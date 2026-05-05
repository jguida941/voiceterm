# VoiceTerm — Review Snapshot

> Deterministically generated from typed governance state. Do not edit by hand — rerun `devctl review-snapshot --write`.

## Quick status

- Branch: `feature/governance-quality-sweep`
- HEAD: `0492bac5595b` — Refresh external review snapshot for 10364c5f
- Tree hash: `54337009d266`
- Generation stamp: `snap-ce5cf3b92160`
- Generated at (UTC): 2026-05-05T16:02:20Z
- Push decision: `run_devctl_push` — push_preconditions_satisfied
- Reviewer mode: `single_agent` (interaction: `local_terminal`)
- Pipeline state: `n/a` (approval: `n/a`)
- Delta since last snapshot: 24 commits, 170 files, +16599/-2932
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
- HEAD SHA: `0492bac5595b3e7aaae62a503ac7fb257d9097e1`
- HEAD author: Justin Guida
- HEAD timestamp (UTC): 2026-05-05T11:39:17-04:00

## 2. Governance state

### Push decision
- action: `run_devctl_push`
- reason: push_preconditions_satisfied
- push_eligible_now: True
- worktree_clean: True
- staged_path_count: 0
- unstaged_path_count: 0
- next_step_command: `python3 dev/scripts/devctl.py push --execute`
- latest_push_report_state: `blocked` (validation_failed)
- current_push_authorization: `push-auth-20260505T040833598726Z` (valid=False)
- authorized_head_commit: `f5e2e1830745efacc21971413762206eb66d62da`
- publication_backlog: urgent
- publication_guidance: 10 local commit(s) waiting for governed push. Run `python3 dev/scripts/devctl.py push --execute` now.

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

Range: last 24 commits ending at `0492bac5595b`

- commits: 24
- files changed: 170
- insertions: +16599
- deletions: -2932
- bundle classes touched: docs, tooling
- authority surfaces touched: 7 file(s)

### Commits

| # | SHA | Subject | Files | +/- | Bundle | Risk |
|---|---|---|---|---|---|---|
| 1 | `0492bac5` | Refresh external review snapshot for 10364c5f | 2 | +64/-64 | docs |  |
| 2 | `10364c5f` | Refresh projections for rev_pkt_3068+3069+3070 plan handoff… | 4 | +60/-58 | tooling |  |
| 3 | `2e1d341f` | Refresh external review snapshot for d7ce0f7d | 2 | +63/-63 | docs |  |
| 4 | `d7ce0f7d` | Add publication-defer routing and peer attention-window pro… | 27 | +1380/-146 | tooling |  |
| 5 | `9c02b8b2` | Refresh external review snapshot for 1cfa5df2 | 2 | +57/-59 | docs |  |
| 6 | `1cfa5df2` | Refresh external review snapshot for f5e2e183 | 2 | +54/-52 | docs |  |
| 7 | `f5e2e183` | Refresh external review snapshot for ed79cd0e | 2 | +95/-91 | docs |  |
| 8 | `ed79cd0e` | Implement runtime truth remote control pipeline | 100 | +10011/-1014 | tooling |  |
| 9 | `27b81fdb` | Refresh external review snapshot for de639cbc | 2 | +74/-73 | docs |  |
| 10 | `de639cbc` | Add relaunch-loop lifecycle contracts | 31 | +1911/-106 | tooling |  |
| 11 | `afb71fe6` | Refresh external review snapshot for b9406f73 | 2 | +66/-71 | docs |  |
| 12 | `b9406f73` | Refresh external review snapshot for b3ff926d | 2 | +45/-43 | docs |  |
| 13 | `b3ff926d` | Refresh external review snapshot for 299674a0 | 2 | +80/-80 | docs |  |
| 14 | `299674a0` | Add routed guard timeout progress | 39 | +1783/-406 | tooling |  |
| 15 | `ef9db514` | Refresh external review snapshot for da0c9c80 | 2 | +53/-53 | docs |  |
| 16 | `da0c9c80` | Refresh external review snapshot for 9ef66045 | 2 | +46/-44 | docs |  |
| 17 | `9ef66045` | Refresh external review snapshot for faba8791 | 2 | +71/-72 | docs |  |
| 18 | `faba8791` | Classify durable expired packets | 25 | +360/-126 | tooling |  |
| 19 | `7d29dd85` | Refresh external review snapshot for 9e027548 | 2 | +47/-44 | docs |  |
| 20 | `9e027548` | Refresh external review snapshot for 116d5b6e | 2 | +46/-44 | docs |  |
| 21 | `116d5b6e` | Refresh external review snapshot for 6a721e78 | 2 | +65/-70 | docs |  |
| 22 | `6a721e78` | Fix post-push range scoping | 4 | +75/-58 | tooling |  |
| 23 | `759abf90` | Refresh external review snapshot for 3db1597c | 2 | +46/-46 | docs |  |
| 24 | `3db1597c` | Refresh external review snapshot for 04ad16b1 | 2 | +47/-49 | docs |  |

