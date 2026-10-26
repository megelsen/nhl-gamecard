import json
import requests
import random
import threading
import time
import logging
from contextlib import contextmanager
from email.utils import parsedate_to_datetime
from cache_utils import load_cache, load_latest_cache, save_cache, is_cache_fresh

__all__ = ['get_logo','get_schedule', 'get_current_standings', 'get_team_stats', 'get_season_data','get_player_stats','get_playoff_bracket','get_team_summary','get_game_stats','get_roster','get_boxscore','get_skater_edge','get_goalie_edge','get_shot_locations','get_player_season_report','get_player_ranking','get_skater_summary','get_skater_leaders','get_goalie_leaders','get_edge_skater_leaders','EDGE_LEADER_PATHS','track_fetch_failures']

logger = logging.getLogger(__name__)

MAX_ATTEMPTS = 3
RETRY_DELAYS_SECONDS = (1, 4)  # before the 2nd and 3rd attempt, plus up to 1s of jitter
# Longest wait (e.g. from a Retry-After header) before a retry: short while a visitor is
# waiting on the page, longer for a forced refresh running in the background.
MAX_RETRY_WAIT_SECONDS = 5
MAX_RETRY_WAIT_SECONDS_FORCED = 30
FAILURE_BACKOFF_SECONDS = 300  # after a failed fetch, serve stale cache for this long before retrying

# url -> time of the last failed fetch, so an outage doesn't make every request wait on retries
_recent_failures = {}

# Per-thread list of failed fetches, set while inside track_fetch_failures()
_tracker = threading.local()


@contextmanager
def track_fetch_failures():
    """Collects a description of every fetch in this thread that fails inside the block
    (the caller got stale cache or None instead of fresh data)."""
    _tracker.failures = []
    try:
        yield _tracker.failures
    finally:
        _tracker.failures = None


def _fetch_once(url, parse=None):
    """Single attempt. Returns parsed JSON (or `parse(text)`), or raises on failure/bad response."""
    res = requests.get(url, timeout=10)
    res.raise_for_status()
    return parse(res.text) if parse else res.json()


def _retry_after_seconds(response):
    """Seconds requested by a Retry-After header (delta-seconds or HTTP date), or None."""
    value = response.headers.get("Retry-After") if response is not None else None
    if not value:
        return None
    try:
        return max(0.0, float(value))
    except ValueError:
        pass
    try:
        return max(0.0, parsedate_to_datetime(value).timestamp() - time.time())
    except (TypeError, ValueError):
        return None


def _fetch_with_retries(url, max_wait=MAX_RETRY_WAIT_SECONDS, parse=None):
    """Retries transient failures with exponential backoff and jitter, honoring Retry-After.
    Returns (data, None) on success, or (None, short error description)."""
    last_error = None

    for attempt in range(1, MAX_ATTEMPTS + 1):
        retry_after = None
        try:
            return _fetch_once(url, parse), None
        except requests.exceptions.RequestException as e:
            status = getattr(e.response, "status_code", None)
            last_error = f"HTTP {status}" if status is not None else type(e).__name__
            logger.warning(f"[fetch_nhl_api] Attempt {attempt}/{MAX_ATTEMPTS} failed for {url}: {e}")
            if status is not None and 400 <= status < 500 and status != 429:
                break  # e.g. 404 for a season without playoffs yet: retrying won't help
            retry_after = _retry_after_seconds(e.response)
        except ValueError as e:
            # includes requests' JSONDecodeError, which subclasses ValueError
            last_error = "unparseable response"
            logger.warning(f"[fetch_nhl_api] Attempt {attempt}/{MAX_ATTEMPTS}: unparseable response from {url}: {e}")

        if attempt == MAX_ATTEMPTS:
            break
        if retry_after is not None:
            if retry_after > max_wait:
                logger.warning(f"[fetch_nhl_api] {url} asks to retry after {retry_after:.0f}s — giving up for now.")
                break
            delay = retry_after
        else:
            delay = min(RETRY_DELAYS_SECONDS[attempt - 1] + random.uniform(0, 1), max_wait)
        time.sleep(delay)

    logger.warning(f"[fetch_nhl_api] Fetch failed for {url} after {attempt} attempt(s): {last_error}")
    return None, last_error


