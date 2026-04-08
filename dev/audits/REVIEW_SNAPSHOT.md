# VoiceTerm — Review Snapshot

> Deterministically generated from typed governance state. Do not edit by hand — rerun `devctl review-snapshot --write`.

## Quick status

- Branch: `feature/governance-quality-sweep`
- HEAD: `8330b1d9668b` — LIVE_RUN: Q58 autonomy-swarm discoverability + full system test plan (6 tests)
- Tree hash: `7f61b250a170`
- Generation stamp: `snap-09a3cf48b691`
- Generated at (UTC): 2026-04-08T21:46:52Z
- Push decision: `await_checkpoint` — worktree_dirty
- Reviewer mode: `tools_only` (interaction: `unresolved`)
- Pipeline state: `n/a` (approval: `n/a`)
- Delta since last snapshot: 24 commits, 19 files, +3674/-1320
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
- HEAD SHA: `8330b1d9668b4b829d38e8aa601aec38bf7efa21`
- HEAD author: Justin Guida
- HEAD timestamp (UTC): 2026-04-08T17:35:43-04:00

## 2. Governance state

### Push decision
- action: `await_checkpoint`
- reason: worktree_dirty
- push_eligible_now: False
- worktree_clean: False
- next_step_command: `n/a`
- latest_push_report: `dev/reports/push/latest.json`
- latest_push_report_state: `blocked` (validation_failed)
- current_push_authorization: `push-auth-20260407T220000Z-hardening-plan` (valid=False)
- authorized_head_commit: `ee13a6c6337f395afa574e99a4234f2eaf45a161`
- approved_target_identity: `tree-receipt-20260407T220000Z:281dea21851063411d2c43c2b4621a1c2a1168b5`
- publication_backlog: urgent
- publication_guidance: 31 local commit(s) waiting for governed push once the current slice is checkpoint-clean.

### Reviewer runtime
- reviewer_mode: `tools_only`
- reviewer_freshness: unknown
- reviewer_publish_clear: False
- interaction_mode: `unresolved`
- implementation_blocked: yes — reviewer_heartbeat_stale

### Remote commit pipeline
- state: `n/a`
- approval_state: `n/a`

### Work intake
- active plan: **Master Plan (Active, Unified)**
- plan path: `dev/active/MASTER_PLAN.md`
- active MP scope: all active MP execution state
- advisory: `checkpoint_before_continue` — concurrent_writer_activity

## 3. Delta — what changed since the previous snapshot

Range: last 24 commits ending at `8330b1d9668b`

- commits: 24
- files changed: 19
- insertions: +3674
- deletions: -1320
- bundle classes touched: tooling, docs
- authority surfaces touched: 2 file(s)

### Commits

