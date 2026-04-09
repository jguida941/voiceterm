# VoiceTerm — Review Snapshot

> Deterministically generated from typed governance state. Do not edit by hand — rerun `devctl review-snapshot --write`.

## Quick status

- Branch: `feature/governance-quality-sweep`
- HEAD: `a65fc7c44e4f` — fix(review): land F1+F2 from Codex reviewer pass
- Tree hash: `6b5e042632f5`
- Generation stamp: `snap-c4a63dca5584`
- Generated at (UTC): 2026-04-09T20:11:00Z
- Push decision: `await_checkpoint` — dirty_path_budget_exceeded
- Reviewer mode: `active_dual_agent` (interaction: `remote_control`)
- Pipeline state: `n/a` (approval: `n/a`)
- Delta since last snapshot: 24 commits, 102 files, +6396/-2464
- Governance findings: 39 open / 68 fixed / 121 total
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
- HEAD SHA: `a65fc7c44e4f5e7bc0fbb37137dca12612d37b2c`
- HEAD author: Justin Guida
- HEAD timestamp (UTC): 2026-04-09T16:10:04-04:00

## 2. Governance state

### Push decision
- action: `await_checkpoint`
- reason: dirty_path_budget_exceeded
- push_eligible_now: False
- worktree_clean: False
- staged_path_count: 3
- unstaged_path_count: 10
- next_step_command: `n/a`
- latest_push_report: `dev/reports/push/latest.json`
- latest_push_report_state: `post_push_green` (push_completed)
- current_push_authorization: `push-auth-20260409T132557373695Z` (valid=False)
- authorized_head_commit: `2ca00812b1faf8edc7e08b8d6f2a8c3e8991673e`
- approved_target_identity: `tree-receipt-20260409T132557373695Z:f94740d60423a9e197ed696a6de7e89983b7b90e`
- publication_backlog: queued
- publication_guidance: 1 local commit(s) waiting for governed push once the current slice is checkpoint-clean.

### Reviewer runtime
- reviewer_mode: `active_dual_agent`
- reviewer_freshness: unknown
- reviewer_publish_clear: False
- interaction_mode: `remote_control`

### Remote commit pipeline
- state: `n/a`
- approval_state: `n/a`

### Work intake
- active plan: **Master Plan (Active, Unified)**
- plan path: `dev/active/MASTER_PLAN.md`
- active MP scope: all active MP execution state
- advisory: `checkpoint_before_continue` — dirty_path_budget_exceeded
- checkpoint_required: **yes**

## 3. Delta — what changed since the previous snapshot

Range: last 24 commits ending at `a65fc7c44e4f`

- commits: 24
- files changed: 102
- insertions: +6396
- deletions: -2464
- bundle classes touched: tooling, docs
- risk add-ons triggered: Parser / ANSI boundary
- authority surfaces touched: 9 file(s)

### Commits

| # | SHA | Subject | Files | +/- | Bundle | Risk |
|---|---|---|---|---|---|---|
| 1 | `a65fc7c4` | fix(review): land F1+F2 from Codex reviewer pass | 5 | +161/-58 | tooling |  |
| 2 | `adb266b5` | Refresh external review snapshot for d84b27fa | 1 | +60/-58 | tooling |  |
| 3 | `d84b27fa` | feat(lifecycle): add recoverable flag to ReviewerSupervisor… | 2 | +77/-86 | tooling |  |
| 4 | `8f42ea3f` | feat(devctl): rollout-tail MVP for Codex/Claude session JSO… | 11 | +1088/-49 | tooling | Parser / ANSI boundary |
| 5 | `2ca00812` | Refresh external review snapshot for 696f4772 | 1 | +52/-46 | tooling |  |
| 6 | `696f4772` | fix(hygiene): trust supervisor heartbeat for reparented con… | 2 | +62/-54 | tooling |  |
| 7 | `8c800411` | Refresh external review snapshot for a12b6593 | 1 | +82/-77 | tooling |  |
| 8 | `a12b6593` | feat(review-channel): attach-remote-control action + typed… | 37 | +1188/-131 | tooling | Parser / ANSI boundary |
| 9 | `a5ad7fc0` | fix(runtime): F1 coordination parity via review_state_overr… | 7 | +253/-103 | tooling |  |
| 10 | `838b762c` | Refresh external review snapshot for d7e7e597 | 1 | +57/-51 | tooling |  |
| 11 | `d7e7e597` | policy: declare operator_interaction_mode=remote_control | 2 | +63/-63 | tooling |  |
| 12 | `08770a66` | Refresh external review snapshot for 675ca93d | 1 | +65/-69 | tooling |  |
| 13 | `675ca93d` | fix: scope post-push validation to published diff | 13 | +359/-91 | tooling |  |
| 14 | `a60f1470` | Refresh external review snapshot for 69317302 | 1 | +52/-49 | tooling |  |
| 15 | `69317302` | fix: support coderabbit gate script imports | 3 | +82/-65 | tooling |  |
| 16 | `bc1a40ec` | Refresh external review snapshot for 013e15f6 | 1 | +63/-66 | tooling |  |
| 17 | `013e15f6` | fix: defer coderabbit gates until publish | 11 | +380/-178 | tooling |  |
| 18 | `46de6f81` | Refresh external review snapshot for 4c8aeb5b | 1 | +63/-70 | tooling |  |
| 19 | `4c8aeb5b` | chore: route release checks and review commands | 13 | +285/-61 | tooling |  |
| 20 | `a3fd3393` | Refresh external review snapshot for 38535f77 | 1 | +63/-62 | tooling |  |
| 21 | `38535f77` | chore: wire mutation bypass guard into shared lanes | 14 | +146/-63 | tooling |  |
| 22 | `0a194dfe` | Refresh external review snapshot for a547a2be | 1 | +59/-65 | tooling |  |
| 23 | `a547a2be` | refactor: move path audit behind compatibility shim | 9 | +528/-417 | tooling |  |
| 24 | `d094550c` | chore: register mutation guard and unify bootstrap catalog | 27 | +1108/-432 | tooling |  |

