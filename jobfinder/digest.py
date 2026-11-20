"""Optional daily digest: newly found internships (best fits first, with a link to all of
them), verified program deadlines in the next three weeks, and sources that failed.

Off by default. Every run writes the digest it would send to data/digest_preview.md, and
nothing is sent until BOTH are true:
  1. [notify] enabled = true in profile.toml
  2. at least one channel's secrets are set in the repo (Settings -> Secrets -> Actions):
       email:   SMTP_HOST, SMTP_USERNAME, SMTP_PASSWORD, DIGEST_TO
                (optional SMTP_PORT, default 587 with STARTTLS; DIGEST_FROM)
       push:    NTFY_TOPIC (optional NTFY_SERVER, default https://ntfy.sh)
       webhook: DIGEST_WEBHOOK_URL (Discord or Slack incoming webhook)
It goes out at most once a day, on the first scan after [notify] hour (Eastern time).

data/notify_log.json records every posting already included in a sent digest (by its job
key, plus any older key it had), so the same posting is never announced twice, and a log
of each digest sent. Previews never touch the log.

Try it without sending:   python -m jobfinder.digest
"""
from __future__ import annotations

import datetime as dt
import html
import json
import os
import smtplib
import ssl
import sys
import urllib.request
from email.message import EmailMessage
from pathlib import Path

LOG_KEEP_DAYS = 90
TOP = 15


def load_log(path: Path) -> dict:
    try:
        log = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, ValueError):
        log = {}
    log.setdefault("sent", {})      # job key -> date it went out in a digest
    log.setdefault("digests", [])   # one record per digest sent
    return log


def save_log(path: Path, log: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(log, indent=1, ensure_ascii=False), encoding="utf-8")


def _best(j: dict) -> tuple[str, dict]:
    curated = {k: v for k, v in (j.get("tracks") or {}).items() if k != "all"}
    pool = curated or {k: v for k, v in (j.get("tracks") or {}).items()}
    return max(pool.items(), key=lambda kv: kv[1].get("score", 0)) if pool else ("all", {"score": 0})


def _since(log: dict, now: dt.datetime) -> str:
    """New means found after the last digest that went out (or in the last day)."""
    last = (log["digests"][-1]["at"] if log["digests"] else "")
    day_ago = (now - dt.timedelta(hours=24)).isoformat(timespec="seconds")
    return max(last, day_ago) if last else day_ago


def _found(j: dict) -> str:
    return j.get("found_at") or (j.get("first_seen", "") + "T00:00:00+00:00")


