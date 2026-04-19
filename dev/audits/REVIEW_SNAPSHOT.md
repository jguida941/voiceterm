# VoiceTerm — Review Snapshot

> Deterministically generated from typed governance state. Do not edit by hand — rerun `devctl review-snapshot --write`.

## Quick status

- Branch: `feature/governance-quality-sweep`
- HEAD: `02325c7671dc` — Add regression test for observer-scoped authority snapshot (rev_pkt_1397 step 2)
- Tree hash: `01167f2f238c`
- Generation stamp: `snap-b092fcab06c2`
- Generated at (UTC): 2026-04-19T22:45:58Z
- Push decision: `await_review` — review_loop_relaunch_required
- Reviewer mode: `tools_only` (interaction: `local_terminal`)
- Pipeline state: `n/a` (approval: `n/a`)
- Delta since last snapshot: 24 commits, 7 files, +1535/-1268
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
- HEAD SHA: `02325c7671dc976bc0378fa768428eca5c9f538f`
- HEAD author: Justin Guida
- HEAD timestamp (UTC): 2026-04-19T18:45:31-04:00

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
- publication_backlog: urgent
- publication_guidance: 22 local commit(s) waiting for governed push once review is accepted.

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

Range: last 24 commits ending at `02325c7671dc`

- commits: 24
- files changed: 7
- insertions: +1535
- deletions: -1268
- bundle classes touched: tooling, docs
- authority surfaces touched: 1 file(s)

### Commits

