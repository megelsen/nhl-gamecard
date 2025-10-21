// Function to synchronize widths
function synchronizeWidths() {
    const sourceElement = document.getElementById('widthSourceElement');
    const targetElements = document.querySelectorAll('.widthTargetElement');                
    const sourceWidth = sourceElement.offsetWidth;
    const adjustedWidth = sourceWidth ;
    targetElements.forEach(element => {
        element.style.width = `${adjustedWidth}px`;
    });

    const sourceElementCard = document.getElementById('card_target_width');
    const targetElementsCard = document.querySelectorAll('.statsCard');                
    const sourceWidthCard = sourceElementCard.offsetWidth;
    const adjustedWidthCard = sourceWidthCard ;
    targetElementsCard.forEach(element => {
        element.style.width = `${adjustedWidthCard}px`;
    });

} 