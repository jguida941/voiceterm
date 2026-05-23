# VoiceTerm — Review Snapshot

> Deterministically generated from typed governance state. Do not edit by hand — rerun `devctl review-snapshot --write`.

## Quick status

- Branch: `extraction/guardir-core-p0-proof-integrity`
- HEAD: `e960567a0df1` — A38 Batch 1: receipt_steward + cadence substrates + SYSTEM_MAP doc-fix
- Tree hash: `613fd3809d6c`
- Generation stamp: `snap-fb65330a2bf5`
- Generated at (UTC): 2026-05-23T22:45:33Z
- Push decision: `run_devctl_push` — push_preconditions_satisfied
- Reviewer mode: `tools_only` (interaction: `local_terminal`)
- Pipeline state: `n/a` (approval: `n/a`)
- Delta since last snapshot: 24 commits, 443 files, +86143/-3197
- Governance findings: 27 open / 0 fixed / 27 total
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
- HEAD SHA: `e960567a0df130405395c66ca76b2756ff728b64`
- HEAD author: Justin Guida
- HEAD timestamp (UTC): 2026-05-23T18:44:34-04:00

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
- publication_backlog: urgent
- publication_guidance: 19 local commit(s) waiting for governed push. Run `python3 dev/scripts/devctl.py push --execute` now.

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

Range: last 24 commits ending at `e960567a0df1`

- commits: 24
- files changed: 443
- insertions: +86143
- deletions: -3197
- bundle classes touched: tooling, docs
- risk add-ons triggered: Dependency / security
- authority surfaces touched: 8 file(s)

### Commits

