"""Regression tests for the scan's keep/drop rules. Run with:  python -m unittest discover tests"""
from __future__ import annotations

import datetime as dt
import sys
import tomllib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from jobfinder import health, pipeline  # noqa: E402
from jobfinder.match import Matcher  # noqa: E402
from jobfinder.quals import QualChecker  # noqa: E402
from jobfinder.util import job_key  # noqa: E402

PROFILE = tomllib.loads((ROOT / "profile.toml").read_text(encoding="utf-8"))
SOURCES = tomllib.loads((ROOT / "sources.toml").read_text(encoding="utf-8"))
TODAY = dt.date.today()


def days_ago(n: int) -> str:
    return (TODAY - dt.timedelta(days=n)).isoformat()


def matcher() -> Matcher:
    m = Matcher(PROFILE, SOURCES)
    m.qc = QualChecker(m, PROFILE)
    return m


def job(**kw) -> dict:
    j = {"company": "Acme Widgets", "title": "Mechanical Engineering Intern - Summer 2027", "location": "Orlando, FL",
         "url": "https://example.com/jobs/1", "source": "Acme careers", "source_id": "Acme", "posted": days_ago(2),
         "description": "", "season_hint": ""}
    j.update(kw)
    j.setdefault("key", job_key(j["url"], j["company"], j["title"]))
    return j


class AgeLimit(unittest.TestCase):
    def test_profile_keeps_15_days(self):
        self.assertEqual(PROFILE["search"]["max_age_days"], 15)

    def test_dated_postings(self):
        today = TODAY.isoformat()
        self.assertFalse(pipeline.too_old({"posted": days_ago(15)}, today, 15))
        self.assertTrue(pipeline.too_old({"posted": days_ago(16)}, today, 15))

    def test_undated_postings_count_from_first_seen(self):
        today = TODAY.isoformat()
        self.assertFalse(pipeline.too_old({"posted": "", "first_seen": days_ago(15)}, today, 15))
        self.assertTrue(pipeline.too_old({"posted": "", "first_seen": days_ago(16)}, today, 15))

    def test_analyze_drops_old_postings(self):
        analysis, why = matcher().analyze(job(posted=days_ago(20)))
        self.assertIsNone(analysis)
        self.assertEqual(why, "posting too old")

    def test_merge_applies_limit_to_kept_postings(self):
        old = {"k1": {**job(key="k1"), "posted": days_ago(30), "first_seen": days_ago(30), "tracks": {"all": {}}}}
        out = pipeline.merge([], old, {"Acme": "failed"}, {"keys": {}}, TODAY.isoformat(), "x", 15)
        self.assertEqual(out, [])


class LowScoreRetention(unittest.TestCase):
    def test_low_score_kept_in_all(self):
        # An electrical internship at a non-aerospace company: not in Summer (aerospace),
        # but it still passes the basic checks
        a, why = matcher().analyze(job(company="Generic Power Co", title="Electrical Engineering Intern",
                                       description="Pursuing a bachelor's degree in electrical engineering."))
        self.assertIsNotNone(a, why)
        self.assertIn("all", a["tracks"])
        self.assertNotIn("summer", a["tracks"])
        self.assertIn("summer", a["misses"])

    def test_below_section_minimum_still_in_all(self):
        m = matcher()
        for tr in m.tracks.values():
            tr["min_score"] = 101  # nothing can reach a curated section
        a, _ = m.analyze(job(company="SpaceX", title="Propulsion Engineering Intern - Summer 2027"))
        self.assertIsNotNone(a)
        self.assertEqual(set(a["tracks"]), {"all"})
        for t in ("summer", "broad"):
            self.assertTrue(a["misses"][t].startswith("low score"), a["misses"][t])

    def test_missing_description_is_uncertain_not_dropped(self):
        a, _ = matcher().analyze(job(description=""))
        self.assertIsNotNone(a)
        self.assertIn("Full description not loaded", a["uncertain"])

    def test_eligibility_problems_stay_visible(self):
        a, _ = matcher().analyze(job(description="Must be graduating between December 2026 and May 2027. "
                                                 "Pursuing a bachelor's degree in mechanical engineering."))
        self.assertIsNotNone(a)
        self.assertTrue(any(f["kind"] == "warn" for f in a["flags"]))


