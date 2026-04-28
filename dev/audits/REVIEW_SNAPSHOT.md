# VoiceTerm — Review Snapshot

> Deterministically generated from typed governance state. Do not edit by hand — rerun `devctl review-snapshot --write`.

## Quick status

- Branch: `feature/governance-quality-sweep`
- HEAD: `5af77734d8ca` — Refresh external review snapshot for f259c8eb
- Tree hash: `570af1c1fdc5`
- Generation stamp: `snap-415bb6c30d6d`
- Generated at (UTC): 2026-04-28T21:12:09Z
- Push decision: `run_devctl_push` — push_preconditions_satisfied
- Reviewer mode: `active_dual_agent` (interaction: `remote_control`)
- Pipeline state: `n/a` (approval: `n/a`)
- Delta since last snapshot: 24 commits, 72 files, +5049/-1770
- Governance findings: 126 open / 88 fixed / 228 total
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
- HEAD SHA: `5af77734d8ca2266d42203a4ed95dff219a22455`
- HEAD author: Justin Guida
- HEAD timestamp (UTC): 2026-04-28T17:09:20-04:00

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
- current_push_authorization: `push-auth-20260428T210759796527Z` (valid=True)
- authorized_head_commit: `5af77734d8ca2266d42203a4ed95dff219a22455`
- approved_target_identity: `tree-receipt-20260428T210759796527Z:7ba30411456ba8a7ccba27d63b228cffac6bf3f0`
- publication_backlog: urgent
- publication_guidance: 78 local commit(s) waiting for governed push. Run `python3 dev/scripts/devctl.py push --execute` now.

### Reviewer runtime
- reviewer_mode: `active_dual_agent`
- reviewer_freshness: unknown
- reviewer_publish_clear: False
- interaction_mode: `remote_control`
- implementation_blocked: yes — runtime_missing

### Remote commit pipeline
- state: `n/a`
- approval_state: `n/a`

### Work intake
- active plan: **AI Governance Platform Plan**
- plan path: `dev/active/ai_governance_platform.md`
- active MP scope: `MP-377`
- advisory: `repair_reviewer_loop` — runtime_missing

## 3. Delta — what changed since the previous snapshot

Range: last 24 commits ending at `5af77734d8ca`

- commits: 24
- files changed: 72
- insertions: +5049
- deletions: -1770
- bundle classes touched: docs, tooling
- authority surfaces touched: 4 file(s)

### Commits

