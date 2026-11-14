"""Build docs/index.html (your job page) and the table at the top of README.md."""
from __future__ import annotations

import datetime as dt
import json
import re
from pathlib import Path

TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Internship scan</title>
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='4' fill='%23111316'/%3E%3Cpath d='M8 23 16 7l8 16-8-4z' fill='%23FF7B3A'/%3E%3C/svg%3E">
<script>try{document.documentElement.setAttribute('data-theme',localStorage.getItem('ajf-theme')||'light')}catch(e){}</script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600&display=swap" rel="stylesheet">
<style>
:root{
  --bg:#F7F7F4; --surface:#FFFFFF; --ink:#111316; --ink2:#3B4046; --muted:#686E74; --faint:#9A9FA4;
  --line:#DFDFD8; --line2:#C9C9C1; --accent:#C2410C; --accent-bg:rgba(194,65,12,.09);
  --pos:#1D7348; --mid:#2B579A; --low:#8A6510; --neg:#B0361F;
  --sans:"IBM Plex Sans",system-ui,-apple-system,"Segoe UI",sans-serif;
  --mono:"IBM Plex Mono",ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;
  color-scheme:light;
}
/* Dark is a soft slate, not black; the page opens in light unless dark is picked */
@media (prefers-color-scheme:dark){:root[data-theme=auto]{
  --bg:#1D2127; --surface:#252A31; --ink:#E9ECEF; --ink2:#C5CBD2; --muted:#9BA3AC; --faint:#717A84;
  --line:#343A42; --line2:#424951; --accent:#FF8A4C; --accent-bg:rgba(255,138,76,.13);
  --pos:#5CCB95; --mid:#8DB4F2; --low:#DDB95A; --neg:#F28A76; color-scheme:dark;
}}
:root[data-theme=dark]{
  --bg:#1D2127; --surface:#252A31; --ink:#E9ECEF; --ink2:#C5CBD2; --muted:#9BA3AC; --faint:#717A84;
  --line:#343A42; --line2:#424951; --accent:#FF8A4C; --accent-bg:rgba(255,138,76,.13);
  --pos:#5CCB95; --mid:#8DB4F2; --low:#DDB95A; --neg:#F28A76; color-scheme:dark;
}
*{box-sizing:border-box}
[hidden]{display:none!important}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 var(--sans);-webkit-font-smoothing:antialiased}
a{color:inherit}
button{font:inherit;color:inherit}
:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.num,.mono{font-family:var(--mono);font-variant-numeric:tabular-nums}
.wrap{max-width:1120px;margin:0 auto;padding:0 20px 72px}

/* top bar */
.top{display:flex;align-items:center;justify-content:space-between;gap:16px;height:52px;border-bottom:1px solid var(--line);font:500 11.5px/1 var(--mono);letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}
.brand{display:flex;align-items:center;gap:10px;color:var(--ink)}
.brand svg{display:block}
.top .right{display:flex;align-items:center;gap:16px}
.theme{background:none;border:1px solid var(--line2);border-radius:3px;height:26px;padding:0 9px;font:inherit;letter-spacing:inherit;color:var(--ink2);cursor:pointer}
.theme:hover{color:var(--ink);border-color:var(--ink2)}

/* heading + readout */
.hero{padding:40px 0 0}
.hero h1{font:600 clamp(30px,4.4vw,46px)/1.04 var(--sans);letter-spacing:-.025em;margin:0 0 12px}
.hero p{margin:0;color:var(--muted);max-width:64ch}
.stats{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));margin:28px 0 0;border-top:1px solid var(--line);border-bottom:1px solid var(--line)}
.stats div{padding:14px 16px 16px 0}
.stats div+div{border-left:1px solid var(--line);padding-left:16px}
.stats dt{font:500 11px/1.3 var(--mono);letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}
.stats dd{margin:8px 0 0;font:500 30px/1 var(--mono);font-variant-numeric:tabular-nums;letter-spacing:-.02em}
.stats dd.acc{color:var(--accent)}

/* sections */
.tabs{display:flex;gap:26px;margin-top:30px;border-bottom:1px solid var(--line);overflow-x:auto;scrollbar-width:none}
.tabs::-webkit-scrollbar{display:none}
.tab{flex:none;padding:12px 0 11px;margin-bottom:-1px;border:0;border-bottom:2px solid transparent;background:none;font:500 14.5px/1.2 var(--sans);color:var(--muted);cursor:pointer;white-space:nowrap}
.tab:hover{color:var(--ink)}
.tab[aria-selected=true]{color:var(--ink);border-bottom-color:var(--accent)}
.tab .n{margin-left:7px;font:400 12px/1 var(--mono);color:var(--faint)}
.tab[aria-selected=true] .n{color:var(--ink2)}
.tabnote{margin:14px 0 0;color:var(--muted);font-size:14px;max-width:80ch}

/* skills panel */
details.panel{margin-top:18px;border:1px solid var(--line);border-radius:3px;background:var(--surface)}
details.panel>summary{list-style:none;display:flex;justify-content:space-between;align-items:center;padding:11px 14px;font:500 11.5px/1.2 var(--mono);letter-spacing:.07em;text-transform:uppercase;color:var(--ink2);cursor:pointer}
details.panel>summary::-webkit-details-marker{display:none}
details.panel>summary::after{content:"+";font-size:15px;color:var(--muted)}
details.panel[open]>summary::after{content:"\2212"}
.panel .inner{display:grid;gap:22px;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));padding:4px 14px 16px}
.panel h3{margin:0 0 10px;font:500 11px/1.3 var(--mono);letter-spacing:.07em;text-transform:uppercase;color:var(--muted)}
.bar{display:grid;grid-template-columns:160px 1fr 40px;gap:10px;align-items:center;font-size:13.5px;margin:5px 0}
.bar i{display:block;height:4px;background:var(--line)}
.bar i span{display:block;height:100%}
.bar em{font:400 12px var(--mono);font-style:normal;color:var(--muted);text-align:right}

/* controls */
.controls{position:sticky;top:0;z-index:5;background:var(--bg);margin-top:18px;padding:12px 0;border-bottom:1px solid var(--line);display:grid;gap:10px}
.ctl{display:flex;flex-wrap:wrap;gap:8px 14px;align-items:center}
input[type=search],select{height:36px;font:14px var(--sans);border:1px solid var(--line2);border-radius:3px;background:var(--surface);color:var(--ink)}
input[type=search]{flex:1 1 260px;min-width:0;padding:0 12px}
select{padding:0 30px 0 10px;appearance:none;-webkit-appearance:none;background-image:linear-gradient(45deg,transparent 50%,var(--muted) 50%),linear-gradient(135deg,var(--muted) 50%,transparent 50%);background-position:calc(100% - 15px) 16px,calc(100% - 10px) 16px;background-size:5px 5px;background-repeat:no-repeat}
input[type=search]:focus,select:focus{outline:none;border-color:var(--ink2);box-shadow:0 0 0 3px var(--accent-bg)}
.seg{display:inline-flex;border:1px solid var(--line2);border-radius:3px;overflow:hidden}
.seg button{height:30px;padding:0 12px;border:0;background:transparent;font:500 11.5px/1 var(--mono);letter-spacing:.05em;text-transform:uppercase;color:var(--muted);cursor:pointer}
.seg button+button{border-left:1px solid var(--line2)}
.seg button[aria-pressed=true]{background:var(--ink);color:var(--bg)}
label.tog{display:inline-flex;gap:7px;align-items:center;font-size:13.5px;color:var(--ink2);cursor:pointer}
label.tog input{accent-color:var(--accent);margin:0}

.shown{display:flex;flex-wrap:wrap;gap:6px 14px;align-items:center;margin:16px 0 0;padding-bottom:10px;font:400 12px/1.4 var(--mono);color:var(--muted);border-bottom:1px solid var(--line)}
.pick{display:inline-flex;align-items:center;gap:8px;padding:3px 4px 3px 9px;border:1px solid var(--accent);border-radius:2px;color:var(--accent)}
.pick button{border:0;background:none;color:inherit;cursor:pointer;font:500 13px/1 var(--mono);padding:0 4px}

