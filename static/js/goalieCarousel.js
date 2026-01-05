let homeGoalieIndex = 0;
let oppGoalieIndex = 0;

const { goalies, goaliesOpponent } = window;

function goalieCompare(left, right) {
    return `
        <table class="player-compare">
            <tr>
                <td class="player left">${left.games_played}</td>
                <th>GP</th>
                <td class="player right">${right.games_played}</td>
            </tr>
            <tr>
                <td class="player left">${left.wins}</td>
                <th>W</th>
                <td class="player right">${right.wins}</td>
            </tr>
            <tr>
                <td class="player left">${left.goalsAgainstAverage}</td>
                <th>GAA</th>
                <td class="player right">${right.goalsAgainstAverage}</td>
            </tr>
            <tr>
                <td class="player left">${left.savePercentage}</td>
                <th>S%</th>
                <td class="player right">${right.savePercentage}</td>
            </tr>
            <tr>
                <td class="player left">${left.shutouts}</td>
                <th>SO</th>
                <td class="player right">${right.shutouts}</td>
            </tr>
        </table>
    `;
}

function renderGoalies() {
    const home = goalies[homeGoalieIndex];
    const opp = goaliesOpponent[oppGoalieIndex];

    // Home goalie
    document.getElementById("goalie-img").src = home.heroImage_url;
    document.getElementById("goalie-name").innerHTML = `<b>${home.name}</b>`;
    document.getElementById("goalie-number").textContent = `#${home.sweaterNumber}`;

    // Opponent goalie
    document.getElementById("opp-goalie-img").src = opp.heroImage_url;
    document.getElementById("opp-goalie-name").innerHTML = `<b>${opp.name}</b>`;
    document.getElementById("opp-goalie-number").textContent = `#${opp.sweaterNumber}`;

    // Comparison table
    document.getElementById("goalie-compare").innerHTML =
        goalieCompare(home, opp);
}

// Home goalie arrows
function nextHomeGoalie() {
    homeGoalieIndex = (homeGoalieIndex + 1) % goalies.length;
    renderGoalies();
}
function prevHomeGoalie() {
    homeGoalieIndex = (homeGoalieIndex - 1 + goalies.length) % goalies.length;
    renderGoalies();
}

// Opponent goalie arrows
function nextOppGoalie() {
    oppGoalieIndex = (oppGoalieIndex + 1) % goaliesOpponent.length;
    renderGoalies();
}
function prevOppGoalie() {
    oppGoalieIndex = (oppGoalieIndex - 1 + goaliesOpponent.length) % goaliesOpponent.length;
    renderGoalies();
}

document.addEventListener("DOMContentLoaded", renderGoalies);
