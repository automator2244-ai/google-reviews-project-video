#!/usr/bin/env python3
"""Add or refresh the music credit in a post's caption.txt.

Usage: python3 credit.py <post_dir>
If the post's music.json has a "credit" (CC BY tracks), the caption gets a credit block right before
the hashtag line. A CC0 track removes any old block. Run it again after every caption edit; it is idempotent.
"""
import json
import os
import sys

MARK = "🎵 מוזיקה (קטע מקוצר):"


def main():
    post = sys.argv[1]
    cap_p, mus_p = os.path.join(post, "caption.txt"), os.path.join(post, "music.json")
    if not (os.path.exists(cap_p) and os.path.exists(mus_p)):
        return
    credit = json.load(open(mus_p, encoding="utf-8")).get("credit")
    paras = open(cap_p, encoding="utf-8").read().strip().split("\n\n")
    paras = [p for p in paras if not p.startswith(MARK)]
    if credit:
        block = MARK + " " + credit
        tags = len(paras) - 1 if paras and paras[-1].lstrip().startswith("#") else len(paras)
        paras.insert(tags, block)
    open(cap_p, "w", encoding="utf-8").write("\n\n".join(paras) + "\n")
    print("credit:", "added" if credit else "none needed")


if __name__ == "__main__":
    main()
