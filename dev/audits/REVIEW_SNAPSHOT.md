# VoiceTerm — Review Snapshot

> Deterministically generated from typed governance state. Do not edit by hand — rerun `devctl review-snapshot --write`.

## Quick status

- Branch: `feature/governance-quality-sweep`
- HEAD: `9f492c39f91a` — WIP snapshot: Slice A.5 lifecycle unification + connectivity progress
- Tree hash: `c66e57f31229`
- Generation stamp: `snap-0109b5135c0c`
- Generated at (UTC): 2026-04-29T21:28:24Z
- Push decision: `await_checkpoint` — staged_index_present
- Reviewer mode: `single_agent` (interaction: `remote_control`)
- Pipeline state: `n/a` (approval: `n/a`)
- Delta since last snapshot: 24 commits, 275 files, +22172/-3376
- Governance findings: 132 open / 88 fixed / 234 total
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
- HEAD SHA: `9f492c39f91af84d22a6e00278a5150bfbe480ba`
- HEAD author: Justin Guida
- HEAD timestamp (UTC): 2026-04-29T17:24:12-04:00

## 2. Governance state

### Push decision
- action: `await_checkpoint`
- reason: staged_index_present
- push_eligible_now: False
- worktree_clean: False
- staged_path_count: 1
- unstaged_path_count: 0
- next_step_command: `n/a`
- latest_push_report: `dev/reports/push/latest.json`
- latest_push_report_state: `blocked` (validation_failed)
- current_push_authorization: `push-auth-20260429T102330298808Z` (valid=False)
- authorized_head_commit: `afb62cdf40472770e80b1d6171946248a70a3fd6`
- approved_target_identity: `tree-receipt-20260429T102330298808Z:d6023541398e274909b40e012508e74e9e89153b`
- publication_backlog: urgent
- publication_guidance: 13 local commit(s) waiting for governed push once the current slice is checkpoint-clean.

### Reviewer runtime
- reviewer_mode: `single_agent`
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
- advisory: `checkpoint_before_continue` — dirty_after_local_checkpoint

## 3. Delta — what changed since the previous snapshot

Range: last 24 commits ending at `9f492c39f91a`

- commits: 24
- files changed: 275
- insertions: +22172
- deletions: -3376
- bundle classes touched: docs, tooling
- risk add-ons triggered: Parser / ANSI boundary, Dependency / security
- authority surfaces touched: 21 file(s)

### Commits

| # | SHA | Subject | Files | +/- | Bundle | Risk |
|---|---|---|---|---|---|---|
| 1 | `9f492c39` | WIP snapshot: Slice A.5 lifecycle unification + connectivit… | 140 | +8870/-1093 | tooling | Parser / ANSI boundary |
| 2 | `07ac1bd3` | Refresh external review snapshot for 6902e3c8 | 1 | +52/-52 | tooling |  |
| 3 | `6902e3c8` | Refresh external review snapshot for ee2ee1b1 | 2 | +50/-54 | docs |  |
| 4 | `ee2ee1b1` | Refresh external review snapshot for afb62cdf | 1 | +48/-42 | tooling |  |
| 5 | `afb62cdf` | Refresh external review snapshot for c2fcb696 | 2 | +61/-63 | docs |  |
| 6 | `c2fcb696` | Enforce typed authority provenance probe | 2 | +52/-52 | tooling |  |
| 7 | `b6cb7332` | Refresh external review snapshot for 3a874752 | 2 | +50/-51 | docs |  |
| 8 | `3a874752` | Refresh external review snapshot for cd57207f | 1 | +46/-46 | tooling |  |
| 9 | `cd57207f` | Refresh external review snapshot for ee7635ed | 2 | +52/-51 | docs |  |
| 10 | `ee7635ed` | Refresh external review snapshot for 0da0bfe1 | 1 | +58/-55 | tooling |  |
| 11 | `0da0bfe1` | Refresh policy-owned generated surfaces for eff73aad | 1 | +1/-1 | docs |  |
| 12 | `eff73aad` | Refresh external review snapshot for 8d31f774 | 2 | +106/-90 | docs |  |
| 13 | `8d31f774` | Implement typed governance continuation | 146 | +9271/-770 | tooling | Parser / ANSI boundary, Dependency / security |
| 14 | `0233390f` | Refresh external review snapshot for 39083dc8 | 2 | +48/-48 | docs |  |
| 15 | `39083dc8` | Refresh external review snapshot for 5af77734 | 1 | +50/-47 | tooling |  |
| 16 | `5af77734` | Refresh external review snapshot for f259c8eb | 2 | +69/-70 | docs |  |
| 17 | `f259c8eb` | Plan 4.1 / MP-377 Codex 42 slice — Layer H push-identity du… | 11 | +227/-81 | tooling |  |
| 18 | `00eb5fd7` | Refresh external review snapshot for cce19014 | 2 | +48/-48 | docs |  |
| 19 | `cce19014` | Refresh external review snapshot for 06f6d2b2 | 1 | +50/-47 | tooling |  |
| 20 | `06f6d2b2` | Refresh external review snapshot for 5adc6ebd | 2 | +91/-70 | docs |  |
| 21 | `5adc6ebd` | Plan 4.1 / MP-377 Codex 41 slice — events.py NameError fix… | 56 | +2716/-386 | tooling |  |
| 22 | `acf4ae3d` | Refresh external review snapshot for f971174a | 2 | +61/-67 | docs |  |
| 23 | `f971174a` | Refresh external review snapshot for b5e92596 | 2 | +48/-48 | docs |  |
| 24 | `b5e92596` | Refresh external review snapshot for f06b2658 | 1 | +47/-44 | tooling |  |

