"""Render the last year of contributions as an oblique 3D city (light and dark SVGs)."""
import json
import math
import os
import sys
import urllib.request
from datetime import date

QUERY = """query($u:String!){user(login:$u){contributionsCollection{contributionCalendar{
weeks{contributionDays{date contributionCount}}}}}}"""

THEMES = {
    "light": {
        "bg": "#fafaf7", "ground": "#ecece6", "muted": "#6b6b6b", "empty": "#dcdcd3",
        "water": "#9fd3ee", "wave": "#e8f6fd",
        "levels": ["#a7e8b4", "#6fdc8c", "#22c55e", "#16a34a", "#0f7a3a", "#0a5c2c"],
    },
    "dark": {
        "bg": "#0d1117", "ground": "#161b22", "muted": "#8b949e", "empty": "#262c35",
        "water": "#1d4a6b", "wave": "#4c8fbf",
        "levels": ["#1b4d2e", "#1f7a43", "#26a659", "#2fcc6c", "#5be38e", "#a6f5c0"],
    },
}

COL, BAR, DX, DY, DEPTH, MAX_H, RIVER = 22, 13, 10.0, 9.0, 0.6, 190, 62
PAD_L, PAD_T, PAD_B, PAD_R = 24, 24, 34, 24
ROWS = 7


def fetch(user, token):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"u": user}}).encode(),
        headers={"Authorization": f"bearer {token}"},
    )
    cal = json.load(urllib.request.urlopen(req))["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    return [[(d["date"], d["contributionCount"]) for d in w["contributionDays"]] for w in cal["weeks"]]


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


def shade(hex_color, f):
    r, g, b = (int(hex_color[i:i + 2], 16) for i in (1, 3, 5))
    mix = (lambda c: c + (255 - c) * f) if f > 0 else (lambda c: c * (1 + f))
    return "#%02x%02x%02x" % tuple(round(mix(c)) for c in (r, g, b))


def render(weeks, theme):
    t = THEMES[theme]
    peak = max(1, max(n for w in weeks for _, n in w))
    items, span = layout(weeks)
    width = PAD_L + span + ROWS * DX + PAD_R
    height = PAD_T + MAX_H + ROWS * DY + PAD_B
    base_y = height - PAD_B
    dx, dy = DX * DEPTH, DY * DEPTH
    back = (ROWS * DX, -ROWS * DY)

    def plane(x0, x1, pad=0):
        y = base_y + 4
        return (f"{x0 - pad},{y} {x1 + pad},{y} {x1 + pad + back[0]},{y + back[1]} "
                f"{x0 - pad + back[0]},{y + back[1]}")

    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width:.0f} {height:.0f}" '
        f'font-family="-apple-system,Segoe UI,Helvetica,Arial,sans-serif">',
        "<style>.b{transform-box:fill-box;transform-origin:50% 100%;transform:scaleY(.02);opacity:0;"
        "animation:rise 1.1s cubic-bezier(.22,1.4,.36,1) forwards}"
        "@keyframes rise{0%{opacity:0;transform:scaleY(.02)}20%{opacity:1}100%{opacity:1;transform:scaleY(1)}}"
        ".v{stroke-dasharray:6 10;animation:flow 3s linear infinite}@keyframes flow{to{stroke-dashoffset:-32}}"
        ".f{opacity:0;animation:fade .8s ease forwards}@keyframes fade{to{opacity:1}}</style>",
        f'<rect width="100%" height="100%" rx="14" fill="{t["bg"]}"/>',
        f'<polygon fill="{t["ground"]}" points="{plane(PAD_L, PAD_L + span, 8)}"/>',
    ]
    for kind, x, val in items:
        if kind != "r":
            continue
        x0, x1 = PAD_L + x + 6, PAD_L + x + RIVER - 6
        cx = (x0 + x1) / 2
        out.append(f'<g class="f"><polygon fill="{t["water"]}" points="{plane(x0, x1)}"/>')
        for k in (-8, 0, 8):
            out.append(f'<line class="v" x1="{cx + k + back[0]}" y1="{base_y + 4 + back[1]}" x2="{cx + k}" '
                       f'y2="{base_y + 4}" stroke="{t["wave"]}" stroke-width="1.2" stroke-linecap="round"/>')
        label = f"{val} wk quiet"
        out.append(f'<text x="{cx}" y="{base_y + 22}" font-size="10" text-anchor="middle" '
                   f'fill="{t["muted"]}">{label}</text></g>')

    for day in range(ROWS):  # Sunday is the back row; draw back to front for painter's order
        r = ROWS - 1 - day
        for kind, x, w in items:
            if kind != "w":
                continue
            hit = [d for d in w if (date.fromisoformat(d[0]).weekday() + 1) % 7 == day]
            if not hit:
                continue
            d, n = hit[0]
            bx, by = PAD_L + x + r * DX, base_y - r * DY
            f = math.sqrt(n / peak)
            h = 2 if n == 0 else 5 + MAX_H * f
            col = t["empty"] if n == 0 else t["levels"][min(5, int(6 * f))]
            top = by - h
            delay = 0.15 + x / span * 2.2 + r * 0.09
            out.append(
                f'<g class="b" style="animation-delay:{delay:.2f}s"><title>{n} on {d}</title>'
                f'<polygon fill="{shade(col, -0.3)}" points="{bx + BAR},{by} {bx + BAR + dx},{by - dy} {bx + BAR + dx},{top - dy:.1f} {bx + BAR},{top:.1f}"/>'
                f'<rect x="{bx}" y="{top:.1f}" width="{BAR}" height="{h:.1f}" fill="{col}"/>'
                f'<polygon fill="{shade(col, 0.32)}" points="{bx},{top:.1f} {bx + BAR},{top:.1f} {bx + BAR + dx},{top - dy:.1f} {bx + dx},{top - dy:.1f}"/></g>'
            )
    out.append("</svg>")
    return "\n".join(out)


if __name__ == "__main__":
    weeks = fetch(sys.argv[1], os.environ["GITHUB_TOKEN"])
    os.makedirs("assets", exist_ok=True)
    for theme in THEMES:
        with open(f"assets/city-{theme}.svg", "w", encoding="utf-8") as f:
            f.write(render(weeks, theme))
