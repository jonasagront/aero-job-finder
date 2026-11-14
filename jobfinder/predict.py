"""Predicted internships: roles posted in past cycles that should come back this
cycle, and when.

Each past posting date moves forward to this cycle (a role posted Sep 10, 2025
for Summer 2026 is expected around Sep 10, 2026 for Summer 2027); with several
past cycles the middle date is used. A role counts as posted once this cycle has
a posting from the same company with a similar title. The dates come from
data/history.json (see history.py).
"""
from __future__ import annotations

import datetime as dt
import re
import urllib.parse
from collections import defaultdict

from .geo import nearest

LOOKBACK = 3    # past cycles used
DUE_AHEAD = 7   # a role expected within this many days counts as due now...
DUE_LATE = 21   # ...and so does one expected up to this many days ago
SIMILAR = 0.6   # share of title words two postings must have in common to be one role

_SUFFIX = {"inc", "llc", "ltd", "corp", "corporation", "company", "co", "the", "technologies", "technology",
           "industries", "usa", "us", "america", "americas", "group", "holdings", "international", "plc",
           "lp", "llp", "gmbh", "ag", "sa"}
_STOP = {"and", "of", "the", "for", "in", "at", "to", "a", "an", "with", "on", "or", "by", "us", "usa"}
_MONTHS = (r"(?:january|february|march|april|may|june|july|august|september|october|november|december|"
           r"jan|feb|mar|apr|jun|jul|aug|sep|sept|oct|nov|dec)")
# Words that change from year to year or say nothing about the work
_DROP = re.compile(
    r"(?i)(?<![a-z0-9])(summer|fall|autumn|spring|winter|20\d\d|intern(?:ship)?s?|co-?ops?|co op|students?|"
    r"program|paid|onsite|on-site|hybrid|remote|undergraduate|undergrad|college|collegiate|associate|seasonal|"
    r"temporary|full[- ]time|part[- ]time|u\.?\s?s\.?\s(?:person|citizen)s?|required|only|position|"
    r"opportunit(?:y|ies)|level|i{1,3}|iv|\d{1,2}[- ](?:week|month)s?|" + _MONTHS + r"|"
    r"r-?\d{3,}|jr\d+|\d{3,})(?![a-z0-9])")  # months, requisition numbers
_TERM = re.compile(r"(Summer|Fall|Spring|Winter) (\d{4})$")
_STARTS = {"winter": 2, "spring": 4, "summer": 7, "fall": 10}  # postings go up before this month


def _norm(s) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).strip()


def company_key(name: str, employers: list[tuple[str, str]]) -> str:
    """One name per employer: "The Boeing Company" and "Boeing" are the same, and
    the [same_company] names in sources.toml ("Raytheon" for RTX) count too."""
    co = _norm(name)
    for piece, employer in employers:
        exact = piece.startswith("=")
        if (exact and co == piece[1:]) or (not exact and f" {piece} " in f" {co} "):
            return employer
    return " ".join(w for w in co.split() if w not in _SUFFIX) or co


def _stem(w: str) -> str:
    if len(w) > 5 and w.endswith("ing"):
        w = w[:-3]
    if len(w) > 4 and w.endswith("ies"):
        return w[:-3] + "y"
    return w[:-1] if len(w) > 3 and w.endswith("s") and not w.endswith("ss") else w


def role_words(title: str) -> frozenset:
    """The words of a title that say what the work is ("Propulsion Engineering
    Intern - Summer 2026" -> {propulsion, engineer})."""
    return frozenset(_stem(w) for w in re.findall(r"[a-z0-9&+]+", _DROP.sub(" ", (title or "").lower()))
                     if w not in _STOP and len(w) > 1)


def similar(a: frozenset, b: frozenset) -> bool:
    if not a or not b:
        return a == b
    both = len(a & b)
    return both / len(a | b) >= SIMILAR or (both == min(len(a), len(b)) and both >= 2)


