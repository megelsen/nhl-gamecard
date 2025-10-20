document.addEventListener("DOMContentLoaded", function() {
    const sections = [
        { id: "points-leaders-content", title: "Points" },
        { id: "goal-leaders-content", title: "Goals" },
        { id: "assist-leaders-content", title: "Assists" },
    ];

    let currentIndex = 0;
    const modalTitle = document.getElementById("modal-title");

    // Add event listeners to tabs
    const tabs = document.querySelectorAll(".tab");
    tabs.forEach(tab => {
        tab.addEventListener("click", () => {
            const index = parseInt(tab.getAttribute("data-index"));
            switchContent(index);
        });
    });

    function switchContent(newIndex) {
        document.getElementById(sections[currentIndex].id).style.display = "none";
        currentIndex = newIndex;
        document.getElementById(sections[currentIndex].id).style.display = "block";
        updateActiveTab();
    }

    function updateActiveTab() {
        tabs.forEach(tab => tab.classList.remove("active"));
        tabs[currentIndex].classList.add("active");
    }

    updateActiveTab();

    // --- Modal controls ---
    const modal = document.getElementById("statsPopUp");
    const moreDots = document.getElementById("moreStats");
    const closeBtn = document.getElementById("closeBtn");

    function positionModal() {
        modal.style.display = "flex";
    }

    // --- Hidden content sources ---
    const teamData = {
        points: document.getElementById("team-points")?.innerHTML || "",
        goals: document.getElementById("team-goals")?.innerHTML || "",
        assists: document.getElementById("team-assists")?.innerHTML || ""
    };

    const oppData = {
        points: document.getElementById("opp-points")?.innerHTML || "",
        goals: document.getElementById("opp-goals")?.innerHTML || "",
        assists: document.getElementById("opp-assists")?.innerHTML || ""
    };

    let currentMode = "team"; // "team" or "opponent"

    function loadModalContent(mode) {
        const data = mode === "opponent" ? oppData : teamData;
        document.getElementById("points-leaders-content").innerHTML = data.points;
        document.getElementById("goal-leaders-content").innerHTML = data.goals;
        document.getElementById("assist-leaders-content").innerHTML = data.assists;

        if (modalTitle) {
            modalTitle.textContent = mode === "opponent" ? "Top 5 – Opponent" : "Top 5 – Team";
        }
    }

    moreDots.onclick = function() {
        currentMode = "team";
        loadModalContent(currentMode);
        positionModal();
    };

    // Opponent button
    const moreDotsOpponent = document.getElementById("moreStatsOpponent");
    if (moreDotsOpponent) {
        moreDotsOpponent.onclick = function() {
            currentMode = "opponent";
            loadModalContent(currentMode);
            positionModal();
        };
    }

    closeBtn.onclick = function() {
        modal.style.display = "none";
    };

    window.onclick = function(event) {
        if (event.target === modal) {
            modal.style.display = "none";
        }
    };
});