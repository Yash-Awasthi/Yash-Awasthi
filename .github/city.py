"""Render the last year of contributions as an oblique 3D city (light and dark SVGs)."""
import json
import math
import os
import sys
import urllib.request
from datetime import date

QUERY = """query($u:String!){user(login:$u){contributionsCollection{contributionCalendar{
totalContributions weeks{contributionDays{date contributionCount}}}}}}"""

THEMES = {
    "light": {
        "bg": "#fafaf7", "ground": "#ecece6", "text": "#1c1c1c", "muted": "#6b6b6b",
        "empty": "#e2e2da",
        "levels": ["#a7e8b4", "#6fdc8c", "#22c55e", "#16a34a", "#0f7a3a", "#0a5c2c"],
    },
    "dark": {
        "bg": "#0d1117", "ground": "#161b22", "text": "#e6edf3", "muted": "#8b949e",
        "empty": "#21262d",
        "levels": ["#1b4d2e", "#1f7a43", "#26a659", "#2fcc6c", "#5be38e", "#a6f5c0"],
    },
}

COL, BAR, DX, DY, DEPTH, MAX_H = 15, 11, 6.0, 7.5, 0.7, 170
PAD_L, PAD_T, PAD_B, PAD_R = 30, 70, 40, 30


def fetch(user, token):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"u": user}}).encode(),
        headers={"Authorization": f"bearer {token}"},
    )
    cal = json.load(urllib.request.urlopen(req))["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    return cal["totalContributions"], [[(d["date"], d["contributionCount"]) for d in w["contributionDays"]] for w in cal["weeks"]]


def shade(hex_color, f):
    r, g, b = (int(hex_color[i:i + 2], 16) for i in (1, 3, 5))
    mix = (lambda c: c + (255 - c) * f) if f > 0 else (lambda c: c * (1 + f))
    return "#%02x%02x%02x" % tuple(round(mix(c)) for c in (r, g, b))


def render(total, weeks, theme):
    t = THEMES[theme]
    peak_date, peak = max((d for w in weeks for d in w), key=lambda d: d[1])
    peak = max(peak, 1)
    rows = 7
    width = PAD_L + len(weeks) * COL + rows * DX + PAD_R
    height = PAD_T + MAX_H + rows * DY + PAD_B
    base_y = height - PAD_B
    dx, dy = DX * DEPTH, DY * DEPTH

    def origin(wi, day):
        # Sunday is the back row so the city reads front (Saturday) to back.
        r = rows - 1 - day
        return PAD_L + wi * COL + r * DX, base_y - r * DY

    gx0, gy0 = origin(0, 6)
    gx1, _ = origin(len(weeks) - 1, 6)
    gx1 += BAR
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width:.0f} {height:.0f}" '
        f'font-family="-apple-system,Segoe UI,Helvetica,Arial,sans-serif">',
        "<style>.b{transform-box:fill-box;transform-origin:50% 100%;transform:scaleY(0);"
        "animation:rise .9s cubic-bezier(.2,.8,.2,1) forwards}"
        "@keyframes rise{to{transform:scaleY(1)}}"
        ".l{opacity:0;animation:fade .6s ease forwards}@keyframes fade{to{opacity:1}}</style>",
        f'<rect width="100%" height="100%" rx="14" fill="{t["bg"]}"/>',
        f'<text x="{PAD_L}" y="34" font-size="20" font-weight="600" fill="{t["text"]}">Contribution city</text>',
        f'<text x="{PAD_L}" y="54" font-size="12" fill="{t["muted"]}">{total:,} contributions in the last year. '
        f'One building per day, as tall as that day.</text>',
        f'<polygon fill="{t["ground"]}" points="{gx0 - 6},{gy0 + 4} {gx1 + 6},{gy0 + 4} '
        f'{gx1 + 6 + rows * DX},{gy0 + 4 - rows * DY} {gx0 - 6 + rows * DX},{gy0 + 4 - rows * DY}"/>',
    ]
    peak_xy = None
    for day in range(rows):  # back row first for painter's order
        for wi, week in enumerate(weeks):
            hit = [d for d in week if date.fromisoformat(d[0]).weekday() == (day - 1) % 7]
            if not hit:
                continue
            d, n = hit[0]
            x, y = origin(wi, day)
            h = 2 if n == 0 else 4 + MAX_H * math.sqrt(n / peak)
            col = t["empty"] if n == 0 else t["levels"][min(5, int(6 * math.sqrt(n / peak)))]
            top = y - h
            delay = (rows - 1 - day) * 0.12 + wi * 0.012
            out.append(
                f'<g class="b" style="animation-delay:{delay:.2f}s"><title>{n} on {d}</title>'
                f'<polygon fill="{shade(col, -0.28)}" points="{x + BAR},{y} {x + BAR + dx},{y - dy} {x + BAR + dx},{top - dy} {x + BAR},{top}"/>'
                f'<rect x="{x}" y="{top:.1f}" width="{BAR}" height="{h:.1f}" fill="{col}"/>'
                f'<polygon fill="{shade(col, 0.3)}" points="{x},{top:.1f} {x + BAR},{top:.1f} {x + BAR + dx},{top - dy:.1f} {x + dx},{top - dy:.1f}"/></g>'
            )
            if d == peak_date:
                peak_xy = (x + BAR / 2 + dx / 2, top - dy)
    if peak_xy:
        px, py = peak_xy
        s = -1 if px > width - 220 else 1
        lx, ly = px + 40 * s, max(PAD_T - 8, py - 30)
        pd = date.fromisoformat(peak_date)
        nice = f"{pd.day} {pd:%b %Y}"
        end = 1.0 + (rows - 1) * 0.12 + len(weeks) * 0.012
        anchor = "end" if s < 0 else "start"
        out.append(
            f'<g class="l" style="animation-delay:{end:.2f}s"><circle cx="{px:.1f}" cy="{py:.1f}" r="3" fill="{t["text"]}"/>'
            f'<path d="M{px:.1f},{py:.1f} L{lx:.1f},{ly:.1f} h{8 * s}" stroke="{t["text"]}" fill="none"/>'
            f'<text x="{lx + 12 * s:.1f}" y="{ly + 4:.1f}" font-size="12" text-anchor="{anchor}" fill="{t["text"]}">Biggest day: {peak} on {nice}</text></g>'
        )
    out.append("</svg>")
    return "\n".join(out)


if __name__ == "__main__":
    user, token = sys.argv[1], os.environ["GITHUB_TOKEN"]
    total, weeks = fetch(user, token)
    os.makedirs("assets", exist_ok=True)
    for theme in THEMES:
        with open(f"assets/city-{theme}.svg", "w", encoding="utf-8") as f:
            f.write(render(total, weeks, theme))
