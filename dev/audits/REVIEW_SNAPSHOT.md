# VoiceTerm — Review Snapshot

> Deterministically generated from typed governance state. Do not edit by hand — rerun `devctl review-snapshot --write`.

## Quick status

- Branch: `feature/governance-quality-sweep`
- HEAD: `23c4239ace80` — Fix session command blocking (Codex finding rev_pkt_0785): add 30s timeout
- Tree hash: `ceb2878b08e9`
- Generation stamp: `snap-0378dbefd04e`
- Generated at (UTC): 2026-04-16T18:28:35Z
- Push decision: `await_review` — runtime_missing
- Reviewer mode: `tools_only` (interaction: `local_terminal`)
- Pipeline state: `n/a` (approval: `n/a`)
- Delta since last snapshot: 24 commits, 28 files, +4423/-1638
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
- HEAD SHA: `23c4239ace8003d36196b360a962b42bda7f6977`
- HEAD author: Justin Guida
- HEAD timestamp (UTC): 2026-04-16T14:28:09-04:00

## 2. Governance state

### Push decision
- action: `await_review`
- reason: runtime_missing
- push_eligible_now: False
- worktree_clean: True
- staged_path_count: 0
- unstaged_path_count: 0
- next_step_command: `python3 dev/scripts/devctl.py review-channel --action status --terminal none --format json`
- latest_push_report: `dev/reports/push/latest.json`
- latest_push_report_state: `blocked` (validation_failed)
- publication_backlog: queued
- publication_guidance: 1 local commit(s) waiting for governed push once review is accepted.

### Reviewer runtime
- reviewer_mode: `tools_only`
- reviewer_freshness: unknown
- reviewer_publish_clear: False
- interaction_mode: `local_terminal`
- implementation_blocked: yes — runtime_missing

### Remote commit pipeline
- state: `n/a`
- approval_state: `n/a`

### Work intake
- active plan: **AI Governance Platform Plan**
- plan path: `dev/active/ai_governance_platform.md`
- active MP scope: `MP-377`
- advisory: `repair_reviewer_loop` — runtime_missing

## 3. Delta — what changed since the previous snapshot

Range: last 24 commits ending at `23c4239ace80`

- commits: 24
- files changed: 28
- insertions: +4423
- deletions: -1638
- bundle classes touched: tooling, docs
- authority surfaces touched: 8 file(s)

### Commits

| # | SHA | Subject | Files | +/- | Bundle | Risk |
|---|---|---|---|---|---|---|
| 1 | `23c4239a` | Fix session command blocking (Codex finding rev_pkt_0785):… | 1 | +29/-12 | tooling |  |
| 2 | `598aa8a3` | Refresh external review snapshot for 526019f9 | 2 | +70/-76 | docs |  |
| 3 | `526019f9` | Fix Codex findings rev_pkt_0777/0779/0783 | 3 | +7/-4 | tooling |  |
| 4 | `5fa0f1a2` | Refresh external review snapshot for 66ca79db | 2 | +58/-56 | docs |  |
| 5 | `66ca79db` | devctl session command + gate hardening + reviewer loop + m… | 8 | +479/-64 | tooling |  |
| 6 | `c3e13cdf` | Refresh external review snapshot for 1f927cbf | 1 | +58/-55 | tooling |  |
| 7 | `1f927cbf` | Refresh external review snapshot for 819a88a3 | 2 | +66/-59 | docs |  |
| 8 | `819a88a3` | Typed reviewer-wake convergence + modularization | 9 | +361/-181 | tooling |  |
| 9 | `06665471` | Refresh external review snapshot for 32e5997d | 2 | +50/-54 | docs |  |
| 10 | `32e5997d` | Refresh external review snapshot for e9f6a6b3 | 2 | +72/-70 | docs |  |
| 11 | `e9f6a6b3` | Fix fail-open regression in commit_packet_gate + contract d… | 5 | +448/-74 | tooling |  |
| 12 | `a9f1a42f` | Refresh external review snapshot for d2d91aaf | 2 | +66/-64 | docs |  |
| 13 | `d2d91aaf` | Unify commit-gate caller policy across governed + receipt p… | 8 | +218/-145 | tooling |  |
| 14 | `7c1562f3` | Refresh external review snapshot for dae1df84 | 2 | +65/-65 | docs |  |
| 15 | `dae1df84` | Make reviewer turn runner governance-shaped instead of brid… | 3 | +138/-50 | tooling |  |
| 16 | `b627c135` | Unify target resolver + fail-closed on unresolved target +… | 5 | +110/-118 | tooling |  |
| 17 | `4c01b779` | Add fail-closed commit gate on pending reviewer packets | 6 | +622/-49 | tooling |  |
| 18 | `6221bc32` | Refresh external review snapshot for f4c3a335 | 2 | +63/-61 | docs |  |
| 19 | `f4c3a335` | Fix Codex review findings: revert premature follow wiring +… | 6 | +66/-64 | tooling |  |
| 20 | `26e8730a` | Refresh external review snapshot for d08407ca | 1 | +67/-75 | tooling |  |
| 21 | `4d2c991c` | Refresh external review snapshot for d08407ca | 2 | +66/-63 | docs |  |
| 22 | `d08407ca` | Add portable controller-owned reviewer turn runner + public… | 9 | +1129/-65 | tooling |  |
| 23 | `eea5abf5` | Refresh external review snapshot for bf0c0d90 | 2 | +56/-54 | docs |  |
| 24 | `bf0c0d90` | Fix test_implementer_stall import after event_projection re… | 2 | +59/-60 | tooling |  |

