// JavaScript function to automatically submit the form when the dropdown changes
function handleTeamChange() {
    // Show loading wheel immediately
    document.getElementById("loading-wheel").style.display = "flex";
    // Slight delay to ensure UI updates before form submission
    setTimeout(function () {
        document.getElementById("team_form").submit();
    }, 50); // Adjust delay if needed
}