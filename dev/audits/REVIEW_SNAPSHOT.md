# VoiceTerm — Review Snapshot

> Deterministically generated from typed governance state. Do not edit by hand — rerun `devctl review-snapshot --write`.

## Quick status

- Branch: `feature/governance-quality-sweep`
- HEAD: `516e839c78de` — Refresh external review snapshot for c1a1ee28
- Tree hash: `cccb5bc5506c`
- Generation stamp: `snap-70f4e6fd3f20`
- Generated at (UTC): 2026-04-09T07:05:50Z
- Push decision: `await_checkpoint` — dirty_path_budget_exceeded
- Reviewer mode: `tools_only` (interaction: `unresolved`)
- Pipeline state: `n/a` (approval: `n/a`)
- Delta since last snapshot: 25 commits, 69 files, +7020/-2328
- Governance findings: 39 open / 68 fixed / 121 total
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
- HEAD SHA: `516e839c78de76d67c66d1975eed11c88819e4da`
- HEAD author: Justin Guida
- HEAD timestamp (UTC): 2026-04-09T00:00:37-04:00

## 2. Governance state

### Push decision
- action: `await_checkpoint`
- reason: dirty_path_budget_exceeded
- push_eligible_now: False
- worktree_clean: False
- next_step_command: `n/a`
- latest_push_report: `dev/reports/push/latest.json`
- latest_push_report_state: `blocked` (validation_failed)
- publication_backlog: none

### Reviewer runtime
- reviewer_mode: `tools_only`
- reviewer_freshness: unknown
- reviewer_publish_clear: False
- interaction_mode: `unresolved`
- implementation_blocked: yes — reviewer_overdue

### Remote commit pipeline
- state: `n/a`
- approval_state: `n/a`

### Work intake
- active plan: **Master Plan (Active, Unified)**
- plan path: `dev/active/MASTER_PLAN.md`
- active MP scope: all active MP execution state
- advisory: `checkpoint_before_continue` — dirty_path_budget_exceeded
- checkpoint_required: **yes**

## 3. Delta — what changed since the previous snapshot

Range: last 25 commits ending at `516e839c78de`

- commits: 25
- files changed: 69
- insertions: +7020
- deletions: -2328
- bundle classes touched: tooling, docs
- authority surfaces touched: 9 file(s)

### Commits

