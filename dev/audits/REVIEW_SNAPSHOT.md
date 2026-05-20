# VoiceTerm — Review Snapshot

> Deterministically generated from typed governance state. Do not edit by hand — rerun `devctl review-snapshot --write`.

## Quick status

- Branch: `extraction/guardir-core-p0-proof-integrity`
- HEAD: `a1f4a834352a` — Refresh external review snapshot for 6f94e606
- Tree hash: `7c72d9553b17`
- Generation stamp: `snap-eede747cc8d0`
- Generated at (UTC): 2026-05-20T05:23:24Z
- Push decision: `await_checkpoint` — staged_index_present
- Reviewer mode: `tools_only` (interaction: `local_terminal`)
- Pipeline state: `n/a` (approval: `n/a`)
- Delta since last snapshot: 24 commits, 44 files, +3014/-1398
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
- HEAD SHA: `a1f4a834352a57cf0075e09b6a0aff26e89493d5`
- HEAD author: Justin Guida
- HEAD timestamp (UTC): 2026-05-20T00:49:22-04:00

## 2. Governance state

### Push decision
- action: `await_checkpoint`
- reason: staged_index_present
- push_eligible_now: False
- worktree_clean: False
- staged_path_count: 5
- unstaged_path_count: 0
- next_step_command: `n/a`
- latest_push_report_state: `blocked` (validation_failed)
- publication_backlog: urgent
- publication_guidance: 22 local commit(s) waiting for governed push once the current slice is checkpoint-clean.

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
- advisory: `checkpoint_before_continue` — dirty_after_local_checkpoint

## 3. Delta — what changed since the previous snapshot

Range: last 24 commits ending at `a1f4a834352a`

- commits: 24
- files changed: 44
- insertions: +3014
- deletions: -1398
- bundle classes touched: tooling, docs
- authority surfaces touched: 6 file(s)

### Commits

| # | SHA | Subject | Files | +/- | Bundle | Risk |
|---|---|---|---|---|---|---|
| 1 | `a1f4a834` | Refresh external review snapshot for 6f94e606 | 1 | +62/-63 | tooling |  |
| 2 | `6f94e606` | Record contract connectivity plan closure | 5 | +51/-48 | tooling |  |
| 3 | `200af3e3` | Refresh external review snapshot for bad81bdf | 1 | +86/-95 | tooling |  |
| 4 | `bad81bdf` | Gate contract connectivity debt through typed plans | 9 | +277/-55 | tooling |  |
| 5 | `d480a306` | Refresh external review snapshot for b5214fdd | 1 | +48/-49 | tooling |  |
| 6 | `b5214fdd` | Record plan closure for proof ledger guard | 5 | +55/-52 | tooling |  |
| 7 | `acd9bd92` | Refresh external review snapshot for c023e7bc | 1 | +51/-52 | tooling |  |
| 8 | `c023e7bc` | Classify plan closure receipts as proof ledger | 7 | +82/-58 | tooling |  |
| 9 | `5fb57f5a` | Refresh external review snapshot for ee079435 | 1 | +52/-52 | tooling |  |
| 10 | `ee079435` | Scope feature proof enforcement to source commits | 3 | +171/-56 | tooling |  |
| 11 | `1489c777` | Refresh external review snapshot for 01290117 | 1 | +48/-48 | tooling |  |
| 12 | `01290117` | Backfill packet binding continuity receipts | 4 | +76/-62 | tooling |  |
| 13 | `3486373d` | Refresh external review snapshot for 30211cd7 | 1 | +51/-51 | tooling |  |
| 14 | `30211cd7` | Record ground truth probe receipt | 2 | +52/-51 | tooling |  |
| 15 | `b8901376` | Refresh external review snapshot for 3b60f794 | 1 | +53/-53 | tooling |  |
| 16 | `3b60f794` | Surface contract connectivity debt at startup | 9 | +533/-54 | tooling |  |
| 17 | `465a3e15` | Refresh external review snapshot for 5835341d | 1 | +60/-62 | tooling |  |
| 18 | `5835341d` | Keep git mutation proof store generated | 6 | +129/-52 | tooling |  |
| 19 | `22dbba15` | Refresh external review snapshot for 38e86f1d | 1 | +55/-58 | tooling |  |
| 20 | `38e86f1d` | Fix managed receipt commit proof coverage | 7 | +442/-121 | tooling |  |
| 21 | `96e66452` | Refresh external review snapshot for 682174e9 | 1 | +64/-67 | tooling |  |
| 22 | `682174e9` | Tighten portable proof guard routing | 11 | +245/-74 | tooling |  |
| 23 | `8b6424e8` | Refresh external review snapshot for 52b445b6 | 1 | +47/-53 | tooling |  |
| 24 | `52b445b6` | Fix control decision consistency guard routing | 10 | +224/-12 | tooling |  |

### Files

