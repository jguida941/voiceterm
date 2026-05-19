# VoiceTerm — Review Snapshot

> Deterministically generated from typed governance state. Do not edit by hand — rerun `devctl review-snapshot --write`.

## Quick status

- Branch: `extraction/guardir-core-p0-proof-integrity`
- HEAD: `9ea2c912b0eb` — Keep bridge report under shape budget
- Tree hash: `544ce963d16a`
- Generation stamp: `snap-5447a1c86b08`
- Generated at (UTC): 2026-05-19T07:01:15Z
- Push decision: `run_devctl_push` — push_preconditions_satisfied
- Reviewer mode: `tools_only` (interaction: `local_terminal`)
- Pipeline state: `n/a` (approval: `n/a`)
- Delta since last snapshot: 24 commits, 61 files, +4711/-2562
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
- HEAD SHA: `9ea2c912b0ebd6e633ea201bc7db352ec7a651b0`
- HEAD author: Justin Guida
- HEAD timestamp (UTC): 2026-05-19T03:00:54-04:00

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

Range: last 24 commits ending at `9ea2c912b0eb`

- commits: 24
- files changed: 61
- insertions: +4711
- deletions: -2562
- bundle classes touched: tooling, docs, runtime
- risk add-ons triggered: Threading / lifecycle / memory, Performance / latency
- authority surfaces touched: 1 file(s)

### Commits

| # | SHA | Subject | Files | +/- | Bundle | Risk |
|---|---|---|---|---|---|---|
| 1 | `9ea2c912` | Keep bridge report under shape budget | 3 | +93/-78 | tooling |  |
| 2 | `2b0756d3` | Refresh external review snapshot for efc7f761 | 1 | +62/-62 | tooling |  |
| 3 | `efc7f761` | Fix package layout root-scoped ratchet | 10 | +307/-123 | tooling |  |
| 4 | `a5292d33` | Refresh external review snapshot for c6c7052f | 1 | +71/-77 | tooling |  |
| 5 | `c6c7052f` | Wire governance closure CI guard coverage | 10 | +138/-60 | tooling |  |
| 6 | `27a086e3` | Refresh external review snapshot for 6a9b5c68 | 1 | +59/-56 | tooling |  |
| 7 | `6a9b5c68` | Stop claiming real-life proof without pytest nodes | 12 | +123/-61 | tooling |  |
| 8 | `3fbbc5fe` | Refresh external review snapshot for 58db3f97 | 1 | +52/-49 | tooling |  |
| 9 | `58db3f97` | Record ground-truth receipt for release preflight | 2 | +48/-46 | tooling |  |
| 10 | `10ad9a2c` | Refresh external review snapshot for 8afa3efa | 1 | +65/-71 | tooling |  |
| 11 | `8afa3efa` | Classify guard enforcement lanes for release preflight | 15 | +407/-303 | tooling |  |
| 12 | `801df43e` | Refresh external review snapshot for 1efa1407 | 1 | +63/-65 | tooling |  |
| 13 | `1efa1407` | Route publication-scope release checks through push refs | 10 | +109/-51 | tooling |  |
| 14 | `4d80a6f9` | Refresh external review snapshot for a68c6b47 | 1 | +64/-79 | tooling |  |
| 15 | `a68c6b47` | Document release hygiene guard inventory | 8 | +84/-47 | tooling |  |
| 16 | `12600f3f` | Refresh external review snapshot for 7a272579 | 1 | +69/-64 | tooling |  |
| 17 | `7a272579` | Phase 0.6A: propagate validation scope through release chec… | 18 | +240/-85 | tooling | Threading / lifecycle / memory, Performance / latency |
| 18 | `38057f5c` | Refresh external review snapshot for 15425337 | 1 | +60/-61 | tooling |  |
| 19 | `15425337` | Phase 0.6A: carry push preflight refs into publication scope | 13 | +200/-61 | tooling |  |
| 20 | `cf75f3f4` | Refresh external review snapshot for 9716470b | 1 | +69/-76 | tooling |  |
| 21 | `9716470b` | Phase 0.6A: bind governed push to publication authorization | 19 | +815/-419 | tooling |  |
| 22 | `fcb709ef` | Refresh external review snapshot for 36a930f7 | 1 | +55/-57 | tooling |  |
| 23 | `36a930f7` | Phase 0.6A: fix typed collaboration routing and controller… | 21 | +1391/-447 | tooling |  |
| 24 | `ddaf58f5` | Refresh external review snapshot for f2f152dd | 1 | +67/-64 | tooling |  |

### Files

