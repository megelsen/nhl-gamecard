// Function to synchronize widths
function synchronizeWidths() {
    const sourceElement = document.getElementById('widthSourceElement');
    const targetElements = document.querySelectorAll('.widthTargetElement');                
    const sourceWidth = sourceElement.offsetWidth;
    const adjustedWidth = sourceWidth ;
    targetElements.forEach(element => {
        element.style.width = `${adjustedWidth}px`;
    });
} 