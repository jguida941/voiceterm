# VoiceTerm — Review Snapshot

> Deterministically generated from typed governance state. Do not edit by hand — rerun `devctl review-snapshot --write`.

## Quick status

- Branch: `feature/governance-quality-sweep`
- HEAD: `cc5132413eac` — Refresh external review snapshot for f5d534ad
- Tree hash: `b3edcd6e7b34`
- Generation stamp: `snap-882caa033ea5`
- Generated at (UTC): 2026-05-03T07:12:05Z
- Push decision: `run_devctl_push` — push_preconditions_satisfied
- Reviewer mode: `tools_only` (interaction: `local_terminal`)
- Pipeline state: `n/a` (approval: `n/a`)
- Delta since last snapshot: 24 commits, 108 files, +7034/-2088
- Governance findings: 152 open / 88 fixed / 254 total
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
- HEAD SHA: `cc5132413eac35483a300279ce34ac0bf1c851f9`
- HEAD author: Justin Guida
- HEAD timestamp (UTC): 2026-05-03T03:07:24-04:00

## 2. Governance state

### Push decision
- action: `run_devctl_push`
- reason: push_preconditions_satisfied
- push_eligible_now: False
- worktree_clean: True
- staged_path_count: 0
- unstaged_path_count: 0
- next_step_command: `python3 dev/scripts/devctl.py review-channel --action status --terminal none --format json`
- latest_push_report: `dev/reports/push/latest.json`
- latest_push_report_state: `blocked` (push_preflight_running)
- current_push_authorization: `push-auth-20260503T065934651679Z` (valid=True)
- authorized_head_commit: `1ad2844d6a806bfca0c9d615302619a09d984907`
- approved_target_identity: `tree-receipt-20260503T065934651679Z:2e68c5766215a41862ad02d7f90f3204a24e4861`
- publication_backlog: urgent
- publication_guidance: 5 local commit(s) waiting for governed push. Run `python3 dev/scripts/devctl.py push --execute` now.

### Reviewer runtime
- reviewer_mode: `tools_only`
- reviewer_freshness: unknown
- reviewer_publish_clear: False
- interaction_mode: `local_terminal`
- implementation_blocked: yes — runtime_missing

### Remote commit pipeline
- state: `n/a`
- approval_state: `n/a`

### Work intake
- active plan: **AI Governance Platform Plan**
- plan path: `dev/active/ai_governance_platform.md`
- active MP scope: `MP-377`
- advisory: `repair_reviewer_loop` — runtime_missing

## 3. Delta — what changed since the previous snapshot

Range: last 24 commits ending at `cc5132413eac`

- commits: 24
- files changed: 108
- insertions: +7034
- deletions: -2088
- bundle classes touched: docs, tooling
- authority surfaces touched: 10 file(s)

### Commits

