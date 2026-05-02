# VoiceTerm — Review Snapshot

> Deterministically generated from typed governance state. Do not edit by hand — rerun `devctl review-snapshot --write`.

## Quick status

- Branch: `feature/governance-quality-sweep`
- HEAD: `4baabf40eb22` — Refresh policy-owned generated surfaces for 2cc4bd10
- Tree hash: `3e4f1548695f`
- Generation stamp: `snap-101bbc1a9cac`
- Generated at (UTC): 2026-05-02T19:10:52Z
- Push decision: `run_devctl_push` — push_preconditions_satisfied
- Reviewer mode: `single_agent` (interaction: `single_agent`)
- Pipeline state: `n/a` (approval: `n/a`)
- Delta since last snapshot: 24 commits, 49 files, +4194/-1440
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
- HEAD SHA: `4baabf40eb22523f78573289cf5fde9a554eac25`
- HEAD author: Justin Guida
- HEAD timestamp (UTC): 2026-05-02T15:10:30-04:00

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
- current_push_authorization: `push-auth-20260502T190847186600Z` (valid=True)
- authorized_head_commit: `2cc4bd100e3ee21178b2e9f8307446bee7d3bdf6`
- approved_target_identity: `tree-receipt-20260502T190847186600Z:d35559bc6542701e8b24ad296b7baa4603275dd3`
- publication_backlog: urgent
- publication_guidance: 20 local commit(s) waiting for governed push. Run `python3 dev/scripts/devctl.py push --execute` now.

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

Range: last 24 commits ending at `4baabf40eb22`

- commits: 24
- files changed: 49
- insertions: +4194
- deletions: -1440
- bundle classes touched: docs, tooling
- authority surfaces touched: 4 file(s)

### Commits

