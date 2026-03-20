# AI Governance Platform -- Consolidated Architecture Specification

**Version**: 1.0  |  **Date**: 2026-03-19  |  **Status**: Draft reference
**Decision source**: Final contract/sequencing decisions live in
`dev/active/ai_governance_platform.md` and
`dev/active/platform_authority_loop.md`.
**Authority**: This document is a consolidated reference for the portable AI
governance platform extracted from VoiceTerm under MP-377. When a simplified
statement here conflicts with the active-plan docs, the active-plan docs win.
**Execution spec**: `dev/active/platform_authority_loop.md`
**Product plan**: `dev/active/ai_governance_platform.md`
**Engine companion**: `dev/active/portable_code_governance.md`

This specification is a consolidated reference, not a second execution
authority. Use it for the full-system picture, then confirm the active-plan
docs for the current `P0`/`P1` contract boundary and execution order.

## Final-plan review adjustments

The 2026-03-19 final-plan review accepted several directions from the broader
architecture draft and rejected a few premature simplifications:

- accepted now: one startup-authority path, fail-closed auto-resume,
  stale-state auto-demotion, bridge-as-projection, and replayable
  single-agent vs multi-agent proof-pack benchmarking
- not accepted for current `P0`/`P1`: merging `WorkIntakePacket` and
  `CollaborationSession`, replacing intake-backed writer authority with
  optimistic concurrency alone, or reducing `PlanTargetRef` to heading-only
  targeting
- current next slice: generated `project.governance.json` + `PlanRegistry`,
  `startup-context` / `WorkIntakePacket`, `CollaborationSession`
  projection materialization, repo-pack activation, and Phase 5a
  evidence-identity freeze

---

## 1. Product Thesis

Prompt instructions are useful, but executable local control is what makes
AI-assisted engineering reliable. This platform enforces code quality through
commands, policies, tests, typed actions, and evidence artifacts that run the
same way every time. The AI can suggest, explain, draft, and repair, but the
environment owns the deterministic contract.

The target product is one platform with five layers, callable from any repo
without VoiceTerm-specific assumptions:

| Layer | Contents |
|---|---|
| `governance_core` | Guards, probes, policy resolution, export, bootstrap, review ledger, measurement schemas, artifact generation |
| `governance_runtime` | Typed control state, action execution, loop orchestration, repo sessions, queueing, artifact-store contracts |
| `governance_adapters` | Provider (Codex/Claude/etc), CI/workflow, VCS, notifier, local-environment capability detection |
| `governance_frontends` | CLI (devctl), PyQt6 operator console, overlay/TUI (VoiceTerm), phone/mobile, MCP adapter |
| `repo_packs` | Per-repo policy, workflow defaults, docs templates, bounded repo-local guard/lane wiring |

VoiceTerm sits above all five layers as the first consumer and optional rich
operator shell, not as the backend.

---

## 2. The Universal Contract Chain

Every governed session -- whether single-agent, multi-agent, or human-only --
flows through one authority chain. This is the canonical spine of the platform:

```text
project.governance.json
        |
        v
    RepoPack
        |
        v
  PlanRegistry
        |
        v
  PlanTargetRef
        |
        v
 WorkIntakePacket
        |
        v
 CollaborationSession
        |
        v
   TypedAction
        |
        v
 ActionResult / RunRecord / Finding
        |
        v
  ContextPack
```

### Chain semantics

| Node | What it does | Key fields |
|---|---|---|
| `project.governance.json` | Declares repo identity and platform configuration. Machine-readable; `project.governance.md` is the human-reviewed companion | repo_identity, repo_pack_id, path_roots, plan_registry, artifact_roots, memory_roots, bridge_mode, guard_probe_enablement, bundle_overrides |
| `RepoPack` | Runtime-loaded repo configuration. Replaces VoiceTerm fallback globals | repo_pack_id, platform_version_requirement, RepoPathConfig (37 fields), policy, workflow defaults, docs templates |
| `PlanRegistry` | Typed map of active plans, scopes, roles, execution authority. Replaces prose-scraping of MASTER_PLAN.md / INDEX.md | plan_entries[], scope_map, role_assignments, execution_authority, JSON twin of markdown authority |
| `PlanTargetRef` | Versioned locator for mutable reviewed plan targets | plan_id, scope, target_doc_path, target_kind, anchor_refs, target_revision |
| `WorkIntakePacket` | Bounded startup/work-routing envelope that selects target, routing, and write authority | intake_id, selected_target_ref, changed_scope, command_goal, routed_bundle, writer_lease, accepted_outcome_sinks |
| `CollaborationSession` | Live shared-work projection over intake + review/runtime state | session_id, intake_ref, reviewer_mode, current_slice, findings, responses, delegated_receipts, ready_gates |
| `TypedAction` | Explicit command contract for check/probe/bootstrap/fix/report/export/review/remediation | action_id, goal_taxonomy, inputs, routed_bundle, target_refs |
| `Finding` | Canonical evidence record shared by guards, probes, imports, and review ledger | schema_version, finding_id, rule_id, rule_version, severity, file_path, evidence, provenance (see Section 8) |
| `ContextPack` | Portable, schema-versioned context bundle for AI consumption | schema_version, pack_id, repo_identity, source_refs, summaries, prioritization, estimated_size, cost_fields |

