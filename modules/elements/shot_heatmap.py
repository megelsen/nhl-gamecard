from modules.elements.player_card import ordinal, season_name

__all__ = ['build_shot_heatmap', 'shot_maps']

# NHL EDGE's 17 shot-location areas drawn on the offensive zone, net at the top, in feet:
# x across the ice (-42.5 = left as the shooter faces the net), y from the end boards
# (goal line 11, faceoff dots 31, blue line 75). The neutral zone and "beyond the red line"
# are shortened strips at the bottom. {area: (SVG path, label position)}
ZONES = {
    "L Corner": ("M-42.5 0H-12V11H-22V24H-42.5Z", (-31, 11)),
    "Behind the Net": ("M-12 0H12V11H-12Z", (0, 5)),
    "R Corner": ("M42.5 0H12V11H22V24H42.5Z", (31, 11)),
    "L Net Side": ("M-22 11H-7V24H-22Z", (-14.5, 18.5)),
    "R Net Side": ("M22 11H7V24H22Z", (14.5, 18.5)),
    "Low Slot": ("M-7 11H7V24H12V38H-12V24H-7Z", (0, 30)),
    "Crease": ("M-6 11A6 6 0 0 0 6 11Z", (0, 15)),
    "L Circle": ("M-34 24H-12V60H-34Z", (-23, 43)),
    "R Circle": ("M34 24H12V60H34Z", (23, 43)),
    "Outside L": ("M-42.5 24H-34V60H-42.5Z", (-38.25, 43)),
    "Outside R": ("M42.5 24H34V60H42.5Z", (38.25, 43)),
    "High Slot": ("M-12 38H12V60H-12Z", (0, 49)),
    "L Point": ("M-42.5 60H-12V75H-42.5Z", (-27, 67.5)),
    "Center Point": ("M-12 60H12V75H-12Z", (0, 67.5)),
    "R Point": ("M42.5 60H12V75H42.5Z", (27, 67.5)),
    "Offensive Neutral Zone": ("M-42.5 75H42.5V89H-42.5Z", (0, 82)),
    "Beyond Red Line": ("M-42.5 89H42.5V100H-42.5Z", (0, 94.5)),
}
# Strip names, written next to the value
STRIP_LABELS = {"Offensive Neutral Zone": "Neutral zone", "Beyond Red Line": "Beyond red line"}

# Heat scale from pale yellow to deep red; areas without any get a neutral grey
HEAT_STOPS = ["#ffeda0", "#fed976", "#feb24c", "#fd8d3c", "#fc4e2a", "#e31a1c", "#b10026"]
EMPTY_FILL = "#eceff3"
# (mode key, button label, area field). "share" is computed: the area's part of all the player's
# shots (or shots against), which compares players with different games played.
SKATER_MODES = [("shots", "Shots", "sog"), ("goals", "Goals", "goals"), ("share", "Share", None)]
GOALIE_MODES = [("shots", "Shots against", "shotsAgainst"), ("goals", "Goals against", "goalsAgainst"),
                ("share", "Share", None)]


def build_shot_heatmap(data, is_goalie, player_id, season_id):
    """Shot map for the player card's third face, or None without data. See shot_maps()."""
    maps = shot_maps([data], is_goalie, [player_id], season_id)
    return maps[0] if maps else None


