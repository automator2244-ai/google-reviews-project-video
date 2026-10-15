import { handleAdmin } from "./admin";
import { type Env, notFound } from "./util";
import { handleEvent, handleMedia, handleUpload, handleView, ID_RE } from "./video";

const ROBOTS = "User-agent: *\nDisallow: /admin\nDisallow: /v/\n";
const MEDIA_RE = /^\/(m|s)\/([A-Za-z0-9_-]{1,64})\.(mp4|jpg)$/;
const UPLOAD_RE = /^\/(upload|upload-shared)\/([A-Za-z0-9_-]{1,64})\.(mp4|jpg)$/;

export default {
  async fetch(req: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
    const url = new URL(req.url);
    const path = url.pathname;
    const read = req.method === "GET" || req.method === "HEAD";

    if (path === "/robots.txt") return new Response(ROBOTS, { headers: { "Content-Type": "text/plain" } });

    if (path.startsWith("/v/")) {
      const id = path.slice(3).replace(/\/$/, "");
      return read && ID_RE.test(id) ? handleView(req, env, ctx, id, url.origin) : notFound();
    }

    const media = path.match(MEDIA_RE);
    if (media) {
      const folder = media[1] === "s" ? "shared" : "videos";
      return read ? handleMedia(req, env, `${folder}/${media[2]}.${media[3]}`, media[3] as "mp4" | "jpg") : notFound();
    }

    const upload = path.match(UPLOAD_RE);
    if (upload) {
      const shared = upload[1] === "upload-shared";
      return req.method === "PUT" ? handleUpload(req, env, upload[2], upload[3] as "mp4" | "jpg", shared) : notFound();
    }

    if (path.startsWith("/e/")) {
      const id = path.slice(3);
      return req.method === "POST" && ID_RE.test(id) ? handleEvent(req, env, ctx, id) : notFound();
    }

    if (path === "/admin" || path.startsWith("/admin/")) return handleAdmin(req, env, url);

    return notFound();
  },
} satisfies ExportedHandler<Env>;