### Locked decisions carried into this reference

1. **`WorkIntakePacket` and `CollaborationSession` stay separate** through the
   current `P0`/`P1` authority-loop closure. Intake is the bounded startup /
   routing / write-authority envelope; collaboration session is the mutable
   shared-work projection over intake plus review/runtime state.

2. **Intake-backed writer leases are primary authority** for canonical
   plan/session mutation. `expected_revision`, `version_counter`, and
   `state_hash` are supplemental freshness and stale-read checks, not
   replacements for designated writer ownership.

3. **`PlanTargetRef` starts with registry-generated anchor ids**, not
   heading-only targeting. The initial grammar is already
   `section:<id>|checklist:<id>|session_resume:<id>|progress:<id>|audit:<id>`,
   with collision-free ids and fail-closed resolution.

4. **Bridge (`code_audit.md`) is a projection**, not a second authority. The
   write authority remains the intake/session/runtime path; the markdown bridge
   is a human-readable projection over that state.

---

## 3. PlanTargetRef

PlanTargetRef is a versioned locator for canonical plan authority targets.

### Initial implementation (Phases 1-3)

```text
PlanTargetRef:
    plan_id:          str     # which plan document
    scope:            str     # MP scope or sub-scope
    target_doc_path:  str     # canonical reviewed markdown authority
    target_kind:      enum    # section | checklist_item | session_resume | progress_log | audit_evidence
    anchor_refs:      list[str]
    target_revision:  str     # expected revision/hash of the reviewed target
    content_hash:     str     # drift-detection hash for the resolved content
```

The `anchor_refs` grammar is part of the initial contract, not a later add-on:

```text
section:<id> | checklist:<id> | session_resume:<id> | progress:<id> | audit:<id>
```

Registry-generated, collision-free machine IDs. Clients never invent IDs from
prose. Ambiguity or missing highest-precedence anchors fail closed.

Phase-1 prerequisite note:

- Freeze the anchor grammar and collision-free id-generation rules before
  `PlanRegistry` / `PlanTargetRef` implementation can count as closed. Phase 3
  consumes that grammar; it does not get to invent it.

### Allowed mutation operations per target kind

| Target kind | Allowed operations |
|---|---|
| `section` | `rewrite_section_note` |
| `checklist_item` | `set_checklist_state` |
| `session_resume` | `rewrite_session_resume` |
| `progress_log` | `append_progress_log` |
| `audit_evidence` | `append_audit_evidence` |

Machine-readable JSON twin alongside markdown is required. Runtime never
parses prose to determine plan state.

---

## 4. Intake And Collaboration Contracts

The current locked design keeps startup/work intake separate from mutable
collaboration state.

### 4.1 WorkIntakePacket

`WorkIntakePacket` is the bounded startup/work-routing envelope. It can remain
valid even when a stale `CollaborationSession` is auto-demoted and rebuilt.

```text
WorkIntakePacket:
    intake_id:                 str
    repo_identity:             str
    repo_pack_id:              str
    selected_target_ref:       PlanTargetRef | None
    changed_scope:             list[str]
    command_goal:              str
    routed_bundle:             str
    targeted_check_plan:       TargetedCheckPlan | None
    repo_map_snapshot:         RepoMapSnapshot | None
    map_focus_query:           MapFocusQuery | None
    canonical_write_authority: str
    writer_lease:
        writer_id:             str
        lease_epoch:           str
        expires_at_utc:        str | None
        stale_writer_recovery: str
    accepted_outcome_sinks:    list[str]
    restart_packet:            RestartPacket | None
    ready_gates:               list[ReadyGate]
    cache_invalidation:        CachePolicy | None
```

