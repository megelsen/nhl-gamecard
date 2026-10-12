import html
import json

from modules.fetch_nhl_api import get_skater_edge, get_goalie_edge

__all__ = ['skater_edge_stats', 'goalie_edge_stats', 'skater_comparison', 'game_comparison', 'compare_mount', 'season_subtitle']

# Row keys understood by static/js/comparison.js (labels, formats and bar rules live there)
SKATER_ROWS = ["GP", "G", "A", "P", "TOI", "HDSOG", "HDG", "SHOT", "SPEED"]
GAME_ROWS = ["Score", "SOG", "SV%", "FO%", "PP", "Hits"]


def skater_edge_stats(player_id):
    """High-danger shots/goals, top shot speed and max skating speed from NHL EDGE (None when missing)."""
    edge = get_skater_edge(player_id) or {}
    high = next((s for s in edge.get("sogSummary", []) if s.get("locationCode") == "high"), {})
    return {
        "hd_shots": high.get("shots"),
        "hd_goals": high.get("goals"),
        "shot_speed": (edge.get("topShotSpeed") or {}).get("metric"),
        "skate_speed": ((edge.get("skatingSpeed") or {}).get("speedMax") or {}).get("metric"),
    }


def goalie_edge_stats(player_id):
    edge = get_goalie_edge(player_id) or {}
    high = next((s for s in edge.get("shotLocationSummary", []) if s.get("locationCode") == "high"), {})
    return {"hd_save_pct": high.get("savePctg")}


def skater_comparison(left, right, left_team, right_team):
    def values(player):
        player = player or {}
        return {
            "GP": player.get("games_played"),
            "G": player.get("goals"),
            "A": player.get("assists"),
            "P": player.get("points"),
            "TOI": player.get("toi_seconds"),
            "HDSOG": player.get("hd_shots"),
            "HDG": player.get("hd_goals"),
            "SHOT": player.get("shot_speed"),
            "SPEED": player.get("skate_speed"),
        }
    left_values, right_values = values(left), values(right)
    return comparison(left_team, right_team, [(key, left_values[key], right_values[key]) for key in SKATER_ROWS])


def game_comparison(game_data):
    """Last meeting: home team on the left, away team on the right."""
    home, away = game_data["homeTeam"], game_data["awayTeam"]
    stats = {item["category"]: item for item in game_data.get("summary", {}).get("teamGameStats", [])}

    def save_pct(shots_against, goals_against):
        return 1 - goals_against / shots_against if shots_against else None

    def stat(category):
        item = stats.get(category, {})
        return item.get("homeValue"), item.get("awayValue")

    def pp_goals(value):
        # "1/2" -> 1 power play goal (on 2 opportunities)
        try:
            return int(str(value).split("/")[0])
        except ValueError:
            return None

    faceoff_home, faceoff_away = stat("faceoffWinningPctg")
    pp_home, pp_away = stat("powerPlay")
    hits_home, hits_away = stat("hits")
    rows = [
        ("Score", home.get("score"), away.get("score")),
        ("SOG", home.get("sog"), away.get("sog")),
        ("SV%", save_pct(away.get("sog"), away.get("score")), save_pct(home.get("sog"), home.get("score"))),
        ("FO%", faceoff_home, faceoff_away),
        ("PP", pp_goals(pp_home), pp_goals(pp_away), pp_home, pp_away),
        ("Hits", hits_home, hits_away),
    ]
    return comparison(home.get("abbrev"), away.get("abbrev"), rows)


def comparison(left_team, right_team, rows):
    out = []
    for row in rows:
        key, left, right = row[:3]
        entry = {"key": key, "left": left, "right": right}
        if len(row) > 3:
            entry["leftText"], entry["rightText"] = row[3], row[4]
        out.append(entry)
    return {"left": left_team, "right": right_team, "rows": out}


def compare_mount(data):
    """Placeholder element that comparison.js renders into."""
    return f'<div class="compare-mount" data-compare="{html.escape(json.dumps(data), quote=True)}"></div>'


def season_subtitle(team_stats_data):
    season = str((team_stats_data or {}).get("season", ""))
    label = f"{season[:4]}-{season[-2:]}" if len(season) == 8 else ""
    phase = "playoffs" if (team_stats_data or {}).get("gameType") == 3 else "regular season"
    return f"{label} {phase}".strip()
