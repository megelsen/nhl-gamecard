from modules.fetch_nhl_api import get_logo
import pandas as pd

__all__ =['build_playoffs_race_table','get_standings','format_team_standings','bold','playoff_bracket','current_round_matchups']
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
        "P%": round(team.get('pointPctg') or 0, 2),
        "points_rank": team["points"],
    }

def format_team_standings(standings,playoffs,bold_on=1):
    """
    Applies formatting to standings based on conditions.

    :param standings: List of team standings dictionaries.
    :param bold_condition: Function that returns True if a row should be bold.
    :param label_change_condition: Function that modifies a specific label.
    :return: List of formatted standings dictionaries.
    """
        # Apply label change condition
    if playoffs == 2:
        standings["Rank"] = f"WC2"  # Change label
    if playoffs == 1:
        standings["Rank"] = f"WC1"  # Change label

    
    # Apply bold condition
    if playoffs < 3 and bold_on == 1:
        standings = {k: bold(v) if k != "points_rank" else v for k, v in standings.items()}  # Apply bold to all fields




    return standings

def bold(text):
    return f"<b>{text}</b>"  # Change formatting as needed (Markdown, HTML, etc.)

def playoff_bracket(playoff_data):

    current_round = playoff_data['currentRound']
    bracket_dict = {}

    for i in range(current_round):
        round_data = playoff_data['rounds'][i]
        round_label = f"Round {i + 1}"
        western, eastern, finals = current_round_matchups(round_data)

        if finals:
            bracket_dict[round_label] = {"Finals": finals}
        else:
            bracket_dict[round_label] = {
                "Eastern": eastern,
                "Western": western
            }

    return bracket_dict

def current_round_matchups(current_round_data):
    eastern_matchups = []
    western_matchups = []
    finals_matchup = []
    # Find round number & number of matchups:
    # Max 4 rounds, nr of mathcups is given by: 2^3, 2^2, 2^1, 2^1
    nr_matchups = len(current_round_data['series'])
    for series_nr in range(nr_matchups):
        top_seed = current_round_data['series'][series_nr]['topSeed']
        bottom_seed = current_round_data['series'][series_nr]['bottomSeed']

        if nr_matchups == 1:
            finals_matchup.append([top_seed, bottom_seed])
        elif series_nr < nr_matchups/2:           
            eastern_matchups.append([top_seed, bottom_seed])
        else:
            western_matchups.append([top_seed, bottom_seed])
    
    return [western_matchups, eastern_matchups, finals_matchup]
