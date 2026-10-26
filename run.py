"""Internship scan: Summer 2027 aerospace, Fall 2027 near home, and all engineering.

Run locally with:   python run.py
GitHub Actions runs this every 6 hours and publishes docs/index.html.
"""
from __future__ import annotations

import datetime as dt
import json
import sys
import tomllib
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urlparse

from jobfinder.ai import review_jobs
from jobfinder.match import Matcher
from jobfinder.quals import QualChecker
from jobfinder.render import build_page, update_readme
from jobfinder.sources import fetch_all, fetch_description
from jobfinder.util import FetchError, job_key

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
JOBS_FILE = DATA / "jobs.json"
DESC_FILE = DATA / "descriptions.json"
AI_FILE = DATA / "ai_reviews.json"
MISS_FILE = DATA / "description_misses.json"
PAGE_URL = "https://jonasagront.github.io/aero-job-finder/"

MAX_NEW_LOOKUPS = 500   # full-description lookups per run for list-only postings
KEEP_MISSING_DAYS = 5   # keep a job this long if its source failed to load
RETRY_MISS_DAYS = 7     # wait this long before retrying a page that had no description


def load_json(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, ValueError):
        return default


def save_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8")


def upgrade_old(j: dict) -> dict:
    """Saved results from before the page had sections were all Summer 2027 aerospace."""
    if "tracks" not in j:
        flags = j.get("flags") or []
        label = flags[0]["label"] if flags else ""
        parts = dict(j.get("parts") or {})
        parts["fit"] = parts.pop("aerospace", 0)
        j["tracks"] = {"summer": {"score": j["score"], "tier": j["tier"], "parts": parts,
                                  "season": j.get("season", "unstated"), "season_label": label}}
        j["flags"] = flags[1:]
        j.setdefault("discipline", "Aerospace")
    return j


def main() -> int:
    now = dt.datetime.now(dt.timezone.utc)
    today = now.date().isoformat()
    profile = tomllib.loads((ROOT / "profile.toml").read_text(encoding="utf-8"))
    sources_cfg = tomllib.loads((ROOT / "sources.toml").read_text(encoding="utf-8"))
    matcher = Matcher(profile, sources_cfg)
    matcher.qc = QualChecker(matcher, profile)

    def keep(title: str) -> bool:
        """Internship with an engineering-looking title (any section could use it)."""
        return matcher.title_ok(title)[0] and bool(
            matcher.discipline(title)[0] or matcher.aero_relevance(title.lower(), "", False, True) is not None)

    print("1) Reading job sources")
    raw, status = fetch_all(sources_cfg, keep=keep)
    print(f"   {len(raw)} postings read")

    # Apply links must open the company's own posting, not an AI job site or aggregator
    blocked = tuple(d.lower() for d in sources_cfg.get("blocked_link_domains", []))

    def link_ok(url: str) -> bool:
        host = urlparse(url).netloc.lower()
        return not any(host == d or host.endswith("." + d) for d in blocked)

    # 2) Quick title filter, then de-duplicate across sources
    candidates: dict[str, dict] = {}
    n_blocked = 0
    for j in raw:
        if not j.get("url") or not keep(j.get("title", "")):
            continue
        if not link_ok(j["url"]):
            n_blocked += 1
            continue
        j["key"] = job_key(j["url"], j.get("company", ""), j.get("title", ""))
        prev = candidates.get(j["key"])
        # Prefer the copy that has a description (company board over list)
        if prev is None or (not prev.get("description") and j.get("description")):
            if prev and prev.get("season_hint") and not j.get("season_hint"):
                j["season_hint"] = prev["season_hint"]
            candidates[j["key"]] = j
        elif j.get("season_hint") and not prev.get("season_hint"):
            prev["season_hint"] = j["season_hint"]
    print(f"2) {len(candidates)} engineering internship postings after removing duplicates"
          f" ({n_blocked} skipped for linking to a blocked site)")

    # 3) Fill in descriptions for list postings (cached between runs)
    desc_cache: dict = load_json(DESC_FILE, {})
    misses: dict = load_json(MISS_FILE, {})  # key -> date a lookup last came back empty
    need = [j for j in candidates.values() if not j.get("description")]
    for j in need:
        if j["key"] in desc_cache:
            j["description"] = desc_cache[j["key"]]
    lookup = [j for j in need if not j.get("description")
              and (now.date() - dt.date.fromisoformat(misses.get(j["key"], "2000-01-01"))).days >= RETRY_MISS_DAYS]
    # Look up the most promising ones first: aerospace companies, then mechanical/aerospace titles
    first = ("Aerospace", "Mechanical")
    lookup.sort(key=lambda j: (not matcher.is_aero_company(j.get("company", "")),
                               matcher.discipline(j.get("title", ""))[0] not in first))
    lookup = lookup[:MAX_NEW_LOOKUPS]

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

    # 4) Score
    drops: dict[str, int] = {}
    scored = []
    descriptions = {}
    for j in candidates.values():
        analysis, why = matcher.analyze(j)
        if analysis is None:
            drops[why] = drops.get(why, 0) + 1
            continue
        descriptions[j["key"]] = j.get("description", "")
        scored.append({k: v for k, v in j.items() if k not in ("description", "season_hint")} | analysis)
    print(f"4) {len(scored)} matches. Dropped: " + ", ".join(f"{v} {k}" for k, v in sorted(drops.items())))

    # 5) Merge with yesterday's results (keeps "first seen" dates)
    old = {j["key"]: j for j in load_json(JOBS_FILE, {}).get("jobs", [])}
    failed_sources = {s["name"] for s in status if not s["ok"]}
    final = []
    for j in scored:
        j["first_seen"] = old.get(j["key"], {}).get("first_seen", today)
        j["last_seen"] = today
        final.append(j)
    current = {j["key"] for j in final}
    for k, j in old.items():
        if k in current or j.get("source_id") not in failed_sources:
            continue  # gone from a working source = posting closed
        last = dt.date.fromisoformat(j.get("last_seen", today))
        if (now.date() - last).days <= KEEP_MISSING_DAYS:
            final.append(upgrade_old(j))  # source hiccup: keep for now

    # 6) Optional Claude reviews
    ai_cache = load_json(AI_FILE, {})
    n = review_jobs(final, descriptions, profile, ai_cache)
    if n:
        print(f"6) Claude reviewed {n} postings")
    for j in final:
        if j["key"] in ai_cache:
            j["ai"] = ai_cache[j["key"]]

    final.sort(key=lambda j: (-j["score"], j["company"]))

    # 7) Save + publish
    keep_keys = {j["key"] for j in final}
    save_json(JOBS_FILE, {"updated": now.isoformat(timespec="seconds"), "jobs": final})
    save_json(DESC_FILE, {k: v for k, v in desc_cache.items() if k in keep_keys or k in candidates})
    save_json(AI_FILE, {k: v for k, v in ai_cache.items() if k in keep_keys})
    save_json(MISS_FILE, {k: v for k, v in misses.items() if k in candidates})
    (ROOT / "docs").mkdir(exist_ok=True)
    (ROOT / "docs" / "index.html").write_text(build_page(final, status, profile, now), encoding="utf-8")
    update_readme(ROOT / "README.md", final, PAGE_URL, now)
    new_today = sum(1 for j in final if j["first_seen"] == today)
    per = ", ".join(f"{sum(1 for j in final if t in j['tracks'])} {t}" for t in matcher.tracks)
    print(f"Done: {len(final)} postings on the page ({per}), {new_today} new today.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
