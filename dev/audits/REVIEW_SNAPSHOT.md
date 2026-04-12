# VoiceTerm — Review Snapshot

> Deterministically generated from typed governance state. Do not edit by hand — rerun `devctl review-snapshot --write`.

## Quick status

- Branch: `codex-role-portability`
- HEAD: `763be95da41f` — Refresh external review snapshot for e8ccc7e7
- Tree hash: `ff64a6cec366`
- Generation stamp: `snap-381ae7ad5d99`
- Generated at (UTC): 2026-04-12T14:41:21Z
- Push decision: `await_checkpoint` — staged_index_budget_exceeded
- Reviewer mode: `single_agent` (interaction: `local_terminal`)
- Pipeline state: `n/a` (approval: `n/a`)
- Delta since last snapshot: 24 commits, 106 files, +8968/-1757
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
- Current branch: `codex-role-portability`
- HEAD SHA: `763be95da41f3f2424ca1a7b3023f4f1fb6d8406`
- HEAD author: Justin Guida
- HEAD timestamp (UTC): 2026-04-12T08:24:00-04:00

## 2. Governance state

### Push decision
- action: `await_checkpoint`
- reason: staged_index_budget_exceeded
- push_eligible_now: False
- worktree_clean: False
- staged_path_count: 32
- unstaged_path_count: 0
- next_step_command: `n/a`
- latest_push_report: `dev/reports/push/latest.json`
- publication_backlog: queued
- publication_guidance: Local branch still has unpublished work waiting for governed push once the current slice is checkpoint-clean.

### Reviewer runtime
- reviewer_mode: `single_agent`
- reviewer_freshness: unknown
- reviewer_publish_clear: True
- interaction_mode: `local_terminal`

### Remote commit pipeline
- state: `n/a`
- approval_state: `n/a`

### Work intake
- active plan: **Master Plan (Active, Unified)**
- plan path: `dev/active/MASTER_PLAN.md`
- active MP scope: all active MP execution state
- advisory: `checkpoint_before_continue` — staged_index_budget_exceeded
- checkpoint_required: **yes**

## 3. Delta — what changed since the previous snapshot

Range: last 24 commits ending at `763be95da41f`

- commits: 24
- files changed: 106
- insertions: +8968
- deletions: -1757
- bundle classes touched: tooling, docs
- authority surfaces touched: 17 file(s)

### Commits

| # | SHA | Subject | Files | +/- | Bundle | Risk |
|---|---|---|---|---|---|---|
| 1 | `763be95d` | Refresh external review snapshot for e8ccc7e7 | 1 | +63/-64 | tooling |  |
| 2 | `e8ccc7e7` | review_channel: remote-control attachment counts as live co… | 11 | +258/-61 | tooling |  |
| 3 | `70e2544f` | docs(audit): dashboard-loop ticks 33-48 + liveness symmetry… | 3 | +285/-51 | tooling |  |
| 4 | `5cc9e8d9` | Refresh external review snapshot for 01e436d0 | 1 | +67/-65 | tooling |  |
| 5 | `01e436d0` | docs+workflow: propagate bundle.tooling publications-ignore… | 7 | +72/-49 | tooling |  |
| 6 | `bb6bbef4` | Refresh external review snapshot for 0db1267c | 1 | +56/-59 | tooling |  |
| 7 | `0db1267c` | bundles(tooling): ignore publications warning source in str… | 3 | +53/-50 | tooling |  |
| 8 | `49dcf13e` | Refresh external review snapshot for 353f3bb6 | 1 | +59/-62 | tooling |  |
| 9 | `353f3bb6` | review_channel: priority selector drives current_session.cu… | 6 | +69/-51 | tooling |  |
| 10 | `0d2cb8ad` | Refresh external review snapshot for 637a4ad9 | 1 | +59/-62 | tooling |  |
| 11 | `637a4ad9` | docs: slice-closure updates from Codex for the review_chann… | 4 | +97/-42 | docs |  |
| 12 | `7a3091c5` | plans: record review_channel trigger primitive slice in act… | 5 | +101/-66 | tooling |  |
| 13 | `de08f5c9` | review_channel: split enrich_event_review_state to satisfy… | 2 | +103/-58 | tooling |  |
| 14 | `52878653` | Refresh external review snapshot for 061a1261 | 1 | +54/-51 | tooling |  |
| 15 | `061a1261` | review_channel: packet_control_loop priority selection + co… | 5 | +350/-62 | tooling |  |
| 16 | `2cd74a7c` | Refresh external review snapshot for 6db71aca | 1 | +107/-85 | tooling |  |
| 17 | `6db71aca` | review_channel: typed participant authoritative + action_re… | 78 | +3818/-316 | tooling |  |
| 18 | `a3e3347c` | docs(audit): dashboard-loop tick 1-32 + typed findings 0200… | 3 | +2200/-99 | tooling |  |
| 19 | `0936a4e5` | Refresh external review snapshot for 2e46f645 | 1 | +67/-66 | tooling |  |
| 20 | `2e46f645` | fix(runtime): keep local single-agent takeover local | 18 | +425/-113 | tooling |  |
| 21 | `47e2b4e1` | Clarify platform boundary and startup mutability routing | 17 | +358/-46 | tooling |  |
| 22 | `30dcf434` | Refresh external review snapshot for 8a05ad7f | 1 | +55/-52 | tooling |  |
| 23 | `8a05ad7f` | docs(bridge): scribe capture live Codex state + autonomy pl… | 3 | +72/-65 | tooling |  |
| 24 | `936cbc3d` | fix(review-snapshot): gate single_agent lane on reviewer ve… | 3 | +120/-62 | tooling |  |

