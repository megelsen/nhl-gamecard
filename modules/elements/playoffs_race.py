from modules.fetch_nhl_api import get_logo

__all__ =['build_standings_tables','get_standings','format_team_standings','bold','build_playoff_picture']

STANDINGS_COLUMNS = ["Team", "Rank", "GP", "PTS", "W", "L", "OTL", "P%"]
PLAYOFF_SPOTS_PER_DIVISION = 3


def build_standings_tables(team_abbr, standings_data):
    """
    Standings tables for both conferences, in two views each:
    {"Eastern": {"conference": html, "wildcard": html}, "Western": {...}}
    """
    standings = standings_data.get("standings", [])
    tables = {}
    for conference in ("Eastern", "Western"):
        teams = [t for t in standings if t.get("conferenceName") == conference]
        tables[conference] = {
            "conference": build_conference_table(teams, team_abbr),
            "wildcard": build_wildcard_table(teams, team_abbr),
        }
    return tables


def build_conference_table(teams, team_abbr):
    teams = sorted(teams, key=lambda t: t.get("conferenceSequence", 99))
    playoff_teams = [t for t in teams if t.get("wildcardSequence", 99) <= 2]
    # Division leaders can rank below a wild card, so the 8 playoff teams aren't always
    # the top 8 by conference rank: only draw the cut line when they are.
    cut_after = len(playoff_teams) - 1 if teams[:len(playoff_teams)] == playoff_teams else None
    rows = [standings_row(t, team_abbr, cut_line=(i == cut_after)) for i, t in enumerate(teams)]
    return standings_table(rows)


def build_wildcard_table(teams, team_abbr):
    """NHL.com style: top 3 of each division, then the wild card race."""
    divisions = {}
    for t in teams:
        divisions.setdefault(t.get("divisionName", ""), []).append(t)
    # Division with the conference leader first
    division_order = sorted(divisions, key=lambda d: min(t.get("conferenceSequence", 99) for t in divisions[d]))

    rows = []
    for division in division_order:
        leaders = sorted(divisions[division], key=lambda t: t.get("divisionSequence", 99))[:PLAYOFF_SPOTS_PER_DIVISION]
        rows.append(group_row(division))
        rows += [standings_row(t, team_abbr) for t in leaders]

    wildcard = sorted(
        (t for t in teams if t.get("wildcardSequence", 0) > 0),
        key=lambda t: t["wildcardSequence"],
    )
    rows.append(group_row("Wild Card"))
    rows += [standings_row(t, team_abbr, cut_line=(t["wildcardSequence"] == 2)) for t in wildcard]
    return standings_table(rows)


def standings_row(team, team_abbr, cut_line=False):
    stats = format_team_standings(get_standings(team), team.get("wildcardSequence", 99))
    classes = []
    if team.get("teamAbbrev", {}).get("default") == team_abbr:
        classes.append("own-team")
    if cut_line:
        classes.append("cut-line")
    class_attr = f' class="{" ".join(classes)}"' if classes else ""
    cells = "".join(f"<td>{stats[col]}</td>" for col in STANDINGS_COLUMNS)
    return f"<tr{class_attr}>{cells}</tr>"


def group_row(label):
    return f'<tr class="standings-group"><th colspan="{len(STANDINGS_COLUMNS)}">{label}</th></tr>'


def standings_table(rows):
    header = "".join(f"<th>{col}</th>" for col in STANDINGS_COLUMNS)
    return (
        '<table class="teams-table standings-table">'
        f"<thead><tr>{header}</tr></thead>"
        f"<tbody>{''.join(rows)}</tbody>"
        "</table>"
    )

def get_standings(team):
    """
    Returns a dictionary with the standings data for a given team.
    
    :param team: Dictionary containing team data.
    :return: Dictionary with raw standings data.
    """
    team_logo = get_logo(team.get('teamAbbrev', {}).get("default"))
    team_logo_html = f"""<a href="javascript:void(0);" class="team-link"><img src="{team_logo}" width="50px"></a>"""

    return {        
        "Team": team_logo_html,
        "Rank": f"{team['divisionAbbrev']}{team['divisionSequence']}",
        "GP": team["gamesPlayed"],        
        "PTS": team["points"],
        "W": team["wins"],
        "L": team["losses"],
        "OTL": team["otLosses"],
        "P%": round(team.get('pointPctg') or 0, 2),
        "points_rank": team["points"],
    }

def format_team_standings(standings,playoffs,bold_on=1):
    """
    Applies formatting to standings based on conditions.

    :param standings: List of team standings dictionaries.
    :param bold_condition: Function that returns True if a row should be bold.
    :param label_change_condition: Function that modifies a specific label.
    :return: List of formatted standings dictionaries.
    """
        # Apply label change condition
    if playoffs == 2:
        standings["Rank"] = f"WC2"  # Change label
    if playoffs == 1:
        standings["Rank"] = f"WC1"  # Change label

    
    # Apply bold condition
    if playoffs < 3 and bold_on == 1:
        standings = {k: bold(v) if k != "points_rank" else v for k, v in standings.items()}  # Apply bold to all fields




    return standings

def bold(text):
    return f"<b>{text}</b>"  # Change formatting as needed (Markdown, HTML, etc.)

ROUND_LABELS = {1: "1st Round", 2: "2nd Round", 3: "Conference Finals", 4: "Stanley Cup Final"}


