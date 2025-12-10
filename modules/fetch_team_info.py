from modules.fetch_nhl_api import get_logo
import os
import json

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

def get_team_color(team_info):
    team_name = team_info['team_name']
    # Make sure the JSON file exists
    json_path = os.path.join(os.path.dirname(__file__), "nhl_team_colors.json")
    if not os.path.exists(json_path):
        raise FileNotFoundError("nhl_team_colors.json not found. Please run the scraper first.")

    # Load JSON data
    with open(json_path, "r") as f:
        team_data = json.load(f)

    # Search for the matching team
    for team in team_data:
        if team["team"].lower() == team_name.lower():
            return {
                "primary": team.get("primary"),
                "secondary": team.get("secondary"),
                "accent": team.get("accent")
            }

    raise ValueError(f"Could not find colors for {team_name}")


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