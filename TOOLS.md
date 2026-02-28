# TOOLS.md - Local Notes

## Email
- Joy inbox: joyai8009@gmail.com
- Policy: Joy may read/triage inbox and report results to Steven.
- Steven emails (allowed outbound recipients): steve.x.xu@gmail.com, steven@inp-capital.com
- Outbound: Joy may only send emails to Steven at the addresses above (never to third parties) and only when explicitly asked.
- Auth: Gmail IMAP with App Password (2FA enabled).

## LinkedIn
- Account: steve.x.xu@gmail.com
- Daily Flywheel (review/check/post): use **isolated browser** (OpenClaw profile="openclaw") by default.
- Do **not** assume Chrome Relay is attached; only use Relay when Steven explicitly asks.

---

(Keep credentials out of this repo; prefer environment variables or a secrets store.)

<!-- antfarm:workflows -->
# Antfarm Workflows

Antfarm CLI (always use full path to avoid PATH issues):
`node ~/.openclaw/workspace/antfarm/dist/cli/cli.js`

Commands:
- Install: `node ~/.openclaw/workspace/antfarm/dist/cli/cli.js workflow install <name>`
- Run: `node ~/.openclaw/workspace/antfarm/dist/cli/cli.js workflow run <workflow-id> "<task>"`
- Status: `node ~/.openclaw/workspace/antfarm/dist/cli/cli.js workflow status "<task title>"`
- Logs: `node ~/.openclaw/workspace/antfarm/dist/cli/cli.js logs`

Workflows are self-advancing via per-agent cron jobs. No manual orchestration needed.
<!-- /antfarm:workflows -->

