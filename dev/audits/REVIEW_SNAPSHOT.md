# VoiceTerm — Review Snapshot

> Deterministically generated from typed governance state. Do not edit by hand — rerun `devctl review-snapshot --write`.

## Quick status

- Branch: `feature/governance-quality-sweep`
- HEAD: `b426061d2111` — docs(audit): Q46 — governance only activates for dual-agent, not all modes
- Tree hash: `33aab1b91d1b`
- Generation stamp: `snap-909c23706cb4`
- Generated at (UTC): 2026-04-10T16:00:45Z
- Push decision: `await_checkpoint` — dirty_and_untracked_budget_exceeded
- Reviewer mode: `tools_only` (interaction: `remote_control`)
- Pipeline state: `n/a` (approval: `n/a`)
- Delta since last snapshot: 24 commits, 17 files, +2156/-1516
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
- HEAD SHA: `b426061d211132260625ee008c6ee418b04c5838`
- HEAD author: Justin Guida
- HEAD timestamp (UTC): 2026-04-10T11:53:51-04:00

## 2. Governance state

### Push decision
- action: `await_checkpoint`
- reason: dirty_and_untracked_budget_exceeded
- push_eligible_now: False
- worktree_clean: False
- staged_path_count: 1
- unstaged_path_count: 11
- next_step_command: `n/a`
- latest_push_report: `dev/reports/push/latest.json`
- latest_push_report_state: `blocked` (validation_failed)
- publication_backlog: urgent
- publication_guidance: 30 local commit(s) waiting for governed push once the current slice is checkpoint-clean.

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
- advisory: `checkpoint_before_continue` — dirty_and_untracked_budget_exceeded
- checkpoint_required: **yes**

## 3. Delta — what changed since the previous snapshot

Range: last 24 commits ending at `b426061d2111`

- commits: 24
- files changed: 17
- insertions: +2156
- deletions: -1516
- bundle classes touched: tooling, docs
- authority surfaces touched: 3 file(s)

### Commits

| # | SHA | Subject | Files | +/- | Bundle | Risk |
|---|---|---|---|---|---|---|
| 1 | `b426061d` | docs(audit): Q46 — governance only activates for dual-agent… | 2 | +82/-40 | tooling |  |
| 2 | `83ebf2d6` | docs(audit): Q45 — commit gate missing, evidence ≠ authority | 2 | +88/-56 | tooling |  |
| 3 | `79aab6c1` | docs(audit): Q44 — governed dashboard contradicts itself, m… | 2 | +75/-39 | tooling |  |
| 4 | `8a8d9b4f` | docs(audit): Q42-Q43 — destructive action from observer tel… | 2 | +134/-55 | tooling |  |
| 5 | `7eff1d9b` | docs(audit): Q39-Q41 — state-source drift, role violation,… | 2 | +162/-48 | tooling |  |
| 6 | `e0ef7aa2` | Refresh external review snapshot for 76f753d7 | 1 | +52/-55 | tooling |  |
| 7 | `76f753d7` | docs(audit): Q38 — control plane reasons from intended, not… | 3 | +107/-58 | tooling |  |
| 8 | `652b81d4` | Refresh external review snapshot for efcb2cd9 | 1 | +65/-61 | tooling |  |
| 9 | `efcb2cd9` | fix(audit): close Q37 supervisor-fallback gap + Codex revie… | 13 | +295/-108 | tooling |  |
| 10 | `4b36412c` | Refresh external review snapshot for 95b14712 | 1 | +49/-62 | tooling |  |
| 11 | `95b14712` | Document startup gate authority boundary | 7 | +94/-69 | tooling |  |
| 12 | `dff9cbb2` | Refresh external review snapshot for 8c2ac807 | 1 | +60/-71 | tooling |  |
| 13 | `8c2ac807` | chore: commit concurrent agent changes | 2 | +52/-79 | tooling |  |
| 14 | `8feab0b9` | fix(push): auto-commit runs even after preflight failure to… | 3 | +51/-94 | tooling |  |
| 15 | `f56664d2` | Refresh external review snapshot for 5b0a2d87 | 1 | +53/-49 | tooling |  |
| 16 | `5b0a2d87` | chore: surface refresh after push fix | 3 | +62/-64 | docs |  |
| 17 | `79475b97` | fix(push): auto-commit preflight-generated changes to break… | 3 | +120/-49 | tooling |  |
| 18 | `bd383199` | Refresh external review snapshot for 161f7ef0 | 1 | +53/-52 | tooling |  |
| 19 | `161f7ef0` | chore: push-generated code + surface refresh | 4 | +100/-73 | tooling |  |
| 20 | `bfc8dd3e` | Refresh external review snapshot for 0e2fcf0d | 1 | +51/-52 | tooling |  |
| 21 | `0e2fcf0d` | chore: push-generated surface refresh | 2 | +153/-86 | tooling |  |
| 22 | `4a33bd02` | fix(startup-gate): refined repair-launch bypass with checkp… | 2 | +91/-80 | tooling |  |
| 23 | `7fb42f8e` | Refresh external review snapshot for c3866e56 | 1 | +45/-55 | tooling |  |
| 24 | `c3866e56` | chore: bridge projection refresh | 2 | +62/-61 | docs |  |

### Files

