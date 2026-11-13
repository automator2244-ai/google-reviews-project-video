#!/usr/bin/env python3
"""Build repost/<slot>/ for every post in repost/plan.json: a copy of the published post with a new first screen.

The original folder in queue/ stays as the record of what was published. Here the opening changes:
  reel      "hook" replaces the first scene (or goes before it, with "mode": "prepend"); the music stays pinned
  carousel  "slide" replaces the cover: {"style", "cover"} for a covers.py look, or {"tone"} for a brand cover
Usage: python3 repost/build.py   (then render each folder with tools/reel.py or tools/carousel.py)
"""
import json
import os
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
IG = os.path.dirname(HERE)
SKIP = {"build", "reel.mp4", "render.log", "poster.jpg"}

for e in json.load(open(os.path.join(HERE, "plan.json"), encoding="utf-8")):
    slot = e["slot"]
    src, dst = os.path.join(IG, "queue", slot), os.path.join(HERE, slot)
    os.makedirs(dst, exist_ok=True)
    for f in os.listdir(src):
        if f in SKIP or f.startswith("slide-"):
            continue
        p = os.path.join(src, f)
        if os.path.isfile(p):
            shutil.copy(p, os.path.join(dst, f))
    meta = json.load(open(os.path.join(src, "meta.json"), encoding="utf-8"))
    old = {k: meta.pop(k, None) for k in ("permalink", "media_id", "published_at", "missed")}
    meta.update(status="approved", repost=True, repost_of=old["permalink"], old_media_id=old["media_id"],
                approved_repost="2026-11-13, בניה: אישור מלא לשינוי המסך הראשון ולהעלאה מחדש")
    if "hook" in e:
        r = json.load(open(os.path.join(src, "reel.json"), encoding="utf-8"))
        r["music"] = json.load(open(os.path.join(src, "music.json"), encoding="utf-8"))["track"]
        hook = dict({"dur": 2.6 if e["hook"].get("look") == "cover" else 2.4, "type": "hook"}, **e["hook"])
        if e.get("mode") == "prepend":
            r["scenes"].insert(0, hook)
        else:
            r["scenes"][0] = hook
        json.dump(r, open(os.path.join(dst, "reel.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        meta["cover"] = e["hook"].get("style") or e["hook"]["look"]
    else:
        s = json.load(open(os.path.join(src, "slides.json"), encoding="utf-8"))
        was = s["slides"][0]
        if e["slide"].get("style"):
            s["slides"][0] = {"type": "cover", "style": e["slide"]["style"], "cover": e["slide"]["cover"], "was": was}
            meta["cover"] = e["slide"]["style"]
        else:
            s["slides"][0] = dict(was, tone=e["slide"]["tone"])
            meta["cover"] = "brand " + e["slide"]["tone"]
        json.dump(s, open(os.path.join(dst, "slides.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump(meta, open(os.path.join(dst, "meta.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(slot, meta["cover"])