### Files

| Path | Bundle | +/- |
|---|---|---|
| `.github/workflows/README.md` | tooling | +1/-0 |
| `.github/workflows/adopter_portability.yml` | tooling | +74/-0 |
| `AGENTS.md` | docs | +34/-12 |
| `app/operator_console/state/core/models.py` | tooling | +1/-0 |
| `app/operator_console/state/snapshots/dashboard_snapshot.py` | tooling | +28/-0 |
| `app/operator_console/state/snapshots/snapshot_builder.py` | tooling | +3/-1 |
| `bridge.md` | docs | +95/-94 |
| `dev/active/MASTER_PLAN.md` | tooling | +90/-9 |
| `dev/active/ai_governance_platform.md` | tooling | +138/-3 |
| `dev/audits/REVIEW_SNAPSHOT.md` | tooling | +1309/-1265 |
| `dev/config/publication_sync_registry.json` | tooling | +1/-27 |
| `dev/config/quality_presets/portable_python.json` | tooling | +2/-0 |
| `dev/guides/DEVELOPMENT.md` | docs | +63/-20 |
| `dev/guides/PORTABLE_GOVERNANCE_SETUP.md` | docs | +39/-0 |
| `dev/guides/SYSTEM_MAP.md` | docs | +16/-16 |
| `dev/history/ENGINEERING_EVOLUTION.md` | tooling | +327/-6 |
| `dev/scripts/README.md` | tooling | +104/-29 |
| `dev/scripts/checks/README.md` | tooling | +6/-0 |
| `dev/scripts/checks/architecture_probes/README.md` | tooling | +10/-0 |
| `dev/scripts/checks/architecture_probes/probe_architecture_connectivity.py` | tooling | +161/-0 |
| `dev/scripts/checks/architecture_probes/probe_typed_authority_provenance.py` | tooling | +201/-0 |
| `dev/scripts/checks/contract_connectivity/inventory_helpers.py` | tooling | +2/-0 |
| `dev/scripts/checks/probe_architecture_connectivity.py` | tooling | +12/-0 |
| `dev/scripts/checks/probe_typed_authority_provenance.py` | tooling | +12/-0 |
| `dev/scripts/checks/review_channel_bridge/report.py` | tooling | +53/-96 |
| `dev/scripts/checks/review_channel_bridge/typed_state.py` | tooling | +150/-0 |
| `dev/scripts/devctl/cli_parser/builders_checks.py` | tooling | +12/-1 |
| `dev/scripts/devctl/cli_parser/claude_loop.py` | tooling | +45/-1 |
| `dev/scripts/devctl/cli_parser/controller_action.py` | tooling | +15/-1 |
| `dev/scripts/devctl/cli_parser/entrypoint.py` | tooling | +23/-4 |
| `dev/scripts/devctl/commands/check/__init__.py` | tooling | +11/-1 |
| `dev/scripts/devctl/commands/controller_action.py` | tooling | +24/-6 |
| `dev/scripts/devctl/commands/dashboard.py` | tooling | +53/-44 |
| `dev/scripts/devctl/commands/dashboard_data.py` | tooling | +6/-2 |
| `dev/scripts/devctl/commands/dashboard_render/__init__.py` | tooling | +26/-3 |
| `dev/scripts/devctl/commands/dashboard_render/attention.py` | tooling | +55/-0 |
| `dev/scripts/devctl/commands/dashboard_render/typed_state.py` | tooling | +98/-0 |
| `dev/scripts/devctl/commands/dashboard_typed_state.py` | tooling | +128/-0 |
| `dev/scripts/devctl/commands/governance/bootstrap.py` | tooling | +24/-1 |
| `dev/scripts/devctl/commands/governance/session_resume.py` | tooling | +124/-10 |
| _235 more files trimmed_ | | |

