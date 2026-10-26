import json

from modules.elements.player_card import season_name
from modules.rink_zones import STRIP_LABELS, ZONES

__all__ = ['build_shot_heatmap', 'shot_maps']

# Shot maps from MoneyPuck's shot data (cached_moneypuck_shots): a heat map (playerCard.js smooths
# the 1-ft grid in the browser) and the 17 areas of modules/rink_zones.py, each for shots on goal /
# misses / goals (goalies: shots against / saves / goals against) as totals or as each area's share,
# plus goals vs. expected goals per area.

# Heat scale from pale yellow to deep red; areas without any get a neutral grey
HEAT_STOPS = ["#ffeda0", "#fed976", "#feb24c", "#fd8d3c", "#fc4e2a", "#e31a1c", "#b10026"]
EMPTY_FILL = "#eceff3"
# vs. expected goals: green above = better (more goals than expected for a skater, more saves for a
# goalie), red below = worse
XG_NEUTRAL, XG_ABOVE, XG_BELOW = "#f4f4f4", "#1a9850", "#d7301f"
# (key, button label, index in the cached per-area counts)
SKATER_CATEGORIES = [("shots", "Shots", 0), ("misses", "Misses", 1), ("goals", "Goals", 2)]
GOALIE_CATEGORIES = [("shots", "Shots", 0), ("saves", "Saves", 1), ("goals", "Goals", 2)]
UNITS = [("total", "Total"), ("pct", "%")]


def build_shot_heatmap(shots, is_goalie, player_id, season_id):
    """Shot map for the player card's third face, or None without shots. See shot_maps()."""
    maps = shot_maps(shots, is_goalie, [player_id], season_id)
    return maps[0] if maps else None


def shot_maps(shots, is_goalie, player_ids, season_id):
    """One shot map per player, all on the same color scales (a comparison's colors mean the same
    on both sides); [] when nobody has a shot. Each map: {"clip_id", "season", "is_goalie",
    "categories", "units", "stops", "gradient", "xg_gradient", "xg_max", "maxima", "summary" and
    "short_summary" ([(value, label)] tiles under the map), "heat" (JSON for playerCard.js), "zones": [{path, x, y, name, small, strip,
    title, fills, inks, texts}]}. Fills, text colors and texts are per mode key ("shots-total",
    "goals-pct", "xg", ...), swapped by playerCard.js."""
    group = (shots or {}).get("goalies" if is_goalie else "skaters") or {}
    players = [group.get(str(player_id)) or {} for player_id in player_ids]
    if not any(player.get("z") for player in players):
        return []
    categories = GOALIE_CATEGORIES if is_goalie else SKATER_CATEGORIES

    values = [zone_values(player.get("z") or {}, categories, is_goalie) for player in players]
    keys = values[0][next(iter(ZONES))].keys()
    maxima = {key: max(abs(v[zone][key]) for v in values for zone in ZONES) for key in keys}

    maps = []
    for player_id, player, player_values in zip(player_ids, players, values):
        zones = []
        for name, (_, path, (x, y)) in ZONES.items():
            fills, inks, texts = {}, {}, {}
            for key in keys:
                value = player_values[name][key]
                if key == "xg":
                    fills[key], inks[key] = xg_color(value, maxima[key])
                else:
                    fills[key], inks[key] = heat_color(value, maxima[key])
                texts[key] = format_value(key, value)
            zones.append({"path": path, "x": x, "y": y, "name": STRIP_LABELS.get(name, ""),
                          "small": name == "Crease", "strip": name in STRIP_LABELS,
                          "title": zone_title(name, (player.get("z") or {}).get(name), is_goalie),
                          "fills": fills, "inks": inks, "texts": texts})
        totals = [sum(counts[i] for counts in (player.get("z") or {}).values()) for i in range(4)]
        maps.append({
            "clip_id": f"shot-map-clip-{player_id}",
            "season": season_name(season_id),
            "is_goalie": is_goalie,
            "categories": [{"key": key, "label": label} for key, label, _ in categories],
            "units": [{"key": key, "label": label} for key, label in UNITS],
            "stops": json.dumps(HEAT_STOPS),
            "gradient": f"linear-gradient(to right, {', '.join(HEAT_STOPS)})",
            "xg_gradient": f"linear-gradient(to right, {XG_BELOW}, {XG_NEUTRAL}, {XG_ABOVE})",
            "xg_max": f"{maxima['xg']:.1f}",
            "maxima": {key: format_value(key, value) for key, value in maxima.items() if key != "xg"},
            "summary": summary(totals, is_goalie),
            "short_summary": summary(totals, is_goalie, short=True),
            "heat": json.dumps(player.get("h") or {}, separators=(",", ":")),
            "zones": zones,
        })
    return maps


