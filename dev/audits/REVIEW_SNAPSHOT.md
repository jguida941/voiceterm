# VoiceTerm — Review Snapshot

> Deterministically generated from typed governance state. Do not edit by hand — rerun `devctl review-snapshot --write`.

## Quick status

- Branch: `extraction/guardir-core-p0-proof-integrity`
- HEAD: `ddaf58f53ed6` — Refresh external review snapshot for f2f152dd
- Tree hash: `8b6484d4e86d`
- Generation stamp: `snap-adab100e020b`
- Generated at (UTC): 2026-05-19T02:38:17Z
- Push decision: `await_checkpoint` — staged_index_budget_exceeded
- Reviewer mode: `tools_only` (interaction: `local_terminal`)
- Pipeline state: `n/a` (approval: `n/a`)
- Delta since last snapshot: 24 commits, 178 files, +28194/-1380
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
- HEAD SHA: `ddaf58f53ed6be2613a7dd6a7ebd752f3a601a46`
- HEAD author: Justin Guida
- HEAD timestamp (UTC): 2026-05-18T20:33:00-04:00

## 2. Governance state

### Push decision
- action: `await_checkpoint`
- reason: staged_index_budget_exceeded
- push_eligible_now: False
- worktree_clean: False
- staged_path_count: 20
- unstaged_path_count: 0
- next_step_command: `n/a`
- latest_push_report_state: `published_remote` (post_push_bundle_pending)
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
- advisory: `checkpoint_before_continue` — staged_index_budget_exceeded
- checkpoint_required: **yes**

## 3. Delta — what changed since the previous snapshot

Range: last 24 commits ending at `ddaf58f53ed6`

- commits: 24
- files changed: 178
- insertions: +28194
- deletions: -1380
- bundle classes touched: tooling, docs
- authority surfaces touched: 13 file(s)

### Commits

| # | SHA | Subject | Files | +/- | Bundle | Risk |
|---|---|---|---|---|---|---|
| 1 | `ddaf58f5` | Refresh external review snapshot for f2f152dd | 1 | +67/-64 | tooling |  |
| 2 | `f2f152dd` | Phase 0A: bridge and boot-card projection kill-switch | 18 | +328/-224 | tooling |  |
| 3 | `b161e95b` | Phase 0.6.C: AGENTS.md vs CLAUDE.md projection-parity viola… | 2 | +2/-2 | tooling |  |
| 4 | `286b8703` | Phase 0.6.A: add alias-authority-parity guardrail | 2 | +2/-1 | tooling |  |
| 5 | `87f1248e` | Narrow Phase 0.6 to entrypoint, bridge containment, and top… | 2 | +69/-68 | tooling |  |
| 6 | `815901f4` | Refresh external review snapshot for b16d00a4 | 2 | +72/-74 | docs |  |
| 7 | `b16d00a4` | Phase 0.4-Bootstrap IMPLEMENTATION: launcher + post authori… | 21 | +900/-13 | tooling |  |
| 8 | `b85ed85a` | Phase 0.6 amendment: Entry-Point Hardening + Bridge Retirem… | 2 | +96/-1 | tooling |  |
| 9 | `f453f8c1` | Refresh external review snapshot for f6ef179c | 2 | +56/-53 | docs |  |
| 10 | `f6ef179c` | Phase 0.4-Bootstrap amendment: Bootstrap/Launcher/Topology… | 2 | +55/-1 | tooling |  |
| 11 | `5bf86443` | Refresh external review snapshot for 4b51058a | 1 | +42/-42 | tooling |  |
| 12 | `4b51058a` | Refresh external review snapshot for 50039a1b | 2 | +49/-43 | tooling |  |
| 13 | `50039a1b` | Phase 0.4: Sync canonical GuardIR extraction plan | 1 | +386/-65 | tooling |  |
| 14 | `bf21b66a` | Refresh external review snapshot for ccf6b4f5 | 2 | +49/-48 | docs |  |
| 15 | `ccf6b4f5` | Phase 0.1: Preserve cached-hammock + may17 + approved extra… | 4 | +6246/-0 | tooling |  |
| 16 | `d92dc2ff` | Refresh external review snapshot for 92ef4032 | 2 | +73/-65 | docs |  |
| 17 | `92ef4032` | UNREVIEWED PRESERVATION SNAPSHOT — voiceterm governance pat… | 69 | +7933/-165 | tooling |  |
| 18 | `835060c2` | Refresh external review snapshot for 47944776 | 2 | +80/-74 | docs |  |
| 19 | `47944776` | Add semantic output consumption gates | 67 | +6820/-72 | tooling |  |
| 20 | `85932c69` | Refresh external review snapshot for 6859108d | 2 | +79/-72 | docs |  |
| 21 | `6859108d` | Add publication scope integrity guard | 7 | +395/-5 | tooling |  |
| 22 | `4529338e` | Enforce successful closure proof for plan rows | 62 | +4313/-163 | tooling |  |
| 23 | `a066d4c7` | Refresh external review snapshot for e5354d23 | 2 | +67/-65 | docs |  |
| 24 | `e5354d23` | Backfill P13 applied plan row | 3 | +15/-0 | tooling |  |

