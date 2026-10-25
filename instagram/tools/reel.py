#!/usr/bin/env python3
"""Build and render an Instagram Reel (1080x1920 MP4) in the EZ.Path.AI design language with HyperFrames.

Usage: python3 reel.py <post_dir> [--no-render]
Reads <post_dir>/reel.json, writes <post_dir>/build/ (HyperFrames project) and <post_dir>/reel.mp4.

reel.json:
{
  "series": "שאלה של מנהלת · 1",
  "music": "advertime",              # key in MUSIC below
  "scenes": [ {"dur": 2.8, "type": ..., ...}, ... ]
}
Scene types:
  bubble  who, text                      a chat bubble (the hook question)
  title   text, kicker?, sub?            big serif statement
  vs      rows: [{label, text, good?}]   two or three contrasting rows
  point   n, title, body?                one numbered point
  number  value, unit, note?             big number in mono
  end     text, sub?                     closing line and the EZ.Path.AI sign
Inline markup: *word* = accent green, newline = line break.
Layout keeps every text inside the Reels safe zone: y 300 to 1440, and 230px clear on the right.
"""
import html
import json
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
IG = os.path.abspath(os.path.join(HERE, ".."))
REPO = os.path.abspath(os.path.join(IG, ".."))
V2 = os.path.join(REPO, "google-reviews-v2", "assets")
CATALOG = os.path.join(IG, "music.json")
LOG = os.path.join(IG, "music-log.json")
CACHE = os.path.join(IG, ".music-cache")
HF = "hyperframes@0.8.140"

# Entry and exit motion per style. Picked from the music mood so the motion matches the track.
STYLES = {
    "rise":  ("{opacity: 0, y: 70}", "{opacity: 1, y: 0, duration: 0.55, ease: 'power3.out', stagger: 0.16}",
              "{opacity: 0, y: -40, duration: 0.3, ease: 'power2.in'}"),
    "pop":   ("{opacity: 0, scale: 0.6}", "{opacity: 1, scale: 1, duration: 0.5, ease: 'back.out(2.2)', stagger: 0.12}",
              "{opacity: 0, scale: 0.9, duration: 0.25, ease: 'power2.in'}"),
    "slide": ("{opacity: 0, x: -140}", "{opacity: 1, x: 0, duration: 0.45, ease: 'power4.out', stagger: 0.1}",
              "{opacity: 0, x: 140, duration: 0.25, ease: 'power2.in'}"),
    "punch": ("{opacity: 0, scale: 1.35, rotation: -3}", "{opacity: 1, scale: 1, rotation: 0, duration: 0.4, ease: 'expo.out', stagger: 0.1}",
              "{opacity: 0, scale: 0.85, duration: 0.22, ease: 'power3.in'}"),
    "drift": ("{opacity: 0, y: 40, filter: 'blur(10px)'}", "{opacity: 1, y: 0, filter: 'blur(0px)', duration: 1.0, ease: 'power2.out', stagger: 0.25}",
              "{opacity: 0, filter: 'blur(6px)', duration: 0.45, ease: 'power1.in'}"),
}


def pick_track(spec, slot):
    cat = json.load(open(CATALOG, encoding="utf-8"))
    tracks = cat["tracks"]
    log = [e for e in json.load(open(LOG)) if e["slot"] != slot]
    if spec.get("music") in tracks:
        name = spec["music"]
    else:
        mood = spec.get("mood")
        if not mood:
            series = spec.get("series", "")
            mood = next((m for k, m in cat["series_mood"].items() if series.startswith(k)), "bright")
        recent = [e["track"] for e in log[-10:]]
        used = [e["track"] for e in log]
        pool = [n for n, t in tracks.items() if t["mood"] == mood and n not in recent] or \
               [n for n in tracks if n not in recent]
        # least used first, then catalog order
        name = sorted(pool, key=lambda n: (used.count(n), list(tracks).index(n)))[0]
    t = tracks[name]
    path = os.path.join(CACHE, t["file"])
    if not os.path.exists(path):
        os.makedirs(CACHE, exist_ok=True)
        import urllib.parse
        subprocess.run(["curl", "-sSfL", "-o", path,
                        "https://archive.org/download/freepd/" + urllib.parse.quote(t["freepd"])], check=True)
    style = spec.get("style") or cat["mood_style"][t["mood"]]
    return name, t, path, style


