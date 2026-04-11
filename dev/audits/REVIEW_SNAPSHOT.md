# VoiceTerm — Review Snapshot

> Deterministically generated from typed governance state. Do not edit by hand — rerun `devctl review-snapshot --write`.

## Quick status

- Branch: `feature/governance-quality-sweep`
- HEAD: `6e8d96c272e2` — Refresh external review snapshot for b505d809
- Tree hash: `c585dba150ad`
- Generation stamp: `snap-69aba6310adb`
- Generated at (UTC): 2026-04-11T06:28:23Z
- Push decision: `await_checkpoint` — staged_index_present
- Reviewer mode: `single_agent` (interaction: `remote_control`)
- Pipeline state: `n/a` (approval: `n/a`)
- Delta since last snapshot: 24 commits, 69 files, +8199/-2017
- Governance findings: 86 open / 71 fixed / 171 total
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
- HEAD SHA: `6e8d96c272e2c35da522b179b0a3de3993e2f7dd`
- HEAD author: Justin Guida
- HEAD timestamp (UTC): 2026-04-11T01:55:27-04:00

## 2. Governance state

### Push decision
- action: `await_checkpoint`
- reason: staged_index_present
- push_eligible_now: False
- worktree_clean: False
- staged_path_count: 1
- unstaged_path_count: 0
- next_step_command: `n/a`
- latest_push_report: `dev/reports/push/latest.json`
- latest_push_report_state: `published_remote` (post_push_bundle_pending)
- publication_backlog: urgent
- publication_guidance: 8 local commit(s) waiting for governed push once the current slice is checkpoint-clean.

### Reviewer runtime
- reviewer_mode: `single_agent`
- reviewer_freshness: unknown
- reviewer_publish_clear: True
- interaction_mode: `remote_control`

### Remote commit pipeline
- state: `n/a`
- approval_state: `n/a`

### Work intake
- active plan: **Master Plan (Active, Unified)**
- plan path: `dev/active/MASTER_PLAN.md`
- active MP scope: all active MP execution state
- advisory: `checkpoint_allowed` — worktree_dirty_within_budget

## 3. Delta — what changed since the previous snapshot

Range: last 24 commits ending at `6e8d96c272e2`

- commits: 24
- files changed: 69
- insertions: +8199
- deletions: -2017
- bundle classes touched: tooling, docs
- risk add-ons triggered: Parser / ANSI boundary
- authority surfaces touched: 3 file(s)

### Commits

