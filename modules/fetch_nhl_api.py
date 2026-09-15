import requests
import time
import logging
from datetime import datetime
from cache_utils import load_cache, save_cache, is_cache_fresh

__all__ = ['get_logo','get_schedule', 'get_current_standings', 'get_team_stats', 'get_season_data','get_player_stats','get_playoff_series','get_team_summary','get_game_stats']

logger = logging.getLogger(__name__)

MAX_ATTEMPTS = 3
RETRY_DELAY_SECONDS = 1.5  # multiplied by attempt number (1.5s, 3s, ...)


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


def _safe_get_json(url, cache_name):
    """
    Fetch JSON from `url` (using a valid fresh cache entry if one exists), retrying
    a few times on transient failures before falling back to a stale cache entry.
    Never raises. Returns None only if there is no usable data anywhere.
    """
    cached = _get_cached_json(cache_name)
    if cached is not None:
        return cached

    data = _fetch_with_retries(url)

    if data is not None:
        save_cache(cache_name, data)
        return data

    # Fall back to stale cache if we have one, rather than crashing the caller.
    try:
        stale = load_cache(cache_name)
        if stale:
            logger.warning(f"[fetch_nhl_api] Using stale cache for {cache_name} after fetch failure.")
            return stale
        return None
    except Exception:
        return None


def get_logo(team_abr):
# # Download the SVG file
  url = f"https://assets.nhle.com/logos/nhl/svg/{team_abr}_light.svg"
  #response = requests.get(url)
  return url

def get_schedule(team_abbr,season_id="now"):
    cache_name = f"schedule_{team_abbr}_{season_id}"
    url = f"https://api-web.nhle.com/v1/club-schedule-season/{team_abbr}/{season_id}"
    return _safe_get_json(url, cache_name)


def get_current_standings(current_date):
    cache_name = f"standings_{current_date}"
    url = f"https://api-web.nhle.com/v1/standings/{current_date}"
    return _safe_get_json(url, cache_name)


def get_team_stats(team_abbr):
    cache_name = f"team_stats_{team_abbr}"
    url = f"https://api-web.nhle.com/v1/club-stats/{team_abbr}/now"
    return _safe_get_json(url, cache_name)


def get_season_data():
    cache_name = "season_data"
    url = f"https://api-web.nhle.com/v1/standings-season"
    return _safe_get_json(url, cache_name)


def get_player_stats(playerID):
    cache_name = f"player_{playerID}"
    url = f"https://api-web.nhle.com/v1/player/{playerID}/landing"
    return _safe_get_json(url, cache_name)

def get_game_stats(gameID):
    cache_name = f"game_stats_{gameID}"
    url = f"https://api-web.nhle.com/v1/wsc/game-story/{gameID}"
    return _safe_get_json(url, cache_name)


def get_playoff_series(seasonID):
    cache_name = f"playoff_series_{seasonID}"
    url = f"https://api-web.nhle.com/v1/playoff-series/carousel/{seasonID}/"
    return _safe_get_json(url, cache_name)

def get_team_summary(seasonID, playoffs):
    cache_name = f"teams_summary_{seasonID}_{playoffs}"

    if playoffs == 1:
        gameID = 3
    else:
        gameID = 2

    url = f"https://api.nhle.com/stats/rest/en/team/summary?sort=shotsForPerGame&cayenneExp=seasonId={seasonID}%20and%20gameTypeId={gameID}"
    return _safe_get_json(url, cache_name)