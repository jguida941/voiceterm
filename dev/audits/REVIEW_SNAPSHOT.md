# VoiceTerm — Review Snapshot

> Deterministically generated from typed governance state. Do not edit by hand — rerun `devctl review-snapshot --write`.

## Quick status

- Branch: `feature/governance-quality-sweep`
- HEAD: `2db48c12a7fc` — Record rev_pkt_3968 plan binding
- Tree hash: `48300e73c0cd`
- Generation stamp: `snap-81dfbe1f4e62`
- Generated at (UTC): 2026-05-13T22:17:53Z
- Push decision: `run_devctl_push` — push_preconditions_satisfied
- Reviewer mode: `single_agent` (interaction: `remote_control`)
- Pipeline state: `n/a` (approval: `n/a`)
- Delta since last snapshot: 24 commits, 111 files, +4730/-959
- Governance findings: 43 open / 0 fixed / 43 total
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
- Current branch: `feature/governance-quality-sweep`
- HEAD SHA: `2db48c12a7fcb25c02b84b2e1217745de38e2c9a`
- HEAD author: Justin Guida
- HEAD timestamp (UTC): 2026-05-13T18:17:18-04:00

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
- reviewer_mode: `single_agent`
- reviewer_freshness: unknown
- reviewer_publish_clear: True
- interaction_mode: `remote_control`

### Remote commit pipeline
- state: `n/a`
- approval_state: `n/a`

### Work intake
- active plan: **AI Governance Platform Plan**
- plan path: `dev/active/ai_governance_platform.md`
- active MP scope: `MP-377`
- advisory: `push_allowed` — worktree_clean_and_review_accepted

## 3. Delta — what changed since the previous snapshot

Range: last 24 commits ending at `2db48c12a7fc`

- commits: 24
- files changed: 111
- insertions: +4730
- deletions: -959
- bundle classes touched: tooling, docs
- authority surfaces touched: 9 file(s)

### Commits

| # | SHA | Subject | Files | +/- | Bundle | Risk |
|---|---|---|---|---|---|---|
| 1 | `2db48c12` | Record rev_pkt_3968 plan binding | 2 | +2/-0 | tooling |  |
| 2 | `1e0ceffd` | Refresh external review snapshot for 94d2df5d | 2 | +68/-62 | docs |  |
| 3 | `94d2df5d` | Add delivery modes to governance runtime | 23 | +499/-78 | tooling |  |
| 4 | `66919658` | Refresh external review snapshot for 1cc7d657 | 2 | +59/-56 | docs |  |
| 5 | `1cc7d657` | Fix stale pending packet blocker normalization | 8 | +84/-19 | tooling |  |
| 6 | `0b7707c9` | Refresh external review snapshot for 35b5131c | 2 | +64/-61 | docs |  |
| 7 | `35b5131c` | Phase 8: add receipt state evidence | 18 | +352/-55 | tooling |  |
| 8 | `9a3ae526` | Refresh external review snapshot for 4ff12daa | 2 | +70/-71 | docs |  |
| 9 | `4ff12daa` | Phase 7: add governed transition verifier | 25 | +854/-2 | tooling |  |
| 10 | `72f2b85b` | Refresh external review snapshot for f9804b01 | 2 | +59/-59 | docs |  |
| 11 | `f9804b01` | Phase 1.5: add typed ID wrappers | 12 | +223/-8 | tooling |  |
| 12 | `6571e026` | Refresh external review snapshot for cdd7c805 | 2 | +68/-67 | docs |  |
| 13 | `cdd7c805` | Phase C: add typestate result cases | 20 | +706/-79 | tooling |  |
| 14 | `5237713c` | Refresh external review snapshot for be3f8650 | 2 | +60/-59 | docs |  |
| 15 | `be3f8650` | Phase 5: add governed transition registry | 46 | +1045/-4 | tooling |  |
| 16 | `2f4b9058` | Refresh external review snapshot for 25335b5b | 2 | +56/-56 | docs |  |
| 17 | `25335b5b` | Record packet attention refinement plan binding | 2 | +2/-0 | tooling |  |
| 18 | `7e7c1ecf` | Refresh external review snapshot for 1676e5cc | 2 | +49/-49 | docs |  |
| 19 | `1676e5cc` | Phase A: add lifecycle graph edge kinds | 4 | +86/-8 | tooling |  |
| 20 | `667a9959` | Refresh external review snapshot for e73ef5c4 | 2 | +51/-51 | docs |  |
| 21 | `e73ef5c4` | Phase B: extract reusable receipt state gate | 5 | +111/-8 | tooling |  |
| 22 | `42c692e6` | Refresh external review snapshot for 6097fb64 | 2 | +52/-53 | docs |  |
| 23 | `6097fb64` | Phase 1: enable strict type checking config | 5 | +59/-3 | tooling |  |
| 24 | `11ac15c3` | Refresh external review snapshot for 804d4738 | 2 | +51/-51 | docs |  |

