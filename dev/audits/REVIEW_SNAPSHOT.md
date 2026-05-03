# VoiceTerm — Review Snapshot

> Deterministically generated from typed governance state. Do not edit by hand — rerun `devctl review-snapshot --write`.

## Quick status

- Branch: `feature/governance-quality-sweep`
- HEAD: `1096b88d77d4` — Implement codex's rev_pkt_2922 (Finding Y) + rev_pkt_2923 (T22AN-L) dispatched fixes
- Tree hash: `7ce246cf9bb0`
- Generation stamp: `snap-02d3881ca4b5`
- Generated at (UTC): 2026-05-03T23:27:10Z
- Push decision: `await_checkpoint` — staged_index_present
- Reviewer mode: `single_agent` (interaction: `local_terminal`)
- Pipeline state: `n/a` (approval: `n/a`)
- Delta since last snapshot: 24 commits, 66 files, +4183/-1265
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
- HEAD SHA: `1096b88d77d4e4af0585a289a4b3bc561ad2b27e`
- HEAD author: Justin Guida
- HEAD timestamp (UTC): 2026-05-03T18:57:44-04:00

## 2. Governance state

### Push decision
- action: `await_checkpoint`
- reason: staged_index_present
- push_eligible_now: False
- worktree_clean: False
- staged_path_count: 10
- unstaged_path_count: 0
- next_step_command: `n/a`
- latest_push_report: `dev/reports/push/latest.json`
- latest_push_report_state: `blocked` (push_preflight_running)
- publication_backlog: recommended
- publication_guidance: 4 local commit(s) waiting for governed push once the current slice is checkpoint-clean.

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
- advisory: `checkpoint_before_continue` — dirty_after_local_checkpoint

## 3. Delta — what changed since the previous snapshot

Range: last 24 commits ending at `1096b88d77d4`

- commits: 24
- files changed: 66
- insertions: +4183
- deletions: -1265
- bundle classes touched: tooling, docs
- authority surfaces touched: 4 file(s)

### Commits

