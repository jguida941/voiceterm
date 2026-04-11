# VoiceTerm — Review Snapshot

> Deterministically generated from typed governance state. Do not edit by hand — rerun `devctl review-snapshot --write`.

## Quick status

- Branch: `feature/governance-quality-sweep`
- HEAD: `a3e3347c1ea5` — docs(audit): dashboard-loop tick 1-32 + typed findings 0200-0237
- Tree hash: `e6c6769cd2a3`
- Generation stamp: `snap-bfeb63a2b2f0`
- Generated at (UTC): 2026-04-11T23:10:29Z
- Push decision: `await_checkpoint` — staged_index_budget_exceeded
- Reviewer mode: `single_agent` (interaction: `local_terminal`)
- Pipeline state: `n/a` (approval: `n/a`)
- Delta since last snapshot: 24 commits, 59 files, +6998/-1988
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
- HEAD SHA: `a3e3347c1ea58c6eab1e0197e15b54bbc0b7fa2e`
- HEAD author: Justin Guida
- HEAD timestamp (UTC): 2026-04-11T19:08:23-04:00

## 2. Governance state

### Push decision
- action: `await_checkpoint`
- reason: staged_index_budget_exceeded
- push_eligible_now: False
- worktree_clean: False
- staged_path_count: 77
- unstaged_path_count: 0
- next_step_command: `n/a`
- latest_push_report: `dev/reports/push/latest.json`
- latest_push_report_state: `published_remote` (post_push_bundle_pending)
- current_push_authorization: `push-auth-20260411T184445146140Z` (valid=False)
- authorized_head_commit: `0936a4e543f5a3c38d0e8a9348718bd50c533a05`
- approved_target_identity: `tree-receipt-20260411T184445146140Z:b5ba49bb30bbdc75b5f28bba1c287afcec975a34`
- publication_backlog: queued
- publication_guidance: 1 local commit(s) waiting for governed push once the current slice is checkpoint-clean.

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

Range: last 24 commits ending at `a3e3347c1ea5`

- commits: 24
- files changed: 59
- insertions: +6998
- deletions: -1988
- bundle classes touched: docs, tooling
- risk add-ons triggered: Parser / ANSI boundary
- authority surfaces touched: 6 file(s)

### Commits

