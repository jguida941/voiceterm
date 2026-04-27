# VoiceTerm — Review Snapshot

> Deterministically generated from typed governance state. Do not edit by hand — rerun `devctl review-snapshot --write`.

## Quick status

- Branch: `feature/governance-quality-sweep`
- HEAD: `f6e3783d7bb3` — Refresh external review snapshot for 80c1791a
- Tree hash: `ed8cb6bd8c66`
- Generation stamp: `snap-679a5b1cf07b`
- Generated at (UTC): 2026-04-27T18:57:38Z
- Push decision: `run_devctl_push` — push_preconditions_satisfied
- Reviewer mode: `active_dual_agent` (interaction: `remote_control`)
- Pipeline state: `n/a` (approval: `n/a`)
- Delta since last snapshot: 24 commits, 74 files, +6898/-2030
- Governance findings: 124 open / 88 fixed / 226 total
- Probe hints: 0 total across 0 files scanned

## 1. Identity

- Repository: **VoiceTerm**
- Product thesis: This is the product thesis for the governance stack in this repository.
Absorb these four commitments before engaging with SOP, guard, routing,
or plan detail — they explain why the process exists.

This repo builds a portable AI governance platform proven through one
production client (VoiceTerm, a Rust voice-first terminal overlay for AI
CLIs). The product thesis is that executable local control — guards,
probes, typed actions, deterministic policy resolution — is what makes
AI-assisted engineering reliable, not prompt instructions alone.

**Mission**: Ship a reusable governance stack that any repo can adopt by
installing the platform and selecting a repo pack, without forking
VoiceTerm-specific code.

**Proof obligation**: Every claim about quality, safety, or process
compliance must be backed by a repo-owned executable artifact (guard
script, probe, typed action, CI workflow) that produces the same result
regardless of which AI model or operator runs it. Prompt-only governance
is not accepted as proof.

**Platform boundaries**: VoiceTerm is one client of the platform; portable
governance layers must not hardcode repo names, bridge paths, plan doc
locations, or product-specific defaults. Repo-local assumptions belong in
the repo pack, not in the platform core. MCP servers, operator consoles,
mobile surfaces, and overlay/TUI adapters are clients, not authority.

**Current priority**: Harden the governance stack for multi-repo adoption —
remove VoiceTerm-local assumptions from portable layers, stabilize the
typed contract surface (ProjectGovernance, StartupContext, ReviewState,
TypedAction → ActionResult → RunRecord), and close the remaining probe
and guard gaps so the platform proves its own thesis before external
adopters arrive.
- Remote: `https://github.com/jguida941/voiceterm.git`
- Default branch: `master`
- Current branch: `feature/governance-quality-sweep`
- HEAD SHA: `f6e3783d7bb359fc1124b16a871bf53dbf1c995f`
- HEAD author: Justin Guida
- HEAD timestamp (UTC): 2026-04-27T14:56:45-04:00

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
- current_push_authorization: `push-auth-20260427T185308521095Z` (valid=True)
- authorized_head_commit: `aebed8b596358b4c87b58011ce266bc0ff05cd6c`
- approved_target_identity: `tree-receipt-20260427T185308521095Z:a502558eebaecbd4d25b2588bd5acde1fa187219`
- publication_backlog: urgent
- publication_guidance: 25 local commit(s) waiting for governed push. Run `python3 dev/scripts/devctl.py push --execute` now.

### Reviewer runtime
- reviewer_mode: `active_dual_agent`
- reviewer_freshness: unknown
- reviewer_publish_clear: False
- interaction_mode: `remote_control`

### Remote commit pipeline
- state: `n/a`
- approval_state: `n/a`

### Work intake
- active plan: **AI Governance Platform Plan**
- plan path: `dev/active/ai_governance_platform.md`
- active MP scope: `MP-377`
- advisory: `await_review` — review_pending_before_push

## 3. Delta — what changed since the previous snapshot

Range: last 24 commits ending at `f6e3783d7bb3`

- commits: 24
- files changed: 74
- insertions: +6898
- deletions: -2030
- bundle classes touched: tooling, docs
- authority surfaces touched: 7 file(s)

