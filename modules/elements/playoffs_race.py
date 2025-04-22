from modules.fetch_nhl_api import get_logo
import pandas as pd

__all__ =['build_playoffs_race_table','get_standings','format_team_standings','bold','playoff_bracket','number_to_letter']
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
    columns_to_display = ["Team", "Rank", "GP", "PTS", "W", "L", "OTL", "P%"]

    # Filter the DataFrame to only include those columns
    df_div_standings = df_div_standings[columns_to_display]

    html_standings_table = df_div_standings.to_html(classes="teams-table", escape=False, index=False)
    return html_standings_table
    
def get_standings(team):
    """
    Returns a dictionary with the standings data for a given team.
    
    :param team: Dictionary containing team data.
    :return: Dictionary with raw standings data.
    """
    team_logo = get_logo(team.get('teamAbbrev', {}).get("default"))
    team_logo_html = f"""<a href="javascript:void(0);" class="team-link"><img src="{team_logo}" width="50px"></a>"""

    return {        
        "Team": team_logo_html,
        "Rank": f"{team['divisionAbbrev']}{team['divisionSequence']}",
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

def playoff_bracket(playoff_data):
    eastern_matchups = []
    western_matchups = []
    current_round = playoff_data['currentRound'] - 1
    # First round: 0-3 in East, 4-7 in West
    current_round_matchups = playoff_data['rounds'][current_round]
    # Eastern Rounds:
    for series_nr in range(8):
        if series_nr < 4:
            eastern_matchups.append = series_nr
        elif series_nr >= 4:
            western_matchups.append = series_nr

    return current_round_matchups

def number_to_letter(n):
    if 0 <= n <= 25:
        return chr(ord('A') + n)
    else:
        return "Invalid input"