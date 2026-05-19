# VoiceTerm — Review Snapshot

> Deterministically generated from typed governance state. Do not edit by hand — rerun `devctl review-snapshot --write`.

## Quick status

- Branch: `extraction/guardir-core-p0-proof-integrity`
- HEAD: `d30618cc9ad2` — Refresh external review snapshot for f8b35641
- Tree hash: `1f10aa42bf33`
- Generation stamp: `snap-052a1b2b9222`
- Generated at (UTC): 2026-05-19T08:43:42Z
- Push decision: `await_checkpoint` — staged_index_present
- Reviewer mode: `tools_only` (interaction: `local_terminal`)
- Pipeline state: `n/a` (approval: `n/a`)
- Delta since last snapshot: 24 commits, 30 files, +2596/-2025
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
- HEAD SHA: `d30618cc9ad262e8eb58561f433521cab8f20822`
- HEAD author: Justin Guida
- HEAD timestamp (UTC): 2026-05-19T04:11:10-04:00

## 2. Governance state

### Push decision
- action: `await_checkpoint`
- reason: staged_index_present
- push_eligible_now: False
- worktree_clean: False
- staged_path_count: 2
- unstaged_path_count: 0
- next_step_command: `n/a`
- latest_push_report_state: `blocked` (validation_failed)
- publication_backlog: queued
- publication_guidance: Local branch still has unpublished work waiting for governed push once the current slice is checkpoint-clean.

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
- advisory: `checkpoint_allowed` — worktree_dirty_within_budget

## 3. Delta — what changed since the previous snapshot

Range: last 24 commits ending at `d30618cc9ad2`

- commits: 24
- files changed: 30
- insertions: +2596
- deletions: -2025
- bundle classes touched: tooling, docs
- authority surfaces touched: 1 file(s)

### Commits

| # | SHA | Subject | Files | +/- | Bundle | Risk |
|---|---|---|---|---|---|---|
| 1 | `d30618cc` | Refresh external review snapshot for f8b35641 | 1 | +48/-48 | tooling |  |
| 2 | `f8b35641` | Record push preflight artifact receipt | 2 | +59/-61 | tooling |  |
| 3 | `3a98de57` | Refresh external review snapshot for 9471fad2 | 1 | +59/-57 | tooling |  |
| 4 | `9471fad2` | Keep bridge projection guard out of checks root | 10 | +438/-389 | tooling |  |
| 5 | `9a5d3788` | Refresh external review snapshot for ba8eb11f | 1 | +49/-48 | tooling |  |
| 6 | `ba8eb11f` | Record ground-truth probe receipt for GuardIR push | 2 | +63/-60 | tooling |  |
| 7 | `94b93673` | Refresh policy-owned generated surfaces for 1e4a96f7 | 1 | +1/-1 | docs |  |
| 8 | `1e4a96f7` | Refresh external review snapshot for 9ea2c912 | 1 | +65/-69 | tooling |  |
| 9 | `9ea2c912` | Keep bridge report under shape budget | 3 | +93/-78 | tooling |  |
| 10 | `2b0756d3` | Refresh external review snapshot for efc7f761 | 1 | +62/-62 | tooling |  |
| 11 | `efc7f761` | Fix package layout root-scoped ratchet | 10 | +307/-123 | tooling |  |
| 12 | `a5292d33` | Refresh external review snapshot for c6c7052f | 1 | +71/-77 | tooling |  |
| 13 | `c6c7052f` | Wire governance closure CI guard coverage | 10 | +138/-60 | tooling |  |
| 14 | `27a086e3` | Refresh external review snapshot for 6a9b5c68 | 1 | +59/-56 | tooling |  |
| 15 | `6a9b5c68` | Stop claiming real-life proof without pytest nodes | 12 | +123/-61 | tooling |  |
| 16 | `3fbbc5fe` | Refresh external review snapshot for 58db3f97 | 1 | +52/-49 | tooling |  |
| 17 | `58db3f97` | Record ground-truth receipt for release preflight | 2 | +48/-46 | tooling |  |
| 18 | `10ad9a2c` | Refresh external review snapshot for 8afa3efa | 1 | +65/-71 | tooling |  |
| 19 | `8afa3efa` | Classify guard enforcement lanes for release preflight | 15 | +407/-303 | tooling |  |
| 20 | `801df43e` | Refresh external review snapshot for 1efa1407 | 1 | +63/-65 | tooling |  |
| 21 | `1efa1407` | Route publication-scope release checks through push refs | 10 | +109/-51 | tooling |  |
| 22 | `4d80a6f9` | Refresh external review snapshot for a68c6b47 | 1 | +64/-79 | tooling |  |
| 23 | `a68c6b47` | Document release hygiene guard inventory | 8 | +84/-47 | tooling |  |
| 24 | `12600f3f` | Refresh external review snapshot for 7a272579 | 1 | +69/-64 | tooling |  |

