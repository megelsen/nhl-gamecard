document.getElementById("team_abbr").addEventListener("change", function() {
    const teamAbbr = this.value; // Get selected team abbreviation
    if (teamAbbr) {
        window.location.href = `/${teamAbbr}`; // Redirect to new page
    }
});