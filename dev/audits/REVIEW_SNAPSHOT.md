# VoiceTerm — Review Snapshot

> Deterministically generated from typed governance state. Do not edit by hand — rerun `devctl review-snapshot --write`.

## Quick status

- Branch: `feature/governance-quality-sweep`
- HEAD: `95140873c9e6` — fix(bundles): dual import support for registry.py — works as package + standalone
- Tree hash: `c551bf55b18e`
- Generation stamp: `snap-666da2eb428c`
- Generated at (UTC): 2026-04-11T01:36:34Z
- Push decision: `run_devctl_push` — push_preconditions_satisfied
- Reviewer mode: `single_agent` (interaction: `remote_control`)
- Pipeline state: `n/a` (approval: `n/a`)
- Delta since last snapshot: 24 commits, 84 files, +8359/-2060
- Governance findings: 86 open / 70 fixed / 170 total
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
- HEAD SHA: `95140873c9e618de3f6927dfff79eb86acc8ba88`
- HEAD author: Justin Guida
- HEAD timestamp (UTC): 2026-04-10T21:35:45-04:00

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
- latest_push_report_state: `blocked` (validation_failed)
- publication_backlog: recommended
- publication_guidance: 3 local commit(s) waiting for governed push. Run `python3 dev/scripts/devctl.py push --execute` now.

### Reviewer runtime
- reviewer_mode: `single_agent`
- reviewer_freshness: unknown
- reviewer_publish_clear: True
- interaction_mode: `remote_control`

### Remote commit pipeline
- state: `n/a`
- approval_state: `n/a`

### Work intake
- active plan: **Master Plan (Active, Unified)**
- plan path: `dev/active/MASTER_PLAN.md`
- active MP scope: all active MP execution state
- advisory: `push_allowed` — worktree_clean_and_review_accepted

## 3. Delta — what changed since the previous snapshot

Range: last 24 commits ending at `95140873c9e6`

- commits: 24
- files changed: 84
- insertions: +8359
- deletions: -2060
- bundle classes touched: tooling, docs
- risk add-ons triggered: Parser / ANSI boundary
- authority surfaces touched: 4 file(s)

### Commits

