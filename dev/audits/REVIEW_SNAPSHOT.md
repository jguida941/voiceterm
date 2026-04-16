# VoiceTerm — Review Snapshot

> Deterministically generated from typed governance state. Do not edit by hand — rerun `devctl review-snapshot --write`.

## Quick status

- Branch: `feature/governance-quality-sweep`
- HEAD: `c09fb18c2be4` — Cache graph at escalation level — fixes ALL blocking paths (3.4s from 20s)
- Tree hash: `3646bcd0c563`
- Generation stamp: `snap-feee7581d4cc`
- Generated at (UTC): 2026-04-16T23:00:10Z
- Push decision: `await_review` — review_loop_relaunch_required
- Reviewer mode: `tools_only` (interaction: `local_terminal`)
- Pipeline state: `n/a` (approval: `n/a`)
- Delta since last snapshot: 25 commits, 11 files, +1065/-718
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
- HEAD SHA: `c09fb18c2be4e1b15c6ad2a75318cae563bde2be`
- HEAD author: Justin Guida
- HEAD timestamp (UTC): 2026-04-16T18:59:58-04:00

## 2. Governance state

### Push decision
- action: `await_review`
- reason: review_loop_relaunch_required
- push_eligible_now: False
- worktree_clean: True
- staged_path_count: 0
- unstaged_path_count: 0
- next_step_command: `python3 dev/scripts/devctl.py review-channel --action status --terminal none --format json`
- latest_push_report: `dev/reports/push/latest.json`
- latest_push_report_state: `blocked` (validation_failed)
- publication_backlog: queued
- publication_guidance: 1 local commit(s) waiting for governed push once review is accepted.

### Reviewer runtime
- reviewer_mode: `tools_only`
- reviewer_freshness: unknown
- reviewer_publish_clear: False
- interaction_mode: `local_terminal`
- implementation_blocked: yes — review_loop_relaunch_required

### Remote commit pipeline
- state: `n/a`
- approval_state: `n/a`

### Work intake
- active plan: **AI Governance Platform Plan**
- plan path: `dev/active/ai_governance_platform.md`
- active MP scope: `MP-377`
- advisory: `repair_reviewer_loop` — review_loop_relaunch_required

## 3. Delta — what changed since the previous snapshot

Range: last 25 commits ending at `c09fb18c2be4`

- commits: 25
- files changed: 11
- insertions: +1065
- deletions: -718
- bundle classes touched: tooling, docs

### Commits

