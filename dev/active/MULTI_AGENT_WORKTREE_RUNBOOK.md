# Multi-Agent Worktree Execution Runbook

Use this file as the canonical coordination surface for active multi-agent execution.
All orchestrator instructions, agent ACKs, progress updates, and handoffs must be logged here.

## 0) Current Execution Mode (3 Agents, Default)

This mode is authoritative for the active `MP-306` sprint.

Coordination contract:

1. `dev/active/MULTI_AGENT_WORKTREE_RUNBOOK.md` is the only coordination surface.
2. Orchestrator instructions are posted in Section 14.
3. Each agent ACKs instructions in Section 14.
4. Each agent posts progress and handoff entries in Section 15.
5. `dev/active/MASTER_PLAN.md` remains the execution tracker for lane status.
6. Hard rule: anything not behind `--dev` is out of scope; default Whisper/listen mode must remain behavior-identical.

| Agent | Lane | Primary active docs | MP scope | Worktree | Branch |
|---|---|---|---|---|---|
| `AGENT-1` | Rust runtime lane (`--dev` overlay bridge) | `dev/active/devctl_reporting_upgrade.md` + runtime docs | `MP-306 (Rust --dev panel + async broker)` | `../codex-voice-wt-a1` | `feature/a1-mp306-rust-dev-bridge` |
| `AGENT-2` | Control-plane lane (`devctl` + CIHUB primitives) | `dev/active/devctl_reporting_upgrade.md` + tooling docs | `MP-306 (scanner tiers + JSON outputs + allowlists)` | `../codex-voice-wt-a2` | `feature/a2-mp306-control-plane` |
| `AGENT-3` | Governance/safety lane (non-interference + audit) | `dev/active/devctl_reporting_upgrade.md` + governance docs | `MP-306 (non-interference gates + docs/audit readiness)` | `../codex-voice-wt-a3` | `feature/a3-mp306-governance-safety` |

## 1) Sprint Goal

Execute `MP-306` in three isolated lanes with deterministic merge order and no default-mode regressions.

## 2) Lane File Boundaries (No Overlap)

- `AGENT-1`: `src/src/bin/voiceterm/**` only.
- `AGENT-2`: `dev/scripts/devctl/**`, `.github/workflows/security_guard.yml`, `.github/workflows/release_preflight.yml` only.
- `AGENT-3`: `dev/active/**`, `dev/DEVELOPMENT.md`, `dev/scripts/README.md`, tooling tests/docs only.

## 3) First Execution Order

1. `AGENT-2` lands control-plane primitives first.
2. `AGENT-1` integrates Rust dev-panel bridge to those primitives.
3. `AGENT-3` finalizes non-interference gates, docs updates, and merge-readiness audit.

## 4) Orchestrator Control Loop (Every 30 Minutes)

Run exactly:

```bash
python3 dev/scripts/devctl.py orchestrate-status --format md
python3 dev/scripts/devctl.py orchestrate-watch --stale-minutes 30 --format md
python3 dev/scripts/checks/check_multi_agent_sync.py --format md
```

## 5) Branch + Worktree Setup

```bash
cd /Users/jguida941/testing_upgrade/codex-voice
python3 dev/scripts/devctl.py sync --push

git worktree add -b feature/a1-mp306-rust-dev-bridge ../codex-voice-wt-a1 develop
git worktree add -b feature/a2-mp306-control-plane ../codex-voice-wt-a2 develop
git worktree add -b feature/a3-mp306-governance-safety ../codex-voice-wt-a3 develop
```

## 6) Worker Command Contract (Required)

All lanes run:

```bash
python3 dev/scripts/devctl.py docs-check --strict-tooling
python3 dev/scripts/devctl.py hygiene
python3 dev/scripts/checks/check_active_plan_sync.py
python3 dev/scripts/checks/check_multi_agent_sync.py
python3 dev/scripts/checks/check_cli_flags_parity.py
python3 dev/scripts/checks/check_screenshot_integrity.py --stale-days 120
python3 dev/scripts/checks/check_code_shape.py
python3 dev/scripts/checks/check_rust_lint_debt.py
python3 dev/scripts/checks/check_rust_best_practices.py
markdownlint -c dev/config/markdownlint.yaml -p dev/config/markdownlint.ignore README.md QUICK_START.md DEV_INDEX.md guides/*.md dev/README.md scripts/README.md pypi/README.md app/README.md
find . -maxdepth 1 -type f -name '--*'
```