def zone_values(zones, categories, is_goalie):
    """{area: {"shots-total": n, "shots-pct": share, ..., "xg": goals above expected}}. For a goalie
    "xg" is expected goals against minus goals against: positive = saved more than expected."""
    totals = {key: sum(counts[i] for counts in zones.values()) for key, _, i in categories}
    values = {}
    for name in ZONES:
        counts = zones.get(name) or [0, 0, 0, 0.0]
        area = {}
        for key, _, i in categories:
            area[f"{key}-total"] = counts[i]
            area[f"{key}-pct"] = counts[i] / totals[key] if totals[key] else 0
        area["xg"] = counts[3] - counts[2] if is_goalie else counts[2] - counts[3]
        values[name] = area
    return values


def format_value(key, value):
    if key == "xg":
        return f"{value:+.1f}".replace("-", "−") if round(value, 1) else "0.0"
    if key.endswith("-pct"):
        return f"{value * 100:.0f}%"
    return str(value)


def heat_color(value, maximum):
    """(fill, text color) for a value relative to the busiest area. The square root spreads the
    colors, since one area (usually the low slot) often has most of the shots."""
    if not value or not maximum:
        return EMPTY_FILL, "#8a8f98"
    t = (value / maximum) ** 0.5
    position = t * (len(HEAT_STOPS) - 1)
    i = min(int(position), len(HEAT_STOPS) - 2)
    return mix(HEAT_STOPS[i], HEAT_STOPS[i + 1], position - i), ("#ffffff" if t > 0.62 else "#4a3000")


def xg_color(value, maximum):
    # Diverging: white around zero, green above expected, red below; scaled by the largest difference
    if not maximum or abs(value) < 0.05:
        return XG_NEUTRAL, "#8a8f98"
    t = min(1.0, abs(value) / maximum) ** 0.7
    return mix(XG_NEUTRAL, XG_ABOVE if value > 0 else XG_BELOW, t), ("#ffffff" if t > 0.6 else "#333333")


def mix(a, b, t):
    rgb = [round(int(a[k:k + 2], 16) * (1 - t) + int(b[k:k + 2], 16) * t) for k in (1, 3, 5)]
    return "#" + "".join(f"{c:02x}" for c in rgb)


def zone_title(name, counts, is_goalie):
    # Hover text with the area's numbers
    shots, second, goals, xg = counts or [0, 0, 0, 0.0]
    if is_goalie:
        save_pct = f" ({(shots - goals) / shots:.3f})".replace("0.", ".", 1) if shots else ""
        return (f"{name}: {shots} shots against, {second} saves, {goals} goals against{save_pct} · "
                f"{xg:.1f} expected goals against ({xg - goals:+.1f} saved above expected)")
    shooting = f" ({goals / shots * 100:.1f}%)" if shots else ""
    return (f"{name}: {shots} shots on goal, {second} missed, {goals} goals{shooting} · "
            f"{xg:.1f} expected goals ({goals - xg:+.1f})")


def summary(totals, is_goalie, short=False):
    """Totals under the map as [(value, label)] tiles; `short` for the narrow maps of a comparison."""
    shots, second, goals, xg = totals
    if is_goalie:
        saved = format_value("xg", xg - goals)
        save_pct = f"{(shots - goals) / shots:.3f}".replace("0.", ".", 1) if shots else "–"
        if short:
            return [(shots, "SA"), (save_pct, "SV%"), (saved, "GSAx")]
        return [(shots, "Shots against"), (goals, "Goals against"), (save_pct, "SV%"), (saved, "Saved vs xG")]
    shooting = f"{goals / shots * 100:.1f}%" if shots else "–"
    if short:
        return [(shots, "SOG"), (goals, "G"), (shooting, "Sh%"), (f"{xg:.1f}", "xG")]
    return [(shots, "Shots on goal"), (second, "Missed"), (goals, "Goals"), (shooting, "Shooting %"),
            (f"{xg:.1f}", "Expected goals")]
