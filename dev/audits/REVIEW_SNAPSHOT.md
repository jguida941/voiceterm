# VoiceTerm — Review Snapshot

> Deterministically generated from typed governance state. Do not edit by hand — rerun `devctl review-snapshot --write`.

## Quick status

- Branch: `feature/governance-quality-sweep`
- HEAD: `1ea62a2412d5` — Bound Python test execution policy
- Tree hash: `8e42df75c505`
- Generation stamp: `snap-7ae84b747227`
- Generated at (UTC): 2026-05-03T14:54:25Z
- Push decision: `await_checkpoint` — staged_index_budget_exceeded
- Reviewer mode: `single_agent` (interaction: `local_terminal`)
- Pipeline state: `n/a` (approval: `n/a`)
- Delta since last snapshot: 24 commits, 52 files, +2816/-1471
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
- HEAD SHA: `1ea62a2412d5b02a14444ea09957508327e8ff1a`
- HEAD author: Justin Guida
- HEAD timestamp (UTC): 2026-05-03T09:54:19-04:00

## 2. Governance state

### Push decision
- action: `await_checkpoint`
- reason: staged_index_budget_exceeded
- push_eligible_now: False
- worktree_clean: False
- staged_path_count: 23
- unstaged_path_count: 0
- next_step_command: `n/a`
- latest_push_report: `dev/reports/push/latest.json`
- latest_push_report_state: `post_push_green` (push_completed)
- publication_backlog: queued
- publication_guidance: 1 local commit(s) waiting for governed push once the current slice is checkpoint-clean.

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

Range: last 24 commits ending at `1ea62a2412d5`

- commits: 24
- files changed: 52
- insertions: +2816
- deletions: -1471
- bundle classes touched: tooling, docs
- authority surfaces touched: 2 file(s)

### Commits

| # | SHA | Subject | Files | +/- | Bundle | Risk |
|---|---|---|---|---|---|---|
| 1 | `1ea62a24` | Bound Python test execution policy | 36 | +1046/-102 | tooling |  |
| 2 | `b7278dd4` | Refresh external review snapshot for 961d2e71 | 2 | +45/-45 | docs |  |
| 3 | `961d2e71` | Refresh external review snapshot for bf37dd06 | 1 | +52/-48 | tooling |  |
| 4 | `bf37dd06` | Refresh policy-owned generated surfaces for 4906ad50 | 1 | +1/-1 | docs |  |
| 5 | `4906ad50` | Refresh external review snapshot for 772a0ce7 | 2 | +60/-55 | docs |  |
| 6 | `772a0ce7` | Treat finding backlog as advisory in session resume | 5 | +247/-148 | tooling |  |
| 7 | `2662a44f` | Refresh external review snapshot for f67eded6 | 2 | +45/-45 | docs |  |
| 8 | `f67eded6` | Refresh external review snapshot for 2096395c | 1 | +46/-43 | tooling |  |
| 9 | `2096395c` | Refresh external review snapshot for bcf72a35 | 2 | +60/-56 | docs |  |
| 10 | `bcf72a35` | Fix idle review-channel status readiness | 8 | +246/-71 | tooling |  |
| 11 | `b3e303b7` | Refresh external review snapshot for 2ff46d1c | 2 | +44/-44 | docs |  |
| 12 | `2ff46d1c` | Refresh external review snapshot for fa2ca61c | 1 | +45/-42 | tooling |  |
| 13 | `fa2ca61c` | Refresh external review snapshot for 9b6cc0d0 | 2 | +65/-58 | docs |  |
| 14 | `9b6cc0d0` | Allow pending-publish pipeline authorization refresh | 6 | +191/-58 | tooling |  |
| 15 | `7cb7ba19` | Refresh external review snapshot for fde85cea | 2 | +50/-55 | docs |  |
| 16 | `fde85cea` | Refresh external review snapshot for d80d603a | 2 | +83/-115 | docs |  |
| 17 | `d80d603a` | Refresh external review snapshot for a1a0468d | 2 | +57/-58 | docs |  |
| 18 | `a1a0468d` | Refresh external review snapshot for de294ab4 | 2 | +69/-67 | docs |  |
| 19 | `de294ab4` | Refresh external review snapshot for 37eb2d78 | 2 | +63/-67 | docs |  |
| 20 | `37eb2d78` | Refresh external review snapshot for cc513241 | 2 | +54/-53 | docs |  |
| 21 | `cc513241` | Refresh external review snapshot for f5d534ad | 2 | +49/-49 | docs |  |
| 22 | `f5d534ad` | Refresh external review snapshot for 1ad2844d | 2 | +53/-50 | docs |  |
| 23 | `1ad2844d` | Refresh external review snapshot for 330a82e6 | 2 | +78/-83 | docs |  |
| 24 | `330a82e6` | Align review-channel launch dry-run test with visible policy | 2 | +67/-58 | tooling |  |

