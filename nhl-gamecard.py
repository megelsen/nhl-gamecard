import requests
from datetime import datetime
from collections import defaultdict
from IPython.display import SVG, display, HTML
import pandas as pd
from flask import Flask, render_template_string, request, render_template, Response, session, send_from_directory, redirect, url_for
import os
from threading import Thread


# Import custom functions
from modules import *
from scheduler import start_scheduler

app = Flask(__name__)
app.secret_key = os.urandom(24)

team_abbr_list = [
"ANA", "BOS", "BUF", "CGY", "CAR", "CHI", "COL", "CBJ", "DAL",
"DET", "EDM", "FLA", "LAK", "MIN", "MTL", "NJD", "NSH", "NYI", "NYR",
"OTT", "PHI", "PIT", "SEA", "SJS", "STL", "TBL", "UTA", "TOR", "VAN", "VGK",
"WPG", "WSH",
]
@app.route("/", methods=["GET"])
def home():
    return redirect(url_for("team_page", team_abbr="NYR"))  # Default to MIN

@app.route("/<team_abbr>", methods=["GET", "POST"])
def team_page(team_abbr):
    if request.method == "POST":
        team_abbr = request.form.get("team_abbr", "UTA").upper()
        return redirect(url_for("team_page", team_abbr=team_abbr))  # Redirect on selection


    # Build the dropdown HTML
    dropdown_html = ''.join([f'<option value="{abbr}" {"selected" if abbr == team_abbr else ""}>{abbr}</option>' for abbr in team_abbr_list])

    schedule_data = get_schedule(team_abbr)
    current_date = datetime.now().strftime("%Y-%m-%d")
    season_data = get_season_data()
    # Check whether current date is past last game of regular season:
    current_date_format = datetime.strptime(current_date, "%Y-%m-%d").date()
    last_reg_season_format = datetime.strptime(season_data['currentDate'], "%Y-%m-%d").date()
    if current_date_format > last_reg_season_format:
        current_date = last_reg_season_format
        post_season = 1
    else: 
        post_season = 0
    standings_data = get_current_standings(current_date)    
    team_stats_data = get_team_stats(team_abbr)


    # Load Team info
    team_info = get_team_info(standings_data, team_abbr)
    team_color = get_team_color(team_abbr)  
    light_color = lighten_hex_color(team_color,0.25)
    # Read Schedule
    current_season_id = get_season_id()
    season_start = get_season_start(season_data,current_season_id)
    season_end = get_season_end(current_season_id)
    games_by_date, games_by_opponent =  get_games_data(team_info,schedule_data,season_data,current_season_id)
    # Playoff Data
    # playoff_series_data = get_playoff_series(current_season_id)
    playoff_series_data = get_playoff_series('20232024')
    # Sort games by opponents: 
    sorted_opponents = sort_games_by_opponent(games_by_opponent)
    # Put into table
    record_table_eastern, record_table_western = build_records_table(sorted_opponents)

    if team_info["team_conference"] == "Eastern":
        record_table_html_1 = record_table_eastern.to_html(classes="table_records",escape=False, index=False)
        record_table_html_2 = record_table_western.to_html(classes="table_records",escape=False, index=False)
    else:
        record_table_html_2 = record_table_eastern.to_html(classes="table_records",escape=False, index=False)
        record_table_html_1 = record_table_western.to_html(classes="table_records",escape=False, index=False)


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
    next_games = get_upcoming_opponent(games_by_date,5)  or []      
    next_game = next_games[0] if next_games and next_games[0] is not None else None
    next_opponent = next_games[0]['opponent_abr'] if next_games and next_games[0] is not None else None
    html_next_game, utc_starttime = get_upcoming_game(next_game)
    html_next_opponent_summary = team_summary(next_opponent,standings_data)
    # Get next Opponent Top Scorer:
    opponent_stats = get_team_stats(next_games[0]['opponent_abr'])
    top_scorer_opponent = find_top_scorer(opponent_stats)
    point_leaders_opponent = find_pointleaders(opponent_stats,nr_top)
    html_pts_leader_table_opponent = build_leaders_table(point_leaders_opponent,'P')
    goal_leaders_opponent = find_goalleaders(opponent_stats,nr_top)
    html_goals_leader_table_opponent = build_leaders_table(goal_leaders_opponent,'G')
    assist_leaders_opponent = find_assistleaders(opponent_stats,nr_top)
    html_assists_leader_table_opponent = build_leaders_table(assist_leaders_opponent,'A')
    
    # Generate html for next 5 games    
    next_games_data = []

    for i in range(1, 5):  # Adjust range based on the number of games you want
        if i < len(next_games) and next_games[i] is not None:
            html_game, utc_starttime_upcoming = get_upcoming_game(next_games[i])
            next_games_data.append((html_game, utc_starttime_upcoming))
            # Access results like this:
            # next_game_data[0][0] -> html_next_game_2
            # next_game_data[0][1] -> utc_starttime_2
        else:
            next_games_data.append(("", ""))


    # Previous games
    html_last_games = get_previous_games(games_by_date,nr_games=3)
    # Playoffs race standings
    html_standings_table = build_playoffs_race_table(team_info,standings_data)
    # Playoff Bracket
    playoff_data = playoff_bracket(playoff_series_data)

    # Some styling variables:
    min_width_team_summary = 515
    min_width_previous_games = 300
    outer_margin = 12
    card_gap = 24
    card_padding = 8

    max_width_medium_screen = 2*min_width_team_summary + min_width_previous_games + 2*outer_margin + 4*card_gap
    max_width_small_screen = 2*min_width_team_summary + 2*outer_margin
    max_width_smallest_screen = min_width_team_summary + 2*outer_margin

    # Store variables in session
    session["team_color"] = team_color
    session["card_gap"] = card_gap
    session["light_color"] = light_color
    session["max_width_medium_screen"] = max_width_medium_screen
    session["max_width_small_screen"] = max_width_small_screen
    session["max_width_smallest_screen"] = max_width_smallest_screen
    session["outer_margin"] = outer_margin
    session["card_padding"] = card_padding
    session["card_gap"] = card_gap
    session["min_width_previous_games"] = min_width_previous_games
    session["min_width_team_summary"] = min_width_team_summary

    vars = {
        "team_info": team_info,  # Pass it directly
        "dropdown_html": dropdown_html,
        "top_scorer": top_scorer,
        "html_team_summary": html_team_summary,
        "html_pts_leader_table": html_pts_leader_table,
        "html_goals_leader_table": html_goals_leader_table,
        "html_assists_leader_table": html_assists_leader_table,
        "html_standings_table": html_standings_table,
        "html_next_game": html_next_game,
        "next_games_data": next_games_data,
        "html_next_opponent_summary": html_next_opponent_summary,
        "top_scorer_opponent": top_scorer_opponent,
        "html_pts_leader_table_opponent": html_pts_leader_table_opponent,
        "html_goals_leader_table_opponent": html_goals_leader_table_opponent,
        "html_assists_leader_table_opponent": html_assists_leader_table_opponent,
        "html_last_games": html_last_games,
        "record_table_1": record_table_html_1,
        "record_table_2": record_table_html_2,
        "utc_starttime": utc_starttime,
        "max_width_smallest_screen": max_width_smallest_screen,
    }
    return render_template("index.html",**vars)

