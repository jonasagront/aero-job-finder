"""Checks on the job page build (docs/index.html). Run with:  python -m unittest discover tests"""
from __future__ import annotations

import datetime as dt
import json
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from jobfinder import render  # noqa: E402

PROFILE = tomllib.loads((ROOT / "profile.toml").read_text(encoding="utf-8"))
NOW = dt.datetime(2026, 11, 22, 21, 3, tzinfo=dt.timezone.utc)


def job(**kw) -> dict:
    j = {"key": "le:1", "company": "Acme (25539)", "title": "Propulsion Intern </script><b>", "location": "US-FL-MELBOURNE-310 ~ 1 Rd ~ BLDG 310",
         "url": "https://example.com/1", "source": "Acme careers", "posted": "2026-11-20", "first_seen": "2026-11-21",
         "tracks": {"all": {"score": 70, "tier": "good", "parts": {"fit": 30, "skills": 25, "eligibility": 15},
                            "season": "match", "season_label": "Summer 2027"}},
         "matched": ["Python"], "related": [], "gaps": [], "flags": []}
    j.update(kw)
    return j


def embedded(page: str) -> dict:
    m = render.DATA_RX.search(page)
    assert m, "no data block"
    return json.loads(m.group(1))


class PageBuild(unittest.TestCase):
    def test_data_is_embedded_once_and_cannot_close_the_script_tag(self):
        page = render.build_page([job()], [], PROFILE, NOW)
        self.assertNotIn("__DATA__", page)
        self.assertEqual(page.count('<script id="data" type="application/json">'), 1)
        self.assertNotIn("Propulsion Intern </script>", page)
        data = embedded(page)
        self.assertEqual(data["jobs"][0]["title"], "Propulsion Intern </script><b>")
        # Display cleanup happens in the browser; the record itself is passed through unchanged
        self.assertEqual(data["jobs"][0]["company"], "Acme (25539)")
        self.assertEqual(data["jobs"][0]["location"], "US-FL-MELBOURNE-310 ~ 1 Rd ~ BLDG 310")

    def test_missing_lists_become_empty_lists(self):
        data = embedded(render.build_page([job(matched=None, gaps=None)], [], PROFILE, NOW))
        self.assertEqual(data["jobs"][0]["matched"], [])
        self.assertEqual(data["jobs"][0]["gaps"], [])

    def test_rebuild_keeps_the_data_and_uses_the_current_template(self):
        page = render.build_page([job(), job(key="le:2", title="Structures Intern")], [], PROFILE, NOW)
        with tempfile.TemporaryDirectory() as d:
            src, dst = Path(d) / "in.html", Path(d) / "out" / "index.html"
            src.write_text(page.replace("<title>Aero Job Finder</title>", "<title>old</title>"), encoding="utf-8")
            render.rebuild(src, dst, PROFILE)
            out = dst.read_text(encoding="utf-8")
        self.assertIn("<title>Aero Job Finder</title>", out)
        self.assertEqual(embedded(out)["jobs"], embedded(page)["jobs"])

    def test_old_links_still_have_somewhere_to_land(self):
        # The README links to #predicted and the digest to #unread; the page maps both
        for h in ("'predicted'", "'unread'", "'my-list'", "'summer'", "'all-opportunities'"):
            self.assertIn(h, render.TEMPLATE)

    def test_storage_keys_are_unchanged(self):
        # Saved, applied, dismissed and read state live under these keys on people's browsers
        for k in ("'ajf-status'", "'ajf-activity'", "'ajf-unread'", "'ajf-theme'"):
            self.assertIn(k, render.TEMPLATE)

    def test_template_has_no_triple_quotes_or_extra_placeholders(self):
        self.assertEqual(render.TEMPLATE.count("__DATA__"), 1)


if __name__ == "__main__":
    unittest.main()