### Files

| Path | Bundle | +/- |
|---|---|---|
| `.github/workflows/tooling_control_plane.yml` | tooling | +1/-1 |
| `AGENTS.md` | docs | +33/-8 |
| `bridge.md` | docs | +181/-78 |
| `dev/active/MASTER_PLAN.md` | tooling | +103/-1 |
| `dev/active/ai_governance_platform.md` | tooling | +45/-1 |
| `dev/active/autonomous_control_plane.md` | tooling | +2/-0 |
| `dev/active/remote_commit_pipeline.md` | tooling | +28/-0 |
| `dev/active/remote_control_runtime.md` | tooling | +80/-0 |
| `dev/audits/LIVE_RUN.md` | tooling | +2229/-0 |
| `dev/audits/REVIEW_SNAPSHOT.md` | tooling | +1380/-1319 |
| `dev/config/devctl_repo_policy.json` | tooling | +1/-1 |
| `dev/config/git_hooks/pre-push-governed-push.sh` | tooling | +1/-1 |
| `dev/config/templates/claude_instructions.template.md` | tooling | +7/-5 |
| `dev/config/templates/portable_governance_repo_setup.template.md` | tooling | +5/-3 |
| `dev/guides/DEVELOPMENT.md` | docs | +43/-5 |
| `dev/history/ENGINEERING_EVOLUTION.md` | tooling | +163/-1 |
| `dev/scripts/README.md` | tooling | +56/-12 |
| `dev/scripts/checks/platform_contract_closure/emitter_parity.py` | tooling | +5/-0 |
| `dev/scripts/devctl/bundles/registry.py` | tooling | +1/-1 |
| `dev/scripts/devctl/commands/agent_mind/slice_builder.py` | tooling | +58/-0 |
| `dev/scripts/devctl/commands/dashboard.py` | tooling | +10/-0 |
| `dev/scripts/devctl/commands/dashboard_typed_state.py` | tooling | +12/-1 |
| `dev/scripts/devctl/commands/governance/startup_context_render.py` | tooling | +11/-5 |
| `dev/scripts/devctl/commands/review_channel/_render_bridge.py` | tooling | +7/-0 |
| `dev/scripts/devctl/commands/review_channel/_reviewer.py` | tooling | +7/-0 |
| `dev/scripts/devctl/commands/review_channel/bridge_handler.py` | tooling | +7/-0 |
| `dev/scripts/devctl/commands/review_channel/bridge_render.py` | tooling | +3/-15 |
| `dev/scripts/devctl/commands/review_channel/ensure.py` | tooling | +23/-1 |
| `dev/scripts/devctl/commands/review_channel/event_handler.py` | tooling | +67/-0 |
| `dev/scripts/devctl/commands/review_channel/reviewer_runtime_snapshot.py` | tooling | +44/-7 |
| `dev/scripts/devctl/commands/review_channel_command/models.py` | tooling | +1/-0 |
| `dev/scripts/devctl/commands/vcs/commit.py` | tooling | +25/-2 |
| `dev/scripts/devctl/commands/vcs/governed_executor.py` | tooling | +16/-0 |
| `dev/scripts/devctl/commands/vcs/governed_executor_actions.py` | tooling | +21/-4 |
| `dev/scripts/devctl/commands/vcs/governed_executor_support.py` | tooling | +59/-0 |
| `dev/scripts/devctl/commands/vcs/governed_executor_validation.py` | tooling | +76/-0 |
| `dev/scripts/devctl/commands/vcs/push.py` | tooling | +70/-18 |
| `dev/scripts/devctl/commands/vcs/push_flow.py` | tooling | +17/-11 |
| `dev/scripts/devctl/commands/vcs/push_snapshot.py` | tooling | +41/-5 |
| `dev/scripts/devctl/governance/bootstrap_guide.py` | tooling | +5/-2 |
| _66 more files trimmed_ | | |

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

