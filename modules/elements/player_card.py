from datetime import date, datetime

from modules.fetch_nhl_api import get_logo

__all__ = ['build_player_card']

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
    inches = landing.get("heightInInches")
    parts = []
    if inches:
        parts.append(f"{inches // 12}'{inches % 12}\" ({landing.get('heightInCentimeters', '-')} cm)")
    if landing.get("weightInPounds"):
        parts.append(f"{landing['weightInPounds']} lb ({landing.get('weightInKilograms', '-')} kg)")
    return ", ".join(parts) or "-"


def draft(details):
    if not details:
        return "Undrafted"
    return (
        f"{details.get('year')}, {details.get('teamAbbrev', '')}, "
        f"round {details.get('round')}, #{details.get('overallPick')} overall"
    )
