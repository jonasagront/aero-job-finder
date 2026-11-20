"""Pagination, partial scans, discovery's repair queue, the digest and programs, all offline."""
from __future__ import annotations

import datetime as dt
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from jobfinder import digest, discover, programs, sources  # noqa: E402
from jobfinder.util import FetchError  # noqa: E402


def wd_dated(titles: list[str], ages: list[int]):
    """A fake Workday site that lists its openings (title, days since posted) in the given order."""
    calls = []

    def post(url, body, **kw):
        calls.append(body)
        off = body.get("offset", 0)
        rows = list(zip(titles, ages))[off:off + 20] if not body.get("searchText") else []
        word = lambda a: "Posted Today" if a == 0 else "Posted Yesterday" if a == 1 else (  # noqa: E731
            "Posted 30+ Days Ago" if a >= 30 else f"Posted {a} Days Ago")
        return {"total": len(titles), "jobPostings": [{"title": t, "externalPath": f"/job/x/{t}_R{off + i}",
                                                       "postedOn": word(a)} for i, (t, a) in enumerate(rows)]}
    return post, calls


def wd_site(titles: list[str], facet_titles: list[str] | None = None, fail_at: int | None = None,
            repeat: bool = False):
    """A fake Workday API over a list of titles: answers searches (full text, so a
    term matches any title containing it), an internship filter, and the empty search."""
    calls = []

    def post(url, body, **kw):
        calls.append(body)
        off = body.get("offset", 0)
        if fail_at is not None and off == fail_at:
            raise FetchError("HTTP 500", 500)
        if body.get("appliedFacets"):
            pool = facet_titles or []
        elif body.get("searchText"):
            pool = [t for t in titles if body["searchText"].lower() in t.lower()]
        else:
            pool = titles
        page = pool[0:20] if repeat else pool[off:off + 20]
        out = {"total": len(pool), "jobPostings": [{"title": t, "externalPath": f"/job/x/{t}_R{titles.index(t) if t in titles else 9000 + (facet_titles or []).index(t)}"} for t in page]}
        if off == 0 and not body.get("appliedFacets") and not body.get("searchText"):
            out["facets"] = [{"facetParameter": "workerSubType", "values": [{"descriptor": "Intern", "id": "i1"}]}] if facet_titles else []
        return out
    return post, calls


def detail(host, tenant, site, path):
    return {"jobDescription": "<p>Text</p>", "startDate": dt.date.today().isoformat()}


