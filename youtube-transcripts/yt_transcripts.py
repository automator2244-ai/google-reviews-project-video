"""Download the transcripts of a YouTube channel, slowly, so YouTube does not block us.

Usage (on Windows through yt.bat):
    yt @channel                      every video on the channel
    yt @channel --limit 50           the 50 newest videos not downloaded yet
    yt @channel --limit 50 --oldest  the 50 oldest
    yt status                        what was downloaded so far

Every video is written to channels/<handle>/ as soon as it is fetched, so a run
can stop at any point and the next run continues where it stopped. Progress is
committed and pushed to GitHub every few videos and at the end.

Console messages are in English on purpose: the Windows console shows Hebrew
letters in reverse order.
"""

import argparse
import json
import random
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CHANNELS = ROOT / "channels"

LANGS = ["en", "en-US", "en-GB"]
PARAGRAPH_SECONDS = 30
LONG_BREAK_EVERY = 25
LONG_BREAK_SECONDS = (5 * 60, 10 * 60)
PUSH_EVERY = 20
BLOCK_WAITS_MINUTES = [15, 30, 60]
MAX_ERRORS_IN_A_ROW = 5


class Blocked(Exception):
    """YouTube refused us (rate limit, bot check, IP block)."""


class NoTranscript(Exception):
    """The video has no transcript at all."""


def say(msg=""):
    print(msg, flush=True)


