#!/usr/bin/env python3
"""The quarterly claim audit: for every project, number, live link, licence, last commit.

    python3 scripts/audit_claims.py                  # print the table
    python3 scripts/audit_claims.py --links          # also fetch every live URL
    python3 scripts/audit_claims.py --fail-on-stale  # exit 1 if any project is dead weight

"Dead weight" is a project with no live demo whose last push is older than
`STALE_DAYS`; the plan's rule is to archive it with the date or drop it. The
script also notes a repository with no licence, because a public project without
one is not reusable by anyone who finds it.

Reads the GitHub REST API (one request per project); set GITHUB_TOKEN to lift the
60-requests-an-hour anonymous limit.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROJECTS = ROOT / "projects.json"
STALE_DAYS = 365


def api(url: str) -> dict | None:
    headers = {"Accept": "application/vnd.github+json"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=20) as r:  # noqa: S310
            return json.load(r)
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError):
        return None


def head_status(url: str, budget: float = 15.0) -> str:
    try:
        with urllib.request.urlopen(urllib.request.Request(url, method="GET",
                                  headers={"User-Agent": "profile-claim-audit"}), timeout=budget) as r:  # noqa: S310
            return str(r.status)
    except urllib.error.HTTPError as e:
        return str(e.code)
    except (urllib.error.URLError, TimeoutError):
        return "no answer"


def age_days(stamp: str, today: date) -> int:
    return (today - datetime.fromisoformat(stamp.replace("Z", "+00:00")).date()).days


def audit(data: dict, check_links: bool) -> tuple[list[str], list[str], list[dict]]:
    """Return (failures, notes, rows) for every project and archived project."""
    today = datetime.now(timezone.utc).date()
    failures, notes, rows = [], [], []
    for p in data["projects"] + data.get("archive", []):
        owner, name = p["repo"].rstrip("/").rsplit("/", 2)[-2:]
        repo = api(f"https://api.github.com/repos/{owner}/{name}")
        if repo is None:
            failures.append(f"{p['name']}: the GitHub API could not describe {owner}/{name}")
            continue
        pushed = repo.get("pushed_at")
        days = age_days(pushed, today) if pushed else None
        licence = (repo.get("license") or {}).get("spdx_id") or "none"
        live = p.get("live") or ""
        row = {"name": p["name"], "claim": p.get("claim", ""), "pushed": pushed[:10] if pushed else "?",
               "age": days, "licence": licence, "live": live, "status": head_status(live) if live and check_links else ""}
        rows.append(row)
        if not live and days is not None and days > STALE_DAYS:
            failures.append(f"{p['name']}: last push {row['pushed']} ({days} days), no live demo — "
                            f"archive it with the date or drop it")
        if licence == "none":
            notes.append(f"{p['name']}: no licence, so nobody else may reuse the code")
        if row["status"] and row["status"] != "200":
            notes.append(f"{p['name']}: {live} answered {row['status']}")
    return failures, notes, rows


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--links", action="store_true", help="also fetch every live URL")
    ap.add_argument("--fail-on-stale", action="store_true", help="exit 1 when a project is stale and undemoed")
    args = ap.parse_args()

    data = json.loads(PROJECTS.read_text(encoding="utf-8"))
    failures, notes, rows = audit(data, args.links)
    width = max(len(r["name"]) for r in rows) if rows else 10
    print(f"{'project'.ljust(width)}  pushed      age  licence      live")
    for r in rows:
        live = r["live"] or "-"
        if r["status"]:
            live = f"{live} ({r['status']})"
        print(f"{r['name'].ljust(width)}  {r['pushed']}  {str(r['age']).rjust(3)}  {r['licence']:<11}  {live}")
    for note in notes:
        print(f"note {note}")
    for failure in failures:
        print(f"FAIL {failure}")
    print(f"{len(rows)} projects audited, {len(notes)} note(s), {len(failures)} stale")
    return 1 if failures and args.fail_on_stale else 0


if __name__ == "__main__":
    sys.exit(main())
