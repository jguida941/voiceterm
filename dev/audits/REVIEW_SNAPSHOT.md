# VoiceTerm — Review Snapshot

> Deterministically generated from typed governance state. Do not edit by hand — rerun `devctl review-snapshot --write`.

## Quick status

- Branch: `extraction/guardir-core-p0-proof-integrity`
- HEAD: `a4e1ef0bf7d3` — Phase 0.6D: authorize remote-lane review-channel posts
- Tree hash: `53b027776ac8`
- Generation stamp: `snap-528137739c1c`
- Generated at (UTC): 2026-05-19T13:30:09Z
- Push decision: `run_devctl_push` — push_preconditions_satisfied
- Reviewer mode: `tools_only` (interaction: `local_terminal`)
- Pipeline state: `n/a` (approval: `n/a`)
- Delta since last snapshot: 24 commits, 62 files, +4020/-2004
- Governance findings: 27 open / 0 fixed / 27 total
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
- HEAD SHA: `a4e1ef0bf7d37895d574b3201affbbd38a3d8e30`
- HEAD author: Justin Guida
- HEAD timestamp (UTC): 2026-05-19T09:29:47-04:00

## 2. Governance state

### Push decision
- action: `run_devctl_push`
- reason: push_preconditions_satisfied
- push_eligible_now: True
- worktree_clean: True
- staged_path_count: 0
- unstaged_path_count: 0
- next_step_command: `python3 dev/scripts/devctl.py push --execute`
- latest_push_report_state: `blocked` (push_preflight_running)
- publication_backlog: queued
- publication_guidance: Local branch still has unpublished work waiting for governed push. Run `python3 dev/scripts/devctl.py push --execute` now.

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
- advisory: `no_push_needed` — clean_worktree

## 3. Delta — what changed since the previous snapshot

Range: last 24 commits ending at `a4e1ef0bf7d3`

- commits: 24
- files changed: 62
- insertions: +4020
- deletions: -2004
- bundle classes touched: tooling, docs
- authority surfaces touched: 1 file(s)

### Commits

| # | SHA | Subject | Files | +/- | Bundle | Risk |
|---|---|---|---|---|---|---|
| 1 | `a4e1ef0b` | Phase 0.6D: authorize remote-lane review-channel posts | 10 | +156/-2 | tooling |  |
| 2 | `8425c4da` | Refresh external review snapshot for 3c61f60b | 1 | +52/-52 | tooling |  |
| 3 | `3c61f60b` | Phase 0.6D: keep ingested packet bodies out of next selecti… | 5 | +68/-1 | tooling |  |
| 4 | `cdb1424c` | Refresh external review snapshot for 40f6977a | 1 | +68/-59 | tooling |  |
| 5 | `40f6977a` | Phase 0.6C: guard bridge projection and topology artifacts | 24 | +1012/-4 | tooling |  |
| 6 | `aa848fbd` | Refresh external review snapshot for fbd2993e | 1 | +51/-51 | tooling |  |
| 7 | `fbd2993e` | Record ground truth receipt for Phase 0.6A push | 2 | +62/-64 | tooling |  |
| 8 | `cba89fef` | Refresh external review snapshot for f1d053be | 1 | +67/-60 | tooling |  |
| 9 | `f1d053be` | Phase 0.6A: fix packet attention lifecycle routing | 18 | +935/-478 | tooling |  |
| 10 | `81045581` | Refresh external review snapshot for bd76e5a8 | 1 | +58/-56 | tooling |  |
| 11 | `bd76e5a8` | Fix push preflight artifact receipt suppression | 10 | +128/-61 | tooling |  |
| 12 | `2a3787c9` | Refresh external review snapshot for b6a19290 | 1 | +51/-49 | tooling |  |
| 13 | `b6a19290` | Fix push preflight artifact receipt loop | 3 | +68/-71 | tooling |  |
| 14 | `d30618cc` | Refresh external review snapshot for f8b35641 | 1 | +48/-48 | tooling |  |
| 15 | `f8b35641` | Record push preflight artifact receipt | 2 | +59/-61 | tooling |  |
| 16 | `3a98de57` | Refresh external review snapshot for 9471fad2 | 1 | +59/-57 | tooling |  |
| 17 | `9471fad2` | Keep bridge projection guard out of checks root | 10 | +438/-389 | tooling |  |
| 18 | `9a5d3788` | Refresh external review snapshot for ba8eb11f | 1 | +49/-48 | tooling |  |
| 19 | `ba8eb11f` | Record ground-truth probe receipt for GuardIR push | 2 | +63/-60 | tooling |  |
| 20 | `94b93673` | Refresh policy-owned generated surfaces for 1e4a96f7 | 1 | +1/-1 | docs |  |
| 21 | `1e4a96f7` | Refresh external review snapshot for 9ea2c912 | 1 | +65/-69 | tooling |  |
| 22 | `9ea2c912` | Keep bridge report under shape budget | 3 | +93/-78 | tooling |  |
| 23 | `2b0756d3` | Refresh external review snapshot for efc7f761 | 1 | +62/-62 | tooling |  |
| 24 | `efc7f761` | Fix package layout root-scoped ratchet | 10 | +307/-123 | tooling |  |

