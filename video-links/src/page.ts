import { CONTACT_NAME, CONTACT_PHONE, CONTACT_ROLE, CONTACT_WA, PHOTO, SITE } from "./brand";
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
.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:16px}
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
.tag{display:inline-block;white-space:nowrap;margin-top:2px;background:var(--tag);color:var(--muted);border-radius:999px;padding:1px 8px;font-size:12px;margin-inline-start:6px}
.tag.ok{color:var(--ok)}.acts{display:flex;gap:6px;margin-top:6px}.acts button,.acts .btn{padding:3px 10px;font-size:13px}summary{cursor:pointer;font-weight:600}
.empty{color:var(--muted);text-align:center;padding:20px}
@media (max-width:600px){th{white-space:normal}.stats{grid-template-columns:repeat(2,1fr)}.stat b{font-size:22px}th,td{padding:7px 4px}.hide-sm{display:none}}
`;

function shell(title: string, body: string): string {
  return `<!doctype html><html lang="he" dir="rtl"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,nofollow">
<title>${title}</title><style>${STYLE}</style></head><body>${body}</body></html>`;
}

const DEFAULT_TEMPLATE = "היי {שם}, הכנתי לך סרטון קצר במיוחד בשבילך: {קישור}";

export function dashboardPage(origin: string): string {
  return shell(
    "מעקב צפיות",
    `<main>
<header><h1>מעקב צפיות בסרטונים</h1></header>

<div class="stats">
<div class="stat"><b id="s-total">0</b><span>נמענים</span></div>
<div class="stat"><b id="s-clicked">0</b><span>נכנסו לקישור</span></div>
<div class="stat"><b id="s-played">0</b><span>ניגנו את הסרטון</span></div>
<div class="stat"><b id="s-rate">0%</b><span>אחוז כניסה</span></div>
</div>

<section class="card"><details>
<summary>נוסח הודעה לוואטסאפ</summary>
<textarea id="tpl" style="min-height:70px;margin-top:10px"></textarea>
<p class="hint">{שם} ו-{קישור} יוחלפו אוטומטית כשלוחצים "וואטסאפ" בטבלה.</p>
</details></section>

<section class="card">
<h2>מי צפה</h2>
<div class="row" style="margin-top:0">
<input id="search" type="search" placeholder="חיפוש לפי שם" style="flex:1;min-width:160px">
<button id="refresh">רענון</button><a class="btn" href="/admin/export.csv">ייצוא CSV</a>
</div>
<div class="scroll"><table><thead><tr>
<th data-key="name">שם</th><th data-key="clicks">כניסות</th><th data-key="watched">צפייה</th>
<th data-key="last_click">כניסה אחרונה ▼</th><th data-key="first_click" class="hide-sm">כניסה ראשונה</th><th data-key="country" class="hide-sm">מדינה</th>
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
  for(var k in attrs){if(k==='class')e.className=attrs[k];else e.setAttribute(k,attrs[k])}
  for(var i=2;i<arguments.length;i++){if(arguments[i]!=null)e.append(arguments[i])}return e}
var fmt=new Intl.DateTimeFormat('he-IL',{timeZone:'Asia/Jerusalem',dateStyle:'short',timeStyle:'short'});
function tf(iso){return iso?fmt.format(new Date(iso)):''}
function linkFor(id){return ORIGIN+'/v/'+id}
function copy(text,btn){
  function done(){var old=btn.textContent;btn.textContent='הועתק ✓';setTimeout(function(){btn.textContent=old},1200)}
  if(navigator.clipboard){navigator.clipboard.writeText(text).then(done,fallback)}else{fallback()}
  function fallback(){var t=el('textarea');t.value=text;document.body.append(t);t.select();document.execCommand('copy');t.remove();done()}
}
function watchedLabel(w){if(w==null)return '';if(w===0)return 'התחיל';return w===100?'עד הסוף ✓':w+'%'}

/* WhatsApp message template, kept in this browser only */
var tpl=$('#tpl');
try{tpl.value=localStorage.getItem('wa_template')||DEFAULT_TEMPLATE}catch(e){tpl.value=DEFAULT_TEMPLATE}
tpl.oninput=function(){try{localStorage.setItem('wa_template',tpl.value)}catch(e){}};
function waLink(r){return 'https://wa.me/'+r.phone+'?text='+encodeURIComponent(tpl.value.split('{שם}').join(r.name).split('{קישור}').join(linkFor(r.id)))}

