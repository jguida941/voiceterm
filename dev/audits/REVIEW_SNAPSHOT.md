# VoiceTerm — Review Snapshot

> Deterministically generated from typed governance state. Do not edit by hand — rerun `devctl review-snapshot --write`.

## Quick status

- Branch: `feature/governance-quality-sweep`
- HEAD: `1271a075877f` — Refresh external review snapshot for fc86c018
- Tree hash: `ca489ae1cccf`
- Generation stamp: `snap-4d4702e1a6f9`
- Generated at (UTC): 2026-04-15T17:50:21Z
- Push decision: `await_checkpoint` — staged_index_budget_exceeded
- Reviewer mode: `tools_only` (interaction: `remote_control`)
- Pipeline state: `n/a` (approval: `n/a`)
- Delta since last snapshot: 24 commits, 99 files, +8526/-3064
- Governance findings: 116 open / 82 fixed / 212 total
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
- HEAD SHA: `1271a075877f3c54e34521321b9a55eca501b4db`
- HEAD author: Justin Guida
- HEAD timestamp (UTC): 2026-04-14T21:51:48-04:00

## 2. Governance state

### Push decision
- action: `await_checkpoint`
- reason: staged_index_budget_exceeded
- push_eligible_now: False
- worktree_clean: False
- staged_path_count: 87
- unstaged_path_count: 0
- next_step_command: `python3 dev/scripts/devctl.py review-channel --action status --terminal none --format json`
- latest_push_report: `dev/reports/push/latest.json`
- latest_push_report_state: `published_remote` (post_push_bundle_pending)
- publication_backlog: none

### Reviewer runtime
- reviewer_mode: `tools_only`
- reviewer_freshness: unknown
- reviewer_publish_clear: False
- interaction_mode: `remote_control`
- implementation_blocked: yes — review_loop_relaunch_required

### Remote commit pipeline
- state: `n/a`
- approval_state: `n/a`

### Work intake
- active plan: **AI Governance Platform Plan**
- plan path: `dev/active/ai_governance_platform.md`
- active MP scope: `MP-377`
- advisory: `checkpoint_before_continue` — staged_index_budget_exceeded
- checkpoint_required: **yes**

## 3. Delta — what changed since the previous snapshot

Range: last 24 commits ending at `1271a075877f`

- commits: 24
- files changed: 99
- insertions: +8526
- deletions: -3064
- bundle classes touched: docs, tooling
- risk add-ons triggered: Parser / ANSI boundary
- authority surfaces touched: 15 file(s)

### Commits

