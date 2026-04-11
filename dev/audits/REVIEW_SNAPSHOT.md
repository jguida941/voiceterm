# VoiceTerm — Review Snapshot

> Deterministically generated from typed governance state. Do not edit by hand — rerun `devctl review-snapshot --write`.

## Quick status

- Branch: `worktree-agent-a189c06e`
- HEAD: `3c294f0d4437` — Refresh external review snapshot for 0247df7c
- Tree hash: `ff28c8c0a7c4`
- Generation stamp: `snap-5270f3300a56`
- Generated at (UTC): 2026-04-11T07:36:10Z
- Push decision: `await_checkpoint` — staged_index_present
- Reviewer mode: `unknown` (interaction: `unresolved`)
- Pipeline state: `n/a` (approval: `n/a`)
- Delta since last snapshot: 24 commits, 54 files, +7533/-1608
- Governance findings: 0 open / 0 fixed / 0 total
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
- Current branch: `worktree-agent-a189c06e`
- HEAD SHA: `3c294f0d44379460274ed4b85675d2bd9a0161df`
- HEAD author: Justin Guida
- HEAD timestamp (UTC): 2026-04-11T02:49:55-04:00

## 2. Governance state

### Push decision
- action: `await_checkpoint`
- reason: staged_index_present
- push_eligible_now: False
- worktree_clean: False
- staged_path_count: 7
- unstaged_path_count: 0
- next_step_command: `n/a`
- latest_push_report: `dev/reports/push/latest.json`
- latest_push_report_state: `published_remote` (post_push_bundle_pending)
- publication_backlog: queued
- publication_guidance: Local branch still has unpublished work waiting for governed push once the current slice is checkpoint-clean.

### Reviewer runtime
- reviewer_mode: `unknown`
- reviewer_freshness: unknown
- reviewer_publish_clear: False
- interaction_mode: `unresolved`
- implementation_blocked: yes — typed_review_state_required

### Remote commit pipeline
- state: `n/a`
- approval_state: `n/a`

### Work intake
- advisory: `repair_reviewer_loop` — typed_review_state_required

## 3. Delta — what changed since the previous snapshot

Range: last 24 commits ending at `3c294f0d4437`

- commits: 24
- files changed: 54
- insertions: +7533
- deletions: -1608
- bundle classes touched: tooling, docs
- authority surfaces touched: 3 file(s)

### Commits