### Files

| Path | Bundle | +/- |
|---|---|---|
| `.github/workflows/release_preflight.yml` | tooling | +1/-0 |
| `.github/workflows/tooling_control_plane.yml` | tooling | +35/-0 |
| `AGENTS.md` | docs | +6/-3 |
| `dev/active/MASTER_PLAN.md` | tooling | +29/-3 |
| `dev/active/ai_governance_platform.md` | tooling | +36/-1 |
| `dev/audits/REVIEW_SNAPSHOT.md` | tooling | +1311/-1318 |
| `dev/guides/DEVELOPMENT.md` | docs | +27/-6 |
| `dev/guides/SYSTEM_MAP.md` | docs | +3/-3 |
| `dev/history/ENGINEERING_EVOLUTION.md` | tooling | +118/-0 |
| `dev/scripts/README.md` | tooling | +30/-8 |
| `dev/scripts/checks/bridge_projection_only/__init__.py` | tooling | +2/-0 |
| `dev/scripts/checks/bridge_projection_only/command.py` | tooling | +330/-0 |
| `dev/scripts/checks/check_bridge_projection_only.py` | tooling | +6/-319 |
| `dev/scripts/checks/check_guard_enforcement_inventory.py` | tooling | +7/-252 |
| `dev/scripts/checks/guard_enforcement_inventory/command.py` | tooling | +285/-0 |
| `dev/scripts/checks/package_layout/command.py` | tooling | +169/-73 |
| `dev/scripts/checks/review_channel_bridge/projection_stub.py` | tooling | +34/-0 |
| `dev/scripts/checks/review_channel_bridge/report.py` | tooling | +8/-27 |
| `dev/scripts/devctl/bundles/registry.py` | tooling | +1/-0 |
| `dev/scripts/devctl/commands/check/router_range.py` | tooling | +28/-0 |
| `dev/scripts/devctl/governance/instruction_boot_card.py` | tooling | +6/-3 |
| `dev/scripts/devctl/runtime/commit_receipt.py` | tooling | +19/-2 |
| `dev/scripts/devctl/tests/checks/package_layout/test_check_package_layout.py` | tooling | +46/-1 |
| `dev/scripts/devctl/tests/checks/test_check_bridge_projection_only.py` | tooling | +4/-2 |
| `dev/scripts/devctl/tests/checks/test_check_guard_enforcement_inventory.py` | tooling | +32/-1 |
| `dev/scripts/devctl/tests/commands/check/test_check_router.py` | tooling | +5/-0 |
| `dev/scripts/devctl/tests/runtime/test_commit_receipt.py` | tooling | +6/-3 |
| `dev/state/artifact_receipts.jsonl` | tooling | +3/-0 |
| `dev/state/ground_truth_probe_receipts.jsonl` | tooling | +2/-0 |
| `dev/state/non_trivial_output_proof_remediation_findings.jsonl` | tooling | +7/-0 |

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

- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/commands/check/test_check_router.py`) — Review contract-level invariants for this file

### Suggested verification commands

- `python3 dev/scripts/devctl.py check --profile ci`
- `python3 dev/scripts/devctl.py probe-report --format md`
- `python3 dev/scripts/devctl.py docs-check --strict-tooling`
- `python3 dev/scripts/devctl.py governance-review --format md`
- `python3 dev/scripts/devctl.py check-router --format md`

## 7. Reasoning — why these changes landed

### Per-commit rationale

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
- **`a5292d33`** — Refresh external review snapshot for c6c7052f
  - evolution: The GuardIR extraction checkpoint exposed a live-controller gap: parser and alias parity could pass while the governed `review-channel` path still hid actor-addressed packets, disclosed packet bodies before failing the …
- **`c6c7052f`** — Wire governance closure CI guard coverage
  - evolution: The GuardIR extraction checkpoint exposed a live-controller gap: parser and alias parity could pass while the governed `review-channel` path still hid actor-addressed packets, disclosed packet bodies before failing the …
- **`27a086e3`** — Refresh external review snapshot for 6a9b5c68
  - evolution: The GuardIR extraction checkpoint exposed a live-controller gap: parser and alias parity could pass while the governed `review-channel` path still hid actor-addressed packets, disclosed packet bodies before failing the …
- **`6a9b5c68`** — Stop claiming real-life proof without pytest nodes
  - evolution: The GuardIR extraction checkpoint exposed a live-controller gap: parser and alias parity could pass while the governed `review-channel` path still hid actor-addressed packets, disclosed packet bodies before failing the …
- **`3fbbc5fe`** — Refresh external review snapshot for 58db3f97
  - evolution: The GuardIR extraction checkpoint exposed a live-controller gap: parser and alias parity could pass while the governed `review-channel` path still hid actor-addressed packets, disclosed packet bodies before failing the …
- **`58db3f97`** — Record ground-truth receipt for release preflight
  - evolution: The GuardIR extraction checkpoint exposed a live-controller gap: parser and alias parity could pass while the governed `review-channel` path still hid actor-addressed packets, disclosed packet bodies before failing the …
- **`10ad9a2c`** — Refresh external review snapshot for 8afa3efa
  - evolution: The GuardIR extraction checkpoint exposed a live-controller gap: parser and alias parity could pass while the governed `review-channel` path still hid actor-addressed packets, disclosed packet bodies before failing the …
- **`8afa3efa`** — Classify guard enforcement lanes for release preflight
  - evolution: The GuardIR extraction checkpoint exposed a live-controller gap: parser and alias parity could pass while the governed `review-channel` path still hid actor-addressed packets, disclosed packet bodies before failing the …
- **`801df43e`** — Refresh external review snapshot for 1efa1407
  - evolution: The GuardIR extraction checkpoint exposed a live-controller gap: parser and alias parity could pass while the governed `review-channel` path still hid actor-addressed packets, disclosed packet bodies before failing the …
- **`1efa1407`** — Route publication-scope release checks through push refs
  - evolution: The GuardIR extraction checkpoint exposed a live-controller gap: parser and alias parity could pass while the governed `review-channel` path still hid actor-addressed packets, disclosed packet bodies before failing the …
- **`4d80a6f9`** — Refresh external review snapshot for a68c6b47
  - evolution: The GuardIR extraction checkpoint exposed a live-controller gap: parser and alias parity could pass while the governed `review-channel` path still hid actor-addressed packets, disclosed packet bodies before failing the …
- **`a68c6b47`** — Document release hygiene guard inventory
  - evolution: The GuardIR extraction checkpoint exposed a live-controller gap: parser and alias parity could pass while the governed `review-channel` path still hid actor-addressed packets, disclosed packet bodies before failing the …
- **`12600f3f`** — Refresh external review snapshot for 7a272579
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
- checkpoint_allowed: worktree_dirty_within_budget

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

Projection produced by `devctl review-snapshot`. Generation stamp `snap-052a1b2b9222` binds this file to HEAD `d30618cc9ad2`; if they drift, the freshness guard will fail CI. When the latest commit only refreshes this generated snapshot, the guard accepts this file as bound to that commit's parent code state.
