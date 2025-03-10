function applyScaling() {
    var deviceWidth = window.visualViewport ? window.visualViewport.width : window.innerWidth;

    // Apply scaling only if the device width is <= max_width_smallest_screen
    if (deviceWidth <= max_width_smallest_screen) {
        var containers = document.querySelectorAll('.content');  // Get the content element
        var scaleFactor = deviceWidth / (max_width_smallest_screen);
        containers.forEach(function(container) {
            container.style.transform = 'scale(' + scaleFactor + ')';
            container.style.transformOrigin = 'left top';
        })
    } else {
        // Reset scaling if width is greater than the max width
        var containers = document.querySelectorAll('.content');
        containers.forEach(function(container) {
            container.style.transform = 'scale(1)';
        });
    }
}