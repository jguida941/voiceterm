# VoiceTerm — Review Snapshot

> Deterministically generated from typed governance state. Do not edit by hand — rerun `devctl review-snapshot --write`.

## Quick status

- Branch: `feature/governance-quality-sweep`
- HEAD: `09ef6ccc55c8` — Refresh external review snapshot for a0686d76
- Tree hash: `3fe34b45d8a3`
- Generation stamp: `snap-07c4dabcac30`
- Generated at (UTC): 2026-04-16T06:11:08Z
- Push decision: `await_checkpoint` — staged_index_budget_exceeded
- Reviewer mode: `single_agent` (interaction: `local_terminal`)
- Pipeline state: `n/a` (approval: `n/a`)
- Delta since last snapshot: 24 commits, 111 files, +8048/-2797
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
- HEAD SHA: `09ef6ccc55c84eef7ba8deccc4aef760856f2106`
- HEAD author: Justin Guida
- HEAD timestamp (UTC): 2026-04-16T00:51:33-04:00

## 2. Governance state

### Push decision
- action: `await_checkpoint`
- reason: staged_index_budget_exceeded
- push_eligible_now: False
- worktree_clean: False
- staged_path_count: 26
- unstaged_path_count: 0
- next_step_command: `n/a`
- latest_push_report: `dev/reports/push/latest.json`
- latest_push_report_state: `post_push_green` (push_completed)
- current_push_authorization: `push-auth-20260416T045111064083Z` (valid=False)
- authorized_head_commit: `09ef6ccc55c84eef7ba8deccc4aef760856f2106`
- approved_target_identity: `tree-receipt-20260416T045111064083Z:5d89fb3f8b159b4226e2ef22e214464969be6342`
- publication_backlog: none

### Reviewer runtime
- reviewer_mode: `single_agent`
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
- advisory: `checkpoint_before_continue` — staged_index_budget_exceeded
- checkpoint_required: **yes**

## 3. Delta — what changed since the previous snapshot

Range: last 24 commits ending at `09ef6ccc55c8`

- commits: 24
- files changed: 111
- insertions: +8048
- deletions: -2797
- bundle classes touched: docs, tooling
- risk add-ons triggered: Parser / ANSI boundary
- authority surfaces touched: 15 file(s)

### Commits

| # | SHA | Subject | Files | +/- | Bundle | Risk |
|---|---|---|---|---|---|---|
| 1 | `09ef6ccc` | Refresh external review snapshot for a0686d76 | 2 | +62/-66 | docs |  |
| 2 | `a0686d76` | Split loop-packet commands into packets package | 11 | +653/-581 | tooling |  |
| 3 | `1e54c022` | Refresh external review snapshot for 85b11941 | 2 | +58/-61 | docs |  |
| 4 | `85b11941` | Project typed plan authority and packet inbox state | 24 | +1116/-138 | tooling |  |
| 5 | `fa370be5` | Refresh external review snapshot for bc594104 | 2 | +65/-68 | docs |  |
| 6 | `bc594104` | Project plan authority readers from typed registry | 18 | +464/-93 | tooling |  |
| 7 | `af3724b7` | Refresh external review snapshot for 8873e4e5 | 2 | +62/-67 | docs |  |
| 8 | `8873e4e5` | Persist plan registry artifact for startup authority | 14 | +703/-73 | tooling |  |
| 9 | `42ddab83` | Refresh external review snapshot for 980648dd | 2 | +69/-76 | docs |  |
| 10 | `980648dd` | Prefer effective reviewer mode for governed commit fallback | 10 | +159/-73 | tooling |  |
| 11 | `5146e651` | Refresh external review snapshot for a14356d3 | 2 | +72/-89 | docs |  |
| 12 | `a14356d3` | Fix review-channel launch authority and runtime packet pari… | 28 | +732/-126 | tooling |  |
| 13 | `bc1b011b` | Refresh external review snapshot for d599b9b6 | 2 | +61/-61 | docs |  |
| 14 | `d599b9b6` | Fix startup repair authority parity | 11 | +395/-58 | tooling |  |
| 15 | `7d35f8e8` | Refresh external review snapshot for f3350f0d | 2 | +74/-69 | docs |  |
| 16 | `f3350f0d` | Implement dogfood campaign contract and bound startup autho… | 23 | +908/-99 | tooling | Parser / ANSI boundary |
| 17 | `8b587485` | Refresh external review snapshot for 5807328b | 2 | +66/-68 | docs |  |
| 18 | `5807328b` | Harden shim governance and review state parsing | 15 | +292/-94 | tooling |  |
| 19 | `2454de6b` | Refresh external review snapshot for 63ad7200 | 1 | +62/-66 | tooling |  |
| 20 | `63ad7200` | Repair event-backed bridge projection parity | 11 | +214/-83 | tooling |  |
| 21 | `8dfa6a83` | Refresh external review snapshot for 0af6b46f | 1 | +58/-61 | tooling |  |
| 22 | `0af6b46f` | Repair bridge poll metadata projection | 10 | +224/-73 | tooling |  |
| 23 | `ae95f570` | Refresh external review snapshot for 1bd047a3 | 2 | +77/-72 | docs |  |
| 24 | `1bd047a3` | Stabilize review-channel authority recovery | 30 | +1402/-482 | tooling |  |

