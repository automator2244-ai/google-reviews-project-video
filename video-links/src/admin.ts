import { isAuthed, login, logoutCookie, sameOrigin } from "./auth";
import { dashboardPage, loginPage } from "./page";
import { type Env, html, json, notFound } from "./util";

interface StatRow {
  id: string;
  name: string;
  phone: string | null;
  note: string | null;
  created_at: string;
  video_at: string | null;
  clicks: number;
  first_click: string | null;
  last_click: string | null;
  country: string | null;
  watched: number | null; // null = never pressed play, else highest progress (0/25/50/75/100)
}

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
    case "GET /admin/export.csv":
      return exportCsv(env, url.origin);
  }
  return notFound();
}

async function stats(env: Env): Promise<StatRow[]> {
  const { results } = await env.DB.prepare(
    `SELECT r.id, r.name, r.phone, r.note, r.created_at, r.video_at,
            COUNT(c.id) AS clicks, MIN(c.clicked_at) AS first_click, MAX(c.clicked_at) AS last_click,
            (SELECT c2.country FROM clicks c2 WHERE c2.recipient_id = r.id AND c2.is_bot = 0
              ORDER BY c2.clicked_at DESC LIMIT 1) AS country,
            (SELECT MAX(w.progress) FROM watch_events w WHERE w.recipient_id = r.id) AS watched
     FROM recipients r
     LEFT JOIN clicks c ON c.recipient_id = r.id AND c.is_bot = 0
     GROUP BY r.id
     ORDER BY last_click IS NULL, last_click DESC, r.created_at DESC`,
  ).all<StatRow>();
  return results;
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

function watchedLabel(w: number | null): string {
  if (w === null) return "לא ניגן";
  if (w === 0) return "התחיל";
  return w === 100 ? "עד הסוף" : `${w}%`;
}

async function exportCsv(env: Env, origin: string): Promise<Response> {
  const rows = await stats(env);
  const fmt = (iso: string | null) => (iso ? ilTime.format(new Date(iso)) : "");
  const lines = [
    ["שם", "מזהה", "טלפון", "הערה", "קישור", "כניסות", "צפייה", "כניסה ראשונה", "כניסה אחרונה", "מדינה"],
    ...rows.map((r) => [
      r.name, r.id, r.phone, r.note, `${origin}/v/${r.id}`, r.clicks, watchedLabel(r.watched),
      fmt(r.first_click), fmt(r.last_click), r.country,
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
