# VoiceTerm — Review Snapshot

> Deterministically generated from typed governance state. Do not edit by hand — rerun `devctl review-snapshot --write`.

## Quick status

- Branch: `feature/governance-quality-sweep`
- HEAD: `27b81fdb2eb2` — Refresh external review snapshot for de639cbc
- Tree hash: `822ee0f3f1b3`
- Generation stamp: `snap-741d06531f60`
- Generated at (UTC): 2026-05-05T04:05:15Z
- Push decision: `await_checkpoint` — staged_index_budget_exceeded
- Reviewer mode: `single_agent` (interaction: `local_terminal`)
- Pipeline state: `n/a` (approval: `n/a`)
- Delta since last snapshot: 24 commits, 90 files, +6410/-1986
- Governance findings: 157 open / 88 fixed / 259 total
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
- HEAD SHA: `27b81fdb2eb23d212fcecd1a46abb6d12804f118`
- HEAD author: Justin Guida
- HEAD timestamp (UTC): 2026-05-04T14:20:48-04:00

## 2. Governance state

### Push decision
- action: `await_checkpoint`
- reason: staged_index_budget_exceeded
- push_eligible_now: False
- worktree_clean: False
- staged_path_count: 98
- unstaged_path_count: 0
- next_step_command: `n/a`
- latest_push_report_state: `post_push_green` (push_completed)
- publication_backlog: recommended
- publication_guidance: 2 local commit(s) waiting for governed push once the current slice is checkpoint-clean.

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

Range: last 24 commits ending at `27b81fdb2eb2`

- commits: 24
- files changed: 90
- insertions: +6410
- deletions: -1986
- bundle classes touched: docs, tooling
- authority surfaces touched: 5 file(s)

### Commits

| # | SHA | Subject | Files | +/- | Bundle | Risk |
|---|---|---|---|---|---|---|
| 1 | `27b81fdb` | Refresh external review snapshot for de639cbc | 2 | +74/-73 | docs |  |
| 2 | `de639cbc` | Add relaunch-loop lifecycle contracts | 31 | +1911/-106 | tooling |  |
| 3 | `afb71fe6` | Refresh external review snapshot for b9406f73 | 2 | +66/-71 | docs |  |
| 4 | `b9406f73` | Refresh external review snapshot for b3ff926d | 2 | +45/-43 | docs |  |
| 5 | `b3ff926d` | Refresh external review snapshot for 299674a0 | 2 | +80/-80 | docs |  |
| 6 | `299674a0` | Add routed guard timeout progress | 39 | +1783/-406 | tooling |  |
| 7 | `ef9db514` | Refresh external review snapshot for da0c9c80 | 2 | +53/-53 | docs |  |
| 8 | `da0c9c80` | Refresh external review snapshot for 9ef66045 | 2 | +46/-44 | docs |  |
| 9 | `9ef66045` | Refresh external review snapshot for faba8791 | 2 | +71/-72 | docs |  |
| 10 | `faba8791` | Classify durable expired packets | 25 | +360/-126 | tooling |  |
| 11 | `7d29dd85` | Refresh external review snapshot for 9e027548 | 2 | +47/-44 | docs |  |
| 12 | `9e027548` | Refresh external review snapshot for 116d5b6e | 2 | +46/-44 | docs |  |
| 13 | `116d5b6e` | Refresh external review snapshot for 6a721e78 | 2 | +65/-70 | docs |  |
| 14 | `6a721e78` | Fix post-push range scoping | 4 | +75/-58 | tooling |  |
| 15 | `759abf90` | Refresh external review snapshot for 3db1597c | 2 | +46/-46 | docs |  |
| 16 | `3db1597c` | Refresh external review snapshot for 04ad16b1 | 2 | +47/-49 | docs |  |
| 17 | `04ad16b1` | Refresh external review snapshot for c66f5f65 | 2 | +67/-66 | docs |  |
| 18 | `c66f5f65` | Shard focused Python tests | 14 | +420/-72 | tooling |  |
| 19 | `639ef536` | Refresh external review snapshot for 12cf2f1d | 2 | +46/-46 | docs |  |
| 20 | `12cf2f1d` | Refresh external review snapshot for bb85d5e0 | 2 | +47/-45 | docs |  |
| 21 | `bb85d5e0` | Refresh external review snapshot for 5a2eb104 | 2 | +69/-74 | docs |  |
| 22 | `5a2eb104` | Show governed commit progress | 16 | +249/-75 | tooling |  |
| 23 | `e382b175` | Phase routed preflight execution | 18 | +646/-170 | tooling |  |
| 24 | `35dc5c13` | Refresh external review snapshot for e7aa7df1 | 2 | +51/-53 | docs |  |

