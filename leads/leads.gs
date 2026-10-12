/**
 * Dentist leads: fills the "עסקי" and "מאובטח" tabs with dentists from Google Places,
 * every Sunday to Thursday around 07:00 (Israel time). Only clinics with a mobile number (05x) and
 * 15 to 70 Google reviews are added, and a phone number never appears twice across both tabs.
 *
 * Every value comes straight from the Google Places response. A field Google does not return
 * (website, rating, review count) stays empty; nothing is guessed or filled in.
 *
 * Areas ("הגדרות" A2:A) are searched in order. A row is either a place name ("נתניה מרכז") or a
 * map square given by its center ("32.0765,34.7845"), searched with a location restriction so squares
 * don't overlap. A square that hits Google's 60-result limit is split into four smaller ones.
 *
 * Setup (once): Project Settings > Script properties > add PLACES_KEY, then run `setup`.
 */

const TABS = ['עסקי', 'מאובטח'];
const SETTINGS = 'הגדרות';
const SEEN = '_נסרקו';   // every place already looked at, including landlines (never fetched twice)
const QUEUE = '_תור';    // mobile clinics found beyond today's quota, used first next time

const PER_TAB = 40;             // new clinics per tab per run
const MIN_REVIEWS = 15;         // only clinics with 15 to 70 Google reviews (inclusive)
const MAX_REVIEWS = 70;
// No cap on searches (owner's choice): a run searches until both tabs have 40 or the areas run out.
// Google bills about $35 per 1,000 searches beyond the first 1,000 free each month.
const MAX_RUN_MS = 5 * 60 * 1000; // Apps Script kills a run at 6 minutes; stop before that and save
const PAGES_PER_AREA = 3;       // Google returns at most 60 results (3 x 20) per query
const TZ = 'Asia/Jerusalem';
const CELL_LAT = 0.011; // map square of about 1.2 x 1.2 km
const CELL_LNG = 0.013;

const STATUS_NEW = 'עוד לא נשלחה הודעה';
const NCOLS = 13; // A..M are written; N holds the phone-key formula and is never touched
// A date | B name | C phone | D WhatsApp | E status | F rating | G reviews | H website
// I city | J address | K Google Maps | L notes | M place id

const FIELDS = [
  'places.id', 'places.displayName', 'places.nationalPhoneNumber', 'places.internationalPhoneNumber',
  'places.websiteUri', 'places.rating', 'places.userRatingCount', 'places.formattedAddress',
  'places.googleMapsUri', 'places.businessStatus', 'places.types', 'places.addressComponents', 'nextPageToken',
].join(',');

// ---------- entry points ----------

function onOpen() {
  SpreadsheetApp.getUi().createMenu('לידים')
    .addItem('מלא עכשיו', 'fillNow')
    .addItem('התקנה (פעם אחת)', 'setup')
    .addToUi();
}

/** Installs the daily trigger. Run once from the editor (or the menu) and approve the permissions. */
function setup() {
  if (!PropertiesService.getScriptProperties().getProperty('PLACES_KEY')) {
    throw new Error('חסר PLACES_KEY: Project Settings > Script properties > Add script property');
  }
  ScriptApp.getProjectTriggers()
    .filter((t) => t.getHandlerFunction() === 'dailyRun')
    .forEach((t) => ScriptApp.deleteTrigger(t));
  ScriptApp.newTrigger('dailyRun').timeBased().everyDays(1).atHour(7).nearMinute(0).inTimezone(TZ).create();
  status_({ message: 'מותקן: ירוץ כל יום ראשון עד חמישי בסביבות 07:00' });
}

/** Daily trigger: Sunday to Thursday only. */
function dailyRun() {
  const isoDay = Number(Utilities.formatDate(new Date(), TZ, 'u')); // 1 = Monday ... 7 = Sunday
  if (isoDay === 5 || isoDay === 6) return; // Friday, Saturday
  fill_();
}

function fillNow() {
  const r = fill_();
  SpreadsheetApp.getActive().toast(`נוספו ${r.added[0]} לעסקי ו-${r.added[1]} למאובטח. ${r.message}`, 'לידים', 10);
}

/** Manual entry of a phone that already exists anywhere in the two tabs: flag it right away. */
function onEdit(e) {
  const sheet = e.range.getSheet();
  if (TABS.indexOf(sheet.getName()) < 0 || e.range.getColumn() !== 3 || e.range.getRow() < 2) return;
  const key = phoneKey_(e.range.getValue());
  if (!key) return;
  const row = e.range.getRow();
  const where = findPhone_(key, sheet.getName(), row);
  if (where) {
    SpreadsheetApp.getActive().toast(`המספר כבר קיים בלשונית "${where.tab}", שורה ${where.row}`, 'כפילות', 10);
    return;
  }
  // A clean manual row gets the same date, WhatsApp button and status as an automatic one.
  const cells = sheet.getRange(row, 1, 1, 5).getValues()[0];
  if (!cells[0]) sheet.getRange(row, 1).setValue(new Date());
  if (!cells[3]) sheet.getRange(row, 4).setFormula(waFormula_(key));
  if (!cells[4]) sheet.getRange(row, 5).setValue(STATUS_NEW);
}

