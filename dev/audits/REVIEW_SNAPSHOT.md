# VoiceTerm — Review Snapshot

> Deterministically generated from typed governance state. Do not edit by hand — rerun `devctl review-snapshot --write`.

## Quick status

- Branch: `feature/governance-quality-sweep`
- HEAD: `227ca27e1822` — Refresh external review snapshot for dbd0b7e2
- Tree hash: `07810c8e5e4f`
- Generation stamp: `snap-e9233ebb2d4e`
- Generated at (UTC): 2026-04-21T15:59:01Z
- Push decision: `await_checkpoint` — staged_index_present
- Reviewer mode: `single_agent` (interaction: `local_terminal`)
- Pipeline state: `n/a` (approval: `n/a`)
- Delta since last snapshot: 25 commits, 101 files, +7299/-2779
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
- HEAD SHA: `227ca27e18227199ef1097c840a65c470721410a`
- HEAD author: Justin Guida
- HEAD timestamp (UTC): 2026-04-20T21:11:02-04:00

## 2. Governance state

### Push decision
- action: `await_checkpoint`
- reason: staged_index_present
- push_eligible_now: False
- worktree_clean: False
- staged_path_count: 7
- unstaged_path_count: 0
- next_step_command: `n/a`
- latest_push_report: `dev/reports/push/latest.json`
- latest_push_report_state: `published_remote` (post_push_bundle_pending)
- current_push_authorization: `push-auth-20260420T125551238377Z` (valid=False)
- authorized_head_commit: `861d8bc43bf17bd6d13b1fe32172bca90ae9ef50`
- approved_target_identity: `tree-receipt-20260420T125551238377Z:b2c921400551a8a623c82114d4195b996afbed0b`
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
- advisory: `checkpoint_allowed` — worktree_dirty_within_budget

## 3. Delta — what changed since the previous snapshot

Range: last 25 commits ending at `227ca27e1822`

- commits: 25
- files changed: 101
- insertions: +7299
- deletions: -2779
- bundle classes touched: docs, tooling
- risk add-ons triggered: Parser / ANSI boundary
- authority surfaces touched: 10 file(s)

### Commits

| # | SHA | Subject | Files | +/- | Bundle | Risk |
|---|---|---|---|---|---|---|
| 1 | `227ca27e` | Refresh external review snapshot for dbd0b7e2 | 2 | +67/-70 | docs |  |
| 2 | `dbd0b7e2` | Close reviewer-wake auto-elevation gap and align stall diag… | 10 | +341/-54 | tooling |  |
| 3 | `99442e7f` | Refresh external review snapshot for 16c6f9ad | 2 | +73/-75 | docs |  |
| 4 | `16c6f9ad` | Unblock headless remote-control launches and add typed cond… | 15 | +1017/-68 | tooling | Parser / ANSI boundary |
| 5 | `25d420ad` | Refresh external review snapshot for 103a9871 | 2 | +75/-76 | docs |  |
| 6 | `103a9871` | Heal no-op push reruns back to push_completed | 8 | +200/-57 | tooling |  |
| 7 | `e72da77b` | Keep push pipeline state monotonic on no-op reruns | 4 | +337/-53 | tooling |  |
| 8 | `861d8bc4` | Refresh external review snapshot for d7fea144 | 2 | +60/-59 | docs |  |
| 9 | `d7fea144` | Refresh review-state cache and proof-tick parity | 6 | +370/-64 | tooling |  |
| 10 | `92dc15df` | Refresh external review snapshot for b1e8bfc9 | 2 | +61/-62 | docs |  |
| 11 | `b1e8bfc9` | Align phone bridge fallback with tools-only contract | 2 | +54/-52 | tooling |  |
| 12 | `a0c1e5f9` | Refresh external review snapshot for 1b671cfb | 2 | +60/-64 | docs |  |
| 13 | `1b671cfb` | Close event context seam and provenance guard gap | 5 | +206/-106 | tooling |  |
| 14 | `fb5030f3` | Refresh external review snapshot for 65fbf188 | 2 | +68/-65 | docs |  |
| 15 | `65fbf188` | Align bridge projection to effective reviewer mode | 5 | +143/-77 | tooling |  |
| 16 | `89807c69` | Refresh external review snapshot for e6fe5938 | 2 | +58/-59 | docs |  |
| 17 | `e6fe5938` | Guard projection helpers against world-building drift | 9 | +343/-179 | tooling |  |
| 18 | `99334c92` | Refresh external review snapshot for 7faed568 | 2 | +76/-71 | docs |  |
| 19 | `7faed568` | Propagate review-state provenance and zref parity | 29 | +1140/-551 | tooling |  |
| 20 | `b36d14e8` | Harden conductor hygiene and reviewer wake | 14 | +393/-185 | tooling |  |
| 21 | `54ec06d8` | Advance session-resume parity and conductor hygiene | 24 | +1302/-503 | tooling |  |
| 22 | `19bbe4f6` | Refresh external review snapshot for 066112fb | 2 | +74/-63 | docs |  |
| 23 | `066112fb` | Checkpoint session-resume parity and collaboration wake clo… | 14 | +657/-93 | tooling |  |
| 24 | `95131e80` | Refresh external review snapshot for 818e4692 | 2 | +53/-56 | docs |  |
| 25 | `818e4692` | Fix regression test per Codex rev_pkt_1403: assert real fie… | 1 | +71/-17 | tooling |  |

