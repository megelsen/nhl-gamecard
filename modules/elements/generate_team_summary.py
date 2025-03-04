from modules.fetch_nhl_api import get_logo
import pandas as pd

__all__ = ['team_summary',]
def team_summary(team_abbr,standings_data):
  team_summary_list = []
  # Extract the standings data for the Winnipeg Jets (WPG)
  for team in standings_data['standings']:
    if team['teamAbbrev']['default'] == team_abbr:
        # Extract relevant data
        team_name = team['teamName']['default']
        logo = get_logo(team_abbr)
        team_logo_html = f"""<img src="{logo}" width="50">"""
        games_played = team['gamesPlayed']
        wins = team['wins']
        losses = team['losses']
        ot_losses = team['otLosses']
        points = team['points']
        points_pct = team['pointPctg']

        l10Wins = team['l10Wins']  # Last 10 Wins
        l10Loss = team['l10Losses']
        l10OTL = team['l10OtLosses']

        l10 = f"{l10Wins}-{l10Loss}-{l10OTL}"
        streak_cnt = team['streakCount']
        streak_type = team['streakCode']

        streak = f"{streak_type}{streak_cnt}"

        nhl_rank = team['leagueSequence']

        team_summary_list.append({
            "NHL Rank": nhl_rank,
            #"Team":  team_logo_html,
            "GP":  games_played,
            "PTS":  points,
            "W":  wins,
            "L": losses,
            "OTL":  ot_losses,
            "P%":  f"<b>{round(points_pct,2)}</b>",  # Regular-time wins
            "L10": l10,
            "Streak": streak,
        })
        # Append the extracted data into a list
        # Convert to DataFrame
  df_team_summary = pd.DataFrame(team_summary_list)

  # Extract only the first 8 columns
  columns_to_display = ["NHL Rank", "GP", "PTS","W", "L", "OTL", "P%","L10","Streak"]

  # Filter the DataFrame to only include those columns
  df_team_summary = df_team_summary[columns_to_display]

  html_team_summary = df_team_summary.to_html(escape=False, index=False)
  return html_team_summary