### Files

| Path | Bundle | +/- |
|---|---|---|
| `AGENTS.md` | docs | +66/-22 |
| `bridge.md` | docs | +63/-63 |
| `dev/active/MASTER_PLAN.md` | tooling | +136/-2 |
| `dev/active/ai_governance_platform.md` | tooling | +332/-6 |
| `dev/active/continuous_swarm.md` | tooling | +24/-0 |
| `dev/active/portable_code_governance.md` | tooling | +31/-2 |
| `dev/active/remote_control_runtime.md` | tooling | +24/-1 |
| `dev/audits/REVIEW_SNAPSHOT.md` | tooling | +1463/-1478 |
| `dev/config/quality_presets/voiceterm.json` | tooling | +28/-0 |
| `dev/guides/DEVELOPMENT.md` | docs | +77/-12 |
| `dev/history/ENGINEERING_EVOLUTION.md` | tooling | +547/-0 |
| `dev/scripts/README.md` | tooling | +77/-21 |
| `dev/scripts/checks/check_review_snapshot_freshness.py` | tooling | +6/-252 |
| `dev/scripts/checks/review_snapshot_freshness/__init__.py` | tooling | +1/-0 |
| `dev/scripts/checks/review_snapshot_freshness/command.py` | tooling | +260/-0 |
| `dev/scripts/checks/startup_authority_contract/runtime_import_atomicity.py` | tooling | +36/-1 |
| `dev/scripts/checks/startup_authority_contract/runtime_import_git.py` | tooling | +37/-0 |
| `dev/scripts/devctl/commands/check/__init__.py` | tooling | +1/-1 |
| `dev/scripts/devctl/commands/check_phases.py` | tooling | +0/-13 |
| `dev/scripts/devctl/commands/governance/import_findings.py` | tooling | +26/-4 |
| `dev/scripts/devctl/commands/governance/session_resume_render.py` | tooling | +3/-1 |
| `dev/scripts/devctl/commands/governance/startup_repair_runtime.py` | tooling | +41/-2 |
| `dev/scripts/devctl/commands/loop_packet.py` | tooling | +8/-280 |
| `dev/scripts/devctl/commands/loop_packet_helpers.py` | tooling | +8/-215 |
| `dev/scripts/devctl/commands/packets/loop_packet.py` | tooling | +288/-0 |
| `dev/scripts/devctl/commands/packets/loop_packet_helpers.py` | tooling | +218/-0 |
| `dev/scripts/devctl/commands/reporting/dogfood.py` | tooling | +28/-0 |
| `dev/scripts/devctl/commands/vcs/governed_executor_commit_runtime.py` | tooling | +2/-2 |
| `dev/scripts/devctl/context_graph/catalog_nodes.py` | tooling | +16/-2 |
| `dev/scripts/devctl/governance/draft_governed_docs.py` | tooling | +53/-9 |
| `dev/scripts/devctl/governance/draft_governed_docs_artifact.py` | tooling | +349/-0 |
| `dev/scripts/devctl/governance/governed_doc_routing.py` | tooling | +93/-9 |
| `dev/scripts/devctl/governance/live_run_import.py` | tooling | +85/-0 |
| `dev/scripts/devctl/governance/parser.py` | tooling | +6/-3 |
| `dev/scripts/devctl/platform/coordination_snapshot_support.py` | tooling | +2/-2 |
| `dev/scripts/devctl/quality_policy_values.py` | tooling | +0/-7 |
| `dev/scripts/devctl/review_channel/bridge_projection_metadata.py` | tooling | +42/-5 |
| `dev/scripts/devctl/review_channel/collaboration_session.py` | tooling | +67/-0 |
| `dev/scripts/devctl/review_channel/collaboration_session_local_reviewer.py` | tooling | +24/-11 |
| `dev/scripts/devctl/review_channel/event_projection_assembly.py` | tooling | +40/-21 |
| _71 more files trimmed_ | | |

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
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/review_snapshot_why.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/runtime/test_review_snapshot_why.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_commit_runtime.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/vcs/test_governed_executor.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/runtime/test_startup_context.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/checks/startup_authority_contract/runtime_import_atomicity.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/checks/startup_authority_contract/runtime_import_git.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/checks/test_startup_authority_contract.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/review_channel/bridge_projection_metadata.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/checks/check_review_snapshot_freshness.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/checks/review_snapshot_freshness/__init__.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/checks/review_snapshot_freshness/command.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/review_snapshot_refresh.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/reviewer_runtime_models.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/checks/test_check_review_snapshot_freshness.py`) — Review contract-level invariants for this file
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/dogfood_models.py`) — Commit f3350f0d changed dev/scripts/devctl/runtime/dogfood_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/tests/checks/test_startup_authority_contract.py`) — Commit f3350f0d changed dev/scripts/devctl/tests/checks/test_startup_authority_contract.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/reviewer_runtime_models.py`) — Commit 1bd047a3 changed dev/scripts/devctl/runtime/reviewer_runtime_models.py

