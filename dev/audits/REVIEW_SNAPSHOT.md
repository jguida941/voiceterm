# VoiceTerm — Review Snapshot

> Deterministically generated from typed governance state. Do not edit by hand — rerun `devctl review-snapshot --write`.

## Quick status

- Branch: `feature/governance-quality-sweep`
- HEAD: `35dc5c13b955` — Refresh external review snapshot for e7aa7df1
- Tree hash: `dbbccbb9fcc9`
- Generation stamp: `snap-a2c69acb82a3`
- Generated at (UTC): 2026-05-04T04:59:56Z
- Push decision: `await_checkpoint` — staged_index_budget_exceeded
- Reviewer mode: `single_agent` (interaction: `local_terminal`)
- Pipeline state: `n/a` (approval: `n/a`)
- Delta since last snapshot: 24 commits, 87 files, +4470/-3696
- Governance findings: 154 open / 88 fixed / 256 total
- Probe hints: 0 total across 0 files scanned

## 1. Identity

- Repository: **VoiceTerm**
- Product thesis: This is the product thesis for the governance stack in this repository.
Absorb these four commitments before engaging with SOP, guard, routing,
or plan detail — they explain why the process exists.

This repo builds a portable AI governance platform proven through one
production client (VoiceTerm, a Rust voice-first terminal overlay for AI
CLIs). The product thesis is that executable local control — guards,
probes, typed actions, deterministic policy resolution — is what m...
- Remote: `https://github.com/jguida941/voiceterm.git`
- Default branch: `master`
- Current branch: `feature/governance-quality-sweep`
- HEAD SHA: `35dc5c13b955bdf02e0a469680eb42a9af10f11e`
- HEAD author: Justin Guida
- HEAD timestamp (UTC): 2026-05-04T00:26:51-04:00

## 2. Governance state

### Push decision
- action: `await_checkpoint`
- reason: staged_index_budget_exceeded
- push_eligible_now: False
- worktree_clean: False
- staged_path_count: 17
- unstaged_path_count: 0
- next_step_command: `n/a`
- latest_push_report_state: `blocked` (validation_failed)
- current_push_authorization: `push-auth-20260504T042056758132Z` (valid=False)
- authorized_head_commit: `b6a926fc721b3cc440f5853f1f8a4bb5c84b191b`
- publication_backlog: urgent
- publication_guidance: 19 local commit(s) waiting for governed push once the current slice is checkpoint-clean.

### Reviewer runtime
- reviewer_mode: `single_agent`
- reviewer_freshness: unknown
- reviewer_publish_clear: True
- interaction_mode: `local_terminal`

### Remote commit pipeline
- state: `n/a`
- approval_state: `n/a`

### Work intake
- active plan: **AI Governance Platform Plan**
- plan path: `dev/active/ai_governance_platform.md`
- active MP scope: `MP-377`
- advisory: `checkpoint_before_continue` — staged_index_budget_exceeded
- checkpoint_required: **yes**

## 3. Delta — what changed since the previous snapshot

Range: last 24 commits ending at `35dc5c13b955`

- commits: 24
- files changed: 87
- insertions: +4470
- deletions: -3696
- bundle classes touched: docs, tooling
- authority surfaces touched: 4 file(s)

### Commits

