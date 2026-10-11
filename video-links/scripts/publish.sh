#!/usr/bin/env bash
# Builds a personal video, uploads it to R2 and creates the recipient. Prints the personal link.
set -euo pipefail
cd "$(dirname "$0")/.."

BASE_URL="https://go.ezpath-ai.com"
BUCKET="ezpath-videos"
DB="ezpath-loom-tracker"
TEMPLATE="../google-reviews-demo/out/google-reviews-demo-full.mp4"
W=720 H=1280

usage() {
  cat <<'EOF'
Usage: scripts/publish.sh --name "שם העסק" [--phone 050...] (--personal clip.mp4 | --video ready.mp4) [options]
  --personal FILE   personal recording, merged with the template
  --video FILE      a finished video, uploaded as-is (only re-encoded for the web)
  --template FILE   template video (default: ../google-reviews-demo/out/google-reviews-demo-full.mp4)
  --personal-last   put the personal part after the template (default: before it)
  --note TEXT       free-text note (shows up in the CSV export)
  --id ID           replace the video of an existing recipient
  --local           upload to the local `wrangler dev` storage instead of Cloudflare
EOF
  exit 1
}

NAME="" PHONE="" NOTE="" PERSONAL="" VIDEO="" ID="" PERSONAL_LAST=0 WHERE="--remote"
while [ $# -gt 0 ]; do
  case "$1" in
    --name) NAME="$2"; shift 2 ;;
    --phone) PHONE="$2"; shift 2 ;;
    --note) NOTE="$2"; shift 2 ;;
    --personal) PERSONAL="$2"; shift 2 ;;
    --video) VIDEO="$2"; shift 2 ;;
    --template) TEMPLATE="$2"; shift 2 ;;
    --id) ID="$2"; shift 2 ;;
    --personal-last) PERSONAL_LAST=1; shift ;;
    --local) WHERE="--local"; BASE_URL="http://127.0.0.1:8787"; shift ;;
    *) usage ;;
  esac
done
[ -n "$NAME" ] || usage
[ -n "$PERSONAL" ] || [ -n "$VIDEO" ] || usage
for f in "$PERSONAL" "$VIDEO"; do [ -z "$f" ] || [ -f "$f" ] || { echo "File not found: $f" >&2; exit 1; }; done
[ -n "$VIDEO" ] || [ -f "$TEMPLATE" ] || { echo "Template not found: $TEMPLATE" >&2; exit 1; }

