# VoiceTerm — Review Snapshot

> Deterministically generated from typed governance state. Do not edit by hand — rerun `devctl review-snapshot --write`.

## Quick status

- Branch: `extraction/guardir-core-p0-proof-integrity`
- HEAD: `58bee30ca5a3` — Multi-session checkpoint: peer-spawn id-resolution + bounded task-prompt + agent-spawn allow-list
- Tree hash: `10299c17f4ee`
- Generation stamp: `snap-9d1ca1265158`
- Generated at (UTC): 2026-05-23T15:42:28Z
- Push decision: `run_devctl_push` — push_preconditions_satisfied
- Reviewer mode: `tools_only` (interaction: `local_terminal`)
- Pipeline state: `n/a` (approval: `n/a`)
- Delta since last snapshot: 24 commits, 420 files, +81114/-3619
- Governance findings: 26 open / 0 fixed / 26 total
- Probe hints: 0 total across 0 files scanned

## 1. Identity

- Repository: **VoiceTerm**
- Product thesis: This is the product thesis for the governance stack in this repository.
Absorb these four commitments before engaging with SOP, guard, routing,
or plan detail — they explain why the process exists.

This repo builds a portable AI governance platform proven through one
production client (VoiceTerm...
- Remote: `https://github.com/jguida941/voiceterm.git`
- Default branch: `master`
- Current branch: `extraction/guardir-core-p0-proof-integrity`
- HEAD SHA: `58bee30ca5a3be49c08f820f933e6b45b49cdd95`
- HEAD author: Justin Guida
- HEAD timestamp (UTC): 2026-05-23T11:41:34-04:00

## 2. Governance state

### Push decision
- action: `run_devctl_push`
- reason: push_preconditions_satisfied
- push_eligible_now: True
- worktree_clean: True
- staged_path_count: 0
- unstaged_path_count: 0
- next_step_command: `python3 dev/scripts/devctl.py push --execute`
- latest_push_report_state: `blocked` (validation_failed)
- publication_backlog: recommended
- publication_guidance: 2 local commit(s) waiting for governed push. Run `python3 dev/scripts/devctl.py push --execute` now.

### Reviewer runtime
- reviewer_mode: `tools_only`
- reviewer_freshness: unknown
- reviewer_publish_clear: True
- interaction_mode: `local_terminal`

### Remote commit pipeline
- state: `n/a`
- approval_state: `n/a`

### Work intake
- active plan: **AI Governance Platform Plan**
- plan path: `dev/active/ai_governance_platform.md`
- active MP scope: `MP-377`
- advisory: `push_allowed` — worktree_clean_and_review_accepted

## 3. Delta — what changed since the previous snapshot

Range: last 24 commits ending at `58bee30ca5a3`

- commits: 24
- files changed: 420
- insertions: +81114
- deletions: -3619
- bundle classes touched: tooling, docs
- risk add-ons triggered: Dependency / security
- authority surfaces touched: 6 file(s)

### Commits

| # | SHA | Subject | Files | +/- | Bundle | Risk |
|---|---|---|---|---|---|---|
| 1 | `58bee30c` | Multi-session checkpoint: peer-spawn id-resolution + bounde… | 344 | +58347/-1882 | tooling | Dependency / security |
| 2 | `9b321ff7` | CLAUDE-REV-002 G1+G8: pre_mutation gate + pre-commit hook c… | 11 | +2094/-7 | tooling |  |
| 3 | `7a7afa85` | Refresh external review snapshot for 90451b8a | 1 | +19/-19 | tooling |  |
| 4 | `90451b8a` | Snapshot remaining GuardIR governance repair state | 88 | +17323/-697 | tooling |  |
| 5 | `d1387379` | Repair current plan packet scheduler | 17 | +1287/-76 | tooling |  |
| 6 | `fda73137` | Refresh external review snapshot for 41ad2430 | 1 | +49/-47 | tooling |  |
| 7 | `41ad2430` | Land GuardIR v4 canonical plan markdown | 2 | +716/-0 | tooling |  |
| 8 | `62dd7efb` | Refresh external review snapshot for 3a698ba6 | 1 | +55/-49 | tooling |  |
| 9 | `3a698ba6` | Add packet contract schema fixtures | 7 | +166/-54 | tooling |  |
| 10 | `a55f1fbe` | Refresh external review snapshot for 52d8835c | 1 | +52/-53 | tooling |  |
| 11 | `52d8835c` | Bind system map closure plan row | 5 | +53/-50 | tooling |  |
| 12 | `37e29c9a` | Refresh external review snapshot for d06542d2 | 1 | +53/-54 | tooling |  |
| 13 | `d06542d2` | Bind proof resolver closure row | 6 | +55/-52 | tooling |  |
| 14 | `88cd53ad` | Refresh external review snapshot for 877ec1c5 | 1 | +52/-50 | tooling |  |
| 15 | `877ec1c5` | Resolve unittest proof test nodes | 4 | +133/-62 | tooling |  |
| 16 | `93bce1be` | Refresh external review snapshot for 5e431ccc | 1 | +52/-53 | tooling |  |
| 17 | `5e431ccc` | Bind push proof closure plan row | 5 | +54/-57 | tooling |  |
| 18 | `fd57faa3` | Refresh external review snapshot for 69c856eb | 1 | +52/-53 | tooling |  |
| 19 | `69c856eb` | Record push proof closure receipts | 6 | +59/-62 | tooling |  |
| 20 | `20a808a3` | Refresh external review snapshot for 3e35699c | 1 | +54/-51 | tooling |  |
| 21 | `3e35699c` | Fix push-owned commit proof receipts | 5 | +282/-78 | tooling |  |
| 22 | `af8ef168` | Refresh policy-owned generated surfaces for 58a30236 | 1 | +2/-2 | docs |  |
| 23 | `58a30236` | Refresh external review snapshot for ef1f4365 | 1 | +54/-63 | tooling |  |
| 24 | `ef1f4365` | Record packet attention plan closure | 5 | +51/-48 | tooling |  |

### Files

| Path | Bundle | +/- |
|---|---|---|
| `.claude/settings.json` | tooling | +12/-0 |
| `.github/workflows/release_preflight.yml` | tooling | +15/-0 |
| `.github/workflows/tooling_control_plane.yml` | tooling | +45/-0 |
| `AGENTS.md` | docs | +6/-0 |
| `System_Connection_Flowchart.md` | docs | +49/-5 |
| `delete_after_ingest.md` | docs | +5312/-0 |
| `dev/active/INDEX.md` | tooling | +22/-6 |
| `dev/active/MASTER_PLAN.md` | tooling | +204/-24 |
| `dev/active/ai_governance_platform.md` | tooling | +87/-49 |
| `dev/active/contract_orphans_audit.md` | tooling | +58/-0 |
| `dev/active/live_state_semantic_tdd_plan.md` | tooling | +1092/-0 |
| `dev/active/platform_authority_loop.md` | tooling | +12/-12 |
| `dev/active/semantic_tdd_lane.md` | tooling | +209/-0 |
| `dev/audits/REVIEW_SNAPSHOT.md` | tooling | +997/-1008 |
| `dev/audits/plan_intake/2026-05-20-guardir-lifecycle-recovery-ci-proof-bridge-v4.md` | tooling | +5496/-355 |
| `dev/audits/plan_intake/sha256-manifest.txt` | tooling | +2/-1 |
| `dev/config/git_hooks/pre-commit-review-snapshot.sh` | tooling | +89/-7 |
| `dev/dev/state/ground_truth_probe_receipts.jsonl` | tooling | +1/-0 |
| `dev/guides/AI_GOVERNANCE_PLATFORM.md` | docs | +3/-2 |
| `dev/guides/DEVELOPMENT.md` | docs | +56/-20 |
| `dev/guides/PLATFORM_GUIDE.md` | docs | +872/-12 |
| `dev/guides/SYSTEM_MAP.md` | docs | +58/-55 |
| `dev/history/ENGINEERING_EVOLUTION.md` | tooling | +63/-1 |
| `dev/reports/feature_proof_receipts/7a7afa8520c0d7ca751be3eb889e36b02ea6ebf2.json` | tooling | +48/-0 |
| `dev/scripts/README.md` | tooling | +21/-0 |
| `dev/scripts/checks/_git_status_helpers.py` | tooling | +44/-0 |
| `dev/scripts/checks/_receipt_store_scope.py` | tooling | +44/-0 |
| `dev/scripts/checks/check_action_request_expiry_refresh.py` | tooling | +680/-0 |
| `dev/scripts/checks/check_active_plan_sync.py` | tooling | +11/-1 |
| `dev/scripts/checks/check_active_topology_liveness.py` | tooling | +1498/-0 |
| `dev/scripts/checks/check_bootstrap.py` | tooling | +185/-0 |
| `dev/scripts/checks/check_child_actor_scope.py` | tooling | +459/-0 |
| `dev/scripts/checks/check_continuation_anchor_enforcement.py` | tooling | +955/-0 |
| `dev/scripts/checks/check_contract_consumer_coverage_sweep.py` | tooling | +835/-0 |
| `dev/scripts/checks/check_current_plan_authority.py` | tooling | +11/-0 |
| `dev/scripts/checks/check_current_row_proof_bundle.py` | tooling | +176/-0 |
| `dev/scripts/checks/check_every_applied_row_has_closure_receipt.py` | tooling | +315/-0 |
| `dev/scripts/checks/check_feature_completion.py` | tooling | +121/-0 |
| `dev/scripts/checks/check_loose_chat_to_typed_lane.py` | tooling | +492/-0 |
| `dev/scripts/checks/check_multi_actor_merge_conflict.py` | tooling | +506/-0 |
| _380 more files trimmed_ | | |

## 4. Quality signals

### Governance review
- total findings: 26
- open: 26
- fixed: 0
- false positives: 0

Recent findings:
- `dogfood.command.reports-cleanup` — `dev/scripts/devctl/commands/reports_cleanup.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.process-cleanup` — `dev/scripts/devctl/commands/process/cleanup.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.agent-mind` — `dev/scripts/devctl/commands/agent_mind/command.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.path-rewrite` — `dev/scripts/devctl/commands/path_rewrite.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.install-git-hooks` — `dev/scripts/devctl/commands/governance/install_git_hooks.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.process-audit` — `dev/scripts/devctl/commands/process/audit.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.probe-report` — `dev/scripts/devctl/commands/probe_report.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.bypass` — `dev/scripts/devctl/commands/bypass/command.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.raw-git` — `dev/scripts/devctl/commands/raw_git.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.guard-run` — `dev/scripts/devctl/commands/guard_run.py` (n/a, verdict=`confirmed_issue`)

### Probe report
- run_state: `missing`
- warnings: 0
- errors: 0
- files scanned: 0
- total hints: 0

## 5. Architecture surface

### Contract ownership map

| Contract | Owner layer | Runtime model | Tokens |
|---|---|---|---|
| `RemoteCommitPipelineContract` | `governance_runtime` | `dev.scripts.devctl.runtime.remote_commit_pipeline_models:RemoteCommitPipelineContract` | snapshot_id, state |
| `ReviewState` | `governance_runtime` | `dev.scripts.devctl.runtime.review_state_models:ReviewState` | snapshot_id, bridge |

### Key documents

- `AGENTS.md`
- `dev/active/MASTER_PLAN.md`
- `dev/active/INDEX.md`
- `dev/guides/AI_GOVERNANCE_PLATFORM.md`

## 6. Reviewer hints — please verify

### Targeted hints

- **risk**: Dependency / security — Delta touches a risk-sensitive surface; verify the routed bundle
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/governance/startup_context.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/review_channel/bridge_render.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_actor_authority.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_commit_targets.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/reviewer_runtime_models.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/vcs/test_governed_executor.py`) — Review contract-level invariants for this file
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/commands/development/collaboration_models.py`) — Commit 58bee30c changed dev/scripts/devctl/commands/development/collaboration_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/platform/adapter_contract_rows.py`) — Commit 58bee30c changed dev/scripts/devctl/platform/adapter_contract_rows.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/platform/coordination_topology_models.py`) — Commit 58bee30c changed dev/scripts/devctl/platform/coordination_topology_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/platform/runtime_contract_rows.py`) — Commit 58bee30c changed dev/scripts/devctl/platform/runtime_contract_rows.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/platform/runtime_guard_violation_contract_rows.py`) — Commit 58bee30c changed dev/scripts/devctl/platform/runtime_guard_violation_contract_rows.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/platform/runtime_identity_contract_rows.py`) — Commit 58bee30c changed dev/scripts/devctl/platform/runtime_identity_contract_rows.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/platform/runtime_state_contract_rows.py`) — Commit 58bee30c changed dev/scripts/devctl/platform/runtime_state_contract_rows.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/review_channel/event_models.py`) — Commit 58bee30c changed dev/scripts/devctl/review_channel/event_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/review_channel/packet_contract.py`) — Commit 58bee30c changed dev/scripts/devctl/review_channel/packet_contract.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/agent_loop_decision_models.py`) — Commit 58bee30c changed dev/scripts/devctl/runtime/agent_loop_decision_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/relaunch_loop_models.py`) — Commit 58bee30c changed dev/scripts/devctl/runtime/relaunch_loop_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/commands/development/orchestration_models.py`) — Commit 90451b8a changed dev/scripts/devctl/commands/development/orchestration_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/reviewer_runtime_models.py`) — Commit 90451b8a changed dev/scripts/devctl/runtime/reviewer_runtime_models.py

