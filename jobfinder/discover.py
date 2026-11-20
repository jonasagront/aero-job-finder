"""Find more company career sites automatically, and keep the ones that break.

Where boards come from (each saved entry's "via" says which):
- List links: postings on the big lists link to each company's own hiring system. An
  aerospace or motorsport company's board is scanned from its first such link (this cycle
  or any earlier one in data/history.json). Other employers' boards are scanned once they've
  listed engineering_min aerospace/mechanical internships in the past 15 months; with fewer,
  the board waits in a candidate queue and a few candidates are tried each run. A candidate
  that answers is validated and kept.
- Name probes: names from [aerospace_companies], [motorsport_companies] and [discover] seeds
  that have no board yet are looked up on hiring systems with public APIs (Greenhouse, Lever,
  Ashby, SmartRecruiters, Workable), a few names per run. A board only counts when the
  system's own company name (or the postings' text) matches.

Boards are told apart by their address, not the company name, so a company's separate
boards (Relativity's intern board, GDIT's early-talent site) are all read; postings that
appear on two of them are merged later by their job ID.

Repair queue: a board that fails is retried every run three times, then after 1, 2, 4, 8
and at most 14 days, forever (it isn't deleted). While it fails, links to the same company
on another hiring system mean it moved, and the new board takes over. Every entry keeps a
link to its career site for checking by hand.
"""
from __future__ import annotations

import datetime as dt
import re
from concurrent.futures import ThreadPoolExecutor

from .sources import BOARD_KINDS, board_url
from .util import FetchError, get_json, parse_ats_url

FORGET_DAYS = 450   # stop scanning a list-linked site no list has linked to in this long
RETRY_FREE = 3      # failing runs retried right away before backing off
MAX_WAIT_DAYS = 14
CANDIDATES_PER_RUN = 12
PROBES_PER_RUN = 12
REPROBE_DAYS = 60

# Boards site_of can recognize, and the fields each needs in sources.toml terms
KINDS = ("greenhouse", "lever", "ashby", "workday", "successfactors", "oracle", "jibe", "icims",
         "smartrecruiters", "workable", "bamboohr", "rippling", "breezy", "jazzhr", "pinpoint", "gem",
         "adp", "ukg", "brassring", "applicantpro")
_FIELDS = ("name", "board", "host", "site", "tenant", "cid", "partner", "sites")

_ORACLE = re.compile(r"https://([\w.-]+\.oraclecloud\.com)/hcmUI/CandidateExperience/[\w-]+/sites/([^/?#]+)/job/")
_SF = re.compile(r"https://([\w.-]+)/job/[^/?#]+/\d+/?\?(?:.*&)?ats=successfactors")
_JIBE = re.compile(r"https://([\w.-]+)/jobs/\d+\?(?:.*&)?icims=1")
_ICIMS = re.compile(r"https://([\w-]+\.icims\.com)/jobs/\d+")
_SMARTR = re.compile(r"https://(?:jobs|careers)\.smartrecruiters\.com/([\w-]+)/\d+")
_WORKABLE = re.compile(r"https://apply\.workable\.com/([\w-]+)/j/")
_BAMBOO = re.compile(r"https://([\w-]+)\.bamboohr\.com/(?:careers|jobs)")
_RIPPLING = re.compile(r"https://ats\.rippling\.com/([\w-]+)/jobs/")
_BREEZY = re.compile(r"https://([\w-]+)\.breezy\.hr/p/")
_JAZZ = re.compile(r"https://([\w-]+)\.applytojob\.com/apply/")
_PINPOINT = re.compile(r"https://([\w-]+)\.pinpointhq\.com/")
_GEM = re.compile(r"https://jobs\.gem\.com/([\w-]+)/")
_ADP = re.compile(r"https://workforcenow\.adp\.com/.*?[?&]cid=([\w-]+)")
_UKG = re.compile(r"(https://recruiting2?\.ultipro\.com/[\w-]+/JobBoard/[\w-]+)/")
_BRASS = re.compile(r"https://sjobs\.brassring\.com/.*?partnerid=(\d+)&siteid=(\d+)", re.I)
_APRO = re.compile(r"https://([\w-]+\.(?:applicantpro|isolvedhire)\.com)/jobs/\d+")
_SIMPLE = [(_SMARTR, "smartrecruiters"), (_WORKABLE, "workable"), (_BAMBOO, "bamboohr"), (_RIPPLING, "rippling"),
           (_BREEZY, "breezy"), (_JAZZ, "jazzhr"), (_PINPOINT, "pinpoint"), (_GEM, "gem")]


