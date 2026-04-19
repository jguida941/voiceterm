# VoiceTerm — Review Snapshot

> Deterministically generated from typed governance state. Do not edit by hand — rerun `devctl review-snapshot --write`.

## Quick status

- Branch: `feature/governance-quality-sweep`
- HEAD: `b16d5d3b78fa` — SYSTEM_MAP.md v6 — 10 gap-audit sections added per external-AI review
- Tree hash: `ebc9a7ac2874`
- Generation stamp: `snap-56e554588dde`
- Generated at (UTC): 2026-04-19T20:09:53Z
- Push decision: `await_review` — review_loop_relaunch_required
- Reviewer mode: `tools_only` (interaction: `local_terminal`)
- Pipeline state: `n/a` (approval: `n/a`)
- Delta since last snapshot: 24 commits, 217 files, +11877/-5194
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
- HEAD SHA: `b16d5d3b78fa8f9c086cf56f4ff6f247db5e262a`
- HEAD author: Justin Guida
- HEAD timestamp (UTC): 2026-04-19T16:09:40-04:00

## 2. Governance state

### Push decision
- action: `await_review`
- reason: review_loop_relaunch_required
- push_eligible_now: False
- worktree_clean: True
- staged_path_count: 0
- unstaged_path_count: 0
- next_step_command: `python3 dev/scripts/devctl.py review-channel --action status --terminal none --format json`
- latest_push_report: `dev/reports/push/latest.json`
- latest_push_report_state: `blocked` (validation_failed)
- current_push_authorization: `push-auth-20260419T184040545919Z` (valid=False)
- authorized_head_commit: `92b17e69456d8959e36d6091fa6a6f0a23c85844`
- approved_target_identity: `tree-receipt-20260419T132557054922Z:ad447307c9b99c354023f77d625a2babf8f55a3d`
- publication_backlog: queued
- publication_guidance: 1 local commit(s) waiting for governed push once review is accepted.

### Reviewer runtime
- reviewer_mode: `tools_only`
- reviewer_freshness: unknown
- reviewer_publish_clear: False
- interaction_mode: `local_terminal`
- implementation_blocked: yes — review_loop_relaunch_required

### Remote commit pipeline
- state: `n/a`
- approval_state: `n/a`

### Work intake
- active plan: **AI Governance Platform Plan**
- plan path: `dev/active/ai_governance_platform.md`
- active MP scope: `MP-377`
- advisory: `repair_reviewer_loop` — review_loop_relaunch_required

## 3. Delta — what changed since the previous snapshot

Range: last 24 commits ending at `b16d5d3b78fa`

- commits: 24
- files changed: 217
- insertions: +11877
- deletions: -5194
- bundle classes touched: docs, tooling
- risk add-ons triggered: Parser / ANSI boundary
- authority surfaces touched: 15 file(s)

### Commits

