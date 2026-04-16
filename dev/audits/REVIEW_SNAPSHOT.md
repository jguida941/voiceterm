# VoiceTerm — Review Snapshot

> Deterministically generated from typed governance state. Do not edit by hand — rerun `devctl review-snapshot --write`.

## Quick status

- Branch: `feature/governance-quality-sweep`
- HEAD: `46679665c8aa` — Hybrid reviewer loop: ensure heartbeats + direct Codex relaunch
- Tree hash: `add92da41df1`
- Generation stamp: `snap-f501be0740f4`
- Generated at (UTC): 2026-04-16T21:02:54Z
- Push decision: `await_review` — review_loop_relaunch_required
- Reviewer mode: `tools_only` (interaction: `local_terminal`)
- Pipeline state: `n/a` (approval: `n/a`)
- Delta since last snapshot: 25 commits, 26 files, +2578/-1411
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
- HEAD SHA: `46679665c8aa160124787460c03e00aa99e2f0eb`
- HEAD author: Justin Guida
- HEAD timestamp (UTC): 2026-04-16T17:02:17-04:00

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

Range: last 25 commits ending at `46679665c8aa`

- commits: 25
- files changed: 26
- insertions: +2578
- deletions: -1411
- bundle classes touched: tooling, docs
- authority surfaces touched: 6 file(s)

### Commits

