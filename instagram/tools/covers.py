"""Opening frames ("the first screen") that look nothing like the brand slides.

One stage of 1080x1350 that both tools use: carousel.py renders it as the whole cover, and reel.py places it
in the middle of the 1080x1920 frame (top 285) as the hook scene. Keep what matters above y 1150 of the stage,
so in a reel it stays clear of the caption and buttons.

render(style, d, img) -> (bg_css, stage_html)
  style  chat | poster | face | vs | newspaper | maps | timer | postit | calendar | notes
  d      the fields of that style (below). *word* marks a highlighted word.
  img    URL prefix where bnaya.jpg can be loaded from (assets/ in a reel build, file://.../assets/ in a carousel)
"""
import html
import re


def fmt(t, cls="cv-hl"):
    t = html.escape(t or "")
    t = re.sub(r"\*([^*]+)\*", rf'<span class="{cls}">\1</span>', t)
    return t.replace("\n", "<br>")


CHECK = '<svg viewBox="0 0 24 24"><path d="M5 12.5l4.2 4.2L19 7" fill="none" stroke="currentColor" stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round"/></svg>'
CROSS = '<svg viewBox="0 0 24 24"><path d="M6 6l12 12M18 6L6 18" fill="none" stroke="currentColor" stroke-width="3.4" stroke-linecap="round"/></svg>'
TICKS = ('<svg class="cv-ticks" viewBox="0 0 34 20"><path d="M2 11l5 5L17 4M14 14l2 2L28 4" fill="none" '
         'stroke="#53bdeb" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/></svg>')
MAG = '<svg viewBox="0 0 24 24"><circle cx="10" cy="10" r="6.5" fill="none" stroke="#5f6368" stroke-width="2.4"/><path d="M15 15l5 5" stroke="#5f6368" stroke-width="2.6" stroke-linecap="round"/></svg>'

