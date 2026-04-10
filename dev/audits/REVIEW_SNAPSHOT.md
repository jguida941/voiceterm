# VoiceTerm — Review Snapshot

> Deterministically generated from typed governance state. Do not edit by hand — rerun `devctl review-snapshot --write`.

## Quick status

- Branch: `feature/governance-quality-sweep`
- HEAD: `efcb2cd9525c` — fix(audit): close Q37 supervisor-fallback gap + Codex review pass
- Tree hash: `ec7d9627b98d`
- Generation stamp: `snap-caa78169a0c2`
- Generated at (UTC): 2026-04-10T14:24:05Z
- Push decision: `await_review` — reviewer_overdue
- Reviewer mode: `tools_only` (interaction: `remote_control`)
- Pipeline state: `n/a` (approval: `n/a`)
- Delta since last snapshot: 24 commits, 18 files, +2012/-1737
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
- HEAD SHA: `efcb2cd9525c3935b0b3bfe3a5ff449e3a0cee24`
- HEAD author: Justin Guida
- HEAD timestamp (UTC): 2026-04-10T10:23:46-04:00

## 2. Governance state

### Push decision
- action: `await_review`
- reason: reviewer_overdue
- push_eligible_now: False
- worktree_clean: True
- staged_path_count: 0
- unstaged_path_count: 0
- next_step_command: `python3 dev/scripts/devctl.py review-channel --action status --terminal none --format json`
- latest_push_report: `dev/reports/push/latest.json`
- latest_push_report_state: `published_remote` (post_push_bundle_pending)
- publication_backlog: urgent
- publication_guidance: 22 local commit(s) waiting for governed push once review is accepted.

### Reviewer runtime
- reviewer_mode: `tools_only`
- reviewer_freshness: unknown
- reviewer_publish_clear: False
- interaction_mode: `remote_control`
- implementation_blocked: yes — reviewer_overdue

### Remote commit pipeline
- state: `n/a`
- approval_state: `n/a`

### Work intake
- active plan: **Master Plan (Active, Unified)**
- plan path: `dev/active/MASTER_PLAN.md`
- active MP scope: all active MP execution state
- advisory: `repair_reviewer_loop` — reviewer_overdue

## 3. Delta — what changed since the previous snapshot

Range: last 24 commits ending at `efcb2cd9525c`

- commits: 24
- files changed: 18
- insertions: +2012
- deletions: -1737
- bundle classes touched: docs, tooling
- authority surfaces touched: 3 file(s)

### Commits

| # | SHA | Subject | Files | +/- | Bundle | Risk |
|---|---|---|---|---|---|---|
| 1 | `efcb2cd9` | fix(audit): close Q37 supervisor-fallback gap + Codex revie… | 13 | +295/-108 | tooling |  |
| 2 | `4b36412c` | Refresh external review snapshot for 95b14712 | 1 | +49/-62 | tooling |  |
| 3 | `95b14712` | Document startup gate authority boundary | 7 | +94/-69 | tooling |  |
| 4 | `dff9cbb2` | Refresh external review snapshot for 8c2ac807 | 1 | +60/-71 | tooling |  |
| 5 | `8c2ac807` | chore: commit concurrent agent changes | 2 | +52/-79 | tooling |  |
| 6 | `8feab0b9` | fix(push): auto-commit runs even after preflight failure to… | 3 | +51/-94 | tooling |  |
| 7 | `f56664d2` | Refresh external review snapshot for 5b0a2d87 | 1 | +53/-49 | tooling |  |
| 8 | `5b0a2d87` | chore: surface refresh after push fix | 3 | +62/-64 | docs |  |
| 9 | `79475b97` | fix(push): auto-commit preflight-generated changes to break… | 3 | +120/-49 | tooling |  |
| 10 | `bd383199` | Refresh external review snapshot for 161f7ef0 | 1 | +53/-52 | tooling |  |
| 11 | `161f7ef0` | chore: push-generated code + surface refresh | 4 | +100/-73 | tooling |  |
| 12 | `bfc8dd3e` | Refresh external review snapshot for 0e2fcf0d | 1 | +51/-52 | tooling |  |
| 13 | `0e2fcf0d` | chore: push-generated surface refresh | 2 | +153/-86 | tooling |  |
| 14 | `4a33bd02` | fix(startup-gate): refined repair-launch bypass with checkp… | 2 | +91/-80 | tooling |  |
| 15 | `7fb42f8e` | Refresh external review snapshot for c3866e56 | 1 | +45/-55 | tooling |  |
| 16 | `c3866e56` | chore: bridge projection refresh | 2 | +62/-61 | docs |  |
| 17 | `28af7d69` | chore: post-push surface refresh | 3 | +90/-77 | tooling |  |
| 18 | `c06cf533` | Refresh external review snapshot for 2c1315eb | 1 | +56/-52 | tooling |  |
| 19 | `2c1315eb` | chore: render-surfaces refresh after startup-gate fix | 7 | +89/-66 | tooling |  |
| 20 | `f096b141` | fix(startup-gate): use receipt attribute access + regressio… | 4 | +108/-73 | tooling |  |
| 21 | `e3c56a53` | Refresh external review snapshot for 1696f8ee | 1 | +60/-54 | tooling |  |
| 22 | `1696f8ee` | fix(startup-gate): allow launch when action=repair_reviewer… | 3 | +97/-188 | tooling |  |
| 23 | `5687e3be` | Refresh external review snapshot for 4d3cf6ac | 1 | +59/-58 | tooling |  |
| 24 | `4d3cf6ac` | docs(bridge): graph infrastructure research — codeshape 70%… | 2 | +62/-65 | docs |  |