Lane-specific add-ons:

- `AGENT-1`: `python3 dev/scripts/devctl.py check --profile ci` and `cd src && cargo test --bin voiceterm`.
- `AGENT-2`: run updated `dev/scripts/devctl/tests/*` unit coverage and scanner-tier smoke checks.
- `AGENT-3`: run non-interference and orchestrator accountability evidence bundle before review handoff.

## 7) Non-Interference Guard Contract

1. No new default-mode code paths or behavior changes outside `--dev`.
2. No startup/hotkey/transcript/send-flow regressions in normal mode.
3. Any new control-plane action must remain behind explicit allowlists and confirmation for mutating commands.

## 8) Reviewer Gate Protocol

Worker stop token (exact):

- `READY FOR REVIEW AGENT-1`
- `READY FOR REVIEW AGENT-2`
- `READY FOR REVIEW AGENT-3`

Reviewer responses (exact):

- `REVIEW-OK AGENT-1`
- `REVIEW-OK AGENT-2`
- `REVIEW-OK AGENT-3`
- `REVIEW-CHANGES AGENT-1`
- `REVIEW-CHANGES AGENT-2`
- `REVIEW-CHANGES AGENT-3`

Rules:

1. No merge to `develop` without matching `REVIEW-OK AGENT-<N>`.
2. On requested changes, the agent patches and re-runs required checks.
3. After each merge, remaining active lanes rebase onto `origin/develop`.

## 9) Rebase Protocol After Each Merge

```bash
git -C /Users/jguida941/testing_upgrade/codex-voice-wt-a1 fetch origin && git -C /Users/jguida941/testing_upgrade/codex-voice-wt-a1 rebase origin/develop
git -C /Users/jguida941/testing_upgrade/codex-voice-wt-a2 fetch origin && git -C /Users/jguida941/testing_upgrade/codex-voice-wt-a2 rebase origin/develop
git -C /Users/jguida941/testing_upgrade/codex-voice-wt-a3 fetch origin && git -C /Users/jguida941/testing_upgrade/codex-voice-wt-a3 rebase origin/develop
```

## 10) Integration Audit Before Final Merge Readiness

Run on `develop` after all lane merges:

```bash
python3 dev/scripts/devctl.py check --profile ci
python3 dev/scripts/devctl.py docs-check --strict-tooling
python3 dev/scripts/devctl.py orchestrate-status --format md
python3 dev/scripts/devctl.py orchestrate-watch --stale-minutes 30 --format md
python3 dev/scripts/checks/check_multi_agent_sync.py --format md
python3 dev/scripts/devctl.py status --ci --require-ci --format md
```

## 11) Merge/Promotion Policy

- Merge lane branches to `develop` only after reviewer approval token.
- `master` remains release-only.
- Promote `develop` to `master` only after final integration audit and green CI.

## 12) Agent Prompt Template

```text
You are AGENT-<N> for MP-306.

Hard constraints:
1) Work only in your assigned lane and file boundaries.
2) Keep all new behavior behind --dev unless task explicitly says otherwise.
3) Read dev/active/INDEX.md and dev/active/MASTER_PLAN.md first.
4) Use AGENTS.md bundles/risk matrix for validation.
5) Post ACK/progress/handoff in MULTI_AGENT_WORKTREE_RUNBOOK.md.
6) Stop with READY FOR REVIEW AGENT-<N> when done.
```

## 13) Sprint Completion Criteria

1. `AGENT-2` control-plane primitives merged.
2. `AGENT-1` Rust `--dev` panel bridge merged on top of `AGENT-2` primitives.
3. `AGENT-3` non-interference gates, docs, and audit evidence merged.
4. Orchestrator loop checks green with no stale/inconsistent lane state.

## 14) Orchestrator Instruction Log (Append-Only)

