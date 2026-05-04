# VoiceTerm — Review Snapshot

> Deterministically generated from typed governance state. Do not edit by hand — rerun `devctl review-snapshot --write`.

## Quick status

- Branch: `feature/governance-quality-sweep`
- HEAD: `9e027548a020` — Refresh external review snapshot for 116d5b6e
- Tree hash: `e5bed15222e0`
- Generation stamp: `snap-fdde93a7f368`
- Generated at (UTC): 2026-05-04T12:13:42Z
- Push decision: `run_devctl_push` — push_preconditions_satisfied
- Reviewer mode: `single_agent` (interaction: `local_terminal`)
- Pipeline state: `n/a` (approval: `n/a`)
- Delta since last snapshot: 25 commits, 95 files, +5162/-4037
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
- HEAD SHA: `9e027548a0207f7b38309c963c95814992b7c3ed`
- HEAD author: Justin Guida
- HEAD timestamp (UTC): 2026-05-04T08:12:43-04:00

## 2. Governance state

### Push decision
- action: `run_devctl_push`
- reason: push_preconditions_satisfied
- push_eligible_now: True
- worktree_clean: True
- staged_path_count: 0
- unstaged_path_count: 0
- next_step_command: `python3 dev/scripts/devctl.py push --execute`
- latest_push_report_state: `blocked` (push_preflight_running)
- current_push_authorization: `push-auth-20260504T120925322555Z` (valid=True)
- authorized_head_commit: `116d5b6e338bcdc6ac6862246e30b2057e2a0fe0`
- publication_backlog: recommended
- publication_guidance: 3 local commit(s) waiting for governed push. Run `python3 dev/scripts/devctl.py push --execute` now.

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
- advisory: `push_allowed` — worktree_clean_and_review_accepted

## 3. Delta — what changed since the previous snapshot

Range: last 25 commits ending at `9e027548a020`

- commits: 25
- files changed: 95
- insertions: +5162
- deletions: -4037
- bundle classes touched: docs, tooling
- authority surfaces touched: 5 file(s)

### Commits

| # | SHA | Subject | Files | +/- | Bundle | Risk |
|---|---|---|---|---|---|---|
| 1 | `9e027548` | Refresh external review snapshot for 116d5b6e | 2 | +46/-44 | docs |  |
| 2 | `116d5b6e` | Refresh external review snapshot for 6a721e78 | 2 | +65/-70 | docs |  |
| 3 | `6a721e78` | Fix post-push range scoping | 4 | +75/-58 | tooling |  |
| 4 | `759abf90` | Refresh external review snapshot for 3db1597c | 2 | +46/-46 | docs |  |
| 5 | `3db1597c` | Refresh external review snapshot for 04ad16b1 | 2 | +47/-49 | docs |  |
| 6 | `04ad16b1` | Refresh external review snapshot for c66f5f65 | 2 | +67/-66 | docs |  |
| 7 | `c66f5f65` | Shard focused Python tests | 14 | +420/-72 | tooling |  |
| 8 | `639ef536` | Refresh external review snapshot for 12cf2f1d | 2 | +46/-46 | docs |  |
| 9 | `12cf2f1d` | Refresh external review snapshot for bb85d5e0 | 2 | +47/-45 | docs |  |
| 10 | `bb85d5e0` | Refresh external review snapshot for 5a2eb104 | 2 | +69/-74 | docs |  |
| 11 | `5a2eb104` | Show governed commit progress | 16 | +249/-75 | tooling |  |
| 12 | `e382b175` | Phase routed preflight execution | 18 | +646/-170 | tooling |  |
| 13 | `35dc5c13` | Refresh external review snapshot for e7aa7df1 | 2 | +51/-53 | docs |  |
| 14 | `e7aa7df1` | Refresh external review snapshot for 6d8004fc | 2 | +52/-50 | docs |  |
| 15 | `6d8004fc` | Refresh policy-owned generated surfaces for b6a926fc | 1 | +1/-1 | docs |  |
| 16 | `b6a926fc` | Refresh external review snapshot for d3cf4e73 | 2 | +99/-86 | docs |  |
| 17 | `d3cf4e73` | Harden packet attention and routed guard coverage | 72 | +2469/-2618 | tooling |  |
| 18 | `2a3e3731` | Refresh external review snapshot for 764252dc | 2 | +43/-43 | docs |  |
| 19 | `764252dc` | Refresh external review snapshot for bc821042 | 2 | +48/-45 | docs |  |
| 20 | `bc821042` | Refresh external review snapshot for c2cf00e6 | 2 | +68/-67 | docs |  |
| 21 | `c2cf00e6` | Preserve priority action-request current session | 14 | +347/-92 | tooling |  |
| 22 | `71258903` | Refresh external review snapshot for c3b8b148 | 2 | +43/-43 | docs |  |
| 23 | `c3b8b148` | Refresh external review snapshot for 6d9e177d | 2 | +43/-45 | docs |  |
| 24 | `6d9e177d` | Refresh external review snapshot for 26a94370 | 2 | +66/-72 | docs |  |
| 25 | `26a94370` | Absorb projection drift to clear governed-push gate per cod… | 3 | +9/-7 | tooling |  |

