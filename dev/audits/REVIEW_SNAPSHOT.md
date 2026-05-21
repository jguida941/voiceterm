# VoiceTerm — Review Snapshot

> Deterministically generated from typed governance state. Do not edit by hand — rerun `devctl review-snapshot --write`.

## Quick status

- Branch: `extraction/guardir-core-p0-proof-integrity`
- HEAD: `15fd95b7d880` — Snapshot remaining GuardIR governance repair state
- Tree hash: `a9a661cf56ec`
- Generation stamp: `snap-6bbea6c355d4`
- Generated at (UTC): 2026-05-21T16:12:32Z
- Push decision: `run_devctl_push` — push_preconditions_satisfied
- Reviewer mode: `tools_only` (interaction: `local_terminal`)
- Pipeline state: `n/a` (approval: `n/a`)
- Delta since last snapshot: 24 commits, 124 files, +21432/-1886
- Governance findings: 26 open / 0 fixed / 26 total
- Probe hints: 0 total across 0 files scanned

## 1. Identity

- Repository: **VoiceTerm**
- Product thesis: This is the product thesis for the governance stack in this repository.
Absorb these four commitments before engaging with SOP, guard, routing,
or plan detail — they explain why the process exists.

This repo builds a portable AI governance platform proven through one
production client (VoiceTerm...
- Remote: `https://github.com/jguida941/voiceterm.git`
- Default branch: `master`
- Current branch: `extraction/guardir-core-p0-proof-integrity`
- HEAD SHA: `15fd95b7d880e120c17474f3cc9c6999f323528e`
- HEAD author: Justin Guida
- HEAD timestamp (UTC): 2026-05-21T12:11:33-04:00

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
- publication_backlog: queued
- publication_guidance: 1 local commit(s) waiting for governed push. Run `python3 dev/scripts/devctl.py push --execute` now.

### Reviewer runtime
- reviewer_mode: `tools_only`
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

Range: last 24 commits ending at `15fd95b7d880`

- commits: 24
- files changed: 124
- insertions: +21432
- deletions: -1886
- bundle classes touched: tooling, docs
- authority surfaces touched: 4 file(s)

### Commits

| # | SHA | Subject | Files | +/- | Bundle | Risk |
|---|---|---|---|---|---|---|
| 1 | `15fd95b7` | Snapshot remaining GuardIR governance repair state | 88 | +17721/-617 | tooling |  |
| 2 | `d1387379` | Repair current plan packet scheduler | 17 | +1287/-76 | tooling |  |
| 3 | `fda73137` | Refresh external review snapshot for 41ad2430 | 1 | +49/-47 | tooling |  |
| 4 | `41ad2430` | Land GuardIR v4 canonical plan markdown | 2 | +716/-0 | tooling |  |
| 5 | `62dd7efb` | Refresh external review snapshot for 3a698ba6 | 1 | +55/-49 | tooling |  |
| 6 | `3a698ba6` | Add packet contract schema fixtures | 7 | +166/-54 | tooling |  |
| 7 | `a55f1fbe` | Refresh external review snapshot for 52d8835c | 1 | +52/-53 | tooling |  |
| 8 | `52d8835c` | Bind system map closure plan row | 5 | +53/-50 | tooling |  |
| 9 | `37e29c9a` | Refresh external review snapshot for d06542d2 | 1 | +53/-54 | tooling |  |
| 10 | `d06542d2` | Bind proof resolver closure row | 6 | +55/-52 | tooling |  |
| 11 | `88cd53ad` | Refresh external review snapshot for 877ec1c5 | 1 | +52/-50 | tooling |  |
| 12 | `877ec1c5` | Resolve unittest proof test nodes | 4 | +133/-62 | tooling |  |
| 13 | `93bce1be` | Refresh external review snapshot for 5e431ccc | 1 | +52/-53 | tooling |  |
| 14 | `5e431ccc` | Bind push proof closure plan row | 5 | +54/-57 | tooling |  |
| 15 | `fd57faa3` | Refresh external review snapshot for 69c856eb | 1 | +52/-53 | tooling |  |
| 16 | `69c856eb` | Record push proof closure receipts | 6 | +59/-62 | tooling |  |
| 17 | `20a808a3` | Refresh external review snapshot for 3e35699c | 1 | +54/-51 | tooling |  |
| 18 | `3e35699c` | Fix push-owned commit proof receipts | 5 | +282/-78 | tooling |  |
| 19 | `af8ef168` | Refresh policy-owned generated surfaces for 58a30236 | 1 | +2/-2 | docs |  |
| 20 | `58a30236` | Refresh external review snapshot for ef1f4365 | 1 | +54/-63 | tooling |  |
| 21 | `ef1f4365` | Record packet attention plan closure | 5 | +51/-48 | tooling |  |
| 22 | `6ec72fd2` | Refresh external review snapshot for 623a21ac | 1 | +60/-61 | tooling |  |
| 23 | `623a21ac` | Fix packet attention drain accounting | 6 | +258/-131 | tooling |  |
| 24 | `a1f4a834` | Refresh external review snapshot for 6f94e606 | 1 | +62/-63 | tooling |  |

### Files

| Path | Bundle | +/- |
|---|---|---|
| `dev/active/INDEX.md` | tooling | +19/-6 |
| `dev/active/MASTER_PLAN.md` | tooling | +144/-24 |
| `dev/active/ai_governance_platform.md` | tooling | +73/-48 |
| `dev/active/platform_authority_loop.md` | tooling | +12/-12 |
| `dev/audits/REVIEW_SNAPSHOT.md` | tooling | +1042/-1081 |
| `dev/audits/plan_intake/2026-05-20-guardir-lifecycle-recovery-ci-proof-bridge-v4.md` | tooling | +5124/-353 |
| `dev/audits/plan_intake/sha256-manifest.txt` | tooling | +2/-1 |
| `dev/guides/AI_GOVERNANCE_PLATFORM.md` | docs | +3/-2 |
| `dev/guides/DEVELOPMENT.md` | docs | +21/-20 |
| `dev/guides/PLATFORM_GUIDE.md` | docs | +5/-3 |
| `dev/guides/SYSTEM_MAP.md` | docs | +25/-24 |
| `dev/history/ENGINEERING_EVOLUTION.md` | tooling | +35/-0 |
| `dev/scripts/README.md` | tooling | +1/-0 |
| `dev/scripts/checks/check_active_plan_sync.py` | tooling | +11/-1 |
| `dev/scripts/checks/check_no_prose_authority_promotion.py` | tooling | +455/-0 |
| `dev/scripts/devctl/commands/development/campaign.py` | tooling | +21/-2 |
| `dev/scripts/devctl/commands/development/continuation.py` | tooling | +5/-0 |
| `dev/scripts/devctl/commands/development/final_response_gate.py` | tooling | +146/-13 |
| `dev/scripts/devctl/commands/development/final_response_gate_agent_loop.py` | tooling | +64/-15 |
| `dev/scripts/devctl/commands/development/next_slice.py` | tooling | +87/-16 |
| `dev/scripts/devctl/commands/development/operator_command_wrappers.py` | tooling | +26/-1 |
| `dev/scripts/devctl/commands/development/orchestration_agent_loop.py` | tooling | +14/-2 |
| `dev/scripts/devctl/commands/development/orchestration_agent_loop_parse.py` | tooling | +54/-10 |
| `dev/scripts/devctl/commands/development/orchestration_agent_supervise.py` | tooling | +5/-1 |
| `dev/scripts/devctl/commands/development/orchestration_models.py` | tooling | +11/-0 |
| `dev/scripts/devctl/commands/development/packet_attention.py` | tooling | +55/-6 |
| `dev/scripts/devctl/commands/development/packet_attention_body_followup.py` | tooling | +8/-8 |
| `dev/scripts/devctl/commands/development/report.py` | tooling | +61/-6 |
| `dev/scripts/devctl/commands/development/report_assembly.py` | tooling | +21/-1 |
| `dev/scripts/devctl/commands/development/report_assembly_final.py` | tooling | +12/-0 |
| `dev/scripts/devctl/commands/review_channel/event_handler.py` | tooling | +322/-0 |
| `dev/scripts/devctl/commands/review_channel/event_post_action.py` | tooling | +111/-0 |
| `dev/scripts/devctl/commands/runtime/agent_supervise.py` | tooling | +5/-1 |
| `dev/scripts/devctl/commands/vcs/governed_executor_actor_authority.py` | tooling | +89/-0 |
| `dev/scripts/devctl/commands/vcs/governed_executor_commit_targets.py` | tooling | +41/-10 |
| `dev/scripts/devctl/commands/vcs/push_owned_commit_proof.py` | tooling | +67/-0 |
| `dev/scripts/devctl/commands/vcs/push_preflight_commit.py` | tooling | +45/-7 |
| `dev/scripts/devctl/commands/vcs/push_projection_receipt.py` | tooling | +46/-7 |
| `dev/scripts/devctl/review_channel/agent_loop_decision_projection.py` | tooling | +15/-3 |
| `dev/scripts/devctl/review_channel/agent_packet_attention.py` | tooling | +110/-72 |
| _84 more files trimmed_ | | |

## 4. Quality signals

### Governance review
- total findings: 26
- open: 26
- fixed: 0
- false positives: 0

Recent findings:
- `dogfood.command.probe-report` — `dev/scripts/devctl/commands/probe_report.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.push` — `dev/scripts/devctl/commands/vcs/push.py` (n/a, verdict=`confirmed_issue`)
- `role_oriented_packet_inbox` — `dev/scripts/devctl/review_channel/event_reducer_inbox.py` (high, verdict=`confirmed_issue`)
- `dogfood.command.install-git-hooks` — `dev/scripts/devctl/commands/governance/install_git_hooks.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.orchestrate-status` — `dev/scripts/devctl/commands/reporting/orchestrate_status.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.orchestrate-watch` — `dev/scripts/devctl/commands/governance/orchestrate_watch.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.pipeline` — `dev/scripts/devctl/commands/pipeline/command.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.reports-cleanup` — `dev/scripts/devctl/commands/reports_cleanup.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.agent-mind` — `dev/scripts/devctl/commands/agent_mind/command.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.path-rewrite` — `dev/scripts/devctl/commands/path_rewrite.py` (n/a, verdict=`confirmed_issue`)

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

- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_actor_authority.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_commit_targets.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/reviewer_runtime_models.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/vcs/test_governed_executor.py`) — Review contract-level invariants for this file
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/commands/development/orchestration_models.py`) — Commit 15fd95b7 changed dev/scripts/devctl/commands/development/orchestration_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/agent_loop_decision_models.py`) — Commit 15fd95b7 changed dev/scripts/devctl/runtime/agent_loop_decision_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/reviewer_runtime_models.py`) — Commit 15fd95b7 changed dev/scripts/devctl/runtime/reviewer_runtime_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/review_channel/packet_contract.py`) — Commit d1387379 changed dev/scripts/devctl/review_channel/packet_contract.py

### Suggested verification commands

- `python3 dev/scripts/devctl.py check --profile ci`
- `python3 dev/scripts/devctl.py probe-report --format md`
- `python3 dev/scripts/devctl.py docs-check --strict-tooling`
- `python3 dev/scripts/devctl.py governance-review --format md`
- `python3 dev/scripts/devctl.py check-router --format md`

## 7. Reasoning — why these changes landed

### Per-commit rationale

- **`15fd95b7`** — Snapshot remaining GuardIR governance repair state
  - evolution: The cascade absorption window across MP-GUARDIR-V4-PHASE-0-6-E surfaced a quiet authority-promotion path: hand-maintained guides such as `dev/guides/SYSTEM_MAP.md`, `dev/guides/DEVELOPMENT.md`, and `dev/active/INDEX.md`…
- **`d1387379`** — Repair current plan packet scheduler
  - evolution: The cascade absorption window across MP-GUARDIR-V4-PHASE-0-6-E surfaced a quiet authority-promotion path: hand-maintained guides such as `dev/guides/SYSTEM_MAP.md`, `dev/guides/DEVELOPMENT.md`, and `dev/active/INDEX.md`…
- **`fda73137`** — Refresh external review snapshot for 41ad2430
- **`41ad2430`** — Land GuardIR v4 canonical plan markdown
- **`62dd7efb`** — Refresh external review snapshot for 3a698ba6
- **`3a698ba6`** — Add packet contract schema fixtures
- **`a55f1fbe`** — Refresh external review snapshot for 52d8835c
- **`52d8835c`** — Bind system map closure plan row
- **`37e29c9a`** — Refresh external review snapshot for d06542d2
- **`d06542d2`** — Bind proof resolver closure row
- **`88cd53ad`** — Refresh external review snapshot for 877ec1c5
- **`877ec1c5`** — Resolve unittest proof test nodes
- **`93bce1be`** — Refresh external review snapshot for 5e431ccc
- **`5e431ccc`** — Bind push proof closure plan row
- **`fd57faa3`** — Refresh external review snapshot for 69c856eb
- **`69c856eb`** — Record push proof closure receipts
- **`20a808a3`** — Refresh external review snapshot for 3e35699c
- **`3e35699c`** — Fix push-owned commit proof receipts
- **`af8ef168`** — Refresh policy-owned generated surfaces for 58a30236
- **`58a30236`** — Refresh external review snapshot for ef1f4365
- **`ef1f4365`** — Record packet attention plan closure
- **`6ec72fd2`** — Refresh external review snapshot for 623a21ac
- **`623a21ac`** — Fix packet attention drain accounting
- **`a1f4a834`** — Refresh external review snapshot for 6f94e606
### Active MP scope (from MASTER_PLAN.md)

- contract slice for MP-355 plus the temporary markdown-swarm operating mode
- 2026-05-11 slice 18 fix arc + bilateral protocol consolidation (MP-377):
- 2026-05-14 launch-bootstrap repair family (MP-378): after the relaunch
- `dev/active/review_probes.md` is the review-probe execution spec; implementation tasks stay in this file under `MP-368..MP-375`.
- companion under `MP-376`, not a second main product plan; implementation
- 2026-04-18 `MP-399` governed commit staged-index preservation in `MP-377`
- 2026-04-18 `MP-410` devctl root package-layout relief in `MP-377` scope:
- 2026-04-18 `MP-398` push preflight staged-index exclusion in `MP-377`
- 2026-04-18 `MP-388` consolidation archive pass in `MP-377` scope:
- 2026-04-18 `MP-389` semantic plan-loader core in `MP-377` scope:

## 8. Known gaps and open items

- open governance findings: 26

### Startup advisories
- push_allowed: worktree_clean_and_review_accepted

### Stale warnings
- Stop because nothing remains to push.

### Open gap rows
- **governance_open** (`dev/scripts/devctl/commands/probe_report.py`): dogfood.command.probe-report: Auto-ingested devctl finalization failure rc=1.
repo_path=/Users/jguida941/testing_upgrade/codex-voice
- **governance_open** (`dev/scripts/devctl/commands/vcs/push.py`): dogfood.command.push: Auto-ingested devctl finalization failure rc=1.
repo_path=/Users/jguida941/testing_upgrade/codex-voice
- **governance_open** (`dev/scripts/devctl/review_channel/event_reducer_inbox.py`): role_oriented_packet_inbox: Packet inbox routing is still provider-keyed in several runtime readers. Visibility and consumption must resolve through actor role plus exact session when scoped so provider role switches cannot hide, consume, or drop pending packets.
- **governance_open** (`dev/scripts/devctl/commands/governance/install_git_hooks.py`): dogfood.command.install-git-hooks: Auto-ingested devctl finalization failure rc=1.
repo_path=/Users/jguida941/testing_upgrade/codex-voice
- **governance_open** (`dev/scripts/devctl/commands/reporting/orchestrate_status.py`): dogfood.command.orchestrate-status: Auto-ingested devctl finalization failure rc=1.
repo_path=/Users/jguida941/testing_upgrade/codex-voice
- **governance_open** (`dev/scripts/devctl/commands/governance/orchestrate_watch.py`): dogfood.command.orchestrate-watch: Auto-ingested devctl finalization failure rc=1.
repo_path=/Users/jguida941/testing_upgrade/codex-voice
- **governance_open** (`dev/scripts/devctl/commands/pipeline/command.py`): dogfood.command.pipeline: Auto-ingested devctl finalization failure rc=1.
repo_path=/Users/jguida941/testing_upgrade/codex-voice
- **governance_open** (`dev/scripts/devctl/commands/reports_cleanup.py`): dogfood.command.reports-cleanup: Auto-ingested devctl finalization failure rc=1.
repo_path=/Users/jguida941/testing_upgrade/codex-voice

---

Projection produced by `devctl review-snapshot`. Generation stamp `snap-6bbea6c355d4` binds this file to HEAD `15fd95b7d880`; if they drift, the freshness guard will fail CI. When the latest commit only refreshes this generated snapshot, the guard accepts this file as bound to that commit's parent code state.
