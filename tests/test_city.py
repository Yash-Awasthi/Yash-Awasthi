"""Tests for .github/city.py, run offline: python3 -m unittest discover -s tests

The generator decides whether the committed SVGs are replaced, so its failure
paths are the interesting part: a bad fetch must raise and must not render.
"""
from __future__ import annotations

import importlib.util
import io
import json
import re
import unittest
import urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_city():
    spec = importlib.util.spec_from_file_location("city", ROOT / ".github" / "city.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


city = load_city()
# The generator is a package (scripts/citykit) behind a thin CLI; patch the real call site.
source = importlib.import_module("citykit.source")
assets = importlib.import_module("citykit.assets")


def payload(days):
    """A GraphQL payload whose single week holds `days` as (date, count) pairs."""
    return {"data": {"user": {"contributionsCollection": {"contributionCalendar": {"weeks": [
        {"contributionDays": [{"date": d, "contributionCount": n} for d, n in days]}
    ]}}}}}


class Response(io.BytesIO):
    def __init__(self, body: bytes, status: int = 200):
        super().__init__(body)
        self.status = status


class FakeUrlopen:
    def __init__(self, body: bytes = b"", status: int = 200, error: Exception | None = None):
        self.body, self.status, self.error = body, status, error

    def __call__(self, req, timeout=None):
        if self.error:
            raise self.error
        return Response(self.body, self.status)


class FetchTest(unittest.TestCase):
    def run_fetch(self, **kw):
        real = source.urllib.request.urlopen
        source.urllib.request.urlopen = FakeUrlopen(**kw)
        try:
            return city.fetch("someone", "token")
        finally:
            source.urllib.request.urlopen = real

    def test_http_error_becomes_fetch_error(self):
        err = urllib.error.HTTPError("u", 401, "Unauthorized", {}, None)
        with self.assertRaises(city.FetchError):
            self.run_fetch(error=err)

    def test_network_error_becomes_fetch_error(self):
        with self.assertRaises(city.FetchError):
            self.run_fetch(error=urllib.error.URLError("no route"))

    def test_non_200_becomes_fetch_error(self):
        with self.assertRaises(city.FetchError):
            self.run_fetch(body=json.dumps(payload([("2026-11-01", 3)])).encode(), status=502)

    def test_graphql_errors_become_fetch_error(self):
        body = json.dumps({"errors": [{"message": "rate limited"}], "data": None}).encode()
        with self.assertRaises(city.FetchError):
            self.run_fetch(body=body)

    def test_empty_calendar_becomes_fetch_error(self):
        with self.assertRaises(city.FetchError):
            self.run_fetch(body=json.dumps(payload([("2026-11-01", 0)])).encode())

    def test_a_sha256_digest_of_nothing_is_not_rendered(self):
        with self.assertRaises(city.FetchError):
            city.parse_calendar({"data": {"user": None}})

    def test_valid_payload_is_parsed(self):
        weeks = self.run_fetch(body=json.dumps(payload([("2026-11-01", 3)])).encode())
        self.assertEqual(weeks, [[("2026-11-01", 3)]])


class WriteTest(unittest.TestCase):
    WEEKS = [[("2026-11-0%d" % (d + 1), d) for d in range(7)]]

    def setUp(self):
        import tempfile
        self.dir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.dir, ignore_errors=True)

    def test_both_themes_are_written(self):
        written = city.write_assets(self.WEEKS, self.dir)
        names = sorted(p.name for p in Path(self.dir).iterdir())
        self.assertEqual(names, ["city-dark.svg", "city-light.svg", "city-stats.json"])
        self.assertEqual(len(written), 3)  # two SVGs plus the facts the caption is rendered from

    def test_a_render_crash_leaves_the_previous_assets_untouched(self):
        city.write_assets(self.WEEKS, self.dir)
        before = {p.name: p.read_bytes() for p in Path(self.dir).iterdir()}
        real_render, calls = assets.render, []

        def render_then_fail(weeks, theme, *rest):
            calls.append(theme)
            if len(calls) == 2:
                raise RuntimeError("theme 2 exploded")
            return real_render(weeks, theme)

        assets.render = render_then_fail
        try:
            with self.assertRaises(RuntimeError):
                city.write_assets(self.WEEKS, self.dir)
        finally:
            assets.render = real_render
        after = {p.name: p.read_bytes() for p in Path(self.dir).iterdir()}
        self.assertEqual(before, after, "a failed render must not replace either theme")

    def test_no_temp_files_are_left_behind(self):
        city.write_assets(self.WEEKS, self.dir)
        self.assertFalse([p for p in Path(self.dir).iterdir() if p.name.startswith(".city-")])


