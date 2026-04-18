# VoiceTerm — Review Snapshot

> Deterministically generated from typed governance state. Do not edit by hand — rerun `devctl review-snapshot --write`.

## Quick status

- Branch: `feature/governance-quality-sweep`
- HEAD: `1f7b4f380350` — Land MP-398/399/410/412/413/415/416 combined multi-slice (Codex v2-v7)
- Tree hash: `979213eb92fb`
- Generation stamp: `snap-b8b656bc9395`
- Generated at (UTC): 2026-04-18T21:36:03Z
- Push decision: `await_review` — review_pending_before_push
- Reviewer mode: `active_dual_agent` (interaction: `remote_control`)
- Pipeline state: `n/a` (approval: `n/a`)
- Delta since last snapshot: 25 commits, 323 files, +16482/-7444
- Governance findings: 112 open / 86 fixed / 212 total
- Probe hints: 0 total across 0 files scanned

## 1. Identity

- Repository: **VoiceTerm**
- Product thesis: This is the product thesis for the governance stack in this repository.
Absorb these four commitments before engaging with SOP, guard, routing,
or plan detail — they explain why the process exists.

This repo builds a portable AI governance platform proven through one
production client (VoiceTerm, a Rust voice-first terminal overlay for AI
CLIs). The product thesis is that executable local control — guards,
probes, typed actions, deterministic policy resolution — is what makes
AI-assisted engineering reliable, not prompt instructions alone.

**Mission**: Ship a reusable governance stack that any repo can adopt by
installing the platform and selecting a repo pack, without forking
VoiceTerm-specific code.

**Proof obligation**: Every claim about quality, safety, or process
compliance must be backed by a repo-owned executable artifact (guard
script, probe, typed action, CI workflow) that produces the same result
regardless of which AI model or operator runs it. Prompt-only governance
is not accepted as proof.

**Platform boundaries**: VoiceTerm is one client of the platform; portable
governance layers must not hardcode repo names, bridge paths, plan doc
locations, or product-specific defaults. Repo-local assumptions belong in
the repo pack, not in the platform core. MCP servers, operator consoles,
mobile surfaces, and overlay/TUI adapters are clients, not authority.

**Current priority**: Harden the governance stack for multi-repo adoption —
remove VoiceTerm-local assumptions from portable layers, stabilize the
typed contract surface (ProjectGovernance, StartupContext, ReviewState,
TypedAction → ActionResult → RunRecord), and close the remaining probe
and guard gaps so the platform proves its own thesis before external
adopters arrive.
- Remote: `https://github.com/jguida941/voiceterm.git`
- Default branch: `master`
- Current branch: `feature/governance-quality-sweep`
- HEAD SHA: `1f7b4f3803508d9160af2af7f2d97ef30d6dc4e9`
- HEAD author: Justin Guida
- HEAD timestamp (UTC): 2026-04-18T17:35:37-04:00

## 2. Governance state

### Push decision
- action: `await_review`
- reason: review_pending_before_push
- push_eligible_now: False
- worktree_clean: True
- staged_path_count: 0
- unstaged_path_count: 0
- next_step_command: `python3 dev/scripts/devctl.py review-channel --action status --terminal none --format json`
- latest_push_report: `dev/reports/push/latest.json`
- latest_push_report_state: `published_remote` (post_push_bundle_pending)
- publication_backlog: urgent
- publication_guidance: 17 local commit(s) waiting for governed push once review is accepted.

### Reviewer runtime
- reviewer_mode: `active_dual_agent`
- reviewer_freshness: unknown
- reviewer_publish_clear: False
- interaction_mode: `remote_control`

### Remote commit pipeline
- state: `n/a`
- approval_state: `n/a`

### Work intake
- active plan: **AI Governance Platform Plan**
- plan path: `dev/active/ai_governance_platform.md`
- active MP scope: `MP-377`
- advisory: `await_review` — review_pending_before_push

## 3. Delta — what changed since the previous snapshot

Range: last 25 commits ending at `1f7b4f380350`

- commits: 25
- files changed: 323
- insertions: +16482
- deletions: -7444
- bundle classes touched: docs, tooling
- risk add-ons triggered: Parser / ANSI boundary
- authority surfaces touched: 33 file(s)

