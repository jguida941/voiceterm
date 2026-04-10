# VoiceTerm — Review Snapshot

> Deterministically generated from typed governance state. Do not edit by hand — rerun `devctl review-snapshot --write`.

## Quick status

- Branch: `feature/governance-quality-sweep`
- HEAD: `ed2134b8e034` — Refresh external review snapshot for c3be08ff
- Tree hash: `504d950f5551`
- Generation stamp: `snap-314d76d6051c`
- Generated at (UTC): 2026-04-10T03:38:56Z
- Push decision: `await_checkpoint` — staged_index_budget_exceeded
- Reviewer mode: `single_agent` (interaction: `remote_control`)
- Pipeline state: `n/a` (approval: `n/a`)
- Delta since last snapshot: 24 commits, 56 files, +7947/-1514
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
- HEAD SHA: `ed2134b8e034d54116ce69ce584a91adfffd9446`
- HEAD author: Justin Guida
- HEAD timestamp (UTC): 2026-04-09T22:31:49-04:00

## 2. Governance state

### Push decision
- action: `await_checkpoint`
- reason: staged_index_budget_exceeded
- push_eligible_now: False
- worktree_clean: False
- staged_path_count: 14
- unstaged_path_count: 0
- next_step_command: `n/a`
- latest_push_report: `dev/reports/push/latest.json`
- latest_push_report_state: `post_push_green` (push_completed)
- current_push_authorization: `push-auth-20260410T013026997488Z` (valid=False)
- authorized_head_commit: `b5d609ce5e212babe502a142472941a5e14b8105`
- approved_target_identity: `tree-receipt-20260410T013026997488Z:f06cd7445bc99ebd96c363dcd2e920a4c1d5ab6f`
- publication_backlog: none

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
- advisory: `checkpoint_before_continue` — staged_index_budget_exceeded
- checkpoint_required: **yes**

## 3. Delta — what changed since the previous snapshot

Range: last 24 commits ending at `ed2134b8e034`

- commits: 24
- files changed: 56
- insertions: +7947
- deletions: -1514
- bundle classes touched: tooling, docs
- risk add-ons triggered: Parser / ANSI boundary

### Commits

