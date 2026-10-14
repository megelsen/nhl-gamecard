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
5. [x] Slanted-split comparison bar below each stat line in the player (topscorer, goalie) and team comparisons
6. [x] Complete the playoff race module: a separate card showing the current playoff bracket, based on matchups from current standings
7. [x] Player cards: clicking a player's headshot opens a hockey-card-style modal (birthplace, nationality flag, hero image, career stats, ...)

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

For visual checks, run the app on a spare port and screenshot with headless Chrome (`--headless=new --screenshot --virtual-time-budget=6000`). To test an interaction, save the page HTML into `static/` with an injected script that clicks the controls, serve it from the app, and delete it afterwards. Without the session cookie, that copy renders with the default dynamic CSS. Headless Chrome won't lay out narrower than ~500px, so for phone widths wrap the page in a 375px `<iframe>` served from `static/`. Pointing the iframe at `/<TEAM>` itself gives the real session CSS. Compile with `py -3.11 -W error -m py_compile ...` before finishing: production is 3.11, and the local 3.14 accepts syntax 3.11 rejects (e.g. backslashes inside f-string expressions).

Set `SECRET_KEY` in production, otherwise sessions (and therefore the dynamic CSS) reset on every restart.

Useful routes: `/player/<id>/card` (player card HTML fragment), `/img-proxy?url=` (assets.nhle.com images for the PNG export), `/refresh` (force-refresh the cache in a background thread), `/debug-nhl?url=...` (proxy an `https://*.nhle.com` URL and show status/headers/body preview), `/health`. Unknown team codes return 404; lowercase codes redirect to uppercase.

## Architecture

**Request flow** — `app.py:team_page` does everything for one request: fetches schedule, season, standings, team stats, team summary, playoff series and the next opponent's stats; passes them through helper functions in `modules/`; and renders `templates/index.html` with a large `vars` dict. Most "element" helpers return **pre-built HTML strings** (or pandas `DataFrame.to_html`) that the template injects with `|safe`, so markup lives partly in Python (`modules/elements/*.py`) and partly in Jinja (`templates/index.html`, `templates/macros/`).

**Module layout** — `modules/__init__.py` and `modules/elements/__init__.py` re-export every submodule's `__all__`, and `app.py` does `from modules import *`. When adding a public function, add it to that submodule's `__all__` or it won't be visible in `app.py`.
- `modules/fetch_nhl_api.py` — all NHL API calls.
- `modules/read_schedule.py` — season ID/date math and turning a schedule into `games_by_date` / `games_by_opponent`.
- `modules/fetch_team_info.py` — team info from standings, team colors from `modules/nhl_team_colors.json`.
- `modules/elements/` — one file per dashboard section, producing HTML.
- `modules/fetch_team_colors.py` — standalone scraper (runs on import, needs `bs4`) that regenerates `nhl_team_colors.json`; not part of the app.

**Caching** — Every fetch goes through `_safe_get_json(url, cache_name, force)`: today's cache → fetch (3 attempts with exponential backoff and jitter for network errors/5xx/429, none for other 4xx; `Retry-After` is honored up to 5s for page requests and 30s for forced refreshes, longer means give up) → newest older cache file (`load_latest_cache`) → `None`. After a failed fetch, the URL is skipped for 5 minutes (stale data or `None` is returned immediately) so an outage doesn't stall every request. Cache files live in `cache/<name>_<YYYY-MM-DD>.json` (`cache_utils.py`), so "fresh" means "from today"; `prune_cache` removes files older than 3 days. Callers must handle `None`; `team_page` returns a 503 only when core data (schedule, season, standings, team stats) is missing and degrades the opponent/playoff sections otherwise. `scheduler.py` force-refreshes through the same fetch functions (so keys always match) at 06:00 and 12:00 UTC, and in a background thread at startup if there's no cache for today; a lock prevents overlapping refreshes. It pauses 0.5s between requests (~3 min for all ~100) and logs how many entries were actually updated, using `track_fetch_failures()`. `save_cache` writes atomically (temp file + rename). `modules/cache.py` / `cached_data.pkl` is an unused legacy pickle cache.

**Dynamic CSS** — Layout constants (widths, gaps, team colors) are computed in `team_page`, stored in the Flask `session`, and served by routes like `/body.css` and `/cards.css` that render `templates/dynamic/styles/*.css.jinja`. Those stylesheets depend on a `team_page` request having populated the session first. Static CSS/JS lives in `static/styles` and `static/js`; the JS handles timezone formatting, modals, the team dropdown, spoiler hiding and width syncing.

**Season phase** — `season_data['currentDate']` is the latest date with standings: it trails today by a day during the season, so don't compare it to today to detect the post-season. Standings are requested for `min(today, currentDate)` (the scheduler warms the same date). Post-season means the playoff team summary (`get_team_summary(season, 1)`) has rows; `get_special_teams_for` uses a team's playoff stats if it has any, else regular season. Team rows from the stats API are matched to standings by exact full name (`teamFullName` == standings `teamName.default`).

**Summary circles** — `templates/index.html` reads `Conf Rank` / `Conf Name` / `Conf Rank Pct` from `team_summary()` and `PP%` / `PK%` / `* Rank` / `* Rank Pct` from `get_special_teams()`. Keep those keys when changing either function.

