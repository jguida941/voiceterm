# VoiceTerm — Review Snapshot

> Deterministically generated from typed governance state. Do not edit by hand — rerun `devctl review-snapshot --write`.

## Quick status

- Branch: `feature/governance-quality-sweep`
- HEAD: `cbd035fce04e` — Add 12 tests for graph cache freshness validation
- Tree hash: `b68c357a9436`
- Generation stamp: `snap-6b7e3fb9687a`
- Generated at (UTC): 2026-04-17T00:09:44Z
- Push decision: `await_review` — review_loop_relaunch_required
- Reviewer mode: `tools_only` (interaction: `local_terminal`)
- Pipeline state: `n/a` (approval: `n/a`)
- Delta since last snapshot: 25 commits, 13 files, +1126/-733
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
- HEAD SHA: `cbd035fce04e339a7d2a9ad74abd7cb6e447a394`
- HEAD author: Justin Guida
- HEAD timestamp (UTC): 2026-04-16T20:09:20-04:00

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

Range: last 25 commits ending at `cbd035fce04e`

- commits: 25
- files changed: 13
- insertions: +1126
- deletions: -733
- bundle classes touched: tooling, docs

### Commits

| # | SHA | Subject | Files | +/- | Bundle | Risk |
|---|---|---|---|---|---|---|
| 1 | `cbd035fc` | Add 12 tests for graph cache freshness validation | 1 | +100/-0 | tooling |  |
| 2 | `dd16c411` | Refresh external review snapshot for e29f388d | 2 | +55/-62 | docs |  |
| 3 | `e29f388d` | Fix 3 Codex blockers: graph freshness, loop scoping, T08 pr… | 5 | +156/-25 | tooling |  |
| 4 | `9a4238f1` | Refresh external review snapshot for bed137b9 | 2 | +53/-53 | docs |  |
| 5 | `bed137b9` | Fix cache type mismatch: coerce snapshot dicts to GraphNode… | 1 | +32/-4 | tooling |  |
| 6 | `f3a9785d` | Refresh external review snapshot for c09fb18c | 2 | +53/-48 | docs |  |
| 7 | `c09fb18c` | Cache graph at escalation level — fixes ALL blocking paths… | 1 | +31/-1 | tooling |  |
| 8 | `ca4439d8` | Refresh external review snapshot for 38a05ad3 | 2 | +46/-47 | docs |  |
| 9 | `38a05ad3` | Fix rev_pkt_0819: emit liveness on real status path + HEAD… | 1 | +4/-0 | tooling |  |
| 10 | `058d5259` | Refresh external review snapshot for afbcc99f | 2 | +50/-53 | docs |  |
| 11 | `afbcc99f` | Fix reviewer loop death: HEAD change no longer kills sessio… | 1 | +13/-0 | tooling |  |
| 12 | `b6da49eb` | Refresh external review snapshot for bc266a94 | 2 | +55/-44 | docs |  |
| 13 | `bc266a94` | Wire ParticipantLivenessSignal into status projection (T08) | 1 | +30/-0 | tooling |  |
| 14 | `81a50662` | Refresh external review snapshot for 7f703e6d | 2 | +46/-65 | docs |  |
| 15 | `7f703e6d` | Fix snapshot sort: use timestamp portion of filename (Codex… | 1 | +3/-1 | tooling |  |
| 16 | `a0b6047a` | Refresh external review snapshot for 28d5d120 | 2 | +49/-56 | docs |  |
| 17 | `28d5d120` | Fix graph cache: load single latest snapshot, not all 362 f… | 1 | +12/-5 | tooling |  |
| 18 | `d918792c` | Refresh external review snapshot for 07262419 | 2 | +48/-41 | docs |  |
| 19 | `07262419` | Add ParticipantLivenessSignal typed model (MP377-P1-T08) | 1 | +87/-0 | tooling |  |
| 20 | `d62361a0` | Refresh external review snapshot for d2539063 | 2 | +54/-59 | docs |  |
| 21 | `d2539063` | Fix rev_pkt_0810: only override open_findings when backlog… | 1 | +6/-3 | tooling |  |
| 22 | `713cb440` | Refresh external review snapshot for 3f698e22 | 2 | +49/-62 | docs |  |
| 23 | `3f698e22` | Fix rev_pkt_0809: empty backlog always overrides stale brid… | 1 | +3/-3 | tooling |  |
| 24 | `403c547e` | Refresh external review snapshot for cbcb36bb | 2 | +52/-58 | docs |  |
| 25 | `cbcb36bb` | Fix Codex findings 0806/0807 + hybrid loop rewrite | 3 | +39/-43 | tooling |  |

### Files

| Path | Bundle | +/- |
|---|---|---|
| `bridge.md` | docs | +60/-65 |
| `dev/audits/REVIEW_SNAPSHOT.md` | tooling | +550/-583 |
| `dev/scripts/devctl/commands/governance/session_resume_support.py` | tooling | +12/-8 |
| `dev/scripts/devctl/commands/governance/session_reviewer_loop.py` | tooling | +43/-9 |
| `dev/scripts/devctl/context_graph/escalation.py` | tooling | +79/-8 |
| `dev/scripts/devctl/context_graph/snapshot_payload.py` | tooling | +53/-0 |
| `dev/scripts/devctl/review_channel/event_projection_context.py` | tooling | +34/-14 |
| `dev/scripts/devctl/review_channel/launch_authority.py` | tooling | +13/-0 |
| `dev/scripts/devctl/review_channel/participant_liveness_signal.py` | tooling | +87/-0 |
| `dev/scripts/devctl/review_channel/status_projection_helpers.py` | tooling | +4/-0 |
| `dev/scripts/devctl/review_channel/status_projection_liveness.py` | tooling | +59/-10 |
| `dev/scripts/devctl/tests/context_graph/test_snapshot_cache_freshness.py` | tooling | +100/-0 |
| `dev/scripts/devctl/tests/review_channel/test_context_injection.py` | tooling | +32/-36 |

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

- **`cbd035fc`** — Add 12 tests for graph cache freshness validation
- **`dd16c411`** — Refresh external review snapshot for e29f388d
- **`e29f388d`** — Fix 3 Codex blockers: graph freshness, loop scoping, T08 providers
  - 1. Graph cache freshness (rev_pkt_0832 #1):
  -    - escalation.py + event_projection_context.py: validate snapshot HEAD
  -      against current HEAD, reject stale snapshots
- **`9a4238f1`** — Refresh external review snapshot for bed137b9
- **`bed137b9`** — Fix cache type mismatch: coerce snapshot dicts to GraphNode/GraphEdge (rev_pkt_0830)
  - Cached graph snapshots contain raw dicts but query.py expects typed
  - GraphNode objects with .label attribute. Now coerces each row to the
  - typed dataclass. Status command: crash → 14.1s success.
- **`f3a9785d`** — Refresh external review snapshot for c09fb18c
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

Projection produced by `devctl review-snapshot`. Generation stamp `snap-6b7e3fb9687a` binds this file to HEAD `cbd035fce04e`; if they drift, the freshness guard will fail CI. When the latest commit only refreshes this generated snapshot, the guard accepts this file as bound to that commit's parent code state.
