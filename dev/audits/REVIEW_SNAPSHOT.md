# VoiceTerm — Review Snapshot

> Deterministically generated from typed governance state. Do not edit by hand — rerun `devctl review-snapshot --write`.

## Quick status

- Branch: `feature/governance-quality-sweep`
- HEAD: `061a1261dadc` — review_channel: packet_control_loop priority selection + control hints
- Tree hash: `8cf812efa87a`
- Generation stamp: `snap-d76020f07d6c`
- Generated at (UTC): 2026-04-11T23:20:55Z
- Push decision: `run_devctl_push` — push_preconditions_satisfied
- Reviewer mode: `single_agent` (interaction: `local_terminal`)
- Pipeline state: `n/a` (approval: `n/a`)
- Delta since last snapshot: 24 commits, 122 files, +10737/-2277
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
- HEAD SHA: `061a1261dadccdd882b3f22e9001accc232021bc`
- HEAD author: Justin Guida
- HEAD timestamp (UTC): 2026-04-11T19:19:59-04:00

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
- latest_push_report_state: `blocked` (validation_failed)
- current_push_authorization: `push-auth-20260411T184445146140Z` (valid=False)
- authorized_head_commit: `0936a4e543f5a3c38d0e8a9348718bd50c533a05`
- approved_target_identity: `tree-receipt-20260411T184445146140Z:b5ba49bb30bbdc75b5f28bba1c287afcec975a34`
- publication_backlog: recommended
- publication_guidance: 4 local commit(s) waiting for governed push. Run `python3 dev/scripts/devctl.py push --execute` now.

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
- advisory: `push_allowed` — worktree_clean_and_review_accepted

## 3. Delta — what changed since the previous snapshot

Range: last 24 commits ending at `061a1261dadc`

- commits: 24
- files changed: 122
- insertions: +10737
- deletions: -2277
- bundle classes touched: tooling, docs
- risk add-ons triggered: Parser / ANSI boundary
- authority surfaces touched: 19 file(s)

### Commits