def build_playoff_picture(team_abbr, standings_data, bracket_data):
    """
    Matchups of the current playoff round. Before the playoffs: round 1 projected from
    standings ("if the season ended today"); during/after them: the real series.
    Returns {"title": str, "subtitle": str, "tables": {"Eastern": html, "Western": html} or {"Final": html}}.
    """
    standings = {t["teamAbbrev"]["default"]: t for t in standings_data.get("standings", [])}
    series = [s for s in (bracket_data or {}).get("series", []) if s.get("topSeedTeam") and s.get("bottomSeedTeam")]

    if series:
        return live_picture(team_abbr, standings, series)
    return projected_picture(team_abbr, standings)


def projected_picture(team_abbr, standings):
    picture = {"title": "Playoff Picture", "subtitle": "1st round if the season ended today", "tables": {}}
    if not any(t.get("gamesPlayed") for t in standings.values()):
        picture["subtitle"] = "Projected matchups appear after the first games"
        return picture

    for conference in ("Eastern", "Western"):
        teams = [t for t in standings.values() if t.get("conferenceName") == conference]
        leaders = sorted((t for t in teams if t.get("divisionSequence") == 1), key=lambda t: t.get("conferenceSequence", 99))
        wildcards = {t.get("wildcardSequence"): t for t in teams}
        if len(leaders) != 2 or 1 not in wildcards or 2 not in wildcards:
            continue
        matchups = []
        # Best division winner plays WC2, the other one WC1; 2nd vs 3rd in each division
        for leader, wildcard in ((leaders[0], wildcards[2]), (leaders[1], wildcards[1])):
            division = [t for t in teams if t.get("divisionName") == leader.get("divisionName")]
            by_seq = {t.get("divisionSequence"): t for t in division}
            matchups.append((leader, wildcard))
            if 2 in by_seq and 3 in by_seq:
                matchups.append((by_seq[2], by_seq[3]))
        rows = [matchup_row(team_abbr, projected_side(top), projected_side(bottom)) for top, bottom in matchups]
        picture["tables"][conference] = matchup_table(rows)
    return picture


def projected_side(team):
    return {
        "abbrev": team["teamAbbrev"]["default"],
        "seed": format_team_standings(get_standings(team), team.get("wildcardSequence", 99), bold_on=0)["Rank"],
        "value": f"{team.get('points', 0)} <small>PTS</small>",
        "won": False,
    }


def live_picture(team_abbr, standings, series):
    # Lowest round still being played; once everything is decided, the last round
    unfinished = [s["playoffRound"] for s in series if not s.get("winningTeamId")]
    current_round = min(unfinished) if unfinished else max(s["playoffRound"] for s in series)
    round_series = sorted((s for s in series if s["playoffRound"] == current_round), key=lambda s: s.get("seriesLetter", ""))
    picture = {"title": "Playoffs", "subtitle": ROUND_LABELS.get(current_round, f"Round {current_round}"), "tables": {}}

    if current_round >= 4:
        picture["tables"]["Final"] = matchup_table([series_row(team_abbr, standings, s) for s in round_series])
        return picture
    for conference in ("Eastern", "Western"):
        rows = [series_row(team_abbr, standings, s) for s in round_series
                if standings.get(s["topSeedTeam"]["abbrev"], {}).get("conferenceName") == conference]
        if rows:
            picture["tables"][conference] = matchup_table(rows)
    return picture


def series_row(team_abbr, standings, series):
    sides = []
    for prefix in ("topSeed", "bottomSeed"):
        team = series[f"{prefix}Team"]
        abbrev = team["abbrev"]
        rank = series.get(f"{prefix}RankAbbrev", "")
        # "D2" -> "M2" so seeds read like the standings card
        if rank.startswith("D") and abbrev in standings:
            rank = f"{standings[abbrev].get('divisionAbbrev', 'D')}{rank[1:]}"
        sides.append({
            "abbrev": abbrev,
            "seed": rank,
            "value": series.get(f"{prefix}Wins", 0),
            "won": series.get("winningTeamId") == team.get("id"),
        })
    return matchup_row(team_abbr, *sides, status=series_status(series, sides))


def series_status(series, sides):
    top, bottom = sides
    if series.get("winningTeamId"):
        winner, loser = (top, bottom) if top["won"] else (bottom, top)
        return f"{winner['abbrev']} wins {winner['value']}-{loser['value']}"
    if top["value"] == bottom["value"]:
        return f"Tied {top['value']}-{bottom['value']}"
    leader, trailer = (top, bottom) if top["value"] > bottom["value"] else (bottom, top)
    return f"{leader['abbrev']} leads {leader['value']}-{trailer['value']}"


def matchup_row(team_abbr, left, right, status="vs"):
    def side_html(side):
        classes = "playoff-team" + (" won" if side["won"] else "")
        return (
            f'<td class="{classes}"><span class="playoff-seed">{side["seed"]}</span>'
            f'<a href="javascript:void(0);" class="team-link"><img src="{get_logo(side["abbrev"])}"></a>'
            f'<span class="playoff-value">{side["value"]}</span></td>'
        )
    own_class = ' class="own-team"' if team_abbr in (left["abbrev"], right["abbrev"]) else ""
    return f"<tr{own_class}>{side_html(left)}<th>{status}</th>{side_html(right)}</tr>"


def matchup_table(rows):
    return f'<table class="playoff-matchups"><tbody>{"".join(rows)}</tbody></table>'