### Suggested verification commands

- `python3 dev/scripts/devctl.py check --profile ci`
- `python3 dev/scripts/devctl.py probe-report --format md`
- `python3 dev/scripts/devctl.py docs-check --strict-tooling`
- `python3 dev/scripts/devctl.py governance-review --format md`
- `python3 dev/scripts/devctl.py check-router --format md`

## 7. Reasoning — why these changes landed

### Per-commit rationale

- **`58bee30c`** — Multi-session checkpoint: peer-spawn id-resolution + bounded task-prompt + agent-spawn allow-list
  - Captures accumulated cross-session work under
  - MP-GUARDIR-V4-PHASE-0-6-E-CURRENT-PLAN-AUTHORITY-S1 before role-flipped
  - implementer/reviewer dogfood resumes. Clears
- **`9b321ff7`** — CLAUDE-REV-002 G1+G8: pre_mutation gate + pre-commit hook coverage
  - - check_role_lane_mutation_authority.py gains --mode pre_mutation that inspects git status for impl-file edits without typed authority (G1 per delete_after_ingest.md §A11)
  - - pre-commit-review-snapshot.sh template + installed .git/hooks/pre-commit invoke role-lane gate before commit_permission_hook (G8 partial)
  - - test_install_git_hooks.py asserts the role-lane invocation literal
  - evolution: The cascade absorption window across MP-GUARDIR-V4-PHASE-0-6-E surfaced a quiet authority-promotion path: hand-maintained guides such as `dev/guides/SYSTEM_MAP.md`, `dev/guides/DEVELOPMENT.md`, and `dev/active/INDEX.md`…
