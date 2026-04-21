# VoiceTerm — Review Snapshot

> Deterministically generated from typed governance state. Do not edit by hand — rerun `devctl review-snapshot --write`.

## Quick status

- Branch: `feature/governance-quality-sweep`
- HEAD: `42fecac51340` — Refresh external review snapshot for db210b73
- Tree hash: `4655386f2a0f`
- Generation stamp: `snap-5fc15c1943bc`
- Generated at (UTC): 2026-04-21T23:45:15Z
- Push decision: `await_checkpoint` — dirty_path_budget_exceeded
- Reviewer mode: `single_agent` (interaction: `local_terminal`)
- Pipeline state: `n/a` (approval: `n/a`)
- Delta since last snapshot: 24 commits, 42 files, +4553/-1819
- Governance findings: 112 open / 86 fixed / 212 total
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
- HEAD SHA: `42fecac513408dd5be1b62a0212df7d12cf86bfd`
- HEAD author: Justin Guida
- HEAD timestamp (UTC): 2026-04-21T17:14:59-04:00

## 2. Governance state

### Push decision
- action: `await_checkpoint`
- reason: dirty_path_budget_exceeded
- push_eligible_now: False
- worktree_clean: False
- staged_path_count: 7
- unstaged_path_count: 5
- next_step_command: `n/a`
- latest_push_report: `dev/reports/push/latest.json`
- latest_push_report_state: `published_remote` (post_push_bundle_pending)
- current_push_authorization: `push-auth-20260421T211231876340Z` (valid=False)
- authorized_head_commit: `db210b738074fbbba29803db44bcdbe5f526f6f0`
- approved_target_identity: `tree-receipt-20260421T211231876340Z:09c5b028fa100556f3d2068c8fe6a2e543866c25`
- publication_backlog: none

### Reviewer runtime
- reviewer_mode: `single_agent`
- reviewer_freshness: unknown
- reviewer_publish_clear: True
- interaction_mode: `local_terminal`

### Remote commit pipeline
- state: `n/a`
- approval_state: `n/a`

### Work intake
- active plan: **AI Governance Platform Plan**
- plan path: `dev/active/ai_governance_platform.md`
- active MP scope: `MP-377`
- advisory: `checkpoint_before_continue` — dirty_path_budget_exceeded
- checkpoint_required: **yes**

## 3. Delta — what changed since the previous snapshot

Range: last 24 commits ending at `42fecac51340`

- commits: 24
- files changed: 42
- insertions: +4553
- deletions: -1819
- bundle classes touched: docs, tooling
- risk add-ons triggered: Parser / ANSI boundary
- authority surfaces touched: 7 file(s)

### Commits

