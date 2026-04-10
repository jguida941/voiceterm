# VoiceTerm — Review Snapshot

> Deterministically generated from typed governance state. Do not edit by hand — rerun `devctl review-snapshot --write`.

## Quick status

- Branch: `feature/governance-quality-sweep`
- HEAD: `f3f9fb10e9af` — Refresh external review snapshot for c39f93e2
- Tree hash: `587b9d23a12c`
- Generation stamp: `snap-031d2cd587b0`
- Generated at (UTC): 2026-04-10T17:10:40Z
- Push decision: `await_checkpoint` — staged_index_present
- Reviewer mode: `single_agent` (interaction: `remote_control`)
- Pipeline state: `n/a` (approval: `n/a`)
- Delta since last snapshot: 24 commits, 33 files, +3363/-1462
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
- HEAD SHA: `f3f9fb10e9af405ae230fa8ef7e9c8cf2e8e2101`
- HEAD author: Justin Guida
- HEAD timestamp (UTC): 2026-04-10T13:01:21-04:00

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
- advisory: `checkpoint_allowed` — worktree_dirty_within_budget

## 3. Delta — what changed since the previous snapshot

Range: last 24 commits ending at `f3f9fb10e9af`

- commits: 24
- files changed: 33
- insertions: +3363
- deletions: -1462
- bundle classes touched: tooling, docs
- authority surfaces touched: 6 file(s)

### Commits

| # | SHA | Subject | Files | +/- | Bundle | Risk |
|---|---|---|---|---|---|---|
| 1 | `f3f9fb10` | Refresh external review snapshot for c39f93e2 | 1 | +66/-61 | tooling |  |
| 2 | `c39f93e2` | feat(governance): Q47+Q45+Q43 authority spine — action rout… | 12 | +680/-59 | tooling |  |
| 3 | `bc6363a6` | docs(audit): Q49-Q50 — publisher died silently, 100 unfixed… | 2 | +82/-50 | tooling |  |
| 4 | `20f7085f` | docs(audit): Q48 — system has all data but no composed arch… | 2 | +121/-75 | tooling |  |
| 5 | `2b93d6b4` | Refresh external review snapshot for a7477364 | 1 | +76/-60 | tooling |  |
| 6 | `a7477364` | feat(topology): Q38 observed_control_topology + implementat… | 19 | +653/-58 | tooling |  |
| 7 | `f99de6a3` | docs(audit): Q47 — agent reasons when repo can already comp… | 2 | +84/-42 | tooling |  |
| 8 | `b426061d` | docs(audit): Q46 — governance only activates for dual-agent… | 2 | +82/-40 | tooling |  |
| 9 | `83ebf2d6` | docs(audit): Q45 — commit gate missing, evidence ≠ authority | 2 | +88/-56 | tooling |  |
| 10 | `79aab6c1` | docs(audit): Q44 — governed dashboard contradicts itself, m… | 2 | +75/-39 | tooling |  |
| 11 | `8a8d9b4f` | docs(audit): Q42-Q43 — destructive action from observer tel… | 2 | +134/-55 | tooling |  |
| 12 | `7eff1d9b` | docs(audit): Q39-Q41 — state-source drift, role violation,… | 2 | +162/-48 | tooling |  |
| 13 | `e0ef7aa2` | Refresh external review snapshot for 76f753d7 | 1 | +52/-55 | tooling |  |
| 14 | `76f753d7` | docs(audit): Q38 — control plane reasons from intended, not… | 3 | +107/-58 | tooling |  |
| 15 | `652b81d4` | Refresh external review snapshot for efcb2cd9 | 1 | +65/-61 | tooling |  |
| 16 | `efcb2cd9` | fix(audit): close Q37 supervisor-fallback gap + Codex revie… | 13 | +295/-108 | tooling |  |
| 17 | `4b36412c` | Refresh external review snapshot for 95b14712 | 1 | +49/-62 | tooling |  |
| 18 | `95b14712` | Document startup gate authority boundary | 7 | +94/-69 | tooling |  |
| 19 | `dff9cbb2` | Refresh external review snapshot for 8c2ac807 | 1 | +60/-71 | tooling |  |
| 20 | `8c2ac807` | chore: commit concurrent agent changes | 2 | +52/-79 | tooling |  |
| 21 | `8feab0b9` | fix(push): auto-commit runs even after preflight failure to… | 3 | +51/-94 | tooling |  |
| 22 | `f56664d2` | Refresh external review snapshot for 5b0a2d87 | 1 | +53/-49 | tooling |  |
| 23 | `5b0a2d87` | chore: surface refresh after push fix | 3 | +62/-64 | docs |  |
| 24 | `79475b97` | fix(push): auto-commit preflight-generated changes to break… | 3 | +120/-49 | tooling |  |

