# VoiceTerm — Review Snapshot

> Deterministically generated from typed governance state. Do not edit by hand — rerun `devctl review-snapshot --write`.

## Quick status

- Branch: `feature/governance-quality-sweep`
- HEAD: `6d9e177d995d` — Refresh external review snapshot for 26a94370
- Tree hash: `c3eda7be8da8`
- Generation stamp: `snap-31ce140d4b1a`
- Generated at (UTC): 2026-05-04T00:00:31Z
- Push decision: `run_devctl_push` — push_preconditions_satisfied
- Reviewer mode: `single_agent` (interaction: `single_agent`)
- Pipeline state: `n/a` (approval: `n/a`)
- Delta since last snapshot: 24 commits, 29 files, +2113/-1161
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
- HEAD SHA: `6d9e177d995d5d12abdff42803931fb3d18653b1`
- HEAD author: Justin Guida
- HEAD timestamp (UTC): 2026-05-03T19:58:27-04:00

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
- latest_push_report_state: `blocked` (push_preflight_running)
- current_push_authorization: `push-auth-20260503T232946774021Z` (valid=False)
- authorized_head_commit: `d1b3377bd278d6b826942b130811b307179fdce4`
- approved_target_identity: `tree-receipt-20260503T232946774021Z:122864b8c3ddd03141504a39b40a2d93ede335d4`
- publication_backlog: urgent
- publication_guidance: 8 local commit(s) waiting for governed push. Run `python3 dev/scripts/devctl.py push --execute` now.

### Reviewer runtime
- reviewer_mode: `single_agent`
- reviewer_freshness: unknown
- reviewer_publish_clear: True
- interaction_mode: `single_agent`

### Remote commit pipeline
- state: `n/a`
- approval_state: `n/a`

### Work intake
- active plan: **AI Governance Platform Plan**
- plan path: `dev/active/ai_governance_platform.md`
- active MP scope: `MP-377`
- advisory: `push_allowed` — worktree_clean_and_review_accepted

## 3. Delta — what changed since the previous snapshot

Range: last 24 commits ending at `6d9e177d995d`

- commits: 24
- files changed: 29
- insertions: +2113
- deletions: -1161
- bundle classes touched: docs, tooling
- authority surfaces touched: 3 file(s)

### Commits