### Commits

| # | SHA | Subject | Files | +/- | Bundle | Risk |
|---|---|---|---|---|---|---|
| 1 | `f6e3783d` | Refresh external review snapshot for 80c1791a | 1 | +43/-43 | tooling |  |
| 2 | `80c1791a` | Refresh external review snapshot for aebed8b5 | 1 | +50/-47 | tooling |  |
| 3 | `aebed8b5` | Refresh external review snapshot for f86e0db2 | 2 | +55/-60 | docs |  |
| 4 | `f86e0db2` | Plan 4.1 catch-22 unblock: push.py import for build_push_ac… | 2 | +59/-58 | tooling |  |
| 5 | `d70b2b6f` | Plan 4.1 catch-22 unblock: post-receipt startup-context ref… | 4 | +236/-64 | tooling |  |
| 6 | `0503204b` | Refresh external review snapshot for 196a2f7f | 1 | +40/-40 | tooling |  |
| 7 | `196a2f7f` | Refresh external review snapshot for f429524b | 1 | +43/-43 | tooling |  |
| 8 | `f429524b` | Refresh external review snapshot for 7e78f6c0 | 1 | +69/-72 | tooling |  |
| 9 | `7e78f6c0` | Refresh external review snapshot for 7bf66f03 | 2 | +81/-82 | docs |  |
| 10 | `7bf66f03` | Plan 4.1 bounded slice: G1 push.py duplicate fix + G2 push_… | 35 | +2281/-513 | tooling |  |
| 11 | `dc4863ea` | Refresh external review snapshot for 1c5e13e2 | 2 | +71/-72 | docs |  |
| 12 | `1c5e13e2` | Plan 4.1 bounded push pre-validation recovery phase + revie… | 22 | +1383/-101 | tooling |  |
| 13 | `ab077ec4` | Refresh external review snapshot for f650da29 | 1 | +49/-46 | tooling |  |
| 14 | `f650da29` | Refresh external review snapshot for ee0558a2 | 2 | +67/-66 | docs |  |
| 15 | `ee0558a2` | Plan 4.1 startup push-state managed-receipt classifier alig… | 18 | +387/-74 | tooling |  |
| 16 | `3db9f243` | Refresh external review snapshot for 1ba92833 | 2 | +78/-82 | docs |  |
| 17 | `1ba92833` | Plan 4.1 Slice C/D repair: commit-pipeline proof identity r… | 33 | +1102/-125 | tooling |  |
| 18 | `dd3a6d44` | Refresh external review snapshot for 46a70116 | 2 | +52/-52 | docs |  |
| 19 | `46a70116` | Refresh external review snapshot for af7d01c7 | 1 | +50/-47 | tooling |  |
| 20 | `af7d01c7` | Refresh external review snapshot for 29e7eeda | 2 | +69/-74 | docs |  |
| 21 | `29e7eeda` | Plan 4.1 Slice C/D repair: proof-tick startup_context autho… | 16 | +455/-91 | tooling |  |
| 22 | `eff88042` | Refresh external review snapshot for 2bc8ba57 | 2 | +52/-52 | docs |  |
| 23 | `2bc8ba57` | Refresh external review snapshot for 33c8ecb8 | 1 | +52/-49 | tooling |  |
| 24 | `33c8ecb8` | Refresh external review snapshot for 2193afad | 2 | +74/-77 | docs |  |

### Files