| Path | Bundle | +/- |
|---|---|---|
| `.github/workflows/release_preflight.yml` | tooling | +2/-2 |
| `.github/workflows/tooling_control_plane.yml` | tooling | +8/-8 |
| `dev/active/MASTER_PLAN.md` | tooling | +2/-0 |
| `dev/audits/REVIEW_SNAPSHOT.md` | tooling | +1249/-1276 |
| `dev/guides/SYSTEM_MAP.md` | docs | +1/-1 |
| `dev/scripts/checks/contract_connectivity/models.py` | tooling | +22/-0 |
| `dev/scripts/checks/contract_connectivity/planned_debt.py` | tooling | +58/-0 |
| `dev/scripts/checks/contract_connectivity/report.py` | tooling | +42/-0 |
| `dev/scripts/checks/contract_connectivity/support.py` | tooling | +34/-8 |
| `dev/scripts/checks/control_decision_consistency/command.py` | tooling | +17/-1 |
| `dev/scripts/checks/feature_has_proof_receipt/command.py` | tooling | +70/-1 |
| `dev/scripts/checks/git_support/range.py` | tooling | +62/-2 |
| `dev/scripts/checks/guard_enforcement_inventory/command.py` | tooling | +0/-4 |
| `dev/scripts/devctl/bundles/registry.py` | tooling | +3/-8 |
| `dev/scripts/devctl/commands/check/router_range.py` | tooling | +16/-0 |
| `dev/scripts/devctl/commands/vcs/governed_executor_commit_phase.py` | tooling | +16/-51 |
| `dev/scripts/devctl/commands/vcs/governed_executor_commit_proof.py` | tooling | +34/-20 |
| `dev/scripts/devctl/commands/vcs/governed_executor_commit_receipts.py` | tooling | +180/-0 |
| `dev/scripts/devctl/commands/vcs/governed_executor_stage_index.py` | tooling | +50/-0 |
| `dev/scripts/devctl/context_graph/quality_signal_render.py` | tooling | +45/-0 |
| `dev/scripts/devctl/quality_policy/defaults.py` | tooling | +6/-0 |
| `dev/scripts/devctl/runtime/agent_loop_decision_builder.py` | tooling | +27/-0 |
| `dev/scripts/devctl/runtime/agent_loop_policy_proof.py` | tooling | +8/-0 |
| `dev/scripts/devctl/runtime/control_decision_consistency.py` | tooling | +115/-1 |
| `dev/scripts/devctl/runtime/git_mutation_proof_receipt.py` | tooling | +29/-3 |
| `dev/scripts/devctl/runtime/startup_signal_contract_connectivity.py` | tooling | +278/-0 |
| `dev/scripts/devctl/runtime/startup_signals.py` | tooling | +36/-0 |
| `dev/scripts/devctl/tests/checks/contract_connectivity/test_check_contract_connectivity.py` | tooling | +69/-0 |
| `dev/scripts/devctl/tests/checks/test_check_feature_has_proof_receipt.py` | tooling | +48/-0 |
| `dev/scripts/devctl/tests/checks/test_check_git_mutation_proof.py` | tooling | +45/-0 |
| `dev/scripts/devctl/tests/commands/check/test_check_router.py` | tooling | +40/-0 |
| `dev/scripts/devctl/tests/context_graph/test_context_graph.py` | tooling | +20/-0 |
| `dev/scripts/devctl/tests/governance/test_bundle_registry.py` | tooling | +21/-0 |
| `dev/scripts/devctl/tests/runtime/test_commit_receipt.py` | tooling | +131/-0 |
| `dev/scripts/devctl/tests/runtime/test_control_decision_consistency.py` | tooling | +43/-0 |
| `dev/scripts/devctl/tests/runtime/test_startup_signals.py` | tooling | +99/-1 |
| `dev/scripts/devctl/tests/vcs/test_governed_executor.py` | tooling | +26/-0 |
| `dev/scripts/devctl/tests/vcs/test_push_report.py` | tooling | +2/-2 |
| `dev/state/git_mutation_proof_receipts.jsonl` | tooling | +2/-2 |
| `dev/state/ground_truth_probe_receipts.jsonl` | tooling | +1/-0 |
| _4 more files trimmed_ | | |

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

- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_stage_index.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/vcs/test_governed_executor.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_commit_phase.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_commit_proof.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_commit_receipts.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/commands/check/test_check_router.py`) — Review contract-level invariants for this file

### Suggested verification commands

- `python3 dev/scripts/devctl.py check --profile ci`
- `python3 dev/scripts/devctl.py probe-report --format md`
- `python3 dev/scripts/devctl.py docs-check --strict-tooling`
- `python3 dev/scripts/devctl.py governance-review --format md`
- `python3 dev/scripts/devctl.py check-router --format md`

## 7. Reasoning — why these changes landed

### Per-commit rationale

- **`a1f4a834`** — Refresh external review snapshot for 6f94e606
- **`6f94e606`** — Record contract connectivity plan closure
- **`200af3e3`** — Refresh external review snapshot for bad81bdf
- **`bad81bdf`** — Gate contract connectivity debt through typed plans
- **`d480a306`** — Refresh external review snapshot for b5214fdd
- **`b5214fdd`** — Record plan closure for proof ledger guard
- **`acd9bd92`** — Refresh external review snapshot for c023e7bc
- **`c023e7bc`** — Classify plan closure receipts as proof ledger
- **`5fb57f5a`** — Refresh external review snapshot for ee079435
  - evolution: The GuardIR extraction checkpoint exposed a live-controller gap: parser and alias parity could pass while the governed `review-channel` path still hid actor-addressed packets, disclosed packet bodies before failing the …
- **`ee079435`** — Scope feature proof enforcement to source commits
  - evolution: The GuardIR extraction checkpoint exposed a live-controller gap: parser and alias parity could pass while the governed `review-channel` path still hid actor-addressed packets, disclosed packet bodies before failing the …
- **`1489c777`** — Refresh external review snapshot for 01290117
  - evolution: The GuardIR extraction checkpoint exposed a live-controller gap: parser and alias parity could pass while the governed `review-channel` path still hid actor-addressed packets, disclosed packet bodies before failing the …
- **`01290117`** — Backfill packet binding continuity receipts
  - evolution: The GuardIR extraction checkpoint exposed a live-controller gap: parser and alias parity could pass while the governed `review-channel` path still hid actor-addressed packets, disclosed packet bodies before failing the …
- **`3486373d`** — Refresh external review snapshot for 30211cd7
  - evolution: The GuardIR extraction checkpoint exposed a live-controller gap: parser and alias parity could pass while the governed `review-channel` path still hid actor-addressed packets, disclosed packet bodies before failing the …
- **`30211cd7`** — Record ground truth probe receipt
  - evolution: The GuardIR extraction checkpoint exposed a live-controller gap: parser and alias parity could pass while the governed `review-channel` path still hid actor-addressed packets, disclosed packet bodies before failing the …
- **`b8901376`** — Refresh external review snapshot for 3b60f794
  - evolution: The GuardIR extraction checkpoint exposed a live-controller gap: parser and alias parity could pass while the governed `review-channel` path still hid actor-addressed packets, disclosed packet bodies before failing the …
- **`3b60f794`** — Surface contract connectivity debt at startup
  - evolution: The GuardIR extraction checkpoint exposed a live-controller gap: parser and alias parity could pass while the governed `review-channel` path still hid actor-addressed packets, disclosed packet bodies before failing the …
- **`465a3e15`** — Refresh external review snapshot for 5835341d
  - evolution: The GuardIR extraction checkpoint exposed a live-controller gap: parser and alias parity could pass while the governed `review-channel` path still hid actor-addressed packets, disclosed packet bodies before failing the …
- **`5835341d`** — Keep git mutation proof store generated
  - evolution: The GuardIR extraction checkpoint exposed a live-controller gap: parser and alias parity could pass while the governed `review-channel` path still hid actor-addressed packets, disclosed packet bodies before failing the …
- **`22dbba15`** — Refresh external review snapshot for 38e86f1d
  - evolution: The GuardIR extraction checkpoint exposed a live-controller gap: parser and alias parity could pass while the governed `review-channel` path still hid actor-addressed packets, disclosed packet bodies before failing the …
- **`38e86f1d`** — Fix managed receipt commit proof coverage
  - evolution: The GuardIR extraction checkpoint exposed a live-controller gap: parser and alias parity could pass while the governed `review-channel` path still hid actor-addressed packets, disclosed packet bodies before failing the …
- **`96e66452`** — Refresh external review snapshot for 682174e9
  - evolution: The GuardIR extraction checkpoint exposed a live-controller gap: parser and alias parity could pass while the governed `review-channel` path still hid actor-addressed packets, disclosed packet bodies before failing the …
- **`682174e9`** — Tighten portable proof guard routing
  - evolution: The GuardIR extraction checkpoint exposed a live-controller gap: parser and alias parity could pass while the governed `review-channel` path still hid actor-addressed packets, disclosed packet bodies before failing the …
- **`8b6424e8`** — Refresh external review snapshot for 52b445b6
  - evolution: The GuardIR extraction checkpoint exposed a live-controller gap: parser and alias parity could pass while the governed `review-channel` path still hid actor-addressed packets, disclosed packet bodies before failing the …
- **`52b445b6`** — Fix control decision consistency guard routing
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
- checkpoint_before_continue: dirty_after_local_checkpoint

### Stale warnings
- Relaunch the reviewer loop immediately.

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

Projection produced by `devctl review-snapshot`. Generation stamp `snap-eede747cc8d0` binds this file to HEAD `a1f4a834352a`; if they drift, the freshness guard will fail CI. When the latest commit only refreshes this generated snapshot, the guard accepts this file as bound to that commit's parent code state.
