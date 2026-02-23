# Multi-Agent Worktree Execution Runbook

Use this file as the canonical orchestration surface for parallel execution.
All worker agents and the reviewer append evidence in this file while the cycle is active.

## 0) Current Execution Mode (3 Agents, Default)

This mode is authoritative for current runs with three concurrent agents.

Coordination contract:

1. The assignment/status board in `dev/active/MASTER_PLAN.md` is the
   canonical "who owns what now" tracker.
2. This runbook is the append-only command/evidence log.
3. Every agent works from `develop` in its own worktree/branch.
4. `master` is release-only; no feature work lands directly on `master`.
5. Agents must not edit MP lines outside their assigned lane scope.

| Agent | Lane | Primary active docs | MP scope | Worktree | Branch |
|---|---|---|---|---|---|
| `AGENT-1` | Runtime/Theme execution | `dev/active/theme_upgrade.md` | `MP-161`, `MP-162`, `MP-166`, `MP-167`, `MP-172`, `MP-173`, `MP-174`, `MP-177`, `MP-178`, `MP-181` | `../codex-voice-wt-a1` | `feature/a1-runtime-theme` |
| `AGENT-2` | Tooling/control-plane and governance | `dev/active/devctl_reporting_upgrade.md` | `MP-257`, `MP-297`, `MP-298`, `MP-306` | `../codex-voice-wt-a2` | `feature/a2-tooling-control-plane` |
| `AGENT-3` | Memory/mutation/reliability execution | `dev/active/memory_studio.md` | `MP-015`, `MP-230..MP-255`, `MP-301` | `../codex-voice-wt-a3` | `feature/a3-memory-mutation-reliability` |

## 1) Current Audit Snapshot (2026-02-19)

### Branch and release posture

- Working branch: `develop`
- `origin/develop` is ahead of `origin/master` by 10 commits (`origin/master...origin/develop = 1 10`).
- Existing historical area worktrees are attached (`area-a`..`area-e`) and should be treated as prior-cycle artifacts.

### Active plan posture (`dev/active/MASTER_PLAN.md`)

- Open MP items total: `59`
- Completed MP items total: `126`
- Primary open execution tracks:
  - Theme Studio completion track (`MP-102`, `MP-161`, `MP-162`, `MP-172`, `MP-174`, `MP-175`, `MP-176`, `MP-179`, `MP-180`, `MP-182`, `MP-164`..`MP-167`, `MP-173`, `MP-177`, `MP-178`, `MP-181`)
  - Memory + Action Studio planning-to-implementation track (`MP-230`..`MP-255`)
  - Mutation hardening (`MP-015`)

## 2) Goal For This Cycle

Execute open Theme + Memory + Mutation scope in parallel with strict review gates,
while preserving one canonical execution tracker (`dev/active/MASTER_PLAN.md`) and
passing governance guardrails on every merge.

## 3) Scope Routing For This Cycle

### In scope now

- Theme foundation and delivery:
  - `MP-102`, `MP-161`, `MP-162`, `MP-172`, `MP-174`
  - `MP-175`, `MP-176`, `MP-179`, `MP-180`, `MP-182`
  - `MP-164`, `MP-165`, `MP-166`
  - `MP-167`, `MP-173`, `MP-177`, `MP-178`, `MP-181`
- Memory track:
  - `MP-230`..`MP-255`
- Mutation track:
  - `MP-015`

### Out of scope for this cycle

- Phase 4 expansion items not explicitly listed above.
- Backlog-only work not promoted into `MASTER_PLAN` active scope.

## 4) Area Model (Parallel Lanes)

Each area has one owner agent and a fixed MP scope.
Do not edit MP lines owned by another area.

- `AREA-T1` Theme foundation/runtime surfaces
  - MPs: `MP-102`, `MP-161`, `MP-162`, `MP-172`, `MP-174`
  - Outcome: visual/runtime surfaces fully routed through style-pack contracts.

- `AREA-T2` Theme capability/ecosystem matrix
  - MPs: `MP-175`, `MP-176`, `MP-179`, `MP-180`, `MP-182`
  - Outcome: capability fallback matrix + ecosystem parity + rule-profile scaffolding.

- `AREA-T3` Theme Studio core mode
  - MPs: `MP-164`, `MP-165`, `MP-166`
  - Outcome: dedicated Theme Studio mode and settings ownership migration.

- `AREA-T4` Theme GA and policy gates
  - MPs: `MP-167`, `MP-173`, `MP-177`, `MP-178`, `MP-181`
  - Outcome: GA validation, CI policy gates, inspector/advanced interaction parity.

