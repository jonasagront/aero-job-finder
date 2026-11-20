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
.newbtn{display:inline-flex;align-items:center;gap:7px;height:26px;padding:0 9px;border:1px solid var(--accent);border-radius:3px;background:none;font:inherit;letter-spacing:inherit;color:var(--accent);cursor:pointer;white-space:nowrap}
.newbtn:hover{background:var(--accent-bg)}
.newbtn[aria-pressed=true]{background:var(--accent);color:#fff}
.newbtn .n{font-weight:400;opacity:.85}
.fgroup{margin:26px 0 0;padding-bottom:8px;border-bottom:1px solid var(--line2);font:500 11.5px/1.3 var(--mono);letter-spacing:.07em;text-transform:uppercase;color:var(--ink2)}
.fgroup span{margin-left:8px;color:var(--muted)}
.fgroup.now{color:var(--accent)}

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

/* coverage line under the stats */
details.cov{margin-top:14px;border:1px solid var(--line);border-radius:3px;background:var(--surface)}
details.cov>summary{list-style:none;display:flex;flex-wrap:wrap;gap:4px 14px;align-items:center;padding:9px 12px;font:400 12.5px/1.4 var(--mono);color:var(--ink2);cursor:pointer}
details.cov>summary::-webkit-details-marker{display:none}
details.cov>summary::after{content:"Details +";margin-left:auto;font-size:11px;letter-spacing:.06em;text-transform:uppercase;color:var(--muted)}
details.cov[open]>summary::after{content:"Details \2212"}
.cov .lbl{font:500 11px/1.3 var(--mono);letter-spacing:.07em;text-transform:uppercase;color:var(--muted)}
.cov b{font-weight:500}
.c-ok{color:var(--pos)} .c-partial{color:var(--low)} .c-failed,.c-stale{color:var(--neg)} .c-off{color:var(--muted)}
.covbody{padding:2px 12px 14px;font-size:13px}
.covbody h3{margin:16px 0 6px;font:500 11px/1.3 var(--mono);letter-spacing:.07em;text-transform:uppercase;color:var(--muted)}
.covbody p{margin:6px 0;color:var(--ink2);max-width:90ch}
.covbody table{border-collapse:collapse;width:100%;font-size:12.5px}
.covbody td,.covbody th{text-align:left;padding:5px 10px 5px 0;border-bottom:1px solid var(--line);vertical-align:top}
.covbody th{font:500 10.5px/1.3 var(--mono);letter-spacing:.07em;text-transform:uppercase;color:var(--muted)}
.covbody details{margin-top:12px}
.covbody details>summary{cursor:pointer;font:500 11px/1.3 var(--mono);letter-spacing:.07em;text-transform:uppercase;color:var(--ink2)}
.covwarn{display:inline-flex;align-items:center;gap:6px;color:var(--neg);background:none;border:0;padding:0;font:inherit;cursor:pointer;text-decoration:underline dotted}

/* All opportunities filters */
.afl{display:flex;flex-wrap:wrap;gap:8px 12px;align-items:center}
.afl label{display:inline-flex;align-items:center;gap:6px;font-size:13px;color:var(--ink2)}
.afl select{height:32px;font-size:13px}
.reset{height:30px;padding:0 12px;border:1px solid var(--accent);border-radius:3px;background:none;color:var(--accent);font:500 11.5px/1 var(--mono);letter-spacing:.05em;text-transform:uppercase;cursor:pointer}
.reset:hover{background:var(--accent-bg)}
.chip{display:inline-flex;align-items:center;gap:6px;padding:2px 4px 2px 8px;border:1px solid var(--accent);border-radius:2px;color:var(--accent)}
.chip button{border:0;background:none;color:inherit;cursor:pointer;font:500 13px/1 var(--mono);padding:0 3px}
.tag.unc{border-style:dashed;color:var(--low)}
.tag.unread{background:var(--mid);border-color:var(--mid);color:#fff;font-weight:600}
.row.unread .title::before{content:"";display:inline-block;width:8px;height:8px;margin:0 8px 2px 0;border-radius:50%;background:var(--mid)}
.lnk.sv{color:var(--mid)}
.datebits{color:var(--muted)}

/* programs */
.pg{display:grid;grid-template-columns:110px minmax(0,1fr) 150px;gap:0 22px;padding:18px 0;border-bottom:1px solid var(--line)}
.pg .when b{display:block;font:500 19px/1.1 var(--mono);letter-spacing:-.01em}
.pg .when small{display:block;margin-top:6px;font:500 10px/1.25 var(--mono);letter-spacing:.07em;text-transform:uppercase;color:var(--muted)}
.pg.s-open .when b{color:var(--pos)} .pg.s-published .when b{color:var(--mid)} .pg.s-closed .when b{color:var(--faint)}
.pg p{margin:8px 0 0;font-size:13.5px;color:var(--ink2);max-width:80ch}
.pg ul{margin:6px 0 0;padding-left:18px;font-size:13.5px}
.pg q{color:var(--muted)}

/* my list */
.mine h3{margin:26px 0 0;padding-bottom:8px;border-bottom:1px solid var(--line2);font:500 11.5px/1.3 var(--mono);letter-spacing:.07em;text-transform:uppercase;color:var(--ink2)}
.mine h3 span{margin-left:8px;color:var(--muted)}
.hist{display:grid;grid-template-columns:90px minmax(0,1fr) 120px;gap:0 18px;padding:10px 0;border-bottom:1px solid var(--line);font-size:13.5px}
.hist .st{font:500 11px/1.3 var(--mono);letter-spacing:.06em;text-transform:uppercase;color:var(--muted)}
.tools{display:flex;flex-wrap:wrap;gap:10px;align-items:center;margin-top:14px}

@media (max-width:760px){
  .pg{grid-template-columns:80px minmax(0,1fr);gap:0 14px}
  .pg .acts{grid-column:1/-1;flex-direction:row;margin-top:12px;gap:8px}
  .hist{grid-template-columns:70px minmax(0,1fr)}
  .hist a{grid-column:2}
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
  .top{gap:10px;letter-spacing:.03em}
  .top .right{gap:8px}
  .brand{white-space:nowrap;gap:7px}
  .newbtn,.theme{padding:0 7px}
}
/* Phones: the logo alone, so New internships and Theme fit on one line */
@media (max-width:440px){
  .brand .bname{display:none}
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
  <div class="brand"><svg width="16" height="16" viewBox="0 0 32 32" aria-hidden="true"><path d="M5 27 16 4l11 23-11-5.5z" fill="var(--accent)"/></svg><span class="bname">Aero job finder</span></div>
  <div class="right"><button class="newbtn" id="unreadbtn" type="button" aria-pressed="false" hidden title="Opportunities you haven't reviewed, saved, applied to or dismissed">Unread<span class="n" id="unreadn"></span></button><button class="newbtn" id="newbtn" type="button" aria-pressed="false" hidden>New internships<span class="n" id="newn"></span></button><span class="stamp" id="stamp"></span><button class="theme" id="theme" type="button"></button></div>
</div>

<header class="hero">
  <h1>Engineering internships</h1>
  <p id="sub"></p>
  <dl class="stats" id="stats"></dl>
  <details class="cov" id="cov"><summary id="covsum"></summary><div class="covbody" id="covbody"></div></details>
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
      <option value="found">Most recently found</option>
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
    <button class="reset" id="markAll" type="button" hidden>Mark all as read</button>
  </div>
  <div class="ctl afl" id="allFilters" hidden>
    <label>Term <select id="fSeason" aria-label="Season"><option value="">Any season</option><option>Spring</option><option>Summer</option><option>Fall</option><option>Winter</option><option value="none">Not stated</option></select></label>
    <select id="fYear" aria-label="Year"><option value="">Any year</option></select>
    <label>Where <select id="fState" aria-label="State"></select></label>
    <select id="fRemote" aria-label="Remote"><option value="">On-site or remote</option><option value="only">Remote only</option><option value="no">No remote</option></select>
    <select id="fMiles" aria-label="Distance"></select>
    <select id="fDate" aria-label="Posted date"><option value="">Any posted date</option><option value="known">Posted date known</option><option value="unknown">Posting date unknown</option></select>
    <select id="fUnc" aria-label="Uncertain"><option value="">Uncertain included</option><option value="hide">Hide uncertain</option><option value="only">Uncertain only</option></select>
    <label class="tog"><input type="checkbox" id="fElig"> Hide eligibility problems</label>
    <button class="reset" id="fReset" type="button">Reset filters</button>
  </div>
</div>

<div class="shown" id="shown" aria-live="polite"></div>
<div id="list"></div>
<button class="more" id="more" hidden>Show more</button>
</div>

<section id="progView" hidden>
  <p class="bnote">Programs that aren't a company job board. Status, deadlines and eligibility are what each program's official page said on the date shown as verified; a date the page doesn't give is left out, and past-cycle timing is labeled as an estimate. Every scan re-reads each page it can and flags it when the page changes, so re-check those. Individual internship postings elsewhere on this page still follow the 15-day limit; these records follow each program's own application cycle.</p>
  <div id="progList"></div>
</section>

<section id="mineView" class="mine" hidden>
  <p class="bnote">Opportunities you saved or applied to, and a record of ones that are no longer listed. This is stored in this browser only: it doesn't sync between your phone and computer. Use Export to save it as a file and Import on another device (imports merge; nothing is deleted).</p>
  <div class="tools">
    <button class="reset" id="exportBtn" type="button">Export my data</button>
    <label class="reset" style="display:inline-flex;align-items:center">Import<input type="file" id="importFile" accept="application/json,.json" hidden></label>
    <span id="mineMsg" class="datebits"></span>
  </div>
  <div id="mineList"></div>
</section>

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
    <summary>All sources checked on this run</summary>
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
// ---- per-browser state: unread queue and activity history (stored here only; see My list)
const jget = (k, d) => { try { const v = JSON.parse(localStorage.getItem(k) || 'null'); return v === null ? d : v; } catch(e){ return d; } };
const jset = (k, v) => { try { localStorage.setItem(k, JSON.stringify(v)); } catch(e){} };
let activity = jget('ajf-activity', {});   // key -> {s: status, at, c, t, u} for the My list history
let unread = jget('ajf-unread', null);     // {since: ISO time, read: {key: date reviewed}}
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
// When the scan first found a posting, measured from this update (older saves only have the day)
const updMs = Date.parse(D.updated || (D.today + 'T12:00:00Z'));
const LATEST_HOURS = 72;
const foundKey = j => j.found_at || (j.first_seen ? j.first_seen + 'T00:00:00+00:00' : '');
const foundMs = j => j.found_at ? Date.parse(j.found_at) : j.first_seen ? Date.parse(j.first_seen + 'T12:00:00') : NaN;
const foundRecently = j => updMs - foundMs(j) <= LATEST_HOURS * 36e5;
const inThisUpdate = j => !!j.found_at && j.found_at === D.updated;
const clock = ms => new Date(ms).toLocaleTimeString(undefined, {hour:'numeric', minute:'2-digit'});
const dayDiff = ms => { const a = new Date(updMs), b = new Date(ms);
  return Math.round((new Date(a.getFullYear(), a.getMonth(), a.getDate()) - new Date(b.getFullYear(), b.getMonth(), b.getDate())) / 864e5); };
const foundLabel = j => {
  if(inThisUpdate(j)) return 'Found in this update';
  if(!j.found_at) return `Found ${fmt(j.first_seen)}`;
  const h = (updMs - Date.parse(j.found_at)) / 36e5;
  return h < 24 ? `Found ${Math.max(1, Math.round(h))}h before this update` : `Found ${fmt(j.found_at.slice(0, 10))}`;
};
// One heading per scan: "This update", "Earlier today · 12:06 PM", "Yesterday · 5:42 PM"...
const foundGroup = j => {
  if(inThisUpdate(j)) return ['now', `This update · ${clock(updMs)}`];
  if(!j.found_at) return ['d' + j.first_seen, `${fmt(j.first_seen)} · time not recorded`];
  const ms = Date.parse(j.found_at), dd = dayDiff(ms);
  const day = dd === 0 ? 'Earlier today' : dd === 1 ? 'Yesterday' : new Date(ms).toLocaleDateString(undefined, {weekday:'long', month:'short', day:'numeric'});
  return [j.found_at, `${day} · ${clock(ms)} scan`];
};
const coMatch = (company, terms) => { const c = (company || '').toLowerCase(); return terms.some(t => t[0] === '=' ? c === t.slice(1) : c.includes(t)); };

// The unread queue: everything found since the queue started stays unread until it's
// reviewed (Apply or "Mark read"), saved, applied to or dismissed, however long it stays
// on the page. The first visit starts it 3 days back, so it isn't the whole page.
if(!unread || !unread.since) unread = {since: new Date(updMs - LATEST_HOURS * 36e5).toISOString(), read: {}};
unread.read = unread.read || {};
unread.force = unread.force || {};  // marked unread again by hand
{ // forget review marks after 45 days, and carry state over from a posting's old link
  const cut = daysBack(45);
  for(const k in unread.read) if(unread.read[k] < cut) delete unread.read[k];
  for(const k in unread.force) if(unread.force[k] < cut) delete unread.force[k];
  for(const j of D.jobs) for(const a of (j.aka || [])){
    if(status[a] && !status[j.key]) status[j.key] = status[a];
    if(unread.read[a] && !unread.read[j.key]) unread.read[j.key] = unread.read[a];
    if(activity[a] && !activity[j.key]) activity[j.key] = activity[a];
  }
  store.set(status); jset('ajf-unread', unread); jset('ajf-activity', activity);
}
const sinceMs = () => Date.parse(unread.since);
const isUnread = j => !status[j.key] && !unread.read[j.key] && (!!unread.force[j.key] || foundMs(j) > sinceMs());
const markRead = key => { delete unread.force[key]; if(!unread.read[key]){ unread.read[key] = D.today; } jset('ajf-unread', unread); };
function setStatus(j, s){
  status[j.key] = status[j.key] === s ? undefined : s;
  if(!status[j.key]){ delete status[j.key]; delete activity[j.key]; }
  else activity[j.key] = {s: status[j.key], at: D.today, c: j.company, t: j.title, u: j.url};
  store.set(status); jset('ajf-activity', activity);
}
// Where a posting's date came from (older saved results only know posted/posted_from)
const dateKind = j => j.date_kind || (j.posted ? (j.posted_from ? 'listing' : 'employer') : 'none');
const WARN = j => j.flags.some(f => f.kind === 'warn');
const C = D.coverage || {counts: {}};
const problemSources = D.sources.filter(s => ['partial', 'failed', 'stale'].includes(s.state));

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
// "latest" (New internships) and "unread" live in the top bar beside the update time, not in the row of tabs
const PROGS = D.programs || [];
const ORDER = ['latest', 'unread', 'new', 'summer', 'motor', 'fall', 'broad', 'all', 'prog', 'pred', 'undated', 'leads', 'big', 'mine'].filter(k =>
  ['new', 'undated', 'mine', 'unread'].includes(k) || (k === 'latest' ? D.sources.length : k === 'leads' ? hasLeads : k === 'big' ? D.popular.length
    : k === 'pred' ? P.length : k === 'prog' ? PROGS.length : k === 'all' ? D.jobs.some(j => j.tracks.all) : T[k]));
const HASH = {latest:'new-internships', unread:'unread', new:'new', summer:'summer', motor:'motorsports', fall:'fall', broad:'all', all:'all-opportunities',
  prog:'programs', pred:'predicted', undated:'date-unknown', leads:'leads', big:'big-names', mine:'my-list'};
const NAME = {latest:'New internships', unread:'Unread', new:'New this week', all:'All opportunities', prog:'Programs', pred:'Predicted',
  undated:'Posting date unknown', leads:'Leads without a link', big:'Big names', mine:'My list'};
const VIEWS = ['big', 'pred', 'prog', 'mine'];  // sections that aren't a list of postings
const TOPBAR = ['latest', 'unread'];
for(const k in T) NAME[k] = T[k].tab;
// The best curated section for a posting ("all" only when it's in none of them)
const best = j => { const e = Object.entries(j.tracks), c = e.filter(([k]) => k !== 'all');
  return (c.length ? c : e).reduce((a, b) => !a || b[1].score > a[1].score ? b : a, null); };
const curated = j => Object.keys(j.tracks).some(k => k !== 'all');
// New internships, Unread, New this week, Posting date unknown and Leads gather postings from every other section
const mixed = t => ['latest', 'unread', 'new', 'undated', 'leads'].includes(t);
// Leads (no direct company link) only show in their own section and the unread queue
const inTab = (j, t) => t === 'leads' ? !!j.lead : t === 'unread' ? isUnread(j) : !j.lead &&
  (t === 'latest' ? foundRecently(j) : t === 'undated' ? !j.posted : t === 'new' ? postedThisWeek(j) : !VIEWS.includes(t) && !!j.tracks[t]);
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
  ? `Scored against ${D.name}'s resume. ${D.sources.filter(s => s.ok).length} company career sites and internship lists read every 5 hours.` +
    (D.max_age ? ` Only postings from the last ${D.max_age} days are shown (by posted date, or by the day the scan first found them when no date is known).` : '')
  : 'Waiting for the first scan.';
const c = D.counts;
const nSummer = D.jobs.filter(j => inTab(j, 'summer')).length;
$('stats').innerHTML = [
  [T.summer ? T.summer.tab + ' aerospace' : 'Postings', T.summer ? nSummer : D.jobs.length, ''],
  ['All opportunities', D.jobs.filter(j => inTab(j, 'all')).length, ''],
  ['Found today', c.new_today, c.new_today ? 'acc' : ''],
  ['Posted this week', D.jobs.filter(j => inTab(j, 'new')).length, ''],
].map(([k, v, cls]) => `<div><dt>${esc(k)}</dt><dd class="${cls}">${v}</dd></div>`).join('');
$('oldLabel').textContent = `Hide postings older than ${D.old_after} days`;

function tabs(){
  const n = k => k === 'big' ? D.popular.length : k === 'pred' ? P.filter(p => isSoon(p) && pTerm(p) === pTerms[0] && (p.aero || p.mo || !pAeroDefault(pTerms[0]))).length
    : k === 'prog' ? PROGS.filter(p => p.status === 'open' || p.status === 'published').length
    : k === 'mine' ? Object.values(status).filter(s => s === 'saved' || s === 'applied').length
    : D.jobs.filter(j => inTab(j, k)).length;
  $('newbtn').hidden = !ORDER.includes('latest');
  $('newbtn').setAttribute('aria-pressed', tab === 'latest');
  $('newn').textContent = n('latest');
  $('unreadbtn').hidden = !D.jobs.length;
  $('unreadbtn').setAttribute('aria-pressed', tab === 'unread');
  $('unreadn').textContent = n('unread');
  $('tabs').innerHTML = ORDER.filter(k => !TOPBAR.includes(k)).map(k => `<button class="tab" role="tab" data-tab="${k}" aria-selected="${k === tab}">${esc(NAME[k])}<span class="n">${n(k)}</span></button>`).join('');
}

// ---- coverage: which sources worked, so a failed scan never reads as "nothing posted"
const fmtT = iso => iso ? new Date(iso).toLocaleString(undefined, {month:'short', day:'numeric', hour:'numeric', minute:'2-digit'}) : 'never';
const STATE = {ok:'read fully', partial:'partial', failed:'failed', stale:'stale', off:'needs setup'};
function coverage(){
  const k = C.counts || {}, sus = D.sources.filter(s => s.suspicious);
  $('cov').hidden = !D.sources.length;
  $('covsum').innerHTML = `<span class="lbl">Sources this update</span>` +
    ['ok', 'partial', 'failed', 'stale', 'off'].filter(s => k[s]).map(s => `<span class="c-${s}"><b>${k[s]}</b> ${STATE[s]}</span>`).join('') +
    (sus.length ? `<span class="c-failed">⚠ ${sus.length} unexpected drop${sus.length > 1 ? 's' : ''}</span>` : '');
  const bad = D.sources.filter(s => s.state && s.state !== 'ok' || s.suspicious)
    .sort((a, b) => ['stale', 'failed', 'partial', 'off', 'ok'].indexOf(a.state) - ['stale', 'failed', 'partial', 'off', 'ok'].indexOf(b.state));
  const row = s => `<tr><td>${esc(s.name)}<br><span class="datebits">${esc(s.kind)}</span></td><td class="c-${s.state}">${esc(STATE[s.state] || s.state)}${s.suspicious ? '<br><span class="c-failed">⚠ ' + esc(s.suspicious) + '</span>' : ''}</td>` +
    `<td>${esc(fmtT(s.last_success))}${s.last_complete && s.last_complete !== s.last_success ? '<br><span class="datebits">complete: ' + esc(fmtT(s.last_complete)) + '</span>' : ''}</td>` +
    `<td>${esc(s.error || (s.notes || []).join('; ') || '')}</td><td>${s.careers ? `<a href="${esc(s.careers)}" target="_blank" rel="noopener">Career site ↗</a>` : ''}</td></tr>`;
  let h = `<p>"Read fully" means the request worked and nothing cut it short. <b>Partial</b>: it worked but stopped early (a page cap, a page that failed, a site that repeated itself), so postings it didn't return are kept from earlier scans, marked as not re-checked, instead of being treated as closed. <b>Failed</b>: no answer this time, but it worked within the last day. <b>Stale</b>: it hasn't worked for over a day; its postings stay (still subject to the ${D.max_age}-day limit) and are marked as not re-checked. Check those companies' career sites by hand.</p>`;
  h += bad.length ? `<div class="tbl"><table><tr><th>Source</th><th>State</th><th>Last worked</th><th>Error or notes</th><th></th></tr>${bad.map(row).join('')}</table></div>` : '<p>Every source was read completely.</p>';
  const dr = D.discovery || {};
  if(dr.date){
    const rep = dr.repair || [];
    h += `<details><summary>Boards found automatically: ${Object.entries(dr.states || {}).map(([s, n]) => n + ' ' + s).join(', ')}</summary>` +
      `<p>Boards that fail are retried every run three times, then after 1, 2, 4, 8 and at most 14 days; they're never dropped for failing. A board that moved to another hiring system is replaced when the lists link to the new one.</p>` +
      (rep.length ? `<div class="tbl"><table><tr><th>Repair queue</th><th>Failing since</th><th>Next try</th><th>Error</th><th></th></tr>${rep.map(r => `<tr><td>${esc(r.name)}<br><span class="datebits">${esc(r.kind)} · ${r.fails} failed runs · last worked ${esc(r.last_ok || 'never')}</span></td><td>${esc(r.since)}</td><td>${esc(r.next_try)}</td><td>${esc(r.error)}</td><td>${r.link ? `<a href="${esc(r.link)}" target="_blank" rel="noopener">Career site ↗</a>` : ''}</td></tr>`).join('')}</table></div>` : '<p>Nothing in the repair queue.</p>') +
      ((dr.added || []).length ? `<h3>Added this run</h3><p>${dr.added.map(a => esc(a.name) + ' (' + esc(a.kind) + ', ' + esc(a.via) + ')').join('; ')}</p>` : '') +
      ((dr.moved || []).length ? `<h3>Moved or covered elsewhere</h3><p>${dr.moved.map(m => esc(m.name) + (m.moved_to ? ' → ' + esc(m.moved_to) : ' (another board covers it)')).join('; ')}</p>` : '') +
      ((dr.candidates || []).length ? `<h3>Candidate boards waiting to be validated (${dr.candidates.length})</h3><p>${dr.candidates.slice(0, 25).map(r => esc(r.name)).join(', ')}</p>` : '') +
      ((dr.unsupported || []).length ? `<h3>Hiring systems the scan can't read yet (relevant companies on the lists)</h3><p>${dr.unsupported.map(u => `${esc(u.host)} (${u.count}: ${esc(u.companies.join(', '))})`).join('; ')}</p>` : '') +
      (dr.probed ? `<p>Name lookups: ${dr.probed.done} of ${dr.probed.names} names checked on Greenhouse, Lever, Ashby, SmartRecruiters and Workable so far; ${dr.probed.found} had a board.</p>` : '') + `</details>`;
  }
  const au = D.audit || {};
  if(au.audits){
    const pct = au.in_scope ? Math.round(100 * au.found / au.in_scope) : null;
    h += `<details><summary>Coverage audit: ${au.found} of ${au.in_scope} in-scope postings found${pct !== null ? ' (' + pct + '%)' : ''} on ${au.boards} boards since ${esc(fmt(au.since))}</summary>` +
      `<p>Each run, a few boards are re-read as completely as the site allows (Workday sites in full) and every internship there that passes the same basic checks and the ${D.max_age}-day limit is looked up on this page. This measures the audited boards only, not every employer.</p>` +
      `<p>Misses by where they were lost: ${Object.entries(au.by_category || {}).map(([k, v]) => k + ' ' + v).join(', ') || 'none'}.</p>` +
      ((au.recent_misses || []).length ? `<div class="tbl"><table><tr><th>Missed posting</th><th>Lost at</th><th>Why</th></tr>${au.recent_misses.map(m => `<tr><td><a href="${esc(m.url)}" target="_blank" rel="noopener">${esc(m.title)}</a><br><span class="datebits">${esc(m.source)} · audited ${esc(m.date)}</span></td><td>${esc(m.category)}</td><td>${esc(m.why)}</td></tr>`).join('')}</table></div>` : '') + `</details>`;
  }
  const rj = D.rejections || {};
  if(Object.keys(rj).length){
    h += `<details><summary>What the filters dropped this run (${D.read || 0} postings read)</summary>` +
      Object.entries(rj).filter(([, v]) => Object.keys(v).length).map(([stage, v]) => `<h3>${esc(stage)}</h3><p>${Object.entries(v).map(([r, n]) => esc(r) + ': ' + n).join(' · ')}</p>`).join('') +
      `<p>Examples of each are saved in data/rejections.json.</p></details>`;
  }
  if(D.digest) h += `<p class="datebits">Daily digest: ${esc(D.digest.status)}.</p>`;
  $('covbody').innerHTML = h;
}
coverage();
const covNote = () => problemSources.length ? ` <button class="covwarn" data-cov>${problemSources.length} source${problemSources.length > 1 ? 's' : ''} not fully read this update: this list may be missing postings</button>` : '';

function bars(list, color){
  if(!list.length) return '<p style="color:var(--muted);font-size:13.5px;margin:0">Not enough descriptions yet.</p>';
  return list.map(g => `<div class="bar"><span>${esc(g.name)}</span><i><span style="width:${g.pct}%;background:${color}"></span></i><em>${g.pct}%</em></div>`).join('');
}
function topSkills(jobs, field){
  const withDesc = jobs.filter(j => j.has_description), n = {};
  for(const j of withDesc) for(const s of j[field]) n[s] = (n[s] || 0) + 1;
  return Object.entries(n).sort((a, b) => b[1] - a[1]).slice(0, 8).map(([name, v]) => ({name, pct: Math.round(100 * v / withDesc.length)}));
}

$('src').innerHTML = '<tr><th>Source</th><th>Type</th><th>Result</th><th>Last worked</th></tr>' + D.sources.map(s =>
  `<tr><td>${s.careers ? `<a href="${esc(s.careers)}" target="_blank" rel="noopener">${esc(s.name)}</a>` : esc(s.name)}</td><td>${esc(s.kind)}</td><td class="${s.ok && s.complete !== false ? '' : 'bad'}">${s.ok ? s.count + ' postings read' + (s.complete === false ? ' (partial: ' + esc((s.notes || []).join('; ')) + ')' : '') : 'Failed: ' + esc(s.error)}</td><td>${esc(fmtT(s.last_success))}</td></tr>`).join('');
const isFound = s => String(s.kind).includes('found automatically');
const nFound = D.sources.filter(isFound).length;
$('foot').textContent = `${D.sources.length} sources checked` + (nFound ? ` (${nFound} career sites found automatically)` : '') +
  `. Sources that fail or stop early are listed at the top of the page. Scores are keyword-based estimates. Always read the posting before applying.`;

const QI = {met:'✓', partial:'~', missing:'✗', check:'?', soft:'·'};
const num = x => Number.isInteger(x) ? x : x.toFixed(1);
// "Most qualifications met": preferred first (what sets you apart), then required
const reqPct = j => { const s = j.quals && j.quals.summary; if(!s) return -1;
  const f = (m, n) => n ? m / n : 0.5; return (s.preferred_total || s.required_checked) ? 0.6 * f(s.preferred_met, s.preferred_total) + 0.4 * f(s.required_met, s.required_checked) : -1; };
function qualTag(q){
  const s = q && q.summary;
  if(!s) return '';
  const out = [];
  if(s.preferred_total){
    const r = s.preferred_met / s.preferred_total;
    out.push(`<span class="tag ${r >= 0.6 ? 'ok' : r < 0.3 ? 'warn' : ''}">Preferred ${num(s.preferred_met)} of ${s.preferred_total}</span>`);
  }
  if(s.required_checked){
    const cls = s.required_missing ? 'warn' : s.required_met === s.required_checked ? 'ok' : '';
    out.push(`<span class="tag ${cls}">Required ${num(s.required_met)} of ${s.required_checked}</span>`);
  }
  return out.join('');
}
function qualList(q){
  if(!q) return '';
  const sec = (name, rows) => rows && rows.length ? `<div class="qh">${name}</div><ul class="ql">` + rows.map(r =>
    `<li class="q-${r.status}"><b>${QI[r.status]}</b><span>${esc(r.text)}${r.why ? `<small>${esc(r.why)}</small>` : (r.status === 'check' ? '<small>Couldn\'t check this one automatically</small>' : '')}</span></li>`).join('') + '</ul>' : '';
  const s = q.summary, bits = [];
  if(s.preferred_total) bits.push(`Your resume shows ${num(s.preferred_met)} of ${s.preferred_total} preferred qualifications (partial counts half)`);
  if(s.required_checked) bits.push(`you meet ${num(s.required_met)} of ${s.required_checked} required ones I could check`);
  let head = bits.length ? bits.join(', and ') + '.' : 'Qualifications found, but none I could check automatically.';
  head = head.charAt(0).toUpperCase() + head.slice(1);
  if(s.to_check) head += ` ${s.to_check} to confirm yourself.`;
  return `<details class="x"><summary>Qualifications</summary><div class="body"><p class="qhead">${head}</p>${sec('Preferred', q.preferred)}${sec('Required', q.required)}</div></details>`;
}
const where = tr => tr.miles === 'remote' ? 'Remote' : `${tr.miles} mi from ${T.fall.home}`;

function card(j){
  const st = status[j.key];
  const k = trackKey(j), tr = j.tracks[k] || j.tracks.all || best(j)[1];
  const un = isUnread(j);
  const tags = [];
  if(un) tags.push('<span class="tag unread">Unread</span>');
  // "Found today" is when the scan found it, not when it was posted (see the date line)
  if(j.first_seen >= D.today) tags.push('<span class="tag new">Found today</span>');
  if(j.stale) tags.push(`<span class="tag old" title="${esc('Not seen on the latest scan because ' + j.stale.why + '. Kept until it passes the ' + D.max_age + '-day limit.')}">Not re-checked since ${esc(fmt(j.stale.since))}</span>`);
  if(isOld(j)) tags.push(`<span class="tag old">Older than ${D.old_after} days</span>`);
  if(mixed(tab) || tab === 'all'){
    for(const t of ORDER) if(t !== 'all' && T[t] && j.tracks[t]) tags.push(`<span class="tag sec">${tab === 'all' ? 'In ' : ''}${esc(t === 'fall' ? NAME[t] + ' · ' + where(j.tracks[t]) : NAME[t])}</span>`);
  } else if(k === 'fall'){
    tags.push(`<span class="tag sec">${esc(where(tr))}</span>`);
  }
  if(tab === 'all' && j.geo && j.geo.mi != null && T.fall) tags.push(`<span class="tag sec">${j.geo.approx ? '~' : ''}${j.geo.mi} mi from ${esc(T.fall.home)}</span>`);
  tags.push(`<span class="tag ${tr.season === 'match' ? 'ok' : ''}">${esc(tr.season_label)}</span>`);
  if(k !== 'summer' && j.discipline) tags.push(`<span class="tag">${esc(j.discipline)}</span>`);
  const qt = qualTag(j.quals); if(qt) tags.push(qt);
  for(const f of j.flags) tags.push(`<span class="tag ${f.kind === 'info' ? '' : f.kind === 'good' ? 'ok' : f.kind}">${esc(f.label)}</span>`);
  for(const u of j.uncertain || []) tags.push(`<span class="tag unc" title="Couldn't be settled automatically; kept so you can judge">? ${esc(u)}</span>`);
  const p = tr.parts, rows = [];
  if(j.matched.length) rows.push(`<dt>Your skills it asks for</dt><dd>${esc(j.matched.join(', '))}</dd>`);
  if(j.related.length) rows.push(`<dt>Transferable</dt><dd>${esc(j.related.join(', '))}</dd>`);
  if(j.gaps.length) rows.push(`<dt>Not on your resume</dt><dd>${esc(j.gaps.join(', '))}</dd>`);
  const fitName = k === 'summer' ? 'aerospace fit' : 'engineering fit';
  rows.push(`<dt>Score</dt><dd>` + (p.preferred !== undefined
    ? `Preferred qualifications ${p.preferred}/40, required ${p.required}/25, ${fitName} ${p.fit}/20, eligibility ${p.eligibility}/15`
    : `${fitName} ${p.fit}/40, skills ${p.skills}/35, eligibility ${p.eligibility}/25`) +
    (p.requirements ? `, ${p.requirements} for missing required qualifications` : '') + `</dd>`);
  const miss = Object.entries(j.misses || {}).filter(([t]) => T[t]);
  if(miss.length) rows.push(`<dt>Not in these tabs</dt><dd>${miss.map(([t, why]) => esc(NAME[t]) + ': ' + esc(why)).join('<br>')}</dd>`);
  rows.push(`<dt>Found via</dt><dd>${esc(j.source)}${j.lead ? ' (no direct link: the button searches for the company\'s own posting)' : ''}</dd>`);
  rows.push(`<dt>Dates</dt><dd>${dateDetail(j)}</dd>`);
  const ai = j.ai ? `<div class="ai"><b>Claude's take (${esc(j.ai.fit)}):</b> ${esc(j.ai.summary)}${j.ai.talking_point ? '<br><b>Lead with:</b> ' + esc(j.ai.talking_point) : ''}</div>` : '';
  const age = ageDays(j.posted), dk = dateKind(j);
  // Employer's own date, a list's date (named), or none: never the day it was found
  const when = dk === 'employer'
    ? `<span>Posted ${fmt(j.posted)} (${age <= 0 ? 'today' : age + 'd ago'})</span>`
    : dk === 'listing'
    ? `<span title="The employer's own posted date isn't known; this is when ${esc(j.posted_from || 'a list')} listed it">Listed ${fmt(j.posted)} on ${esc(j.posted_from || 'a list')} (${age <= 0 ? 'today' : age + 'd ago'})</span>`
    : `<span title="Not on its source, its own listing page, or any internship list the scan reads. It counts toward the ${D.max_age}-day limit from the day it was first found.">Posting date unknown</span>`;
  const meta = [j.location && `<span>${esc(j.location)}</span>`, when, `<span>${esc(foundLabel(j))}</span>`].filter(Boolean).join('');
  const apply = j.lead
    ? `<a class="btn find" href="${esc(j.url)}" target="_blank" rel="noopener" data-open>Find posting ↗</a>`
    : `<a class="btn" href="${esc(j.url)}" target="_blank" rel="noopener" data-open>Apply ↗</a>`;
  return `<article class="row t-${tr.tier} ${st === 'applied' || st === 'dismissed' ? 'done' : ''} ${un ? 'unread' : ''}" data-key="${esc(j.key)}">
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
      <button class="lnk ${st === 'saved' ? 'sv' : ''}" data-act="saved">${st === 'saved' ? 'Saved ★' : 'Save'}</button>
      <button class="lnk ${st === 'applied' ? 'on' : ''}" data-act="applied">${st === 'applied' ? 'Applied ✓' : 'Mark applied'}</button>
      <button class="lnk" data-act="dismissed">${st === 'dismissed' ? 'Dismissed' : 'Dismiss'}</button>
      ${st ? '' : `<button class="lnk" data-act="read">${un ? 'Mark read' : 'Mark unread'}</button>`}
    </div>
  </article>`;
}
// Employer date, list date and first-found date, kept apart
function dateDetail(j){
  const dk = dateKind(j), out = [];
  out.push(dk === 'employer' ? `Employer's posted date: ${fmtY(j.posted)}` : `Employer's posted date: not known`);
  if(dk === 'listing') out.push(`Listed on ${esc(j.posted_from || 'a list')}: ${fmtY(j.posted)} (third-party date)`);
  out.push(`First found by this scan: ${j.found_at ? esc(fmtT(j.found_at)) : esc(fmtY(j.first_seen))}`);
  if(j.checked) out.push(`Last confirmed on its source: ${esc(fmtT(j.checked))}`);
  if(j.stale) out.push(`Not seen on the latest scan: ${esc(j.stale.why)}`);
  out.push(`Age for the ${D.max_age}-day limit counts from ${dk === 'none' ? 'the day it was first found' : 'the date above'}.`);
  return out.join('<br>');
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
    const scanBad = p.scan && p.scan !== 'ok';
    if(mine.length) st = `<button class="go" data-pick="${i}" title="Open postings from the last ${D.max_age} days">${mine.length} posted recently →</button><small>${strong ? `${strong} strong fit${strong > 1 ? 's' : ''}` : 'None rated strong yet'}${scanBad ? ' · scan ' + esc(p.scan) + ', may be missing some' : ''}</small>`;
    // A failed or partial scan is never shown as "nothing posted"
    else if(scanBad) st = `<span class="c-failed">Scan ${p.scan === 'partial' ? 'incomplete' : esc(p.scan)}</span><small title="${esc(p.scan_note || '')}">Couldn't confirm what's posted; check their site</small>`;
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

// ---- programs (NASA OSTEM, NREIP, AFRL Scholars, SULI...): not postings, so no 15-day limit
const PST = {open:'Open', published:'Deadline published', 'not-yet':'Not open yet', unverified:'Unverified', closed:'Closed'};
function renderProg(){
  $('progList').innerHTML = PROGS.map(p => {
    const next = p.deadlines.find(d => !d.passed);
    const [b, s] = next ? [fmt(next.date), `${next.term} deadline · ${next.days === 0 ? 'today' : next.days + ' days'}`]
      : [PST[p.status] || p.status, p.deadlines.length ? 'All listed deadlines passed' : 'No deadline published'];
    const tags = [`<span class="tag ${p.status === 'open' ? 'ok' : p.status === 'closed' ? '' : 'old'}">${esc(PST[p.status] || p.status)}</span>`,
      ...p.terms.map(t => `<span class="tag sec">${esc(t)}</span>`), `<span class="tag">Verified ${esc(fmtY(p.verified))}</span>`];
    if(p.changed) tags.push(`<span class="tag warn">Page changed ${esc(fmt(p.changed))}: re-check</span>`);
    if(p.check_ok === false) tags.push(`<span class="tag unc">${esc(p.check_error || 'Not re-checked automatically')}</span>`);
    const dl = p.deadlines.map(d => `<li>${esc(d.term)}: <b>${esc(fmtY(d.date))}</b>${d.passed ? ' (passed)' : ''} <q>${esc(d.text)}</q></li>`).join('');
    return `<article class="pg s-${esc(p.status)}">
      <div class="when"><b>${esc(b)}</b><small>${esc(s)}</small></div>
      <div class="main">
        <div class="co">${esc(p.sponsor)}</div>
        <h2 class="title">${esc(p.name)}</h2>
        <div class="tags">${tags.join('')}</div>
        ${p.status_note ? `<p>${esc(p.status_note)}</p>` : ''}
        <details class="x"><summary>Eligibility and dates</summary><div class="body">
          <p><b>Eligibility (as the page states):</b> ${esc(p.eligibility)}</p>
          ${dl ? `<p><b>Deadlines on the official page:</b></p><ul>${dl}</ul>` : '<p>No deadline is published on the official page.</p>'}
          ${p.estimate ? `<p><b>Estimate (past cycle, not an announced date):</b> ${esc(p.estimate)}</p>` : ''}
          <p class="datebits">Verified on the official page ${esc(fmtY(p.verified))}${p.page_updated ? ' (page last updated ' + esc(fmtY(p.page_updated)) + ')' : ''}. Page last re-checked by the scan ${esc(fmtT(p.checked))}.</p>
          ${(p.dates_seen || []).length && p.changed ? `<p class="datebits">Dates on the page now: ${p.dates_seen.map(esc).join(' · ')}</p>` : ''}
        </div></details>
      </div>
      <div class="acts"><a class="btn" href="${esc(p.apply)}" target="_blank" rel="noopener">Apply ↗</a><a class="lnk" href="${esc(p.url)}" target="_blank" rel="noopener">Official page ↗</a></div>
    </article>`;
  }).join('') || '<div class="empty">No programs set up (programs.toml).</div>';
}

// ---- my list: saved and applied postings, and ones no longer listed
function renderMine(){
  const live = new Map(D.jobs.map(j => [j.key, j]));
  const act = Object.entries(activity);
  const section = (title, rows) => `<h3>${esc(title)}<span>${rows.length}</span></h3>` + (rows.length ? rows.join('') : '<div class="empty" style="padding:18px">None yet.</div>');
  const activeOf = s => D.jobs.filter(j => status[j.key] === s);
  const gone = act.filter(([k]) => !live.has(k)).sort((a, b) => (b[1].at || '').localeCompare(a[1].at || ''));
  $('mineList').innerHTML = section('Saved', activeOf('saved').map(card)) + section('Applied', activeOf('applied').map(card)) +
    `<h3>No longer listed<span>${gone.length}</span></h3><p class="datebits">Postings you acted on that have closed or passed the ${D.max_age}-day limit. Kept here as a record only.</p>` +
    (gone.length ? gone.map(([k, a]) => `<div class="hist"><span class="st">${esc(a.s)} ${esc(fmt(a.at))}</span><span>${esc(a.c)}: ${esc(a.t)}</span>${a.u ? `<a class="lnk" href="${esc(a.u)}" target="_blank" rel="noopener">Old link ↗</a>` : '<span></span>'}</div>`).join('') : '');
}
$('exportBtn').addEventListener('click', () => {
  const blob = new Blob([JSON.stringify({app: 'aero-job-finder', version: 1, exported: new Date().toISOString(), status, activity, unread}, null, 1)], {type: 'application/json'});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob); a.download = `aero-job-finder-${D.today}.json`;
  document.body.appendChild(a); a.click(); a.remove();
  $('mineMsg').textContent = 'Exported.';
});
$('importFile').addEventListener('change', e => {
  const f = e.target.files[0]; if(!f) return;
  f.text().then(t => {
    const d = JSON.parse(t);
    if(d.app !== 'aero-job-finder') throw new Error('not an export from this page');
    status = {...status, ...(d.status || {})}; activity = {...activity, ...(d.activity || {})};
    if(d.unread){ unread.read = {...unread.read, ...(d.unread.read || {})}; if(d.unread.since > unread.since) unread.since = d.unread.since; }
    store.set(status); jset('ajf-activity', activity); jset('ajf-unread', unread);
    $('mineMsg').textContent = `Imported ${Object.keys(d.status || {}).length} statuses.`;
    tabs(); renderMine();
  }).catch(err => { $('mineMsg').textContent = 'Import failed: ' + err.message; });
  e.target.value = '';
});

// ---- All opportunities filters (separate from the Summer and Fall tabs' settings, and not saved)
const AF = {fSeason: '', fYear: '', fState: '', fRemote: '', fMiles: '', fDate: '', fUnc: '', fElig: false};
function setupAll(){
  const years = [...new Set(D.jobs.flatMap(j => (j.terms || []).map(t => t.split(' ')[1])))].sort();
  $('fYear').innerHTML = '<option value="">Any year</option>' + years.map(y => `<option>${esc(y)}</option>`).join('');
  const st = {};
  for(const j of D.jobs) if(!j.lead) for(const s of (j.geo || {}).states || []) st[s] = (st[s] || 0) + 1;
  $('fState').innerHTML = '<option value="">Anywhere in the U.S.</option>' + Object.keys(st).sort().map(s => `<option value="${s}">${s} (${st[s]})</option>`).join('');
  const home = T.fall ? T.fall.home : 'home';
  $('fMiles').innerHTML = `<option value="">Any distance</option>` + [25, 55, 100, 250, 500, 1000].map(m => `<option value="${m}">Within ${m} mi of ${esc(home)}</option>`).join('');
  for(const k in AF) if($(k).type === 'checkbox') $(k).checked = AF[k]; else $(k).value = AF[k];
}
const afActive = () => Object.entries(AF).filter(([k, v]) => v);
const AFLABEL = {fSeason: v => v === 'none' ? 'Term not stated' : v, fYear: v => v, fState: v => v, fRemote: v => v === 'only' ? 'Remote only' : 'No remote',
  fMiles: v => `≤${v} mi`, fDate: v => v === 'known' ? 'Posted date known' : 'Posting date unknown', fUnc: v => v === 'hide' ? 'No uncertain' : 'Uncertain only', fElig: () => 'No eligibility problems'};
function allOk(j){
  const terms = j.terms || [], g = j.geo || {};
  if(AF.fSeason === 'none' ? terms.length : AF.fSeason && !terms.some(t => t.startsWith(AF.fSeason) && (!AF.fYear || t.endsWith(AF.fYear)))) return false;
  if(AF.fYear && AF.fSeason !== 'none' && !terms.some(t => t.endsWith(AF.fYear))) return false;
  if(AF.fState && !(g.states || []).includes(AF.fState)) return false;
  if(AF.fRemote === 'only' && !g.remote) return false;
  if(AF.fRemote === 'no' && g.remote && !(g.states || []).length) return false;
  if(AF.fMiles && !(g.mi != null && g.mi <= +AF.fMiles) && !(g.remote && AF.fRemote !== 'no')) return false;
  if(AF.fDate === 'known' && !j.posted || AF.fDate === 'unknown' && j.posted) return false;
  const unc = (j.uncertain || []).length > 0;
  if(AF.fUnc === 'hide' && unc || AF.fUnc === 'only' && !unc) return false;
  if(AF.fElig && WARN(j)) return false;
  return true;
}
['fSeason', 'fYear', 'fState', 'fRemote', 'fMiles', 'fDate', 'fUnc', 'fElig'].forEach(id => $(id).addEventListener('change', () => {
  AF[id] = $(id).type === 'checkbox' ? $(id).checked : $(id).value; limit = PAGE; render(); }));
$('fReset').addEventListener('click', () => { for(const k in AF) AF[k] = k === 'fElig' ? false : ''; tier = 'all';
  document.querySelectorAll('.seg button[data-tier]').forEach(x => x.setAttribute('aria-pressed', x.dataset.tier === 'all'));
  $('disc').value = ''; $('q').value = ''; setupAll(); limit = PAGE; render(); });

// Controls that depend on the section
function setupTab(){
  tabs();
  const view = VIEWS.includes(tab);
  $('jobsView').hidden = view;
  $('bigView').hidden = tab !== 'big';
  $('predView').hidden = tab !== 'pred';
  $('progView').hidden = tab !== 'prog';
  $('mineView').hidden = tab !== 'mine';
  $('tabnote').hidden = view;
  $('allFilters').hidden = tab !== 'all';
  $('markAll').hidden = tab !== 'unread';
  if(tab === 'big'){ renderBig(); return; }
  if(tab === 'pred'){ setupPred(); renderPred(); return; }
  if(tab === 'prog'){ renderProg(); return; }
  if(tab === 'mine'){ renderMine(); return; }
  if(tab === 'all') setupAll();
  const nNow = D.jobs.filter(j => !j.lead && inThisUpdate(j)).length;
  $('tabnote').textContent = tab === 'latest' ? `Internships the scan found in the ${LATEST_HOURS / 24} days up to this update (${D.updated_label}), from every section, grouped by the scan that found them. Found is when the scan first saw it, not when it was posted. ` +
      (nNow ? `${nNow} ${nNow === 1 ? 'is' : 'are'} new in this update.` : 'Nothing new turned up in this update.')
    : tab === 'unread' ? `Everything found since ${fmtY(unread.since.slice(0, 10))} that you haven't reviewed (opened with Apply or marked read), saved, applied to or dismissed, whichever tab it's in. Items stay here until you act on them or they pass the ${D.max_age}-day limit. Stored in this browser only (export it from My list).`
    : tab === 'new' ? `Everything posted in the last 7 days, from every section, best fit first.`
    : tab === 'all' ? `Every engineering internship and student program found in the last ${D.max_age} days, at any score, for any term, anywhere in the U.S. Low scores rank lower instead of disappearing, and postings that couldn't be fully checked are marked "?" rather than dropped. The filters here don't change the Summer or Fall tabs.`
    : tab === 'undated' ? `Postings with no posted date on their source, their own listing page, or any internship list the scan reads. They also appear in the other tabs, labeled "Posting date unknown"; the ${D.max_age}-day limit counts from the day the scan first found them.`
    : tab === 'leads' ? `Postings only intern-list.com has found. Its links go to jobright.ai instead of the company, so Find posting searches for the company's own listing. A lead moves to the other sections on its own once a company career site the scan reads has the same job.`
    : T[tab].note;
  const inThis = D.jobs.filter(j => inTab(j, tab));
  const counts = {};
  for(const j of inThis) if(j.discipline) counts[j.discipline] = (counts[j.discipline] || 0) + 1;
  const discs = Object.entries(counts).sort((a, b) => b[1] - a[1]);
  $('disc').innerHTML = '<option value="">All disciplines</option>' + discs.map(([d, n]) => `<option value="${esc(d)}">${esc(d)} (${n})</option>`).join('');
  $('disc').hidden = tab === 'summer';
  $('sort').querySelector('[value=near]').hidden = tab !== 'fall' && tab !== 'all';
  $('sort').value = tab === 'latest' || tab === 'unread' ? 'found' : tab === 'new' ? 'new' : 'score';
  $('seasonTog').hidden = mixed(tab) || tab === 'all';
  // Only offer to hide old postings when the age limit in profile.toml lets some through
  $('hideOld').parentNode.hidden = mixed(tab) || !inThis.some(isOld);
  $('season').checked = !!seasonChk[tab];
  if(!mixed(tab) && T[tab]) $('seasonLabel').textContent = tab === 'fall' ? 'Include nearby postings that don\'t name a season' : `Only ones that say ${T[tab].season_label}`;
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
  const trOf = j => j.tracks[trackKey(j)] || j.tracks.all || best(j)[1];
  let jobs = pool.filter(j => {
    const tr = trOf(j);
    if(pick && !coMatch(j.company, pick.match)) return false;
    if(tier !== 'all' && tr.tier !== tier) return false;
    if(hide && (status[j.key] === 'applied' || status[j.key] === 'dismissed')) return false;
    if(hideOld && isOld(j)) return false;
    if(disc && j.discipline !== disc) return false;
    if(tab === 'fall' && !seasonOn && tr.season !== 'match') return false;
    if(tab !== 'fall' && tab !== 'all' && !mixed(tab) && seasonOn && tr.season !== 'match') return false;
    if(tab === 'all' && !allOk(j)) return false;
    if(q){
      const hay = [j.company, j.title, j.location, j.discipline, j.matched.join(' '), j.gaps.join(' ')].join(' ').toLowerCase();
      if(!q.split(/\s+/).every(w => hay.includes(w))) return false;
    }
    return true;
  });
  const sc = j => trOf(j).score;
  const mi = j => { const m = tab === 'all' ? (j.geo || {}).mi : (j.tracks.fall || {}).miles; return typeof m === 'number' ? m : 9999; };
  const s = $('sort').value;
  jobs.sort(s === 'found' ? (a,b) => foundKey(b).localeCompare(foundKey(a)) || sc(b) - sc(a)
         : s === 'new' ?(a,b) => ((b.posted || b.first_seen) + b.first_seen).localeCompare((a.posted || a.first_seen) + a.first_seen) || sc(b) - sc(a)
         : s === 'company' ? (a,b) => a.company.localeCompare(b.company) || sc(b) - sc(a)
         : s === 'reqs' ? (a,b) => reqPct(b) - reqPct(a) || sc(b) - sc(a)
         : s === 'near' ? (a,b) => mi(a) - mi(b) || sc(b) - sc(a)
         : (a,b) => sc(b) - sc(a));
  // Restrictions in force, so a short list never looks like "nothing out there"
  const chips = tab === 'all' ? afActive().map(([k, v]) => `<span class="chip">${esc(AFLABEL[k](v))}<button data-clear="${k}" aria-label="Remove filter">×</button></span>`) : [];
  if(tier !== 'all') chips.push(`<span class="chip">${esc(TIER[tier])}<button data-clear="tier" aria-label="Remove filter">×</button></span>`);
  if(disc) chips.push(`<span class="chip">${esc(disc)}<button data-clear="disc" aria-label="Remove filter">×</button></span>`);
  if(q) chips.push(`<span class="chip">“${esc(q)}”<button data-clear="q" aria-label="Clear search">×</button></span>`);
  $('shown').innerHTML = `<span>Showing ${Math.min(limit, jobs.length)} of ${jobs.length} matching / ${pool.length} in this section</span>` +
    (pick ? `<span class="pick">${esc(pick.name)}<button id="unpick" aria-label="Show all companies">×</button></span>` : '') + chips.join('') +
    (chips.length > 1 ? `<button class="reset" data-clear="all" type="button">Reset</button>` : '') + covNote();
  const emptyMsg = tab === 'undated' && !pool.length ? 'Every posting on the page has a posted date.'
    : tab === 'leads' && !pool.length ? 'No leads right now: every posting has a direct company link.'
    : tab === 'unread' && !pool.length ? 'Nothing unread: you\'ve reviewed everything found so far.'
    : tab === 'motor' && !pool.length ? T.motor.empty
    : tab === 'fall' && !pool.some(j => j.tracks.fall.season === 'match') ? T.fall.empty
    : tab === 'latest' && !pool.length ? `Nothing new found in the ${LATEST_HOURS / 24} days up to this update.`
    : 'No postings match these filters. Clear the search or reset the filters.';
  // In New internships and Unread, sorted by when found, each scan gets its own heading
  let html = '';
  if((tab === 'latest' || tab === 'unread') && s === 'found'){
    const shown = jobs.slice(0, limit), size = {};
    for(const j of jobs){ const g = foundGroup(j)[0]; size[g] = (size[g] || 0) + 1; }
    let last = null;
    for(const j of shown){
      const [g, label] = foundGroup(j);
      if(g !== last) html += `<h3 class="fgroup ${g === 'now' ? 'now' : ''}">${esc(label)}<span>${size[g]}</span></h3>`;
      last = g;
      html += card(j);
    }
  } else html = jobs.slice(0, limit).map(card).join('');
  // Never let a failed or partial scan read as "no internships available"
  const caveat = problemSources.length ? `<p style="margin-top:10px;font-size:13px">${problemSources.length} source${problemSources.length > 1 ? 's were' : ' was'} not fully read this update, so postings may be missing here. See “Sources this update” at the top.</p>` : '';
  $('list').innerHTML = jobs.length ? html : `<div class="empty">${esc(emptyMsg)}${caveat}</div>`;
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
$('newbtn').addEventListener('click', () => { pick = null; go('latest'); scrollTo({top: $('tabs').offsetTop - 8}); });
$('unreadbtn').addEventListener('click', () => { pick = null; go('unread'); scrollTo({top: $('tabs').offsetTop - 8}); });
$('markAll').addEventListener('click', () => { unread = {since: D.updated || new Date().toISOString(), read: unread.read, force: {}}; jset('ajf-unread', unread); tabs(); render(); });
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
$('shown').addEventListener('click', e => {
  if(e.target.id === 'unpick'){ pick = null; limit = PAGE; render(); return; }
  if(e.target.closest('[data-cov]')){ $('cov').open = true; $('cov').scrollIntoView({behavior: 'smooth'}); return; }
  const c = e.target.closest('[data-clear]'); if(!c) return;
  const k = c.dataset.clear;
  if(k === 'all'){ $('fReset').click(); return; }
  if(k === 'tier'){ tier = 'all'; document.querySelectorAll('.seg button[data-tier]').forEach(x => x.setAttribute('aria-pressed', x.dataset.tier === 'all')); }
  else if(k === 'disc') $('disc').value = '';
  else if(k === 'q') $('q').value = '';
  else { AF[k] = k === 'fElig' ? false : ''; setupAll(); }
  limit = PAGE; render();
});
// Only the fit buttons (the Predicted tab has its own button groups)
document.querySelectorAll('.seg button[data-tier]').forEach(b => b.addEventListener('click', () => {
  tier = b.dataset.tier;
  document.querySelectorAll('.seg button[data-tier]').forEach(x => x.setAttribute('aria-pressed', x === b));
  limit = PAGE;
  render();
}));
$('season').addEventListener('change', () => { seasonChk[tab] = $('season').checked; });
['q','disc','sort','season','hideOld','hideDone'].forEach(id => $(id).addEventListener(id === 'q' ? 'input' : 'change', () => { limit = PAGE; render(); }));
$('more').addEventListener('click', () => { limit += PAGE; render(); });
const byKey = new Map(D.jobs.map(j => [j.key, j]));
function onCard(e){
  const row = e.target.closest('.row');
  if(!row) return;
  const j = byKey.get(row.dataset.key);
  if(!j) return;
  if(e.target.closest('[data-open]')){ markRead(j.key); setTimeout(() => { tabs(); render(); }, 0); return; }  // opening it counts as reviewed
  const btn = e.target.closest('button[data-act]');
  if(!btn) return;
  if(btn.dataset.act === 'read'){
    if(isUnread(j)) markRead(j.key);
    else { delete unread.read[j.key]; unread.force[j.key] = D.today; jset('ajf-unread', unread); }
  } else setStatus(j, btn.dataset.act);
  tabs();
  if(tab === 'mine') renderMine(); else render();
}
$('list').addEventListener('click', onCard);
$('mineList').addEventListener('click', onCard);
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


def _page_job(j: dict) -> dict:
    out = {k: j.get(k) for k in (
        "key", "company", "title", "location", "url", "source", "posted", "posted_from", "date_kind", "first_seen",
        "tracks", "discipline", "matched", "related", "gaps", "flags", "ai", "quals", "has_description", "lead",
        "found_at", "terms", "uncertain", "misses", "geo", "stale", "aka", "checked")}
    # Keep the page light: drop empty fields, and for postings only in All opportunities,
    # the qualification-by-qualification lists beyond the summary (the scores stay)
    always = ("key", "company", "title", "location", "url", "source", "posted", "first_seen", "tracks", "matched",
              "related", "gaps", "flags")
    out = {k: ("" if v is None and k in always else v) for k, v in out.items()
           if v not in (None, [], {}, "") or k in always}
    if out.get("quals") and set(out["tracks"]) == {"all"}:
        out["quals"] = {"summary": out["quals"].get("summary"), "preferred": [], "required": []}
    return out


def build_page(jobs: list[dict], sources: list[dict], profile: dict, now: dt.datetime,
               popular: list[dict] | None = None, predicted: list[dict] | None = None,
               pred_info: dict | None = None, extras: dict | None = None) -> str:
    today = now.date().isoformat()
    page_jobs = [_page_job(j) for j in jobs]
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
        # Matches the found_at stamp run.py gives postings first found on this run
        "updated": now.isoformat(timespec="seconds"),
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
        **(extras or {}),
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
        "| Fit | Company | Role | Preferred quals | Required quals | Location | Posted | Apply |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for j in sorted(summer, key=lambda j: -j["tracks"]["summer"]["score"])[:top]:
        new = " 🆕" if j.get("first_seen") == today else ""
        loc = re.sub(r"\s+", " ", (j.get("location") or ""))[:40]
        title = (j["title"] or "").replace("|", "/")
        s = (j.get("quals") or {}).get("summary") or {}
        reqs = f"{s['required_met']:g} of {s['required_checked']}" if s.get("required_checked") else "–"
        prefs = f"{s['preferred_met']:g} of {s['preferred_total']}" if s.get("preferred_total") else "–"
        lines.append(f"| {j['tracks']['summer']['score']} | {j['company'].replace('|', '/')} | {title}{new} | {prefs} | {reqs} "
                     f"| {loc} | {j.get('posted') or 'unknown'} | [Apply]({j['url']}) |")
    if not summer:
        lines.append("| | No matches yet | Run the workflow from the Actions tab | | | | |")
    path.write_text(_replace_block(text, start, end, lines), encoding="utf-8")