def build(jobs: list[dict], status: list[dict], deadlines: list[dict], log: dict, now: dt.datetime,
          page_url: str, track_names: dict[str, str]) -> dict:
    """The digest's parts and its text, Markdown and HTML versions."""
    since = _since(log, now)
    sent = log["sent"]
    new = [j for j in jobs if not j.get("stale") and _found(j) > since
           and j["key"] not in sent and not any(k in sent for k in j.get("aka") or [])]
    relevant = [j for j in new if any(k != "all" for k in j.get("tracks", {}))]
    relevant.sort(key=lambda j: -_best(j)[1].get("score", 0))
    others = len(new) - len(relevant)
    failures = [s for s in status if s.get("state") in ("failed", "stale")]
    flagged = [s for s in status if s.get("suspicious")]
    partial = [s for s in status if s.get("state") == "partial"]

    def when(j):
        if j.get("date_kind") == "employer":
            return f"posted {j['posted']}"
        if j.get("date_kind") == "listing":
            return f"listed {j['posted']} on {j.get('posted_from') or 'a list'}"
        return f"posting date unknown, found {j.get('first_seen', '')}"

    items = []
    for j in relevant[:TOP]:
        k, tr = _best(j)
        items.append({"score": tr.get("score", 0), "section": track_names.get(k, k), "company": j.get("company", ""),
                      "title": j.get("title", ""), "location": (j.get("location") or "")[:60], "when": when(j),
                      "url": j.get("url", ""), "key": j["key"], "uncertain": j.get("uncertain") or []})
    subject = (f"{len(relevant)} new internship{'s' if len(relevant) != 1 else ''}"
               + (f", {len(deadlines)} deadline{'s' if len(deadlines) != 1 else ''} soon" if deadlines else "")
               + (f", {len(failures)} source{'s' if len(failures) != 1 else ''} failing" if failures else "")
               + f" ({now:%b} {now.day})")
    unread = f"{page_url}#unread"
    md = [f"# {subject}", ""]
    if items:
        md += [f"## New since the last digest (best fits first)", ""]
        for i in items:
            unc = f" _(uncertain: {'; '.join(i['uncertain'])})_" if i["uncertain"] else ""
            md.append(f"- **{i['score']}** {i['company']}: [{i['title']}]({i['url']}) · {i['location']} · "
                      f"{i['when']} · {i['section']}{unc}")
        if len(relevant) > TOP:
            md.append(f"- ...and {len(relevant) - TOP} more")
    else:
        md.append("No new internships in the curated tabs since the last digest.")
    md += ["", f"All {len(new)} newly found ({others} only in All opportunities): {unread}", ""]
    if deadlines:
        md += ["## Program deadlines in the next 3 weeks (verified on the official pages)", ""]
        md += [f"- {d['date']} ({d['days']} days): {d['program']}, {d['term']} — {d['url']}" for d in deadlines]
        md.append("")
    if failures or flagged or partial:
        md += ["## Collection problems", ""]
        md += [f"- {s['name']}: {s.get('state')} — {s.get('error') or 'no error text'}"
               + (f" (last worked {s['last_success'][:10]})" if s.get("last_success") else " (never worked)")
               + (f" — check by hand: {s['careers']}" if s.get("careers") else "") for s in failures[:20]]
        md += [f"- {s['name']}: {s['suspicious']}" for s in flagged[:10]]
        if partial:
            md.append(f"- {len(partial)} source{'s' if len(partial) != 1 else ''} read only partly this run "
                      f"(postings they didn't return are kept, not treated as closed)")
        md.append("")
    md.append(f"Full page: {page_url}")
    text = "\n".join(md)
    body = "".join(
        f"<li><b>{i['score']}</b> {html.escape(i['company'])}: <a href=\"{html.escape(i['url'])}\">"
        f"{html.escape(i['title'])}</a> · {html.escape(i['location'])} · {html.escape(i['when'])} · "
        f"{html.escape(i['section'])}</li>" for i in items)
    html_out = (f"<h2>{html.escape(subject)}</h2>"
                + (f"<ul>{body}</ul>" if body else "<p>No new internships in the curated tabs.</p>")
                + f"<p><a href=\"{unread}\">All {len(new)} newly found</a></p>"
                + ("<h3>Program deadlines (verified)</h3><ul>" + "".join(
                    f"<li>{d['date']} ({d['days']} days): {html.escape(d['program'])}, {html.escape(d['term'])}</li>"
                    for d in deadlines) + "</ul>" if deadlines else "")
                + ("<h3>Collection problems</h3><ul>" + "".join(
                    f"<li>{html.escape(s['name'])}: {html.escape(str(s.get('state')))} — "
                    f"{html.escape(str(s.get('error', '')))}</li>" for s in failures[:20]) + "</ul>" if failures else ""))
    return {"subject": subject, "text": text, "html": html_out, "keys": [j["key"] for j in new],
            "aka": [k for j in new for k in j.get("aka") or []], "new": len(new), "relevant": len(relevant),
            "deadlines": len(deadlines), "failures": len(failures)}


# ---------------------------------------------------------------- delivery

def channels() -> list[str]:
    """Channels whose secrets are set (names only; values never leave os.environ)."""
    env = os.environ
    out = []
    if all(env.get(k) for k in ("SMTP_HOST", "SMTP_USERNAME", "SMTP_PASSWORD", "DIGEST_TO")):
        out.append("email")
    if env.get("NTFY_TOPIC"):
        out.append("ntfy")
    if env.get("DIGEST_WEBHOOK_URL"):
        out.append("webhook")
    return out


