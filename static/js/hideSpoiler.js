document.querySelectorAll(".toggle-spoiler").forEach(button => {
    button.addEventListener("click", function() {
        let content = this.nextElementSibling;
        if (content && content.classList.contains("hide-spoiler")) {
            content.style.display = "block"; // Show the content
            this.style.display = "none"; // Hide the button after clicking
        }
    });
});