| # | SHA | Subject | Files | +/- | Bundle | Risk |
|---|---|---|---|---|---|---|
| 1 | `95140873` | fix(bundles): dual import support for registry.py — works a… | 2 | +68/-51 | tooling |  |
| 2 | `6b51ebe9` | Refresh external review snapshot for 3f1d9950 | 1 | +71/-73 | tooling |  |
| 3 | `3f1d9950` | feat(governance): Q57 + Q58 — devctl monitor + registry-as-… | 27 | +1575/-137 | tooling |  |
| 4 | `ae265ed6` | Refresh external review snapshot for f240bfe3 | 1 | +53/-59 | tooling |  |
| 5 | `f240bfe3` | docs: register findings-priority in AGENTS.md tooling inven… | 2 | +42/-38 | docs |  |
| 6 | `eac80fb7` | chore: refresh REVIEW_SNAPSHOT after Round 8 | 1 | +61/-65 | tooling |  |
| 7 | `ab7569ab` | Refresh external review snapshot for 7eca4d0c | 1 | +70/-68 | tooling |  |
| 8 | `7eca4d0c` | feat(governance): Q52 + Q55 — commit gate hook + findings p… | 21 | +1529/-486 | tooling | Parser / ANSI boundary |
| 9 | `4cee9ac1` | Refresh external review snapshot for 1840993a | 1 | +45/-42 | tooling |  |
| 10 | `1840993a` | chore: sync bridge.md after Codex Q67 session | 2 | +77/-82 | docs |  |
| 11 | `51da1e71` | fix(governance): Q67 — strengthen contract connectivity gua… | 15 | +679/-190 | tooling |  |
| 12 | `b42dd589` | feat(governance): Q65 — contract connectivity guard + actio… | 24 | +1649/-89 | tooling |  |
| 13 | `5d02040f` | feat(governance): Q54+Q64 — observer signal type, session p… | 22 | +962/-85 | tooling |  |
| 14 | `2813a913` | Refresh external review snapshot for 10242d1a | 1 | +76/-71 | tooling |  |
| 15 | `10242d1a` | feat(governance): Q40+Q42+Q51 — lane edit gate, typed recov… | 21 | +697/-67 | tooling |  |
| 16 | `368c3b8d` | docs(audit): Q61 — findings stay flat in LIVE_RUN, not rout… | 2 | +65/-44 | tooling |  |
| 17 | `51e01936` | docs(audit): Q60 — guards run after coding, not during | 2 | +102/-64 | tooling |  |
| 18 | `53e06b4b` | docs(audit): Q57-Q59 — monitor pass, registry dispatcher, h… | 2 | +109/-49 | tooling |  |
| 19 | `862ebd16` | docs(audit): Q56 — Q54+Q55 compose from existing systems, m… | 2 | +77/-44 | tooling |  |
| 20 | `d285d33f` | docs(audit): Q55 — no priority/planning pass over accumulat… | 2 | +83/-62 | tooling |  |
| 21 | `306116c6` | docs(audit): Q54 — observer layer ungoverned, no self-audit… | 2 | +81/-42 | tooling |  |
| 22 | `5e9022a7` | docs(audit): Q53 — dashboard 77% success is command ok=True… | 2 | +73/-48 | tooling |  |
| 23 | `151b28d9` | Refresh external review snapshot for 1e193595 | 1 | +59/-56 | tooling |  |
| 24 | `1e193595` | docs(audit): Q52 update — cross-tool hook enforcement must… | 2 | +56/-48 | tooling |  |

### Files

| Path | Bundle | +/- |
|---|---|---|
| `.github/workflows/release_preflight.yml` | tooling | +1/-0 |
| `.github/workflows/tooling_control_plane.yml` | tooling | +3/-0 |
| `AGENTS.md` | docs | +20/-5 |
| `bridge.md` | docs | +3/-3 |
| `dev/active/MASTER_PLAN.md` | tooling | +18/-0 |
| `dev/active/ai_governance_platform.md` | tooling | +14/-0 |
| `dev/active/platform_authority_loop.md` | tooling | +101/-7 |
| `dev/active/remote_control_runtime.md` | tooling | +18/-1 |
| `dev/audits/LIVE_RUN.md` | tooling | +471/-1 |
| `dev/audits/REVIEW_SNAPSHOT.md` | tooling | +1363/-1339 |
| `dev/config/git_hooks/pre-commit-review-snapshot.sh` | tooling | +41/-18 |
| `dev/config/templates/portable_governance_finding_review.schema.json` | tooling | +3/-2 |
| `dev/config/templates/portable_governance_pre_commit_hook.sh` | tooling | +13/-1 |
| `dev/guides/DEVELOPMENT.md` | docs | +33/-17 |
| `dev/history/ENGINEERING_EVOLUTION.md` | tooling | +80/-3 |
| `dev/scripts/README.md` | tooling | +27/-10 |
| `dev/scripts/checks/check_contract_connectivity.py` | tooling | +12/-0 |
| `dev/scripts/checks/contract_connectivity/__init__.py` | tooling | +1/-0 |
| `dev/scripts/checks/contract_connectivity/command.py` | tooling | +61/-0 |
| `dev/scripts/checks/contract_connectivity/findings.py` | tooling | +282/-9 |
| `dev/scripts/checks/contract_connectivity/inventory.py` | tooling | +374/-107 |
| `dev/scripts/checks/contract_connectivity/inventory_helpers.py` | tooling | +310/-0 |
| `dev/scripts/checks/contract_connectivity/models.py` | tooling | +128/-1 |
| `dev/scripts/checks/contract_connectivity/report.py` | tooling | +104/-2 |
| `dev/scripts/checks/contract_connectivity/support.py` | tooling | +102/-0 |
| `dev/scripts/devctl/autonomy/run_helpers.py` | tooling | +3/-2 |
| `dev/scripts/devctl/bundles/registry.py` | tooling | +112/-80 |
| `dev/scripts/devctl/cli.py` | tooling | +7/-388 |
| `dev/scripts/devctl/cli_parser/entrypoint.py` | tooling | +407/-0 |
| `dev/scripts/devctl/commands/dashboard_render/__init__.py` | tooling | +4/-1 |
| `dev/scripts/devctl/commands/dashboard_render/mobile.py` | tooling | +51/-0 |
| `dev/scripts/devctl/commands/governance/install_git_hooks.py` | tooling | +11/-8 |
| `dev/scripts/devctl/commands/governance/review.py` | tooling | +1/-0 |
| `dev/scripts/devctl/commands/governance/simple_lanes_support.py` | tooling | +3/-2 |
| `dev/scripts/devctl/commands/governance/startup_context.py` | tooling | +27/-0 |
| `dev/scripts/devctl/commands/governance/startup_context_recovery.py` | tooling | +38/-0 |
| `dev/scripts/devctl/commands/governance/startup_context_render.py` | tooling | +11/-0 |
| `dev/scripts/devctl/commands/listing.py` | tooling | +2/-0 |
| `dev/scripts/devctl/commands/monitor.py` | tooling | +13/-0 |
| `dev/scripts/devctl/commands/reporting/findings_priority.py` | tooling | +58/-0 |
| _44 more files trimmed_ | | |