# 050-123-4567 / +972 50... / 00972... -> 972501234567
if [ -n "$PHONE" ]; then
  PHONE=$(printf '%s' "$PHONE" | tr -cd '0-9')
  case "$PHONE" in 00*) PHONE=${PHONE:2} ;; 0*) PHONE=972${PHONE:1} ;; esac
  [ ${#PHONE} -ge 9 ] && [ ${#PHONE} -le 15 ] || { echo "Invalid phone number" >&2; exit 1; }
fi

if [ -z "$ID" ]; then
  ID=$(node -e "const a='abcdefghijkmnpqrstuvwxyz23456789';console.log([...crypto.getRandomValues(new Uint8Array(8))].map(b=>a[b&31]).join(''))")
fi
[[ "$ID" =~ ^[A-Za-z0-9_-]{1,64}$ ]] || { echo "Invalid id" >&2; exit 1; }

OUT="out/$ID"
mkdir -p "$OUT"

duration() { ffprobe -v error -show_entries format=duration -of csv=p=0 "$1"; }
has_audio() { [ -n "$(ffprobe -v error -select_streams a -show_entries stream=index -of csv=p=0 "$1")" ]; }

# Each segment: fit into 720x1280 over a blurred fill (works for vertical or horizontal recordings),
# loudness-normalized audio (voice at -16 LUFS, template music a bit lower), silence if there is no audio.
INPUTS=() NI=0 FILTER="" CONCAT="" N=0
add_segment() { # file lufs
  local i=$NI
  INPUTS+=(-i "$1"); NI=$((NI + 1))
  FILTER+="[$i:v]split[bg$N][fg$N];"
  FILTER+="[bg$N]scale=$W:$H:force_original_aspect_ratio=increase,crop=$W:$H,gblur=sigma=30,eq=brightness=-0.15[b$N];"
  FILTER+="[fg$N]scale=$W:$H:force_original_aspect_ratio=decrease[f$N];"
  FILTER+="[b$N][f$N]overlay=(W-w)/2:(H-h)/2,setsar=1,fps=30,format=yuv420p[v$N];"
  if has_audio "$1"; then
    FILTER+="[$i:a]aformat=sample_fmts=fltp:channel_layouts=stereo,loudnorm=I=$2:TP=-1.5:LRA=11,aresample=48000[a$N];"
  else
    INPUTS+=(-f lavfi -t "$(duration "$1")" -i anullsrc=r=48000:cl=stereo); NI=$((NI + 1))
    FILTER+="[$((NI - 1)):a]anull[a$N];"
  fi
  CONCAT+="[v$N][a$N]"
  N=$((N + 1))
}

THUMB_AT=1
if [ -n "$VIDEO" ]; then
  add_segment "$VIDEO" -16
elif [ "$PERSONAL_LAST" = 1 ]; then
  add_segment "$TEMPLATE" -20
  add_segment "$PERSONAL" -16
  THUMB_AT=$(awk "BEGIN{print $(duration "$TEMPLATE") + 1}")
else
  add_segment "$PERSONAL" -16
  add_segment "$TEMPLATE" -20
fi
FILTER+="${CONCAT}concat=n=$N:v=1:a=1[v][a]"

echo "Encoding video..."
ffmpeg -hide_banner -loglevel error -y "${INPUTS[@]}" -filter_complex "$FILTER" -map "[v]" -map "[a]" \
  -c:v libx264 -preset medium -crf 24 -profile:v high -pix_fmt yuv420p \
  -c:a aac -b:a 128k -movflags +faststart "$OUT/video.mp4"
ffmpeg -hide_banner -loglevel error -y -ss "$THUMB_AT" -i "$OUT/video.mp4" -frames:v 1 -vf scale=540:960 -q:v 4 "$OUT/thumb.jpg"
echo "  $(du -h "$OUT/video.mp4" | cut -f1), $(printf '%.0f' "$(duration "$OUT/video.mp4")") seconds"

# Quiet on success, full output on failure.
wrangler() { local log; log=$(npx wrangler "$@" 2>&1) || { echo "$log" >&2; exit 1; }; }

echo "Uploading..."
wrangler r2 object put "$BUCKET/videos/$ID.mp4" --file "$OUT/video.mp4" --content-type video/mp4 "$WHERE"
wrangler r2 object put "$BUCKET/videos/$ID.jpg" --file "$OUT/thumb.jpg" --content-type image/jpeg "$WHERE"

q() { if [ -n "$1" ]; then printf "'%s'" "${1//\'/\'\'}"; else printf 'NULL'; fi; }
NOW=$(date -u +%Y-%m-%dT%H:%M:%S.000Z)
cat > "$OUT/recipient.sql" <<SQL
INSERT INTO recipients (id, name, phone, note, created_at, video_at)
VALUES ($(q "$ID"), $(q "$NAME"), $(q "$PHONE"), $(q "$NOTE"), '$NOW', '$NOW')
ON CONFLICT(id) DO UPDATE SET video_at = excluded.video_at;
SQL
wrangler d1 execute "$DB" "$WHERE" --yes --file "$OUT/recipient.sql"

LINK="$BASE_URL/v/$ID"
echo
echo "Done: $NAME"
echo "  Link:      $LINK"
if [ -n "$PHONE" ]; then
  MSG=$(node -e 'console.log(encodeURIComponent(process.argv[1]))' "היי $NAME, הכנתי לך סרטון קצר במיוחד בשבילך: $LINK")
  echo "  WhatsApp:  https://wa.me/$PHONE?text=$MSG"
fi
