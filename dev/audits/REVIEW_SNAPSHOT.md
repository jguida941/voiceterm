# VoiceTerm — Review Snapshot

> Deterministically generated from typed governance state. Do not edit by hand — rerun `devctl review-snapshot --write`.

## Quick status

- Branch: `feature/governance-quality-sweep`
- HEAD: `8d59ccfbc2e0` — Refresh external review snapshot for 67901df8
- Tree hash: `f91bc78bbf13`
- Generation stamp: `snap-713d88d1a3d3`
- Generated at (UTC): 2026-05-02T22:30:53Z
- Push decision: `no_push_needed` — managed_projection_drift_only
- Reviewer mode: `single_agent` (interaction: `local_terminal`)
- Pipeline state: `n/a` (approval: `n/a`)
- Delta since last snapshot: 24 commits, 23 files, +1972/-1268
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
- HEAD SHA: `8d59ccfbc2e07cb9d6717afec35561802d72704b`
- HEAD author: Justin Guida
- HEAD timestamp (UTC): 2026-05-02T18:04:23-04:00

## 2. Governance state

### Push decision
- action: `no_push_needed`
- reason: managed_projection_drift_only
- push_eligible_now: False
- worktree_clean: True
- staged_path_count: 0
- unstaged_path_count: 0
- next_step_command: `n/a`
- latest_push_report: `dev/reports/push/latest.json`
- latest_push_report_state: `post_push_green` (push_completed)
- current_push_authorization: `push-auth-20260502T220343952902Z` (valid=True)
- authorized_head_commit: `8d59ccfbc2e07cb9d6717afec35561802d72704b`
- approved_target_identity: `tree-receipt-20260502T220343952902Z:1c13b282a0626a019c397dae4cceb22d1794aa98`
- publication_backlog: none

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
- advisory: `no_push_needed` — managed_projection_drift_only

## 3. Delta — what changed since the previous snapshot

Range: last 24 commits ending at `8d59ccfbc2e0`

- commits: 24
- files changed: 23
- insertions: +1972
- deletions: -1268
- bundle classes touched: docs, tooling
- authority surfaces touched: 5 file(s)

### Commits

| # | SHA | Subject | Files | +/- | Bundle | Risk |
|---|---|---|---|---|---|---|
| 1 | `8d59ccfb` | Refresh external review snapshot for 67901df8 | 2 | +69/-65 | docs |  |
| 2 | `67901df8` | Route commit failures through failure packet router | 11 | +273/-87 | tooling |  |
| 3 | `ed38ab8e` | Refresh external review snapshot for 5d00434a | 2 | +46/-48 | docs |  |
| 4 | `5d00434a` | Refresh external review snapshot for 34c4ea42 | 1 | +47/-44 | tooling |  |
| 5 | `34c4ea42` | Refresh external review snapshot for 1733d2a8 | 2 | +60/-60 | docs |  |
| 6 | `1733d2a8` | Integrate packet finding stack into MP-377 plan | 2 | +176/-61 | tooling |  |
| 7 | `82d0bb3a` | Refresh external review snapshot for 48b0e03d | 1 | +42/-39 | tooling |  |
| 8 | `48b0e03d` | Refresh external review snapshot for f04275a0 | 2 | +57/-62 | docs |  |
| 9 | `f04275a0` | chore(push): auto-commit preflight-generated changes | 3 | +56/-58 | tooling |  |
| 10 | `38c938ba` | Refresh external review snapshot for 6ed88467 | 2 | +47/-44 | docs |  |
| 11 | `6ed88467` | Refresh external review snapshot for 50ac1d8a | 1 | +45/-49 | tooling |  |
| 12 | `50ac1d8a` | Refresh plan projection for automation findings | 2 | +2/-0 | tooling |  |
| 13 | `3d02e980` | Refresh review snapshot after system picture update | 1 | +71/-97 | tooling |  |
| 14 | `93f32b7d` | Refresh managed projection surfaces after publisher stop | 3 | +5/-3 | tooling |  |
| 15 | `9d05fe6c` | Refresh managed projection surfaces after publisher update | 3 | +7/-5 | tooling |  |
| 16 | `b8dfb984` | Refresh managed projection surfaces after drift repair | 4 | +67/-55 | tooling |  |
| 17 | `8a361a42` | Refresh external review snapshot for f510da77 | 2 | +65/-69 | docs |  |
| 18 | `f510da77` | Fix empty develop packet attention summary | 11 | +160/-83 | tooling |  |
| 19 | `5908bcd9` | Refresh external review snapshot for a2c85e4a | 2 | +47/-47 | docs |  |
| 20 | `a2c85e4a` | Refresh external review snapshot for 4baabf40 | 1 | +53/-50 | tooling |  |
| 21 | `4baabf40` | Refresh policy-owned generated surfaces for 2cc4bd10 | 1 | +1/-1 | docs |  |
| 22 | `2cc4bd10` | Refresh external review snapshot for 7a3579b1 | 2 | +66/-64 | docs |  |
| 23 | `7a3579b1` | Persist launcher discipline bypass receipts | 8 | +452/-119 | tooling |  |
| 24 | `3ff41ec7` | Refresh external review snapshot for 117ea0d3 | 2 | +58/-58 | docs |  |