## 4. Quality signals

### Governance review
- total findings: 170
- open: 86
- fixed: 70
- false positives: 0

Recent findings:
- `subprocess_missing_timeout` — `dev/scripts/devctl/security/python_scope.py` (n/a, verdict=`confirmed_issue`)
- `subprocess_missing_timeout` — `dev/scripts/devctl/security/codeql.py` (n/a, verdict=`confirmed_issue`)
- `subprocess_missing_timeout` — `dev/scripts/devctl/integrations/import_core.py` (n/a, verdict=`confirmed_issue`)
- `subprocess_missing_timeout` — `app/operator_console/launch_support.py` (n/a, verdict=`confirmed_issue`)
- `threading_shared_state_no_lock` — `dev/scripts/devctl/common.py` (n/a, verdict=`confirmed_issue`)
- `none_safety_chained_get_crash` — `dev/scripts/devctl/review_channel/bridge_projection_state.py` (n/a, verdict=`confirmed_issue`)
- `none_safety_chained_get_crash` — `app/operator_console/state/review/operator_decisions.py` (n/a, verdict=`confirmed_issue`)
- `none_safety_chained_get_crash` — `dev/scripts/devctl/autonomy/run_render.py` (n/a, verdict=`confirmed_issue`)
- `none_safety_chained_get_crash` — `dev/scripts/devctl/autonomy/report_helpers.py` (n/a, verdict=`confirmed_issue`)
- `none_safety_chained_get_crash` — `dev/scripts/devctl/quality_backlog/priorities.py` (n/a, verdict=`confirmed_issue`)

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
| `ActionResult` | `governance_runtime` | `n/a` | status |
| `ArtifactStore` | `governance_runtime` | `n/a` | root |
| `AutoModeState` | `governance_runtime` | `n/a` | phase |
| `CallerAuthorityPolicy` | `governance_runtime` | `n/a` | caller_id |
| `CheckResult` | `governance_runtime` | `n/a` | success |
| `ControlPlaneReadModel` | `governance_runtime` | `n/a` | push_eligible |
| `ControlState` | `governance_runtime` | `n/a` | approvals |
| `CoordinationSnapshot` | `governance_core` | `n/a` | current_slice |
| `DecisionPacket` | `governance_runtime` | `n/a` | decision_mode |
| `FailurePacket` | `governance_runtime` | `n/a` | runner |
| `Finding` | `governance_runtime` | `n/a` | check_id |
| `LocalServiceEndpoint` | `governance_runtime` | `n/a` | service_id |
| `ProviderAdapter` | `governance_adapters` | `n/a` | provider_id |
| `PushAuthorizationRecord` | `governance_runtime` | `n/a` | authorization_id |
| `RemoteCommitPipelineContract` | `governance_runtime` | `dev.scripts.devctl.runtime.remote_commit_pipeline_models:RemoteCommitPipelineContract` | snapshot_id |
| `RepoPack` | `repo_packs` | `n/a` | pack_id |
| `ReviewCandidateRecord` | `governance_runtime` | `n/a` | candidate_id |
| `ReviewState` | `governance_runtime` | `dev.scripts.devctl.runtime.review_state_models:ReviewState` | snapshot_id |
| `ReviewerRuntimeContract` | `governance_runtime` | `n/a` | reviewer_mode |
| `RunRecord` | `governance_runtime` | `n/a` | run_id |
| `SessionCachePacket` | `governance_commands` | `n/a` | last_reviewed_sha |
| `TypedAction` | `governance_runtime` | `n/a` | action_id |
| `WorkflowAdapter` | `governance_adapters` | `n/a` | adapter_id |