| # | SHA | Subject | Files | +/- | Bundle | Risk |
|---|---|---|---|---|---|---|
| 1 | `02325c76` | Add regression test for observer-scoped authority snapshot… | 1 | +45/-0 | tooling |  |
| 2 | `74467983` | Refresh external review snapshot for 9ac8211d | 2 | +48/-50 | docs |  |
| 3 | `9ac8211d` | SYSTEM_MAP.md v7.0 — §0.7 tier fix per Codex rev_pkt_1397 s… | 1 | +2/-1 | docs |  |
| 4 | `c52d7972` | Refresh external review snapshot for 902b39af | 2 | +67/-52 | docs |  |
| 5 | `902b39af` | rev_pkt_1366 FULL close per Codex rev_pkt_1396 directive | 2 | +5/-2 | tooling |  |
| 6 | `908b0c97` | Refresh external review snapshot for 17d68365 | 2 | +58/-63 | docs |  |
| 7 | `17d68365` | SYSTEM_MAP.md v6.9 — revert §54 per operator: SYSTEM_MAP is… | 2 | +52/-87 | tooling |  |
| 8 | `3dc695bc` | Refresh external review snapshot for 096df5bf | 2 | +61/-61 | docs |  |
| 9 | `096df5bf` | SYSTEM_MAP.md v6.8 — §54 Active Joint Work coordination sur… | 2 | +89/-50 | tooling |  |
| 10 | `635c1a23` | Refresh external review snapshot for 93e96fc6 | 2 | +64/-65 | docs |  |
| 11 | `93e96fc6` | rev_pkt_1366: status.py passes caller_role='observer' to pr… | 2 | +54/-52 | tooling |  |
| 12 | `74c99383` | Refresh external review snapshot for 6d4ca720 | 2 | +61/-62 | docs |  |
| 13 | `6d4ca720` | SYSTEM_MAP.md v6.7 — fix 2 errors from rev_pkt_1380 (spine… | 2 | +61/-56 | tooling |  |
| 14 | `4248a857` | Refresh external review snapshot for 2a84010d | 2 | +55/-61 | docs |  |
| 15 | `2a84010d` | SYSTEM_MAP.md v6.6 — §51 row #11: typed state-transition re… | 2 | +55/-50 | tooling |  |
| 16 | `dfd27e61` | Refresh external review snapshot for 2e8db252 | 2 | +60/-62 | docs |  |
| 17 | `2e8db252` | SYSTEM_MAP.md v6.5 — rev_pkt_1375: remove last imperative "… | 3 | +52/-47 | docs |  |
| 18 | `13d57c1f` | SYSTEM_MAP.md v6.4 — rev_pkt_1374 correction: §0.6/§0.7 ove… | 2 | +55/-66 | tooling |  |
| 19 | `1ca1b8ac` | Refresh external review snapshot for 48becbeb | 2 | +62/-110 | docs |  |
| 20 | `48becbeb` | SYSTEM_MAP.md v6.3 — fix 3 errors flagged by Codex rev_pkt_… | 2 | +56/-55 | tooling |  |
| 21 | `82c0d4bc` | Refresh external review snapshot for 18034f22 | 2 | +60/-55 | docs |  |
| 22 | `18034f22` | SYSTEM_MAP.md v6.2 — compact Runtime Spine at top + Authori… | 2 | +121/-97 | tooling |  |
| 23 | `cb5214c8` | Refresh external review snapshot for 8a8ef059 | 2 | +59/-57 | docs |  |
| 24 | `8a8ef059` | SYSTEM_MAP.md v6.1 — sections 48-53 + governance-first §0.5… | 1 | +233/-7 | docs |  |

### Files

| Path | Bundle | +/- |
|---|---|---|
| `bridge.md` | docs | +57/-52 |
| `dev/audits/REVIEW_SNAPSHOT.md` | tooling | +1094/-1154 |
| `dev/guides/SYSTEM_MAP.md` | docs | +332/-58 |
| `dev/scripts/devctl/commands/review_channel/reviewer_runtime_snapshot.py` | tooling | +4/-2 |
| `dev/scripts/devctl/commands/review_channel/status.py` | tooling | +2/-2 |
| `dev/scripts/devctl/review_channel/projection_bundle.py` | tooling | +1/-0 |
| `dev/scripts/devctl/tests/review_channel/test_status_observer_scope.py` | tooling | +45/-0 |

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
- **`1ca1b8ac`** — Refresh external review snapshot for 48becbeb
  - evolution: Fact: the next live Codex+Claude remote-control pass exposed a narrower defect than "the heartbeat is stale." Event-backed packet posting already updated the typed queue immediately, but the actual reviewer wake lived o…
- **`48becbeb` | MPs: MP-388** — SYSTEM_MAP.md v6.3 — fix 3 errors flagged by Codex rev_pkt_1367
  - Codex review of v6.2 caught 3 real errors I introduced:
  - evolution: Fact: the next live Codex+Claude remote-control pass exposed a narrower defect than "the heartbeat is stale." Event-backed packet posting already updated the typed queue immediately, but the actual reviewer wake lived o…
- **`82c0d4bc`** — Refresh external review snapshot for 18034f22
  - evolution: Fact: the next live Codex+Claude remote-control pass exposed a narrower defect than "the heartbeat is stale." Event-backed packet posting already updated the typed queue immediately, but the actual reviewer wake lived o…
- **`18034f22`** — SYSTEM_MAP.md v6.2 — compact Runtime Spine at top + Authority Load Order
  - evolution: Fact: the next live Codex+Claude remote-control pass exposed a narrower defect than "the heartbeat is stale." Event-backed packet posting already updated the typed queue immediately, but the actual reviewer wake lived o…
- **`cb5214c8`** — Refresh external review snapshot for 8a8ef059
  - evolution: Fact: the next live Codex+Claude remote-control pass exposed a narrower defect than "the heartbeat is stale." Event-backed packet posting already updated the typed queue immediately, but the actual reviewer wake lived o…
- **`8a8ef059`** — SYSTEM_MAP.md v6.1 — sections 48-53 + governance-first §0.5 pivot
  - - §0.5 reframed governance-first: repo is a portable typed AI-governance
  -   platform; VoiceTerm is ONE adopter/product shell, not the engine
  - - §48 Portable Engine Boundary: 4-tier classification (engine / repo-pack /
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

Projection produced by `devctl review-snapshot`. Generation stamp `snap-b092fcab06c2` binds this file to HEAD `02325c7671dc`; if they drift, the freshness guard will fail CI. When the latest commit only refreshes this generated snapshot, the guard accepts this file as bound to that commit's parent code state.
