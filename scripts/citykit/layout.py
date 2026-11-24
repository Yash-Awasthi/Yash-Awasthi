"""Grid constants and the week-to-columns layout: pure numbers, no SVG."""
from __future__ import annotations


COL, BAR, DX, DY, DEPTH, MAX_H, RIVER = 22, 13, 10.0, 9.0, 0.6, 190, 62
PAD_L, PAD_T, PAD_B, PAD_R = 28, 40, 56, 28
ROWS = 7


def layout(weeks):
    """Weeks become ("w", x, days) columns; each run of empty weeks becomes one ("r", x, count) river."""
    items, x = [], 0.0
    for w in weeks:
        if any(n for _, n in w):
            items.append(("w", x, w))
            x += COL
        elif items and items[-1][0] == "r":
            items[-1] = ("r", items[-1][1], items[-1][2] + 1)
        else:
            items.append(("r", x, 1))
            x += RIVER
    return items, x


def nf(v):
    """A compact number: one decimal, no trailing ".0" (identical geometry, fewer bytes)."""
    s = f"{v:.1f}"
    return s[:-2] if s.endswith(".0") else s
