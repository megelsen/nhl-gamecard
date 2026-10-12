import requests
from datetime import datetime
from urllib.parse import urlparse
from flask import Flask, request, render_template, Response, session, send_from_directory, redirect, url_for, abort
from werkzeug.exceptions import HTTPException
import os
from threading import Thread


# Import custom functions
from modules import *
from scheduler import start_scheduler, update_daily_cache, TEAM_LIST

app = Flask(__name__)
# A fixed key keeps sessions (which the dynamic CSS routes read) valid across restarts
app.secret_key = os.environ.get("SECRET_KEY") or os.urandom(24)

if os.environ.get("RUN_SCHEDULER", "true") == "true":
    try:
        start_scheduler()
    except Exception as e:
        # Don't let a failed initial cache refresh (e.g. a bad/non-JSON
        # response from the NHL API) prevent the app from booting.
        print(f"[ERROR] start_scheduler failed, continuing without initial cache warm-up: {e}")

team_abbr_list = TEAM_LIST
DEFAULT_TEAM = "NYR"

@app.errorhandler(Exception)
def handle_internal_error(e):
    # Let normal HTTP errors (404, 405, ...) through unchanged
    if isinstance(e, HTTPException):
        return e
    # Catches downstream failures too (e.g. a None value slipping through from
    # a failed/uncached NHL API call): log the traceback, return a clean 503.
    app.logger.exception(f"Unhandled exception in request: {e}")
    return Response(
        "NHL data is temporarily unavailable. Please try again in a few minutes.",
        status=503,
    )

@app.route("/", methods=["GET"])
def home():
    return redirect(url_for("team_page", team_abbr=DEFAULT_TEAM))

@app.route("/favicon.ico")
def favicon():
    return send_from_directory(os.path.join(app.root_path, "static"), "stick-64x64.ico", mimetype="image/vnd.microsoft.icon")

