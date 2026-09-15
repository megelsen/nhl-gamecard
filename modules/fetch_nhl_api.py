import requests
import logging
from datetime import datetime
from cache_utils import load_cache, save_cache, is_cache_fresh

__all__ = ['get_logo','get_schedule', 'get_current_standings', 'get_team_stats', 'get_season_data','get_player_stats','get_playoff_series','get_team_summary','get_game_stats']

logger = logging.getLogger(__name__)


def _safe_get_json(url, cache_name):
    """
    Fetch JSON from `url`, falling back to whatever is in cache (even if stale)
    if the request fails or the response isn't valid JSON. Never raises.
    Returns None only if there is no cached fallback available either.
    """
    try:
        res = requests.get(url, timeout=10)
        res.raise_for_status()
        data = res.json()
    except requests.exceptions.RequestException as e:
        logger.warning(f"[fetch_nhl_api] Request failed for {url}: {e}")
        data = None
    except ValueError as e:
        # includes requests' JSONDecodeError, which subclasses ValueError
        body_preview = res.text[:200] if 'res' in locals() else ""
        logger.warning(f"[fetch_nhl_api] Non-JSON response from {url}: {e} | body: {body_preview!r}")
        data = None

    if data is not None:
        save_cache(cache_name, data)
        return data

    # Fall back to stale cache if we have one, rather than crashing the caller.
    try:
        stale = load_cache(cache_name)
        if stale is not None:
            logger.warning(f"[fetch_nhl_api] Using stale cache for {cache_name} after fetch failure.")
        return stale
    except Exception:
        return None


def get_logo(team_abr):
# # Download the SVG file
  url = f"https://assets.nhle.com/logos/nhl/svg/{team_abr}_light.svg"
  #response = requests.get(url)
  return url

def get_schedule(team_abbr,season_id="now"):
    cache_name = f"schedule_{team_abbr}_{season_id}"
    if is_cache_fresh(cache_name):
        return load_cache(cache_name)

    url = f"https://api-web.nhle.com/v1/club-schedule-season/{team_abbr}/{season_id}"
    return _safe_get_json(url, cache_name)


def get_current_standings(current_date):
    cache_name = f"standings_{current_date}"
    if is_cache_fresh(cache_name):
        return load_cache(cache_name)

    url = f"https://api-web.nhle.com/v1/standings/{current_date}"
    return _safe_get_json(url, cache_name)


def get_team_stats(team_abbr):
    cache_name = f"team_stats_{team_abbr}"
    if is_cache_fresh(cache_name):
        return load_cache(cache_name)

    url = f"https://api-web.nhle.com/v1/club-stats/{team_abbr}/now"
    return _safe_get_json(url, cache_name)


def get_season_data():
    cache_name = "season_data"
    if is_cache_fresh(cache_name):
        return load_cache(cache_name)

    url = f"https://api-web.nhle.com/v1/standings-season"
    return _safe_get_json(url, cache_name)


def get_player_stats(playerID):
    cache_name = f"player_{playerID}"
    if is_cache_fresh(cache_name):
        return load_cache(cache_name)

    url = f"https://api-web.nhle.com/v1/player/{playerID}/landing"
    return _safe_get_json(url, cache_name)

def get_game_stats(gameID):
    cache_name = f"game_stats_{gameID}"
    if is_cache_fresh(cache_name):
        return load_cache(cache_name)

    url = f"https://api-web.nhle.com/v1/wsc/game-story/{gameID}"
    return _safe_get_json(url, cache_name)


def get_playoff_series(seasonID):
    cache_name = f"playoff_series_{seasonID}"
    if is_cache_fresh(cache_name):
        return load_cache(cache_name)

    url = f"https://api-web.nhle.com/v1/playoff-series/carousel/{seasonID}/"
    return _safe_get_json(url, cache_name)

def get_team_summary(seasonID, playoffs):
    cache_name = f"teams_summary_{seasonID}_{playoffs}"
    if is_cache_fresh(cache_name):
        return load_cache(cache_name)

    if playoffs == 1:
        gameID = 3
    else:
        gameID = 2

    url = f"https://api.nhle.com/stats/rest/en/team/summary?sort=shotsForPerGame&cayenneExp=seasonId={seasonID}%20and%20gameTypeId={gameID}"
    return _safe_get_json(url, cache_name)