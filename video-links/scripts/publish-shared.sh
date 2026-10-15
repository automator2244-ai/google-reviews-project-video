#!/usr/bin/env bash
# Uploads one video that many links share (recipients with video_key = KEY, see publish.sh --shared).
# Step 1 builds out/shared-KEY/ (web encode + poster) and the SQL for a one-hour upload pass.
# Step 2, after that SQL ran on D1, uploads. Use a new KEY for every new version (unified-v2, ...):
# browsers cache a video for a day.
# Usage: scripts/publish-shared.sh KEY FILE [--thumb-at SEC] [--local]
#        scripts/publish-shared.sh KEY --upload
set -euo pipefail
cd "$(dirname "$0")/.."

DB="ezpath-loom-tracker"
KEY="${1:?usage: scripts/publish-shared.sh KEY FILE [--thumb-at SEC] [--local] | KEY --upload}"
FILE="${2:?usage: scripts/publish-shared.sh KEY FILE [--thumb-at SEC] [--local] | KEY --upload}"
shift 2
[[ "$KEY" =~ ^[A-Za-z0-9_-]{1,64}$ ]] || { echo "Invalid key" >&2; exit 1; }
OUT="out/shared-$KEY"

upload() { # base
  local f code token
  token=$(cat "$OUT/token")
  for f in thumb.jpg video.mp4; do
    code=$(curl -sS -o /dev/null -w '%{http_code}' -X PUT -H "Authorization: Bearer $token" \
      -H "Content-Type: $([ "$f" = video.mp4 ] && echo video/mp4 || echo image/jpeg)" \
      --data-binary "@$OUT/$f" "$1/upload-shared/$KEY.${f##*.}")
    [ "$code" = 204 ] || { echo "Upload of $f failed (HTTP $code). Was register.sql run, and within the last hour?" >&2; exit 1; }
  done
  echo "Uploaded: $1/s/$KEY.mp4"
}

if [ "$FILE" = --upload ]; then
  upload "https://go.ezpath-ai.com"
  exit 0
fi

THUMB_AT=1 LOCAL=0
while [ $# -gt 0 ]; do
  case "$1" in
    --thumb-at) THUMB_AT="$2"; shift 2 ;;
    --local) LOCAL=1; shift ;;
    *) echo "Unknown option: $1" >&2; exit 1 ;;
  esac
done
[ -f "$FILE" ] || { echo "File not found: $FILE" >&2; exit 1; }

mkdir -p "$OUT"
echo "Encoding video..."
ffmpeg -hide_banner -loglevel error -y -i "$FILE" -vf "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,setsar=1" \
  -c:v libx264 -preset medium -crf 24 -profile:v high -pix_fmt yuv420p -c:a aac -b:a 128k -movflags +faststart "$OUT/video.mp4"
ffmpeg -hide_banner -loglevel error -y -ss "$THUMB_AT" -i "$OUT/video.mp4" -frames:v 1 -vf scale=540:960 -q:v 4 "$OUT/thumb.jpg"
echo "  $(du -h "$OUT/video.mp4" | cut -f1)"

TOKEN=$(openssl rand -hex 32)
printf '%s' "$TOKEN" > "$OUT/token"
cat > "$OUT/register.sql" <<SQL
INSERT INTO upload_tokens (token_hash, recipient_id, expires_at)
VALUES ('$(printf '%s' "$TOKEN" | sha256sum | cut -d' ' -f1)', 'shared:$KEY', $(( ($(date +%s) + 3600) * 1000 )));
SQL

if [ "$LOCAL" = 1 ]; then
  log=$(npx wrangler d1 execute "$DB" --local --yes --file "$OUT/register.sql" 2>&1) || { echo "$log" >&2; exit 1; }
  upload "http://127.0.0.1:8787"
  exit 0
fi

echo "Built: $OUT"
echo "Next: run $OUT/register.sql on D1 database $DB (Cloudflare connector), then: scripts/publish-shared.sh $KEY --upload"
