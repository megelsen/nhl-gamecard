// "Export PNG" in the footer: captures the dashboard (.content) minus the controls (modal buttons,
// standings tabs, goalie arrows, link icons) and with spoilers revealed. The layout select next to it
// picks "as shown" (this window) or a 1/2/3 column layout: the columns come from media queries on the
// window width (media_scaling.css.jinja), so those load the page in a hidden iframe of a width that
// gets that layout, copy over the standings conference and goalies shown here, and capture the copy.
// NHL images go through /img-proxy, since assets.nhle.com sends no CORS headers and would taint the canvas.
// modern-screenshot only writes non-default styles; html-to-image made a ~14 MB SVG Chrome refused to decode
const EXPORT_LIBRARY = "https://cdn.jsdelivr.net/npm/modern-screenshot@4.6.8/dist/index.js";
const EXPORT_PROXY_HOSTS = ["assets.nhle.com"];
const EXPORT_EXCLUDE = [
    ".toggle-spoiler",            // spoiler covers: the scores underneath show
    ".roster_button", "#team_form",
    ".show-top5-btn", ".show-top5-btn-opponent", ".upcoming_games_button",
    ".standings-tabs-container", ".leaders-more-btn",
    "button.arrow-button",
    ".recap-link > .material-symbols-outlined",  // link icons (the record table pills are links too)
    "[hidden]", ".stats-popup",   // the other standings conference, closed modals
].join(", ");
const EXPORT_FRAME = 24; // px of team color left and right of the cards, at most (the card gap)
// Iframe widths per column count: 3 columns above max_width_medium_screen (1450px), 2 above
// max_width_small_screen (1054px), 1 above max_width_smallest_screen (539px, the phone layout)
const EXPORT_LAYOUT_WIDTHS = { 1: 640, 2: 1100, 3: 1500 };
const EXPORT_SCALE = 2;
const EXPORT_MAX_PIXELS = 16_000_000; // iOS Safari won't draw canvases larger than ~16.7M pixels
const EXPORT_SETTLE_MS = 1000;        // eventListeners.js syncs widths 700 ms after DOMContentLoaded
const EXPORT_FRAME_TIMEOUT_MS = 30000; // iframes fire no error event, so a page that never loads would hang the button
const EXPORT_IMAGE_TIMEOUT_MS = 10000; // an image that never loads is captured blank rather than hanging the button
const EXPORT_REDRAWS = 5; // at most this many extra canvas redraws on Firefox / Safari, see renderPng()

let exportLibraryPromise = null;

// Loads modern-screenshot into win (this window, or the iframe so it captures in its own document)
function loadExportLibrary(win = window) {
    if (win.modernScreenshot) return Promise.resolve();
    const load = () => new Promise((resolve, reject) => {
        const script = win.document.createElement("script");
        script.src = EXPORT_LIBRARY;
        script.onload = resolve;
        script.onerror = () => reject(new Error("Could not load the export library"));
        win.document.head.appendChild(script);
    });
    if (win !== window) return load();
    exportLibraryPromise ??= load().catch(e => {
        exportLibraryPromise = null;
        throw e;
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
        swapped.push([img, img.getAttribute("src"), img.loading]);
        img.src = `/img-proxy?url=${encodeURIComponent(url.href)}`;
    });
    await Promise.all(swapped.map(([img]) => imageReady(img)));
    return () => swapped.forEach(([img, src, loading]) => {
        img.setAttribute("src", src);
        img.loading = loading;
    });
}

