# VoiceTerm — Review Snapshot

> Deterministically generated from typed governance state. Do not edit by hand — rerun `devctl review-snapshot --write`.

## Quick status

- Branch: `feature/governance-quality-sweep`
- HEAD: `079d7f3f1228` — Preserve Claude-CLI WIP (F1 consumer wiring) from session 5 death
- Tree hash: `b981e5c7b3e2`
- Generation stamp: `snap-3d360cd519ca`
- Generated at (UTC): 2026-04-08T20:38:09Z
- Push decision: `await_review` — reviewer_overdue
- Reviewer mode: `tools_only` (interaction: `local_terminal`)
- Pipeline state: `n/a` (approval: `n/a`)
- Delta since last snapshot: 24 commits, 13 files, +2536/-1310
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
- HEAD SHA: `079d7f3f1228b70744ad226ef7a8b86a803bae85`
- HEAD author: Justin Guida
- HEAD timestamp (UTC): 2026-04-08T16:37:50-04:00

## 2. Governance state

### Push decision
- action: `await_review`
- reason: reviewer_overdue
- push_eligible_now: False
- worktree_clean: True
- next_step_command: `python3 dev/scripts/devctl.py review-channel --action status --terminal none --format json`
- latest_push_report: `dev/reports/push/latest.json`
- latest_push_report_state: `blocked` (validation_failed)
- current_push_authorization: `push-auth-20260407T220000Z-hardening-plan` (valid=False)
- authorized_head_commit: `ee13a6c6337f395afa574e99a4234f2eaf45a161`
- approved_target_identity: `tree-receipt-20260407T220000Z:281dea21851063411d2c43c2b4621a1c2a1168b5`
- publication_backlog: urgent
- publication_guidance: 21 local commit(s) waiting for governed push once review is accepted.

### Reviewer runtime
- reviewer_mode: `tools_only`
- reviewer_freshness: unknown
- reviewer_publish_clear: False
- interaction_mode: `local_terminal`
- implementation_blocked: yes — reviewer_overdue

### Remote commit pipeline
- state: `n/a`
- approval_state: `n/a`

### Work intake
- active plan: **Master Plan (Active, Unified)**
- plan path: `dev/active/MASTER_PLAN.md`
- active MP scope: all active MP execution state
- advisory: `repair_reviewer_loop` — reviewer_overdue

## 3. Delta — what changed since the previous snapshot

Range: last 24 commits ending at `079d7f3f1228`

- commits: 24
- files changed: 13
- insertions: +2536
- deletions: -1310
- bundle classes touched: docs, tooling
- authority surfaces touched: 1 file(s)

### Commits

