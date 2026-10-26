from datetime import date, datetime

from modules.fetch_nhl_api import get_logo, get_skater_edge, get_goalie_edge, get_skater_summary
from modules.fetch_moneypuck import get_moneypuck_skaters, get_moneypuck_goalies
from modules.read_schedule import get_season_id
from modules.elements.compare import skater_edge_stats, skater_xg_stats, goalie_edge_stats

__all__ = ['build_player_card', 'build_percentiles', 'build_compare_player', 'season_name']

POSITIONS = {"C": "C", "L": "LW", "R": "RW", "D": "D", "G": "G"}

# NHL API birth countries are ISO 3166-1 alpha-3; flagcdn.com wants alpha-2
COUNTRY_ISO2 = {
    "CAN": "ca", "USA": "us", "SWE": "se", "FIN": "fi", "CZE": "cz", "SVK": "sk", "RUS": "ru",
    "CHE": "ch", "DEU": "de", "LVA": "lv", "DNK": "dk", "NOR": "no", "AUT": "at", "BLR": "by",
    "FRA": "fr", "GBR": "gb", "SVN": "si", "UKR": "ua", "KAZ": "kz", "AUS": "au", "NLD": "nl",
    "ITA": "it", "POL": "pl", "EST": "ee", "LTU": "lt", "JPN": "jp", "KOR": "kr", "JAM": "jm",
    "NGA": "ng", "BRA": "br", "HUN": "hu", "BEL": "be", "CHN": "cn", "HRV": "hr", "ZAF": "za",
    "SRB": "rs", "ROU": "ro", "BGR": "bg", "ISR": "il", "MEX": "mx", "VEN": "ve", "TWN": "tw",
}

SKATER_COLUMNS = [("GP", "gamesPlayed"), ("G", "goals"), ("A", "assists"), ("P", "points"), ("+/-", "plusMinus"),
                  ("PIM", "pim"), ("Hits", "hits")]
GOALIE_COLUMNS = [("GP", "gamesPlayed"), ("W", "wins"), ("GAA", "goalsAgainstAvg"), ("SV%", "savePctg"), ("SO", "shutouts")]
SEASONS_SHOWN = 5
# Summed when a player had several teams in one season (trade)
COUNTING_KEYS = ("gamesPlayed", "goals", "assists", "points", "plusMinus", "pim", "wins", "losses", "otLosses",
                 "shutouts", "goalsAgainst", "shotsAgainst")


def build_player_card(landing, season_report=None):
    """
    Everything the player card template needs, from the /player/{id}/landing response.
    `season_report` (stats API, one row per season) adds the teams per season and hits.
    """
    is_goalie = landing.get("position") == "G"
    country = landing.get("birthCountry", "")
    iso2 = COUNTRY_ISO2.get(country)
    columns = GOALIE_COLUMNS if is_goalie else SKATER_COLUMNS
    stats_rows = season_rows(landing, season_report, columns, is_goalie)

    return {
        "name": f"{landing['firstName']['default']} {landing['lastName']['default']}",
        "number": landing.get("sweaterNumber", ""),
        "position": POSITIONS.get(landing.get("position"), landing.get("position", "")),
        "team_name": (landing.get("fullTeamName") or {}).get("default", ""),
        "team_logo": landing.get("teamLogo", ""),
        "player_id": landing.get("playerId"),
        "is_goalie": is_goalie,
        "team_abbrev": landing.get("currentTeamAbbrev", ""),
        "headshot": landing.get("headshot", ""),
        "hero_image": landing.get("heroImage") or landing.get("headshot", ""),
        "country": country,
        "flag_url": f"https://flagcdn.com/{iso2}.svg" if iso2 else None,
        "born": born(landing.get("birthDate")),
        "birthplace": ", ".join(
            part for part in (
                (landing.get("birthCity") or {}).get("default"),
                (landing.get("birthStateProvince") or {}).get("default"),
                country,
            ) if part
        ),
        "size": size(landing),
        "hand_label": "Catches" if is_goalie else "Shoots",
        "hand": landing.get("shootsCatches", "-"),
        "draft": draft(landing.get("draftDetails")),
        "stat_columns": [label for label, _ in columns],
        "stats_rows": stats_rows,
    }


