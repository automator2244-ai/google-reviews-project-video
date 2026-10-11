import { isAuthed, login, logoutCookie, sameOrigin } from "./auth";
import { dashboardPage, loginPage } from "./page";
import { type Env, html, json, notFound, randomId } from "./util";

interface StatRow {
  id: string;
  name: string;
  phone: string | null;
  note: string | null;
  created_at: string;
  clicks: number;
  first_click: string | null;
  last_click: string | null;
  country: string | null;
}

const MAX_LINES = 500;

export async function handleAdmin(req: Request, env: Env, url: URL): Promise<Response> {
  const path = url.pathname.replace(/\/+$/, "") || "/admin";

  if (path === "/admin/login" && req.method === "POST") {
    if (!sameOrigin(req, url)) return new Response("Forbidden", { status: 403 });
    const form = await req.formData();
    const result = await login(req, env, String(form.get("password") ?? ""));
    if (result.ok) return new Response(null, { status: 303, headers: { Location: "/admin", "Set-Cookie": result.cookie } });
    const msg = result.status === 429 ? "יותר מדי ניסיונות. נסה שוב בעוד 15 דקות." : "סיסמה שגויה.";
    return html(loginPage(result.status === 503 ? "הסיסמה לא הוגדרה בשרת." : msg), result.status);
  }

  if (!(await isAuthed(req, env))) {
    return path === "/admin" && req.method === "GET" ? html(loginPage(), 401) : json({ error: "unauthorized" }, 401);
  }

  if (req.method === "POST" && !sameOrigin(req, url)) return new Response("Forbidden", { status: 403 });

  switch (`${req.method} ${path}`) {
    case "GET /admin":
      return html(dashboardPage(url.origin));
    case "POST /admin/logout":
      return new Response(null, { status: 303, headers: { Location: "/admin", "Set-Cookie": logoutCookie } });
    case "GET /admin/api/stats":
      return json({ rows: await stats(env) });
    case "POST /admin/api/recipients":
      return createRecipients(req, env, url.origin);
    case "GET /admin/export.csv":
      return exportCsv(env, url.origin);
  }
  return notFound();
}

async function stats(env: Env): Promise<StatRow[]> {
  const { results } = await env.DB.prepare(
    `SELECT r.id, r.name, r.phone, r.note, r.created_at,
            COUNT(c.id) AS clicks, MIN(c.clicked_at) AS first_click, MAX(c.clicked_at) AS last_click,
            (SELECT c2.country FROM clicks c2 WHERE c2.recipient_id = r.id AND c2.is_bot = 0
              ORDER BY c2.clicked_at DESC LIMIT 1) AS country
     FROM recipients r
     LEFT JOIN clicks c ON c.recipient_id = r.id AND c.is_bot = 0
     GROUP BY r.id
     ORDER BY last_click IS NULL, last_click DESC, r.created_at DESC`,
  ).all<StatRow>();
  return results;
}

// "05x..." -> "9725x...", "+972 5x..." -> "9725x...", "00972..." -> "972...".
export function normalizePhone(raw: string): string | null {
  let d = raw.replace(/\D/g, "");
  if (d.startsWith("00")) d = d.slice(2);
  else if (d.startsWith("0")) d = "972" + d.slice(1);
  return d.length >= 9 && d.length <= 15 ? d : null;
}

const looksLikePhone = (s: string) => /^[+\d][\d\s()-]{6,}$/.test(s.trim());

export function parseLines(text: string): { name: string; phone: string | null; note: string | null }[] {
  return text
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean)
    .slice(0, MAX_LINES)
    .map((line) => {
      let parts = line.split(line.includes("\t") ? "\t" : ",").map((p) => p.trim());
      // Accept "phone, name" too.
      if (parts.length >= 2 && looksLikePhone(parts[0]) && !looksLikePhone(parts[1])) parts = [parts[1], parts[0], ...parts.slice(2)];
      const [name, phone = "", ...rest] = parts;
      return {
        name: name.slice(0, 120),
        phone: phone ? normalizePhone(phone) : null,
        note: rest.join(", ").slice(0, 500) || null,
      };
    })
    .filter((r) => r.name);
}

async function createRecipients(req: Request, env: Env, origin: string): Promise<Response> {
  const body = await req.json<{ text?: string }>().catch(() => ({}) as { text?: string });
  const rows = parseLines(String(body.text ?? ""));
  if (rows.length === 0) return json({ error: "empty" }, 400);

  const now = new Date().toISOString();
  const created = rows.map((r) => ({ ...r, id: randomId() }));
  const insert = env.DB.prepare("INSERT INTO recipients (id, name, phone, note, created_at) VALUES (?, ?, ?, ?, ?)");
  await env.DB.batch(created.map((r) => insert.bind(r.id, r.name, r.phone, r.note, now)));

  return json({ rows: created.map((r) => ({ ...r, link: `${origin}/v/${r.id}` })) });
}

const ilTime = new Intl.DateTimeFormat("he-IL", {
  timeZone: "Asia/Jerusalem",
  dateStyle: "short",
  timeStyle: "short",
});

function csvCell(v: unknown): string {
  let s = v == null ? "" : String(v);
  if (/^[=+\-@\t\r]/.test(s)) s = "'" + s; // keep Excel from treating names as formulas
  return /[",\r\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
}

async function exportCsv(env: Env, origin: string): Promise<Response> {
  const rows = await stats(env);
  const fmt = (iso: string | null) => (iso ? ilTime.format(new Date(iso)) : "");
  const lines = [
    ["שם", "מזהה", "טלפון", "הערה", "קישור", "קליקים", "קליק ראשון", "קליק אחרון", "מדינה"],
    ...rows.map((r) => [
      r.name, r.id, r.phone, r.note, `${origin}/v/${r.id}`, r.clicks, fmt(r.first_click), fmt(r.last_click), r.country,
    ]),
  ];
  const csv = "﻿" + lines.map((l) => l.map(csvCell).join(",")).join("\r\n");
  return new Response(csv, {
    headers: {
      "Content-Type": "text/csv; charset=utf-8",
      "Content-Disposition": `attachment; filename="clicks-${new Date().toISOString().slice(0, 10)}.csv"`,
      "Cache-Control": "no-store",
    },
  });
}