| # | SHA | Subject | Files | +/- | Bundle | Risk |
|---|---|---|---|---|---|---|
| 1 | `46679665` | Hybrid reviewer loop: ensure heartbeats + direct Codex rela… | 1 | +104/-38 | tooling |  |
| 2 | `7ac8911c` | Wire FindingBacklog into session-resume + cached graph rehy… | 2 | +67/-0 | tooling |  |
| 3 | `107bd54a` | Fix stale snapshot selection: use canonical resolver (Codex… | 1 | +55/-8 | tooling |  |
| 4 | `7d2a3897` | Refresh external review snapshot for 84d06a2d | 2 | +55/-63 | docs |  |
| 5 | `84d06a2d` | Use cached context graph in session-resume — fixes infinite… | 1 | +31/-1 | tooling |  |
| 6 | `f402fbe8` | Refresh external review snapshot for 0f85c5d9 | 2 | +58/-52 | docs |  |
| 7 | `0f85c5d9` | Dashboard reads FindingBacklog for open count (Phase-0 item… | 1 | +10/-1 | tooling |  |
| 8 | `ad1d5a99` | Refresh external review snapshot for 8fa4728c | 2 | +61/-65 | docs |  |
| 9 | `8fa4728c` | Fix reviewer loop wake: --loop sets remote_control mode (re… | 2 | +16/-3 | tooling |  |
| 10 | `68acce2b` | Refresh external review snapshot for 6f8fce71 | 2 | +51/-53 | docs |  |
| 11 | `6f8fce71` | Wire session reviewer loop into governed ensure --follow ru… | 1 | +39/-149 | tooling |  |
| 12 | `a38150a1` | Refresh external review snapshot for 23c4239a | 2 | +49/-64 | docs |  |
| 13 | `23c4239a` | Fix session command blocking (Codex finding rev_pkt_0785):… | 1 | +29/-12 | tooling |  |
| 14 | `598aa8a3` | Refresh external review snapshot for 526019f9 | 2 | +70/-76 | docs |  |
| 15 | `526019f9` | Fix Codex findings rev_pkt_0777/0779/0783 | 3 | +7/-4 | tooling |  |
| 16 | `5fa0f1a2` | Refresh external review snapshot for 66ca79db | 2 | +58/-56 | docs |  |
| 17 | `66ca79db` | devctl session command + gate hardening + reviewer loop + m… | 8 | +479/-64 | tooling |  |
| 18 | `c3e13cdf` | Refresh external review snapshot for 1f927cbf | 1 | +58/-55 | tooling |  |
| 19 | `1f927cbf` | Refresh external review snapshot for 819a88a3 | 2 | +66/-59 | docs |  |
| 20 | `819a88a3` | Typed reviewer-wake convergence + modularization | 9 | +361/-181 | tooling |  |
| 21 | `06665471` | Refresh external review snapshot for 32e5997d | 2 | +50/-54 | docs |  |
| 22 | `32e5997d` | Refresh external review snapshot for e9f6a6b3 | 2 | +72/-70 | docs |  |
| 23 | `e9f6a6b3` | Fix fail-open regression in commit_packet_gate + contract d… | 5 | +448/-74 | tooling |  |
| 24 | `a9f1a42f` | Refresh external review snapshot for d2d91aaf | 2 | +66/-64 | docs |  |
| 25 | `d2d91aaf` | Unify commit-gate caller policy across governed + receipt p… | 8 | +218/-145 | tooling |  |

### Files

| Path | Bundle | +/- |
|---|---|---|
| `bridge.md` | docs | +64/-64 |
| `dev/audits/REVIEW_SNAPSHOT.md` | tooling | +866/-887 |
| `dev/scripts/devctl/cli_parser/entrypoint.py` | tooling | +4/-0 |
| `dev/scripts/devctl/commands/dashboard_builders.py` | tooling | +10/-1 |
| `dev/scripts/devctl/commands/governance/review_snapshot.py` | tooling | +7/-10 |
| `dev/scripts/devctl/commands/governance/session.py` | tooling | +146/-13 |
| `dev/scripts/devctl/commands/governance/session_resume_support.py` | tooling | +9/-0 |
| `dev/scripts/devctl/commands/governance/session_reviewer_loop.py` | tooling | +335/-187 |
| `dev/scripts/devctl/commands/review_channel/_ensure_follow_runtime.py` | tooling | +9/-3 |
| `dev/scripts/devctl/commands/review_channel/reviewer_runtime_snapshot.py` | tooling | +3/-0 |
| `dev/scripts/devctl/commands/vcs/governed_executor_commit_phase.py` | tooling | +7/-10 |
| `dev/scripts/devctl/platform/runtime_state_contract_rows_review.py` | tooling | +2/-0 |
| `dev/scripts/devctl/review_channel/event_projection_context.py` | tooling | +86/-9 |
| `dev/scripts/devctl/review_channel/follow_controller.py` | tooling | +12/-84 |
| `dev/scripts/devctl/review_channel/follow_controller_wake_target.py` | tooling | +152/-0 |
| `dev/scripts/devctl/review_channel/reviewer_follow_packet_guard.py` | tooling | +12/-28 |
| `dev/scripts/devctl/review_channel/reviewer_follow_trigger_gate.py` | tooling | +77/-4 |
| `dev/scripts/devctl/review_channel/reviewer_turn_runner.py` | tooling | +6/-6 |
| `dev/scripts/devctl/runtime/commit_packet_gate.py` | tooling | +85/-24 |
| `dev/scripts/devctl/tests/governance/test_read_only_commands.py` | tooling | +1/-0 |
| `dev/scripts/devctl/tests/review_channel/test_context_injection.py` | tooling | +58/-0 |
| `dev/scripts/devctl/tests/review_channel/test_reviewer_turn_runner.py` | tooling | +22/-0 |
| `dev/scripts/devctl/tests/runtime/test_review_snapshot.py` | tooling | +355/-66 |
| `dev/scripts/devctl/tests/vcs/test_commit_gate.py` | tooling | +5/-2 |
| `dev/scripts/devctl/tests/vcs/test_commit_pending_reviewer_gate.py` | tooling | +151/-13 |
| `dev/scripts/reviewer_loop.sh` | tooling | +94/-0 |

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

### Targeted hints

- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/review_channel/reviewer_follow_trigger_gate.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/review_channel/reviewer_runtime_snapshot.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/review_channel/reviewer_follow_packet_guard.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/runtime/test_review_snapshot.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/governance/review_snapshot.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_commit_phase.py`) — Review contract-level invariants for this file

### Suggested verification commands

- `python3 dev/scripts/devctl.py check --profile ci`
- `python3 dev/scripts/devctl.py probe-report --format md`
- `python3 dev/scripts/devctl.py docs-check --strict-tooling`
- `python3 dev/scripts/devctl.py governance-review --format md`
- `python3 dev/scripts/devctl.py check-router --format md`

## 7. Reasoning — why these changes landed

### Per-commit rationale

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
- **`f402fbe8`** — Refresh external review snapshot for 0f85c5d9
- **`0f85c5d9`** — Dashboard reads FindingBacklog for open count (Phase-0 item #2)
  - Dashboard now prefers quality_signals.finding_backlog.open_finding_count
  - over the raw governance_review.open_finding_count. Falls back to the
  - old source when FindingBacklog isn't loaded.
- **`ad1d5a99`** — Refresh external review snapshot for 8fa4728c
- **`8fa4728c`** — Fix reviewer loop wake: --loop sets remote_control mode (rev_pkt_0794)
  - session --role reviewer --loop now sets DEVCTL_OPERATOR_INTERACTION_MODE=
  - remote_control for the ensure --follow subprocess. The wake controller
  - only relaunches the reviewer when interaction_mode == remote_control.
- **`68acce2b`** — Refresh external review snapshot for 6f8fce71
- **`6f8fce71`** — Wire session reviewer loop into governed ensure --follow runtime
  - Per Codex rev_pkt_0791: the reviewer needs a durable runtime that
  - re-enters the next review cycle, not one-shot chat turns.
- **`a38150a1`** — Refresh external review snapshot for 23c4239a
- **`23c4239a`** — Fix session command blocking (Codex finding rev_pkt_0785): add 30s timeout
- **`598aa8a3`** — Refresh external review snapshot for 526019f9
- **`526019f9`** — Fix Codex findings rev_pkt_0777/0779/0783
  - - session.py: dashboard role maps to 'observer' (rev_pkt_0777)
  - - reviewer_follow_trigger_gate: relaunch-required bypasses review_needed
  -   check instead of being blocked by it (rev_pkt_0779)
- **`5fa0f1a2`** — Refresh external review snapshot for 66ca79db
- **`66ca79db`** — devctl session command + gate hardening + reviewer loop + modularization
  - New command: devctl session --role reviewer/implementer/dashboard
  - - session.py: role dispatcher with --loop and --headless flags
  - - session_reviewer_loop.py: governed Python reviewer loop
- **`c3e13cdf`** — Refresh external review snapshot for 1f927cbf
- **`1f927cbf`** — Refresh external review snapshot for 819a88a3
- **`819a88a3`** — Typed reviewer-wake convergence + modularization
  - Reviewer-wake convergence (MP377-P1-T06, rev_pkt_0734):
  - - reviewer_runtime_snapshot: attaches typed packet_inbox to report
  - - follow_controller: typed coordination gate, typed packet selection
- **`06665471`** — Refresh external review snapshot for 32e5997d
- **`32e5997d`** — Refresh external review snapshot for e9f6a6b3
- **`e9f6a6b3`** — Fix fail-open regression in commit_packet_gate + contract drift
  - Gate fix: check_commit_packet_gate() now distinguishes "no review channel"
  - (allow) from "load failed" (block) with 5-case fail-closed contract.
  - Replaces getattr() with typed AgentAttentionRecord/PacketInboxState.
- **`a9f1a42f`** — Refresh external review snapshot for d2d91aaf
- **`d2d91aaf`** — Unify commit-gate caller policy across governed + receipt paths
  - Both governed_executor_commit_phase and review_snapshot now call
  - check_commit_packet_gate() with identical load→resolve→skip→gate
  - semantics. Fixes rev_pkt_0728 finding: split caller policy where
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

Projection produced by `devctl review-snapshot`. Generation stamp `snap-f501be0740f4` binds this file to HEAD `46679665c8aa`; if they drift, the freshness guard will fail CI. When the latest commit only refreshes this generated snapshot, the guard accepts this file as bound to that commit's parent code state.
