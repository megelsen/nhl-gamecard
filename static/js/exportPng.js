// "Export PNG" in the footer: captures the dashboard (.content) as it looks right now, minus the
// controls (modal buttons, standings tabs, goalie arrows, link icons) and with spoilers revealed.
// NHL images go through /img-proxy, since assets.nhle.com sends no CORS headers and would taint the canvas.
// modern-screenshot only writes non-default styles; html-to-image made a ~14 MB SVG Chrome refused to decode
const EXPORT_LIBRARY = "https://cdn.jsdelivr.net/npm/modern-screenshot@4.6.8/dist/index.js";
const EXPORT_PROXY_HOSTS = ["assets.nhle.com"];
const EXPORT_EXCLUDE = [
    ".toggle-spoiler",            // spoiler covers: the scores underneath show
    ".roster_button", "#team_form",
    ".show-top5-btn", ".show-top5-btn-opponent", ".upcoming_games_button",
    ".standings-tabs-container",
    "button.arrow-button",
    ".recap-link > .material-symbols-outlined",  // link icons (the record table pills are links too)
    "[hidden]", ".stats-popup",   // the other standings conference, closed modals
].join(", ");
const EXPORT_FRAME = 24; // px of team color left and right of the cards, at most (the card gap)

let exportLibraryPromise = null;

function loadExportLibrary() {
    if (window.modernScreenshot) return Promise.resolve();
    exportLibraryPromise ??= new Promise((resolve, reject) => {
        const script = document.createElement("script");
        script.src = EXPORT_LIBRARY;
        script.onload = resolve;
        script.onerror = () => {
            exportLibraryPromise = null;
            reject(new Error("Could not load the export library"));
        };
        document.head.appendChild(script);
    });
    return exportLibraryPromise;
}

// Point NHL images at the same-origin proxy; returns a function that puts the originals back
async function proxyImages(root) {
    const swapped = [];
    root.querySelectorAll("img").forEach(img => {
        const src = img.currentSrc || img.src;
        if (!src) return;
        const url = new URL(src, location.href);
        if (!EXPORT_PROXY_HOSTS.includes(url.hostname)) return;
        swapped.push([img, img.getAttribute("src")]);
        img.src = `/img-proxy?url=${encodeURIComponent(url.href)}`;
    });
    await Promise.all(swapped.map(([img]) => img.decode().catch(() => {})));
    return () => swapped.forEach(([img, src]) => img.setAttribute("src", src));
}

// .content spans the window and centers the card rows, so a wide window leaves wide side margins.
// Width that fits the cards with at most EXPORT_FRAME on either side (null = already narrow enough).
function exportWidth(root) {
    const box = root.getBoundingClientRect();
    let left = Infinity, right = -Infinity;
    for (const child of root.children) {
        if (child.matches(EXPORT_EXCLUDE)) continue;
        const rect = child.getBoundingClientRect();
        if (!rect.width) continue;
        left = Math.min(left, rect.left);
        right = Math.max(right, rect.right);
    }
    if (left === Infinity) return null;
    const margin = Math.min(left - box.left, box.right - right, EXPORT_FRAME);
    const width = Math.ceil(right - left + 2 * Math.max(0, margin));
    return width < box.width ? width : null;
}

function exportFileName() {
    const team = document.getElementById("team_abbr")?.value || "team";
    const day = new Date().toISOString().slice(0, 10);
    return `gamecard-${team}-${day}.png`;
}

async function exportPng(button) {
    const root = document.querySelector(".content");
    if (!root) return;
    const label = button.innerHTML;
    button.disabled = true;
    button.textContent = "Exporting…";
    let restoreImages = () => {};
    try {
        await loadExportLibrary();
        restoreImages = await proxyImages(root);
        document.body.classList.add("exporting");
        // Narrow the real .content (centered, so the cards don't move on screen) rather than the
        // copy: modern-screenshot freezes computed margins, so a narrower copy isn't re-centered
        const width = exportWidth(root);
        if (width) {
            root.style.width = `${width}px`;
            root.style.marginInline = "auto";
        }
        const dataUrl = await window.modernScreenshot.domToPng(root, {
            scale: 2,
            // Same frame above the title card as beside and below the cards (padding is safe on the copy)
            height: root.offsetHeight + EXPORT_FRAME,
            style: { paddingTop: `${EXPORT_FRAME}px` },
            backgroundColor: getComputedStyle(document.body).backgroundColor,
            filter: node => !(node instanceof Element && node.matches(EXPORT_EXCLUDE)),
        });
        const link = document.createElement("a");
        link.download = exportFileName();
        link.href = dataUrl;
        link.click();
    } catch (e) {
        console.error("PNG export failed", e);
        alert("Sorry, the export failed. Please try again.");
    } finally {
        restoreImages();
        root.style.width = root.style.marginInline = "";
        document.body.classList.remove("exporting");
        button.disabled = false;
        button.innerHTML = label;
    }
}

document.addEventListener("DOMContentLoaded", () => {
    const button = document.getElementById("exportPngBtn");
    if (button) button.addEventListener("click", () => exportPng(button));
});