| # | SHA | Subject | Files | +/- | Bundle | Risk |
|---|---|---|---|---|---|---|
| 1 | `35dc5c13` | Refresh external review snapshot for e7aa7df1 | 2 | +51/-53 | docs |  |
| 2 | `e7aa7df1` | Refresh external review snapshot for 6d8004fc | 2 | +52/-50 | docs |  |
| 3 | `6d8004fc` | Refresh policy-owned generated surfaces for b6a926fc | 1 | +1/-1 | docs |  |
| 4 | `b6a926fc` | Refresh external review snapshot for d3cf4e73 | 2 | +99/-86 | docs |  |
| 5 | `d3cf4e73` | Harden packet attention and routed guard coverage | 72 | +2469/-2618 | tooling |  |
| 6 | `2a3e3731` | Refresh external review snapshot for 764252dc | 2 | +43/-43 | docs |  |
| 7 | `764252dc` | Refresh external review snapshot for bc821042 | 2 | +48/-45 | docs |  |
| 8 | `bc821042` | Refresh external review snapshot for c2cf00e6 | 2 | +68/-67 | docs |  |
| 9 | `c2cf00e6` | Preserve priority action-request current session | 14 | +347/-92 | tooling |  |
| 10 | `71258903` | Refresh external review snapshot for c3b8b148 | 2 | +43/-43 | docs |  |
| 11 | `c3b8b148` | Refresh external review snapshot for 6d9e177d | 2 | +43/-45 | docs |  |
| 12 | `6d9e177d` | Refresh external review snapshot for 26a94370 | 2 | +66/-72 | docs |  |
| 13 | `26a94370` | Absorb projection drift to clear governed-push gate per cod… | 3 | +9/-7 | tooling |  |
| 14 | `d1b3377b` | Refresh external review snapshot for dae2c50e | 2 | +86/-88 | docs |  |
| 15 | `dae2c50e` | Tighten operator notice sync guard | 12 | +297/-127 | tooling |  |
| 16 | `1096b88d` | Implement codex's rev_pkt_2922 (Finding Y) + rev_pkt_2923 (… | 7 | +196/-16 | tooling |  |
| 17 | `1761e564` | Absorb projection drift to clear startup gate before termin… | 3 | +7/-5 | tooling |  |
| 18 | `0bba7ed5` | Absorb projection drift to clear bridge guard ACK mismatch… | 3 | +23/-12 | tooling |  |
| 19 | `14945bd5` | Tighten remote_control wake routing per codex rev_pkt_2904 | 3 | +122/-1 | tooling |  |
| 20 | `8c61c403` | Refresh external review snapshot for 8da8cee3 | 2 | +44/-44 | docs |  |
| 21 | `8da8cee3` | Refresh external review snapshot for 1bf050cb | 1 | +44/-44 | tooling |  |
| 22 | `1bf050cb` | Refresh policy-owned generated surfaces for 66480513 | 1 | +1/-1 | docs |  |
| 23 | `66480513` | Refresh external review snapshot for b5a3728c | 2 | +70/-69 | docs |  |
| 24 | `b5a3728c` | Phase 1.5: tighten remote_control wake/launch scope per rev… | 9 | +241/-67 | tooling |  |

### Files

