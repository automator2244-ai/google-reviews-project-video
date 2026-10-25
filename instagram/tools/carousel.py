#!/usr/bin/env python3
"""Render an Instagram carousel (1080x1350 PNG per slide) in the EZ.Path.AI design language.

Usage: python3 carousel.py <post_dir>
Reads <post_dir>/slides.json and writes <post_dir>/slide-01.png, slide-02.png, ...

slides.json: {"slides": [ {"type": ..., ...}, ... ]}
Slide types:
  cover   title, sub
  text    kicker?, title, body?
  quote   label, title, quote, note?
  list    title, items[], mark ("check" | "cross" | "num"), note?
  end     title, sub?
  web     label, title?, url, head, text      a website mockup (what the clinic says about itself)
  reviews label, title?, items[{name, when, text}], note?   Google-style review cards (UI as content).
          Example reviews must be marked as examples in "note".
Inline markup in any text: *word* renders in the accent green, newline breaks the line.
"""
import html
import json
import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, "..", "shared", "fonts")
CHROME = os.environ.get("CHROME", "/opt/pw-browsers/chromium-1194/chrome-linux/chrome")

CSS = """
@font-face { font-family: "Frank Ruhl Libre"; src: url("FONTS/frank-ruhl-libre-hebrew.woff2") format("woff2"); font-weight: 300 900; unicode-range: U+0590-05FF, U+FB1D-FB4F; }
@font-face { font-family: "Frank Ruhl Libre"; src: url("FONTS/frank-ruhl-libre-latin.woff2") format("woff2"); font-weight: 300 900; }
@font-face { font-family: "Assistant"; src: url("FONTS/assistant-hebrew.woff2") format("woff2"); font-weight: 200 800; unicode-range: U+0590-05FF, U+FB1D-FB4F; }
@font-face { font-family: "Assistant"; src: url("FONTS/assistant-latin.woff2") format("woff2"); font-weight: 200 800; }
@font-face { font-family: "JetBrains Mono"; src: url("FONTS/jetbrains-mono-latin.woff2") format("woff2"); font-weight: 400 700; }
:root { --paper:#f4f8f5; --paper-2:#e8efe9; --rule:#ccd3cd; --muted:#4e544f; --ink:#141a15;
        --accent:#007329; --accent-deep:#004c1a; --accent-soft:#d0eed5; --card:#fdfefd; --red:#b3261e; }
* { box-sizing: border-box; margin: 0; padding: 0; }
html, body { width: 1080px; height: 1350px; overflow: hidden; }
body { background: var(--paper); color: var(--ink); font-family: "Assistant", sans-serif; direction: rtl;
       background-image: radial-gradient(ellipse 900px 700px at 85% 10%, #e3f1e6 0%, rgba(244,248,245,0) 70%); }
.frame { position: absolute; inset: 0; padding: 120px 120px 130px; display: flex; flex-direction: column; }
.top { position: absolute; top: 64px; left: 120px; right: 120px; display: flex; justify-content: space-between;
       font-family: "JetBrains Mono", monospace; font-size: 30px; letter-spacing: 1px; color: var(--muted); }
.top .brand { color: var(--ink); font-weight: 700; }
.top .series { font-family: "Assistant"; font-weight: 800; font-size: 34px; color: var(--accent); letter-spacing: 0; }
.bottom { position: absolute; bottom: 60px; left: 120px; right: 120px; display: flex; justify-content: space-between;
          font-family: "JetBrains Mono", monospace; font-size: 28px; color: var(--muted); }
.rule { width: 140px; height: 6px; background: var(--accent); border-radius: 3px; margin: 0 0 40px; }
em { font-style: normal; color: var(--accent); }
.display { font-family: "Frank Ruhl Libre", serif; font-weight: 900; line-height: 1.08; letter-spacing: -1px; }
.body { font-size: 54px; line-height: 1.45; color: var(--muted); font-weight: 500; }
.kicker { font-family: "Assistant"; font-weight: 800; font-size: 34px; color: var(--accent); margin-bottom: 28px; }
.center { justify-content: center; }
/* cover */
.cover .display { font-size: 118px; }
.cover .sub { margin-top: 52px; font-size: 56px; line-height: 1.4; color: var(--muted); font-weight: 600; }
/* text */
.text .display { font-size: 104px; margin-bottom: 52px; }
/* quote */
.quote .label { font-family: "Assistant"; font-size: 40px; font-weight: 800; color: var(--accent); font-weight: 700; margin-bottom: 20px; }
.quote .display { font-size: 96px; margin-bottom: 60px; }
.bubble { background: var(--card); border: 2px solid var(--rule); border-radius: 44px 44px 44px 12px; padding: 52px 56px;
          font-size: 62px; line-height: 1.36; font-weight: 600; color: var(--ink); box-shadow: 0 18px 50px rgba(20,26,21,0.08); }
.note { margin-top: 52px; font-size: 46px; line-height: 1.45; color: var(--muted); }
/* list */
.list .display { font-size: 100px; margin-bottom: 60px; }
.items { list-style: none; display: flex; flex-direction: column; gap: 40px; }
.items li { display: flex; gap: 28px; align-items: flex-start; font-size: 56px; line-height: 1.35; font-weight: 600; }
.mark { flex: 0 0 76px; height: 76px; border-radius: 50%; display: flex; align-items: center; justify-content: center;
        font-family: "JetBrains Mono", monospace; font-size: 36px; font-weight: 700; margin-top: 0; }
.mark.check, .mark.num { background: var(--accent); color: #fff; }
.mark.cross { background: #f6dcda; color: var(--red); }
/* web, reviews */
.label { font-family: "Assistant"; font-size: 40px; font-weight: 800; color: var(--accent); margin-bottom: 24px; }
.wt { font-size: 88px; margin-bottom: 48px; }
.site { background: #fff; border: 2px solid var(--rule); border-radius: 30px; overflow: hidden; box-shadow: 0 18px 50px rgba(20,26,21,.08); }
.bar { background: #eceeec; padding: 22px 28px; display: flex; align-items: center; gap: 12px; direction: ltr; }
.bar i { width: 20px; height: 20px; border-radius: 50%; background: #c9cdca; display: block; }
.bar span { flex: 1; margin-left: 16px; background: #fff; border-radius: 14px; padding: 8px 22px; font-size: 30px; color: var(--muted); direction: rtl; text-align: right; }
.hero { padding: 56px 56px 60px; direction: rtl; }
.hero .h { font-size: 66px; font-weight: 800; line-height: 1.2; color: #5d635e; }
.hero .p { margin-top: 22px; font-size: 44px; line-height: 1.45; color: #8a908b; font-weight: 500; }
.hero .btn { display: inline-block; margin-top: 36px; background: #b9c0ba; color: #fff; font-size: 38px; font-weight: 800; padding: 18px 40px; border-radius: 16px; }
.rvl { display: flex; flex-direction: column; gap: 30px; }
.rv { background: #fff; border: 2px solid var(--rule); border-radius: 30px; padding: 34px 40px; box-shadow: 0 14px 40px rgba(20,26,21,.07); }
.rvh { display: flex; align-items: center; gap: 22px; }
.av { width: 72px; height: 72px; border-radius: 50%; color: #fff; font-weight: 800; font-size: 38px; display: flex; align-items: center; justify-content: center; }
.nm { font-size: 40px; font-weight: 800; }
.rvs { display: flex; align-items: center; gap: 18px; margin: 18px 0 14px; }
.st { display: flex; gap: 4px; }
.st svg { width: 38px; height: 38px; fill: #f2a900; }
.wh { font-size: 32px; color: var(--muted); }
.rvt { font-size: 46px; line-height: 1.4; font-weight: 600; }
.note.sm { font-size: 34px; margin-top: 30px; }
/* end */
.end .display { font-size: 112px; }
.end .sub { margin-top: 44px; font-size: 54px; color: var(--muted); font-weight: 600; line-height: 1.4; }
.end .sign { margin-top: 90px; font-family: "JetBrains Mono", monospace; font-size: 40px; font-weight: 700; letter-spacing: 2px; }
.end .sign span { display: block; width: 120px; height: 5px; background: var(--accent); margin-top: 22px; border-radius: 3px; }
"""


