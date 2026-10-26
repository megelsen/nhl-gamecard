import os, json, re, tempfile
from datetime import datetime, timedelta


CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)

DATE_FORMAT = "%Y-%m-%d"
CACHE_FILE_RE = re.compile(r"^(?P<name>.+)_(?P<date>\d{4}-\d{2}-\d{2})\.json$")


def get_cache_path(name, date=None):
    date = date or datetime.now().strftime(DATE_FORMAT)
    return os.path.join(CACHE_DIR, f"{name}_{date}.json")

def load_cache(name):
    path = get_cache_path(name)
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return None

def latest_cache_path(name):
    """Path of the newest cache file for `name` from any day, or None."""
    dates = [m.group("date") for m in map(CACHE_FILE_RE.match, os.listdir(CACHE_DIR)) if m and m.group("name") == name]
    return get_cache_path(name, max(dates)) if dates else None

def load_latest_cache(name):
    """Return the newest cached entry for `name` from any day (today included), or None."""
    dates = []
    for filename in os.listdir(CACHE_DIR):
        match = CACHE_FILE_RE.match(filename)
        if match and match.group("name") == name:
            dates.append(match.group("date"))
    for date in sorted(dates, reverse=True):
        try:
            with open(get_cache_path(name, date), "r") as f:
                data = json.load(f)
        except (OSError, ValueError):
            continue
        if data:
            return data
    return None

def save_cache(name, data):
    """Write to a temp file and rename it into place, so a crash mid-write can't leave a
    truncated cache file behind."""
    path = get_cache_path(name)
    fd, tmp_path = tempfile.mkstemp(dir=CACHE_DIR, suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(data, f)
        os.replace(tmp_path, path)
    except BaseException:
        try:
            os.remove(tmp_path)
        except OSError:
            pass
        raise

def is_cache_fresh(name):
    path = get_cache_path(name)
    return os.path.exists(path)

def prune_cache(keep_days=3):
    """Delete cache files older than `keep_days`, keeping recent ones as stale fallbacks."""
    cutoff = (datetime.now() - timedelta(days=keep_days)).strftime(DATE_FORMAT)
    for filename in os.listdir(CACHE_DIR):
        match = CACHE_FILE_RE.match(filename)
        if match and match.group("date") < cutoff:
            try:
                os.remove(os.path.join(CACHE_DIR, filename))
            except OSError:
                pass