### Files

| Path | Bundle | +/- |
|---|---|---|
| `.github/workflows/release_preflight.yml` | tooling | +1/-0 |
| `.github/workflows/tooling_control_plane.yml` | tooling | +7/-0 |
| `AGENTS.md` | docs | +5/-1 |
| `README.md` | docs | +1/-1 |
| `app/operator_console/AGENTS.md` | docs | +1/-1 |
| `bridge.md` | docs | +126/-126 |
| `conftest.py` | tooling | +128/-0 |
| `dev/active/MASTER_PLAN.md` | tooling | +5/-0 |
| `dev/active/ai_governance_platform.md` | tooling | +8/-0 |
| `dev/audits/REVIEW_SNAPSHOT.md` | tooling | +1206/-1244 |
| `dev/guides/DEVELOPMENT.md` | docs | +8/-0 |
| `dev/guides/SYSTEM_MAP.md` | docs | +3/-3 |
| `dev/history/ENGINEERING_EVOLUTION.md` | tooling | +27/-0 |
| `dev/scripts/README.md` | tooling | +10/-0 |
| `dev/scripts/checks/check_pytest_runtime_policy.py` | tooling | +12/-0 |
| `dev/scripts/checks/pytest_runtime_policy/__init__.py` | tooling | +1/-0 |
| `dev/scripts/checks/pytest_runtime_policy/command.py` | tooling | +109/-0 |
| `dev/scripts/devctl/bundles/registry.py` | tooling | +1/-5 |
| `dev/scripts/devctl/cli.py` | tooling | +2/-0 |
| `dev/scripts/devctl/cli_parser/entrypoint.py` | tooling | +4/-0 |
| `dev/scripts/devctl/cli_parser/python_tests.py` | tooling | +59/-0 |
| `dev/scripts/devctl/commands/check/router.py` | tooling | +5/-1 |
| `dev/scripts/devctl/commands/check/router_python_tests.py` | tooling | +172/-0 |
| `dev/scripts/devctl/commands/check/router_support.py` | tooling | +2/-0 |
| `dev/scripts/devctl/commands/governance/session_resume_authority_finalize.py` | tooling | +87/-0 |
| `dev/scripts/devctl/commands/governance/session_resume_review_state_payload.py` | tooling | +57/-0 |
| `dev/scripts/devctl/commands/governance/session_resume_support.py` | tooling | +26/-78 |
| `dev/scripts/devctl/commands/listing.py` | tooling | +1/-0 |
| `dev/scripts/devctl/commands/pipeline/auto_recover_action.py` | tooling | +3/-1 |
| `dev/scripts/devctl/commands/pipeline/support.py` | tooling | +12/-4 |
| `dev/scripts/devctl/commands/python_test_runner/__init__.py` | tooling | +1/-0 |
| `dev/scripts/devctl/commands/python_test_runner/command.py` | tooling | +74/-0 |
| `dev/scripts/devctl/commands/python_tests.py` | tooling | +13/-0 |
| `dev/scripts/devctl/commands/review_channel/status_readiness.py` | tooling | +35/-1 |
| `dev/scripts/devctl/governance/script_catalog_registry.py` | tooling | +1/-0 |
| `dev/scripts/devctl/review_channel/current_session_support.py` | tooling | +37/-0 |
| `dev/scripts/devctl/runtime/python_test_contract.py` | tooling | +85/-0 |
| `dev/scripts/devctl/runtime/remote_commit_pipeline_state.py` | tooling | +1/-0 |
| `dev/scripts/devctl/runtime/review_packet_inbox.py` | tooling | +16/-0 |
| `dev/scripts/devctl/runtime/review_packet_inbox_merge.py` | tooling | +25/-2 |
| _12 more files trimmed_ | | |

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
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/remote_commit_pipeline_state.py`) — Review contract-level invariants for this file
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/python_test_contract.py`) — Commit 1ea62a24 changed dev/scripts/devctl/runtime/python_test_contract.py