def cycles(row: dict) -> list[tuple[str, int]]:
    """The (season, year) terms a posting was for: the ones it named, or else the
    summer whose hiring season (July to June) it was posted in. A term that had
    already started, or was more than a year off, when the posting went up is a
    list's typo and is skipped."""
    out = []
    y, mo = int(row["d"][:4]), int(row["d"][5:7])
    for part in (row.get("s") or "").split(", "):
        m = _TERM.match(part.strip())
        if not m:
            continue
        season, year = m.group(1).lower(), int(m.group(2))
        if y <= year <= y + 1 and row["d"] < f"{year}-{_STARTS[season]:02d}-01":
            out.append((season, year))
    if not out and not row.get("s"):
        out.append(("summer", y + 1 if mo >= 7 else y))
    return out


_NAME_DROP = re.compile(r"(?i)\s*(?:\b(?:summer|fall|autumn|spring|winter)\s*'?(?:20)?\d\d\b|"
                        r"\b" + _MONTHS + r"\.?\s+20\d\d\b|\b20\d\d\b|"
                        r"\bR-?\d{3,}\b|\bJR\d+\b|\((?:\s|/|,|-)*\))")


def role_name(title: str) -> str:
    """A title without its year, season, or requisition number, for showing a role
    that isn't posted yet ("Autonomy Test Intern - Summer 2024 - R2336" -> "Autonomy Test Intern")."""
    t = _NAME_DROP.sub(" ", title or "")
    t = re.sub(r"\(\s*[-–/,:|\s]*\)", " ", t)
    t = re.sub(r"\s*[-–|:,/]\s*(?=[-–|:,/]|$)", " ", t)  # separators left with nothing after them
    t = re.sub(r"^\s*[-–|:,/]\s*", "", t)
    return re.sub(r"\s+", " ", t).strip(" -–|:,/") or (title or "").strip()


def _shift(iso: str, years: int) -> dt.date:
    d = dt.date.fromisoformat(iso)
    try:
        return d.replace(year=d.year + years)
    except ValueError:  # Feb 29
        return d.replace(year=d.year + years, day=28)