CSS = """
.cv-stage { position: absolute; left: 0; width: 1080px; height: 1350px; direction: rtl; font-family: "Assistant", sans-serif; }
.cv-stage * { box-sizing: border-box; }
.cv-heavy { font-family: "Assistant", sans-serif; font-weight: 800; letter-spacing: -1px; }

/* chat: a WhatsApp-like screen */
.cv-chat .cv-bar { position: absolute; top: 0; left: 0; right: 0; height: 132px; background: #008069; color: #fff; display: flex; align-items: center; gap: 22px; padding: 0 40px; }
.cv-chat .cv-av { width: 76px; height: 76px; border-radius: 50%; background: #d9fdd3; color: #008069; font-weight: 800; font-size: 40px; display: flex; align-items: center; justify-content: center; }
.cv-chat .cv-nm { font-weight: 800; font-size: 42px; line-height: 1.1; }
.cv-chat .cv-nm small { display: block; font-weight: 500; font-size: 30px; opacity: .85; }
.cv-chat .cv-col { position: absolute; top: 190px; left: 70px; right: 70px; display: flex; flex-direction: column; gap: 46px; }
.cv-chat .cv-ttl { font-size: 104px; line-height: 1.02; color: #111b21; }
.cv-chat .cv-hl { background: #ffd60a; padding: 0 14px; border-radius: 10px; box-decoration-break: clone; -webkit-box-decoration-break: clone; }
.cv-chat .cv-bub { align-self: flex-end; max-width: 860px; background: #d9fdd3; border-radius: 26px 26px 26px 6px; padding: 30px 34px 18px; font-size: 46px; line-height: 1.34; font-weight: 600; color: #111b21; box-shadow: 0 2px 3px rgba(0,0,0,.13); }
.cv-chat .cv-meta { display: flex; justify-content: flex-start; align-items: center; gap: 8px; direction: ltr; font-size: 28px; color: #667781; margin-top: 8px; }
.cv-ticks { width: 40px; height: 24px; }
.cv-chat .cv-in { align-self: flex-start; background: #fff; border-radius: 26px 6px 26px 26px; }
.cv-chat .cv-stk { align-self: flex-start; margin-right: 30px; transform: rotate(-5deg); background: #111b21; color: #ffd60a; font-weight: 800; font-size: 50px; padding: 18px 34px; border-radius: 14px; }

/* poster: one loud color, huge sans */
.cv-poster .cv-col { position: absolute; top: 120px; bottom: 200px; left: 90px; right: 90px; display: flex; flex-direction: column; justify-content: center; gap: 40px; }
.cv-poster .cv-k { font-weight: 800; font-size: 56px; }
.cv-poster .cv-t { line-height: .96; }
.cv-poster .cv-s { font-weight: 700; font-size: 56px; line-height: 1.3; }
.cv-poster .cv-hl, .cv-face .cv-hl { color: var(--acc); }
.cv-stripes { position: absolute; left: 0; right: 0; height: 70px; background: repeating-linear-gradient(-45deg, #111 0 40px, #ffd000 40px 80px); }

/* face: a framed photo of Benaya and a speech bubble */
.cv-face .cv-pol { position: absolute; top: 70px; right: 90px; width: 560px; background: #fff; padding: 22px 22px 78px; transform: rotate(-4deg); box-shadow: 0 30px 60px rgba(0,0,0,.28); }
.cv-face .cv-pol img { display: block; width: 516px; height: 516px; object-fit: cover; }
.cv-face .cv-pol span { position: absolute; bottom: 18px; right: 0; left: 0; text-align: center; font-weight: 700; font-size: 38px; color: #333; }
.cv-face .cv-bub { position: absolute; top: 150px; left: 60px; width: 440px; background: #fff; color: #111; border-radius: 40px; padding: 34px 38px; font-weight: 800; font-size: 46px; line-height: 1.2; box-shadow: 0 16px 40px rgba(0,0,0,.22); transform: rotate(3deg); }
.cv-face .cv-bub::after { content: ""; position: absolute; right: -26px; top: 70px; border: 22px solid transparent; border-left-color: #fff; }
.cv-face .cv-t { position: absolute; top: 760px; left: 80px; right: 80px; line-height: 1.0; }

/* vs: two halves, X against V */
.cv-vs .cv-half { position: absolute; left: 0; right: 0; height: 675px; display: flex; align-items: center; gap: 50px; padding: 0 90px; }
.cv-vs .cv-a { top: 0; background: #dfe3e8; color: #4a5560; }
.cv-vs .cv-b { top: 675px; background: #ffd84d; color: #141a15; }
.cv-vs .cv-ic { flex: 0 0 190px; height: 190px; border-radius: 50%; color: #fff; display: flex; align-items: center; justify-content: center; }
.cv-vs .cv-ic svg { width: 120px; height: 120px; }
.cv-vs .cv-a .cv-ic { background: #d93025; }
.cv-vs .cv-b .cv-ic { background: #188038; }
.cv-vs .cv-lbl { font-weight: 700; font-size: 44px; margin-bottom: 10px; }
.cv-vs .cv-big { font-size: 112px; line-height: 1; }
.cv-vs .cv-mid { position: absolute; top: 675px; left: 50%; transform: translate(-50%, -50%) rotate(-3deg); background: #141a15; color: #fff; font-weight: 800; font-size: 50px; padding: 20px 44px; border-radius: 60px; white-space: nowrap; }

/* newspaper: a front page */
.cv-news .cv-mast { position: absolute; top: 40px; left: 70px; right: 70px; text-align: center; font-family: "Frank Ruhl Libre", serif; font-weight: 900; font-size: 116px; color: #1a1a1a; line-height: 1.1; }
.cv-news .cv-rule { position: absolute; left: 70px; right: 70px; border-top: 6px double #1a1a1a; }
.cv-news .cv-dl { position: absolute; top: 210px; left: 70px; right: 70px; display: flex; justify-content: space-between; font-family: "JetBrains Mono", monospace; font-size: 26px; color: #444; }
.cv-news .cv-h { position: absolute; top: 300px; left: 70px; right: 70px; font-size: 122px; line-height: 1.0; color: #111; }
.cv-news .cv-h .cv-hl { background: #ffe14d; padding: 0 10px; box-decoration-break: clone; -webkit-box-decoration-break: clone; }
.cv-news .cv-sub { position: absolute; top: 700px; left: 70px; right: 70px; font-family: "Frank Ruhl Libre", serif; font-weight: 700; font-size: 54px; line-height: 1.25; color: #333; border-right: 10px solid #d62828; padding-right: 26px; }
.cv-news .cv-cols { position: absolute; top: 930px; left: 70px; right: 70px; display: grid; grid-template-columns: 1fr 1fr 320px; gap: 36px; }
.cv-news .cv-cols i { display: block; height: 14px; background: #c9c2b2; margin-bottom: 18px; border-radius: 3px; }
.cv-news .cv-ph { height: 230px; background: #c9c2b2; }

/* maps: local search results with a red circle drawn by hand */
.cv-maps .cv-sb { position: absolute; top: 40px; left: 60px; right: 60px; height: 120px; border-radius: 60px; background: #fff; box-shadow: 0 4px 18px rgba(0,0,0,.16); display: flex; align-items: center; gap: 24px; padding: 0 44px; font-size: 46px; color: #202124; font-weight: 600; }
.cv-maps .cv-sb svg { width: 50px; height: 50px; flex: 0 0 50px; }
.cv-maps .cv-map { position: absolute; top: 200px; left: 60px; right: 60px; height: 300px; border-radius: 26px; overflow: hidden; background: linear-gradient(135deg, #e6efe0 0%, #f2f0e6 45%, #d7e6f4 100%); }
.cv-maps .cv-map i { position: absolute; background: #fff; }
.cv-maps .cv-pin { position: absolute; width: 46px; height: 46px; border-radius: 50% 50% 50% 0; background: #d93025; transform: rotate(-45deg); }
.cv-maps .cv-res { position: absolute; left: 60px; right: 60px; height: 150px; background: #fff; border-radius: 22px; padding: 22px 34px; box-shadow: 0 1px 6px rgba(0,0,0,.08); }
.cv-maps .cv-res b { display: block; font-size: 44px; color: #1a0dab; font-weight: 700; }
.cv-maps .cv-res span { font-size: 38px; color: #70757a; direction: rtl; }
.cv-maps .cv-res .cv-st { color: #fbbc04; letter-spacing: 2px; }
.cv-maps .cv-circle { position: absolute; }
.cv-maps .cv-note { position: absolute; top: 1010px; left: 70px; right: 70px; font-weight: 800; font-size: 92px; line-height: 1.0; color: #d93025; transform: rotate(-3deg); }

/* timer: a phone stopwatch */
.cv-timer .cv-ring { position: absolute; top: 40px; left: 50%; margin-left: -330px; width: 660px; height: 660px; }
.cv-timer .cv-dg { position: absolute; top: 250px; left: 0; right: 0; text-align: center; direction: ltr; font-weight: 200; font-size: 200px; color: #fff; letter-spacing: -4px; }
.cv-timer .cv-lb { position: absolute; top: 500px; left: 0; right: 0; text-align: center; font-weight: 600; font-size: 40px; color: #8e8e93; }
.cv-timer .cv-t { position: absolute; top: 790px; left: 90px; right: 90px; line-height: 1.0; color: #fff; text-align: center; }
.cv-timer .cv-hl { color: #ff9f0a; }

/* postit: a sticky note on a monitor */
.cv-postit .cv-mon { position: absolute; top: 50px; left: 70px; right: 70px; height: 600px; border-radius: 30px; background: #1f2933; padding: 26px; }
.cv-postit .cv-mon i { display: block; height: 100%; border-radius: 14px; background: linear-gradient(160deg, #3a4b57, #23303a); }
.cv-postit .cv-note { position: absolute; top: 330px; right: 110px; width: 540px; min-height: 480px; background: #ffe066; transform: rotate(5deg); padding: 70px 50px 40px; box-shadow: 0 24px 40px rgba(0,0,0,.3); font-weight: 800; font-size: 66px; line-height: 1.12; color: #222; }
.cv-postit .cv-note::before { content: ""; position: absolute; top: -26px; left: 50%; margin-left: -110px; width: 220px; height: 60px; background: rgba(255,255,255,.55); transform: rotate(-3deg); }
.cv-postit .cv-note u { text-decoration-thickness: 8px; text-underline-offset: 10px; text-decoration-color: #d93025; }
.cv-postit .cv-t { position: absolute; top: 900px; left: 70px; right: 70px; line-height: 1.22; }
.cv-postit .cv-t span.cv-box { background: #fff; color: #111; padding: 4px 22px; border-radius: 12px; box-decoration-break: clone; -webkit-box-decoration-break: clone; }
.cv-postit .cv-hl { color: #d93025; }

/* calendar: a tear-off calendar page */
.cv-cal .cv-pg { position: absolute; top: 50px; left: 50%; margin-left: -330px; width: 660px; height: 740px; background: #fff; border-radius: 26px; overflow: hidden; box-shadow: 0 30px 60px rgba(60,40,20,.25); text-align: center; }
.cv-cal .cv-band { height: 170px; background: #d62828; color: #fff; font-weight: 800; font-size: 64px; display: flex; align-items: center; justify-content: center; position: relative; }
.cv-cal .cv-band i { position: absolute; top: 24px; width: 34px; height: 34px; border-radius: 50%; background: #e9dfcf; }
.cv-cal .cv-day { font-weight: 800; font-size: 250px; color: #d62828; line-height: 1; margin-top: 90px; }
.cv-cal .cv-dsub { font-weight: 600; font-size: 46px; color: #777; margin-top: 30px; }
.cv-cal .cv-t { position: absolute; top: 880px; left: 80px; right: 80px; line-height: 1.02; color: #2b2b2b; text-align: center; }
.cv-cal .cv-hl { color: #d62828; }

/* notes: the phone's notes app */
.cv-notes .cv-top { position: absolute; top: 40px; left: 70px; right: 70px; display: flex; justify-content: space-between; font-weight: 600; font-size: 40px; color: #d4a017; }
.cv-notes .cv-dt { position: absolute; top: 130px; left: 0; right: 0; text-align: center; font-size: 30px; color: #8e8e93; }
.cv-notes .cv-ttl { position: absolute; top: 200px; left: 70px; right: 70px; font-size: 100px; line-height: 1.04; color: #111; }
.cv-notes ul { position: absolute; top: 470px; left: 70px; right: 70px; list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 34px; }
.cv-notes li { display: flex; align-items: center; gap: 30px; font-size: 54px; font-weight: 600; color: #111; }
.cv-notes li b { flex: 0 0 62px; height: 62px; border-radius: 50%; border: 4px solid #c7c7cc; color: #fff; display: flex; align-items: center; justify-content: center; }
.cv-notes li b svg { width: 40px; height: 40px; }
.cv-notes li.cv-on b { background: #e0a800; border-color: #e0a800; }
"""