- `AREA-M1` Memory foundation and safe runtime baseline
  - MPs: `MP-230`, `MP-231`, `MP-232`, `MP-233`, `MP-234`, `MP-235`, `MP-243`
  - Outcome: canonical schema/storage/retrieval/browser/action-center baseline + user memory modes.

- `AREA-M2` Memory advanced validation/interop/perf track
  - MPs: `MP-236`, `MP-237`, `MP-238`, `MP-240`, `MP-241`, `MP-242`, `MP-244`, `MP-246`, `MP-247`, `MP-248`, `MP-249`, `MP-250`, `MP-251`, `MP-252`, `MP-253`, `MP-254`, `MP-255`
  - Outcome: docs/release readiness, evaluation harnesses, interop, safety escalation, compaction/acceleration gates.

- `AREA-X1` Mutation hardening
  - MPs: `MP-015`
  - Outcome: mutation score hardening with targeted survivors and evidence.

## 5) Dependency Graph

- `AREA-T1` -> `AREA-T3` -> `AREA-T4`
- `AREA-T2` -> `AREA-T4`
- `AREA-M1` -> `AREA-M2`
- `AREA-X1` is independent.

## 6) Wave Plan (Dependency-Safe)

1. Wave 1 (parallel): `AREA-T1`, `AREA-T2`, `AREA-M1`, `AREA-X1`
2. Wave 2 (parallel): `AREA-T3`, `AREA-M2` (after upstream approvals/merges)
3. Wave 3: `AREA-T4`
4. Final integration audit on `develop`.
5. Release promotion prep only after `develop` is green and synchronized.

## 7) Branch + Worktree Setup

### 7.0 Default setup for 3-agent mode

```bash
cd /Users/jguida941/testing_upgrade/codex-voice
python3 dev/scripts/devctl.py sync --push

git worktree add -b feature/a1-runtime-theme ../codex-voice-wt-a1 develop
git worktree add -b feature/a2-tooling-control-plane ../codex-voice-wt-a2 develop
git worktree add -b feature/a3-memory-mutation-reliability ../codex-voice-wt-a3 develop
```

### 7.1 Optional cleanup of prior-cycle worktrees

```bash
cd /Users/jguida941/testing_upgrade/codex-voice
git worktree list
# Remove only if no longer needed:
# git worktree remove ../codex-voice-wt-area-a
# git worktree remove ../codex-voice-wt-area-b
# git worktree remove ../codex-voice-wt-area-c
# git worktree remove ../codex-voice-wt-area-d
# git worktree remove ../codex-voice-wt-area-e
```

### 7.2 Create fresh worktrees for this cycle

```bash
cd /Users/jguida941/testing_upgrade/codex-voice
git fetch origin
git checkout develop
git pull --ff-only origin develop

git worktree add -b feature/t1-theme-foundation ../codex-voice-wt-t1 develop
git worktree add -b feature/t2-theme-capability ../codex-voice-wt-t2 develop
git worktree add -b feature/t3-theme-studio-core ../codex-voice-wt-t3 develop
git worktree add -b feature/t4-theme-ga-policy ../codex-voice-wt-t4 develop
git worktree add -b feature/m1-memory-foundation ../codex-voice-wt-m1 develop
git worktree add -b feature/m2-memory-advanced ../codex-voice-wt-m2 develop
git worktree add -b feature/x1-mutation-hardening ../codex-voice-wt-x1 develop
```

## 8) Worker Command Contract (Required)

Each worker must run at least:

```bash
python3 dev/scripts/devctl.py check --profile ci
python3 dev/scripts/devctl.py docs-check --user-facing
python3 dev/scripts/devctl.py hygiene
python3 dev/scripts/checks/check_agents_contract.py
python3 dev/scripts/checks/check_active_plan_sync.py
python3 dev/scripts/checks/check_cli_flags_parity.py
python3 dev/scripts/checks/check_screenshot_integrity.py --stale-days 120
find . -maxdepth 1 -type f -name '--*'
cd src && cargo test --bin voiceterm
```

If risk-sensitive paths are touched, run the mapped add-on matrix from `AGENTS.md`.

## 9) Reviewer Gate Protocol

Worker stop token (exact):

- `READY FOR REVIEW AREA-<ID>`
- `READY FOR REVIEW AGENT-<N>`

Reviewer responses (exact):