| Path | Bundle | +/- |
|---|---|---|
| `.github/workflows/release_preflight.yml` | tooling | +9/-2 |
| `.github/workflows/tooling_control_plane.yml` | tooling | +38/-5 |
| `AGENTS.md` | docs | +51/-5 |
| `bridge.md` | docs | +117/-117 |
| `dev/active/MASTER_PLAN.md` | tooling | +76/-0 |
| `dev/active/ai_governance_platform.md` | tooling | +47/-3 |
| `dev/audits/REVIEW_SNAPSHOT.md` | tooling | +959/-951 |
| `dev/guides/DEVELOPMENT.md` | docs | +24/-8 |
| `dev/guides/SYSTEM_MAP.md` | docs | +4/-4 |
| `dev/history/ENGINEERING_EVOLUTION.md` | tooling | +293/-27 |
| `dev/scripts/README.md` | tooling | +57/-46 |
| `dev/scripts/checks/check_guard_enforcement_inventory.py` | tooling | +0/-4 |
| `dev/scripts/checks/multi_agent_sync/runtime_truth.py` | tooling | +11/-1 |
| `dev/scripts/checks/multi_agent_sync/runtime_truth_agent_loop.py` | tooling | +61/-4 |
| `dev/scripts/devctl/bundles/registry.py` | tooling | +15/-0 |
| `dev/scripts/devctl/cli_parser/quality.py` | tooling | +17/-0 |
| `dev/scripts/devctl/commands/check/router.py` | tooling | +46/-104 |
| `dev/scripts/devctl/commands/check/router_coverage.py` | tooling | +163/-0 |
| `dev/scripts/devctl/commands/check/router_execution.py` | tooling | +182/-0 |
| `dev/scripts/devctl/commands/check/router_range.py` | tooling | +52/-0 |
| `dev/scripts/devctl/commands/check/router_render.py` | tooling | +38/-0 |
| `dev/scripts/devctl/commands/development/attention_commands.py` | tooling | +46/-0 |
| `dev/scripts/devctl/commands/development/collaboration_models.py` | tooling | +1/-0 |
| `dev/scripts/devctl/commands/development/models.py` | tooling | +1/-0 |
| `dev/scripts/devctl/commands/development/packet_attention.py` | tooling | +1/-0 |
| `dev/scripts/devctl/commands/development/peer_mind.py` | tooling | +5/-3 |
| `dev/scripts/devctl/commands/development/peer_mind_commands.py` | tooling | +1/-1 |
| `dev/scripts/devctl/commands/development/peer_mind_wake.py` | tooling | +13/-3 |
| `dev/scripts/devctl/commands/development/render.py` | tooling | +6/-1 |
| `dev/scripts/devctl/commands/development/render_collaboration.py` | tooling | +2/-1 |
| `dev/scripts/devctl/commands/development/report.py` | tooling | +15/-1 |
| `dev/scripts/devctl/commands/governance/startup_context.py` | tooling | +7/-3 |
| `dev/scripts/devctl/commands/review_channel/bridge_action_support.py` | tooling | +12/-4 |
| `dev/scripts/devctl/commands/review_channel/event_handler.py` | tooling | +1/-0 |
| `dev/scripts/devctl/commands/review_channel/event_post_wake.py` | tooling | +36/-284 |
| `dev/scripts/devctl/commands/review_channel/event_post_wake_reports.py` | tooling | +30/-0 |
| `dev/scripts/devctl/commands/review_channel/review_only_scope.py` | tooling | +24/-0 |
| `dev/scripts/devctl/commands/review_channel/status_runtime_projection.py` | tooling | +25/-0 |
| `dev/scripts/devctl/governance/push_routing.py` | tooling | +1/-0 |
| `dev/scripts/devctl/review_channel/agent_loop_decision_projection.py` | tooling | +26/-0 |
| _47 more files trimmed_ | | |

## 4. Quality signals

### Governance review
- total findings: 256
- open: 154
- fixed: 88
- false positives: 0

Recent findings:
- `dogfood.command.agent-loop` — `dev/scripts/devctl/commands/reporting/claude_loop.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.agent-mind` — `dev/scripts/devctl/commands/agent_mind/command.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.governance-bootstrap` — `dev/scripts/devctl/commands/governance/bootstrap.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.orchestrate-status` — `dev/scripts/devctl/commands/reporting/orchestrate_status.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.orchestrate-watch` — `dev/scripts/devctl/commands/governance/orchestrate_watch.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.integrations-import` — `dev/scripts/devctl/commands/integrations_import.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.governance-export` — `dev/scripts/devctl/commands/governance/export.py` (n/a, verdict=`confirmed_issue`)
- `packet.transition_session_disambiguation` — `dev/scripts/devctl/review_channel/instruction_transitions.py` (critical, verdict=`confirmed_issue`)
- `packet.durable_ingestion_before_ttl` — `dev/scripts/devctl/runtime/packet_carry_forward.py` (critical, verdict=`confirmed_issue`)
- `agent_sync.ambiguity_projection` — `dev/scripts/checks/multi_agent_sync` (high, verdict=`confirmed_issue`)

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
| `RemoteCommitPipelineContract` | `governance_runtime` | `dev.scripts.devctl.runtime.remote_commit_pipeline_models:RemoteCommitPipelineContract` | snapshot_id, state |
| `ReviewState` | `governance_runtime` | `dev.scripts.devctl.runtime.review_state_models:ReviewState` | snapshot_id, bridge |

### Key documents

- `AGENTS.md`
- `dev/active/MASTER_PLAN.md`
- `dev/active/INDEX.md`
- `dev/guides/AI_GOVERNANCE_PLATFORM.md`

## 6. Reviewer hints — please verify

### Targeted hints

- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/governance/startup_context.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/commands/check/test_check_router.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/runtime/test_startup_context.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/review_channel/bridge_action_support.py`) — Review contract-level invariants for this file
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/commands/development/collaboration_models.py`) — Commit d3cf4e73 changed dev/scripts/devctl/commands/development/collaboration_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/startup_context_models.py`) — Commit d3cf4e73 changed dev/scripts/devctl/runtime/startup_context_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/work_intake_models.py`) — Commit d3cf4e73 changed dev/scripts/devctl/runtime/work_intake_models.py

