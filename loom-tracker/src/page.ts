import { escapeHtml } from "./util";

const STYLE = `
:root{--bg:#f6f7f9;--card:#fff;--text:#1a1d21;--muted:#6b7280;--line:#e5e7eb;--accent:#2563eb;--accent-text:#fff;--ok:#15803d;--idle:#9ca3af;--tag:#f3f4f6;--wa:#16a34a}
@media (prefers-color-scheme:dark){:root{--bg:#0f1115;--card:#181b21;--text:#e8eaed;--muted:#9aa0a6;--line:#2a2e36;--accent:#60a5fa;--accent-text:#0b1220;--ok:#4ade80;--idle:#6b7280;--tag:#23272f;--wa:#22c55e}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--text);font:15px/1.5 system-ui,-apple-system,"Segoe UI",Arial,sans-serif}
main{max-width:1000px;margin:0 auto;padding:16px}
header{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:16px}
h1{font-size:20px;margin:0}h2{font-size:17px;margin:0 0 12px}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px;margin-bottom:16px}
.stats{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-bottom:16px}
.stat{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:12px;text-align:center}
.stat b{display:block;font-size:26px;font-variant-numeric:tabular-nums}.stat span{color:var(--muted);font-size:13px}
button,.btn{font:inherit;border:1px solid var(--line);background:var(--card);color:var(--text);border-radius:8px;padding:7px 12px;cursor:pointer;text-decoration:none;display:inline-block;white-space:nowrap}
button.primary{background:var(--accent);border-color:var(--accent);color:var(--accent-text)}
button:disabled{opacity:.5;cursor:default}
.btn.wa{background:var(--wa);border-color:var(--wa);color:#fff}.btn.off{opacity:.4;pointer-events:none}
textarea,input{font:inherit;width:100%;border:1px solid var(--line);border-radius:8px;padding:8px 10px;background:var(--bg);color:var(--text)}
textarea{min-height:110px;resize:vertical}
label{display:block;font-weight:600;margin:10px 0 6px}.hint{color:var(--muted);font-size:13px;margin:4px 0 0}
.row{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin-top:10px}
.scroll{overflow-x:auto;margin-top:12px}
table{width:100%;border-collapse:collapse;font-size:14px}
th,td{text-align:right;padding:8px 6px;border-bottom:1px solid var(--line);vertical-align:middle}
th{color:var(--muted);font-weight:600;white-space:nowrap}th[data-key]{cursor:pointer;user-select:none}
td.num{font-variant-numeric:tabular-nums;font-weight:700}
.mono{font-family:ui-monospace,Menlo,Consolas,monospace;direction:ltr;unicode-bidi:embed;font-size:13px}
tr.idle td{color:var(--idle)}tr.idle td.num{font-weight:400}
.tag{display:inline-block;white-space:nowrap;background:var(--tag);color:var(--muted);border-radius:999px;padding:1px 8px;font-size:12px;margin-inline-start:6px}
.err{color:#dc2626}.empty{color:var(--muted);text-align:center;padding:20px}
@media (max-width:600px){.stat b{font-size:22px}th,td{padding:7px 4px}.hide-sm{display:none}}
`;

function shell(title: string, body: string): string {
  return `<!doctype html><html lang="he" dir="rtl"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,nofollow">
<title>${title}</title><style>${STYLE}</style></head><body>${body}</body></html>`;
}

export function loginPage(error?: string): string {
  return shell(
    "כניסה",
    `<main style="max-width:380px;padding-top:12vh"><div class="card">
<h1 style="margin-bottom:12px">מעקב צפיות</h1>
<form method="post" action="/admin/login">
<label for="pw">סיסמה</label><input id="pw" name="password" type="password" autocomplete="current-password" required autofocus>
${error ? `<p class="err">${escapeHtml(error)}</p>` : ""}
<div class="row"><button class="primary" type="submit">כניסה</button></div>
</form></div></main>`,
  );
}

const DEFAULT_TEMPLATE = "היי {שם}, הנה הסרטון הקצר שהבטחתי (פחות מדקה): {קישור}";