def season_rows(landing, season_report, columns, is_goalie):
    """Last NHL regular seasons (up to SEASONS_SHOWN) plus a career row: [(label, teams, values)]."""
    report = {row.get("seasonId"): row for row in (season_report or {}).get("data", [])}
    by_season = {}
    for entry in landing.get("seasonTotals", []):
        if entry.get("leagueAbbrev") == "NHL" and entry.get("gameTypeId") == 2:
            by_season.setdefault(entry["season"], []).append(entry)

    rows = []
    for season in sorted(by_season)[-SEASONS_SHOWN:]:
        parts = sorted(by_season[season], key=lambda e: e.get("sequence", 0))
        stats = combine_seasons(parts, is_goalie)
        stats["hits"] = report.get(season, {}).get("hits")
        rows.append((season_label(season), season_teams(parts, report.get(season)), format_stats(stats, columns)))

    career = dict((landing.get("careerTotals") or {}).get("regularSeason") or {})
    if career:
        # Hits are only tracked since 2005-06, so the career total covers those seasons
        hits = [row.get("hits") for row in report.values() if row.get("hits") is not None]
        career["hits"] = sum(hits) if hits else None
        rows.append(("Career", [], format_stats(career, columns)))
    return rows


def combine_seasons(parts, is_goalie):
    """One season's stats; a traded player's per-team rows are summed (goalie rates recalculated)."""
    if len(parts) == 1:
        return dict(parts[0])
    stats = {key: sum(p.get(key) or 0 for p in parts) for key in COUNTING_KEYS}
    if is_goalie:
        minutes = sum(toi_minutes(p.get("timeOnIce")) for p in parts)
        stats["goalsAgainstAvg"] = stats["goalsAgainst"] * 60 / minutes if minutes else None
        shots = stats["shotsAgainst"]
        stats["savePctg"] = 1 - stats["goalsAgainst"] / shots if shots else None
    return stats


def toi_minutes(time_on_ice):
    # "334:45" -> 334.75
    try:
        minutes, seconds = str(time_on_ice).split(":")
        return int(minutes) + int(seconds) / 60
    except ValueError:
        return 0


def season_teams(parts, report_row):
    """Teams of one season in order, e.g. [VAN, NYR] after a trade. Abbreviations (for logos) come
    from the stats report; without it, fall back to the team names."""
    abbrevs = [a for a in ((report_row or {}).get("teamAbbrevs") or "").split(",") if a]
    if len(abbrevs) == len(parts):
        return [{"abbrev": a, "logo": get_logo(a)} for a in abbrevs]
    return [{"abbrev": (p.get("teamCommonName") or {}).get("default", ""), "logo": None} for p in parts]


def season_label(season):
    # 20262027 -> "26-27"
    season = str(season or "")
    return f"{season[2:4]}-{season[-2:]}" if len(season) == 8 else ""


def format_stats(stats, columns):
    values = []
    for label, key in columns:
        value = stats.get(key)
        if value is None:
            values.append("-")
        elif label == "GAA":
            values.append(f"{value:.2f}")
        elif label == "SV%":
            values.append(f"{value:.3f}".lstrip("0"))
        elif label == "+/-" and value > 0:
            values.append(f"+{value}")
        else:
            values.append(value)
    return values


def born(birth_date):
    if not birth_date:
        return "-"
    birthday = datetime.strptime(birth_date, "%Y-%m-%d").date()
    today = date.today()
    age = today.year - birthday.year - ((today.month, today.day) < (birthday.month, birthday.day))
    return f"{birthday.strftime('%b %d, %Y')} (age {age})"


def size(landing):
    """Height and weight in both unit systems; the footer's units setting picks one (userSettings.js)."""
    inches = landing.get("heightInInches")
    metric, imperial = [], []
    if inches:
        imperial.append(f"{inches // 12}'{inches % 12}\"")
        metric.append(f"{landing.get('heightInCentimeters', '-')} cm")
    if landing.get("weightInPounds"):
        imperial.append(f"{landing['weightInPounds']} lb")
        metric.append(f"{landing.get('weightInKilograms', '-')} kg")
    return {"metric": ", ".join(metric) or "-", "imperial": ", ".join(imperial) or "-"}