### Suggested verification commands

- `python3 dev/scripts/devctl.py check --profile ci`
- `python3 dev/scripts/devctl.py probe-report --format md`
- `python3 dev/scripts/devctl.py docs-check --strict-tooling`
- `python3 dev/scripts/devctl.py governance-review --format md`
- `python3 dev/scripts/devctl.py check-router --format md`

## 7. Reasoning — why these changes landed

### Per-commit rationale

- **`35dc5c13`** — Refresh external review snapshot for e7aa7df1
  - evolution: Fact: live dogfooding showed the packet-delivery path was still carrying process semantics. Even after earlier exact-session fixes, packet post/follow helpers and their docs/tests still treated "packet arrived" as a pos…
- **`e7aa7df1`** — Refresh external review snapshot for 6d8004fc
  - evolution: Fact: live dogfooding showed the packet-delivery path was still carrying process semantics. Even after earlier exact-session fixes, packet post/follow helpers and their docs/tests still treated "packet arrived" as a pos…
- **`6d8004fc`** — Refresh policy-owned generated surfaces for b6a926fc
  - evolution: Fact: live dogfooding showed the packet-delivery path was still carrying process semantics. Even after earlier exact-session fixes, packet post/follow helpers and their docs/tests still treated "packet arrived" as a pos…
- **`b6a926fc`** — Refresh external review snapshot for d3cf4e73
  - evolution: Fact: live dogfooding showed the packet-delivery path was still carrying process semantics. Even after earlier exact-session fixes, packet post/follow helpers and their docs/tests still treated "packet arrived" as a pos…
- **`d3cf4e73`** — Harden packet attention and routed guard coverage
  - evolution: Fact: live dogfooding showed the packet-delivery path was still carrying process semantics. Even after earlier exact-session fixes, packet post/follow helpers and their docs/tests still treated "packet arrived" as a pos…
- **`2a3e3731`** — Refresh external review snapshot for 764252dc
  - evolution: Fact: The final T22AN-L/Finding Y stage-commit handoff packet selected a queue-priority `action_request`, but event-backed `current_session` projection still preferred the stale reviewer checkpoint and then let implemen…
- **`764252dc`** — Refresh external review snapshot for bc821042
  - evolution: Fact: The final T22AN-L/Finding Y stage-commit handoff packet selected a queue-priority `action_request`, but event-backed `current_session` projection still preferred the stale reviewer checkpoint and then let implemen…
- **`bc821042`** — Refresh external review snapshot for c2cf00e6
  - evolution: Fact: The final T22AN-L/Finding Y stage-commit handoff packet selected a queue-priority `action_request`, but event-backed `current_session` projection still preferred the stale reviewer checkpoint and then let implemen…
- **`c2cf00e6`** — Preserve priority action-request current session
  - evolution: Fact: The final T22AN-L/Finding Y stage-commit handoff packet selected a queue-priority `action_request`, but event-backed `current_session` projection still preferred the stale reviewer checkpoint and then let implemen…
- **`71258903`** — Refresh external review snapshot for c3b8b148
  - evolution: Fact: The final T22AN-L/Finding Y stage-commit handoff packet selected a queue-priority `action_request`, but event-backed `current_session` projection still preferred the stale reviewer checkpoint and then let implemen…
- **`c3b8b148`** — Refresh external review snapshot for 6d9e177d
  - evolution: Fact: The final T22AN-L/Finding Y stage-commit handoff packet selected a queue-priority `action_request`, but event-backed `current_session` projection still preferred the stale reviewer checkpoint and then let implemen…
- **`6d9e177d`** — Refresh external review snapshot for 26a94370
  - evolution: Fact: The final T22AN-L/Finding Y stage-commit handoff packet selected a queue-priority `action_request`, but event-backed `current_session` projection still preferred the stale reviewer checkpoint and then let implemen…
