from datetime import datetime
import pytz
from modules.fetch_nhl_api import get_logo

__all__ = ['get_upcoming_game','get_upcoming_opponent','get_venue_start_time']

def get_upcoming_opponent(games_by_date,n=1):
    current_date = datetime.now()
    current_date = current_date.replace(hour=0, minute=0, second=0, microsecond=0)
    # Filter and get the first upcoming game
    upcoming_games = sorted([game for game in games_by_date if game['game_date'] >= current_date], key=lambda x: x['game_date'])
    print(upcoming_games)
    next_games = upcoming_games[:n] if upcoming_games else None
    return next_games

def get_upcoming_game(next_game):   
    if next_game != None: 
        next_opponent_logo = get_logo(next_game['opponent_abr'])
        utc_start_time = next_game['startTimeUTC']        
        display_next_game_info = f"""{next_game['game_venue']}
        <a href="javascript:void(0);" class="team-link">
        <img src="{next_opponent_logo}" style="width: 100px">
        </a>on """
    else:
        display_next_game_info = f""" No games scheduled """
        utc_start_time = None
    return display_next_game_info, utc_start_time

def get_venue_start_time(utc_start_time, venue_timezone):
    # Parse the UTC start time into a datetime object
    utc_time = datetime.strptime(utc_start_time, "%Y-%m-%dT%H:%M:%SZ")
    
    # Convert to timezone-aware datetime in UTC
    utc_time = pytz.utc.localize(utc_time)
    
    # Convert to the venue's time zone
    venue_tz = pytz.timezone(venue_timezone)
    venue_time = utc_time.astimezone(venue_tz)

    # Get the time zone abbreviation (PST, PDT, EST, EDT, etc.)
    timezone_abbr = venue_time.tzname()

    # Manually format hour to avoid Windows issues with %-I
    hour = venue_time.hour % 12 or 12  # Convert 0 to 12 for 12-hour format
    minute = venue_time.strftime("%M")  # Get minutes
    am_pm = venue_time.strftime("%p").lower()  # Get AM/PM in lowercase
    
    # Return formatted time as "7:30pm PST"
    return f"{hour}:{minute}{am_pm} {timezone_abbr}"