### Files

| Path | Bundle | +/- |
|---|---|---|
| `.github/workflows/release_preflight.yml` | tooling | +1/-0 |
| `.github/workflows/tooling_control_plane.yml` | tooling | +3/-0 |
| `AGENTS.md` | docs | +50/-5 |
| `bridge.md` | docs | +4/-4 |
| `dev/active/MASTER_PLAN.md` | tooling | +55/-3 |
| `dev/active/ai_governance_platform.md` | tooling | +66/-0 |
| `dev/active/continuous_swarm.md` | tooling | +10/-0 |
| `dev/active/platform_authority_loop.md` | tooling | +17/-1 |
| `dev/active/remote_commit_pipeline.md` | tooling | +22/-0 |
| `dev/active/remote_control_runtime.md` | tooling | +43/-0 |
| `dev/audits/REVIEW_SNAPSHOT.md` | tooling | +1431/-1456 |
| `dev/config/devctl_repo_policy.json` | tooling | +3/-0 |
| `dev/config/git_hooks/pre-push-governed-push.sh` | tooling | +12/-1 |
| `dev/config/quality_presets/portable_python.json` | tooling | +1/-0 |
| `dev/guides/DEVELOPMENT.md` | docs | +33/-9 |
| `dev/history/ENGINEERING_EVOLUTION.md` | tooling | +238/-0 |
| `dev/scripts/README.md` | tooling | +52/-12 |
| `dev/scripts/checks/check_architecture_surface_sync.py` | tooling | +19/-1 |
| `dev/scripts/checks/coderabbit_gate_core.py` | tooling | +71/-90 |
| `dev/scripts/checks/coderabbit_gate_core/__init__.py` | tooling | +6/-37 |
| `dev/scripts/checks/coderabbit_gate_support.py` | tooling | +181/-0 |
| `dev/scripts/devctl/bundles/registry.py` | tooling | +1/-0 |
| `dev/scripts/devctl/cli.py` | tooling | +5/-0 |
| `dev/scripts/devctl/commands/check/__init__.py` | tooling | +30/-2 |
| `dev/scripts/devctl/commands/check/process_sweep.py` | tooling | +31/-2 |
| `dev/scripts/devctl/commands/dashboard.py` | tooling | +11/-3 |
| `dev/scripts/devctl/commands/discover/__init__.py` | tooling | +5/-2 |
| `dev/scripts/devctl/commands/governance/hygiene_support.py` | tooling | +13/-1 |
| `dev/scripts/devctl/commands/governance/session_resume_render.py` | tooling | +21/-0 |
| `dev/scripts/devctl/commands/governance/session_resume_support.py` | tooling | +38/-14 |
| `dev/scripts/devctl/commands/review_channel/__init__.py` | tooling | +9/-0 |
| `dev/scripts/devctl/commands/review_channel/_attach_remote_control.py` | tooling | +180/-0 |
| `dev/scripts/devctl/commands/review_channel/doctor_support.py` | tooling | +36/-0 |
| `dev/scripts/devctl/commands/review_channel/status.py` | tooling | +4/-0 |
| `dev/scripts/devctl/commands/review_channel_command/constants.py` | tooling | +1/-0 |
| `dev/scripts/devctl/commands/review_channel_command/helpers.py` | tooling | +12/-0 |
| `dev/scripts/devctl/commands/rollout_tail/__init__.py` | tooling | +37/-0 |
| `dev/scripts/devctl/commands/rollout_tail/command.py` | tooling | +70/-0 |
| `dev/scripts/devctl/commands/rollout_tail/constants.py` | tooling | +19/-0 |
| `dev/scripts/devctl/commands/rollout_tail/discovery.py` | tooling | +86/-0 |
| _62 more files trimmed_ | | |