| # | SHA | Subject | Files | +/- | Bundle | Risk |
|---|---|---|---|---|---|---|
| 1 | `cc513241` | Refresh external review snapshot for f5d534ad | 2 | +49/-49 | docs |  |
| 2 | `f5d534ad` | Refresh external review snapshot for 1ad2844d | 2 | +53/-50 | docs |  |
| 3 | `1ad2844d` | Refresh external review snapshot for 330a82e6 | 2 | +78/-83 | docs |  |
| 4 | `330a82e6` | Align review-channel launch dry-run test with visible policy | 2 | +67/-58 | tooling |  |
| 5 | `0278cb96` | Migrate Codex provider args from --full-auto to explicit ap… | 8 | +112/-93 | tooling |  |
| 6 | `a982d6d2` | Refresh external review snapshot for 4dee7ce3 | 2 | +46/-46 | docs |  |
| 7 | `4dee7ce3` | Refresh external review snapshot for 6e55bc00 | 1 | +43/-43 | tooling |  |
| 8 | `6e55bc00` | Refresh external review snapshot for e9a687a9 | 2 | +44/-44 | docs |  |
| 9 | `e9a687a9` | Refresh external review snapshot for 8f6e138e | 1 | +47/-44 | tooling |  |
| 10 | `8f6e138e` | Refresh external review snapshot for dbedb6d3 | 2 | +63/-68 | docs |  |
| 11 | `dbedb6d3` | Fix governed push managed projection parsing | 15 | +359/-215 | tooling |  |
| 12 | `04434ae5` | Refresh external review snapshot for 5799b3bf | 2 | +47/-47 | docs |  |
| 13 | `5799b3bf` | Refresh external review snapshot for e6fbc758 | 1 | +47/-44 | tooling |  |
| 14 | `e6fbc758` | Refresh external review snapshot for 819ec43e | 2 | +64/-66 | docs |  |
| 15 | `819ec43e` | Fix stale supervised process audit | 13 | +420/-88 | tooling |  |
| 16 | `0e6730e1` | Refresh external review snapshot for 19d53fbc | 2 | +45/-45 | docs |  |
| 17 | `19d53fbc` | Refresh external review snapshot for ba76cf52 | 1 | +46/-43 | tooling |  |
| 18 | `ba76cf52` | Refresh external review snapshot for 900de219 | 2 | +43/-46 | docs |  |
| 19 | `900de219` | Record review-channel poll projection receipt | 2 | +44/-41 | docs |  |
| 20 | `532f5665` | Refresh external review snapshot for f9176c87 | 2 | +112/-83 | docs |  |
| 21 | `f9176c87` | Checkpoint typed develop and wake routing | 89 | +4809/-588 | tooling |  |
| 22 | `d66f61f2` | Refresh external review snapshot for 8d59ccfb | 2 | +54/-52 | docs |  |
| 23 | `8d59ccfb` | Refresh external review snapshot for 67901df8 | 2 | +69/-65 | docs |  |
| 24 | `67901df8` | Route commit failures through failure packet router | 11 | +273/-87 | tooling |  |

### Files

| Path | Bundle | +/- |
|---|---|---|
| `.claude/commands/develop.md` | docs | +5/-0 |
| `.github/workflows/README.md` | tooling | +2/-2 |
| `.github/workflows/release_preflight.yml` | tooling | +1/-0 |
| `.github/workflows/tooling_control_plane.yml` | tooling | +7/-0 |
| `AGENTS.md` | docs | +26/-7 |
| `bridge.md` | docs | +110/-110 |
| `dev/active/MASTER_PLAN.md` | tooling | +44/-5 |
| `dev/active/ai_governance_platform.md` | tooling | +66/-0 |
| `dev/audits/REVIEW_SNAPSHOT.md` | tooling | +1305/-1270 |
| `dev/config/devctl_repo_policy.json` | tooling | +17/-1 |
| `dev/config/templates/README.md` | tooling | +3/-0 |
| `dev/config/templates/develop_role_adapters.template.md` | tooling | +8/-0 |
| `dev/guides/DEVELOPMENT.md` | docs | +17/-3 |
| `dev/guides/SYSTEM_MAP.md` | docs | +14/-6 |
| `dev/history/ENGINEERING_EVOLUTION.md` | tooling | +151/-1 |
| `dev/scripts/README.md` | tooling | +60/-27 |
| `dev/scripts/devctl/approval_mode.py` | tooling | +9/-1 |
| `dev/scripts/devctl/bundles/registry.py` | tooling | +2/-0 |
| `dev/scripts/devctl/cli_parser/artifact_suppression.py` | tooling | +7/-0 |
| `dev/scripts/devctl/commands/check/router.py` | tooling | +71/-10 |
| `dev/scripts/devctl/commands/check/router_constants.py` | tooling | +1/-1 |
| `dev/scripts/devctl/commands/development/actions.py` | tooling | +17/-0 |
| `dev/scripts/devctl/commands/development/command.py` | tooling | +4/-1 |
| `dev/scripts/devctl/commands/development/models.py` | tooling | +19/-0 |
| `dev/scripts/devctl/commands/development/parser.py` | tooling | +153/-6 |
| `dev/scripts/devctl/commands/development/plan_intake.py` | tooling | +216/-0 |
| `dev/scripts/devctl/commands/development/plan_intake_evidence.py` | tooling | +47/-0 |
| `dev/scripts/devctl/commands/development/plan_intake_provenance.py` | tooling | +27/-0 |
| `dev/scripts/devctl/commands/development/plan_intake_receipts.py` | tooling | +81/-0 |
| `dev/scripts/devctl/commands/development/plan_intake_rows.py` | tooling | +126/-0 |
| `dev/scripts/devctl/commands/development/plan_intake_sources.py` | tooling | +146/-0 |
| `dev/scripts/devctl/commands/development/plan_intake_support.py` | tooling | +23/-0 |
| `dev/scripts/devctl/commands/development/plan_intake_titles.py` | tooling | +32/-0 |
| `dev/scripts/devctl/commands/development/render.py` | tooling | +52/-0 |
| `dev/scripts/devctl/commands/development/render_collaboration.py` | tooling | +3/-1 |
| `dev/scripts/devctl/commands/development/report.py` | tooling | +18/-10 |
| `dev/scripts/devctl/commands/governance/session_reviewer_loop.py` | tooling | +8/-5 |
| `dev/scripts/devctl/commands/process/audit.py` | tooling | +56/-4 |
| `dev/scripts/devctl/commands/process/cleanup.py` | tooling | +19/-5 |
| `dev/scripts/devctl/commands/process/conductor_staleness.py` | tooling | +90/-0 |
| _68 more files trimmed_ | | |

