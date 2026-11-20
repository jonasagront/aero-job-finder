"""Coverage audit: how much does the scan miss, measured on a sample.

Each run picks a few company boards (rotating, least recently audited first) and reads
each one again as completely as the site allows, independently of the scan's shortcuts:
Workday sites are read whole (every opening, not just searches and filters), and other
boards are read without the scan's title filter and with higher page caps. Every opening
that is in scope (passes the same basic checks the page uses: an internship or student
role, engineering, in the U.S., and within the 15-day age limit) should be on the page.
Each one that isn't is a miss, classified by where it was lost:

  discovery       the board isn't scanned at all (a candidate board)
  collection      the scan's request for that board failed, or its searches never
                  returned the posting
  pagination      the scan stopped early on that board (page cap or failed page)
  parsing         the scan read the posting but got a field wrong (no link, a date or
                  place that made it look old or foreign)
  deduplication   merged into a different posting that isn't on the page
  filtering       read, then dropped by a filter (the reason is saved)
  display         saved but in no tab of the page

Results go to data/coverage_audit.json: each audited board, its in-scope count, what was
found, and every miss with the posting's title, link, dates and the reason. Coverage is
reported for the audited sample only; it says nothing about boards never audited.
"""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

from . import sources as S
from .pipeline import same_job
from .util import FetchError, job_key, post_json

PER_RUN = 3
KEEP_RUNS = 60
WD_AUDIT_PAGES = 150  # Workday sites up to 3,000 openings are audited by a full read

# Kinds the audit can re-read, and how independent that read is from the scan's own
FULL_LIST = {"greenhouse", "lever", "ashby", "workable", "gem", "pinpoint", "bamboohr", "rippling", "breezy",
             "paylocity", "applicantpro", "paycor", "jazzhr", "adp", "clearcompany"}
SEARCHED = {"successfactors", "icims", "jibe", "oracle", "phenom", "smartrecruiters", "taleo", "eightfold",
            "ukg", "activate", "jobsfeed", "searchpage", "brassring"}


def load(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, ValueError):
        data = {}
    data.setdefault("audited", {})   # source name -> last audit date
    data.setdefault("runs", [])
    return data