def _middle(dates: list[dt.date]) -> dt.date:
    ords = sorted(d.toordinal() for d in dates)
    n = len(ords)
    return dt.date.fromordinal(ords[n // 2] if n % 2 else (ords[n // 2 - 1] + ords[n // 2]) // 2)


def careers_links(cfg: dict, found: dict, employers) -> dict[str, str]:
    """Company key -> the career site the scan reads for it, for roles not posted yet."""
    pages = {
        "greenhouse": lambda c: f"https://job-boards.greenhouse.io/{c['board']}",
        "lever": lambda c: f"https://jobs.lever.co/{c['board']}",
        "ashby": lambda c: f"https://jobs.ashbyhq.com/{c['board']}",
        "workday": lambda c: (f"https://{c['host']}/recruiting/{c['tenant']}/{c['site']}" if c.get("tenant")
                              else f"https://{c['host']}/{c['site']}"),
        "eightfold": lambda c: f"https://{c['host']}/careers",
        "successfactors": lambda c: f"https://{c['host']}/search/?q=intern",
        "icims": lambda c: f"https://{c['host']}/jobs/search?ss=1&searchKeyword=intern",
        "jibe": lambda c: f"https://{c['host']}/jobs?keywords=intern",
        "oracle": lambda c: f"https://{c['host']}/hcmUI/CandidateExperience/en/sites/{c['site']}/requisitions?keyword=intern",
        "phenom": lambda c: f"{c['base'].rstrip('/')}/search-results?keywords=intern",
        "pinpoint": lambda c: f"https://{c['board']}.pinpointhq.com",
        "bamboohr": lambda c: f"https://{c['board']}.bamboohr.com/careers",
        "rippling": lambda c: f"https://ats.rippling.com/{c['board']}/jobs",
        "smartrecruiters": lambda c: f"https://jobs.smartrecruiters.com/{c['board']}",
        "workable": lambda c: f"https://apply.workable.com/{c['board']}",
        "gem": lambda c: f"https://jobs.gem.com/{c['board']}",
        "taleo": lambda c: f"https://{c['host']}/careersection/{c['section']}/jobsearch.ftl",
        "jazzhr": lambda c: f"https://{c['board']}.applytojob.com/apply",
        "searchpage": lambda c: c["search"].format(term="intern", page=1, offset=0),
        "jobsfeed": lambda c: f"https://{c['host']}/jobs/?q=intern",
        "brassring": lambda c: (f"https://sjobs.brassring.com/TGnewUI/Search/Home/Home?partnerid={c['partner']}"
                                f"&siteid={c['sites'][0]}"),
        "adp": lambda c: f"https://workforcenow.adp.com/mascsr/default/mdf/recruitment/recruitment.html?cid={c['cid']}",
        "ukg": lambda c: c["board"],
        "paycor": lambda c: f"https://recruitingbypaycor.com/career/CareerHome.action?clientId={c['client']}",
        "breezy": lambda c: f"https://{c['board']}.breezy.hr",
        "activate": lambda c: f"https://{c['host']}/search/searchjobs?keyword=intern",
        "paylocity": lambda c: f"https://recruiting.paylocity.com/recruiting/jobs/All/{c['board']}",
        "applicantpro": lambda c: f"https://{c['host']}/jobs/",
    }
    out: dict[str, str] = {}
    entries = [(kind, c) for kind in pages for c in cfg.get(kind, [])]
    entries += [(e["kind"], e) for e in found.values() if e.get("kind") in pages]
    for kind, c in entries:
        try:
            out.setdefault(company_key(c["name"], employers), pages[kind](c))
        except (KeyError, IndexError):
            continue
    return out


def _merge_names(keys, scanned) -> dict[str, str]:
    """Key -> the key it's filed under: a company whose name starts with another
    company's whole name ("honeywell aerospace", "honeywell") counts as that one,
    when the shorter name is two words or more or a company the scan reads."""
    out = {}
    for k in sorted(keys, key=len):
        words = k.split()
        for n in range(1, len(words)):
            head = " ".join(words[:n])
            if head in keys and (n >= 2 or head in scanned):
                out[k] = out.get(head, head)
                break
    return out


def build(hist: dict, jobs: list[dict], today: str, targets: list[tuple[str, int]], employers,
          matcher, links: dict[str, str], home=None, radius: float = 0) -> tuple[list[dict], dict]:
    """(rows for the Predicted tab, company key -> per-season timing for Big names).

    targets: the terms to predict, e.g. [("summer", 2027), ("fall", 2027)]."""
    now = dt.date.fromisoformat(today)
    raw: dict[str, list] = defaultdict(list)   # company key -> [(term, posted, words, row)]
    for r in hist["rows"].values():
        words = role_words(r["t"])
        for term in cycles(r):
            raw[company_key(r["c"], employers)].append((term, r["d"], words, r))
    alias = _merge_names(set(raw) | set(links), set(links))
    by_co: dict[str, list] = defaultdict(list)
    for k, entries in raw.items():
        by_co[alias.get(k, k)].extend(entries)
    for k, url in list(links.items()):
        links.setdefault(alias.get(k, k), url)
    on_page: dict[str, list] = defaultdict(list)  # postings open now, for links
    for j in jobs:
        if not j.get("lead"):
            k = company_key(j.get("company", ""), employers)
            on_page[alias.get(k, k)].append((role_words(j.get("title", "")), j))

    rows, timing = [], {}
    for season, year in targets:
        for ck, entries in by_co.items():
            past = sorted((e for e in entries if e[0][0] == season and year - LOOKBACK <= e[0][1] < year),
                          key=lambda e: e[1])
            if not past:
                continue
            this = [e for e in entries if e[0] == (season, year)]
            # When the company's first posting of each cycle went up, and how many it had
            first: dict[int, list] = {}
            for (_, y), d, _, _ in past:
                f = first.setdefault(y, [d, 0])
                f[0], f[1] = min(f[0], d), f[1] + 1
            timing.setdefault(ck, {})[season] = {
                "name": past[-1][3]["c"],
                "past": [[y, d, n] for y, (d, n) in sorted(first.items(), reverse=True)],
                "expect": _middle([_shift(d, year - y) for y, (d, _) in first.items()]).isoformat(),
                "first": min((e[1] for e in this), default=""),
            }
            # Group the company's past postings into roles by title
            roles: list[dict] = []
            for e in past:
                for role in roles:
                    if similar(role["words"], e[2]):
                        role["rows"].append(e)
                        role["words"] = e[2]  # follow the newest title
                        break
                else:
                    roles.append({"words": e[2], "rows": [e]})
            for role in roles:
                earliest: dict[int, tuple] = {}
                for e in role["rows"]:
                    y = e[0][1]
                    if y not in earliest or e[1] < earliest[y][1]:
                        earliest[y] = e
                if max(earliest) < year - 2:
                    continue  # not posted in the last two cycles: probably discontinued
                last = role["rows"][-1][3]
                title = last["t"]
                # The scan's quick title filter lets any "engineer"/"research" title through
                # for possible aerospace companies; elsewhere a role needs an engineering discipline
                disc = matcher.discipline(title)[0]
                aero_co = matcher.is_aero_company(last["c"])
                aero = aero_co and matcher.aero_relevance(title.lower(), "", False, True) is not None
                if not disc and not aero:
                    continue
                motor = matcher.is_motorsport(last["c"], title)
                moved = [_shift(e[1], year - y) for y, e in earliest.items()]
                expect = _middle(moved)
                seen = sorted(e[1] for e in this if similar(role["words"], e[2]))
                # Posted this cycle: link to it while it's still open
                live = next((j for w, j in on_page.get(ck, []) if similar(role["words"], w)), None) if seen else None
                if seen:
                    status = "posted"
                else:
                    ahead = (expect - now).days
                    status = "upcoming" if ahead > DUE_AHEAD else "due" if ahead >= -DUE_LATE else "late"
                near = nearest(last.get("l", ""), home) if home else None
                row = {
                    "co": last["c"],
                    "t": role_name(title),
                    "lt": title,
                    "s": season,
                    "y": year,
                    "exp": expect.isoformat(),
                    "past": [[y, earliest[y][1]] for y in sorted(earliest, reverse=True)],
                    "st": status,
                    "u": (live or {}).get("url") or links.get(ck) or
                         "https://www.google.com/search?q=" + urllib.parse.quote_plus(f"{last['c']} {season} internship"),
                    "loc": last.get("l", "")[:70],
                    "d": disc or "Aerospace",
                }
                if len(moved) > 1:
                    row["lo"], row["hi"] = min(moved).isoformat(), max(moved).isoformat()
                if seen:
                    row["seen"] = seen[0]
                if live:
                    row["key"] = live["key"]
                if last.get("u") and last["u"] != row["u"]:
                    row["last"] = last["u"]
                if aero:
                    row["aero"] = 1
                if motor:
                    row["mo"] = 1
                if near and near[0] <= radius:
                    row["mi"] = round(near[0])
                rows.append(row)
    rows.sort(key=lambda r: (r["exp"], r["co"]))
    return rows, timing


def for_popular(popular: list[dict], timing: dict, season: str = "summer", min_postings: int = 5) -> None:
    """Add each Big names company's past first-posting dates to its row: "past"
    [(cycle year, date, postings that cycle)], and "expect", the predicted opening.
    Cycles where the lists had only a few of its postings say little about when it
    started, so they're left out."""
    for p in popular:
        terms = p.get("match") or [p["name"].lower()]
        hits = [t[season] for t in timing.values() if season in t and
                any(t[season]["name"].lower() == m[1:] if m.startswith("=") else m in t[season]["name"].lower()
                    for m in terms)]
        if not hits:
            continue
        first: dict[int, list] = {}
        for h in hits:
            for y, d, n in h["past"]:
                f = first.setdefault(y, [d, 0])
                f[0], f[1] = min(f[0], d), f[1] + n
        p["past"] = [[y, d, n] for y, (d, n) in sorted(first.items(), reverse=True) if n >= min_postings]
