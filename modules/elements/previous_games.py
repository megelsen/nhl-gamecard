from datetime import datetime
from modules.fetch_nhl_api import (get_logo,  get_game_stats)
from datetime import timedelta
__all__ = ['display_game_result', 'get_previous_games','display_latest_game_result','display_previous_matchup']

def display_game_result(game):
    opponent_logo = get_logo(game['opponent_abr'])
    game_disp = f"""
                {game['game_venue']}
                <a href="javascript:void(0);" class="team-link">
                <img src="{opponent_logo}" style="width: 85px">
                </a>
                {game['home_score']} -  {game['away_score']} ({game['result']})
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
    game_date = game['game_date']
    current_date = datetime.now()
    current_date = current_date.replace(hour=0, minute=0, second=0, microsecond=0)
    date_str = game_date.strftime("%b %d %Y") 
    if current_date - game_date < timedelta(days=3):
        previous_matchup =  display_latest_game_result(game)
        
    else:
        game_data = get_game_stats(game['game_id'])
    
        home_logo = get_logo(game_data['homeTeam']['abbrev'])
        home_score = game_data['homeTeam']['score']
        home_sog = game_data['homeTeam']['sog']              

        away_logo = get_logo(game_data['awayTeam']['abbrev'])
        away_score = game_data['awayTeam']['score']
        away_sog = game_data['awayTeam']['sog']      

        home_svpct = round(1 - (away_score/away_sog),2)
        away_svpct = round(1 - (home_score/home_sog),2)
        
        stats = {
            item["category"]: item
            for item in game_data["summary"]["teamGameStats"]
        }

        faceoff = stats["faceoffWinningPctg"]
        powerplay = stats["powerPlay"]
        hits = stats["hits"]

        faceoff_away = round(faceoff["awayValue"],2)
        faceoff_home = round(faceoff["homeValue"],2)

        pp_away = powerplay["awayValue"]
        pp_home = powerplay["homeValue"]

        hits_away = hits["awayValue"]
        hits_home = hits["homeValue"]

        

        previous_matchup =   f"""
            <table class="team-compare">
            <tr>
                <td class="team left">
                    <a href="javascript:void(0);" class="team-link">
                        <img src="{home_logo}" style="width: 85px">
                    </a>
                </td>
                <th>vs</th>
                <td class="team right">
                    <a href="javascript:void(0);" class="team-link">                
                        <img src="{away_logo}" style="width: 85px">
                    </a>
                </td>
            </tr>
            <tr>
                <td class="team left">{home_score}</td>
                <th>Score</th>
                <td class="team right">{away_score}</td>
            </tr>
            <tr>
                <td class="team left">{home_sog}</td>
                <th>SOG</th>
                <td class="team right">{away_sog}</td>
            </tr>

            <tr>
                <td class="team left">{home_svpct}</td>
                <th>S%</th>
                <td class="team right">{away_svpct}</td>
            </tr>                         
            <tr>
                <td class="team left">{faceoff_home}</td>
                <th>FO%</th>
                <td class="team right">{faceoff_away}</td>
            </tr>
                                    
            <tr>
                <td class="team left">{pp_home}</td>
                <th>PP</th>
                <td class="team right">{pp_away}</td>            
            </tr>                                     
            <tr>
                <td class="team left">{hits_home}</td>
                <th>Hits</th>
                <td class="team right">{hits_away}</td>            
            </tr> 
                  
            </table>         
            """   
        date_str = f"""
                <span> On {date_str} ({game['result']})</span>
                <a href={game["gamecenterURL"]} target="_blank" rel="noopener noreferrer" class="recap-link">                
                <span class="material-symbols-outlined">
                    open_in_new
                </span></a> <br>
                """
    return previous_matchup, date_str 

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

