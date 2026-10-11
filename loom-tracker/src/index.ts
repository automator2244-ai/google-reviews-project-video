import { handleAdmin } from "./admin";
import { handleClick, ID_RE } from "./click";
import { type Env, notFound } from "./util";

const ROBOTS = "User-agent: *\nDisallow: /admin\nDisallow: /v/\n";

export default {
  async fetch(req: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    const url = new URL(req.url);
    const path = url.pathname;

    if (path === "/robots.txt") return new Response(ROBOTS, { headers: { "Content-Type": "text/plain" } });

    if (path.startsWith("/v/")) {
      const id = path.slice(3).replace(/\/$/, "");
      if ((req.method !== "GET" && req.method !== "HEAD") || !ID_RE.test(id)) return notFound();
      return handleClick(req, env, ctx, id);
    }

    if (path === "/admin" || path.startsWith("/admin/")) return handleAdmin(req, env, url);

    return notFound();
  },
} satisfies ExportedHandler<Env>;
