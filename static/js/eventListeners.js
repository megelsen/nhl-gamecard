// Call the function initially and on window resize
window.addEventListener('load', function() {    
    synchronizeWidths();
    // synchronizeWidthsStatsPopUp();
});
window.addEventListener('resize', function() {    
    synchronizeWidths();
    setTimeout(applyScaling, 500);
});

document.addEventListener("DOMContentLoaded", function () {
    // Show loading wheel
    document.getElementById("loading-wheel").style.display = "flex";

    setTimeout(function () {
        // Hide loading wheel after content loads
        document.getElementById("loading-wheel").style.display = "none";

        // Run other functions after loading
        synchronizeWidths();
        applyScaling();
    }, 700); // Adjust timeout as needed
});