### Key documents

- `AGENTS.md`
- `dev/active/MASTER_PLAN.md`
- `dev/active/INDEX.md`
- `dev/guides/AI_GOVERNANCE_PLATFORM.md`

## 6. Reviewer hints — please verify

### Targeted hints

- **risk**: Parser / ANSI boundary — Delta touches a risk-sensitive surface; verify the routed bundle
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/review_channel/test_reviewer_runtime_doctor.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/governance/startup_context.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/runtime/test_startup_context.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/startup_context.py`) — Review contract-level invariants for this file
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/monitor_snapshot_contracts.py`) — Commit 3f1d9950 changed dev/scripts/devctl/runtime/monitor_snapshot_contracts.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/triage/findings_priority_models.py`) — Commit 7eca4d0c changed dev/scripts/devctl/triage/findings_priority_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/work_intake_models.py`) — Commit b42dd589 changed dev/scripts/devctl/runtime/work_intake_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/governance_review_models.py`) — Commit 5d02040f changed dev/scripts/devctl/governance_review_models.py

### Suggested verification commands

- `python3 dev/scripts/devctl.py check --profile ci`
- `python3 dev/scripts/devctl.py probe-report --format md`
- `python3 dev/scripts/devctl.py docs-check --strict-tooling`
- `python3 dev/scripts/devctl.py governance-review --format md`
- `python3 dev/scripts/devctl.py check-router --format md`

## 7. Reasoning — why these changes landed

### Per-commit rationale

- **`95140873`** — fix(bundles): dual import support for registry.py — works as package + standalone
  - Q58 registry-dispatcher refactor added a relative import that broke
  - check_bundle_registry_dry.py which loads the file via spec_from_file_location.
  - Fall back to absolute import with repo-root sys.path adjustment when the
  - evolution: Fact: the Q40/Q42 live-run findings showed two separate authority leaks. A dashboard/observer lane could still slide into implementation edits while another agent owned the active lane, and recovery code could escalate …
- **`6b51ebe9`** — Refresh external review snapshot for 3f1d9950
  - evolution: Fact: the Q40/Q42 live-run findings showed two separate authority leaks. A dashboard/observer lane could still slide into implementation edits while another agent owned the active lane, and recovery code could escalate …
- **`3f1d9950`** — feat(governance): Q57 + Q58 — devctl monitor + registry-as-sovereign-dispatcher
  - Codex Round 9 implementation:
  - - Q57: devctl monitor command for remote phone mode with typed
  -   MonitorSnapshot, --follow --interval NDJSON streaming, and
  - evolution: Fact: the Q40/Q42 live-run findings showed two separate authority leaks. A dashboard/observer lane could still slide into implementation edits while another agent owned the active lane, and recovery code could escalate …
- **`ae265ed6`** — Refresh external review snapshot for f240bfe3
  - evolution: Fact: the Q40/Q42 live-run findings showed two separate authority leaks. A dashboard/observer lane could still slide into implementation edits while another agent owned the active lane, and recovery code could escalate …
- **`f240bfe3`** — docs: register findings-priority in AGENTS.md tooling inventory
  - evolution: Fact: the Q40/Q42 live-run findings showed two separate authority leaks. A dashboard/observer lane could still slide into implementation edits while another agent owned the active lane, and recovery code could escalate …
- **`eac80fb7`** — chore: refresh REVIEW_SNAPSHOT after Round 8
  - evolution: Fact: the Q40/Q42 live-run findings showed two separate authority leaks. A dashboard/observer lane could still slide into implementation edits while another agent owned the active lane, and recovery code could escalate …
- **`ab7569ab`** — Refresh external review snapshot for 7eca4d0c
  - evolution: Fact: the Q40/Q42 live-run findings showed two separate authority leaks. A dashboard/observer lane could still slide into implementation edits while another agent owned the active lane, and recovery code could escalate …
- **`7eca4d0c`** — feat(governance): Q52 + Q55 — commit gate hook + findings priority engine
  - Codex Round 8 implementation:
  - - Q52: pre-commit hook wires raw git commit through commit_permission
  -   gate via pre-commit-review-snapshot.sh + commit_permission_hook.py.
  - evolution: Fact: the Q40/Q42 live-run findings showed two separate authority leaks. A dashboard/observer lane could still slide into implementation edits while another agent owned the active lane, and recovery code could escalate …
- **`4cee9ac1`** — Refresh external review snapshot for 1840993a
  - evolution: Fact: the Q40/Q42 live-run findings showed two separate authority leaks. A dashboard/observer lane could still slide into implementation edits while another agent owned the active lane, and recovery code could escalate …
- **`1840993a`** — chore: sync bridge.md after Codex Q67 session
  - evolution: Fact: the Q40/Q42 live-run findings showed two separate authority leaks. A dashboard/observer lane could still slide into implementation edits while another agent owned the active lane, and recovery code could escalate …
- **`51da1e71`** — fix(governance): Q67 — strengthen contract connectivity guard detection
  - Codex Round 7 implementation:
  - - Semantic duplicate detection now catches contracts with generic field
  -   names (CatalogCommand vs CommandEntry) by comparing purpose/field
  - evolution: Fact: the Q40/Q42 live-run findings showed two separate authority leaks. A dashboard/observer lane could still slide into implementation edits while another agent owned the active lane, and recovery code could escalate …
- **`b42dd589`** — feat(governance): Q65 — contract connectivity guard + action_routing fix
  - Codex Round 6 implementation:
  - - Q65 fix: action_routing now consumes typed WorkIntakeCoordinationState
  -   via action_routing_coordination.py bridge instead of rebuilding from
  - evolution: Fact: the Q40/Q42 live-run findings showed two separate authority leaks. A dashboard/observer lane could still slide into implementation edits while another agent owned the active lane, and recovery code could escalate …
- **`5d02040f`** — feat(governance): Q54+Q64 — observer signal type, session pacing contract
  - Codex Round 5 implementation:
  - - Q54: 'observer' added to VALID_SIGNAL_TYPES in governance_review_log.py,
  -   optional finding_type field through review input/log/parser path
  - evolution: Fact: the Q40/Q42 live-run findings showed two separate authority leaks. A dashboard/observer lane could still slide into implementation edits while another agent owned the active lane, and recovery code could escalate …
- **`2813a913`** — Refresh external review snapshot for 10242d1a
  - evolution: Fact: the Q40/Q42 live-run findings showed two separate authority leaks. A dashboard/observer lane could still slide into implementation edits while another agent owned the active lane, and recovery code could escalate …
- **`10242d1a`** — feat(governance): Q40+Q42+Q51 — lane edit gate, typed recovery authority, mobile dashboard
  - Codex Round 3 implementation:
  - - Q40: Dashboard/observer lanes are findings-only, cannot edit code
  - - Q42: Typed destructive-recovery authority (RecoveryAuthorityState)
  - evolution: Fact: the Q40/Q42 live-run findings showed two separate authority leaks. A dashboard/observer lane could still slide into implementation edits while another agent owned the active lane, and recovery code could escalate …
- **`368c3b8d`** — docs(audit): Q61 — findings stay flat in LIVE_RUN, not routed to plan system
  - 24 findings (Q37-Q60) logged but not converted to phased MP-items
  - with dependency ordering and graph-derived priority. Context-graph
  - has 64K edges showing which files are hotspots — that intelligence
  - evolution: Fact: the Q40/Q42 live-run findings showed two separate authority leaks. A dashboard/observer lane could still slide into implementation edits while another agent owned the active lane, and recovery code could escalate …
- **`51e01936`** — docs(audit): Q60 — guards run after coding, not during
  - Guards batch after all code is written. Some (code_shape, py_compile,
  - formatter, import cycles) could run incrementally per-file during
  - coding, failing fast before context exhaustion. System should split
  - evolution: Fact: the Q40/Q42 live-run findings showed two separate authority leaks. A dashboard/observer lane could still slide into implementation edits while another agent owned the active lane, and recovery code could escalate …
- **`53e06b4b`** — docs(audit): Q57-Q59 — monitor pass, registry dispatcher, human UX
  - Q57: No canonical single-pass monitor for remote phone mode. Agent
  - manually stitches multiple commands. Need devctl monitor --mode
  - remote_phone that returns all state in one typed mobile-safe pass.
  - evolution: Fact: the Q40/Q42 live-run findings showed two separate authority leaks. A dashboard/observer lane could still slide into implementation edits while another agent owned the active lane, and recovery code could escalate …
- **`862ebd16`** — docs(audit): Q56 — Q54+Q55 compose from existing systems, minimal wiring
  - Research confirmed: self-audit (Q54) needs 1 line in VALID_SIGNAL_TYPES
  - + optional finding_type field. Priority engine (Q55) reuses triage
  - SEVERITY_ORDER + context-graph dependency edges. No new tools needed.
  - evolution: Fact: the Q40/Q42 live-run findings showed two separate authority leaks. A dashboard/observer lane could still slide into implementation edits while another agent owned the active lane, and recovery code could escalate …
- **`d285d33f`** — docs(audit): Q55 — no priority/planning pass over accumulated evidence
  - Findings are flat with no dependency edges or authority-impact scoring.
  - The system needs a scheduler pass that reads all plans/findings/runtime
  - state and emits ranked work priorities. Integrates with existing
  - evolution: Fact: the Q40/Q42 live-run findings showed two separate authority leaks. A dashboard/observer lane could still slide into implementation edits while another agent owned the active lane, and recovery code could escalate …
- **`306116c6`** — docs(audit): Q54 — observer layer ungoverned, no self-audit loop
  - The system governs state/review/commit/push but not HOW the observer
  - gathers evidence. Observation phase is ungoverned — agent can bypass
  - canonical commands, promote inferences, narrate from raw shell without
  - evolution: Fact: the Q40/Q42 live-run findings showed two separate authority leaks. A dashboard/observer lane could still slide into implementation edits while another agent owned the active lane, and recovery code could escalate …
- **`5e9022a7`** — docs(audit): Q53 — dashboard 77% success is command ok=True, not quality
  - Traced to data_science/aggregates.py:82-107. The metric is command
  - return-code success (layer 1: runtime reliability). Not finding
  - precision, decision correctness, or control correctness. Dashboard
  - evolution: Fact: the Q40/Q42 live-run findings showed two separate authority leaks. A dashboard/observer lane could still slide into implementation edits while another agent owned the active lane, and recovery code could escalate …
- **`151b28d9`** — Refresh external review snapshot for 1e193595
  - evolution: Fact: the Q40/Q42 live-run findings showed two separate authority leaks. A dashboard/observer lane could still slide into implementation edits while another agent owned the active lane, and recovery code could escalate …
- **`1e193595`** — docs(audit): Q52 update — cross-tool hook enforcement must be unified
  - Claude Code hooks, Codex hooks, and git hooks are three separate
  - enforcement systems. Governance configured in one is bypassed by
  - using another tool. Fix: one repo-owned governance command that all
  - evolution: Fact: the Q40/Q42 live-run findings showed two separate authority leaks. A dashboard/observer lane could still slide into implementation edits while another agent owned the active lane, and recovery code could escalate …
### Active MP scope (from MASTER_PLAN.md)

- `dev/active/devctl_reporting_upgrade.md` is the phased `devctl` reporting/CIHub specification, but not a separate execution tracker; implementation tasks stay in this file under `MP-297..MP-300`, `MP-303`, `MP-306`, `MP…
- `dev/active/autonomous_control_plane.md` is the autonomous loop + mobile control-plane execution spec; implementation tasks stay in this file under `MP-325..MP-338, MP-340`.
- `dev/active/loop_chat_bridge.md` is the loop artifact-to-chat suggestion coordination runbook; execution evidence and operator handoffs for this path stay there under `MP-338`.
- `dev/active/naming_api_cohesion.md` is the naming/API cohesion execution spec; implementation tasks stay in this file under `MP-267`.
- `dev/active/ide_provider_modularization.md` is the IDE/provider adapter modularization execution spec; implementation tasks stay in this file under `MP-346`, `MP-354`.
- contract slice for MP-355 plus the temporary markdown-swarm operating mode
- `dev/active/ralph_guardrail_control_plane.md` is the Ralph guardrail control plane execution spec; implementation tasks stay in this file under `MP-360..MP-367`.
- `dev/active/review_probes.md` is the review-probe execution spec; implementation tasks stay in this file under `MP-368..MP-375`.
- companion under `MP-376`, not a second main product plan; implementation
- architecture plan for the extracted AI-governance system under `MP-377`.

