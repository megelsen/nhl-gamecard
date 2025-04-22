from modules.fetch_nhl_api import get_logo
import pandas as pd

__all__ = ['colorize_result', 'build_records_table',]
# Function to apply background color and return formatted game detail
def colorize_result(game):
    result = game['result']
    game_venue = game['game_venue']
    home_score = game['home_score']
    away_score = game['away_score']
    game_date = game['game_date'].strftime('%m-%d-%y')

    # Formating the game detail string
    game_detail = f"{game_venue} {home_score} - {away_score}"
    background_padding_width = 9
    background_padding_height = 2
    background_padding_style = f"padding: {background_padding_height}px {background_padding_width}px"
    # Apply background color based on the result
    if result == 'W':
        return f'<span style="background-color: green; color: white; {background_padding_style}; border-radius: 2px;">{game_detail} </span>'
    elif result == 'OTL':
        return f'<span style="background-color: #EDB120; color: black; {background_padding_style};border-radius: 2px;">{game_detail} </span>'
    elif result == 'L':
        return f'<span style="background-color: #D95319; color: white; {background_padding_style};border-radius: 2px;">{game_detail} </span>'
    else:
      return f'<span> {game_date}' # Default return if something else
    
def build_records_table(sorted_opponents):
    max_games_E = 0
    max_games_W = 0
    data_eastern = []
    data_western = []
    game_detail = []
    for opponent, games in sorted_opponents:
        games = [game for game in games if game.get('game_type') == 2]
        if not games:
            continue
        opponent_logo = get_logo(games[0]['opponent_abr'])  # Assuming all games in the list have the same opponent_abr
        row = [f'<a href="javascript:void(0);" class="team-link"><img src="{opponent_logo}" width="50"></a>']
        opponent_conference = get_conference_abbreviation(games[0]['opponent_abr'])
        # Add the game details with colored background for the result
        for i, game in enumerate(games, start=1):
            # Get the formatted game detail with background color
            game_detail = colorize_result(game)
            if "video" in game["recap_URL"]:
                game_detail_recap_link = f'<a href={game["recap_URL"]} target="_blank" rel="noopener noreferrer" class="recap-link">{game_detail}</a>'
            else:
                game_detail_recap_link = game_detail
            row.append(game_detail_recap_link)            

            # Split Eastern and Western
            if opponent_conference == "E":
                max_games_E = max(max_games_E, len(games))               
            elif opponent_conference == "W":
                max_games_W = max(max_games_W, len(games))
                    # Split Eastern and Western
        if opponent_conference == "E":            
            data_eastern.append(row)
        elif opponent_conference == "W":            
            data_western.append(row)
    
    columns_E = ['vs'] + [f'Game {i}' for i in range(1, max_games_E + 1)]
    columns_W = ['vs'] + [f'Game {i}' for i in range(1, max_games_W + 1)]

    
    # Create the DataFrame
    df_record_table_eastern = pd.DataFrame(data_eastern, columns=columns_E)
    record_table_eastern = df_record_table_eastern.applymap(lambda x: " " if x is None else x)

    df_record_table_western = pd.DataFrame(data_western, columns=columns_W)
    record_table_western = df_record_table_western.applymap(lambda x: " " if x is None else x)
    # convert to html element the logos as a row of images
    #record_table_html = df_record_table.to_html(escape=False,index=False)
    return record_table_eastern, record_table_western
    
def get_conference_abbreviation(team_abbr):
    
    nhl_team_conferences = {
        "ANA": "W",
        "BOS": "E",
        "BUF": "E",
        "CAR": "E",
        "CBJ": "E",
        "CGY": "W",
        "CHI": "W",
        "COL": "W",
        "DAL": "W",
        "DET": "E",
        "EDM": "W",
        "FLA": "E",
        "LAK": "W",
        "MIN": "W",
        "MTL": "E",
        "NSH": "W",
        "NJD": "E",
        "NYI": "E",
        "NYR": "E",
        "OTT": "E",
        "PHI": "E",
        "PIT": "E",
        "SEA": "W",
        "SJS": "W",
        "STL": "W",
        "TBL": "E",
        "TOR": "E",
        "UTA": "W",
        "VAN": "W",
        "VGK": "W",
        "WPG": "W",
        "WSH": "E"
    }

    conference = nhl_team_conferences[team_abbr]
    return conference

