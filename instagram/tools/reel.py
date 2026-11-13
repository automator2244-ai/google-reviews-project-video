#!/usr/bin/env python3
"""Build and render an Instagram Reel (1080x1920 MP4) in the EZ.Path.AI design language with HyperFrames.

Usage: python3 reel.py <post_dir> [--no-render]
Reads <post_dir>/reel.json, writes <post_dir>/build/ (HyperFrames project) and <post_dir>/reel.mp4.

reel.json:
{
  "series": "שאלה של מנהלת · 1",       # internal only: never shown in the video (13.11, Benaya)
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
  confess tag, role?, quote, icon?       documentary "talking head": dark frame, lower-third name tag, quote.
                                         icon: person (default) | star. Good for sitcom and mockumentary formats.
  phone   msgs[{from, text, name?, ...}] a msg with "name" shows the sender, for group chats (chat, sub on the scene)
  hook    look, text, kicker?, ...        the opening frame (put it first). Full screen, no series bar or logo,
                                         one big line of up to 5 words. It is also the grid cover, so vary the look:
            look ink | green | sun          solid backgrounds (dark, brand green, warm yellow)
            look notif  time?, notif{app, title, text}?   a phone lock screen; the notification plays a ding
            look search query, text in a dark card over a blurred Google results page
            look number value, text        a giant number with the line under it
            size?                          font size of the line in px (default 170), for very short lines
            look cover  style, cover{...}  a full "different" cover from covers.py (chat, poster, face, maps, timer,
                                           postit, calendar, newspaper, notes, vs). Not the brand look: see AUTOMATION.md
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

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import covers  # noqa: E402

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
    "bounce": ("{opacity: 0, y: -90, scaleY: 1.15}", "{opacity: 1, y: 0, scaleY: 1, duration: 0.7, ease: 'bounce.out', stagger: 0.12}",
               "{opacity: 0, y: 60, duration: 0.25, ease: 'power2.in'}"),
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
        # least used first, then CC0 before tracks that need a credit line, then catalog order
        name = sorted(pool, key=lambda n: (used.count(n), "credit" in tracks[n], list(tracks).index(n)))[0]
    t = tracks[name]
    path = os.path.join(CACHE, t["file"])
    if not os.path.exists(path):
        os.makedirs(CACHE, exist_ok=True)
        import urllib.parse
        url = t.get("url") or "https://archive.org/download/freepd/" + urllib.parse.quote(t["freepd"])
        subprocess.run(["curl", "-sSfL", "-A", "Mozilla/5.0", "-o", path, url], check=True)
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


def hook_bg(s):
    """Full-screen background of a hook scene. Sits under the text box and covers the series bar."""
    look = s.get("look", "ink")
    if look == "cover":
        bg, stage = covers.render(s["style"], s["cover"], "assets/img/")
        return (f'<div class="hk-bg" style="{bg}"><div class="hk-zoom">'
                f'<div style="position:absolute;top:285px;left:0;width:1080px;height:1350px">{stage}</div></div></div>')
    extra = ""
    if look == "notif":
        n = s.get("notif")
        card = ""
        if n:
            card = (f'<div class="hk-notif"><div class="hk-nh"><span class="hk-app"></span>'
                    f'<span class="hk-an">{fmt(n.get("app", "WhatsApp"))}</span><span class="hk-now">עכשיו</span></div>'
                    f'<div class="hk-nt">{fmt(n["title"])}</div><div class="hk-nx">{fmt(n["text"])}</div></div>')
        extra = (f'<div class="hk-time" dir="ltr">{fmt(s.get("time", "09:41"))}</div>'
                 f'<div class="hk-date">{fmt(s.get("date", ""))}</div>{card}')
    if look == "search":
        rows = "".join(
            '<div class="hk-res"><span class="hk-pin"></span><span class="hk-l1"></span>'
            f'<span class="hk-st">{"★" * k}{"☆" * (5 - k)}</span><span class="hk-l2"></span></div>'
            for k in (5, 4, 5, 3, 4))
        extra = (f'<div class="hk-sbar"><span class="hk-g" dir="ltr">G</span>{fmt(s.get("query", ""))}</div>'
                 f'<div class="hk-blur"><div class="hk-map"></div>{rows}</div>')
    return f'<div class="hk-bg look-{look}"><div class="hk-zoom">{extra}</div></div>'


def scene_inner(s):
    t = s["type"]
    if t == "hook" and s.get("look") == "cover":
        return ""
    if t == "hook":
        k = f'<div class="hk-kicker in">{fmt(s["kicker"])}</div>' if s.get("kicker") else ""
        num = f'<div class="hk-num in" dir="ltr">{fmt(s["value"])}</div>' if s.get("look") == "number" else ""
        size = f' style="font-size:{s["size"]}px"' if s.get("size") else ""
        txt = f'{k}{num}<div class="hk-text in"{size}>{fmt(s["text"])}</div>'
        if s.get("look") == "search":
            return f'<div class="hk-card in"><div class="hk-rule"></div>{txt}<div class="hk-sign" dir="ltr">EZ.Path.AI</div></div>'
        return txt
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
    if t == "confess":
        icon = STAR_SVG if s.get("icon") == "star" else PERSON_SVG
        role = f'<span class="cf-role">{fmt(s["role"])}</span>' if s.get("role") else ""
        return (f'<div class="cf-card in"><span class="cf-c tl"></span><span class="cf-c tr"></span>'
                f'<span class="cf-c bl"></span><span class="cf-c br"></span>'
                f'<span class="cf-rec" dir="ltr"><i></i>REC</span>{icon}</div>'
                f'<div class="cf-tag in"><span class="cf-name">{fmt(s["tag"])}</span>{role}</div>'
                f'<div class="cf-quote in">{fmt(s["quote"])}</div>')
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
            anim = "" if m.get("show") else " in"
            who = ""
            if m.get("name"):
                col = NAME_COLORS[sum(map(ord, m["name"])) % len(NAME_COLORS)]
                who = f'<div class="mn" style="color:{col}">{fmt(m["name"])}</div>'
            msgs += f'<div class="m{anim} {m["from"]}"><div class="mt">{who}{fmt(m["text"])}{link}</div>{btns}</div>'
        head = fmt(s.get("chat", "מרפאת השיניים"))
        if s.get("sub"):
            head = f'<span class="ph-hn">{head}<small>{fmt(s["sub"])}</small></span>'
        pcls = "phone" + ("" if s.get("_cont") else " in") + (" keep" if s.get("_next_phone") else "")
        return (f'{cap}<div class="{pcls}"><div class="ph-head"><span class="ph-av"></span>'
                f'<span class="ph-name">{head}</span></div><div class="ph-body">{msgs}</div></div>')
    raise SystemExit(f"unknown scene type {t}")


PERSON_SVG = ('<svg class="cf-icon" viewBox="0 0 200 200"><circle cx="100" cy="72" r="40"/>'
              '<path d="M30 190c0-42 31-70 70-70s70 28 70 70z"/></svg>')
STAR_SVG = ('<svg class="cf-icon star" viewBox="0 0 24 24"><path d="M12 2.5l2.9 6 6.6.9-4.8 4.6 1.2 6.5L12 17.4 '
            '6.1 20.5l1.2-6.5L2.5 9.4l6.6-.9z"/></svg>')
NAME_COLORS = ["#007329", "#b3261e", "#6b3fb5", "#b35c00", "#027eb5"]

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
.mn { font-weight: 800; font-size: 34px; margin-bottom: 4px; }
.ph-hn { display: flex; flex-direction: column; line-height: 1.15; }
.ph-hn small { font-size: 28px; font-weight: 600; opacity: .8; }
.cf-card { position: relative; height: 470px; border-radius: 48px; background: var(--ink); display: flex; align-items: flex-end; justify-content: center; overflow: hidden; box-shadow: 0 30px 70px rgba(20,26,21,.22); }
.cf-icon { width: 330px; height: 330px; fill: #3a453c; margin-bottom: -6px; }
.cf-icon.star { fill: #f2a900; width: 300px; height: 300px; margin-bottom: 70px; }
.cf-c { position: absolute; width: 56px; height: 56px; border: 0 solid rgba(244,248,245,.75); }
.cf-c.tl { top: 34px; left: 34px; border-top-width: 6px; border-left-width: 6px; }
.cf-c.tr { top: 34px; right: 34px; border-top-width: 6px; border-right-width: 6px; }
.cf-c.bl { bottom: 34px; left: 34px; border-bottom-width: 6px; border-left-width: 6px; }
.cf-c.br { bottom: 34px; right: 34px; border-bottom-width: 6px; border-right-width: 6px; }
.cf-rec { position: absolute; top: 46px; left: 110px; font-family: "JetBrains Mono", monospace; font-weight: 700; font-size: 30px; color: #f4f8f5; display: flex; align-items: center; gap: 12px; }
.cf-rec i { width: 22px; height: 22px; border-radius: 50%; background: #e5483e; display: block; }
.cf-tag { align-self: flex-start; margin-top: -110px; position: relative; background: var(--accent); color: #fff; padding: 20px 38px; border-radius: 20px; display: flex; flex-direction: column; gap: 4px; box-shadow: 0 14px 30px rgba(0,76,26,.3); }
.cf-name { font-weight: 800; font-size: 54px; line-height: 1.1; }
.cf-role { font-weight: 600; font-size: 34px; opacity: .9; }
.cf-quote { font-family: "Frank Ruhl Libre", serif; font-weight: 900; font-size: 84px; line-height: 1.16; }
#s0 .cf-quote { font-size: 96px; }
/* hook: full-screen opening frame, also the grid cover */
.scene.hook { z-index: 5; }
.hk-bg { position: absolute; inset: 0; overflow: hidden; }
.hk-zoom { position: absolute; inset: 0; }
.look-ink { background: radial-gradient(ellipse 900px 900px at 80% 20%, #1f3a26 0%, rgba(20,26,21,0) 70%), #141a15; }
.look-green { background: radial-gradient(ellipse 900px 900px at 80% 15%, #1a8c3f 0%, rgba(0,115,41,0) 70%), radial-gradient(ellipse 700px 700px at 10% 95%, #005a20 0%, rgba(0,115,41,0) 70%), #007329; }
.look-sun { background: radial-gradient(ellipse 900px 900px at 80% 15%, #fff1c2 0%, rgba(248,214,107,0) 70%), #f8d66b; }
.look-number { background: radial-gradient(ellipse 900px 900px at 80% 15%, #1a8c3f 0%, rgba(0,115,41,0) 70%), #007329; }
.look-notif { background: radial-gradient(ellipse 1000px 800px at 70% 10%, #2c6b45 0%, rgba(11,40,22,0) 70%), radial-gradient(ellipse 800px 700px at 0% 100%, #3b2a5a 0%, rgba(11,40,22,0) 70%), #0b2816; }
.look-search { background: #f1f3f4; }
.hook .box { top: 360px; bottom: 480px; gap: 30px; }
.hk-text { font-family: "Frank Ruhl Libre", serif; font-weight: 900; font-size: 170px; line-height: 1.04; letter-spacing: -2px; }
.hk-kicker { font-weight: 800; font-size: 56px; }
.hk-num { font-family: "JetBrains Mono", monospace; font-weight: 700; font-size: 380px; line-height: .9; color: #fff; text-align: right; }
.look-ink ~ .box, .look-green ~ .box, .look-number ~ .box, .look-notif ~ .box { color: #fff; }
.look-ink ~ .box em, .look-notif ~ .box em { color: #4cc472; }
.look-ink ~ .box .hk-kicker, .look-notif ~ .box .hk-kicker { color: #4cc472; }
.look-green ~ .box em, .look-number ~ .box em { color: #c9f2d2; }
.look-green ~ .box .hk-kicker, .look-number ~ .box .hk-kicker { color: #c9f2d2; }
.look-sun ~ .box { color: var(--ink); }
.look-sun ~ .box em { color: var(--accent); }
.look-sun ~ .box .hk-kicker { color: #8a5a00; }
.look-number ~ .box .hk-text { font-size: 104px; }
.look-notif ~ .box { justify-content: flex-end; }
.look-notif ~ .box .hk-text { font-size: 128px; }
.hk-time { position: absolute; top: 330px; left: 0; right: 0; text-align: center; font-family: "Assistant", sans-serif; font-weight: 300; font-size: 190px; color: #fff; letter-spacing: -4px; }
.hk-date { position: absolute; top: 560px; left: 0; right: 0; text-align: center; font-weight: 600; font-size: 44px; color: rgba(255,255,255,.85); direction: rtl; }
.hk-notif { position: absolute; top: 680px; left: 70px; right: 70px; direction: rtl; background: rgba(244,248,245,.92); border-radius: 44px; padding: 30px 38px 36px; box-shadow: 0 20px 60px rgba(0,0,0,.35); color: var(--ink); }
.hk-nh { display: flex; align-items: center; gap: 16px; font-size: 32px; color: var(--muted); font-weight: 700; }
.hk-app { width: 52px; height: 52px; border-radius: 14px; background: #25d366; display: block; }
.hk-now { margin-right: auto; font-weight: 600; }
.hk-nt { font-weight: 800; font-size: 44px; margin-top: 16px; }
.hk-nx { font-size: 46px; line-height: 1.3; font-weight: 600; margin-top: 6px; }
.hk-sbar { position: absolute; top: 250px; left: 70px; right: 70px; height: 120px; border-radius: 60px; background: #fff; box-shadow: 0 6px 20px rgba(0,0,0,.12); display: flex; align-items: center; gap: 26px; padding: 0 44px; direction: rtl; font-size: 48px; font-weight: 600; color: #202124; }
.hk-g { font-family: "Assistant", sans-serif; font-weight: 800; font-size: 62px; color: #4285f4; }
.hk-blur { position: absolute; top: 410px; left: 70px; right: 70px; bottom: 0; filter: blur(9px); display: flex; flex-direction: column; gap: 28px; }
.hk-map { height: 420px; border-radius: 30px; background: linear-gradient(135deg, #cfe8d4 0%, #e8f0e0 40%, #c9dcf0 100%); }
.hk-res { display: grid; grid-template-columns: 70px 1fr; gap: 10px 24px; background: #fff; border-radius: 26px; padding: 28px 34px; direction: rtl; }
.hk-pin { grid-row: span 3; width: 60px; height: 60px; border-radius: 50%; background: #ea4335; }
.hk-l1 { height: 34px; width: 70%; background: #3c4043; border-radius: 8px; }
.hk-st { color: #fbbc04; font-size: 40px; letter-spacing: 4px; }
.hk-l2 { height: 26px; width: 50%; background: #bdc1c6; border-radius: 8px; }
.hk-card { background: #141a15; color: #fff; border-radius: 44px; padding: 64px 60px 56px; box-shadow: 0 30px 80px rgba(0,0,0,.35); display: flex; flex-direction: column; gap: 26px; }
.hk-card em { color: #4cc472; }
.hk-card .hk-text { font-size: 118px; }
.hk-card .hk-kicker { color: #4cc472; }
.hk-rule { width: 120px; height: 8px; border-radius: 4px; background: #4cc472; }
.hk-sign { font-family: "JetBrains Mono", monospace; font-weight: 700; font-size: 34px; letter-spacing: 2px; color: #a9b3ab; text-align: right; }
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
    os.makedirs(os.path.join(b, "assets", "img"))
    shutil.copy(os.path.join(IG, "assets", "bnaya.jpg"), os.path.join(b, "assets", "img"))
    fade = max(0.1, total - 1.5)
    af = f"loudnorm=I=-16:TP=-1.5:LRA=11,afade=t=in:d=0.4,afade=t=out:st={fade}:d=1.5"
    out_mp3 = os.path.join(b, "assets", "audio", "music.mp3")
    if scenes[0]["type"] == "hook" and scenes[0].get("look") == "notif" and scenes[0].get("notif"):
        # A two-tone notification ding over the first beat, so the opening has a sound that stops the thumb.
        ding = ("aevalsrc='0.55*sin(2*PI*1319*t)*exp(-14*t)+0.5*sin(2*PI*1760*(t-0.11))*exp(-9*(t-0.11))*gte(t,0.11)'"
                ":s=44100:d=0.7,aformat=channel_layouts=stereo")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(track["start"]), "-i", music, "-t", str(total),
                        "-filter_complex", f"[0:a]{af},aformat=channel_layouts=stereo:sample_rates=44100[m];{ding}[d];"
                        "[m][d]amix=inputs=2:duration=first:normalize=0[o]", "-map", "[o]", out_mp3], check=True)
    else:
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(track["start"]), "-i", music, "-t", str(total), "-af",
                        af, out_mp3], check=True)

    secs = "".join(
        f'<section id="s{i}" class="scene clip{' hook' if s['type'] == 'hook' else ''}" data-start="{starts[i]}" data-duration="{s["dur"]}" '
        f'data-track-index="{1 + i % 2}">{hook_bg(s) if s['type'] == 'hook' else ''}<div class="box{' ph' if s['type'] == 'phone' else ''}">{scene_inner(s)}</div></section>'
        for i, s in enumerate(scenes))
    st_from, st_to, st_out = STYLES[style]
    js_scenes = json.dumps([{"start": starts[i], "dur": s["dur"], "stagger": s.get("stagger")} for i, s in enumerate(scenes)])
    doc = f"""<!doctype html>