def fmt_time(seconds):
    seconds = int(seconds)
    h, rest = divmod(seconds, 3600)
    m, s = divmod(rest, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


def fmt_duration(seconds):
    seconds = int(seconds)
    h, rest = divmod(seconds, 3600)
    m = rest // 60
    return f"{h}h {m}m" if h else f"{m}m"


def wait(seconds, why):
    say(f"  {why}: waiting {fmt_time(seconds)} ...")
    time.sleep(seconds)


# ---------- channel listing ----------

def channel_base_url(arg):
    arg = arg.strip()
    if arg.startswith("@"):
        return f"https://www.youtube.com/{arg}"
    if not arg.startswith("http"):
        arg = "https://" + arg.lstrip("/")
    arg = arg.split("?")[0].rstrip("/")
    return re.sub(r"/(videos|shorts|streams|featured|playlists|community|about)$", "", arg)


def list_channel(arg, include_shorts, include_streams, max_items=0):
    import yt_dlp

    base = channel_base_url(arg)
    tabs = ["videos"] + (["shorts"] if include_shorts else []) + (["streams"] if include_streams else [])
    opts = {
        "extract_flat": "in_playlist",
        "quiet": True,
        "no_warnings": True,
        "sleep_interval_requests": 1,
        # A page that fails mid-way keeps what was listed so far instead of stopping the run.
        "ignoreerrors": True,
        "extractor_args": {"youtubetab": {"approximate_date": [""]}},
    }
    if max_items:
        opts["playlistend"] = max_items
    info, videos, seen = None, [], set()
    with yt_dlp.YoutubeDL(opts) as ydl:
        for tab in tabs:
            say(f"Listing {base}/{tab} ...")
            data = None
            for attempt in range(3 if tab == "videos" else 1):
                if attempt:
                    wait(attempt * 120, "Listing failed, trying again")
                try:
                    data = ydl.extract_info(f"{base}/{tab}", download=False)
                except yt_dlp.utils.DownloadError:
                    data = None
                if data:
                    break
            if not data:
                if tab == "videos":
                    raise SystemExit("Could not read the channel. Check the link, or try again later.")
                say(f"  (no {tab} tab, skipping)")
                continue
            info = info or data
            for e in data.get("entries") or []:
                vid = e.get("id")
                if not vid or vid in seen:
                    continue
                seen.add(vid)
                ts = e.get("timestamp")
                videos.append({
                    "id": vid,
                    "title": e.get("title") or "",
                    "date": datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%d") if ts else "",
                    "duration": int(e.get("duration") or 0),
                    "kind": tab,
                })
    if info is None:
        raise SystemExit("Could not read the channel.")
    handle = info.get("uploader_id") or ""
    channel = {
        "name": info.get("channel") or info.get("uploader") or handle,
        "handle": handle,
        "channel_id": info.get("channel_id") or "",
        "url": info.get("channel_url") or base,
    }
    # Newest first; videos without a date go last.
    videos.sort(key=lambda v: v["date"] or "0000", reverse=True)
    return channel, videos


def channel_slug(channel):
    raw = channel["handle"].lstrip("@") or channel["channel_id"] or channel["name"]
    return re.sub(r"[^A-Za-z0-9._-]+", "_", raw).strip("_").lower() or "channel"


def slug_guess(arg):
    """Folder name for an @handle argument before the channel is listed (empty for other links)."""
    m = re.search(r"@([^/?]+)", arg)
    return re.sub(r"[^A-Za-z0-9._-]+", "_", m.group(1)).strip("_").lower() if m else "_none_"


# ---------- transcripts ----------

def fetch_transcript(api, video_id):
    """Returns (snippets, language_code, is_generated). snippets: [(start, text)]."""
    from youtube_transcript_api import (
        AgeRestricted, CouldNotRetrieveTranscript, IpBlocked, NoTranscriptFound,
        RequestBlocked, TranscriptsDisabled, VideoUnavailable, VideoUnplayable,
    )

    try:
        tlist = api.list(video_id)
        try:
            t = tlist.find_manually_created_transcript(LANGS)
        except NoTranscriptFound:
            try:
                t = tlist.find_generated_transcript(LANGS)
            except NoTranscriptFound:
                t = next(iter(tlist), None)
                if t is None:
                    raise NoTranscript("no transcript in any language")
        fetched = t.fetch()
    except (IpBlocked, RequestBlocked) as e:
        raise Blocked(type(e).__name__) from e
    except (TranscriptsDisabled, NoTranscriptFound) as e:
        raise NoTranscript(type(e).__name__) from e
    except (VideoUnavailable, VideoUnplayable, AgeRestricted) as e:
        raise NoTranscript(type(e).__name__) from e
    except CouldNotRetrieveTranscript as e:
        text = str(e)
        if "429" in text or "Too Many Requests" in text:
            raise Blocked("429 Too Many Requests") from e
        raise
    snippets = [(s.start, s.text) for s in fetched]
    return snippets, fetched.language_code, fetched.is_generated


def to_paragraphs(snippets):
    paras, start, words = [], None, []
    for s_start, text in snippets:
        text = " ".join(text.replace("\n", " ").split())
        if not text:
            continue
        if start is None:
            start = s_start
        elif s_start - start >= PARAGRAPH_SECONDS:
            paras.append((start, " ".join(words)))
            start, words = s_start, []
        words.append(text)
    if words:
        paras.append((start, " ".join(words)))
    return paras


def write_transcript(folder, channel, video, snippets, lang, generated):
    name = f"{video['date'] or 'nodate'}_{video['id']}.md"
    lines = [
        f"# {video['title']}",
        "",
        f"- video: https://www.youtube.com/watch?v={video['id']}",
        f"- channel: {channel['name']} ({channel['handle']})",
        f"- date: {video['date'] or 'unknown'} (approximate)",
        f"- duration: {fmt_duration(video['duration'])}",
        f"- transcript: {lang}, {'auto-generated' if generated else 'manual'}",
        "",
    ]
    lines += [f"[{fmt_time(start)}] {text}" for start, text in to_paragraphs(snippets)]
    (folder / name).write_text("\n".join(lines) + "\n", encoding="utf-8")
    return name


# ---------- state ----------

def load_index(folder):
    index = {}
    path = folder / "videos.jsonl"
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rec = json.loads(line)
                index[rec["id"]] = rec
    return index


def append_index(folder, rec):
    with open(folder / "videos.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


# ---------- git ----------

def git(*args, cwd):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")


def push(folder, channel, count):
    top = git("rev-parse", "--show-toplevel", cwd=ROOT)
    if top.returncode != 0:
        say("  (not inside a git clone, skipping upload)")
        return
    repo = top.stdout.strip()
    rel = folder.relative_to(Path(repo).resolve()).as_posix()
    git("add", rel, cwd=repo)
    if git("diff", "--cached", "--quiet", "--", rel, cwd=repo).returncode == 0:
        return
    ident = []
    if not git("config", "user.email", cwd=repo).stdout.strip():
        ident = ["-c", "user.name=yt-transcripts", "-c", "user.email=yt-transcripts@localhost"]
    msg = f"Transcripts: {channel['name']} ({count} videos)"
    res = git(*ident, "commit", "-m", msg, "--", rel, cwd=repo)
    if res.returncode != 0:
        say(f"  Upload skipped, commit failed: {res.stderr.strip() or res.stdout.strip()}")
        return
    git(*ident, "pull", "--rebase", "--autostash", cwd=repo)
    res = git("push", cwd=repo)
    if res.returncode == 0:
        say("  Uploaded to GitHub.")
    else:
        say(f"  Upload failed (will retry next time): {res.stderr.strip()[:300]}")


# ---------- main loop ----------

def download(args):
    from youtube_transcript_api import YouTubeTranscriptApi

    # With --limit on the newest videos there is no need to list the whole channel.
    max_items = 0
    if args.limit and not args.oldest:
        known = CHANNELS / slug_guess(args.channel) / "videos.jsonl"
        max_items = args.limit + 20 + (len(load_index(known.parent)) if known.exists() else 0)
    channel, videos = list_channel(args.channel, args.include_shorts, args.include_streams, max_items)
    slug = channel_slug(channel)
    folder = CHANNELS / slug
    folder.mkdir(parents=True, exist_ok=True)
    channel["updated"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    (folder / "channel.json").write_text(json.dumps(channel, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    index = load_index(folder)
    retry = {"error"} | ({"no_transcript"} if args.retry_missing else set())
    todo = [v for v in videos if v["id"] not in index or index[v["id"]]["status"] in retry]
    if args.oldest:
        todo.reverse()
    if args.limit:
        todo = todo[: args.limit]

    done_total = sum(1 for r in index.values() if r["status"] == "done")
    say(f"\nChannel: {channel['name']} ({channel['handle']}), {len(videos)} videos, "
        f"{done_total} already downloaded, {len(todo)} to do now.")
    if not todo:
        say("Nothing to do.")
        push(folder, channel, done_total)
        return

    avg_delay = (args.min_delay + args.max_delay) / 2
    eta = len(todo) * (avg_delay + 3) + (len(todo) // LONG_BREAK_EVERY) * sum(LONG_BREAK_SECONDS) / 2
    say(f"Estimated time: about {fmt_duration(eta)}. You can stop anytime with Ctrl+C; "
        f"the next run continues from where it stopped.\n")

    api = YouTubeTranscriptApi()
    since_push = errors_in_a_row = 0
    try:
        for i, video in enumerate(todo, 1):
            say(f"[{i}/{len(todo)}] {video['title'][:80]}")
            block_round = 0
            while True:
                try:
                    snippets, lang, generated = fetch_transcript(api, video["id"])
                    name = write_transcript(folder, channel, video, snippets, lang, generated)
                    rec = {**video, "status": "done", "file": name, "lang": lang, "generated": generated}
                    done_total += 1
                    errors_in_a_row = 0
                    say(f"  OK ({lang}{', auto' if generated else ''}, {len(snippets)} lines)")
                    break
                except NoTranscript as e:
                    rec = {**video, "status": "no_transcript", "reason": str(e)}
                    errors_in_a_row = 0
                    say(f"  No transcript ({e})")
                    break
                except Blocked as e:
                    if block_round >= len(BLOCK_WAITS_MINUTES):
                        raise
                    wait(BLOCK_WAITS_MINUTES[block_round] * 60, f"YouTube is limiting us ({e})")
                    block_round += 1
                    api = YouTubeTranscriptApi()
                except Exception as e:  # unknown failure: record it, retried on the next run
                    rec = {**video, "status": "error", "reason": f"{type(e).__name__}: {str(e)[:200]}"}
                    errors_in_a_row += 1
                    say(f"  Error: {rec['reason']}")
                    if errors_in_a_row >= MAX_ERRORS_IN_A_ROW:
                        append_index(folder, rec)
                        raise Blocked(f"{errors_in_a_row} errors in a row")
                    break
            append_index(folder, rec)
            since_push += 1
            if since_push >= PUSH_EVERY:
                push(folder, channel, done_total)
                since_push = 0
            if i == len(todo):
                break
            if i % LONG_BREAK_EVERY == 0:
                wait(random.uniform(*LONG_BREAK_SECONDS), "Long break")
            else:
                time.sleep(random.uniform(args.min_delay, args.max_delay))
    except Blocked as e:
        say(f"\nYouTube keeps blocking ({e}). Stopping for now. Everything so far is saved.")
        say("Run the same command again later (tomorrow is safest); it continues where it stopped.")
    except KeyboardInterrupt:
        say("\nStopped. Everything so far is saved; run the same command again to continue.")
    if not args.no_push:
        push(folder, channel, done_total)
    say(f"\nDone for now: {done_total} transcripts for {channel['name']} in {folder}")


def status():
    folders = sorted(p for p in CHANNELS.glob("*") if (p / "videos.jsonl").exists())
    if not folders:
        say("No channels yet.")
    for folder in folders:
        meta = json.loads((folder / "channel.json").read_text(encoding="utf-8"))
        counts = {}
        for rec in load_index(folder).values():
            counts[rec["status"]] = counts.get(rec["status"], 0) + 1
        say(f"{meta['name']} ({meta['handle']}): {counts.get('done', 0)} transcripts, "
            f"{counts.get('no_transcript', 0)} without transcript, {counts.get('error', 0)} errors. "
            f"Last run {meta.get('updated', '?')}")


def main():
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    p = argparse.ArgumentParser(description="Download all transcripts of a YouTube channel, slowly.")
    p.add_argument("channel", help="@handle, channel URL, or the word 'status'")
    p.add_argument("--limit", type=int, default=0, help="how many new videos to download in this run")
    p.add_argument("--oldest", action="store_true", help="start from the oldest videos")
    p.add_argument("--include-shorts", action="store_true")
    p.add_argument("--include-streams", action="store_true", help="also past live streams")
    p.add_argument("--min-delay", type=float, default=20, help="seconds, default 20")
    p.add_argument("--max-delay", type=float, default=60, help="seconds, default 60")
    p.add_argument("--retry-missing", action="store_true", help="try again videos that had no transcript")
    p.add_argument("--no-push", action="store_true", help="do not upload to GitHub")
    args = p.parse_args()
    if args.channel.lower() == "status":
        status()
    else:
        args.max_delay = max(args.max_delay, args.min_delay)
        download(args)


if __name__ == "__main__":
    main()
