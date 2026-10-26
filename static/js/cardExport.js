// Card export: the Export icon on a player card or comparison opens #cardExportPopUp with a preview
// of exactly what the PNG will show and a download button. Front, back and the comparison bars
// export the face as shown, without the icons. Shot maps get a sheet built from copies of the open
// maps: a) the current view, b) two stats side by side, c) all stats in a 2x2 grid (a comparison:
// one row per stat, one column per player), each in Heat or Zones (vs xG always as zones) and Total
// or % (a skater next to a goalie: % only), with the stat tiles below. Capturing reuses exportPng.js (library, /img-proxy for NHL images).
const CARD_EXPORT_SCALE = 2;
const CARD_EXPORT_WIDE = 640; // px: sheets with two maps side by side
const CARD_EXPORT_LAYOUTS = [["current", "Current view"], ["two", "Two stats"], ["all", "All stats"]];
const CARD_EXPORT_VIEWS = [["heat", "Heat"], ["zones", "Zones"]];
const CARD_EXPORT_UNITS = [["total", "Total"], ["pct", "%"]];

let cardExport = null; // what the open export shows: {face, kind, name, ...shot map state}

function exportElement(tag, className, text) {
    const element = document.createElement(tag);
    if (className) element.className = className;
    if (text !== undefined) element.textContent = text;
    return element;
}

function slug(text) {
    return String(text).normalize("NFKD").replace(/[̀-ͯ]/g, "").toLowerCase()
        .replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
}

// The face currently showing in a card or comparison flip card
function visibleFace(flip) {
    const faces = [...flip.querySelectorAll(".hockey-card-flipper > .hockey-card")];
    return faces.find(face => !face.hidden) || faces[0];
}

function openCardExport(button) {
    const flip = button.closest(".hockey-card-flip");
    if (!flip) return;
    const face = visibleFace(flip);
    const comparison = flip.classList.contains("player-compare-flip");
    const names = comparison
        ? [...flip.querySelectorAll(".player-compare-side .option-name")].map(el => el.textContent.trim())
        : [flip.querySelector(".hockey-card-front .hockey-card-name")?.textContent.trim() || "player"];
    const map = face.querySelector(".shot-map");
    cardExport = {
        flip, face, comparison, map,
        // Card colors live on the flip card (player card) or on the face (comparison)
        style: (comparison ? face : flip).getAttribute("style") || "",
        name: names.map(name => slug(name.split(" ").slice(-1)[0])).join("-vs-"),
        kind: map ? "shot-map" : comparison ? "comparison"
            : face.classList.contains("hockey-card-back") ? "percentiles" : "card",
    };
    if (map) {
        const categories = shotMapCategories(map);
        // Starts from what the card shows (its One / Two / All layout)
        const layout = { two: "two", all: "all" }[map.dataset.layout] || "current";
        Object.assign(cardExport, {
            categories,
            layout,
            view: map.dataset.view,
            unit: map.dataset.unitFixed || map.dataset.unit,
            cats: layout === "two" ? map.dataset.cats.split(",")
                : [map.dataset.cat === "xg" ? categories[0][0] : map.dataset.cat,
                   categories.find(([key]) => key !== map.dataset.cat)?.[0] || categories[1][0]],
        });
    }
    renderExportOptions();
    renderExportPreview();
    document.getElementById("cardExportPopUp").style.display = "flex";
}

// --- Options (shot maps only) -----------------------------------------------------------------

function exportPill(name, options, value) {
    return `<span class="shot-map-pill">${options.map(([key, label]) =>
        `<span class="shot-map-pill-option${key === value ? " active" : ""}" role="button" tabindex="0"
               data-export-set="${name}" data-value="${key}">${label}</span>`).join("")}</span>`;
}

function exportSelect(index, value) {
    return `<select class="card-export-select" data-export-cat="${index}">${cardExport.categories.map(([key, label]) =>
        `<option value="${key}"${key === value ? " selected" : ""}>${label}</option>`).join("")}</select>`;
}

function renderExportOptions() {
    const box = document.querySelector("#cardExportPopUp .card-export-options");
    if (!cardExport.map) {
        box.innerHTML = "";
        return;
    }
    const { layout, view, unit, cats } = cardExport;
    // The current view keeps the card's settings; the others choose view, unit and (b) two stats
    box.innerHTML = `
        <div class="card-export-row"><span class="card-export-label">Layout</span>${exportPill("layout", CARD_EXPORT_LAYOUTS, layout)}</div>
        ${layout === "two" ? `<div class="card-export-row"><span class="card-export-label">Stats</span>${exportSelect(0, cats[0])}
            <span class="card-export-and">&amp;</span>${exportSelect(1, cats[1])}</div>` : ""}
        ${layout !== "current" ? `<div class="card-export-row"><span class="card-export-label">View</span>${exportPill("view", CARD_EXPORT_VIEWS, view)}
            ${cardExport.map.dataset.unitFixed ? "" : exportPill("unit", CARD_EXPORT_UNITS, unit)}</div>
            <p class="card-export-hint">vs xG is shown per area (Zones) in either view.</p>` : ""}`;
}

// --- Preview ----------------------------------------------------------------------------------

function renderExportPreview() {
    const stage = document.querySelector("#cardExportPopUp .card-export-stage");
    stage.replaceChildren(cardExport.map ? shotMapSheet() : faceCopy());
}

// The face as shown, straightened (a turned face would come out mirrored) and without the icons
function faceCopy() {
    const copy = cardExport.face.cloneNode(true);
    copy.hidden = false;
    copy.classList.remove("face-turned");
    copy.classList.add("card-export-face");
    copy.querySelectorAll(".player-compare-head [data-card-action], .player-compare-change").forEach(el => el.remove());
    copy.setAttribute("style", `${cardExport.style}; width: ${cardExport.face.offsetWidth}px;`);
    return copy;
}

