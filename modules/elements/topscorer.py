import pandas as pd
from modules.fetch_nhl_api import get_player_stats

__all__ = ['find_top_scorer','find_pointleaders','find_goalleaders','find_assistleaders','build_leaders_table','get_skater_info','get_goalies','build_goalie_table','get_stats_from_playerID']

def find_top_scorer(team_stats_data):
    # Initialize a variable to track the player with the most points
    top_scorer_info = {}
    # Check if summary is from playoffs (gameType 3) or regular season (gameType 2)
    #Sort skaters by points in descending order
    sorted_skaters = sorted(team_stats_data['skaters'], key=lambda skater: skater['points'], reverse=True)
    # Iterate through the list of players to find the one with the most points
    top_scorer = sorted_skaters[0] if len(sorted_skaters) is not 0 else None
    top_scorer_info = get_skater_info(top_scorer) if top_scorer is not None else None
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

    if leaders is not None:
        for skater in leaders:            
            leader_info = {            
                " ": skater['headshot_scalable_html'],
                "Player": f"<b>{skater['name']}</b> <br> #{skater['sweaterNumber']} {skater['position']}",                
                "GP": skater['games_played'],
                category_header: skater[category_key],
            }
            leaders_list.append(leader_info)

        # Convert to DataFrame
        df_leaders = pd.DataFrame(leaders_list)
        html_leaders_table = df_leaders.to_html(classes="leaders-table", escape=False, index=False)
    else:
        html_leaders_table = [f"""
                            <span> No player info available </span>
                            """]
    return html_leaders_table

def get_skater_info(skater):
    
    position_code =  skater.get("position") or skater.get("positionCode")
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

def get_goalies(team_stats_data):
    goalies = []
    sorted_goalies = sorted(team_stats_data['goalies'], key=lambda goalie: goalie['wins'], reverse=True)
    for goalie in sorted_goalies:
       goalies.append(get_goalie_info(goalie))
    return goalies
def get_goalie_info(goalie):
   
    player_basic_stats = {
            "name": goalie['firstName']['default'] + " " + goalie['lastName']['default'],
            "points": goalie['points'],
            "goals": goalie['goals'],
            "assists": goalie['assists'],
            "wins": goalie['wins'],
            "goalsAgainstAverage": round(goalie['goalsAgainstAverage'],2),
            "savePercentage": round(goalie['savePercentage'],2),           
            "shutouts": goalie['shutouts'],
            "games_played": goalie['gamesPlayed'],
            "headshot_url": goalie['headshot'],
            "headshot_html": f"""<img src="{goalie['headshot']}">""",
            "headshot_scalable_html": f"""<img class="content_scalable" src="{goalie['headshot']}">""",
            "position": 'G',
            "playerID": goalie['playerId'],
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
    goalie_info = {**player_basic_stats, **player_advanced_stats}
    return goalie_info
    
def build_goalie_table(goalie):
    goalie_fields = []
    goalie_fields.append({
            "GP": goalie['games_played'],
            "W": goalie['wins'],
            "SO": goalie['shutouts'],
            "S%": goalie['savePercentage'],
            "GAA": goalie['goalsAgainstAverage'],
          })
          # Append the extracted data into a list
          # Convert to DataFrame
    df_goalie_fields = pd.DataFrame(goalie_fields)

    # Extract only the first 8 columns
    columns_to_display = ["GP", "W", "SO","S%", "GAA"]

    # Filter the DataFrame to only include those columns
    df_goalie_fields = df_goalie_fields[columns_to_display]

    html_goalie_fields = df_goalie_fields.to_html(classes="teams-table", escape=False, index=False)
    return html_goalie_fields

def get_stats_from_playerID(skater):
    position_code =  skater.get("position")
    if position_code in ['R', 'L']:
        position_code += 'W'

    player_stats = {
            "name": skater['firstName']['default'] + " " + skater['lastName']['default'],
            "points": skater['featuredStats']['regularSeason']['subSeason']['points'],
            "goals": skater['featuredStats']['regularSeason']['subSeason']['goals'],
            "assists": skater['featuredStats']['regularSeason']['subSeason']['assists'],
            "games_played": skater['featuredStats']['regularSeason']['subSeason']['gamesPlayed'],
            "headshot_url": skater['headshot'],
            "headshot_html": f"""<img src="{skater['headshot']}">""",
            "headshot_scalable_html": f"""<img class="content_scalable" src="{skater['headshot']}">""",
            "position": position_code,
            "playerID": skater['playerId'],

            "sweaterNumber": skater['sweaterNumber'],
            "heroImage_url": skater['heroImage'],
            "birth_country": skater['birthCountry'],
            "shoots": skater['shootsCatches'],
            "height_in": skater['heightInInches'],
            "height_cm": skater['heightInCentimeters'],
            "birthdate": skater['birthDate'],
            "draft_details": skater.get('draftDetails', 'undrafted'),
            "career_stats": skater['careerTotals']['regularSeason'],
    }
    
    return player_stats