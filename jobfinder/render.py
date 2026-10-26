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
<title>Internship finder</title>
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🚀</text></svg>">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Barlow+Semi+Condensed:wght@500;600;700&family=Barlow:wght@400;500;600&display=swap" rel="stylesheet">
<style>
:root{
  --bg:#E6EBEF; --panel:#FFFFFF; --ink:#16212B; --muted:#56636F; --line:#C7D0D8;
  --strong:#1D7A4E; --good:#2B5C9C; --look:#94690F; --warn:#A3442D;
  --chip:#EEF2F5; --focus:#2B5C9C;
  --cond:"Barlow Semi Condensed","Arial Narrow",Arial,sans-serif;
  --body:Barlow,"Segoe UI",Roboto,Arial,sans-serif;
}
@media (prefers-color-scheme:dark){:root{
  --bg:#0F171E; --panel:#18232C; --ink:#E3E9EE; --muted:#93A1AD; --line:#2B3843;
  --strong:#4FBF88; --good:#6F9EE0; --look:#D9A93F; --warn:#E07A5F; --chip:#212E38; --focus:#6F9EE0;
}}
*{box-sizing:border-box}
[hidden]{display:none!important}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.5 var(--body)}
a{color:inherit}
:focus-visible{outline:2px solid var(--focus);outline-offset:2px}
.wrap{max-width:1040px;margin:0 auto;padding:28px 18px 64px}
header h1{font:700 clamp(28px,5vw,42px)/1.05 var(--cond);letter-spacing:-.01em;margin:0 0 8px}
header p{margin:0;color:var(--muted)}
.counts{display:flex;flex-wrap:wrap;gap:6px 18px;margin-top:14px;font:600 15px/1.3 var(--cond)}
.counts b{font-size:20px;margin-right:4px}
.tabs{display:flex;flex-wrap:wrap;gap:2px;margin-top:20px;border-bottom:1px solid var(--line)}
.tab{font:600 17px/1.2 var(--cond);padding:10px 14px 9px;border:0;border-bottom:3px solid transparent;background:none;color:var(--muted);white-space:nowrap;cursor:pointer}
.tab[aria-selected=true]{color:var(--ink);border-bottom-color:var(--ink)}
.tab span{display:inline-block;margin-left:6px;padding:1px 7px;border-radius:10px;background:var(--chip);font-size:13px;color:var(--muted)}
.tab[aria-selected=true] span{background:var(--ink);color:var(--bg)}
.tabnote{margin:10px 0 0;color:var(--muted);font-size:15px}
.controls{position:sticky;top:0;z-index:5;background:var(--bg);padding:12px 0;border-bottom:1px solid var(--line);display:grid;gap:10px}
.row{display:flex;flex-wrap:wrap;gap:8px;align-items:center}
input[type=search]{flex:1 1 240px;min-width:0;font:inherit;padding:9px 12px;border:1px solid var(--line);border-radius:6px;background:var(--panel);color:var(--ink)}
select{font:inherit;padding:8px 10px;border:1px solid var(--line);border-radius:6px;background:var(--panel);color:var(--ink)}
.seg{display:inline-flex;border:1px solid var(--line);border-radius:6px;overflow:hidden;background:var(--panel)}
.seg button{font:600 14px/1 var(--cond);padding:9px 12px;border:0;background:transparent;color:var(--muted);cursor:pointer}
.seg button[aria-pressed=true]{background:var(--ink);color:var(--bg)}
label.tog{display:inline-flex;gap:6px;align-items:center;font-size:14px;color:var(--muted);cursor:pointer}
.gapbox{margin:18px 0 6px;background:var(--panel);border:1px solid var(--line);border-radius:8px}
.gapbox summary{cursor:pointer;padding:12px 16px;font:600 17px/1.3 var(--cond)}
.gapbox .inner{padding:0 16px 16px;display:grid;gap:18px;grid-template-columns:repeat(auto-fit,minmax(280px,1fr))}
.gapbox h3{font:600 15px/1.3 var(--cond);margin:0 0 8px;color:var(--muted)}
.bar{display:grid;grid-template-columns:150px 1fr 40px;gap:8px;align-items:center;font-size:14px;margin:4px 0}
.bar i{display:block;height:8px;border-radius:4px;background:var(--line)}
.bar i span{display:block;height:100%;border-radius:4px}
.bar em{font-style:normal;color:var(--muted);text-align:right}
#list{display:grid;gap:10px;margin-top:16px}
.strip{display:grid;grid-template-columns:76px 1fr auto;background:var(--panel);border:1px solid var(--line);border-radius:8px;overflow:hidden}
.strip.done{opacity:.55}
.score{display:flex;flex-direction:column;align-items:center;justify-content:center;color:#fff;padding:10px 4px;font-family:var(--cond)}
.score b{font-size:30px;line-height:1}
.score small{font-size:12px;font-weight:600;opacity:.92;margin-top:2px;text-align:center}
.t-strong .score{background:var(--strong)} .t-good .score{background:var(--good)} .t-look .score{background:var(--look)}
@media (prefers-color-scheme:dark){.score{color:#0F171E}}
.main{padding:12px 16px;min-width:0}
.co{font:600 14px/1.3 var(--cond);color:var(--muted)}
.title{font:600 20px/1.2 var(--cond);margin:2px 0 4px}
.meta{font-size:14px;color:var(--muted);display:flex;flex-wrap:wrap;gap:2px 14px}
.chips{display:flex;flex-wrap:wrap;gap:6px;margin-top:8px}
.chip{font-size:13px;padding:2px 8px;border-radius:4px;background:var(--chip);border:1px solid transparent}
.chip.good{border-color:var(--strong);color:var(--strong)}
.chip.warn{border-color:var(--warn);color:var(--warn)}
.chip.new{background:var(--ink);color:var(--bg);font-weight:600}
.chip.old{border-color:var(--look);color:var(--look)}
.chip.sec{background:transparent;border-color:var(--line)}
.more{display:block;margin:14px auto 0;font:600 15px/1 var(--cond);padding:12px 22px;border-radius:6px;border:1px solid var(--line);background:var(--panel);color:var(--ink);cursor:pointer}
details.why{margin-top:8px}
details.why summary{cursor:pointer;font-size:14px;font-weight:600;color:var(--good)}
.why dl{display:grid;grid-template-columns:max-content 1fr;gap:4px 12px;margin:8px 0 0;font-size:14px}
.why dt{color:var(--muted)} .why dd{margin:0}
.ai{margin-top:8px;padding:8px 10px;border-left:3px solid var(--good);background:var(--chip);font-size:14px}
.acts{display:flex;flex-direction:column;gap:8px;padding:12px 14px 12px 0;justify-content:center}
.btn{font:600 15px/1 var(--cond);text-decoration:none;text-align:center;padding:10px 16px;border-radius:6px;border:1px solid var(--ink);background:var(--ink);color:var(--bg);white-space:nowrap;cursor:pointer}
.btn.ghost{background:transparent;color:var(--ink);border-color:var(--line);font-weight:500}
.qh{font:600 14px/1.3 var(--cond);margin:10px 0 0;color:var(--muted);text-transform:uppercase;letter-spacing:.04em}
.ql{list-style:none;margin:4px 0 0;padding:0;display:grid;gap:5px;font-size:14px}
.ql li{display:grid;grid-template-columns:18px 1fr;gap:6px}
.ql b{text-align:center} .ql small{display:block;color:var(--muted)}
.q-met b{color:var(--strong)} .q-partial b{color:var(--look)} .q-missing b{color:var(--warn)} .q-check b,.q-soft b{color:var(--muted)}
.shown{margin:12px 0 0;font:600 15px/1.3 var(--cond);color:var(--muted)}
.empty{padding:40px 20px;text-align:center;background:var(--panel);border:1px dashed var(--line);border-radius:8px;color:var(--muted)}
footer{margin-top:36px;font-size:14px;color:var(--muted)}
footer details summary{cursor:pointer;font-weight:600}
footer table{border-collapse:collapse;margin-top:8px;width:100%;font-size:13px}
footer td,footer th{text-align:left;padding:4px 8px;border-bottom:1px solid var(--line);vertical-align:top}
.tbl{overflow-x:auto}
@media (max-width:640px){
  .controls{position:static}
  .strip{grid-template-columns:58px 1fr}
  .score b{font-size:24px}
  .acts{grid-column:1/-1;flex-direction:row;padding:0 12px 12px}
  .acts .btn{flex:1}
  .bar{grid-template-columns:120px 1fr 36px}
}
@media (prefers-reduced-motion:no-preference){.strip{transition:opacity .2s}}
</style>
</head>
<body>
<div class="wrap">
<header>
  <h1>Engineering internships</h1>
  <p id="sub"></p>
  <div class="counts" id="counts"></div>
</header>

<nav class="tabs" role="tablist" id="tabs" aria-label="Sections"></nav>
<p class="tabnote" id="tabnote"></p>

<details class="gapbox" id="gapbox">
  <summary>What these postings ask for</summary>
  <div class="inner">
    <div><h3>Skills you have that come up most</h3><div id="have"></div></div>
    <div><h3>Skills not on your resume yet</h3><div id="need"></div></div>
  </div>
</details>

<div class="controls">
  <div class="row">
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
  <div class="row">
    <div class="seg" role="group" aria-label="Fit">
      <button data-tier="all" aria-pressed="true">All</button>
      <button data-tier="strong" aria-pressed="false">Strong fit</button>
      <button data-tier="good" aria-pressed="false">Good fit</button>
      <button data-tier="look" aria-pressed="false">Worth a look</button>
    </div>
    <label class="tog" id="seasonTog"><input type="checkbox" id="season"> <span id="seasonLabel"></span></label>
    <label class="tog"><input type="checkbox" id="hideOld"> <span id="oldLabel"></span></label>
    <label class="tog"><input type="checkbox" id="hideDone" checked> Hide applied and dismissed</label>
  </div>
</div>

<p class="shown" id="shown" aria-live="polite"></p>
<div id="list"></div>
<button class="more" id="more" hidden>Show more</button>

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
let tier = 'all', limit = PAGE;
const $ = id => document.getElementById(id);
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const fmt = iso => { if(!iso) return ''; const d = new Date(iso + 'T12:00:00'); return d.toLocaleDateString(undefined,{month:'short',day:'numeric'}); };
const TIER = {strong:'Strong fit', good:'Good fit', look:'Worth a look'};
const T = D.tracks;
const todayMs = Date.parse(D.today + 'T12:00:00');
const daysBack = n => new Date(todayMs - n*864e5).toISOString().slice(0,10);
const weekAgo = daysBack(7), oldCut = daysBack(D.old_after);
const ageDays = iso => iso ? Math.round((todayMs - Date.parse(iso + 'T12:00:00')) / 864e5) : null;
// "This week" and "old" go by the posting date; first_seen only when a source gives no date
const postedThisWeek = j => (j.posted || j.first_seen) >= weekAgo;
const isOld = j => (j.posted || j.first_seen) < oldCut;

// ---- sections
const ORDER = ['new', 'summer', 'fall', 'broad'].filter(k => k === 'new' || T[k]);
const HASH = {new:'new', summer:'summer', fall:'fall', broad:'all'};
const NAME = {new:'New this week'};
for(const k in T) NAME[k] = T[k].tab;
const best = j => Object.entries(j.tracks).reduce((a, b) => !a || b[1].score > a[1].score ? b : a, null);
const inTab = (j, t) => t === 'new' ? postedThisWeek(j) : !!j.tracks[t];
let tab = (() => {
  const h = location.hash.slice(1);
  const fromHash = Object.keys(HASH).find(k => HASH[k] === h);
  const saved = pref.get('tab', 'summer');
  return fromHash || (ORDER.includes(saved) ? saved : 'summer');
})();
const trackKey = j => tab === 'new' ? best(j)[0] : tab;
const seasonChk = {};

$('sub').textContent = D.sources.length ? `Scored against ${D.name}'s resume. Updated ${D.updated_label}.` : 'Waiting for the first scan.';
const c = D.counts;
$('counts').innerHTML = `<span><b>${D.jobs.length}</b>postings</span><span><b>${c.strong}</b>strong summer fits</span><span><b>${c.new_today}</b>new today</span><span><b>${D.jobs.filter(postedThisWeek).length}</b>posted this week</span>`;
$('oldLabel').textContent = `Hide postings older than ${D.old_after} days`;

function tabs(){
  $('tabs').innerHTML = ORDER.map(k => `<button class="tab" role="tab" data-tab="${k}" aria-selected="${k === tab}">${esc(NAME[k])}<span>${D.jobs.filter(j => inTab(j, k)).length}</span></button>`).join('');
}

function bars(list, color){
  if(!list.length) return '<p style="color:var(--muted);font-size:14px;margin:0">Not enough descriptions yet.</p>';
  return list.map(g => `<div class="bar"><span>${esc(g.name)}</span><i><span style="width:${g.pct}%;background:${color}"></span></i><em>${g.pct}%</em></div>`).join('');
}
function topSkills(jobs, field){
  const withDesc = jobs.filter(j => j.has_description), n = {};
  for(const j of withDesc) for(const s of j[field]) n[s] = (n[s] || 0) + 1;
  return Object.entries(n).sort((a, b) => b[1] - a[1]).slice(0, 8).map(([name, v]) => ({name, pct: Math.round(100 * v / withDesc.length)}));
}

$('src').innerHTML = '<tr><th>Source</th><th>Type</th><th>Result</th></tr>' + D.sources.map(s =>
  `<tr><td>${esc(s.name)}</td><td>${esc(s.kind)}</td><td>${s.ok ? s.count + ' postings read' : 'Failed: ' + esc(s.error)}</td></tr>`).join('');
const bad = D.sources.filter(s => !s.ok && !String(s.error).startsWith('skipped')).length;
$('foot').textContent = `${D.sources.length} sources checked` + (bad ? `, ${bad} failed (see below; fix or remove them in sources.toml).` : '.') + ' Scores are keyword-based estimates. Always read the posting before applying.';

const QI = {met:'✓', partial:'~', missing:'✗', check:'?', soft:'·'};
const num = x => Number.isInteger(x) ? x : x.toFixed(1);
const reqPct = j => { const s = j.quals && j.quals.summary; return s && s.required_checked ? s.required_met / s.required_checked : -1; };
function qualChip(q){
  const s = q && q.summary;
  if(!s || !s.required_checked) return '';
  const cls = s.required_missing ? 'warn' : s.required_met === s.required_checked ? 'good' : '';
  return `<span class="chip ${cls}">Meets ${num(s.required_met)} of ${s.required_checked} required</span>`;
}
function qualList(q){
  if(!q) return '';
  const sec = (name, rows) => rows && rows.length ? `<div class="qh">${name}</div><ul class="ql">` + rows.map(r =>
    `<li class="q-${r.status}"><b>${QI[r.status]}</b><span>${esc(r.text)}${r.why ? `<small>${esc(r.why)}</small>` : (r.status === 'check' ? '<small>Couldn\'t check this one automatically</small>' : '')}</span></li>`).join('') + '</ul>' : '';
  const s = q.summary;
  const head = s.required_checked ? `You meet ${num(s.required_met)} of ${s.required_checked} required qualifications I could check` +
    (s.preferred_total ? `, and ${s.preferred_met} of ${s.preferred_total} preferred` : '') + (s.to_check ? `. ${s.to_check} to confirm yourself.` : '.') : 'Qualifications found, but none I could check automatically.';
  return `<details class="why"><summary>Qualifications vs your resume</summary><p style="margin:8px 0 0;font-size:14px">${head}</p>${sec('Required', q.required)}${sec('Preferred', q.preferred)}</details>`;
}
const where = tr => tr.miles === 'remote' ? 'Remote' : `${tr.miles} mi from ${T.fall.home}`;

function card(j){
  const st = status[j.key];
  const k = trackKey(j), tr = j.tracks[k];
  const chips = [];
  if(j.first_seen >= D.today) chips.push('<span class="chip new">New</span>');
  if(isOld(j)) chips.push(`<span class="chip old">Older than ${D.old_after} days</span>`);
  if(tab === 'new'){
    for(const t of ORDER) if(j.tracks[t]) chips.push(`<span class="chip sec">${esc(t === 'fall' ? NAME[t] + ' · ' + where(j.tracks[t]) : NAME[t])}</span>`);
  } else if(k === 'fall'){
    chips.push(`<span class="chip sec">${esc(where(tr))}</span>`);
  }
  chips.push(`<span class="chip ${tr.season === 'match' ? 'good' : ''}">${esc(tr.season_label)}</span>`);
  if(k !== 'summer' && j.discipline) chips.push(`<span class="chip">${esc(j.discipline)}</span>`);
  const qc = qualChip(j.quals); if(qc) chips.push(qc);
  for(const f of j.flags) chips.push(`<span class="chip ${f.kind === 'info' ? '' : f.kind}">${esc(f.label)}</span>`);
  const p = tr.parts, rows = [];
  if(j.matched.length) rows.push(`<dt>Your skills it asks for</dt><dd>${esc(j.matched.join(', '))}</dd>`);
  if(j.related.length) rows.push(`<dt>Transferable</dt><dd>${esc(j.related.join(', '))}</dd>`);
  if(j.gaps.length) rows.push(`<dt>Not on your resume</dt><dd>${esc(j.gaps.join(', '))}</dd>`);
  rows.push(`<dt>Score breakdown</dt><dd>${k === 'summer' ? 'Aerospace' : 'Engineering fit'} ${p.fit}/40, skills ${p.skills}/35, eligibility ${p.eligibility}/25` +
    (p.requirements ? `, ${p.requirements} for missing required qualifications` : '') + `</dd>`);
  rows.push(`<dt>Found via</dt><dd>${esc(j.source)}</dd>`);
  const ai = j.ai ? `<div class="ai"><b>Claude's take (${esc(j.ai.fit)}):</b> ${esc(j.ai.summary)}${j.ai.talking_point ? '<br><b>Lead with:</b> ' + esc(j.ai.talking_point) : ''}</div>` : '';
  const age = ageDays(j.posted);
  const meta = [j.location && `<span>${esc(j.location)}</span>`, j.posted && `<span>Posted ${fmt(j.posted)} (${age === 0 ? 'today' : age + 'd ago'})</span>`, `<span>Found ${fmt(j.first_seen)}</span>`].filter(Boolean).join('');
  return `<article class="strip t-${tr.tier} ${st ? 'done' : ''}" data-key="${esc(j.key)}">
    <div class="score" title="Fit score out of 100"><b>${tr.score}</b><small>${TIER[tr.tier]}</small></div>
    <div class="main">
      <div class="co">${esc(j.company)}</div>
      <h2 class="title">${esc(j.title)}</h2>
      <div class="meta">${meta}</div>
      <div class="chips">${chips.join('')}</div>
      ${ai}
      ${qualList(j.quals)}
      <details class="why"><summary>Why this score</summary><dl>${rows.join('')}</dl></details>
    </div>
    <div class="acts">
      <a class="btn" href="${esc(j.url)}" target="_blank" rel="noopener">Apply</a>
      <button class="btn ghost" data-act="applied">${st === 'applied' ? 'Applied ✓' : 'Mark applied'}</button>
      <button class="btn ghost" data-act="dismissed">${st === 'dismissed' ? 'Dismissed' : 'Dismiss'}</button>
    </div>
  </article>`;
}

// Controls that depend on the section
function setupTab(){
  tabs();
  $('tabnote').textContent = tab === 'new' ? `Everything posted in the last 7 days, from every section, best fit first.` : T[tab].note;
  const inThis = D.jobs.filter(j => inTab(j, tab));
  const counts = {};
  for(const j of inThis) if(j.discipline) counts[j.discipline] = (counts[j.discipline] || 0) + 1;
  const discs = Object.entries(counts).sort((a, b) => b[1] - a[1]);
  $('disc').innerHTML = '<option value="">All disciplines</option>' + discs.map(([d, n]) => `<option value="${esc(d)}">${esc(d)} (${n})</option>`).join('');
  $('disc').hidden = tab === 'summer';
  $('sort').querySelector('[value=near]').hidden = tab !== 'fall';
  $('sort').value = tab === 'new' ? 'new' : 'score';
  $('seasonTog').hidden = $('hideOld').parentNode.hidden = tab === 'new';
  $('season').checked = !!seasonChk[tab];
  if(tab !== 'new') $('seasonLabel').textContent = tab === 'fall' ? 'Include nearby postings that don\'t name a season' : `Only ones that say ${T[tab].season_label}`;
  $('have').innerHTML = bars(topSkills(inThis, 'matched'), 'var(--strong)');
  $('need').innerHTML = bars(topSkills(inThis, 'gaps'), 'var(--warn)');
  limit = PAGE;
}

function render(){
  if(!D.jobs.length){
    $('list').innerHTML = `<div class="empty"><p><b>No scan results yet.</b></p><p>In your GitHub repo, open the Actions tab, choose “Daily job scan”, and click “Run workflow”. This page fills in about five minutes later.</p></div>`;
    return;
  }
  const q = $('q').value.trim().toLowerCase(), disc = $('disc').hidden ? '' : $('disc').value;
  const hide = $('hideDone').checked, hideOld = $('hideOld').checked, seasonOn = $('season').checked;
  const pool = D.jobs.filter(j => inTab(j, tab));
  let jobs = pool.filter(j => {
    const tr = j.tracks[trackKey(j)];
    if(tier !== 'all' && tr.tier !== tier) return false;
    if(hide && status[j.key]) return false;
    if(hideOld && isOld(j)) return false;
    if(disc && j.discipline !== disc) return false;
    if(tab === 'fall' && !seasonOn && tr.season !== 'match') return false;
    if((tab === 'summer' || tab === 'broad') && seasonOn && tr.season !== 'match') return false;
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
  $('shown').textContent = `Showing ${Math.min(limit, jobs.length)} of ${jobs.length} matching postings (${pool.length} in this section)`;
  const emptyMsg = tab === 'fall' && !pool.some(j => j.tracks.fall.season === 'match') ? T.fall.empty
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
$('tabs').addEventListener('click', e => { const b = e.target.closest('[data-tab]'); if(b) go(b.dataset.tab); });
addEventListener('hashchange', () => go(Object.keys(HASH).find(k => HASH[k] === location.hash.slice(1))));
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
  const key = btn.closest('.strip').dataset.key;
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
    if fa.get("enabled", True) and "home_lat" in fa:
        fall = f"{fa.get('season', 'fall').title()} {fa.get('year', 2027)}"
        home, radius = fa.get("home_name", "home"), fa.get("radius_miles", 50)
        info["fall"] = {
            "tab": f"{fall} near {home}", "season_label": fall, "home": home,
            "note": f"{fall} internships and co-ops within {radius} miles of {home}"
                    + (", plus remote ones" if fa.get("include_remote", True) else "") + ". Any engineering discipline.",
            "empty": f"No {fall} postings within {radius} miles of {home} yet. Fall co-ops are mostly posted "
                     "January to April. Tick the box above to see nearby postings that don't name a season.",
        }
    return info


def build_page(jobs: list[dict], sources: list[dict], profile: dict, now: dt.datetime) -> str:
    today = now.date().isoformat()
    page_jobs = [{k: j.get(k) for k in (
        "key", "company", "title", "location", "url", "source", "posted", "first_seen", "tracks",
        "discipline", "matched", "related", "gaps", "flags", "ai", "quals", "has_description")} for j in jobs]
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
        "tracks": track_info(profile),
        "jobs": page_jobs,
        "sources": sources,
        "counts": {
            "strong": sum(1 for j in jobs if j["tracks"].get("summer", {}).get("tier") == "strong"),
            "new_today": sum(1 for j in jobs if j.get("first_seen") == today),
        },
    }
    blob = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    return TEMPLATE.replace("__DATA__", blob)


def update_readme(path: Path, jobs: list[dict], page_url: str, now: dt.datetime, top: int = 25) -> None:
    """The README shows the top Summer 2027 aerospace matches."""
    start, end = "<!-- JOBS:START -->", "<!-- JOBS:END -->"
    text = path.read_text(encoding="utf-8")
    if start not in text or end not in text:
        return
    today = now.date().isoformat()
    summer = [j for j in jobs if "summer" in j["tracks"]]
    others = ", ".join(f"{sum(1 for j in jobs if t in j['tracks'])} {name}"
                       for t, name in (("fall", "Fall 2027 near home"), ("broad", "in All engineering")))
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
                     f"| {loc} | {j.get('posted') or '?'} | [Apply]({j['url']}) |")
    if not summer:
        lines.append("| | No matches yet | Run the workflow from the Actions tab | | | | |")
    block = start + "\n" + "\n".join(lines) + "\n" + end
    text = re.sub(re.escape(start) + r".*?" + re.escape(end), lambda _: block, text, flags=re.S)
    path.write_text(text, encoding="utf-8")
