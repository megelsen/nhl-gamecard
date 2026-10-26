from html import escape

from cache_utils import load_latest_cache
from modules.fetch_nhl_api import get_logo
from modules.fetch_team_info import get_team_color
from modules.elements.player_card import QUALIFY_SHARE, per_60, goals_saved_above_expected

__all__ = ['build_league_leaders']

CARD_ROWS = 5
MODAL_ROWS = 15
POSITIONS = {"L": "LW", "R": "RW"}

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

# NHL EDGE top 10s: (name in get_edge_skater_leaders, tab label, caption, STAT_INFO key, value key,
# units, or None for a plain count)
EDGE_CATEGORIES = [
    ("speed", "Speed", "Top skating speed", "SPEED", "maxSpeed", ("km/h", "mph")),
    ("shot", "Shot", "Hardest shot", "SHOT", "hardestShot", ("km/h", "mph")),
    ("distance", "Distance", "Total distance skated", "DIST", "distanceTotal", ("km", "mi")),
    ("hdshots", "HD shots", "High-danger shots on goal", "HDSOG", "highDanger", None),
]
MONEYPUCK_SOURCE = '<a href="https://moneypuck.com" target="_blank" rel="noopener">MoneyPuck.com</a>'


def build_league_leaders(team_abbr, standings_data, skater_leaders, goalie_leaders, edge_leaders,
                         moneypuck_skaters, moneypuck_goalies, season_id):
    """
    League leaders as pre-rendered lists: {"card": {label: html}, "modal": {"Skaters": {label: html},
    "Goalies": {...}, "Advanced": {...}}}. Each row has a stripe in the player's team color.
    edge_leaders: {name: EDGE top 10} for the names in EDGE_CATEGORIES.
    """
    colors = team_colors_by_abbrev(standings_data)
    skater_leaders = skater_leaders or {}
    goalie_leaders = goalie_leaders or {}

    def render(entries, rows, caption=""):
        return caption + leader_list(entries[:rows], team_abbr, colors)

    def stats_lists(data, categories, rows):
        return {label: render([nhl_entry(p, fmt) for p in data.get(key) or []], rows)
                for key, label, fmt in categories}

    advanced = {}
    for name, label, caption, info, key, units in EDGE_CATEGORIES:
        entries = [edge_entry(p, key, units) for p in (edge_leaders or {}).get(name) or []]
        advanced[label] = render([e for e in entries if e], MODAL_ROWS, list_caption(caption, info, "NHL EDGE"))
    advanced.update(moneypuck_lists(moneypuck_skaters, moneypuck_goalies, season_id, render))

    return {
        "card": stats_lists(skater_leaders, CARD_CATEGORIES, CARD_ROWS),
        "modal": {
            "Skaters": stats_lists(skater_leaders, SKATER_CATEGORIES, MODAL_ROWS),
            "Goalies": stats_lists(goalie_leaders, GOALIE_CATEGORIES, MODAL_ROWS),
            "Advanced": advanced,
        },
    }


def team_colors_by_abbrev(standings_data):
    teams = (standings_data or {}).get("standings", [])
    return {t["teamAbbrev"]["default"]: get_team_color(t["teamName"]["default"])["primary"] for t in teams}


def list_caption(text, info, source, qualifier=""):
    qualifier = f" · {qualifier}" if qualifier else ""
    return (f'<p class="leaders-caption"><span data-stat-info="{info}">{escape(text)}</span>'
            f'{qualifier} · {source}</p>')


# Every source becomes the same entry: {id, first, last, number, team, position, headshot, value, display}
# (value is compared for ties, display is the HTML shown)

def nhl_entry(player, fmt):
    return {
        "id": player.get("id"),
        "first": (player.get("firstName") or {}).get("default", ""),
        "last": (player.get("lastName") or {}).get("default", ""),
        "number": player.get("sweaterNumber"),
        "team": player.get("teamAbbrev") or "",
        "position": player.get("position") or "",
        "headshot": player.get("headshot") or "",
        "value": player.get("value"),
        "display": format_value(player.get("value"), fmt),
    }


def edge_entry(item, key, units):
    player = item.get("player") or {}
    if units:
        measure = item.get(key) or {}
        if measure.get("metric") is None:
            return None
        metric, imperial = f"{measure['metric']:.1f}", f"{measure['imperial']:.1f}"
        value = measure["metric"]
        # userSettings.js swaps the text by the viewer's Units setting
        display = (f'<span class="unit-value" data-metric="{metric} {units[0]}" data-imperial="{imperial} {units[1]}">'
                   f'{metric} {units[0]}</span>')
    else:
        value = item.get(key)
        if value is None:
            return None
        display = str(value)
    # EDGE lists have no player id field, only the slug ("philip-broberg-8481598")
    slug_id = (player.get("slug") or "").rsplit("-", 1)[-1]
    return {
        "id": int(slug_id) if slug_id.isdigit() else None,
        "first": (player.get("firstName") or {}).get("default", ""),
        "last": (player.get("lastName") or {}).get("default", ""),
        "number": player.get("sweaterNumber"),
        "team": (player.get("team") or {}).get("abbrev") or "",
        "position": player.get("position") or "",
        "headshot": player.get("headshot") or "",
        "value": value,
        "display": display,
    }