| # | SHA | Subject | Files | +/- | Bundle | Risk |
|---|---|---|---|---|---|---|
| 1 | `e960567a` | A38 Batch 1: receipt_steward + cadence substrates + SYSTEM_… | 11 | +1879/-16 | tooling |  |
| 2 | `ae977a36` | Refresh external review snapshot for 6490c8c4 | 1 | +66/-48 | tooling |  |
| 3 | `6490c8c4` | A37 Slice C.4 (expand): retire single_agent / dual_agent to… | 18 | +129/-79 | tooling |  |
| 4 | `21821ed2` | evidence.md cases 8-11 + SYSTEM_MAP.md renderer auto-update | 2 | +316/-5 | docs |  |
| 5 | `61e65e93` | A38 amendment + A38.4 TDD-the-SYSTEM_MAP invariants | 2 | +567/-0 | docs |  |
| 6 | `452cfee5` | add evidence.md + semantic-TDD evidence-log forcing function | 3 | +1026/-0 | tooling |  |
| 7 | `0fa30a90` | A37 Slice C.4 (narrow): CONTROL-TOPOLOGY-CUTOVER — `single_… | 4 | +122/-15 | tooling |  |
| 8 | `d35d08ec` | Refresh external review snapshot for 65ad7a4e | 1 | +45/-42 | tooling |  |
| 9 | `65ad7a4e` | A37 Slice C.3: REVIEW-CHANNEL-TYPED — 3 files retire 8 topo… | 5 | +66/-12 | tooling |  |
| 10 | `4389bef4` | Refresh external review snapshot for 889d03ec | 1 | +44/-41 | tooling |  |
| 11 | `889d03ec` | A37 Slice C.0: TOPO-HUNT-BASELINE topology-literal ratchet | 2 | +132/-0 | tooling |  |
| 12 | `3ce6a487` | Refresh external review snapshot for 05eace21 | 1 | +51/-50 | tooling |  |
| 13 | `05eace21` | A37 Phase 0.5: ship devctl role CLI surface (MP377-TYPED-RO… | 12 | +564/-5 | tooling |  |
| 14 | `312b3e45` | Refresh external review snapshot for 7afc813d | 1 | +57/-49 | tooling |  |
| 15 | `7afc813d` | A37 Phase 0 + Pre-0 + Phase 0.x: SemanticTDDRoleSpec + inge… | 9 | +131/-1 | tooling |  |
| 16 | `960135c9` | A37 Phase 0 + Pre-0: SemanticTDDRoleSpec consolidation + in… | 9 | +993/-8 | tooling |  |
| 17 | `eabfd370` | Refresh external review snapshot for 58bee30c | 1 | +120/-98 | tooling |  |
| 18 | `58bee30c` | Multi-session checkpoint: peer-spawn id-resolution + bounde… | 344 | +58347/-1882 | tooling | Dependency / security |
| 19 | `9b321ff7` | CLAUDE-REV-002 G1+G8: pre_mutation gate + pre-commit hook c… | 11 | +2094/-7 | tooling |  |
| 20 | `7a7afa85` | Refresh external review snapshot for 90451b8a | 1 | +19/-19 | tooling |  |
| 21 | `90451b8a` | Snapshot remaining GuardIR governance repair state | 88 | +17323/-697 | tooling |  |
| 22 | `d1387379` | Repair current plan packet scheduler | 17 | +1287/-76 | tooling |  |
| 23 | `fda73137` | Refresh external review snapshot for 41ad2430 | 1 | +49/-47 | tooling |  |
| 24 | `41ad2430` | Land GuardIR v4 canonical plan markdown | 2 | +716/-0 | tooling |  |

### Files

| Path | Bundle | +/- |
|---|---|---|
| `.claude/settings.json` | tooling | +12/-0 |
| `.github/workflows/release_preflight.yml` | tooling | +15/-0 |
| `.github/workflows/tooling_control_plane.yml` | tooling | +45/-0 |
| `AGENTS.md` | docs | +6/-0 |
| `System_Connection_Flowchart.md` | docs | +49/-5 |
| `delete_after_ingest.md` | docs | +5860/-0 |
| `dev/active/INDEX.md` | tooling | +23/-6 |
| `dev/active/MASTER_PLAN.md` | tooling | +204/-24 |
| `dev/active/ai_governance_platform.md` | tooling | +87/-49 |
| `dev/active/contract_orphans_audit.md` | tooling | +58/-0 |
| `dev/active/live_state_semantic_tdd_plan.md` | tooling | +1149/-0 |
| `dev/active/platform_authority_loop.md` | tooling | +12/-12 |
| `dev/active/receipt_steward_lane.md` | tooling | +87/-0 |
| `dev/active/semantic_tdd_lane.md` | tooling | +309/-5 |
| `dev/audits/REVIEW_SNAPSHOT.md` | tooling | +556/-474 |
| `dev/audits/plan_intake/2026-05-20-guardir-lifecycle-recovery-ci-proof-bridge-v4.md` | tooling | +5496/-355 |
| `dev/audits/plan_intake/sha256-manifest.txt` | tooling | +2/-1 |
| `dev/config/git_hooks/pre-commit-review-snapshot.sh` | tooling | +89/-7 |
| `dev/dev/state/ground_truth_probe_receipts.jsonl` | tooling | +1/-0 |
| `dev/guides/AI_GOVERNANCE_PLATFORM.md` | docs | +3/-2 |
| `dev/guides/DEVELOPMENT.md` | docs | +56/-20 |
| `dev/guides/PLATFORM_GUIDE.md` | docs | +872/-12 |
| `dev/guides/SYSTEM_MAP.md` | docs | +62/-59 |
| `dev/history/ENGINEERING_EVOLUTION.md` | tooling | +63/-1 |
| `dev/reports/feature_proof_receipts/7a7afa8520c0d7ca751be3eb889e36b02ea6ebf2.json` | tooling | +48/-0 |
| `dev/scripts/README.md` | tooling | +22/-0 |
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
| _403 more files trimmed_ | | |

## 4. Quality signals

### Governance review
- total findings: 27
- open: 27
- fixed: 0
- false positives: 0

Recent findings:
- `dogfood.command.process-cleanup` — `dev/scripts/devctl/commands/process/cleanup.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.agent-mind` — `dev/scripts/devctl/commands/agent_mind/command.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.path-rewrite` — `dev/scripts/devctl/commands/path_rewrite.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.install-git-hooks` — `dev/scripts/devctl/commands/governance/install_git_hooks.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.process-audit` — `dev/scripts/devctl/commands/process/audit.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.probe-report` — `dev/scripts/devctl/commands/probe_report.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.bypass` — `dev/scripts/devctl/commands/bypass/command.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.raw-git` — `dev/scripts/devctl/commands/raw_git.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.guard-run` — `dev/scripts/devctl/commands/guard_run.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.status` — `dev/scripts/devctl/commands/reporting/status.py` (n/a, verdict=`confirmed_issue`)

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
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/project_governance_contract.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/project_governance_parse.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/governance/startup_context.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/review_channel/bridge_render.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_actor_authority.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_commit_targets.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/reviewer_runtime_models.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/vcs/test_governed_executor.py`) — Review contract-level invariants for this file
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/platform/coordination_snapshot_models.py`) — Commit 6490c8c4 changed dev/scripts/devctl/platform/coordination_snapshot_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/platform/planning_ir_models.py`) — Commit 6490c8c4 changed dev/scripts/devctl/platform/planning_ir_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/work_intake_models.py`) — Commit 6490c8c4 changed dev/scripts/devctl/runtime/work_intake_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/project_governance_contract.py`) — Commit 7afc813d changed dev/scripts/devctl/runtime/project_governance_contract.py
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

