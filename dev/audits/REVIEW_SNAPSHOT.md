# VoiceTerm — Review Snapshot

> Deterministically generated from typed governance state. Do not edit by hand — rerun `devctl review-snapshot --write`.

## Quick status

- Branch: `feature/governance-quality-sweep`
- HEAD: `f3bbca1813c0` — fix(review-channel): typed preflight gate — reviewer-checkpoint refuses while inbox has unread packets
- Tree hash: `8a5d57079571`
- Generation stamp: `snap-7681cca9ac5c`
- Generated at (UTC): 2026-04-11T07:52:41Z
- Push decision: `run_devctl_push` — push_preconditions_satisfied
- Reviewer mode: `single_agent` (interaction: `remote_control`)
- Pipeline state: `n/a` (approval: `n/a`)
- Delta since last snapshot: 24 commits, 33 files, +5419/-1908
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
- HEAD SHA: `f3bbca1813c0dd90ae2771b25a45ea682850f74f`
- HEAD author: Justin Guida
- HEAD timestamp (UTC): 2026-04-11T03:52:01-04:00

## 2. Governance state

### Push decision
- action: `run_devctl_push`
- reason: push_preconditions_satisfied
- push_eligible_now: True
- worktree_clean: True
- staged_path_count: 0
- unstaged_path_count: 0
- next_step_command: `python3 dev/scripts/devctl.py push --execute`
- latest_push_report: `dev/reports/push/latest.json`
- latest_push_report_state: `published_remote` (post_push_bundle_pending)
- publication_backlog: urgent
- publication_guidance: 27 local commit(s) waiting for governed push. Run `python3 dev/scripts/devctl.py push --execute` now.

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
- advisory: `push_allowed` — worktree_clean_and_review_accepted

## 3. Delta — what changed since the previous snapshot

Range: last 24 commits ending at `f3bbca1813c0`

- commits: 24
- files changed: 33
- insertions: +5419
- deletions: -1908
- bundle classes touched: tooling, docs
- risk add-ons triggered: Parser / ANSI boundary
- authority surfaces touched: 5 file(s)

### Commits

