# Active Docs Index

This file is a **maintained pointer/projection** over the typed plan state. The
**canonical PlanRow registry** is `dev/state/plan_index.jsonl` (per GuardIR
v4.37+ packet-as-evidence rule); this markdown lists active owner docs and when
to read them but is not itself durable plan authority. Closure receipts live in
`dev/state/plan_row_closure_receipts.jsonl`, intent ingest receipts in
`dev/state/plan_ingestion_receipts.jsonl`, and source snapshots in
`dev/state/plan_source_snapshots.jsonl`. Resolve plan questions through those
typed stores first; consult this file as a maintained navigation index.

Keep the execution-owner set small: `MASTER_PLAN.md` plus 3-4 owner specs.
Narrower or completed lanes stay here as reference-only owner docs until they
are archived or folded into the umbrella plan.

## Registry

The `Execution authority` column below describes each doc's **role in the
projection**, not durable authority. A row marked `tracker_projection` is a
maintained projection over `dev/state/plan_index.jsonl` (the typed canonical
PlanRow store); a `reference-only` row is documentation that informs the typed
plan but is not consulted as authority.

| Path | Role | Authority projection | MP scope | When agents read |
|---|---|---|---|---|
| `dev/active/MASTER_PLAN.md` | `tracker` | `tracker_projection` (over `dev/state/plan_index.jsonl`) | all active MP execution state | always |
| `dev/active/README.md` | `reference` | `reference-only` | active-doc navigation helper (non-tracker) | when scanning `dev/active/` ownership/read-order context |
| `dev/active/theme_upgrade.md` | `reference` | `reference-only` | `MP-099`, `MP-148..MP-151`, `MP-161..MP-167`, `MP-172..MP-182` | when Theme Studio, overlay visual research, or visual-surface redesign context is needed; execution state stays in `MASTER_PLAN.md` |
| `dev/active/memory_studio.md` | `reference` | `reference-only` | `MP-230..MP-255` | only when memory/action/context-pack reference context is needed |
| `dev/active/devctl_reporting_upgrade.md` | `reference` | `reference-only` | `MP-297..MP-300`, `MP-303`, `MP-306`, `MP-379` | when improving `devctl` reporting, dashboard outputs, CIHub integration, or collector integrity; use as owner reference, not standalone execution authority |
| `dev/active/autonomous_control_plane.md` | `reference` | `reference-only` | `MP-325..MP-338, MP-340` | when autonomy/mobile-control-plane reference context is needed; the typed phase registry in `ai_governance_platform.md` decides live execution order |
| `dev/active/review_channel.md` | `spec` | `mirrored in MASTER_PLAN` | `MP-355` | when designing or implementing the shared review channel, dual-agent shared-screen surfaces, reviewer/coder packet flows, overlay-visible Codex/Claude coordination, or the merged markdown-swarm multi-agent cycle |
| `dev/active/CLAUDE_SESSION_AUTOMATION_SAFETY_DECLARATION.md` | `reference` | `reference-only` | session-scoped automation safety evidence | only when reviewing the current operator-authorized Claude loop automation safety declaration; not durable governance policy or execution authority |
| `dev/active/host_process_hygiene.md` | `reference` | `reference-only` | `MP-356` | when host-side process cleanup/audit reference context is needed |
| `dev/active/continuous_swarm.md` | `reference` | `reference-only` | `MP-358` | when the standing Codex/Claude dogfood loop or launcher proof context is needed |
| `dev/active/operator_console.md` | `reference` | `reference-only` | `MP-359` | when Operator Console reference context is needed |
| `dev/active/loop_chat_bridge.md` | `reference` | `reference-only` | `MP-338` | when coordinating loop artifact-to-chat suggestion flow or reviewing legacy handoff evidence |
| `dev/active/naming_api_cohesion.md` | `reference` | `reference-only` | `MP-267` | when naming/API cohesion reference context is needed |
| `dev/active/ide_provider_modularization.md` | `reference` | `reference-only` | `MP-346`, `MP-354` | when provider/IDE modularization reference context is needed |
| `dev/active/pre_release_architecture_audit.md` | `reference` | `reference-only` | `MP-347`, `MP-349` | when reviewing consolidated pre-release audit evidence or follow-up reference context |
| `dev/active/audit.md` | `reference` | `reference-only` | `MP-347`, `MP-349` | when reviewing consolidated full-surface findings and sequencing remediation work under the pre-release architecture audit plan |
| `dev/active/move.md` | `reference` | `reference-only` | `MP-347`, `MP-349` | when reviewing raw multi-agent merge transcript evidence that supports `dev/active/audit.md` findings |
| `dev/active/RUST_AUDIT_FINDINGS.md` | `reference` | `reference-only` | bridge pointer to canonical guard-driven remediation scaffold at `dev/reports/audits/RUST_AUDIT_FINDINGS.md` (supporting context, not execution authority) | when AI guard checks fail or guard findings are referenced; follow the bridge to canonical reports path |
| `dev/active/slash_command_standalone.md` | `reference` | `reference-only` | `MP-352`, `MP-353` | when standalone slash-command reference context is needed |
| `dev/active/ralph_guardrail_control_plane.md` | `reference` | `reference-only` | `MP-360..MP-367` | when Ralph guardrail/control-plane reference context is needed |
| `dev/active/review_probes.md` | `spec` | `mirrored in MASTER_PLAN` | `MP-368..MP-375` | when implementing heuristic review probes, non-blocking risk-hint collectors, or probe-fed AI review triage surfaces |
| `dev/active/portable_code_governance.md` | `reference` | `reference-only` | `MP-376` | when extending the portable guard/probe engine, defining repo-policy vs engine boundaries, building measurement/eval corpora, exporting the governance stack for off-repo review, or piloting the system on other repositories; keep the live execution order in `dev/active/ai_governance_platform.md` and treat this as the owner reference for the portable-proof phase instead of a standalone authority surface |
| `dev/active/ai_governance_platform.md` | `spec` | `mirrored in MASTER_PLAN` | `MP-377` | read first for any standalone governance-product architecture, packaging, repo-pack, runtime-contract, or extraction work; this is the primary maintained owner-spec projection for the transition from VoiceTerm-embedded tooling to an installable product |
| `dev/active/agent_substrate_architecture_review.md` | `reference` | `reference-only` | `MP-377` / Plan 4.1 | when validating the 2026-04-27 operator request for one coherent agent substrate, proof-tick authority, mode-axis separation, or future any-agent-any-role capability migration; execution order stays in `ai_governance_platform.md` |
| `dev/active/platform_authority_loop.md` | `reference` | `reference-only` | `MP-377` | after reading `ai_governance_platform.md`, load only when the current typed phase/task route names startup authority, repo-pack activation, plan routing, or runtime/evidence/context closure as the owner doc |
| `dev/active/autonomous_governance_loop_v2.md` | `reference` | `reference-only` | `MP-377` | after reading `ai_governance_platform.md`, load only when the current typed phase/task route names loop-v2 composition, findings priority, auto-mode, monitor, or graph-backed discoverability as the owner doc |
| `dev/active/remote_commit_pipeline.md` | `reference` | `reference-only` | `MP-377` | after reading `ai_governance_platform.md`, load only when the current typed phase/task route names the governed remote commit/push lane as the owner doc |
| `dev/active/remote_control_runtime.md` | `reference` | `reference-only` | `MP-380..MP-387` | after reading `ai_governance_platform.md`, load only when the current typed phase/task route names remote-control reviewer/runtime convergence as the owner doc |
| `dev/active/PLAN_FORMAT.md` | `reference` | `reference-only` | `MP-377` | when editing governed active-plan markdown, extending active-plan/docs-governance enforcement, or aligning `PlanRegistry` / `PlanTargetRef` design with the repo's own plan-doc contract |
| `dev/active/code_shape_expansion.md` | `reference` | `supporting` | `MP-378` | when calibrating or sequencing Phase 5b+ probe candidates, thresholds, metadata, and shared infrastructure for future code-shape additions under `dev/active/review_probes.md`; this is a subordinate research/evidence companion, not a second execution authority |
| `dev/active/phase2.md` | `reference` | `reference-only` | bridge pointer to canonical phase-2 companion-platform research context at `dev/deferred/phase2.md` (not active MP execution state) | only when evaluating long-range terminal companion planning; follow the bridge to deferred research |

