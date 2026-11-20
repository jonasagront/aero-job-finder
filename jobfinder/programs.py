"""The Programs tab: NASA OSTEM, NREIP, AFRL Scholars, SULI and other programs that
aren't a company job board (see programs.toml).

The facts (status, deadlines, eligibility) are the ones read on each program's official
page and written into programs.toml with the date they were verified; nothing here makes
up a date. Each run re-reads every page it can and records when it last checked, whether
the page loaded, and whether its text changed since the first check after verification,
so a changed page shows "re-check" instead of silently going stale. Deadlines that have
passed show as passed. data/programs.json keeps the check results.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from .util import FetchError, html_to_text, request

_PAGE_HEADERS = {"Accept": "text/html", "User-Agent": "Mozilla/5.0 (compatible; aero-job-finder)"}
_DATE = re.compile(r"(?i)\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\.? \d{1,2}(?:st|nd|rd|th)?,? 20\d\d\b")


def load(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, ValueError):
        return {}


def save(path: Path, state: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=1, ensure_ascii=False), encoding="utf-8")


def _page_text(url: str) -> str:
    raw = request(url, headers=_PAGE_HEADERS, timeout=25, retries=1)
    raw = re.sub(r"(?is)<(script|style|noscript|svg)\b.*?</\1>", " ", raw)
    return re.sub(r"\s+", " ", html_to_text(raw))


def check(programs: list[dict], state: dict, stamp: str) -> None:
    """Re-read each program's page (state: name -> check record, updated in place)."""
    def one(p):
        if p.get("check") is False:
            return p, None, "not checked automatically (the site blocks scripts or needs a browser)"
        try:
            return p, _page_text(p["url"]), ""
        except FetchError as e:
            return p, None, f"page didn't load ({e})"

    with ThreadPoolExecutor(max_workers=6) as pool:
        results = list(pool.map(one, programs))
    for p, text, err in results:
        rec = state.setdefault(p["name"], {})
        rec["checked"] = stamp
        if text is None:
            rec["ok"] = False
            rec["error"] = err
            continue
        digest = hashlib.sha256(text.encode()).hexdigest()[:16]
        # The first look after a (re)verification is the baseline
        if rec.get("verified") != p.get("verified") or not rec.get("baseline"):
            rec.update(verified=p.get("verified"), baseline=digest, changed="")
        elif digest != rec.get("hash") and digest != rec["baseline"]:
            rec["changed"] = rec.get("changed") or stamp[:10]
        elif digest == rec["baseline"]:
            rec["changed"] = ""
        rec.update(ok=True, hash=digest, error="")
        # Dates the page mentions now, with a little context, as a hint of what changed
        rec["dates_seen"] = list(dict.fromkeys(
            text[max(0, m.start() - 60):m.end() + 10].strip() for m in _DATE.finditer(text)))[:8]


def rows(programs: list[dict], state: dict, today: str) -> list[dict]:
    """Program records for the page, with each deadline marked passed or not."""
    out = []
    for p in programs:
        rec = state.get(p["name"], {})
        deadlines = []
        for d in p.get("deadlines", []):
            try:
                days = (dt.date.fromisoformat(d["date"]) - dt.date.fromisoformat(today)).days
            except (KeyError, ValueError):
                continue
            deadlines.append({**d, "days": days, "passed": days < 0})
        status = p.get("status", "unverified")
        upcoming = [d for d in deadlines if not d["passed"]]
        if status in ("open", "published") and deadlines and not upcoming:
            status = "closed"  # every deadline the page gave has passed
        out.append({
            "name": p["name"], "sponsor": p.get("sponsor", ""), "url": p["url"], "apply": p.get("apply", p["url"]),
            "terms": p.get("terms", []), "status": status, "status_note": p.get("status_note", ""),
            "eligibility": p.get("eligibility", ""), "verified": p.get("verified", ""),
            "page_updated": p.get("page_updated", ""), "estimate": p.get("estimate", ""), "deadlines": deadlines,
            "checked": rec.get("checked", ""), "check_ok": rec.get("ok"), "check_error": rec.get("error", ""),
            "changed": rec.get("changed", ""), "dates_seen": rec.get("dates_seen", []),
        })
    order = {"open": 0, "published": 1, "not-yet": 2, "unverified": 3, "closed": 4}
    out.sort(key=lambda r: (order.get(r["status"], 5),
                            min((d["date"] for d in r["deadlines"] if not d["passed"]), default="9999")))
    return out


def upcoming_deadlines(rows_: list[dict], within_days: int = 21) -> list[dict]:
    """Verified deadlines in the next within_days days, soonest first (for the digest)."""
    out = [{"program": r["name"], "term": d["term"], "date": d["date"], "days": d["days"], "url": r["apply"]}
           for r in rows_ for d in r["deadlines"] if 0 <= d["days"] <= within_days]
    return sorted(out, key=lambda d: d["date"])