| # | SHA | Subject | Files | +/- | Bundle | Risk |
|---|---|---|---|---|---|---|
| 1 | `f3bbca18` | fix(review-channel): typed preflight gate — reviewer-checkp… | 8 | +539/-135 | tooling | Parser / ANSI boundary |
| 2 | `8bb338bc` | feat(runtime): Q99 — canonical startup_blocker_decision ker… | 8 | +495/-100 | tooling |  |
| 3 | `2a1977cb` | fix(runtime,governance): Codex P1 — pacing live-rebuild + a… | 6 | +615/-141 | tooling |  |
| 4 | `b0885088` | Refresh external review snapshot for 2730689c | 1 | +104/-80 | tooling |  |
| 5 | `2730689c` | docs(bridge): neutralize stale Q37 Operator Direction block | 2 | +91/-126 | docs |  |
| 6 | `31be10ee` | Refresh external review snapshot for ee79f9c3 | 1 | +108/-72 | tooling |  |
| 7 | `ee79f9c3` | fix(review-snapshot): Q92-C7 — consult live reviewer verdic… | 3 | +325/-100 | tooling |  |
| 8 | `eb4a15b6` | Refresh external review snapshot for 38cb9e95 | 1 | +120/-100 | tooling |  |
| 9 | `38cb9e95` | fix(review-channel): Q94 — emit participant_liveness_expire… | 6 | +437/-111 | tooling |  |
| 10 | `63bd97e1` | Refresh external review snapshot for 7f2f925f | 1 | +111/-93 | tooling |  |
| 11 | `7f2f925f` | docs(claude): force typed ingestion — --format json over --… | 5 | +69/-96 | tooling |  |
| 12 | `09565fe7` | Refresh external review snapshot for 4a67140e | 1 | +42/-40 | tooling |  |
| 13 | `4a67140e` | docs(bridge): scribe capture Codex fdd35a6207cc verdict (Q9… | 2 | +46/-47 | docs |  |
| 14 | `3c294f0d` | Refresh external review snapshot for 0247df7c | 1 | +41/-42 | tooling |  |
| 15 | `0247df7c` | docs(bridge): scribe capture for Q98-Q99 post (Q91b workaro… | 2 | +64/-61 | docs |  |
| 16 | `84006af1` | docs(audit): Q98-Q99 — ChatGPT proposal audit + 5-field pro… | 2 | +431/-71 | tooling |  |
| 17 | `a805652b` | Refresh external review snapshot for 186f8974 | 1 | +45/-40 | tooling |  |
| 18 | `186f8974` | docs(bridge): capture Codex fresh verdict (Q91b workaround,… | 2 | +67/-63 | docs |  |
| 19 | `d0d60a3e` | docs(audit): Q94-Q97 — 5-agent audit verdict, MasterAuthori… | 2 | +486/-72 | tooling |  |
| 20 | `6e8d96c2` | Refresh external review snapshot for b505d809 | 1 | +61/-63 | tooling |  |
| 21 | `b505d809` | docs(bridge): capture Codex reviewer verdict state (Q91b wo… | 2 | +84/-83 | docs |  |
| 22 | `a662deb5` | docs(audit): Q92 — 14+ prose-as-authority fields across gov… | 2 | +539/-48 | tooling |  |
| 23 | `d8c71114` | Refresh external review snapshot for 8243c5ab | 1 | +64/-70 | tooling |  |
| 24 | `8243c5ab` | docs(audit): Q91 — dashboard checkpoint, role correction, 4… | 2 | +435/-54 | tooling |  |

### Files

| Path | Bundle | +/- |
|---|---|---|
| `bridge.md` | docs | +75/-77 |
| `dev/audits/LIVE_RUN.md` | tooling | +1665/-0 |
| `dev/audits/REVIEW_SNAPSHOT.md` | tooling | +1681/-1716 |
| `dev/scripts/devctl/commands/dashboard.py` | tooling | +8/-2 |
| `dev/scripts/devctl/commands/dashboard_builders.py` | tooling | +27/-22 |
| `dev/scripts/devctl/commands/governance/startup_context.py` | tooling | +23/-0 |
| `dev/scripts/devctl/commands/governance/startup_context_advisory_coherence.py` | tooling | +132/-0 |
| `dev/scripts/devctl/commands/review_channel/_reviewer.py` | tooling | +9/-0 |
| `dev/scripts/devctl/governance/surface_context.py` | tooling | +1/-1 |
| `dev/scripts/devctl/governance/system_catalog_bootstrap.py` | tooling | +2/-2 |
| `dev/scripts/devctl/review_channel/event_reducer.py` | tooling | +18/-0 |
| `dev/scripts/devctl/review_channel/parser_bridge_controls.py` | tooling | +11/-0 |
| `dev/scripts/devctl/review_channel/reviewer_state.py` | tooling | +18/-3 |
| `dev/scripts/devctl/review_channel/reviewer_state_support.py` | tooling | +9/-0 |
| `dev/scripts/devctl/review_channel/session_liveness_events.py` | tooling | +130/-0 |
| `dev/scripts/devctl/review_channel/state.py` | tooling | +1/-0 |
| `dev/scripts/devctl/review_channel/status_projection_helpers.py` | tooling | +26/-0 |
| `dev/scripts/devctl/review_channel/write_preconditions.py` | tooling | +84/-0 |
| `dev/scripts/devctl/runtime/control_plane_resolve.py` | tooling | +33/-35 |
| `dev/scripts/devctl/runtime/review_snapshot_state.py` | tooling | +95/-3 |
| `dev/scripts/devctl/runtime/startup_blocker_decision.py` | tooling | +212/-0 |
| `dev/scripts/devctl/runtime/startup_context.py` | tooling | +44/-27 |
| `dev/scripts/devctl/runtime/work_intake_pacing.py` | tooling | +22/-6 |
| `dev/scripts/devctl/tests/commands/governance/test_startup_context.py` | tooling | +200/-0 |
| `dev/scripts/devctl/tests/commands/reporting/test_dashboard.py` | tooling | +38/-10 |
| `dev/scripts/devctl/tests/governance/test_render_surfaces.py` | tooling | +1/-1 |
| `dev/scripts/devctl/tests/governance/test_system_catalog.py` | tooling | +2/-2 |
| `dev/scripts/devctl/tests/review_channel/test_reviewer_checkpoint_inputs.py` | tooling | +1/-1 |
| `dev/scripts/devctl/tests/review_channel/test_reviewer_inbox_gate.py` | tooling | +265/-0 |
| `dev/scripts/devctl/tests/review_channel/test_session_liveness_events.py` | tooling | +169/-0 |
| `dev/scripts/devctl/tests/runtime/test_review_snapshot.py` | tooling | +168/-0 |
| `dev/scripts/devctl/tests/runtime/test_startup_blocker_decision.py` | tooling | +128/-0 |
| `dev/scripts/devctl/tests/runtime/test_work_intake_pacing_snapshot_preference.py` | tooling | +121/-0 |

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
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/governance/startup_context.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/commands/governance/test_startup_context.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/review_snapshot_state.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/runtime/test_review_snapshot.py`) — Review contract-level invariants for this file

### Suggested verification commands

- `python3 dev/scripts/devctl.py check --profile ci`
- `python3 dev/scripts/devctl.py probe-report --format md`
- `python3 dev/scripts/devctl.py docs-check --strict-tooling`
- `python3 dev/scripts/devctl.py governance-review --format md`
- `python3 dev/scripts/devctl.py check-router --format md`

## 7. Reasoning — why these changes landed

### Per-commit rationale

- **`f3bbca18`** — fix(review-channel): typed preflight gate — reviewer-checkpoint refuses while inbox has unread packets
  - Root cause: across 4 Codex review sessions in a single dashboard session,
  - Codex never ran `review-channel --action inbox --target codex --status
  - pending` before writing a reviewer-checkpoint verdict. Two typed finding
- **`8bb338bc`** — feat(runtime): Q99 — canonical startup_blocker_decision kernel (top_blocker/next_action)
  - Create runtime/startup_blocker_decision.py with BlockerSnapshot dataclass
  - and derive_blocker_decision() canonical reducer. Wire into
  - build_startup_context() so top_blocker and next_action are computed once
- **`2a1977cb`** — fix(runtime,governance): Codex P1 — pacing live-rebuild + advisory_action contradiction
  - Finding 1: work_intake_pacing.py:158-176 forced a full context graph
  - live rebuild whenever the saved snapshot's HEAD did not match the
  - current HEAD, making startup-context hang on every fresh commit (repo
- **`b0885088`** — Refresh external review snapshot for 2730689c
- **`2730689c`** — docs(bridge): neutralize stale Q37 Operator Direction block
  - Replaces the stale Q37 Phase 1 operator-direction content (which
  - referenced efcb2cd9, already upstream) with fresh operator guidance
  - pointing at the real active slice: Q98/Q99 integration delta + Codex's
- **`31be10ee`** — Refresh external review snapshot for ee79f9c3
- **`ee79f9c3`** — fix(review-snapshot): Q92-C7 — consult live reviewer verdict before emitting push_eligible_now
  - devctl review-snapshot --write now checks the live ReviewerObservation
  - verdict before emitting push_eligible_now: True or next_step_command=
  - python3 dev/scripts/devctl.py push --execute. When the live verdict is
- **`eb4a15b6`** — Refresh external review snapshot for 38cb9e95
- **`38cb9e95`** — fix(review-channel): Q94 — emit participant_liveness_expired on heartbeat TTL expiry
  - Wire the existing liveness detection (PID probe + _pid_is_alive +
  - SessionLivenessEvidence + detached_exit auto-set) to the existing event
  - reducer so dead participants auto-decrement live_*_total counters.
- **`63bd97e1`** — Refresh external review snapshot for 7f2f925f
- **`7f2f925f`** — docs(claude): force typed ingestion — --format json over --format summary (Q98 one-line fix)
  - CLAUDE.md now instructs the AI consumer to read startup-context via
  - --format json (typed JSON StartupContext dataclass) instead of
  - --format summary (markdown prose). Generator change, not direct
- **`09565fe7`** — Refresh external review snapshot for 4a67140e
- **`4a67140e`** — docs(bridge): scribe capture Codex fdd35a6207cc verdict (Q91b, pre-merge)
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
- push_allowed: worktree_clean_and_review_accepted

### Stale warnings
- Stop because nothing remains to push.

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

Projection produced by `devctl review-snapshot`. Generation stamp `snap-7681cca9ac5c` binds this file to HEAD `f3bbca1813c0`; if they drift, the freshness guard will fail CI. When the latest commit only refreshes this generated snapshot, the guard accepts this file as bound to that commit's parent code state.
