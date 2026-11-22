# Runbook

What to do when something breaks. Every entry starts with how you notice it, then
the command that tells you what is wrong, then the fix, then the guard that should
have caught it earlier.

## The nightly city job failed

**Notice:** the "Contrib city" workflow run is red, or `assets/city-*.svg` stop
changing (their provenance comment still names an old commit).

**Diagnose:**

```bash
gh run list --workflow=contrib-city.yml --limit 5
gh run view <run-id> --log-failed
```

**Fix:** run it by hand with the same inputs, and read the one-line reason it prints:

```bash
GITHUB_USER=Yash-Awasthi GITHUB_TOKEN=$(gh auth token) python3 .github/city.py
```

The job writes nothing unless both themes render, so a failed run leaves the
previous day's images in place — a red run means "stale by one day", not "broken
page". If the run failed while committing, pull, then re-run.

**Guard:** `write_assets()` renders both themes before replacing either, and CI
re-renders from a fixture and compares hashes (`tests/test_city.py`).

## The GitHub GraphQL call is rate-limited

**Notice:** the job prints `city.py: GraphQL HTTP 403 … (assets left untouched)` or
`GraphQL HTTP 429`.

**Diagnose:** the token is scoped to one GraphQL point per day of the calendar, so a
limit is almost always a shared or misconfigured token rather than volume.

**Fix:** confirm the token still exists and belongs to the account, then re-run the
workflow; the daily job needs exactly one request. A fine-grained token needs
*read* access to the account's contributions, and the account must be the repository
owner (the calendar is the owner's), otherwise the numbers belong to someone else.

**Guard:** a non-200 or a payload without the expected keys raises `FetchError`, and
the CLI exits 1 with the reason instead of rendering a zero-contribution city.

## An external image host is down

**Notice:** the weekly `links` job fails, or a badge or skill icon renders as a
broken image on the profile.

**Diagnose:**

```bash
python3 scripts/check_links.py
```

It names the URL and the status it got.

**Fix:** three cases.

- **Transient (5xx, timeout):** re-run the job. Nothing else to do.
- **The host is gone:** replace the asset in this repository (`assets/`) and point
  README at the raw URL, then delete the host from `docs/DEPENDENCIES.md`.
- **The host blocks the runner:** if it answers for you but not for CI, the check is
  wrong, not the page — pin the URL's expected behaviour in `scripts/check_links.py`
  with a comment saying why.

**Guard:** `docs/DEPENDENCIES.md` lists every host the page loads from, and
`check_page.py` fails if README grows a host that is not in that list.

## A live demo is offline

**Notice:** `python3 scripts/check_claims.py --links` reports a non-200 for a `live`
URL, or the demo link is dead when clicked.

**Diagnose:** open it in a browser. A free host that sleeps answers in 30–60 s the
first time; anything that never answers is down.

**Fix:** remove the `live` key from that entry in `projects.json`, re-render with
`python3 scripts/gen_readme.py --write`, and commit. The project keeps its row and
its claim; the claim just stops promising a demo. If the demo returns later, add the
key back. A documented cold start (`cold_start: true` + `cold_start_note`) keeps its
120-second exemption; anything else is held to 10 seconds.

**Guard:** the weekly `links` job runs `check_claims.py --links`; the profile's link
text says `Live (cold start)` for the exempted one, so the reader is not surprised by
the wait.

## A claim is disputed

**Notice:** someone says a project does not do what the row says — or you notice it
yourself during a review.

**Diagnose:** go to the pinned line, not to memory:

```bash
python3 scripts/pin_claims.py --check     # the line numbers still match the code
python3 scripts/check_claims.py           # the snippet is still on the pinned line
```

Open the file at the cited line. Either the line still supports the sentence, and the
dispute is about wording — or it does not, and the sentence is wrong.

**Fix:** soften or replace the sentence in `projects.json` **and** re-pin
(`pin_claims.py --write`) if the supporting code moved, then
`gen_readme.py --write`. Claim and evidence change in one commit; never edit README
by hand, because `gen_readme.py --check` will fail on the drift.

**Guard:** every claim carries `claim_source` with a file and a line, and CI fails on
an unpinned or moved line.

## The page guard fails on a budget

**Notice:** `check_page.py` fails on asset size, README length, SVG geometry or a
missing legend.

**Fix:** decide whether the budget or the change is wrong — then change one of them
deliberately and say why in the commit. The budgets are: each SVG under 100 KB, README
under 80 lines, both themes sharing one viewBox, a legend and a
`prefers-reduced-motion` rule in both SVGs, badge contrast at or above 4.5:1.

**Guard:** these are the numbers that stop the page creeping back to ×3 its size.
