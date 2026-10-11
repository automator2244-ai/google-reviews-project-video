#!/usr/bin/env bash
# Smoke test against `npx wrangler dev` (local D1).
# Usage: ADMIN_PASSWORD=... LOOM_URL=... scripts/smoke.sh [base_url]
set -u
BASE="${1:-http://127.0.0.1:8787}"
PASS="${ADMIN_PASSWORD:?set ADMIN_PASSWORD}"
LOOM="${LOOM_URL:?set LOOM_URL}"
CHROME="Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0 Mobile Safari/537.36"
FAILS=0

check() { # name expected actual
  if [ "$2" = "$3" ]; then echo "  ok   $1"; else echo "  FAIL $1 (expected '$2', got '$3')"; FAILS=$((FAILS + 1)); fi
}
status() { curl -s -o /dev/null -w '%{http_code}' "$@"; }
location() { curl -s -o /dev/null -w '%{redirect_url}' "$@"; }

echo "admin is locked without a session"
check "GET /admin -> login page" 401 "$(status "$BASE/admin")"
check "GET /admin/api/stats" 401 "$(status "$BASE/admin/api/stats")"
check "GET /admin/export.csv" 401 "$(status "$BASE/admin/export.csv")"
check "POST /admin/api/recipients" 401 "$(status -X POST -H 'content-type: application/json' -d '{"text":"x"}' "$BASE/admin/api/recipients")"
check "forged cookie" 401 "$(status -H 'cookie: admin_session=9999999999999.deadbeef' "$BASE/admin/api/stats")"

echo "login"
COOKIE=$(curl -s -o /dev/null -D - --data-urlencode "password=$PASS" "$BASE/admin/login" | tr -d '\r' | sed -n 's/^[Ss]et-[Cc]ookie: \([^;]*\).*/\1/p')
[ -n "$COOKIE" ] && echo "  ok   got session cookie" || { echo "  FAIL no session cookie"; exit 1; }
check "GET /admin with session" 200 "$(status -H "cookie: $COOKIE" "$BASE/admin")"

echo "create recipients"
CREATED=$(curl -s -H "cookie: $COOKIE" -H 'content-type: application/json' \
  -d '{"text":"בדיקה אחת, 050-123-4567\n052 7654321\tבדיקה שתיים\nבלי טלפון"}' "$BASE/admin/api/recipients")
ID1=$(echo "$CREATED" | node -pe 'JSON.parse(require("fs").readFileSync(0)).rows[0].id')
ID2=$(echo "$CREATED" | node -pe 'JSON.parse(require("fs").readFileSync(0)).rows[1].id')
check "3 rows created" 3 "$(echo "$CREATED" | node -pe 'JSON.parse(require("fs").readFileSync(0)).rows.length')"
check "phone normalized" 972501234567 "$(echo "$CREATED" | node -pe 'JSON.parse(require("fs").readFileSync(0)).rows[0].phone')"
check "phone,name order swapped" "בדיקה שתיים|972527654321" "$(echo "$CREATED" | node -pe 'const r=JSON.parse(require("fs").readFileSync(0)).rows[1]; r.name+"|"+r.phone')"
check "id is 8 random chars" 1 "$(echo "$ID1" | grep -cE '^[a-z2-9]{8}$')"

echo "clicks"
check "real click -> 302 to Loom" "$LOOM" "$(location -A "$CHROME" "$BASE/v/$ID1")"
check "WhatsApp preview -> 302" "$LOOM" "$(location -A 'WhatsApp/2.24.20.80 A' "$BASE/v/$ID1")"
check "facebookexternalhit -> 302" "$LOOM" "$(location -A 'facebookexternalhit/1.1 (+http://www.facebook.com/externalhit_uatext.php)' "$BASE/v/$ID1")"
check "HEAD -> 302" 302 "$(status -I -A "$CHROME" "$BASE/v/$ID1")"
check "prefetch -> 302" "$LOOM" "$(location -A "$CHROME" -H 'Sec-Purpose: prefetch' "$BASE/v/$ID1")"
check "curl default UA -> 302" "$LOOM" "$(location "$BASE/v/$ID1")"
check "unknown valid id -> same 302" "$LOOM" "$(location -A "$CHROME" "$BASE/v/doesnotexist")"
check "no cookies set on /v" "" "$(curl -s -o /dev/null -D - -A "$CHROME" "$BASE/v/$ID1" | grep -i '^set-cookie' || true)"

echo "invalid ids -> 404"
check "/v/a\$b" 404 "$(status "$BASE/v/a%24b")"
check "/v/ (empty)" 404 "$(status "$BASE/v/")"
check "65 chars" 404 "$(status "$BASE/v/$(printf 'a%.0s' $(seq 65))")"
check "POST /v/id" 404 "$(status -X POST "$BASE/v/$ID1")"
check "unknown path" 404 "$(status "$BASE/whatever")"

sleep 1
echo "dashboard counts (bots excluded)"
STATS=$(curl -s -H "cookie: $COOKIE" "$BASE/admin/api/stats")
count() { echo "$STATS" | node -pe "(JSON.parse(require('fs').readFileSync(0)).rows.find(r=>r.id==='$1')||{}).clicks"; }
check "recipient 1: 2 real clicks (first + no-cookie check)" 2 "$(count "$ID1")"
check "recipient 2: 0 clicks" 0 "$(count "$ID2")"
check "recipient 2 not in list as clicked" null "$(echo "$STATS" | node -pe "JSON.parse(require('fs').readFileSync(0)).rows.find(r=>r.id==='$ID2').last_click")"
curl -s -o /dev/null -A "$CHROME" "$BASE/v/$ID1"; sleep 1
STATS=$(curl -s -H "cookie: $COOKIE" "$BASE/admin/api/stats")
check "one more real click counts once" 3 "$(count "$ID1")"
check "CSV export" 200 "$(status -H "cookie: $COOKIE" "$BASE/admin/export.csv")"

echo "robots.txt"
check "blocks /admin and /v/" 2 "$(curl -s "$BASE/robots.txt" | grep -cE '^Disallow: /(admin|v/)$')"

echo "login rate limit"
for i in 1 2 3 4 5; do check "wrong password $i" 401 "$(status --data-urlencode 'password=wrong' "$BASE/admin/login")"; done
check "6th attempt blocked" 429 "$(status --data-urlencode 'password=wrong' "$BASE/admin/login")"
check "even the right password is blocked" 429 "$(status --data-urlencode "password=$PASS" "$BASE/admin/login")"

echo
[ "$FAILS" -eq 0 ] && echo "ALL PASSED" || { echo "$FAILS FAILED"; exit 1; }