## 4. Quality signals

### Governance review
- total findings: 234
- open: 132
- fixed: 88
- false positives: 0

Recent findings:
- `dogfood.command.docs-check` — `dev/scripts/devctl/commands/docs/check.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.check-router` — `dev/scripts/devctl/commands/check/router.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.push` — `dev/scripts/devctl/commands/vcs/push.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.commit` — `dev/scripts/devctl/commands/vcs/commit.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.security` — `dev/scripts/devctl/commands/security.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.probe-report` — `dev/scripts/devctl/commands/probe_report.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.tandem-validate` — `dev/scripts/devctl/commands/governance/simple_lanes.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.process-audit` — `dev/scripts/devctl/commands/process/audit.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.hygiene` — `dev/scripts/devctl/commands/governance/hygiene.py` (n/a, verdict=`confirmed_issue`)
- `dogfood.command.launcher-check` — `dev/scripts/devctl/commands/governance/simple_lanes.py` (n/a, verdict=`confirmed_issue`)

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

- **risk**: Parser / ANSI boundary — Delta touches a risk-sensitive surface; verify the routed bundle
- **risk**: Dependency / security — Delta touches a risk-sensitive surface; verify the routed bundle
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/review_channel/reviewer_runtime_snapshot.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_actions.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_commit_phase.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_packets.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_support.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/review_channel/reviewer_runtime_contract.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/reviewer_runtime_models.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/reviewer_runtime_parser.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/reviewer_runtime_parser_state_rows.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/startup_context.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/review_channel/test_reviewer_runtime_contract.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/review_channel/test_reviewer_runtime_doctor.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/vcs/test_governed_executor.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/review_channel/bridge_projection_metadata.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/review_channel/bridge_projection_state.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/project_governance.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/project_governance_contract.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/project_governance_parse.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/runtime/test_remote_commit_pipeline_phases34.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_commit_runtime.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/review_channel/bridge_validation.py`) — Review contract-level invariants for this file
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/platform/coordination_snapshot_models.py`) — Commit 9f492c39 changed dev/scripts/devctl/platform/coordination_snapshot_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/platform/surface_state_contract_rows.py`) — Commit 9f492c39 changed dev/scripts/devctl/platform/surface_state_contract_rows.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/review_channel/event_models.py`) — Commit 9f492c39 changed dev/scripts/devctl/review_channel/event_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/review_channel/reviewer_runtime_contract.py`) — Commit 9f492c39 changed dev/scripts/devctl/review_channel/reviewer_runtime_contract.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/review_state_collaboration_models.py`) — Commit 9f492c39 changed dev/scripts/devctl/runtime/review_state_collaboration_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/review_state_models.py`) — Commit 9f492c39 changed dev/scripts/devctl/runtime/review_state_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/review_state_packet_models.py`) — Commit 9f492c39 changed dev/scripts/devctl/runtime/review_state_packet_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/reviewer_runtime_models.py`) — Commit 9f492c39 changed dev/scripts/devctl/runtime/reviewer_runtime_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/startup_context_models.py`) — Commit 9f492c39 changed dev/scripts/devctl/runtime/startup_context_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/work_intake_models.py`) — Commit 9f492c39 changed dev/scripts/devctl/runtime/work_intake_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/tests/platform/test_platform_contracts.py`) — Commit 9f492c39 changed dev/scripts/devctl/tests/platform/test_platform_contracts.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/tests/review_channel/test_reviewer_runtime_contract.py`) — Commit 9f492c39 changed dev/scripts/devctl/tests/review_channel/test_reviewer_runtime_contract.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/review_channel/packet_contract.py`) — Commit 8d31f774 changed dev/scripts/devctl/review_channel/packet_contract.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/agent_session_continuation_models.py`) — Commit 8d31f774 changed dev/scripts/devctl/runtime/agent_session_continuation_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/master_plan_contract.py`) — Commit 8d31f774 changed dev/scripts/devctl/runtime/master_plan_contract.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/project_governance_contract.py`) — Commit 8d31f774 changed dev/scripts/devctl/runtime/project_governance_contract.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/review_channel/prompt_contract.py`) — Commit 5adc6ebd changed dev/scripts/devctl/review_channel/prompt_contract.py