| Path | Bundle | +/- |
|---|---|---|
| `.github/workflows/release_preflight.yml` | tooling | +1/-0 |
| `.github/workflows/tooling_control_plane.yml` | tooling | +3/-0 |
| `AGENTS.md` | docs | +14/-1 |
| `bridge.md` | docs | +105/-105 |
| `dev/README.md` | docs | +2/-0 |
| `dev/active/INDEX.md` | tooling | +1/-0 |
| `dev/active/MASTER_PLAN.md` | tooling | +82/-0 |
| `dev/active/README.md` | tooling | +4/-0 |
| `dev/active/agent_substrate_architecture_review.md` | tooling | +174/-2 |
| `dev/active/ai_governance_platform.md` | tooling | +163/-2 |
| `dev/audits/AUTOMATION_DEBT_REGISTER.md` | tooling | +8/-0 |
| `dev/audits/REVIEW_SNAPSHOT.md` | tooling | +1348/-1350 |
| `dev/guides/DEVELOPMENT.md` | docs | +28/-1 |
| `dev/guides/SYSTEM_MAP.md` | docs | +6/-6 |
| `dev/history/ENGINEERING_EVOLUTION.md` | tooling | +139/-0 |
| `dev/scripts/README.md` | tooling | +19/-6 |
| `dev/scripts/checks/check_typed_enum_connectivity.py` | tooling | +12/-0 |
| `dev/scripts/checks/review_surface_consistency/README.md` | tooling | +3/-0 |
| `dev/scripts/checks/review_surface_consistency/proof_tick.py` | tooling | +128/-5 |
| `dev/scripts/checks/typed_enum_connectivity/__init__.py` | tooling | +2/-0 |
| `dev/scripts/checks/typed_enum_connectivity/command.py` | tooling | +137/-0 |
| `dev/scripts/checks/typed_enum_connectivity/models.py` | tooling | +88/-0 |
| `dev/scripts/checks/typed_enum_connectivity/scanner.py` | tooling | +254/-0 |
| `dev/scripts/devctl/bundles/registry.py` | tooling | +1/-0 |
| `dev/scripts/devctl/commands/review_channel/launcher_discipline.py` | tooling | +41/-44 |
| `dev/scripts/devctl/commands/vcs/commit_preflight_support.py` | tooling | +2/-4 |
| `dev/scripts/devctl/commands/vcs/governed_executor.py` | tooling | +14/-11 |
| `dev/scripts/devctl/commands/vcs/governed_executor_actions.py` | tooling | +41/-36 |
| `dev/scripts/devctl/commands/vcs/governed_executor_push_result.py` | tooling | +48/-3 |
| `dev/scripts/devctl/commands/vcs/governed_executor_recovery_actions.py` | tooling | +75/-0 |
| `dev/scripts/devctl/commands/vcs/push.py` | tooling | +118/-136 |
| `dev/scripts/devctl/commands/vcs/push_diagnostics.py` | tooling | +7/-1 |
| `dev/scripts/devctl/commands/vcs/push_executor_routing.py` | tooling | +47/-6 |
| `dev/scripts/devctl/commands/vcs/push_findings.py` | tooling | +12/-0 |
| `dev/scripts/devctl/commands/vcs/push_findings_identity.py` | tooling | +137/-0 |
| `dev/scripts/devctl/commands/vcs/push_findings_identity_validation.py` | tooling | +158/-0 |
| `dev/scripts/devctl/commands/vcs/push_findings_payloads.py` | tooling | +163/-0 |
| `dev/scripts/devctl/commands/vcs/push_flow.py` | tooling | +98/-4 |
| `dev/scripts/devctl/commands/vcs/push_git_status.py` | tooling | +47/-0 |
| `dev/scripts/devctl/commands/vcs/push_pipeline_state_sync.py` | tooling | +61/-1 |
| _34 more files trimmed_ | | |

## 4. Quality signals

### Governance review
- total findings: 226
- open: 124
- fixed: 88
- false positives: 0

Recent findings:
- `dogfood.review_channel_post_timeout` — `dev/scripts/devctl/review_channel/event_projection_queue.py` (n/a, verdict=`fixed`)
- `portability_python_310` — `dev/scripts/devctl/runtime/worktree_orphan_inventory_support.py` (p0, verdict=`confirmed_issue`)
- `bridge_content_loss_on_rollover` — `dev/scripts/devctl/review_channel/projections` (class1, verdict=`confirmed_issue`)
- `actor_template_missing` — `dev/scripts/devctl/runtime/review_packet_inbox.py` (medium, verdict=`confirmed_issue`)
- `slice_1_2_rev_11` — `dev/scripts/devctl` (n/a, verdict=`fixed`)
- `x12_provider_name_pin_audit` — `dev/scripts/devctl` (n/a, verdict=`confirmed_issue`)
- `slice_1_2_rev_12` — `dev/scripts/devctl` (n/a, verdict=`fixed`)
- `dogfood.command.check` — `dev/scripts/devctl/commands/check/__init__.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.docs-check` — `dev/scripts/devctl/commands/docs/check.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.check-router` — `dev/scripts/devctl/commands/check/router.py` (n/a, verdict=`confirmed_issue`)

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

- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_actions.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_push_result.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_recovery_actions.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/project_governance_push.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/project_governance_push_ahead.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/review_snapshot_refresh.py`) — Review contract-level invariants for this file
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/governance/push_state_models.py`) — Commit ee0558a2 changed dev/scripts/devctl/governance/push_state_models.py

### Suggested verification commands

- `python3 dev/scripts/devctl.py check --profile ci`
- `python3 dev/scripts/devctl.py probe-report --format md`
- `python3 dev/scripts/devctl.py docs-check --strict-tooling`
- `python3 dev/scripts/devctl.py governance-review --format md`
- `python3 dev/scripts/devctl.py check-router --format md`

## 7. Reasoning — why these changes landed

### Per-commit rationale

- **`f6e3783d`** — Refresh external review snapshot for 80c1791a
  - evolution: Fact: the live `rev_pkt_2019` push attempt proved an automation gap in the publication path. `devctl push` already committed managed bridge, ReviewSnapshot, and generated-surface receipts automatically, but when the pos…
- **`80c1791a`** — Refresh external review snapshot for aebed8b5
  - evolution: Fact: the live `rev_pkt_2019` push attempt proved an automation gap in the publication path. `devctl push` already committed managed bridge, ReviewSnapshot, and generated-surface receipts automatically, but when the pos…
- **`aebed8b5`** — Refresh external review snapshot for f86e0db2
  - evolution: Fact: the live `rev_pkt_2019` push attempt proved an automation gap in the publication path. `devctl push` already committed managed bridge, ReviewSnapshot, and generated-surface receipts automatically, but when the pos…
- **`f86e0db2`** — Plan 4.1 catch-22 unblock: push.py import for build_push_action (rev_pkt_2047 M2 path C completion)
  - evolution: Fact: the live `rev_pkt_2019` push attempt proved an automation gap in the publication path. `devctl push` already committed managed bridge, ReviewSnapshot, and generated-surface receipts automatically, but when the pos…
- **`d70b2b6f`** — Plan 4.1 catch-22 unblock: post-receipt startup-context refresh auto-recovery in push_projection_runtime_refresh + regression test (rev_pkt_2047 M2 path C; bootstrap break for rev_pkt_2039 publication)
  - evolution: Fact: the live `rev_pkt_2019` push attempt proved an automation gap in the publication path. `devctl push` already committed managed bridge, ReviewSnapshot, and generated-surface receipts automatically, but when the pos…
- **`0503204b`** — Refresh external review snapshot for 196a2f7f
  - evolution: Fact: the live `rev_pkt_2019` push attempt proved an automation gap in the publication path. `devctl push` already committed managed bridge, ReviewSnapshot, and generated-surface receipts automatically, but when the pos…
- **`196a2f7f`** — Refresh external review snapshot for f429524b
  - evolution: Fact: the live `rev_pkt_2019` push attempt proved an automation gap in the publication path. `devctl push` already committed managed bridge, ReviewSnapshot, and generated-surface receipts automatically, but when the pos…
- **`f429524b`** — Refresh external review snapshot for 7e78f6c0
  - evolution: Fact: the live `rev_pkt_2019` push attempt proved an automation gap in the publication path. `devctl push` already committed managed bridge, ReviewSnapshot, and generated-surface receipts automatically, but when the pos…
- **`7e78f6c0`** — Refresh external review snapshot for 7bf66f03
  - evolution: Fact: the live `rev_pkt_2019` push attempt proved an automation gap in the publication path. `devctl push` already committed managed bridge, ReviewSnapshot, and generated-surface receipts automatically, but when the pos…
