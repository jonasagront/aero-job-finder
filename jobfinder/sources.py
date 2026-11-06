"""Fetch internship postings from every source listed in sources.toml.

Each fetcher returns a list of job dicts with these keys:
  company, title, location, url, source, posted (YYYY-MM-DD or ""),
  description (plain text, may be ""), season_hint (str, may be "")
"""
from __future__ import annotations

import csv
import datetime as dt
import email.utils
import html
import http.cookiejar
import io
import json
import os
import re
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor

from .util import FetchError, get_json, html_to_text, parse_ats_url, post_json, request, strip_tracking


# sources.toml sections that are one company's own career board
BOARD_KINDS = ("greenhouse", "lever", "ashby", "workday", "eightfold", "clearcompany", "successfactors",
               "icims", "jibe", "oracle", "phenom", "pinpoint", "bamboohr", "rippling", "smartrecruiters",
               "workable", "gem", "taleo", "jazzhr", "searchpage", "jobsfeed", "brassring", "adp", "ukg", "paycor",
               "breezy", "activate")


_DATE_FORMATS = ("%a %b %d %H:%M:%S UTC %Y", "%m/%d/%Y", "%B %d, %Y", "%b %d, %Y", "%d %B %Y", "%d %b %Y")


def _date_from_iso(s) -> str:
    """YYYY-MM-DD from an ISO date or timestamp, or from the other formats some sites
    send in its place ("October 28, 2026" on Schneider Electric's); "" if unreadable."""
    s = str(s or "").strip()
    if not s:
        return ""
    try:
        return dt.datetime.fromisoformat(s.replace("Z", "+00:00")).date().isoformat()
    except ValueError:
        pass
    if re.match(r"\d{4}-\d{2}-\d{2}", s):
        return s[:10]
    s = re.sub(r"\s+", " ", s)
    for f in _DATE_FORMATS:
        try:
            return dt.datetime.strptime(s, f).date().isoformat()
        except ValueError:
            pass
    return ""


def _date_from_epoch(n, ms=False) -> str:
    try:
        n = float(n) / (1000 if ms else 1)
        return dt.datetime.fromtimestamp(n, dt.timezone.utc).date().isoformat()
    except (TypeError, ValueError, OSError):
        return ""


# ------------------------------------------------------------ GitHub lists

# Each list's whole contents from this run (closed postings too), for data/history.json
LIST_ITEMS: dict[str, list] = {}


def fetch_simplify_list(src: dict) -> list[dict]:
    data, err = None, None
    for url in src["urls"]:
        try:
            data = get_json(url, timeout=60)
            break
        except (FetchError, ValueError) as e:
            err = e
    if data is None:
        raise FetchError(f"list not reachable ({err})")
    LIST_ITEMS[src["name"]] = data
    jobs = []
    for item in data:
        if not item.get("active", True) or not item.get("is_visible", True):
            continue
        terms = item.get("terms") or []
        season = ", ".join(terms) if isinstance(terms, list) else str(terms)
        locs = item.get("locations") or []
        jobs.append({
            "company": item.get("company_name", "").strip(),
            "title": item.get("title", "").strip(),
            "location": "; ".join(locs) if isinstance(locs, list) else str(locs),
            "url": strip_tracking(item.get("url", "")),
            "source": src["name"],
            "posted": _date_from_epoch(item.get("date_posted")),
            "description": "",
            "season_hint": season,
            "sponsorship": item.get("sponsorship", ""),
        })
    return jobs


_TERM_HINT = re.compile(r"(?i)^(spring|summer|fall|winter) 20\d\d$")


def fetch_csv_list(src: dict) -> list[dict]:
    """Internship lists published as a CSV file, one posting per row with the
    company's own link (the mechanical engineering list's data/internships.csv):
    company, title, location, url, posted_at, and season unless season_inferred
    says the list guessed it."""
    rows = csv.DictReader(io.StringIO(request(src["url"], headers={"Accept": "text/csv, text/plain, */*"}, timeout=60)))
    jobs = []
    for r in rows:
        company, title = (r.get("company") or "").strip(), (r.get("title") or "").strip()
        url = strip_tracking((r.get("url") or "").strip())
        if not company or not title or not url.startswith("http"):
            continue
        season = (r.get("season") or "").strip()
        guessed = (r.get("season_inferred") or "").strip().lower() == "true"
        jobs.append({
            "company": company,
            "title": title,
            "location": (r.get("location") or "").strip(),
            "url": url,
            "source": src["name"],
            "posted": _date_from_iso(r.get("posted_at")),
            "description": "",
            "season_hint": season.title() if _TERM_HINT.match(season) and not guessed else "",
        })
    if not jobs:
        raise FetchError("list has no rows (its columns may have changed)")
    return jobs


def fetch_getro(src: dict) -> list[dict]:
    """Getro-powered job boards (e.g. the Space Capital board). Each posting links
    to the company's own hiring page, so descriptions are filled in later."""
    api = f"https://api.getro.com/api/v2/collections/{src['collection']}/search/jobs"
    found: dict = {}
    # Interns tagged as such, plus "Summer 2027" titles the board left untagged
    for body in ({"query": "", "filters": {"seniority": ["internship"]}},
                 {"query": "summer 2027 intern", "filters": {}}):
        page = 0
        while page < 150:
            res = post_json(api, {"hitsPerPage": 20, "page": page, **body}, timeout=40).get("results") or {}
            batch = res.get("jobs") or []
            for j in batch:
                found[j.get("id")] = j
            page += 1
            if not batch or page * 20 >= int(res.get("count") or 0):
                break
    jobs = []
    for j in found.values():
        jobs.append({
            "company": ((j.get("organization") or {}).get("name") or "").strip(),
            "title": (j.get("title") or "").strip(),
            "location": "; ".join(j.get("locations") or []),
            "url": strip_tracking(j.get("url", "")),
            "source": src["name"],
            "posted": _date_from_epoch(j.get("created_at")),
            "description": "",
            "season_hint": "",
        })
    return jobs


# ------------------------------------------------------------ company boards