| # | SHA | Subject | Files | +/- | Bundle | Risk |
|---|---|---|---|---|---|---|
| 1 | `6d9e177d` | Refresh external review snapshot for 26a94370 | 2 | +66/-72 | docs |  |
| 2 | `26a94370` | Absorb projection drift to clear governed-push gate per cod… | 3 | +9/-7 | tooling |  |
| 3 | `d1b3377b` | Refresh external review snapshot for dae2c50e | 2 | +86/-88 | docs |  |
| 4 | `dae2c50e` | Tighten operator notice sync guard | 12 | +297/-127 | tooling |  |
| 5 | `1096b88d` | Implement codex's rev_pkt_2922 (Finding Y) + rev_pkt_2923 (… | 7 | +196/-16 | tooling |  |
| 6 | `1761e564` | Absorb projection drift to clear startup gate before termin… | 3 | +7/-5 | tooling |  |
| 7 | `0bba7ed5` | Absorb projection drift to clear bridge guard ACK mismatch… | 3 | +23/-12 | tooling |  |
| 8 | `14945bd5` | Tighten remote_control wake routing per codex rev_pkt_2904 | 3 | +122/-1 | tooling |  |
| 9 | `8c61c403` | Refresh external review snapshot for 8da8cee3 | 2 | +44/-44 | docs |  |
| 10 | `8da8cee3` | Refresh external review snapshot for 1bf050cb | 1 | +44/-44 | tooling |  |
| 11 | `1bf050cb` | Refresh policy-owned generated surfaces for 66480513 | 1 | +1/-1 | docs |  |
| 12 | `66480513` | Refresh external review snapshot for b5a3728c | 2 | +70/-69 | docs |  |
| 13 | `b5a3728c` | Phase 1.5: tighten remote_control wake/launch scope per rev… | 9 | +241/-67 | tooling |  |
| 14 | `63171e06` | Refresh external review snapshot for 689b31b2 | 2 | +60/-61 | docs |  |
| 15 | `689b31b2` | Unblock remote-control codex launch (Findings D + F minimal… | 8 | +274/-59 | tooling |  |
| 16 | `19b907d1` | Refresh external review snapshot for ebc0732d | 2 | +62/-62 | docs |  |
| 17 | `ebc0732d` | Suppress packet-post auto-spawn in remote_control mode (Fin… | 6 | +148/-76 | tooling |  |
| 18 | `d876071a` | Refresh external review snapshot for 8b102bf9 | 2 | +45/-45 | docs |  |
| 19 | `8b102bf9` | Refresh external review snapshot for 72269c1b | 1 | +45/-42 | tooling |  |
| 20 | `72269c1b` | Refresh external review snapshot for 08e13d94 | 2 | +58/-61 | docs |  |
| 21 | `08e13d94` | Document test-python command inventory | 6 | +68/-55 | tooling |  |
| 22 | `33543b22` | Refresh external review snapshot for ad0f4ed0 | 2 | +45/-45 | docs |  |
| 23 | `ad0f4ed0` | Refresh external review snapshot for f963b75c | 1 | +47/-44 | tooling |  |
| 24 | `f963b75c` | Refresh external review snapshot for b089cc14 | 2 | +55/-58 | docs |  |

### Files

| Path | Bundle | +/- |
|---|---|---|
| `AGENTS.md` | docs | +4/-1 |
| `bridge.md` | docs | +124/-124 |
| `dev/active/MASTER_PLAN.md` | tooling | +27/-1 |
| `dev/audits/REVIEW_SNAPSHOT.md` | tooling | +965/-971 |
| `dev/guides/DEVELOPMENT.md` | docs | +9/-2 |
| `dev/guides/SYSTEM_MAP.md` | docs | +1/-1 |
| `dev/history/ENGINEERING_EVOLUTION.md` | tooling | +67/-1 |
| `dev/scripts/README.md` | tooling | +12/-5 |
| `dev/scripts/checks/multi_agent_sync/runtime_truth.py` | tooling | +11/-1 |
| `dev/scripts/checks/multi_agent_sync/runtime_truth_agent_loop.py` | tooling | +61/-4 |
| `dev/scripts/devctl/commands/review_channel/bridge_action_support.py` | tooling | +12/-4 |
| `dev/scripts/devctl/commands/review_channel/event_post_wake.py` | tooling | +11/-1 |
| `dev/scripts/devctl/commands/review_channel/review_only_scope.py` | tooling | +24/-0 |
| `dev/scripts/devctl/review_channel/agent_wake_dispatch.py` | tooling | +64/-0 |
| `dev/scripts/devctl/review_channel/current_session_attention.py` | tooling | +27/-0 |
| `dev/scripts/devctl/review_channel/current_session_projection.py` | tooling | +7/-2 |
| `dev/scripts/devctl/review_channel/event_projection_assembly.py` | tooling | +17/-6 |
| `dev/scripts/devctl/review_channel/event_projection_current_session.py` | tooling | +17/-6 |
| `dev/scripts/devctl/review_channel/launch_script.py` | tooling | +36/-1 |
| `dev/scripts/devctl/review_channel/launch_topology.py` | tooling | +15/-2 |
| `dev/scripts/devctl/runtime/startup_gate.py` | tooling | +18/-1 |
| `dev/scripts/devctl/tests/checks/test_check_multi_agent_sync_runtime_truth.py` | tooling | +63/-0 |
| `dev/scripts/devctl/tests/review_channel/test_current_session_projection.py` | tooling | +79/-0 |
| `dev/scripts/devctl/tests/review_channel/test_event_post_wake.py` | tooling | +106/-25 |
| `dev/scripts/devctl/tests/review_channel/test_follow_controller_reviewer_wake.py` | tooling | +119/-0 |
| `dev/scripts/devctl/tests/review_channel/test_launch_script.py` | tooling | +108/-0 |
| `dev/scripts/devctl/tests/review_channel/test_launch_topology.py` | tooling | +34/-0 |
| `dev/scripts/devctl/tests/runtime/test_startup_gate.py` | tooling | +52/-2 |
| `dev/state/plan_index.jsonl` | tooling | +23/-0 |

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

- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/review_channel/bridge_action_support.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/startup_gate.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/runtime/test_startup_gate.py`) — Review contract-level invariants for this file

### Suggested verification commands

- `python3 dev/scripts/devctl.py check --profile ci`
- `python3 dev/scripts/devctl.py probe-report --format md`
- `python3 dev/scripts/devctl.py docs-check --strict-tooling`
- `python3 dev/scripts/devctl.py governance-review --format md`
- `python3 dev/scripts/devctl.py check-router --format md`

## 7. Reasoning — why these changes landed

### Per-commit rationale

- **`6d9e177d`** — Refresh external review snapshot for 26a94370
  - evolution: Fact: A pytest-runaway dogfood failure showed that broad raw pytest commands could still be selected by static bundles or copied into agent workflows, burning local sessions without a repo-owned timeout/target contract.…
- **`26a94370`** — Absorb projection drift to clear governed-push gate per codex rev_pkt_2929
  - Codex shipped dae2c50e (multi_agent_sync runtime_truth fix) and emitted rev_pkt_2929
  - action_request requesting stage_commit_pipeline at HEAD d1b3377b. Bundle.tooling/check-router
  - passed; codex confirmed governed checkpoint recorded. Push was not executed because the typed
  - evolution: Fact: A pytest-runaway dogfood failure showed that broad raw pytest commands could still be selected by static bundles or copied into agent workflows, burning local sessions without a repo-owned timeout/target contract.…
- **`d1b3377b`** — Refresh external review snapshot for dae2c50e
  - evolution: Fact: A pytest-runaway dogfood failure showed that broad raw pytest commands could still be selected by static bundles or copied into agent workflows, burning local sessions without a repo-owned timeout/target contract.…
- **`dae2c50e`** — Tighten operator notice sync guard
  - evolution: Fact: A pytest-runaway dogfood failure showed that broad raw pytest commands could still be selected by static bundles or copied into agent workflows, burning local sessions without a repo-owned timeout/target contract.…
- **`1096b88d`** — Implement codex's rev_pkt_2922 (Finding Y) + rev_pkt_2923 (T22AN-L) dispatched fixes
  - Operator-authorized 22:55Z: claude implements per codex's typed dispatch (codex picked the slices via architectural review at 22:17Z; codex itself was reviewer-only and could not edit; claude executes per codex's spec).
  - evolution: Fact: A pytest-runaway dogfood failure showed that broad raw pytest commands could still be selected by static bundles or copied into agent workflows, burning local sessions without a repo-owned timeout/target contract.…
- **`1761e564`** — Absorb projection drift to clear startup gate before terminal-app launch
  - evolution: Fact: A pytest-runaway dogfood failure showed that broad raw pytest commands could still be selected by static bundles or copied into agent workflows, burning local sessions without a repo-owned timeout/target contract.…
- **`0bba7ed5`** — Absorb projection drift to clear bridge guard ACK mismatch + unblock codex relaunch
  - evolution: Fact: A pytest-runaway dogfood failure showed that broad raw pytest commands could still be selected by static bundles or copied into agent workflows, burning local sessions without a repo-owned timeout/target contract.…
- **`14945bd5`** — Tighten remote_control wake routing per codex rev_pkt_2904
  - Codex (live as reviewer at 20:13Z) reviewed Phase 1.5 and found that agent_wake_dispatch.py:62 immediately routed unscoped codex packets to maybe_wake_reviewer_fn (legacy reviewer wake) BEFORE the remote_control attention-only guard in _wake_via_relaunch could fire. This defeats the rev_pkt_2892 fix and could spawn a fresh codex conductor from packet post.
  - evolution: Fact: A pytest-runaway dogfood failure showed that broad raw pytest commands could still be selected by static bundles or copied into agent workflows, burning local sessions without a repo-owned timeout/target contract.…
- **`8c61c403`** — Refresh external review snapshot for 8da8cee3
  - evolution: Fact: A pytest-runaway dogfood failure showed that broad raw pytest commands could still be selected by static bundles or copied into agent workflows, burning local sessions without a repo-owned timeout/target contract.…
- **`8da8cee3`** — Refresh external review snapshot for 1bf050cb
  - evolution: Fact: A pytest-runaway dogfood failure showed that broad raw pytest commands could still be selected by static bundles or copied into agent workflows, burning local sessions without a repo-owned timeout/target contract.…
- **`1bf050cb`** — Refresh policy-owned generated surfaces for 66480513
  - evolution: Fact: A pytest-runaway dogfood failure showed that broad raw pytest commands could still be selected by static bundles or copied into agent workflows, burning local sessions without a repo-owned timeout/target contract.…
- **`66480513`** — Refresh external review snapshot for b5a3728c
  - evolution: Fact: A pytest-runaway dogfood failure showed that broad raw pytest commands could still be selected by static bundles or copied into agent workflows, burning local sessions without a repo-owned timeout/target contract.…
- **`b5a3728c`** — Phase 1.5: tighten remote_control wake/launch scope per rev_pkt_2892/2893
  - Operator-authorized raw bypass 2026-05-03T19:25Z (per feedback_raw_bypass_when_guards_falsely_block).
  - evolution: Fact: A pytest-runaway dogfood failure showed that broad raw pytest commands could still be selected by static bundles or copied into agent workflows, burning local sessions without a repo-owned timeout/target contract.…
- **`63171e06`** — Refresh external review snapshot for 689b31b2
  - evolution: Fact: A pytest-runaway dogfood failure showed that broad raw pytest commands could still be selected by static bundles or copied into agent workflows, burning local sessions without a repo-owned timeout/target contract.…
- **`689b31b2`** — Unblock remote-control codex launch (Findings D + F minimal fixes)
  - evolution: Fact: A pytest-runaway dogfood failure showed that broad raw pytest commands could still be selected by static bundles or copied into agent workflows, burning local sessions without a repo-owned timeout/target contract.…
- **`19b907d1`** — Refresh external review snapshot for ebc0732d
  - evolution: Fact: A pytest-runaway dogfood failure showed that broad raw pytest commands could still be selected by static bundles or copied into agent workflows, burning local sessions without a repo-owned timeout/target contract.…
- **`ebc0732d`** — Suppress packet-post auto-spawn in remote_control mode (Finding W from rev_pkt_2886)
  - evolution: Fact: A pytest-runaway dogfood failure showed that broad raw pytest commands could still be selected by static bundles or copied into agent workflows, burning local sessions without a repo-owned timeout/target contract.…
- **`d876071a`** — Refresh external review snapshot for 8b102bf9
  - evolution: Fact: A pytest-runaway dogfood failure showed that broad raw pytest commands could still be selected by static bundles or copied into agent workflows, burning local sessions without a repo-owned timeout/target contract.…
- **`8b102bf9`** — Refresh external review snapshot for 72269c1b
  - evolution: Fact: A pytest-runaway dogfood failure showed that broad raw pytest commands could still be selected by static bundles or copied into agent workflows, burning local sessions without a repo-owned timeout/target contract.…
- **`72269c1b`** — Refresh external review snapshot for 08e13d94
  - evolution: Fact: A pytest-runaway dogfood failure showed that broad raw pytest commands could still be selected by static bundles or copied into agent workflows, burning local sessions without a repo-owned timeout/target contract.…
- **`08e13d94`** — Document test-python command inventory
  - evolution: Fact: A pytest-runaway dogfood failure showed that broad raw pytest commands could still be selected by static bundles or copied into agent workflows, burning local sessions without a repo-owned timeout/target contract.…
- **`33543b22`** — Refresh external review snapshot for ad0f4ed0
  - evolution: Fact: A pytest-runaway dogfood failure showed that broad raw pytest commands could still be selected by static bundles or copied into agent workflows, burning local sessions without a repo-owned timeout/target contract.…
- **`ad0f4ed0`** — Refresh external review snapshot for f963b75c
  - evolution: Fact: A pytest-runaway dogfood failure showed that broad raw pytest commands could still be selected by static bundles or copied into agent workflows, burning local sessions without a repo-owned timeout/target contract.…
- **`f963b75c`** — Refresh external review snapshot for b089cc14
  - evolution: Fact: A pytest-runaway dogfood failure showed that broad raw pytest commands could still be selected by static bundles or copied into agent workflows, burning local sessions without a repo-owned timeout/target contract.…
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

Projection produced by `devctl review-snapshot`. Generation stamp `snap-31ce140d4b1a` binds this file to HEAD `6d9e177d995d`; if they drift, the freshness guard will fail CI. When the latest commit only refreshes this generated snapshot, the guard accepts this file as bound to that commit's parent code state.
