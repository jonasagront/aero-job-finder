"""Internship scan: Summer 2027 aerospace, Fall 2027 near home, all engineering, and every
engineering internship found (All opportunities).

Run locally with:   python run.py
GitHub Actions runs this every 5 hours and publishes docs/index.html.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import re
import sys
import time
import tomllib
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urlparse

from jobfinder import audit, digest, discover, health, history, pipeline, popular, predict, programs
from jobfinder import sources as sources_mod
from jobfinder.ai import review_jobs
from jobfinder.geo import place_info
from jobfinder.match import Matcher
from jobfinder.quals import QualChecker
from jobfinder.render import build_page, track_info, update_readme
from jobfinder.sources import (LIST_ITEMS, fetch_all, fetch_description, fetch_posted_date, posting_closed,
                               source_tasks)
from jobfinder.util import FetchError, job_key

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
JOBS_FILE = DATA / "jobs.json"
DESC_FILE = DATA / "descriptions.json"
AI_FILE = DATA / "ai_reviews.json"
MISS_FILE = DATA / "description_misses.json"
DATE_MISS_FILE = DATA / "date_misses.json"
POPULAR_FILE = DATA / "popular_seen.json"
FOUND_FILE = DATA / "discovered_boards.json"
HISTORY_FILE = DATA / "history.json"
SEEN_FILE = DATA / "seen.json"
HEALTH_FILE = DATA / "source_health.json"
STATUS_FILE = DATA / "last_status.json"
REJECT_FILE = DATA / "rejections.json"
DISCOVERY_FILE = DATA / "discovery.json"
PROGRAMS_STATE = DATA / "programs.json"
AUDIT_FILE = DATA / "coverage_audit.json"
NOTIFY_LOG = DATA / "notify_log.json"
DIGEST_FILE = DATA / "digest_preview.md"
PAGE_URL = "https://jonasagront.github.io/aero-job-finder/"

MAX_NEW_LOOKUPS = 500   # full-description lookups per run for list-only postings
MAX_DATE_LOOKUPS = 300  # posting pages opened per run to find a missing posted date
RETRY_MISS_DAYS = 7     # wait this long before retrying a page that had no description
RETRY_DATE_DAYS = 2     # wait this long before retrying a page that had no posted date
BUDGET_MINUTES = 22     # the workflow stops at 40; optional steps (audit) are skipped after this
# Collectors stop turning pages this long after the run started (SCAN_COLLECT_MINUTES overrides it
# for quick local test runs)
COLLECT_MINUTES = float(os.environ.get("SCAN_COLLECT_MINUTES") or 24)
# Motorsport names too generic to look up as a company
GENERIC_NAMES = {"racing", "race team", "nascar", "indycar", "imsa", "trd", "rcr", "rfk", "hrc us"}


def load_json(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, ValueError):
        return default


def save_json(path: Path, data, indent: int | None = 1) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=indent, ensure_ascii=False), encoding="utf-8")


def fill_in(dst: dict, src: dict) -> None:
    """Copy what another source knows about the same posting onto the copy being kept."""
    if src.get("season_hint") and not dst.get("season_hint"):
        dst["season_hint"] = src["season_hint"]
    if src.get("emp_type") and not dst.get("emp_type"):
        dst["emp_type"] = src["emp_type"]
    if src.get("posted") and not dst.get("posted"):
        dst["posted"] = src["posted"]
        if src.get("source") != dst.get("source"):
            dst["posted_from"] = src.get("posted_from") or src.get("source", "")


def main() -> int:
    t0 = time.time()
    minutes = lambda: (time.time() - t0) / 60  # noqa: E731
    now = dt.datetime.now(dt.timezone.utc)
    today = now.date().isoformat()
    stamp = now.isoformat(timespec="seconds")
    profile = tomllib.loads((ROOT / "profile.toml").read_text(encoding="utf-8"))
    sources_cfg = tomllib.loads((ROOT / "sources.toml").read_text(encoding="utf-8"))
    try:
        program_cfg = tomllib.loads((ROOT / "programs.toml").read_text(encoding="utf-8")).get("program", [])
    except FileNotFoundError:
        program_cfg = []
    matcher = Matcher(profile, sources_cfg)
    matcher.qc = QualChecker(matcher, profile)
    pipeline.set_employers(sources_cfg)
    EMPLOYERS = pipeline.EMPLOYERS
    max_age = int(profile["search"].get("max_age_days", 0))
    fa = profile.get("fall", {})
    home = (float(fa["home_lat"]), float(fa["home_lon"])) if "home_lat" in fa else None

    def keep(title: str) -> bool:
        """Internship with an engineering-looking title (the history and Predicted tab use this)."""
        return matcher.title_ok(title)[0] and bool(
            matcher.discipline(title)[0] or matcher.aero_relevance(title.lower(), "", False, True) is not None)

    def keep_fetch(title: str) -> bool:
        """Which internship-looking titles collectors open for their text: any that isn't a
        grad-student or clearly non-engineering role, so a plain "Summer 2027 Intern" gets
        judged on its description instead of its title."""
        return matcher.title_excluded(title)[0]

    def wanted_co(company: str) -> bool:
        """Aerospace and motorsport companies get their whole career site scanned once a list
        links to it, and their leads kept (see below)."""
        return matcher.is_aero_company(company) or matcher.is_motor_company(company)

    # Every engineering internship seen so far, for the Predicted tab (see history.py);
    # old copies of the lists are read into it once
    hist = history.load(HISTORY_FILE)
    n_past = history.read_pinned(hist, sources_cfg.get("history", {}).get("urls", []), keep)
    if n_past:
        print(f"   {n_past} postings from past cycles added to the history")

    # ---- Career sites found automatically (see discover.py)
    found: dict = load_json(FOUND_FILE, {})
    disc_state: dict = load_json(DISCOVERY_FILE, {})
    past = list(hist["rows"].values())
    n_new = discover.learn(found, ((r["c"], r["u"], r["d"]) for r in past), wanted_co, today)
    eng_min = int(sources_cfg.get("discover", {}).get("engineering_min", 3))
    # Engineering titles only ("Mechanical Design Engineer Intern", not "Product Development Intern")
    mech = lambda t: (matcher.discipline(t)[0] in ("Aerospace", "Mechanical")  # noqa: E731
                      and re.search(r"(?i)engineer|mechanical|aerospace|aeronautic", t))
    n_new += discover.learn_engineering(found, ((r["c"], r["u"], r["t"], r["d"]) for r in past), mech, today, eng_min)
    # Independent discovery: look up companies by name on hiring systems with public APIs
    dcfg = sources_cfg.get("discover", {})
    probe_names = ([(n, "aerospace_companies") for n in sources_cfg.get("aerospace_companies", {}).get("names", [])]
                   + [(n, "motorsport_companies") for n in sources_cfg.get("motorsport_companies", {}).get("names", [])
                      if n.lower() not in GENERIC_NAMES]
                   + [(n, "discover seeds") for n in dcfg.get("seeds", [])])
    probe_added = discover.probe_names(found, disc_state, probe_names, sources_cfg, today,
                                       budget=int(dcfg.get("probes_per_run", discover.PROBES_PER_RUN)))
    extra, waiting = discover.as_sources(found, sources_cfg, today)
    scan_cfg = {**sources_cfg, **{k: sources_cfg.get(k, []) + v for k, v in extra.items()}}
    found_names = {c["name"] for v in extra.values() for c in v}
    print(f"   discovery: {len(probe_added)} boards found by name, {sum(map(len, extra.values()))} found boards "
          f"to scan, {len(waiting)} waiting to be retried")

    print(f"1) Reading job sources ({len(found_names)} career sites found automatically)")
    # Past this point collectors stop turning pages (their sources count as partial), so a run
    # slowed by rate limits still publishes well inside the workflow's 40 minutes
    sources_mod.DEADLINE = time.monotonic() - (time.time() - t0) + COLLECT_MINUTES * 60
    sources_mod.MAX_AGE_DAYS = max_age  # Workday sites are read newest first down to this age
    raw, status = fetch_all(scan_cfg, keep=keep_fetch)
    for s in status:
        if s["name"] in found_names:
            s["kind"] += " (found automatically)"
            s["found"] = True
    status += waiting
    print(f"   sources read in {minutes():.1f} min")

    # Postings on lists, by company: where each company hires now (for boards that moved)
    # and which hiring systems the scan can't read yet (the discovery report)
    lists = {s["name"] for k in ("list", "csvlist", "getro", "jobboard", "internlist") for s in sources_cfg.get(k, [])}
    intern_lists = {s["name"] for k in ("list", "csvlist", "internlist") for s in sources_cfg.get(k, [])}
    company_sites: dict[str, dict] = {}
    unsupported: dict[str, set] = {}
    cut = (now.date() - dt.timedelta(days=120)).isoformat()
    for company, url, title in ([(j.get("company", ""), j.get("url", ""), j.get("title", "")) for j in raw
                                 if j.get("source_id") in lists and not j.get("lead")]
                                + [(r["c"], r["u"], r["t"]) for r in past if r["d"] >= cut and r.get("u")]):
        site = discover.site_of(url)
        if site:
            company_sites.setdefault(discover._norm(company), {}).setdefault(site[0], site[1])
        elif url.startswith("http") and (wanted_co(company) or mech(title)):
            unsupported.setdefault(urlparse(url).netloc.lower().removeprefix("www."), set()).add(company.strip())
    covered = {s["name"].lower() for s in status if s["ok"] and not s.get("found")}
    replaced = discover.record_results(found, status, today, company_sites, covered)
    n_new += discover.learn(found, ((j.get("company", ""), j.get("url", "")) for j in raw
                                    if j.get("source_id") in lists), wanted_co, today)
    health_db = health.load(HEALTH_FILE)
    health.update(health_db, status, stamp)
    cov = health.summary(status)
    print(f"   {len(raw)} postings read; {n_new} new career sites found for next time; sources: "
          + ", ".join(f"{v} {k}" for k, v in cov["counts"].items() if v))

    # Apply links must open the company's own posting, not an AI job site or aggregator
    blocked = tuple(d.lower() for d in sources_cfg.get("blocked_link_domains", []))

    def link_ok(url: str) -> bool:
        host = urlparse(url).netloc.lower()
        return not any(host == d or host.endswith("." + d) for d in blocked)

    # What happened to every posting read, for the coverage audit and data/rejections.json
    fate: dict[str, tuple[str, str]] = {}
    drops: dict[str, Counter] = {"title and link checks": Counter(), "basic checks": Counter(), "other": Counter()}
    examples: dict[str, list] = {}

    def reject(j: dict, why: str, stage: str, kind: str = "filter") -> None:
        drops[stage][why] += 1
        ex = examples.setdefault(why, [])
        if len(ex) < 15:
            ex.append({"company": j.get("company", ""), "title": j.get("title", ""), "url": j.get("url", ""),
                       "source": j.get("source_id", "")})
        for k in filter(None, [j.get("key"), "same:" + pipeline.same_str(j)]):
            fate.setdefault(k, (kind, why))

    # 2) Basic checks on each title, then de-duplicate across sources
    candidates: dict[str, dict] = {}
    for j in raw:
        title, company, desc = j.get("title", ""), j.get("company", ""), j.get("description") or ""
        # Internship lists only list internships, even when a title doesn't say so
        if j.get("source_id") in intern_lists and not j.get("emp_type"):
            j["emp_type"] = "Internship (on an internship list)"
        if j.get("url"):
            j["key"] = j.get("key") or job_key(j["url"], company, title)
        if not j.get("url") or not title:
            reject(j, "no link or title", "title and link checks", "parse")
            continue
        ok, why = matcher.title_excluded(title)
        if not ok:
            reject(j, why, "title and link checks")
            continue
        istatus, inote = matcher.intern_status(title, desc, j.get("emp_type") or "")
        if istatus == "no":
            reject(j, inote or "not an internship", "title and link checks")
            continue
        eng_title = bool(matcher.discipline(title)[0] or matcher.aero_relevance(title.lower(), "", False, True) is not None)
        # A title with no field at an aerospace or motorsport company, or one whose description
        # lists engineering majors, gets judged on its description
        if not (eng_title or wanted_co(company) or (desc and matcher.disc_from_text(desc))):
            reject(j, "not engineering (title)" if not desc else "not engineering (title or majors listed)",
                   "title and link checks")
            continue
        if not link_ok(j["url"]):
            reject(j, "links to a blocked site", "title and link checks")
            continue
        prev = candidates.get(j["key"])
        # Prefer the copy that has a description (company board over list)
        if prev is None or (not prev.get("description") and j.get("description")):
            if prev:
                fill_in(j, prev)
            candidates[j["key"]] = j
        else:
            fill_in(prev, j)
    # Each company + title's earliest date on any source, for postings whose own site
    # gives none (taken before leads are dropped: intern-list dates count too)
    listed: dict[tuple[str, str], dict] = {}
    for j in raw:
        if j.get("posted") and j.get("title"):
            k = pipeline.same_job(j)
            if k not in listed or j["posted"] < listed[k]["posted"]:
                listed[k] = j
    # Leads (postings with no direct link) only stay when they're at an aerospace/defense or
    # motorsport company and no source with a real link has the same job. The list repeats
    # some (one per location, or under a division's name); their button runs the same search,
    # so one of each is kept.
    taken = {pipeline.same_job(j): j["key"] for j in candidates.values() if not j.get("lead")}
    n_leads = sum(1 for j in candidates.values() if j.get("lead"))
    for k, j in list(candidates.items()):
        if j.get("lead"):
            if pipeline.same_job(j) in taken:
                fate.setdefault(k, ("dup", taken[pipeline.same_job(j)]))
                del candidates[k]
            elif not wanted_co(j.get("company", "")):
                reject(j, "lead (no company link) at a company outside aerospace and motorsport", "other")
                del candidates[k]
            else:
                taken[pipeline.same_job(j)] = k
    n_new_leads = sum(1 for j in candidates.values() if j.get("lead"))
    print(f"2) {len(candidates)} engineering internship postings after removing duplicates"
          f" ({drops['title and link checks']['links to a blocked site']} skipped for linking to a blocked site;"
          f" {n_new_leads} of {n_leads} leads weren't on any company board)")

    # 3) Fill in descriptions for list postings (cached between runs)
    desc_cache: dict = load_json(DESC_FILE, {})
    misses: dict = load_json(MISS_FILE, {})  # key -> date a lookup last came back empty
    need = [j for j in candidates.values() if not j.get("description") and not j.get("lead")]
    for j in need:
        if j["key"] in desc_cache:
            j["description"] = desc_cache[j["key"]]
    lookup = [j for j in need if not j.get("description")
              and (now.date() - dt.date.fromisoformat(misses.get(j["key"], "2000-01-01"))).days >= RETRY_MISS_DAYS]
    # Look up the most promising ones first: aerospace and motorsport companies, then
    # mechanical/aerospace titles
    first = ("Aerospace", "Mechanical")
    lookup.sort(key=lambda j: (not wanted_co(j.get("company", "")),
                               matcher.discipline(j.get("title", ""))[0] not in first))
    lookup = lookup[:MAX_NEW_LOOKUPS if minutes() < COLLECT_MINUTES + 2 else 100]

    def get_desc(j):
        try:
            return j, fetch_description(j["url"])
        except (FetchError, ValueError):
            return j, ""

    got = 0
    with ThreadPoolExecutor(max_workers=8) as pool:
        for j, text in pool.map(get_desc, lookup):
            if text:
                j["description"] = text
                desc_cache[j["key"]] = text[:12000]
                misses.pop(j["key"], None)
                got += 1
            else:
                misses[j["key"]] = today
    print(f"3) Loaded {got} full descriptions ({len(lookup)} tried)")

    # Posted dates for postings whose source gave none: the date its own page gave
    # on an earlier run, then its page now, then a list with the same company + title.
    # Anything still undated shows as "Posting date unknown" with the day it was found.
    old = {j["key"]: j for j in load_json(JOBS_FILE, {}).get("jobs", [])}
    date_misses: dict = load_json(DATE_MISS_FILE, {})  # key -> date a page last showed no date
    undated = [j for j in candidates.values() if not j.get("posted")]
    for j in undated:
        prev = old.get(j["key"], {})
        if prev.get("posted") and not prev.get("posted_from"):
            j["posted"] = prev["posted"]
    look = [j for j in undated if not j.get("posted") and not j.get("lead") and j["url"].startswith("http")
            and (now.date() - dt.date.fromisoformat(date_misses.get(j["key"], "2000-01-01"))).days >= RETRY_DATE_DAYS]
    look = look[:MAX_DATE_LOOKUPS if minutes() < COLLECT_MINUTES + 4 else 60]

    def get_date(j):
        try:
            return j, fetch_posted_date(j["url"])
        except (FetchError, ValueError):
            return j, ""

    on_page = 0
    with ThreadPoolExecutor(max_workers=8) as pool:
        for j, posted in pool.map(get_date, look):
            if posted:
                j["posted"] = posted
                date_misses.pop(j["key"], None)
                on_page += 1
            else:
                date_misses[j["key"]] = today
    from_list = 0
    for j in undated:
        other = listed.get(pipeline.same_job(j))
        if not j.get("posted") and other:
            j["posted"], j["posted_from"] = other["posted"], other.get("source", "")
            from_list += 1
    for j in candidates.values():
        pipeline.date_provenance(j, lists)
    print(f"   {len(undated)} postings had no posted date: {on_page} found on their own page ({len(look)} opened), "
          f"{from_list} from another list, {sum(1 for j in undated if not j.get('posted'))} still unknown")

    # Everything this run read goes in the history, the lists' closed postings and
    # ones that won't make the page included: they still show when roles get posted
    n_hist = sum(history.add_list_items(hist, items, keep, name) for name, items in LIST_ITEMS.items())
    n_hist += history.add_jobs(hist, raw, keep, skip_sources=set(LIST_ITEMS))
    print(f"   {n_hist} postings added to the history ({len(hist['rows'])} in all)")

    # 4) Basic checks with the description, then fit scores (a low score never drops a posting)
    scored = []
    descriptions = {}
    for j in candidates.values():
        analysis, why = matcher.analyze(j)
        if analysis is None:
            reject(j, why, "basic checks")
            continue
        descriptions[j["key"]] = j.get("description", "")
        scored.append({k: v for k, v in j.items() if k not in ("description", "season_hint", "emp_type")} | analysis)
    print(f"4) {len(scored)} postings pass the basic checks "
          f"({sum(1 for j in scored if len(j['tracks']) > 1)} in a curated tab). Dropped: "
          + ", ".join(f"{v} {k}" for k, v in sorted(drops["basic checks"].items())))

    # The lists and job boards keep some postings for days after the company takes them
    # down, so each one that made the page is checked with its own hiring system first
    # (company career sites only list open postings)
    from_lists = [j for j in scored if j.get("source_id") in lists and not j.get("lead")]
    with ThreadPoolExecutor(max_workers=8) as pool:
        closed = {j["key"] for j, gone in zip(from_lists, pool.map(lambda j: posting_closed(j["url"]), from_lists))
                  if gone}
    for j in scored:
        if j["key"] in closed:
            reject(j, "closed on the company's own site (still on a list)", "other")
    scored = [j for j in scored if j["key"] not in closed]
    print(f"   {len(closed)} of {len(from_lists)} postings from lists dropped: closed on the company's own site")

    # 5) Merge with the last run: first-seen dates survive, and postings from sources that
    # failed or were cut short stay (marked stale) until they pass the age limit
    seen = pipeline.load_seen(SEEN_FILE)
    states = {s["name"]: ("skipped" if s.get("waiting") else "failed" if not s["ok"]
                          else "partial" if not s.get("complete", True) else "ok") for s in status}
    final = pipeline.merge(scored, old, states, seen, today, stamp, max_age)
    n_stale = sum(1 for j in final if j.get("stale"))
    print(f"5) {len(final)} postings on the page ({n_stale} kept from sources that failed or were cut short)")

    # 6) Optional Claude reviews
    ai_cache = load_json(AI_FILE, {})
    n = review_jobs(final, descriptions, profile, ai_cache)
    if n:
        print(f"6) Claude reviewed {n} postings")
    for j in final:
        if j["key"] in ai_cache:
            j["ai"] = ai_cache[j["key"]]
        j["geo"] = place_info(j.get("location", ""), home)

    final.sort(key=lambda j: (-j["score"], j["company"]))

    # 7) Save
    keep_keys = {j["key"] for j in final}
    save_json(JOBS_FILE, {"updated": stamp, "jobs": final})
    save_json(DESC_FILE, {k: v for k, v in desc_cache.items() if k in keep_keys or k in candidates})
    save_json(AI_FILE, {k: v for k, v in ai_cache.items() if k in keep_keys})
    save_json(MISS_FILE, {k: v for k, v in misses.items() if k in candidates})
    save_json(DATE_MISS_FILE, {k: v for k, v in date_misses.items() if k in candidates})
    pipeline.remember(seen, final, today)
    pipeline.prune_seen(seen, today)
    pipeline.save_seen(SEEN_FILE, seen)
    health.save(HEALTH_FILE, health_db)
    save_json(STATUS_FILE, status)
    save_json(REJECT_FILE, {"date": today, "read": len(raw), "kept": len(final),
                            "counts": {stage: dict(c.most_common()) for stage, c in drops.items()},
                            "examples": examples})
    seen_pop = load_json(POPULAR_FILE, {})
    big = popular.build(sources_cfg.get("popular", []), final, seen_pop, today, str(profile["search"].get("year", "")))
    save_json(POPULAR_FILE, seen_pop)
    # A Big names company whose sources failed or were cut short isn't "nothing posted"
    rank = {"ok": 0, "partial": 1, "failed": 2, "stale": 3}
    for p in big:
        mine = [s for s in status if s.get("state") in rank and any(
            s["name"].lower() == t[1:] if t.startswith("=") else t in s["name"].lower() for t in p["match"])]
        if mine:
            worst = max(mine, key=lambda s: rank[s["state"]])
            p["scan"] = worst["state"]
            if worst["state"] != "ok":
                p["scan_note"] = f"{worst['name']}: " + (worst.get("error") or "; ".join(worst.get("notes") or []))[:140]

    # 8) Predicted internships: past cycles' roles and when each should be posted this cycle
    year = int(profile["search"].get("year", 2027))
    targets = [(s.lower(), year) for s in profile.get("predict", {}).get("seasons", ["summer", "fall"])]
    links = predict.careers_links(sources_cfg, found, EMPLOYERS)
    preds, timing = predict.build(hist, final, today, targets, EMPLOYERS, matcher, links,
                                  home, float(fa.get("radius_miles", 0)))
    predict.for_popular(big, timing)
    history.prune(hist, today)
    history.save(HISTORY_FILE, hist)
    pstates = ", ".join(f"{sum(1 for p in preds if p['st'] == s)} {s}" for s in ("upcoming", "due", "late", "posted"))
    print(f"8) {len(preds)} roles predicted from {len(hist['rows'])} past and current postings ({pstates})")

    # 9) Programs (NASA OSTEM, NREIP, AFRL Scholars, SULI...): re-check each official page
    prog_state = load_json(PROGRAMS_STATE, {})
    programs.check(program_cfg, prog_state, stamp)
    programs.save(PROGRAMS_STATE, prog_state)
    prog_rows = programs.rows(program_cfg, prog_state, today)
    print(f"9) {len(prog_rows)} programs checked ({sum(1 for r in prog_rows if r['changed'])} pages changed "
          f"since verified)")

    # 10) Coverage audit on a rotating sample of boards (skipped when the run is long)
    audit_data = audit.load(AUDIT_FILE)
    status_by = {s["name"]: s for s in status}
    if minutes() < BUDGET_MINUTES:
        tasks = source_tasks(scan_cfg, keep_fetch)
        sample = audit.pick(tasks, status_by, audit_data, per_run=2)
        cands = sorted(((e.get("label") or e["name"], "candidate", e["kind"], e, None) for e in found.values()
                        if e.get("state") == "candidate" and (e.get("label") or e["name"]) not in status_by
                        and e["kind"] in audit.FULL_LIST | audit.SEARCHED | {"workday"}),
                       key=lambda t: audit_data["audited"].get(t[0], ""))[:1]
        raw_keys: dict[str, set] = {}
        for j in raw:
            if j.get("key"):
                raw_keys.setdefault(j.get("source_id", ""), set()).add(j["key"])
        ctx = {"status": status_by, "fate": fate, "final_keys": keep_keys, "raw_keys": raw_keys,
               "final_same": {pipeline.same_str(j) for j in final}, "candidates": {t[0] for t in cands}}
        rep = audit.run(sample + cands, ctx, matcher, today, max_age)
        audit_sum = audit.record(audit_data, rep, today)
        print(f"10) audited {', '.join(b['source'] for b in rep['boards'])}: "
              + "; ".join(f"{b['found']}/{b['in_scope']} in scope found" if 'error' not in b else 'failed'
                          for b in rep["boards"]))
    else:
        audit_sum = audit.record(audit_data, {"date": today, "boards": []}, today)
        print(f"10) coverage audit skipped ({minutes():.1f} min used)")
    audit.save(AUDIT_FILE, audit_data)

    # 11) Daily digest: always previewed, sent only when turned on (see digest.py)
    log = digest.load_log(NOTIFY_LOG)
    names = {k: v["tab"] for k, v in track_info(profile).items()}
    d = digest.build(final, status, programs.upcoming_deadlines(prog_rows), log, now, PAGE_URL, names)
    DIGEST_FILE.write_text(d["text"] + "\n", encoding="utf-8")
    try:
        from zoneinfo import ZoneInfo
        now_et = now.astimezone(ZoneInfo("America/New_York"))
    except Exception:  # noqa: BLE001
        now_et = now - dt.timedelta(hours=5)
    send, why = digest.should_send(profile.get("notify", {}), log, now_et)
    if send:
        errors = digest.deliver(d, log, now, now_et.date().isoformat())
        why = "sent" + (f" with errors: {', '.join(errors)}" if errors else "")
        digest.prune(log, today)
        digest.save_log(NOTIFY_LOG, log)
    print(f"11) digest: {d['relevant']} new in curated tabs, {d['new']} new in all; delivery {why}")

    # 12) Discovery report, then the page and README
    disc_report = discover.report(found, today, probe_added + replaced, unsupported, disc_state, len(probe_names))
    disc_state["report"] = disc_report
    save_json(DISCOVERY_FILE, disc_state)
    save_json(FOUND_FILE, dict(sorted(found.items())))
    pred_info = {"postings": len(hist["rows"]), "since": min((r["d"] for r in hist["rows"].values()), default=today),
                 "terms": [f"{s} {y}" for s, y in targets]}
    extras = {
        "coverage": cov,
        "discovery": disc_report,
        "programs": prog_rows,
        "audit": audit_sum,
        "rejections": {stage: dict(c.most_common(12)) for stage, c in drops.items()},
        "read": len(raw),
        "digest": {"enabled": bool(profile.get("notify", {}).get("enabled")), "status": why,
                   "channels": digest.channels()},
    }
    (ROOT / "docs").mkdir(exist_ok=True)
    (ROOT / "docs" / "index.html").write_text(build_page(final, status, profile, now, big, preds, pred_info, extras),
                                              encoding="utf-8")
    update_readme(ROOT / "README.md", final, PAGE_URL, now, preds=preds)
    new_today = sum(1 for j in final if j["first_seen"] == today)
    per = ", ".join(f"{sum(1 for j in final if t in j['tracks'])} {t}" for t in [*matcher.tracks, "all"])
    print(f"Done in {minutes():.1f} min: {len(final)} postings on the page ({per}), {new_today} found today.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
