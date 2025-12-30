import requests
from datetime import datetime
from cache_utils import load_cache, save_cache, is_cache_fresh

__all__ = ['get_logo','get_schedule', 'get_current_standings', 'get_team_stats', 'get_season_data','get_player_stats','get_playoff_series','get_team_summary','get_game_stats']


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
    res = requests.get(url)
    data = res.json()
    save_cache(cache_name, data)
    return data


def get_current_standings(current_date):    
    cache_name = f"standings_{current_date}"
    if is_cache_fresh(cache_name):
        return load_cache(cache_name)

    url = f"https://api-web.nhle.com/v1/standings/{current_date}"
    res = requests.get(url)
    data = res.json()
    save_cache(cache_name, data)
    return data


def get_team_stats(team_abbr):
    cache_name = f"team_stats_{team_abbr}"
    if is_cache_fresh(cache_name):
        return load_cache(cache_name)

    url = f"https://api-web.nhle.com/v1/club-stats/{team_abbr}/now"
    res = requests.get(url)
    data = res.json()
    save_cache(cache_name, data)
    return data


def get_season_data():
    cache_name = "season_data"
    if is_cache_fresh(cache_name):
        return load_cache(cache_name)

    url = f"https://api-web.nhle.com/v1/standings-season"
    res = requests.get(url)
    data = res.json()
    save_cache(cache_name, data)
    return data


def get_player_stats(playerID):
    cache_name = f"player_{playerID}"
    if is_cache_fresh(cache_name):
        return load_cache(cache_name)

    url = f"https://api-web.nhle.com/v1/player/{playerID}/landing"
    res = requests.get(url)
    data = res.json()
    save_cache(cache_name, data)
    return data

def get_game_stats(gameID):
    cache_name = f"game_stats_{gameID}"
    if is_cache_fresh(cache_name):
        return load_cache(cache_name)

    url = f"https://api-web.nhle.com/v1/wsc/game-story/{gameID}"
    res = requests.get(url)
    data = res.json()
    save_cache(cache_name, data)
    return data


def get_playoff_series(seasonID):
    cache_name = f"playoff_series_{seasonID}"
    if is_cache_fresh(cache_name):
        return load_cache(cache_name)

    url = f"https://api-web.nhle.com/v1/playoff-series/carousel/{seasonID}/"
    res = requests.get(url)
    data = res.json()
    save_cache(cache_name, data)
    return data

def get_team_summary(seasonID, playoffs):
    cache_name = f"teams_summary_{seasonID}_{playoffs}"
    if is_cache_fresh(cache_name):
        return load_cache(cache_name)

    if playoffs == 1:
        gameID = 3
    else: 
        gameID = 2

    url = f"https://api.nhle.com/stats/rest/en/team/summary?sort=shotsForPerGame&cayenneExp=seasonId={seasonID}%20and%20gameTypeId={gameID}"
    res = requests.get(url)
    data = res.json()
    save_cache(cache_name, data)
    return data