| # | SHA | Subject | Files | +/- | Bundle | Risk |
|---|---|---|---|---|---|---|
| 1 | `5af77734` | Refresh external review snapshot for f259c8eb | 2 | +69/-70 | docs |  |
| 2 | `f259c8eb` | Plan 4.1 / MP-377 Codex 42 slice — Layer H push-identity du… | 11 | +227/-81 | tooling |  |
| 3 | `00eb5fd7` | Refresh external review snapshot for cce19014 | 2 | +48/-48 | docs |  |
| 4 | `cce19014` | Refresh external review snapshot for 06f6d2b2 | 1 | +50/-47 | tooling |  |
| 5 | `06f6d2b2` | Refresh external review snapshot for 5adc6ebd | 2 | +91/-70 | docs |  |
| 6 | `5adc6ebd` | Plan 4.1 / MP-377 Codex 41 slice — events.py NameError fix… | 56 | +2716/-386 | tooling |  |
| 7 | `acf4ae3d` | Refresh external review snapshot for f971174a | 2 | +61/-67 | docs |  |
| 8 | `f971174a` | Refresh external review snapshot for b5e92596 | 2 | +48/-48 | docs |  |
| 9 | `b5e92596` | Refresh external review snapshot for f06b2658 | 1 | +47/-44 | tooling |  |
| 10 | `f06b2658` | Refresh external review snapshot for b113e951 | 2 | +60/-63 | docs |  |
| 11 | `b113e951` | Managed projection receipt: SYSTEM_MAP.md auto-refresh from… | 2 | +50/-51 | tooling |  |
| 12 | `125bd6ea` | Refresh external review snapshot for a946ba66 | 1 | +53/-50 | tooling |  |
| 13 | `a946ba66` | Refresh external review snapshot for d5f2c214 | 2 | +71/-61 | docs |  |
| 14 | `d5f2c214` | Plan 4.1 final layer — completed-handoff outcome → current_… | 10 | +814/-119 | tooling |  |
| 15 | `951ba609` | Refresh external review snapshot for 2df8a969 | 2 | +54/-57 | docs |  |
| 16 | `2df8a969` | Refresh external review snapshot for 8f412975 | 1 | +40/-40 | tooling |  |
| 17 | `8f412975` | Refresh external review snapshot for 10ab0bce | 2 | +42/-42 | docs |  |
| 18 | `10ab0bce` | Refresh external review snapshot for 22fcd435 | 1 | +62/-78 | tooling |  |
| 19 | `22fcd435` | Refresh external review snapshot for 00b8340f | 2 | +55/-58 | docs |  |
| 20 | `00b8340f` | Plan 4.1 live-runtime completed-handoff matcher fix (Codex… | 4 | +187/-72 | tooling |  |
| 21 | `20f1e4b6` | Refresh external review snapshot for cd3a1fb0 | 2 | +44/-44 | docs |  |
| 22 | `cd3a1fb0` | Refresh external review snapshot for 7a5b14a5 | 1 | +68/-85 | tooling |  |
| 23 | `7a5b14a5` | Refresh external review snapshot for ce90a950 | 2 | +43/-43 | docs |  |
| 24 | `ce90a950` | Refresh external review snapshot for ddf7bfe1 | 1 | +49/-46 | tooling |  |

### Files

| Path | Bundle | +/- |
|---|---|---|
| `AGENTS.md` | docs | +8/-0 |
| `app/operator_console/state/core/models.py` | tooling | +1/-0 |
| `app/operator_console/state/snapshots/dashboard_snapshot.py` | tooling | +28/-0 |
| `app/operator_console/state/snapshots/snapshot_builder.py` | tooling | +3/-1 |
| `bridge.md` | docs | +61/-61 |
| `dev/active/MASTER_PLAN.md` | tooling | +27/-0 |
| `dev/active/ai_governance_platform.md` | tooling | +10/-1 |
| `dev/audits/REVIEW_SNAPSHOT.md` | tooling | +1283/-1293 |
| `dev/guides/DEVELOPMENT.md` | docs | +14/-3 |
| `dev/guides/SYSTEM_MAP.md` | docs | +9/-9 |
| `dev/history/ENGINEERING_EVOLUTION.md` | tooling | +101/-0 |
| `dev/scripts/README.md` | tooling | +23/-4 |
| `dev/scripts/checks/review_channel_bridge/report.py` | tooling | +53/-96 |
| `dev/scripts/checks/review_channel_bridge/typed_state.py` | tooling | +150/-0 |
| `dev/scripts/checks/tandem_consistency/implementer_checks.py` | tooling | +7/-9 |
| `dev/scripts/checks/tandem_consistency/support.py` | tooling | +0/-45 |
| `dev/scripts/devctl/cli_parser/claude_loop.py` | tooling | +44/-0 |
| `dev/scripts/devctl/cli_parser/entrypoint.py` | tooling | +17/-2 |
| `dev/scripts/devctl/commands/dashboard.py` | tooling | +32/-44 |
| `dev/scripts/devctl/commands/dashboard_render/__init__.py` | tooling | +26/-3 |
| `dev/scripts/devctl/commands/dashboard_render/typed_state.py` | tooling | +98/-0 |
| `dev/scripts/devctl/commands/listing.py` | tooling | +1/-0 |
| `dev/scripts/devctl/commands/mobile_status.py` | tooling | +22/-0 |
| `dev/scripts/devctl/commands/reporting/claude_loop.py` | tooling | +152/-0 |
| `dev/scripts/devctl/commands/reporting/dashboard_follow.py` | tooling | +74/-0 |
| `dev/scripts/devctl/commands/reporting/dashboard_views.py` | tooling | +34/-0 |
| `dev/scripts/devctl/commands/vcs/governed_executor_commit_runtime.py` | tooling | +15/-1 |
| `dev/scripts/devctl/commands/vcs/governed_executor_packets.py` | tooling | +48/-0 |
| `dev/scripts/devctl/commands/vcs/push.py` | tooling | +7/-0 |
| `dev/scripts/devctl/commands/vcs/push_findings_identity_validation.py` | tooling | +5/-0 |
| `dev/scripts/devctl/commands/vcs/push_recovery_loop_state.py` | tooling | +11/-2 |
| `dev/scripts/devctl/review_channel/ack_freshness_authority.py` | tooling | +63/-0 |
| `dev/scripts/devctl/review_channel/bridge_validation.py` | tooling | +34/-4 |
| `dev/scripts/devctl/review_channel/event_projection_ack_state.py` | tooling | +54/-0 |
| `dev/scripts/devctl/review_channel/event_projection_assembly.py` | tooling | +5/-1 |
| `dev/scripts/devctl/review_channel/event_projection_bridge.py` | tooling | +6/-0 |
| `dev/scripts/devctl/review_channel/event_projection_current_session.py` | tooling | +22/-2 |
| `dev/scripts/devctl/review_channel/event_reducer_ack_projection.py` | tooling | +304/-0 |
| `dev/scripts/devctl/review_channel/event_reducer_state.py` | tooling | +7/-1 |
| `dev/scripts/devctl/review_channel/events.py` | tooling | +5/-22 |
| _32 more files trimmed_ | | |

## 4. Quality signals

### Governance review
- total findings: 228
- open: 126
- fixed: 88
- false positives: 0

Recent findings:
- `bridge_content_loss_on_rollover` — `dev/scripts/devctl/review_channel/projections` (class1, verdict=`confirmed_issue`)
- `actor_template_missing` — `dev/scripts/devctl/runtime/review_packet_inbox.py` (medium, verdict=`confirmed_issue`)
- `slice_1_2_rev_11` — `dev/scripts/devctl` (n/a, verdict=`fixed`)
- `x12_provider_name_pin_audit` — `dev/scripts/devctl` (n/a, verdict=`confirmed_issue`)
- `slice_1_2_rev_12` — `dev/scripts/devctl` (n/a, verdict=`fixed`)
- `dogfood.command.check` — `dev/scripts/devctl/commands/check/__init__.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.docs-check` — `dev/scripts/devctl/commands/docs/check.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.check-router` — `dev/scripts/devctl/commands/check/router.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.push` — `dev/scripts/devctl/commands/vcs/push.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.commit` — `dev/scripts/devctl/commands/vcs/commit.py` (n/a, verdict=`confirmed_issue`)

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

- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_commit_runtime.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_packets.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/review_channel/bridge_validation.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/vcs/test_governed_executor.py`) — Review contract-level invariants for this file
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/review_channel/prompt_contract.py`) — Commit 5adc6ebd changed dev/scripts/devctl/review_channel/prompt_contract.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/review_state_models.py`) — Commit 5adc6ebd changed dev/scripts/devctl/runtime/review_state_models.py

### Suggested verification commands

- `python3 dev/scripts/devctl.py check --profile ci`
- `python3 dev/scripts/devctl.py probe-report --format md`
- `python3 dev/scripts/devctl.py docs-check --strict-tooling`
- `python3 dev/scripts/devctl.py governance-review --format md`
- `python3 dev/scripts/devctl.py check-router --format md`

## 7. Reasoning — why these changes landed

### Per-commit rationale

- **`5af77734`** — Refresh external review snapshot for f259c8eb
  - evolution: Fact: push preflight can legitimately move `HEAD` by committing policy-owned generated surfaces, `bridge.md`, and ReviewSnapshot receipt artifacts before publication. `publication_authorization_decision` already accepte…
- **`f259c8eb` | MPs: MP-377** — Plan 4.1 / MP-377 Codex 42 slice — Layer H push-identity duplicate-elimination via reuse of publication_authorization_decision chain-membership authority
  - Closes the 5th gate from this evening's prose-vs-typed-state pattern: governed push identity validation now consumes the same managed receipt-chain authority already proven by `publication_authorization_decision`, so receipt commits above an approved content commit do not trigger a duplicate `ApprovedTargetIdentityViolation`. Preserves fail-closed against fixture/stale/non-managed HEAD drift per memory rule feedback_branch_identity_invariant_required.md (Codex 18 escalation invariants).
  - plan: `dev/active/ai_governance_platform.md`
  - evolution: Fact: push preflight can legitimately move `HEAD` by committing policy-owned generated surfaces, `bridge.md`, and ReviewSnapshot receipt artifacts before publication. `publication_authorization_decision` already accepte…
- **`00eb5fd7`** — Refresh external review snapshot for cce19014
  - evolution: Fact: push preflight can legitimately move `HEAD` by committing policy-owned generated surfaces, `bridge.md`, and ReviewSnapshot receipt artifacts before publication. `publication_authorization_decision` already accepte…
- **`cce19014`** — Refresh external review snapshot for 06f6d2b2
  - evolution: Fact: push preflight can legitimately move `HEAD` by committing policy-owned generated surfaces, `bridge.md`, and ReviewSnapshot receipt artifacts before publication. `publication_authorization_decision` already accepte…
- **`06f6d2b2`** — Refresh external review snapshot for 5adc6ebd
  - evolution: Fact: push preflight can legitimately move `HEAD` by committing policy-owned generated surfaces, `bridge.md`, and ReviewSnapshot receipt artifacts before publication. `publication_authorization_decision` already accepte…
- **`5adc6ebd` | MPs: MP-377** — Plan 4.1 / MP-377 Codex 41 slice — events.py NameError fix + Layer F handoff packet auto-emit (α + β) + Layer G typed liveness producer
  - This slice closes the typed-handoff-before-task-complete meta-pattern that all prior Codex sessions (33/35/37/39/40) skipped:
  -   - Layer F-α (in-Codex): bootstrap promotes typed stage_commit_pipeline action_request emission to PRIMARY contract; Codex 41 itself proved this works by posting rev_pkt_2116 from=codex to=claude as the LAST tool action before TASK_COMPLETE, target_ref=devctl_commit:acf4ae3d, full_guard_bundle_evidence=--profile ci.
  -   - Layer F-β (launcher backup): launch_script_watchdog session-end guard now auto-emits stage_commit_pipeline if Codex's task_complete event lacks a matching packet — fail-closed against partial-exit deadlocks.
  - plan: `dev/active/ai_governance_platform.md`
  - evolution: Fact: push preflight can legitimately move `HEAD` by committing policy-owned generated surfaces, `bridge.md`, and ReviewSnapshot receipt artifacts before publication. `publication_authorization_decision` already accepte…
- **`acf4ae3d`** — Refresh external review snapshot for f971174a
  - evolution: Fact: push preflight can legitimately move `HEAD` by committing policy-owned generated surfaces, `bridge.md`, and ReviewSnapshot receipt artifacts before publication. `publication_authorization_decision` already accepte…
- **`f971174a`** — Refresh external review snapshot for b5e92596
  - evolution: Fact: push preflight can legitimately move `HEAD` by committing policy-owned generated surfaces, `bridge.md`, and ReviewSnapshot receipt artifacts before publication. `publication_authorization_decision` already accepte…
- **`b5e92596`** — Refresh external review snapshot for f06b2658
  - evolution: Fact: push preflight can legitimately move `HEAD` by committing policy-owned generated surfaces, `bridge.md`, and ReviewSnapshot receipt artifacts before publication. `publication_authorization_decision` already accepte…
- **`f06b2658`** — Refresh external review snapshot for b113e951
  - evolution: Fact: push preflight can legitimately move `HEAD` by committing policy-owned generated surfaces, `bridge.md`, and ReviewSnapshot receipt artifacts before publication. `publication_authorization_decision` already accepte…
- **`b113e951`** — Managed projection receipt: SYSTEM_MAP.md auto-refresh from Codex 39 contract changes (Plan 4.1 final layer)
  - Generated by render-surfaces during push v12 preflight; pre-commit hook now passes via Codex 39's typed ACK projection (implementer_ack_state=current). Cleans the staged index left by push v12 preflight so push v13 can proceed.
  - evolution: Fact: push preflight can legitimately move `HEAD` by committing policy-owned generated surfaces, `bridge.md`, and ReviewSnapshot receipt artifacts before publication. `publication_authorization_decision` already accepte…
- **`125bd6ea`** — Refresh external review snapshot for a946ba66
  - evolution: Fact: push preflight can legitimately move `HEAD` by committing policy-owned generated surfaces, `bridge.md`, and ReviewSnapshot receipt artifacts before publication. `publication_authorization_decision` already accepte…
- **`a946ba66`** — Refresh external review snapshot for d5f2c214
  - evolution: Fact: push preflight can legitimately move `HEAD` by committing policy-owned generated surfaces, `bridge.md`, and ReviewSnapshot receipt artifacts before publication. `publication_authorization_decision` already accepte…
- **`d5f2c214`** — Plan 4.1 final layer — completed-handoff outcome → current_session.implementer_ack_* projection (Codex 39):
  - Layer 1 (projection gap close): new event_reducer_ack_projection.py (+304) wired from event_reducer_state.py:142 — packet_applied for stage_commit_pipeline now translates the typed AgentSessionOutcomeState into current_session.implementer_ack_revision/implementer_ack/implementer_ack_state="current" via the proper event_projection_assembly.py boundary. Idempotent replay; fail-closed when outcome cannot be matched (provider mismatch, off-chain revision, temporal violation).
  - evolution: Fact: push preflight can legitimately move `HEAD` by committing policy-owned generated surfaces, `bridge.md`, and ReviewSnapshot receipt artifacts before publication. `publication_authorization_decision` already accepte…
- **`951ba609`** — Refresh external review snapshot for 2df8a969
  - evolution: Fact: push preflight can legitimately move `HEAD` by committing policy-owned generated surfaces, `bridge.md`, and ReviewSnapshot receipt artifacts before publication. `publication_authorization_decision` already accepte…
- **`2df8a969`** — Refresh external review snapshot for 8f412975
  - evolution: Fact: push preflight can legitimately move `HEAD` by committing policy-owned generated surfaces, `bridge.md`, and ReviewSnapshot receipt artifacts before publication. `publication_authorization_decision` already accepte…
- **`8f412975`** — Refresh external review snapshot for 10ab0bce
  - evolution: Fact: push preflight can legitimately move `HEAD` by committing policy-owned generated surfaces, `bridge.md`, and ReviewSnapshot receipt artifacts before publication. `publication_authorization_decision` already accepte…
- **`10ab0bce`** — Refresh external review snapshot for 22fcd435
  - evolution: Fact: push preflight can legitimately move `HEAD` by committing policy-owned generated surfaces, `bridge.md`, and ReviewSnapshot receipt artifacts before publication. `publication_authorization_decision` already accepte…
- **`22fcd435`** — Refresh external review snapshot for 00b8340f
  - evolution: Fact: push preflight can legitimately move `HEAD` by committing policy-owned generated surfaces, `bridge.md`, and ReviewSnapshot receipt artifacts before publication. `publication_authorization_decision` already accepte…
- **`00b8340f`** — Plan 4.1 live-runtime completed-handoff matcher fix (Codex 37): event_projection_current_session.py metadata-free matcher now accepts devctl_commit:<sha> target_ref when both outcome target_revision AND ref revision (including unambiguous abbreviated SHA) are in the same managed-receipt chain (fixes target_revision/target_ref equality strict-check that rejected valid handoffs where receipts accumulated above content commit) + push_recovery_loop_state.py merges parsed compact startup output with extracted typed record fields (initial bypass evaluation no longer requires startup-context/ensure loop cost) + +4 live-shape regression tests in test_push.py covering abbreviated-SHA matching + receipts-above-content-commit + merged startup payload acceptance; full check --profile ci 40/42 (only expected dirty-checkpoint + stale-implementer-ACK live-state gates remaining); test_push.py 95 tests passed; closes the live-runtime bypass mismatch that pushes v6/v7/v8 hit despite Codex 33+34+35's prior fixes
  - evolution: Fact: push preflight can legitimately move `HEAD` by committing policy-owned generated surfaces, `bridge.md`, and ReviewSnapshot receipt artifacts before publication. `publication_authorization_decision` already accepte…
- **`20f1e4b6`** — Refresh external review snapshot for cd3a1fb0
  - evolution: Fact: push preflight can legitimately move `HEAD` by committing policy-owned generated surfaces, `bridge.md`, and ReviewSnapshot receipt artifacts before publication. `publication_authorization_decision` already accepte…
- **`cd3a1fb0`** — Refresh external review snapshot for 7a5b14a5
  - evolution: Fact: push preflight can legitimately move `HEAD` by committing policy-owned generated surfaces, `bridge.md`, and ReviewSnapshot receipt artifacts before publication. `publication_authorization_decision` already accepte…
- **`7a5b14a5`** — Refresh external review snapshot for ce90a950
  - evolution: Fact: push preflight can legitimately move `HEAD` by committing policy-owned generated surfaces, `bridge.md`, and ReviewSnapshot receipt artifacts before publication. `publication_authorization_decision` already accepte…
- **`ce90a950`** — Refresh external review snapshot for ddf7bfe1
  - evolution: Fact: push preflight can legitimately move `HEAD` by committing policy-owned generated surfaces, `bridge.md`, and ReviewSnapshot receipt artifacts before publication. `publication_authorization_decision` already accepte…
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

- open governance findings: 126

### Startup advisories
- repair_reviewer_loop: runtime_missing

### Stale warnings
- Cut a checkpoint before doing anything else.

### Open gap rows
- **governance_open** (`dev/scripts/devctl/review_channel/projections`): bridge_content_loss_on_rollover: Rollover convergence re-projects bridge from typed current_session authority, overwriting reviewer-checkpoint content. System warning names it explicitly. Every rollover loses prior reviewer decision. Recover-from-event-store fix proposed rev_pkt_1715.
repo_path=/Users/jguida941/testing_upgrade/codex-voice
- **governance_open** (`dev/scripts/devctl/runtime/review_packet_inbox.py`): actor_template_missing: Live repro: first apply call failed with --actor required; retry with --actor claude succeeded. Matches codex Finding 3 independent confirmation. Template review_packet_inbox.py:27 omits --actor in generated command.
repo_path=/Users/jguida941/testing_upgrade/codex-voice
- **governance_open** (`dev/scripts/devctl`): x12_provider_name_pin_audit: X12 audit (16 production-code provider-name pins) posted to codex as rev_pkt_1782; operator-confirmed: identity binds to typed role, not provider name
repo_path=/Users/jguida941/testing_upgrade/codex-voice
- **governance_open** (`dev/scripts/devctl/commands/check/__init__.py`): dogfood.command.check: Auto-ingested devctl finalization failure rc=1.
repo_path=/Users/jguida941/testing_upgrade/codex-voice
- **governance_open** (`dev/scripts/devctl/commands/docs/check.py`): dogfood.command.docs-check: Auto-ingested devctl finalization failure rc=1.
repo_path=/Users/jguida941/testing_upgrade/codex-voice
- **governance_open** (`dev/scripts/devctl/commands/check/router.py`): dogfood.command.check-router: Auto-ingested devctl finalization failure rc=1.
repo_path=/Users/jguida941/testing_upgrade/codex-voice

---

Projection produced by `devctl review-snapshot`. Generation stamp `snap-415bb6c30d6d` binds this file to HEAD `5af77734d8ca`; if they drift, the freshness guard will fail CI. When the latest commit only refreshes this generated snapshot, the guard accepts this file as bound to that commit's parent code state.