- **`7bf66f03`** — Plan 4.1 bounded slice: G1 push.py duplicate fix + G2 push_findings canonical Finding seam refactor + 3-module split + noqa rationale + MP377-P0-T13..T18 plan rows + ADR-024..027 + 5 regression tests (rev_pkt_2039; supersedes rev_pkt_2034/2037; closes rev_pkt_2029/2030/2032/2035/2041/2042; publishes rev_pkt_1997 + rev_pkt_2003 + rev_pkt_2008 + Codex 13/18/19/23/25/26 fixes)
  - evolution: Fact: the live `rev_pkt_2019` push attempt proved an automation gap in the publication path. `devctl push` already committed managed bridge, ReviewSnapshot, and generated-surface receipts automatically, but when the pos…
- **`dc4863ea`** — Refresh external review snapshot for 1c5e13e2
  - evolution: Fact: the live `rev_pkt_2019` push attempt proved an automation gap in the publication path. `devctl push` already committed managed bridge, ReviewSnapshot, and generated-surface receipts automatically, but when the pos…
- **`1c5e13e2`** — Plan 4.1 bounded push pre-validation recovery phase + reviewer_mode parity authority shift (rev_pkt_2022 + rev_pkt_2024 shape extraction; supersedes rev_pkt_2016/2015; closes rev_pkt_2019/2020/2021/2023; publishes pending rev_pkt_1997 + rev_pkt_2003 + rev_pkt_2008 + Codex 13 fix)
  - evolution: Fact: the live `rev_pkt_2019` push attempt proved an automation gap in the publication path. `devctl push` already committed managed bridge, ReviewSnapshot, and generated-surface receipts automatically, but when the pos…
- **`ab077ec4`** — Refresh external review snapshot for f650da29
  - evolution: Fact: the live `rev_pkt_2019` push attempt proved an automation gap in the publication path. `devctl push` already committed managed bridge, ReviewSnapshot, and generated-surface receipts automatically, but when the pos…
- **`f650da29`** — Refresh external review snapshot for ee0558a2
  - evolution: Fact: the live `rev_pkt_2019` push attempt proved an automation gap in the publication path. `devctl push` already committed managed bridge, ReviewSnapshot, and generated-surface receipts automatically, but when the pos…
- **`ee0558a2`** — Plan 4.1 startup push-state managed-receipt classifier alignment + ahead-commit split classification (rev_pkt_2015; supersedes rev_pkt_2013; closes rev_pkt_2011 + rev_pkt_2014; publishes pending rev_pkt_1997 + rev_pkt_2003 + rev_pkt_2008)
  - evolution: Fact: the live `rev_pkt_2019` push attempt proved an automation gap in the publication path. `devctl push` already committed managed bridge, ReviewSnapshot, and generated-surface receipts automatically, but when the pos…
- **`3db9f243`** — Refresh external review snapshot for 1ba92833
  - evolution: Fact: the live `rev_pkt_2019` push attempt proved an automation gap in the publication path. `devctl push` already committed managed bridge, ReviewSnapshot, and generated-surface receipts automatically, but when the pos…
- **`1ba92833`** — Plan 4.1 Slice C/D repair: commit-pipeline proof identity refresh + typed_enum_connectivity guard + OperatorInteractionMode policy + proof-tick authority priority (rev_pkt_2008; addresses 6 findings from rev_pkt_2006; publishes pending rev_pkt_1997 + rev_pkt_2003)
  - evolution: Fact: the live `rev_pkt_2019` push attempt proved an automation gap in the publication path. `devctl push` already committed managed bridge, ReviewSnapshot, and generated-surface receipts automatically, but when the pos…
- **`dd3a6d44`** — Refresh external review snapshot for 46a70116
  - evolution: Fact: the live `rev_pkt_2019` push attempt proved an automation gap in the publication path. `devctl push` already committed managed bridge, ReviewSnapshot, and generated-surface receipts automatically, but when the pos…
