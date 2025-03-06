from modules.fetch_nhl_api import get_logo
import pandas as pd

__all__ =['build_playoffs_race_table','get_standings','format_team_standings','bold']
def build_playoffs_race_table(team_info,standings_data):
    # Extract standings by division
    standings_list = []
    team_conference = team_info.get("team_conference")
    for team in standings_data.get("standings", []):
        if team['conferenceName'] == team_conference:
            playoffs = team['wildcardSequence']
            team_stats = get_standings(team)
            formatted_stats = format_team_standings(team_stats,playoffs)
            standings_list.append(formatted_stats)

    # Convert to DataFrame
    df_div_standings = pd.DataFrame(standings_list)

    #print(df_div_standings)
    # Sort by division and points
    df_div_standings = df_div_standings.sort_values(by=['points_rank'], ascending=[ False])
    # Extract only the first 8 columns
    columns_to_display = ["Rank", "Team", "GP", "PTS", "W", "L", "OTL", "P%"]

    # Filter the DataFrame to only include those columns
    df_div_standings = df_div_standings[columns_to_display]

    html_standings_table = df_div_standings.to_html(escape=False, index=False)
    return html_standings_table
    
def get_standings(team):
    """
    Returns a dictionary with the standings data for a given team.
    
    :param team: Dictionary containing team data.
    :return: Dictionary with raw standings data.
    """
    team_logo = get_logo(team.get('teamAbbrev', {}).get("default"))
    team_logo_html = f"""<a href="javascript:void(0);" class="team-link"><img src="{team_logo}" width="30"></a>"""

    return {
        "Rank": f"{team['divisionAbbrev']}{team['divisionSequence']}",
        "Team": team_logo_html,
        "GP": team["gamesPlayed"],        
        "PTS": team["points"],
        "W": team["wins"],
        "L": team["losses"],
        "OTL": team["otLosses"],
        "P%": round(team["pointPctg"], 2),
        "points_rank": team["points"],
    }

def format_team_standings(standings,playoffs):
    """
    Applies formatting to standings based on conditions.

    :param standings: List of team standings dictionaries.
    :param bold_condition: Function that returns True if a row should be bold.
    :param label_change_condition: Function that modifies a specific label.
    :return: List of formatted standings dictionaries.
    """
    
    # Apply bold condition
    if playoffs < 3:
        standings = {k: bold(v) if k != "points_rank" else v for k, v in standings.items()}  # Apply bold to all fields

    # Apply label change condition
    if playoffs == 2:
        standings["Rank"] = f"<b>WC2</b>"  # Change label
    if playoffs == 1:
        standings["Rank"] = f"<b>WC1</b>"  # Change label


    return standings

def bold(text):
    return f"<b>{text}</b>"  # Change formatting as needed (Markdown, HTML, etc.)