## 4. Quality signals

### Governance review
- total findings: 121
- open: 39
- fixed: 68
- false positives: 0

Recent findings:
- `agent_checkpoint_contract_ignorance` — `dev/scripts/devctl/review_channel/bridge_sanitize.py` (n/a, verdict=`confirmed_issue`)
- `claude_uses_osascript_not_typed_system` — `dev/scripts/devctl/review_channel/state.py` (n/a, verdict=`confirmed_issue`)
- `push_invalidation_head_equality` — `dev/scripts/devctl/review_channel/push_state.py` (n/a, verdict=`confirmed_issue`)
- `reviewer_truth_distributed_no_owner` — `dev/scripts/devctl/review_channel/state.py` (n/a, verdict=`confirmed_issue`)
- `startup_surface_tokens_unpopulated` — `dev/scripts/devctl/runtime/startup_context.py` (n/a, verdict=`confirmed_issue`)
- `terminal_window_id_not_captured` — `dev/scripts/devctl/review_channel/terminal_app.py` (n/a, verdict=`confirmed_issue`)
- `bridge_projection_drops_operator_direction` — `dev/scripts/devctl/review_channel/bridge_projection_state.py` (n/a, verdict=`confirmed_issue`)
- `bridge_still_active_gate_not_projection` — `dev/scripts/devctl/review_channel/state.py` (n/a, verdict=`confirmed_issue`)
- `need_review_channel_doctor_surface` — `dev/scripts/devctl/review_channel/state.py` (n/a, verdict=`confirmed_issue`)
- `reviewer_runtime_contract_needed` — `dev/scripts/devctl/platform/runtime_state_contract_rows.py` (n/a, verdict=`confirmed_issue`)

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
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/review_channel/reviewer_runtime_contract.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/review_channel/reviewer_runtime_session_owner.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/reviewer_runtime_models.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/reviewer_runtime_parser.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/startup_context.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/runtime/test_startup_context.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/active/remote_commit_pipeline.md`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/vcs/test_governed_executor.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/review_channel/test_reviewer_runtime_doctor.py`) — Review contract-level invariants for this file
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/platform/surface_state_contract_rows.py`) — Commit a12b6593 changed dev/scripts/devctl/platform/surface_state_contract_rows.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/review_channel/reviewer_runtime_contract.py`) — Commit a12b6593 changed dev/scripts/devctl/review_channel/reviewer_runtime_contract.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/reviewer_runtime_models.py`) — Commit a12b6593 changed dev/scripts/devctl/runtime/reviewer_runtime_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/governance/system_catalog_models.py`) — Commit d094550c changed dev/scripts/devctl/governance/system_catalog_models.py

### Suggested verification commands

- `python3 dev/scripts/devctl.py check --profile ci`
- `python3 dev/scripts/devctl.py probe-report --format md`
- `python3 dev/scripts/devctl.py docs-check --strict-tooling`
- `python3 dev/scripts/devctl.py governance-review --format md`
- `python3 dev/scripts/devctl.py check-router --format md`

## 7. Reasoning — why these changes landed

### Per-commit rationale

- **`a65fc7c4` | markers: F1, F2** — fix(review): land F1+F2 from Codex reviewer pass
  - Codex (reviewer, PID 90168) posted F1/F2/F3 findings during the live
  - review channel pass for HEAD adb266b5 and authored the F1 + F2 fixes
  - through its conductor session. Claude-88455 is committing them so the
  - evolution: Fact: the phone-steered Claude remote-control wrapper was still too prompt- local. It printed typed health but did not consume typed next-step / recovery truth, and the tracked remote prompt still taught raw `git commit…
- **`adb266b5`** — Refresh external review snapshot for d84b27fa
  - evolution: Fact: the phone-steered Claude remote-control wrapper was still too prompt- local. It printed typed health but did not consume typed next-step / recovery truth, and the tracked remote prompt still taught raw `git commit…
