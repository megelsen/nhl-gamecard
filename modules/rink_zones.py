"""The shot map's 17 offensive-zone areas (named like NHL EDGE's), shared by the MoneyPuck shot
parser (assigning shots by coordinates) and the drawing (modules/elements/shot_heatmap.py).

Coordinates in feet, net at the top: x across the ice (-42.5 = left as the shooter faces the net),
y from the end boards (goal line 11, blue line 75, red line 100). EDGE doesn't publish its areas;
these boundaries were fitted to EDGE's per-area counts for a few players (about 8% of shots still
land in a neighbouring area, mostly from the two sources' coordinates differing)."""

__all__ = ['ZONES', 'STRIP_LABELS', 'zone_for', 'from_moneypuck']

# {area: (rectangles for assigning shots, SVG path of their outline, label position)}. The neutral
# zone and "beyond the red line" are drawn as shortened strips under the blue line.
ZONES = {
    "L Corner": ([(-42.5, -16, 0, 11), (-42.5, -22, 11, 20)], "M-42.5 0H-16V11H-22V20H-42.5Z", (-31, 9.5)),
    "Behind the Net": ([(-16, 16, 0, 11)], "M-16 0H16V11H-16Z", (0, 4.5)),
    "R Corner": ([(16, 42.5, 0, 11), (22, 42.5, 11, 20)], "M42.5 0H16V11H22V20H42.5Z", (31, 9.5)),
    "L Net Side": ([(-22, -10, 11, 20)], "M-22 11H-10V20H-22Z", (-16, 15.5)),
    "R Net Side": ([(10, 22, 11, 20)], "M22 11H10V20H22Z", (16, 15.5)),
    "Low Slot": ([(-10, 10, 11, 20), (-12, 12, 20, 30)], "M-10 11H10V20H12V30H-12V20H-10Z", (0, 25)),
    "Crease": ([], "M-6 11A6 6 0 0 0 6 11Z", (0, 14.5)),  # assigned by distance, see zone_for()
    "L Circle": ([(-25, -12, 20, 50)], "M-25 20H-12V50H-25Z", (-18.5, 35)),
    "R Circle": ([(12, 25, 20, 50)], "M25 20H12V50H25Z", (18.5, 35)),
    "Outside L": ([(-42.5, -25, 20, 50)], "M-42.5 20H-25V50H-42.5Z", (-33.75, 35)),
    "Outside R": ([(25, 42.5, 20, 50)], "M42.5 20H25V50H42.5Z", (33.75, 35)),
    "High Slot": ([(-12, 12, 30, 50)], "M-12 30H12V50H-12Z", (0, 40)),
    "L Point": ([(-42.5, -12, 50, 75)], "M-42.5 50H-12V75H-42.5Z", (-27, 62.5)),
    "Center Point": ([(-12, 12, 50, 75)], "M-12 50H12V75H-12Z", (0, 62.5)),
    "R Point": ([(12, 42.5, 50, 75)], "M42.5 50H12V75H42.5Z", (27, 62.5)),
    "Offensive Neutral Zone": ([], "M-42.5 75H42.5V89H-42.5Z", (0, 82)),
    "Beyond Red Line": ([], "M-42.5 89H42.5V100H-42.5Z", (0, 94.5)),
}
# Strip names, written next to the value
STRIP_LABELS = {"Offensive Neutral Zone": "Neutral zone", "Beyond Red Line": "Beyond red line"}
CREASE_RADIUS = 6


def zone_for(x, y):
    """Area name for a shot at (x, y), or None (never for a shot inside the rink)."""
    if y >= 100:
        return "Beyond Red Line"
    if y >= 75:
        return "Offensive Neutral Zone"
    if y >= 11 and x * x + (y - 11) ** 2 <= CREASE_RADIUS ** 2:
        return "Crease"
    x, y = max(-42.5, min(42.5, x)), max(0.0, y)
    for name, (rects, _, _) in ZONES.items():
        for x0, x1, y0, y1 in rects:
            if x0 <= x <= x1 and y0 <= y <= y1:
                return name
    return None


def from_moneypuck(x_adjusted, y_adjusted):
    """MoneyPuck's xCordAdjusted / yCordAdjusted (shooting towards +x, net at x = 89; +y is the
    shooter's left, checked against EDGE's left/right areas) -> this module's (x, y)."""
    return -y_adjusted, 100 - x_adjusted
