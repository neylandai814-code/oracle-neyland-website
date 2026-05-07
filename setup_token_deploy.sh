#!/usr/bin/env bash
# Oracle Live Site — one-time setup for unattended (token-based) Vercel deploys.
#
# What this does:
#   1. Installs the vercel CLI locally into ./node_modules so the scheduled-task
#      sandbox can find it (the sandbox can't install packages itself).
#   2. Writes the Vercel access token you provide into ./.vercel-token (mode 600).
#      This file is gitignored.
#   3. Runs a test deployment to confirm everything works.
#
# Run this from your Mac (the sandbox can't install npm packages).
#
# Usage:
#   ./setup_token_deploy.sh                  # prompts for token interactively
#   VERCEL_TOKEN=xxx ./setup_token_deploy.sh # picks up token from env

set -euo pipefail
cd "$(dirname "$0")"

echo "=========================================="
echo "Oracle — Token-based Vercel Deploy Setup"
echo "=========================================="
echo

# Step 1: get token
if [[ -z "${VERCEL_TOKEN:-}" ]]; then
  echo "Step 1/3: Generate a Vercel access token"
  echo "  - Open https://vercel.com/account/tokens"
  echo "  - Click 'Create Token', name it 'oracle-scheduled-deploy'"
  echo "  - Scope: 'Full Account' (or scoped to the oracle-neyland project if available)"
  echo "  - Copy the token shown (you won't see it again)"
  echo
  read -r -s -p "Paste token here (input hidden): " TOKEN_INPUT
  echo
  VERCEL_TOKEN="$TOKEN_INPUT"
fi
if [[ -z "$VERCEL_TOKEN" ]]; then
  echo "ERROR: empty token. Aborting." >&2
  exit 1
fi

echo "$VERCEL_TOKEN" > .vercel-token
chmod 600 .vercel-token
echo "  ✓ Wrote .vercel-token (mode 600, gitignored)"
echo

# Step 2: install vercel locally
echo "Step 2/3: Install vercel CLI locally (./node_modules/.bin/vercel)"
if [[ -x "./node_modules/.bin/vercel" ]]; then
  echo "  ✓ Already installed at ./node_modules/.bin/vercel"
else
  if ! command -v npm >/dev/null 2>&1; then
    echo "ERROR: npm not found. Install Node.js first: https://nodejs.org" >&2
    exit 1
  fi
  npm install vercel
  echo "  ✓ Installed via npm"
fi
echo

# Step 3: test deploy
echo "Step 3/3: Test unattended deployment"
read -r -p "Run a test production deploy now? [y/N] " ANS
case "$ANS" in y|Y|yes|YES|Yes) DO_TEST=1;; *) DO_TEST=0;; esac
if [[ $DO_TEST -eq 1 ]]; then
  ./deploy.sh --skip-build
  echo
  echo "  ✓ Setup complete. The scheduled task can now deploy itself."
  echo
  echo "Next steps for the scheduled task:"
  echo "  - The scheduled task already invokes ./deploy.sh from the SKILL.md."
  echo "  - With ./.vercel-token in place + ./node_modules/.bin/vercel installed,"
  echo "    future runs will auto-deploy without any further intervention."
else
  echo
  echo "  ✓ Token + CLI installed. Test skipped."
  echo "  Run ./deploy.sh manually whenever you're ready to verify."
fi
