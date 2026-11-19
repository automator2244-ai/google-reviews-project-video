#!/usr/bin/env python3
"""Build a Reel (1080x1920, 30fps) from real footage: stock clips or Benaya's recordings, with text on top.

Usage: python3 clipreel.py <post_dir>
Reads <post_dir>/clip.json, writes <post_dir>/reel.mp4, poster.jpg and music.json.

clip.json:
{
  "mood": "light",              # music mood from music.json (or "music": "<track name>")
  "music_vol": 0.5,             # 0.5 for silent footage, about 0.12 under a voice
  "shots": [                    # hard cuts, in order
    {"src": "footage/1551.mp4", # path relative to instagram/
     "ss": 0.0, "dur": 2.4,     # where to start in the source, and how long the shot is on screen
     "focus": 0.5,              # 0..1: which part of a wide source stays in the vertical crop
     "focus_y": 0.5,
     "zoom": [1.0, 1.08],       # slow push in or out over the shot
     "voice": false,            # true keeps the source audio (a recording of Benaya)
     "dim": 0.0}                # 0..1 darkens the shot, for text or a card on top
  ],
  "overlays": [                 # on the timeline of the finished reel
    {"t": 0.0, "d": 2.4, "kind": "hook", "text": "line one\\n*accent* line", "y": 420, "size": 112},
    {"t": 3.0, "d": 1.2, "kind": "cap", "text": "caption under a voice", "y": 1210},
    {"t": 5.0, "d": 4.0, "kind": "html", "html": "<div ...>", "pop": true}
  ]
}
Text kinds: hook (big, white with a dark outline), cap (white rounded box, dark text), tag (small brand line).
*word* = accent colour. Everything stays in the Reels safe zone: y 300 to 1440.
No brand design language here on purpose: these should look like something filmed, not designed.
"""
import html
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
IG = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
import reel as R  # noqa: E402  (music catalogue and log)

W, H, FPS = 1080, 1920, 30

CSS = """
@font-face{font-family:Heebo;src:url('file://%(f)s/heebo-hebrew.woff2');font-weight:400 900;unicode-range:U+0590-05FF,U+200C-2010,U+20AA,U+25CC,U+FB1D-FB4F}
@font-face{font-family:Heebo;src:url('file://%(f)s/heebo-latin.woff2');font-weight:400 900}
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:1080px;height:1920px;background:transparent;overflow:hidden;font-family:Heebo,sans-serif;direction:rtl}
.abs{position:absolute;left:0;width:1080px;display:flex;justify-content:center;padding:0 70px}
.hook{font-weight:900;color:#fff;text-align:center;line-height:1.12;letter-spacing:-1px;
  -webkit-text-stroke:16px #111;paint-order:stroke fill;text-shadow:0 8px 0 rgba(0,0,0,.35)}
.hook em{font-style:normal;color:#ffe14d}
.cap{font-weight:800;font-size:64px;line-height:1.2;color:#111;background:#fff;border-radius:22px;padding:14px 30px 18px;
  text-align:center;box-shadow:0 8px 24px rgba(0,0,0,.28);max-width:860px}
.cap em{font-style:normal;color:#00883a}
.tag{font-weight:800;font-size:40px;color:#fff;background:rgba(17,17,17,.78);border-radius:999px;padding:12px 30px 14px;direction:rtl}
.tag b{font-weight:900;color:#7dffa8;direction:ltr;unicode-bidi:isolate}
""" % {"f": os.path.join(IG, "shared", "fonts")}


def fmt(t):
    t = html.escape(t or "")
    t = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", t)
    return t.replace("\n", "<br>")


def overlay_html(o):
    k = o.get("kind", "hook")
    if k == "html":
        body = o["html"]
    elif k == "hook":
        body = (f'<div class="abs" style="top:{o.get("y", 420)}px"><div class="hook" '
                f'style="font-size:{o.get("size", 112)}px">{fmt(o["text"])}</div></div>')
    elif k == "cap":
        body = f'<div class="abs" style="top:{o.get("y", 1210)}px"><div class="cap">{fmt(o["text"])}</div></div>'
    elif k == "tag":
        body = f'<div class="abs" style="top:{o.get("y", 1330)}px"><div class="tag">{o["text"]}</div></div>'
    else:
        raise ValueError(k)
    return f'<!doctype html><html lang="he"><head><meta charset="utf-8"><style>{CSS}{o.get("css", "")}</style></head><body>{body}</body></html>'


def render_overlays(build, overlays):
    pages = []
    for i, o in enumerate(overlays):
        p = os.path.join(build, f"ov{i:02d}.html")
        open(p, "w", encoding="utf-8").write(overlay_html(o))
        pages.append(p)
    js = os.path.join(build, "shoot.js")
    open(js, "w").write("""
const {chromium} = require('playwright');
(async () => {
  const b = await chromium.launch();
  const pg = await b.newPage({viewport: {width: 1080, height: 1920}});
  for (const f of process.argv.slice(2)) {
    await pg.goto('file://' + f);
    await pg.evaluate(() => document.fonts.ready);
    await pg.screenshot({path: f.replace('.html', '.png'), omitBackground: true});
  }
  await b.close();
})();
""")
    env = dict(os.environ, NODE_PATH=subprocess.run(["npm", "root", "-g"], capture_output=True, text=True).stdout.strip())
    subprocess.run(["node", js] + pages, check=True, env=env)
    return [p.replace(".html", ".png") for p in pages]