def log_track(slot, name):
    log = [e for e in json.load(open(LOG)) if e["slot"] != slot]
    log.append({"slot": slot, "track": name})
    log.sort(key=lambda e: e["slot"])
    json.dump(log, open(LOG, "w"), indent=1)


def fmt(t):
    t = html.escape(t or "")
    t = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", t)
    return t.replace("\n", "<br>")


def scene_inner(s):
    t = s["type"]
    if t == "bubble":
        return (f'<div class="who in">{fmt(s["who"])}</div>'
                f'<div class="bubble in">{fmt(s["text"])}</div>')
    if t == "title":
        k = f'<div class="kicker in">{fmt(s["kicker"])}</div>' if s.get("kicker") else ""
        sub = f'<div class="sub in">{fmt(s["sub"])}</div>' if s.get("sub") else ""
        return f'{k}<div class="title in">{fmt(s["text"])}</div>{sub}'
    if t == "vs":
        rows = "".join(
            f'<div class="row in{" good" if r.get("good") else ""}"><div class="rl">{fmt(r["label"])}</div>'
            f'<div class="rt">{fmt(r["text"])}</div></div>' for r in s["rows"])
        k = f'<div class="kicker in">{fmt(s["kicker"])}</div>' if s.get("kicker") else ""
        return f'{k}<div class="rows">{rows}</div>'
    if t == "point":
        body = f'<div class="pbody in">{fmt(s["body"])}</div>' if s.get("body") else ""
        return (f'<div class="pnum in">{fmt(str(s["n"]))}</div>'
                f'<div class="ptitle in">{fmt(s["title"])}</div>{body}')
    if t == "number":
        note = f'<div class="sub in">{fmt(s["note"])}</div>' if s.get("note") else ""
        return (f'<div class="big in" dir="ltr">{fmt(s["value"])}</div>'
                f'<div class="unit in">{fmt(s["unit"])}</div>{note}')
    if t == "end":
        sub = f'<div class="sub in">{fmt(s["sub"])}</div>' if s.get("sub") else ""
        return (f'<div class="title in">{fmt(s["text"])}</div>{sub}'
                f'<div class="sign in" dir="ltr">EZ.Path.AI<span></span></div>')
    if t == "phone":
        cap = f'<div class="pcap in">{fmt(s["caption"])}</div>' if s.get("caption") else ""
        msgs = ""
        for m in s["msgs"]:
            if m.get("stars"):
                msgs += '<div class="m in stars" dir="ltr">' + "".join(
                    '<svg viewBox="0 0 24 24"><path d="M12 2.5l2.9 6 6.6.9-4.8 4.6 1.2 6.5L12 17.4 6.1 20.5l1.2-6.5L2.5 9.4l6.6-.9z"/></svg>'
                    for _ in range(5)) + '</div>'
                continue
            btns = "".join(f'<div class="qb">{fmt(b)}</div>' for b in m.get("buttons", []))
            btns = f'<div class="qbs">{btns}</div>' if btns else ""
            link = f'<div class="lnk" dir="ltr">{fmt(m["link"])}</div>' if m.get("link") else ""
            msgs += f'<div class="m in {m["from"]}"><div class="mt">{fmt(m["text"])}{link}</div>{btns}</div>'
        head = fmt(s.get("chat", "מרפאת השיניים"))
        pcls = "phone" + ("" if s.get("_cont") else " in") + (" keep" if s.get("_next_phone") else "")
        return (f'{cap}<div class="{pcls}"><div class="ph-head"><span class="ph-av"></span>'
                f'<span class="ph-name">{head}</span></div><div class="ph-body">{msgs}</div></div>')
    raise SystemExit(f"unknown scene type {t}")


