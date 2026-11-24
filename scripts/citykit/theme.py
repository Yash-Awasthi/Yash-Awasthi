"""Colours, gradients and the per-theme palette for the contribution city."""
from __future__ import annotations


THEMES = {
    "light": {
        "sky": ("#f6f9f7", "#e2ebe6"), "ground": ("#e4ebe7", "#d0dbd5"), "edge": "#b9c7c0", "grass": "#7cc47f", "tuft": "#4f9d57", "leaf": "#4caf50", "trunk": "#7a5a3a",
        "muted": "#6b7a73", "fog": "#eef3f0", "win": "#fffbe6", "win_on": 0.6,
        "water": ("#c4e6f6", "#7cc3e8"), "wave": "#ffffff",
        "levels": ["#9fe3b0", "#5fd47f", "#2bbf62", "#169e4c", "#0e7b3b", "#095c2d"],
    },
    "dark": {
        "sky": ("#0b1324", "#04060b"), "ground": ("#162030", "#0b1018"), "edge": "#04070b", "grass": "#173d24", "tuft": "#2e6b3e", "leaf": "#2e7d42", "trunk": "#4a3524",
        "muted": "#7d8a99", "fog": "#0b1324", "win": "#ffe9a8", "win_on": 0.9,
        "water": ("#15466b", "#0b2640"), "wave": "#6cc0f0",
        "levels": ["#14532d", "#16733b", "#1f9a4e", "#2bc265", "#57e08a", "#a3f5bf"],
    },
}


def rgb(c):
    return [int(c[i:i + 2], 16) for i in (1, 3, 5)]


def mix(c, other, f):
    return "#%02x%02x%02x" % tuple(round(a + (b - a) * f) for a, b in zip(rgb(c), rgb(other)))


def grad(gid, c0, c1):
    return (f'<linearGradient id="{gid}" x1="0" y1="0" x2="0" y2="1">'
            f'<stop offset="0" stop-color="{c0}"/><stop offset="1" stop-color="{c1}"/></linearGradient>')
