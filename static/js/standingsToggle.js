// Standings card: East/West tabs + Conference/Wild Card view toggle.
// Uses its own classes (.standings-tab) so topscorers_modal.js, which binds every .tab, leaves it alone.
document.addEventListener("DOMContentLoaded", function () {
    const card = document.querySelector(".standings-card");
    if (!card) return;

    const tabs = card.querySelectorAll(".standings-tab");
    const viewButtons = card.querySelectorAll(".standings-view");
    const tables = card.querySelectorAll(".standings-table-wrapper");

    let conference = card.querySelector(".standings-tab.active")?.dataset.conference || "Eastern";
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
});
