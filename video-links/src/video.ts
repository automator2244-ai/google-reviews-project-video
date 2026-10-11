import { isBot } from "./bots";
import { unavailablePage, videoPage } from "./page";
import { type Env, html, ipHash, notFound, sha256Hex } from "./util";

export const ID_RE = /^[A-Za-z0-9_-]{1,64}$/;
const PROGRESS = new Set([0, 25, 50, 75, 100]);

interface Recipient {
  name: string;
  video_at: string | null;
}

// GET/HEAD /v/{id}: the personal video page. Every visit is logged; bots and previews are flagged, not counted.
export async function handleView(req: Request, env: Env, ctx: ExecutionContext, id: string, origin: string): Promise<Response> {
  let r: Recipient | null = null;
  try {
    r = await env.DB.prepare("SELECT name, video_at FROM recipients WHERE id = ?").bind(id).first<Recipient>();
  } catch (err) {
    console.error("recipient lookup failed", err);
  }
  if (!r?.video_at) return html(unavailablePage(), 404);

  ctx.waitUntil(logClick(req, env, id).catch((err) => console.error("click log failed", err)));
  return html(videoPage(id, r.name, origin));
}

async function logClick(req: Request, env: Env, id: string): Promise<void> {
  const ua = (req.headers.get("user-agent") ?? "").slice(0, 500);
  await env.DB.prepare(
    "INSERT INTO clicks (recipient_id, clicked_at, user_agent, ip_hash, country, is_bot) VALUES (?, ?, ?, ?, ?, ?)",
  )
    .bind(id, new Date().toISOString(), ua, await ipHash(req, env), req.headers.get("cf-ipcountry"), isBot(req) ? 1 : 0)
    .run();
}

// POST /e/{id}: player beacon. Body is one of 0 (play), 25, 50, 75, 100.
export async function handleEvent(req: Request, env: Env, ctx: ExecutionContext, id: string): Promise<Response> {
  const progress = Number((await req.text()).trim());
  if (PROGRESS.has(progress) && !isBot(req)) {
    ctx.waitUntil(
      env.DB.prepare(
        "INSERT INTO watch_events (recipient_id, at, progress) SELECT ?, ?, ? WHERE EXISTS (SELECT 1 FROM recipients WHERE id = ?)",
      )
        .bind(id, new Date().toISOString(), progress, id)
        .run()
        .catch((err) => console.error("event log failed", err)),
    );
  }
  return new Response(null, { status: 204 });
}

const TYPES = { mp4: "video/mp4", jpg: "image/jpeg" } as const;

// GET/HEAD /m/{id}.mp4|jpg: streams from R2 with Range support (iOS Safari will not play video without it).
export async function handleMedia(req: Request, env: Env, id: string, ext: keyof typeof TYPES): Promise<Response> {
  const key = `videos/${id}.${ext}`;
  let obj: R2Object | R2ObjectBody | null;
  try {
    obj = req.method === "HEAD" ? await env.VIDEOS.head(key) : await env.VIDEOS.get(key, { range: req.headers });
  } catch {
    return new Response(null, { status: 416 }); // unsatisfiable Range
  }
  if (!obj) return notFound();

  const headers = new Headers({
    "Content-Type": TYPES[ext],
    "Accept-Ranges": "bytes",
    "Cache-Control": "private, max-age=86400",
    "X-Robots-Tag": "noindex",
    ETag: obj.httpEtag,
  });

  let status = 200;
  let length = obj.size;
  // R2 may report a range even without a Range header, and may carry `suffix: undefined`.
  const range = obj.range as { offset?: number; length?: number; suffix?: number } | undefined;
  if (req.headers.has("range") && range && "body" in obj) {
    const start = range.suffix !== undefined ? obj.size - range.suffix : (range.offset ?? 0);
    const end = range.suffix === undefined && range.length !== undefined ? start + range.length - 1 : obj.size - 1;
    status = 206;
    length = end - start + 1;
    headers.set("Content-Range", `bytes ${start}-${end}/${obj.size}`);
  }
  headers.set("Content-Length", String(length));

  return new Response("body" in obj ? (obj as R2ObjectBody).body : null, { status, headers });
}

const MAX_UPLOAD = 100 * 1024 * 1024;

// PUT /upload/{id}.mp4|jpg with "Authorization: Bearer <pass>". The pass is created with the recipient
// (publish.sh -> register.sql) and is valid for an hour. Uploading the mp4 makes the page live.
export async function handleUpload(req: Request, env: Env, id: string, ext: keyof typeof TYPES): Promise<Response> {
  const pass = (req.headers.get("authorization") ?? "").replace(/^Bearer\s+/i, "");
  const size = Number(req.headers.get("content-length"));
  if (!pass || !req.body) return new Response("Unauthorized", { status: 401 });
  if (!(size > 0 && size <= MAX_UPLOAD)) return new Response("Bad size", { status: 413 });

  const now = Date.now();
  const ok = await env.DB.prepare("SELECT 1 FROM upload_tokens WHERE token_hash = ? AND recipient_id = ? AND expires_at > ?")
    .bind(await sha256Hex(pass), id, now)
    .first();
  if (!ok) return new Response("Unauthorized", { status: 401 });

  await env.VIDEOS.put(`videos/${id}.${ext}`, req.body, { httpMetadata: { contentType: TYPES[ext] } });
  const done = [env.DB.prepare("DELETE FROM upload_tokens WHERE expires_at <= ?").bind(now)];
  if (ext === "mp4") done.push(env.DB.prepare("UPDATE recipients SET video_at = ? WHERE id = ?").bind(new Date().toISOString(), id));
  await env.DB.batch(done);
  return new Response(null, { status: 204 });
}
