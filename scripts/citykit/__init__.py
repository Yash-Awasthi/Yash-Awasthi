"""The contribution city generator, split so each part can be read on its own.

source.py fetches and validates the calendar, layout.py turns weeks into columns,
theme.py holds the palettes, stats.py states the facts the drawing encodes, draw.py writes
the SVG, assets.py swaps the files in.
"""
__version__ = "1.0.0"  # the generator's own version; see docs/CHANGELOG.md

from .assets import summary, write_assets
from .draw import render
from .layout import layout
from .safety import unsafe_refs
from .source import FetchError, fetch, filter_year, parse_calendar
from .stats import caption, stats
from .theme import THEMES

__all__ = ["THEMES", "__version__", "FetchError", "caption", "fetch", "filter_year", "layout",
           "parse_calendar", "render", "stats", "summary", "unsafe_refs", "write_assets"]
