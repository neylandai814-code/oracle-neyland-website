# Add this to the Oracle scheduled task

To make the live site auto-refresh after every Oracle run, append the block below
to the bottom of the scheduled task body (the same SKILL.md that drives the daily
Oracle pipeline). Once added, every scheduled run will rebuild and push the
website to Vercel as the final step.

---

## STEP 9 — DEPLOY LIVE WEBSITE (append to SKILL.md)

After all closeout protocol steps and the Gmail draft are complete, refresh the
password-protected live site so today's dashboard is reachable from the
Neyland archive URL:

    cd "/Users/neylandai/Documents/Oracle Reports/website" && ./deploy.sh

The deploy script auto-detects the right mode based on what's set up:
  1. Runs `build_site.py` to copy today's `ORACLE_Dashboard_YYYY-MM-DD.html`
     into `website/runs/YYYY-MM-DD/index.html` and regenerate the landing page.
  2. Then either:
     - **GIT MODE (preferred):** `git add -A && git commit && git push origin main`
       — Vercel auto-deploys via Git integration webhook. Activated by running
       `./setup_git_deploy.sh` once on Atlas's Mac.
     - **TOKEN MODE:** `./node_modules/.bin/vercel deploy --prod --token … --yes`
       — uses `.vercel-token` on disk. Activated by `./setup_token_deploy.sh`.
     - **INTERACTIVE MODE:** plain `vercel deploy --prod` — requires `vercel login`
       state on the host (not available in scheduled-task sandbox).

If the deploy fails (Vercel CLI not authenticated, env vars missing, network
issue), include the failure message in the run summary BUT DO NOT block the
rest of the run. The dashboard, archive files, brain updates, and Gmail draft
are still authoritative — Atlas can re-deploy manually any time by running
`./deploy.sh` from the website folder.

If the deploy succeeds, include the production URL Vercel returns in the run
summary so Atlas has the live link.

---

## How to apply this addendum

The scheduled task body (SKILL.md) lives wherever you saved it when you set up
Cowork's scheduled tasks. Open that file in any text editor, scroll to the
bottom, and paste the `## STEP 9 — DEPLOY LIVE WEBSITE` block above.

That's the only change needed. Save the file. The next scheduled run will pick
it up automatically — no other config to touch.
