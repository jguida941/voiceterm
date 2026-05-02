# VoiceTerm — Review Snapshot

> Deterministically generated from typed governance state. Do not edit by hand — rerun `devctl review-snapshot --write`.

## Quick status

- Branch: `feature/governance-quality-sweep`
- HEAD: `50ac1d8a8998` — Refresh plan projection for automation findings
- Tree hash: `70c1eced0947`
- Generation stamp: `snap-a624372ab9b2`
- Generated at (UTC): 2026-05-02T20:07:34Z
- Push decision: `run_devctl_push` — push_preconditions_satisfied
- Reviewer mode: `single_agent` (interaction: `single_agent`)
- Pipeline state: `n/a` (approval: `n/a`)
- Delta since last snapshot: 24 commits, 22 files, +2095/-1305
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
- HEAD SHA: `50ac1d8a89982cb49fc5534e710e8dae6e272f47`
- HEAD author: Justin Guida
- HEAD timestamp (UTC): 2026-05-02T16:05:15-04:00

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
- current_push_authorization: `push-auth-20260502T200524954326Z` (valid=True)
- authorized_head_commit: `50ac1d8a89982cb49fc5534e710e8dae6e272f47`
- approved_target_identity: `tree-receipt-20260502T195254207801Z:b912d337c291269169827e1c696eae3b5d215040`
- publication_backlog: urgent
- publication_guidance: 29 local commit(s) waiting for governed push. Run `python3 dev/scripts/devctl.py push --execute` now.

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

Range: last 24 commits ending at `50ac1d8a8998`

- commits: 24
- files changed: 22
- insertions: +2095
- deletions: -1305
- bundle classes touched: tooling, docs
- authority surfaces touched: 2 file(s)

### Commits

