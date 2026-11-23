"""Build docs/index.html (your job page) and the table at the top of README.md.

Preview a template change without running a scan:

    python -m jobfinder.render            # re-renders docs/index.html's data into preview/index.html
"""
from __future__ import annotations

import datetime as dt
import json
import re
import sys
from pathlib import Path

TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Aero Job Finder</title>
<meta name="description" content="Engineering internships scored against a resume, refreshed every few hours.">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='6' fill='%231D5BC9'/%3E%3Cpath d='M8 23 16 7l8 16-8-4z' fill='%23fff'/%3E%3C/svg%3E">
<script>try{var t=localStorage.getItem('ajf-theme');document.documentElement.setAttribute('data-theme',t==='dark'||t==='auto'?t:'light')}catch(e){document.documentElement.setAttribute('data-theme','light')}</script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&display=swap" rel="stylesheet">
<style>
:root{
  --bg:#F4F5F7;--surface:#FFFFFF;--hover:#F0F2F5;--ink:#15181C;--ink2:#3B424A;--muted:#5E6771;--faint:#8D959E;
  --line:#E2E5E9;--line2:#CBD0D6;
  --accent:#1D5BC9;--accent-h:#174BA8;--on-accent:#FFFFFF;--accent-soft:#E9F0FB;--accent-line:#A8C0EC;
  --pos:#18794E;--warn:#975A00;--neg:#B3261E;--warn-soft:#FBF4E6;
  --shadow:0 10px 30px rgba(16,24,40,.14),0 2px 6px rgba(16,24,40,.08);
  --r:6px;--h:36px;
  --sans:"IBM Plex Sans",system-ui,-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
  color-scheme:light;
}
/* Dark is a soft slate, not black; the page opens in light unless dark or system is picked */
@media (prefers-color-scheme:dark){:root[data-theme=auto]{
  --bg:#181B20;--surface:#1F2329;--hover:#272C33;--ink:#E7E9EC;--ink2:#C4C9CF;--muted:#9BA3AD;--faint:#6F7782;
  --line:#2E333A;--line2:#424951;--accent:#86AEF9;--accent-h:#A6C3FB;--on-accent:#0D1626;--accent-soft:rgba(134,174,249,.14);--accent-line:rgba(134,174,249,.5);
  --pos:#5CC690;--warn:#E3AD55;--neg:#F28B82;--warn-soft:rgba(227,173,85,.1);
  --shadow:0 10px 30px rgba(0,0,0,.45),0 2px 6px rgba(0,0,0,.3);color-scheme:dark;
}}
:root[data-theme=dark]{
  --bg:#181B20;--surface:#1F2329;--hover:#272C33;--ink:#E7E9EC;--ink2:#C4C9CF;--muted:#9BA3AD;--faint:#6F7782;
  --line:#2E333A;--line2:#424951;--accent:#86AEF9;--accent-h:#A6C3FB;--on-accent:#0D1626;--accent-soft:rgba(134,174,249,.14);--accent-line:rgba(134,174,249,.5);
  --pos:#5CC690;--warn:#E3AD55;--neg:#F28B82;--warn-soft:rgba(227,173,85,.1);
  --shadow:0 10px 30px rgba(0,0,0,.45),0 2px 6px rgba(0,0,0,.3);color-scheme:dark;
}
*{box-sizing:border-box}
[hidden]{display:none!important}
html{-webkit-text-size-adjust:100%;scroll-padding-top:84px;scrollbar-gutter:stable}
html:has(dialog[open]){overflow:hidden}
body{margin:0;background:var(--bg);color:var(--ink);font:14px/1.45 var(--sans);-webkit-font-smoothing:antialiased;font-variant-numeric:tabular-nums}
a{color:var(--accent);text-underline-offset:2px}
button,input,select{font:inherit;color:inherit}
button{cursor:pointer}
svg{flex:none}
:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.sr{position:absolute!important;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0}
.wrap{max-width:1180px;margin:0 auto;padding:0 24px}
.muted{color:var(--muted)}
.small{font-size:13px}
.unk{font-style:italic;padding-right:2px}
.skip{position:absolute;left:12px;top:-60px;z-index:100;padding:8px 12px;border:1px solid var(--line2);border-radius:var(--r);background:var(--surface);color:var(--ink)}
.skip:focus{top:12px}

/* header */
.hdr{background:var(--surface);border-bottom:1px solid var(--line)}
.hbar{display:flex;align-items:center;gap:28px;min-height:52px}
.brand{display:inline-flex;align-items:center;gap:9px;color:var(--ink);font-weight:600;font-size:15px;text-decoration:none;white-space:nowrap}
.nav{display:flex;align-self:stretch;gap:2px;overflow-x:auto;scrollbar-width:none}
.nav::-webkit-scrollbar{display:none}
.nav a{display:inline-flex;align-items:center;gap:6px;padding:0 10px;margin-bottom:-1px;border-bottom:2px solid transparent;color:var(--ink2);font-weight:500;text-decoration:none;white-space:nowrap}
.nav a:hover{color:var(--ink);background:var(--hover)}
.nav a[aria-current=page]{color:var(--ink);border-bottom-color:var(--accent)}
.nav .n{font-weight:400;font-size:12.5px;color:var(--muted)}
.nsep{flex:none;width:1px;margin:16px 8px;background:var(--line2)}
.hend{margin-left:auto;display:flex;align-items:center;gap:4px}
.stat{display:inline-flex;align-items:center;gap:10px;height:34px;padding:0 10px;border:1px solid transparent;border-radius:var(--r);background:none;color:var(--muted);font-size:13px;white-space:nowrap}
.stat:hover{background:var(--hover);color:var(--ink)}
.stat .w{display:inline-flex;align-items:center;gap:5px;color:var(--warn);font-weight:500}
.stat .s{display:none}
.iconbtn{display:inline-flex;align-items:center;justify-content:center;width:36px;height:36px;padding:0;border:1px solid transparent;border-radius:var(--r);background:none;color:var(--ink2)}
.iconbtn:hover{background:var(--hover);color:var(--ink)}
.iconbtn.bd{border-color:var(--line2);background:var(--surface)}
.iconbtn.bd:hover{border-color:var(--faint)}
.iconbtn.sm{width:32px;height:32px}

/* page heading */
.phead{display:flex;flex-wrap:wrap;align-items:baseline;gap:2px 14px;padding:20px 0 6px}
.phead h1{margin:0;font-size:20px;line-height:1.3;font-weight:600;letter-spacing:-.01em}
.phead p{margin:0;color:var(--muted)}
.phead .tools{margin-left:auto;display:flex;flex-wrap:wrap;align-items:center;gap:8px}

/* tabs */
.tabs{display:flex;gap:22px;border-bottom:1px solid var(--line);overflow-x:auto;scrollbar-width:none}
.tabs::-webkit-scrollbar{display:none}
.tab{display:inline-flex;align-items:center;gap:7px;height:42px;padding:0 1px;margin-bottom:-1px;border:0;border-bottom:2px solid transparent;background:none;color:var(--muted);font-weight:500;white-space:nowrap}
.tab:hover{color:var(--ink)}
.tab[aria-selected=true]{color:var(--ink);border-bottom-color:var(--accent)}
.tab .n{font-size:12.5px;font-weight:400;color:var(--muted)}

/* toolbar and controls */
.toolbar{display:flex;flex-wrap:wrap;align-items:center;gap:8px;padding:12px 0 10px;background:var(--bg)}
.sticky{position:sticky;top:0;z-index:20}
.search{position:relative;flex:1 1 280px;min-width:200px}
.search>svg{position:absolute;left:11px;top:50%;margin-top:-8px;color:var(--muted);pointer-events:none}
.search input{width:100%;height:var(--h);padding:0 36px 0 34px;border:1px solid var(--line2);border-radius:var(--r);background:var(--surface);color:var(--ink)}
.search input::placeholder{color:var(--muted);opacity:1}
.search input:focus{outline:none;border-color:var(--accent);box-shadow:0 0 0 3px var(--accent-soft)}
.search kbd{position:absolute;right:9px;top:50%;margin-top:-10px;height:20px;padding:0 6px;border:1px solid var(--line2);border-radius:4px;font:12px/18px var(--sans);color:var(--muted);pointer-events:none}
.search input:focus~kbd,.search input:not(:placeholder-shown)~kbd{display:none}
.sel{height:var(--h);max-width:230px;padding:0 30px 0 10px;border:1px solid var(--line2);border-radius:var(--r);background-color:var(--surface);background-image:linear-gradient(45deg,transparent 50%,var(--muted) 50%),linear-gradient(135deg,var(--muted) 50%,transparent 50%);background-position:calc(100% - 15px) 50%,calc(100% - 10px) 50%;background-size:5px 5px;background-repeat:no-repeat;appearance:none;-webkit-appearance:none;color:var(--ink);text-overflow:ellipsis;cursor:pointer}
.sel:hover{border-color:var(--faint)}
.sel:focus{outline:none;border-color:var(--accent);box-shadow:0 0 0 3px var(--accent-soft)}
.sel.on{border-color:var(--accent-line);background-color:var(--accent-soft)}
.toolbar>.sel{flex:0 1 160px;min-width:118px;width:160px}
.toolbar>.sel[data-sort]{flex-basis:184px;width:184px;max-width:184px}
#toolbar .search{flex-basis:240px}
.btn{display:inline-flex;align-items:center;justify-content:center;gap:6px;height:var(--h);padding:0 13px;border:1px solid var(--line2);border-radius:var(--r);background:var(--surface);color:var(--ink);font-weight:500;line-height:1;text-decoration:none;white-space:nowrap}
.btn:hover{background:var(--hover);border-color:var(--faint)}
.btn.primary{background:var(--accent);border-color:var(--accent);color:var(--on-accent)}
.btn.primary:hover{background:var(--accent-h);border-color:var(--accent-h)}
.btn.sm{height:32px;padding:0 11px;font-size:13px}
.btn[aria-pressed=true]{background:var(--accent-soft);border-color:var(--accent-line);color:var(--accent)}
.btn .n{font-weight:400;color:var(--muted)}
.btn[aria-pressed=true] .n{color:inherit}
.badge{display:inline-block;min-width:18px;height:18px;padding:0 5px;border-radius:9px;background:var(--accent);color:var(--on-accent);font-size:11.5px;line-height:18px;font-weight:600;text-align:center}
.linkbtn{display:inline-flex;align-items:center;gap:5px;padding:4px 2px;border:0;background:none;color:var(--accent);font-weight:500;text-decoration:underline;text-decoration-thickness:1px;text-underline-offset:2px}
.linkbtn:hover{color:var(--accent-h)}
.cb{display:inline-flex;align-items:center;justify-content:center;width:14px;height:14px;border:1.5px solid currentColor;border-radius:3px}
.cb svg{display:none}
[aria-pressed=true]>.cb{background:currentColor}
[aria-pressed=true]>.cb svg{display:block;color:var(--surface)}
.m-only{display:none}

/* quick filters */
.presets{display:flex;flex-wrap:wrap;align-items:center;gap:6px;padding:0 0 12px}
.presets .lbl{margin-right:4px;color:var(--muted);font-size:13px}
.preset{display:inline-flex;align-items:center;gap:5px;height:30px;padding:0 11px;border:1px solid var(--line2);border-radius:var(--r);background:var(--surface);color:var(--ink2);font-size:13px;white-space:nowrap}
.preset:hover{border-color:var(--faint);color:var(--ink)}
.preset[aria-pressed=true]{background:var(--accent-soft);border-color:var(--accent-line);color:var(--accent);font-weight:500}
.preset svg{display:none}
.preset[aria-pressed=true] svg{display:block}