### Files

| Path | Bundle | +/- |
|---|---|---|
| `AGENTS.md` | docs | +2/-1 |
| `bridge.md` | docs | +57/-57 |
| `dev/active/MASTER_PLAN.md` | tooling | +18/-0 |
| `dev/active/ai_governance_platform.md` | tooling | +121/-0 |
| `dev/audits/REVIEW_SNAPSHOT.md` | tooling | +1139/-1185 |
| `dev/guides/DEVELOPMENT.md` | docs | +9/-0 |
| `dev/guides/SYSTEM_MAP.md` | docs | +2/-2 |
| `dev/history/ENGINEERING_EVOLUTION.md` | tooling | +59/-0 |
| `dev/scripts/README.md` | tooling | +10/-0 |
| `dev/scripts/devctl/commands/development/models.py` | tooling | +4/-1 |
| `dev/scripts/devctl/commands/development/packet_attention.py` | tooling | +4/-1 |
| `dev/scripts/devctl/commands/review_channel/_recover.py` | tooling | +14/-2 |
| `dev/scripts/devctl/commands/review_channel/bridge_handler.py` | tooling | +10/-2 |
| `dev/scripts/devctl/commands/review_channel/bridge_launch_control.py` | tooling | +9/-2 |
| `dev/scripts/devctl/commands/review_channel/launcher_discipline.py` | tooling | +68/-10 |
| `dev/scripts/devctl/commands/review_channel/launcher_discipline_receipts.py` | tooling | +81/-0 |
| `dev/scripts/devctl/commands/vcs/governed_executor_commit_failure_router.py` | tooling | +49/-0 |
| `dev/scripts/devctl/commands/vcs/governed_executor_commit_phase.py` | tooling | +28/-5 |
| `dev/scripts/devctl/review_channel/recover_support.py` | tooling | +1/-0 |
| `dev/scripts/devctl/tests/commands/test_development_command.py` | tooling | +18/-0 |
| `dev/scripts/devctl/tests/review_channel/test_launcher_discipline_bypass_receipt.py` | tooling | +182/-0 |
| `dev/scripts/devctl/tests/vcs/test_governed_executor.py` | tooling | +75/-0 |
| `dev/state/plan_index.jsonl` | tooling | +12/-0 |

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

- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_commit_failure_router.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_commit_phase.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/vcs/test_governed_executor.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/review_channel/bridge_handler.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/review_channel/bridge_launch_control.py`) — Review contract-level invariants for this file

### Suggested verification commands

- `python3 dev/scripts/devctl.py check --profile ci`
- `python3 dev/scripts/devctl.py probe-report --format md`
- `python3 dev/scripts/devctl.py docs-check --strict-tooling`
- `python3 dev/scripts/devctl.py governance-review --format md`
- `python3 dev/scripts/devctl.py check-router --format md`

## 7. Reasoning — why these changes landed

### Per-commit rationale

- **`8d59ccfb`** — Refresh external review snapshot for 67901df8
  - evolution: Fact: Plan r3 dogfooding showed that the `ActionResult.auto_executable` and `remediation` fields were still mostly write-only in the governed commit failure path. Commit failures could name a next command, but `_commit_…
- **`67901df8`** — Route commit failures through failure packet router
  - evolution: Fact: Plan r3 dogfooding showed that the `ActionResult.auto_executable` and `remediation` fields were still mostly write-only in the governed commit failure path. Commit failures could name a next command, but `_commit_…
- **`ed38ab8e`** — Refresh external review snapshot for 5d00434a
  - evolution: Fact: Plan r3 dogfooding showed that the `ActionResult.auto_executable` and `remediation` fields were still mostly write-only in the governed commit failure path. Commit failures could name a next command, but `_commit_…
- **`5d00434a`** — Refresh external review snapshot for 34c4ea42
  - evolution: Fact: Plan r3 dogfooding showed that the `ActionResult.auto_executable` and `remediation` fields were still mostly write-only in the governed commit failure path. Commit failures could name a next command, but `_commit_…
- **`34c4ea42`** — Refresh external review snapshot for 1733d2a8
  - evolution: Fact: Plan r3 dogfooding showed that the `ActionResult.auto_executable` and `remediation` fields were still mostly write-only in the governed commit failure path. Commit failures could name a next command, but `_commit_…
- **`1733d2a8` | MPs: MP-377** — Integrate packet finding stack into MP-377 plan
  - plan: `dev/active/ai_governance_platform.md`
  - evolution: Fact: the live Codex/Claude beta pass found that the Plan 4.1 `/develop` design had typed topology contracts but no `devctl develop` CLI entrypoint, so agents could not actually invoke the controller surface they were t…
- **`82d0bb3a`** — Refresh external review snapshot for 48b0e03d
  - evolution: Fact: Plan r3 dogfooding showed that the `ActionResult.auto_executable` and `remediation` fields were still mostly write-only in the governed commit failure path. Commit failures could name a next command, but `_commit_…
- **`48b0e03d`** — Refresh external review snapshot for f04275a0
  - evolution: Fact: Plan r3 dogfooding showed that the `ActionResult.auto_executable` and `remediation` fields were still mostly write-only in the governed commit failure path. Commit failures could name a next command, but `_commit_…
- **`f04275a0`** — chore(push): auto-commit preflight-generated changes
  - evolution: Fact: Plan r3 dogfooding showed that the `ActionResult.auto_executable` and `remediation` fields were still mostly write-only in the governed commit failure path. Commit failures could name a next command, but `_commit_…
- **`38c938ba`** — Refresh external review snapshot for 6ed88467
  - evolution: Fact: Plan r3 dogfooding showed that the `ActionResult.auto_executable` and `remediation` fields were still mostly write-only in the governed commit failure path. Commit failures could name a next command, but `_commit_…
- **`6ed88467`** — Refresh external review snapshot for 50ac1d8a
  - evolution: Fact: Plan r3 dogfooding showed that the `ActionResult.auto_executable` and `remediation` fields were still mostly write-only in the governed commit failure path. Commit failures could name a next command, but `_commit_…
- **`50ac1d8a`** — Refresh plan projection for automation findings
  - evolution: Fact: Plan r3 dogfooding showed that the `ActionResult.auto_executable` and `remediation` fields were still mostly write-only in the governed commit failure path. Commit failures could name a next command, but `_commit_…