- **`d84b27fa`** — feat(lifecycle): add recoverable flag to ReviewerSupervisorHeartbeat (Q8 groundwork)
  - Partial Q8 fix: extends the typed ReviewerSupervisorHeartbeat contract
  - with a `recoverable: bool = False` field so an intentional
  - operator-directed stop can be distinguished from a permanent manual
  - evolution: Fact: the phone-steered Claude remote-control wrapper was still too prompt- local. It printed typed health but did not consume typed next-step / recovery truth, and the tracked remote prompt still taught raw `git commit…
- **`8f42ea3f`** — feat(devctl): rollout-tail MVP for Codex/Claude session JSONL projection
  - Closes the single biggest typed-state gap identified in session 2026-04-09:
  - remote operators had no visibility into agent CLI internals (thoughts,
  - tool calls, sandbox-escalation requests). Codex's own rollout JSONL
  - evolution: Fact: the phone-steered Claude remote-control wrapper was still too prompt- local. It printed typed health but did not consume typed next-step / recovery truth, and the tracked remote prompt still taught raw `git commit…
- **`2ca00812`** — Refresh external review snapshot for 696f4772
  - evolution: Fact: the phone-steered Claude remote-control wrapper was still too prompt- local. It printed typed health but did not consume typed next-step / recovery truth, and the tracked remote prompt still taught raw `git commit…
- **`696f4772`** — fix(hygiene): trust supervisor heartbeat for reparented conductor detection
  - The hygiene runtime-process audit previously excluded supervised conductor
  - scripts from the supervised_conductors list whenever their ppid had become
  - 1 (init). Unix reparents children to init when their original parent shell
  - evolution: Fact: the phone-steered Claude remote-control wrapper was still too prompt- local. It printed typed health but did not consume typed next-step / recovery truth, and the tracked remote prompt still taught raw `git commit…
- **`8c800411`** — Refresh external review snapshot for a12b6593
  - evolution: Fact: the phone-steered Claude remote-control wrapper was still too prompt- local. It printed typed health but did not consume typed next-step / recovery truth, and the tracked remote prompt still taught raw `git commit…
- **`a12b6593`** — feat(review-channel): attach-remote-control action + typed attachment state
  - Adds the `review-channel --action attach-remote-control` action with a typed
  - RemoteControlAttachmentArtifact model and regression tests. Wires the typed
  - attachment registration through remote-bridge-loop.sh and
  - evolution: Fact: the phone-steered Claude remote-control wrapper was still too prompt- local. It printed typed health but did not consume typed next-step / recovery truth, and the tracked remote prompt still taught raw `git commit…
- **`a5ad7fc0` | markers: F1** — fix(runtime): F1 coordination parity via review_state_override
  - Closes the F1 non-determinism finding from dev/active/remote_control_runtime.md:
  - `TestCoordinationParityF1::test_three_surfaces_report_identical_coordination`
  - was flaky because `build_startup_context()` reused one typed `review_state`
  - evolution: Fact: the phone-steered Claude remote-control wrapper was still too prompt- local. It printed typed health but did not consume typed next-step / recovery truth, and the tracked remote prompt still taught raw `git commit…
- **`838b762c`** — Refresh external review snapshot for d7e7e597
  - evolution: Fact: the phone-steered Claude remote-control wrapper was still too prompt- local. It printed typed health but did not consume typed next-step / recovery truth, and the tracked remote prompt still taught raw `git commit…
- **`d7e7e597`** — policy: declare operator_interaction_mode=remote_control
  - Adds repo_governance.bridge_config.operator_interaction_mode="remote_control"
  - to dev/config/devctl_repo_policy.json so the F4 fail-closed launcher
  - discipline permits headless bridge launches (--terminal none) from the
  - evolution: Fact: the phone-steered Claude remote-control wrapper was still too prompt- local. It printed typed health but did not consume typed next-step / recovery truth, and the tracked remote prompt still taught raw `git commit…
- **`08770a66`** — Refresh external review snapshot for 675ca93d
  - evolution: Fact: the phone-steered Claude remote-control wrapper was still too prompt- local. It printed typed health but did not consume typed next-step / recovery truth, and the tracked remote prompt still taught raw `git commit…