- **authority_surface**: Typed authority surface touched (`dev/active/remote_commit_pipeline.md`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/review_channel/bridge_handler.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/review_channel/bridge_render.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/review_channel/reviewer_runtime_snapshot.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_actions.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_support.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_validation.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/review_channel/reviewer_runtime_doctor.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/remote_commit_pipeline_models.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/startup_push_decision.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/review_channel/test_reviewer_runtime_doctor.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/runtime/test_startup_context.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/vcs/test_governed_executor.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/startup_context.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/review_snapshot_state.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/runtime/test_review_snapshot.py`) — Review contract-level invariants for this file
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/review_channel/event_models.py`) — Commit 6db71aca changed dev/scripts/devctl/review_channel/event_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/remote_commit_pipeline_models.py`) — Commit 6db71aca changed dev/scripts/devctl/runtime/remote_commit_pipeline_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/review_state_models.py`) — Commit 6db71aca changed dev/scripts/devctl/runtime/review_state_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/validation_contracts.py`) — Commit 6db71aca changed dev/scripts/devctl/runtime/validation_contracts.py

### Suggested verification commands

- `python3 dev/scripts/devctl.py check --profile ci`
- `python3 dev/scripts/devctl.py probe-report --format md`
- `python3 dev/scripts/devctl.py docs-check --strict-tooling`
- `python3 dev/scripts/devctl.py governance-review --format md`
- `python3 dev/scripts/devctl.py check-router --format md`

## 7. Reasoning — why these changes landed

### Per-commit rationale

- **`763be95d`** — Refresh external review snapshot for e8ccc7e7
  - evolution: Fact: the architecture docs already said reviewer, implementer, and operator are role-first contracts over one shared backend, but the active execution plans still mixed that with live-proof language that read as `Codex…
- **`e8ccc7e7`** — review_channel: remote-control attachment counts as live conductor in single_agent mode
  - In single_agent reviewer mode, attach_conductor_session_state() now reads
  - active remote-control attachments via load_remote_control_attachments() and
  - adds their providers to active_providers alongside conductor-session-file
  - evolution: Fact: the architecture docs already said reviewer, implementer, and operator are role-first contracts over one shared backend, but the active execution plans still mixed that with live-proof language that read as `Codex…
- **`70e2544f`** — docs(audit): dashboard-loop ticks 33-48 + liveness symmetry fix verification
  - Post-push dashboard observations from the Claude remote-control lane:
  - - Ticks 33-35: post-push steady-state verification (HEAD synced, worktree clean)
  - - Tick 36: detected new Codex session PID 90192 on ttys014
  - evolution: Fact: the architecture docs already said reviewer, implementer, and operator are role-first contracts over one shared backend, but the active execution plans still mixed that with live-proof language that read as `Codex…
- **`5cc9e8d9`** — Refresh external review snapshot for 01e436d0
- **`01e436d0` | MPs: MP-377** — docs+workflow: propagate bundle.tooling publications-ignore to CI + maintainer docs
  - Co-modification required by docs-check --strict-tooling after
  - dev/scripts/devctl/bundles/registry.py extended the bundle.tooling
  - hygiene command with --ignore-warning-source publications:
  - plan: `dev/active/ai_governance_platform.md`
  - plan: `dev/active/platform_authority_loop.md`
  - plan: `dev/active/autonomous_governance_loop_v2.md`
  - plan: `dev/active/remote_commit_pipeline.md`
  - plan: `dev/active/PLAN_FORMAT.md`
