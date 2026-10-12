from modules.fetch_nhl_api import get_boxscore

__all__ = ['build_roster_tables', 'recent_lineups']

RECENT_GAMES = 5
POSITION_GROUPS = [("Goalies", "goalies"), ("Defense", "defensemen"), ("Forwards", "forwards")]
BOXSCORE_GROUPS = ("forwards", "defense", "goalies")
FORWARD_POSITIONS = {"C": "C", "L": "LW", "R": "RW"}


def build_roster_tables(team_abbr, roster_data, team_stats_data, games_by_date):
    """
    Roster tables per position, each split into Lineup / Rotation / Extras based on
    who dressed in the most recent games: {"Goalies": html, "Defense": html, "Forwards": html}
    """
    roster_data = roster_data or {}
    team_stats_data = team_stats_data or {}
    stats_by_id = {p["playerId"]: p for p in team_stats_data.get("skaters", []) + team_stats_data.get("goalies", [])}
    lineups = recent_lineups(team_abbr, games_by_date)

    tables = {}
    for label, roster_key in POSITION_GROUPS:
        players = roster_data.get(roster_key, [])
        is_goalie = roster_key == "goalies"
        groups = group_by_activity(players, lineups)
        rows = []
        for group_label, group_players in groups:
            group_players = sorted(group_players, key=lambda p: sort_key(p, stats_by_id, is_goalie))
            if lineups:
                rows.append(group_row(group_label, is_goalie))
            rows += [player_row(p, stats_by_id.get(p["id"]), is_goalie) for p in group_players]
        tables[label] = roster_table(rows, is_goalie) if rows else "<p>No roster data available.</p>"
    return tables


def recent_lineups(team_abbr, games_by_date, n=RECENT_GAMES):
    """Sets of player IDs that dressed in the team's last `n` completed games, most recent first."""
    completed = sorted(
        (g for g in games_by_date if g.get("home_score") is not None and g.get("away_score") is not None),
        key=lambda g: g["game_date"],
        reverse=True,
    )[:n]
    lineups = []
    for game in completed:
        boxscore = get_boxscore(game["game_id"]) or {}
        by_team = boxscore.get("playerByGameStats", {})
        side = "homeTeam" if boxscore.get("homeTeam", {}).get("abbrev") == team_abbr else "awayTeam"
        dressed = {p["playerId"] for group in BOXSCORE_GROUPS for p in by_team.get(side, {}).get(group, [])}
        if dressed:
            lineups.append(dressed)
    return lineups


def group_by_activity(players, lineups):
    if not lineups:
        return [("Roster", players)]
    last_game = lineups[0]
    recent = set().union(*lineups)
    groups = [
        ("Lineup", [p for p in players if p["id"] in last_game]),
        ("Rotation", [p for p in players if p["id"] in recent and p["id"] not in last_game]),
        ("Extras", [p for p in players if p["id"] not in recent]),
    ]
    return [(label, group) for label, group in groups if group]


def sort_key(player, stats_by_id, is_goalie):
    stats = stats_by_id.get(player["id"]) or {}
    primary = stats.get("wins", 0) if is_goalie else stats.get("points", 0)
    return (-primary, player.get("sweaterNumber") or 99)


def player_row(player, stats, is_goalie):
    name = f"{player['firstName']['default']} {player['lastName']['default']}"
    position = "" if is_goalie else FORWARD_POSITIONS.get(player.get("positionCode"), "")
    position_html = f"<br><span class=\"roster-position\">{position}</span>" if position else ""
    cells = [
        f'<img class="roster-headshot" src="{player.get("headshot", "")}" alt="" data-player-id="{player["id"]}">',
        f"<b>{name}</b>{position_html}",
        player.get("sweaterNumber", "-"),
    ]
    if not stats:
        cells += ["-"] * 4
    elif is_goalie:
        cells += [stats.get("gamesPlayed", 0), stats.get("wins", 0), f"{stats.get('goalsAgainstAverage') or 0:.2f}", f"{stats.get('savePercentage') or 0:.3f}"]
    else:
        cells += [stats.get(key, 0) for key in ("gamesPlayed", "goals", "assists", "points")]
    return "<tr>" + "".join(f"<td>{c}</td>" for c in cells) + "</tr>"


def columns(is_goalie):
    return ["", "Player", "Nr", "GP"] + (["W", "GAA", "S%"] if is_goalie else ["G", "A", "P"])


def group_row(label, is_goalie):
    return f'<tr class="roster-group"><th colspan="{len(columns(is_goalie))}">{label}</th></tr>'


def roster_table(rows, is_goalie):
    header = "".join(f"<th>{c}</th>" for c in columns(is_goalie))
    return (
        '<table class="roster-table">'
        f"<thead><tr>{header}</tr></thead>"
        f"<tbody>{''.join(rows)}</tbody>"
        "</table>"
    )
