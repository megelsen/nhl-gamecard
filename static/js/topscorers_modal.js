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
    // Hide current section
    document.getElementById(sections[currentIndex].id).style.display = "none";
    
    // Update the current index to the new tab index
    currentIndex = newIndex;

    // Show the new section
    document.getElementById(sections[currentIndex].id).style.display = "block";

    // Update active tab
    updateActiveTab();
}

function updateActiveTab() {
    // Remove active class from all tabs
    tabs.forEach(tab => tab.classList.remove("active"));

    // Add active class to the current tab
    tabs[currentIndex].classList.add("active");
}

// Initialize by setting the active tab
updateActiveTab();
// Get the modal, the button, and the close button
    const modal = document.getElementById("statsPopUp");
    const moreDots = document.getElementById("moreStats");
    const closeBtn = document.getElementById("closeBtn");

    function positionModal() {
        modal.style.visibility = "hidden"; // Hide the modal but keep it in the layout to calculate size
        modal.style.display = "flex"; // Temporarily display to calculate width/height
        const rect = moreDots.getBoundingClientRect(); // Get position of the icon
        const modalWidth = modal.clientWidth;  // Get the modal's width
        const modalHeight = modal.clientHeight; // Get the modal's height
        modal.style.visibility = "visible"; // Make sure the modal is visible after calculations

        // Make sure the modal doesn't go off-screen
        const viewportWidth = window.innerWidth;
        const viewportHeight = window.innerHeight;
        const dotsBottom = rect.bottom
       
        // Position modal below the "more_horiz" icon by default
        let modalLeft = rect.left + modalWidth - 15;
        let modalTop = dotsBottom - 100;

        console.log("Modal Width:", modalWidth);
        console.log("Modal Height:", modalHeight);
        console.log("Modal Left:", modalLeft);
        console.log("Modal Top:", modalTop);
        console.log("Viewport Width:", viewportWidth);
        console.log("Viewport Height:", viewportHeight);
        // Check if the modal overflows the right edge of the viewport
        if (modalWidth > viewportWidth){
            modalLeft = 20;
        }
        // Set the modal's position
        modal.style.left = `${modalLeft}px`;
        modal.style.top = `${modalTop}px`;
        modal.style.display = "flex"; // Show the modal
    }

    moreDots.onclick = function() {
        positionModal(); // Position the modal when "more_horiz" is clicked
    };
    // When the user clicks on the close button, close the modal
    closeBtn.onclick = function() {    
        modal.style.display = "none"; // Hide the modal
    }

    // When the user clicks anywhere outside the modal, close it
    window.onclick = function(event) {
        if (event.target === modal) {
            modal.style.display = "none"; // Hide the modal
        }
    }