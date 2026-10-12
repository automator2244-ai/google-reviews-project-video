// Runs leads.gs in Node against in-memory fakes of SpreadsheetApp and Google Places.
// Usage: node leads/test/run.js
const fs = require('fs');
const path = require('path');
const vm = require('vm');
const assert = require('assert');

class FakeRange {
  constructor(sheet, row, col, nr, nc) { Object.assign(this, { sheet, row, col, nr, nc }); }
  getValues() {
    return Array.from({ length: this.nr }, (_, i) =>
      Array.from({ length: this.nc }, (_, j) => this.sheet.cell(this.row + i, this.col + j)));
  }
  getValue() { return this.getValues()[0][0]; }
  setValues(v) {
    assert.strictEqual(v.length, this.nr, 'row count');
    v.forEach((r, i) => { assert.strictEqual(r.length, this.nc, 'col count'); r.forEach((x, j) => this.sheet.set(this.row + i, this.col + j, x)); });
    return this;
  }
  setValue(x) { this.sheet.set(this.row, this.col, x); return this; }
  setFormula(x) { return this.setValue(x); }
  setNumberFormat() { return this; }
  clearContent() { for (let i = 0; i < this.nr; i++) for (let j = 0; j < this.nc; j++) this.sheet.set(this.row + i, this.col + j, ''); return this; }
  getSheet() { return this.sheet; }
  getRow() { return this.row; }
  getColumn() { return this.col; }
}

class FakeSheet {
  constructor(name, rows) { this.name = name; this.data = new Map(); this.maxRows = 1000; (rows || []).forEach((r, i) => r.forEach((v, j) => this.set(i + 1, j + 1, v))); }
  key(r, c) { return r + ',' + c; }
  cell(r, c) { assert(r <= this.maxRows, `row ${r} beyond max ${this.maxRows}`); return this.data.has(this.key(r, c)) ? this.data.get(this.key(r, c)) : ''; }
  set(r, c, v) { assert(r <= this.maxRows, `write row ${r} beyond max`); if (v === '' || v === null) this.data.delete(this.key(r, c)); else this.data.set(this.key(r, c), v); }
  getName() { return this.name; }
  getLastRow() { let m = 0; for (const k of this.data.keys()) m = Math.max(m, Number(k.split(',')[0])); return m; }
  getMaxRows() { return this.maxRows; }
  insertRowsAfter(after, n) { this.maxRows += n; }
  getRange(r, c, nr = 1, nc = 1) { return new FakeRange(this, r, c, nr, nc); }
  row(r) { return Array.from({ length: 14 }, (_, j) => this.cell(r, j + 1)); }
}

function makeSpreadsheet(areas) {
  const header = ['תאריך הוספה', 'שם המרפאה', 'טלפון', 'וואטסאפ', 'סטטוס', 'דירוג', 'ביקורות', 'אתר', 'אזור', 'כתובת', 'גוגל מפות', 'הערות', 'מזהה גוגל', 'מפתח טלפון'];
  const sheets = {
    'עסקי': new FakeSheet('עסקי', [header]),
    'מאובטח': new FakeSheet('מאובטח', [header]),
    'הגדרות': new FakeSheet('הגדרות', [['אזור', 'מצב', 'תאריך סריקה', 'נמצאו'], ...areas.map((a) => [a])]),
    '_נסרקו': new FakeSheet('_נסרקו', [['מזהה', 'שם', 'טלפון', 'סוג', 'אזור', 'תאריך']]),
    '_תור': new FakeSheet('_תור', [['id', 'name', 'phone', 'key', 'kind', 'rating', 'reviews', 'website', 'area', 'address', 'maps']]),
  };
  return { sheets, getSheetByName: (n) => sheets[n], toast: () => {} };
}

// Fake Google: each area returns pages of places built from a seed.
function makePlaces(byArea) {
  const calls = [];
  return {
    calls,
    fetch(url, opts) {
      const body = JSON.parse(opts.payload);
      assert.strictEqual(opts.headers['X-Goog-Api-Key'], 'TESTKEY');
      assert(opts.headers['X-Goog-FieldMask'].includes('places.userRatingCount'));
      assert.strictEqual(body.includedType, 'dentist');
      const area = body.textQuery.replace('רופא שיניים ', '');
      calls.push({ area, token: body.pageToken || '' });
      const pages = byArea[area] || [[]];
      const idx = body.pageToken ? Number(body.pageToken) : 0;
      const out = { places: pages[idx] || [] };
      if (idx + 1 < pages.length) out.nextPageToken = String(idx + 1);
      return { getResponseCode: () => 200, getContentText: () => JSON.stringify(out) };
    },
  };
}

