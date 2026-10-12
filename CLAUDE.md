# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Working agreement

- Work through the roadmap below one step at a time.
- For each step: investigate first, then outline a plan and **ask the user for confirmation before changing any code**.
- When a step is done, summarize what changed, mark it done here, and suggest moving on to the next step. Don't start the next step without confirmation.

## Roadmap

1. [x] Plan and fix the known bugs
2. [x] Find out why the team summary (Rank, PP, PK) isn't working
3. [x] League-wide standings: switch between East and West in the standings card
4. [x] Roster overview: a "Roster" button in the title row opens a modal (like the topscorer modal) with the full roster and relevant stats, split into Goalies, Defense, and Forwards
5. [ ] Slanted-split comparison bar below each stat line in the player (topscorer, goalie) and team comparisons
6. [ ] Complete the playoff race module: a separate card showing the current playoff bracket, based on matchups from current standings
7. [ ] Player cards: clicking a player's headshot opens a hockey-card-style modal (birthplace, nationality flag, hero image, career stats, ...)

## Overview

Flask app that renders a single-page "gamecard" dashboard for an NHL team (standings, leaders, goalies, next opponent comparison, previous games, records vs. every opponent, playoff race). Data comes from the public NHL APIs (`api-web.nhle.com/v1/...` and `api.nhle.com/stats/rest/...`). Deployed on Render at `https://nhl-gamecard.onrender.com` via the `Dockerfile`; a GitHub Action (`.github/workflows/keep-alive.yml`) hits `/health` every 5 minutes to keep the free instance awake. (Don't point it at `/refresh`: that forces a full re-fetch.)

## Commands

```bash
pip install -r requirements.txt
python app.py                       # dev server on $PORT (default 8080)
gunicorn -b :8080 app:app           # production entrypoint (matches Dockerfile)
RUN_SCHEDULER=false python app.py   # skip the APScheduler + startup cache warm-up
```

There are no tests, linter, or build step. Verify changes by loading `/<TEAM_ABBR>` (e.g. `/NYR`) in a browser, or with `app.test_client()` and `RUN_SCHEDULER=false`. Run from a scratch directory if you don't want to touch the project's `cache/` (it's relative to the CWD). A cold cache takes ~25s per team page because every leader and goalie needs a separate player-landing request.

For visual checks, run the app on a spare port and screenshot with headless Chrome (`--headless=new --screenshot --virtual-time-budget=6000`). To test an interaction, save the page HTML into `static/` with an injected script that clicks the controls, serve it from the app, and delete it afterwards. Without the session cookie, that copy renders with the default dynamic CSS. Headless Chrome won't lay out narrower than ~500px, so for phone widths wrap the page in a 375px `<iframe>`.

Set `SECRET_KEY` in production, otherwise sessions (and therefore the dynamic CSS) reset on every restart.

Useful routes: `/refresh` (force-refresh the cache in a background thread), `/debug-nhl?url=...` (proxy an `https://*.nhle.com` URL and show status/headers/body preview), `/health`. Unknown team codes return 404; lowercase codes redirect to uppercase.

## Architecture

**Request flow** — `app.py:team_page` does everything for one request: fetches schedule, season, standings, team stats, team summary, playoff series and the next opponent's stats; passes them through helper functions in `modules/`; and renders `templates/index.html` with a large `vars` dict. Most "element" helpers return **pre-built HTML strings** (or pandas `DataFrame.to_html`) that the template injects with `|safe`, so markup lives partly in Python (`modules/elements/*.py`) and partly in Jinja (`templates/index.html`, `templates/macros/`).

**Module layout** — `modules/__init__.py` and `modules/elements/__init__.py` re-export every submodule's `__all__`, and `app.py` does `from modules import *`. When adding a public function, add it to that submodule's `__all__` or it won't be visible in `app.py`.
- `modules/fetch_nhl_api.py` — all NHL API calls.
- `modules/read_schedule.py` — season ID/date math and turning a schedule into `games_by_date` / `games_by_opponent`.
- `modules/fetch_team_info.py` — team info from standings, team colors from `modules/nhl_team_colors.json`.
- `modules/elements/` — one file per dashboard section, producing HTML.
- `modules/fetch_team_colors.py` — standalone scraper (runs on import, needs `bs4`) that regenerates `nhl_team_colors.json`; not part of the app.

**Caching** — Every fetch goes through `_safe_get_json(url, cache_name, force)`: today's cache → fetch (3 retries for network errors/5xx, none for 4xx) → newest older cache file (`load_latest_cache`) → `None`. After a failed fetch, the URL is skipped for 5 minutes (stale data or `None` is returned immediately) so an outage doesn't stall every request. Cache files live in `cache/<name>_<YYYY-MM-DD>.json` (`cache_utils.py`), so "fresh" means "from today"; `prune_cache` removes files older than 3 days. Callers must handle `None`; `team_page` returns a 503 only when core data (schedule, season, standings, team stats) is missing and degrades the opponent/playoff sections otherwise. `scheduler.py` force-refreshes through the same fetch functions (so keys always match) at 06:00 and 12:00 UTC, and in a background thread at startup if there's no cache for today; a lock prevents overlapping refreshes. `modules/cache.py` / `cached_data.pkl` is an unused legacy pickle cache.

**Dynamic CSS** — Layout constants (widths, gaps, team colors) are computed in `team_page`, stored in the Flask `session`, and served by routes like `/body.css` and `/cards.css` that render `templates/dynamic/styles/*.css.jinja`. Those stylesheets depend on a `team_page` request having populated the session first. Static CSS/JS lives in `static/styles` and `static/js`; the JS handles timezone formatting, modals, the team dropdown, spoiler hiding and width syncing.

**Season phase** — `season_data['currentDate']` is the latest date with standings: it trails today by a day during the season, so don't compare it to today to detect the post-season. Standings are requested for `min(today, currentDate)` (the scheduler warms the same date). Post-season means the playoff team summary (`get_team_summary(season, 1)`) has rows; `get_special_teams_for` uses a team's playoff stats if it has any, else regular season. Team rows from the stats API are matched to standings by exact full name (`teamFullName` == standings `teamName.default`).

**Summary circles** — `templates/index.html` reads `Conf Rank` / `Conf Name` / `Conf Rank Pct` from `team_summary()` and `PP%` / `PK%` / `* Rank` / `* Rank Pct` from `get_special_teams()`. Keep those keys when changing either function.

**Standings card** — `build_standings_tables()` (`modules/elements/playoffs_race.py`) pre-renders 4 tables (East/West × Conference/Wild Card) as hand-built HTML (row classes `own-team`, `cut-line`, `standings-group`); `static/js/standingsToggle.js` only toggles `hidden`. Use `.standings-tab`, not `.tab`, for tabs outside the topscorer modal: `topscorers_modal.js` binds every `.tab` on the page.

**Roster modal** — `build_roster_tables()` (`modules/elements/roster.py`) merges `/v1/roster/{team}/current` (all rostered players plus bio) with `club-stats` (only players who have played). Within each position tab it splits players into Lineup / Rotation / Extras, based on who dressed in the last 5 completed games (from boxscores, `get_boxscore`). Headshots carry `data-player-id` for the player cards (step 7). Use `window.addEventListener("click", ...)`, never `window.onclick =`, for outside-click closing: each modal script used to overwrite the others' handler.

**No next game** — In the off-season there's no upcoming opponent: `next_game`/`next_opponent` are `None`, opponent dicts are empty, and the template and `goalieCarousel.js` render blanks/dashes. Keep that path working when touching opponent features. `TEAM_LIST` lives in `scheduler.py` and `app.py` imports it.

## Notes

- `.gitignore` ignores `*.json`, so a new JSON data file must be force-added (`nhl_team_colors.json` is tracked this way).
- `gamecard-debug.py` (gitignored) is a local script that runs the pipeline outside Flask.