def draft(details):
    if not details:
        return "Undrafted"
    return (
        f"{details.get('year')}, {details.get('teamAbbrev', '')}, "
        f"round {details.get('round')}, #{details.get('overallPick')} overall"
    )


# Back of the card: the player vs. the NHL average of his position group, drawn like the
# comparison rows (comparison.css) with the bar split at his percentile (higher = better).
# NHL EDGE ships its own percentiles; MoneyPuck xG percentiles are computed here.
QUALIFY_SHARE = 0.25  # computed percentiles count players with >= 25% of the group's most games
POSITION_GROUPS = {"G": "goalies", "D": "defensemen"}


def build_percentiles(landing, season_id):
    """{"group": "forwards", "season": "2026-27", "rows": [{label, value, avg, pct, split}]} or None.
    Labels and values are strings, or {"metric", "imperial"} dicts (unit-value spans in the template)."""
    player_id = landing.get("playerId")
    position = landing.get("position")
    if position == "G":
        rows = goalie_percentiles(get_goalie_edge(player_id) or {}, player_id, get_moneypuck_goalies(season_id))
    else:
        rows = skater_percentiles(get_skater_edge(player_id) or {}, player_id, position,
                                  get_skater_summary(season_id), get_moneypuck_skaters(season_id))
    rows = [row for row in rows if row["pct"] is not None and row["value"] is not None]
    if not rows:
        return None
    return {"group": POSITION_GROUPS.get(position, "forwards"), "season": season_name(season_id), "rows": rows}


def season_name(season_id):
    # 20262027 -> "2026-27"
    season = str(season_id)
    return f"{season[:4]}-{season[-2:]}"


def skater_percentiles(edge, player_id, position, summary, moneypuck):
    speed = edge.get("skatingSpeed") or {}
    shots = {s.get("locationCode"): s for s in edge.get("sogSummary", [])}
    all_shots = shots.get("all", {})
    # Goals, assists, points (stats API) and 5v5 on-ice xG per 60 (MoneyPuck), vs. forwards or defensemen.
    # Goals, assists and points show the player's NHL rank (all skaters); the bar still splits at the percentile.
    group = (lambda e: e.get("pos") == "D") if position == "D" else (lambda e: e.get("pos") != "D")
    rows = [with_nhl_rank(row(label, *league_percentile(summary, player_id, group, lambda e, key=key: e.get(key)),
                              "{:.0f}", "{:.1f}"), summary, player_id, key)
            for label, key in (("Goals", "g"), ("Assists", "a"), ("Points", "p"))]
    rows += [
        info("SHOT", measured("Top shot", edge.get("topShotSpeed"), "km/h", "mph")),
        info("SPEED", measured("Max speed", speed.get("speedMax"), "km/h", "mph")),
        info("DIST", measured("Distance", edge.get("totalDistanceSkated"), "km", "mi")),
        row("Shots", all_shots.get("shots"), all_shots.get("shotsLeagueAvg"), all_shots.get("shotsPercentile"), "{:.0f}", "{:.1f}"),
        info("SH%", row("Shooting %", all_shots.get("shootingPctg"), all_shots.get("shootingPctgLeagueAvg"),
                        all_shots.get("shootingPctgPercentile"), "pct")),
    ]
    rows.append(info("XGF60", row("xGF/60 5v5", *league_percentile(moneypuck, player_id, group, lambda e: per_60(e, "xgf")),
                                  "{:.2f}")))
    # Fewer expected goals against is better: the percentile counts players with more
    rows.append(info("XGA60", row("xGA/60 5v5", *league_percentile(moneypuck, player_id, group, lambda e: per_60(e, "xga"),
                                                                   lower_is_better=True), "{:.2f}")))
    return rows


