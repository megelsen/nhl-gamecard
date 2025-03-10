 // Function to extract team abbreviation from the image source or alt attribute
 function extractTeamAbbr(imgElement) {
    // If the abbreviation is in the 'src' URL (e.g., https://assets.nhle.com/logos/nhl/svg/team_abbr_light.svg)
    const src = imgElement.getAttribute('src');
    const match = src.match(/\/([A-Z]{3})_light\.svg/); // Regex to match the 3-letter team abbreviation
    
    if (match) {
        return match[1]; // Return the team abbreviation
    }
    
    return null; // If no abbreviation found
}

// Add event listener for all team image links
const teamLinks = document.querySelectorAll('.team-link');
teamLinks.forEach(link => {
    link.addEventListener('click', function(event) {
        const imgElement = link.querySelector('img'); // Get the image inside the clicked link
        const teamAbbr = extractTeamAbbr(imgElement); // Extract the abbreviation

        if (teamAbbr) {
            // Reload the page with the new team_abbr in the query string
            // Set the team_abbr value in the hidden input field
            document.getElementById("team_abbr").value = teamAbbr;

            // Call the handleTeamChange function to submit the form
            handleTeamChange(); // Reusing your function to submit the form
        }
    });
});