### 4.2 CollaborationSession

`CollaborationSession` is the live shared-work projection over one intake path
plus review/runtime state. It is mutable and may be demoted/rebuilt without
invalidating the intake contract that selected the work.

```text
CollaborationSession:
    session_id:                str
    repo_identity:             str
    repo_pack_id:              str
    intake_ref:                str
    lead_agent:                str | None
    review_agent:              str | None
    coding_agent:              str | None
    reviewer_mode:             enum    # single_agent | active_dual_agent | tools_only | paused | offline
    operator_mode:             enum    # interactive | autonomous | observe_only
    current_slice:             str
    current_instruction:       str
    findings:                  list[Finding]
    responses:                 list[FindingResponse]
    disagreement_state:        DisagreementState | None
    arbitration_result:        ArbitrationResult | None
    delegated_receipts:        list[WorkerReceipt]
    ready_gates:               list[ReadyGate]
    expected_revision:         str | None
    version_counter:           int | None
    state_hash:                str | None
    last_writer_id:            str | None
    last_writer_timestamp:     str | None
    created_at:                str
    updated_at:                str
```

### Bridge projection

The markdown bridge (`code_audit.md`) is rendered from `CollaborationSession`
state. It
exposes a human-readable view of:

- Poll Status / Last Codex Poll
- Current Verdict
- Open Findings
- Current Instruction For Claude
- Last Reviewed Scope
- Claude Questions

The bridge is never the write authority. All state changes go through the
intake/session/runtime path. The bridge is regenerated on every authoritative
state update.

---

## 5. Writer Authority And Freshness Protocol

All agents sharing one governed slice must follow these rules to prevent stale
reads, conflicting writes, and ownership ambiguity.

### 5.1 Intake-backed writer authority

Canonical plan/session mutations require valid write authority from the active
`WorkIntakePacket` (or an explicit transferred replacement recorded through the
same authority path). If writer authority is missing, expired, mismatched, or
stale-recovery rules are not satisfied, the mutation fails closed.

### 5.2 Freshness and revision checks

`expected_revision`, `version_counter`, and `state_hash` are accepted
freshness/convergence checks when the runtime surface exposes them. They are
used to detect stale reads and force re-read/retry, but they do not grant
authority to a caller that is not the intake-selected writer.

### 5.3 Writer identity and timestamp

Every section written to the bridge or collaboration-session projection must
include:

- `writer_id`: which agent wrote it (for example `codex-reviewer`)
- `writer_timestamp`: ISO 8601 UTC time of the write

### 5.4 Mandatory re-read

Before making a decision based on intake/session state, the agent must re-read
the current authoritative state. Cached state is never authoritative.

### 5.5 Heartbeat with state hash

Each agent may emit periodic heartbeats containing:

```text
Heartbeat:
    agent_id:       str
    session_id:     str
    state_hash:     str     # hash of agent's last-read CollaborationSession state
    timestamp:      str     # ISO 8601 UTC
    status:         enum    # active | idle | waiting | stalled
```

If two agents' `state_hash` values diverge, both must pause and re-read the
canonical state before proceeding.

### 5.5 Acknowledgment Protocol

When one agent writes an instruction or finding for another agent:

