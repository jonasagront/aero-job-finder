"""Fetch internship postings from every source listed in sources.toml.

Each fetcher returns a list of job dicts with these keys:
  company, title, location, url, source, posted (YYYY-MM-DD or ""),
  description (plain text, may be ""), season_hint (str, may be "")
"""
from __future__ import annotations

import datetime as dt
import html
import json
import os
import re
from concurrent.futures import ThreadPoolExecutor

from .util import FetchError, get_json, html_to_text, parse_ats_url, post_json, request, strip_tracking


def _date_from_iso(s) -> str:
    if not s:
        return ""
    try:
        return dt.datetime.fromisoformat(str(s).replace("Z", "+00:00")).date().isoformat()
    except ValueError:
        return str(s)[:10]


def _date_from_epoch(n, ms=False) -> str:
    try:
        n = float(n) / (1000 if ms else 1)
        return dt.datetime.fromtimestamp(n, dt.timezone.utc).date().isoformat()
    except (TypeError, ValueError, OSError):
        return ""


# ------------------------------------------------------------ GitHub lists

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


def fetch_workday(host: str, site: str, company: str, max_pages: int = 10, keep=_keep_all) -> list[dict]:
    tenant = host.split(".")[0]
    api = f"https://{host}/wday/cxs/{tenant}/{site}/jobs"
    postings, seen_paths = [], set()
    for term in ("intern", "internship", "co-op"):
        offset = 0
        for _ in range(max_pages):
            page = post_json(api, {"appliedFacets": {}, "limit": 20, "offset": offset,
                                   "searchText": term}, timeout=40)
            batch = page.get("jobPostings") or []
            for p in batch:
                if p.get("externalPath") not in seen_paths:
                    seen_paths.add(p.get("externalPath"))
                    postings.append(p)
            offset += len(batch)
            if not batch or offset >= int(page.get("total") or 0):
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
            "url": info.get("externalUrl") or f"https://{host}/{site}{path}",
            "source": f"{company} careers",
            "posted": _date_from_iso(info.get("startDate")),
            "description": html_to_text(info.get("jobDescription")),
            "season_hint": "",
        }

    with ThreadPoolExecutor(max_workers=6) as pool:
        return list(pool.map(detail, wanted))


def fetch_eightfold(host: str, domain: str, company: str, max_pages: int = 15, keep=_keep_all) -> list[dict]:
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


def fetch_jibe(host: str, company: str, max_pages: int = 30) -> list[dict]:
    """iCIMS career sites built on Jibe (careers.jhuapl.edu, careers.spiritaero.com):
    a JSON search API that includes each posting's full text."""
    out, page = [], 1
    while page <= max_pages:
        data = get_json(f"https://{host}/api/jobs?keywords=intern&page={page}", timeout=40)
        batch = [b.get("data") or {} for b in data.get("jobs") or []]
        for j in batch:
            out.append({
                "company": company,
                "title": (j.get("title") or "").strip(),
                "location": j.get("full_location") or ", ".join(filter(None, [j.get("city"), j.get("state")])),
                "url": f"https://{host}/jobs/{j.get('slug') or j.get('req_id')}",
                "source": f"{company} careers",
                "posted": _date_from_iso(j.get("posted_date") or j.get("create_date")),
                "description": html_to_text(j.get("description")),
                "season_hint": "",
            })
        page += 1
        if not batch or len(out) >= int(data.get("totalCount") or 0):
            break
    return out


def fetch_oracle(host: str, site: str, company: str, max_pages: int = 40, keep=_keep_all) -> list[dict]:
    """Oracle Recruiting Cloud sites (Honeywell, Howmet): host is the
    *.oraclecloud.com address, site the name after /sites/ in a job link."""
    api = f"https://{host}/hcmRestApi/resources/latest"
    reqs, offset = [], 0
    for _ in range(max_pages):
        data = get_json(f"{api}/recruitingCEJobRequisitions?onlyData=true&expand=requisitionList"
                        f"&finder=findReqs;siteNumber={site},keyword=intern,limit=25,offset={offset}", timeout=40)
        item = (data.get("items") or [{}])[0]
        batch = item.get("requisitionList") or []
        reqs.extend(batch)
        offset += len(batch)
        if not batch or offset >= int(item.get("TotalJobsCount") or 0):
            break
    # The keyword also matches descriptions, so only open internship titles
    wanted = [r for r in reqs if _INTERNISH.search(r.get("Title", "")) and keep(r.get("Title", ""))]

    def detail(r):
        try:
            d = get_json(f'{api}/recruitingCEJobRequisitionDetails?expand=all&onlyData=true'
                         f'&finder=ById;Id=%22{r["Id"]}%22,siteNumber={site}', timeout=30)
            d = (d.get("items") or [{}])[0]
        except FetchError:
            d = {}
        text = "\n".join(html_to_text(d.get(k)) for k in
                         ("ExternalDescriptionStr", "ExternalResponsibilitiesStr", "ExternalQualificationsStr"))
        return {
            "company": company,
            "title": (r.get("Title") or "").strip(),
            "location": r.get("PrimaryLocation", ""),
            "url": f"https://{host}/hcmUI/CandidateExperience/en/sites/{site}/job/{r['Id']}",
            "source": f"{company} careers",
            "posted": _date_from_iso(r.get("PostedDate")),
            "description": text.strip(),
            "season_hint": "",
        }

    with ThreadPoolExecutor(max_workers=6) as pool:
        return list(pool.map(detail, wanted))