| # | SHA | Subject | Files | +/- | Bundle | Risk |
|---|---|---|---|---|---|---|
| 1 | `8330b1d9` | LIVE_RUN: Q58 autonomy-swarm discoverability + full system… | 2 | +254/-42 | tooling |  |
| 2 | `06d591c0` | LIVE_RUN: Q55 THE DISEASE (authority-lane split) + Q56 smok… | 2 | +281/-51 | tooling |  |
| 3 | `c6743678` | Refresh external review snapshot for ffc7f954 | 1 | +58/-50 | tooling |  |
| 4 | `ffc7f954` | Preserve Claude-CLI session 6 WIP batch 2 (plan docs + new… | 8 | +325/-56 | tooling |  |
| 5 | `7ac4d4f1` | Preserve Claude-CLI session 6 WIP (F1 + F4 + test + README)… | 6 | +220/-82 | tooling |  |
| 6 | `527eb1b2` | LIVE_RUN: Q54 role separation unclear — publisher vs superv… | 2 | +166/-40 | tooling |  |
| 7 | `22b06b22` | LIVE_RUN: Q53 bootstrap guidance missing — AI agents learn… | 2 | +182/-63 | tooling |  |
| 8 | `c5890296` | LIVE_RUN: Q52 TOP-LEVEL ARCHITECTURAL FAILURE — AI agents f… | 2 | +170/-42 | tooling |  |
| 9 | `e9a37347` | LIVE_RUN: Q50 lazy dashboard + Q51 update cadence drift (AI… | 2 | +200/-53 | tooling |  |
| 10 | `81cff0d8` | Refresh external review snapshot for 079d7f3f | 1 | +55/-50 | tooling |  |
| 11 | `079d7f3f` | Preserve Claude-CLI WIP (F1 consumer wiring) from session 5… | 4 | +155/-155 | tooling |  |
| 12 | `dde77865` | LIVE_RUN: add AI Research Lane architecture proposal (Codex… | 2 | +217/-49 | tooling |  |
| 13 | `9515a083` | LIVE_RUN: Q45/Q46/Q47 from typed-state discoverability audit | 2 | +147/-45 | tooling |  |
| 14 | `5f5c049f` | LIVE_RUN: Q43 publisher lifecycle drift + Q44 publisher rea… | 2 | +150/-55 | tooling |  |
| 15 | `a65da5bf` | Refresh external review snapshot for e596901 | 1 | +55/-54 | tooling |  |
| 16 | `e5969014` | Preserve Claude-CLI WIP (F1 extension) from second session… | 3 | +230/-46 | tooling |  |
| 17 | `4522b125` | Fix Q41: exclude registered conductor shells from orphan/st… | 2 | +98/-45 | tooling |  |
| 18 | `b7674a38` | LIVE_RUN: Q41 ROOT CAUSE — process-sweep-post reaps live co… | 2 | +109/-49 | tooling |  |
| 19 | `c60bd77b` | LIVE_RUN: Q33-Q40 findings from full surface audit + guard-… | 3 | +238/-57 | tooling |  |
| 20 | `839008c6` | Refresh external review snapshot for 17d7c73 | 1 | +41/-38 | tooling |  |
| 21 | `17d7c734` | Refresh external review snapshot for 1de0fc0 | 1 | +41/-41 | tooling |  |
| 22 | `1de0fc06` | Bridge refresh: Codex polls post-relaunch at 19:30:05Z + 19… | 2 | +58/-60 | docs |  |
| 23 | `7a1ba282` | LIVE_RUN: A11 + Q31 role drift self-correction + Q32 Q4 reg… | 2 | +174/-49 | tooling |  |
| 24 | `73842029` | Extend Q1 bypass to concurrent-writer rule (Q30) + regen AG… | 3 | +50/-48 | tooling |  |

### Files

| Path | Bundle | +/- |
|---|---|---|
| `AGENTS.md` | docs | +2/-1 |
| `bridge.md` | docs | +56/-67 |
| `dev/active/MASTER_PLAN.md` | tooling | +21/-0 |
| `dev/active/ai_governance_platform.md` | tooling | +25/-0 |
| `dev/audits/LIVE_RUN.md` | tooling | +1706/-0 |
| `dev/audits/REVIEW_SNAPSHOT.md` | tooling | +1186/-1183 |
| `dev/guides/DEVELOPMENT.md` | docs | +12/-1 |
| `dev/history/ENGINEERING_EVOLUTION.md` | tooling | +42/-0 |
| `dev/scripts/README.md` | tooling | +12/-0 |
| `dev/scripts/checks/startup_authority_contract/runtime_checks.py` | tooling | +2/-0 |
| `dev/scripts/devctl/commands/governance/session_resume_support.py` | tooling | +42/-43 |
| `dev/scripts/devctl/governance/draft_policy_scan.py` | tooling | +18/-0 |
| `dev/scripts/devctl/platform/coordination_snapshot.py` | tooling | +11/-1 |
| `dev/scripts/devctl/process_sweep/internals.py` | tooling | +51/-4 |
| `dev/scripts/devctl/runtime/control_plane_read_model.py` | tooling | +27/-13 |
| `dev/scripts/devctl/runtime/coordination_loader.py` | tooling | +174/-0 |
| `dev/scripts/devctl/runtime/startup_context.py` | tooling | +28/-7 |
| `dev/scripts/devctl/tests/runtime/test_coordination_loader_wiring.py` | tooling | +166/-0 |
| `dev/scripts/devctl/tests/runtime/test_operator_mode_fail_closed.py` | tooling | +93/-0 |

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

- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/startup_context.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/checks/startup_authority_contract/runtime_checks.py`) — Review contract-level invariants for this file

### Suggested verification commands

- `python3 dev/scripts/devctl.py check --profile ci`
- `python3 dev/scripts/devctl.py probe-report --format md`
- `python3 dev/scripts/devctl.py docs-check --strict-tooling`
- `python3 dev/scripts/devctl.py governance-review --format md`
- `python3 dev/scripts/devctl.py check-router --format md`

## 7. Reasoning — why these changes landed

### Per-commit rationale

- **`8330b1d9`** — LIVE_RUN: Q58 autonomy-swarm discoverability + full system test plan (6 tests)
  - Operator asked 'what is the best way to test all of this system and
  - make sure it is fully connected?' — and mentioned 'saved cards for
  - this.' The saved-cards answer is devctl autonomy-swarm, a
  - evolution: The previous coordination slice landed `CoordinationSnapshot` on `ControlPlaneReadModel` and added `dev/scripts/devctl/runtime/coordination_loader.py` as the canonical resolution path. `session_resume_support` and `cont…
- **`06d591c0`** — LIVE_RUN: Q55 THE DISEASE (authority-lane split) + Q56 smoking gun + Q57 --claude-workers flag bug
  - Operator's external audit (via ChatGPT Pro) diagnosed the root
  - architectural failure this entire session has been circling
  - without naming:
  - evolution: The previous coordination slice landed `CoordinationSnapshot` on `ControlPlaneReadModel` and added `dev/scripts/devctl/runtime/coordination_loader.py` as the canonical resolution path. `session_resume_support` and `cont…
- **`c6743678`** — Refresh external review snapshot for ffc7f954
  - evolution: The previous coordination slice landed `CoordinationSnapshot` on `ControlPlaneReadModel` and added `dev/scripts/devctl/runtime/coordination_loader.py` as the canonical resolution path. `session_resume_support` and `cont…
- **`ffc7f954`** — Preserve Claude-CLI session 6 WIP batch 2 (plan docs + new coordination loader test)
  - Additional Claude-CLI work from session 6 not captured in the first
  - preservation commit (7ac4d4f1). Session 6 was more productive than
  - the git diff --stat view suggested:
  - evolution: The previous coordination slice landed `CoordinationSnapshot` on `ControlPlaneReadModel` and added `dev/scripts/devctl/runtime/coordination_loader.py` as the canonical resolution path. `session_resume_support` and `cont…
- **`7ac4d4f1` | markers: F1, F4** — Preserve Claude-CLI session 6 WIP (F1 + F4 + test + README) before solo-Codex test
  - Session 6 (PIDs 71697/71734) survived 34+ minutes — new session
  - record, 2.5x longer than session 5 death — but Claude-CLI never
  - committed its in-flight work, so Codex had nothing new to review
  - evolution: The previous coordination slice landed `CoordinationSnapshot` on `ControlPlaneReadModel` and added `dev/scripts/devctl/runtime/coordination_loader.py` as the canonical resolution path. `session_resume_support` and `cont…
- **`527eb1b2`** — LIVE_RUN: Q54 role separation unclear — publisher vs supervisor + no typed role contracts
  - evolution: The previous coordination slice landed `CoordinationSnapshot` on `ControlPlaneReadModel` and added `dev/scripts/devctl/runtime/coordination_loader.py` as the canonical resolution path. `session_resume_support` and `cont…
- **`22b06b22`** — LIVE_RUN: Q53 bootstrap guidance missing — AI agents learn by trial and error
  - Root cause of every 'I didn't know X' finding in this session:
  - Claude-Code receives a generic prompt at session start and has
  - no typed onboarding protocol that tells it which devctl commands
  - evolution: The previous coordination slice landed `CoordinationSnapshot` on `ControlPlaneReadModel` and added `dev/scripts/devctl/runtime/coordination_loader.py` as the canonical resolution path. `session_resume_support` and `cont…
- **`c5890296`** — LIVE_RUN: Q52 TOP-LEVEL ARCHITECTURAL FAILURE — AI agents fly blind on typed state
  - Operator correctly identified that the real root-cause of the
  - discoverability findings (Q22/Q45/Q46/Q50) is a top-level
  - architectural failure: the governance platform invests heavily in
  - evolution: The previous coordination slice landed `CoordinationSnapshot` on `ControlPlaneReadModel` and added `dev/scripts/devctl/runtime/coordination_loader.py` as the canonical resolution path. `session_resume_support` and `cont…
- **`e9a37347`** — LIVE_RUN: Q50 lazy dashboard + Q51 update cadence drift (AI misalignment)
  - evolution: The previous coordination slice landed `CoordinationSnapshot` on `ControlPlaneReadModel` and added `dev/scripts/devctl/runtime/coordination_loader.py` as the canonical resolution path. `session_resume_support` and `cont…
- **`81cff0d8`** — Refresh external review snapshot for 079d7f3f
  - evolution: The previous coordination slice landed `CoordinationSnapshot` on `ControlPlaneReadModel` and added `dev/scripts/devctl/runtime/coordination_loader.py` as the canonical resolution path. `session_resume_support` and `cont…
- **`079d7f3f` | markers: F1** — Preserve Claude-CLI WIP (F1 consumer wiring) from session 5 death
  - Session 5 (PIDs 32968/33008) died at 20:20:57Z after reaching 18:44
  - elapsed, just past the Q41-protected ~7min death window (proving Q41
  - fixed the process-sweep cause) but still short of task completion.
  - evolution: The previous coordination slice landed `CoordinationSnapshot` on `ControlPlaneReadModel` and added `dev/scripts/devctl/runtime/coordination_loader.py` as the canonical resolution path. `session_resume_support` and `cont…
- **`dde77865` | MPs: MP-388** — LIVE_RUN: add AI Research Lane architecture proposal (Codex review lane)
  - Operator requested formalizing the beta-test flow this session has
  - been running ad-hoc ('research → LIVE_RUN → Codex review → Claude
  - implement') as a first-class governed architecture. Proposal is
  - evolution: The previous coordination slice landed `CoordinationSnapshot` on `ControlPlaneReadModel` and added `dev/scripts/devctl/runtime/coordination_loader.py` as the canonical resolution path. `session_resume_support` and `cont…
- **`9515a083`** — LIVE_RUN: Q45/Q46/Q47 from typed-state discoverability audit
  - evolution: The previous coordination slice landed `CoordinationSnapshot` on `ControlPlaneReadModel` and added `dev/scripts/devctl/runtime/coordination_loader.py` as the canonical resolution path. `session_resume_support` and `cont…
- **`5f5c049f`** — LIVE_RUN: Q43 publisher lifecycle drift + Q44 publisher reaper risk
  - evolution: The previous coordination slice landed `CoordinationSnapshot` on `ControlPlaneReadModel` and added `dev/scripts/devctl/runtime/coordination_loader.py` as the canonical resolution path. `session_resume_support` and `cont…
- **`a65da5bf`** — Refresh external review snapshot for e596901
  - evolution: The previous coordination slice landed `CoordinationSnapshot` on `ControlPlaneReadModel` and added `dev/scripts/devctl/runtime/coordination_loader.py` as the canonical resolution path. `session_resume_support` and `cont…
- **`e5969014` | markers: F1** — Preserve Claude-CLI WIP (F1 extension) from second session death (Q38)
  - The second conductor session (PIDs 62800 Codex, 62835 Claude-CLI at
  - 19:30-19:37Z) produced the following in-progress edits before both
  - conductors were silently reaped by process-sweep-post (Q41):
  - evolution: The previous coordination slice landed `CoordinationSnapshot` on `ControlPlaneReadModel` and added `dev/scripts/devctl/runtime/coordination_loader.py` as the canonical resolution path. `session_resume_support` and `cont…
- **`4522b125`** — Fix Q41: exclude registered conductor shells from orphan/stale reap
  - Root cause of every silent conductor death observed during the
  - remote_control beta test (see LIVE_RUN.md Q41). devctl commit →
  - check --profile quick → process-sweep-post → split_orphaned_processes
  - evolution: The previous coordination slice landed `CoordinationSnapshot` on `ControlPlaneReadModel` and added `dev/scripts/devctl/runtime/coordination_loader.py` as the canonical resolution path. `session_resume_support` and `cont…
- **`b7674a38`** — LIVE_RUN: Q41 ROOT CAUSE — process-sweep-post reaps live conductors
  - This is the architectural root cause of every silent conductor death
  - observed during this remote_control beta test session. devctl commit
  - runs check --profile quick which includes process-sweep-post which
  - evolution: The previous coordination slice landed `CoordinationSnapshot` on `ControlPlaneReadModel` and added `dev/scripts/devctl/runtime/coordination_loader.py` as the canonical resolution path. `session_resume_support` and `cont…
- **`c60bd77b`** — LIVE_RUN: Q33-Q40 findings from full surface audit + guard-block cascade
  - evolution: The previous coordination slice landed `CoordinationSnapshot` on `ControlPlaneReadModel` and added `dev/scripts/devctl/runtime/coordination_loader.py` as the canonical resolution path. `session_resume_support` and `cont…
- **`839008c6`** — Refresh external review snapshot for 17d7c73
  - evolution: The previous coordination slice landed `CoordinationSnapshot` on `ControlPlaneReadModel` and added `dev/scripts/devctl/runtime/coordination_loader.py` as the canonical resolution path. `session_resume_support` and `cont…
- **`17d7c734`** — Refresh external review snapshot for 1de0fc0
  - evolution: The previous coordination slice landed `CoordinationSnapshot` on `ControlPlaneReadModel` and added `dev/scripts/devctl/runtime/coordination_loader.py` as the canonical resolution path. `session_resume_support` and `cont…
- **`1de0fc06`** — Bridge refresh: Codex polls post-relaunch at 19:30:05Z + 19:31:03Z heartbeat
  - evolution: The previous coordination slice landed `CoordinationSnapshot` on `ControlPlaneReadModel` and added `dev/scripts/devctl/runtime/coordination_loader.py` as the canonical resolution path. `session_resume_support` and `cont…
- **`7a1ba282`** — LIVE_RUN: A11 + Q31 role drift self-correction + Q32 Q4 regression
  - evolution: The previous coordination slice landed `CoordinationSnapshot` on `ControlPlaneReadModel` and added `dev/scripts/devctl/runtime/coordination_loader.py` as the canonical resolution path. `session_resume_support` and `cont…
- **`73842029`** — Extend Q1 bypass to concurrent-writer rule (Q30) + regen AGENTS.md after Q18 fix
  - evolution: The previous coordination slice landed `CoordinationSnapshot` on `ControlPlaneReadModel` and added `dev/scripts/devctl/runtime/coordination_loader.py` as the canonical resolution path. `session_resume_support` and `cont…
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
- checkpoint_before_continue: concurrent_writer_activity

### Stale warnings
- Keep editing the current slice.

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

Projection produced by `devctl review-snapshot`. Generation stamp `snap-09a3cf48b691` binds this file to HEAD `8330b1d9668b`; if they drift, the freshness guard will fail CI. When the latest commit only refreshes this generated snapshot, the guard accepts this file as bound to that commit's parent code state.
