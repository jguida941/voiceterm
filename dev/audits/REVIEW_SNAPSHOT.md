# VoiceTerm — Review Snapshot

> Deterministically generated from typed governance state. Do not edit by hand — rerun `devctl review-snapshot --write`.

## Quick status

- Branch: `feature/governance-quality-sweep`
- HEAD: `7fb42f8e7742` — Refresh external review snapshot for c3866e56
- Tree hash: `735a8e82f2a4`
- Generation stamp: `snap-9692208bf5e0`
- Generated at (UTC): 2026-04-10T05:39:28Z
- Push decision: `await_checkpoint` — staged_index_present
- Reviewer mode: `active_dual_agent` (interaction: `remote_control`)
- Pipeline state: `n/a` (approval: `n/a`)
- Delta since last snapshot: 25 commits, 34 files, +3392/-1870
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
- HEAD SHA: `7fb42f8e77422279d3c7dd95412b75a54135dde1`
- HEAD author: Justin Guida
- HEAD timestamp (UTC): 2026-04-10T01:38:24-04:00

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
- publication_backlog: urgent
- publication_guidance: 8 local commit(s) waiting for governed push once the current slice is checkpoint-clean.

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
- advisory: `checkpoint_before_continue` — concurrent_writer_activity

## 3. Delta — what changed since the previous snapshot

Range: last 25 commits ending at `7fb42f8e7742`

- commits: 25
- files changed: 34
- insertions: +3392
- deletions: -1870
- bundle classes touched: tooling, docs
- risk add-ons triggered: Parser / ANSI boundary
- authority surfaces touched: 3 file(s)

### Commits

| # | SHA | Subject | Files | +/- | Bundle | Risk |
|---|---|---|---|---|---|---|
| 1 | `7fb42f8e` | Refresh external review snapshot for c3866e56 | 1 | +45/-55 | tooling |  |
| 2 | `c3866e56` | chore: bridge projection refresh | 2 | +62/-61 | docs |  |
| 3 | `28af7d69` | chore: post-push surface refresh | 3 | +90/-77 | tooling |  |
| 4 | `c06cf533` | Refresh external review snapshot for 2c1315eb | 1 | +56/-52 | tooling |  |
| 5 | `2c1315eb` | chore: render-surfaces refresh after startup-gate fix | 7 | +89/-66 | tooling |  |
| 6 | `f096b141` | fix(startup-gate): use receipt attribute access + regressio… | 4 | +108/-73 | tooling |  |
| 7 | `e3c56a53` | Refresh external review snapshot for 1696f8ee | 1 | +60/-54 | tooling |  |
| 8 | `1696f8ee` | fix(startup-gate): allow launch when action=repair_reviewer… | 3 | +97/-188 | tooling |  |
| 9 | `5687e3be` | Refresh external review snapshot for 4d3cf6ac | 1 | +59/-58 | tooling |  |
| 10 | `4d3cf6ac` | docs(bridge): graph infrastructure research — codeshape 70%… | 2 | +62/-65 | docs |  |
| 11 | `5e6879d2` | Refresh external review snapshot for d9774b64 | 1 | +56/-58 | tooling |  |
| 12 | `d9774b64` | docs(bridge): post-discovery sweep status — 48 new findings… | 2 | +97/-85 | docs |  |
| 13 | `fd30e634` | Refresh external review snapshot for 5375193c | 1 | +64/-57 | tooling |  |
| 14 | `5375193c` | fix(devctl): P1 stale refresh-authorization + P2 cursor-saf… | 12 | +328/-116 | tooling | Parser / ANSI boundary |
| 15 | `49217891` | Refresh external review snapshot for 24460777 | 1 | +68/-63 | tooling |  |
| 16 | `24460777` | feat(governance): guard promotion queue + pipeline auto-res… | 15 | +507/-93 | tooling |  |
| 17 | `ed2134b8` | Refresh external review snapshot for c3be08ff | 1 | +60/-59 | tooling |  |
| 18 | `c3be08ff` | docs(audits): guard promotion pipeline — issue-to-guard lea… | 3 | +216/-52 | tooling |  |
| 19 | `a325bdae` | Refresh external review snapshot for 304708c2 | 1 | +55/-58 | tooling |  |
| 20 | `304708c2` | fix(tests): prevent Qt offscreen segfault from accumulated… | 2 | +75/-56 | tooling |  |
| 21 | `c2685e4c` | Refresh external review snapshot for 54cf3225 | 1 | +52/-52 | tooling |  |
| 22 | `54cf3225` | Refresh external review snapshot for b5d609ce | 2 | +76/-87 | docs |  |
| 23 | `b5d609ce` | fix: keep poll status mode coherent | 3 | +117/-63 | tooling |  |
| 24 | `98cc9ab0` | fix: stabilize review-channel recovery | 13 | +843/-180 | tooling |  |
| 25 | `655db93a` | fix(discover): Q22 closure — repair KeyError crashes in --f… | 2 | +50/-42 | tooling |  |

