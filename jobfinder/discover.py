"""Find more company career sites automatically.

Postings on the big lists link to each company's own hiring system. When an
aerospace company's link points at a system the scan can read, its whole career
site is scanned from then on, so a company only has to show up on a list once
(this year's or last year's). Found sites are saved in data/discovered_boards.json.
"""
from __future__ import annotations

import datetime as dt
import re

from .sources import BOARD_KINDS
from .util import FetchError, get_json, parse_ats_url

KINDS = ("greenhouse", "lever", "ashby", "workday", "successfactors", "oracle", "jibe")
FORGET_DAYS = 365  # stop scanning a found site no list has linked to in this long
MAX_FAILS = 8      # ...or one that failed this many runs in a row (about two days)

_ORACLE = re.compile(r"https://([\w.-]+\.oraclecloud\.com)/hcmUI/CandidateExperience/[\w-]+/sites/([^/?#]+)/job/")
_SF = re.compile(r"https://([\w.-]+)/job/[^/?#]+/\d+/?\?(?:.*&)?ats=successfactors")
_JIBE = re.compile(r"https://([\w.-]+)/jobs/\d+\?(?:.*&)?icims=1")


def site_of(url: str) -> tuple[str, dict] | None:
    """(key, sources.toml-style entry without a name) for a posting link, or None."""
    info = parse_ats_url(url)
    if info and info["ats"] in ("greenhouse", "lever", "ashby"):
        return f"{info['ats']}:{info['board'].lower()}", {"kind": info["ats"], "board": info["board"]}
    if info and info["ats"] == "workday":
        if re.search(r"(?i)private|restricted|internal", info["site"]):
            return None  # hidden sites for employees or special hiring
        return (f"workday:{info['host'].lower()}/{info['site'].lower()}",
                {"kind": "workday", "host": info["host"], "site": info["site"]})
    m = _ORACLE.match(url)
    if m:
        return f"oracle:{m.group(1).lower()}/{m.group(2).lower()}", {"kind": "oracle", "host": m.group(1), "site": m.group(2)}
    m = _SF.match(url)
    if m:
        return f"successfactors:{m.group(1).lower()}", {"kind": "successfactors", "host": m.group(1)}
    m = _JIBE.match(url)
    if m:
        return f"jibe:{m.group(1).lower()}", {"kind": "jibe", "host": m.group(1)}
    return None


def _configured(cfg: dict) -> tuple[set[str], set[str], set[str]]:
    """Keys, company names and hosts of the sites already listed in sources.toml
    (any board type, so a company read through iCIMS or Taleo isn't added twice)."""
    keys, names, hosts = set(), set(), set()
    for kind in BOARD_KINDS:
        for c in cfg.get(kind, []):
            names.add(c["name"].lower())
            hosts.add(c.get("host", "").lower())
            if "board" in c:
                keys.add(f"{kind}:{c['board'].lower()}")
            elif "site" in c:
                keys.add(f"{kind}:{c['host'].lower()}/{c['site'].lower()}")
            elif "host" in c:
                keys.add(f"{kind}:{c['host'].lower()}")
    hosts.discard("")
    return keys, names, hosts


def learn(found: dict, postings, is_aero, today: str) -> int:
    """Record the career sites behind aerospace companies' list postings.
    postings: (company, url) pairs. Returns how many sites are new."""
    new = 0
    for company, url in postings:
        if not company or not is_aero(company):
            continue
        site = site_of(url)
        if not site:
            continue
        key, entry = site
        if key not in found:
            found[key] = {**entry, "name": company.strip(), "first_seen": today, "fails": 0}
            new += 1
        found[key]["last_seen"] = today
    return new


def learn_from_lists(found: dict, urls: list[str], is_aero, today: str) -> int:
    """Older or full copies of the internship lists, closed postings included."""
    new = 0
    for url in urls:
        try:
            data = get_json(url, timeout=60)
        except (FetchError, ValueError):
            continue
        new += learn(found, ((it.get("company_name", ""), it.get("url", "")) for it in data), is_aero, today)
    return new


def as_sources(found: dict, cfg: dict, today: str) -> dict[str, list[dict]]:
    """The found sites to scan this run, as sources.toml-style lists."""
    keys, names, hosts = _configured(cfg)
    out: dict[str, list[dict]] = {k: [] for k in KINDS}
    now = dt.date.fromisoformat(today)
    for key, e in list(found.items()):
        stale = (now - dt.date.fromisoformat(e.get("last_seen", today))).days > FORGET_DAYS
        if stale or e.get("fails", 0) >= MAX_FAILS:
            del found[key]
            continue
        # Skip sites sources.toml already scans, and extra sites of companies
        # already scanned (same name or same Workday/Oracle account)
        if key in keys or e["name"].lower() in names or e.get("host", "").lower() in hosts:
            continue
        names.add(e["name"].lower())
        out[e["kind"]].append({k: v for k, v in e.items() if k in ("name", "board", "host", "site")})
    return {k: v for k, v in out.items() if v}


def record_results(found: dict, status: list[dict]) -> None:
    """Count failures so dead sites drop out on their own."""
    by_name = {e["name"]: e for e in found.values()}
    for s in status:
        e = by_name.get(s["name"])
        if e is not None:
            e["fails"] = 0 if s["ok"] else e.get("fails", 0) + 1
