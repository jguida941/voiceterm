# VoiceTerm — Review Snapshot

> Deterministically generated from typed governance state. Do not edit by hand — rerun `devctl review-snapshot --write`.

## Quick status

- Branch: `feature/governance-quality-sweep`
- HEAD: `99334c9298b4` — Refresh external review snapshot for 7faed568
- Tree hash: `936d930eefc4`
- Generation stamp: `snap-2bdf66104e9e`
- Generated at (UTC): 2026-04-20T08:24:46Z
- Push decision: `await_checkpoint` — staged_index_present
- Reviewer mode: `tools_only` (interaction: `local_terminal`)
- Pipeline state: `n/a` (approval: `n/a`)
- Delta since last snapshot: 24 commits, 73 files, +4470/-2176
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
- HEAD SHA: `99334c9298b4a397bb95fa884f9c1d9cf62d1def`
- HEAD author: Justin Guida
- HEAD timestamp (UTC): 2026-04-20T04:13:15-04:00

## 2. Governance state

### Push decision
- action: `await_checkpoint`
- reason: staged_index_present
- push_eligible_now: False
- worktree_clean: False
- staged_path_count: 8
- unstaged_path_count: 0
- next_step_command: `python3 dev/scripts/devctl.py review-channel --action status --terminal none --format json`
- latest_push_report: `dev/reports/push/latest.json`
- latest_push_report_state: `blocked` (validation_failed)
- current_push_authorization: `push-auth-20260420T081256549563Z` (valid=True)
- authorized_head_commit: `99334c9298b4a397bb95fa884f9c1d9cf62d1def`
- approved_target_identity: `tree-receipt-20260420T081256549563Z:2f80841e42bebb57656930ddbf92aeee6cd4da9c`
- publication_backlog: recommended
- publication_guidance: 2 local commit(s) waiting for governed push once the current slice is checkpoint-clean.

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
- advisory: `checkpoint_before_continue` — dirty_after_local_checkpoint

## 3. Delta — what changed since the previous snapshot

Range: last 24 commits ending at `99334c9298b4`

- commits: 24
- files changed: 73
- insertions: +4470
- deletions: -2176
- bundle classes touched: docs, tooling
- authority surfaces touched: 5 file(s)

### Commits

| # | SHA | Subject | Files | +/- | Bundle | Risk |
|---|---|---|---|---|---|---|
| 1 | `99334c92` | Refresh external review snapshot for 7faed568 | 2 | +76/-71 | docs |  |
| 2 | `7faed568` | Propagate review-state provenance and zref parity | 29 | +1140/-551 | tooling |  |
| 3 | `b36d14e8` | Harden conductor hygiene and reviewer wake | 14 | +393/-185 | tooling |  |
| 4 | `54ec06d8` | Advance session-resume parity and conductor hygiene | 24 | +1302/-503 | tooling |  |
| 5 | `19bbe4f6` | Refresh external review snapshot for 066112fb | 2 | +74/-63 | docs |  |
| 6 | `066112fb` | Checkpoint session-resume parity and collaboration wake clo… | 14 | +657/-93 | tooling |  |
| 7 | `95131e80` | Refresh external review snapshot for 818e4692 | 2 | +53/-56 | docs |  |
| 8 | `818e4692` | Fix regression test per Codex rev_pkt_1403: assert real fie… | 1 | +71/-17 | tooling |  |
| 9 | `e61fb65c` | Refresh external review snapshot for 3d14a22a | 2 | +50/-47 | docs |  |
| 10 | `3d14a22a` | SYSTEM_MAP.md v7.1 — §9 coverage refreshed 22%->37% + dogfo… | 1 | +6/-5 | docs |  |
| 11 | `c762e1c0` | Refresh external review snapshot for 6944d2c9 | 2 | +48/-54 | docs |  |
| 12 | `6944d2c9` | bridge.md: substantive Claude Status + Ack for rev 66a62d41… | 1 | +7/-2 | docs |  |
| 13 | `fe7cf67b` | Refresh external review snapshot for 02325c76 | 2 | +48/-46 | docs |  |
| 14 | `02325c76` | Add regression test for observer-scoped authority snapshot… | 1 | +45/-0 | tooling |  |
| 15 | `74467983` | Refresh external review snapshot for 9ac8211d | 2 | +48/-50 | docs |  |
| 16 | `9ac8211d` | SYSTEM_MAP.md v7.0 — §0.7 tier fix per Codex rev_pkt_1397 s… | 1 | +2/-1 | docs |  |
| 17 | `c52d7972` | Refresh external review snapshot for 902b39af | 2 | +67/-52 | docs |  |
| 18 | `902b39af` | rev_pkt_1366 FULL close per Codex rev_pkt_1396 directive | 2 | +5/-2 | tooling |  |
| 19 | `908b0c97` | Refresh external review snapshot for 17d68365 | 2 | +58/-63 | docs |  |
| 20 | `17d68365` | SYSTEM_MAP.md v6.9 — revert §54 per operator: SYSTEM_MAP is… | 2 | +52/-87 | tooling |  |
| 21 | `3dc695bc` | Refresh external review snapshot for 096df5bf | 2 | +61/-61 | docs |  |
| 22 | `096df5bf` | SYSTEM_MAP.md v6.8 — §54 Active Joint Work coordination sur… | 2 | +89/-50 | tooling |  |
| 23 | `635c1a23` | Refresh external review snapshot for 93e96fc6 | 2 | +64/-65 | docs |  |
| 24 | `93e96fc6` | rev_pkt_1366: status.py passes caller_role='observer' to pr… | 2 | +54/-52 | tooling |  |

