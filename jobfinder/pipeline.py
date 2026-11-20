"""The parts of a scan that decide what stays on the page between runs:

- same_job: one company + title, to spot the same posting under two links
- seen store (data/seen.json): when each posting was first found, kept after it leaves the
  page, so a posting that drops off (its source failed, a filter changed, a list relisted
  it under a new link) keeps its original first-seen date when it comes back
- date provenance: an employer's own posted date, a list's or job board's date, or none
- merge: this run's postings plus last run's from sources that failed or were cut short
- too_old: the max_age_days rule (from the posted date, else the first-seen date)
"""
from __future__ import annotations

import datetime as dt
import json
import re
from pathlib import Path

SEEN_KEEP_DAYS = 120   # forget a posting this long after it was last on the page
RELIST_DAYS = 21       # a posting under a new link counts as the same one if the old link was seen this recently

_CO_SUFFIX = re.compile(r"\b(inc|llc|corp|corporation|company|co|the|technologies|industries)\b")
# (name piece, employer) pairs from sources.toml [same_company], set by set_employers()
EMPLOYERS: list[tuple[str, str]] = []


def _norm(s) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).strip()


def set_employers(cfg: dict) -> None:
    EMPLOYERS[:] = [(("=" if p.startswith("=") else "") + _norm(p), _norm(employer))
                    for employer, pieces in cfg.get("same_company", {}).items() for p in pieces]


def same_job(j: dict) -> tuple[str, str]:
    """Company + title, loosely, to spot the same posting listed under different links.
    Names one employer goes by ("Raytheon" for RTX's board) count as that employer."""
    co = _norm(j.get("company"))
    for piece, employer in EMPLOYERS:
        exact = piece.startswith("=")
        if (exact and co == piece[1:]) or (not exact and f" {piece} " in f" {co} "):
            co = employer
            break
    words = _CO_SUFFIX.sub("", co).split()
    return (words[0] if words else "", _norm(j.get("title")))


def same_str(j: dict) -> str:
    return "|".join(same_job(j))


# ---------------------------------------------------------------- seen store

def load_seen(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, ValueError):
        data = {}
    data.setdefault("keys", {})
    return data


def save_seen(path: Path, seen: dict) -> None:
    # One posting per line keeps the file's git diffs small
    rows = ",\n".join(f"{json.dumps(k)}: {json.dumps(v, ensure_ascii=False, separators=(',', ':'))}"
                      for k, v in sorted(seen["keys"].items()))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('{"keys": {\n' + rows + "\n}}\n", encoding="utf-8")


def _days(a: str, b: str) -> int:
    try:
        return (dt.date.fromisoformat(a[:10]) - dt.date.fromisoformat(b[:10])).days
    except ValueError:
        return 10 ** 6


def lookup_seen(seen: dict, key: str, same: str, today: str) -> dict | None:
    """The record for this posting: by its key, or else (a relisting under a new link) by
    company + title when that one was on the page in the last RELIST_DAYS days."""
    rec = seen["keys"].get(key)
    if rec:
        return {**rec, "k": key}
    index = seen.get("_same")
    if index is None:  # built once per run
        index = seen["_same"] = {}
        for k, r in seen["keys"].items():
            s = r.get("s")
            if s and (s not in index or r.get("l", "") > seen["keys"][index[s]].get("l", "")):
                index[s] = k
    k = index.get(same)
    if k and _days(today, seen["keys"][k].get("l", "")) <= RELIST_DAYS:
        return {**seen["keys"][k], "k": k}
    return None


def remember(seen: dict, jobs: list[dict], today: str) -> None:
    """Record every posting on the page this run (stale ones keep their last-seen day)."""
    for j in jobs:
        rec = seen["keys"].setdefault(j["key"], {"f": j.get("first_seen") or today, "s": same_str(j)})
        rec["f"] = min(rec.get("f") or today, j.get("first_seen") or today)
        if j.get("found_at") and not rec.get("a"):
            rec["a"] = j["found_at"]
        if not j.get("stale"):
            rec["l"] = today
        rec.setdefault("l", today)
    seen.pop("_same", None)


def prune_seen(seen: dict, today: str) -> None:
    seen["keys"] = {k: v for k, v in seen["keys"].items() if _days(today, v.get("l", today)) <= SEEN_KEEP_DAYS}
    seen.pop("_same", None)


# ---------------------------------------------------------------- posted dates

def date_provenance(j: dict, listing_sources: set[str]) -> None:
    """Say where a posting's date came from (date_kind):
    employer  the company's own hiring system or posting page
    listing   an internship list or job board (posted_from names it); the employer's own
              date is unknown
    none      no date anywhere: the page shows "Posting date unknown" and when it was found"""
    if not j.get("posted"):
        j["date_kind"] = "none"
        j.pop("posted_from", None)
    elif j.get("posted_from"):
        j["date_kind"] = "listing"
    elif j.get("lead") or j.get("source_id") in listing_sources:
        j["date_kind"] = "listing"
        j["posted_from"] = j.get("source") or j.get("source_id", "")
    else:
        j["date_kind"] = "employer"


def too_old(j: dict, today: str, max_age: int) -> bool:
    """Older than max_age days, from the posted date or, with none, the day first found.
    Unchanged from before: max_age_days in profile.toml (15) applies everywhere."""
    since = j.get("posted") or j.get("first_seen") or today
    try:
        return bool(max_age) and (dt.date.fromisoformat(today) - dt.date.fromisoformat(since[:10])).days > max_age
    except ValueError:
        return False


# ---------------------------------------------------------------- merge

STALE_WHY = {
    "failed": "its source failed on the latest scan",
    "partial": "the latest scan of its source was incomplete",
    "skipped": "its source is waiting for a retry",
}


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


def merge(scored: list[dict], old: dict[str, dict], states: dict[str, str], seen: dict,
          today: str, stamp: str, max_age: int) -> list[dict]:
    """This run's postings, with first-seen and found-at carried over, plus last run's postings
    whose source failed, was cut short, or is waiting to be retried (states: source name ->
    ok | partial | failed | skipped). Those are kept, marked stale, until they pass the age
    limit; a posting only counts as closed when it's missing from a complete scan."""
    final = []
    live = {j["key"] for j in scored}
    for j in scored:
        prev = old.get(j["key"]) or {}
        rec = lookup_seen(seen, j["key"], same_str(j), today)
        if rec and rec["k"] != j["key"] and rec["k"] in live:
            rec = None  # another live posting with the same title (a second location), not a relisting
        firsts = [d for d in (prev.get("first_seen"), (rec or {}).get("f")) if d]
        j["first_seen"] = min(firsts) if firsts else today
        # The exact scan that first found it, for New internships and the unread queue
        j["found_at"] = prev.get("found_at") or (rec or {}).get("a") or (None if (prev or rec) else stamp)
        if rec and rec["k"] != j["key"]:
            j["aka"] = [rec["k"]]  # same posting under its old link: the page carries its read/applied state over
        j["last_seen"] = today
        j["checked"] = stamp
        j.pop("stale", None)
        final.append(j)
    current = {j["key"] for j in final}
    for k, j in old.items():
        if k in current:
            continue
        st = states.get(j.get("source_id"))
        if st in STALE_WHY:
            j = upgrade_old(dict(j))
            j["stale"] = {"since": (j.get("checked") or j.get("last_seen") or today)[:10], "why": STALE_WHY[st]}
            final.append(j)
        # else: missing from a complete scan of a working source (closed), or a source no longer read
    return [j for j in final if not too_old(j, today, max_age)]
