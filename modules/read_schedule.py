from datetime import datetime
from collections import defaultdict

__all__ = ['get_season_id', 'compare_season_ids', 'get_season_start', 'get_season_end', 'get_games_data','sort_games_by_opponent']

def get_season_id():
    current_year = datetime.now().year
    current_month = datetime.now().month
    # Check if month after august, but before january (new season)
    if 8 < current_month <= 12:
        start_year = current_year
        end_year = current_year + 1
    else:
        start_year = current_year - 1
        end_year = current_year
    season_id = str(start_year) + str(end_year)
    return season_id


PAST_SEASONS = 2  # finished seasons a comparison can pick, besides the current one


def compare_season_ids(season_id=None):
    """The current season and the PAST_SEASONS before it, newest first: ["20262027", "20252026", ...]"""
    start = int(str(season_id or get_season_id())[:4])
    return [f"{year}{year + 1}" for year in range(start, start - PAST_SEASONS - 1, -1)]

def get_season_start(season_data,current_season_id):
    seasons = (season_data or {}).get("seasons") or []
    for season in seasons:
        season_id = str(season.get("id"))
        if season_id == current_season_id and season.get("standingsStart"):
            season_start = season.get("standingsStart")
            season_start = datetime.strptime(season_start, "%Y-%m-%d")
            return season_start
    # Season not listed (yet): assume it starts in September of its first year
    return datetime(int(str(current_season_id)[:4]), 9, 1)


def get_season_end(current_season_id):
    end_year = str(current_season_id)[-4:]
    season_end =  end_year + "-08-01"
    season_end = datetime.strptime(season_end, "%Y-%m-%d")
    return season_end
    

def get_games_data(team_info,schedule_data,season_data,current_season_id):
    
    query_team = team_info.get("query_team")
    start_date = get_season_start(season_data,current_season_id)
    end_date = get_season_end(current_season_id)
    games_by_date = []
    games_by_opponent = {}
    if not schedule_data:
        return games_by_date, games_by_opponent
    games = schedule_data.get("games", [])

    for game in games:
        game_date = datetime.strptime(game.get("gameDate"), "%Y-%m-%d")  # Convert string to datetime object

        # Filter games after the cutoff date
        if start_date <= game_date < end_date and (game.get("gameType") or 0) > 1:
            game_type = game.get("gameType")
            game_id = game.get("id")
            home_team = game.get("homeTeam", {}).get("commonName", {}).get("default")
            away_team = game.get("awayTeam", {}).get("commonName", {}).get("default")
            home_score = game.get("homeTeam", {}).get("score")
            away_score = game.get("awayTeam", {}).get("score")
            game_outcome = game.get("gameOutcome", {}).get("lastPeriodType")
            winning_goalie = game.get("winningGoalie", {})
            winning_goal_scorer = game.get("winningGoalScorer")
            gamecenter = game.get("gameCenterLink")
            gamecenterURL = f'https://www.nhl.com{gamecenter}'
            recap = game.get("condensedGame")
            if recap == None:
               recap = game.get("threeMinRecap")
            startTimeUTC = game.get("startTimeUTC")
            venueTimezone = game.get("venueTimezone")
            recapURL = f'https://www.nhl.com{recap}'
            
            if away_team == query_team:
              game_venue = f'<span class="alt-font">@</span>'
              opponent = home_team
              opponent_place = game.get("homeTeam", {}).get("placeName", {}).get("default")
              opponent_name = f"{opponent_place or ''} {opponent or ''}".strip()
              opponent_abr = game.get("homeTeam", {}).get("abbrev")
              opponent_score = home_score
              team_score = away_score
              opponent_logo = game.get("homeTeam", {}).get("logo")
            else:
              game_venue = "vs"
              opponent = away_team
              opponent_place = game.get("awayTeam", {}).get("placeName", {}).get("default")
              opponent_name = f"{opponent_place or ''} {opponent or ''}".strip()
              opponent_abr = game.get("awayTeam", {}).get("abbrev")
              opponent_score = away_score
              team_score = home_score
              opponent_logo = game.get("awayTeam", {}).get("logo")

            if team_score is not None and opponent_score is not None:
              # get result (W,L,OTL)
              if team_score > opponent_score:
                result = "W"
              elif game_outcome == "REG":
                result = "L"
              else:
                result = "OTL"
            else:
              result = None

            # Store the game information as a dictionary
            game_details = {
              "game_type": game_type,
              "game_id": game_id,
              "game_date": game_date,
              "home_team": home_team,
              "away_team": away_team,
              "home_score": home_score,
              "away_score": away_score,
              "game_outcome": game_outcome,
              "winning_goalie": winning_goalie,
              "winning_goal_scorer": winning_goal_scorer,
              "recap_URL": recapURL,
              "game_venue": game_venue,
              "opponent": opponent,
              "opponent_abr": opponent_abr,
              "result": result,
              "startTimeUTC": startTimeUTC,
              "venueTimezone": venueTimezone,
              "recapURL": recapURL,
              "opponent_name": opponent_name, 
              "gamecenterURL": gamecenterURL,

            }
            games_by_date.append(game_details)
            games_by_opponent.setdefault(opponent, []).append(game_details)
    return games_by_date, games_by_opponent

def sort_games_by_opponent(games_by_opponent):
    sorted_opponents = sorted(games_by_opponent.items(), key=lambda x: len(x[1]), reverse=True)
    return sorted_opponents


