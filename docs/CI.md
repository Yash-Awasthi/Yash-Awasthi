# CI toolchain

Everything the workflows run is pinned. A runner image update must not be able to
change what CI checks, and a floating `python3` or `node` is exactly that risk.

## Pinned versions

| Tool | Pinned to | Where |
|:--|:--|:--|
| Python | `3.14.8` | `.github/workflows/check.yml`, `.github/workflows/contrib-city.yml`, `.github/workflows/audit.yml` (`actions/setup-python`) |
| Node | `24.22.3` | `.github/workflows/check.yml` (`actions/setup-node`) |
| markdownlint-cli2 | `0.16.0` | `npx --yes markdownlint-cli2@0.16.0` in the *Markdown lint* step |

The Python version is the one this repository is developed against; every script
and test in `scripts/` and `tests/` runs under it locally before it runs in CI.

## Pinned actions

| Action | SHA | Version |
|:--|:--|:--|
| `actions/checkout` | `11d5960a326750d5838078e36cf38b85af677262` | v4.4.0 |
| `actions/setup-python` | `6d4fd22b20465ccc0f7354476588e8df7c9ca0e0` | v7.1.0 |
| `actions/setup-node` | `949feb2413d6458794dcd2491c4babbbce0c15c1` | v7.1.0 |

A tag is a moving target; a commit SHA is not. To bump one, resolve the tag to a
commit and keep the version in the comment:

```sh
curl -s https://api.github.com/repos/actions/setup-python/git/ref/tags/v7.1.0
```

## Schedules

| Workflow | Cron (UTC) | Why that time |
|:--|:--|:--|
| `contrib-city.yml` | `30 2 * * *` | The previous UTC day's contribution count is final hours before this; a midnight run races the day boundary. |
| `check.yml` | `0 6 * * 1` | The network-heavy checks (URLs, live demos, the published PDF) run weekly, not on every push. |
| `audit.yml` | `0 7 1 */3 *` | The [claim audit](AUDIT.md) is a quarterly read: number, live link, licence, last commit date. Quarterly, because a project does not go stale overnight and a weekly report becomes noise. |

`contrib-city.yml` also takes a manual run with an optional `year` input, which the
job passes on as `--year`, so a past year can be re-rendered without editing the
workflow.

needs-verify: the exact moment GitHub finalises a day's contribution count is not
published; `02:30 UTC` is a margin, not a measurement. A run that lands early still
renders a valid city, and the commit step skips when the SVGs are byte-identical.

## Running the same checks locally

```sh
python3 -m unittest discover -s tests
python3 scripts/check_claims.py            # add --links to fetch every live URL
python3 scripts/gen_readme.py --check
python3 scripts/check_page.py
python3 scripts/check_privacy.py
npx --yes markdownlint-cli2@0.16.0 "README.md" "SECURITY.md" "docs/*.md"
```