### Files

| Path | Bundle | +/- |
|---|---|---|
| `bridge.md` | docs | +40/-35 |
| `dev/audits/REVIEW_SNAPSHOT.md` | tooling | +1244/-1248 |
| `dev/scripts/devctl/cli_parser/entrypoint.py` | tooling | +4/-0 |
| `dev/scripts/devctl/commands/governance/review_snapshot.py` | tooling | +47/-14 |
| `dev/scripts/devctl/commands/governance/session.py` | tooling | +146/-13 |
| `dev/scripts/devctl/commands/governance/session_reviewer_loop.py` | tooling | +185/-0 |
| `dev/scripts/devctl/commands/review_channel/reviewer_runtime_snapshot.py` | tooling | +3/-0 |
| `dev/scripts/devctl/commands/vcs/governed_executor_commit_phase.py` | tooling | +34/-10 |
| `dev/scripts/devctl/platform/runtime_state_contract_rows_review.py` | tooling | +2/-0 |
| `dev/scripts/devctl/review_channel/current_session_attention.py` | tooling | +14/-14 |
| `dev/scripts/devctl/review_channel/follow_controller.py` | tooling | +12/-84 |
| `dev/scripts/devctl/review_channel/follow_controller_wake_target.py` | tooling | +152/-0 |
| `dev/scripts/devctl/review_channel/publication_ownership.py` | tooling | +164/-0 |
| `dev/scripts/devctl/review_channel/reviewer_follow.py` | tooling | +6/-6 |
| `dev/scripts/devctl/review_channel/reviewer_follow_packet_guard.py` | tooling | +12/-28 |
| `dev/scripts/devctl/review_channel/reviewer_follow_trigger_gate.py` | tooling | +77/-4 |
| `dev/scripts/devctl/review_channel/reviewer_state.py` | tooling | +3/-4 |
| `dev/scripts/devctl/review_channel/reviewer_turn_runner.py` | tooling | +309/-14 |
| `dev/scripts/devctl/runtime/commit_packet_gate.py` | tooling | +261/-65 |
| `dev/scripts/devctl/runtime/remote_commit_pipeline_models.py` | tooling | +6/-0 |
| `dev/scripts/devctl/tests/governance/test_read_only_commands.py` | tooling | +1/-0 |
| `dev/scripts/devctl/tests/review_channel/test_implementer_stall.py` | tooling | +1/-1 |
| `dev/scripts/devctl/tests/review_channel/test_publication_ownership.py` | tooling | +189/-0 |
| `dev/scripts/devctl/tests/review_channel/test_reviewer_turn_runner.py` | tooling | +525/-0 |
| `dev/scripts/devctl/tests/runtime/test_review_snapshot.py` | tooling | +480/-77 |
| `dev/scripts/devctl/tests/vcs/test_commit_gate.py` | tooling | +5/-2 |
| `dev/scripts/devctl/tests/vcs/test_commit_pending_reviewer_gate.py` | tooling | +407/-19 |
| `dev/scripts/reviewer_loop.sh` | tooling | +94/-0 |

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

- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/review_channel/reviewer_follow_trigger_gate.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/review_channel/reviewer_runtime_snapshot.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/review_channel/reviewer_follow_packet_guard.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/runtime/test_review_snapshot.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/governance/review_snapshot.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_commit_phase.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/review_channel/reviewer_follow.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/remote_commit_pipeline_models.py`) — Review contract-level invariants for this file
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/remote_commit_pipeline_models.py`) — Commit d08407ca changed dev/scripts/devctl/runtime/remote_commit_pipeline_models.py

### Suggested verification commands

- `python3 dev/scripts/devctl.py check --profile ci`
- `python3 dev/scripts/devctl.py probe-report --format md`
- `python3 dev/scripts/devctl.py docs-check --strict-tooling`
- `python3 dev/scripts/devctl.py governance-review --format md`
- `python3 dev/scripts/devctl.py check-router --format md`

