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
        self.assertEqual(readme, gen.render_readme(readme, self.data, now))

    def test_a_missing_marker_block_is_an_error_not_a_rewrite(self):
        with self.assertRaises(SystemExit):
            gen.replace_block("# no block here\n", "projects", "x")


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


if __name__ == "__main__":
    unittest.main()
