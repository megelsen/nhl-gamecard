# scheduler.py
import os
import logging
import time
from datetime import datetime
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
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
    logging.info("🚀 Starting daily NHL data cache refresh...")

    try:
        current_date = datetime.utcnow().strftime("%Y-%m-%d")

        # Refresh general data
        season_data = get_season_data()
        save_cache("season_data", season_data)

        standings_data = get_current_standings(current_date)
        save_cache(f"standings_{current_date}", standings_data)

        # Refresh each team's data
        for team in TEAM_LIST:
            logging.info(f"Updating cache for {team}")
            try:
                save_cache(f"schedule_{team}", get_schedule(team))
                save_cache(f"team_stats_{team}", get_team_stats(team))
                time.sleep(0.5)  # avoid API throttling
            except Exception as e:
                logging.error(f"Failed to update {team}: {e}")

        # Refresh playoff data
        playoff_data = get_playoff_series("20232024")
        save_cache("playoff_series_20232024", playoff_data)

        logging.info("✅ Daily cache refresh complete.")
    except Exception as e:
        logging.exception(f"❌ Cache update failed: {e}")


def start_scheduler():
    """Run APScheduler continuously in a standalone worker process."""
    cache_dir = "cache"
    os.makedirs(cache_dir, exist_ok=True)

    # Run once immediately on startup
    files = [f for f in os.listdir(cache_dir) if f.endswith(".json")]
    if not files:
        logging.info("🟡 Cache empty on startup — performing initial build...")
        update_daily_cache()

    scheduler = BlockingScheduler(timezone="UTC")

    # Schedule automatic refresh at 04:00 and 10:00 UTC
    scheduler.add_job(update_daily_cache, CronTrigger(hour=4, minute=0))
    scheduler.add_job(update_daily_cache, CronTrigger(hour=10, minute=0))

    logging.info("✅ Scheduler running (04:00 and 10:00 UTC). Waiting for next job...")
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logging.info("🛑 Scheduler stopped manually.")


if __name__ == "__main__":
    start_scheduler()