def run(cmd):
    subprocess.run(cmd, check=True)


def build(post):
    post = os.path.abspath(post)
    spec = json.load(open(os.path.join(post, "clip.json"), encoding="utf-8"))
    bd = os.path.join(post, "build")
    os.makedirs(bd, exist_ok=True)

    # 1. each shot as a vertical clip with an audio track (voice or silence)
    parts = []
    for i, s in enumerate(spec["shots"]):
        out = os.path.join(bd, f"shot{i:02d}.mp4")
        z0, z1 = s.get("zoom", [1.0, 1.0])
        d = s["dur"]
        z = f"({z0}+({z1}-{z0})*t/{d})"
        vf = (f"fps={FPS},scale=w='ceil(max({W}/iw,{H}/ih)*iw*{z}/2)*2':h='ceil(max({W}/iw,{H}/ih)*ih*{z}/2)*2':eval=frame,"
              f"crop={W}:{H}:'(iw-{W})*{s.get('focus', 0.5)}':'(ih-{H})*{s.get('focus_y', 0.5)}',setsar=1")
        if s.get("dim"):
            vf += f",eq=brightness={-0.5 * s['dim']:.3f}:saturation={1 - 0.4 * s['dim']:.3f}"
        if s.get("vf"):
            vf += "," + s["vf"]
        src = os.path.join(IG, s["src"])
        cmd = ["ffmpeg", "-v", "error", "-y", "-ss", str(s.get("ss", 0)), "-t", str(d), "-i", src]
        if s.get("voice"):
            af = "afade=t=in:d=0.02,afade=t=out:st=%.3f:d=0.03,aresample=48000" % (d - 0.03)
            cmd += ["-vf", vf, "-af", af, "-ac", "2"]
        else:
            cmd += ["-f", "lavfi", "-t", str(d), "-i", "anullsrc=r=48000:cl=stereo", "-vf", vf, "-map", "0:v", "-map", "1:a"]
        cmd += ["-t", str(d), "-c:v", "libx264", "-crf", "16", "-preset", "fast", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", out]
        run(cmd)
        parts.append(out)
    total = sum(s["dur"] for s in spec["shots"])

    # 2. overlays
    ovs = spec.get("overlays", [])
    pngs = render_overlays(bd, ovs)

    # 3. music
    slot = os.path.basename(post)
    name, track, music, _ = R.pick_track(spec, slot)
    has_voice = any(s.get("voice") for s in spec["shots"])
    vol = spec.get("music_vol", 0.12 if has_voice else 0.5)

    cmd = ["ffmpeg", "-v", "error", "-y"]
    for p in parts:
        cmd += ["-i", p]
    for p in pngs:
        cmd += ["-loop", "1", "-t", f"{total:.3f}", "-i", p]
    cmd += ["-ss", str(track["start"]), "-t", f"{total:.3f}", "-i", music]
    n = len(parts)
    fc = "".join(f"[{i}:v][{i}:a]" for i in range(n)) + f"concat=n={n}:v=1:a=1[v0][voice];"
    last = "v0"
    for j, o in enumerate(ovs):
        t, d = o["t"], o["d"]
        fi, fo = o.get("fade_in", 0.14), o.get("fade_out", 0.12)
        fc += (f"[{n + j}:v]format=rgba,fade=t=in:st={t}:d={fi}:alpha=1,"
               f"fade=t=out:st={t + d - fo:.3f}:d={fo}:alpha=1[o{j}];")
        rise = o.get("rise", 60)
        y = f"'if(lt(t-{t},0.2),{rise}*pow(1-(t-{t})/0.2,3),0)'"
        fc += f"[{last}][o{j}]overlay=0:{y}:enable='between(t,{t},{t + d:.3f})'[v{j + 1}];"
        last = f"v{j + 1}"
    mi = n + len(pngs)
    fade = max(total - 1.2, 0)
    fc += (f"[{mi}:a]volume={vol},afade=t=in:d=0.3,afade=t=out:st={fade:.3f}:d=1.2[m];"
           f"[voice][m]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-16:TP=-1.5:LRA=11[a]")
    out = os.path.join(post, "reel.mp4")
    cmd += ["-filter_complex", fc, "-map", f"[{last}]", "-map", "[a]", "-t", f"{total:.3f}",
            "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p", "-r", str(FPS),
            "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", out]
    run(cmd)
    run(["ffmpeg", "-v", "error", "-y", "-ss", str(spec.get("poster_at", 0.6)), "-i", out, "-frames:v", "1", "-q:v", "2",
         os.path.join(post, "poster.jpg")])
    R.log_track(slot, name)
    json.dump({"track": name, "license": track["license"], "credit": track.get("credit"), "duration": total},
              open(os.path.join(post, "music.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("built", out, f"{total:.1f}s", "music:", name)
    subprocess.run([sys.executable, os.path.join(HERE, "credit.py"), post], check=True)


if __name__ == "__main__":
    build(sys.argv[1])
