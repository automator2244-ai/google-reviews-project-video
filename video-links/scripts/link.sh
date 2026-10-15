#!/usr/bin/env bash
# Prints the personal link for a recipient built by publish.sh.
# No ready WhatsApp message for now: Bnaya will decide on the wording first.
# Usage: scripts/link.sh <id> [base_url]
set -euo pipefail
cd "$(dirname "$0")/.."
ID="${1:?usage: scripts/link.sh <id> [base_url]}"
BASE="${2:-https://go.ezpath-ai.com}"
OUT="out/$ID"
NAME=$(cat "$OUT/name")
LINK="$BASE/v/$ID"
echo
echo "Done: $NAME"
echo "  Link:      $LINK"
