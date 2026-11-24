"""A generated asset must stand on its own: no script, no external references."""
from __future__ import annotations

import re


FORBIDDEN_TAGS = ("<script", "<image", "<foreignobject")


def unsafe_refs(svg):
    """A generated asset must not rely on GitHub's sanitizer: no script, no foreign object, no external href."""
    problems = [f"contains {tag}" for tag in FORBIDDEN_TAGS if tag in svg.lower()]
    problems += [f"external href {m}" for m in re.findall(r'href="(?!\#)[^"]*"', svg)]
    problems += [f"external xlink:href {m}" for m in re.findall(r'xlink:href="(?!\#)[^"]*"', svg)]
    return problems