### Commits

| # | SHA | Subject | Files | +/- | Bundle | Risk |
|---|---|---|---|---|---|---|
| 1 | `1f7b4f38` | Land MP-398/399/410/412/413/415/416 combined multi-slice (C… | 157 | +4448/-3794 | tooling | Parser / ANSI boundary |
| 2 | `fc20cc1b` | Refresh external review snapshot for aa570cee | 2 | +65/-67 | docs |  |
| 3 | `aa570cee` | Add role-implicit commit approval for /remote-control (rev_… | 14 | +414/-159 | tooling |  |
| 4 | `46d34660` | Refresh external review snapshot for 6e87e071 | 2 | +58/-56 | docs |  |
| 5 | `6e87e071` | Extend MP-377 with consolidation phases MP-388..MP-397 + Da… | 5 | +362/-66 | tooling |  |
| 6 | `a2e283de` | Post-commit checkpoint: governance refresh after MP-388..MP… | 1 | +46/-42 | tooling |  |
| 7 | `7d0f87a4` | Extend MP-377 with consolidation phases MP-388..MP-397 (Cod… | 1 | +57/-66 | tooling |  |
| 8 | `0b09da19` | Refresh external review snapshot for 4f19b308 | 2 | +85/-75 | docs |  |
| 9 | `4f19b308` | Converge review-channel authority and effective-mode projec… | 74 | +3274/-789 | tooling |  |
| 10 | `637ef6f3` | Refresh external review snapshot for 077a875e | 2 | +58/-57 | docs |  |
| 11 | `077a875e` | Allow review relaunch when refresh-recommended sessions hav… | 4 | +119/-62 | tooling |  |
| 12 | `1732a6f5` | Refresh external review snapshot for 3632d600 | 2 | +68/-71 | docs |  |
| 13 | `3632d600` | Finish checkpoint repair authority follow-up | 13 | +247/-80 | tooling |  |
| 14 | `17d84eb0` | Protect running conductors during host cleanup | 20 | +1088/-476 | tooling |  |
| 15 | `3f387494` | Refine commit packet gate and pipeline recovery sequencing | 44 | +2368/-649 | tooling | Parser / ANSI boundary |
| 16 | `72103135` | Refresh external review snapshot for e117defd | 2 | +89/-83 | docs |  |
| 17 | `e117defd` | Automate remote-control checkpoint approval | 47 | +1514/-190 | tooling | Parser / ANSI boundary |
| 18 | `baad2052` | Fail closed packet authority and type convergence results | 12 | +383/-94 | tooling |  |
| 19 | `12360f8e` | Refresh external review snapshot for 30b1beff | 2 | +58/-58 | docs |  |
| 20 | `30b1beff` | Add IR contract metadata closures | 8 | +103/-23 | tooling |  |
| 21 | `c90cf9ab` | Refresh external review snapshot for 0e7c12a3 | 2 | +68/-67 | docs |  |
| 22 | `0e7c12a3` | Fail closed reviewer instruction authority state | 21 | +687/-168 | tooling |  |
| 23 | `afc2af14` | Refresh external review snapshot for 83e27bad | 2 | +98/-59 | docs |  |
| 24 | `83e27bad` | Harden typed review-channel authority state | 30 | +606/-192 | tooling |  |
| 25 | `1e7465d5` | T05: Render INDEX.md + MASTER_PLAN.md from PlanRegistry (MP… | 1 | +119/-1 | tooling |  |

### Files

| Path | Bundle | +/- |
|---|---|---|
| `AGENTS.md` | docs | +27/-2 |
| `bridge.md` | docs | +76/-76 |
| `dev/active/MASTER_PLAN.md` | tooling | +172/-4 |
| `dev/active/ai_governance_platform.md` | tooling | +510/-15 |
| `dev/active/remote_control_runtime.md` | tooling | +25/-1 |
| `dev/active/review_channel.md` | tooling | +22/-1 |
| `dev/audits/REVIEW_SNAPSHOT.md` | tooling | +1292/-1240 |
| `dev/guides/DEVELOPMENT.md` | docs | +55/-12 |
| `dev/history/ENGINEERING_EVOLUTION.md` | tooling | +529/-41 |
| `dev/scripts/README.md` | tooling | +99/-23 |
| `dev/scripts/checks/check_rustsec_policy.py` | tooling | +1/-17 |
| `dev/scripts/checks/coderabbit/gate_core.py` | tooling | +319/-0 |
| `dev/scripts/checks/coderabbit/gate_support.py` | tooling | +236/-0 |
| `dev/scripts/checks/coderabbit/run_ralph_loop.py` | tooling | +118/-0 |
| `dev/scripts/checks/coderabbit_gate_core.py` | tooling | +6/-318 |
| `dev/scripts/checks/coderabbit_gate_support.py` | tooling | +10/-236 |
| `dev/scripts/checks/governance_closure/command.py` | tooling | +1/-1 |
| `dev/scripts/checks/mutation_outcome_parse.py` | tooling | +6/-144 |
| `dev/scripts/checks/mutation_ralph_loop/outcome_parse.py` | tooling | +145/-0 |
| `dev/scripts/checks/probe_boolean_params.py` | tooling | +1/-17 |
| `dev/scripts/checks/probe_clone_density.py` | tooling | +1/-17 |
| `dev/scripts/checks/probe_concurrency.py` | tooling | +1/-17 |
| `dev/scripts/checks/probe_defensive_overchecking.py` | tooling | +1/-17 |
| `dev/scripts/checks/probe_design_smells.py` | tooling | +1/-17 |
| `dev/scripts/checks/probe_dict_as_struct.py` | tooling | +1/-17 |
| `dev/scripts/checks/probe_exception_quality.py` | tooling | +1/-17 |
| `dev/scripts/checks/probe_magic_numbers.py` | tooling | +1/-17 |
| `dev/scripts/checks/probe_stringly_typed.py` | tooling | +1/-17 |
| `dev/scripts/checks/probe_type_conversions.py` | tooling | +1/-17 |
| `dev/scripts/checks/probe_unnecessary_intermediates.py` | tooling | +1/-17 |
| `dev/scripts/checks/probe_unwrap_chains.py` | tooling | +1/-17 |
| `dev/scripts/checks/probe_vague_errors.py` | tooling | +1/-17 |
| `dev/scripts/checks/review_surface_consistency/command.py` | tooling | +38/-17 |
| `dev/scripts/checks/review_surface_consistency/models.py` | tooling | +45/-0 |
| `dev/scripts/checks/review_surface_consistency/parity.py` | tooling | +153/-18 |
| `dev/scripts/checks/run_coderabbit_ralph_loop.py` | tooling | +7/-113 |
| `dev/scripts/checks/run_probe_report.py` | tooling | +1/-1 |
| `dev/scripts/checks/startup_authority_contract/command.py` | tooling | +10/-4 |
| `dev/scripts/checks/startup_authority_contract/runtime_import_git.py` | tooling | +37/-0 |
| `dev/scripts/checks/tandem_consistency/implementer_checks.py` | tooling | +32/-4 |
| _283 more files trimmed_ | | |

## 4. Quality signals

### Governance review
- total findings: 212
- open: 112
- fixed: 86
- false positives: 0

Recent findings:
- `dogfood_finding_id_instability` — `dev/scripts/devctl/runtime/dogfood_log.py` (n/a, verdict=`confirmed_issue`)
- `dogfood_read_only_registration_missing` — `dev/scripts/devctl/cli_parser/entrypoint.py` (n/a, verdict=`confirmed_issue`)
- `finding_backlog_writer_closure_broken` — `dev/scripts/devctl/runtime/finding_backlog.py` (n/a, verdict=`confirmed_issue`)
- `dogfood_governance_pipeline_missing` — `dev/scripts/devctl/runtime/dogfood_log.py` (n/a, verdict=`confirmed_issue`)
- `bridge_authority_conflict` — `bridge.md` (n/a, verdict=`confirmed_issue`)
- `plan_markdown_projection_missing` — `dev/scripts/devctl/platform/planning_ir_models.py` (n/a, verdict=`confirmed_issue`)
- `plan_authority_gap` — `dev/active/MASTER_PLAN.md` (n/a, verdict=`confirmed_issue`)
- `bridge_metadata_parsed_as_authority` — `dev/scripts/devctl/review_channel/handoff.py` (n/a, verdict=`confirmed_issue`)
- `authority_snapshot_3_fields_missing` — `dev/scripts/devctl/runtime/startup_context.py` (n/a, verdict=`fixed`)
- `dogfood.command.startup-context` — `dev/scripts/devctl/commands/governance/startup_context.py` (n/a, verdict=`confirmed_issue`)

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
| `ActionResult` | `governance_runtime` | `n/a` | status, reason |
| `ArtifactStore` | `governance_runtime` | `n/a` | root, managed_kinds |
| `AutoModeState` | `governance_runtime` | `n/a` | phase, next_transition |
| `CallerAuthorityPolicy` | `governance_runtime` | `n/a` | caller_id, allowed_actions |
| `CheckResult` | `governance_runtime` | `n/a` | success, total |
| `ControlPlaneReadModel` | `governance_runtime` | `n/a` | push_eligible, top_blocker |
| `ControlState` | `governance_runtime` | `n/a` | approvals, active_runs |
| `CoordinationSnapshot` | `governance_core` | `n/a` | current_slice, recommended_topology |
| `DecisionPacket` | `governance_runtime` | `n/a` | decision_mode, rule_summary |
| `FailurePacket` | `governance_runtime` | `n/a` | runner, status |
| `Finding` | `governance_runtime` | `n/a` | check_id, severity |
| `LocalServiceEndpoint` | `governance_runtime` | `n/a` | service_id, discovery_fields |
| `ProviderAdapter` | `governance_adapters` | `n/a` | provider_id, capabilities |
| `PushAuthorizationRecord` | `governance_runtime` | `n/a` | authorization_id, authorized_head_sha |
| `RemoteCommitPipelineContract` | `governance_runtime` | `dev.scripts.devctl.runtime.remote_commit_pipeline_models:RemoteCommitPipelineContract` | snapshot_id, state |
| `RepoPack` | `repo_packs` | `n/a` | pack_id, policy_path |
| `ReviewCandidateRecord` | `governance_runtime` | `n/a` | candidate_id, artifact_kind |
| `ReviewState` | `governance_runtime` | `dev.scripts.devctl.runtime.review_state_models:ReviewState` | snapshot_id, bridge |
| `ReviewerRuntimeContract` | `governance_runtime` | `n/a` | reviewer_mode, reviewer_freshness |
| `RunRecord` | `governance_runtime` | `n/a` | run_id, status |
| `SessionCachePacket` | `governance_commands` | `n/a` | last_reviewed_sha, advisory_action |
| `TypedAction` | `governance_runtime` | `n/a` | action_id, repo_pack_id |
| `WorkflowAdapter` | `governance_adapters` | `n/a` | adapter_id, transport |

### Key documents

- `AGENTS.md`
- `dev/active/MASTER_PLAN.md`
- `dev/active/INDEX.md`
- `dev/guides/AI_GOVERNANCE_PLATFORM.md`

## 6. Reviewer hints — please verify

### Targeted hints

- **risk**: Parser / ANSI boundary — Delta touches a risk-sensitive surface; verify the routed bundle
- **authority_surface**: Typed authority surface touched (`dev/scripts/checks/startup_authority_contract/command.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/checks/startup_authority_contract/runtime_import_git.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_phases.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_stage_attention.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_stage_snapshot.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/review_snapshot_sources.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/checks/test_startup_authority_contract.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/vcs/test_governed_executor.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_packets.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/governance/startup_context.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/review_channel/reviewer_runtime_snapshot.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_commit_attention.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_commit_runtime.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/review_channel/bridge_validation.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/review_channel/reviewer_follow_packet_guard.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/review_channel/reviewer_follow_packets.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/reviewer_runtime_parser.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/startup_context.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/review_channel/test_reviewer_follow_packet_guard.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/review_channel/test_reviewer_follow_packets.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/runtime/test_startup_context.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/review_channel/bridge_projection_sections.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/project_governance_push.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/startup_push_decision.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_sync.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/review_channel/bridge_projection_metadata.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/review_channel/bridge_projection_state.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/review_channel/test_reviewer_follow_restore_policy.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/project_governance_contract.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/project_governance_plan_parse.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/runtime/test_project_governance.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/review_channel/reviewer_follow_guard.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/review_channel/reviewer_runtime_contract.py`) — Review contract-level invariants for this file
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/{governance_review_models.py => governance_review/models.py}`) — Commit 1f7b4f38 changed dev/scripts/devctl/{governance_review_models.py => governance_review/models.py}
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/tests/checks/test_startup_authority_contract.py`) — Commit 1f7b4f38 changed dev/scripts/devctl/tests/checks/test_startup_authority_contract.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/governance/push_state_models.py`) — Commit 3f387494 changed dev/scripts/devctl/governance/push_state_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/project_governance_contract.py`) — Commit 30b1beff changed dev/scripts/devctl/runtime/project_governance_contract.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/review_channel/reviewer_runtime_contract.py`) — Commit 83e27bad changed dev/scripts/devctl/review_channel/reviewer_runtime_contract.py

### Suggested verification commands

- `python3 dev/scripts/devctl.py check --profile ci`
- `python3 dev/scripts/devctl.py probe-report --format md`
- `python3 dev/scripts/devctl.py docs-check --strict-tooling`
- `python3 dev/scripts/devctl.py governance-review --format md`
- `python3 dev/scripts/devctl.py check-router --format md`

## 7. Reasoning — why these changes landed

### Per-commit rationale

- **`1f7b4f38` | MPs: MP-398** — Land MP-398/399/410/412/413/415/416 combined multi-slice (Codex v2-v7)
  - evolution: Fact: the next live `/remote-control` dogfood pass exposed a narrower gap than either of the repo's earlier extremes. The branch had already moved away from blanket promptless `remote_control` approval, and `devctl comm…
- **`fc20cc1b`** — Refresh external review snapshot for aa570cee
  - evolution: Fact: the next live `/remote-control` dogfood pass exposed a narrower gap than either of the repo's earlier extremes. The branch had already moved away from blanket promptless `remote_control` approval, and `devctl comm…
- **`aa570cee`** — Add role-implicit commit approval for /remote-control (rev_pkt_1120 gap #1)
  - evolution: Fact: the next live `/remote-control` dogfood pass exposed a narrower gap than either of the repo's earlier extremes. The branch had already moved away from blanket promptless `remote_control` approval, and `devctl comm…
- **`46d34660`** — Refresh external review snapshot for 6e87e071
  - evolution: Fact: the next live `/remote-control` dogfood pass exposed a narrower gap than either of the repo's earlier extremes. The branch had already moved away from blanket promptless `remote_control` approval, and `devctl comm…
- **`6e87e071` | MPs: MP-377, MP-388, MP-397** — Extend MP-377 with consolidation phases MP-388..MP-397 + Data Contracts
  - plan: `dev/active/ai_governance_platform.md`
  - evolution: Fact: the next live `/remote-control` dogfood pass exposed a narrower gap than either of the repo's earlier extremes. The branch had already moved away from blanket promptless `remote_control` approval, and `devctl comm…
- **`a2e283de` | MPs: MP-388, MP-397** — Post-commit checkpoint: governance refresh after MP-388..MP-397 landing
  - evolution: Fact: the next live `/remote-control` dogfood pass exposed a narrower gap than either of the repo's earlier extremes. The branch had already moved away from blanket promptless `remote_control` approval, and `devctl comm…
- **`7d0f87a4` | MPs: MP-377, MP-388, MP-397** — Extend MP-377 with consolidation phases MP-388..MP-397 (Codex v3 plan-authoring slice)
  - plan: `dev/active/ai_governance_platform.md`
  - evolution: Fact: the next live `/remote-control` dogfood pass exposed a narrower gap than either of the repo's earlier extremes. The branch had already moved away from blanket promptless `remote_control` approval, and `devctl comm…
- **`0b09da19`** — Refresh external review snapshot for 4f19b308
  - evolution: Fact: the next live `/remote-control` dogfood pass exposed a narrower gap than either of the repo's earlier extremes. The branch had already moved away from blanket promptless `remote_control` approval, and `devctl comm…
- **`4f19b308`** — Converge review-channel authority and effective-mode projections
  - evolution: Fact: the next live `/remote-control` dogfood pass exposed a narrower gap than either of the repo's earlier extremes. The branch had already moved away from blanket promptless `remote_control` approval, and `devctl comm…
- **`637ef6f3`** — Refresh external review snapshot for 077a875e
- **`077a875e`** — Allow review relaunch when refresh-recommended sessions have no live process
- **`1732a6f5`** — Refresh external review snapshot for 3632d600
- **`3632d600`** — Finish checkpoint repair authority follow-up
- **`17d84eb0`** — Protect running conductors during host cleanup
- **`3f387494`** — Refine commit packet gate and pipeline recovery sequencing
- **`72103135`** — Refresh external review snapshot for e117defd
- **`e117defd`** — Automate remote-control checkpoint approval
- **`baad2052`** — Fail closed packet authority and type convergence results
- **`12360f8e`** — Refresh external review snapshot for 30b1beff
- **`30b1beff`** — Add IR contract metadata closures
- **`c90cf9ab`** — Refresh external review snapshot for 0e7c12a3
- **`0e7c12a3`** — Fail closed reviewer instruction authority state
- **`afc2af14`** — Refresh external review snapshot for 83e27bad
- **`83e27bad`** — Harden typed review-channel authority state
- **`1e7465d5`** — T05: Render INDEX.md + MASTER_PLAN.md from PlanRegistry (MP377-P1-T05)
  - New functions in plan_registry_projection.py:
  - - render_index_projection: produces INDEX.md table from typed PlanRegistry
  - - render_master_plan_projection: produces MASTER_PLAN.md grouped by lifecycle
### Active MP scope (from MASTER_PLAN.md)

- contract slice for MP-355 plus the temporary markdown-swarm operating mode
- `dev/active/review_probes.md` is the review-probe execution spec; implementation tasks stay in this file under `MP-368..MP-375`.
- companion under `MP-376`, not a second main product plan; implementation
- architecture plan for the extracted AI-governance system under `MP-377`.
- `dev/active/code_shape_expansion.md` is the research/calibration companion for future code-shape additions under `MP-378`; promotion into implementation still flows through `dev/active/review_probes.md` once Phase 5b ev…
- 2026-04-18 `MP-399` governed commit staged-index preservation in `MP-377`
- 2026-04-18 `MP-410` devctl root package-layout relief in `MP-377` scope:
- 2026-04-18 `MP-398` push preflight staged-index exclusion in `MP-377`
- 2026-04-18 `MP-388` consolidation archive pass in `MP-377` scope:
- 2026-04-18 `MP-389` semantic plan-loader core in `MP-377` scope:

## 8. Known gaps and open items

- open governance findings: 112

### Startup advisories
- await_review: review_pending_before_push

### Stale warnings
- Keep editing the current slice.
- Move straight to the governed push path.

### Open gap rows
- **governance_open** (`dev/scripts/devctl/runtime/dogfood_log.py`): dogfood_finding_id_instability: 
- **governance_open** (`dev/scripts/devctl/cli_parser/entrypoint.py`): dogfood_read_only_registration_missing: 
- **governance_open** (`dev/scripts/devctl/runtime/finding_backlog.py`): finding_backlog_writer_closure_broken: 
- **governance_open** (`dev/scripts/devctl/runtime/dogfood_log.py`): dogfood_governance_pipeline_missing: 
- **governance_open** (`bridge.md`): bridge_authority_conflict: 
- **governance_open** (`dev/scripts/devctl/platform/planning_ir_models.py`): plan_markdown_projection_missing: 
- **governance_open** (`dev/active/MASTER_PLAN.md`): plan_authority_gap: 
- **governance_open** (`dev/scripts/devctl/review_channel/handoff.py`): bridge_metadata_parsed_as_authority: 

---

Projection produced by `devctl review-snapshot`. Generation stamp `snap-b8b656bc9395` binds this file to HEAD `1f7b4f380350`; if they drift, the freshness guard will fail CI. When the latest commit only refreshes this generated snapshot, the guard accepts this file as bound to that commit's parent code state.
