#!/usr/bin/env bash
# Runs the transcript downloader on Android (Termux), Linux or Mac.
# First run sets up the Python packages by itself.
HERE="$(cd "$(dirname "$0")" && pwd)"
PY="$HERE/.venv/bin/python"

if [ ! -x "$PY" ]; then
  echo "First run: setting up, this takes a minute..."
  python3 -m venv "$HERE/.venv" || exit 1
fi

# Keep yt-dlp and the transcript library up to date, YouTube changes often.
"$PY" -m pip install -q --disable-pip-version-check -U -r "$HERE/requirements.txt" || exit 1
if [ "$1" = "--setup-only" ]; then
  echo "Setup done."
  exit 0
fi

# Get the latest version of the tool (ignored when offline).
git -C "$HERE" pull -q --rebase --autostash 2>/dev/null

# On Android: keep running while the screen is off.
if command -v termux-wake-lock >/dev/null; then
  termux-wake-lock
  trap 'termux-wake-unlock' EXIT
fi

"$PY" "$HERE/yt_transcripts.py" "$@"