def save(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8")


def pick(tasks: list[tuple], status: dict[str, dict], data: dict, per_run: int = PER_RUN) -> list[tuple]:
    """Up to per_run boards the scan read this run (any outcome), least recently audited
    first; at most one Workday site (a full read is the slowest audit)."""
    cands = [t for t in tasks if t[2] in FULL_LIST | SEARCHED | {"workday"} and t[0] in status]
    cands.sort(key=lambda t: (data["audited"].get(t[0], ""), t[0]))
    out, wd = [], 0
    for t in cands:
        if t[2] == "workday":
            if wd:
                continue
            wd += 1
        out.append(t)
        if len(out) >= per_run:
            break
    return out


def _workday_full(entry: dict, have: set[str]) -> list[dict]:
    """Every opening on a Workday site; internship-looking ones not already collected
    are opened for their text (the rest only need their title)."""
    host, site = entry["host"], entry["site"]
    tenant = entry.get("tenant") or host.split(".")[0]
    api = f"https://{host}/wday/cxs/{tenant}/{site}/jobs"
    page_root = (f"https://{host}/recruiting/{tenant}/{site}" if host.endswith(".myworkdaysite.com")
                 else f"https://{host}/{site}")
    rows, offset, total = {}, 0, 0
    for _ in range(WD_AUDIT_PAGES):
        page = post_json(api, {"appliedFacets": {}, "limit": 20, "offset": offset, "searchText": ""}, timeout=40, retries=4)
        batch = page.get("jobPostings") or []
        for p in batch:
            rows.setdefault(p.get("externalPath"), p)
        offset += len(batch)
        total = total or int(page.get("total") or 0)
        if not batch or offset >= total:
            break
    out = []
    for path, p in rows.items():
        url = f"{page_root}{path}"
        j = {"company": entry["name"], "title": (p.get("title") or "").strip(), "location": p.get("locationsText", ""),
             "url": url, "posted": S._workday_posted_on(p.get("postedOn", "")), "description": "", "season_hint": ""}
        if S._INTERNISH.search(j["title"]) and job_key(url, j["company"], j["title"]) not in have:
            try:
                info = S._workday_detail(host, tenant, site, path)
                j["description"] = S.html_to_text(info.get("jobDescription"))
                j["posted"] = S._date_from_iso(info.get("startDate")) or j["posted"]
                j["url"] = info.get("externalUrl") or url
                if not j["location"] or j["location"].endswith("Locations"):
                    j["location"] = "; ".join(filter(None, [info.get("location")] + (info.get("additionalLocations") or [])))
            except FetchError:
                pass
        out.append(j)
    return out


def official(task: tuple, have: set[str]) -> tuple[list[dict], str]:
    """(openings, how they were read) for one board."""
    name, label, kind, entry, fn = task
    if kind == "workday":
        return _workday_full({**entry, "name": name}, have), "full list of every opening"
    # The scan's own fetcher, without its title filter
    fetchers = {
        "greenhouse": lambda: S.fetch_greenhouse(entry["board"], name),
        "lever": lambda: S.fetch_lever(entry["board"], name),
        "ashby": lambda: S.fetch_ashby(entry["board"], name),
        "workable": lambda: S.fetch_workable(entry["board"], name),
        "gem": lambda: S.fetch_gem(entry["board"], name),
        "pinpoint": lambda: S.fetch_pinpoint(entry["board"], name),
        "bamboohr": lambda: S.fetch_bamboohr(entry["board"], name),
        "rippling": lambda: S.fetch_rippling(entry["board"], name),
        "breezy": lambda: S.fetch_breezy(entry["board"], name),
        "paylocity": lambda: S.fetch_paylocity(entry["board"], name),
        "applicantpro": lambda: S.fetch_applicantpro(entry["host"], name),
        "paycor": lambda: S.fetch_paycor(entry["client"], name),
        "jazzhr": lambda: S.fetch_jazzhr(entry["board"], name),
        "adp": lambda: S.fetch_adp(entry["cid"], name),
        "clearcompany": lambda: S.fetch_clearcompany(entry["site_id"], name),
        "successfactors": lambda: S.fetch_successfactors(entry["host"], name, max_pages=40),
        "icims": lambda: S.fetch_icims(entry["host"], name, max_pages=30),
        "jibe": lambda: S.fetch_jibe(entry["host"], name, max_pages=20),
        "oracle": lambda: S.fetch_oracle(entry["host"], entry["site"], name, max_pages=80),
        "phenom": lambda: S.fetch_phenom(entry["base"].rstrip("/"), name, max_pages=30),
        "smartrecruiters": lambda: S.fetch_smartrecruiters(entry["board"], name),
        "taleo": lambda: S.fetch_taleo(entry["host"], entry["section"], entry["portal"], name, max_pages=20),
        "eightfold": lambda: S.fetch_eightfold(entry["host"], entry["domain"], name, max_pages=80),
        "ukg": lambda: S.fetch_ukg(entry["board"].rstrip("/"), name),
        "activate": lambda: S.fetch_activate(entry["host"], name, max_pages=20),
        "jobsfeed": lambda: S.fetch_jobsfeed(entry["host"], name, max_pages=20),
        "searchpage": lambda: S.fetch_searchpage(entry["search"], entry["path"], name, max_pages=30,
                                                 content=entry.get("content", "")),
        "brassring": lambda: S.fetch_brassring(entry["partner"], entry["sites"], name,
                                               entry.get("location_fields", ("formtext5", "formtext4")),
                                               entry.get("title_field", "jobtitle"), max_pages=30),
    }
    how = "full list, no title filter" if kind in FULL_LIST else "same searches with higher page caps, no title filter"
    return fetchers[kind](), how


def classify(j: dict, ctx: dict) -> tuple[str, str]:
    """Where an in-scope opening the page doesn't have was lost."""
    st = ctx["status"].get(j["source_id"], {})
    if ctx.get("candidate"):
        return "discovery", "the board is only a candidate; it isn't scanned yet"
    if not st.get("ok"):
        return "collection", f"the scan's request failed: {st.get('error', '')}"
    other = ctx["fate"].get(j["key"]) or ctx["fate"].get("same:" + "|".join(same_job(j)))
    if j["key"] not in ctx.get("raw_keys", {}).get(j["source_id"], set()):
        # The scan never got this board's own copy
        also = f" (a copy from another source was dropped: {other[1]})" if other else ""
        if not st.get("complete", True):
            return "pagination", ("; ".join(st.get("notes") or []) or "the scan stopped early") + also
        if not S._INTERNISH.search(j["title"]) and not j.get("emp_type"):
            return "filtering", "the title doesn't look like an internship, so the scan never opened it" + also
        return "collection", "the board's searches didn't return it to the scan" + also
    if other:
        kind, why = other
        if kind == "dup":
            return "deduplication", f"merged into {why}, which isn't on the page"
        if kind == "parse":
            return "parsing", why
        if why in ("posting too old", "outside the U.S."):
            return "parsing", f"the scan's copy was dropped as {why}; the board's own copy passes"
        return "filtering", why
    return "display", "collected and kept, but not on the page"


def run(sample: list[tuple], ctx: dict, matcher, today: str, max_age: int) -> dict:
    """Audit the sampled boards. ctx: status (name -> status), fate (key -> (kind, reason)),
    final_keys, final_same, candidate names."""
    report = {"date": today, "boards": []}
    for task in sample:
        name, kind = task[0], task[2]
        rec = {"source": name, "kind": kind, "in_scope": 0, "found": 0, "misses": []}
        try:
            got, how = official(task, ctx["final_keys"])
        except Exception as e:  # noqa: BLE001 - an audit never stops the scan
            rec["error"] = str(e)[:160]
            report["boards"].append(rec)
            continue
        rec["read"] = how
        rec["openings"] = len(got)
        for j in got:
            j["source_id"] = name
            j["posted"] = S._date_from_iso(j.get("posted"))
            if not j.get("url"):
                continue
            j["key"] = job_key(j["url"], j.get("company", ""), j.get("title", ""))
            analysis, _ = matcher.analyze(j)
            if analysis is None:
                continue  # out of scope: not an internship, not engineering, abroad, or past the age limit
            rec["in_scope"] += 1
            if j["key"] in ctx["final_keys"] or "|".join(same_job(j)) in ctx["final_same"]:
                rec["found"] += 1
                continue
            cat, why = classify(j, {**ctx, "candidate": name in ctx.get("candidates", set())})
            rec["misses"].append({"category": cat, "why": why, "title": j["title"], "url": j["url"], "key": j["key"],
                                  "posted": j.get("posted", ""), "location": j.get("location", "")[:80]})
        report["boards"].append(rec)
    return report


def record(data: dict, report: dict, today: str) -> dict:
    """Save a run's audit and return the rolling summary over the last KEEP_RUNS runs."""
    for b in report["boards"]:
        data["audited"][b["source"]] = today
    data["runs"] = (data["runs"] + [report])[-KEEP_RUNS:]
    boards = [b for r in data["runs"] for b in r["boards"] if "error" not in b]
    in_scope = sum(b["in_scope"] for b in boards)
    found = sum(b["found"] for b in boards)
    by_cat: dict[str, int] = {}
    for b in boards:
        for m in b["misses"]:
            by_cat[m["category"]] = by_cat.get(m["category"], 0) + 1
    since = data["runs"][0]["date"] if data["runs"] else today
    return {"since": since, "boards": len({b["source"] for b in boards}), "audits": len(boards),
            "in_scope": in_scope, "found": found, "by_category": by_cat,
            "recent_misses": [dict(m, source=b["source"], date=r["date"]) for r in data["runs"][-10:]
                              for b in r["boards"] for m in b["misses"]][-25:],
            "errors": [{"source": b["source"], "error": b["error"], "date": r["date"]}
                       for r in data["runs"][-5:] for b in r["boards"] if "error" in b]}