### Suggested verification commands

- `python3 dev/scripts/devctl.py check --profile ci`
- `python3 dev/scripts/devctl.py probe-report --format md`
- `python3 dev/scripts/devctl.py docs-check --strict-tooling`
- `python3 dev/scripts/devctl.py governance-review --format md`
- `python3 dev/scripts/devctl.py check-router --format md`

## 7. Reasoning — why these changes landed

### Per-commit rationale

- **`09ef6ccc`** — Refresh external review snapshot for a0686d76
- **`a0686d76`** — Split loop-packet commands into packets package
- **`1e54c022`** — Refresh external review snapshot for 85b11941
- **`85b11941`** — Project typed plan authority and packet inbox state
- **`fa370be5`** — Refresh external review snapshot for bc594104
  - evolution: Fact: the next dogfood pass after the launch-authority/runtime-parity repair found one more place where declared topology could outrank typed authority. `resolve_commit_execution_target()` still preferred `collaboration…
- **`bc594104`** — Project plan authority readers from typed registry
  - evolution: Fact: the next dogfood pass after the launch-authority/runtime-parity repair found one more place where declared topology could outrank typed authority. `resolve_commit_execution_target()` still preferred `collaboration…
- **`af3724b7`** — Refresh external review snapshot for 8873e4e5
  - evolution: Fact: the next dogfood pass after the launch-authority/runtime-parity repair found one more place where declared topology could outrank typed authority. `resolve_commit_execution_target()` still preferred `collaboration…
- **`8873e4e5`** — Persist plan registry artifact for startup authority
  - evolution: Fact: the next dogfood pass after the launch-authority/runtime-parity repair found one more place where declared topology could outrank typed authority. `resolve_commit_execution_target()` still preferred `collaboration…
- **`42ddab83`** — Refresh external review snapshot for 980648dd
  - evolution: Fact: the next dogfood pass after the launch-authority/runtime-parity repair found one more place where declared topology could outrank typed authority. `resolve_commit_execution_target()` still preferred `collaboration…
- **`980648dd`** — Prefer effective reviewer mode for governed commit fallback
  - evolution: Fact: the next dogfood pass after the launch-authority/runtime-parity repair found one more place where declared topology could outrank typed authority. `resolve_commit_execution_target()` still preferred `collaboration…
- **`5146e651`** — Refresh external review snapshot for a14356d3
  - evolution: Fact: the next dogfood pass after the launch-authority/runtime-parity repair found one more place where declared topology could outrank typed authority. `resolve_commit_execution_target()` still preferred `collaboration…
- **`a14356d3`** — Fix review-channel launch authority and runtime packet parity
  - evolution: Fact: the next dogfood pass after the launch-authority/runtime-parity repair found one more place where declared topology could outrank typed authority. `resolve_commit_execution_target()` still preferred `collaboration…
