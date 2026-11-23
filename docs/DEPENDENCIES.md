# Third-party dependencies of the profile page

Measured from `README.md`: **10 hosts, 23 URLs** — 4 serve images, 6 are link
destinations. `python3 -c` host count is reproducible with the snippet at the
bottom. Anything listed here that dies changes what a reader sees; nothing else
does.

## Image hosts — the page looks wrong when these fail

| Host | Serves | If it is down | Mitigation in the README |
|---|---|---|---|
| `capsule-render.vercel.app` | The waving gradient banner (1 URL) | Banner is missing; a broken-image placeholder shows | Banner is decorative (`alt="Gradient banner"`); the name and tagline directly under it are real text (`# Yash Vaibhav Awasthi`), so the page still reads. Self-hosting it as a static SVG is m2.3.3. |
| `img.shields.io` | 4 badges (Portfolio, LinkedIn, Resume, Email) | The four links lose their coloured badges, so nothing clickable remains in their place | Each badge's `alt` names its destination (m1.2.1); the destinations are also plain URLs in this repo's history and in the resume. |
| `skillicons.dev` | The 14-icon stack strip (1 URL) | Icons vanish, leaving a gap | The stack is written out as text in the same section (`**Stack:** TypeScript · … · Three.js`), and the strip is decorative (`alt=""`). |
| `raw.githubusercontent.com` | `city-dark.svg`, `city-light.svg` (2 URLs) | The contribution city is missing | The underlying numbers are still readable in the GitHub contribution graph on the profile; the asset is generated here and can be re-pointed at `github.com/…/blob/…` or a relative path if this repo changes its default branch. |

## Link hosts — only the click fails

| Host | Serves | If it is down |
|---|---|---|
| `github.com` | 9 project and profile links | Every project link fails to load on GitHub's side; nothing this repo can fix, and CI's link check goes red. |
| `yash-portfolio-nine-navy.vercel.app` | Portfolio (2 URLs: site and resume PDF) | Portfolio and the resume both unavailable; the PDF is the only resume source, so this is the highest-impact link. |
| `www.linkedin.com` | LinkedIn profile | Profile unreachable. Answers `999` to non-browser clients, so CI reports it as `blocked`, not as a failure. |
| `nexus-iosc.onrender.com` | Nexus live demo | Demo offline. Render's free tier cold-starts: measured **45.8 s** to first byte on 2026-11-23. |
| `winfin.pages.dev` | FinScrape live demo | Demo offline (Cloudflare Pages). |
| `yash-awasthi.github.io` | LobIQ sample reports | Reports offline (GitHub Pages, built by LobIQ's own CI). |

## Rules

1. A new external host is a new dependency: add it to this table in the same commit.
2. `scripts/check_page.py` fails when `README.md` points at a host this file does not name.
3. Image URLs keep every visual parameter explicit (`theme`, `perline`, `height`,
   `fontSize`, `style`, `logo`, colours), so an upstream default change cannot
   silently restyle the page.
4. A host whose terms forbid hotlinking gets replaced, not documented.

## Counting the hosts

```bash
python3 -c "import re;from urllib.parse import urlparse;t=open('README.md').read();u=re.findall(r'(?:href|src)=\"(https?://[^\"]+)\"',t)+re.findall(r'srcset=\"(https?://[^\"]+)\"',t)+re.findall(r'\]\((https?://[^)]+)\)',t);print(len(set(urlparse(x).netloc for x in u)),'hosts',len(u),'urls')"
```