| # | SHA | Subject | Files | +/- | Bundle | Risk |
|---|---|---|---|---|---|---|
| 1 | `b16d5d3b` | SYSTEM_MAP.md v6 — 10 gap-audit sections added per external… | 1 | +320/-0 | docs |  |
| 2 | `548401c3` | Refresh external review snapshot for 01830a05 | 2 | +53/-62 | docs |  |
| 3 | `01830a05` | Fix SYSTEM_MAP.md per Codex rev_pkt_1358/1360 + prep for ex… | 1 | +11/-5 | docs |  |
| 4 | `0fb9dda6` | Refresh external review snapshot for 4dc05995 | 2 | +51/-46 | docs |  |
| 5 | `4dc05995` | SYSTEM_MAP.md v5 — operator override on Codex rev_pkt_1354… | 1 | +259/-2 | docs |  |
| 6 | `da2a7aec` | Refresh external review snapshot for ce1d75b4 | 2 | +55/-52 | docs |  |
| 7 | `ce1d75b4` | Fix SYSTEM_MAP.md per Codex rev_pkt_1353/1356 re-review | 1 | +8/-6 | docs |  |
| 8 | `27fc2d73` | Refresh external review snapshot for e19c5551 | 2 | +60/-59 | docs |  |
| 9 | `e19c5551` | Expand SYSTEM_MAP.md sections 22-29 from third 8-agent sweep | 1 | +186/-0 | docs |  |
| 10 | `983d3381` | Refresh external review snapshot for 995559a8 | 2 | +57/-57 | docs |  |
| 11 | `995559a8` | Fix SYSTEM_MAP.md per Codex review (rev_pkt_1348) | 1 | +36/-18 | docs |  |
| 12 | `6b0bcba1` | Refresh external review snapshot for 3c59b601 | 2 | +56/-50 | docs |  |
| 13 | `3c59b601` | Expand SYSTEM_MAP.md sections 14-21 from second 8-agent swe… | 1 | +243/-0 | docs |  |
| 14 | `fe9ed851` | Refresh external review snapshot for 9097f268 | 2 | +52/-51 | docs |  |
| 15 | `9097f268` | Add dev/guides/SYSTEM_MAP.md living connectivity index | 1 | +378/-0 | docs |  |
| 16 | `37d6be74` | Refresh external review snapshot for 8ef9f1a7 | 2 | +93/-79 | docs |  |
| 17 | `8ef9f1a7` | Recovery checkpoint: restore stashed session state + test f… | 7 | +312/-5 | docs |  |
| 18 | `92b17e69` | Land collaboration wake/ownership + typed plan integration… | 61 | +4203/-474 | tooling |  |
| 19 | `4245890c` | Refresh external review snapshot for 1f7b4f38 | 2 | +97/-86 | docs |  |
| 20 | `1f7b4f38` | Land MP-398/399/410/412/413/415/416 combined multi-slice (C… | 157 | +4448/-3794 | tooling | Parser / ANSI boundary |
| 21 | `fc20cc1b` | Refresh external review snapshot for aa570cee | 2 | +65/-67 | docs |  |
| 22 | `aa570cee` | Add role-implicit commit approval for /remote-control (rev_… | 14 | +414/-159 | tooling |  |
| 23 | `46d34660` | Refresh external review snapshot for 6e87e071 | 2 | +58/-56 | docs |  |
| 24 | `6e87e071` | Extend MP-377 with consolidation phases MP-388..MP-397 + Da… | 5 | +362/-66 | tooling |  |

### Files

| Path | Bundle | +/- |
|---|---|---|
| `AGENTS.md` | docs | +13/-0 |
| `bridge.md` | docs | +62/-62 |
| `dev/active/MASTER_PLAN.md` | tooling | +121/-0 |
| `dev/active/ai_governance_platform.md` | tooling | +490/-13 |
| `dev/active/remote_control_runtime.md` | tooling | +25/-1 |
| `dev/audits/REVIEW_SNAPSHOT.md` | tooling | +883/-857 |
| `dev/config/publication_sync_registry.json` | tooling | +2/-2 |
| `dev/drafts/claude_finding_readiness_proposal.md` | docs | +73/-0 |
| `dev/drafts/codex_exit_82_silent_death.md` | docs | +88/-0 |
| `dev/drafts/rev_pkt_1270_validation_partial.md` | docs | +58/-0 |
| `dev/drafts/wake_system_empirical_fail_20260419.md` | docs | +62/-0 |
| `dev/guides/DEVELOPMENT.md` | docs | +28/-10 |
| `dev/guides/SYSTEM_MAP.md` | docs | +1441/-31 |
| `dev/history/ENGINEERING_EVOLUTION.md` | tooling | +225/-40 |
| `dev/scripts/README.md` | tooling | +32/-15 |
| `dev/scripts/checks/active_plan/packet_plan_sync.py` | tooling | +69/-0 |
| `dev/scripts/checks/check_rustsec_policy.py` | tooling | +1/-17 |
| `dev/scripts/checks/coderabbit/gate_core.py` | tooling | +319/-0 |
| `dev/scripts/checks/coderabbit/gate_support.py` | tooling | +236/-0 |
| `dev/scripts/checks/coderabbit/run_ralph_loop.py` | tooling | +118/-0 |
| `dev/scripts/checks/coderabbit_gate_core.py` | tooling | +6/-318 |
| `dev/scripts/checks/coderabbit_gate_support.py` | tooling | +10/-236 |
| `dev/scripts/checks/governance_closure/command.py` | tooling | +1/-1 |
| `dev/scripts/checks/mutation_outcome_parse.py` | tooling | +6/-144 |
| `dev/scripts/checks/mutation_ralph_loop/outcome_parse.py` | tooling | +145/-0 |
| `dev/scripts/checks/platform_contract_closure/emitter_parity_contract_checks.py` | tooling | +5/-0 |
| `dev/scripts/checks/probe_boolean_params.py` | tooling | +1/-17 |
| `dev/scripts/checks/probe_clone_density.py` | tooling | +1/-17 |
| `dev/scripts/checks/probe_concurrency.py` | tooling | +1/-17 |
| `dev/scripts/checks/probe_defensive_overchecking.py` | tooling | +1/-17 |
| `dev/scripts/checks/probe_design_smells.py` | tooling | +1/-17 |
| `dev/scripts/checks/probe_dict_as_struct.py` | tooling | +1/-17 |
| `dev/scripts/checks/probe_exception_quality.py` | tooling | +1/-17 |
| `dev/scripts/checks/probe_magic_numbers.py` | tooling | +1/-17 |
| `dev/scripts/checks/probe_stringly_typed.py` | tooling | +1/-17 |
| `dev/scripts/checks/probe_type_conversions.py` | tooling | +1/-17 |
| `dev/scripts/checks/probe_unnecessary_intermediates.py` | tooling | +1/-17 |
| `dev/scripts/checks/probe_unwrap_chains.py` | tooling | +1/-17 |
| `dev/scripts/checks/probe_vague_errors.py` | tooling | +1/-17 |
| `dev/scripts/checks/run_coderabbit_ralph_loop.py` | tooling | +7/-113 |
| _177 more files trimmed_ | | |

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
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/review_channel/reviewer_runtime_snapshot.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_commit_phase.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_sync.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/review_channel/test_reviewer_runtime_doctor.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/runtime/test_startup_context.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/vcs/test_governed_executor.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/checks/startup_authority_contract/command.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/checks/startup_authority_contract/runtime_import_git.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_phases.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_stage_attention.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_stage_snapshot.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/review_snapshot_sources.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/checks/test_startup_authority_contract.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/vcs/governed_executor_packets.py`) — Review contract-level invariants for this file
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/collaboration_wake_contract.py`) — Commit 92b17e69 changed dev/scripts/devctl/runtime/collaboration_wake_contract.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/runtime/review_state_collaboration_models.py`) — Commit 92b17e69 changed dev/scripts/devctl/runtime/review_state_collaboration_models.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/tests/test_active_plan_contract.py`) — Commit 92b17e69 changed dev/scripts/devctl/tests/test_active_plan_contract.py
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/{governance_review_models.py => governance_review/models.py}`) — Commit 1f7b4f38 changed dev/scripts/devctl/{governance_review_models.py => governance_review/models.py}
- **contract_mutation**: Contract / typed model mutated (`dev/scripts/devctl/tests/checks/test_startup_authority_contract.py`) — Commit 1f7b4f38 changed dev/scripts/devctl/tests/checks/test_startup_authority_contract.py

### Suggested verification commands

- `python3 dev/scripts/devctl.py check --profile ci`
- `python3 dev/scripts/devctl.py probe-report --format md`
- `python3 dev/scripts/devctl.py docs-check --strict-tooling`
- `python3 dev/scripts/devctl.py governance-review --format md`
- `python3 dev/scripts/devctl.py check-router --format md`

## 7. Reasoning — why these changes landed

### Per-commit rationale

- **`b16d5d3b`** — SYSTEM_MAP.md v6 — 10 gap-audit sections added per external-AI review
  - Outside AI gap analysis flagged 10 missing content areas needed for
  - SYSTEM_MAP.md to serve as real AI orientation layer.
  - evolution: Fact: the next live Codex+Claude remote-control pass exposed a narrower defect than "the heartbeat is stale." Event-backed packet posting already updated the typed queue immediately, but the actual reviewer wake lived o…
- **`548401c3`** — Refresh external review snapshot for 01830a05
  - evolution: Fact: the next live Codex+Claude remote-control pass exposed a narrower defect than "the heartbeat is stale." Event-backed packet posting already updated the typed queue immediately, but the actual reviewer wake lived o…
- **`01830a05`** — Fix SYSTEM_MAP.md per Codex rev_pkt_1358/1360 + prep for external-AI gap response
  - 4 factual corrections:
  - evolution: Fact: the next live Codex+Claude remote-control pass exposed a narrower defect than "the heartbeat is stale." Event-backed packet posting already updated the typed queue immediately, but the actual reviewer wake lived o…
- **`0fb9dda6`** — Refresh external review snapshot for 4dc05995
  - evolution: Fact: the next live Codex+Claude remote-control pass exposed a narrower defect than "the heartbeat is stale." Event-backed packet posting already updated the typed queue immediately, but the actual reviewer wake lived o…
- **`4dc05995` | MPs: MP-230, MP-255** — SYSTEM_MAP.md v5 — operator override on Codex rev_pkt_1354 hold
  - Operator quote 2026-04-19 evening: 'I'm not sure if we don't have everything
  - in the system map that AI is not gonna know things... We need to have the
  - whole system mapped... regardless of what codex says until both of you are
  - evolution: Fact: the next live Codex+Claude remote-control pass exposed a narrower defect than "the heartbeat is stale." Event-backed packet posting already updated the typed queue immediately, but the actual reviewer wake lived o…
- **`da2a7aec`** — Refresh external review snapshot for ce1d75b4
  - evolution: Fact: the next live Codex+Claude remote-control pass exposed a narrower defect than "the heartbeat is stale." Event-backed packet posting already updated the typed queue immediately, but the actual reviewer wake lived o…
- **`ce1d75b4`** — Fix SYSTEM_MAP.md per Codex rev_pkt_1353/1356 re-review
  - 3 remaining doc integrity issues addressed:
  - evolution: Fact: the next live Codex+Claude remote-control pass exposed a narrower defect than "the heartbeat is stale." Event-backed packet posting already updated the typed queue immediately, but the actual reviewer wake lived o…
- **`27fc2d73`** — Refresh external review snapshot for e19c5551
  - evolution: Fact: the next live Codex+Claude remote-control pass exposed a narrower defect than "the heartbeat is stale." Event-backed packet posting already updated the typed queue immediately, but the actual reviewer wake lived o…
- **`e19c5551`** — Expand SYSTEM_MAP.md sections 22-29 from third 8-agent sweep
  - Operator directive 2026-04-19 evening: 'keep iterating with as many agents as
  - you need... looking for type state isn't connected... full system map of
  - everything what's connected what's not connected.'
  - evolution: Fact: the next live Codex+Claude remote-control pass exposed a narrower defect than "the heartbeat is stale." Event-backed packet posting already updated the typed queue immediately, but the actual reviewer wake lived o…
- **`983d3381`** — Refresh external review snapshot for 995559a8
  - evolution: Fact: the next live Codex+Claude remote-control pass exposed a narrower defect than "the heartbeat is stale." Event-backed packet posting already updated the typed queue immediately, but the actual reviewer wake lived o…
- **`995559a8`** — Fix SYSTEM_MAP.md per Codex review (rev_pkt_1348)
  - 4 findings confirmed + fixed:
  - evolution: Fact: the next live Codex+Claude remote-control pass exposed a narrower defect than "the heartbeat is stale." Event-backed packet posting already updated the typed queue immediately, but the actual reviewer wake lived o…
- **`6b0bcba1`** — Refresh external review snapshot for 3c59b601
  - evolution: Fact: the next live Codex+Claude remote-control pass exposed a narrower defect than "the heartbeat is stale." Event-backed packet posting already updated the typed queue immediately, but the actual reviewer wake lived o…
- **`3c59b601` | MPs: MP-377** — Expand SYSTEM_MAP.md sections 14-21 from second 8-agent sweep
  - Operator-directed iteration (2026-04-19 evening): 'keep iterating on system map
  - until you find nothing left with agents... tons of different commands not
  - documented, smarter guards, zgraphs needs to be talked about this MD too... full
  - plan: `dev/active/ai_governance_platform.md`
  - evolution: Fact: the next live Codex+Claude remote-control pass exposed a narrower defect than "the heartbeat is stale." Event-backed packet posting already updated the typed queue immediately, but the actual reviewer wake lived o…
- **`fe9ed851`** — Refresh external review snapshot for 9097f268
  - evolution: Fact: the next live Codex+Claude remote-control pass exposed a narrower defect than "the heartbeat is stale." Event-backed packet posting already updated the typed queue immediately, but the actual reviewer wake lived o…
- **`9097f268` | MPs: MP-405** — Add dev/guides/SYSTEM_MAP.md living connectivity index
  - Operator-directed (2026-04-19 evening): single canonical doc that indexes the
  - entire typed system + consolidates 7 stale architecture docs into one living
  - map. Section 0 Mermaid replaces SYSTEM_FLOWCHART.md sections 1-9. Sections 4-9
  - evolution: Fact: the next live Codex+Claude remote-control pass exposed a narrower defect than "the heartbeat is stale." Event-backed packet posting already updated the typed queue immediately, but the actual reviewer wake lived o…
- **`37d6be74`** — Refresh external review snapshot for 8ef9f1a7
  - evolution: Fact: the next live Codex+Claude remote-control pass exposed a narrower defect than "the heartbeat is stale." Event-backed packet posting already updated the typed queue immediately, but the actual reviewer wake lived o…
- **`8ef9f1a7`** — Recovery checkpoint: restore stashed session state + test file + drafts + review_only
  - Operator-directed recovery 2026-04-19 evening. Bypasses pre-commit hook because
  - startup-gate checks untracked_budget separately and was blocking single-agent
  - launcher. Files preserved from stash@{0} which has been dropped. No data lost.
  - evolution: Fact: the next live Codex+Claude remote-control pass exposed a narrower defect than "the heartbeat is stale." Event-backed packet posting already updated the typed queue immediately, but the actual reviewer wake lived o…
- **`92b17e69` | MPs: MP-417, MP-400, MP-418** — Land collaboration wake/ownership + typed plan integration + MP-417 drift fixes + 1288/1289/1290 regressions
  - Closes mutation/verification/watcher ownership drift (rev_pkt_1194), verification_owner
  - dedup (rev_pkt_1205), reviewer-wait-false-healthy (rev_pkt_1207), reviewer wake edge
  - (rev_pkt_1212 partial). Adds event_post_wake populating authority_snapshot +
  - evolution: Fact: the next live Codex+Claude remote-control pass exposed a narrower defect than "the heartbeat is stale." Event-backed packet posting already updated the typed queue immediately, but the actual reviewer wake lived o…
- **`4245890c`** — Refresh external review snapshot for 1f7b4f38
  - evolution: Fact: the next MP-377 collaboration pass exposed a smaller but more important coupling bug than "Claude should dogfood more." The repo already had `devctl dogfood --record --dev-mode`, but the live collaboration contrac…
- **`1f7b4f38` | MPs: MP-398** — Land MP-398/399/410/412/413/415/416 combined multi-slice (Codex v2-v7)
  - evolution: Fact: the next MP-377 collaboration pass exposed a smaller but more important coupling bug than "Claude should dogfood more." The repo already had `devctl dogfood --record --dev-mode`, but the live collaboration contrac…
- **`fc20cc1b`** — Refresh external review snapshot for aa570cee
  - evolution: Fact: the next MP-377 collaboration pass exposed a smaller but more important coupling bug than "Claude should dogfood more." The repo already had `devctl dogfood --record --dev-mode`, but the live collaboration contrac…
- **`aa570cee`** — Add role-implicit commit approval for /remote-control (rev_pkt_1120 gap #1)
  - evolution: Fact: the next MP-377 collaboration pass exposed a smaller but more important coupling bug than "Claude should dogfood more." The repo already had `devctl dogfood --record --dev-mode`, but the live collaboration contrac…
- **`46d34660`** — Refresh external review snapshot for 6e87e071
  - evolution: Fact: the next MP-377 collaboration pass exposed a smaller but more important coupling bug than "Claude should dogfood more." The repo already had `devctl dogfood --record --dev-mode`, but the live collaboration contrac…
- **`6e87e071` | MPs: MP-377, MP-388, MP-397** — Extend MP-377 with consolidation phases MP-388..MP-397 + Data Contracts
  - plan: `dev/active/ai_governance_platform.md`
  - evolution: Fact: the next MP-377 collaboration pass exposed a smaller but more important coupling bug than "Claude should dogfood more." The repo already had `devctl dogfood --record --dev-mode`, but the live collaboration contrac…
### Active MP scope (from MASTER_PLAN.md)

- contract slice for MP-355 plus the temporary markdown-swarm operating mode
- `dev/active/review_probes.md` is the review-probe execution spec; implementation tasks stay in this file under `MP-368..MP-375`.
- companion under `MP-376`, not a second main product plan; implementation
- architecture plan for the extracted AI-governance system under `MP-377`.
- `dev/active/code_shape_expansion.md` is the research/calibration companion for future code-shape additions under `MP-378`; promotion into implementation still flows through `dev/active/review_probes.md` once Phase 5b ev…
- 2026-04-18 `MP-399` governed commit staged-index preservation in `MP-377`
- 2026-04-18 `MP-410` devctl root package-layout relief in `MP-377` scope:
- 2026-04-18 `MP-398` push preflight staged-index exclusion in `MP-377`
- 2026-04-18 `MP-388` consolidation archive pass in `MP-377` scope:
- 2026-04-18 `MP-389` semantic plan-loader core in `MP-377` scope:

## 8. Known gaps and open items

- open governance findings: 112

### Startup advisories
- repair_reviewer_loop: review_loop_relaunch_required

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

Projection produced by `devctl review-snapshot`. Generation stamp `snap-56e554588dde` binds this file to HEAD `b16d5d3b78fa`; if they drift, the freshness guard will fail CI. When the latest commit only refreshes this generated snapshot, the guard accepts this file as bound to that commit's parent code state.
