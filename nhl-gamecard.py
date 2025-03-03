import requests
from datetime import datetime
from collections import defaultdict
from IPython.display import SVG, display, HTML
import pandas as pd
from flask import Flask, render_template_string, request  
# Import custom functions
from modules import *


app = Flask(__name__)

# List of NHL team abbreviations (you can expand this list as needed)
team_abbr_list = [
    "ANA", "ARI", "BOS", "BUF", "CGY", "CAR", "CHI", "COL", "CBJ", "DAL",
    "DET", "EDM", "FLA", "LAK", "MIN", "MTL", "NJD", "NSH", "NYI", "NYR",
    "OTT", "PHI", "PIT", "SEA", "SJS", "STL", "TBL", "UTA", "TOR", "VAN", "VGK",
    "WPG", "WSH",
]

@app.route("/", methods=["GET", "POST"])
def home():
    # For design purposes:
    RUN_HTML_ONLY = False
    STORE_OUTPUT = False
    
    # Select Team (Make INPUT in future)
    team_abbr= "UTA"
    if request.method == "POST":
        team_abbr = request.form.get("team_abbr", "UTA").upper()
    # Build the dropdown HTML
    dropdown_html = ''.join([f'<option value="{abbr}" {"selected" if abbr == team_abbr else ""}>{abbr}</option>' for abbr in team_abbr_list])
    if not RUN_HTML_ONLY:
        # Fetch data from API
        schedule_data = get_schedule(team_abbr)
        current_date = datetime.now().strftime("%Y-%m-%d")
        standings_data = get_current_standings(current_date)    
        team_stats_data = get_team_stats(team_abbr)
        season_data = get_season_data()

        # Load Team info
        team_info = get_team_info(standings_data, team_abbr)
        team_color = get_team_color(team_abbr)  
        light_color = lighten_hex_color(team_color,0.25)
        # Read Schedule
        current_season_id = get_season_id()
        season_start = get_season_start(season_data,current_season_id)
        season_end = get_season_end(current_season_id)
        games_by_date, games_by_opponent =  get_games_data(team_info,schedule_data,season_data,current_season_id)
        # Sort games by opponents: 
        sorted_opponents = sort_games_by_opponent(games_by_opponent)
        # Put into table
        record_table = build_records_table(sorted_opponents)
        # Summary of team:
        html_team_summary = team_summary(team_abbr,standings_data)
        # Find top scorer 
        top_scorer = find_top_scorer(team_stats_data)
        # Next game
        next_game = get_upcoming_opponent(games_by_date)
        html_next_game = get_upcoming_game(next_game)
        html_next_opponent_summary = team_summary(next_game['opponent_abr'],standings_data)
        # Previous games
        html_last_games = get_previous_games(games_by_date,nr_games=3)
        # Playoffs race standings
        html_standings_table = build_playoffs_race_table(team_info,standings_data)

        if STORE_OUTPUT:
            data = {
                "team_info": team_info,
                "record_table": record_table,
                "html_team_summary": html_team_summary,
                "top_scorer": top_scorer,
                "html_next_game": html_next_game,
                "html_next_opponent_summary": html_next_opponent_summary,
                "html_last_games": html_last_games,
                "html_standings_table": html_standings_table,
                "team_color": team_color,
                "light_color": light_color,
            }
            save_data(data)
    else:
        data = load_data()
        team_info = data["team_info"]
        record_table = data["record_table"]
        html_team_summary = data["html_team_summary"]
        top_scorer = data["top_scorer"]
        html_next_game = data["html_next_game"]
        html_next_opponent_summary = data["html_next_opponent_summary"]
        html_last_games = data["html_last_games"]
        html_standings_table = data["html_standings_table"]
        team_color = data["team_color"]
        light_color = data["light_color"]
    # HTML styling for compact table
    opponent_table_style = """
    <style>
        table {
            border-collapse: collapse;
            width: auto;  /* Set width to auto to minimize space */
            font-size: 12px;  /* Smaller font size */
            img {
            max-width: 30px;  /* Smaller logo images */
            height: auto;
            }}
        td, th {
            padding: 4px 6px;
            margin: 0;
            text-align: center;  
            border: none;  /* No borders */
        }
    </style>
    """

    # Define CSS for centering content
    summary_style = """
        <style>
            table {
                width: auto;
                border-collapse: collapse;
            }
            th, td {
                text-align: right;
                border: 1px solid black;
            }
        </style>
    """

    # Some styling variables:
    min_width_team_summary = 515
    min_width_previous_games = 300
    outer_margin = 12
    card_gap = 24
    card_padding = 12

    max_width_medium_screen = 2*min_width_team_summary + min_width_previous_games + 2*outer_margin + 4*card_gap
    max_width_small_screen = 2*min_width_team_summary + 2*outer_margin
    max_width_smallest_screen = min_width_team_summary + 2*outer_margin

    # Combine them into one HTML page with CSS grid layout
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Data Tables</title>
        <style>
            body {{                
                font-family: Arial, sans-serif;
                background-color: {team_color};
                color: #333;
                font-size: 18px;
                margin: {outer_margin}px;
            }}

            .team-dropdown {{
                font-size: 16px;  
                padding: 12px 20px;  
                border-radius: 8px;  
                border: 2px solid #ccc;  
                background-color: #fcfcfc;  
                color: #333; 
                cursor: pointer; 
                width: 200px;  
                transition: all 0.3s ease;  
                margin: {outer_margin}px;
            }}

                /* Style for the dropdown when hovered */
                .team-dropdown:hover {{
                    border-color: #f1f1f1;  /* Change border color on hover */
                    background-color: #f2f2f2;  /* Change background color on hover */
                }}

                /* Style for the selected option */
                .team-dropdown:focus {{
                    border-color: {light_color};  /* Highlight border when selected */
                    background-color: #f2f2f2;  /* Light background on focus */
                    outline: none;  /* Remove outline */
                }}

            .container {{
                display: grid;
                grid-template-columns: minmax({min_width_team_summary}px, 1fr) minmax({min_width_team_summary}px, 1fr) minmax({min_width_previous_games}px, 1fr);            
                gap: {card_gap}px;
                justify-self: anchor-center;
                margin-bottom: {card_gap}px;
            }}            
            
            .container_title {{
                justify-self: center;
            }}
            .title_card {{
                display: grid;
                grid-template-columns: 150px 1fr min-content;
                align-items: center;
                justify-self: center;
                margin-bottom: {card_gap}px;
                > img{{width: 150px}};
            }}

            .top_row_element {{
                display: grid;
                grid-template-columns: 1fr 1fr 1fr;
                white-space: nowrap;
                gap: 4px;
                align-items: center;
                text-align: left;        
                justify-items: center;
                
            }}
                .top_card_header{{
                    grid-row: 1;
                    grid-column: 2;
                }}

                .top-scorer-label {{
                    grid-row: 2;
                    font-weight: bold;
                }}

                .top-scorer-info {{ 
                    grid-row: 2;
                    grid-column: 2;
                    align-items: center;
                }}
                .headshot-img {{
                    grid-row: 1 / span 2;  
                    grid-column: 3;
                    align-self: end;
                    justify-self: end;
                    }}

                /* Team summary spans full width in row 4 */
                .team-summary {{
                    grid-row: 3;
                    grid-column: 1 / span 3;
                    width: fit-content;                
                    align-self: self-end;
                    justify-self: center;
                }}

                .upcoming_game{{
                    grid-row: 2;
                    grid-column: 1 / span 3
                }}

                .previous_game{{
                    grid-column: 3;
                    justify-items: center;
                    width: -webkit-fill-available"
                }}

            .game_display {{
            display: grid;
            grid-template-columns: min-content 70px 1fr;
            align-items: center;
            gap: 4px;
            align-self: stretch;
            }}

            .card_display {{
                background: #fefefe;  
                border-radius: 12px;          
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1); /* Optional shadow for depth */
                padding: {card_padding}px;            
                width: -webkit-fill-available;
                justify-items: anchor-center;
                min-width: max-content;
                
            }}

            /* Ensure logo is properly displayed */
            h1 {{
                align-items: center;
                gap: 100px; /* Space between text and image */
                width: 100%; /* Ensure h1 uses the full available width */
                max-width: 100%; /* Ensure it doesn't overflow */
            }}


            /* Table styling */
            table {{
                justify-items: center
                border-collapse: collapse; /* Removes unnecessary borders */
                width: 100%; /* Ensure full width */
                border: none;
                width: fit-content
                place-self: center;
            }}

            th {{
                background-color: #ffffff;
                color: black;
                text-align: center;
                border: none;
                font-size: 18px;
            }}

            tr:nth-child(odd) {{
                background-color: #f2f2f2;
                text-align: center;
                border: none;
                font-size: 18px;
            }}

            tr:nth-child(even) {{
                background-color: #fcfcfc;
                text-align: center;
                border: none;
                font-size: 18px;
            }}

            @media (max-width: {max_width_medium_screen}px) {{

                .title_card {{
                    grid-column: span 2;
                }}
                .container {{
                    grid-template-columns: 1fr 1fr;
                }}
                .previous_game {{
                    grid-column: 1 / span 2;
                    justify-items: center;
                }}
            }}

            @media (max-width: {max_width_small_screen}px) {{ 
               
                .container {{
                    grid-template-columns: 1fr;
                }}
                .previous_game {{
                    grid-column: 1;
                }}
                .title_card {{
                    grid-template-columns: 150px 1fr;                                      
                    }}
                .dropdown_wrapper{{
                    grid-column: span 2;
                }}
            }}

            @media screen and (max-width: {max_width_smallest_screen}px) {{
                body {{
                    transform: scale(0.75); 
                    transform-origin: top;
                }}
            }}
        </style>
        <script>
            // JavaScript function to automatically submit the form when the dropdown changes
            function handleDropdownChange() {{
                document.getElementById("team_form").submit();
            }}

                    // Function to synchronize widths
            function synchronizeWidths() {{
                const sourceElement = document.getElementById('widthSourceElement');
                const targetElements = document.querySelectorAll('.widthTargetElement');                
                const sourceWidth = sourceElement.offsetWidth;
                const adjustedWidth = sourceWidth - 0*{card_padding};
                targetElements.forEach(element => {{
                    element.style.width = `${{adjustedWidth}}px`;
                }});
            }}

            // Call the function initially and on window resize
            window.addEventListener('load', synchronizeWidths);
            window.addEventListener('resize', synchronizeWidths);
        </script>
    </head>
    <body>
        <div class="container_title widthTargetElement">
            <div class="title_card card_display">
                <img src="{team_info['query_team_logo_big']}">
                <h1>
                    {team_info['team_name']}
                </h1>
                <form class="dropdown_wrapper" id="team_form" method="POST">
                    <select class="team-dropdown" id="team_abbr" name="team_abbr" onchange="handleDropdownChange()">
                        {dropdown_html}
                    </select>        
                </form>
            </div>
        </div>
        <div class="container" id="widthSourceElement">
            <div class="top_row_element card_display">
                <h2 class="top_card_header">Stats</h2>
                <p class="top-scorer-label">Top scorer:</p>
                <div class ="top-scorer-info">
                    <p style="  margin-block-end: 0">{top_scorer['name']}</p>            
                    <p style="  margin-block: 0">({ top_scorer['goals']}G-{ top_scorer['assists']}A-{ top_scorer['points']}P)</p>
                </div>
                <div class="headshot-img">
                    <img src={ top_scorer['headshot_url']} style="max-width: 150px;">
                </div>
                <div class="team-summary">
                    { html_team_summary }
                </div>
            </div>
            <div class="top_row_element card_display">
                <h2  class="top_card_header">Next game</h2>
                <div class="game_display upcoming_game">
                    {html_next_game} 
                </div>
                <div class="team-summary">
                    {html_next_opponent_summary}
                </div>                
            </div>
            <div class="previous_game card_display">
            <h2>Last games</h2>
            <p class="game_display previous_game">{html_last_games[0]}</p>
            <p class="game_display previous_game">{html_last_games[1]}</p>
            <p class="game_display previous_game">{html_last_games[2]}</p>
            </div>
        </div>
        <div class="container widthTargetElement">
            <div class="table card_display">
                <h2>
                Standings
                </h2>
                <p>{html_standings_table}</p>
            </div>
            <div class="card_display">
                <h2> Record vs {team_info['team_conference']} </h2>
                {opponent_table_style + record_table.iloc[:len(record_table) // 2].to_html(escape=False,index=False)}
            </div>
            <div class="card_display">
                <h2>  Record vs {team_info['opposite_conference']} </h2>
                {opponent_table_style + record_table.iloc[len(record_table) // 2:,:3].to_html(escape=False,index=False)}
            </div>
        </div>        
    </body>
    </html>
    """
    return render_template_string(html_content)

"""
# Save to a file or display it
filename = "output.html"
with open(filename, 'w') as file:
    file.write(html_content)

import webbrowser
webbrowser.open(filename)  # Automatically open in browser
"""

    
if __name__ == "__main__":
    #app.run(host='0.0.0.0', port=10000)# debug=True)  # Use `host="0.0.0.0", port=80` for production
    app.run(debug=True)# )