// ---------- the fill ----------

function fill_() {
  const lock = LockService.getScriptLock();
  if (!lock.tryLock(30000)) return { added: [0, 0], message: 'ריצה אחרת כבר פועלת' };
  try {
    return fillLocked_();
  } finally {
    lock.releaseLock();
  }
}

function fillLocked_() {
  const ss = SpreadsheetApp.getActive();
  const key = PropertiesService.getScriptProperties().getProperty('PLACES_KEY');
  if (!key) return status_({ added: [0, 0], message: 'חסר PLACES_KEY בהגדרות הסקריפט' });

  const tabs = TABS.map((n) => ss.getSheetByName(n));
  const settings = ss.getSheetByName(SETTINGS);
  const seenSheet = ss.getSheetByName(SEEN);
  const queueSheet = ss.getSheetByName(QUEUE);

  const knownPhones = new Set();
  tabs.forEach((t) => columnValues_(t, 3).forEach((v) => { const k = phoneKey_(v); if (k) knownPhones.add(k); }));
  const seenIds = new Set(columnValues_(seenSheet, 1).filter(String));
  tabs.forEach((t) => columnValues_(t, 13).filter(String).forEach((id) => seenIds.add(id)));

  const buckets = [[], []];
  const room = () => buckets[0].length < PER_TAB || buckets[1].length < PER_TAB;
  const take = (lead) => {
    const i = buckets[0].length <= buckets[1].length ? 0 : 1;
    const j = buckets[i].length < PER_TAB ? i : 1 - i;
    buckets[j].push(lead);
  };
  const leftover = [];

  // 1. Yesterday's surplus first (re-checked, a phone may have been typed in by hand since).
  const queued = readQueue_(queueSheet);
  queued.forEach((lead) => {
    if (!inReviewRange_(lead.reviews) || knownPhones.has(lead.key)) return;
    knownPhones.add(lead.key);
    if (room()) take(lead); else leftover.push(lead);
  });

  // 2. New searches, area by area, until both tabs are full or a limit is reached.
  const month = Utilities.formatDate(new Date(), TZ, 'yyyy-MM');
  const props = PropertiesService.getScriptProperties();
  let usedMonth = Number(props.getProperty('searches:' + month) || 0);
  const started = Date.now();
  let message = '';
  const seenRows = [];

  while (room()) {
    if (Date.now() - started > MAX_RUN_MS) { message = 'נעצר אחרי 5 דקות (המגבלה של גוגל לריצה). ממשיך בריצה הבאה'; break; }
    const area = nextArea_(settings);
    if (!area) { message = 'נגמרו האזורים ברשימה. הוסף אזורים בלשונית "הגדרות"'; break; }

    let token = '';
    let found = 0;
    let total = 0;
    let failed = false;
    for (let page = 0; page < PAGES_PER_AREA; page++) {
      const res = searchText_(key, area.name, token);
      usedMonth++;
      if (res.error) { message = 'שגיאה מגוגל: ' + res.error; failed = true; break; }
      total += (res.places || []).length;
      (res.places || []).forEach((p) => {
        if (!p.id || seenIds.has(p.id)) return;
        seenIds.add(p.id);
        const lead = toLead_(p);
        seenRows.push([p.id, lead.name, lead.phone, lead.kind, area.name, new Date()]);
        if (lead.kind !== 'נייד' || !inReviewRange_(lead.reviews) || knownPhones.has(lead.key)) return;
        knownPhones.add(lead.key);
        found++;
        if (room()) take(lead); else leftover.push(lead);
      });
      token = res.nextPageToken || '';
      if (!token) break;
    }
    props.setProperty('searches:' + month, String(usedMonth));
    if (failed) break;
    markArea_(settings, area.row, found);
    // Google stops at 60 results: a full square may hold more, so search its four quarters next.
    const cell = parseCell_(area.name);
    if (cell && total >= PAGES_PER_AREA * 20) splitCell_(settings, area.row, cell);
  }

  // 3. Write: a blank row between runs, then the new rows.
  const day = new Date();
  buckets.forEach((leads, i) => appendLeads_(tabs[i], leads.map((l) => leadRow_(l, day))));
  appendRows_(seenSheet, seenRows);
  writeQueue_(queueSheet, leftover);

  const added = [buckets[0].length, buckets[1].length];
  if (!message && (added[0] < PER_TAB || added[1] < PER_TAB)) message = 'נמצאו פחות מ-40';
  return status_({ added, searches: usedMonth, message: message || 'הכל תקין', waiting: leftover.length });
}

