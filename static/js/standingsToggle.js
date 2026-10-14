// Standings card: West/East tabs.
// Uses its own classes (.standings-tab) so topscorers_modal.js, which binds every .tab, leaves it alone.
function setupConferenceTabs(card) {
    const tabs = card.querySelectorAll(".standings-tab");
    const tables = card.querySelectorAll(".standings-table-wrapper");
    if (!tabs.length) return;

    let conference = card.querySelector(".standings-tab.active")?.dataset.conference || tabs[0].dataset.conference;

    function render() {
        tabs.forEach(tab => tab.classList.toggle("active", tab.dataset.conference === conference));
        tables.forEach(table => {
            table.hidden = table.dataset.conference !== conference;
        });
    }

    tabs.forEach(tab => tab.addEventListener("click", () => {
        conference = tab.dataset.conference;
        render();
    }));
    render();
}

document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll(".standings-card").forEach(setupConferenceTabs);
});