- **`e960567a`** — A38 Batch 1: receipt_steward + cadence substrates + SYSTEM_MAP doc-fix
  - Coordinated 3 parallel agents under operator direction "use as many
  - agents as you need." Dependency-DAG batched: all 3 tasks share zero
  - file overlap, executed in parallel, integrated in this single commit.
- **`ae977a36`** — Refresh external review snapshot for 6490c8c4
- **`6490c8c4`** — A37 Slice C.4 (expand): retire single_agent / dual_agent topology literals across 6 parallel carriers + 1 runtime producer
  - Expands the narrow C.4 cutover (which retired `single_agent` only from
  - `ObservedControlTopology` in control_topology.py at commit 0fa30a90) to
  - the PARALLEL topology carriers that independently carried the same
- **`21821ed2`** — evidence.md cases 8-11 + SYSTEM_MAP.md renderer auto-update
  - evidence.md — appends 4 worked-example cases for TDD wins caught after
  - the initial doc-agent sweep. Style matches docs/04-worked-example.md
  - from https://github.com/jguida941/semantic-tdd/tree/main (real code
- **`61e65e93`** — A38 amendment + A38.4 TDD-the-SYSTEM_MAP invariants
  - delete_after_ingest.md — adds A38 amendment with FOUR composable typed
  - substrates surfaced by 3 parallel design agents + operator correction +
  - operator joke-with-serious-intent:
- **`452cfee5`** — add evidence.md + semantic-TDD evidence-log forcing function
  - evidence.md (3371 words) — documents seven concrete cases from today's
  - session where semantic-TDD discipline caught architectural problems
  - that would have shipped otherwise. Each case follows the canonical
- **`0fa30a90`** — A37 Slice C.4 (narrow): CONTROL-TOPOLOGY-CUTOVER — `single_agent` retired from ObservedControlTopology
  - Removes `"single_agent"` from the `ObservedControlTopology` Literal union
  - in `dev/scripts/devctl/runtime/control_topology.py`. The conflation —
  - topology (role-occupancy facts) vs authority mode (which ReviewerMode is
- **`d35d08ec`** — Refresh external review snapshot for 65ad7a4e
- **`65ad7a4e`** — A37 Slice C.3: REVIEW-CHANNEL-TYPED — 3 files retire 8 topology literal branches
  - Migrates raw `"active_dual_agent"` string comparisons to the typed
  - predicate `reviewer_mode_is_active()` (defined in enum-owner
  - runtime/reviewer_mode.py). Baseline ratchet: 44 → 41 files.
- **`4389bef4`** — Refresh external review snapshot for 889d03ec
- **`889d03ec`** — A37 Slice C.0: TOPO-HUNT-BASELINE topology-literal ratchet
  - Establishes the baseline violation count for the canonical Slice C
  - topology-literal retirement (streamed-sprouting-pizza.md). 2a/2b split
  - per the lane discipline: current-safety drift catcher GREEN today,
- **`3ce6a487`** — Refresh external review snapshot for 05eace21
- **`05eace21`** — A37 Phase 0.5: ship devctl role CLI surface (MP377-TYPED-ROLE-MODE-CUSTOMIZATION-S1 S1a)
  - Drives 4 Phase 0.5 RED tests to GREEN. CLI surface live.
- **`312b3e45`** — Refresh external review snapshot for 7afc813d
- **`7afc813d`** — A37 Phase 0 + Pre-0 + Phase 0.x: SemanticTDDRoleSpec + ingest authority + PathRoots state + RED Phase 0.5
  - Lands a comprehensive checkpoint of the A37 (Slice C topology retirement)
  - work, covering Phase 0 + Pre-0 + Phase 0.x. Phase 0.5 CLI implementation
  - RED tests included as the resume-point spec for next session.
- **`960135c9`** — A37 Phase 0 + Pre-0: SemanticTDDRoleSpec consolidation + ingest authority + RED for Phase 0.5
  - Lands Phase 0 + Pre-0 portions of A37 (Slice C topology retirement amendment).
  - Phase 0.5 (devctl role CLI) RED tests included as the resume-point spec.
- **`eabfd370`** — Refresh external review snapshot for 58bee30c
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

- open governance findings: 27

### Startup advisories
- push_allowed: worktree_clean_and_review_accepted

### Stale warnings
- Stop because nothing remains to push.

### Open gap rows
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
- **governance_open** (`dev/scripts/devctl/commands/raw_git.py`): dogfood.command.raw-git: Auto-ingested devctl finalization failure rc=1.
repo_path=/Users/jguida941/testing_upgrade/codex-voice

---

Projection produced by `devctl review-snapshot`. Generation stamp `snap-fb65330a2bf5` binds this file to HEAD `e960567a0df1`; if they drift, the freshness guard will fail CI. When the latest commit only refreshes this generated snapshot, the guard accepts this file as bound to that commit's parent code state.