| # | SHA | Subject | Files | +/- | Bundle | Risk |
|---|---|---|---|---|---|---|
| 1 | `c09fb18c` | Cache graph at escalation level — fixes ALL blocking paths… | 1 | +31/-1 | tooling |  |
| 2 | `ca4439d8` | Refresh external review snapshot for 38a05ad3 | 2 | +46/-47 | docs |  |
| 3 | `38a05ad3` | Fix rev_pkt_0819: emit liveness on real status path + HEAD… | 1 | +4/-0 | tooling |  |
| 4 | `058d5259` | Refresh external review snapshot for afbcc99f | 2 | +50/-53 | docs |  |
| 5 | `afbcc99f` | Fix reviewer loop death: HEAD change no longer kills sessio… | 1 | +13/-0 | tooling |  |
| 6 | `b6da49eb` | Refresh external review snapshot for bc266a94 | 2 | +55/-44 | docs |  |
| 7 | `bc266a94` | Wire ParticipantLivenessSignal into status projection (T08) | 1 | +30/-0 | tooling |  |
| 8 | `81a50662` | Refresh external review snapshot for 7f703e6d | 2 | +46/-65 | docs |  |
| 9 | `7f703e6d` | Fix snapshot sort: use timestamp portion of filename (Codex… | 1 | +3/-1 | tooling |  |
| 10 | `a0b6047a` | Refresh external review snapshot for 28d5d120 | 2 | +49/-56 | docs |  |
| 11 | `28d5d120` | Fix graph cache: load single latest snapshot, not all 362 f… | 1 | +12/-5 | tooling |  |
| 12 | `d918792c` | Refresh external review snapshot for 07262419 | 2 | +48/-41 | docs |  |
| 13 | `07262419` | Add ParticipantLivenessSignal typed model (MP377-P1-T08) | 1 | +87/-0 | tooling |  |
| 14 | `d62361a0` | Refresh external review snapshot for d2539063 | 2 | +54/-59 | docs |  |
| 15 | `d2539063` | Fix rev_pkt_0810: only override open_findings when backlog… | 1 | +6/-3 | tooling |  |
| 16 | `713cb440` | Refresh external review snapshot for 3f698e22 | 2 | +49/-62 | docs |  |
| 17 | `3f698e22` | Fix rev_pkt_0809: empty backlog always overrides stale brid… | 1 | +3/-3 | tooling |  |
| 18 | `403c547e` | Refresh external review snapshot for cbcb36bb | 2 | +52/-58 | docs |  |
| 19 | `cbcb36bb` | Fix Codex findings 0806/0807 + hybrid loop rewrite | 3 | +39/-43 | tooling |  |
| 20 | `d69ff4e1` | Refresh external review snapshot for 46679665 | 2 | +76/-67 | docs |  |
| 21 | `46679665` | Hybrid reviewer loop: ensure heartbeats + direct Codex rela… | 1 | +104/-38 | tooling |  |
| 22 | `7ac8911c` | Wire FindingBacklog into session-resume + cached graph rehy… | 2 | +67/-0 | tooling |  |
| 23 | `107bd54a` | Fix stale snapshot selection: use canonical resolver (Codex… | 1 | +55/-8 | tooling |  |
| 24 | `7d2a3897` | Refresh external review snapshot for 84d06a2d | 2 | +55/-63 | docs |  |
| 25 | `84d06a2d` | Use cached context graph in session-resume — fixes infinite… | 1 | +31/-1 | tooling |  |

### Files

| Path | Bundle | +/- |
|---|---|---|
| `bridge.md` | docs | +59/-64 |
| `dev/audits/REVIEW_SNAPSHOT.md` | tooling | +521/-551 |
| `dev/scripts/devctl/commands/governance/session_resume_support.py` | tooling | +21/-8 |
| `dev/scripts/devctl/commands/governance/session_reviewer_loop.py` | tooling | +104/-38 |
| `dev/scripts/devctl/context_graph/escalation.py` | tooling | +31/-1 |
| `dev/scripts/devctl/review_channel/event_projection_context.py` | tooling | +105/-20 |
| `dev/scripts/devctl/review_channel/launch_authority.py` | tooling | +13/-0 |
| `dev/scripts/devctl/review_channel/participant_liveness_signal.py` | tooling | +87/-0 |
| `dev/scripts/devctl/review_channel/status_projection_helpers.py` | tooling | +4/-0 |
| `dev/scripts/devctl/review_channel/status_projection_liveness.py` | tooling | +30/-0 |
| `dev/scripts/devctl/tests/review_channel/test_context_injection.py` | tooling | +90/-36 |

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

### Suggested verification commands

- `python3 dev/scripts/devctl.py check --profile ci`
- `python3 dev/scripts/devctl.py probe-report --format md`
- `python3 dev/scripts/devctl.py docs-check --strict-tooling`
- `python3 dev/scripts/devctl.py check-router --format md`

## 7. Reasoning — why these changes landed

### Per-commit rationale

- **`c09fb18c`** — Cache graph at escalation level — fixes ALL blocking paths (3.4s from 20s)
  - build_context_escalation_packet now tries cached snapshot before full
  - AST rebuild. This fixes status, inbox, promotion, and every other path
  - that queries the context graph — not just session-resume.
- **`ca4439d8`** — Refresh external review snapshot for 38a05ad3
- **`38a05ad3`** — Fix rev_pkt_0819: emit liveness on real status path + HEAD bypass
  - rev_pkt_0819: Added participant_liveness emission to the helpers
  - compatibility wrapper (the real call path) not just the liveness module.
- **`058d5259`** — Refresh external review snapshot for afbcc99f
- **`afbcc99f`** — Fix reviewer loop death: HEAD change no longer kills session in remote_control
  - launch_authority.py:124 now returns refresh_recommended instead of stale
  - when DEVCTL_OPERATOR_INTERACTION_MODE=remote_control. In reviewer-loop
  - mode, HEAD advancement is expected (implementer commits while reviewer
- **`b6da49eb`** — Refresh external review snapshot for bc266a94
- **`bc266a94`** — Wire ParticipantLivenessSignal into status projection (T08)
  - attach_conductor_session_state now emits participant_liveness list
  - with typed signals for each provider (codex/claude). Surfaces can
  - read bridge_liveness["participant_liveness"] for canonical
- **`81a50662`** — Refresh external review snapshot for 7f703e6d
- **`7f703e6d`** — Fix snapshot sort: use timestamp portion of filename (Codex rev_pkt_0815)
- **`a0b6047a`** — Refresh external review snapshot for 28d5d120
- **`28d5d120`** — Fix graph cache: load single latest snapshot, not all 362 files
- **`d918792c`** — Refresh external review snapshot for 07262419
- **`07262419` | MPs: MP-377** — Add ParticipantLivenessSignal typed model (MP377-P1-T08)
  - New canonical liveness signal family: alive/degraded/detached_runtime_only/dead.
  - classify_participant_liveness() classifies one agent based on conductor,
  - publisher, supervisor state + poll age. All surfaces should consume
  - plan: `dev/active/ai_governance_platform.md`
- **`d62361a0`** — Refresh external review snapshot for d2539063
- **`d2539063`** — Fix rev_pkt_0810: only override open_findings when backlog has history
- **`713cb440`** — Refresh external review snapshot for 3f698e22
- **`3f698e22`** — Fix rev_pkt_0809: empty backlog always overrides stale bridge count
- **`403c547e`** — Refresh external review snapshot for cbcb36bb
- **`cbcb36bb`** — Fix Codex findings 0806/0807 + hybrid loop rewrite
  - rev_pkt_0806: session-resume backlog override now handles zero-open case
  - rev_pkt_0807: test patches list_context_graph_snapshots at module level
  - Hybrid reviewer loop: ensure tick + direct Codex launch when work pending
- **`d69ff4e1`** — Refresh external review snapshot for 46679665
- **`46679665`** — Hybrid reviewer loop: ensure heartbeats + direct Codex relaunch
  - Rewrites session_reviewer_loop.py as a hybrid that:
  - 1. Runs ensure --follow tick for heartbeats/supervisor state (bounded)
  - 2. Checks for pending packets + dirty worktree
- **`7ac8911c`** — Wire FindingBacklog into session-resume + cached graph rehydration test
  - Session-resume now prefers canonical FindingBacklog count over
  - bridge-derived open_findings, matching the dashboard wiring.
  - Falls back on load errors.
- **`107bd54a`** — Fix stale snapshot selection: use canonical resolver (Codex rev_pkt_0803)
  - _load_cached_graph now uses list_context_graph_snapshots() which sorts
  - by generated_at_utc instead of raw stat().st_mtime. This prevents
  - selecting a stale snapshot when file modification time disagrees with
- **`7d2a3897`** — Refresh external review snapshot for 84d06a2d
- **`84d06a2d`** — Use cached context graph in session-resume — fixes infinite hang
  - build_event_context_packet now loads the latest cached graph snapshot
  - instead of triggering a full AST scan of ~191K LOC Python. Falls back
  - to full rebuild only when no cached snapshot exists.
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
- repair_reviewer_loop: review_loop_relaunch_required

### Stale warnings
- Cut a checkpoint before doing anything else.

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

Projection produced by `devctl review-snapshot`. Generation stamp `snap-feee7581d4cc` binds this file to HEAD `c09fb18c2be4`; if they drift, the freshness guard will fail CI. When the latest commit only refreshes this generated snapshot, the guard accepts this file as bound to that commit's parent code state.