### Files

| Path | Bundle | +/- |
|---|---|---|
| `.gitignore` | tooling | +1/-0 |
| `AGENTS.md` | docs | +24/-13 |
| `bridge.md` | docs | +57/-57 |
| `dev/active/MASTER_PLAN.md` | tooling | +44/-6 |
| `dev/active/ai_governance_platform.md` | tooling | +21/-4 |
| `dev/audits/REVIEW_SNAPSHOT.md` | tooling | +1333/-1344 |
| `dev/config/git_hooks/post-commit-review-snapshot.sh` | tooling | +8/-0 |
| `dev/guides/DEVELOPMENT.md` | docs | +39/-2 |
| `dev/guides/SYSTEM_MAP.md` | docs | +7/-7 |
| `dev/history/ENGINEERING_EVOLUTION.md` | tooling | +185/-1 |
| `dev/scripts/README.md` | tooling | +44/-12 |
| `dev/scripts/checks/compat_matrix/yaml_json_loader.py` | tooling | +2/-0 |
| `dev/scripts/checks/multi_agent_sync/runtime_truth_agent_loop.py` | tooling | +16/-0 |
| `dev/scripts/checks/platform_contract_closure/field_routes_parity_compare.py` | tooling | +1/-2 |
| `dev/scripts/checks/python_analysis/check_python_broad_except.py` | tooling | +21/-2 |
| `dev/scripts/checks/rust_analysis/check_rust_audit_patterns.py` | tooling | +1/-0 |
| `dev/scripts/devctl/bundles/registry.py` | tooling | +0/-3 |
| `dev/scripts/devctl/cli.py` | tooling | +5/-3 |
| `dev/scripts/devctl/cli_parser/entrypoint.py` | tooling | +7/-1 |
| `dev/scripts/devctl/cli_parser/python_tests.py` | tooling | +12/-0 |
| `dev/scripts/devctl/cli_parser/quality.py` | tooling | +18/-0 |
| `dev/scripts/devctl/cli_parser/relaunch_loop.py` | tooling | +80/-0 |
| `dev/scripts/devctl/cli_parser/reporting.py` | tooling | +2/-0 |
| `dev/scripts/devctl/command_runner.py` | tooling | +227/-0 |
| `dev/scripts/devctl/command_runner_process.py` | tooling | +332/-0 |
| `dev/scripts/devctl/command_runner_process_progress.py` | tooling | +58/-0 |
| `dev/scripts/devctl/command_runner_process_tree.py` | tooling | +58/-0 |
| `dev/scripts/devctl/commands/autonomy/swarm.py` | tooling | +2/-0 |
| `dev/scripts/devctl/commands/check/router.py` | tooling | +4/-0 |
| `dev/scripts/devctl/commands/check/router_coverage.py` | tooling | +7/-0 |
| `dev/scripts/devctl/commands/check/router_execution.py` | tooling | +225/-81 |
| `dev/scripts/devctl/commands/check/router_phases.py` | tooling | +49/-0 |
| `dev/scripts/devctl/commands/check/router_plan.py` | tooling | +138/-0 |
| `dev/scripts/devctl/commands/check/router_python_tests.py` | tooling | +21/-2 |
| `dev/scripts/devctl/commands/check/router_render.py` | tooling | +31/-7 |
| `dev/scripts/devctl/commands/check/router_steps.py` | tooling | +58/-0 |
| `dev/scripts/devctl/commands/check/steps.py` | tooling | +3/-1 |
| `dev/scripts/devctl/commands/development/continuation.py` | tooling | +10/-2 |
| `dev/scripts/devctl/commands/development/continuation_commands.py` | tooling | +51/-2 |
| `dev/scripts/devctl/commands/development/orchestration_agent_loop_state.py` | tooling | +28/-2 |
| _50 more files trimmed_ | | |

## 4. Quality signals