### Files

| Path | Bundle | +/- |
|---|---|---|
| `.github/workflows/release_preflight.yml` | tooling | +1/-0 |
| `.github/workflows/tooling_control_plane.yml` | tooling | +3/-0 |
| `bridge.md` | docs | +45/-45 |
| `dev/active/MASTER_PLAN.md` | tooling | +53/-0 |
| `dev/active/ai_governance_platform.md` | tooling | +188/-1 |
| `dev/audits/REVIEW_SNAPSHOT.md` | tooling | +662/-650 |
| `dev/guides/DEVELOPMENT.md` | docs | +57/-0 |
| `dev/guides/SYSTEM_MAP.md` | docs | +9/-9 |
| `dev/history/ENGINEERING_EVOLUTION.md` | tooling | +147/-0 |
| `dev/scripts/README.md` | tooling | +52/-0 |
| `dev/scripts/checks/check_governed_transitions.py` | tooling | +12/-0 |
| `dev/scripts/checks/governed_transitions/__init__.py` | tooling | +1/-0 |
| `dev/scripts/checks/governed_transitions/command.py` | tooling | +93/-0 |
| `dev/scripts/checks/governed_transitions/graph.py` | tooling | +29/-0 |
| `dev/scripts/checks/governed_transitions/graph_build.py` | tooling | +168/-0 |
| `dev/scripts/checks/governed_transitions/ids.py` | tooling | +25/-0 |
| `dev/scripts/checks/governed_transitions/models.py` | tooling | +67/-0 |
| `dev/scripts/checks/governed_transitions/render.py` | tooling | +47/-0 |
| `dev/scripts/checks/governed_transitions/shape.py` | tooling | +63/-0 |
| `dev/scripts/checks/governed_transitions/walks.py` | tooling | +107/-0 |
| `dev/scripts/devctl/approval_mode.py` | tooling | +20/-8 |
| `dev/scripts/devctl/bundles/registry.py` | tooling | +1/-0 |
| `dev/scripts/devctl/commands/development/lifecycle_commands.py` | tooling | +7/-3 |
| `dev/scripts/devctl/commands/governance/startup_context_advisory_coherence.py` | tooling | +2/-0 |
| `dev/scripts/devctl/commands/vcs/governed_executor_push_result.py` | tooling | +50/-55 |
| `dev/scripts/devctl/commands/vcs/governed_executor_validation.py` | tooling | +36/-6 |
| `dev/scripts/devctl/commands/vcs/push_result_typestate.py` | tooling | +97/-0 |
| `dev/scripts/devctl/context_graph/models.py` | tooling | +18/-6 |
| `dev/scripts/devctl/governance/draft_policy_scan.py` | tooling | +2/-0 |
| `dev/scripts/devctl/governance/script_catalog_registry.py` | tooling | +1/-0 |
| `dev/scripts/devctl/platform/runtime_identity_contract_rows.py` | tooling | +2/-33 |
| `dev/scripts/devctl/platform/runtime_identity_contract_rows_commit.py` | tooling | +65/-0 |
| `dev/scripts/devctl/platform/runtime_state_contract_rows.py` | tooling | +2/-0 |
| `dev/scripts/devctl/platform/runtime_state_contract_rows_bypass_lifecycle.py` | tooling | +13/-0 |
| `dev/scripts/devctl/platform/runtime_state_contract_rows_pipeline.py` | tooling | +15/-0 |
| `dev/scripts/devctl/platform/runtime_state_contract_rows_review.py` | tooling | +14/-0 |
| `dev/scripts/devctl/platform/runtime_state_contract_rows_transitions.py` | tooling | +59/-0 |
| `dev/scripts/devctl/platform/surface_state_contract_rows.py` | tooling | +1/-0 |
| `dev/scripts/devctl/runtime/agent_loop_decision.py` | tooling | +37/-21 |
| `dev/scripts/devctl/runtime/agent_loop_operator_override.py` | tooling | +4/-2 |
| _71 more files trimmed_ | | |