**Standings card** — `build_standings_tables()` (`modules/elements/playoffs_race.py`) pre-renders one conference table per conference as hand-built HTML (row classes `own-team`, `cut-line`); `static/js/standingsToggle.js` only toggles `hidden`. Conferences are ordered West, then East (`CONFERENCES`), like on a map, for tabs and the playoff card alike. Use `.standings-tab`, not `.tab`, for tabs outside the topscorer modal: `topscorers_modal.js` binds every `.tab` on the page.

**Roster modal** — `build_roster_tables()` (`modules/elements/roster.py`) merges `/v1/roster/{team}/current` (all rostered players plus bio) with `club-stats` (only players who have played). Within each position tab it splits players into Lineup / Rotation / Extras, based on who dressed in the last 5 completed games (from boxscores, `get_boxscore`). Headshots carry `data-player-id` for the player cards (step 7). Use `window.addEventListener("click", ...)`, never `window.onclick =`, for outside-click closing: each modal script used to overwrite the others' handler.

**Comparisons** — Top scorers, Goalies and Last meeting all render through one JS component, `renderComparison()` in `static/js/comparison.js`. Python only supplies raw numbers: `modules/elements/compare.py` builds `{left, right, rows: [{key, left, right}]}` and `compare_mount()` embeds it as `data-compare` JSON. The goalie carousel builds the same data in JS. `COMPARE_SPECS` in `comparison.js` is the single place for labels, number formats (61%, .927, 19:06), lower-is-better stats, and amplified bars for rate stats (`spread`). To add a stat row, add its key there and supply the value from Python. In Top scorers and Goalies the top of the photo lines up with the team tags above the stat rows, with `.headshot-caption` (name, number, Show Top 5 / goalie arrows) underneath. Colors come from `window.compareColors` (team primary; the opponent's color via `pick_contrasting_color`). Advanced rows come from NHL EDGE (`get_skater_edge` / `get_goalie_edge`): shot speed and skating speed for skaters, high-danger save % for goalies. EDGE also has high-danger shots/goals, but the user removed those rows. Expected goals (xG) isn't available from any NHL endpoint.

**Playoff card** — `build_playoff_picture()` (`playoffs_race.py`) shows only the current round. Until `/v1/playoff-bracket/{year}` (year = the season's end year) has series, it projects round 1 from standings: the better division winner plays WC2, the other WC1, and 2nd plays 3rd in each division. During the playoffs it shows the lowest round with an unfinished series; after the Final, the Final. Seeds use standings labels (M1, WC2). Each series is a stacked bracket box (`series_box`), and `bracket()` pairs consecutive series, whose winners meet next round, with CSS connector lines. Keep the series order when changing how matchups are built. Both conferences show at once in `.playoff-conferences`, a grid that puts them side by side when there's room and stacks them on phones. In the widest (3-column) layout the card spans the whole row with the brackets flanking the middle (`standings.css`); `media_scaling.css.jinja` undoes that for 2 and 1 columns. Side by side, the East bracket (`bracket(..., mirrored=True)`) has its connector lines on the left so both open towards the middle (a container query on `.playoff-conferences`).

**Player cards** — Any element with `data-player-id` opens a card. `static/js/playerCard.js` uses one delegated click listener and fetches `/player/<id>/card`. That route renders `templates/partials/player_card.html` from `build_player_card()` (`modules/elements/player_card.py`) using the cached player landing data, in the player's current team colors. The stats table shows the last 5 NHL regular seasons plus career. A traded player's per-team rows from the landing data are merged into one row (goalie GAA/SV% recalculated). Team abbreviations for the logos, and hits, come from the stats API report (`get_player_season_report`), because the landing data has only team names. Flags come from flagcdn.com via the `COUNTRY_ISO2` map (the API gives ISO alpha-3 codes); add codes there when a new country shows up. When adding a new headshot anywhere, give it `data-player-id`.

**Viewer settings** — The footer has Timezone and Units selectors (`static/js/userSettings.js`), saved in `localStorage` and applied without reloading. Scripts read `window.userSettings` / `settingsTimeZone()` and re-render on the `settingschange` event: game times (`formatEventTime.js`), speed rows in comparisons (`unit: "speed"` in `COMPARE_SPECS`; values arrive in km/h), and `.unit-value` elements carrying `data-metric` / `data-imperial` (player card size; call `applyUnits(root)` after inserting such HTML).

**PNG export** — "Export PNG" in the footer (`static/js/exportPng.js`) captures `.content` with modern-screenshot, loaded from jsDelivr on first click. (html-to-image produced a ~14 MB SVG that Chrome wouldn't decode.) Controls are left out via `EXPORT_EXCLUDE`, and spoilers are revealed by dropping their covers. assets.nhle.com sends no CORS headers, so NHL images are swapped to the same-origin `/img-proxy?url=` (assets.nhle.com only) during the capture. The Google Fonts links need `crossorigin="anonymous"` so the fonts can be embedded. Add new controls to `EXPORT_EXCLUDE`.

**No next game** — In the off-season there's no upcoming opponent: `next_game`/`next_opponent` are `None`, opponent dicts are empty, and the template and `goalieCarousel.js` render blanks/dashes. Keep that path working when touching opponent features. `TEAM_LIST` lives in `scheduler.py` and `app.py` imports it.

## Notes

- `.gitignore` ignores `*.json`, so a new JSON data file must be force-added (`nhl_team_colors.json` is tracked this way).
- `gamecard-debug.py` (gitignored) is a local script that runs the pipeline outside Flask.
