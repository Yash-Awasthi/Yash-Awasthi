# Handover

Everything needed to change this profile is in this repository. This page is the
shortest path for someone who has never opened it: what the files are, the four
things you are likely to do, and how to tell you did them right.

## What is where

| File | What it decides |
|:--|:--|
| `projects.json` | every claim, every badge, the stack line, the archive — the single source of the data blocks |
| `README.md` | prose, headings, the banner, the images; the generated blocks between `<!-- kind:start -->` and `<!-- kind:end -->` |
| `now.json` | the "Now:" line (written by `scripts/gen_now.py` from the GitHub API) |
| `assets/city-*.svg` | the contribution city, light and dark (written by `.github/city.py`) |
| `assets/city-stats.json` | the numbers behind the caption under the city |
| `scripts/gen_readme.py` | renders the data into README; `--check` fails on drift |
| `scripts/check_claims.py` | every claim names a file and a line that still says it |
| `scripts/pin_claims.py` | re-derives those line numbers from the code |
| `scripts/check_page.py` | the budgets: size, length, geometry, legend, contrast, review date, hosts |
| `scripts/audit_claims.py` | the quarterly table: number, live link, licence, last commit |
| `scripts/citykit/` | the drawing, split into source, layout, theme, stats, draw, assets, safety |
| `docs/` | [audit](AUDIT.md), [review](REVIEW.md), [runbook](RUNBOOK.md), [accessibility](ACCESSIBILITY.md), [CI](CI.md), [dependencies](DEPENDENCIES.md), [privacy](PRIVACY.md), [changelog](CHANGELOG.md) |

## The four jobs

### Change a claim

1. Edit the sentence in `projects.json` (`projects[].claim`).
2. Point it at evidence: `claim_source: [{file, line, any:[…]}]`. `line` may be
   guessed; `python3 scripts/pin_claims.py --write` corrects it from the code.
3. `python3 scripts/gen_readme.py --write` — never hand-edit a generated block.
4. `python3 scripts/check_claims.py && python3 scripts/check_page.py`.

### Add a project

1. Add an object to `projects` in `projects.json` with `name`, `repo`, `claim`,
   `claim_source` (file + snippets), and `live` if it is deployed.
2. `python3 scripts/pin_claims.py --write && python3 scripts/gen_readme.py --write`.
3. `python3 scripts/check_claims.py --links` — a new live URL has to answer.

### Retire a project

Move the object from `projects` to `archive` in the same file: it renders inside the
collapsed "Earlier work (N)" block and stays audited. Do not delete the evidence —
the archive is checked like the table.

### Refresh the city

```bash
GITHUB_USER=Yash-Awasthi GITHUB_TOKEN=$(gh auth token) python3 .github/city.py
python3 scripts/gen_readme.py --write   # the caption under the image
```

The nightly workflow does both for you; run it by hand only to check a change or to
recover from a red run. Re-rendering twice with the same calendar produces the same
bytes, so a diff means something really changed.

## How to know it worked

```bash
python3 -m unittest discover -s tests
python3 scripts/gen_readme.py --check
python3 scripts/check_claims.py
python3 scripts/pin_claims.py --check
python3 scripts/check_page.py
```

All five must pass. CI runs the same set on every push, so a green workflow is the
same statement made by someone else's machine.

## What is not in this repository

- The projects themselves live in their own repositories; a claim is a link to one
  of them, and `claim_source` points into that repository by path.
- The periodic decisions — retire, soften, licence — are recorded in
  [docs/REVIEW.md](REVIEW.md), not in code.
- A licence for the projects without one is added in those repositories, not here.
