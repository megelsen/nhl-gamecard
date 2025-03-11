function applyScaling() {
    var deviceWidth = window.visualViewport ? window.visualViewport.width : window.innerWidth;

    // Apply scaling only if the device width is <= max_width_smallest_screen
    if (deviceWidth <= max_width_smallest_screen) {
        var containers = document.querySelectorAll('.content');  // Get the content element
        var modal_contents = document.querySelectorAll('.content_modal')
        var scaleFactor = deviceWidth / (max_width_smallest_screen);
        containers.forEach(function(container) {
            container.style.transform = 'scale(' + scaleFactor + ')';
            container.style.transformOrigin = 'left top';  
        })    
        modal_contents.forEach(function(modal_content) {
            modal_content.style.transform = 'scale(' + scaleFactor + ')';
            modal_content.style.transformOrigin = 'top';   
        } )
    } else {
        // Reset scaling if width is greater than the max width
        var containers = document.querySelectorAll('.content');
        containers.forEach(function(container) {
            container.style.transform = 'scale(1)';
        });

        // Reset scaling if width is greater than the max width
        var modal_contents = document.querySelectorAll('.content_modal');
        modal_contents.forEach(function(modal_content) {
            modal_content.style.transform = 'scale(1)';
        });
    }
}