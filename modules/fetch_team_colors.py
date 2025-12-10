import requests
from bs4 import BeautifulSoup
import json
import re

def expand_hex(hex_code):
    """Convert 3-digit hex (#111) to 6-digit (#111111)."""
    if hex_code and re.fullmatch(r"#([0-9a-fA-F]{3})", hex_code):
        return "#" + "".join([c*2 for c in hex_code[1:]])
    return hex_code

# URL of the page
url = "https://teamcolorcodes.com/nhl-team-color-code"

# Fetch the page
response = requests.get(url)
soup = BeautifulSoup(response.text, "html.parser")

teams = []

# Loop through all <a class="team-button">
for a in soup.find_all("a", class_="team-button"):
    team_name = a.get_text(strip=True)
    
    style = a.get("style", "")
    
    # Extract colors using regex
    primary_match = re.search(r"background-color:\s*(#[0-9A-Fa-f]{3,6})", style)
    secondary_match = re.search(r"border-bottom:\s*\d+px solid\s*(#[0-9A-Fa-f]{3,6})", style)
    accent_match = re.search(r"color:\s*([^;]+)", style)
    
    primary = expand_hex(primary_match.group(1)) if primary_match else None
    secondary = expand_hex(secondary_match.group(1)) if secondary_match else None
    accent = accent_match.group(1) if accent_match else None
    
    teams.append({
        "team": team_name,
        "primary": primary,
        "secondary": secondary,
        "accent": accent
    })

# Save to JSON file
with open("nhl_team_colors.json", "w") as f:
    json.dump(teams, f, indent=4)

print(f"Extracted {len(teams)} teams and saved to nhl_team_colors.json")