| # | SHA | Subject | Files | +/- | Bundle | Risk |
|---|---|---|---|---|---|---|
| 1 | `a3e3347c` | docs(audit): dashboard-loop tick 1-32 + typed findings 0200… | 3 | +2200/-99 | tooling |  |
| 2 | `0936a4e5` | Refresh external review snapshot for 2e46f645 | 1 | +67/-66 | tooling |  |
| 3 | `2e46f645` | fix(runtime): keep local single-agent takeover local | 18 | +425/-113 | tooling |  |
| 4 | `47e2b4e1` | Clarify platform boundary and startup mutability routing | 17 | +358/-46 | tooling |  |
| 5 | `30dcf434` | Refresh external review snapshot for 8a05ad7f | 1 | +55/-52 | tooling |  |
| 6 | `8a05ad7f` | docs(bridge): scribe capture live Codex state + autonomy pl… | 3 | +72/-65 | tooling |  |
| 7 | `936cbc3d` | fix(review-snapshot): gate single_agent lane on reviewer ve… | 3 | +120/-62 | tooling |  |
| 8 | `e1dac616` | Refresh external review snapshot for f3bbca18 | 1 | +63/-70 | tooling |  |
| 9 | `f3bbca18` | fix(review-channel): typed preflight gate — reviewer-checkp… | 8 | +539/-135 | tooling | Parser / ANSI boundary |
| 10 | `8bb338bc` | feat(runtime): Q99 — canonical startup_blocker_decision ker… | 8 | +495/-100 | tooling |  |
| 11 | `2a1977cb` | fix(runtime,governance): Codex P1 — pacing live-rebuild + a… | 6 | +615/-141 | tooling |  |
| 12 | `b0885088` | Refresh external review snapshot for 2730689c | 1 | +104/-80 | tooling |  |
| 13 | `2730689c` | docs(bridge): neutralize stale Q37 Operator Direction block | 2 | +91/-126 | docs |  |
| 14 | `31be10ee` | Refresh external review snapshot for ee79f9c3 | 1 | +108/-72 | tooling |  |
| 15 | `ee79f9c3` | fix(review-snapshot): Q92-C7 — consult live reviewer verdic… | 3 | +325/-100 | tooling |  |
| 16 | `eb4a15b6` | Refresh external review snapshot for 38cb9e95 | 1 | +120/-100 | tooling |  |
| 17 | `38cb9e95` | fix(review-channel): Q94 — emit participant_liveness_expire… | 6 | +437/-111 | tooling |  |
| 18 | `63bd97e1` | Refresh external review snapshot for 7f2f925f | 1 | +111/-93 | tooling |  |
| 19 | `7f2f925f` | docs(claude): force typed ingestion — --format json over --… | 5 | +69/-96 | tooling |  |
| 20 | `09565fe7` | Refresh external review snapshot for 4a67140e | 1 | +42/-40 | tooling |  |
| 21 | `4a67140e` | docs(bridge): scribe capture Codex fdd35a6207cc verdict (Q9… | 2 | +46/-47 | docs |  |
| 22 | `3c294f0d` | Refresh external review snapshot for 0247df7c | 1 | +41/-42 | tooling |  |
| 23 | `0247df7c` | docs(bridge): scribe capture for Q98-Q99 post (Q91b workaro… | 2 | +64/-61 | docs |  |
| 24 | `84006af1` | docs(audit): Q98-Q99 — ChatGPT proposal audit + 5-field pro… | 2 | +431/-71 | tooling |  |

### Files

| Path | Bundle | +/- |
|---|---|---|
| `AGENTS.md` | docs | +16/-1 |
| `bridge.md` | docs | +221/-125 |
| `dev/active/MASTER_PLAN.md` | tooling | +16/-0 |
| `dev/active/ai_governance_platform.md` | tooling | +21/-1 |
| `dev/active/autonomous_control_plane.md` | tooling | +2/-0 |
| `dev/audits/LIVE_RUN.md` | tooling | +2367/-0 |
| `dev/audits/REVIEW_SNAPSHOT.md` | tooling | +1672/-1669 |
| `dev/config/devctl_repo_policy.json` | tooling | +1/-1 |
| `dev/config/templates/claude_instructions.template.md` | tooling | +7/-5 |
| `dev/config/templates/portable_governance_repo_setup.template.md` | tooling | +5/-3 |
| `dev/guides/DEVELOPMENT.md` | docs | +15/-0 |
| `dev/history/ENGINEERING_EVOLUTION.md` | tooling | +53/-1 |
| `dev/scripts/README.md` | tooling | +16/-5 |
| `dev/scripts/devctl/commands/dashboard.py` | tooling | +8/-2 |
| `dev/scripts/devctl/commands/dashboard_builders.py` | tooling | +27/-22 |
| `dev/scripts/devctl/commands/governance/startup_context.py` | tooling | +23/-0 |
| `dev/scripts/devctl/commands/governance/startup_context_advisory_coherence.py` | tooling | +132/-0 |
| `dev/scripts/devctl/commands/review_channel/_reviewer.py` | tooling | +9/-0 |
| `dev/scripts/devctl/governance/bootstrap_guide.py` | tooling | +5/-2 |
| `dev/scripts/devctl/governance/surface_context.py` | tooling | +1/-1 |
| `dev/scripts/devctl/governance/system_catalog_bootstrap.py` | tooling | +2/-2 |
| `dev/scripts/devctl/platform/coordination_snapshot_support.py` | tooling | +17/-4 |
| `dev/scripts/devctl/review_channel/collaboration_session_status.py` | tooling | +46/-8 |
| `dev/scripts/devctl/review_channel/event_reducer.py` | tooling | +18/-0 |
| `dev/scripts/devctl/review_channel/parser_bridge_controls.py` | tooling | +11/-0 |
| `dev/scripts/devctl/review_channel/reviewer_state.py` | tooling | +18/-3 |
| `dev/scripts/devctl/review_channel/reviewer_state_support.py` | tooling | +9/-0 |
| `dev/scripts/devctl/review_channel/session_liveness_events.py` | tooling | +130/-0 |
| `dev/scripts/devctl/review_channel/state.py` | tooling | +1/-0 |
| `dev/scripts/devctl/review_channel/status_projection_helpers.py` | tooling | +26/-0 |
| `dev/scripts/devctl/review_channel/write_preconditions.py` | tooling | +84/-0 |
| `dev/scripts/devctl/runtime/action_routing.py` | tooling | +39/-13 |
| `dev/scripts/devctl/runtime/commit_permission.py` | tooling | +1/-1 |
| `dev/scripts/devctl/runtime/control_plane_resolve.py` | tooling | +33/-35 |
| `dev/scripts/devctl/runtime/control_topology.py` | tooling | +59/-1 |
| `dev/scripts/devctl/runtime/implementation_admissibility.py` | tooling | +66/-0 |
| `dev/scripts/devctl/runtime/monitor_snapshot.py` | tooling | +18/-6 |
| `dev/scripts/devctl/runtime/review_snapshot_state.py` | tooling | +109/-15 |
| `dev/scripts/devctl/runtime/startup_blocker_decision.py` | tooling | +212/-0 |
| `dev/scripts/devctl/runtime/startup_context.py` | tooling | +47/-33 |
| _19 more files trimmed_ | | |

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
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/review_snapshot_state.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/runtime/test_review_snapshot.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/governance/startup_context.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/commands/governance/test_startup_context.py`) — Review contract-level invariants for this file

### Suggested verification commands

- `python3 dev/scripts/devctl.py check --profile ci`
- `python3 dev/scripts/devctl.py probe-report --format md`
- `python3 dev/scripts/devctl.py docs-check --strict-tooling`
- `python3 dev/scripts/devctl.py governance-review --format md`
- `python3 dev/scripts/devctl.py check-router --format md`

## 7. Reasoning — why these changes landed

### Per-commit rationale

- **`a3e3347c`** — docs(audit): dashboard-loop tick 1-32 + typed findings 0200-0237
  - Durable audit trail from this remote-dashboard session covering:
  - - 32 dashboard-loop ticks with verbatim typed state, parity matrix,
  -   agent-mind cursor polls, and target-file mtime deltas
  - evolution: Fact: the sanctioned local reviewer-takeover surface already existed, but the repo still drifted back toward `remote_control` semantics in one important place. The current policy had been left on `remote_control`, and s…
- **`0936a4e5`** — Refresh external review snapshot for 2e46f645
  - evolution: Fact: the sanctioned local reviewer-takeover surface already existed, but the repo still drifted back toward `remote_control` semantics in one important place. The current policy had been left on `remote_control`, and s…
- **`2e46f645`** — fix(runtime): keep local single-agent takeover local
  - evolution: Fact: the sanctioned local reviewer-takeover surface already existed, but the repo still drifted back toward `remote_control` semantics in one important place. The current policy had been left on `remote_control`, and s…
- **`47e2b4e1`** — Clarify platform boundary and startup mutability routing
  - evolution: Fact: the sanctioned local reviewer-takeover surface already existed, but the repo still drifted back toward `remote_control` semantics in one important place. The current policy had been left on `remote_control`, and s…
- **`30dcf434`** — Refresh external review snapshot for 8a05ad7f
  - evolution: Fact: the sanctioned local reviewer-takeover surface already existed, but the repo still drifted back toward `remote_control` semantics in one important place. The current policy had been left on `remote_control`, and s…
- **`8a05ad7f`** — docs(bridge): scribe capture live Codex state + autonomy plan drift (pre-push Q91b workaround)
  - evolution: Fact: the sanctioned local reviewer-takeover surface already existed, but the repo still drifted back toward `remote_control` semantics in one important place. The current policy had been left on `remote_control`, and s…
- **`936cbc3d`** — fix(review-snapshot): gate single_agent lane on reviewer verdict, not mode alone
  - Codex verdict at instruction_revision 214e376fabc0 flagged that
  - review_snapshot_state.py:107-137 only downgraded push_eligible_now and
  - the governed push next_step_command when effective_reviewer_mode ==
  - evolution: Fact: the sanctioned local reviewer-takeover surface already existed, but the repo still drifted back toward `remote_control` semantics in one important place. The current policy had been left on `remote_control`, and s…
- **`e1dac616`** — Refresh external review snapshot for f3bbca18
  - evolution: Fact: the sanctioned local reviewer-takeover surface already existed, but the repo still drifted back toward `remote_control` semantics in one important place. The current policy had been left on `remote_control`, and s…
- **`f3bbca18`** — fix(review-channel): typed preflight gate — reviewer-checkpoint refuses while inbox has unread packets
  - Root cause: across 4 Codex review sessions in a single dashboard session,
  - Codex never ran `review-channel --action inbox --target codex --status
  - pending` before writing a reviewer-checkpoint verdict. Two typed finding
  - evolution: Fact: the sanctioned local reviewer-takeover surface already existed, but the repo still drifted back toward `remote_control` semantics in one important place. The current policy had been left on `remote_control`, and s…
- **`8bb338bc`** — feat(runtime): Q99 — canonical startup_blocker_decision kernel (top_blocker/next_action)
  - Create runtime/startup_blocker_decision.py with BlockerSnapshot dataclass
  - and derive_blocker_decision() canonical reducer. Wire into
  - build_startup_context() so top_blocker and next_action are computed once
  - evolution: Fact: the sanctioned local reviewer-takeover surface already existed, but the repo still drifted back toward `remote_control` semantics in one important place. The current policy had been left on `remote_control`, and s…
- **`2a1977cb`** — fix(runtime,governance): Codex P1 — pacing live-rebuild + advisory_action contradiction
  - Finding 1: work_intake_pacing.py:158-176 forced a full context graph
  - live rebuild whenever the saved snapshot's HEAD did not match the
  - current HEAD, making startup-context hang on every fresh commit (repo
  - evolution: Fact: the sanctioned local reviewer-takeover surface already existed, but the repo still drifted back toward `remote_control` semantics in one important place. The current policy had been left on `remote_control`, and s…
- **`b0885088`** — Refresh external review snapshot for 2730689c
  - evolution: Fact: the sanctioned local reviewer-takeover surface already existed, but the repo still drifted back toward `remote_control` semantics in one important place. The current policy had been left on `remote_control`, and s…
- **`2730689c`** — docs(bridge): neutralize stale Q37 Operator Direction block
  - Replaces the stale Q37 Phase 1 operator-direction content (which
  - referenced efcb2cd9, already upstream) with fresh operator guidance
  - pointing at the real active slice: Q98/Q99 integration delta + Codex's
  - evolution: Fact: the sanctioned local reviewer-takeover surface already existed, but the repo still drifted back toward `remote_control` semantics in one important place. The current policy had been left on `remote_control`, and s…
- **`31be10ee`** — Refresh external review snapshot for ee79f9c3
  - evolution: Fact: the sanctioned local reviewer-takeover surface already existed, but the repo still drifted back toward `remote_control` semantics in one important place. The current policy had been left on `remote_control`, and s…
- **`ee79f9c3`** — fix(review-snapshot): Q92-C7 — consult live reviewer verdict before emitting push_eligible_now
  - devctl review-snapshot --write now checks the live ReviewerObservation
  - verdict before emitting push_eligible_now: True or next_step_command=
  - python3 dev/scripts/devctl.py push --execute. When the live verdict is
  - evolution: Fact: the sanctioned local reviewer-takeover surface already existed, but the repo still drifted back toward `remote_control` semantics in one important place. The current policy had been left on `remote_control`, and s…
- **`eb4a15b6`** — Refresh external review snapshot for 38cb9e95
  - evolution: Fact: the sanctioned local reviewer-takeover surface already existed, but the repo still drifted back toward `remote_control` semantics in one important place. The current policy had been left on `remote_control`, and s…
- **`38cb9e95`** — fix(review-channel): Q94 — emit participant_liveness_expired on heartbeat TTL expiry
  - Wire the existing liveness detection (PID probe + _pid_is_alive +
  - SessionLivenessEvidence + detached_exit auto-set) to the existing event
  - reducer so dead participants auto-decrement live_*_total counters.
  - evolution: Fact: the sanctioned local reviewer-takeover surface already existed, but the repo still drifted back toward `remote_control` semantics in one important place. The current policy had been left on `remote_control`, and s…
- **`63bd97e1`** — Refresh external review snapshot for 7f2f925f
  - evolution: Fact: the sanctioned local reviewer-takeover surface already existed, but the repo still drifted back toward `remote_control` semantics in one important place. The current policy had been left on `remote_control`, and s…
- **`7f2f925f`** — docs(claude): force typed ingestion — --format json over --format summary (Q98 one-line fix)
  - CLAUDE.md now instructs the AI consumer to read startup-context via
  - --format json (typed JSON StartupContext dataclass) instead of
  - --format summary (markdown prose). Generator change, not direct
  - evolution: Fact: the sanctioned local reviewer-takeover surface already existed, but the repo still drifted back toward `remote_control` semantics in one important place. The current policy had been left on `remote_control`, and s…
- **`09565fe7`** — Refresh external review snapshot for 4a67140e
  - evolution: Fact: the sanctioned local reviewer-takeover surface already existed, but the repo still drifted back toward `remote_control` semantics in one important place. The current policy had been left on `remote_control`, and s…
- **`4a67140e`** — docs(bridge): scribe capture Codex fdd35a6207cc verdict (Q91b, pre-merge)
  - evolution: Fact: the sanctioned local reviewer-takeover surface already existed, but the repo still drifted back toward `remote_control` semantics in one important place. The current policy had been left on `remote_control`, and s…
- **`3c294f0d`** — Refresh external review snapshot for 0247df7c
  - evolution: Fact: the sanctioned local reviewer-takeover surface already existed, but the repo still drifted back toward `remote_control` semantics in one important place. The current policy had been left on `remote_control`, and s…
- **`0247df7c`** — docs(bridge): scribe capture for Q98-Q99 post (Q91b workaround)
  - evolution: Fact: the sanctioned local reviewer-takeover surface already existed, but the repo still drifted back toward `remote_control` semantics in one important place. The current policy had been left on `remote_control`, and s…
- **`84006af1`** — docs(audit): Q98-Q99 — ChatGPT proposal audit + 5-field producer trace
  - Dashboard append from the 4-audit verification of ChatGPT's DecisionState
  - proposal against the actual codebase, plus a 5-authority-field producer
  - trace per ChatGPT's refined rule ("decision logic in one place").
  - evolution: Fact: the sanctioned local reviewer-takeover surface already existed, but the repo still drifted back toward `remote_control` semantics in one important place. The current policy had been left on `remote_control`, and s…
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
- checkpoint_before_continue: staged_index_budget_exceeded

### Stale warnings
- Keep editing the current slice.
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

Projection produced by `devctl review-snapshot`. Generation stamp `snap-bfeb63a2b2f0` binds this file to HEAD `a3e3347c1ea5`; if they drift, the freshness guard will fail CI. When the latest commit only refreshes this generated snapshot, the guard accepts this file as bound to that commit's parent code state.