def _site_host(c: dict) -> str:
    """A site's host, with the company's tenant in front on a shared Workday
    address (wd5.myworkdaysite.com serves many companies)."""
    host = c.get("host", "").lower()
    return f"{c['tenant'].lower()}.{host}" if c.get("tenant") else host


def entry_key(kind: str, c: dict) -> str:
    """One key per board, the same whether it came from sources.toml or a link."""
    if kind in ("workday", "oracle"):
        return f"{kind}:{_site_host(c)}/{c.get('site', '').lower()}"
    if kind == "adp":
        return f"adp:{c.get('cid', '').lower()}"
    if kind == "brassring":
        return f"brassring:{c.get('partner')}/{','.join(map(str, c.get('sites', [])))}"
    if kind == "ukg":
        return f"ukg:{c.get('board', '').lower().rstrip('/')}"
    if "board" in c:
        return f"{kind}:{str(c['board']).lower()}"
    return f"{kind}:{c.get('host', '').lower()}"


def site_of(url: str) -> tuple[str, dict] | None:
    """(key, sources.toml-style entry without a name) for a posting link, or None."""
    info = parse_ats_url(url)
    entry: dict | None = None
    if info and info["ats"] in ("greenhouse", "lever", "ashby"):
        entry = {"kind": info["ats"], "board": info["board"]}
    elif info and info["ats"] == "workday":
        if re.search(r"(?i)private|restricted|internal", info["site"]):
            return None  # hidden sites for employees or special hiring
        entry = {"kind": "workday", "host": info["host"], "site": info["site"]}
        if not info["host"].lower().startswith(info["tenant"].lower() + "."):
            entry["tenant"] = info["tenant"]  # shared wdN.myworkdaysite.com address
    elif m := _ORACLE.match(url or ""):
        entry = {"kind": "oracle", "host": m.group(1), "site": m.group(2)}
    elif m := _SF.match(url or ""):
        entry = {"kind": "successfactors", "host": m.group(1)}
    elif m := _JIBE.match(url or ""):
        entry = {"kind": "jibe", "host": m.group(1)}
    elif m := _ICIMS.match(url or ""):
        entry = {"kind": "icims", "host": m.group(1)}
    elif m := _ADP.match(url or ""):
        entry = {"kind": "adp", "cid": m.group(1)}
    elif m := _UKG.match(url or ""):
        entry = {"kind": "ukg", "board": m.group(1)}
    elif m := _BRASS.match(url or ""):
        entry = {"kind": "brassring", "partner": m.group(1), "sites": [m.group(2)]}
    elif m := _APRO.match(url or ""):
        entry = {"kind": "applicantpro", "host": m.group(1)}
    else:
        for rx, kind in _SIMPLE:
            m = rx.match(url or "")
            if m:
                entry = {"kind": kind, "board": m.group(1)}
                break
    if not entry:
        return None
    return entry_key(entry["kind"], entry), entry


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).strip()


_SUFFIX = {"inc", "llc", "ltd", "corp", "corporation", "company", "co", "the", "technologies", "technology",
           "industries", "group", "holdings", "usa", "us", "america", "systems", "aerospace", "space", "labs"}


def _core(name: str) -> set[str]:
    return {w for w in _norm(name).split() if w not in _SUFFIX and len(w) > 1}


def names_match(target: str, other: str) -> bool:
    """Do two company names mean the same company? Generic words (Inc, Aerospace, Space,
    Systems...) don't count, the rest must agree: "Firehawk Aerospace" is "Firehawk", but
    "Mercury Systems" isn't "Mercury Insurance"."""
    a, b = _core(target), _core(other)
    if not a or not b:
        return _norm(target) == _norm(other)
    return a == b


def _configured(cfg: dict) -> tuple[set[str], set[str]]:
    """Keys and names of the boards sources.toml already lists (any board type)."""
    keys, names = set(), set()
    for kind in BOARD_KINDS:
        for c in cfg.get(kind, []):
            names.add(c["name"].lower())
            keys.add(entry_key(kind, c))
    return keys, names


def _configured_hosts(cfg: dict) -> set[str]:
    """Hosts sources.toml reads one way or another (a search page, Phenom, iCIMS...), so a
    found board on the same host read another way isn't a separate board. Workday and
    Oracle hosts are left out: one host there serves several separate boards."""
    hosts = set()
    for kind in BOARD_KINDS:
        if kind in ("workday", "oracle"):
            continue
        for c in cfg.get(kind, []):
            for v in (c.get("host"), c.get("search"), c.get("base")):
                if v:
                    hosts.add(re.sub(r"^https?://", "", v).split("/")[0].lower())
    return hosts