### Files

| Path | Bundle | +/- |
|---|---|---|
| `.github/workflows/release_preflight.yml` | tooling | +3/-0 |
| `.github/workflows/tooling_control_plane.yml` | tooling | +9/-0 |
| `AGENTS.md` | docs | +9/-8 |
| `bridge.md` | docs | +66/-188 |
| `dev/active/MASTER_PLAN.md` | tooling | +109/-0 |
| `dev/active/ai_governance_platform.md` | tooling | +18/-1 |
| `dev/audits/REVIEW_SNAPSHOT.md` | tooling | +608/-577 |
| `dev/audits/plan_intake/2026-05-18-cached-hammock-role-audit.md` | tooling | +4314/-0 |
| `dev/audits/plan_intake/2026-05-18-guardir-extraction-plan.md` | tooling | +1224/-140 |
| `dev/audits/plan_intake/2026-05-18-may17-plan.md` | tooling | +1373/-0 |
| `dev/audits/plan_intake/sha256-manifest.txt` | tooling | +9/-6 |
| `dev/guides/DEVELOPMENT.md` | docs | +5/-0 |
| `dev/guides/SYSTEM_MAP.md` | docs | +33/-33 |
| `dev/history/ENGINEERING_EVOLUTION.md` | tooling | +18/-0 |
| `dev/scripts/README.md` | tooling | +6/-0 |
| `dev/scripts/checks/check_bridge_projection_only.py` | tooling | +47/-0 |
| `dev/scripts/checks/check_command_output_consumed.py` | tooling | +12/-0 |
| `dev/scripts/checks/check_control_decision_consistency.py` | tooling | +12/-0 |
| `dev/scripts/checks/check_control_decision_obeyed.py` | tooling | +12/-0 |
| `dev/scripts/checks/check_feature_has_proof_receipt.py` | tooling | +65/-1 |
| `dev/scripts/checks/check_launcher_authority_ordering.py` | tooling | +12/-0 |
| `dev/scripts/checks/check_packet_absorption_required.py` | tooling | +12/-0 |
| `dev/scripts/checks/check_plan_gold_claims_resolve.py` | tooling | +15/-0 |
| `dev/scripts/checks/check_plan_metric_freshness.py` | tooling | +12/-0 |
| `dev/scripts/checks/check_publication_scope_integrity.py` | tooling | +477/-2 |
| `dev/scripts/checks/check_substrate_commits_have_applied_plan_row.py` | tooling | +67/-7 |
| `dev/scripts/checks/command_output_consumed/__init__.py` | tooling | +1/-0 |
| `dev/scripts/checks/command_output_consumed/command.py` | tooling | +120/-0 |
| `dev/scripts/checks/control_decision_consistency/__init__.py` | tooling | +1/-0 |
| `dev/scripts/checks/control_decision_consistency/command.py` | tooling | +116/-0 |
| `dev/scripts/checks/control_decision_obeyed/__init__.py` | tooling | +1/-0 |
| `dev/scripts/checks/control_decision_obeyed/command.py` | tooling | +109/-0 |
| `dev/scripts/checks/launcher_authority_ordering/__init__.py` | tooling | +1/-0 |
| `dev/scripts/checks/launcher_authority_ordering/command.py` | tooling | +230/-0 |
| `dev/scripts/checks/packet_absorption_required/__init__.py` | tooling | +1/-0 |
| `dev/scripts/checks/packet_absorption_required/command.py` | tooling | +149/-0 |
| `dev/scripts/checks/plan_gold_claims_resolve/__init__.py` | tooling | +1/-0 |
| `dev/scripts/checks/plan_gold_claims_resolve/command.py` | tooling | +282/-0 |
| `dev/scripts/checks/plan_gold_claims_resolve/symbol_index.py` | tooling | +170/-0 |
| `dev/scripts/checks/plan_metric_freshness/__init__.py` | tooling | +1/-0 |
| _138 more files trimmed_ | | |

