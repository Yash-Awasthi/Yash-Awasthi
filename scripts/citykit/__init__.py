"""The contribution city generator, split so each part can be read on its own.

source.py fetches and validates the calendar, layout.py turns weeks into columns,
theme.py holds the palettes, draw.py writes the SVG, assets.py swaps the files in.
"""
from .assets import summary, write_assets
from .draw import render
from .layout import layout
from .safety import unsafe_refs
from .source import FetchError, fetch, filter_year, parse_calendar
from .theme import THEMES

__all__ = ["THEMES", "FetchError", "fetch", "filter_year", "layout",
           "parse_calendar", "render", "summary", "unsafe_refs", "write_assets"]