### Governance review
- total findings: 259
- open: 157
- fixed: 88
- false positives: 0

Recent findings:
- `dogfood.command.orchestrate-status` — `dev/scripts/devctl/commands/reporting/orchestrate_status.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.orchestrate-watch` — `dev/scripts/devctl/commands/governance/orchestrate_watch.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.integrations-import` — `dev/scripts/devctl/commands/integrations_import.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.governance-export` — `dev/scripts/devctl/commands/governance/export.py` (n/a, verdict=`confirmed_issue`)
- `packet.transition_session_disambiguation` — `dev/scripts/devctl/review_channel/instruction_transitions.py` (critical, verdict=`confirmed_issue`)
- `packet.durable_ingestion_before_ttl` — `dev/scripts/devctl/runtime/packet_carry_forward.py` (critical, verdict=`confirmed_issue`)
- `agent_sync.ambiguity_projection` — `dev/scripts/checks/multi_agent_sync` (high, verdict=`confirmed_issue`)
- `review_channel.command_latency_under_fanout` — `dev/scripts/devctl/commands/review_channel` (high, verdict=`confirmed_issue`)
- `work_board.rows_duplication` — `dev/scripts/devctl/runtime/agent_dispatch_router.py` (high, verdict=`confirmed_issue`)
- `dogfood.command.reports-cleanup` — `dev/scripts/devctl/commands/reports_cleanup.py` (n/a, verdict=`confirmed_issue`)

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

- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_commit_runtime.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/commands/check/test_check_router.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/review_snapshot_refresh.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_commit_phase.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/vcs/test_governed_executor.py`) — Review contract-level invariants for this file
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/platform/runtime_state_contract_rows.py`) — Commit de639cbc changed dev/scripts/devctl/platform/runtime_state_contract_rows.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/relaunch_loop_models.py`) — Commit de639cbc changed dev/scripts/devctl/runtime/relaunch_loop_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/review_channel/packet_outcome_models.py`) — Commit faba8791 changed dev/scripts/devctl/review_channel/packet_outcome_models.py

### Suggested verification commands

- `python3 dev/scripts/devctl.py check --profile ci`
- `python3 dev/scripts/devctl.py probe-report --format md`
- `python3 dev/scripts/devctl.py docs-check --strict-tooling`
- `python3 dev/scripts/devctl.py governance-review --format md`
- `python3 dev/scripts/devctl.py check-router --format md`

## 7. Reasoning — why these changes landed

### Per-commit rationale

- **`27b81fdb`** — Refresh external review snapshot for de639cbc
  - evolution: Fact: the phone/dashboard remote-control path had two authority leaks. The legacy bridge-loop wrapper carried lifecycle behavior and a policy-heavy Claude slash file, while stale `remote_control` signals could keep loca…
- **`de639cbc`** — Add relaunch-loop lifecycle contracts
  - evolution: Fact: the phone/dashboard remote-control path had two authority leaks. The legacy bridge-loop wrapper carried lifecycle behavior and a policy-heavy Claude slash file, while stale `remote_control` signals could keep loca…
- **`afb71fe6`** — Refresh external review snapshot for b9406f73
  - evolution: Fact: the phone/dashboard remote-control path had two authority leaks. The legacy bridge-loop wrapper carried lifecycle behavior and a policy-heavy Claude slash file, while stale `remote_control` signals could keep loca…
- **`b9406f73`** — Refresh external review snapshot for b3ff926d
  - evolution: Fact: the phone/dashboard remote-control path had two authority leaks. The legacy bridge-loop wrapper carried lifecycle behavior and a policy-heavy Claude slash file, while stale `remote_control` signals could keep loca…
- **`b3ff926d`** — Refresh external review snapshot for 299674a0
  - evolution: Fact: the phone/dashboard remote-control path had two authority leaks. The legacy bridge-loop wrapper carried lifecycle behavior and a policy-heavy Claude slash file, while stale `remote_control` signals could keep loca…
- **`299674a0`** — Add routed guard timeout progress
  - evolution: Fact: the phone/dashboard remote-control path had two authority leaks. The legacy bridge-loop wrapper carried lifecycle behavior and a policy-heavy Claude slash file, while stale `remote_control` signals could keep loca…