## 4. Quality signals

### Governance review
- total findings: 26
- open: 26
- fixed: 0
- false positives: 0

Recent findings:
- `dogfood.command.test-python` — `dev/scripts/devctl/commands/python_tests.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.test-python` — `dev/scripts/devctl/commands/python_test_runner/command.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.process-cleanup` — `dev/scripts/devctl/commands/process/cleanup.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.install-git-hooks` — `dev/scripts/devctl/commands/governance/install_git_hooks.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.relaunch-loop` — `dev/scripts/devctl/commands/relaunch_loop.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.relaunch-loop` — `dev/scripts/devctl/commands/governance/relaunch_loop.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.render-surfaces` — `dev/scripts/devctl/commands/governance/render_surfaces.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.remote-control` — `dev/scripts/devctl/commands/remote_control/command.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.probe-report` — `dev/scripts/devctl/commands/probe_report.py` (n/a, verdict=`confirmed_issue`)
- `role_oriented_packet_inbox` — `dev/scripts/devctl/review_channel/event_reducer_inbox.py` (high, verdict=`confirmed_issue`)

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
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/review_channel/bridge_action_prepare.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/review_channel/bridge_handler.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/review_channel/bridge_success_report.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/review_channel/bridge_support.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/project_governance_push.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/reviewer_runtime_models.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/reviewer_runtime_parser.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/runtime/test_startup_context.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_sync.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/commands/check/test_check_router.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/vcs/test_governed_executor.py`) — Review contract-level invariants for this file
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/tests/checks/test_check_agents_contract.py`) — Commit f2f152dd changed dev/scripts/devctl/tests/checks/test_check_agents_contract.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/governance/push_state_models.py`) — Commit 92ef4032 changed dev/scripts/devctl/governance/push_state_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/review_channel/event_models.py`) — Commit 92ef4032 changed dev/scripts/devctl/review_channel/event_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/agent_loop_decision_models.py`) — Commit 92ef4032 changed dev/scripts/devctl/runtime/agent_loop_decision_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/review_state_packet_models.py`) — Commit 92ef4032 changed dev/scripts/devctl/runtime/review_state_packet_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/reviewer_runtime_models.py`) — Commit 92ef4032 changed dev/scripts/devctl/runtime/reviewer_runtime_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/startup_context_models.py`) — Commit 92ef4032 changed dev/scripts/devctl/runtime/startup_context_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/work_intake_models.py`) — Commit 92ef4032 changed dev/scripts/devctl/runtime/work_intake_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/python_test_contract.py`) — Commit 4529338e changed dev/scripts/devctl/runtime/python_test_contract.py

### Suggested verification commands

- `python3 dev/scripts/devctl.py check --profile ci`
- `python3 dev/scripts/devctl.py probe-report --format md`
- `python3 dev/scripts/devctl.py docs-check --strict-tooling`
- `python3 dev/scripts/devctl.py governance-review --format md`
- `python3 dev/scripts/devctl.py check-router --format md`

## 7. Reasoning — why these changes landed

### Per-commit rationale

- **`ddaf58f5`** — Refresh external review snapshot for f2f152dd
- **`f2f152dd`** — Phase 0A: bridge and boot-card projection kill-switch
- **`b161e95b`** — Phase 0.6.C: AGENTS.md vs CLAUDE.md projection-parity violation captured
  - Operator-mandated 2026-05-18T~18:00 EDT. Empirical evidence that the topology-hardcode-via-projection bug source is dev/scripts/devctl/governance/instruction_boot_card.py — the template that generates AGENTS.md AND CLAUDE.md from render-surfaces. Both projections SHOULD be byte-equal (modulo surface_id marker) since any agent can play any role per cached-hammock P58.5, but they currently diverge on 8 lines hardcoding --role reviewer --actor codex (AGENTS.md) vs --role implementer --actor claude (CLAUDE.md).
- **`286b8703`** — Phase 0.6.A: add alias-authority-parity guardrail
  - Operator-mandated 2026-05-18T~17:45 EDT. Single guardrail added to Phase 0.6.A green criteria: no command alias may parse into a different authority model than /develop. /goal, /check-it, /archive-evidence, /session-log must be adapters into the SAME typed path as /develop, not parallel command systems. Regression test: byte-for-byte packet/event payload equality (modulo timestamp/id) between alias invocation and canonical /develop action.