def render(style, d, img):
    if style == "chat":
        bg = "background: #efeae2; background-image: radial-gradient(#e2d9cc 2px, transparent 2px); background-size: 46px 46px;"
        stk = f'<div class="cv-stk">{fmt(d["sticker"])}</div>' if d.get("sticker") else ""
        if d.get("reply"):
            stk = (f'<div class="cv-bub cv-in">{fmt(d["reply"])}<div class="cv-meta"><span>'
                   f'{fmt(d.get("reply_time", "18:09"))}</span></div></div>') + stk
        body = (f'<div class="cv-bar"><span class="cv-av">{fmt(d.get("initial", "מ"))}</span>'
                f'<span class="cv-nm">{fmt(d.get("name", "מרפאת השיניים"))}<small>{fmt(d.get("status", "מקוון"))}</small></span></div>'
                f'<div class="cv-col"><div class="cv-ttl cv-heavy">{fmt(d["title"])}</div>'
                f'<div class="cv-bub">{fmt(d["msg"])}<div class="cv-meta">{TICKS}<span>{fmt(d.get("time", "18:02"))}</span></div></div>{stk}</div>')
        return bg, f'<div class="cv-stage cv-chat">{body}</div>'
    if style == "poster":
        bgc, fg, acc = d.get("bg", "#e5322d"), d.get("fg", "#fff"), d.get("accent", "#ffd60a")
        k = f'<div class="cv-k" style="color:{d.get("kfg", acc)}">{fmt(d["kicker"])}</div>' if d.get("kicker") else ""
        s = f'<div class="cv-s" style="color:{d.get("sfg", fg)}">{fmt(d["sub"])}</div>' if d.get("sub") else ""
        stripes = ('<div class="cv-stripes" style="top:0"></div><div class="cv-stripes" style="bottom:110px"></div>'
                   if d.get("stripes") else "")
        t = f'<div class="cv-t cv-heavy" style="font-size:{d.get("size", 200)}px;color:{fg}">{fmt(d["text"])}</div>'
        return f"background: {bgc};", f'<div class="cv-stage cv-poster" style="--acc:{acc}">{stripes}<div class="cv-col">{k}{t}{s}</div></div>'
    if style == "face":
        bgc, fg, acc = d.get("bg", "#1d4ed8"), d.get("fg", "#fff"), d.get("accent", "#ffd60a")
        t = f'<div class="cv-t cv-heavy" style="font-size:{d.get("size", 124)}px;color:{fg};--acc:{acc}">{fmt(d["text"])}</div>'
        body = (f'<div class="cv-pol"><img src="{img}bnaya.jpg" alt=""><span>{fmt(d.get("name", "בניה, EZ.Path.AI"))}</span></div>'
                f'<div class="cv-bub">{fmt(d["bubble"])}</div>{t}')
        return f"background: {bgc};", f'<div class="cv-stage cv-face">{body}</div>'
    if style == "vs":
        body = (f'<div class="cv-half cv-a"><span class="cv-ic">{CROSS}</span><div><div class="cv-lbl">{fmt(d["a_label"])}</div>'
                f'<div class="cv-big cv-heavy">{fmt(d["a"])}</div></div></div>'
                f'<div class="cv-half cv-b"><span class="cv-ic">{CHECK}</span><div><div class="cv-lbl">{fmt(d["b_label"])}</div>'
                f'<div class="cv-big cv-heavy">{fmt(d["b"])}</div></div></div><div class="cv-mid">{fmt(d["mid"])}</div>')
        return "background: #dfe3e8;", f'<div class="cv-stage cv-vs">{body}</div>'
    if style == "newspaper":
        lines = "".join("<i></i>" for _ in range(9))
        body = (f'<div class="cv-mast">{fmt(d.get("masthead", "יומון המרפאה"))}</div>'
                '<div class="cv-rule" style="top:190px"></div><div class="cv-rule" style="top:262px"></div>'
                f'<div class="cv-dl"><span>{fmt(d.get("date", ""))}</span><span>{fmt(d.get("issue", "מהדורה מיוחדת"))}</span></div>'
                f'<div class="cv-h cv-heavy" style="font-size:{d.get("size", 122)}px">{fmt(d["text"])}</div>'
                f'<div class="cv-sub">{fmt(d["sub"])}</div>'
                f'<div class="cv-cols"><div>{lines}</div><div>{lines}</div><div class="cv-ph"></div></div>')
        return "background: #f3eee2;", f'<div class="cv-stage cv-news">{body}</div>'
    if style == "maps":
        rows = ""
        for i, (name, rate, cnt) in enumerate(d["results"]):
            stars = "★" * round(float(rate)) + "☆" * (5 - round(float(rate)))
            rows += (f'<div class="cv-res" style="top:{525 + i * 175}px"><b>{fmt(name)}</b>'
                     f'<span>{rate} <span class="cv-st">{stars}</span> ({cnt}) · רופא שיניים</span></div>')
        mp = ('<div class="cv-map"><i style="top:120px;left:0;right:0;height:16px"></i><i style="left:300px;top:0;bottom:0;width:16px"></i>'
              '<i style="left:640px;top:0;bottom:0;width:12px;transform:rotate(18deg)"></i>'
              '<span class="cv-pin" style="top:70px;left:200px"></span><span class="cv-pin" style="top:170px;left:520px"></span>'
              '<span class="cv-pin" style="top:60px;left:780px"></span></div>')
        circle = ('<svg class="cv-circle" style="top:500px;left:20px;width:1040px;height:200px" viewBox="0 0 1040 200">'
                  '<path d="M90 30 C 400 0, 900 4, 1010 60 C 1050 120, 900 190, 520 192 C 200 194, 20 170, 16 110 '
                  'C 12 60, 80 30, 200 22" fill="none" stroke="#d93025" stroke-width="10" stroke-linecap="round"/></svg>')
        body = (f'<div class="cv-sb">{MAG}<span>{fmt(d["query"])}</span></div>{mp}{rows}{circle}'
                f'<div class="cv-note">{fmt(d["note"])}</div>')
        return "background: #f1f3f4;", f'<div class="cv-stage cv-maps">{body}</div>'
    if style == "timer":
        frac = d.get("frac", 0.8)
        c = 2 * 3.14159 * 300
        ring = (f'<svg class="cv-ring" viewBox="0 0 660 660"><circle cx="330" cy="330" r="300" fill="none" stroke="#2c2c2e" stroke-width="22"/>'
                f'<circle cx="330" cy="330" r="300" fill="none" stroke="#ff9f0a" stroke-width="22" stroke-linecap="round" '
                f'stroke-dasharray="{c * frac:.0f} {c:.0f}" transform="rotate(-90 330 330)"/></svg>')
        body = (f'{ring}<div class="cv-dg">{fmt(d["digits"])}</div><div class="cv-lb">{fmt(d.get("label", ""))}</div>'
                f'<div class="cv-t cv-heavy" style="font-size:{d.get("size", 116)}px">{fmt(d["text"])}</div>')
        return "background: #000;", f'<div class="cv-stage cv-timer">{body}</div>'
    if style == "postit":
        text = fmt(d["text"]).replace("<br>", "</span><br><span class=\"cv-box\">")
        body = (f'<div class="cv-mon"><i></i></div><div class="cv-note">{fmt(d["note"])}</div>'
                f'<div class="cv-t cv-heavy" style="font-size:{d.get("size", 92)}px"><span class="cv-box">{text}</span></div>')
        return "background: linear-gradient(180deg, #cfd8dc, #9fb0b9);", f'<div class="cv-stage cv-postit">{body}</div>'
    if style == "calendar":
        body = (f'<div class="cv-pg"><div class="cv-band"><i style="right:150px"></i><i style="left:150px"></i>{fmt(d.get("month", "נובמבר"))}</div>'
                f'<div class="cv-day">{fmt(d["day"])}</div><div class="cv-dsub">{fmt(d.get("dsub", ""))}</div></div>'
                f'<div class="cv-t cv-heavy" style="font-size:{d.get("size", 110)}px">{fmt(d["text"])}</div>')
        return "background: #e9dfcf;", f'<div class="cv-stage cv-cal">{body}</div>'
    if style == "notes":
        on = set(d.get("checked", []))
        items = "".join(f'<li class="{"cv-on" if i in on else ""}"><b>{CHECK if i in on else ""}</b>{fmt(t)}</li>'
                        for i, t in enumerate(d["items"]))
        body = (f'<div class="cv-top"><span>‹ פתקים</span><span>סיום</span></div><div class="cv-dt">{fmt(d.get("date", ""))}</div>'
                f'<div class="cv-ttl cv-heavy">{fmt(d["title"])}</div><ul>{items}</ul>')
        return "background: #fff;", f'<div class="cv-stage cv-notes">{body}</div>'
    raise SystemExit(f"unknown cover style {style}")
