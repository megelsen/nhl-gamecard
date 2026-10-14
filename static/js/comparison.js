// Shared stat comparison: one component for Top scorers, Goalies and Last meeting.
// Data: {left: "NYR", right: "TBL", rows: [{key, left, right, leftText?, rightText?}]} with raw numbers.
// Labels, number formats and bar rules for every row key live here, in COMPARE_SPECS.
// Colors: window.compareColors = {ABBR: color}. Speeds follow the footer's units setting (userSettings.js).

const COMPARE_SPECS = {
    GP: { label: "GP" },
    G: { label: "G" },
    A: { label: "A" },
    P: { label: "P" },
    W: { label: "W" },
    SO: { label: "SO" },
    TOI: { label: "TOI/GP", format: "time" },
    SHOT: { label: "Shot", unit: "speed", format: "fixed1", spread: 10 },
    SPEED: { label: "Speed", unit: "speed", format: "fixed1" },
    GAA: { label: "GAA", format: "fixed2", spread: 1.5, lowerIsBetter: true },
    "SV%": { label: "SV%", format: "svpct", spread: 0.05 },
    "HDSV%": { label: "HD SV%", format: "svpct", spread: 0.08 },
    "FO%": { label: "FO%", format: "pct", spread: 0.3 },
    Score: { label: "Score" },
    SOG: { label: "SOG" },
    PP: { label: "PP" },
    Hits: { label: "Hits" },
};
const COMPARE_MAX_SHIFT = 40; // the split stays within 10%..90%
const KMH_TO_MPH = 0.621371;

// Values come in km/h; convert when the viewer picked imperial units
function compareUnit(spec) {
    if (spec.unit !== "speed") return { label: spec.label, factor: 1 };
    return (window.userSettings || {}).units === "imperial"
        ? { label: `${spec.label} mph`, factor: KMH_TO_MPH }
        : { label: `${spec.label} km/h`, factor: 1 };
}

function scaleValue(value, factor) {
    return value === null || value === undefined ? value : value * factor;
}

function formatCompareValue(value, format) {
    if (value === null || value === undefined || Number.isNaN(value)) return "-";
    switch (format) {
        case "time": {
            const seconds = Math.round(value);
            return `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, "0")}`;
        }
        case "fixed1": return value.toFixed(1);
        case "fixed2": return value.toFixed(2);
        case "svpct": return value.toFixed(3).replace(/^0/, "");
        case "pct": return `${Math.round(value * 100)}%`;
        default: return String(value);
    }
}

// Percentage of the bar for the left side; null = no meaningful split (grey bar)
function compareSplit(spec, left, right) {
    if (left === null || left === undefined || right === null || right === undefined) return null;
    const sign = spec.lowerIsBetter ? -1 : 1;
    if (spec.spread) {
        // Rate stats: shift by the difference relative to a typical spread instead of a plain share
        const shift = Math.max(-1, Math.min(1, sign * (left - right) / spec.spread));
        return 50 + shift * COMPARE_MAX_SHIFT;
    }
    if (left + right === 0) return null;
    const share = sign > 0 ? left / (left + right) : right / (left + right);
    return 50 + Math.max(-COMPARE_MAX_SHIFT, Math.min(COMPARE_MAX_SHIFT, (share - 0.5) * 100));
}

function compareLogo(abbrev) {
    return `https://assets.nhle.com/logos/nhl/svg/${abbrev}_light.svg`;
}

function renderComparison(container, data) {
    if (!container || !data) return;
    container.compareData = data; // re-rendered when the units change
    const colors = window.compareColors || {};
    const leftColor = colors[data.left] || "#555";
    const rightColor = colors[data.right] || "#bbb";

    const teamTag = (abbrev, color, side) => abbrev
        ? `<span class="compare-team ${side}" style="--team-color: ${color};"><img src="${compareLogo(abbrev)}" alt="">${abbrev}</span>`
        : `<span class="compare-team ${side}"></span>`;

    const rows = data.rows.map(row => {
        const spec = COMPARE_SPECS[row.key] || { label: row.key };
        const unit = compareUnit(spec);
        const left = scaleValue(row.left, unit.factor);
        const right = scaleValue(row.right, unit.factor);
        const leftText = row.leftText ?? formatCompareValue(left, spec.format);
        const rightText = row.rightText ?? formatCompareValue(right, spec.format);
        let bar = "";
        if (spec.bar !== false) {
            const split = compareSplit({ ...spec, spread: spec.spread && spec.spread * unit.factor }, left, right);
            bar = `<div class="compare-bar${split === null ? " even" : ""}" style="--split: ${split ?? 50}%;">
                       <span class="bar-left"></span><span class="bar-right"></span></div>`;
        }
        return `<div class="compare-row">
                    <span class="compare-value left">${leftText}</span>
                    <span class="compare-label">${unit.label}</span>
                    <span class="compare-value right">${rightText}</span>
                    ${bar}
                </div>`;
    }).join("");

    container.innerHTML = `<div class="compare" style="--left-color: ${leftColor}; --right-color: ${rightColor};">
            <div class="compare-teams">${teamTag(data.left, leftColor, "left")}${teamTag(data.right, rightColor, "right")}</div>
            ${rows}
        </div>`;
}

document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll(".compare-mount[data-compare]").forEach(mount => {
        try {
            renderComparison(mount, JSON.parse(mount.dataset.compare));
        } catch (e) {
            mount.textContent = "Comparison unavailable";
        }
    });
});

document.addEventListener("settingschange", event => {
    if (event.detail.name !== "units") return;
    document.querySelectorAll(".compare-mount, #goalie-compare").forEach(container => {
        if (container.compareData) renderComparison(container, container.compareData);
    });
});
