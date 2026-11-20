"""How each source has been doing across runs (data/source_health.json), so the page can
say which sources worked, which were cut short, which failed, and which haven't worked in
a while, instead of a failed scan looking like "no internships".

Per source: last attempt, last success, last complete scan, failures in a row, the last
error, and the last dozen runs' results. A source whose count suddenly drops to zero (or
by most of its usual size) is flagged as suspicious: the site may have changed.

States on the page:
  ok       read completely this run
  partial  read, but something cut the scan short (see its notes)
  failed   failed this run; it worked within the last day
  stale    failed or was skipped this run, and hasn't worked for over a day
  off      needs setup (an API key) before it can run
"""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from statistics import median

STALE_HOURS = 24
HISTORY_RUNS = 12
FORGET_DAYS = 45  # drop sources not attempted in this long (removed from sources.toml)


def load(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, ValueError):
        return {}


def save(path: Path, health: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = ",\n".join(f"{json.dumps(k)}: {json.dumps(v, ensure_ascii=False, separators=(',', ':'))}"
                      for k, v in sorted(health.items()))
    path.write_text("{\n" + rows + "\n}\n", encoding="utf-8")


def _hours(a: str, b: str) -> float:
    try:
        return (dt.datetime.fromisoformat(a) - dt.datetime.fromisoformat(b)).total_seconds() / 3600
    except (TypeError, ValueError):
        return 1e9


def suspicious(runs: list, count: int) -> str:
    """A warning when this run's count falls far below the source's usual size."""
    usual = [r[2] for r in runs if r[1] in ("ok", "partial")][-6:]
    if len(usual) < 2:
        return ""
    m = median(usual)
    if m >= 5 and count == 0:
        return f"dropped from about {round(m)} postings to 0"
    if m >= 20 and count < 0.2 * m:
        return f"dropped from about {round(m)} postings to {count}"
    return ""


def update(health: dict, status: list[dict], stamp: str) -> None:
    """Fold this run's statuses into health, and give each status its state, last success,
    last complete scan, failures in a row, and any suspicious drop."""
    for s in status:
        rec = health.setdefault(s["name"], {"fails": 0, "runs": []})
        rec["kind"] = s.get("kind", "")
        if s.get("careers"):
            rec["careers"] = s["careers"]
        if str(s.get("error", "")).startswith("skipped:") and not s.get("waiting"):
            code = "off"
        elif s.get("waiting"):
            code = "skip"
        elif not s["ok"]:
            code = "fail"
        else:
            code = "ok" if s.get("complete", True) else "partial"
        if code != "skip":
            rec["last_attempt"] = stamp
            rec.setdefault("first_attempt", stamp)
        if code in ("ok", "partial"):
            warn = suspicious(rec["runs"], s.get("count", 0))
            rec["last_success"] = stamp
            if code == "ok":
                rec["last_complete"] = stamp
            rec["fails"] = 0
            rec.pop("error", None)
            if warn:
                s["suspicious"] = warn
        elif code == "fail":
            rec["fails"] = rec.get("fails", 0) + 1
            rec["error"] = s.get("error", "")
        if code != "skip":
            rec["runs"] = (rec["runs"] + [[stamp[:16], code, s.get("count", 0)]])[-HISTORY_RUNS:]
        # What the page shows
        if code == "off":
            state = "off"
        elif code in ("ok", "partial"):
            state = code
        elif _hours(stamp, rec.get("last_success") or rec.get("first_attempt", stamp)) <= STALE_HOURS:
            state = "failed"  # worked within the last day (or was first tried less than a day ago)
        else:
            state = "stale"
        s["state"] = state
        s["last_success"] = rec.get("last_success", "")
        s["last_complete"] = rec.get("last_complete", "")
        s["fails"] = rec.get("fails", 0)
        if code == "skip" and rec.get("error") and not s.get("error"):
            s["error"] = rec["error"]
    names = {s["name"] for s in status}
    for name in list(health):
        if name not in names and _hours(stamp, health[name].get("last_attempt", "")) > FORGET_DAYS * 24:
            del health[name]


def summary(status: list[dict]) -> dict:
    """Counts by state, plus the sources needing attention, for the page's coverage line."""
    counts = {k: 0 for k in ("ok", "partial", "failed", "stale", "off")}
    for s in status:
        counts[s.get("state", "ok")] = counts.get(s.get("state", "ok"), 0) + 1
    return {"counts": counts, "suspicious": sum(1 for s in status if s.get("suspicious")),
            "postings": sum(s.get("count", 0) for s in status)}
