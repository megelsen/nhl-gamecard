from modules.fetch_nhl_api import get_logo
import pandas as pd

__all__ = ['team_summary', 'get_special_teams', 'generate_team_summary_table']


def team_summary(team_abbr, standings_data):
  if not team_abbr or not isinstance(standings_data, dict):
    return []

  standings = standings_data.get("standings", [])
  if not standings:
    return []

  team_summary_list = []

  for team in standings:
    if team.get("teamAbbrev", {}).get("default") != team_abbr:
      continue

    games_played = team.get("gamesPlayed", 0)

    if not games_played:
      return [{
        "NHL Rank": "-",
        "GP": 0,
        "PTS": "-",
        "W": "-",
        "L": "-",
        "OTL": "-",
        "P%": "-",
        "L10": "-",
        "Streak": "-",
      }]

    points_pct = team.get("pointPctg")
    l10 = (
      f"{team.get('l10Wins', 0)}-"
      f"{team.get('l10Losses', 0)}-"
      f"{team.get('l10OtLosses', 0)}"
    )

    streak = (
      f"{team.get('streakCode', '-')}"
      f"{team.get('streakCount', '-')}"
    )

    team_summary_list.append({
      "NHL Rank": team.get("leagueSequence", "-"),
      "GP": games_played,
      "PTS": team.get("points", 0),
      "W": team.get("wins", 0),
      "L": team.get("losses", 0),
      "OTL": team.get("otLosses", 0),
      "P%": f"<b>{round(points_pct, 2)}</b>" if points_pct is not None else "-",
      "L10": l10,
      "Streak": streak,
    })

    break

  return team_summary_list


def generate_team_summary_table(team_summary_list):
  columns_to_display = [
    "NHL Rank", "GP", "PTS", "W", "L", "OTL", "P%", "L10", "Streak"
  ]

  df_team_summary = pd.DataFrame(team_summary_list)

  if df_team_summary.empty:
    return "<p>No team summary data available.</p>"

  for column in columns_to_display:
    if column not in df_team_summary:
      df_team_summary[column] = "-"

  df_team_summary = df_team_summary[columns_to_display]

  return df_team_summary.to_html(
    classes="teams-table",
    escape=False,
    index=False
  )


def get_special_teams(all_teams_summary_data, team_name):
  teams = (
    all_teams_summary_data.get("data", [])
    if isinstance(all_teams_summary_data, dict)
    else []
  )

  if not teams or not team_name:
    return {
      "PP%": "-",
      "PK%": "-",
      "PP Rank": "-",
      "PK Rank": "-",
      "PP Rank Pct": "-",
      "PK Rank Pct": "-",
    }

  team = next(
    (team for team in teams if team_name in team.get("teamFullName", "")),
    None
  )

  if team is None:
    return {
      "PP%": "-",
      "PK%": "-",
      "PP Rank": "-",
      "PK Rank": "-",
      "PP Rank Pct": "-",
      "PK Rank Pct": "-",
    }

  pp_pct = team.get("powerPlayPct")
  pk_pct = team.get("penaltyKillPct")

  if pp_pct is None or pk_pct is None:
    return {
      "PP%": "-",
      "PK%": "-",
      "PP Rank": "-",
      "PK Rank": "-",
      "PP Rank Pct": "-",
      "PK Rank Pct": "-",
    }

  pp_values = sorted(
    (t.get("powerPlayPct") for t in teams if t.get("powerPlayPct") is not None),
    reverse=True
  )
  pk_values = sorted(
    (t.get("penaltyKillPct") for t in teams if t.get("penaltyKillPct") is not None),
    reverse=True
  )

  pp_rank_unformatted = pp_values.index(pp_pct) + 1
  pk_rank_unformatted = pk_values.index(pk_pct) + 1

  return {
    "PP%": f"{pp_pct * 100:.2f}%",
    "PK%": f"{pk_pct * 100:.2f}%",
    "PP Rank": ordinal(pp_rank_unformatted),
    "PK Rank": ordinal(pk_rank_unformatted),
    "PP Rank Pct": rank_to_pct(pp_rank_unformatted, len(pp_values)),
    "PK Rank Pct": rank_to_pct(pk_rank_unformatted, len(pk_values)),
  }


def ordinal(n: int) -> str:
  if 11 <= (n % 100) <= 13:
    suffix = "th"
  else:
    suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
  return f"{n}{suffix}"


def rank_to_pct(rank, max_rank):
  if max_rank <= 1:
    return 100.0
  return round((max_rank - rank) / (max_rank - 1) * 100, 1)
