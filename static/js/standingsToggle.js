// Standings and playoff cards: East/West tabs (+ Conference/Wild Card view toggle on standings).
// Uses its own classes (.standings-tab) so topscorers_modal.js, which binds every .tab, leaves it alone.
function setupConferenceTabs(card) {
    const tabs = card.querySelectorAll(".standings-tab");
    const viewButtons = card.querySelectorAll(".standings-view");
    const tables = card.querySelectorAll(".standings-table-wrapper");
    if (!tabs.length) return;

    let conference = card.querySelector(".standings-tab.active")?.dataset.conference || tabs[0].dataset.conference;
    let view = card.querySelector(".standings-view.active")?.dataset.view || "conference";

    function render() {
        tabs.forEach(tab => tab.classList.toggle("active", tab.dataset.conference === conference));
        viewButtons.forEach(btn => btn.classList.toggle("active", btn.dataset.view === view));
        tables.forEach(table => {
            table.hidden = !(table.dataset.conference === conference && table.dataset.view === view);
        });
    }

    tabs.forEach(tab => tab.addEventListener("click", () => {
        conference = tab.dataset.conference;
        render();
    }));
    viewButtons.forEach(btn => btn.addEventListener("click", () => {
        view = btn.dataset.view;
        render();
    }));
    render();
}

document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll(".standings-card, .playoff-card").forEach(setupConferenceTabs);
});