| # | SHA | Subject | Files | +/- | Bundle | Risk |
|---|---|---|---|---|---|---|
| 1 | `061a1261` | review_channel: packet_control_loop priority selection + co… | 5 | +350/-62 | tooling |  |
| 2 | `2cd74a7c` | Refresh external review snapshot for 6db71aca | 1 | +107/-85 | tooling |  |
| 3 | `6db71aca` | review_channel: typed participant authoritative + action_re… | 78 | +3818/-316 | tooling |  |
| 4 | `a3e3347c` | docs(audit): dashboard-loop tick 1-32 + typed findings 0200… | 3 | +2200/-99 | tooling |  |
| 5 | `0936a4e5` | Refresh external review snapshot for 2e46f645 | 1 | +67/-66 | tooling |  |
| 6 | `2e46f645` | fix(runtime): keep local single-agent takeover local | 18 | +425/-113 | tooling |  |
| 7 | `47e2b4e1` | Clarify platform boundary and startup mutability routing | 17 | +358/-46 | tooling |  |
| 8 | `30dcf434` | Refresh external review snapshot for 8a05ad7f | 1 | +55/-52 | tooling |  |
| 9 | `8a05ad7f` | docs(bridge): scribe capture live Codex state + autonomy pl… | 3 | +72/-65 | tooling |  |
| 10 | `936cbc3d` | fix(review-snapshot): gate single_agent lane on reviewer ve… | 3 | +120/-62 | tooling |  |
| 11 | `e1dac616` | Refresh external review snapshot for f3bbca18 | 1 | +63/-70 | tooling |  |
| 12 | `f3bbca18` | fix(review-channel): typed preflight gate — reviewer-checkp… | 8 | +539/-135 | tooling | Parser / ANSI boundary |
| 13 | `8bb338bc` | feat(runtime): Q99 — canonical startup_blocker_decision ker… | 8 | +495/-100 | tooling |  |
| 14 | `2a1977cb` | fix(runtime,governance): Codex P1 — pacing live-rebuild + a… | 6 | +615/-141 | tooling |  |
| 15 | `b0885088` | Refresh external review snapshot for 2730689c | 1 | +104/-80 | tooling |  |
| 16 | `2730689c` | docs(bridge): neutralize stale Q37 Operator Direction block | 2 | +91/-126 | docs |  |
| 17 | `31be10ee` | Refresh external review snapshot for ee79f9c3 | 1 | +108/-72 | tooling |  |
| 18 | `ee79f9c3` | fix(review-snapshot): Q92-C7 — consult live reviewer verdic… | 3 | +325/-100 | tooling |  |
| 19 | `eb4a15b6` | Refresh external review snapshot for 38cb9e95 | 1 | +120/-100 | tooling |  |
| 20 | `38cb9e95` | fix(review-channel): Q94 — emit participant_liveness_expire… | 6 | +437/-111 | tooling |  |
| 21 | `63bd97e1` | Refresh external review snapshot for 7f2f925f | 1 | +111/-93 | tooling |  |
| 22 | `7f2f925f` | docs(claude): force typed ingestion — --format json over --… | 5 | +69/-96 | tooling |  |
| 23 | `09565fe7` | Refresh external review snapshot for 4a67140e | 1 | +42/-40 | tooling |  |
| 24 | `4a67140e` | docs(bridge): scribe capture Codex fdd35a6207cc verdict (Q9… | 2 | +46/-47 | docs |  |

### Files

| Path | Bundle | +/- |
|---|---|---|
| `AGENTS.md` | docs | +24/-6 |
| `bridge.md` | docs | +209/-114 |
| `dev/active/MASTER_PLAN.md` | tooling | +82/-0 |
| `dev/active/ai_governance_platform.md` | tooling | +37/-1 |
| `dev/active/autonomous_control_plane.md` | tooling | +2/-0 |
| `dev/active/remote_commit_pipeline.md` | tooling | +28/-0 |
| `dev/active/remote_control_runtime.md` | tooling | +71/-0 |
| `dev/audits/LIVE_RUN.md` | tooling | +1997/-0 |
| `dev/audits/REVIEW_SNAPSHOT.md` | tooling | +1732/-1706 |
| `dev/config/devctl_repo_policy.json` | tooling | +1/-1 |
| `dev/config/git_hooks/pre-push-governed-push.sh` | tooling | +1/-1 |
| `dev/config/templates/claude_instructions.template.md` | tooling | +7/-5 |
| `dev/config/templates/portable_governance_repo_setup.template.md` | tooling | +5/-3 |
| `dev/guides/DEVELOPMENT.md` | docs | +20/-3 |
| `dev/history/ENGINEERING_EVOLUTION.md` | tooling | +78/-1 |
| `dev/scripts/README.md` | tooling | +37/-9 |
| `dev/scripts/checks/platform_contract_closure/emitter_parity.py` | tooling | +5/-0 |
| `dev/scripts/devctl/commands/agent_mind/slice_builder.py` | tooling | +58/-0 |
| `dev/scripts/devctl/commands/dashboard.py` | tooling | +18/-2 |
| `dev/scripts/devctl/commands/dashboard_builders.py` | tooling | +27/-22 |
| `dev/scripts/devctl/commands/dashboard_typed_state.py` | tooling | +12/-1 |
| `dev/scripts/devctl/commands/governance/startup_context.py` | tooling | +23/-0 |
| `dev/scripts/devctl/commands/governance/startup_context_advisory_coherence.py` | tooling | +132/-0 |
| `dev/scripts/devctl/commands/governance/startup_context_render.py` | tooling | +11/-5 |
| `dev/scripts/devctl/commands/review_channel/_render_bridge.py` | tooling | +7/-0 |
| `dev/scripts/devctl/commands/review_channel/_reviewer.py` | tooling | +16/-0 |
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
| _82 more files trimmed_ | | |

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
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/governance/startup_context.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/commands/governance/test_startup_context.py`) — Review contract-level invariants for this file
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

- **`061a1261`** — review_channel: packet_control_loop priority selection + control hints
  - Adds packet_control_loop.py with select_priority_pending_packet(), which
  - picks the highest-priority live pending packet (action_request class first,
  - then findings/questions/instructions) and returns control-state metadata
  - evolution: Fact: the sanctioned local reviewer-takeover surface already existed, but the repo still drifted back toward `remote_control` semantics in one important place. The current policy had been left on `remote_control`, and s…
- **`2cd74a7c`** — Refresh external review snapshot for 6db71aca
  - evolution: Fact: the sanctioned local reviewer-takeover surface already existed, but the repo still drifted back toward `remote_control` semantics in one important place. The current policy had been left on `remote_control`, and s…
- **`6db71aca` | MPs: MP-355** — review_channel: typed participant authoritative + action_request delivery primitive + dashboard/control-plane parity
  - Closes six of the eight scaffolding layers named in the architectural meta-
  - finding this session. Introduces the action_request_delivery primitive that
  - stamps delivery_emitted_at_utc / delivery_observed_at_utc / delivery_observed_by
  - plan: `dev/active/review_channel.md`
  - evolution: Fact: the sanctioned local reviewer-takeover surface already existed, but the repo still drifted back toward `remote_control` semantics in one important place. The current policy had been left on `remote_control`, and s…
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

Projection produced by `devctl review-snapshot`. Generation stamp `snap-d76020f07d6c` binds this file to HEAD `061a1261dadc`; if they drift, the freshness guard will fail CI. When the latest commit only refreshes this generated snapshot, the guard accepts this file as bound to that commit's parent code state.