def _add(found: dict, key: str, entry: dict, name: str, today: str, via: str, **extra) -> bool:
    if key in found:
        return False
    found[key] = {**entry, "name": name.strip(), "first_seen": today, "fails": 0, "state": "active",
                  "via": via, **extra}
    return True


def learn(found: dict, postings, is_aero, today: str) -> int:
    """Record the career sites behind aerospace companies' list postings.
    postings: (company, url) pairs, or (company, url, posted date) for past
    postings, whose date then counts as when the site was last linked.
    Returns how many sites are new."""
    new = 0
    cut = (dt.date.fromisoformat(today) - dt.timedelta(days=FORGET_DAYS)).isoformat()
    for company, url, *when in postings:
        seen = when[0] if when and when[0] else today
        if not company or seen < cut or not is_aero(company):
            continue
        site = site_of(url)
        if not site:
            continue
        key, entry = site
        new += _add(found, key, entry, company, today, f"list link ({seen})")
        found[key]["last_seen"] = max(found[key].get("last_seen", ""), seen)
    return new


def learn_engineering(found: dict, postings, wanted, today: str, min_postings: int) -> int:
    """Career sites of other employers (carmakers, energy, robotics...) from their
    aerospace or mechanical internships on the lists in the past 15 months. With
    min_postings or more the board is scanned; with fewer it joins the candidate queue.
    postings: (company, url, title, posted date). These feed All engineering, Fall and
    All opportunities only."""
    cut = (dt.date.fromisoformat(today) - dt.timedelta(days=FORGET_DAYS)).isoformat()
    counts: dict[str, list] = {}
    for company, url, title, posted in postings:
        if not company or posted < cut or not wanted(title):
            continue
        site = site_of(url)
        if site:
            c = counts.setdefault(site[0], [site[1], company.strip(), 0, posted, title])
            c[2], c[3] = c[2] + 1, max(c[3], posted)
    new = 0
    for key, (entry, company, n, last, title) in counts.items():
        state = "active" if n >= min_postings else "candidate"
        added = _add(found, key, entry, company, today,
                     f"{n} mechanical/aerospace internship{'s' if n > 1 else ''} on the lists (e.g. {title[:60]})",
                     engineering=True, state=state)
        new += added
        e = found[key]
        e["last_seen"] = max(e.get("last_seen", ""), last)
        if e.get("state") == "candidate" and n >= min_postings:
            e["state"] = "active"
    return new


def _due(e: dict, today: str) -> bool:
    return not e.get("next_try") or e["next_try"] <= today


def as_sources(found: dict, cfg: dict, today: str,
               max_candidates: int = CANDIDATES_PER_RUN) -> tuple[dict[str, list[dict]], list[dict]]:
    """The found sites to scan this run, as sources.toml-style lists, and the ones waiting
    for a retry (for the page's coverage list). Boards sources.toml already lists are
    skipped by address, so a company's other boards are still read."""
    keys, names = _configured(cfg)
    hosts = _configured_hosts(cfg)
    out: dict[str, list[dict]] = {k: [] for k in KINDS}
    waiting = []
    now = dt.date.fromisoformat(today)
    used: set[str] = set(names)
    # Candidates tried longest ago go first
    cands = sorted((k for k, e in found.items() if e.get("state") == "candidate" and _due(e, today)),
                   key=lambda k: found[k].get("tried", ""))[:max_candidates]
    for key, e in list(found.items()):
        if e.get("kind") not in KINDS:
            continue
        e.setdefault("state", "active")
        stale = (now - dt.date.fromisoformat(e.get("last_seen", today))).days > FORGET_DAYS
        if stale and e["state"] != "repair" and "probe" not in e.get("via", ""):
            del found[key]
            continue
        if key in keys or e["state"] in ("moved", "covered"):
            continue
        if e["kind"] not in ("workday", "oracle") and e.get("host", "").lower() in hosts:
            e["state"] = "covered"  # sources.toml reads this site another way
            continue
        if e["state"] == "candidate" and key not in cands:
            continue
        # A unique name on the page when a company has several boards
        label = e["name"] if e["name"].lower() not in used else f"{e['name']} ({_short(e)})"
        used.add(label.lower())
        e["label"] = label
        if not _due(e, today):
            waiting.append({"name": label, "kind": f"{e['kind'].title()} (found automatically)", "ok": False,
                            "complete": False, "count": 0, "waiting": True, "careers": board_url(e["kind"], e),
                            "error": f"skipped: retry scheduled for {e['next_try']} after {e.get('fails', 0)} "
                                     f"failed runs ({e.get('error', 'error')})"})
            continue
        if e["state"] == "candidate":
            e["tried"] = today
        out[e["kind"]].append({**{k: v for k, v in e.items() if k in _FIELDS}, "name": label})
    return {k: v for k, v in out.items() if v}, waiting


