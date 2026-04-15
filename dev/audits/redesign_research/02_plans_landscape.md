# VoiceTerm / Codex-Voice: Active Plans Redesign Synthesis (2026-04-14)

## Plan Inventory

| Plan | MP-IDs | Status | Primary Scope | Overlap-With |
|------|--------|--------|---------------|--------------|
| theme_upgrade | MP-099, MP-148..151, MP-161..167, MP-172..182 | OPEN | rust/src/theme/* | operator_console, memory_studio |
| memory_studio | MP-230..255 | OPEN | runtime/memory/*, event_loop overlay UX | theme_upgrade, review_channel |
| devctl_reporting_upgrade | MP-297..300, MP-303, MP-306, MP-379 | OPEN | dev/scripts/devctl/report*, dashboard, CIHub | operator_console |
| autonomous_control_plane | MP-325..338, MP-340 | OPEN | Ralph loop, mobile control, guardrails | review_channel, continuous_swarm |
| review_channel | MP-355 | OPEN (spec) | devctl review-channel, bridge.md, shared packet contract | continuous_swarm, autonomous_control_plane, operator_console |
| host_process_hygiene | MP-356 | OPEN (follow-up) | devctl process-audit/cleanup, host PTY trees | continuous_swarm |
| continuous_swarm | MP-358 | OPEN | Codex/Claude loop launcher, bridge cycling | review_channel, host_process_hygiene |
| operator_console | MP-359 | OPEN | app/operator_console/ PyQt6 shell | theme_upgrade, devctl_reporting_upgrade, review_channel |
| loop_chat_bridge | MP-338 | OPEN (runbook) | artifact-to-chat loop evidence | autonomous_control_plane |
| naming_api_cohesion | MP-267 | OPEN (Phase 1 complete) | theme/event_loop/status_line/memory naming | review_probes (downstream tooling) |
| ide_provider_modularization | MP-346, MP-354 | OPEN (MP-354 closed, MP-346 backlog) | rust provider/IDE policy, JetBrains/Cursor detection | slash_command_standalone |
| pre_release_architecture_audit | MP-347, MP-349 | LANDING (Phases 1-7 complete) | full-surface audit, bundle DRY, CI lint, Python tooling | multiple (intake artifact) |
| slash_command_standalone | MP-352, MP-353 | OPEN | voiceterm --capture-once, voiceterm-mcp binary, /voice CLI | ide_provider_modularization |
| ralph_guardrail_control_plane | MP-360..367 | OPEN (Phase 1 landed) | ralph_ai_fix.py, guardrail config registry, ralph-report.json | review_probes, portable_code_governance |
| review_probes | MP-368..375 | OPEN (Phase 2 live) | probe_concurrency, probe_design_smells, risk_hints, probes/*.py | code_shape_expansion, ralph_guardrail_control_plane |
| portable_code_governance | MP-376 | OPEN | guard/probe engine portability, repo-pack policy, external-repo proof | ai_governance_platform, review_probes |
| ai_governance_platform | MP-377 | OPEN (main product) | typed runtime contracts, startup-context, repo-pack, extraction spec | platform_authority_loop, remote_commit_pipeline, remote_control_runtime, autonomous_governance_loop_v2 |
| platform_authority_loop | MP-377 (P0 subordinate) | OPEN | ProjectGovernance, RepoPack, PlanRegistry, WorkIntakePacket, TypedAction spine | ai_governance_platform |
| autonomous_governance_loop_v2 | MP-377 (loop composition) | OPEN | StartupContext -> PlanningIRSnapshot -> ControlPlaneReadModel -> commit/push | platform_authority_loop, remote_control_runtime |
| remote_commit_pipeline | MP-377 (governed VCS) | OPEN | typed commit/push lifecycle, RemoteCommitPipelineContract, approval | platform_authority_loop, remote_control_runtime |
| remote_control_runtime | MP-380..387 | OPEN | operator-interaction mode, headless lifecycle, dashboard projection, actor dispatch | autonomous_governance_loop_v2, remote_commit_pipeline |
| code_shape_expansion | MP-378 | OPEN (research) | new structural code-shape probes, halstead metrics, LCOM4 | review_probes (Phase 5b gate) |

**Key:** OPEN = active work, LANDED = shipped (phases), DEFERRED = moved to `dev/deferred/`, STALE = no recent activity.

---

## Scope-Overlap Matrix

**High-intensity overlaps (3+ files shared):**

1. **governance runtime core** (ai_governance_platform, platform_authority_loop, autonomous_governance_loop_v2, remote_control_runtime)
   - Shared: runtime/*.py, dev/scripts/devctl/platform/*.py, typed contracts (WorkIntakePacket, ActionResult, ReviewState)
   - Risk: cross-layer scope drift without explicit handoff docs

2. **operator surfaces** (review_channel, continuous_swarm, operator_console)
   - Shared: bridge.md, packet structures, dashboard/terminal projections
   - Risk: bridge authority inflation vs typed-contract ownership

3. **quality/review loop** (review_probes, ralph_guardrail_control_plane, portable_code_governance)
   - Shared: probe_*.py, guard_*.py, violation/finding rendering, config registry
   - Risk: probe/guard authority split not yet fully portable

4. **runtime shell** (theme_upgrade, memory_studio, operator_console)
   - Shared: rust/src/bin/voiceterm/*, overlay UX, status-line rendering
   - Risk: visual/UX consolidation needed as feature work expands

**Medium overlaps (2 files):**
- review_channel ↔ autonomous_control_plane (loop infrastructure)
- devctl_reporting_upgrade ↔ operator_console (dashboard/status projection)
- naming_api_cohesion ↔ review_probes (symbol/identifier scanners)
- ide_provider_modularization ↔ slash_command_standalone (provider abstraction)

---

## Plan Cluster Analysis

### Cluster 1: Governance Platform Core (MP-377)
**Purpose:** Extract, contract, and productize the AI governance system.  
**Plans:** ai_governance_platform, platform_authority_loop, autonomous_governance_loop_v2, portable_code_governance  
**Status:** OPEN; multiple subordinate specs with phased closure  
**Primary output:** Typed runtime contracts, portable repo-pack authority, cross-repo proof  
**Risk:** Scope inflation without explicit Phase/gate clarity

### Cluster 2: Review + Execution Surfaces (MP-355, MP-358)
**Purpose:** Unified review channel and continuous dual-agent loop.  
**Plans:** review_channel, continuous_swarm, loop_chat_bridge  
**Status:** OPEN; markdown bridge transitive (typed artifacts pending)  
**Primary output:** Shared PacketPostRequest contract, bridge cycling automation, proof-of-life harness  
**Risk:** Bridge authority bleed; typed packet contract still in transition

### Cluster 3: Remote + Phone Runtime (MP-380..387)
**Purpose:** Phone/remote-control operator surfaces over typed governance backend.  
**Plans:** remote_control_runtime, remote_commit_pipeline  
**Status:** OPEN; pending dashboard parity + actor dispatch closure  
**Primary output:** typed RemoteCommitPipelineContract, headless session lifecycle, operator-mode projection  
**Risk:** Multiple fallback/compat seams still live (bridge, review_helpers.py)

### Cluster 4: Quality Intelligence (MP-368..376, MP-378)
**Purpose:** Deterministic guards + heuristic probes + portable policy layer.  
**Plans:** review_probes, ralph_guardrail_control_plane, code_shape_expansion, portable_code_governance  
**Status:** OPEN (Phase 2 live); Phase 5b gate controls new probes  
**Primary output:** probe_*.py suite, structured risk_hints, ralph config registry, multi-repo rollout  
**Risk:** Probe/guard authority boundary not yet portable-by-default; new probes stalled until Phase 5b gates

### Cluster 5: Runtime Hardening (MP-267, MP-346, MP-347..349, MP-356)
**Purpose:** Cohesion, modularization, architecture audit, process hygiene.  
**Plans:** naming_api_cohesion, ide_provider_modularization, pre_release_architecture_audit, host_process_hygiene  
**Status:** MIXED (MP-267 Phase 1 complete; MP-347..349 Phases 1-7 landed; MP-356 follow-up open)  
**Primary output:** Unified naming, provider/IDE policy, audit remediations, host cleanup automation  
**Risk:** Pre-release audit intake needs explicit routing to platform/portable lanes

### Cluster 6: UX + Operator (MP-099, MP-230..255, MP-297..300, MP-359)
**Purpose:** Visual surfaces, memory, reporting, desktop operator console.  
**Plans:** theme_upgrade, memory_studio, devctl_reporting_upgrade, operator_console  
**Status:** OPEN (not top strategic priority; secondary to MP-377)  
**Primary output:** consolidated theme helpers, memory browser/action center, report dashboards, PyQt6 console  
**Risk:** Operator console scope bloat without stricter acceptance gates

### Cluster 7: Voice + CLI (MP-352, MP-353)
**Purpose:** Standalone slash-command voice, MCP server, hold-to-talk.  
**Plans:** slash_command_standalone  
**Status:** OPEN (Phase A deliverable)  
**Primary output:** voiceterm --capture-once, voiceterm-mcp binary, installable templates  
**Risk:** Provider-specific integration coupling if MCP not kept read-only

---

## Recommended Consolidation Targets

### Immediate (Ready now)

1. **Merge Governance Runtime Subordinates → ai_governance_platform**
   - **Target plans:** platform_authority_loop, autonomous_governance_loop_v2, remote_commit_pipeline, remote_control_runtime
   - **Rationale:** All four are phase-gated subordinate execution specs under MP-377; consolidating into the main product plan eliminates four separate registry entries and clarifies that they are not peer architecture authorities.
   - **Action:** Keep ai_governance_platform as the single tracker; move subordinate specs into subsections or a companion `platform_phases.md` reference doc.

2. **Merge quality clusters into one "Governance Quality" umbrella**
   - **Target plans:** review_probes, ralph_guardrail_control_plane, code_shape_expansion, portable_code_governance
   - **Rationale:** All four live under MP-376/MP-368..378 scope; split across four files creates navigation friction without clear authority hierarchy.
   - **Action:** Promote review_probes to main governance-quality spec (MP-368..375 authority); demote code_shape_expansion and ralph control-plane to subsections or `governance_quality_phases.md` reference.

3. **Consolidate operator surfaces into shared "Operator Runtime" plan**
   - **Target plans:** review_channel, continuous_swarm, operator_console, loop_chat_bridge
   - **Rationale:** All four project the same typed review/runtime/bridge state; split creates duplicate authority on bridge shape, packet structure, and dashboard projection.
   - **Action:** Keep review_channel as main MP-355 authority (schema + contract); move continuous_swarm, operator_console, and loop_chat_bridge to subordinate phases or `operator_runtime_surfaces.md` companion.

### Medium-term (After subordinate closure)

4. **Close pre-release audit as intake artifact, not a live plan**
   - **Target plan:** pre_release_architecture_audit (MP-347, MP-349)
   - **Rationale:** Phases 1-7 are landed; remaining phases (8-14) are deferred post-release. Keep findings routed to platform_authority_loop (path/default), remote_commit_pipeline (commit/push/override), and portable_code_governance (adopter proof) instead of as a separate ongoing plan.
   - **Action:** Archive pre_release_architecture_audit; capture any remaining findings in those three owner plans.

5. **Demote host_process_hygiene to reference doc (follow-up is thin)**
   - **Target plan:** host_process_hygiene (MP-356)
   - **Rationale:** Phase 1 complete; current follow-up is narrowly scoped to three specific blind spots. Remaining work fits as a bounded checklist within continuous_swarm or process/hygiene guard updates.
   - **Action:** Keep active until MP-356 follow-up closes; then archive to `dev/reference/`.

### Deferred/Defer

6. **Hold memory_studio, theme_upgrade as reference-only until execution resumes**
   - **Target plans:** memory_studio (MP-230..255), theme_upgrade (MP-099, MP-148..182)
   - **Rationale:** Both are architecturally sound but deprioritized while MP-377 (AI governance platform) is the main strategic lane. Keep them in `dev/active/` for navigation but clearly mark as "secondary priority."
   - **Action:** Index registry already marks these as "reference-only"; confirm no action required until explicit re-prioritization.

---

## Stale / Zombie Plans

**Plans with no recent activity or explicit pause state:**

1. **phase2.md** (DEFERRED)
   - Status: Explicit bridge pointer to `dev/deferred/phase2.md`
   - Activity signal: None visible in active registry; explicitly deferred long-range planning
   - **Action:** No action needed; correctly archived per INDEX.md protocol

2. **RUST_AUDIT_FINDINGS.md** (DEFERRED)
   - Status: Bridge pointer to canonical `dev/reports/audits/RUST_AUDIT_FINDINGS.md`
   - Activity signal: None visible in active registry; supporting context only
   - **Action:** Confirm bridge is current; if no updates in 4+ weeks, demote to reference-only

3. **audit.md, move.md** (REFERENCE)
   - Status: Supporting audit/merge evidence only; not execution authority
   - Activity signal: None visible; last updated as part of pre-release audit intake
   - **Action:** Archive to `dev/reference/audits/` after pre-release audit consolidation closes

4. **README.md** (REFERENCE)
   - Status: Navigation helper; non-tracker
   - Activity signal: Minimal; maintained with INDEX.md updates
   - **Action:** No action; keep as navigation aid

---

## Cross-Repo Portability Readiness

**Portable by design (ready for external adopter proof):**
- portable_code_governance (MP-376) — engine/policy boundary designed for external repos
- review_probes (MP-368..375) — probe framework portable; Phase 5b gate required before new probes
- platform_authority_loop (MP-377 P0) — ProjectGovernance/RepoPack design targets arbitrary repos

**Portable pending closure:**
- ai_governance_platform (MP-377) — main product architecture; portability-by-default closure (2026-04-07 note) pending hidden-default extraction + typed capability gating
- remote_control_runtime (MP-380..387) — requires dashboard parity + actor dispatch closure before remote-only proof

**Not yet portable:**
- review_channel, continuous_swarm (MP-355, MP-358) — bridge.md and markdown cycling not portable; pending typed review-channel closure
- operator_console (MP-359) — VoiceTerm-specific PyQt6 shell; portability deferred post-main-product

---

## Execution Priorities for Next Redesign Phase

1. **Consolidate governance runtime subordinates** (immediate; unblocks downstream clarity)
2. **Confirm quality clusters single authority** (medium; reduces navigation friction)
3. **Promote portable-code-governance external adopter proof** (high; delivers portability value)
4. **Close typed review-channel contract** (high; unblocks operator/remote surfaces)
5. **Retire pre-release audit as live plan** (low; intake already routed)

---

## Summary

- **Total active plans:** 24
- **Execution-owner authority:** 5 canonical (MASTER_PLAN + ai_governance_platform + review_channel + review_probes + continuous_swarm)
- **Consolidation opportunities:** 4 high-priority merges
- **Stale plans needing archive:** 3–4 (audit supporting docs, phase2)
- **Cross-repo ready:** 1 (portable_code_governance for external proof)
- **Pending portability gates:** 2 (ai_governance_platform, remote_control_runtime)

