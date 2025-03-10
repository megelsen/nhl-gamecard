function formatEventTime(utcStartTime) {
    const utcDate = new Date(utcStartTime); // Convert UTC string to Date object
    const options = {
        hour: "numeric",
        minute: "2-digit",
        hour12: true,
        timeZoneName: "short"
    };

    // Get user's local timezone formatted time
    const formatter = new Intl.DateTimeFormat(navigator.language, options);
    const parts = formatter.formatToParts(utcDate);

    let hour, minute, ampm, timezoneAbbr;
    for (const part of parts) {
        if (part.type === "hour") hour = part.value;
        if (part.type === "minute") minute = part.value;
        if (part.type === "dayPeriod") ampm = part.value.toLowerCase();
        if (part.type === "timeZoneName") timezoneAbbr = part.value;
    }

    return `${hour}:${minute}${ampm} ${timezoneAbbr}`;
}

// Get the event time from the HTML element
const eventElement = document.getElementById("event-time");
const utcStartTime = eventElement.getAttribute("data-utc-time"); 

if (utcStartTime) {
    const formattedTime = formatEventTime(utcStartTime);
    // const currentContent = eventElement.innerHTML.trim();
    
    eventElement.innerHTML = `${eventElement.innerHTML} ${formattedTime}`;
} else {
    eventElement.innerHTML = "Time unavailable";
}