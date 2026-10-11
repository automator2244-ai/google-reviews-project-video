#!/usr/bin/env bash
# Deploys the worker and makes sure its secrets exist.
# Needs CLOUDFLARE_API_TOKEN and ADMIN_PASSWORD in the environment. IP_SALT is generated once if missing.
set -euo pipefail
cd "$(dirname "$0")/.."
: "${CLOUDFLARE_API_TOKEN:?CLOUDFLARE_API_TOKEN is not set}"
: "${ADMIN_PASSWORD:?ADMIN_PASSWORD is not set}"
export CI=true # non-interactive: wrangler confirms prompts itself

npx tsc --noEmit
npx wrangler d1 migrations apply ezpath-loom-tracker --remote
npx wrangler deploy

SECRETS=$(npx wrangler secret list --format json 2>/dev/null || echo '[]')
printf '%s' "$ADMIN_PASSWORD" | npx wrangler secret put ADMIN_PASSWORD
if ! grep -q '"IP_SALT"' <<<"$SECRETS"; then
  openssl rand -hex 32 | tr -d '\n' | npx wrangler secret put IP_SALT
fi
echo "Deployed: https://go.ezpath-ai.com/admin"
