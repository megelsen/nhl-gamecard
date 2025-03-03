__all__ = ['find_top_scorer']

def find_top_scorer(team_stats_data):
    # Initialize a variable to track the player with the most points
    top_scorer_info = {}
    max_points = -1

    # Iterate through the list of players to find the one with the most points
    for skater in team_stats_data['skaters']:
        if skater['points'] > max_points:
            max_points =  skater['points']
            top_scorer_info = {
                    "name": skater['firstName']['default'] + " " + skater['lastName']['default'],
                    "points": skater['points'],
                    "goals": skater['goals'],
                    "assists": skater['assists'],
                    "headshot_url": skater['headshot'],
                    "headshot_html": f"""<img src="{skater['headshot']}">"""
                }
    return top_scorer_info