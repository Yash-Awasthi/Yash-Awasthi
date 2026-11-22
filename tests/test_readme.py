"""Tests for scripts/gen_readme.py: the table is data, and README.md must match it."""
from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_gen():
    spec = importlib.util.spec_from_file_location("gen_readme", ROOT / "scripts" / "gen_readme.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


gen = load_gen()


class TableTest(unittest.TestCase):
    def setUp(self):
        self.data = gen.load()

    def test_every_project_gets_one_row(self):
        table = gen.render_table(self.data["projects"])
        rows = [ln for ln in table.splitlines()[2:] if ln.startswith("|")]
        self.assertEqual(len(rows), len(self.data["projects"]))
        for p in self.data["projects"]:
            self.assertIn(f"[**{p['name']}**]({p['repo']})", table)

    def test_a_cold_start_is_named_in_the_link(self):
        table = gen.render_table([
            {"name": "A", "repo": "https://github.com/o/A", "claim": "x", "live": "https://a.example",
             "cold_start": True},
            {"name": "B", "repo": "https://github.com/o/B", "claim": "y", "live": "https://b.example"},
        ])
        self.assertIn("[Live (cold start)](https://a.example)", table)
        self.assertIn("[Live](https://b.example)", table)

    def test_a_live_url_becomes_a_link(self):
        table = gen.render_table([
            {"name": "X", "repo": "https://github.com/o/X", "claim": "does things", "live": "https://x.example"},
            {"name": "Y", "repo": "https://github.com/o/Y", "claim": "does other things"},
        ])
        self.assertIn("[Live](https://x.example)", table)
        self.assertEqual(table.count("[Live]"), 1)

    def test_readme_is_in_sync_with_the_data(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        now = json.loads((ROOT / "now.json").read_text(encoding="utf-8"))
        city = json.loads((ROOT / "assets" / "city-stats.json").read_text(encoding="utf-8"))
        self.assertEqual(readme, gen.render_readme(readme, self.data, now, city))

    def test_a_missing_marker_block_is_an_error_not_a_rewrite(self):
        with self.assertRaises(SystemExit):
            gen.replace_block("# no block here\n", "projects", "x")


class ArchiveTest(unittest.TestCase):
    def setUp(self):
        self.data = gen.load()

    def test_the_archive_is_collapsed_and_counts_itself(self):
        block = gen.render_archive(self.data["archive"])
        self.assertTrue(block.startswith("<details>"))
        self.assertIn(f"<summary>Earlier work ({len(self.data['archive'])})</summary>", block)
        self.assertTrue(block.endswith("</details>"))
        for a in self.data["archive"]:
            self.assertIn(f"[**{a['name']}**]({a['repo']})", block)

    def test_no_archive_renders_nothing_at_all(self):
        self.assertEqual(gen.render_archive([]), "")

    def test_the_stack_line_comes_from_the_data(self):
        self.assertEqual(gen.render_stack(["A", "B"]), "**Stack:** A · B")
        self.assertIn(self.data["stack"][0], gen.render_stack(self.data["stack"]))


class BadgeTest(unittest.TestCase):
    def setUp(self):
        self.data = gen.load()

    def test_every_link_gets_one_badge_with_its_alt_and_url(self):
        row = gen.render_badges(self.data["profile"]["links"])
        for link in self.data["profile"]["links"]:
            self.assertIn(f"[![{link['alt']}]", row)
            self.assertIn(f"]({link['url']})", row)
        self.assertEqual(row.count("[!["), len(self.data["profile"]["links"]))

    def test_appearance_parameters_are_pinned(self):
        row = gen.render_badges(self.data["profile"]["links"])
        for fragment in ("style=flat-square", "logoColor=white", "labelColor=555"):
            self.assertEqual(row.count(fragment), len(self.data["profile"]["links"]), fragment)

    def test_a_changed_link_changes_the_row(self):
        links = [{"label": "A", "url": "https://a.example", "alt": "A — a.example",
                  "color": "000000", "logo": "github"}]
        self.assertIn("https://a.example", gen.render_badges(links))
        self.assertIn("badge/A-000000", gen.render_badges(links))


class CityCaptionTest(unittest.TestCase):
    """The one line under the city image restates what the drawing encodes (M5.2)."""

    CITY = {"caption": "3,573 contributions on 82 active days, 2025-11-23 to 2026-11-24"}

    def test_the_caption_is_rendered_under_the_image(self):
        readme = "# x\n<!-- city:start -->\n<!-- city:end -->\n"
        self.assertIn(self.CITY["caption"], gen.replace_block(readme, "city", gen.render_city(self.CITY)))

    def test_a_caption_drift_is_caught(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        stale = dict(self.CITY, caption=self.CITY["caption"].replace("3,573", "3,574"))
        self.assertNotEqual(readme, gen.replace_block(readme, "city", gen.render_city(stale)))


if __name__ == "__main__":
    unittest.main()
