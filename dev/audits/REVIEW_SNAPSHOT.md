# VoiceTerm — Review Snapshot

> Deterministically generated from typed governance state. Do not edit by hand — rerun `devctl review-snapshot --write`.

## Quick status

- Branch: `feature/governance-quality-sweep`
- HEAD: `5e6879d250b5` — Refresh external review snapshot for d9774b64
- Tree hash: `762c33712558`
- Generation stamp: `snap-b47431f1148a`
- Generated at (UTC): 2026-04-10T04:50:23Z
- Push decision: `no_push_needed` — remote_publish_recorded_current_head
- Reviewer mode: `single_agent` (interaction: `remote_control`)
- Pipeline state: `n/a` (approval: `n/a`)
- Delta since last snapshot: 25 commits, 58 files, +7728/-1693
- Governance findings: 85 open / 70 fixed / 169 total
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
- HEAD SHA: `5e6879d250b506fd1b3d5671e3537053a7c7db6b`
- HEAD author: Justin Guida
- HEAD timestamp (UTC): 2026-04-10T00:35:23-04:00

## 2. Governance state

### Push decision
- action: `no_push_needed`
- reason: remote_publish_recorded_current_head
- push_eligible_now: False
- worktree_clean: True
- staged_path_count: 0
- unstaged_path_count: 0
- next_step_command: `n/a`
- latest_push_report: `dev/reports/push/latest.json`
- latest_push_report_state: `post_push_green` (push_completed)
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
- advisory: `no_push_needed` — clean_worktree

## 3. Delta — what changed since the previous snapshot

Range: last 25 commits ending at `5e6879d250b5`

- commits: 25
- files changed: 58
- insertions: +7728
- deletions: -1693
- bundle classes touched: tooling, docs
- risk add-ons triggered: Parser / ANSI boundary
- authority surfaces touched: 1 file(s)

### Commits

