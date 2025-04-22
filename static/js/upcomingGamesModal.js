

// Get the modal, the button, and the close button
    const modalUpcoming = document.getElementById("UpcomingGamesPopUp");
    const moreBtnUpcoming = document.getElementById("moreGames");
    const closeBtnUpcoming = document.getElementById("closeBtnUpcoming");

    function positionModalUpcoming() {
      
        modalUpcoming.style.display = "flex"; // Show the modal
    }

    moreBtnUpcoming.onclick = function() {
        positionModalUpcoming(); // Position the modal when "more_horiz" is clicked
    };

    // When the user clicks on the close button, close the modal
    closeBtnUpcoming.onclick = function() {    
        modalUpcoming.style.display = "none"; // Hide the modal
    }

    // When the user clicks anywhere outside the modal, close it
    window.onclick = function(event) {
        if (event.target === modalUpcoming) {
            modalUpcoming.style.display = "none"; // Hide the modal
        }
    }