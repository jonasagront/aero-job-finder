# Aero Job Finder

Every 5 hours this repo scans company career sites and internship lists for
engineering internships, scores each one against my resume, and publishes the
results to a page I can open on my phone.

**Job page:** https://jonasagront.github.io/aero-job-finder/

The page has nine tabs:

| Tab | What's in it |
|---|---|
| **New this week** | Everything from the other tabs posted in the last 7 days |
| **Summer 2027** | Aerospace and mechanical internships at aerospace companies (the main list) |
| **Motorsports** | Engineering internships at racing teams and motorsport companies (NASCAR, IndyCar, F1 and sports car teams, race engine builders), plus racing roles at any company, for spring, summer or fall 2027, since race teams hire for every part of the season |
| **Fall 2027 near UCF** | Fall 2027 internships and co-ops within 55 miles of UCF (Orlando to the Space Coast, Melbourne included), plus remote ones, any engineering discipline |
| **All engineering** | Every Summer 2027 engineering internship from any company or major, with mechanical and aerospace ranked first and a discipline filter |
| **Predicted** | Internships posted in past cycles that should come back for Summer 2027 or Fall 2027, with the date each is expected: coming up, due now, not seen yet (past last cycle's date), or already posted (see below) |
| **Posted date unknown** | Postings whose posted date couldn't be found anywhere (see below); they're kept out of the other tabs until one turns up |
| **Leads without a link** | Postings only intern-list.com has found, with a **Find posting** button instead of Apply (see below) |
| **Big names** | About 50 well-known employers and programs, grouped into space, defense primes, defense tech, aviation, labs and programs, and fellowships (SpaceX, NASA, Lockheed, Northrop, RTX, Leidos, Sandia, NREIP, SULI, Brooke Owens...): when each usually recruits (a typical window from past cycles; NASA, SMART and SULI deadlines are the published ones), how many of its postings went up in the last 15 days, the earliest posting seen this cycle, and when its first one went up last cycle |

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
came from). Postings with no date anywhere go in **Posted date unknown**.

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
**357 Summer 2027 aerospace matches** (3 in Motorsports, 15 Fall 2027 near home, 960 in All engineering, 145 leads without a direct link) as of Nov 14, 2026. Full list with filters: **[open the job page](https://jonasagront.github.io/aero-job-finder/)**

| Fit | Company | Role | Required quals met | Location | Posted | Apply |
|---|---|---|---|---|---|---|
| 100 | GE Aerospace | Test and Manufacturing Operations Intern - Bohemia, NY - Summer 2027 | 5 of 5 | Bohemia | 2026-11-12 | [Apply](https://geaerospace.wd5.myworkdayjobs.com/GE_ExternalSite/job/Bohemia/Test-and-Manufacturing-Operations-Intern---Bohemia--NY---Summer-2027_R5042960-1) |
| 100 | GE Aerospace | Propulsion Performance Engineering Intern - Bohemia, NY - Summer 2027 | 4 of 4 | Bohemia | 2026-11-05 | [Apply](https://geaerospace.wd5.myworkdayjobs.com/GE_ExternalSite/job/Bohemia/Propulsion-Performance-Engineering-Intern---Bohemia--NY---Summer-2027_R5042754-2) |
| 100 | Loft Orbital | Summer 2027 Internship – Thermal & Manufacturing Engineering | 4 of 4 | Golden, CO | 2026-10-30 | [Apply](https://jobs.lever.co/loftorbital/03f948ff-0767-4bb0-a13b-345321d63d71) |
| 100 | Sandia National Laboratories | Intern, R&D Graduate Summer - Computational Thermal & Fluid Mechanics - Onsite | 5 of 5 | Albuquerque, NM, USA | 2026-10-30 | [Apply](https://sandia.jobs/55DCABEA768C4AFD8AB93846AEE6311F25) |
| 98 | GE Aerospace | Design Engineering Intern - Bohemia, NY - Summer 2027 | 3 of 3 | Bohemia | 2026-11-10 | [Apply](https://geaerospace.wd5.myworkdayjobs.com/GE_ExternalSite/job/Bohemia/Digital-Systems-Intern---Bohemia--NY---Summer-2027_R5042864-1) |
| 97 | CesiumAstro | Summer 2027 - Mechanical Engineering Internship | 2 of 2 | Melbourne, FL | 2026-11-09 | [Apply](https://jobs.lever.co/CesiumAstro/cfcdb403-c51a-430d-a1e2-4378178714d5) |
| 97 | GE Aerospace | Working Student – Thermal Systems Design / CFD Analysis (m/f/d) | 5 of 5 | Garching | 2026-11-12 | [Apply](https://geaerospace.wd5.myworkdayjobs.com/GE_ExternalSite/job/Garching/Working-Student---Thermal-Systems-Design---CFD-Analysis--m-f-d-_R5043154-2) |
| 97 | Johns Hopkins Applied Physics Laboratory | 2027 Internship - Mechanical Engineering Intern | – | Laurel, Maryland | 2026-11-13 | [Apply](https://careers.jhuapl.edu/jobs/60389) |
| 97 | Leidos | Flight Test and Integration Summer Intern | 2 of 2 | Huntsville, AL | 2026-11-13 | [Apply](https://leidos.wd5.myworkdayjobs.com/External/job/Huntsville-AL/Flight-Test-and-Integration-Summer-Intern_R-00196666) |
| 97 | MIT Lincoln Laboratory | Summer Research Program Intern 2027, Fabrication Engineering Integration (Group 07-72) | 3 of 3 | Lexington, MA, US | 2026-11-06 | [Apply](https://careers.ll.mit.edu/job/Lexington-Summer-Research-Program-Intern-2027%2C-Fabrication-Engineering-Integration-%28Group-07-72%29-MA-02420/1448734700/) |
| 97 | MIT Lincoln Laboratory | Structural & Thermal-Fluids Engineering CO-OP, Spring/Summer 2027 (Group 07-74) | – | Lexington, MA, US | 2026-11-12 | [Apply](https://careers.ll.mit.edu/job/Lexington-Structural-&-Thermal-Fluids-Engineering-CO-OP%2C-SpringSummer-2027-%28Group-07-74%29-MA-02420/1450304600/) |
| 96 | United Launch Alliance | Composite Engineering Internship - Summer 2027 | 4 of 4 | Decatur, AL, US, 35601 | 2026-11-05 | [Apply](https://jobs.ulalaunch.com/job/Decatur-Composite-Engineering-Internship-Summer-2027-AL-35601/1427397600/) |
| 95 | Reliable Robotics | Hardware Test Engineering Intern (Summer 2027) | 2.5 of 4 | Mountain View, CA | 2026-11-13 | [Apply](https://jobs.ashbyhq.com/reliable-robotics/0af72d5a-87b7-49a1-b49e-424d28758c9e) |
| 95 | Sierra Lobo | Aerospace Engineer Intern - Spring/Summer 2027 | 4 of 5 | US-OH-Milan | 2026-11-05 | [Apply](https://jobs-sierralobo.icims.com/jobs/3533/aerospace-engineer-intern---spring-summer-2027/job) |
| 93 | Sierra Lobo | Mechanical Engineer Intern - Spring/Summer 2027 | 4 of 4 | US-OH-Milan | 2026-11-05 | [Apply](https://jobs-sierralobo.icims.com/jobs/3534/mechanical-engineer-intern---spring-summer-2027/job) |
| 92 | GE Aerospace | Working Student – Thermal Systems Design / Experimental (m/f/d) | 4 of 5 | Garching | 2026-11-12 | [Apply](https://geaerospace.wd5.myworkdayjobs.com/GE_ExternalSite/job/Garching/Working-Student---Thermal-Systems-Design---Experimental--m-f-d-_R5043157-1) |
| 91 | REGENT | Aerodynamics Engineering Intern (Summer) | 4 of 4 | North Kingstown, Rhode Island, USA | 2026-11-10 | [Apply](https://jobs.ashbyhq.com/REGENT/8bd9c9a5-04f4-4321-b837-9888a70d363d) |
| 89 | BAE Systems | Mechanical Engineer Intern Summer 2027 | 2 of 2 | Kingsport, Tennessee, United States | 2026-11-11 | [Apply](https://jobs.baesystems.com/global/en/job/132333BR) |
| 89 | Sandia National Laboratories | Intern, R&D Graduate Summer  - Weather Effects Research, Hybrid | 6 of 6 | Albuquerque, NM, USA | 2026-11-04 | [Apply](https://sandia.jobs/CBCEC290A6F548FA97BCDEBE1043A89C25) |
| 88 | RTX (Raytheon, Pratt & Whitney, Collins) | Manufacturing Engineer Co-op (Spring/Summer 2027) | 6 of 6 | US-NC-WILSON-4200 ~ 4200 Airport Dr ~ BL | 2026-11-09 | [Apply](https://globalhr.wd5.myworkdayjobs.com/REC_RTX_Ext_Gateway/job/US-NC-WILSON-4200--4200-Airport-Dr--BLDG-4200/Manufacturing-Engineer-Co-op--Spring-Summer-2027-_01887620) |
| 88 | GE Aerospace | GE Aerospace Research - Controls & Optimization Internship, 2027 | 1 of 2 | Niskayuna | 2026-11-09 | [Apply](https://geaerospace.wd5.myworkdayjobs.com/GE_ExternalSite/job/Niskayuna/GE-Aerospace-Research---Controls---Optimization-Internship--2027_R5043004-1) |
| 87 | Safran Defense & Space | Mechanical Engineering Internship 🆕 | 4 of 4 | Bedford, NH, US, 03110 | 2026-11-14 | [Apply](https://careers.safran-dsi.com/job/Bedford-Mechanical-Engineering-Internship-NH-03110/1431029700/) |
| 87 | Sandia National Laboratories | Intern, R&D Graduate Summer - Advanced Concepts Engineering, Onsite | 7 of 7 | Albuquerque, NM, USA | 2026-11-05 | [Apply](https://sandia.jobs/5A8B0975ECC947A680D7EDC34DCDEB0725) |
| 87 | Sandia National Laboratories | Intern, R&D Undergraduate Summer - Advanced Concepts Engineering, Onsite | 6 of 6 | Albuquerque, NM, USA | 2026-11-05 | [Apply](https://sandia.jobs/C11ACA40ECD4454A8EC287A2907691E725) |
| 86 | United Launch Alliance | Mechanical Engineering Internship - Summer 2027 | 3.5 of 4 | Cape Canaveral, FL, US, 32925 | 2026-11-05 | [Apply](https://jobs.ulalaunch.com/job/Cape-Canaveral-Mechanical-Engineering-Internship-Summer-2027-FL-32925/1427396400/) |
<!-- JOBS:END -->

## Expected soon

<!-- PREDICTED:START -->
**31 aerospace internships expected in the next 60 days**, from past cycles' posting dates. All of them, with filters: **[Predicted tab](https://jonasagront.github.io/aero-job-finder/#predicted)**

| Expected | Company | Role | For | Last cycle's posting date | Career site |
|---|---|---|---|---|---|
| ~2026-10-24 (due now) | Skyryse | Vehicle Design Intern | Summer 2027 | 2025-10-24 | [Open](https://job-boards.greenhouse.io/skyryse) |
| ~2026-10-30 (due now) | Relativity Space | Flight Software Engineer Intern | Summer 2027 | 2025-10-30 | [Open](https://job-boards.greenhouse.io/relativity) |
| ~2026-10-31 (due now) | Huntington Ingalls Industries | Engineering Intern | Summer 2027 | 2025-10-31 | [Open](https://careers.huntingtoningalls.com/search/?q=intern) |
| ~2026-10-31 (due now) | Northwood Space | Site Engineer Intern | Summer 2027 | 2025-10-31 | [Open](https://jobs.ashbyhq.com/NorthwoodSpace) |
| ~2026-10-31 (due now) | Peraton | Computer Engineering Intern | Summer 2027 | 2025-10-31 | [Open](https://careers-peraton.icims.com/jobs/search?ss=1&searchKeyword=intern) |
| ~2026-10-31 (due now) | Safran | Engineering Internships! | Fall 2027 | 2025-10-31 | [Open](https://careers.safran-dsi.com/search/?q=intern) |
| ~2026-11-01 (due now) | Draper | Microelectronics Integration & Test Summer Intern | Summer 2027 | 2025-11-01 | [Open](https://draper.wd5.myworkdayjobs.com/Draper_Careers) |
| ~2026-11-04 (due now) | RTX | Intern - Production and Field Support - Onsite | Summer 2027 | 2025-11-04 | [Open](https://globalhr.wd5.myworkdayjobs.com/REC_RTX_Ext_Gateway) |
| ~2026-11-04 (due now) | Space Dynamics Laboratory | Large Language Model Inference & Integration Engineer Intern - C4ISR Systems Division - LLM Inference Pipelines | Summer 2027 | 2025-11-04 | [Open](https://spacedynamicslaboratory.applytojob.com/apply) |
| ~2026-11-06 (due now) | Anduril | Perception Engineer Intern | Summer 2027 | 2024-11-06 | [Open](https://job-boards.greenhouse.io/andurilindustries) |
| ~2026-11-08 (due now) | Leidos | AI Explainability Engineer Intern | Summer 2027 | 2024-11-08 | [Open](https://leidos.wd5.myworkdayjobs.com/External) |
| ~2026-11-13 (due now) | Northrop Grumman | Engineering Intern - Radford VA | Summer 2027 | 2025-11-13 | [Open](https://ngc.wd1.myworkdayjobs.com/Northrop_Grumman_External_Site) |
| ~2026-11-21 (due now) | Leidos | Aerospace AI/ML Intern | Summer 2027 | 2025-11-11 | [Open](https://leidos.wd5.myworkdayjobs.com/External) |
| ~2026-11-21 (due now) | Northrop Grumman | Engineering Intern | Summer 2027 | 2025-11-21 | [Open](https://ngc.wd1.myworkdayjobs.com/Northrop_Grumman_External_Site) |
| ~2026-11-24 | Shield AI | Mission Systems Engineering Intern – Summer Intern | Summer 2027 | 2025-11-24 | [Open](https://jobs.lever.co/shieldai) |
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

---

## How the score works (out of 100)

- **Aerospace, up to 40** (Summer 2027 tab). Words in the title and description (propulsion,
  structures, CFD, composites, flight test...), majors listed (Aerospace Engineering earns the
  most), and whether the company is an aerospace company.
- **Engineering fit, up to 40** (Fall and All engineering tabs, in place of Aerospace). The
  title's discipline (aerospace and mechanical 24, manufacturing 18, electrical 10, civil 8,
  plain "engineering" 8...), hands-on mechanical words in the description (SolidWorks, GD&T,
  FEA, prototyping...), and whether Mechanical or Aerospace Engineering is a listed major.
- **Your skills, up to 35.** How many of my resume skills the posting asks for, weighted by
  how strong each one is. Close substitutes (NX instead of SolidWorks, Fluent instead of
  STAR-CCM+) get half credit.
- **Eligibility, up to 25.** Points come off for graduation windows that don't include
  2029, senior-only or grad-student-only roles, a GPA minimum (if a GPA is set), or a
  posting that never says what season it's for.

Fit labels: **Strong fit** 72+, **Good fit** 56 to 71, **Worth a look** below 56.
Anything below 40 is hidden from Summer 2027, and below 30 from the other tabs.

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
  feed the Motorsports tab. On Workday sites the scan also reads each site's internship filter ("Intern
  (Fixed Term)", "Co-op/Intern"...), since the site's search ranks internships among thousands of
  other jobs. The `[[popular]]`
  entries at the bottom set the Big names tab (companies and their usual recruiting months). The bottom of the job page
  shows which sources worked on the last run, so I know what to fix or remove. To let a
  company through the aerospace-only filter, add it to `[aerospace_companies]`. Career
  boards marked `aero = false` (GM, Caterpillar, Disney, Stryker...) only feed the
  All engineering and Fall tabs.
- **Career sites found automatically**: when a company on the aerospace list shows up on
  any internship list (this cycle's, or in the history from the past 15 months) with a link to a
  hiring system the scan can read, its whole career site is scanned from then on. Other employers
  get the same once they've listed 3 or more aerospace or mechanical internships in that time
  (`engineering_min` under `[discover]`); those feed All engineering and Fall only. Adding a name
  to `[aerospace_companies]` is usually enough to get a company fully covered. Found sites
  are saved in `data/discovered_boards.json` and drop out on their own if they keep failing.
- **`[predict]` in `profile.toml`**: which terms the Predicted tab covers (Summer and Fall 2027).
- **`[motorsport]` in `profile.toml`**: the Motorsports tab's terms (spring, summer and fall 2027),
  its minimum score, and the title words that make a posting count as racing work anywhere.

## Files

| Path | What it is |
|---|---|
| `run.py` | Runs the whole scan |
| `jobfinder/` | Fetching, scoring, and page-building code |
| `docs/index.html` | The job page (rebuilt every run) |
| `data/` | Saved results so the page knows what's new; `data/history.json` is every posting seen, for the Predicted tab |
| `.github/workflows/daily.yml` | The schedule (every 5 hours) |

**Note:** GitHub pauses scheduled runs in repos with no activity for 60 days. If that ever
happens, GitHub emails you; open the Actions tab and re-enable the workflow.
