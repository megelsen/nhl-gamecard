# scheduler.py
import logging
import threading
import time
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from modules import (
    get_schedule,
    get_current_standings,
    get_team_stats,
    get_season_data,
    get_playoff_bracket,
    get_team_summary,
    get_season_id,
    get_roster,
    get_moneypuck_skaters,
    get_moneypuck_goalies,
    track_fetch_failures,
)
from cache_utils import is_cache_fresh, prune_cache

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

TEAM_LIST = [
    "ANA", "BOS", "BUF", "CGY", "CAR", "CHI", "COL", "CBJ", "DAL",
    "DET", "EDM", "FLA", "LAK", "MIN", "MTL", "NJD", "NSH", "NYI", "NYR",
    "OTT", "PHI", "PIT", "SEA", "SJS", "STL", "TBL", "UTA", "TOR", "VAN", "VGK",
    "WPG", "WSH",
]

REQUEST_PAUSE_SECONDS = 0.5  # between requests during a refresh, to go easy on the NHL API

_refresh_lock = threading.Lock()


def update_daily_cache():
    """Re-fetch all critical data. Goes through the fetch functions so cache keys always
    match what the app reads; if a fetch fails, the previous cache entry is kept."""
    if not _refresh_lock.acquire(blocking=False):
        logging.info("Cache refresh already running — skipping.")
        return

    try:
        logging.info("Starting NHL data cache refresh...")
        started = time.time()
        current_date = datetime.now().strftime("%Y-%m-%d")
        season_id = get_season_id()

        with track_fetch_failures() as failed:
            season_data = get_season_data(force=True) or {}
            # Same date the app requests standings for
            standings_date = min(current_date, season_data.get("currentDate") or current_date)
            jobs = [
                (get_current_standings, standings_date),
                (get_team_summary, season_id, 0),
                (get_team_summary, season_id, 1),
                (get_playoff_bracket, season_id),
                (get_moneypuck_skaters, season_id),
                (get_moneypuck_goalies, season_id),
            ]
            for team in TEAM_LIST:
                jobs += [(get_schedule, team), (get_team_stats, team), (get_roster, team)]

            for fetch, *args in jobs:
                time.sleep(REQUEST_PAUSE_SECONDS)
                fetch(*args, force=True)

        prune_cache()
        total = len(jobs) + 1  # + season data
        elapsed = time.time() - started
        if failed:
            logging.warning(
                f"Cache refresh finished in {elapsed:.0f}s: {total - len(failed)}/{total} updated, "
                f"{len(failed)} failed (previous cache kept, if any): {', '.join(failed)}"
            )
        else:
            logging.info(f"Cache refresh complete in {elapsed:.0f}s: all {total} entries updated.")
    finally:
        _refresh_lock.release()


def start_scheduler():
    scheduler = BackgroundScheduler(timezone="UTC")

    scheduler.add_job(update_daily_cache, CronTrigger(hour=6, minute=0))
    scheduler.add_job(update_daily_cache, CronTrigger(hour=12, minute=0))
    scheduler.start()
    logging.info(" Scheduler started (06:00 and 12:00 UTC).")

    # Warm the cache at startup in the background so the server can bind its port right away
    if not is_cache_fresh("season_data"):
        logging.info("No cache for today on startup — refreshing in background...")
        threading.Thread(target=update_daily_cache, daemon=True).start()
    else:
        logging.info("Cache already populated for today.")