| # | SHA | Subject | Files | +/- | Bundle | Risk |
|---|---|---|---|---|---|---|
| 1 | `1271a075` | Refresh external review snapshot for fc86c018 | 2 | +51/-47 | docs |  |
| 2 | `fc86c018` | Mark Q94 fixed in LIVE_RUN | 1 | +9/-1 | tooling |  |
| 3 | `9c63556a` | Refresh external review snapshot for 8d1c30a0 | 2 | +74/-82 | docs |  |
| 4 | `8d1c30a0` | Fail closed on stale dashboard daemon state | 5 | +304/-31 | tooling |  |
| 5 | `847adc03` | Refresh external review snapshot for 5daed3c2 | 1 | +54/-52 | tooling |  |
| 6 | `5daed3c2` | Delete redesign_research/ — operator: stop making MDs, use… | 5 | +0/-748 | tooling |  |
| 7 | `acac5ee0` | Refresh external review snapshot for f5dc6d5e | 1 | +62/-66 | tooling |  |
| 8 | `f5dc6d5e` | Push redesign research bundle for Codex (operator directive… | 5 | +748/-0 | tooling |  |
| 9 | `d3aafd01` | Refresh external review snapshot for 9b4f8fb2 | 2 | +86/-75 | docs |  |
| 10 | `9b4f8fb2` | Bulk push for Codex redesign: 3 worktree agent slices (Q100… | 12 | +741/-38 | tooling |  |
| 11 | `c6ef4054` | Refresh external review snapshot for 671dfff3 | 1 | +57/-57 | tooling |  |
| 12 | `671dfff3` | Append Q100 architectural finding (attention_revision lease… | 3 | +141/-96 | tooling |  |
| 13 | `b374610d` | Log Q100 architectural finding: commit pipeline self-invali… | 1 | +49/-44 | tooling |  |
| 14 | `64ad27ef` | Refresh external review snapshot for 08859553 + sync bridge… | 1 | +64/-93 | tooling |  |
| 15 | `08859553` | Extract canonical operator_interaction_mode reducer to oper… | 7 | +343/-189 | tooling |  |
| 16 | `951b86aa` | Propagate attachment-overrides-local_terminal promotion to… | 3 | +69/-19 | tooling |  |
| 17 | `dba730f7` | Wire reviewer-wake path + fix dashboard render keying + pen… | 14 | +769/-12 | tooling |  |
| 18 | `493b9d03` | Fix attachment override of operator_interaction_mode; rever… | 4 | +131/-60 | tooling |  |
| 19 | `60a8d1bd` | Refresh external review snapshot for 686a1283 | 1 | +61/-69 | tooling |  |
| 20 | `686a1283` | Align authority parity and review packet handling | 15 | +623/-157 | tooling | Parser / ANSI boundary |
| 21 | `6361080a` | Fix review-channel watch follow liveness | 16 | +1255/-183 | tooling |  |
| 22 | `3d78ef9f` | Refresh external review snapshot for 6fdde964 | 1 | +60/-69 | tooling |  |
| 23 | `6fdde964` | Align authority snapshots and dashboard headers | 28 | +996/-241 | tooling |  |
| 24 | `455a2c64` | Add authority snapshot runtime contract | 34 | +1779/-635 | tooling |  |

### Files

| Path | Bundle | +/- |
|---|---|---|
| `AGENTS.md` | docs | +3/-1 |
| `bridge.md` | docs | +61/-61 |
| `dev/active/MASTER_PLAN.md` | tooling | +18/-0 |
| `dev/active/ai_governance_platform.md` | tooling | +314/-6 |
| `dev/audits/LIVE_RUN.md` | tooling | +59/-1 |
| `dev/audits/REVIEW_SNAPSHOT.md` | tooling | +1026/-1086 |
| `dev/audits/redesign_research/00_codex_directive.md` | tooling | +55/-55 |
| `dev/audits/redesign_research/01_livelogs_findings.md` | tooling | +191/-191 |
| `dev/audits/redesign_research/02_plans_landscape.md` | tooling | +216/-216 |
| `dev/audits/redesign_research/03_debt_ledger.md` | tooling | +142/-142 |
| `dev/audits/redesign_research/04_today_postmortem.md` | tooling | +144/-144 |
| `dev/guides/DEVELOPMENT.md` | docs | +16/-0 |
| `dev/history/ENGINEERING_EVOLUTION.md` | tooling | +88/-1 |
| `dev/scripts/README.md` | tooling | +20/-9 |
| `dev/scripts/checks/code_shape/code_shape_policy.py` | tooling | +0/-6 |
| `dev/scripts/devctl/commands/dashboard.py` | tooling | +142/-149 |
| `dev/scripts/devctl/commands/dashboard_builders.py` | tooling | +4/-1 |
| `dev/scripts/devctl/commands/dashboard_header.py` | tooling | +69/-0 |
| `dev/scripts/devctl/commands/dashboard_health.py` | tooling | +119/-3 |
| `dev/scripts/devctl/commands/dashboard_render/markdown.py` | tooling | +6/-1 |
| `dev/scripts/devctl/commands/dashboard_render/terminal.py` | tooling | +6/-1 |
| `dev/scripts/devctl/commands/governance/common.py` | tooling | +6/-1 |
| `dev/scripts/devctl/commands/governance/review.py` | tooling | +2/-2 |
| `dev/scripts/devctl/commands/governance/review_snapshot.py` | tooling | +138/-18 |
| `dev/scripts/devctl/commands/governance/session_resume.py` | tooling | +1/-0 |
| `dev/scripts/devctl/commands/governance/session_resume_authority_payload.py` | tooling | +85/-0 |
| `dev/scripts/devctl/commands/governance/session_resume_support.py` | tooling | +154/-132 |
| `dev/scripts/devctl/commands/governance/startup_context.py` | tooling | +22/-15 |
| `dev/scripts/devctl/commands/governance/startup_context_summary.py` | tooling | +8/-94 |
| `dev/scripts/devctl/commands/reporting/dogfood_governance.py` | tooling | +3/-3 |
| `dev/scripts/devctl/commands/review_channel/_ensure_follow_runtime.py` | tooling | +42/-26 |
| `dev/scripts/devctl/commands/review_channel/_reviewer_supervisor_autostart.py` | tooling | +45/-24 |
| `dev/scripts/devctl/commands/review_channel/_wait_runtime_state.py` | tooling | +15/-3 |
| `dev/scripts/devctl/commands/review_channel/bridge_action_support.py` | tooling | +44/-26 |
| `dev/scripts/devctl/commands/review_channel/doctor_support.py` | tooling | +2/-0 |
| `dev/scripts/devctl/commands/review_channel/event_handler.py` | tooling | +41/-102 |
| `dev/scripts/devctl/commands/review_channel/reviewer_runtime_snapshot.py` | tooling | +21/-4 |
| `dev/scripts/devctl/commands/review_channel/status.py` | tooling | +12/-2 |
| `dev/scripts/devctl/commands/review_channel/watch_follow.py` | tooling | +85/-0 |
| `dev/scripts/devctl/commands/review_channel/watch_follow_frames.py` | tooling | +110/-0 |
| _59 more files trimmed_ | | |

## 4. Quality signals

### Governance review
- total findings: 212
- open: 116
- fixed: 82
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
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/governance/review_snapshot.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_commit_phase.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_commit_runtime.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_support.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/remote_commit_pipeline_models.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/runtime/test_review_snapshot.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/review_channel/bridge_action_support.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/review_channel/reviewer_follow_guard.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/startup_context.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/review_channel/reviewer_runtime_snapshot.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/review_channel/test_reviewer_runtime_doctor.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/governance/startup_context.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/startup_receipt.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/runtime/test_startup_context.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/runtime/test_startup_receipt.py`) — Review contract-level invariants for this file
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/remote_commit_pipeline_models.py`) — Commit 9b4f8fb2 changed dev/scripts/devctl/runtime/remote_commit_pipeline_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/platform/surface_state_contract_rows.py`) — Commit 455a2c64 changed dev/scripts/devctl/platform/surface_state_contract_rows.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/review_state_models.py`) — Commit 455a2c64 changed dev/scripts/devctl/runtime/review_state_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/tests/platform/test_platform_contracts.py`) — Commit 455a2c64 changed dev/scripts/devctl/tests/platform/test_platform_contracts.py

### Suggested verification commands

- `python3 dev/scripts/devctl.py check --profile ci`
- `python3 dev/scripts/devctl.py probe-report --format md`
- `python3 dev/scripts/devctl.py docs-check --strict-tooling`
- `python3 dev/scripts/devctl.py governance-review --format md`
- `python3 dev/scripts/devctl.py check-router --format md`

## 7. Reasoning — why these changes landed

### Per-commit rationale

- **`1271a075`** — Refresh external review snapshot for fc86c018
  - evolution: Fact: the remote-control review loop still had three small but real projection gaps. `ControlPlaneReadModel.pending_action_requests` counted every live pending packet even though the field name promised action requests …
- **`fc86c018`** — Mark Q94 fixed in LIVE_RUN
  - evolution: Fact: the remote-control review loop still had three small but real projection gaps. `ControlPlaneReadModel.pending_action_requests` counted every live pending packet even though the field name promised action requests …
- **`9c63556a`** — Refresh external review snapshot for 8d1c30a0
  - evolution: Fact: the remote-control review loop still had three small but real projection gaps. `ControlPlaneReadModel.pending_action_requests` counted every live pending packet even though the field name promised action requests …
- **`8d1c30a0`** — Fail closed on stale dashboard daemon state
  - evolution: Fact: the remote-control review loop still had three small but real projection gaps. `ControlPlaneReadModel.pending_action_requests` counted every live pending packet even though the field name promised action requests …
- **`847adc03`** — Refresh external review snapshot for 5daed3c2
  - evolution: Fact: the remote-control review loop still had three small but real projection gaps. `ControlPlaneReadModel.pending_action_requests` counted every live pending packet even though the field name promised action requests …
- **`5daed3c2`** — Delete redesign_research/ — operator: stop making MDs, use existing master plan + 24 active plans + LIVE_RUN.md
  - evolution: Fact: the remote-control review loop still had three small but real projection gaps. `ControlPlaneReadModel.pending_action_requests` counted every live pending packet even though the field name promised action requests …
- **`acac5ee0`** — Refresh external review snapshot for f5dc6d5e
  - evolution: Fact: the remote-control review loop still had three small but real projection gaps. `ControlPlaneReadModel.pending_action_requests` counted every live pending packet even though the field name promised action requests …
- **`f5dc6d5e`** — Push redesign research bundle for Codex (operator directive 2026-04-15)
  - Operator: "All this needs to be pushed to Codex. It is going to plan and code
  - this. Your job is research and push findings. You are not coding a goddamn line."
  - evolution: Fact: the remote-control review loop still had three small but real projection gaps. `ControlPlaneReadModel.pending_action_requests` counted every live pending packet even though the field name promised action requests …
- **`d3aafd01`** — Refresh external review snapshot for 9b4f8fb2
  - evolution: Fact: the remote-control review loop still had three small but real projection gaps. `ControlPlaneReadModel.pending_action_requests` counted every live pending packet even though the field name promised action requests …
- **`9b4f8fb2`** — Bulk push for Codex redesign: 3 worktree agent slices (Q100 lease + rev_pkt_0489 atomic + finding_backlog writer closure) + Q100 LIVE_RUN + bridge sync
  - Operator directive 2026-04-15: governed gate is part of what needs redesign;
  - push everything now so Codex can see full state and produce actual plan.
  - Bypass intentional per operator. 4 research agents still running — redesign
  - evolution: Fact: the remote-control review loop still had three small but real projection gaps. `ControlPlaneReadModel.pending_action_requests` counted every live pending packet even though the field name promised action requests …
- **`c6ef4054`** — Refresh external review snapshot for 671dfff3
  - evolution: Fact: the remote-control review loop still had three small but real projection gaps. `ControlPlaneReadModel.pending_action_requests` counted every live pending packet even though the field name promised action requests …
- **`671dfff3`** — Append Q100 architectural finding (attention_revision lease) to LIVE_RUN.md + bridge sync
  - evolution: Fact: the remote-control review loop still had three small but real projection gaps. `ControlPlaneReadModel.pending_action_requests` counted every live pending packet even though the field name promised action requests …
- **`b374610d`** — Log Q100 architectural finding: commit pipeline self-invalidates via shared attention_revision + dogfood records
  - evolution: Fact: the remote-control review loop still had three small but real projection gaps. `ControlPlaneReadModel.pending_action_requests` counted every live pending packet even though the field name promised action requests …
- **`64ad27ef`** — Refresh external review snapshot for 08859553 + sync bridge.md from typed review-state
  - evolution: Fact: the remote-control review loop still had three small but real projection gaps. `ControlPlaneReadModel.pending_action_requests` counted every live pending packet even though the field name promised action requests …
- **`08859553`** — Extract canonical operator_interaction_mode reducer to operator_context + delegate 3 launcher sites (closes rev_pkt_0463)
  - evolution: Fact: the remote-control review loop still had three small but real projection gaps. `ControlPlaneReadModel.pending_action_requests` counted every live pending packet even though the field name promised action requests …
- **`951b86aa`** — Propagate attachment-overrides-local_terminal promotion to launcher/ensure-follow/supervisor (rev_pkt_0459)
  - evolution: Fact: the remote-control review loop still had three small but real projection gaps. `ControlPlaneReadModel.pending_action_requests` counted every live pending packet even though the field name promised action requests …
- **`dba730f7`** — Wire reviewer-wake path + fix dashboard render keying + pending_action_requests filtering
  - evolution: Fact: the remote-control review loop still had three small but real projection gaps. `ControlPlaneReadModel.pending_action_requests` counted every live pending packet even though the field name promised action requests …
- **`493b9d03`** — Fix attachment override of operator_interaction_mode; revert policy default (closes rev_pkt_0448)
  - evolution: Fact: the remote-control review loop still had three small but real projection gaps. `ControlPlaneReadModel.pending_action_requests` counted every live pending packet even though the field name promised action requests …
- **`60a8d1bd`** — Refresh external review snapshot for 686a1283
  - evolution: Fact: the remote-control review loop still had three small but real projection gaps. `ControlPlaneReadModel.pending_action_requests` counted every live pending packet even though the field name promised action requests …
- **`686a1283`** — Align authority parity and review packet handling
  - evolution: Fact: the remote-control review loop still had three small but real projection gaps. `ControlPlaneReadModel.pending_action_requests` counted every live pending packet even though the field name promised action requests …
- **`6361080a`** — Fix review-channel watch follow liveness
  - evolution: Fact: the remote-control review loop still had three small but real projection gaps. `ControlPlaneReadModel.pending_action_requests` counted every live pending packet even though the field name promised action requests …
- **`3d78ef9f`** — Refresh external review snapshot for 6fdde964
  - evolution: Fact: the remote-control review loop still had three small but real projection gaps. `ControlPlaneReadModel.pending_action_requests` counted every live pending packet even though the field name promised action requests …
- **`6fdde964`** — Align authority snapshots and dashboard headers
  - evolution: Fact: the remote-control review loop still had three small but real projection gaps. `ControlPlaneReadModel.pending_action_requests` counted every live pending packet even though the field name promised action requests …
- **`455a2c64`** — Add authority snapshot runtime contract
  - evolution: Fact: the remote-control review loop still had three small but real projection gaps. `ControlPlaneReadModel.pending_action_requests` counted every live pending packet even though the field name promised action requests …
### Active MP scope (from MASTER_PLAN.md)

- contract slice for MP-355 plus the temporary markdown-swarm operating mode
- `dev/active/review_probes.md` is the review-probe execution spec; implementation tasks stay in this file under `MP-368..MP-375`.
- companion under `MP-376`, not a second main product plan; implementation
- architecture plan for the extracted AI-governance system under `MP-377`.
- `dev/active/code_shape_expansion.md` is the research/calibration companion for future code-shape additions under `MP-378`; promotion into implementation still flows through `dev/active/review_probes.md` once Phase 5b ev…
- 2026-04-11 remote-participant visibility follow-up in `MP-380..MP-387`
- the reopened MP-384/MP-387 F1 parity flake is now narrowed at the CLI edge
- Current 2026-04-05 reviewer-handoff closure inside that same lane: `MP-387`
- the `MP-381` field-route proof helper
- `MP-383` / `MP-381` packet-backed action-request and shared

## 8. Known gaps and open items

- open governance findings: 116

### Startup advisories
- checkpoint_before_continue: staged_index_budget_exceeded

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

Projection produced by `devctl review-snapshot`. Generation stamp `snap-4d4702e1a6f9` binds this file to HEAD `1271a075877f`; if they drift, the freshness guard will fail CI. When the latest commit only refreshes this generated snapshot, the guard accepts this file as bound to that commit's parent code state.