class Pagination(unittest.TestCase):
    def run_wd(self, post):
        rep = sources.Scan("t")
        sources._local.scan = rep
        try:
            with mock.patch.object(sources, "post_json", post), mock.patch.object(sources, "_workday_detail", detail):
                jobs = sources.fetch_workday("acme.wd1.myworkdayjobs.com", "Ext", "Acme")
        finally:
            sources._local.scan = None
        return jobs, rep

    def test_newest_first_reads_to_the_age_limit(self):
        # 3,000 openings, newest first, one internship deep in the list (page 30) but posted
        # 9 days ago, and one posted 25 days ago: the first is found, reading stops after that
        titles = [f"Engineer {i}" for i in range(3000)]
        ages = [i // 60 for i in range(3000)]  # 60 postings a day
        titles[590], titles[1500] = "Structures Intern", "Old Thermal Intern"
        post, calls = wd_dated(titles, ages)
        jobs, rep = self.run_wd(post)
        self.assertEqual([j["title"] for j in jobs], ["Structures Intern"])
        self.assertFalse(rep.partial)
        # 18 days (15 + 3 margin) of 60 a day is 1,080 postings: about 55 pages, not 150
        self.assertLess(len(calls), 60)
        self.assertTrue(all(not b.get("searchText") for b in calls))

    def test_not_newest_first_falls_back(self):
        titles = [f"Engineer {i}" for i in range(80)] + ["Propulsion Intern"]
        ages = [30 if i % 2 else 0 for i in range(81)]  # mixed order
        post, calls = wd_dated(titles, ages)
        jobs, rep = self.run_wd(post)
        self.assertTrue(any("newest first" in n for n in rep.notes))
        self.assertEqual([j["title"] for j in jobs], ["Propulsion Intern"])

    def test_date_stop_only_trusts_newest_first(self):
        day = lambda n: (dt.date.today() - dt.timedelta(days=n)).isoformat()  # noqa: E731
        stop = sources._DateStop()
        self.assertFalse(stop.done([day(i) for i in range(0, 10)]))
        self.assertTrue(stop.done([day(i) for i in range(19, 29)]))  # a whole page past 15 + 3 days
        mixed = sources._DateStop()
        self.assertFalse(mixed.done([day(1), day(40), day(2)] + [day(3)] * 8))  # not newest first
        self.assertFalse(mixed.done([day(40)] * 20))

    def test_small_site_read_whole_past_pages_without_interns(self):
        # 3 pages with no internship titles, then internships on page 4: the old scan stopped early
        titles = [f"Senior Engineer {i}" for i in range(60)] + ["Mechanical Engineering Intern", "Student Engineer"]
        post, calls = wd_site(titles)
        jobs, rep = self.run_wd(post)
        self.assertEqual(sorted(j["title"] for j in jobs), ["Mechanical Engineering Intern", "Student Engineer"])
        self.assertFalse(rep.partial)
        self.assertEqual(len(calls), 4)

    def test_big_site_uses_filter_and_full_searches(self):
        titles = [f"Engineer {i}" for i in range(1200)] + ["Propulsion Intern"]
        titles[700] = "Structures Internship"
        post, calls = wd_site(titles, facet_titles=["Test Co-op"])
        jobs, rep = self.run_wd(post)
        self.assertEqual({j["title"] for j in jobs}, {"Propulsion Intern", "Structures Internship", "Test Co-op"})
        self.assertFalse(rep.partial)
        self.assertTrue(any(b.get("appliedFacets") for b in calls))

    def test_page_cap_marks_partial(self):
        titles = [f"Engineering Intern {i}" for i in range(500)]
        post, _ = wd_site(titles)
        with mock.patch.object(sources, "WD_FULL_READ", 100):
            jobs, rep = self.run_wd(post)
        # Big-site path; searches read to the 100-page cap fine, so it's complete here
        self.assertFalse(rep.partial)
        rep = sources.Scan("cap")
        sources._paged("x", 3, rep, lambda i: False)
        self.assertTrue(rep.partial)
        self.assertIn("3-page safety limit", rep.notes[0])

    def test_failing_later_page_keeps_earlier_pages(self):
        titles = [f"Engineering Intern {i}" for i in range(50)]
        post, _ = wd_site(titles, fail_at=20)
        jobs, rep = self.run_wd(post)
        self.assertEqual(len(jobs), 20)
        self.assertTrue(rep.partial)

    def test_repeated_page_stops(self):
        titles = [f"Engineering Intern {i}" for i in range(50)]
        post, calls = wd_site(titles, repeat=True)
        jobs, rep = self.run_wd(post)
        self.assertTrue(rep.partial)
        self.assertLess(len(calls), 10)

    def test_first_page_failure_fails_the_source(self):
        def post(url, body, **kw):
            raise FetchError("HTTP 500", 500)
        with mock.patch.object(sources, "post_json", post), mock.patch.object(sources, "_answer", lambda *a, **k: (500, "")):
            _, st = sources.run_source("Acme", "Workday", lambda: sources.fetch_workday("a.wd1.myworkdayjobs.com", "E", "A"))
        self.assertFalse(st["ok"])

    def test_successfactors_json_reads_past_pages_without_interns(self):
        pages = {0: ["Engineer A"] * 10, 1: ["Engineer B"] * 10, 2: ["Mechanical Intern"]}

        def post(url, body, **kw):
            if body["keywords"] != "intern":
                return {"jobSearchResult": [], "totalJobs": 0}
            titles = pages.get(body["pageNumber"], [])
            return {"totalJobs": 21, "jobSearchResult": [{"response": {"id": f"{body['pageNumber']}{i}",
                                                                        "unifiedStandardTitle": t}} for i, t in enumerate(titles)]}
        with mock.patch.object(sources, "post_json", post), mock.patch.object(sources, "_get_page", lambda *a, **k: ""):
            jobs = sources._successfactors_json("x.com", "X", 40, sources._keep_all)
        self.assertEqual([j["title"] for j in jobs], ["Mechanical Intern"])

    def test_time_budget_stops_paging_as_partial(self):
        rep = sources.Scan("t")
        pages = []
        with mock.patch.object(sources, "DEADLINE", 0.0):  # already past
            sources._paged("search", 50, rep, lambda i: pages.append(i) or False)
        self.assertEqual(pages, [0])
        self.assertTrue(rep.partial)
        self.assertIn("time budget", rep.notes[0])

    def test_run_source_reports_partial(self):
        def fetch():
            sources._scan().incomplete("search: stopped at the 10-page safety limit")
            return [{"title": "Intern", "posted": ""}]
        jobs, st = sources.run_source("S", "Kind", fetch)
        self.assertTrue(st["ok"])
        self.assertFalse(st["complete"])
        self.assertEqual(jobs[0]["source_id"], "S")


class Discovery(unittest.TestCase):
    def test_failing_board_is_never_dropped(self):
        found = {"greenhouse:x": {"kind": "greenhouse", "board": "x", "name": "X", "first_seen": "2026-01-01",
                                  "last_seen": "2026-11-01", "fails": 0}}
        day = dt.date(2026, 11, 1)
        for i in range(12):
            today = (day + dt.timedelta(days=i)).isoformat()
            extra, waiting = discover.as_sources(found, {}, today)
            scanned = [c["name"] for v in extra.values() for c in v]
            discover.record_results(found, [{"name": n, "ok": False, "error": "HTTP 500"} for n in scanned], today)
        self.assertIn("greenhouse:x", found)
        self.assertEqual(found["greenhouse:x"]["state"], "repair")
        self.assertGreater(found["greenhouse:x"]["next_try"], "2026-11-12")

    def test_backoff(self):
        self.assertEqual(discover._next_try(1, "2026-11-19"), "2026-11-19")
        self.assertEqual(discover._next_try(3, "2026-11-19"), "2026-11-20")
        self.assertEqual(discover._next_try(30, "2026-11-19"), "2026-12-03")

    def test_moved_board_is_replaced(self):
        found = {"workday:old/site": {"kind": "workday", "host": "old", "site": "site", "name": "Symbotic",
                                      "first_seen": "2026-01-01", "last_seen": "2026-11-01", "fails": 5, "state": "repair"}}
        added = discover.record_results(found, [{"name": "Symbotic", "ok": False, "error": "HTTP 422"}], "2026-11-19",
                                        {"symbotic": {"greenhouse:symbotic": {"kind": "greenhouse", "board": "symbotic"}}})
        self.assertEqual(found["workday:old/site"]["state"], "moved")
        self.assertIn("greenhouse:symbotic", found)
        self.assertTrue(added)

    def test_separate_boards_of_one_company_both_scanned(self):
        cfg = {"greenhouse": [{"name": "Relativity Space", "board": "relativity"}]}
        found = {"greenhouse:rsinternboard": {"kind": "greenhouse", "board": "rsinternboard", "name": "Relativity Space",
                                              "first_seen": "2026-11-01", "last_seen": "2026-11-01", "fails": 0}}
        extra, _ = discover.as_sources(found, cfg, "2026-11-19")
        self.assertEqual(extra["greenhouse"][0]["name"], "Relativity Space (rsinternboard)")

    def test_candidates_wait_for_validation(self):
        found = {}
        posts = [("Small Robotics", "https://job-boards.greenhouse.io/smallrobo/jobs/1", "Mechanical Engineering Intern",
                  "2026-10-01")]
        discover.learn_engineering(found, posts, lambda t: True, "2026-11-19", 3)
        self.assertEqual(found["greenhouse:smallrobo"]["state"], "candidate")
        extra, _ = discover.as_sources(found, {}, "2026-11-19")
        discover.record_results(found, [{"name": "Small Robotics", "ok": True}], "2026-11-19")
        self.assertEqual(found["greenhouse:smallrobo"]["state"], "active")
        self.assertEqual(found["greenhouse:smallrobo"]["validated"], "2026-11-19")

    def test_more_hiring_systems_recognized(self):
        self.assertEqual(discover.site_of("https://careers-acme.icims.com/jobs/123/x/job")[0], "icims:careers-acme.icims.com")
        self.assertEqual(discover.site_of("https://apply.workable.com/acme/j/AB12/")[0], "workable:acme")
        self.assertIsNone(discover.site_of("https://www.google.com/search?q=x"))

    def test_name_matching(self):
        self.assertTrue(discover.names_match("Firehawk Aerospace", "Firehawk"))
        self.assertFalse(discover.names_match("Mercury Systems", "Mercury Insurance"))


class Digest(unittest.TestCase):
    def jobs(self):
        now = "2026-11-19T15:00:00+00:00"
        return [{"key": "a", "company": "SpaceX", "title": "Propulsion Intern", "url": "https://x/a", "found_at": now,
                 "first_seen": "2026-11-19", "tracks": {"summer": {"score": 80}, "all": {"score": 80}},
                 "date_kind": "employer", "posted": "2026-11-18"},
                {"key": "b", "company": "Acme", "title": "Intern", "url": "https://x/b", "found_at": now,
                 "first_seen": "2026-11-19", "tracks": {"all": {"score": 20}}, "date_kind": "none", "posted": ""}]

    def test_build_and_no_repeats(self):
        now = dt.datetime(2026, 11, 19, 16, tzinfo=dt.timezone.utc)
        log = {"sent": {}, "digests": []}
        status = [{"name": "NXP", "state": "stale", "error": "Workday maintenance", "last_success": ""}]
        deadlines = [{"program": "NREIP", "term": "Summer 2027", "date": "2026-11-30", "days": 11, "url": "u"}]
        d = digest.build(self.jobs(), status, deadlines, log, now, "https://p/", {"summer": "Summer 2027"})
        self.assertEqual(d["relevant"], 1)
        self.assertEqual(d["new"], 2)
        self.assertIn("Propulsion Intern", d["text"])
        self.assertIn("NREIP", d["text"])
        self.assertIn("NXP", d["text"])
        log["sent"] = {"a": "2026-11-19", "b": "2026-11-19"}
        d2 = digest.build(self.jobs(), [], [], log, now, "https://p/", {})
        self.assertEqual(d2["new"], 0)

    def test_off_by_default_and_needs_secrets(self):
        now = dt.datetime(2026, 11, 19, 12)
        self.assertFalse(digest.should_send({"enabled": False}, {"digests": []}, now)[0])
        with mock.patch.dict("os.environ", {}, clear=True):
            self.assertFalse(digest.should_send({"enabled": True}, {"digests": []}, now)[0])
        with mock.patch.dict("os.environ", {"NTFY_TOPIC": "t"}, clear=True):
            self.assertTrue(digest.should_send({"enabled": True, "hour": 9}, {"digests": []}, now)[0])
            self.assertFalse(digest.should_send({"enabled": True, "hour": 9},
                                                {"digests": [{"day": "2026-11-19", "ok": True}]}, now)[0])


class Programs(unittest.TestCase):
    def test_passed_deadlines_close_a_program(self):
        cfg = [{"name": "P", "url": "u", "status": "open", "verified": "2026-11-01",
                "deadlines": [{"term": "Summer 2027", "date": "2026-11-10", "text": "t"}]},
               {"name": "Q", "url": "u", "status": "open", "verified": "2026-11-01",
                "deadlines": [{"term": "Summer 2027", "date": "2026-12-01", "text": "t"}]}]
        rows = {r["name"]: r for r in programs.rows(cfg, {}, "2026-11-19")}
        self.assertEqual(rows["P"]["status"], "closed")
        self.assertEqual(rows["Q"]["status"], "open")
        self.assertEqual(programs.upcoming_deadlines(list(rows.values()))[0]["program"], "Q")

    def test_program_file_has_only_dated_deadlines(self):
        import tomllib
        cfg = tomllib.loads((ROOT / "programs.toml").read_text(encoding="utf-8"))["program"]
        for p in cfg:
            self.assertTrue(p.get("verified"), p["name"])
            for d in p.get("deadlines", []):
                dt.date.fromisoformat(d["date"])
                self.assertTrue(d.get("text"), p["name"])


if __name__ == "__main__":
    unittest.main()
