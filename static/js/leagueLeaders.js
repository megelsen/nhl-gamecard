// League leaders card (Goals / Assists / Points tabs) and its "More stats" modal (every category).
// Uses .standings-tab / .leaders-chip (not .tab) so topscorers_modal.js, which binds every .tab, leaves them alone.
function setupLeaderTabs(root, tabSelector) {
    const tabs = root.querySelectorAll(tabSelector);
    const lists = root.querySelectorAll(".leaders-list-wrapper");
    tabs.forEach(tab => tab.addEventListener("click", () => {
        tabs.forEach(t => t.classList.toggle("active", t === tab));
        lists.forEach(list => {
            list.hidden = list.dataset.category !== tab.dataset.category;
        });
    }));
}

document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll(".league-leaders-card").forEach(card => setupLeaderTabs(card, ".leaders-tab"));

    const modal = document.getElementById("leadersPopUp");
    const openBtn = document.getElementById("moreLeadersBtn");
    const closeBtn = document.getElementById("closeBtnLeaders");
    if (!modal || !openBtn) return;

    setupLeaderTabs(modal, ".leaders-chip");
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