### Files

| Path | Bundle | +/- |
|---|---|---|
| `.github/workflows/release_preflight.yml` | tooling | +9/-2 |
| `.github/workflows/tooling_control_plane.yml` | tooling | +38/-5 |
| `AGENTS.md` | docs | +66/-13 |
| `bridge.md` | docs | +73/-73 |
| `dev/active/MASTER_PLAN.md` | tooling | +82/-4 |
| `dev/active/ai_governance_platform.md` | tooling | +49/-5 |
| `dev/audits/REVIEW_SNAPSHOT.md` | tooling | +1243/-1239 |
| `dev/config/git_hooks/post-commit-review-snapshot.sh` | tooling | +8/-0 |
| `dev/guides/DEVELOPMENT.md` | docs | +28/-7 |
| `dev/guides/SYSTEM_MAP.md` | docs | +5/-5 |
| `dev/history/ENGINEERING_EVOLUTION.md` | tooling | +284/-28 |
| `dev/scripts/README.md` | tooling | +67/-51 |
| `dev/scripts/checks/check_guard_enforcement_inventory.py` | tooling | +0/-4 |
| `dev/scripts/checks/multi_agent_sync/runtime_truth_agent_loop.py` | tooling | +16/-0 |
| `dev/scripts/devctl/bundles/registry.py` | tooling | +15/-3 |
| `dev/scripts/devctl/cli_parser/python_tests.py` | tooling | +12/-0 |
| `dev/scripts/devctl/cli_parser/quality.py` | tooling | +17/-0 |
| `dev/scripts/devctl/commands/check/router.py` | tooling | +48/-104 |
| `dev/scripts/devctl/commands/check/router_coverage.py` | tooling | +163/-0 |
| `dev/scripts/devctl/commands/check/router_execution.py` | tooling | +237/-80 |
| `dev/scripts/devctl/commands/check/router_phases.py` | tooling | +49/-0 |
| `dev/scripts/devctl/commands/check/router_plan.py` | tooling | +138/-0 |
| `dev/scripts/devctl/commands/check/router_python_tests.py` | tooling | +21/-2 |
| `dev/scripts/devctl/commands/check/router_range.py` | tooling | +52/-0 |
| `dev/scripts/devctl/commands/check/router_render.py` | tooling | +50/-1 |
| `dev/scripts/devctl/commands/check/router_steps.py` | tooling | +54/-0 |
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
| `dev/scripts/devctl/commands/python_test_runner/command.py` | tooling | +197/-7 |
| `dev/scripts/devctl/commands/review_channel/event_handler.py` | tooling | +1/-0 |
| `dev/scripts/devctl/commands/review_channel/event_post_wake.py` | tooling | +25/-283 |
| _55 more files trimmed_ | | |

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

- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/commands/check/test_check_router.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_commit_phase.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/vcs/test_governed_executor.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/governance/startup_context.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/runtime/test_startup_context.py`) — Review contract-level invariants for this file
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

- **`9e027548`** — Refresh external review snapshot for 116d5b6e
  - evolution: Fact: live dogfooding showed the packet-delivery path was still carrying process semantics. Even after earlier exact-session fixes, packet post/follow helpers and their docs/tests still treated "packet arrived" as a pos…
- **`116d5b6e`** — Refresh external review snapshot for 6a721e78
  - evolution: Fact: live dogfooding showed the packet-delivery path was still carrying process semantics. Even after earlier exact-session fixes, packet post/follow helpers and their docs/tests still treated "packet arrived" as a pos…
- **`6a721e78`** — Fix post-push range scoping
  - evolution: Fact: live dogfooding showed the packet-delivery path was still carrying process semantics. Even after earlier exact-session fixes, packet post/follow helpers and their docs/tests still treated "packet arrived" as a pos…
- **`759abf90`** — Refresh external review snapshot for 3db1597c
  - evolution: Fact: live dogfooding showed the packet-delivery path was still carrying process semantics. Even after earlier exact-session fixes, packet post/follow helpers and their docs/tests still treated "packet arrived" as a pos…
- **`3db1597c`** — Refresh external review snapshot for 04ad16b1
  - evolution: Fact: live dogfooding showed the packet-delivery path was still carrying process semantics. Even after earlier exact-session fixes, packet post/follow helpers and their docs/tests still treated "packet arrived" as a pos…
- **`04ad16b1`** — Refresh external review snapshot for c66f5f65
  - evolution: Fact: live dogfooding showed the packet-delivery path was still carrying process semantics. Even after earlier exact-session fixes, packet post/follow helpers and their docs/tests still treated "packet arrived" as a pos…
- **`c66f5f65`** — Shard focused Python tests
  - evolution: Fact: live dogfooding showed the packet-delivery path was still carrying process semantics. Even after earlier exact-session fixes, packet post/follow helpers and their docs/tests still treated "packet arrived" as a pos…
- **`639ef536`** — Refresh external review snapshot for 12cf2f1d
  - evolution: Fact: live dogfooding showed the packet-delivery path was still carrying process semantics. Even after earlier exact-session fixes, packet post/follow helpers and their docs/tests still treated "packet arrived" as a pos…
- **`12cf2f1d`** — Refresh external review snapshot for bb85d5e0
  - evolution: Fact: live dogfooding showed the packet-delivery path was still carrying process semantics. Even after earlier exact-session fixes, packet post/follow helpers and their docs/tests still treated "packet arrived" as a pos…
- **`bb85d5e0`** — Refresh external review snapshot for 5a2eb104
  - evolution: Fact: live dogfooding showed the packet-delivery path was still carrying process semantics. Even after earlier exact-session fixes, packet post/follow helpers and their docs/tests still treated "packet arrived" as a pos…
- **`5a2eb104`** — Show governed commit progress
  - evolution: Fact: live dogfooding showed the packet-delivery path was still carrying process semantics. Even after earlier exact-session fixes, packet post/follow helpers and their docs/tests still treated "packet arrived" as a pos…
- **`e382b175`** — Phase routed preflight execution
  - evolution: Fact: live dogfooding showed the packet-delivery path was still carrying process semantics. Even after earlier exact-session fixes, packet post/follow helpers and their docs/tests still treated "packet arrived" as a pos…
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
- push_allowed: worktree_clean_and_review_accepted

### Stale warnings
- Stop because nothing remains to push.

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

Projection produced by `devctl review-snapshot`. Generation stamp `snap-fdde93a7f368` binds this file to HEAD `9e027548a020`; if they drift, the freshness guard will fail CI. When the latest commit only refreshes this generated snapshot, the guard accepts this file as bound to that commit's parent code state.
