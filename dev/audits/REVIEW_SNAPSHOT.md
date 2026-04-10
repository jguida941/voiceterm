# VoiceTerm — Review Snapshot

> Deterministically generated from typed governance state. Do not edit by hand — rerun `devctl review-snapshot --write`.

## Quick status

- Branch: `feature/governance-quality-sweep`
- HEAD: `b5d609ce5e21` — fix: keep poll status mode coherent
- Tree hash: `f862716ec206`
- Generation stamp: `snap-fadc5dd845f1`
- Generated at (UTC): 2026-04-10T01:58:58Z
- Push decision: `await_checkpoint` — staged_index_present
- Reviewer mode: `single_agent` (interaction: `remote_control`)
- Pipeline state: `n/a` (approval: `n/a`)
- Delta since last snapshot: 24 commits, 82 files, +9121/-1644
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
- HEAD SHA: `b5d609ce5e212babe502a142472941a5e14b8105`
- HEAD author: Justin Guida
- HEAD timestamp (UTC): 2026-04-09T21:31:38-04:00

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
- current_push_authorization: `push-auth-20260410T013026997488Z` (valid=True)
- authorized_head_commit: `b5d609ce5e212babe502a142472941a5e14b8105`
- approved_target_identity: `tree-receipt-20260410T013026997488Z:f06cd7445bc99ebd96c363dcd2e920a4c1d5ab6f`
- publication_backlog: recommended
- publication_guidance: 2 local commit(s) waiting for governed push once the current slice is checkpoint-clean.

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
- advisory: `checkpoint_allowed` — worktree_dirty_within_budget

## 3. Delta — what changed since the previous snapshot

Range: last 24 commits ending at `b5d609ce5e21`

- commits: 24
- files changed: 82
- insertions: +9121
- deletions: -1644
- bundle classes touched: tooling, docs
- risk add-ons triggered: Parser / ANSI boundary
- authority surfaces touched: 6 file(s)

### Commits

