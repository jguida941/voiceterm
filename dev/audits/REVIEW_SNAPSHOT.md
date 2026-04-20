# VoiceTerm — Review Snapshot

> Deterministically generated from typed governance state. Do not edit by hand — rerun `devctl review-snapshot --write`.

## Quick status

- Branch: `feature/governance-quality-sweep`
- HEAD: `95131e800ca7` — Refresh external review snapshot for 818e4692
- Tree hash: `f2f4fbfa7f0a`
- Generation stamp: `snap-50b9446cef16`
- Generated at (UTC): 2026-04-20T01:21:54Z
- Push decision: `await_checkpoint` — staged_index_budget_exceeded
- Reviewer mode: `active_dual_agent` (interaction: `local_terminal`)
- Pipeline state: `n/a` (approval: `n/a`)
- Delta since last snapshot: 25 commits, 7 files, +1227/-1114
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
- HEAD SHA: `95131e800ca7ca93aadc83f638a057d182b6301f`
- HEAD author: Justin Guida
- HEAD timestamp (UTC): 2026-04-19T19:15:38-04:00

## 2. Governance state

### Push decision
- action: `await_checkpoint`
- reason: staged_index_budget_exceeded
- push_eligible_now: False
- worktree_clean: False
- staged_path_count: 13
- unstaged_path_count: 0
- next_step_command: `python3 dev/scripts/devctl.py review-channel --action status --terminal none --format json`
- latest_push_report: `dev/reports/push/latest.json`
- latest_push_report_state: `blocked` (validation_failed)
- current_push_authorization: `push-auth-20260419T184040545919Z` (valid=False)
- authorized_head_commit: `92b17e69456d8959e36d6091fa6a6f0a23c85844`
- approved_target_identity: `tree-receipt-20260419T132557054922Z:ad447307c9b99c354023f77d625a2babf8f55a3d`
- publication_backlog: urgent
- publication_guidance: 29 local commit(s) waiting for governed push once the current slice is checkpoint-clean.

### Reviewer runtime
- reviewer_mode: `active_dual_agent`
- reviewer_freshness: unknown
- reviewer_publish_clear: False
- interaction_mode: `local_terminal`

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

Range: last 25 commits ending at `95131e800ca7`

- commits: 25
- files changed: 7
- insertions: +1227
- deletions: -1114
- bundle classes touched: docs, tooling
- authority surfaces touched: 1 file(s)

### Commits