| # | SHA | Subject | Files | +/- | Bundle | Risk |
|---|---|---|---|---|---|---|
| 1 | `6e8d96c2` | Refresh external review snapshot for b505d809 | 1 | +61/-63 | tooling |  |
| 2 | `b505d809` | docs(bridge): capture Codex reviewer verdict state (Q91b wo… | 2 | +84/-83 | docs |  |
| 3 | `a662deb5` | docs(audit): Q92 — 14+ prose-as-authority fields across gov… | 2 | +539/-48 | tooling |  |
| 4 | `d8c71114` | Refresh external review snapshot for 8243c5ab | 1 | +64/-70 | tooling |  |
| 5 | `8243c5ab` | docs(audit): Q91 — dashboard checkpoint, role correction, 4… | 2 | +435/-54 | tooling |  |
| 6 | `ef3f08ae` | Refresh external review snapshot for dfcd171a | 1 | +71/-67 | tooling |  |
| 7 | `dfcd171a` | docs(governance): Q78-Q90 — loop v1 retrospective and loop… | 11 | +2160/-59 | tooling |  |
| 8 | `5a92fa03` | feat(context-graph): Q78 Phase 0 — expose typed contracts a… | 9 | +557/-74 | tooling |  |
| 9 | `3566b16b` | Refresh external review snapshot for 9be23299 | 1 | +59/-59 | tooling |  |
| 10 | `9be23299` | fix(governance): Q70 — collapse action_routing onto single… | 10 | +191/-137 | tooling |  |
| 11 | `4db52ae8` | Refresh external review snapshot for a77c3b3f | 1 | +58/-57 | tooling |  |
| 12 | `a77c3b3f` | docs(audit): Q70-Q75 — Codex architectural review of Q40-Q6… | 3 | +243/-49 | tooling |  |
| 13 | `48c7b5e9` | Refresh external review snapshot for b078731a | 1 | +58/-61 | tooling |  |
| 14 | `b078731a` | chore(code_shape): remove stale path overrides for files un… | 2 | +50/-59 | tooling |  |
| 15 | `e914ad33` | Refresh external review snapshot for 95140873 | 1 | +55/-58 | tooling |  |
| 16 | `95140873` | fix(bundles): dual import support for registry.py — works a… | 2 | +68/-51 | tooling |  |
| 17 | `6b51ebe9` | Refresh external review snapshot for 3f1d9950 | 1 | +71/-73 | tooling |  |
| 18 | `3f1d9950` | feat(governance): Q57 + Q58 — devctl monitor + registry-as-… | 27 | +1575/-137 | tooling |  |
| 19 | `ae265ed6` | Refresh external review snapshot for f240bfe3 | 1 | +53/-59 | tooling |  |
| 20 | `f240bfe3` | docs: register findings-priority in AGENTS.md tooling inven… | 2 | +42/-38 | docs |  |
| 21 | `eac80fb7` | chore: refresh REVIEW_SNAPSHOT after Round 8 | 1 | +61/-65 | tooling |  |
| 22 | `ab7569ab` | Refresh external review snapshot for 7eca4d0c | 1 | +70/-68 | tooling |  |
| 23 | `7eca4d0c` | feat(governance): Q52 + Q55 — commit gate hook + findings p… | 21 | +1529/-486 | tooling | Parser / ANSI boundary |
| 24 | `4cee9ac1` | Refresh external review snapshot for 1840993a | 1 | +45/-42 | tooling |  |

### Files

| Path | Bundle | +/- |
|---|---|---|
| `AGENTS.md` | docs | +3/-0 |
| `bridge.md` | docs | +18/-15 |
| `dev/README.md` | docs | +2/-0 |
| `dev/active/INDEX.md` | tooling | +13/-2 |
| `dev/active/MASTER_PLAN.md` | tooling | +12/-0 |
| `dev/active/ai_governance_platform.md` | tooling | +11/-0 |
| `dev/active/autonomous_governance_loop_v2.md` | tooling | +473/-0 |
| `dev/active/platform_authority_loop.md` | tooling | +31/-7 |
| `dev/active/remote_control_runtime.md` | tooling | +8/-0 |
| `dev/audits/LIVE_RUN.md` | tooling | +2606/-1 |
| `dev/audits/REVIEW_SNAPSHOT.md` | tooling | +1356/-1371 |
| `dev/audits/reviews/q40_q67_codex_review_2026-04-10.md` | tooling | +71/-0 |
| `dev/config/git_hooks/pre-commit-review-snapshot.sh` | tooling | +41/-18 |
| `dev/config/templates/portable_governance_pre_commit_hook.sh` | tooling | +13/-1 |
| `dev/guides/DEVELOPMENT.md` | docs | +9/-2 |
| `dev/history/ENGINEERING_EVOLUTION.md` | tooling | +29/-0 |
| `dev/scripts/README.md` | tooling | +25/-5 |
| `dev/scripts/checks/code_shape/code_shape_policy.py` | tooling | +0/-12 |
| `dev/scripts/devctl/autonomy/run_helpers.py` | tooling | +3/-2 |
| `dev/scripts/devctl/bundles/registry.py` | tooling | +111/-80 |
| `dev/scripts/devctl/cli.py` | tooling | +7/-388 |
| `dev/scripts/devctl/cli_parser/entrypoint.py` | tooling | +407/-0 |
| `dev/scripts/devctl/commands/governance/install_git_hooks.py` | tooling | +11/-8 |
| `dev/scripts/devctl/commands/governance/simple_lanes_support.py` | tooling | +3/-2 |
| `dev/scripts/devctl/commands/listing.py` | tooling | +2/-0 |
| `dev/scripts/devctl/commands/monitor.py` | tooling | +13/-0 |
| `dev/scripts/devctl/commands/reporting/findings_priority.py` | tooling | +58/-0 |
| `dev/scripts/devctl/commands/reporting/monitor.py` | tooling | +184/-0 |
| `dev/scripts/devctl/commands/review_channel/_ensure_follow_runtime.py` | tooling | +1/-0 |
| `dev/scripts/devctl/commands/review_channel/_follow_runtime.py` | tooling | +1/-0 |
| `dev/scripts/devctl/commands/review_channel/_publisher.py` | tooling | +28/-0 |
| `dev/scripts/devctl/context_graph/builder.py` | tooling | +5/-3 |
| `dev/scripts/devctl/context_graph/contract_nodes.py` | tooling | +108/-0 |
| `dev/scripts/devctl/context_graph/contract_relations.py` | tooling | +85/-0 |
| `dev/scripts/devctl/context_graph/contract_scan.py` | tooling | +120/-0 |
| `dev/scripts/devctl/context_graph/models.py` | tooling | +2/-0 |
| `dev/scripts/devctl/context_graph/query.py` | tooling | +18/-10 |
| `dev/scripts/devctl/context_graph/query_matching.py` | tooling | +68/-0 |
| `dev/scripts/devctl/governance/script_catalog_registry.py` | tooling | +50/-4 |
| `dev/scripts/devctl/review_channel/follow_controller.py` | tooling | +12/-0 |
| _29 more files trimmed_ | | |

## 4. Quality signals

### Governance review
- total findings: 171
- open: 86
- fixed: 71
- false positives: 0

Recent findings:
- `subprocess_missing_timeout` — `dev/scripts/devctl/security/codeql.py` (n/a, verdict=`confirmed_issue`)
- `subprocess_missing_timeout` — `dev/scripts/devctl/integrations/import_core.py` (n/a, verdict=`confirmed_issue`)
- `subprocess_missing_timeout` — `app/operator_console/launch_support.py` (n/a, verdict=`confirmed_issue`)
- `threading_shared_state_no_lock` — `dev/scripts/devctl/common.py` (n/a, verdict=`confirmed_issue`)
- `none_safety_chained_get_crash` — `dev/scripts/devctl/review_channel/bridge_projection_state.py` (n/a, verdict=`confirmed_issue`)
- `none_safety_chained_get_crash` — `app/operator_console/state/review/operator_decisions.py` (n/a, verdict=`confirmed_issue`)
- `none_safety_chained_get_crash` — `dev/scripts/devctl/autonomy/run_render.py` (n/a, verdict=`confirmed_issue`)
- `none_safety_chained_get_crash` — `dev/scripts/devctl/autonomy/report_helpers.py` (n/a, verdict=`confirmed_issue`)
- `none_safety_chained_get_crash` — `dev/scripts/devctl/quality_backlog/priorities.py` (n/a, verdict=`confirmed_issue`)
- `none_safety_chained_get_crash` — `dev/scripts/devctl/commands/loop_packet.py` (n/a, verdict=`confirmed_issue`)

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
| `ActionResult` | `governance_runtime` | `n/a` | status |
| `ArtifactStore` | `governance_runtime` | `n/a` | root |
| `AutoModeState` | `governance_runtime` | `n/a` | phase |
| `CallerAuthorityPolicy` | `governance_runtime` | `n/a` | caller_id |
| `CheckResult` | `governance_runtime` | `n/a` | success |
| `ControlPlaneReadModel` | `governance_runtime` | `n/a` | push_eligible |
| `ControlState` | `governance_runtime` | `n/a` | approvals |
| `CoordinationSnapshot` | `governance_core` | `n/a` | current_slice |
| `DecisionPacket` | `governance_runtime` | `n/a` | decision_mode |
| `FailurePacket` | `governance_runtime` | `n/a` | runner |
| `Finding` | `governance_runtime` | `n/a` | check_id |
| `LocalServiceEndpoint` | `governance_runtime` | `n/a` | service_id |
| `ProviderAdapter` | `governance_adapters` | `n/a` | provider_id |
| `PushAuthorizationRecord` | `governance_runtime` | `n/a` | authorization_id |
| `RemoteCommitPipelineContract` | `governance_runtime` | `dev.scripts.devctl.runtime.remote_commit_pipeline_models:RemoteCommitPipelineContract` | snapshot_id |
| `RepoPack` | `repo_packs` | `n/a` | pack_id |
| `ReviewCandidateRecord` | `governance_runtime` | `n/a` | candidate_id |
| `ReviewState` | `governance_runtime` | `dev.scripts.devctl.runtime.review_state_models:ReviewState` | snapshot_id |
| `ReviewerRuntimeContract` | `governance_runtime` | `n/a` | reviewer_mode |
| `RunRecord` | `governance_runtime` | `n/a` | run_id |
| `SessionCachePacket` | `governance_commands` | `n/a` | last_reviewed_sha |
| `TypedAction` | `governance_runtime` | `n/a` | action_id |
| `WorkflowAdapter` | `governance_adapters` | `n/a` | adapter_id |

### Key documents

- `AGENTS.md`
- `dev/active/MASTER_PLAN.md`
- `dev/active/INDEX.md`
- `dev/guides/AI_GOVERNANCE_PLATFORM.md`

## 6. Reviewer hints — please verify

### Targeted hints

- **risk**: Parser / ANSI boundary — Delta touches a risk-sensitive surface; verify the routed bundle
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/startup_context.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/runtime/test_startup_context.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/review_channel/test_reviewer_runtime_doctor.py`) — Review contract-level invariants for this file
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/work_intake_models.py`) — Commit 9be23299 changed dev/scripts/devctl/runtime/work_intake_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/monitor_snapshot_contracts.py`) — Commit 3f1d9950 changed dev/scripts/devctl/runtime/monitor_snapshot_contracts.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/triage/findings_priority_models.py`) — Commit 7eca4d0c changed dev/scripts/devctl/triage/findings_priority_models.py

