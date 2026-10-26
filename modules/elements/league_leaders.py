from html import escape

from modules.fetch_nhl_api import get_logo
from modules.fetch_team_info import get_team_color

__all__ = ['build_league_leaders']

CARD_ROWS = 5
MODAL_ROWS = 15

# (API key, tab label, value format); the card shows the first three, the modal all of them
SKATER_CATEGORIES = [
    ("goals", "Goals", "int"),
    ("assists", "Assists", "int"),
    ("points", "Points", "int"),
    ("plusMinus", "+/-", "signed"),
    ("goalsPp", "PPG", "int"),
    ("goalsSh", "SHG", "int"),
    ("faceoffLeaders", "FO%", "pct"),
    ("penaltyMins", "PIM", "int"),
    ("toi", "TOI", "toi"),
]
GOALIE_CATEGORIES = [
    ("wins", "Wins", "int"),
    ("savePctg", "SV%", "save"),
    ("goalsAgainstAverage", "GAA", "gaa"),
    ("shutouts", "SO", "int"),
]
CARD_CATEGORIES = SKATER_CATEGORIES[:3]


def build_league_leaders(team_abbr, standings_data, skater_leaders, goalie_leaders):
    """
    League leaders as pre-rendered lists: {"card": {label: html}, "modal": {"Skaters": {label: html},
    "Goalies": {label: html}}}. Each row has a stripe in the player's team color.
    """
    colors = team_colors_by_abbrev(standings_data)
    skater_leaders = skater_leaders or {}
    goalie_leaders = goalie_leaders or {}

    def lists(data, categories, rows):
        return {label: leader_list(data.get(key) or [], fmt, rows, team_abbr, colors)
                for key, label, fmt in categories}

    return {
        "card": lists(skater_leaders, CARD_CATEGORIES, CARD_ROWS),
        "modal": {
            "Skaters": lists(skater_leaders, SKATER_CATEGORIES, MODAL_ROWS),
            "Goalies": lists(goalie_leaders, GOALIE_CATEGORIES, MODAL_ROWS),
        },
    }


def team_colors_by_abbrev(standings_data):
    teams = (standings_data or {}).get("standings", [])
    return {t["teamAbbrev"]["default"]: get_team_color(t["teamName"]["default"])["primary"] for t in teams}


def leader_list(players, fmt, rows, team_abbr, colors):
    players = players[:rows]
    if not players:
        return '<p class="leaders-empty">No data available.</p>'
    items = []
    rank = 0
    for i, player in enumerate(players):
        # Ties share a rank (1, 2, 2, 4)
        if i == 0 or player.get("value") != players[i - 1].get("value"):
            rank = i + 1
        items.append(leader_row(player, rank, fmt, team_abbr, colors))
    return f'<ol class="leaders-list">{"".join(items)}</ol>'


def leader_row(player, rank, fmt, team_abbr, colors):
    abbrev = player.get("teamAbbrev") or ""
    first = (player.get("firstName") or {}).get("default", "")
    last = (player.get("lastName") or {}).get("default", "")
    name = f"{first[:1]}. {last}" if first else last
    own = " own-team" if abbrev == team_abbr else ""
    color = colors.get(abbrev, "#888888")
    return (
        f'<li class="leader-row{own}" style="--leader-color: {color};">'
        f'<span class="leader-rank">{rank}</span>'
        f'<img class="leader-headshot" src="{escape(player.get("headshot") or "")}" alt="" '
        f'data-player-id="{player.get("id")}" loading="lazy">'
        f'<span class="leader-name" title="{escape(f"{first} {last}")}">{escape(name)}'
        f'<small>{escape(abbrev)} · {escape(player.get("position") or "")}</small></span>'
        f'<a href="javascript:void(0);" class="team-link"><img class="leader-logo" src="{get_logo(abbrev)}" alt="{escape(abbrev)}"></a>'
        f'<span class="leader-value">{format_value(player.get("value"), fmt)}</span>'
        f'</li>'
    )


def format_value(value, fmt):
    if value is None:
        return "–"
    if fmt == "signed":
        return f"{value:+d}" if value else "0"
    if fmt == "pct":
        return f"{value * 100:.1f}%"
    if fmt == "save":
        return f"{value:.3f}".lstrip("0")
    if fmt == "gaa":
        return f"{value:.2f}"
    if fmt == "toi":
        minutes, seconds = divmod(round(value), 60)
        return f"{minutes}:{seconds:02d}"
    return str(value)
