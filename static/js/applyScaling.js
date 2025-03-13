function applyScaling() {
    var deviceWidth = window.visualViewport ? window.visualViewport.width : window.innerWidth;

    // Apply scaling only if the device width is <= max_width_smallest_screen
    if (deviceWidth <= max_width_smallest_screen) {        
        var modal_contents = document.querySelectorAll('.content_scalable')
        var scaleFactor = deviceWidth / (max_width_smallest_screen - 70);
  
        modal_contents.forEach(function(modal_content) {
            modal_content.style.transform = 'scale(' + scaleFactor +')';
            modal_content.style.transformOrigin = 'left top';   
        } )
    } else {
        // Reset scaling if width is greater than the max width
        var modal_contents = document.querySelectorAll('.content_scalable');
        modal_contents.forEach(function(modal_content) {
            modal_content.style.transform = 'scale(1)';
        });
    }
}