// Slanted-split comparison bars under each stat row of .player-compare / .team-compare tables.
// Reads the two values already in the row; the bigger part of the bar is always the better side.
// Colors: window.compareColors = {ABBR: color}; tables are team (left) vs opponent (right)
// unless they set data-left-team / data-right-team (e.g. the home/away "Last meeting" table).

const COMPARE_SKIP = new Set(["GP"]);
const COMPARE_LOWER_IS_BETTER = new Set(["GAA"]);
// Rate stats: shift the split by the difference relative to a typical spread instead of a plain share
const COMPARE_RATE_SPREAD = { "S%": 0.05, "GAA": 1.5, "FO%": 0.3 };
const COMPARE_MAX_SHIFT = 40; // split stays within 10%..90%

function parseCompareValue(text) {
    // "1/2" (power play goals/opportunities) compares the goals
    const match = text.trim().match(/^-?\d*\.?\d+/);
    return match ? parseFloat(match[0]) : null;
}

function compareSplit(label, left, right) {
    const sign = COMPARE_LOWER_IS_BETTER.has(label) ? -1 : 1;
    if (label in COMPARE_RATE_SPREAD) {
        const shift = Math.max(-1, Math.min(1, sign * (left - right) / COMPARE_RATE_SPREAD[label]));
        return 50 + shift * COMPARE_MAX_SHIFT;
    }
    if (left + right === 0) return null;
    const share = sign > 0 ? left / (left + right) : right / (left + right);
    return 50 + Math.max(-COMPARE_MAX_SHIFT, Math.min(COMPARE_MAX_SHIFT, (share - 0.5) * 100));
}

function applyCompareBars(root = document) {
    const colors = window.compareColors || {};
    const teams = window.compareTeams || {};
    root.querySelectorAll(".player-compare, .team-compare").forEach(table => {
        table.querySelectorAll("tr.compare-bar-row").forEach(row => row.remove());
        const leftColor = colors[table.dataset.leftTeam || teams.left] || "#555";
        const rightColor = colors[table.dataset.rightTeam || teams.right] || "#bbb";

        table.querySelectorAll("tr").forEach(row => {
            const label = row.querySelector("th")?.textContent.trim();
            const cells = row.querySelectorAll("td");
            if (!label || cells.length !== 2 || COMPARE_SKIP.has(label)) return;
            const left = parseCompareValue(cells[0].textContent);
            const right = parseCompareValue(cells[1].textContent);
            if (left === null || right === null) return;

            const split = compareSplit(label, left, right);
            const barRow = document.createElement("tr");
            barRow.className = "compare-bar-row";
            barRow.innerHTML = `<td colspan="3"><div class="compare-bar${split === null ? " even" : ""}"
                style="--split: ${split ?? 50}%; --left-color: ${leftColor}; --right-color: ${rightColor};">
                <span class="bar-left"></span><span class="bar-right"></span></div></td>`;
            row.after(barRow);
        });
    });
}

document.addEventListener("DOMContentLoaded", () => applyCompareBars());