/* postings */
.row{display:grid;grid-template-columns:72px minmax(0,1fr) 150px;gap:0 22px;padding:18px 0 18px;border-bottom:1px solid var(--line)}
.row.done{opacity:.45}
.fit b{display:block;font:500 27px/1 var(--mono);font-variant-numeric:tabular-nums;letter-spacing:-.02em}
.fit small{display:block;margin-top:7px;font:500 10px/1.25 var(--mono);letter-spacing:.07em;text-transform:uppercase;color:var(--muted)}
.meter{width:52px;height:2px;margin-top:9px;background:var(--line)}
.meter i{display:block;height:100%}
.t-strong .fit b{color:var(--pos)} .t-good .fit b{color:var(--mid)} .t-look .fit b{color:var(--low)}
.t-strong .meter i{background:var(--pos)} .t-good .meter i{background:var(--mid)} .t-look .meter i{background:var(--low)}
.co{font:500 11.5px/1.3 var(--mono);letter-spacing:.06em;text-transform:uppercase;color:var(--muted)}
.title{font:600 17px/1.3 var(--sans);letter-spacing:-.005em;margin:5px 0 6px}
.meta{display:flex;flex-wrap:wrap;gap:2px 0;font-size:13.5px;color:var(--muted)}
.meta span+span::before{content:"/";margin:0 8px;color:var(--line2)}
.tags{display:flex;flex-wrap:wrap;gap:6px;margin-top:11px}
.tag{font:400 12px/1 var(--sans);padding:4px 7px 5px;border:1px solid var(--line2);border-radius:2px;color:var(--ink2);white-space:nowrap}
.tag.ok{color:var(--pos);border-color:var(--pos);border-color:color-mix(in srgb,var(--pos) 45%,transparent)}
.tag.warn{color:var(--neg);border-color:var(--neg);border-color:color-mix(in srgb,var(--neg) 45%,transparent)}
.tag.old{color:var(--low);border-color:var(--low);border-color:color-mix(in srgb,var(--low) 45%,transparent)}
.tag.new{background:var(--accent);border-color:var(--accent);color:#fff;font-weight:600}
.tag.sec{color:var(--muted)}
.ai{margin-top:12px;padding:9px 12px;border-left:2px solid var(--mid);background:var(--surface);font-size:13.5px}
details.x{margin-top:10px}
details.x>summary{list-style:none;display:inline-flex;gap:7px;font:500 11px/1.3 var(--mono);letter-spacing:.07em;text-transform:uppercase;color:var(--ink2);cursor:pointer}
details.x>summary::-webkit-details-marker{display:none}
details.x>summary::before{content:"+";width:9px;color:var(--muted)}
details.x[open]>summary::before{content:"\2212"}
details.x>summary:hover{color:var(--ink)}
.x .body{margin-top:8px;padding-left:16px;border-left:1px solid var(--line)}
.why{display:grid;grid-template-columns:150px 1fr;gap:5px 14px;margin:0;font-size:13.5px}
.why dt{color:var(--muted)} .why dd{margin:0}
.qhead{margin:0;font-size:13.5px}
.qh{margin:12px 0 4px;font:500 10.5px/1.3 var(--mono);letter-spacing:.07em;text-transform:uppercase;color:var(--muted)}
.ql{list-style:none;margin:0;padding:0;display:grid;gap:5px;font-size:13.5px}
.ql li{display:grid;grid-template-columns:16px 1fr;gap:8px}
.ql b{font-family:var(--mono);text-align:center} .ql small{display:block;color:var(--muted)}
.q-met b{color:var(--pos)} .q-partial b{color:var(--low)} .q-missing b{color:var(--neg)} .q-check b,.q-soft b{color:var(--faint)}
.acts{display:flex;flex-direction:column;gap:4px}
.btn{display:inline-flex;align-items:center;justify-content:center;gap:6px;height:34px;padding:0 14px;border:1px solid var(--ink);border-radius:3px;background:var(--ink);color:var(--bg);font:500 13.5px/1 var(--sans);text-decoration:none;white-space:nowrap;cursor:pointer}
.btn:hover{opacity:.86}
.btn.find{background:transparent;color:var(--ink);border-color:var(--line2)}
.btn.find:hover{border-color:var(--ink2);opacity:1}
.lnk{height:28px;border:0;background:none;font:400 12.5px/1 var(--sans);color:var(--muted);cursor:pointer}
.lnk:hover{color:var(--ink)}
.lnk.on{color:var(--pos)}
a.lnk{display:inline-flex;align-items:center;text-decoration:none}
.more{display:block;margin:22px auto 0;height:38px;padding:0 18px;border:1px solid var(--line2);border-radius:3px;background:var(--surface);font:500 11.5px/1 var(--mono);letter-spacing:.07em;text-transform:uppercase;color:var(--ink);cursor:pointer}
.more:hover{border-color:var(--ink2)}
.empty{padding:48px 20px;text-align:center;color:var(--muted);border-bottom:1px solid var(--line)}

/* big names */
.bnote{margin:14px 0 0;color:var(--muted);font-size:14px;max-width:80ch}
.bn-head,.bn{display:grid;grid-template-columns:minmax(170px,1.25fr) minmax(150px,.9fr) minmax(250px,1.6fr) 112px;gap:6px 22px}
.bn-head{margin-top:18px;padding-bottom:9px;border-bottom:1px solid var(--line);font:500 10.5px/1.3 var(--mono);letter-spacing:.07em;text-transform:uppercase;color:var(--muted)}
.bn{padding:16px 0;border-bottom:1px solid var(--line);align-items:start}
.bn-group{margin:30px 0 0;padding-bottom:8px;border-bottom:1px solid var(--line2);font:500 11.5px/1.3 var(--mono);letter-spacing:.07em;text-transform:uppercase;color:var(--ink2)}
.bn-group span{margin-left:8px;color:var(--muted)}
.bn .nm{font:600 15.5px/1.3 var(--sans)}
.bn .nm a{display:inline-block;margin-top:4px;font:400 11.5px/1 var(--mono);letter-spacing:.04em;color:var(--muted);text-decoration:none}
.bn .nm a:hover{color:var(--ink)}
.bn .st{font-size:14px}
.bn .st small{display:block;margin-top:3px;font-size:12.5px;color:var(--muted)}
.bn .hot{color:var(--accent);font-weight:500}
.go{padding:0;border:0;background:none;font:600 14px/1.3 var(--sans);color:var(--accent);cursor:pointer;text-align:left}
.go:hover{text-decoration:underline}
.tl{display:grid;grid-template-columns:repeat(12,1fr);gap:2px}
.tl i{position:relative;height:12px;background:var(--line)}
.tl i.on{background:var(--accent);opacity:.8}
.tl i.now::after{content:"";position:absolute;left:50%;top:-4px;bottom:-4px;width:2px;margin-left:-1px;background:var(--ink)}
.tlm{display:grid;grid-template-columns:repeat(12,1fr);gap:2px;margin-top:5px;font:400 9.5px/1 var(--mono);color:var(--faint);text-align:center}
.tlm b{color:var(--ink);font-weight:500}
.win{margin-top:7px;font:400 12px/1.4 var(--mono);color:var(--muted)}
.pub{margin-top:6px;font-size:12.5px;color:var(--ink2)}
.pub b{font:500 10px/1 var(--mono);letter-spacing:.07em;text-transform:uppercase;color:var(--pos);margin-right:6px}
.bn .fs{font:400 13px/1.3 var(--mono);color:var(--ink2)}
.bn .fs small{display:block;margin-top:3px;font-family:var(--sans);font-size:12px;color:var(--muted)}
.bn .sub{grid-column:1/-1;margin-top:-2px;font-size:13px;color:var(--muted);max-width:90ch}
.bn .lbl{display:none}

/* predicted */
.months{display:grid;grid-template-columns:repeat(9,minmax(0,1fr));gap:6px;margin-top:16px}
.mo{display:flex;flex-direction:column;justify-content:flex-end;gap:5px;min-height:74px;padding:6px 4px;border:1px solid var(--line);border-radius:3px;background:var(--surface);cursor:pointer;font:400 11px/1 var(--mono);color:var(--muted);text-align:center}
.mo:hover{border-color:var(--ink2)}
.mo[aria-pressed=true]{border-color:var(--accent);color:var(--accent)}
.mo i{display:block;margin:0 auto;width:60%;min-height:2px;background:var(--mid);opacity:.75}
.mo[aria-pressed=true] i{background:var(--accent)}
.mo b{font-weight:500;color:var(--ink)}
.pr{display:grid;grid-template-columns:96px minmax(0,1fr) 150px;gap:0 22px;padding:16px 0;border-bottom:1px solid var(--line)}
.pr .when b{display:block;font:500 19px/1.1 var(--mono);letter-spacing:-.01em}
.pr .when small{display:block;margin-top:6px;font:500 10px/1.25 var(--mono);letter-spacing:.07em;text-transform:uppercase;color:var(--muted)}
.st-upcoming .when b{color:var(--mid)} .st-due .when b,.st-due .when small{color:var(--accent)}
.st-late .when b{color:var(--low)} .st-posted .when b{color:var(--pos)}
.pr .title{font-size:16px;margin:4px 0 5px}
.pr .past{margin-top:6px;font-size:13px;color:var(--ink2)}
.pr .past span{color:var(--muted)}

@media (max-width:760px){
  .months{grid-template-columns:repeat(5,minmax(0,1fr))}
  .months .mo:nth-child(n+6){display:none}
  .pr{grid-template-columns:72px minmax(0,1fr);gap:0 14px}
  .pr .when b{font-size:16px}
}

footer{margin-top:52px;padding-top:16px;border-top:1px solid var(--line);font-size:13px;color:var(--muted)}
footer details>summary{cursor:pointer;font:500 11px/1.3 var(--mono);letter-spacing:.07em;text-transform:uppercase;color:var(--ink2)}
.tbl{overflow-x:auto}
footer table{border-collapse:collapse;margin-top:10px;width:100%;font-size:12.5px}
footer td,footer th{text-align:left;padding:5px 10px 5px 0;border-bottom:1px solid var(--line);vertical-align:top}
footer th{font:500 10.5px/1.3 var(--mono);letter-spacing:.07em;text-transform:uppercase;color:var(--muted)}
footer td.bad{color:var(--neg)}

@media (max-width:760px){
  .wrap{padding:0 16px 56px}
  .top .stamp{display:none}
  .hero{padding-top:28px}
  .stats{grid-template-columns:repeat(2,minmax(0,1fr))}
  .stats div:nth-child(3){border-left:0;padding-left:0}
  .stats div:nth-child(n+3){border-top:1px solid var(--line)}
  .controls{position:static}
  .row{grid-template-columns:52px minmax(0,1fr);gap:0 14px}
  .fit b{font-size:22px}
  .meter{width:40px}
  .meta{flex-direction:column}
  .meta span+span::before{display:none}
  .acts{grid-column:1/-1;flex-direction:row;align-items:center;gap:6px;margin-top:14px}
  .acts .btn{flex:1}
  .why{grid-template-columns:1fr}
  .why dt{margin-top:6px}
  .bar{grid-template-columns:120px 1fr 36px}
  .bn-head{display:none}
  .bn{grid-template-columns:1fr 1fr;gap:12px 16px}
  .bn .tlw{grid-column:1/-1}
  .bn .lbl{display:inline;font-family:var(--sans);color:var(--muted)}
}
</style>
</head>
<body>
<div class="wrap">
<div class="top">
  <div class="brand"><svg width="16" height="16" viewBox="0 0 32 32" aria-hidden="true"><path d="M5 27 16 4l11 23-11-5.5z" fill="var(--accent)"/></svg>Aero job finder</div>
  <div class="right"><span class="stamp" id="stamp"></span><button class="theme" id="theme" type="button"></button></div>
</div>

<header class="hero">
  <h1>Engineering internships</h1>
  <p id="sub"></p>
  <dl class="stats" id="stats"></dl>
</header>

<nav class="tabs" role="tablist" id="tabs" aria-label="Sections"></nav>
<p class="tabnote" id="tabnote"></p>

<div id="jobsView">
<details class="panel" id="gapbox">
  <summary>What these postings ask for</summary>
  <div class="inner">
    <div><h3>Your skills that come up most</h3><div id="have"></div></div>
    <div><h3>Skills not on your resume yet</h3><div id="need"></div></div>
  </div>
</details>

<div class="controls">
  <div class="ctl">
    <input type="search" id="q" placeholder="Search company, title, location, skill" aria-label="Search">
    <select id="disc" aria-label="Discipline"></select>
    <select id="sort" aria-label="Sort">
      <option value="score">Best fit first</option>
      <option value="reqs">Most qualifications met</option>
      <option value="new">Newest first</option>
      <option value="near">Closest first</option>
      <option value="company">Company A to Z</option>
    </select>
  </div>
  <div class="ctl">
    <div class="seg" role="group" aria-label="Fit">
      <button data-tier="all" aria-pressed="true">All</button>
      <button data-tier="strong" aria-pressed="false">Strong</button>
      <button data-tier="good" aria-pressed="false">Good</button>
      <button data-tier="look" aria-pressed="false">Worth a look</button>
    </div>
    <label class="tog" id="seasonTog"><input type="checkbox" id="season"> <span id="seasonLabel"></span></label>
    <label class="tog"><input type="checkbox" id="hideOld"> <span id="oldLabel"></span></label>
    <label class="tog"><input type="checkbox" id="hideDone" checked> Hide applied and dismissed</label>
  </div>
</div>

<div class="shown" id="shown" aria-live="polite"></div>
<div id="list"></div>
<button class="more" id="more" hidden>Show more</button>
</div>

<section id="predView" hidden>
  <p class="bnote" id="predNote"></p>
  <div class="controls">
    <div class="ctl">
      <input type="search" id="pq" placeholder="Search company, role, location" aria-label="Search predicted internships">
      <select id="pdisc" aria-label="Discipline"></select>
    </div>
    <div class="ctl">
      <div class="seg" role="group" aria-label="Term" id="pseason"></div>
      <div class="seg" role="group" aria-label="Status" id="pstat">
        <button data-st="soon" aria-pressed="true">Coming up</button>
        <button data-st="late" aria-pressed="false">Not seen yet</button>
        <button data-st="posted" aria-pressed="false">Already posted</button>
        <button data-st="all" aria-pressed="false">All</button>
      </div>
      <label class="tog"><input type="checkbox" id="paero"> Aerospace and motorsport only</label>
      <label class="tog" id="pnearTog"><input type="checkbox" id="pnear"> <span id="pnearLabel"></span></label>
    </div>
  </div>
  <div class="months" id="pmonths" aria-label="Expected postings by month"></div>
  <div class="shown" id="pshown" aria-live="polite"></div>
  <div id="plist"></div>
  <button class="more" id="pmore" hidden>Show more</button>
</section>

<section id="bigView" hidden>
  <p class="bnote">When well-known aerospace and defense employers usually recruit summer interns, and what this cycle's scans have found from each. Shaded months are the typical window from past cycles (an estimate, not an announced date); the line marks this month. Dates marked <b class="mono" style="font-size:11px;color:var(--pos)">PUBLISHED</b> come from the program itself. "Last cycle" is the company's first engineering internship on the Simplify list in the previous cycle, which doesn't catch every company's first postings.</p>
  <div class="bn-head"><span>Company</span><span>This cycle</span><span>Typical window, Jul to Jun</span><span>Earliest posting</span></div>
  <div id="bigList"></div>
</section>

<footer>
  <p id="foot"></p>
  <details>
    <summary>Sources checked on this run</summary>
    <div class="tbl"><table id="src"></table></div>
  </details>
</footer>
</div>

<script id="data" type="application/json">__DATA__</script>
<script>
(function(){
const D = JSON.parse(document.getElementById('data').textContent);
// A posted date the page can't read counts as unknown instead of showing "Invalid Date"
for(const j of D.jobs) if(j.posted && !/^\d{4}-\d{2}-\d{2}$/.test(j.posted)) j.posted = '';
const store = {
  get(){ try { return JSON.parse(localStorage.getItem('ajf-status') || '{}'); } catch(e){ return {}; } },
  set(v){ try { localStorage.setItem('ajf-status', JSON.stringify(v)); } catch(e){} }
};
const pref = {
  get(k, d){ try { const v = localStorage.getItem('ajf-' + k); return v === null ? d : v; } catch(e){ return d; } },
  set(k, v){ try { localStorage.setItem('ajf-' + k, v); } catch(e){} }
};
let status = store.get();
const PAGE = 60;
let tier = 'all', limit = PAGE, pick = null;
const $ = id => document.getElementById(id);
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const fmt = iso => { if(!iso) return ''; const d = new Date(iso + 'T12:00:00'); return d.toLocaleDateString(undefined,{month:'short',day:'numeric'}); };
const MON = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
const TIER = {strong:'Strong fit', good:'Good fit', look:'Worth a look'};
const T = D.tracks;
const todayMs = Date.parse(D.today + 'T12:00:00');
const daysBack = n => new Date(todayMs - n*864e5).toISOString().slice(0,10);
const weekAgo = daysBack(7), oldCut = daysBack(D.old_after);
const ageDays = iso => iso ? Math.round((todayMs - Date.parse(iso + 'T12:00:00')) / 864e5) : null;
// "This week" and "old" go by the posting date; undated postings have their own section
const postedThisWeek = j => !!j.posted && j.posted >= weekAgo;
const isOld = j => !!j.posted && j.posted < oldCut;
const coMatch = (company, terms) => { const c = (company || '').toLowerCase(); return terms.some(t => t[0] === '=' ? c === t.slice(1) : c.includes(t)); };

// ---- theme: light unless dark (or the system's setting) is picked here
const THEMES = ['light', 'dark', 'auto'];
let theme = THEMES.includes(pref.get('theme', 'light')) ? pref.get('theme', 'light') : 'light';
function applyTheme(){
  document.documentElement.setAttribute('data-theme', theme);
  $('theme').textContent = 'Theme: ' + (theme === 'auto' ? 'system' : theme);
}
$('theme').addEventListener('click', () => { theme = THEMES[(THEMES.indexOf(theme) + 1) % 3]; pref.set('theme', theme); applyTheme(); });
applyTheme();

// ---- sections
const hasLeads = D.jobs.some(j => j.lead);
const P = D.predicted;
const ORDER = ['new', 'summer', 'motor', 'fall', 'broad', 'pred', 'undated', 'leads', 'big'].filter(k => k === 'new' || k === 'undated' ||
  (k === 'leads' ? hasLeads : k === 'big' ? D.popular.length : k === 'pred' ? P.length : T[k]));
const HASH = {new:'new', summer:'summer', motor:'motorsports', fall:'fall', broad:'all', pred:'predicted', undated:'date-unknown', leads:'leads', big:'big-names'};
const NAME = {new:'New this week', pred:'Predicted', undated:'Posted date unknown', leads:'Leads without a link', big:'Big names'};
const VIEWS = ['big', 'pred'];  // sections that aren't a list of postings
for(const k in T) NAME[k] = T[k].tab;
const best = j => Object.entries(j.tracks).reduce((a, b) => !a || b[1].score > a[1].score ? b : a, null);
// "New this week", "Posted date unknown" and "Leads" gather postings from every other section
const mixed = t => t === 'new' || t === 'undated' || t === 'leads';
// Leads (no direct company link) only show in their own section
const inTab = (j, t) => t === 'leads' ? !!j.lead : !j.lead &&
  (t === 'undated' ? !j.posted : t === 'new' ? postedThisWeek(j) : t !== 'big' && !!j.posted && !!j.tracks[t]);
let tab = (() => {
  const h = location.hash.slice(1);
  const fromHash = Object.keys(HASH).find(k => HASH[k] === h);
  const saved = pref.get('tab', 'summer');
  return fromHash && ORDER.includes(fromHash) ? fromHash : (ORDER.includes(saved) ? saved : 'summer');
})();
const trackKey = j => mixed(tab) ? best(j)[0] : tab;
const seasonChk = {};

$('stamp').textContent = D.sources.length ? `Updated ${D.updated_label}` : '';
$('sub').textContent = D.sources.length
  ? `Scored against ${D.name}'s resume. ${D.sources.filter(s => s.ok).length} company career sites and internship lists checked every 5 hours.` +
    (D.max_age ? ` Only postings from the last ${D.max_age} days are shown.` : '')
  : 'Waiting for the first scan.';
const c = D.counts;
const nSummer = D.jobs.filter(j => inTab(j, 'summer')).length;
$('stats').innerHTML = [
  [T.summer ? T.summer.tab + ' aerospace' : 'Postings', T.summer ? nSummer : D.jobs.length, ''],
  ['Strong summer fits', c.strong, ''],
  ['New today', c.new_today, c.new_today ? 'acc' : ''],
  ['Posted this week', D.jobs.filter(j => inTab(j, 'new')).length, ''],
].map(([k, v, cls]) => `<div><dt>${esc(k)}</dt><dd class="${cls}">${v}</dd></div>`).join('');
$('oldLabel').textContent = `Hide postings older than ${D.old_after} days`;

function tabs(){
  const n = k => k === 'big' ? D.popular.length : k === 'pred' ? P.filter(p => isSoon(p) && pTerm(p) === pTerms[0] && (p.aero || p.mo || !pAeroDefault(pTerms[0]))).length
    : D.jobs.filter(j => inTab(j, k)).length;
  $('tabs').innerHTML = ORDER.map(k => `<button class="tab" role="tab" data-tab="${k}" aria-selected="${k === tab}">${esc(NAME[k])}<span class="n">${n(k)}</span></button>`).join('');
}

function bars(list, color){
  if(!list.length) return '<p style="color:var(--muted);font-size:13.5px;margin:0">Not enough descriptions yet.</p>';
  return list.map(g => `<div class="bar"><span>${esc(g.name)}</span><i><span style="width:${g.pct}%;background:${color}"></span></i><em>${g.pct}%</em></div>`).join('');
}
function topSkills(jobs, field){
  const withDesc = jobs.filter(j => j.has_description), n = {};
  for(const j of withDesc) for(const s of j[field]) n[s] = (n[s] || 0) + 1;
  return Object.entries(n).sort((a, b) => b[1] - a[1]).slice(0, 8).map(([name, v]) => ({name, pct: Math.round(100 * v / withDesc.length)}));
}

$('src').innerHTML = '<tr><th>Source</th><th>Type</th><th>Result</th></tr>' + D.sources.map(s =>
  `<tr><td>${esc(s.name)}</td><td>${esc(s.kind)}</td><td class="${s.ok ? '' : 'bad'}">${s.ok ? s.count + ' postings read' : 'Failed: ' + esc(s.error)}</td></tr>`).join('');
// Sites found automatically drop out on their own after repeated failures
const isFound = s => String(s.kind).includes('found automatically');
const bad = D.sources.filter(s => !s.ok && !String(s.error).startsWith('skipped') && !isFound(s)).length;
const nFound = D.sources.filter(isFound).length;
$('foot').textContent = `${D.sources.length} sources checked` + (nFound ? ` (${nFound} career sites found automatically)` : '') +
  (bad ? `, ${bad} failed (listed below; fix or remove them in sources.toml).` : '.') + ' Scores are keyword-based estimates. Always read the posting before applying.';

const QI = {met:'✓', partial:'~', missing:'✗', check:'?', soft:'·'};
const num = x => Number.isInteger(x) ? x : x.toFixed(1);
const reqPct = j => { const s = j.quals && j.quals.summary; return s && s.required_checked ? s.required_met / s.required_checked : -1; };
function qualTag(q){
  const s = q && q.summary;
  if(!s || !s.required_checked) return '';
  const cls = s.required_missing ? 'warn' : s.required_met === s.required_checked ? 'ok' : '';
  return `<span class="tag ${cls}">Meets ${num(s.required_met)} of ${s.required_checked} required</span>`;
}
function qualList(q){
  if(!q) return '';
  const sec = (name, rows) => rows && rows.length ? `<div class="qh">${name}</div><ul class="ql">` + rows.map(r =>
    `<li class="q-${r.status}"><b>${QI[r.status]}</b><span>${esc(r.text)}${r.why ? `<small>${esc(r.why)}</small>` : (r.status === 'check' ? '<small>Couldn\'t check this one automatically</small>' : '')}</span></li>`).join('') + '</ul>' : '';
  const s = q.summary;
  const head = s.required_checked ? `You meet ${num(s.required_met)} of ${s.required_checked} required qualifications I could check` +
    (s.preferred_total ? `, and ${s.preferred_met} of ${s.preferred_total} preferred` : '') + (s.to_check ? `. ${s.to_check} to confirm yourself.` : '.') : 'Qualifications found, but none I could check automatically.';
  return `<details class="x"><summary>Qualifications</summary><div class="body"><p class="qhead">${head}</p>${sec('Required', q.required)}${sec('Preferred', q.preferred)}</div></details>`;
}
const where = tr => tr.miles === 'remote' ? 'Remote' : `${tr.miles} mi from ${T.fall.home}`;

function card(j){
  const st = status[j.key];
  const k = trackKey(j), tr = j.tracks[k];
  const tags = [];
  if(j.first_seen >= D.today) tags.push('<span class="tag new">New</span>');
  if(isOld(j)) tags.push(`<span class="tag old">Older than ${D.old_after} days</span>`);
  if(mixed(tab)){
    for(const t of ORDER) if(j.tracks[t]) tags.push(`<span class="tag sec">${esc(t === 'fall' ? NAME[t] + ' · ' + where(j.tracks[t]) : NAME[t])}</span>`);
  } else if(k === 'fall'){
    tags.push(`<span class="tag sec">${esc(where(tr))}</span>`);
  }
  tags.push(`<span class="tag ${tr.season === 'match' ? 'ok' : ''}">${esc(tr.season_label)}</span>`);
  if(k !== 'summer' && j.discipline) tags.push(`<span class="tag">${esc(j.discipline)}</span>`);
  const qt = qualTag(j.quals); if(qt) tags.push(qt);
  for(const f of j.flags) tags.push(`<span class="tag ${f.kind === 'info' ? '' : f.kind === 'good' ? 'ok' : f.kind}">${esc(f.label)}</span>`);
  const p = tr.parts, rows = [];
  if(j.matched.length) rows.push(`<dt>Your skills it asks for</dt><dd>${esc(j.matched.join(', '))}</dd>`);
  if(j.related.length) rows.push(`<dt>Transferable</dt><dd>${esc(j.related.join(', '))}</dd>`);
  if(j.gaps.length) rows.push(`<dt>Not on your resume</dt><dd>${esc(j.gaps.join(', '))}</dd>`);
  rows.push(`<dt>Score</dt><dd>${k === 'summer' ? 'Aerospace' : 'Engineering fit'} ${p.fit}/40, skills ${p.skills}/35, eligibility ${p.eligibility}/25` +
    (p.requirements ? `, ${p.requirements} for missing required qualifications` : '') + `</dd>`);
  rows.push(`<dt>Found via</dt><dd>${esc(j.source)}${j.lead ? ' (no direct link: the button searches for the company\'s own posting)' : ''}</dd>`);
  const ai = j.ai ? `<div class="ai"><b>Claude's take (${esc(j.ai.fit)}):</b> ${esc(j.ai.summary)}${j.ai.talking_point ? '<br><b>Lead with:</b> ' + esc(j.ai.talking_point) : ''}</div>` : '';
  const age = ageDays(j.posted);
  // posted_from names the list the date came from when the company's own site gave none
  const when = j.posted
    ? `<span>Posted ${fmt(j.posted)} (${age <= 0 ? 'today' : age + 'd ago'}${j.posted_from ? ', per ' + esc(j.posted_from) : ''})</span>`
    : `<span title="Not on its source, its own listing page, or any internship list the scan reads">Posted date unknown</span>`;
  const meta = [j.location && `<span>${esc(j.location)}</span>`, when, `<span>Found ${fmt(j.first_seen)}</span>`].filter(Boolean).join('');
  const apply = j.lead
    ? `<a class="btn find" href="${esc(j.url)}" target="_blank" rel="noopener">Find posting ↗</a>`
    : `<a class="btn" href="${esc(j.url)}" target="_blank" rel="noopener">Apply ↗</a>`;
  return `<article class="row t-${tr.tier} ${st ? 'done' : ''}" data-key="${esc(j.key)}">
    <div class="fit" title="Fit score out of 100"><b>${tr.score}</b><small>${TIER[tr.tier]}</small><div class="meter"><i style="width:${tr.score}%"></i></div></div>
    <div class="main">
      <div class="co">${esc(j.company)}</div>
      <h2 class="title">${esc(j.title)}</h2>
      <div class="meta">${meta}</div>
      <div class="tags">${tags.join('')}</div>
      ${ai}
      ${qualList(j.quals)}
      <details class="x"><summary>Why this score</summary><div class="body"><dl class="why">${rows.join('')}</dl></div></details>
    </div>
    <div class="acts">
      ${apply}
      <button class="lnk ${st === 'applied' ? 'on' : ''}" data-act="applied">${st === 'applied' ? 'Applied ✓' : 'Mark applied'}</button>
      <button class="lnk" data-act="dismissed">${st === 'dismissed' ? 'Dismissed' : 'Dismiss'}</button>
    </div>
  </article>`;
}

// ---- big names
const inWin = (w, m) => w.length === 2 && (w[0] <= w[1] ? m >= w[0] && m <= w[1] : m >= w[0] || m <= w[1]);
const RECRUIT_YEAR = [7,8,9,10,11,12,1,2,3,4,5,6];
function renderBig(){
  const m = +D.today.slice(5, 7);
  // Companies come grouped (space, defense...) in sources.toml order; each group gets a heading
  const inGroup = {};
  for(const p of D.popular) inGroup[p.group] = (inGroup[p.group] || 0) + 1;
  let last = null;
  $('bigList').innerHTML = D.popular.map((p, i) => {
    const head = p.group && p.group !== last ? `<h3 class="bn-group">${esc(p.group)}<span>${inGroup[p.group]}</span></h3>` : '';
    last = p.group;
    const mine = D.jobs.filter(j => inTab(j, 'broad') && coMatch(j.company, p.match));
    const strong = mine.filter(j => Object.values(j.tracks).some(t => t.tier === 'strong')).length;
    const live = inWin(p.window, m);
    const opens = p.window.length ? MON[p.window[0] - 1] : '';
    let st;
    if(mine.length) st = `<button class="go" data-pick="${i}" title="Open postings from the last ${D.max_age} days">${mine.length} posted recently →</button><small>${strong ? `${strong} strong fit${strong > 1 ? 's' : ''}` : 'None rated strong yet'}</small>`;
    else if(!p.scanned) st = live ? `<span class="hot">In season</span><small>Not scanned here; apply on their site</small>` : `<span>Usually opens ${opens}</span><small>Not scanned here; apply on their site</small>`;
    else st = live ? `<span class="hot">In season</span><small>Nothing posted in the last ${D.max_age} days</small>` : `<span>${opens ? 'Usually opens ' + opens : 'No usual window set'}</span><small>Nothing posted in the last ${D.max_age} days</small>`;
    const tl = `<div class="tl">${RECRUIT_YEAR.map(mo => `<i class="${inWin(p.window, mo) ? 'on' : ''} ${mo === m ? 'now' : ''}" title="${MON[mo - 1]}"></i>`).join('')}</div>` +
      `<div class="tlm">${RECRUIT_YEAR.map(mo => mo === m ? `<b>${MON[mo - 1][0]}</b>` : `<span>${MON[mo - 1][0]}</span>`).join('')}</div>` +
      (p.window.length ? `<div class="win">Typically ${MON[p.window[0] - 1]} to ${MON[p.window[1] - 1]}</div>` : '') +
      (p.dates ? `<div class="pub"><b>Published</b>${esc(p.dates)}</div>` : '');
    const fs = '<span class="lbl">Earliest posting: </span>' + (p.first_seen ? `${fmt(p.first_seen)}<small>${p.most_open} open at most</small>` : '—') +
      (p.past && p.past.length ? `<small>Last cycle: from ${fmtY(p.past[0][1])} (${p.past[0][2]} on the list)</small>` : '');
    return head + `<div class="bn">
      <div class="nm">${esc(p.name)}${p.careers ? `<br><a href="${esc(p.careers)}" target="_blank" rel="noopener">Student careers ↗</a>` : ''}</div>
      <div class="st">${st}</div>
      <div class="tlw">${tl}</div>
      <div class="fs">${fs}</div>
      ${p.note ? `<div class="sub">${esc(p.note)}</div>` : ''}
    </div>`;
  }).join('');
}

// ---- predicted internships (one term at a time: Summer 2027, Fall 2027...)
const fmtY = iso => { if(!iso) return ''; const d = new Date(iso + 'T12:00:00'); return d.toLocaleDateString(undefined,{month:'short',day:'numeric',year:'numeric'}); };
const isSoon = p => p.st === 'upcoming' || p.st === 'due';
const pTerm = p => p.s + ' ' + p.y;
const pTerms = (D.pred_info.terms || []).filter(t => P.some(p => pTerm(p) === t));
const cap = s => s.charAt(0).toUpperCase() + s.slice(1);
// Summer is the aerospace section, so it starts on aerospace companies; other terms take any engineering
const pAeroDefault = term => term.startsWith('summer');
const pAero = {}, pNear = {};
let pT = pTerms[0] || '', pStat = 'soon', pMonth = '', pLimit = PAGE;
const thisMonth = D.today.slice(0, 7);
// Roles due now (expected up to three weeks ago) count toward this month
const pMonthOf = p => p.exp.slice(0, 7) < thisMonth ? thisMonth : p.exp.slice(0, 7);
const MONTHS = (() => { const out = []; let y = +D.today.slice(0, 4), m = +D.today.slice(5, 7);
  for(let i = 0; i < 9; i++){ out.push(`${y}-${String(m).padStart(2, '0')}`); if(++m > 12){ m = 1; y++; } } return out; })();

function setupPred(){
  $('pseason').innerHTML = pTerms.map(t => `<button data-term="${esc(t)}" aria-pressed="${t === pT}">${esc(cap(t))}</button>`).join('');
  $('pseason').hidden = pTerms.length < 2;
  $('paero').checked = pT in pAero ? pAero[pT] : pAeroDefault(pT);
  const fall = T.fall && pT.startsWith('fall');
  $('pnearTog').hidden = !fall;
  if(fall) $('pnearLabel').textContent = `Within ${T.fall.radius} mi of ${T.fall.home} only`;
  $('pnear').checked = !!pNear[pT];
  const counts = {};
  for(const p of P) if(pTerm(p) === pT) counts[p.d] = (counts[p.d] || 0) + 1;
  $('pdisc').innerHTML = '<option value="">All disciplines</option>' + Object.entries(counts).sort((a, b) => b[1] - a[1])
    .map(([d, n]) => `<option value="${esc(d)}">${esc(d)} (${n})</option>`).join('');
  $('predNote').textContent = `Internships posted in past cycles, and when each should come back for ${cap(pT)}: last cycle's posting date moved forward a year (the middle date when there are several cycles). ` +
    `Built from ${D.pred_info.postings.toLocaleString()} engineering internship postings since ${fmtY(D.pred_info.since)} (old copies of the Simplify list, plus everything this scan has read). ` +
    `A role counts as posted once the same company posts one with a similar title this cycle. Companies don't repeat every role, so treat the dates as estimates.`;
  pLimit = PAGE;
}

function pPool(){
  const q = $('pq').value.trim().toLowerCase(), disc = $('pdisc').value;
  const aero = $('paero').checked, near = !$('pnearTog').hidden && $('pnear').checked;
  return P.filter(p => pTerm(p) === pT && (!aero || p.aero || p.mo) && (!near || p.mi != null) && (!disc || p.d === disc) &&
    (!q || q.split(/\s+/).every(w => [p.co, p.t, p.lt, p.loc, p.d].join(' ').toLowerCase().includes(w))));
}

function pCard(p){
  const days = Math.round((Date.parse(p.exp + 'T12:00:00') - todayMs) / 864e5);
  const [when, label] = p.st === 'posted' ? [fmt(p.seen), 'Posted ✓']
    : ['~' + fmt(p.exp), p.st === 'due' ? 'Due now' : p.st === 'late' ? 'Not seen yet' : days > 60 ? `In ${Math.round(days / 7)} weeks` : `In ${days} days`];
  const tags = [`<span class="tag">${esc(p.d)}</span>`];
  if(p.aero) tags.push('<span class="tag ok">Aerospace company</span>');
  if(p.mo) tags.push('<span class="tag ok">Motorsport</span>');
  if(p.mi != null) tags.push(`<span class="tag sec">${p.mi} mi from ${esc(T.fall ? T.fall.home : 'home')}</span>`);
  if(p.st === 'late') tags.push(`<span class="tag old">${-days} days past last cycle's date</span>`);
  if(p.past.length > 1) tags.push(`<span class="tag">Posted ${p.past.length} cycles running</span>`);
  if(p.lo && p.hi) tags.push(`<span class="tag sec">Past cycles: ${fmt(p.lo)} to ${fmt(p.hi)}</span>`);
  const meta = [p.loc && `<span>${esc(p.loc)}</span>`, p.lt !== p.t && `<span>Last posted as “${esc(p.lt)}”</span>`].filter(Boolean).join('');
  const past = p.past.map(([y, d]) => `${fmtY(d)} <span>for ${cap(p.s)} ${y}</span>`).join(' · ');
  const act = p.key ? `<a class="btn" href="${esc(p.u)}" target="_blank" rel="noopener">Apply ↗</a>`
    : `<a class="btn find" href="${esc(p.u)}" target="_blank" rel="noopener">Career site ↗</a>`;
  return `<article class="pr st-${p.st}">
    <div class="when"><b>${esc(when)}</b><small>${esc(label)}</small></div>
    <div class="main">
      <div class="co">${esc(p.co)}</div>
      <h2 class="title">${esc(p.t)}</h2>
      ${meta ? `<div class="meta">${meta}</div>` : ''}
      <div class="past">Posted ${past}</div>
      <div class="tags">${tags.join('')}</div>
    </div>
    <div class="acts">${act}${p.last ? `<a class="lnk" href="${esc(p.last)}" target="_blank" rel="noopener">Last cycle's posting ↗</a>` : ''}</div>
  </article>`;
}

function renderPred(){
  const pool = pPool();
  const counts = MONTHS.map(mo => pool.filter(p => isSoon(p) && pMonthOf(p) === mo).length), most = Math.max(1, ...counts);
  $('pmonths').innerHTML = MONTHS.map((mo, i) => `<button class="mo" data-mo="${mo}" aria-pressed="${mo === pMonth}" title="Roles expected in ${MON[+mo.slice(5) - 1]} ${mo.slice(0, 4)}"><i style="height:${2 + Math.round(38 * counts[i] / most)}px"></i><b>${counts[i]}</b>${MON[+mo.slice(5) - 1]}</button>`).join('');
  let rows = pool.filter(p => pStat === 'all' || (pStat === 'soon' ? isSoon(p) : p.st === pStat));
  if(pMonth) rows = rows.filter(p => isSoon(p) && pMonthOf(p) === pMonth);
  rows.sort(pStat === 'late' ? (a, b) => b.exp.localeCompare(a.exp) : pStat === 'posted' ? (a, b) => (b.seen || '').localeCompare(a.seen || '')
    : (a, b) => a.exp.localeCompare(b.exp) || a.co.localeCompare(b.co));
  $('pshown').innerHTML = `<span>Showing ${Math.min(pLimit, rows.length)} of ${rows.length} roles</span>` +
    (pMonth ? `<span class="pick">Expected in ${MON[+pMonth.slice(5) - 1]} ${pMonth.slice(0, 4)}<button id="punpick" aria-label="Show every month">×</button></span>` : '');
  const empty = pStat === 'posted' ? 'None of these roles has been posted yet this cycle.'
    : pStat === 'late' ? 'Nothing overdue: every role due by now has been posted.' : 'No roles match these filters.';
  $('plist').innerHTML = rows.length ? rows.slice(0, pLimit).map(pCard).join('') : `<div class="empty">${esc(empty)}</div>`;
  $('pmore').hidden = rows.length <= pLimit;
  $('pmore').textContent = `Show ${Math.min(PAGE, rows.length - pLimit)} more`;
}
const pPress = () => document.querySelectorAll('#pstat button').forEach(x => x.setAttribute('aria-pressed', x.dataset.st === pStat));
$('pseason').addEventListener('click', e => { const b = e.target.closest('[data-term]'); if(!b) return; pT = b.dataset.term; pMonth = ''; setupPred(); renderPred(); });
$('pstat').addEventListener('click', e => { const b = e.target.closest('[data-st]'); if(!b) return; pStat = b.dataset.st; if(pStat !== 'soon') pMonth = ''; pPress(); pLimit = PAGE; renderPred(); });
$('pmonths').addEventListener('click', e => { const b = e.target.closest('[data-mo]'); if(!b) return;
  pMonth = pMonth === b.dataset.mo ? '' : b.dataset.mo; pStat = 'soon'; pPress(); pLimit = PAGE; renderPred(); });
$('pshown').addEventListener('click', e => { if(e.target.id === 'punpick'){ pMonth = ''; pLimit = PAGE; renderPred(); } });
$('paero').addEventListener('change', () => { pAero[pT] = $('paero').checked; pLimit = PAGE; renderPred(); });
$('pnear').addEventListener('change', () => { pNear[pT] = $('pnear').checked; pLimit = PAGE; renderPred(); });
['pq', 'pdisc'].forEach(id => $(id).addEventListener(id === 'pq' ? 'input' : 'change', () => { pLimit = PAGE; renderPred(); }));
$('pmore').addEventListener('click', () => { pLimit += PAGE; renderPred(); });

// Controls that depend on the section
function setupTab(){
  tabs();
  const view = VIEWS.includes(tab);
  $('jobsView').hidden = view;
  $('bigView').hidden = tab !== 'big';
  $('predView').hidden = tab !== 'pred';
  $('tabnote').hidden = view;
  if(tab === 'big'){ renderBig(); return; }
  if(tab === 'pred'){ setupPred(); renderPred(); return; }
  $('tabnote').textContent = tab === 'new' ? `Everything posted in the last 7 days, from every section, best fit first.`
    : tab === 'undated' ? `Postings with no posted date on their source, their own listing page, or any internship list the scan reads. They stay out of the other sections until a date turns up.`
    : tab === 'leads' ? `Postings only intern-list.com has found. Its links go to jobright.ai instead of the company, so Find posting searches for the company's own listing. A lead moves to the other sections on its own once a company career site the scan reads has the same job.`
    : T[tab].note;
  const inThis = D.jobs.filter(j => inTab(j, tab));
  const counts = {};
  for(const j of inThis) if(j.discipline) counts[j.discipline] = (counts[j.discipline] || 0) + 1;
  const discs = Object.entries(counts).sort((a, b) => b[1] - a[1]);
  $('disc').innerHTML = '<option value="">All disciplines</option>' + discs.map(([d, n]) => `<option value="${esc(d)}">${esc(d)} (${n})</option>`).join('');
  $('disc').hidden = tab === 'summer';
  $('sort').querySelector('[value=near]').hidden = tab !== 'fall';
  $('sort').value = tab === 'new' ? 'new' : 'score';
  $('seasonTog').hidden = mixed(tab);
  // Only offer to hide old postings when the age limit in profile.toml lets some through
  $('hideOld').parentNode.hidden = mixed(tab) || !inThis.some(isOld);
  $('season').checked = !!seasonChk[tab];
  if(!mixed(tab)) $('seasonLabel').textContent = tab === 'fall' ? 'Include nearby postings that don\'t name a season' : `Only ones that say ${T[tab].season_label}`;
  $('have').innerHTML = bars(topSkills(inThis, 'matched'), 'var(--pos)');
  $('need').innerHTML = bars(topSkills(inThis, 'gaps'), 'var(--neg)');
  limit = PAGE;
}

function render(){
  if(VIEWS.includes(tab)) return;
  if(!D.jobs.length){
    $('list').innerHTML = `<div class="empty"><p><b>No scan results yet.</b></p><p>In your GitHub repo, open the Actions tab, choose “Daily job scan”, and click “Run workflow”. This page fills in about five minutes later.</p></div>`;
    return;
  }
  const q = $('q').value.trim().toLowerCase(), disc = $('disc').hidden ? '' : $('disc').value;
  const hide = $('hideDone').checked, hideOld = $('hideOld').checked, seasonOn = $('season').checked;
  const pool = D.jobs.filter(j => inTab(j, tab));
  let jobs = pool.filter(j => {
    const tr = j.tracks[trackKey(j)];
    if(pick && !coMatch(j.company, pick.match)) return false;
    if(tier !== 'all' && tr.tier !== tier) return false;
    if(hide && status[j.key]) return false;
    if(hideOld && isOld(j)) return false;
    if(disc && j.discipline !== disc) return false;
    if(tab === 'fall' && !seasonOn && tr.season !== 'match') return false;
    if(tab !== 'fall' && !mixed(tab) && seasonOn && tr.season !== 'match') return false;
    if(q){
      const hay = [j.company, j.title, j.location, j.discipline, j.matched.join(' '), j.gaps.join(' ')].join(' ').toLowerCase();
      if(!q.split(/\s+/).every(w => hay.includes(w))) return false;
    }
    return true;
  });
  const sc = j => j.tracks[trackKey(j)].score;
  const mi = j => { const m = (j.tracks.fall || {}).miles; return typeof m === 'number' ? m : 999; };
  const s = $('sort').value;
  jobs.sort(s === 'new' ? (a,b) => ((b.posted || b.first_seen) + b.first_seen).localeCompare((a.posted || a.first_seen) + a.first_seen) || sc(b) - sc(a)
         : s === 'company' ? (a,b) => a.company.localeCompare(b.company) || sc(b) - sc(a)
         : s === 'reqs' ? (a,b) => reqPct(b) - reqPct(a) || sc(b) - sc(a)
         : s === 'near' ? (a,b) => mi(a) - mi(b) || sc(b) - sc(a)
         : (a,b) => sc(b) - sc(a));
  $('shown').innerHTML = `<span>Showing ${Math.min(limit, jobs.length)} of ${jobs.length} matching / ${pool.length} in this section</span>` +
    (pick ? `<span class="pick">${esc(pick.name)}<button id="unpick" aria-label="Show all companies">×</button></span>` : '');
  const emptyMsg = tab === 'undated' && !pool.length ? 'Every posting on the page has a posted date.'
    : tab === 'leads' && !pool.length ? 'No leads right now: every posting has a direct company link.'
    : tab === 'motor' && !pool.length ? T.motor.empty
    : tab === 'fall' && !pool.some(j => j.tracks.fall.season === 'match') ? T.fall.empty
    : 'No postings match these filters. Clear the search or choose “All”.';
  $('list').innerHTML = jobs.length ? jobs.slice(0, limit).map(card).join('') : `<div class="empty">${esc(emptyMsg)}</div>`;
  $('more').hidden = jobs.length <= limit;
  $('more').textContent = `Show ${Math.min(PAGE, jobs.length - limit)} more`;
}

function go(t){
  if(t === tab || !ORDER.includes(t)) return;
  tab = t;
  pref.set('tab', tab);
  history.replaceState(null, '', '#' + HASH[tab]);
  setupTab();
  render();
}
$('tabs').addEventListener('click', e => { const b = e.target.closest('[data-tab]'); if(b){ pick = null; go(b.dataset.tab); } });
addEventListener('hashchange', () => { pick = null; go(Object.keys(HASH).find(k => HASH[k] === location.hash.slice(1))); });
$('bigList').addEventListener('click', e => {
  const b = e.target.closest('[data-pick]');
  if(!b) return;
  pick = D.popular[+b.dataset.pick];
  go('broad');
  limit = PAGE;
  render();
  scrollTo({top: $('tabs').offsetTop - 8});
});
$('shown').addEventListener('click', e => { if(e.target.id === 'unpick'){ pick = null; limit = PAGE; render(); } });
document.querySelectorAll('.seg button').forEach(b => b.addEventListener('click', () => {
  tier = b.dataset.tier;
  document.querySelectorAll('.seg button').forEach(x => x.setAttribute('aria-pressed', x === b));
  limit = PAGE;
  render();
}));
$('season').addEventListener('change', () => { seasonChk[tab] = $('season').checked; });
['q','disc','sort','season','hideOld','hideDone'].forEach(id => $(id).addEventListener(id === 'q' ? 'input' : 'change', () => { limit = PAGE; render(); }));
$('more').addEventListener('click', () => { limit += PAGE; render(); });
$('list').addEventListener('click', e => {
  const btn = e.target.closest('button[data-act]');
  if(!btn) return;
  const key = btn.closest('.row').dataset.key;
  status[key] = status[key] === btn.dataset.act ? undefined : btn.dataset.act;
  if(!status[key]) delete status[key];
  store.set(status);
  render();
});
setupTab();
render();
})();
</script>
</body>
</html>
"""


def track_info(profile: dict) -> dict:
    """Tab names and one-line descriptions for each section, from profile.toml."""
    se, br, fa = profile["search"], profile.get("broad", {}), profile.get("fall", {})
    summer = f"{se.get('season', 'summer').title()} {se.get('year', 2027)}"
    info = {
        "summer": {"tab": summer, "season_label": summer,
                   "note": f"{summer} internships in aerospace and mechanical work at aerospace companies, "
                           "scored against your resume."},
        "broad": {"tab": "All engineering",
                  "season_label": f"{br.get('season', 'summer').title()} {br.get('year', 2027)}",
                  "note": "Every engineering internship found, from any company and any major. "
                          "Your resume's mechanical and aerospace skills push those to the top; use the discipline filter below to narrow it."},
    }
    mo = profile.get("motorsport", {})
    if mo.get("enabled", True):
        terms = [t.split() for t in mo.get("terms", ["summer 2027"])]
        seasons = [s.title() for s, _ in terms]
        years = {y for _, y in terms}
        label = (", ".join(seasons[:-1]) + " or " + seasons[-1] if len(seasons) > 1 else seasons[0]) + (
            f" {years.pop()}" if len(years) == 1 else "")
        info["motor"] = {
            "tab": "Motorsports", "season_label": label,
            "note": "Engineering internships at racing teams and motorsport companies (NASCAR, IndyCar, F1 and "
                    "sports car teams, race engine and chassis builders), plus racing roles at any company, for "
                    f"{label}. Race teams hire interns for every part of the season, not just the summer.",
            "empty": "No motorsport internships posted lately. Race teams post a few at a time, often for the "
                     "spring or fall; new ones show up here as soon as a scan finds them.",
        }
    if fa.get("enabled", True) and "home_lat" in fa:
        fall = f"{fa.get('season', 'fall').title()} {fa.get('year', 2027)}"
        home, radius = fa.get("home_name", "home"), fa.get("radius_miles", 50)
        info["fall"] = {
            "tab": f"{fall} near {home}", "season_label": fall, "home": home, "radius": radius,
            "note": f"{fall} internships and co-ops within {radius} miles of {home}"
                    + (", plus remote ones" if fa.get("include_remote", True) else "") + ". Any engineering discipline.",
            "empty": f"No {fall} postings within {radius} miles of {home} yet. Fall co-ops are mostly posted "
                     "January to April. Tick the box above to see nearby postings that don't name a season.",
        }
    return info


def build_page(jobs: list[dict], sources: list[dict], profile: dict, now: dt.datetime,
               popular: list[dict] | None = None, predicted: list[dict] | None = None,
               pred_info: dict | None = None) -> str:
    today = now.date().isoformat()
    page_jobs = [{k: j.get(k) for k in (
        "key", "company", "title", "location", "url", "source", "posted", "posted_from", "first_seen", "tracks",
        "discipline", "matched", "related", "gaps", "flags", "ai", "quals", "has_description", "lead")} for j in jobs]
    try:
        from zoneinfo import ZoneInfo
        eastern = now.astimezone(ZoneInfo("America/New_York"))
    except Exception:  # noqa: BLE001 - label only
        eastern = now - dt.timedelta(hours=4)
    data = {
        "name": profile["student"].get("name", "you"),
        # %-d / %-I are Linux-only, so build the unpadded parts by hand
        "updated_label": (f"{eastern:%b} {eastern.day}, {eastern.year} at "
                          f"{eastern.hour % 12 or 12}:{eastern:%M %p} ET") if jobs or sources else "never",
        "today": today,
        "old_after": int(profile.get("page", {}).get("old_after_days", 15)),
        "max_age": int(profile["search"].get("max_age_days", 0)),
        "tracks": track_info(profile),
        "jobs": page_jobs,
        "sources": sources,
        "popular": popular or [],
        "predicted": predicted or [],
        "pred_info": pred_info or {"postings": 0, "since": today},
        # Leads have their own section, so the headline numbers leave them out
        "counts": {
            "strong": sum(1 for j in jobs if not j.get("lead") and j["tracks"].get("summer", {}).get("tier") == "strong"),
            "new_today": sum(1 for j in jobs if not j.get("lead") and j.get("first_seen") == today),
        },
    }
    blob = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    return TEMPLATE.replace("__DATA__", blob)


def _readme_predicted(preds: list[dict], page_url: str, now: dt.datetime, top: int = 15) -> list[str]:
    """Aerospace roles expected in the next 60 days that haven't been posted yet."""
    soon = (now.date() + dt.timedelta(days=60)).isoformat()
    rows = [p for p in preds if p.get("aero") and p["st"] in ("upcoming", "due") and p["exp"] <= soon]
    lines = [f"**{len(rows)} aerospace internships expected in the next 60 days**, from past cycles' posting dates. "
             f"All of them, with filters: **[Predicted tab]({page_url}#predicted)**", "",
             "| Expected | Company | Role | For | Last cycle's posting date | Career site |", "|---|---|---|---|---|---|"]
    for p in rows[:top]:
        due = " (due now)" if p["st"] == "due" else ""
        lines.append(f"| ~{p['exp']}{due} | {p['co'].replace('|', '/')} | {p['t'].replace('|', '/')} "
                     f"| {p['s'].title()} {p['y']} | {p['past'][0][1]} | [Open]({p['u']}) |")
    if not rows:
        lines.append("| | Nothing expected in the next 60 days | | | | |")
    return lines


def _replace_block(text: str, start: str, end: str, lines: list[str]) -> str:
    if start not in text or end not in text:
        return text
    block = start + "\n" + "\n".join(lines) + "\n" + end
    return re.sub(re.escape(start) + r".*?" + re.escape(end), lambda _: block, text, flags=re.S)


def update_readme(path: Path, jobs: list[dict], page_url: str, now: dt.datetime, top: int = 25,
                  preds: list[dict] | None = None) -> None:
    """The README shows the top Summer 2027 aerospace matches (leads, which have no
    direct link, are only counted) and the aerospace roles expected soon."""
    start, end = "<!-- JOBS:START -->", "<!-- JOBS:END -->"
    text = path.read_text(encoding="utf-8")
    if preds is not None:
        text = _replace_block(text, "<!-- PREDICTED:START -->", "<!-- PREDICTED:END -->",
                              _readme_predicted(preds, page_url, now))
    if start not in text or end not in text:
        path.write_text(text, encoding="utf-8")
        return
    today = now.date().isoformat()
    leads = sum(1 for j in jobs if j.get("lead"))
    jobs = [j for j in jobs if not j.get("lead")]
    summer = [j for j in jobs if "summer" in j["tracks"]]
    others = ", ".join(f"{sum(1 for j in jobs if t in j['tracks'])} {name}"
                       for t, name in (("motor", "in Motorsports"), ("fall", "Fall 2027 near home"),
                                       ("broad", "in All engineering")))
    if leads:
        others += f", {leads} leads without a direct link"
    lines = [
        f"**{len(summer)} Summer 2027 aerospace matches** ({others}) as of {now:%b} {now.day}, {now.year}. "
        f"Full list with filters: **[open the job page]({page_url})**",
        "",
        "| Fit | Company | Role | Required quals met | Location | Posted | Apply |",
        "|---|---|---|---|---|---|---|",
    ]
    for j in sorted(summer, key=lambda j: -j["tracks"]["summer"]["score"])[:top]:
        new = " 🆕" if j.get("first_seen") == today else ""
        loc = re.sub(r"\s+", " ", (j.get("location") or ""))[:40]
        title = (j["title"] or "").replace("|", "/")
        s = (j.get("quals") or {}).get("summary") or {}
        reqs = f"{s['required_met']:g} of {s['required_checked']}" if s.get("required_checked") else "–"
        lines.append(f"| {j['tracks']['summer']['score']} | {j['company'].replace('|', '/')} | {title}{new} | {reqs} "
                     f"| {loc} | {j.get('posted') or 'unknown'} | [Apply]({j['url']}) |")
    if not summer:
        lines.append("| | No matches yet | Run the workflow from the Actions tab | | | | |")
    path.write_text(_replace_block(text, start, end, lines), encoding="utf-8")