All orchestrator-to-agent instructions must be logged here. This is the
canonical thread for assignment, due-time, ACK tracking, and completion state.

| UTC issued | Instruction ID | From | To | Summary | Due (UTC) | Ack token | Ack UTC | Status |
|---|---|---|---|---|---|---|---|---|
| `2026-02-23T20:15:00Z` | `ORCH-001` | `ORCHESTRATOR` | `AGENT-2` | land MP-306 control-plane primitives: scanner tiers (core/expensive), JSON outputs, command allowlists, CIHUB setup flow scaffolding | `2026-02-23T22:00:00Z` | `ACK-AGENT-2-ORCH-001` | `2026-02-23T20:26:00Z` | `completed` |
| `2026-02-23T20:15:00Z` | `ORCH-002` | `ORCHESTRATOR` | `AGENT-1` | integrate Rust `--dev` tab/panel bridge + async command broker after AGENT-2 primitives; no default-mode impact | `2026-02-23T23:30:00Z` | `ACK-AGENT-1-ORCH-002` | `2026-02-23T21:02:37Z` | `completed` |
| `2026-02-23T20:15:00Z` | `ORCH-003` | `ORCHESTRATOR` | `AGENT-3` | finalize non-interference tests, CI guard wiring, docs/plan updates, and merge-readiness audit | `2026-02-23T23:59:00Z` | `ACK-AGENT-3-ORCH-003` | `2026-02-23T20:15:00Z` | `completed` |

Instruction log rules:

1. `Instruction ID` must be unique and immutable.
2. `To` must be one of `AGENT-1`, `AGENT-2`, `AGENT-3`.
3. `Due (UTC)` and `Ack UTC` must use `YYYY-MM-DDTHH:MM:SSZ`.
4. `Status` lifecycle is `pending` -> `acked` -> `completed` (or `cancelled`).
5. Any row in `pending`/`acked` past `Due (UTC)` is an SLA breach.

## 15) Shared Ledger (Append-Only)