- **`46a70116`** — Refresh external review snapshot for af7d01c7
  - evolution: Fact: the live `rev_pkt_2019` push attempt proved an automation gap in the publication path. `devctl push` already committed managed bridge, ReviewSnapshot, and generated-surface receipts automatically, but when the pos…
- **`af7d01c7`** — Refresh external review snapshot for 29e7eeda
  - evolution: Fact: the live `rev_pkt_2019` push attempt proved an automation gap in the publication path. `devctl push` already committed managed bridge, ReviewSnapshot, and generated-surface receipts automatically, but when the pos…
- **`29e7eeda`** — Plan 4.1 Slice C/D repair: proof-tick startup_context authority + operator_interaction_mode parity + agent substrate architecture review (rev_pkt_2003; closes rev_pkt_2000; publishes pending rev_pkt_1997)
  - evolution: Fact: the live `rev_pkt_2019` push attempt proved an automation gap in the publication path. `devctl push` already committed managed bridge, ReviewSnapshot, and generated-surface receipts automatically, but when the pos…
- **`eff88042`** — Refresh external review snapshot for 2bc8ba57
  - evolution: Fact: live Plan 4.1 dogfood exposed a bad remote-control recovery route. `review-channel status` recommended `recover --recover-provider claude --terminal terminal-app` while the active operator mode was remote-control,…
- **`2bc8ba57`** — Refresh external review snapshot for 33c8ecb8
  - evolution: Fact: live Plan 4.1 dogfood exposed a bad remote-control recovery route. `review-channel status` recommended `recover --recover-provider claude --terminal terminal-app` while the active operator mode was remote-control,…
- **`33c8ecb8`** — Refresh external review snapshot for 2193afad
  - evolution: Fact: live Plan 4.1 dogfood exposed a bad remote-control recovery route. `review-channel status` recommended `recover --recover-provider claude --terminal terminal-app` while the active operator mode was remote-control,…
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

- open governance findings: 124

### Startup advisories
- await_review: review_pending_before_push

### Stale warnings
- Keep editing the current slice.
- Move straight to the governed push path.

### Open gap rows
- **governance_open** (`dev/scripts/devctl/runtime/worktree_orphan_inventory_support.py`): portability_python_310: from datetime import UTC requires Python 3.11+; operator default python3 is pyenv 3.10.4; every devctl call crashes at import on operator shell. Regression from commit dc82fbf1 2026-04-22. Fix: from datetime import datetime, timezone + timezone.utc.
repo_path=/Users/jguida941/testing_upgrade/codex-voice
- **governance_open** (`dev/scripts/devctl/review_channel/projections`): bridge_content_loss_on_rollover: Rollover convergence re-projects bridge from typed current_session authority, overwriting reviewer-checkpoint content. System warning names it explicitly. Every rollover loses prior reviewer decision. Recover-from-event-store fix proposed rev_pkt_1715.
repo_path=/Users/jguida941/testing_upgrade/codex-voice
- **governance_open** (`dev/scripts/devctl/runtime/review_packet_inbox.py`): actor_template_missing: Live repro: first apply call failed with --actor required; retry with --actor claude succeeded. Matches codex Finding 3 independent confirmation. Template review_packet_inbox.py:27 omits --actor in generated command.
repo_path=/Users/jguida941/testing_upgrade/codex-voice
- **governance_open** (`dev/scripts/devctl`): x12_provider_name_pin_audit: X12 audit (16 production-code provider-name pins) posted to codex as rev_pkt_1782; operator-confirmed: identity binds to typed role, not provider name
repo_path=/Users/jguida941/testing_upgrade/codex-voice
- **governance_open** (`dev/scripts/devctl/commands/check/__init__.py`): dogfood.command.check: Auto-ingested devctl finalization failure rc=1.
repo_path=/Users/jguida941/testing_upgrade/codex-voice

---

Projection produced by `devctl review-snapshot`. Generation stamp `snap-679a5b1cf07b` binds this file to HEAD `f6e3783d7bb3`; if they drift, the freshness guard will fail CI. When the latest commit only refreshes this generated snapshot, the guard accepts this file as bound to that commit's parent code state.
