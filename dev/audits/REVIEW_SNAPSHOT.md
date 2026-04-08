# VoiceTerm — Review Snapshot

> Deterministically generated from typed governance state. Do not edit by hand — rerun `devctl review-snapshot --write`.

## Quick status

- Branch: `feature/governance-quality-sweep`
- HEAD: `199291a506ab` — Refresh external review snapshot for 3bd849c
- Tree hash: `25ea7ac0a9d5`
- Generation stamp: `snap-81fd0f9b4f27`
- Generated at (UTC): 2026-04-08T18:54:00Z
- Push decision: `run_devctl_push` — push_preconditions_satisfied
- Reviewer mode: `single_agent` (interaction: `local_terminal`)
- Pipeline state: `n/a` (approval: `n/a`)
- Delta since last snapshot: 25 commits, 15 files, +3060/-1558
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
- HEAD SHA: `199291a506abe9b75bd1ed6736c41e25554c9002`
- HEAD author: Justin Guida
- HEAD timestamp (UTC): 2026-04-08T14:52:52-04:00

## 2. Governance state

### Push decision
- action: `run_devctl_push`
- reason: push_preconditions_satisfied
- push_eligible_now: True
- worktree_clean: True
- next_step_command: `python3 dev/scripts/devctl.py push --execute`
- latest_push_report: `dev/reports/push/latest.json`
- latest_push_report_state: `blocked` (validation_failed)
- current_push_authorization: `push-auth-20260407T220000Z-hardening-plan` (valid=False)
- authorized_head_commit: `ee13a6c6337f395afa574e99a4234f2eaf45a161`
- approved_target_identity: `tree-receipt-20260407T220000Z:281dea21851063411d2c43c2b4621a1c2a1168b5`
- publication_backlog: urgent
- publication_guidance: 16 local commit(s) waiting for governed push. Run `python3 dev/scripts/devctl.py push --execute` now.

### Reviewer runtime
- reviewer_mode: `single_agent`
- reviewer_freshness: unknown
- reviewer_publish_clear: True
- interaction_mode: `local_terminal`

### Remote commit pipeline
- state: `n/a`
- approval_state: `n/a`

### Work intake
- active plan: **Master Plan (Active, Unified)**
- plan path: `dev/active/MASTER_PLAN.md`
- active MP scope: all active MP execution state
- advisory: `push_allowed` — worktree_clean_and_review_accepted

## 3. Delta — what changed since the previous snapshot

Range: last 25 commits ending at `199291a506ab`

- commits: 25
- files changed: 15
- insertions: +3060
- deletions: -1558
- bundle classes touched: tooling, docs
- authority surfaces touched: 3 file(s)

### Commits

