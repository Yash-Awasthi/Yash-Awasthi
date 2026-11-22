# Accessibility statement

This page is a GitHub profile README with an illustrated contribution city. What
follows is what has been checked, how, and what has not been checked at all. The
distinction matters: an untested claim of accessibility is just a hope.

## Verified

| What | How it was verified | Where the check lives |
|:--|:--|:--|
| The city has a name and a description | `<title id="ct">` and `<desc id="cd">` are present, state the year, the total and the date range, and `aria-labelledby="ct cd"` points at them | `scripts/check_page.py` → `check_accessible_names()` |
| The description carries the same facts as the visible caption | the caption total must appear in the SVG title, otherwise the check fails | `check_city_encoder()` |
| The drawing says what its geometry means | a legend line inside both SVGs: a tower is one day, its height the contributions of that day, a river a run of quiet weeks | `check_city_encoder()` |
| Badge text stays readable | white on every badge colour is at least 4.5:1 (measured: 5.68, 5.84, 5.36, 4.90) | `check_badge_contrast()` |
| The six green levels survive colour-blindness | simulated deuteranopia, adjacent CIELAB ΔE ≥ 14.7, whole ramp 67–78 | `tests/test_city.py` → `ColourBlindTest` |
| Nothing moves for readers who ask for less motion | `@media (prefers-reduced-motion: reduce)` stops every animation and makes the buildings visible | `tests/test_city.py` → `LegendTest` |
| The page does not scroll sideways on a phone | 360 px viewport: `scrollWidth == innerWidth`, table 278 px inside a 278 px wrapper | measured with Chromium, recorded in `plan.md` (M5.1.4) |
| No placeholder content, no empty links | `check_no_placeholders()` | `scripts/check_page.py` |

## Not verified

- **No screen-reader testing on real devices.** No VoiceOver, TalkBack, NVDA or JAWS
  session has been run against GitHub's rendering of this page. The SVG's accessible
  name is checked in the file, not in a screen reader's output.
- **One browser engine.** Everything measured above was measured in Chromium. Firefox
  and Safari render GitHub's README identically in principle, but `prefers-reduced-motion`
  behaviour inside an `<img>`-embedded SVG has not been checked there.
- **No Windows High Contrast / forced-colors testing.** The city's palette would be
  replaced by the system palette, and nobody has looked at it in that mode.
- **No zoom testing beyond 200 %** or a text-only enlargement pass.
- **The 360 px first screen does not show name, sentence and links together.** GitHub's
  own header takes 506 of the 640 px; the measurements are recorded in `plan.md`
  (M5.1.2) rather than papered over. Nothing in the README can change that.
- **No cognitive-load or plain-language review** beyond keeping the claims one clause.

## Reporting

Open an issue on this repository, or mail the address under the Email badge. An
accessibility problem is treated as a bug, not a preference: the claim about the page
is the same as its behaviour.
