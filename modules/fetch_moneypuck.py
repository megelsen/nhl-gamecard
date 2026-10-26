import csv
import io

from modules.fetch_nhl_api import _safe_get_json

__all__ = ['get_moneypuck_skaters', 'get_moneypuck_goalies']

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


def get_moneypuck_skaters(season_id, force=False):
    year = _start_year(season_id)
    url = MONEYPUCK_URL.format(year=year, kind="skaters")
    return _safe_get_json(url, f"moneypuck_skaters_v2_{year}", force, parse=_parse_skaters)


def get_moneypuck_goalies(season_id, force=False):
    year = _start_year(season_id)
    url = MONEYPUCK_URL.format(year=year, kind="goalies")
    return _safe_get_json(url, f"moneypuck_goalies_v2_{year}", force, parse=_parse_goalies)