| # | SHA | Subject | Files | +/- | Bundle | Risk |
|---|---|---|---|---|---|---|
| 1 | `50ac1d8a` | Refresh plan projection for automation findings | 2 | +2/-0 | tooling |  |
| 2 | `3d02e980` | Refresh review snapshot after system picture update | 1 | +71/-97 | tooling |  |
| 3 | `93f32b7d` | Refresh managed projection surfaces after publisher stop | 3 | +5/-3 | tooling |  |
| 4 | `9d05fe6c` | Refresh managed projection surfaces after publisher update | 3 | +7/-5 | tooling |  |
| 5 | `b8dfb984` | Refresh managed projection surfaces after drift repair | 4 | +67/-55 | tooling |  |
| 6 | `8a361a42` | Refresh external review snapshot for f510da77 | 2 | +65/-69 | docs |  |
| 7 | `f510da77` | Fix empty develop packet attention summary | 11 | +160/-83 | tooling |  |
| 8 | `5908bcd9` | Refresh external review snapshot for a2c85e4a | 2 | +47/-47 | docs |  |
| 9 | `a2c85e4a` | Refresh external review snapshot for 4baabf40 | 1 | +53/-50 | tooling |  |
| 10 | `4baabf40` | Refresh policy-owned generated surfaces for 2cc4bd10 | 1 | +1/-1 | docs |  |
| 11 | `2cc4bd10` | Refresh external review snapshot for 7a3579b1 | 2 | +66/-64 | docs |  |
| 12 | `7a3579b1` | Persist launcher discipline bypass receipts | 8 | +452/-119 | tooling |  |
| 13 | `3ff41ec7` | Refresh external review snapshot for 117ea0d3 | 2 | +58/-58 | docs |  |
| 14 | `117ea0d3` | Preserve single-agent topology mode | 2 | +101/-135 | tooling |  |
| 15 | `625580af` | Refresh policy-owned generated surfaces for c3adea3a | 1 | +1/-1 | docs |  |
| 16 | `c3adea3a` | Refresh external review snapshot for ff9988fe | 2 | +57/-54 | docs |  |
| 17 | `ff9988fe` | Add failure packet router | 3 | +467/-57 | tooling |  |
| 18 | `11ede1db` | Refresh external review snapshot for 492a2f37 | 2 | +64/-78 | docs |  |
| 19 | `492a2f37` | drift before reviewer launch | 4 | +57/-49 | tooling |  |
| 20 | `be1a3a04` | Refresh external review snapshot for be2c47c0 | 2 | +58/-59 | docs |  |
| 21 | `be2c47c0` | Refresh managed projection surfaces (terminal-app launch pr… | 4 | +56/-51 | tooling |  |
| 22 | `dfeb010d` | Refresh external review snapshot for 007b574f | 2 | +59/-60 | docs |  |
| 23 | `007b574f` | Refresh managed projection surfaces (single_agent launch pr… | 4 | +60/-56 | tooling |  |
| 24 | `3b643953` | Refresh managed projection surfaces (post-9537766e follow-u… | 3 | +61/-54 | tooling |  |

### Files

| Path | Bundle | +/- |
|---|---|---|
| `AGENTS.md` | docs | +1/-0 |
| `bridge.md` | docs | +58/-60 |
| `dev/active/MASTER_PLAN.md` | tooling | +15/-0 |
| `dev/audits/REVIEW_SNAPSHOT.md` | tooling | +1141/-1217 |
| `dev/guides/DEVELOPMENT.md` | docs | +4/-0 |
| `dev/guides/SYSTEM_MAP.md` | docs | +2/-2 |
| `dev/history/ENGINEERING_EVOLUTION.md` | tooling | +36/-0 |
| `dev/scripts/README.md` | tooling | +5/-0 |
| `dev/scripts/devctl/commands/development/models.py` | tooling | +4/-1 |
| `dev/scripts/devctl/commands/development/packet_attention.py` | tooling | +4/-1 |
| `dev/scripts/devctl/commands/review_channel/_recover.py` | tooling | +14/-2 |
| `dev/scripts/devctl/commands/review_channel/bridge_handler.py` | tooling | +10/-2 |
| `dev/scripts/devctl/commands/review_channel/bridge_launch_control.py` | tooling | +9/-2 |
| `dev/scripts/devctl/commands/review_channel/launcher_discipline.py` | tooling | +68/-10 |
| `dev/scripts/devctl/commands/review_channel/launcher_discipline_receipts.py` | tooling | +81/-0 |
| `dev/scripts/devctl/review_channel/collaboration_session_coordination.py` | tooling | +10/-8 |
| `dev/scripts/devctl/review_channel/failure_packet_router.py` | tooling | +212/-0 |
| `dev/scripts/devctl/review_channel/recover_support.py` | tooling | +1/-0 |
| `dev/scripts/devctl/tests/commands/test_development_command.py` | tooling | +18/-0 |
| `dev/scripts/devctl/tests/review_channel/test_failure_packet_router.py` | tooling | +204/-0 |
| `dev/scripts/devctl/tests/review_channel/test_launcher_discipline_bypass_receipt.py` | tooling | +182/-0 |
| `dev/state/plan_index.jsonl` | tooling | +16/-0 |

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

- **`50ac1d8a`** — Refresh plan projection for automation findings
  - evolution: Fact: Codex/Claude MP-377 dogfooding found three control-plane gaps in the same launch/review handoff lane. Development-mode launcher bypasses could return a typed `LauncherDisciplineBypass` receipt without any durable …
- **`3d02e980`** — Refresh review snapshot after system picture update
  - evolution: Fact: Codex/Claude MP-377 dogfooding found three control-plane gaps in the same launch/review handoff lane. Development-mode launcher bypasses could return a typed `LauncherDisciplineBypass` receipt without any durable …
- **`93f32b7d`** — Refresh managed projection surfaces after publisher stop
  - evolution: Fact: Codex/Claude MP-377 dogfooding found three control-plane gaps in the same launch/review handoff lane. Development-mode launcher bypasses could return a typed `LauncherDisciplineBypass` receipt without any durable …
- **`9d05fe6c`** — Refresh managed projection surfaces after publisher update
  - evolution: Fact: Codex/Claude MP-377 dogfooding found three control-plane gaps in the same launch/review handoff lane. Development-mode launcher bypasses could return a typed `LauncherDisciplineBypass` receipt without any durable …
- **`b8dfb984`** — Refresh managed projection surfaces after drift repair
  - evolution: Fact: Codex/Claude MP-377 dogfooding found three control-plane gaps in the same launch/review handoff lane. Development-mode launcher bypasses could return a typed `LauncherDisciplineBypass` receipt without any durable …
- **`8a361a42`** — Refresh external review snapshot for f510da77
  - evolution: Fact: Codex/Claude MP-377 dogfooding found three control-plane gaps in the same launch/review handoff lane. Development-mode launcher bypasses could return a typed `LauncherDisciplineBypass` receipt without any durable …
- **`f510da77`** — Fix empty develop packet attention summary
  - evolution: Fact: Codex/Claude MP-377 dogfooding found three control-plane gaps in the same launch/review handoff lane. Development-mode launcher bypasses could return a typed `LauncherDisciplineBypass` receipt without any durable …
- **`5908bcd9`** — Refresh external review snapshot for a2c85e4a
  - evolution: Fact: Codex/Claude MP-377 dogfooding found three control-plane gaps in the same launch/review handoff lane. Development-mode launcher bypasses could return a typed `LauncherDisciplineBypass` receipt without any durable …
- **`a2c85e4a`** — Refresh external review snapshot for 4baabf40
  - evolution: Fact: Codex/Claude MP-377 dogfooding found three control-plane gaps in the same launch/review handoff lane. Development-mode launcher bypasses could return a typed `LauncherDisciplineBypass` receipt without any durable …
- **`4baabf40`** — Refresh policy-owned generated surfaces for 2cc4bd10
  - evolution: Fact: Codex/Claude MP-377 dogfooding found three control-plane gaps in the same launch/review handoff lane. Development-mode launcher bypasses could return a typed `LauncherDisciplineBypass` receipt without any durable …
- **`2cc4bd10`** — Refresh external review snapshot for 7a3579b1
  - evolution: Fact: Codex/Claude MP-377 dogfooding found three control-plane gaps in the same launch/review handoff lane. Development-mode launcher bypasses could return a typed `LauncherDisciplineBypass` receipt without any durable …
- **`7a3579b1`** — Persist launcher discipline bypass receipts
  - evolution: Fact: Codex/Claude MP-377 dogfooding found three control-plane gaps in the same launch/review handoff lane. Development-mode launcher bypasses could return a typed `LauncherDisciplineBypass` receipt without any durable …
- **`3ff41ec7`** — Refresh external review snapshot for 117ea0d3
  - evolution: Fact: Codex/Claude MP-377 dogfooding found three control-plane gaps in the same launch/review handoff lane. Development-mode launcher bypasses could return a typed `LauncherDisciplineBypass` receipt without any durable …
- **`117ea0d3`** — Preserve single-agent topology mode
  - evolution: Fact: Codex/Claude MP-377 dogfooding found three control-plane gaps in the same launch/review handoff lane. Development-mode launcher bypasses could return a typed `LauncherDisciplineBypass` receipt without any durable …
- **`625580af`** — Refresh policy-owned generated surfaces for c3adea3a
  - evolution: Fact: Codex/Claude MP-377 dogfooding found three control-plane gaps in the same launch/review handoff lane. Development-mode launcher bypasses could return a typed `LauncherDisciplineBypass` receipt without any durable …
- **`c3adea3a`** — Refresh external review snapshot for ff9988fe
  - evolution: Fact: Codex/Claude MP-377 dogfooding found three control-plane gaps in the same launch/review handoff lane. Development-mode launcher bypasses could return a typed `LauncherDisciplineBypass` receipt without any durable …
- **`ff9988fe`** — Add failure packet router
  - evolution: Fact: Codex/Claude MP-377 dogfooding found three control-plane gaps in the same launch/review handoff lane. Development-mode launcher bypasses could return a typed `LauncherDisciplineBypass` receipt without any durable …
- **`11ede1db`** — Refresh external review snapshot for 492a2f37
  - evolution: Fact: Codex/Claude MP-377 dogfooding found three control-plane gaps in the same launch/review handoff lane. Development-mode launcher bypasses could return a typed `LauncherDisciplineBypass` receipt without any durable …
- **`492a2f37`** — drift before reviewer launch
  - evolution: Fact: Codex/Claude MP-377 dogfooding found three control-plane gaps in the same launch/review handoff lane. Development-mode launcher bypasses could return a typed `LauncherDisciplineBypass` receipt without any durable …
- **`be1a3a04`** — Refresh external review snapshot for be2c47c0
  - evolution: Fact: Codex/Claude MP-377 dogfooding found three control-plane gaps in the same launch/review handoff lane. Development-mode launcher bypasses could return a typed `LauncherDisciplineBypass` receipt without any durable …
- **`be2c47c0` | MPs: MP-377** — Refresh managed projection surfaces (terminal-app launch prep)
  - Anchors: section:MP-377
  - plan: `dev/active/ai_governance_platform.md`
  - evolution: Fact: the live Codex/Claude beta pass found that the Plan 4.1 `/develop` design had typed topology contracts but no `devctl develop` CLI entrypoint, so agents could not actually invoke the controller surface they were t…
- **`dfeb010d`** — Refresh external review snapshot for 007b574f
  - evolution: Fact: Codex/Claude MP-377 dogfooding found three control-plane gaps in the same launch/review handoff lane. Development-mode launcher bypasses could return a typed `LauncherDisciplineBypass` receipt without any durable …
- **`007b574f` | MPs: MP-377** — Refresh managed projection surfaces (single_agent launch prep)
  - Anchors: section:MP-377
  - plan: `dev/active/ai_governance_platform.md`
  - evolution: Fact: the live Codex/Claude beta pass found that the Plan 4.1 `/develop` design had typed topology contracts but no `devctl develop` CLI entrypoint, so agents could not actually invoke the controller surface they were t…
- **`3b643953` | MPs: MP-377** — Refresh managed projection surfaces (post-9537766e follow-up)
  - Standard auto-regenerated drift cleanup per typed
  - recommended_action=commit_before_push. Unblocks fresh Codex
  - session launch so his investigation agents can pick up rev_pkt_2779
  - plan: `dev/active/ai_governance_platform.md`
  - evolution: Fact: the live Codex/Claude beta pass found that the Plan 4.1 `/develop` design had typed topology contracts but no `devctl develop` CLI entrypoint, so agents could not actually invoke the controller surface they were t…
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

Projection produced by `devctl review-snapshot`. Generation stamp `snap-a624372ab9b2` binds this file to HEAD `50ac1d8a8998`; if they drift, the freshness guard will fail CI. When the latest commit only refreshes this generated snapshot, the guard accepts this file as bound to that commit's parent code state.