class SummaryTest(unittest.TestCase):
    def test_summary_names_total_and_range(self):
        weeks = [[("2026-11-01", 2), ("2026-11-02", 0)], [("2026-11-03", 5)]]
        self.assertEqual(city.summary(weeks),
                         "7 contributions, 2026-11-01 to 2026-11-03, 2 weeks")


class YearAndCliTest(unittest.TestCase):
    WEEKS = [[("2025-12-30", 1), ("2026-01-01", 4)], [("2026-01-04", 2)]]

    def test_filter_year_drops_other_years(self):
        self.assertEqual(city.filter_year(self.WEEKS, 2026),
                         [[("2026-01-01", 4)], [("2026-01-04", 2)]])

    def test_filter_year_refuses_a_year_with_nothing_in_it(self):
        with self.assertRaises(city.FetchError):
            city.filter_year(self.WEEKS, 2024)

    def test_cli_offers_year_and_out(self):
        import subprocess, sys
        out = subprocess.run([sys.executable, str(ROOT / ".github" / "city.py"), "--help"],
                             capture_output=True, text=True, check=True)
        self.assertIn("--year", out.stdout)
        self.assertIn("--out", out.stdout)
        self.assertIn("$GITHUB_USER", out.stdout)  # the positional user's default


class DeterminismTest(unittest.TestCase):
    """The same calendar must always produce the same bytes, in this process and any other."""

    WEEKS = [[("2026-11-%02d" % (d + 1), (d * 3) % 7) for d in range(7)],
             [("2026-11-%02d" % (d + 8), 0 if d % 2 else d) for d in range(7)],
             [("2026-11-%02d" % (d + 15), d * 2) for d in range(7)]]

    def test_two_renders_are_byte_identical(self):
        for theme in city.THEMES:
            self.assertEqual(city.render(self.WEEKS, theme), city.render(self.WEEKS, theme), theme)

    def test_a_separate_process_agrees_under_another_hash_seed(self):
        import hashlib, json, os, subprocess, sys, tempfile
        digest = []
        for seed in ("0", "12345"):
            with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fh:
                json.dump(self.WEEKS, fh)
                path = fh.name
            code = (
                "import hashlib, importlib.util, json, sys;"
                f"spec=importlib.util.spec_from_file_location('city', {str(ROOT / '.github' / 'city.py')!r});"
                "m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);"
                f"weeks=json.load(open({path!r}));"
                "print(hashlib.sha256(''.join(m.render(weeks,t) for t in m.THEMES).encode()).hexdigest())"
            )
            env = dict(os.environ, PYTHONHASHSEED=seed)
            out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, env=env, check=True)
            digest.append(out.stdout.strip())
            os.unlink(path)
        self.assertEqual(digest[0], digest[1])
        self.assertEqual(len(digest[0]), 64)


FIXTURE = ROOT / "tests" / "fixtures" / "calendar.json"
GOLDEN = ROOT / "tests" / "fixtures" / "golden.json"


class FixtureTest(unittest.TestCase):
    """The generator must render from a committed payload, without the network."""

    def setUp(self):
        self.payload = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def test_fixture_parses_into_weeks(self):
        weeks = city.parse_calendar(self.payload)
        self.assertEqual(len(weeks), 53)
        self.assertEqual(weeks[0][0][0], "2025-11-23")
        self.assertGreater(sum(n for w in weeks for _, n in w), 0)

    def test_both_themes_render_from_the_fixture(self):
        weeks = city.parse_calendar(self.payload)
        for theme in city.THEMES:
            svg = city.render(weeks, theme)
            self.assertTrue(svg.startswith("<svg"))
            self.assertTrue(svg.rstrip().endswith("</svg>"))