def fmt(text):
    out = html.escape(text or "")
    out = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", out)
    return out.replace("\n", "<br>")


def slide_html(s, idx, total, series):
    t = s["type"]
    top = (f'<div class="top"><span class="brand">EZ.Path.AI</span>'
           f'<span class="series">{fmt(series)}</span></div>')
    bottom = f'<div class="bottom"><span dir="ltr">{idx}/{total}</span><span dir="ltr">@ez.path.ai</span></div>'
    if t == "cover":
        inner = (f'<div class="frame cover center"><div class="rule"></div>'
                 f'<div class="display">{fmt(s["title"])}</div><div class="sub">{fmt(s.get("sub"))}</div></div>')
    elif t == "text":
        k = f'<div class="kicker">{fmt(s["kicker"])}</div>' if s.get("kicker") else ""
        inner = (f'<div class="frame text center">{k}<div class="display">{fmt(s["title"])}</div>'
                 f'<div class="body">{fmt(s.get("body"))}</div></div>')
    elif t == "quote":
        note = f'<div class="note">{fmt(s["note"])}</div>' if s.get("note") else ""
        inner = (f'<div class="frame quote center"><div class="label">{fmt(s["label"])}</div>'
                 f'<div class="display">{fmt(s["title"])}</div><div class="bubble">{fmt(s["quote"])}</div>{note}</div>')
    elif t == "list":
        mark = s.get("mark", "check")
        sym = {"check": "✓", "cross": "✕"}
        lis = "".join(
            f'<li><span class="mark {mark}">{sym.get(mark, str(i + 1))}</span><span>{fmt(it)}</span></li>'
            for i, it in enumerate(s["items"]))
        note = f'<div class="note">{fmt(s["note"])}</div>' if s.get("note") else ""
        inner = (f'<div class="frame list center"><div class="display">{fmt(s["title"])}</div>'
                 f'<ul class="items">{lis}</ul>{note}</div>')
    elif t == "web":
        ttl = f'<div class="display wt">{fmt(s["title"])}</div>' if s.get("title") else ""
        inner = (f'<div class="frame web center"><div class="label">{fmt(s["label"])}</div>{ttl}'
                 f'<div class="site"><div class="bar"><i></i><i></i><i></i><span>{fmt(s["url"])}</span></div>'
                 f'<div class="hero"><div class="h">{fmt(s["head"])}</div><div class="p">{fmt(s["text"])}</div>'
                 f'<div class="btn">לקביעת תור</div></div></div></div>')
    elif t == "reviews":
        ttl = f'<div class="display wt">{fmt(s["title"])}</div>' if s.get("title") else ""
        stars = "".join('<svg viewBox="0 0 24 24"><path d="M12 2.5l2.9 6 6.6.9-4.8 4.6 1.2 6.5L12 17.4 '
                        '6.1 20.5l1.2-6.5L2.5 9.4l6.6-.9z"/></svg>' for _ in range(5))
        cols = ["#007329", "#6b3fb5", "#b35c00", "#027eb5"]
        cards = "".join(
            f'<div class="rv"><div class="rvh"><span class="av" style="background:{cols[i % 4]}">{fmt(it["name"][0])}</span>'
            f'<span class="nm">{fmt(it["name"])}</span></div><div class="rvs"><span class="st" dir="ltr">{stars}</span>'
            f'<span class="wh">{fmt(it.get("when", ""))}</span></div><div class="rvt">{fmt(it["text"])}</div></div>'
            for i, it in enumerate(s["items"]))
        note = f'<div class="note sm">{fmt(s["note"])}</div>' if s.get("note") else ""
        inner = (f'<div class="frame reviews center"><div class="label">{fmt(s["label"])}</div>{ttl}'
                 f'<div class="rvl">{cards}</div>{note}</div>')
    elif t == "end":
        inner = (f'<div class="frame end center"><div class="display">{fmt(s["title"])}</div>'
                 f'<div class="sub">{fmt(s.get("sub"))}</div><div class="sign">EZ.Path.AI<span></span></div></div>')
    else:
        raise SystemExit(f"unknown slide type: {t}")
    css = CSS.replace("FONTS", "file://" + os.path.abspath(FONTS))
    return (f'<!doctype html><html lang="he" dir="rtl"><head><meta charset="utf-8"><style>{css}</style></head>'
            f'<body>{top}{inner}{bottom}</body></html>')


def main():
    post = os.path.abspath(sys.argv[1])
    spec = json.load(open(os.path.join(post, "slides.json"), encoding="utf-8"))
    slides = spec["slides"]
    series = spec.get("series", "")
    with tempfile.TemporaryDirectory() as tmp:
        for i, s in enumerate(slides, 1):
            page = os.path.join(tmp, f"s{i}.html")
            open(page, "w", encoding="utf-8").write(slide_html(s, i, len(slides), series))
            out = os.path.join(post, f"slide-{i:02d}.png")
            subprocess.run([CHROME, "--headless=new", "--no-sandbox", "--hide-scrollbars", "--disable-gpu",
                            "--force-device-scale-factor=1", "--window-size=1080,1350",
                            "--virtual-time-budget=3000", f"--screenshot={out}", "file://" + page],
                           check=True, capture_output=True)
            # Instagram's API takes JPEG only for images.
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", out, "-q:v", "2", out[:-4] + ".jpg"], check=True)
            print(out)


if __name__ == "__main__":
    main()