def moneypuck_lists(skaters, goalies, season_id, render):
    """5v5 on-ice xGF/60 and xGA/60 among skaters, GSAx among goalies (top MODAL_ROWS each).
    Rates only count players with at least QUALIFY_SHARE of the most games, like the card percentiles."""
    specs = [
        ("xGF/60", "5v5 on-ice xGF/60", "XGF60", skaters, lambda e: per_60(e, "xgf"), False, "{:.2f}", True),
        ("xGA/60", "5v5 on-ice xGA/60 (lowest)", "XGA60", skaters, lambda e: per_60(e, "xga"), True, "{:.2f}", True),
        ("GSAx", "Goals saved above expected", "GSAX", goalies, goals_saved_above_expected, False, "{:+.1f}", False),
    ]
    lists = {}
    for label, caption, info, players, metric, lower_is_better, fmt, qualify in specs:
        players = players or {}
        played = {pid: e for pid, e in players.items() if e.get("gp")}
        min_games = QUALIFY_SHARE * max((e["gp"] for e in played.values()), default=0) if qualify else 0
        ranked = [(pid, e, metric(e)) for pid, e in played.items() if e["gp"] >= min_games]
        ranked = sorted((r for r in ranked if r[2] is not None), key=lambda r: r[2], reverse=not lower_is_better)
        entries = [moneypuck_entry(pid, e, value, fmt, season_id) for pid, e, value in ranked[:MODAL_ROWS]]
        qualifier = f"min. {min_games:.0f} GP" if qualify and min_games >= 1 else ""
        lists[label] = render(entries, MODAL_ROWS, list_caption(caption, info, MONEYPUCK_SOURCE, qualifier))
    return lists


def moneypuck_entry(player_id, entry, value, fmt, season_id):
    # MoneyPuck has no sweater numbers or headshots: take them from the team's cached roster
    team = entry.get("team") or ""
    rostered = roster_player(team, player_id)
    first, _, last = (entry.get("name") or "").partition(" ")
    return {
        "id": int(player_id),
        "first": first,
        "last": last or first,
        "number": rostered.get("sweaterNumber"),
        "team": team,
        "position": entry.get("pos") or rostered.get("positionCode") or "G",
        "headshot": rostered.get("headshot") or f"https://assets.nhle.com/mugs/nhl/{season_id}/{team}/{player_id}.png",
        "value": value,
        "display": fmt.format(value),
    }


def roster_player(team, player_id):
    # Cache only (the scheduler keeps every roster fresh): looking numbers up must not cost NHL requests
    roster = load_latest_cache(f"roster_{team}") if team else None
    for group in ("forwards", "defensemen", "goalies"):
        for player in (roster or {}).get(group, []):
            if str(player.get("id")) == str(player_id):
                return player
    return {}


def leader_list(entries, team_abbr, colors):
    if not entries:
        return '<p class="leaders-empty">No data available.</p>'
    items = []
    rank = 0
    for i, entry in enumerate(entries):
        # Ties share a rank (1, 2, 2, 4)
        if i == 0 or entry["value"] != entries[i - 1]["value"]:
            rank = i + 1
        items.append(leader_row(entry, rank, team_abbr, colors))
    return f'<ol class="leaders-list">{"".join(items)}</ol>'


def leader_row(entry, rank, team_abbr, colors):
    team = entry["team"]
    first, last = entry["first"], entry["last"]
    name = f"{first[:1]}. {last}" if first and first != last else last
    details = [f"#{entry['number']}" if entry["number"] else "", team, POSITIONS.get(entry["position"], entry["position"])]
    own = " own-team" if team == team_abbr else ""
    player_id = f' data-player-id="{entry["id"]}"' if entry["id"] else ""
    return (
        f'<li class="leader-row{own}" style="--leader-color: {colors.get(team, "#888888")};">'
        f'<span class="leader-rank">{rank}</span>'
        # Team logo sits on the headshot's edge, lower right (league_leaders.css)
        f'<span class="leader-photo">'
        f'<img class="leader-headshot" src="{escape(entry["headshot"])}" alt=""{player_id} loading="lazy">'
        f'<a href="javascript:void(0);" class="team-link"><img class="leader-logo" src="{get_logo(team)}" alt="{escape(team)}"></a>'
        f'</span>'
        f'<span class="leader-name" title="{escape(f"{first} {last}")}">{escape(name)}'
        f'<small>{escape(" · ".join(d for d in details if d))}</small></span>'
        f'<span class="leader-value">{entry["display"]}</span>'
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
