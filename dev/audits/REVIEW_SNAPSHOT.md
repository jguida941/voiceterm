# VoiceTerm — Review Snapshot

> Deterministically generated from typed governance state. Do not edit by hand — rerun `devctl review-snapshot --write`.

## Quick status

- Branch: `extraction/guardir-core-p0-proof-integrity`
- HEAD: `43f7b254e101` — Record SLICE-Z ground truth probe receipt
- Tree hash: `40fd1179a820`
- Generation stamp: `snap-33c40fa9ab1e`
- Generated at (UTC): 2026-05-19T18:27:08Z
- Push decision: `run_devctl_push` — push_preconditions_satisfied
- Reviewer mode: `tools_only` (interaction: `remote_control`)
- Pipeline state: `n/a` (approval: `n/a`)
- Delta since last snapshot: 24 commits, 84 files, +5013/-1179
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
- HEAD SHA: `43f7b254e1014aefa5f73304a6d0a43709129ebc`
- HEAD author: Justin Guida
- HEAD timestamp (UTC): 2026-05-19T14:26:39-04:00

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
- interaction_mode: `remote_control`

### Remote commit pipeline
- state: `n/a`
- approval_state: `n/a`

### Work intake
- active plan: **AI Governance Platform Plan**
- plan path: `dev/active/ai_governance_platform.md`
- active MP scope: `MP-377`
- advisory: `no_push_needed` — clean_worktree

## 3. Delta — what changed since the previous snapshot

Range: last 24 commits ending at `43f7b254e101`

- commits: 24
- files changed: 84
- insertions: +5013
- deletions: -1179
- bundle classes touched: tooling, docs
- authority surfaces touched: 1 file(s)

### Commits