## 4. Quality signals

### Governance review
- total findings: 43
- open: 43
- fixed: 0
- false positives: 0

Recent findings:
- `packet.durable_ingestion_before_ttl` — `dev/scripts/devctl/runtime/packet_carry_forward.py` (critical, verdict=`confirmed_issue`)
- `agent_sync.ambiguity_projection` — `dev/scripts/checks/multi_agent_sync` (high, verdict=`confirmed_issue`)
- `review_channel.command_latency_under_fanout` — `dev/scripts/devctl/commands/review_channel` (high, verdict=`confirmed_issue`)
- `work_board.rows_duplication` — `dev/scripts/devctl/runtime/agent_dispatch_router.py` (high, verdict=`confirmed_issue`)
- `dogfood.command.pipeline` — `dev/scripts/devctl/commands/pipeline/command.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.process-audit` — `dev/scripts/devctl/commands/process/audit.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.reports-cleanup` — `dev/scripts/devctl/commands/reports_cleanup.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.test-python` — `dev/scripts/devctl/commands/python_tests.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.test-python` — `dev/scripts/devctl/commands/python_test_runner/command.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.process-cleanup` — `dev/scripts/devctl/commands/process/cleanup.py` (n/a, verdict=`confirmed_issue`)

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

- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/project_governance.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/project_governance_contract.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/project_governance_parse.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/startup_context.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/runtime/test_project_governance.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/runtime/test_startup_context.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_validation.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/vcs/test_governed_executor.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_push_result.py`) — Review contract-level invariants for this file
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/platform/surface_state_contract_rows.py`) — Commit 94d2df5d changed dev/scripts/devctl/platform/surface_state_contract_rows.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/project_governance_contract.py`) — Commit 94d2df5d changed dev/scripts/devctl/runtime/project_governance_contract.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/platform/runtime_identity_contract_rows.py`) — Commit 35b5131c changed dev/scripts/devctl/platform/runtime_identity_contract_rows.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/validation_contracts.py`) — Commit 35b5131c changed dev/scripts/devctl/runtime/validation_contracts.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/tests/platform/test_platform_contracts.py`) — Commit 35b5131c changed dev/scripts/devctl/tests/platform/test_platform_contracts.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/platform/runtime_state_contract_rows.py`) — Commit be3f8650 changed dev/scripts/devctl/platform/runtime_state_contract_rows.py

### Suggested verification commands

- `python3 dev/scripts/devctl.py check --profile ci`
- `python3 dev/scripts/devctl.py probe-report --format md`
- `python3 dev/scripts/devctl.py docs-check --strict-tooling`
- `python3 dev/scripts/devctl.py governance-review --format md`
- `python3 dev/scripts/devctl.py check-router --format md`

## 7. Reasoning — why these changes landed

### Per-commit rationale

- **`2db48c12`** — Record rev_pkt_3968 plan binding
  - evolution: Live MP-377 remote-control dogfood exposed four small friction points that were making the typed loop slower and harder to read: repeated check-router policy loads, governed-push preflight not forwarding worker parallel…
- **`1e0ceffd`** — Refresh external review snapshot for 94d2df5d
  - evolution: Live MP-377 remote-control dogfood exposed four small friction points that were making the typed loop slower and harder to read: repeated check-router policy loads, governed-push preflight not forwarding worker parallel…
- **`94d2df5d`** — Add delivery modes to governance runtime
  - evolution: Live MP-377 remote-control dogfood exposed four small friction points that were making the typed loop slower and harder to read: repeated check-router policy loads, governed-push preflight not forwarding worker parallel…
- **`66919658`** — Refresh external review snapshot for 1cc7d657
  - evolution: Live MP-377 remote-control dogfood exposed four small friction points that were making the typed loop slower and harder to read: repeated check-router policy loads, governed-push preflight not forwarding worker parallel…
- **`1cc7d657`** — Fix stale pending packet blocker normalization
  - evolution: Live MP-377 remote-control dogfood exposed four small friction points that were making the typed loop slower and harder to read: repeated check-router policy loads, governed-push preflight not forwarding worker parallel…
- **`0b7707c9`** — Refresh external review snapshot for 35b5131c
  - evolution: Live MP-377 remote-control dogfood exposed four small friction points that were making the typed loop slower and harder to read: repeated check-router policy loads, governed-push preflight not forwarding worker parallel…
- **`35b5131c`** — Phase 8: add receipt state evidence
  - evolution: Live MP-377 remote-control dogfood exposed four small friction points that were making the typed loop slower and harder to read: repeated check-router policy loads, governed-push preflight not forwarding worker parallel…
- **`9a3ae526`** — Refresh external review snapshot for 4ff12daa
  - evolution: Live MP-377 remote-control dogfood exposed four small friction points that were making the typed loop slower and harder to read: repeated check-router policy loads, governed-push preflight not forwarding worker parallel…
- **`4ff12daa`** — Phase 7: add governed transition verifier
  - evolution: Live MP-377 remote-control dogfood exposed four small friction points that were making the typed loop slower and harder to read: repeated check-router policy loads, governed-push preflight not forwarding worker parallel…
- **`72f2b85b`** — Refresh external review snapshot for f9804b01
  - evolution: Live MP-377 remote-control dogfood exposed four small friction points that were making the typed loop slower and harder to read: repeated check-router policy loads, governed-push preflight not forwarding worker parallel…
- **`f9804b01`** — Phase 1.5: add typed ID wrappers
  - evolution: Live MP-377 remote-control dogfood exposed four small friction points that were making the typed loop slower and harder to read: repeated check-router policy loads, governed-push preflight not forwarding worker parallel…
- **`6571e026`** — Refresh external review snapshot for cdd7c805
  - evolution: Live MP-377 remote-control dogfood exposed four small friction points that were making the typed loop slower and harder to read: repeated check-router policy loads, governed-push preflight not forwarding worker parallel…
- **`cdd7c805`** — Phase C: add typestate result cases
  - evolution: Live MP-377 remote-control dogfood exposed four small friction points that were making the typed loop slower and harder to read: repeated check-router policy loads, governed-push preflight not forwarding worker parallel…
- **`5237713c`** — Refresh external review snapshot for be3f8650
  - evolution: Live MP-377 remote-control dogfood exposed four small friction points that were making the typed loop slower and harder to read: repeated check-router policy loads, governed-push preflight not forwarding worker parallel…
- **`be3f8650`** — Phase 5: add governed transition registry
  - evolution: Live MP-377 remote-control dogfood exposed four small friction points that were making the typed loop slower and harder to read: repeated check-router policy loads, governed-push preflight not forwarding worker parallel…
- **`2f4b9058`** — Refresh external review snapshot for 25335b5b
  - evolution: Live MP-377 remote-control dogfood exposed four small friction points that were making the typed loop slower and harder to read: repeated check-router policy loads, governed-push preflight not forwarding worker parallel…
- **`25335b5b`** — Record packet attention refinement plan binding
  - evolution: Live MP-377 remote-control dogfood exposed four small friction points that were making the typed loop slower and harder to read: repeated check-router policy loads, governed-push preflight not forwarding worker parallel…
- **`7e7c1ecf`** — Refresh external review snapshot for 1676e5cc
  - evolution: Live MP-377 remote-control dogfood exposed four small friction points that were making the typed loop slower and harder to read: repeated check-router policy loads, governed-push preflight not forwarding worker parallel…
- **`1676e5cc`** — Phase A: add lifecycle graph edge kinds
  - evolution: Live MP-377 remote-control dogfood exposed four small friction points that were making the typed loop slower and harder to read: repeated check-router policy loads, governed-push preflight not forwarding worker parallel…
- **`667a9959`** — Refresh external review snapshot for e73ef5c4
  - evolution: Live MP-377 remote-control dogfood exposed four small friction points that were making the typed loop slower and harder to read: repeated check-router policy loads, governed-push preflight not forwarding worker parallel…
- **`e73ef5c4`** — Phase B: extract reusable receipt state gate
  - evolution: Live MP-377 remote-control dogfood exposed four small friction points that were making the typed loop slower and harder to read: repeated check-router policy loads, governed-push preflight not forwarding worker parallel…
- **`42c692e6`** — Refresh external review snapshot for 6097fb64
  - evolution: Live MP-377 remote-control dogfood exposed four small friction points that were making the typed loop slower and harder to read: repeated check-router policy loads, governed-push preflight not forwarding worker parallel…
- **`6097fb64`** — Phase 1: enable strict type checking config
  - evolution: Live MP-377 remote-control dogfood exposed four small friction points that were making the typed loop slower and harder to read: repeated check-router policy loads, governed-push preflight not forwarding worker parallel…
- **`11ac15c3`** — Refresh external review snapshot for 804d4738
  - evolution: Live MP-377 remote-control dogfood exposed four small friction points that were making the typed loop slower and harder to read: repeated check-router policy loads, governed-push preflight not forwarding worker parallel…
### Active MP scope (from MASTER_PLAN.md)

- contract slice for MP-355 plus the temporary markdown-swarm operating mode
- 2026-05-11 slice 18 fix arc + bilateral protocol consolidation (MP-377):
- `dev/active/review_probes.md` is the review-probe execution spec; implementation tasks stay in this file under `MP-368..MP-375`.
- companion under `MP-376`, not a second main product plan; implementation
- `dev/active/code_shape_expansion.md` is the research/calibration companion for future code-shape additions under `MP-378`; promotion into implementation still flows through `dev/active/review_probes.md` once Phase 5b ev…
- 2026-04-18 `MP-399` governed commit staged-index preservation in `MP-377`
- 2026-04-18 `MP-410` devctl root package-layout relief in `MP-377` scope:
- 2026-04-18 `MP-398` push preflight staged-index exclusion in `MP-377`
- 2026-04-18 `MP-388` consolidation archive pass in `MP-377` scope:
- 2026-04-18 `MP-389` semantic plan-loader core in `MP-377` scope:

## 8. Known gaps and open items

- open governance findings: 43

### Startup advisories
- push_allowed: worktree_clean_and_review_accepted

### Stale warnings
- Stop because nothing remains to push.

### Open gap rows
- **governance_open** (`dev/scripts/devctl/runtime/packet_carry_forward.py`): packet.durable_ingestion_before_ttl: source_packet_ids=rev_pkt_2691,rev_pkt_2696,rev_pkt_2697,rev_pkt_2699,rev_pkt_2700,rev_pkt_2701,rev_pkt_2702,rev_pkt_2704,rev_pkt_2705; packets are transport/provenance only, so packet-carried work must be promoted into PlanRow/FindingReview/GuardPromotionCandidate/knowledge state before TTL expiry. Durable owner: MP377-GUARDIR-PACKET-DURABLE-INGESTION.
- **governance_open** (`dev/scripts/checks/multi_agent_sync`): agent_sync.ambiguity_projection: source_packet_ids=rev_pkt_2697,rev_pkt_2705; canonical_active_packet_ambiguity can render empty while ambiguity exists, and expired-but-pending split state creates carry-forward debt. Durable owner: MP377-GUARDIR-AGENT-SYNC-AMBIGUITY-CARRYFORWARD.
- **governance_open** (`dev/scripts/devctl/commands/review_channel`): review_channel.command_latency_under_fanout: source_packet_ids=rev_pkt_2704,rev_pkt_2705; review-channel post and startup-context can hang under multi-agent load, tied to process-cleanup and detached sleep pressure. Durable owner: MP377-GUARDIR-FANOUT-COMMAND-HANGS.
- **governance_open** (`dev/scripts/devctl/runtime/agent_dispatch_router.py`): work_board.rows_duplication: source_packet_ids=rev_pkt_2700,rev_pkt_2705; _work_board_rows logic is duplicated between packet_route_resolution.py and agent_dispatch_router.py. Durable owner: MP377-GUARDIR-WORK-BOARD-ROUTE-DEDUP.
- **governance_open** (`dev/scripts/devctl/commands/pipeline/command.py`): dogfood.command.pipeline: Auto-ingested devctl finalization failure rc=1.
repo_path=/Users/jguida941/testing_upgrade/codex-voice
- **governance_open** (`dev/scripts/devctl/commands/process/audit.py`): dogfood.command.process-audit: Auto-ingested devctl finalization failure rc=1.
repo_path=/Users/jguida941/testing_upgrade/codex-voice
- **governance_open** (`dev/scripts/devctl/commands/reports_cleanup.py`): dogfood.command.reports-cleanup: Auto-ingested devctl finalization failure rc=1.
repo_path=/Users/jguida941/testing_upgrade/codex-voice
- **governance_open** (`dev/scripts/devctl/commands/python_tests.py`): dogfood.command.test-python: Auto-ingested devctl finalization failure rc=1.
repo_path=/Users/jguida941/testing_upgrade/codex-voice

---

Projection produced by `devctl review-snapshot`. Generation stamp `snap-81dfbe1f4e62` binds this file to HEAD `2db48c12a7fc`; if they drift, the freshness guard will fail CI. When the latest commit only refreshes this generated snapshot, the guard accepts this file as bound to that commit's parent code state.