| # | SHA | Subject | Files | +/- | Bundle | Risk |
|---|---|---|---|---|---|---|
| 1 | `3c294f0d` | Refresh external review snapshot for 0247df7c | 1 | +41/-42 | tooling |  |
| 2 | `0247df7c` | docs(bridge): scribe capture for Q98-Q99 post (Q91b workaro… | 2 | +64/-61 | docs |  |
| 3 | `84006af1` | docs(audit): Q98-Q99 — ChatGPT proposal audit + 5-field pro… | 2 | +431/-71 | tooling |  |
| 4 | `a805652b` | Refresh external review snapshot for 186f8974 | 1 | +45/-40 | tooling |  |
| 5 | `186f8974` | docs(bridge): capture Codex fresh verdict (Q91b workaround,… | 2 | +67/-63 | docs |  |
| 6 | `d0d60a3e` | docs(audit): Q94-Q97 — 5-agent audit verdict, MasterAuthori… | 2 | +486/-72 | tooling |  |
| 7 | `6e8d96c2` | Refresh external review snapshot for b505d809 | 1 | +61/-63 | tooling |  |
| 8 | `b505d809` | docs(bridge): capture Codex reviewer verdict state (Q91b wo… | 2 | +84/-83 | docs |  |
| 9 | `a662deb5` | docs(audit): Q92 — 14+ prose-as-authority fields across gov… | 2 | +539/-48 | tooling |  |
| 10 | `d8c71114` | Refresh external review snapshot for 8243c5ab | 1 | +64/-70 | tooling |  |
| 11 | `8243c5ab` | docs(audit): Q91 — dashboard checkpoint, role correction, 4… | 2 | +435/-54 | tooling |  |
| 12 | `ef3f08ae` | Refresh external review snapshot for dfcd171a | 1 | +71/-67 | tooling |  |
| 13 | `dfcd171a` | docs(governance): Q78-Q90 — loop v1 retrospective and loop… | 11 | +2160/-59 | tooling |  |
| 14 | `5a92fa03` | feat(context-graph): Q78 Phase 0 — expose typed contracts a… | 9 | +557/-74 | tooling |  |
| 15 | `3566b16b` | Refresh external review snapshot for 9be23299 | 1 | +59/-59 | tooling |  |
| 16 | `9be23299` | fix(governance): Q70 — collapse action_routing onto single… | 10 | +191/-137 | tooling |  |
| 17 | `4db52ae8` | Refresh external review snapshot for a77c3b3f | 1 | +58/-57 | tooling |  |
| 18 | `a77c3b3f` | docs(audit): Q70-Q75 — Codex architectural review of Q40-Q6… | 3 | +243/-49 | tooling |  |
| 19 | `48c7b5e9` | Refresh external review snapshot for b078731a | 1 | +58/-61 | tooling |  |
| 20 | `b078731a` | chore(code_shape): remove stale path overrides for files un… | 2 | +50/-59 | tooling |  |
| 21 | `e914ad33` | Refresh external review snapshot for 95140873 | 1 | +55/-58 | tooling |  |
| 22 | `95140873` | fix(bundles): dual import support for registry.py — works a… | 2 | +68/-51 | tooling |  |
| 23 | `6b51ebe9` | Refresh external review snapshot for 3f1d9950 | 1 | +71/-73 | tooling |  |
| 24 | `3f1d9950` | feat(governance): Q57 + Q58 — devctl monitor + registry-as-… | 27 | +1575/-137 | tooling |  |

### Files

| Path | Bundle | +/- |
|---|---|---|
| `AGENTS.md` | docs | +2/-0 |
| `bridge.md` | docs | +45/-39 |
| `dev/README.md` | docs | +2/-0 |
| `dev/active/INDEX.md` | tooling | +13/-2 |
| `dev/active/MASTER_PLAN.md` | tooling | +12/-0 |
| `dev/active/ai_governance_platform.md` | tooling | +11/-0 |
| `dev/active/autonomous_governance_loop_v2.md` | tooling | +473/-0 |
| `dev/active/platform_authority_loop.md` | tooling | +8/-0 |
| `dev/active/remote_control_runtime.md` | tooling | +8/-0 |
| `dev/audits/LIVE_RUN.md` | tooling | +3397/-1 |
| `dev/audits/REVIEW_SNAPSHOT.md` | tooling | +1348/-1368 |
| `dev/audits/reviews/q40_q67_codex_review_2026-04-10.md` | tooling | +71/-0 |
| `dev/guides/DEVELOPMENT.md` | docs | +7/-0 |
| `dev/history/ENGINEERING_EVOLUTION.md` | tooling | +29/-0 |
| `dev/scripts/README.md` | tooling | +16/-2 |
| `dev/scripts/checks/code_shape/code_shape_policy.py` | tooling | +0/-12 |
| `dev/scripts/devctl/autonomy/run_helpers.py` | tooling | +3/-2 |
| `dev/scripts/devctl/bundles/registry.py` | tooling | +111/-80 |
| `dev/scripts/devctl/cli_parser/entrypoint.py` | tooling | +3/-0 |
| `dev/scripts/devctl/commands/governance/simple_lanes_support.py` | tooling | +3/-2 |
| `dev/scripts/devctl/commands/listing.py` | tooling | +1/-0 |
| `dev/scripts/devctl/commands/monitor.py` | tooling | +13/-0 |
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
| `dev/scripts/devctl/runtime/action_routing.py` | tooling | +4/-5 |
| `dev/scripts/devctl/runtime/action_routing_coordination.py` | tooling | +4/-69 |
| `dev/scripts/devctl/runtime/coordination_loader.py` | tooling | +39/-7 |
| `dev/scripts/devctl/runtime/monitor_snapshot.py` | tooling | +318/-0 |
| `dev/scripts/devctl/runtime/monitor_snapshot_contracts.py` | tooling | +85/-0 |
| _14 more files trimmed_ | | |

## 4. Quality signals

### Governance review
- total findings: 0
- open: 0
- fixed: 0
- false positives: 0

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

- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/startup_context.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/runtime/test_startup_context.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/review_channel/test_reviewer_runtime_doctor.py`) — Review contract-level invariants for this file
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/work_intake_models.py`) — Commit 9be23299 changed dev/scripts/devctl/runtime/work_intake_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/monitor_snapshot_contracts.py`) — Commit 3f1d9950 changed dev/scripts/devctl/runtime/monitor_snapshot_contracts.py

### Suggested verification commands

- `python3 dev/scripts/devctl.py check --profile ci`
- `python3 dev/scripts/devctl.py probe-report --format md`
- `python3 dev/scripts/devctl.py docs-check --strict-tooling`
- `python3 dev/scripts/devctl.py governance-review --format md`
- `python3 dev/scripts/devctl.py check-router --format md`

## 7. Reasoning — why these changes landed

### Per-commit rationale

- **`3c294f0d`** — Refresh external review snapshot for 0247df7c
- **`0247df7c`** — docs(bridge): scribe capture for Q98-Q99 post (Q91b workaround)
- **`84006af1`** — docs(audit): Q98-Q99 — ChatGPT proposal audit + 5-field producer trace
  - Dashboard append from the 4-audit verification of ChatGPT's DecisionState
  - proposal against the actual codebase, plus a 5-authority-field producer
  - trace per ChatGPT's refined rule ("decision logic in one place").
- **`a805652b`** — Refresh external review snapshot for 186f8974
- **`186f8974`** — docs(bridge): capture Codex fresh verdict (Q91b workaround, Q97 pre-post)
  - Codex session 019d7b1d task_complete at 06:09:21Z wrote a new verdict
  - to bridge.md via review-channel, rotating current_instruction_revision
  - from 798446bc35db to f26e114a45d7 and landing a new finding list
- **`d0d60a3e`** — docs(audit): Q94-Q97 — 5-agent audit verdict, MasterAuthorityPacket rejected
  - Dashboard append from the 5-agent parallel audit Claude ran on
  - operator instruction ("audit the MasterAuthorityPacket idea against
  - existing architecture, I don't want to duplicate logic").
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

- open governance findings: 0

### Startup advisories
- repair_reviewer_loop: typed_review_state_required

### Stale warnings
- Cut a checkpoint before doing anything else.

---

Projection produced by `devctl review-snapshot`. Generation stamp `snap-5270f3300a56` binds this file to HEAD `3c294f0d4437`; if they drift, the freshness guard will fail CI. When the latest commit only refreshes this generated snapshot, the guard accepts this file as bound to that commit's parent code state.