### Suggested verification commands

- `python3 dev/scripts/devctl.py check --profile ci`
- `python3 dev/scripts/devctl.py probe-report --format md`
- `python3 dev/scripts/devctl.py docs-check --strict-tooling`
- `python3 dev/scripts/devctl.py governance-review --format md`
- `python3 dev/scripts/devctl.py check-router --format md`

## 7. Reasoning — why these changes landed

### Per-commit rationale

- **`6e8d96c2`** — Refresh external review snapshot for b505d809
- **`b505d809`** — docs(bridge): capture Codex reviewer verdict state (Q91b workaround)
  - Codex's review pass (session 019d7b02, task_complete 05:39:20Z) wrote
  - the blocking verdict to bridge.md via review-channel --action post,
  - rotating current_instruction_revision from a5e7f631bfba to 798446bc35db
- **`a662deb5`** — docs(audit): Q92 — 14+ prose-as-authority fields across governance stack
  - Dashboard append from the 3-agent parallel audit Claude ran on
  - instruction from the operator ("look for anywhere else in the AI
  - system where code should be typed and isn't connected properly").
- **`d8c71114`** — Refresh external review snapshot for 8243c5ab
- **`8243c5ab`** — docs(audit): Q91 — dashboard checkpoint, role correction, 4 findings for Codex
  - Dashboard-mode LIVE_RUN append covering the 2026-04-11 tick:
- **`ef3f08ae`** — Refresh external review snapshot for dfcd171a
- **`dfcd171a` | MPs: MP-377** — docs(governance): Q78-Q90 — loop v1 retrospective and loop v2 convergence plan
  - - autonomous_governance_loop_v2.md (new): bounded MP-377 convergence spec
  -   composing existing StartupContext / WorkIntakePacket / PlanningIRSnapshot /
  -   ControlPlaneReadModel / AutoModeState / FindingReview surfaces into one
  - plan: `dev/active/ai_governance_platform.md`
  - plan: `dev/active/platform_authority_loop.md`
  - plan: `dev/active/autonomous_governance_loop_v2.md`
  - plan: `dev/active/remote_commit_pipeline.md`
  - plan: `dev/active/PLAN_FORMAT.md`
- **`5a92fa03`** — feat(context-graph): Q78 Phase 0 — expose typed contracts as graph nodes
  - Add typed_contract and dataclass_field node kinds so loop-v2 seed symbols
  - (AutoModeState, GuardPromotionCandidate, PlanningIRSnapshot,
  - SessionPacingState) resolve through devctl context-graph --query instead
- **`3566b16b`** — Refresh external review snapshot for 9be23299
  - evolution: Fact: the Q40/Q42 live-run findings showed two separate authority leaks. A dashboard/observer lane could still slide into implementation edits while another agent owned the active lane, and recovery code could escalate …
- **`9be23299`** — fix(governance): Q70 — collapse action_routing onto single coordination truth
  - Adopted from killed Codex Round 10 session (PID 6154) that had written
  - the Q70 fix before being interrupted. Resumed rather than discarded.
  - evolution: Fact: the Q40/Q42 live-run findings showed two separate authority leaks. A dashboard/observer lane could still slide into implementation edits while another agent owned the active lane, and recovery code could escalate …
- **`4db52ae8`** — Refresh external review snapshot for a77c3b3f
  - evolution: Fact: the Q40/Q42 live-run findings showed two separate authority leaks. A dashboard/observer lane could still slide into implementation edits while another agent owned the active lane, and recovery code could escalate …
- **`a77c3b3f`** — docs(audit): Q70-Q75 — Codex architectural review of Q40-Q67 commits
  - Codex ran as reviewer (5.6M tokens, no patches, verdict-only) and found:
  - - Q70: action_routing still has parallel coordination truth (Q65 not complete)
  - - Q71: session_pacing emitted but no controller enforces it
  - evolution: Fact: the Q40/Q42 live-run findings showed two separate authority leaks. A dashboard/observer lane could still slide into implementation edits while another agent owned the active lane, and recovery code could escalate …
- **`48c7b5e9`** — Refresh external review snapshot for b078731a
  - evolution: Fact: the Q40/Q42 live-run findings showed two separate authority leaks. A dashboard/observer lane could still slide into implementation edits while another agent owned the active lane, and recovery code could escalate …
- **`b078731a`** — chore(code_shape): remove stale path overrides for files under default soft limit
  - presentation_state.py (329 lines) and mobile_status_views.py (346 lines)
  - are both well under the Python default soft limit. Their PATH_POLICY_OVERRIDES
  - entries allowed 550/375 soft limits that are looser than needed, and the
  - evolution: Fact: the Q40/Q42 live-run findings showed two separate authority leaks. A dashboard/observer lane could still slide into implementation edits while another agent owned the active lane, and recovery code could escalate …
- **`e914ad33`** — Refresh external review snapshot for 95140873
  - evolution: Fact: the Q40/Q42 live-run findings showed two separate authority leaks. A dashboard/observer lane could still slide into implementation edits while another agent owned the active lane, and recovery code could escalate …
- **`95140873`** — fix(bundles): dual import support for registry.py — works as package + standalone
  - Q58 registry-dispatcher refactor added a relative import that broke
  - check_bundle_registry_dry.py which loads the file via spec_from_file_location.
  - Fall back to absolute import with repo-root sys.path adjustment when the
  - evolution: Fact: the Q40/Q42 live-run findings showed two separate authority leaks. A dashboard/observer lane could still slide into implementation edits while another agent owned the active lane, and recovery code could escalate …
- **`6b51ebe9`** — Refresh external review snapshot for 3f1d9950
  - evolution: Fact: the Q40/Q42 live-run findings showed two separate authority leaks. A dashboard/observer lane could still slide into implementation edits while another agent owned the active lane, and recovery code could escalate …
- **`3f1d9950`** — feat(governance): Q57 + Q58 — devctl monitor + registry-as-sovereign-dispatcher
  - Codex Round 9 implementation:
  - - Q57: devctl monitor command for remote phone mode with typed
  -   MonitorSnapshot, --follow --interval NDJSON streaming, and
  - evolution: Fact: the Q40/Q42 live-run findings showed two separate authority leaks. A dashboard/observer lane could still slide into implementation edits while another agent owned the active lane, and recovery code could escalate …
- **`ae265ed6`** — Refresh external review snapshot for f240bfe3
  - evolution: Fact: the Q40/Q42 live-run findings showed two separate authority leaks. A dashboard/observer lane could still slide into implementation edits while another agent owned the active lane, and recovery code could escalate …
- **`f240bfe3`** — docs: register findings-priority in AGENTS.md tooling inventory
  - evolution: Fact: the Q40/Q42 live-run findings showed two separate authority leaks. A dashboard/observer lane could still slide into implementation edits while another agent owned the active lane, and recovery code could escalate …
- **`eac80fb7`** — chore: refresh REVIEW_SNAPSHOT after Round 8
  - evolution: Fact: the Q40/Q42 live-run findings showed two separate authority leaks. A dashboard/observer lane could still slide into implementation edits while another agent owned the active lane, and recovery code could escalate …
- **`ab7569ab`** — Refresh external review snapshot for 7eca4d0c
  - evolution: Fact: the Q40/Q42 live-run findings showed two separate authority leaks. A dashboard/observer lane could still slide into implementation edits while another agent owned the active lane, and recovery code could escalate …
- **`7eca4d0c`** — feat(governance): Q52 + Q55 — commit gate hook + findings priority engine
  - Codex Round 8 implementation:
  - - Q52: pre-commit hook wires raw git commit through commit_permission
  -   gate via pre-commit-review-snapshot.sh + commit_permission_hook.py.
  - evolution: Fact: the Q40/Q42 live-run findings showed two separate authority leaks. A dashboard/observer lane could still slide into implementation edits while another agent owned the active lane, and recovery code could escalate …
- **`4cee9ac1`** — Refresh external review snapshot for 1840993a
  - evolution: Fact: the Q40/Q42 live-run findings showed two separate authority leaks. A dashboard/observer lane could still slide into implementation edits while another agent owned the active lane, and recovery code could escalate …
### Active MP scope (from MASTER_PLAN.md)

- `dev/active/devctl_reporting_upgrade.md` is the phased `devctl` reporting/CIHub specification, but not a separate execution tracker; implementation tasks stay in this file under `MP-297..MP-300`, `MP-303`, `MP-306`, `MP…
- `dev/active/autonomous_control_plane.md` is the autonomous loop + mobile control-plane execution spec; implementation tasks stay in this file under `MP-325..MP-338, MP-340`.
- `dev/active/loop_chat_bridge.md` is the loop artifact-to-chat suggestion coordination runbook; execution evidence and operator handoffs for this path stay there under `MP-338`.
- `dev/active/naming_api_cohesion.md` is the naming/API cohesion execution spec; implementation tasks stay in this file under `MP-267`.
- `dev/active/ide_provider_modularization.md` is the IDE/provider adapter modularization execution spec; implementation tasks stay in this file under `MP-346`, `MP-354`.
- contract slice for MP-355 plus the temporary markdown-swarm operating mode
- `dev/active/ralph_guardrail_control_plane.md` is the Ralph guardrail control plane execution spec; implementation tasks stay in this file under `MP-360..MP-367`.
- `dev/active/review_probes.md` is the review-probe execution spec; implementation tasks stay in this file under `MP-368..MP-375`.
- companion under `MP-376`, not a second main product plan; implementation
- architecture plan for the extracted AI-governance system under `MP-377`.

## 8. Known gaps and open items

- open governance findings: 86

### Startup advisories
- checkpoint_allowed: worktree_dirty_within_budget

### Stale warnings
- Move straight to the governed push path.

### Open gap rows
- **governance_open** (`dev/scripts/devctl/security/codeql.py`): subprocess_missing_timeout: 
- **governance_open** (`dev/scripts/devctl/integrations/import_core.py`): subprocess_missing_timeout: 
- **governance_open** (`app/operator_console/launch_support.py`): subprocess_missing_timeout: 
- **governance_open** (`dev/scripts/devctl/common.py`): threading_shared_state_no_lock: 
- **governance_open** (`dev/scripts/devctl/review_channel/bridge_projection_state.py`): none_safety_chained_get_crash: 
- **governance_open** (`app/operator_console/state/review/operator_decisions.py`): none_safety_chained_get_crash: 
- **governance_open** (`dev/scripts/devctl/autonomy/run_render.py`): none_safety_chained_get_crash: 
- **governance_open** (`dev/scripts/devctl/autonomy/report_helpers.py`): none_safety_chained_get_crash: 

---

Projection produced by `devctl review-snapshot`. Generation stamp `snap-69aba6310adb` binds this file to HEAD `6e8d96c272e2`; if they drift, the freshness guard will fail CI. When the latest commit only refreshes this generated snapshot, the guard accepts this file as bound to that commit's parent code state.