| # | SHA | Subject | Files | +/- | Bundle | Risk |
|---|---|---|---|---|---|---|
| 1 | `42fecac5` | Refresh external review snapshot for db210b73 | 2 | +76/-68 | docs |  |
| 2 | `db210b73` | Add authority snapshot provenance | 18 | +592/-187 | tooling |  |
| 3 | `c2eecb29` | Refresh external review snapshot for 7dd94280 | 2 | +71/-65 | docs |  |
| 4 | `7dd94280` | Require post-push-green proof before projecting push_comple… | 11 | +220/-154 | tooling |  |
| 5 | `bc0a31f7` | Refresh external review snapshot for 3625ecbb | 2 | +50/-50 | docs |  |
| 6 | `3625ecbb` | Refresh external review snapshot for 211b6094 | 2 | +77/-81 | docs |  |
| 7 | `211b6094` | Keep event-backed review state authoritative | 10 | +187/-79 | tooling |  |
| 8 | `9f69c9d2` | Keep event-backed review state authoritative | 1 | +61/-63 | tooling |  |
| 9 | `39816b18` | Refresh external review snapshot for be738893 | 2 | +73/-79 | docs |  |
| 10 | `be738893` | Fix stall_diagnostics replacement-session precedence (rev_p… | 9 | +157/-68 | tooling |  |
| 11 | `227ca27e` | Refresh external review snapshot for dbd0b7e2 | 2 | +67/-70 | docs |  |
| 12 | `dbd0b7e2` | Close reviewer-wake auto-elevation gap and align stall diag… | 10 | +341/-54 | tooling |  |
| 13 | `99442e7f` | Refresh external review snapshot for 16c6f9ad | 2 | +73/-75 | docs |  |
| 14 | `16c6f9ad` | Unblock headless remote-control launches and add typed cond… | 15 | +1017/-68 | tooling | Parser / ANSI boundary |
| 15 | `25d420ad` | Refresh external review snapshot for 103a9871 | 2 | +75/-76 | docs |  |
| 16 | `103a9871` | Heal no-op push reruns back to push_completed | 8 | +200/-57 | tooling |  |
| 17 | `e72da77b` | Keep push pipeline state monotonic on no-op reruns | 4 | +337/-53 | tooling |  |
| 18 | `861d8bc4` | Refresh external review snapshot for d7fea144 | 2 | +60/-59 | docs |  |
| 19 | `d7fea144` | Refresh review-state cache and proof-tick parity | 6 | +370/-64 | tooling |  |
| 20 | `92dc15df` | Refresh external review snapshot for b1e8bfc9 | 2 | +61/-62 | docs |  |
| 21 | `b1e8bfc9` | Align phone bridge fallback with tools-only contract | 2 | +54/-52 | tooling |  |
| 22 | `a0c1e5f9` | Refresh external review snapshot for 1b671cfb | 2 | +60/-64 | docs |  |
| 23 | `1b671cfb` | Close event context seam and provenance guard gap | 5 | +206/-106 | tooling |  |
| 24 | `fb5030f3` | Refresh external review snapshot for 65fbf188 | 2 | +68/-65 | docs |  |

### Files

| Path | Bundle | +/- |
|---|---|---|
| `AGENTS.md` | docs | +16/-6 |
| `app/operator_console/tests/state/test_phone_status_snapshot.py` | tooling | +1/-1 |
| `bridge.md` | docs | +112/-112 |
| `dev/active/MASTER_PLAN.md` | tooling | +63/-5 |
| `dev/active/ai_governance_platform.md` | tooling | +19/-1 |
| `dev/audits/REVIEW_SNAPSHOT.md` | tooling | +1453/-1444 |
| `dev/guides/DEVELOPMENT.md` | docs | +54/-8 |
| `dev/history/ENGINEERING_EVOLUTION.md` | tooling | +270/-6 |
| `dev/scripts/README.md` | tooling | +21/-3 |
| `dev/scripts/checks/review_surface_consistency/command.py` | tooling | +12/-1 |
| `dev/scripts/checks/review_surface_consistency/snapshot_fields.py` | tooling | +33/-5 |
| `dev/scripts/devctl/approval_mode.py` | tooling | +29/-0 |
| `dev/scripts/devctl/commands/review_channel/_recover.py` | tooling | +5/-1 |
| `dev/scripts/devctl/commands/review_channel/bridge_action_support.py` | tooling | +5/-2 |
| `dev/scripts/devctl/commands/vcs/governed_executor_push_result.py` | tooling | +23/-19 |
| `dev/scripts/devctl/commands/vcs/push.py` | tooling | +10/-0 |
| `dev/scripts/devctl/commands/vcs/push_pipeline_state_sync.py` | tooling | +120/-0 |
| `dev/scripts/devctl/platform/coordination_snapshot.py` | tooling | +45/-7 |
| `dev/scripts/devctl/platform/coordination_snapshot_models.py` | tooling | +13/-3 |
| `dev/scripts/devctl/platform/surface_state_contract_rows.py` | tooling | +19/-0 |
| `dev/scripts/devctl/review_channel/event_projection_context.py` | tooling | +2/-2 |
| `dev/scripts/devctl/review_channel/parser.py` | tooling | +7/-5 |
| `dev/scripts/devctl/review_channel/prompt.py` | tooling | +14/-0 |
| `dev/scripts/devctl/review_channel/reviewer_follow_guard.py` | tooling | +22/-1 |
| `dev/scripts/devctl/review_channel/reviewer_runtime_publication.py` | tooling | +2/-8 |
| `dev/scripts/devctl/review_channel/stall_diagnostics.py` | tooling | +261/-9 |
| `dev/scripts/devctl/runtime/authority_snapshot_build.py` | tooling | +5/-7 |
| `dev/scripts/devctl/runtime/authority_snapshot_core.py` | tooling | +39/-61 |
| `dev/scripts/devctl/runtime/authority_snapshot_packet_target.py` | tooling | +43/-0 |
| `dev/scripts/devctl/runtime/authority_snapshot_provenance.py` | tooling | +60/-0 |
| `dev/scripts/devctl/runtime/review_state_contract_drift.py` | tooling | +113/-0 |
| `dev/scripts/devctl/runtime/review_state_locator.py` | tooling | +28/-12 |
| `dev/scripts/devctl/runtime/surface_provenance.py` | tooling | +103/-27 |
| `dev/scripts/devctl/tests/checks/test_check_review_surface_consistency.py` | tooling | +198/-9 |
| `dev/scripts/devctl/tests/platform/test_coordination_snapshot.py` | tooling | +79/-0 |
| `dev/scripts/devctl/tests/review_channel/test_context_injection.py` | tooling | +24/-27 |
| `dev/scripts/devctl/tests/review_channel/test_inbox_first_and_trusted_default.py` | tooling | +329/-0 |
| `dev/scripts/devctl/tests/review_channel/test_reviewer_runtime_doctor.py` | tooling | +51/-2 |
| `dev/scripts/devctl/tests/review_channel/test_stall_diagnostics.py` | tooling | +431/-0 |
| `dev/scripts/devctl/tests/runtime/test_review_state_locator.py` | tooling | +125/-10 |
| _2 more files trimmed_ | | |

## 4. Quality signals

### Governance review
- total findings: 212
- open: 112
- fixed: 86
- false positives: 0

Recent findings:
- `dogfood_finding_id_instability` — `dev/scripts/devctl/runtime/dogfood_log.py` (n/a, verdict=`confirmed_issue`)
- `dogfood_read_only_registration_missing` — `dev/scripts/devctl/cli_parser/entrypoint.py` (n/a, verdict=`confirmed_issue`)
- `finding_backlog_writer_closure_broken` — `dev/scripts/devctl/runtime/finding_backlog.py` (n/a, verdict=`confirmed_issue`)
- `dogfood_governance_pipeline_missing` — `dev/scripts/devctl/runtime/dogfood_log.py` (n/a, verdict=`confirmed_issue`)
- `bridge_authority_conflict` — `bridge.md` (n/a, verdict=`confirmed_issue`)
- `plan_markdown_projection_missing` — `dev/scripts/devctl/platform/planning_ir_models.py` (n/a, verdict=`confirmed_issue`)
- `plan_authority_gap` — `dev/active/MASTER_PLAN.md` (n/a, verdict=`confirmed_issue`)
- `bridge_metadata_parsed_as_authority` — `dev/scripts/devctl/review_channel/handoff.py` (n/a, verdict=`confirmed_issue`)
- `authority_snapshot_3_fields_missing` — `dev/scripts/devctl/runtime/startup_context.py` (n/a, verdict=`fixed`)
- `dogfood.command.startup-context` — `dev/scripts/devctl/commands/governance/startup_context.py` (n/a, verdict=`confirmed_issue`)

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
| `ActionResult` | `governance_runtime` | `n/a` | status, reason |
| `ArtifactStore` | `governance_runtime` | `n/a` | root, managed_kinds |
| `AutoModeState` | `governance_runtime` | `n/a` | phase, next_transition |
| `CallerAuthorityPolicy` | `governance_runtime` | `n/a` | caller_id, allowed_actions |
| `CheckResult` | `governance_runtime` | `n/a` | success, total |
| `ControlPlaneReadModel` | `governance_runtime` | `n/a` | push_eligible, top_blocker |
| `ControlState` | `governance_runtime` | `n/a` | approvals, active_runs |
| `CoordinationSnapshot` | `governance_core` | `n/a` | current_slice, recommended_topology |
| `DecisionPacket` | `governance_runtime` | `n/a` | decision_mode, rule_summary |
| `FailurePacket` | `governance_runtime` | `n/a` | runner, status |
| `Finding` | `governance_runtime` | `n/a` | check_id, severity |
| `LocalServiceEndpoint` | `governance_runtime` | `n/a` | service_id, discovery_fields |
| `ProviderAdapter` | `governance_adapters` | `n/a` | provider_id, capabilities |
| `PushAuthorizationRecord` | `governance_runtime` | `n/a` | authorization_id, authorized_head_sha |
| `RemoteCommitPipelineContract` | `governance_runtime` | `dev.scripts.devctl.runtime.remote_commit_pipeline_models:RemoteCommitPipelineContract` | snapshot_id, state |
| `RepoPack` | `repo_packs` | `n/a` | pack_id, policy_path |
| `ReviewCandidateRecord` | `governance_runtime` | `n/a` | candidate_id, artifact_kind |
| `ReviewState` | `governance_runtime` | `dev.scripts.devctl.runtime.review_state_models:ReviewState` | snapshot_id, bridge |
| `ReviewerRuntimeContract` | `governance_runtime` | `n/a` | reviewer_mode, reviewer_freshness |
| `RunRecord` | `governance_runtime` | `n/a` | run_id, status |
| `SessionCachePacket` | `governance_commands` | `n/a` | last_reviewed_sha, advisory_action |
| `TypedAction` | `governance_runtime` | `n/a` | action_id, repo_pack_id |
| `WorkflowAdapter` | `governance_adapters` | `n/a` | adapter_id, transport |

### Key documents

- `AGENTS.md`
- `dev/active/MASTER_PLAN.md`
- `dev/active/INDEX.md`
- `dev/guides/AI_GOVERNANCE_PLATFORM.md`

## 6. Reviewer hints — please verify

### Targeted hints

- **risk**: Parser / ANSI boundary — Delta touches a risk-sensitive surface; verify the routed bundle
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/runtime/test_startup_context.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_push_result.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/review_channel/reviewer_runtime_publication.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/review_channel/test_reviewer_runtime_doctor.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/review_channel/reviewer_follow_guard.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/review_channel/bridge_action_support.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/review_state_contract_drift.py`) — Review contract-level invariants for this file
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/platform/coordination_snapshot_models.py`) — Commit db210b73 changed dev/scripts/devctl/platform/coordination_snapshot_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/platform/surface_state_contract_rows.py`) — Commit db210b73 changed dev/scripts/devctl/platform/surface_state_contract_rows.py

### Suggested verification commands

- `python3 dev/scripts/devctl.py check --profile ci`
- `python3 dev/scripts/devctl.py probe-report --format md`
- `python3 dev/scripts/devctl.py docs-check --strict-tooling`
- `python3 dev/scripts/devctl.py governance-review --format md`
- `python3 dev/scripts/devctl.py check-router --format md`

## 7. Reasoning — why these changes landed

### Per-commit rationale

- **`42fecac5`** — Refresh external review snapshot for db210b73
  - evolution: Fact: `rev_pkt_1557` exposed a reviewer-mode drift loop in the transitional review-channel path. `reviewer-heartbeat --reviewer-mode single_agent` wrote the explicit bridge mode, but event-backed bridge liveness could d…
- **`db210b73`** — Add authority snapshot provenance
  - evolution: Fact: `rev_pkt_1557` exposed a reviewer-mode drift loop in the transitional review-channel path. `reviewer-heartbeat --reviewer-mode single_agent` wrote the explicit bridge mode, but event-backed bridge liveness could d…
- **`c2eecb29`** — Refresh external review snapshot for 7dd94280
  - evolution: Fact: `rev_pkt_1557` exposed a reviewer-mode drift loop in the transitional review-channel path. `reviewer-heartbeat --reviewer-mode single_agent` wrote the explicit bridge mode, but event-backed bridge liveness could d…
- **`7dd94280`** — Require post-push-green proof before projecting push_completed (rev_pkt_1502)
  - Close the heal-path regression codex self-identified earlier in this
  - sweep: `_push_report_completed` in `governed_executor_push_result.py`
  - was treating any `branch_already_pushed + published_remote=true` rerun
  - evolution: Fact: `rev_pkt_1557` exposed a reviewer-mode drift loop in the transitional review-channel path. `reviewer-heartbeat --reviewer-mode single_agent` wrote the explicit bridge mode, but event-backed bridge liveness could d…
- **`bc0a31f7`** — Refresh external review snapshot for 3625ecbb
  - evolution: Fact: `rev_pkt_1557` exposed a reviewer-mode drift loop in the transitional review-channel path. `reviewer-heartbeat --reviewer-mode single_agent` wrote the explicit bridge mode, but event-backed bridge liveness could d…
- **`3625ecbb`** — Refresh external review snapshot for 211b6094
  - evolution: Fact: `rev_pkt_1557` exposed a reviewer-mode drift loop in the transitional review-channel path. `reviewer-heartbeat --reviewer-mode single_agent` wrote the explicit bridge mode, but event-backed bridge liveness could d…
- **`211b6094`** — Keep event-backed review state authoritative
  - evolution: Fact: `rev_pkt_1557` exposed a reviewer-mode drift loop in the transitional review-channel path. `reviewer-heartbeat --reviewer-mode single_agent` wrote the explicit bridge mode, but event-backed bridge liveness could d…
- **`9f69c9d2`** — Keep event-backed review state authoritative
  - evolution: Fact: `rev_pkt_1557` exposed a reviewer-mode drift loop in the transitional review-channel path. `reviewer-heartbeat --reviewer-mode single_agent` wrote the explicit bridge mode, but event-backed bridge liveness could d…
- **`39816b18`** — Refresh external review snapshot for be738893
  - evolution: Fact: `rev_pkt_1557` exposed a reviewer-mode drift loop in the transitional review-channel path. `reviewer-heartbeat --reviewer-mode single_agent` wrote the explicit bridge mode, but event-backed bridge liveness could d…
- **`be738893`** — Fix stall_diagnostics replacement-session precedence (rev_pkt_1529)
  - The prior iteration removed the `and not task_complete_iso` gate on the
  - `escalation_deadlock` reason branch, but the check order stayed wrong:
  - the diagnostic reported `escalation_deadlock` before inspecting the
  - evolution: Fact: `rev_pkt_1557` exposed a reviewer-mode drift loop in the transitional review-channel path. `reviewer-heartbeat --reviewer-mode single_agent` wrote the explicit bridge mode, but event-backed bridge liveness could d…
- **`227ca27e`** — Refresh external review snapshot for dbd0b7e2
  - evolution: Superseded by the 2026-04-21 follow-up above. Fact: the first fix for the no-op governed-push regression only added a monotonic guard at pipeline persistence time. That prevented an already-green `push_completed` pipeli…
- **`dbd0b7e2`** — Close reviewer-wake auto-elevation gap and align stall diagnostics with real rollout shape
  - The 16c6f9ad batch covered launch / rollover / recover but the ensure-follow
  - reviewer-wake path in `reviewer_follow_guard.py::launch_waiting_reviewer_conductor`
  - still coerced the unset `--approval-mode` parser default to an empty string,
  - evolution: Superseded by the 2026-04-21 follow-up above. Fact: the first fix for the no-op governed-push regression only added a monotonic guard at pipeline persistence time. That prevented an already-green `push_completed` pipeli…
- **`99442e7f`** — Refresh external review snapshot for 16c6f9ad
  - evolution: Superseded by the 2026-04-21 follow-up above. Fact: the first fix for the no-op governed-push regression only added a monotonic guard at pipeline persistence time. That prevented an already-green `push_completed` pipeli…
- **`16c6f9ad`** — Unblock headless remote-control launches and add typed conductor stall diagnostics
  - Headless `--terminal none` review-channel launches in remote-control mode were
  - silently wedging on local sandbox-escalation prompts (e.g. ps/pgrep) that
  - never rendered. Auto-elevate `--approval-mode` to `trusted` for that case
  - evolution: Superseded by the 2026-04-21 follow-up above. Fact: the first fix for the no-op governed-push regression only added a monotonic guard at pipeline persistence time. That prevented an already-green `push_completed` pipeli…
- **`25d420ad`** — Refresh external review snapshot for 103a9871
  - evolution: Superseded by the 2026-04-21 follow-up above. Fact: the first fix for the no-op governed-push regression only added a monotonic guard at pipeline persistence time. That prevented an already-green `push_completed` pipeli…
- **`103a9871`** — Heal no-op push reruns back to push_completed
  - project_push_report() now promotes branch_already_pushed + published_remote
  - reports to push_completed even when post_push_green is absent in the no-op
  - report. Combined with the monotonic guard in sync_commit_pipeline_with_push_report
  - evolution: Superseded by the 2026-04-21 follow-up above. Fact: the first fix for the no-op governed-push regression only added a monotonic guard at pipeline persistence time. That prevented an already-green `push_completed` pipeli…
- **`e72da77b`** — Keep push pipeline state monotonic on no-op reruns
  - sync_commit_pipeline_with_push_report() previously downgraded a terminal
  - push_completed pipeline back to push_blocked whenever a no-op rerun on an
  - already-published head (reason=branch_already_pushed) was projected — because
  - evolution: Superseded by the 2026-04-21 follow-up above. Fact: the first fix for the no-op governed-push regression only added a monotonic guard at pipeline persistence time. That prevented an already-green `push_completed` pipeli…
- **`861d8bc4`** — Refresh external review snapshot for d7fea144
  - evolution: Superseded by the 2026-04-21 follow-up above. Fact: the first fix for the no-op governed-push regression only added a monotonic guard at pipeline persistence time. That prevented an already-green `push_completed` pipeli…
- **`d7fea144`** — Refresh review-state cache and proof-tick parity
  - evolution: Superseded by the 2026-04-21 follow-up above. Fact: the first fix for the no-op governed-push regression only added a monotonic guard at pipeline persistence time. That prevented an already-green `push_completed` pipeli…
- **`92dc15df`** — Refresh external review snapshot for b1e8bfc9
  - evolution: Superseded by the 2026-04-21 follow-up above. Fact: the first fix for the no-op governed-push regression only added a monotonic guard at pipeline persistence time. That prevented an already-green `push_completed` pipeli…
- **`b1e8bfc9`** — Align phone bridge fallback with tools-only contract
  - evolution: Superseded by the 2026-04-21 follow-up above. Fact: the first fix for the no-op governed-push regression only added a monotonic guard at pipeline persistence time. That prevented an already-green `push_completed` pipeli…
- **`a0c1e5f9`** — Refresh external review snapshot for 1b671cfb
  - evolution: Superseded by the 2026-04-21 follow-up above. Fact: the first fix for the no-op governed-push regression only added a monotonic guard at pipeline persistence time. That prevented an already-green `push_completed` pipeli…
- **`1b671cfb`** — Close event context seam and provenance guard gap
  - evolution: Superseded by the 2026-04-21 follow-up above. Fact: the first fix for the no-op governed-push regression only added a monotonic guard at pipeline persistence time. That prevented an already-green `push_completed` pipeli…
- **`fb5030f3`** — Refresh external review snapshot for 65fbf188
  - evolution: Superseded by the 2026-04-21 follow-up above. Fact: the first fix for the no-op governed-push regression only added a monotonic guard at pipeline persistence time. That prevented an already-green `push_completed` pipeli…
### Active MP scope (from MASTER_PLAN.md)

- contract slice for MP-355 plus the temporary markdown-swarm operating mode
- `dev/active/autonomous_governance_loop_v2.md` MP-377): headless
- `dev/active/review_probes.md` is the review-probe execution spec; implementation tasks stay in this file under `MP-368..MP-375`.
- companion under `MP-376`, not a second main product plan; implementation
- `dev/active/code_shape_expansion.md` is the research/calibration companion for future code-shape additions under `MP-378`; promotion into implementation still flows through `dev/active/review_probes.md` once Phase 5b ev…
- 2026-04-18 `MP-399` governed commit staged-index preservation in `MP-377`
- 2026-04-18 `MP-410` devctl root package-layout relief in `MP-377` scope:
- 2026-04-18 `MP-398` push preflight staged-index exclusion in `MP-377`
- 2026-04-18 `MP-388` consolidation archive pass in `MP-377` scope:
- 2026-04-18 `MP-389` semantic plan-loader core in `MP-377` scope:

## 8. Known gaps and open items

- open governance findings: 112

### Startup advisories
- checkpoint_before_continue: dirty_path_budget_exceeded

### Stale warnings
- Keep editing the current slice.
- Move straight to the governed push path.

### Open gap rows
- **governance_open** (`dev/scripts/devctl/runtime/dogfood_log.py`): dogfood_finding_id_instability: 
- **governance_open** (`dev/scripts/devctl/cli_parser/entrypoint.py`): dogfood_read_only_registration_missing: 
- **governance_open** (`dev/scripts/devctl/runtime/finding_backlog.py`): finding_backlog_writer_closure_broken: 
- **governance_open** (`dev/scripts/devctl/runtime/dogfood_log.py`): dogfood_governance_pipeline_missing: 
- **governance_open** (`bridge.md`): bridge_authority_conflict: 
- **governance_open** (`dev/scripts/devctl/platform/planning_ir_models.py`): plan_markdown_projection_missing: 
- **governance_open** (`dev/active/MASTER_PLAN.md`): plan_authority_gap: 
- **governance_open** (`dev/scripts/devctl/review_channel/handoff.py`): bridge_metadata_parsed_as_authority: 

---

Projection produced by `devctl review-snapshot`. Generation stamp `snap-5fc15c1943bc` binds this file to HEAD `42fecac51340`; if they drift, the freshness guard will fail CI. When the latest commit only refreshes this generated snapshot, the guard accepts this file as bound to that commit's parent code state.