/* stats table */
var rows=[],sortKey='last_click',sortDir=-1;
function cmp(a,b){var x=a[sortKey],y=b[sortKey];
  if(x==null&&y==null)return 0;if(x==null)return 1;if(y==null)return -1;
  if(typeof x==='string'){return x.localeCompare(y,'he')*sortDir}return (x-y)*sortDir}
function render(){
  var total=rows.length,clicked=rows.filter(function(r){return r.clicks>0}).length;
  $('#s-total').textContent=total;$('#s-clicked').textContent=clicked;
  $('#s-played').textContent=rows.filter(function(r){return r.watched!=null}).length;
  $('#s-rate').textContent=total?Math.round(clicked*100/total)+'%':'0%';
  var q=$('#search').value.trim().toLowerCase();
  var list=rows.filter(function(r){return !q||r.name.toLowerCase().indexOf(q)>=0}).sort(cmp);
  var body=$('#stats-body');
  if(!list.length){body.replaceChildren(el('tr',{},el('td',{colspan:'7',class:'empty'},rows.length?'אין תוצאות':'עוד אין נמענים. נמען נוצר כשמעלים לו סרטון.')));return}
  body.replaceChildren.apply(body,list.map(function(r){
    var btn=el('button',{title:linkFor(r.id)},'העתק');btn.onclick=function(){copy(linkFor(r.id),btn)};
    var wa=r.phone?el('a',{class:'btn wa',href:waLink(r),target:'_blank',rel:'noopener'},'וואטסאפ'):null;
    if(wa)wa.onclick=function(){wa.href=waLink(r)};
    var tag=!r.video_at?el('span',{class:'tag'},'אין סרטון'):r.clicks?null:el('span',{class:'tag'},'עוד לא נכנס');
    return el('tr',{class:r.clicks?'':'idle'},
      el('td',{},el('div',{},r.name,tag),el('div',{class:'acts'},btn,wa)),
      el('td',{class:'num'},String(r.clicks)),
      el('td',{},r.watched==null?'':el('span',{class:'tag ok'},watchedLabel(r.watched))),
      el('td',{},tf(r.last_click)),el('td',{class:'hide-sm'},tf(r.first_click)),el('td',{class:'hide-sm'},r.country||''));
  }));
}
document.querySelectorAll('th[data-key]').forEach(function(th){th.onclick=function(){
  var k=th.dataset.key;if(sortKey===k){sortDir=-sortDir}else{sortKey=k;sortDir=(k==='name'||k==='country')?1:-1}
  document.querySelectorAll('th[data-key]').forEach(function(h){h.textContent=h.textContent.replace(/ [▲▼]$/,'')});
  th.textContent+=sortDir>0?' ▲':' ▼';render()}});
function load(){fetch('/admin/api/stats').then(function(r){return r.json()})
  .then(function(d){rows=d.rows;render()}).catch(function(){})}
