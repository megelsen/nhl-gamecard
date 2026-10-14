// Player card modal: click any headshot with data-player-id (top scorers, goalies, Top 5, roster).
// One delegated listener, so headshots rendered later (modals, goalie carousel) work too.
document.addEventListener("DOMContentLoaded", function () {
    const modal = document.getElementById("playerCardPopUp");
    const content = document.getElementById("playerCardContent");
    const closeBtn = document.getElementById("closeBtnPlayerCard");
    if (!modal || !content) return;

    const cache = new Map();

    async function openCard(playerId) {
        modal.style.display = "flex";
        if (cache.has(playerId)) {
            content.innerHTML = cache.get(playerId);
            applyUnits(content);
            return;
        }
        content.innerHTML = '<div class="player-card-loading"><div class="spinner"></div></div>';
        try {
            const res = await fetch(`/player/${playerId}/card`);
            if (!res.ok) throw new Error(res.status);
            const html = await res.text();
            cache.set(playerId, html);
            content.innerHTML = html;
            applyUnits(content);
        } catch (e) {
            content.innerHTML = '<p class="hockey-card-empty">Player info is unavailable right now.</p>';
        }
    }

    document.addEventListener("click", event => {
        const target = event.target.closest("[data-player-id]");
        if (!target) return;
        const playerId = target.dataset.playerId;
        if (/^\d+$/.test(playerId || "")) openCard(playerId);
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
