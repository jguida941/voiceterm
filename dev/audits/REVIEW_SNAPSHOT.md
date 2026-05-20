# VoiceTerm — Review Snapshot

> Deterministically generated from typed governance state. Do not edit by hand — rerun `devctl review-snapshot --write`.

## Quick status

- Branch: `extraction/guardir-core-p0-proof-integrity`
- HEAD: `52b445b65bdc` — Fix control decision consistency guard routing
- Tree hash: `3ed622240a13`
- Generation stamp: `snap-beb3cdebb442`
- Generated at (UTC): 2026-05-20T01:24:56Z
- Push decision: `run_devctl_push` — push_preconditions_satisfied
- Reviewer mode: `tools_only` (interaction: `local_terminal`)
- Pipeline state: `n/a` (approval: `n/a`)
- Delta since last snapshot: 25 commits, 132 files, +7091/-2042
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
- HEAD SHA: `52b445b65bdc2054b2279690fb7bdc464ab8a8b7`
- HEAD author: Justin Guida
- HEAD timestamp (UTC): 2026-05-19T21:24:32-04:00

## 2. Governance state

### Push decision
- action: `run_devctl_push`
- reason: push_preconditions_satisfied
- push_eligible_now: True
- worktree_clean: True
- staged_path_count: 0
- unstaged_path_count: 0
- next_step_command: `python3 dev/scripts/devctl.py push --execute`
- latest_push_report_state: `blocked` (push_preflight_running)
- publication_backlog: queued
- publication_guidance: 1 local commit(s) waiting for governed push. Run `python3 dev/scripts/devctl.py push --execute` now.

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

Range: last 25 commits ending at `52b445b65bdc`

- commits: 25
- files changed: 132
- insertions: +7091
- deletions: -2042
- bundle classes touched: tooling, docs
- authority surfaces touched: 4 file(s)

### Commits

| # | SHA | Subject | Files | +/- | Bundle | Risk |
|---|---|---|---|---|---|---|
| 1 | `52b445b6` | Fix control decision consistency guard routing | 10 | +224/-12 | tooling |  |
| 2 | `e6f95248` | Refresh external review snapshot for c2f6777d | 1 | +51/-56 | tooling |  |
| 3 | `c2f6777d` | Fix packet attention receipt drainage | 19 | +835/-40 | tooling |  |
| 4 | `6357774a` | Refresh external review snapshot for 42f2629e | 1 | +93/-94 | tooling |  |
| 5 | `42f2629e` | Checkpoint proof integrity and layout repairs | 72 | +3777/-1019 | tooling |  |
| 6 | `36b1e810` | P0 contract connectivity sub-A: 4 missing authority contrac… | 14 | +260/-26 | tooling |  |
| 7 | `94b95813` | Refresh external review snapshot for 101aacd2 | 1 | +52/-49 | tooling |  |
| 8 | `101aacd2` | Bind reviewer-round intake follow-ups | 4 | +74/-47 | tooling |  |
| 9 | `b126e825` | Refresh external review snapshot for 41217fca | 1 | +69/-66 | tooling |  |
| 10 | `41217fca` | Allow pending lifecycle packet focus in multi-agent sync | 12 | +249/-52 | tooling |  |
| 11 | `f869134a` | Refresh external review snapshot for 58d527c1 | 1 | +52/-52 | tooling |  |
| 12 | `58d527c1` | Share optional integer coercion across runtime contracts | 9 | +64/-20 | tooling |  |
| 13 | `4f5974fe` | Refresh external review snapshot for b348c95d | 1 | +55/-55 | tooling |  |
| 14 | `b348c95d` | Split multi-agent communication-only focus helper | 8 | +71/-31 | tooling |  |
| 15 | `fd5ca17e` | Refresh external review snapshot for b2639c99 | 1 | +57/-60 | tooling |  |
| 16 | `b2639c99` | Anchor task-started packet bindings to backfill commit | 5 | +49/-18 | tooling |  |
| 17 | `cc739fa3` | Refresh external review snapshot for eb5ed905 | 1 | +42/-42 | tooling |  |
| 18 | `eb5ed905` | Bind feature-proof receipt finding packet | 3 | +20/-0 | tooling |  |
| 19 | `60b0f15a` | Refresh external review snapshot for 70b81e6a | 1 | +50/-49 | tooling |  |
| 20 | `70b81e6a` | Backfill task-started packet bindings | 5 | +51/-0 | tooling |  |
| 21 | `db755032` | Refresh external review snapshot for 43f7b254 | 1 | +51/-50 | tooling |  |
| 22 | `43f7b254` | Record SLICE-Z ground truth probe receipt | 1 | +1/-0 | tooling |  |
| 23 | `a1b40b4c` | Refresh external review snapshot for 4593576d | 1 | +105/-78 | tooling |  |
| 24 | `4593576d` | SLICE-Z follow-up: align sync guard and docs | 9 | +152/-2 | tooling |  |
| 25 | `bb80f85a` | SLICE-Z repair: slice-counted continuation_anchor full life… | 17 | +587/-124 | tooling |  |