| Path | Bundle | +/- |
|---|---|---|
| `AGENTS.md` | docs | +11/-4 |
| `bridge.md` | docs | +86/-53 |
| `dev/active/MASTER_PLAN.md` | tooling | +10/-3 |
| `dev/active/remote_commit_pipeline.md` | tooling | +18/-0 |
| `dev/audits/LIVE_RUN.md` | tooling | +417/-1 |
| `dev/audits/REVIEW_SNAPSHOT.md` | tooling | +1223/-1256 |
| `dev/guides/DEVELOPMENT.md` | docs | +12/-8 |
| `dev/history/ENGINEERING_EVOLUTION.md` | tooling | +38/-5 |
| `dev/scripts/README.md` | tooling | +8/-7 |
| `dev/scripts/devctl/commands/check/process_sweep.py` | tooling | +5/-21 |
| `dev/scripts/devctl/commands/process/audit.py` | tooling | +12/-1 |
| `dev/scripts/devctl/commands/vcs/push.py` | tooling | +3/-0 |
| `dev/scripts/devctl/commands/vcs/push_preflight_commit.py` | tooling | +66/-2 |
| `dev/scripts/devctl/runtime/startup_gate.py` | tooling | +52/-73 |
| `dev/scripts/devctl/tests/commands/process/test_process_audit.py` | tooling | +41/-0 |
| `dev/scripts/devctl/tests/process_sweep/test_process_sweep.py` | tooling | +11/-16 |
| `dev/scripts/devctl/tests/runtime/test_startup_gate.py` | tooling | +143/-66 |

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

- **`b426061d`** — docs(audit): Q46 — governance only activates for dual-agent, not all modes
  - The control plane (review authority, commit gates, topology checks)
  - was built from the dual-agent use case outward. Single-agent and
  - human-solo are treated as degraded states rather than first-class
  - evolution: Fact: the dogfooded governed-push lane exposed a stale authorization bug after a completed push pipeline. A terminal `push_completed` same-branch `RemoteCommitPipelineContract` could still be selected by `devctl push` w…
- **`83ebf2d6`** — docs(audit): Q45 — commit gate missing, evidence ≠ authority
  - Implementation evidence (tests pass, verdict exists, files changed)
  - was treated as commit permission while governed state said: blocked,
  - checkpoint required, reviewer overdue, no_live_agents. Documents
  - evolution: Fact: the dogfooded governed-push lane exposed a stale authorization bug after a completed push pipeline. A terminal `push_completed` same-branch `RemoteCommitPipelineContract` could still be selected by `devctl push` w…
- **`79aab6c1`** — docs(audit): Q44 — governed dashboard contradicts itself, misses live agents
  - Dashboard shows Active agents: 0 and Codex: NO SESSION while codex
  - exec PID 15617 is actively running. codex exec processes don't
  - register with the conductor session system. Also: Mode: Dual-agent
  - evolution: Fact: the dogfooded governed-push lane exposed a stale authorization bug after a completed push pipeline. A terminal `push_completed` same-branch `RemoteCommitPipelineContract` could still be selected by `devctl push` w…
- **`8a8d9b4f`** — docs(audit): Q42-Q43 — destructive action from observer telemetry, mode design gap
  - Q42: Agent killed a Codex process from observer heuristics (session
  - file stopped growing) without establishing canonical process topology.
  - Discovered multiple live sessions afterward. Documents the missing
  - evolution: Fact: the dogfooded governed-push lane exposed a stale authorization bug after a completed push pipeline. A terminal `push_completed` same-branch `RemoteCommitPipelineContract` could still be selected by `devctl push` w…
- **`7eff1d9b`** — docs(audit): Q39-Q41 — state-source drift, role violation, authority bypass
  - Three architectural findings from live testing of remote-control
  - multi-agent workflow:
  - evolution: Fact: the dogfooded governed-push lane exposed a stale authorization bug after a completed push pipeline. A terminal `push_completed` same-branch `RemoteCommitPipelineContract` could still be selected by `devctl push` w…
- **`e0ef7aa2`** — Refresh external review snapshot for 76f753d7
  - evolution: Fact: the dogfooded governed-push lane exposed a stale authorization bug after a completed push pipeline. A terminal `push_completed` same-branch `RemoteCommitPipelineContract` could still be selected by `devctl push` w…
- **`76f753d7`** — docs(audit): Q38 — control plane reasons from intended, not observed topology
  - Operator-identified architectural gap: the governance system detects
  - every individual blocker (reviewer overdue, dirty worktree, zero
  - supervised conductors) but fails to compose them into the governing
  - evolution: Fact: the dogfooded governed-push lane exposed a stale authorization bug after a completed push pipeline. A terminal `push_completed` same-branch `RemoteCommitPipelineContract` could still be selected by `devctl push` w…
- **`652b81d4`** — Refresh external review snapshot for efcb2cd9
  - evolution: Fact: the dogfooded governed-push lane exposed a stale authorization bug after a completed push pipeline. A terminal `push_completed` same-branch `RemoteCommitPipelineContract` could still be selected by `devctl push` w…
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
- checkpoint_before_continue: dirty_and_untracked_budget_exceeded

### Stale warnings
- Keep editing the current slice.
- Move straight to the governed push path.

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

Projection produced by `devctl review-snapshot`. Generation stamp `snap-909c23706cb4` binds this file to HEAD `b426061d2111`; if they drift, the freshness guard will fail CI. When the latest commit only refreshes this generated snapshot, the guard accepts this file as bound to that commit's parent code state.