// ---------- Google Places ----------

function searchText_(key, area, pageToken) {
  const cell = parseCell_(area);
  const body = {
    textQuery: cell ? 'רופא שיניים' : 'רופא שיניים ' + area,
    includedType: 'dentist',
    strictTypeFiltering: true,
    languageCode: 'he',
    regionCode: 'IL',
    pageSize: 20,
  };
  if (cell) {
    const h = cell.scale / 2;
    body.locationRestriction = { rectangle: {
      low: { latitude: cell.lat - CELL_LAT * h, longitude: cell.lng - CELL_LNG * h },
      high: { latitude: cell.lat + CELL_LAT * h, longitude: cell.lng + CELL_LNG * h },
    } };
  }
  if (pageToken) body.pageToken = pageToken;
  const res = UrlFetchApp.fetch('https://places.googleapis.com/v1/places:searchText', {
    method: 'post',
    contentType: 'application/json',
    headers: { 'X-Goog-Api-Key': key, 'X-Goog-FieldMask': FIELDS },
    payload: JSON.stringify(body),
    muteHttpExceptions: true,
  });
  const json = JSON.parse(res.getContentText() || '{}');
  if (res.getResponseCode() !== 200) return { error: (json.error && json.error.message) || 'HTTP ' + res.getResponseCode() };
  return json;
}

/** "32.0765,34.7845" or "32.0765,34.7845,0.5" (a quarter-size square) -> {lat, lng, scale}. */
function parseCell_(area) {
  const m = String(area).trim().match(/^(-?\d+\.\d+)\s*,\s*(-?\d+\.\d+)(?:\s*,\s*(\d*\.?\d+))?$/);
  return m ? { lat: Number(m[1]), lng: Number(m[2]), scale: m[3] ? Number(m[3]) : 1 } : null;
}

function splitCell_(settings, row, cell) {
  const s = cell.scale / 2;
  const dl = (CELL_LAT * s) / 2;
  const dg = (CELL_LNG * s) / 2;
  const f = (x) => x.toFixed(5);
  const rows = [[-1, -1], [-1, 1], [1, -1], [1, 1]].map(([a, b]) => [`${f(cell.lat + a * dl)},${f(cell.lng + b * dg)},${s}`]);
  settings.insertRowsAfter(row, rows.length);
  settings.getRange(row + 1, 1, rows.length, 1).setValues(rows);
}

/** The city as Google gives it: the address's locality, else the last non-numeric part of the address. */
function city_(p) {
  const loc = (p.addressComponents || []).find((c) => (c.types || []).indexOf('locality') >= 0);
  if (loc && loc.longText) return loc.longText;
  const parts = String(p.formattedAddress || '').split(',').map((x) => x.trim()).filter((x) => x && !/^\d+$/.test(x));
  return parts.length > 1 ? parts[parts.length - 1] : '';
}

/** A clinic with no review count on Google counts as 0 reviews, so it is outside the range. */
function inReviewRange_(reviews) {
  const n = Number(reviews || 0);
  return n >= MIN_REVIEWS && n <= MAX_REVIEWS;
}

/** Only fields Google returned; anything missing stays empty. */
function toLead_(p) {
  const phone = p.nationalPhoneNumber || '';
  const key = phoneKey_(phone || p.internationalPhoneNumber || '');
  let kind = 'ללא טלפון';
  if (p.businessStatus !== 'OPERATIONAL') kind = 'לא פעיל';
  else if (key) kind = /^05\d{8}$/.test(key) ? 'נייד' : 'קווי';
  return {
    id: p.id,
    name: (p.displayName && p.displayName.text) || '',
    phone,
    key,
    kind,
    rating: typeof p.rating === 'number' ? p.rating : '',
    reviews: typeof p.userRatingCount === 'number' ? p.userRatingCount : '',
    website: p.websiteUri || '',
    area: city_(p),
    address: p.formattedAddress || '',
    maps: p.googleMapsUri || '',
  };
}

// ---------- sheet helpers ----------

/** 050-123-4567, +972 50-123-4567, 00972... -> 0501234567 (same rule as the sheet's key column). */
function phoneKey_(v) {
  let d = String(v || '').replace(/\D/g, '');
  if (d.startsWith('00')) d = d.slice(2);
  if (d.startsWith('972')) d = '0' + d.slice(3);
  return d.length >= 9 ? d : '';
}

function waFormula_(key) {
  return `=HYPERLINK("https://wa.me/972${key.slice(1)}","פתח צ'אט")`;
}

/** Text that Sheets would read as a formula is stored as plain text. */
function text_(s) {
  return /^[=+\-@]/.test(s) ? "'" + s : s;
}