// Resolves once img has loaded or failed, or after EXPORT_IMAGE_TIMEOUT_MS. A lazy image off screen
// (the leaders card on a phone) or in a hidden element never loads, and its decode() never settles,
// so it is switched to eager first
function imageReady(img) {
    img.loading = "eager";
    const timeout = new Promise(resolve => setTimeout(resolve, EXPORT_IMAGE_TIMEOUT_MS));
    return Promise.race([img.decode().catch(() => {}), timeout]);
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

function exportFileName(columns) {
    const team = document.getElementById("team_abbr")?.value || "team";
    const day = new Date().toISOString().slice(0, 10);
    return `gamecard-${team}-${day}${columns ? `-${columns}col` : ""}.png`;
}

// Captures .content of win's document as a PNG data URL
async function capture(win) {
    const doc = win.document;
    const root = doc.querySelector(".content");
    if (!root) throw new Error("Nothing to export");
    await loadExportLibrary(win);
    const restoreImages = await proxyImages(root);
    doc.body.classList.add("exporting");
    try {
        // Narrow the real .content (centered, so the cards don't move on screen) rather than the
        // copy: modern-screenshot freezes computed margins, so a narrower copy isn't re-centered
        const width = exportWidth(root);
        if (width) {
            root.style.width = `${width}px`;
            root.style.marginInline = "auto";
        }
        // Same frame above the title card as beside and below the cards (padding is safe on the copy)
        const height = root.offsetHeight + EXPORT_FRAME;
        const pixels = root.offsetWidth * height;
        return await renderPng(win, root, {
            scale: Math.min(EXPORT_SCALE, Math.sqrt(EXPORT_MAX_PIXELS / pixels)),
            height,
            style: { paddingTop: `${EXPORT_FRAME}px` },
            backgroundColor: win.getComputedStyle(doc.body).backgroundColor,
            filter: node => !(node instanceof win.Element && node.matches(EXPORT_EXCLUDE)),
        });
    } finally {
        restoreImages();
        root.style.width = root.style.marginInline = "";
        doc.body.classList.remove("exporting");
    }
}

// domToPng() in win, with the redraws capped: on Firefox and Safari modern-screenshot redraws the
// whole capture once per embedded image and CSS image (its fixSvgXmlDecode workaround, waiting
// longer before each one). For the dashboard that's hundreds of full-page redraws, minutes on a phone,
// which left the button stuck on "Exporting…". A few redraws are enough for the images to show up.
async function renderPng(win, node, options) {
    const library = win.modernScreenshot;
    let context = null;
    context = await library.createContext(node, {
        ...options,
        // Runs after every image is embedded, right before the canvas is drawn
        onCreateForeignObjectSvg: () => {
            context.drawImageCount = Math.min(context.drawImageCount, EXPORT_REDRAWS);
        },
    });
    try {
        return await library.domToPng(context);
    } finally {
        library.destroyContext(context);
    }
}

// This page in a hidden iframe at the given width, loaded and settled; the caller removes it
function loadLayoutFrame(width) {
    let frame;
    let timer;
    const timeout = new Promise((_, reject) => {
        timer = setTimeout(() => {
            frame?.remove();
            reject(new Error("The page for the export took too long to load"));
        }, EXPORT_FRAME_TIMEOUT_MS);
    });
    const loaded = new Promise((resolve, reject) => {
        frame = document.createElement("iframe");
        frame.setAttribute("aria-hidden", "true");
        frame.tabIndex = -1;
        // Off screen but rendered: display:none or visibility:hidden would skip layout and images
        frame.style.cssText = `position: fixed; top: 0; left: -${width + 100}px; width: ${width}px;
            height: 1000px; border: 0; pointer-events: none;`;
        frame.onload = async () => {
            try {
                const win = frame.contentWindow;
                await win.document.fonts?.ready;
                await new Promise(r => setTimeout(r, EXPORT_SETTLE_MS));
                resolve(frame);
            } catch (e) {
                reject(e);
            }
        };
        frame.src = location.href;
        document.body.appendChild(frame);
    });
    return Promise.race([loaded, timeout]).finally(() => clearTimeout(timer));
}

// Waits for the images in doc's .content (after copyViewState, which may swap the goalie photos)
function imagesReady(doc) {
    const images = [...doc.querySelectorAll(".content img")];
    return Promise.all(images.map(imageReady));
}

// Shows the same standings conference, leaders category and goalies in the iframe as on this page
function copyViewState(win) {
    const conference = document.querySelector(".standings-tab.active[data-conference]")?.dataset.conference;
    if (conference) win.document.querySelector(`.standings-tab[data-conference="${conference}"]`)?.click();
    const category = document.querySelector(".leaders-tab.active")?.dataset.category;
    if (category) win.document.querySelector(`.leaders-tab[data-category="${category}"]`)?.click();
    // goalieCarousel.js keeps the index in top-level lets: readable here, but not from another window
    if (typeof homeGoalieIndex === "number") {
        for (let i = 0; i < homeGoalieIndex; i++) win.nextHomeGoalie?.();
    }
    if (typeof oppGoalieIndex === "number") {
        for (let i = 0; i < oppGoalieIndex; i++) win.nextOppGoalie?.();
    }
}

async function exportPng(button, columns) {
    const label = button.innerHTML;
    button.disabled = true;
    button.textContent = "Exporting…";
    let frame = null;
    try {
        let win = window;
        if (columns) {
            frame = await loadLayoutFrame(EXPORT_LAYOUT_WIDTHS[columns]);
            win = frame.contentWindow;
            copyViewState(win);
            await imagesReady(win.document);
        }
        const dataUrl = await capture(win);
        const link = document.createElement("a");
        link.download = exportFileName(columns);
        link.href = dataUrl;
        link.click();
    } catch (e) {
        console.error("PNG export failed", e);
        alert("Sorry, the export failed. Please try again.");
    } finally {
        frame?.remove();
        button.disabled = false;
        button.innerHTML = label;
    }
}

document.addEventListener("DOMContentLoaded", () => {
    const button = document.getElementById("exportPngBtn");
    const layout = document.getElementById("export-layout");
    if (button) button.addEventListener("click", () => exportPng(button, Number(layout?.value) || 0));
});
