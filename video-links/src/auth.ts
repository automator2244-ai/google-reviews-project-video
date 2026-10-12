import { type Env, hmacHex, ipHash, safeEqual } from "./util";

const COOKIE = "admin_session";
const SESSION_MS = 30 * 24 * 60 * 60 * 1000;
const WINDOW_MS = 15 * 60 * 1000;
const MAX_FAILS = 5;

// Signing key depends on the password, so changing ADMIN_PASSWORD logs out every session.
const signingKey = (env: Env) => `${env.ADMIN_PASSWORD}|${env.IP_SALT}`;

export async function isAuthed(req: Request, env: Env): Promise<boolean> {
  if (!env.ADMIN_PASSWORD) return false;
  const value = (req.headers.get("cookie") ?? "")
    .split(";")
    .map((c) => c.trim())
    .find((c) => c.startsWith(`${COOKIE}=`))
    ?.slice(COOKIE.length + 1);
  if (!value) return false;

  const [exp, sig] = value.split(".");
  if (!exp || !sig || !(Number(exp) > Date.now())) return false;
  return safeEqual(sig, await hmacHex(signingKey(env), `session.${exp}`));
}

// Same-origin check for state-changing requests (on top of SameSite=Strict).
// Browsers send Sec-Fetch-Site; Origin is the fallback for clients that don't.
export function sameOrigin(req: Request, url: URL): boolean {
  const site = req.headers.get("sec-fetch-site");
  if (site) return site === "same-origin";
  const origin = req.headers.get("origin");
  return origin === null || origin === url.origin;
}

export type LoginResult = { ok: true; cookie: string } | { ok: false; status: 401 | 429 | 503 };

export async function login(req: Request, env: Env, password: string): Promise<LoginResult> {
  if (!env.ADMIN_PASSWORD) return { ok: false, status: 503 };

  const who = (await ipHash(req, env)) ?? "unknown";
  const now = Date.now();
  await env.DB.prepare("DELETE FROM login_attempts WHERE ts < ?").bind(now - WINDOW_MS).run();
  const row = await env.DB.prepare("SELECT COUNT(*) AS n FROM login_attempts WHERE ip_hash = ?")
    .bind(who)
    .first<{ n: number }>();
  if ((row?.n ?? 0) >= MAX_FAILS) return { ok: false, status: 429 };

  // Trimmed on both sides: a secret pasted into the dashboard often picks up a trailing newline or space.
  if (!(await safeEqual(password.trim(), env.ADMIN_PASSWORD.trim()))) {
    await env.DB.prepare("INSERT INTO login_attempts (ip_hash, ts) VALUES (?, ?)").bind(who, now).run();
    return { ok: false, status: 401 };
  }

  await env.DB.prepare("DELETE FROM login_attempts WHERE ip_hash = ?").bind(who).run();
  const exp = String(now + SESSION_MS);
  const sig = await hmacHex(signingKey(env), `session.${exp}`);
  return {
    ok: true,
    cookie: `${COOKIE}=${exp}.${sig}; Path=/admin; HttpOnly; Secure; SameSite=Strict; Max-Age=${SESSION_MS / 1000}`,
  };
}

export const logoutCookie = `${COOKIE}=; Path=/admin; HttpOnly; Secure; SameSite=Strict; Max-Age=0`;