### Files

| Path | Bundle | +/- |
|---|---|---|
| `AGENTS.md` | docs | +16/-5 |
| `bridge.md` | docs | +134/-210 |
| `dev/active/MASTER_PLAN.md` | tooling | +15/-3 |
| `dev/active/ai_governance_platform.md` | tooling | +4/-0 |
| `dev/active/remote_commit_pipeline.md` | tooling | +18/-0 |
| `dev/audits/LIVE_RUN.md` | tooling | +72/-1 |
| `dev/audits/REVIEW_SNAPSHOT.md` | tooling | +1265/-1314 |
| `dev/guides/DEVELOPMENT.md` | docs | +16/-8 |
| `dev/history/ENGINEERING_EVOLUTION.md` | tooling | +58/-5 |
| `dev/scripts/README.md` | tooling | +13/-7 |
| `dev/scripts/devctl/commands/check/process_sweep.py` | tooling | +5/-21 |
| `dev/scripts/devctl/commands/process/audit.py` | tooling | +12/-1 |
| `dev/scripts/devctl/commands/vcs/push.py` | tooling | +3/-0 |
| `dev/scripts/devctl/commands/vcs/push_preflight_commit.py` | tooling | +66/-2 |
| `dev/scripts/devctl/runtime/startup_gate.py` | tooling | +78/-77 |
| `dev/scripts/devctl/tests/commands/process/test_process_audit.py` | tooling | +41/-0 |
| `dev/scripts/devctl/tests/process_sweep/test_process_sweep.py` | tooling | +11/-16 |
| `dev/scripts/devctl/tests/runtime/test_startup_gate.py` | tooling | +185/-67 |

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