| # | SHA | Subject | Files | +/- | Bundle | Risk |
|---|---|---|---|---|---|---|
| 1 | `b5d609ce` | fix: keep poll status mode coherent | 3 | +117/-63 | tooling |  |
| 2 | `98cc9ab0` | fix: stabilize review-channel recovery | 13 | +843/-180 | tooling |  |
| 3 | `655db93a` | fix(discover): Q22 closure — repair KeyError crashes in --f… | 2 | +50/-42 | tooling |  |
| 4 | `8f4bf379` | docs(audits): log BL-032 through BL-035 from session 2026-0… | 2 | +173/-58 | tooling |  |
| 5 | `1864fc2c` | feat(devctl): BL-031 cross-mind polling — agent-mind command | 10 | +1513/-55 | tooling |  |
| 6 | `4129af6c` | docs(governance): Codex's doc updates for 2026-04-09 F1/F2/… | 7 | +403/-66 | tooling |  |
| 7 | `5985e70c` | feat(devctl): pipeline recovery command (BL-006) — typed re… | 12 | +1652/-46 | tooling |  |
| 8 | `49d1db53` | Refresh external review snapshot for 363fe42c | 1 | +57/-54 | tooling |  |
| 9 | `363fe42c` | fix(hygiene): Platform Boundary fix + regression tests + co… | 3 | +223/-47 | tooling |  |
| 10 | `e4870754` | fix(review-channel): attach-remote-control cleanup (F2.1 th… | 4 | +336/-70 | tooling |  |
| 11 | `d35abef0` | test(process-sweep): positive + negative regression tests f… | 2 | +195/-60 | tooling |  |
| 12 | `971647ec` | fix(rollout-tail): F3 narrow Claude session discovery + tai… | 4 | +351/-58 | tooling | Parser / ANSI boundary |
| 13 | `a65fc7c4` | fix(review): land F1+F2 from Codex reviewer pass | 5 | +161/-58 | tooling |  |
| 14 | `adb266b5` | Refresh external review snapshot for d84b27fa | 1 | +60/-58 | tooling |  |
| 15 | `d84b27fa` | feat(lifecycle): add recoverable flag to ReviewerSupervisor… | 2 | +77/-86 | tooling |  |
| 16 | `8f42ea3f` | feat(devctl): rollout-tail MVP for Codex/Claude session JSO… | 11 | +1088/-49 | tooling | Parser / ANSI boundary |
| 17 | `2ca00812` | Refresh external review snapshot for 696f4772 | 1 | +52/-46 | tooling |  |
| 18 | `696f4772` | fix(hygiene): trust supervisor heartbeat for reparented con… | 2 | +62/-54 | tooling |  |
| 19 | `8c800411` | Refresh external review snapshot for a12b6593 | 1 | +82/-77 | tooling |  |
| 20 | `a12b6593` | feat(review-channel): attach-remote-control action + typed… | 37 | +1188/-131 | tooling | Parser / ANSI boundary |
| 21 | `a5ad7fc0` | fix(runtime): F1 coordination parity via review_state_overr… | 7 | +253/-103 | tooling |  |
| 22 | `838b762c` | Refresh external review snapshot for d7e7e597 | 1 | +57/-51 | tooling |  |
| 23 | `d7e7e597` | policy: declare operator_interaction_mode=remote_control | 2 | +63/-63 | tooling |  |
| 24 | `08770a66` | Refresh external review snapshot for 675ca93d | 1 | +65/-69 | tooling |  |

### Files

| Path | Bundle | +/- |
|---|---|---|
| `AGENTS.md` | docs | +18/-2 |
| `bridge.md` | docs | +4/-4 |
| `dev/active/MASTER_PLAN.md` | tooling | +39/-0 |
| `dev/active/ai_governance_platform.md` | tooling | +13/-0 |
| `dev/active/continuous_swarm.md` | tooling | +10/-0 |
| `dev/active/remote_control_runtime.md` | tooling | +59/-0 |
| `dev/audits/REVIEW_SNAPSHOT.md` | tooling | +1395/-1383 |
| `dev/audits/TEST_BACKLOG.md` | tooling | +733/-0 |
| `dev/config/devctl_repo_policy.json` | tooling | +3/-0 |
| `dev/config/git_hooks/pre-push-governed-push.sh` | tooling | +12/-1 |
| `dev/guides/DEVELOPMENT.md` | docs | +30/-3 |
| `dev/history/ENGINEERING_EVOLUTION.md` | tooling | +154/-0 |
| `dev/scripts/README.md` | tooling | +27/-7 |
| `dev/scripts/devctl/agent_mind_parser.py` | tooling | +75/-0 |
| `dev/scripts/devctl/cli.py` | tooling | +13/-0 |
| `dev/scripts/devctl/commands/agent_mind/__init__.py` | tooling | +27/-0 |
| `dev/scripts/devctl/commands/agent_mind/command.py` | tooling | +141/-0 |
| `dev/scripts/devctl/commands/agent_mind/projection.py` | tooling | +65/-0 |
| `dev/scripts/devctl/commands/agent_mind/renderers.py` | tooling | +110/-0 |
| `dev/scripts/devctl/commands/agent_mind/slice_builder.py` | tooling | +297/-0 |
| `dev/scripts/devctl/commands/check/process_sweep.py` | tooling | +31/-2 |
| `dev/scripts/devctl/commands/dashboard.py` | tooling | +11/-3 |
| `dev/scripts/devctl/commands/discover/__init__.py` | tooling | +9/-3 |
| `dev/scripts/devctl/commands/governance/hygiene_support.py` | tooling | +49/-5 |
| `dev/scripts/devctl/commands/governance/session_resume_render.py` | tooling | +21/-0 |
| `dev/scripts/devctl/commands/governance/session_resume_support.py` | tooling | +40/-14 |
| `dev/scripts/devctl/commands/pipeline/__init__.py` | tooling | +28/-0 |
| `dev/scripts/devctl/commands/pipeline/abandon_action.py` | tooling | +165/-0 |
| `dev/scripts/devctl/commands/pipeline/command.py` | tooling | +39/-0 |
| `dev/scripts/devctl/commands/pipeline/recover_action.py` | tooling | +191/-0 |
| `dev/scripts/devctl/commands/pipeline/refresh_authorization_action.py` | tooling | +173/-0 |
| `dev/scripts/devctl/commands/pipeline/status_action.py` | tooling | +153/-0 |
| `dev/scripts/devctl/commands/pipeline/support.py` | tooling | +268/-0 |
| `dev/scripts/devctl/commands/review_channel/__init__.py` | tooling | +9/-0 |
| `dev/scripts/devctl/commands/review_channel/_attach_remote_control.py` | tooling | +203/-12 |
| `dev/scripts/devctl/commands/review_channel/_recover.py` | tooling | +69/-100 |
| `dev/scripts/devctl/commands/review_channel/_reviewer.py` | tooling | +49/-0 |
| `dev/scripts/devctl/commands/review_channel_command/constants.py` | tooling | +1/-0 |
| `dev/scripts/devctl/commands/review_channel_command/helpers.py` | tooling | +12/-0 |
| `dev/scripts/devctl/commands/rollout_tail/__init__.py` | tooling | +37/-0 |
| _42 more files trimmed_ | | |

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
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/platform/surface_state_contract_rows.py`) — Commit a12b6593 changed dev/scripts/devctl/platform/surface_state_contract_rows.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/review_channel/reviewer_runtime_contract.py`) — Commit a12b6593 changed dev/scripts/devctl/review_channel/reviewer_runtime_contract.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/reviewer_runtime_models.py`) — Commit a12b6593 changed dev/scripts/devctl/runtime/reviewer_runtime_models.py

### Suggested verification commands

- `python3 dev/scripts/devctl.py check --profile ci`
- `python3 dev/scripts/devctl.py probe-report --format md`
- `python3 dev/scripts/devctl.py docs-check --strict-tooling`
- `python3 dev/scripts/devctl.py governance-review --format md`
- `python3 dev/scripts/devctl.py check-router --format md`

## 7. Reasoning — why these changes landed

### Per-commit rationale

- **`b5d609ce`** — fix: keep poll status mode coherent
  - evolution: Fact: the narrow repo-owned `review-channel --action recover` path had one real remote-control gap left. In governed `--terminal none` mode it prepared fresh Claude implementer scripts and metadata, but `_maybe_launch_r…