class Matching(unittest.TestCase):
    def test_student_program_titles(self):
        m = matcher()
        self.assertEqual(m.intern_status("Mechanical Engineering Co-op")[0], "yes")
        self.assertEqual(m.intern_status("Student Engineer, Test")[0], "yes")
        self.assertEqual(m.intern_status("Undergraduate Research Assistant")[0], "yes")
        self.assertEqual(m.intern_status("Propulsion Engineer", emp="Intern")[0], "yes")
        self.assertEqual(m.intern_status("Engineering Trainee", "We are looking for currently enrolled students")[0], "yes")
        self.assertEqual(m.intern_status("Engineering Trainee", "Requires 5+ years of engineering experience")[0], "no")
        self.assertEqual(m.intern_status("Engineering Trainee")[0], "maybe")
        self.assertEqual(m.intern_status("Propulsion Engineer - Summer 2027")[0], "maybe")
        self.assertEqual(m.intern_status("Senior Mechanical Engineer")[0], "no")
        self.assertEqual(m.intern_status("Apprentice Electrician")[0], "no")
        self.assertEqual(m.intern_status("Entry Level Fire Protection Engineer - Summer 2027")[0], "no")
        self.assertEqual(m.intern_status("Engineering Apprentice")[0], "maybe")

    def test_ambiguous_kept_only_in_all(self):
        a, _ = matcher().analyze(job(title="Propulsion Engineer - Summer 2027", company="SpaceX"))
        self.assertIsNotNone(a)
        self.assertEqual(set(a["tracks"]), {"all"})
        self.assertTrue(a["uncertain"])

    def test_graduate_only_titles_dropped(self):
        a, why = matcher().analyze(job(title="PhD Intern, Aerodynamics"))
        self.assertIsNone(a)
        self.assertEqual(why, "graduate-student role")

    def test_field_from_description(self):
        a, _ = matcher().analyze(job(title="Summer 2027 Intern", company="Generic Power Co",
                                     description="Currently enrolled students pursuing a degree in Mechanical "
                                                 "Engineering. Design fixtures in SolidWorks."))
        self.assertIsNotNone(a)
        self.assertEqual(a["discipline"], "Mechanical")
        self.assertIn("Field taken from the majors the description lists", a["uncertain"])

    def test_terms(self):
        m = matcher()
        self.assertEqual(m.terms_of({"title": "Intern - Fall 2027"}, ""), ["Fall 2027"])
        self.assertEqual(m.terms_of({"title": "Intern", "season_hint": "Summer 2027, Fall 2027"}, ""),
                         ["Summer 2027", "Fall 2027"])
        self.assertEqual(m.terms_of({"title": "Intern"}, "graduating Spring 2029"), [])


class UndatedPostings(unittest.TestCase):
    def test_provenance(self):
        lists = {"Simplify Summer 2027 list"}
        j = job(posted="")
        pipeline.date_provenance(j, lists)
        self.assertEqual(j["date_kind"], "none")
        j = job()
        pipeline.date_provenance(j, lists)
        self.assertEqual(j["date_kind"], "employer")
        j = job(source_id="Simplify Summer 2027 list", source="Simplify Summer 2027 list")
        pipeline.date_provenance(j, lists)
        self.assertEqual((j["date_kind"], j["posted_from"]), ("listing", "Simplify Summer 2027 list"))
        j = job(posted_from="intern-list.com")
        pipeline.date_provenance(j, lists)
        self.assertEqual(j["date_kind"], "listing")

    def test_undated_kept_in_curated_tabs(self):
        a, _ = matcher().analyze(job(posted="", company="SpaceX", title="Propulsion Engineering Intern - Summer 2027"))
        self.assertIsNotNone(a)
        self.assertIn("summer", a["tracks"])

    def test_undated_first_found_today_is_kept(self):
        today = TODAY.isoformat()
        out = pipeline.merge([job(posted="", tracks={"all": {}})], {}, {"Acme": "ok"}, {"keys": {}}, today, "stamp", 15)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["first_seen"], today)
        self.assertEqual(out[0]["found_at"], "stamp")


