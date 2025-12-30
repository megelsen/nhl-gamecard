from modules.elements.previous_games import (get_logo, display_game_result)
from modules.read_schedule import *
from modules.fetch_nhl_api import get_schedule

__all__ = ['games_vs_opponent','get_previous_matchup']
# 
def games_vs_opponent(sorted_opponents, opponent_abr):
    return next(
        (
            (opponent, games)
            for opponent, games in sorted_opponents
            if games and games[0]["opponent_abr"] == opponent_abr
        ),
        None
    )

def get_previous_matchup(team_abbr,team_info, opponent,sorted_opponents,season_data,season_id):
    # current season
    games = games_vs_opponent(sorted_opponents, opponent)


    games_list = games[1] 
    latest_game = next(
    (g for g in reversed(games_list)
     if g["home_score"] is not None and g["away_score"] is not None),
    None)

    # previous season
    if latest_game is None:
        # API Call to previous season:
        
        previous_season_id = str(int(season_id) - 10001)
        previous_season_schelude = get_schedule(team_abbr,previous_season_id)
        previous_games_by_date, previous_games_by_opponent =  get_games_data(team_info,previous_season_schelude,season_data,previous_season_id)
        previous_sorted_opponents = sort_games_by_opponent(previous_games_by_opponent)
        games = games_vs_opponent(previous_sorted_opponents, opponent)
        
        games_list = games[1]  # this is the list of dicts
        latest_game = next(
            (g for g in reversed(games_list)
            if g["home_score"] is not None and g["away_score"] is not None),
            None
        )

    return latest_game