1. Writer sets `ack_required: true` on the entry
2. Reader must write an explicit acknowledgment (`ack_revision` matching the
   instruction's revision) before acting on new instructions
3. If no acknowledgment arrives within the staleness threshold, the writer
   pauses and re-reads

### 5.6 Staleness Threshold

If the bridge/session `updated_at` is older than the configured threshold
(default: implementation-defined, expected 30-120 seconds for active sessions),
any reading agent must pause normal work and re-read before proceeding.

---

## 6. Startup Rules

What the platform does automatically at session start:

- Inspect the repo (read `project.governance.json`, resolve `RepoPack`)
- Refresh cached startup authority (plan registry, repo map, guard/probe state)
- Attach to or resume exactly one Session (if one valid/repairable Session
  exists for the same repo identity and target authority)
- Auto-demote stale state (expired sessions, stale bridge data)
- Emit one intake/resume packet into the Session

What the platform does NOT do automatically:

- Guess among multiple active plans (emits `ambiguous_scope` and waits)
- Launch conductors or orchestration loops without explicit choice
- Escalate to `active_dual_agent` mode without explicit operator/policy choice
- Resume when the prior Session is ambiguous or unrepairable (emits
  `stale_session` and waits)

Fail-closed rule: if startup cannot determine exactly one valid Session to
attach/resume, it stops and asks rather than guessing.

---

## 7. Execution Phases

### Phase dependency graph

```text
Phase 0 --> Phase 1 --> [Phase 2, Phase 3, Phase 5a]  (parallel)
                                    |
                                    v
                                Phase 4
                                    |
                                    v
                                Phase 5b
                                    |
                                    v
                                Phase 6
                                    |
                                    v
                                Phase 7
                                    |
                                    v
                                Phase 8  (deferred)
```

### Phase 0: Scope Freeze and Authority Definition

- Freeze this lane as the current MP-377 P0 execution priority
- Record the universal contract chain explicitly
- Define the migration rule: monorepo packages first, separate repos only after
  boundaries are proven stable on multiple repos
- Define the proof rule: no slice counts as complete until it lands with docs,
  tests/guards, and one durable artifact a fresh session can consume

### Phase 1: Startup Authority (~2500-3000 lines new code)

**Deliverables:**

- `governance-draft` command: deterministic repo scanner that produces
  `project.governance.md` (human-reviewed) + `project.governance.json`
  (machine-readable)
- `ProjectGovernance` schema with all required fields (repo identity,
  repo-pack id, path roots, plan registry, artifact roots, memory roots,
  bridge mode, guard/probe enablement, bundle overrides)
- `startup-context` / `WorkIntakePacket` surface: bounded startup packet with
  selected target, routed bundle/check plan, writer lease, sinks, and typed
  `ambiguous_scope` / `stale_session` outcomes
- `CollaborationSession` projection: live shared-work state derived from the
  intake path plus review/runtime state
- Frozen anchor grammar for `PlanTargetRef`:
  `section:<id>|checklist:<id>|session_resume:<id>|progress:<id>|audit:<id>`
- `check_startup_authority_contract.py` guard: verifies one repo declares one
  startup authority, one active-plan registry, one tracker, and valid path
  roots
- Strict schema/format validation for human-authored plan/governance docs

**Done when:**

- This repo can emit reviewed `project.governance.md` + generated
  `project.governance.json`, a bounded `startup-context` / `WorkIntakePacket`,
  and a `CollaborationSession` projection from the same intake path
- Ambiguity and stale-resume cases fail closed as typed outcomes instead of
  guessing
- `check_startup_authority_contract.py` is green and covered by focused tests

**Key decisions:**

- Machine runtime authority comes from typed contracts and generated JSON, never
  from prose parsing
- Markdown remains the human-facing reviewed surface
- Writer-lease semantics for planning review are frozen here (not Phase 4) so
  `plan_gap_review` / `plan_patch_review` can safely mutate canonical plans
- Anchor grammar freeze is a Phase-1 deliverable and a Phase-3 prerequisite

### Phase 2: RepoPack Runtime Activation (parallel with 3, 5a)

**Deliverables:**

- Runtime-loaded `RepoPack` / `RepoPathConfig` replacing VoiceTerm fallback
  globals
- Compatibility-first rollout: `get_repo_pack()` coexists with old defaults
  during migration
- Dependency injection pattern: top-level commands, service constructors, and
  helper entrypoints accept `RepoPack` explicitly. Module-level frozen defaults
  and hidden global path lookup are banned
- `check_repo_pack_activation.py` guard: fails if declared non-VoiceTerm packs
  still resolve VoiceTerm defaults
- `check_frozen_path_config_imports.py` guard: advisory first, then blocking
  after call sites are migrated

**First migration batch:**

- startup/governance bootstrap surfaces
- review-channel runtime/projection surfaces
- MP-359 Operator Console snapshot/logging/review loaders
- shared path helpers directly used by those surfaces

**Done when (first batch):**

- Those first-batch surfaces run through explicit `RepoPack` /
  `RepoPathConfig`
- `check_repo_pack_activation.py` is green for the batch
- Compatibility mode remains in place for untouched callers while later
  batches migrate the remaining `active_path_config()` call sites

### Phase 3: Typed Plan Registry (parallel with 2, 5a)

**Deliverables:**

- `PlanRegistry` contract mapping active plans, scopes, roles, execution
  authority
- Machine-readable JSON twin alongside markdown plan documents
- `PlanTargetRef` with registry-generated anchor refs + target revision
- Anchor-ID normalization/uniqueness: registry generates collision-free IDs
  for duplicate headings, repeated checklist text, append-only log rows

**Prerequisite:**

- Phase-1 anchor grammar freeze lands before registry generation is treated as
  closed

**Replaces:**

- `plan_resolution.py` prose-scraping (205 lines)
- `promotion.py` prose-scraping (301 lines)
- Line-number or context-based plan targeting in bridge/proposal flows

### Phase 4: First Runtime Slice (after 2, 3, 5a)

**First candidate:** `review-channel-status` (not swarm)

**Deliverables:**

- One command routed fully through `TypedAction -> ActionResult -> RunRecord`
- Provider inference (`codex`/`claude` labels) moved behind `ProviderAdapter`
  abstractions
- `_compat` removed from the first slice's canonical path
- Freshness/revision checks for stale-read rejection without replacing
  intake-backed writer authority
- Review/control state machine: valid states, transitions, degraded modes,
  recovery, receipts
- `check_runtime_contract_adoption.py` guard

**Key decisions:**

- Portable review identity frozen only after Phase 5a unifies stable identity
  inputs
- Single-reviewer is the first implementation; multi-reviewer topology is
  defined but deferred
- Planning review (`plan_gap_review`, `plan_patch_review`, `plan_ready_gate`)
  reuses the review-channel packet transport

### Phase 5a: Evidence Identity Freeze (parallel with 2, 3)

**Deliverables:**

- Backfill 107 legacy governance-review rows in
  `dev/reports/governance/finding_reviews.jsonl` with `schema_version`
- Unified `finding_id` scheme across guard + probe + external sources (stable
  repo identity + repo-relative path, not checkout-path-based)
- `upgrade_governance_review_row()` migration function
- Backward-compatible reader that infers legacy v1 rows during compatibility
  window
- Defined compatibility window, rollback path, and cutover rule before Phase 4
  freezes portable review identity

**Must be green before Phase 4 freezes runtime review identity.**

### Phase 5b: Evidence and Provenance Closure (after Phase 4)

**Provenance fields (required everywhere):**

| Field | Purpose |
|---|---|
| `rule_id` | Which guard/probe/rule produced this finding |
| `rule_version` | Version of that rule |
| `source_command` | Which devctl command invoked the check |
| `repo_pack_id` | Which repo pack was active |
| `policy_hash` | Hash or version of the active policy |
| `run_id` | Which execution run produced this evidence |

**Cost telemetry fields (where provider/runtime can supply):**

| Field | Purpose |
|---|---|
| `model_id` | Which AI model was used |
| `token_count` | Tokens consumed |
| `context_budget` | Context window budget |
| `cost_usd` | Estimated cost (or explicit unavailable marker) |

**Ledger integrity:**

- Malformed-row handling (detect, quarantine, report)
- Retention and repair policy
- Refresh-ledger/storage contract for cached repo intelligence
- Explicit failure behavior when evidence would otherwise be lost silently

**Aggregate governance surfaces:**

- `master-report`: consolidated platform quality report
- `converge`: meta-findings over guard/probe/CI/exception/evidence completeness
- Direct test coverage required for all authority-loop guards/checks

### Phase 6: ContextPack and Memory Boundary (after Phase 5b)

**Deliverables:**

- Portable `ContextPack` contract with schema version, stable IDs, repo
  identity, provenance, bounded references
- Memory as a provider/store behind the contract (not `.voiceterm/` paths)
- Bidirectional bridge: governance evidence writes into memory substrate,
  startup/master-report/packet-outcome ingestion reads back out
- `check_context_pack_contract.py` guard

### Phase 7: Packaging and Cross-Repo Proof (after Phase 6)

**Proof requirements:**

- Two repositories with different layouts
- No core-engine patches between adoptions
- Portable and language-appropriate guards/probes pass
- Repo-structure guards are optional (skipped via `--adoption-scan`)
- Repo-pack activation is explicit in receipts

**Minimum non-VoiceTerm bootstrap set:**

- One reviewed governance contract (`project.governance.md`/`.json`)
- One active-plan registry export
- At least one canonical plan authority document
- Exported `PlanTargetRef` targets
- One bounded `startup-context` / `WorkIntakePacket`
- One `CollaborationSession` projection

**Proof-pack schema:**

- Replayable evaluation corpus
- Benchmark runner
- Context-cost telemetry
- Adjudicated external findings
- Cache-first startup artifacts
- Reviewer-readable quality-to-cost comparisons

### Phase 8: Deferred Follow-Ons

- Plugin/entrypoint-based guard/probe/bundle discovery
- Extension/adopter conformance packs
- Multi-reviewer, skill routing, remote/cloud coordination
- Language packs (Java, Go, TypeScript)
- Cross-repo/federated governance
- Full anchor grammar for PlanTargetRef

---

## 8. Finding Contract (Canonical Evidence Record)

Every evidence record in the system -- guard output, probe output, external
import, review decision -- materializes as a `Finding` or derives from one.

```text
Finding:
    schema_version:     int
    contract_id:        str     # "Finding"
    finding_id:         str     # stable identity (repo_identity + repo-relative path + rule_id + content hash)
    signal_type:        str     # guard | probe | import | review
    check_id:           str
    rule_id:            str
    rule_version:       int
    repo_name:          str
    repo_path:          str     # repo-relative, never checkout-absolute
    file_path:          str
    symbol:             str
    line:               int
    end_line:           int
    severity:           str     # critical | high | medium | low | info
    risk_type:          str
    review_lens:        str
    ai_instruction:     str
    signals:            list[str]
    evidence:           str
    rationale:          str
    suggested_fix:      str
    autofixable:        bool
    suppression:        SuppressionMetadata | None
    source_command:     str
    source_artifact:    str

    # Provenance (Phase 5b)
    repo_pack_id:       str
    policy_hash:        str
    run_id:             str
    model_id:           str | None
    token_count:        int | None
    context_budget:     int | None
    cost_usd:           float | None
```

Related contracts:

- `DecisionPacket`: review decision on a Finding (accept/defer/suppress/dispute)
- `ActionResult`: canonical command/service result envelope
- `RunRecord`: durable record for one governed execution episode
- `ProbeReport`, `ReviewPacket`, `ReviewTargets`, `FileTopology`,
  `ProbeAllowlist`: typed artifact contracts with schema metadata

---

## 9. Single-Agent vs Multi-Agent Testing Framework

The platform must prove that multi-agent governance (coder + reviewer) produces
measurably better results than single-agent governance. This is not assumed --
it is measured.

### Test methodology

- **Corpus**: same set of tasks, same guards, same repo state
- **Configurations**: single agent vs coder + reviewer (active_dual_agent)
- **Metrics captured per configuration:**

| Metric | What it measures |
|---|---|
| Finding count delta | Are more real issues caught? |
| Severity distribution | Are the findings higher-signal? |
| False-positive rate | Does multi-agent produce noise? |
| Token cost | What is the context/cost overhead? |
| Time-to-disposition | How fast are findings reviewed? |
| Repair-loop count | How many fix cycles before green? |

### ImprovementDelta comparison

```text
ImprovementDelta:
    config_a:               str     # e.g., "single_agent"
    config_b:               str     # e.g., "active_dual_agent"
    finding_count_delta:    int
    severity_distribution:  dict[str, int]
    false_positive_rate:    float
    token_cost_delta:       int
    time_to_disposition:    float
    repair_loop_delta:      int
```

Phase 7 proof-pack must include this comparison across configurations.
A zero false-positive rate is not a success metric on its own -- read it
together with coverage, per-family disposition mix, and time-to-disposition.

---

## 10. Current System Inventory (Audit Baseline)

These numbers ground the specification in the actual codebase as of
2026-03-19:

| Metric | Count | Notes |
|---|---|---|
| Hard guards | 64 | 37 portable, 30 configurable, 16 coupled to VoiceTerm |
| Review probes | 27 | 100% portable |
| devctl commands | 65 | 22 subsystems |
| Review channel files | 54 | 48 portable |
| `active_path_config()` call sites | 51 | Must migrate to explicit DI (Phase 2) |
| `RepoPathConfig` fields | 37 | Runtime-loaded, not frozen globals |
| Legacy ledger rows without `schema_version` | 107 | Must backfill (Phase 5a) |
| `.voiceterm` path references | ~15 | Must migrate to repo-pack roots (Phase 2) |
| Operator Console Python files | 161 | 23 direct devctl imports |
| Policy-enabled hard guards | 32 | Active enforcement surface |
| Policy-enabled review probes | 23 | Active advisory surface |

---

## 11. Guard Architecture

Guards are the enforcement backbone. They split into three families:

### Guard families

| Family | Scope | Portable? | Phase 7 behavior |
|---|---|---|---|
| **Portable/core** | Code structure, duplication, complexity, naming | Yes | Must pass in any adopter repo |
| **Language-aware** | Rust function length, Python function length, etc. | Yes (per-language) | Pass if language applies |
| **Repo-structure** | AGENTS.md presence, MASTER_PLAN.md format, docs templates | No (VoiceTerm-specific) | Skipped via `--adoption-scan` |

### Guard configurability

- `project.governance.json` can declare enabled guard/probe IDs, bundle
  overrides, and repo-local routing
- Hardcoded defaults remain only as backward-compatible fallback
- Plugin/entrypoint discovery deferred to Phase 8
- Guard exceptions tracked with owner, expiry date, and follow-up MP reference

### Guard limits (CI enforcement)

| Limit | Value |
|---|---|
| Rust function length | max 100 lines |
| Python function length | max 150 lines |
| Duplicated function bodies | identical normalized bodies >= 6 lines blocked |
| Rust file size | soft 900 / hard 1400 lines |
| Python file size | soft 350 / hard 650 lines |

---

## 12. Definition of Done

The platform authority loop is complete when all 17 items are green:

| # | Criterion | Phase |
|---|---|---|
| 1 | Repo boots from `project.governance.md`/`.json` | 1 |
| 2 | Real repo-pack loads without VoiceTerm fallback | 2 |
| 3 | Plans resolve from typed registry, not prose scraping | 3 |
| 4 | One runtime slice through typed contracts end-to-end (`TypedAction -> ActionResult -> RunRecord`) | 4 |
| 5 | Unified finding/evidence identity (stable repo identity + repo-relative paths) | 5a |
| 6 | Schema-versioned context pack | 6 |
| 7 | Second repo works without core-engine patches | 7 |
| 8 | Guards discoverable via config (`project.governance.json`) | 2 |
| 9 | Bundles customizable per-repo | 2 |
| 10 | Finding provenance traces to guard + policy + run | 5b |
| 11 | Provider naming only in adapters (no `codex`/`claude` in canonical runtime) | 4 |
| 12 | `.voiceterm` roots replaced with repo-pack-declared paths | 2 |
| 13 | Cost telemetry captured (`model_id`, `token_count`, `context_budget`, `cost_usd`) | 5b |
| 14 | Authority-loop guards have direct test coverage | 5b |
| 15 | Legacy ledger backfilled (107 rows with `schema_version`) | 5a |
| 16 | Operator console migrated off VoiceTerm-specific path globals | 2 |
| 17 | Phase 7 proof distinguishes portable vs repo-structure guards | 7 |

---

## 13. ProjectGovernance Schema

The `project.governance.json` file is the machine-readable startup authority
for any governed repo.

```json
{
    "schema_version": 1,
    "repo_identity": "org/repo-name",
    "repo_pack_id": "voiceterm-v1",
    "repo_pack_version": "1.0.0",
    "platform_version_requirement": ">=0.1.0",

    "path_roots": {
        "active_docs": "dev/active",
        "reports": "dev/reports",
        "scripts": "dev/scripts",
        "guards": "dev/scripts/checks",
        "workflows": ".github/workflows",
        "artifacts": "dev/reports",
        "memory": ".voiceterm/memory"
    },

    "plan_registry": {
        "tracker": "dev/active/MASTER_PLAN.md",
        "index": "dev/active/INDEX.md",
        "plans": [
            {
                "plan_id": "MP-377",
                "doc": "dev/active/ai_governance_platform.md",
                "scope": "platform-extraction",
                "role": "main",
                "execution_authority": true
            }
        ]
    },

    "artifact_roots": {
        "governance_review": "dev/reports/governance",
        "probe_reports": "dev/reports/probes",
        "guard_reports": "dev/reports/guards",
        "snapshots": "dev/reports/snapshots"
    },

    "memory_roots": {
        "session_memory": ".voiceterm/memory/sessions",
        "context_cache": ".voiceterm/memory/context"
    },

    "bridge_mode": "active_dual_agent",

    "guard_probe_enablement": {
        "enabled_guards": ["code_shape", "function_duplication", "..."],
        "enabled_probes": ["concurrency", "design_smells", "..."],
        "disabled_guards": [],
        "disabled_probes": []
    },

    "bundle_overrides": {
        "bundle.runtime": {
            "extras": ["check_mobile_relay_protocol"]
        }
    }
}
```

---

## 14. CommandGoalTaxonomy

Stable grouping for canonical backend actions. Every `TypedAction` maps to
exactly one goal:

| Goal | Actions | Purpose |
|---|---|---|
| `inspect` | check, probe-report, map, quality-policy | Read-only analysis |
| `review` | review-channel, tandem-validate, governance-review | Peer review |
| `fix` | guard-run, autonomy-loop, remediation | Automated repair |
| `run` | swarm_run, autonomy-swarm | Execution loops |
| `control` | review-channel --action, orchestrate-status | State management |
| `adopt` | governance-draft, bootstrap, adoption-scan | Repo onboarding |
| `publish` | governance-export, render-surfaces | Output generation |
| `maintain` | hygiene, docs-check, converge | Maintenance |

---

## 15. Composability Rule

Every major subsystem must satisfy two tests:

1. **Standalone usefulness**: it can run from CLI, API, service, or artifact
   path on its own, in any repo
2. **Integrated usefulness**: it plugs into the shared runtime/action/state/
   evidence contracts so the full app becomes smarter without inventing a
   second backend

If a feature only works inside one client, it is not done.
If a feature only works as an isolated script with no shared contract, it is
not done either.

---

## 16. Versioning and Compatibility

### Contract versioning rules

- Every durable JSON/JSONL row family carries `schema_version`
- Every runtime/artifact payload carries `schema_version`
- Every command/service receipt carries `schema_version`
- Repo packs declare `platform_version_requirement`
- CI/bootstrap/adoption flows validate both package/runtime compatibility and
  schema-version compatibility before mutable execution

### Migration rules

- Every contract family has a documented owner, compatibility window, migration
  path, rollback path, and enforcing guard
- Legacy readers maintained during compatibility windows
- Hard schema enforcement lands only after backfill/migration is complete
- Rollback path defined and tested before cutover

---

## 17. File and Module Map

| What | Where |
|---|---|
| This spec | `dev/guides/SYSTEM_ARCHITECTURE_SPEC.md` |
| Execution tracker | `dev/active/platform_authority_loop.md` |
| Product plan | `dev/active/ai_governance_platform.md` |
| Engine companion | `dev/active/portable_code_governance.md` |
| Runtime contracts (Python) | `dev/scripts/devctl/runtime/` |
| Platform contract catalog | `dev/scripts/devctl/platform/` |
| Finding contracts | `dev/scripts/devctl/runtime/finding_contracts.py` |
| Review state models | `dev/scripts/devctl/runtime/review_state_models.py` |
| Guard scripts | `dev/scripts/checks/` |
| devctl commands | `dev/scripts/devctl/commands/` |
| Repo policy | `dev/config/devctl_repo_policy.json` |
| Quality presets | `dev/config/quality_presets/` |
| CI workflows | `.github/workflows/` |
| Rust source | `rust/src/bin/voiceterm/` |
| Operator console | `app/operator_console/` |

---

## 18. Glossary

| Term | Definition |
|---|---|
| **Authority loop** | The full chain from `project.governance.json` through `ContextPack` that makes governance portable |
| **Bridge** | `code_audit.md` -- a markdown projection of `CollaborationSession` state, never the write authority |
| **CQRS** | Command Query Responsibility Segregation -- the intake/session/runtime path is the write model, bridge is the read model |
| **Finding** | Canonical evidence record shared by all governance surfaces |
| **Guard** | Hard enforcement script (Layer 1) -- blocks merge on violation |
| **Optimistic concurrency** | Supplemental conflict/freshness detection via revision/version counters; it does not replace intake-backed writer authority |
| **Probe** | Advisory analysis script (Layer 2) -- reports risk hints, does not block |
| **Proof-pack** | Artifact bundle proving the platform works on a given repo |
| **RepoPack** | Runtime-loaded repo configuration replacing VoiceTerm globals |
| **Repo-structure guard** | Guard specific to VoiceTerm's docs/plan conventions -- not required for adopters |
| **WorkIntakePacket** | Bounded startup/work-routing envelope carrying target selection, routing, and writer authority |
| **CollaborationSession** | Live shared-work projection over intake + review/runtime state; mutable and rebuildable from a valid intake path |

---

*End of specification.*
