import requests
import time
import logging
from cache_utils import load_cache, load_latest_cache, save_cache, is_cache_fresh

__all__ = ['get_logo','get_schedule', 'get_current_standings', 'get_team_stats', 'get_season_data','get_player_stats','get_playoff_bracket','get_team_summary','get_game_stats','get_roster','get_boxscore']

logger = logging.getLogger(__name__)

MAX_ATTEMPTS = 3
RETRY_DELAY_SECONDS = 1.5  # multiplied by attempt number (1.5s, 3s, ...)
FAILURE_BACKOFF_SECONDS = 300  # after a failed fetch, serve stale cache for this long before retrying

# url -> time of the last failed fetch, so an outage doesn't make every request wait on retries
_recent_failures = {}


def _fetch_once(url):
    """Single attempt. Returns parsed JSON, or raises on failure/bad response."""
    res = requests.get(url, timeout=10)
    res.raise_for_status()
    return res.json()


def _fetch_with_retries(url):
    """Retries a few times on transient failures. Returns None if all attempts fail."""
    data = None
    last_error = None

    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            data = _fetch_once(url)
            break
        except requests.exceptions.RequestException as e:
            last_error = e
            logger.warning(f"[fetch_nhl_api] Attempt {attempt}/{MAX_ATTEMPTS} failed for {url}: {e}")
            status = getattr(e.response, "status_code", None)
            if status is not None and 400 <= status < 500 and status != 429:
                break  # e.g. 404 for a season without playoffs yet: retrying won't help
        except ValueError as e:
            # includes requests' JSONDecodeError, which subclasses ValueError
            last_error = e
            logger.warning(f"[fetch_nhl_api] Attempt {attempt}/{MAX_ATTEMPTS}: non-JSON response from {url}: {e}")

        if attempt < MAX_ATTEMPTS:
            time.sleep(RETRY_DELAY_SECONDS * attempt)

    if data is None:
        logger.warning(f"[fetch_nhl_api] All {MAX_ATTEMPTS} attempts failed for {url}: {last_error}")

    return data


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


def _safe_get_json(url, cache_name, force=False):
    """
    Fetch JSON from `url` (using a valid fresh cache entry if one exists, unless `force`),
    retrying a few times on transient failures before falling back to the newest stale
    cache entry from a previous day. Never raises. Returns None only if there is no
    usable data anywhere.
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

    data = _fetch_with_retries(url)

    if data is not None:
        _recent_failures.pop(url, None)
        save_cache(cache_name, data)
        return data

    _recent_failures[url] = time.time()
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