### Files

| Path | Bundle | +/- |
|---|---|---|
| `bridge.md` | docs | +66/-66 |
| `dev/active/MASTER_PLAN.md` | tooling | +9/-4 |
| `dev/active/ai_governance_platform.md` | tooling | +24/-8 |
| `dev/audits/REVIEW_SNAPSHOT.md` | tooling | +994/-944 |
| `dev/guides/SYSTEM_MAP.md` | docs | +45/-43 |
| `dev/scripts/README.md` | tooling | +24/-10 |
| `dev/scripts/checks/review_surface_consistency/command.py` | tooling | +26/-69 |
| `dev/scripts/checks/review_surface_consistency/models.py` | tooling | +2/-0 |
| `dev/scripts/checks/review_surface_consistency/snapshot_fields.py` | tooling | +175/-0 |
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
| `dev/scripts/devctl/commands/review_channel/reviewer_runtime_snapshot.py` | tooling | +101/-2 |
| `dev/scripts/devctl/commands/review_channel/status.py` | tooling | +5/-29 |
| `dev/scripts/devctl/commands/review_channel/status_runtime_projection.py` | tooling | +49/-0 |
| `dev/scripts/devctl/commands/review_channel_command/helpers.py` | tooling | +9/-0 |
| `dev/scripts/devctl/platform/runtime_state_contract_rows_review.py` | tooling | +25/-0 |
| `dev/scripts/devctl/platform/surface_state_contract_rows.py` | tooling | +25/-0 |
| `dev/scripts/devctl/process_sweep/internals.py` | tooling | +2/-41 |
| `dev/scripts/devctl/review_channel/collaboration_registry.py` | tooling | +16/-6 |
| `dev/scripts/devctl/review_channel/event_projection_assembly.py` | tooling | +50/-69 |
| `dev/scripts/devctl/review_channel/event_projection_context.py` | tooling | +114/-53 |
| `dev/scripts/devctl/review_channel/event_projection_support.py` | tooling | +45/-13 |
| `dev/scripts/devctl/review_channel/event_reducer.py` | tooling | +5/-2 |
| `dev/scripts/devctl/review_channel/follow_controller.py` | tooling | +4/-5 |
| `dev/scripts/devctl/review_channel/heartbeat.py` | tooling | +1/-0 |
| `dev/scripts/devctl/review_channel/projection_bundle.py` | tooling | +3/-1 |
| `dev/scripts/devctl/review_channel/projection_bundle_parity.py` | tooling | +77/-0 |
| `dev/scripts/devctl/review_channel/projection_provenance.py` | tooling | +29/-0 |
| `dev/scripts/devctl/review_channel/prompt_support.py` | tooling | +8/-4 |
| `dev/scripts/devctl/review_channel/registry_context.py` | tooling | +24/-0 |
| `dev/scripts/devctl/review_channel/reviewer_follow_guard.py` | tooling | +8/-2 |
| `dev/scripts/devctl/review_channel/status_bundle.py` | tooling | +2/-1 |
| _33 more files trimmed_ | | |

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

- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/runtime/startup_context.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/tests/runtime/test_startup_context.py`) — Review contract-level invariants for this file
- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/review_channel/reviewer_follow_guard.py`) — Review contract-level invariants for this file
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

- **`99334c92`** — Refresh external review snapshot for 7faed568
- **`7faed568`** — Propagate review-state provenance and zref parity
- **`b36d14e8`** — Harden conductor hygiene and reviewer wake
- **`54ec06d8`** — Advance session-resume parity and conductor hygiene
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
- **`e61fb65c`** — Refresh external review snapshot for 3d14a22a
  - evolution: Fact: the next live Codex+Claude remote-control pass exposed a narrower defect than "the heartbeat is stale." Event-backed packet posting already updated the typed queue immediately, but the actual reviewer wake lived o…
- **`3d14a22a`** — SYSTEM_MAP.md v7.1 — §9 coverage refreshed 22%->37% + dogfood display bug noted
  - Stream C dogfood this iteration bumped command coverage from 19 to 31 (37%)
  - after recording this session's 12+ runs. Also surfaced devctl dogfood bug:
  - --max-rows N misapplied to Coverage stat computation (not just display).
  - evolution: Fact: the next live Codex+Claude remote-control pass exposed a narrower defect than "the heartbeat is stale." Event-backed packet posting already updated the typed queue immediately, but the actual reviewer wake lived o…
- **`c762e1c0`** — Refresh external review snapshot for 6944d2c9
  - evolution: Fact: the next live Codex+Claude remote-control pass exposed a narrower defect than "the heartbeat is stale." Event-backed packet posting already updated the typed queue immediately, but the actual reviewer wake lived o…
- **`6944d2c9`** — bridge.md: substantive Claude Status + Ack for rev 66a62d41cd9f (rev_pkt_1397 step 1)
  - Codex rev_pkt_1397 step 1: restore substantive Claude Status + Ack for
  - revision 66a62d41cd9f after the 'Status unavailable' placeholder.
  - evolution: Fact: the next live Codex+Claude remote-control pass exposed a narrower defect than "the heartbeat is stale." Event-backed packet posting already updated the typed queue immediately, but the actual reviewer wake lived o…
- **`fe7cf67b`** — Refresh external review snapshot for 02325c76
  - evolution: Fact: the next live Codex+Claude remote-control pass exposed a narrower defect than "the heartbeat is stale." Event-backed packet posting already updated the typed queue immediately, but the actual reviewer wake lived o…
- **`02325c76`** — Add regression test for observer-scoped authority snapshot (rev_pkt_1397 step 2)
  - Codex rev_pkt_1397 step 2: add regression coverage so persisted status/projection
  - authority snapshots stay observer-scoped and cannot advertise vcs.stage/vcs.commit
  - on read-only surfaces.
  - evolution: Fact: the next live Codex+Claude remote-control pass exposed a narrower defect than "the heartbeat is stale." Event-backed packet posting already updated the typed queue immediately, but the actual reviewer wake lived o…
- **`74467983`** — Refresh external review snapshot for 9ac8211d
  - evolution: Fact: the next live Codex+Claude remote-control pass exposed a narrower defect than "the heartbeat is stale." Event-backed packet posting already updated the typed queue immediately, but the actual reviewer wake lived o…
