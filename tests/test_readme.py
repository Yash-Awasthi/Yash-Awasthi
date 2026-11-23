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
        self.assertEqual(readme, gen.replace_block(readme, gen.render_block(self.data)))

    def test_a_missing_marker_block_is_an_error_not_a_rewrite(self):
        with self.assertRaises(SystemExit):
            gen.replace_block("# no block here\n", "x")


if __name__ == "__main__":
    unittest.main()