| # | SHA | Subject | Files | +/- | Bundle | Risk |
|---|---|---|---|---|---|---|
| 1 | `ed2134b8` | Refresh external review snapshot for c3be08ff | 1 | +60/-59 | tooling |  |
| 2 | `c3be08ff` | docs(audits): guard promotion pipeline — issue-to-guard lea… | 3 | +216/-52 | tooling |  |
| 3 | `a325bdae` | Refresh external review snapshot for 304708c2 | 1 | +55/-58 | tooling |  |
| 4 | `304708c2` | fix(tests): prevent Qt offscreen segfault from accumulated… | 2 | +75/-56 | tooling |  |
| 5 | `c2685e4c` | Refresh external review snapshot for 54cf3225 | 1 | +52/-52 | tooling |  |
| 6 | `54cf3225` | Refresh external review snapshot for b5d609ce | 2 | +76/-87 | docs |  |
| 7 | `b5d609ce` | fix: keep poll status mode coherent | 3 | +117/-63 | tooling |  |
| 8 | `98cc9ab0` | fix: stabilize review-channel recovery | 13 | +843/-180 | tooling |  |
| 9 | `655db93a` | fix(discover): Q22 closure — repair KeyError crashes in --f… | 2 | +50/-42 | tooling |  |
| 10 | `8f4bf379` | docs(audits): log BL-032 through BL-035 from session 2026-0… | 2 | +173/-58 | tooling |  |
| 11 | `1864fc2c` | feat(devctl): BL-031 cross-mind polling — agent-mind command | 10 | +1513/-55 | tooling |  |
| 12 | `4129af6c` | docs(governance): Codex's doc updates for 2026-04-09 F1/F2/… | 7 | +403/-66 | tooling |  |
| 13 | `5985e70c` | feat(devctl): pipeline recovery command (BL-006) — typed re… | 12 | +1652/-46 | tooling |  |
| 14 | `49d1db53` | Refresh external review snapshot for 363fe42c | 1 | +57/-54 | tooling |  |
| 15 | `363fe42c` | fix(hygiene): Platform Boundary fix + regression tests + co… | 3 | +223/-47 | tooling |  |
| 16 | `e4870754` | fix(review-channel): attach-remote-control cleanup (F2.1 th… | 4 | +336/-70 | tooling |  |
| 17 | `d35abef0` | test(process-sweep): positive + negative regression tests f… | 2 | +195/-60 | tooling |  |
| 18 | `971647ec` | fix(rollout-tail): F3 narrow Claude session discovery + tai… | 4 | +351/-58 | tooling | Parser / ANSI boundary |
| 19 | `a65fc7c4` | fix(review): land F1+F2 from Codex reviewer pass | 5 | +161/-58 | tooling |  |
| 20 | `adb266b5` | Refresh external review snapshot for d84b27fa | 1 | +60/-58 | tooling |  |
| 21 | `d84b27fa` | feat(lifecycle): add recoverable flag to ReviewerSupervisor… | 2 | +77/-86 | tooling |  |
| 22 | `8f42ea3f` | feat(devctl): rollout-tail MVP for Codex/Claude session JSO… | 11 | +1088/-49 | tooling | Parser / ANSI boundary |
| 23 | `2ca00812` | Refresh external review snapshot for 696f4772 | 1 | +52/-46 | tooling |  |
| 24 | `696f4772` | fix(hygiene): trust supervisor heartbeat for reparented con… | 2 | +62/-54 | tooling |  |

### Files

| Path | Bundle | +/- |
|---|---|---|
| `AGENTS.md` | docs | +13/-1 |
| `app/operator_console/tests/views/test_ui_layouts.py` | tooling | +24/-8 |
| `bridge.md` | docs | +31/-35 |
| `dev/active/MASTER_PLAN.md` | tooling | +28/-0 |
| `dev/active/remote_control_runtime.md` | tooling | +16/-0 |
| `dev/audits/2026-04-10-guard-promotion-pipeline.md` | tooling | +154/-0 |
| `dev/audits/REVIEW_SNAPSHOT.md` | tooling | +1322/-1308 |
| `dev/audits/TEST_BACKLOG.md` | tooling | +733/-0 |
| `dev/guides/DEVELOPMENT.md` | docs | +24/-1 |
| `dev/history/ENGINEERING_EVOLUTION.md` | tooling | +126/-0 |
| `dev/scripts/README.md` | tooling | +7/-2 |
| `dev/scripts/devctl/agent_mind_parser.py` | tooling | +75/-0 |
| `dev/scripts/devctl/cli.py` | tooling | +13/-0 |
| `dev/scripts/devctl/commands/agent_mind/__init__.py` | tooling | +27/-0 |
| `dev/scripts/devctl/commands/agent_mind/command.py` | tooling | +141/-0 |
| `dev/scripts/devctl/commands/agent_mind/projection.py` | tooling | +65/-0 |
| `dev/scripts/devctl/commands/agent_mind/renderers.py` | tooling | +110/-0 |
| `dev/scripts/devctl/commands/agent_mind/slice_builder.py` | tooling | +297/-0 |
| `dev/scripts/devctl/commands/check/process_sweep.py` | tooling | +31/-2 |
| `dev/scripts/devctl/commands/discover/__init__.py` | tooling | +9/-3 |
| `dev/scripts/devctl/commands/governance/hygiene_support.py` | tooling | +49/-5 |
| `dev/scripts/devctl/commands/governance/session_resume_support.py` | tooling | +2/-0 |
| `dev/scripts/devctl/commands/pipeline/__init__.py` | tooling | +28/-0 |
| `dev/scripts/devctl/commands/pipeline/abandon_action.py` | tooling | +165/-0 |
| `dev/scripts/devctl/commands/pipeline/command.py` | tooling | +39/-0 |
| `dev/scripts/devctl/commands/pipeline/recover_action.py` | tooling | +191/-0 |
| `dev/scripts/devctl/commands/pipeline/refresh_authorization_action.py` | tooling | +173/-0 |
| `dev/scripts/devctl/commands/pipeline/status_action.py` | tooling | +153/-0 |
| `dev/scripts/devctl/commands/pipeline/support.py` | tooling | +268/-0 |
| `dev/scripts/devctl/commands/review_channel/_attach_remote_control.py` | tooling | +23/-12 |
| `dev/scripts/devctl/commands/review_channel/_recover.py` | tooling | +69/-100 |
| `dev/scripts/devctl/commands/review_channel/_reviewer.py` | tooling | +49/-0 |
| `dev/scripts/devctl/commands/rollout_tail/__init__.py` | tooling | +37/-0 |
| `dev/scripts/devctl/commands/rollout_tail/command.py` | tooling | +70/-0 |
| `dev/scripts/devctl/commands/rollout_tail/constants.py` | tooling | +19/-0 |
| `dev/scripts/devctl/commands/rollout_tail/discovery.py` | tooling | +117/-11 |
| `dev/scripts/devctl/commands/rollout_tail/parser.py` | tooling | +242/-2 |
| `dev/scripts/devctl/commands/rollout_tail/renderers.py` | tooling | +94/-0 |
| `dev/scripts/devctl/commands/vcs/commit.py` | tooling | +12/-2 |
| `dev/scripts/devctl/pipeline_parser.py` | tooling | +80/-0 |
| _16 more files trimmed_ | | |

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

### Suggested verification commands

- `python3 dev/scripts/devctl.py check --profile ci`
- `python3 dev/scripts/devctl.py probe-report --format md`
- `python3 dev/scripts/devctl.py docs-check --strict-tooling`
- `python3 dev/scripts/devctl.py governance-review --format md`
- `python3 dev/scripts/devctl.py check-router --format md`

## 7. Reasoning — why these changes landed

### Per-commit rationale

- **`ed2134b8`** — Refresh external review snapshot for c3be08ff
  - evolution: Fact: the narrow repo-owned `review-channel --action recover` path had one real remote-control gap left. In governed `--terminal none` mode it prepared fresh Claude implementer scripts and metadata, but `_maybe_launch_r…
- **`c3be08ff`** — docs(audits): guard promotion pipeline — issue-to-guard learning loop design
  - Root-cause investigation of the Qt test segfault revealed 12 gap
  - categories in the guard/probe system. Designed a continuous
  - issue→evaluate→draft→validate→register pipeline that uses existing
  - evolution: Fact: the narrow repo-owned `review-channel --action recover` path had one real remote-control gap left. In governed `--terminal none` mode it prepared fresh Claude implementer scripts and metadata, but `_maybe_launch_r…
- **`a325bdae`** — Refresh external review snapshot for 304708c2
  - evolution: Fact: the narrow repo-owned `review-channel --action recover` path had one real remote-control gap left. In governed `--terminal none` mode it prepared fresh Claude implementer scripts and metadata, but `_maybe_launch_r…
- **`304708c2`** — fix(tests): prevent Qt offscreen segfault from accumulated unclosed windows
  - Add _WindowCleanupMixin to all 7 widget-creating test classes in
  - test_ui_layouts.py. Each test now closes top-level QMainWindow
  - instances after execution, preventing Qt platform state corruption
  - evolution: Fact: the narrow repo-owned `review-channel --action recover` path had one real remote-control gap left. In governed `--terminal none` mode it prepared fresh Claude implementer scripts and metadata, but `_maybe_launch_r…
- **`c2685e4c`** — Refresh external review snapshot for 54cf3225
  - evolution: Fact: the narrow repo-owned `review-channel --action recover` path had one real remote-control gap left. In governed `--terminal none` mode it prepared fresh Claude implementer scripts and metadata, but `_maybe_launch_r…
- **`54cf3225`** — Refresh external review snapshot for b5d609ce
  - evolution: Fact: the narrow repo-owned `review-channel --action recover` path had one real remote-control gap left. In governed `--terminal none` mode it prepared fresh Claude implementer scripts and metadata, but `_maybe_launch_r…
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
- checkpoint_before_continue: staged_index_budget_exceeded

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

Projection produced by `devctl review-snapshot`. Generation stamp `snap-314d76d6051c` binds this file to HEAD `ed2134b8e034`; if they drift, the freshness guard will fail CI. When the latest commit only refreshes this generated snapshot, the guard accepts this file as bound to that commit's parent code state.
