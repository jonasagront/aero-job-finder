# Aero Job Finder

Every 5 hours this repo scans company career sites and internship lists for
engineering internships, scores each one against my resume, and publishes the
results to a page I can open on my phone.

**Job page:** https://jonasagront.github.io/aero-job-finder/

**New internships** and **Unread** sit in the top bar next to the update time; the rest are in the row of tabs:

| Tab | What's in it |
|---|---|
| **New internships** | Everything the scan found in the 3 days up to the latest update, from every tab, grouped by the scan that found it ("This update", "Earlier today · 12:06 PM scan", "Yesterday"...) |
| **Unread** | Every opportunity found since you started using the queue that you haven't reviewed (opened with Apply, or marked read), saved, applied to or dismissed, however many days ago it was found, as long as it's still within the 15-day limit (see below) |
| **New this week** | Everything from the other tabs posted in the last 7 days |
| **Summer 2027** | Aerospace and mechanical internships at aerospace companies (the main list) |
| **Motorsports** | Engineering internships at racing teams and motorsport companies (NASCAR, IndyCar, F1 and sports car teams, race engine builders), plus racing roles at any company, for spring, summer or fall 2027, since race teams hire for every part of the season |
| **Fall 2027 near UCF** | Fall 2027 internships and co-ops within 55 miles of UCF (Orlando to the Space Coast, Melbourne included), plus remote ones, any engineering discipline |
| **All engineering** | Every Summer 2027 engineering internship from any company or major, with mechanical and aerospace ranked first and a discipline filter |
| **All opportunities** | Every engineering internship and student program the scan found in the last 15 days, at any fit score, any term and anywhere in the U.S., with its own filters: term and year, state, remote, distance from UCF, posted date known or not, uncertain or not, and eligibility problems hidden or not. Active filters show as chips with a Reset button; they don't change the other tabs |
| **Programs** | NASA OSTEM, JPL, NREIP, AFRL Scholars, SULI, SMART, Brooke Owens and Patti Grace Smith: status, deadlines and eligibility as each official page states them, with the date verified (see below) |
| **Predicted** | Internships posted in past cycles that should come back for Summer 2027 or Fall 2027, with the date each is expected: coming up, due now, not seen yet (past last cycle's date), or already posted (see below) |
| **Posting date unknown** | Postings whose posted date couldn't be found anywhere. They're also in the other tabs, labeled "Posting date unknown" with the day the scan first found them |
| **Leads without a link** | Postings only intern-list.com has found, with a **Find posting** button instead of Apply (see below) |
| **Big names** | About 50 well-known employers and programs, grouped into space, defense primes, defense tech, aviation, labs and programs, and fellowships (SpaceX, NASA, Lockheed, Northrop, RTX, Leidos, Sandia, NREIP, SULI, Brooke Owens...): when each usually recruits (a typical window from past cycles; NASA, SMART and SULI deadlines are the published ones), how many of its postings went up in the last 15 days, the earliest posting seen this cycle, and when its first one went up last cycle. A company whose scan failed or was cut short says so instead of "nothing posted" |
| **My list** | What you saved or applied to, plus a record of ones that are no longer listed; Export and Import move it between devices |

**Scores rank, they don't hide.** Each posting first passes basic checks: it's an internship, co-op
or student program (titles like Student Engineer, Engineering Trainee or Undergraduate Research
Assistant count, and so does a hiring system's own "Intern" employment type; ambiguous ones are judged
on the description), it's engineering work (from the title, or the majors the description lists), it's
in the U.S., and it's within the age limit. Grad-student-only roles and full-time jobs with
student-sounding titles are dropped. Everything that passes is in **All opportunities**; the curated
tabs add their own score minimums and terms. A posting that couldn't be fully checked (no description,
student status unclear, no term named) is kept and tagged with a "?" saying what's uncertain, and
eligibility problems (graduation window, seniors only, GPA) stay visible as red tags. "Why this score"
says why a posting isn't in each curated tab.