### Suggested verification commands

- `python3 dev/scripts/devctl.py check --profile ci`
- `python3 dev/scripts/devctl.py probe-report --format md`
- `python3 dev/scripts/devctl.py docs-check --strict-tooling`
- `python3 dev/scripts/devctl.py governance-review --format md`
- `python3 dev/scripts/devctl.py check-router --format md`

## 7. Reasoning — why these changes landed

### Per-commit rationale

- **`9f492c39`** — WIP snapshot: Slice A.5 lifecycle unification + connectivity progress
  - Save in-flight work-in-progress before continuing GuardIR plan 4.1+ V2.1
  - Slice A.5 / runtime-agreement / connectivity sweep. Includes:
  - evolution: Fact: live Plan 4.1 dogfood still had a packet-loss shaped failure mode: expired pending packets could fall out of the actionable inbox without a per-packet audit trail proving whether an actor acknowledged, acted on, i…
- **`07ac1bd3`** — Refresh external review snapshot for 6902e3c8
  - evolution: Fact: live Plan 4.1 dogfood still had a packet-loss shaped failure mode: expired pending packets could fall out of the actionable inbox without a per-packet audit trail proving whether an actor acknowledged, acted on, i…
- **`6902e3c8`** — Refresh external review snapshot for ee2ee1b1
  - evolution: Fact: live Plan 4.1 dogfood still had a packet-loss shaped failure mode: expired pending packets could fall out of the actionable inbox without a per-packet audit trail proving whether an actor acknowledged, acted on, i…
- **`ee2ee1b1`** — Refresh external review snapshot for afb62cdf
  - evolution: Fact: live Plan 4.1 dogfood still had a packet-loss shaped failure mode: expired pending packets could fall out of the actionable inbox without a per-packet audit trail proving whether an actor acknowledged, acted on, i…
- **`afb62cdf`** — Refresh external review snapshot for c2fcb696
  - evolution: Fact: live Plan 4.1 dogfood still had a packet-loss shaped failure mode: expired pending packets could fall out of the actionable inbox without a per-packet audit trail proving whether an actor acknowledged, acted on, i…
- **`c2fcb696`** — Enforce typed authority provenance probe
  - evolution: Fact: live Plan 4.1 dogfood still had a packet-loss shaped failure mode: expired pending packets could fall out of the actionable inbox without a per-packet audit trail proving whether an actor acknowledged, acted on, i…
- **`b6cb7332`** — Refresh external review snapshot for 3a874752
  - evolution: Fact: live Plan 4.1 dogfood still had a packet-loss shaped failure mode: expired pending packets could fall out of the actionable inbox without a per-packet audit trail proving whether an actor acknowledged, acted on, i…
- **`3a874752`** — Refresh external review snapshot for cd57207f
  - evolution: Fact: live Plan 4.1 dogfood still had a packet-loss shaped failure mode: expired pending packets could fall out of the actionable inbox without a per-packet audit trail proving whether an actor acknowledged, acted on, i…