## 8. Known gaps and open items

- open governance findings: 86

### Startup advisories
- push_allowed: worktree_clean_and_review_accepted

### Stale warnings
- Stop because nothing remains to push.

### Open gap rows
- **governance_open** (`dev/scripts/devctl/security/python_scope.py`): subprocess_missing_timeout: 
- **governance_open** (`dev/scripts/devctl/security/codeql.py`): subprocess_missing_timeout: 
- **governance_open** (`dev/scripts/devctl/integrations/import_core.py`): subprocess_missing_timeout: 
- **governance_open** (`app/operator_console/launch_support.py`): subprocess_missing_timeout: 
- **governance_open** (`dev/scripts/devctl/common.py`): threading_shared_state_no_lock: 
- **governance_open** (`dev/scripts/devctl/review_channel/bridge_projection_state.py`): none_safety_chained_get_crash: 
- **governance_open** (`app/operator_console/state/review/operator_decisions.py`): none_safety_chained_get_crash: 
- **governance_open** (`dev/scripts/devctl/autonomy/run_render.py`): none_safety_chained_get_crash: 

---

Projection produced by `devctl review-snapshot`. Generation stamp `snap-666da2eb428c` binds this file to HEAD `95140873c9e6`; if they drift, the freshness guard will fail CI. When the latest commit only refreshes this generated snapshot, the guard accepts this file as bound to that commit's parent code state.