- **`26a94370`** — Absorb projection drift to clear governed-push gate per codex rev_pkt_2929
  - Codex shipped dae2c50e (multi_agent_sync runtime_truth fix) and emitted rev_pkt_2929
  - action_request requesting stage_commit_pipeline at HEAD d1b3377b. Bundle.tooling/check-router
  - passed; codex confirmed governed checkpoint recorded. Push was not executed because the typed
  - evolution: Fact: The final T22AN-L/Finding Y stage-commit handoff packet selected a queue-priority `action_request`, but event-backed `current_session` projection still preferred the stale reviewer checkpoint and then let implemen…
- **`d1b3377b`** — Refresh external review snapshot for dae2c50e
  - evolution: Fact: The final T22AN-L/Finding Y stage-commit handoff packet selected a queue-priority `action_request`, but event-backed `current_session` projection still preferred the stale reviewer checkpoint and then let implemen…
- **`dae2c50e`** — Tighten operator notice sync guard
  - evolution: Fact: The final T22AN-L/Finding Y stage-commit handoff packet selected a queue-priority `action_request`, but event-backed `current_session` projection still preferred the stale reviewer checkpoint and then let implemen…
- **`1096b88d`** — Implement codex's rev_pkt_2922 (Finding Y) + rev_pkt_2923 (T22AN-L) dispatched fixes
  - Operator-authorized 22:55Z: claude implements per codex's typed dispatch (codex picked the slices via architectural review at 22:17Z; codex itself was reviewer-only and could not edit; claude executes per codex's spec).
  - evolution: Fact: The final T22AN-L/Finding Y stage-commit handoff packet selected a queue-priority `action_request`, but event-backed `current_session` projection still preferred the stale reviewer checkpoint and then let implemen…
- **`1761e564`** — Absorb projection drift to clear startup gate before terminal-app launch
  - evolution: Fact: The final T22AN-L/Finding Y stage-commit handoff packet selected a queue-priority `action_request`, but event-backed `current_session` projection still preferred the stale reviewer checkpoint and then let implemen…
- **`0bba7ed5`** — Absorb projection drift to clear bridge guard ACK mismatch + unblock codex relaunch
  - evolution: Fact: The final T22AN-L/Finding Y stage-commit handoff packet selected a queue-priority `action_request`, but event-backed `current_session` projection still preferred the stale reviewer checkpoint and then let implemen…
- **`14945bd5`** — Tighten remote_control wake routing per codex rev_pkt_2904
  - Codex (live as reviewer at 20:13Z) reviewed Phase 1.5 and found that agent_wake_dispatch.py:62 immediately routed unscoped codex packets to maybe_wake_reviewer_fn (legacy reviewer wake) BEFORE the remote_control attention-only guard in _wake_via_relaunch could fire. This defeats the rev_pkt_2892 fix and could spawn a fresh codex conductor from packet post.
  - evolution: Fact: The final T22AN-L/Finding Y stage-commit handoff packet selected a queue-priority `action_request`, but event-backed `current_session` projection still preferred the stale reviewer checkpoint and then let implemen…
- **`8c61c403`** — Refresh external review snapshot for 8da8cee3
  - evolution: Fact: The final T22AN-L/Finding Y stage-commit handoff packet selected a queue-priority `action_request`, but event-backed `current_session` projection still preferred the stale reviewer checkpoint and then let implemen…
- **`8da8cee3`** — Refresh external review snapshot for 1bf050cb
  - evolution: Fact: The final T22AN-L/Finding Y stage-commit handoff packet selected a queue-priority `action_request`, but event-backed `current_session` projection still preferred the stale reviewer checkpoint and then let implemen…
- **`1bf050cb`** — Refresh policy-owned generated surfaces for 66480513
  - evolution: Fact: The final T22AN-L/Finding Y stage-commit handoff packet selected a queue-priority `action_request`, but event-backed `current_session` projection still preferred the stale reviewer checkpoint and then let implemen…
- **`66480513`** — Refresh external review snapshot for b5a3728c
  - evolution: Fact: The final T22AN-L/Finding Y stage-commit handoff packet selected a queue-priority `action_request`, but event-backed `current_session` projection still preferred the stale reviewer checkpoint and then let implemen…