- **`bc1b011b`** — Refresh external review snapshot for d599b9b6
  - evolution: Fact: the next dogfood pass after the launch-authority/runtime-parity repair found one more place where declared topology could outrank typed authority. `resolve_commit_execution_target()` still preferred `collaboration…
- **`d599b9b6`** — Fix startup repair authority parity
  - evolution: Fact: the next dogfood pass after the launch-authority/runtime-parity repair found one more place where declared topology could outrank typed authority. `resolve_commit_execution_target()` still preferred `collaboration…
- **`7d35f8e8`** — Refresh external review snapshot for f3350f0d
  - evolution: Fact: the next dogfood pass after the launch-authority/runtime-parity repair found one more place where declared topology could outrank typed authority. `resolve_commit_execution_target()` still preferred `collaboration…
- **`f3350f0d`** — Implement dogfood campaign contract and bound startup authority
  - evolution: Fact: the next dogfood pass after the launch-authority/runtime-parity repair found one more place where declared topology could outrank typed authority. `resolve_commit_execution_target()` still preferred `collaboration…
- **`8b587485`** — Refresh external review snapshot for 5807328b
  - evolution: Fact: the next dogfood pass after the launch-authority/runtime-parity repair found one more place where declared topology could outrank typed authority. `resolve_commit_execution_target()` still preferred `collaboration…
- **`5807328b`** — Harden shim governance and review state parsing
  - evolution: Fact: the next dogfood pass after the launch-authority/runtime-parity repair found one more place where declared topology could outrank typed authority. `resolve_commit_execution_target()` still preferred `collaboration…
- **`2454de6b`** — Refresh external review snapshot for 63ad7200
  - evolution: Fact: the next dogfood pass after the launch-authority/runtime-parity repair found one more place where declared topology could outrank typed authority. `resolve_commit_execution_target()` still preferred `collaboration…
- **`63ad7200`** — Repair event-backed bridge projection parity
  - evolution: Fact: the next dogfood pass after the launch-authority/runtime-parity repair found one more place where declared topology could outrank typed authority. `resolve_commit_execution_target()` still preferred `collaboration…
- **`8dfa6a83`** — Refresh external review snapshot for 0af6b46f
  - evolution: Fact: the next dogfood pass after the launch-authority/runtime-parity repair found one more place where declared topology could outrank typed authority. `resolve_commit_execution_target()` still preferred `collaboration…
- **`0af6b46f`** — Repair bridge poll metadata projection
  - evolution: Fact: the next dogfood pass after the launch-authority/runtime-parity repair found one more place where declared topology could outrank typed authority. `resolve_commit_execution_target()` still preferred `collaboration…
- **`ae95f570`** — Refresh external review snapshot for 1bd047a3
  - evolution: Fact: the next dogfood pass after the launch-authority/runtime-parity repair found one more place where declared topology could outrank typed authority. `resolve_commit_execution_target()` still preferred `collaboration…
- **`1bd047a3`** — Stabilize review-channel authority recovery
  - evolution: Fact: the next dogfood pass after the launch-authority/runtime-parity repair found one more place where declared topology could outrank typed authority. `resolve_commit_execution_target()` still preferred `collaboration…
### Active MP scope (from MASTER_PLAN.md)

- contract slice for MP-355 plus the temporary markdown-swarm operating mode
- `dev/active/review_probes.md` is the review-probe execution spec; implementation tasks stay in this file under `MP-368..MP-375`.
- companion under `MP-376`, not a second main product plan; implementation
- architecture plan for the extracted AI-governance system under `MP-377`.
- `dev/active/code_shape_expansion.md` is the research/calibration companion for future code-shape additions under `MP-378`; promotion into implementation still flows through `dev/active/review_probes.md` once Phase 5b ev…
- 2026-04-11 remote-participant visibility follow-up in `MP-380..MP-387`
- the reopened MP-384/MP-387 F1 parity flake is now narrowed at the CLI edge
- Current 2026-04-05 reviewer-handoff closure inside that same lane: `MP-387`
- the `MP-381` field-route proof helper
- `MP-383` / `MP-381` packet-backed action-request and shared

## 8. Known gaps and open items

- open governance findings: 112

### Startup advisories
- checkpoint_before_continue: staged_index_budget_exceeded

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

Projection produced by `devctl review-snapshot`. Generation stamp `snap-07c4dabcac30` binds this file to HEAD `09ef6ccc55c8`; if they drift, the freshness guard will fail CI. When the latest commit only refreshes this generated snapshot, the guard accepts this file as bound to that commit's parent code state.