- **`98cc9ab0`** — fix: stabilize review-channel recovery
  - evolution: Fact: the narrow repo-owned `review-channel --action recover` path had one real remote-control gap left. In governed `--terminal none` mode it prepared fresh Claude implementer scripts and metadata, but `_maybe_launch_r…
- **`655db93a`** — fix(discover): Q22 closure — repair KeyError crashes in --format md renderer
  - Closes Q22 from dev/audits/LIVE_RUN.md: `devctl discover --format md`
  - crashed with KeyError when rendering guards, probes, and surfaces.
  - This was the top-level AI-callable capability inventory — every AI
  - evolution: Fact: the narrow repo-owned `review-channel --action recover` path had one real remote-control gap left. In governed `--terminal none` mode it prepared fresh Claude implementer scripts and metadata, but `_maybe_launch_r…
- **`8f4bf379`** — docs(audits): log BL-032 through BL-035 from session 2026-04-09 audit pass
  - Extends TEST_BACKLOG.md with four new findings surfaced during the
  - rich-detail audit pass + cross-mind polling landing:
  - evolution: Fact: the narrow repo-owned `review-channel --action recover` path had one real remote-control gap left. In governed `--terminal none` mode it prepared fresh Claude implementer scripts and metadata, but `_maybe_launch_r…
- **`1864fc2c`** — feat(devctl): BL-031 cross-mind polling — agent-mind command
  - Implements the cross-mind polling MVP from TEST_BACKLOG BL-031. This is
  - the architectural multiplier the operator asked for in session 2026-04-09:
  - agents can now read each other's live JSONL reasoning streams as typed
  - evolution: Fact: the narrow repo-owned `review-channel --action recover` path had one real remote-control gap left. In governed `--terminal none` mode it prepared fresh Claude implementer scripts and metadata, but `_maybe_launch_r…
