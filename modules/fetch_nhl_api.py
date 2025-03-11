import requests
from datetime import datetime

__all__ = ['get_logo','get_schedule', 'get_current_standings', 'get_team_stats', 'get_season_data','get_player_stats']

def get_logo(team_abr):
# # Download the SVG file
  url = f"https://assets.nhle.com/logos/nhl/svg/{team_abr}_light.svg"
  #response = requests.get(url)
  return url

def get_schedule(team_abbr):
    schedule_url = f"https://api-web.nhle.com/v1/club-schedule-season/{team_abbr}/now"
    schedule = requests.get(schedule_url)
    schedule_data = schedule.json()
    return schedule_data

def get_current_standings(current_date):    
    standings_url = f"https://api-web.nhle.com/v1/standings/{current_date}"
    standings = requests.get(standings_url)
    standings_data = standings.json()
    return standings_data

def get_team_stats(team_abbr):
    team_stats_url = f"https://api-web.nhle.com/v1/club-stats/{team_abbr}/now"
    team_stats = requests.get(team_stats_url)
    team_stats_data = team_stats.json()
    return team_stats_data

def get_season_data():
    season_url = f"https://api-web.nhle.com/v1/standings-season"
    season = requests.get(season_url)
    season_data = season.json()
    return season_data

def get_player_stats(playerID):
    player_stats_url = f"https://api-web.nhle.com/v1/player/{playerID}/landing"
    player_stats = requests.get(player_stats_url)
    player_stats_data = player_stats.json()
    return player_stats_data