| # | SHA | Subject | Files | +/- | Bundle | Risk |
|---|---|---|---|---|---|---|
| 1 | `43f7b254` | Record SLICE-Z ground truth probe receipt | 1 | +1/-0 | tooling |  |
| 2 | `a1b40b4c` | Refresh external review snapshot for 4593576d | 1 | +105/-78 | tooling |  |
| 3 | `4593576d` | SLICE-Z follow-up: align sync guard and docs | 9 | +152/-2 | tooling |  |
| 4 | `bb80f85a` | SLICE-Z repair: slice-counted continuation_anchor full life… | 17 | +587/-124 | tooling |  |
| 5 | `84d43c50` | SLICE-Z: slice-counted continuation_anchor auto-release for… | 2 | +217/-0 | tooling |  |
| 6 | `83721f94` | SLICE-Y repair: typed fail-loud blocker for FindingBacklog… | 2 | +85/-25 | tooling |  |
| 7 | `148f4c4e` | SLICE-Y: wire FindingBacklog -> select_next_slice in report… | 2 | +107/-0 | tooling |  |
| 8 | `0ea70c7d` | SLICE-X: bug-priority preemption helper in select_next_slice | 2 | +187/-0 | tooling |  |
| 9 | `0530d797` | SLICE-A repair: register GUARDIR_EXTENSION_BUNDLE alias | 2 | +12/-4 | tooling |  |
| 10 | `83b35f57` | SLICE-A: regenerate boot cards as GuardIR (repo_pack_id=gua… | 5 | +6/-6 | tooling |  |
| 11 | `644fa92f` | Add orchestrator post authority for role-flip task_started/… | 2 | +146/-0 | tooling |  |
| 12 | `ae55487b` | Refresh external review snapshot for 9b3908c2 | 1 | +57/-57 | tooling |  |
| 13 | `9b3908c2` | Phase 0.6D: bind packet lifecycle decisions | 18 | +769/-3 | tooling |  |
| 14 | `eaef4d08` | Refresh external review snapshot for a4e1ef0b | 1 | +53/-53 | tooling |  |
| 15 | `a4e1ef0b` | Phase 0.6D: authorize remote-lane review-channel posts | 10 | +156/-2 | tooling |  |
| 16 | `8425c4da` | Refresh external review snapshot for 3c61f60b | 1 | +52/-52 | tooling |  |
| 17 | `3c61f60b` | Phase 0.6D: keep ingested packet bodies out of next selecti… | 5 | +68/-1 | tooling |  |
| 18 | `cdb1424c` | Refresh external review snapshot for 40f6977a | 1 | +68/-59 | tooling |  |
| 19 | `40f6977a` | Phase 0.6C: guard bridge projection and topology artifacts | 24 | +1012/-4 | tooling |  |
| 20 | `aa848fbd` | Refresh external review snapshot for fbd2993e | 1 | +51/-51 | tooling |  |
| 21 | `fbd2993e` | Record ground truth receipt for Phase 0.6A push | 2 | +62/-64 | tooling |  |
| 22 | `cba89fef` | Refresh external review snapshot for f1d053be | 1 | +67/-60 | tooling |  |
| 23 | `f1d053be` | Phase 0.6A: fix packet attention lifecycle routing | 18 | +935/-478 | tooling |  |
| 24 | `81045581` | Refresh external review snapshot for bd76e5a8 | 1 | +58/-56 | tooling |  |

### Files

| Path | Bundle | +/- |
|---|---|---|
| `.github/workflows/release_preflight.yml` | tooling | +3/-0 |
| `.github/workflows/tooling_control_plane.yml` | tooling | +9/-0 |
| `AGENTS.md` | docs | +1/-1 |
| `dev/active/MASTER_PLAN.md` | tooling | +46/-1 |
| `dev/active/ai_governance_platform.md` | tooling | +61/-1 |
| `dev/audits/REVIEW_SNAPSHOT.md` | tooling | +630/-594 |
| `dev/audits/plan_intake/2026-05-18-guardir-extraction-plan.md` | tooling | +72/-0 |
| `dev/audits/plan_intake/sha256-manifest.txt` | tooling | +1/-1 |
| `dev/config/cognitive_role_fleet.json` | tooling | +14/-0 |
| `dev/config/devctl_repo_policy.json` | tooling | +2/-2 |
| `dev/config/templates/portable_governance_post_commit_hook.stub.sh` | tooling | +1/-1 |
| `dev/config/templates/portable_governance_pre_commit_hook.stub.sh` | tooling | +1/-1 |
| `dev/config/templates/portable_governance_pre_push_hook.stub.sh` | tooling | +1/-1 |
| `dev/guides/DEVELOPMENT.md` | docs | +32/-2 |
| `dev/guides/SYSTEM_MAP.md` | docs | +4/-4 |
| `dev/history/ENGINEERING_EVOLUTION.md` | tooling | +83/-0 |
| `dev/scripts/README.md` | tooling | +33/-1 |
| `dev/scripts/checks/check_guardir_extraction_plan_artifacts.py` | tooling | +8/-0 |
| `dev/scripts/checks/check_no_new_hardcoded_provider_authority.py` | tooling | +12/-0 |
| `dev/scripts/checks/check_no_new_topology_count_coupling.py` | tooling | +12/-0 |
| `dev/scripts/checks/guardir_extraction_plan_artifacts/__init__.py` | tooling | +1/-0 |
| `dev/scripts/checks/guardir_extraction_plan_artifacts/command.py` | tooling | +190/-0 |
| `dev/scripts/checks/multi_agent_sync/runtime_truth_agent_loop_instruction.py` | tooling | +26/-0 |
| `dev/scripts/checks/topology_hardcode/__init__.py` | tooling | +1/-0 |
| `dev/scripts/checks/topology_hardcode/command.py` | tooling | +311/-0 |
| `dev/scripts/devctl/bundles/registry.py` | tooling | +3/-0 |
| `dev/scripts/devctl/commands/check/router_python_tests.py` | tooling | +30/-0 |
| `dev/scripts/devctl/commands/development/next_slice.py` | tooling | +66/-0 |
| `dev/scripts/devctl/commands/development/packet_attention.py` | tooling | +199/-85 |
| `dev/scripts/devctl/commands/development/packet_attention_body_followup.py` | tooling | +269/-2 |
| `dev/scripts/devctl/commands/development/packet_attention_commands.py` | tooling | +6/-0 |
| `dev/scripts/devctl/commands/development/report_assembly.py` | tooling | +110/-19 |
| `dev/scripts/devctl/commands/development/report_context.py` | tooling | +1/-0 |
| `dev/scripts/devctl/commands/review_channel/event_handler.py` | tooling | +37/-0 |
| `dev/scripts/devctl/commands/review_channel/event_post_action.py` | tooling | +5/-0 |
| `dev/scripts/devctl/commands/review_channel/status_bridge_sync.py` | tooling | +10/-2 |
| `dev/scripts/devctl/governance/script_catalog_registry.py` | tooling | +12/-0 |
| `dev/scripts/devctl/platform/extension_bundle_defaults.py` | tooling | +8/-0 |
| `dev/scripts/devctl/quality_policy/defaults.py` | tooling | +18/-0 |
| `dev/scripts/devctl/review_channel/agent_packet_attention.py` | tooling | +7/-0 |
| _44 more files trimmed_ | | |

## 4. Quality signals

### Governance review
- total findings: 27
- open: 27
- fixed: 0
- false positives: 0

Recent findings:
- `dogfood.command.install-git-hooks` — `dev/scripts/devctl/commands/governance/install_git_hooks.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.relaunch-loop` — `dev/scripts/devctl/commands/relaunch_loop.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.relaunch-loop` — `dev/scripts/devctl/commands/governance/relaunch_loop.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.render-surfaces` — `dev/scripts/devctl/commands/governance/render_surfaces.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.remote-control` — `dev/scripts/devctl/commands/remote_control/command.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.probe-report` — `dev/scripts/devctl/commands/probe_report.py` (n/a, verdict=`confirmed_issue`)
- `role_oriented_packet_inbox` — `dev/scripts/devctl/review_channel/event_reducer_inbox.py` (high, verdict=`confirmed_issue`)
- `dogfood.command.pipeline` — `dev/scripts/devctl/commands/pipeline/command.py` (n/a, verdict=`confirmed_issue`)
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
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/review_channel/event_models.py`) — Commit bb80f85a changed dev/scripts/devctl/review_channel/event_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/review_channel/packet_contract.py`) — Commit bb80f85a changed dev/scripts/devctl/review_channel/packet_contract.py