## 4. Quality signals

### Governance review
- total findings: 254
- open: 152
- fixed: 88
- false positives: 0

Recent findings:
- `dogfood.command.status` — `dev/scripts/devctl/commands/reporting/status.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.render-surfaces` — `dev/scripts/devctl/commands/governance/render_surfaces.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.agent-loop` — `dev/scripts/devctl/commands/reporting/claude_loop.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.agent-mind` — `dev/scripts/devctl/commands/agent_mind/command.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.governance-bootstrap` — `dev/scripts/devctl/commands/governance/bootstrap.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.orchestrate-status` — `dev/scripts/devctl/commands/reporting/orchestrate_status.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.orchestrate-watch` — `dev/scripts/devctl/commands/governance/orchestrate_watch.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.integrations-import` — `dev/scripts/devctl/commands/integrations_import.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.governance-export` — `dev/scripts/devctl/commands/governance/export.py` (n/a, verdict=`confirmed_issue`)
- `packet.transition_session_disambiguation` — `dev/scripts/devctl/review_channel/instruction_transitions.py` (critical, verdict=`confirmed_issue`)

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

- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/review_channel/reviewer_follow_guard.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/review_channel/reviewer_runtime_contract.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/review_snapshot_hints.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/reviewer_runtime_models.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/commands/check/test_check_router.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/commands/check/test_check_router_support.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/runtime/test_review_snapshot.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_commit_failure_router.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_commit_phase.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/vcs/test_governed_executor.py`) — Review contract-level invariants for this file
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/review_channel/event_models.py`) — Commit f9176c87 changed dev/scripts/devctl/review_channel/event_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/review_channel/packet_contract.py`) — Commit f9176c87 changed dev/scripts/devctl/review_channel/packet_contract.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/review_channel/reviewer_runtime_contract.py`) — Commit f9176c87 changed dev/scripts/devctl/review_channel/reviewer_runtime_contract.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/review_channel/wake_receipt_models.py`) — Commit f9176c87 changed dev/scripts/devctl/review_channel/wake_receipt_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/agent_dispatch_router_models.py`) — Commit f9176c87 changed dev/scripts/devctl/runtime/agent_dispatch_router_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/development_packet_pressure_models.py`) — Commit f9176c87 changed dev/scripts/devctl/runtime/development_packet_pressure_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/review_state_packet_models.py`) — Commit f9176c87 changed dev/scripts/devctl/runtime/review_state_packet_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/reviewer_runtime_models.py`) — Commit f9176c87 changed dev/scripts/devctl/runtime/reviewer_runtime_models.py

### Suggested verification commands

- `python3 dev/scripts/devctl.py check --profile ci`
- `python3 dev/scripts/devctl.py probe-report --format md`
- `python3 dev/scripts/devctl.py docs-check --strict-tooling`
- `python3 dev/scripts/devctl.py governance-review --format md`
- `python3 dev/scripts/devctl.py check-router --format md`

## 7. Reasoning — why these changes landed

### Per-commit rationale

- **`cc513241`** — Refresh external review snapshot for f5d534ad
  - evolution: Fact: Live post-push dogfooding caught a false green: `devctl push` published and reported `post_push_green`, but the final startup/bootstrap checks still found `dev/audits/REVIEW_SNAPSHOT.md` dirty. The root cause was …
- **`f5d534ad`** — Refresh external review snapshot for 1ad2844d
  - evolution: Fact: Live post-push dogfooding caught a false green: `devctl push` published and reported `post_push_green`, but the final startup/bootstrap checks still found `dev/audits/REVIEW_SNAPSHOT.md` dirty. The root cause was …
- **`1ad2844d`** — Refresh external review snapshot for 330a82e6
  - evolution: Fact: Live post-push dogfooding caught a false green: `devctl push` published and reported `post_push_green`, but the final startup/bootstrap checks still found `dev/audits/REVIEW_SNAPSHOT.md` dirty. The root cause was …
- **`330a82e6`** — Align review-channel launch dry-run test with visible policy
  - evolution: Fact: Live post-push dogfooding caught a false green: `devctl push` published and reported `post_push_green`, but the final startup/bootstrap checks still found `dev/audits/REVIEW_SNAPSHOT.md` dirty. The root cause was …
- **`0278cb96`** — Migrate Codex provider args from --full-auto to explicit approval/sandbox flags
  - evolution: Fact: Live post-push dogfooding caught a false green: `devctl push` published and reported `post_push_green`, but the final startup/bootstrap checks still found `dev/audits/REVIEW_SNAPSHOT.md` dirty. The root cause was …
- **`a982d6d2`** — Refresh external review snapshot for 4dee7ce3
  - evolution: Fact: Live post-push dogfooding caught a false green: `devctl push` published and reported `post_push_green`, but the final startup/bootstrap checks still found `dev/audits/REVIEW_SNAPSHOT.md` dirty. The root cause was …
- **`4dee7ce3`** — Refresh external review snapshot for 6e55bc00
  - evolution: Fact: Live post-push dogfooding caught a false green: `devctl push` published and reported `post_push_green`, but the final startup/bootstrap checks still found `dev/audits/REVIEW_SNAPSHOT.md` dirty. The root cause was …
- **`6e55bc00`** — Refresh external review snapshot for e9a687a9
  - evolution: Fact: Live post-push dogfooding caught a false green: `devctl push` published and reported `post_push_green`, but the final startup/bootstrap checks still found `dev/audits/REVIEW_SNAPSHOT.md` dirty. The root cause was …
- **`e9a687a9`** — Refresh external review snapshot for 8f6e138e
  - evolution: Fact: Live post-push dogfooding caught a false green: `devctl push` published and reported `post_push_green`, but the final startup/bootstrap checks still found `dev/audits/REVIEW_SNAPSHOT.md` dirty. The root cause was …
- **`8f6e138e`** — Refresh external review snapshot for dbedb6d3
  - evolution: Fact: Live post-push dogfooding caught a false green: `devctl push` published and reported `post_push_green`, but the final startup/bootstrap checks still found `dev/audits/REVIEW_SNAPSHOT.md` dirty. The root cause was …
- **`dbedb6d3`** — Fix governed push managed projection parsing
  - evolution: Fact: Live post-push dogfooding caught a false green: `devctl push` published and reported `post_push_green`, but the final startup/bootstrap checks still found `dev/audits/REVIEW_SNAPSHOT.md` dirty. The root cause was …
- **`04434ae5`** — Refresh external review snapshot for 5799b3bf
  - evolution: Fact: Live post-push dogfooding caught a false green: `devctl push` published and reported `post_push_green`, but the final startup/bootstrap checks still found `dev/audits/REVIEW_SNAPSHOT.md` dirty. The root cause was …
- **`5799b3bf`** — Refresh external review snapshot for e6fbc758
  - evolution: Fact: Live post-push dogfooding caught a false green: `devctl push` published and reported `post_push_green`, but the final startup/bootstrap checks still found `dev/audits/REVIEW_SNAPSHOT.md` dirty. The root cause was …
- **`e6fbc758`** — Refresh external review snapshot for 819ec43e
  - evolution: Fact: Live post-push dogfooding caught a false green: `devctl push` published and reported `post_push_green`, but the final startup/bootstrap checks still found `dev/audits/REVIEW_SNAPSHOT.md` dirty. The root cause was …
- **`819ec43e`** — Fix stale supervised process audit
  - evolution: Fact: Live post-push dogfooding caught a false green: `devctl push` published and reported `post_push_green`, but the final startup/bootstrap checks still found `dev/audits/REVIEW_SNAPSHOT.md` dirty. The root cause was …
- **`0e6730e1`** — Refresh external review snapshot for 19d53fbc
  - evolution: Fact: The MP-377 Typed AgentAttentionLoop plan exposed one more authority gap: agent-authored plans could still live only in chat, packet text, or temp files until a later manual edit copied them into the typed master-p…
- **`19d53fbc`** — Refresh external review snapshot for ba76cf52
  - evolution: Fact: The MP-377 Typed AgentAttentionLoop plan exposed one more authority gap: agent-authored plans could still live only in chat, packet text, or temp files until a later manual edit copied them into the typed master-p…
- **`ba76cf52`** — Refresh external review snapshot for 900de219
  - evolution: Fact: The MP-377 Typed AgentAttentionLoop plan exposed one more authority gap: agent-authored plans could still live only in chat, packet text, or temp files until a later manual edit copied them into the typed master-p…
- **`900de219`** — Record review-channel poll projection receipt
  - evolution: Fact: The MP-377 Typed AgentAttentionLoop plan exposed one more authority gap: agent-authored plans could still live only in chat, packet text, or temp files until a later manual edit copied them into the typed master-p…
- **`532f5665`** — Refresh external review snapshot for f9176c87
  - evolution: Fact: The MP-377 Typed AgentAttentionLoop plan exposed one more authority gap: agent-authored plans could still live only in chat, packet text, or temp files until a later manual edit copied them into the typed master-p…
- **`f9176c87`** — Checkpoint typed develop and wake routing
  - evolution: Fact: The MP-377 Typed AgentAttentionLoop plan exposed one more authority gap: agent-authored plans could still live only in chat, packet text, or temp files until a later manual edit copied them into the typed master-p…
- **`d66f61f2`** — Refresh external review snapshot for 8d59ccfb
  - evolution: Fact: The MP-377 Typed AgentAttentionLoop plan exposed one more authority gap: agent-authored plans could still live only in chat, packet text, or temp files until a later manual edit copied them into the typed master-p…
- **`8d59ccfb`** — Refresh external review snapshot for 67901df8
  - evolution: Fact: The MP-377 Typed AgentAttentionLoop plan exposed one more authority gap: agent-authored plans could still live only in chat, packet text, or temp files until a later manual edit copied them into the typed master-p…
- **`67901df8`** — Route commit failures through failure packet router
  - evolution: Fact: The MP-377 Typed AgentAttentionLoop plan exposed one more authority gap: agent-authored plans could still live only in chat, packet text, or temp files until a later manual edit copied them into the typed master-p…
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

- open governance findings: 152

### Startup advisories
- repair_reviewer_loop: runtime_missing

### Stale warnings
- Cut a checkpoint before doing anything else.

### Open gap rows
- **governance_open** (`dev/scripts/devctl/commands/reporting/status.py`): dogfood.command.status: Auto-ingested devctl finalization failure rc=1.
repo_path=/Users/jguida941/testing_upgrade/codex-voice
- **governance_open** (`dev/scripts/devctl/commands/governance/render_surfaces.py`): dogfood.command.render-surfaces: Auto-ingested devctl finalization failure rc=1.
repo_path=/Users/jguida941/testing_upgrade/codex-voice
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

---

Projection produced by `devctl review-snapshot`. Generation stamp `snap-882caa033ea5` binds this file to HEAD `cc5132413eac`; if they drift, the freshness guard will fail CI. When the latest commit only refreshes this generated snapshot, the guard accepts this file as bound to that commit's parent code state.
