from modules.fetch_nhl_api import get_logo
import pandas as pd

__all__ = ['team_summary','get_special_teams','generate_team_summary_table']
def team_summary(team_abbr,standings_data):
  team_summary_list = []
  if team_abbr != None:
    # Extract the standings data
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
          points_pct =  team.get('pointPctg') or 0

          l10Wins = team['l10Wins']  # Last 10 Wins
          l10Loss = team['l10Losses']
          l10OTL = team['l10OtLosses']

          l10 = f"{l10Wins}-{l10Loss}-{l10OTL}"
          l10_html = f"""<div class="spoiler-wrapper"><button class="toggle-spoiler"><span class="material-symbols-outlined">visibility</span></button><span class="hide-spoiler">{l10}</span></div>"""

          streak_cnt = team.get('streakCount') or "-"
          streak_type =  team.get('streakCode') or "-"

          streak = f"{streak_type}{streak_cnt}"        
          streak_html = f"""<div class="spoiler-wrapper"><button class="toggle-spoiler"><span class="material-symbols-outlined">visibility</span></button><span class="hide-spoiler">{streak}</span></div>"""

          nhl_rank = team['leagueSequence']
          division_rank = ordinal(team['divisionSequence'])
          division_name = team['divisionName']
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
              "Streak": streak_html,
              "Div Rank":  division_rank,
              "Div Name": division_name,
              "Div Rank Pct": rank_to_pct(team['divisionSequence'], 8),
              "Conf Rank": ordinal(team['conferenceSequence']),
              "Conf Name": team['conferenceName'],
              "Conf Rank Pct": rank_to_pct(team['conferenceSequence'],16),
          })

    return team_summary_list
def generate_team_summary_table(team_summary_list):
  # Append the extracted data into a list
  # Convert to DataFrame
  df_team_summary = pd.DataFrame(team_summary_list)

  # Extract only the first 8 columns
  columns_to_display = ["NHL Rank", "GP", "PTS","W", "L", "OTL", "P%","L10","Streak"]

  # Filter the DataFrame to only include those columns
  df_team_summary = df_team_summary[columns_to_display]

  html_team_summary = df_team_summary.to_html(classes="teams-table", escape=False, index=False)
  return html_team_summary

def get_special_teams(all_teams_summary_data,team_name):
    #Special teams
  teams = all_teams_summary_data["data"]
  idx = next(
      (i for i, t in enumerate(teams)
      if team_name in t["teamFullName"]),
      None
  )

  if idx is None:
      # team not found
      print(f"Warning: team containing '{team_name}' not found!")
      pk_pct = 0
      pp_pct = 0
  else:
    pk_pct = teams[idx]["penaltyKillPct"] 
    pp_pct = teams[idx]["powerPlayPct"] 
  # Rank
  pp_values = sorted(
    (t["powerPlayPct"] for t in teams),
    reverse=True
  )

  pp_rank_unformatted = pp_values.index(pp_pct) + 1
  pp_rank = ordinal(pp_rank_unformatted)

  pk_values = sorted(
    (t["penaltyKillPct"] for t in teams),
    reverse=True
  )
  pk_rank_unformatted = pk_values.index(pk_pct) + 1
  pk_rank = ordinal(pk_rank_unformatted)

  special_teams = {
    "PP%": f"{pp_pct*100:.2f}%",
    "PK%": f"{pk_pct*100:.2f}%",
    "PP Rank": pp_rank,
    "PK Rank": pk_rank,
    "PP Rank Pct": rank_to_pct(pp_rank_unformatted, 32),
    "PK Rank Pct": rank_to_pct(pk_rank_unformatted, 32)
  }
  return special_teams

def ordinal(n: int) -> str:
    if 11 <= (n % 100) <= 13:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"

def rank_to_pct(rank, max_rank):
    return round((max_rank - rank) / (max_rank - 1) * 100, 1)