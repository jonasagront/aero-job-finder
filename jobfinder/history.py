"""Every engineering internship posting seen so far, with its posted date, so the
page can predict when this cycle's postings will appear (see predict.py).

data/history.json starts from old copies of the Simplify list, pinned to a commit
in sources.toml [history] and read once, and grows every run with the current
list (closed postings included), the company career sites, and intern-list.com.
Each year's predictions therefore draw on more sites than the year before.

  {"read": [pinned list addresses already read],
   "rows": {id: {"c": company, "t": title, "d": posted, "s": seasons, "l": location,
                 "u": link, "f": where it came from}}}

seasons is like "Summer 2026" or "Spring 2027, Summer 2027", or "" when the
posting never said.
"""
from __future__ import annotations

import datetime as dt
import json
import re
from pathlib import Path

from .match import Matcher, where
from .util import FetchError, get_json

KEEP_YEARS = 4  # rows older than this are dropped
_TERM = re.compile(r"(?i)^(summer|fall|spring|winter)\s+(20\d\d)$")
_ISO = re.compile(r"^20\d\d-\d\d-\d\d$")  # older saved scans hold some unreadable dates


def load(path: Path) -> dict:
    try:
        hist = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, ValueError):
        hist = {}
    hist.setdefault("read", [])
    hist.setdefault("rows", {})
    return hist


def save(path: Path, hist: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    # One row per line keeps the file's git diffs small
    rows = ",\n".join(f"{json.dumps(k)}: {json.dumps(v, ensure_ascii=False, separators=(',', ':'))}"
                      for k, v in sorted(hist["rows"].items()))
    path.write_text('{"read": ' + json.dumps(hist["read"], indent=1) + ',\n"rows": {\n' + rows + "\n}}\n",
                    encoding="utf-8")


def _add(hist: dict, rid: str, company: str, title: str, posted: str, seasons: str,
         location: str, url: str, src: str) -> None:
    if not _ISO.match(posted or "") or not company or not title:
        return
    old = hist["rows"].get(rid)
    if old and old["d"] <= posted:
        if seasons and not old.get("s"):
            old["s"] = seasons
        return
    hist["rows"][rid] = {"c": company.strip(), "t": title.strip(), "d": posted[:10], "s": seasons,
                         "l": re.sub(r"\s+", " ", location or "")[:90], "u": url or "", "f": src}


def _wanted(keep, title: str, location: str) -> bool:
    return keep(title) and where(location) != "foreign"


def _terms(terms) -> str:
    if not isinstance(terms, list):
        terms = [terms] if terms else []
    return ", ".join(t.strip().title() for t in terms if _TERM.match(str(t).strip()))


def add_list_items(hist: dict, items: list[dict], keep, src: str) -> int:
    """Simplify-style list entries (closed ones included)."""
    n = len(hist["rows"])
    for it in items:
        locs = it.get("locations") or []
        loc = "; ".join(locs) if isinstance(locs, list) else str(locs)
        title = it.get("title") or ""
        if not it.get("id") or not _wanted(keep, title, loc):
            continue
        try:
            posted = dt.datetime.fromtimestamp(float(it.get("date_posted")), dt.timezone.utc).date().isoformat()
        except (TypeError, ValueError, OSError):
            continue
        _add(hist, f"sim:{it['id']}", it.get("company_name") or "", title, posted, _terms(it.get("terms")),
             loc, it.get("url") or "", src)
    return len(hist["rows"]) - n


def read_pinned(hist: dict, urls: list[str], keep) -> int:
    """Old copies of the lists, each read once (a pinned commit never changes)."""
    n = 0
    for url in urls:
        if url in hist["read"]:
            continue
        try:
            items = get_json(url, timeout=120)
        except (FetchError, ValueError) as e:
            print(f"   past list not read ({e}): {url}")
            continue
        n += add_list_items(hist, items, keep, "Simplify list (past cycle)")
        hist["read"].append(url)
    return n


def seasons_of(title: str, text: str, posted: str) -> str:
    """Seasons a posting names in its title, else its description ("Summer 2027")."""
    year = int(posted[:4]) + 1 if posted else 2000
    found = Matcher._seasons_named(title, year) or Matcher._seasons_named(text or "", year)
    return ", ".join(f"{s.title()} {y}" for s, y in sorted(found, key=lambda x: (x[1], x[0])))


def add_jobs(hist: dict, jobs, keep, skip_sources=()) -> int:
    """Postings from this run, before scoring, so ones that didn't make the page
    still count as posted. skip_sources: lists already read whole by add_list_items."""
    n = len(hist["rows"])
    for j in jobs:
        if (j.get("source_id") in skip_sources or not _ISO.match(j.get("posted") or "") or not j.get("key")
                or not _wanted(keep, j.get("title", ""), j.get("location", ""))):
            continue
        seasons = _terms(j["season_hint"].split(", ")) if j.get("season_hint") else ""
        seasons = seasons or seasons_of(j.get("title", ""), j.get("description", ""), j["posted"])
        _add(hist, j["key"], j.get("company", ""), j.get("title", ""), j["posted"], seasons, j.get("location", ""),
             "" if j.get("lead") else j.get("url", ""), j.get("source_id") or j.get("source", ""))
    return len(hist["rows"]) - n


def prune(hist: dict, today: str) -> None:
    cut = (dt.date.fromisoformat(today) - dt.timedelta(days=365 * KEEP_YEARS)).isoformat()
    hist["rows"] = {k: v for k, v in hist["rows"].items() if v["d"] >= cut}