- **`ef9db514`** — Refresh external review snapshot for da0c9c80
  - evolution: Fact: the phone/dashboard remote-control path had two authority leaks. The legacy bridge-loop wrapper carried lifecycle behavior and a policy-heavy Claude slash file, while stale `remote_control` signals could keep loca…
- **`da0c9c80`** — Refresh external review snapshot for 9ef66045
  - evolution: Fact: the phone/dashboard remote-control path had two authority leaks. The legacy bridge-loop wrapper carried lifecycle behavior and a policy-heavy Claude slash file, while stale `remote_control` signals could keep loca…
- **`9ef66045`** — Refresh external review snapshot for faba8791
  - evolution: Fact: the phone/dashboard remote-control path had two authority leaks. The legacy bridge-loop wrapper carried lifecycle behavior and a policy-heavy Claude slash file, while stale `remote_control` signals could keep loca…
- **`faba8791`** — Classify durable expired packets
  - evolution: Fact: the phone/dashboard remote-control path had two authority leaks. The legacy bridge-loop wrapper carried lifecycle behavior and a policy-heavy Claude slash file, while stale `remote_control` signals could keep loca…
- **`7d29dd85`** — Refresh external review snapshot for 9e027548
  - evolution: Fact: the phone/dashboard remote-control path had two authority leaks. The legacy bridge-loop wrapper carried lifecycle behavior and a policy-heavy Claude slash file, while stale `remote_control` signals could keep loca…
- **`9e027548`** — Refresh external review snapshot for 116d5b6e
  - evolution: Fact: the phone/dashboard remote-control path had two authority leaks. The legacy bridge-loop wrapper carried lifecycle behavior and a policy-heavy Claude slash file, while stale `remote_control` signals could keep loca…
- **`116d5b6e`** — Refresh external review snapshot for 6a721e78
  - evolution: Fact: the phone/dashboard remote-control path had two authority leaks. The legacy bridge-loop wrapper carried lifecycle behavior and a policy-heavy Claude slash file, while stale `remote_control` signals could keep loca…
- **`6a721e78`** — Fix post-push range scoping
  - evolution: Fact: the phone/dashboard remote-control path had two authority leaks. The legacy bridge-loop wrapper carried lifecycle behavior and a policy-heavy Claude slash file, while stale `remote_control` signals could keep loca…
- **`759abf90`** — Refresh external review snapshot for 3db1597c
  - evolution: Fact: the phone/dashboard remote-control path had two authority leaks. The legacy bridge-loop wrapper carried lifecycle behavior and a policy-heavy Claude slash file, while stale `remote_control` signals could keep loca…
- **`3db1597c`** — Refresh external review snapshot for 04ad16b1
  - evolution: Fact: the phone/dashboard remote-control path had two authority leaks. The legacy bridge-loop wrapper carried lifecycle behavior and a policy-heavy Claude slash file, while stale `remote_control` signals could keep loca…
- **`04ad16b1`** — Refresh external review snapshot for c66f5f65
  - evolution: Fact: the phone/dashboard remote-control path had two authority leaks. The legacy bridge-loop wrapper carried lifecycle behavior and a policy-heavy Claude slash file, while stale `remote_control` signals could keep loca…
- **`c66f5f65`** — Shard focused Python tests
  - evolution: Fact: the phone/dashboard remote-control path had two authority leaks. The legacy bridge-loop wrapper carried lifecycle behavior and a policy-heavy Claude slash file, while stale `remote_control` signals could keep loca…
- **`639ef536`** — Refresh external review snapshot for 12cf2f1d
  - evolution: Fact: the phone/dashboard remote-control path had two authority leaks. The legacy bridge-loop wrapper carried lifecycle behavior and a policy-heavy Claude slash file, while stale `remote_control` signals could keep loca…
- **`12cf2f1d`** — Refresh external review snapshot for bb85d5e0
  - evolution: Fact: the phone/dashboard remote-control path had two authority leaks. The legacy bridge-loop wrapper carried lifecycle behavior and a policy-heavy Claude slash file, while stale `remote_control` signals could keep loca…
- **`bb85d5e0`** — Refresh external review snapshot for 5a2eb104
  - evolution: Fact: the phone/dashboard remote-control path had two authority leaks. The legacy bridge-loop wrapper carried lifecycle behavior and a policy-heavy Claude slash file, while stale `remote_control` signals could keep loca…