@app.route("/<team_abbr>", methods=["GET", "POST"])
def team_page(team_abbr):
    if request.method == "POST":
        team_abbr = request.form.get("team_abbr", DEFAULT_TEAM).upper()
        if team_abbr not in team_abbr_list:
            team_abbr = DEFAULT_TEAM
        return redirect(url_for("team_page", team_abbr=team_abbr))  # Redirect on selection

    if team_abbr not in team_abbr_list:
        if team_abbr.upper() in team_abbr_list:
            return redirect(url_for("team_page", team_abbr=team_abbr.upper()))
        abort(404)


    # Build the dropdown HTML
    dropdown_html = ''.join([f'<option value="{abbr}" {"selected" if abbr == team_abbr else ""}>{abbr}</option>' for abbr in team_abbr_list])

    schedule_data = get_schedule(team_abbr)
    current_date = datetime.now().strftime("%Y-%m-%d")
    season_data = get_season_data()

    if schedule_data is None or season_data is None:
        # NHL API is unreachable/blocked and there's no cached fallback yet.
        # Fail gracefully instead of raising on season_data['currentDate'] below.
        return Response(
            "NHL data is temporarily unavailable (upstream API unreachable and no "
            "cache yet). Please try again in a few minutes.",
            status=503,
        )

    current_season_id = get_season_id()
    season_start = get_season_start(season_data,current_season_id)
    season_end = get_season_end(current_season_id)
    # season_data['currentDate'] is the latest date with standings (it trails today by a
    # day during the season, and stays on the last regular-season day afterwards)
    standings_date = min(current_date, season_data.get('currentDate') or current_date)
    standings_data = get_current_standings(standings_date)
    team_stats_data = get_team_stats(team_abbr)

    if standings_data is None or team_stats_data is None:
        return Response(
            "NHL data is temporarily unavailable (team stats/standings unreachable "
            "and no cache yet). Please try again in a few minutes.",
            status=503,
        )

    # Team overview of all teams. Playoff stats are empty until the playoffs start;
    # teams that aren't in the playoffs keep their regular-season special teams.
    regular_season_summary = get_team_summary(current_season_id, 0)
    playoff_summary = get_team_summary(current_season_id, 1)


    # Load Team info
    team_info = get_team_info(standings_data, team_abbr)
    if team_info is None:
        return Response(
            f"No standings data for {team_abbr} yet. Please try again in a few minutes.",
            status=503,
        )
    team_colors = get_team_color(team_info["team_name"])  
    light_color = lighten_hex_color(team_colors['primary'],0.25)
    standings_highlight = lighten_hex_color(team_colors['primary'], 0.8)

    # Read Schedule


    games_by_date, games_by_opponent =  get_games_data(team_info,schedule_data,season_data,current_season_id)
    roster_tables = build_roster_tables(team_abbr, get_roster(team_abbr), team_stats_data, games_by_date)
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
    team_summary_list = team_summary(team_abbr,standings_data)
    html_team_summary = generate_team_summary_table(team_summary_list)
    # Special Teams
    special_teams = get_special_teams_for(team_info['team_name'], regular_season_summary, playoff_summary)
    # Team Stats:
    

    # Find top scorer 
    top_scorer = find_top_scorer(team_stats_data)
    nr_top = 5
    point_leaders = find_pointleaders(team_stats_data,nr_top)
    html_pts_leader_table = build_leaders_table(point_leaders,'P')
    goal_leaders = find_goalleaders(team_stats_data,nr_top)
    html_goals_leader_table = build_leaders_table(goal_leaders,'G')
    assist_leaders = find_assistleaders(team_stats_data,nr_top)
    html_assists_leader_table = build_leaders_table(assist_leaders,'A')
    # Get Goalie Info:
    goalies = get_goalies(team_stats_data)
    html_goalie_table = []
    for goalie in goalies:
        html_goalie_table.append(build_goalie_table(goalie))
      
    # Next game
    # Next game (there may be none, e.g. in the off-season)
    next_games = get_upcoming_opponent(games_by_date,5)  or []
    next_game = next_games[0] if next_games and next_games[0] is not None else None
    next_opponent = next_game['opponent_abr'] if next_game else None
    opponent_logo = get_logo(next_opponent) if next_opponent else None
    previous_matchup = get_previous_matchup(team_abbr,team_info, next_opponent,sorted_opponents,season_data,current_season_id)
    html_previous_matchup, previous_date = display_previous_matchup(previous_matchup)
    #previous_winning_goal_scorer_data = get_player_stats(previous_matchup['winning_goal_scorer']['playerId'])
    #previous_winning_goal_scorer = get_stats_from_playerID(previous_winning_goal_scorer_data)

    html_next_game, utc_starttime = get_upcoming_game(next_game)
    opponent_summary_list = team_summary(next_opponent,standings_data)
    html_next_opponent_summary = generate_team_summary_table(opponent_summary_list)

    opponent_info = get_team_info(standings_data, next_opponent) if next_opponent else None
    opponent_special_teams = get_special_teams_for(opponent_info['team_name'] if opponent_info else None, regular_season_summary, playoff_summary)
    # Opponent colors
    opponent_colors = get_team_color(next_game['opponent_name']) if next_game else {"primary": "#d1d1d1"}
    # Comparison bars: the opponent's side needs a color that stands out from the team's
    compare_colors = {team_abbr: team_colors['primary']}
    if next_opponent:
        compare_colors[next_opponent] = pick_contrasting_color(
            team_colors['primary'],
            [opponent_colors.get('primary'), opponent_colors.get('secondary'), opponent_colors.get('accent')],
        )

    # Get next Opponent Top Scorer (opponent stats may be missing: show empty sections then)
    opponent_stats = (get_team_stats(next_opponent) if next_opponent else None) or {}
    top_scorer_opponent = find_top_scorer(opponent_stats)
    for scorer in (top_scorer, top_scorer_opponent):
        if scorer:
            scorer.update(skater_edge_stats(scorer["playerID"]))
    topscorer_compare = compare_mount(skater_comparison(top_scorer, top_scorer_opponent, team_abbr, next_opponent))
    point_leaders_opponent = find_pointleaders(opponent_stats,nr_top)
    html_pts_leader_table_opponent = build_leaders_table(point_leaders_opponent,'P')
    goal_leaders_opponent = find_goalleaders(opponent_stats,nr_top)
    html_goals_leader_table_opponent = build_leaders_table(goal_leaders_opponent,'G')
    assist_leaders_opponent = find_assistleaders(opponent_stats,nr_top)
    html_assists_leader_table_opponent = build_leaders_table(assist_leaders_opponent,'A')
    # Opponet Goalie   
    goalies_opponent = get_goalies(opponent_stats)
    html_goalie_table_opponent = []
    for goalie in goalies_opponent:
        html_goalie_table_opponent.append(build_goalie_table(goalie))

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
    standings_tables = build_standings_tables(team_abbr, standings_data)
    # Current playoff round: projected from standings until the playoffs start
    playoff_picture = build_playoff_picture(team_abbr, standings_data, get_playoff_bracket(current_season_id))
    
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
    session["team_color"] = team_colors['primary']
    session["secondary_color"] = team_colors['secondary']
    session["opponent_color"] = opponent_colors['primary']
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
        "standings_tables": standings_tables,
        "roster_tables": roster_tables,
        "topscorer_compare": topscorer_compare,
        "playoff_picture": playoff_picture,
        "compare_colors": compare_colors,
        "team_abbr": team_abbr,
        "next_opponent": next_opponent,
        "standings_highlight": standings_highlight,
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
        "goalies": goalies,
        "html_goalie_table": html_goalie_table,        
        "goalies_opponent": goalies_opponent,
        "html_goalie_table_opponent": html_goalie_table_opponent,
        "special_teams": special_teams,
        "opponent_special_teams":opponent_special_teams,
        "html_previous_matchup": html_previous_matchup,
        "previous_date": previous_date,
        "team_summary_list": team_summary_list[0] if team_summary_list else {},
        "opponent_summary_list": opponent_summary_list[0] if opponent_summary_list else {},
        "opponent_logo": opponent_logo,
        #"previous_winning_goal_scorer": previous_winning_goal_scorer,

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
    light_color = session.get("light_color", "white")
    outer_margin = session.get("outer_margin", "12px")
    return Response(render_template("dynamic/styles/team_dropdown.css.jinja", outer_margin=outer_margin,light_color=light_color), mimetype="text/css")