| # | SHA | Subject | Files | +/- | Bundle | Risk |
|---|---|---|---|---|---|---|
| 1 | `199291a` | Refresh external review snapshot for 3bd849c | 1 | +64/-51 | tooling |  |
| 2 | `3bd849c` | Land F1/F2/F3: unified review-state loader + packet labels… | 9 | +271/-201 | tooling |  |
| 3 | `9f9d8d7` | bridge + LIVE_RUN refresh: Codex F4 verdict + Q23/Q25/Q26/Q… | 3 | +197/-56 | tooling |  |
| 4 | `53d54b9` | LIVE_RUN: Q22-Q24 + capability discovery gap from devctl co… | 2 | +177/-42 | tooling |  |
| 5 | `003f117` | Bridge Action Request + LIVE_RUN retirement plan + enhancem… | 3 | +330/-63 | tooling |  |
| 6 | `3758302` | LIVE_RUN: acknowledge Codex F4 regression from Q4 tactical… | 2 | +77/-43 | tooling |  |
| 7 | `46c94dd` | Revert "Q4 tactical fix: flip BridgeConfig.operator_interac… | 2 | +65/-66 | tooling |  |
| 8 | `2a93f52` | Refresh external review snapshot for f54116e | 1 | +44/-41 | tooling |  |
| 9 | `f54116e` | bridge: point Claude Questions at LIVE_RUN.md; announce Q20… | 2 | +83/-79 | docs |  |
| 10 | `9a6dd2f` | LIVE_RUN: append Q18-Q20 findings discovered during push+re… | 2 | +152/-65 | tooling |  |
| 11 | `409e65e` | Refresh external review snapshot for e31232a | 1 | +44/-46 | tooling |  |
| 12 | `e31232a` | Refresh external review snapshot for 2602f22 | 1 | +56/-53 | tooling |  |
| 13 | `2602f22` | Add CHANGELOG entry for LIVE_RUN.md + log Q17 router misrou… | 3 | +113/-58 | tooling |  |
| 14 | `f58c69f` | Refresh external review snapshot for b6af0d3 | 1 | +44/-45 | tooling |  |
| 15 | `b6af0d3` | Refresh external review snapshot for 69719d3 | 1 | +55/-51 | tooling |  |
| 16 | `69719d3` | Add LIVE_RUN.md — running trial log of every issue found th… | 2 | +736/-50 | tooling |  |
| 17 | `e215663` | Refresh external review snapshot for f177aae | 1 | +69/-65 | tooling |  |
| 18 | `f177aae` | Q4 tactical fix: flip BridgeConfig.operator_interaction_mod… | 2 | +52/-46 | tooling |  |
| 19 | `ca59eaf` | Hotfix: defensive pending_approvals tolerates dict-shaped p… | 2 | +74/-55 | tooling |  |
| 20 | `f567eb1` | Refresh external review snapshot for d58eecb | 1 | +52/-49 | tooling |  |
| 21 | `d58eecb` | Expand Q4 root cause with file:line breadcrumbs for Codex f… | 2 | +51/-51 | docs |  |
| 22 | `00640d0` | Refresh external review snapshot for 6546c09 | 1 | +62/-64 | tooling |  |
| 23 | `6546c09` | Add Q4 remote_control interaction_mode classification bug t… | 2 | +45/-43 | docs |  |
| 24 | `5fe9148` | Refresh external review snapshot for 84f9140 | 1 | +64/-81 | tooling |  |
| 25 | `84f9140` | Clear stale path overrides and refresh bridge checkpoint | 3 | +83/-94 | tooling |  |

### Files

| Path | Bundle | +/- |
|---|---|---|
| `bridge.md` | docs | +88/-84 |
| `dev/CHANGELOG.md` | docs | +26/-0 |
| `dev/audits/LIVE_RUN.md` | tooling | +1375/-1 |
| `dev/audits/REVIEW_SNAPSHOT.md` | tooling | +1328/-1341 |
| `dev/scripts/checks/code_shape/code_shape_policy.py` | tooling | +0/-12 |
| `dev/scripts/devctl/commands/dashboard_render/attention.py` | tooling | +11/-2 |
| `dev/scripts/devctl/commands/governance/session_resume_support.py` | tooling | +8/-8 |
| `dev/scripts/devctl/commands/governance/startup_context.py` | tooling | +3/-0 |
| `dev/scripts/devctl/runtime/control_plane_read_model.py` | tooling | +12/-3 |
| `dev/scripts/devctl/runtime/control_plane_sources.py` | tooling | +31/-4 |
| `dev/scripts/devctl/runtime/project_governance_contract.py` | tooling | +2/-2 |
| `dev/scripts/devctl/runtime/review_state_models.py` | tooling | +19/-1 |
| `dev/scripts/devctl/runtime/startup_context.py` | tooling | +9/-99 |
| `dev/scripts/devctl/runtime/startup_context_projections.py` | tooling | +141/-0 |
| `dev/scripts/devctl/tests/test_dashboard.py` | tooling | +7/-1 |

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

- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/governance/startup_context.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/startup_context.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/project_governance_contract.py`) — Review contract-level invariants for this file
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/project_governance_contract.py`) — Commit 46c94dd changed dev/scripts/devctl/runtime/project_governance_contract.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/review_state_models.py`) — Commit ca59eaf changed dev/scripts/devctl/runtime/review_state_models.py

### Suggested verification commands

- `python3 dev/scripts/devctl.py check --profile ci`
- `python3 dev/scripts/devctl.py probe-report --format md`
- `python3 dev/scripts/devctl.py docs-check --strict-tooling`
- `python3 dev/scripts/devctl.py governance-review --format md`
- `python3 dev/scripts/devctl.py check-router --format md`

## 7. Reasoning — why these changes landed

### Per-commit rationale

- **`199291a`** — Refresh external review snapshot for 3bd849c
  - evolution: The next coordination follow-up was not another reducer. The reducer already existed and multiple rich surfaces already rendered it. The miss was load-bearing: the shared `ControlPlaneReadModel` still had no coordinatio…
- **`3bd849c` | MPs: MP-384, MP-385 | markers: F1, F2, F3** — Land F1/F2/F3: unified review-state loader + packet labels + ownership projection
  - This commit lands the F1/F2/F3 work that the Claude-CLI coder worked
  - on autonomously during the remote_control session while Codex was
  - polling as reviewer. The operator (remote) explicitly authorized this
  - evolution: The next coordination follow-up was not another reducer. The reducer already existed and multiple rich surfaces already rendered it. The miss was load-bearing: the shared `ControlPlaneReadModel` still had no coordinatio…
- **`9f9d8d7` | MPs: MP-380 | markers: F4** — bridge + LIVE_RUN refresh: Codex F4 verdict + Q23/Q25/Q26/Q27 appends
  - Bridge:
  - - Codex's latest poll at 18:26:17Z posted a new Current Verdict
  -   (`changes requested`) and added F4 as an Open Finding: the Q4
  - plan: `dev/active/remote_control_runtime.md`
  - evolution: The next coordination follow-up was not another reducer. The reducer already existed and multiple rich surfaces already rendered it. The miss was load-bearing: the shared `ControlPlaneReadModel` still had no coordinatio…
- **`53d54b9`** — LIVE_RUN: Q22-Q24 + capability discovery gap from devctl command exploration
  - Q22 — CRASH — devctl discover --format md crashes with KeyError('id') in
  - _render_category at line 254. The capability-discovery surface itself is
  - broken, which is probably why neither Codex nor Claude-Code found the
  - evolution: The next coordination follow-up was not another reducer. The reducer already existed and multiple rich surfaces already rendered it. The miss was load-bearing: the shared `ControlPlaneReadModel` still had no coordinatio…
- **`003f117`** — Bridge Action Request + LIVE_RUN retirement plan + enhancement proposals
  - Bridge:
  - - Action Request: re-scope Claude-CLI's instruction to include Q-series
  -   findings (it only sees F1/F2/F3 from its launch prompt; Q1-Q21 are
  - evolution: The next coordination follow-up was not another reducer. The reducer already existed and multiple rich surfaces already rendered it. The miss was load-bearing: the shared `ControlPlaneReadModel` still had no coordinatio…
- **`3758302` | MPs: MP-380 | markers: F4** — LIVE_RUN: acknowledge Codex F4 regression from Q4 tactical fix
  - Codex reviewed the session's tactical fixes at 18:26:17Z and raised
  - F4: the one-line BridgeConfig.operator_interaction_mode default flip
  - (commit f177aae) fixed this session's launch but broke the MP-380
  - plan: `dev/active/remote_control_runtime.md`
  - evolution: The next coordination follow-up was not another reducer. The reducer already existed and multiple rich surfaces already rendered it. The miss was load-bearing: the shared `ControlPlaneReadModel` still had no coordinatio…
- **`46c94dd`** — Revert "Q4 tactical fix: flip BridgeConfig.operator_interaction_mode default to remote_control"
  - This reverts commit f177aae4081fa638fb347c046570ad3bd0b58ef4.
  - evolution: The next coordination follow-up was not another reducer. The reducer already existed and multiple rich surfaces already rendered it. The miss was load-bearing: the shared `ControlPlaneReadModel` still had no coordinatio…
- **`2a93f52`** — Refresh external review snapshot for f54116e
  - evolution: The next coordination follow-up was not another reducer. The reducer already existed and multiple rich surfaces already rendered it. The miss was load-bearing: the shared `ControlPlaneReadModel` still had no coordinatio…
- **`f54116e`** — bridge: point Claude Questions at LIVE_RUN.md; announce Q20 packet transport break
  - Replaces the inline Q1-Q4 detail blocks with a single pointer to
  - dev/audits/LIVE_RUN.md (which now contains all 20 findings in full).
  - Frees ~3000 bytes of bridge budget and gives Codex a stable canonical
  - evolution: The next coordination follow-up was not another reducer. The reducer already existed and multiple rich surfaces already rendered it. The miss was load-bearing: the shared `ControlPlaneReadModel` still had no coordinatio…
- **`9a6dd2f`** — LIVE_RUN: append Q18-Q20 findings discovered during push+relaunch cycle
  - Q18 — BUG — docs-check in push-preflight vs standalone give different
  - results. Preflight reports `changelog_updated: False` on the exact same
  - tree where standalone reports `changelog_updated: True`. Same command,
  - evolution: The next coordination follow-up was not another reducer. The reducer already existed and multiple rich surfaces already rendered it. The miss was load-bearing: the shared `ControlPlaneReadModel` still had no coordinatio…
- **`409e65e`** — Refresh external review snapshot for e31232a
  - evolution: The next coordination follow-up was not another reducer. The reducer already existed and multiple rich surfaces already rendered it. The miss was load-bearing: the shared `ControlPlaneReadModel` still had no coordinatio…
- **`e31232a`** — Refresh external review snapshot for 2602f22
  - evolution: The next coordination follow-up was not another reducer. The reducer already existed and multiple rich surfaces already rendered it. The miss was load-bearing: the shared `ControlPlaneReadModel` still had no coordinatio…
- **`2602f22`** — Add CHANGELOG entry for LIVE_RUN.md + log Q17 router misrouting
  - - dev/CHANGELOG.md: Added section names LIVE_RUN.md; Fixed section names
  -   the three code landings (Q4 default, Q11 hotfix, stale overrides).
  -   This unblocks the Q17 docs-check --user-facing preflight that misrouted
  - evolution: The next coordination follow-up was not another reducer. The reducer already existed and multiple rich surfaces already rendered it. The miss was load-bearing: the shared `ControlPlaneReadModel` still had no coordinatio…
- **`f58c69f`** — Refresh external review snapshot for b6af0d3
  - evolution: The next coordination follow-up was not another reducer. The reducer already existed and multiple rich surfaces already rendered it. The miss was load-bearing: the shared `ControlPlaneReadModel` still had no coordinatio…
- **`b6af0d3`** — Refresh external review snapshot for 69719d3
  - evolution: The next coordination follow-up was not another reducer. The reducer already existed and multiple rich surfaces already rendered it. The miss was load-bearing: the shared `ControlPlaneReadModel` still had no coordinatio…
- **`69719d3`** — Add LIVE_RUN.md — running trial log of every issue found this session
  - Operator directive from remote_control session: log everything. Every
  - finding, every working component, every unknown or suspected blind spot.
  - Single authoritative file that Codex can pull from during review.
  - evolution: The next coordination follow-up was not another reducer. The reducer already existed and multiple rich surfaces already rendered it. The miss was load-bearing: the shared `ControlPlaneReadModel` still had no coordinatio…
- **`e215663`** — Refresh external review snapshot for f177aae
  - evolution: The next coordination follow-up was not another reducer. The reducer already existed and multiple rich surfaces already rendered it. The miss was load-bearing: the shared `ControlPlaneReadModel` still had no coordinatio…
- **`f177aae`** — Q4 tactical fix: flip BridgeConfig.operator_interaction_mode default to remote_control
  - One-line tactical unblock matching Q4 (rev_pkt_0129) fix recommendation #4.
  - This flips the hardcoded dataclass default in
  - project_governance_contract.py:209 from "local_terminal" to "remote_control"
  - evolution: The next coordination follow-up was not another reducer. The reducer already existed and multiple rich surfaces already rendered it. The miss was load-bearing: the shared `ControlPlaneReadModel` still had no coordinatio…
- **`ca59eaf`** — Hotfix: defensive pending_approvals tolerates dict-shaped packets
  - Q11 surfaced during this session: after posting 10 typed finding
  - packets (Q1-Q10, rev_pkt_0120..rev_pkt_0129) via review-channel post,
  - the next review-channel --action status call crashed with:
  - evolution: The next coordination follow-up was not another reducer. The reducer already existed and multiple rich surfaces already rendered it. The miss was load-bearing: the shared `ControlPlaneReadModel` still had no coordinatio…
- **`f567eb1`** — Refresh external review snapshot for d58eecb
  - evolution: The next coordination follow-up was not another reducer. The reducer already existed and multiple rich surfaces already rendered it. The miss was load-bearing: the shared `ControlPlaneReadModel` still had no coordinatio…
- **`d58eecb`** — Expand Q4 root cause with file:line breadcrumbs for Codex fix
  - Replaces the Q4 classification bug description with the full root
  - cause breadcrumb chain Codex needs to implement the fix:
  - evolution: The next coordination follow-up was not another reducer. The reducer already existed and multiple rich surfaces already rendered it. The miss was load-bearing: the shared `ControlPlaneReadModel` still had no coordinatio…
- **`00640d0`** — Refresh external review snapshot for 6546c09
  - evolution: The next coordination follow-up was not another reducer. The reducer already existed and multiple rich surfaces already rendered it. The miss was load-bearing: the shared `ControlPlaneReadModel` still had no coordinatio…
- **`6546c09`** — Add Q4 remote_control interaction_mode classification bug to bridge
  - Q4 (CLASSIFICATION): `startup-context.interaction_mode=local_terminal`
  - while this session is actually `remote_control` (operator on phone;
  - bridge "Remote Session Protocol" section declares it explicitly). The
  - evolution: The next coordination follow-up was not another reducer. The reducer already existed and multiple rich surfaces already rendered it. The miss was load-bearing: the shared `ControlPlaneReadModel` still had no coordinatio…
- **`5fe9148`** — Refresh external review snapshot for 84f9140
  - evolution: The next coordination follow-up was not another reducer. The reducer already existed and multiple rich surfaces already rendered it. The miss was load-bearing: the shared `ControlPlaneReadModel` still had no coordinatio…
- **`84f9140`** — Clear stale path overrides and refresh bridge checkpoint
  - Bundles two mutually dependent changes: `devctl commit` cannot land
  - either one in isolation because its pre-commit guard
  - (`startup-authority-contract-guard`) counts staged files as
  - evolution: The next coordination follow-up was not another reducer. The reducer already existed and multiple rich surfaces already rendered it. The miss was load-bearing: the shared `ControlPlaneReadModel` still had no coordinatio…
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
- push_allowed: worktree_clean_and_review_accepted

### Stale warnings
- Stop because nothing remains to push.

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

Projection produced by `devctl review-snapshot`. Generation stamp `snap-81fd0f9b4f27` binds this file to HEAD `199291a506ab`; if they drift, the freshness guard will fail CI. When the latest commit only refreshes this generated snapshot, the guard accepts this file as bound to that commit's parent code state.
