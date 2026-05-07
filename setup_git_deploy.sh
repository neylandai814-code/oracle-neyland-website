#!/usr/bin/env bash
# Oracle Live Site — one-time setup for GIT MODE deploys (recommended).
#
# Architecture:
#   Scheduled task → git push to GitHub → Vercel webhook → auto-deploy.
#
# This eliminates the need for a Vercel token on disk or vercel CLI in the
# scheduled-task sandbox; only `git push` is required, and Vercel pulls from
# GitHub on its own.
#
# Run this from your Mac (the sandbox can't create GitHub repos for you).
#
# Usage:
#   ./setup_git_deploy.sh

set -euo pipefail
cd "$(dirname "$0")"

echo "============================================================"
echo "Oracle — Git-based Vercel Deploy Setup (option 3)"
echo "============================================================"
echo
echo "Before continuing, make sure you've done these in your browser:"
echo
echo "  A) CREATE A NEW GITHUB REPO (private):"
echo "       - Go to https://github.com/new"
echo "       - Name: oracle-neyland-website (or anything you like)"
echo "       - Visibility: Private"
echo "       - Do NOT add README/license/.gitignore (we already have everything locally)"
echo "       - Click 'Create repository'"
echo
echo "  B) GENERATE A FINE-GRAINED PERSONAL ACCESS TOKEN:"
echo "       - Go to https://github.com/settings/personal-access-tokens/new"
echo "       - Token name: oracle-scheduled-deploy"
echo "       - Resource owner: your account"
echo "       - Repository access: 'Only select repositories' → choose the new repo"
echo "       - Permissions → Repository → 'Contents' → Read and Write"
echo "       - Click 'Generate token'"
echo "       - Copy the token (you won't see it again)"
echo
echo "  C) CONNECT THE NEW REPO TO YOUR VERCEL PROJECT:"
echo "       - Open https://vercel.com → oracle-neyland project → Settings → Git"
echo "       - Click 'Connect Git Repository' → GitHub → select the new repo"
echo "       - Production Branch: main"
echo "       - Save."
echo
read -r -p "Have you done A, B, and C? [y/N] " READY
case "$READY" in
  y|Y|yes|YES|Yes) ;;
  *) echo "Run this again once you've done all three. Aborting."; exit 0 ;;
esac

# Step 1: collect inputs
echo
echo "Step 1/4: Collect repo info"
read -r -p "  GitHub username: " GH_USER
read -r -p "  Repo name (e.g. oracle-neyland-website): " GH_REPO
read -r -s -p "  PAT (input hidden): " GH_PAT
echo
if [[ -z "$GH_USER" || -z "$GH_REPO" || -z "$GH_PAT" ]]; then
  echo "ERROR: all three are required." >&2; exit 1
fi

REMOTE_URL_HTTPS="https://github.com/${GH_USER}/${GH_REPO}.git"
REMOTE_URL_AUTH="https://${GH_USER}:${GH_PAT}@github.com/${GH_USER}/${GH_REPO}.git"

# Step 2: write PAT to credentials file (mode 600, gitignored)
# Note: git config --local must wait until after `git init` (Step 3).
echo
echo "Step 2/4: Write credentials file"
echo "https://${GH_USER}:${GH_PAT}@github.com" > .git-credentials
chmod 600 .git-credentials
echo "  ✓ Credentials stored at ./.git-credentials (mode 600, gitignored)"

# Make sure .git-credentials is in .gitignore (so we never push the PAT itself)
if ! grep -q "^\.git-credentials$" .gitignore 2>/dev/null; then
  echo ".git-credentials" >> .gitignore
fi

# Step 3: init repo (idempotent), connect remote, configure credential helper
echo
echo "Step 3/4: Initialize repo + connect remote + wire credentials"
if [[ ! -d ".git" ]]; then
  # Older git (<2.28) doesn't support `git init -b main`; fall back gracefully.
  git init >/dev/null 2>&1
  git symbolic-ref HEAD refs/heads/main 2>/dev/null || git checkout -b main 2>/dev/null || true
  echo "  ✓ git init (default branch: main)"
else
  echo "  ✓ already a git repo"
fi

# Now that .git exists, --local works
git config credential.helper "store --file=$(pwd)/.git-credentials"
echo "  ✓ credential.helper -> store --file=./.git-credentials"

if git remote get-url origin >/dev/null 2>&1; then
  git remote set-url origin "$REMOTE_URL_HTTPS"
  echo "  ✓ origin remote updated to $REMOTE_URL_HTTPS"
else
  git remote add origin "$REMOTE_URL_HTTPS"
  echo "  ✓ origin remote added: $REMOTE_URL_HTTPS"
fi

# Set Oracle Bot identity locally so scheduled-task pushes don't require
# a global git user.name/user.email.
git config user.name "Oracle Bot"
git config user.email "oracle@neylanddev.local"

# Step 4: first commit + push
echo
echo "Step 4/4: First commit + push"
git add -A
if git diff --cached --quiet; then
  echo "  (nothing to commit — already committed)"
else
  git commit -m "Initial Oracle live-site commit"
  echo "  ✓ initial commit created"
fi

echo "  ==> Pushing to origin/main (Vercel will auto-deploy on receipt)"
git push -u origin main

cat <<EOF

============================================================
  ✓ Setup complete.
============================================================
The next scheduled run will:
  1. Regenerate website/index.html + website/runs/<DATE>/index.html
  2. git add -A && git commit && git push origin main
  3. Vercel sees the push and auto-deploys (~30-60 seconds)

You no longer need .vercel-token or vercel CLI for the scheduled task.
deploy.sh auto-detects git mode when ./.git/ has a remote.

Test it now from your Mac:
  ./deploy.sh

To roll back any future deploy: 'git revert <commit>' + push.
EOF