- **`87f1248e`** — Narrow Phase 0.6 to entrypoint, bridge containment, and topology guards
  - Plan-only correction per operator scope-discipline directive 2026-05-18T~17:30 EDT. Phase 0.6 is scoped to bounded substrate guardrails before Phase 1 proof-integrity, not full bridge retirement or full N-agent topology refactor.
- **`815901f4`** — Refresh external review snapshot for b16d00a4
- **`b16d00a4`** — Phase 0.4-Bootstrap IMPLEMENTATION: launcher + post authority-ordering fix
  - Operator-issued 2026-05-18T~17:30 EDT. This commit lands the Phase 0.4-Bootstrap implementation files codex shipped during exec session (PID 61481, session 019e3cc2-c993-75c1-851a-24866d133b5d). Prior commit b85ed85a was the Phase 0.6 PLAN AMENDMENT only — this commit makes the Phase 0.4 IMPLEMENTATION durable on GuardIR extraction branch.
- **`b85ed85a`** — Phase 0.6 amendment: Entry-Point Hardening + Bridge Retirement + Role-Based Topology
  - Operator amendment 2026-05-18T~17:00 EDT. Threads three architectural root-cause concerns already specified in cached-hammock plan into canonical extraction plan as Phase 0.6 (lands BEFORE Phase 1 P0 proof-integrity).
- **`f453f8c1`** — Refresh external review snapshot for f6ef179c
- **`f6ef179c`** — Phase 0.4-Bootstrap amendment: Bootstrap/Launcher/Topology Reliability + authority-ordering defect
  - Operator amendment 2026-05-18T~16:30 EDT.
- **`5bf86443`** — Refresh external review snapshot for 4b51058a
- **`4b51058a`** — Refresh external review snapshot for 50039a1b
- **`50039a1b`** — Phase 0.4: Sync canonical GuardIR extraction plan
  - Operator-approved plan update (2026-05-18T~16:00 EDT via ChatGPT review chain):
  - - Replace stale 558-line plan-intake version with 879-line current text
  - - Correct trunk root from d92dc2ff (auto ReviewSnapshot artifact) to 92ef4032 (actual UNREVIEWED PRESERVATION SNAPSHOT content commit)
- **`bf21b66a`** — Refresh external review snapshot for ccf6b4f5
- **`ccf6b4f5`** — Phase 0.1: Preserve cached-hammock + may17 + approved extraction plan into typed state
  - Operator-issued 2026-05-18T~14:50Z UTC. UNREVIEWED PRESERVATION COMMIT — emergency preservation mode (Phase 1 P0 proof-integrity not yet fixed; raw --no-verify per operator's pre-approved preservation pattern from today's R416 round).
- **`d92dc2ff`** — Refresh external review snapshot for 92ef4032
- **`92ef4032`** — UNREVIEWED PRESERVATION SNAPSHOT — voiceterm governance patch quarantine
  - Operator-issued 2026-05-18T~14:30Z UTC. This is an emergency preservation
  - snapshot, NOT a release commit. It captures the 69-path uncommitted
  - governance patch + 3 untracked files from working tree of
- **`835060c2`** — Refresh external review snapshot for 47944776
- **`47944776`** — Add semantic output consumption gates
- **`85932c69`** — Refresh external review snapshot for 6859108d
- **`6859108d`** — Add publication scope integrity guard
- **`4529338e`** — Enforce successful closure proof for plan rows
- **`a066d4c7`** — Refresh external review snapshot for e5354d23
- **`e5354d23`** — Backfill P13 applied plan row
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
- checkpoint_before_continue: staged_index_budget_exceeded

### Stale warnings
- Keep editing the current slice.
- Move straight to the governed push path.

### Open gap rows
- **governance_open** (`dev/scripts/devctl/commands/python_tests.py`): dogfood.command.test-python: Auto-ingested devctl finalization failure rc=1.
repo_path=/Users/jguida941/testing_upgrade/codex-voice
- **governance_open** (`dev/scripts/devctl/commands/python_test_runner/command.py`): dogfood.command.test-python: Auto-ingested devctl finalization failure rc=1.
repo_path=/Users/jguida941/testing_upgrade/codex-voice
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

---

Projection produced by `devctl review-snapshot`. Generation stamp `snap-adab100e020b` binds this file to HEAD `ddaf58f53ed6`; if they drift, the freshness guard will fail CI. When the latest commit only refreshes this generated snapshot, the guard accepts this file as bound to that commit's parent code state.