/* result header */
.rhead{display:flex;flex-wrap:wrap;align-items:center;gap:8px 10px;padding:10px 0;border-bottom:1px solid var(--line)}
.rcount{font-weight:600;color:var(--ink);margin-right:2px}
.rcount:focus{outline:none}
.rcount span{font-weight:400;color:var(--muted)}
.chip{display:inline-flex;align-items:center;max-width:100%;height:28px;padding:0 2px 0 10px;border:1px solid var(--line2);border-radius:var(--r);background:var(--surface);color:var(--ink2);font-size:13px}
.chip>span{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.chip button{display:inline-flex;align-items:center;justify-content:center;width:26px;height:26px;margin-left:2px;border:0;border-radius:4px;background:none;color:var(--muted)}
.chip button:hover{background:var(--hover);color:var(--ink)}
.rhead .end{margin-left:auto;display:flex;flex-wrap:wrap;align-items:center;gap:6px 10px}
.rnote{flex-basis:100%;margin:0;color:var(--muted);font-size:13px;max-width:100ch}

/* listings */
.list{list-style:none;margin:0;padding:0}
.job{display:grid;grid-template-columns:14px minmax(0,1fr) 136px auto;grid-template-areas:"dot t fit acts" ". meta fit acts" ". flags fit acts";column-gap:12px;row-gap:3px;align-items:center;padding:12px 10px 12px 2px;border-bottom:1px solid var(--line);cursor:pointer}
.job:hover{background:var(--hover)}
.job.cur{background:var(--accent-soft);box-shadow:inset 2px 0 0 var(--accent)}
.job>.dot{grid-area:dot;align-self:start;justify-self:center;width:8px;height:8px;margin-top:7px;border-radius:50%;background:var(--accent)}
.job .t{grid-area:t;justify-self:start;padding:0;border:0;background:none;color:var(--ink);font-size:15px;font-weight:600;line-height:1.35;text-align:left}
.job .t:hover{text-decoration:underline;text-underline-offset:2px}
.job .meta{grid-area:meta;display:flex;flex-wrap:wrap;min-width:0;color:var(--muted);font-size:13px}
.mg{display:inline-flex;flex-wrap:wrap;min-width:0;max-width:100%}
.mg>span,.meta>span{max-width:100%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.mg>span+span::before,.mg+.mg::before,.meta>span+span::before{content:"\00B7";margin:0 7px;color:var(--faint)}
.co{color:var(--ink2);font-weight:500}
.job .flags{grid-area:flags;display:flex;flex-wrap:wrap;gap:2px 14px;font-size:13px}
.job .fit{grid-area:fit}
.job .acts{grid-area:acts;display:flex;align-items:center;gap:6px}
.job.done .t{color:var(--muted)}
.concern{display:inline-flex;align-items:center;gap:5px;color:var(--warn);font-weight:500}
.note{display:inline-flex;align-items:center;gap:5px;color:var(--muted)}
.stl{display:inline-flex;align-items:center;gap:4px;color:var(--pos);font-weight:500}
.stl.dis{color:var(--muted)}
.fitl{display:inline-flex;align-items:center;gap:7px;color:var(--ink2);font-size:13px;white-space:nowrap}
.bars{display:inline-flex;align-items:flex-end;gap:2px;height:12px}
.bars i{display:block;width:3px;border-radius:1px;background:var(--line2)}
.bars i:nth-child(1){height:5px}.bars i:nth-child(2){height:8px}.bars i:nth-child(3){height:12px}
.f-strong .bars i{background:var(--pos)}
.f-good .bars i:nth-child(-n+2){background:var(--accent)}
.f-look .bars i:nth-child(1){background:var(--muted)}
.save svg path{fill:none}
.save[aria-pressed=true] svg path{fill:currentColor}
.grp{padding:18px 0 6px;border-bottom:1px solid var(--line)}
.grp h3{margin:0;font-size:13px;font-weight:600;color:var(--ink2)}
.grp h3 span{margin-left:6px;font-weight:400;color:var(--muted)}
.grp.now h3{color:var(--accent)}
.pager{display:flex;flex-direction:column;align-items:center;gap:10px;padding:20px 0 4px;color:var(--muted);font-size:13px}
.pager:empty{padding:0}
.empty,.loading{padding:44px 16px;text-align:center;color:var(--muted);border-bottom:1px solid var(--line);cursor:default}
.empty b{display:block;margin-bottom:4px;color:var(--ink);font-size:15px;font-weight:600}
.empty p{margin:4px auto;max-width:62ch}
.empty .btn{margin-top:12px}
.err{border:1px solid var(--line);border-radius:var(--r);margin-top:24px;background:var(--surface)}
.foot{padding-top:28px;padding-bottom:48px;color:var(--muted);font-size:13px}
.foot p{margin:0;max-width:100ch}

/* side sheets: job details, filters, data status, insights */
dialog.sheet{position:fixed;inset:0 0 0 auto;width:min(640px,100vw);max-width:100vw;height:100%;height:100dvh;max-height:100dvh;margin:0;padding:0;border:0;border-left:1px solid var(--line);background:var(--surface);color:var(--ink);box-shadow:var(--shadow)}
dialog.sheet.narrow{width:min(440px,100vw)}
dialog.sheet[open]{display:flex;flex-direction:column}
dialog::backdrop{background:rgba(17,22,28,.42)}
.sh{display:flex;align-items:center;gap:4px;min-height:52px;padding:8px 10px 8px 20px;border-bottom:1px solid var(--line)}
.sh h2{flex:1;margin:0;font-size:15px;font-weight:600}
.sh h2:focus{outline:none}
.sh .pos{flex:1;margin-left:6px;color:var(--muted);font-size:13px}
.sb{flex:1;overflow-y:auto;padding:20px 24px 32px;overscroll-behavior:contain}
.sf{display:flex;justify-content:flex-end;gap:8px;padding:12px 20px;border-top:1px solid var(--line)}
.d-co{margin:0;color:var(--ink2);font-weight:500}
.d-title{margin:4px 0 6px;font-size:21px;line-height:1.3;font-weight:600;letter-spacing:-.01em}
.d-title:focus{outline:none}
.d-meta{margin:0;color:var(--muted)}
.d-acts{display:flex;flex-wrap:wrap;gap:8px;margin:16px 0 0}
.d-state{margin:10px 0 0;color:var(--muted);font-size:13px}
.dsec{margin-top:22px;padding-top:18px;border-top:1px solid var(--line)}
.dsec h3{margin:0 0 10px;font-size:14px;font-weight:600}
.dsec h4{margin:14px 0 6px;font-size:13px;font-weight:600;color:var(--ink2)}
.dsec p{margin:0 0 8px}
.kv{display:grid;grid-template-columns:minmax(120px,180px) 1fr;gap:7px 16px;margin:0;font-size:13.5px}
.kv dt{color:var(--muted)}
.kv dd{margin:0;min-width:0;overflow-wrap:anywhere}
.bl{margin:0 0 8px;padding:0;list-style:none;display:grid;gap:8px;font-size:13.5px}
.bl>li{display:flex;gap:8px;align-items:flex-start}
.bl>li>svg,.bl>li>.qg{margin-top:2px}
.bl .ok>svg{color:var(--pos)}
.bl .cn>svg{color:var(--warn)}
.bl .no>svg{color:var(--neg)}
.bl ul{margin:4px 0 0;padding-left:18px}
.qg{display:inline-flex;justify-content:center;width:14px;font-weight:600;line-height:1}
.ql{list-style:none;margin:0;padding:0;display:grid;gap:9px;font-size:13.5px}
.ql li{display:grid;grid-template-columns:118px 1fr;gap:12px}
.qs{display:inline-flex;align-items:center;gap:5px;font-size:12.5px;font-weight:500;white-space:nowrap}
.q-met .qs{color:var(--pos)}.q-partial .qs{color:var(--warn)}.q-missing .qs{color:var(--neg)}.q-check .qs,.q-soft .qs{color:var(--muted)}
.ql small{display:block;margin-top:1px;color:var(--muted);font-size:12.5px}
.callout{display:flex;gap:10px;align-items:flex-start;margin:14px 0 0;padding:10px 12px;border:1px solid var(--line);border-left:3px solid var(--warn);border-radius:var(--r);background:var(--warn-soft);font-size:13.5px}
.callout.info{border-left-color:var(--accent);background:var(--accent-soft)}
.callout>svg{margin-top:2px;color:var(--warn)}
.callout.info>svg{color:var(--accent)}
.callout p{margin:0}
.callout b{font-weight:600}
.fgrid{display:grid;gap:18px}
.fld{display:grid;gap:5px}
.fld>span{font-weight:500;font-size:13.5px}
.fld .sel{width:100%;max-width:none}
.fld small{color:var(--muted);font-size:12.5px}
.fs-primary{display:grid;gap:18px;padding-bottom:18px;border-bottom:1px solid var(--line)}
.bar{display:grid;grid-template-columns:170px 1fr 40px;gap:10px;align-items:center;margin:6px 0;font-size:13.5px}
.bar i{display:block;height:6px;border-radius:3px;background:var(--line);overflow:hidden}
.bar i span{display:block;height:100%}
.bar em{font-style:normal;color:var(--muted);text-align:right}
.tbl{overflow-x:auto}
.tbl table{width:100%;border-collapse:collapse;font-size:13px}
.tbl th,.tbl td{padding:7px 10px 7px 0;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}
.tbl th{color:var(--muted);font-weight:500;font-size:12.5px}
.c-ok{color:var(--pos)}.c-partial{color:var(--warn)}.c-failed,.c-stale{color:var(--neg)}.c-off{color:var(--muted)}
.ds-sum{display:flex;flex-wrap:wrap;gap:6px 16px;margin:12px 0;padding:0;list-style:none;font-size:13.5px}
.ds-sum li{display:inline-flex;align-items:center;gap:5px}
.sb details{margin-top:16px}
.sb details>summary{cursor:pointer;font-weight:500}
.sb h3{margin:20px 0 8px;font-size:14px;font-weight:600}
.sb p{margin:6px 0}

/* menus and toast */
.menu{position:fixed;z-index:80;min-width:210px;max-width:calc(100vw - 16px);padding:4px;border:1px solid var(--line2);border-radius:8px;background:var(--surface);box-shadow:var(--shadow)}
.menu [role^=menuitem]{display:flex;align-items:center;gap:9px;width:100%;min-height:34px;padding:0 10px;border:0;border-radius:4px;background:none;color:var(--ink);text-align:left;font-size:13.5px;white-space:nowrap}
.menu [role^=menuitem]:hover,.menu [role^=menuitem]:focus{background:var(--hover);outline:none}
.menu [role^=menuitem]:focus-visible{outline:2px solid var(--accent);outline-offset:-2px}
.menu .rd{display:inline-flex;justify-content:center;width:14px}
.menu .rd svg{visibility:hidden}
.menu [aria-checked=true] .rd svg{visibility:visible}
.menu .mh{padding:8px 10px 4px;color:var(--muted);font-size:12px;font-weight:500}
.menu [role=separator]{height:1px;margin:4px 0;background:var(--line)}
.toast{position:fixed;left:50%;bottom:20px;z-index:90;transform:translateX(-50%);display:flex;align-items:center;gap:10px;max-width:calc(100vw - 32px);padding:8px 8px 8px 16px;border-radius:8px;background:var(--ink);color:var(--bg);box-shadow:var(--shadow);font-size:13.5px}
.toast .tb{height:30px;padding:0 12px;border:1px solid currentColor;border-radius:var(--r);background:none;color:inherit;font-weight:600}
.toast .x{display:inline-flex;align-items:center;justify-content:center;width:30px;height:30px;border:0;border-radius:var(--r);background:none;color:inherit}
.toast :focus-visible{outline-color:var(--bg)}

/* Outlook: programs, predicted roles, leads, big names */
.opane .callout{margin:16px 0 4px}
.item{display:grid;grid-template-columns:112px minmax(0,1fr) auto;gap:4px 18px;align-items:start;padding:14px 0;border-bottom:1px solid var(--line)}
.item .when b{display:block;font-size:15px;font-weight:600}
.item .when small{display:block;margin-top:2px;color:var(--muted);font-size:12.5px}
.item .t2{margin:0;font-size:15px;font-weight:600;line-height:1.35}
.item .meta{display:flex;flex-wrap:wrap;margin:3px 0 0;color:var(--muted);font-size:13px}
.item .sub{margin:5px 0 0;font-size:13px;color:var(--ink2)}
.item .sub.muted{color:var(--muted)}
.item .acts{display:flex;flex-direction:column;align-items:flex-end;gap:6px}
.item .flags{display:flex;flex-wrap:wrap;gap:2px 14px;margin-top:5px;font-size:13px}
.item details{margin-top:8px;font-size:13.5px}
.item details summary{cursor:pointer;color:var(--accent);font-weight:500}
.item details p,.item details ul{margin:8px 0 0}
.item q{color:var(--muted)}
.st-due .when b,.st-due .when small{color:var(--accent)}
.st-late .when b{color:var(--warn)}.st-posted .when b{color:var(--pos)}
.s-open .when b{color:var(--pos)}.s-closed .when b{color:var(--muted)}
.seg{display:inline-flex;border:1px solid var(--line2);border-radius:var(--r);overflow:hidden;background:var(--surface)}
.seg button{height:34px;padding:0 12px;border:0;background:none;color:var(--ink2);font-size:13px;font-weight:500;white-space:nowrap}
.seg button+button{border-left:1px solid var(--line2)}
.seg button:hover{background:var(--hover)}
.seg button[aria-pressed=true]{background:var(--accent-soft);color:var(--accent)}
.chk{display:inline-flex;align-items:center;gap:7px;min-height:32px;font-size:13.5px;color:var(--ink2);cursor:pointer}
.chk input{width:16px;height:16px;margin:0;accent-color:var(--accent)}
.ctlrow{display:flex;flex-wrap:wrap;gap:4px 18px;padding:0 0 10px}
.months{display:grid;grid-template-columns:repeat(9,minmax(0,1fr));gap:6px;margin:2px 0 12px}
.mo{display:flex;flex-direction:column;justify-content:flex-end;align-items:center;gap:4px;min-height:76px;padding:6px 4px;border:1px solid var(--line);border-radius:var(--r);background:var(--surface);color:var(--muted);font-size:12px}
.mo:hover{border-color:var(--faint)}
.mo[aria-pressed=true]{border-color:var(--accent);background:var(--accent-soft);color:var(--accent)}
.mo i{display:block;width:min(60%,26px);min-height:2px;border-radius:1px;background:var(--accent);opacity:.55}
.mo b{color:var(--ink);font-weight:600}
.bn-head,.bn{display:grid;grid-template-columns:minmax(160px,1.2fr) minmax(150px,1fr) minmax(220px,1.5fr) 140px;gap:6px 20px}
.bn-head{padding:14px 0 8px;border-bottom:1px solid var(--line);color:var(--muted);font-size:12.5px;font-weight:500}
.bn{padding:14px 0;border-bottom:1px solid var(--line);align-items:start;font-size:13.5px}
.bn-group{margin:22px 0 0;padding-bottom:6px;border-bottom:1px solid var(--line2);font-size:13px;font-weight:600;color:var(--ink2)}
.bn-group span{margin-left:6px;font-weight:400;color:var(--muted)}
.bn .nm{font-weight:600;font-size:14.5px}
.bn .nm a{display:block;margin-top:2px;font-weight:400;font-size:12.5px}
.bn small{display:block;margin-top:2px;color:var(--muted);font-size:12.5px}
.bn .hot{color:var(--accent);font-weight:500}
.bn .bad{color:var(--warn);font-weight:500}
.bn .go{padding:0;border:0;background:none;color:var(--accent);font-weight:600;text-align:left;text-decoration:underline;text-underline-offset:2px}
.bn .sub2{grid-column:1/-1;color:var(--muted);font-size:13px;max-width:90ch}
.bn .lbl{display:none}
.tl{display:grid;grid-template-columns:repeat(12,1fr);gap:2px}
.tl i{position:relative;height:10px;border-radius:1px;background:var(--line)}
.tl i.on{background:var(--accent);opacity:.7}
.tl i.now::after{content:"";position:absolute;left:50%;top:-4px;bottom:-4px;width:2px;margin-left:-1px;background:var(--ink)}
.tlm{display:grid;grid-template-columns:repeat(12,1fr);gap:2px;margin-top:4px;color:var(--faint);font-size:10.5px;text-align:center}
.tlm b{color:var(--ink)}
.win{margin-top:6px;color:var(--muted);font-size:12.5px}
.pub{margin-top:4px;font-size:12.5px;color:var(--ink2)}
.pub b{margin-right:6px;color:var(--pos);font-weight:600}
.h2s{margin:28px 0 4px;font-size:15px;font-weight:600}
.h2s span{margin-left:6px;font-weight:400;color:var(--muted)}
.hist{list-style:none;margin:8px 0 0;padding:0}
.hist li{display:grid;grid-template-columns:120px minmax(0,1fr) auto;gap:4px 16px;padding:10px 0;border-bottom:1px solid var(--line);font-size:13.5px}
.hist .when{color:var(--muted)}

@media (max-width:1000px){.stat .l{display:none}.stat .s{display:inline}.stat .l2{display:none}}
@media (max-width:760px){
  .wrap{padding:0 16px}
  .hbar{flex-wrap:wrap;gap:0 10px;min-height:0}
  .brand{height:48px}
  .stat{gap:6px;padding:0 6px}
  .stat .s .u{display:none}
  .job .mg{flex-basis:100%}
  .job .mg+.mg::before{content:none}
  .search input,.sel{font-size:16px}
  .nav{order:3;flex:1 0 100%;margin:0 -16px;padding:0 6px;border-top:1px solid var(--line)}
  .nav a{flex:1;justify-content:center;height:46px;padding:0 6px}
  .nav .n{display:none}
  .nsep{margin:15px 2px}
  .phead{padding:14px 0 4px}
  .phead h1{font-size:18px}
  .phead p{font-size:13px}
  .tb-f{display:none}
  .sticky{position:static}
  .search,#toolbar .search{flex-basis:100%}
  .toolbar>.sel,.toolbar>.sel[data-sort]{flex:1 1 0;width:auto;min-width:0;max-width:none}
  .tabs{gap:18px}
  .d-only{display:none}.m-only{display:inline}
  .presets{flex-wrap:nowrap;overflow-x:auto;margin:0 -16px;padding:0 16px 12px;scrollbar-width:none}
  .presets::-webkit-scrollbar{display:none}
  .presets .lbl{display:none}
  .job{grid-template-columns:12px minmax(0,1fr) auto;grid-template-areas:"dot t t" ". meta meta" ". flags flags" ". fit acts";row-gap:4px;padding:14px 2px 14px 0}
  .job .acts{justify-self:end;margin-top:4px}
  .job .fit{margin-top:4px}
  .save .lbl{display:none}
  .job .btn.sm{height:40px;padding:0 14px}
  .job .save.btn.sm{width:40px;padding:0}
  .job .iconbtn.sm{width:40px;height:40px}
  .rhead .end{margin-left:0}
  .kv{grid-template-columns:1fr;gap:2px}
  .kv dd{margin-bottom:8px}
  .ql li{grid-template-columns:1fr;gap:2px}
  .sb{padding:16px 16px 28px}
  .sh{padding-left:16px}
  .item{grid-template-columns:86px minmax(0,1fr)}
  .item .acts{grid-column:1/-1;flex-direction:row;flex-wrap:wrap;align-items:center;margin-top:8px}
  .months{grid-template-columns:repeat(5,minmax(0,1fr))}
  .months .mo:nth-child(n+6){display:none}
  .bn-head{display:none}
  .bn{grid-template-columns:1fr 1fr;gap:10px 14px}
  .bn .tlw{grid-column:1/-1}
  .bn .lbl{display:inline;color:var(--muted)}
  .bar{grid-template-columns:120px 1fr 36px}
  .hist li{grid-template-columns:1fr}
  .toast{bottom:12px}
}
@media (pointer:coarse){.btn,.sel,.search input,.seg button{min-height:40px}.preset{height:36px}.chip{height:34px}.chip button{width:32px;height:32px}}
</style>
</head>
<body>
<a class="skip" href="#results">Skip to results</a>
<header class="hdr">
  <div class="wrap hbar">
    <a class="brand" href="#for-you" id="brand"><svg width="18" height="18" viewBox="0 0 32 32" aria-hidden="true"><path d="M5 27 16 4l11 23-11-5.5z" fill="var(--accent)"/></svg><span>Aero Job Finder</span></a>
    <nav class="nav" aria-label="Main" id="nav">
      <a href="#for-you" data-sec="browse" id="navBrowse">Browse</a>
      <a href="#saved" data-sec="saved">Saved<span class="n" id="nSaved"></span></a>
      <a href="#applied" data-sec="applied">Applied<span class="n" id="nApplied"></span></a>
      <span class="nsep" aria-hidden="true"></span>
      <a href="#programs" data-sec="outlook" id="navOut" title="Programs, predicted roles, unverified leads and recruiting windows: not confirmed job postings">Outlook</a>
    </nav>
    <div class="hend">
      <button class="stat" type="button" id="statBtn" aria-haspopup="dialog"></button>
      <button class="iconbtn" type="button" id="setBtn" aria-haspopup="menu" aria-expanded="false" aria-controls="setMenu" aria-label="Settings" title="Settings"><svg width="18" height="18" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><circle cx="10" cy="10" r="2.6"/><path d="M10 1.8v2.4M10 15.8v2.4M1.8 10h2.4M15.8 10h2.4M4.2 4.2l1.7 1.7M14.1 14.1l1.7 1.7M4.2 15.8l1.7-1.7M14.1 5.9l1.7-1.7" stroke-linecap="round"/><circle cx="10" cy="10" r="5.6"/></svg></button>
    </div>
  </div>
</header>
<noscript><div class="wrap"><p class="empty">This page needs JavaScript to list and filter internships.</p></div></noscript>

<main id="main">
<section id="browseView" class="wrap" aria-labelledby="browseH">
  <div class="phead"><h1 id="browseH">Internships</h1><p id="browseSub"></p></div>
  <div class="tabs" role="tablist" aria-label="Views" id="viewTabs"></div>
  <div role="tabpanel" id="viewPanel" aria-labelledby="tab-foryou">
    <div class="toolbar sticky" id="toolbar">
      <div class="search"><svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true"><circle cx="7" cy="7" r="4.6"/><path d="m10.4 10.4 3.4 3.4" stroke-linecap="round"/></svg><input type="search" id="q" placeholder="Search roles, companies, or skills" aria-label="Search roles, companies, or skills" autocomplete="off" spellcheck="false"><kbd aria-hidden="true">/</kbd></div>
      <select class="sel tb-f" data-f="term" aria-label="Term"></select>
      <select class="sel tb-f" data-f="loc" aria-label="Location"></select>
      <select class="sel tb-f" data-f="field" aria-label="Field"></select>
      <select class="sel" data-sort aria-label="Sort"></select>
      <button class="btn" type="button" id="moreBtn" aria-haspopup="dialog"><svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" aria-hidden="true"><path d="M2 4.5h6M11 4.5h3M2 11.5h2M7 11.5h7"/><circle cx="9.5" cy="4.5" r="1.6"/><circle cx="5.5" cy="11.5" r="1.6"/></svg><span class="d-only">More filters</span><span class="m-only">Filters</span><span class="badge d-only" id="moreN" hidden></span><span class="badge m-only" id="allN" hidden></span></button>
    </div>
    <div class="presets" role="group" aria-labelledby="presetsL" id="presets"></div>
    <div class="rhead" id="rhead"></div>
    <ul class="list" id="results" data-ctx="browse" aria-label="Results" tabindex="-1"><li class="loading">Loading internships…</li></ul>
    <div class="pager" id="pager"></div>
  </div>
</section>

<section id="mineView" class="wrap" aria-labelledby="mineH" hidden>
  <div class="phead"><h1 id="mineH">Saved</h1><p id="mineSub"></p>
    <div class="tools"><span class="small muted">Stored in this browser only.</span><button class="btn sm" type="button" data-m="export">Export</button><button class="btn sm" type="button" data-m="import">Import</button></div>
  </div>
  <ul class="list" id="mineList" data-ctx="mine" aria-labelledby="mineH"></ul>
  <div id="mineGone"></div>
</section>

<section id="outView" class="wrap" aria-labelledby="outH" hidden>
  <div class="phead"><h1 id="outH">Outlook</h1><p>Programs, forecasts and leads, kept apart from Browse because none of them is a confirmed job posting.</p></div>
  <div class="tabs" role="tablist" aria-label="Outlook sections" id="outTabs"></div>
  <div class="opane" role="tabpanel" id="pane-programs" aria-labelledby="otab-programs" hidden>
    <div class="callout info" id="note-programs"></div>
    <ul class="list" id="progList"></ul>
  </div>
  <div class="opane" role="tabpanel" id="pane-predicted" aria-labelledby="otab-predicted" hidden>
    <div class="callout info" id="note-predicted"></div>
    <div class="toolbar">
      <div class="search"><svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true"><circle cx="7" cy="7" r="4.6"/><path d="m10.4 10.4 3.4 3.4" stroke-linecap="round"/></svg><input type="search" id="pq" placeholder="Search company, role, location" aria-label="Search predicted roles" autocomplete="off"></div>
      <select class="sel" id="pdisc" aria-label="Field"></select>
      <div class="seg" role="group" aria-label="Term" id="pseason"></div>
      <div class="seg" role="group" aria-label="Status" id="pstat">
        <button type="button" data-st="soon" aria-pressed="true">Coming up</button><button type="button" data-st="late" aria-pressed="false">Not seen yet</button><button type="button" data-st="posted" aria-pressed="false">Already posted</button><button type="button" data-st="all" aria-pressed="false">All</button>
      </div>
    </div>
    <div class="ctlrow"><label class="chk"><input type="checkbox" id="paero"> Aerospace and motorsport companies only</label><label class="chk" id="pnearTog"><input type="checkbox" id="pnear"> <span id="pnearLabel"></span></label></div>
    <div class="months" id="pmonths" role="group" aria-label="Expected postings by month"></div>
    <div class="rhead" id="pshown" aria-live="polite"></div>
    <ul class="list" id="plist"></ul>
    <div class="pager" id="ppager"></div>
  </div>
  <div class="opane" role="tabpanel" id="pane-leads" aria-labelledby="otab-leads" hidden>
    <div class="callout" id="note-leads"></div>
    <div class="toolbar">
      <div class="search"><svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true"><circle cx="7" cy="7" r="4.6"/><path d="m10.4 10.4 3.4 3.4" stroke-linecap="round"/></svg><input type="search" id="lq" placeholder="Search roles, companies, or skills" aria-label="Search leads" autocomplete="off"></div>
      <select class="sel" id="lsort" aria-label="Sort leads"><option value="score">Sort: Best match</option><option value="found">Sort: Recently added</option><option value="company">Sort: Company A–Z</option></select>
    </div>
    <div class="rhead" id="lhead"></div>
    <ul class="list" id="leadList" data-ctx="leads" aria-label="Leads"></ul>
    <div class="pager" id="lpager"></div>
  </div>
  <div class="opane" role="tabpanel" id="pane-big" aria-labelledby="otab-big" hidden>
    <div class="callout info" id="note-big"></div>
    <div class="bn-head" aria-hidden="true"><span>Company</span><span>This cycle</span><span>Typical window, Jul to Jun</span><span>Earliest posting</span></div>
    <div id="bigList"></div>
  </div>
</section>
</main>
<footer class="wrap foot"><p id="foot"></p></footer>

<dialog class="sheet" id="detail" aria-labelledby="dTitle">
  <div class="sh">
    <button class="iconbtn" type="button" data-nav="-1" aria-label="Previous listing" title="Previous (K)"><svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M10 3 5 8l5 5"/></svg></button>
    <button class="iconbtn" type="button" data-nav="1" aria-label="Next listing" title="Next (J)"><svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m6 3 5 5-5 5"/></svg></button>
    <span class="pos" id="dPos"></span>
    <button class="iconbtn" type="button" data-close aria-label="Close details" title="Close (Esc)"><svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" aria-hidden="true"><path d="m4 4 8 8M12 4l-8 8"/></svg></button>
  </div>
  <div class="sb" id="dBody"></div>
</dialog>

<dialog class="sheet narrow" id="filtDlg" aria-labelledby="filtH">
  <div class="sh"><h2 id="filtH" tabindex="-1">Filters</h2><button class="iconbtn" type="button" data-close aria-label="Close filters"><svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" aria-hidden="true"><path d="m4 4 8 8M12 4l-8 8"/></svg></button></div>
  <div class="sb">
    <div class="fgrid">
      <div class="fs-primary" id="fsPrimary">
        <label class="fld"><span>Term</span><select class="sel" data-f="term"></select></label>
        <label class="fld"><span>Location</span><select class="sel" data-f="loc"></select></label>
        <label class="fld"><span>Field</span><select class="sel" data-f="field"></select></label>
      </div>
      <label class="fld"><span>Match level</span><select class="sel" data-f="fit"></select><small>An estimate from your resume. Eligibility is filtered separately below.</small></label>
      <label class="fld"><span>Posting date</span><select class="sel" data-f="posted"></select><small>The employer's date, or an internship list's date when the employer gives none. Never the day the scanner found it.</small></label>
      <label class="fld"><span>Added by the scanner</span><select class="sel" data-f="added"></select><small>When the scan first found the listing. This isn't a posting date.</small></label>
      <label class="fld"><span>Education level</span><select class="sel" data-f="edu"></select></label>
      <label class="fld"><span>Eligibility</span><select class="sel" data-f="elig"></select><small>Graduation window, class year, GPA and graduate-only checks from the description.</small></label>
      <label class="fld"><span>Remote</span><select class="sel" data-f="remote"></select></label>
      <label class="fld"><span>Data quality</span><select class="sel" data-f="unc"></select><small>Listings with details the scan couldn't settle, such as a field inferred from the majors listed.</small></label>
      <label class="fld"><span>Applied and dismissed</span><select class="sel" data-f="show"></select></label>
    </div>
  </div>
  <div class="sf"><button class="btn" type="button" data-clear="all">Clear all</button><button class="btn primary" type="button" data-close id="filtShow">Show results</button></div>
</dialog>

<dialog class="sheet" id="dsDlg" aria-labelledby="dsH">
  <div class="sh"><h2 id="dsH" tabindex="-1">Data status</h2><button class="iconbtn" type="button" data-close aria-label="Close data status"><svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" aria-hidden="true"><path d="m4 4 8 8M12 4l-8 8"/></svg></button></div>
  <div class="sb" id="dsBody"></div>
</dialog>

<dialog class="sheet narrow" id="insDlg" aria-labelledby="insH">
  <div class="sh"><h2 id="insH" tabindex="-1">Skill insights</h2><button class="iconbtn" type="button" data-close aria-label="Close skill insights"><svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" aria-hidden="true"><path d="m4 4 8 8M12 4l-8 8"/></svg></button></div>
  <div class="sb" id="insBody"></div>
</dialog>

<div class="menu" id="setMenu" role="menu" aria-label="Settings" hidden></div>
<div class="menu" id="rowMenu" role="menu" hidden></div>
<div class="toast" id="toast" hidden></div>
<div class="sr" id="live" role="status" aria-live="polite"></div>
<input type="file" id="importFile" accept="application/json,.json" hidden>

<script id="data" type="application/json">__DATA__</script>
<script>
(function(){
'use strict';
const $ = id => document.getElementById(id);
const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function fatal(err){
  const m = $('main');
  if(m) m.innerHTML = `<div class="wrap"><div class="empty err" role="alert"><b>The internship list couldn't be displayed.</b><p>${esc(err && err.message || err)}</p><p>Try reloading the page. Saved and applied jobs are stored in this browser and aren't affected.</p></div></div>`;
}
let D;
try { D = JSON.parse($('data').textContent); } catch(e){ fatal(e); return; }
try { boot(); } catch(e){ console.error(e); fatal(e); }

function boot(){
const PAGE = 60;
const nf = n => Number(n || 0).toLocaleString();
const plural = (n, one, many) => `${nf(n)} ${n === 1 ? one : (many || one + 's')}`;
const jget = (k, d) => { try { const v = JSON.parse(localStorage.getItem(k) || 'null'); return v === null ? d : v; } catch(e){ return d; } };
const jset = (k, v) => { try { localStorage.setItem(k, JSON.stringify(v)); } catch(e){} };
const sget = k => { try { return localStorage.getItem(k); } catch(e){ return null; } };
const sset = (k, v) => { try { localStorage.setItem(k, v); } catch(e){} };
const ICON = {
  star: '<svg width="15" height="15" viewBox="0 0 16 16" stroke="currentColor" stroke-width="1.4" aria-hidden="true"><path d="M8 1.9l1.85 3.86 4.25.58-3.1 2.95.77 4.21L8 11.46 4.23 13.5 5 9.29 1.9 6.34l4.25-.58z" stroke-linejoin="round"/></svg>',
  dots: '<svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true"><circle cx="3.5" cy="8" r="1.4"/><circle cx="8" cy="8" r="1.4"/><circle cx="12.5" cy="8" r="1.4"/></svg>',
  ext: '<svg width="12" height="12" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M9 3h4v4M13 3 7.5 8.5M12 9.5V13H3V4h3.5"/></svg>',
  warn: '<svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linejoin="round" aria-hidden="true"><path d="M8 2.2 1.6 13.4h12.8z"/><path d="M8 6.6v3.1M8 11.5v.2" stroke-linecap="round"/></svg>',
  check: '<svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m3 8.5 3.2 3.2L13 4.8"/></svg>',
  x: '<svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" aria-hidden="true"><path d="m4 4 8 8M12 4l-8 8"/></svg>',
  info: '<svg width="15" height="15" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><circle cx="8" cy="8" r="6.2"/><path d="M8 7.2v4M8 4.8v.2" stroke-linecap="round"/></svg>',
};
const CB = `<span class="cb" aria-hidden="true">${ICON.check}</span>`;

// ---------- dates (same rules as before)
const MON = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
const fmt = iso => { if(!iso) return ''; const d = new Date(iso + 'T12:00:00'); return d.toLocaleDateString(undefined, {month:'short', day:'numeric'}); };
const fmtY = iso => { if(!iso) return ''; const d = new Date(iso + 'T12:00:00'); return d.toLocaleDateString(undefined, {month:'short', day:'numeric', year:'numeric'}); };
const fmtT = iso => iso ? new Date(iso).toLocaleString(undefined, {month:'short', day:'numeric', hour:'numeric', minute:'2-digit'}) : 'never';
for(const j of D.jobs){
  if(j.posted && !/^\d{4}-\d{2}-\d{2}$/.test(j.posted)) j.posted = '';
  for(const k of ['matched', 'related', 'gaps', 'flags']) if(!Array.isArray(j[k])) j[k] = [];
}
const todayMs = Date.parse(D.today + 'T12:00:00');
const daysBack = n => new Date(todayMs - n * 864e5).toISOString().slice(0, 10);
const weekAgo = daysBack(7), oldCut = daysBack(D.old_after);
const ageDays = iso => iso ? Math.round((todayMs - Date.parse(iso + 'T12:00:00')) / 864e5) : null;
const postedThisWeek = j => !!j.posted && j.posted >= weekAgo;
const isOld = j => !!j.posted && j.posted < oldCut;
const updMs = Date.parse(D.updated || (D.today + 'T12:00:00Z'));
const LATEST_HOURS = 72;
const foundKey = j => j.found_at || (j.first_seen ? j.first_seen + 'T00:00:00+00:00' : '');
const foundMs = j => j.found_at ? Date.parse(j.found_at) : j.first_seen ? Date.parse(j.first_seen + 'T12:00:00') : NaN;
const inThisUpdate = j => !!j.found_at && j.found_at === D.updated;
const clock = ms => new Date(ms).toLocaleTimeString(undefined, {hour:'numeric', minute:'2-digit'});
const dayDiff = ms => { const a = new Date(updMs), b = new Date(ms);
  return Math.round((new Date(a.getFullYear(), a.getMonth(), a.getDate()) - new Date(b.getFullYear(), b.getMonth(), b.getDate())) / 864e5); };
const ago = d => d == null || isNaN(d) ? '' : d <= 0 ? 'today' : d === 1 ? 'yesterday' : `${d} days ago`;
// One heading per scan when sorted by Recently added: "This update", "Earlier today", "Yesterday"...
const foundGroup = j => {
  if(inThisUpdate(j)) return ['now', `Added in this update · ${clock(updMs)}`];
  if(!j.found_at) return ['d' + j.first_seen, `Added ${fmt(j.first_seen)} · time not recorded`];
  const ms = Date.parse(j.found_at), dd = dayDiff(ms);
  const day = dd === 0 ? 'Earlier today' : dd === 1 ? 'Yesterday' : new Date(ms).toLocaleDateString(undefined, {weekday:'long', month:'short', day:'numeric'});
  return [j.found_at, `${day} · ${clock(ms)} scan`];
};
// Where a posting's date came from (older saved results only know posted/posted_from)
const dateKind = j => j.date_kind || (j.posted ? (j.posted_from ? 'listing' : 'employer') : 'none');

// ---------- per-browser state: same storage keys as before, so saved, applied, dismissed and read marks carry over
let status = jget('ajf-status', {});
if(!status || typeof status !== 'object' || Array.isArray(status)) status = {};
let activity = jget('ajf-activity', {});   // key -> {s: status, at, c, t, u} for the history lists
if(!activity || typeof activity !== 'object') activity = {};
let unread = jget('ajf-unread', null);     // {since: ISO time, read: {key: date reviewed}, force: {key: date}}
// The unread queue: everything found since the queue started stays unread until it's reviewed
// (details opened, Apply clicked or marked read), saved, applied to or dismissed.
if(!unread || !unread.since) unread = {since: new Date(updMs - LATEST_HOURS * 36e5).toISOString(), read: {}};
unread.read = unread.read || {};
unread.force = unread.force || {};
{ // forget review marks after 45 days, and carry state over from a posting's old link
  const cut = daysBack(45);
  for(const k in unread.read) if(unread.read[k] < cut) delete unread.read[k];
  for(const k in unread.force) if(unread.force[k] < cut) delete unread.force[k];
  for(const j of D.jobs) for(const a of (j.aka || [])){
    if(status[a] && !status[j.key]) status[j.key] = status[a];
    if(unread.read[a] && !unread.read[j.key]) unread.read[j.key] = unread.read[a];
    if(activity[a] && !activity[j.key]) activity[j.key] = activity[a];
  }
  jset('ajf-status', status); jset('ajf-unread', unread); jset('ajf-activity', activity);
}
const sinceMs = () => Date.parse(unread.since);
const isUnread = j => !status[j.key] && !unread.read[j.key] && (!!unread.force[j.key] || foundMs(j) > sinceMs());
const markRead = key => { delete unread.force[key]; if(!unread.read[key]) unread.read[key] = D.today; jset('ajf-unread', unread); };
const markUnread = key => { delete unread.read[key]; unread.force[key] = D.today; jset('ajf-unread', unread); };
function setStatus(j, s){
  status[j.key] = status[j.key] === s ? undefined : s;
  if(!status[j.key]){ delete status[j.key]; delete activity[j.key]; }
  else activity[j.key] = {s: status[j.key], at: D.today, c: j.company, t: j.title, u: j.url};
  jset('ajf-status', status); jset('ajf-activity', activity);
}
function change(j, s){
  const prev = {key: j.key, st: status[j.key], act: activity[j.key] ? Object.assign({}, activity[j.key]) : undefined};
  setStatus(j, s);
  return prev;
}
function undo(prev){
  if(prev.st) status[prev.key] = prev.st; else delete status[prev.key];
  if(prev.act) activity[prev.key] = prev.act; else delete activity[prev.key];
  jset('ajf-status', status); jset('ajf-activity', activity);
  refresh();
  say('Undone.');
}

// ---------- theme: light unless dark (or the system setting) is picked
const THEMES = {light:'Light', dark:'Dark', auto:'Match system'};
let theme = THEMES[sget('ajf-theme')] ? sget('ajf-theme') : 'light';
const applyTheme = () => document.documentElement.setAttribute('data-theme', theme);
applyTheme();

// ---------- sections, views and presets
const T = D.tracks || {};
const BIG = D.popular || [];
const PROGS = D.programs || [];
const P = D.predicted || [];
const HOME = T.fall ? T.fall.home : '';
const coMatch = (company, terms) => { const c = (company || '').toLowerCase(); return terms.some(t => t[0] === '=' ? c === t.slice(1) : c.includes(t)); };
const byKey = new Map(D.jobs.map(j => [j.key, j]));
// The best curated section for a posting ("all" only when it's in none of them)
const best = j => j._best || (j._best = (() => { const e = Object.entries(j.tracks), c = e.filter(([k]) => k !== 'all');
  return (c.length ? c : e).reduce((a, b) => !a || b[1].score > a[1].score ? b : a, null); })());
for(const j of D.jobs) j._big = BIG.some(p => coMatch(j.company, p.match || []));
const TIERL = {strong:'Strong match', good:'Good match', look:'Possible match'};
const gone = j => status[j.key] === 'applied' || status[j.key] === 'dismissed';
const forYou = j => !!(j.tracks.summer || j.tracks.motor || j.tracks.fall || (j.tracks.broad && j.tracks.broad.tier !== 'look'));
const VIEWS = {
  foryou: {name:'For you', test: j => !j.lead && forYou(j), sort:'score', what:'matched to your profile',
    title:'Summer 2027 aerospace, motorsport and Fall near-home listings, plus strong and good engineering matches'},
  new: {name:'New this week', test: j => !j.lead && postedThisWeek(j), sort:'new', what:'posted in the last 7 days',
    title:'Posting date (from the employer or an internship list) in the last 7 days'},
  all: {name:'All opportunities', short:'All', test: j => !j.lead && !!j.tracks.all, sort:'score', what:'',
    title:`Every engineering internship and student program found in the last ${D.max_age} days, at any score`},
};
const POOL = {}; for(const v in VIEWS) POOL[v] = D.jobs.filter(VIEWS[v].test);
const LEADS = D.jobs.filter(j => j.lead);
const PRESETS = [
  T.summer && {id:'summer', name:T.summer.tab, track:'summer', desc:T.summer.note},
  T.motor && {id:'motor', name:T.motor.tab, track:'motor', desc:T.motor.note},
  T.fall && {id:'fall', name:T.fall.tab, track:'fall', term:T.fall.season_label, desc:T.fall.note},
  T.broad && {id:'broad', name:'Engineering', track:'broad', desc:T.broad.note},
  BIG.length && {id:'big', name:'Big-name companies', desc:'Listings from the well-known aerospace and defense employers tracked under Outlook, Big-name timing.'},
].filter(Boolean);
const PRESET_BY = Object.fromEntries(PRESETS.map(p => [p.id, p]));
const SORTS = {score:'Best match', reqs:'Most qualifications met', new:'Recently posted', found:'Recently added', near: HOME ? `Closest to ${HOME}` : '', company:'Company A–Z'};
const F0 = {q:'', preset:'', company:'', term:'', loc:'', field:'', fit:'', posted:'', added:'', edu:'', elig:'', remote:'', unc:'', show:''};
const MORE_KEYS = ['fit', 'posted', 'added', 'edu', 'elig', 'remote', 'unc', 'show'];
const OPTS = {
  fit: [['', 'Any match level'], ['strong', 'Strong match'], ['good+', 'Strong or good match'], ['good', 'Good match'], ['look', 'Possible match']],
  posted: [['', 'Any posting date'], ['3', 'Posted in the last 3 days'], ['7', 'Posted in the last 7 days'], ['known', 'Posting date known'], ['unknown', 'Posting date unknown']]
    .concat(D.jobs.some(isOld) ? [['recent', `Hide postings older than ${D.old_after} days`]] : []),
  added: [['', 'Any time'], ['update', 'In the latest update'], ['1', 'In the last 24 hours'], ['3', 'In the last 3 days'], ['7', 'In the last 7 days']],
  edu: [['', 'Any level'], ['under', 'Open to underclassmen'], ['nograd', 'Not graduate-only']],
  elig: [['', 'Show all'], ['ok', 'Hide possible eligibility concerns'], ['concern', 'Only listings with concerns']],
  remote: [['', 'Include remote'], ['no', 'Exclude remote-only']],
  unc: [['', 'Include uncertain details'], ['hide', 'Hide uncertain details'], ['only', 'Only uncertain details']],
  show: [['', 'Hide applied and dismissed'], ['all', 'Show everything'], ['dismissed', 'Dismissed only']],
};
const optLabel = (k, v) => (OPTS[k].find(o => o[0] === v) || [, v])[1];

let ui = {section:'browse', view:'foryou', out:'programs', f:Object.assign({}, F0), sort:{}, unreadOnly:false};
const OUTS = ['programs', 'predicted', 'leads', 'big'];
const VIEW_HASH = {foryou:'for-you', new:'new', all:'all-opportunities'};
const OUT_HASH = {programs:'programs', predicted:'predicted', leads:'leads', big:'big-names'};
// Links from the old page (README, digest, bookmarks) still land somewhere sensible
const LEGACY = {
  'summer': {view:'foryou', preset:'summer'}, 'motorsports': {view:'foryou', preset:'motor'}, 'fall': {view:'foryou', preset:'fall'},
  'all': {view:'all', preset:'broad'}, 'new-internships': {view:'all', added:'3', sort:'found'},
  'unread': {view:'all', unreadOnly:true, sort:'found'}, 'date-unknown': {view:'all', posted:'unknown'}, 'my-list': {section:'saved'},
};
function applyPreset(id){
  const old = PRESET_BY[ui.f.preset];
  if(old && old.term && ui.f.term === old.term) ui.f.term = '';
  ui.f.preset = PRESET_BY[id] ? id : '';
  const p = PRESET_BY[ui.f.preset];
  if(p && p.term) ui.f.term = p.term;
}
function route(h){
  h = (h || '').replace(/^#/, '');
  for(const v in VIEW_HASH) if(VIEW_HASH[v] === h){ ui.section = 'browse'; ui.view = v; return true; }
  for(const o in OUT_HASH) if(OUT_HASH[o] === h){ ui.section = 'outlook'; ui.out = o; return true; }
  if(h === 'saved' || h === 'applied'){ ui.section = h; return true; }
  const L = LEGACY[h];
  if(!L) return false;
  if(L.section){ ui.section = L.section; return true; }
  ui.section = 'browse'; ui.view = L.view; ui.f = Object.assign({}, F0); ui.unreadOnly = !!L.unreadOnly;
  if(L.preset) applyPreset(L.preset);
  if(L.added) ui.f.added = L.added;
  if(L.posted) ui.f.posted = L.posted;
  if(L.sort) ui.sort[L.view] = L.sort;
  return true;
}
(function loadUI(){
  const s = jget('ajf-ui', null);
  if(s && typeof s === 'object'){
    if(['browse', 'saved', 'applied', 'outlook'].includes(s.section)) ui.section = s.section;
    if(VIEWS[s.view]) ui.view = s.view;
    if(OUTS.includes(s.out)) ui.out = s.out;
    if(s.f && typeof s.f === 'object') for(const k in F0) if(typeof s.f[k] === 'string') ui.f[k] = s.f[k];
    if(ui.f.preset && !PRESET_BY[ui.f.preset]) ui.f.preset = '';
    if(s.sort && typeof s.sort === 'object') for(const v in VIEWS) if(SORTS[s.sort[v]]) ui.sort[v] = s.sort[v];
    ui.unreadOnly = !!s.unreadOnly;
  } else {
    // First visit after the redesign: open the old page's last tab as the matching view or preset
    const OLD = {summer:'summer', motor:'motorsports', fall:'fall', broad:'all', all:'all-opportunities', new:'new', latest:'new-internships',
      unread:'unread', undated:'date-unknown', leads:'leads', prog:'programs', pred:'predicted', big:'big-names', mine:'my-list'};
    const old = sget('ajf-tab');
    if(old && OLD[old]) route(OLD[old]);
  }
})();
if(location.hash) route(location.hash);
const saveUI = () => jset('ajf-ui', ui);
const curSort = () => ui.sort[ui.view] && SORTS[ui.sort[ui.view]] ? ui.sort[ui.view] : VIEWS[ui.view].sort;
const hashOf = () => '#' + (ui.section === 'browse' ? VIEW_HASH[ui.view] : ui.section === 'outlook' ? OUT_HASH[ui.out] : ui.section);
function syncHash(){ const h = hashOf(); if(location.hash !== h) history.replaceState(history.state, '', h); }

// ---------- display cleanup: presentation only, the records themselves are untouched
// "Shield AI (f7d8749a-...)", "General Atomics (25539)", "Samsung (Samsung_Careers)" -> the company name
const initials = s => s.split(/\s+/).map(w => w[0] || '').join('').toUpperCase();
function cleanCompany(c){
  c = String(c || '').trim();
  const m = c.match(/^(.+?)\s*\(([^()]+)\)$/);
  if(!m) return c;
  const name = m[1].trim(), inner = m[2].trim();
  const idLike = /^[0-9a-f]{8}-[0-9a-f]{4}-/i.test(inner) || (!/\s/.test(inner) && (
    /[\d_.\-]/.test(inner) || inner.toLowerCase() === name.toLowerCase().replace(/\s+/g, '') ||
    /^[a-z]+$/.test(inner) || (/^[A-Z]{1,3}$/.test(inner) && inner !== initials(name))));
  return idLike ? name : c;
}
const coName = j => j._co || (j._co = cleanCompany(j.company));
const ST = {AL:'Alabama',AK:'Alaska',AZ:'Arizona',AR:'Arkansas',CA:'California',CO:'Colorado',CT:'Connecticut',DE:'Delaware',DC:'District of Columbia',FL:'Florida',GA:'Georgia',HI:'Hawaii',ID:'Idaho',IL:'Illinois',IN:'Indiana',IA:'Iowa',KS:'Kansas',KY:'Kentucky',LA:'Louisiana',ME:'Maine',MD:'Maryland',MA:'Massachusetts',MI:'Michigan',MN:'Minnesota',MS:'Mississippi',MO:'Missouri',MT:'Montana',NE:'Nebraska',NV:'Nevada',NH:'New Hampshire',NJ:'New Jersey',NM:'New Mexico',NY:'New York',NC:'North Carolina',ND:'North Dakota',OH:'Ohio',OK:'Oklahoma',OR:'Oregon',PA:'Pennsylvania',RI:'Rhode Island',SC:'South Carolina',SD:'South Dakota',TN:'Tennessee',TX:'Texas',UT:'Utah',VT:'Vermont',VA:'Virginia',WA:'Washington',WV:'West Virginia',WI:'Wisconsin',WY:'Wyoming',PR:'Puerto Rico'};
const ST_NAME = {}; for(const k in ST) ST_NAME[ST[k].toLowerCase()] = k;
const CTRY = {'united states':'US','united states of america':'US','usa':'US','us':'US','u.s.':'US','u.s.a.':'US',
  'canada':'Canada','can':'Canada','mexico':'Mexico','mex':'Mexico','united kingdom':'United Kingdom','uk':'United Kingdom','gbr':'United Kingdom','gb':'United Kingdom','england':'United Kingdom','scotland':'United Kingdom',
  'spain':'Spain','es':'Spain','esp':'Spain','germany':'Germany','deu':'Germany','france':'France','fra':'France','italy':'Italy','ita':'Italy','israel':'Israel','isr':'Israel',
  'brazil':'Brazil','bra':'Brazil','malaysia':'Malaysia','mys':'Malaysia','egypt':'Egypt','bulgaria':'Bulgaria','russia':'Russia','costa rica':'Costa Rica','switzerland':'Switzerland','ch':'Switzerland',
  'india':'India','japan':'Japan','jpn':'Japan','poland':'Poland','pol':'Poland','netherlands':'Netherlands','nld':'Netherlands','china':'China','chn':'China','taiwan':'Taiwan','twn':'Taiwan',
  'singapore':'Singapore','sgp':'Singapore','sweden':'Sweden','norway':'Norway','ireland':'Ireland','australia':'Australia','portugal':'Portugal','belgium':'Belgium','austria':'Austria','denmark':'Denmark','finland':'Finland','south korea':'South Korea','korea':'South Korea'};
const titleCase = s => s.toLowerCase().replace(/(^|[\s\-'.\/])([a-z])/g, (m, a, b) => a + b.toUpperCase());
function tidyCity(s){
  s = String(s || '').replace(/\s+Area$/i, '').trim();
  if((s.match(/\//g) || []).length >= 2) s = s.split('/').pop().trim();
  if(/[a-z]/.test(s)) s = s.replace(/-[A-Z]{2,}\b.*$/, '').trim();
  if(s.length > 3 && (s === s.toUpperCase() || s === s.toLowerCase())) s = titleCase(s);
  return s;
}
function stateOf(t){
  const u = String(t || '').trim();
  if(/^[A-Za-z]{2}$/.test(u)) return ST[u.toUpperCase()] ? u.toUpperCase() : '';
  const m = u.match(/^([A-Z]{2})\s+\S*\d/);
  if(m && ST[m[1]]) return m[1];
  return ST_NAME[u.toLowerCase()] || '';
}
const junk = t => /^\d/.test(t) || (!/\s/.test(t) && /[\d_]/.test(t)) || /^[A-Z]\d[A-Z]\s?\d[A-Z]\d$/.test(t) || /^more\.*$/i.test(t);
const ABBR = {'nyc':'New York, NY', 'new york city':'New York, NY', 'sf':'San Francisco, CA', 'south sf':'South San Francisco, CA'};
// One location from a source's free text: "City, ST", "City, Country", "Remote", or the text itself when it can't be read reliably
function placeOf(raw){
  let s = String(raw || '').replace(/\s+/g, ' ').trim();
  if(!s || /^multi[- ]?locations?$/i.test(s)) return null;
  let note = '', more = false, m;
  if(/^remote\b/i.test(s)){
    const c = /canada/i.test(s) ? 'Canada' : /\b(usa|u\.s\.|us|united states|any state)\b/i.test(s) ? 'US' : '';
    return {label: c ? `Remote (${c})` : 'Remote', remote: true};
  }
  if(/\bhybrid\b/i.test(s)){ note = 'hybrid'; s = s.replace(/\(?\s*\bhybrid\b\s*\)?/ig, ' ').replace(/\s+/g, ' ').replace(/[\s,]+$/, '').trim(); }
  if(/\s[-–]\s*remote$/i.test(s)){ note = 'remote'; s = s.replace(/\s[-–]\s*remote$/i, '').trim(); }
  if(/,?\s*more\.{3}$/i.test(s)){ more = true; s = s.replace(/,?\s*more\.{3}$/i, '').trim(); }
  if(ABBR[s.toLowerCase()]) s = ABBR[s.toLowerCase()];
  const out = (label, st) => label ? {label: label + (note ? ` (${note})` : ''), st: st || '', more} : null;
  const city = c => tidyCity(String(c).replace(/\s*\([^)]*\)/g, ''));
  // Workday building codes: "US-FL-MELBOURNE-310 ~ 1100 W Hibiscus Blvd ~ BLDG 310"
  if((m = s.match(/^([A-Z]{2})-([A-Z]{2,3})-([^~]+?)-[^~-]*~/))){
    if(m[1] === 'US' && ST[m[2]]) return out(`${city(m[3])}, ${m[2]}`, m[2]);
    if(CTRY[m[1].toLowerCase()]) return out(`${city(m[3])}, ${CTRY[m[1].toLowerCase()]}`);
  }
  // "US | AZ | Scottsdale - 1475 North Scottsdale Road", "CA | BC | Victoria - ..."
  if((m = s.match(/^([A-Z]{2})\s*\|\s*([A-Z]{2})\s*\|\s*(.+?)(?:\s+-\s+.*)?$/))){
    if(m[1] === 'US' && ST[m[2]]) return out(`${city(m[3])}, ${m[2]}`, m[2]);
    if(m[1] === 'CA') return out(`${city(m[3])}, ${m[2]}, Canada`);
  }
  // "US.MI.Gaylord.814 South Otsego Avenue", "CA.ON.Mississauga.2251 Speakman Drive"
  if((m = s.match(/^([A-Z]{2})\.([A-Z]{2})\.([^.]+)/))){
    if(m[1] === 'US' && ST[m[2]]) return out(`${city(m[3])}, ${m[2]}`, m[2]);
    if(m[1] === 'CA') return out(`${city(m[3])}, ${m[2]}, Canada`);
  }
  // "US-AL-Huntsville", "USA - New York - Malta", "United States-Arizona-Chandler", "US-TX-Dallas-Field Service Office"
  if((m = s.match(/^(?:US|USA|United States)\s*-\s*([A-Za-z]+(?: [A-Za-z]+)*)\s*-\s*(.+)$/))){
    const st = stateOf(m[1]);
    if(st){
      const c = city(m[2].replace(/-(?=\s*(?:[A-Z0-9 ]*\d|Field|Office|Site|Main|HQ|Bldg|Building|Campus)).*$/i, '').replace(/,\s*[A-Z]{2}$/, ''));
      if(c) return out(`${c}, ${st}`, st);
    }
  }
  s = s.replace(/^[A-Z0-9]{3,6}:\s*/, '')                 // site codes: "CAF77: CCS - CIB, 13995 Pasteur Blvd, ..."
       .replace(/\s*\(([A-Z]{2}),\s*USA?\)/, ', $1')       // "Midland (MI, USA)"
       .replace(/\s*\([^)]*\)/g, '')                       // "(Neptune Road)", "(US-HQ)"
       .replace(/^(?:United States of America|United States|USA)\s+(?=[A-Z])/, '')
       .replace(/^US\s+(?=[A-Z]{2}\s)/, '')                // "US NY Waterford"
       .replace(/^(.+?)\s+([A-Z]{2})\s+(?:USA|US)$/, '$1, $2') // "Salem VA USA"
       .replace(/^([A-Za-z][A-Za-z .'-]*[a-z])\s+([A-Z]{2})$/, (m, c, st) => ST[st] ? `${c}, ${st}` : m); // "Long Beach CA"
  const toks = s.split(/\s*,\s*|\s+[-–|>:]\s+|\s*\|\s*/).map(t => t.trim()).filter(Boolean);
  const items = []; let country = '';
  for(let t of toks){
    t = t.replace(/^\d{5}(?:-\d{4})?\s+/, '').replace(/\s+\d{5}(?:-\d{4})?$/, '');
    const cm = t.match(/^(.+?)\s+(?:USA|US|U\.S\.A?\.?)$/);
    if(cm){ country = country || 'US'; t = cm[1]; }
    if(!t) continue;
    const st = stateOf(t);
    if(st){ items.push({st, t}); continue; }
    const c = CTRY[t.toLowerCase().replace(/\.$/, '')];
    if(c){ country = country || c; continue; }
    if(junk(t)) continue;
    const sm = t.match(/^([A-Z]{2})\s+([A-Za-z].*)$/);        // "NY Waterford", "MD Baltimore"
    if(sm && ST[sm[1]]){ items.push({st: sm[1], t: sm[1]}); items.push({t: sm[2]}); continue; }
    items.push({t});
  }
  let si = -1;
  for(let k = items.length - 1; k >= 0; k--) if(items[k].st){ si = k; break; }
  if(si >= 0){
    const code = items[si].st; let c = '';
    for(let k = si - 1; k >= 0 && !c; k--){ const x = items[k]; if(!x.st || x.st !== code || x.t.length > 2) c = x.t; }
    for(let k = si + 1; k < items.length && !c; k++) if(!items[k].st) c = items[k].t;
    if(c) return out(`${tidyCity(c)}, ${code}`, code);
    // A bare code is ambiguous ("LA" in a list of cities is Los Angeles, not Louisiana), so it stays as written
    return items[si].t.length === 2 ? out(s.trim()) : out(ST[code], code);
  }
  const plain = items.map(x => x.t);
  if(country && country !== 'US'){
    const c = plain.find(t => !/\b(province|governorate|region|oblast|county|state|prefecture|district)\b/i.test(t));
    return out(c ? `${tidyCity(c)}, ${country}` : country);
  }
  if(plain.length === 1) return out(tidyCity(plain[0]));
  if(!plain.length) return country === 'US' ? out('United States') : null;
  return out(String(raw).replace(/\s+/g, ' ').trim());
}
function places(raw){
  const list = [], seen = new Set(); let more = false;
  for(const part of String(raw || '').split(/\s*;\s*|\n+/)){
    const p = placeOf(part);
    if(!p) continue;
    if(p.more) more = true;
    const k = p.label.toLowerCase();
    if(seen.has(k)) continue;
    seen.add(k); list.push(p);
  }
  // Drop entries another one already covers: "United States", "New Hampshire" next to "Nashua, NH", "Dallas" next to "Dallas, TX"
  const states = new Set(list.filter(p => p.label.includes(',')).map(p => p.st).filter(Boolean));
  const cities = new Set(list.filter(p => p.st && p.label.includes(',')).map(p => p.label.split(',')[0].toLowerCase()));
  const out = list.filter(p => !(list.length > 1 && (p.label === 'United States' || (p.st && !p.label.includes(',') && states.has(p.st)) ||
    (!p.st && !p.remote && !p.label.includes(',') && cities.has(p.label.toLowerCase())))));
  out.more = more;
  return out;
}
const placesOf = j => j._pl || (j._pl = places(j.location));
const locShort = pl => !pl.length ? '' : pl[0].label + (pl.more ? (pl.length > 1 ? ' and other locations' : ' + more') : pl.length > 1 ? ` +${pl.length - 1} more` : '');
function termOf(j, tr){
  if(j.terms && j.terms.length) return {text: j.terms.join(', '), known: true};
  const l = (tr && tr.season_label) || '';
  if(!l || /^(term|season) not stated$/i.test(l)) return {text: 'Term not stated', known: false};
  return {text: l, known: !/not stated/i.test(l)};
}
function whenOf(j){
  const dk = dateKind(j);
  if(dk === 'employer') return {text: 'Posted ' + ago(ageDays(j.posted)), title: `Posted by the employer on ${fmtY(j.posted)}`};
  if(dk === 'listing') return {text: 'Listed ' + ago(ageDays(j.posted)), title: `${j.posted_from || 'An internship list'} listed it on ${fmtY(j.posted)}. The employer's own posting date isn't known.`};
  const f = foundMs(j);
  return {text: isNaN(f) ? 'Posting date unknown' : `Found ${ago(dayDiff(f))} · posting date unknown`, title: 'No posting date from the employer or any list the scan reads. This is when the scanner first found it.'};
}
const milesOf = j => { const g = j.geo || {}; if(typeof g.mi === 'number') return g.mi; const f = (j.tracks.fall || {}).miles; return typeof f === 'number' ? f : null; };
const distOf = j => { if(!HOME) return ''; const g = j.geo || {}, m = milesOf(j); return m === null ? '' : `${g.approx ? '~' : ''}${m} mi from ${HOME}`; };
const concernText = l => l === 'Grad students only?' ? 'May be graduate students only' : l === 'Seniors only?' ? 'May be seniors only'
  : /^Grad window /.test(l) ? l.replace(/^Grad window /, 'Graduation window ') : /^Min GPA /.test(l) ? l + ' (above yours)' : l;
const concernWhy = l => l === 'Grad students only?' ? 'The description may limit this role to graduate students.'
  : l === 'Seniors only?' ? 'The description may limit this role to seniors.'
  : /^Wants /.test(l) ? 'Asks for more completed years of school than your profile shows.'
  : /^Grad window /.test(l) ? 'Your graduation year falls outside the window the description gives.'
  : /^Min GPA /.test(l) ? 'Higher than the GPA in your profile.' : '';
const secName = k => k === 'all' ? 'All opportunities' : k === 'broad' ? 'Engineering (all majors)' : (T[k] && T[k].tab) || k;

// ---------- filtering and sorting
function trackFor(j, usePreset){
  const p = usePreset !== false && PRESET_BY[ui.f.preset];
  if(p && p.track && j.tracks[p.track]) return [p.track, j.tracks[p.track]];
  return best(j);
}
const hasFlag = (j, label) => j.flags.some(f => f.label === label);
const hasWarn = j => j.flags.some(f => f.kind === 'warn');
const hay = j => j._hay || (j._hay = [j.company, coName(j), j.title, j.location, j.discipline, j.matched.join(' '), j.gaps.join(' '), j.related.join(' ')].join(' ').toLowerCase());
const words = q => q.toLowerCase().split(/\s+/).filter(Boolean);
function keep(j, f, skip){
  if(f.preset){ const p = PRESET_BY[f.preset]; if(p && (p.track ? !j.tracks[p.track] : !j._big)) return false; }
  if(f.company){ const p = BIG.find(b => b.name === f.company); if(p && !coMatch(j.company, p.match || [])) return false; }
  if(skip !== 'term' && f.term){ const t = j.terms || []; if(f.term === 'none' ? t.length : !t.includes(f.term)) return false; }
  const g = j.geo || {};
  if(skip !== 'loc' && f.loc){
    if(f.loc === 'remote'){ if(!g.remote) return false; }
    else if(f.loc.startsWith('mi:')){ const m = milesOf(j); if(!(m !== null && m <= +f.loc.slice(3)) && !(g.remote && f.remote !== 'no')) return false; }
    else if(f.loc.startsWith('st:') && !(g.states || []).includes(f.loc.slice(3))) return false;
  }
  if(f.remote === 'no' && g.remote && !(g.states || []).length) return false;
  if(skip !== 'field' && f.field && j.discipline !== f.field) return false;
  if(f.fit){ const tier = trackFor(j)[1].tier; if(f.fit === 'good+' ? tier === 'look' : tier !== f.fit) return false; }
  if(f.posted && (f.posted === 'known' ? !j.posted : f.posted === 'unknown' ? !!j.posted : f.posted === 'recent' ? isOld(j)
    : !(j.posted && ageDays(j.posted) <= +f.posted))) return false;
  if(f.added && (f.added === 'update' ? !inThisUpdate(j) : !(updMs - foundMs(j) <= +f.added * 864e5))) return false;
  if(f.edu === 'under' && !hasFlag(j, 'Open to underclassmen')) return false;
  if(f.edu === 'nograd' && hasFlag(j, 'Grad students only?')) return false;
  if(f.elig === 'ok' && hasWarn(j) || f.elig === 'concern' && !hasWarn(j)) return false;
  const unc = (j.uncertain || []).length > 0;
  if(f.unc === 'hide' && unc || f.unc === 'only' && !unc) return false;
  const st = status[j.key];
  if(!f.show && gone(j) || f.show === 'dismissed' && st !== 'dismissed') return false;
  if(f.q){ const h = hay(j); if(!words(f.q).every(w => h.includes(w))) return false; }
  return true;
}
// "Most qualifications met": preferred first (what sets you apart), then required
const reqPct = j => { const s = j.quals && j.quals.summary; if(!s) return -1;
  const f = (m, n) => n ? m / n : 0.5; return (s.preferred_total || s.required_checked) ? 0.6 * f(s.preferred_met, s.preferred_total) + 0.4 * f(s.required_met, s.required_checked) : -1; };
function sortJobs(arr, s, usePreset){
  const sc = j => trackFor(j, usePreset)[1].score;
  const cmp = {
    found: (a, b) => foundKey(b).localeCompare(foundKey(a)) || sc(b) - sc(a),
    new: (a, b) => ((b.posted || b.first_seen) + b.first_seen).localeCompare((a.posted || a.first_seen) + a.first_seen) || sc(b) - sc(a),
    company: (a, b) => coName(a).localeCompare(coName(b)) || sc(b) - sc(a),
    reqs: (a, b) => reqPct(b) - reqPct(a) || sc(b) - sc(a),
    near: (a, b) => (milesOf(a) === null ? 9999 : milesOf(a)) - (milesOf(b) === null ? 9999 : milesOf(b)) || sc(b) - sc(a),
  }[s] || ((a, b) => sc(b) - sc(a));
  return arr.sort(cmp);
}

// ---------- one listing row
let lastOpen = null;
const fitHTML = tr => `<span class="fitl f-${esc(tr.tier)}" title="Estimated fit: ${tr.score} out of 100"><span class="bars" aria-hidden="true"><i></i><i></i><i></i></span>${TIERL[tr.tier] || ''}</span>`;
const applyHTML = (j, cls) => j.lead
  ? `<a class="btn ${cls}" href="${esc(j.url)}" target="_blank" rel="noopener" data-act="apply">Find posting${ICON.ext}<span class="sr"> (web search, opens in a new tab)</span></a>`
  : `<a class="btn primary ${cls}" href="${esc(j.url)}" target="_blank" rel="noopener" data-act="apply">Apply${ICON.ext}<span class="sr"> at ${esc(coName(j))} (opens in a new tab)</span></a>`;
const actAt = j => activity[j.key] && activity[j.key].at ? ' ' + fmt(activity[j.key].at) : '';
function rowHTML(j, ctx){
  const tr = trackFor(j, ctx === 'browse')[1];
  const st = status[j.key], un = isUnread(j);
  const pl = placesOf(j), w = whenOf(j), term = termOf(j, tr);
  // Two groups (who and where, then when) so a wrapped line never starts with a separator
  const who = [`<span class="co">${esc(coName(j))}</span>`,
    pl.length ? `<span title="${esc(pl.map(p => p.label).join('; '))}">${esc(locShort(pl))}</span>` : '<span class="unk">Location not listed</span>'];
  const when = [`<span${term.known ? '' : ' class="unk"'}>${esc(term.text)}</span>`, `<span title="${esc(w.title)}">${esc(w.text)}</span>`];
  const d = distOf(j);
  if(d && ctx === 'browse' && (ui.f.preset === 'fall' || curSort() === 'near' || ui.f.loc.startsWith('mi:'))) when.push(`<span>${esc(d)}</span>`);
  const meta = [`<span class="mg">${who.join('')}</span><span class="mg">${when.join('')}</span>`];
  const flags = [];
  if(st === 'applied') flags.push(`<span class="stl">${ICON.check}Applied${esc(actAt(j))}</span>`);
  else if(st === 'dismissed') flags.push('<span class="stl dis">Dismissed</span>');
  else if(st === 'saved' && ctx === 'mine') flags.push(`<span class="note">Saved${esc(actAt(j))}</span>`);
  for(const f of j.flags) if(f.kind === 'warn') flags.push(`<span class="concern" title="${esc(concernWhy(f.label) || 'Possible eligibility concern')}">${ICON.warn}<span class="sr">Possible eligibility concern: </span>${esc(concernText(f.label))}</span>`);
  if(j.stale) flags.push(`<span class="note" title="${esc('Not seen on the latest scan because ' + j.stale.why + '. Kept until it passes the ' + D.max_age + '-day limit.')}">Not re-checked since ${esc(fmt(j.stale.since))}</span>`);
  if(j.lead && ctx !== 'leads') flags.push('<span class="note">Unverified lead, no direct link</span>');
  return `<li class="job${un ? ' unread' : ''}${gone(j) && ctx !== 'mine' ? ' done' : ''}${lastOpen === j.key ? ' cur' : ''}" data-key="${esc(j.key)}">` +
    (un ? '<span class="dot" aria-hidden="true"></span>' : '') +
    `<button type="button" class="t" data-act="open" aria-haspopup="dialog">${un ? '<span class="sr">Unread: </span>' : ''}${esc(j.title)}</button>` +
    `<div class="meta">${meta.join('')}</div>` +
    (flags.length ? `<div class="flags">${flags.join('')}</div>` : '') +
    `<div class="fit">${fitHTML(tr)}</div>` +
    `<div class="acts">${applyHTML(j, 'sm')}` +
    `<button type="button" class="btn sm save" data-act="save" aria-pressed="${st === 'saved'}" aria-label="Save ${esc(j.title)}">${ICON.star}<span class="lbl">${st === 'saved' ? 'Saved' : 'Save'}</span></button>` +
    `<button type="button" class="iconbtn bd sm" data-act="menu" aria-haspopup="menu" aria-expanded="false" aria-controls="rowMenu" aria-label="More actions for ${esc(j.title)}">${ICON.dots}</button></div></li>`;
}

// ---------- Browse
let limit = PAGE, curBrowse = [];
const opt = (v, label, cur) => `<option value="${esc(v)}"${v === cur ? ' selected' : ''}>${esc(label)}</option>`;
function fillSelect(sel, html, value){
  if(sel._html !== html){ sel.innerHTML = html; sel._html = html; }
  sel.value = value;
  if(sel.value !== value) sel.value = '';
  sel.classList.toggle('on', !!value);
}
function syncControls(pool){
  const f = ui.f, cT = {}, cF = {}, cS = {};
  let nNone = 0, nRemote = 0;
  for(const j of pool){
    if(keep(j, f, 'term')){ const t = j.terms || []; if(!t.length) nNone++; for(const x of t) cT[x] = (cT[x] || 0) + 1; }
    if(keep(j, f, 'field') && j.discipline) cF[j.discipline] = (cF[j.discipline] || 0) + 1;
    if(keep(j, f, 'loc')){ const g = j.geo || {}; if(g.remote) nRemote++; for(const s of g.states || []) cS[s] = (cS[s] || 0) + 1; }
  }
  if(f.term && f.term !== 'none' && !(f.term in cT)) cT[f.term] = 0;
  if(f.field && !(f.field in cF)) cF[f.field] = 0;
  const byN = o => Object.entries(o).sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]));
  const term = opt('', 'Any term', f.term) + byN(cT).map(([t, n]) => opt(t, `${t} (${nf(n)})`, f.term)).join('') + opt('none', `Term not stated (${nf(nNone)})`, f.term);
  const states = Object.keys(cS).concat(f.loc.startsWith('st:') && !cS[f.loc.slice(3)] ? [f.loc.slice(3)] : []).sort((a, b) => (ST[a] || a).localeCompare(ST[b] || b));
  const loc = opt('', 'Any location', f.loc) + opt('remote', `Remote (${nf(nRemote)})`, f.loc) +
    (HOME ? `<optgroup label="Distance from ${esc(HOME)}">` + [25, 55, 100, 250, 500].map(m => opt('mi:' + m, `Within ${m} mi of ${HOME}, or remote`, f.loc)).join('') + '</optgroup>' : '') +
    '<optgroup label="State">' + states.map(s => opt('st:' + s, `${ST[s] || s} (${nf(cS[s] || 0)})`, f.loc)).join('') + '</optgroup>';
  const field = opt('', 'Any field', f.field) + byN(cF).map(([d, n]) => opt(d, `${d} (${nf(n)})`, f.field)).join('');
  const s = curSort();
  const sort = Object.entries(SORTS).filter(([, n]) => n).map(([k, n]) => opt(k, 'Sort: ' + n, s)).join('');
  document.querySelectorAll('[data-f="term"]').forEach(el => fillSelect(el, term, f.term));
  document.querySelectorAll('[data-f="loc"]').forEach(el => fillSelect(el, loc, f.loc));
  document.querySelectorAll('[data-f="field"]').forEach(el => fillSelect(el, field, f.field));
  document.querySelectorAll('[data-sort]').forEach(el => { fillSelect(el, sort, s); el.classList.remove('on'); });
  for(const k of MORE_KEYS) document.querySelectorAll(`[data-f="${k}"]`).forEach(el => fillSelect(el, OPTS[k].map(([v, l]) => opt(v, l, f[k])).join(''), f[k]));
  if(document.activeElement !== $('q')) $('q').value = f.q;
  const nMore = MORE_KEYS.filter(k => f[k]).length, nAll = nMore + ['term', 'loc', 'field'].filter(k => f[k]).length;
  $('moreN').hidden = !nMore; $('moreN').textContent = nMore;
  $('allN').hidden = !nAll; $('allN').textContent = nAll;
}
function chipList(){
  const f = ui.f, c = [];
  if(f.company) c.push(['company', `Company: ${f.company}`]);
  if(f.term) c.push(['term', f.term === 'none' ? 'Term not stated' : f.term]);
  if(f.loc) c.push(['loc', f.loc === 'remote' ? 'Remote' : f.loc.startsWith('mi:') ? `Within ${f.loc.slice(3)} mi of ${HOME}, or remote` : (ST[f.loc.slice(3)] || f.loc.slice(3))]);
  if(f.field) c.push(['field', f.field]);
  for(const k of MORE_KEYS) if(f[k]) c.push([k, optLabel(k, f[k])]);
  if(f.q) c.push(['q', `“${f.q}”`]);
  if(ui.unreadOnly) c.push(['unread', 'Unread only']);
  return c;
}
function renderBrowse(){
  const f = ui.f, v = ui.view, s = curSort(), pool = POOL[v];
  const res = pool.filter(j => keep(j, f));
  const nUnread = res.reduce((n, j) => n + (isUnread(j) ? 1 : 0), 0);
  const list = ui.unreadOnly ? res.filter(isUnread) : res;
  sortJobs(list, s);
  curBrowse = list;
  $('viewTabs').innerHTML = Object.entries(VIEWS).map(([k, V]) => `<button type="button" role="tab" class="tab" id="tab-${k}" data-view="${k}" aria-selected="${k === v}" aria-controls="viewPanel" tabindex="${k === v ? 0 : -1}" title="${esc(V.title)}">${V.short ? `<span class="d-only">${esc(V.name)}</span><span class="m-only">${esc(V.short)}</span>` : esc(V.name)}<span class="n">${nf(POOL[k].filter(j => f.show || !gone(j)).length)}</span></button>`).join('');
  $('viewPanel').setAttribute('aria-labelledby', 'tab-' + v);
  $('presets').innerHTML = '<span class="lbl" id="presetsL">Quick filters</span>' + PRESETS.map(p => `<button type="button" class="preset" data-preset="${p.id}" aria-pressed="${f.preset === p.id}" title="${esc(p.desc || '')}">${ICON.check}${esc(p.name)}</button>`).join('');
  syncControls(pool);
  const chips = chipList(), P0 = PRESET_BY[f.preset];
  $('rhead').innerHTML = `<span class="rcount" id="rcount" tabindex="-1">${plural(list.length, 'opportunity', 'opportunities')}${VIEWS[v].what ? ` <span>${esc(VIEWS[v].what)}</span>` : ''}</span>` +
    chips.map(([k, l]) => `<span class="chip"><span>${esc(l)}</span><button type="button" data-clear="${k}" aria-label="Remove filter: ${esc(l)}">${ICON.x}</button></span>`).join('') +
    (chips.length || f.preset ? '<button type="button" class="linkbtn" data-clear="all">Clear all</button>' : '') +
    `<span class="end"><button type="button" class="btn sm" id="unreadBtn" aria-pressed="${ui.unreadOnly}" title="Listings you haven't opened, saved, applied to or dismissed">${CB}Unread only <span class="n">${nf(nUnread)}</span></button>` +
    (ui.unreadOnly && nUnread ? '<button type="button" class="linkbtn" data-m="markall">Mark all as read</button>' : '') +
    `<button type="button" class="linkbtn" id="insBtn" aria-haspopup="dialog">Skill insights</button></span>` +
    (P0 && P0.desc ? `<p class="rnote">${esc(P0.name)}: ${esc(P0.desc)}</p>` : '');
  const shown = list.slice(0, limit);
  let h = '';
  if(s === 'found'){
    const size = {}; let last = null;
    for(const j of list){ const g = foundGroup(j)[0]; size[g] = (size[g] || 0) + 1; }
    for(const j of shown){
      const [g, label] = foundGroup(j);
      if(g !== last) h += `<li class="grp${g === 'now' ? ' now' : ''}"><h3>${esc(label)}<span>${nf(size[g])}</span></h3></li>`;
      last = g; h += rowHTML(j, 'browse');
    }
  } else h = shown.map(j => rowHTML(j, 'browse')).join('');
  $('results').innerHTML = list.length ? h : emptyBrowse(pool);
  $('pager').innerHTML = list.length > PAGE ? `<span>Showing ${nf(shown.length)} of ${nf(list.length)}</span>` +
    (list.length > shown.length ? `<button type="button" class="btn" data-more="browse">Show ${nf(Math.min(PAGE, list.length - shown.length))} more</button>` : '') : '';
  $('filtShow').textContent = `Show ${plural(list.length, 'result')}`;
}
function emptyBrowse(pool){
  if(!D.jobs.length) return '<li class="empty"><b>No scan results yet</b><p>In the GitHub repository, open the Actions tab, choose “Daily job scan”, and select “Run workflow”. This page fills in about fifteen minutes later.</p></li>';
  if(ui.unreadOnly) return '<li class="empty"><b>Nothing unread here</b><p>You’ve reviewed everything that matches. Listings from the next scan show up here.</p><button type="button" class="btn" data-clear="unread">Show all listings</button></li>';
  const P0 = PRESET_BY[ui.f.preset];
  let title = 'No opportunities match these filters', msg = 'Remove a filter or clear the search to see more.';
  if(ui.view === 'new' && !pool.length) [title, msg] = ['Nothing posted in the last 7 days', 'Listings with a posting date this week will show up here.'];
  else if(P0 && P0.id === 'motor' && T.motor && !pool.some(j => j.tracks.motor)) [title, msg] = ['No motorsport listings right now', T.motor.empty];
  else if(P0 && P0.id === 'fall' && T.fall && ui.f.term === T.fall.season_label) [title, msg] = [`No ${T.fall.tab} listings yet`, T.fall.empty];
  return `<li class="empty"><b>${esc(title)}</b><p>${esc(msg)}</p><button type="button" class="btn" data-clear="all">Clear all filters</button></li>`;
}

// ---------- Saved and Applied
let curMine = [];
function renderMine(){
  const kind = ui.section;
  const at = j => (activity[j.key] || {}).at || '';
  const live = D.jobs.filter(j => status[j.key] === kind).sort((a, b) => at(b).localeCompare(at(a)) || best(b)[1].score - best(a)[1].score);
  curMine = live;
  $('mineH').textContent = kind === 'saved' ? 'Saved' : 'Applied';
  $('mineSub').textContent = kind === 'saved' ? `${plural(live.length, 'listing')} saved to come back to.`
    : `${plural(live.length, 'listing')} marked as applied. Opening an Apply link never marks a job as applied on its own.`;
  $('mineList').innerHTML = live.length ? live.map(j => rowHTML(j, 'mine')).join('')
    : `<li class="empty"><b>${kind === 'saved' ? 'Nothing saved yet' : 'Nothing marked as applied yet'}</b><p>${kind === 'saved'
      ? 'Use Save on any listing to keep it here.' : 'After you apply, open the listing and select Applied, or use the ⋯ menu on its row.'}</p></li>`;
  const old = s => Object.entries(activity).filter(([k, a]) => a && a.s === s && !byKey.has(k)).sort((a, b) => (b[1].at || '').localeCompare(a[1].at || ''));
  const histRow = ([k, a]) => `<li><span class="when">${esc(a.s === 'applied' ? 'Applied' : a.s === 'saved' ? 'Saved' : 'Dismissed')} ${esc(fmt(a.at))}</span><span><span class="co">${esc(cleanCompany(a.c))}</span> · ${esc(a.t)}</span>${a.u ? `<a href="${esc(a.u)}" target="_blank" rel="noopener">Old link${ICON.ext}<span class="sr"> (opens in a new tab)</span></a>` : '<span></span>'}</li>`;
  const g = old(kind), dis = kind === 'applied' ? old('dismissed') : [];
  $('mineGone').innerHTML = (g.length ? `<h2 class="h2s">No longer listed<span>${nf(g.length)}</span></h2><p class="small muted">Closed, or past the ${D.max_age}-day window. Kept here as a record.</p><ul class="hist">${g.map(histRow).join('')}</ul>` : '') +
    (dis.length ? `<details class="small" style="margin-top:20px"><summary>Dismissed listings that are no longer listed (${nf(dis.length)})</summary><ul class="hist">${dis.map(histRow).join('')}</ul></details>` : '');
}

// ---------- Outlook: programs, predicted roles, leads, big names
const OUTN = {programs:'Programs', predicted:'Predicted', leads:'Leads', big:'Big-name timing'};
const isSoon = p => p.st === 'upcoming' || p.st === 'due';
const pTerm = p => p.s + ' ' + p.y;
const pTerms = ((D.pred_info || {}).terms || []).filter(t => P.some(p => pTerm(p) === t));
const cap = s => s.charAt(0).toUpperCase() + s.slice(1);
// Summer is the aerospace section, so it starts on aerospace companies; other terms take any engineering
const pAeroDefault = term => term.startsWith('summer');
function outCount(o){
  if(o === 'programs') return PROGS.filter(p => p.status === 'open' || p.status === 'published').length;
  if(o === 'predicted') return P.filter(p => isSoon(p) && pTerm(p) === pTerms[0] && (p.aero || p.mo || !pAeroDefault(pTerms[0] || ''))).length;
  if(o === 'leads') return LEADS.filter(j => !gone(j)).length;
  return BIG.length;
}
function renderOut(){
  $('outTabs').innerHTML = OUTS.map(o => `<button type="button" role="tab" class="tab" id="otab-${o}" data-out="${o}" aria-selected="${o === ui.out}" aria-controls="pane-${o}" tabindex="${o === ui.out ? 0 : -1}">${OUTN[o]}<span class="n">${nf(outCount(o))}</span></button>`).join('');
  for(const o of OUTS) $('pane-' + o).hidden = o !== ui.out;
  if(ui.out === 'programs') renderProg();
  else if(ui.out === 'predicted'){ if(!pReady) setupPred(); renderPred(); }
  else if(ui.out === 'leads') renderLeads();
  else renderBig();
}
const callout = (title, body) => `${ICON.info}<p><b>${esc(title)}.</b> ${esc(body)}</p>`;
$('note-programs').innerHTML = callout('Programs, not job postings', `Government and lab programs with their own application cycles. Status, deadlines and eligibility are what each official page said on the date shown as verified; a date the page doesn't give is left out, and past-cycle timing is labeled as an estimate. They don't follow the ${D.max_age}-day posting window.`);
$('note-leads').innerHTML = callout('Unverified leads with no direct application link', 'Found only on intern-list.com, which links to jobright.ai instead of the employer, so Find posting searches the web for the company’s own listing. A lead moves to Browse on its own once a career site the scan reads lists the same job.').replace(ICON.info, ICON.warn);
$('note-big').innerHTML = callout('Typical recruiting windows, not announced dates', 'When well-known aerospace and defense employers usually recruit summer interns, from past cycles, and what this cycle’s scans found from each. Shaded months are the usual window; the line marks this month. Dates marked Published come from the program itself. “Last cycle” is the company’s first engineering internship on the Simplify list in the previous cycle, which doesn’t catch every company’s first postings.');

const PST = {open:'Open', published:'Deadline published', 'not-yet':'Not open yet', unverified:'Unverified', closed:'Closed'};
function renderProg(){
  $('progList').innerHTML = PROGS.map(p => {
    const next = p.deadlines.find(d => !d.passed);
    const [b, s] = next ? [fmt(next.date), `${next.term} deadline · ${next.days === 0 ? 'today' : 'in ' + next.days + ' days'}`]
      : [PST[p.status] || p.status, p.deadlines.length ? 'All listed deadlines passed' : 'No deadline published'];
    const meta = [`<span class="co">${esc(p.sponsor)}</span>`, `<span>Status: ${esc(PST[p.status] || p.status)}</span>`, ...p.terms.map(t => `<span>${esc(t)}</span>`), `<span>Verified ${esc(fmtY(p.verified))}</span>`];
    const flags = [];
    if(p.changed) flags.push(`<span class="concern">${ICON.warn}Official page changed ${esc(fmt(p.changed))}: re-check it</span>`);
    if(p.check_ok === false) flags.push(`<span class="note">${esc(p.check_error || 'Not re-checked automatically')}</span>`);
    const dl = p.deadlines.map(d => `<li>${esc(d.term)}: <b>${esc(fmtY(d.date))}</b>${d.passed ? ' (passed)' : ''} <q>${esc(d.text)}</q></li>`).join('');
    return `<li class="item s-${esc(p.status)}"><div class="when"><b>${esc(b)}</b><small>${esc(s)}</small></div><div class="main">
      <p class="t2">${esc(p.name)}</p><p class="meta">${meta.join('')}</p>${flags.length ? `<div class="flags">${flags.join('')}</div>` : ''}
      ${p.status_note ? `<p class="sub">${esc(p.status_note)}</p>` : ''}
      <details><summary>Eligibility and dates</summary>
        <p><b>Eligibility, as the page states:</b> ${esc(p.eligibility)}</p>
        ${dl ? `<p><b>Deadlines on the official page:</b></p><ul>${dl}</ul>` : '<p>No deadline is published on the official page.</p>'}
        ${p.estimate ? `<p><b>Estimate (past cycle, not an announced date):</b> ${esc(p.estimate)}</p>` : ''}
        <p class="muted">Verified on the official page ${esc(fmtY(p.verified))}${p.page_updated ? ' (page last updated ' + esc(fmtY(p.page_updated)) + ')' : ''}. Page last re-checked by the scan ${esc(fmtT(p.checked))}.</p>
        ${(p.dates_seen || []).length && p.changed ? `<p class="muted">Dates on the page now: ${p.dates_seen.map(esc).join(' · ')}</p>` : ''}
      </details></div>
      <div class="acts"><a class="btn primary sm" href="${esc(p.apply)}" target="_blank" rel="noopener">Apply${ICON.ext}<span class="sr"> to ${esc(p.name)} (opens in a new tab)</span></a><a class="linkbtn" href="${esc(p.url)}" target="_blank" rel="noopener">Official page${ICON.ext}<span class="sr"> (opens in a new tab)</span></a></div></li>`;
  }).join('') || '<li class="empty"><b>No programs set up</b><p>Add them to programs.toml.</p></li>';
}

const pAero = {}, pNear = {};
let pT = pTerms[0] || '', pStat = 'soon', pMonth = '', pLimit = PAGE, pReady = false;
const thisMonth = D.today.slice(0, 7);
// Roles due now (expected up to three weeks ago) count toward this month
const pMonthOf = p => p.exp.slice(0, 7) < thisMonth ? thisMonth : p.exp.slice(0, 7);
const MONTHS = (() => { const out = []; let y = +D.today.slice(0, 4), m = +D.today.slice(5, 7);
  for(let i = 0; i < 9; i++){ out.push(`${y}-${String(m).padStart(2, '0')}`); if(++m > 12){ m = 1; y++; } } return out; })();
function setupPred(){
  pReady = true;
  $('pseason').innerHTML = pTerms.map(t => `<button type="button" data-term="${esc(t)}" aria-pressed="${t === pT}">${esc(cap(t))}</button>`).join('');
  $('pseason').hidden = pTerms.length < 2;
  $('paero').checked = pT in pAero ? pAero[pT] : pAeroDefault(pT);
  const fall = T.fall && pT.startsWith('fall');
  $('pnearTog').hidden = !fall;
  if(fall) $('pnearLabel').textContent = `Within ${T.fall.radius} mi of ${T.fall.home} only`;
  $('pnear').checked = !!pNear[pT];
  const counts = {};
  for(const p of P) if(pTerm(p) === pT) counts[p.d] = (counts[p.d] || 0) + 1;
  $('pdisc').innerHTML = '<option value="">Any field</option>' + Object.entries(counts).sort((a, b) => b[1] - a[1]).map(([d, n]) => `<option value="${esc(d)}">${esc(d)} (${nf(n)})</option>`).join('');
  const pi = D.pred_info || {};
  $('note-predicted').innerHTML = callout('Forecasts, not openings', `Internships posted in past cycles, and when each should come back for ${cap(pT)}: last cycle's posting date moved forward a year (the middle date when there are several cycles). Built from ${nf(pi.postings)} engineering internship postings since ${fmtY(pi.since)}. A role counts as posted once the same company posts one with a similar title this cycle. Companies don't repeat every role, so treat the dates as estimates.`);
  pLimit = PAGE;
}
function pPool(){
  const q = $('pq').value.trim().toLowerCase(), disc = $('pdisc').value;
  const aero = $('paero').checked, near = !$('pnearTog').hidden && $('pnear').checked;
  return P.filter(p => pTerm(p) === pT && (!aero || p.aero || p.mo) && (!near || p.mi != null) && (!disc || p.d === disc) &&
    (!q || words(q).every(w => [p.co, p.t, p.lt, p.loc, p.d].join(' ').toLowerCase().includes(w))));
}
function pRow(p){
  const days = Math.round((Date.parse(p.exp + 'T12:00:00') - todayMs) / 864e5);
  const [when, label] = p.st === 'posted' ? [fmt(p.seen), 'Posted this cycle']
    : ['~' + fmt(p.exp), p.st === 'due' ? 'Expected now' : p.st === 'late' ? 'Not seen yet' : days > 60 ? `Expected in ${Math.round(days / 7)} weeks` : `Expected in ${days} days`];
  // Past-cycle locations are cut at 70 characters upstream, so a cut-off last city is dropped rather than shown half-written
  let ploc = p.loc || '', cut = false;
  if(ploc.length >= 70 && ploc.includes(';')){ ploc = ploc.slice(0, ploc.lastIndexOf(';')); cut = true; }
  const pl = ploc ? places(ploc) : [];
  if(cut) pl.more = true;
  const meta = [`<span class="co">${esc(cleanCompany(p.co))}</span>`, pl.length && `<span title="${esc(p.loc)}">${esc(locShort(pl))}</span>`, p.d && `<span>${esc(p.d)}</span>`,
    p.mi != null && HOME && `<span>${p.mi} mi from ${esc(HOME)}</span>`].filter(Boolean).join('');
  const notes = [];
  if(p.aero) notes.push('Aerospace company');
  if(p.mo) notes.push('Motorsport');
  if(p.st === 'late') notes.push(`${-days} days past last cycle's date`);
  if(p.past.length > 1) notes.push(`Posted ${p.past.length} cycles running`);
  if(p.lo && p.hi) notes.push(`Past cycles: ${fmt(p.lo)} to ${fmt(p.hi)}`);
  if(p.lt !== p.t) notes.push(`Last posted as “${p.lt}”`);
  const past = p.past.map(([y, d]) => `${fmtY(d)} for ${cap(p.s)} ${y}`).join(' · ');
  const act = p.key ? `<a class="btn primary sm" href="${esc(p.u)}" target="_blank" rel="noopener">Apply${ICON.ext}<span class="sr"> (opens in a new tab)</span></a>`
    : `<a class="btn sm" href="${esc(p.u)}" target="_blank" rel="noopener">Career site${ICON.ext}<span class="sr"> (opens in a new tab)</span></a>`;
  return `<li class="item st-${esc(p.st)}"><div class="when"><b>${esc(when)}</b><small>${esc(label)}</small></div><div class="main">
    <p class="t2">${esc(p.t)}</p><p class="meta">${meta}</p><p class="sub">Previously posted ${esc(past)}</p>${notes.length ? `<p class="sub muted">${esc(notes.join(' · '))}</p>` : ''}</div>
    <div class="acts">${act}${p.last ? `<a class="linkbtn" href="${esc(p.last)}" target="_blank" rel="noopener">Last cycle's posting${ICON.ext}<span class="sr"> (opens in a new tab)</span></a>` : ''}</div></li>`;
}
function renderPred(){
  const pool = pPool();
  const counts = MONTHS.map(mo => pool.filter(p => isSoon(p) && pMonthOf(p) === mo).length), most = Math.max(1, ...counts);
  $('pmonths').innerHTML = MONTHS.map((mo, i) => `<button type="button" class="mo" data-mo="${mo}" aria-pressed="${mo === pMonth}" aria-label="${counts[i]} roles expected in ${MON[+mo.slice(5) - 1]} ${mo.slice(0, 4)}"><i style="height:${2 + Math.round(38 * counts[i] / most)}px"></i><b>${counts[i]}</b>${MON[+mo.slice(5) - 1]}</button>`).join('');
  let rows = pool.filter(p => pStat === 'all' || (pStat === 'soon' ? isSoon(p) : p.st === pStat));
  if(pMonth) rows = rows.filter(p => isSoon(p) && pMonthOf(p) === pMonth);
  rows.sort(pStat === 'late' ? (a, b) => b.exp.localeCompare(a.exp) : pStat === 'posted' ? (a, b) => (b.seen || '').localeCompare(a.seen || '')
    : (a, b) => a.exp.localeCompare(b.exp) || a.co.localeCompare(b.co));
  const mLabel = pMonth ? `Expected in ${MON[+pMonth.slice(5) - 1]} ${pMonth.slice(0, 4)}` : '';
  $('pshown').innerHTML = `<span class="rcount">${plural(rows.length, 'predicted role')}</span>` +
    (pMonth ? `<span class="chip"><span>${esc(mLabel)}</span><button type="button" id="punpick" aria-label="Remove filter: ${esc(mLabel)}">${ICON.x}</button></span>` : '');
  const empty = pStat === 'posted' ? 'None of these roles has been posted yet this cycle.'
    : pStat === 'late' ? 'Nothing overdue: every role due by now has been posted.' : 'No predicted roles match these filters.';
  $('plist').innerHTML = rows.length ? rows.slice(0, pLimit).map(pRow).join('') : `<li class="empty"><b>${esc(empty)}</b></li>`;
  $('ppager').innerHTML = rows.length > PAGE ? `<span>Showing ${nf(Math.min(pLimit, rows.length))} of ${nf(rows.length)}</span>` +
    (rows.length > pLimit ? `<button type="button" class="btn" data-more="pred">Show ${nf(Math.min(PAGE, rows.length - pLimit))} more</button>` : '') : '';
}
const pPress = () => document.querySelectorAll('#pstat button').forEach(x => x.setAttribute('aria-pressed', x.dataset.st === pStat));
$('pseason').addEventListener('click', e => { const b = e.target.closest('[data-term]'); if(!b) return; pT = b.dataset.term; pMonth = ''; setupPred(); renderPred(); });
$('pstat').addEventListener('click', e => { const b = e.target.closest('[data-st]'); if(!b) return; pStat = b.dataset.st; if(pStat !== 'soon') pMonth = ''; pPress(); pLimit = PAGE; renderPred(); });
$('pmonths').addEventListener('click', e => { const b = e.target.closest('[data-mo]'); if(!b) return;
  pMonth = pMonth === b.dataset.mo ? '' : b.dataset.mo; pStat = 'soon'; pPress(); pLimit = PAGE; renderPred(); });
$('pshown').addEventListener('click', e => { if(e.target.closest('#punpick')){ pMonth = ''; pLimit = PAGE; renderPred(); $('pmonths').querySelector('button').focus(); } });
$('paero').addEventListener('change', () => { pAero[pT] = $('paero').checked; pLimit = PAGE; renderPred(); });
$('pnear').addEventListener('change', () => { pNear[pT] = $('pnear').checked; pLimit = PAGE; renderPred(); });
$('pq').addEventListener('input', debounce(() => { pLimit = PAGE; renderPred(); }, 150));
$('pdisc').addEventListener('change', () => { pLimit = PAGE; renderPred(); });

let leadLimit = PAGE, curLeads = [];
function renderLeads(){
  const q = $('lq').value.trim(), s = $('lsort').value;
  const list = LEADS.filter(j => (ui.f.show || !gone(j)) && (!q || words(q).every(w => hay(j).includes(w))));
  sortJobs(list, s, false);
  curLeads = list;
  $('lhead').innerHTML = `<span class="rcount">${plural(list.length, 'lead')}</span><span class="muted small">Each one still needs to be found on the employer’s own site.</span>`;
  $('leadList').innerHTML = list.length ? list.slice(0, leadLimit).map(j => rowHTML(j, 'leads')).join('')
    : `<li class="empty"><b>${LEADS.length ? 'No leads match this search.' : 'No leads right now: every listing has a direct company link.'}</b></li>`;
  $('lpager').innerHTML = list.length > PAGE ? `<span>Showing ${nf(Math.min(leadLimit, list.length))} of ${nf(list.length)}</span>` +
    (list.length > leadLimit ? `<button type="button" class="btn" data-more="leads">Show ${nf(Math.min(PAGE, list.length - leadLimit))} more</button>` : '') : '';
}
$('lq').addEventListener('input', debounce(() => { leadLimit = PAGE; renderLeads(); }, 150));
$('lsort').addEventListener('change', () => { leadLimit = PAGE; renderLeads(); });

const inWin = (w, m) => w.length === 2 && (w[0] <= w[1] ? m >= w[0] && m <= w[1] : m >= w[0] || m <= w[1]);
const RECRUIT_YEAR = [7, 8, 9, 10, 11, 12, 1, 2, 3, 4, 5, 6];
function renderBig(){
  const m = +D.today.slice(5, 7);
  // Companies come grouped (space, defense...) in sources.toml order; each group gets a heading
  const inGroup = {};
  for(const p of BIG) inGroup[p.group] = (inGroup[p.group] || 0) + 1;
  let last = null;
  $('bigList').innerHTML = BIG.map((p, i) => {
    const head = p.group && p.group !== last ? `<h2 class="bn-group">${esc(p.group)}<span>${inGroup[p.group]}</span></h2>` : '';
    last = p.group;
    const mine = D.jobs.filter(j => !j.lead && j.tracks.broad && coMatch(j.company, p.match));
    const strong = mine.filter(j => Object.values(j.tracks).some(t => t.tier === 'strong')).length;
    const live = inWin(p.window, m), opens = p.window.length ? MON[p.window[0] - 1] : '';
    const scanBad = p.scan && p.scan !== 'ok';
    let st;
    if(mine.length) st = `<button type="button" class="go" data-pick="${i}">${plural(mine.length, 'listing')} posted recently</button><small>${strong ? `${strong} strong match${strong > 1 ? 'es' : ''}` : 'None rated a strong match yet'}${scanBad ? ' · scan ' + esc(p.scan) + ', may be missing some' : ''}</small>`;
    // A failed or partial scan is never shown as "nothing posted"
    else if(scanBad) st = `<span class="bad">${ICON.warn} Scan ${p.scan === 'partial' ? 'incomplete' : esc(p.scan)}</span><small title="${esc(p.scan_note || '')}">Couldn't confirm what's posted; check their site</small>`;
    else if(!p.scanned) st = live ? '<span class="hot">In season</span><small>Not scanned here; apply on their site</small>' : `<span>Usually opens ${opens}</span><small>Not scanned here; apply on their site</small>`;
    else st = live ? `<span class="hot">In season</span><small>Nothing posted in the last ${D.max_age} days</small>` : `<span>${opens ? 'Usually opens ' + opens : 'No usual window set'}</span><small>Nothing posted in the last ${D.max_age} days</small>`;
    const tl = `<div class="tl" aria-hidden="true">${RECRUIT_YEAR.map(mo => `<i class="${inWin(p.window, mo) ? 'on' : ''} ${mo === m ? 'now' : ''}"></i>`).join('')}</div>` +
      `<div class="tlm" aria-hidden="true">${RECRUIT_YEAR.map(mo => mo === m ? `<b>${MON[mo - 1][0]}</b>` : `<span>${MON[mo - 1][0]}</span>`).join('')}</div>` +
      (p.window.length ? `<div class="win">Typically ${MON[p.window[0] - 1]} to ${MON[p.window[1] - 1]} (estimate)</div>` : '<div class="win">No usual window set</div>') +
      (p.dates ? `<div class="pub"><b>Published</b>${esc(p.dates)}</div>` : '');
    const fs = '<span class="lbl">Earliest posting: </span>' + (p.first_seen ? `${fmt(p.first_seen)}<small>${p.most_open} open at most</small>` : '—') +
      (p.past && p.past.length ? `<small>Last cycle: from ${fmtY(p.past[0][1])} (${p.past[0][2]} on the list)</small>` : '');
    return head + `<div class="bn"><div class="nm">${esc(p.name)}${p.careers ? `<a href="${esc(p.careers)}" target="_blank" rel="noopener">Student careers${ICON.ext}<span class="sr"> (opens in a new tab)</span></a>` : ''}</div>
      <div class="st">${st}</div><div class="tlw">${tl}</div><div class="fs">${fs}</div>${p.note ? `<div class="sub2">${esc(p.note)}</div>` : ''}</div>`;
  }).join('') || '<p class="empty">No companies set up (sources.toml [popular]).</p>';
}
$('bigList').addEventListener('click', e => {
  const b = e.target.closest('[data-pick]'); if(!b) return;
  const p = BIG[+b.dataset.pick];
  ui.section = 'browse'; ui.view = 'all'; ui.f = Object.assign({}, F0, {company: p.name}); applyPreset('broad'); ui.unreadOnly = false;
  limit = PAGE; showSection(); scrollTo(0, 0); $('rcount').focus();
});

// ---------- Data status (scanner coverage), insights
const C = D.coverage || {counts: {}};
const issues = D.sources.filter(s => ['partial', 'failed', 'stale'].includes(s.state) || s.suspicious);
function renderStat(){
  const b = $('statBtn');
  if(!D.sources.length){ b.innerHTML = '<span>Waiting for the first scan</span>'; b.setAttribute('aria-label', 'Data status: waiting for the first scan'); return; }
  const lbl = String(D.updated_label || '').replace(/, \d{4}/, '');
  const time = (lbl.match(/\d{1,2}:\d{2}\s?[AP]M/) || [lbl])[0];
  b.innerHTML = `<span class="l">Updated ${esc(lbl)}</span><span class="s"><span class="u">Updated </span>${esc(time)}</span>` +
    (issues.length ? `<span class="w">${ICON.warn}${issues.length}<span class="l2">&nbsp;source issue${issues.length > 1 ? 's' : ''}</span></span>` : '');
  b.setAttribute('aria-label', `Updated ${lbl}. ` + (issues.length ? `${plural(issues.length, 'source')} weren't fully read or dropped unexpectedly, so some listings may be missing. Open data status.` : 'Every source was read fully. Open data status.'));
  b.title = issues.length ? 'Some sources weren’t fully read: open Data status for details' : 'Open Data status';
}
const STATE = {ok:'read fully', partial:'partial', failed:'failed', stale:'stale', off:'needs setup'};
function renderStatusBody(){
  const k = C.counts || {}, sus = D.sources.filter(s => s.suspicious);
  let h = `<p>Last update: <b>${esc(D.updated_label)}</b>. Sources are read every 5 hours. Listings stay for ${D.max_age} days, counted from the posting date or, when no date is known, from the day the scan first found them.</p>`;
  h += '<ul class="ds-sum">' + ['ok', 'partial', 'failed', 'stale', 'off'].filter(s => k[s]).map(s => `<li class="c-${s}"><b>${nf(k[s])}</b>&nbsp;${STATE[s]}</li>`).join('') +
    (sus.length ? `<li class="c-failed">${ICON.warn}<b>${sus.length}</b>&nbsp;unexpected drop${sus.length > 1 ? 's' : ''}</li>` : '') + '</ul>';
  const bad = D.sources.filter(s => s.state && s.state !== 'ok' || s.suspicious)
    .sort((a, b) => ['stale', 'failed', 'partial', 'off', 'ok'].indexOf(a.state) - ['stale', 'failed', 'partial', 'off', 'ok'].indexOf(b.state));
  const row = s => `<tr><td>${esc(s.name)}<br><span class="muted">${esc(s.kind)}</span></td><td class="c-${esc(s.state)}">${esc(STATE[s.state] || s.state)}${s.suspicious ? '<br><span class="c-failed">' + esc(s.suspicious) + '</span>' : ''}</td>` +
    `<td>${esc(fmtT(s.last_success))}${s.last_complete && s.last_complete !== s.last_success ? '<br><span class="muted">complete: ' + esc(fmtT(s.last_complete)) + '</span>' : ''}</td>` +
    `<td>${esc(s.error || (s.notes || []).join('; ') || '')}</td><td>${s.careers ? `<a href="${esc(s.careers)}" target="_blank" rel="noopener">Career site${ICON.ext}<span class="sr"> (opens in a new tab)</span></a>` : ''}</td></tr>`;
  h += '<h3>Sources that need attention</h3>';
  h += bad.length ? `<div class="tbl"><table><thead><tr><th scope="col">Source</th><th scope="col">State</th><th scope="col">Last worked</th><th scope="col">Error or notes</th><th scope="col"><span class="sr">Link</span></th></tr></thead><tbody>${bad.map(row).join('')}</tbody></table></div>` : '<p>Every source was read completely.</p>';
  h += `<p class="small muted"><b>Partial</b>: the request worked but stopped early (a page cap, a page that failed, a site that repeated itself), so listings it didn't return are kept from earlier scans, marked as not re-checked, instead of being treated as closed. <b>Failed</b>: no answer this time, but it worked within the last day. <b>Stale</b>: it hasn't worked for over a day; its listings stay (still subject to the ${D.max_age}-day limit) and are marked as not re-checked. Check those companies' career sites by hand.</p>`;
  const dr = D.discovery || {};
  if(dr.date){
    const rep = dr.repair || [];
    h += `<details><summary>Boards found automatically: ${Object.entries(dr.states || {}).map(([s, n]) => n + ' ' + s).join(', ')}</summary>` +
      '<p>Boards that fail are retried every run three times, then after 1, 2, 4, 8 and at most 14 days; they’re never dropped for failing. A board that moved to another hiring system is replaced when the lists link to the new one.</p>' +
      (rep.length ? `<div class="tbl"><table><thead><tr><th scope="col">Repair queue</th><th scope="col">Failing since</th><th scope="col">Next try</th><th scope="col">Error</th><th scope="col"><span class="sr">Link</span></th></tr></thead><tbody>${rep.map(r => `<tr><td>${esc(r.name)}<br><span class="muted">${esc(r.kind)} · ${r.fails} failed runs · last worked ${esc(r.last_ok || 'never')}</span></td><td>${esc(r.since)}</td><td>${esc(r.next_try)}</td><td>${esc(r.error)}</td><td>${r.link ? `<a href="${esc(r.link)}" target="_blank" rel="noopener">Career site${ICON.ext}</a>` : ''}</td></tr>`).join('')}</tbody></table></div>` : '<p>Nothing in the repair queue.</p>') +
      ((dr.added || []).length ? `<h3>Added this run</h3><p>${dr.added.map(a => esc(a.name) + ' (' + esc(a.kind) + ', ' + esc(a.via) + ')').join('; ')}</p>` : '') +
      ((dr.moved || []).length ? `<h3>Moved or covered elsewhere</h3><p>${dr.moved.map(m => esc(m.name) + (m.moved_to ? ' → ' + esc(m.moved_to) : ' (another board covers it)')).join('; ')}</p>` : '') +
      ((dr.candidates || []).length ? `<h3>Candidate boards waiting to be validated (${dr.candidates.length})</h3><p>${dr.candidates.slice(0, 25).map(r => esc(r.name)).join(', ')}</p>` : '') +
      ((dr.unsupported || []).length ? `<h3>Hiring systems the scan can't read yet</h3><p>${dr.unsupported.map(u => `${esc(u.host)} (${u.count}: ${esc(u.companies.join(', '))})`).join('; ')}</p>` : '') +
      (dr.probed ? `<p>Name lookups: ${dr.probed.done} of ${dr.probed.names} names checked on Greenhouse, Lever, Ashby, SmartRecruiters and Workable so far; ${dr.probed.found} had a board.</p>` : '') + '</details>';
  }
  const au = D.audit || {};
  if(au.audits){
    const pct = au.in_scope ? Math.round(100 * au.found / au.in_scope) : null;
    h += `<details><summary>Coverage audit: ${au.found} of ${au.in_scope} in-scope listings found${pct !== null ? ' (' + pct + '%)' : ''} on ${au.boards} boards since ${esc(fmt(au.since))}</summary>` +
      `<p>Each run, a few boards are re-read as completely as the site allows (Workday sites in full) and every internship there that passes the same basic checks and the ${D.max_age}-day limit is looked up on this page. This measures the audited boards only, not every employer.</p>` +
      `<p>Misses by where they were lost: ${Object.entries(au.by_category || {}).map(([k, v]) => k + ' ' + v).join(', ') || 'none'}.</p>` +
      ((au.recent_misses || []).length ? `<div class="tbl"><table><thead><tr><th scope="col">Missed listing</th><th scope="col">Lost at</th><th scope="col">Why</th></tr></thead><tbody>${au.recent_misses.map(m => `<tr><td><a href="${esc(m.url)}" target="_blank" rel="noopener">${esc(m.title)}</a><br><span class="muted">${esc(m.source)} · audited ${esc(m.date)}</span></td><td>${esc(m.category)}</td><td>${esc(m.why)}</td></tr>`).join('')}</tbody></table></div>` : '') + '</details>';
  }
  const rj = D.rejections || {};
  if(Object.keys(rj).length){
    h += `<details><summary>What the filters dropped this run (${nf(D.read || 0)} postings read)</summary>` +
      Object.entries(rj).filter(([, v]) => Object.keys(v).length).map(([stage, v]) => `<h3>${esc(stage)}</h3><p>${Object.entries(v).map(([r, n]) => esc(r) + ': ' + n).join(' · ')}</p>`).join('') +
      '<p>Examples of each are saved in data/rejections.json.</p></details>';
  }
  h += `<details id="srcAll"><summary>All ${nf(D.sources.length)} sources checked on this run</summary><div class="tbl" id="srcTbl"></div></details>`;
  if(D.digest) h += `<p class="small muted" style="margin-top:16px">Daily digest: ${esc(D.digest.status)}.</p>`;
  h += '<p class="small muted">Fit scores are keyword-based estimates. Always read the posting before applying.</p>';
  $('dsBody').innerHTML = h;
  $('srcAll').addEventListener('toggle', () => {
    if(!$('srcAll').open || $('srcTbl').firstChild) return;
    $('srcTbl').innerHTML = '<table><thead><tr><th scope="col">Source</th><th scope="col">Type</th><th scope="col">Result</th><th scope="col">Last worked</th></tr></thead><tbody>' + D.sources.map(s =>
      `<tr><td>${s.careers ? `<a href="${esc(s.careers)}" target="_blank" rel="noopener">${esc(s.name)}</a>` : esc(s.name)}</td><td>${esc(s.kind)}</td><td class="${s.ok && s.complete !== false ? '' : 'c-failed'}">${s.ok ? nf(s.count) + ' postings read' + (s.complete === false ? ' (partial: ' + esc((s.notes || []).join('; ')) + ')' : '') : 'Failed: ' + esc(s.error)}</td><td>${esc(fmtT(s.last_success))}</td></tr>`).join('') + '</tbody></table>';
  });
}
function bars(list, color){
  if(!list.length) return '<p class="small muted">Not enough descriptions in these results yet.</p>';
  return list.map(g => `<div class="bar"><span>${esc(g.name)}</span><i aria-hidden="true"><span style="width:${g.pct}%;background:${color}"></span></i><em>${g.pct}%</em></div>`).join('');
}
function topSkills(jobs, field){
  const n = {};
  for(const j of jobs) for(const s of j[field]) n[s] = (n[s] || 0) + 1;
  return Object.entries(n).sort((a, b) => b[1] - a[1]).slice(0, 8).map(([name, v]) => ({name, pct: Math.round(100 * v / jobs.length)}));
}
function openInsights(trigger){
  const withDesc = curBrowse.filter(j => j.has_description);
  $('insBody').innerHTML = `<p class="small muted">What the ${nf(withDesc.length)} listings with a full description ask for, out of the ${plural(curBrowse.length, 'result')} currently shown in ${esc(VIEWS[ui.view].name)}. Change the filters to compare.</p>` +
    `<h3>Your skills that come up most</h3>${bars(topSkills(withDesc, 'matched'), 'var(--pos)')}<h3>Skills not on your resume yet</h3>${bars(topSkills(withDesc, 'gaps'), 'var(--warn)')}`;
  openSheet($('insDlg'), trigger);
}

// ---------- job details
let detailKey = null, navList = [], navCtx = 'browse', ignorePop = false;
const dlg = $('detail');
const QS = {met:['Met', ICON.check], partial:['Partly met', '<span class="qg" aria-hidden="true">~</span>'], missing:['Missing', ICON.x],
  check:['Check yourself', '<span class="qg" aria-hidden="true">?</span>'], soft:['Not scored', '<span class="qg" aria-hidden="true">·</span>']};
const num = x => Number.isInteger(x) ? x : Number(x).toFixed(1);
function qualBlock(rows, kind, s){
  const tot = kind === 'required' ? s && s.required_checked : s && s.preferred_total;
  const met = kind === 'required' ? s && s.required_met : s && s.preferred_met;
  if(rows && rows.length){
    const n = st => rows.filter(r => r.status === st).length;
    const m = n('met'), pa = n('partial'), mi = n('missing'), ch = n('check'), scored = m + pa + mi;
    let sum = scored ? `You meet ${m} of the ${scored} ${kind} qualifications the scan could check` + (pa ? ` and partly meet ${pa} more` : '') + '.' : `None of the ${kind} qualifications could be checked automatically.`;
    if(ch) sum += ` ${ch} to confirm yourself.`;
    return `<p>${esc(sum)}</p><ul class="ql">${rows.map(r => { const q = QS[r.status] || QS.soft;
      return `<li class="q-${esc(r.status)}"><span class="qs">${q[1]}${q[0]}</span><span>${esc(r.text)}${r.why ? `<small>${esc(r.why)}</small>` : r.status === 'check' ? '<small>Couldn’t be checked automatically</small>' : ''}</span></li>`; }).join('')}</ul>`;
  }
  if(tot) return `<p>About ${num(met)} of ${tot} ${kind} qualifications met (partial matches count as half). The item-by-item list isn't kept on this page for listings outside the curated sections; read it on the original posting.</p>`;
  return '<p class="small muted">None listed in the description, or none could be extracted.</p>';
}
function detailHTML(j){
  const [tk, tr] = trackFor(j, navCtx === 'browse');
  const st = status[j.key], pl = placesOf(j), term = termOf(j, tr), w = whenOf(j), dk = dateKind(j);
  const q = j.quals, s = q && q.summary, req = (q && q.required) || [], pref = (q && q.preferred) || [];
  const warn = j.flags.filter(f => f.kind === 'warn'), info = j.flags.filter(f => f.kind === 'info'), good = j.flags.filter(f => f.kind === 'good');
  let h = `<p class="d-co">${esc(coName(j))}</p><h2 class="d-title" id="dTitle" tabindex="-1">${esc(j.title)}</h2>` +
    `<p class="d-meta">${[pl.length ? esc(locShort(pl)) : '<span class="unk">Location not listed</span>', term.known ? esc(term.text) : `<span class="unk">${esc(term.text)}</span>`, esc(w.text)].join(' · ')}</p>`;
  h += `<div class="d-acts">${applyHTML(j, '')}` +
    `<button type="button" class="btn save" data-dact="saved" aria-pressed="${st === 'saved'}">${ICON.star}${st === 'saved' ? 'Saved' : 'Save'}</button>` +
    `<button type="button" class="btn" data-dact="applied" aria-pressed="${st === 'applied'}">${CB}Applied</button>` +
    `<button type="button" class="btn" data-dact="dismissed">${st === 'dismissed' ? 'Restore' : 'Dismiss'}</button>` +
    (st ? '' : `<button type="button" class="btn" data-dact="unread">${isUnread(j) ? 'Mark as read' : 'Mark as unread'}</button>`) + '</div>';
  h += st ? `<p class="d-state">${st === 'applied' ? 'Marked as applied' : st === 'saved' ? 'Saved' : 'Dismissed'}${activity[j.key] && activity[j.key].at ? ' on ' + esc(fmtY(activity[j.key].at)) : ''}. Stored in this browser only.</p>`
    : '<p class="d-state">Opening Apply doesn’t mark a job as applied; select Applied once you’ve submitted.</p>';
  if(j.lead) h += `<div class="callout">${ICON.warn}<p><b>Unverified lead.</b> Found only on ${esc(j.source)}, which doesn't link to the employer. Find posting searches the web for the company's own listing; confirm it exists before applying.</p></div>`;
  if(j.stale) h += `<div class="callout">${ICON.warn}<p><b>Not re-checked since ${esc(fmtY(j.stale.since))}.</b> It wasn't seen on the latest scan because ${esc(j.stale.why)}. It may have closed.</p></div>`;
  // Summary
  h += '<section class="dsec"><h3>Summary</h3>' + (j.ai ? `<p><b>Claude's take (${esc(j.ai.fit)}):</b> ${esc(j.ai.summary)}</p>${j.ai.talking_point ? `<p><b>Lead with:</b> ${esc(j.ai.talking_point)}</p>` : ''}` : '') +
    `<p class="small muted">${j.has_description ? 'The full job description isn’t stored on this page. Read it on the original posting before applying.' : 'The scan couldn’t load this posting’s full description, so skills, qualifications and eligibility couldn’t be checked. Read it on the original posting.'}</p></section>`;
  // Eligibility, kept apart from skill fit
  let e = '';
  if(warn.length) e += '<ul class="bl">' + warn.map(f => `<li class="cn">${ICON.warn}<span><b>${esc(concernText(f.label))}.</b> ${esc(concernWhy(f.label))}</span></li>`).join('') + '</ul>';
  if(good.length) e += '<ul class="bl">' + good.map(f => `<li class="ok">${ICON.check}<span>${esc(f.label)}</span></li>`).join('') + '</ul>';
  if(info.length) e += `<p>Mentioned in the posting: ${info.map(f => esc(f.label)).join(', ')}.</p>`;
  if(!e) e = `<p>${j.has_description ? 'No class-year, graduation, GPA, citizenship or clearance requirements were detected. Confirm on the posting.' : 'Not checked: the description wasn’t loaded.'}</p>`;
  h += `<section class="dsec"><h3>Eligibility</h3>${e}<p class="small muted">Checked separately from skill fit, so a strong match can still have a restriction.</p></section>`;
  // Why it matches
  const why = [];
  if(j.matched.length) why.push(`<li class="ok">${ICON.check}<span><b>Skills from your resume it asks for:</b> ${esc(j.matched.join(', '))}</span></li>`);
  if(j.related.length) why.push(`<li class="ok">${ICON.check}<span><b>Transferable:</b> ${esc(j.related.join(', '))}</span></li>`);
  const metQ = req.concat(pref).filter(r => r.status === 'met');
  if(metQ.length) why.push(`<li class="ok">${ICON.check}<span><b>Qualifications you meet:</b> ${metQ.length} (listed below)</span></li>`);
  h += `<section class="dsec"><h3>Why it matches your background</h3><p>${fitHTML(tr)} <span class="muted">· estimated ${tr.score} of 100, scored for ${esc(secName(tk))}</span></p>` +
    (why.length ? `<ul class="bl">${why.join('')}</ul>` : '<p class="small muted">No specific resume skills were matched.</p>') + '</section>';
  // Missing and uncertain
  const miss = [];
  if(j.gaps.length) miss.push(`<li class="no">${ICON.x}<span><b>Not on your resume yet:</b> ${esc(j.gaps.join(', '))}</span></li>`);
  const lack = req.map(r => [r, 'required']).concat(pref.map(r => [r, 'preferred'])).filter(([r]) => r.status === 'missing' || r.status === 'partial');
  if(lack.length) miss.push(`<li class="no">${ICON.x}<span><b>Qualifications you don't fully show:</b><ul>${lack.map(([r, k]) => `<li>${esc(r.text)} <span class="muted">(${k}${r.status === 'partial' ? ', partly met' : ''})</span></li>`).join('')}</ul></span></li>`);
  const chk = req.concat(pref).filter(r => r.status === 'check').length || (s && !req.length && !pref.length ? s.to_check || 0 : 0);
  if(chk) miss.push(`<li><span class="qg" aria-hidden="true">?</span><span><b>${plural(chk, 'qualification')} to confirm yourself.</b> The scan couldn't check ${chk === 1 ? 'it' : 'them'} automatically.</span></li>`);
  for(const u of j.uncertain || []) miss.push(`<li><span class="qg" aria-hidden="true">?</span><span><b>Uncertain:</b> ${esc(u)}</span></li>`);
  if(dk === 'none') miss.push('<li><span class="qg" aria-hidden="true">?</span><span><b>Posting date unknown.</b> Neither the employer nor any list the scan reads gives one.</span></li>');
  if(!term.known) miss.push('<li><span class="qg" aria-hidden="true">?</span><span><b>Term not stated</b> in the title or description.</span></li>');
  if(!pl.length) miss.push('<li><span class="qg" aria-hidden="true">?</span><span><b>Location not listed</b> by the source.</span></li>');
  h += `<section class="dsec"><h3>Missing requirements and uncertainties</h3>${miss.length ? `<ul class="bl">${miss.join('')}</ul>` : '<p class="small muted">Nothing flagged.</p>'}</section>`;
  h += `<section class="dsec"><h3>Required qualifications</h3>${qualBlock(req, 'required', s)}</section>`;
  h += `<section class="dsec"><h3>Preferred qualifications</h3>${qualBlock(pref, 'preferred', s)}</section>`;
  // Fit estimate details
  const p = tr.parts || {}, fitName = tk === 'summer' ? 'Aerospace fit' : 'Engineering fit';
  const parts = p.preferred !== undefined ? [['Preferred qualifications', p.preferred, 40], ['Required qualifications', p.required, 25], [fitName, p.fit, 20], ['Eligibility', p.eligibility, 15]]
    : [[fitName, p.fit, 40], ['Skills', p.skills, 35], ['Eligibility', p.eligibility, 25]];
  if(p.requirements) parts.push(['Missing required qualifications', p.requirements, null]);
  const others = Object.entries(j.tracks).filter(([k]) => k !== tk).map(([k, t]) => `${esc(secName(k))}: ${t.score} (${TIERL[t.tier]})`);
  const missT = Object.entries(j.misses || {}).filter(([t]) => T[t]).map(([t, why]) => `${esc(secName(t))}: ${esc(why)}`);
  h += `<section class="dsec"><h3>How the fit estimate adds up</h3><p class="small muted">A keyword comparison between the posting and your resume. It's an estimate, not a prediction of how an employer will read your application.</p>` +
    `<dl class="kv"><dt>Total, ${esc(secName(tk))}</dt><dd><b>${tr.score}</b> of 100 · ${TIERL[tr.tier]}</dd>${parts.map(([n, v, o]) => `<dt>${esc(n)}</dt><dd>${v === undefined ? '–' : v}${o ? ' of ' + o : ''}</dd>`).join('')}` +
    (others.length ? `<dt>Other sections</dt><dd>${others.join('<br>')}</dd>` : '') + (missT.length ? `<dt>Not included in</dt><dd>${missT.join('<br>')}</dd>` : '') + '</dl></section>';
  // Dates, kept apart
  const posted = dk === 'employer' ? `${esc(fmtY(j.posted))} <span class="muted">(from the employer)</span>`
    : dk === 'listing' ? `${esc(fmtY(j.posted))} <span class="muted">(from ${esc(j.posted_from || 'an internship list')}; the employer's own date isn't known)</span>`
    : '<span class="unk">Not provided</span>';
  h += `<section class="dsec"><h3>Dates</h3><dl class="kv"><dt>Posting date</dt><dd>${posted}</dd>` +
    `<dt>First found by the scanner</dt><dd>${esc(j.found_at ? fmtT(j.found_at) : fmtY(j.first_seen))} <span class="muted">(discovery date, not a posting date)</span></dd>` +
    (j.checked ? `<dt>Last confirmed on its source</dt><dd>${esc(fmtT(j.checked))}</dd>` : '') +
    `<dt>${D.max_age}-day window</dt><dd>Counted from ${dk === 'none' ? 'the day it was first found' : 'the posting date above'}</dd></dl></section>`;
  // Source and original values
  let host = ''; try { host = new URL(j.url).hostname.replace(/^www\./, ''); } catch(err){ host = j.url; }
  const rows = [`<dt>Original posting</dt><dd><a href="${esc(j.url)}" target="_blank" rel="noopener">${esc(host)}${ICON.ext}<span class="sr"> (opens in a new tab)</span></a><br><span class="small muted">${esc(j.url)}</span></dd>`,
    `<dt>Found via</dt><dd>${esc(j.source)}</dd>`];
  if(j.discipline) rows.push(`<dt>Field</dt><dd>${esc(j.discipline)}</dd>`);
  if(pl.length > 1) rows.push(`<dt>Locations (${pl.length})</dt><dd>${pl.map(x => esc(x.label)).join('<br>')}</dd>`);
  if(j.location && j.location.trim() !== pl.map(x => x.label).join('; ')) rows.push(`<dt>Location as listed</dt><dd>${esc(j.location)}</dd>`);
  const d = distOf(j); if(d) rows.push(`<dt>Distance</dt><dd>${esc(d)}${(j.geo || {}).approx ? ' (approximate)' : ''}</dd>`);
  if(coName(j) !== j.company) rows.push(`<dt>Company as listed</dt><dd>${esc(j.company)}</dd>`);
  h += `<section class="dsec"><h3>Source</h3><dl class="kv">${rows.join('')}</dl></section>`;
  return h;
}
function renderDetail(){
  const j = byKey.get(detailKey); if(!j) return;
  const i = navList.findIndex(x => x.key === detailKey);
  $('dBody').innerHTML = detailHTML(j);
  $('dPos').textContent = i >= 0 ? `${nf(i + 1)} of ${nf(navList.length)}` : '';
  dlg.querySelector('[data-nav="-1"]').disabled = i <= 0;
  dlg.querySelector('[data-nav="1"]').disabled = i < 0 || i >= navList.length - 1;
}
function openDetail(j, ctx, keepNav){
  navCtx = ctx;
  // Previous/Next walk the list as it was when the panel opened, even when reading a listing drops it from "Unread only"
  if(!keepNav || !dlg.open) navList = (ctx === 'leads' ? curLeads : ctx === 'mine' ? curMine : curBrowse).slice();
  detailKey = j.key; lastOpen = j.key;
  if(isUnread(j)) markRead(j.key);   // opening it counts as reviewing it
  renderDetail();
  if(!dlg.open){ dlg.showModal(); history.pushState({ajfDetail: j.key}, ''); }
  else history.replaceState({ajfDetail: j.key}, '');
  $('dBody').scrollTop = 0;
  $('dTitle').focus();
  refresh(true);
}
function stepDetail(d){
  const i = navList.findIndex(x => x.key === detailKey), n = navList[i + d];
  if(i < 0 || !n) return;
  openDetail(n, navCtx, true);
  const row = document.querySelector(`.job[data-key="${CSS.escape(n.key)}"]`);
  if(row) row.scrollIntoView({block: 'nearest'});
}
function closeDetail(){ if(dlg.open) dlg.close(); }
dlg.addEventListener('close', () => {
  if(history.state && history.state.ajfDetail){ ignorePop = true; history.back(); }
  const key = detailKey; detailKey = null;
  if(!focusRow(key)){ const i = navList.findIndex(x => x.key === key);
    if(!navList.slice(i + 1).concat(navList.slice(0, Math.max(0, i)).reverse()).some(x => focusRow(x.key))) ($('rcount') || $('main')).focus(); }
});
addEventListener('popstate', () => {
  if(ignorePop){ ignorePop = false; return; }
  if(dlg.open && !(history.state && history.state.ajfDetail)) dlg.close();
});
dlg.addEventListener('click', e => {
  if(e.target === dlg) return closeDetail();
  const b = e.target.closest('button,a'); if(!b) return;
  if(b.matches('[data-close]')) return closeDetail();
  if(b.dataset.nav) return stepDetail(+b.dataset.nav);
  const j = byKey.get(detailKey); if(!j) return;
  if(b.dataset.act === 'apply'){ markRead(j.key); return; }
  const a = b.dataset.dact; if(!a) return;
  if(a === 'unread'){ if(isUnread(j)) markRead(j.key); else markUnread(j.key); }
  else if(a === 'dismissed' && status[j.key] !== 'dismissed'){
    const prev = change(j, 'dismissed'); closeDetail(); refresh();
    toast(`Dismissed “${short(j.title)}”.`, () => undo(prev)); return;
  } else change(j, a);
  renderDetail(); refresh(true);
  const again = dlg.querySelector(`[data-dact="${a}"]`); if(again) again.focus();
  say(a === 'saved' ? (status[j.key] === 'saved' ? 'Saved.' : 'Removed from saved.') : a === 'applied' ? (status[j.key] === 'applied' ? 'Marked as applied.' : 'No longer marked as applied.')
    : a === 'dismissed' ? 'Restored.' : isUnread(j) ? 'Marked as unread.' : 'Marked as read.');
});

// ---------- sheets, menus, toast
let sheetTrigger = new Map();
function openSheet(d, trigger){
  sheetTrigger.set(d, trigger || document.activeElement);
  d.showModal();
  const h = d.querySelector('h2[tabindex]'); if(h) h.focus();
}
for(const d of [$('filtDlg'), $('dsDlg'), $('insDlg')]){
  d.addEventListener('click', e => { if(e.target === d || e.target.closest('[data-close]')) d.close(); });
  d.addEventListener('close', () => { const t = sheetTrigger.get(d); if(t && t.isConnected) t.focus(); });
}
function openStatus(trigger){ renderStatusBody(); openSheet($('dsDlg'), trigger); }

let menuOpen = null;
function openMenu(m, trigger){
  closeMenu();
  m.hidden = false;
  const r = trigger.getBoundingClientRect(), w = m.offsetWidth, h = m.offsetHeight;
  m.style.left = Math.max(8, Math.min(r.right - w, innerWidth - w - 8)) + 'px';
  m.style.top = (r.bottom + 4 + h > innerHeight - 8 ? Math.max(8, r.top - h - 4) : r.bottom + 4) + 'px';
  trigger.setAttribute('aria-expanded', 'true');
  menuOpen = {el: m, trigger};
  const first = m.querySelector('[role^=menuitem]'); if(first) first.focus();
}
function closeMenu(refocus){
  if(!menuOpen) return;
  const {el, trigger} = menuOpen; menuOpen = null;
  el.hidden = true; trigger.setAttribute('aria-expanded', 'false');
  if(refocus && trigger.isConnected) trigger.focus();
}
function menuKeys(e){
  if(!menuOpen) return;
  const its = [...menuOpen.el.querySelectorAll('[role^=menuitem]')], i = its.indexOf(document.activeElement);
  const go = n => { e.preventDefault(); its[(n + its.length) % its.length].focus(); };
  if(e.key === 'ArrowDown') go(i + 1); else if(e.key === 'ArrowUp') go(i - 1); else if(e.key === 'Home') go(0); else if(e.key === 'End') go(its.length - 1);
  else if(e.key === 'Escape'){ e.preventDefault(); e.stopPropagation(); closeMenu(true); }
  else if(e.key === 'Tab') closeMenu(false);
}
$('setMenu').addEventListener('keydown', menuKeys);
$('rowMenu').addEventListener('keydown', menuKeys);
document.addEventListener('pointerdown', e => { if(menuOpen && !menuOpen.el.contains(e.target) && !menuOpen.trigger.contains(e.target)) closeMenu(); });
addEventListener('resize', () => closeMenu());
addEventListener('scroll', () => { if(menuOpen) closeMenu(); }, {passive: true});
function renderSetMenu(){
  $('setMenu').innerHTML = '<div class="mh" id="thmL">Theme</div><div role="group" aria-labelledby="thmL">' +
    Object.entries(THEMES).map(([k, n]) => `<button type="button" role="menuitemradio" aria-checked="${k === theme}" data-theme="${k}"><span class="rd">${ICON.check}</span>${n}</button>`).join('') +
    '</div><div role="separator"></div><button type="button" role="menuitem" data-m="status">Data status</button>' +
    '<button type="button" role="menuitem" data-m="markall">Mark everything as read</button><div role="separator"></div>' +
    '<button type="button" role="menuitem" data-m="export">Export my saved and applied data</button><button type="button" role="menuitem" data-m="import">Import data…</button>';
}
$('setBtn').addEventListener('click', () => { if(menuOpen && menuOpen.el === $('setMenu')) return closeMenu(true); renderSetMenu(); openMenu($('setMenu'), $('setBtn')); });
$('setMenu').addEventListener('click', e => {
  const t = e.target.closest('[data-theme]');
  if(t){ theme = t.dataset.theme; sset('ajf-theme', theme); applyTheme(); closeMenu(true); say(`Theme: ${THEMES[theme]}.`); return; }
  const b = e.target.closest('[data-m]'); if(!b) return;
  closeMenu(true); command(b.dataset.m, $('setBtn'));
});
function command(m, trigger){
  if(m === 'status') return openStatus(trigger);
  if(m === 'markall'){
    unread = {since: D.updated || new Date().toISOString(), read: unread.read, force: {}}; jset('ajf-unread', unread);
    refresh(); say('Everything is marked as read.'); return;
  }
  if(m === 'export'){
    const blob = new Blob([JSON.stringify({app:'aero-job-finder', version:1, exported:new Date().toISOString(), status, activity, unread}, null, 1)], {type:'application/json'});
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob); a.download = `aero-job-finder-${D.today}.json`;
    document.body.appendChild(a); a.click(); a.remove();
    toast('Exported your saved, applied and read data as a file.'); return;
  }
  if(m === 'import') return $('importFile').click();
}
$('importFile').addEventListener('change', e => {
  const f = e.target.files[0]; if(!f) return;
  f.text().then(t => {
    const d = JSON.parse(t);
    if(d.app !== 'aero-job-finder') throw new Error('this file isn’t an export from this page');
    status = Object.assign({}, status, d.status || {}); activity = Object.assign({}, activity, d.activity || {});
    if(d.unread){ unread.read = Object.assign({}, unread.read, d.unread.read || {}); if(d.unread.since > unread.since) unread.since = d.unread.since; }
    jset('ajf-status', status); jset('ajf-activity', activity); jset('ajf-unread', unread);
    refresh(); toast(`Imported ${plural(Object.keys(d.status || {}).length, 'status', 'statuses')}. Nothing was deleted.`);
  }).catch(err => toast('Import failed: ' + err.message));
  e.target.value = '';
});
function openRowMenu(j, btn){
  if(menuOpen && menuOpen.trigger === btn) return closeMenu(true);
  const st = status[j.key], m = $('rowMenu');
  m.innerHTML = '<button type="button" role="menuitem" data-m="open">View details</button>' +
    `<button type="button" role="menuitem" data-m="applied">${st === 'applied' ? 'Unmark as applied' : 'Mark as applied'}</button>` +
    (st ? '' : `<button type="button" role="menuitem" data-m="read">${isUnread(j) ? 'Mark as read' : 'Mark as unread'}</button>`) +
    `<div role="separator"></div><button type="button" role="menuitem" data-m="dismissed">${st === 'dismissed' ? 'Restore' : 'Dismiss'}</button>`;
  m.dataset.key = j.key;
  m.setAttribute('aria-label', `Actions for ${j.title}`);
  openMenu(m, btn);
}
$('rowMenu').addEventListener('click', e => {
  const b = e.target.closest('[data-m]'); if(!b || !menuOpen) return;
  const key = $('rowMenu').dataset.key, j = byKey.get(key), trig = menuOpen.trigger;
  closeMenu(true);
  const a = b.dataset.m;
  if(a === 'open') return openDetail(j, ctxOf(trig));
  if(a === 'read'){ if(isUnread(j)) markRead(key); else markUnread(key); refresh(); say(isUnread(j) ? 'Marked as unread.' : 'Marked as read.'); return; }
  const prev = change(j, a);
  refresh();
  if(status[key] === 'dismissed') toast(`Dismissed “${short(j.title)}”.`, () => undo(prev));
  else if(status[key] === 'applied') toast(`Marked “${short(j.title)}” as applied.`, () => undo(prev));
  else say(a === 'dismissed' ? 'Restored.' : 'No longer marked as applied.');
});
const short = s => s.length > 48 ? s.slice(0, 46).trim() + '…' : s;
const say = msg => { $('live').textContent = ''; setTimeout(() => { $('live').textContent = msg; }, 30); };
let toastT = null, toastUndo = null;
function toast(msg, undoFn){
  const t = $('toast');
  toastUndo = undoFn || null;
  t.innerHTML = `<span>${esc(msg)}</span>` + (undoFn ? '<button type="button" class="tb" data-undo>Undo</button>' : '') + `<button type="button" class="x" data-x aria-label="Close notification">${ICON.x}</button>`;
  t.hidden = false;
  say(msg + (undoFn ? ' Press Control+Z or use the Undo button to undo.' : ''));
  clearTimeout(toastT); toastT = setTimeout(hideToast, 8000);
}
function hideToast(){ $('toast').hidden = true; toastUndo = null; }
$('toast').addEventListener('click', e => {
  if(e.target.closest('[data-undo]') && toastUndo){ const u = toastUndo; hideToast(); u(); }
  else if(e.target.closest('[data-x]')) hideToast();
});
$('toast').addEventListener('mouseenter', () => clearTimeout(toastT));
$('toast').addEventListener('focusin', () => clearTimeout(toastT));
$('toast').addEventListener('mouseleave', () => { toastT = setTimeout(hideToast, 4000); });

// ---------- shared row events
const ctxOf = el => (el.closest('[data-ctx]') || {dataset: {ctx: 'browse'}}).dataset.ctx;
function focusRow(key, sel){
  if(!key) return false;
  const row = document.querySelector(`.job[data-key="${CSS.escape(key)}"]`);
  const el = row && row.querySelector(sel || '.t');
  if(el){ el.focus(); return true; }
  return false;
}
// Re-render the section in view, keeping keyboard focus on the same row (or the next one when it left the list)
function refresh(quiet){
  const a = document.activeElement, row = a && a.closest && a.closest('.job');
  const key = row && row.dataset.key, act = a && a.dataset && a.dataset.act;
  const keys = row ? [...row.parentNode.querySelectorAll('.job')].map(r => r.dataset.key) : null;
  renderCounts();
  if(ui.section === 'browse') renderBrowse();
  else if(ui.section === 'outlook') renderOut();
  else renderMine();
  if(quiet || !key || document.contains(a)) return;
  if(focusRow(key, act ? `[data-act="${act}"]` : '.t')) return;
  const i = keys.indexOf(key);
  if(!keys.slice(i + 1).concat(keys.slice(0, i).reverse()).some(k => focusRow(k))) ($('rcount') || $('main')).focus();
}
function onList(e){
  const row = e.target.closest('.job'); if(!row) return;
  const j = byKey.get(row.dataset.key); if(!j) return;
  const el = e.target.closest('a,button');
  if(el){
    const a = el.dataset.act;
    if(a === 'apply'){ if(isUnread(j)){ markRead(j.key); setTimeout(() => refresh(), 0); } return; }
    if(a === 'open') return openDetail(j, ctxOf(row));
    if(a === 'save'){ change(j, 'saved'); refresh(); say(status[j.key] === 'saved' ? 'Saved.' : 'Removed from saved.'); return; }
    if(a === 'menu') return openRowMenu(j, el);
    return;
  }
  if(String(getSelection ? getSelection() : '').length) return;   // selecting text isn't a click
  row.querySelector('.t').focus({preventScroll: true});
  openDetail(j, ctxOf(row));
}
for(const id of ['results', 'mineList', 'leadList']) $(id).addEventListener('click', onList);

// ---------- counts in the header, sections
function renderCounts(){
  const n = s => D.jobs.filter(j => status[j.key] === s).length;
  $('nSaved').textContent = n('saved') || ''; $('nApplied').textContent = n('applied') || '';
  $('navBrowse').href = $('brand').href = '#' + VIEW_HASH[ui.view];
  $('navOut').href = '#' + OUT_HASH[ui.out];
  document.querySelectorAll('#nav a').forEach(a => a.dataset.sec === ui.section ? a.setAttribute('aria-current', 'page') : a.removeAttribute('aria-current'));
}
const TITLES = {browse: 'Internships', saved: 'Saved', applied: 'Applied', outlook: 'Outlook'};
function showSection(){
  closeMenu();
  $('browseView').hidden = ui.section !== 'browse';
  $('mineView').hidden = ui.section !== 'saved' && ui.section !== 'applied';
  $('outView').hidden = ui.section !== 'outlook';
  document.title = `${TITLES[ui.section]} · Aero Job Finder`;
  renderCounts();
  if(ui.section === 'browse') renderBrowse();
  else if(ui.section === 'outlook') renderOut();
  else renderMine();
  syncHash(); saveUI();
}
function toResults(){
  const y = $('viewTabs').getBoundingClientRect().bottom + scrollY;
  if(scrollY > y) scrollTo(0, y);
}
function onFilter(){ limit = PAGE; saveUI(); renderBrowse(); toResults(); }
function debounce(fn, ms){ let t; return (...a) => { clearTimeout(t); t = setTimeout(() => fn(...a), ms); }; }
function clearFilter(k){
  if(k === 'all'){ ui.f = Object.assign({}, F0); ui.unreadOnly = false; $('q').value = ''; }
  else if(k === 'unread') ui.unreadOnly = false;
  else if(k === 'preset') applyPreset('');
  else { ui.f[k] = ''; if(k === 'q') $('q').value = ''; }
  onFilter();
  if(!$('filtDlg').open) $('rcount').focus();
  say(k === 'all' ? 'All filters cleared.' : 'Filter removed.');
}
document.addEventListener('change', e => {
  const el = e.target;
  if(el.matches('[data-f]')){ ui.f[el.dataset.f] = el.value; onFilter(); }
  else if(el.matches('[data-sort]')){ ui.sort[ui.view] = el.value; onFilter(); }
});
$('q').addEventListener('input', debounce(() => { ui.f.q = $('q').value.trim(); onFilter(); }, 150));
$('q').addEventListener('keydown', e => { if(e.key === 'Escape' && $('q').value){ e.preventDefault(); $('q').value = ''; ui.f.q = ''; onFilter(); } });
document.addEventListener('click', e => {
  const c = e.target.closest('[data-clear]');
  if(c){ clearFilter(c.dataset.clear); return; }
  const m = e.target.closest('[data-more]');
  if(m){
    const kind = m.dataset.more, listId = kind === 'browse' ? 'results' : kind === 'leads' ? 'leadList' : 'plist';
    const before = $(listId).querySelectorAll('.job,.item').length;
    if(kind === 'browse'){ limit += PAGE; renderBrowse(); } else if(kind === 'leads'){ leadLimit += PAGE; renderLeads(); } else { pLimit += PAGE; renderPred(); }
    const next = $(listId).querySelectorAll('.job,.item')[before];
    if(next){ const f = next.querySelector('.t, a, button'); if(f) f.focus(); }
    return;
  }
  const cmd = e.target.closest('#mineView [data-m], #rhead [data-m]');
  if(cmd){ command(cmd.dataset.m, cmd); return; }
});
$('rhead').addEventListener('click', e => {
  if(e.target.closest('#unreadBtn')){ ui.unreadOnly = !ui.unreadOnly; onFilter(); $('unreadBtn').focus(); return; }
  if(e.target.closest('#insBtn')) openInsights($('insBtn'));
});
$('presets').addEventListener('click', e => {
  const b = e.target.closest('[data-preset]'); if(!b) return;
  applyPreset(ui.f.preset === b.dataset.preset ? '' : b.dataset.preset); onFilter();
  const again = $('presets').querySelector(`[data-preset="${b.dataset.preset}"]`); if(again) again.focus();
});
$('viewTabs').addEventListener('click', e => { const b = e.target.closest('[data-view]'); if(!b || b.dataset.view === ui.view) return; ui.view = b.dataset.view; limit = PAGE; showSection(); toResults(); $('tab-' + ui.view).focus(); });
$('outTabs').addEventListener('click', e => { const b = e.target.closest('[data-out]'); if(!b || b.dataset.out === ui.out) return; ui.out = b.dataset.out; showSection(); $('otab-' + ui.out).focus(); });
// Arrow keys move between tabs (roving tabindex)
for(const id of ['viewTabs', 'outTabs']) $(id).addEventListener('keydown', e => {
  const tabs = [...$(id).querySelectorAll('[role=tab]')], i = tabs.indexOf(document.activeElement);
  if(i < 0) return;
  const n = e.key === 'ArrowRight' ? i + 1 : e.key === 'ArrowLeft' ? i - 1 : e.key === 'Home' ? 0 : e.key === 'End' ? tabs.length - 1 : null;
  if(n === null) return;
  e.preventDefault(); tabs[(n + tabs.length) % tabs.length].click();
});
$('moreBtn').addEventListener('click', () => openSheet($('filtDlg'), $('moreBtn')));
$('statBtn').addEventListener('click', () => openStatus($('statBtn')));
addEventListener('hashchange', () => { if(dlg.open) return; if(route(location.hash)){ limit = PAGE; showSection(); scrollTo(0, 0); } });
document.addEventListener('keydown', e => {
  const tag = (e.target.tagName || '').toLowerCase(), typing = tag === 'input' || tag === 'select' || tag === 'textarea' || e.target.isContentEditable;
  const mod = e.ctrlKey || e.metaKey || e.altKey;
  if(e.key === '/' && !typing && !mod && !document.querySelector('dialog[open]') && ui.section === 'browse'){ e.preventDefault(); $('q').focus(); $('q').select(); return; }
  if((e.key === 'z' || e.key === 'Z') && (e.ctrlKey || e.metaKey) && !typing && toastUndo){ e.preventDefault(); const u = toastUndo; hideToast(); u(); return; }
  if(dlg.open && !typing && !mod){ if(e.key === 'j') stepDetail(1); else if(e.key === 'k') stepDetail(-1); }
});

// ---------- footer and start
const okN = D.sources.filter(s => s.ok).length;
$('browseSub').textContent = D.sources.length ? `Engineering internships from the last ${D.max_age} days, found on ${nf(okN)} career sites and lists and scored against your resume.` : 'Waiting for the first scan.';
$('foot').textContent = `${nf(D.sources.length)} sources checked every 5 hours. Fit scores are keyword-based estimates. Always read the posting before applying.`;
renderStat();
// Come back to the same place after a reload (or after the browser drops the page while you're on a company's site)
const SKEY = 'ajf-scroll';
let back = null;
try { back = JSON.parse(sessionStorage.getItem(SKEY) || 'null'); } catch(err){}
if('scrollRestoration' in history) history.scrollRestoration = 'manual';
if(back && back.h === hashOf()){ limit = Math.max(PAGE, back.limit || PAGE); leadLimit = Math.max(PAGE, back.ll || PAGE); }
if(history.state && history.state.ajfDetail) history.replaceState(null, '');
showSection();
if(back && back.h === hashOf() && back.y) scrollTo(0, back.y);
const saveScroll = () => { try { sessionStorage.setItem(SKEY, JSON.stringify({h: hashOf(), y: Math.round(scrollY), limit, ll: leadLimit})); } catch(err){} };
addEventListener('pagehide', saveScroll);
addEventListener('scroll', debounce(saveScroll, 250), {passive: true});
}
})();
</script>
</body>
</html>
"""


def track_info(profile: dict) -> dict:
    """Names and one-line descriptions for each section (quick filters on the page), from profile.toml."""
    se, br, fa = profile["search"], profile.get("broad", {}), profile.get("fall", {})
    summer = f"{se.get('season', 'summer').title()} {se.get('year', 2027)}"
    info = {
        "summer": {"tab": summer, "season_label": summer,
                   "note": f"{summer} internships in aerospace and mechanical work at aerospace companies, "
                           "scored against your resume."},
        "broad": {"tab": "All engineering",
                  "season_label": f"{br.get('season', 'summer').title()} {br.get('year', 2027)}",
                  "note": "Every engineering internship found, from any company and any major. "
                          "Your resume's mechanical and aerospace skills push those to the top; use the Field filter to narrow it."},
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
                     f"January to April. Remove the {fall} term filter to see nearby postings that don't name a season.",
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
    for k in ("matched", "related", "gaps", "flags"):
        if not isinstance(out.get(k), list):
            out[k] = []
    if out.get("quals") and set(out["tracks"]) == {"all"}:
        out["quals"] = {"summary": out["quals"].get("summary"), "preferred": [], "required": []}
    return out


def _blob(data: dict) -> str:
    return json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")


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
    return TEMPLATE.replace("__DATA__", _blob(data))


DATA_RX = re.compile(r'<script id="data" type="application/json">(.*?)</script>', re.S)


def rebuild(page_in: Path, page_out: Path, profile: dict | None = None) -> None:
    """Re-render an already built page with the current template (no scan): takes the data
    embedded in page_in, refreshes the section texts from profile.toml when given, and writes page_out."""
    m = DATA_RX.search(page_in.read_text(encoding="utf-8"))
    if not m:
        raise ValueError(f"{page_in} has no embedded data")
    data = json.loads(m.group(1))
    if profile:
        data["tracks"] = track_info(profile)
    page_out.parent.mkdir(parents=True, exist_ok=True)
    page_out.write_text(TEMPLATE.replace("__DATA__", _blob(data)), encoding="utf-8")


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


if __name__ == "__main__":
    # python -m jobfinder.render [built page] [output]: preview the current template on the last scan's data
    root = Path(__file__).resolve().parent.parent
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else root / "docs" / "index.html"
    dst = Path(sys.argv[2]) if len(sys.argv) > 2 else root / "preview" / "index.html"
    prof = None
    try:
        import tomllib
        prof = tomllib.loads((root / "profile.toml").read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001 - the embedded section texts are fine too
        pass
    rebuild(src, dst, prof)
    print(f"Wrote {dst}")