def fetch_greenhouse(board: str, company: str) -> list[dict]:
    data = get_json(f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs?content=true", timeout=60)
    out = []
    for j in data.get("jobs", []):
        out.append({
            "company": company,
            "title": (j.get("title") or "").strip(),
            "location": (j.get("location") or {}).get("name", ""),
            "url": j.get("absolute_url", ""),
            "source": f"{company} careers",
            "posted": _date_from_iso(j.get("first_published") or j.get("updated_at")),
            "description": html_to_text(j.get("content")),
            "season_hint": "",
        })
    return out


def _lever_text(j: dict) -> str:
    parts = [j.get("descriptionPlain") or html_to_text(j.get("description"))]
    for lst in j.get("lists") or []:
        parts.append(lst.get("text", ""))
        parts.append(html_to_text(lst.get("content")))
    parts.append(j.get("additionalPlain") or "")
    return "\n".join(p for p in parts if p)


def fetch_lever(board: str, company: str) -> list[dict]:
    data = get_json(f"https://api.lever.co/v0/postings/{board}?mode=json", timeout=60)
    out = []
    for j in data:
        cats = j.get("categories") or {}
        out.append({
            "company": company,
            "title": (j.get("text") or "").strip(),
            "location": cats.get("location") or ", ".join(cats.get("allLocations") or []),
            "url": j.get("hostedUrl") or j.get("applyUrl", ""),
            "source": f"{company} careers",
            "posted": _date_from_epoch(j.get("createdAt"), ms=True),
            "description": _lever_text(j),
            "season_hint": "",
        })
    return out


_ashby_cache: dict[str, list] = {}


def _ashby_board(board: str) -> list:
    if board not in _ashby_cache:
        data = get_json(f"https://api.ashbyhq.com/posting-api/job-board/{board}", timeout=60)
        _ashby_cache[board] = data.get("jobs", [])
    return _ashby_cache[board]


def fetch_ashby(board: str, company: str) -> list[dict]:
    out = []
    for j in _ashby_board(board):
        if j.get("isListed") is False:
            continue
        out.append({
            "company": company,
            "title": (j.get("title") or "").strip(),
            "location": j.get("location", ""),
            "url": j.get("jobUrl") or j.get("applyUrl", ""),
            "source": f"{company} careers",
            "posted": _date_from_iso(j.get("publishedAt")),
            "description": j.get("descriptionPlain") or html_to_text(j.get("descriptionHtml")),
            "season_hint": "",
        })
    return out


_INTERNISH = re.compile(r"(?i)(?<![a-z])(intern|internship|co-?op|co op|student)(?![a-z])")


def _workday_detail(host: str, tenant: str, site: str, path: str) -> dict:
    data = get_json(f"https://{host}/wday/cxs/{tenant}/{site}{path}", timeout=30)
    return data.get("jobPostingInfo") or {}


def _keep_all(title: str) -> bool:
    return True


# Workday filters that mark internships ("Intern (Fixed Term)", "Co-op/Intern",
# "Trainee / Student"...), on filters about the kind of job, not its place or skills
_WD_INTERN_VALUE = re.compile(r"(?i)(?<![a-z-])(interns?|internships?|co-?ops?|cooperative|students?|trainees?)(?![a-z])")
_WD_OTHER_FACET = re.compile(r"(?i)location|skill|country|region|compan|distance|date|clearance")


def _workday_intern_facets(facets) -> dict[str, list[str]]:
    """{filter name: [value ids]} for the values of a site's filters that mean internship."""
    out: dict[str, list[str]] = {}

    def walk(param, values):
        for v in values or []:
            if v.get("values"):  # a group of filters, like "Locations"
                walk(v.get("facetParameter") or param, v["values"])
            elif (param and v.get("id") and not _WD_OTHER_FACET.search(param)
                  and _WD_INTERN_VALUE.search(v.get("descriptor") or "")):
                out.setdefault(param, []).append(v["id"])

    for f in facets or []:
        walk(f.get("facetParameter"), f.get("values"))
    return out


def fetch_workday(host: str, site: str, company: str, max_pages: int = 50, keep=_keep_all,
                  tenant: str | None = None) -> list[dict]:
    """Workday career sites. tenant is only needed on wdN.myworkdaysite.com sites,
    which carry it in the address (wd5.myworkdaysite.com/recruiting/<tenant>/<site>)
    instead of the host name (<tenant>.wd5.myworkdayjobs.com/<site>)."""
    tenant = tenant or host.split(".")[0]
    api = f"https://{host}/wday/cxs/{tenant}/{site}/jobs"
    page_root = (f"https://{host}/recruiting/{tenant}/{site}" if host.endswith(".myworkdaysite.com")
                 else f"https://{host}/{site}")
    postings, seen_paths = [], set()
    facets: dict[str, list[str]] = {}

    def add(batch):
        for p in batch:
            if p.get("externalPath") not in seen_paths:
                seen_paths.add(p.get("externalPath"))
                postings.append(p)

    for term in ("intern", "internship", "co-op"):
        offset = total = 0
        for _ in range(max_pages):
            # Workday rate-limits busy runs (HTTP 429); request() waits and retries
            page = post_json(api, {"appliedFacets": {}, "limit": 20, "offset": offset,
                                   "searchText": term}, timeout=40, retries=4)
            if not offset and term == "intern":
                facets = _workday_intern_facets(page.get("facets"))
            batch = page.get("jobPostings") or []
            add(batch)
            offset += len(batch)
            # Some sites only give the total on the first page (later pages say 0)
            total = total or int(page.get("total") or 0)
            if not batch or offset >= total:
                break
            # The search matches the whole text ("co-op" finds nearly every job), so
            # stop once a whole page has no internship titles; the filters below
            # find the rest
            if not any(_INTERNISH.search(p.get("title", "")) for p in batch):
                break
    # Most sites tag internships with a filter (worker type, job family...), which
    # lists them all no matter where the search would have ranked them
    for param, ids in facets.items():
        offset = total = 0
        for _ in range(max_pages):
            page = post_json(api, {"appliedFacets": {param: ids}, "limit": 20, "offset": offset,
                                   "searchText": ""}, timeout=40, retries=4)
            batch = page.get("jobPostings") or []
            add(batch)
            offset += len(batch)
            total = total or int(page.get("total") or 0)
            if not batch or offset >= total:
                break
    # Workday's list has no descriptions, so only open internship-looking ones
    # (and skip titles the scan would drop anyway, like "Finance Intern").
    wanted = [p for p in postings if _INTERNISH.search(p.get("title", "")) and keep(p.get("title", ""))]

    def detail(p):
        path = p.get("externalPath", "")
        try:
            info = _workday_detail(host, tenant, site, path)
        except FetchError:
            info = {}
        loc = p.get("locationsText") or info.get("location", "")
        if re.fullmatch(r"\d+ Locations", loc.strip()):  # the list only gives a count
            loc = "; ".join(filter(None, [info.get("location")] + (info.get("additionalLocations") or []))) or loc
        return {
            "company": company,
            "title": (p.get("title") or "").strip(),
            "location": loc,
            "url": info.get("externalUrl") or f"{page_root}{path}",
            "source": f"{company} careers",
            "posted": _date_from_iso(info.get("startDate")) or _workday_posted_on(p.get("postedOn", "")),
            "description": html_to_text(info.get("jobDescription")),
            "season_hint": "",
        }

    with ThreadPoolExecutor(max_workers=6) as pool:
        return list(pool.map(detail, wanted))


def _workday_posted_on(text: str) -> str:
    """Workday's list says "Posted Today", "Posted Yesterday" or "Posted 3 Days Ago"
    ("30+ Days Ago" is too vague to use)."""
    t = text.lower()
    days = 0 if "today" in t else 1 if "yesterday" in t else None
    m = re.search(r"posted (\d+) days? ago", t)
    if m:
        days = int(m.group(1))
    return (dt.date.today() - dt.timedelta(days=days)).isoformat() if days is not None else ""


def fetch_eightfold(host: str, domain: str, company: str, max_pages: int = 40, keep=_keep_all) -> list[dict]:
    """Eightfold career sites (e.g. lockheedmartin.eightfold.ai). Search pages hold
    10 postings and no description, so each internship is opened for its text."""
    api = f"https://{host}/api/pcsx"
    postings, seen = [], set()
    for term in ("intern", "co-op"):
        start = 0
        for _ in range(max_pages):
            page = get_json(f"{api}/search?domain={domain}&query={term}&start={start}", timeout=40)
            page = page.get("data", page)
            batch = page.get("positions") or []
            for p in batch:
                if p.get("id") not in seen:
                    seen.add(p.get("id"))
                    postings.append(p)
            start += len(batch)
            if not batch or start >= int(page.get("count") or 0):
                break
    wanted = [p for p in postings if _INTERNISH.search(p.get("name", "")) and keep(p.get("name", ""))]

    def detail(p):
        try:
            info = get_json(f"{api}/position_details?position_id={p['id']}&domain={domain}&hl=en", timeout=30)
            info = info.get("data", info)
        except FetchError:
            info = {}
        return {
            "company": company,
            "title": (p.get("name") or "").strip(),
            "location": "; ".join(p.get("locations") or []),
            "url": info.get("publicUrl") or f"https://{host}{p.get('positionUrl', '')}",
            "source": f"{company} careers",
            "posted": _date_from_epoch(p.get("postedTs")),
            "description": html_to_text(info.get("jobDescription")),
            "season_hint": "",
        }

    with ThreadPoolExecutor(max_workers=6) as pool:
        return list(pool.map(detail, wanted))


def fetch_clearcompany(site_id: str, company: str) -> list[dict]:
    """ClearCompany career sites. site_id is the GUID in the page's
    careers-api.clearcompany.com/v1/<site_id> request."""
    out, page_index = [], 0
    while True:
        data = get_json(f"https://careers-api.clearcompany.com/v1/{site_id}"
                        f"?pageIndex={page_index}&pageSize=100&source=CJB-0", timeout=60)
        batch = data.get("results") or []
        for j in batch:
            out.append({
                "company": company,
                "title": (j.get("positionTitle") or "").strip(),
                "location": j.get("location", ""),
                "url": re.sub(r"/apply(\?.*)?$", "", j.get("applyLink", "")),
                "source": f"{company} careers",
                "posted": _date_from_iso(j.get("postedDate") or j.get("openDate")),
                "description": html_to_text(j.get("description")),
                "season_hint": "",
            })
        page_index += 1
        if not batch or len(out) >= int(data.get("totalCount") or 0):
            return out


# ------------------------------------------------------------ more hiring systems
# Big defense/aerospace employers on systems with no Greenhouse-style API. Most
# list pages carry no description, so (like Workday) only internship-looking
# titles that keep() wants get their posting opened.

_PAGE_HEADERS = {"Accept": "text/html", "User-Agent": "Mozilla/5.0 (compatible; aero-job-finder)"}


def _get_page(url: str, timeout: int = 40) -> str:
    return request(url, headers=_PAGE_HEADERS, timeout=timeout)


def _wanted(title: str, keep) -> bool:
    return bool(_INTERNISH.search(title or "")) and keep(title or "")


def _open_each(postings: list, detail) -> list[dict]:
    with ThreadPoolExecutor(max_workers=6) as pool:
        return list(pool.map(detail, postings))


_RMK_LINK = re.compile(r'(?s)<a\b([^>]*\bjobTitle-link\b[^>]*)>(.*?)</a>')
_RMK_DESC = re.compile(r'<(span|div)\b[^>]*\b(?:class="jobdescription"|itemprop="description")[^>]*>')


def _rmk_text(page: str) -> str:
    """The posting sits in <span class="jobdescription"> (or spans or divs marked
    itemprop="description", one per section on some sites), which hold more of
    the same tag, so find each one's closing tag by counting."""
    parts, pos = [], 0
    while m := _RMK_DESC.search(page, pos):
        depth, pos = 1, len(page)
        for tag in re.compile(rf'<(/?){m.group(1)}\b[^>]*>').finditer(page, m.end()):
            depth += -1 if tag.group(1) else 1
            if depth == 0:
                parts.append(html_to_text(page[m.end():tag.start()]))
                pos = tag.end()
                break
    return "\n".join(p for p in parts if p)


def fetch_successfactors(host: str, company: str, max_pages: int = 20, keep=_keep_all) -> list[dict]:
    """SuccessFactors career sites (jobs.l3harris.com, jobs.ulalaunch.com...): links
    look like <host>/job/<City-Title>/<id>/. The search is full text, so it also
    returns non-intern jobs; titles are filtered before any posting is opened.
    Newer sites (jobs.bombardier.com...) build the list in the browser, so their
    JSON search is read instead."""
    postings: dict[str, tuple[str, str]] = {}  # id -> (path, title)
    for term in ("intern", "co-op"):
        start = 0
        for _ in range(max_pages):
            page = _get_page(f"https://{host}/search/?q={term}&startrow={start}")
            if not start and term == "intern" and "jobTitle-link" not in page:
                return _successfactors_json(host, company, max_pages * 2, keep)
            new = 0
            for attrs, title in _RMK_LINK.findall(page):
                m = re.search(r'href="(/job/[^"]+?/(\d+)/?)"', attrs)
                if m and m.group(2) not in postings:
                    postings[m.group(2)] = (html.unescape(m.group(1)), html_to_text(title))
                    new += 1
            if not new:
                break
            start += new
    wanted = [(path, title) for path, title in postings.values() if _wanted(title, keep)]

    def detail(p):
        path, title = p
        url = f"https://{host}{path}"
        try:
            page = _get_page(url, timeout=30)
        except FetchError:
            page = ""
        loc = re.search(r'class="jobGeoLocation"[^>]*>([^<]+)', page)
        posted = re.search(r'itemprop="datePosted" content="([^"]+)"', page)
        try:
            posted = dt.datetime.strptime(posted.group(1), "%a %b %d %H:%M:%S UTC %Y").date().isoformat() if posted else ""
        except ValueError:
            posted = ""
        return {
            "company": company,
            "title": title,
            "location": loc.group(1).strip() if loc else "",
            "url": url,
            "source": f"{company} careers",
            "posted": posted,
            "description": _rmk_text(page),
            "season_hint": "",
        }

    return _open_each(wanted, detail)


def _successfactors_json(host: str, company: str, max_pages: int, keep) -> list[dict]:
    """The JSON search behind newer SuccessFactors career sites, 10 postings a page,
    best matches first. A site with neither this nor result links has no matches."""
    api = f"https://{host}/services/recruiting/v1/jobs"
    found: dict[str, dict] = {}
    try:
        for term in ("intern", "co-op"):
            seen = 0
            for page in range(max_pages):
                data = post_json(api, {"locale": "en_US", "pageNumber": page, "sortBy": "", "keywords": term,
                                       "location": "", "facetFilters": {}, "brand": "", "skills": [],
                                       "categoryId": 0, "alertId": "", "rcmCandidateId": ""}, timeout=40)
                batch = [r.get("response") or {} for r in data.get("jobSearchResult") or []]
                for r in batch:
                    found.setdefault(r.get("id"), r)
                seen += len(batch)
                if not batch or seen >= int(data.get("totalJobs") or 0):
                    break
                # Best matches come first, so stop once a whole page has no internship titles
                if not any(_INTERNISH.search(r.get("unifiedStandardTitle") or "") for r in batch):
                    break
    except FetchError:
        return []
    wanted = [r for r in found.values() if r.get("id") and _wanted(r.get("unifiedStandardTitle", ""), keep)]

    def detail(r):
        url = f"https://{host}/job/{html.unescape(r.get('urlTitle') or 'job')}/{r['id']}-en_US"
        try:
            text = _rmk_text(_get_page(url, timeout=30))
        except FetchError:
            text = ""
        try:
            posted = dt.datetime.strptime(r.get("unifiedStandardStart", ""), "%m/%d/%y").date().isoformat()
        except ValueError:
            posted = ""
        return {
            "company": company,
            "title": html.unescape(r.get("unifiedStandardTitle") or "").strip(),
            "location": "; ".join(re.sub(r"<br/?>|[,\s]+$", "", html.unescape(x)).strip()
                                  for x in r.get("jobLocationShort") or []),
            "url": url,
            "source": f"{company} careers",
            "posted": posted,
            "description": text,
            "season_hint": "",
        }

    return _open_each(wanted, detail)


_ICIMS_CARD = re.compile(r'(?s)<li class="iCIMS_JobCardItem">(.*?)</li>')


def fetch_icims(host: str, company: str, max_pages: int = 15, keep=_keep_all) -> list[dict]:
    """iCIMS career sites (careers-<company>.icims.com). The search page lists 20
    postings; each internship is opened for its full text (schema.org data).
    On some sites the keyword search finds nothing at all, whatever the word
    (Peraton, Iridium, Sierra Lobo: "no jobs were found"), so when neither search
    finds a posting the site's whole list is read instead."""
    postings: dict[str, dict] = {}

    def read(query: str, n_pages: int) -> None:
        for pr in range(n_pages):
            page = _get_page(f"https://{host}/jobs/search?ss=1{query}&in_iframe=1&pr={pr}")
            for card in _ICIMS_CARD.findall(page):
                link = re.search(r'href="(https://[^"]+?/jobs/\d+/[^"?]+/job)', card)
                title = re.search(r'(?s)<h3[^>]*>(.*?)</h3>', card)
                if not link or not title or link.group(1) in postings:
                    continue
                # In the card header on some sites, in the field list on others
                loc = re.search(r'(?s)Job Locations?</span>\s*(?:</dt>\s*<dd[^>]*>\s*)?<span[^>]*>(.*?)</span>', card)
                posted = re.search(r'<span title="(\d+)/(\d+)/(\d{4})', card)
                postings[link.group(1)] = {
                    "url": link.group(1),
                    "title": html_to_text(title.group(1)),
                    "location": html_to_text(loc.group(1)) if loc else "",
                    "posted": f"{posted.group(3)}-{int(posted.group(1)):02d}-{int(posted.group(2)):02d}" if posted else "",
                }
            pages = re.search(r"Page \d+ of (\d+)", page)
            if not pages or pr + 1 >= int(pages.group(1)):
                break

    for term in ("intern", "co-op"):
        read(f"&searchKeyword={term}", max_pages)
    if not postings:
        read("", 40)
    wanted = [p for p in postings.values() if _wanted(p["title"], keep)]

    def detail(p):
        try:
            text, posted = fetch_page_posting(p["url"] + "?in_iframe=1")
        except FetchError:
            text, posted = "", ""
        # Some iCIMS search pages show no date; the job page usually has one
        return {"company": company, "source": f"{company} careers", "description": text, "season_hint": "",
                **p, "posted": p["posted"] or posted}

    return _open_each(wanted, detail)


def fetch_jibe(host: str, company: str, max_pages: int = 10) -> list[dict]:
    """Jibe career sites (careers.jhuapl.edu, careers.viasat.com...), which answer
    <host>/api/jobs with full postings."""
    out, seen = [], set()
    for term in ("intern", "co-op"):
        for page in range(1, max_pages + 1):
            data = get_json(f"https://{host}/api/jobs?keywords={term}&limit=100&page={page}", timeout=60)
            batch = data.get("jobs") or []
            for item in batch:
                j = item.get("data") or {}
                if j.get("slug") in seen:
                    continue
                seen.add(j.get("slug"))
                out.append({
                    "company": company,
                    "title": (j.get("title") or "").strip(),
                    "location": j.get("full_location") or ", ".join(filter(None, [j.get("city"), j.get("state")])),
                    "url": f"https://{host}/jobs/{j.get('slug')}",
                    "source": f"{company} careers",
                    "posted": _date_from_iso(j.get("posted_date")),
                    "description": "\n".join(html_to_text(j.get(k)) for k in
                                             ("description", "responsibilities", "qualifications") if j.get(k)),
                    "season_hint": "",
                })
            if not batch or page * 100 >= int(data.get("totalCount") or 0):
                break
    return out


def fetch_oracle(host: str, site: str, company: str, max_pages: int = 40, keep=_keep_all) -> list[dict]:
    """Oracle Recruiting Cloud sites (<pod>.fa.ocs.oraclecloud.com/hcmUI/CandidateExperience/
    en/sites/<site>). The keyword search is fuzzy ("intern" also finds "internal"),
    so titles are filtered before each posting is opened. Big sites match several
    hundred postings (Honeywell: about 700), so up to 1,000 are read."""
    api = f"https://{host}/hcmRestApi/resources/latest"
    postings: dict[str, dict] = {}
    for term in ("intern", "co-op"):
        for page in range(max_pages):
            data = get_json(f"{api}/recruitingCEJobRequisitions?onlyData=true&expand=requisitionList"
                            f"&finder=findReqs;siteNumber={site},"
                            f"keyword={term},limit=25,offset={page * 25}", timeout=40)
            found = (data.get("items") or [{}])[0]
            batch = found.get("requisitionList") or []
            for r in batch:
                postings.setdefault(r.get("Id"), r)
            if not batch or (page + 1) * 25 >= int(found.get("TotalJobsCount") or 0):
                break
    wanted = [r for r in postings.values() if _wanted(r.get("Title", ""), keep)]

    def detail(r):
        try:
            d = get_json(f'{api}/recruitingCEJobRequisitionDetails?expand=all&onlyData=true'
                         f'&finder=ById;Id=%22{r["Id"]}%22,siteNumber={site}', timeout=30)
            d = (d.get("items") or [{}])[0]
        except FetchError:
            d = {}
        return {
            "company": company,
            "title": (r.get("Title") or "").strip(),
            "location": r.get("PrimaryLocation", ""),
            "url": f"https://{host}/hcmUI/CandidateExperience/en/sites/{site}/job/{r['Id']}",
            "source": f"{company} careers",
            "posted": _date_from_iso(r.get("PostedDate")),
            "description": "\n".join(html_to_text(d.get(k)) for k in
                                     ("ExternalDescriptionStr", "ExternalResponsibilitiesStr",
                                      "ExternalQualificationsStr") if d.get(k)) or r.get("ShortDescriptionStr", ""),
            "season_hint": "",
        }

    return _open_each(wanted, detail)


_PHENOM_SEARCH = '"eagerLoadRefineSearch":'


def fetch_phenom(base: str, company: str, max_pages: int = 15, keep=_keep_all) -> list[dict]:
    """Phenom career sites (jobs.baesystems.com/global/en...). Search results are
    embedded in the page as JSON, 20 at a time; postings are opened for full text."""
    postings: dict[str, dict] = {}
    for term in ("intern", "co-op"):
        total = None
        for page in range(max_pages):
            text = _get_page(f"{base}/search-results?keywords={term}&from={page * 20}")
            i = text.find(_PHENOM_SEARCH)
            if i < 0:
                raise FetchError("no search results in page")
            res, _ = json.JSONDecoder().raw_decode(text, i + len(_PHENOM_SEARCH))
            if total is None:
                total = int(res.get("totalHits") or 0)
            elif int(res.get("totalHits") or 0) != total:
                break  # site dropped the keyword for later pages
            batch = (res.get("data") or {}).get("jobs") or []
            for j in batch:
                postings.setdefault(j.get("jobId"), j)
            if not batch or (page + 1) * 20 >= total:
                break
    wanted = [j for j in postings.values() if _wanted(j.get("title", ""), keep)]

    def detail(j):
        url = f"{base}/job/{j['jobId']}"
        try:
            text, posted = fetch_page_posting(url)
        except FetchError:
            text, posted = "", ""
        return {
            "company": company,
            "title": (j.get("title") or "").strip(),
            "location": "; ".join(j.get("multi_location") or []) or j.get("location", ""),
            "url": url,
            "source": f"{company} careers",
            "posted": _date_from_iso(j.get("postedDate")) or posted,
            "description": text or j.get("descriptionTeaser", ""),
            "season_hint": "",
        }

    return _open_each(wanted, detail)


def fetch_pinpoint(board: str, company: str, keep=_keep_all) -> list[dict]:
    """Pinpoint boards. The JSON has full postings but no dates, so each
    internship's page is opened for its posted date."""
    data = get_json(f"https://{board}.pinpointhq.com/postings.json", timeout=60)
    out = []
    for j in data.get("data", []):
        parts = [(j.get(k + "_header") or "") + "\n" + html_to_text(j.get(k)) if k != "description"
                 else html_to_text(j.get(k))
                 for k in ("description", "key_responsibilities", "skills_knowledge_expertise", "benefits") if j.get(k)]
        out.append({
            "company": company,
            "title": (j.get("title") or "").strip(),
            "location": (j.get("location") or {}).get("name", ""),
            "url": j.get("url", ""),
            "source": f"{company} careers",
            "posted": "",
            "description": "\n".join(parts),
            "season_hint": "",
        })

    def dated(p):
        try:
            p["posted"] = fetch_page_posting(p["url"])[1]
        except FetchError:
            pass
        return p

    wanted = [p for p in out if p["url"] and _wanted(p["title"], keep)]
    _open_each(wanted, dated)
    return out


def fetch_bamboohr(board: str, company: str, keep=_keep_all) -> list[dict]:
    base = f"https://{board}.bamboohr.com/careers"
    wanted = [j for j in get_json(f"{base}/list", timeout=40).get("result", [])
              if _wanted(j.get("jobOpeningName", ""), keep)]

    def detail(j):
        try:
            d = get_json(f"{base}/{j['id']}/detail", timeout=30).get("result", {}).get("jobOpening", {})
        except FetchError:
            d = {}
        loc = j.get("location") or {}
        return {
            "company": company,
            "title": (j.get("jobOpeningName") or "").strip(),
            "location": "Remote" if j.get("isRemote") else ", ".join(filter(None, [loc.get("city"), loc.get("state")])),
            "url": f"{base}/{j['id']}",
            "source": f"{company} careers",
            "posted": _date_from_iso(d.get("datePosted")),
            "description": html_to_text(d.get("description")),
            "season_hint": "",
        }

    return _open_each(wanted, detail)


def fetch_rippling(board: str, company: str, keep=_keep_all) -> list[dict]:
    api = f"https://api.rippling.com/platform/api/ats/v1/board/{board}/jobs"
    wanted = [j for j in get_json(api, timeout=40) if _wanted(j.get("name", ""), keep)]

    def detail(j):
        try:
            d = get_json(f"{api}/{j['uuid']}", timeout=30)
        except FetchError:
            d = {}
        desc = d.get("description") or {}
        return {
            "company": company,
            "title": (j.get("name") or "").strip(),
            "location": (j.get("workLocation") or {}).get("label", ""),
            "url": j.get("url", ""),
            "source": f"{company} careers",
            "posted": _date_from_iso(d.get("createdOn")),
            "description": "\n".join(html_to_text(v) for v in desc.values() if isinstance(v, str)),
            "season_hint": "",
        }

    return _open_each(wanted, detail)


def fetch_smartrecruiters(board: str, company: str, keep=_keep_all) -> list[dict]:
    api = f"https://api.smartrecruiters.com/v1/companies/{board}/postings"
    postings: dict = {}
    for term in ("intern", "co-op"):
        offset = 0
        while offset < 1000:
            data = get_json(f"{api}?q={term}&limit=100&offset={offset}", timeout=40)
            batch = data.get("content") or []
            for p in batch:
                postings.setdefault(p.get("id"), p)
            offset += len(batch)
            if not batch or offset >= int(data.get("totalFound") or 0):
                break
    wanted = [p for p in postings.values() if _wanted(p.get("name", ""), keep)]

    def detail(p):
        try:
            d = get_json(f"{api}/{p['id']}", timeout=30)
        except FetchError:
            d = {}
        sections = ((d.get("jobAd") or {}).get("sections") or {})
        return {
            "company": company,
            "title": (p.get("name") or "").strip(),
            "location": (p.get("location") or {}).get("fullLocation", ""),
            "url": d.get("postingUrl") or f"https://jobs.smartrecruiters.com/{board}/{p['id']}",
            "source": f"{company} careers",
            "posted": _date_from_iso(p.get("releasedDate")),
            "description": "\n".join(html_to_text(s.get("text")) for k, s in sections.items()
                                     if k != "companyDescription" and isinstance(s, dict)),
            "season_hint": "",
        }

    return _open_each(wanted, detail)


def fetch_workable(board: str, company: str) -> list[dict]:
    data = get_json(f"https://apply.workable.com/api/v1/widget/accounts/{board}?details=true", timeout=60)
    out = []
    for j in data.get("jobs", []):
        out.append({
            "company": company,
            "title": (j.get("title") or "").strip(),
            "location": "Remote" if j.get("telecommuting") else ", ".join(
                filter(None, [j.get("city"), j.get("state"), j.get("country")])),
            "url": j.get("url", ""),
            "source": f"{company} careers",
            "posted": _date_from_iso(j.get("published_on")),
            "description": html_to_text(j.get("description")),
            "season_hint": "",
        })
    return out


_TALEO_SEARCH = {
    "multilineEnabled": False,
    "sortingSelection": {"sortBySelectionParam": "3", "ascendingSortingOrder": "false"},
    "filterSelectionParam": {"searchFilterSelections": []},
    "advancedSearchFiltersSelectionParam": {"searchFilterSelections": []},
}


def _taleo_text(page: str) -> str:
    """Taleo pages ship the posting URL-encoded inside a hidden "initialHistory"
    field, split by !|!; the posting is the longest piece."""
    m = re.search(r'id="initialHistory"[^>]*value="([^"]*)"', page)
    if not m:
        return ""
    parts = urllib.parse.unquote(m.group(1)).split("!|!")
    return html_to_text(max(parts, key=len).replace("!*!", ""))


def fetch_taleo(host: str, section: str, portal: str, company: str, max_pages: int = 10, keep=_keep_all) -> list[dict]:
    """Taleo career sections (textron.taleo.net/careersection/<section>/...). portal
    is the number in the section page's portal= requests."""
    api = f"https://{host}/careersection/rest/jobboard/searchjobs?lang=en&portal={portal}"
    headers = {"tz": "GMT-05:00", "tzname": "America/New_York"}
    postings: dict[str, dict] = {}
    for term in ("intern", "co-op"):
        for page in range(1, max_pages + 1):
            data = post_json(api, {**_TALEO_SEARCH, "pageNo": page,
                                   "fieldData": {"fields": {"KEYWORD": term, "LOCATION": ""}, "valid": True}},
                             headers=headers, timeout=40)
            batch = data.get("requisitionList") or []
            for r in batch:
                postings.setdefault(r.get("contestNo"), r)
            paging = data.get("pagingData") or {}
            if not batch or page * int(paging.get("pageSize") or 25) >= int(paging.get("totalCount") or 0):
                break
    wanted = [r for r in postings.values() if _wanted((r.get("column") or [""])[0], keep)]

    def detail(r):
        col = r.get("column") or []
        url = f"https://{host}/careersection/{section}/jobdetail.ftl?job={r['contestNo']}&lang=en"
        try:
            locs = "; ".join(json.loads(col[1])) if len(col) > 1 else ""
        except ValueError:
            locs = col[1] if len(col) > 1 else ""
        posted = re.fullmatch(r"(\d+)/(\d+)/(\d{4})", col[2] if len(col) > 2 else "")
        try:
            text = _taleo_text(_get_page(url, timeout=30))
        except FetchError:
            text = ""
        return {
            "company": company,
            "title": (col[0] if col else "").strip(),
            "location": locs.replace("Multiple Locations", "").strip("; ") or locs,
            "url": url,
            "source": f"{company} careers",
            "posted": f"{posted.group(3)}-{int(posted.group(1)):02d}-{int(posted.group(2)):02d}" if posted else "",
            "description": text,
            "season_hint": "",
        }

    return _open_each(wanted, detail)


_JAZZ_ROW = re.compile(r'(?s)<li class="list-group-item">(.*?)</li>\s*(?=<li class="list-group-item">|</ul>)')


def fetch_jazzhr(board: str, company: str, keep=_keep_all) -> list[dict]:
    """JazzHR boards (<board>.applytojob.com/apply)."""
    page = _get_page(f"https://{board}.applytojob.com/apply")
    postings = []
    for row in _JAZZ_ROW.findall(page):
        link = re.search(r'href="(https://[^"]+/apply/\w+/[^"]+)"[^>]*>\s*(.*?)\s*</a>', row)
        if not link or not _wanted(html_to_text(link.group(2)), keep):
            continue
        loc = re.search(r"fa-map-marker'></i>\s*([^<]+)", row)
        postings.append({"url": link.group(1), "title": html_to_text(link.group(2)),
                         "location": loc.group(1).strip() if loc else ""})

    def detail(p):
        try:
            text, posted = fetch_page_posting(p["url"])
        except FetchError:
            text, posted = "", ""
        return {"company": company, "source": f"{company} careers", "posted": posted, "description": text,
                "season_hint": "", **p}

    return _open_each(postings, detail)


def fetch_searchpage(search: str, path: str, company: str, max_pages: int = 15, keep=_keep_all) -> list[dict]:
    """Career sites with a plain search page and no hiring-system API
    (careers.gulfstream.com, Avature sites like jobs.siemens-energy.com...).
    search is the page's address with {term} and either {page} (1, 2, 3...) or
    {offset} (how many results came before); postings are its links that start
    with path. Each posting's own page carries standard job-posting data, or
    labeled fields as on Avature sites."""
    root = re.match(r"https?://[^/]+", search).group(0)
    link = re.compile(r'(?s)<a\b[^>]*\bhref="((?:' + re.escape(root) + ")?" + re.escape(path) + r'[^"#?]+)"[^>]*>(.*?)</a>')
    postings: dict[str, str] = {}  # url -> title
    for term in ("intern", "co-op"):
        offset = 0
        for page in range(1, max_pages + 1):
            found = link.findall(_get_page(search.format(term=term, page=page, offset=offset)))
            new = 0
            for href, title in found:
                url = urllib.parse.urljoin(root, html.unescape(href))
                if url not in postings or not postings[url]:
                    new += url not in postings
                    postings[url] = html_to_text(title)
            offset += len({h for h, _ in found})
            if not new:  # past the last page, the site repeats it or shows none
                break
    wanted = [(url, title) for url, title in postings.items() if _wanted(title, keep)]

    def detail(p):
        url, title = p
        try:
            page = _get_page(url, timeout=30)
        except FetchError:
            page = ""
        posting = _job_posting(page)
        fields = _avature_fields(page)
        place = next((v for k, v in fields.items() if re.search(r"(?i)location|city", k)), "") or _avature_place(fields)
        return {
            "company": company,
            "title": html_to_text(posting.get("title")) or title,
            "location": _ld_location(posting) or place,
            "url": url,
            "source": f"{company} careers",
            "posted": _page_date(page, posting),
            "description": html_to_text(posting.get("description")) or "\n".join(
                f"{k}: {v}" if len(v) < 120 else f"{k}\n{v}" for k, v in fields.items()),
            "season_hint": "",
        }

    return _open_each(wanted, detail)


_AV_FIELD = re.compile(r'(?s)<div class="article__content__view__field(?:\s[^"]*)?">(.*?)'
                       r'(?=<div class="article__content__view__field(?:\s[^"]*)?">|</article>|</main>|<footer|<script|$)')
_AV_LABEL = re.compile(r'(?s)<div class="article__content__view__field__label">(.*?)</div>')


def _avature_fields(page: str) -> dict[str, str]:
    """Label -> text of the fields on an Avature job page (Location, Description...)."""
    out = {}
    for i, block in enumerate(_AV_FIELD.findall(page)):
        label = _AV_LABEL.search(block)
        text = html_to_text(_AV_LABEL.sub(" ", block, count=1) if label else block)
        if text:
            out[html_to_text(label.group(1)) if label else f"Details {i + 1}"] = text
    return out


def _avature_place(fields: dict[str, str]) -> str:
    """Some Avature sites show a "Location" heading followed by unlabeled country,
    state and city fields: "Orlando, Florida, United States"."""
    items = list(fields.items())
    for i, (_, v) in enumerate(items):
        if v.lower() in ("location", "locations", "job location"):
            parts = []
            for k, v2 in items[i + 1:]:
                if not k.startswith("Details ") or len(v2) > 60:
                    break
                parts.append(v2)
            return ", ".join(reversed(parts))
    return ""


def fetch_internlist(src: dict) -> list[dict]:
    """intern-list.com's tables (public Airtable views embedded on the site).
    Its Apply links go to jobright.ai, which hides the company's link behind a
    sign-in, so these become leads: the button searches for the company's own
    posting, and run.py drops any lead a company board already supplied."""
    out = []
    for view in src["views"]:
        app = view.split("/")[0]
        embed = _get_page(f"https://airtable.com/embed/{view}")
        m = re.search(r'urlWithParams:\s*"([^"]+)"', embed)
        if not m:
            raise FetchError(f"view {view} has no shared data (the site may have replaced it)")
        data = get_json("https://airtable.com" + m.group(1).encode().decode("unicode_escape"), timeout=90, headers={
            "x-airtable-application-id": app, "x-requested-with": "XMLHttpRequest",
            "x-time-zone": "America/New_York", "x-user-locale": "en", "User-Agent": _PAGE_HEADERS["User-Agent"]})
        table = data["data"]["table"]
        cols = {c["id"]: c["name"] for c in table["columns"]}
        for r in table["rows"]:
            row = {cols.get(k, k): v for k, v in r["cellValuesByColumnId"].items()}
            company = (row.get("Company") or "").strip()
            # Some titles were scraped with the page name: "... Job Details | L3HHCM20"
            title = re.sub(r"\s*Job Details\s*(\|.*)?$", "", (row.get("Position Title") or "").strip())
            link = (row.get("Apply") or {}).get("url", "") if isinstance(row.get("Apply"), dict) else ""
            listing = re.search(r"/jobs/info/(\w+)", link)
            if not company or not title or not listing:
                continue
            query = urllib.parse.quote_plus(f'{company} "{title}"')
            out.append({
                "company": company,
                "title": title,
                "location": row.get("Location", ""),
                "url": f"https://www.google.com/search?q={query}",
                "key": "il:" + listing.group(1),
                "lead": True,
                "source": src["name"],
                "posted": _date_from_iso(row.get("Date")),
                "description": "\n".join(filter(None, [
                    row.get("Qualifications", ""),
                    f"Graduation: {row['Graduate Time']}" if row.get("Graduate Time") else "",
                    f"Pay: {row['Salary']}" if row.get("Salary") else "",
                ])),
                "season_hint": _start_to_season(row.get("Hire Time") or ""),
            })
    return out


_MONTH_SEASON = {"january": "Spring", "february": "Spring", "march": "Spring", "april": "Spring",
                 "may": "Summer", "june": "Summer", "july": "Summer", "august": "Summer",
                 "september": "Fall", "october": "Fall", "november": "Fall", "december": "Fall"}


def _start_to_season(start: str) -> str:
    """intern-list start dates ("2027-Summer", "2027-May") as "Summer 2027"."""
    m = re.fullmatch(r"(\d{4})-(\w+)", start.strip())
    if not m:
        return ""
    word = m.group(2).lower()
    season = _MONTH_SEASON.get(word) or (word.title() if word in ("spring", "summer", "fall", "winter") else "")
    return f"{season} {m.group(1)}" if season else ""


def fetch_gem(board: str, company: str) -> list[dict]:
    out = []
    for j in get_json(f"https://api.gem.com/job_board/v0/{board}/job_posts/", timeout=60):
        loc = j.get("location") or {}
        out.append({
            "company": company,
            "title": (j.get("title") or "").strip(),
            "location": loc.get("name", "") if isinstance(loc, dict) else str(loc),
            "url": j.get("absolute_url", ""),
            "source": f"{company} careers",
            "posted": _date_from_iso(j.get("first_published_at") or j.get("updated_at")),
            "description": html_to_text(j.get("content")),
            "season_hint": "",
        })
    return out


_RSS_ITEM = re.compile(r"(?s)<item>(.*?)</item>")


def _rss_field(item: str, tag: str) -> str:
    m = re.search(rf"(?s)<{tag}[^>]*>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</{tag}>", item)
    return html.unescape(m.group(1)).strip() if m else ""


def fetch_jobsfeed(host: str, company: str, max_pages: int = 10, keep=_keep_all) -> list[dict]:
    """DirectEmployers .jobs sites (sandia.jobs, jacobs.jobs): an RSS feed of the
    search with each posting's full text. Titles start with the place, as in
    "(USA-NM-Albuquerque) Intern, ...". Links go to the company's own .jobs page."""
    found: dict[str, dict] = {}
    for term in ("intern", "co-op"):
        offset = 0
        for _ in range(max_pages):
            items = _RSS_ITEM.findall(_get_page(f"https://{host}/jobs/feed/rss?q={term}&offset={offset}", timeout=60))
            new = 0
            for it in items:
                link = _rss_field(it, "link")
                if link and link not in found:
                    found[link] = it
                    new += 1
            offset += len(items)
            if not new:
                break
    out = []
    for link, it in found.items():
        m = re.match(r"\(([^)]*)\)\s*(.*)", _rss_field(it, "title"))
        place, title = (m.group(1), m.group(2)) if m else ("", _rss_field(it, "title"))
        if not _wanted(title, keep):
            continue
        parts = place.split("-", 2)  # USA-NM-Albuquerque
        try:
            posted = email.utils.parsedate_to_datetime(_rss_field(it, "pubDate")).date().isoformat()
        except (TypeError, ValueError):
            posted = ""
        out.append({
            "company": company,
            "title": title,
            "location": ", ".join(reversed(parts)) if len(parts) == 3 else place,
            "url": link,
            "source": f"{company} careers",
            "posted": posted,
            "description": html_to_text(_rss_field(it, "description")),
            "season_hint": "",
        })
    return out


def fetch_brassring(partner: str, sites: list[str], company: str, location_fields=("formtext5", "formtext4"),
                    title_field: str = "jobtitle", max_pages: int = 15, keep=_keep_all) -> list[dict]:
    """IBM Kenexa BrassRing sites (sjobs.brassring.com/TGnewUI/Search/Home/Home?
    partnerid=<partner>&siteid=<site>). The search answers only with the cookies
    and token the search page hands out. Each result carries its fields as
    "questions"; which ones hold the city, state and the specific job name differs
    by company (General Atomics titles every intern "Intern - Undergraduate
    (technical)" and names the role in formtext8)."""
    out, seen = [], set()
    for site in sites:
        opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
        hdr: dict = {}  # the search token, once the search page has handed it out

        def call(url, body=None, opener=opener, hdr=hdr):
            req = urllib.request.Request(url, data=json.dumps(body).encode() if body else None, headers={
                **_PAGE_HEADERS, "Accept": "application/json, text/html", "Content-Type": "application/json", **hdr})
            try:
                with opener.open(req, timeout=40) as resp:
                    return resp.read().decode("utf-8", "replace")
            except Exception as e:  # noqa: BLE001 - HTTP, timeouts, bad SSL...
                raise FetchError(str(e) or e.__class__.__name__) from e

        page = call(f"https://sjobs.brassring.com/TGnewUI/Search/Home/Home?partnerid={partner}&siteid={site}")
        tok = re.search(r'__RequestVerificationToken" type="hidden" value="([^"]+)"', page)
        if not tok:
            raise FetchError(f"site {site}: no search token on the page")
        hdr.update({"RFT": tok.group(1), "X-Requested-With": "XMLHttpRequest"})
        for term in ("intern", "co-op"):
            listed: set = set()
            for n in range(1, max_pages + 1):
                # The first page comes from the search; later ones from its "show more" call
                data = json.loads(call("https://sjobs.brassring.com/TgNewUI/Search/Ajax/"
                                       + ("MatchedJobs" if n == 1 else "ProcessSortAndShowMoreJobs"), {
                    "partnerId": partner, "siteId": site, "keyword": term, "location": "",
                    "keywordCustomSolrFields": "", "locationCustomSolrFields": "", "linkId": "",
                    "Latitude": 0, "Longitude": 0, "facetfilterfields": {"Facet": []},
                    "powersearchoptions": {"PowerSearchOption": []}, "SortType": "LastUpdated",
                    "pageNumber": n, "encryptedSessionValue": ""}))
                batch = [{x.get("QuestionName"): x.get("Value") for x in j.get("Questions") or []}
                         for j in (data.get("Jobs") or {}).get("Job") or []]
                new = {q.get("reqid") for q in batch} - listed
                listed |= new
                for q in batch:
                    title = html.unescape(q.get(title_field) or q.get("jobtitle") or "").strip()
                    if q.get("reqid") in seen or not _wanted(title, keep):
                        continue
                    seen.add(q.get("reqid"))
                    try:
                        posted = dt.datetime.strptime(q.get("lastupdated", ""), "%d-%b-%Y").date().isoformat()
                    except ValueError:
                        posted = ""
                    out.append({
                        "company": company,
                        "title": title,
                        "location": ", ".join(filter(None, (str(q.get(f) or "").strip() for f in location_fields))),
                        "url": f"https://sjobs.brassring.com/TGnewUI/Search/home/HomeWithPreLoad?partnerid={partner}"
                               f"&siteid={site}&PageType=JobDetails&jobid={q.get('reqid')}",
                        "source": f"{company} careers",
                        "posted": posted,
                        "description": html_to_text(q.get("jobdescription")),
                        "season_hint": "",
                    })
                if not new or len(listed) >= int(data.get("JobsCount") or 0):
                    break
    return out


def fetch_adp(cid: str, company: str, keep=_keep_all) -> list[dict]:
    """ADP Workforce Now career centers (workforcenow.adp.com/mascsr/default/mdf/
    recruitment/recruitment.html?cid=<cid>). The list has no keyword search, so
    every opening is listed and internship titles are opened for their text."""
    api = "https://workforcenow.adp.com/mascsr/default/careercenter/public/events/staffing/v1/job-requisitions"
    args = f"cid={cid}&lang=en_US&locale=en_US&ccId=19000101_000001"
    reqs, skip = {}, 1
    while skip < 2000:
        data = get_json(f"{api}?{args}&$top=50&$skip={skip}", timeout=40)
        batch = data.get("jobRequisitions") or []
        for r in batch:
            reqs.setdefault(r.get("itemID"), r)
        skip += len(batch)
        if not batch or skip > int((data.get("meta") or {}).get("totalNumber") or 0):
            break
    wanted = [r for r in reqs.values() if _wanted(r.get("requisitionTitle", ""), keep)]

    def detail(r):
        try:
            d = get_json(f"{api}/{r['itemID']}?{args}", timeout=30)
        except FetchError:
            d = {}
        places = []
        for loc in r.get("requisitionLocations") or []:
            a = loc.get("address") or {}
            places.append(", ".join(filter(None, [a.get("cityName"), (a.get("countrySubdivisionLevel1") or {}).get("codeValue"),
                                                  a.get("countryCode")])))
        return {
            "company": company,
            "title": (r.get("requisitionTitle") or "").strip(),
            "location": "; ".join(filter(None, places)),
            "url": f"https://workforcenow.adp.com/mascsr/default/mdf/recruitment/recruitment.html?{args}&jobId={r['itemID']}",
            "source": f"{company} careers",
            "posted": _date_from_iso(r.get("postDate")),
            "description": html_to_text(d.get("requisitionDescription")),
            "season_hint": "",
        }

    return _open_each(wanted, detail)


def fetch_ukg(board: str, company: str, keep=_keep_all) -> list[dict]:
    """UKG Pro (UltiPro) job boards: board is the address up to the board's ID,
    recruiting.ultipro.com/<tenant>/JobBoard/<id>. Each posting's page holds its
    full text as JSON."""
    found: dict[str, dict] = {}
    for term in ("intern", "co-op"):
        skip = 0
        while skip < 1000:
            data = post_json(f"{board}/JobBoardView/LoadSearchResults", {
                "opportunitySearch": {"Top": 50, "Skip": skip, "QueryString": term, "Filters": [],
                                      "OrderBy": [{"Value": "postedDateDesc", "PropertyName": "PostedDate", "Ascending": False}]},
                "matchCriteria": {"PreferredJobs": [], "Educations": [], "LicenseAndCertifications": [], "Skills": [],
                                  "hasNoLicenses": False, "SkippedSkills": []}}, timeout=40)
            batch = data.get("opportunities") or []
            for o in batch:
                found.setdefault(o.get("Id"), o)
            skip += len(batch)
            if not batch or skip >= int(data.get("totalCount") or 0):
                break
    wanted = [o for o in found.values() if _wanted(o.get("Title", ""), keep)]

    def detail(o):
        url = f"{board}/OpportunityDetail?opportunityId={o['Id']}"
        text = o.get("BriefDescription") or ""
        try:
            page = _get_page(url, timeout=30)
            i = page.find("CandidateOpportunityDetail(")
            if i >= 0:
                d, _ = json.JSONDecoder().raw_decode(page, i + len("CandidateOpportunityDetail("))
                text = html_to_text(d.get("Description")) or text
        except (FetchError, ValueError):
            pass
        places = []
        for loc in o.get("Locations") or []:
            a = loc.get("Address") or {}
            places.append(", ".join(filter(None, [a.get("City"), (a.get("State") or {}).get("Code"),
                                                  (a.get("Country") or {}).get("Code")])) or loc.get("LocalizedDescription") or "")
        return {
            "company": company,
            "title": (o.get("Title") or "").strip(),
            "location": "; ".join(filter(None, places)),
            "url": url,
            "source": f"{company} careers",
            "posted": _date_from_iso(o.get("PostedDate")),
            "description": text,
            "season_hint": "",
        }

    return _open_each(wanted, detail)


_PAYCOR_ROW = re.compile(r'(?s)<a href="(https://recruitingbypaycor\.com/career/JobIntroduction\.action\?[^"]+)"[^>]*>'
                         r'\s*(.*?)\s*</a>\s*</div>\s*<div class="gnewtonCareerGroupJobDescriptionClass">\s*(.*?)\s*</div>')


def fetch_paycor(client: str, company: str, keep=_keep_all) -> list[dict]:
    """Paycor Recruiting (Newton) boards: client is the clientId in the board's
    recruitingbypaycor.com/career/CareerHome.action address. One page lists every
    opening with its place; each posting's page holds its text."""
    page = _get_page(f"https://recruitingbypaycor.com/career/CareerHome.action?clientId={client}")
    rows = [(html.unescape(u), html_to_text(t), html_to_text(loc)) for u, t, loc in _PAYCOR_ROW.findall(page)]
    wanted = [r for r in rows if _wanted(r[1], keep)]

    def detail(r):
        url, title, loc = r
        try:
            text = _get_page(url, timeout=30)
            text = re.sub(r"(?is)<(script|style)\b.*?</\1>", " ", text)
            i = text.find("gnewtonCareerBodyClass")
            text = html_to_text(text[i:]) if i >= 0 else ""
        except FetchError:
            text = ""
        return {"company": company, "title": title, "location": loc, "url": url, "source": f"{company} careers",
                "posted": "", "description": text, "season_hint": ""}

    return _open_each(wanted, detail)


def fetch_breezy(board: str, company: str, keep=_keep_all) -> list[dict]:
    """Breezy HR boards (<board>.breezy.hr): <board>.breezy.hr/json lists every
    opening with its place and date; each internship's page holds its text as
    schema.org data."""
    data = get_json(f"https://{board}.breezy.hr/json", timeout=40)
    postings = []
    for j in data if isinstance(data, list) else []:
        loc = j.get("location") or {}
        state = (loc.get("state") or {}).get("id") or (loc.get("state") or {}).get("name")
        place = loc.get("name") or ", ".join(filter(None, [loc.get("city"), state, (loc.get("country") or {}).get("id")]))
        postings.append({
            "company": company,
            "title": (j.get("name") or "").strip(),
            "location": "Remote" if loc.get("is_remote") and not place else place,
            "url": j.get("url", ""),
            "source": f"{company} careers",
            "posted": _date_from_iso(j.get("published_date")),
            "description": "",
            "season_hint": "",
        })
    wanted = [p for p in postings if p["url"] and _wanted(p["title"], keep)]

    def detail(p):
        try:
            p["description"] = fetch_page_posting(p["url"])[0]
        except FetchError:
            pass
        return p

    return _open_each(wanted, detail)


def fetch_activate(host: str, company: str, max_pages: int = 10, keep=_keep_all) -> list[dict]:
    """Activate career sites (lanl.jobs): the search page fills its table from
    <host>/Search/SearchResults, which sends JSON wrapped in a JSON string. The
    keyword search is full text, so titles are filtered before each posting's
    page (schema.org data) is opened."""
    found: dict[str, dict] = {}
    for term in ("intern", "student", "co-op"):
        start = 0
        for _ in range(max_pages):
            data = get_json(f"https://{host}/Search/SearchResults?keyword={term}&jtStartIndex={start}&jtPageSize=100",
                            headers={"X-Requested-With": "XMLHttpRequest"}, timeout=40)
            if isinstance(data, str):
                data = json.loads(data)
            batch = data.get("Records") or []
            for r in batch:
                found.setdefault(r.get("ID"), r)
            start += len(batch)
            if not batch or start >= int(data.get("TotalRecordCount") or 0):
                break
    wanted = [r for r in found.values() if r.get("ID") and _wanted(html_to_text(r.get("Title")), keep)]

    def detail(r):
        title = html_to_text(r.get("Title"))
        url = f"https://{host}/search/jobdetails/{re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-') or 'job'}/{r['ID']}"
        try:
            text, posted = fetch_page_posting(url)
        except FetchError:
            text, posted = "", ""
        return {
            "company": company,
            "title": title,
            "location": html_to_text(r.get("CityStateDataAbbrev")) or html_to_text(r.get("LocationName")),
            "url": url,
            "source": f"{company} careers",
            "posted": _date_from_iso(r.get("PostedDateRaw")) or posted,
            "description": text,
            "season_hint": "",
        }

    return _open_each(wanted, detail)


# ------------------------------------------------------------ USAJOBS

def fetch_usajobs(cfg: dict) -> list[dict]:
    key, email = os.environ.get("USAJOBS_API_KEY"), os.environ.get("USAJOBS_EMAIL")
    if not key or not email:
        raise FetchError("skipped: add USAJOBS_API_KEY and USAJOBS_EMAIL secrets to enable")
    headers = {"Host": "data.usajobs.gov", "User-Agent": email, "Authorization-Key": key}
    seen, out = set(), []
    for kw in cfg.get("keywords", []):
        url = ("https://data.usajobs.gov/api/search?ResultsPerPage=250&HiringPath=student&Keyword="
               + kw.replace(" ", "%20"))
        data = get_json(url, headers=headers, timeout=60)
        for item in (data.get("SearchResult") or {}).get("SearchResultItems", []):
            d = item.get("MatchedObjectDescriptor") or {}
            pid = d.get("PositionID") or d.get("PositionURI")
            if pid in seen:
                continue
            seen.add(pid)
            details = (d.get("UserArea") or {}).get("Details") or {}
            desc = "\n".join(filter(None, [
                details.get("JobSummary", ""), d.get("QualificationSummary", ""),
                "\n".join(details.get("MajorDuties") or []),
                "U.S. citizenship is required for federal positions.",
            ]))
            apply = (d.get("ApplyURI") or [d.get("PositionURI", "")])[0]
            out.append({
                "company": " / ".join(filter(None, [d.get("OrganizationName"), d.get("DepartmentName")])),
                "title": d.get("PositionTitle", ""),
                "location": d.get("PositionLocationDisplay", ""),
                "url": apply,
                "source": "USAJOBS",
                "posted": _date_from_iso(d.get("PublicationStartDate")),
                "description": desc,
                "season_hint": "",
            })
    return out


# ------------------------------------------------------------ run them all

def fetch_all(cfg: dict, keep=_keep_all) -> tuple[list[dict], list[dict]]:
    """Returns (jobs, source_status). One broken source never stops the rest.
    keep(title) lets sites that need one request per posting skip unwanted titles."""
    tasks = []  # (label, kind, callable)
    for src in cfg.get("list", []):
        tasks.append((src["name"], "Internship list", lambda s=src: fetch_simplify_list(s)))
    for src in cfg.get("csvlist", []):
        tasks.append((src["name"], "Internship list", lambda s=src: fetch_csv_list(s)))
    for src in cfg.get("getro", []):
        tasks.append((src["name"], "Job board", lambda s=src: fetch_getro(s)))
    for c in cfg.get("greenhouse", []):
        tasks.append((c["name"], "Greenhouse", lambda c=c: fetch_greenhouse(c["board"], c["name"])))
    for c in cfg.get("lever", []):
        tasks.append((c["name"], "Lever", lambda c=c: fetch_lever(c["board"], c["name"])))
    for c in cfg.get("ashby", []):
        tasks.append((c["name"], "Ashby", lambda c=c: fetch_ashby(c["board"], c["name"])))
    for c in cfg.get("workday", []):
        tasks.append((c["name"], "Workday", lambda c=c: fetch_workday(c["host"], c["site"], c["name"], keep=keep,
                                                                      tenant=c.get("tenant"))))
    for c in cfg.get("eightfold", []):
        tasks.append((c["name"], "Eightfold", lambda c=c: fetch_eightfold(c["host"], c["domain"], c["name"], keep=keep)))
    for c in cfg.get("clearcompany", []):
        tasks.append((c["name"], "ClearCompany", lambda c=c: fetch_clearcompany(c["site_id"], c["name"])))
    for c in cfg.get("successfactors", []):
        tasks.append((c["name"], "SuccessFactors", lambda c=c: fetch_successfactors(c["host"], c["name"], keep=keep)))
    for c in cfg.get("icims", []):
        tasks.append((c["name"], "iCIMS", lambda c=c: fetch_icims(c["host"], c["name"], keep=keep)))
    for c in cfg.get("jibe", []):
        tasks.append((c["name"], "Jibe", lambda c=c: fetch_jibe(c["host"], c["name"])))
    for c in cfg.get("oracle", []):
        tasks.append((c["name"], "Oracle", lambda c=c: fetch_oracle(c["host"], c["site"], c["name"], keep=keep)))
    for c in cfg.get("phenom", []):
        tasks.append((c["name"], "Phenom", lambda c=c: fetch_phenom(c["base"].rstrip("/"), c["name"], keep=keep)))
    for c in cfg.get("pinpoint", []):
        tasks.append((c["name"], "Pinpoint", lambda c=c: fetch_pinpoint(c["board"], c["name"], keep=keep)))
    for c in cfg.get("bamboohr", []):
        tasks.append((c["name"], "BambooHR", lambda c=c: fetch_bamboohr(c["board"], c["name"], keep=keep)))
    for c in cfg.get("rippling", []):
        tasks.append((c["name"], "Rippling", lambda c=c: fetch_rippling(c["board"], c["name"], keep=keep)))
    for c in cfg.get("smartrecruiters", []):
        tasks.append((c["name"], "SmartRecruiters", lambda c=c: fetch_smartrecruiters(c["board"], c["name"], keep=keep)))
    for c in cfg.get("workable", []):
        tasks.append((c["name"], "Workable", lambda c=c: fetch_workable(c["board"], c["name"])))
    for c in cfg.get("gem", []):
        tasks.append((c["name"], "Gem", lambda c=c: fetch_gem(c["board"], c["name"])))
    for c in cfg.get("taleo", []):
        tasks.append((c["name"], "Taleo", lambda c=c: fetch_taleo(c["host"], c["section"], c["portal"], c["name"], keep=keep)))
    for c in cfg.get("jazzhr", []):
        tasks.append((c["name"], "JazzHR", lambda c=c: fetch_jazzhr(c["board"], c["name"], keep=keep)))
    for c in cfg.get("searchpage", []):
        tasks.append((c["name"], "Search page", lambda c=c: fetch_searchpage(c["search"], c["path"], c["name"], keep=keep)))
    for c in cfg.get("jobsfeed", []):
        tasks.append((c["name"], ".jobs feed", lambda c=c: fetch_jobsfeed(c["host"], c["name"], keep=keep)))
    for c in cfg.get("brassring", []):
        tasks.append((c["name"], "BrassRing", lambda c=c: fetch_brassring(
            c["partner"], c["sites"], c["name"], c.get("location_fields", ("formtext5", "formtext4")),
            c.get("title_field", "jobtitle"), keep=keep)))
    for c in cfg.get("adp", []):
        tasks.append((c["name"], "ADP", lambda c=c: fetch_adp(c["cid"], c["name"], keep=keep)))
    for c in cfg.get("ukg", []):
        tasks.append((c["name"], "UKG", lambda c=c: fetch_ukg(c["board"].rstrip("/"), c["name"], keep=keep)))
    for c in cfg.get("paycor", []):
        tasks.append((c["name"], "Paycor", lambda c=c: fetch_paycor(c["client"], c["name"], keep=keep)))
    for c in cfg.get("breezy", []):
        tasks.append((c["name"], "Breezy HR", lambda c=c: fetch_breezy(c["board"], c["name"], keep=keep)))
    for c in cfg.get("activate", []):
        tasks.append((c["name"], "Activate", lambda c=c: fetch_activate(c["host"], c["name"], keep=keep)))
    for src in cfg.get("internlist", []):
        tasks.append((src["name"], "Internship list", lambda s=src: fetch_internlist(s)))
    if "usajobs" in cfg:
        tasks.append(("USAJOBS", "Federal", lambda: fetch_usajobs(cfg["usajobs"])))

    def run(task):
        label, kind, fn = task
        try:
            jobs = fn()
            for j in jobs:
                j["source_id"] = label
                # The page reads posted dates as YYYY-MM-DD; anything else would show "Invalid Date"
                j["posted"] = _date_from_iso(j.get("posted"))
            return jobs, {"name": label, "kind": kind, "ok": True, "count": len(jobs), "error": ""}
        except Exception as e:  # noqa: BLE001 - report anything, keep going
            return [], {"name": label, "kind": kind, "ok": False, "count": 0, "error": str(e)[:160]}

    jobs, status = [], []
    with ThreadPoolExecutor(max_workers=8) as pool:
        for got, st in pool.map(run, tasks):
            jobs.extend(got)
            status.append(st)
            mark = "ok " if st["ok"] else "ERR"
            print(f"  [{mark}] {st['name']:<45} {st['count']:>5} jobs  {st['error']}")
    return jobs, status


# ------------------------------------------------------------ fill in descriptions

def fetch_description(url: str) -> str:
    """Get the full posting text for a link from a list (lists only give titles)."""
    info = parse_ats_url(url)
    if not info:
        return fetch_page_description(url)
    if info["ats"] == "greenhouse":
        j = get_json(f"https://boards-api.greenhouse.io/v1/boards/{info['board']}/jobs/{info['id']}", timeout=30)
        return html_to_text(j.get("content"))
    if info["ats"] == "lever":
        j = get_json(f"https://api.lever.co/v0/postings/{info['board']}/{info['id']}?mode=json", timeout=30)
        return _lever_text(j)
    if info["ats"] == "ashby":
        for j in _ashby_board(info["board"]):
            if j.get("id") == info["id"]:
                return j.get("descriptionPlain") or html_to_text(j.get("descriptionHtml"))
        return ""
    if info["ats"] == "workday":
        d = _workday_detail(info["host"], info["tenant"], info["site"], info["path"])
        return html_to_text(d.get("jobDescription"))
    return ""


def fetch_posted_date(url: str) -> str:
    """The posted date from a posting's own page, for postings whose source gave
    none. Hiring systems with an API are asked directly."""
    info = parse_ats_url(url)
    if info and info["ats"] == "greenhouse":
        j = get_json(f"https://boards-api.greenhouse.io/v1/boards/{info['board']}/jobs/{info['id']}", timeout=30)
        return _date_from_iso(j.get("first_published") or j.get("updated_at"))
    if info and info["ats"] == "lever":
        j = get_json(f"https://api.lever.co/v0/postings/{info['board']}/{info['id']}?mode=json", timeout=30)
        return _date_from_epoch(j.get("createdAt"), ms=True)
    if info and info["ats"] == "ashby":
        return next((_date_from_iso(j.get("publishedAt")) for j in _ashby_board(info["board"])
                     if j.get("id") == info["id"]), "")
    if info and info["ats"] == "workday":
        return _date_from_iso(_workday_detail(info["host"], info["tenant"], info["site"], info["path"]).get("startDate"))
    if ".icims.com/" in url and "in_iframe=" not in url:
        url += ("&" if "?" in url else "?") + "in_iframe=1"  # the page around the frame has no posting data
    return fetch_page_posting(url)[1]


# Some sites write the type with its + escaped (lanl.jobs: "application/ld&#x2B;json")
_LD_JSON = re.compile(r'(?is)<script[^>]*application/ld(?:\+|&#x2B;|&#43;)json[^>]*>(.*?)</script>')


def _job_posting(page: str) -> dict:
    """The schema.org JobPosting data embedded in a job page, or {}."""
    for m in _LD_JSON.finditer(page):
        try:
            data = json.loads(m.group(1).strip())
        except ValueError:
            continue
        items = data if isinstance(data, list) else data.get("@graph", [data]) if isinstance(data, dict) else []
        for it in items:
            kind = it.get("@type") if isinstance(it, dict) else None
            if kind == "JobPosting" or (isinstance(kind, list) and "JobPosting" in kind):
                return it
    return {}


def _ld_location(posting: dict) -> str:
    """"City, ST, Country" for each place in schema.org JobPosting data."""
    places = posting.get("jobLocation") or []
    out = []
    for p in places if isinstance(places, list) else [places]:
        if not isinstance(p, dict):
            continue
        a = p.get("address")
        if isinstance(a, dict):
            country = a.get("addressCountry")
            country = country.get("name") if isinstance(country, dict) else country
            place = ", ".join(str(x) for x in (a.get("addressLocality"), a.get("addressRegion"), country) if x)
        else:
            place = str(a or "")
        place = place or p.get("name", "")
        if place and place not in out:
            out.append(place)
    return "; ".join(out)


_ITEMPROP_DATE = re.compile(r'itemprop="datePosted"[^>]*?content="([^"]+)"')
_JSON_DATE = re.compile(r'"datePosted"\s*:\s*"([^"]+)"')


def _page_date(page: str, posting: dict) -> str:
    """The posted date a job page gives: its schema.org data, or the same field
    in the page's markup or embedded JSON when that data is missing or broken."""
    for raw in [posting.get("datePosted"), *_ITEMPROP_DATE.findall(page), *_JSON_DATE.findall(page)]:
        d = _plausible_date(_date_from_iso(raw))
        if d:
            return d
    return ""


def _plausible_date(iso: str) -> str:
    """A posted date from page data, or "" when it can't be right. Some iCIMS
    sites stamp every posting exactly two years before today."""
    try:
        age = (dt.date.today() - dt.date.fromisoformat(iso)).days
    except ValueError:
        return ""
    return iso if -2 <= age <= 400 else ""


def fetch_page_posting(url: str) -> tuple[str, str]:
    """(text, posted date) from a job page. Most hiring sites (iCIMS, JazzHR,
    Pinpoint, Phenom...) embed the posting as schema.org JobPosting data."""
    if not url.startswith("http"):
        return "", ""
    page = request(url, headers={"Accept": "text/html", "User-Agent": "Mozilla/5.0 (compatible; aero-job-finder)"},
                   timeout=20, retries=0)
    p = _job_posting(page)
    text = html_to_text(p.get("description")) or _rmk_text(page) or _taleo_text(page)  # those two don't
    return text, _page_date(page, p)


def fetch_page_description(url: str) -> str:
    return fetch_page_posting(url)[0]