# Dynamic CSS files
@app.route('/body.css')
def dynamic_body_css():
    team_color = session.get("team_color", "white")
    outer_margin = session.get("outer_margin", "12px")
    return Response(render_template("dynamic/styles/body.css.jinja", team_color=team_color, outer_margin=outer_margin), mimetype="text/css")

@app.route('/cards.css')
def dynamic_card_css():
    card_padding = session.get("card_padding","8px")
    min_width_team_summary = session.get("min_width_team_summary","515px")
    return Response(render_template("dynamic/styles/cards.css.jinja", card_padding=card_padding,min_width_team_summary=min_width_team_summary), mimetype="text/css")

@app.route('/container.css')
def dynamic_container_css():
    card_gap = session.get("card_gap", "4px")
    min_width_team_summary = session.get("min_width_team_summary","515px")
    min_width_previous_games = session.get("min_width_previous_games","300px")
    return Response(render_template("dynamic/styles/container.css.jinja", card_gap=card_gap,min_width_team_summary=min_width_team_summary,min_width_previous_games=min_width_previous_games,), mimetype="text/css")

@app.route('/media_scaling.css')
def dynamic_media_scaling_css():
    max_width_medium_screen = session.get("max_width_medium_screen","1400px")
    max_width_small_screen = session.get("max_width_small_screen","1000px")
    max_width_smallest_screen = session.get("max_width_smallest_screen","515px")
    return Response(render_template("dynamic/styles/media_scaling.css.jinja", max_width_medium_screen=max_width_medium_screen,max_width_small_screen=max_width_small_screen,max_width_smallest_screen=max_width_smallest_screen,), mimetype="text/css")

@app.route('/previous_games.css')
def dynamic__prevGame_css():
    min_width_team_summary = session.get("min_width_team_summary","515px")
    min_width_previous_games = session.get("min_width_previous_games","300px")
    return Response(render_template("dynamic/styles/previous_games.css.jinja", min_width_team_summary=min_width_team_summary,min_width_previous_games=min_width_previous_games,), mimetype="text/css")

@app.route('/team_dropdown.css')
def dynamic_dropdown_css():
    light_color = session.get("lightcolor", "white")
    outer_margin = session.get("outer_margin", "12px")
    return Response(render_template("dynamic/styles/team_dropdown.css.jinja", outer_margin=outer_margin,light_color=light_color), mimetype="text/css")

@app.route('/title_card.css')
def dynamic_titleCard_css():
    card_gap = session.get("card_gap", "4px")
    return Response(render_template("dynamic/styles/title_card.css.jinja", card_gap=card_gap,), mimetype="text/css")

@app.route("/refresh")
def manual_refresh():
    from scheduler import update_daily_cache
    def manual_refresh():
        def run_refresh():
            try:
                update_daily_cache()
            except Exception as e:
                print(f"[ERROR] Manual refresh failed: {e}")

        Thread(target=run_refresh).start()
        return "✅ Refresh started in background. Check logs for progress."

@app.route('/health')
def health():
    return "OK", 200

# Dynamic JS
#@app.route('/applyScaling.js')
#def dynamic_js():
 #   return Response(render_template("dynamic/scripts/applyScaling.js.jinja", max_width_smallest_screen=max_width_smallest_screen,), mimetype="application/javascript")
# Run function
if __name__ == "__main__":
    # Start your background scheduler (runs at 6:00 and 10:00 UTC daily)
    start_scheduler()
    #app.run(host='0.0.0.0', port=10000)# debug=True)  # Use `host="0.0.0.0", port=80` for production
    app.run(debug=False)# )