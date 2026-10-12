export interface Env {
  DB: D1Database;
  VIDEOS: R2Bucket;
  IP_SALT: string;
}

const enc = new TextEncoder();

function toHex(buf: ArrayBuffer): string {
  return [...new Uint8Array(buf)].map((b) => b.toString(16).padStart(2, "0")).join("");
}

export async function sha256Hex(input: string): Promise<string> {
  return toHex(await crypto.subtle.digest("SHA-256", enc.encode(input)));
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

export function json(data: unknown, status = 200): Response {
  return new Response(JSON.stringify(data), {
    status,
    headers: { ...NO_INDEX, "Content-Type": "application/json; charset=utf-8" },
  });
}

const CSP =
  "default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'self'; " +
  "img-src 'self' data:; media-src 'self'; form-action 'self'; frame-ancestors 'none'; base-uri 'none'";

export function html(body: string, status = 200, extra: Record<string, string> = {}): Response {
  return new Response(body, {
    status,
    headers: {
      ...NO_INDEX,
      "Content-Type": "text/html; charset=utf-8",
      "Content-Security-Policy": CSP,
      "X-Content-Type-Options": "nosniff",
      "Referrer-Policy": "no-referrer",
      ...extra,
    },
  });
}

export function escapeHtml(s: string): string {
  return s.replace(/[&<>"']/g, (c) => `&#${c.charCodeAt(0)};`);
}