### Suggested verification commands

- `python3 dev/scripts/devctl.py check --profile ci`
- `python3 dev/scripts/devctl.py probe-report --format md`
- `python3 dev/scripts/devctl.py docs-check --strict-tooling`
- `python3 dev/scripts/devctl.py governance-review --format md`
- `python3 dev/scripts/devctl.py check-router --format md`

## 7. Reasoning — why these changes landed

### Per-commit rationale

- **`43f7b254`** — Record SLICE-Z ground truth probe receipt
  - Adds the GroundTruthProbeRunReceipt for the slice-counted continuation anchor repair range.
  - evolution: The GuardIR extraction checkpoint exposed a live-controller gap: parser and alias parity could pass while the governed `review-channel` path still hid actor-addressed packets, disclosed packet bodies before failing the …
- **`a1b40b4c`** — Refresh external review snapshot for 4593576d
  - evolution: The GuardIR extraction checkpoint exposed a live-controller gap: parser and alias parity could pass while the governed `review-channel` path still hid actor-addressed packets, disclosed packet bodies before failing the …
- **`4593576d`** — SLICE-Z follow-up: align sync guard and docs
  - Follow-up to bb80f85a for the live role-flip loop. Allows a communication-only open_packet_body focus to supersede an older plan inbox packet within the same scoped active packet set, and records the slice-counted continuation_anchor contract in durable docs.
  - evolution: The GuardIR extraction checkpoint exposed a live-controller gap: parser and alias parity could pass while the governed `review-channel` path still hid actor-addressed packets, disclosed packet bodies before failing the …
- **`bb80f85a`** — SLICE-Z repair: slice-counted continuation_anchor full lifecycle (block + auto-release)
  - Closes codex rev_pkt_4520 SLICE-Z repair directive (rev_pkt_4519 review_failed of
  - my prior 84d43c50 block-side-only attempt). Role-flip cycle 2: codex orchestrator
  - posted typed verdict + 7 acceptance criteria; this commit lands codex's full
  - evolution: The GuardIR extraction checkpoint exposed a live-controller gap: parser and alias parity could pass while the governed `review-channel` path still hid actor-addressed packets, disclosed packet bodies before failing the …