$('#search').oninput=render;$('#refresh').onclick=load;
document.addEventListener('visibilitychange',function(){if(!document.hidden)load()});
load();
`;

const VIDEO_STYLE = `
*{box-sizing:border-box}
html,body{margin:0;height:100%;background:#0b0c0f;color:#e8eaed;font:15px/1.5 system-ui,-apple-system,"Segoe UI",Arial,sans-serif}
main{min-height:100%;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:12px;padding:12px}
h1{font-size:17px;font-weight:600;margin:0;text-align:center}
video{display:block;max-width:100%;max-height:calc(100vh - 80px);max-height:calc(100svh - 80px);aspect-ratio:9/16;background:#000;border-radius:14px}
.stage{display:flex;justify-content:center;max-width:100%}
.col{display:none}
@media (min-width:760px) and (min-aspect-ratio:1/1){
html,body{background:radial-gradient(ellipse 75% 85% at 50% 45%,#ffffff,transparent 75%),radial-gradient(circle,#dde6df 1.2px,transparent 1.6px) 0 0/24px 24px,#f6faf7;color:#141a15}
main{padding:20px 24px;gap:14px}
h1{font-size:20px;font-weight:700}
.stage{--h:min(calc(100vh - 92px),900px);gap:clamp(18px,3.5vw,56px);align-items:center}
video{height:var(--h);max-height:none;width:auto;border-radius:18px;box-shadow:0 20px 50px rgba(20,26,21,.22)}
.col{display:flex;width:clamp(196px,21vw,290px)}
.deco,.side{width:100%;min-height:390px;border-radius:22px;background:#fff;border:1px solid #dbe4dc;box-shadow:0 14px 40px rgba(20,26,21,.10)}
.side{display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;gap:10px;padding:22px 22px}
.side img{width:76px;height:76px;border-radius:50%;border:3px solid #007329;object-fit:cover}
.who{font-size:14px;color:#4e544f;line-height:1.3}.who b{display:block;font-size:18px;color:#141a15}
.side p{margin:2px 0 4px;font-size:18px;font-weight:700;line-height:1.35}
.btn{display:flex;align-items:center;justify-content:center;gap:9px;width:100%;height:46px;border-radius:23px;font-size:16px;font-weight:700;text-decoration:none}
.btn svg{width:20px;height:20px;flex:none}
.wa{background:#007329;color:#fff}.call{border:1px solid #ccd3cd;color:#141a15}
.num{direction:ltr;unicode-bidi:isolate}
.site{font-size:13px;color:#4e544f;text-decoration:none;direction:ltr}
.deco{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:22px;padding:30px 26px;text-align:center;animation:float 7s ease-in-out 2.4s infinite}
.score{font:700 76px/1 Georgia,"Times New Roman",serif;color:#141a15;direction:ltr;letter-spacing:-1px}
.stars{display:flex;gap:6px;direction:ltr}
.stars i{width:30px;height:30px;background:#dbe4dc;clip-path:polygon(50% 0,61.8% 35.4%,100% 38.2%,69.1% 61.8%,80.9% 100%,50% 76.4%,19.1% 100%,30.9% 61.8%,0 38.2%,38.2% 35.4%);animation:star .45s ease-out forwards}
.stars i:nth-child(1){animation-delay:.3s}.stars i:nth-child(2){animation-delay:.45s}.stars i:nth-child(3){animation-delay:.6s}.stars i:nth-child(4){animation-delay:.75s}.stars i:nth-child(5){animation-delay:.9s}
.bars{display:flex;align-items:flex-end;gap:9px;height:96px;direction:ltr}
.bars i{width:22px;border-radius:6px 6px 3px 3px;background:#d0eed5;transform-origin:bottom;transform:scaleY(0);animation:grow .7s cubic-bezier(.2,.8,.2,1) forwards}
.bars i:last-child{background:#007329}
.bars i:nth-child(1){height:22%;animation-delay:1.1s}.bars i:nth-child(2){height:34%;animation-delay:1.2s}.bars i:nth-child(3){height:47%;animation-delay:1.3s}.bars i:nth-child(4){height:63%;animation-delay:1.4s}.bars i:nth-child(5){height:80%;animation-delay:1.5s}.bars i:nth-child(6){height:100%;animation-delay:1.6s}
.deco p{margin:0;font-size:19px;font-weight:700;line-height:1.35}.deco p em{font-style:normal;color:#007329}
@keyframes star{0%{transform:scale(.6)}60%{transform:scale(1.18);background:#f2a900}100%{transform:scale(1);background:#f2a900}}
@keyframes grow{to{transform:scaleY(1)}}
@keyframes float{0%,100%{transform:translateY(0)}50%{transform:translateY(-8px)}}
@media (max-width:1150px){.deco,.side{min-height:340px}.side{padding:18px 14px;gap:8px}.side img{width:62px;height:62px}.side p{font-size:15px}.btn{height:40px;font-size:13.5px;gap:6px}.btn svg{width:17px;height:17px}.score{font-size:58px}.stars i{width:23px;height:23px}.bars{height:74px;gap:7px}.bars i{width:17px}.deco p{font-size:16px}}
@media (prefers-reduced-motion:reduce){.deco,.stars i,.bars i{animation-duration:1ms;animation-delay:0s;animation-iteration-count:1}}
}
`;

const WA_ICON =
  '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M12 2a10 10 0 0 0-8.6 15.1L2 22l5-1.3A10 10 0 1 0 12 2zm0 18.2c-1.5 0-3-.4-4.3-1.2l-.3-.2-3 .8.8-2.9-.2-.3A8.2 8.2 0 1 1 12 20.2zm4.5-6.1c-.2-.1-1.5-.7-1.7-.8-.2-.1-.4-.1-.6.1l-.8 1c-.1.2-.3.2-.5.1a6.7 6.7 0 0 1-3.3-2.9c-.2-.4.2-.4.7-1.3.1-.2 0-.3 0-.4l-.8-1.8c-.2-.5-.4-.4-.6-.4h-.5c-.2 0-.4.1-.6.3-.2.2-.8.8-.8 2s.8 2.3 1 2.5c.1.2 1.7 2.6 4.1 3.6 1.5.7 2.1.7 2.9.6.5-.1 1.5-.6 1.7-1.2.2-.6.2-1.1.2-1.2-.1-.1-.2-.2-.4-.3z"/></svg>';
const PHONE_ICON =
  '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3.1 19.5 19.5 0 0 1-6-6A19.8 19.8 0 0 1 2.1 4.2 2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7c.1.9.4 1.8.7 2.7a2 2 0 0 1-.5 2.1L8 9.8a16 16 0 0 0 6 6l1.3-1.3a2 2 0 0 1 2.1-.4c.9.3 1.8.6 2.7.7a2 2 0 0 1 1.7 2z"/></svg>';

// Decorative card on the other side of the video (wide screens only): pure CSS, no images to load.
const DECO = `<div class="deco" aria-hidden="true">
<div class="score">5.0</div>
<div class="stars"><i></i><i></i><i></i><i></i><i></i></div>
<div class="bars"><i></i><i></i><i></i><i></i><i></i><i></i></div>
<p>ביקורות חדשות<br><em>כל שבוע.</em></p>
</div>`;

// Shown beside the video on wide screens only (WhatsApp Web / Desktop users); phones see just the video.
function sideCard(name: string): string {
  const text = encodeURIComponent(`היי ${CONTACT_NAME}, ראיתי את הסרטון ששלחת ל${name} ואשמח לשמוע עוד`);
  return `<aside class="side">
<img src="${PHOTO}" alt="${escapeHtml(CONTACT_NAME)}">
<div class="who"><b>${escapeHtml(CONTACT_NAME)}</b>${escapeHtml(CONTACT_ROLE)}</div>
<p>רוצים לראות איך זה יעבוד אצלכם?</p>
<a class="btn wa" href="https://wa.me/${CONTACT_WA}?text=${text}" target="_blank" rel="noopener">${WA_ICON}<span>דברו איתי בוואטסאפ</span></a>
<a class="btn call" href="tel:+${CONTACT_WA}">${PHONE_ICON}<span class="num">${CONTACT_PHONE}</span></a>
<a class="site" href="https://${SITE}" target="_blank" rel="noopener">${SITE}</a>
</aside>`;
}

export function videoPage(id: string, name: string, origin: string): string {
  const title = escapeHtml(`סרטון אישי עבור ${name}`);
  const thumb = `${origin}/m/${id}.jpg`;
  return `<!doctype html><html lang="he" dir="rtl"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,nofollow">
<title>${title}</title>
<meta property="og:type" content="video.other"><meta property="og:title" content="${title}">
<meta property="og:description" content="סרטון קצר שהוכן במיוחד בשבילך">
<meta property="og:url" content="${origin}/v/${id}">
<meta property="og:image" content="${thumb}"><meta property="og:image:type" content="image/jpeg">
<meta property="og:image:width" content="540"><meta property="og:image:height" content="960">
<meta name="twitter:card" content="summary_large_image">
<style>${VIDEO_STYLE}</style></head><body><main>
<h1>${title}</h1>
<div class="stage">
<div class="col">${DECO}</div>
<video id="v" src="/m/${id}.mp4" poster="/m/${id}.jpg" controls playsinline preload="metadata"></video>
<div class="col">${sideCard(name)}</div>
</div>
</main>
<script>
(function(){var v=document.getElementById('v'),sent={},url='/e/${id}';
function send(p){if(sent[p])return;sent[p]=1;
  if(!(navigator.sendBeacon&&navigator.sendBeacon(url,String(p))))fetch(url,{method:'POST',body:String(p),keepalive:true}).catch(function(){})}
v.addEventListener('play',function(){send(0)});
v.addEventListener('timeupdate',function(){if(!v.duration)return;var p=v.currentTime/v.duration*100;
  if(p>=25)send(25);if(p>=50)send(50);if(p>=75)send(75)});
v.addEventListener('ended',function(){send(100)});
})();
</script></body></html>`;
}

export function unavailablePage(): string {
  return `<!doctype html><html lang="he" dir="rtl"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,nofollow">
<title>הסרטון לא זמין</title><style>${VIDEO_STYLE}</style></head>
<body><main><h1>הסרטון לא זמין</h1></main></body></html>`;
}