def _send_email(d: dict) -> None:
    env = os.environ
    msg = EmailMessage()
    msg["Subject"] = d["subject"]
    msg["From"] = env.get("DIGEST_FROM") or env["SMTP_USERNAME"]
    msg["To"] = env["DIGEST_TO"]
    msg.set_content(d["text"])
    msg.add_alternative(d["html"], subtype="html")
    with smtplib.SMTP(env["SMTP_HOST"], int(env.get("SMTP_PORT") or 587), timeout=30) as s:
        s.starttls(context=ssl.create_default_context())
        s.login(env["SMTP_USERNAME"], env["SMTP_PASSWORD"])
        s.send_message(msg)


def _post(url: str, body: bytes, headers: dict) -> None:
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=30) as resp:
        resp.read()


def _send_ntfy(d: dict) -> None:
    server = (os.environ.get("NTFY_SERVER") or "https://ntfy.sh").rstrip("/")
    _post(f"{server}/{os.environ['NTFY_TOPIC']}", d["text"][:3800].encode("utf-8"),
          {"Title": d["subject"].encode("ascii", "replace").decode(), "Markdown": "yes"})


def _send_webhook(d: dict) -> None:
    url = os.environ["DIGEST_WEBHOOK_URL"]
    key = "content" if "discord" in url else "text"
    _post(url, json.dumps({key: d["text"][:1900]}).encode("utf-8"), {"Content-Type": "application/json"})


def should_send(cfg: dict, log: dict, now_et: dt.datetime) -> tuple[bool, str]:
    if not cfg.get("enabled", False):
        return False, "off ([notify] enabled = false in profile.toml)"
    if not channels():
        return False, "on, but no delivery secrets are set"
    if now_et.hour < int(cfg.get("hour", 9)):
        return False, f"waiting for {int(cfg.get('hour', 9))}:00 ET"
    if any(x.get("day") == now_et.date().isoformat() and x.get("ok") for x in log["digests"]):
        return False, "already sent today"
    return True, ""


def deliver(d: dict, log: dict, now: dt.datetime, day: str) -> list[str]:
    """Send on every configured channel; log the postings included if any channel worked."""
    senders = {"email": _send_email, "ntfy": _send_ntfy, "webhook": _send_webhook}
    done, errors = [], []
    for ch in channels():
        try:
            senders[ch](d)
            done.append(ch)
        except Exception as e:  # noqa: BLE001 - report, never break the scan
            errors.append(f"{ch}: {e.__class__.__name__}")
    stamp = now.isoformat(timespec="seconds")
    if done:
        for k in d["keys"] + d["aka"]:
            log["sent"].setdefault(k, day)
    log["digests"] = (log["digests"] + [{"at": stamp, "day": day, "ok": bool(done), "channels": done,
                                         "errors": errors, "new": d["new"], "relevant": d["relevant"]}])[-120:]
    return errors


def prune(log: dict, today: str) -> None:
    cut = (dt.date.fromisoformat(today) - dt.timedelta(days=LOG_KEEP_DAYS)).isoformat()
    log["sent"] = {k: v for k, v in log["sent"].items() if v >= cut}


def main() -> int:
    """Print the digest the latest scan would send, from data/ (sends nothing)."""
    root = Path(__file__).resolve().parent.parent
    try:
        jobs = json.loads((root / "data" / "jobs.json").read_text(encoding="utf-8")).get("jobs", [])
    except (FileNotFoundError, ValueError):
        jobs = []
    try:
        status = json.loads((root / "data" / "last_status.json").read_text(encoding="utf-8"))
    except (FileNotFoundError, ValueError):
        status = []
    d = build(jobs, status, [], load_log(root / "data" / "notify_log.json"), dt.datetime.now(dt.timezone.utc),
              "https://jonasagront.github.io/aero-job-finder/", {})
    sys.stdout.reconfigure(encoding="utf-8")
    print(d["text"])
    print(f"\n[preview only: channels configured here: {', '.join(channels()) or 'none'}]")
    return 0


if __name__ == "__main__":
    sys.exit(main())