- **`cd57207f`** — Refresh external review snapshot for ee7635ed
  - evolution: Fact: live Plan 4.1 dogfood still had a packet-loss shaped failure mode: expired pending packets could fall out of the actionable inbox without a per-packet audit trail proving whether an actor acknowledged, acted on, i…
- **`ee7635ed`** — Refresh external review snapshot for 0da0bfe1
  - evolution: Fact: live Plan 4.1 dogfood still had a packet-loss shaped failure mode: expired pending packets could fall out of the actionable inbox without a per-packet audit trail proving whether an actor acknowledged, acted on, i…
- **`0da0bfe1`** — Refresh policy-owned generated surfaces for eff73aad
  - evolution: Fact: live Plan 4.1 dogfood still had a packet-loss shaped failure mode: expired pending packets could fall out of the actionable inbox without a per-packet audit trail proving whether an actor acknowledged, acted on, i…
- **`eff73aad`** — Refresh external review snapshot for 8d31f774
  - evolution: Fact: live Plan 4.1 dogfood still had a packet-loss shaped failure mode: expired pending packets could fall out of the actionable inbox without a per-packet audit trail proving whether an actor acknowledged, acted on, i…
- **`8d31f774`** — Implement typed governance continuation
  - evolution: Fact: live Plan 4.1 dogfood still had a packet-loss shaped failure mode: expired pending packets could fall out of the actionable inbox without a per-packet audit trail proving whether an actor acknowledged, acted on, i…
- **`0233390f`** — Refresh external review snapshot for 39083dc8
  - evolution: Fact: live Codex/Claude dogfood found several small but compounding surface lies: bridge/status reviewer mode could disagree, packet counters counted different queues, Action Requests risked reading receipt-like rows, c…
- **`39083dc8`** — Refresh external review snapshot for 5af77734
  - evolution: Fact: live Codex/Claude dogfood found several small but compounding surface lies: bridge/status reviewer mode could disagree, packet counters counted different queues, Action Requests risked reading receipt-like rows, c…
- **`5af77734`** — Refresh external review snapshot for f259c8eb
  - evolution: Fact: live Codex/Claude dogfood found several small but compounding surface lies: bridge/status reviewer mode could disagree, packet counters counted different queues, Action Requests risked reading receipt-like rows, c…
- **`f259c8eb` | MPs: MP-377** — Plan 4.1 / MP-377 Codex 42 slice — Layer H push-identity duplicate-elimination via reuse of publication_authorization_decision chain-membership authority
  - Closes the 5th gate from this evening's prose-vs-typed-state pattern: governed push identity validation now consumes the same managed receipt-chain authority already proven by `publication_authorization_decision`, so receipt commits above an approved content commit do not trigger a duplicate `ApprovedTargetIdentityViolation`. Preserves fail-closed against fixture/stale/non-managed HEAD drift per memory rule feedback_branch_identity_invariant_required.md (Codex 18 escalation invariants).
  - plan: `dev/active/ai_governance_platform.md`
  - evolution: Fact: live Codex/Claude dogfood found several small but compounding surface lies: bridge/status reviewer mode could disagree, packet counters counted different queues, Action Requests risked reading receipt-like rows, c…
- **`00eb5fd7`** — Refresh external review snapshot for cce19014
  - evolution: Fact: live Codex/Claude dogfood found several small but compounding surface lies: bridge/status reviewer mode could disagree, packet counters counted different queues, Action Requests risked reading receipt-like rows, c…
- **`cce19014`** — Refresh external review snapshot for 06f6d2b2
  - evolution: Fact: live Codex/Claude dogfood found several small but compounding surface lies: bridge/status reviewer mode could disagree, packet counters counted different queues, Action Requests risked reading receipt-like rows, c…
- **`06f6d2b2`** — Refresh external review snapshot for 5adc6ebd
  - evolution: Fact: live Codex/Claude dogfood found several small but compounding surface lies: bridge/status reviewer mode could disagree, packet counters counted different queues, Action Requests risked reading receipt-like rows, c…
