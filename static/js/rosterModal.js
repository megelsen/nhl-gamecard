// Roster modal: Goalies / Defense / Forwards tabs.
// Uses .roster-tab (not .tab) so topscorers_modal.js, which binds every .tab, leaves it alone.
document.addEventListener("DOMContentLoaded", function () {
    const modal = document.getElementById("rosterPopUp");
    const openBtn = document.getElementById("rosterBtn");
    const closeBtn = document.getElementById("closeBtnRoster");
    if (!modal || !openBtn) return;

    const tabs = modal.querySelectorAll(".roster-tab");
    const tables = modal.querySelectorAll(".roster-table-wrapper");

    tabs.forEach(tab => tab.addEventListener("click", () => {
        tabs.forEach(t => t.classList.toggle("active", t === tab));
        tables.forEach(table => {
            table.hidden = table.dataset.group !== tab.dataset.group;
        });
    }));

    openBtn.addEventListener("click", () => {
        modal.style.display = "flex";
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