## Load Order (Agent Bootstrap)

1. Read this file (`dev/active/INDEX.md`).
2. Read `dev/active/MASTER_PLAN.md`.
3. If the task is repo-wide status, current strategy, extraction sequencing,
   PyQt6, phone/mobile, or shared-backend architecture while `MP-377` is
   active, read `dev/active/ai_governance_platform.md` next before narrower
   domain specs. Theme, Memory, and the legacy per-lane docs are supporting
   context, not top-level priority signals in that mode.
3.1 Read only the owner docs named by the typed phase/task registry at the top
    of `dev/active/ai_governance_platform.md`.
    The default tracker-projection owner set is:
    `dev/active/review_channel.md`,
    `dev/active/review_probes.md`,
    plus reference owner docs such as
    `dev/active/portable_code_governance.md`,
    `dev/active/platform_authority_loop.md`,
    `dev/active/autonomous_governance_loop_v2.md`,
    `dev/active/remote_commit_pipeline.md`, and
    `dev/active/remote_control_runtime.md` only when the active phase/task
    explicitly points there.
3.2 If that same `MP-377` work changes governed active-plan markdown shape or
    execution-plan schema expectations, read `dev/active/PLAN_FORMAT.md`
    before editing plan docs or active-plan guards.
4. Read only registry docs required by the task class after that.
5. Do not treat any non-tracker file as execution state authority.

## Process: Add A New `dev/active/*.md` File

1. Create the new markdown file under `dev/active/`.
2. Add one registry row in this file with path, role, authority, MP scope, and read trigger.
3. If the new file introduces execution state, wire that scope into `dev/active/MASTER_PLAN.md`.
4. Update links in `AGENTS.md` and `dev/README.md` when discovery/navigation changes.
5. Run sync/governance checks:
   - `python3 dev/scripts/checks/check_active_plan_sync.py`
   - `python3 dev/scripts/devctl.py docs-check --strict-tooling`
   - `python3 dev/scripts/devctl.py hygiene`
6. Commit docs and governance updates in the same change as the new file.
