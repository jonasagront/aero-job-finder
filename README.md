# Aero Job Finder

Every 6 hours this repo scans company career sites and internship lists for
engineering internships, scores each one against my resume, and publishes the
results to a page I can open on my phone.

**Job page:** https://jonasagront.github.io/aero-job-finder/

The page has seven tabs:

| Tab | What's in it |
|---|---|
| **New this week** | Everything from the other tabs posted in the last 7 days |
| **Summer 2027** | Aerospace and mechanical internships at aerospace companies (the main list) |
| **Fall 2027 near UCF** | Fall 2027 internships and co-ops within 55 miles of UCF (Orlando to the Space Coast, Melbourne included), plus remote ones, any engineering discipline |
| **All engineering** | Every Summer 2027 engineering internship from any company or major, with mechanical and aerospace ranked first and a discipline filter |
| **Posted date unknown** | Postings whose posted date couldn't be found anywhere (see below); they're kept out of the other tabs until one turns up |
| **Leads without a link** | Postings only intern-list.com has found, with a **Find posting** button instead of Apply (see below) |
| **Big names** | SpaceX, NASA, Lockheed, Northrop, RTX and other well-known employers: when each usually recruits (a typical window from past cycles; NASA and SMART deadlines are the published ones), how many of its postings are open now, and the earliest posting seen this cycle |

Leads come from intern-list.com, which links to jobright.ai instead of the company, so they get
their own tab and a **Find posting** button that searches for the company's own posting. A lead
leaves that tab on its own once a company career site the scan reads has the same job (a lead
under a division's name, like Raytheon or Collins Aerospace for RTX, counts: see `[same_company]`
in `sources.toml`).

Postings more than 15 days old are left off the page (`max_age_days` in `profile.toml`).
When a posting's source gives no posted date, the scan opens the posting's own page for one, then
checks the internship lists for the same company and title (the page then says which list the date
came from). Postings with no date anywhere go in **Posted date unknown**.

## Today's top matches

