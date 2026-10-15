// Player card modal: click any headshot with data-player-id (top scorers, goalies, Top 5, roster).
// One delegated listener, so headshots rendered later (modals, goalie carousel) work too.
// Icons on the card: flip to the league percentiles, or compare with another player (picked by
// name search or from a team roster), shown with the shared comparison bars (comparison.js).
const PLAYER_SEARCH_URL = "https://search.d3.nhle.com/api/v1/search/player?culture=en-us&limit=20&active=true&q=";
const COMPARE_KEYS = {
    skater: ["GP", "G", "A", "P", "PM", "TOI", "XGF60", "XGA60", "SHOT", "SPEED"],
    goalie: ["GP", "W", "GAA", "SV%", "SO", "HDSV%", "GSAX"],
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
            const res = await fetch(`/player/${playerId}/card`);
            if (!res.ok) throw new Error(res.status);
            const html = await res.text();
            cardCache.set(playerId, html);
            showCard(html);
        } catch (e) {
            content.innerHTML = '<p class="hockey-card-empty">Player info is unavailable right now.</p>';
        }
    }

    // Both faces are shown while the card turns; afterwards the hidden one gets `hidden` again
    function flip(card) {
        const front = card.querySelector(".hockey-card-front");
        const back = card.querySelector(".hockey-card-back");
        if (!front || !back) return;
        const toBack = !card.classList.contains("flipped");
        front.hidden = back.hidden = false;
        void card.offsetWidth; // start the turn from the current position
        card.classList.toggle("flipped", toBack);
        const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
        clearTimeout(card.flipTimer);
        card.flipTimer = setTimeout(() => {
            (toBack ? front : back).hidden = true;
        }, reduced ? 0 : FLIP_MS);
    }

    // --- Comparison: pick a second player ---------------------------------------------------

    function compareShell(title, body) {
        return `<div class="hockey-card player-compare" style="--card-primary: ${compareLeft.color}; --card-accent: ${compareLeft.accent};">
                    <div class="player-compare-head">
                        <span class="card-icon material-symbols-outlined" role="button" tabindex="0"
                              data-card-action="back" title="Back" aria-label="Back">arrow_back</span>
                        <h3>${title}</h3>
                    </div>
                    ${body}
                </div>`;
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

    // null = loading; only players of the same kind (skaters or goalies) can be compared
    function renderResults(players, emptyText = "No players.") {
        const list = content.querySelector(".player-compare-results");
        if (!list) return;
        if (players === null) {
            list.innerHTML = '<li class="player-compare-note"><div class="spinner"></div></li>';
            return;
        }
        const matching = players.filter(p => String(p.id) !== String(compareLeft.id) && (p.position === "G") === compareLeft.goalie);
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
            content.innerHTML = compareShell(`${escapeHtml(left.season)} regular season`, `
                <div class="player-compare-players">${playerSide(left)}${playerSide(right, true)}</div>
                <div class="compare-mount player-compare-mount"></div>
                <p class="hockey-card-source">Tracking: NHL EDGE · xG: MoneyPuck.com</p>`);
            renderComparison(content.querySelector(".player-compare-mount"), {
                left: left.team,
                right: right.team,
                leftColor: left.color,
                rightColor: right.color,
                rows: keys.map(key => ({ key, left: left.values[key], right: right.values[key] })),
            });
        } catch (e) {
            content.innerHTML = compareShell("Compare", '<p class="hockey-card-empty">Comparison unavailable right now.</p>');
        }
    }

    function openCompare(card) {
        compareLeft = { id: card.dataset.player, goalie: card.dataset.goalie === "true", color: card.dataset.color, accent: card.dataset.accent };
        showPicker();
    }

    function handleAction(target) {
        const action = target.dataset.cardAction;
        if (action === "flip") flip(target.closest(".hockey-card-flip"));
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
