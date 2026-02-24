# Loop Chat Bridge Runbook

Execution plan contract: required

## Scope

- Define one repeatable flow for turning loop outputs into operator-facing chat suggestions.
- Keep agent/operator coordination visible in a tracked markdown file (no hidden memory-only state).
- Capture dry-run and live-run evidence so promotion decisions are auditable.

## Execution Checklist

- [x] Confirm GitHub auth and repo access (`gh auth status -h github.com`) and record blockers.
- [x] Run loop command in report-only mode and emit bundle output (dry-run smoke).
- [ ] Convert loop output into a concise suggestion packet for chat handoff (live data run pending).
- [ ] Record decision (accept/reject/defer) and next action in this file.
- [ ] When auth/network is restored, run one live workflow dispatch and capture run URL + outcome.
- [ ] If a repeated manual step appears 2+ times, automate it or log it in `dev/audits/AUTOMATION_DEBT_REGISTER.md`.

## Progress Log

| UTC | Actor | Action | Result | Next step |
|---|---|---|---|---|
| `2026-02-24T00:00:00Z` | `ORCHESTRATOR` | Initialized loop-to-chat runbook and governance linkage (`INDEX`/`MASTER_PLAN`/discovery docs). | `in-progress` | Validate with strict-tooling checks and begin first dry-run packet capture. |
| `2026-02-24T05:03:00Z` | `ORCHESTRATOR` | Ran dry-run smoke for `triage-loop` + `mutation-loop` in `report-only` mode for `jguida941/voiceterm` on `develop`. | `passed (dry-run)` | Restore GitHub auth/token, run one live `workflow_dispatch`, and log run URL + suggestion packet. |

## Audit Evidence

- Dry-run evidence (local):
  - `python3 dev/scripts/devctl.py triage-loop --repo jguida941/voiceterm --branch develop --mode report-only --source-event workflow_dispatch --notify summary-only --format md --dry-run` -> `ok: True`, `reason: dry-run`.
  - `python3 dev/scripts/devctl.py mutation-loop --repo jguida941/voiceterm --branch develop --mode report-only --threshold 0.80 --notify summary-only --format md --dry-run` -> `ok: True`, `reason: dry-run`.
- Auth blocker recorded:
  - `gh auth status -h github.com` -> token invalid in this environment; live API/workflow evidence pending re-auth.
- Pending: first live workflow dispatch URL + success/failure note.
- Validation commands for this runbook change:
  - `python3 dev/scripts/checks/check_active_plan_sync.py`
  - `python3 dev/scripts/checks/check_multi_agent_sync.py`
  - `python3 dev/scripts/devctl.py docs-check --strict-tooling`
  - `python3 dev/scripts/devctl.py hygiene`
