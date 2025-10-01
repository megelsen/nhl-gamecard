import pandas as pd
from modules.fetch_nhl_api import get_player_stats

__all__ = ['find_top_scorer','find_pointleaders','find_goalleaders','find_assistleaders','build_leaders_table','get_skater_info']

def find_top_scorer(team_stats_data):
    # Initialize a variable to track the player with the most points
    top_scorer_info = {}
    # Check if summary is from playoffs (gameType 3) or regular season (gameType 2)
    #Sort skaters by points in descending order
    sorted_skaters = sorted(team_stats_data['skaters'], key=lambda skater: skater['points'], reverse=True)
    # Iterate through the list of players to find the one with the most points
    top_scorer = sorted_skaters[0]
    top_scorer_info = get_skater_info(top_scorer)    
    return top_scorer_info

def find_pointleaders(team_stats_data,n):
    # Sort skaters by points in descending order
    sorted_skaters = sorted(team_stats_data['skaters'], key=lambda skater: skater['points'], reverse=True)
    # Get the top 10 skaters
    point_leaders = []
    for skater in sorted_skaters[:n]:  # Slice to get the top 10
        skater_info = get_skater_info(skater)
        point_leaders.append(skater_info)
    return point_leaders

def find_goalleaders(team_stats_data,n):
    # Sort skaters by points in descending order
    sorted_skaters = sorted(team_stats_data['skaters'], key=lambda skater: skater['goals'], reverse=True)
    # Get the top 10 skaters
    goal_leaders = []
    for skater in sorted_skaters[:n]:  # Slice to get the top 10
        skater_info = get_skater_info(skater)
        goal_leaders.append(skater_info)
    return goal_leaders

def find_assistleaders(team_stats_data,n):
    # Sort skaters by points in descending order
    sorted_skaters = sorted(team_stats_data['skaters'], key=lambda skater: skater['assists'], reverse=True)
    # Get the top 10 skaters
    assist_leaders = []
    for skater in sorted_skaters[:n]:  # Slice to get the top 10
       skater_info = get_skater_info(skater)
       assist_leaders.append(skater_info)
    return assist_leaders

def build_leaders_table(leaders,category):
    # Category: G, A, or P
    leaders_list = []
    if category == 'G':
        category_header = "Goals"
        category_key = 'goals'
    elif category == 'A':
         category_header = "Assists"
         category_key = 'assists'
    else:
        category_header = "Points"
        category_key = 'points'    

    for skater in leaders:            
        leader_info = {            
            " ": skater['headshot_scalable_html'],
            "Player": f"<b>{skater['name']}</b> #{skater['sweaterNumber']} {skater['position']}",
            category_header: skater[category_key],
            "GP": skater['games_played'],
        }
        leaders_list.append(leader_info)

    # Convert to DataFrame
    df_leaders = pd.DataFrame(leaders_list)
    html_leaders_table = df_leaders.to_html(classes="leaders-table", escape=False, index=False)
    return html_leaders_table

def get_skater_info(skater):
    
    position_code = skater['positionCode']
    if position_code in ['R', 'L']:
        position_code += 'W'

    player_basic_stats = {
            "name": skater['firstName']['default'] + " " + skater['lastName']['default'],
            "points": skater['points'],
            "goals": skater['goals'],
            "assists": skater['assists'],
            "games_played": skater['gamesPlayed'],
            "headshot_url": skater['headshot'],
            "headshot_html": f"""<img src="{skater['headshot']}">""",
            "headshot_scalable_html": f"""<img class="content_scalable" src="{skater['headshot']}">""",
            "position": position_code,
            "playerID": skater['playerId'],
    }
    player_stats_data = get_player_stats(player_basic_stats["playerID"])
    player_advanced_stats = {       
        "sweaterNumber": player_stats_data['sweaterNumber'],
        "heroImage_url": player_stats_data['heroImage'],
        "birth_country": player_stats_data['birthCountry'],
        "shoots": player_stats_data['shootsCatches'],
        "height_in": player_stats_data['heightInInches'],
        "height_cm": player_stats_data['heightInCentimeters'],
        "birthdate": player_stats_data['birthDate'],
        "draft_details": player_stats_data.get('draftDetails', 'undrafted'),
        "career_stats": player_stats_data['careerTotals']['regularSeason'],
    }
    skater_info = {**player_basic_stats, **player_advanced_stats}
    return skater_info


    
