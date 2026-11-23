#!/usr/bin/env python3
"""Fail when the public page gains data that must never be published.

Rules live in docs/PRIVACY.md. This script enforces the mechanical part:
no phone number, no street address, no credential-shaped string, in README.md,
in the committed SVG assets, or in the published resume PDF.

    python3 scripts/check_privacy.py            # README + assets
    python3 scripts/check_privacy.py --resume   # also fetch and read the resume PDF

The PDF needs no dependency: text inside it is found by decompressing its
FlateDecode streams and reading the text operators, which is enough to notice a
phone number or a street address.
"""
from __future__ import annotations

import argparse
import re
import sys
import urllib.request
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
ASSETS = ROOT / "assets"
RESUME = "https://yash-portfolio-nine-navy.vercel.app/Yash-Vaibhav-Awasthi-Resume.pdf"

PHONE = [
    re.compile(r"\+91[\s\-()]?\d{5}[\s\-]?\d{5}"),          # +91 XXXXX XXXXX
    re.compile(r"(?<![0-9.])\b[6-9]\d{4}[\s\-]\d{5}\b"),    # Indian mobile, split
    re.compile(r"(?<![0-9.])\b[6-9]\d{9}\b"),               # Indian mobile, unspaced
]
ADDRESS = re.compile(
    r"\b(?:street|lane|colony|apartment|flat\s+no|pin\s?code|pincode|house\s+no|"
    r"sector\s+\d+|plot\s+no|near\s+\w+\s+(?:temple|school|market))\b",
    re.IGNORECASE,
)
SECRETS = [
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}"),
    re.compile(r"\bsk-[A-Za-z0-9]{20,}"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"-----BEGIN (?:[A-Z ]+ )?PRIVATE KEY-----"),
    re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}"),
    re.compile(r"\bsk-gw-[A-Za-z0-9]{10,}"),
]


def scan(label: str, text: str) -> list[str]:
    problems = []
    for rx in PHONE:
        for m in rx.finditer(text):
            problems.append(f"{label}: phone-like value {m.group(0)!r}")
    for m in ADDRESS.finditer(text):
        problems.append(f"{label}: address-like text {m.group(0)!r}")
    for rx in SECRETS:
        for m in rx.finditer(text):
            problems.append(f"{label}: credential-shaped string {m.group(0)[:12]}…")
    return problems


def pdf_text(data: bytes) -> str:
    """Best-effort text from a PDF: decompress each stream and keep the text operators."""
    out = []
    for m in re.finditer(rb"stream\r?\n(.*?)endstream", data, re.S):
        raw = m.group(1)
        try:
            raw = zlib.decompress(raw)
        except zlib.error:
            continue
        for t in re.findall(rb"\((.*?)(?<!\\)\)", raw, re.S):
            out.append(t.decode("latin-1", "replace"))
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--resume", action="store_true", help="also fetch and scan the published resume PDF")
    args = ap.parse_args()

    problems = scan("README.md", README.read_text(encoding="utf-8"))
    for svg in sorted(ASSETS.glob("*.svg")):
        problems += scan(svg.name, svg.read_text(encoding="utf-8"))

    if args.resume:
        try:
            with urllib.request.urlopen(RESUME, timeout=60) as r:  # noqa: S310 - published URL
                data = r.read()
        except Exception as e:  # noqa: BLE001 - any fetch failure is a failure to check
            problems.append(f"resume: could not fetch {RESUME}: {e!r}")
        else:
            text = pdf_text(data)
            if len(text) < 200:
                problems.append(f"resume: extracted only {len(text)} characters of text; check it by hand")
            problems += scan("resume.pdf", text)
            print(f"ok   resume {len(data):,} B, {len(text)} chars of text scanned")

    for p in problems:
        print(f"FAIL {p}")
    print(f"{len(problems)} problem(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