export function dashboardPage(origin: string): string {
  return shell(
    "מעקב צפיות",
    `<main>
<header><h1>מעקב צפיות בסרטון</h1>
<form method="post" action="/admin/logout"><button type="submit">יציאה</button></form></header>

<div class="stats">
<div class="stat"><b id="s-total">0</b><span>נמענים</span></div>
<div class="stat"><b id="s-clicked">0</b><span>לחצו</span></div>
<div class="stat"><b id="s-rate">0%</b><span>אחוז לחיצה</span></div>
</div>

<section class="card">
<h2>יצירת קישורים</h2>
<label for="bulk">רשימת נמענים</label>
<textarea id="bulk" placeholder="דני כהן, 050-1234567&#10;מרפאת שיניים לוי, 052-7654321"></textarea>
<p class="hint">שורה לכל נמען: שם, טלפון (מופרדים בפסיק או בטאב). הטלפון אופציונלי.</p>
<label for="tpl">נוסח הודעה לוואטסאפ</label>
<textarea id="tpl" style="min-height:70px"></textarea>
<p class="hint">{שם} ו-{קישור} יוחלפו אוטומטית.</p>
<div class="row"><button class="primary" id="create">צור קישורים</button><span id="create-msg" class="hint"></span></div>
<div id="created" hidden>
<div class="row"><button id="copy-all">העתק הכל</button><button id="created-csv">ייצוא CSV</button></div>
<div class="scroll"><table><thead><tr><th>שם</th><th>טלפון</th><th class="hide-sm">קישור</th><th></th><th></th></tr></thead>
<tbody id="created-body"></tbody></table></div>
</div>
</section>

<section class="card">
<h2>מי לחץ</h2>
<div class="row" style="margin-top:0">
<input id="search" type="search" placeholder="חיפוש לפי שם" style="flex:1;min-width:160px">
<button id="refresh">רענון</button><a class="btn" href="/admin/export.csv">ייצוא CSV</a>
</div>
<div class="scroll"><table><thead><tr>
<th data-key="name">שם</th><th data-key="id">קישור</th><th data-key="clicks">קליקים</th>
<th data-key="first_click">קליק ראשון</th><th data-key="last_click">קליק אחרון ▼</th><th data-key="country">מדינה</th>
</tr></thead><tbody id="stats-body"></tbody></table></div>
</section>
</main>
<script>
var ORIGIN = ${JSON.stringify(origin)};
var DEFAULT_TEMPLATE = ${JSON.stringify(DEFAULT_TEMPLATE)};
${CLIENT_JS}
</script>`,
  );
}