| # | SHA | Subject | Files | +/- | Bundle | Risk |
|---|---|---|---|---|---|---|
| 1 | `5e6879d2` | Refresh external review snapshot for d9774b64 | 1 | +56/-58 | tooling |  |
| 2 | `d9774b64` | docs(bridge): post-discovery sweep status — 48 new findings… | 2 | +97/-85 | docs |  |
| 3 | `fd30e634` | Refresh external review snapshot for 5375193c | 1 | +64/-57 | tooling |  |
| 4 | `5375193c` | fix(devctl): P1 stale refresh-authorization + P2 cursor-saf… | 12 | +328/-116 | tooling | Parser / ANSI boundary |
| 5 | `49217891` | Refresh external review snapshot for 24460777 | 1 | +68/-63 | tooling |  |
| 6 | `24460777` | feat(governance): guard promotion queue + pipeline auto-res… | 15 | +507/-93 | tooling |  |
| 7 | `ed2134b8` | Refresh external review snapshot for c3be08ff | 1 | +60/-59 | tooling |  |
| 8 | `c3be08ff` | docs(audits): guard promotion pipeline — issue-to-guard lea… | 3 | +216/-52 | tooling |  |
| 9 | `a325bdae` | Refresh external review snapshot for 304708c2 | 1 | +55/-58 | tooling |  |
| 10 | `304708c2` | fix(tests): prevent Qt offscreen segfault from accumulated… | 2 | +75/-56 | tooling |  |
| 11 | `c2685e4c` | Refresh external review snapshot for 54cf3225 | 1 | +52/-52 | tooling |  |
| 12 | `54cf3225` | Refresh external review snapshot for b5d609ce | 2 | +76/-87 | docs |  |
| 13 | `b5d609ce` | fix: keep poll status mode coherent | 3 | +117/-63 | tooling |  |
| 14 | `98cc9ab0` | fix: stabilize review-channel recovery | 13 | +843/-180 | tooling |  |
| 15 | `655db93a` | fix(discover): Q22 closure — repair KeyError crashes in --f… | 2 | +50/-42 | tooling |  |
| 16 | `8f4bf379` | docs(audits): log BL-032 through BL-035 from session 2026-0… | 2 | +173/-58 | tooling |  |
| 17 | `1864fc2c` | feat(devctl): BL-031 cross-mind polling — agent-mind command | 10 | +1513/-55 | tooling |  |
| 18 | `4129af6c` | docs(governance): Codex's doc updates for 2026-04-09 F1/F2/… | 7 | +403/-66 | tooling |  |
| 19 | `5985e70c` | feat(devctl): pipeline recovery command (BL-006) — typed re… | 12 | +1652/-46 | tooling |  |
| 20 | `49d1db53` | Refresh external review snapshot for 363fe42c | 1 | +57/-54 | tooling |  |
| 21 | `363fe42c` | fix(hygiene): Platform Boundary fix + regression tests + co… | 3 | +223/-47 | tooling |  |
| 22 | `e4870754` | fix(review-channel): attach-remote-control cleanup (F2.1 th… | 4 | +336/-70 | tooling |  |
| 23 | `d35abef0` | test(process-sweep): positive + negative regression tests f… | 2 | +195/-60 | tooling |  |
| 24 | `971647ec` | fix(rollout-tail): F3 narrow Claude session discovery + tai… | 4 | +351/-58 | tooling | Parser / ANSI boundary |
| 25 | `a65fc7c4` | fix(review): land F1+F2 from Codex reviewer pass | 5 | +161/-58 | tooling |  |

### Files

| Path | Bundle | +/- |
|---|---|---|
| `AGENTS.md` | docs | +25/-2 |
| `app/operator_console/tests/views/test_ui_layouts.py` | tooling | +24/-8 |
| `bridge.md` | docs | +67/-65 |
| `dev/active/MASTER_PLAN.md` | tooling | +43/-0 |
| `dev/active/ai_governance_platform.md` | tooling | +21/-0 |
| `dev/active/portable_code_governance.md` | tooling | +13/-0 |
| `dev/active/remote_commit_pipeline.md` | tooling | +19/-0 |
| `dev/active/remote_control_runtime.md` | tooling | +16/-0 |
| `dev/audits/2026-04-10-guard-promotion-pipeline.md` | tooling | +154/-0 |
| `dev/audits/REVIEW_SNAPSHOT.md` | tooling | +1452/-1445 |
| `dev/audits/TEST_BACKLOG.md` | tooling | +733/-0 |
| `dev/guides/DEVELOPMENT.md` | docs | +41/-1 |
| `dev/history/ENGINEERING_EVOLUTION.md` | tooling | +183/-1 |
| `dev/scripts/README.md` | tooling | +20/-4 |
| `dev/scripts/devctl/agent_mind_parser.py` | tooling | +75/-0 |
| `dev/scripts/devctl/cli.py` | tooling | +8/-0 |
| `dev/scripts/devctl/commands/agent_mind/__init__.py` | tooling | +27/-0 |
| `dev/scripts/devctl/commands/agent_mind/command.py` | tooling | +147/-1 |
| `dev/scripts/devctl/commands/agent_mind/projection.py` | tooling | +65/-0 |
| `dev/scripts/devctl/commands/agent_mind/renderers.py` | tooling | +110/-0 |
| `dev/scripts/devctl/commands/agent_mind/slice_builder.py` | tooling | +297/-0 |
| `dev/scripts/devctl/commands/check/process_sweep.py` | tooling | +31/-2 |
| `dev/scripts/devctl/commands/discover/__init__.py` | tooling | +9/-3 |
| `dev/scripts/devctl/commands/governance/hygiene_support.py` | tooling | +36/-4 |
| `dev/scripts/devctl/commands/governance/review.py` | tooling | +22/-0 |
| `dev/scripts/devctl/commands/governance/session_resume_support.py` | tooling | +2/-0 |
| `dev/scripts/devctl/commands/pipeline/__init__.py` | tooling | +28/-0 |
| `dev/scripts/devctl/commands/pipeline/abandon_action.py` | tooling | +165/-0 |
| `dev/scripts/devctl/commands/pipeline/command.py` | tooling | +39/-0 |
| `dev/scripts/devctl/commands/pipeline/recover_action.py` | tooling | +191/-0 |
| `dev/scripts/devctl/commands/pipeline/refresh_authorization_action.py` | tooling | +199/-1 |
| `dev/scripts/devctl/commands/pipeline/status_action.py` | tooling | +153/-0 |
| `dev/scripts/devctl/commands/pipeline/support.py` | tooling | +268/-0 |
| `dev/scripts/devctl/commands/review_channel/_attach_remote_control.py` | tooling | +23/-12 |
| `dev/scripts/devctl/commands/review_channel/_recover.py` | tooling | +69/-100 |
| `dev/scripts/devctl/commands/review_channel/_reviewer.py` | tooling | +49/-0 |
| `dev/scripts/devctl/commands/rollout_tail/discovery.py` | tooling | +31/-11 |
| `dev/scripts/devctl/commands/rollout_tail/parser.py` | tooling | +31/-6 |
| `dev/scripts/devctl/commands/vcs/commit.py` | tooling | +12/-2 |
| `dev/scripts/devctl/commands/vcs/push.py` | tooling | +4/-2 |
| _18 more files trimmed_ | | |

## 4. Quality signals

### Governance review
- total findings: 169
- open: 85
- fixed: 70
- false positives: 0

Recent findings:
- `subprocess_missing_timeout` — `dev/scripts/devctl/quality_backlog/collect.py` (n/a, verdict=`confirmed_issue`)
- `subprocess_missing_timeout` — `dev/scripts/devctl/security/python_scope.py` (n/a, verdict=`confirmed_issue`)
- `subprocess_missing_timeout` — `dev/scripts/devctl/security/codeql.py` (n/a, verdict=`confirmed_issue`)
- `subprocess_missing_timeout` — `dev/scripts/devctl/integrations/import_core.py` (n/a, verdict=`confirmed_issue`)
- `subprocess_missing_timeout` — `app/operator_console/launch_support.py` (n/a, verdict=`confirmed_issue`)
- `threading_shared_state_no_lock` — `dev/scripts/devctl/common.py` (n/a, verdict=`confirmed_issue`)
- `none_safety_chained_get_crash` — `dev/scripts/devctl/review_channel/bridge_projection_state.py` (n/a, verdict=`confirmed_issue`)
- `none_safety_chained_get_crash` — `app/operator_console/state/review/operator_decisions.py` (n/a, verdict=`confirmed_issue`)
- `none_safety_chained_get_crash` — `dev/scripts/devctl/autonomy/run_render.py` (n/a, verdict=`confirmed_issue`)
- `none_safety_chained_get_crash` — `dev/scripts/devctl/autonomy/report_helpers.py` (n/a, verdict=`confirmed_issue`)

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
- **authority_surface**: Typed authority surface touched (`dev/active/remote_commit_pipeline.md`) — Review contract-level invariants for this file

### Suggested verification commands

- `python3 dev/scripts/devctl.py check --profile ci`
- `python3 dev/scripts/devctl.py probe-report --format md`
- `python3 dev/scripts/devctl.py docs-check --strict-tooling`
- `python3 dev/scripts/devctl.py governance-review --format md`
- `python3 dev/scripts/devctl.py check-router --format md`

## 7. Reasoning — why these changes landed

### Per-commit rationale

- **`5e6879d2`** — Refresh external review snapshot for d9774b64
  - evolution: Fact: the dogfooded governed-push lane exposed a stale authorization bug after a completed push pipeline. A terminal `push_completed` same-branch `RemoteCommitPipelineContract` could still be selected by `devctl push` w…
- **`d9774b64`** — docs(bridge): post-discovery sweep status — 48 new findings, 6 probe candidates
  - Full gap scan across 7 categories: test cleanup, error handling,
  - subprocess timeouts, None safety, resource lifecycle, threading.
  - 169 total findings logged. Key direction for Codex: wire graph
  - evolution: Fact: the dogfooded governed-push lane exposed a stale authorization bug after a completed push pipeline. A terminal `push_completed` same-branch `RemoteCommitPipelineContract` could still be selected by `devctl push` w…
- **`fd30e634`** — Refresh external review snapshot for 5375193c
  - evolution: Fact: the dogfooded governed-push lane exposed a stale authorization bug after a completed push pipeline. A terminal `push_completed` same-branch `RemoteCommitPipelineContract` could still be selected by `devctl push` w…
- **`5375193c`** — fix(devctl): P1 stale refresh-authorization + P2 cursor-safe agent-mind polling
  - P1: refresh_authorization_action.py now refuses refresh when
  - authorized_head_sha no longer matches current HEAD, directing
  - the operator to recover instead of silently minting a stale
  - evolution: Fact: the dogfooded governed-push lane exposed a stale authorization bug after a completed push pipeline. A terminal `push_completed` same-branch `RemoteCommitPipelineContract` could still be selected by `devctl push` w…
- **`49217891`** — Refresh external review snapshot for 24460777
  - evolution: Fact: the narrow repo-owned `review-channel --action recover` path had one real remote-control gap left. In governed `--terminal none` mode it prepared fresh Claude implementer scripts and metadata, but `_maybe_launch_r…
- **`24460777`** — feat(governance): guard promotion queue + pipeline auto-reset
  - Auto-generated from push post-flight after audit doc landed:
  - evolution: Fact: the narrow repo-owned `review-channel --action recover` path had one real remote-control gap left. In governed `--terminal none` mode it prepared fresh Claude implementer scripts and metadata, but `_maybe_launch_r…
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

- open governance findings: 85

### Startup advisories
- no_push_needed: clean_worktree

### Stale warnings
- Move straight to the governed push path.

### Open gap rows
- **governance_open** (`dev/scripts/devctl/quality_backlog/collect.py`): subprocess_missing_timeout: 
- **governance_open** (`dev/scripts/devctl/security/python_scope.py`): subprocess_missing_timeout: 
- **governance_open** (`dev/scripts/devctl/security/codeql.py`): subprocess_missing_timeout: 
- **governance_open** (`dev/scripts/devctl/integrations/import_core.py`): subprocess_missing_timeout: 
- **governance_open** (`app/operator_console/launch_support.py`): subprocess_missing_timeout: 
- **governance_open** (`dev/scripts/devctl/common.py`): threading_shared_state_no_lock: 
- **governance_open** (`dev/scripts/devctl/review_channel/bridge_projection_state.py`): none_safety_chained_get_crash: 
- **governance_open** (`app/operator_console/state/review/operator_decisions.py`): none_safety_chained_get_crash: 

---

Projection produced by `devctl review-snapshot`. Generation stamp `snap-b47431f1148a` binds this file to HEAD `5e6879d250b5`; if they drift, the freshness guard will fail CI. When the latest commit only refreshes this generated snapshot, the guard accepts this file as bound to that commit's parent code state.