| # | SHA | Subject | Files | +/- | Bundle | Risk |
|---|---|---|---|---|---|---|
| 1 | `95131e80` | Refresh external review snapshot for 818e4692 | 2 | +53/-56 | docs |  |
| 2 | `818e4692` | Fix regression test per Codex rev_pkt_1403: assert real fie… | 1 | +71/-17 | tooling |  |
| 3 | `e61fb65c` | Refresh external review snapshot for 3d14a22a | 2 | +50/-47 | docs |  |
| 4 | `3d14a22a` | SYSTEM_MAP.md v7.1 — §9 coverage refreshed 22%->37% + dogfo… | 1 | +6/-5 | docs |  |
| 5 | `c762e1c0` | Refresh external review snapshot for 6944d2c9 | 2 | +48/-54 | docs |  |
| 6 | `6944d2c9` | bridge.md: substantive Claude Status + Ack for rev 66a62d41… | 1 | +7/-2 | docs |  |
| 7 | `fe7cf67b` | Refresh external review snapshot for 02325c76 | 2 | +48/-46 | docs |  |
| 8 | `02325c76` | Add regression test for observer-scoped authority snapshot… | 1 | +45/-0 | tooling |  |
| 9 | `74467983` | Refresh external review snapshot for 9ac8211d | 2 | +48/-50 | docs |  |
| 10 | `9ac8211d` | SYSTEM_MAP.md v7.0 — §0.7 tier fix per Codex rev_pkt_1397 s… | 1 | +2/-1 | docs |  |
| 11 | `c52d7972` | Refresh external review snapshot for 902b39af | 2 | +67/-52 | docs |  |
| 12 | `902b39af` | rev_pkt_1366 FULL close per Codex rev_pkt_1396 directive | 2 | +5/-2 | tooling |  |
| 13 | `908b0c97` | Refresh external review snapshot for 17d68365 | 2 | +58/-63 | docs |  |
| 14 | `17d68365` | SYSTEM_MAP.md v6.9 — revert §54 per operator: SYSTEM_MAP is… | 2 | +52/-87 | tooling |  |
| 15 | `3dc695bc` | Refresh external review snapshot for 096df5bf | 2 | +61/-61 | docs |  |
| 16 | `096df5bf` | SYSTEM_MAP.md v6.8 — §54 Active Joint Work coordination sur… | 2 | +89/-50 | tooling |  |
| 17 | `635c1a23` | Refresh external review snapshot for 93e96fc6 | 2 | +64/-65 | docs |  |
| 18 | `93e96fc6` | rev_pkt_1366: status.py passes caller_role='observer' to pr… | 2 | +54/-52 | tooling |  |
| 19 | `74c99383` | Refresh external review snapshot for 6d4ca720 | 2 | +61/-62 | docs |  |
| 20 | `6d4ca720` | SYSTEM_MAP.md v6.7 — fix 2 errors from rev_pkt_1380 (spine… | 2 | +61/-56 | tooling |  |
| 21 | `4248a857` | Refresh external review snapshot for 2a84010d | 2 | +55/-61 | docs |  |
| 22 | `2a84010d` | SYSTEM_MAP.md v6.6 — §51 row #11: typed state-transition re… | 2 | +55/-50 | tooling |  |
| 23 | `dfd27e61` | Refresh external review snapshot for 2e8db252 | 2 | +60/-62 | docs |  |
| 24 | `2e8db252` | SYSTEM_MAP.md v6.5 — rev_pkt_1375: remove last imperative "… | 3 | +52/-47 | docs |  |
| 25 | `13d57c1f` | SYSTEM_MAP.md v6.4 — rev_pkt_1374 correction: §0.6/§0.7 ove… | 2 | +55/-66 | tooling |  |

### Files

| Path | Bundle | +/- |
|---|---|---|
| `bridge.md` | docs | +64/-64 |
| `dev/audits/REVIEW_SNAPSHOT.md` | tooling | +978/-977 |
| `dev/guides/SYSTEM_MAP.md` | docs | +62/-52 |
| `dev/scripts/devctl/commands/review_channel/reviewer_runtime_snapshot.py` | tooling | +4/-2 |
| `dev/scripts/devctl/commands/review_channel/status.py` | tooling | +2/-2 |
| `dev/scripts/devctl/review_channel/projection_bundle.py` | tooling | +1/-0 |
| `dev/scripts/devctl/tests/review_channel/test_status_observer_scope.py` | tooling | +116/-17 |

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

- **authority_surface**: Typed authority surface touched (`dev/scripts/devctl/commands/review_channel/reviewer_runtime_snapshot.py`) — Review contract-level invariants for this file

### Suggested verification commands

- `python3 dev/scripts/devctl.py check --profile ci`
- `python3 dev/scripts/devctl.py probe-report --format md`
- `python3 dev/scripts/devctl.py docs-check --strict-tooling`
- `python3 dev/scripts/devctl.py governance-review --format md`
- `python3 dev/scripts/devctl.py check-router --format md`

## 7. Reasoning — why these changes landed

### Per-commit rationale

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
- **`74c99383`** — Refresh external review snapshot for 6d4ca720
  - evolution: Fact: the next live Codex+Claude remote-control pass exposed a narrower defect than "the heartbeat is stale." Event-backed packet posting already updated the typed queue immediately, but the actual reviewer wake lived o…
- **`6d4ca720`** — SYSTEM_MAP.md v6.7 — fix 2 errors from rev_pkt_1380 (spine order + §40 role hardcode)
  - Codex rev_pkt_1380 caught 3 follow-up errors. 2 are in my dashboard surface
  - and fixed here:
  - evolution: Fact: the next live Codex+Claude remote-control pass exposed a narrower defect than "the heartbeat is stale." Event-backed packet posting already updated the typed queue immediately, but the actual reviewer wake lived o…
- **`4248a857`** — Refresh external review snapshot for 2a84010d
  - evolution: Fact: the next live Codex+Claude remote-control pass exposed a narrower defect than "the heartbeat is stale." Event-backed packet posting already updated the typed queue immediately, but the actual reviewer wake lived o…
- **`2a84010d`** — SYSTEM_MAP.md v6.6 — §51 row #11: typed state-transition reasons + auto-chain (operator finding 2026-04-19)
  - evolution: Fact: the next live Codex+Claude remote-control pass exposed a narrower defect than "the heartbeat is stale." Event-backed packet posting already updated the typed queue immediately, but the actual reviewer wake lived o…
- **`dfd27e61`** — Refresh external review snapshot for 2e8db252
  - evolution: Fact: the next live Codex+Claude remote-control pass exposed a narrower defect than "the heartbeat is stale." Event-backed packet posting already updated the typed queue immediately, but the actual reviewer wake lived o…
- **`2e8db252`** — SYSTEM_MAP.md v6.5 — rev_pkt_1375: remove last imperative "must" from §0.7
  - Codex rev_pkt_1375 Finding 1: v6.4 still had imperative "tier 3 must be
  - updated" language on §0.7 line 94, which reads as enforced contract even
  - though no check_* enforces it. Same class of error as rev_pkt_1374 caught
  - evolution: Fact: the next live Codex+Claude remote-control pass exposed a narrower defect than "the heartbeat is stale." Event-backed packet posting already updated the typed queue immediately, but the actual reviewer wake lived o…
- **`13d57c1f`** — SYSTEM_MAP.md v6.4 — rev_pkt_1374 correction: §0.6/§0.7 overstate discoverability
  - Codex rev_pkt_1374 caught the exact modeling-truth vs load-bearing-truth
  - anti-pattern operator warned about (feedback_modeling_vs_load_bearing.md):
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

Projection produced by `devctl review-snapshot`. Generation stamp `snap-50b9446cef16` binds this file to HEAD `95131e800ca7`; if they drift, the freshness guard will fail CI. When the latest commit only refreshes this generated snapshot, the guard accepts this file as bound to that commit's parent code state.