### Files

| Path | Bundle | +/- |
|---|---|---|
| `.github/workflows/release_preflight.yml` | tooling | +3/-0 |
| `.github/workflows/tooling_control_plane.yml` | tooling | +9/-0 |
| `AGENTS.md` | docs | +1/-1 |
| `dev/active/MASTER_PLAN.md` | tooling | +23/-2 |
| `dev/active/ai_governance_platform.md` | tooling | +17/-1 |
| `dev/audits/REVIEW_SNAPSHOT.md` | tooling | +1145/-1146 |
| `dev/config/cognitive_role_fleet.json` | tooling | +14/-0 |
| `dev/guides/DEVELOPMENT.md` | docs | +27/-3 |
| `dev/guides/SYSTEM_MAP.md` | docs | +5/-5 |
| `dev/history/ENGINEERING_EVOLUTION.md` | tooling | +101/-0 |
| `dev/scripts/README.md` | tooling | +25/-3 |
| `dev/scripts/checks/bridge_projection_only/__init__.py` | tooling | +2/-0 |
| `dev/scripts/checks/bridge_projection_only/command.py` | tooling | +330/-0 |
| `dev/scripts/checks/check_bridge_projection_only.py` | tooling | +6/-319 |
| `dev/scripts/checks/check_guardir_extraction_plan_artifacts.py` | tooling | +8/-0 |
| `dev/scripts/checks/check_no_new_hardcoded_provider_authority.py` | tooling | +12/-0 |
| `dev/scripts/checks/check_no_new_topology_count_coupling.py` | tooling | +12/-0 |
| `dev/scripts/checks/guardir_extraction_plan_artifacts/__init__.py` | tooling | +1/-0 |
| `dev/scripts/checks/guardir_extraction_plan_artifacts/command.py` | tooling | +190/-0 |
| `dev/scripts/checks/package_layout/command.py` | tooling | +169/-73 |
| `dev/scripts/checks/review_channel_bridge/projection_stub.py` | tooling | +34/-0 |
| `dev/scripts/checks/review_channel_bridge/report.py` | tooling | +8/-27 |
| `dev/scripts/checks/topology_hardcode/__init__.py` | tooling | +1/-0 |
| `dev/scripts/checks/topology_hardcode/command.py` | tooling | +311/-0 |
| `dev/scripts/devctl/bundles/registry.py` | tooling | +3/-0 |
| `dev/scripts/devctl/cli_parser/artifact_suppression.py` | tooling | +11/-0 |
| `dev/scripts/devctl/cli_parser/entrypoint.py` | tooling | +12/-2 |
| `dev/scripts/devctl/commands/check/router_python_tests.py` | tooling | +30/-0 |
| `dev/scripts/devctl/commands/development/packet_attention.py` | tooling | +19/-85 |
| `dev/scripts/devctl/commands/development/packet_attention_body_followup.py` | tooling | +235/-1 |
| `dev/scripts/devctl/commands/review_channel/status_bridge_sync.py` | tooling | +10/-2 |
| `dev/scripts/devctl/governance/instruction_boot_card.py` | tooling | +1/-1 |
| `dev/scripts/devctl/governance/push_routing.py` | tooling | +6/-2 |
| `dev/scripts/devctl/governance/script_catalog_registry.py` | tooling | +12/-0 |
| `dev/scripts/devctl/quality_policy/defaults.py` | tooling | +18/-0 |
| `dev/scripts/devctl/review_channel/bridge_projection.py` | tooling | +9/-0 |
| `dev/scripts/devctl/review_channel/current_session_support.py` | tooling | +2/-0 |
| `dev/scripts/devctl/review_channel/packet_semantic_action_items.py` | tooling | +15/-0 |
| `dev/scripts/devctl/review_channel/parser_query_arguments.py` | tooling | +8/-0 |
| `dev/scripts/devctl/review_channel/state.py` | tooling | +7/-1 |
| _22 more files trimmed_ | | |

