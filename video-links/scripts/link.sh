#!/usr/bin/env bash
# Prints the personal link and a ready WhatsApp link for a recipient built by publish.sh.
# Usage: scripts/link.sh <id> [base_url]
set -euo pipefail
cd "$(dirname "$0")/.."
ID="${1:?usage: scripts/link.sh <id> [base_url]}"
BASE="${2:-https://go.ezpath-ai.com}"
OUT="out/$ID"
NAME=$(cat "$OUT/name") PHONE=$(cat "$OUT/phone")
LINK="$BASE/v/$ID"
echo
echo "Done: $NAME"
echo "  Link:      $LINK"
if [ -n "$PHONE" ]; then
  MSG=$(node -e 'console.log(encodeURIComponent(process.argv[1]))' "היי $NAME, הכנתי לך סרטון קצר במיוחד בשבילך: $LINK")
  echo "  WhatsApp:  https://wa.me/$PHONE?text=$MSG"
fi