### Files

| Path | Bundle | +/- |
|---|---|---|
| `.claude/commands/typed-remote-control.md` | docs | +56/-0 |
| `.claude/settings.json` | tooling | +51/-0 |
| `.github/workflows/release_preflight.yml` | tooling | +2/-0 |
| `.github/workflows/tooling_control_plane.yml` | tooling | +6/-0 |
| `.gitignore` | tooling | +4/-0 |
| `AGENTS.md` | docs | +16/-8 |
| `bridge.md` | docs | +71/-71 |
| `dev/active/MASTER_PLAN.md` | tooling | +110/-2 |
| `dev/active/ai_governance_platform.md` | tooling | +62/-5 |
| `dev/active/remote_control_runtime.md` | tooling | +37/-1 |
| `dev/audits/REVIEW_SNAPSHOT.md` | tooling | +1414/-1417 |
| `dev/config/devctl_repo_policy.json` | tooling | +50/-0 |
| `dev/config/templates/README.md` | tooling | +7/-0 |
| `dev/config/templates/claude_typed_remote_control_command.template.md` | tooling | +56/-0 |
| `dev/config/templates/remote_control_slash_adapters.template.md` | tooling | +1/-0 |
| `dev/guides/DEVELOPMENT.md` | docs | +88/-14 |
| `dev/guides/SYSTEM_MAP.md` | docs | +13/-10 |
| `dev/history/ENGINEERING_EVOLUTION.md` | tooling | +263/-0 |
| `dev/scripts/README.md` | tooling | +77/-17 |
| `dev/scripts/checks/check_ground_truth_probe_gate.py` | tooling | +11/-0 |
| `dev/scripts/checks/check_memory_not_authority.py` | tooling | +12/-0 |
| `dev/scripts/checks/compat_matrix/yaml_json_loader.py` | tooling | +2/-0 |
| `dev/scripts/checks/ground_truth_probe_gate/__init__.py` | tooling | +2/-0 |
| `dev/scripts/checks/ground_truth_probe_gate/command.py` | tooling | +144/-0 |
| `dev/scripts/checks/memory_authority/__init__.py` | tooling | +1/-0 |
| `dev/scripts/checks/memory_authority/checks.py` | tooling | +132/-0 |
| `dev/scripts/checks/memory_authority/command.py` | tooling | +80/-0 |
| `dev/scripts/checks/platform_contract_closure/field_routes_parity_compare.py` | tooling | +1/-2 |
| `dev/scripts/checks/python_analysis/check_python_broad_except.py` | tooling | +21/-2 |
| `dev/scripts/checks/rust_analysis/check_rust_audit_patterns.py` | tooling | +1/-0 |
| `dev/scripts/devctl/bundles/registry.py` | tooling | +2/-3 |
| `dev/scripts/devctl/cli.py` | tooling | +16/-11 |
| `dev/scripts/devctl/cli_parser/entrypoint.py` | tooling | +11/-1 |
| `dev/scripts/devctl/cli_parser/quality.py` | tooling | +18/-0 |
| `dev/scripts/devctl/cli_parser/relaunch_loop.py` | tooling | +80/-0 |
| `dev/scripts/devctl/cli_parser/remote_control.py` | tooling | +148/-0 |
| `dev/scripts/devctl/cli_parser/reporting.py` | tooling | +2/-0 |
| `dev/scripts/devctl/command_runner.py` | tooling | +227/-0 |
| `dev/scripts/devctl/command_runner_process.py` | tooling | +332/-0 |
| `dev/scripts/devctl/command_runner_process_progress.py` | tooling | +58/-0 |
| _130 more files trimmed_ | | |

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

- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/governance/startup_context.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/runtime/test_startup_context.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/reviewer_runtime_models.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/startup_context.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_commit_runtime.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/commands/check/test_check_router.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/review_snapshot_refresh.py`) — Review contract-level invariants for this file
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/review_state_models.py`) — Commit d7ce0f7d changed dev/scripts/devctl/runtime/review_state_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/remote_control_attachment_models.py`) — Commit ed79cd0e changed dev/scripts/devctl/runtime/remote_control_attachment_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/reviewer_runtime_models.py`) — Commit ed79cd0e changed dev/scripts/devctl/runtime/reviewer_runtime_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/startup_context_models.py`) — Commit ed79cd0e changed dev/scripts/devctl/runtime/startup_context_models.py
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

- **`0492bac5`** — Refresh external review snapshot for 10364c5f
  - evolution: Fact: the remote-control dogfood failure showed a structural AI-agent failure mode. The typed system designed hook/transcript proof channels around `bridge_status` before asking where Claude Code itself stored the statu…
- **`10364c5f`** — Refresh projections for rev_pkt_3068+3069+3070 plan handoff to codex
  - evolution: Fact: the remote-control dogfood failure showed a structural AI-agent failure mode. The typed system designed hook/transcript proof channels around `bridge_status` before asking where Claude Code itself stored the statu…
- **`2e1d341f`** — Refresh external review snapshot for d7ce0f7d
  - evolution: Fact: the remote-control dogfood failure showed a structural AI-agent failure mode. The typed system designed hook/transcript proof channels around `bridge_status` before asking where Claude Code itself stored the statu…
- **`d7ce0f7d`** — Add publication-defer routing and peer attention-window projection
  - evolution: Fact: the remote-control dogfood failure showed a structural AI-agent failure mode. The typed system designed hook/transcript proof channels around `bridge_status` before asking where Claude Code itself stored the statu…
- **`9c02b8b2`** — Refresh external review snapshot for 1cfa5df2
  - evolution: Fact: the remote-control dogfood failure showed a structural AI-agent failure mode. The typed system designed hook/transcript proof channels around `bridge_status` before asking where Claude Code itself stored the statu…
- **`1cfa5df2`** — Refresh external review snapshot for f5e2e183
  - evolution: Fact: the remote-control dogfood failure showed a structural AI-agent failure mode. The typed system designed hook/transcript proof channels around `bridge_status` before asking where Claude Code itself stored the statu…
- **`f5e2e183`** — Refresh external review snapshot for ed79cd0e
  - evolution: Fact: the remote-control dogfood failure showed a structural AI-agent failure mode. The typed system designed hook/transcript proof channels around `bridge_status` before asking where Claude Code itself stored the statu…
- **`ed79cd0e`** — Implement runtime truth remote control pipeline
  - evolution: Fact: the remote-control dogfood failure showed a structural AI-agent failure mode. The typed system designed hook/transcript proof channels around `bridge_status` before asking where Claude Code itself stored the statu…
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
- push_allowed: worktree_clean_and_review_accepted

### Stale warnings
- Stop because nothing remains to push.

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

Projection produced by `devctl review-snapshot`. Generation stamp `snap-ce5cf3b92160` binds this file to HEAD `0492bac5595b`; if they drift, the freshness guard will fail CI. When the latest commit only refreshes this generated snapshot, the guard accepts this file as bound to that commit's parent code state.