| # | SHA | Subject | Files | +/- | Bundle | Risk |
|---|---|---|---|---|---|---|
| 1 | `079d7f3f` | Preserve Claude-CLI WIP (F1 consumer wiring) from session 5… | 4 | +155/-155 | tooling |  |
| 2 | `dde77865` | LIVE_RUN: add AI Research Lane architecture proposal (Codex… | 2 | +217/-49 | tooling |  |
| 3 | `9515a083` | LIVE_RUN: Q45/Q46/Q47 from typed-state discoverability audit | 2 | +147/-45 | tooling |  |
| 4 | `5f5c049f` | LIVE_RUN: Q43 publisher lifecycle drift + Q44 publisher rea… | 2 | +150/-55 | tooling |  |
| 5 | `a65da5bf` | Refresh external review snapshot for e596901 | 1 | +55/-54 | tooling |  |
| 6 | `e5969014` | Preserve Claude-CLI WIP (F1 extension) from second session… | 3 | +230/-46 | tooling |  |
| 7 | `4522b125` | Fix Q41: exclude registered conductor shells from orphan/st… | 2 | +98/-45 | tooling |  |
| 8 | `b7674a38` | LIVE_RUN: Q41 ROOT CAUSE — process-sweep-post reaps live co… | 2 | +109/-49 | tooling |  |
| 9 | `c60bd77b` | LIVE_RUN: Q33-Q40 findings from full surface audit + guard-… | 3 | +238/-57 | tooling |  |
| 10 | `839008c6` | Refresh external review snapshot for 17d7c73 | 1 | +41/-38 | tooling |  |
| 11 | `17d7c734` | Refresh external review snapshot for 1de0fc0 | 1 | +41/-41 | tooling |  |
| 12 | `1de0fc06` | Bridge refresh: Codex polls post-relaunch at 19:30:05Z + 19… | 2 | +58/-60 | docs |  |
| 13 | `7a1ba282` | LIVE_RUN: A11 + Q31 role drift self-correction + Q32 Q4 reg… | 2 | +174/-49 | tooling |  |
| 14 | `73842029` | Extend Q1 bypass to concurrent-writer rule (Q30) + regen AG… | 3 | +50/-48 | tooling |  |
| 15 | `015cec99` | Refresh external review snapshot for 7889291 | 1 | +52/-57 | tooling |  |
| 16 | `78892916` | Fix Q18: bundle.docs docs-check missing --since-ref origin/… | 2 | +59/-49 | tooling |  |
| 17 | `12594100` | Refresh external review snapshot for 44c0018 | 1 | +41/-47 | tooling |  |
| 18 | `44c0018d` | Refresh external review snapshot for d9a9a3b | 1 | +52/-57 | tooling |  |
| 19 | `d9a9a3b7` | CHANGELOG: Q1 FIXED + A1-A10 automation gaps entry (unblock… | 2 | +70/-48 | docs |  |
| 20 | `2ec69918` | Refresh external review snapshot for 2ee89e5 | 1 | +52/-56 | tooling |  |
| 21 | `2ee89e50` | LIVE_RUN: Q1 FIXED + Q29 + A1-A10 automation gaps (remote_c… | 2 | +267/-50 | tooling |  |
| 22 | `5c95b87b` | Refresh external review snapshot for ee0a1d0 | 1 | +40/-46 | tooling |  |
| 23 | `ee0a1d08` | Refresh external review snapshot for 2bd24b1 | 1 | +55/-49 | tooling |  |
| 24 | `2bd24b15` | Fix Q1: devctl commit self-block via DEVCTL_COMMIT_GATE_BYP… | 3 | +85/-60 | tooling |  |

### Files

| Path | Bundle | +/- |
|---|---|---|
| `AGENTS.md` | docs | +1/-1 |
| `bridge.md` | docs | +24/-24 |
| `dev/CHANGELOG.md` | docs | +19/-0 |
| `dev/audits/LIVE_RUN.md` | tooling | +965/-1 |
| `dev/audits/REVIEW_SNAPSHOT.md` | tooling | +1178/-1220 |
| `dev/scripts/checks/startup_authority_contract/runtime_checks.py` | tooling | +12/-0 |
| `dev/scripts/devctl/bundles/registry.py` | tooling | +8/-1 |
| `dev/scripts/devctl/commands/governance/session_resume_support.py` | tooling | +42/-43 |
| `dev/scripts/devctl/commands/vcs/commit.py` | tooling | +24/-2 |
| `dev/scripts/devctl/platform/coordination_snapshot.py` | tooling | +11/-1 |
| `dev/scripts/devctl/process_sweep/internals.py` | tooling | +51/-4 |
| `dev/scripts/devctl/runtime/control_plane_read_model.py` | tooling | +27/-13 |
| `dev/scripts/devctl/runtime/coordination_loader.py` | tooling | +174/-0 |

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

- **authority_surface**: Typed authority surface touched (`dev/scripts/checks/startup_authority_contract/runtime_checks.py`) — Review contract-level invariants for this file

### Suggested verification commands

- `python3 dev/scripts/devctl.py check --profile ci`
- `python3 dev/scripts/devctl.py probe-report --format md`
- `python3 dev/scripts/devctl.py docs-check --strict-tooling`
- `python3 dev/scripts/devctl.py governance-review --format md`
- `python3 dev/scripts/devctl.py check-router --format md`

## 7. Reasoning — why these changes landed

### Per-commit rationale

- **`079d7f3f` | markers: F1** — Preserve Claude-CLI WIP (F1 consumer wiring) from session 5 death
  - Session 5 (PIDs 32968/33008) died at 20:20:57Z after reaching 18:44
  - elapsed, just past the Q41-protected ~7min death window (proving Q41
  - fixed the process-sweep cause) but still short of task completion.
  - evolution: The next coordination follow-up was not another reducer. The reducer already existed and multiple rich surfaces already rendered it. The miss was load-bearing: the shared `ControlPlaneReadModel` still had no coordinatio…
- **`dde77865` | MPs: MP-388** — LIVE_RUN: add AI Research Lane architecture proposal (Codex review lane)
  - Operator requested formalizing the beta-test flow this session has
  - been running ad-hoc ('research → LIVE_RUN → Codex review → Claude
  - implement') as a first-class governed architecture. Proposal is
  - evolution: The next coordination follow-up was not another reducer. The reducer already existed and multiple rich surfaces already rendered it. The miss was load-bearing: the shared `ControlPlaneReadModel` still had no coordinatio…
- **`9515a083`** — LIVE_RUN: Q45/Q46/Q47 from typed-state discoverability audit
  - evolution: The next coordination follow-up was not another reducer. The reducer already existed and multiple rich surfaces already rendered it. The miss was load-bearing: the shared `ControlPlaneReadModel` still had no coordinatio…
- **`5f5c049f`** — LIVE_RUN: Q43 publisher lifecycle drift + Q44 publisher reaper risk
  - evolution: The next coordination follow-up was not another reducer. The reducer already existed and multiple rich surfaces already rendered it. The miss was load-bearing: the shared `ControlPlaneReadModel` still had no coordinatio…
- **`a65da5bf`** — Refresh external review snapshot for e596901
  - evolution: The next coordination follow-up was not another reducer. The reducer already existed and multiple rich surfaces already rendered it. The miss was load-bearing: the shared `ControlPlaneReadModel` still had no coordinatio…
- **`e5969014` | markers: F1** — Preserve Claude-CLI WIP (F1 extension) from second session death (Q38)
  - The second conductor session (PIDs 62800 Codex, 62835 Claude-CLI at
  - 19:30-19:37Z) produced the following in-progress edits before both
  - conductors were silently reaped by process-sweep-post (Q41):
  - evolution: The next coordination follow-up was not another reducer. The reducer already existed and multiple rich surfaces already rendered it. The miss was load-bearing: the shared `ControlPlaneReadModel` still had no coordinatio…
- **`4522b125`** — Fix Q41: exclude registered conductor shells from orphan/stale reap
  - Root cause of every silent conductor death observed during the
  - remote_control beta test (see LIVE_RUN.md Q41). devctl commit →
  - check --profile quick → process-sweep-post → split_orphaned_processes
  - evolution: The next coordination follow-up was not another reducer. The reducer already existed and multiple rich surfaces already rendered it. The miss was load-bearing: the shared `ControlPlaneReadModel` still had no coordinatio…
- **`b7674a38`** — LIVE_RUN: Q41 ROOT CAUSE — process-sweep-post reaps live conductors
  - This is the architectural root cause of every silent conductor death
  - observed during this remote_control beta test session. devctl commit
  - runs check --profile quick which includes process-sweep-post which
  - evolution: The next coordination follow-up was not another reducer. The reducer already existed and multiple rich surfaces already rendered it. The miss was load-bearing: the shared `ControlPlaneReadModel` still had no coordinatio…
- **`c60bd77b`** — LIVE_RUN: Q33-Q40 findings from full surface audit + guard-block cascade
  - evolution: The next coordination follow-up was not another reducer. The reducer already existed and multiple rich surfaces already rendered it. The miss was load-bearing: the shared `ControlPlaneReadModel` still had no coordinatio…
- **`839008c6`** — Refresh external review snapshot for 17d7c73
  - evolution: The next coordination follow-up was not another reducer. The reducer already existed and multiple rich surfaces already rendered it. The miss was load-bearing: the shared `ControlPlaneReadModel` still had no coordinatio…
- **`17d7c734`** — Refresh external review snapshot for 1de0fc0
  - evolution: The next coordination follow-up was not another reducer. The reducer already existed and multiple rich surfaces already rendered it. The miss was load-bearing: the shared `ControlPlaneReadModel` still had no coordinatio…
- **`1de0fc06`** — Bridge refresh: Codex polls post-relaunch at 19:30:05Z + 19:31:03Z heartbeat
  - evolution: The next coordination follow-up was not another reducer. The reducer already existed and multiple rich surfaces already rendered it. The miss was load-bearing: the shared `ControlPlaneReadModel` still had no coordinatio…
- **`7a1ba282`** — LIVE_RUN: A11 + Q31 role drift self-correction + Q32 Q4 regression
  - evolution: The next coordination follow-up was not another reducer. The reducer already existed and multiple rich surfaces already rendered it. The miss was load-bearing: the shared `ControlPlaneReadModel` still had no coordinatio…
- **`73842029`** — Extend Q1 bypass to concurrent-writer rule (Q30) + regen AGENTS.md after Q18 fix
  - evolution: The next coordination follow-up was not another reducer. The reducer already existed and multiple rich surfaces already rendered it. The miss was load-bearing: the shared `ControlPlaneReadModel` still had no coordinatio…
- **`015cec99`** — Refresh external review snapshot for 7889291
  - evolution: The next coordination follow-up was not another reducer. The reducer already existed and multiple rich surfaces already rendered it. The miss was load-bearing: the shared `ControlPlaneReadModel` still had no coordinatio…
- **`78892916`** — Fix Q18: bundle.docs docs-check missing --since-ref origin/develop
  - evolution: The next coordination follow-up was not another reducer. The reducer already existed and multiple rich surfaces already rendered it. The miss was load-bearing: the shared `ControlPlaneReadModel` still had no coordinatio…
- **`12594100`** — Refresh external review snapshot for 44c0018
  - evolution: The next coordination follow-up was not another reducer. The reducer already existed and multiple rich surfaces already rendered it. The miss was load-bearing: the shared `ControlPlaneReadModel` still had no coordinatio…
- **`44c0018d`** — Refresh external review snapshot for d9a9a3b
  - evolution: The next coordination follow-up was not another reducer. The reducer already existed and multiple rich surfaces already rendered it. The miss was load-bearing: the shared `ControlPlaneReadModel` still had no coordinatio…
- **`d9a9a3b7`** — CHANGELOG: Q1 FIXED + A1-A10 automation gaps entry (unblock docs-check)
  - evolution: The next coordination follow-up was not another reducer. The reducer already existed and multiple rich surfaces already rendered it. The miss was load-bearing: the shared `ControlPlaneReadModel` still had no coordinatio…
- **`2ec69918`** — Refresh external review snapshot for 2ee89e5
  - evolution: The next coordination follow-up was not another reducer. The reducer already existed and multiple rich surfaces already rendered it. The miss was load-bearing: the shared `ControlPlaneReadModel` still had no coordinatio…
- **`2ee89e50`** — LIVE_RUN: Q1 FIXED + Q29 + A1-A10 automation gaps (remote_control beta test)
  - evolution: The next coordination follow-up was not another reducer. The reducer already existed and multiple rich surfaces already rendered it. The miss was load-bearing: the shared `ControlPlaneReadModel` still had no coordinatio…
- **`5c95b87b`** — Refresh external review snapshot for ee0a1d0
  - evolution: The next coordination follow-up was not another reducer. The reducer already existed and multiple rich surfaces already rendered it. The miss was load-bearing: the shared `ControlPlaneReadModel` still had no coordinatio…
- **`ee0a1d08`** — Refresh external review snapshot for 2bd24b1
  - evolution: The next coordination follow-up was not another reducer. The reducer already existed and multiple rich surfaces already rendered it. The miss was load-bearing: the shared `ControlPlaneReadModel` still had no coordinatio…
- **`2bd24b15`** — Fix Q1: devctl commit self-block via DEVCTL_COMMIT_GATE_BYPASS_STARTUP_AUTHORITY env var
  - evolution: The next coordination follow-up was not another reducer. The reducer already existed and multiple rich surfaces already rendered it. The miss was load-bearing: the shared `ControlPlaneReadModel` still had no coordinatio…
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
- repair_reviewer_loop: reviewer_overdue

### Stale warnings
- Cut a checkpoint before doing anything else.

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

Projection produced by `devctl review-snapshot`. Generation stamp `snap-3d360cd519ca` binds this file to HEAD `079d7f3f1228`; if they drift, the freshness guard will fail CI. When the latest commit only refreshes this generated snapshot, the guard accepts this file as bound to that commit's parent code state.