## 7. Reasoning — why these changes landed

### Per-commit rationale

- **`23c4239a`** — Fix session command blocking (Codex finding rev_pkt_0785): add 30s timeout
- **`598aa8a3`** — Refresh external review snapshot for 526019f9
- **`526019f9`** — Fix Codex findings rev_pkt_0777/0779/0783
  - - session.py: dashboard role maps to 'observer' (rev_pkt_0777)
  - - reviewer_follow_trigger_gate: relaunch-required bypasses review_needed
  -   check instead of being blocked by it (rev_pkt_0779)
- **`5fa0f1a2`** — Refresh external review snapshot for 66ca79db
- **`66ca79db`** — devctl session command + gate hardening + reviewer loop + modularization
  - New command: devctl session --role reviewer/implementer/dashboard
  - - session.py: role dispatcher with --loop and --headless flags
  - - session_reviewer_loop.py: governed Python reviewer loop
- **`c3e13cdf`** — Refresh external review snapshot for 1f927cbf
- **`1f927cbf`** — Refresh external review snapshot for 819a88a3
- **`819a88a3`** — Typed reviewer-wake convergence + modularization
  - Reviewer-wake convergence (MP377-P1-T06, rev_pkt_0734):
  - - reviewer_runtime_snapshot: attaches typed packet_inbox to report
  - - follow_controller: typed coordination gate, typed packet selection
- **`06665471`** — Refresh external review snapshot for 32e5997d
- **`32e5997d`** — Refresh external review snapshot for e9f6a6b3
- **`e9f6a6b3`** — Fix fail-open regression in commit_packet_gate + contract drift
  - Gate fix: check_commit_packet_gate() now distinguishes "no review channel"
  - (allow) from "load failed" (block) with 5-case fail-closed contract.
  - Replaces getattr() with typed AgentAttentionRecord/PacketInboxState.
- **`a9f1a42f`** — Refresh external review snapshot for d2d91aaf
- **`d2d91aaf`** — Unify commit-gate caller policy across governed + receipt paths
  - Both governed_executor_commit_phase and review_snapshot now call
  - check_commit_packet_gate() with identical load→resolve→skip→gate
  - semantics. Fixes rev_pkt_0728 finding: split caller policy where
- **`7c1562f3`** — Refresh external review snapshot for dae1df84
- **`dae1df84`** — Make reviewer turn runner governance-shaped instead of bridge-local
  - detect_reviewer_wake() and build_reviewer_turn_context() now accept
  - optional governance: ProjectGovernance parameter. When provided:
  - - bridge_path is resolved from governance.bridge_config.bridge_path
- **`b627c135`** — Unify target resolver + fail-closed on unresolved target + receipt tests
  - Addresses rev_pkt_0716 findings:
- **`4c01b779`** — Add fail-closed commit gate on pending reviewer packets
  - Shared lease-independent gate in runtime/commit_packet_gate.py blocks
  - both governed commit (commit_phase.py) and snapshot receipt-commit
  - (review_snapshot.py) when actionable reviewer packets exist.
- **`6221bc32`** — Refresh external review snapshot for f4c3a335
- **`f4c3a335`** — Fix Codex review findings: revert premature follow wiring + acked wake bug
  - 1. Revert reviewer_follow.py wiring — keep turn runner out of live
  -    follow/report path until core wake/context contract is accepted.
  - 2. Fix acked-status wake bug — only pending packets trigger reviewer
- **`26e8730a`** — Refresh external review snapshot for d08407ca
- **`4d2c991c`** — Refresh external review snapshot for d08407ca
- **`d08407ca`** — Add portable controller-owned reviewer turn runner + publication ownership
  - Cut 1: reviewer_turn_runner.py — typed contract for one bounded reviewer
  - turn without chat relay (ReviewerWakeSignal, ReviewerTurnContext,
  - ReviewerTurnResult). Builds on existing ReviewerTurnAuthority.
- **`eea5abf5`** — Refresh external review snapshot for bf0c0d90
- **`bf0c0d90`** — Fix test_implementer_stall import after event_projection restructuring
  - detect_event_implementer_stall moved from event_projection to
  - event_projection_bridge during the operator's module extraction.
  - Update test import path to match. 7/7 tests pass.
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

- open governance findings: 112

### Startup advisories
- repair_reviewer_loop: runtime_missing

### Stale warnings
- Cut a checkpoint before doing anything else.

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

Projection produced by `devctl review-snapshot`. Generation stamp `snap-0378dbefd04e` binds this file to HEAD `23c4239ace80`; if they drift, the freshness guard will fail CI. When the latest commit only refreshes this generated snapshot, the guard accepts this file as bound to that commit's parent code state.
