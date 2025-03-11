//import { timezoneMap } from './timezoneMap.js' // Adjust the path if necessary

function formatEventTime(utcStartTime) {
    const utcDate = new Date(utcStartTime); // Convert UTC string to Date object
    const userTimeZone = Intl.DateTimeFormat().resolvedOptions().timeZone;    // Get the local date-time in the user's timezone

    const options = {
        month: "short",  // Get abbreviated month (e.g., "Mar")
        day: "numeric",  // Get day number (e.g., "12")
        weekday: "short", // Get abbreviated weekday (e.g., "Thu")
        hour: "numeric",
        minute: "2-digit",
        hour12: true,
        timeZone: userTimeZone,
        timeZoneName: "short"
    };

    // Format the local date-time
    const formatter = new Intl.DateTimeFormat(navigator.language, options);
    const formattedParts = formatter.formatToParts(utcDate);

    let eventMonth, eventDate, eventDay, hour, minute, ampm, timezoneAbbr;
    for (const part of formattedParts) {
        if (part.type === "month") eventMonth = part.value;
        if (part.type === "day") eventDate = part.value;
        if (part.type === "weekday") eventDay = part.value;
        if (part.type === "hour") hour = part.value;
        if (part.type === "minute") minute = part.value;
        if (part.type === "dayPeriod") ampm = part.value.toLowerCase();
        if (part.type === "timeZoneName") timezoneAbbr = part.value;
    }

    // If the time is between midnight and 10 AM, adjust to next day
    if ((ampm === "am" && hour < 10)) {
        eventDate = parseInt(eventDate) + 1; // Move to the next day

        // Get the next day's formatted month & weekday
        const nextDay = new Date(utcDate);
        nextDay.setDate(nextDay.getDate() + 1);
        eventMonth = new Intl.DateTimeFormat(navigator.language, { month: "short", timeZone: userTimeZone }).format(nextDay);
        eventDay = new Intl.DateTimeFormat(navigator.language, { weekday: "short", timeZone: userTimeZone }).format(nextDay);
    }

    console.log("userTimeZone:", userTimeZone);
    console.log("timezoneAbbr:", timezoneAbbr);
    // 🔥 Full timezone map (Northern Hemisphere)
    const timezoneMap = {
        "America/New_York": "EST",
        "America/Chicago": "CST",
        "America/Denver": "MST",
        "America/Los_Angeles": "PST",
        "America/Toronto": "EST",
        "America/Vancouver": "PST",
        "America/Edmonton": "MST",
        "America/Mexico_City": "CST",
        "America/Phoenix": "MST",
        "America/Anchorage": "AKST",
        "America/Honolulu": "HST",
        "America/Indianapolis": "EST",
        "America/Detroit": "EST",
        "America/Seattle": "PST",
        "America/Salt_Lake_City": "MST",
        "America/Minneapolis": "CST",
        "America/Kansas_City": "CST",
        "America/Columbus": "EST",
        "America/Pittsburgh": "EST",
        "America/Atlanta": "EST",
        "Europe/London": "GMT",
        "Europe/Paris": "CET",
        "Europe/Berlin": "CET",
        "Europe/Madrid": "CET",
        "Europe/Rome": "CET",
        "Europe/Amsterdam": "CET",
        "Europe/Stockholm": "CET",
        "Europe/Moscow": "MSK",
        "Europe/Oslo": "CET",
        "Europe/Zurich": "CET",
        "Europe/Brussels": "CET",
        "Europe/Prague": "CET",
        "Europe/Belgrade": "CET",
        "Europe/Vienna": "CET",
        "Europe/Helsinki": "EET",
        "Europe/Istanbul": "TRT",
        "Europe/Dublin": "GMT",
        "Europe/Copenhagen": "CET",
        "Europe/Chisinau": "EET",
        "Europe/Sofia": "EET",
        "Europe/Lisbon": "WET",
        "Europe/Tallinn": "EET",
        "Europe/Skopje": "CET",
        "Europe/Chisinau": "EET",
        "Europe/London": "GMT",
        "Europe/Paris": "CET",
        "Europe/Berlin": "CET",
        "Europe/Madrid": "CET",
        "Europe/Rome": "CET",
        "Europe/Amsterdam": "CET",
        "Europe/Stockholm": "CET",
        "Europe/Moscow": "MSK",
        "Europe/Oslo": "CET",
        "Europe/Zurich": "CET",
        "Europe/Brussels": "CET",
        "Europe/Prague": "CET",
        "Europe/Belgrade": "CET",
        "Europe/Vienna": "CET",
        "Europe/Helsinki": "EET",
        "Europe/Istanbul": "TRT",
        "Europe/Dublin": "GMT",
        "Europe/Copenhagen": "CET",
        "Europe/Chisinau": "EET",
        "Europe/Sofia": "EET",
        "Europe/Lisbon": "WET",
        "Europe/Tallinn": "EET",
        "Europe/Sarajevo": "CET",
        "Europe/Zagreb": "CET",
        "Europe/Ljubljana": "CET",
        "Europe/Monaco": "CET",
        "Europe/Luxembourg": "CET",
        "Europe/Cluj": "EET",
        "Europe/Tirane": "CET",
        "Europe/Podgorica": "CET",
        "Europe/Valletta": "CET",
        "Europe/Andorra": "CET",
        "Europe/Chisinau": "EET",
        "Europe/Belgrade": "CET",
        "Europe/Kaliningrad": "USZ1",
        "Europe/Skopje": "CET",
        "Europe/Minsk": "MSK",
        "Europe/Georgia": "GET",
        "Europe/Moscow": "MSK",
        "Europe/Volgograd": "MSK",
        "Asia/Kolkata": "IST",
        "Asia/Tokyo": "JST",
        "Asia/Shanghai": "CST",
        "Asia/Karachi": "PKT",
        "Asia/Seoul": "KST",
        "Asia/Baghdad": "AST",
        "Asia/Bangkok": "ICT",
        "Asia/Jakarta": "WIB",
        "Asia/Manila": "PHT",
        "Asia/Kuala_Lumpur": "MYT",
        "Asia/Singapore": "SGT",
        "Asia/Hong_Kong": "HKT",
        "Asia/Dubai": "GST",
        "Asia/Calcutta": "IST",
        "Asia/Chennai": "IST",
        "Asia/Riyadh": "AST",
        "Asia/Tehran": "IRST",
        "Asia/Almaty": "ALMT",
    };

    // Override if Firefox returns GMT+X instead of proper abbreviation
    if (/^GMT[\+\-]\d+$/.test(timezoneAbbr)) {
        const timezoneOffset = timezoneAbbr;
        timezoneAbbr = timezoneMap[userTimeZone] || timezoneOffset;
        console.log('Processed timezoneAbbr:', timezoneAbbr);
    }

    return `${eventDay}, ${eventMonth} ${eventDate}, at ${hour}:${minute}${ampm} ${timezoneAbbr}`;
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