### Suggested verification commands

- `python3 dev/scripts/devctl.py check --profile ci`
- `python3 dev/scripts/devctl.py probe-report --format md`
- `python3 dev/scripts/devctl.py docs-check --strict-tooling`
- `python3 dev/scripts/devctl.py governance-review --format md`
- `python3 dev/scripts/devctl.py check-router --format md`

## 7. Reasoning — why these changes landed

### Per-commit rationale

- **`1ea62a24`** — Bound Python test execution policy
  - evolution: Fact: A pytest-runaway dogfood failure showed that broad raw pytest commands could still be selected by static bundles or copied into agent workflows, burning local sessions without a repo-owned timeout/target contract.…
- **`b7278dd4`** — Refresh external review snapshot for 961d2e71
  - evolution: Fact: A pytest-runaway dogfood failure showed that broad raw pytest commands could still be selected by static bundles or copied into agent workflows, burning local sessions without a repo-owned timeout/target contract.…
- **`961d2e71`** — Refresh external review snapshot for bf37dd06
  - evolution: Fact: A pytest-runaway dogfood failure showed that broad raw pytest commands could still be selected by static bundles or copied into agent workflows, burning local sessions without a repo-owned timeout/target contract.…
- **`bf37dd06`** — Refresh policy-owned generated surfaces for 4906ad50
  - evolution: Fact: A pytest-runaway dogfood failure showed that broad raw pytest commands could still be selected by static bundles or copied into agent workflows, burning local sessions without a repo-owned timeout/target contract.…
- **`4906ad50`** — Refresh external review snapshot for 772a0ce7
  - evolution: Fact: A pytest-runaway dogfood failure showed that broad raw pytest commands could still be selected by static bundles or copied into agent workflows, burning local sessions without a repo-owned timeout/target contract.…
- **`772a0ce7`** — Treat finding backlog as advisory in session resume
  - evolution: Fact: A pytest-runaway dogfood failure showed that broad raw pytest commands could still be selected by static bundles or copied into agent workflows, burning local sessions without a repo-owned timeout/target contract.…
- **`2662a44f`** — Refresh external review snapshot for f67eded6
  - evolution: Fact: A pytest-runaway dogfood failure showed that broad raw pytest commands could still be selected by static bundles or copied into agent workflows, burning local sessions without a repo-owned timeout/target contract.…
- **`f67eded6`** — Refresh external review snapshot for 2096395c
  - evolution: Fact: A pytest-runaway dogfood failure showed that broad raw pytest commands could still be selected by static bundles or copied into agent workflows, burning local sessions without a repo-owned timeout/target contract.…
- **`2096395c`** — Refresh external review snapshot for bcf72a35
  - evolution: Fact: A pytest-runaway dogfood failure showed that broad raw pytest commands could still be selected by static bundles or copied into agent workflows, burning local sessions without a repo-owned timeout/target contract.…
- **`bcf72a35`** — Fix idle review-channel status readiness
  - evolution: Fact: A pytest-runaway dogfood failure showed that broad raw pytest commands could still be selected by static bundles or copied into agent workflows, burning local sessions without a repo-owned timeout/target contract.…
