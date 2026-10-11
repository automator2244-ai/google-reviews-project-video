#!/usr/bin/env bash
# Uploads a video built by publish.sh, using its one-hour upload pass. Prints the personal link.
# Usage: scripts/upload.sh <id> [base_url]
set -euo pipefail
cd "$(dirname "$0")/.."
ID="${1:?usage: scripts/upload.sh <id> [base_url]}"
BASE="${2:-https://go.ezpath-ai.com}"
OUT="out/$ID"
TOKEN=$(cat "$OUT/token")

put() { # file type
  local code
  code=$(curl -sS -o /dev/null -w '%{http_code}' -X PUT -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: $2" --data-binary "@$OUT/$1" "$BASE/upload/$ID.${1##*.}")
  [ "$code" = 204 ] || { echo "Upload of $1 failed (HTTP $code). Was register.sql run, and within the last hour?" >&2; exit 1; }
}

echo "Uploading..."
put thumb.jpg image/jpeg
put video.mp4 video/mp4 # last: this one makes the page live

NAME=$(cat "$OUT/name") PHONE=$(cat "$OUT/phone")
LINK="$BASE/v/$ID"
echo
echo "Done: $NAME"
echo "  Link:      $LINK"
if [ -n "$PHONE" ]; then
  MSG=$(node -e 'console.log(encodeURIComponent(process.argv[1]))' "היי $NAME, הכנתי לך סרטון קצר במיוחד בשבילך: $LINK")
  echo "  WhatsApp:  https://wa.me/$PHONE?text=$MSG"
fi
