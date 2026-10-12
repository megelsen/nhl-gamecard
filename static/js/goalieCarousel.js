let homeGoalieIndex = 0;
let oppGoalieIndex = 0;

const { goalies, goaliesOpponent } = window;

// Rows for the shared comparison component (static/js/comparison.js)
const GOALIE_ROWS = [
    ["GP", "games_played"], ["W", "wins"], ["GAA", "goalsAgainstAverage"],
    ["SV%", "savePercentage"], ["HDSV%", "hd_save_pct"], ["SO", "shutouts"],
];

function goalieComparison(left, right) {
    const teams = window.compareTeams || {};
    return {
        left: teams.left,
        right: teams.right,
        rows: GOALIE_ROWS.map(([key, field]) => ({ key, left: left[field] ?? null, right: right[field] ?? null })),
    };
}

function renderGoalies() {
    const home = goalies[homeGoalieIndex];
    const opp = goaliesOpponent[oppGoalieIndex];

    // Home goalie
    if (home) {
        document.getElementById("goalie-img").src = home.heroImage_url;
        document.getElementById("goalie-img").dataset.playerId = home.playerID;
        document.getElementById("goalie-name").innerHTML = `<b>${home.name}</b>`;
        document.getElementById("goalie-number").textContent = `#${home.sweaterNumber}`;
    }

    // Opponent goalie
    if (opp) {
        document.getElementById("opp-goalie-img").src = opp.heroImage_url;
        document.getElementById("opp-goalie-img").dataset.playerId = opp.playerID;
        document.getElementById("opp-goalie-name").innerHTML = `<b>${opp.name}</b>`;
        document.getElementById("opp-goalie-number").textContent = `#${opp.sweaterNumber}`;
    }

    // Comparison table
    const compare = document.getElementById("goalie-compare");
    renderComparison(compare, goalieComparison(home || {}, opp || {}));
}

// Home goalie arrows
function nextHomeGoalie() {
    if (!goalies.length) return;
    homeGoalieIndex = (homeGoalieIndex + 1) % goalies.length;
    renderGoalies();
}
function prevHomeGoalie() {
    if (!goalies.length) return;
    homeGoalieIndex = (homeGoalieIndex - 1 + goalies.length) % goalies.length;
    renderGoalies();
}

// Opponent goalie arrows
function nextOppGoalie() {
    if (!goaliesOpponent.length) return;
    oppGoalieIndex = (oppGoalieIndex + 1) % goaliesOpponent.length;
    renderGoalies();
}
function prevOppGoalie() {
    if (!goaliesOpponent.length) return;
    oppGoalieIndex = (oppGoalieIndex - 1 + goaliesOpponent.length) % goaliesOpponent.length;
    renderGoalies();
}

document.addEventListener("DOMContentLoaded", renderGoalies);
