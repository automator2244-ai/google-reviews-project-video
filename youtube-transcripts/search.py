"""Search the downloaded transcripts.

    python search.py "how to price a service"          best matching paragraphs
    python search.py "pricing" --channel veritasium -n 30
    python search.py "pricing NEAR/5 clients" --raw    SQLite FTS5 syntax as is
    python search.py --list                            channels and video counts

Builds a local SQLite full text index (.index.db, not in git) from channels/*/*.md
and rebuilds it whenever a transcript file was added or changed.
"""

import argparse
import hashlib
import json
import re
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CHANNELS = ROOT / "channels"
DB = ROOT / ".index.db"
LINE = re.compile(r"^\[(?:(\d+):)?(\d+):(\d+)\] (.*)$")


def files():
    return sorted(CHANNELS.glob("*/*.md"))


def signature(paths):
    h = hashlib.sha1()
    for p in paths:
        st = p.stat()
        h.update(f"{p}|{st.st_mtime_ns}|{st.st_size}\n".encode())
    return h.hexdigest()


def parse(path):
    text = path.read_text(encoding="utf-8")
    title = text.splitlines()[0].lstrip("# ").strip()
    vid = re.search(r"watch\?v=([\w-]+)", text)
    date = re.search(r"^- date: (\S+)", text, re.M)
    paras = []
    for line in text.splitlines():
        m = LINE.match(line)
        if m:
            h, mnt, s, body = m.groups()
            paras.append((int(h or 0) * 3600 + int(mnt) * 60 + int(s), body))
    return title, vid.group(1) if vid else "", date.group(1) if date else "", paras


def open_index():
    paths = files()
    sig = signature(paths)
    con = sqlite3.connect(DB)
    con.execute("CREATE TABLE IF NOT EXISTS meta (k TEXT PRIMARY KEY, v TEXT)")
    row = con.execute("SELECT v FROM meta WHERE k='sig'").fetchone()
    if row and row[0] == sig:
        return con
    con.execute("DROP TABLE IF EXISTS chunks")
    con.execute("CREATE VIRTUAL TABLE chunks USING fts5(text, title, channel UNINDEXED, video UNINDEXED, "
                "date UNINDEXED, start UNINDEXED, pos UNINDEXED, file UNINDEXED, tokenize='porter unicode61')")
    for p in paths:
        title, vid, date, paras = parse(p)
        con.executemany("INSERT INTO chunks VALUES (?,?,?,?,?,?,?,?)",
                        [(body, title, p.parent.name, vid, date, start, i, str(p.relative_to(ROOT)))
                         for i, (start, body) in enumerate(paras)])
    con.execute("INSERT OR REPLACE INTO meta VALUES ('sig', ?)", (sig,))
    con.commit()
    return con


def fmt(seconds):
    h, rest = divmod(int(seconds), 3600)
    m, s = divmod(rest, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


def to_query(text):
    words = re.findall(r"\w+", text.lower())
    return " OR ".join(f'"{w}"' for w in words)


def search(args):
    con = open_index()
    query = args.query if args.raw else to_query(args.query)
    if not query:
        sys.exit("Empty query.")
    sql = ("SELECT channel, title, video, date, start, pos, file, text FROM chunks WHERE chunks MATCH ?"
           + (" AND channel = ?" if args.channel else "") + " ORDER BY bm25(chunks, 1.0, 0.3) LIMIT ?")
    params = [query] + ([args.channel.lstrip("@").lower()] if args.channel else []) + [args.n]
    rows = con.execute(sql, params).fetchall()
    if not rows:
        print("No matches.")
    for channel, title, video, date, start, pos, file, text in rows:
        print(f"== {title}  [{channel}, {date}]")
        print(f"   {fmt(start)}  https://www.youtube.com/watch?v={video}&t={int(start)}s  ({file})")
        if args.context:
            around = con.execute("SELECT pos, text FROM chunks WHERE file = ? AND CAST(pos AS INT) BETWEEN ? AND ? "
                                 "ORDER BY CAST(pos AS INT)", (file, int(pos) - args.context, int(pos) + args.context))
            text = " ".join(t for _, t in around)
        print(f"   {text}\n")


def list_channels():
    for folder in sorted(p for p in CHANNELS.glob("*") if p.is_dir()):
        meta_path = folder / "channel.json"
        meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}
        print(f"{folder.name}: {meta.get('name', '?')}, {len(list(folder.glob('*.md')))} transcripts")


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    p = argparse.ArgumentParser(description="Search the downloaded YouTube transcripts.")
    p.add_argument("query", nargs="?", default="")
    p.add_argument("--channel", help="folder name under channels/, e.g. veritasium")
    p.add_argument("-n", type=int, default=15, help="number of results")
    p.add_argument("--context", type=int, default=1, help="paragraphs to show before and after each hit")
    p.add_argument("--raw", action="store_true", help="pass the query to FTS5 as is")
    p.add_argument("--list", action="store_true", help="list channels")
    args = p.parse_args()
    if args.list or not args.query:
        list_channels()
    else:
        search(args)


if __name__ == "__main__":
    main()
