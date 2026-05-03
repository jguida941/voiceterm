# VoiceTerm — Review Snapshot

> Deterministically generated from typed governance state. Do not edit by hand — rerun `devctl review-snapshot --write`.

## Quick status

- Branch: `feature/governance-quality-sweep`
- HEAD: `330a82e6606c` — Align review-channel launch dry-run test with visible policy
- Tree hash: `2e68c5766215`
- Generation stamp: `snap-9aa53964b096`
- Generated at (UTC): 2026-05-03T07:00:53Z
- Push decision: `run_devctl_push` — push_preconditions_satisfied
- Reviewer mode: `single_agent` (interaction: `local_terminal`)
- Pipeline state: `n/a` (approval: `n/a`)
- Delta since last snapshot: 24 commits, 108 files, +7007/-2058
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
- HEAD SHA: `330a82e6606cc6bf15bf2f0fea269b81e778cd6d`
- HEAD author: Justin Guida
- HEAD timestamp (UTC): 2026-05-03T03:00:37-04:00

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
- latest_push_report_state: `post_push_green` (push_completed)
- publication_backlog: recommended
- publication_guidance: 2 local commit(s) waiting for governed push. Run `python3 dev/scripts/devctl.py push --execute` now.

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

Range: last 24 commits ending at `330a82e6606c`

- commits: 24
- files changed: 108
- insertions: +7007
- deletions: -2058
- bundle classes touched: tooling, docs
- authority surfaces touched: 10 file(s)

### Commits

| # | SHA | Subject | Files | +/- | Bundle | Risk |
|---|---|---|---|---|---|---|
| 1 | `330a82e6` | Align review-channel launch dry-run test with visible policy | 2 | +67/-58 | tooling |  |
| 2 | `0278cb96` | Migrate Codex provider args from --full-auto to explicit ap… | 8 | +112/-93 | tooling |  |
| 3 | `a982d6d2` | Refresh external review snapshot for 4dee7ce3 | 2 | +46/-46 | docs |  |
| 4 | `4dee7ce3` | Refresh external review snapshot for 6e55bc00 | 1 | +43/-43 | tooling |  |
| 5 | `6e55bc00` | Refresh external review snapshot for e9a687a9 | 2 | +44/-44 | docs |  |
| 6 | `e9a687a9` | Refresh external review snapshot for 8f6e138e | 1 | +47/-44 | tooling |  |
| 7 | `8f6e138e` | Refresh external review snapshot for dbedb6d3 | 2 | +63/-68 | docs |  |
| 8 | `dbedb6d3` | Fix governed push managed projection parsing | 15 | +359/-215 | tooling |  |
| 9 | `04434ae5` | Refresh external review snapshot for 5799b3bf | 2 | +47/-47 | docs |  |
| 10 | `5799b3bf` | Refresh external review snapshot for e6fbc758 | 1 | +47/-44 | tooling |  |
| 11 | `e6fbc758` | Refresh external review snapshot for 819ec43e | 2 | +64/-66 | docs |  |
| 12 | `819ec43e` | Fix stale supervised process audit | 13 | +420/-88 | tooling |  |
| 13 | `0e6730e1` | Refresh external review snapshot for 19d53fbc | 2 | +45/-45 | docs |  |
| 14 | `19d53fbc` | Refresh external review snapshot for ba76cf52 | 1 | +46/-43 | tooling |  |
| 15 | `ba76cf52` | Refresh external review snapshot for 900de219 | 2 | +43/-46 | docs |  |
| 16 | `900de219` | Record review-channel poll projection receipt | 2 | +44/-41 | docs |  |
| 17 | `532f5665` | Refresh external review snapshot for f9176c87 | 2 | +112/-83 | docs |  |
| 18 | `f9176c87` | Checkpoint typed develop and wake routing | 89 | +4809/-588 | tooling |  |
| 19 | `d66f61f2` | Refresh external review snapshot for 8d59ccfb | 2 | +54/-52 | docs |  |
| 20 | `8d59ccfb` | Refresh external review snapshot for 67901df8 | 2 | +69/-65 | docs |  |
| 21 | `67901df8` | Route commit failures through failure packet router | 11 | +273/-87 | tooling |  |
| 22 | `ed38ab8e` | Refresh external review snapshot for 5d00434a | 2 | +46/-48 | docs |  |
| 23 | `5d00434a` | Refresh external review snapshot for 34c4ea42 | 1 | +47/-44 | tooling |  |
| 24 | `34c4ea42` | Refresh external review snapshot for 1733d2a8 | 2 | +60/-60 | docs |  |

### Files

| Path | Bundle | +/- |
|---|---|---|
| `.claude/commands/develop.md` | docs | +5/-0 |
| `.github/workflows/README.md` | tooling | +2/-2 |
| `.github/workflows/release_preflight.yml` | tooling | +1/-0 |
| `.github/workflows/tooling_control_plane.yml` | tooling | +7/-0 |
| `AGENTS.md` | docs | +26/-7 |
| `bridge.md` | docs | +80/-80 |
| `dev/active/MASTER_PLAN.md` | tooling | +44/-5 |
| `dev/active/ai_governance_platform.md` | tooling | +66/-0 |
| `dev/audits/REVIEW_SNAPSHOT.md` | tooling | +1308/-1270 |
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
- **`ed38ab8e`** — Refresh external review snapshot for 5d00434a
  - evolution: Fact: The MP-377 Typed AgentAttentionLoop plan exposed one more authority gap: agent-authored plans could still live only in chat, packet text, or temp files until a later manual edit copied them into the typed master-p…
- **`5d00434a`** — Refresh external review snapshot for 34c4ea42
  - evolution: Fact: The MP-377 Typed AgentAttentionLoop plan exposed one more authority gap: agent-authored plans could still live only in chat, packet text, or temp files until a later manual edit copied them into the typed master-p…
- **`34c4ea42`** — Refresh external review snapshot for 1733d2a8
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
- push_allowed: worktree_clean_and_review_accepted

### Stale warnings
- Stop because nothing remains to push.

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

Projection produced by `devctl review-snapshot`. Generation stamp `snap-9aa53964b096` binds this file to HEAD `330a82e6606c`; if they drift, the freshness guard will fail CI. When the latest commit only refreshes this generated snapshot, the guard accepts this file as bound to that commit's parent code state.