class GoldenTest(unittest.TestCase):
    """A pixel change from the committed fixture has to be an intentional commit."""

    def test_fixture_render_matches_the_committed_hash(self):
        import hashlib, os
        weeks = city.parse_calendar(json.loads(FIXTURE.read_text(encoding="utf-8")))
        actual = {theme: hashlib.sha256(city.render(weeks, theme).encode()).hexdigest()
                  for theme in city.THEMES}
        if os.environ.get("UPDATE_GOLDEN") == "1":
            GOLDEN.write_text(json.dumps(actual, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        stored = json.loads(GOLDEN.read_text(encoding="utf-8"))
        self.assertEqual(actual, stored,
                         "rendered output changed; rerun with UPDATE_GOLDEN=1 only if that is intended")


class SafetyTest(unittest.TestCase):
    """The asset is generated, but it must still be inert on its own."""

    def test_fixture_output_holds_nothing_active(self):
        weeks = city.parse_calendar(json.loads(FIXTURE.read_text(encoding="utf-8")))
        for theme in city.THEMES:
            self.assertEqual(city.unsafe_refs(city.render(weeks, theme)), [], theme)

    def test_the_scanner_catches_what_it_claims_to(self):
        self.assertTrue(city.unsafe_refs('<svg><script>alert(1)</script></svg>'))
        self.assertTrue(city.unsafe_refs('<svg><image href="https://x/y.png"/></svg>'))
        self.assertTrue(city.unsafe_refs('<svg><foreignObject></foreignObject></svg>'))
        self.assertTrue(city.unsafe_refs('<svg><use href="https://x/y.svg#a"/></svg>'))
        self.assertEqual(city.unsafe_refs('<svg><rect fill="url(#sky)"/></svg>'), [])


class AccessibleNameTest(unittest.TestCase):
    """A screen reader must hear the year and the total, not "image" (M3.2.2)."""

    def setUp(self):
        self.weeks = city.parse_calendar(json.loads(FIXTURE.read_text(encoding="utf-8")))
        self.total = sum(n for w in self.weeks for _, n in w)

    def test_each_theme_states_year_dates_and_total(self):
        for theme in city.THEMES:
            svg = city.render(self.weeks, theme)
            title = re.search(r"<title[^>]*>([^<]*)</title>", svg).group(1)
            desc = re.search(r"<desc[^>]*>([^<]*)</desc>", svg).group(1)
            self.assertIn(f"{self.total:,} contributions", title)
            first = self.weeks[0][0][0]
            last = self.weeks[-1][-1][0]
            self.assertIn(f"{first} to {last}", desc)

    def test_both_themes_declare_the_same_total(self):
        totals = {theme: re.search(r"([\d,]+) contributions", city.render(self.weeks, theme)).group(1)
                  for theme in city.THEMES}
        self.assertEqual(len(set(totals.values())), 1, totals)

    def test_the_svg_points_at_its_own_title_and_desc(self):
        svg = city.render(self.weeks, "dark")
        self.assertIn('aria-labelledby="ct cd"', svg)
        self.assertIn('id="ct"', svg)
        self.assertIn('id="cd"', svg)


if __name__ == "__main__":
    unittest.main()

class LegendTest(unittest.TestCase):
    """The drawing has to say what its geometry means, and to stop when asked (M5.2)."""

    def test_both_themes_state_what_a_tower_means(self):
        for theme in ("light", "dark"):
            svg = city.render([[("2026-11-01", 3), ("2026-11-02", 0)]], theme)
            self.assertIn("Each tower is one day", svg)
            self.assertIn("each river a run of quiet weeks", svg)

    def test_the_legend_sits_inside_the_viewbox(self):
        svg = city.render([[("2026-11-01", 3)]], "light")
        height = float(re.search(r'viewBox="0 0 [\d.]+ ([\d.]+)"', svg).group(1))
        legend_y = float(re.search(r'<text x="28" y="([\d.]+)"[^>]*>Each tower', svg).group(1))
        self.assertLess(legend_y, height)
        self.assertGreater(legend_y, height - 40)

    def test_animation_stops_for_reduced_motion(self):
        svg = city.render([[("2026-11-01", 3)]], "dark")
        self.assertIn("@media (prefers-reduced-motion:reduce)", svg)
        # Buildings start hidden and rise; the override must also restore them, or they stay invisible.
        reduced = svg.split("@media (prefers-reduced-motion:reduce)", 1)[1].split("</style>", 1)[0]
        self.assertIn(".b,.f{opacity:1!important;transform:none!important}", reduced)

    def test_the_description_carries_the_same_facts_as_the_caption(self):
        weeks = [[("2026-11-01", 3), ("2026-11-02", 0), ("2026-11-03", 5)]]
        stats = city.stats(weeks)
        self.assertEqual(stats["total"], 8)
        self.assertEqual(stats["streak"], 1)
        self.assertIn(city.caption(stats), city.render(weeks, "light"))


class StatsTest(unittest.TestCase):
    def test_a_streak_counts_consecutive_active_days(self):
        weeks = [[("2026-11-01", 1), ("2026-11-02", 2), ("2026-11-03", 0),
                  ("2026-11-04", 4), ("2026-11-05", 5), ("2026-11-06", 6)]]
        self.assertEqual(city.stats(weeks)["streak"], 3)
        self.assertEqual(city.stats(weeks)["streak_end"], "2026-11-06")

    def test_the_busiest_month_is_the_tallest_total(self):
        weeks = [[("2026-10-30", 40), ("2026-10-31", 5), ("2026-11-01", 7)]]
        stats = city.stats(weeks)
        self.assertEqual(stats["best_month"], "2026-10")
        self.assertEqual(stats["best_month_count"], 45)

    def test_the_caption_names_the_month_not_its_number(self):
        weeks = [[("2026-05-01", 3)]]
        self.assertIn("May 2026", city.caption(city.stats(weeks)))

    def test_writing_the_assets_also_writes_the_facts(self):
        import tempfile
        weeks = [[("2026-11-01", 3)]]
        with tempfile.TemporaryDirectory() as d:
            city.write_assets(weeks, d)
            facts = json.loads((Path(d) / "city-stats.json").read_text(encoding="utf-8"))
        self.assertEqual(facts["total"], 3)
        self.assertIn("3 contributions", facts["caption"])


class ColourBlindTest(unittest.TestCase):
    """Six levels of green must stay tellable apart without green cones (M5.2)."""

    @staticmethod
    def _lms(rgb):
        def lin(c):
            c /= 255
            return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
        r, g, b = (lin(x) for x in rgb)
        return (0.31399022 * r + 0.63951294 * g + 0.04649755 * b,
                0.15537241 * r + 0.75789446 * g + 0.08670142 * b,
                0.01775239 * r + 0.10944209 * g + 0.87256922 * b)

    @classmethod
    def deuteranope(cls, rgb):
        L, M, S = cls._lms(rgb)
        L2 = 2.02344 * M - 2.52581 * S
        r = 5.47221206 * L2 - 4.6419601 * M + 0.16963708 * S
        g = -1.1252419 * L2 + 2.29317094 * M - 0.1678952 * S
        b = 0.02980165 * L2 - 0.19318073 * M + 1.16364789 * S
        return [max(0.0, min(1.0, v)) for v in (r, g, b)]

    @classmethod
    def delta_e(cls, a, b):
        import math

        def lab(v):
            r, g, bl = (v[0], v[1], v[2])
            def f(t):
                return t ** (1 / 3) if t > 0.008856 else 7.787 * t + 16 / 116
            X = 0.4124564 * r + 0.3575761 * g + 0.1804375 * bl
            Y = 0.2126729 * r + 0.7151522 * g + 0.0721750 * bl
            Z = 0.0193339 * r + 0.1191920 * g + 0.9503041 * bl
            fx, fy, fz = f(X / 0.95047), f(Y), f(Z / 1.08883)
            return (116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz))
        return math.dist(lab(a), lab(b))

    def test_adjacent_levels_stay_apart_without_red_green_vision(self):
        from citykit.theme import THEMES
        for scheme, theme in THEMES.items():
            levels = [[int(c[i:i + 2], 16) for i in (1, 3, 5)] for c in theme["levels"]]
            sim = [self.deuteranope(v) for v in levels]
            for i in range(len(sim) - 1):
                with self.subTest(theme=scheme, pair=(theme["levels"][i], theme["levels"][i + 1])):
                    self.assertGreater(self.delta_e(sim[i], sim[i + 1]), 10,
                                       "levels become indistinguishable for deuteranopes")
            self.assertGreater(self.delta_e(sim[0], sim[-1]), 40)

class ProvenanceTest(unittest.TestCase):
    """A stale image has to identify its own generator, data range and commit (M6.1.2)."""

    WEEKS = [[("2026-11-01", 3), ("2026-11-02", 0)]]

    def test_the_comment_names_version_data_and_commit(self):
        svg = city.render(self.WEEKS, "light", "citykit 1.0.0 · data 2026-11-01..2026-11-02 · commit abc1234")
        self.assertIn("<!-- citykit 1.0.0 · data 2026-11-01..2026-11-02 · commit abc1234 -->", svg)

    def test_the_version_number_survives_the_numeric_cleanup(self):
        svg = city.render(self.WEEKS, "light", "citykit 1.0.0 · data 2026-11-01..2026-11-02 · commit abc1234")
        self.assertIn("citykit 1.0.0", svg)
        self.assertNotIn("citykit 1 ·", svg)

    def test_without_provenance_there_is_no_comment(self):
        self.assertNotIn("citykit", city.render(self.WEEKS, "light"))

    def test_the_committed_assets_carry_provenance(self):
        for svg in sorted((ROOT / "assets").glob("city-*.svg")):
            self.assertIn("<!-- citykit ", svg.read_text(encoding="utf-8"), svg.name)

    def test_the_cli_reports_the_commit(self):
        self.assertRegex(city.commit_sha(), r"^([0-9a-f]{7}|unknown)$")