- **`4129af6c` | markers: F1, F2, F3** — docs(governance): Codex's doc updates for 2026-04-09 F1/F2/F3 closure
  - Authored by Codex (reviewer conductor PID 90168) during the session
  - 2026-04-09 review pass. Codex wrote the canonical documentation for
  - the F1/F2/F3 reviewer closure into the governance doc surfaces while
  - evolution: Fact: the narrow repo-owned `review-channel --action recover` path had one real remote-control gap left. In governed `--terminal none` mode it prepared fresh Claude implementer scripts and metadata, but `_maybe_launch_r…
- **`5985e70c`** — feat(devctl): pipeline recovery command (BL-006) — typed recovery for wedged commit pipelines
  - Implements `devctl.py pipeline --action {status,recover,abandon,refresh-authorization}`,
  - the typed recovery surface that eliminates the single biggest bypass driver
  - of session 2026-04-09.
  - evolution: Fact: the narrow repo-owned `review-channel --action recover` path had one real remote-control gap left. In governed `--terminal none` mode it prepared fresh Claude implementer scripts and metadata, but `_maybe_launch_r…
- **`49d1db53`** — Refresh external review snapshot for 363fe42c
  - evolution: Fact: the narrow repo-owned `review-channel --action recover` path had one real remote-control gap left. In governed `--terminal none` mode it prepared fresh Claude implementer scripts and metadata, but `_maybe_launch_r…
- **`363fe42c`** — fix(hygiene): Platform Boundary fix + regression tests + corrupt heartbeat diagnostic
  - Closes H1, H2, H3 from code-reviewer agent audit on commit 696f4772
  - (`fix(hygiene): trust supervisor heartbeat for reparented conductor
  - detection`).
  - evolution: Fact: the narrow repo-owned `review-channel --action recover` path had one real remote-control gap left. In governed `--terminal none` mode it prepared fresh Claude implementer scripts and metadata, but `_maybe_launch_r…
- **`e4870754` | markers: F2** — fix(review-channel): attach-remote-control cleanup (F2.1 through F2.7)
  - Closes 6 code-review findings on commit a12b6593 (`feat(review-channel):
  - attach-remote-control action + typed attachment state`). All findings
  - surfaced by the parallel code-reviewer agent pass.
  - evolution: Fact: the narrow repo-owned `review-channel --action recover` path had one real remote-control gap left. In governed `--terminal none` mode it prepared fresh Claude implementer scripts and metadata, but `_maybe_launch_r…
- **`d35abef0` | markers: F2** — test(process-sweep): positive + negative regression tests for F2 fallback
  - Adds two regression tests for the supervisor-backed conductor-protection
  - fallback in `_protected_registered_conductor_pids` (landed alongside
  - Codex's F2 fix in commit a65fc7c4).
  - evolution: Fact: the narrow repo-owned `review-channel --action recover` path had one real remote-control gap left. In governed `--terminal none` mode it prepared fresh Claude implementer scripts and metadata, but `_maybe_launch_r…
- **`971647ec` | markers: F3** — fix(rollout-tail): F3 narrow Claude session discovery + tail reader off-by-one
  - Closes F3 from Codex's review pass on HEAD adb266b5, plus a tail-reader
  - bug caught by code-reviewer agent audit on the same commit set.
  - evolution: Fact: the narrow repo-owned `review-channel --action recover` path had one real remote-control gap left. In governed `--terminal none` mode it prepared fresh Claude implementer scripts and metadata, but `_maybe_launch_r…
- **`a65fc7c4` | markers: F1, F2** — fix(review): land F1+F2 from Codex reviewer pass
  - Codex (reviewer, PID 90168) posted F1/F2/F3 findings during the live
  - review channel pass for HEAD adb266b5 and authored the F1 + F2 fixes
  - through its conductor session. Claude-88455 is committing them so the
  - evolution: Fact: the narrow repo-owned `review-channel --action recover` path had one real remote-control gap left. In governed `--terminal none` mode it prepared fresh Claude implementer scripts and metadata, but `_maybe_launch_r…
- **`adb266b5`** — Refresh external review snapshot for d84b27fa
  - evolution: Fact: the narrow repo-owned `review-channel --action recover` path had one real remote-control gap left. In governed `--terminal none` mode it prepared fresh Claude implementer scripts and metadata, but `_maybe_launch_r…
- **`d84b27fa`** — feat(lifecycle): add recoverable flag to ReviewerSupervisorHeartbeat (Q8 groundwork)
  - Partial Q8 fix: extends the typed ReviewerSupervisorHeartbeat contract
  - with a `recoverable: bool = False` field so an intentional
  - operator-directed stop can be distinguished from a permanent manual
  - evolution: Fact: the narrow repo-owned `review-channel --action recover` path had one real remote-control gap left. In governed `--terminal none` mode it prepared fresh Claude implementer scripts and metadata, but `_maybe_launch_r…