function leadRow_(l, day) {
  return [
    day, text_(l.name), l.phone, waFormula_(l.key), STATUS_NEW, l.rating, l.reviews, l.website,
    text_(l.area), text_(l.address), l.maps ? `=HYPERLINK("${l.maps}","פתח במפות")` : '', '', l.id,
  ];
}

function columnValues_(sheet, col) {
  const last = sheet.getLastRow();
  if (last < 2) return [];
  return sheet.getRange(2, col, last - 1, 1).getValues().map((r) => r[0]);
}

/** Last row with a name or phone (the key formula in N is ignored). */
function lastDataRow_(sheet) {
  const last = sheet.getLastRow();
  if (last < 2) return 1;
  const vals = sheet.getRange(2, 2, last - 1, 2).getValues();
  for (let i = vals.length - 1; i >= 0; i--) if (vals[i][0] !== '' || vals[i][1] !== '') return i + 2;
  return 1;
}

function appendLeads_(sheet, rows) {
  if (!rows.length) return;
  const last = lastDataRow_(sheet);
  const start = last === 1 ? 2 : last + 2; // one empty row between runs
  ensureRows_(sheet, start + rows.length - 1);
  sheet.getRange(start, 3, rows.length, 1).setNumberFormat('@');
  sheet.getRange(start, 1, rows.length, NCOLS).setValues(rows);
}

function appendRows_(sheet, rows) {
  if (!rows.length) return;
  const start = sheet.getLastRow() + 1;
  ensureRows_(sheet, start + rows.length - 1);
  sheet.getRange(start, 1, rows.length, rows[0].length).setValues(rows);
}

function ensureRows_(sheet, needed) {
  const max = sheet.getMaxRows();
  if (needed > max) sheet.insertRowsAfter(max, needed - max + 200);
}

function findPhone_(key, editedTab, editedRow) {
  const ss = SpreadsheetApp.getActive();
  for (const tab of TABS) {
    const vals = columnValues_(ss.getSheetByName(tab), 3);
    for (let i = 0; i < vals.length; i++) {
      if (tab === editedTab && i + 2 === editedRow) continue;
      if (phoneKey_(vals[i]) === key) return { tab, row: i + 2 };
    }
  }
  return null;
}

// Areas live in "הגדרות" A2:A, with status in B ("נסרק" once done), date in C and count in D.
function nextArea_(settings) {
  const last = settings.getLastRow();
  if (last < 2) return null;
  const vals = settings.getRange(2, 1, last - 1, 2).getValues();
  for (let i = 0; i < vals.length; i++) {
    const name = String(vals[i][0]).trim();
    if (name && vals[i][1] !== 'נסרק') return { name, row: i + 2 };
  }
  return null;
}

function markArea_(settings, row, found) {
  settings.getRange(row, 2, 1, 3).setValues([['נסרק', new Date(), found]]);
}

const QUEUE_COLS = ['id', 'name', 'phone', 'key', 'kind', 'rating', 'reviews', 'website', 'area', 'address', 'maps'];

function readQueue_(sheet) {
  const last = sheet.getLastRow();
  if (last < 2) return [];
  return sheet.getRange(2, 1, last - 1, QUEUE_COLS.length).getValues()
    .map((r) => Object.fromEntries(QUEUE_COLS.map((c, i) => [c, c === 'key' ? String(r[i]) : r[i]])));
}

function writeQueue_(sheet, leads) {
  const last = sheet.getLastRow();
  if (last >= 2) sheet.getRange(2, 1, last - 1, QUEUE_COLS.length).clearContent();
  if (!leads.length) return;
  ensureRows_(sheet, leads.length + 1);
  sheet.getRange(2, 4, leads.length, 1).setNumberFormat('@');
  sheet.getRange(2, 1, leads.length, QUEUE_COLS.length).setValues(leads.map((l) => QUEUE_COLS.map((c) => l[c])));
}

/** Status panel in "הגדרות" F2:G6. */
function status_(r) {
  const s = SpreadsheetApp.getActive().getSheetByName(SETTINGS);
  const now = Utilities.formatDate(new Date(), TZ, 'dd/MM/yyyy HH:mm');
  const rows = [['ריצה אחרונה', now], ['הודעה', r.message || '']];
  if (r.added) rows.push(['נוספו', `עסקי ${r.added[0]}, מאובטח ${r.added[1]}`]);
  if (r.searches !== undefined) rows.push(['חיפושים החודש', r.searches]);
  if (r.waiting !== undefined) rows.push(['ממתינים בתור למחר', r.waiting]);
  s.getRange(2, 6, 5, 2).clearContent();
  s.getRange(2, 6, rows.length, 2).setValues(rows);
  return r;
}
