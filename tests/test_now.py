"""Tests for scripts/gen_now.py and the "Now" block gen_readme.py renders from it."""
from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


now_mod = load("gen_now")
readme = load("gen_readme")


def city_stats():
    """The facts block the README's city caption is rendered from."""
    return json.loads((ROOT / "assets" / "city-stats.json").read_text(encoding="utf-8"))

REPOS = [
    {"name": "Yash-Awasthi", "html_url": "https://github.com/Yash-Awasthi/Yash-Awasthi",
     "description": "GitHub Profile README", "pushed_at": "2026-11-24T06:00:00Z", "fork": False},
    {"name": "ResBackup", "html_url": "https://github.com/Yash-Awasthi/ResBackup",
     "description": "", "pushed_at": "2026-11-24T05:00:00Z", "fork": False},
    {"name": "FinScrape", "html_url": "https://github.com/Yash-Awasthi/FinScrape",
     "description": "FinScrape: see what moves markets.", "pushed_at": "2026-11-23T09:00:00Z",
     "fork": False, "language": "Python"},
    {"name": "forked", "html_url": "https://github.com/x/forked", "description": "not mine",
     "pushed_at": "2026-11-25T09:00:00Z", "fork": True},
]


class PickTest(unittest.TestCase):
    def test_the_profile_repo_and_forks_are_never_picked(self):
        self.assertEqual(now_mod.pick(REPOS, "Yash-Awasthi")["name"], "ResBackup")

    def test_an_empty_list_is_an_error_not_an_empty_section(self):
        with self.assertRaises(SystemExit):
            now_mod.pick([REPOS[0]], "Yash-Awasthi")

    def test_the_record_keeps_only_the_fields_the_page_uses(self):
        rec = now_mod.record(REPOS[2], "Yash-Awasthi", "2026-11-24")
        self.assertEqual(rec["pushed_at"], "2026-11-23")  # the date, not the timestamp
        self.assertEqual(rec["language"], "Python")
        self.assertEqual(set(rec), {"user", "repo", "url", "description", "language",
                                   "pushed_at", "fetched_at"})


class RenderTest(unittest.TestCase):
    NOW = {"repo": "FinScrape", "url": "https://github.com/Yash-Awasthi/FinScrape",
           "description": "FinScrape: see what moves markets.", "pushed_at": "2026-11-23"}

    def test_the_line_names_the_repo_the_link_and_the_push_date(self):
        line = readme.render_now(self.NOW)
        self.assertTrue(line.startswith("**Now:** [**FinScrape**](https://github.com/Yash-Awasthi/FinScrape)"))
        self.assertIn("Last push 2026-11-23.", line)
        self.assertNotIn("FinScrape: see", line, "the repo name must not be repeated")

    def test_a_missing_description_still_renders_one_line(self):
        line = readme.render_now({**self.NOW, "description": ""})
        self.assertIn("Last push 2026-11-23.", line)
        self.assertNotIn("None", line)

    def test_a_long_description_is_trimmed(self):
        line = readme.render_now({**self.NOW, "description": "word " * 80 + "."})
        self.assertLess(len(line), readme.NOW_DESCRIPTION_CHARS + 120)

    def test_the_committed_now_json_is_what_the_readme_shows(self):
        data = readme.load()
        now = json.loads((ROOT / "now.json").read_text(encoding="utf-8"))
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertEqual(text, readme.render_readme(text, data, now, city_stats()))


if __name__ == "__main__":
    unittest.main()
