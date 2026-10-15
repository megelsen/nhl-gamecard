from datetime import date, datetime

from modules.fetch_nhl_api import get_logo, get_skater_edge, get_goalie_edge
from modules.fetch_moneypuck import get_moneypuck_skaters, get_moneypuck_goalies

__all__ = ['build_player_card', 'build_percentiles']

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


# Back of the card: percentiles vs. the player's position group, oriented so higher = better.
# NHL EDGE ships its own percentiles; MoneyPuck xG percentiles are computed here.
MP_QUALIFY_SHARE = 0.25  # MoneyPuck percentiles count players with >= 25% of the group's most games
POSITION_GROUPS = {"G": "goalies", "D": "defensemen"}


def build_percentiles(landing, season_id):
    """{"group": "forwards", "season": "2026-27", "rows": [{label, value, avg, pct}]} or None.
    `value`/`avg` are strings or {"metric", "imperial"} dicts (unit-value spans in the template)."""
    player_id = landing.get("playerId")
    position = landing.get("position")
    if position == "G":
        rows = goalie_percentiles(get_goalie_edge(player_id) or {}, player_id, get_moneypuck_goalies(season_id))
    else:
        rows = skater_percentiles(get_skater_edge(player_id) or {}, player_id, position, get_moneypuck_skaters(season_id))
    rows = [row for row in rows if row["pct"] is not None and row["value"] is not None]
    if not rows:
        return None
    season = str(season_id)
    return {
        "group": POSITION_GROUPS.get(position, "forwards"),
        "season": f"{season[:4]}-{season[-2:]}",
        "rows": rows,
    }


def skater_percentiles(edge, player_id, position, moneypuck):
    speed = (edge.get("skatingSpeed") or {})
    shots = {s.get("locationCode"): s for s in edge.get("sogSummary", [])}
    zone = edge.get("zoneTimeDetails") or {}
    rows = [
        measured("Top shot speed", edge.get("topShotSpeed"), "km/h", "mph"),
        measured("Max skating speed", speed.get("speedMax"), "km/h", "mph"),
        row({"metric": "Bursts over 32 km/h", "imperial": "Bursts over 20 mph"}, (speed.get("burstsOver20") or {}).get("value"),
            (speed.get("burstsOver20") or {}).get("leagueAvg", {}).get("value"),
            (speed.get("burstsOver20") or {}).get("percentile"), "{:.0f}"),
        measured("Distance skated", edge.get("totalDistanceSkated"), "km", "mi"),
        row("Shots on goal", shots.get("all", {}).get("shots"), shots.get("all", {}).get("shotsLeagueAvg"),
            shots.get("all", {}).get("shotsPercentile"), "{:.0f}"),
        row("High-danger shots", shots.get("high", {}).get("shots"), shots.get("high", {}).get("shotsLeagueAvg"),
            shots.get("high", {}).get("shotsPercentile"), "{:.0f}"),
        row("Shooting %", shots.get("all", {}).get("shootingPctg"), shots.get("all", {}).get("shootingPctgLeagueAvg"),
            shots.get("all", {}).get("shootingPctgPercentile"), "pct"),
        row("Offensive-zone time", zone.get("offensiveZonePctg"), zone.get("offensiveZoneLeagueAvg"),
            zone.get("offensiveZonePercentile"), "pct"),
    ]
    # 5v5 on-ice share of expected goals, vs. forwards or defensemen
    def xgf_share(entry):
        total = (entry.get("xgf") or 0) + (entry.get("xga") or 0)
        return entry["xgf"] / total if total else None
    group = (lambda pos: pos == "D") if position == "D" else (lambda pos: pos != "D")
    value, avg, pct = moneypuck_percentile(moneypuck, player_id, lambda e: group(e.get("pos")), xgf_share)
    rows.append(row("xGF% (5v5)", value, avg, pct, "pct"))
    return rows


def goalie_percentiles(edge, player_id, moneypuck):
    stats = edge.get("stats") or {}
    saves = {s.get("locationCode"): s for s in edge.get("shotLocationSummary", [])}

    def stat(label, key, fmt):
        item = stats.get(key) or {}
        return row(label, item.get("value"), item.get("leagueAvg"), item.get("percentile"), fmt)

    rows = [
        stat("GAA", "goalsAgainstAvg", "{:.2f}"),
        row("SV%", saves.get("all", {}).get("savePctg"), saves.get("all", {}).get("savePctgLeagueAvg"),
            saves.get("all", {}).get("savePctgPercentile"), "svpct"),
        row("High-danger SV%", saves.get("high", {}).get("savePctg"), saves.get("high", {}).get("savePctgLeagueAvg"),
            saves.get("high", {}).get("savePctgPercentile"), "svpct"),
        stat("Goal differential/60", "goalDifferentialPer60", "{:+.2f}"),
        stat("Games with SV% .900+", "gamesAbove900", "pct"),
    ]
    gsax = lambda e: e["xga"] - e["ga"] if e.get("xga") is not None and e.get("ga") is not None else None
    value, avg, pct = moneypuck_percentile(moneypuck, player_id, lambda e: True, gsax)
    rows.append(row("Goals saved above expected", value, avg, pct, "{:+.1f}"))
    return rows


def moneypuck_percentile(players, player_id, in_group, metric):
    """(value, group average, percentile) of `metric` among qualified players of the same group."""
    players = players or {}
    entry = players.get(str(player_id))
    value = metric(entry) if entry else None
    if value is None:
        return None, None, None
    group = [e for e in players.values() if in_group(e) and e.get("gp")]
    min_games = MP_QUALIFY_SHARE * max((e["gp"] for e in group), default=0)
    values = [v for v in (metric(e) for e in group if e["gp"] >= min_games) if v is not None]
    if not values:
        return value, None, None
    below = sum(v < value for v in values) + 0.5 * sum(v == value for v in values)
    return value, sum(values) / len(values), below / len(values)


def measured(label, item, metric_unit, imperial_unit):
    """EDGE value with metric and imperial numbers (speeds, distances)."""
    item = item or {}
    avg = item.get("leagueAvg") or {}
    if item.get("metric") is None:
        return row(label, None, None, None, None)

    def both(source):
        if source.get("metric") is None:
            return None
        return {"metric": f"{source['metric']:.1f} {metric_unit}", "imperial": f"{source['imperial']:.1f} {imperial_unit}"}
    return {"label": label, "value": both(item), "avg": both(avg), "pct": percent(item.get("percentile"))}


def row(label, value, avg, percentile, fmt):
    return {"label": label, "value": format_value(value, fmt), "avg": format_value(avg, fmt), "pct": percent(percentile)}


def format_value(value, fmt):
    if value is None:
        return None
    if fmt == "pct":
        return f"{value * 100:.1f}%"
    if fmt == "svpct":
        return f"{value:.3f}".lstrip("0")
    return fmt.format(value)


def percent(percentile):
    # 0.9967 -> 99 (rounded down, so only the very top shows 100)
    return None if percentile is None else max(0, min(100, int(percentile * 100)))
