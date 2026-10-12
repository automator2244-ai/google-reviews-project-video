#!/usr/bin/env bash
# Smoke test against `npx wrangler dev` (local D1 + R2).
# Usage: scripts/smoke.sh <id of a recipient published with publish.sh --local> [base_url]
# Note: expires the local upload passes.
set -u
ID1="${1:?pass a recipient id published with: scripts/publish.sh --local ...}"
BASE="${2:-http://127.0.0.1:8787}"
CHROME="Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0 Mobile Safari/537.36"
FAILS=0

check() { # name expected actual
  if [ "$2" = "$3" ]; then echo "  ok   $1"; else echo "  FAIL $1 (expected '$2', got '$3')"; FAILS=$((FAILS + 1)); fi
}
status() { curl -s -o /dev/null -w '%{http_code}' "$@"; }
js() { node -pe "const d=JSON.parse(require('fs').readFileSync(0));$1"; }

echo "dashboard is open (no password, by choice)"
check "GET /admin" 200 "$(status "$BASE/admin")"
check "GET /admin/api/stats" 200 "$(status "$BASE/admin/api/stats")"
check "GET /admin/export.csv" 200 "$(status "$BASE/admin/export.csv")"
check "no login route" 404 "$(status -X POST "$BASE/admin/login")"
stats() { curl -s "$BASE/admin/api/stats"; }
row() { stats | js "JSON.stringify(d.rows.find(r=>r.id==='$ID1')||null)"; }
BEFORE=$(row | js 'd.clicks')

echo "video page"
PAGE=$(curl -s -A "$CHROME" "$BASE/v/$ID1")
check "page has the video" 1 "$(echo "$PAGE" | grep -c "<video id=\"v\" src=\"/m/$ID1.mp4\"")"
check "page has og:image for the preview" 1 "$(echo "$PAGE" | grep -c "og:image\" content=\"[^\"]*/m/$ID1.jpg\"")"
check "no cookies set on /v" "" "$(curl -s -o /dev/null -D - -A "$CHROME" "$BASE/v/$ID1" | grep -i '^set-cookie' || true)"
check "WhatsApp preview -> 200" 200 "$(status -A 'WhatsApp/2.24.20.80 A' "$BASE/v/$ID1")"
check "facebookexternalhit -> 200" 200 "$(status -A 'facebookexternalhit/1.1' "$BASE/v/$ID1")"
check "HEAD -> 200" 200 "$(status -I -A "$CHROME" "$BASE/v/$ID1")"
check "prefetch -> 200" 200 "$(status -A "$CHROME" -H 'Sec-Purpose: prefetch' "$BASE/v/$ID1")"

echo "media"
check "thumbnail" "200 image/jpeg" "$(curl -s -o /dev/null -w '%{http_code} %{content_type}' "$BASE/m/$ID1.jpg")"
check "video full" "200 video/mp4" "$(curl -s -o /dev/null -w '%{http_code} %{content_type}' "$BASE/m/$ID1.mp4")"
check "video range (iPhone)" "206 100" "$(curl -s -o /dev/null -w '%{http_code} %{size_download}' -H 'Range: bytes=0-99' "$BASE/m/$ID1.mp4")"
check "video range has Content-Range" 1 "$(curl -s -o /dev/null -D - -H 'Range: bytes=100-199' "$BASE/m/$ID1.mp4" | grep -ci '^content-range: bytes 100-199/')"
check "video suffix range" "206 50" "$(curl -s -o /dev/null -w '%{http_code} %{size_download}' -H 'Range: bytes=-50' "$BASE/m/$ID1.mp4")"
check "missing media -> 404" 404 "$(status "$BASE/m/nothere.mp4")"

echo "upload is locked"
TOK=$(cat "out/$ID1/token" 2>/dev/null || echo none)
up() { status -X PUT -H 'Content-Type: image/jpeg' --data-binary 'x' "$@"; }
check "no pass -> 401" 401 "$(up "$BASE/upload/$ID1.jpg")"
check "wrong pass -> 401" 401 "$(up -H 'Authorization: Bearer wrong' "$BASE/upload/$ID1.jpg")"
check "pass of another id -> 401" 401 "$(up -H "Authorization: Bearer $TOK" "$BASE/upload/someoneelse.jpg")"
check "GET /upload -> 404" 404 "$(status "$BASE/upload/$ID1.jpg")"
npx wrangler d1 execute ezpath-loom-tracker --local --command "UPDATE upload_tokens SET expires_at = 1" >/dev/null 2>&1
check "expired pass -> 401" 401 "$(up -H "Authorization: Bearer $TOK" "$BASE/upload/$ID1.jpg")"

echo "not found"
check "unknown id -> 404 page" 404 "$(status -A "$CHROME" "$BASE/v/doesnotexist")"
check "/v/a\$b" 404 "$(status "$BASE/v/a%24b")"
check "65 chars" 404 "$(status "$BASE/v/$(printf 'a%.0s' $(seq 65))")"
check "POST /v/id" 404 "$(status -X POST "$BASE/v/$ID1")"
check "unknown path" 404 "$(status "$BASE/whatever")"

echo "player events"
for p in 0 25 50; do check "event $p" 204 "$(status -A "$CHROME" -X POST -d "$p" "$BASE/e/$ID1")"; done
check "bad event value ignored" 204 "$(status -A "$CHROME" -X POST -d "33" "$BASE/e/$ID1")"
check "GET /e/id" 404 "$(status "$BASE/e/$ID1")"

sleep 1
echo "dashboard counts (bots excluded)"
check "two real visits counted (page + no-cookie check)" $((BEFORE + 2)) "$(row | js 'd.clicks')"
check "watched = 50%" 50 "$(row | js 'd.watched')"
curl -s -o /dev/null -A "$CHROME" "$BASE/v/$ID1"; sleep 1
check "one more visit counts once" $((BEFORE + 3)) "$(row | js 'd.clicks')"

echo "robots.txt"
check "blocks /admin and /v/" 2 "$(curl -s "$BASE/robots.txt" | grep -cE '^Disallow: /(admin|v/)$')"

echo
[ "$FAILS" -eq 0 ] && echo "ALL PASSED" || { echo "$FAILS FAILED"; exit 1; }