<!-- JOBS:START -->
**343 Summer 2027 aerospace matches** (7 Fall 2027 near home, 513 in All engineering, 67 leads without a direct link) as of Oct 30, 2026. Full list with filters: **[open the job page](https://jonasagront.github.io/aero-job-finder/)**

| Fit | Company | Role | Required quals met | Location | Posted | Apply |
|---|---|---|---|---|---|---|
| 100 | Axiom Space | Mechanical/Aerospace Engineering Intern (Summer 2027) | 2 of 2 | Houston | 2026-10-15 | [Apply](https://axiomspace.wd5.myworkdayjobs.com/External_Career_Site/job/Houston/Mechanical-Aerospace-Engineering-Intern--Summer-2027-_JR100766) |
| 100 | CACI | Aerospace Engineer Intern - Summer 2027 | 5 of 5 | Aberdeen Proving Ground, MD, US | 2026-10-16 | [Apply](https://caci.wd1.myworkdayjobs.com/External/job/Aberdeen-Proving-Ground-MD-US/Aerospace-Engineer-Intern---Summer-2027_333648) |
| 100 | CACI | Aerospace Engineer Intern - Summer 2027 | 5 of 5 | Aberdeen Proving Ground, MD, US | 2026-10-16 | [Apply](https://caci.wd1.myworkdayjobs.com/External/job/Aberdeen-Proving-Ground-MD-US/Aerospace-Engineer-Intern---Summer-2027_333570) |
| 100 | CesiumAstro | Summer 2027 - Flight Dynamics Internship | 3 of 3 | Huntsville, AL | 2026-10-16 | [Apply](https://jobs.lever.co/CesiumAstro/385a6217-7931-4bb4-861a-1e5651e3a998) |
| 100 | Gulfstream | Summer 2027 - IEF - Structures/ Structural Design College Intern 🆕 | 2 of 2 | Savannah, GA, US | 2026-10-15 | [Apply](https://careers.gulfstream.com/en/jobs/236094/summer-2027-ief-structures-structural-design-college-intern/) |
| 100 | Loft Orbital | Summer 2027 Internship – Mechanical Engineering | 3 of 3 | Golden, CO | 2026-10-27 | [Apply](https://jobs.lever.co/loftorbital/34edd0b7-2a5b-4efa-a379-860097784534) |
| 100 | Loft Orbital | Summer 2027 Internship - Thermal & Manufacturing Engineering 🆕 | 4 of 4 | Golden, CO | 2026-10-30 | [Apply](https://jobs.lever.co/loftorbital/03f948ff-0767-4bb0-a13b-345321d63d71) |
| 97 | Inversion Space | Avionics Mechanical Engineer - Summer Internship 2027 | 3 of 3 | Playa Vista, California, United States | 2026-10-15 | [Apply](https://job-boards.greenhouse.io/inversionspace/jobs/4744390005) |
| 97 | Johns Hopkins Applied Physics Laboratory | 2027 Internship - Mechanical Engineering Intern | – | Laurel, Maryland | 2026-10-26 | [Apply](https://careers.jhuapl.edu/jobs/60389) |
| 97 | Johns Hopkins Applied Physics Laboratory | 2027 Internship - Missile, Reentry, and Hypersonics Systems Performance | – | Laurel, Maryland | 2026-10-27 | [Apply](https://careers.jhuapl.edu/jobs/60578) |
| 97 | MIT Lincoln Laboratory | Summer Research Program Intern 2027, Structural & Thermal-Fluids Engineering (Group Group 07-74) 🆕 | – | Lexington, MA, US | 2026-10-21 | [Apply](https://careers.ll.mit.edu/job/Lexington-Summer-Research-Program-Intern-2027%2C-Structural-&-Thermal-Fluids-Engineering-%28Group-Group-07-74%29-MA-02420/1442417400/) |
| 97 | MIT Lincoln Laboratory | Summer Research Program Intern 2027, Mechanical Engineering (Group 07-71) 🆕 | – | Lexington, MA, US | 2026-10-27 | [Apply](https://careers.ll.mit.edu/job/Lexington-Summer-Research-Program-Intern-2027%2C-Mechanical-Engineering-%28Group-07-71%29-MA-02420/1434255400/) |
| 94 | RTX (Raytheon, Pratt & Whitney, Collins) | Mechanical Engineering Intern (Summer 2027) | 6 of 6 | US-CA-EL SEGUNDO-E01 ~ 2000 E El Segundo | 2026-10-28 | [Apply](https://globalhr.wd5.myworkdayjobs.com/REC_RTX_Ext_Gateway/job/US-CA-EL-SEGUNDO-E01--2000-E-El-Segundo-Blvd--BLDG-E01/Mechanical-Engineering-Intern--Summer-2027-_01883293) |
| 93 | Lockheed Martin | Mechanical Design Intern | 3 of 3 | Grand Prairie, TX | 2026-10-22 | [Apply](https://lockheedmartin.eightfold.ai/careers/job/996477505085) |
| 93 | Lockheed Martin | Mechanical Design Engineering Intern | 3 of 3 | Grand Prairie, TX | 2026-10-15 | [Apply](https://lockheedmartin.eightfold.ai/careers/job/996477394326) |
| 93 | Lockheed Martin | Mechanical Design Engineering Intern | 3 of 3 | Orlando, FL | 2026-10-18 | [Apply](https://lockheedmartin.eightfold.ai/careers/job/996477394527) |
| 93 | Loft Orbital | Summer 2027 Internship – Satellite Programs | 3 of 3 | Golden, CO | 2026-10-27 | [Apply](https://jobs.lever.co/loftorbital/d49feb08-351a-4f03-84ba-948c8df633ab) |
| 90 | Scout AI | Mechanical Engineer Intern (Summer 2027) | 4 of 4 | Sunnyvale, CA | 2026-10-27 | [Apply](https://jobs.ashbyhq.com/scout-ai/fba467c4-30e8-4ee1-8ac9-20b48e132076) |
| 90 | RTX (Raytheon, Pratt & Whitney, Collins) | Manufacturing Engineering Co-Op (Spring/Summer 2027) | 6 of 6 | US-IA-MANCHESTER-185 ~ 901 S 10th St ~ S | 2026-10-20 | [Apply](https://globalhr.wd5.myworkdayjobs.com/REC_RTX_Ext_Gateway/job/US-IA-MANCHESTER-185--901-S-10th-St--S-10TH/Manufacturing-Engineering-Co-Op--Spring-Summer-2027-_01876132) |
| 90 | Anduril | 2027 Low Observables Engineer Intern | 3 of 3 | Costa Mesa, California, United States | 2026-10-19 | [Apply](https://boards.greenhouse.io/andurilindustries/jobs/5268752007?gh_jid=5268752007) |
| 89 | AeroVironment | Aeromechanical Engineering Intern | 3 of 3 | Moorpark, CA | 2026-10-29 | [Apply](https://avav.wd1.myworkdayjobs.com/AVAV/job/Moorpark-CA/Aeromechanical-Engineering-Intern_9217) |
| 88 | CACI | Mechanical Engineering Intern - Summer 2027 | 2 of 2 | Dulles, VA, US | 2026-10-19 | [Apply](https://caci.wd1.myworkdayjobs.com/External/job/Dulles-VA-US/Mechanical-Engineering-Intern---Summer-2027_333564) |
| 88 | Lockheed Martin | Systems Integration/Electrical Test Engineer-INTERN | 2 of 2 | Cape Canaveral, FL | 2026-10-19 | [Apply](https://lockheedmartin.eightfold.ai/careers/job/996477338210) |
| 88 | MIT Lincoln Laboratory | Rapid Prototyping Aero/Mech Co-Op - Group 77 🆕 | 2 of 2 | Lexington, MA, US | 2026-10-22 | [Apply](https://careers.ll.mit.edu/job/Lexington-Rapid-Prototyping-AeroMech-Co-Op-Group-77-MA-02420/1423005300/) |
| 87 | Safran Defense & Space | Mechanical Engineering Internship | 4 of 4 | Bedford, NH, US, 03110 | 2026-10-16 | [Apply](https://careers.safran-dsi.com/job/Bedford-Mechanical-Engineering-Internship-NH-03110/1431029700/) |
<!-- JOBS:END -->

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

From then on it runs by itself every 6 hours.

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
  Greenhouse, Lever, Ashby, Workday, Eightfold, SuccessFactors (L3Harris, ULA, HII, Leonardo DRS),
  iCIMS (GD Mission Systems, Joby, Peraton), Jibe (JHU APL, Spirit), Oracle (Honeywell, Howmet),
  Phenom (BAE Systems), Taleo (Textron, Bell), Pinpoint, BambooHR, Rippling, SmartRecruiters,
  Workable, Gem and JazzHR, plus the Simplify list, the Space Capital board and intern-list.com;
  each section of the file explains which part of a company's job link to copy. The `[[popular]]`
  entries at the bottom set the Big names tab (companies and their usual recruiting months). The bottom of the job page
  shows which sources worked on the last run, so I know what to fix or remove. To let a
  company through the aerospace-only filter, add it to `[aerospace_companies]`. Career
  boards marked `aero = false` (GM, Caterpillar, Disney, Stryker...) only feed the
  All engineering and Fall tabs.
- **Career sites found automatically**: when a company on the aerospace list shows up on
  any internship list (this year's or last year's) with a link to a hiring system the scan
  can read, its whole career site is scanned from then on. Adding a name to
  `[aerospace_companies]` is usually enough to get a company fully covered. Found sites
  are saved in `data/discovered_boards.json` and drop out on their own if they keep failing.

## Files

| Path | What it is |
|---|---|
| `run.py` | Runs the whole scan |
| `jobfinder/` | Fetching, scoring, and page-building code |
| `docs/index.html` | The job page (rebuilt every run) |
| `data/` | Saved results so the page knows what's new |
| `.github/workflows/daily.yml` | The schedule (every 6 hours) |

**Note:** GitHub pauses scheduled runs in repos with no activity for 60 days. If that ever
happens, GitHub emails you; open the Actions tab and re-enable the workflow.
