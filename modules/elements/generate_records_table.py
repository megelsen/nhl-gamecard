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

    # Apply background color based on the result
    if result == 'W':
        return f'<span style="background-color: green; color: white; padding: 2px 4px; border-radius: 2px;">{game_detail} </span>'
    elif result == 'OTL':
        return f'<span style="background-color: #EDB120; color: black; padding: 2px 4px;border-radius: 2px;">{game_detail} </span>'
    elif result == 'L':
        return f'<span style="background-color: #D95319; color: white; padding: 2px 4px;border-radius: 2px;">{game_detail} </span>'
    else:
      return f'<span> {game_date}' # Default return if something else
    
def build_records_table(sorted_opponents):
    max_games = 0
    data = []
    game_detail = []
    for opponent, games in sorted_opponents:
        opponent_logo = get_logo(games[0]['opponent_abr'])  # Assuming all games in the list have the same opponent_abr
        row = [f'<img src="{opponent_logo}" width="50">']

        # Add the game details with colored background for the result
        for i, game in enumerate(games, start=1):
            # Get the formatted game detail with background color
            game_detail = colorize_result(game)
            row.append(game_detail)
        max_games = max(max_games, len(games))
        data.append(row)

    num_games = max(len(games) for _, games in sorted_opponents)
    columns = ['vs'] + [f'Game {i}' for i in range(1, num_games + 1)]

    # Create the DataFrame
    df_record_table = pd.DataFrame(data, columns=columns)
    record_table = df_record_table.applymap(lambda x: " " if x is None else x)
    # convert to html element the logos as a row of images
    #record_table_html = df_record_table.to_html(escape=False,index=False)
    return record_table
    

