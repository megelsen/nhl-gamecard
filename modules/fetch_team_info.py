from modules.fetch_nhl_api import get_logo

__all__ = ['get_team_info','get_team_color','lighten_hex_color']

def get_team_info(standings_data,team_abbr='CAR'):
    for team in standings_data['standings']:
        if team['teamAbbrev']['default'] == team_abbr:
            team_info = {

                    "query_team": team['teamCommonName']['default'],
                    "team_conference": team['conferenceName'],
                    "team_division": team['divisionName'],
                    "team_name": team['teamName']['default'],
                    "query_team_logo": f"""<img src="{get_logo(team_abbr)}" width="50">""",
                    "query_team_logo_big": get_logo(team_abbr),
                    "opposite_conference": 'Eastern' if team['conferenceName'] == 'Western' else 'Western'
                }
    return team_info

def get_team_color(team_abbr):
    nhl_team_colors = {
        'ANA': '#F47A38',  # Anaheim Ducks
        'ARI': '#8C2633',  # Arizona Coyotes
        'BOS': '#FFB81C',  # Boston Bruins
        'BUF': '#002654',  # Buffalo Sabres
        'CGY': '#C8102E',  # Calgary Flames
        'CAR': '#CC0000',  # Carolina Hurricanes
        'CHI': '#CF0A2C',  # Chicago Blackhawks
        'COL': '#6F263D',  # Colorado Avalanche
        'CBJ': '#041E42',  # Columbus Blue Jackets
        'DAL': '#006847',  # Dallas Stars
        'DET': '#CE1126',  # Detroit Red Wings
        'EDM': '#041E42',  # Edmonton Oilers
        'FLA': '#041E42',  # Florida Panthers
        'LAK': '#111111',  # Los Angeles Kings
        'MIN': '#154734',  # Minnesota Wild
        'MTL': '#AF1E2D',  # Montreal Canadiens
        'NSH': '#FFB81C',  # Nashville Predators
        'NJD': '#CE1126',  # New Jersey Devils
        'NYI': '#00539B',  # New York Islanders
        'NYR': '#0038A8',  # New York Rangers
        'OTT': '#C52032',  # Ottawa Senators
        'PHI': '#F74902',  # Philadelphia Flyers
        'PIT': '#CFC493',  # Pittsburgh Penguins
        'SJS': '#006D75',  # San Jose Sharks
        'SEA': '#001628',  # Seattle Kraken
        'STL': '#002F87',  # St. Louis Blues
        'TBL': '#002868',  # Tampa Bay Lightning
        'TOR': '#00205B',  # Toronto Maple Leafs
        'VAN': '#00205B',  # Vancouver Canucks
        'VGK': '#B4975A',  # Vegas Golden Knights
        'WSH': '#041E42',  # Washington Capitals
        'WPG': '#041E42',  # Winnipeg Jets
        'UTA': '#71AFE5',
    }

    return nhl_team_colors.get(team_abbr)

def lighten_hex_color(hex_color, factor):
    # Convert hex to RGB
    r = int(hex_color[1:3], 16)
    g = int(hex_color[3:5], 16)
    b = int(hex_color[5:7], 16)

    # Mix the color with white (255, 255, 255)
    r_new = int(r + (255 - r) * factor)
    g_new = int(g + (255 - g) * factor)
    b_new = int(b + (255 - b) * factor)

    # Convert back to hex and return
    return f"#{r_new:02x}{g_new:02x}{b_new:02x}"