def shot_maps(datasets, is_goalie, player_ids, season_id):
    """One shot map per player, all on the same color scale (the busiest area of any of them), so
    a comparison's colors mean the same on both sides. [] when nobody has a shot. Each map:
    {"clip_id", "season", "gradient", "summary", "modes": [{key, label, max}],
     "zones": [{path, x, y, title, name, small, fills, inks, texts}]}; every zone carries its fill,
    text color and text for each mode (playerCard.js switches)."""
    modes = GOALIE_MODES if is_goalie else SKATER_MODES
    shot_field = modes[0][2]
    parsed = []
    for data in datasets:
        areas = {a.get("area"): a for a in (data or {}).get("shotLocationDetails", [])}
        totals = next((t for t in (data or {}).get("shotLocationTotals", []) if t.get("locationCode") == "all"), {})
        all_shots = sum(areas.get(name, {}).get(shot_field) or 0 for name in ZONES)
        values = {name: {key: area_value(areas.get(name, {}), field or shot_field, all_shots if key == "share" else None)
                         for key, _, field in modes}
                  for name in ZONES}
        parsed.append((areas, totals, values))
    if not any(values[name]["shots"] for _, _, values in parsed for name in ZONES):
        return []

    maxima = {key: max(values[name][key] for _, _, values in parsed for name in ZONES) for key, _, _ in modes}
    maps = []
    for player_id, (areas, totals, values) in zip(player_ids, parsed):
        zones = []
        for name, (path, (x, y)) in ZONES.items():
            fills, inks, texts = {}, {}, {}
            for key, _, _ in modes:
                value = values[name][key]
                fills[key], inks[key] = heat_color(value, maxima[key])
                texts[key] = f"{value * 100:.0f}%" if key == "share" else str(value)
            zones.append({"path": path, "x": x, "y": y, "name": STRIP_LABELS.get(name, ""), "small": name == "Crease",
                          "title": zone_title(name, areas.get(name, {}), is_goalie),
                          "fills": fills, "inks": inks, "texts": texts})
        maps.append({
            "clip_id": f"shot-map-clip-{player_id}",
            "season": season_name(season_id),
            "gradient": f"linear-gradient(to right, {', '.join(HEAT_STOPS)})",
            "summary": summary(totals, is_goalie),
            "short_summary": short_summary(totals, is_goalie),
            "modes": [{"key": key, "label": label,
                       "max": f"{maxima[key] * 100:.0f}%" if key == "share" else maxima[key]}
                      for key, label, _ in modes],
            "zones": zones,
        })
    return maps


def area_value(area, field, all_shots=None):
    # A count, or with `all_shots` the area's share of them
    value = area.get(field) or 0
    if all_shots is None:
        return value
    return value / all_shots if all_shots else 0


def heat_color(value, maximum):
    """(fill, text color) for a value relative to the busiest area. The square root spreads the
    colors, since one area (usually the low slot) often has most of the shots."""
    if not value or not maximum:
        return EMPTY_FILL, "#8a8f98"
    t = (value / maximum) ** 0.5
    position = t * (len(HEAT_STOPS) - 1)
    i = min(int(position), len(HEAT_STOPS) - 2)
    fill = mix(HEAT_STOPS[i], HEAT_STOPS[i + 1], position - i)
    return fill, ("#ffffff" if t > 0.62 else "#4a3000")


def mix(a, b, t):
    rgb = [round(int(a[k:k + 2], 16) * (1 - t) + int(b[k:k + 2], 16) * t) for k in (1, 3, 5)]
    return "#" + "".join(f"{c:02x}" for c in rgb)


def pctl(value):
    return f"{ordinal(round(value * 100))} pctl" if value is not None else None


def zone_title(name, area, is_goalie):
    # Hover text: the area's numbers and the league percentile of its volume
    if is_goalie:
        shots, goals = area.get("shotsAgainst") or 0, area.get("goalsAgainst") or 0
        parts = [f"{shots} shots against", f"{goals} goals against"]
        if shots:
            parts.append(f"{area.get('savePctg', 0):.3f}".lstrip("0") + " SV%")
        rank = pctl(area.get("savePctgPercentile")) if shots else None
        rank = f"SV% {rank}" if rank else None
    else:
        shots, goals = area.get("sog") or 0, area.get("goals") or 0
        parts = [f"{shots} shots on goal", f"{goals} goals"]
        if shots:
            parts.append(f"{(area.get('shootingPctg') or 0) * 100:.1f}%")
        rank = pctl(area.get("sogPercentile"))
        rank = f"shots {rank}" if rank else None
    return f"{name}: {', '.join(parts)}" + (f" · {rank}" if rank else "")


def summary(totals, is_goalie):
    if not totals:
        return ""
    if is_goalie:
        save_pct = f"{totals.get('savePctg') or 0:.3f}".lstrip("0")
        return f"{totals.get('shotsAgainst', 0)} shots against · {totals.get('goalsAgainst', 0)} goals against · {save_pct} SV%"
    return (f"{totals.get('sog', 0)} shots on goal · {totals.get('goals', 0)} goals · "
            f"{(totals.get('shootingPctg') or 0) * 100:.1f}%")


def short_summary(totals, is_goalie):
    # For the narrow maps side by side in a comparison
    if not totals:
        return ""
    if is_goalie:
        return f"{totals.get('shotsAgainst', 0)} SA · {totals.get('goalsAgainst', 0)} GA"
    return f"{totals.get('sog', 0)} SOG · {totals.get('goals', 0)} G"