# ------------------------------------------------------------ career sites read from their pages
# SuccessFactors and Phenom sites have no open JSON search, so these read
# the search result pages, then open each internship's own page, which carries
# the posting as schema.org JobPosting data (text, location, date).

_BROWSER = {"Accept": "text/html", "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"}


def _page(url: str) -> str:
    return request(url, headers=_BROWSER, timeout=30, retries=1)


def _postings_from_pages(company: str, links: dict[str, str], keep) -> list[dict]:
    """links: {url: title}. Opens each internship-titled link for its full posting."""
    wanted = [(u, t) for u, t in links.items() if _INTERNISH.search(t) and keep(t)]

    def detail(item):
        url, title = item
        try:
            page = _page(url)
            p = _job_posting(page) or _microdata_posting(page) or _phenom_posting(page)
        except FetchError:
            p = {}
        return {
            "company": company,
            "title": title,
            "location": _posting_location(p),
            "url": url,
            "source": f"{company} careers",
            "posted": _date_from_iso(p.get("datePosted")),
            "description": html_to_text(p.get("description")),
            "season_hint": "",
        }

    with ThreadPoolExecutor(max_workers=6) as pool:
        return list(pool.map(detail, wanted))


def _microdata_posting(page: str) -> dict:
    """SuccessFactors job pages mark the posting up with itemprop attributes
    instead of JobPosting JSON. Returned in the same shape as _job_posting."""
    i = page.find('class="jobdescription"')
    if i < 0:
        return {}
    # The text is the element with class="jobdescription": walk to its closing tag
    start = page.rfind("<", 0, i)
    tag = re.match(r"<(\w+)", page[start:]).group(1)
    depth, end = 0, len(page)
    for m in re.finditer(rf"<(/?){tag}\b", page[start:]):
        depth += -1 if m.group(1) else 1
        if depth == 0:
            end = start + m.end()
            break

    def prop(name: str) -> str:
        m = re.search(rf'itemprop="{name}"[^>]*content="([^"]*)"', page)
        return html.unescape(m.group(1)) if m else ""

    posted = prop("datePosted")  # like "Wed Oct 07 07:00:00 UTC 2026"
    try:
        posted = dt.datetime.strptime(posted, "%a %b %d %H:%M:%S UTC %Y").date().isoformat()
    except ValueError:
        pass
    return {"description": page[start:end], "datePosted": posted,
            "jobLocation": {"address": {k: prop(k) for k in ("addressLocality", "addressRegion", "addressCountry")}}}


_SF_LINK = re.compile(r'class="jobTitle-link[^"]*"[^>]*href="(/job/[^"]+)"[^>]*>\s*([^<]+?)\s*<')


def fetch_successfactors(host: str, company: str, max_pages: int = 40, keep=_keep_all) -> list[dict]:
    """SuccessFactors career sites (jobs.l3harris.com, jobs.ulalaunch.com):
    links look like /job/<city-title>/<id>/."""
    links: dict[str, str] = {}
    for n in range(max_pages):
        found = {f"https://{host}{html.unescape(u)}": html.unescape(t)
                 for u, t in _SF_LINK.findall(_page(f"https://{host}/search/?q=intern&startrow={25 * n}"))}
        if not set(found) - set(links):
            break
        links.update(found)
    return _postings_from_pages(company, links, keep)


def _phenom_ddo(page: str) -> dict:
    """The JSON a Phenom page embeds in phApp.ddo, or {}."""
    i = page.find("phApp.ddo = ")
    if i < 0:
        return {}
    try:
        return json.JSONDecoder().raw_decode(page[i + len("phApp.ddo = "):])[0]
    except ValueError:
        return {}


def _phenom_posting(page: str) -> dict:
    """Phenom job pages that skip JobPosting data still embed the job in phApp.ddo."""
    job = ((_phenom_ddo(page).get("jobDetail") or {}).get("data") or {}).get("job") or {}
    if not job.get("description"):
        return {}
    return {"description": job["description"], "datePosted": job.get("postedDate", ""),
            "jobLocation": {"address": job.get("location", "")}}


