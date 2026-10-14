#!/usr/bin/env bash
# One-time setup on an Android phone, inside the Termux app.
# Installs git, python and the GitHub CLI, logs in to GitHub, and downloads only
# the youtube-transcripts folder of the repo (not the videos in it).
set -e
REPO=automator2244-ai/google-reviews-project-video
DIR="$HOME/google-reviews-project-video"

echo "== 1/4 Installing git, python and gh"
pkg update -y
yes | pkg upgrade -y
pkg install -y git python gh

echo "== 2/4 GitHub login"
if ! gh auth status >/dev/null 2>&1; then
  echo "Copy the 8 character code shown below, then open github.com/login/device in the browser and paste it."
  gh auth login --hostname github.com --git-protocol https --web
fi
gh auth setup-git

echo "== 3/4 Downloading the tool"
if [ ! -d "$DIR" ]; then
  git clone --filter=blob:none --sparse "https://github.com/$REPO.git" "$DIR"
  git -C "$DIR" sparse-checkout set youtube-transcripts
fi

echo "== 4/4 Installing Python packages"
bash "$DIR/youtube-transcripts/yt.sh" --setup-only
grep -q "alias yt=" "$HOME/.bashrc" 2>/dev/null || \
  echo "alias yt='bash $DIR/youtube-transcripts/yt.sh'" >> "$HOME/.bashrc"

echo
echo "All set. Close Termux and open it again, then run for example:"
echo "  yt @channelname --limit 5"
