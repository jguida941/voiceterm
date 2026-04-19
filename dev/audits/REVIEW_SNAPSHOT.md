# VoiceTerm — Review Snapshot

> Deterministically generated from typed governance state. Do not edit by hand — rerun `devctl review-snapshot --write`.

## Quick status

- Branch: `feature/governance-quality-sweep`
- HEAD: `dfd27e61a21c` — Refresh external review snapshot for 2e8db252
- Tree hash: `2e884e77ee41`
- Generation stamp: `snap-9be7ded0dd82`
- Generated at (UTC): 2026-04-19T21:05:38Z
- Push decision: `await_checkpoint` — staged_index_present
- Reviewer mode: `active_dual_agent` (interaction: `local_terminal`)
- Pipeline state: `n/a` (approval: `n/a`)
- Delta since last snapshot: 25 commits, 3 files, +2320/-1007
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
- HEAD SHA: `dfd27e61a21c7960a12b1eb27ec191e87eff621a`
- HEAD author: Justin Guida
- HEAD timestamp (UTC): 2026-04-19T17:02:28-04:00

## 2. Governance state

### Push decision
- action: `await_checkpoint`
- reason: staged_index_present
- push_eligible_now: False
- worktree_clean: False
- staged_path_count: 1
- unstaged_path_count: 0
- next_step_command: `python3 dev/scripts/devctl.py review-channel --action status --terminal none --format json`
- latest_push_report: `dev/reports/push/latest.json`
- latest_push_report_state: `blocked` (validation_failed)
- current_push_authorization: `push-auth-20260419T184040545919Z` (valid=False)
- authorized_head_commit: `92b17e69456d8959e36d6091fa6a6f0a23c85844`
- approved_target_identity: `tree-receipt-20260419T132557054922Z:ad447307c9b99c354023f77d625a2babf8f55a3d`
- publication_backlog: urgent
- publication_guidance: 7 local commit(s) waiting for governed push once the current slice is checkpoint-clean.

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
- advisory: `checkpoint_before_continue` — dirty_after_local_checkpoint

## 3. Delta — what changed since the previous snapshot

Range: last 25 commits ending at `dfd27e61a21c`

- commits: 25
- files changed: 3
- insertions: +2320
- deletions: -1007
- bundle classes touched: docs, tooling

### Commits

