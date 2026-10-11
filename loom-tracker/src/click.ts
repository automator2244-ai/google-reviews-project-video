import { isBot } from "./bots";
import { type Env, ipHash, notFound, redirect } from "./util";

export const ID_RE = /^[A-Za-z0-9_-]{1,64}$/;

export async function handleClick(req: Request, env: Env, ctx: ExecutionContext, id: string): Promise<Response> {
  // Every valid id is logged and redirected the same way, whether or not it exists, so the response reveals nothing.
  ctx.waitUntil(logClick(req, env, id).catch((err) => console.error("click log failed", err)));

  let target = env.LOOM_URL;
  try {
    const row = await env.DB.prepare("SELECT target_url FROM recipients WHERE id = ?")
      .bind(id)
      .first<{ target_url: string | null }>();
    if (row?.target_url) target = row.target_url;
  } catch (err) {
    console.error("target lookup failed", err);
  }

  return target ? redirect(target) : notFound();
}

async function logClick(req: Request, env: Env, id: string): Promise<void> {
  const ua = (req.headers.get("user-agent") ?? "").slice(0, 500);
  await env.DB.prepare(
    "INSERT INTO clicks (recipient_id, clicked_at, user_agent, ip_hash, country, is_bot) VALUES (?, ?, ?, ?, ?, ?)",
  )
    .bind(id, new Date().toISOString(), ua, await ipHash(req, env), req.headers.get("cf-ipcountry"), isBot(req) ? 1 : 0)
    .run();
}