- **`b5a3728c`** — Phase 1.5: tighten remote_control wake/launch scope per rev_pkt_2892/2893
  - Operator-authorized raw bypass 2026-05-03T19:25Z (per feedback_raw_bypass_when_guards_falsely_block).
  - evolution: Fact: The final T22AN-L/Finding Y stage-commit handoff packet selected a queue-priority `action_request`, but event-backed `current_session` projection still preferred the stale reviewer checkpoint and then let implemen…
### Active MP scope (from MASTER_PLAN.md)

- contract slice for MP-355 plus the temporary markdown-swarm operating mode
- `dev/active/autonomous_governance_loop_v2.md` MP-377): headless
- `dev/active/review_probes.md` is the review-probe execution spec; implementation tasks stay in this file under `MP-368..MP-375`.
- companion under `MP-376`, not a second main product plan; implementation
- `dev/active/code_shape_expansion.md` is the research/calibration companion for future code-shape additions under `MP-378`; promotion into implementation still flows through `dev/active/review_probes.md` once Phase 5b ev…
- 2026-04-18 `MP-399` governed commit staged-index preservation in `MP-377`
- 2026-04-18 `MP-410` devctl root package-layout relief in `MP-377` scope:
- 2026-04-18 `MP-398` push preflight staged-index exclusion in `MP-377`
- 2026-04-18 `MP-388` consolidation archive pass in `MP-377` scope:
- 2026-04-18 `MP-389` semantic plan-loader core in `MP-377` scope:

## 8. Known gaps and open items

- open governance findings: 154

### Startup advisories
- checkpoint_before_continue: staged_index_budget_exceeded

### Stale warnings
- Keep editing the current slice.
- Move straight to the governed push path.

### Open gap rows
- **governance_open** (`dev/scripts/devctl/commands/reporting/claude_loop.py`): dogfood.command.agent-loop: Auto-ingested devctl finalization failure rc=1.
repo_path=/Users/jguida941/testing_upgrade/codex-voice
- **governance_open** (`dev/scripts/devctl/commands/agent_mind/command.py`): dogfood.command.agent-mind: Auto-ingested devctl finalization failure rc=1.
repo_path=/Users/jguida941/testing_upgrade/codex-voice
- **governance_open** (`dev/scripts/devctl/commands/governance/bootstrap.py`): dogfood.command.governance-bootstrap: Auto-ingested devctl finalization failure rc=2.
repo_path=/Users/jguida941/testing_upgrade/codex-voice
- **governance_open** (`dev/scripts/devctl/commands/reporting/orchestrate_status.py`): dogfood.command.orchestrate-status: Auto-ingested devctl finalization failure rc=1.
repo_path=/Users/jguida941/testing_upgrade/codex-voice
- **governance_open** (`dev/scripts/devctl/commands/governance/orchestrate_watch.py`): dogfood.command.orchestrate-watch: Auto-ingested devctl finalization failure rc=1.
repo_path=/Users/jguida941/testing_upgrade/codex-voice
- **governance_open** (`dev/scripts/devctl/commands/integrations_import.py`): dogfood.command.integrations-import: Auto-ingested devctl finalization failure rc=1.
repo_path=/Users/jguida941/testing_upgrade/codex-voice
- **governance_open** (`dev/scripts/devctl/commands/governance/export.py`): dogfood.command.governance-export: Auto-ingested devctl finalization failure rc=2.
repo_path=/Users/jguida941/testing_upgrade/codex-voice
- **governance_open** (`dev/scripts/devctl/review_channel/instruction_transitions.py`): packet.transition_session_disambiguation: source_packet_ids=rev_pkt_2691,rev_pkt_2696,rev_pkt_2705; Claude beta finding: transition_packet ack/apply/dismiss paths bypass session disambiguation, allowing cross-session packet actions. Durable owner: MP377-GUARDIR-TRANSITION-DISAMBIGUATION.

---

Projection produced by `devctl review-snapshot`. Generation stamp `snap-a2c69acb82a3` binds this file to HEAD `35dc5c13b955`; if they drift, the freshness guard will fail CI. When the latest commit only refreshes this generated snapshot, the guard accepts this file as bound to that commit's parent code state.