- **`9ac8211d`** — SYSTEM_MAP.md v7.0 — §0.7 tier fix per Codex rev_pkt_1397 step 3: platform_authority_loop reference-only
  - evolution: Fact: the next live Codex+Claude remote-control pass exposed a narrower defect than "the heartbeat is stale." Event-backed packet posting already updated the typed queue immediately, but the actual reviewer wake lived o…
- **`c52d7972`** — Refresh external review snapshot for 902b39af
  - evolution: Fact: the next live Codex+Claude remote-control pass exposed a narrower defect than "the heartbeat is stale." Event-backed packet posting already updated the typed queue immediately, but the actual reviewer wake lived o…
- **`902b39af`** — rev_pkt_1366 FULL close per Codex rev_pkt_1396 directive
  - Codex (reviewer-locked, cannot code itself) directed Claude to self-execute
  - the 2-file patch. Operator authorized bypass since typed directive from
  - Codex + green verification from Claude side should flow through hook as
  - evolution: Fact: the next live Codex+Claude remote-control pass exposed a narrower defect than "the heartbeat is stale." Event-backed packet posting already updated the typed queue immediately, but the actual reviewer wake lived o…
- **`908b0c97`** — Refresh external review snapshot for 17d68365
  - evolution: Fact: the next live Codex+Claude remote-control pass exposed a narrower defect than "the heartbeat is stale." Event-backed packet posting already updated the typed queue immediately, but the actual reviewer wake lived o…
- **`17d68365`** — SYSTEM_MAP.md v6.9 — revert §54 per operator: SYSTEM_MAP is reference, not work log
  - evolution: Fact: the next live Codex+Claude remote-control pass exposed a narrower defect than "the heartbeat is stale." Event-backed packet posting already updated the typed queue immediately, but the actual reviewer wake lived o…
- **`3dc695bc`** — Refresh external review snapshot for 096df5bf
  - evolution: Fact: the next live Codex+Claude remote-control pass exposed a narrower defect than "the heartbeat is stale." Event-backed packet posting already updated the typed queue immediately, but the actual reviewer wake lived o…
- **`096df5bf`** — SYSTEM_MAP.md v6.8 — §54 Active Joint Work coordination surface
  - Operator directive 2026-04-19: 'that's the point of the system MD... stop
  - packet-flooding and actually build.' This adds §54 as the single
  - coordination surface for active joint work.
  - evolution: Fact: the next live Codex+Claude remote-control pass exposed a narrower defect than "the heartbeat is stale." Event-backed packet posting already updated the typed queue immediately, but the actual reviewer wake lived o…
- **`635c1a23`** — Refresh external review snapshot for 93e96fc6
  - evolution: Fact: the next live Codex+Claude remote-control pass exposed a narrower defect than "the heartbeat is stale." Event-backed packet posting already updated the typed queue immediately, but the actual reviewer wake lived o…
- **`93e96fc6`** — rev_pkt_1366: status.py passes caller_role='observer' to project_authority_snapshot
  - Codex rev_pkt_1366: review_channel status.py calls project_authority_snapshot
  - without caller_role, so normalize_agent_lane defaults to 'implementer' and the
  - returned authority_snapshot silently grants vcs.stage/vcs.commit to read-only
  - evolution: Fact: the next live Codex+Claude remote-control pass exposed a narrower defect than "the heartbeat is stale." Event-backed packet posting already updated the typed queue immediately, but the actual reviewer wake lived o…
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
- checkpoint_before_continue: dirty_after_local_checkpoint

### Stale warnings
- Relaunch the reviewer loop immediately.

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

Projection produced by `devctl review-snapshot`. Generation stamp `snap-2bdf66104e9e` binds this file to HEAD `99334c9298b4`; if they drift, the freshness guard will fail CI. When the latest commit only refreshes this generated snapshot, the guard accepts this file as bound to that commit's parent code state.