- **`b3e303b7`** — Refresh external review snapshot for 2ff46d1c
  - evolution: Fact: A pytest-runaway dogfood failure showed that broad raw pytest commands could still be selected by static bundles or copied into agent workflows, burning local sessions without a repo-owned timeout/target contract.…
- **`2ff46d1c`** — Refresh external review snapshot for fa2ca61c
  - evolution: Fact: A pytest-runaway dogfood failure showed that broad raw pytest commands could still be selected by static bundles or copied into agent workflows, burning local sessions without a repo-owned timeout/target contract.…
- **`fa2ca61c`** — Refresh external review snapshot for 9b6cc0d0
  - evolution: Fact: A pytest-runaway dogfood failure showed that broad raw pytest commands could still be selected by static bundles or copied into agent workflows, burning local sessions without a repo-owned timeout/target contract.…
- **`9b6cc0d0`** — Allow pending-publish pipeline authorization refresh
  - evolution: Fact: A pytest-runaway dogfood failure showed that broad raw pytest commands could still be selected by static bundles or copied into agent workflows, burning local sessions without a repo-owned timeout/target contract.…
- **`7cb7ba19`** — Refresh external review snapshot for fde85cea
  - evolution: Fact: A pytest-runaway dogfood failure showed that broad raw pytest commands could still be selected by static bundles or copied into agent workflows, burning local sessions without a repo-owned timeout/target contract.…
- **`fde85cea`** — Refresh external review snapshot for d80d603a
  - evolution: Fact: A pytest-runaway dogfood failure showed that broad raw pytest commands could still be selected by static bundles or copied into agent workflows, burning local sessions without a repo-owned timeout/target contract.…
- **`d80d603a`** — Refresh external review snapshot for a1a0468d
  - evolution: Fact: A pytest-runaway dogfood failure showed that broad raw pytest commands could still be selected by static bundles or copied into agent workflows, burning local sessions without a repo-owned timeout/target contract.…
- **`a1a0468d`** — Refresh external review snapshot for de294ab4
  - evolution: Fact: A pytest-runaway dogfood failure showed that broad raw pytest commands could still be selected by static bundles or copied into agent workflows, burning local sessions without a repo-owned timeout/target contract.…
- **`de294ab4`** — Refresh external review snapshot for 37eb2d78
  - evolution: Fact: A pytest-runaway dogfood failure showed that broad raw pytest commands could still be selected by static bundles or copied into agent workflows, burning local sessions without a repo-owned timeout/target contract.…
- **`37eb2d78`** — Refresh external review snapshot for cc513241
  - evolution: Fact: A pytest-runaway dogfood failure showed that broad raw pytest commands could still be selected by static bundles or copied into agent workflows, burning local sessions without a repo-owned timeout/target contract.…
- **`cc513241`** — Refresh external review snapshot for f5d534ad
  - evolution: Fact: A pytest-runaway dogfood failure showed that broad raw pytest commands could still be selected by static bundles or copied into agent workflows, burning local sessions without a repo-owned timeout/target contract.…
- **`f5d534ad`** — Refresh external review snapshot for 1ad2844d
  - evolution: Fact: A pytest-runaway dogfood failure showed that broad raw pytest commands could still be selected by static bundles or copied into agent workflows, burning local sessions without a repo-owned timeout/target contract.…
- **`1ad2844d`** — Refresh external review snapshot for 330a82e6
  - evolution: Fact: A pytest-runaway dogfood failure showed that broad raw pytest commands could still be selected by static bundles or copied into agent workflows, burning local sessions without a repo-owned timeout/target contract.…
- **`330a82e6`** — Align review-channel launch dry-run test with visible policy
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

Projection produced by `devctl review-snapshot`. Generation stamp `snap-7ae84b747227` binds this file to HEAD `1ea62a2412d5`; if they drift, the freshness guard will fail CI. When the latest commit only refreshes this generated snapshot, the guard accepts this file as bound to that commit's parent code state.