### Files

| Path | Bundle | +/- |
|---|---|---|
| `AGENTS.md` | docs | +29/-3 |
| `app/operator_console/tests/views/test_ui_layouts.py` | tooling | +24/-8 |
| `bridge.md` | docs | +125/-234 |
| `dev/active/MASTER_PLAN.md` | tooling | +35/-0 |
| `dev/active/ai_governance_platform.md` | tooling | +25/-0 |
| `dev/active/portable_code_governance.md` | tooling | +13/-0 |
| `dev/active/remote_commit_pipeline.md` | tooling | +19/-0 |
| `dev/active/remote_control_runtime.md` | tooling | +16/-0 |
| `dev/audits/2026-04-10-guard-promotion-pipeline.md` | tooling | +154/-0 |
| `dev/audits/REVIEW_SNAPSHOT.md` | tooling | +1469/-1497 |
| `dev/audits/TEST_BACKLOG.md` | tooling | +332/-0 |
| `dev/guides/DEVELOPMENT.md` | docs | +34/-1 |
| `dev/history/ENGINEERING_EVOLUTION.md` | tooling | +129/-1 |
| `dev/scripts/README.md` | tooling | +20/-3 |
| `dev/scripts/devctl/commands/agent_mind/command.py` | tooling | +6/-1 |
| `dev/scripts/devctl/commands/discover/__init__.py` | tooling | +9/-3 |
| `dev/scripts/devctl/commands/governance/review.py` | tooling | +22/-0 |
| `dev/scripts/devctl/commands/governance/session_resume_support.py` | tooling | +2/-0 |
| `dev/scripts/devctl/commands/pipeline/refresh_authorization_action.py` | tooling | +26/-1 |
| `dev/scripts/devctl/commands/review_channel/_recover.py` | tooling | +69/-100 |
| `dev/scripts/devctl/commands/review_channel/_reviewer.py` | tooling | +49/-0 |
| `dev/scripts/devctl/commands/rollout_tail/parser.py` | tooling | +18/-4 |
| `dev/scripts/devctl/commands/vcs/push.py` | tooling | +4/-2 |
| `dev/scripts/devctl/governance/guard_promotion_queue.py` | tooling | +189/-0 |
| `dev/scripts/devctl/repo_packs/voiceterm.py` | tooling | +5/-0 |
| `dev/scripts/devctl/review_channel/poll_status.py` | tooling | +17/-4 |
| `dev/scripts/devctl/review_channel/recover_support.py` | tooling | +76/-0 |
| `dev/scripts/devctl/runtime/startup_gate.py` | tooling | +26/-4 |
| `dev/scripts/devctl/tests/commands/test_agent_mind_command.py` | tooling | +82/-0 |
| `dev/scripts/devctl/tests/commands/test_pipeline_command.py` | tooling | +54/-0 |
| `dev/scripts/devctl/tests/governance/test_governance_review.py` | tooling | +69/-2 |
| `dev/scripts/devctl/tests/review_channel/test_review_channel.py` | tooling | +170/-1 |
| `dev/scripts/devctl/tests/runtime/test_startup_gate.py` | tooling | +42/-1 |
| `dev/scripts/devctl/tests/vcs/test_push.py` | tooling | +33/-0 |

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
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/startup_gate.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/runtime/test_startup_gate.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/active/remote_commit_pipeline.md`) — Review contract-level invariants for this file

### Suggested verification commands

- `python3 dev/scripts/devctl.py check --profile ci`
- `python3 dev/scripts/devctl.py probe-report --format md`
- `python3 dev/scripts/devctl.py docs-check --strict-tooling`
- `python3 dev/scripts/devctl.py governance-review --format md`
- `python3 dev/scripts/devctl.py check-router --format md`

## 7. Reasoning — why these changes landed

### Per-commit rationale

- **`7fb42f8e`** — Refresh external review snapshot for c3866e56
  - evolution: Fact: the dogfooded governed-push lane exposed a stale authorization bug after a completed push pipeline. A terminal `push_completed` same-branch `RemoteCommitPipelineContract` could still be selected by `devctl push` w…
- **`c3866e56`** — chore: bridge projection refresh
  - evolution: Fact: the dogfooded governed-push lane exposed a stale authorization bug after a completed push pipeline. A terminal `push_completed` same-branch `RemoteCommitPipelineContract` could still be selected by `devctl push` w…
- **`28af7d69`** — chore: post-push surface refresh
  - evolution: Fact: the dogfooded governed-push lane exposed a stale authorization bug after a completed push pipeline. A terminal `push_completed` same-branch `RemoteCommitPipelineContract` could still be selected by `devctl push` w…
- **`c06cf533`** — Refresh external review snapshot for 2c1315eb
  - evolution: Fact: the dogfooded governed-push lane exposed a stale authorization bug after a completed push pipeline. A terminal `push_completed` same-branch `RemoteCommitPipelineContract` could still be selected by `devctl push` w…
- **`2c1315eb`** — chore: render-surfaces refresh after startup-gate fix
  - evolution: Fact: the dogfooded governed-push lane exposed a stale authorization bug after a completed push pipeline. A terminal `push_completed` same-branch `RemoteCommitPipelineContract` could still be selected by `devctl push` w…
- **`f096b141`** — fix(startup-gate): use receipt attribute access + regression tests
  - Operator fix: startup_gate._is_repair_launch() now uses
  - receipt.advisory_action attribute instead of dict .get(), and
  - narrows exception handling to FileNotFoundError + ValueError.
  - evolution: Fact: the dogfooded governed-push lane exposed a stale authorization bug after a completed push pipeline. A terminal `push_completed` same-branch `RemoteCommitPipelineContract` could still be selected by `devctl push` w…
- **`e3c56a53`** — Refresh external review snapshot for 1696f8ee
  - evolution: Fact: the dogfooded governed-push lane exposed a stale authorization bug after a completed push pipeline. A terminal `push_completed` same-branch `RemoteCommitPipelineContract` could still be selected by `devctl push` w…
- **`1696f8ee`** — fix(startup-gate): allow launch when action=repair_reviewer_loop
  - The startup gate was deadlocking: startup-context says
  - repair_reviewer_loop, but the gate blocks review-channel launch
  - because authority is red. Launch IS the repair — the gate must
  - evolution: Fact: the dogfooded governed-push lane exposed a stale authorization bug after a completed push pipeline. A terminal `push_completed` same-branch `RemoteCommitPipelineContract` could still be selected by `devctl push` w…
- **`5687e3be`** — Refresh external review snapshot for 4d3cf6ac
  - evolution: Fact: the dogfooded governed-push lane exposed a stale authorization bug after a completed push pipeline. A terminal `push_completed` same-branch `RemoteCommitPipelineContract` could still be selected by `devctl push` w…
- **`4d3cf6ac`** — docs(bridge): graph infrastructure research — codeshape 70% built, first probe slice designed
  - 3-agent research sweep: ZGraph is not a graph engine (prime
  - compression), ContextGraphSnapshot is the right foundation,
  - codeshape ingestor is 70% done (scoped to 9 files, needs
  - evolution: Fact: the dogfooded governed-push lane exposed a stale authorization bug after a completed push pipeline. A terminal `push_completed` same-branch `RemoteCommitPipelineContract` could still be selected by `devctl push` w…
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
- checkpoint_before_continue: concurrent_writer_activity

### Stale warnings
- Keep editing the current slice.

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

Projection produced by `devctl review-snapshot`. Generation stamp `snap-9692208bf5e0` binds this file to HEAD `7fb42f8e7742`; if they drift, the freshness guard will fail CI. When the latest commit only refreshes this generated snapshot, the guard accepts this file as bound to that commit's parent code state.