- **`84d43c50`** — SLICE-Z: slice-counted continuation_anchor auto-release for bug #9
  - Per codex orchestrator directive rev_pkt_4517 (Role-flip cycle 2 SLICE-Z bug #9 fix):
  - add typed extension to SessionTerminationPolicy so continuation_anchor packets can
  - opt into release_mode=commit_count + release_commit_count=N. TaskCompleteDecision
  - evolution: The GuardIR extraction checkpoint exposed a live-controller gap: parser and alias parity could pass while the governed `review-channel` path still hid actor-addressed packets, disclosed packet bodies before failing the …
- **`83721f94`** — SLICE-Y repair: typed fail-loud blocker for FindingBacklog source
  - Per codex review_failed rev_pkt_4513: SLICE-Y commit 148f4c4e left soft-fail
  - catches that recreated original silent-fallback bug. This repair adds typed
  - DevelopmentNextSlice blocker when FindingBacklog load fails, so develop next
  - evolution: The GuardIR extraction checkpoint exposed a live-controller gap: parser and alias parity could pass while the governed `review-channel` path still hid actor-addressed packets, disclosed packet bodies before failing the …
- **`148f4c4e`** — SLICE-Y: wire FindingBacklog -> select_next_slice in report_assembly
  - Per codex orchestrator directive rev_pkt_4495 / rev_pkt_4511 + sidecar rev_pkt_4508
  - (Role-flip cycle 2 SLICE-Y): wire ranked critical/high open findings from the
  - canonical FindingBacklog source into select_next_slice via report_assembly._build_core
  - evolution: The GuardIR extraction checkpoint exposed a live-controller gap: parser and alias parity could pass while the governed `review-channel` path still hid actor-addressed packets, disclosed packet bodies before failing the …
- **`0ea70c7d`** — SLICE-X: bug-priority preemption helper in select_next_slice
  - Per codex orchestrator directive rev_pkt_4494/rev_pkt_4506 (Role-flip cycle 2 SLICE-X):
  - make confirmed systemic/high-severity bugs preempt ordinary plan work in the
  - develop-next selector, using existing Finding/FindingBacklog/RankedFinding
  - evolution: The GuardIR extraction checkpoint exposed a live-controller gap: parser and alias parity could pass while the governed `review-channel` path still hid actor-addressed packets, disclosed packet bodies before failing the …
- **`0530d797`** — SLICE-A repair: register GUARDIR_EXTENSION_BUNDLE alias
  - Per codex review_failed rev_pkt_4501: SLICE-A commit 83b35f57 flipped policy
  - repo_pack_metadata.pack_id voiceterm->guardir but extension_bundle_defaults.py
  - still registered only VOICETERM_EXTENSION_BUNDLE under repo_pack_id=voiceterm,
  - evolution: The GuardIR extraction checkpoint exposed a live-controller gap: parser and alias parity could pass while the governed `review-channel` path still hid actor-addressed packets, disclosed packet bodies before failing the …
- **`83b35f57`** — SLICE-A: regenerate boot cards as GuardIR (repo_pack_id=guardir)
  - Per codex orchestrator directive rev_pkt_4493 (Role-flip cycle 2 SLICE-A):
  - make AGENTS.md/CLAUDE.md resolve repo_pack_id=guardir / GuardIR identity
  - instead of voiceterm/VoiceTerm authority leakage.
  - evolution: The GuardIR extraction checkpoint exposed a live-controller gap: parser and alias parity could pass while the governed `review-channel` path still hid actor-addressed packets, disclosed packet bodies before failing the …
- **`644fa92f`** — Add orchestrator post authority for role-flip task_started/finding
  - Per codex directive rev_pkt_4488 (Role-flip task 1): exempt codex-source
  - review-channel posts of kind task_started/finding from ControlDecisionObeyedGuard
  - when no AgentLoopDecision present. Narrow scope: review-channel POST only +
  - evolution: The GuardIR extraction checkpoint exposed a live-controller gap: parser and alias parity could pass while the governed `review-channel` path still hid actor-addressed packets, disclosed packet bodies before failing the …
- **`ae55487b`** — Refresh external review snapshot for 9b3908c2
  - evolution: The GuardIR extraction checkpoint exposed a live-controller gap: parser and alias parity could pass while the governed `review-channel` path still hid actor-addressed packets, disclosed packet bodies before failing the …
- **`9b3908c2`** — Phase 0.6D: bind packet lifecycle decisions
  - evolution: The GuardIR extraction checkpoint exposed a live-controller gap: parser and alias parity could pass while the governed `review-channel` path still hid actor-addressed packets, disclosed packet bodies before failing the …
- **`eaef4d08`** — Refresh external review snapshot for a4e1ef0b
  - evolution: The GuardIR extraction checkpoint exposed a live-controller gap: parser and alias parity could pass while the governed `review-channel` path still hid actor-addressed packets, disclosed packet bodies before failing the …
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
- **governance_open** (`dev/scripts/devctl/commands/pipeline/command.py`): dogfood.command.pipeline: Auto-ingested devctl finalization failure rc=1.
repo_path=/Users/jguida941/testing_upgrade/codex-voice

---

Projection produced by `devctl review-snapshot`. Generation stamp `snap-33c40fa9ab1e` binds this file to HEAD `43f7b254e101`; if they drift, the freshness guard will fail CI. When the latest commit only refreshes this generated snapshot, the guard accepts this file as bound to that commit's parent code state.