- **`5adc6ebd` | MPs: MP-377** — Plan 4.1 / MP-377 Codex 41 slice — events.py NameError fix + Layer F handoff packet auto-emit (α + β) + Layer G typed liveness producer
  - This slice closes the typed-handoff-before-task-complete meta-pattern that all prior Codex sessions (33/35/37/39/40) skipped:
  -   - Layer F-α (in-Codex): bootstrap promotes typed stage_commit_pipeline action_request emission to PRIMARY contract; Codex 41 itself proved this works by posting rev_pkt_2116 from=codex to=claude as the LAST tool action before TASK_COMPLETE, target_ref=devctl_commit:acf4ae3d, full_guard_bundle_evidence=--profile ci.
  -   - Layer F-β (launcher backup): launch_script_watchdog session-end guard now auto-emits stage_commit_pipeline if Codex's task_complete event lacks a matching packet — fail-closed against partial-exit deadlocks.
  - plan: `dev/active/ai_governance_platform.md`
  - evolution: Fact: live Codex/Claude dogfood found several small but compounding surface lies: bridge/status reviewer mode could disagree, packet counters counted different queues, Action Requests risked reading receipt-like rows, c…
- **`acf4ae3d`** — Refresh external review snapshot for f971174a
  - evolution: Fact: live Codex/Claude dogfood found several small but compounding surface lies: bridge/status reviewer mode could disagree, packet counters counted different queues, Action Requests risked reading receipt-like rows, c…
- **`f971174a`** — Refresh external review snapshot for b5e92596
  - evolution: Fact: live Codex/Claude dogfood found several small but compounding surface lies: bridge/status reviewer mode could disagree, packet counters counted different queues, Action Requests risked reading receipt-like rows, c…
- **`b5e92596`** — Refresh external review snapshot for f06b2658
  - evolution: Fact: live Codex/Claude dogfood found several small but compounding surface lies: bridge/status reviewer mode could disagree, packet counters counted different queues, Action Requests risked reading receipt-like rows, c…
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

- open governance findings: 132

### Startup advisories
- checkpoint_before_continue: dirty_after_local_checkpoint

### Stale warnings
- Relaunch the reviewer loop immediately.

### Open gap rows
- **governance_open** (`dev/scripts/devctl/commands/docs/check.py`): dogfood.command.docs-check: Auto-ingested devctl finalization failure rc=1.
repo_path=/Users/jguida941/testing_upgrade/codex-voice
- **governance_open** (`dev/scripts/devctl/commands/check/router.py`): dogfood.command.check-router: Auto-ingested devctl finalization failure rc=1.
repo_path=/Users/jguida941/testing_upgrade/codex-voice
- **governance_open** (`dev/scripts/devctl/commands/vcs/push.py`): dogfood.command.push: Auto-ingested devctl finalization failure rc=1.
repo_path=/Users/jguida941/testing_upgrade/codex-voice
- **governance_open** (`dev/scripts/devctl/commands/vcs/commit.py`): dogfood.command.commit: Auto-ingested devctl finalization failure rc=1.
repo_path=/Users/jguida941/testing_upgrade/codex-voice
- **governance_open** (`dev/scripts/devctl/commands/security.py`): dogfood.command.security: Auto-ingested devctl finalization failure rc=1.
repo_path=/Users/jguida941/testing_upgrade/codex-voice
- **governance_open** (`dev/scripts/devctl/commands/probe_report.py`): dogfood.command.probe-report: Auto-ingested devctl finalization failure rc=1.
repo_path=/Users/jguida941/testing_upgrade/codex-voice
- **governance_open** (`dev/scripts/devctl/commands/governance/simple_lanes.py`): dogfood.command.tandem-validate: Auto-ingested devctl finalization failure rc=1.
repo_path=/Users/jguida941/testing_upgrade/codex-voice
- **governance_open** (`dev/scripts/devctl/commands/process/audit.py`): dogfood.command.process-audit: Auto-ingested devctl finalization failure rc=1.
repo_path=/Users/jguida941/testing_upgrade/codex-voice

---

Projection produced by `devctl review-snapshot`. Generation stamp `snap-0109b5135c0c` binds this file to HEAD `9f492c39f91a`; if they drift, the freshness guard will fail CI. When the latest commit only refreshes this generated snapshot, the guard accepts this file as bound to that commit's parent code state.