| # | SHA | Subject | Files | +/- | Bundle | Risk |
|---|---|---|---|---|---|---|
| 1 | `516e839c` | Refresh external review snapshot for c1a1ee28 | 1 | +96/-69 | tooling |  |
| 2 | `c1a1ee28` | Advance typed authority convergence across mutation and con… | 59 | +3285/-956 | tooling |  |
| 3 | `1c74c07f` | Refresh external review snapshot for f294de63 | 1 | +68/-59 | tooling |  |
| 4 | `f294de63` | Operator-directed commit+push: F1 parity flake fix + bridge… | 5 | +116/-41 | tooling |  |
| 5 | `ed23ac62` | LIVE_RUN: Q61 typed state lies about PID liveness + Q62 err… | 2 | +147/-54 | tooling |  |
| 6 | `839ee400` | Refresh external review snapshot for 9109ae4e | 1 | +57/-53 | tooling |  |
| 7 | `9109ae4e` | Preserve Claude-CLI session 7 WIP before solo-Codex test | 4 | +179/-69 | tooling |  |
| 8 | `8330b1d9` | LIVE_RUN: Q58 autonomy-swarm discoverability + full system… | 2 | +254/-42 | tooling |  |
| 9 | `06d591c0` | LIVE_RUN: Q55 THE DISEASE (authority-lane split) + Q56 smok… | 2 | +281/-51 | tooling |  |
| 10 | `c6743678` | Refresh external review snapshot for ffc7f954 | 1 | +58/-50 | tooling |  |
| 11 | `ffc7f954` | Preserve Claude-CLI session 6 WIP batch 2 (plan docs + new… | 8 | +325/-56 | tooling |  |
| 12 | `7ac4d4f1` | Preserve Claude-CLI session 6 WIP (F1 + F4 + test + README)… | 6 | +220/-82 | tooling |  |
| 13 | `527eb1b2` | LIVE_RUN: Q54 role separation unclear — publisher vs superv… | 2 | +166/-40 | tooling |  |
| 14 | `22b06b22` | LIVE_RUN: Q53 bootstrap guidance missing — AI agents learn… | 2 | +182/-63 | tooling |  |
| 15 | `c5890296` | LIVE_RUN: Q52 TOP-LEVEL ARCHITECTURAL FAILURE — AI agents f… | 2 | +170/-42 | tooling |  |
| 16 | `e9a37347` | LIVE_RUN: Q50 lazy dashboard + Q51 update cadence drift (AI… | 2 | +200/-53 | tooling |  |
| 17 | `81cff0d8` | Refresh external review snapshot for 079d7f3f | 1 | +55/-50 | tooling |  |
| 18 | `079d7f3f` | Preserve Claude-CLI WIP (F1 consumer wiring) from session 5… | 4 | +155/-155 | tooling |  |
| 19 | `dde77865` | LIVE_RUN: add AI Research Lane architecture proposal (Codex… | 2 | +217/-49 | tooling |  |
| 20 | `9515a083` | LIVE_RUN: Q45/Q46/Q47 from typed-state discoverability audit | 2 | +147/-45 | tooling |  |
| 21 | `5f5c049f` | LIVE_RUN: Q43 publisher lifecycle drift + Q44 publisher rea… | 2 | +150/-55 | tooling |  |
| 22 | `a65da5bf` | Refresh external review snapshot for e596901 | 1 | +55/-54 | tooling |  |
| 23 | `e5969014` | Preserve Claude-CLI WIP (F1 extension) from second session… | 3 | +230/-46 | tooling |  |
| 24 | `4522b125` | Fix Q41: exclude registered conductor shells from orphan/st… | 2 | +98/-45 | tooling |  |
| 25 | `b7674a38` | LIVE_RUN: Q41 ROOT CAUSE — process-sweep-post reaps live co… | 2 | +109/-49 | tooling |  |

### Files

| Path | Bundle | +/- |
|---|---|---|
| `AGENTS.md` | docs | +13/-0 |
| `bridge.md` | docs | +89/-97 |
| `dev/active/MASTER_PLAN.md` | tooling | +52/-0 |
| `dev/active/ai_governance_platform.md` | tooling | +59/-0 |
| `dev/active/platform_authority_loop.md` | tooling | +70/-0 |
| `dev/active/portable_code_governance.md` | tooling | +24/-1 |
| `dev/active/remote_commit_pipeline.md` | tooling | +79/-17 |
| `dev/active/remote_control_runtime.md` | tooling | +105/-1 |
| `dev/audits/AUTOMATION_DEBT_REGISTER.md` | tooling | +1/-0 |
| `dev/audits/LIVE_RUN.md` | tooling | +1495/-0 |
| `dev/audits/REVIEW_SNAPSHOT.md` | tooling | +1294/-1249 |
| `dev/guides/DEVELOPMENT.md` | docs | +18/-1 |
| `dev/history/ENGINEERING_EVOLUTION.md` | tooling | +84/-0 |
| `dev/scripts/README.md` | tooling | +19/-0 |
| `dev/scripts/devctl/commands/dashboard.py` | tooling | +46/-46 |
| `dev/scripts/devctl/commands/dashboard_builders.py` | tooling | +56/-153 |
| `dev/scripts/devctl/commands/dashboard_people.py` | tooling | +113/-0 |
| `dev/scripts/devctl/commands/dashboard_typed_state.py` | tooling | +5/-7 |
| `dev/scripts/devctl/commands/governance/session_resume.py` | tooling | +9/-1 |
| `dev/scripts/devctl/commands/governance/session_resume_support.py` | tooling | +70/-52 |
| `dev/scripts/devctl/commands/mobile_status.py` | tooling | +1/-1 |
| `dev/scripts/devctl/commands/vcs/commit.py` | tooling | +258/-105 |
| `dev/scripts/devctl/commands/vcs/governed_executor_actions.py` | tooling | +209/-28 |
| `dev/scripts/devctl/commands/vcs/governed_executor_packets.py` | tooling | +33/-0 |
| `dev/scripts/devctl/commands/vcs/governed_executor_phases.py` | tooling | +62/-41 |
| `dev/scripts/devctl/commands/vcs/governed_executor_support.py` | tooling | +25/-3 |
| `dev/scripts/devctl/commands/vcs/push.py` | tooling | +62/-51 |
| `dev/scripts/devctl/governance/draft_policy_scan.py` | tooling | +18/-0 |
| `dev/scripts/devctl/platform/coordination_snapshot.py` | tooling | +17/-2 |
| `dev/scripts/devctl/platform/planning_ir_sources.py` | tooling | +6/-1 |
| `dev/scripts/devctl/platform/system_picture.py` | tooling | +11/-2 |
| `dev/scripts/devctl/process_sweep/internals.py` | tooling | +51/-4 |
| `dev/scripts/devctl/repo_packs/review_helpers.py` | tooling | +87/-0 |
| `dev/scripts/devctl/repo_packs/voiceterm.py` | tooling | +5/-0 |
| `dev/scripts/devctl/review_channel/action_request.py` | tooling | +6/-9 |
| `dev/scripts/devctl/review_channel/bridge_projection_state.py` | tooling | +4/-1 |
| `dev/scripts/devctl/review_channel/current_session_render.py` | tooling | +3/-13 |
| `dev/scripts/devctl/review_channel/current_session_support.py` | tooling | +2/-3 |
| `dev/scripts/devctl/review_channel/event_packet_rows.py` | tooling | +21/-20 |
| `dev/scripts/devctl/review_channel/event_projection_queue.py` | tooling | +2/-16 |
| _29 more files trimmed_ | | |

## 4. Quality signals

### Governance review
- total findings: 121
- open: 39
- fixed: 68
- false positives: 0

Recent findings:
- `agent_checkpoint_contract_ignorance` — `dev/scripts/devctl/review_channel/bridge_sanitize.py` (n/a, verdict=`confirmed_issue`)
- `claude_uses_osascript_not_typed_system` — `dev/scripts/devctl/review_channel/state.py` (n/a, verdict=`confirmed_issue`)
- `push_invalidation_head_equality` — `dev/scripts/devctl/review_channel/push_state.py` (n/a, verdict=`confirmed_issue`)
- `reviewer_truth_distributed_no_owner` — `dev/scripts/devctl/review_channel/state.py` (n/a, verdict=`confirmed_issue`)
- `startup_surface_tokens_unpopulated` — `dev/scripts/devctl/runtime/startup_context.py` (n/a, verdict=`confirmed_issue`)
- `terminal_window_id_not_captured` — `dev/scripts/devctl/review_channel/terminal_app.py` (n/a, verdict=`confirmed_issue`)
- `bridge_projection_drops_operator_direction` — `dev/scripts/devctl/review_channel/bridge_projection_state.py` (n/a, verdict=`confirmed_issue`)
- `bridge_still_active_gate_not_projection` — `dev/scripts/devctl/review_channel/state.py` (n/a, verdict=`confirmed_issue`)
- `need_review_channel_doctor_surface` — `dev/scripts/devctl/review_channel/state.py` (n/a, verdict=`confirmed_issue`)
- `reviewer_runtime_contract_needed` — `dev/scripts/devctl/platform/runtime_state_contract_rows.py` (n/a, verdict=`confirmed_issue`)

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
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_actions.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_packets.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_phases.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_support.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/review_channel/bridge_projection_state.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/vcs/test_governed_executor.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/startup_context.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/runtime/test_startup_context.py`) — Review contract-level invariants for this file
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/review_state_models.py`) — Commit c1a1ee28 changed dev/scripts/devctl/runtime/review_state_models.py

### Suggested verification commands

- `python3 dev/scripts/devctl.py check --profile ci`
- `python3 dev/scripts/devctl.py probe-report --format md`
- `python3 dev/scripts/devctl.py docs-check --strict-tooling`
- `python3 dev/scripts/devctl.py governance-review --format md`
- `python3 dev/scripts/devctl.py check-router --format md`

## 7. Reasoning — why these changes landed

### Per-commit rationale

- **`516e839c`** — Refresh external review snapshot for c1a1ee28
  - evolution: Fact: the next typed-authority convergence slice moved the shared live review-state loader off bridge refresh as its default freshness strategy. `load_current_review_state*` now prefers canonical event-backed review sta…
- **`c1a1ee28`** — Advance typed authority convergence across mutation and control-plane
  - evolution: Fact: the next typed-authority convergence slice moved the shared live review-state loader off bridge refresh as its default freshness strategy. `load_current_review_state*` now prefers canonical event-backed review sta…
- **`1c74c07f`** — Refresh external review snapshot for f294de63
  - evolution: The next remote-control/platform hardening slice was not a new architecture layer. It was closure on the typed paths that already existed but still left practical escape hatches. On the write side, `devctl commit` no lo…
- **`f294de63` | markers: F1** — Operator-directed commit+push: F1 parity flake fix + bridge state + 4hr session unblock
  - Claude-CLI (session 9, PID 89248) authored F1 parity flake fix on
  - instruction revision 7f94c6cae1a6 from Codex:
  - - dev/scripts/devctl/runtime/startup_context.py
  - evolution: The next remote-control/platform hardening slice was not a new architecture layer. It was closure on the typed paths that already existed but still left practical escape hatches. On the write side, `devctl commit` no lo…
- **`ed23ac62`** — LIVE_RUN: Q61 typed state lies about PID liveness + Q62 error system too coarse
  - Operator directly caught two compound findings while reviewing the
  - dashboard data:
  - evolution: The next remote-control/platform hardening slice was not a new architecture layer. It was closure on the typed paths that already existed but still left practical escape hatches. On the write side, `devctl commit` no lo…
- **`839ee400`** — Refresh external review snapshot for 9109ae4e
  - evolution: The next remote-control/platform hardening slice was not a new architecture layer. It was closure on the typed paths that already existed but still left practical escape hatches. On the write side, `devctl commit` no lo…
- **`9109ae4e`** — Preserve Claude-CLI session 7 WIP before solo-Codex test
  - Session 7 reached 19 min before Codex (PID 31108) died; Claude-CLI
  - (PID 31148) remained productive in hybrid_claude_only mode, writing
  - the F1 continuation:
  - evolution: The next remote-control/platform hardening slice was not a new architecture layer. It was closure on the typed paths that already existed but still left practical escape hatches. On the write side, `devctl commit` no lo…
- **`8330b1d9`** — LIVE_RUN: Q58 autonomy-swarm discoverability + full system test plan (6 tests)
  - Operator asked 'what is the best way to test all of this system and
  - make sure it is fully connected?' — and mentioned 'saved cards for
  - this.' The saved-cards answer is devctl autonomy-swarm, a
  - evolution: The next remote-control/platform hardening slice was not a new architecture layer. It was closure on the typed paths that already existed but still left practical escape hatches. On the write side, `devctl commit` no lo…
- **`06d591c0`** — LIVE_RUN: Q55 THE DISEASE (authority-lane split) + Q56 smoking gun + Q57 --claude-workers flag bug
  - Operator's external audit (via ChatGPT Pro) diagnosed the root
  - architectural failure this entire session has been circling
  - without naming:
  - evolution: The next remote-control/platform hardening slice was not a new architecture layer. It was closure on the typed paths that already existed but still left practical escape hatches. On the write side, `devctl commit` no lo…
- **`c6743678`** — Refresh external review snapshot for ffc7f954
  - evolution: The next remote-control/platform hardening slice was not a new architecture layer. It was closure on the typed paths that already existed but still left practical escape hatches. On the write side, `devctl commit` no lo…
- **`ffc7f954`** — Preserve Claude-CLI session 6 WIP batch 2 (plan docs + new coordination loader test)
  - Additional Claude-CLI work from session 6 not captured in the first
  - preservation commit (7ac4d4f1). Session 6 was more productive than
  - the git diff --stat view suggested:
  - evolution: The next remote-control/platform hardening slice was not a new architecture layer. It was closure on the typed paths that already existed but still left practical escape hatches. On the write side, `devctl commit` no lo…
- **`7ac4d4f1` | markers: F1, F4** — Preserve Claude-CLI session 6 WIP (F1 + F4 + test + README) before solo-Codex test
  - Session 6 (PIDs 71697/71734) survived 34+ minutes — new session
  - record, 2.5x longer than session 5 death — but Claude-CLI never
  - committed its in-flight work, so Codex had nothing new to review
  - evolution: The next remote-control/platform hardening slice was not a new architecture layer. It was closure on the typed paths that already existed but still left practical escape hatches. On the write side, `devctl commit` no lo…
- **`527eb1b2`** — LIVE_RUN: Q54 role separation unclear — publisher vs supervisor + no typed role contracts
  - evolution: The next remote-control/platform hardening slice was not a new architecture layer. It was closure on the typed paths that already existed but still left practical escape hatches. On the write side, `devctl commit` no lo…
- **`22b06b22`** — LIVE_RUN: Q53 bootstrap guidance missing — AI agents learn by trial and error
  - Root cause of every 'I didn't know X' finding in this session:
  - Claude-Code receives a generic prompt at session start and has
  - no typed onboarding protocol that tells it which devctl commands
  - evolution: The next remote-control/platform hardening slice was not a new architecture layer. It was closure on the typed paths that already existed but still left practical escape hatches. On the write side, `devctl commit` no lo…
- **`c5890296`** — LIVE_RUN: Q52 TOP-LEVEL ARCHITECTURAL FAILURE — AI agents fly blind on typed state
  - Operator correctly identified that the real root-cause of the
  - discoverability findings (Q22/Q45/Q46/Q50) is a top-level
  - architectural failure: the governance platform invests heavily in
  - evolution: The next remote-control/platform hardening slice was not a new architecture layer. It was closure on the typed paths that already existed but still left practical escape hatches. On the write side, `devctl commit` no lo…
- **`e9a37347`** — LIVE_RUN: Q50 lazy dashboard + Q51 update cadence drift (AI misalignment)
  - evolution: The next remote-control/platform hardening slice was not a new architecture layer. It was closure on the typed paths that already existed but still left practical escape hatches. On the write side, `devctl commit` no lo…
- **`81cff0d8`** — Refresh external review snapshot for 079d7f3f
  - evolution: The next remote-control/platform hardening slice was not a new architecture layer. It was closure on the typed paths that already existed but still left practical escape hatches. On the write side, `devctl commit` no lo…
- **`079d7f3f` | markers: F1** — Preserve Claude-CLI WIP (F1 consumer wiring) from session 5 death
  - Session 5 (PIDs 32968/33008) died at 20:20:57Z after reaching 18:44
  - elapsed, just past the Q41-protected ~7min death window (proving Q41
  - fixed the process-sweep cause) but still short of task completion.
  - evolution: The next remote-control/platform hardening slice was not a new architecture layer. It was closure on the typed paths that already existed but still left practical escape hatches. On the write side, `devctl commit` no lo…
- **`dde77865` | MPs: MP-388** — LIVE_RUN: add AI Research Lane architecture proposal (Codex review lane)
  - Operator requested formalizing the beta-test flow this session has
  - been running ad-hoc ('research → LIVE_RUN → Codex review → Claude
  - implement') as a first-class governed architecture. Proposal is
  - evolution: The next remote-control/platform hardening slice was not a new architecture layer. It was closure on the typed paths that already existed but still left practical escape hatches. On the write side, `devctl commit` no lo…
- **`9515a083`** — LIVE_RUN: Q45/Q46/Q47 from typed-state discoverability audit
  - evolution: The next remote-control/platform hardening slice was not a new architecture layer. It was closure on the typed paths that already existed but still left practical escape hatches. On the write side, `devctl commit` no lo…
- **`5f5c049f`** — LIVE_RUN: Q43 publisher lifecycle drift + Q44 publisher reaper risk
  - evolution: The next remote-control/platform hardening slice was not a new architecture layer. It was closure on the typed paths that already existed but still left practical escape hatches. On the write side, `devctl commit` no lo…
- **`a65da5bf`** — Refresh external review snapshot for e596901
  - evolution: The next remote-control/platform hardening slice was not a new architecture layer. It was closure on the typed paths that already existed but still left practical escape hatches. On the write side, `devctl commit` no lo…
- **`e5969014` | markers: F1** — Preserve Claude-CLI WIP (F1 extension) from second session death (Q38)
  - The second conductor session (PIDs 62800 Codex, 62835 Claude-CLI at
  - 19:30-19:37Z) produced the following in-progress edits before both
  - conductors were silently reaped by process-sweep-post (Q41):
  - evolution: The next remote-control/platform hardening slice was not a new architecture layer. It was closure on the typed paths that already existed but still left practical escape hatches. On the write side, `devctl commit` no lo…
- **`4522b125`** — Fix Q41: exclude registered conductor shells from orphan/stale reap
  - Root cause of every silent conductor death observed during the
  - remote_control beta test (see LIVE_RUN.md Q41). devctl commit →
  - check --profile quick → process-sweep-post → split_orphaned_processes
  - evolution: The next remote-control/platform hardening slice was not a new architecture layer. It was closure on the typed paths that already existed but still left practical escape hatches. On the write side, `devctl commit` no lo…
- **`b7674a38`** — LIVE_RUN: Q41 ROOT CAUSE — process-sweep-post reaps live conductors
  - This is the architectural root cause of every silent conductor death
  - observed during this remote_control beta test session. devctl commit
  - runs check --profile quick which includes process-sweep-post which
  - evolution: The next remote-control/platform hardening slice was not a new architecture layer. It was closure on the typed paths that already existed but still left practical escape hatches. On the write side, `devctl commit` no lo…
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

- open governance findings: 39

### Startup advisories
- checkpoint_before_continue: dirty_path_budget_exceeded

### Stale warnings
- Keep editing the current slice.
- Move straight to the governed push path.

### Open gap rows
- **governance_open** (`dev/scripts/devctl/review_channel/bridge_sanitize.py`): agent_checkpoint_contract_ignorance: 
- **governance_open** (`dev/scripts/devctl/review_channel/state.py`): claude_uses_osascript_not_typed_system: 
- **governance_open** (`dev/scripts/devctl/review_channel/push_state.py`): push_invalidation_head_equality: 
- **governance_open** (`dev/scripts/devctl/review_channel/state.py`): reviewer_truth_distributed_no_owner: 
- **governance_open** (`dev/scripts/devctl/runtime/startup_context.py`): startup_surface_tokens_unpopulated: 
- **governance_open** (`dev/scripts/devctl/review_channel/terminal_app.py`): terminal_window_id_not_captured: 
- **governance_open** (`dev/scripts/devctl/review_channel/bridge_projection_state.py`): bridge_projection_drops_operator_direction: 
- **governance_open** (`dev/scripts/devctl/review_channel/state.py`): bridge_still_active_gate_not_projection: 

---

Projection produced by `devctl review-snapshot`. Generation stamp `snap-70f4e6fd3f20` binds this file to HEAD `516e839c78de`; if they drift, the freshness guard will fail CI. When the latest commit only refreshes this generated snapshot, the guard accepts this file as bound to that commit's parent code state.