function shotMapSheet() {
    const { map, comparison, layout, categories } = cardExport;
    const label = key => categories.find(([k]) => k === key)?.[1] || key;
    const viewLabel = key => (key === "xg" ? "Zones" : CARD_EXPORT_VIEWS.find(([k]) => k === key)[1]);
    // The current view takes the card's settings, the other layouts the export's own
    const current = layout === "current";
    const view = current ? map.dataset.view : cardExport.view;
    const unit = current ? map.dataset.unit : cardExport.unit;
    const cats = current ? [map.dataset.cat] : layout === "two" ? cardExport.cats : categories.map(([key]) => key);
    const unitLabel = CARD_EXPORT_UNITS.find(([key]) => key === unit)[1];
    const what = current ? label(cats[0]) : layout === "two" ? `${label(cats[0])} & ${label(cats[1])}` : "All stats";
    const title = current && cats[0] === "xg" ? "vs xG · Zones" : `${what} · ${viewLabel(view)} · ${unitLabel}`;

    const sheet = exportElement("div", "hockey-card card-export-sheet");
    const wide = comparison || layout !== "current";
    sheet.setAttribute("style", `${cardExport.style}; width: ${wide ? CARD_EXPORT_WIDE : cardExport.face.offsetWidth}px;`);

    // Header: the card's head (headshot, name, team, flag) or the comparison's player names
    const head = cardExport.face.querySelector(".hockey-card-back-head");
    if (head) {
        sheet.append(Object.assign(head.cloneNode(true), { className: "hockey-card-back-head card-export-head" }));
    } else {
        const compareHead = exportElement("div", "player-compare-head card-export-head");
        compareHead.append(exportElement("h3", "", cardExport.face.querySelector(".player-compare-head h3")?.textContent || ""));
        sheet.append(compareHead);
    }
    sheet.append(exportElement("div", "card-export-title", title));

    const rinks = ownElements(map, ".shot-map-rink");
    const grid = exportElement("div", "card-export-grid");
    if (comparison) {
        // Player names over the two columns, in their comparison colors
        const names = exportElement("div", "card-export-columns");
        map.querySelectorAll(".shot-map-side").forEach(side => {
            const caption = exportElement("span", "card-export-column", side.querySelector("figcaption")?.textContent);
            caption.style.setProperty("--side-color", side.style.getPropertyValue("--side-color"));
            names.append(caption);
        });
        sheet.append(names);
        cats.forEach(cat => grid.append(shotMapCell(map, rinks, cat, view, unit, layout === "current" ? "" : label(cat))));
    } else {
        grid.classList.toggle("two-columns", cats.length > 1);
        cats.forEach(cat => grid.append(shotMapCell(map, rinks, cat, view, unit, cats.length > 1 ? label(cat) : "")));
    }
    sheet.append(grid);

    // Stat tiles: one row per player, under that player's column
    const tiles = exportElement("div", `card-export-tiles${comparison ? " two-columns" : ""}`);
    map.querySelectorAll(".shot-map-summary").forEach(summary => tiles.append(summary.cloneNode(true)));
    sheet.append(tiles);
    const source = cardExport.face.querySelector(".hockey-card-source");
    if (source) sheet.append(source.cloneNode(true));
    return sheet;
}

// --- Download ---------------------------------------------------------------------------------

async function downloadCardExport(button) {
    const target = document.querySelector("#cardExportPopUp .card-export-stage > *");
    if (!target) return;
    const label = button.innerHTML;
    button.disabled = true;
    button.textContent = "Exporting…";
    document.body.classList.add("exporting");
    let restoreImages = () => {};
    try {
        await loadExportLibrary();
        restoreImages = await proxyImages(target);
        const dataUrl = await window.modernScreenshot.domToPng(target, { scale: CARD_EXPORT_SCALE });
        const link = document.createElement("a");
        link.download = `${cardExport.name}-${cardExport.kind}-${new Date().toISOString().slice(0, 10)}.png`;
        link.href = dataUrl;
        link.click();
    } catch (e) {
        console.error("Card export failed", e);
        alert("Sorry, the export failed. Please try again.");
    } finally {
        restoreImages();
        document.body.classList.remove("exporting");
        button.disabled = false;
        button.innerHTML = label;
    }
}

document.addEventListener("DOMContentLoaded", () => {
    const modal = document.getElementById("cardExportPopUp");
    if (!modal) return;
    const close = () => { modal.style.display = "none"; };
    document.getElementById("closeBtnCardExport").addEventListener("click", close);
    window.addEventListener("click", event => {
        if (event.target === modal) close();
    });
    modal.querySelector(".card-export-download").addEventListener("click", event => downloadCardExport(event.currentTarget));
    modal.querySelector(".card-export-options").addEventListener("click", event => {
        const option = event.target.closest("[data-export-set]");
        if (!option || !cardExport) return;
        cardExport[option.dataset.exportSet] = option.dataset.value;
        renderExportOptions();
        renderExportPreview();
    });
    modal.querySelector(".card-export-options").addEventListener("keydown", event => {
        if ((event.key === "Enter" || event.key === " ") && event.target.matches("[data-export-set]")) {
            event.preventDefault();
            event.target.click();
        }
    });
    modal.querySelector(".card-export-options").addEventListener("change", event => {
        const select = event.target.closest("[data-export-cat]");
        if (!select || !cardExport) return;
        cardExport.cats[Number(select.dataset.exportCat)] = select.value;
        renderExportPreview();
    });
});
