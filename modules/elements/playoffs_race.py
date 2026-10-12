from modules.fetch_nhl_api import get_logo

__all__ =['build_standings_tables','get_standings','format_team_standings','bold','playoff_bracket','current_round_matchups']

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

def playoff_bracket(playoff_data):

    bracket_dict = {}
    if not playoff_data:
        return bracket_dict
    rounds = playoff_data.get('rounds', [])
    current_round = min(playoff_data.get('currentRound', 0), len(rounds))

    for i in range(current_round):
        round_data = rounds[i]
        round_label = f"Round {i + 1}"
        western, eastern, finals = current_round_matchups(round_data)

        if finals:
            bracket_dict[round_label] = {"Finals": finals}
        else:
            bracket_dict[round_label] = {
                "Eastern": eastern,
                "Western": western
            }

    return bracket_dict

def current_round_matchups(current_round_data):
    eastern_matchups = []
    western_matchups = []
    finals_matchup = []
    # Find round number & number of matchups:
    # Max 4 rounds, nr of mathcups is given by: 2^3, 2^2, 2^1, 2^1
    nr_matchups = len(current_round_data['series'])
    for series_nr in range(nr_matchups):
        top_seed = current_round_data['series'][series_nr]['topSeed']
        bottom_seed = current_round_data['series'][series_nr]['bottomSeed']

        if nr_matchups == 1:
            finals_matchup.append([top_seed, bottom_seed])
        elif series_nr < nr_matchups/2:           
            eastern_matchups.append([top_seed, bottom_seed])
        else:
            western_matchups.append([top_seed, bottom_seed])
    
    return [western_matchups, eastern_matchups, finals_matchup]
