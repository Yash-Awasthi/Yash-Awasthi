"""The drawing itself: pure functions from columns and a theme to SVG text."""
from __future__ import annotations

import math
import re
import zlib
from datetime import date

from .layout import BAR, COL, DEPTH, DX, DY, MAX_H, PAD_B, PAD_L, PAD_R, PAD_T, RIVER, ROWS, layout, nf
from .theme import THEMES, grad, mix


def sky_scene(theme, width, horizon):
    out = []
    if theme == "dark":
        buckets = {}
        for i in range(70):
            h = zlib.crc32(b"star%d" % i)
            x, y = h % int(width), 8 + (h >> 12) % int(horizon - 8)
            r = .5 + (h >> 24) % 3 * .35
            buckets.setdefault(h % 50 // 10, []).append(f'<circle cx="{x}" cy="{y}" r="{r:.2f}"/>')
        out.append('<g fill="#fff" opacity=".8">')
        for tenth, stars in sorted(buckets.items()):  # ten groups, not seventy, share the twinkle delay
            out.append(f'<g class="t" style="animation-delay:{tenth}s">{"".join(stars)}</g>')
        out.append("</g>")
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


def car(body, theme, glass):
    """Side-view car facing +x, 18 long; origin at rear bumper, road level."""
    beam = ('<polygon points="18,-3.2 40,-6 40,0" fill="#fff3b0" opacity=".22"/>' if theme == "dark" else "")
    return (f'{beam}<path d="M0,-2.2 Q0,-4.6 2.5,-4.8 L5,-5 L7.2,-8 H12.4 L15.2,-5 Q18,-4.8 18,-2.6 V-1.4 H0 Z" fill="{body}"/>'
            f'<path d="M7.8,-7.4 H10 V-5.2 H6.2 Z M10.7,-7.4 H12.1 L14.2,-5.2 H10.7 Z" fill="{glass}"/>'
            '<rect x="0" y="-2.4" width="18" height=".7" fill="#000" opacity=".18"/>'
            '<circle cx="4.2" cy="-1.2" r="1.7" fill="#14171c"/><circle cx="4.2" cy="-1.2" r=".7" fill="#9aa3ad"/>'
            '<circle cx="13.8" cy="-1.2" r="1.7" fill="#14171c"/><circle cx="13.8" cy="-1.2" r=".7" fill="#9aa3ad"/>'
            '<rect x="17" y="-4" width="1.2" height="1" rx=".4" fill="#fff6c2"/>'
            '<rect x="-.2" y="-4" width="1" height="1" rx=".3" fill="#ff3b3b"/>')


def road(theme, x0, x1, y):
    asphalt, curb = ("#232a35", "#3a4350") if theme == "dark" else ("#7f8a85", "#c9d1cd")
    glass = "#9fd3ff" if theme == "dark" else "#d9f0ff"
    out = [f'<rect x="{x0}" y="{y}" width="{x1 - x0}" height="18" fill="{asphalt}"/>',
           f'<rect x="{x0}" y="{y + 18}" width="{x1 - x0}" height="2" fill="{curb}"/>',
           f'<line x1="{x0}" y1="{y + 9}" x2="{x1}" y2="{y + 9}" stroke="#f5e9a8" stroke-opacity=".55" stroke-dasharray="7 7"/>',
           f'<clipPath id="rd"><rect x="{x0}" y="{y - 12}" width="{x1 - x0}" height="30"/></clipPath><g clip-path="url(#rd)">']
    span = x1 - x0 + 60
    palette = ["#e5484d", "#3e8ef7", "#f5b82e", "#eceff1", "#8e6cf0", "#2bb673", "#ff8a3d"]
    for i in range(11):
        h = zlib.crc32(b"car%d" % i)
        fwd = i % 2 == 0
        base = y + (8 if fwd else 17)
        start = x0 - 30 if fwd else x1 + 30
        flip = "" if fwd else " scale(-1,1)"
        out.append(f'<g class="c" style="--d:{span if fwd else -span}px;animation-duration:{10 + h % 10}s;animation-delay:-{h % 100 / 10}s">'
                   f'<g transform="translate({start},{base}){flip}">{car(palette[h % len(palette)], theme, glass)}</g></g>')
    out.append("</g>")
    return "".join(out)


def flora(bx, by, dx, dy, seed, fog, t):
    """A tree or hedge standing on an empty day cell. Its trunk shares one CSS class."""
    leaf = mix(t["leaf"], t["fog"], fog)
    dark, light = mix(leaf, "#000000", .3), mix(leaf, "#ffffff", .25)
    cx = bx + BAR / 2 + dx / 2
    if seed % 3:
        r = 4 + seed % 3
        y = by - dy / 2
        return (f'<line class="k" x1="{nf(cx)}" y1="{nf(y)}" x2="{nf(cx)}" y2="{nf(y - 6)}"/>'
                f'<circle cx="{nf(cx)}" cy="{nf(y - 6 - r * .6)}" r="{nf(r)}" fill="{dark}"/>'
                f'<circle cx="{nf(cx - .8)}" cy="{nf(y - 7 - r * .6)}" r="{nf(r * .75)}" fill="{leaf}"/>'
                f'<circle cx="{nf(cx - 1.8)}" cy="{nf(y - 8 - r * .6)}" r="{nf(r * .3)}" fill="{light}"/>')
    return (f'<polygon fill="{dark}" points="{nf(bx + BAR)},{nf(by)} {nf(bx + BAR + dx)},{nf(by - dy)} '
            f'{nf(bx + BAR + dx)},{nf(by - dy - 5)} {nf(bx + BAR)},{nf(by - 5)}"/>'
            f'<rect x="{nf(bx)}" y="{nf(by - 5)}" width="{BAR}" height="5" rx="1.5" fill="{leaf}"/>'
            f'<polygon fill="{light}" points="{nf(bx)},{nf(by - 5)} {nf(bx + BAR)},{nf(by - 5)} '
            f'{nf(bx + BAR + dx)},{nf(by - dy - 5)} {nf(bx + dx)},{nf(by - dy - 5)}"/>')


def verge(t, x0, x1, y):
    """Grass strip with tufts; every tuft shares one path and one set of stroke attributes."""
    d = []
    x = x0 + 2
    while x < x1 - 2:
        h = zlib.crc32(b"tuft%d" % int(x))
        tall = 2 + h % 4
        d.append(f"M{nf(x)},{nf(y + 1)}l-1.2,-{tall}M{nf(x)},{nf(y + 1)}l0,-{tall + 1}M{nf(x)},{nf(y + 1)}l1.2,-{tall}")
        x += 4 + h % 6
    return (f'<rect x="{nf(x0)}" y="{nf(y)}" width="{nf(x1 - x0)}" height="6" fill="{t["grass"]}"/>'
            f'<path d="{"".join(d)}" stroke="{t["tuft"]}" stroke-width=".8" stroke-linecap="round" fill="none"/>')


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
    days = [d for w in weeks for d, _ in w]
    total = sum(n for w in weeks for _, n in w)
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="ct cd" '
        f'viewBox="0 0 {width:.0f} {height:.0f}" '
        f'font-family="-apple-system,Segoe UI,Helvetica,Arial,sans-serif">',
        f'<title id="ct">{days[0][:4]}-{days[-1][:4]}: {total:,} contributions</title>',
        f'<desc id="cd">An isometric city of GitHub contributions, one tower per '
        f'active day and one river per quiet stretch, {days[0]} to {days[-1]}, {len(weeks)} weeks, '
        f'{total:,} contributions in total.</desc>',
        "<defs>",
        grad("sky", *t["sky"]), grad("gnd", *t["ground"]), grad("wat", *t["water"]),
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
        ".s{animation:drift linear infinite alternate}@keyframes drift{to{transform:translateX(60px)}}"
        f".k{{stroke:{t['trunk']};stroke-width:1.6}}</style>",
        '<rect width="100%" height="100%" rx="16" fill="url(#sky)"/>',
        '<rect width="100%" height="100%" rx="16" fill="url(#glow)"/>',
        sky_scene(theme, width, base_y - MAX_H * 0.55),
        f'<polygon fill="{mix(t["edge"], "#000000", .2)}" points="{g1},{gy} {g1 + bkx},{gy + bky} {g1 + bkx},{gy + bky + 6} {g1},{gy + 6}"/>',
        f'<polygon fill="url(#gnd)" points="{plane(PAD_L, PAD_L + span, 10)}"/>',
        verge(t, g0, g1, gy),
    ]
    for kind, x, val in items:
        if kind != "r":
            continue
        x0, x1 = PAD_L + x + 8, PAD_L + x + RIVER - 8
        cx = (x0 + x1) / 2
        out.append(f'<g class="f"><polygon fill="url(#wat)" points="{plane(x0, x1)}"/>'
                   f'<rect x="{x0}" y="{gy}" width="{x1 - x0}" height="6" fill="{t["water"][1]}"/>')
        waves = "".join(f'<line style="animation-delay:{k / 10:.1f}s" x1="{cx + k + bkx}" y1="{gy + bky}" '
                        f'x2="{cx + k}" y2="{gy}"/>' for k in (-9, -3, 3, 9))
        out.append(f'<g class="v" stroke="{t["wave"]}" stroke-opacity=".7" stroke-width="1.1" stroke-linecap="round">{waves}</g>')
        out.append(f'<text x="{cx}" y="{gy + 40}" font-size="10" letter-spacing=".4" text-anchor="middle" '
                   f'fill="{t["muted"]}">{val} wk quiet</text></g>')

    out.append(road(theme, g0, g1, gy + 6))
    towers = sorted((n for w in weeks for _, n in w), reverse=True)[:3]
    for day in range(ROWS):  # Sunday is the back row; draw back to front for painter's order
        r = ROWS - 1 - day
        fog = r / ROWS * 0.4
        for kind, x, w in items:
            if kind != "w":
                continue
            hit = [d for d in w if (date.fromisoformat(d[0]).weekday() + 1) % 7 == day]
            if not hit:
                continue
            d, n = hit[0]
            bx, by = PAD_L + x + r * DX, base_y - r * DY
            if not n:
                delay = 0.6 + x / span * 2.4
                out.append(f'<g class="f" style="animation-delay:{delay:.2f}s">{flora(bx, by, dx, dy, zlib.crc32(d.encode()), fog, t)}</g>')
                continue
            f = math.sqrt(n / peak)
            h = 6 + MAX_H * f
            col = mix(t["levels"][min(5, int(6 * f))], t["fog"], fog)
            top = by - h
            side = f"{bx + BAR},{by} {bx + BAR + dx},{by - dy} {bx + BAR + dx},{top - dy:.1f} {bx + BAR},{top:.1f}"
            delay = 0.2 + x / span * 2.4 + r * 0.08
            parts = [
                f'<g class="b" style="animation-delay:{delay:.2f}s"><title>{n} on {d}</title>',
                f'<polygon fill="{mix(col, "#000000", .45)}" points="{side}"/>',
                f'<rect x="{bx}" y="{top:.1f}" width="{BAR}" height="{h:.1f}" fill="{col}"/>',
                f'<polygon fill="{mix(col, "#ffffff", .38)}" points="{bx},{top:.1f} {bx + BAR},{top:.1f} '
                f'{bx + BAR + dx},{top - dy:.1f} {bx + dx},{top - dy:.1f}"/>',
            ]
            seed = zlib.crc32(d.encode())
            wy, k, lit, twinkle = top + 5, 0, [], []
            while wy < by - 6:
                for wx in (bx + 3, bx + BAR - 5):
                    k += 1
                    on = (seed + k * 2654435761) % 7
                    if on >= 3:
                        continue
                    if on == 0 and theme == "dark":
                        twinkle.append(f"M{round(wx)},{round(wy)}h2v2.4h-2z")  # twinkles blink per building, not per window
                    else:
                        lit.append(f"M{round(wx)},{round(wy)}h2v2.4h-2z")  # a 2x2.4 window, one path for all
                wy += 6
            if lit:
                parts.append(f'<path d="{"".join(lit)}" fill="{t["win"]}" opacity="{t["win_on"]}"/>')
            if twinkle:
                parts.append(f'<g class="t" style="animation-delay:{(seed >> 3) % 40 / 10}s">'
                             f'<path d="{"".join(twinkle)}" fill="{t["win"]}" opacity="{t["win_on"]}"/></g>')
            if n in towers and n:
                ax, ay = bx + BAR / 2 + dx / 2, top - dy / 2
                parts.append(f'<line x1="{ax:.1f}" y1="{ay:.1f}" x2="{ax:.1f}" y2="{ay - 16:.1f}" stroke="{mix(col, "#000000", .4)}" stroke-width="1.2"/>'
                             f'<circle class="a" style="animation-delay:{towers.index(n) * .5}s" cx="{ax:.1f}" cy="{ay - 17:.1f}" r="2" fill="#ff4d4d"/>')
            parts.append("</g>")
            out.append("".join(parts))
    out.append("</svg>")
    # Every ".0" is redundant in SVG numbers: dropping it keeps the geometry byte-identical.
    return re.sub(r"(?<=[0-9])\.0(?![0-9])", "", "\n".join(out))