### Files

| Path | Bundle | +/- |
|---|---|---|
| `AGENTS.md` | docs | +18/-5 |
| `bridge.md` | docs | +78/-45 |
| `dev/active/MASTER_PLAN.md` | tooling | +24/-3 |
| `dev/active/ai_governance_platform.md` | tooling | +29/-1 |
| `dev/active/platform_authority_loop.md` | tooling | +15/-1 |
| `dev/active/remote_commit_pipeline.md` | tooling | +18/-0 |
| `dev/audits/LIVE_RUN.md` | tooling | +532/-1 |
| `dev/audits/REVIEW_SNAPSHOT.md` | tooling | +1284/-1265 |
| `dev/guides/DEVELOPMENT.md` | docs | +23/-9 |
| `dev/history/ENGINEERING_EVOLUTION.md` | tooling | +80/-5 |
| `dev/scripts/README.md` | tooling | +24/-11 |
| `dev/scripts/devctl/commands/check/process_sweep.py` | tooling | +5/-21 |
| `dev/scripts/devctl/commands/governance/startup_context.py` | tooling | +40/-4 |
| `dev/scripts/devctl/commands/governance/startup_context_render.py` | tooling | +10/-0 |
| `dev/scripts/devctl/commands/process/audit.py` | tooling | +12/-1 |
| `dev/scripts/devctl/commands/vcs/commit.py` | tooling | +24/-0 |
| `dev/scripts/devctl/commands/vcs/push.py` | tooling | +3/-0 |
| `dev/scripts/devctl/commands/vcs/push_preflight_commit.py` | tooling | +66/-2 |
| `dev/scripts/devctl/review_channel/observed_topology.py` | tooling | +20/-0 |
| `dev/scripts/devctl/runtime/action_routing.py` | tooling | +189/-0 |
| `dev/scripts/devctl/runtime/commit_permission.py` | tooling | +168/-0 |
| `dev/scripts/devctl/runtime/control_topology.py` | tooling | +143/-0 |
| `dev/scripts/devctl/runtime/control_topology_bridge_counts.py` | tooling | +87/-0 |
| `dev/scripts/devctl/runtime/control_topology_numeric.py` | tooling | +29/-0 |
| `dev/scripts/devctl/runtime/control_topology_runtime_counts.py` | tooling | +78/-0 |
| `dev/scripts/devctl/runtime/startup_context.py` | tooling | +12/-0 |
| `dev/scripts/devctl/runtime/startup_gate.py` | tooling | +0/-33 |
| `dev/scripts/devctl/tests/commands/process/test_process_audit.py` | tooling | +41/-0 |
| `dev/scripts/devctl/tests/process_sweep/test_process_sweep.py` | tooling | +11/-16 |
| `dev/scripts/devctl/tests/review_channel/test_observed_topology.py` | tooling | +104/-0 |
| `dev/scripts/devctl/tests/runtime/test_startup_context.py` | tooling | +34/-0 |
| `dev/scripts/devctl/tests/runtime/test_startup_gate.py` | tooling | +8/-38 |
| `dev/scripts/devctl/tests/vcs/test_commit_gate.py` | tooling | +154/-1 |

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

- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/governance/startup_context.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/startup_context.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/runtime/test_startup_context.py`) — Review contract-level invariants for this file
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

- **`f3f9fb10`** — Refresh external review snapshot for c39f93e2
  - evolution: Fact: the Q37-Q47 live audit showed the same control-plane failure repeating: agents reasoned from partial status, inferred the next step, and then revised after the typed state contradicted that inference. The highest-…
- **`c39f93e2`** — feat(governance): Q47+Q45+Q43 authority spine — action routing, commit gate, agent lane
  - Codex implementation of the Q47/Q45/Q43 authority spine:
  - evolution: Fact: the Q37-Q47 live audit showed the same control-plane failure repeating: agents reasoned from partial status, inferred the next step, and then revised after the typed state contradicted that inference. The highest-…
- **`bc6363a6`** — docs(audit): Q49-Q50 — publisher died silently, 100 unfixed findings
  - Q49: Publisher daemon (207 snapshots, running since 12:58AM) stopped
  - without typed stop_reason or recovery action. Dashboard shows STOPPED
  - but no alert triggered. Same monitoring gap as Q42.
  - evolution: Fact: the Q37-Q47 live audit showed the same control-plane failure repeating: agents reasoned from partial status, inferred the next step, and then revised after the typed state contradicted that inference. The highest-…
- **`20f7085f`** — docs(audit): Q48 — system has all data but no composed architectural view
  - The context-graph (64K edges), probes (25), guards (64), typed state,
  - process topology, session traces, and plan docs all exist. But no
  - composition pass reads them together to derive architectural
  - evolution: Fact: the Q37-Q47 live audit showed the same control-plane failure repeating: agents reasoned from partial status, inferred the next step, and then revised after the typed state contradicted that inference. The highest-…
- **`2b93d6b4`** — Refresh external review snapshot for a7477364
  - evolution: Fact: the Q37-Q47 live audit showed the same control-plane failure repeating: agents reasoned from partial status, inferred the next step, and then revised after the typed state contradicted that inference. The highest-…
- **`a7477364`** — feat(topology): Q38 observed_control_topology + implementation_permission
  - Codex implementation of Q38 first slice: startup-context now derives
  - and emits observed_control_topology and implementation_permission
  - from live runtime evidence (supervised conductor count, bridge
  - evolution: Fact: the Q37-Q47 live audit showed the same control-plane failure repeating: agents reasoned from partial status, inferred the next step, and then revised after the typed state contradicted that inference. The highest-…
- **`f99de6a3`** — docs(audit): Q47 — agent reasons when repo can already compute next step
  - Synthesizes Q37-Q46: every failure came from the agent reasoning
  - about control flow that typed state already had enough information
  - to decide deterministically. The fix is not smarter agents — it is
  - evolution: Fact: the Q37-Q47 live audit showed the same control-plane failure repeating: agents reasoned from partial status, inferred the next step, and then revised after the typed state contradicted that inference. The highest-…
- **`b426061d`** — docs(audit): Q46 — governance only activates for dual-agent, not all modes
  - The control plane (review authority, commit gates, topology checks)
  - was built from the dual-agent use case outward. Single-agent and
  - human-solo are treated as degraded states rather than first-class
  - evolution: Fact: the Q37-Q47 live audit showed the same control-plane failure repeating: agents reasoned from partial status, inferred the next step, and then revised after the typed state contradicted that inference. The highest-…
- **`83ebf2d6`** — docs(audit): Q45 — commit gate missing, evidence ≠ authority
  - Implementation evidence (tests pass, verdict exists, files changed)
  - was treated as commit permission while governed state said: blocked,
  - checkpoint required, reviewer overdue, no_live_agents. Documents
  - evolution: Fact: the Q37-Q47 live audit showed the same control-plane failure repeating: agents reasoned from partial status, inferred the next step, and then revised after the typed state contradicted that inference. The highest-…
- **`79aab6c1`** — docs(audit): Q44 — governed dashboard contradicts itself, misses live agents
  - Dashboard shows Active agents: 0 and Codex: NO SESSION while codex
  - exec PID 15617 is actively running. codex exec processes don't
  - register with the conductor session system. Also: Mode: Dual-agent
  - evolution: Fact: the Q37-Q47 live audit showed the same control-plane failure repeating: agents reasoned from partial status, inferred the next step, and then revised after the typed state contradicted that inference. The highest-…
- **`8a8d9b4f`** — docs(audit): Q42-Q43 — destructive action from observer telemetry, mode design gap
  - Q42: Agent killed a Codex process from observer heuristics (session
  - file stopped growing) without establishing canonical process topology.
  - Discovered multiple live sessions afterward. Documents the missing
  - evolution: Fact: the Q37-Q47 live audit showed the same control-plane failure repeating: agents reasoned from partial status, inferred the next step, and then revised after the typed state contradicted that inference. The highest-…
- **`7eff1d9b`** — docs(audit): Q39-Q41 — state-source drift, role violation, authority bypass
  - Three architectural findings from live testing of remote-control
  - multi-agent workflow:
  - evolution: Fact: the Q37-Q47 live audit showed the same control-plane failure repeating: agents reasoned from partial status, inferred the next step, and then revised after the typed state contradicted that inference. The highest-…
- **`e0ef7aa2`** — Refresh external review snapshot for 76f753d7
  - evolution: Fact: the Q37-Q47 live audit showed the same control-plane failure repeating: agents reasoned from partial status, inferred the next step, and then revised after the typed state contradicted that inference. The highest-…
- **`76f753d7`** — docs(audit): Q38 — control plane reasons from intended, not observed topology
  - Operator-identified architectural gap: the governance system detects
  - every individual blocker (reviewer overdue, dirty worktree, zero
  - supervised conductors) but fails to compose them into the governing
  - evolution: Fact: the Q37-Q47 live audit showed the same control-plane failure repeating: agents reasoned from partial status, inferred the next step, and then revised after the typed state contradicted that inference. The highest-…
- **`652b81d4`** — Refresh external review snapshot for efcb2cd9
  - evolution: Fact: the Q37-Q47 live audit showed the same control-plane failure repeating: agents reasoned from partial status, inferred the next step, and then revised after the typed state contradicted that inference. The highest-…
- **`efcb2cd9`** — fix(audit): close Q37 supervisor-fallback gap + Codex review pass
  - Remove the blanket supervisor-backed fallback in
  - _protected_registered_conductor_pids that added ALL conductor-scoped
  - PIDs to the protected set when any supervisor heartbeat was running.
  - evolution: Fact: the Q37-Q47 live audit showed the same control-plane failure repeating: agents reasoned from partial status, inferred the next step, and then revised after the typed state contradicted that inference. The highest-…
- **`4b36412c`** — Refresh external review snapshot for 95b14712
  - evolution: Fact: the Q37-Q47 live audit showed the same control-plane failure repeating: agents reasoned from partial status, inferred the next step, and then revised after the typed state contradicted that inference. The highest-…
- **`95b14712`** — Document startup gate authority boundary
  - evolution: Fact: the Q37-Q47 live audit showed the same control-plane failure repeating: agents reasoned from partial status, inferred the next step, and then revised after the typed state contradicted that inference. The highest-…
- **`dff9cbb2`** — Refresh external review snapshot for 8c2ac807
  - evolution: Fact: the Q37-Q47 live audit showed the same control-plane failure repeating: agents reasoned from partial status, inferred the next step, and then revised after the typed state contradicted that inference. The highest-…
- **`8c2ac807`** — chore: commit concurrent agent changes
  - evolution: Fact: the Q37-Q47 live audit showed the same control-plane failure repeating: agents reasoned from partial status, inferred the next step, and then revised after the typed state contradicted that inference. The highest-…
- **`8feab0b9`** — fix(push): auto-commit runs even after preflight failure to break the loop
  - evolution: Fact: the Q37-Q47 live audit showed the same control-plane failure repeating: agents reasoned from partial status, inferred the next step, and then revised after the typed state contradicted that inference. The highest-…
- **`f56664d2`** — Refresh external review snapshot for 5b0a2d87
  - evolution: Fact: the Q37-Q47 live audit showed the same control-plane failure repeating: agents reasoned from partial status, inferred the next step, and then revised after the typed state contradicted that inference. The highest-…
- **`5b0a2d87`** — chore: surface refresh after push fix
  - evolution: Fact: the Q37-Q47 live audit showed the same control-plane failure repeating: agents reasoned from partial status, inferred the next step, and then revised after the typed state contradicted that inference. The highest-…
- **`79475b97`** — fix(push): auto-commit preflight-generated changes to break dirty-tree loop
  - The push pipeline runs check-router during preflight, which can
  - trigger render-surfaces and code generation passes that dirty the
  - worktree. The push then fails its own clean-tree check, creating
  - evolution: Fact: the Q37-Q47 live audit showed the same control-plane failure repeating: agents reasoned from partial status, inferred the next step, and then revised after the typed state contradicted that inference. The highest-…
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
- checkpoint_allowed: worktree_dirty_within_budget

### Stale warnings
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

Projection produced by `devctl review-snapshot`. Generation stamp `snap-031d2cd587b0` binds this file to HEAD `f3f9fb10e9af`; if they drift, the freshness guard will fail CI. When the latest commit only refreshes this generated snapshot, the guard accepts this file as bound to that commit's parent code state.