- **authority_surface**: Typed authority surface touched (`dev/active/remote_commit_pipeline.md`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/runtime/test_startup_gate.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/startup_gate.py`) — Review contract-level invariants for this file

### Suggested verification commands

- `python3 dev/scripts/devctl.py check --profile ci`
- `python3 dev/scripts/devctl.py probe-report --format md`
- `python3 dev/scripts/devctl.py docs-check --strict-tooling`
- `python3 dev/scripts/devctl.py governance-review --format md`
- `python3 dev/scripts/devctl.py check-router --format md`

## 7. Reasoning — why these changes landed

### Per-commit rationale

- **`efcb2cd9`** — fix(audit): close Q37 supervisor-fallback gap + Codex review pass
  - Remove the blanket supervisor-backed fallback in
  - _protected_registered_conductor_pids that added ALL conductor-scoped
  - PIDs to the protected set when any supervisor heartbeat was running.
  - evolution: Fact: the dogfooded governed-push lane exposed a stale authorization bug after a completed push pipeline. A terminal `push_completed` same-branch `RemoteCommitPipelineContract` could still be selected by `devctl push` w…
- **`4b36412c`** — Refresh external review snapshot for 95b14712
  - evolution: Fact: the dogfooded governed-push lane exposed a stale authorization bug after a completed push pipeline. A terminal `push_completed` same-branch `RemoteCommitPipelineContract` could still be selected by `devctl push` w…
- **`95b14712`** — Document startup gate authority boundary
  - evolution: Fact: the dogfooded governed-push lane exposed a stale authorization bug after a completed push pipeline. A terminal `push_completed` same-branch `RemoteCommitPipelineContract` could still be selected by `devctl push` w…
- **`dff9cbb2`** — Refresh external review snapshot for 8c2ac807
  - evolution: Fact: the dogfooded governed-push lane exposed a stale authorization bug after a completed push pipeline. A terminal `push_completed` same-branch `RemoteCommitPipelineContract` could still be selected by `devctl push` w…
- **`8c2ac807`** — chore: commit concurrent agent changes
  - evolution: Fact: the dogfooded governed-push lane exposed a stale authorization bug after a completed push pipeline. A terminal `push_completed` same-branch `RemoteCommitPipelineContract` could still be selected by `devctl push` w…
- **`8feab0b9`** — fix(push): auto-commit runs even after preflight failure to break the loop
  - evolution: Fact: the dogfooded governed-push lane exposed a stale authorization bug after a completed push pipeline. A terminal `push_completed` same-branch `RemoteCommitPipelineContract` could still be selected by `devctl push` w…
- **`f56664d2`** — Refresh external review snapshot for 5b0a2d87
  - evolution: Fact: the dogfooded governed-push lane exposed a stale authorization bug after a completed push pipeline. A terminal `push_completed` same-branch `RemoteCommitPipelineContract` could still be selected by `devctl push` w…
- **`5b0a2d87`** — chore: surface refresh after push fix
  - evolution: Fact: the dogfooded governed-push lane exposed a stale authorization bug after a completed push pipeline. A terminal `push_completed` same-branch `RemoteCommitPipelineContract` could still be selected by `devctl push` w…
- **`79475b97`** — fix(push): auto-commit preflight-generated changes to break dirty-tree loop
  - The push pipeline runs check-router during preflight, which can
  - trigger render-surfaces and code generation passes that dirty the
  - worktree. The push then fails its own clean-tree check, creating
  - evolution: Fact: the dogfooded governed-push lane exposed a stale authorization bug after a completed push pipeline. A terminal `push_completed` same-branch `RemoteCommitPipelineContract` could still be selected by `devctl push` w…
- **`bd383199`** — Refresh external review snapshot for 161f7ef0
  - evolution: Fact: the dogfooded governed-push lane exposed a stale authorization bug after a completed push pipeline. A terminal `push_completed` same-branch `RemoteCommitPipelineContract` could still be selected by `devctl push` w…
- **`161f7ef0`** — chore: push-generated code + surface refresh
  - evolution: Fact: the dogfooded governed-push lane exposed a stale authorization bug after a completed push pipeline. A terminal `push_completed` same-branch `RemoteCommitPipelineContract` could still be selected by `devctl push` w…
- **`bfc8dd3e`** — Refresh external review snapshot for 0e2fcf0d
  - evolution: Fact: the dogfooded governed-push lane exposed a stale authorization bug after a completed push pipeline. A terminal `push_completed` same-branch `RemoteCommitPipelineContract` could still be selected by `devctl push` w…
- **`0e2fcf0d`** — chore: push-generated surface refresh
  - evolution: Fact: the dogfooded governed-push lane exposed a stale authorization bug after a completed push pipeline. A terminal `push_completed` same-branch `RemoteCommitPipelineContract` could still be selected by `devctl push` w…
- **`4a33bd02`** — fix(startup-gate): refined repair-launch bypass with checkpoint guard
  - Auto-generated improvement: _is_repair_allowed() now lives inside
  - enforce_startup_gate() and bypasses receipt-staleness and
  - reviewer-loop authority blocks, but still respects checkpoint
  - evolution: Fact: the dogfooded governed-push lane exposed a stale authorization bug after a completed push pipeline. A terminal `push_completed` same-branch `RemoteCommitPipelineContract` could still be selected by `devctl push` w…
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
- repair_reviewer_loop: reviewer_overdue

### Stale warnings
- Cut a checkpoint before doing anything else.

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

Projection produced by `devctl review-snapshot`. Generation stamp `snap-caa78169a0c2` binds this file to HEAD `efcb2cd9525c`; if they drift, the freshness guard will fail CI. When the latest commit only refreshes this generated snapshot, the guard accepts this file as bound to that commit's parent code state.