| # | SHA | Subject | Files | +/- | Bundle | Risk |
|---|---|---|---|---|---|---|
| 1 | `dfd27e61` | Refresh external review snapshot for 2e8db252 | 2 | +60/-62 | docs |  |
| 2 | `2e8db252` | SYSTEM_MAP.md v6.5 — rev_pkt_1375: remove last imperative "… | 3 | +52/-47 | docs |  |
| 3 | `13d57c1f` | SYSTEM_MAP.md v6.4 — rev_pkt_1374 correction: §0.6/§0.7 ove… | 2 | +55/-66 | tooling |  |
| 4 | `1ca1b8ac` | Refresh external review snapshot for 48becbeb | 2 | +62/-110 | docs |  |
| 5 | `48becbeb` | SYSTEM_MAP.md v6.3 — fix 3 errors flagged by Codex rev_pkt_… | 2 | +56/-55 | tooling |  |
| 6 | `82c0d4bc` | Refresh external review snapshot for 18034f22 | 2 | +60/-55 | docs |  |
| 7 | `18034f22` | SYSTEM_MAP.md v6.2 — compact Runtime Spine at top + Authori… | 2 | +121/-97 | tooling |  |
| 8 | `cb5214c8` | Refresh external review snapshot for 8a8ef059 | 2 | +59/-57 | docs |  |
| 9 | `8a8ef059` | SYSTEM_MAP.md v6.1 — sections 48-53 + governance-first §0.5… | 1 | +233/-7 | docs |  |
| 10 | `331c7ff2` | Refresh external review snapshot for a7e9e127 | 2 | +51/-50 | docs |  |
| 11 | `a7e9e127` | SYSTEM_MAP.md §47 — doc sprawl (60 top-level orientation MD… | 1 | +71/-0 | docs |  |
| 12 | `d7168933` | Refresh external review snapshot for b16d5d3b | 2 | +45/-44 | docs |  |
| 13 | `b16d5d3b` | SYSTEM_MAP.md v6 — 10 gap-audit sections added per external… | 1 | +320/-0 | docs |  |
| 14 | `548401c3` | Refresh external review snapshot for 01830a05 | 2 | +53/-62 | docs |  |
| 15 | `01830a05` | Fix SYSTEM_MAP.md per Codex rev_pkt_1358/1360 + prep for ex… | 1 | +11/-5 | docs |  |
| 16 | `0fb9dda6` | Refresh external review snapshot for 4dc05995 | 2 | +51/-46 | docs |  |
| 17 | `4dc05995` | SYSTEM_MAP.md v5 — operator override on Codex rev_pkt_1354… | 1 | +259/-2 | docs |  |
| 18 | `da2a7aec` | Refresh external review snapshot for ce1d75b4 | 2 | +55/-52 | docs |  |
| 19 | `ce1d75b4` | Fix SYSTEM_MAP.md per Codex rev_pkt_1353/1356 re-review | 1 | +8/-6 | docs |  |
| 20 | `27fc2d73` | Refresh external review snapshot for e19c5551 | 2 | +60/-59 | docs |  |
| 21 | `e19c5551` | Expand SYSTEM_MAP.md sections 22-29 from third 8-agent sweep | 1 | +186/-0 | docs |  |
| 22 | `983d3381` | Refresh external review snapshot for 995559a8 | 2 | +57/-57 | docs |  |
| 23 | `995559a8` | Fix SYSTEM_MAP.md per Codex review (rev_pkt_1348) | 1 | +36/-18 | docs |  |
| 24 | `6b0bcba1` | Refresh external review snapshot for 3c59b601 | 2 | +56/-50 | docs |  |
| 25 | `3c59b601` | Expand SYSTEM_MAP.md sections 14-21 from second 8-agent swe… | 1 | +243/-0 | docs |  |

### Files

| Path | Bundle | +/- |
|---|---|---|
| `bridge.md` | docs | +48/-48 |
| `dev/audits/REVIEW_SNAPSHOT.md` | tooling | +858/-915 |
| `dev/guides/SYSTEM_MAP.md` | docs | +1414/-44 |

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

### Suggested verification commands

- `python3 dev/scripts/devctl.py check --profile ci`
- `python3 dev/scripts/devctl.py probe-report --format md`
- `python3 dev/scripts/devctl.py docs-check --strict-tooling`
- `python3 dev/scripts/devctl.py check-router --format md`

## 7. Reasoning — why these changes landed

### Per-commit rationale

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
- **`331c7ff2`** — Refresh external review snapshot for a7e9e127
  - evolution: Fact: the next live Codex+Claude remote-control pass exposed a narrower defect than "the heartbeat is stale." Event-backed packet posting already updated the typed queue immediately, but the actual reviewer wake lived o…
- **`a7e9e127` | MPs: MP-388** — SYSTEM_MAP.md §47 — doc sprawl (60 top-level orientation MDs) + consolidation roadmap
  - Operator 2026-04-19 evening: 'I cannot have 50 fucking different MDs. This
  - needs to be addressed in the system plan.'
  - evolution: Fact: the next live Codex+Claude remote-control pass exposed a narrower defect than "the heartbeat is stale." Event-backed packet posting already updated the typed queue immediately, but the actual reviewer wake lived o…
- **`d7168933`** — Refresh external review snapshot for b16d5d3b
  - evolution: Fact: the next live Codex+Claude remote-control pass exposed a narrower defect than "the heartbeat is stale." Event-backed packet posting already updated the typed queue immediately, but the actual reviewer wake lived o…
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

Projection produced by `devctl review-snapshot`. Generation stamp `snap-9be7ded0dd82` binds this file to HEAD `dfd27e61a21c`; if they drift, the freshness guard will fail CI. When the latest commit only refreshes this generated snapshot, the guard accepts this file as bound to that commit's parent code state.
