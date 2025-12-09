# scheduler.py
import os
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
import logging
from modules import (
    get_schedule,
    get_current_standings,
    get_team_stats,
    get_season_data,
    get_playoff_series,
)
from cache_utils import save_cache

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

TEAM_LIST = [
    "ANA", "BOS", "BUF", "CGY", "CAR", "CHI", "COL", "CBJ", "DAL",
    "DET", "EDM", "FLA", "LAK", "MIN", "MTL", "NJD", "NSH", "NYI", "NYR",
    "OTT", "PHI", "PIT", "SEA", "SJS", "STL", "TBL", "UTA", "TOR", "VAN", "VGK",
    "WPG", "WSH",
]

def update_daily_cache():
    """Fetch all critical data and save it to cache once per day."""
    logging.info("Starting daily NHL data cache refresh...")

    # Example: use today's date for standings
    current_date = datetime.now().strftime("%Y-%m-%d")

    # Refresh general data
    season_data = get_season_data()
    save_cache("season_data", season_data)

    standings_data = get_current_standings(current_date)
    save_cache(f"standings_{current_date}", standings_data)

    # Refresh each team's data
    for team in TEAM_LIST:
        logging.info(f"Updating cache for {team}")
        save_cache(f"schedule_{team}", get_schedule(team))
        save_cache(f"team_stats_{team}", get_team_stats(team))

    # Refresh playoff data (use hardcoded or dynamically detected season)
    playoff_data = get_playoff_series("20232024")
    save_cache("playoff_series_20232024", playoff_data)

    logging.info("Daily cache refresh complete.")


def start_scheduler():
    scheduler = BackgroundScheduler(timezone="UTC")

    scheduler.add_job(update_daily_cache, CronTrigger(hour=6, minute=0))
    scheduler.add_job(update_daily_cache, CronTrigger(hour=12, minute=0))
    scheduler.start()
    logging.info(" Scheduler started (06:00 and 12:00 UTC).")

    # Check cache folder at startup
    cache_dir = "cache"
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)

    files = [f for f in os.listdir(cache_dir) if f.endswith(".json")]
    if not files:
        logging.info("🟡 Cache empty on startup — refreshing now...")
        update_daily_cache()
        logging.info(" Cache built successfully.")
    else:
        logging.info("🟢 Cache already populated.")