- **`bb6bbef4`** — Refresh external review snapshot for 0db1267c
- **`0db1267c`** — bundles(tooling): ignore publications warning source in strict hygiene
  - The bundle.tooling hygiene gate fails on long-standing external-publication
  - drift for terminal-as-interface (tracked at 369cb67b3c85 vs 380+ impacted
  - paths across HEAD). That drift is unrelated to review-channel / runtime
- **`49dcf13e`** — Refresh external review snapshot for 353f3bb6
- **`353f3bb6`** — review_channel: priority selector drives current_session.current_instruction
  - Wires the action-request-first priority selection from
  - packet_control_loop.select_priority_pending_packet into
  - current_session.current_instruction so read-only dashboard and status
- **`0d2cb8ad`** — Refresh external review snapshot for 637a4ad9
- **`637a4ad9`** — docs: slice-closure updates from Codex for the review_channel trigger primitive
  - Concurrent with Claude's sequential push attempts, Codex finished its slice
  - documentation pass:
  - - AGENTS.md: note the new action_request_delivery + packet_control_loop
- **`7a3091c5` | MPs: MP-380, MP-387** — plans: record review_channel trigger primitive slice in active docs
  - Codex continuing its slice with plan-doc updates landing in the working
  - tree concurrently with Claude's governed push attempts:
  - - dev/active/MASTER_PLAN.md: mark the packet_control_loop + action_request
  - plan: `dev/active/remote_control_runtime.md`
- **`de08f5c9`** — review_channel: split enrich_event_review_state to satisfy function-length gate
  - check_code_shape flagged enrich_event_review_state at 172 lines (110-281),
  - over the 150-line Python function default. Extract the _compat-merging
  - block (service_identity, attach_auth_policy, push_enforcement, doctor,
- **`52878653`** — Refresh external review snapshot for 061a1261
- **`061a1261`** — review_channel: packet_control_loop priority selection + control hints
  - Adds packet_control_loop.py with select_priority_pending_packet(), which
  - picks the highest-priority live pending packet (action_request class first,
  - then findings/questions/instructions) and returns control-state metadata
- **`2cd74a7c`** — Refresh external review snapshot for 6db71aca
- **`6db71aca` | MPs: MP-355** — review_channel: typed participant authoritative + action_request delivery primitive + dashboard/control-plane parity
  - Closes six of the eight scaffolding layers named in the architectural meta-
  - finding this session. Introduces the action_request_delivery primitive that
  - stamps delivery_emitted_at_utc / delivery_observed_at_utc / delivery_observed_by
  - plan: `dev/active/review_channel.md`
- **`a3e3347c`** — docs(audit): dashboard-loop tick 1-32 + typed findings 0200-0237
  - Durable audit trail from this remote-dashboard session covering:
  - - 32 dashboard-loop ticks with verbatim typed state, parity matrix,
  -   agent-mind cursor polls, and target-file mtime deltas
- **`0936a4e5`** — Refresh external review snapshot for 2e46f645
- **`2e46f645`** — fix(runtime): keep local single-agent takeover local
- **`47e2b4e1`** — Clarify platform boundary and startup mutability routing
- **`30dcf434`** — Refresh external review snapshot for 8a05ad7f
- **`8a05ad7f`** — docs(bridge): scribe capture live Codex state + autonomy plan drift (pre-push Q91b workaround)
- **`936cbc3d`** — fix(review-snapshot): gate single_agent lane on reviewer verdict, not mode alone
  - Codex verdict at instruction_revision 214e376fabc0 flagged that
  - review_snapshot_state.py:107-137 only downgraded push_eligible_now and
  - the governed push next_step_command when effective_reviewer_mode ==
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
- checkpoint_before_continue: staged_index_budget_exceeded

### Stale warnings
- Keep editing the current slice.
- Move straight to the governed push path.

---

Projection produced by `devctl review-snapshot`. Generation stamp `snap-381ae7ad5d99` binds this file to HEAD `763be95da41f`; if they drift, the freshness guard will fail CI. When the latest commit only refreshes this generated snapshot, the guard accepts this file as bound to that commit's parent code state.