- **`3d02e980`** — Refresh review snapshot after system picture update
  - evolution: Fact: Plan r3 dogfooding showed that the `ActionResult.auto_executable` and `remediation` fields were still mostly write-only in the governed commit failure path. Commit failures could name a next command, but `_commit_…
- **`93f32b7d`** — Refresh managed projection surfaces after publisher stop
  - evolution: Fact: Plan r3 dogfooding showed that the `ActionResult.auto_executable` and `remediation` fields were still mostly write-only in the governed commit failure path. Commit failures could name a next command, but `_commit_…
- **`9d05fe6c`** — Refresh managed projection surfaces after publisher update
  - evolution: Fact: Plan r3 dogfooding showed that the `ActionResult.auto_executable` and `remediation` fields were still mostly write-only in the governed commit failure path. Commit failures could name a next command, but `_commit_…
- **`b8dfb984`** — Refresh managed projection surfaces after drift repair
  - evolution: Fact: Plan r3 dogfooding showed that the `ActionResult.auto_executable` and `remediation` fields were still mostly write-only in the governed commit failure path. Commit failures could name a next command, but `_commit_…
- **`8a361a42`** — Refresh external review snapshot for f510da77
  - evolution: Fact: Plan r3 dogfooding showed that the `ActionResult.auto_executable` and `remediation` fields were still mostly write-only in the governed commit failure path. Commit failures could name a next command, but `_commit_…
- **`f510da77`** — Fix empty develop packet attention summary
  - evolution: Fact: Plan r3 dogfooding showed that the `ActionResult.auto_executable` and `remediation` fields were still mostly write-only in the governed commit failure path. Commit failures could name a next command, but `_commit_…
- **`5908bcd9`** — Refresh external review snapshot for a2c85e4a
  - evolution: Fact: Plan r3 dogfooding showed that the `ActionResult.auto_executable` and `remediation` fields were still mostly write-only in the governed commit failure path. Commit failures could name a next command, but `_commit_…
- **`a2c85e4a`** — Refresh external review snapshot for 4baabf40
  - evolution: Fact: Plan r3 dogfooding showed that the `ActionResult.auto_executable` and `remediation` fields were still mostly write-only in the governed commit failure path. Commit failures could name a next command, but `_commit_…
- **`4baabf40`** — Refresh policy-owned generated surfaces for 2cc4bd10
  - evolution: Fact: Plan r3 dogfooding showed that the `ActionResult.auto_executable` and `remediation` fields were still mostly write-only in the governed commit failure path. Commit failures could name a next command, but `_commit_…
- **`2cc4bd10`** — Refresh external review snapshot for 7a3579b1
  - evolution: Fact: Plan r3 dogfooding showed that the `ActionResult.auto_executable` and `remediation` fields were still mostly write-only in the governed commit failure path. Commit failures could name a next command, but `_commit_…
- **`7a3579b1`** — Persist launcher discipline bypass receipts
  - evolution: Fact: Plan r3 dogfooding showed that the `ActionResult.auto_executable` and `remediation` fields were still mostly write-only in the governed commit failure path. Commit failures could name a next command, but `_commit_…
- **`3ff41ec7`** — Refresh external review snapshot for 117ea0d3
  - evolution: Fact: Plan r3 dogfooding showed that the `ActionResult.auto_executable` and `remediation` fields were still mostly write-only in the governed commit failure path. Commit failures could name a next command, but `_commit_…
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
- no_push_needed: managed_projection_drift_only

### Stale warnings
- Checkpoint dirty work.
- Move straight to the governed push path.

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

Projection produced by `devctl review-snapshot`. Generation stamp `snap-713d88d1a3d3` binds this file to HEAD `8d59ccfbc2e0`; if they drift, the freshness guard will fail CI. When the latest commit only refreshes this generated snapshot, the guard accepts this file as bound to that commit's parent code state.