**Dates.** A posting shows the employer's own posted date when its hiring system or page gives one,
"Listed ... on <list>" when only an internship list or job board dated it, or "Posting date unknown",
always next to when the scan first found it. Found is never shown as posted. The first-found date is
kept in `data/seen.json` for 120 days after a posting was last on the page, so a posting that drops
off (a source outage, a relisting under a new link) keeps its original date when it comes back.

**Coverage.** Under the headline numbers, **Sources this update** counts sources read fully, partial
(the request worked but something cut it short: a page cap, a page that failed, a site repeating
itself, or the run's 24-minute collection budget running out on a slow, rate-limited day), failed (worked within the last day), stale (hasn't worked for over a day) and needing setup,
and flags any source whose count suddenly dropped (40 postings to 0, say). Details lists each affected
source's last successful scan, error and career-site link, the repair queue for boards found
automatically, the coverage audit, and what the filters dropped. A posting that's missing from a
partial or failed scan is kept, tagged "Not re-checked since ...", until it passes the 15-day limit;
only a posting missing from a complete scan counts as closed.

**Unread queue and device sync.** Unread, saved, applied and dismissed marks live in your browser's
storage, so they don't sync between your phone and computer by themselves. **My list → Export my data**
saves them to a file and **Import** on the other device merges them in. The queue starts with the last
3 days of finds the first time you open the page. A posting relisted under a new link carries its
marks over, so it isn't announced twice.

Leads come from intern-list.com, which links to jobright.ai instead of the company, so they get
their own tab and a **Find posting** button that searches for the company's own posting. A lead
leaves that tab on its own once a company career site the scan reads has the same job (a lead
under a division's name, like Raytheon or Collins Aerospace for RTX, counts: see `[same_company]`
in `sources.toml`).

Postings more than 15 days old are left off the page (`max_age_days` in `profile.toml`). Age
counts from the posted date, or for a posting with no date anywhere, from the day the scan first
saw it. Closed postings drop off on their own once they leave their source. The internship
lists and job boards keep some postings for days after the company takes them down, so before
one of their postings goes on the page the scan asks the company's own hiring system whether
it's still open (Greenhouse, Lever, Ashby, Workday and SmartRecruiters say so directly; other
sites count as closed when the posting's page is gone).
When a posting's source gives no posted date, the scan opens the posting's own page for one, then
checks the internship lists for the same company and title (the page then says which list the date
came from). Postings with no date anywhere stay in the normal tabs, labeled **Posting date unknown**
with the day the scan first found them, and the 15-day limit counts from that day.

**How the Predicted tab guesses dates.** `data/history.json` holds every engineering internship
seen so far with its posted date: old copies of the Simplify list back to 2023 (pinned to a
commit in `sources.toml` under `[history]`), plus everything each scan reads, closed postings
included. Postings from the same company with similar titles count as one role. Each past posting
date moves forward to this cycle (posted Sep 10, 2025 for Summer 2026 means expected around
Sep 10, 2026 for Summer 2027), using the middle date when a role ran several cycles. A role
counts as posted once the company posts one with a similar title this cycle; one expected more
than three weeks ago that hasn't shown up is "not seen yet". Roles that skipped the last two
cycles are dropped. The lists don't catch every company's postings, but each year the scan's own
history fills more of that in.

## Today's top matches

