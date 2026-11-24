"""Write both themes atomically, and describe what was rendered."""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

from .draw import render
from .theme import THEMES


def summary(weeks):
    """One line for the job log: how much was rendered, over which days."""
    days = [d for w in weeks for d, _ in w]
    total = sum(n for w in weeks for _, n in w)
    return f"{total} contributions, {min(days)} to {max(days)}, {len(weeks)} weeks"


def write_assets(weeks, out_dir="assets"):
    """Render both themes first, then swap both files in, so neither theme can go stale."""
    rendered = {theme: render(weeks, theme) for theme in THEMES}
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    staged = []
    try:
        for theme, svg in rendered.items():
            fd, tmp = tempfile.mkstemp(dir=out, prefix=f".city-{theme}-", suffix=".svg")
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(svg)
            staged.append((tmp, out / f"city-{theme}.svg"))
        for tmp, final in staged:
            os.replace(tmp, final)
    finally:
        for tmp, _ in staged:
            if os.path.exists(tmp):
                os.unlink(tmp)
    return [final for _, final in staged]
