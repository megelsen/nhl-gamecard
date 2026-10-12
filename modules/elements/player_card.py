from datetime import date, datetime

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

SKATER_COLUMNS = [("GP", "gamesPlayed"), ("G", "goals"), ("A", "assists"), ("P", "points"), ("+/-", "plusMinus")]
GOALIE_COLUMNS = [("GP", "gamesPlayed"), ("W", "wins"), ("GAA", "goalsAgainstAvg"), ("SV%", "savePctg"), ("SO", "shutouts")]


def build_player_card(landing):
    """Everything the player card template needs, from the /player/{id}/landing response."""
    is_goalie = landing.get("position") == "G"
    country = landing.get("birthCountry", "")
    iso2 = COUNTRY_ISO2.get(country)

    columns = GOALIE_COLUMNS if is_goalie else SKATER_COLUMNS
    featured = landing.get("featuredStats") or {}
    season_stats = featured.get("regularSeason", {}).get("subSeason")
    career_stats = (landing.get("careerTotals") or {}).get("regularSeason")
    stats_rows = []
    if season_stats:
        stats_rows.append((season_label(featured.get("season")), format_stats(season_stats, columns)))
    if career_stats:
        stats_rows.append(("Career", format_stats(career_stats, columns)))

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


def season_label(season):
    # 20262027 -> "2026-27"
    season = str(season or "")
    return f"{season[:4]}-{season[-2:]}" if len(season) == 8 else "This season"


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
