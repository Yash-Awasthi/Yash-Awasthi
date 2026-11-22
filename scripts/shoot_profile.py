#!/usr/bin/env python3
"""Screenshot the live profile at three widths in both colour schemes.

Manual, not CI: it needs a Playwright-compatible browser (`patchright` or
`playwright`) and network access to github.com.

    python3 scripts/shoot_profile.py --out docs/screenshots/before

Writes `<out>/<width>-<scheme>.png` for 360, 768 and 1440 px, and prints what sits
above the 640 px fold at 360 px so the numbers in plan.md come from a measurement.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

# Each viewport height is the fold that plan.md measures against: a phone, a tablet, a laptop.
VIEWPORTS = ((360, 640), (768, 1024), (1440, 900))


def measure(page) -> dict:
    """Where the name, the first sentence and the badges end, relative to the viewport."""
    return page.evaluate(
        """() => {
        const box = sel => { const el = document.querySelector(sel); if (!el) return null;
            const r = el.getBoundingClientRect(); return {top: Math.round(r.top), bottom: Math.round(r.bottom)}; };
        const article = document.querySelector('article.markdown-body');
        const firstP = article ? article.querySelector('p') : null;
        const badges = article ? article.querySelector('p img') : null;
        const badgeRow = badges ? badges.closest('p') : null;
        const r = el => el ? (b => ({top: Math.round(b.top), bottom: Math.round(b.bottom)}))(el.getBoundingClientRect()) : null;
        return {
            name: box('h1'),
            intro: r(firstP),
            badges: r(badgeRow),
            docWidth: document.documentElement.scrollWidth,
            viewportWidth: window.innerWidth,
            horizontalScroll: document.documentElement.scrollWidth > window.innerWidth,
        };
    }"""
    )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--url", default="https://github.com/Yash-Awasthi")
    ap.add_argument("--out", default="docs/screenshots/before")
    ap.add_argument("--engine", default="patchright", choices=("patchright", "playwright"))
    args = ap.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    mod = __import__(f"{args.engine}.sync_api", fromlist=["sync_playwright"])
    report = {}

    with mod.sync_playwright() as p:
        browser = p.chromium.launch()
        for width, height in VIEWPORTS:
            for scheme in ("light", "dark"):
                page = browser.new_page(viewport={"width": width, "height": height},
                                        color_scheme=scheme)
                page.goto(args.url, wait_until="domcontentloaded")
                page.wait_for_timeout(3500)  # let the images and the contribution graph settle
                page.screenshot(path=str(out / f"{width}-{scheme}.png"))
                report[f"{width}-{scheme}"] = measure(page)
                page.close()
        browser.close()

    print(json.dumps(report["360-light"], indent=2))
    print(f"wrote {len(VIEWPORTS) * 2} screenshots to {out}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
