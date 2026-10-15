from datetime import datetime
from modules.fetch_nhl_api import (get_logo,  get_game_stats)
from modules.elements.compare import compare_mount, game_comparison
from datetime import timedelta
__all__ = ['display_game_result', 'get_previous_games','display_latest_game_result','display_previous_matchup']

def short_date(date):
    return f"{date:%b} {date.day}"  # e.g. "Oct 13"

def display_game_result(game):
    opponent_logo = get_logo(game['opponent_abr'])
    game_disp = f"""
                {game['game_venue']}
                <a href="javascript:void(0);" class="team-link">
                <img src="{opponent_logo}" style="width: 85px">
                </a>
                <span class="game-score">
                    <span>{game['home_score']} -  {game['away_score']} ({game['result']})</span>
                    <span class="game-date">{short_date(game['game_date'])}</span>
                </span>
                <a href={game["gamecenterURL"]} target="_blank" rel="noopener noreferrer" class="recap-link">                
                <span class="material-symbols-outlined">
                    open_in_new
                </span></a> <br>
                """

    return game_disp

def display_latest_game_result(game):
    opponent_logo = get_logo(game['opponent_abr'])
    game_disp = f"""
                {game['game_venue']}
                <a href="javascript:void(0);" class="team-link">
                <img src="{opponent_logo}" style="width: 85px">
                </a>
                <span class="game-score">
                    <div class="spoiler-wrapper">
                        <button class="toggle-spoiler">
                            <span class="material-symbols-outlined">
                                visibility
                            </span>
                        </button>
                        <span class="hide-spoiler"> {game['home_score']} -  {game['away_score']} ({game['result']}) </span>
                    </div>
                    <span class="game-date">{short_date(game['game_date'])}</span>
                </span>
                <a href={game["recap_URL"]} target="_blank" rel="noopener noreferrer" class="recap-link">                
                <span class="material-symbols-outlined">
                    open_in_new
                </span></a> <br>
                """

    return game_disp

def get_previous_games(games_by_date,nr_games=3):
    # Get the current date and time
    current_date = datetime.now()
    current_date = current_date.replace(hour=0, minute=0, second=0, microsecond=0)
    previous_games = sorted([game for game in games_by_date if game['game_date'] < current_date], key= lambda x: x['game_date'])
    last_games = previous_games[-nr_games:] if len(previous_games) >= nr_games else previous_games
    if last_games == []:
        last_game_disp = [f"""
                            <span> No games played yet </span>
                            """]
    else:
        last_game_disp = [display_latest_game_result(last_games[-1])]  # First game uses different function
        last_game_disp += [display_game_result(game) for game in reversed(last_games[:-1])]  # The rest use the normal function

    return last_game_disp

def display_previous_matchup(game):
    if game is None:
        return "<span> No recent meeting </span>", ""
    game_date = game['game_date']
    current_date = datetime.now()
    current_date = current_date.replace(hour=0, minute=0, second=0, microsecond=0)
    date_str = game_date.strftime("%b %d %Y")     

    game_data = get_game_stats(game['game_id'])
    if not game_data or 'homeTeam' not in game_data or 'awayTeam' not in game_data:
        # Game details unavailable: fall back to the result from the schedule
        return display_game_result(game), f"<span> On {date_str} </span>"

    previous_matchup = compare_mount(game_comparison(game_data))
    if current_date - game_date < timedelta(days=3):
        previous_matchup_html = f"""
        <div class="spoiler-wrapper">
            <button class="toggle-spoiler">
                <span class="material-symbols-outlined">visibility</span>
            </button>
            <span class="hide-spoiler">
                {previous_matchup}
            </span>
        </div>
        """
    else:
        previous_matchup_html = previous_matchup
        date_str = f"""
                <span> On {date_str} ({game['result']})</span>
                <a href={game["gamecenterURL"]} target="_blank" rel="noopener noreferrer" class="recap-link">                
                <span class="material-symbols-outlined">
                    open_in_new
                </span></a> <br>
                """
    return previous_matchup_html, date_str 

def display_game_no_spoiler(game):
    
    game_disp = f"""
                {game['game_venue']}
               
                {game['home_score']} -  {game['away_score']} ({game['result']}) 
                <a href={game["recap_URL"]} target="_blank" rel="noopener noreferrer" class="recap-link">                
                <span class="material-symbols-outlined">
                    open_in_new
                </span></a> <br>
                """

    return game_disp

def display_matchup_spoiler(game):
    
    game_disp = f"""
                {game['game_venue']}
                
                <div class="spoiler-wrapper">
                    <button class="toggle-spoiler">
                        <span class="material-symbols-outlined">
                            visibility
                        </span>
                    </button>  
                    <span class="hide-spoiler"> {game['home_score']} -  {game['away_score']} ({game['result']}) </span>
                </div>
                <a href={game["recap_URL"]} target="_blank" rel="noopener noreferrer" class="recap-link">                
                <span class="material-symbols-outlined">
                    open_in_new
                </span></a> <br>
                """

    return game_disp