CSS = """
@font-face { font-family: "Frank Ruhl Libre"; src: url("assets/fonts/frank-ruhl-libre-hebrew.woff2") format("woff2"); font-weight: 300 900; font-display: block; unicode-range: U+0590-05FF, U+FB1D-FB4F; }
@font-face { font-family: "Frank Ruhl Libre"; src: url("assets/fonts/frank-ruhl-libre-latin.woff2") format("woff2"); font-weight: 300 900; font-display: block; }
@font-face { font-family: "Assistant"; src: url("assets/fonts/assistant-hebrew.woff2") format("woff2"); font-weight: 200 800; font-display: block; unicode-range: U+0590-05FF, U+FB1D-FB4F; }
@font-face { font-family: "Assistant"; src: url("assets/fonts/assistant-latin.woff2") format("woff2"); font-weight: 200 800; font-display: block; }
@font-face { font-family: "JetBrains Mono"; src: url("assets/fonts/jetbrains-mono-latin.woff2") format("woff2"); font-weight: 400 700; font-display: block; }
:root { --paper:#f4f8f5; --rule:#ccd3cd; --muted:#4e544f; --ink:#141a15; --accent:#007329; --accent-soft:#d0eed5; --card:#fdfefd; --red:#b3261e; --red-soft:#f6dcda; }
* { box-sizing: border-box; margin: 0; padding: 0; }
html, body { width: 1080px; height: 1920px; overflow: hidden; background: var(--paper); }
#root { position: relative; width: 1080px; height: 1920px; overflow: hidden; background: var(--paper); color: var(--ink); font-family: "Assistant", sans-serif; }
#bg { position: absolute; inset: 0; background: radial-gradient(ellipse 900px 900px at 80% 18%, #dcefe0 0%, rgba(244,248,245,0) 70%), radial-gradient(ellipse 700px 700px at 10% 90%, #e6f2e8 0%, rgba(244,248,245,0) 70%); }
#top { position: absolute; top: 236px; left: 90px; right: 230px; display: flex; justify-content: space-between; align-items: center; direction: rtl; }
#top .series { font-weight: 800; font-size: 36px; color: var(--accent); }
#top .brand { font-family: "JetBrains Mono", monospace; font-weight: 700; font-size: 30px; letter-spacing: 1px; direction: ltr; }
#prog { position: absolute; top: 300px; left: 90px; right: 230px; height: 6px; border-radius: 3px; background: var(--rule); overflow: hidden; }
#prog-fill { width: 100%; height: 100%; background: var(--accent); transform-origin: right center; transform: scaleX(0); }
.clip { position: absolute; inset: 0; }
.scene .box { position: absolute; top: 360px; bottom: 480px; left: 90px; right: 230px; display: flex; flex-direction: column; justify-content: center; gap: 36px; direction: rtl; text-align: right; }
em { font-style: normal; color: var(--accent); }
.who { font-weight: 800; font-size: 44px; color: var(--muted); }
.bubble { background: var(--card); border: 2px solid var(--rule); border-radius: 56px 56px 14px 56px; padding: 56px 60px; font-family: "Frank Ruhl Libre", serif; font-weight: 900; font-size: 100px; line-height: 1.12; box-shadow: 0 24px 60px rgba(20,26,21,.10); }
.kicker { font-weight: 800; font-size: 42px; color: var(--accent); }
.title { font-family: "Frank Ruhl Libre", serif; font-weight: 900; font-size: 108px; line-height: 1.12; letter-spacing: -1px; }
.sub { font-size: 56px; line-height: 1.4; color: var(--muted); font-weight: 600; }
.rows { display: flex; flex-direction: column; gap: 30px; }
.row { background: var(--card); border: 2px solid var(--rule); border-radius: 36px; padding: 40px 44px; display: flex; flex-direction: column; gap: 14px; }
.row .rl { font-weight: 800; font-size: 38px; color: var(--red); }
.row .rt { font-size: 58px; line-height: 1.3; font-weight: 700; }
.row.good { border-color: var(--accent); background: #eef8f0; }
.row.good .rl { color: var(--accent); }
.pnum { width: 120px; height: 120px; border-radius: 50%; background: var(--accent); color: #fff; font-family: "JetBrains Mono", monospace; font-weight: 700; font-size: 60px; display: flex; align-items: center; justify-content: center; }
.ptitle { font-family: "Frank Ruhl Libre", serif; font-weight: 900; font-size: 100px; line-height: 1.12; }
.pbody { font-size: 58px; line-height: 1.4; color: var(--muted); font-weight: 600; }
.big { font-family: "JetBrains Mono", monospace; font-weight: 700; font-size: 220px; line-height: 1; color: var(--accent); text-align: right; }
.unit { font-family: "Frank Ruhl Libre", serif; font-weight: 900; font-size: 84px; line-height: 1.15; }
.sign { margin-top: 30px; font-family: "JetBrains Mono", monospace; font-weight: 700; font-size: 46px; letter-spacing: 2px; text-align: right; }
.sign span { display: block; width: 150px; height: 6px; background: var(--accent); margin: 20px 0 0 auto; border-radius: 3px; }
#s0 .title { font-size: 128px; line-height: 1.08; }
#s0 .bubble { font-size: 112px; }
#s0 .kicker { font-size: 46px; }
.scene .box.ph { gap: 26px; justify-content: flex-start; top: 350px; bottom: 470px; }
.pcap { font-family: "Frank Ruhl Libre", serif; font-weight: 900; font-size: 64px; line-height: 1.15; min-height: 148px; }
.phone { flex: 1; border-radius: 56px; background: #ece5dd; border: 14px solid var(--ink); overflow: hidden; display: flex; flex-direction: column; box-shadow: 0 30px 70px rgba(20,26,21,.18); }
.ph-head { background: #075e54; color: #fff; padding: 24px 30px; display: flex; align-items: center; gap: 18px; font-weight: 800; font-size: 40px; }
.ph-av { width: 56px; height: 56px; border-radius: 50%; background: #d0eed5; flex: 0 0 56px; }
.ph-body { flex: 1; padding: 26px 24px; display: flex; flex-direction: column; gap: 18px; justify-content: flex-end; }
.m { max-width: 88%; font-size: 42px; line-height: 1.32; font-weight: 600; }
.m .mt { padding: 20px 24px; border-radius: 26px; box-shadow: 0 2px 4px rgba(0,0,0,.08); }
.m.clinic { align-self: flex-start; }
.m.clinic .mt { background: #fff; border-top-right-radius: 6px; }
.m.patient { align-self: flex-end; }
.m.patient .mt { background: #d9fdd3; border-top-left-radius: 6px; }
.lnk { margin-top: 10px; color: #027eb5; font-size: 36px; text-decoration: underline; }
.qbs { display: flex; flex-direction: column; gap: 8px; margin-top: 8px; }
.qb { background: #fff; color: #027eb5; text-align: center; padding: 18px; border-radius: 20px; font-size: 38px; font-weight: 700; }
.m.stars { align-self: center; display: flex; gap: 14px; background: #fff; padding: 26px 34px; border-radius: 30px; max-width: none; }
.m.stars svg { width: 76px; height: 76px; fill: #f2a900; }
"""