| Path | Bundle | +/- |
|---|---|---|
| `.github/workflows/release_preflight.yml` | tooling | +1/-0 |
| `.github/workflows/tooling_control_plane.yml` | tooling | +35/-0 |
| `AGENTS.md` | docs | +8/-3 |
| `dev/active/MASTER_PLAN.md` | tooling | +49/-2 |
| `dev/active/ai_governance_platform.md` | tooling | +67/-2 |
| `dev/audits/REVIEW_SNAPSHOT.md` | tooling | +1406/-1410 |
| `dev/config/devctl_repo_policy.json` | tooling | +1/-0 |
| `dev/guides/DEVELOPMENT.md` | docs | +57/-5 |
| `dev/guides/SYSTEM_MAP.md` | docs | +4/-4 |
| `dev/history/ENGINEERING_EVOLUTION.md` | tooling | +184/-1 |
| `dev/scripts/README.md` | tooling | +71/-7 |
| `dev/scripts/checks/check_guard_enforcement_inventory.py` | tooling | +7/-252 |
| `dev/scripts/checks/check_publication_scope_integrity_for_push.py` | tooling | +14/-0 |
| `dev/scripts/checks/guard_enforcement_inventory/command.py` | tooling | +285/-0 |
| `dev/scripts/checks/package_layout/command.py` | tooling | +169/-73 |
| `dev/scripts/checks/publication_scope_integrity_for_push/__init__.py` | tooling | +1/-0 |
| `dev/scripts/checks/publication_scope_integrity_for_push/command.py` | tooling | +81/-0 |
| `dev/scripts/checks/review_channel_bridge/projection_stub.py` | tooling | +34/-0 |
| `dev/scripts/checks/review_channel_bridge/report.py` | tooling | +8/-27 |
| `dev/scripts/devctl/bundles/registry.py` | tooling | +1/-0 |
| `dev/scripts/devctl/cli_parser/builders_checks.py` | tooling | +13/-0 |
| `dev/scripts/devctl/commands/check/phases.py` | tooling | +1/-0 |
| `dev/scripts/devctl/commands/check/router_range.py` | tooling | +29/-0 |
| `dev/scripts/devctl/commands/check/support.py` | tooling | +11/-0 |
| `dev/scripts/devctl/commands/development/packet_attention.py` | tooling | +84/-10 |
| `dev/scripts/devctl/commands/development/packet_attention_commands.py` | tooling | +49/-5 |
| `dev/scripts/devctl/commands/review_channel/event_attempted_action_scope.py` | tooling | +180/-0 |
| `dev/scripts/devctl/commands/review_channel/event_handler.py` | tooling | +28/-168 |
| `dev/scripts/devctl/commands/vcs/push.py` | tooling | +24/-265 |
| `dev/scripts/devctl/commands/vcs/push_attempted_command.py` | tooling | +29/-0 |
| `dev/scripts/devctl/commands/vcs/push_authorization_control.py` | tooling | +102/-0 |
| `dev/scripts/devctl/commands/vcs/push_control_decision.py` | tooling | +64/-0 |
| `dev/scripts/devctl/commands/vcs/push_control_decision_report.py` | tooling | +54/-0 |
| `dev/scripts/devctl/commands/vcs/push_preflight_flow.py` | tooling | +179/-0 |
| `dev/scripts/devctl/governance/instruction_boot_card.py` | tooling | +8/-3 |
| `dev/scripts/devctl/governance/push_routing.py` | tooling | +11/-8 |
| `dev/scripts/devctl/governance/script_catalog_registry.py` | tooling | +4/-0 |
| `dev/scripts/devctl/quality_policy/__init__.py` | tooling | +1/-0 |
| `dev/scripts/devctl/quality_policy/defaults.py` | tooling | +3/-0 |
| `dev/scripts/devctl/quality_policy/rendering.py` | tooling | +4/-2 |
| _21 more files trimmed_ | | |

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

- **risk**: Threading / lifecycle / memory — Delta touches a risk-sensitive surface; verify the routed bundle
- **risk**: Performance / latency — Delta touches a risk-sensitive surface; verify the routed bundle
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/commands/check/test_check_router.py`) — Review contract-level invariants for this file

### Suggested verification commands

- `cd rust && cargo test --bin voiceterm`
- `cd rust && cargo clippy --all-targets -- -D warnings`
- `python3 dev/scripts/devctl.py check --profile ci`
- `python3 dev/scripts/devctl.py probe-report --format md`
- `python3 dev/scripts/devctl.py docs-check --strict-tooling`
- `python3 dev/scripts/devctl.py governance-review --format md`
- `python3 dev/scripts/devctl.py check-router --format md`

## 7. Reasoning — why these changes landed

### Per-commit rationale

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
- **`7a272579`** — Phase 0.6A: propagate validation scope through release checks
  - evolution: The GuardIR extraction checkpoint exposed a live-controller gap: parser and alias parity could pass while the governed `review-channel` path still hid actor-addressed packets, disclosed packet bodies before failing the …
- **`38057f5c`** — Refresh external review snapshot for 15425337
  - evolution: The GuardIR extraction checkpoint exposed a live-controller gap: parser and alias parity could pass while the governed `review-channel` path still hid actor-addressed packets, disclosed packet bodies before failing the …
- **`15425337`** — Phase 0.6A: carry push preflight refs into publication scope
  - evolution: The GuardIR extraction checkpoint exposed a live-controller gap: parser and alias parity could pass while the governed `review-channel` path still hid actor-addressed packets, disclosed packet bodies before failing the …
- **`cf75f3f4`** — Refresh external review snapshot for 9716470b
- **`9716470b`** — Phase 0.6A: bind governed push to publication authorization
- **`fcb709ef`** — Refresh external review snapshot for 36a930f7
- **`36a930f7`** — Phase 0.6A: fix typed collaboration routing and controller reads
- **`ddaf58f5`** — Refresh external review snapshot for f2f152dd
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

Projection produced by `devctl review-snapshot`. Generation stamp `snap-5447a1c86b08` binds this file to HEAD `9ea2c912b0eb`; if they drift, the freshness guard will fail CI. When the latest commit only refreshes this generated snapshot, the guard accepts this file as bound to that commit's parent code state.
