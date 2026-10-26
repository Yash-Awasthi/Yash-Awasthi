"""Render the last year of contributions as an oblique 3D city (light and dark SVGs)."""
import json
import math
import os
import sys
import urllib.request
import zlib
from datetime import date

QUERY = """query($u:String!){user(login:$u){contributionsCollection{contributionCalendar{
weeks{contributionDays{date contributionCount}}}}}}"""

THEMES = {
    "light": {
        "sky": ("#f6f9f7", "#e2ebe6"), "ground": ("#e4ebe7", "#d0dbd5"), "edge": "#b9c7c0",
        "muted": "#6b7a73", "fog": "#eef3f0", "win": "#fffbe6", "win_on": 0.6,
        "water": ("#c4e6f6", "#7cc3e8"), "wave": "#ffffff",
        "levels": ["#9fe3b0", "#5fd47f", "#2bbf62", "#169e4c", "#0e7b3b", "#095c2d"],
    },
    "dark": {
        "sky": ("#0b1324", "#04060b"), "ground": ("#162030", "#0b1018"), "edge": "#04070b",
        "muted": "#7d8a99", "fog": "#0b1324", "win": "#ffe9a8", "win_on": 0.9,
        "water": ("#15466b", "#0b2640"), "wave": "#6cc0f0",
        "levels": ["#14532d", "#16733b", "#1f9a4e", "#2bc265", "#57e08a", "#a3f5bf"],
    },
}

COL, BAR, DX, DY, DEPTH, MAX_H, RIVER = 22, 13, 10.0, 9.0, 0.6, 190, 62
PAD_L, PAD_T, PAD_B, PAD_R = 28, 40, 48, 28
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


def rgb(c):
    return [int(c[i:i + 2], 16) for i in (1, 3, 5)]


def mix(c, other, f):
    return "#%02x%02x%02x" % tuple(round(a + (b - a) * f) for a, b in zip(rgb(c), rgb(other)))


def grad(gid, c0, c1):
    return (f'<linearGradient id="{gid}" x1="0" y1="0" x2="0" y2="1">'
            f'<stop offset="0" stop-color="{c0}"/><stop offset="1" stop-color="{c1}"/></linearGradient>')


def sky_scene(theme, width, horizon):
    out = []
    if theme == "dark":
        for i in range(70):
            h = zlib.crc32(b"star%d" % i)
            x, y = h % int(width), 8 + (h >> 12) % int(horizon - 8)
            out.append(f'<circle class="t" style="animation-delay:{h % 50 / 10}s" cx="{x}" cy="{y}" '
                       f'r="{.5 + (h >> 24) % 3 * .35:.2f}" fill="#fff" opacity=".8"/>')
        out.append('<circle cx="90" cy="46" r="15" fill="#fdf3c7" opacity=".95"/>'
                   '<circle cx="97" cy="41" r="13" fill="#0b1324"/>')
    else:
        out.append('<circle cx="90" cy="48" r="28" fill="#ffd966" opacity=".18"/>'
                   '<circle cx="90" cy="48" r="15" fill="#ffcf4d"/>')
        for i, (x, y, s, dur) in enumerate(((180, 40, 1, 38), (420, 62, .8, 52), (720, 34, 1.15, 45))):
            out.append(f'<g class="s" style="animation-duration:{dur}s" opacity=".85" fill="#fff">'
                       f'<ellipse cx="{x}" cy="{y}" rx="{26 * s}" ry="{8 * s}"/>'
                       f'<ellipse cx="{x - 9 * s}" cy="{y - 6 * s}" rx="{12 * s}" ry="{9 * s}"/>'
                       f'<ellipse cx="{x + 8 * s}" cy="{y - 8 * s}" rx="{14 * s}" ry="{10 * s}"/></g>')
    return "".join(out)


