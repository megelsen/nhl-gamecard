import pandas as pd

__all__ = ['find_top_scorer','find_pointleaders','find_goalleaders','find_assistleaders','build_leaders_table']

def find_top_scorer(team_stats_data):
    # Initialize a variable to track the player with the most points
    top_scorer_info = {}
    #Sort skaters by points in descending order
    sorted_skaters = sorted(team_stats_data['skaters'], key=lambda skater: skater['points'], reverse=True)
    # Iterate through the list of players to find the one with the most points
    top_scorer = sorted_skaters[0]
    top_scorer_info = {
            "name": top_scorer['firstName']['default'] + " " + top_scorer['lastName']['default'],
            "points": top_scorer['points'],
            "goals": top_scorer['goals'],
            "assists": top_scorer['assists'],
            "games_played": top_scorer['gamesPlayed'],
            "headshot_url": top_scorer['headshot'],
            "headshot_html": f"""<img src="{top_scorer['headshot']}">"""
        }
    return top_scorer_info

def find_pointleaders(team_stats_data,n):
    # Sort skaters by points in descending order
    sorted_skaters = sorted(team_stats_data['skaters'], key=lambda skater: skater['points'], reverse=True)
    # Get the top 10 skaters
    point_leaders = []
    for skater in sorted_skaters[:n]:  # Slice to get the top 10
        point_leaders.append({
            "name": skater['firstName']['default'] + " " + skater['lastName']['default'],
            "points": skater['points'],
            "goals": skater['goals'],
            "assists": skater['assists'],
            "games_played": skater['gamesPlayed'],
            "headshot_url": skater['headshot'],
            "headshot_html": f"""<img src="{skater['headshot']}">"""
        })
    return point_leaders

def find_goalleaders(team_stats_data,n):
    # Sort skaters by points in descending order
    sorted_skaters = sorted(team_stats_data['skaters'], key=lambda skater: skater['goals'], reverse=True)
    # Get the top 10 skaters
    goal_leaders = []
    for skater in sorted_skaters[:n]:  # Slice to get the top 10
        goal_leaders.append({
            "name": skater['firstName']['default'] + " " + skater['lastName']['default'],
            "points": skater['points'],
            "goals": skater['goals'],
            "assists": skater['assists'],
            "games_played": skater['gamesPlayed'],
            "headshot_url": skater['headshot'],
            "headshot_html": f"""<img src="{skater['headshot']}">"""
        })
    return goal_leaders

def find_assistleaders(team_stats_data,n):
    # Sort skaters by points in descending order
    sorted_skaters = sorted(team_stats_data['skaters'], key=lambda skater: skater['assists'], reverse=True)
    # Get the top 10 skaters
    assist_leaders = []
    for skater in sorted_skaters[:n]:  # Slice to get the top 10
        assist_leaders.append({
            "name": skater['firstName']['default'] + " " + skater['lastName']['default'],
            "points": skater['points'],
            "goals": skater['goals'],
            "assists": skater['assists'],
            "games_played": skater['gamesPlayed'],
            "headshot_url": skater['headshot'],
            "headshot_html": f"""<img src="{skater['headshot']}">"""
        })
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
            " ": skater['headshot_html'],
            "Player": skater['name'],
            category_header: skater[category_key],
            "GP": skater['games_played'],
        }
        leaders_list.append(leader_info)

    # Convert to DataFrame
    df_leaders = pd.DataFrame(leaders_list)
    html_leaders_table = df_leaders.to_html(classes="leaders-table", escape=False, index=False)
    return html_leaders_table