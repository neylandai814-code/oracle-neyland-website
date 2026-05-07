#!/usr/bin/env bash
# Oracle Live Site — deploy script (v3: git-mode + token-mode + interactive).
#
# Three deploy modes (auto-detected; override with flags below):
#   1. GIT MODE  — push to GitHub; Vercel auto-deploys via Git integration webhook.
#                  Detected when ./.git/ exists AND a remote is configured.
#                  PREFERRED — no Vercel CLI or token needed in the runtime env.
#   2. TOKEN MODE — local vercel CLI + ./.vercel-token (or VERCEL_TOKEN env).
#                   Detected when ./.vercel-token (or env var) is present.
#   3. INTERACTIVE MODE — relies on `vercel login` state on the host machine.
#                          Used when neither of the above is configured.
#
# Setup helpers:
#   ./setup_git_deploy.sh        # one-time setup for GIT MODE (recommended)
#   ./setup_token_deploy.sh      # one-time setup for TOKEN MODE
#
# Usage:
#   ./deploy.sh                  # build + deploy via auto-detected mode
#   ./deploy.sh --skip-build     # deploy whatever's currently on disk
#   ./deploy.sh --preview        # preview deploy (only meaningful in TOKEN/INTERACTIVE mode)
#   ./deploy.sh --git-mode       # force git mode
#   ./deploy.sh --vercel-mode    # force vercel-CLI mode

set -euo pipefail
cd "$(dirname "$0")"

SKIP_BUILD=0
PREVIEW=0
FORCE_MODE=""
for arg in "$@"; do
  case "$arg" in
    --skip-build)  SKIP_BUILD=1 ;;
    --preview)     PREVIEW=1 ;;
    --git-mode)    FORCE_MODE="git" ;;
    --vercel-mode) FORCE_MODE="vercel" ;;
    -h|--help)     sed -n '1,30p' "$0"; exit 0 ;;
  esac
done

# ----------------------------------------------------------------------------
# Step 1: Build (unless --skip-build)
# ----------------------------------------------------------------------------
if [[ $SKIP_BUILD -eq 0 ]]; then
  echo "==> Building site (build_site.py)"
  REPORTS_ROOT="${ORACLE_REPORTS_ROOT:-/Users/neylandai/Documents/Oracle Reports}"
  if [[ ! -d "$REPORTS_ROOT" ]]; then
    SANDBOX_ROOT="/sessions/admiring-charming-pascal/mnt/Oracle Reports"
    if [[ -d "$SANDBOX_ROOT" ]]; then REPORTS_ROOT="$SANDBOX_ROOT"; fi
  fi
  python3 build_site.py "$REPORTS_ROOT"
fi

# ----------------------------------------------------------------------------
# Step 2: Detect mode
# ----------------------------------------------------------------------------
GIT_OK=0
if [[ -d ".git" ]]; then
  if git -C . config --get remote.origin.url >/dev/null 2>&1; then
    GIT_OK=1
  fi
fi

TOKEN=""
TOKEN_SOURCE=""
if [[ -n "${VERCEL_TOKEN:-}" ]]; then
  TOKEN="$VERCEL_TOKEN"; TOKEN_SOURCE="VERCEL_TOKEN env"
elif [[ -f ".vercel-token" ]]; then
  TOKEN="$(tr -d '[:space:]' < .vercel-token)"; TOKEN_SOURCE=".vercel-token file"
fi

VERCEL_CLI=""
if [[ -x "./node_modules/.bin/vercel" ]]; then
  VERCEL_CLI="./node_modules/.bin/vercel"
elif command -v vercel >/dev/null 2>&1; then
  VERCEL_CLI="$(command -v vercel)"
fi

# Decide
MODE=""
if [[ -n "$FORCE_MODE" ]]; then
  MODE="$FORCE_MODE"
elif [[ $GIT_OK -eq 1 ]]; then
  MODE="git"
elif [[ -n "$VERCEL_CLI" ]]; then
  MODE="vercel"
else
  echo "ERROR: no deploy mode available. Need either:" >&2
  echo "  - git remote configured (run ./setup_git_deploy.sh), OR" >&2
  echo "  - vercel CLI + token (run ./setup_token_deploy.sh), OR" >&2
  echo "  - global vercel CLI + interactive login on this host" >&2
  exit 1
fi
echo "==> Mode: $MODE"

# ----------------------------------------------------------------------------
# Step 3a: GIT MODE
# ----------------------------------------------------------------------------
if [[ "$MODE" == "git" ]]; then
  REMOTE_URL="$(git -C . config --get remote.origin.url)"
  echo "==> Remote: $REMOTE_URL"
  BRANCH="$(git -C . rev-parse --abbrev-ref HEAD 2>/dev/null || echo main)"
  echo "==> Branch: $BRANCH"

  # Stage everything that should be tracked (gitignore filters secrets / build artifacts)
  git add -A

  if git -C . diff --cached --quiet; then
    echo "==> No changes to commit; skipping push."
  else
    DATE_STAMP="$(date +%Y-%m-%d)"
    git -C . -c user.name="Oracle Bot" -c user.email="oracle@neylanddev.local" \
      commit -m "Oracle run $DATE_STAMP" --no-verify
    echo "==> Pushing to origin/$BRANCH"
    git -C . push origin "$BRANCH"
    echo "==> Push complete. Vercel will deploy automatically via Git integration."
  fi
  echo
  echo "Done. Check Vercel dashboard for the production URL."
  exit 0
fi

# ----------------------------------------------------------------------------
# Step 3b: VERCEL CLI MODE (token or interactive)
# ----------------------------------------------------------------------------
if [[ -z "$VERCEL_CLI" ]]; then
  echo "ERROR: vercel CLI not found." >&2
  echo "  Install: cd $(pwd) && npm install vercel" >&2
  exit 1
fi
if [[ ! -f ".vercel/project.json" ]]; then
  echo "ERROR: .vercel/project.json missing. Run on host: vercel link" >&2
  exit 1
fi

DEPLOY_ARGS=()
[[ $PREVIEW -eq 0 ]] && DEPLOY_ARGS+=(--prod)
if [[ -n "$TOKEN" ]]; then
  echo "==> Auth: $TOKEN_SOURCE (unattended)"
  DEPLOY_ARGS+=(--token "$TOKEN" --yes)
else
  echo "==> Auth: interactive vercel login state on host"
fi
echo "==> Vercel CLI: $VERCEL_CLI"

if [[ $PREVIEW -eq 1 ]]; then
  echo "==> Deploying preview"
else
  echo "==> Deploying to production"
fi

DEPLOY_URL="$("$VERCEL_CLI" deploy "${DEPLOY_ARGS[@]}" 2>&1 | tee /dev/stderr | grep -oE 'https://[^[:space:]]+\.vercel\.app' | tail -1 || true)"

echo
if [[ -n "$DEPLOY_URL" ]]; then
  echo "Done. Live at: $DEPLOY_URL"
else
  echo "Done. Check Vercel dashboard for the production URL."
fi
