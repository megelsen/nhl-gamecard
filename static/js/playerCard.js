// Player card modal: click any headshot with data-player-id (top scorers, goalies, Top 5, roster).
// One delegated listener, so headshots rendered later (modals, goalie carousel) work too.
// Icons on the card: flip to the league percentiles and the shot map, or compare with another player (picked by
// name search or from a team roster), shown with the shared comparison bars (comparison.js).
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

document.addEventListener("DOMContentLoaded", function () {
    const modal = document.getElementById("playerCardPopUp");
    const content = document.getElementById("playerCardContent");
    const closeBtn = document.getElementById("closeBtnPlayerCard");
    if (!modal || !content) return;

    const cardCache = new Map();
    const jsonCache = new Map();
    let cardHtml = "";     // the open card, to return to from the comparison
    let compareLeft = null; // {id, goalie, color, accent} of the open card's player
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

    // Shot map: Shots / Goals buttons swap each zone's color and number (data-* from the template)
    function setShotMapMode(button) {
        const map = button.closest(".shot-map");
        const mode = button.dataset.mode;
        map.querySelectorAll(".shot-map-mode").forEach(b => b.classList.toggle("active", b === button));
        map.querySelectorAll(`[data-fill-${mode}]`).forEach(el => el.setAttribute("fill", el.getAttribute(`data-fill-${mode}`)));
        map.querySelectorAll(`[data-ink-${mode}]`).forEach(el => el.setAttribute("fill", el.getAttribute(`data-ink-${mode}`)));
        map.querySelectorAll(`[data-text-${mode}]`).forEach(el => { el.textContent = el.getAttribute(`data-text-${mode}`); });
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
        const kind = compareLeft.goalie ? "goalies" : "skaters";
        content.innerHTML = compareShell("Compare with…", `
            <div class="player-compare-picker">
                <input type="search" class="player-compare-search" placeholder="Search NHL ${kind} by name"
                       aria-label="Search NHL ${kind} by name" autocomplete="off">
                <div class="player-compare-sources">
                    ${quick.map(team => `<button type="button" class="picker-tab" data-team="${team}">${team}</button>`).join("")}
                    <select class="picker-team-select" aria-label="Other team's roster">
                        <option value="">Other team…</option>
                        ${others.map(team => `<option value="${team}">${team}</option>`).join("")}
                    </select>
                </div>
                <ul class="player-compare-results"></ul>
            </div>`);
        content.dataset.view = "picker";
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

    // null = loading; only players of the same kind (skaters or goalies) can be compared.
    // Best first: most points, or for goalies most games (the sort keeps the order on ties).
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
        const matching = players
            .filter(p => String(p.id) !== String(compareLeft.id) && (p.position === "G") === compareLeft.goalie)
            .sort((a, b) => rank(b) - rank(a));
        list.innerHTML = matching.length ? matching.map(p => `
            <li><button type="button" class="player-compare-option" data-pick="${escapeHtml(p.id)}">
                <img src="${escapeHtml(p.headshot)}" alt="" loading="lazy" onerror="this.style.visibility='hidden'">
                <span class="option-name">${escapeHtml(p.name)}</span>
                <span class="option-meta">${p.number ? "#" + escapeHtml(p.number) + " " : ""}${escapeHtml(p.position)} · ${escapeHtml(p.team || "")}</span>
            </button></li>`).join("")
            : `<li class="player-compare-note">${emptyText}</li>`;
    }

    // --- Comparison: both players side by side -----------------------------------------------

    function playerSide(player, changeable = false) {
        return `<div class="player-compare-side" style="--team-color: ${player.color};">
                    <img class="player-compare-headshot" src="${escapeHtml(player.headshot)}" alt="${escapeHtml(player.name)}"
                         data-player-id="${escapeHtml(player.id)}" title="Open player card">
                    <span class="option-name">${escapeHtml(player.name)}</span>
                    <span class="option-meta">#${escapeHtml(player.number)} ${escapeHtml(player.position)}</span>
                    <span class="option-meta">
                        ${player.flag_url ? `<img class="player-compare-flag" src="${escapeHtml(player.flag_url)}" alt="" title="${escapeHtml(player.country)}">` : ""}
                        ${escapeHtml(player.team)}
                    </span>
                    ${changeable ? `<span class="player-compare-change material-symbols-outlined" role="button" tabindex="0"
                          data-card-action="change" title="Change player" aria-label="Change player">compare_arrows</span>` : ""}
                </div>`;
    }

    async function showComparison(rightId) {
        content.innerHTML = spinner;
        content.dataset.view = "comparison";
        try {
            const left = await getJson(`/player/${compareLeft.id}/compare.json`);
            const right = await getJson(`/player/${rightId}/compare.json?against=${left.color.slice(1)}`);
            const keys = left.is_goalie ? COMPARE_KEYS.goalie : COMPARE_KEYS.skater;
            // A flip card: stat bars in front, both players' shot maps behind (added once they load)
            const title = `${escapeHtml(left.season)} regular season`;
            content.innerHTML = `<div class="hockey-card-flip player-compare-flip"><div class="hockey-card-flipper">
                ${compareShell(title, `
                    <div class="player-compare-players">${playerSide(left)}${playerSide(right, true)}</div>
                    <div class="compare-mount player-compare-mount"></div>
                    <p class="hockey-card-source">Tracking: NHL EDGE · xG: MoneyPuck.com</p>`,
                    { head: compareFlipIcon("Shot map").replace('role="button"', 'role="button" hidden') })}
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

    // Both players' shot maps on one color scale, as the comparison's back face; no back (and no
    // flip icon) when neither has data
    async function showShotMaps(leftId, rightId, leftColor, rightColor, title) {
        const view = content.innerHTML;
        try {
            const res = await fetch(`/player/${leftId}/shot-map/${rightId}?v=${encodeURIComponent(window.playerCardVersion || "")}`);
            if (!res.ok) return;
            const html = await res.text();
            const flipper = content.querySelector(".player-compare-flip .hockey-card-flipper");
            if (!flipper || content.innerHTML !== view) return; // another view opened meanwhile
            flipper.insertAdjacentHTML("beforeend", compareShell(title,
                `<div class="player-compare-shotmap">${html}</div>
                 <p class="hockey-card-source">Shot locations: NHL EDGE</p>`,
                { head: compareFlipIcon("Stats"), classes: "player-compare-maps" }));
            const maps = flipper.lastElementChild;
            maps.hidden = true;
            maps.querySelector(".shot-map-side.left")?.style.setProperty("--side-color", leftColor);
            maps.querySelector(".shot-map-side.right")?.style.setProperty("--side-color", rightColor);
            flipper.querySelector(".player-compare-flip-icon[hidden]")?.removeAttribute("hidden");
        } catch (e) {
            // the comparison stays without the maps
        }
    }

    function openCompare(card) {
        compareLeft = { id: card.dataset.player, goalie: card.dataset.goalie === "true", color: card.dataset.color, accent: card.dataset.accent };
        showPicker();
    }

    function handleAction(target) {
        const action = target.dataset.cardAction;
        if (action === "flip") flip(target.closest(".hockey-card-flip"));
        else if (action === "shotmode") setShotMapMode(target);
        else if (action === "compare") openCompare(target.closest(".hockey-card-flip"));
        else if (action === "change") showPicker();
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
