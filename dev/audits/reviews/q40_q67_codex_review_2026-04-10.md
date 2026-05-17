# Governance Quality Sweep Review Verdict

Date: 2026-04-10
Reviewed commits: `10242d1a`, `5d02040f`, `b42dd589`, `51da1e71`, `7eca4d0c`, `3f1d9950`, `95140873`, `b078731a`

## Architecturally sound

- `Q40/Q42/Q51` is directionally correct. `action_routing.py` gives dashboard/observer lanes findings-only permissions, `startup_context.py` exports typed recovery authority, and the mobile dashboard renderer is a thin projection rather than a second control plane.
- `Q52` is sound. The raw `git commit` hook now calls `build_startup_context()` plus `build_commit_permission_decision()` through `runtime/commit_permission_hook.py`, so raw commits no longer bypass the typed commit gate.
- `Q57` is sound. `runtime/monitor_snapshot.py` composes `build_startup_context()` and `build_control_plane_read_model()` instead of inventing new authority, then writes `monitor_snapshot.{json,md}` into the existing status bundle.
- `Q58` is the right direction. Moving guard/probe path resolution behind `script_catalog_registry` removes a large class of hardcoded-path drift.
- `95140873` is an acceptable compatibility repair. The standalone import shim in `bundles/registry.py` is ugly but honest, and it restores self-hosting behavior for loaders that still use `spec_from_file_location`.
- `b078731a` is clean debt paydown. It removes stale code-shape overrides instead of widening them.

## Weak or half-built

- `Q65` is not fully layered yet. `runtime/startup_context.py` still builds both `work_intake.coordination` and a separate top-level `coordination` snapshot. `runtime/action_routing_coordination.py` then prefers `work_intake.coordination` but falls back to the top-level snapshot for both `coordination_state()` and `active_implementation_owner()`. `runtime/action_routing.py` also still reads top-level `implementation_permission`. The result is reduced duplication, not single-source truth.
- `Q64` is emitted but not behavior-driving. `runtime/work_intake.py` builds `session_pacing`, and startup rendering surfaces print it, but there is no controller, launcher, or loop that actually enforces `research_ref_budget`, `implementation_trigger`, or `focus_slice_id`. It is advisory text today.
- `Q42` recovery authority is mostly descriptive today. `RecoveryAuthorityState` is exported by startup/monitor surfaces, but runtime mutation control still depends on other recovery fields such as `reviewer_runtime.recovery_action_allowed`. The new contract is not yet the governing executor input.
- `Q55` is also advisory-only. `commands/reporting/findings_priority.py` ranks LIVE_RUN findings, but nothing in the autonomy stack consumes that ranking to choose the next slice.
- `Q67` improved the detector materially, but the contract-connectivity guard is still a noisy inventory, not a clean architecture gate. On 2026-04-10 at current HEAD, `check_contract_connectivity.py --absolute` reports `130` orphaned contracts, `69` duplicate contracts, and `20` stranded consumers. The older `39 orphan / 40 duplicate` figure is stale.
- The current orphan baseline is mostly noise: local UI/helper dataclasses, intentional internal-only models, and package-private report payloads. The current duplicate baseline is mixed: some rows are real cross-layer debt, but many are projection/snapshot/helper pairs that should not be treated with the same severity.
- `Q58` needed `95140873` immediately after landing. That is not a reason to revert the refactor, but it is evidence that the first pass was not fully self-hosting.

## Contract connectivity verdict

- The guard infrastructure is useful: AST inventory, importer maps, semantic duplicate detection, stranded-consumer detection, and baseline-growth blocking are all legitimate building blocks.
- The baseline is not yet trustworthy as an architectural truth surface. In current absolute mode, the majority of orphan rows are expected internal/private helper contracts, especially under `app/operator_console/**` and `governance/quality_feedback/**`.
- Some duplicate findings are real and worth action:
  - `CatalogCommand` vs `CommandEntry`
  - dual `SystemCatalog` families
  - overlapping push-state families
  - `CoordinationTopologySnapshot` vs `WorkIntakeCoordinationState`
- Some stranded-consumer findings are also real, but many are parser/projection rebuilds that exist because the repo still has dict-to-contract rehydration seams. Those should be triaged separately from true contract duplication.
- Verdict: keep the guard as a growth blocker and inventory tool, but do not treat the current baseline counts as "real debt counts" until the findings are stratified.

## Q69 manual-loop review

- The gap is real. `autonomy-loop` runs bounded controller rounds over triage/packet/checkpoint, `autonomy-run` runs swarm + governance bundles, and `AutoModeState` already models `committing` and `pushing`, but nothing actually connects green implementation output to governed commit/push/next-slice progression.
- The operator's manual loop is therefore architecturally important evidence, not operator folklore. It proves the missing closure is real.
- Q69 should not be built exactly as written. The proposed `codex exec --full-auto --json -o /tmp/codex-verdict-*.md` plus "watch for verdict file appearance" design overfits one provider and makes file side effects look like authority.
- The right design is to extend the existing autonomy stack or add a sibling controller inside it that composes existing typed surfaces:
  - task selection from LIVE_RUN plus `findings-priority`
  - bounded intake from `WorkIntakePacket`
  - monitor/control-plane state from `MonitorSnapshot` and `ControlPlaneReadModel`
  - governed commit through existing commit pipeline
  - governed push through `devctl push --execute`
  - phase/render state through `AutoModeState`
- Keep provider launch as an adapter detail, not the core contract. The core loop should advance on repo-owned typed state, not on the existence of `/tmp/codex-verdict-*.md`.
- Verdict: build Q69, but redesign it as a composition over existing autonomy + commit/push infrastructure. Do not ship the bespoke verdict-file controller as the long-term architecture.

## Recommended next Q-findings

- `Q70 — ARCHITECTURE — action_routing still depends on parallel coordination truth`
  Collapse startup action routing onto one canonical typed coordination contract and demote top-level `coordination` to projection-only status.
- `Q71 — CONTRACT — session_pacing is emitted but not enforced`
  Wire `SessionPacingState` into at least one launcher/controller so `research_ref_budget`, `implementation_trigger`, and `focus_slice_id` affect behavior.
- `Q72 — GUARD — contract_connectivity baseline is too noisy for architectural decisions`
  Split findings into severity classes such as real cross-layer duplicate, intentional internal-only contract, projection/parser rebuild, and UI-local helper payload.
- `Q73 — ARCHITECTURE — findings-priority has no consuming controller`
  Route at least one autonomous task selector through `findings-priority` instead of leaving it as a read-only report.
- `Q74 — ARCHITECTURE — autonomous governance loop should extend existing autonomy/commit/push surfaces, not add a verdict-file controller`
  Reuse `autonomy-loop` or `autonomy-run` machinery, `AutoModeState`, governed commit, and governed push rather than centering the loop on provider-specific output files.
- `Q75 — CONTRACT — RecoveryAuthorityState is exported but not authoritative`
  Either make the typed recovery-authority contract the actual runtime mutation gate or explicitly demote it to display-only projection.

## Overall verdict

The series is directionally strong. The repo now has better typed control surfaces, a real monitor surface, a raw-commit gate, registry-based path resolution, and a more capable contract-connectivity inventory. The main architectural weakness is that several new contracts stop at projection/reporting: coordination truth is still split, session pacing is advisory only, findings priority is unconsumed, and recovery authority is not yet the executor's source of truth.

If the next slice is Q69, build it, but do it as closure over the existing governed system rather than as a fresh bespoke loop around Codex verdict files.