def _short(e: dict) -> str:
    return str(e.get("site") or e.get("board") or e.get("host") or e.get("cid") or e.get("partner") or e["kind"])


def _next_try(fails: int, today: str) -> str:
    if fails < RETRY_FREE:
        return today
    days = min(MAX_WAIT_DAYS, 2 ** (fails - RETRY_FREE))
    return (dt.date.fromisoformat(today) + dt.timedelta(days=days)).isoformat()


def record_results(found: dict, status: list[dict], today: str, company_sites: dict | None = None,
                   covered: set[str] | None = None) -> list[dict]:
    """Track each found board's health: validate candidates that answered, schedule
    retries for failures, and move a failing board's company to its new hiring system
    when list links show one (company_sites: normalized company -> {key: entry}).
    covered: names of companies a configured source read fine this run.
    Returns the boards added as replacements."""
    by_label = {e.get("label") or e["name"]: (k, e) for k, e in found.items()}
    added = []
    for s in status:
        hit = by_label.get(s["name"])
        if not hit or s.get("waiting"):
            continue
        key, e = hit
        if s["ok"]:
            e.update(fails=0, last_ok=today)
            for k in ("next_try", "error", "fail_since"):
                e.pop(k, None)
            if e.get("state") in ("candidate", "repair"):
                if e["state"] == "candidate":
                    e["validated"] = today
                e["state"] = "active"
            continue
        e["fails"] = e.get("fails", 0) + 1
        e["error"] = s.get("error", "")[:160]
        e.setdefault("fail_since", today)
        e["next_try"] = _next_try(e["fails"], today)
        if e.get("state") != "candidate":
            e["state"] = "repair"
        if e["fails"] < RETRY_FREE:
            continue
        # Did the company move? Another hiring system for the same name on recent lists...
        co = _norm(e["name"])
        for new_key, entry in (company_sites or {}).get(co, {}).items():
            if new_key != key and new_key not in found:
                _add(found, new_key, entry, e["name"], today, f"replacement for {key} (failing since {e['fail_since']})",
                     **({"engineering": True} if e.get("engineering") else {}))
                e.update(state="moved", moved_to=new_key)
                added.append({"name": e["name"], "kind": entry["kind"], "via": found[new_key]["via"]})
                break
        else:
            # ...or a board in sources.toml already covers the company and worked this run
            if covered and e["name"].lower() in covered:
                e.update(state="covered")
    return added


# ---------------------------------------------------------------- name probes

def _slugs(name: str) -> list[str]:
    words = _norm(name).split()
    core = [w for w in words if w not in ("inc", "llc", "corp", "corporation", "company", "the")]
    out = ["".join(core), "-".join(core)]
    if len(core) > 1 and len(core[0]) >= 5:
        out.append(core[0])
    return list(dict.fromkeys(s for s in out if len(s) >= 3))


def _mentions(name: str, texts) -> bool:
    core = _core(name) or set(_norm(name).split())
    return any(core <= set(_norm(t).split()) for t in texts if t)