| # | SHA | Subject | Files | +/- | Bundle | Risk |
|---|---|---|---|---|---|---|
| 1 | `4baabf40` | Refresh policy-owned generated surfaces for 2cc4bd10 | 1 | +1/-1 | docs |  |
| 2 | `2cc4bd10` | Refresh external review snapshot for 7a3579b1 | 2 | +66/-64 | docs |  |
| 3 | `7a3579b1` | Persist launcher discipline bypass receipts | 8 | +452/-119 | tooling |  |
| 4 | `3ff41ec7` | Refresh external review snapshot for 117ea0d3 | 2 | +58/-58 | docs |  |
| 5 | `117ea0d3` | Preserve single-agent topology mode | 2 | +101/-135 | tooling |  |
| 6 | `625580af` | Refresh policy-owned generated surfaces for c3adea3a | 1 | +1/-1 | docs |  |
| 7 | `c3adea3a` | Refresh external review snapshot for ff9988fe | 2 | +57/-54 | docs |  |
| 8 | `ff9988fe` | Add failure packet router | 3 | +467/-57 | tooling |  |
| 9 | `11ede1db` | Refresh external review snapshot for 492a2f37 | 2 | +64/-78 | docs |  |
| 10 | `492a2f37` | drift before reviewer launch | 4 | +57/-49 | tooling |  |
| 11 | `be1a3a04` | Refresh external review snapshot for be2c47c0 | 2 | +58/-59 | docs |  |
| 12 | `be2c47c0` | Refresh managed projection surfaces (terminal-app launch pr… | 4 | +56/-51 | tooling |  |
| 13 | `dfeb010d` | Refresh external review snapshot for 007b574f | 2 | +59/-60 | docs |  |
| 14 | `007b574f` | Refresh managed projection surfaces (single_agent launch pr… | 4 | +60/-56 | tooling |  |
| 15 | `3b643953` | Refresh managed projection surfaces (post-9537766e follow-u… | 3 | +61/-54 | tooling |  |
| 16 | `a8a150d1` | Refresh external review snapshot for 9537766e | 2 | +60/-59 | docs |  |
| 17 | `9537766e` | Refresh managed projection surfaces (post-7f4b5bf4 follow-u… | 3 | +61/-56 | tooling |  |
| 18 | `08d33a43` | Refresh policy-owned generated surfaces for 4fc6a797 | 1 | +1/-1 | docs |  |
| 19 | `4fc6a797` | Refresh external review snapshot for 7f4b5bf4 | 2 | +68/-64 | docs |  |
| 20 | `7f4b5bf4` | Wake-binding slice + auto-dispatcher prep refactor (T22AN-C… | 29 | +1824/-171 | tooling |  |
| 21 | `b06b38b4` | Refresh policy-owned generated surfaces for e61fdda3 | 1 | +1/-1 | docs |  |
| 22 | `e61fdda3` | Refresh external review snapshot for 1fcceafa | 2 | +76/-90 | docs |  |
| 23 | `1fcceafa` | Protect review-channel monitors from cleanup | 11 | +440/-57 | tooling |  |
| 24 | `4a77272a` | Refresh external review snapshot for 05425b97 | 2 | +45/-45 | docs |  |

### Files

| Path | Bundle | +/- |
|---|---|---|
| `bridge.md` | docs | +47/-49 |
| `dev/active/MASTER_PLAN.md` | tooling | +18/-0 |
| `dev/active/ai_governance_platform.md` | tooling | +4/-0 |
| `dev/audits/REVIEW_SNAPSHOT.md` | tooling | +1186/-1243 |
| `dev/guides/SYSTEM_MAP.md` | docs | +4/-4 |
| `dev/history/ENGINEERING_EVOLUTION.md` | tooling | +56/-1 |
| `dev/scripts/README.md` | tooling | +34/-2 |
| `dev/scripts/devctl/commands/check/process_sweep.py` | tooling | +33/-1 |
| `dev/scripts/devctl/commands/development/actor_resolution.py` | tooling | +52/-4 |
| `dev/scripts/devctl/commands/development/models.py` | tooling | +2/-0 |
| `dev/scripts/devctl/commands/development/next_slice.py` | tooling | +17/-3 |
| `dev/scripts/devctl/commands/development/packet_attention.py` | tooling | +97/-5 |
| `dev/scripts/devctl/commands/development/render.py` | tooling | +3/-0 |
| `dev/scripts/devctl/commands/governance/hygiene_render.py` | tooling | +4/-0 |
| `dev/scripts/devctl/commands/governance/hygiene_support.py` | tooling | +11/-1 |
| `dev/scripts/devctl/commands/process/audit.py` | tooling | +17/-1 |
| `dev/scripts/devctl/commands/review_channel/_recover.py` | tooling | +14/-2 |
| `dev/scripts/devctl/commands/review_channel/bridge_handler.py` | tooling | +10/-2 |
| `dev/scripts/devctl/commands/review_channel/bridge_launch_control.py` | tooling | +9/-2 |
| `dev/scripts/devctl/commands/review_channel/bridge_launch_headless.py` | tooling | +14/-0 |
| `dev/scripts/devctl/commands/review_channel/event_post_wake.py` | tooling | +62/-18 |
| `dev/scripts/devctl/commands/review_channel/launcher_discipline.py` | tooling | +68/-10 |
| `dev/scripts/devctl/commands/review_channel/launcher_discipline_receipts.py` | tooling | +81/-0 |
| `dev/scripts/devctl/commands/review_channel/wake_receipt_persistence.py` | tooling | +168/-0 |
| `dev/scripts/devctl/process_sweep/review_channel_monitors.py` | tooling | +51/-0 |
| `dev/scripts/devctl/review_channel/agent_wake_dispatch.py` | tooling | +211/-0 |
| `dev/scripts/devctl/review_channel/collaboration_session_coordination.py` | tooling | +10/-8 |
| `dev/scripts/devctl/review_channel/event_models.py` | tooling | +1/-0 |
| `dev/scripts/devctl/review_channel/event_packet_rows.py` | tooling | +23/-0 |
| `dev/scripts/devctl/review_channel/event_reducer.py` | tooling | +2/-0 |
| `dev/scripts/devctl/review_channel/event_render.py` | tooling | +52/-0 |
| `dev/scripts/devctl/review_channel/failure_packet_router.py` | tooling | +212/-0 |
| `dev/scripts/devctl/review_channel/follow_controller.py` | tooling | +24/-52 |
| `dev/scripts/devctl/review_channel/headless_delegate.py` | tooling | +69/-0 |
| `dev/scripts/devctl/review_channel/recover_support.py` | tooling | +1/-0 |
| `dev/scripts/devctl/review_channel/reviewer_follow_guard.py` | tooling | +58/-28 |
| `dev/scripts/devctl/review_channel/wake_receipt_models.py` | tooling | +102/-0 |
| `dev/scripts/devctl/tests/commands/process/test_process_audit.py` | tooling | +101/-0 |
| `dev/scripts/devctl/tests/commands/test_development_command.py` | tooling | +199/-0 |
| `dev/scripts/devctl/tests/governance/test_hygiene.py` | tooling | +75/-0 |
| _9 more files trimmed_ | | |

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
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/review_channel/bridge_launch_headless.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/review_channel/reviewer_follow_guard.py`) — Review contract-level invariants for this file
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/review_channel/event_models.py`) — Commit 7f4b5bf4 changed dev/scripts/devctl/review_channel/event_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/review_channel/wake_receipt_models.py`) — Commit 7f4b5bf4 changed dev/scripts/devctl/review_channel/wake_receipt_models.py

### Suggested verification commands

- `python3 dev/scripts/devctl.py check --profile ci`
- `python3 dev/scripts/devctl.py probe-report --format md`
- `python3 dev/scripts/devctl.py docs-check --strict-tooling`
- `python3 dev/scripts/devctl.py governance-review --format md`
- `python3 dev/scripts/devctl.py check-router --format md`

## 7. Reasoning — why these changes landed

### Per-commit rationale

- **`4baabf40`** — Refresh policy-owned generated surfaces for 2cc4bd10
  - evolution: Fact: Codex/Claude `/develop` dogfooding exposed a bad split between typed queue truth and wake truth. A provider-to-provider `system_notice` could sit in the pending queue and count in runtime sync state, while `/devel…
- **`2cc4bd10`** — Refresh external review snapshot for 7a3579b1
  - evolution: Fact: Codex/Claude `/develop` dogfooding exposed a bad split between typed queue truth and wake truth. A provider-to-provider `system_notice` could sit in the pending queue and count in runtime sync state, while `/devel…
- **`7a3579b1`** — Persist launcher discipline bypass receipts
  - evolution: Fact: Codex/Claude `/develop` dogfooding exposed a bad split between typed queue truth and wake truth. A provider-to-provider `system_notice` could sit in the pending queue and count in runtime sync state, while `/devel…
- **`3ff41ec7`** — Refresh external review snapshot for 117ea0d3
  - evolution: Fact: Codex/Claude `/develop` dogfooding exposed a bad split between typed queue truth and wake truth. A provider-to-provider `system_notice` could sit in the pending queue and count in runtime sync state, while `/devel…
- **`117ea0d3`** — Preserve single-agent topology mode
  - evolution: Fact: Codex/Claude `/develop` dogfooding exposed a bad split between typed queue truth and wake truth. A provider-to-provider `system_notice` could sit in the pending queue and count in runtime sync state, while `/devel…
- **`625580af`** — Refresh policy-owned generated surfaces for c3adea3a
  - evolution: Fact: Codex/Claude `/develop` dogfooding exposed a bad split between typed queue truth and wake truth. A provider-to-provider `system_notice` could sit in the pending queue and count in runtime sync state, while `/devel…
- **`c3adea3a`** — Refresh external review snapshot for ff9988fe
  - evolution: Fact: Codex/Claude `/develop` dogfooding exposed a bad split between typed queue truth and wake truth. A provider-to-provider `system_notice` could sit in the pending queue and count in runtime sync state, while `/devel…
- **`ff9988fe`** — Add failure packet router
  - evolution: Fact: Codex/Claude `/develop` dogfooding exposed a bad split between typed queue truth and wake truth. A provider-to-provider `system_notice` could sit in the pending queue and count in runtime sync state, while `/devel…
- **`11ede1db`** — Refresh external review snapshot for 492a2f37
  - evolution: Fact: Codex/Claude `/develop` dogfooding exposed a bad split between typed queue truth and wake truth. A provider-to-provider `system_notice` could sit in the pending queue and count in runtime sync state, while `/devel…
- **`492a2f37`** — drift before reviewer launch
  - evolution: Fact: Codex/Claude `/develop` dogfooding exposed a bad split between typed queue truth and wake truth. A provider-to-provider `system_notice` could sit in the pending queue and count in runtime sync state, while `/devel…
- **`be1a3a04`** — Refresh external review snapshot for be2c47c0
  - evolution: Fact: Codex/Claude `/develop` dogfooding exposed a bad split between typed queue truth and wake truth. A provider-to-provider `system_notice` could sit in the pending queue and count in runtime sync state, while `/devel…
- **`be2c47c0` | MPs: MP-377** — Refresh managed projection surfaces (terminal-app launch prep)
  - Anchors: section:MP-377
  - plan: `dev/active/ai_governance_platform.md`
  - evolution: Fact: the live Codex/Claude beta pass found that the Plan 4.1 `/develop` design had typed topology contracts but no `devctl develop` CLI entrypoint, so agents could not actually invoke the controller surface they were t…
- **`dfeb010d`** — Refresh external review snapshot for 007b574f
  - evolution: Fact: Codex/Claude `/develop` dogfooding exposed a bad split between typed queue truth and wake truth. A provider-to-provider `system_notice` could sit in the pending queue and count in runtime sync state, while `/devel…
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
- **`a8a150d1`** — Refresh external review snapshot for 9537766e
  - evolution: Fact: Codex/Claude `/develop` dogfooding exposed a bad split between typed queue truth and wake truth. A provider-to-provider `system_notice` could sit in the pending queue and count in runtime sync state, while `/devel…
- **`9537766e` | MPs: MP-377** — Refresh managed projection surfaces (post-7f4b5bf4 follow-up)
  - Auto-regenerated after the wake-binding slice + auto-dispatcher prep
  - refactor commit. Per startup-authority typed gate
  - recommended_action=commit_before_push, committing these projection
  - plan: `dev/active/ai_governance_platform.md`
  - evolution: Fact: the live Codex/Claude beta pass found that the Plan 4.1 `/develop` design had typed topology contracts but no `devctl develop` CLI entrypoint, so agents could not actually invoke the controller surface they were t…
- **`08d33a43`** — Refresh policy-owned generated surfaces for 4fc6a797
  - evolution: Fact: Codex/Claude `/develop` dogfooding exposed a bad split between typed queue truth and wake truth. A provider-to-provider `system_notice` could sit in the pending queue and count in runtime sync state, while `/devel…
- **`4fc6a797`** — Refresh external review snapshot for 7f4b5bf4
  - evolution: Fact: Codex/Claude `/develop` dogfooding exposed a bad split between typed queue truth and wake truth. A provider-to-provider `system_notice` could sit in the pending queue and count in runtime sync state, while `/devel…
- **`7f4b5bf4` | MPs: MP-377** — Wake-binding slice + auto-dispatcher prep refactor (T22AN-C/F + plan revision r2 prep)
  - Operator-authorized scope: 'commit and push the wake-binding slice from the
  - dashboard' (2026-05-02T14:35Z) + 'Codex reviews and you code' role flip.
  - plan: `dev/active/ai_governance_platform.md`
  - evolution: Fact: the live Codex/Claude beta pass found that the Plan 4.1 `/develop` design had typed topology contracts but no `devctl develop` CLI entrypoint, so agents could not actually invoke the controller surface they were t…
- **`b06b38b4`** — Refresh policy-owned generated surfaces for e61fdda3
  - evolution: Fact: Codex/Claude `/develop` dogfooding exposed a bad split between typed queue truth and wake truth. A provider-to-provider `system_notice` could sit in the pending queue and count in runtime sync state, while `/devel…
- **`e61fdda3`** — Refresh external review snapshot for 1fcceafa
  - evolution: Fact: Codex/Claude `/develop` dogfooding exposed a bad split between typed queue truth and wake truth. A provider-to-provider `system_notice` could sit in the pending queue and count in runtime sync state, while `/devel…
- **`1fcceafa`** — Protect review-channel monitors from cleanup
  - evolution: Fact: Codex/Claude `/develop` dogfooding exposed a bad split between typed queue truth and wake truth. A provider-to-provider `system_notice` could sit in the pending queue and count in runtime sync state, while `/devel…
- **`4a77272a`** — Refresh external review snapshot for 05425b97
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

Projection produced by `devctl review-snapshot`. Generation stamp `snap-101bbc1a9cac` binds this file to HEAD `4baabf40eb22`; if they drift, the freshness guard will fail CI. When the latest commit only refreshes this generated snapshot, the guard accepts this file as bound to that commit's parent code state.