- **`5a2eb104`** — Show governed commit progress
  - evolution: Fact: the phone/dashboard remote-control path had two authority leaks. The legacy bridge-loop wrapper carried lifecycle behavior and a policy-heavy Claude slash file, while stale `remote_control` signals could keep loca…
- **`e382b175`** — Phase routed preflight execution
  - evolution: Fact: the phone/dashboard remote-control path had two authority leaks. The legacy bridge-loop wrapper carried lifecycle behavior and a policy-heavy Claude slash file, while stale `remote_control` signals could keep loca…
- **`35dc5c13`** — Refresh external review snapshot for e7aa7df1
  - evolution: Fact: the phone/dashboard remote-control path had two authority leaks. The legacy bridge-loop wrapper carried lifecycle behavior and a policy-heavy Claude slash file, while stale `remote_control` signals could keep loca…
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

- open governance findings: 157

### Startup advisories
- checkpoint_before_continue: staged_index_budget_exceeded

### Stale warnings
- Keep editing the current slice.
- Move straight to the governed push path.

### Open gap rows
- **governance_open** (`dev/scripts/devctl/commands/reporting/orchestrate_status.py`): dogfood.command.orchestrate-status: Auto-ingested devctl finalization failure rc=1.
repo_path=/Users/jguida941/testing_upgrade/codex-voice
- **governance_open** (`dev/scripts/devctl/commands/governance/orchestrate_watch.py`): dogfood.command.orchestrate-watch: Auto-ingested devctl finalization failure rc=1.
repo_path=/Users/jguida941/testing_upgrade/codex-voice
- **governance_open** (`dev/scripts/devctl/commands/integrations_import.py`): dogfood.command.integrations-import: Auto-ingested devctl finalization failure rc=1.
repo_path=/Users/jguida941/testing_upgrade/codex-voice
- **governance_open** (`dev/scripts/devctl/commands/governance/export.py`): dogfood.command.governance-export: Auto-ingested devctl finalization failure rc=2.
repo_path=/Users/jguida941/testing_upgrade/codex-voice
- **governance_open** (`dev/scripts/devctl/review_channel/instruction_transitions.py`): packet.transition_session_disambiguation: source_packet_ids=rev_pkt_2691,rev_pkt_2696,rev_pkt_2705; Claude beta finding: transition_packet ack/apply/dismiss paths bypass session disambiguation, allowing cross-session packet actions. Durable owner: MP377-GUARDIR-TRANSITION-DISAMBIGUATION.
- **governance_open** (`dev/scripts/devctl/runtime/packet_carry_forward.py`): packet.durable_ingestion_before_ttl: source_packet_ids=rev_pkt_2691,rev_pkt_2696,rev_pkt_2697,rev_pkt_2699,rev_pkt_2700,rev_pkt_2701,rev_pkt_2702,rev_pkt_2704,rev_pkt_2705; packets are transport/provenance only, so packet-carried work must be promoted into PlanRow/FindingReview/GuardPromotionCandidate/knowledge state before TTL expiry. Durable owner: MP377-GUARDIR-PACKET-DURABLE-INGESTION.
- **governance_open** (`dev/scripts/checks/multi_agent_sync`): agent_sync.ambiguity_projection: source_packet_ids=rev_pkt_2697,rev_pkt_2705; canonical_active_packet_ambiguity can render empty while ambiguity exists, and expired-but-pending split state creates carry-forward debt. Durable owner: MP377-GUARDIR-AGENT-SYNC-AMBIGUITY-CARRYFORWARD.
- **governance_open** (`dev/scripts/devctl/commands/review_channel`): review_channel.command_latency_under_fanout: source_packet_ids=rev_pkt_2704,rev_pkt_2705; review-channel post and startup-context can hang under multi-agent load, tied to process-cleanup and detached sleep pressure. Durable owner: MP377-GUARDIR-FANOUT-COMMAND-HANGS.

---

Projection produced by `devctl review-snapshot`. Generation stamp `snap-741d06531f60` binds this file to HEAD `27b81fdb2eb2`; if they drift, the freshness guard will fail CI. When the latest commit only refreshes this generated snapshot, the guard accepts this file as bound to that commit's parent code state.