## 4. Quality signals

### Governance review
- total findings: 27
- open: 27
- fixed: 0
- false positives: 0

Recent findings:
- `dogfood.command.process-cleanup` — `dev/scripts/devctl/commands/process/cleanup.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.install-git-hooks` — `dev/scripts/devctl/commands/governance/install_git_hooks.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.relaunch-loop` — `dev/scripts/devctl/commands/relaunch_loop.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.relaunch-loop` — `dev/scripts/devctl/commands/governance/relaunch_loop.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.render-surfaces` — `dev/scripts/devctl/commands/governance/render_surfaces.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.remote-control` — `dev/scripts/devctl/commands/remote_control/command.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.probe-report` — `dev/scripts/devctl/commands/probe_report.py` (n/a, verdict=`confirmed_issue`)
- `role_oriented_packet_inbox` — `dev/scripts/devctl/review_channel/event_reducer_inbox.py` (high, verdict=`confirmed_issue`)
- `dogfood.command.reports-cleanup` — `dev/scripts/devctl/commands/reports_cleanup.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.agent-mind` — `dev/scripts/devctl/commands/agent_mind/command.py` (n/a, verdict=`confirmed_issue`)

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

- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/review_channel/bridge_projection.py`) — Review contract-level invariants for this file

### Suggested verification commands

- `python3 dev/scripts/devctl.py check --profile ci`
- `python3 dev/scripts/devctl.py probe-report --format md`
- `python3 dev/scripts/devctl.py docs-check --strict-tooling`
- `python3 dev/scripts/devctl.py governance-review --format md`
- `python3 dev/scripts/devctl.py check-router --format md`

## 7. Reasoning — why these changes landed

### Per-commit rationale

- **`a4e1ef0b`** — Phase 0.6D: authorize remote-lane review-channel posts
  - evolution: The GuardIR extraction checkpoint exposed a live-controller gap: parser and alias parity could pass while the governed `review-channel` path still hid actor-addressed packets, disclosed packet bodies before failing the …
- **`8425c4da`** — Refresh external review snapshot for 3c61f60b
  - evolution: The GuardIR extraction checkpoint exposed a live-controller gap: parser and alias parity could pass while the governed `review-channel` path still hid actor-addressed packets, disclosed packet bodies before failing the …
- **`3c61f60b`** — Phase 0.6D: keep ingested packet bodies out of next selection
  - evolution: The GuardIR extraction checkpoint exposed a live-controller gap: parser and alias parity could pass while the governed `review-channel` path still hid actor-addressed packets, disclosed packet bodies before failing the …
- **`cdb1424c`** — Refresh external review snapshot for 40f6977a
  - evolution: The GuardIR extraction checkpoint exposed a live-controller gap: parser and alias parity could pass while the governed `review-channel` path still hid actor-addressed packets, disclosed packet bodies before failing the …
- **`40f6977a`** — Phase 0.6C: guard bridge projection and topology artifacts
  - evolution: The GuardIR extraction checkpoint exposed a live-controller gap: parser and alias parity could pass while the governed `review-channel` path still hid actor-addressed packets, disclosed packet bodies before failing the …
- **`aa848fbd`** — Refresh external review snapshot for fbd2993e
  - evolution: The GuardIR extraction checkpoint exposed a live-controller gap: parser and alias parity could pass while the governed `review-channel` path still hid actor-addressed packets, disclosed packet bodies before failing the …
- **`fbd2993e`** — Record ground truth receipt for Phase 0.6A push
  - evolution: The GuardIR extraction checkpoint exposed a live-controller gap: parser and alias parity could pass while the governed `review-channel` path still hid actor-addressed packets, disclosed packet bodies before failing the …
- **`cba89fef`** — Refresh external review snapshot for f1d053be
  - evolution: The GuardIR extraction checkpoint exposed a live-controller gap: parser and alias parity could pass while the governed `review-channel` path still hid actor-addressed packets, disclosed packet bodies before failing the …
- **`f1d053be`** — Phase 0.6A: fix packet attention lifecycle routing
  - evolution: The GuardIR extraction checkpoint exposed a live-controller gap: parser and alias parity could pass while the governed `review-channel` path still hid actor-addressed packets, disclosed packet bodies before failing the …
- **`81045581`** — Refresh external review snapshot for bd76e5a8
  - evolution: The GuardIR extraction checkpoint exposed a live-controller gap: parser and alias parity could pass while the governed `review-channel` path still hid actor-addressed packets, disclosed packet bodies before failing the …
- **`bd76e5a8`** — Fix push preflight artifact receipt suppression
  - evolution: The GuardIR extraction checkpoint exposed a live-controller gap: parser and alias parity could pass while the governed `review-channel` path still hid actor-addressed packets, disclosed packet bodies before failing the …
- **`2a3787c9`** — Refresh external review snapshot for b6a19290
  - evolution: The GuardIR extraction checkpoint exposed a live-controller gap: parser and alias parity could pass while the governed `review-channel` path still hid actor-addressed packets, disclosed packet bodies before failing the …
- **`b6a19290`** — Fix push preflight artifact receipt loop
  - evolution: The GuardIR extraction checkpoint exposed a live-controller gap: parser and alias parity could pass while the governed `review-channel` path still hid actor-addressed packets, disclosed packet bodies before failing the …
- **`d30618cc`** — Refresh external review snapshot for f8b35641
  - evolution: The GuardIR extraction checkpoint exposed a live-controller gap: parser and alias parity could pass while the governed `review-channel` path still hid actor-addressed packets, disclosed packet bodies before failing the …
- **`f8b35641`** — Record push preflight artifact receipt
  - evolution: The GuardIR extraction checkpoint exposed a live-controller gap: parser and alias parity could pass while the governed `review-channel` path still hid actor-addressed packets, disclosed packet bodies before failing the …
- **`3a98de57`** — Refresh external review snapshot for 9471fad2
  - evolution: The GuardIR extraction checkpoint exposed a live-controller gap: parser and alias parity could pass while the governed `review-channel` path still hid actor-addressed packets, disclosed packet bodies before failing the …
- **`9471fad2`** — Keep bridge projection guard out of checks root
  - evolution: The GuardIR extraction checkpoint exposed a live-controller gap: parser and alias parity could pass while the governed `review-channel` path still hid actor-addressed packets, disclosed packet bodies before failing the …
- **`9a5d3788`** — Refresh external review snapshot for ba8eb11f
  - evolution: The GuardIR extraction checkpoint exposed a live-controller gap: parser and alias parity could pass while the governed `review-channel` path still hid actor-addressed packets, disclosed packet bodies before failing the …
- **`ba8eb11f`** — Record ground-truth probe receipt for GuardIR push
  - evolution: The GuardIR extraction checkpoint exposed a live-controller gap: parser and alias parity could pass while the governed `review-channel` path still hid actor-addressed packets, disclosed packet bodies before failing the …
- **`94b93673`** — Refresh policy-owned generated surfaces for 1e4a96f7
  - evolution: The GuardIR extraction checkpoint exposed a live-controller gap: parser and alias parity could pass while the governed `review-channel` path still hid actor-addressed packets, disclosed packet bodies before failing the …
- **`1e4a96f7`** — Refresh external review snapshot for 9ea2c912
  - evolution: The GuardIR extraction checkpoint exposed a live-controller gap: parser and alias parity could pass while the governed `review-channel` path still hid actor-addressed packets, disclosed packet bodies before failing the …
- **`9ea2c912`** — Keep bridge report under shape budget
  - evolution: The GuardIR extraction checkpoint exposed a live-controller gap: parser and alias parity could pass while the governed `review-channel` path still hid actor-addressed packets, disclosed packet bodies before failing the …
- **`2b0756d3`** — Refresh external review snapshot for efc7f761
  - evolution: The GuardIR extraction checkpoint exposed a live-controller gap: parser and alias parity could pass while the governed `review-channel` path still hid actor-addressed packets, disclosed packet bodies before failing the …
- **`efc7f761`** — Fix package layout root-scoped ratchet
  - evolution: The GuardIR extraction checkpoint exposed a live-controller gap: parser and alias parity could pass while the governed `review-channel` path still hid actor-addressed packets, disclosed packet bodies before failing the …
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

- open governance findings: 27

### Startup advisories
- no_push_needed: clean_worktree

### Stale warnings
- Move straight to the governed push path.

### Open gap rows
- **governance_open** (`dev/scripts/devctl/commands/process/cleanup.py`): dogfood.command.process-cleanup: Auto-ingested devctl finalization failure rc=1.
repo_path=/Users/jguida941/testing_upgrade/codex-voice
- **governance_open** (`dev/scripts/devctl/commands/governance/install_git_hooks.py`): dogfood.command.install-git-hooks: Auto-ingested devctl finalization failure rc=1.
repo_path=/Users/jguida941/testing_upgrade/codex-voice
- **governance_open** (`dev/scripts/devctl/commands/relaunch_loop.py`): dogfood.command.relaunch-loop: Auto-ingested devctl finalization failure rc=2.
repo_path=/Users/jguida941/testing_upgrade/codex-voice
- **governance_open** (`dev/scripts/devctl/commands/governance/relaunch_loop.py`): dogfood.command.relaunch-loop: Auto-ingested devctl finalization failure rc=2.
repo_path=/Users/jguida941/testing_upgrade/codex-voice
- **governance_open** (`dev/scripts/devctl/commands/governance/render_surfaces.py`): dogfood.command.render-surfaces: Auto-ingested devctl finalization failure rc=1.
repo_path=/Users/jguida941/testing_upgrade/codex-voice
- **governance_open** (`dev/scripts/devctl/commands/remote_control/command.py`): dogfood.command.remote-control: Auto-ingested devctl finalization failure rc=1.
repo_path=/Users/jguida941/testing_upgrade/codex-voice
- **governance_open** (`dev/scripts/devctl/commands/probe_report.py`): dogfood.command.probe-report: Auto-ingested devctl finalization failure rc=1.
repo_path=/Users/jguida941/testing_upgrade/codex-voice
- **governance_open** (`dev/scripts/devctl/review_channel/event_reducer_inbox.py`): role_oriented_packet_inbox: Packet inbox routing is still provider-keyed in several runtime readers. Visibility and consumption must resolve through actor role plus exact session when scoped so provider role switches cannot hide, consume, or drop pending packets.

---

Projection produced by `devctl review-snapshot`. Generation stamp `snap-528137739c1c` binds this file to HEAD `a4e1ef0bf7d3`; if they drift, the freshness guard will fail CI. When the latest commit only refreshes this generated snapshot, the guard accepts this file as bound to that commit's parent code state.