def _get_cached_json(cache_name):
    """
    Returns the cached value ONLY if it's fresh AND actually usable (not None/empty).
    A cache entry that is None or empty is treated as if there were no cache at all,
    so a bad/corrupted cache entry can never silently short-circuit a real fetch.
    """
    if not is_cache_fresh(cache_name):
        return None
    try:
        cached = load_cache(cache_name)
    except Exception as e:
        logger.warning(f"[fetch_nhl_api] Failed to load cache {cache_name}: {e}")
        return None
    if not cached:
        logger.warning(f"[fetch_nhl_api] Cache {cache_name} marked fresh but empty/None — ignoring it.")
        return None
    return cached


def _safe_get_json(url, cache_name, force=False, parse=None):
    """
    Fetch JSON from `url` (using a valid fresh cache entry if one exists, unless `force`),
    retrying a few times on transient failures before falling back to the newest stale
    cache entry from a previous day. Never raises. Returns None only if there is no
    usable data anywhere. `parse` turns a non-JSON body (e.g. CSV) into JSON-serializable data.
    """
    if not force:
        cached = _get_cached_json(cache_name)
        if cached is not None:
            return cached

    stale = load_latest_cache(cache_name)

    # During an outage (or for a URL that doesn't exist yet), don't make every request
    # sit through the retries again.
    last_failure = _recent_failures.get(url)
    if not force and last_failure and time.time() - last_failure < FAILURE_BACKOFF_SECONDS:
        return stale

    data, error = _fetch_with_retries(url, MAX_RETRY_WAIT_SECONDS_FORCED if force else MAX_RETRY_WAIT_SECONDS, parse)

    if data is not None:
        _recent_failures.pop(url, None)
        save_cache(cache_name, data)
        return data

    _recent_failures[url] = time.time()
    failures = getattr(_tracker, "failures", None)
    if failures is not None:
        failures.append(f"{cache_name} ({error})")
    if stale:
        logger.warning(f"[fetch_nhl_api] Using stale cache for {cache_name} after fetch failure.")
    return stale


def get_logo(team_abr):
  url = f"https://assets.nhle.com/logos/nhl/svg/{team_abr}_light.svg"
  return url

def get_schedule(team_abbr, season_id="now", force=False):
    cache_name = f"schedule_{team_abbr}_{season_id}"
    url = f"https://api-web.nhle.com/v1/club-schedule-season/{team_abbr}/{season_id}"
    return _safe_get_json(url, cache_name, force)


def get_current_standings(current_date, force=False):
    cache_name = f"standings_{current_date}"
    url = f"https://api-web.nhle.com/v1/standings/{current_date}"
    return _safe_get_json(url, cache_name, force)


def get_team_stats(team_abbr, force=False):
    cache_name = f"team_stats_{team_abbr}"
    url = f"https://api-web.nhle.com/v1/club-stats/{team_abbr}/now"
    return _safe_get_json(url, cache_name, force)


def get_roster(team_abbr, force=False):
    cache_name = f"roster_{team_abbr}"
    url = f"https://api-web.nhle.com/v1/roster/{team_abbr}/current"
    return _safe_get_json(url, cache_name, force)


def get_skater_edge(playerID):
    # NHL EDGE tracking: shot speed, skating speed, shots by danger zone (regular season)
    cache_name = f"edge_skater_{playerID}"
    url = f"https://api-web.nhle.com/v1/edge/skater-detail/{playerID}/now"
    return _safe_get_json(url, cache_name)


def get_goalie_edge(playerID):
    # NHL EDGE: save % by danger zone (regular season)
    cache_name = f"edge_goalie_{playerID}"
    url = f"https://api-web.nhle.com/v1/edge/goalie-detail/{playerID}/now"
    return _safe_get_json(url, cache_name)


def get_shot_locations(playerID, goalie=False):
    # NHL EDGE shots (skaters) or shots against (goalies) per offensive-zone area: the card's shot map
    kind = "goalie" if goalie else "skater"
    url = f"https://api-web.nhle.com/v1/edge/{kind}-shot-location-detail/{playerID}/now"
    return _safe_get_json(url, f"edge_shot_locations_{playerID}")


def get_player_season_report(playerID, goalie=False):
    # One row per NHL regular season with the teams in order ("VAN,NYR") and, for skaters, hits
    report = "goalie/summary" if goalie else "skater/realtime"
    cache_name = f"season_report_{playerID}"
    url = f"https://api.nhle.com/stats/rest/en/{report}?cayenneExp=playerId={playerID}%20and%20gameTypeId=2"
    return _safe_get_json(url, cache_name)


def _ranking(text, key):
    # {playerId: value} from a league-wide stats report, so the cache stays small
    return {str(row["playerId"]): row.get(key) or 0 for row in json.loads(text).get("data", [])}