- **`8f42ea3f`** — feat(devctl): rollout-tail MVP for Codex/Claude session JSONL projection
  - Closes the single biggest typed-state gap identified in session 2026-04-09:
  - remote operators had no visibility into agent CLI internals (thoughts,
  - tool calls, sandbox-escalation requests). Codex's own rollout JSONL
  - evolution: Fact: the narrow repo-owned `review-channel --action recover` path had one real remote-control gap left. In governed `--terminal none` mode it prepared fresh Claude implementer scripts and metadata, but `_maybe_launch_r…
- **`2ca00812`** — Refresh external review snapshot for 696f4772
  - evolution: Fact: the narrow repo-owned `review-channel --action recover` path had one real remote-control gap left. In governed `--terminal none` mode it prepared fresh Claude implementer scripts and metadata, but `_maybe_launch_r…
- **`696f4772`** — fix(hygiene): trust supervisor heartbeat for reparented conductor detection
  - The hygiene runtime-process audit previously excluded supervised conductor
  - scripts from the supervised_conductors list whenever their ppid had become
  - 1 (init). Unix reparents children to init when their original parent shell
  - evolution: Fact: the narrow repo-owned `review-channel --action recover` path had one real remote-control gap left. In governed `--terminal none` mode it prepared fresh Claude implementer scripts and metadata, but `_maybe_launch_r…
- **`8c800411`** — Refresh external review snapshot for a12b6593
  - evolution: Fact: the narrow repo-owned `review-channel --action recover` path had one real remote-control gap left. In governed `--terminal none` mode it prepared fresh Claude implementer scripts and metadata, but `_maybe_launch_r…
- **`a12b6593`** — feat(review-channel): attach-remote-control action + typed attachment state
  - Adds the `review-channel --action attach-remote-control` action with a typed
  - RemoteControlAttachmentArtifact model and regression tests. Wires the typed
  - attachment registration through remote-bridge-loop.sh and
  - evolution: Fact: the narrow repo-owned `review-channel --action recover` path had one real remote-control gap left. In governed `--terminal none` mode it prepared fresh Claude implementer scripts and metadata, but `_maybe_launch_r…
- **`a5ad7fc0` | markers: F1** — fix(runtime): F1 coordination parity via review_state_override
  - Closes the F1 non-determinism finding from dev/active/remote_control_runtime.md:
  - `TestCoordinationParityF1::test_three_surfaces_report_identical_coordination`
  - was flaky because `build_startup_context()` reused one typed `review_state`
  - evolution: Fact: the narrow repo-owned `review-channel --action recover` path had one real remote-control gap left. In governed `--terminal none` mode it prepared fresh Claude implementer scripts and metadata, but `_maybe_launch_r…
- **`838b762c`** — Refresh external review snapshot for d7e7e597
  - evolution: Fact: the narrow repo-owned `review-channel --action recover` path had one real remote-control gap left. In governed `--terminal none` mode it prepared fresh Claude implementer scripts and metadata, but `_maybe_launch_r…
- **`d7e7e597`** — policy: declare operator_interaction_mode=remote_control
  - Adds repo_governance.bridge_config.operator_interaction_mode="remote_control"
  - to dev/config/devctl_repo_policy.json so the F4 fail-closed launcher
  - discipline permits headless bridge launches (--terminal none) from the
  - evolution: Fact: the narrow repo-owned `review-channel --action recover` path had one real remote-control gap left. In governed `--terminal none` mode it prepared fresh Claude implementer scripts and metadata, but `_maybe_launch_r…
- **`08770a66`** — Refresh external review snapshot for 675ca93d
  - evolution: Fact: the narrow repo-owned `review-channel --action recover` path had one real remote-control gap left. In governed `--terminal none` mode it prepared fresh Claude implementer scripts and metadata, but `_maybe_launch_r…
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
- checkpoint_allowed: worktree_dirty_within_budget

### Stale warnings
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

Projection produced by `devctl review-snapshot`. Generation stamp `snap-fadc5dd845f1` binds this file to HEAD `b5d609ce5e21`; if they drift, the freshness guard will fail CI. When the latest commit only refreshes this generated snapshot, the guard accepts this file as bound to that commit's parent code state.