### Files

| Path | Bundle | +/- |
|---|---|---|
| `AGENTS.md` | docs | +6/-1 |
| `app/operator_console/tests/state/test_phone_status_snapshot.py` | tooling | +1/-1 |
| `bridge.md` | docs | +72/-77 |
| `dev/active/MASTER_PLAN.md` | tooling | +38/-4 |
| `dev/active/ai_governance_platform.md` | tooling | +24/-8 |
| `dev/audits/REVIEW_SNAPSHOT.md` | tooling | +1414/-1374 |
| `dev/config/quality_presets/voiceterm.json` | tooling | +15/-0 |
| `dev/guides/DEVELOPMENT.md` | docs | +28/-1 |
| `dev/history/ENGINEERING_EVOLUTION.md` | tooling | +153/-1 |
| `dev/scripts/README.md` | tooling | +32/-12 |
| `dev/scripts/checks/architecture_boundary/command.py` | tooling | +6/-31 |
| `dev/scripts/checks/architecture_boundary/imports.py` | tooling | +105/-0 |
| `dev/scripts/checks/review_surface_consistency/command.py` | tooling | +38/-70 |
| `dev/scripts/checks/review_surface_consistency/models.py` | tooling | +2/-0 |
| `dev/scripts/checks/review_surface_consistency/snapshot_fields.py` | tooling | +208/-5 |
| `dev/scripts/devctl/approval_mode.py` | tooling | +29/-0 |
| `dev/scripts/devctl/commands/check/process_sweep.py` | tooling | +49/-17 |
| `dev/scripts/devctl/commands/governance/hygiene_support.py` | tooling | +16/-16 |
| `dev/scripts/devctl/commands/governance/session_resume.py` | tooling | +13/-4 |
| `dev/scripts/devctl/commands/governance/session_resume_authority_payload.py` | tooling | +17/-5 |
| `dev/scripts/devctl/commands/governance/session_resume_packet.py` | tooling | +179/-0 |
| `dev/scripts/devctl/commands/governance/session_resume_render.py` | tooling | +77/-12 |
| `dev/scripts/devctl/commands/governance/session_resume_source_helpers.py` | tooling | +258/-0 |
| `dev/scripts/devctl/commands/governance/session_resume_support.py` | tooling | +164/-359 |
| `dev/scripts/devctl/commands/process/audit.py` | tooling | +4/-2 |
| `dev/scripts/devctl/commands/review_channel/_bridge_poll_support.py` | tooling | +2/-0 |
| `dev/scripts/devctl/commands/review_channel/_recover.py` | tooling | +5/-1 |
| `dev/scripts/devctl/commands/review_channel/bridge_action_support.py` | tooling | +5/-2 |
| `dev/scripts/devctl/commands/review_channel/reviewer_runtime_snapshot.py` | tooling | +97/-0 |
| `dev/scripts/devctl/commands/review_channel/status.py` | tooling | +3/-27 |
| `dev/scripts/devctl/commands/review_channel/status_runtime_projection.py` | tooling | +49/-0 |
| `dev/scripts/devctl/commands/review_channel_command/helpers.py` | tooling | +9/-0 |
| `dev/scripts/devctl/commands/vcs/governed_executor_push_result.py` | tooling | +20/-9 |
| `dev/scripts/devctl/commands/vcs/push.py` | tooling | +10/-0 |
| `dev/scripts/devctl/commands/vcs/push_pipeline_state_sync.py` | tooling | +120/-0 |
| `dev/scripts/devctl/context_graph/cache_adapter.py` | tooling | +81/-0 |
| `dev/scripts/devctl/platform/runtime_state_contract_rows_review.py` | tooling | +25/-0 |
| `dev/scripts/devctl/platform/surface_state_contract_rows.py` | tooling | +25/-0 |
| `dev/scripts/devctl/process_sweep/internals.py` | tooling | +2/-41 |
| `dev/scripts/devctl/review_channel/bridge_projection_metadata.py` | tooling | +14/-13 |
| _61 more files trimmed_ | | |

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
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/review_channel/reviewer_follow_guard.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/review_channel/bridge_action_support.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_push_result.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/review_state_contract_drift.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/review_channel/bridge_projection_metadata.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/review_channel/bridge_projection_sections.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/startup_context.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/runtime/test_startup_context.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/review_channel/reviewer_runtime_snapshot.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/review_channel/test_reviewer_runtime_doctor.py`) — Review contract-level invariants for this file
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/review_state_models.py`) — Commit 7faed568 changed dev/scripts/devctl/runtime/review_state_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/review_state_packet_models.py`) — Commit 7faed568 changed dev/scripts/devctl/runtime/review_state_packet_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/startup_push_models.py`) — Commit 7faed568 changed dev/scripts/devctl/runtime/startup_push_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/platform/surface_state_contract_rows.py`) — Commit 54ec06d8 changed dev/scripts/devctl/platform/surface_state_contract_rows.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/collaboration_wake_contract.py`) — Commit 54ec06d8 changed dev/scripts/devctl/runtime/collaboration_wake_contract.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/review_state_collaboration_models.py`) — Commit 066112fb changed dev/scripts/devctl/runtime/review_state_collaboration_models.py

### Suggested verification commands

- `python3 dev/scripts/devctl.py check --profile ci`
- `python3 dev/scripts/devctl.py probe-report --format md`
- `python3 dev/scripts/devctl.py docs-check --strict-tooling`
- `python3 dev/scripts/devctl.py governance-review --format md`
- `python3 dev/scripts/devctl.py check-router --format md`

## 7. Reasoning — why these changes landed

### Per-commit rationale

- **`227ca27e`** — Refresh external review snapshot for dbd0b7e2
  - evolution: Fact: the first fix for the no-op governed-push regression only added a monotonic guard at pipeline persistence time. That prevented an already-green `push_completed` pipeline from regressing on a rerun, but it still le…
- **`dbd0b7e2`** — Close reviewer-wake auto-elevation gap and align stall diagnostics with real rollout shape
  - The 16c6f9ad batch covered launch / rollover / recover but the ensure-follow
  - reviewer-wake path in `reviewer_follow_guard.py::launch_waiting_reviewer_conductor`
  - still coerced the unset `--approval-mode` parser default to an empty string,
  - evolution: Fact: the first fix for the no-op governed-push regression only added a monotonic guard at pipeline persistence time. That prevented an already-green `push_completed` pipeline from regressing on a rerun, but it still le…
- **`99442e7f`** — Refresh external review snapshot for 16c6f9ad
  - evolution: Fact: the first fix for the no-op governed-push regression only added a monotonic guard at pipeline persistence time. That prevented an already-green `push_completed` pipeline from regressing on a rerun, but it still le…
- **`16c6f9ad`** — Unblock headless remote-control launches and add typed conductor stall diagnostics
  - Headless `--terminal none` review-channel launches in remote-control mode were
  - silently wedging on local sandbox-escalation prompts (e.g. ps/pgrep) that
  - never rendered. Auto-elevate `--approval-mode` to `trusted` for that case
  - evolution: Fact: the first fix for the no-op governed-push regression only added a monotonic guard at pipeline persistence time. That prevented an already-green `push_completed` pipeline from regressing on a rerun, but it still le…
- **`25d420ad`** — Refresh external review snapshot for 103a9871
  - evolution: Fact: the first fix for the no-op governed-push regression only added a monotonic guard at pipeline persistence time. That prevented an already-green `push_completed` pipeline from regressing on a rerun, but it still le…
- **`103a9871`** — Heal no-op push reruns back to push_completed
  - project_push_report() now promotes branch_already_pushed + published_remote
  - reports to push_completed even when post_push_green is absent in the no-op
  - report. Combined with the monotonic guard in sync_commit_pipeline_with_push_report
  - evolution: Fact: the first fix for the no-op governed-push regression only added a monotonic guard at pipeline persistence time. That prevented an already-green `push_completed` pipeline from regressing on a rerun, but it still le…
- **`e72da77b`** — Keep push pipeline state monotonic on no-op reruns
  - sync_commit_pipeline_with_push_report() previously downgraded a terminal
  - push_completed pipeline back to push_blocked whenever a no-op rerun on an
  - already-published head (reason=branch_already_pushed) was projected — because
  - evolution: Fact: the first fix for the no-op governed-push regression only added a monotonic guard at pipeline persistence time. That prevented an already-green `push_completed` pipeline from regressing on a rerun, but it still le…
- **`861d8bc4`** — Refresh external review snapshot for d7fea144
  - evolution: Fact: the first fix for the no-op governed-push regression only added a monotonic guard at pipeline persistence time. That prevented an already-green `push_completed` pipeline from regressing on a rerun, but it still le…
- **`d7fea144`** — Refresh review-state cache and proof-tick parity
  - evolution: Fact: the first fix for the no-op governed-push regression only added a monotonic guard at pipeline persistence time. That prevented an already-green `push_completed` pipeline from regressing on a rerun, but it still le…
- **`92dc15df`** — Refresh external review snapshot for b1e8bfc9
  - evolution: Fact: the first fix for the no-op governed-push regression only added a monotonic guard at pipeline persistence time. That prevented an already-green `push_completed` pipeline from regressing on a rerun, but it still le…
- **`b1e8bfc9`** — Align phone bridge fallback with tools-only contract
  - evolution: Fact: the first fix for the no-op governed-push regression only added a monotonic guard at pipeline persistence time. That prevented an already-green `push_completed` pipeline from regressing on a rerun, but it still le…
- **`a0c1e5f9`** — Refresh external review snapshot for 1b671cfb
  - evolution: Fact: the first fix for the no-op governed-push regression only added a monotonic guard at pipeline persistence time. That prevented an already-green `push_completed` pipeline from regressing on a rerun, but it still le…
- **`1b671cfb`** — Close event context seam and provenance guard gap
  - evolution: Fact: the first fix for the no-op governed-push regression only added a monotonic guard at pipeline persistence time. That prevented an already-green `push_completed` pipeline from regressing on a rerun, but it still le…
- **`fb5030f3`** — Refresh external review snapshot for 65fbf188
  - evolution: Fact: the first fix for the no-op governed-push regression only added a monotonic guard at pipeline persistence time. That prevented an already-green `push_completed` pipeline from regressing on a rerun, but it still le…
- **`65fbf188`** — Align bridge projection to effective reviewer mode
  - evolution: Fact: the first fix for the no-op governed-push regression only added a monotonic guard at pipeline persistence time. That prevented an already-green `push_completed` pipeline from regressing on a rerun, but it still le…
- **`89807c69`** — Refresh external review snapshot for e6fe5938
  - evolution: Fact: the first fix for the no-op governed-push regression only added a monotonic guard at pipeline persistence time. That prevented an already-green `push_completed` pipeline from regressing on a rerun, but it still le…
- **`e6fe5938`** — Guard projection helpers against world-building drift
  - evolution: Fact: the first fix for the no-op governed-push regression only added a monotonic guard at pipeline persistence time. That prevented an already-green `push_completed` pipeline from regressing on a rerun, but it still le…
- **`99334c92`** — Refresh external review snapshot for 7faed568
  - evolution: Fact: the first fix for the no-op governed-push regression only added a monotonic guard at pipeline persistence time. That prevented an already-green `push_completed` pipeline from regressing on a rerun, but it still le…
- **`7faed568`** — Propagate review-state provenance and zref parity
  - evolution: Fact: the first fix for the no-op governed-push regression only added a monotonic guard at pipeline persistence time. That prevented an already-green `push_completed` pipeline from regressing on a rerun, but it still le…
- **`b36d14e8`** — Harden conductor hygiene and reviewer wake
  - evolution: Fact: the first fix for the no-op governed-push regression only added a monotonic guard at pipeline persistence time. That prevented an already-green `push_completed` pipeline from regressing on a rerun, but it still le…
- **`54ec06d8`** — Advance session-resume parity and conductor hygiene
  - evolution: Fact: the first fix for the no-op governed-push regression only added a monotonic guard at pipeline persistence time. That prevented an already-green `push_completed` pipeline from regressing on a rerun, but it still le…
- **`19bbe4f6`** — Refresh external review snapshot for 066112fb
  - evolution: Fact: the next live Codex+Claude remote-control pass exposed a narrower defect than "the heartbeat is stale." Event-backed packet posting already updated the typed queue immediately, but the actual reviewer wake lived o…
- **`066112fb`** — Checkpoint session-resume parity and collaboration wake closure
  - evolution: Fact: the next live Codex+Claude remote-control pass exposed a narrower defect than "the heartbeat is stale." Event-backed packet posting already updated the typed queue immediately, but the actual reviewer wake lived o…
- **`95131e80`** — Refresh external review snapshot for 818e4692
  - evolution: Fact: the next live Codex+Claude remote-control pass exposed a narrower defect than "the heartbeat is stale." Event-backed packet posting already updated the typed queue immediately, but the actual reviewer wake lived o…
- **`818e4692`** — Fix regression test per Codex rev_pkt_1403: assert real fields + exercise call sites
  - Codex rev_pkt_1403: my 02325c76 regression test was vacuous. It read
  - authority_snapshot['agent_lane']['permissions'] but AuthoritySnapshot.to_dict()
  - only emits actor_role/allowed_actions/blocked_actions. perms was always empty,
  - evolution: Fact: the next live Codex+Claude remote-control pass exposed a narrower defect than "the heartbeat is stale." Event-backed packet posting already updated the typed queue immediately, but the actual reviewer wake lived o…
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
- checkpoint_allowed: worktree_dirty_within_budget

### Stale warnings
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

Projection produced by `devctl review-snapshot`. Generation stamp `snap-e9233ebb2d4e` binds this file to HEAD `227ca27e1822`; if they drift, the freshness guard will fail CI. When the latest commit only refreshes this generated snapshot, the guard accepts this file as bound to that commit's parent code state.