- **`7a7afa85`** — Refresh external review snapshot for 90451b8a
  - evolution: The cascade absorption window across MP-GUARDIR-V4-PHASE-0-6-E surfaced a quiet authority-promotion path: hand-maintained guides such as `dev/guides/SYSTEM_MAP.md`, `dev/guides/DEVELOPMENT.md`, and `dev/active/INDEX.md`…
- **`90451b8a`** — Snapshot remaining GuardIR governance repair state
  - evolution: The cascade absorption window across MP-GUARDIR-V4-PHASE-0-6-E surfaced a quiet authority-promotion path: hand-maintained guides such as `dev/guides/SYSTEM_MAP.md`, `dev/guides/DEVELOPMENT.md`, and `dev/active/INDEX.md`…
- **`d1387379`** — Repair current plan packet scheduler
  - evolution: The cascade absorption window across MP-GUARDIR-V4-PHASE-0-6-E surfaced a quiet authority-promotion path: hand-maintained guides such as `dev/guides/SYSTEM_MAP.md`, `dev/guides/DEVELOPMENT.md`, and `dev/active/INDEX.md`…
- **`fda73137`** — Refresh external review snapshot for 41ad2430
- **`41ad2430`** — Land GuardIR v4 canonical plan markdown
- **`62dd7efb`** — Refresh external review snapshot for 3a698ba6
- **`3a698ba6`** — Add packet contract schema fixtures
- **`a55f1fbe`** — Refresh external review snapshot for 52d8835c
- **`52d8835c`** — Bind system map closure plan row
- **`37e29c9a`** — Refresh external review snapshot for d06542d2
- **`d06542d2`** — Bind proof resolver closure row
- **`88cd53ad`** — Refresh external review snapshot for 877ec1c5
- **`877ec1c5`** — Resolve unittest proof test nodes
- **`93bce1be`** — Refresh external review snapshot for 5e431ccc
- **`5e431ccc`** — Bind push proof closure plan row
- **`fd57faa3`** — Refresh external review snapshot for 69c856eb
- **`69c856eb`** — Record push proof closure receipts
- **`20a808a3`** — Refresh external review snapshot for 3e35699c
- **`3e35699c`** — Fix push-owned commit proof receipts
- **`af8ef168`** — Refresh policy-owned generated surfaces for 58a30236
- **`58a30236`** — Refresh external review snapshot for ef1f4365
- **`ef1f4365`** — Record packet attention plan closure
### Active MP scope (from MASTER_PLAN.md)