def with_nhl_rank(entry, summary, player_id, key):
    # 1 + skaters with more, so ties share a rank (like NHL.com)
    value = ((summary or {}).get(str(player_id)) or {}).get(key)
    if value is not None and entry["pct"] is not None:
        rank = 1 + sum(1 for e in summary.values() if (e.get(key) or 0) > value)
        entry["rank"] = f"{ordinal(rank)} in NHL"
        entry["rank_info"] = "RANK"
    return entry


def per_60(entry, key):
    hours = (entry.get("toi") or 0) / 3600
    return entry[key] / hours if hours and entry.get(key) is not None else None


def goalie_percentiles(edge, player_id, moneypuck):
    stats = edge.get("stats") or {}
    saves = {s.get("locationCode"): s for s in edge.get("shotLocationSummary", [])}
    all_saves, high_saves = saves.get("all", {}), saves.get("high", {})

    def stat(label, key, fmt):
        item = stats.get(key) or {}
        return row(label, item.get("value"), item.get("leagueAvg"), item.get("percentile"), fmt)

    rows = [
        stat("GAA", "goalsAgainstAvg", "{:.2f}"),
        row("SV%", all_saves.get("savePctg"), all_saves.get("savePctgLeagueAvg"), all_saves.get("savePctgPercentile"), "svpct"),
        info("HDSV%", row("HD SV%", high_saves.get("savePctg"), high_saves.get("savePctgLeagueAvg"),
                          high_saves.get("savePctgPercentile"), "svpct")),
        info("GD60", stat("GD/60", "goalDifferentialPer60", "{:+.2f}")),
        info("Q900", stat(".900+ games", "gamesAbove900", "pct")),
    ]
    rows.append(info("GSAX", row("GSAx", *league_percentile(moneypuck, player_id, lambda e: True, goals_saved_above_expected),
                                 "{:+.1f}")))
    return rows


def goals_saved_above_expected(entry):
    if not entry or entry.get("xga") is None or entry.get("ga") is None:
        return None
    return entry["xga"] - entry["ga"]


def league_percentile(players, player_id, in_group, metric, lower_is_better=False):
    """(value, group average, percentile) of `metric` among qualified players of the same group
    (MoneyPuck or stats API rows, each with "gp"). Higher percentile = better."""
    players = players or {}
    entry = players.get(str(player_id))
    value = metric(entry) if entry else None
    if value is None:
        return None, None, None
    group = [e for e in players.values() if in_group(e) and e.get("gp")]
    min_games = QUALIFY_SHARE * max((e["gp"] for e in group), default=0)
    values = [v for v in (metric(e) for e in group if e["gp"] >= min_games) if v is not None]
    if not values:
        return value, None, None
    worse = sum((v > value) if lower_is_better else (v < value) for v in values)
    below = worse + 0.5 * sum(v == value for v in values)
    return value, sum(values) / len(values), below / len(values)


def measured(label, item, metric_unit, imperial_unit):
    """EDGE value with metric and imperial numbers (speeds, distances); the unit goes in the label."""
    item = item or {}
    avg = item.get("leagueAvg") or {}

    def both(source):
        if source.get("metric") is None:
            return None
        return {"metric": f"{source['metric']:.1f}", "imperial": f"{source['imperial']:.1f}"}
    return with_percentile({"label": {"metric": f"{label} {metric_unit}", "imperial": f"{label} {imperial_unit}"},
                            "value": both(item), "avg": both(avg)}, item.get("percentile"))


def info(key, entry):
    # Key of the stat's definition in STAT_INFO (static/js/statInfo.js), shown when hovering the label
    entry["info"] = key
    return entry


def row(label, value, avg, percentile, fmt, avg_fmt=None):
    # avg_fmt: e.g. one decimal for the average of a count
    return with_percentile({"label": label, "value": format_value(value, fmt),
                            "avg": format_value(avg, avg_fmt or fmt)}, percentile)


def with_percentile(entry, percentile):
    # 0.9967 -> 99 (rounded down, so only the very top shows 100). The bar split stays
    # within 4..96% so the slanted edge is always visible.
    pct = None if percentile is None else max(0, min(100, int(percentile * 100)))
    entry["pct"] = pct
    entry["rank"] = None if pct is None else f"{ordinal(pct)} pctl"
    entry["rank_info"] = "PCT"
    entry["split"] = None if pct is None else max(4, min(96, pct))
    return entry