@app.route('/title_card.css')
def dynamic_titleCard_css():
    card_gap = session.get("card_gap", "4px")
    return Response(render_template("dynamic/styles/title_card.css.jinja", card_gap=card_gap,), mimetype="text/css")

@app.route("/player/<int:player_id>/card")
def player_card(player_id):
    # HTML fragment for the player card modal (static/js/playerCard.js)
    landing = get_player_stats(player_id)
    if not landing or "firstName" not in landing:
        abort(404)
    card = build_player_card(landing, get_player_season_report(player_id, goalie=landing.get("position") == "G"))
    colors = get_team_color(card["team_name"]) if card["team_name"] else DEFAULT_COLORS
    card["primary_color"] = colors.get("primary") or DEFAULT_COLORS["primary"]
    card["accent_color"] = pick_contrasting_color(
        card["primary_color"], [colors.get("secondary"), colors.get("accent")], min_distance=80, fallback="#d1d1d1"
    )
    return render_template("partials/player_card.html", card=card)

@app.route("/refresh")
def manual_refresh():
  
    def run_refresh():
        try:
            update_daily_cache()
        except Exception as e:
            print(f"[ERROR] Manual refresh failed: {e}")

    Thread(target=run_refresh).start()
    return " Refresh started in background. Check logs for progress."

@app.route('/debug-nhl')
def debug_nhl():
    url = request.args.get(
        "url",
        "https://api-web.nhle.com/v1/standings/now",
    )
    # Only proxy NHL API hosts, so this can't be used to make the server fetch arbitrary URLs
    parsed = urlparse(url)
    host = parsed.hostname or ""
    if parsed.scheme != "https" or not (host == "nhle.com" or host.endswith(".nhle.com")):
        return {"url": url, "error": "Only https://*.nhle.com URLs are allowed"}, 400
    try:
        res = requests.get(url, timeout=10)
        return {
            "url": url,
            "status_code": res.status_code,
            "headers": dict(res.headers),
            "body_preview": res.text[:500],
        }
    except Exception as e:
        return {"url": url, "error": str(e)}

@app.route('/health')
def health():
    return "OK", 200

# Dynamic JS
#@app.route('/applyScaling.js')
#def dynamic_js():
 #   return Response(render_template("dynamic/scripts/applyScaling.js.jinja", max_width_smallest_screen=max_width_smallest_screen,), mimetype="application/javascript")
# Run function
if __name__ == "__main__":
   
   
    #app.run(debug=True)# )
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))