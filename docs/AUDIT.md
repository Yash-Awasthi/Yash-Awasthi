# Claim audit

Every row of the profile's project table is a claim about a repository. These are
the rules that keep those claims true, and the quarterly pass that re-checks them.

## The four checks

| # | check | what answers it | how often |
|---|-------|-----------------|-----------|
| 1 | the claim is still in the repo, on the line it cites | `python3 scripts/check_claims.py` | every push, and quarterly |
| 2 | the live link still answers | `python3 scripts/check_claims.py --links` | every push, and quarterly |
| 3 | the number in the claim still matches the code | `python3 scripts/check_claims.py` (`count` entries) | every push, and quarterly |
| 4 | number, live link, licence, last commit date | `python3 scripts/audit_claims.py --links` | quarterly |

## Quarterly pass

Run these from the repository root, in this order:

```bash
python3 scripts/pin_claims.py --check      # every claim still sits on its pinned line
python3 scripts/check_claims.py --links    # every snippet and every live URL still answers
python3 scripts/audit_claims.py --links --fail-on-stale
```

Then read the table the third command prints and answer for each project:

- **number** — is the count in the claim still the count in the code? A change
  here means `projects.json` and the claim sentence are both edited in one commit.
- **live link** — does it answer `200`? A `no answer` on a free host means the
  demo is asleep or dead; a dead demo is removed from the claim.
- **licence** — `none` means nobody else may legally reuse the code. Either add a
  licence to that repository or stop presenting it as work others can build on.
- **last commit date** — anything older than a year with no live demo is stale.

## When it runs by itself

`.github/workflows/audit.yml` runs the same three commands every quarter
(`0 7 1 */3 *`, and on demand) and fails if a project has no live demo and no push
in the last year. `check.yml` runs the first two on every push, and on its weekly
schedule with `--links`.

## The stale rule

A project with **no live demo** and **no push in 365 days** is either moved to the
archive list in `projects.json` with the date it was retired, or removed from the
profile entirely. `audit_claims.py --fail-on-stale` fails on exactly that
condition, so the quarterly workflow reports it instead of relying on memory.

Archived projects stay in the archive list and keep their `claim_source`, so they
are audited like the live ones — the archive is "earlier work", not "unchecked
work".

## Last pass

- 2026-11-24 — 11 projects (9 live, 2 archived): all pushed within 33 days
  (oldest `2026-10-22`: CaseFiles, Ping, RISC-VInjection, ToolkitArchive),
  no project stale, 0 failures. Notes: five repositories carry no licence
  (AdapFit, CaseFiles, RISC-VInjection, sign-setu, ToolkitArchive), which is
  outside this repository to fix and is recorded in `plan.md` as `needs-verify`.