def _summary_url(report, season_id):
    return f"https://api.nhle.com/stats/rest/en/{report}/summary?limit=-1&cayenneExp=seasonId={season_id}%20and%20gameTypeId=2"


def _skater_summary(text):
    return {str(row["playerId"]): {"pos": row.get("positionCode"), "gp": row.get("gamesPlayed") or 0,
                                   "g": row.get("goals") or 0, "a": row.get("assists") or 0, "p": row.get("points") or 0}
            for row in json.loads(text).get("data", [])}


def get_skater_summary(season_id, force=False):
    """Every skater's regular-season {playerId: {pos, gp, g, a, p}} (whole league, one request),
    for the player card percentiles and for sorting player lists."""
    return _safe_get_json(_summary_url("skater", season_id), f"skater_summary_{season_id}", force, parse=_skater_summary)


def get_player_ranking(season_id, force=False):
    """Every player's {playerId: value} for sorting player lists: points for skaters, games
    played for goalies (regular season, whole league, one request each)."""
    ranking = {player_id: row["p"] for player_id, row in (get_skater_summary(season_id, force) or {}).items()}
    goalies = _safe_get_json(_summary_url("goalie", season_id), f"ranking_goalie_{season_id}", force,
                             parse=lambda text: _ranking(text, "gamesPlayed"))
    ranking.update(goalies or {})
    return ranking


def get_boxscore(gameID):
    cache_name = f"boxscore_{gameID}"
    url = f"https://api-web.nhle.com/v1/gamecenter/{gameID}/boxscore"
    return _safe_get_json(url, cache_name)


def get_season_data(force=False):
    cache_name = "season_data"
    url = f"https://api-web.nhle.com/v1/standings-season"
    return _safe_get_json(url, cache_name, force)


def get_player_stats(playerID):
    cache_name = f"player_{playerID}"
    url = f"https://api-web.nhle.com/v1/player/{playerID}/landing"
    return _safe_get_json(url, cache_name)

def get_game_stats(gameID):
    cache_name = f"game_stats_{gameID}"
    url = f"https://api-web.nhle.com/v1/wsc/game-story/{gameID}"
    return _safe_get_json(url, cache_name)


LEADERS_LIMIT = 15


def get_skater_leaders(force=False):
    # League leaders per category (goals, assists, points, plusMinus, goalsPp, goalsSh,
    # faceoffLeaders, penaltyMins, toi), each a list of players with headshot, team and value
    url = f"https://api-web.nhle.com/v1/skater-stats-leaders/current?limit={LEADERS_LIMIT}"
    return _safe_get_json(url, "skater_leaders", force)


def get_goalie_leaders(force=False):
    # Same for goalies: wins, savePctg, goalsAgainstAverage, shutouts
    url = f"https://api-web.nhle.com/v1/goalie-stats-leaders/current?limit={LEADERS_LIMIT}"
    return _safe_get_json(url, "goalie_leaders", force)


# NHL EDGE top 10s (no deeper lists, and none for goalies): {name: path under /v1/edge/}
EDGE_LEADER_PATHS = {
    "speed": "skater-speed-top-10/all/max/now",
    "shot": "skater-shot-speed-top-10/all/max/now",
    "distance": "skater-distance-top-10/all/all/total/now",
    "hdshots": "skater-shot-location-top-10/all/sog/high/now",
}


def get_edge_skater_leaders(name, force=False):
    url = f"https://api-web.nhle.com/v1/edge/{EDGE_LEADER_PATHS[name]}"
    return _safe_get_json(url, f"edge_leaders_{name}", force)


def get_playoff_bracket(seasonID, force=False):
    # The bracket is keyed by the year the playoffs are played in (season 20262027 -> 2027);
    # its "series" list stays empty until the playoffs start.
    year = str(seasonID)[-4:]
    cache_name = f"playoff_bracket_{year}"
    url = f"https://api-web.nhle.com/v1/playoff-bracket/{year}"
    return _safe_get_json(url, cache_name, force)

def get_team_summary(seasonID, playoffs, force=False):
    cache_name = f"teams_summary_{seasonID}_{playoffs}"

    if playoffs == 1:
        gameID = 3
    else:
        gameID = 2

    url = f"https://api.nhle.com/stats/rest/en/team/summary?sort=shotsForPerGame&cayenneExp=seasonId={seasonID}%20and%20gameTypeId={gameID}"
    return _safe_get_json(url, cache_name, force)