- **`675ca93d`** — fix: scope post-push validation to published diff
  - evolution: Fact: the phone-steered Claude remote-control wrapper was still too prompt- local. It printed typed health but did not consume typed next-step / recovery truth, and the tracked remote prompt still taught raw `git commit…
- **`a60f1470`** — Refresh external review snapshot for 69317302
  - evolution: Fact: the phone-steered Claude remote-control wrapper was still too prompt- local. It printed typed health but did not consume typed next-step / recovery truth, and the tracked remote prompt still taught raw `git commit…
- **`69317302`** — fix: support coderabbit gate script imports
  - evolution: Fact: the phone-steered Claude remote-control wrapper was still too prompt- local. It printed typed health but did not consume typed next-step / recovery truth, and the tracked remote prompt still taught raw `git commit…
- **`bc1a40ec`** — Refresh external review snapshot for 013e15f6
  - evolution: Fact: the phone-steered Claude remote-control wrapper was still too prompt- local. It printed typed health but did not consume typed next-step / recovery truth, and the tracked remote prompt still taught raw `git commit…
- **`013e15f6`** — fix: defer coderabbit gates until publish
  - evolution: Fact: the phone-steered Claude remote-control wrapper was still too prompt- local. It printed typed health but did not consume typed next-step / recovery truth, and the tracked remote prompt still taught raw `git commit…
- **`46de6f81`** — Refresh external review snapshot for 4c8aeb5b
  - evolution: Fact: the phone-steered Claude remote-control wrapper was still too prompt- local. It printed typed health but did not consume typed next-step / recovery truth, and the tracked remote prompt still taught raw `git commit…
- **`4c8aeb5b`** — chore: route release checks and review commands
  - evolution: Fact: the phone-steered Claude remote-control wrapper was still too prompt- local. It printed typed health but did not consume typed next-step / recovery truth, and the tracked remote prompt still taught raw `git commit…
- **`a3fd3393`** — Refresh external review snapshot for 38535f77
  - evolution: Fact: the phone-steered Claude remote-control wrapper was still too prompt- local. It printed typed health but did not consume typed next-step / recovery truth, and the tracked remote prompt still taught raw `git commit…
- **`38535f77`** — chore: wire mutation bypass guard into shared lanes
  - evolution: Fact: the phone-steered Claude remote-control wrapper was still too prompt- local. It printed typed health but did not consume typed next-step / recovery truth, and the tracked remote prompt still taught raw `git commit…
- **`0a194dfe`** — Refresh external review snapshot for a547a2be
  - evolution: Fact: the phone-steered Claude remote-control wrapper was still too prompt- local. It printed typed health but did not consume typed next-step / recovery truth, and the tracked remote prompt still taught raw `git commit…
- **`a547a2be`** — refactor: move path audit behind compatibility shim
  - evolution: Fact: the phone-steered Claude remote-control wrapper was still too prompt- local. It printed typed health but did not consume typed next-step / recovery truth, and the tracked remote prompt still taught raw `git commit…
- **`d094550c`** — chore: register mutation guard and unify bootstrap catalog
  - evolution: Fact: the phone-steered Claude remote-control wrapper was still too prompt- local. It printed typed health but did not consume typed next-step / recovery truth, and the tracked remote prompt still taught raw `git commit…
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

- open governance findings: 39

### Startup advisories
- checkpoint_before_continue: dirty_path_budget_exceeded

### Stale warnings
- Keep editing the current slice.
- Move straight to the governed push path.

### Open gap rows
- **governance_open** (`dev/scripts/devctl/review_channel/bridge_sanitize.py`): agent_checkpoint_contract_ignorance: 
- **governance_open** (`dev/scripts/devctl/review_channel/state.py`): claude_uses_osascript_not_typed_system: 
- **governance_open** (`dev/scripts/devctl/review_channel/push_state.py`): push_invalidation_head_equality: 
- **governance_open** (`dev/scripts/devctl/review_channel/state.py`): reviewer_truth_distributed_no_owner: 
- **governance_open** (`dev/scripts/devctl/runtime/startup_context.py`): startup_surface_tokens_unpopulated: 
- **governance_open** (`dev/scripts/devctl/review_channel/terminal_app.py`): terminal_window_id_not_captured: 
- **governance_open** (`dev/scripts/devctl/review_channel/bridge_projection_state.py`): bridge_projection_drops_operator_direction: 
- **governance_open** (`dev/scripts/devctl/review_channel/state.py`): bridge_still_active_gate_not_projection: 

---

Projection produced by `devctl review-snapshot`. Generation stamp `snap-c4a63dca5584` binds this file to HEAD `a65fc7c44e4f`; if they drift, the freshness guard will fail CI. When the latest commit only refreshes this generated snapshot, the guard accepts this file as bound to that commit's parent code state.
