// Player card modal: click any headshot with data-player-id (top scorers, goalies, Top 5, roster).
// One delegated listener, so headshots rendered later (modals, goalie carousel) work too.
// Icons on the card: flip to the league percentiles and the shot map, or compare with another player (picked by
// name search or from a team roster), shown with the shared comparison bars (comparison.js). Each side can be
// this season or a past one (window.compareSeasons), also the same player in two seasons.
const PLAYER_SEARCH_URL = "https://search.d3.nhle.com/api/v1/search/player?culture=en-us&limit=20&active=true&q=";
const COMPARE_KEYS = {
    // Same order as the Top scorers and Goalies cards, then the extra rows
    skater: ["GP", "G", "A", "P", "XGF60", "SPEED", "TOI", "XGA60", "SHOT", "PM"],
    goalie: ["GP", "W", "GAA", "SV%", "HDSV%", "SO", "GSAX"],
};
const FLIP_MS = 600; // matches the transition in player_card.css

function escapeHtml(text) {
    return String(text ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
}

// --- Shot map (partials/shot_map.html) ----------------------------------------------------
// The .shot-map container holds view (heat / zones), category and unit (total / pct). Zones swap
// their color and number from data-* attributes; the heat view paints a smoothed image of the
// 1-ft shot grid. All maps in one container (a comparison) share each color scale. Top level, since
// the card export (cardExport.js) draws maps in other views with applyShotMap().

// The categories in this map's own buttons: [[key, label], ...]
function shotMapCategories(map) {
    return [...map.querySelectorAll('[data-set="cat"]')].map(b => [b.dataset.value, b.textContent.trim()]);
}

function setShotMap(button) {
    const map = button.closest(".shot-map");
    const { set, value } = button.dataset;
    if (set === "unit" && map.classList.contains("unit-off")) return;
    if (set === "cat" && map.dataset.layout === "all") return; // every stat is shown
    if (set === "cat" && map.dataset.layout === "two") {
        // Two stats side by side: a third replaces the one picked longer ago
        const cats = map.dataset.cats.split(",");
        if (!cats.includes(value)) map.dataset.cats = [cats[1], value].join(",");
    } else {
        map.dataset[set] = value;
    }
    if (set === "layout" && value === "two" && !map.dataset.cats) {
        const other = shotMapCategories(map).find(([key]) => key !== map.dataset.cat && key !== "xg");
        map.dataset.cats = [map.dataset.cat, other[0]].join(",");
    }
    // vs xG exists per area only (a single map switches to zones; in a grid only its own cell does)
    if (set === "cat" && value === "xg" && map.dataset.layout !== "two") map.dataset.view = "zones";
    if (set === "view" && value === "heat" && map.dataset.cat === "xg" && (map.dataset.layout || "one") === "one") map.dataset.cat = "shots";
    applyShotMap(map);
}

// This map's own elements, not those of the cells of a grid inside it
function ownElements(map, selector) {
    return [...map.querySelectorAll(selector)].filter(el => el.closest(".shot-map") === map);
}

function applyShotMap(map) {
    const { view, cat, unit } = map.dataset;
    const layout = map.dataset.layout || "one";
    const cats = layout === "two" ? map.dataset.cats.split(",") : null;
    const key = cat === "xg" ? "xg" : `${cat}-${unit}`;
    const rinks = ownElements(map, ".shot-map-rink");
    ownElements(map, "[data-set]").forEach(b => b.classList.toggle("active",
        b.dataset.set === "cat" && cats ? cats.includes(b.dataset.value) : map.dataset[b.dataset.set] === b.dataset.value));
    map.classList.toggle("cats-off", layout === "all");
    // Total vs. % doesn't apply to vs xG, nor to a heat map on its own scale (same picture, only the
    // scale's numbers differ); a grid's cells each have their own scale
    map.classList.toggle("unit-off", Boolean(map.dataset.unitFixed) || (layout === "one" && cat === "xg")
        || (view === "heat" && (layout !== "one" || rinks.length < 2)));
    rinks.forEach(rink => { rink.dataset.view = cat === "xg" ? "zones" : view; });
    ownElements(map, `[data-fill-${key}]`).forEach(el => el.setAttribute("fill", el.getAttribute(`data-fill-${key}`)));
    ownElements(map, `[data-ink-${key}]`).forEach(el => el.setAttribute("fill", el.getAttribute(`data-ink-${key}`)));
    ownElements(map, `[data-text-${key}]`).forEach(el => { el.textContent = el.getAttribute(`data-text-${key}`); });
    if (view === "heat" && cat !== "xg") paintHeat(map, rinks, cat, unit === "pct");
    if (map.classList.contains("shot-map-cell")) return;
    renderShotMapGrid(map, layout, layout === "two" ? cats : shotMapCategories(map).map(([k]) => k));
}

// One map in the given category, view and unit, drawn from copies of `rinks` (a comparison's row of
// two shares one color scale), with its legends; the card's grid and the export (cardExport.js) use it
function shotMapCell(source, rinks, cat, view, unit, label) {
    const cell = document.createElement("div");
    cell.className = "shot-map shot-map-cell";
    Object.assign(cell.dataset, { view: cat === "xg" ? "zones" : view, cat, unit, stops: source.dataset.stops });
    if (label) {
        const title = document.createElement("div");
        title.className = "shot-map-cell-label";
        title.textContent = label;
        cell.append(title);
    }
    const row = document.createElement("div");
    row.className = "shot-map-cell-rinks";
    rinks.forEach(rink => row.append(rink.cloneNode(true)));
    cell.append(row, ...ownElements(source, ".shot-map-legend").map(legend => legend.cloneNode(true)));
    applyShotMap(cell);
    return cell;
}

// The card's Two / All layouts: a grid of cells instead of the single map
function renderShotMapGrid(map, layout, cats) {
    ownElements(map, ".shot-map-grid").forEach(grid => grid.remove());
    map.classList.toggle("multi", layout !== "one");
    if (layout === "one") return;
    const labels = Object.fromEntries(shotMapCategories(map));
    const rinks = ownElements(map, ".shot-map-rink");
    const grid = document.createElement("div");
    grid.className = "shot-map-grid";
    cats.forEach(cat => grid.append(shotMapCell(map, rinks, cat, map.dataset.view, map.dataset.unit, labels[cat])));
    rinks[rinks.length - 1].after(grid);
}

const HEAT_W = 85, HEAT_H = 75, HEAT_SIGMA = 3.5; // feet: the offensive zone, kernel width

// Smoothed density of [column, row, count] cells (Gaussian kernel); `share` scales to the player's total
function heatDensity(cells, share) {
    const grid = new Float32Array(HEAT_W * HEAT_H);
    const total = cells.reduce((sum, cell) => sum + cell[2], 0) || 1;
    const radius = Math.ceil(HEAT_SIGMA * 3);
    for (const [col, row, n] of cells) {
        const weight = share ? n / total : n;
        for (let y = Math.max(0, row - radius); y <= Math.min(HEAT_H - 1, row + radius); y++) {
            for (let x = Math.max(0, col - radius); x <= Math.min(HEAT_W - 1, col + radius); x++) {
                const d2 = (x - col) ** 2 + (y - row) ** 2;
                grid[y * HEAT_W + x] += weight * Math.exp(-d2 / (2 * HEAT_SIGMA ** 2));
            }
        }
    }
    return grid;
}

function heatRgb(stops, t) {
    const position = t * (stops.length - 1);
    const i = Math.min(Math.floor(position), stops.length - 2);
    const f = position - i;
    const a = stops[i].match(/\w\w/g).map(h => parseInt(h, 16));
    const b = stops[i + 1].match(/\w\w/g).map(h => parseInt(h, 16));
    return a.map((v, k) => Math.round(v + (b[k] - v) * f));
}

function paintHeat(map, rinks, cat, share) {
    const stops = JSON.parse(map.dataset.stops);
    const grids = [...rinks].map(rink => heatDensity((JSON.parse(rink.dataset.heat || "{}")[cat]) || [], share));
    const max = Math.max(...grids.map(grid => grid.reduce((m, v) => Math.max(m, v), 0))) || 1;
    const canvas = document.createElement("canvas");
    canvas.width = HEAT_W;
    canvas.height = HEAT_H;
    const context = canvas.getContext("2d");
    rinks.forEach((rink, index) => {
        const image = context.createImageData(HEAT_W, HEAT_H);
        grids[index].forEach((value, i) => {
            const t = value / max;
            if (t < 0.03) return; // transparent: the white ice shows
            const [r, g, b] = heatRgb(stops, Math.sqrt(t));
            // Fades in from transparent, so a few stray shots stay a light tint
            image.data.set([r, g, b, Math.round(255 * Math.min(0.92, 0.08 + t * 1.6))], i * 4);
        });
        context.putImageData(image, 0, 0);
        rink.querySelector(".shot-map-heat").setAttribute("href", canvas.toDataURL());
    });
}

function initShotMaps(root) {
    root.querySelectorAll(".shot-map:not(.shot-map-cell)").forEach(applyShotMap);
}

document.addEventListener("DOMContentLoaded", function () {
    const modal = document.getElementById("playerCardPopUp");
    const content = document.getElementById("playerCardContent");
    const closeBtn = document.getElementById("closeBtnPlayerCard");
    if (!modal || !content) return;

    const cardCache = new Map();
    const jsonCache = new Map();
    let cardHtml = "";     // the open card, to return to from the comparison
    let compareLeft = null; // {id, goalie, color, accent} of the open card's player
    const seasonOptions = window.compareSeasons || []; // [{id, label}], this season first
    let seasons = {};       // {left, right}: each side's season id ("" = this season)
    let searchToken = 0;   // drops search/roster answers that arrive after a newer request

    const spinner = '<div class="player-card-loading"><div class="spinner"></div></div>';

    function getJson(url) {
        if (!jsonCache.has(url)) {
            jsonCache.set(url, fetch(url).then(res => {
                if (!res.ok) throw new Error(res.status);
                return res.json();
            }).catch(error => {
                jsonCache.delete(url);
                throw error;
            }));
        }
        return jsonCache.get(url);
    }

    function showCard(html) {
        delete content.dataset.view;
        cardHtml = html;
        content.innerHTML = html;
        applyUnits(content);
        initShotMaps(content);
    }

    async function openCard(playerId) {
        modal.style.display = "flex";
        if (cardCache.has(playerId)) {
            showCard(cardCache.get(playerId));
            return;
        }
        content.innerHTML = spinner;
        try {
            // Versioned, so browsers don't keep showing a card from before a deploy
            const res = await fetch(`/player/${playerId}/card?v=${encodeURIComponent(window.playerCardVersion || "")}`);
            if (!res.ok) throw new Error(res.status);
            const html = await res.text();
            cardCache.set(playerId, html);
            showCard(html);
        } catch (e) {
            content.innerHTML = '<p class="hockey-card-empty">Player info is unavailable right now.</p>';
        }
    }

    // Front -> percentiles -> shot map -> front, always turning the same way: every flip adds half a
    // turn, and the next face is pre-turned to face the viewer when it ends. The current and next
    // face are shown while the card turns; afterwards the others get `hidden` again.
    function flip(card) {
        const faces = [...card.querySelectorAll(".hockey-card-flipper > .hockey-card")];
        if (faces.length < 2) return;
        card.turns = (card.turns || 0) + 1;
        const next = faces[card.turns % faces.length];
        next.classList.toggle("face-turned", card.turns % 2 === 1);
        next.hidden = false;
        void card.offsetWidth; // start the turn from the current position
        card.querySelector(".hockey-card-flipper").style.transform = `rotateY(${card.turns * 180}deg)`;
        const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
        clearTimeout(card.flipTimer);
        card.flipTimer = setTimeout(() => {
            faces.forEach(face => { face.hidden = face !== next; });
        }, reduced ? 0 : FLIP_MS);
    }

    // --- Comparison: pick a second player ---------------------------------------------------

    // `head`: extra header content (the comparison's flip icon); `classes`: extra classes and attributes
    function compareShell(title, body, { head = "", classes = "" } = {}) {
        return `<div class="hockey-card player-compare ${classes}" style="--card-primary: ${compareLeft.color}; --card-accent: ${compareLeft.accent};">
                    <div class="player-compare-head">
                        <span class="card-icon material-symbols-outlined" role="button" tabindex="0"
                              data-card-action="back" title="Back" aria-label="Back">arrow_back</span>
                        <h3>${title}</h3>
                        ${head}
                    </div>
                    ${body}
                </div>`;
    }

    // Exports the comparison's current face (cardExport.js)
    const compareExportIcon = `<span class="card-icon-button player-compare-flip-icon" role="button" tabindex="0" data-card-action="export"
                      title="Export as PNG" aria-label="Export as PNG">
                    <span class="card-icon material-symbols-outlined" aria-hidden="true">download</span>
                    <span class="card-icon-caption">Export</span>
                </span>`;

    // Flips the comparison between the stat bars and the shot maps
    function compareFlipIcon(caption) {
        return `<span class="card-icon-button player-compare-flip-icon" role="button" tabindex="0" data-card-action="flip"
                      title="Flip" aria-label="Flip to ${caption}">
                    <span class="card-icon material-symbols-outlined" aria-hidden="true">cached</span>
                    <span class="card-icon-caption">${caption}</span>
                </span>`;
    }

    function showPicker() {
        const teams = window.compareTeams || {};
        const quick = [teams.left, teams.right].filter(Boolean);
        const others = (window.teamList || []).filter(team => !quick.includes(team));
        content.innerHTML = compareShell("Compare with…", `
            <div class="player-compare-picker">
                <input type="search" class="player-compare-search" placeholder="Search NHL players by name"
                       aria-label="Search NHL players by name" autocomplete="off">
                <div class="player-compare-sources">
                    ${quick.map(team => `<button type="button" class="picker-tab" data-team="${team}">${team}</button>`).join("")}
                    <select class="picker-team-select" aria-label="Other team's roster">
                        <option value="">Other team…</option>
                        ${others.map(team => `<option value="${team}">${team}</option>`).join("")}
                    </select>
                </div>
                ${seasonPicker()}
                <ul class="player-compare-results"></ul>
            </div>`);
        content.dataset.view = "picker";
        content.querySelectorAll(".picker-season-select").forEach(select => select.addEventListener("change", () => {
            seasons[select.dataset.side] = select.value;
        }));
        const input = content.querySelector(".player-compare-search");
        let debounce;
        input.addEventListener("input", () => {
            clearTimeout(debounce);
            const query = input.value.trim();
            if (query.length < 2) return;
            debounce = setTimeout(() => searchPlayers(query), 250);
        });
        content.querySelector(".picker-team-select").addEventListener("change", event => {
            if (event.target.value) showRoster(event.target.value);
        });
        // Start with the next opponent's roster (or the team's own in the off-season)
        showRoster(teams.right || teams.left || others[0]);
        input.focus();
    }

    // Each side's season, and a button to compare the player with another of their own seasons
    function seasonPicker() {
        if (seasonOptions.length < 2) return "";
        const select = side => `<select class="picker-season-select" data-side="${side}"
                    aria-label="${side === "left" ? "This player's season" : "Other player's season"}">
                ${seasonOptions.map(s => `<option value="${escapeHtml(s.id)}"${s.id === seasons[side] ? " selected" : ""}>${escapeHtml(s.label)}</option>`).join("")}
            </select>`;
        return `<div class="player-compare-seasons">
                    <span>Season</span>${select("left")}<span>vs</span>${select("right")}
                    <button type="button" class="picker-tab" data-card-action="self">Own seasons</button>
                </div>`;
    }

    // The open card's player against another season of their own (the other side's season, or the
    // one before when both sides are on the same)
    function compareOwnSeasons() {
        if (seasons.left === seasons.right) {
            const index = seasonOptions.findIndex(s => s.id === seasons.left);
            seasons.right = seasonOptions[(index + 1) % seasonOptions.length].id;
        }
        showComparison(compareLeft.id);
    }

    function setActiveSource(team) {
        content.querySelectorAll(".picker-tab").forEach(tab => tab.classList.toggle("active", tab.dataset.team === team));
        const select = content.querySelector(".picker-team-select");
        if (select) select.value = [...select.options].some(o => o.value === team) ? team : "";
    }

    async function showRoster(team) {
        if (!team) return;
        setActiveSource(team);
        const token = ++searchToken;
        renderResults(null);
        try {
            const players = await getJson(`/team/${team}/roster.json`);
            if (token === searchToken) renderResults(players);
        } catch (e) {
            if (token === searchToken) renderResults([], "Roster unavailable right now.");
        }
    }

    async function searchPlayers(query) {
        setActiveSource(null);
        const token = ++searchToken;
        renderResults(null);
        try {
            const results = await getJson(PLAYER_SEARCH_URL + encodeURIComponent(query));
            if (token !== searchToken) return;
            renderResults(results.map(p => ({
                id: p.playerId,
                name: p.name,
                number: p.sweaterNumber,
                position: p.positionCode,
                team: p.teamAbbrev || p.lastTeamAbbrev,
                headshot: `https://assets.nhle.com/mugs/nhl/latest/${p.playerId}.png`,
            })), "No players found.");
        } catch (e) {
            if (token === searchToken) renderResults([], "Search unavailable right now.");
        }
    }

    // {playerId: points (skaters) or games played (goalies)}; lists stay unsorted without it
    function loadRanking() {
        return getJson("/players/ranking.json").catch(() => ({}));
    }

    // null = loading. Players of the same kind (skaters or goalies) first, then the other kind, which
    // compares shot maps only. Best first: most points, or for goalies most games (stable on ties).
    async function renderResults(players, emptyText = "No players.") {
        const list = content.querySelector(".player-compare-results");
        if (!list) return;
        if (players === null) {
            list.innerHTML = '<li class="player-compare-note"><div class="spinner"></div></li>';
            return;
        }
        const token = searchToken;
        const ranking = await loadRanking();
        if (token !== searchToken) return;
        const rank = p => ranking[p.id] ?? -1;
        const candidates = players.filter(p => String(p.id) !== String(compareLeft.id)).sort((a, b) => rank(b) - rank(a));
        const sameKind = p => (p.position === "G") === compareLeft.goalie;
        const same = candidates.filter(sameKind);
        const other = candidates.filter(p => !sameKind(p));
        const option = p => `
            <li><button type="button" class="player-compare-option" data-pick="${escapeHtml(p.id)}">
                <img src="${escapeHtml(p.headshot)}" alt="" loading="lazy" onerror="this.style.visibility='hidden'">
                <span class="option-name">${escapeHtml(p.name)}</span>
                <span class="option-meta">${p.number ? "#" + escapeHtml(p.number) + " " : ""}${escapeHtml(p.position)} · ${escapeHtml(p.team || "")}</span>
            </button></li>`;
        list.innerHTML = candidates.length
            ? same.map(option).join("") + (other.length
                ? `<li class="player-compare-group">${compareLeft.goalie ? "Skaters" : "Goalies"} · shot maps only</li>${other.map(option).join("")}`
                : "")
            : `<li class="player-compare-note">${emptyText}</li>`;
    }

    // --- Comparison: both players side by side -----------------------------------------------

    // `showSeason`: the sides are from different seasons
    function playerSide(player, changeable = false, showSeason = false) {
        return `<div class="player-compare-side" style="--team-color: ${player.color};">
                    <img class="player-compare-headshot" src="${escapeHtml(player.headshot)}" alt="${escapeHtml(player.name)}"
                         data-player-id="${escapeHtml(player.id)}" title="Open player card">
                    <span class="option-name">${escapeHtml(player.name)}</span>
                    <span class="option-meta">#${escapeHtml(player.number)} ${escapeHtml(player.position)}</span>
                    <span class="option-meta">
                        ${player.flag_url ? `<img class="player-compare-flag" src="${escapeHtml(player.flag_url)}" alt="" title="${escapeHtml(player.country)}">` : ""}
                        ${escapeHtml(player.team)}
                    </span>
                    ${showSeason ? `<span class="option-meta player-compare-season">${escapeHtml(player.season)}</span>` : ""}
                    ${changeable ? `<span class="player-compare-change material-symbols-outlined" role="button" tabindex="0"
                          data-card-action="change" title="Change player" aria-label="Change player">compare_arrows</span>` : ""}
                </div>`;
    }

    async function showComparison(rightId) {
        content.innerHTML = spinner;
        content.dataset.view = "comparison";
        try {
            const left = await getJson(`/player/${compareLeft.id}/compare.json?season=${seasons.left}`);
            const right = await getJson(`/player/${rightId}/compare.json?season=${seasons.right}&against=${left.color.slice(1)}`);
            if (left.is_goalie !== right.is_goalie) return showCrossComparison(left, right, rightId);
            const keys = left.is_goalie ? COMPARE_KEYS.goalie : COMPARE_KEYS.skater;
            // A flip card: stat bars in front, both players' shot maps behind (added once they load)
            const title = compareTitle(left, right);
            content.innerHTML = `<div class="hockey-card-flip player-compare-flip"><div class="hockey-card-flipper">
                ${compareShell(title, `
                    <div class="player-compare-players">${compareSides(left, right)}</div>
                    <div class="compare-mount player-compare-mount"></div>
                    <p class="hockey-card-source">Tracking: NHL EDGE · xG: MoneyPuck.com</p>`,
                    { head: compareExportIcon + compareFlipIcon("Shot map").replace('role="button"', 'role="button" hidden') })}
                </div></div>`;
            renderComparison(content.querySelector(".player-compare-mount"), {
                left: left.team,
                right: right.team,
                leftColor: left.color,
                rightColor: right.color,
                rows: keys.map(key => ({ key, left: left.values[key], right: right.values[key] })),
            });
            showShotMaps(compareLeft.id, rightId, left.color, right.color, title);
        } catch (e) {
            content.innerHTML = compareShell("Compare", '<p class="hockey-card-empty">Comparison unavailable right now.</p>');
        }
    }

    // "2025-26 regular season", or with two seasons only "Regular season" (each side shows its own)
    function compareTitle(left, right) {
        return left.season === right.season ? `${escapeHtml(left.season)} regular season` : "Regular season";
    }

    function compareSides(left, right) {
        const twoSeasons = left.season !== right.season;
        return playerSide(left, false, twoSeasons) + playerSide(right, true, twoSeasons);
    }

    // Both players' shot maps (HTML) in the comparison's seasons, or null without data
    async function fetchShotMaps(leftId, rightId) {
        const query = `seasons=${seasons.left},${seasons.right}&v=${encodeURIComponent(window.playerCardVersion || "")}`;
        const res = await fetch(`/player/${leftId}/shot-map/${rightId}?${query}`);
        return res.ok ? res.text() : null;
    }

    function colorShotMapSides(root, leftColor, rightColor) {
        root.querySelector(".shot-map-side.left")?.style.setProperty("--side-color", leftColor);
        root.querySelector(".shot-map-side.right")?.style.setProperty("--side-color", rightColor);
        initShotMaps(root);
    }

    // A skater next to a goalie: their stats don't compare, so only the shot maps, with no flip
    async function showCrossComparison(left, right, rightId) {
        content.innerHTML = `<div class="hockey-card-flip player-compare-flip"><div class="hockey-card-flipper">
            ${compareShell(compareTitle(left, right), `
                <div class="player-compare-players">${compareSides(left, right)}</div>
                <div class="player-compare-shotmap">${spinner}</div>
                <p class="hockey-card-source">Shot data: MoneyPuck.com</p>`,
                { head: compareExportIcon, classes: "player-compare-maps" })}
            </div></div>`;
        const view = content.innerHTML;
        let html = null;
        try {
            html = await fetchShotMaps(compareLeft.id, rightId);
        } catch (e) {
            // shown as unavailable below
        }
        const mount = content.querySelector(".player-compare-shotmap");
        if (!mount || content.innerHTML !== view) return; // another view opened meanwhile
        if (!html) {
            mount.innerHTML = '<p class="hockey-card-empty">No shot maps for these players yet.</p>';
            return;
        }
        mount.innerHTML = html;
        colorShotMapSides(mount, left.color, right.color);
    }

    // Both players' shot maps on one color scale, as the comparison's back face; no back (and no
    // flip icon) when neither has data
    async function showShotMaps(leftId, rightId, leftColor, rightColor, title) {
        const view = content.innerHTML;
        try {
            const html = await fetchShotMaps(leftId, rightId);
            if (!html) return;
            const flipper = content.querySelector(".player-compare-flip .hockey-card-flipper");
            if (!flipper || content.innerHTML !== view) return; // another view opened meanwhile
            flipper.insertAdjacentHTML("beforeend", compareShell(title,
                `<div class="player-compare-shotmap">${html}</div>
                 <p class="hockey-card-source">Shot data: MoneyPuck.com</p>`,
                { head: compareExportIcon + compareFlipIcon("Stats"), classes: "player-compare-maps" }));
            const maps = flipper.lastElementChild;
            maps.hidden = true;
            colorShotMapSides(maps, leftColor, rightColor);
            flipper.querySelector(".player-compare-flip-icon[hidden]")?.removeAttribute("hidden");
        } catch (e) {
            // the comparison stays without the maps
        }
    }

    function openCompare(card) {
        compareLeft = { id: card.dataset.player, goalie: card.dataset.goalie === "true", color: card.dataset.color, accent: card.dataset.accent };
        const current = seasonOptions[0]?.id || "";
        seasons = { left: current, right: current };
        showPicker();
    }

    function handleAction(target) {
        const action = target.dataset.cardAction;
        if (action === "flip") flip(target.closest(".hockey-card-flip"));
        else if (action === "shotmap") setShotMap(target);
        else if (action === "export") openCardExport(target);
        else if (action === "compare") openCompare(target.closest(".hockey-card-flip"));
        else if (action === "change") showPicker();
        else if (action === "self") compareOwnSeasons();
        else if (action === "back") {
            // Comparison -> picker -> card
            if (content.dataset.view === "comparison") showPicker();
            else showCard(cardHtml);
        }
    }

    content.addEventListener("click", event => {
        const action = event.target.closest("[data-card-action]");
        if (action) return handleAction(action);
        // Any other click on the card flips it, unless it ends a text selection or opens a stat definition
        const flipper = event.target.closest(".hockey-card-flipper");
        if (flipper && !String(window.getSelection()) && !event.target.closest("[data-stat-info]") && !statInfoOpen()) return flip(flipper.closest(".hockey-card-flip"));
        const tab = event.target.closest(".picker-tab");
        if (tab) return showRoster(tab.dataset.team);
        const option = event.target.closest("[data-pick]");
        if (option) showComparison(option.dataset.pick);
    });
    content.addEventListener("keydown", event => {
        const action = event.target.closest("[data-card-action]");
        if (action && (event.key === "Enter" || event.key === " ")) {
            event.preventDefault();
            handleAction(action);
        }
    });

    document.addEventListener("click", event => {
        const target = event.target.closest("[data-player-id]");
        if (!target) return;
        const playerId = target.dataset.playerId;
        if (/^\d+$/.test(playerId || "")) openCard(playerId);
    });

    closeBtn.addEventListener("click", () => {
        modal.style.display = "none";
    });
    window.addEventListener("click", event => {
        if (event.target === modal) {
            modal.style.display = "none";
        }
    });
});
