"""The "Big names" section: well-known employers, when they usually recruit,
and what this cycle's scans have seen from each.

The usual windows come from [[popular]] in sources.toml (hand-written, based on
past cycles). The live part (open now, first seen this cycle) comes from the
scan, and is remembered in data/popular_seen.json so a company's first posting
date survives after that posting closes.
"""
from __future__ import annotations


def _matches(company: str, terms: list[str]) -> bool:
    c = company.lower()
    return any(c == t[1:] if t.startswith("=") else t in c for t in terms)


def build(cfg: list[dict], jobs: list[dict], seen: dict, today: str, cycle: str) -> list[dict]:
    """Rows for the page. Updates `seen` in place (company -> first/last dates this cycle)."""
    rows = []
    for p in cfg:
        terms = [t.lower() for t in p.get("match", [p["name"]])]
        mine = [j for j in jobs if _matches(j.get("company", ""), terms)]
        dates = sorted((j.get("posted") or j.get("first_seen") or today) for j in mine)
        rec = seen.get(p["name"])
        if not rec or rec.get("cycle") != cycle:
            rec = {"cycle": cycle, "first_seen": "", "last_seen": "", "most_open": 0}
        if dates:
            rec["first_seen"] = min(filter(None, [rec["first_seen"], dates[0]]))
            rec["last_seen"] = max(rec["last_seen"], dates[-1])
        rec["most_open"] = max(rec["most_open"], len(mine))
        seen[p["name"]] = rec
        window = p.get("window") or []
        rows.append({
            "name": p["name"],
            "match": terms,
            "careers": p.get("careers", ""),
            "window": window if len(window) == 2 else [],
            "dates": p.get("dates", ""),
            "note": p.get("note", ""),
            "scanned": p.get("scanned", True),
            "first_seen": rec["first_seen"],
            "most_open": rec["most_open"],
        })
    return rows
