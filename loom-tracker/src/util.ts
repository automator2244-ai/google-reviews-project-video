export interface Env {
  DB: D1Database;
  LOOM_URL: string;
  ADMIN_PASSWORD: string;
  IP_SALT: string;
}

const enc = new TextEncoder();

function toHex(buf: ArrayBuffer): string {
  return [...new Uint8Array(buf)].map((b) => b.toString(16).padStart(2, "0")).join("");
}

export async function sha256Hex(input: string): Promise<string> {
  return toHex(await crypto.subtle.digest("SHA-256", enc.encode(input)));
}

export async function hmacHex(key: string, data: string): Promise<string> {
  const k = await crypto.subtle.importKey("raw", enc.encode(key), { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
  return toHex(await crypto.subtle.sign("HMAC", k, enc.encode(data)));
}

// Compares two strings without leaking where they differ. Both are hashed first so lengths match.
export async function safeEqual(a: string, b: string): Promise<boolean> {
  const [ha, hb] = await Promise.all([sha256Hex(a), sha256Hex(b)]);
  let diff = 0;
  for (let i = 0; i < ha.length; i++) diff |= ha.charCodeAt(i) ^ hb.charCodeAt(i);
  return diff === 0 && a.length === b.length;
}

// 32 unambiguous characters (no 0/o/1/l), so `byte & 31` is unbiased.
const ID_ALPHABET = "abcdefghijkmnpqrstuvwxyz23456789";

export function randomId(len = 8): string {
  const bytes = crypto.getRandomValues(new Uint8Array(len));
  return [...bytes].map((b) => ID_ALPHABET[b & 31]).join("");
}

export async function ipHash(req: Request, env: Env): Promise<string | null> {
  const ip = req.headers.get("cf-connecting-ip");
  if (!ip || !env.IP_SALT) return null;
  return sha256Hex(env.IP_SALT + ip);
}

const NO_INDEX = { "Cache-Control": "no-store", "X-Robots-Tag": "noindex, nofollow" };

export function notFound(): Response {
  return new Response("Not found", { status: 404, headers: { ...NO_INDEX, "Content-Type": "text/plain" } });
}

export function redirect(location: string): Response {
  return new Response(null, {
    status: 302,
    headers: { ...NO_INDEX, Location: location, "Referrer-Policy": "no-referrer" },
  });
}

export function json(data: unknown, status = 200): Response {
  return new Response(JSON.stringify(data), {
    status,
    headers: { ...NO_INDEX, "Content-Type": "application/json; charset=utf-8" },
  });
}

const ADMIN_CSP =
  "default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'self'; " +
  "img-src 'self' data:; form-action 'self'; frame-ancestors 'none'; base-uri 'none'";

export function html(body: string, status = 200, extra: Record<string, string> = {}): Response {
  return new Response(body, {
    status,
    headers: {
      ...NO_INDEX,
      "Content-Type": "text/html; charset=utf-8",
      "Content-Security-Policy": ADMIN_CSP,
      "X-Content-Type-Options": "nosniff",
      "Referrer-Policy": "no-referrer",
      ...extra,
    },
  });
}

export function escapeHtml(s: string): string {
  return s.replace(/[&<>"']/g, (c) => `&#${c.charCodeAt(0)};`);
}