| # | SHA | Subject | Files | +/- | Bundle | Risk |
|---|---|---|---|---|---|---|
| 1 | `1096b88d` | Implement codex's rev_pkt_2922 (Finding Y) + rev_pkt_2923 (… | 7 | +196/-16 | tooling |  |
| 2 | `1761e564` | Absorb projection drift to clear startup gate before termin… | 3 | +7/-5 | tooling |  |
| 3 | `0bba7ed5` | Absorb projection drift to clear bridge guard ACK mismatch… | 3 | +23/-12 | tooling |  |
| 4 | `14945bd5` | Tighten remote_control wake routing per codex rev_pkt_2904 | 3 | +122/-1 | tooling |  |
| 5 | `8c61c403` | Refresh external review snapshot for 8da8cee3 | 2 | +44/-44 | docs |  |
| 6 | `8da8cee3` | Refresh external review snapshot for 1bf050cb | 1 | +44/-44 | tooling |  |
| 7 | `1bf050cb` | Refresh policy-owned generated surfaces for 66480513 | 1 | +1/-1 | docs |  |
| 8 | `66480513` | Refresh external review snapshot for b5a3728c | 2 | +70/-69 | docs |  |
| 9 | `b5a3728c` | Phase 1.5: tighten remote_control wake/launch scope per rev… | 9 | +241/-67 | tooling |  |
| 10 | `63171e06` | Refresh external review snapshot for 689b31b2 | 2 | +60/-61 | docs |  |
| 11 | `689b31b2` | Unblock remote-control codex launch (Findings D + F minimal… | 8 | +274/-59 | tooling |  |
| 12 | `19b907d1` | Refresh external review snapshot for ebc0732d | 2 | +62/-62 | docs |  |
| 13 | `ebc0732d` | Suppress packet-post auto-spawn in remote_control mode (Fin… | 6 | +148/-76 | tooling |  |
| 14 | `d876071a` | Refresh external review snapshot for 8b102bf9 | 2 | +45/-45 | docs |  |
| 15 | `8b102bf9` | Refresh external review snapshot for 72269c1b | 1 | +45/-42 | tooling |  |
| 16 | `72269c1b` | Refresh external review snapshot for 08e13d94 | 2 | +58/-61 | docs |  |
| 17 | `08e13d94` | Document test-python command inventory | 6 | +68/-55 | tooling |  |
| 18 | `33543b22` | Refresh external review snapshot for ad0f4ed0 | 2 | +45/-45 | docs |  |
| 19 | `ad0f4ed0` | Refresh external review snapshot for f963b75c | 1 | +47/-44 | tooling |  |
| 20 | `f963b75c` | Refresh external review snapshot for b089cc14 | 2 | +55/-58 | docs |  |
| 21 | `b089cc14` | Surface governed push in session orientation | 3 | +144/-49 | tooling |  |
| 22 | `22ba3616` | Refresh external review snapshot for be072632 | 2 | +79/-79 | docs |  |
| 23 | `be072632` | Automate typed session orientation | 25 | +1259/-168 | tooling |  |
| 24 | `1ea62a24` | Bound Python test execution policy | 36 | +1046/-102 | tooling |  |

### Files

| Path | Bundle | +/- |
|---|---|---|
| `.github/workflows/release_preflight.yml` | tooling | +1/-0 |
| `.github/workflows/tooling_control_plane.yml` | tooling | +7/-0 |
| `AGENTS.md` | docs | +26/-6 |
| `README.md` | docs | +1/-1 |
| `app/operator_console/AGENTS.md` | docs | +1/-1 |
| `bridge.md` | docs | +95/-94 |
| `conftest.py` | tooling | +128/-0 |
| `dev/active/MASTER_PLAN.md` | tooling | +38/-1 |
| `dev/active/ai_governance_platform.md` | tooling | +24/-0 |
| `dev/audits/REVIEW_SNAPSHOT.md` | tooling | +1041/-1020 |
| `dev/guides/DEVELOPMENT.md` | docs | +26/-9 |
| `dev/guides/SYSTEM_MAP.md` | docs | +6/-6 |
| `dev/history/ENGINEERING_EVOLUTION.md` | tooling | +100/-1 |
| `dev/scripts/README.md` | tooling | +32/-10 |
| `dev/scripts/checks/check_pytest_runtime_policy.py` | tooling | +12/-0 |
| `dev/scripts/checks/pytest_runtime_policy/__init__.py` | tooling | +1/-0 |
| `dev/scripts/checks/pytest_runtime_policy/command.py` | tooling | +109/-0 |
| `dev/scripts/devctl/bundles/registry.py` | tooling | +1/-5 |
| `dev/scripts/devctl/cli.py` | tooling | +4/-0 |
| `dev/scripts/devctl/cli_parser/artifact_suppression.py` | tooling | +8/-0 |
| `dev/scripts/devctl/cli_parser/entrypoint.py` | tooling | +4/-0 |
| `dev/scripts/devctl/cli_parser/python_tests.py` | tooling | +59/-0 |
| `dev/scripts/devctl/commands/check/router.py` | tooling | +5/-1 |
| `dev/scripts/devctl/commands/check/router_python_tests.py` | tooling | +172/-0 |
| `dev/scripts/devctl/commands/check/router_support.py` | tooling | +2/-0 |
| `dev/scripts/devctl/commands/governance/session.py` | tooling | +48/-79 |
| `dev/scripts/devctl/commands/governance/session_orientation.py` | tooling | +22/-0 |
| `dev/scripts/devctl/commands/governance/session_orientation_models.py` | tooling | +64/-0 |
| `dev/scripts/devctl/commands/governance/session_orientation_render.py` | tooling | +87/-0 |
| `dev/scripts/devctl/commands/governance/session_orientation_runner.py` | tooling | +248/-0 |
| `dev/scripts/devctl/commands/governance/session_orientation_summary.py` | tooling | +331/-0 |
| `dev/scripts/devctl/commands/governance/session_resume_render.py` | tooling | +2/-1 |
| `dev/scripts/devctl/commands/listing.py` | tooling | +2/-0 |
| `dev/scripts/devctl/commands/python_test_runner/__init__.py` | tooling | +1/-0 |
| `dev/scripts/devctl/commands/python_test_runner/command.py` | tooling | +74/-0 |
| `dev/scripts/devctl/commands/python_tests.py` | tooling | +13/-0 |
| `dev/scripts/devctl/commands/review_channel/bridge_action_support.py` | tooling | +12/-4 |
| `dev/scripts/devctl/commands/review_channel/event_post_wake.py` | tooling | +11/-1 |
| `dev/scripts/devctl/commands/review_channel/review_only_scope.py` | tooling | +24/-0 |
| `dev/scripts/devctl/governance/script_catalog_registry.py` | tooling | +1/-0 |
| _26 more files trimmed_ | | |

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
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/commands/check/test_check_router.py`) — Review contract-level invariants for this file
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/commands/governance/session_orientation_models.py`) — Commit be072632 changed dev/scripts/devctl/commands/governance/session_orientation_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/platform/surface_state_contract_rows.py`) — Commit be072632 changed dev/scripts/devctl/platform/surface_state_contract_rows.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/python_test_contract.py`) — Commit 1ea62a24 changed dev/scripts/devctl/runtime/python_test_contract.py

### Suggested verification commands

- `python3 dev/scripts/devctl.py check --profile ci`
- `python3 dev/scripts/devctl.py probe-report --format md`
- `python3 dev/scripts/devctl.py docs-check --strict-tooling`
- `python3 dev/scripts/devctl.py governance-review --format md`
- `python3 dev/scripts/devctl.py check-router --format md`

## 7. Reasoning — why these changes landed

### Per-commit rationale

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
- **`b089cc14`** — Surface governed push in session orientation
  - evolution: Fact: A pytest-runaway dogfood failure showed that broad raw pytest commands could still be selected by static bundles or copied into agent workflows, burning local sessions without a repo-owned timeout/target contract.…
- **`22ba3616`** — Refresh external review snapshot for be072632
  - evolution: Fact: A pytest-runaway dogfood failure showed that broad raw pytest commands could still be selected by static bundles or copied into agent workflows, burning local sessions without a repo-owned timeout/target contract.…
- **`be072632`** — Automate typed session orientation
  - evolution: Fact: A pytest-runaway dogfood failure showed that broad raw pytest commands could still be selected by static bundles or copied into agent workflows, burning local sessions without a repo-owned timeout/target contract.…
- **`1ea62a24`** — Bound Python test execution policy
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
- checkpoint_before_continue: dirty_after_local_checkpoint

### Stale warnings
- Relaunch the reviewer loop immediately.

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

Projection produced by `devctl review-snapshot`. Generation stamp `snap-02d3881ca4b5` binds this file to HEAD `1096b88d77d4`; if they drift, the freshness guard will fail CI. When the latest commit only refreshes this generated snapshot, the guard accepts this file as bound to that commit's parent code state.
