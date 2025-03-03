from modules.fetch_nhl_api import get_logo
import pandas as pd

__all__ =['build_playoffs_race_table',]
def build_playoffs_race_table(team_info,standings_data):
    # Extract standings by division
    standings_list = []
    team_conference = team_info.get("team_conference")
    for team in standings_data.get("standings", []):
        if team['conferenceName'] == team_conference:
            team_logo = get_logo(team.get('teamAbbrev', {}).get("default"))
            team_logo_html = f"""<img src="{team_logo}" width="30">"""
            playoffs = team['wildcardSequence']
            if playoffs < 1:
                standings_list.append({
                    "Rank": f"<b>{team['divisionAbbrev']}{team['divisionSequence']}</b>",
                    "Team":  team_logo_html,
                    "GP":  f"<b>{team['gamesPlayed']}</b>",
                    "W":  f"<b>{team['wins']}</b>",
                    "L":  f"<b>{team['losses']}</b>",
                    "OTL":  f"<b>{team['otLosses']}</b>",
                    "PTS":  f"<b>{team['points']}</b>",
                    "P%":  f"<b>{round(team['pointPctg'],2)}</b>",  # Regular-time wins
                    "points_rank": team['points']
            })
            elif playoffs > 2:
                standings_list.append({
                "Rank": f"{team['divisionAbbrev']}{team['divisionSequence']}",
                "Team":  team_logo_html,
                "GP": team["gamesPlayed"],
                "W": team["wins"],
                "L": team["losses"],
                "OTL": team["otLosses"],
                "PTS": team["points"],
                "P%": round(team['pointPctg'],2),  # Regular-time wins
                "points_rank": team['points'],
                })
        # Extract Wild card spot:

            elif playoffs == 2: #and team['divisionName'] != team_division:
                team_logo = get_logo(team.get('teamAbbrev', {}).get("default"))
                team_logo_html = f"""<img src="{team_logo}" width="30">"""
                standings_list.append({
                    "Rank": f"<b> WC2 </b>",
                    "Team":  team_logo_html,
                    "GP":  f"<b>{team['gamesPlayed']}</b>",
                    "W":  f"<b>{team['wins']}</b>",
                    "L":  f"<b>{team['losses']}</b>",
                    "OTL":  f"<b>{team['otLosses']}</b>",
                    "PTS":  f"<b>{team['points']}</b>",
                    "P%":  f"<b>{round(team['pointPctg'],2)}</b>",  # Regular-time wins
                    "points_rank": team['points']
                })
            elif playoffs == 1: #and team['divisionName'] != team_division:
                team_logo = get_logo(team.get('teamAbbrev', {}).get("default"))
                team_logo_html = f"""<img src="{team_logo}" width="30">"""
                standings_list.append({
                    "Rank": f"<b> WC1 </b>",
                    "Team":  team_logo_html,
                    "GP":  f"<b>{team['gamesPlayed']}</b>",
                    "W":  f"<b>{team['wins']}</b>",
                    "L":  f"<b>{team['losses']}</b>",
                    "OTL":  f"<b>{team['otLosses']}</b>",
                    "PTS":  f"<b>{team['points']}</b>",
                    "P%":  f"<b>{round(team['pointPctg'],2)}</b>",  # Regular-time wins
                    "points_rank": team['points']
                })

    # Convert to DataFrame
    df_div_standings = pd.DataFrame(standings_list)

    #print(df_div_standings)
    # Sort by division and points
    df_div_standings = df_div_standings.sort_values(by=[ "points_rank"], ascending=[ False])
    # Extract only the first 8 columns
    columns_to_display = ["Rank", "Team", "GP", "W", "L", "OTL", "PTS", "P%"]

    # Filter the DataFrame to only include those columns
    df_div_standings = df_div_standings[columns_to_display]

    html_standings_table = df_div_standings.to_html(escape=False, index=False)
    return html_standings_table
    