### Files

| Path | Bundle | +/- |
|---|---|---|
| `.github/workflows/release_preflight.yml` | tooling | +3/-0 |
| `.github/workflows/tooling_control_plane.yml` | tooling | +15/-6 |
| `dev/active/MASTER_PLAN.md` | tooling | +123/-0 |
| `dev/active/ai_governance_platform.md` | tooling | +67/-0 |
| `dev/audits/REVIEW_SNAPSHOT.md` | tooling | +838/-813 |
| `dev/config/devctl_repo_policy.json` | tooling | +5/-0 |
| `dev/guides/DEVELOPMENT.md` | docs | +23/-3 |
| `dev/guides/SYSTEM_MAP.md` | docs | +73/-72 |
| `dev/history/ENGINEERING_EVOLUTION.md` | tooling | +186/-0 |
| `dev/scripts/README.md` | tooling | +20/-2 |
| `dev/scripts/checks/check_commit_complete_proof.py` | tooling | +11/-0 |
| `dev/scripts/checks/check_feature_has_proof_receipt.py` | tooling | +10/-302 |
| `dev/scripts/checks/check_no_projection_proof_misuse.py` | tooling | +11/-0 |
| `dev/scripts/checks/check_push_complete_proof.py` | tooling | +11/-0 |
| `dev/scripts/checks/check_substrate_commits_have_applied_plan_row.py` | tooling | +10/-518 |
| `dev/scripts/checks/commit_complete_proof/__init__.py` | tooling | +15/-0 |
| `dev/scripts/checks/commit_complete_proof/command.py` | tooling | +172/-0 |
| `dev/scripts/checks/contract_connectivity/bidirectional.py` | tooling | +89/-0 |
| `dev/scripts/checks/contract_connectivity/models.py` | tooling | +37/-0 |
| `dev/scripts/checks/contract_connectivity/report.py` | tooling | +41/-1 |
| `dev/scripts/checks/contract_connectivity/support.py` | tooling | +42/-3 |
| `dev/scripts/checks/control_decision_consistency/command.py` | tooling | +17/-1 |
| `dev/scripts/checks/feature_has_proof_receipt/__init__.py` | tooling | +1/-0 |
| `dev/scripts/checks/feature_has_proof_receipt/command.py` | tooling | +274/-0 |
| `dev/scripts/checks/git_support/__init__.py` | tooling | +1/-0 |
| `dev/scripts/checks/git_support/range.py` | tooling | +41/-0 |
| `dev/scripts/checks/guard_enforcement_inventory/command.py` | tooling | +0/-4 |
| `dev/scripts/checks/multi_agent_sync/runtime_truth_agent_loop_communication.py` | tooling | +60/-0 |
| `dev/scripts/checks/multi_agent_sync/runtime_truth_agent_loop_instruction.py` | tooling | +37/-28 |
| `dev/scripts/checks/no_projection_proof_misuse/__init__.py` | tooling | +15/-0 |
| `dev/scripts/checks/no_projection_proof_misuse/command.py` | tooling | +235/-0 |
| `dev/scripts/checks/push_complete_proof/__init__.py` | tooling | +15/-0 |
| `dev/scripts/checks/push_complete_proof/command.py` | tooling | +214/-0 |
| `dev/scripts/checks/substrate_commits_have_applied_plan_row/__init__.py` | tooling | +1/-0 |
| `dev/scripts/checks/substrate_commits_have_applied_plan_row/command.py` | tooling | +334/-0 |
| `dev/scripts/checks/substrate_commits_have_applied_plan_row/coverage.py` | tooling | +50/-0 |
| `dev/scripts/checks/substrate_commits_have_applied_plan_row/enforcement.py` | tooling | +30/-0 |
| `dev/scripts/checks/substrate_commits_have_applied_plan_row/jsonl_rows.py` | tooling | +44/-0 |
| `dev/scripts/checks/substrate_commits_have_applied_plan_row/matching.py` | tooling | +13/-0 |
| `dev/scripts/checks/substrate_commits_have_applied_plan_row/path_policy.py` | tooling | +29/-0 |
| _92 more files trimmed_ | | |

