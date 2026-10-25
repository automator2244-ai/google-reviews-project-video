#!/usr/bin/env python3
"""Build the approval page from the queue.

Usage: python3 review.py <from YYYY-MM-DD> <to YYYY-MM-DD> [out_dir]
Writes <out_dir>/index.html (default: instagram/review/) with every queued post in the date range,
and prints a JSON map {published_path: local_file} to pass as the Artifact `files` parameter.
"""
import datetime as dt
import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
IG = os.path.abspath(os.path.join(HERE, ".."))
DAYS = ["שני", "שלישי", "רביעי", "חמישי", "שישי", "שבת", "ראשון"]
STATUS = {"draft": "ממתין לאישור", "approved": "אושר", "published": "פורסם", "prototype": "אב טיפוס, לא בלוח"}


def main():
    start, end = sys.argv[1], sys.argv[2]
    out_dir = sys.argv[3] if len(sys.argv) > 3 else os.path.join(IG, "review")
    posts, files = [], {}
    dirs = [d for d in sorted(glob.glob(os.path.join(IG, "queue", "20*")))
            if start <= os.path.basename(d)[:10] <= end]
    # Prototypes (instagram/prototypes/*) are shown too, as long as their status is "prototype".
    dirs += sorted(glob.glob(os.path.join(IG, "prototypes", "*")))
    for d in dirs:
        name = os.path.basename(d)
        if not os.path.exists(os.path.join(d, "meta.json")):
            continue
        meta = json.load(open(os.path.join(d, "meta.json"), encoding="utf-8"))
        if "prototypes" in d:
            if meta.get("status") != "prototype":
                continue
            slot = meta["slot"]
        else:
            date = dt.date.fromisoformat(name[:10])
            hm = name[11:13] + ":" + name[13:15]
            day = "מוצאי שבת" if date.weekday() == 5 else "יום " + DAYS[date.weekday()]
            slot = f"{day}, {date.day}.{date.month} · {hm.lstrip('0')}"
        p = {
            "slot": slot,
            "status": STATUS.get(meta.get("status", "draft"), meta.get("status")),
            "series": meta["series"].replace(" ", " · ", 1) if re.search(r"\d$", meta["series"]) else meta["series"],
            "title": meta["topic"],
            "dir": "p/" + name,
            "caption": open(os.path.join(d, "caption.txt"), encoding="utf-8").read().strip(),
            "notes": list(meta.get("sources", [])) + list(meta.get("notes", [])),
        }
        p["series"] = re.sub(r" (\d+)$", r" · \1", meta["series"])
        if os.path.exists(os.path.join(d, "reel.mp4")):
            mus = json.load(open(os.path.join(d, "music.json"), encoding="utf-8"))
            p["video"] = True
            p["format"] = f"ריל, {round(mus['duration'])} שניות, עם מוזיקה"
            lic = "נחלת הכלל, FreePD" if mus.get("license", "CC0") == "CC0" else f"{mus['license']}, Kevin MacLeod, עם קרדיט בכיתוב"
            p["notes"].append(f"מוזיקה: {mus['track'].replace('_', ' ')} ({lic}). סגנון אנימציה: {mus['style']}.")
            files[f"p/{name}/reel.mp4"] = os.path.join(d, "reel.mp4")
            poster = os.path.join(d, "poster.jpg")
            os.system(f'ffmpeg -v error -y -ss 0 -i "{d}/reel.mp4" -frames:v 1 -vf scale=540:-1 "{poster}"')
            files[f"p/{name}/poster.jpg"] = poster
        else:
            slides = sorted(glob.glob(os.path.join(d, "slide-*.jpg")))
            p["slides"] = len(slides)
            p["format"] = f"קרוסלה, {len(slides)} שקפים"
            for s in slides:
                files[f"p/{name}/{os.path.basename(s)}"] = s
        posts.append(p)
    tpl = open(os.path.join(IG, "review", "index.html"), encoding="utf-8").read()
    data = json.dumps(posts, ensure_ascii=False, indent=1)
    page = re.sub(r"const POSTS = \[.*?\n\s*\];", lambda m: "const POSTS = " + data + ";", tpl, count=1, flags=re.S)
    page = page.replace(".png`", ".jpg`").replace('.png" alt=', '.jpg" alt=')
    os.makedirs(out_dir, exist_ok=True)
    open(os.path.join(out_dir, "index.html"), "w", encoding="utf-8").write(page)
    print(json.dumps(files, ensure_ascii=False))


if __name__ == "__main__":
    main()