def road(t, theme, x0, x1, y):
    lane = "#2a3240" if theme == "dark" else "#8f9b95"
    out = [f'<rect x="{x0}" y="{y}" width="{x1 - x0}" height="10" fill="{lane}"/>',
           f'<line x1="{x0}" y1="{y + 5}" x2="{x1}" y2="{y + 5}" stroke="#f5f1d0" stroke-opacity=".5" stroke-dasharray="6 6"/>',
           f'<clipPath id="rd"><rect x="{x0}" y="{y}" width="{x1 - x0}" height="10"/></clipPath><g clip-path="url(#rd)">']
    span = x1 - x0 + 40
    palette = ["#ff6b6b", "#4dabf7", "#ffd43b", "#f8f9fa", "#b197fc"]
    for i in range(9):
        h = zlib.crc32(b"car%d" % i)
        fwd = i % 2 == 0
        dur = 9 + h % 9
        lane_y = y + (1 if fwd else 6)
        start = x0 - 20 if fwd else x1 + 20
        lamp, tail = ("#fff6c2", "#ff3b3b")
        body = palette[h % len(palette)]
        nose, rear = (13, -1) if fwd else (-1, 13)
        out.append(f'<g class="c" style="--d:{span if fwd else -span}px;animation-duration:{dur}s;animation-delay:-{h % 90 / 10}s">'
                   f'<rect x="{start}" y="{lane_y}" width="12" height="3" rx="1" fill="{body}"/>'
                   f'<circle cx="{start + nose}" cy="{lane_y + 1.5}" r="1" fill="{lamp}"/>'
                   f'<circle cx="{start + rear}" cy="{lane_y + 1.5}" r=".8" fill="{tail}"/></g>')
    out.append("</g>")
    return "".join(out)