- `REVIEW-OK AREA-<ID>`
- `REVIEW-CHANGES AREA-<ID>`
- `REVIEW-OK AGENT-<N>`
- `REVIEW-CHANGES AGENT-<N>`

Rules:

1. No merge to `develop` without a matching `REVIEW-OK ...` token.
2. If changes requested, worker patches and re-runs required checks.
3. After merge, rebase active downstream worktrees onto `origin/develop`.

## 10) Rebase Protocol After Each Merge

Default 3-agent mode:

```bash
git -C /Users/jguida941/testing_upgrade/codex-voice-wt-a1 fetch origin && git -C /Users/jguida941/testing_upgrade/codex-voice-wt-a1 rebase origin/develop
git -C /Users/jguida941/testing_upgrade/codex-voice-wt-a2 fetch origin && git -C /Users/jguida941/testing_upgrade/codex-voice-wt-a2 rebase origin/develop
git -C /Users/jguida941/testing_upgrade/codex-voice-wt-a3 fetch origin && git -C /Users/jguida941/testing_upgrade/codex-voice-wt-a3 rebase origin/develop
```

Expanded-lane mode (legacy/optional):

```bash
git -C /Users/jguida941/testing_upgrade/codex-voice-wt-t1 fetch origin && git -C /Users/jguida941/testing_upgrade/codex-voice-wt-t1 rebase origin/develop
git -C /Users/jguida941/testing_upgrade/codex-voice-wt-t2 fetch origin && git -C /Users/jguida941/testing_upgrade/codex-voice-wt-t2 rebase origin/develop
git -C /Users/jguida941/testing_upgrade/codex-voice-wt-t3 fetch origin && git -C /Users/jguida941/testing_upgrade/codex-voice-wt-t3 rebase origin/develop
git -C /Users/jguida941/testing_upgrade/codex-voice-wt-t4 fetch origin && git -C /Users/jguida941/testing_upgrade/codex-voice-wt-t4 rebase origin/develop
git -C /Users/jguida941/testing_upgrade/codex-voice-wt-m1 fetch origin && git -C /Users/jguida941/testing_upgrade/codex-voice-wt-m1 rebase origin/develop
git -C /Users/jguida941/testing_upgrade/codex-voice-wt-m2 fetch origin && git -C /Users/jguida941/testing_upgrade/codex-voice-wt-m2 rebase origin/develop
git -C /Users/jguida941/testing_upgrade/codex-voice-wt-x1 fetch origin && git -C /Users/jguida941/testing_upgrade/codex-voice-wt-x1 rebase origin/develop
```

## 11) Claude Worker Prompt Templates (Copy/Paste)

### 11.1 Launch prompt for a worker area

```text
You are assigned AREA-<ID> from dev/active/MULTI_AGENT_WORKTREE_RUNBOOK.md.

Hard constraints:
1) Work only on MP items assigned to AREA-<ID>.
2) Use only this worktree: <ABSOLUTE_WORKTREE_PATH>
3) Branch is fixed: <BRANCH_NAME>
4) Read dev/active/INDEX.md and dev/active/MASTER_PLAN.md first.
5) Follow AGENTS.md command bundles and risk-matrix checks.
6) Update MASTER_PLAN evidence only for AREA-<ID> MP lines.
7) Run required checks before review and include exact command outputs summary.
8) Append one row to runbook ledger with status=ready-for-review when done.
9) Stop and output exactly: READY FOR REVIEW AREA-<ID>
```

### 11.2 Reviewer prompt (for Claude reviewer session)

```text
You are the reviewer for AREA-<ID> in dev/active/MULTI_AGENT_WORKTREE_RUNBOOK.md.

Review protocol:
1) Audit only AREA-<ID> scope for regressions, missing tests, and docs/governance drift.
2) Verify required checks were run and are credible for changed risk classes.
3) Confirm MASTER_PLAN evidence lines are accurate and scoped.
4) Return exactly one token:
   - REVIEW-OK AREA-<ID>
   - REVIEW-CHANGES AREA-<ID>
5) If REVIEW-CHANGES, include numbered required fixes.
```

## 12) Integration/Release Audit After All Area Merges

Run on `develop`:

```bash
cd /Users/jguida941/testing_upgrade/codex-voice
git status
git log --oneline --decorate -n 15
python3 dev/scripts/devctl.py check --profile ci
python3 dev/scripts/devctl.py check --profile release
python3 dev/scripts/devctl.py docs-check --user-facing --strict
python3 dev/scripts/devctl.py docs-check --strict-tooling
python3 dev/scripts/devctl.py hygiene
python3 dev/scripts/checks/check_agents_contract.py
python3 dev/scripts/checks/check_active_plan_sync.py
python3 dev/scripts/checks/check_release_version_parity.py
python3 dev/scripts/checks/check_cli_flags_parity.py
python3 dev/scripts/checks/check_screenshot_integrity.py --stale-days 120
find . -maxdepth 1 -type f -name '--*'
```

Then verify CI status:

```bash
python3 dev/scripts/devctl.py status --ci --require-ci --format md
```

## 13) Merge/Promotion Policy

- Merge area branches to `develop` only after reviewer token is `REVIEW-OK`.
- Keep `master` as release branch; do not push feature work directly to `master`.
- Promote `develop` to `master` only when full integration audit and required CI lanes are green.

## 14) Orchestrator Instruction Log (Append-Only)

All orchestrator-to-agent instructions must be logged here. This is the
canonical MD thread for assignment + due-time + acknowledgment tracking.

| UTC issued | Instruction ID | From | To | Summary | Due (UTC) | Ack token | Ack UTC | Status |
|---|---|---|---|---|---|---|---|---|
| `2026-02-23T00:00:00Z` | `INS-A1-BOOT` | `ORCHESTRATOR` | `AGENT-1` | bootstrap lane and post first execution update in board/ledger | `2026-02-23T00:10:00Z` | `ACK-AGENT-1-BOOT` | `2026-02-23T00:05:00Z` | `completed` |
| `2026-02-23T00:00:00Z` | `INS-A2-BOOT` | `ORCHESTRATOR` | `AGENT-2` | bootstrap lane and post first execution update in board/ledger | `2026-02-23T00:10:00Z` | `ACK-AGENT-2-BOOT` | `2026-02-23T00:06:00Z` | `completed` |
| `2026-02-23T00:00:00Z` | `INS-A3-BOOT` | `ORCHESTRATOR` | `AGENT-3` | bootstrap lane and post first execution update in board/ledger | `2026-02-23T00:10:00Z` | `ACK-AGENT-3-BOOT` | `2026-02-23T00:07:00Z` | `completed` |

Instruction log rules:

1. `Instruction ID` must be unique and immutable.
2. `To` must be one of `AGENT-1`, `AGENT-2`, `AGENT-3`.
3. `Due (UTC)` and `Ack UTC` must use `YYYY-MM-DDTHH:MM:SSZ`.
4. `Status` lifecycle is `pending` -> `acked` -> `completed` (or `cancelled`).
5. Any row in `pending`/`acked` past `Due (UTC)` is an SLA breach.

## 15) Shared Ledger (Append-Only)

| UTC | Actor | Area | Worktree | Branch | Commit | MP scope | Verification summary | Status | Reviewer token | Next action |
|---|---|---|---|---|---|---|---|---|---|---|
| 2026-02-19T20:00:00Z | reviewer | setup | `n/a` | `develop` | `17254cd` | Theme+Memory+Mutation cycle bootstrap | runbook refreshed to current open scope and guard contracts | ready | pending | launch Wave 1 areas |
| 2026-02-19T21:00:00Z | orchestrator | all | t1..t4,m1,m2,x1 | `develop` | `5b46a91` | Worktree creation for 7 areas | prior worktrees removed; 7 fresh worktrees created off develop@5b46a91 | ready | pending | launch Wave 1 workers (T1,T2,M1,X1) |

Status values:

- `in-progress`
- `ready-for-review`
- `changes-requested`
- `approved`
- `merged`
- `blocked`

## 16) End-of-Cycle Signoff (Required)

Complete this table after all three agent lanes are merged. The multi-agent
guard validates these rows when all agent statuses in `MASTER_PLAN` are
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
3. `Bundle reference` must point to the final verification run evidence.
4. `Signature` must be a concrete initials/name token, not `pending`.

## 17) Final Cleanup (After Cycle Completes)

```bash
cd /Users/jguida941/testing_upgrade/codex-voice
git worktree list
# Remove cycle worktrees once merged and no longer needed:
# git worktree remove ../codex-voice-wt-t1
# git worktree remove ../codex-voice-wt-t2
# git worktree remove ../codex-voice-wt-t3
# git worktree remove ../codex-voice-wt-t4
# git worktree remove ../codex-voice-wt-m1
# git worktree remove ../codex-voice-wt-m2
# git worktree remove ../codex-voice-wt-x1
```
