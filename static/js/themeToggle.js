// Team design switch (only rendered for teams with a theme, e.g. MIN's "Dark mode" remix).
// The server renders <body class="theme-<abbr>"> and this script, loaded right after the title card,
// removes it again for viewers who switched it off, before the cards below are parsed.
// The choice is kept per browser (localStorage) and per team. The PNG export leaves the button out
// (EXPORT_EXCLUDE in exportPng.js), and print never shows the theme (min.css is screen-only).
(function () {
    const button = document.getElementById("themeToggle");
    if (!button) return;
    const themeClass = button.dataset.themeClass;          // e.g. "theme-min"
    const storageKey = `gamecard-${themeClass}`;
    const logo = document.querySelector(".title_card > img");

    function readChoice() {
        try { return localStorage.getItem(storageKey); } catch (e) { return null; }
    }
    function saveChoice(on) {
        try { localStorage.setItem(storageKey, on ? "on" : "off"); } catch (e) { /* private mode */ }
    }

    function apply(on) {
        document.body.classList.toggle(themeClass, on);
        if (logo && button.dataset.themeLogo) {
            if (!logo.dataset.defaultSrc) logo.dataset.defaultSrc = logo.getAttribute("src");
            logo.setAttribute("src", on ? button.dataset.themeLogo : logo.dataset.defaultSrc);
        }
        button.setAttribute("aria-pressed", String(on));
        const label = on ? "Switch to the classic design" : `Switch to the ${button.dataset.themeName} design`;
        button.title = label;
        button.setAttribute("aria-label", label);
        button.querySelector(".material-symbols-outlined").textContent = on ? "light_mode" : "dark_mode";
    }

    apply(readChoice() !== "off"); // on unless switched off before

    button.addEventListener("click", () => {
        const on = !document.body.classList.contains(themeClass);
        apply(on);
        saveChoice(on);
    });
})();