def build(post):
    spec = json.load(open(os.path.join(post, "reel.json"), encoding="utf-8"))
    scenes = spec["scenes"]
    slot = os.path.basename(post)
    name, track, music, style = pick_track(spec, slot)
    # Snap every scene to the beat grid: whole multiples of two beats (half time above 150 bpm).
    beat = 60.0 / track["bpm"] * (2 if track["bpm"] > 150 else 1)
    unit = 2 * beat
    for s in scenes:
        s["dur"] = round(max(2, round(s["dur"] / unit)) * unit, 3)
    for i, s in enumerate(scenes):
        s["_cont"] = i > 0 and s["type"] == "phone" and scenes[i - 1]["type"] == "phone"
        s["_next_phone"] = s["type"] == "phone" and i + 1 < len(scenes) and scenes[i + 1]["type"] == "phone"
    starts, t = [], 0.0
    for s in scenes:
        starts.append(round(t, 3))
        t += s["dur"]
    total = round(t, 3)

    b = os.path.join(post, "build")
    shutil.rmtree(b, ignore_errors=True)
    os.makedirs(os.path.join(b, "assets", "audio"))
    shutil.copytree(os.path.join(V2, "fonts"), os.path.join(b, "assets", "fonts"))
    os.makedirs(os.path.join(b, "assets", "vendor"))
    shutil.copy(os.path.join(V2, "vendor", "gsap.min.js"), os.path.join(b, "assets", "vendor"))
    fade = max(0.1, total - 1.5)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(track["start"]), "-i", music, "-t", str(total), "-af",
                    f"afade=t=in:d=0.4,afade=t=out:st={fade}:d=1.5,volume=0.8",
                    os.path.join(b, "assets", "audio", "music.mp3")], check=True)

    secs = "".join(
        f'<section id="s{i}" class="scene clip" data-start="{starts[i]}" data-duration="{s["dur"]}" '
        f'data-track-index="{1 + i % 2}"><div class="box{' ph' if s['type'] == 'phone' else ''}">{scene_inner(s)}</div></section>'
        for i, s in enumerate(scenes))
    st_from, st_to, st_out = STYLES[style]
    js_scenes = json.dumps([{"start": starts[i], "dur": s["dur"], "stagger": s.get("stagger")} for i, s in enumerate(scenes)])
    doc = f"""<!doctype html>
<html lang="he" data-resolution="portrait"><head><meta charset="UTF-8"><meta name="viewport" content="width=1080, height=1920">
<title>{html.escape(spec.get("series", "reel"))}</title><script src="assets/vendor/gsap.min.js"></script><style>{CSS}</style></head>
<body><div id="root" data-composition-id="main" data-start="0" data-duration="{total}" data-width="1080" data-height="1920">
<div id="bg"></div>
<div id="top"><span class="series">{fmt(spec.get("series", ""))}</span><span class="brand">EZ.Path.AI</span></div>
<div id="prog"><div id="prog-fill"></div></div>
{secs}
<audio id="music" src="assets/audio/music.mp3" data-start="0" data-duration="{total}" data-track-index="10" data-volume="1"></audio>
</div>
<script>
(function () {{
  const SCENES = {js_scenes};
  const TOTAL = {total};
  function build() {{
    window.__timelines = window.__timelines || {{}};
    const tl = gsap.timeline({{ paused: true }});
    tl.fromTo("#prog-fill", {{ scaleX: 0 }}, {{ scaleX: 1, duration: TOTAL, ease: "none" }}, 0);
    SCENES.forEach((sc, i) => {{
      const items = "#s" + i + " .in";
      if (i === 0)
        tl.fromTo(items, {{ opacity: 1, scale: 0.94 }}, {{ opacity: 1, scale: 1, duration: 0.6, ease: "back.out(2)", stagger: 0.08 }}, 0);
      else
        tl.fromTo(items, {st_from}, Object.assign({st_to}, sc.stagger ? {{ stagger: sc.stagger }} : {{}}), sc.start + 0.02);
      if (i < SCENES.length - 1)
        tl.to("#s" + i + " .in:not(.keep)", {st_out}, sc.start + sc.dur - 0.3);
    }});
    window.__timelines["main"] = tl;
    if (typeof window.__hfForceTimelineRebind === "function") window.__hfForceTimelineRebind();
  }}
  Promise.all([
    document.fonts.load('900 90px "Frank Ruhl Libre"', "אבגד"),
    document.fonts.load('700 40px "Assistant"', "אבגד"),
    document.fonts.load('700 40px "JetBrains Mono"', "EZ.Path0123"),
  ]).then(() => document.fonts.ready).then(build, build);
}})();
</script></body></html>
"""
    open(os.path.join(b, "index.html"), "w", encoding="utf-8").write(doc)
    json.dump({"track": name, "freepd": track["freepd"], "bpm": track["bpm"], "style": style, "duration": total},
              open(os.path.join(post, "music.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump({"id": os.path.basename(post), "name": os.path.basename(post)}, open(os.path.join(b, "meta.json"), "w"))
    return b, total


def main():
    post = os.path.abspath(sys.argv[1])
    b, total = build(post)
    print(f"built {b} ({total}s)")
    if "--no-render" in sys.argv:
        return
    out = os.path.join(post, "reel.mp4")
    subprocess.run(["npx", "--yes", HF, "render", b, "-o", out, "--quiet"], check=True)
    log_track(os.path.basename(post), json.load(open(os.path.join(post, "music.json")))["track"])
    print(out)


if __name__ == "__main__":
    main()