def probe_board(name: str) -> tuple[str, dict, int] | None:
    """Look a company up on hiring systems with public APIs. Returns (key, entry, openings)
    for the first board whose own company name, or posting text, matches the name."""
    for slug in _slugs(name):
        tries = [
            ("greenhouse", f"https://boards-api.greenhouse.io/v1/boards/{slug}"),
            ("workable", f"https://apply.workable.com/api/v1/widget/accounts/{slug}"),
            ("smartrecruiters", f"https://api.smartrecruiters.com/v1/companies/{slug}/postings?limit=20"),
            ("lever", f"https://api.lever.co/v0/postings/{slug}?mode=json&limit=20"),
            ("ashby", f"https://api.ashbyhq.com/posting-api/job-board/{slug}"),
        ]
        for kind, url in tries:
            try:
                data = get_json(url, timeout=15, retries=0)
            except (FetchError, ValueError):
                continue
            entry = {"kind": kind, "board": slug}
            if kind == "greenhouse" and names_match(name, (data or {}).get("name", "")):
                try:
                    n = len(get_json(f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs", timeout=20,
                                     retries=0).get("jobs", []))
                except (FetchError, ValueError):
                    n = 0
                return entry_key(kind, entry), entry, n
            if kind == "workable" and names_match(name, (data or {}).get("name", "")):
                return entry_key(kind, entry), entry, len(data.get("jobs") or [])
            if kind == "smartrecruiters":
                posts = (data or {}).get("content") or []
                if posts and any(names_match(name, (p.get("company") or {}).get("name", "")) for p in posts):
                    return entry_key(kind, entry), entry, int(data.get("totalFound") or len(posts))
            if kind == "lever" and isinstance(data, list) and data and _mentions(
                    name, [j.get("descriptionPlain") or "" for j in data] + [j.get("additionalPlain") or "" for j in data]):
                return entry_key(kind, entry), entry, len(data)
            if kind == "ashby":
                jobs = (data or {}).get("jobs") or []
                if jobs and _mentions(name, [j.get("descriptionPlain") or "" for j in jobs[:20]]):
                    return entry_key(kind, entry), entry, len(jobs)
    return None


def probe_names(found: dict, state: dict, names: list[tuple[str, str]], cfg: dict, today: str,
                budget: int = PROBES_PER_RUN) -> list[dict]:
    """Probe a few names without a board (names: (name, where it came from)), oldest
    probe first. state["probed"] remembers each name's last probe so the list rotates.
    Returns the boards added."""
    _, configured = _configured(cfg)
    have = configured | {e["name"].lower() for e in found.values()}
    probed = state.setdefault("probed", {})
    todo = []
    for name, origin in names:
        n = name.lower().lstrip("=").strip()
        if len(n) < 4 or "*" in n or any(n in h or h in n for h in have if len(h) >= 4):
            continue
        last = probed.get(n, {}).get("d", "")
        if last and (dt.date.fromisoformat(today) - dt.date.fromisoformat(last)).days < REPROBE_DAYS:
            continue
        todo.append((last, n, origin))
    todo.sort()
    todo = todo[:budget]

    def one(item):
        _, n, origin = item
        try:
            return n, origin, probe_board(n)
        except Exception:  # noqa: BLE001 - a probe never stops the scan
            return n, origin, None

    added = []
    with ThreadPoolExecutor(max_workers=6) as pool:
        for n, origin, hit in pool.map(one, todo):
            if hit:
                key, entry, count = hit
                probed[n] = {"d": today, "r": f"{key} ({count} openings)"}
                if _add(found, key, entry, n.title(), today, f"name probe ({origin})", last_seen=today,
                        **({"engineering": True} if origin != "aerospace_companies" else {})):
                    added.append({"name": n.title(), "kind": entry["kind"], "via": f"name probe ({origin})",
                                  "openings": count})
            else:
                probed[n] = {"d": today, "r": "no board found on Greenhouse, Lever, Ashby, SmartRecruiters or Workable"}
    return added


def report(found: dict, today: str, added: list[dict], unsupported: dict, probe_state: dict,
           names_total: int) -> dict:
    """What discovery did and where it stands, for the page and data/discovery.json."""
    def row(e):
        return {"name": e.get("label") or e["name"], "kind": e["kind"], "via": e.get("via", "list link"),
                "link": board_url(e["kind"], e), "fails": e.get("fails", 0), "error": e.get("error", ""),
                "next_try": e.get("next_try", ""), "last_ok": e.get("last_ok", ""), "since": e.get("fail_since", ""),
                "moved_to": e.get("moved_to", "")}
    states: dict[str, int] = {}
    for e in found.values():
        states[e.get("state", "active")] = states.get(e.get("state", "active"), 0) + 1
    return {
        "date": today,
        "added": added,
        "states": states,
        "repair": sorted((row(e) for e in found.values() if e.get("state") == "repair"),
                         key=lambda r: -r["fails"]),
        "moved": [row(e) for e in found.values() if e.get("state") in ("moved", "covered")],
        "candidates": [row(e) for e in found.values() if e.get("state") == "candidate"][:40],
        "unsupported": sorted(({"host": h, "count": len(v), "companies": sorted(v)[:6]} for h, v in unsupported.items()),
                              key=lambda r: -r["count"])[:20],
        "probed": {"done": sum(1 for v in probe_state.get("probed", {}).values() if v.get("d")), "names": names_total,
                   "found": sum(1 for v in probe_state.get("probed", {}).values() if not v.get("r", "").startswith("no "))},
    }