| UTC | Actor | Area | Worktree | Branch | Commit | MP scope | Verification summary | Status | Reviewer token | Next action |
|---|---|---|---|---|---|---|---|---|---|---|
| `2026-02-23T20:15:00Z` | `ORCHESTRATOR` | `AGENT-2` | `../codex-voice-wt-a2` | `feature/a2-mp306-control-plane` | `pending` | `MP-306` | `ORCH-001 issued; lane ordered first per sprint execution plan.` | `in-progress` | `pending` | `AGENT-2 posts first progress + ACK update in Section 14/15.` |
| `2026-02-23T20:15:00Z` | `AGENT-3` | `AGENT-3` | `../codex-voice-wt-a3` | `feature/a3-mp306-governance-safety` | `working-tree` | `MP-306` | `Ran orchestrator control loop: orchestrate-status=ok, orchestrate-watch=ok, check_multi_agent_sync=ok; started runbook/master-plan sprint retarget.` | `in-progress` | `pending` | `Finalize governance docs and non-interference gate checklist after AGENT-2/AGENT-1 slices land.` |
| `2026-02-23T20:26:00Z` | `AGENT-2` | `AGENT-2` | `../codex-voice-wt-a2` | `feature/a2-mp306-control-plane` | `working-tree` | `MP-306` | `Implemented control-plane primitives: devctl scanner tiers (rustsec/core/all), new allowlisted cihub-setup preview/apply flow with JSON output, and CI workflow wiring updates; verification: devctl unit suites + tooling bundle gates (bundle blocked only by pre-existing unrelated check_code_shape failure in src/src/bin/voiceterm/event_loop.rs).` | `ready-for-review` | `pending` | `AGENT-1 integrates Rust --dev Dev Tools bridge on top of AGENT-2 command primitives.` |
| `2026-02-23T20:56:21Z` | `AGENT-2` | `AGENT-2` | `/Users/jguida941/testing_upgrade/codex-voice` | `develop` | `working-tree` | `MP-306` | `User-directed cross-lane pass landed control-plane + runtime audit hardening: added check_rust_audit_patterns guard and wired it into devctl/CI, added ai-guard checks to security/release preflight lanes, fixed UTF-8 preview slicing, char-safe transcript truncation/input limits, multi-occurrence secret redaction, non-deterministic event/session ID suffixing, and saturating VAD float-to-i16 conversion; verification included devctl unit tests, targeted cargo tests, docs-check, hygiene, active-plan sync, and multi-agent sync.` | `ready-for-review` | `pending` | `Review combined diff; split/land as requested by orchestrator policy.` |
| `2026-02-23T21:02:37Z` | `AGENT-1` | `AGENT-1` | `/Users/jguida941/testing_upgrade/codex-voice` | `develop` | `working-tree` | `MP-306` | `User-directed cross-lane execution completed Rust lane scope with --dev-only bridge behavior preserved and default-mode non-interference maintained; runtime audit remediations validated with targeted cargo tests and ai-guard profile.` | `ready-for-review` | `pending` | `Orchestrator review + branch split if strict lane-only merge is required.` |
| `2026-02-23T21:02:37Z` | `AGENT-3` | `AGENT-3` | `/Users/jguida941/testing_upgrade/codex-voice` | `develop` | `working-tree` | `MP-306` | `Governance/safety lane updated for cross-lane execution: refreshed runbook instruction statuses, refreshed MASTER_PLAN lane status timestamps, and reran sync/docs orchestration checks for audit-ready state.` | `ready-for-review` | `pending` | `Final policy review and merge sequencing decision.` |
| `2026-02-23T21:02:37Z` | `AGENT-2` | `AGENT-2` | `/Users/jguida941/testing_upgrade/codex-voice` | `develop` | `working-tree` | `MP-306` | `Control-plane lane verified after security-python-scope module integration: devctl ai-guard profile now passes end-to-end and includes rust audit pattern gate.` | `ready-for-review` | `pending` | `Proceed to combined review or split lane commits for orchestrator policy.` |
| `2026-02-23T21:36:03Z` | `AGENT-2` | `AGENT-2` | `/Users/jguida941/testing_upgrade/codex-voice` | `develop` | `working-tree` | `MP-306` | `User-requested Dev Tools bridge hardening: dev-panel allowlisted commands now request CI-aware payloads (`status/report/triage --ci`) so run pass/fail and remediation guidance flow through the same `devctl` JSON contract; broker summary logic now prioritizes `ci` health and `next_actions`; verification: \`cd src && cargo test --bin voiceterm dev_command::tests:: -- --nocapture\` (8 passed).` | `ready-for-review` | `pending` | `Confirm with orchestrator whether this cross-lane runtime bridge delta remains in AGENT-2 combined pass or is cherry-picked into AGENT-1 lane PR.` |

Status values:

- `in-progress`
- `ready-for-review`
- `changes-requested`
- `approved`
- `merged`
- `blocked`
- `ready`

## 16) End-of-Cycle Signoff (Required)

Complete this table after all three agent lanes are merged. The multi-agent
sync guard validates these rows when all lane statuses in `MASTER_PLAN` are
`merged`.

| Signer | Date (UTC) | Result | Isolation verified | Bundle reference | Signature |
|---|---|---|---|---|---|
| `AGENT-1` | `pending` | `pending` | `pending` | `pending` | `pending` |
| `AGENT-2` | `pending` | `pending` | `pending` | `pending` | `pending` |
| `AGENT-3` | `pending` | `pending` | `pending` | `pending` | `pending` |
| `ORCHESTRATOR` | `pending` | `pending` | `pending` | `pending` | `pending` |

Signoff rules:

1. `Result` must be `pass` for every signer.
2. `Isolation verified` must be `yes` for every signer.
3. `Bundle reference` must point to final verification evidence.
4. `Signature` must be concrete initials/name token, not `pending`.

## 17) Final Cleanup (After Cycle Completes)

```bash
cd /Users/jguida941/testing_upgrade/codex-voice
git worktree list
# Remove cycle worktrees once merged and no longer needed:
# git worktree remove ../codex-voice-wt-a1
# git worktree remove ../codex-voice-wt-a2
# git worktree remove ../codex-voice-wt-a3
```
