import os, json
from datetime import datetime, timedelta
import shutil



CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)

def get_cache_path(name):
    today = datetime.now().strftime("%Y-%m-%d")
    return os.path.join(CACHE_DIR, f"{name}_{today}.json")

def load_cache(name):
    path = get_cache_path(name)
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return None

def save_cache(name, data):
    path = get_cache_path(name)
    with open(path, "w") as f:
        json.dump(data, f)

def is_cache_fresh(name):
    path = get_cache_path(name)
    return os.path.exists(path)


def clear_cache():
    if os.path.exists(CACHE_DIR):
        shutil.rmtree(CACHE_DIR)
    os.makedirs(CACHE_DIR, exist_ok=True)