function load(ss, places, now) {
  const props = new Map([['PLACES_KEY', 'TESTKEY']]);
  const ctx = {
    console,
    Set, Map, Date: class extends Date { constructor(...a) { super(...(a.length ? a : [now])); } },
    SpreadsheetApp: { getActive: () => ss, getUi: () => ({}) },
    PropertiesService: { getScriptProperties: () => ({ getProperty: (k) => props.get(k) || null, setProperty: (k, v) => props.set(k, v) }) },
    LockService: { getScriptLock: () => ({ tryLock: () => true, releaseLock: () => {} }) },
    UrlFetchApp: places,
    Utilities: {
      formatDate(d, tz, fmt) {
        const p = Object.fromEntries(new Intl.DateTimeFormat('en-GB', { timeZone: tz, year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', weekday: 'short', hour12: false })
          .formatToParts(d).map((x) => [x.type, x.value]));
        const u = { Mon: 1, Tue: 2, Wed: 3, Thu: 4, Fri: 5, Sat: 6, Sun: 7 }[p.weekday];
        return fmt.replace('yyyy', p.year).replace('MM', p.month).replace('dd', p.day).replace('HH', p.hour).replace('mm', p.minute).replace('u', String(u));
      },
    },
  };
  vm.createContext(ctx);
  vm.runInContext(fs.readFileSync(path.join(__dirname, '..', 'leads.gs'), 'utf8'), ctx);
  ctx.props = props;
  return ctx;
}

let n = 0;
const place = (o) => ({
  id: 'p' + (++n),
  displayName: { text: o.name || 'מרפאה ' + n },
  nationalPhoneNumber: o.phone,
  businessStatus: o.status || 'OPERATIONAL',
  types: ['dentist'],
  formattedAddress: 'רחוב ' + n + ', תל אביב',
  googleMapsUri: 'https://maps.google.com/?cid=' + n,
  ...(o.site ? { websiteUri: o.site } : {}),
  ...(o.rating !== undefined ? { rating: o.rating } : {}),
  ...(o.reviews !== undefined ? { userRatingCount: o.reviews } : {}),
  ...(o.id ? { id: o.id } : {}),
});
const mobile = (i) => `05${String(i % 10)}-${String(1000000 + i).slice(1, 4)}-${String(1000000 + i).slice(3)}`;
const dataRows = (sheet) => { const out = []; for (let r = 2; r <= sheet.getLastRow(); r++) out.push(sheet.row(r)); return out; };
const filled = (rows) => rows.filter((r) => r[1] !== '');

// ---------- test 1: content, accuracy, filtering, dedup ----------
{
  const special = [
    place({ name: 'מרפאה עם הכל', phone: '050-111-2222', site: 'https://dent.example.co.il/', rating: 4.6, reviews: 38 }),
    place({ name: 'בלי אתר ודירוג', phone: '052-333-4444' }),
    place({ name: 'קווי', phone: '03-555-6666', rating: 4.9, reviews: 200 }),
    place({ name: 'סגורה', phone: '054-777-8888', status: 'CLOSED_PERMANENTLY' }),
    place({ name: 'בלי טלפון' }),
    place({ name: 'אותו טלפון בפורמט אחר', phone: '+972 50-111-2222' }),
    place({ name: '=HACK()', phone: '058-000-1111' }),
  ];
  const ss = makeSpreadsheet(['תל אביב צפון']);
  const g = makePlaces({ 'תל אביב צפון': [special] });
  const ctx = load(ss, g, new Date('2026-10-13T04:05:00Z')); // Tuesday 07:05 Israel
  ctx.dailyRun();
  const a = filled(dataRows(ss.sheets['עסקי'])), b = filled(dataRows(ss.sheets['מאובטח']));
  const all = [...a, ...b];
  assert.strictEqual(all.length, 3, 'only 3 valid mobile clinics');
  const byName = Object.fromEntries(all.map((r) => [r[1], r]));
  const full = byName['מרפאה עם הכל'];
  assert.deepStrictEqual([full[2], full[4], full[5], full[6], full[7]], ['050-111-2222', 'עוד לא נשלחה הודעה', 4.6, 38, 'https://dent.example.co.il/']);
  assert.strictEqual(full[3], `=HYPERLINK("https://wa.me/972501112222","פתח צ'אט")`);
  const bare = byName['בלי אתר ודירוג'];
  assert.deepStrictEqual([bare[5], bare[6], bare[7]], ['', '', ''], 'missing fields stay empty');
  assert(byName["'=HACK()"], 'formula-like name stored as text');
  assert(!byName['קווי'] && !byName['סגורה'] && !byName['בלי טלפון'] && !byName['אותו טלפון בפורמט אחר']);
  const seen = dataRows(ss.sheets['_נסרקו']);
  assert.strictEqual(seen.length, 7, 'every place recorded as seen');
  assert.strictEqual(seen.find((r) => r[1] === 'קווי')[3], 'קווי', 'landline kept aside');
  assert.strictEqual(ss.sheets['הגדרות'].cell(2, 2), 'נסרק');
  console.log('ok  content, empty fields, landline/closed/no-phone filtered, same phone in two formats deduped');
}

// ---------- test 2: 40 + 40, alternate, queue, blank row between days, no cross-tab dupes ----------
{
  n = 0;
  const pagesFor = (from, count) => {
    const ps = Array.from({ length: count }, (_, i) => place({ phone: mobile(from + i), rating: 4.0, reviews: i }));
    return [ps.slice(0, 20), ps.slice(20, 40), ps.slice(40, 60)].filter((p) => p.length);
  };
  const areas = { 'א': pagesFor(0, 60), 'ב': pagesFor(100, 60), 'ג': pagesFor(200, 60) };
  const ss = makeSpreadsheet(['א', 'ב', 'ג']);
  const g = makePlaces(areas);
  const ctx = load(ss, g, new Date('2026-10-13T04:05:00Z'));
  ctx.dailyRun();
  let a = filled(dataRows(ss.sheets['עסקי'])), b = filled(dataRows(ss.sheets['מאובטח']));
  assert.strictEqual(a.length, 40); assert.strictEqual(b.length, 40);
  assert.strictEqual(g.calls.length, 6, 'two full areas = 6 searches');
  const queued = dataRows(ss.sheets['_תור']).filter((r) => r[0] !== '');
  assert.strictEqual(queued.length, 40, 'surplus kept for tomorrow');
  assert.strictEqual(ss.sheets['עסקי'].getLastRow(), 41, 'first run starts right under the header');

  // Day 2: queue (40) + area ג (60) -> 80 written, 20 queued; blank row before the new block.
  const ctx2 = load(ss, g, new Date('2026-10-14T04:05:00Z'));
  ctx2.props = ctx.props;
  ctx2.dailyRun();
  const ra = dataRows(ss.sheets['עסקי']);
  assert.deepStrictEqual(ra[40].slice(0, 13).every((x) => x === ''), true, 'row 42 is the blank separator');
  a = filled(ra); b = filled(dataRows(ss.sheets['מאובטח']));
  assert.strictEqual(a.length, 80); assert.strictEqual(b.length, 80);
  const keys = [...a, ...b].map((r) => ctx2.phoneKey_(r[2]));
  assert.strictEqual(new Set(keys).size, keys.length, 'no phone twice across both tabs');
  console.log('ok  40 + 40 per run, surplus queued, blank row between days, zero duplicates across tabs');

  // Day 3: areas exhausted -> queue (20) written, clear message.
  const ctx3 = load(ss, g, new Date('2026-10-15T04:05:00Z'));
  ctx3.dailyRun();
  assert.strictEqual(filled(dataRows(ss.sheets['עסקי'])).length + filled(dataRows(ss.sheets['מאובטח'])).length, 180);
  assert.match(String(ss.sheets['הגדרות'].cell(3, 7)), /נגמרו האזורים/);
  console.log('ok  areas exhausted: leftovers written and a clear message in "הגדרות"');
}

// ---------- test 3: weekend skip, monthly cap ----------
{
  const ss = makeSpreadsheet(['א']);
  const g = makePlaces({ 'א': [[place({ phone: '050-999-0000' })]] });
  const fri = load(ss, g, new Date('2026-10-16T04:05:00Z')); // Friday
  fri.dailyRun();
  assert.strictEqual(g.calls.length, 0, 'no run on Friday');
  const capped = load(ss, g, new Date('2026-10-18T04:05:00Z')); // Sunday
  capped.props.set('searches:2026-10', '898');
  capped.dailyRun();
  assert.strictEqual(g.calls.length, 0, 'monthly cap respected');
  assert.match(String(ss.sheets['הגדרות'].cell(3, 7)), /החודשית/);
  console.log('ok  Friday/Saturday skipped, monthly cap of 900 respected');
}

// ---------- test 4: manual entry ----------
{
  const ss = makeSpreadsheet([]);
  const t = ss.sheets['עסקי'];
  t.set(2, 2, 'קיימת'); t.set(2, 3, '050-123-4567');
  const ctx = load(ss, makePlaces({}), new Date('2026-10-13T04:05:00Z'));
  let toast = '';
  ss.toast = (m) => { toast = m; };
  const m = ss.sheets['מאובטח'];
  m.set(2, 3, '+972501234567');
  ctx.onEdit({ range: m.getRange(2, 3) });
  assert.match(toast, /עסקי/, 'duplicate across tabs flagged');
  m.set(3, 3, '052 765 4321');
  ctx.onEdit({ range: m.getRange(3, 3) });
  assert.strictEqual(m.cell(3, 4), `=HYPERLINK("https://wa.me/972527654321","פתח צ'אט")`);
  assert.strictEqual(m.cell(3, 5), 'עוד לא נשלחה הודעה');
  console.log('ok  manual entry: duplicate flagged, new row gets WhatsApp button and status');
}

console.log('\nALL PASSED');