<!-- JOBS:START -->
**369 Summer 2027 aerospace matches** (2 in Motorsports, 17 Fall 2027 near home, 1237 in All engineering, 171 leads without a direct link) as of Nov 23, 2026. Full list with filters: **[open the job page](https://jonasagront.github.io/aero-job-finder/)**

| Fit | Company | Role | Preferred quals | Required quals | Location | Posted | Apply |
|---|---|---|---|---|---|---|---|
| 98 | GE Aerospace | Working Student – Thermal Systems Design / CFD Analysis (m/f/d) | 4 of 4 | 6 of 6 | Garching | 2026-11-12 | [Apply](https://geaerospace.wd5.myworkdayjobs.com/GE_ExternalSite/job/Garching/Working-Student---Thermal-Systems-Design---CFD-Analysis--m-f-d-_R5043154-2) |
| 92 | L3Harris | Intern, Manufacturing Engineer | 2 of 2 | 3 of 3 | Canoga Park, CA, US, 91311 | 2026-11-09 | [Apply](https://jobs.l3harris.com/job/Canoga-Park-Intern%2C-Manufacturing-Engineer-CA-91311/1448973300/) |
| 91 | RTX (Raytheon, Pratt & Whitney, Collins) | Manufacturing Engineering Intern (Summer 2027) | 1 of 1 | 3 of 3 | US-WA-SPOKANE-11135 ~ 11135 W Westbow Ln | 2026-11-17 | [Apply](https://globalhr.wd5.myworkdayjobs.com/REC_RTX_Ext_Gateway/job/US-WA-SPOKANE-11135--11135-W-Westbow-Ln--WESTBOW/Manufacturing-Engineering-Intern--Summer-2027-_01888202) |
| 90 | Intuitive Machines | Satellite Mission Operations Intern – Altus | 3 of 4 | 2 of 2 | Houston, TX; Houston, TX | 2026-11-13 | [Apply](https://workforcenow.adp.com/mascsr/default/mdf/recruitment/recruitment.html?cid=b0e24f83-6e4d-492d-9d6a-bc0fea197d6a&lang=en_US&locale=en_US&ccId=19000101_000001&jobId=9207519358072_165) |
| 90 | Shield AI (shield) | 2027 June Co-op - Hardware Test - #6426 | 2 of 2 | 2 of 2 | Dallas, TX, US | 2026-11-12 | [Apply](https://jobs.ashbyhq.com/shield/ec8a822c-ccbf-4b4e-b41c-2f0db5c8342d) |
| 89 | Intuitive Machines | Guidance, Navigation & Controls (GNC) Intern | 1 of 1 | 3 of 3 | Houston, TX; Houston, TX | 2026-11-13 | [Apply](https://workforcenow.adp.com/mascsr/default/mdf/recruitment/recruitment.html?cid=b0e24f83-6e4d-492d-9d6a-bc0fea197d6a&lang=en_US&locale=en_US&ccId=19000101_000001&jobId=9207519357554_173) |
| 88 | The Aerospace Corporation | 2027 Structural Engineering Undergraduate Intern | – | 6 of 6 | El Segundo, CA | 2026-11-16 | [Apply](https://aero.wd5.myworkdayjobs.com/External/job/El-Segundo-CA/XMLNAME-2027-Structural-Engineering-Undergraduate-Intern_R017211) |
| 87 | Reliable Robotics | Flight Test Integration Engineer Intern (Summer 2027) | 2 of 3 | 2 of 2 | Mountain View, CA | 2026-11-13 | [Apply](https://jobs.ashbyhq.com/reliable-robotics/1d020651-71bb-4e47-baa6-2286dc780d96) |
| 86 | Intuitive Machines | Assembly Integration & Test Intern | 1 of 1 | 2 of 2 | Houston, TX | 2026-11-13 | [Apply](https://workforcenow.adp.com/mascsr/default/mdf/recruitment/recruitment.html?cid=b0e24f83-6e4d-492d-9d6a-bc0fea197d6a&lang=en_US&locale=en_US&ccId=19000101_000001&jobId=9207519595481_89) |
| 86 | Lockheed Martin | aerospace engineering intern | 1 of 1 | 3 of 3 | Littleton, CO | 2026-11-12 | [Apply](https://lockheedmartin.eightfold.ai/careers/job/996477909687) |
| 85 | MIT Lincoln Laboratory | Summer Research Program Intern 2027, Advanced Sensor Systems and Test Beds (Group 03-33) | 1 of 1 | 4 of 4 | Lexington, MA, US | 2026-11-17 | [Apply](https://careers.ll.mit.edu/job/Lexington-Summer-Research-Program-Intern-2027%2C-Advanced-Sensor-Systems-and-Test-Beds-%28Group-03-33%29-MA-02420/1441287700/) |
| 85 | Lockheed Martin | Aeronautical Engineering Intern 🆕 | 3 of 4 | 3 of 3 | King of Prussia, PA | 2026-11-23 | [Apply](https://lockheedmartin.eightfold.ai/careers/job/996478125490) |
| 85 | Sandia National Laboratories | Intern, R&D Graduate Year Round - Concentrating Solar Thermal Technologies, Onsite | – | 2 of 2 | Albuquerque, NM, USA | 2026-11-19 | [Apply](https://sandia.jobs/535112F90DDF471BB17D1255B71A36D925) |
| 85 | L3Harris | Intern, Manufacturing Engineer | 2 of 2 | 1.5 of 2 | Canoga Park, CA, US, 91311 | 2026-11-09 | [Apply](https://jobs.l3harris.com/job/Canoga-Park-Intern%2C-Manufacturing-Engineer-CA-91311/1448982100/) |
| 85 | GE Aerospace | Test and Manufacturing Operations Intern - Bohemia, NY - Summer 2027 | 4.5 of 7 | 8.5 of 9 | Bohemia | 2026-11-12 | [Apply](https://geaerospace.wd5.myworkdayjobs.com/GE_ExternalSite/job/Bohemia/Test-and-Manufacturing-Operations-Intern---Bohemia--NY---Summer-2027_R5042960-1) |
| 84 | Howmet Aerospace | Process Engineer Co-Op | 2 of 2 | 2 of 2 | LaPorte, IN, United States | 2026-11-20 | [Apply](https://fa-exty-saasfaprod1.fa.ocs.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1/job/120667) |
| 84 | Intuitive Machines | Structures and Design Intern | 3 of 5 | 3 of 3 | Houston, TX; Houston, TX | 2026-11-17 | [Apply](https://workforcenow.adp.com/mascsr/default/mdf/recruitment/recruitment.html?cid=b0e24f83-6e4d-492d-9d6a-bc0fea197d6a&lang=en_US&locale=en_US&ccId=19000101_000001&jobId=9207523114195_165) |
| 84 | Reliable Robotics | Flight Simulation Engineering Intern (Summer 2027) | 1 of 1 | 2 of 2 | Mountain View, CA | 2026-11-13 | [Apply](https://jobs.ashbyhq.com/reliable-robotics/0cd44e07-169f-4664-bf31-cded94b93deb) |
| 83 | Johns Hopkins Applied Physics Laboratory | 2027 Internship - Vehicle Design and Technologies Intern | – | – | Laurel, Maryland | 2026-11-18 | [Apply](https://careers.jhuapl.edu/jobs/60909) |
| 83 | Reliable Robotics | Hardware Test Engineering Intern (Summer 2027) | 2.5 of 3 | 3.5 of 6 | Mountain View, CA | 2026-11-13 | [Apply](https://jobs.ashbyhq.com/reliable-robotics/0af72d5a-87b7-49a1-b49e-424d28758c9e) |
| 82 | Safran Defense & Space | Mechanical Engineering Internship | – | 4 of 4 | Bedford, NH, US, 03110 | 2026-11-14 | [Apply](https://careers.safran-dsi.com/job/Bedford-Mechanical-Engineering-Internship-NH-03110/1431029700/) |
| 82 | Scout Space | Mechanical Engineering Intern (Summer 2027) | 1 of 1 | 3 of 3 | Reston, VA | 2026-11-19 | [Apply](https://job-boards.greenhouse.io/scoutspace/jobs/5489237008) |
| 82 | MIT Lincoln Laboratory | Summer Research Program Intern 2027, Systems & Analysis (Group 10-09) | 3 of 3 | – | Lexington, MA, US | 2026-11-11 | [Apply](https://careers.ll.mit.edu/job/Lexington-Summer-Research-Program-Intern-2027%2C-Systems-&-Analysis-%28Group-10-09%29-MA-02420/1439633800/) |
| 82 | The Aerospace Corporation | 2027 Communication Architectures Modeling and Analysis Engineering Grad Intern | – | 5 of 5 | El Segundo, CA | 2026-11-16 | [Apply](https://aero.wd5.myworkdayjobs.com/External/job/El-Segundo-CA/XMLNAME-2027-Communication-Architectures-Modeling-and-Analysis-Engineering-Grad-Intern_R017010) |
| 82 | The Aerospace Corporation | 2027 Communication Architectures Modeling and Analysis Engineering Undergraduate Intern | – | 5 of 5 | El Segundo, CA | 2026-11-16 | [Apply](https://aero.wd5.myworkdayjobs.com/External/job/El-Segundo-CA/XMLNAME-2027-Communication-Architectures-Modeling-and-Analysis-Engineering-Undergraduate-Intern_R017009) |
<!-- JOBS:END -->

## Expected soon

<!-- PREDICTED:START -->
**24 aerospace internships expected in the next 60 days**, from past cycles' posting dates. All of them, with filters: **[Predicted tab](https://jonasagront.github.io/aero-job-finder/#predicted)**

| Expected | Company | Role | For | Last cycle's posting date | Career site |
|---|---|---|---|---|---|
| ~2026-11-04 (due now) | RTX | Intern - Production and Field Support - Onsite | Summer 2027 | 2025-11-04 | [Open](https://globalhr.wd5.myworkdayjobs.com/REC_RTX_Ext_Gateway) |
| ~2026-11-04 (due now) | Space Dynamics Laboratory | Large Language Model Inference & Integration Engineer Intern - C4ISR Systems Division - LLM Inference Pipelines | Summer 2027 | 2025-11-04 | [Open](https://spacedynamicslaboratory.applytojob.com/apply) |
| ~2026-11-06 (due now) | Anduril | Perception Engineer Intern | Summer 2027 | 2024-11-06 | [Open](https://job-boards.greenhouse.io/andurilindustries) |
| ~2026-11-08 (due now) | Leidos | AI Explainability Engineer Intern | Summer 2027 | 2024-11-08 | [Open](https://leidos.wd5.myworkdayjobs.com/External) |
| ~2026-11-13 (due now) | Northrop Grumman | Engineering Intern - Radford VA | Summer 2027 | 2025-11-13 | [Open](https://ngc.wd1.myworkdayjobs.com/Northrop_Grumman_External_Site) |
| ~2026-11-21 (due now) | Leidos | Aerospace AI/ML Intern | Summer 2027 | 2025-11-11 | [Open](https://leidos.wd5.myworkdayjobs.com/External) |
| ~2026-11-21 (due now) | Northrop Grumman | Engineering Intern | Summer 2027 | 2025-11-21 | [Open](https://ngc.wd1.myworkdayjobs.com/Northrop_Grumman_External_Site) |
| ~2026-11-24 (due now) | Shield AI | Mission Systems Engineering Intern – Summer Intern | Summer 2027 | 2025-11-24 | [Open](https://jobs.lever.co/shieldai) |
| ~2026-11-25 (due now) | LeoLabs | Hardware Engineering Intern | Summer 2027 | 2025-11-25 | [Open](https://job-boards.greenhouse.io/leolabsinc) |
| ~2026-11-25 (due now) | LeoLabs | Hardware Engineering Intern | Fall 2027 | 2025-11-25 | [Open](https://job-boards.greenhouse.io/leolabsinc) |
| ~2026-11-27 (due now) | Shield AI | Intern - Radio Frequency Engineering | Summer 2027 | 2025-11-27 | [Open](https://jobs.lever.co/shieldai) |
| ~2026-12-01 | Shield AI | Flight Test Engineering Intern | Summer 2027 | 2025-12-01 | [Open](https://jobs.lever.co/shieldai) |
| ~2026-12-06 | Parsons | Space Systems Engineer Intern | Summer 2027 | 2024-12-06 | [Open](https://parsons.wd5.myworkdayjobs.com/search) |
| ~2026-12-10 | General Dynamics Mission Systems | Intern Engineer Co-op - Start | Summer 2027 | 2025-12-10 | [Open](https://careers-gdeb.icims.com/jobs/search?ss=1&searchKeyword=intern) |
| ~2026-12-12 | Nightwing | RF Engineering Intern | Summer 2027 | 2025-12-12 | [Open](https://nwis.wd12.myworkdayjobs.com/NW) |
<!-- PREDICTED:END -->

---

## One-time setup (about 10 minutes)

### 1. Upload the files
1. Unzip `aero-job-finder.zip` on your computer.
2. Open https://github.com/jonasagront/aero-job-finder and click **uploading an existing file**
   (or **Add file → Upload files**).
3. Open the unzipped folder, select **everything inside it**, and drag it onto the page.
   - **On a Mac:** the `.github` folder is hidden. In Finder press **Cmd + Shift + .**
     (period) to show it, then select everything.
4. Click **Commit changes**.
5. Check that the repo now shows a `.github` folder. If it doesn't, click
   **Add file → Create new file**, type `.github/workflows/daily.yml` as the name
   (the slashes create the folders), paste in the contents of that file from the zip,
   and click **Commit changes**.

### 2. Turn on the job page
1. In the repo, go to **Settings → Pages**.
2. Under **Build and deployment**, set **Source** to **Deploy from a branch**.
3. Set the branch to **main** and the folder to **/docs**, then click **Save**.

### 3. Run the first scan
1. Go to the **Actions** tab. If GitHub asks, click **I understand my workflows, go ahead and enable them**.
2. Click **Daily job scan** on the left, then **Run workflow → Run workflow**.
3. Wait about 5 minutes for a green check mark. Your page updates a minute or two after that.

From then on it runs by itself every 5 hours.

---

## Optional upgrades

Add these under **Settings → Secrets and variables → Actions → New repository secret**.
Secrets stay private even though the repo is public.

| Secret | What it adds | Where to get it |
|---|---|---|
| `USAJOBS_API_KEY` and `USAJOBS_EMAIL` | Federal student jobs (Air Force, Navy, Army, NASA, DoD) | Free at https://developer.usajobs.gov/apirequest/ (use the same email for both) |
| `ANTHROPIC_API_KEY` | Claude writes a one-sentence fit review and a "lead with this" tip for top matches | https://console.anthropic.com (pay-as-you-go, about 20 reviews a day by default) |
| Digest secrets (below) | The optional daily digest | Your email provider, ntfy.sh, or a Discord/Slack webhook |

Without these secrets, those sources show as "needs setup" in the coverage line; nothing pretends
to have read them.

### Daily digest (off until you turn it on)

Once a day it sends the internships found since the last digest (best fits first, linking to the
Unread view for the rest), program deadlines in the next 3 weeks that were verified on the official
pages, and any sources that are failing. Every scan writes what it would send to
`data/digest_preview.md`, so you can read it before turning anything on (`python -m jobfinder.digest`
prints the same thing locally). Nothing is ever sent until **both**:

1. `enabled = true` under `[notify]` in `profile.toml` (`hour` sets the earliest Eastern hour it goes
   out; scans run about every 5 hours, so it goes on the first scan after that hour), and
2. at least one channel's secrets are set:
   - **Email:** `SMTP_HOST`, `SMTP_USERNAME`, `SMTP_PASSWORD`, `DIGEST_TO` (optional `SMTP_PORT`,
     default 587 with STARTTLS, and `DIGEST_FROM`). For Gmail: host `smtp.gmail.com` and an
     [app password](https://myaccount.google.com/apppasswords), not your normal password.
   - **Phone push:** `NTFY_TOPIC` (a long random name; anyone who knows it can read the messages),
     then subscribe to that topic in the ntfy app. Optional `NTFY_SERVER`.
   - **Discord or Slack:** `DIGEST_WEBHOOK_URL`, an incoming-webhook address.

`data/notify_log.json` records every posting already sent (by its job ID, and its old ID if it was
relisted), so nothing is announced twice. Secrets stay in GitHub's secret store; the repo never
holds them.

---

## How the score works (out of 100)

Most of the score comes from the posting's own qualification lists, checked bullet by bullet
against my resume and portfolio (`[[skill]]` and `[[evidence]]` in `profile.toml`). A bullet
my resume backs up counts in full, light exposure counts half.

- **Preferred qualifications, up to 40.** The share of the posting's preferred list my
  resume shows. This is what recruiters use to pick between applicants who all meet the
  basics, so it weighs most. A technical topic my resume doesn't show counts against it.
- **Required qualifications, up to 25.** The share of required bullets I meet, of those that
  could be checked (GPA without a GPA set, for example, can't be). Each required bullet I
  clearly miss also takes 5 off the total (up to 15).
- **Aerospace, up to 20** (Summer 2027 tab). Words in the title and description (propulsion,
  structures, CFD, composites, flight test...), majors listed (Aerospace Engineering earns the
  most), and whether the company is an aerospace company.
- **Engineering fit, up to 20** (Motorsports, Fall and All engineering tabs, in place of
  Aerospace). The title's discipline (aerospace and mechanical first), hands-on mechanical words
  in the description (SolidWorks, GD&T, FEA, prototyping...), and whether Mechanical or
  Aerospace Engineering is a listed major.
- **Eligibility, up to 15.** Points come off for graduation windows that don't include
  2029, senior-only or grad-student-only roles, a GPA minimum (if a GPA is set), or a
  posting that never says what season it's for.

A posting with no preferred list (or too short a one to judge) uses how many of my resume
skills it asks for instead, at 75% weight, so it can't outrank one whose preferred list I
actually match.

Fit labels: **Strong fit** 72+, **Good fit** 56 to 71, **Worth a look** below 56.
Anything below 40 is left out of Summer 2027, and below 30 out of the other curated tabs, but it
stays in **All opportunities**, ranked by the same score.

Tags like **U.S. person / ITAR** and **Clearance** are shown so I can filter quickly;
they don't change the score.

## Tuning it

- **`profile.toml`**: my skills, the aerospace keywords, titles to skip, the minimum score.
  Add a skill when I learn one (MATLAB next!) and future scores pick it up.
  `aerospace_companies_only = true` hides postings from companies that aren't on the
  aerospace list from the Summer 2027 tab (the big lists otherwise pull in chip makers,
  carmakers, and so on); All engineering and Fall take any company.
  `[fall]` sets the home point and radius, `[broad]` the All engineering tab, and
  `[engineering]` the disciplines and their points.
- **`sources.toml`**: which companies and lists get checked. It reads company career sites on
  Greenhouse, Lever, Ashby, Workday, Eightfold, SuccessFactors (L3Harris, ULA, HII, Bombardier),
  iCIMS (GD Mission Systems, Joby, Peraton, Sierra Lobo), Jibe (JHU APL, Spirit, V2X, SPA), Oracle (Honeywell, Howmet, SAIC),
  Phenom (BAE Systems, MITRE, Virgin Galactic), Taleo (Textron, Bell, Textron Aviation), BrassRing (General Atomics), DirectEmployers .jobs
  feeds (Sandia, Jacobs), Los Alamos's job search, Avature and plain search pages (Siemens Energy, Gulfstream, Redwire),
  ADP Workforce Now (Kaman, Intuitive Machines, Sidus Space, Team Penske), UKG (TCOM, ARA, IndyCar), Paycor (York Space, Craig Technologies, Ilmor),
  Paylocity (Orbion), isolved/ApplicantPro (X-Bow, Bastion), Breezy HR (Embraer, Benchmark Space), Pinpoint, BambooHR, Rippling, SmartRecruiters,
  Workable, Gem and JazzHR, plus the Simplify list, a mechanical engineering internship list (published as a CSV),
  intern-list.com, the Space Capital board, ten venture firms' portfolio boards (Lux, 8VC, DCVC, Khosla, General
  Catalyst, Accel, Energy Impact Partners, Techstars, Eclipse, The Engine) and RacerJobs (where most NASCAR teams post);
  each section of the file explains which part of a company's job link to copy.
  `[motorsport_companies]` sets which companies count as motorsport, and boards marked `motorsport = true`
  feed the Motorsports tab. Workday sites list their openings newest first, so the scan reads each
  one from the top until a whole page is older than the 15-day limit (plus 3 days' margin); every title
  in that window is checked, however it's worded. The order is checked as it's read, and a site that
  isn't newest first is read whole, or through its internship filter ("Intern (Fixed Term)",
  "Co-op/Intern"...) and searches read to their last page. (The old scan stopped a search at the first
  page with no internship titles, which on Northrop's site was page 1 of 82.) Oracle, UKG, Phenom,
  SmartRecruiters and iCIMS searches stop the same way when their results are newest first. Workday
  requests are paced per site, and a run stops turning pages after 24 minutes so it always publishes;
  sources cut short are marked partial. The `[[popular]]`
  entries at the bottom set the Big names tab (companies and their usual recruiting months). The bottom of the job page
  shows which sources worked on the last run, so I know what to fix or remove. To let a
  company through the aerospace-only filter, add it to `[aerospace_companies]`. Career
  boards marked `aero = false` (GM, Caterpillar, Disney, Stryker...) only feed the
  All engineering and Fall tabs.
- **Career sites found automatically**: when a company on the aerospace list shows up on
  any internship list (this cycle's, or in the history from the past 15 months) with a link to a
  hiring system the scan can read (Greenhouse, Lever, Ashby, Workday, Oracle, SuccessFactors, Jibe,
  iCIMS, SmartRecruiters, Workable, BambooHR, Rippling, Breezy, JazzHR, Pinpoint, Gem, ADP, UKG,
  BrassRing, ApplicantPro), its whole career site is scanned from then on. Other employers are scanned
  once they've listed 3 or more aerospace or mechanical internships in that time (`engineering_min`
  under `[discover]`); with one or two, their board joins a **candidate queue** and a dozen candidates
  are tried each run, validated when they answer. Separately, names in `[aerospace_companies]`,
  `[motorsport_companies]` and `[discover] seeds` (robotics, test labs, manufacturing, energy,
  racing teams) that have no board yet are **looked up by name** on Greenhouse, Lever, Ashby,
  SmartRecruiters and Workable, 12 a run; a board only counts when the system's own company name
  (or its postings' text) matches. Boards are told apart by address, not company name, so a
  company's separate boards (an intern board, an early-talent site, a division) are all read.
  Found sites are saved in `data/discovered_boards.json` with where each came from. One that fails
  goes into a **repair queue**: retried every run three times, then after 1, 2, 4, 8 and at most 14
  days, and never dropped; if the lists start linking the company to a different hiring system, the
  new board replaces it. The page's coverage details list the repair queue, boards added this run,
  candidates, and hiring systems the scan can't read yet (with how many relevant postings use them).
- **`programs.toml`**: the Programs tab. Each program's status, deadlines and eligibility are copied
  from its official page with the date verified; a date the page doesn't state isn't filled in, and
  past-cycle timing is marked as an estimate. Each scan re-reads the pages it can and tags a program
  "Page changed: re-check" when its page changes; update the entry and its `verified` date then.
- **Coverage audit**: each run re-reads a few boards (rotating) as completely as the site allows
  (Workday sites in full) and checks every in-scope posting there (internship, engineering, U.S.,
  within 15 days) against the page. Misses are classified by where they were lost (discovery,
  collection, pagination, parsing, deduplication, filtering, display) and saved with their links in
  `data/coverage_audit.json`. The page reports coverage for the audited boards only.
- **What got dropped**: `data/rejections.json` counts every posting the filters dropped by reason,
  with examples, so filtering losses can be checked.
- **`[predict]` in `profile.toml`**: which terms the Predicted tab covers (Summer and Fall 2027).
- **`[motorsport]` in `profile.toml`**: the Motorsports tab's terms (spring, summer and fall 2027),
  its minimum score, and the title words that make a posting count as racing work anywhere.

## Files

| Path | What it is |
|---|---|
| `run.py` | Runs the whole scan |
| `jobfinder/` | Fetching, scoring, and page-building code |
| `programs.toml` | The Programs tab's verified program details |
| `tests/` | Checks for the 15-day limit, pagination, partial sources, low-score retention, undated postings, first-seen dates and duplicates (`python -m unittest discover tests`; the workflow runs them before each scan) |
| `docs/index.html` | The job page (rebuilt every run) |
| `data/` | Saved results: `jobs.json` (the page's postings), `seen.json` (when each posting was first found), `history.json` (every posting seen, for the Predicted tab), `source_health.json` and `last_status.json` (how each source did), `discovered_boards.json` and `discovery.json` (found boards, repair queue, name lookups), `coverage_audit.json`, `rejections.json`, `programs.json` (page checks), `digest_preview.md` and `notify_log.json` |
| `.github/workflows/daily.yml` | The schedule (every 5 hours) |

**Note:** GitHub pauses scheduled runs in repos with no activity for 60 days. If that ever
happens, GitHub emails you; open the Actions tab and re-enable the workflow.
