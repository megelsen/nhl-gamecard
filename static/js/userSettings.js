// Viewer settings from the footer: timezone and units, saved in this browser.
// Other scripts read window.userSettings and re-render on the "settingschange" event.
const SETTINGS_KEY = "gamecardSettings";
const SETTINGS_DEFAULTS = { timezone: "auto", units: "metric" };

const SETTINGS_TIMEZONES = [
    ["America/New_York", "Eastern (New York)"],
    ["America/Chicago", "Central (Chicago)"],
    ["America/Denver", "Mountain (Denver)"],
    ["America/Phoenix", "Arizona (Phoenix)"],
    ["America/Los_Angeles", "Pacific (Los Angeles)"],
    ["America/Anchorage", "Alaska (Anchorage)"],
    ["UTC", "UTC"],
    ["Europe/London", "UK (London)"],
    ["Europe/Zurich", "Central Europe (Zurich)"],
    ["Europe/Helsinki", "Eastern Europe (Helsinki)"],
    ["Europe/Moscow", "Moscow"],
    ["Asia/Tokyo", "Japan (Tokyo)"],
    ["Australia/Sydney", "Australia (Sydney)"],
];

function loadSettings() {
    try {
        return { ...SETTINGS_DEFAULTS, ...JSON.parse(localStorage.getItem(SETTINGS_KEY) || "{}") };
    } catch (e) {
        return { ...SETTINGS_DEFAULTS };
    }
}

window.userSettings = loadSettings();

function browserTimeZone() {
    return Intl.DateTimeFormat().resolvedOptions().timeZone;
}

// The IANA zone to show game times in
function settingsTimeZone() {
    return window.userSettings.timezone === "auto" ? browserTimeZone() : window.userSettings.timezone;
}

function updateSetting(name, value) {
    window.userSettings[name] = value;
    try {
        localStorage.setItem(SETTINGS_KEY, JSON.stringify(window.userSettings));
    } catch (e) { /* not saved, still applied for this page */ }
    document.dispatchEvent(new CustomEvent("settingschange", { detail: { name, value } }));
}

// Elements rendered with both unit systems: <span class="unit-value" data-metric="..." data-imperial="...">
function applyUnits(root = document) {
    root.querySelectorAll(".unit-value").forEach(el => {
        const text = el.dataset[window.userSettings.units];
        if (text) el.textContent = text;
    });
}

document.addEventListener("DOMContentLoaded", () => {
    const timezoneSelect = document.getElementById("setting-timezone");
    const unitsSelect = document.getElementById("setting-units");

    if (timezoneSelect) {
        const options = [["auto", `Auto (${browserTimeZone()})`], ...SETTINGS_TIMEZONES];
        // Keep a saved zone selectable even if it's not in the list
        if (!options.some(([value]) => value === window.userSettings.timezone)) {
            options.push([window.userSettings.timezone, window.userSettings.timezone]);
        }
        timezoneSelect.innerHTML = options.map(([value, label]) => `<option value="${value}">${label}</option>`).join("");
        timezoneSelect.value = window.userSettings.timezone;
        timezoneSelect.addEventListener("change", () => updateSetting("timezone", timezoneSelect.value));
    }
    if (unitsSelect) {
        unitsSelect.value = window.userSettings.units;
        unitsSelect.addEventListener("change", () => updateSetting("units", unitsSelect.value));
    }
    applyUnits();
});

document.addEventListener("settingschange", event => {
    if (event.detail.name === "units") applyUnits();
});