def render(weeks, theme):
    t = THEMES[theme]
    peak = max(1, max(n for w in weeks for _, n in w))
    items, span = layout(weeks)
    width = PAD_L + span + ROWS * DX + PAD_R
    height = PAD_T + MAX_H + ROWS * DY + PAD_B
    base_y = height - PAD_B
    gy = base_y + 4
    dx, dy = DX * DEPTH, DY * DEPTH
    bkx, bky = ROWS * DX, -ROWS * DY

    def plane(x0, x1, pad=0):
        return (f"{x0 - pad},{gy} {x1 + pad},{gy} {x1 + pad + bkx},{gy + bky} "
                f"{x0 - pad + bkx},{gy + bky}")

    g0, g1 = PAD_L - 10, PAD_L + span + 10
    accent = t["levels"][3]
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width:.0f} {height:.0f}" '
        f'font-family="-apple-system,Segoe UI,Helvetica,Arial,sans-serif">',
        "<defs>",
        grad("sky", *t["sky"]), grad("gnd", *t["ground"]), grad("wat", *t["water"]),
        '<linearGradient id="lit" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff" stop-opacity=".25"/>'
        '<stop offset=".55" stop-color="#fff" stop-opacity="0"/><stop offset="1" stop-color="#000" stop-opacity=".25"/></linearGradient>',
        '<linearGradient id="sid" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#000" stop-opacity=".04"/>'
        '<stop offset="1" stop-color="#000" stop-opacity=".32"/></linearGradient>',
        f'<radialGradient id="glow" cx=".75" cy=".85" r=".55"><stop offset="0" stop-color="{accent}" stop-opacity=".2"/>'
        f'<stop offset="1" stop-color="{accent}" stop-opacity="0"/></radialGradient>',
        "</defs>",
        "<style>.b{transform-box:fill-box;transform-origin:50% 100%;transform:scaleY(.02);opacity:0;"
        "animation:rise 1.2s cubic-bezier(.22,1.35,.36,1) forwards}"
        "@keyframes rise{0%{opacity:0;transform:scaleY(.02)}15%{opacity:1}100%{opacity:1;transform:scaleY(1)}}"
        ".v{stroke-dasharray:5 11;animation:flow 2.6s linear infinite}@keyframes flow{to{stroke-dashoffset:-32}}"
        ".f{opacity:0;animation:fade 1s ease forwards}@keyframes fade{to{opacity:1}}"
        ".t{animation:tw 4s ease-in-out infinite}@keyframes tw{50%{opacity:.1}}"
        ".c{animation:drive linear infinite}@keyframes drive{from{transform:translateX(0)}to{transform:translateX(var(--d))}}"
        ".a{animation:blink 1.6s steps(1) infinite}@keyframes blink{50%{opacity:.15}}"
        ".s{animation:drift linear infinite alternate}@keyframes drift{to{transform:translateX(60px)}}</style>",
        '<rect width="100%" height="100%" rx="16" fill="url(#sky)"/>',
        '<rect width="100%" height="100%" rx="16" fill="url(#glow)"/>',
        sky_scene(theme, width, base_y - MAX_H * 0.55),
        f'<polygon fill="{t["edge"]}" points="{g0},{gy} {g1},{gy} {g1},{gy + 6} {g0},{gy + 6}"/>',
        f'<polygon fill="{mix(t["edge"], "#000000", .2)}" points="{g1},{gy} {g1 + bkx},{gy + bky} {g1 + bkx},{gy + bky + 6} {g1},{gy + 6}"/>',
        f'<polygon fill="url(#gnd)" points="{plane(PAD_L, PAD_L + span, 10)}"/>',
    ]
    for kind, x, val in items:
        if kind != "r":
            continue
        x0, x1 = PAD_L + x + 8, PAD_L + x + RIVER - 8
        cx = (x0 + x1) / 2
        out.append(f'<g class="f"><polygon fill="url(#wat)" points="{plane(x0, x1)}"/>'
                   f'<rect x="{x0}" y="{gy}" width="{x1 - x0}" height="6" fill="{t["water"][1]}"/>')
        for k in (-9, -3, 3, 9):
            out.append(f'<line class="v" style="animation-delay:{k / 10:.1f}s" x1="{cx + k + bkx}" y1="{gy + bky}" '
                       f'x2="{cx + k}" y2="{gy}" stroke="{t["wave"]}" stroke-opacity=".7" stroke-width="1.1" stroke-linecap="round"/>')
        out.append(f'<text x="{cx}" y="{gy + 34}" font-size="10" letter-spacing=".4" text-anchor="middle" '
                   f'fill="{t["muted"]}">{val} wk quiet</text></g>')

    out.append(road(t, theme, g0, g1, gy + 6))
    towers = sorted((n for w in weeks for _, n in w), reverse=True)[:3]
    for day in range(ROWS):  # Sunday is the back row; draw back to front for painter's order
        r = ROWS - 1 - day
        fog = r / ROWS * 0.4
        for kind, x, w in items:
            if kind != "w":
                continue
            hit = [d for d in w if d[1] and (date.fromisoformat(d[0]).weekday() + 1) % 7 == day]
            if not hit:
                continue
            d, n = hit[0]
            bx, by = PAD_L + x + r * DX, base_y - r * DY
            f = math.sqrt(n / peak)
            h = 6 + MAX_H * f
            col = mix(t["levels"][min(5, int(6 * f))], t["fog"], fog)
            top = by - h
            side = f"{bx + BAR},{by} {bx + BAR + dx},{by - dy} {bx + BAR + dx},{top - dy:.1f} {bx + BAR},{top:.1f}"
            delay = 0.2 + x / span * 2.4 + r * 0.08
            parts = [
                f'<g class="b" style="animation-delay:{delay:.2f}s"><title>{n} on {d}</title>',
                f'<polygon fill="{mix(col, "#000000", .32)}" points="{side}"/><polygon fill="url(#sid)" points="{side}"/>',
                f'<rect x="{bx}" y="{top:.1f}" width="{BAR}" height="{h:.1f}" fill="{col}"/>',
                f'<rect x="{bx}" y="{top:.1f}" width="{BAR}" height="{h:.1f}" fill="url(#lit)"/>',
                f'<polygon fill="{mix(col, "#ffffff", .38)}" points="{bx},{top:.1f} {bx + BAR},{top:.1f} '
                f'{bx + BAR + dx},{top - dy:.1f} {bx + dx},{top - dy:.1f}"/>',
            ]
            seed = zlib.crc32(d.encode())
            wy, k = top + 5, 0
            while wy < by - 6:
                for wx in (bx + 3, bx + BAR - 5):
                    k += 1
                    on = (seed + k * 2654435761) % 7
                    if on < 3:
                        tw = f' class="t" style="animation-delay:{(seed + k) % 40 / 10}s"' if on == 0 and theme == "dark" else ""
                        parts.append(f'<rect{tw} x="{wx}" y="{wy:.1f}" width="2" height="2.4" fill="{t["win"]}" opacity="{t["win_on"]}"/>')
                wy += 6
            if n in towers and n:
                ax, ay = bx + BAR / 2 + dx / 2, top - dy / 2
                parts.append(f'<line x1="{ax:.1f}" y1="{ay:.1f}" x2="{ax:.1f}" y2="{ay - 16:.1f}" stroke="{mix(col, "#000000", .4)}" stroke-width="1.2"/>'
                             f'<circle class="a" style="animation-delay:{towers.index(n) * .5}s" cx="{ax:.1f}" cy="{ay - 17:.1f}" r="2" fill="#ff4d4d"/>')
            parts.append("</g>")
            out.append("".join(parts))
    out.append("</svg>")
    return "\n".join(out)


if __name__ == "__main__":
    weeks = fetch(sys.argv[1], os.environ["GITHUB_TOKEN"])
    os.makedirs("assets", exist_ok=True)
    for theme in THEMES:
        with open(f"assets/city-{theme}.svg", "w", encoding="utf-8") as f:
            f.write(render(weeks, theme))