// Client script. Builds the DOM with textContent only, so names can never inject HTML.
const CLIENT_JS = String.raw`
function $(s){return document.querySelector(s)}
function el(tag,attrs){var e=document.createElement(tag);attrs=attrs||{};
  for(var k in attrs){if(k==='class')e.className=attrs[k];else if(k.slice(0,2)==='on')e.addEventListener(k.slice(2),attrs[k]);else e.setAttribute(k,attrs[k])}
  for(var i=2;i<arguments.length;i++){if(arguments[i]!=null)e.append(arguments[i])}return e}
var fmt=new Intl.DateTimeFormat('he-IL',{timeZone:'Asia/Jerusalem',dateStyle:'short',timeStyle:'short'});
function tf(iso){return iso?fmt.format(new Date(iso)):''}
function linkFor(id){return ORIGIN+'/v/'+id}
function copy(text,btn){
  function done(){var old=btn.textContent;btn.textContent='הועתק ✓';setTimeout(function(){btn.textContent=old},1200)}
  if(navigator.clipboard){navigator.clipboard.writeText(text).then(done,fallback)}else{fallback()}
  function fallback(){var t=el('textarea');t.value=text;document.body.append(t);t.select();document.execCommand('copy');t.remove();done()}
}
function csvCell(v){var s=v==null?'':String(v);if(/^[=+\-@\t\r]/.test(s))s="'"+s;return /[",\r\n]/.test(s)?'"'+s.replace(/"/g,'""')+'"':s}
function download(name,rows){
  var csv='﻿'+rows.map(function(r){return r.map(csvCell).join(',')}).join('\r\n');
  var a=el('a',{href:URL.createObjectURL(new Blob([csv],{type:'text/csv;charset=utf-8'})),download:name});
  document.body.append(a);a.click();a.remove();
}

/* stats table */
var rows=[],sortKey='last_click',sortDir=-1;
function cmp(a,b){var x=a[sortKey],y=b[sortKey];
  if(x==null&&y==null)return 0;if(x==null)return 1;if(y==null)return -1;
  if(typeof x==='string'){return x.localeCompare(y,'he')*sortDir}return (x-y)*sortDir}
function render(){
  var total=rows.length,clicked=rows.filter(function(r){return r.clicks>0}).length;
  $('#s-total').textContent=total;$('#s-clicked').textContent=clicked;
  $('#s-rate').textContent=total?Math.round(clicked*100/total)+'%':'0%';
  var q=$('#search').value.trim().toLowerCase();
  var list=rows.filter(function(r){return !q||r.name.toLowerCase().indexOf(q)>=0}).sort(cmp);
  var body=$('#stats-body');
  if(!list.length){body.replaceChildren(el('tr',{},el('td',{colspan:'6',class:'empty'},rows.length?'אין תוצאות':'עוד אין נמענים. צור קישורים למעלה.')));return}
  body.replaceChildren.apply(body,list.map(function(r){
    var btn=el('button',{title:'העתק קישור'},'העתק');btn.onclick=function(){copy(linkFor(r.id),btn)};
    return el('tr',{class:r.clicks?'':'idle'},
      el('td',{},r.name,r.clicks?null:el('span',{class:'tag'},'עוד לא לחץ')),
      el('td',{},el('span',{class:'mono hide-sm'},r.id+' '),btn),
      el('td',{class:'num'},String(r.clicks)),
      el('td',{},tf(r.first_click)),el('td',{},tf(r.last_click)),el('td',{},r.country||''));
  }));
}
document.querySelectorAll('th[data-key]').forEach(function(th){th.onclick=function(){
  var k=th.dataset.key;if(sortKey===k){sortDir=-sortDir}else{sortKey=k;sortDir=(k==='name'||k==='id'||k==='country')?1:-1}
  document.querySelectorAll('th[data-key]').forEach(function(h){h.textContent=h.textContent.replace(/ [▲▼]$/,'')});
  th.textContent+=sortDir>0?' ▲':' ▼';render()}});
function load(){fetch('/admin/api/stats').then(function(r){if(r.status===401){location.reload();throw 0}return r.json()})
  .then(function(d){rows=d.rows;render()}).catch(function(){})}
$('#search').oninput=render;$('#refresh').onclick=load;
document.addEventListener('visibilitychange',function(){if(!document.hidden)load()});
load();

/* bulk create */
var tpl=$('#tpl'),created=[];
try{tpl.value=localStorage.getItem('wa_template')||DEFAULT_TEMPLATE}catch(e){tpl.value=DEFAULT_TEMPLATE}
tpl.oninput=function(){try{localStorage.setItem('wa_template',tpl.value)}catch(e){}renderCreated()};
function message(r){return tpl.value.split('{שם}').join(r.name).split('{קישור}').join(r.link)}
function waLink(r){return r.phone?'https://wa.me/'+r.phone+'?text='+encodeURIComponent(message(r)):''}
function renderCreated(){
  $('#created').hidden=!created.length;
  var body=$('#created-body');
  body.replaceChildren.apply(body,created.map(function(r){
    var btn=el('button',{},'העתק');btn.onclick=function(){copy(r.link,btn)};
    var wa=r.phone?el('a',{class:'btn wa',href:waLink(r),target:'_blank',rel:'noopener'},'וואטסאפ'):el('span',{class:'btn wa off'},'אין טלפון');
    return el('tr',{},el('td',{},r.name),el('td',{class:'mono'},r.phone||''),el('td',{class:'mono hide-sm'},r.link),el('td',{},btn),el('td',{},wa));
  }));
}
$('#create').onclick=function(){
  var text=$('#bulk').value,btn=$('#create'),msg=$('#create-msg');
  if(!text.trim())return;btn.disabled=true;msg.textContent='';
  fetch('/admin/api/recipients',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({text:text})})
    .then(function(r){if(!r.ok)throw r;return r.json()})
    .then(function(d){created=d.rows;renderCreated();$('#bulk').value='';msg.textContent='נוצרו '+created.length+' קישורים';load()})
    .catch(function(){msg.textContent='שגיאה ביצירה. נסה שוב.'})
    .finally(function(){btn.disabled=false});
};
$('#copy-all').onclick=function(){copy(created.map(function(r){return r.name+'\t'+r.link}).join('\n'),$('#copy-all'))};
$('#created-csv').onclick=function(){
  download('links.csv',[['שם','טלפון','קישור','קישור וואטסאפ']].concat(created.map(function(r){return [r.name,r.phone,r.link,waLink(r)]})));
};
`;