## 4. Quality signals

### Governance review
- total findings: 26
- open: 26
- fixed: 0
- false positives: 0

Recent findings:
- `dogfood.command.install-git-hooks` — `dev/scripts/devctl/commands/governance/install_git_hooks.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.relaunch-loop` — `dev/scripts/devctl/commands/relaunch_loop.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.relaunch-loop` — `dev/scripts/devctl/commands/governance/relaunch_loop.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.render-surfaces` — `dev/scripts/devctl/commands/governance/render_surfaces.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.remote-control` — `dev/scripts/devctl/commands/remote_control/command.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.probe-report` — `dev/scripts/devctl/commands/probe_report.py` (n/a, verdict=`confirmed_issue`)
- `role_oriented_packet_inbox` — `dev/scripts/devctl/review_channel/event_reducer_inbox.py` (high, verdict=`confirmed_issue`)
- `dogfood.command.pipeline` — `dev/scripts/devctl/commands/pipeline/command.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.reports-cleanup` — `dev/scripts/devctl/commands/reports_cleanup.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.agent-mind` — `dev/scripts/devctl/commands/agent_mind/command.py` (n/a, verdict=`confirmed_issue`)

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

- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/commands/check/test_check_router.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_commit_phase.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_commit_proof.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/startup_context.py`) — Review contract-level invariants for this file
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/platform/connectivity_registry_models.py`) — Commit 42f2629e changed dev/scripts/devctl/platform/connectivity_registry_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/tests/platform/test_platform_contracts.py`) — Commit 42f2629e changed dev/scripts/devctl/tests/platform/test_platform_contracts.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/review_channel/event_models.py`) — Commit bb80f85a changed dev/scripts/devctl/review_channel/event_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/review_channel/packet_contract.py`) — Commit bb80f85a changed dev/scripts/devctl/review_channel/packet_contract.py

### Suggested verification commands

- `python3 dev/scripts/devctl.py check --profile ci`
- `python3 dev/scripts/devctl.py probe-report --format md`
- `python3 dev/scripts/devctl.py docs-check --strict-tooling`
- `python3 dev/scripts/devctl.py governance-review --format md`
- `python3 dev/scripts/devctl.py check-router --format md`

## 7. Reasoning — why these changes landed

### Per-commit rationale

- **`52b445b6`** — Fix control decision consistency guard routing
  - evolution: The GuardIR extraction checkpoint exposed a live-controller gap: parser and alias parity could pass while the governed `review-channel` path still hid actor-addressed packets, disclosed packet bodies before failing the …
- **`e6f95248`** — Refresh external review snapshot for c2f6777d
  - evolution: The GuardIR extraction checkpoint exposed a live-controller gap: parser and alias parity could pass while the governed `review-channel` path still hid actor-addressed packets, disclosed packet bodies before failing the …
- **`c2f6777d`** — Fix packet attention receipt drainage
  - evolution: The GuardIR extraction checkpoint exposed a live-controller gap: parser and alias parity could pass while the governed `review-channel` path still hid actor-addressed packets, disclosed packet bodies before failing the …
- **`6357774a`** — Refresh external review snapshot for 42f2629e
  - evolution: The GuardIR extraction checkpoint exposed a live-controller gap: parser and alias parity could pass while the governed `review-channel` path still hid actor-addressed packets, disclosed packet bodies before failing the …
- **`42f2629e`** — Checkpoint proof integrity and layout repairs
  - evolution: The GuardIR extraction checkpoint exposed a live-controller gap: parser and alias parity could pass while the governed `review-channel` path still hid actor-addressed packets, disclosed packet bodies before failing the …
- **`36b1e810`** — P0 contract connectivity sub-A: 4 missing authority contract registry rows + SYSTEM_MAP refresh
  - Per codex rev_pkt_4548 task_started (P0 contract connectivity truth source repair).
  - Sub-task A of multi-slice fix - register 4 authority contracts that were missing from
  - dev/state/contract_registry.jsonl despite being declared authority contracts:
  - evolution: The GuardIR extraction checkpoint exposed a live-controller gap: parser and alias parity could pass while the governed `review-channel` path still hid actor-addressed packets, disclosed packet bodies before failing the …
- **`94b95813`** — Refresh external review snapshot for 101aacd2
  - evolution: The GuardIR extraction checkpoint exposed a live-controller gap: parser and alias parity could pass while the governed `review-channel` path still hid actor-addressed packets, disclosed packet bodies before failing the …
- **`101aacd2`** — Bind reviewer-round intake follow-ups
  - evolution: The GuardIR extraction checkpoint exposed a live-controller gap: parser and alias parity could pass while the governed `review-channel` path still hid actor-addressed packets, disclosed packet bodies before failing the …
- **`b126e825`** — Refresh external review snapshot for 41217fca
  - evolution: The GuardIR extraction checkpoint exposed a live-controller gap: parser and alias parity could pass while the governed `review-channel` path still hid actor-addressed packets, disclosed packet bodies before failing the …
- **`41217fca`** — Allow pending lifecycle packet focus in multi-agent sync
  - evolution: The GuardIR extraction checkpoint exposed a live-controller gap: parser and alias parity could pass while the governed `review-channel` path still hid actor-addressed packets, disclosed packet bodies before failing the …
- **`f869134a`** — Refresh external review snapshot for 58d527c1
  - evolution: The GuardIR extraction checkpoint exposed a live-controller gap: parser and alias parity could pass while the governed `review-channel` path still hid actor-addressed packets, disclosed packet bodies before failing the …
- **`58d527c1`** — Share optional integer coercion across runtime contracts
  - evolution: The GuardIR extraction checkpoint exposed a live-controller gap: parser and alias parity could pass while the governed `review-channel` path still hid actor-addressed packets, disclosed packet bodies before failing the …
- **`4f5974fe`** — Refresh external review snapshot for b348c95d
  - evolution: The GuardIR extraction checkpoint exposed a live-controller gap: parser and alias parity could pass while the governed `review-channel` path still hid actor-addressed packets, disclosed packet bodies before failing the …
- **`b348c95d`** — Split multi-agent communication-only focus helper
  - evolution: The GuardIR extraction checkpoint exposed a live-controller gap: parser and alias parity could pass while the governed `review-channel` path still hid actor-addressed packets, disclosed packet bodies before failing the …
- **`fd5ca17e`** — Refresh external review snapshot for b2639c99
  - evolution: The GuardIR extraction checkpoint exposed a live-controller gap: parser and alias parity could pass while the governed `review-channel` path still hid actor-addressed packets, disclosed packet bodies before failing the …
- **`b2639c99`** — Anchor task-started packet bindings to backfill commit
  - evolution: The GuardIR extraction checkpoint exposed a live-controller gap: parser and alias parity could pass while the governed `review-channel` path still hid actor-addressed packets, disclosed packet bodies before failing the …
- **`cc739fa3`** — Refresh external review snapshot for eb5ed905
  - evolution: The GuardIR extraction checkpoint exposed a live-controller gap: parser and alias parity could pass while the governed `review-channel` path still hid actor-addressed packets, disclosed packet bodies before failing the …
- **`eb5ed905`** — Bind feature-proof receipt finding packet
  - evolution: The GuardIR extraction checkpoint exposed a live-controller gap: parser and alias parity could pass while the governed `review-channel` path still hid actor-addressed packets, disclosed packet bodies before failing the …
- **`60b0f15a`** — Refresh external review snapshot for 70b81e6a
  - evolution: The GuardIR extraction checkpoint exposed a live-controller gap: parser and alias parity could pass while the governed `review-channel` path still hid actor-addressed packets, disclosed packet bodies before failing the …
- **`70b81e6a`** — Backfill task-started packet bindings
  - Adds PKT-BIND rows for post-mandate task_started packets via develop ingest-plan with mutation_op=task_started_packet_binding.
  - evolution: The GuardIR extraction checkpoint exposed a live-controller gap: parser and alias parity could pass while the governed `review-channel` path still hid actor-addressed packets, disclosed packet bodies before failing the …
- **`db755032`** — Refresh external review snapshot for 43f7b254
  - evolution: The GuardIR extraction checkpoint exposed a live-controller gap: parser and alias parity could pass while the governed `review-channel` path still hid actor-addressed packets, disclosed packet bodies before failing the …
- **`43f7b254`** — Record SLICE-Z ground truth probe receipt
  - Adds the GroundTruthProbeRunReceipt for the slice-counted continuation anchor repair range.
  - evolution: The GuardIR extraction checkpoint exposed a live-controller gap: parser and alias parity could pass while the governed `review-channel` path still hid actor-addressed packets, disclosed packet bodies before failing the …
- **`a1b40b4c`** — Refresh external review snapshot for 4593576d
  - evolution: The GuardIR extraction checkpoint exposed a live-controller gap: parser and alias parity could pass while the governed `review-channel` path still hid actor-addressed packets, disclosed packet bodies before failing the …
- **`4593576d`** — SLICE-Z follow-up: align sync guard and docs
  - Follow-up to bb80f85a for the live role-flip loop. Allows a communication-only open_packet_body focus to supersede an older plan inbox packet within the same scoped active packet set, and records the slice-counted continuation_anchor contract in durable docs.
  - evolution: The GuardIR extraction checkpoint exposed a live-controller gap: parser and alias parity could pass while the governed `review-channel` path still hid actor-addressed packets, disclosed packet bodies before failing the …
- **`bb80f85a`** — SLICE-Z repair: slice-counted continuation_anchor full lifecycle (block + auto-release)
  - Closes codex rev_pkt_4520 SLICE-Z repair directive (rev_pkt_4519 review_failed of
  - my prior 84d43c50 block-side-only attempt). Role-flip cycle 2: codex orchestrator
  - posted typed verdict + 7 acceptance criteria; this commit lands codex's full
  - evolution: The GuardIR extraction checkpoint exposed a live-controller gap: parser and alias parity could pass while the governed `review-channel` path still hid actor-addressed packets, disclosed packet bodies before failing the …
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
- **governance_open** (`dev/scripts/devctl/commands/governance/install_git_hooks.py`): dogfood.command.install-git-hooks: Auto-ingested devctl finalization failure rc=1.
repo_path=/Users/jguida941/testing_upgrade/codex-voice
- **governance_open** (`dev/scripts/devctl/commands/relaunch_loop.py`): dogfood.command.relaunch-loop: Auto-ingested devctl finalization failure rc=2.
repo_path=/Users/jguida941/testing_upgrade/codex-voice
- **governance_open** (`dev/scripts/devctl/commands/governance/relaunch_loop.py`): dogfood.command.relaunch-loop: Auto-ingested devctl finalization failure rc=2.
repo_path=/Users/jguida941/testing_upgrade/codex-voice
- **governance_open** (`dev/scripts/devctl/commands/governance/render_surfaces.py`): dogfood.command.render-surfaces: Auto-ingested devctl finalization failure rc=1.
repo_path=/Users/jguida941/testing_upgrade/codex-voice
- **governance_open** (`dev/scripts/devctl/commands/remote_control/command.py`): dogfood.command.remote-control: Auto-ingested devctl finalization failure rc=1.
repo_path=/Users/jguida941/testing_upgrade/codex-voice
- **governance_open** (`dev/scripts/devctl/commands/probe_report.py`): dogfood.command.probe-report: Auto-ingested devctl finalization failure rc=1.
repo_path=/Users/jguida941/testing_upgrade/codex-voice
- **governance_open** (`dev/scripts/devctl/review_channel/event_reducer_inbox.py`): role_oriented_packet_inbox: Packet inbox routing is still provider-keyed in several runtime readers. Visibility and consumption must resolve through actor role plus exact session when scoped so provider role switches cannot hide, consume, or drop pending packets.
- **governance_open** (`dev/scripts/devctl/commands/pipeline/command.py`): dogfood.command.pipeline: Auto-ingested devctl finalization failure rc=1.
repo_path=/Users/jguida941/testing_upgrade/codex-voice

---

Projection produced by `devctl review-snapshot`. Generation stamp `snap-beb3cdebb442` binds this file to HEAD `52b445b65bdc`; if they drift, the freshness guard will fail CI. When the latest commit only refreshes this generated snapshot, the guard accepts this file as bound to that commit's parent code state.