class FirstSeenPersistence(unittest.TestCase):
    def setUp(self):
        self.today = TODAY.isoformat()

    def test_kept_across_rescans(self):
        old = {"k": {**job(key="k"), "first_seen": days_ago(5), "found_at": "t0"}}
        out = pipeline.merge([job(key="k")], old, {"Acme": "ok"}, {"keys": {}}, self.today, "t1", 15)
        self.assertEqual((out[0]["first_seen"], out[0]["found_at"]), (days_ago(5), "t0"))

    def test_survives_dropping_off_the_page(self):
        seen = {"keys": {}}
        first = job(key="k", first_seen=days_ago(6), found_at="t0")
        pipeline.remember(seen, [first], days_ago(6))
        # Gone for a few runs (source failing past the cache), then back with no jobs.json record
        out = pipeline.merge([job(key="k")], {}, {"Acme": "ok"}, seen, self.today, "t9", 15)
        self.assertEqual(out[0]["first_seen"], days_ago(6))
        self.assertEqual(out[0]["found_at"], "t0")

    def test_relisting_under_new_link(self):
        seen = {"keys": {}}
        pipeline.remember(seen, [job(key="old", first_seen=days_ago(4), found_at="t0")], days_ago(3))
        out = pipeline.merge([job(key="new")], {}, {"Acme": "ok"}, seen, self.today, "t9", 15)
        self.assertEqual(out[0]["first_seen"], days_ago(4))
        self.assertEqual(out[0]["aka"], ["old"])

    def test_second_live_location_is_not_a_relisting(self):
        seen = {"keys": {}}
        pipeline.remember(seen, [job(key="a", first_seen=days_ago(9))], days_ago(1))
        out = pipeline.merge([job(key="a"), job(key="b")], {}, {"Acme": "ok"}, seen, self.today, "t9", 15)
        b = next(j for j in out if j["key"] == "b")
        self.assertEqual(b["first_seen"], self.today)
        self.assertNotIn("aka", b)

    def test_failed_or_partial_source_keeps_postings_marked_stale(self):
        for state in ("failed", "partial", "skipped"):
            old = {"k": {**job(key="k"), "first_seen": days_ago(3), "checked": days_ago(1) + "T10:00:00+00:00",
                         "tracks": {"all": {"score": 50}}}}
            out = pipeline.merge([], old, {"Acme": state}, {"keys": {}}, self.today, "t", 15)
            self.assertEqual(len(out), 1, state)
            self.assertEqual(out[0]["stale"]["since"], days_ago(1))

    def test_missing_from_complete_scan_is_closed(self):
        old = {"k": {**job(key="k"), "first_seen": days_ago(3), "tracks": {"all": {}}}}
        self.assertEqual(pipeline.merge([], old, {"Acme": "ok"}, {"keys": {}}, self.today, "t", 15), [])


class Dedup(unittest.TestCase):
    def test_workday_same_req_on_two_sites(self):
        a = job_key("https://boeing.wd1.myworkdayjobs.com/EXTERNAL_CAREERS/job/Seattle/Intern_JR2026123", "", "")
        b = job_key("https://boeing.wd1.myworkdayjobs.com/en-US/INTERN/job/Seattle-WA/Intern-Mech_JR2026123", "", "")
        self.assertEqual(a, b)

    def test_greenhouse_link_forms(self):
        self.assertEqual(job_key("https://boards.greenhouse.io/spacex/jobs/123", "", ""),
                         job_key("https://boards.greenhouse.io/embed/job_app?for=spacex&token=123", "", ""))

    def test_query_ids_kept_apart(self):
        u = "https://workforcenow.adp.com/mascsr/default/mdf/recruitment/recruitment.html?cid=x&jobId={}"
        self.assertNotEqual(job_key(u.format(1), "", ""), job_key(u.format(2), "", ""))

    def test_same_company_names(self):
        pipeline.set_employers(SOURCES)
        self.assertEqual(pipeline.same_job({"company": "Raytheon", "title": "Systems Intern"}),
                         pipeline.same_job({"company": "RTX", "title": "Systems Intern"}))


class Health(unittest.TestCase):
    def test_states_and_suspicious_drop(self):
        db: dict = {}
        for i in range(4):
            health.update(db, [{"name": "S", "ok": True, "complete": True, "count": 40}], f"2026-11-1{i}T10:00:00+00:00")
        st = [{"name": "S", "ok": True, "complete": True, "count": 0}]
        health.update(db, st, "2026-11-15T10:00:00+00:00")
        self.assertEqual(st[0]["state"], "ok")
        self.assertIn("dropped from about 40 postings to 0", st[0]["suspicious"])
        st = [{"name": "S", "ok": True, "complete": False, "count": 30}]
        health.update(db, st, "2026-11-15T15:00:00+00:00")
        self.assertEqual(st[0]["state"], "partial")
        st = [{"name": "S", "ok": False, "complete": False, "count": 0, "error": "HTTP 500"}]
        health.update(db, st, "2026-11-15T20:00:00+00:00")
        self.assertEqual(st[0]["state"], "failed")
        health.update(db, st, "2026-11-17T20:00:00+00:00")
        self.assertEqual(st[0]["state"], "stale")
        self.assertEqual(st[0]["last_success"], "2026-11-15T15:00:00+00:00")


if __name__ == "__main__":
    unittest.main()