<html lang="he" data-resolution="portrait"><head><meta charset="UTF-8"><meta name="viewport" content="width=1080, height=1920">
<title>{html.escape(spec.get("series", "reel"))}</title><script src="assets/vendor/gsap.min.js"></script><style>{CSS}{covers.CSS}</style></head>
<body><div id="root" data-composition-id="main" data-start="0" data-duration="{total}" data-width="1080" data-height="1920">
<div id="bg"></div>
<div id="top"><span></span><span class="brand">EZ.Path.AI</span></div>
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
      if (document.querySelector("#s" + i + ".hook"))
        tl.fromTo("#s" + i + " .hk-zoom", {{ scale: 1 }}, {{ scale: 1.08, duration: sc.dur, ease: "none" }}, sc.start);
      if (i === 0)
        tl.fromTo(items, {{ opacity: 1, scale: 0.94 }}, {{ opacity: 1, scale: 1, duration: 0.6, ease: "back.out(2)", stagger: 0.08 }}, 0);
      else
        tl.fromTo(items, {st_from}, Object.assign({st_to}, sc.stagger ? {{ stagger: sc.stagger }} : {{}}), sc.start + 0.02);
      if (i < SCENES.length - 1)
        tl.to("#s" + i + " .in:not(.keep):not(.keep .in)", {st_out}, sc.start + sc.dur - 0.3);
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
    json.dump({"track": name, "source": track.get("url") or track["freepd"], "license": track.get("license", "CC0"),
               "credit": track.get("credit"), "bpm": track["bpm"], "style": style, "duration": total},
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
    if os.path.basename(os.path.dirname(post)) == "queue":  # prototypes do not use up a track
        log_track(os.path.basename(post), json.load(open(os.path.join(post, "music.json")))["track"])
    subprocess.run([sys.executable, os.path.join(HERE, "credit.py"), post], check=True)
    print(out)


if __name__ == "__main__":
    main()
