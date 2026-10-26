import csv
import io
import json
import os
import zipfile
from collections import defaultdict

from cache_utils import latest_cache_path
from modules.fetch_nhl_api import _safe_get_json
from modules.read_schedule import get_season_id
from modules.rink_zones import from_moneypuck, zone_for

__all__ = ['get_moneypuck_skaters', 'get_moneypuck_goalies', 'get_moneypuck_shots', 'cached_moneypuck_shots',
           'has_moneypuck_shots', 'moneypuck_cache_names']

# Expected goals (xG) from MoneyPuck.com: no NHL endpoint has xG. Free for non-commercial use
# as long as MoneyPuck.com is credited wherever the data shows (see the footer disclaimer).
# One CSV per season for the whole league, keyed by the same playerId as the NHL APIs.
MONEYPUCK_URL = "https://moneypuck.com/moneypuck/playerData/seasonSummary/{year}/regular/{kind}.csv"


def _number(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _parse_skaters(text):
    """5-on-5 on-ice expected goals per player: {playerId: {name, team, pos, gp, toi, xgf, xga}}."""
    players = {}
    for row in csv.DictReader(io.StringIO(text)):
        if row.get("situation") != "5on5":
            continue
        players[row["playerId"]] = {
            "name": row.get("name"),
            "team": row.get("team"),  # same abbreviations as the NHL APIs
            "pos": row.get("position"),
            "gp": _number(row.get("games_played")),
            "toi": _number(row.get("icetime")),  # seconds
            "xgf": _number(row.get("OnIce_F_xGoals")),
            "xga": _number(row.get("OnIce_A_xGoals")),
        }
    if not players:
        raise ValueError("no 5on5 rows in MoneyPuck skaters CSV")
    return players


def _parse_goalies(text):
    """All-situations expected vs. actual goals against: {playerId: {name, team, gp, xga, ga}}."""
    goalies = {}
    for row in csv.DictReader(io.StringIO(text)):
        if row.get("situation") != "all":
            continue
        goalies[row["playerId"]] = {
            "name": row.get("name"),
            "team": row.get("team"),
            "gp": _number(row.get("games_played")),
            "xga": _number(row.get("xGoals")),
            "ga": _number(row.get("goals")),
        }
    if not goalies:
        raise ValueError("no rows in MoneyPuck goalies CSV")
    return goalies


def _start_year(season_id):
    # MoneyPuck names a season by the year it starts in (20262027 -> 2026)
    return str(season_id)[:4]


def _finished(season_id):
    # A past season's files don't change any more: downloaded once and kept (see moneypuck_cache_names)
    return str(season_id) < get_season_id()


def _summary_cache_name(season_id, kind):
    return f"moneypuck_{kind}_v2_{_start_year(season_id)}"


def get_moneypuck_skaters(season_id, force=False):
    url = MONEYPUCK_URL.format(year=_start_year(season_id), kind="skaters")
    return _safe_get_json(url, _summary_cache_name(season_id, "skaters"), force, parse=_parse_skaters,
                          final=_finished(season_id))


def get_moneypuck_goalies(season_id, force=False):
    url = MONEYPUCK_URL.format(year=_start_year(season_id), kind="goalies")
    return _safe_get_json(url, _summary_cache_name(season_id, "goalies"), force, parse=_parse_goalies,
                          final=_finished(season_id))


# Every unblocked shot attempt of a season (shots on goal, misses, goals) with coordinates and
# expected goals, one zip per season (about 20 MB zipped by the end of a season). The scheduler
# downloads it daily and adds it up per player for the card's shot map; cards read only the cache.
MONEYPUCK_SHOTS_URL = "https://peter-tanner.com/moneypuck/downloads/shots_{year}.zip"
HEAT_ZONE_DEPTH = 75  # the heat grid covers the offensive zone (end boards to blue line)
SHOTS_MEMO_SIZE = 2  # seasons kept in memory (a few MB of JSON each): this one and one past season
_shots_memo = {}  # season start year -> (cache path, mtime, data), least recently used first


def _heat_cell(x, y):
    # 1 x 1 ft cells: (column 0-84 from the left boards, row 0-74 from the end boards), or None
    if y >= HEAT_ZONE_DEPTH:
        return None
    return min(84, max(0, int(x + 42.5))), max(0, int(y))


def _parse_shots(content):
    """Per player: {"skaters": {playerId: {"z": {area: [shots on goal, misses, goals, xG]},
    "h": {"shots": [[col, row, n], ...], "misses": [...], "goals": [...]}}},
    "goalies": {playerId: {"z": {area: [shots against, saves, goals against, xG against]},
    "h": {"shots": [...], "saves": [...], "goals": [...]}}}}, regular season only.
    Areas from rink_zones; xG covers all unblocked attempts, misses included (like MoneyPuck's GSAx)."""
    archive = zipfile.ZipFile(io.BytesIO(content))
    reader = csv.reader(io.TextIOWrapper(archive.open(archive.namelist()[0]), encoding="utf-8"))
    column = {name: i for i, name in enumerate(next(reader))}
    event_i, xg_i, playoff_i = column["event"], column["xGoal"], column["isPlayoffGame"]
    x_i, y_i = column["xCordAdjusted"], column["yCordAdjusted"]
    shooter_i, goalie_i = column["shooterPlayerId"], column["goalieIdForShot"]

    zones = {"skaters": defaultdict(lambda: defaultdict(lambda: [0, 0, 0, 0.0])),
             "goalies": defaultdict(lambda: defaultdict(lambda: [0, 0, 0, 0.0]))}
    heat = {"skaters": defaultdict(lambda: defaultdict(lambda: defaultdict(int))),
            "goalies": defaultdict(lambda: defaultdict(lambda: defaultdict(int)))}
    for row in reader:
        event = row[event_i]
        if row[playoff_i] != "0" or event not in ("SHOT", "MISS", "GOAL"):
            continue
        try:
            x, y = from_moneypuck(float(row[x_i]), float(row[y_i]))
            xg = float(row[xg_i] or 0)
        except ValueError:
            continue
        zone, cell = zone_for(x, y), _heat_cell(x, y)
        on_goal, goal = event != "MISS", event == "GOAL"
        shooter, goalie = row[shooter_i].split(".")[0], row[goalie_i].split(".")[0]
        if shooter and shooter != "0":
            totals = zones["skaters"][shooter][zone]
            totals[0] += on_goal
            totals[1] += not on_goal
            totals[2] += goal
            totals[3] += xg
            if cell:
                kind = "goals" if goal else "shots" if on_goal else "misses"
                heat["skaters"][shooter][kind][cell] += 1
                if goal:
                    heat["skaters"][shooter]["shots"][cell] += 1  # goals are shots on goal too
        if goalie and goalie != "0":  # "0": empty net
            totals = zones["goalies"][goalie][zone]
            totals[0] += on_goal
            totals[1] += on_goal and not goal
            totals[2] += goal
            totals[3] += xg
            if cell and on_goal:
                heat["goalies"][goalie]["shots"][cell] += 1
                heat["goalies"][goalie]["goals" if goal else "saves"][cell] += 1

    result = {}
    for group in ("skaters", "goalies"):
        result[group] = {
            player: {
                "z": {zone: [*counts[:3], round(counts[3], 3)] for zone, counts in player_zones.items() if zone},
                "h": {kind: [[col, line, n] for (col, line), n in cells.items()]
                      for kind, cells in heat[group][player].items()},
            }
            for player, player_zones in zones[group].items()
        }
    if not result["skaters"]:
        raise ValueError("no shots in MoneyPuck shots file")
    return result


_parse_shots.binary = True


def _shots_cache_name(season_id):
    return f"moneypuck_shots_{_start_year(season_id)}"


def get_moneypuck_shots(season_id, force=False):
    """Download and add up the season's shots (scheduler); see _parse_shots."""
    year = _start_year(season_id)
    return _safe_get_json(MONEYPUCK_SHOTS_URL.format(year=year), _shots_cache_name(season_id), force,
                          parse=_parse_shots, final=_finished(season_id))


def has_moneypuck_shots(season_id):
    """Whether the season's shots were downloaded, without loading them."""
    return latest_cache_path(_shots_cache_name(season_id)) is not None


def moneypuck_cache_names(season_ids):
    """Cache names of the finished seasons among `season_ids`, which prune_cache must keep, since
    they're downloaded only once."""
    return {name(season_id) for season_id in season_ids if _finished(season_id)
            for name in (_shots_cache_name, lambda s: _summary_cache_name(s, "skaters"),
                         lambda s: _summary_cache_name(s, "goalies"))}


def cached_moneypuck_shots(season_id):
    """The newest added-up shots from the cache, without downloading (for page requests). Kept in
    memory until the cache file changes, since it's a few MB of JSON by the end of a season; at most
    SHOTS_MEMO_SIZE seasons at a time."""
    path = latest_cache_path(_shots_cache_name(season_id))
    if not path:
        return None
    year = _start_year(season_id)
    try:
        mtime = os.path.getmtime(path)
        entry = _shots_memo.pop(year, None)
        if not entry or entry[:2] != (path, mtime):
            with open(path) as f:
                entry = (path, mtime, json.load(f))
    except (OSError, ValueError):
        return None
    _shots_memo[year] = entry  # most recently used last
    while len(_shots_memo) > SHOTS_MEMO_SIZE:
        del _shots_memo[next(iter(_shots_memo))]
    return entry[2]
