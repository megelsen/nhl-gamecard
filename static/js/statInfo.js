// Definitions of the advanced stats, shown in a small info box when hovering (or tapping) a label
// with data-stat-info="<key>": comparison rows (comparison.js) and the player card back.
// One floating box on <body>, so the cards' overflow never clips it.
const STAT_INFO = {
    PCT: "Percentile (pctl) among NHL players of the same position (forwards, defensemen or goalies) this season: " +
         "90th = better than 90% of them. NHL EDGE ranks its own stats; xG and GSAx are ranked among players with " +
         "at least 25% of the group's most games. The bar splits at the percentile; the right-hand value is the " +
         "NHL average for the position.",
    RANK: "Rank among all NHL skaters this season (tied players share a rank). The bar shows the percentile among " +
          "players of the same position with at least 25% of the group's most games; the right-hand value is " +
          "their average.",
    XGF60: "Expected goals for per 60 minutes at 5-on-5 while the player is on the ice. Every shot attempt is weighted " +
           "by its chance to score (distance, angle, shot type, rebound, rush), so this measures the quality of chances " +
           "the team creates with the player out there. Higher is better. Source: MoneyPuck.com.",
    XGA60: "Expected goals against per 60 minutes at 5-on-5 while the player is on the ice: the quality of chances " +
           "the opponent gets. Lower is better. Source: MoneyPuck.com.",
    SHOT: "Hardest shot this season, measured by NHL EDGE puck tracking.",
    SPEED: "Top skating speed reached in a game this season (NHL EDGE player tracking).",
    DIST: "Total distance skated this season (NHL EDGE player tracking).",
    "SH%": "Shooting percentage: goals divided by shots on goal.",
    "HDSV%": "Save percentage on high-danger shots, the ones from right in front of the net (slot and crease), " +
             "per NHL EDGE shot locations.",
    GD60: "Goal differential per 60 minutes: goals the team scores minus goals it allows while the goalie is in net.",
    Q900: "Share of games in which the goalie had a save percentage of .900 or better.",
    GSAX: "Goals saved above expected: expected goals against (from the quality of shots faced) minus goals actually " +
          "allowed, all situations. Positive = the goalie stopped more than an average goalie would have. Source: MoneyPuck.com.",
};

// True while a definition is open, so a tap that only closes it doesn't also act (player card flip)
function statInfoOpen() {
    const box = document.querySelector(".stat-info-box");
    return Boolean(box && !box.hidden);
}

document.addEventListener("DOMContentLoaded", () => {
    const box = document.createElement("div");
    box.className = "stat-info-box";
    box.setAttribute("role", "tooltip");
    box.hidden = true;
    document.body.appendChild(box);
    let current = null; // label the box belongs to
    let pinned = false; // opened by click/tap: stays until the next click

    function show(label) {
        const text = STAT_INFO[label.dataset.statInfo];
        if (!text) return;
        current = label;
        box.textContent = text;
        box.hidden = false;
        // Below the label, centered on it, kept inside the viewport (above it when there's no room below)
        const rect = label.getBoundingClientRect();
        const width = box.offsetWidth;
        const left = Math.max(8, Math.min(window.innerWidth - width - 8, rect.left + rect.width / 2 - width / 2));
        const below = rect.bottom + 8;
        const top = below + box.offsetHeight > window.innerHeight - 8 ? rect.top - box.offsetHeight - 8 : below;
        box.style.left = `${left}px`;
        box.style.top = `${Math.max(8, top)}px`;
    }

    function hide() {
        box.hidden = true;
        current = null;
        pinned = false;
    }

    document.addEventListener("pointerover", event => {
        if (event.pointerType !== "mouse" || pinned) return;
        const label = event.target.closest("[data-stat-info]");
        if (label && label !== current) show(label);
    });
    document.addEventListener("pointerout", event => {
        if (event.pointerType !== "mouse" || pinned || !current) return;
        if (!current.contains(event.relatedTarget)) hide();
    });
    // Tap (touch) or click: toggle and keep it open; any click elsewhere closes it
    document.addEventListener("click", event => {
        const label = event.target.closest("[data-stat-info]");
        if (label && STAT_INFO[label.dataset.statInfo]) {
            if (pinned && label === current) return hide();
            show(label);
            pinned = true;
        } else if (!box.hidden) {
            hide();
        }
    });
    document.addEventListener("focusin", event => {
        const label = event.target.closest("[data-stat-info]");
        if (label) show(label);
    });
    document.addEventListener("focusout", () => { if (!pinned) hide(); });
    document.addEventListener("keydown", event => { if (event.key === "Escape" && !box.hidden) hide(); });
    // The box is fixed to the viewport, so it would drift away from its label
    window.addEventListener("scroll", () => { if (!box.hidden) hide(); }, true);
    window.addEventListener("resize", () => { if (!box.hidden) hide(); });
});
