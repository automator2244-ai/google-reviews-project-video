// Link preview fetchers, crawlers and scripted clients. Matched case-insensitively against the user-agent.
const BOT_UA = new RegExp(
  [
    "whatsapp", "facebookexternalhit", "facebot", "meta-externalagent", "twitterbot", "slackbot", "telegrambot",
    "linkedinbot", "discordbot", "skypeuripreview", "googlebot", "google-inspectiontool", "adsbot-google",
    "google-pagerenderer", "googleother", "feedfetcher-google", "google-read-aloud", "storebot-google",
    "mediapartners-google", "apis-google", "google favicon", "google-site-verification",
    "bingbot", "bingpreview", "applebot", "yandex", "baiduspider", "duckduckbot", "embedly", "pinterest", "redditbot",
    "headlesschrome", "phantomjs", "puppeteer", "playwright", "lighthouse",
    "curl/", "wget", "python-requests", "python-urllib", "aiohttp", "httpx", "go-http-client", "okhttp", "axios",
    "node-fetch", "undici", "java/", "libwww", "httpclient", "postman",
    "crawler", "spider", "preview", "bot[/;]", "\\bbot\\b",
  ].join("|"),
  "i",
);

export function isBot(req: Request): boolean {
  if (req.method === "HEAD") return true;

  const h = req.headers;
  const purpose = `${h.get("purpose") ?? ""} ${h.get("sec-purpose") ?? ""} ${h.get("x-moz") ?? ""} ${h.get("x-purpose") ?? ""}`;
  if (/prefetch|prerender|preview/i.test(purpose)) return true;

  const ua = h.get("user-agent") ?? "";
  return ua.trim() === "" || BOT_UA.test(ua);
}