- contract slice for MP-355 plus the temporary markdown-swarm operating mode
- 2026-05-11 slice 18 fix arc + bilateral protocol consolidation (MP-377):
- 2026-05-14 launch-bootstrap repair family (MP-378): after the relaunch
- `dev/active/review_probes.md` is the review-probe execution spec; implementation tasks stay in this file under `MP-368..MP-375`.
- companion under `MP-376`, not a second main product plan; implementation
- 2026-04-18 `MP-399` governed commit staged-index preservation in `MP-377`
- 2026-04-18 `MP-410` devctl root package-layout relief in `MP-377` scope:
- 2026-04-18 `MP-398` push preflight staged-index exclusion in `MP-377`
- 2026-04-18 `MP-388` consolidation archive pass in `MP-377` scope:
- 2026-04-18 `MP-389` semantic plan-loader core in `MP-377` scope:

## 8. Known gaps and open items

- open governance findings: 26

### Startup advisories
- push_allowed: worktree_clean_and_review_accepted

### Stale warnings
- Stop because nothing remains to push.

### Open gap rows
- **governance_open** (`dev/scripts/devctl/commands/reports_cleanup.py`): dogfood.command.reports-cleanup: Auto-ingested devctl finalization failure rc=1.
repo_path=/Users/jguida941/testing_upgrade/codex-voice
- **governance_open** (`dev/scripts/devctl/commands/process/cleanup.py`): dogfood.command.process-cleanup: Auto-ingested devctl finalization failure rc=1.
repo_path=/Users/jguida941/testing_upgrade/codex-voice
- **governance_open** (`dev/scripts/devctl/commands/agent_mind/command.py`): dogfood.command.agent-mind: Auto-ingested devctl finalization failure rc=1.
repo_path=/Users/jguida941/testing_upgrade/codex-voice
- **governance_open** (`dev/scripts/devctl/commands/path_rewrite.py`): dogfood.command.path-rewrite: Auto-ingested devctl finalization failure rc=1.
repo_path=/Users/jguida941/testing_upgrade/codex-voice
- **governance_open** (`dev/scripts/devctl/commands/governance/install_git_hooks.py`): dogfood.command.install-git-hooks: Auto-ingested devctl finalization failure rc=1.
repo_path=/Users/jguida941/testing_upgrade/codex-voice
- **governance_open** (`dev/scripts/devctl/commands/process/audit.py`): dogfood.command.process-audit: Auto-ingested devctl finalization failure rc=1.
repo_path=/Users/jguida941/testing_upgrade/codex-voice
- **governance_open** (`dev/scripts/devctl/commands/probe_report.py`): dogfood.command.probe-report: Auto-ingested devctl finalization failure rc=1.
repo_path=/Users/jguida941/testing_upgrade/codex-voice
- **governance_open** (`dev/scripts/devctl/commands/bypass/command.py`): dogfood.command.bypass: Auto-ingested devctl finalization failure rc=1.
repo_path=/Users/jguida941/testing_upgrade/codex-voice

---

Projection produced by `devctl review-snapshot`. Generation stamp `snap-9d1ca1265158` binds this file to HEAD `58bee30ca5a3`; if they drift, the freshness guard will fail CI. When the latest commit only refreshes this generated snapshot, the guard accepts this file as bound to that commit's parent code state.