def ordinal(number):
    # 1 -> "1st", 12 -> "12th", 22 -> "22nd"
    suffix = "th" if 10 <= number % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(number % 10, "th")
    return f"{number}{suffix}"


def format_value(value, fmt):
    if value is None:
        return "-"
    if fmt == "pct":
        return f"{value * 100:.1f}%"
    if fmt == "svpct":
        return f"{value:.3f}".lstrip("0")
    return fmt.format(value)


# Player comparison (static/js/playerCard.js): one season's raw numbers per COMPARE_SPECS key
# (this season or a past one, so a player can also be compared with another of their own seasons)
def build_compare_player(landing, season_id, season_report=None):
    """`season_report` (stats API) gives a past season's team abbreviation."""
    player_id = landing.get("playerId")
    is_goalie = landing.get("position") == "G"
    current = str(season_id) == get_season_id()
    parts = season_parts(landing, season_id)
    featured = landing.get("featuredStats") or {}
    if current:
        live = str(featured.get("season")) == str(season_id)
        stats = ((featured.get("regularSeason") or {}).get("subSeason") or {}) if live else {}
    else:
        stats = combine_seasons(parts, is_goalie) if parts else {}
    edge_season = None if current else season_id  # EDGE's "now" is the current season
    if is_goalie:
        mp = (get_moneypuck_goalies(season_id) or {}).get(str(player_id))
        values = {
            "GP": stats.get("gamesPlayed"),
            "W": stats.get("wins"),
            "GAA": stats.get("goalsAgainstAvg"),
            "SV%": stats.get("savePctg"),
            "SO": stats.get("shutouts"),
            "HDSV%": goalie_edge_stats(player_id, edge_season)["hd_save_pct"],
            "GSAX": goals_saved_above_expected(mp),
        }
    else:
        edge = skater_edge_stats(player_id, edge_season)
        xg = skater_xg_stats(player_id, get_moneypuck_skaters(season_id))
        values = {
            "GP": stats.get("gamesPlayed"),
            "G": stats.get("goals"),
            "A": stats.get("assists"),
            "P": stats.get("points"),
            "PM": stats.get("plusMinus"),
            "TOI": average_toi(landing, season_id),
            "XGF60": xg["xgf_60"],
            "XGA60": xg["xga_60"],
            "SHOT": edge["shot_speed"],
            "SPEED": edge["skate_speed"],
        }
    card = build_player_card(landing)
    team, team_name = card["team_abbrev"], card["team_name"]
    if not current and parts:
        # The team he finished that season with (its colors too)
        team_name = (parts[-1].get("teamName") or {}).get("default", "")
        report = next((row for row in (season_report or {}).get("data", [])
                       if str(row.get("seasonId")) == str(season_id)), {})
        team = ((report.get("teamAbbrevs") or "").split(",") or [""])[-1] or team
    return {
        "id": player_id,
        "name": card["name"],
        "number": card["number"],
        "position": card["position"],
        "is_goalie": is_goalie,
        "team": team,
        "team_name": team_name,
        "headshot": card["headshot"],
        "flag_url": card["flag_url"],
        "country": card["country"],
        "season": season_name(season_id),
        "season_id": str(season_id),
        "values": values,
    }


def season_parts(landing, season_id):
    """A season's NHL regular-season rows from the landing data, one per team, in order."""
    parts = [e for e in landing.get("seasonTotals", [])
             if str(e.get("season")) == str(season_id) and e.get("leagueAbbrev") == "NHL" and e.get("gameTypeId") == 2]
    return sorted(parts, key=lambda e: e.get("sequence", 0))


def average_toi(landing, season_id):
    """Seconds of ice time per game in a season (weighted over teams after a trade)."""
    parts = season_parts(landing, season_id)
    games = sum(e.get("gamesPlayed") or 0 for e in parts)
    if not games:
        return None
    return sum(toi_minutes(e.get("avgToi")) * 60 * (e.get("gamesPlayed") or 0) for e in parts) / games