def fetch_phenom(base: str, company: str, max_pages: int = 20, keep=_keep_all) -> list[dict]:
    """Phenom career sites (jobs.baesystems.com/global/en): each search page
    embeds its results as JSON in phApp.ddo."""
    links: dict[str, str] = {}
    for n in range(max_pages):
        ddo = _phenom_ddo(_page(f"{base}/search-results?keywords=intern&from={20 * n}"))
        if not ddo:
            raise FetchError("search page has no job data")
        found = ((ddo.get("eagerLoadRefineSearch") or {}).get("data") or {}).get("jobs") or []
        for j in found:
            links[f"{base}/job/{j.get('jobSeqNo')}"] = (j.get("title") or "").strip()
        if len(found) < 20:
            break
    return _postings_from_pages(company, links, keep)


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
    for src in cfg.get("getro", []):
        tasks.append((src["name"], "Job board", lambda s=src: fetch_getro(s)))
    for c in cfg.get("greenhouse", []):
        tasks.append((c["name"], "Greenhouse", lambda c=c: fetch_greenhouse(c["board"], c["name"])))
    for c in cfg.get("lever", []):
        tasks.append((c["name"], "Lever", lambda c=c: fetch_lever(c["board"], c["name"])))
    for c in cfg.get("ashby", []):
        tasks.append((c["name"], "Ashby", lambda c=c: fetch_ashby(c["board"], c["name"])))
    for c in cfg.get("workday", []):
        tasks.append((c["name"], "Workday", lambda c=c: fetch_workday(c["host"], c["site"], c["name"], keep=keep)))
    for c in cfg.get("eightfold", []):
        tasks.append((c["name"], "Eightfold", lambda c=c: fetch_eightfold(c["host"], c["domain"], c["name"], keep=keep)))
    for c in cfg.get("clearcompany", []):
        tasks.append((c["name"], "ClearCompany", lambda c=c: fetch_clearcompany(c["site_id"], c["name"])))
    for c in cfg.get("jibe", []):
        tasks.append((c["name"], "iCIMS (Jibe)", lambda c=c: fetch_jibe(c["host"], c["name"])))
    for c in cfg.get("oracle", []):
        tasks.append((c["name"], "Oracle", lambda c=c: fetch_oracle(c["host"], c["site"], c["name"], keep=keep)))
    for c in cfg.get("successfactors", []):
        tasks.append((c["name"], "SuccessFactors", lambda c=c: fetch_successfactors(c["host"], c["name"], keep=keep)))
    for c in cfg.get("phenom", []):
        tasks.append((c["name"], "Phenom", lambda c=c: fetch_phenom(c["base"], c["name"], keep=keep)))
    if "usajobs" in cfg:
        tasks.append(("USAJOBS", "Federal", lambda: fetch_usajobs(cfg["usajobs"])))

    def run(task):
        label, kind, fn = task
        try:
            jobs = fn()
            for j in jobs:
                j["source_id"] = label
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


_LD_JSON = re.compile(r'(?is)<script[^>]*application/ld\+json[^>]*>(.*?)</script>')


def _job_posting(page: str) -> dict:
    """The schema.org JobPosting data embedded in a job page, or {}."""
    for m in _LD_JSON.finditer(page):
        try:
            data = json.loads(m.group(1).strip())
        except ValueError:
            continue
        items = data if isinstance(data, list) else data.get("@graph", [data]) if isinstance(data, dict) else []
        for it in items:
            if isinstance(it, dict) and it.get("@type") == "JobPosting" and it.get("description"):
                return it
    return {}


def _posting_location(p: dict) -> str:
    locs = p.get("jobLocation") or []
    out = []
    for loc in locs if isinstance(locs, list) else [locs]:
        a = (loc or {}).get("address") or {} if isinstance(loc, dict) else {}
        if isinstance(a, str):
            out.append(a)
            continue
        country = a.get("addressCountry")
        if isinstance(country, dict):
            country = country.get("name")
        out.append(", ".join(filter(None, [a.get("addressLocality"), a.get("addressRegion"), country])))
    return "; ".join(dict.fromkeys(filter(None, out)))


def fetch_page_description(url: str) -> str:
    """Any other job page: most hiring sites (iCIMS, SuccessFactors, Oracle...)
    embed the posting as schema.org JobPosting data, which includes the text."""
    if not url.startswith("http"):
        return ""
    page = request(url, headers={"Accept": "text/html", "User-Agent": "Mozilla/5.0 (compatible; aero-job-finder)"},
                   timeout=20, retries=0)
    return html_to_text(_job_posting(page).get("description"))
