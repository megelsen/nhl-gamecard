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
    "ANA", "BOS", "BUF", "CGY", "CAR", "CHI", "COL", "CBJ", "DAL",
    "DET", "EDM", "FLA", "LAK", "MIN", "MTL", "NJD", "NSH", "NYI", "NYR",
    "OTT", "PHI", "PIT", "SEA", "SJS", "STL", "TBL", "UTA", "TOR", "VAN", "VGK",
    "WPG", "WSH",
]

@app.route("/", methods=["GET", "POST"])
def home():
    # For design purposes:
    RUN_HTML_ONLY = False
    STORE_OUTPUT = False
    
    # Select Team 
    team_abbr= "CAR"
    if request.method == "POST":
        team_abbr = request.form.get("team_abbr", "CAR").upper()
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
        nr_top = 5
        point_leaders = find_pointleaders(team_stats_data,nr_top)
        html_pts_leader_table = build_leaders_table(point_leaders,'P')
        goal_leaders = find_goalleaders(team_stats_data,nr_top)
        html_goals_leader_table = build_leaders_table(goal_leaders,'G')
        assist_leaders = find_assistleaders(team_stats_data,nr_top)
        html_assists_leader_table = build_leaders_table(assist_leaders,'A')

        # Next game
        next_game = get_upcoming_opponent(games_by_date)
        html_next_game, utc_starttime = get_upcoming_game(next_game)
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
                "point_leaders": point_leaders,
                "goal_leaders": goal_leaders,
                "assist_leaders": assist_leaders,
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
        point_leaders = data["point_leaders"]
        goal_leaders = data["goal_leaders"]
        assist_leaders = data["assist_leaders"]
        html_next_game = data["html_next_game"]
        html_next_opponent_summary = data["html_next_opponent_summary"]
        html_last_games = data["html_last_games"]
        html_standings_table = data["html_standings_table"]
        team_color = data["team_color"]
        light_color = data["light_color"]


    # HTML styling for opponent table
    opponent_table_style = """
    <style>
        .teams_table {
            border-collapse: collapse;
            width: auto;  /* Set width to auto to minimize space */
            font-size: 12px;  /* Smaller font size */
            align-self: center;
            justify-self: left;
            img {
                max-width: 50px;  /* Smaller logo images */
                height: auto;

            }}
        td, th {
            padding: 4px 6px;
            margin: 0;
            text-align: center;  
            border: none;  /* No borders */
            border-collapse: collapse;
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
        <title>NHL Gamecard</title>
            <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined&display=block" />
        <style>
            body {{                
                font-family: Arial, sans-serif;
                background-color: {team_color};
                color: #333;
                font-size: 18px;
                margin: {outer_margin}px;
                transition: all 0.3s ease;
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
                transition: all 0.01s ease;  
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
            .content {{
                display: grid;
            }}
            .container {{
                display: grid;
                grid-template-columns: {min_width_team_summary}px {min_width_team_summary}px minmax({min_width_previous_games}px, 1fr);  
                gap: {card_gap}px;
                justify-self: anchor-center;
                margin-bottom: {card_gap}px;
                justify-self: center;
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
                    .upcoming_game span{{
                        display: flex;
                        align-items: center;
                    }}

                .previous_game{{
                    display: grid
                    grid-column: 3;
                    justify-items: center;
                    width: -webkit-fill-available;
                    width: -moz-available;
                    min-width: {min_width_previous_games};
                    max-width: {min_width_team_summary};
                    justify-content: center;
                    display: grid;
                    margin: 4px;
                }}

            .game_display {{
                display: grid;
                grid-template-columns: min-content 90px 3fr 1fr;
                /* align-items: center; */
                gap: 4px;
                align-self: stretch;
            }}

            .title_card_display {{
                background: #fefefe;  
                border-radius: 12px;          
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1); /* Optional shadow for depth */
                padding: {card_padding}px;            
                width: -webkit-fill-available;                
                width: -moz-available;
                justify-items: anchor-center;
                
            }}
            .card_display {{
                background: #fefefe;  
                border-radius: 12px;          
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1); /* Optional shadow for depth */
                padding: {card_padding}px;            
                width: -webkit-fill-available;
                width: -moz-available;
                justify-items: anchor-center;
                min-width: max-content;
                display: grid;
                justify-content: center;
                
            }}

            /* Ensure logo is properly displayed */
            h1 {{
                align-items: center;
                gap: 100px; /* Space between text and image */
                width: 100%; /* Ensure h1 uses the full available width */
                max-width: 100%; /* Ensure it doesn't overflow */
            }}

            h2 {{
                align-self: baseline;
                margin-block-start: 0.4em;
            }}
            /* Table styling */
            .dataframe{{
                border-collapse: collapse;
            }}
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

            .team-link {{
                text-decoration: none; /* Remove any default text decoration */
                display: inline-block;
            }}
            .recap-link {{                
                text-decoration: none; 
                color: inherit;                 
                transition: background-color 0.2s ease-in-out, text-decoration 0.2s;
            }}
           
            .recap-link:hover span {{
                opacity: 0.85;
            }}

            /* Darkens more when clicked */
            .recap-link:active span{{
                opacity: 0.7;
            }}

            .more-stats {{
                padding: 10px; 
                grid-column: 3;
                grid-row: 1;
                align-self: start;
                justify-self: end;
                cursor: pointer;
                transition: transform 0.2s;
                z-index: 10;
            }}

                /* Hover effect on the icon */
                .more-dots:hover {{
                    transform: scale(1.2);
                }}

                /* stats popup */
                .stats-popup {{
                    display: none; /* Hidden by default */
                    position: fixed;
                    z-index: 1;
                    left: 0;
                    top: 0;
                    width: 500px;
                    height: 100%;
                    background-color: rgba(0, 0, 0, 0.4); /* Background overlay */
                    padding-top: 60px;
                    justify-content: center;
                    align-items: center;
                    transform: translateX(-100%);
                }}

                /* Modal Content */
                .stats-popup-content {{
                    align-self: baseline;
                    background-color: white;
                    padding: 4px;  
                                      
                }}
                .leaders-table{{
                    border-collapse: collapse;
                    width: auto;  /* Set width to auto to minimize space */
                    font-size: 16px;  /* Smaller font size */
                    text-align: left;  
                    img {{
                        max-width: 120px;  
                        height: auto;
                    }}
                    td, th {{
                        padding: 4px 6px;
                        margin: 0;
                        text-align: left;  
                        border: none;  /* No borders */
                        border-collapse: collapse;
                        background: #ffffff;
                        font-size: larger;
                    }}
                }}

                /* Close Button */
                .close {{
                    position:absolute;
                    padding-right: 16px;
                    padding-top: 8px;
                    justify-self: right;
                    color: #aaa;
                    float: right;
                    font-size: 28px;
                    font-weight: bold;
                }}

                .close:hover,
                .close:focus {{
                    color: black;
                    text-decoration: none;
                    cursor: pointer;
                }}

                .modal-nav{{
                    display: grid;
                    grid-template-columns: 50px 100px 50px;
                    white-space: nowrap;
                    align-items: center;
                    text-align: center;
                }}
                    .nav-button{{
                        background: none;
                        border: none;
                        font-size: 24px;
                        cursor: pointer;
                        padding: 4px;
                        color: inherit; /* Matches text color */
                    }}

                    .nav-button:hover {{
                        color: #007bff; /* Slight color change on hover */
                    }}

            /* Loading wheel container */
            #loading-wheel {{
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(255, 255, 255, 0.8); 
                display: flex;
                align-items: center;
                justify-content: center;
                z-index: 9999; 
            }}

            /* Spinner animation */
            .spinner {{
                width: 50px;
                height: 50px;
                border: 5px solid #ccc;
                border-top: 5px solid #3498db; 
                border-radius: 50%;
                animation: spin 1s linear infinite;
            }}

            /* Keyframes for the spin effect */
            @keyframes spin {{
                0% {{ transform: rotate(0deg); }}
                100% {{ transform: rotate(360deg); }}
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
                .content {{                
                    transform: scale(0.6);            
                    transform-origin: top ;
                }}
            }}
        </style>

    </head>
    <body>
        <div id="loading-wheel">
            <div class="spinner"></div>
        </div>
        <div class="content"> 
            <div class="container_title widthTargetElement ">
                <div class="title_card title_card_display">
                    <img src="{team_info['query_team_logo_big']}">
                    <h1>
                        {team_info['team_name']}
                    </h1>
                    <form class="dropdown_wrapper" id="team_form" method="POST">
                        <select class="team-dropdown" id="team_abbr" name="team_abbr" onchange="handleTeamChange()">
                            {dropdown_html}
                        </select>        
                    </form>
                </div>
            </div>
            <div class="container" id="widthSourceElement">
                <div class="top_row_element card_display" id="statsCard">
                    <h2 class="top_card_header">
                        Stats
                    </h2>                    
                    <span class="material-symbols-outlined more-stats" id="moreStats">
                        more_horiz
                    </span>
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
                <div id="statsPopUp" class="stats-popup">                    
                    <!-- Modal Content -->
                    <div class="stats-popup-content card_display">
                        <!-- Closing Button -->
                        <span class="close" id="closeBtn">&times;</span>
                        <!-- Navigation Buttons -->
                        <div class="modal-nav">
                            <button id="prevButton" class="nav-button">
                                <span class="material-symbols-outlined">
                                    arrow_back_ios
                                </span>
                            </button>
                            <h2 id="modal-title">Points</h2>
                            <button id="nextButton" class="nav-button">
                                <span class="material-symbols-outlined">
                                    arrow_forward_ios
                                </span>
                            </button> 
                        </div>
                        <div id="modalContent">
                            <div id="points-leaders-content">                                
                                {html_pts_leader_table} 
                            </div> 
                            <div id="goal-leaders-content" style="display: none;">
                                {html_goals_leader_table}
                            </div>
                            <div id="assist-leaders-content" style="display: none;">
                                {html_assists_leader_table}
                            </div>    
                        </div>                      
                    </div>
                </div>
                <div class="top_row_element card_display">
                    <h2  class="top_card_header">Next game</h2>
                    <div class="upcoming_game">
                         <span id="event-time" data-utc-time={utc_starttime}>
                            {html_next_game}
                        </span>
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
        </div>

        <script>
            
            // JavaScript function to automatically submit the form when the dropdown changes
            function handleTeamChange() {{
                // Show loading wheel immediately
                document.getElementById("loading-wheel").style.display = "flex";
                // Slight delay to ensure UI updates before form submission
                setTimeout(function () {{
                    document.getElementById("team_form").submit();
                }}, 50); // Adjust delay if needed
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

            function applyScaling() {{
                var deviceWidth = window.visualViewport ? window.visualViewport.width : window.innerWidth;
                var max_width_smallest_screen = {max_width_smallest_screen };                 

                // Apply scaling only if the device width is <= max_width_smallest_screen
                if (deviceWidth <= max_width_smallest_screen) {{
                    var containers = document.querySelectorAll('.content');  // Get the content element
                    var scaleFactor = deviceWidth / (max_width_smallest_screen);
                    containers.forEach(function(container){{
                        container.style.transform = 'scale(' + scaleFactor + ')';
                        container.style.transformOrigin = 'left top';
                    }})
                }} else {{
                    // Reset scaling if width is greater than the max width
                    var containers = document.querySelectorAll('.content');
                    containers.forEach(function(container) {{
                        container.style.transform = 'scale(1)';
                    }});
                }}
            }}

            function formatEventTime(utcStartTime) {{
                const utcDate = new Date(utcStartTime); // Convert UTC string to Date object
                const options = {{
                    hour: "numeric",
                    minute: "2-digit",
                    hour12: true,
                    timeZoneName: "short"
                }};

                // Get user's local timezone formatted time
                const formatter = new Intl.DateTimeFormat(navigator.language, options);
                const parts = formatter.formatToParts(utcDate);

                let hour, minute, ampm, timezoneAbbr;
                for (const part of parts) {{
                    if (part.type === "hour") hour = part.value;
                    if (part.type === "minute") minute = part.value;
                    if (part.type === "dayPeriod") ampm = part.value.toLowerCase();
                    if (part.type === "timeZoneName") timezoneAbbr = part.value;
                }}

                return `${{hour}}:${{minute}}${{ampm}} ${{timezoneAbbr}}`;
            }}
            
            // Call the function initially and on window resize
            window.addEventListener('load', function() {{    
                synchronizeWidths();
                // synchronizeWidthsStatsPopUp();
            }});
            window.addEventListener('resize', function() {{    
                synchronizeWidths();
                setTimeout(applyScaling, 500);
            }});

            document.addEventListener("DOMContentLoaded", function () {{
                // Show loading wheel
                document.getElementById("loading-wheel").style.display = "flex";

                setTimeout(function () {{
                    // Hide loading wheel after content loads
                    document.getElementById("loading-wheel").style.display = "none";

                    // Run other functions after loading
                    synchronizeWidths();
                    applyScaling();
                }}, 500); // Adjust timeout as needed
            }});

            // GET TIMEZONE OF USER
            
            // Get the event time from the HTML element
            const eventElement = document.getElementById("event-time");
            const utcStartTime = eventElement.getAttribute("data-utc-time"); 
            
            if (utcStartTime) {{
                const formattedTime = formatEventTime(utcStartTime);
                // const currentContent = eventElement.innerHTML.trim();
               
                eventElement.innerHTML = `${{eventElement.innerHTML}} ${{formattedTime}}`;
            }} else {{
                eventElement.innerHTML = "Time unavailable";
            }}

            // Function to extract team abbreviation from the image source or alt attribute
            function extractTeamAbbr(imgElement) {{
                // If the abbreviation is in the 'src' URL (e.g., https://assets.nhle.com/logos/nhl/svg/team_abbr_light.svg)
                const src = imgElement.getAttribute('src');
                const match = src.match(/\/([A-Z]{{3}})_light\.svg/); // Regex to match the 3-letter team abbreviation
                
                if (match) {{
                    return match[1]; // Return the team abbreviation
                }}
                
                return null; // If no abbreviation found
            }}

            // Add event listener for all team image links
            const teamLinks = document.querySelectorAll('.team-link');
            teamLinks.forEach(link => {{
                link.addEventListener('click', function(event) {{
                    const imgElement = link.querySelector('img'); // Get the image inside the clicked link
                    const teamAbbr = extractTeamAbbr(imgElement); // Extract the abbreviation

                    if (teamAbbr) {{
                        // Reload the page with the new team_abbr in the query string
                        // Set the team_abbr value in the hidden input field
                        document.getElementById("team_abbr").value = teamAbbr;

                        // Call the handleTeamChange function to submit the form
                        handleTeamChange(); // Reusing your function to submit the form
                    }}
                }});
            }});

        const sections = [
            {{ id: "points-leaders-content", title: "Points" }},
            {{ id: "goal-leaders-content", title: "Goals" }},
            {{ id: "assist-leaders-content", title: "Assists" }}
        ];

        let currentIndex = 0;
        const modalTitle = document.getElementById("modal-title");

        document.getElementById("prevButton").addEventListener("click", () => switchContent(-1));
        document.getElementById("nextButton").addEventListener("click", () => switchContent(1));

        function switchContent(direction) {{
            document.getElementById(sections[currentIndex].id).style.display = "none"; // Hide current
            currentIndex = (currentIndex + direction + sections.length) % sections.length; // Cycle index
            document.getElementById(sections[currentIndex].id).style.display = "block"; // Show new
            modalTitle.textContent = sections[currentIndex].title; // Update header
        }}


        // Get the modal, the button, and the close button
            const modal = document.getElementById("statsPopUp");
            const moreDots = document.getElementById("moreStats");
            const closeBtn = document.getElementById("closeBtn");

            function positionModal() {{
                modal.style.visibility = "hidden"; // Hide the modal but keep it in the layout to calculate size
                modal.style.display = "flex"; // Temporarily display to calculate width/height
                const rect = moreDots.getBoundingClientRect(); // Get position of the icon
                const modalWidth = modal.offsetWidth;  // Get the modal's width
                const modalHeight = modal.offsetHeight; // Get the modal's height
                modal.style.visibility = "visible"; // Make sure the modal is visible after calculations

                // Make sure the modal doesn't go off-screen
                const viewportWidth = window.innerWidth;
                const viewportHeight = window.innerHeight;
                const dotsBottom = rect.bottom
               
                // Position modal below the "more_horiz" icon by default
                let modalRight = rect.left;
                let modalTop = dotsBottom - 100;

                console.log("Modal Width:", modalWidth);
                console.log("Modal Height:", modalHeight);
                console.log("Modal Right:", modalRight);
                console.log("Modal Top:", modalTop);
                console.log("Viewport Width:", viewportWidth);
                console.log("Viewport Height:", viewportHeight);
                // Check if the modal overflows the right edge of the viewport

                // Set the modal's position
                modal.style.left = `${{modalRight}}px`;
                modal.style.top = `${{modalTop}}px`;
                modal.style.display = "flex"; // Show the modal
            }}

            moreDots.onclick = function() {{
                positionModal(); // Position the modal when "more_horiz" is clicked
            }};
            // When the user clicks on the close button, close the modal
            closeBtn.onclick = function() {{    
                modal.style.display = "none"; // Hide the modal
            }}

            // When the user clicks anywhere outside the modal, close it
            window.onclick = function(event) {{
                if (event.target === modal) {{
                    modal.style.display = "none"; // Hide the modal
                }}
            }}
        </script>      
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