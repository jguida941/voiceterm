# AI Governance Platform Plan

**Status**: active  |  **Last updated**: 2026-04-22 | **Owner:** Tooling/control plane/product architecture
Execution plan contract: required
This spec remains execution mirrored in `dev/active/MASTER_PLAN.md` under
`MP-377`, and it is the canonical active architecture plan for the standalone
AI governance product scope. `MASTER_PLAN` stays the repo-wide tracker
authority, but this file is the main scoped plan for architecture decisions,
documentation consolidation, extraction sequencing, and implementation order
under `MP-377`.

For this product scope, treat this file as the only main active plan. Companion
docs may exist for narrower engine/adoption depth or durable guide material,
but they must route back here instead of acting like peer execution authority.
Repo-wide status and strategy surfaces must point here while `MP-377` is the
active extraction lane; if another active doc claims top-level product
priority, treat that as plan drift and correct the summary surface rather than
interpreting it as a second main lane.
The current `P0` subordinate execution spec for startup authority, repo-pack
activation, typed plan routing, runtime/evidence/context closure, and first
cross-repo proof is `dev/active/platform_authority_loop.md`.

Current 2026-04-05 role/bootstrap closure note:
- Launch/bootstrap ownership in the shared governance runtime must stay
  role-first (`reviewer`, `implementer`, `operator`), not provider-first.
  A repo or operator may assign Codex, Claude, or another supported provider
  to any of those roles, but the canonical bootstrap remains
  `startup-context --role <role>` plus
  `session-resume --role <role> --format bootstrap`, and review-channel /
  recover / prompt surfaces must derive the current provider from typed lane
  or collaboration state instead of hardcoding `codex reviewer` /
  `claude coder`.

Current 2026-04-05 terminal/visibility closure note:
- Headless-vs-visible launch is runtime authority, not chat lore. Shared
  review-channel launch/recovery/follow paths must resolve terminal mode
  through one policy: explicit `--terminal` wins, governed `remote_control`
  stays headless, already-headless parent sessions keep recovery headless, and
  otherwise local launches default to visible `Terminal.app`. The same runtime
  contract must expose typed visibility (`reviewer_runtime.conductor_visibility`
  plus reviewer `session_owner.session_visibility`) so operators and AI can
  detect hidden conductor state without reverse-engineering `terminal_window_id`
  nulls or guessing from detached heartbeats.

Current 2026-04-06 shared-violation convergence note:
- `MP-381` has started as a bounded contract-first slice rather than a broad
  frontend rewrite. The new
  `dev/scripts/devctl/runtime/probe_report_violations.py` seam maps enriched
  `probe-report` hints into `tuple[ViolationRecord, ...]` so probes can join
  the shared `CheckResult` / `ViolationRecord` projection path without
  changing probe-report's existing JSON/markdown artifacts or promoting
  `Finding` into the general-purpose check-output row. Treat this as the first
  linker step for shared violation rendering: next consumers should reuse the
  same row contract in governance-review, startup summaries, and dashboard
  surfaces instead of growing another probe-specific presentation family.

Current 2026-04-07 portability-by-default closure note:
- Accept the review verdict as plan state: the architecture is portable by
  design, but the live system is not yet portable by default. Treat the next
  `MP-377` / `MP-376` order as hidden-default extraction first, typed
  capability gating second, controlled fixture proof third, and broad
  real-world adopter trials fourth. Shared layers that need paths,
  capabilities, operator mode, or review topology must consume
  `ProjectGovernance` / `RepoPack` / typed runtime state or fail closed; they
  must not silently resurrect VoiceTerm path/layout, `bridge.md`, tandem, or
  local-terminal defaults.

Current 2026-04-07 ReviewSnapshot audit-intake routing note:
- `dev/audits/architecture_hardening_plan.md` is accepted as reference audit
  intake for MP-377 / MP-376, not as a new active plan. The main product plan
  owns cross-surface consistency, contract registration, generated-artifact
  integrity, suggested-command and WhyRecord production consumers, and later
  MCP / Agent SDK ecosystem surfaces. Path/default cleanup belongs to
  `platform_authority_loop.md`, commit/push and override integrity belong to
  `remote_commit_pipeline.md`, and fresh-adopter proof belongs to
  `portable_code_governance.md`. Hook surfaces from this intake are adapters:
  pre-commit, pre-push, session, provider, and future ecosystem hooks may
  trigger typed commands and record receipts, but the policy stays in typed
  contracts, action packets, and guards. `dev/audits/REVIEW_SNAPSHOT.md`
  remains a generated projection.

Current 2026-04-07 ReviewSnapshot receipt-hook closure note:
- The external-review planning surface now has a repo-owned two-phase raw-git
  path instead of a manual dirty-worktree step. `review-snapshot --receipt-commit`
  creates a snapshot-only receipt commit only when no other path is dirty, and
  `install-git-hooks` installs both the pre-commit projection hook and the
  post-commit receipt hook that invokes that command with recursion disabled.
  This keeps the portable platform contract honest: a snapshot cannot contain
  its own final commit SHA, so freshness is represented as a typed parent-code
  binding rather than a self-referential markdown claim.

Current 2026-04-08 review-status authority / ReviewSnapshot evidence note:
- The next bounded `MP-377` closure tightened live review/status truth without
  reopening bridge authority. When persisted typed `review_state.json`
  already exists, bridge-backed status/compat projection now prefers typed
  `current_session` for instruction/ACK state and typed
  `reviewer_runtime.review_acceptance` for verdict/findings truth, leaving raw
  `bridge.md` prose as compatibility/drift evidence only. The same slice made
  ReviewSnapshot cite emitted evidence instead of only next-command prose by
  projecting probe run-state/artifact refs and current push
  receipt/authorization refs. The same lane now closes the startup ownership
  gap too: `startup-context` / `WorkIntakePacket` emit one bounded ownership
  classifier for dirty paths (`clear`, `in_scope_dirty_paths`,
  `scope_unknown_dirty_paths`, `outside_scope_dirty_paths`,
  `concurrent_writer_activity`), and startup authority consumes that typed
  state so outside-scope dirt with active peer activity fails closed as a
  concurrent-writer condition instead of collapsing into generic
  dirty-budget prose.

Current 2026-04-08 dashboard/current-session/queue authority note:
- The next same-lane observability slice closes the remaining mixed-owner
  read path without widening back into bridge prose. Dashboard/control-plane
  conductor liveness now prefers the shared review-channel `session_probe`
  owner before static `session_pid` metadata fallback; event-backed
  `current_session` preserves `implementer_session_state` /
  `implementer_session_hint`; and bridge-backed queue/state surfaces now reuse
  the expiry-aware pending-packet owner so inbox/status/doctor/dashboard agree
  on pending vs stale counts. This is the bounded observer closure before the
  broader `DecisionTrace` / `explain-latest` explanation chain.

Current 2026-04-08 collaboration-topology / ownership note:
- The next bounded same-lane scheduler closure no longer treats
  concurrent-writer awareness as startup-only truth. `WorkIntakePacket` now
  carries one typed coordination reduction alongside dirty-slice ownership:
  `collaboration_topology`, `authority_mode`, `work_ownership_mode`, and
  `sync_cadence_mode`, plus bounded participant/delegated-worker exemplars.
  That same reduction fails closed on duplicated delegated worktrees before
  dirty-path overlap lands, so a fresh session can see both "who else is
  active?" and "is this slice still exclusively owned?" from one packet
  instead of inferring from reviewer mode, bridge prose, and worktree drift
  separately. The next higher-order scheduler layer is now real too:
  `PlanningIRSnapshot` lives beside `SystemPicture` under
  `dev/scripts/devctl/platform/` and reduces `PlanRegistry` /
  `PlanTargetRef`, recent governance-review findings normalized into
  `FindingRecord`, context-graph `scoped_by` ownership, and live
  ownership/coordination runtime state into four bounded outputs:
  `next_best_slices`, `concurrent_writer_conflicts`, `unowned_hot_paths`, and
  `plan_finding_mismatches`. Projection into startup/dashboard/bridge remains
  the next follow-up, but the reducer itself is no longer plan-only theory.
  The first projection slice is now real too: `CoordinationSnapshot` lives
  beside those reducers under `dev/scripts/devctl/platform/`, joins startup
  work-intake posture with `ReviewState.collaboration` / delegated-worktree
  receipts / ready gates, and projects one bounded answer for
  declared-vs-observed topology, fanout posture, worktree isolation, and
  resync requirement. `system-picture` now consumes that snapshot as its
  first repo-visible typed coordination section, so fresh sessions no longer
  need to reconstruct the inactive-loop / planned-fanout mismatch from raw
  status JSON or bridge prose.

Current 2026-04-08 typed mutation / queue / dashboard convergence note:
- The next same-lane closure is no longer "typed architecture missing"; it is
  fail-closed reuse of the typed seams already landed. Governed mutation must
  keep `devctl commit` auto-approval limited to resolved
  `local_terminal` / `single_agent` modes, require exact-head publication
  authorization whenever review is declared/effective dual-agent even if the
  live runtime temporarily degrades to `tools_only`, and preserve the policy
  remote/current approved target when `devctl push` routes through an active
  pipeline. Queue truth must also stay exact: only applied
  `commit_approval` decisions clear the live approval request, not `acked`
  packets or unrelated history rows. Dashboard/control-plane convergence is
  the matching read-side requirement: dashboard must consume the same fresh
  review-state source as startup/session-resume instead of replaying stale
  `state/latest.json` for instruction/findings truth.

Current 2026-04-10 deterministic action-routing / commit-permission note:
- The Q37-Q47 live audit tightened the same `MP-377` principle: agents should
  not reason about the next control-plane step when repo-owned typed state can
  compute it. The first closure adds startup-facing action routing
  (`next_command`, `allowed_actions`, `blocked_actions`, `recovery_action`,
  `escalation_action`) plus typed `agent_lane` permissions, and makes
  `devctl commit` consume a `CommitPermissionDecision` before staging or
  running guards. Remaining product work is to widen that packet into
  dashboard/status/doctor, raw-git hooks, pre-edit/pre-launch boundaries, and
  destructive recovery.

Current 2026-04-10 loop-v2 convergence note:
- The next bounded `MP-377` planning slice now routes through
  `dev/active/autonomous_governance_loop_v2.md`. That lane does not own a new
  backend; it owns the composition rule that the autonomous governance loop
  must consume existing `StartupContext` / `WorkIntakePacket`,
  `PlanningIRSnapshot`, `findings-priority`, `ControlPlaneReadModel`,
  `AutoModeState`, `MonitorSnapshot`, `governance-review`,
  `GuardPromotionCandidate`, and governed commit/push surfaces instead of
  inventing a provider-specific verdict-file controller or operator-prose
  authority.

Current 2026-04-13 dogfood walkthrough parity note:
- The live system test is now part of the platform proof. Startup, session-
  resume, dashboard, review-channel status, bridge projection, and
  context-graph query surfaces must agree on the same promoted
  `active_target`, typed findings backlog, and plan/task discoverability.
  The current closure keeps continuity subordinate to live planning/finding
  state, projects `quality_signals.finding_backlog` in startup, allows
  status-driven `bridge.md` reprojection from typed `_compat.bridge_projection`
  while leaving explicit `render-bridge` fail-closed on pending reviewer
  packets, and treats task-id / contract query discoverability
  (`PlanPhase`, `PlanTask`, `FindingBacklog`, `MP377-P0-T01`) as a required
  consumer-route proof rather than optional search sugar.

Current 2026-04-22 worktree-orphan prevention note:
- The post-Phase-0 design lock treats orphaned work as a cross-runtime
  inventory problem, not a local `git status` problem. Slice 1 establishes the
  typed contract set for `OrphanSnapshot` / `OrphanSource`,
  `OrphanReconciliationDecision`, `CheckoutInventory`,
  `WorkPublicationLedger`, `SessionLease`, `WorktreeBaseline`, and
  accept-all override receipts. The variants explicitly cover the current
  checkout, registered git worktrees, planned delegated worker worktrees,
  unregistered sibling clones such as Finder/cp-backed repo copies, deep-scan
  repos, prunable or missing worktrees, stash/worker/CI-root orphans, and
  latent state. These contracts are registered through the platform
  `ContractSpec` registry so `check_contract_connectivity.py`,
  `check_governance_closure.py`, and
  `check_platform_contract_closure.py` can prove the schema surface is
  connected before later slices wire launch/push/fanout enforcement.
- Slice 2 keeps the first scanner report-only: `devctl orphan-inventory`
  builds an `OrphanInventoryReport` over the current checkout, registered
  worktrees, planned coordination actors, bounded same-parent same-origin
  sibling clones, and stash sections. It does not fire gates; slice 3 promotes
  this observation stream into packet/projection surfaces before enforcement.
- Slice 3 promotes the scanner output without adding a command:
  `compute_orphan_snapshot()` turns an `OrphanInventoryReport` into a
  deterministic `OrphanSnapshot` with ledger/lease provenance, startup-context
  emits it as typed evidence, and governed commit/push preflight consume the
  same projection as advisory-only warnings. `OrphanReconciliationDecision`
  now also carries plan/finding scope hints so later executor and gate slices
  do not create unscoped remediation debt.

Current 2026-04-15 consolidated redesign note:
- The full active-plan set plus `LIVE_RUN.md` Q1-Q100 all point at the same
  structural failure: the repo already has most of the right contracts, but
  too many surfaces still recompute or rephrase runtime truth independently.
  The redesign for the rest of `MP-377` is therefore a convergence order, not
  a new architecture:
  `FindingBacklog / PlanRegistry -> AuthoritySnapshot / CoordinationSnapshot ->
  canonical ReviewState + commit_pipeline producer -> ControlPlaneReadModel /
  startup-context / status / dashboard / mobile projections -> TypedAction /
  ActionResult / ValidationReceipt -> dogfood/governance-review feedback`.
- `bridge.md`, markdown tables, dashboard prose, and packet-friendly narrative
  remain compatibility or explanation projections only. They may carry the
  latest rendered answer, but they must not be the place where reviewer mode,
  liveness, pending work, commit approval, push readiness, or current slice
  becomes authoritative.
- The next execution order is fixed by the audit and the owner docs already in
  this repo:
  1. single producer/read-model closure for review/runtime authority
     (`review_state.json`, `commit_pipeline.json`, `AuthoritySnapshot`,
     `CoordinationSnapshot`, `ControlPlaneReadModel`);
  2. governed mutation self-healing so commit/push/phone actions refresh and
     consume those same artifacts instead of fighting stale projections;
  3. dogfood as the development engine so findings, priorities, and next-slice
     selection share one persisted feedback loop;
  4. observer/liveness boundary closure so dashboard/mobile/operator surfaces
     route typed action requests but do not invent or mutate backend truth;
  5. only then widen portable/adopter proof on top of the converged owner
     chain.
- Treat these audit clusters as the current acceptance map for that order:
  `Q29`, `Q35-Q37`, `Q41-Q50`, `Q51-Q75`, and `Q90-Q100`. A slice is not done
  until the owning typed contract changes, the read-side consumers converge,
  and the relevant `LIVE_RUN` / `governance-review` entries are updated from
  repo-visible evidence.

## Scope

Turn the current VoiceTerm-local automation stack into a reusable AI governance
platform that can be installed into arbitrary repositories without editing core
orchestration code. The target product is broader than portable guards alone:
it includes the code-governance engine, typed control-plane/runtime contracts,
repo-adapter boundaries, AI remediation loops, and optional frontends such as
CLI, PyQt6 desktop console, overlay/TUI, and phone/mobile views.

VoiceTerm should become the first consumer of that platform rather than the
place where the whole platform remains embedded. Another repo should be able to
adopt the same system through packaging, bootstrap/setup flows, policy/repo-pack
selection, and provider configuration instead of copying VoiceTerm-specific
Python modules and pruning them by hand.

This plan is intentionally broader than
`dev/active/portable_code_governance.md`. That plan stays focused on the
portable guard/probe/policy/bootstrap/export engine and multi-repo evaluation
work. This plan owns the full reusable product architecture: shared runtime
contracts, frontend convergence, repo-pack packaging, and the staged extraction
of higher-level loops that are still repo-local today.

## Canonical Plan Use

Use this file as the main scope-preservation surface for the standalone
governance product direction.

1. Put product-boundary, packaging, repo-pack, runtime-contract, frontend, and
   documentation-consolidation decisions here first.
2. Keep `dev/active/MASTER_PLAN.md` as the repo-wide tracker, but do not rely
   on `MASTER_PLAN` alone to preserve architecture detail for `MP-377`.
3. Treat `dev/active/portable_code_governance.md` as the narrower companion
   engine plan, not a peer architecture authority for the full product.
4. Treat `dev/guides/AI_GOVERNANCE_PLATFORM.md` as the durable guide derived
   from this active plan, not a second active source of execution state.
5. Any platform-scope tooling, policy, runtime-contract, or extraction change
   that triggers repo docs-governance must update this file. The repo-level
   `docs-check` rule is policy-owned and should enforce this requirement
   without hardcoding VoiceTerm-specific logic into the command implementation.

## Scope Preservation Rule

The target is the full system becoming modular and callable from any repo, not
only one loop or one frontend getting cleaner inside the embedded VoiceTerm
tree.

Apply these rules while executing `MP-377`:

1. Treat `governance_core`, `governance_runtime`, `governance_adapters`,
   `governance_frontends`, `repo_packs`, and `product_integrations` as one
   product boundary. The extraction target is the whole stack.
2. Treat `MP-340`, `MP-355`, `MP-358`, and `MP-359` as subordinate
   implementation lanes inside that boundary, not as alternate long-term
   backend authorities.
3. When any loop/control-plane/frontend slice lands, state which shared
   contract or layer it strengthens and which current VoiceTerm-embedded
   assumption it removes or narrows in the same tranche.
4. If a change improves one local surface while increasing direct VoiceTerm
   coupling, duplicating backend logic, or creating a surface-local ruleset,
   it is off-plan even if the local slice looks cleaner.
5. "Modular and callable" means the same typed actions, state, evidence, and
   policy surfaces can be invoked by AI agents, human developers, CLI flows,
   PyQt6, overlay/TUI, phone/mobile clients, and later skills/hooks without
   each surface inventing a second backend or a different check stack.

## Platform Layers

Use these layers consistently while reorganizing the repo and extracting the
reusable product:

1. `governance_core`
   portable guards, probes, policy resolution, bootstrap, export, review ledger,
   measurement schemas, and artifact generation.
2. `governance_runtime`
   typed control state, action execution, loop orchestration, repo sessions,
   queueing, and artifact-store contracts shared by CLI/UI surfaces.
3. `governance_frontends`
   CLI, PyQt6 operator console, overlay/TUI, and phone/mobile surfaces that all
   project the same runtime state instead of re-implementing orchestration.
4. `governance_adapters`
   provider adapters, CI/workflow adapters, VCS adapters, notifier adapters, and
   local-environment capability detection.
5. `repo_packs`
   repo-specific policy, workflow defaults, docs/runbook templates, and any
   bounded repo-local guard or lane wiring that does not belong in the portable
   engine.
6. `product_integrations`
   VoiceTerm-specific packaging and UX, treated as a consumer/integration layer
   over the reusable platform rather than the canonical home of every feature.

## Execution Surface Ownership

Use one repo-pack-owned ownership map for routing and boundary enforcement over
the extracted platform:

1. `voiceterm_client`
   Rust app/runtime UX, HUD/overlay, app-local UI, and other product-client
   surfaces.
2. `governance_engine`
   portable/runtime/control-plane contracts, guards, probes, policy,
   startup/work-intake, evidence, and shared backend logic.
3. `integration`
   the thin seam where a product consumes the engine: repo packs, generated
   bootstrap surfaces, adapter wiring, bridge/debug projections, and other
   client-vs-core glue.

Rules:

1. The ownership map is repo-pack/policy-owned, not a one-repo hardcoded path
   table inside the core router.
2. Startup/work-intake, check routing, and review posture should surface the
   classified ownership slice explicitly so mixed-surface changes can trigger a
   stricter review posture without pretending they are one homogeneous lane.
3. Import-boundary and authority-boundary guards must derive from the same
   ownership map so the platform does not keep a second, inconsistent notion of
   "client vs core vs integration".
4. While the self-hosting repo is still converging, this classification is a
   routing/boundary contract first, not a license to widen one mixed commit
   across the whole monorepo.

## Monorepo Discipline

While the platform and VoiceTerm still share one repo, keep the discipline
explicit instead of relying on reviewer taste.

1. Scoped branch strategy: branch and checkpoint work as
   `voiceterm_client`, `governance_engine`, or `integration` first. Mixed
   slices are allowed when necessary, but they should be smaller, more
   explicit, and reviewed more strictly than single-surface slices.
2. Development-vs-runtime documentation separation: contribution/test/release
   instructions are maintainer development surfaces; startup authority,
   runtime contracts, action permissions, and AI enforcement rules are runtime
   governance surfaces. Do not mix them casually or ask AI to infer which
   rules are live from prose tone.
3. Agent namespacing for external repos: keep adopter repo agents and runtime
   governance agents namespaced from engine-maintenance agents so one repo's
   worker contract or bridge labels cannot silently overwrite another repo's
   authority or telemetry semantics.
4. Diff-audit rule:
   `GOOD` when a diff replaces prose/fallback authority with typed authority,
   resolves repo policy once and passes it explicitly, injects repo-pack state
   instead of ambient assumptions, or adds fixture proof that custom-layout or
   no-bridge repos still work.
   `PARTIAL` when it only wraps the old behavior, keeps `REPO_ROOT` /
   VoiceTerm-default fallback alive, captures repo state at import time, or
   moves bridge/provider-shaped fields around without separating compatibility
   projection from canonical runtime truth.

## Compiler-Pass Framing

Use one compiler-style explanatory model when describing the platform, without
pretending the system is literally a compiler.

1. **Frontend / signal extraction**
   `bootstrap`, `startup-context`, guards, probes, repo maps, and policy
   resolution parse repo state into typed signals and bounded startup packets.
2. **Midend / semantic reduction**
   `Finding`, `DecisionPacket`, quality-feedback summaries, governance review,
   triage/backlog ranking, and repo policy reduce those raw signals into
   bounded repair plans with explicit authority and evidence.
3. **Backend / constrained execution**
   Ralph/autonomy/review-channel/`guard-run` consume typed guidance,
   approvals, and output constraints to emit changes through
   `TypedAction -> ActionResult -> RunRecord`.
4. **Link / feedback**
   governance-review ledgers, session-decision artifacts, startup signals, and
   convergence evidence bind accepted outcomes back into later sessions so the
   next run starts from typed prior truth rather than chat memory.

This framing is for architecture clarity, not a license to add opaque
"optimization" layers. The design rule is to strengthen pass boundaries and
typed handoffs, not to smuggle more behavior into prompt-local heuristics.
The current maturity gap is not missing sensors; it is actuator closure:
dynamic failure rules, structured output constraints, convergence proof, and
session-level decision auditability.

## Architecture Principles

Use these rules whenever new platform scope is proposed or existing runtime
surfaces are evaluated.

1. The repo defines the protocol; the agent is a participant. Repo-owned typed
   authority decides what is true, what is allowed, and what must be recorded.
   AI runtime behavior is a consumer of that governed spine, not a second
   control plane with independent truth.
2. Make context a projection, not a crawler. Startup/work-intake should emit
   the bounded approved context slice first; graph/query/helper surfaces reduce
   search space over that authority instead of teaching agents to rediscover
   repo state from scattered file reads on every run.
3. Preserve same truth, different projections. `startup-context`,
   `WorkIntakePacket`, `CollaborationSession`, review projections, graphs, UI
   views, and generated docs may expose different bounded slices, but they must
   project one shared typed truth and must not become independent stores.
4. Keep AI helper surfaces cheap and disposable; keep authority typed and
   repo-owned. Graph packets, escalation hints, hot indexes, probe summaries,
   and other navigation aids are generated-only, reversible, and safe to
   delete. They may explain or compress canonical state, never replace it.
5. Facts compile, judgment stays live. Deterministic routing, ownership,
   capabilities, boundaries, and schema knowledge should move into typed
   contracts, generated artifacts, repo-pack policy, and guards; AI judgment
   remains for the unresolved remainder after those cheaper layers have run.
6. Keep developer-visible truth layered. Command/UI/chat surfaces should show:
   the repo-owned command or receipt that ran, the typed fact packet or
   projection fields that state what the system observed/decided, and only
   then a short readable summary over those fields. The human sentence is a
   projection over machine-owned truth, not a substitute for it.
7. Make observed vs inferred seams auditable. If a launch/status/bootstrap
   surface reports "continue", "checkpoint", "review needed", or other
   synthesized conclusions, the owning typed fields and source command must be
   recoverable without reading model-private reasoning.
8. Hold a governance-weight budget. Overhead that costs more than it saves is
   a product failure: avoid brittle compiled artifacts, expensive invalidation,
   stale indices, oversized IR/catalog layers, and ceremony that makes humans
   or agents bypass the governed path.
9. VoiceTerm is one adopter and self-hosting client of the platform, not the
   platform's identity. Platform doctrine must survive repos that do not ship
   the VoiceTerm app or its paths, workflows, or terminology.

## Repair And Evolution Boundary

Use one explicit boundary for self-hardening so the platform does not slide
from governed enforcement into unguided self-redefinition.

1. Auto-fix code, not policy. Runtime may auto-apply only predeclared
   invariants whose canonical form already exists in repo-owned authority:
   contract-backed formatting, known structural rewrites, package/layout
   normalization, idempotent repairs, reversible repairs, and narrow-blast-
   radius fixes that a governed validator already knows how to judge.
2. Keep three separate lanes:
   - `deterministic repair lane`: safe auto-repairs over known invariants.
   - `governed decision lane`: ambiguous refactors, behavior changes,
     architectural tradeoffs, repo-specific semantics, and other intent-shaped
     work. These must emit `Finding`, `DecisionPacket`, review, or approval
     artifacts instead of silent mutation.
   - `governance evolution lane`: misses that imply a new guard, probe, test,
     card, or invariant. These must become typed candidate proposals with
     replay evidence, not self-installed rules.
3. Runtime may reduce uncertainty automatically, but it may not expand
   authority automatically. If a change requires new interpretation, new
   permission, new doctrine, or a new cross-cutting rule, it is a proposal,
   not a repair.
4. "Best practice" is not authority. Auto-repair must anchor to canonical repo
   shape, declared contract, tested rule, bounded proof surface, and measured
   validator behavior rather than generic AI cleanup taste.
5. Predeclared invariants can auto-enforce. New invariants must earn
   promotion through candidate rule capture, corpus replay, false-positive /
   false-negative evaluation, approval, and then promotion. The platform
   should be self-hardening, not self-redefining.

## Developer-Facing Truth Stack

Treat developer-visible repo surfaces as one explicit projection stack rather
than a freeform chat stream.

1. `command layer`: the exact repo-owned command/action that executed
   (`startup-context`, `session-resume`, `review-channel status`, `push`,
   etc.).
2. `fact layer`: the typed receipt / packet / projection that carries the
   observed state (`action`, `reason`, `review_range`, `review_needed`,
   `open_findings`, `recommended_command`, frozen dirty-tree
   `review_candidate` targets, and similar fields).
3. `summary layer`: the short human-readable explanation shown in terminal,
   chat, dashboard, or mobile views.

The design rule is strict: the summary layer may compress the fact layer, but
it must not become a second authority owner. If the readable sentence says the
repo is clean, review is accepted, or the next step is relaunch, the typed
fields and owning command should already say that. The system should make it
easy for a developer to answer:

- what exact command ran
- what exact state claims were observed
- what next command the repo requires
- what was inferred vs observed

Dirty-tree review handoff depends on that distinction. If an implementer can
finish a bounded slice before checkpointing, the reviewer must receive a
typed frozen `ReviewCandidateRecord` from the fact layer rather than infer the
review target from `HEAD`/`last_reviewed_sha` plus compatibility bridge text.
The same closure now applies to self-hosting cleanup of that fact layer: keep
candidate parsing/path discovery, recovery decision/evidence shaping, and
collaboration-session dataclasses in small helper modules so the typed
handoff/runtime seam stays readable enough for both humans and AI.

## Machine-Checkable Structure First

For portable governance/runtime paths, move meaning downward from prose into
structure the runtime and checkers can actually enforce.

1. `typed structure`: prefer named `dataclass` / `TypedDict` / `Enum` /
   `Literal` / `Protocol` contracts and frozen value objects for stable
   governance concepts. Avoid free strings, boolean bundles, and
   `dict[str, Any]` once a concept's shape is known.
2. `validated transitions`: keep legal state changes in explicit transition
   functions, guards, or bounded state machines rather than in comments,
   conventions, or renderer-local branches.
3. `derived projections`: terminal/chat/dashboard/mobile/markdown surfaces
   should render from typed state and explicit transition outcomes. They do
   not become a second policy owner.
4. `explanatory prose`: comments and docstrings may explain ownership,
   invariants, and why a contract exists, but they must not be the only place
   where structured meaning or policy lives.
5. `governed semantic docs`: when a repo wants near-code semantic docstrings
   or symbol-level semantic blocks, treat them as structured projection over
   canonical typed contracts, not as freeform authority. They may summarize
   ownership, authority tier, invariants, bounded states, transition notes,
   and consumer surfaces, but they must fail closed on drift and must not
   invent policy that the owning contract does not declare.

This is platform-owned doctrine for the governed boundary, not a repo-wide
style law for arbitrary adopter application code. Repo-pack / governance
policy decides where that boundary starts. Inside it, every important concept
should graduate through:

- plan name
- canonical typed contract
- validator / guard
- governed semantic doc projection where useful
- projection / render surface
- parity or end-to-end proof

For this codebase, the missing linker is not "more comments." It is one typed
symbol-semantics layer for selected governance/runtime symbols so the full
platform stack can consume the same semantic record:

- canonical contract owner (`contract_id`, `owner_domain`, `authority_kind`)
- typed inputs / outputs and bounded states
- invariants and transition notes
- declared consumer surfaces
- projection-only vs canonical status
- freshness proof (`signature_hash`, `doc_hash`, version)

That symbol-semantics family should plug into existing repo-owned surfaces
instead of becoming a second prose system:

- `ProjectGovernance` / `DocPolicy` / `DocRegistry` for doc authority and
  lifecycle
- `context-graph` / ZGraph-compatible discovery for retrieval and bootstrap
  context
- `SystemCatalog` / `discover` / dispatch surfaces for capability and consumer
  awareness
- bootstrap/session/render surfaces as near-code semantic projection, never as
  checkpoint or policy authority

The guard rule is strict: when a semantic doc or symbol block mentions a field,
state, consumer, or authority level that the owning typed contract does not
declare, CI should fail and the projection should be treated as stale.

## Semantic Routing Boundary

For this repo, semantics are not "just docstrings" and not merely decorative
metadata. They are the search-space control layer. But the control boundary
must stay explicit:

1. `resume before search`: if a task is a continuation, `session-resume`,
   `SessionCachePacket`, `StartupContext`, and related typed continuity facts
   stay the first-hop bootstrap path.
2. `deterministic narrowing before semantics`: changed paths, lane
   classification, enabled checks, `ProjectGovernance`, `SystemCatalog`, and
   typed work-intake state bound the candidate frontier first.
3. `semantic ranking inside the bound`: `ConceptIndex` / ZGraph-compatible
   graph layers rank, compress, and explain that frontier second. They answer
   "where should the agent look first?" and "how deep should it go?" without
   becoming a new truth owner.
4. `proof after ranking`: guards, parity, end-to-end checks, and typed
   runtime state still prove the decision path. If graph confidence is low or
   a required authority node is missing, the system widens back out to the
   deterministic catalog instead of trusting semantic compression blindly.

That makes the semantic layer first-class for AI/developer navigation while
preserving the compiler-style authority split:

- typed contracts / state machines own legality
- semantic graph / catalog owns routing and compression
- guards / parity / e2e own proof
- docstrings / markdown / dashboards are projections or graph-fed labels

The immediate codebase fit is therefore not "make ZGraph the runtime spine."
It is "make ZGraph a bounded ranking layer behind `SystemCatalog` and
`AgentDispatchPacket`, and prove it improves search without widening authority
or degrading closure."

## Runtime Adoption Checklist

Adopt from agent-first runtimes where it strengthens the governed system:

1. richer session/runtime UX
2. better tool orchestration and execution-mode clarity
3. explicit `plan` / `default` / `auto` style operating modes
4. plugin/MCP-style extensibility
5. delegation/subagent patterns
6. broader environment/tool integration

Do not adopt the parts that would fork authority away from the repo:

1. raw crawler-style context gathering as startup authority
2. prompt-local instructions as the primary policy source
3. runtime permission systems that can disagree with repo governance

## Compiler Roadmap

Use one explicit four-stage roadmap when discussing "compiler-assisted
governance" so the method is not left as scattered checklist items.

1. `Stage 1: Close truth`
   authority, identity, canonical contracts, stable finding ids, and
   projection-vs-authority boundaries.
2. `Stage 2: Honest routing`
   typed edges, trigger tables, reducer receipts, capability derivation,
   bounded inference, and explicit low-confidence states.
3. `Stage 3: Portable packaging`
   repo-pack resolution, onboarding/ratification, installable engine,
   generated setup surfaces, and second-repo/no-core-patch proof.
4. `Stage 4: Compile stable structure`
   precomputed deterministic artifacts that reduce live search space without
   replacing canonical authority.

Stage-4 compile candidates:

1. repo topology indexing
2. import/export graph construction
3. typed contract extraction
4. rule registries
5. file classification
6. change-lane classification
7. allowed boundary maps
8. generated command/check plans
9. stable finding identities
10. schema validation tables
11. adapter/config codegen
12. prebuilt context indices
13. precomputed dependency and ownership maps

Target intermediate representations:

1. `GraphIR`
2. `ContractIR`
3. `AuthorityIR`
4. `BoundaryIR`
5. `CheckPlanIR`
6. `ContextIndexIR`

Over-compilation failure modes to avoid:

1. brittle build products
2. expensive invalidation
3. stale indices
4. overcomplicated IRs
5. too much ceremony for fast-changing work

Language strategy:

1. Rust is strongest for closed-world typed modeling, fast graph/index builds,
   reproducible artifacts, and deterministic IR/schema closure.
2. Python is strongest for orchestration, glue, rapid rule development, CLI
   surfaces, and flexible policy/report plumbing.
3. End-state: Rust owns more of the deterministic semantic/compiler core while
   Python remains the orchestration and tooling shell over those compiled
   artifacts plus live deltas.

## Packaging And Distribution Model

The deployment target is three layers, not "copy the whole `dev/` tree into
another repo."

1. `portable engine`
   install once; owns `devctl`, guard/probe runners, policy resolution,
   startup/work-intake, report/render, and typed contracts.
2. `repo-local pack`
   small adopter-owned authority layer: repo policy, approved governance
   contract, generated surfaces, local report/cache roots, and exceptions.
3. `runtime/client layer`
   optional local shells and integrations such as CLI, VoiceTerm, PyQt6,
   phone/mobile, or later MCP/plugin adapters.

Engine-owned resources such as presets, templates, and setup assets may ship
with the engine. Adopter authority such as docs roots, plan/backlog ownership,
review mode, report roots, and path authority must remain repo-owned and
overridable.

## Memory Architecture

Use one three-tier memory model for the platform's reusable memory/retrieval
story:

1. `exact memory`
   "I have seen this exact case before." Governance equivalent: exact finding,
   fix, or decision fingerprints that let the system skip re-diagnosis.
2. `pattern memory`
   "I have seen this class of behavior before." Governance equivalent:
   recurring repair strategies, reviewed rule-quality history, and repo-local
   pattern hits that bias the next route or fix strategy.
3. `control memory`
   "I have learned how aggressive to be." Governance equivalent: autonomy
   depth, trust weighting, rejection thresholds, and caution levels tuned from
   prior revert/waiver/failure evidence.

Use memory to avoid work. Use deterministic rules to avoid stupid work even
before memory or search fires.

## ZGraph Integration Roadmap

Treat ZGraph as the repo's generated search-space-reduction / memory /
dispatch substrate, not just a graph file format. The integration order is:

1. Scope definition: keep the doctrine explicit in startup/bootstrap surfaces.
2. Startup/work-intake: carry route tiers, reducer receipts, memory hits,
   dispatch reason, and graph snapshot refs in `WorkIntakePacket`.
3. Query stack: move from substring-first lookup to exact/canonical match,
   concept expansion, typed-relation walks, bounded multi-hop inference, then
   fail-closed fallback.
4. Graph widening: add richer node/edge families such as finding, contract,
   test, workflow, config, producer, consumer, and obligation edges.
5. Memory-guided routing: reuse graph snapshots/deltas, fix history, and
   reliability/decision summaries as reusable route bias.
6. Evidence receipts: carry graph/memory route receipts through finding ->
   decision -> run -> outcome so memory remains helpful but non-authoritative.

Implementation order stays the same as the list above. Do not jump to a Rust
compiler core first; make the current authority loop carry the full method
explicitly before hardening or reimplementing it.

## Data Contracts

The current `MP-388..MP-410` consolidation lane adds or tightens these typed
contracts on top of the broader shared inventory below:

`MP-398` and `MP-399` harden the existing governed commit/push contracts
without introducing a new persisted schema family; they close stale index,
push-preflight, and receipt-reporting gaps inside the current typed lane.
`MP-410` keeps the same lane shippable by relocating crowded `devctl` root
modules into topical packages so package-layout enforcement can stay strict
without waivers.

- `RoleOwnershipRule`: typed role-authority row for one durable role, including
  allowed packet kinds, command families, write surfaces, default policy hint,
  and capability flags so planner/auditor/researcher/coordinator behavior does
  not get inferred from provider names or prose.
- `CommandRegistryEntry`: typed custom-command row linking one command id to
  its owning `PlanTargetRef`, allowed roles, policy/default interaction mode,
  writeback surface, and `active|experimental|deprecated` state.
- `PlanSemanticSnapshot`: persisted semantic projection for one governed plan
  doc, including scope-path hints, checklist completion summary, typed
  phase/task rows, stable anchor refs, referenced contract ids, and the source
  revision used to derive `PlanRegistry` / `WorkIntakePacket` routing.
- `PlanMutationReceipt`: typed writeback record for accepted
  `plan_patch_review` packets, carrying packet id, target ref, expected source
  revision, applied `mutation_op`, changed anchor refs, resulting revision, and
  evidence refs so markdown mutation becomes auditable runtime authority rather
  than a silent side effect.

## Shared Contracts

Frontends and repo integrations should converge on one explicit backend
contract set:

- `RepoPack`: declares repo policy, default workflows, docs templates,
  adoption checks, path roots via `RepoPathConfig`, and platform compatibility
  requirements for one codebase family. Repo-pack-owned bootstrap surfaces
  such as local `CLAUDE.md` must also advertise the live governance
  capability set (`ai_instruction`, `decision_mode`,
  `governance-review --record`, operational feedback, and saved snapshot
  baselines) and point agents at the canonical "which tool do I run when?"
  docs until `startup-context` / `WorkIntakePacket` fully absorbs that
  bootstrap role.
- `RepoPathConfig`: repo-pack-owned mapping for active docs, report roots,
  bridge files, generated surfaces, and workflow/artifact paths that portable
  layers must resolve through instead of hard-coded `dev/...` literals or
  `Path(__file__).resolve().parents[...]` assumptions. Keep this contract
  decomposed into bounded path families rather than one ever-growing bag of
  repo knowledge: repo roots, artifact/report roots, plan/docs authority
  paths, memory roots, and review/bridge paths should be separable so callers
  only depend on the slice they actually need. Bridge rendering portability
  fields now include `display_timezone`, `local_state_prefix_rel`, and
  `review_channel_rel` — heartbeat timestamps, worktree-hash exclusion,
  and swarm-mode plan references derive from these instead of hardcoded
  VoiceTerm-specific values.
- `OnboardingContract`: typed adoption/onboarding envelope that records repo
  identity, discovered capabilities, inferred policy payload, path roots,
  required human-authority decisions, onboarding mode
  (`auto|assisted|locked_down`), ratification state, and the reviewed
  contract/artifact refs that future startup surfaces can consume instead of
  repeating first-run setup inference.
- `InferenceProvenance`: per-field explanation for onboarding/draft inference:
  field name, inferred value, source artifact, reason text, confidence, and
  whether the field remains unresolved for human authority.
- `ContextPack`: bounded AI-input bundle with source refs, summaries,
  prioritization metadata, and estimated size/cost fields.
- `ContextBudgetPolicy`: repo-pack-defined limits and fallback behavior for
  bootstrap, adoption-scan, focused-fix, review, and remediation-loop modes.
- `SurfaceOwnershipMap`: repo-pack-owned mapping from path or subsystem slices
  to `voiceterm_client|governance_engine|integration`, consumed by startup,
  routing, and boundary guards instead of ambient path-prefix lore.
- `ControlState`: canonical machine-readable state for runs, findings, sessions,
  approvals, and queue status.
- `TypedAction`: explicit command contract for check, probe, bootstrap, fix,
  report, export, review, and remediation actions.
- `ActionResult`: canonical command/service result envelope carrying
  `schema_version`, `action_id`, success/failure state, reason codes,
  retryability, partial-progress semantics, operator guidance, warnings, typed
  result payloads, and artifact refs so CLI, services, UI clients, hooks, and
  AI wrappers consume one outcome contract.
- `RunRecord`: durable record for one governed execution episode, including
  inputs, context-pack telemetry, artifacts, findings, repairs, approvals, and
  outcomes.
- `DecisionTrace`: typed per-decision explanation artifact linking triggered
  guard/probe outcomes, graph/evidence path, diff or graph-delta summary,
  metrics deltas, confidence, the chosen `DecisionPacket`, and resulting
  outcome so the system can explain why it acted without stitching that story
  back together from unrelated logs or inventing a second proof-only packet.
- `SessionDecisionLog`: typed per-session audit trail derived from
  `DecisionPacket`, guidance adoption/waiver records, evidence refs, and
  outcomes so startup, `CollaborationSession`, and later operators can see
  what the system decided and why without reconstructing that history from
  chat or scattered ledgers.
- `CommandGoalTaxonomy`: stable grouping for canonical backend actions
  (`inspect`, `review`, `fix`, `run`, `control`, `adopt`, `publish`,
  `maintain`) so help, wrappers, skills, startup guides, and future `map`
  suggestions can stay simple without forking action ids.
- `RepoMapSnapshot`: versioned repo-understanding snapshot that combines
  topology, complexity, hotspot ranking, changed-scope overlays, ownership, and
  guard/probe/review overlays into one machine-readable focus surface.
- `MapFocusQuery`: typed request for one bounded repo slice by path/module,
  owner, changed scope, risk lens, or task reference so clients can ask for
  "just the relevant part" without inventing bespoke prompt instructions.
- `TargetedCheckPlan`: machine-readable recommendation of the next guards,
  probes, reports, docs surfaces, or focused tests that should run for a
  `MapFocusQuery`, including rationale and artifact refs.
- `PlanTargetRef`: versioned locator for canonical plan authority targets
  across repos: plan id/scope, target doc path, target kind
  (`section|checklist_item|session_resume|progress_log|audit_evidence`),
  stable anchor keys, and expected revision/hash. Anchor keys must be
  registry-generated machine ids, not free-form prose slugs, and must stay
  collision-free across duplicate headings/checklist labels/log rows through
  normalization plus explicit disambiguation. Planning/runtime flows must
  resolve reviewed markdown through this contract instead of hard-coded file
  names, brittle surrounding prose, or raw line numbers.
- `PlanExpectationPacket`: typed per-slice expectation contract compiled from
  the selected `PlanTargetRef` / `WorkIntakePacket`, carrying invariants,
  required artifacts, forbidden states, validation commands, evidence queries,
  success criteria, and any blast-radius or approval-policy metadata needed to
  reconcile plan truth against observed runtime evidence without letting
  runtime drift silently become authority. Multi-agent sessions must derive
  delegated worker scope from this packet rather than asking workers to infer
  repo-wide intent from prose or file adjacency.
- `WorkIntakePacket`: repo-pack-aware startup/work-intake envelope that binds
  one task to active `PlanTargetRef` entries, changed scope, command goal,
  routed bundle/check plan, designated canonical-write authority, writer-lease
  metadata (`writer_id`, lease epoch, expiry, stale-writer recovery), and the
  durable sinks where accepted findings/decisions/progress must be recorded.
  It also carries role-routing defaults for later conductor fan-out so the
  plan-selected target, allowed command families, and expected writeback sinks
  stay repo-owned even when multiple agents participate. The first stable form
  must also carry deterministic route-selection evidence such as route tier,
  dispatch reason, reducer receipt refs, graph snapshot refs, and bounded
  memory/pattern hits so startup can explain why this slice was selected
  without reintroducing prompt-local crawler logic.
  This is the universal ingestion surface for AI agents, human operators, and
  automation loops. Bootstrap must materialize at least one reviewed
  governance contract, one active-plan registry, one exported `PlanTargetRef`
  set, and one intake projection even in repos that do not begin with
  VoiceTerm-style plan files. During the current authority-loop transition,
  `startup-context` is the bounded typed receipt feeding that future intake
  family; it now emits the packet while returning non-zero when checkpoint
  budget says another implementation slice must stop and cut a checkpoint
  first.
- `DerivedCapabilityContract`: startup/session capability projection derived
  from `ProjectGovernance`, current execution mode, reviewer gate state, and
  repo-pack policy. Required first fields: allowed/denied/ask-first tool
  families, autonomy mode/scope, publish/network/worktree permissions,
  subagent allowance, session TTL, and the rule/provenance refs that explain
  why those capabilities were granted.
- `SessionCapabilityPacket`: bounded runtime/startup projection of
  `DerivedCapabilityContract` for one live session, including the capability
  decision source, expiry/refresh semantics, and the approval-requiring
  actions for the active mode.
- `SharedBacklogDoc`: repo-pack-configured governed backlog/intake surface
  that startup/work-intake may surface as warm context and an accepted
  writeback sink for humans and AI. It stays shared intake rather than plan
  authority; promotion into `MASTER_PLAN` / active-plan state is still
  required before execution.
- `CollaborationSession`: typed shared-work contract derived from
  `WorkIntakePacket`, review state, and writer-lease state so Codex, Claude,
  operators, and future clients can share one live view of
  role assignment (`lead_agent`, `review_agent`, `coding_agent`,
  `reviewer_mode`, `operator_mode`), the current slice, peer findings and
  responses, disagreement/arbitration state, delegated-worker receipts,
  restart/resume state, reviewer ready gates, and the active worker/lane
  registry. Markdown bridges remain projections of this contract rather than
  a second authority for plan or queue state.
- `ReviewerRuntimeContract`: typed reviewer-lifecycle owner nested inside
  `ReviewState`, covering reviewer mode/effective mode, freshness, stale
  reason, last poll, rollover state, session owner, allowed recovery action,
  review acceptance, and publish-clear state. Bridge `review_accepted`,
  doctor/status renderings, and other compatibility surfaces must project this
  contract instead of inventing separate reviewer truth.
  `ReviewState.attention` is a derived projection of the typed
  `recovery_assessment` (diagnosis + decision pair) when both are present:
  `status` from `diagnosis.status`, `owner` from `decision.execution_owner`,
  `summary` from `diagnosis.root_cause`, `recommended_action` from
  `decision.rationale`, `recommended_command` from `decision.command`.
  Runtime doctor snapshots prefer the typed projection over raw attention.
  `check_review_surface_consistency.py` enforces the projection contract;
  drift between raw and projected attention is a CI-blocking parity error.
- `DelegatedWorkPacket`: typed conductor-issued worker contract compiled from
  `WorkIntakePacket` + `PlanExpectationPacket` for one bounded lane. Required
  fields: role id, owned `PlanTargetRef` / issue cluster, owned worktree and
  path scope, allowed command families, required guards/validators, expected
  artifacts and writeback sinks, escalation policy, and return-to-conductor
  receipt contract. Workers consume this packet instead of self-selecting new
  plan targets or scanning the whole repo for adjacent work.
- `PlanMutationOp`: typed mutation contract for canonical plan authority
  targets so adopters do not invent incompatible patch semantics.
  Initial required operations:
  `rewrite_section_note`, `set_checklist_state`, `rewrite_session_resume`,
  `append_progress_log`, and `append_audit_evidence`.
- `Finding`, `FindingReview`, `MetricEvent`: versioned evidence/metrics records
  shared by guards, probes, governance review, replay/evaluation flows, and UI
  projections. `Finding` is the canonical machine record carrying `rule_id`,
  `rule_version`, category/language/severity/confidence, file/span, evidence,
  rationale, suggested fix, autofixable state, suppression metadata, and
  artifact refs so every agent/reviewer/markdown projection derives from the
  same base object. Guard/probe/import-specific shapes may exist only as
  temporary translation seams while the whole evidence flow converges on this
  record.
- `ArtifactStore`: stable path/retention interface for reports, snapshots,
  review packets, cached repo-map state, query indexes, and benchmark evidence.
- `ProviderAdapter`: abstraction over Codex, Claude, or later providers so
  runtime loops do not hard-code one CLI. The adapter boundary must also own
  provider-specific launch args, prompt/bootstrap shaping, role-owned bridge or
  projection labels, heartbeat/ack parsing, session-health probes, and declared
  capability flags such as worker fanout, takeover support, and noninteractive
  wait semantics.
- `TerminalHostAdapter`: abstraction over Terminal.app, Terminus, headless, or
  later session hosts so review/runtime launchers do not hard-code one local
  terminal implementation.
- `WorkflowAdapter`: abstraction over GitHub/CI/local workflow execution so
  Ralph-style or mutation loops stay reusable.
- `ExtensionBundle`: repo-pack-owned generated integration bundle for
  project-scoped Codex/Claude/MCP surfaces. It records emitted files,
  enabled capabilities, source contracts, compatibility/version requirements,
  and parity receipts for artifacts such as `.codex/hooks.json`, `.mcp.json`,
  `.claude/settings.json`, `.claude/agents`, `.claude/skills`,
  `.agents/skills`, and later plugin/marketplace metadata so tool-native
  extensions project one backend authority instead of hand-maintained
  per-tool configs.
- `AutomationSpec`: typed recurring/background-task contract that binds one
  governed goal to schedule class, allowed execution modes, approval policy,
  required artifacts, and writeback sinks so the same automation can run under
  local scheduler, GitHub workflow cron/dispatch, Codex Automations,
  Claude-facing command/agent surfaces, or later queue runners without
  re-encoding policy per transport.

Versioning rules sit beside those contracts, not outside them:

- repo packs must declare `platform_version_requirement`, owned path roots, and
  any compatibility-window assumptions up front
- runtime/artifact payloads and command/service receipts must own explicit
  `schema_version` fields plus one documented migration and rollback path
  before the surface counts as stable
- every durable JSON/JSONL row family must carry that version coverage under a
  guardable contract; schema versioning is not an opt-in cleanup pass
- CI/bootstrap/adoption flows should validate both package/runtime
  compatibility and schema-version compatibility before mutable execution

Architecture-freeze note for the current `P0`/`P1` lane:

- Keep `WorkIntakePacket` and `CollaborationSession` as separate contracts
  through authority-loop closure. `WorkIntakePacket` is the bounded startup /
  work-routing envelope; `CollaborationSession` is the live shared-work
  projection over intake + review/runtime state. Revisit a merged envelope
  only after cross-repo proof shows the separation is redundant.
- Keep delegated worker routing subordinate to canonical plan authority.
  Conductors may fan out many lanes, but every lane must be derived from the
  selected `PlanTargetRef` / `PlanExpectationPacket` path and reported back
  through `CollaborationSession`; capacity tables are not permission for
  open-ended repo-wide scanning.
- Keep intake-backed writer leases as the authority model for canonical plan
  mutation and shared-session ownership. `version_counter`,
  `expected_revision`, and `state_hash` checks are accepted as supplemental
  stale-read/conflict detection, not as replacements for designated writer
  authority.

If a surface cannot be expressed through those shared contracts, it is still
too repo-local to count as extracted.

## VoiceTerm Operator-Shell Contract

VoiceTerm is a good fit for the first-party local operator shell, but it is not
the backend.

Use this decision rule:

1. VoiceTerm may become the richest local cockpit for the extracted platform:
   shared-screen review, staged drafts, queue visibility, PTY-aware status,
   voice shortcuts, launcher actions, and thin client-launch affordances.
2. VoiceTerm must consume the same backend authority as CLI, PyQt6, phone, and
   future skills/hooks. It must not own a second orchestration truth model,
   provider-specific ruleset, or repo-local action router that bypasses the
   shared runtime contracts.
3. PTY/output observation is evidence only. Typed state and typed actions stay
   authoritative.
4. PyQt6 and phone/mobile may still be useful operator clients, but they remain
   peers over the same backend rather than children of a VoiceTerm-only control
   plane.

The target architecture is:

`work-intake packet / review packet / operator intent -> typed queue record ->
TypedAction -> ProviderAdapter or workflow/runtime handler -> staged terminal
packet or non-terminal execution -> receipt/telemetry -> ControlState /
ReviewState projection`

Rules for that queue/action path:

1. Queue records must be typed, replayable, and auditable. Do not use raw chat
   text or textbox state as the canonical queue contract.
2. Any terminal-directed send must be derived from a typed `terminal_packet`
   or equivalent typed action payload with explicit policy, approval, and audit
   semantics.
3. Raw terminal injection may exist only as a bounded execution mechanism under
   the typed action system. It must never become the sole source of truth for
   plan state, review state, or controller state.
4. VoiceTerm may render and stage these actions more elegantly than other
   clients, but another client must still be able to drive the same queue/action
   flow through the same backend contract.
5. If a feature only works when VoiceTerm owns hidden privileged logic, it is
   off-plan and does not count as extracted platform progress.

## Unified System Contract

This product is one system with many interchangeable entrypoints.

Use this rule set:

1. VoiceTerm may be the preferred first-party app for operators who want the
   richest local shell, terminal-native control plane, and voice-assisted
   experience.
2. The same backend must still be callable without VoiceTerm by CLI, PyQt6,
   phone/mobile, skills/hooks, automation loops, and external repos.
3. If a local background service exists, VoiceTerm may host or launch it as a
   convenience, but the service contract must remain product-owned and
   VoiceTerm-optional.
4. PyQt6, phone/mobile, and future wrappers may use VoiceTerm as a richer local
   host path when available, but they must also be able to talk to the same
   backend directly through the same contract.
4.1 Preferred end-state: VoiceTerm should act as the first-party local host
    and supervisor for the shared daemon/controller stack when present, while
    CLI, PyQt6, phone/mobile, and skills/hooks can still attach to that same
    backend directly. Host/supervisor convenience belongs to VoiceTerm;
    backend truth does not.
4.2 Treat the existing VoiceTerm daemon/session transport as necessary but not
    sufficient. PTY/session transport, socket/WebSocket attach, and terminal
    packet staging are not the same thing as the controller loop that owns
    reviewer heartbeat cadence, agent lifecycle `ensure/watch`, queue/action
    routing, and shared review/control-state publishing.
5. Client differences should be shell affordances, not logic forks. VoiceTerm
   may add voice input, PTY-aware staging, richer terminal visualization, and
   local shell ergonomics, but it must not gain unique backend-only semantics
   that other clients can never reach.
6. Repo portability remains mandatory: another repo must be able to install the
   platform without adopting VoiceTerm, while VoiceTerm remains a powerful
   adopter/integration layer for repos that want it.

VoiceTerm action-surface expectation:

1. VoiceTerm should be able to invoke the same platform actions available
   elsewhere: guards, probes, quality-policy/status/report surfaces, bootstrap,
   governance export, review-channel actions, remediation loops, and generated
   skills/hooks/instruction surfaces.
2. VoiceTerm should support those actions in both human-developer and
   agent-assisted modes, including `single_agent`, `active_dual_agent`, and
   `tools_only` flows, using the same routed checks and policy gates as the
   CLI/devctl path.
3. If VoiceTerm offers a richer local UX for those actions, that is an
   adopter-shell advantage, not a license to fork the underlying logic.
4. VoiceTerm should eventually host/supervise the shared daemon/controller
   stack for local-first operation, but that stack must still expose the same
   attach/discovery/auth/state contracts to non-VoiceTerm clients.

What not to do:

1. Do not make PyQt6, iPhone, skills, or automation loops depend on hidden
   VoiceTerm-only state.
2. Do not make VoiceTerm mandatory for non-VoiceTerm adopters.
3. Do not duplicate orchestration logic across clients just to make a local
   surface feel richer.

## Composable Product Rule

The target is not one giant inseparable app and not a pile of unrelated tools.

The target is:

1. a set of major pieces that can each work by themselves in any repo
2. one integrated agent app that composes those same pieces without forking
   their logic

Every major subsystem must therefore satisfy both tests:

1. standalone usefulness
   - it can run from a CLI, API, service, or machine-readable artifact path on
     its own
2. integrated usefulness
   - it plugs into the shared runtime/action/state/evidence contracts so the
     full app becomes smarter without inventing a second backend

If a feature only works inside one client, it is not done.
If a feature only works as an isolated script with no shared contract, it is
not done either.

### Composable product spine

| Piece | Useful by itself | Must also compose into the full app |
|---|---|---|
| `governance_core` | guards, probes, policy, export, bootstrap | shared policy/evidence engine for every client |
| `governance_runtime` | typed state/actions, queueing, receipts | single orchestration truth for the full app |
| repo intelligence | `map`, hotspots, targeted checks | focus/risk engine for AI, UI, and automation |
| evidence and memory bridge | findings, ledgers, attach-by-ref context | durable recall and replay across agent runs |
| tool/action/skill registry | command catalog and action metadata | one action surface for CLI, UI, and AI |
| provider/workflow adapters | Codex, Claude, CI, VCS integration | interchangeable execution backends |
| frontends | CLI, VoiceTerm, PyQt6, phone/mobile | multiple shells over one backend |
| background service/API | attach, resume, watch, supervisor path | lets the app keep working outside chat |
| observability/evals | telemetry, timelines, replay, benchmarks | proves the system is improving and stable |
| repo packs | per-repo defaults and policies | makes the same platform work in any repo |

### Missing product-grade pieces still worth adding

To become a full agent app instead of only a smart governance toolkit, keep
these missing pieces explicit in plan state:

1. one unified agent/job/session/task registry instead of separate loop-local
   notions of work
2. one typed tool/action/skill catalog so AI, CLI, VoiceTerm, and PyQt6 all
   discover the same actions the same way
3. one background attach/resume/watch service contract so the system can keep
   working outside the current chat session
4. one replay/recovery/checkpoint contract so runs can be resumed, audited,
   and recovered after crashes or detach
5. one repo-intelligence store (`map` snapshots, targeted checks, hotspot
   overlays, cache/index) so AI does not keep re-discovering the same repo
6. one evidence-to-memory bridge so findings, runs, and repo intelligence can
   be attached by ref into `ContextPack` instead of copied ad hoc
7. one workflow/preset layer grouped by user goal (`inspect`, `review`, `fix`,
   `run`, `control`, `adopt`, `publish`, `maintain`) instead of command sprawl
8. one operator-visible timeline/observability surface across sessions,
   findings, actions, approvals, and health
9. one evaluation/proof path that measures correctness, structural quality,
   cost, and stability across repos
10. one packaging/install/update/adoption flow that makes the platform feel
    like a product, not a local repo ritual
11. one multi-repo/worktree contract so the app can manage more than a single
    checkout safely
12. one security/approval/identity contract for human, agent, service, and UI
    callers

### Scope filter for new ideas

Before adding a feature or architecture idea to scope, force it through this
filter:

1. Which composable piece does it belong to?
2. What standalone use does it unlock?
3. What shared contract does it reuse instead of bypassing?
4. How does it make the full integrated app better for both AI and humans?
5. What older duplication, hidden state, or prompt ritual does it retire?
6. What proof, guard, or parity test will keep it from becoming fragile?

If an idea cannot answer those questions clearly, it is probably widening
scope more than strengthening the product.

## System Coherence Contract

The missing cross-cutting rule is not "add more features." It is: define one
coherence framework that tells every layer how drift is prevented.

Without that, good subsystems still drift apart on naming, payload shape,
lifecycle semantics, projections, and wrapper behavior.

Use this coherence stack:

| Coherence layer | What must stay consistent | Canonical owner |
|---|---|---|
| vocabulary | command words, wrapper aliases, beginner-facing terms | naming contract + repo policy |
| identity | repo id, worktree id, run id, task id, agent/job/session ids | runtime contracts |
| state | `ControlState`, `ReviewState`, thin snapshots, queue records | `governance_runtime` |
| action | typed action names, params, approvals, receipts | `TypedAction` contract |
| artifact | JSON/JSONL/SQLite payload families, hashes, retention, refs | `ArtifactStore` contract |
| mutation safety | write ownership, idempotency, leases, replay protection | write-arbitration contract |
| repo intelligence | `RepoMapSnapshot`, focus queries, targeted checks | repo-intelligence contract |
| lifecycle | `ensure/start/resume/watch/pause/stop` semantics | service/controller lifecycle contract |
| failure semantics | degraded modes, retryability, partial progress, operator guidance | action-result/error contract |
| projections | markdown, UI panels, phone/mobile, generated docs, charts | projection contract over machine authority |
| parity | provider parity, mode parity, client parity, repo-pack parity | contract-sync + parity fixtures |
| portability | what is portable core vs repo pack vs product integration | layer boundaries + repo-pack contract |
| evolution | deprecation windows, compatibility promises, migration path | public compatibility contract |

### Coherence rules

1. Every major surface must name its canonical owner.
2. Every machine payload family must have a versioned schema.
3. Every human-readable or UI-visible surface must be a projection over a
   stronger machine contract.
4. Every friendly wrapper must resolve to one canonical backend action.
5. Every client must read the same lifecycle and approval semantics.
6. Every repo-pack override must happen through policy/config, not hidden code
   forks.
7. Every public surface must declare compatibility, deprecation, and migration
   rules before it is treated as stable.
8. Every new subsystem must declare how it satisfies this coherence stack
   before it counts as architecture progress.

### Drift-prevention mechanism

The platform should prevent drift with four layers, not one:

1. contract definition
   - typed models, schema versions, canonical ids, lifecycle semantics
2. generated surfaces
   - starter docs, wrappers, skills, and friendly help derived from those
     contracts
3. parity fixtures
   - one backend snapshot should project consistently across CLI, VoiceTerm,
     PyQt6, phone/mobile, and machine outputs
4. drift guards
   - checks that fail when docs, wrappers, schemas, commands, or clients drift
     from the canonical contracts
5. conformance packs
   - adopters, providers, hooks, wrappers, and clients prove they satisfy the
     same required contracts before they count as supported

### The structure-understanding test

The architecture is only clear enough if a new AI or developer can answer
these questions quickly from repo-visible sources:

1. What is the canonical action?
2. What state changes when it runs?
3. What artifact proves it happened?
4. What wrapper/UI names point at it?
5. What checks keep it honest?
6. What is portable versus repo-specific?
7. What happens when it fails, degrades, or runs concurrently with another
   client?

If those answers are not obvious, the structure is still too implicit.

## User-Facing Naming And Abstraction Contract

The product already has far more surface area than a handful of slash
commands. The right abstraction is layered, not flattened.

Use this rule set:

1. Keep backend command ids and typed actions stable, explicit, and technical.
   Those are the maintainer/runtime contract.
2. Add simpler user-facing aliases, slash commands, skills, PyQt6 buttons, and
   VoiceTerm actions on top of that same backend contract for developers,
   agent-assisted users, and less technical operators. Those wrapper names,
   defaults, and starter bundles should be repo-pack/policy configurable so a
   developer or agent adopter can tune the surface without editing core code.
3. Do not make user-facing names the only source of truth. Friendly wrappers
   should resolve to canonical backend actions instead of inventing separate
   workflows.
4. Generated surfaces should expose multiple layers of vocabulary:
   maintainer command ids, operator-friendly aliases, and agent-facing
   skill/slash wrappers.
5. Name user-facing wrappers by intent, not implementation detail. Prefer
   names that explain outcome directly (`review`, `fix`, `run-plan`,
   `phone`, `export`, `publish`, `maintain`) over repo-internal nouns.
6. Guard the mapping between canonical backend ids and friendly wrappers so
   beginner-friendly names never become a second behavior contract.

Current system scope that the naming layer must cover:

1. Quality and guard execution (`check`, `check-router`, `tandem-validate`,
   `probe-report`, quality policy, guard-run).
2. Review artifacts and packets (review packets, handoff packets, loop
   packets, reviewer findings, adjudication).
3. Collaboration/control-plane loops (`review-channel`, `swarm_run`,
   `autonomy-swarm`, `autonomy-loop`, triage/remediation loops).
4. Operator and device surfaces (VoiceTerm, PyQt6, phone/mobile,
   `controller-action`, `phone-status`, `mobile-status`).
5. Portability/adoption/install surfaces (`governance-bootstrap`,
   `governance-export`, `integrations-import`, `render-surfaces`,
   `platform-contracts`).
6. Release/publish/reporting surfaces (`report`, `status`, `docs-check`,
   `release`, `release-gates`, `ship`, package publishing).
7. Maintenance/cleanup surfaces (`process-cleanup`, `reports-cleanup`,
   failure cleanup, plan/index/archive/generated-surface cleanup, stale bridge
   state repair, and governed doc regeneration).

Naming model:

1. Canonical backend command/action ids remain technical and stable.
2. Friendly wrappers should be grouped by one canonical
   `CommandGoalTaxonomy`, for example: `inspect`, `review`, `fix`, `run`,
   `control`, `adopt`, `publish`, `maintain`.
3. Skills/slash commands should wrap those goal groups, not individual internal
   files or one-off prompts.
4. VoiceTerm, PyQt6, CLI, and generated skill surfaces should all project the
   same grouped action model so a user can learn the system once and then use
   it from any client.
5. Grouped discovery/help surfaces such as `devctl list`, startup guides, and
   future `map` check hints should derive from that same taxonomy rather than
   from hand-curated per-client command piles.

## Machine-Readable Projection Contract

Machine-readable output is the canonical contract for automation, agent
ingestion, replay, metrics, and later database/ML indexing. Human-readable
rendering is still required, but it is a projection over the same base data.

Required rules:

1. Command/report surfaces should emit canonical `json`/`jsonl` payloads for
   machine consumers and may also emit `md` or visual renderings for humans.
2. Markdown summaries, flowcharts, hotspot diagrams, and handoff writeups must
   derive from the same underlying machine payload instead of becoming the only
   authoritative output.
3. Tiered review packets for agents, junior developers, and senior reviewers
   should be profile-specific projections over one shared evidence record, not
   separate ad hoc schemas per audience.
4. When automation or AI loops do not need prose, prefer the machine-readable
   projection so context usage stays smaller and ingestion stays deterministic.
5. If a command cannot produce a compact machine-readable payload, it is not
   ready to count as a reusable platform surface yet.

## Context Budget And Usage Contract

Context efficiency is a product requirement, not later optimization debt.

The platform should improve AI coding quality without assuming infinite prompt
windows or silently burning large amounts of provider context. Every governed
AI path must make context use explicit, measurable, and repo-pack tunable.

Required rules:

1. Every AI-facing run mode (`bootstrap`, `adoption-scan`, `focused-fix`,
   `review`, `remediation-loop`) must declare a target context envelope and
   reserved headroom before provider dispatch.
2. Runtime should estimate prompt size before execution (`tokens` when a
   provider tokenizer is available, otherwise bytes/lines/files as fallback)
   and record actual prompt/response usage when the provider exposes it.
3. When context would exceed budget, the runtime must choose an explicit
   fallback path: summarize, rank/prune, split into smaller runs, or fail with
   an operator-visible overflow reason. Silent "send everything" behavior is
   not acceptable.
4. Repo packs own budget profiles and defaults. VoiceTerm can keep richer
   local defaults, but another repo must be able to tighten or expand them
   without patching portable orchestration code.
5. Adoption and usage docs must publish budget-aware operating modes so
   maintainers know when to use full-repo scans versus focused slices and what
   rough context/cost bands to expect.
6. Artifact-cost telemetry must stay in the same contract surface: at minimum
   record artifact path/hash/bytes, estimated tokens, stdout receipt bytes,
   reread avoidance by hash, unchanged-artifact skip counts, and cost per
   accepted fix, false positive, and no-op cycle.

## Architectural Knowledge Base (Topic-Keyed AI Context)

The platform should provide a structured, queryable knowledge store so AI agents
can retrieve architectural context by topic instead of loading entire plan
documents into the context window.

### Problem

Current AI bootstrap loads flat markdown files sequentially (CLAUDE.md →
AGENTS.md → MASTER_PLAN.md → active docs). This works but is expensive:
MASTER_PLAN alone can consume ~78K tokens. Most of that content is irrelevant to
any single task. The existing `trim_to_budget()` system in the Rust memory
substrate handles overflow by dropping results, but it is better to avoid
retrieving irrelevant content in the first place.

### Solution: Topic-Keyed Knowledge Chapters

Add a structured knowledge layer between flat plan docs and the AI context
window. This layer:

1. **Auto-captures** architecturally significant events via scripts that hook
   into guard-run, governance findings, plan edits, contract changes, and
   schema migrations. Each captured event is tagged with a topic key and a
   structured summary.
2. **Stores** captured knowledge in the existing SQLite schema (already defined
   in `memory/schema.rs` with `topics`, `event_topics`, FTS5 search, and 6
   query indexes). The staged SQLite runtime activation becomes the natural
   home for this store.
3. **Organizes** knowledge into topic-keyed chapters like a reference book, each
   with a token budget so the AI pulls only the relevant chapter(s) instead of
   the whole library. Example topic keys: `memory_system`, `governance_engine`,
   `platform_contracts`, `ci_orchestration`, `autonomy_loops`,
   `operator_surfaces`, `review_channel`, `naming_conventions`.
4. **Exports** chapter content as bounded JSON packets that plug directly into
   the existing `ContextPack` builders with token-cost metadata, so the
   retrieval system can make budget-aware decisions.
5. **Integrates** with the `ConceptIndex` / ZGraph navigation artifact so the
   retrieval system can traverse topic dependencies instead of flat lookup.
   When the AI asks about "memory retrieval", the graph says that depends on
   `[memory_system, token_budget, platform_contracts]` and pulls those 3
   chapters (~5.5K tokens) while skipping the other 12 (~15K tokens saved).

### Auto-Capture Heuristics

Scripts should flag events as architecturally significant when:

- A platform contract is added, modified, or removed
- A guard or probe is registered or deregistered
- A schema version changes or a migration path is defined
- An active plan milestone completes or a new MP is created
- A retrieval strategy or context-pack builder changes
- A CI workflow is added, removed, or structurally modified
- A repo-pack policy or bootstrap surface changes
- A naming/convention rule is added or promoted

Each captured event should carry: topic key, summary, source file paths,
schema/contract refs, timestamp, and staleness policy.

### Relationship To Existing Infrastructure

This concept unifies several existing plan items under one coherent model:

- Evidence-to-memory bridge (existing checklist): serialize findings and run
  records into the Rust memory substrate → the knowledge base IS that bridge
- `ConceptIndex` / ZGraph (existing checklist): the topic graph IS the concept
  index, derived from contracts/plans/registry rather than free-form semantics
- Cached repo-intelligence (existing checklist): topic chapters ARE the cached
  artifacts, with invalidation keyed by git diff and policy hashes
- `master-report` aggregate (existing checklist): the aggregate report READS
  from the same topic-keyed store instead of assembling evidence ad hoc
- SQLite query cache (existing checklist): the knowledge base uses the SAME
  staged SQLite schema, just with the runtime activated

### Priority Assignment

This work spans two priority tiers:

- **P0 prerequisite**: activate the SQLite runtime and freeze the
  evidence-to-memory bridge contract (already in the P0 spine)
- **P1 deliverable**: the full topic-keyed knowledge base with auto-capture
  scripts, chapter budgets, ConceptIndex integration, and context-pack export
  (depends on P0 contracts being stable)

Do not pull the full knowledge base forward into P0, but do ensure the P0
evidence-bridge and SQLite activation work is designed with topic-keyed storage
in mind so the P1 layer composes cleanly.

## Adoption Flow

The reusable platform should be easy for an AI or maintainer to stand up in a
new repo:

1. Install the platform package and CLI entrypoint.
2. Run a bootstrap command against the target repo.
3. Generate or select a starter `RepoPack` / repo policy, including
   context-budget defaults.
4. Run adoption scan + probe/report packet against the full worktree.
5. Optionally enable frontends such as the PyQt6 console or phone/mobile view.
6. Start governed AI loops with the same typed runtime contracts and declared
   context-budget profiles used here.

The ideal setup path is a scriptable installer plus AI-readable bootstrap docs,
not a maintainer manually wiring scattered files.

## Extraction Sequence

Sequence the architecture work in this order:

1. Stabilize and package the portable governance engine already tracked under
   `MP-376`.
2. Define the shared runtime/action/state and context-budget contracts so
   Ralph, mutation, review-channel, and process-hygiene flows stop inventing
   repo-local shapes.
3. Move frontend shells to those contracts so PyQt6, CLI, overlay/TUI, and
   mobile status surfaces are projections over the same backend.
4. Introduce repo-pack packaging so VoiceTerm becomes one adopter profile.
5. Validate the extracted platform against multiple external repos before
   treating the packaging boundary as complete.

## Platform Completion Gates

Do not treat this product as "done" when the code merely compiles or when the
portable core has been split into a separate repo. `MP-377` is only complete
when all of these are true:

1. The architecture boundary is real: VoiceTerm consumes the platform through
   explicit repo-pack + CLI/API/runtime contracts rather than internal imports.
2. The enforcement pipeline is trustworthy end to end: local CLI checks, CI
   workflows, docs-governance, review-ledger recording, and telemetry paths
   agree on the same policy surface.
3. Provider parity is proven: Codex and Claude bootstrap from the same
   repo-owned instruction surfaces, resolve the same active-plan chain, and
   run the same routed validation stack by default; any remaining differences
   are adapter-owned, explicit, and test-covered.
4. Mode parity is proven: `active_dual_agent`, `single_agent`, and
   `tools_only` reuse the same backend/runtime/contracts/check stack, with
   only reviewer-liveness/checkpoint semantics changing instead of hidden
   provider-local rules or a second control plane.
5. Extraction/back-import proof is real: the standalone platform repo can be
   validated on pilot repos and then consumed back into VoiceTerm through the
   adopter seam with matching checks, projections, and artifact behavior.
6. Context use is sustainable and operator-visible: budget profiles, overflow
   behavior, telemetry, and usage guidance exist for bootstrap/full-scan/
   focused modes, and quality claims do not depend on hidden oversized prompts.
7. Platform accuracy claims are backed by broad evidence, not only local spot
   wins: repeated adoption scans, replayable evaluation runs, and reviewed
   finding quality across this repo plus external adopters.
8. Python and Rust have both gone through continued pattern-mining passes so
   the first language lanes are materially stronger than today's baseline and
   no longer rely on a narrow initial rule set.
9. The future database/ML path is bounded by explicit provenance,
   privacy/redaction, replay, and waiver/suppression rules.
10. The analyzer architecture is language-extensible: new languages plug into
   shared finding/policy/telemetry contracts instead of forcing a second engine
   design.

## Competitive Differentiators

This product should not be framed as "Semgrep plus AI wrappers" or "a prettier
SonarQube". Its defensible shape is the combination of deterministic policy,
runtime contracts, governed multi-agent execution, and portable repo adoption.

Keep these differentiators explicit in private architecture docs and public
proof packs:

1. adaptive feedback sizing instead of one fixed review verbosity level
2. three-layer enforcement: hard guards, advisory probes, and AI review
3. artifact-backed governed loops with replayable evidence and review ledgers
4. paired reviewer/coder multi-agent orchestration instead of one-shot fixes
5. explicit context-budget contracts as a product requirement, not an afterthought
6. mutation/remediation loops under the same policy and evidence model
7. multi-surface control across CLI, desktop, overlay/TUI, and phone/mobile
8. self-hosted portability through repo packs rather than vendor lock-in

External analyzers such as Ruff, Semgrep, Clippy, cargo-audit, Black, or
future AST/search-rewrite tools are subordinate engines or optional tool
adapters under this control plane. They can feed or extend the platform, but
they are not the product boundary and they are not `v0.1` blockers.

Keep the governed signal taxonomy explicit:

1. `language-engine findings`: Ruff/Semgrep/Clippy/cargo-audit/other scanner
   or formatter results routed through repo-owned policy.
2. `AI-shape findings`: deterministic structural failures common in
   AI-generated or AI-refactored code such as nesting debt, helper
   fragmentation, shim sprawl, layout drift, schema instability, and packaging
   violations. Keep local-shape and architectural-shape signals explicit inside
   this family.
3. `repo-contract findings`: command/docs/listing drift, plan sync, artifact
   contract violations, telemetry obligations, layer-boundary failures, and
   other repo-owned governance mismatches.

Behavioral/domain correctness remains a separate validation lane rather than
the platform's main differentiation claim. Product tests, typed invariants,
domain-specific checks, and runtime validation still own "does it actually do
the right thing?" evidence, while the governance platform is strongest on the
deterministic local-shape, architectural-shape, and repo-contract failures AI
systems repeatedly produce.

Keep the platform stack legible as three layers:

1. `engine tools`: Ruff, Semgrep, Clippy, cargo-audit, and similar rule
   engines answer "did this pattern fire?".
2. `shape rules`: repo-owned AI-shape and repo-contract rules answer "did the
   code or repo drift into the deterministic bad shapes we keep seeing?".
3. `governed loop`: the control plane decides when to run checks, what the AI
   reads, when to repair, when to stop, and how evidence is stored.

The third layer is the product. The first two are inputs to that product.

The governing thesis should stay precise:

- we are not changing model weights
- we are improving the environment the model codes inside
- the loop works by constraint, cleaner context, reduced complexity, and a
  better local search space

Code-shape and agent memory are related but separate problems. This platform
primarily attacks repo/code shape so later AI passes need less context, read
smaller artifacts, and touch fewer unrelated surfaces; memory and retrieval
improve as a consequence of that cleaner environment, not because the platform
solves long-term model memory directly.

## Loop Value Proof

The platform does not get to claim "better code" on intuition alone. Every
portable primitive and every stronger loop claim should prove value on four
axes:

1. `correctness preserved`: tests/build/smoke status before and after.
2. `structural quality improved`: findings before/after, which rule families
   dropped, and accepted fixes versus reverted fixes.
3. `cost justified`: bytes/tokens, artifacts reread, unchanged-artifact skips,
   and AI turns/loops per successful repair.
4. `generalization shown`: repos tested, language mix, fix rate, false
   positives, defer rate, and cleanup rate.
5. `follow-up stability`: whether the next bounded change becomes more local,
   needs less reread context, or avoids breakage that was harder to avoid on
   the first pass.

Do not interpret a zero false-positive rate in isolation as proof of guard
quality. A clean FP column can also mean the surface is only catching obvious
cases, reviewers are over-marking accuracy, or unreviewed findings are being
left out of the ledger. Treat coverage and disposition mix as first-class
evidence, not optional footnotes.

Also track the caution set explicitly:

- high-risk transformations that often change behavior even when shape looks
  better
- noisy rules with high defer/revert/low-trust rates
- large or frequently reopened artifacts that waste context
- common AI-generated bad patterns still passing all current checks
- over-modularization: too many tiny helpers, vague abstractions, or call
  chains that satisfy shape rules while making the code harder to follow
- rule gaming: changes that technically satisfy the rule but do not improve
  readability, maintainability, or safe follow-up edits

## Concrete Migration Roadmap

Use this as the implementation-order contract for `MP-377`. The goal is to
make the boundaries real inside this repo first, then package them, then split
repos only after external-adoption proof exists.

### Target Package Names

Use these package/workspace names unless a later packaging pass finds a strong
reason to rename them:

| Package / layer | Responsibility | Must not own |
|---|---|---|
| `governance_core` | guards, probes, policy resolution, bootstrap, export, review ledger, evaluation/report schemas | repo-specific paths, UI code, provider/workflow execution details |
| `governance_runtime` | `ControlState`, `ReviewState`, `TypedAction`, `RunRecord`, `ArtifactStore`, action dispatch contracts | repo-specific policies, CLI-only parsing, frontend widgets |
| `governance_adapters` | `ProviderAdapter`, `WorkflowAdapter`, VCS/CI/notifier bridges, environment capability detection | repo-pack defaults, frontend shaping, hard-coded VoiceTerm docs/paths |
| `governance_frontends` | CLI surface, PyQt6 console, overlay/TUI, phone/mobile, optional MCP transport | orchestration truth, direct repo-policy logic, hidden state contracts |
| `repo_packs.voiceterm` | VoiceTerm path layout, branch/docs policy, workflow defaults, thresholds, allowlists, release expectations | portable engine code, generic adapters, frontend logic |
| `product_integrations.voiceterm` | VoiceTerm packaging, branding, release wiring, user-facing integration details | portable engine authority, repo-pack-neutral contracts |

### Ownership Boundaries

Apply these boundaries before moving code across repos:

1. `governance_core` may read repo policy, but repo policy must not patch core
   logic.
2. `governance_runtime` is the only place that defines typed action/state/run
   contracts.
3. `governance_adapters` translate external tools and transports into runtime
   contracts; they do not own repo defaults.
4. `governance_frontends` render runtime state and submit typed actions; they
   do not parse repo-local orchestration artifacts directly once a contract
   exists.
5. `repo_packs.voiceterm` owns all VoiceTerm-specific doc lists, path roots,
   workflow defaults, branch policy, and threshold tuning.
6. `product_integrations.voiceterm` may package or brand the system, but it
   must consume the same backend contracts an external adopter would use.

### Portable `v0.1` Release Boundary

The first portable release must stay narrow enough to prove the architecture
without dragging the whole VoiceTerm product surface across the boundary.

`v0.1` in scope:

- installable governance package + stable CLI entrypoint
- repo-pack packaging + compatibility contract
- shared runtime/evidence contracts (`RepoPack`, `RepoPathConfig`,
  `TypedAction`, `ControlState`, `ReviewState`, `RunRecord`, `Finding`,
  `FindingReview`, `MetricEvent`, `ArtifactStore`)
- compact machine receipts for JSON-canonical surfaces
- replay/evaluation harness and first labeled corpus
- Python/Rust-first rule families and policy/evidence flow

`v0.1` explicitly out of scope as blockers:

- PyQt6/operator-console extraction
- iOS/mobile or MCP parity
- full Ralph/review-channel/process-hygiene extraction
- optional external analyzer integrations beyond what already exists in repo
  policy
- broad multi-repo packaging of every frontend or workflow loop

### Phase 0 - Package Boundary And Compatibility Seams

Objective: stop growing the current flat embedded shape while preserving
working imports and commands.

Deliverables:

- create one stable top-level import boundary for portable platform code
- define a real install surface for the governance package: versioned
  `pyproject.toml`, build backend, dependencies, and CLI entrypoint(s) that
  work in a clean environment without `sys.path` patching
- keep compatibility re-exports in old module locations during the move
- define the repo-pack-owned path-resolution contract (`RepoPathConfig`) so
  portable layers stop depending on raw VoiceTerm path literals
- route new files into layer-owned directories only

Initial file moves:

- move platform blueprint helpers under the future `governance_core` path
  starting from:
  - `dev/scripts/devctl/platform/contracts.py`
  - `dev/scripts/devctl/platform/contract_definitions.py`
  - `dev/scripts/devctl/platform/surface_definitions.py`
  - `dev/scripts/devctl/platform/blueprint.py`
- keep `devctl platform-contracts` as a stable public entrypoint:
  - `dev/scripts/devctl/commands/platform_contracts.py`
- harden the install/config seam that currently anchors the embedded layout:
  - `dev/scripts/pyproject.toml`
  - `dev/scripts/devctl/config.py`
- keep the package-layout guard as the enforcement seam:
  - `dev/scripts/checks/check_package_layout.py`
  - `dev/scripts/checks/package_layout/support.py`

Exit criteria:

- new platform code lands under layer-owned directories, not in flat
  `dev/scripts/devctl/` roots
- the governance CLI can be installed in a clean venv/worktree through a real
  package entrypoint
- compatibility imports exist for moved public modules
- portable layers resolve repo-owned paths through repo-pack/path contracts
  instead of direct `dev/active/*`, `dev/reports/*`, or `parents[...]`
  assumptions
- package-layout guard blocks regressions against the new directory contract

### Phase 1 - Extract `governance_core`

Objective: finish the portable engine first.

Scope:

- policy resolution
- guards and probes
- governance bootstrap/export/review
- evaluation/report schemas
- labeled evaluation corpus plus replay harness for version-to-version
  rule/policy comparisons

Files to move first:

- policy/bootstrap/export:
  - `dev/scripts/devctl/quality_policy.py`
  - `dev/scripts/devctl/quality_policy_loader.py`
  - `dev/scripts/devctl/quality_policy_defaults.py`
  - `dev/scripts/devctl/repo_policy.py`
  - `dev/scripts/devctl/governance/bootstrap_policy.py`
  - `dev/scripts/devctl/governance/bootstrap_guide.py`
  - `dev/scripts/devctl/governance_export_support.py`
  - `dev/scripts/devctl/governance_export_artifacts.py`
  - `dev/scripts/devctl/governance_review_log.py`
  - `dev/scripts/devctl/governance_review_models.py`
  - `dev/scripts/devctl/governance_review_render.py`
- portable report/evaluation helpers:
  - `dev/scripts/devctl/review_probe_report.py`
  - `dev/scripts/devctl/probe_report_artifacts.py`
  - `dev/scripts/devctl/probe_topology_builder.py`
  - `dev/scripts/devctl/probe_topology_scan.py`
  - `dev/scripts/devctl/probe_topology_packet.py`
  - `dev/config/templates/portable_governance_eval_record.schema.json`
- guard/probe engine entrypoints remain public but should become thin wrappers:
  - `dev/scripts/checks/check_package_layout.py`
  - `dev/scripts/checks/probe_*.py`
  - `dev/scripts/checks/check_*.py`

Exit criteria:

- another repo can run bootstrap, quality-policy, check, probe-report,
  governance-export, and governance-review without patching core code
- one labeled replay/evaluation path can compare rule or policy revisions
  against the same stored evidence set instead of only live scans
- repo-specific behavior comes only from preset/policy/repo-pack files

### Phase 2 - Extract `governance_runtime`

Objective: replace ad-hoc payload shaping with one executable contract layer.

Scope:

- `ControlState`
- `ReviewState`
- `TypedAction`
- `RunRecord`
- `ArtifactStore`
- `ContextPack`
- `ContextBudgetPolicy`
- `Finding`
- `FindingReview`
- `MetricEvent`
- thin-client snapshot contracts such as `MobileStatusSnapshot`,
  `RalphGuardrailState`, `QualityBacklogState`, and `RepoAnalyticsState`
- promotion/demotion and waiver/suppression lifecycle contracts attached to the
  same evidence model

Files to move first:

- current shared runtime seam:
  - `dev/scripts/devctl/runtime/action_contracts.py`
  - `dev/scripts/devctl/runtime/control_state.py`
  - `dev/scripts/devctl/runtime/review_state.py`
  - `dev/scripts/devctl/runtime/review_state_models.py`
  - `dev/scripts/devctl/runtime/review_state_parser.py`
- current action/control seams that should be re-expressed as runtime
  contracts:
  - `dev/scripts/devctl/commands/controller_action.py`
  - `dev/scripts/devctl/controller_action_support.py`
  - `dev/scripts/devctl/commands/mobile_status.py`
  - `dev/scripts/devctl/mobile_status_views.py`
- current artifact/report retention seams that should collapse into
  `ArtifactStore`:
  - `dev/scripts/devctl/reports_retention.py`
  - `dev/scripts/devctl/path_audit.py`
  - `dev/scripts/devctl/path_audit_report.py`
- current finding/review/metric seams that should converge on shared runtime
  evidence contracts:
  - `dev/scripts/devctl/governance_review_models.py`
  - `dev/scripts/devctl/governance_review_log.py`
  - `dev/scripts/devctl/watchdog/models.py`
  - `dev/scripts/devctl/data_science/metrics.py`

Exit criteria:

- typed JSON contracts are versioned and documented as the canonical state/run
  interface
- typed runtime contracts cover context budgets, finding/review/metric events,
  and thin-client snapshot state instead of leaving those shapes ad hoc
- promotion/waiver behavior is defined against the same evidence model used by
  guards, probes, review ledgers, and replay/evaluation tooling
- frontends can render status and submit actions without importing repo-local
  orchestration packages

### Phase 3 - Extract `governance_adapters`

Objective: move provider/workflow/repo-tool integrations behind adapter
interfaces.

Scope:

- `ProviderAdapter`
- `WorkflowAdapter`
- VCS/CI/notifier/environment adapters

Files to move first:

- Ralph and workflow-control seams:
  - `dev/scripts/coderabbit/ralph_ai_fix.py`
  - `dev/scripts/devctl/commands/ralph_status.py`
  - `dev/scripts/devctl/ralph_status_views.py`
  - `dev/scripts/devctl/collect.py`
  - `dev/scripts/devctl/triage/input_sources.py`
  - `dev/scripts/devctl/triage/loop_support.py`
  - `dev/scripts/devctl/commands/triage_loop.py`
  - `dev/scripts/devctl/commands/mutation_loop.py`
- review/workflow bridge seams:
  - `dev/scripts/devctl/review_channel/core.py`
  - `dev/scripts/devctl/review_channel/state.py`
  - `dev/scripts/devctl/review_channel/event_store.py`
  - `dev/scripts/devctl/review_channel/terminal_app.py`
  - `dev/scripts/devctl/commands/review_channel.py`
  - `dev/scripts/checks/workflow_loop_utils.py`
  - `dev/scripts/devctl/loops/comment.py`
- host/process and integration seams:
  - `dev/scripts/devctl/commands/process_cleanup.py`
  - `dev/scripts/devctl/commands/process_audit.py`
  - `dev/scripts/devctl/commands/process_watch.py`
  - `dev/scripts/devctl/commands/integrations_sync.py`
  - `dev/scripts/devctl/commands/integrations_import.py`

Exit criteria:

- Ralph, mutation, review-channel, and process-hygiene flows execute through
  adapter contracts, not direct VoiceTerm-only assumptions
- provider/workflow selection is data-driven and repo-pack aware
- environment detection and external-tool capability checks are consolidated
  through adapter-owned seams instead of scattered `shutil.which()` or
  platform-specific branching

### Phase 4 - Converge `governance_frontends`

Objective: turn every surface into a thin client over runtime contracts.

Scope:

- CLI
- PyQt6 Operator Console
- phone/mobile
- overlay/TUI
- optional MCP

Files to move or rewire first:

- Operator Console readers that must stop importing repo-local orchestration:
  - `app/operator_console/state/review/review_state.py`
  - `app/operator_console/state/review/artifact_locator.py`
  - `app/operator_console/state/bridge/bridge_sections.py`
  - `app/operator_console/state/snapshots/phone_status_snapshot.py`
  - `app/operator_console/state/snapshots/analytics_snapshot.py`
  - `app/operator_console/state/snapshots/quality_snapshot.py`
  - `app/operator_console/state/snapshots/ralph_guardrail_snapshot.py`
  - `app/operator_console/state/snapshots/watchdog_snapshot.py`
  - `app/operator_console/state/snapshots/snapshot_builder.py`
  - `app/operator_console/state/sessions/session_trace_reader.py`
  - `app/operator_console/workflows/workflow_presets.py`
- CLI surfaces that should become frontend wrappers over runtime actions:
  - `dev/scripts/devctl/commands/status.py`
  - `dev/scripts/devctl/commands/report.py`
  - `dev/scripts/devctl/commands/phone_status.py`
  - `dev/scripts/devctl/commands/platform_contracts.py`

Exit criteria:

- frontends import runtime contracts plus repo-pack metadata only
- frontends no longer parse raw review-channel markdown or VoiceTerm-only
  artifact conventions when a typed contract exists
- frontend CI/governance checks block new direct `dev.scripts.devctl`
  orchestration imports in console/UI code once the replacement runtime
  contract exists

### Phase 5 - Define `repo_packs.voiceterm`

Objective: isolate all VoiceTerm-specific defaults in one adopter profile.

Scope:

- path/layout rules
- repo-path resolution / artifact-root metadata
- docs expectations
- branch/release policy
- platform-version compatibility requirements
- schema-version ownership, migration rules, and rollback/back-compat
  expectations for repo-pack-facing payloads
- workflow defaults
- threshold tuning and allowlists

Files to move or consolidate first:

- repo policy and presets:
  - `dev/config/devctl_repo_policy.json`
  - `dev/config/quality_presets/voiceterm.json`
- VoiceTerm-specific docs/runbook contracts:
  - `AGENTS.md`
  - `dev/active/INDEX.md`
  - `dev/active/MASTER_PLAN.md`
  - `dev/guides/DEVELOPMENT.md`
  - `dev/scripts/README.md`
- current hard-coded VoiceTerm defaults that should become repo-pack metadata:
  - `dev/scripts/devctl/review_channel/core.py`
  - `dev/scripts/devctl/review_channel/parser.py`
  - `app/operator_console/workflows/workflow_presets.py`

Exit criteria:

- another repo can adopt the platform by choosing a repo pack rather than
  copying VoiceTerm docs/path logic
- repo packs declare both repo-path roots and `platform_version_requirement`
  metadata so compatibility can be checked before bootstrap or runtime launch
- compatibility validation covers runtime/package compatibility plus
  schema-version migration and rollback expectations instead of only one static
  version pin
- VoiceTerm-specific governance lives outside the portable core

### Phase 6 - External Pilots And Repo Split Gate

Objective: prove the boundaries before creating separate GitHub repos.

Required pilot flow:

1. install the packaged platform
2. validate repo-pack/platform compatibility before bootstrap
3. run bootstrap against a non-VoiceTerm repo
4. select or generate a repo pack
5. run `quality-policy`, `check --adoption-scan`, and `probe-report`
6. render at least one frontend/status surface
7. run at least one governed loop without patching core code
8. publish the install/adoption proof pack: package install steps,
   compatibility contract, and the public whitepaper/comparison derived from
   the durable guide

Split readiness gate:

- two external repos succeed without core-engine patching
- repo-pack/platform compatibility is versioned, enforced, and exercised
  through at least one upgrade path
- no frontend imports repo-local orchestration packages directly
- Ralph/review-channel/process-hygiene run through adapter contracts
- repo-local assumptions live in repo-pack metadata only

Only after those gates pass should the code be split into separate GitHub
repositories.

### Proposed Repo Split After Proof

If the pilot gate passes, split in this order:

1. `governance-core`
2. `governance-runtime` (or fold into `governance-core` if it stays compact)
3. `repo-pack-voiceterm`
4. optional `governance-operator-console`
5. VoiceTerm remains a product integration and first consumer

### Current Anti-Patterns To Burn Down Before Split

These patterns are explicitly not acceptable at repo-split time:

- portable packages deriving identity from `Path(__file__).resolve().parents[3]`
- frontends importing `dev.scripts.devctl.*` orchestration internals directly
- hard-coded `dev/active/*`, `dev/reports/*`, `bridge.md`, or VoiceTerm MP
  identifiers inside portable layers
- blueprint-only contracts with no executable runtime owner
- loops that require repo-specific shell commands in core logic rather than
  adapter or repo-pack configuration

### Self-Hosting Enforcement Backlog

The current governance stack catches many local clean-code problems but still
misses several platform-boundary failures because those categories do not yet
have first-class guards/probes. "Why didn't the tools catch this?" must now be
treated as a tracked product question, not a post-hoc complaint.

Before calling extraction mature, the platform should self-host these rule
families against its own tree:

- layer-boundary enforcement that blocks frontends from importing
  orchestration internals once runtime contracts exist
- portable-path construction enforcement that rejects raw
  `Path(__file__).resolve().parents[...]` and other VoiceTerm-specific path
  derivation outside approved bootstrap seams
- provider/workflow adapter-routing enforcement that detects direct provider
  CLI or workflow-tool execution where adapter contracts should own the call
- contract-completion/orphaned-contract enforcement so blueprint-only runtime
  contracts do not linger unused in production code
- schema/platform compatibility enforcement covering
  `platform_version_requirement`, `schema_version`, migration, and rollback
  expectations
- repeatable command-source and shell-execution checks for high-signal cases
  where config or user-controlled input can flow into subprocess or shell
  execution without adapter/runtime validation
- Python contract probes for repeatable typed-boundary blind spots that keep
  surfaced findings opaque (`TypedDict`-sized dict payloads, overly broad
  `Any`, untyped unions at dispatch seams) when those patterns remain
  measurable and low-noise

Every time an audit or external review finds a product-boundary defect, the
follow-up should record whether the miss belongs to an existing rule, a new
rule family, richer runtime contracts, or an explicitly out-of-scope category.

### 2026-03-15 Separation Audit - Remaining VoiceTerm Coupling

The current architecture direction is still right, but the remaining extraction
blockers are now explicit.

`P0` contract blockers:

1. Portable/runtime layers still import the concrete VoiceTerm repo pack
   directly instead of resolving an active repo-pack boundary.
   Current hotspots:
   `quality_policy.py`, `quality_policy_loader.py`, `audit_events.py`,
   `reports_retention.py`, `review_probe_report.py`, `data_science/metrics.py`,
   `publication_sync/core.py`, `integrations/federation_policy.py`,
   `governance_review_log.py`, `governance/external_findings_log.py`,
   `autonomy/{run_parser,benchmark_parser,report_helpers}.py`,
   `review_channel/{core,event_store,promotion,state}.py`,
   `watchdog/episode.py`, `commands/audit_scaffold.py`,
   `cli_parser/reporting.py`.
   Required exit: those modules must consume an active repo-pack/path provider
   contract instead of importing `repo_packs.voiceterm` or
   `VOICETERM_PATH_CONFIG` directly.
2. Frontends still import repo-internal `devctl` modules and VoiceTerm path
   config directly instead of consuming one installable runtime/API contract.
   Current hotspots:
   PyQt6 Operator Console modules under
   `app/operator_console/{run.py,logging_support.py,layout/,collaboration/,state/,workflows/}`,
   iOS preview/demo scaffolding in
   `app/ios/VoiceTermMobile/Sources/VoiceTermMobileCore/MobileRelayPreviewData.swift`,
   and Rust review-artifact readers in
   `rust/src/bin/voiceterm/dev_command/review_artifact/artifact.rs`.
   Required exit: frontends consume shared runtime state/contracts plus
   repo-pack metadata or emitted projections, not `dev.scripts.devctl.*`
   layout details.
3. The transitional markdown bridge is still embedded into runtime/client code
   as a live assumption instead of being only a temporary projection.
   Current hotspots:
   `review_channel/{core,prompt,handoff,heartbeat,reviewer_state}.py`,
   `check_review_channel_bridge.py`,
   `app/operator_console/state/bridge/bridge_sections.py`,
   `app/operator_console/state/review/artifact_locator.py`, and
   `rust/.../review_artifact/artifact.rs`.
   Required exit: `review_state.json`, `controller_state`, and registry/event
   projections become authoritative; `bridge.md` remains a generated,
   repo-pack-owned projection/bootstrap/debug frontend instead of a VoiceTerm-
   local authority seam.
4. VoiceTerm integration details still leak through shared tooling defaults.
   Current hotspots:
   `commands/check_support.py` (`voiceterm_tui.log`),
   `process_sweep/config.py` (`VOICETERM_*` process signatures),
   VoiceTerm-specific environment/log paths in release/mobile helpers, and
   direct `voiceterm_repo_root()` fallbacks in governance logs.
   Required exit: move these assumptions under `repo_packs.voiceterm` or
   `product_integrations.voiceterm` instead of leaving them in shared tooling.

Separation-first queue:

1. Replace direct `repo_packs.voiceterm` imports in portable/runtime/tooling
   layers with active repo-pack resolution and generic path-provider wiring.
2. Move frontend consumers onto shared runtime/API contracts and generated
   projections instead of `dev.scripts.devctl.*` imports.
3. Demote the markdown bridge from live runtime assumption to optional
   repo-pack-portable projection/bootstrap/debug mode over the same backend
   authority instead of deleting markdown outright. If adopters want a
   markdown coordination surface, it should work through the same typed
   backend and repo-pack templates in any repo rather than remaining a
   VoiceTerm-only special case.
4. Isolate remaining VoiceTerm-named env/log/process/product details under the
   adopter/integration layer.
5. Re-run the whole-system coupling inventory after each tranche and keep the
   remaining embedded assumptions listed here until they are gone.

## Consolidated Architecture Assessment And Roadmap

This section is the in-repo scope-preservation record for `MP-377`. It pulls
the repo-grounded architecture review, boundary decisions, and staged roadmap
into one active markdown plan so the work is not trapped in chat history or
split across overlapping documents.

### A. Executive Summary

- This assessment is based on the local checked-out repository, not GitHub.
  Inspected: `git status --short`, `AGENTS.md`,
  `dev/active/MASTER_PLAN.md`, `dev/config/devctl_repo_policy.json`,
  `dev/active/ai_governance_platform.md`,
  `dev/guides/AI_GOVERNANCE_PLATFORM.md`,
  `dev/scripts/devctl/platform/contract_definitions.py`,
  `dev/scripts/devctl/runtime/action_contracts.py`.
  Verified: the local worktree is materially ahead of or different from any
  public baseline, including local architecture work across governance docs,
  policy/config, `devctl`, and platform/runtime surfaces.
  Inferred: local codebase reality must override any simpler public-repo mental
  model.
- The strongest architecture already present is broader and better than a
  portable-guards-only framing. Inspected:
  `dev/active/ai_governance_platform.md`,
  `dev/guides/AI_GOVERNANCE_PLATFORM.md`,
  `dev/scripts/devctl/platform/contract_definitions.py`,
  `dev/scripts/devctl/platform/surface_definitions.py`,
  `dev/scripts/devctl/runtime/control_state.py`.
  Verified: the repo already contains a five-layer governance platform thesis
  centered on `governance_core`, `governance_runtime`,
  `governance_adapters`, `governance_frontends`, and `repo_packs`, plus
  CLI-first determinism, typed runtime contracts, repo-pack policy layering,
  PyQt thin-client intent, and optional MCP alignment.
  Inferred: the right move is extraction and consolidation, not reinvention.
- Recommended direction: make the standalone governance product the primary
  architecture now, preserve `devctl` as the core, promote the repo-pack
  model, generate policy surfaces from one canonical config, move VoiceTerm to
  consumer/integration status, and defer DB-first / ML-first work until the
  package boundary and documentation authority are stable.

### B. Current Codebase Assessment

- The repo is already two intertwined systems: a VoiceTerm runtime/product and
  an embedded governance/control-plane product.
  Inspected: `dev/scripts/devctl.py`, `dev/scripts/devctl/cli.py`,
  `app/operator_console/README.md`,
  `rust/src/bin/voiceterm/memory/store/sqlite.rs`,
  `dev/active/ai_governance_platform.md`.
  Verified: the governance stack is not just helper scripts.
  Inferred: it should stop being treated as an internal VoiceTerm subsystem.
- The local worktree itself is an architectural signal.
  Inspected: `git status --short`, `dev/scripts/devctl/platform/`,
  `dev/scripts/devctl/runtime/`, `dev/scripts/checks/package_layout/`,
  `dev/scripts/coderabbit/`, `dev/scripts/workflow_bridge/`.
  Verified: there is local-only and in-flight architecture work.
  Inferred: recommendations that ignore the dirty local tree will be wrong.
- The authority stack is clear at the top and fragmented below.
  Inspected: `AGENTS.md`, `CLAUDE.md`, `dev/active/INDEX.md`,
  `dev/active/MASTER_PLAN.md`, `dev/active/portable_code_governance.md`,
  `dev/active/ai_governance_platform.md`.
  Verified: `AGENTS -> INDEX -> MASTER_PLAN` is the declared authority chain.
  Inferred: the next problem is not missing governance, it is fragmented
  governance.
- The current implementation style is thin-client, artifact-backed, and
  command-driven.
  Inspected: `app/operator_console/state/snapshots/snapshot_builder.py`,
  `app/operator_console/workflows/command_builder_core.py`,
  `dev/scripts/devctl/commands/check.py`,
  `dev/scripts/devctl/runtime/control_state.py`.
  Verified: the code already prefers deterministic commands and file-backed
  artifacts.
  Inferred: the standalone product should standardize that model rather than
  replace it with an app-centric backend.

### C. What Already Exists

- `CLI-first source of truth`: already implemented.
  Inspected: `dev/scripts/devctl.py`, `dev/scripts/devctl/cli.py`,
  `dev/scripts/devctl/commands/check.py`,
  `dev/scripts/devctl/bundle_registry.py`.
  Verified: `devctl` owns command parsing, policy resolution, checks, bundles,
  and post-command telemetry.
  Inferred: this is the right extraction nucleus.
- `Deterministic analyzers, guards, and probes`: already implemented.
  Inspected: `dev/scripts/devctl/quality_policy_defaults.py`,
  `dev/scripts/devctl/quality_policy.py`,
  `dev/scripts/checks/check_code_shape.py`,
  `dev/scripts/checks/check_package_layout.py`,
  `dev/scripts/checks/probe_compatibility_shims.py`.
  Verified: the repo currently resolves 28 AI guards and 15 review probes in
  the active policy.
  Inferred: the core product claim already exists.
- `Repo-pack style policy layering`: partially implemented.
  Inspected: `dev/config/devctl_repo_policy.json`,
  `dev/config/quality_presets/portable_python.json`,
  `dev/config/quality_presets/portable_rust.json`,
  `dev/config/quality_presets/portable_python_rust.json`,
  `dev/config/quality_presets/voiceterm.json`,
  `dev/scripts/devctl/platform/contract_definitions.py`.
  Verified: presets, repo overrides, and a `RepoPack` contract already exist.
  Inferred: this needs to become a first-class package/install surface.
- `Generated agent surfaces from canonical policy`: partially implemented.
  Inspected: `dev/scripts/checks/check_agents_bundle_render.py`,
  `dev/scripts/checks/check_agents_contract.py`, `AGENTS.md`, `CLAUDE.md`,
  `dev/scripts/devctl/bundle_registry.py`.
  Verified: only the AGENTS bundle surface is rendered and checked;
  `CLAUDE.md` remains manual/local-only.
  Inferred: the repo does not yet have the single-source generation model we
  need.
- `Thin skills/templates`: partially implemented.
  Inspected: `dev/templates/slash/README.md`,
  `dev/templates/slash/claude/SKILL.md`,
  `dev/templates/slash/codex/voice.md`.
  Verified: the repo already uses thin skill/slash templates as adapters over
  real runtime commands.
  Inferred: this is the right model to generalize.
- `Hooks as deterministic enforcement`: implemented but should be redesigned.
  Inspected: `.pre-commit-config.yaml`,
  `.github/workflows/tooling_control_plane.yml`,
  `.github/workflows/release_preflight.yml`, `.git/hooks`.
  Verified: enforcement exists via `devctl`, CI, and optional pre-commit;
  `.git/hooks` is not the real system boundary.
  Inferred: future hook surfaces should be generated adapters, not assumed
  local git-hook state.
- `Structured telemetry and history`: partially implemented.
  Inspected: `dev/scripts/devctl/audit_events.py`,
  `dev/scripts/devctl/governance_review_log.py`,
  `dev/scripts/devctl/review_probe_report.py`,
  `dev/scripts/devctl/watchdog/episode.py`,
  `dev/scripts/devctl/data_science/metrics.py`,
  `dev/reports/governance/finding_reviews.jsonl`,
  `dev/reports/data_science/history/snapshots.jsonl`.
  Verified: the repo already has multiple durable JSONL/NDJSON ledgers.
  Inferred: a canonical artifact/event-store contract is needed before a
  heavier database layer.
- `Database-backed system of record`: missing.
  Inspected: repo-wide sqlite usage,
  `rust/src/bin/voiceterm/memory/store/sqlite.rs`,
  `integrations/code-link-ide/docs/spec/audit-log.md`, local `orb.db`.
  Verified: there is no repo-wide governance DB in active use.
  Inferred: JSONL plus optional SQLite index is the right near-term target.
- `PyQt6 observability layer`: already implemented but should be redesigned.
  Inspected: `app/operator_console/README.md`,
  `app/operator_console/views/main_window.py`,
  `app/operator_console/views/ui_refresh.py`,
  `app/operator_console/state/snapshots/analytics_snapshot.py`,
  `app/operator_console/state/snapshots/phone_status_snapshot.py`.
  Verified: the UI is real and useful.
  Inferred: it must stop importing repo-local internals and hard-coding
  VoiceTerm paths if it is to become a reusable frontend.
- `Typed runtime contracts`: partially implemented.
  Inspected: `dev/scripts/devctl/runtime/action_contracts.py`,
  `dev/scripts/devctl/runtime/control_state.py`,
  `dev/scripts/devctl/runtime/review_state.py`,
  `dev/scripts/devctl/platform/contract_definitions.py`.
  Verified: `TypedAction`, `RunRecord`, `ArtifactStore`, `ControlState`, and
  `ReviewState` exist already.
  Inferred: those seams should become the actual dependency direction, not
  just blueprint docs.
- `Optional MCP`: already implemented in the right posture.
  Inspected: `dev/scripts/devctl/commands/mcp.py`,
  `dev/guides/MCP_DEVCTL_ALIGNMENT.md`,
  `dev/active/slash_command_standalone.md`.
  Verified: current MCP is read-only/additive and explicitly not the authority
  layer.
  Inferred: keep it optional and late.
- `Safe remediation loops`: partially implemented.
  Inspected: `dev/scripts/coderabbit/ralph_ai_fix.py`,
  `dev/scripts/devctl/commands/triage_loop.py`,
  `dev/scripts/devctl/commands/mutation_loop.py`,
  `dev/scripts/devctl/commands/autonomy_loop.py`,
  `dev/config/control_plane_policy.json`.
  Verified: the repo already has bounded refinement/fix loops with policy
  gates.
  Inferred: these belong in an adapter/orchestration layer, not in the core
  rule engine.
- `ML later, not enforcement`: partially implemented in the right direction.
  Inspected: `dev/scripts/devctl/data_science/metrics.py`,
  `dev/config/templates/portable_governance_episode.schema.json`,
  `dev/config/templates/portable_governance_finding_review.schema.json`,
  `dev/guides/PORTABLE_CODE_GOVERNANCE.md`.
  Verified: telemetry, evaluation records, and finding ledgers already exist.
  Inferred: the substrate for later ranking exists without letting ML replace
  deterministic checks.

### C.5. Other Architectural Patterns Already Present In The Repo

- `Review-channel collaboration runtime`: preserve and merge into the
  standalone runtime as a collaboration/approval subsystem.
  Inspected: `dev/scripts/devctl/review_channel/event_store.py`,
  `dev/scripts/devctl/review_channel/state.py`,
  `app/operator_console/collaboration/conversation_state.py`,
  `app/operator_console/collaboration/task_board_state.py`,
  `app/operator_console/collaboration/timeline_builder.py`.
  Verified: collaboration packets, approvals, and session views already exist.
  Inferred: this is a product differentiator the original prompt
  underestimated.
- `Continuous swarm / rollover / shared-screen workflow`: preserve, but keep
  it above the core engine.
  Inspected: `dev/active/continuous_swarm.md`,
  `dev/active/review_channel.md`,
  `dev/scripts/devctl/commands/review_channel.py`.
  Verified: the repo already has a serious multi-agent orchestration model.
  Inferred: it should become a reusable workflow-adapter layer.
- `Host-process hygiene and execution cleanup`: preserve as an optional
  extension.
  Inspected: `dev/scripts/devctl/commands/process_cleanup.py`,
  `dev/scripts/devctl/commands/process_audit.py`,
  `dev/scripts/devctl/commands/process_watch.py`,
  `dev/active/host_process_hygiene.md`.
  Verified: process hygiene is already a governed subsystem.
  Inferred: keep it repo-pack or platform-extension scoped, not mandatory for
  every adopter.
- `Memory + Action Studio`: preserve separately and do not collapse it into the
  governance core.
  Inspected: `dev/active/memory_studio.md`,
  `rust/src/bin/voiceterm/memory/store/sqlite.rs`,
  `rust/src/devtools/events.rs`, `rust/src/devtools/storage.rs`.
  Verified: there is already a parallel structured-memory architecture.
  Inferred: share event-store ideas, but do not let memory broaden the first
  standalone-governance scope.
- `Federated import/reuse model`: preserve as reference/import tooling, not a
  runtime dependency.
  Inspected: `dev/integrations/EXTERNAL_REPOS.md`,
  `dev/scripts/devctl/commands/integrations_sync.py`,
  `integrations/ci-cd-hub/pyproject.toml`,
  `integrations/code-link-ide/docs/spec/audit-log.md`.
  Verified: the repo already studies and reuses external patterns in a
  disciplined way.
  Inferred: that helps extraction, but submodules must not become the package
  boundary.
- `Graph/report/topology observability`: preserve and use as the basis for
  explainability.
  Inspected: `dev/scripts/devctl/probe_report_artifacts.py`,
  `dev/reports/probes/latest/review_packet.md`,
  `dev/reports/probes/latest/hotspots.mmd`.
  Verified: graph/topology outputs already exist.
  Inferred: the PyQt6 UI should consume these instead of inventing its own
  ranking logic.

### D. Gaps And Architectural Problems

- There is no single canonical architecture document today unless this plan is
  explicitly used that way.
  Inspected: `dev/active/portable_code_governance.md`,
  `dev/active/ai_governance_platform.md`,
  `dev/guides/PORTABLE_CODE_GOVERNANCE.md`,
  `dev/guides/AI_GOVERNANCE_PLATFORM.md`.
  Verified: architecture is split across two active plans and two durable
  guides.
  Inferred: consolidation is not optional.
- Execution state is distributed even though `MASTER_PLAN` is supposed to be
  singular tracker authority.
  Inspected: `dev/active/MASTER_PLAN.md`, `dev/active/operator_console.md`,
  `dev/active/autonomous_control_plane.md`,
  `dev/active/review_channel.md`, `dev/active/review_probes.md`.
  Verified: multiple scope docs still carry live checklist/progress state.
  Inferred: contributors can follow the wrong plan even while obeying docs.
- Surface generation is incomplete.
  Inspected: `dev/scripts/checks/check_agents_bundle_render.py`, `CLAUDE.md`,
  `dev/templates/slash/claude/SKILL.md`.
  Verified: AGENTS bundle rendering exists, but no general
  `AGENTS` / `CLAUDE` / skills / hooks generator does.
  Inferred: drift remains structurally likely.
- The artifact model is structured but fragmented.
  Inspected: `dev/scripts/devctl/audit_events.py`,
  `dev/scripts/devctl/governance_review_log.py`,
  `dev/scripts/devctl/review_probe_report.py`,
  `dev/scripts/devctl/watchdog/episode.py`,
  `dev/scripts/devctl/review_channel/event_store.py`.
  Verified: there are multiple ledgers with overlapping semantics.
  Inferred: a canonical run/finding/artifact model is needed before a DB or
  more dashboards.
- Portability blockers are real and concrete.
  Inspected: `app/operator_console/state/snapshots/analytics_snapshot.py`,
  `app/operator_console/state/snapshots/quality_snapshot.py`,
  `dev/scripts/devctl/metric_writers.py`,
  `dev/scripts/devctl/governance_export_support.py`.
  Verified: parts of the system assume the current repo root or home-directory
  paths.
  Inferred: extraction will fail unless those assumptions move behind
  repo-pack/runtime contracts.
- The package layout itself says extraction is overdue.
  Inspected: `dev/scripts/checks/check_package_layout.py` plus current output,
  `dev/scripts/checks/probe_compatibility_shims.py` plus current output.
  Verified: crowded directories include `dev/scripts/checks`,
  `dev/scripts/devctl`, and `dev/scripts/devctl/commands`, and root shim debt
  still exceeds budget.
  Inferred: the codebase is already telling us to split the platform cleanly.
- Repo policy shape is brittle.
  Inspected: `dev/config/devctl_repo_policy.json`,
  `dev/scripts/devctl/quality_policy_loader.py`.
  Verified: the policy file currently has duplicate top-level
  `repo_governance` keys and the loader path does not reject that by contract.
  Inferred: canonical policy generation will remain fragile until both the
  file and loader are normalized.

### D.5. Separation And Repo-Boundary Analysis

- What should be extracted first is the real portable core.
  Inspected: `dev/scripts/devctl/quality_policy.py`,
  `dev/scripts/devctl/quality_policy_defaults.py`,
  `dev/scripts/devctl/commands/check.py`,
  `dev/scripts/devctl/commands/governance/export.py`,
  `dev/scripts/devctl/commands/governance/bootstrap.py`,
  `dev/scripts/devctl/commands/governance/review.py`,
  `dev/scripts/checks/`.
  Verified: these are already mostly productized.
  Inferred: they belong in the standalone repo before frontends move.
- What can remain temporarily bridged is VoiceTerm-specific integration.
  Inspected: `pypi/src/voiceterm/cli.py`, `app/operator_console/`,
  Rust overlay/runtime code, `.github/workflows/`.
  Verified: these are product/integration layers, not the governance core.
  Inferred: they should consume the extracted platform, not host it.
- The biggest blockers to extraction are direct imports and path assumptions.
  Inspected: `app/operator_console/state/snapshots/analytics_snapshot.py`,
  `app/operator_console/state/snapshots/phone_status_snapshot.py`,
  `app/operator_console/workflows/command_builder_core.py`,
  `dev/scripts/devctl/governance_export_support.py`.
  Verified: clients and export code still assume this repo's filesystem layout.
  Inferred: a package boundary without contract cleanup would only move the
  coupling elsewhere.
- VoiceTerm's future consumption model should be external CLI/API plus repo
  pack, not internal module imports.
  Inspected: `dev/scripts/devctl/platform/contract_definitions.py`,
  `dev/scripts/devctl/runtime/action_contracts.py`,
  `dev/config/devctl_repo_policy.json`.
  Verified: the needed contracts already exist in seed form.
  Inferred: VoiceTerm should call the standalone system the same way another
  repo would.
- Avoid drift by making repo packs versioned and tested.
  Inspected: `dev/scripts/devctl/commands/quality_policy.py`,
  `dev/scripts/devctl/commands/platform_contracts.py`,
  `dev/scripts/checks/check_architecture_surface_sync.py`.
  Verified: the repo already has contract-oriented validation habits.
  Inferred: use that to pin repo-pack/platform compatibility.

### D.6. Documentation / Planning Fragmentation Analysis

- Keep `dev/active/MASTER_PLAN.md` as the tracker only.
  Verified from `AGENTS.md` and `dev/active/INDEX.md`: it is the canonical
  execution tracker.
  Inferred: it should stop doubling as a partial architecture document.
- Make `dev/active/ai_governance_platform.md` the single active architecture
  plan for the standalone product.
  Verified: it already owns the broader reusable-platform lane.
  Inferred: it is the strongest candidate for consolidation and should be the
  main plan for this scope.
- Fold `dev/active/portable_code_governance.md` into a narrower engine-focused
  companion role rather than keeping it as peer architecture authority.
  Verified: it overlaps heavily with the broader platform plan.
  Inferred: keeping both as peers will keep causing drift.
- Make `dev/guides/AI_GOVERNANCE_PLATFORM.md` the single durable architecture
  guide for the standalone product.
  Verified: it already states the five-layer thesis.
  Inferred: `dev/guides/PORTABLE_CODE_GOVERNANCE.md` should narrow to
  repo-adoption and engine-usage guidance.
- Keep `dev/guides/ARCHITECTURE.md` as VoiceTerm product architecture, not
  governance-platform architecture.
  Verified: it is broader repo architecture.
  Inferred: mixing it with the extracted product architecture will blur the
  boundary again.
- Replace manual instruction surfaces with generated ones.
  Inspected: `AGENTS.md`, `CLAUDE.md`, `dev/templates/slash/claude/SKILL.md`.
  Verified: these are currently separate human-maintained surfaces.
  Inferred: this is the most preventable source of future drift.

### E. Recommended Architecture

Verified basis: `dev/active/ai_governance_platform.md`,
`dev/guides/AI_GOVERNANCE_PLATFORM.md`,
`dev/scripts/devctl/platform/contract_definitions.py`,
`dev/scripts/devctl/runtime/action_contracts.py`,
`dev/scripts/devctl/runtime/control_state.py`.

Recommended target:

```text
governance_core/
  policy/
  guards/
  probes/
  docs_governance/
  bootstrap/
  export/
  review_ledger/
governance_runtime/
  contracts/
  actions/
  artifact_store/
  run_history/
  collaboration/
governance_adapters/
  providers/
  workflows/
  vcs/
  hooks/
  notifications/
governance_frontends/
repo_packs/
  voiceterm/
  ci_cd_hub/
  templates/
docs/
  ARCHITECTURE.md
  ADOPTION.md
  REPO_PACKS.md
  RUNBOOKS/
```

- Canonical config design: extend the current repo-policy model, do not
  replace it with a new philosophy. Use one repo-pack config as the source of
  truth for policy, scopes, docs manifests, workflow mappings, risk add-ons,
  instruction surfaces, skill templates, and hook profiles. Start from
  `dev/config/devctl_repo_policy.json` and the preset chain under
  `dev/config/quality_presets/`; normalize it into one schema with no
  duplicate-key ambiguity.
- Generated file strategy: add one renderer command that emits `AGENTS.md`,
  `CLAUDE.md`, skill/slash templates, pre-commit fragments, and CI workflow
  stubs from repo-pack config plus templates. Reuse the current
  bundle-rendering pattern from
  `dev/scripts/checks/check_agents_bundle_render.py`, but expand it to
  whole-surface generation.
- CLI command surface: keep CLI as the product core. The minimal stable surface
  should be `check`, `probe-report`, `quality-policy`,
  `governance-bootstrap`, `governance-export`, `governance-review`,
  `platform-contracts`, `render-surfaces`, `artifacts status`,
  `artifacts gc`, and optional loops.
- Database/event schema: structured artifacts should be the system of record
  and markdown a derived view. Near term, standardize on append-only
  JSONL/NDJSON plus schemas for `TypedAction`, `RunRecord`, `Finding`,
  `FindingReview`, `ArtifactManifest`, `Packet`, and `MetricEvent`, with an
  optional SQLite index later for query speed.
- Session continuity and audit/event history must stay separate:
  - active-plan markdown (`Session Resume`, `Progress Log`) is the canonical
    "left off here" surface for AI and maintainer handoff;
  - transitional shared-markdown coordination surfaces such as the current
    review-channel bridge remain human/agent projections and bootstrap aids,
    not the long-term system of record;
  - structured ledgers (`devctl_events.jsonl`, `finding_reviews.jsonl`,
    watchdog episodes, swarm/benchmark summaries) are the machine-readable
    runtime evidence that later rolls into `RunRecord` / `ArtifactStore`,
    optional SQLite indexing, and ML/ranking inputs.
- PyQt6 UI architecture: keep PyQt6, but make it a pure client over runtime
  contracts or CLI JSON responses. No direct repo-local imports, no hard-coded
  repo-root assumptions, no private filesystem contracts.
- ML later: add ML only as an advisory layer over telemetry and governance
  review artifacts for ranking and prioritization. It must not replace
  deterministic gates.
- MCP later: keep MCP read-only and optional. If write-capable MCP exists
  later, route it through the same typed action and approval contracts as the
  CLI, not a separate control plane.
- Separation boundary: VoiceTerm becomes one repo pack plus client
  integrations. It can ship a wrapper CLI, overlay integration, and optional
  Operator Console skin, but it should consume the governance platform the
  same way any other adopter does.
- Canonical docs structure after extraction: one `ARCHITECTURE.md` for product
  design, one tracker document for active execution, one repo-pack guide, and
  generated instruction surfaces. Do not repeat architecture ownership across
  multiple active plans once extracted.

### E.5. Missing Gaps, Blind Spots, And Scope Corrections

- Missing capability: a real install/upgrade story for the governance
  platform.
  Inspected: `dev/scripts/devctl/governance_export_support.py`,
  `dev/scripts/devctl/governance_bootstrap_support.py`.
  Verified: export/bootstrap is snapshot-oriented, not package-oriented.
  Inferred: packaging is the first product gap.
- Missing boundary: a stable service/API between core/runtime and frontends.
  Inspected: `dev/scripts/devctl/platform/contract_definitions.py`,
  `app/operator_console/state/snapshots/analytics_snapshot.py`.
  Verified: contracts exist, but clients still read raw artifacts and internals.
  Inferred: this needs an explicit backend protocol.
- Missing scaling plan: multi-repo contract tests and adopter fixtures.
  Inspected: `dev/scripts/devctl/commands/governance/bootstrap.py`,
  `dev/guides/PORTABLE_CODE_GOVERNANCE.md`,
  `integrations/ci-cd-hub/pyproject.toml`.
  Verified: adoption thinking exists.
  Inferred: the product still needs a formal pilot matrix beyond VoiceTerm.
- Missing model: a unified artifact taxonomy and retention policy.
  Inspected: `dev/scripts/devctl/reports_retention.py`,
  `dev/scripts/devctl/watchdog/episode.py`,
  `dev/scripts/devctl/review_channel/event_store.py`.
  Verified: retention and artifacts exist piecemeal.
  Inferred: extraction needs one artifact-store contract.
- Missing boundary: one explicit audit/event model that tells contributors
  which data belongs in plan markdown versus structured ledgers.
  Inspected: `dev/scripts/devctl/audit_events.py`,
  `dev/scripts/devctl/governance_review_log.py`,
  `dev/audits/METRICS_SCHEMA.md`, `dev/guides/DEVELOPMENT.md`.
  Verified: command telemetry and finding adjudication are already durable
  JSONL ledgers, but the repo has not stated clearly enough that session
  continuity belongs in plan markdown while those ledgers serve runtime
  evidence, metrics, and later DB/ML ingestion.
  Inferred: extraction needs that distinction to stay explicit so a future
  database does not become a dumping ground for prose handoff.
- Missing coverage: broader full-codebase and full-cycle evidence before the
  repo can make strong accuracy claims.
  Inspected: `dev/audits/2026-02-24-autonomy-baseline-audit.md`,
  `dev/scripts/devctl/watchdog/episode.py`,
  `dev/guides/PORTABLE_CODE_GOVERNANCE.md`.
  Verified: the repo has `--adoption-scan`, guarded-coding episode logging, and
  a baseline full-surface audit runbook, but current adjudication evidence is
  still concentrated in a narrow set of probe findings and a small watchdog
  sample.
  Inferred: we need repeated full-worktree audit cycles plus richer watchdog
  coverage before "near-100% accuracy" is a defensible claim.
- Missing policy: false positives should trigger root-cause remediation, not
  just ledger accounting.
  Inspected: `dev/scripts/devctl/governance_review_log.py`,
  `dev/guides/DEVELOPMENT.md`, `AGENTS.md`.
  Verified: the repo records false-positive verdicts, but it has not yet made
  "why was this wrong and how do we narrow it?" an explicit execution
  requirement.
  Inferred: the platform should treat false positives as rule-quality defects
  until proven otherwise.
- Missing context-budget contract: the platform does not yet treat AI-context
  usage as a first-class bounded runtime resource.
  Inspected: `dev/active/ai_governance_platform.md`,
  `dev/active/portable_code_governance.md`,
  `dev/guides/AI_GOVERNANCE_PLATFORM.md`,
  `dev/config/templates/portable_governance_episode.schema.json`.
  Verified: the current plan emphasizes findings, evidence, and portability,
  but it does not yet define mode-specific context budgets, overflow behavior,
  or prompt-usage telemetry as product requirements.
  Inferred: without explicit context contracts, the platform could improve code
  quality while becoming too expensive or too large-context to use in practice.
- Missing metric: adjudication coverage, not just adjudication outcome.
  Inspected: `dev/scripts/devctl/governance_review_log.py`,
  `dev/scripts/devctl/data_science/metrics.py`,
  `dev/reports/governance/latest/review_summary.json`.
  Verified: the repo reports false-positive and cleanup rates for reviewed
  findings, but it does not yet expose how much of the guard/probe surface is
  still unreviewed by signal family, repo, or scan mode.
  Inferred: strong quality claims need "coverage of reviewed findings" metrics,
  not only "quality of reviewed findings" metrics.
- Missing DB-readiness contract: schema migration and provenance strategy for
  the eventual structured store.
  Inspected: `dev/scripts/devctl/runtime/action_contracts.py`,
  `dev/scripts/devctl/platform/contract_definitions.py`,
  `dev/scripts/devctl/watchdog/models.py`,
  `dev/config/templates/portable_governance_eval_record.schema.json`.
  Verified: the repo already uses `schema_version`, `run_id`,
  `controller_run_id`, `session_id`, `repo_pack_id`, and retention metadata in
  several places, but the future database plan does not yet say which fields
  are canonical, how migrations are handled, or how JSONL backfill maps into
  DB tables.
  Inferred: the platform needs a formal ingestion/provenance contract before a
  database layer lands.
- Missing privacy/redaction rule for the future event store and ML corpus.
  Inspected: `dev/guides/ARCHITECTURE.md`,
  `dev/scripts/devctl/audit_events.py`,
  `dev/scripts/devctl/watchdog/episode.py`.
  Verified: the repo already stores command args, paths, provider/session IDs,
  and other provenance-bearing fields in structured artifacts.
  Inferred: we need explicit redaction/privacy policy before scaling that data
  into a richer DB or ML-ranking corpus.
- Missing promotion criteria for hard guards versus advisory probes.
  Inspected: `AGENTS.md`, `dev/scripts/devctl/quality_policy_defaults.py`,
  `dev/scripts/devctl/governance_review_log.py`.
  Verified: the repo distinguishes blocking guards from advisory probes, but it
  does not yet define a measured graduation rule tied to false-positive rate,
  cleanup rate, sample size, and adoption-scan stability.
  Inferred: the platform needs one explicit promotion/demotion rubric so noisy
  heuristics do not silently harden into blockers.
- Missing evaluation corpus and replay harness for rule-quality regression.
  Inspected: `dev/config/templates/portable_governance_eval_record.schema.json`,
  `dev/guides/PORTABLE_CODE_GOVERNANCE.md`,
  `dev/scripts/devctl/data_science/metrics.py`,
  `dev/reports/autonomy/benchmarks/`.
  Verified: the repo already has evaluation-record schema support, benchmark
  artifacts, and telemetry rollups, but it does not yet define one curated
  cross-repo corpus or replay flow that can compare rule/policy versions
  against the same labeled evidence set.
  Inferred: before stronger accuracy claims, DB expansion, or ML-assisted
  ranking, the platform needs a repeatable regression harness that measures
  guard/probe quality across stable inputs instead of only live current-repo
  scans.
- Missing waiver/suppression lifecycle for noisy-but-known signals.
  Inspected: `AGENTS.md`,
  `dev/scripts/devctl/governance_review_log.py`,
  `dev/scripts/devctl/quality_policy_defaults.py`,
  `dev/scripts/devctl/rust_audit/catalog.py`,
  `dev/scripts/devctl/script_catalog.py`.
  Verified: the repo already has waiver/approval concepts, suppression-debt
  guards, and adjudicated review logging, but the standalone platform plan does
  not yet define one lifecycle for waivers/allowlists/suppressions with owner,
  reason, expiry, and reevaluation triggers.
  Inferred: if false positives are handled ad hoc, the system will accumulate
  silent exceptions and lose the very determinism/credibility it is trying to
  preserve.
- Missing completion gate: the repo does not yet state sharply enough that the
  product is unfinished until architecture, pipeline, and evidence quality are
  all proven together.
  Inspected: `dev/active/MASTER_PLAN.md`,
  `dev/guides/AI_GOVERNANCE_PLATFORM.md`,
  `.github/workflows/tooling_control_plane.yml`,
  `dev/scripts/devctl/bundle_registry.py`.
  Verified: the roadmap and checks exist, but the plan previously left too much
  room for "split the repo and call it done" thinking.
  Inferred: the platform needs explicit completion gates so extraction,
  pipeline parity, reviewed evidence, and telemetry trust all count as closure
  criteria.
- Missing pattern-mining program: broader Python/Rust discovery is implied, but
  not yet stated as a standing execution loop in the product plan.
  Inspected: `dev/active/portable_code_governance.md`,
  `dev/guides/PORTABLE_CODE_GOVERNANCE.md`,
  `dev/reports/governance/latest/`,
  `dev/scripts/devctl/data_science/metrics.py`.
  Verified: the repo has evidence surfaces, evaluation schema, and pilot-corpus
  intent, but the broader product plan does not yet say "keep mining repeated
  low-noise patterns from this repo and external repos, especially in Python
  and Rust, until the rule families are much stronger."
  Inferred: the differentiation from generic AI review tools depends on a
  repeatable mining -> probe -> adjudication -> promotion loop, not a one-time
  initial guard set.
- Missing language-extension contract: the plan says the product should expand
  beyond Python/Rust later, but it does not yet define how new language support
  fits the same architecture.
  Inspected: `dev/config/quality_presets/portable_python.json`,
  `dev/config/quality_presets/portable_rust.json`,
  `dev/config/quality_presets/portable_python_rust.json`,
  `dev/scripts/devctl/quality_policy_defaults.py`,
  `dev/scripts/devctl/platform/contract_definitions.py`.
  Verified: the current policy/preset stack already implies a language-aware
  model for Python/Rust.
  Inferred: before new languages arrive, the platform should formalize a
  language-pack/analyzer-module contract so future Swift/TypeScript/etc. reuse
  the same finding schemas, policy resolution, review ledger, and telemetry
  model instead of spawning ad hoc subsystems.
- Assumption to validate: whether JSONL plus optional SQLite is enough for the
  first standalone version.
  Inspected: `dev/scripts/devctl/audit_events.py`,
  `integrations/code-link-ide/docs/spec/audit-log.md`.
  Verified: the repo already succeeds with structured flat-file ledgers.
  Inferred: do not force a DB before query pain justifies it.
- Prototype before full build-out: run the extracted package against VoiceTerm
  and one non-VoiceTerm adopter such as `ci-cd-hub`, using the same repo-pack
  renderer and check surface. That is the shortest way to validate the
  boundary.

### F. Prioritized Implementation Roadmap

- `Phase 1 - Consolidate authority and architecture docs`
  Goal: create one coherent architecture path before more code moves.
  Why it matters: the main failure mode now is plan drift, not missing intent.
  Files/modules: `dev/active/ai_governance_platform.md`,
  `dev/active/portable_code_governance.md`,
  `dev/guides/AI_GOVERNANCE_PLATFORM.md`,
  `dev/guides/PORTABLE_CODE_GOVERNANCE.md`,
  `dev/active/INDEX.md`, `dev/active/MASTER_PLAN.md`.
  Deliverables: one active architecture plan, one durable architecture guide,
  updated index/router language.
  Acceptance criteria: `check_active_plan_sync`,
  `docs-check --strict-tooling`, and
  `check_architecture_surface_sync` pass, and no second peer architecture doc
  remains active.
- `Phase 2 - Normalize repo-pack policy and surface generation`
  Goal: make one canonical config the source for policy plus generated
  instruction surfaces.
  Files/modules: `dev/config/devctl_repo_policy.json`,
  `dev/scripts/devctl/quality_policy.py`,
  `dev/scripts/devctl/quality_policy_defaults.py`,
  `dev/scripts/checks/check_agents_bundle_render.py`,
  `AGENTS.md`, `CLAUDE.md`, `dev/templates/slash/`.
  Deliverables: `render-surfaces` command, generation checks, and repo-pack
  context-budget profiles with usage-tier documentation hooks.
  Acceptance criteria: `AGENTS.md`, `CLAUDE.md`, slash/skill templates, and
  hook/config stubs regenerate cleanly from policy, and repo-pack config can
  declare bounded context modes without patching orchestration code.
- `Phase 3 - Harden the portable core inside the current repo`
  Goal: reduce shim debt and make platform/runtime packages the real internal
  boundary.
  Files/modules: `dev/scripts/devctl/platform/`,
  `dev/scripts/devctl/runtime/`, `dev/scripts/devctl/repo_policy.py`,
  `dev/scripts/devctl/governance/bootstrap_policy.py`,
  `dev/scripts/devctl/data_science/metrics.py`,
  `dev/scripts/checks/check_package_layout.py`,
  `dev/scripts/checks/probe_compatibility_shims.py`.
  Deliverables: lower shim count, lower crowded-root counts, cleaner package
  boundaries, and the first context-usage telemetry path wired into runtime
  evidence.
  Acceptance criteria: shim probe falls materially, package-layout pressure
  drops, and governed runs emit bounded context telemetry rather than hiding
  prompt size inside provider-specific logs.
- `Phase 4 - Extract the standalone repository and package`
  Goal: create the standalone governance product without breaking VoiceTerm.
  Files/modules: portable slices of `dev/scripts/devctl/`,
  `dev/scripts/checks/`, `dev/config/quality_presets/`,
  `dev/config/templates/`.
  Deliverables: installable standalone repo, versioned CLI, VoiceTerm repo pack.
  Acceptance criteria: VoiceTerm can run the extracted CLI locally and at
  least one second repo can adopt it through bootstrap.
- `Phase 5 - Rebind frontends and loops to the extracted runtime`
  Goal: make UI, MCP, and loops clients of the new platform rather than
  private in-repo consumers.
  Files/modules: `app/operator_console/`,
  `dev/scripts/devctl/commands/mcp.py`,
  `dev/scripts/devctl/commands/triage_loop.py`,
  `dev/scripts/devctl/commands/mutation_loop.py`,
  `dev/scripts/devctl/commands/autonomy_loop.py`.
  Deliverables: reusable PyQt client, stable runtime API, adapter-based loops.
  Acceptance criteria: Operator Console can point at the extracted runtime and
  VoiceTerm behaves as one consumer, not the host.

### F.5. Standalone-Repo Migration Roadmap

- Extract first: policy resolution, guard/probe registry, checks, docs
  governance, bootstrap/export/review, runtime contracts, and artifact-store
  code from `dev/scripts/devctl/` and `dev/scripts/checks/`. Temporary bridge:
  keep `dev/scripts/devctl.py` as a wrapper that calls the installed
  standalone package.
- Keep temporarily bridged: VoiceTerm-specific repo pack config, release
  workflows, Operator Console skin, and Rust overlay/mobile integration under
  `dev/config/`, `.github/workflows/`, `app/operator_console/`, and
  `pypi/src/voiceterm/cli.py`.
- Replace direct coupling with interfaces: CLI entrypoints, repo-pack configs,
  typed JSON contracts, generated instruction surfaces, and optionally a
  Python package API. Avoid future imports from
  `VoiceTerm -> dev.scripts.devctl.*` once extraction starts.
- VoiceTerm after extraction should consume the system by installing the
  governance package, shipping a `voiceterm` repo pack, invoking checks and
  exports via CLI/API, and using generated instruction surfaces. VoiceTerm
  should stop being the permanent filesystem host for platform code.
- Prevent drift after separation with contract tests and version pinning.
  VoiceTerm should pin a platform version and repo-pack version, and CI should
  validate `platform-contracts`, `quality-policy`, and `render-surfaces`
  compatibility on every update.

### F.6. Documentation Consolidation Roadmap

- Merge or subordinate `dev/active/portable_code_governance.md` beneath this
  plan. One active full-product architecture plan only.
- Merge durable architecture content into
  `dev/guides/AI_GOVERNANCE_PLATFORM.md`; retain
  `dev/guides/PORTABLE_CODE_GOVERNANCE.md` only as an adoption/how-to guide if
  it becomes materially shorter and non-overlapping.
- Retain `dev/active/MASTER_PLAN.md` as tracker authority and
  `dev/active/INDEX.md` as router authority. Do not keep architectural state
  split across execution specs once consolidated.
- Generate instruction and workflow docs from repo-pack config:
  `AGENTS.md`, `CLAUDE.md`, slash/skill templates, and hook/workflow stubs.
- Add drift checks for every generated surface. The current AGENTS bundle check
  is the pattern; expand it so plan drift and instruction drift fail fast.

### G. File-By-File Or Module-By-Module Action Plan

- `dev/active/ai_governance_platform.md`: promote to the single active
  architecture plan for the standalone product.
- `dev/active/portable_code_governance.md`: shrink to an engine/adoption
  appendix or companion after consolidation.
- `dev/guides/AI_GOVERNANCE_PLATFORM.md`: keep as the canonical durable
  architecture document.
- `dev/guides/PORTABLE_CODE_GOVERNANCE.md`: narrow to adopter workflow and
  repo-pack onboarding.
- `dev/config/devctl_repo_policy.json`: remove duplicate keys and extend schema
  for instruction surfaces, hook profiles, workflow templates, and repo-pack
  metadata.
- `dev/config/quality_presets/`: keep as portable defaults with clean
  separation between engine defaults and repo-pack overrides.
- `dev/scripts/devctl/quality_policy.py` and
  `dev/scripts/devctl/quality_policy_defaults.py`: become the formal repo-pack
  resolver stack in the extracted package.
- `dev/scripts/checks/check_agents_bundle_render.py` and
  `dev/scripts/checks/check_agents_contract.py`: generalize into
  surface-render and surface-contract checks for all generated instruction
  files.
- `AGENTS.md`, `CLAUDE.md`, `dev/templates/slash/`: move to generated outputs
  from repo-pack config plus templates.
- `dev/scripts/devctl/platform/` and `dev/scripts/devctl/runtime/`: become the
  internal package roots other modules must depend on, not just blueprint docs.
- `dev/scripts/devctl/audit_events.py`,
  `dev/scripts/devctl/governance_review_log.py`,
  `dev/scripts/devctl/review_probe_report.py`,
  `dev/scripts/devctl/watchdog/episode.py`: unify under one
  artifact-store/run-history contract.
- `dev/scripts/devctl/governance_export_support.py` and
  `dev/scripts/devctl/governance_bootstrap_support.py`: shift from
  snapshot-copy semantics toward package install/render semantics.
- `app/operator_console/state/snapshots/analytics_snapshot.py` and
  `app/operator_console/state/snapshots/quality_snapshot.py`: remove hard-coded
  VoiceTerm repo restrictions and consume stable runtime/artifact APIs.
- `.github/workflows/` and `.pre-commit-config.yaml`: move toward generated or
  templated hook/workflow surfaces from repo-pack policy.
- `pypi/src/voiceterm/cli.py`: keep VoiceTerm packaging focused on VoiceTerm;
  do not use the PyPI launcher as the governance package boundary.

### H. Risks And Tradeoffs

- Extracting while the worktree is dirty risks stabilizing the wrong seams; the
  countermeasure is to consolidate docs first, not to delay extraction
  indefinitely.
- Keeping too many compatibility shims will slow extraction; removing them too
  fast will break callers. The repo already has the right shim-metadata
  discipline, so use staged shrinkage.
- Standardizing on JSONL plus projections first is the pragmatic move, even if
  users keep asking for a heavier database.
- Generalizing too much too early could erase VoiceTerm-specific quality. The
  fix is the repo-pack model, not more in-engine special cases.
- Pulling the PyQt client out too early could create a second backend. The fix
  is a strict runtime-contract boundary and CLI/API-only data access.
- Loop extraction is trickier than core-rule extraction because workflows,
  branches, notifications, and provider CLIs remain environment-sensitive.

### I. What Not To Build Yet

- Do not make MCP the primary control plane.
- Do not build a mandatory database-backed runtime before the artifact-store
  contract is unified.
- Do not widen the PyQt6 UI into a second orchestration backend before
  extraction and API stabilization.
- Do not prioritize optional Ruff/Semgrep/Black/Clippy wrapper work ahead of
  freezing the core contracts, repo-pack boundary, replay/evaluation path, and
  package/install surface.
- Do not pull the Memory Studio scope into the first standalone governance
  release.
- Do not attempt broad multi-repo packaging of every workflow loop before
  repo-pack rendering and contract tests exist.

### J. Final Recommendation

- The repo-grounded recommendation is to formalize the direction that already
  exists: a standalone deterministic governance product centered on CLI
  authority, repo-pack policy, deterministic guards/probes, typed runtime
  contracts, structured artifacts, and thin adapters.
- The immediate move is:
  1. consolidate architecture authority into this plan,
  2. normalize canonical policy/config generation,
  3. harden internal runtime/platform boundaries in-place,
  4. package the portable core once the contract freeze and boundary proof are
     real,
  5. rebind VoiceTerm, PyQt6, MCP, and loop surfaces as consumers of that
     product, then split repos only after external-pilot proof.
- VoiceTerm should survive as the first adopter and integration target, but it
  should stop being the permanent host architecture for the governance system.

## Priority Ladder

Do not treat every open checklist item as the same priority.

Use this execution ladder:

### `P0` Must-Have Spine

These are the no-skip contracts that keep the whole product coherent:

1. shared runtime authority and typed contracts
2. system coherence matrix and drift-guard strategy
3. canonical identity contract
4. unified agent/job/session/task registry
5. typed tool/action/skill registry plus capability discovery
6. stable backend protocol/API boundary
7. local service lifecycle plus daemon/controller split
8. write arbitration and multi-client mutation model
9. caller authority and approval matrix
10. action-result/error plus degraded-mode contract
11. public deprecation/compatibility contract
12. `map` snapshot/focus/targeted-check contract plus cache/storage contract
13. evidence-to-memory bridge and artifact attach-by-ref flow
14. contract-sync, parity fixtures, validation-routing, and artifact taxonomy

If `P0` is not frozen, the system may still look rich while remaining too easy
to drift.

### `P1` Product-Complete Requirements

These make the platform feel like a full agent app instead of a strong backend:

1. packaging/install/update/adoption flow
2. product-operability layer: health, timeline, replay, recovery, checkpoints
3. generated startup surfaces and repo-pack-configurable wrappers
4. full client parity across CLI, VoiceTerm, PyQt6, phone/mobile, hooks/skills
5. execution-mode parity and collaboration-mode parity
6. bootstrap/adoption flow for arbitrary repos
7. context-budget usage tiers and cost-visible operation
8. broad replay/evaluation proof and cross-repo evidence density
9. extension/adopter conformance packs for providers, hooks, wrappers, and
   supported clients
10. architectural knowledge base: topic-keyed chapters, auto-capture scripts,
    ConceptIndex/ZGraph integration, and context-pack export for
    graph-traversal-based AI retrieval (depends on P0 SQLite activation and
    evidence-to-memory bridge)

### `P2` Enrichments

These are valuable, but they should not outrun `P0` or `P1`:

1. richer wrappers, slash commands, hooks, and shell polish
2. broader language packs and optional analyzer integrations
3. deeper memory/retrieval intelligence beyond the P1 knowledge base
   (semantic rerank, graph boosts, learned retrieval policies)
4. richer desktop/mobile UX and additional shell affordances
5. extra analytics, charts, and operator comfort features

Rule:

- do not pull `P2` work forward if it bypasses or weakens a `P0` contract
- use `P1` to decide "full app" readiness
- use `P2` to improve reach and experience after the spine is stable

### `P3` Far-Future — Advanced AI Coding Patterns

These are ambitious research-grade capabilities that go beyond the current
review-loop and guard-pipeline paradigm. None should be attempted until `P0`
and `P1` are stable and the platform is installable in external repos.

1. **Speculative branching** — agent tries N approaches in parallel worktrees,
   runs tests and guards on each, and picks the best candidate based on guard
   scores and test results instead of committing to one path serially
2. **Semantic diffing** — instead of text-level review, agents reason about
   behavioral equivalence: does this refactor preserve the same observable
   behavior? Uses symbolic analysis, property-based testing, or trace
   comparison instead of line-by-line reading
3. **Continuous synthesis** — instead of writing whole functions in one shot,
   agents maintain a running synthesis loop that refines partial solutions as
   new information arrives (closer to how a human iterates mentally before
   typing), with incremental guard feedback at each refinement step
4. **Graph-based planning** — instead of linear "do step 1, then step 2,"
   build a dependency graph of changes, execute independent leaves in parallel,
   and merge results; the daemon-event reducer and worktree isolation already
   lay groundwork for this
5. **Learning from execution** — agent runs the code, observes actual runtime
   behavior (traces, profiles, coverage deltas, memory snapshots), and uses
   that as primary feedback for the next edit, not just static review or guard
   output

Rule:

- do not pull `P3` work forward while `P0`/`P1`/`P2` are open
- each item requires a proof-of-concept with measurable improvement over the
  current loop before full investment
- these items may depend on model capabilities that do not exist yet; revisit
  when the underlying models support the required reasoning depth
- the current event log, daemon reducer, worktree isolation, and guard pipeline
  are architectural prerequisites that `P0`/`P1` work is already building

### Audit Intake Sequencing (2026-03-16)

The latest architecture re-audit added useful scope, but it must land under
the ladder above instead of as a flat "do everything" backlog.

Current execution tranche (`P0`, do now):

1. freeze the missing contract spine added by the re-audit:
   `ActionResult`, `CommandGoalTaxonomy`,
   `RepoMapSnapshot` / `MapFocusQuery` / `TargetedCheckPlan`
2. freeze the control-plane safety seam:
   service identity/discovery, backend attach/auth, write arbitration,
   caller authority, and degraded-mode semantics
3. freeze the evidence/compatibility seam:
   migrate evidence onto `Finding`, add schema-version coverage, define the
   artifact taxonomy, and make deprecation/compatibility plus contract-sync
   behavior executable

Next tranche (`P1`, only after the current `P0` slice is green):

1. packaging/install/update/adoption flow
2. generated startup surfaces and repo-pack wrapper polish
3. broader client/mode parity and replay/recovery operability
4. context-budget usage tiers plus cross-repo evaluation density

Later tranche (`P2`, do not pull forward while `P0`/`P1` are open):

1. public whitepaper/proof packaging
2. broader rule-quality mining loops and portable primitive ranking
3. language expansion and optional analyzer/search integrations
4. extra shell/mobile/operator comfort features

Practical rule for implementation:

- if a new audit item does not directly freeze a `P0` contract, it should not
  displace the current tranche
- if a `P1` or `P2` item depends on unfinished `P0` contract work, leave it
  in backlog/progress notes instead of promoting it into the active slice

### P0 Clarity Note

Keep the landed slices separate from the still-open closure work so the plan
does not imply that a first self-hosting implementation equals a frozen
platform contract.

Landed now:

- `probe-report` can emit typed design-decision packets from
  `.probe-allowlist.json` entries, and those packets now reach the canonical
  `devctl probe-report` markdown/terminal surfaces.
- `platform-contracts` now carries bounded runtime-model plus durable
  artifact-schema metadata for the already-real `P0` families, and
  `check_platform_contract_closure.py` enforces closure between those rows,
  the corresponding runtime dataclasses / schema constants, and the
  startup-surface command tokens that tell AI/dev operators how to inspect the
  same contract surface.
- Review-channel lifecycle truth now has an explicit typed owner:
  `ReviewState.reviewer_runtime` projects the dedicated
  `ReviewerRuntimeContract` row/model, while bridge `review_accepted` and
  doctor surfaces remain compatibility projections. The same current
  platform-contract inventory now carries `startup_surface_tokens` on every
  implemented row so startup/bootstrap surfaces expose the same contract set
  the closure guard validates.

Still open before `P0` closes:

- all review/fix/decision packets must become projections over the canonical
  `Finding` record instead of being assembled directly from raw `risk_hints`
  plus allowlist rows
- hard guards still emit family-local violation dicts instead of the same
  canonical `Finding` record used by the current probe/report path, so the
  evidence ontology is not yet unified across blocking and advisory layers.
  `governance-review` already accepts `guard` / `probe` / `audit` verdicts,
  but the blocking guard path still lacks the canonical translation seam and
  stable finding-identity flow that probes now use.
- the platform still needs one typed `FixPacket` contract, one typed
  `DecisionPacket` contract, stable finding identity/routing, and a clear
  closure loop into `governance-review`
- packet/artifact families still need full schema/version matrix coverage plus
  executable enforcement beyond the first bounded guard scope that now covers
  the current implemented probe/review families
- `platform-contracts` is still a partial blueprint, not yet the authoritative
  catalog for every `P0` contract named in this plan
- `RepoMapSnapshot` / `MapFocusQuery` / `TargetedCheckPlan` and the
  command-goal/validation-routing seam are still open, so AI/dev startup
  surfaces cannot derive their full workflow from one structured action model
- packaging/install-surface work, `MASTER_PLAN` compaction, and broader
  PyQt6/operator-console seam cleanup are accepted follow-ups, but they remain
  `P1` work unless a specific `P0` contract closure step blocks on them

## Proof Gates

Do not describe the platform as "ready" by elapsed time or by packaging work
alone. Use these proof gates:

1. `Gate 1: Self-hosting honest`
   The repo can run the governed stack on itself without hidden VoiceTerm
   defaults, shadow authority, or bridge-only truth claims.
2. `Gate 2: POC ready`
   A second repo can bootstrap, run `startup-context`, emit at least one
   governed finding/evidence path, and stay green on the same core without
   core-engine patches between adoptions.
3. `Gate 3: Early release ready`
   Install/update/bootstrap flow, reviewed setup guidance, lightweight
   adoption docs, and portable proof artifacts are good enough to ship a
   narrow public POC.
4. `Gate 4: Productizing`
   Packaging polish, broader adapters/frontends, release-artifact governance,
   replay/recovery/observability, and support expectations are strong enough
   for sustained external use rather than one proof demo.

## Execution Checklist

### Phase P0 - Findings Spine, Dogfood, And Plan Authority

Phase metadata: phase_id=MP377-P0; owner_doc=`dev/active/ai_governance_platform.md`; status=in_progress; depends_on=none; summary=Collapse execution authority to one umbrella plan plus a small owner-doc set, then land the missing findings and dogfood closeout spine.

- [x] `MP377-P0-T01` Implement one canonical `FindingBacklog` reader/writer and route finding intake plus compatibility import through it.
      owner_doc: `dev/active/platform_authority_loop.md`
      status: `done`
      depends_on: none
- [x] `MP377-P0-T02` Reduce the active execution-doc registry to the umbrella plan plus the small owner-doc set in `INDEX.md`.
      owner_doc: `dev/active/ai_governance_platform.md`
      status: `done`
      depends_on: `MP377-P0-T01`
- [x] `MP377-P0-T03` Wire `check_active_plan_sync` into the default AI guard policy and make it enforce the typed umbrella-plan contract.
      owner_doc: `dev/active/ai_governance_platform.md`
      status: `done`
      depends_on: `MP377-P0-T02`
- [x] `MP377-P0-T04` Land one repo-owned `devctl dogfood` ledger/report over live commands, guards, probes, and roles, and extend `governance-review` to accept `signal_type=dogfood`.
      owner_doc: `dev/active/ai_governance_platform.md`
      status: `done`
      depends_on: `MP377-P0-T03`
- [x] `MP377-P0-T05` Refresh the active compatibility bridge from typed review status before governed push/pre-commit blocking checks run so stale role markers cannot strand publication.
      owner_doc: `dev/active/review_channel.md`
      status: `done`
      depends_on: `MP377-P0-T03`
- [x] `MP377-P0-T06` Auto-record dogfood-discovered failures into `governance-review` with stable finding ids instead of relying on manual ledger correlation.
      owner_doc: `dev/active/ai_governance_platform.md`
      status: `done`
      depends_on: `MP377-P0-T01`, `MP377-P0-T04`

### Phase P1 - Typed Plan Ingestion And Registry Projection

Phase metadata: phase_id=MP377-P1; owner_doc=`dev/active/ai_governance_platform.md`; status=blocked; depends_on=`MP377-P0`; summary=Finish the remaining typed plan projection and review/runtime convergence work after the `MP-388..MP-410` consolidation lane lands.

- [x] `MP377-P1-T01` Land typed `PlanPhase`, `PlanTask`, and `PlanDependency` models plus a parser for structured execution-checklist phase/task metadata.
      owner_doc: `dev/active/ai_governance_platform.md`
      status: `done`
      depends_on: `MP377-P0-T02`
- [x] `MP377-P1-T02` Enforce unique task ids, required owner docs, and valid dependencies on the umbrella plan.
      owner_doc: `dev/active/ai_governance_platform.md`
      status: `done`
      depends_on: `MP377-P1-T01`
- [x] `MP377-P1-T03` Add phase-aware routing to `WorkIntakePacket` and surface the active phase/task in startup receipts.
      owner_doc: `dev/active/platform_authority_loop.md`
      status: `done`
      depends_on: `MP377-P1-T01`
- [x] `MP377-P1-T04` Persist a repo-pack-owned `PlanRegistry` / `PlanTargetRef` authority artifact so startup and planning consumers stop reparsing mutable markdown on every read.
      owner_doc: `dev/active/platform_authority_loop.md`
      status: `done`
      depends_on: `MP377-P1-T03`
- [ ] `MP377-P1-T05` Render `INDEX.md`, `MASTER_PLAN.md`, and owner-plan markdown as bounded projections over the semantic `PlanRegistry` closure instead of treating raw markdown as mutable execution authority.
      owner_doc: `dev/active/ai_governance_platform.md`
      status: `blocked`
      depends_on: `MP377-P1-T04`, `MP391-P0`
- [ ] `MP377-P1-T06` Collapse reviewer/runtime authority onto one canonical producer tick: `refresh_status_snapshot`, `load_current_review_state`, `review_state_parser`, `commit_pipeline` artifact writes, `AuthoritySnapshot`, and `CoordinationSnapshot` must share one snapshot/generation identity and one reducer-owned field route for liveness, pending packets, current slice, commit approval, and push readiness. `packet_inbox` must become the sole continue-vs-wait authority for reviewer/implementer coordination so startup/session/status cannot drift back to chat-local `Claude Ack` or bridge prose when packet truth is degraded.
      owner_doc: `dev/active/remote_control_runtime.md`
      status: `blocked`
      depends_on: `MP377-P1-T03`, `MP393-P0`
- [ ] `MP377-P1-T07` Make governed mutation self-healing against stale projections: commit/push/phone/operator actions must refresh and consume the canonical review-state + commit-pipeline artifacts before consistency checks, treat compatibility-surface drift as a reducer bug to fix rather than a reason to require manual `review-channel --action status`, and keep raw `git` mutation outside the remote-control path.
      owner_doc: `dev/active/remote_commit_pipeline.md`
      status: `blocked`
      depends_on: `MP377-P1-T06`, `MP394-P0`
- [ ] `MP377-P1-T08` Emit one typed liveness/wake/death signal family for reviewer, implementer, publisher, and observer consumers so dashboard/mobile/startup/status can distinguish `alive`, `degraded`, `detached_runtime_only`, and `dead` from one producer instead of mixing heartbeat prose, PID guesses, and bridge hints. Compatibility projections like `Claude Ack` and bridge heartbeat sections may mirror that state, but they must not remain independent wake/repair gates once typed runtime evidence exists.
      owner_doc: `dev/active/remote_control_runtime.md`
      status: `blocked`
      depends_on: `MP377-P1-T06`, `MP397-P0`
- [x] `MP377-P1-T09` Land slice-one worktree-orphan typed contracts and platform registration for orphan snapshots, checkout inventory, publication ledgers, session leases, baselines, reconciliation decisions, and accept-all receipts.
      owner_doc: `dev/active/ai_governance_platform.md`
      status: `done`
      depends_on: `MP377-P1-T04`

### Phase MP-399 - Governed Commit Staged-Index Preservation

Phase metadata: phase_id=MP399-P0; owner_doc=`dev/active/remote_commit_pipeline.md`; status=in_progress; depends_on=`MP377-P0`; summary=Make `devctl commit` preserve user-staged content through the managed ReviewSnapshot refresh and report the governed content commit separately from any trailing receipt commit.

- [ ] `MP399-T01` Fail closed when the managed ReviewSnapshot refresh drops preexisting user-staged paths from the index instead of silently replacing the staged set with repo-owned artifacts.
      owner_doc: `dev/active/remote_commit_pipeline.md`
      status: `in_progress`
      depends_on: `MP377-P0-T05`
- [ ] `MP399-T02` Keep governed commit reporting truthful when a trailing ReviewSnapshot receipt commit advances `HEAD`: surface the staged/content commit distinctly from the snapshot-only receipt so operators do not infer staged work was lost.
      owner_doc: `dev/active/remote_commit_pipeline.md`
      status: `in_progress`
      depends_on: `MP399-T01`
- [ ] `MP399-T03` Add regression coverage proving user-staged content survives governed staging/commit execution and that receipt-aware commit reporting stays explicit.
      owner_doc: `dev/active/remote_commit_pipeline.md`
      status: `in_progress`
      depends_on: `MP399-T02`

### Phase MP-410 - Devctl Root Package Layout Relief

Phase metadata: phase_id=MP410-P0; owner_doc=`dev/active/ai_governance_platform.md`; status=in_progress; depends_on=`MP399-P0`; summary=Relocate dev/scripts/devctl/ root files into topical subpackages to satisfy package-layout-guard and unblock multi-file slices.

- [ ] `MP410-T01` Move probe-topology and probe-report support modules out of the crowded `dev/scripts/devctl/` root and into their owning packages, then update topology/report callers to the new module paths.
      owner_doc: `dev/active/ai_governance_platform.md`
      status: `in_progress`
      depends_on: `MP399-P0`
- [ ] `MP410-T02` Create topical `governance_review/` and `governance_export/` packages and relocate the review/export helpers out of the root without widening the command surface.
      owner_doc: `dev/active/ai_governance_platform.md`
      status: `in_progress`
      depends_on: `MP410-T01`
- [ ] `MP410-T03` Move the phone/mobile app and status helpers into one `mobile/` package so the frontend-owned support surface no longer crowds the root namespace.
      owner_doc: `dev/active/ai_governance_platform.md`
      status: `in_progress`
      depends_on: `MP410-T02`
- [ ] `MP410-T04` Retire the now-redundant root compatibility shims and rerun package-layout/import validation until `dev/scripts/devctl/` drops below the strict root file cap.
      owner_doc: `dev/active/ai_governance_platform.md`
      status: `in_progress`
      depends_on: `MP410-T03`

### Phase MP-398 - Push Preflight Staged-Index Exclusion

Phase metadata: phase_id=MP398-P0; owner_doc=`dev/active/remote_commit_pipeline.md`; status=in_progress; depends_on=`MP399-P0`; summary=Allow `devctl push --execute` to publish the current governed commit even when the index already holds staged-only content for the next commit.

- [ ] `MP398-T01` Narrow push dirty-tree blocking to unstaged edits plus untracked paths so staged-only next-commit content no longer trips `Working tree has uncommitted changes`.
      owner_doc: `dev/active/remote_commit_pipeline.md`
      status: `in_progress`
      depends_on: `MP399-P0`
- [ ] `MP398-T02` Apply the same staged-index exclusion to preflight-generated auto-commit logic so the push lane cannot sweep staged next-commit intent into a machine commit.
      owner_doc: `dev/active/remote_commit_pipeline.md`
      status: `in_progress`
      depends_on: `MP398-T01`
- [ ] `MP398-T03` Add regression coverage proving push preflight ignores staged-only content while still blocking unstaged or untracked dirt.
      owner_doc: `dev/active/remote_commit_pipeline.md`
      status: `in_progress`
      depends_on: `MP398-T02`

### Phase MP-388 - Archive The Remaining Reference-Only Active Docs

Phase metadata: phase_id=MP388-P0; owner_doc=`dev/active/ai_governance_platform.md`; status=pending; depends_on=`MP398-P0`; summary=Archive the last four reference-only active-doc remnants so the live set matches one umbrella plan plus the small owner-doc set.

- [ ] `MP388-T01` Move `move.md`, `loop_chat_bridge.md`, `phase2.md`, and `RUST_AUDIT_FINDINGS.md` out of `dev/active/` without leaving duplicate active authority or broken reference links.
      owner_doc: `dev/active/ai_governance_platform.md`
      status: `pending`
      depends_on: `MP398-P0`
- [ ] `MP388-T02` Update `INDEX.md`, discovery docs, and archive/deferred pointers so startup/context-graph stop surfacing the archived files as live planning context and the active-doc count drops from 30 to 26.
      owner_doc: `dev/active/ai_governance_platform.md`
      status: `pending`
      depends_on: `MP388-T01`

### Phase MP-389 - Semantic Plan Loader Core

Phase metadata: phase_id=MP389-P0; owner_doc=`dev/active/platform_authority_loop.md`; status=pending; depends_on=`MP388-P0`; summary=Promote plan docs from registration-only records to semantic inputs by extracting scope paths, checklist state, and typed phase/task routing into `PlanRegistry`.

- [ ] `MP389-T01` Extract bounded scope-path hints from each governed `## Scope` section and persist them as typed plan-content fields instead of prose-only descriptions.
      owner_doc: `dev/active/platform_authority_loop.md`
      status: `pending`
      depends_on: `MP388-P0`
- [ ] `MP389-T02` Persist checklist completion state plus typed phase/task summaries from governed plan docs so `PlanRegistry` can answer open-vs-done status without reparsing markdown on every read.
      owner_doc: `dev/active/ai_governance_platform.md`
      status: `pending`
      depends_on: `MP389-T01`
- [ ] `MP389-T03` Feed the semantic phase/task extraction into `plan_routing` and `PlanningIRSnapshot` so startup/work-intake can route from live plan state instead of tracker prose.
      owner_doc: `dev/active/platform_authority_loop.md`
      status: `pending`
      depends_on: `MP389-T02`

### Phase MP-390 - Plan Mutation And Anchor Authority

Phase metadata: phase_id=MP390-P0; owner_doc=`dev/active/ai_governance_platform.md`; status=pending; depends_on=`MP389-P0`; summary=Make plan anchors and accepted plan-patch mutations typed runtime authority instead of manual markdown conventions.

- [ ] `MP390-T01` Auto-populate stable anchor refs for scope, checklist, session-resume, progress, and audit sections so `PlanTargetRef` no longer depends on free-form manual slugs.
      owner_doc: `dev/active/ai_governance_platform.md`
      status: `pending`
      depends_on: `MP389-P0`
- [ ] `MP390-T02` Apply accepted `plan_patch_review` `mutation_op` packets back to markdown with expected-revision checks instead of leaving the packet contract write-only.
      owner_doc: `dev/active/ai_governance_platform.md`
      status: `pending`
      depends_on: `MP390-T01`
- [ ] `MP390-T03` Emit a typed `PlanMutationReceipt` for each applied change so startup/review/status can prove when plan state changed because of accepted packet authority.
      owner_doc: `dev/active/ai_governance_platform.md`
      status: `pending`
      depends_on: `MP390-T02`

### Phase MP-391 - Plan-Target Cutover And Tracker Demotion

Phase metadata: phase_id=MP391-P0; owner_doc=`dev/active/platform_authority_loop.md`; status=pending; depends_on=`MP390-P0`; summary=Make `PlanTargetRef` and semantic plan state the primary routing source, then demote `MASTER_PLAN.md` from live task authority to bounded tracker/reference projection.

- [ ] `MP391-T01` Make `WorkIntakePacket.plan_target_path` plus the selected `PlanTargetRef` the primary scope source for startup/session routing instead of stale continuity or tracker prose.
      owner_doc: `dev/active/platform_authority_loop.md`
      status: `pending`
      depends_on: `MP390-P0`
- [ ] `MP391-T02` Render `MASTER_PLAN.md` as a bounded tracker/projection over semantic `PlanRegistry` state and explicitly demote its free-form task prose to reference/mirror status.
      owner_doc: `dev/active/ai_governance_platform.md`
      status: `pending`
      depends_on: `MP391-T01`
- [ ] `MP391-T03` Keep `check_active_plan_sync`, docs-governance, and startup receipts honest about the new authority order so projected markdown and persisted registry state cannot drift silently.
      owner_doc: `dev/active/PLAN_FORMAT.md`
      status: `pending`
      depends_on: `MP391-T02`

### Phase MP-392 - Role Vocabulary And Ownership

Phase metadata: phase_id=MP392-P0; owner_doc=`dev/active/ai_governance_platform.md`; status=pending; depends_on=`MP391-P0`; summary=Extend the durable collaboration roles beyond reviewer/implementer/operator and bind typed packet/command ownership to those roles.

- [ ] `MP392-T01` Extend `TandemRole` with `PLANNER`, `AUDITOR`, `RESEARCHER`, and `COORDINATOR` plus aliases and default capability envelopes.
      owner_doc: `dev/active/ai_governance_platform.md`
      status: `pending`
      depends_on: `MP391-P0`
- [ ] `MP392-T02` Add `role_ownership.py` so packet kinds, command families, write surfaces, and review-only boundaries map to roles instead of provider-name assumptions.
      owner_doc: `dev/active/ai_governance_platform.md`
      status: `pending`
      depends_on: `MP392-T01`
- [ ] `MP392-T03` Route `plan_gap_review`, `plan_patch_review`, and `plan_ready_gate` through `PLANNER` ownership while keeping `AUDITOR` read-only by contract.
      owner_doc: `dev/active/ai_governance_platform.md`
      status: `pending`
      depends_on: `MP392-T02`

### Phase MP-393 - Role-Aware Runtime Routing

Phase metadata: phase_id=MP393-P0; owner_doc=`dev/active/remote_control_runtime.md`; status=pending; depends_on=`MP392-P0`; summary=Wire the expanded role model through startup, session, commit, and review-channel flows without regressing existing reviewer/implementer/operator behavior.

- [ ] `MP393-T01` Make `session-resume --role`, `startup-context --role`, `commit --role`, and review-channel actor validation accept the expanded role set.
      owner_doc: `dev/active/remote_control_runtime.md`
      status: `pending`
      depends_on: `MP392-P0`
- [ ] `MP393-T02` Surface role ownership in startup/session packets and commit gating so planner/auditor/researcher/coordinator authority is explicit at runtime.
      owner_doc: `dev/active/platform_authority_loop.md`
      status: `pending`
      depends_on: `MP393-T01`
- [ ] `MP393-T03` Add focused proof that the new roles survive remote-control and review-channel flows without breaking existing reviewer/implementer/operator semantics.
      owner_doc: `dev/active/remote_control_runtime.md`
      status: `pending`
      depends_on: `MP393-T02`

### Phase MP-394 - Assistant Command Registry And Role-Aware Command Ownership

Phase metadata: phase_id=MP394-P0; owner_doc=`dev/active/ai_governance_platform.md`; status=pending; depends_on=`MP391-P0`; summary=Split assistant-command work into a current-role portable registry first (`MP394-A`), then role-aware ownership/guards after `MP-392` / `MP-393` (`MP394-B`).

- [ ] `MP394-A-T01` Add canonical `repo_governance.assistant_commands` rows to `dev/config/devctl_repo_policy.json` with command id, goal group, plan target, allowed lanes, required bootstrap, mode preconditions, mutation policy, policy hint, provider aliases, and projection state.
      owner_doc: `dev/active/ai_governance_platform.md`
      status: `pending`
      depends_on: `MP391-P0`
- [ ] `MP394-A-T02` Materialize only the already-shipped provider assets (`control.bridge_loop`, `voice.capture_once`) from that canonical registry and keep additional command ids as truthful `planned` rows until their projections exist.
      owner_doc: `dev/active/ai_governance_platform.md`
      status: `pending`
      depends_on: `MP394-A-T01`
- [ ] `MP394-A-T03` Require provider projections to use explicit typed packet visibility (`review-channel --action inbox|watch --target <agent>`) instead of assuming Codex- or Claude-targeted packets are implicitly visible across lanes.
      owner_doc: `dev/active/ai_governance_platform.md`
      status: `pending`
      depends_on: `MP394-A-T02`
- [ ] `MP394-A-T04` Extend plan/docs sync guards so active assistant commands fail closed when they lack canonical plan linkage, truthful projection state, or current-role policy metadata.
      owner_doc: `dev/active/PLAN_FORMAT.md`
      status: `pending`
      depends_on: `MP394-A-T03`
- [ ] `MP394-B-T01` After `MP-393`, widen assistant-command ownership, allowed-role gates, and runtime guard coverage to the expanded role vocabulary without introducing command-only exceptions.
      owner_doc: `dev/active/ai_governance_platform.md`
      status: `pending`
      depends_on: `MP393-P0`
- [ ] `MP394-B-T02` Keep provider projections (`.claude/commands/*`, slash templates, future Codex assets) as generated wrappers over the canonical registry and reject provider-local registries as authority.
      owner_doc: `dev/active/PLAN_FORMAT.md`
      status: `pending`
      depends_on: `MP394-B-T01`

### Phase MP-395 - Structured Checklist Migration For Half-Done Plans

Phase metadata: phase_id=MP395-P0; owner_doc=`dev/active/operator_console.md`; status=pending; depends_on=`MP394-P0`; summary=Convert the biggest prose-only half-done plan surfaces into typed task/checklist state so routing can see them instead of burying them in long docs.

- [ ] `MP395-T01` Convert `operator_console.md` into typed phase/task or YAML/JSON-backed checklist state so its 113 unchecked items stop living as prose-only backlog.
      owner_doc: `dev/active/operator_console.md`
      status: `pending`
      depends_on: `MP394-P0`
- [ ] `MP395-T02` Migrate the remaining `remote_control_runtime.md` `MP-380..MP-387` closure items onto the same structured checklist contract without promoting a second umbrella plan.
      owner_doc: `dev/active/remote_control_runtime.md`
      status: `pending`
      depends_on: `MP395-T01`
- [ ] `MP395-T03` Add stale-item visibility rules so execution items older than 30 days surface typed owner/status metadata instead of hiding inside long-form prose.
      owner_doc: `dev/active/PLAN_FORMAT.md`
      status: `pending`
      depends_on: `MP395-T02`

### Phase MP-396 - Generator And Module-Ownership Closure

Phase metadata: phase_id=MP396-P0; owner_doc=`dev/active/ai_governance_platform.md`; status=pending; depends_on=`MP395-P0`; summary=Finish the declared generator and module-ownership surfaces so half-built scaffolds stop surviving as silent debt.

- [ ] `MP396-T01` Implement `extension_bundle.py` surface generators for the already-declared contract dataclasses and add round-trip tests proving emitted surfaces match the contract.
      owner_doc: `dev/active/ai_governance_platform.md`
      status: `pending`
      depends_on: `MP395-P0`
- [ ] `MP396-T02` Add an orphan-module detector so every module is either dispatcher-reachable or explicitly marked internal-only.
      owner_doc: `dev/active/ai_governance_platform.md`
      status: `pending`
      depends_on: `MP396-T01`
- [ ] `MP396-T03` Route generator/orphan findings through `bundle.tooling` so unfinished scaffolds fail closed instead of living only in review notes.
      owner_doc: `dev/active/ai_governance_platform.md`
      status: `pending`
      depends_on: `MP396-T02`

### Phase MP-397 - CLI And Runtime Parity Closure

Phase metadata: phase_id=MP397-P0; owner_doc=`dev/active/remote_control_runtime.md`; status=pending; depends_on=`MP396-P0`; summary=Make help text, runtime surfaces, and typed contracts tell the same truth about what is implemented, deprecated, or still experimental.

- [ ] `MP397-T01` Finish `devctl rollout-tail --follow` or mark it `[DEPRECATED]` / experimental with truthful help text and typed output contracts.
      owner_doc: `dev/active/remote_control_runtime.md`
      status: `pending`
      depends_on: `MP396-P0`
- [ ] `MP397-T02` Make CLI help and plan docs converge on one rule: every flag is implemented, deprecated, or explicitly experimental; no `--help` text may claim "not yet implemented."
      owner_doc: `dev/active/ai_governance_platform.md`
      status: `pending`
      depends_on: `MP397-T01`
- [ ] `MP397-T03` Close the remaining typed-contract/prose gap on runtime surfaces so packet/decision paths stay 1:1 with rendered docs instead of compatibility prose.
      owner_doc: `dev/active/remote_control_runtime.md`
      status: `pending`
      depends_on: `MP397-T02`

### Phase MP-400 - Hygiene Gate Category Separation

Phase metadata: phase_id=MP400-P0; owner_doc=`dev/active/ai_governance_platform.md`; status=pending; depends_on=`MP397-P0`; summary=Separate checkpoint, publication, runtime drift, and collaboration debt into typed hygiene-gate families instead of one blended blocker surface.

- [ ] `MP400-T01` Introduce one typed hygiene-gate category family across startup, status, doctor, and commit so repo-owned next-command routing stops flattening different blockers into generic red-state prose.
      owner_doc: `dev/active/ai_governance_platform.md`
      status: `pending`
      depends_on: `MP397-P0`

### Phase MP-401 - Packet Debt vs Repo Dirt

Phase metadata: phase_id=MP401-P0; owner_doc=`dev/active/review_channel.md`; status=pending; depends_on=`MP400-P0`; summary=Separate unread reviewer/implementer packet debt from repo dirt and publication backlog so collaboration work does not masquerade as hygiene drift.

- [ ] `MP401-T01` Split packet debt from repo-governance dirt in startup/status/doctor attention so unread collaboration work produces its own typed fix path instead of collapsing into checkpoint-only guidance.
      owner_doc: `dev/active/review_channel.md`
      status: `pending`
      depends_on: `MP400-P0`

### Phase MP-402 - Projection Drift Classification

Phase metadata: phase_id=MP402-P0; owner_doc=`dev/active/platform_authority_loop.md`; status=pending; depends_on=`MP401-P0`; summary=Separate stale projection drift from live authority loss so repair paths choose the right repo-owned fix instead of treating both as generic dirty state.

- [ ] `MP402-T01` Teach startup/status/doctor to classify stale projection drift separately from live runtime authority loss and emit typed repair decisions for each class.
      owner_doc: `dev/active/platform_authority_loop.md`
      status: `pending`
      depends_on: `MP401-P0`

### Phase MP-403 - Compatibility Drift As Diagnostic

Phase metadata: phase_id=MP403-P0; owner_doc=`dev/active/review_channel.md`; status=pending; depends_on=`MP402-P0`; summary=Treat compatibility-surface drift as a typed diagnostic/fix path instead of a generic dirty-worktree blocker.

- [ ] `MP403-T01` Move bridge/compatibility projection drift onto a typed diagnostic lane with explicit repair commands instead of leaving it mixed into raw worktree hygiene blockers.
      owner_doc: `dev/active/review_channel.md`
      status: `pending`
      depends_on: `MP402-P0`

### Phase MP-404 - Typed Next-Command Hygiene Routing

Phase metadata: phase_id=MP404-P0; owner_doc=`dev/active/platform_authority_loop.md`; status=pending; depends_on=`MP403-P0`; summary=Keep operator/repo-owned next-command guidance grouped by blocker family so hygiene routing stays deterministic and typed.

- [ ] `MP404-T01` Route typed hygiene-gate categories into exact next-command guidance and blocked-action state so operators and AI stop reconstructing recovery from mixed prose.
      owner_doc: `dev/active/platform_authority_loop.md`
      status: `pending`
      depends_on: `MP403-P0`

### Phase MP-405 - Guard Expansion From Dogfood Findings

Phase metadata: phase_id=MP405-P0; owner_doc=`dev/active/review_probes.md`; status=pending; depends_on=`MP404-P0`; summary=Expand guard coverage for packet-to-plan promotion, half-built plan-state drift, and the recurring dogfood findings now visible in typed review state.

- [ ] `MP405-T01` Add the first repo-owned guard family for packet-to-plan promotion gaps, including the packet-only `look-first / half-built-guard / graph extension` A/B/C decision trail so it cannot live only in packet prose again.
      owner_doc: `dev/active/review_probes.md`
      status: `pending`
      depends_on: `MP404-P0`
- [ ] `MP405-T02` Land the first half-built typed-state guard slice from `rev_pkt_1221`: start with enum/field/value routes that define typed state without any canonical producer, consumer, or branch coverage, and require the `look-first` search discipline before new typed contracts land.
      owner_doc: `dev/active/review_probes.md`
      status: `pending`
      depends_on: `MP405-P0`

### Phase MP-406 - Guard/Probe Generator Path

Phase metadata: phase_id=MP406-P0; owner_doc=`dev/active/review_probes.md`; status=pending; depends_on=`MP405-P0`; summary=Add one repo-owned generator path for recurring guard/probe additions so new detection seams land as typed artifacts instead of prose-only ideas.

- [ ] `MP406-T01` Generate guard/probe scaffolds from typed findings metadata so repeated architectural seams stop waiting on manual copy/paste or chat memory before they become repo-owned checks.
      owner_doc: `dev/active/review_probes.md`
      status: `pending`
      depends_on: `MP405-P0`

### Phase MP-407 - Higher-Order Probe Sophistication

Phase metadata: phase_id=MP407-P0; owner_doc=`dev/active/review_probes.md`; status=pending; depends_on=`MP406-P0`; summary=Teach probes to detect higher-order runtime/plan drift rather than only local file smells.

- [ ] `MP407-T01` Expand probe reasoning so cross-surface drift, packet-only plan state, and half-built governance seams become first-class probe findings instead of operator-discovered surprises.
      owner_doc: `dev/active/review_probes.md`
      status: `pending`
      depends_on: `MP406-P0`
- [ ] `MP407-T02` Promote the `higher-order guards + self-teaching` directive from `rev_pkt_1222` into typed probe scope, starting with stress-abstraction, polymorphism-consistency, and architectural-decision mismatches as explicit governed probe classes rather than packet-only ideas.
      owner_doc: `dev/active/review_probes.md`
      status: `pending`
      depends_on: `MP407-P0`

### Phase MP-408 - Smart Guard Reasoning

Phase metadata: phase_id=MP408-P0; owner_doc=`dev/active/review_probes.md`; status=pending; depends_on=`MP407-P0`; summary=Make guard logic smart enough to reason about half-built scaffolds, graph/plan mismatch, and repeated coherence debt.

- [ ] `MP408-T01` Promote the `higher-order guards + self-teaching` decision lane into typed guard logic so the guard layer can reject known half-built or incoherent states without waiting for chat interpretation.
      owner_doc: `dev/active/review_probes.md`
      status: `pending`
      depends_on: `MP407-P0`

### Phase MP-409 - Coherence Restoration

Phase metadata: phase_id=MP409-P0; owner_doc=`dev/active/ai_governance_platform.md`; status=pending; depends_on=`MP408-P0`; summary=Restore coherence across docs, runtime, help text, generated projections, and quality surfaces after the smarter guard/probe rollout.

- [ ] `MP409-T01` Reconcile docs/help/runtime/generated surfaces after the expanded guard/probe lane so higher-order coherence fixes stop bouncing between packet findings and stale projections.
      owner_doc: `dev/active/ai_governance_platform.md`
      status: `pending`
      depends_on: `MP408-P0`

### Phase MP-411 - Portability Audit Closure

Phase metadata: phase_id=MP411-P0; owner_doc=`dev/active/portable_code_governance.md`; status=pending; depends_on=`MP409-P0`; summary=Run the full portability audit and remove remaining repo-specific leakage from portable layers before wider adopter proof.

- [ ] `MP411-T01` Audit the portable-engine/runtime/help/code-shape surfaces for remaining repo-specific literals or hidden VoiceTerm defaults, then thread the existing `ProjectGovernance.path_roots` and repo-pack seams through the offenders.
      owner_doc: `dev/active/portable_code_governance.md`
      status: `pending`
      depends_on: `MP409-P0`

### Phase MP-412 - Harness Authorization Contract

Phase metadata: phase_id=MP412-P0; owner_doc=`dev/active/platform_authority_loop.md`; status=pending; depends_on=`MP411-P0`; summary=Define one HarnessAuthContract so automation knows when typed state already authorizes the next step instead of waiting on chat or launcher lore.

- [ ] `MP412-T01` Introduce the first typed harness-authorization contract that binds role, topology, and current authority snapshot to the sanctioned next actions without per-command chat reconstruction.
      owner_doc: `dev/active/platform_authority_loop.md`
      status: `pending`
      depends_on: `MP411-P0`

### Phase MP-413 - Staged Intent And Worker Output Closure

Phase metadata: phase_id=MP413-P0; owner_doc=`dev/active/remote_commit_pipeline.md`; status=pending; depends_on=`MP412-P0`; summary=Close staged-intent and worker-created-file staging gaps so governed mutation preserves user intent without manual `git add` repair.

- [ ] `MP413-T01` Make governed mutation preserve worker-created files and staged user intent through the managed commit path so remote-control and local lanes stop requiring manual staging cleanup to keep typed state truthful.
      owner_doc: `dev/active/remote_commit_pipeline.md`
      status: `pending`
      depends_on: `MP412-P0`

### Phase MP-414 - Typed Decision Policy

Phase metadata: phase_id=MP414-P0; owner_doc=`dev/active/platform_authority_loop.md`; status=pending; depends_on=`MP412-P0`; summary=Promote typed decision policy so A/B/C architecture choices land in one repo-owned decision surface instead of packet prose.

- [ ] `MP414-T01` Add the first typed decision-policy lane that records unresolved architectural choices, accepted branches, and approval posture so packet-only A/B/C prompts become typed state before more code lands.
      owner_doc: `dev/active/platform_authority_loop.md`
      status: `pending`
      depends_on: `MP412-P0`
- [ ] `MP414-T02` Promote `rev_pkt_1221`, `rev_pkt_1222`, `rev_pkt_1223`, and `rev_pkt_1234` into typed decision authority, including explicit branch choices for `look-first`, graph/guard expansion, and attention-stale handling before those packets leave the pending queue.
      owner_doc: `dev/active/platform_authority_loop.md`
      status: `pending`
      depends_on: `MP414-P0`

### Phase MP-415 - Collaboration Role Contract Read-Side

Phase metadata: phase_id=MP415-P0; owner_doc=`dev/active/ai_governance_platform.md`; status=done; depends_on=`MP414-P0`; summary=Land the collaboration-role contract read-side closure and keep mutation/verifier/watcher ownership derived from typed runtime state.

- [x] `MP415-T01` Project mutation, verification, and watcher ownership through typed collaboration/runtime state so startup, status, and startup-facing summaries stop inferring roles from dev dogfood posture.
      owner_doc: `dev/active/ai_governance_platform.md`
      status: `done`
      depends_on: `MP414-P0`

### Phase MP-416 - Reviewer Wake On Packet Post

Phase metadata: phase_id=MP416-P0; owner_doc=`dev/active/review_channel.md`; status=done; depends_on=`MP415-P0`; summary=Close reviewer wake-on-packet-post so repo-owned review traffic can relaunch or notify the reviewer lane without manual polling.

- [x] `MP416-T01` Wire packet-post reviewer wake to the typed review-state authority and make the wake outcome visible in the post receipt instead of relying on silent polling.
      owner_doc: `dev/active/review_channel.md`
      status: `done`
      depends_on: `MP415-P0`

### Phase MP-417 - Snapshot Drift Ordering

Phase metadata: phase_id=MP417-P0; owner_doc=`dev/active/remote_commit_pipeline.md`; status=pending; depends_on=`MP416-P0`; summary=Fix snapshot-drift and governance-refresh ordering so commit/push and review status stop dirtying the worktree after stage approval.

- [ ] `MP417-T01` Move or harden the post-stage refresh path so staged-tree approval, review-state refresh, and compatibility projection writes stay idempotent and do not regenerate dirty worktree churn after approval.
      owner_doc: `dev/active/remote_commit_pipeline.md`
      status: `pending`
      depends_on: `MP416-P0`
- [ ] `MP417-T02` Treat `attention_revision_stale` as a separate prior slice, not a babysat side effect of later wake/ownership work: make commit authority tolerate peer packet/attention advancement when the staged tree and approved slice state are unchanged, as escalated in `rev_pkt_1223` and `rev_pkt_1234`.
      owner_doc: `dev/active/remote_commit_pipeline.md`
      status: `pending`
      depends_on: `MP417-P0`

### Phase MP-418 - Process Lifecycle Ownership

Phase metadata: phase_id=MP418-P0; owner_doc=`dev/active/remote_control_runtime.md`; status=pending; depends_on=`MP417-P0`; summary=Define one process-lifecycle ownership contract for reviewer, implementer, publisher, and watchers so silent death becomes typed runtime state instead of lore.

- [ ] `MP418-T01` Emit one repo-owned process-lifecycle ownership contract for reviewer, implementer, publisher, and watchers so silent death, detached runtimes, and stale observers resolve through typed state instead of operator memory.
      owner_doc: `dev/active/remote_control_runtime.md`
      status: `pending`
      depends_on: `MP417-P0`
- [x] `MP418-T02` Project per-lane host wake capability (`continuous`, `tick_based`, `manual_nudge_required`) into typed collaboration/authority state and fail closed when `active_dual_agent` lacks continuous wake on mutation, verification, or watcher ownership.
      owner_doc: `dev/active/remote_control_runtime.md`
      status: `done`
      depends_on: `MP415-P0`
- [x] `MP418-T03` Project one typed loop-autonomy contract across single-agent, dual-agent, local, and remote-control modes so control-plane surfaces stop treating host wake as a remote-only special case or a dual-agent-only guard.
      owner_doc: `dev/active/remote_control_runtime.md`
      status: `done`
      depends_on: `MP418-T02`

### Phase P2 - Closed-Loop Quality Composition And Audit Orchestration

Phase metadata: phase_id=MP377-P2; owner_doc=`dev/active/review_probes.md`; status=pending; depends_on=`MP377-P0`, `MP377-P1`; summary=Turn the existing guards, probes, dogfood ledger, and planning reducers into one closed quality loop with shared inputs and consumable outputs.

- [ ] `MP377-P2-T01` Compose `probe_split_advisor.py` from function clusters, import graph fan-out, and hotspot context.
      owner_doc: `dev/active/review_probes.md`
      status: `pending`
      depends_on: `MP377-P1-T01`
- [ ] `MP377-P2-T02` Feed canonical backlog findings and guard/probe outputs back into planning and findings-priority instead of parallel markdown-only lanes.
      owner_doc: `dev/active/autonomous_governance_loop_v2.md`
      status: `pending`
      depends_on: `MP377-P0-T01`
- [ ] `MP377-P2-T03` Remove recent-history blinders from planning so full governed finding history can drive slice selection.
      owner_doc: `dev/active/platform_authority_loop.md`
      status: `pending`
      depends_on: `MP377-P0-T01`
- [ ] `MP377-P2-T04` Compose a multi-agent `devctl dogfood` audit runner that exercises command/guard/probe/role coverage, persists cross-session coverage, and records real failures through `governance-review`.
      owner_doc: `dev/active/autonomous_governance_loop_v2.md`
      status: `pending`
      depends_on: `MP377-P0-T04`, `MP377-P0-T06`, `MP377-P1-T05`
- [ ] `MP377-P2-T05` Promote dogfood from ad hoc walkthrough to the development engine: persist repo-owned dev-mode coverage/results, feed them back into `FindingBacklog`, `findings-priority`, and planning reducers, and make new platform work land with a dogfood proof path instead of `/tmp` notes or operator memory.
      owner_doc: `dev/active/autonomous_governance_loop_v2.md`
      status: `pending`
      depends_on: `MP377-P0-T04`, `MP377-P0-T06`, `MP377-P1-T07`
- [ ] `MP377-P2-T06` Enforce the observer boundary for dashboard/phone/operator surfaces: read-model consumers may render, explain, and route typed action requests, but they must not become hidden implementation lanes, process-killers, or prose-only authority patches.
      owner_doc: `dev/active/remote_control_runtime.md`
      status: `pending`
      depends_on: `MP377-P1-T08`, `MP377-P2-T05`

### Phase P3 - Portable Proof And Adopter Audit

Phase metadata: phase_id=MP377-P3; owner_doc=`dev/active/portable_code_governance.md`; status=pending; depends_on=`MP377-P0`, `MP377-P1`, `MP377-P2`; summary=Prove the consolidated owner-doc set, typed plan authority, and dogfood audit path on another repository without core-engine patching.

- [ ] `MP377-P3-T01` Validate the reduced execution-owner set plus typed plan routing and dogfood audit coverage on a second repo layout.
      owner_doc: `dev/active/portable_code_governance.md`
      status: `pending`
      depends_on: `MP377-P2-T02`, `MP377-P2-T04`
- [ ] `MP377-P3-T02` Close the remaining repo-default assumptions in startup, review transport, and governed mutation proof surfaces.
      owner_doc: `dev/active/portable_code_governance.md`
      status: `pending`
      depends_on: `MP377-P3-T01`

Legacy checklist below remains reference backlog until migrated into the typed
phase/task contract above. Startup/work-intake routing and plan guards must
prefer the typed phase/task entries before any free-form backlog bullets.

- [x] Consolidate the repo-grounded architecture review, boundary analysis, and
      phased roadmap into this one active plan so the work no longer depends on
      chat history or overlapping architecture docs.
- [x] Define the reusable package/workspace boundary and naming so the platform
      can ship independently from VoiceTerm.
- [x] Write one durable maintainable architecture/thesis/flowchart guide for
      the reusable platform so the product direction is not trapped in active
      plan notes or chat history alone.
- [x] Generate one bounded repo/product thesis starter (`Why Stack`) that
      `startup-context` reads before SOP/router detail: in roughly 300-500
      tokens it must state the product mission, proof obligation, platform
      boundaries, and the current priority so fresh AI sessions stop learning
      process without understanding why the process exists.
- [ ] Make that same bootstrap/instruction layer enforce the client-vs-core
      boundary explicitly: generated `CLAUDE.md`, starter setup docs, and
      future wrapper surfaces must tell agents that VoiceTerm is a first-party
      client/product integration over the portable governance platform, while
      repo packs and typed runtime contracts remain the backend authority for
      arbitrary repos. Another repo's generated surfaces must carry the same
      platform thesis with that repo's own product summary instead of
      inheriting VoiceTerm-specific identity or hidden path assumptions.
- [ ] Absorb the typed-authority convergence synthesis into the existing owner
      chain instead of promoting a new architecture tracker: Phase 0 governed
      mutation / publish cutover stays in `remote_commit_pipeline.md`,
      producer/identity/authority-path closure stays in
      `platform_authority_loop.md`, read-side/bootstrap/prompt convergence
      stays in `remote_control_runtime.md`, and second-repo proof stays in
      `portable_code_governance.md`. `MASTER_PLAN.md` remains the tracker and
      subordinate plans must stay in landed/open/priority parity.
- [ ] Keep the architecture guard stack layered instead of overloading
      `package_layout`: crowded-root and compatibility-shim governance remain
      the coarse self-hosting backstop, while product closure must come from
      targeted authority/parity guards for governed mutation anti-bypass,
      authoritative review-state production, identity-tuple parity,
      read-model-first consumers, `SystemCatalog` / `AgentDispatchPacket`
      schema parity, and prompt/bootstrap field-route coverage.
- [ ] Keep `context-graph` / `ConceptIndex` / ZGraph-style intelligence
      subordinate to typed authority and measured proof: graph-backed routing
      or duplicate-authority detection should start as probes or bounded
      reducers over canonical contracts, then only graduate into blocking
      guards after replay/corpus validation proves low-noise behavior.
- [ ] Keep repo entrance surfaces split by audience until extraction is real:
      the root `README.md` in this repo remains the VoiceTerm product/user
      entrypoint while the portable governance platform gets its own
      developer/maintainer entry surface inside the monorepo first and only
      later becomes the root README of the extracted platform repo/package.
      AI-system/control-plane changes must not keep routing through VoiceTerm
      user docs unless product behavior actually changed.
- [ ] Make AI/bootstrap instruction surfaces repo-pack-driven and scope-aware:
      generated `CLAUDE.md`, startup receipts, bridge/conductor prompts, and
      other AI-facing bootstrap text must render the product thesis, active
      workflow mode, and canonical authority chain from `ProjectGovernance` /
      `RepoPack` / `DocPolicy` / `PlanRegistry` instead of embedding
      VoiceTerm-only paths or tandem-review rules as if they were universal.
- [ ] Add one developer-mode bounded-implementer workflow surface over that
      same authority chain: generated implementer instructions, slice
      closeout packets, and audit-ready status summaries must keep the
      human/operator as checkpoint/push authority, keep Codex/Claude bounded
      to one slice at a time, and emit stable fields (`SLICE GOAL`,
      changed files, why, checks run, open risks, recommended next step) so
      outside reviewers can audit a slice without reconstructing chat state.
      Use the same typed decision/current-state inputs for those agent-facing
      instructions instead of asking models to reconstruct authority from
      bridge prose or session memory.
- [ ] Land one explanation projection over typed runtime state instead of
      bridge/chat prose: materialize `DecisionTrace` for startup/review/push
      decisions, keep only current truth under `review_state.json` /
      `current_session`, and render bridge/latest/chat/status/external-audit
      packets plus generated implementer/reviewer instruction views from those
      typed records instead of inventing the "why" in append-only markdown.
- [ ] Make explanation outputs deterministic and teachable: define one small
      schema-validated decision-record vocabulary for startup/review/push and
      later runtime decisions (`status`, `goal`, `facts_observed`,
      `rules_triggered`, `rejected_options`, `chosen_action`, `next_command`,
      `uncertainty`), keep direct observations separate from guesses, and
      render junior-dev-readable explanation views from that packet instead of
      asking AI for open-ended reasoning prose in the authoritative path.
- [ ] Keep live current-status projection narrow and typed: the authoritative
      `review_state.json.current_session` block should carry only the current
      answer by reference to the latest `DecisionTrace`
      (`latest_decision_trace_id`, next action, wait/block reasons, bounded
      blocker summary, and live reviewer/ack state), while `bridge.md`,
      `latest.md`, chat packets, CLI status, and operator views remain
      projections over that typed state rather than carrying independent
      current truth. Adjacent review-freshness booleans such as
      `bridge.reviewed_hash_current` / `bridge.review_needed` should live in
      the same typed `ReviewState` artifact instead of surviving only in the
      ephemeral CLI status envelope.
- [ ] Add one minimal `explain-latest` read surface over the same owner chain:
      it should load `current_session` plus the latest `DecisionTrace` and
      render what changed, why the system chose continue/checkpoint/review/
      push, which evidence blocked or allowed that choice, and the exact next
      command. Treat this as the first explicit explanation command, not as a
      parallel authority path.
- [x] Add one platform-owned Python architecture guide and decision tree
      aligned with the same contract-first style: teach when to use `dict`,
      `TypedDict`, `dataclass`, boundary-validation models, and `Protocol`,
      then connect those modeling choices to repository/service/unit-of-work/
      dependency-injection patterns in plain language. Treat Cosmic Python
      (Ch. 1-6, 8, 13), the official typing docs, Pydantic strict-mode/JSON
      Schema, and FastAPI boundary-model docs as the recommended starter
      stack, while keeping Pydantic scoped to untrusted or serialized
      boundaries rather than as the default internal model for every runtime
      contract.
- [x] Start the explanation rollout from existing typed packets instead of
      waiting for a greenfield `DecisionTrace` module: extend
      `DecisionPacketRecord` plus routed startup/task-router/workflow-profile
      receipts with `match_evidence`, rejected-rule traces, and plain-
      language rule summaries so selected bundles and next commands explain
      why they were chosen before the full provenance-grade trace family
      lands. First rollout targets are explicit: task-router lane selection,
      `selected_workflow_profile`, startup/push decisions, and context-graph
      query relevance ("why this node matched") before widening to broader
      runtime traces.
- [x] Reuse the shipped probe teaching corpus before authoring a second
      disconnected tutorial stack: render
      `dev/scripts/checks/probe_report/practices.py` /
      `SIGNAL_TO_PRACTICE` explanations and fix patterns directly into
      canonical probe packets, and add plain-language metric explanations for
      `fan_in`, `fan_out`, `bridge_score`, and hotspot rank so quality
      signals stop acting like unlabeled telemetry. The rich markdown probe
      report already carries more of this teaching detail; the remaining
      rollout is to preserve that same why/fix/metric layer in compact
      startup/status/context-graph projections instead of compressing back to
      raw numbers.
- [x] Explain context-graph/query relevance in the same vocabulary: query
      matches, ranking/downgrade choices, and selected hotspot/context nodes
      should surface one short "why this node matched / why this node ranked"
      explanation instead of only temperatures, edge counts, or returned file
      lists.
- [x] Add one read-only executable platform blueprint surface
      (`devctl platform-contracts`) so frontends, adopters, and AI setup flows
      can consume the intended backend/repo-pack contract in machine-readable
      form instead of parsing active-plan prose only.
- [ ] Define the shared runtime contracts (`RepoPack`, `ControlState`,
      `TypedAction`, `RunRecord`, `ArtifactStore`, `ProviderAdapter`,
      `WorkflowAdapter`, `ExtensionBundle`, and `AutomationSpec`) in one
      canonical backend layer.
- [ ] Define one real resolved repo-pack contract before `P1`: the runtime,
      frontends, and adopters should consume one typed repo-pack object
      carrying pack identity, policy path, path config, workflow profiles,
      compatibility/version requirements, and feature flags instead of
      reconstructing that state from VoiceTerm-specific globals.
- [ ] Freeze the composable-module contract explicitly: each major subsystem
      must name its standalone entrypoint, shared contract, and integrated-app
      role so the platform stays modular without turning into disconnected
      tools.
- [ ] Define one system coherence matrix and guard strategy across vocabulary,
      identity, state, action, artifact, lifecycle, projections, parity, and
      portability so drift prevention is platform-owned instead of spread
      across many local rules.
- [ ] Add one platform-wide portability-drift prevention stack for the AI
      coding system itself: classify which layers are allowed to mention
      product-specific paths or names, add static detection for repo-name/path
      literals plus import-time path-config capture in portable layers, and
      prove the result on fixture repos that cover empty-repo bootstrap,
      existing-repo adoption, alternate layout roots, and tandem-disabled
      operation. The first forbidden-literal set should include
      `dev/active`, `dev/reports`, `dev/scripts`, `bridge.md`,
      `local_terminal`, `VOICETERM_*`, fixed review-status/session-cache
      paths, and VoiceTerm package/layout names when they appear in
      portable/runtime/tooling layers outside approved compatibility or
      repo-pack integration surfaces.
- [ ] Make read-only control surfaces truly no-write-safe: `platform-contracts`,
      `quality-policy`, `mcp`, `system-picture`, and other report/status
      surfaces must be able to run on read-only mounts or restricted adopters
      without appending audit-event or telemetry artifacts by default.
      Separate explicit write sinks from read-only command execution, make the
      active write mode visible in receipts, and prove the contract with
      fixture/sandbox coverage.
- [ ] Add one repo-pack-owned `ExtensionBundle` generator over project-scoped
      Codex/Claude/MCP surfaces: emit `.codex/hooks.json`, `.mcp.json`,
      `.claude/settings.json`, `.claude/agents`, `.claude/skills`,
      `.agents/skills`, and later plugin manifests/marketplace metadata from
      `ProjectGovernance` / `RepoPack` / `DerivedCapabilityContract` instead
      of hand-maintained tool configs or VoiceTerm literals.
- [ ] Add one typed `AutomationSpec` over governed background work: the same
      task definition should target local scheduler, GitHub workflow
      cron/dispatch, Codex Automations, Claude project commands/agents, or
      later queue runners while preserving one approval/evidence/action
      contract and avoiding transport-specific policy forks.
- [ ] Freeze the backend authority contract in executable form: define the
      canonical reducer-backed JSON/runtime authority, typed action/write
      surface, receipt/telemetry path, optional local service/API seam, and
      which markdown/UI artifacts remain projections only.
- [ ] Freeze the stable backend protocol boundary explicitly: define the
      service/API contract that frontends, wrappers, hooks, and future shells
      consume so file reads and command wrappers remain transitional rather
      than becoming the permanent cross-client interface.
- [ ] Close the backend transport and tempfile security backlog cluster from
      `issues.md`: `ISS-047`, `ISS-048`, and `ISS-049` stay owned here until
      local daemon/control sockets default to restricted permissions,
      temporary file creation moves to unpredictable secure helpers instead of
      fixed `/tmp` paths, and the shared bridge/service transport binds
      locally with an explicit authentication story instead of exposing
      network-reachable defaults.
- [ ] Freeze the local service lifecycle contract: define how the shared
      backend is launched, discovered, attached, health-checked, resumed,
      and shut down when run standalone, through `devctl`, or through
      VoiceTerm as an optional local host path, without changing backend
      semantics across those entrypoints.
- [ ] Freeze the daemon-vs-controller split explicitly: document which current
      responsibilities belong to transport/session attach versus the
      controller-owned review/queue/lifecycle loop so "daemon exists" never
      gets treated as proof that the controller path is already complete.
- [ ] Add a portable contract-sync guard for that same lifecycle surface:
      `platform-contracts`, runtime/client parity tests, and cross-language
      protocol checks must fail when lifecycle or caller-authority shape
      drifts. This must work as reusable governance, not only as local
      reviewer habit.
      First bounded implementation: a dedicated `platform-contract-sync`
      guard over the shared blueprint contracts, instead of overloading the
      VoiceTerm mobile-relay guard or the architecture-surface sync guard.
- [ ] Make spec-vs-reality drift explicit and executable: architecture/spec
      docs must mark which contracts are implemented, partial, or planned, and
      parity guards must prove that emitted blueprint surfaces match the real
      runtime/model coverage instead of letting aspirational docs read like
      shipped behavior.
- [ ] Define the backend-closure milestone explicitly: one authority model,
      one action router, one agent/job registry, one parity/conformance suite,
      and markdown de-authorized to bootstrap/projection status only before
      declaring the operator system stable.
- [ ] Extract Ralph, mutation, review-channel, and host-process hygiene loops
      off repo-local assumptions and onto those shared contracts.
- [ ] Converge CLI, PyQt6 operator console, overlay/TUI, and phone/mobile
      views onto the same runtime state model instead of duplicated shaping.
- [ ] Make machine-readable runtime state authoritative in live operation:
      `review_state.json`, typed projections, and registry state should be the
      source of truth while markdown, PyQt6, phone/mobile, and terminal views
      stay projections over that same backend.
- [ ] Ship a bootstrap/adoption flow that an AI can run against a new repo
      without hand-editing core engine code.
- [ ] Add a self-hosting simplification program for the governance engine
      itself: consolidate overlapping active plans once their lanes stabilize,
      graduate mature operational systems from `dev/active/` into durable
      guides, reduce hot-start mandatory reading, and prove the engine can
      explain itself without a routing maze.
- [ ] Promote the documentation-authority system to a major `MP-377`
      priority: AI and humans should not bootstrap from overlapping prose.
      The product needs one unified docs system that keeps markdown bounded,
      authoritative, lifecycle-managed, and consistent across repos.
- [ ] Extend the existing package-layout / compatibility-shim governance into
      one broader repo-owned structure policy for the governance engine
      itself: package roles (`public_entrypoint`, `compat_shim`,
      `implementation_package`, `support_module`, `generated_artifact`,
      `doc_authority`), `devctl` root-file budgets, approved parser/command
      locations, subsystem file-count budgets, source-of-truth ownership,
      active-doc lifecycle, and shim expiry should be policy-backed instead of
      left as reviewer memory.
- [ ] Project that same structure policy into one startup/AI-readable
      organization surface so agents see declared package roles, allowed
      exceptions, and live layout debt instead of treating a green budget
      receipt as proof that the repo is semantically organized.
- [ ] Define one repo-pack-owned documentation contract (`DocPolicy`) over
      governed markdown/doc surfaces: doc classes
      (`tracker`, `spec`, `runbook`, `guide`, `reference`,
      `generated_report`, `archive`), allowed roots, lifecycle and graduation
      rules, hot/warm/cold context budgets, active-plan count budgets,
      startup-token budgets, and shadow-authority rejection rules.
- [ ] Freeze the initial governed-markdown header contract. Plan docs
      (`tracker`, `spec`, `runbook`) should carry one canonical metadata
      header with `Status`, `Last updated`, `Owner`, `MP`, `Role`,
      `Authority`, and the execution-plan marker. Non-plan governed docs
      should carry a reduced metadata header tied to `DocRegistry` without
      pretending they are execution plans.
- [ ] Freeze the initial closed taxonomies behind that contract instead of
      allowing arbitrary prose drift: status values, owner-lane values,
      role values, and authority values should become repo-pack-owned enums
      or config-backed closed sets, not free-form strings.
- [ ] Freeze initial line-budget policy by doc class with explicit
      warning/fail/exception semantics. Seed targets:
      `spec` soft `1200` hard `2000`, `runbook` soft `200` hard `400`,
      `guide` soft `800` hard `1500`, `reference` soft `150` hard `300`,
      and `tracker` on a transitional exception path until the
      `MASTER_PLAN` state/changelog split lands. Over-budget docs must either
      shrink or carry a tracked exception with owner + expiry.
- [ ] Define one `DocRegistry` companion over all governed docs while
      `PlanRegistry` remains the mutable execution subset. `DocRegistry`
      should record class, owner, authority, lifecycle, scope, summary, token
      budget, and canonical consumer so startup can load bounded consistent
      context instead of rereading the whole repo.
- [ ] Freeze the canonical markdown contract for governed plan docs:
      machine-readable metadata headers, standard section order, stable anchor
      generation, and formatter/normalizer compatibility so plan markdown can
      be organized consistently and turned into typed registry state.
- [ ] Extend the existing docs-governance stack instead of inventing a second
      docs platform: `docs-check`, `check_active_plan_sync`, `hygiene`, and
      `check_architecture_surface_sync` should enforce doc authority,
      lifecycle, placement, budget, and shadow-roadmap rules. Add a dedicated
      `check_doc_authority_contract.py` only if those current surfaces cannot
      model the contract cleanly.
- [ ] Keep `doc-authority` classification deterministic under that same
      docs-governance lane: canonical guide/reference/spec/runbook classes
      must come from policy/registry shape rather than ad hoc path fallbacks,
      and focused regression tests should pin root-guide classification before
      `DocRegistry` becomes startup authority.
- [ ] Dogfood that same markdown contract on the repo's own active plans:
      bring execution-plan docs into parity with the enforced section order,
      metadata-header parsing, and `Session Resume` restart contract before the
      future `PlanRegistry` / `PlanTargetRef` loader claims markdown-derived
      startup authority. Legacy active specs that still sit outside the
      execution-plan marker path must be migrated explicitly rather than left
      as silent formatting exceptions.
- [ ] Land `check_plan_doc_format.py` as the first bounded new docs guard
      under that existing governance stack. Required checks:
      metadata header presence, metadata validity against closed taxonomies,
      MP/INDEX linkage, required section presence, section order, line-budget
      policy, orphan-file detection, execution-plan marker presence, and
      `MASTER_PLAN`/registry linkage for active specs.
- [ ] Upgrade the current docs guards as part of that same slice:
      `check_markdown_metadata_header.py` should enforce header existence
      rather than only normalize it, `check_active_plan_sync.py` should move
      from hardcoded plan coverage to registry-driven coverage, and guide
      validation should stay policy-driven instead of becoming another
      hardcoded one-off scanner.
- [ ] Make operational-doc graduation explicit: once a subsystem becomes
      stable runtime behavior, move its broad description to guides/runbooks
      and keep only live delta execution state under `dev/active`.
- [ ] Run the first measured documentation-consolidation tranche with explicit
      baselines and targets. Current measured baseline:
      `26` active markdown docs / `27,462` lines, `15` guide/reference docs /
      `9,874` lines after moving the whole-system audit references under
      `dev/guides/`, and
      `1,858` lines across maintainer entry docs (`AGENTS.md` +
      `dev/README.md`). Initial target: reduce active-doc count
      toward `~20`, cut active-line volume materially, and stop carrying
      multiple giant active specs that mix architecture, migration history,
      and competitive/reference material in one file.
- [ ] Name the first documentation-consolidation wave explicitly:
      retire or relocate clear reference-only `dev/active` surfaces
      (`audit.md`, `move.md`, bridge `phase2.md`) from live active authority;
      graduate stable operational docs such as
      `host_process_hygiene.md` / `loop_chat_bridge.md` when their remaining
      execution delta is near zero; and trim oversized active docs by moving
      completed phases, comparative analysis, and long reference sections into
      guides/reference/archive surfaces.
- [ ] Front-load the platform/client boundary in plain-language architecture,
      runbook, and generated bootstrap docs. `DEVCTL_ARCHITECTURE`,
      review/runbook surfaces, starter instruction docs, and later
      `doc-authority` reports must teach that VoiceTerm is a first-party
      adopter/client, `bridge.md` is an optional repo-pack-owned compatibility
      projection, and review/MCP/mobile/PyQt6 surfaces are clients over one
      governed backend rather than universal defaults.
- [ ] Absorb the full `dev/guides/SYSTEM_AUDIT.md` action plan into the canonical
      `MP-377` checklist instead of leaving it in a parallel document.
      Required mapping:
      blocker-tranche security items (`D*`, `S*`) -> authority-loop blocker
      tranche; evidence/integrity/feedback items (`E*`, `G*`, `A1-A4`) ->
      startup/evidence/context closure; bootstrap compression (`A5-A8`) ->
      hot/warm/cold `startup-context` and later knowledge-base layers;
      memory/session items (`A9-A12`) -> `ContextPack` + memory bridge;
      structural debt items (`A13-A17`) -> self-hosting simplification,
      check-runner/framework, review-channel consolidation, and root/package
      cleanup; surface simplification (`A18-A21`) -> command/CI/workflow
      contraction; portability (`A22-A26`) -> repo-pack/runtime activation,
      packaging, and cross-repo proof; black-box strengthening (`A27-A30`) ->
      missing guard/probe + governance-review closure; test-hardening
      (`T1-T5`) -> guard/runtime/integration coverage gates.
- [ ] Keep the named `SYSTEM_AUDIT` remediation ideas visible where they fit
      the architecture instead of dissolving into generic prose:
      `governance-quality-feedback` in startup, a shared guard/check runner,
      review-channel consolidation, root/package consolidation, shared
      markdown/artifact writers, contract single-source-of-truth closure, and
      parser-location unification each need explicit owners/phases in this
      plan chain.
- [ ] Land one first-step command for this slice:
      `python3 dev/scripts/devctl.py doc-authority --format md`.
      It should scan governed markdown docs, emit `DocRegistry` /
      authority-budget summaries, report format drift and overlapping
      authority, identify consolidation candidates, and become the standard
      startup surface for reviewer/coder sessions working on docs-governance.
      Later `--write` may scaffold metadata headers, registry rows, or
      normalization fixes, but the first slice should be read-only.
- [ ] Make the machine-readable governance surface singular in the startup
      story: runtime authority must come from `project.governance.json` (or a
      generated equivalent) plus typed registries/receipts. The reviewed
      markdown contract explains and reviews that state for humans, but it
      must not compete with the machine authority or become a second startup
      truth.
- [ ] Prefer strengthening the current package-layout / shim-governance path
      for that structure policy before inventing a second unrelated topology
      framework; only add a distinct guard when the contract boundary is
      genuinely different.
- [ ] Add one self-hosting anti-sprawl guard surface that fails on structure-
      policy budget overruns, unauthorized new root modules or parser
      locations, duplicate authority families, and new audit/spec documents
      that try to behave like shadow roadmaps outside the canonical plan
      chain.
- [ ] Freeze the audit-integration retirement rule: whole-system audit docs
      such as `dev/guides/SYSTEM_AUDIT.md` are temporary reference evidence.
      Accepted findings must be absorbed into canonical plans and maintainer
      docs, and the moved reference copy should be retired once those
      findings are fully
      integrated or explicitly rejected.
- [ ] Freeze the same absorption-first archive gate for root evidence
      companions and reference bridges too: no root markdown cleanup or active-
      doc demotion should happen until `doc-authority` can show that accepted
      conclusions were mirrored into `MASTER_PLAN` plus the owning scoped
      docs, with no remaining execution-only state stranded in the candidate
      file.
- [ ] Add one reviewed repo-local governance contract surface
      (`project.governance.md` as the current working name): human-readable,
      AI-draftable, machine-enforceable repo identity that captures languages,
      source/test roots, architecture/layer hints, boundary rules, quality
      goals, priorities, debt, and exception intent in a compact startup-safe
      form.
- [ ] Split that setup flow into deterministic draft -> human review ->
      materialize: `governance-draft` should infer the sections a scan can
      prove, leave explicit fill-in markers for team priorities/debt/ignore
      areas, then `governance-bootstrap` and/or a later `governance-init`
      should derive repo policy and startup surfaces from the approved
      contract instead of requiring manual policy hand-authoring first.
- [ ] Let the same contract power conversational onboarding too: when a repo
      has governance tooling but no approved governance contract yet, AI
      startup flows should summarize the detected repo shape, ask for the few
      human-only adjustments, and then write the reviewed contract instead of
      dropping users into raw config editing.
- [ ] Freeze `OnboardingContract` as a first-class shared contract instead of
      leaving onboarding spread across bootstrap helpers and starter-policy
      dicts. Required first fields: onboarding mode
      (`auto|assisted|locked_down`), ratification status, inferred policy
      payload, path roots, unresolved authority questions, and field-level
      `InferenceProvenance` so adopters can see what the system inferred and
      what still needs human approval.
- [ ] Add an evolution path for that contract: when the live repo scan no
      longer matches the approved governance document (new layers, roots,
      workflows, or boundary shapes), surface suggested updates or explicit
      exclusions so the contract stays current instead of decaying into stale
      bootstrap prose.
- [ ] Prove the contract can detach from VoiceTerm early, before packaging:
      once startup authority, repo-pack selection, one report-only typed
      action, one blocking guard, one finding/evidence write, and one shared
      status/report render are working, run that thin slice on a rough second
      repo even if the UX is still ugly. Do not wait until the Phase 7 proof
      pack to discover hidden VoiceTerm assumptions.
- [ ] Prove that governed markdown authority is portable over different file
      names, doc roots, and report roots before calling the system repo-
      neutral: partial payloads must not silently invent `AGENTS.md`,
      `dev/active/INDEX.md`, `dev/active/MASTER_PLAN.md`, or `dev/reports/*`,
      and the first custom-layout fixture must use different authority names
      plus different report roots.
- [ ] Freeze the startup auto-boundary explicitly: startup may inspect repo
      state, refresh stale authority caches, resume exactly one valid or
      repairable `CollaborationSession`, auto-demote stale abandoned state,
      and emit one bounded intake/resume packet. Startup must not guess among
      multiple active plans, auto-launch conductor loops, or escalate into
      `active_dual_agent` without explicit operator/policy choice.
- [ ] Derive session/runtime permissions from the same repo-owned authority
      chain instead of from provider-local defaults: materialize one
      `DerivedCapabilityContract` from `ProjectGovernance`, current execution
      mode, reviewer gate state, and repo-pack policy; attach it to startup/
      session surfaces; and require wrappers/launchers to respect it before
      tool execution, worktree creation, remote access, publish, or subagent
      fanout occurs.
- [ ] Define the execution-mode matrix in one place: for
      `active_dual_agent`, `single_agent`, `tools_only`, `paused`, and
      `offline`, record allowed actions, required heartbeats, stale semantics,
      promotion behavior, and which clients/operators can drive each mode.
      Keep collaboration mode separate from objective profile so the same
      backend can run `bootstrap`, `audit`, `refactor`, `review`, or
      `remediation` work under either agent-assisted or script-first flows.
- [ ] Generate simple operator/AI startup surfaces from the same repo-pack
      policy: one shared backend, one routed check stack, thin
      `agents` / `developer` / `refactor` / `audit` wrappers, and
      provider-facing skills/hooks/docs that point at the same commands instead
      of inventing provider-local rules.
- [ ] Define an executable surface-ownership map on top of the layer model so
      routing/review posture/push semantics can distinguish
      `voiceterm_client`, `governance_engine`, and `integration` changes.
      The same map should feed boundary guards and a later Boundary IR instead
      of leaving path ownership as ambient directory lore.
- [x] Land the first repo-pack-owned VCS command-routing slice through the
      same policy chain: `repo_governance.push` now owns remote/default-branch/
      protected-branch rules plus preflight/post-push routing, `devctl push`
      consumes that policy as the canonical branch-push surface, and legacy
      `sync` / release helpers read the same repo-pack contract instead of
      hardcoded GitHub defaults.
- [ ] Converge AI-initiated and human-initiated VCS push paths through one
      canonical `devctl push` surface: `ralph_ai_fix.py` and autonomy-loop
      agents currently push with raw `git push`, bypassing
      `repo_governance.push` policy, preflight/post-push bundles,
      `TypedAction(action_id="vcs.push")` receipts, and governance-ledger
      events. Add `--caller` identity to push policy with per-caller
      preflight profiles, replace raw `git push` in Ralph/autonomy with
      `devctl push --execute`, carry push `ActionResult` in loop-packet
      checkpoint evidence, and record AI push events in the governance
      review ledger. This closes the split-brain where the governed push
      path (`devctl push`) and the ungoverned AI push path (`ralph_ai_fix`)
      apply different rulesets to the same VCS operation — violating
      scope-preservation rule #4.
- [ ] Make those user-facing wrappers repo-pack/policy configurable: alias
      names, default bundles, visible modes, and generated skills/slash
      surfaces should be editable by developers/adopters without patching the
      portable core or forking provider prompts.
- [ ] Add publish/release artifact governance to the same shared pipeline
      before broader release claims: `release` / `ship` must respect startup
      gating, publish a typed receipt, and validate built artifacts for
      forbidden contents and transitive references to internal infrastructure
      instead of trusting source-governance alone.
- [ ] Keep Codex/Claude startup parity explicit: generated instruction
      surfaces, bridge/runbook bootstrap, and routed validation commands must
      point both providers at the same repo-owned flow by default. Any
      remaining divergence must be adapter-owned, documented, and test-covered
      instead of living in chat habits or provider-specific memory.
- [ ] Prove execution-mode parity across `active_dual_agent`,
      `single_agent`, and `tools_only`: the same backend/runtime truth and
      routed check stack must power all three modes, with only
      reviewer-liveness/checkpoint behavior changing.
- [ ] Prove collaboration-mode parity explicitly: the same system must work
      for `Codex+Claude`, `human+Claude`, and `human+tools-only` operation,
      with one backend truth, the same routed checks, and the same
      operator-visible progress semantics instead of chat-only improvisation.
- [ ] Make Phase 7 proof compare collaboration modes on the same replayable
      corpus instead of treating multi-agent value as self-evident: the first
      benchmark/evaluation surface should compare `tools_only`,
      `single_agent`, `active_dual_agent`, and later swarm modes with
      adjudicated findings, severity mix, false-positive rate,
      time-to-disposition, repair-loop count, and quality-to-cost telemetry.
- [ ] Keep the first portability/value scoreboard intentionally small and hard
      to game: time-to-first-governed-run for a new repo, hard-guard blocked-
      change count, reviewed false-positive rate, quality/cost per successful
      fix, and a binary "second repo without core-engine patches" proof should
      all be visible before the platform claims portability or ROI.
- [ ] Define the extraction/back-import proof pack before the repo split:
      maintain a file-family classification (`platform`,
      `product_integrations.voiceterm`, `defer`), the standalone bootstrap
      commands, pilot-repo validation commands, and the VoiceTerm re-import
      diff/evidence checks needed to prove the extracted platform still drives
      the adopter the same way.
- [ ] Run periodic whole-system gap audits with multiple lanes: architecture
      boundary, instruction-surface parity, extraction manifest, and proof
      matrix. Record every still-missing contract here before calling a slice
      complete so the system does not silently drift between Codex, Claude,
      solo developer mode, and adopter surfaces.
- [ ] Define the validation-routing contract once instead of relying on chat
      habit: map backend actions and execution modes to the required routed
      checks (`check-router`, `tandem-validate`, `check --profile ci`,
      docs/probe/report lanes, risk add-ons) so Codex, Claude, and human
      developers all know what to run at the same boundary. The closure
      surface must answer "what runs next, why, and in which mode" in one
      canonical place instead of making operators infer between multiple
      overlapping validator entrypoints.
- [ ] Define the client capability matrix over the shared backend: CLI,
      review-channel conductors, PyQt6, overlay/TUI, phone/mobile, developer
      mode, and VoiceTerm adopter must each name what they can read, write,
      approve, launch, or only observe.
- [ ] Add one repo-owned operator-visible heartbeat/update stream over that
      same backend: reviewer/coder status, findings, next action, and
      stale/healthy state must publish automatically to shared projections so
      chat, CLI, PyQt6, phone/mobile, and overlay users do not need to keep
      asking whether the loop is still alive.
- [ ] Land the first concrete controller-owned lifecycle slice as
      `review-channel ensure/watch`: persistent reviewer heartbeat/update
      publishing, mode-aware liveness ownership, and one canonical structured
      state/projection path. Keep guards read-only and keep markdown as a
      projection/bootstrap surface instead of live authority.
- [ ] Freeze the collaboration timeout/escalation contract on that same
      controller path: define configurable reviewer-overdue, coder-wait,
      idle-session, and absolute-run budgets (for example `--timeout-minutes`
      / policy defaults), what transitions from `fresh` -> `poll_due` ->
      `overdue` -> `timed_out`, and which transitions only warn versus force
      pause/stop. The system must never leave an agent parked for hours with
      no controller-owned escalation.
- [ ] Freeze the stop/shutdown contract for collaborative runs: `pause`,
      `resume`, `stop`, timeout-driven stop, and completion-driven stop must
      all write final backend state, terminate controller-owned publishers and
      helper processes, and run the same repo-owned cleanup/verify path so the
      loop does not leave stale sessions or host processes behind.
- [ ] Define the caller authority + approval matrix over that same backend:
      human operator, solo developer, reviewer agent, implementer agent,
      automation loop, VoiceTerm shell, PyQt6, phone/mobile, and skills/hooks
      must each map to allowed actions, stage-only actions, approval-required
      actions, and forbidden actions under one policy contract.
- [ ] Freeze the operator-shell contract for VoiceTerm in executable terms:
      define which responsibilities belong to VoiceTerm as a first-party local
      shell, which remain backend-owned, and which current behaviors are still
      transitional bridge/adopter debt.
- [ ] Prove full action-surface parity for VoiceTerm as an adopter shell:
      VoiceTerm must be able to drive guards, probes, quality/reporting,
      bootstrap/export, review-channel actions, remediation loops, and
      generated skills/hooks/instruction flows through the same backend action
      router and validation path used by CLI/devctl.
- [ ] Prove VoiceTerm-optional operation explicitly: the same backend contract
      must be runnable through CLI/devctl, PyQt6, phone/mobile, skills/hooks,
      and external repos even when VoiceTerm is absent, while VoiceTerm remains
      the preferred first-party shell when present.
- [ ] Freeze the queue/action contract end-to-end: typed queue record shape,
      allowed sources (`WorkIntakePacket` / plan-targeted intake,
      `review packet`, operator action, automation loop), reducer/receipt
      semantics, how `terminal_packet` staging fits into the flow, and which
      actions are allowed to bypass the terminal entirely.
- [ ] Define the multi-client write-arbitration contract across the whole app:
      write ownership, idempotency, replay/nonces, lease or lock semantics,
      stale-writer recovery, and conflict rules must apply consistently across
      CLI, VoiceTerm, PyQt6, phone/mobile, services, and hooks rather than
      living only in review-channel-specific rules.
- [ ] Prove client parity for the queue/action path: VoiceTerm may be the best
      local shell, but CLI, PyQt6, phone/mobile, and future skills/hooks must
      still consume the same typed queue/action/backend contract without hidden
      VoiceTerm-only logic.
- [ ] Add version/compatibility handshake coverage for shared backend
      contracts: clients must negotiate schema/platform compatibility instead of
      silently assuming they are on the same commit or packet shape.
- [ ] Define the public-surface deprecation and compatibility contract: action
      ids, aliases, hook/skill surfaces, projection fields, and wrapper names
      need explicit support windows, migration paths, and guardable
      deprecation semantics instead of evolving through local convention only.
- [ ] Add parity and fault-injection proof for the operator system: stale
      heartbeat, dropped connection, crash mid-write, replay/reducer recovery,
      reconnect/resume, and writer-lease contention must be testable against
      the shared backend instead of only through manual operator sessions.
- [ ] Add golden projection/parity fixtures for the shared backend: one
      captured backend snapshot should drive equivalent critical fields,
      action availability, and provenance across CLI, VoiceTerm, PyQt6,
      phone/mobile, and generated skills/hooks surfaces.
- [ ] Keep every major subsystem on the same extraction map: CLI, review-
      channel, autonomy loops, PyQt6, overlay/TUI, phone/mobile, generated
      skills/hooks/docs, and VoiceTerm integration work must each name the
      shared backend contract they consume plus the remaining embedded
      assumptions still blocking portability.
- [ ] Define repo-pack packaging so repo-local policy/workflow/docs defaults
      live outside the portable core.
- [ ] Keep VoiceTerm working as the first consumer while replacing direct
      imports of repo-embedded platform logic with explicit integration seams.
- [ ] Treat separation as a live implementation constraint, not a late cleanup
      phase: when new loop/control-plane capability lands, move it behind
      reusable runtime/repo-pack seams first and let VoiceTerm call back into
      that seam, rather than widening the VoiceTerm-embedded architecture and
      promising to extract it later.
- [ ] Treat loop/control-plane slices as consumers of the full-platform
      boundary, not as the boundary itself: `MP-340`, `MP-355`, `MP-358`, and
      `MP-359` may harden their local path, but each meaningful slice must
      either remove a direct VoiceTerm-only dependency, move logic behind
      runtime/repo-pack/adapter contracts, or record the remaining debt here
      before the slice is considered complete.
- [ ] Remove the remaining direct `repo_packs.voiceterm` imports from
      portable/runtime/tooling layers and replace them with active repo-pack
      resolution or explicit adopter-layer wiring.
- [ ] Stop frontend clients from importing repo-internal `dev.scripts.devctl`
      modules or VoiceTerm path config directly; consume shared runtime/API
      contracts and emitted projections instead.
- [ ] Remove `bridge.md` as a required live runtime assumption in code
      paths that should already be reading typed `review_state` /
      `controller_state` authority, while keeping markdown available as an
      optional projection/bootstrap/debug mode where still useful.
- [ ] Define the markdown-authority demotion gate explicitly: list the typed
      `review_state` / `controller_state` / registry projections and client
      migrations that must exist before `bridge.md` becomes a
      backend-fed projection/bootstrap artifact instead of live authority.
- [ ] Define one simple backend-owned agent lifecycle command/action surface
      (for example `ensure/start/resume/stop` plus mode selection) that CLI,
      PyQt6, phone/mobile, overlay, VoiceTerm, and later skills/hooks all call
      instead of each client inventing its own launch logic.
- [ ] Define one unified agent/job/session/task registry over that same
      backend so review loops, autonomous loops, UI clients, services, and AI
      runs stop carrying separate local ideas of "the current work item".
- [ ] Define one typed tool/action/skill registry so backend actions, friendly
      wrappers, generated surfaces, and future slash/hook paths all resolve
      from the same catalog instead of from scattered docs and ad hoc prompts.
- [ ] Define one capability-discovery manifest over that same backend so
      wrappers, hooks, skills, UI clients, and repo adopters can query what
      actions, modes, approvals, projections, and transports are actually
      available instead of hard-coding assumptions.
- [ ] Freeze the local host/supervisor contract explicitly: VoiceTerm may host
      and supervise the shared daemon/controller stack as the preferred local
      shell, but that same stack must remain directly attachable by CLI,
      PyQt6, phone/mobile, and skills/hooks without hidden VoiceTerm-only
      orchestration.
- [ ] Freeze repo/worktree-scoped service identity and discovery for the shared
      backend so multi-repo or multi-worktree clients attach to the correct
      controller/daemon instance instead of whichever global socket or port is
      already listening.
- [ ] Freeze the backend attach/auth security contract before standardizing the
      shared daemon path across VoiceTerm, PyQt6, and phone/mobile: local-only
      vs off-LAN attach, auth tokens/keys, transport expectations, and
      approval boundaries must be explicit backend policy instead of client
      assumptions.
- [ ] Clear the blocking pre-spine hardening tranche before more startup-
      context or knowledge-layer work: (1) daemon attach/auth hardening
      including local-only defaults, explicit off-LAN opt-in, provider
      allowlists, token/origin validation, and restrictive socket
      permissions; (2) autonomy authority hardening so `swarm_run` /
      `autonomy-swarm` can only target typed active-plan authority and cannot
      mutate broad arbitrary docs through compatibility gaps; (3)
      JSONL/evidence integrity closure with single-write append contracts,
      consistent fail-closed parsing on canonical ledgers, and corruption
      detection; and (4) self-governance closure so governance-bundle/CI
      coverage proves the platform checks its own checking stack.
- [ ] Name and implement the daemon-event to runtime-state reducer explicitly:
      live daemon/session events must reduce into authoritative
      `ControlState`/`ReviewState` contracts instead of leaving daemon protocol
      and file-built projections as parallel truths.
- [ ] Make bridge-backed and event-backed review-channel producers emit one
      exact `ReviewState` contract and prove that parity with focused tests so
      PyQt6, phone/mobile, overlay, CLI, and later adopters stop converging
      through compatibility parsers as their primary integration path.
- [ ] Replace absolute-checkout-path review identity in review-channel state
      (`project_id` and related receipts) with one shared stable repo/worktree
      identity helper so controller/review/memory surfaces correlate across
      machines the same way durable finding identity now should.
- [ ] Replace the current false-green mobile protocol check with one real
      daemon/runtime parity lane: Rust daemon events/types, Python runtime
      models, and the Swift live WebSocket client must share one executable
      guard instead of only comparing Rust structs to bundle-only Swift models.
- [ ] Migrate phone/mobile and Operator Console surfaces to typed-state-first
      reads: `ControlState`, `ReviewState`, registry/runtime projections, and
      typed daemon state should become the primary contract, while
      `bridge.md`, `full.json`, `controller_payload`, and `review_payload`
      remain compatibility/debug fallbacks only.
- [ ] Add a repo-pack-aware maintenance/cleanup workflow surface for the whole
      system: managed plan/index/archive/generated-surface cleanup, stale
      bridge/runtime-state cleanup, and report/session residue cleanup should
      be callable through one guarded backend path without letting cleanup
      rewrite semantic review truth or delete repo state ad hoc.
- [ ] Retire VoiceTerm-local action brokerage as explicit migration debt:
      overlay/TUI action catalogs may remain a client shell, but typed action
      routing and argv mapping must converge onto the shared backend router so
      VoiceTerm does not keep a second orchestration brain.
- [ ] Push VoiceTerm-only env/log/process/product details down into
      `repo_packs.voiceterm` or `product_integrations.voiceterm` so shared
      tooling defaults stop carrying host-product naming and behavior.
- [ ] When a meaningful MP-377 slice turns green with validation, docs, and
      reviewer signoff, capture a bounded commit/push checkpoint through the
      normal approval path instead of letting the extraction lane accumulate an
      unreviewable dirty tree.
- [ ] Collapse the remaining peer architecture/doc duplication so this plan is
      the single active authority for the full-product governance architecture
      while durable guides become clearly subordinate/reference surfaces.
- [x] Normalize repo-pack policy/config so generated instruction surfaces can
      come from one canonical source without duplicate-key ambiguity.
- [ ] Define one canonical event-history model that keeps session continuity in
      active-plan markdown while unifying `devctl_events`, governance review
      rows, watchdog episodes, swarm summaries, and future `RunRecord`
      artifacts behind one runtime/artifact-store contract.
- [ ] Define one artifact taxonomy and ledger boundary contract for the whole
      app: state snapshots, append-only events, projections, receipts,
      repo-map artifacts, timelines, replay/benchmark evidence, and cleanup/
      retention classes should have one canonical classification instead of
      growing by subsystem.
- [ ] Define first-class context contracts (`ContextPack`,
      `ContextBudgetPolicy`) plus repo-pack-tunable budget tiers so AI loops
      stay bounded across bootstrap, full-scan, focused-fix, review, and
      remediation modes.
- [ ] Promote the recurring-defect closure rule into the platform contract:
      no important finding is complete until it is evaluated for architectural
      absorption. Every non-trivial issue should classify recurrence risk,
      choose an approved prevention surface (`guard`, `probe`, `contract`,
      `authority_rule`, `parity_check`, `regression_test`, `docs_only`, or
      explicit waiver/`none`), and verify both the local fix and the systemic
      prevention path. When review/audit/manual use finds a deterministic
      low-noise issue, the default follow-up is a reusable guard/probe/policy
      path; if the issue is repo-local only, record why it remains in
      repo-pack policy instead of promoting it into the portable engine.
- [ ] Freeze the evidence-to-memory bridge contract: findings, run records,
      repo-map snapshots, and other machine artifacts should be attachable by
      ref into context packs and later memory/query flows instead of copied
      ad hoc into prompts.
- [ ] Add a governance-self-hosting calibration pass before ratcheting more
      shape limits: the guard/probe stack must evaluate the governance engine
      itself and prefer lower coupling/cohesion cost over line-count-only
      micro-decomposition. If a limit or exception policy pushes the engine
      into more fragmented, less comprehensible code, recalibrate the rule
      rather than treating local line-count wins as architecture wins.
- [ ] Add a concrete governance-evidence bridge task: serialize findings,
      run records, and repo-intelligence snapshots into the Rust memory
      substrate so `startup-context`, `master-report`, and later memory/query
      surfaces consume one bounded packet rather than assembling evidence
      piecemeal from separate JSONL readers.
- [ ] Reuse the existing Rust memory substrate instead of inventing a second
      opaque AI-memory stack: `ContextPack`, `SurvivalIndex`, JSONL event
      storage, deterministic retrieval queries, and the staged SQLite schema
      should plug into startup/work-intake through exported receipts and
      attach-by-ref contracts, not through hidden prompt stuffing or direct
      VoiceTerm-only coupling.
- [ ] Freeze the public repo-understanding surface as a real backend contract:
      promote `devctl map` from a thin topology byproduct into a first-class
      machine-readable surface that combines topology, complexity, hotspots,
      changed scope, and guard/probe/review overlays with focusable output.
- [ ] Define one deterministic navigation artifact above that repo-understanding
      surface: a `ConceptIndex` / concept-graph snapshot derived from active
      plans, command taxonomy, contract rows, guard/probe registry, and repo-
      map state plus canonical pointer refs / typed anchors. It may later be
      serialized in a ZGraph-compatible form, but the authority must remain
      the generated contract/artifact snapshot, not a free-form semantic
      store.
- [ ] Freeze the terminology for that layer explicitly: in these plans,
      `ZGraph` means the internal generated concept-navigation/semantic-graph
      encoding built on canonical pointer refs and typed edges. It is not a
      product name and not a second authority store.
- [ ] Land the first native query surface on top of that backend: extend
      `devctl map` / repo-map generation with active-plan/doc/command nodes
      plus typed edges, emit a generated startup `HotIndex`, and expose a
      read-only `devctl context-graph` query surface whose results always
      resolve back to canonical pointer refs / typed anchors.
- [ ] Keep that first context-graph slice read-only and contract-light: no
      new durable artifact root, no `RepoMapSnapshot` row in
      `platform-contracts`, and no `ContextPack` emission until the query
      surface proves the bounded repo-context packet shape.
- [ ] After the first bounded context-escalation slice is checkpointed, widen
      the same packet shape only through the remaining repo-owned instruction
      builders (`review-channel` promotion/event projections and fresh
      `swarm_run` prompts). Do not jump straight to UI/chat/workflow-local
      injections while backend instruction emitters still start blind.
- [ ] Freeze the ZGraph boundary before implementation: any ZGraph-compatible
      encoding is generated-only, reversible through a typed symbol table, and
      anchored by provenance refs back to canonical plans/contracts/artifacts.
      It is a navigation/compression layer for `ConceptIndex` and bounded
      context retrieval, never an independent authority or lossy memory store.
- [ ] Freeze the full retrieval/control stack too: hard guards/probes are the
      cheapest deterministic classifier layer, `ConceptIndex` /
      ZGraph-compatible graph outputs reduce search space over canonical refs,
      `HotIndex` / `startup-context` / `ContextPack` reconstruct the minimum
      cited working slice for the current task, and reviewer/autonomy/Ralph
      AI loops stay the expensive fallback/controller layer only when the
      cheaper layers cannot decide or fix the issue safely.
- [ ] Freeze the boot/search order more explicitly before widening the graph
      lane: `session-resume` / typed continuity packets stay the first-hop
      bootstrap path for continuation work, deterministic changed-path/lane/
      policy narrowing stays second, and only then may `ConceptIndex` /
      ZGraph-compatible layers rank or compress the bounded candidate set.
      Semantic routing reduces search space; it does not become boot-time or
      control-plane authority.
- [ ] Add a graph-capability ladder instead of one flat “wire ZGraph
      everywhere” task: connected typed plan/doc/command edges first, then
      bounded transitive blast-radius queries, then test-to-code /
      test-selection edges, then agent-authored graph queries. Each step must
      stay reversible to canonical refs and pass the same honesty rules.
- [ ] Extend the generated discovery stack in bounded steps rather than
      treating it as one monolith:
      `SystemCatalog` becomes the static graph root for "what exists",
      `AgentDispatchPacket` becomes the bounded routing frontier for "what to
      inspect/run next", and optional ZGraph-compatible reducers only rank or
      compress that frontier. Do not let semantic routing duplicate runtime
      truth already owned by `StartupContext`, `ControlPlaneReadModel`, or
      packet/state contracts.
- [ ] Keep the first graph hierarchy coarse-to-fine in that same lane:
      lane/subsystem/contract/command/guard/projection/changed-path-trigger
      nodes first, then descend to file/symbol detail only after the bounded
      frontier is selected. Do not model or traverse the whole repo at
      full-fidelity graph depth on every startup or review turn.
- [ ] Add one evaluation gate before broader semantic-routing promotion:
      support at least `dispatch_mode=deterministic`,
      `dispatch_mode=deterministic_plus_semantic`, and
      `dispatch_mode=semantic_audit`; measure files opened before first
      correct touch, tokens spent before first useful action, missed
      authority/proof nodes, wrong guard/test bundle selection, and human
      override rate on representative repo tasks. Promote semantic routing
      only if it lowers search cost without increasing missed-authority
      regressions.
- [ ] Treat governed docstrings / semantic symbol blocks as graph-fed node
      features in that same lane, not as a separate planner. They may improve
      retrieval cues, semantic labeling, and local navigation, but the graph
      and its symbol registry remain subordinate to the owning typed
      contracts.
- [ ] Preserve the broader cross-domain graph backlog explicitly as later
      generated reducer work instead of letting it disappear behind the `P0`
      authority slice: workflow/CI DAG edges, git-history/change-intent edges,
      test-suite / fixture / coverage topology for smart test selection,
      compliance/drift audit views over governed docs such as `AGENTS.md`, AI
      observability / guard-challenge corpus generation, and memory decision /
      execution-trace nodes. Keep all of these generated-only and subordinate
      to the same canonical refs / typed contracts.
- [ ] Upgrade the current repo-local graph from a static discovery helper into
      a task-aware intake reducer in bounded steps. Start with command-graph
      closure (public command -> handler/source edges from dispatch
      authority), explicit honesty states (`low_confidence`, `no_edge`) in
      query output, and edge-validation that rejects orphaned semantic links or
      heuristic plan->concept edges whose target concept never materializes.
- [ ] Unify `INDEX.md` registry parsing behind one canonical helper instead of
      carrying three regex variants across doc-authority, context-graph, and
      review-channel plan resolution. Registry-shape changes should land once
      and fan out through shared parsing/tests, not through copy/pasted row
      matchers.
- [ ] Keep collapsing parallel authority readers once typed projections exist:
      after the shared `INDEX.md` helper lands, bootstrap/context-graph/
      startup/review surfaces should fan out through shared registry/review/
      policy readers (`INDEX.md`, `review_state.json`, quality-policy/script
      inventory) instead of growing new ad hoc parsers around the same
      canonical sources.
- [ ] Add a dedicated command-surface parity guard for `COMMAND_HANDLERS`
      versus `devctl list` / `COMMANDS`. Missing parser/handler/list drift is
      currently too silent; CI should fail if the public command inventory and
      dispatch authority diverge.
- [ ] Stop maintaining a separate context-graph "temperature" algorithm once
      the graph moves beyond the current bootstrap proof. Normalize the graph's
      source-file hotness from the shared hotspot / `priority_score` family so
      probe-report, topology packets, and context-graph are ranking the same
      repo risk through one explainable scoring contract.
- [ ] Fix topology-scan hygiene before relying on graph confidence: the shared
      source enumerator must exclude calibration/transient roots such as
      `dev/repo_example_temp/**` and `.claude/worktrees/**` so sample repos or
      detached worktrees never materialize as high-confidence live graph
      neighbors.
- [ ] Prefer fresh probe/topology artifacts over cold rescans in the next
      reducer step: `context-graph` / `startup-context` should read
      `dev/reports/probes/latest/file_topology.json` and `review_packet.json`
      for changed paths, hint counts, severity counts, connected files, and
      bounded next-slice guidance, with filesystem rescans only as the
      stale/missing fallback.
- [ ] Make query confidence honest before widening capability: direct typed
      matches and bounded word-aware query quality must outrank accidental
      substring/import adjacency, and sample-repo noise, generic guard-edge
      fan-out, or generic neighbor expansion must not surface as `high`
      confidence merely because many low-value edges exist.
- [ ] Replace substring-first query resolution with a bounded progressive
      filter stack in the first routing proof: exact/canonical ref matches
      first, trigger/concept expansion second, typed-relation walks third,
      bounded multi-hop inference fourth, and fail-closed fallback only after
      the cheaper layers reject or exhaust the scope.
- [ ] Land the first richer typed relation families before promising semantic
      routing: wire canonical `guards` / `scoped_by` coverage plus one
      operation-semantic producer/consumer contract family (`computes`,
      `exports`, `consumes`, and `transforms` where the repo-owned contract
      evidence is real) so the graph is anchored in repo-owned evidence
      instead of raw import adjacency alone. `scoped_by` coverage should come
      from plan-registry / ownership-backed mappings for active plans, not
      only docs-policy tooling prefixes.
- [ ] Promote the graph from escalation-only helper to the first bounded
      decision-routing input after those relation families land: make the
      builder emit real `EDGE_KIND_GUARDS` and `EDGE_KIND_SCOPED_BY` edges,
      land `EDGE_KIND_GUARDS` as the first quick win, and add the missing
      node families incrementally (`test`, `workflow`, `config`, `finding`,
      and `contract`) so the graph can widen beyond escalation packets into
      startup, autonomy, Ralph/remediation, guards/probes, and operator
      surfaces. The target is graph-backed answers to "what guards protect
      this file?", "what tests or workflows fire?", "what findings block
      this plan?", and "what contracts or scopes apply here?" through cited
      canonical refs instead of flat substring discovery alone. (evidence:
      `UNIVERSAL_SYSTEM_EVIDENCE.md` Part 43, Part 47)
- [ ] Add deterministic temporal graph snapshots on top of that same graph
      tranche instead of inventing a second analysis stack: save versioned
      context-graph snapshots at CI/check boundaries, diff successive
      snapshots, and surface trend/drift answers such as "is this subsystem
      getting more connected or cleaner over time?" by reusing the existing
      snapshot/delta patterns from data-science and quality-feedback rather
      than starting a parallel temporal-graph architecture. First slice now
      live: `context-graph --mode bootstrap` persists a typed versioned
      `ContextGraphSnapshot` artifact under `dev/reports/graph_snapshots/`,
      and `--save-snapshot` widens the same writer to other graph modes.
      Second slice now live too: `context-graph --mode diff --from ... --to
      ...` reloads saved snapshots into a typed `ContextGraphDelta`, reports
      added/removed/changed nodes and edges plus edge-kind/temperature
      changes, and summarizes rolling trend drift over the selected snapshot
      window. Remaining work is wider capture automation and richer drift
      interpretation, not basic diff/trend plumbing. (evidence:
      `UNIVERSAL_SYSTEM_EVIDENCE.md` Part 53)
- [ ] Land one bounded inference engine on top of those typed relations in the
      same first routing proof: allow 2-3 hop cited chains over canonical
      refs so `WorkIntakePacket` can route intent to the smallest defensible
      read set instead of returning flat match buckets.
- [ ] Replace the ad hoc keyword mapping with a real context-routing trigger
      table: file/path patterns -> required warm refs, plan domains, checks,
      and query hints. `_PLAN_CONCEPT_KEYWORDS` is only the first heuristic.
      The scheduler path should eventually route `dev/scripts/checks/**`,
      `review_channel/**`, `memory/**`, `app/ios/**`, etc. through explicit
      trigger rules instead of relying on substring matches alone.
- [ ] Keep bounded bootstrap as a hard design constraint even as startup gets
      smarter: the default startup packet should stay slim (roughly <=2K
      tokens) and lean on query-on-demand / warm-context retrieval instead of
      growing into another static doc dump.
- [ ] Keep the startup family singular during graph rollout too:
      `startup-context` is the canonical bounded startup packet, while
      `context-graph --mode bootstrap`, `HotIndex`, and later
      `system-picture` views stay generated reducers over the same cached
      authority rather than parallel bootstrap manifests.
- [ ] Promote the first `startup-context` / `WorkIntakePacket` proof from
      "another packet" to the deterministic context-router contract: given
      command intent/goal, changed scope, and a token budget, return a
      bounded cited read set plus targeted checks and fallback refs before
      agents widen into ad hoc file exploration. That proof is not complete
      until the packet is backed by staged filtering plus bounded inference,
      not just richer graph plumbing.
- [ ] Add the first typed `startup-context` / `WorkIntakePacket` command after
      those honesty fixes land. The packet should carry repo identity, command
      goal, active target refs, changed paths, changed symbols when available,
      suggested graph queries, canonical refs, targeted checks, writeback
      sinks, confidence, and fallback refs so the least-effort-first workflow
      is operational rather than prose-only.
- [ ] Pair that same first routing proof with a small bidirectional hot-query
      cache. Repeated lookups should hit a generated cache keyed by query +
      tree/work-scope state, and touched-path/tree-hash invalidation must keep
      the cache disposable and non-authoritative.
- [ ] Make the runtime-behind-docs baseline explicit in the same near-term
      order: kill implicit VoiceTerm-default runtime/path authority first,
      then close fail-closed startup/review truth, then land executable
      plan-mutation handlers behind `plan_patch_review` / `apply`, then clean
      `ActionResult` back to contract-level outcomes plus real `RunRecord`
      receipts, then collapse provider-shaped review fields into the future
      agent-registry middle layer. Do not count portability or control-plane
      closure as done while those five blockers remain open.
- [ ] Track the concrete false assumptions from that same audit as first-class
      closure items, not just commentary: `active_dual_agent` cannot stay a
      safe runtime default, bridge/projection fallback cannot stay a live
      authority path in startup/review recovery, `ActionResult` cannot keep
      business-state strings such as push lifecycle labels, and packet
      `apply` cannot imply executed plan mutation until repo-owned handlers
      write back typed receipts.
- [ ] Add one composed `devctl system-picture` read surface on top of the same
      authority stack so fresh AI/operator sessions do not have to reconstruct
      repo state from five or more separate commands manually. It should stitch
      together startup identity/state, active-plan status / progress
      percentages, runtime contract chain, doc health, guard/probe health,
      topology coverage, mutation-op coverage, and agent-readiness drift into
      one bounded generated view whose sections still cite canonical sources.
- [ ] Make `system-picture` a generated warm-start cache rather than another
      authority document: persist it under managed artifacts with `tree_hash`
      plus per-section hashes, recompute only stale sections on warm start, and
      keep the whole artifact disposable/rebuildable from canonical plans,
      guards, contracts, and graph outputs. If a section is stale or
      contradictory, the canonical command/guard wins and the section is
      recomputed or dropped.
- [ ] Make graph routing inputs live before calling it a scheduler: feed the
      current diff, recent findings, last failed checks, recently touched
      files, and current plan scope into graph temperature/ranking instead of
      rebuilding the same static discovery graph on every command invocation.
- [ ] Widen from file graph to work graph in the next ladder step: symbol
      nodes, explicit test nodes plus test-to-file/test-to-symbol edges,
      finding identity nodes, review-state / governance verdict / autonomy
      episode nodes, plan anchors/checklist rows, repo-pack policy plus
      platform-contract/service nodes, workflow/config edges, and Swift/iOS
      coverage after Python/Rust so this repo's mobile surfaces are not
      invisible to routing.
- [ ] Extend that same graph contract with workflow and config nodes/edges so
      AI and operator surfaces can answer “which CI workflows, guard paths, or
      config files affect this scope?” without separate prompt-local lookup.
- [ ] Feed repo temperature with more than static topology: add git churn,
      complexity, and recency inputs so hotspot ranking favors high-change,
      high-risk files without turning temperature into an opaque score.
- [ ] Add `check_semantic_links.py` after the graph/pointer contract lands so
      bidirectional plan/doc/command links, typed edges, and generated
      `HotIndex` refs cannot drift from canonical pointer/anchor authority.
- [ ] Keep richer graph queries fail-closed and explainable: weak coverage must
      surface explicit `low-confidence` / `no-edge` output and point back to
      canonical warm refs rather than pretending certainty from sparse graph
      matches.
- [ ] Treat generated concept-view / mermaid / dot outputs as first-class
      navigation/review surfaces for senior developers and AI prompts, but
      keep them generated-only from the same canonical graph/pointer contract
      rather than a second viewer-local semantic store.
- [ ] Add a first-class portable `architecture-review` command and matching
      `check --profile architecture` lane after the honesty/intake closure
      work lands. It should orchestrate graph build/query, aggregated
      probe-report data, architecture-relevant hard guards, and
      `platform-contracts` into one JSON-canonical health report with markdown
      projections rather than forcing manual multi-command synthesis.
- [ ] Add `check_system_coherence.py` as the self-governance companion to
      `system-picture` once the read surface is live. CI should fail when the
      platform's own composed picture drifts: required sections missing,
      mutation ops defined without handlers or explicit deferral, agent-id /
      role surfaces inconsistent across reducers/parsers/contracts, or accepted
      graph/command coverage baselines falling below the declared floor. This
      is the dogfooding guard for platform coherence, not a generic code-smell
      check.
- [ ] Add explainable architecture-query primitives to the graph layer for
      that review surface: SCC/cycle detection, fan-in/fan-out and god-module
      queries, dependency depth, transitive blast-radius / impact radius, and
      repo-policy-driven layer-violation queries. Reuse existing typed edges
      and canonical refs; do not hide decisions behind opaque ranking-only
      output.
- [ ] Add generated transformation-rule support on top of that same graph/query
      layer: model common fix families as advisory "if X changes, likely
      companion edits/tests/docs/configs are Y" rules so graph-backed packets
      can predict likely fix fallout before the expensive AI fallback loop
      runs. Keep the rules generated-only, tree-hash invalidated, and
      subordinate to guard/runtime truth.
- [ ] Add a typed `ArchitectureHealthScore` / review payload that aggregates
      coupling, complexity, consistency, layering, and overall health, with
      baseline/trend inputs coming from governance ledgers and portable
      episode/runtime metrics where available. Keep thresholds and weights
      repo-pack configurable.
- [ ] Extend the best-practice / review-packet layer beyond file-local smells
      so the same evidence can explain system-level issues such as dependency
      inversion, cycle breaking, god modules, layer isolation, and
      cohesion-vs-coupling tradeoffs.
- [ ] Add audience-aware rendering on top of that shared evidence record:
      agents get compact repair guidance, junior developers get explanatory
      context and bounded learning paths, senior reviewers get risk ranking +
      trend data, and operators get the same health view projected into
      controller/dashboard surfaces. Do this as projection logic over one
      canonical payload, not as parallel schemas.
- [ ] Activate the SQLite runtime in the Rust memory substrate as a `P0`
      prerequisite for the architectural knowledge base: the schema is already
      fully defined in `memory/schema.rs` (12 tables including `topics`,
      `event_topics`, FTS5 search, 6 query indexes), and the in-memory
      `MemoryIndex` already mirrors the public query interface. Runtime
      activation should swap the in-memory vectors for real SQLite read/write
      without changing the `recent()` / `by_topic()` / `by_task()` /
      `search_text()` query surface. Design the activation with topic-keyed
      knowledge storage in mind so the `P1` knowledge-base layer composes
      cleanly.
- [ ] Add auto-capture scripts that flag architecturally significant events for
      knowledge-base ingestion (`P1`, depends on SQLite activation and
      evidence-to-memory bridge): hook into guard-run, governance findings,
      plan milestone completions, contract changes, schema migrations, guard/
      probe registration changes, CI workflow structural changes, and repo-pack
      policy changes. Each captured event should carry topic key, structured
      summary, source file paths, schema/contract refs, timestamp, and
      staleness policy. The capture heuristics should be repo-pack-configurable
      so another repo can tune significance thresholds.
- [ ] Define topic-keyed knowledge chapters with per-chapter token budgets
      (`P1`): organize captured architectural knowledge into bounded chapters
      (e.g., `memory_system`, `governance_engine`, `platform_contracts`,
      `ci_orchestration`, `autonomy_loops`, `operator_surfaces`,
      `review_channel`, `naming_conventions`) each with a target token budget
      (1K-3K tokens). Export chapters as bounded JSON packets that plug into
      the existing `ContextPack` builders with token-cost metadata. Invalidate
      and regenerate chapters when the underlying source artifacts change
      (keyed by git diff, policy hash, contract version).
- [ ] Integrate the topic-keyed knowledge base with the `ConceptIndex` / ZGraph
      navigation artifact (`P1`): the concept graph should map topic
      dependencies so the retrieval system can pull related chapters
      transitively (e.g., querying `memory_retrieval` also pulls
      `token_budget` and `platform_contracts`) without loading unrelated
      chapters. This replaces sequential full-document loading with
      graph-traversal-based selective loading, directly reducing wasted tokens.
      Track token savings as a measurable metric (tokens retrieved vs tokens
      that would have been loaded under the old sequential model).
- [ ] Evaluate the compact-navigation path against the plain path before
      productizing it: baseline `startup-context` / topic-chapter retrieval,
      then `ConceptIndex` + optional ZGraph-compatible encoding, using the same
      tasks/model while measuring token count, latency, task success,
      citation-validity, and unsupported-claim rate. Compact mode must fail
      closed to the warm raw chapter path when symbols are stale or expansion
      is ambiguous.
- [ ] Add a measured context-injection evaluation path on top of that graph
      work: compare old bootstrap, bounded bootstrap, and bounded bootstrap +
      graph escalation on token cost, right-file selection, right-test
      selection, retry count, missed blast radius, and false-confidence rate.
- [ ] Add one repo-pack-aware startup/intake authority surface for AI and
      human operators: read the active plan registry/tracker, inspect current
      git status/diff, map the slice to command goals + MP scope, emit the
      right validation route, and declare the correct sinks for accepted
      findings/decisions (`plan markdown`, `governance-review`, command
      telemetry, generated surfaces). This must stay repo-neutral through
      `RepoPack` / `RepoPathConfig`, not through VoiceTerm-only hardcoding.
      The same intake packet should be able to attach convention-policy or
      convention-report context so AI startup guidance includes the repo's
      active naming/organization rules when they exist.
- [ ] Keep the startup family singular and typed: `startup-context`,
      `WorkIntakePacket`, `CollaborationSession`, and `ContextPack` should be
      projections of the same intake/authority chain. Do not add a parallel
      `bootstrap-context`, second startup manifest, or hand-maintained session
      summary that can drift from those canonical packets.
- [ ] Make that startup surface minimal enough to be practical: generate a
      task-scoped startup packet/surface that replaces the current huge manual
      bootstrap burden with one bounded summary of active plans, routed checks,
      relevant probes, convention context, and required write-backs.
- [ ] Define collaboration startup/resume over that same intake path instead
      of inventing a second dev-only loop selector: startup should either
      resume one valid `CollaborationSession` (same repo identity, live/repairable
      lease, unambiguous active target) or fail closed with an
      `ambiguous_scope` / `stale_session` decision packet. The bounded startup
      surface should expose role routing, writer ownership, current slice,
      restart packet, and ready gates for both single-agent and dual-agent
      operation.
- [ ] Back that startup/intake surface with cached repo-intelligence artifacts
      instead of full re-bootstrap on every session: define a refreshable
      `plan snapshot`, `command map`, `convention snapshot`, `RepoMapSnapshot`,
      filtered probe summary, and `TargetedCheckPlan` output under
      `ArtifactStore`, plus invalidation rules keyed by git diff, plan/policy
      hashes, and cache freshness. `startup-context` / work-intake should read
      those artifacts first and only rerun the affected scans when the cache is
      stale or missing.
- [ ] Extend that same cache-first startup path with a repo-pack-owned
      checkpoint/push packet, not a second memory authority: on checkpoint or
      governed push, emit one bounded packet into `ArtifactStore` carrying
      repo/worktree identity, tree hash or commit sha, touched paths + diff
      stats, routed plan scope, guard/check summary, reviewer verdict summary,
      checkpoint-budget snapshot, and invalidation metadata. `startup-context`
      may read that packet as a warm-start accelerator when fresh, but it must
      fall back to canonical git/plan/policy/guard sources when the packet is
      stale or absent. Keep the packet generated-only, hash-invalidated, and
      safe to delete/recompute so cache speed never becomes hidden authority.
      `context-graph` / `ConceptIndex` may compress or explain nearby scope for
      review, but checkpoint/push boundaries still ground in git diff + plan +
      guard/review truth and must fail closed by narrowing scope when graph
      confidence is weak.
- [ ] Keep that cache/query layer explainable and portable: canonical
      human-readable JSON artifacts first, append-only refresh-ledger rows
      second, optional SQLite query cache third. Do not make semantic/vector
      retrieval the only source of truth; treat it as an optional accelerator
      over the canonical artifacts once the deterministic snapshot contract is
      stable.
- [ ] Make the cross-repo session-start flow explicit on top of that cache
      layer: first run should seed canonical artifacts through
      `governance-bootstrap`, `check --adoption-scan` /
      `probe-report --adoption-scan`, and one bounded `context-graph` /
      `startup-context` packet; later sessions should refresh only the
      invalidated slices via content-hash + git diff, then emit the next warm
      start from cached artifacts + delta instead of re-deriving the whole
      repo.
- [ ] Add a portable continuation/checkpoint budget to that same startup flow:
      the repo-pack contract should declare when a dirty slice is still safe
      to keep editing versus when the agent must checkpoint before doing more
      work. Expose dirty/untracked counts, threshold values,
      `safe_to_continue_editing`, `checkpoint_required`, and checkpoint reason
      in the startup/intake packet so agents stop relying on prompt-local
      judgment about when to commit/push.
- [ ] Keep a non-Rust fallback first-class for that same flow: until the
      SQLite runtime is active, canonical JSON snapshots plus refresh-ledger
      rows under `dev/reports/**` must remain sufficient for warm-start
      portability on adopting repos.
- [ ] Add one cached aggregate evidence surface (`master-report`) over the
      stable artifact families: guard results, probe findings, governance
      ledger stats, repo-map/topology state, targeted-check hints, convention
      snapshot, cross-language parity summaries, and governance-completeness
      evidence should compose into one machine-readable report so AI and humans
      read measurements instead of cold-reading the repo every session. The
      report must be able to surface meta-findings such as guard/probe test
      coverage, CI invocation coverage, exception-list completeness, workflow
      timeout coverage, JSONL/evidence-integrity gaps, and config-vs-code drift
      when the governance layer is itself incomplete.
- [ ] Close the first feedback-loop tranche on top of those same canonical
      evidence surfaces: auto-persist adjudicable guard/probe outcomes into the
      governance ledgers, unify finding identity generation across guard /
      probe / import paths, feed `code_shape`, duplication, and
      `time_to_green` into one measured quality surface, and project that
      quality summary into bounded startup/operator views instead of chat-only
      bridge prose. Owner/phase: `MP-377` evidence/feedback closure before
      wider `P1` UX. (audit mapping: `SYSTEM_AUDIT.md` A1, A2, A3, A4)
- [ ] Route the fresh operational evidence already produced under
      `dev/reports/**` and adjacent governance/runtime artifacts into the
      first live decision surfaces on top of that same feedback-loop tranche:
      `review_packet.json`, governance summaries / `finding_reviews.jsonl`,
      watchdog episodes, data-science summaries, orchestrate state,
      `DecisionPacket` metadata, quality-feedback recommendations, research
      benchmark bundles, audit-event history, review-channel traces, and
      Ralph guardrail reports should influence bootstrap, conductor, swarm,
      Ralph, loop-packet, escalation, and other runtime decision points
      instead of remaining write-only or display-only data. Sequence this
      behind the authority spine by consuming the existing versioned artifacts
      rather than inventing new side channels. Immediate zero-consumer
      backlog to close here: `finding_reviews.jsonl`, watchdog episodes,
      quality-feedback snapshots/recommendations, data-science summaries, and
      decision/adoption metadata are still largely absent from live prompt
      builders even after the first `ai_instruction` routes landed. Partial
      closure is now real: shared context packets inject bounded recent
      `finding_reviews` fix history plus latest quality-feedback
      recommendations into Ralph/autonomy/review-channel/conductor/swarm
      prompt families; shared escalation/context packets now also carry
      bounded watchdog episode digests plus command-reliability lines from
      the existing data-science summary artifact; matched probe guidance now
      carries the first live `DecisionPacket` behavior gate
      (`decision_mode`) into Ralph, autonomy, `guard-run`, and the shared
      escalation packet instead of leaving it display-only; and bootstrap
      surfaces now explicitly tell agents to escalate from the slim bootstrap
      packet to typed `startup-context` when reviewer/checkpoint truth or
      richer continuity is needed. The next closure here is impact
      measurement plus the remaining broader operational artifacts rather
      than another prompt-only wire. (evidence:
      `UNIVERSAL_SYSTEM_EVIDENCE.md` Part 42, Part 45, Part 54)
- [ ] Version the remaining artifact families before promoting that aggregate
      surface as canonical: governance-ledger summaries, autonomy episodes,
      `devctl` event history, data-science summaries, and any new convention /
      convergence artifacts need explicit `schema_version` + `contract_id`
      fields plus a closure guard proving coverage.
- [ ] Add one measured convergence surface (`converge`) only after
      `master-report` is stable: iterate `master-report -> fix -> remeasure`,
      track deltas per iteration, stop at fixed point / policy limit, and
      record the convergence log as machine-readable evidence rather than as
      chat-only narration. That loop should include governance-quality
      convergence, not only product-code convergence, so the platform can
      prove that its own guard/test/CI/exception mesh is complete enough to be
      trusted.
- [ ] Define the naming contract as two portable layers: canonical backend
      command/action ids plus repo-pack-owned friendly aliases/wrappers for
      docs, skills, slash commands, VoiceTerm, PyQt6, and beginner-facing
      UX, with one guard-backed mapping between them. Widen the existing
      `check_naming_consistency.py` / naming-policy path first; do not treat
      naming governance as a greenfield subsystem when a portable naming guard
      already exists.
- [ ] Define the next coherence-enforcement layer over that naming contract:
      add repo-policy-backed, cross-file naming/organization checks for
      function/class/field vocabulary drift, contract-field consistency,
      import-pattern consistency, and file-structure template conformance.
      These rules should stay portable, explainable, and policy-owned rather
      than VoiceTerm-hardcoded; start as advisory probes where calibration is
      unknown, then promote to guards only after adjudication evidence says the
      signal is accurate enough.
- [ ] Prove that coherence layer on a small reference repo before broadening
      claims: use a compact Python-first repo with intentional naming,
      organization, and contract-drift mistakes, then measure before/after
      findings, adjudication coverage, fix rate, false-positive rate, and
      cleanup rate so "better coherence" is shown rather than assumed.
- [ ] Add context-usage telemetry to `RunRecord`/event history/adoption
      evidence: estimated prompt size, actual provider usage when available,
      compression ratio, and explicit overflow/truncation path.
- [ ] Separate local/offline validation posture from live external status
      gates so tandem validation can distinguish code-quality failures from
      GitHub/network/home-dir environment failures without weakening CI or
      release enforcement.
- [ ] Make "why didn't the tools catch this?" a first-class execution rule:
      for each externally found issue or audit finding, record the enforcement
      miss, decide whether it belongs to an existing guard/probe/runtime
      contract or a new rule family, and keep that follow-up in repo-visible
      plan state before closure. Require one explicit closure read on the
      touched slice too: rerun the relevant direct probes / `probe-report`,
      then classify the miss as no-rule, too-narrow detection, or advisory-
      only severity before the issue can be called closed.
- [ ] Add the self-hosting enforcement tranche for platform-boundary blind
      spots: layer boundaries, portable path construction, provider/workflow
      adapter routing, contract completion, schema/platform compatibility, and
      the first repeatable command-source/shell-execution checks. Include a
      meta-governance guard path that can prove whether the rule engine itself
      is complete: guard/probe tests exist, CI runs the registered guards,
      exception registries are complete, timeouts/coverage gaps are surfaced as
      evidence instead of being assumed away, and the next missing hard-guard
      tranche (unused imports, hardcoded secrets, dead code, dual-authority
      artifact consumers, prose-parsed structured contracts, responsibility-
      count / mixed-concern calibration for tactical AI modules, and similar
      deterministic wins) lands through reusable rule families instead of
      audit-only prose. The recent Ralph guidance slice is the calibration
      case: the dual-authority fallback was fixed in code, but the checker
      stack still lacks deterministic coverage for dual-authority consumers
      and the current string-contract probes stay quiet on prose-parsed
      structured matching seams. (audit mapping: `SYSTEM_AUDIT.md` A27)
- [ ] Expand the watchdog and audit evidence beyond today's narrow slices:
      run repeated full-worktree `--adoption-scan` cycles, widen guarded-coding
      episode coverage, and baseline more guard/probe families so platform
      accuracy claims are backed by codebase-wide evidence instead of a small
      reviewed subset.
- [ ] Treat false positives as rule-quality bugs: for every recorded
      `false_positive`, capture the root cause and either narrow the rule,
      add context, demote severity, move it behind repo-pack policy, or
      explicitly justify why it remains advisory.
- [ ] Add adjudication-coverage metrics: reviewed-vs-unreviewed findings by
      guard/probe family, scan mode, repo, and time window so the repo can
      distinguish "good outcomes on a small sample" from broad signal quality.
      Make `false_positive_rate_pct` read alongside coverage and disposition
      mix so the ledger cannot flatter a small or biased sample.
- [ ] Close the guard-intelligence feedback loop through the existing typed
      evidence stack instead of rewriting individual hard guards: the
      projection layer in `governance/guard_findings.py` and
      `runtime/guard_finding_contracts.py` should become the canonical
      upgrade seam that decorates legacy guard violations with richer
      `Finding`-family metadata derived from signals already in scope rather
      than asking every `check_*.py` script to grow bespoke policy logic.
- [ ] Land a bounded "decoration first" tranche for those guard findings:
      emit or derive `finding_class`, scoped severity, repair guidance,
      `decision_mode`, and `research_instruction` where deterministic policy
      already exists, but keep this first tranche zero-behavior-change for
      merge blocking. The goal is richer typed emission and downstream review
      routing before any adaptive enforcement claims.
- [ ] Add one repo-owned `GuardFeedbackLens` over existing
      `governance-review` history plus quality-feedback snapshots: given a
      bounded key such as `(check_id, file_path, risk_type)`, return recent
      verdicts, false-positive rate, fixed/confirmed counts, recurrence
      posture, and available precedent refs so the next guard/projection run
      can react to adjudicated history without inventing a second evidence
      store.
- [ ] Feed runtime context into that same guard-projection seam before
      widening trust: consume active-slice ownership
      (`WorkIntakeOwnershipState.scope_paths`), task-router risk tier,
      `ContextGraphSnapshot` or `ContextGraphDelta` churn/stability signals,
      and relevant reviewer/runtime visibility so guards can suppress
      obviously outside-scope noise, stay milder on high-churn in-flight
      regions, and become stricter on stable high-risk surfaces.
- [ ] Make the rollout ladder explicit and enforced by policy: decoration-only
      emission first, then advisory/adaptive severity or routing, then
      approval-bound learning behavior, and only then merge-blocking
      promotions after replay/corpus evidence proves low false-positive
      behavior. Adaptive guard intelligence must never silently become
      blocking because one branch looked good locally.
- [ ] Add one typed recommender path for rule promotion and escalation instead
      of hand-maintained folklore: probe-to-guard promotion, repeated-issue
      severity escalation, and similar "this should probably harden" signals
      should be generated from adjudication history and quality-feedback
      evidence, written as typed recommendations/manifests, and require
      operator approval before they affect the blocking guard set.
- [ ] Finish the AI-guidance side of guard intelligence after the feedback
      lens exists: allow render-time or packet-time `ai_instruction`
      synthesis for under-specified guard families using canonical finding
      evidence, nearby adjudication history, and cached fallback behavior,
      but keep that guidance portable, deterministic-by-default, and feature-
      flagged so provider availability never becomes a hard dependency of
      `check --profile ci`.
- [ ] Keep embeddings retrieval, interactive editor/provider hooks, and MCP
      surfaces as later optional layers on top of the same evidence spine, not
      prerequisites for the first closed loop. If those surfaces land, they
      must live behind feature flags in the portable platform layer and read
      canonical finding / review / graph contracts rather than sidecar stores.
- [ ] Define the repo-map storage/cache contract before DB sprawl: canonical
      JSON snapshot, append-only refresh ledger, optional SQLite query index,
      repo-pack-owned retention rules, and explicit attach-by-ref flow into
      `ContextPack` / AI runtime without making VoiceTerm memory the only
      authority.
- [ ] Freeze the legacy-payload retirement rule so transitional adapters do
      not become permanent authority: `controller_payload`,
      `review_payload`, bridge-liveness overlays, and similar raw compatibility
      shapes may exist only as edge adapters once typed state exists; no new
      primary consumer may depend on them, and removal is gated by cross-client
      parity coverage instead of by local convenience.
- [ ] Add the missing cross-language/runtime contract guard on the daemon state
      seam: the repo already guards Rust↔Swift mobile relay compatibility, but
      it still lacks an executable Rust daemon ↔ Python runtime-model parity
      check so semantic drift (`label` vs `display_name` style mismatches)
      does not remain hand-reviewed only.
- [ ] Define the product-operability layer explicitly: packaging/install/update,
      multi-repo/worktree safety, operator-visible health/timeline surfaces,
      and replay/recovery checkpoints should be first-class product contracts,
      not later polish.
- [ ] Define the degraded-mode and failure-domain matrix explicitly: provider
      unavailable, backend stale, incompatible client, missing host shell,
      offline repo, partial progress, and retryable vs non-retryable failures
      should project consistently across CLI, services, UI clients, hooks, and
      AI wrappers.
- [ ] Define the database-ingestion/provenance contract before adding a DB:
      canonical IDs, schema-version migration rules, JSONL-to-DB mapping,
      repo-pack/policy version stamping, and backfill strategy.
- [ ] Define privacy/redaction rules for structured telemetry before expanding
      the event store or ML corpus: which fields can be persisted verbatim,
      which must be redacted/hashed, and which artifacts need shorter
      retention.
- [ ] Define a measured promotion rubric for guard tiers so advisory probes only
      become blocking guards when sample size, false-positive rate, cleanup
      rate, and adoption-scan stability justify it.
- [ ] Ship budget-aware usage guidance so adopters know when to use full-repo
      scans versus focused slices, what the expected context bands are, and
      when the platform will summarize, split, or refuse oversized runs.
- [ ] Freeze the platform boundary with executable import/layer contracts so
      `governance_core`, `governance_runtime`, `governance_adapters`,
      `governance_frontends`, `repo_packs`, and VoiceTerm-specific integrations
      cannot silently bleed back together during extraction.
- [ ] Define one versioned finding/evidence schema at the center of the
      platform: `rule_id`, `rule_version`, category/language/severity/
      confidence, file/span, evidence, rationale, suggested fix, autofixable
      flag, suppression policy, and artifact refs, with every agent/reviewer/
      markdown projection derived from that same base record.
- [ ] Define one canonical identity contract for the whole app: repo/worktree,
      run, task, action, agent, job, session, artifact, and finding IDs should
      have stable ownership and mapping rules so ledgers, services, UI, and AI
      packets can refer to the same thing without ad hoc joins.
- [ ] Finish the machine-receipt contract for JSON-canonical surfaces so
      stdout becomes a stable control channel rather than prose status output:
      compact receipts should include artifact path/hash/bytes/token estimates,
      content type, and command/rule-family metadata.
- [ ] Extend artifact-cost telemetry from the current machine-output helpers
      into a first-class platform metric surface: rereads avoided by hash,
      bytes per accepted fix, token cost per false positive, token cost per
      no-op cycle, and other context-efficiency measures visible to operators.
- [ ] Freeze the artifact-backed retrieval contract for machine-first runs:
      the full JSON artifact stays on disk, stdout carries only a compact
      control receipt, and runtime retrieval opens the full artifact only when
      the hash changes or deeper detail is actually needed. The near-term
      storage target remains JSONL plus an optional SQLite catalog keyed by
      artifact path/hash/bytes/token estimate, run/task/git refs, and summary
      pointers rather than a mandatory database-backed runtime.
- [ ] Migrate guard, probe, import, and adjudication evidence families onto
      the canonical `Finding` contract: keep legacy shapes only as temporary
      translation seams, then add coverage proving the same finding record can
      flow through ledgers, review packets, reports, and UI projections. No
      review/fix/decision packet should emit from raw hints once this closes:
      every packet must carry stable finding identity, rule version, span, and
      evidence/artifact provenance through that shared record.
- [ ] Close the live Q55 findings split with one canonical backlog reader.
      Add a repo-owned `FindingBacklog` snapshot/loader over canonical
      finding rows so `review-channel --action post --kind finding`,
      `findings-priority`, dashboard/startup/monitor, and `bridge.md` all
      consume the exact same typed finding list. Preserve `LIVE_RUN.md` only
      as a compatibility import/projection, and keep `governance-review` as
      the adjudication/close-out sink over stable `finding_id` / human
      `Q-ID` identity rather than a parallel intake ledger.
- [ ] Freeze one deterministic runtime layer before widening autonomy
      surfaces. `StartupContext`, `ControlPlaneReadModel`, packet backlog,
      blocker/next-action reducers, and governed mutation gates must converge
      on one read-side truth or outer `GovernanceSnapshot`, while
      dashboard/status/startup/system-picture/chat projections render that
      state instead of recomputing authority from raw files or bridge prose.
- [ ] Freeze one shared packet/event lifecycle for all AI lanes:
      posted -> delivered -> observed/acked/applied -> execution receipt ->
      resolved/expired. Dashboard, monitor, phone/mobile, and agent loops
      should subscribe to that event-backed wake path instead of keeping
      independent timer polling or inbox-only heuristics.
- [ ] Land `devctl develop` only as a composition surface over that runtime
      layer and only after Phase 0 visibility closure is green. The command
      should load startup authority, plan state, `FindingBacklog` /
      `findings-priority`, packet lifecycle, and governed commit/push state,
      compute the next bounded action from typed state, and wake from state
      change rather than timer polling or prompt-local mode switches.
- [ ] Finish the typed-runtime structural-debt tranche before widening `P1`:
      remove duplicate authority-state models such as the parallel
      `ReviewBridgeState`, replace ad hoc `*_from_dict` loaders with one
      governed deserialization seam, and delete surviving `globals()` / dead-
      code / stringly routing shortcuts that bypass the platform contracts the
      runtime already claims to own. Owner/phase: `MP-377` `P0`
      runtime-contract cleanup before broader adopter-facing packaging. (audit
      mapping: `SYSTEM_AUDIT.md` A13, A16, A17)
- [ ] Define one typed `ActionResult` and error contract for the whole app:
      command handlers, service endpoints, wrappers, and clients should return
      the same success/failure envelope with reason codes, retryability,
      partial-progress semantics, operator guidance, and artifact refs. This
      is the canonical replacement for ad hoc `OutputEnvelope` proposals, not
      a second output-contract family. (audit mapping: `SYSTEM_AUDIT.md` A19)
- [ ] Land a first shared crash/error envelope on top of that contract:
      `devctl` CLI dispatch, `check`, and `autonomy-loop` must translate
      uncaught exceptions into structured machine-output / `ActionResult`
      failures with consistent exit codes instead of raw Python tracebacks.
      First concrete closure sites are the top-level `cli.py` `main()` path
      and the outer `autonomy_loop.py` execution wrapper; after that, fan the
      same helper out across the remaining command families.
      (evidence: `UNIVERSAL_SYSTEM_EVIDENCE.md` Part 36)
- [ ] Define one `CommandGoalTaxonomy` over the canonical action inventory and
      drive grouped discovery from it: `devctl list`, startup surfaces,
      wrappers, skills, future `map` hints, and validation-routing surfaces
      should all group by the same user goals instead of maintaining separate
      hand-curated command sets. `surface_generation` must derive workflow
      semantics from this structured action metadata rather than from freeform
      repo-policy prose blocks alone. The same contract should collapse the
      public/adopter-facing command surface toward a small goal-aligned `gov`
      family instead of another ever-growing flat command list. (audit
      mapping: `SYSTEM_AUDIT.md` A18)
- [ ] Turn the current report-only governance-routing fields into live runtime
      inputs: `ProjectGovernance.startup_order`,
      `command_routing_defaults`, and `workflow_profiles` must drive startup /
      command / workflow routing instead of stopping at draft/render output,
      and docs-governance should keep `DocRegistry` consumer/managed metadata
      aligned with the runtime filters that claim to use them. (evidence:
      `UNIVERSAL_SYSTEM_EVIDENCE.md` Part 38)
- [ ] Define one typed AI decision-routing contract over findings and design
      debt: the platform should distinguish at least `repairable`,
      `decision_candidate`, `approval_required`, and `informational`, with
      explicit auto-apply/recommend/explain-and-wait semantics so ordinary AI
      users do not have to infer architecture choices from raw probe output.
      Stable routing must support multiple findings on the same symbol without
      collapsing them into one implicit decision state.
- [ ] Finish closing the AI-guidance routing gap instead of inventing more
      packet shapes: Ralph now consumes exact file-matched
      `Finding.ai_instruction` from canonical `review_targets.json` probe
      artifacts, and autonomy `triage-loop` / `loop-packet` now consumes the
      same canonical guidance from a bounded structured backlog slice, while
      review-channel / conductor prompt surfaces, swarm `derive_prompt`, and
      escalation packets now inherit the same contract through shared
      context-packet rendering plus projected `guidance_refs`; `guard-run`
      follow-up packets now carry that same probe-guidance contract too, and
      `check_platform_contract_closure.py` now proves the first declared
      `Finding.ai_instruction` consumer family (Ralph, autonomy, and
      `guard-run`) plus a family-completeness failure if any declared route
      drops out. The first carried decision semantic is now live too:
      matched probe guidance merges `DecisionPacket.decision_mode` from the
      existing probe-summary artifact, Ralph/autonomy/`guard-run` treat
      `approval_required` as a real behavior gate instead of report-only
      text, and the deterministic route-closure guard now proves that first
      `DecisionPacket.decision_mode` family as well. The remaining gap is the
      rest of carried decision semantics (`invariants`, `validation_plan`,
      `precedent`, `research_instruction`, `signals`) instead of rendering
      them only for humans. Widen that same enforcement pattern beyond these
      first two families before claiming the rest of the contract is live,
      and fail the same tranche if an AI consumer negotiates between
      multiple artifact authorities or keeps deriving routing keys from prose
      once the structured contract fields exist. The current branch now
      proves transport plus basic
      mandate/telemetry scaffolding and one family-level meta-guard, not full
      impact, so this same tranche still owns three explicit follow-ups:
      prompts and packets must keep telling AI to treat attached probe
      guidance as the default repair plan unless waived with reason, matching
      must prefer structured file/symbol/span identity with prose parsing
      kept only as a compatibility fallback, and the runtime must log stable
      `guidance_id` / `guidance_followed` plus fix outcome so the repo can
      measure whether guidance improves post-fix guard results instead of
      assuming impact from transport alone. (evidence:
      `UNIVERSAL_SYSTEM_EVIDENCE.md` Part 27, Part 38, Part 52, Part 54)
- [ ] Add deterministic validation contracts as a first-class AI trust
      boundary instead of treating generic green test suites as sufficient
      confidence: model a portable contract-test family over runner-specific
      adapters, with a pytest-first adapter in this repo but no universal
      pytest assumption in the core contract. Project failing cases into
      canonical `Finding` records, make `DecisionPacket.validation_plan`
      executable as typed validator refs before and after mutations, and
      allow `decision_mode` upgrades only when the exact routed validation
      plan for that finding passes. Passing validators may widen weaker
      modes, but must never override an explicit human `approval_required`.
      Coverage, blast radius, and change scope may weight trust, but they do
      not replace finding-scoped validator proof as the autonomy gate. Keep
      advisory test-quality probes distinct from blocking contract-test
      guards, and keep selectors/thresholds repo-policy-owned rather than
      hardcoded repo-wide coverage rules.
- [ ] Treat deterministic validation as one evidence family rather than the
      whole governance story: failing contract-test / validation-runner cases
      should normalize into canonical `Finding` rows with a distinct
      validation/test-failure signal family, passing validators count as one
      trust input only, and guard/probe/contract/invariant evidence should
      converge in `DecisionTrace` instead of becoming competing autonomy
      lanes.
- [ ] Track the infrastructure prerequisites for that validation/explanation
      lane explicitly instead of assuming the headline artifacts can stand on
      their own: burn down direct `REPO_ROOT` imports through injected
      repo-root/repo-pack dependencies, extract git/filesystem adapters and
      repository-style loaders, replace governance-ledger `dict[str, Any]`
      rows with typed contracts, add a bounded `GovernanceFinding` aggregate
      over finding/decision/review lifecycle state, and remove inner-runtime
      subprocess/git lookups from the first touched runtime helpers.
- [ ] Make `validation_plan` and contract testing concrete, not aspirational:
      execute `DecisionPacket.validation_plan` on the first repair/apply lane,
      normalize failure cases into canonical findings through a dedicated
      failure adapter, register strict pytest contract/guard markers, and add
      focused contract-test coverage for task-router, push-policy,
      startup-context shape, and the first validation/failure adapter path.
- [ ] Freeze the first explanation/contract boundary shapes in the same lane:
      use closed-vocabulary status/wait-reason enums for `DecisionTrace`, add
      strict boundary-validation models plus JSON Schema emission for
      `StartupReceipt`, `DecisionTrace`, and `FailurePacket`, and keep those
      models parse-time only so the internal runtime remains on frozen
      dataclasses.
- [ ] Compile governed plan truth into a typed `PlanExpectationPacket` before
      AI/runtime reconciliation: the selected `PlanTargetRef` /
      `WorkIntakePacket` input should yield invariants, required artifacts,
      forbidden states, validation commands, evidence queries, and success
      criteria that runtime can compare against observed receipts, tests, and
      findings. Mismatch outcomes should surface as plan drift,
      implementation drift, contract drift, or missing-validation findings.
      Observed behavior must never auto-rewrite plan truth without a governed
      decision.
- [ ] Split the default fix packet from the typed decision packet: the
      everyday AI/dev surface should carry deterministic fixes, scoped
      evidence, the next routed checks, and the preferred validator in a
      first-class `FixPacket`, while higher-order design choices carry
      predeclared options, invariants, precedent, rationale fields, and the
      validation plan needed for either AI or human decision-makers in a
      `DecisionPacket`. `governance-review` should become the canonical
      close-out sink for both packet families.
- [ ] Make `governance-review` a runtime close-out sink, not a manual-only
      CLI: guard-run, autonomy-loop, review-channel closeout, and later
      packet apply/result handlers must auto-record
      `fixed|deferred|waived|false_positive` outcomes with stable finding ids,
      while `governance-review --record` remains the manual override path.
      (evidence: `UNIVERSAL_SYSTEM_EVIDENCE.md` Part 39)
- [ ] Add one governance-closeout/self-governance guard over that same sink:
      fail when adjudicable guard/probe/runtime paths bypass
      `governance-review`, when `governance_closure` or adjacent parity checks
      are registered without bundle/CI ownership or typed exemption, or when
      the checking stack can emit findings without durable ledger linkage.
      Owner/phase: `MP-377` `P0` self-governance closure alongside the blocker
      tranche. (audit mapping: `SYSTEM_AUDIT.md` A29, G1)
- [ ] Extend governance closeout itself before the next self-governance guard
      tranche goes blocking: `FindingReview` rows for `missing_guard` /
      `missing_probe` must carry explicit follow-up refs (proposed guard/probe,
      owning MP, or waiver), and runtime/governance paths must share one
      stable `finding_id` contract so closure checks compare like-for-like
      identities instead of similar-looking rows.
- [x] Add the first guard/probe promotion queue behind that closeout path:
      `governance-review --record` rows with `prevention_surface=guard|probe`
      now create repo-pack-resolved `GuardPromotionCandidate` JSONL rows and
      include candidate id/path metadata in the refreshed JSON summary for the
      recorded row, so follow-up guard/probe design does not rely on chat
      memory or audit prose.
- [ ] Add one self-improvement guard tranche over platform completeness, not
      just code shape: fail when `missing_guard` / `missing_probe` findings
      have no follow-up, when authoritative/live contract rows have no
      declared producer or consumer, when declared machine-readable runtime
      surfaces have no proven consumer route, or when finding ids never reach
      a terminal verdict. Narrow the contract/loop guards to authoritative or
      `live` families so placeholder rows and human-only outputs do not become
      bookkeeping noise.
- [ ] Make startup quality-signal loading repo-pack-aware and fail-closed:
      `startup_signals`, `startup-context`, and bootstrap `context-graph`
      must resolve `probe-report`, `governance-review`,
      `governance-quality-feedback`, and data-science summaries from declared
      `ProjectGovernance.artifact_roots` rather than hardcoded path guesses,
      and focused regression tests must prove every advertised startup signal
      family is actually loadable from those emitted roots.
- [ ] Keep startup/work-intake preflight routing coherent across the same
      inputs: when `startup-context` selects
      `selected_workflow_profile` and emits a `check-router --since-ref ...`
      preflight, the routed bundle must be derived from the same
      dirty-worktree / committed-diff policy the packet used, not tell AI to
      run a docs-only preflight while live tooling changes still drive
      `bundle.tooling`.
- [ ] Add lifecycle status metadata to contract-catalog rows (`live`,
      `scaffold`, `planned`, `compat`) before consumer-parity goes hard red,
      and keep placeholder adapter/runtime rows explicit until a first live
      route exists.
- [ ] Add schema-version coverage for every durable machine artifact family:
      command receipts, event ledgers, findings, review packets, watchdog
      episodes, analytics snapshots, and other JSON/JSONL outputs should carry
      explicit `schema_version` fields with a guard proving coverage rather
      than relying on selective adoption. The first required matrix must
      include `probe-report`, `review_packet`, `decision_packet`,
      `file_topology`, `review_targets`, `.probe-allowlist.json`, and the
      JSONL finding/review ledgers with owner, compatibility window,
      migration path, rollback path, and enforcing guard.
- [ ] Promote `devctl platform-contracts` from partial blueprint to
      authoritative contract catalog before `P1`: extend contract metadata so
      every `P0` contract can declare version/stability/compatibility/migration
      ownership, and do not describe the surface as authoritative until it
      covers `ActionResult`, `CommandGoalTaxonomy`, `RepoMapSnapshot`,
      `MapFocusQuery`, `TargetedCheckPlan`, `Finding`, `FixPacket`, and
      `DecisionPacket`. First bounded matrix landed for the currently
      implemented families (`TypedAction`, `RunRecord`, `ArtifactStore`,
      `ControlState`, `ReviewState`, `Finding`, `DecisionPacket`,
      `ProbeReport`, `ReviewPacket`, `ReviewTargets`, `FileTopology`,
      `ProbeAllowlist`); extend, do not restart, from that seam.
- [ ] Add one contract-closure/meta-governance guard over the platform spine:
      fail when a contract exists only in prose, only in a packet emitter, or
      only in the machine-readable catalog. The guard should reconcile the
      plan-owned `P0` contract list, `platform-contracts`, runtime models,
      schema-version matrices, and generated startup surfaces so AI/dev
      workflow structure cannot silently drift. First bounded implementation is
      now live as `check_platform_contract_closure.py` for the already-real
      runtime/artifact/startup-surface families; expand it as the remaining
      `P0` contracts land, starting with authority-source integrity and
      structured-routing enforcement for the new AI consumer paths so dual
      authority seams and prose-derived contract parsing fail deterministically
      instead of surfacing only in external review.
- [ ] Add the first platform test-hardening matrix behind those contracts:
      cover platform contract registration, failure-mode handling
      (JSONL/subprocess/concurrent access), and boundary integration from
      guard/probe finding through ledger/adjudication/feedback routing so
      `MP-377` proves the wiring, not just the schema prose. The first cut
      must also produce a developer-runnable local integration suite for these
      flows instead of leaving end-to-end coverage CI-only or audit-only.
      Owner/phase:
      `MP-377` `P1` validation tranche after the core routing paths are live.
      (audit mapping: `SYSTEM_AUDIT.md` T3, T4, T5)
- [ ] Add one bounded self-hosting producer-to-consumer smoke lane for the
      governed startup surfaces: exercise `probe-report`,
      `governance-review`, `governance-quality-feedback`,
      `context-graph --mode bootstrap`, `platform-contracts`, and
      `startup-context` against the same artifact roots, and prove the emitted
      startup preflight stays coherent with `check-router` on the same routing
      basis so CI/local smoke validates real emitted data paths instead of
      only schema/catalog drift.
- [ ] Promote `devctl map` from narrative target to checklist deliverable:
      freeze `RepoMapSnapshot`, `MapFocusQuery`, and `TargetedCheckPlan` plus
      cache/store identity, then require topology/hotspot/review outputs and
      routed next-check guidance to be projections over that shared
      repo-understanding contract instead of ad hoc helper artifacts.
- [ ] Define extension/adopter conformance packs explicitly: a new provider,
      client, hook, wrapper, or plugin should have to declare supported
      actions, modes, projections, approvals, and parity tests before it
      counts as a supported platform surface.
- [ ] Strengthen Python contract/boundary enforcement for the portable core:
      move beyond today's advisory mypy lane by evaluating stricter typed
      contract paths plus executable import-boundary enforcement for core vs
      adapters vs frontends vs repo-pack code.
- [ ] Make "no VoiceTerm defaults in portable layers" an executable gate:
      shared/core/runtime modules must not import `repo_packs.voiceterm`
      directly or cache repo-pack-derived defaults at import time; portable
      code should resolve an active repo-pack/context explicitly.
- [ ] Freeze the bridge-retirement contract: allow no new `bridge.md`
      runtime consumers, migrate existing Python/Rust/frontend readers onto
      typed projections, and keep markdown as generated debug/bootstrap output
      only once those projections are in place.
- [ ] Evaluate structural search/rewrite tooling as a bounded extension under
      platform contracts: use repo-owned Semgrep/AST-based rules and optional
      autofixers where they fit, but keep the canonical policy/evidence model
      in repo-owned governance code rather than outsourcing product semantics.
- [ ] Build a replayable evaluation harness for rule quality: define a labeled
      cross-repo corpus, stable replay inputs, and version-to-version accuracy
      comparisons so new policy/rule changes are measured against the same
      evidence set before stronger product claims or ML-ranking work lands.
- [ ] Add guard-quality meta-governance so the platform can grade its own
      rules: every blocking/advisory rule should carry expected benefit,
      bad/good examples, replay coverage, and reviewed false-positive/defer/
      fix stats, and a meta-guard/report lane should flag noisy, untested,
      overlapping, or non-uplifting rules before the check surface turns into
      low-value noise. Expand that lane to include guard/probe coverage,
      workflow coverage, exception completeness, and data-as-code/config
      smells so the repository can measure governance quality instead of only
      product-code quality.
- [ ] Define a waiver/suppression lifecycle that matches the deterministic
      governance goal: owner, rationale, scope, expiry, reevaluation trigger,
      and reporting hooks so suppressions stay visible debt instead of becoming
      unbounded hidden escape hatches.
- [ ] Define platform completion gates so `MP-377` cannot close on packaging
      work alone: architecture boundary, pipeline parity, reviewed evidence
      quality, replay coverage, telemetry trust, and cross-repo adoption all
      need explicit closure criteria.
- [ ] Materialize the proof-gate surface itself so the gates above are not
      prose-only: add one repo-owned maturity/proof readout that can report
      current gate status, missing evidence, and the specific checklist items
      blocking `Gate 2` second-repo proof or later release/productizing
      claims.
- [ ] Establish a standing pattern-mining program for Python and Rust first:
      repeated scans over this repo plus external adopters should keep feeding
      new low-noise probe/guard candidates, with adjudication evidence used to
      decide which patterns graduate, stay advisory, or get discarded.
- [ ] Define the language-extension contract up front: shared finding schema,
      policy hooks, review-ledger semantics, telemetry fields, and packaging
      model for future language analyzers so support can grow beyond
      Python/Rust without fracturing the platform architecture.
- [ ] Continue directory-by-directory organization so filesystem layout mirrors
      package boundaries and support modules stop accumulating in flat roots.
- [ ] Make `devctl` self-hosting for layout governance: overcrowded roots must
      be discoverable by policy, frozen against further flat growth, and
      baseline/adoption scans must explain the same organization contract to
      external repos before packaging/splitting proceeds.
- [ ] Make `devctl/commands` and other high-density families explicit
      namespaces, not implicit dumping grounds: the repo pack should baseline-
      report crowded flat families, freeze further flat family growth, and
      point agents to concrete target subpackages such as `commands/check/`,
      `commands/autonomy/`, and `commands/release/`.
- [ ] Validate the extracted platform on at least two non-VoiceTerm repos with
      no core-engine patching required between adoptions.

## Session Resume

Use this section as the single "left off here" surface for fresh AI sessions
working on `MP-377`.

- 2026-04-18 consolidation-plan authoring follow-up:
  `MP-377` now explicitly absorbs the one-plan consolidation campaign instead
  of spawning another active plan. The new bounded lane is `MP-388..MP-397`:
  archive four reference-only active docs first, then land semantic
  plan-loader extraction, anchor/mutation writeback, `PlanTargetRef` /
  `WorkIntakePacket` cutover plus `MASTER_PLAN` demotion, role expansion,
  command-registry wiring, and the half-done closure contract. `MP377-P1-T05`
  through `MP377-P1-T08` are intentionally parked as `blocked` follow-up work
  until that consolidation lane lands. The next bounded slice is
  `MP388-T01` / `MP388-T02`; the highest-value technical follow-up right after
  that cleanup is `MP389-T01`.
- 2026-04-18 provider-role authority + prepared-launch checkpoint follow-up:
  the current `rev_pkt_0991` checkpoint now folds the sibling
  `rev_pkt_1014` provider-hardcode cleanup into the same bounded proof.
  `assess_prepared_launch_authority()` derives post-launch
  `remote_control` head-drift continuity from typed governance/review-state
  evidence while still honoring explicit `DEVCTL_OPERATOR_INTERACTION_MODE`
  overrides first, and event/status/coordination current-session consumers
  now resolve coding/reviewer providers from `CollaborationSessionState`
  instead of assuming `codex` / `claude`. The same slice keeps
  `event_watch_support.load_target_packets()` compatible with both the new
  `EventWatchContext` call path and the legacy watch-follow arguments during
  the command-package migration. Focused proof is green on
  `test_launch_authority.py`, `test_current_session_projection.py`,
  `test_coordination_snapshot.py`, `test_event_watch_support.py`, and the
  targeted provider-index regression in `test_review_packet_inbox.py`.
  Treat this as code-hardening only, not live runtime closure: fresh
  2026-04-18 `review-channel status` / `doctor` receipts still report
  `runtime_missing`, blank `current_instruction_revision`, and
  `implementer_ack_state=missing`, so the next step after the governed
  checkpoint is to re-run startup/status from the new `HEAD` and keep the
  locked order on `rev_pkt_0947` then `rev_pkt_0950`.
- 2026-04-17 host-process cleanup checkpoint follow-up:
  live `process-cleanup --verify` is green again after narrowing conductor
  protection to runtime/script liveness for registry-backed `session_pid`
  values, even when `session.live` is false because prepared authority drifted.
  That clears the current governed checkpoint blocker without killing the live
  review loop. The explicit next architecture slice after this checkpoint is
  `rev_pkt_0947`: add typed packet lifecycle state so inbox observation stops
  masquerading as resolution; `rev_pkt_0950` Tier 1.1 findings-priority
  activation stays immediately behind it.
- 2026-04-17 checkpoint-first detached-runtime follow-up:
  the current repo proof no longer deadlocks on "relaunch vs checkpoint" when
  dual-agent runtime is detached but reviewer authority is already current.
  Shared attention now preempts detached-runtime recovery with
  `checkpoint_required` when `reviewed_hash_current=true`,
  `review_needed=false`, and typed `push_enforcement` says the tree is over
  budget; `status`, `doctor`, and `startup-context` all surface
  `required_action=cut_checkpoint`, `next_command=python3 dev/scripts/devctl.py commit -m "<descriptive message>"`,
  and allow `vcs.stage` / `vcs.commit` while still blocking
  `implementation.edit`. Focused proof is green on
  `test_recovery_assessment.py`, `test_action_routing.py`,
  `test_startup_context.py`, and the checkpoint-routing status regression in
  `test_review_channel.py`. Next step after this receipt is the governed
  checkpoint, then resume the standing-loop automation work from a fresh
  post-commit receipt.
- 2026-04-17 remote-control commit approval automation follow-up:
  remote-control checkpoints no longer require hand-assembled
  `commit_approval` packets. `devctl commit --approve-pending` now acts as
  the explicit operator-owned resume command: it reuses the governed
  pipeline, posts/applies the matching typed `commit_approval` decision, and
  continues the same `vcs.commit` run without manual packet field assembly.
  The helper and commit-phase packet loader now consume reduced packet rows
  directly instead of forcing a full event-bundle enrichment pass for packet
  matching. Focused proof is green, and the remaining latency hotspot is the
  first `devctl commit -m ...` remote-control preflight, which still pulls
  the heavier context-graph/work-intake path and remains follow-up work.
- 2026-04-17 current-session authority hardening follow-up:
  event-backed `current_session` now requires explicit packet truth before a
  blank queue can clear the prior typed instruction, and
  `queue.derived_next_instruction` only projects into Claude's lane when
  `derived_next_instruction_source.to_agent` is blank or `claude`. The same
  slice keeps bridge-backed authority fail-closed when the live bridge has no
  authority signal, blocks `ImplementationAdmissibility` when typed
  `implementation_permission` is missing/empty, and lets reviewer-follow
  auto-relaunch only when the typed recovery decision marks
  `relaunch_review_loop` auto-fixable. Focused projection/runtime proof is
  green; maintainer-doc closure for this slice now lives in `AGENTS.md`,
  `dev/guides/DEVELOPMENT.md`, `dev/scripts/README.md`,
  `dev/active/MASTER_PLAN.md`, and `dev/history/ENGINEERING_EVOLUTION.md`.
- 2026-04-17 operator-inbox read-only alias follow-up:
  the next `rev_pkt_0915` Phase-1 dogfood slice did not need a new transport
  or new packet enums. `review-channel --action operator-inbox` now exposes
  the operator queue as a first-class read surface over the existing typed
  packet lane, fixes `target=operator`, defaults to `status=pending`, and
  intentionally refuses to stamp `delivery_observed_*` receipts on live
  `action_request` packets. That keeps operator/dashboard/phone reads on the
  same packet spine without mutating delivery state that belongs to the live
  actor watchers. Focused proof is green on the new operator-inbox regression
  test plus `check_code_shape.py`, and the next follow-up remains broader
  dogfood integration: record this operator-facing read surface in the
  dev-mode dogfood ledger and decide whether the later top-level
  `devctl operator-inbox` wrapper is worth the extra command-surface cost.
- 2026-04-17 commit/push next-command convergence follow-up:
  the next dogfood slice closed the remaining gap between typed pipeline
  truth and the operator-facing commit/push blockers. `pipeline status`
  already projected exact `next_command` strings, but commit surfaces still
  regenerated prose. `commit_pipeline_blocking.py` now consumes the typed
  status view directly, auto-refreshes same-HEAD expired authorization before
  it blocks on a live `push_blocked` pipeline, and emits the exact next
  command instead of a fallback sentence. `commit_preflight.py` now does the
  same for explicit-approval edge cases (`no_pending_pipeline_to_approve`,
  stale pipeline, missing operator approval), and `commit.py` projects
  `CommitPermissionDecision` `next_command` / `recovery_action` /
  `escalation_action` at top level so agents do not have to unpack or infer
  the recovery path from nested payloads. Focused proof is green on the
  narrowed commit-gate regressions, the full push/pipeline bundle, and
  `check_code_shape.py`.
- 2026-04-17 push-status truth-split follow-up:
  the next dogfood slice closed the remaining ambiguity between "what is the
  raw latest push artifact on disk?" and "what push report should startup /
  review-channel trust for the current publication target?" `push_enforcement`
  now emits both raw `latest_push_report_*` fields and separately selected
  `selected_push_report_*` / `selected_push_report_source` fields, so
  startup recovery and governed push decisions can fail closed on the
  selected current-target receipt while operator/read-only status surfaces
  stay truthful about the actual `dev/reports/push/latest.json` artifact. The
  same slice also closes the bridge compat omission that kept
  bridge-backed `_compat` payloads from carrying `push_enforcement`, and adds
  latest-push artifact freshness invalidation to review projection caches so
  mobile/read-only consumers refresh when push-state changes. Focused proof is
  green on push-state/startup regressions, compat/cache regressions, and
  `check_code_shape.py`.
- 2026-04-17 checkpoint-recovery projection follow-up:
  the next checkpoint-repair pass closed a stale-state overwrite that was
  still making the dogfood loop look hung. Direct `pipeline`
  `abandon` / `recover` / `refresh-authorization` writes now refresh the
  shared review-channel projections immediately after they persist canonical
  pipeline truth, so `review-channel status` and the next governed
  `devctl commit` read cannot mirror an older `latest/commit_pipeline.json`
  payload back over `projections/latest/commit_pipeline.json`. The same slice
  also types the expanded pending-reviewer commit gate against `ReviewState`,
  keeping repo-wide `check_python_typed_seams.py` green after the helper
  extraction. Focused proof is green on
  `test_pipeline_command.py`, `test_commit_pending_reviewer_gate.py`,
  `check_python_typed_seams.py`, and `check_code_shape.py`. Next live step:
  rerun the governed checkpoint, then take Claude's
  `guards_failed` next-command follow-up (`rev_pkt_0949`) before widening to
  the findings-backlog / packet-lifecycle automation slice.
- 2026-04-15 plan-registry authority artifact closure:
  `scan_governed_markdown_contracts()` now persists governed markdown
  `PlanRegistry` plus per-plan `PlanTargetRef` data to
  `dev/reports/governance/plan_registry.json`, reuses that artifact while the
  governed doc set and per-file stats stay fresh, and `build_target_ref()`
  now consumes the persisted target metadata before hashing plan markdown
  again. Proof is green in `test_governance_draft.py`,
  `test_work_intake.py`, `test_planning_ir.py`, and
  `test_startup_context.py`. Next target: `MP377-P1-T05` bounded markdown
  projection rendering over that persisted registry.
- 2026-04-15 dogfood campaign contract closure:
  `devctl dogfood --record` now carries the live campaign/linkage metadata the
  platform needs for real multi-surface proof (`campaign_id`, `scenario_id`,
  `repo_scope`, `repo_label`, `repo_path`, `topology`, `lane_role`,
  `live_run_refs`, `governance_finding_ids`), and
  `governance-import-findings` now treats `LIVE_RUN.md` as explicit
  compatibility intake with repo-scoped `repo_name:Q-ID` sync keys instead of
  manual copy-forward. That makes the campaign executable through repo-owned
  ledgers: canonical findings stay in `FindingBacklog` /
  `governance-review`, `LIVE_RUN.md` stays mirror/projection evidence, and
  dogfood rows can link the two without chat-local bookkeeping.
- 2026-04-15 docs-routing authority closure:
  `governed_doc_routing.py` now prefers typed `ProjectGovernance` doc paths
  (`docs_authority`, guide roots, scripts README, tracker/index roots) before
  surface-generation context fallbacks when docs-governance composes
  maintainer-doc defaults. Focused proof is green in
  `test_governed_doc_routing.py`, `test_docs_check_constants.py`, and
  `test_governance_draft.py`; clean-tree proof is green in
  `python3 dev/scripts/devctl.py check --profile ci`.
- 2026-04-15 typed scope-reader plus packet-inbox cleanup follow-up:
  `MP377-P1-T05` now keeps `plan_registry` bounded to execution-authority docs
  while still giving scoped plan readers a typed path to companion docs.
  `plan_registry_projection.py` resolves execution plans first and then typed
  `doc_registry` companion docs before any raw `INDEX.md` compatibility
  fallback, and `review_packet_inbox_merge.py` now drops persisted
  latest-finding/expired-unresolved ids that are no longer present in the
  live reducer so `open_findings`/attention cannot be revived by stale merge
  state alone. Focused proof is green in `test_plan_resolution.py`,
  `test_promotion_scope.py`, `test_review_packet_inbox.py`, and
  `test_work_intake.py`; the remaining open queue debt is the historical
  `stale_packet_count` semantics, not current packet visibility.
- Next action: run the campaign in the bounded order now written into the
  owner docs. VoiceTerm remains the full live proof first with
  `Codex conductor/reviewer + Claude remote-control implementer + permanent
  Claude packet watcher`, and mutating fanout stays capped until startup
  receipts stop reporting `safe_to_fanout=False` / `resync_required=True`.
  When Claude/operator loops need live reviewer packet visibility, use the
  explicit typed `review-channel --action inbox|watch --target codex`
  surface; Codex-targeted packets are not implicitly visible in the Claude
  lane.
  External repos remain engine-matrix proof first: rerun anchors in waves of
  `3`, stop on the first new `engine_bug`, import honest adopter findings
  through `governance-import-findings`, and only widen back toward `5` repos
  after one clean wave.
- 2026-04-15 startup-authority bootstrap fix:
  `startup-context --format summary` is healthy again on the live repo. The
  regression was not in startup-context assembly; it was in the
  startup-authority guard's import-index atomicity check, which was walking the
  entire committed Python tree from `HEAD` and reading importer source
  file-by-file on every bootstrap. The guard is now bounded to the local
  worktree package scope touched by current Python changes, so startup still
  catches local split/atomicity drift without turning every fresh session into
  a full committed-tree import audit.
- 2026-04-15 startup-repair authority parity fix:
  `startup-context --repair` no longer reports "healthy" when the same typed
  startup state already blocks implementation on
  `coordination_resync_required`. The repair path now reuses the same
  blocker-driven advisory coercion as normal `startup-context` output and
  emits an explicit manual-follow-up issue from `AuthoritySnapshot` /
  `CoordinationSnapshot` whenever `safe_to_continue=false` comes from
  coordination resync rather than review attention degradation. Remaining live
  resync receipts are now honest operational state, not a repair-surface blind
  spot.
- Current status: the umbrella plan now owns the reduced execution-owner set
  and the typed phase/task contract. The live dogfood walkthrough already
  closed the stale `active_target` / projection parity gaps across startup,
  session-resume, dashboard, review-channel status, and context-graph, and
  the latest closure finished the P0 findings-write spine:
  `governance-review --record` now routes through the canonical
  `FindingBacklog` writer, `devctl dogfood --record --record-governance` can
  auto-close linked dogfood findings with stable ids plus live target-path
  defaults, and the governance/dogfood ledgers resolve against the runtime
  repo root instead of a baked-in VoiceTerm path.
- 2026-04-13 architecture-review ingest:
  Claude review packets `rev_pkt_0375` through `rev_pkt_0378` are now backed
  by typed `governance-review` rows for the still-open architecture gaps
  around dogfood finding-id stability, dogfood read-only registration,
  authority snapshot field reduction, bridge-authority demotion, plan
  markdown projection, and the `AGENTS.md` dual-purpose conflict. Keep the
  execution order explicit: authority snapshot/object closure first, bridge
  demotion second, persisted `PlanRegistry` + markdown projection third, and
  scenario-runner widening after those foundations are real.
- 2026-04-13 authority-snapshot follow-up:
  the first closure from that architecture queue is now real. Startup,
  session-resume, and review-channel status/doctor all project the same
  reduced `AuthoritySnapshot` contract from
  `dev/scripts/devctl/runtime/authority_snapshot.py`, so a fresh AI turn can
  read one typed `coordination_state`, `root_cause`, `required_action`,
  `next_command`, and `safe_to_continue` answer instead of reconstructing it
  from startup prose, doctor fields, current-session ACK state, and packet
  inbox rows separately. Dual-agent instruction-revision drift with a stale
  implementer ACK now reduces to `handshake_stale` before the generic
  blocked-state fallback.
- Next action: close the remaining `P0`/`P1` foundation slices in order:
  first collapse reviewer/runtime authority onto one producer/read-model path
  (`review_state`, `commit_pipeline`, `AuthoritySnapshot`,
  `CoordinationSnapshot`, `ControlPlaneReadModel`), then make commit/push and
  phone/operator actions refresh and consume that same state without manual
  `review-channel --action status` repair loops, then land the persisted
  `PlanRegistry` / `PlanTargetRef` artifact plus markdown projections, then
  widen the dogfood engine into the multi-agent audit runner, and only after
  that spend time on adopter-repo proof.
- Context rule: start from `startup-context`, `governance-review`, and the
  review-channel inbox, then read this file and only the owner docs named by
  the active typed phase/task route.
- 2026-04-13 dogfood follow-up:
  `quality_signals.finding_backlog`, promoted `active_target`, bridge status
  reprojection, and task-id/context-graph aliases are now part of the
  required cross-surface parity set. If one surface still disagrees with the
  typed source, treat that as a platform bug and record it through
  `governance-review --record` before widening functionality.
- 2026-04-14 dogfood follow-up:
  `rev_pkt_0391` is now closed in repo code: `auto-mode` no longer advertises
  push/checkpoint-forward phases when both reviewer and implementer are not
  live, and instead falls back to `phase=reviewing` with a
  "resume a live participant before commit/push can continue" transition.
  The sharper `rev_pkt_0413` gate split is also reduced from a dangerous
  permissive-vs-restrictive mismatch to a label-only drift: startup-context,
  session-resume, review-channel status, and review-channel doctor now all
  block edit/stage/commit on the same checkpoint-required state, even though
  startup/session-resume still phrase the blocker as
  `single_agent_authoritative` / `resume_live_review_loop` while
  status/doctor phrase it as `resync_required` / `cut_checkpoint`.
  `rev_pkt_0414` is the next architecture request on deck after this
  checkpoint: add a typed WakeSignal / wake-fanout / agent-consumer-registry
  lane so Codex-to-Claude delivery is not stuck behind Claude-side polling.
- 2026-04-15 cross-surface attention convergence follow-up:
  the remaining `rev_pkt_0534` split is no longer live. Event-backed review
  state enrichment now attaches the same typed conductor session state as
  bridge-backed `review-channel status` before recovery assessment runs, so
  `review-channel status`, `startup-context`, `session-resume`, and
  `dashboard` all agree on
  `attention.status=review_loop_relaunch_required` for the current repo
  state. Checkpoint sequencing still lives in `advisory_action` /
  `push_decision`, but runtime diagnosis is now one producer path instead of
  a status-vs-dashboard split. Before commit/push, rerun
  `docs-check --strict-tooling`: Claude confirmed via `rev_pkt_0540` and
  `rev_pkt_0541` that `bundle.tooling` routes there authoritatively for this
  change set.
- 2026-04-15 control-plane error-handling follow-up:
  the next real system-reported hotspot from Claude's `rev_pkt_0535`
  governance-review lane is now partially closed too. The hot-path control
  plane reader no longer hides git probe failures behind
  `branch=unknown/head=unknown`: `runtime/control_plane_resolve.py::load_git_state()`
  now raises a typed `ControlPlaneGitStateError` with causal `from exc`
  context on `OSError` / `subprocess.TimeoutExpired`, and the read-model path
  preserves that fail-closed behavior instead of silently treating missing git
  state as benign. Focused proof is green in
  `test_control_plane_read_model.py::GitStateFailureTests`.
- 2026-04-15 bridge-backed attention-priority follow-up:
  the live relaunch-vs-poll-due split reopened inside the shared classifier,
  not in a renderer. `review-channel --action status --refresh-bridge-heartbeat-if-stale`
  had started emitting `attention.status=reviewer_poll_due` even while the
  same bridge payload still carried `launch_truth=hybrid_claude_only`,
  `live_reviewer_total=0`, and detached-runtime contract errors; meanwhile
  `startup-context --format summary` still correctly surfaced
  `review_loop_relaunch_required`. The bounded fix is now in the shared
  attention reducer: detached/hybrid launch truth short-circuits freshness in
  `attention_classify.py` so bridge-backed status cannot downgrade a dead
  reviewer loop to a heartbeat warning. Focused proof is green on the new
  `test_attention_prioritizes_relaunch_over_poll_due_for_hybrid_claude_only`
  regression plus the existing hybrid event-projection/status tests, and live
  proof is green again on both `review-channel --action status ...` and
  `startup-context --format summary`, which now agree on
  `attention_status=review_loop_relaunch_required`. The next blocker after
  this slice is only the real runtime approval boundary:
  operator-approved `review-channel --action launch` / `rollover`.
- 2026-04-15 action-request queue hot-path follow-up:
  the repo-owned coordination lane slowdown was not the 18k-event reducer
  itself. Direct timing on `refresh_event_bundle()` stayed near 1.5s on the
  current event log, but event-backed `review-channel post` / `inbox` reads
  were still taking tens of seconds whenever a pending `action_request`
  existed because queue derivation rebuilt a context-graph escalation packet
  on every read for the selected pending action-request. The shared queue path
  now skips `build_event_context_packet()` for selected
  `kind=action_request` packets while preserving the actionable summary and
  control metadata (`packet_id`, selection policy, wake_required,
  requested_action). Focused proof is green on the new
  `test_action_request_priority_skips_expensive_context_packet_build` plus the
  existing plan-packet action-request regressions, and live proof is green on
  `python3 dev/scripts/devctl.py review-channel --action inbox --target claude
  --terminal none --format json --execution-mode markdown-bridge --limit 1`,
  which now completes in about 2.2s on the current repo state. Claude also
  acked the clean observer request `rev_pkt_0547`; the malformed duplicate
  `rev_pkt_0546` and timing probe `rev_pkt_0548` were explicitly dismissed so
  packet backlog stayed clean.
- 2026-04-15 startup contract-ownership projection follow-up:
  the older `startup_surface_tokens_unpopulated` governance row was stale in
  one real way: `startup-context` had grown a `contract_ownership_map`, but it
  still collapsed startup-surface tokens down to a misleading one-token-only
  preview before JSON serialization. The bounded repair now keeps the full
  `startup_surface_tokens` list inside `StartupContext`, emits
  `startup_surface_token_count` plus a bounded preview in
  `startup-context --format json`, and removes the stale single-token limiter
  from `runtime/startup_context.py`. Focused proof is green on
  `test_startup_context.py` (`contract_ownership_map` / `to_dict` cases), live
  proof is green on both `startup-context --format json` and
  `startup-context --format summary` on the current repo state
  (`ReviewState.startup_surface_token_count=5` with a bounded preview starting
  at `snapshot_id`, while summary still reports
  `action=checkpoint_before_continue`,
  `reason=staged_index_budget_exceeded`, and
  `attention_status=review_loop_relaunch_required`), and both
  `check_platform_contract_closure.py` and `check_code_shape.py` stay green.
  Local dogfood is recorded as `dogfood-95f32b3f4406`, governance-review
  finding `2146d8ee3f303af6` is now fixed, Claude's PASS on the earlier
  action-request queue hot path landed as `rev_pkt_0553` and is acked, and the
  startup-slice observer request `rev_pkt_0554` has now closed cleanly too:
  Claude's PASS landed as `rev_pkt_0555` and is acked.
- 2026-04-15 authority-snapshot actor identity follow-up:
  the older `authority_snapshot_3_fields_missing` architecture finding stayed
  materially open after the first reducer pass: `AuthoritySnapshot` already
  carried `allowed_actions`, but the startup projection still omitted
  `actor_role` and `actor_identity`. The bounded repair now extends the shared
  authority snapshot contract/core reducer so startup JSON and the generated
  startup receipt both persist `actor_role`, `actor_identity`, and bounded
  `allowed_actions` from the same typed snapshot
  (`authority_snapshot.actor_role=implementer`,
  `authority_snapshot.actor_identity=claude` on the current repo state). The
  actor-resolution logic was extracted into
  `runtime/authority_snapshot_actor.py` so `authority_snapshot_build.py` stays
  under the code-shape soft limit. Focused proof is green on
  `test_startup_context.py` authority-snapshot cases,
  `test_session_resume.py` authority-snapshot roundtrip,
  `check_platform_contract_closure.py`, and `check_code_shape.py`; local
  dogfood is recorded as `dogfood-52ab6f07e6dd`, and governance-review finding
  `8487d1d61d49efb9` is now fixed. Claude dogfood for this slice also closed
  cleanly: request `rev_pkt_0556` was acked by Claude, PASS landed as
  `rev_pkt_0557`, and Codex acked it.
- 2026-04-15 governed-commit guard-bundle unblock:
  the staged `MP-377` tree hit a real governed-commit stop, not just stale
  review-loop posture: `devctl commit` reached the guard bundle and failed on
  one duplicated packet-attention helper pair, five new high-parameter
  functions, and one large dict literal. The unblock stayed surgical inside the
  dirty worktree: current-session packet attention now resolves through the new
  shared helper `review_channel/current_session_attention.py`, the
  event-projection/reducer/heartbeat/authority helpers now pass typed resolver
  or input objects instead of widening function signatures, and
  `session_resume_authority_payload.py` now serializes the packet-attention
  agent payload through `asdict()` instead of a new oversized dict literal.
  Focused proof is green on `test_current_session_projection.py`,
  `test_session_liveness_events.py`, targeted `test_startup_context.py`
  authority-snapshot cases, targeted `test_session_resume.py` review-state
  context/authority roundtrip, and the four blocking shape guards
  (`check_function_duplication.py`, `check_structural_similarity.py`,
  `check_parameter_count.py`, `check_python_dict_schema.py`). Local dogfood is
  recorded as `dogfood-baf0d7aa6e50`; Claude observer request `rev_pkt_0558`
  has already closed cleanly too: PASS landed as `rev_pkt_0559`, and Codex
  acked it before rerunning the governed checkpoint.
- 2026-04-15 governed commit validation-receipt replay:
  the next governed retry exposed a real reuse-path automation gap:
  `devctl commit` only replayed the routed guard bundle when
  `guard_result` was missing/failing, so a reusable approved pipeline could
  still fail closed on `validation_receipt_missing` after the staged tree
  and operator decision were already intact. The fix is surgical and
  modularized: `commands/vcs/commit.py` now delegates reusable-pipeline
  receipt recovery through the new `commands/vcs/commit_guard_replay.py`
  helper whenever `validation_receipt` is missing, stale, or
  checkpoint-insufficient, then resyncs approval before `vcs.commit`
  proceeds. Regression coverage in `tests/vcs/test_commit_gate.py` now
  builds an approved pipeline with `validation_receipt=None` and proves the
  receipt is rebuilt, the guard bundle reruns exactly once, and the commit
  records cleanly. Focused proof is green on
  `python3 -m unittest dev.scripts.devctl.tests.vcs.test_commit_gate.TestGovernedCommitPipeline.test_commit_replays_guards_when_approved_pipeline_loses_validation_receipt -v`
  plus `check_code_shape.py`; local dogfood is `dogfood-fc22bfd092ff`, and
  Claude dogfood request `rev_pkt_0562` is now posted on the packet lane.
- 2026-04-13 dogfood engine follow-up:
  the dogfood engine now closes through the same findings spine as the rest
  of the platform: `governance-review --record` writes through the canonical
  `FindingBacklog` seam, and `devctl dogfood --record --record-governance`
  can refresh linked `signal_type=dogfood` findings with stable ids using
  live target-path defaults plus explicit overrides. The next closure is to
  move plan authority into persisted `PlanRegistry` state and rendered
  markdown projections before widening the same flow across reviewer,
  implementer, dashboard, and adopter-repo proofs.
- 2026-04-15 consolidated redesign checkpoint:
  after rereading the full active-plan set, the full `LIVE_RUN.md` Q1-Q100
  audit, and the live runtime receipts (`startup-context`, review-channel
  inbox, `findings-priority`, and `dashboard`), the execution order is now
  explicit in this umbrella plan instead of spread across chat and narrow
  packet notes. The whole repo is already describing one system: typed
  runtime authority first, compatibility projections second, dogfood-fed
  planning third. The next slice must therefore close the single-producer
  reviewer/runtime path before more feature work: make
  `refresh_status_snapshot` / `load_current_review_state` /
  `review_state_parser` / `commit_pipeline` / `AuthoritySnapshot` /
  `CoordinationSnapshot` / `ControlPlaneReadModel` agree on one snapshot and
  one field route, then make governed commit/push refresh and consume that
  state automatically so phone operators stop fighting stale `dashboard`,
  `bridge.md`, and preflight artifacts by hand.
- 2026-04-15 operator-directed convergence order:
  use this umbrella plan as the only writable execution surface for the
  current redesign; do not create another planning doc. The priority order is
  now explicit for the next execution loop:
  `MP377-P1-T04/T05` first so plan authority moves into persisted
  `PlanRegistry` / `PlanTargetRef` state and markdown becomes a bounded
  projection, `MP377-P1-T06` second so startup/status/dashboard/commit all
  read one producer snapshot, `MP377-P1-T07` third so governed mutation
  self-heals stale projections and closes the `Q100` attention-revision race,
  `MP377-P1-T08` fourth so reviewer/implementer/publisher/observer liveness
  comes from one typed signal family, then `MP377-P2-T05/T06` so dogfood and
  observer-boundary enforcement become the default operating path instead of
  operator memory. Live evidence for this order on the repo state at
  `1271a075`:
  `startup-context` still reports `ahead_of_upstream_commits=1` while
  `review-channel --action status` reports `Ahead: 0`, the same status frame
  reports `Infra: Down (0 daemons running)` with one pending action request,
  and the worktree is otherwise clean. Treat any further cross-surface drift
  as a reducer/runtime bug to close before widening features.
- 2026-04-15 shim/public-contract correction plus flat typed review-state
  follow-up:
  the package-layout and review-state lanes both exposed "docs said one thing,
  policy/parser said another" drift. Full shim adoption-scan showed the repo
  was still misclassifying documented `dev/scripts/checks` helper wrappers as
  temporary remove-now debt because repo policy only allowlisted
  `check_*` / `probe_*` / `run_*` root shims; that is now corrected in
  `dev/config/quality_presets/voiceterm.json`, the dead
  `dev/scripts/devctl/quality_policy_values.py` wrapper is gone, and the live
  shim backlog dropped from 9 hints to 7 with the remaining debt concentrated
  in the `dev/scripts/devctl` root plus crowded command families. In the same
  bounded slice, `review_state_parser` stopped requiring bridge-shaped envelope
  keys before it would treat a payload as canonical review state; flat typed
  payloads with `current_session`, `reviewer_runtime`, `coordination`,
  `authority_snapshot`, and `packet_inbox` now parse through the same reducer
  path, which closes one more route back to compatibility-prose authority
  under `MP377-P1-T06`.
- 2026-04-15 ensure-follow bootstrap repair:
  the mandatory repair path itself was broken on the repo state at
  `1271a075`: `python3 dev/scripts/devctl.py review-channel --action ensure
  --follow --terminal none --format json --execution-mode markdown-bridge
  --follow-inactivity-timeout-seconds 0` crashed before any relaunch because
  the publisher tried to emit typed `MonitorSnapshotPaths` directly into the
  NDJSON follow stream. `follow_stream.emit_follow_ndjson_frame` now
  normalizes dataclasses / `to_dict()` payloads / `Path` values into JSON-safe
  structures before emission, the regression is covered in
  `dev/scripts/devctl/tests/review_channel/test_follow_controller.py`, and
  the bounded live proof
  (`review-channel --action ensure --follow ... --max-follow-snapshots 1`)
  now emits a real JSON frame with `monitor_snapshot.{root_dir,json_path,markdown_path}`
  instead of raising `TypeError`. Dogfood row
  `command:review-channel.ensure_follow` is recorded for actor `codex`, and
  Claude observer request `rev_pkt_0505` is pending for packeted acceptance or
  a concrete finding on the repaired path.
- 2026-04-15 expired-inbox visibility repair:
  stale unresolved packets were still disappearing from the actionable packet
  surfaces even after queue math started counting them. Live repro on the repo
  state at `1271a075`:
  `python3 dev/scripts/devctl.py review-channel --action inbox --target codex --status expired --terminal none --format json --limit 5`
  reported `queue.stale_packet_count=282` but returned `packets=[]`. The bug
  was reducer-side, not operator error: `filter_inbox_packets(..., status="expired")`
  only matched literal `status=="expired"` rows, while most stale packets are
  still typed as pending rows whose TTL elapsed. The repair now treats
  `--status expired` as "expired unresolved" semantics
  (explicit `status="expired"` OR pending rows with past `expires_at_utc`)
  while keeping `--status pending` mapped to live actionable packets only.
  The targeted inbox observation path is also fail-closed for non-pending
  reads, so observer/debug reads of expired queues do not create fresh
  `delivery_observed_at_utc` mutations for stale `action_request` rows.
  Focused proof is green on
  `test_review_channel.py::TestDaemonEventReducer.test_filter_inbox_packets_{skips,surfaces}_expired_pending_rows`
  plus
  `test_plan_packets.py::ReviewChannelPlanPacketTests.test_expired_inbox_surfaces_stale_action_request_without_delivery_mutation`,
  and the live command above now returns real stale packet rows instead of an
  empty list. Dogfood row `command:review-channel.inbox_expired` is recorded
  for actor `codex`; Claude then reran the live path plus the observer-boundary
  non-mutation check and posted PASS packet `rev_pkt_0511` with matching
  dogfood rows (`command:review-channel.inbox.expired`,
  `command:review-channel.inbox`).
- 2026-04-15 expired-unresolved packet summaries:
  Claude's follow-up packet `rev_pkt_0512` was correct: the expired-inbox fix
  stopped selector poisoning, but stale work could still disappear from default
  reviewer-facing summaries because `current_session.open_findings`,
  control-plane blocker text, and `session-resume` kept trusting stale
  bridge-backed packet prose. The shared repair now rebuilds packet inbox truth
  from packet rows, derives `expired unresolved review packet(s)` summaries from
  typed inbox attention without reviving `derived_next_instruction`, and threads
  that summary through event-backed current-session/bridge reducers plus the
  runtime/session-resume consumer path. Focused proof is green on
  `test_current_session_projection.py`, the new
  `ResolverUnitTests.test_resolve_blocker_uses_expired_unresolved_packet_summary`,
  and
  `TestBuildFromSources.test_build_from_sources_prefers_packet_backed_expired_findings_summary`.
  Live proof is green on the event reducer (`queue.pending_total=0`,
  `queue.stale_packet_count=282`, `current_session.open_findings=193 expired unresolved review packet(s)`)
  and on `python3 dev/scripts/devctl.py session-resume --role reviewer --format json`
  which now reports `open_findings=193 expired unresolved review packet(s)` and
  blocker text beginning with the same summary instead of silently saying
  `2 pending review packet(s)`. Dev-mode dogfood is recorded as
  `dogfood-598ee3d0e5ff` for
  `command:session-resume.expired_unresolved_visibility`, Claude observer
  dogfood is recorded as `dogfood-34c28f1b9410`, and Claude acceptance landed
  in `rev_pkt_0515` and is acked. This slice is now closed under the dogfood
  contract: focused tests pass, the live reviewer-facing command path passes,
  Claude posted packeted PASS, and the active plan reflects closure.
- 2026-04-15 packet-lane authority gap:
  The operator-called smell is real and belongs under `MP377-P1-T06/T08`, not
  as chat-local process debt. Startup still reports
  `action=checkpoint_before_continue`, `runtime_missing`, and
  `implementation_permission=blocked` while `review-channel --action status
  --execution-mode markdown-bridge --refresh-bridge-heartbeat-if-stale` still
  fails closed on `Missing live implementer ACK compatibility section (Claude
  Ack)`, even though the packet watcher lane is healthy enough to accept and
  ack Claude findings (`rev_pkt_0515`, `rev_pkt_0516`). A bounded sidecar
  investigation confirmed the root cause: packet-backed truth exists in
  `review_packet_inbox`, but startup/session/status reducers and maintainer docs
  still preserve compatibility fallbacks where `current_session`,
  bridge-heartbeat prose, and `Claude Ack` can participate in wait routing.
  Next implementation slice must make typed packet inbox plus typed liveness the
  sole continue-vs-wait authority, keep compatibility projections read-only,
  and remove bridge-only repair blockers that can stall a live packet lane.
- 2026-04-15 live-loader convergence on bridge-backed status/ensure:
  `MP377-P1-T06` moved one layer deeper: bridge-backed
  `refresh_status_snapshot()` was still seeding `prior_review_state` from the
  cached review-state loader, so `review-channel --action status` and
  `review-channel --action ensure --follow` could drift back to the stale
  `- Await reviewer instruction refresh.` projection even after
  startup/session-resume had been repaired to use the live loader. Fixed the
  status seed path by routing `load_prior_review_state()` through
  `load_current_review_state_payload(..., prefer_cached_projection=False,
  review_status_dir=output_root)`, then tightened bridge validation so the
  `Current instruction revision` / `Claude Ack` compatibility gate no longer
  fires when the bridge is only projecting the reviewer-wait placeholder and
  there is no live instruction to acknowledge. Focused proof is green on
  `test_review_state_locator.py`, the new
  `test_refresh_status_snapshot_loads_live_prior_review_state_for_status_refresh`,
  `test_run_status_rehydrates_authority_snapshot_from_fresh_projection`, and
  the new `test_validate_live_bridge_contract_skips_ack_revision_gate_for_wait_placeholder`.
  Live proof is green on both repo-owned commands:
  `review-channel --action status --refresh-bridge-heartbeat-if-stale` and
  `review-channel --action ensure --follow --max-follow-snapshots 1` now emit
  the plan-backed `authority_snapshot.current_slice`, the same
  `coordination.current_slice`, `current_session.current_instruction=""`, and
  only the real reviewer-runtime error (`review_loop_relaunch_required`) rather
  than the stale bridge revision error. `latest/review_state.json` now persists
  the same plan-backed `current_slice` with empty `current_instruction`.
  Dev-mode dogfood is recorded as `dogfood-e09b02277d9d`. Claude observer
  action-request `rev_pkt_0528` is pending; `rev_pkt_0527` should be treated as
  superseded because its body was shell-quoted badly during posting.
- 2026-04-21 `rev_pkt_1503` live-loader follow-up: `MP377-P1-T06` now also
  keeps bridge-contract-drift repair behind event-backed review-state
  authority. `load_current_review_state_payload()` branches
  `projections/latest/review_state.json` before checking cached bridge contract
  drift, so event-backed startup/status/session-resume/dashboard reads cannot
  be silently downgraded to the bridge-backed compatibility root. The
  bridge-backed cached projection path still refreshes when drift is detected.
- 2026-04-15 dogfood loop contract:
  Codex owns implementation, canonical plan updates in this file, repo guard
  runs, and `devctl dogfood --record --dev-mode --actor codex` for every
  exercised command/guard slice. Claude owns dashboard/observer/phone-style
  verification, packeted findings, and
  `devctl dogfood --record --record-governance --dev-mode --actor claude`;
  Claude must not become a hidden implementation lane or raw session killer.
  The operator only supplies product intent, approval-boundary decisions, and
  physical/manual validation. A slice is not done until four things are true:
  focused tests pass, the live repo command path passes, Claude posts either a
  packeted dogfood acceptance or a concrete finding, and the corresponding
  `LIVE_RUN.md` Q-item or finding cluster is updated with the closure state.
- 2026-04-12 architecture-synthesis / phase-order update:
  the 15-command audit plus dashboard packet review confirmed that five
  directions are already platform law (deterministic runtime, role
  enforcement in code, bidirectional event transport, state-driven next
  action, and projection-only status surfaces), but six implementation
  closures remain open. Keep the order explicit: Phase 0 visibility/consumer
  wiring first (`FindingBacklog`, one governed snapshot/root,
  four-surface status convergence, packet lifecycle/event wake, live
  tool-call visibility), then Phase 1 autonomy with `devctl develop` as the
  single self-driving entrypoint over those typed surfaces.
- 2026-04-12 provider-role portability slice:
  resume from the role-first/runtime-first closure order with the first
  provider-neutral/runtime-identity closure already landed. Typed
  review/status reads now prefer reviewer/implementer aliases over legacy
  `codex_*` / `claude_*` bridge names, and governed commit/push approval is
  bound to the exact checkout that staged it. Default requested worker fanout
  stays on the shared primary checkout; isolated worktrees are only for
  explicit delegated-worker fanout with their own `worktree_identity`. The
  next work is to teach that default through bootstrap/dashboard/status
  surfaces, rerun the same backend proof with Codex coding from the primary
  lane and Claude attached as dashboard/operator, then widen to delegated-
  worker, swapped-role, and external-repo proofs without reintroducing
  provider-first defaults.
- 2026-04-11 governed-push visibility slice:
  resume with the phase-aware latest-push artifact closure in place.
  `devctl push --execute` now refreshes `dev/reports/push/latest.json` from
  `push_preflight_running` through `push_pending` and on into the existing
  `published_remote` state, and startup already suppresses duplicate push
  advice when that current-head artifact is live. The next work here is still
  portable authority/read-model convergence, not another shell-local polling
  workaround.
- 2026-04-11 bootstrap/client-vs-core surface slice:
  resume with the portable starter/instruction wording pass. Keep the owned
  edit set to generated instruction surfaces, the bootstrap guide writer,
  portable setup template, maintainer docs, and this plan note. Do not edit
  runtime mutability/precedence code; the goal is to make the product/client
  boundary explicit while preserving the role-first, provider-agnostic
  framing.
- 2026-04-10 guard-promotion intake:
  resume with the guard-promotion audit absorbed into the existing
  governance-closeout chain. `governance-review --record` now creates the
  first durable `GuardPromotionCandidate` queue entry when the prevention
  surface is `guard` or `probe`, with the JSONL queue as the durable read
  surface for now. The next slice should add validation/scaffolding only after
  this queue proves useful; do not bypass `FindingReview` or create a parallel
  audit-only backlog.
- 2026-04-09 bootstrap-catalog / graph convergence slice:
  `SystemCatalog` now owns the generated bootstrap command inventory as typed
  authority rather than leaving `CLAUDE.md` / startup helpers to drift from a
  hand-maintained command block. The bounded follow-up is explicit: keep rich
  relations in `SystemCatalog` / `discover`, keep startup packets token-bounded,
  and let `context-graph` consume a summarized typed bootstrap view plus graph
  edges to commands/guards/probes/surfaces/plans. The next step after this
  green slice is one generated convergence-audit packet that both Codex and
  Claude can read from the same repo-owned artifact instead of reconciling
  separate chat-local summaries.
- 2026-04-09 command-boundary freeze closure:
  the reopened MP-384/MP-387 F1 rerun is now repaired. `session-resume` cache
  misses resolve one live `load_current_review_state(... prefer_cached_projection=False)`
  snapshot, dashboard resolves governance plus current review state once per
  snapshot and threads that same typed object through both raw sources and
  `ControlPlaneReadModel`, and the focused parity pytest bundle is green on
  consecutive runs. Resume from the next bounded follow-up only:
  mobile/helper/repo-pack read-side consumers plus the live remote-control
  proof. Do not reopen the broader typed-authority convergence synthesis.
- 2026-04-09 live parity rerun:
  treat MP-384/MP-387 F1 as reopened on the current tree. The bounded defect
  is no longer missing coordination models; it is proof-tick
  non-determinism. `startup-context`, `session-resume`, and
  `ControlPlaneReadModel` can still observe different review-state freshness
  on one rerun and diverge between
  `attention:reviewer_supervisor_required` and
  `attention:reviewer_poll_due` (`reviewer_freshness:poll_due`) inside
  `coordination.resync_reasons`. Resume with the repo-owned startup packet as
  authority: freeze one review-state / coordination read per proof tick
  across those surfaces, rerun the focused pytest bundle named there until it
  is green on consecutive runs, then widen again.
- 2026-04-09 guard-intelligence audit absorption:
  do not create a second "guard intelligence" plan. The accepted next slice
  after the reopened F1 runtime parity closure is feedback-loop convergence
  over the existing `Finding`/`DecisionPacket`/`governance-review` stack:
  1) enrich guard-to-`Finding` projection instead of leaving hard guards as
  fixed-severity family-local dicts, 2) add one repo-owned feedback lens over
  `governance-review`, quality-feedback metrics, scope ownership, and graph
  churn so repeated false positives narrow while repeatedly confirmed issues
  harden, and 3) keep any adaptive severity/decision routing advisory or
  `recommend_only` until replay/corpus evidence is strong enough for a
  blocking promotion. Prompt-time failure-rule ledger / bad-pattern recall /
  trust-weighting follow-ons remain under `review_probes.md`; runtime-owned
  guard translation and trust inputs stay here in the main `MP-377` owner
  chain.
- 2026-04-08 typed-authority convergence synthesis absorption:
  do not create or revive a separate umbrella plan. Resume from the declared
  owner-chain order only: Phase 0 mutation/push closure in
  `remote_commit_pipeline.md`; review-state producer, identity, and
  authority-path closure in `platform_authority_loop.md`; read-side /
  bootstrap / prompt convergence in `remote_control_runtime.md`; and
  second-repo proof in `portable_code_governance.md`. Do not call Gate 1 or
  Gate 2 closed until the layered proofs are green: snapshot-identified
  remote-control live proof, post-approval publish smoke harness, read-only
  blocked-fanout review proof, fresh-AI bootstrap proof, and second-repo
  proof.
- 2026-04-09 guard-stack layering review:
  the main diagnosis is now "duplicated and partially-connected typed
  architecture," not "typed architecture missing." Resume from one layering
  rule: package-layout and shim governance stay as structural self-hosting
  pressure, while real architecture closure is measured through mutation
  anti-bypass, authoritative producer cutover, identity parity, read-model
  convergence, schema-first discoverability, and prompt/bootstrap field-route
  parity. `context-graph` / `ConceptIndex` / ZGraph-style logic should start
  as graph-backed probes or ranking reducers over those typed contracts, not
  as a second truth owner or a noisy merge blocker.
- 2026-04-08 coordination projection-divergence review:
  the repo now has enough typed coordination truth to answer who is active,
  what slice is owned, whether fanout is safe, and whether resync is
  required. The remaining product-owned gap is load-bearing projection and
  launcher automation, not another reducer. Resume from this rule:
  `CoordinationSnapshot` may stay the bounded authority packet, but
  `ControlPlaneReadModel`, startup summary/machine-summary, dashboard, and
  repo-owned launch/promotion scope must all consume the same answer so
  remote-control bootstrap does not regress to stale bridge-first work
  selection.
- 2026-04-07 portability-by-default review:
  agree with the review distinction: the repo has the right typed abstraction
  shape (`ProjectGovernance`, repo-pack/path roots, typed startup push
  decisions, path-derived next guard bundles, fail-closed operator mode), but
  shared runtime still carries VoiceTerm-shaped defaults and fallback
  behavior. Resume by making repo-pack/bootstrap mandatory for shared layers,
  adding explicit capability records for optional review-channel/autonomy/
  operator-console/bridge behavior, landing a static portability guard over
  forbidden VoiceTerm literals, and proving a controlled fixture matrix before
  broad external repo trials. Use `SystemCatalog` / contract-closure checks to
  block missing repo-pack/capability bindings in generated projections rather
  than asking Claude/Codex to remember this from prose.
- 2026-04-05 developer-truth-stack implementation review:
  keep the three-layer projection rule, but do not overclaim current closure.
  The repo already has typed startup/session/review packets, yet some visible
  surfaces still compute guidance in renderer code and a few downstream
  consumers still read compatibility markdown as data. The next product-owned
  closure slice is therefore concrete: standardize one shared
  developer-surface packet family, remove markdown-as-data consumers where the
  typed state already exists, and add parity/observed-vs-inferred guards so
  the human-facing sentence stays a projection over machine-owned truth.
- 2026-04-05 typed-structure portability review:
  keep the existing Python architecture guide, but promote the missing runtime
  doctrine into active `MP-377` plan state too. The portable correction is
  not "write every repo like Rust" and not a repo-wide style law. It is a
  governed-boundary rule: platform-owned control/governance paths should move
  stable meaning into typed contracts, closed vocabularies, and explicit
  transitions before falling back to projections or prose. Resume by applying
  that rule to the remaining stringly / dict-shaped / prose-shaped control
  seams without widening it into adopter app-code mandates.
- 2026-04-05 governed semantic-doc projection review:
  the same owner chain now also accepts the stronger docstring idea in bounded
  form. The platform should support structured, machine-validated semantic
  docstrings or symbol-level semantic blocks for selected governance/runtime
  symbols, but only as projection over canonical contracts. Resume by wiring
  this through the existing docs/runtime system instead of inventing a second
  prose authority: `SemanticDocRecord` / `SemanticSymbolRecord` metadata,
  freshness/signature checks, `DocRegistry` / doc-authority visibility,
  context-graph + SystemCatalog discoverability, bootstrap/discover surfacing,
  and drift guards that fail when the semantic doc claims outrun the typed
  contract.
- 2026-04-05 semantic-routing boundary review:
  the user's deeper ZGraph/search-space argument is accepted, but at a more
  precise integration point than "make semantics the runtime spine." Resume
  from this rule: semantics are first-class as the repo's routing/compression
  layer, yet they still sit behind typed continuity and deterministic
  narrowing. The next product-owned closure is therefore to keep
  `session-resume` / `StartupContext` as bootstrap authority, extend
  `SystemCatalog` + `AgentDispatchPacket` into the bounded semantic-routing
  seam, add optional ZGraph-style ranking behind evaluation gates, and prove
  it reduces search without widening authority or weakening closure/parity.
- 2026-04-05 truth-source convergence review:
  the "one backend owns facts, surfaces render them" direction is correct and
  is already partially real in code/docs, but the migration overlap is still
  active. Resume from one explicit closure rule: `ControlPlaneReadModel` and
  reduced packet/state contracts must keep absorbing read-side shaping, while
  `ControlState`, legacy `controller_payload` / `review_payload`, and bridge
  compatibility surfaces remain fallback-only adapters until parity proves
  they can be deleted. Do not let compatibility reducers or markdown bridges
  silently remain second truth owners.
- 2026-04-05 self-hardening boundary review:
  treat the current platform as partially closed-loop, not fully autonomous.
  The repo already has typed startup/work-intake/finding/review/
  quality-feedback surfaces, but the runtime spine is still incomplete:
  `TypedAction -> ActionResult -> RunRecord` is only live in bounded lanes,
  `PlanExpectationPacket` is still planned, escapes still require manual
  `governance-review` absorption, and quality feedback recommends tuning but
  does not promote new policy. Resume from this owner chain by preserving one
  hard boundary: predeclared invariants may auto-enforce, but new invariants
  must route through typed candidate capture, corpus replay, FP/FN evaluation,
  approval, and only then promotion. The next product-owned closure slice is
  to encode that repair-vs-proposal boundary in runtime contracts and owner
  plans before widening autonomy claims.
- 2026-04-04 dashboard v3 consolidated research (8 agents, awaiting Codex review):
  **View flags**: `--view {overview|dev|analytics|audit|codebase|quality|publication|health}`.
  Each view loads only needed artifacts. Default is `overview`. Follows
  `context-graph --mode` pattern. 8 views mapped to concrete artifact sets.

  **Query system**: `--query "probe:NAME"`, `--query "file:PATH"`,
  `--query "worker:W1"`, `--query "finding:F1"`, `--query "since:1h"`,
  `--query "command:check"`. Composable AND conditions. Orthogonal to views.

  **Portability gaps to close**: (1) dashboard hardcodes 16 paths instead of
  using RepoPathConfig; (2) agent names hardcoded to "codex"/"claude" instead
  of role-based discovery; (3) `codex_activity` should be `reviewer_activity`;
  (4) quality gates hardcoded instead of dynamic; (5) no `--bootstrap` command.

  **ASCII charts**: zero-dependency sparklines (`▁▂▃▄▅▆▇█`), bar charts
  (`████`), progress bars, dependency trees — all pure Unicode/Python stdlib.
  Push success sparkline from receipts.jsonl, command frequency bars from
  data_science summary, temperature distribution from graph snapshots.

  **Web integration**: `--format html` via Rich export, `--serve` via stdlib
  http.server, GitHub Actions step summary with Mermaid, GitHub Pages static
  site with AlpineJS, Slack webhook notifications. All zero-config.

  **UX patterns** (from k9s, lazygit, gh-dash, wtfutil): widget-based
  composition, tab switching, 10-60s polling intervals, vim-style nav,
  sidebar drill-down, responsive 80-col layouts, YAML-configurable sections.

  Implementation slices: (1) add `--view` flag with selective data loading,
  (2) refactor paths to use RepoPathConfig, (3) rename codex_activity to
  reviewer_activity with role-based discovery, (4) add sparkline/bar chart
  rendering module, (5) add `--query` filter system, (6) add `--format html`,
  (7) add `--serve` mode, (8) add `--bootstrap` for new repos.

### Current status

- 2026-04-04 `devctl dashboard` v2 architecture plan (awaiting Codex review):
  v1 is landed but under-projects the system. The v2 plan treats the dashboard
  as a platform-level explainable AI surface, not a renderer tweak.

  **Core architecture**: sources → DashboardSnapshot IR → derived truth → renderer

  **4 truth planes** (must be visually separated in the render):
  1. Authority truth — who owns turn, loop mode, review accepted
  2. Execution truth — workers running, what's coding, what's blocked
  3. Publication/evidence truth — HEAD published, post-push green, receipt proof
  4. Narrative/coordination truth — instruction, findings, next action

  **Explainability requirement** (operator teaching surface):
  Every section must explain WHY, not just WHAT. The dashboard turns the black
  box into a transparent reasoning surface:
  - Why did the AI make this change? (link to finding + architectural reason)
  - Why is this approach better? (cite best practice, probe rule, guard rule)
  - What proof exists? (link to test results, guard output, governance review)
  - Plain language summaries a junior dev can understand
  - Expandable detail/drill-down to raw evidence

  **Required sections** (dense multi-column, fits one terminal screen):
  - NOW: owner, next action, top blocker, last change age
  - WORKERS: ID, role, scope, state, age, last update per worker
  - PLAN: current slice, progress (N/M items), open findings, pending items
  - PUBLICATION: effective truth, target match breakdown, why not green, timers
    (preflight Xs → push Xs → post-push Xs), evidence path
  - QUALITY: per-guard pass/fail, top probe findings, cleanup rate, failing file
  - COORDINATION: packet queue counts, instruction rev, poll ages, ack state
  - FLOW: compact ASCII flowcharts (review/worker/push pipelines)
  - TIMELINE: last 10 important events with timestamps
  - EVIDENCE: artifact paths for each truth claim

  **Data sources** (all already exist as JSON, 16 surfaces mapped by 8 research agents):
  - review_channel/latest/compact.json (review state, 13 KB)
  - review_channel/latest/registry/agents.json (worker states)
  - push/latest.json + push/history/receipts.jsonl (publication truth + history)
  - startup/latest/receipt.json (advisory action, push eligibility)
  - probes/latest/summary.json (25 probes, risk hints, hotspots)
  - governance/latest/review_summary.json (121 findings, 56.2% cleanup rate)
  - system_picture/latest/summary.json (section integrity)
  - review_channel/latest/commit_pipeline.json (pipeline state)
  - bridge.md live sections (instruction, verdict, findings)
  - publisher_heartbeat.json + reviewer_supervisor_heartbeat.json (daemon health)
  - audits/devctl_events.jsonl (19,903 events with timing)
  - data_science/latest/summary.json (time-to-green, command frequency)
  - data_science/history/snapshots.jsonl (11,457 snapshots, 25 days of trends)
  - graph_snapshots/ (353 snapshots, temperature evolution)
  - governance/finding_reviews.jsonl (136 review records with evidence chain)
  - autonomy/watchdog/episodes/ (guard execution timing)

  **Semantic colors** (strict palette):
  - green: pass / accepted / published / matched
  - yellow: queued / waiting / caution / partial
  - red: blocked / failed / stale / mismatch
  - cyan: active / running / current owner
  - dim gray: evidence paths / raw artifact fields / secondary text

  **Naming rules** (role-neutral, provider secondary):
  - Primary nouns: Reviewer, Implementer, Worker, Plan, Publication, Quality,
    Health, Evidence, Blocker, Next action
  - Provider as sublabel: "Reviewer: Codex" not "Codex conductor"
  - No internal contract names on main screen (push_enforcement, bridge_liveness,
    current_session → Publication truth, Loop health, Current instruction)

  **Auto-launch** (default behavior, not prompt behavior):
  - review-channel launch → emit dashboard
  - remote-control attach → open dashboard first
  - rollover → write dashboard snapshot
  - --follow → refresh every 5-10s (fast for machine, 3min summary for human)

  **Portability**: DashboardSnapshot schema + repo-pack path resolution. Core
  sections fixed (repo, review, workers, publication, quality, coordination,
  flow). Repo-specific sections plug in via repo-pack config. Missing surfaces
  render as "n/a", never crash. Operator console + mobile reuse same snapshot.

  **Implementation slices** (Codex to review this order):
  1. Promote DashboardSnapshot to `dev/scripts/devctl/platform/dashboard_snapshot.py`
  2. Add source collectors that read all 16 artifact surfaces
  3. Add derived truth layer (effective publication, primary blocker, loop health,
     owner, next action, "what changed recently", explainability summaries)
  4. Rebuild terminal renderer as dense multi-column with semantic colors
  5. Add worker table, plan progress, publication pipeline with timers
  6. Add compact ASCII flowcharts (review/worker/push)
  7. Add timeline (last 10 events from devctl_events.jsonl)
  8. Add evidence section with proof chain
  9. Add --follow with diff-aware refresh
  10. Wire auto-launch into review-channel launch + remote-control attach
  11. Add focused tests for snapshot building, rendering, missing-surface fallback
  12. Update plan docs and AGENTS.md with dashboard contract

- 2026-04-04 extension/adopter closure correction: the latest architecture
  audit is now accepted as tracked `MP-377` work before implementation, not as
  off-plan commentary. The system should borrow Codex/Claude extension ideas
  only as adapters over `devctl` authority, and the concrete closure tranche
  is now explicit: make read-only command surfaces truly no-write-safe, close
  Phase-2 repo-pack/runtime fallback so portable mode fails closed instead of
  inheriting VoiceTerm defaults, generate project-scoped Codex/Claude/MCP
  surfaces from one repo-pack-owned `ExtensionBundle`, and define one typed
  `AutomationSpec` so the same governed task can run under local scheduler,
  GitHub workflow, Codex Automation, or Claude-facing command/agent surfaces
  without creating a second policy engine.
- 2026-04-04 proof-state correction: the current `MP-377` execution branch is
  already published, but it is not yet a fully green proof slice.
  `dev/reports/push/latest.json` records `published_remote=true`,
  `post_push_green=false`, and `reason=post_push_bundle_failed`, and the
  remaining blocker is branch-wide
  `check_code_shape --since-ref origin/develop` debt rather than the recent
  push/system-picture fixes themselves. The accepted next bounded slice is
  therefore current-target publication parity plus explicit shape cleanup/debt
  capture, executed through the sanctioned review-channel topology with
  `--codex-workers 0 --claude-workers 3`.
- 2026-04-03 cross-client source-of-truth follow-up is now explicit in the
  main `MP-377` owner chain. Read-only review across the PyQt6 operator
  console, iPhone mobile app, and Claude remote-loop surfaces confirmed that
  the missing platform layer is still the planned generated
  `system-picture` / generated-report reducer: PyQt6 still rebuilds lane
  state from `bridge.md`, mobile still decodes compatibility-shaped
  `mobile-status` payloads, and remote-loop surfaces still orient around
  bridge/status. The accepted next slice is one bounded orientation contract
  over startup/review/control/governance/external-finding state with both
  managed JSON/Markdown and compact GitHub-visible projections, then client
  migration in the order PyQt6 -> iPhone/mobile -> remote/external-review.
- The follow-up architecture review now tightens that same slice further:
  `system-picture` must carry repo/worktree/service identity,
  `CollaborationSession`, session-capability / worker-fanout state,
  delegated-worker receipts / topology, and stale-write collision controls
  (`writer_lease`, owned worktree/path scope, `expected_revision`,
  `state_hash`) so many-agent clients stay on one backend instead of
  reconstructing lane ownership or authority locally.
- The current clean-tree runtime blocker is explicit too: the repo is not
  blocked on plan sync, it is blocked on reviewer cadence. `reviewer_overdue`
  on a clean tree means detached publisher/reviewer-supervisor runtime still is
  not the missing semantic-review link; the remaining gap is the repo-owned
  persistent Codex reviewer worker/service path that keeps review passes and
  operator-visible checkpoints moving without chat babysitting.
- 2026-04-03 remote commit-pipeline Phase-2 authority follow-up landed in the
  same `MP-377` owner chain: `reviewer_runtime` now owns implementer ACK /
  implementation-block truth, bridge review acceptance no longer falls back to
  prose parsing, and governed push recovery now keys approval identity to a
  reviewer-owned tree receipt instead of raw HEAD equality. The next narrow
  follow-up is Phase 3 ownership/write proof plus live-session validation,
  not another bridge-derived authority patch.
- 2026-04-01 integration-analysis absorption: the accepted missing closures are
  now explicit in canonical plan authority instead of living in
  `dev/intrgrate*.md`. `MP-377` already carried most of the direction, so this
  pass tightened the owner chain around execution-surface ownership routing,
  typed onboarding provenance/ratification, session capability projection, and
  proof-gate language. Release-artifact and supply-chain governance remain
  accepted too, but stay sequenced after the current authority-loop and
  second-repo proof bars instead of pretending to be active `P0`.
- 2026-04-01 self-hosting organization correction: the current guard contract
  is honest about drift but it is still not semantic organization. The live
  tree can report `check_package_layout` clean while `dev/scripts/devctl`
  still holds `80` root Python files, `60` non-shim implementation files, and
  `13` non-shim `*_parser` modules. The next closure is therefore explicit:
  `MP-376` owns the portable package-role/package-cohesion policy and report
  surface, while `MP-377` owns projecting that truth into startup/work-intake
  so agents stop confusing budget compliance with architecture completion.
- 2026-04-01 runtime-contract follow-up continued in the same owner chain:
  review-channel launch/session metadata now derives from typed provider/lane
  specs, event-backed packet validation resolves actor/target ids from typed
  collaboration/runtime state or repo-owned session metadata instead of
  parser hardcodes, and `check_multi_agent_sync.py` now blocks
  planned-topology/runtime-truth leakage when typed `review_state` exists.
  The architecture gap is narrower but still open: native delegated worker
  execution and the last fixed-provider recovery/worker-budget seams are not
  done yet.
- 2026-04-01 runtime-contract follow-up landed in the same owner chain:
  `ReviewState` now carries a typed `CollaborationSession` block instead of
  leaving live collaboration truth split between bridge/provider hints and
  synthetic registry rows. The review backend now records live conductor
  participants from repo-owned session metadata, keeps delegated planned-lane
  receipts separate from those live participants, and projects
  `registry/agents.json` from that runtime contract instead of rebuilding
  provider state ad hoc in each emitter. This closes the first native session
  contract seam the architecture plan called for, but launch and packet
  routing still carry fixed provider ids and the typed worker-topology guard
  is still outstanding.
- Current blocking separation tranche:

| Outcome | Owner doc | Exit condition |
|---|---|---|
| Product-doc vs AI-system-doc boundary | `dev/active/platform_authority_loop.md` | `DocPolicy` / `DocRegistry` plus artifact-role/scope classification keep VoiceTerm end-user docs product-only and route AI-system guidance into self-hosting, adopter, or generated surfaces |
| Fail-closed portable authority | `dev/active/platform_authority_loop.md` | portable runtime/startup/docs consumers stop reviving VoiceTerm filenames or paths from partial payloads; repo-pack/bootstrap owns repo-local defaults |
| Publish truth | `dev/active/platform_authority_loop.md` | `devctl push` reports `published` separately from `post-push green`, and unrestricted bypass flags are removed or policy-gated |
| Adopter proof | `dev/active/portable_code_governance.md` | custom-layout, no-bridge, and optional-capability repos stay green without core-engine edits |

- Directory rule for this tranche: do not flatten the repo into one catch-all
  directory. The target layering remains `governance_core`,
  `governance_runtime`, `governance_adapters`, `governance_frontends`,
  `repo_packs`, and `product_integrations`, with VoiceTerm only in
  `product_integrations`.
- 2026-03-27 consumer-refresh follow-up landed: the same authority-closure
  lane now refreshes the bridge-backed typed review-state projection before
  startup/tandem/push consumers read live `current_session` or review
  freshness. That keeps stale `latest/review_state.json` snapshots from
  outranking the repo-owned status writer while `bridge.md` remains a
  compatibility projection. The next same-lane work narrows to
  writer/mutation authority, the last bridge-text-only tandem checks, and the
  separate governed-push publish-vs-post-push truth contract.
- 2026-03-28 publication-cadence closure landed in the same owner chain:
  governed push cadence is now policy-backed typed runtime state instead of
  surface-local prose. `PushEnforcement` computes the shared publication
  backlog once, `PushDecisionState` projects it for operator and AI guidance,
  and startup plus review/status surfaces now render that same typed result.
  Keep the next step narrower than a general recovery merge: broader bridge,
  checkpoint, and review recovery composition should build on top of this
  contract in a later continuation-decision slice.
- 2026-03-29 review-channel authority follow-up landed in the same owner
  chain: the real Claude ACK false-stale failure is now closed on a typed
  contract instead of one bridge-only token. A new shared review-channel ACK
  helper accepts semantic phrasings such as `Acknowledged instruction revision
  <rev>` alongside the legacy `instruction-rev:` form, bridge-backed
  `current_session` now computes instruction revision / ACK revision /
  ACK-state from that shared parser instead of taking those machine fields
  downstream from ad hoc bridge liveness text, bridge-backed `bridge-poll`
  refreshes and prefers the typed `review_state` snapshot for live
  instruction/ACK authority, and compatibility bridge rendering now prefers
  typed current-session sections for machine-deciding live fields instead of
  reparsing the old bridge section bodies. Remaining same-lane follow-up is
  still broader than ACK wording: reviewer-owned prose sections
  (`Poll Status`, `Current Verdict`, `Claude Questions`) and richer wait/block
  reasons still need the planned `DecisionTrace` / typed writer-authority
  cutover before bridge prose fully stops being the live authoring surface.
- 2026-03-31 live-authority follow-up landed in the same owner chain: typed
  review-channel status now carries `effective_reviewer_mode` beside declared
  bridge `reviewer_mode`, demoting dead `active_dual_agent` runtime to a
  read-only inactive authority state when typed `launch_truth` proves the
  loop is no longer live. Startup reviewer-gate detection plus the bounded
  reviewer/implementer wait helpers now consume that effective mode first,
  while the declared bridge mode stays intact for provenance and review-gate
  semantics. The next same-lane follow-up is widening remaining live-authority
  consumers away from declared bridge mode where they still read it directly.
- 2026-03-31 startup-repair parity follow-up landed in that same owner chain:
  the repo-owned `startup-context --repair` adapter now carries the governed
  review-channel `rollover_dir` sibling when it dispatches safe local
  review-channel actions, so the refactored bridge-backed status/ensure path
  no longer crashes on missing runtime paths before it can classify a
  `runtime_missing` loop. This keeps the repair controller on the typed
  runtime-authority path instead of reopening manual operator translation as
  the de facto fallback.
- 2026-04-03 reviewer-bootstrap receipt follow-up landed in the same owner
  chain: startup receipt freshness is now intent-aware instead of assuming
  every guarded action is another implementation slice. Repo-owned
  `review-channel --action launch|rollover` keep the same fail-closed branch,
  checkpoint-budget, and non-reviewer-authority boundaries, but plain HEAD
  drift only blocks reviewer bootstrap when the diff since the receipt touches
  guarded quality-scope roots. Implementation and push authority keep exact
  HEAD binding.
- 2026-03-27 startup-model discoverability follow-up landed: the compiler-
  style governance framing that had been buried here and in local scratch
  notes is now carried by tracked first-hop dev/agent surfaces too.
  `AGENTS.md`, `dev/guides/AI_GOVERNANCE_PLATFORM.md`, and the generated
  `CLAUDE.md` source now all say explicitly that the AI is a probabilistic
  proposer inside repo-owned deterministic passes. The next same-lane work
  stays on startup/work-intake authority and actuator closure, not more
  architecture theory.
- 2026-03-27 authority-closure tranche 1 landed: typed startup authority now
  uses the governed `review_state.json` path or fails closed instead of
  trusting `bridge.md` prose, and `ProjectGovernance` doc/plan entries now
  carry `artifact_role`, `authority_kind`, `system_scope`, and
  `consumer_scope` so default warm refs can suppress compatibility
  projections and lane-specific docs. Fixture proof now covers both
  custom-layout and no-bridge repos. Keep the next slice in the same lane:
  extend explicit repo-pack/capability gating, finish broader doc-authority
  compression, and keep governed-push/Ralph follow-ups separate from graph or
  memory expansion.
- 2026-03-27 shared-backlog intake landed: the same owner chain now treats a
  repo-pack-configured shared backlog doc as governed intake visible to
  startup/work-intake while keeping execution authority in
  `dev/active/MASTER_PLAN.md` plus the owning active plan. Humans and AI can
  share one backlog file without reopening the old hidden-backlog problem.
- 2026-03-27 current priority lock: treat the next `MP-377` work as one
  bounded architecture tranche, not as a general cleanup bucket. The active
  focus is self-hosting authority compression plus governed-push integrity.
  Stay in this lane until four outcomes are true in repo-visible state:
  `DocPolicy` / `DocRegistry` bound the startup/read markdown surface,
  development-self-hosting docs are cleanly separated from portable
  adopter/bootstrap surfaces, portable runtime/startup no longer revive
  VoiceTerm filenames from partial payloads, and governed push reports
  "published" separately from "post-push green" with no unrestricted bypass
  path left in the canonical workflow.
- 2026-03-27 sequencing correction: the current dirty branch already contains
  a bounded docs-authority / publish-truth tranche ahead of the blocker
  queue. Finish that tranche honestly, checkpoint it, and then return to the
  blocker hardening order recorded in `MASTER_PLAN` instead of silently
  treating the out-of-order work as the new universal sequence.
- 2026-03-27 deterministic-validation follow-up: once the current docs/
  authority/push tranche is clear enough to widen, resume from portable
  trust-token closure rather than generic test enthusiasm. The next same-lane
  design is a runner-agnostic validation-contract family (pytest first),
  a `FailurePacket`/failure-case -> canonical `Finding` seam, executable
  `validation_plan` routing, and scoped autonomy upgrades only when the exact
  finding-owned validation plan passes. Keep this separate from advisory
  test-quality probes and reject repo-wide coverage-threshold shortcuts.
- 2026-03-28 recurrence-closing governance follow-up: treat the just-cleared
  release-maintenance/import-shim miss as the bounded template for the next
  `MP-377` self-hosting slice. Finish the concrete escape, then encode the
  class-level mechanism instead of widening into "fix everything related":
  1) make DRY/composition contracts explicit and require declared parameters
  to affect behavior, 2) treat metadata-driven shim redirects as authority
  data with repo-root plus file-exists validation, 3) treat moved commands/
  checks/shims as one declared-surface parity class that must prove script
  mode, package mode, and public CLI/root-entrypoint reachability, and
  4) define one typed closure workflow for escaped findings
  (`classify -> prevention surface -> regression proof -> record closure`).
  Expand only across equivalent instances governed by the same contract, not
  by loose family resemblance. Keep `commands.governance.hygiene` callable
  adapters plus `REPO_ROOT` synchronization marked as bounded compatibility
  debt until that seam has a cleaner long-term shape.
- 2026-03-28 publication-cadence closure landed in the same `MP-377`
  authority lane: `repo_governance.push.publication` now declares the backlog
  thresholds, `PushEnforcement` computes the typed publication state once, and
  `PushDecisionState` carries the shared guidance so startup, review-channel
  status, and startup/context renderers stop inventing separate push wording.
  The next same-lane work stays bounded: broader checkpoint/review/bridge
  recovery composition should consume this shared cadence contract later
  instead of widening this first patch into a second recovery state machine.
- 2026-03-28 docs-check hot-path closure: the governed push replay exposed a
  real `docs-check --since-ref` miss where path-level helpers kept rebuilding
  docs/governance policy for each changed file. The instance fix is a
  per-repo/per-policy-path resolver cache plus regression coverage; the
  class-level rule is "governance scans may be expensive, but path predicates
  must consume one resolved contract instead of rescanning authority inside
  loops."
- 2026-03-29 package-layout baseline-debt enforcement: `check_package_layout`
  now supports `--fail-on-baseline-debt` with optional `--baseline-debt-root`
  filtering. The tooling and release bundles enforce
  `dev/scripts/devctl/commands` as a hard-blocking root, closing the gap where
  92 files (max 48) and 7 crowded families silently passed default CI. The
  same guard uses `getattr` with safe defaults so compatibility callers and
  existing mock-based tests are not broken by the new flag surface. Focused
  tests cover targeted-root enforcement, non-matching-root passthrough,
  flag-disabled passthrough, unfiltered all-roots enforcement, and rendered
  markdown output. This completes the ratchet path described in `MASTER_PLAN`
  2026-03-27: truthful baseline-debt reporting now drives hard enforcement on
  the primary self-hosting hotspot.
- 2026-03-29 package-layout dirty-diff refinement: the first live
  review-channel conductor run after that ratchet showed a narrower workflow
  bug. Filtered `--fail-on-baseline-debt` was still hard-failing dirty
  worktrees whose changed paths did not touch the targeted root, which made
  bridge-only/local tooling loops look permanently red on unrelated debt.
  The guard now preserves clean-worktree/adoption-scan hard enforcement for
  selected roots, but filtered dirty working-tree and commit-range runs only
  block when the current diff actually touches the targeted root. That keeps
  the `dev/scripts/devctl/commands` convergence rule meaningful without
  collapsing all non-command tooling passes into repo-wide debt failures.
- 2026-03-29 startup thesis bootstrap landed: `startup-context` now renders a
  bounded `## Why Stack` section from `dev/config/why_stack.md` before
  SOP/router detail, so fresh sessions see the product mission, proof
  obligation, platform boundaries, and current priority before descending
  into process. The next same-lane closure stays narrow: keep generated
  bootstrap surfaces carrying that same client-vs-core boundary explicitly
  instead of implying it from one repo's defaults.
- 2026-03-27 scope-capture follow-up: preserve the external architecture
  intake in repo-visible plan state instead of letting it live only in chat or
  ad hoc markdown. The same-lane additions are now explicit: keep
  `bridge.md`/latest/chat/status as projections over typed
  `current_session` plus `DecisionTrace`, add `explain-latest`, treat
  validation/test failures as one governed evidence family rather than the
  whole autonomy story, and later compile `PlanTargetRef` into
  `PlanExpectationPacket` so plan truth is reconciled against observed
  evidence without letting runtime drift silently become authority.
- 2026-03-27 foundation-first follow-up: keep the strategic features tied to
  their supporting substrate in plan state. The same lane now explicitly
  includes `REPO_ROOT` injection burn-down, git/filesystem adapters and
  repository seams, typed governance ledger rows, a bounded
  `GovernanceFinding` aggregate, live `validation_plan` execution, failure
  adapters, contract-test markers, strict boundary models, and focused
  boundary-contract suites so future AI sessions do not try to build
  `DecisionTrace` or plan-reconciliation features on top of unstable
  foundations.
- 2026-03-27 docs-boundary correction: a live self-hosting miss showed the
  repo still responds to AI-system review/startup/operator changes by trying
  to teach them through VoiceTerm end-user docs. That is the wrong repair.
  The next organization pass must pull those instructions back into the
  `MP-377` owner chain, maintainer docs, and generated operator/bootstrap
  surfaces, then finish docs-policy classification so product docs,
  development-self-hosting docs, portable adopter docs, and compatibility/
  generated surfaces are different governed classes instead of one markdown
  bucket.
- 2026-03-27 external-review translation follow-up: preserve one constitution,
  but translate it into the repo's actual architecture instead of flattening
  it. The machine truth remains `ProjectGovernance` plus generated
  `project.governance.json` (or equivalent typed materialization), typed
  registries, and runtime receipts; the reviewed `project.governance.md`
  contract remains the human mirror; generated AI/bootstrap surfaces remain
  projections; and the next closure should add explicit artifact-role/scope
  classification so startup can distinguish platform-core, repo-pack/client,
  development-self-hosting, evidence, and compatibility/generated surfaces
  without rereading broad prose. That same closure now also explicitly owns
  startup-order/warm-ref suppression for non-matching doc classes, mixed-doc
  split/suppression where temporary VoiceTerm operating-mode prose still sits
  beside reusable contract text, and the remaining config-driven registry
  migration for guard/probe/bundle/provider routing so the constitution is
  executable instead of aspirational.
- 2026-03-27 self-hosting compression follow-up: the next `MP-377` slice is
  not another universal-plan memo. It is the executable compression pass that
  proves this repo can follow the same governance contract it wants external
  repos to adopt. Current repo-owned measurements are now part of the owner
  state: `doc-authority` reports `50` governed docs / `45,107` lines,
  `19` budget violations, `4` authority overlaps, and `8` consolidation
  candidates; `check_package_layout` still reports four crowded roots and
  seven crowded namespace families under the `devctl` stack, and repo policy
  now ratchets touched files in those self-hosting hotspots to `strict`
  instead of freeze-only drift control. The same guard now also emits
  compatibility redirects from valid `shim-target` metadata so moved
  entrypoints resolve through one portable package-layout surface rather than
  chat memory. Resume from one bounded tranche:
  absorb root intake conclusions into the owner chain,
  shrink the active authority surface through `DocPolicy` / `DocRegistry`,
  separate development-self-hosting docs from adopter/bootstrap surfaces, and
  keep portable runtime/startup blind to VoiceTerm filenames unless repo-pack
  policy explicitly names them.
- 2026-03-27 package-layout truth follow-up: the current self-hosting miss was
  not that `check_package_layout` lacked crowded-root detection; it was that
  freeze-mode reporting could still read as "green" in day-to-day work because
  `ok` only tracked blocking violations. The same guard surface now emits
  explicit baseline-debt state (`status=baseline_debt_detected`,
  `layout_clean=false`) whenever crowded roots/families remain under freeze
  mode. Keep this architecture rule explicit: one `package_layout` system owns
  both blocking drift and baseline organization debt. Do not answer this by
  inventing a second crowding checker; the next follow-up is bounded
  decomposition plus selective ratcheting of crowded roots/families to
  stronger enforcement once those namespaces are actually compressed.
- 2026-03-27 package-layout self-hosting validation follow-up: the same
  portable direction exposed a narrower proof miss in the repo's own coverage
  story. The rule-loading extraction into
  `dev/scripts/checks/package_layout/rule_resolution.py` was the right
  architecture, but the paired support tests were still targeting the old
  `support.py` seam and therefore failed after the refactor even while the
  public command-level package-layout checks stayed green. The immediate fix
  stays at the test boundary; the tracked owner follow-up is that
  package-layout/internal engine refactors must keep the support-level suite
  in routed default validation so self-hosting proof stays aligned with the
  canonical seam rather than only the external command surface.
- 2026-03-27 governed-push follow-up: the platform now has the intended
  fail-closed branch-push truth for this tranche. `repo_governance.push`
  policy now gates skip-flag bypasses, and `devctl push` emits typed stage
  truth that distinguishes validation readiness, remote publication, and
  post-push green instead of collapsing them into one generic success claim.
- 2026-03-28 governed-push recovery follow-up: stage separation alone was not
  enough. The platform also needs eager publication evidence plus stale-view
  override rules, because a successful remote push can leave local upstream
  divergence looking ahead until the next fetch. `devctl push --execute` now
  writes a `published_remote` snapshot immediately after `git push` succeeds
  and startup recovery treats a matching current-branch/current-HEAD artifact
  as canonical publication truth while post-push follow-up finishes.
- 2026-04-04 publication-target parity follow-up: that recovery contract now
  needs projection honesty too. The same managed latest-push artifact must be
  interpreted against the full current publication target, not only branch
  text: current branch, current HEAD, reviewer-approved target identity when
  present, and the tracked upstream/default remote. Startup/status markdown
  now renders effective current-target truth instead of stale raw receipt
  booleans, and event-backed review-state enrichment carries the same push
  enforcement / push decision parity rather than leaving publish truth as a
  bridge-only projection detail.
- 2026-03-27 repo-entrance and dev-loop correction: keep the current repo
  split by audience instead of trying to make one README do two jobs. The
  root `README.md` remains the VoiceTerm product entrypoint while `MP-377`
  now explicitly owns a separate platform/developer entry surface inside this
  monorepo, and the same lane now also owns a bounded-implementer workflow
  surface where the human/operator stays session authority while the coding
  agent returns a deterministic slice packet (`goal`, changed files, why,
  checks, open risks, next step) for outside review. The matching
  architecture rule is also explicit now: typed state is the brain,
  bridge/chat/latest/status are projections, and `DecisionTrace` plus typed
  `current_session` is the right owner chain for future explain/audit
  surfaces rather than another planning memo.
- 2026-03-27 plan-driven swarm follow-up: future Codex-review / Claude-code
  swarms must be derived from plan authority instead of static file buckets.
  The accepted execution model is explicit: `startup-context` selects
  `PlanTargetRef`, `PlanExpectationPacket` compiles the slice contract, the
  conductors derive bounded `DelegatedWorkPacket` lane assignments from that
  contract, and workers stay inside owned targets/worktrees/commands while
  Codex keeps final review authority. Static 8+8 lane tables remain capacity
  planning examples, not permanent role truth. Early adopter smoke work is
  acceptable only as a bounded feedback lane while blocker/P0 foundation work
  continues; official cross-repo proof still stays in the later Phase-7 owner
  lane.
- 2026-03-27 same-lane hardening follow-up: the explainability rollout also
  confirmed the current self-governance blind spot. A local cleanup could
  still satisfy code-shape while weakening typed authority by routing fixed-
  field startup decisions through `object` + `getattr`, and the review-channel
  status surface could still project `checkpoint_required` while
  `active_dual_agent` truth was already invalid because no repo-owned Codex or
  Claude conductors were live. The bounded repair stays inside the same owner
  chain: restore direct typed `PushEnforcement` consumption on startup
  decision helpers, teach `probe_design_smells` to catch first-parameter and
  multiline `: object` seams, and make review-channel attention surface
  `bridge_contract_error` ahead of checkpoint advice when authority-source
  integrity is already red.
- 2026-03-27 explainability/learning-path correction: keep the next
  human-facing clarity slice inside the same owner chain. The right fix is
  not open-ended "AI reasoning" prose; it is typed `DecisionTrace` plus one
  small schema-validated decision-record vocabulary rendered into plain-
  language explanation views. Pair that with one platform-owned Python
  architecture guide/decision tree for `dict` vs `TypedDict` vs `dataclass`
  vs boundary-validation models, `Protocol`, composition, repository/service/
  unit-of-work, and dependency injection. Treat Cosmic Python (Ch. 1-6, 8,
  13), the official typing docs, Pydantic strict-mode/JSON Schema, and
  FastAPI boundary-model docs as the starter study spine, while keeping
  Pydantic scoped to untrusted or serialized boundaries instead of making it
  the default internal runtime model.
  Keep the rollout split explicit: the full provenance-grade `DecisionTrace`
  family remains in the existing `platform_authority_loop` Phase-5b lane, but
  the first operator-facing wins should land sooner by extending
  `DecisionPacketRecord`, routed bundle-selection receipts, and probe packets
  with match evidence, practice-linked why text, plain-language metric
  explanations, and context-graph/query relevance summaries.
- 2026-03-27 explainability tranche landed: the first low-cost explanation
  rollout now exists on the typed surfaces already in use. Startup/task-router
  / workflow-profile receipts and startup push decisions now carry
  `rule_summary`, `match_evidence`, and rejected-rule traces; canonical probe
  packets reuse `SIGNAL_TO_PRACTICE` plus plain-language metric explanations
  for `fan_in`, `fan_out`, `bridge_score`, and hotspot rank; context-graph
  query/bootstrap renders now explain why nodes matched and ranked; and the
  durable Python modeling/composition guide now lives in
  `dev/guides/PYTHON_ARCHITECTURE.md`. Keep the split explicit: this is the
  bounded output-layer rollout, while the provenance-grade `DecisionTrace`
  family remains queued in the existing Phase-5b lane under
  `platform_authority_loop.md`.
- 2026-03-26 doc-authority/organization follow-up: do not treat archive or
  deletion as the first cleanup move. The current repo still carries 27
  `dev/active/*.md` docs and 10 root-level markdown entrypoints, and some of
  the root evidence companions still hold conclusions that have to be audited
  against the tracked owner docs before they can move. The next `MP-377`
  execution slice is therefore absorption-first: mirror execution-relevant
  conclusions into the active authority chain, then demote/archive only the
  docs that truly remain reference-only.
- 2026-03-26 portability-audit follow-up: the broad architecture concern is
  confirmed. The blocker is not just one stale `bridge.md` consumer; the
  larger issue is that the platform still lets missing portable authority
  silently collapse back to VoiceTerm defaults in typed governance models,
  repo-pack accessors, review-channel prompts, and generated AI bootstrap
  text. The next execution slice is now explicit: remove silent
  VoiceTerm-default authority from portable runtime mode, make generated
  AI/bootstrap/review instructions render from repo-pack/governed state, add
  a static portability-drift guard, and prove the same flow on non-VoiceTerm
  fixture repos before calling the system portable.
- 2026-03-25 reviewer-loop fail-closed follow-up: the first stale-reviewer
  architecture gap is now closed as code, not just operator guidance.
  `review-channel` status/attention now treats blank reviewer-owned
  `Poll Status` plus stale/missing Claude ACK as a hard bridge-contract
  error, the Poll Status rewriter no longer buries reviewer notes under blank
  padding, and startup-authority now carries an explicit implementation block
  so reviewer-side mutation paths fail closed in active dual-agent mode unless
  intentionally overridden. The same lane now also has the first bounded
  stale-implementer recovery primitive: attention emits
  `implementer_relaunch_required`, `review-channel --action recover
  --recover-provider claude` replaces only the stale Claude conductor, and
  reviewer-follow escalates repeated unchanged stale-implementer state through
  that repo-owned path instead of a full-loop restart. The remaining `MP-377` closure is the broader
  typed `current_session` / `ReviewState` cutover: more runtime consumers
  still need to stop depending on bridge prose for live freshness and
  continuity, and repo-owned reviewer runtime keepalive still has to prove the
  loop stays alive without manual babysitting.
- 2026-03-23 startup-intake follow-up: the first live startup-family proof is
  now real instead of remaining plan-only architecture. `PlanRegistry`
  entries carry parsed `SessionResumeState`, `startup-context` now emits a
  bounded `WorkIntakePacket` with the selected `PlanTargetRef`, typed
  continuity reconciliation, warm refs, and routing hints, and startup now
  consumes live `startup_order`, `workflow_profiles`, and
  `command_routing_defaults` instead of leaving those governance fields
  report-only. The next closure here is wider adoption/hardening:
  `CollaborationSession`, more runtime consumers, and the validation-
  freshness / raw-push policy gaps already called out in the active plan.
- 2026-03-23 startup-authority enforcement follow-up: the platform no longer
  leaves the repo-owned startup path on an instruction-only honor system.
  `startup-context` is now the explicit Step 0 gate in repo process docs,
  generated bootstrap surfaces, and review-channel conductor bootstrap text;
  it persists a managed `StartupReceipt` under the repo-owned reports root
  derived from live governance/path-root authority; and scoped repo-owned
  launcher/mutation `devctl` paths now require a fresh receipt plus a live
  startup-authority pass before starting another implementation or launcher
  slice. The remaining gap here is narrower but still real: raw interactive
  provider sessions can still skip Step 0 until a supported hook/wrapper
  entry path exists, and raw git/pre-commit plus wider repo-pack activation
  still remain open, not the old repo-owned-launcher loophole.
- 2026-04-10 startup-gate receipt-type fix: `_is_repair_launch` in
  `startup_gate.py` was treating `StartupReceipt` as a dict via `.get()`,
  crashing the `repair_reviewer_loop` → `launch`/`rollover` path. Fixed to
  read `receipt.advisory_action` typed attribute and handle `None` receipts.
- 2026-03-27 startup-summary follow-up: the same startup-authority lane now
  compresses the human Step 0 projection without weakening authority. The
  default AI-facing bootstrap command is `startup-context --format summary`,
  which emits a compact four-line receipt (`action`, `reason`, `blockers`,
  `next`) while the typed JSON payload plus managed `StartupReceipt` keep
  writing under the repo-owned reports root. Generated bootstrap surfaces,
  review-channel conductor bootstrap text, and bridge startup instructions now
  all use that summary path so the next startup/relaunch consumes less prompt
  budget before any deeper `context-graph` expansion. The same lane now makes
  the chat/output boundary explicit too: bootstrap details stay in repo-owned
  artifacts or terminal output by default, while chat acknowledgements should
  stay concise unless the operator asks for the fuller packet.
- 2026-03-24 review-state locator follow-up: another repo-pack activation
  leak is now closed on the same startup-authority lane. The remaining typed
  review-state consumers behind startup/tandem continuity no longer each
  hardcode one VoiceTerm report path; `startup-context`, startup
  `WorkIntakePacket` routing, and `check_tandem_consistency` now share a
  repo-pack-aware review-state resolver that honors candidate-path authority
  instead. The remaining gap is broader migration of review-state/event
  consumers plus the still-separate raw git/pre-commit bypass.
- 2026-03-23 Part-53 hardening follow-up: the live `ContextGraphDelta`
  path is no longer relying on unstable host metadata. Snapshot selection now
  orders `latest` / `previous` by embedded capture time instead of filesystem
  `mtime`, direct-path trend scans ignore non-snapshot sibling JSON instead of
  crashing on mixed directories, and delta/trend anchors normalize snapshot
  refs to portable store-relative paths when the artifacts live under the
  canonical snapshot root. The next graph work should widen capture/consumer
  coverage, not reopen this correctness seam.
- 2026-03-22 implementation follow-up: `governance-review --record` now emits
  a typed `FindingReview` v2 row for new adjudications and requires bounded
  architectural-disposition fields (`finding_class`, `recurrence_risk`,
  `prevention_surface`, `waiver_reason` when applicable). The adjacent
  `check_governance_closure` guard now validates the latest v2 review rows
  while keeping legacy rows readable during the migration window. The next
  closure here is automatic runtime recording from guard/review/autonomy
  flows, not more schema invention.
- 2026-03-22 protocol follow-up: the plan now makes architectural absorption a
  required completion rule, not just a review habit. The next enforcement work
  is to encode that as a bounded finding-disposition contract so important
  issues cannot close as patch-only without an approved prevention surface or
  explicit waiver.
- 2026-03-22 evidence follow-up: Parts 45 and 47 from
  `UNIVERSAL_SYSTEM_EVIDENCE.md` are now explicit in the platform plan. The
  next runtime closure here is not new reporting architecture; it is wiring
  already-written operational artifacts into real decision surfaces and
  landing the first missing graph edges/node families so the graph answers
  runtime questions instead of staying escalation-only.
- 2026-03-22 tranche-2 follow-up: the first live `ai_instruction` wire is now
  real in Ralph. The runtime reads canonical probe findings from
  `review_targets.json`, matches them to the current CodeRabbit file slice,
  and injects the resulting guidance into the live remediation prompt with
  deterministic tests. Keep the closure sequence explicit: tranches 2-4 stay
  on direct contract wires, meta-guards, and startup/session authority;
  ZGraph remains optional context help there and becomes a required execution
  substrate only once `EDGE_KIND_GUARDS` / `EDGE_KIND_SCOPED_BY` plus wider
  graph consumers land.
- 2026-03-22 tranche-3 follow-up: the first produced-but-never-consumed
  meta-guard is now real in the platform-contract lane. The closure guard runs
  a synthetic `Finding.ai_instruction` route proof through the real Ralph
  consumer path and fails if a populated probe artifact no longer reaches the
  live remediation prompt. The next closure is not another generic audit; it
  is extending the same route-closure pattern to the remaining autonomy,
  review-channel, and `guard-run` AI guidance consumers.
- 2026-03-22 tranche-4 follow-up: the next AI consumer is now live too.
  `triage-loop` persists one bounded structured backlog slice, `loop-packet`
  reads canonical `review_targets.json` guidance against that slice, and the
  autonomy loop draft now carries the matched `Finding.ai_instruction` text
  instead of generic unresolved-count prose only. The route-closure guard was
  widened in the same change, so the platform-contract lane now proves both
  Ralph and autonomy before the broader meta-guard/general-consumer tranche.
- 2026-03-22 adoption follow-up: external review after tranches 1-4 showed
  that the current branch proved guidance transport before guidance use. That
  follow-up is now partially closed: Ralph states the probe-guidance rule
  before the findings list, autonomy prompts do the same, escalation packets
  now render `## Probe Guidance` plus stable `guidance_refs`, review-channel /
  conductor and swarm prompt surfaces inherit the same packet contract, and
  `governance-review --record` can now capture `guidance_id` /
  `guidance_followed`. The remaining gap is impact measurement and the last
  `guard-run` consumer path, not another architecture layer.
- 2026-03-22 tranche-5 follow-up: closed the first full declared
  `Finding.ai_instruction` consumer family instead of leaving `guard-run` as
  an unchecked tail. `guard-run` already carried canonical probe guidance on
  the live branch, and this slice made the contract lane prove it: the
  platform-contract guard now runs route proofs for Ralph, autonomy, and
  `guard-run`, then fails again at the family level if any declared consumer
  disappears. The remaining closure here is widening that meta-guard to
  dual-authority consumers, prose-parsed structured routing, and the carried
  decision-semantics fields that still stop at human-facing packets.
- 2026-03-22 checker-gap follow-up: an external architecture review surfaced
  the next governance miss after the Ralph cleanup. The live branch had
  already removed the dual-authority Ralph fallback and split the worst
  tactical module seam, so those specific complaints were stale against the
  current code, but the review still exposed two real blind spots the checker
  stack must own: no deterministic rule yet flags dual-authority artifact
  consumers, and `probe_stringly_typed` stays quiet on prose-parsed
  structured-contract matching. Accepted follow-up: keep this in the `A27`
  hard-guard tranche and require targeted post-fix probe reads so the repo
  can distinguish "stale complaint" from "real silent miss" before closure.
- 2026-03-22 evidence follow-up: Part 53 is now explicitly mapped into the
  graph lane too. The current graph tranche is no longer only missing
  edges/node families; once the direct closure tranches are stable it also
  owns deterministic save/diff/trend graph snapshots so the platform can
  answer architecture-drift questions over time with the same cited graph
  surface instead of a parallel audit stack.
- 2026-03-22 governance follow-up: an external design review did surface a
  real detector gap, but it was narrower than the first report claimed. The
  current branch no longer has Ralph negotiating between `review_targets.json`
  and `review_packet.json`, and the guidance code is already split instead of
  living in one junk-drawer module. The real miss is that the remaining
  summary-string compatibility fallback is still invisible to
  `probe_stringly_typed`, and there is no dedicated authority-source-integrity
  check yet for AI consumers. Accepted follow-up: extend the tranche-3/4
  closure stack so single-authority consumer contracts and prose-derived
  routing fallbacks fail inside the platform lane before external review has to
  point them out.
- 2026-03-22 evidence follow-up: Parts 42-43 from
  `UNIVERSAL_SYSTEM_EVIDENCE.md` are now explicit here instead of living only
  in reference prose. The next `MP-377` implementation slice should route the
  fresh `dev/reports/**` operational artifacts into live prompt builders and
  promote the graph from escalation-only context help into bounded
  decision-routing by landing real `EDGE_KIND_GUARDS` /
  `EDGE_KIND_SCOPED_BY` edges plus non-escalation consumers.
- 2026-03-22 graph-edge follow-up: the first typed relation-family slice is
  now real in code. `context-graph` emits `EDGE_KIND_GUARDS` edges from the
  active quality-policy guard registry plus repo scope roots, and it emits the
  first policy-backed `EDGE_KIND_SCOPED_BY` edges from docs-policy tooling
  prefixes tied to canonical plan docs. This keeps the graph generated-only while
  letting file/path queries answer guard-coverage and plan-ownership questions
  from canonical policy/plan inputs instead of raw import adjacency alone.
- 2026-03-22 Part-53 slice-1 follow-up: the first temporal graph-snapshot
  capture path is live too. `devctl context-graph` now writes a typed
  `ContextGraphSnapshot` artifact under `dev/reports/graph_snapshots/` at the
  end of bootstrap runs and when `--save-snapshot` is requested on other
  modes, carrying commit/branch/time metadata, full node/edge payloads,
  kind counts, and a bounded temperature-distribution summary. That keeps the
  next diff/trend tranche on the same canonical graph contract instead of a
  separate temporal-analysis stack.
- 2026-03-23 Part-53 slice-2 follow-up: saved snapshots are no longer
  write-only. `context-graph --mode diff --from ... --to ...` now resolves
  saved artifacts back into typed `ContextGraphSnapshot` state, emits a typed
  `ContextGraphDelta` with added/removed/changed nodes and edges plus
  temperature/edge-kind deltas, and reports a rolling trend window so the
  graph lane can answer "hotter/cooler/stable" and cycle-count drift without
  inventing another analysis stack. Next Part-53 work is checkpoint/CI
  capture widening and richer drift heuristics, not base diff/trend wiring.
- `dev/active/ai_governance_platform.md` is the only main active plan for this
  product scope; companion docs now route back here instead of acting like peer
  execution authority.
- Session-level "where we left off" state belongs in this file's `Session
  Resume` and `Progress Log`, not in the future structured audit/database
  ledger.
- Repo docs-governance now enforces that platform-scope tooling/policy/runtime/
  extraction changes must update this plan through the policy-owned
  `docs-check` rule in `dev/config/devctl_repo_policy.json`.
- The docs-check implementation was refactored into
  `dev/scripts/devctl/commands/docs/` so the enforcement path now passes the
  repo's own shape/complexity/parameter-count/dict-schema guards.
- The repo already has structured machine-readable ledgers for runtime
  evidence: `dev/reports/audits/devctl_events.jsonl` for command telemetry,
  `dev/reports/governance/external_pilot_findings.jsonl` for raw imported
  external findings, and `dev/reports/governance/finding_reviews.jsonl` for
  adjudicated guard/probe/audit outcomes. Those logs should feed the future
  database/data-science layer, not replace the plan's `Session Resume` /
  `Progress Log`.
- The current operator protocol is now explicit: `devctl` owns command-level
  telemetry, `governance-import-findings` owns raw external-finding intake,
  `governance-review --record` owns adjudicated finding outcomes, and handoff
  notes must say when meaningful work happened outside those ledgers so
  coverage is not overstated.
- Coordination note for tandem review: do not create another per-slice
  `audit.md`. Narrative execution state belongs here (`Session Resume` +
  `Progress Log`), adjudicated evidence belongs in `governance-review`, and
  live Codex/Claude current-state handoff belongs in `review_state.json` with
  `bridge.md` as the compatibility projection.
- 2026-03-22 intake sharpened the `P0` rule further: the next missing work is
  wiring existing contracts into live consumers, not inventing more
  architecture. The remaining high-value gaps are AI guidance routing,
  automated `governance-review` closeout, typed `Session Resume` consumption,
  live use of `ProjectGovernance` routing fields, and shared command-crash
  handling.
- 2026-03-22 mapping follow-up: the remaining accepted `SYSTEM_AUDIT.md`
  structural/surface/test tranche is now fully absorbed into the canonical
  plan chain. `A13`/`A16`/`A17` stay in the `P0` runtime-contract cleanup
  lane, `A18`/`A19` stay attached to the shared command/output contract work,
  and `T3`/`T4`/`T5` now sit in the first platform validation matrix. The next
  move is implementation, not more audit transcription.
- 2026-03-22 full-audit follow-up: the earlier "all actionable items" claim is
  now true only after making the previously implicit tiers explicit. This plan
  now owns the feedback-loop closure (`A1-A4`), the next deterministic
  hard-guard tranche (`A27`), and governance-closeout/self-governance
  enforcement (`A29`, `G1`), while blocker-tranche authority and startup/
  memory tiers stay spelled out in `platform_authority_loop.md`.
- 2026-03-22 ambiguity follow-up: tightened the last two planning ambiguities
  before implementation. Part 39 was already explicit here (`governance-review`
  auto-record closeout remains a real checklist item), while Part 36 now names
  `cli.py` + `autonomy_loop.py` as the first crash-envelope closure sites and
  the platform validation matrix now requires a developer-runnable local
  integration suite instead of relying only on unit tests or CI wiring.
- 2026-03-27 live dirty-branch correction: the review confirmed two bounded
  architecture misses inside the current lane rather than a generic “AI lost
  the big picture” problem. Event-backed current-session state was still
  reading legacy compatibility agent rows before the typed registry, and the
  startup-generated `check-router` preflight hint could still target the
  current feature-branch upstream while the worktree was dirty, yielding
  `changed_paths=0` and a docs-lane misroute. The current branch now narrows
  both seams without widening the owner chain: typed review-state producers
  must prefer canonical registry rows over `_compat` inputs, and dirty
  startup-intake preflight should anchor to the development-branch diff base
  until the slice is checkpointed.
- 2026-03-27 validation follow-up: the bounded fixes are now exercised
  against the real branch state rather than only narrow unit slices. Focused
  runtime tests passed, the dirty-branch router rerun stayed green on local
  guards/tests, and the remaining full-bundle red state is the expected
  release-lane `master` CodeRabbit gate because branch history still carries
  release-sensitive workflow changes. The bigger-picture visibility issue is
  therefore not “AI needs a larger graph”; it is that startup, router, and
  review surfaces must keep reporting this branch-vs-slice distinction
  honestly, while live review-channel truth still fails closed as
  `bridge_contract_error` until repo-owned conductors are relaunched.
- Architecture review on 2026-03-16 closed a planning gap: the current
  topology/hotspot outputs are useful but still too thin to count as the
  public repo-understanding surface. The next public contract must be a real
  `devctl map` snapshot/query layer that combines topology, complexity,
  hotspots, changed scope, existing findings, and recommended checks.
- That same review also clarified the storage rule: `map` may feed later
  memory/database layers, but its authority should live under the shared
  `ArtifactStore` as canonical JSON plus refresh-ledger rows and an optional
  SQLite query index, so any repo can reuse cached focus state without
  depending on VoiceTerm-only memory paths.
- Naming simplification now has an explicit two-layer contract: one stable set
  of backend ids and one repo-pack-owned friendly wrapper layer for beginners,
  agents, and UI surfaces. The guard must validate the mapping between those
  layers so simple names do not drift into a second workflow system.
- The composable-product rule is now explicit too: every major subsystem
  should work by itself in any repo and also compose into one integrated agent
  app through shared contracts. Treat "standalone but composable" as a hard
  architecture requirement, not a nice-to-have.
- The current highest-priority execution lane under `MP-377` is the platform
  authority loop tracked in `dev/active/platform_authority_loop.md`. Treat
  that spec as the active `P0` sequencing surface. Immediate order is:
  blocker tranche first (daemon attach/auth, autonomy authority,
  JSONL/evidence integrity, self-governance closure), then startup authority,
  repo-pack activation, typed plan registry, one real runtime slice,
  evidence/provenance closure, `ContextPack`, and the first two-repo proof.
- `dev/guides/SYSTEM_AUDIT.md` is broad reference evidence, not execution
  authority. Only the code-backed blocker tranche reprioritizes active work;
  the rest of the 2026-03-19 audit remains corroborating evidence until its
  stale counts and internal contradictions are cleaned up. Do not treat the
  audit as a second roadmap.
- Fresh reviewer/coder sessions should use a hot/warm/cold context split
  rather than rereading every large plan on entry. Hot: product identity,
  current `MP-377` slice, authority spine, and live bridge instruction. Warm:
  the exact active plan/runbook sections for the current slice. Cold:
  whole-system audits, history, and broad reference docs such as
  `dev/guides/SYSTEM_AUDIT.md`.
- Startup/session packets must stay on one canonical family:
  `startup-context` / `WorkIntakePacket` / `CollaborationSession` /
  `ContextPack`. Do not introduce a parallel `bootstrap-context` or
  hand-maintained session-summary surface that can drift from the typed
  intake path.
- `ConceptIndex` and any ZGraph-compatible encoding are optional generated
  navigation/compression layers above the canonical plan/contract/artifact
  stack. They are not authority and must always expand back to cited source
  artifacts.
- `devctl probe-report` now honors repo-root `.probe-allowlist.json`
  design-decision entries in both artifact generation and terminal/markdown
  render paths, so the canonical operator packet matches the same filtered
  self-hosting view as the fallback script path. Current local probe state is
  medium-only: `0` active high findings, `14` active medium findings, and
  `25` routed design-decision packets.
- The next platform contract also needs an explicit split between deterministic
  agent repair and typed design-decision packets. AI should be able to consume
  both lanes from the same evidence stack; repo policy should decide whether a
  given decision packet is auto-applicable, recommend-only, or approval-gated
  instead of forcing agents to infer architecture choices from raw probe prose.
- Immediate next slice after the first contract-closure guard landing:
  replace checkout-path-based finding identity with stable repo identity +
  repo-relative path, then add the first hard-guard-to-`Finding`
  normalization seam on the highest-run blocking guards before widening into
  packaging or plan-structure cleanup.
- Fresh reviewer pass on 2026-03-17 refined that sequencing for the live
  dirty tree: keep Claude's bounded coding slice on `ReviewState` emitter
  parity plus stable review-channel identity first, then take the next `P0`
  self-hosting follow-up on the guard holes that review found
  (`check_platform_contract_closure.py` covering only `8` of `13` shared
  contracts and the remaining absolute-`repo_path` finding-id leak outside
  the `review_probe_report.py` workaround).
- Accepted sequencing rule from the 2026-03-17 whole-system audit: keep
  contract freeze first (`P0`), packaging/installable-boundary plus tracker
  compaction second (`P1`), and PyQt6/operator-console seam consolidation
  after the backend contracts exist strongly enough to converge on shared
  parsers, section registries, and CLI/action metadata.
- The current execution order is now explicit too: `P0` is the must-have spine
  (coherence, identity, registry, lifecycle, approvals, `map`, evidence
  bridge, parity), `P1` is product-complete operation (packaging/adoption,
  product-operability, full client/mode parity), and `P2` is later
  enrichments that must not bypass the spine.
- The canonical platform docs are no longer untracked-only local state:
  `dev/active/ai_governance_platform.md` and
  `dev/guides/AI_GOVERNANCE_PLATFORM.md` are now staged in git so fresh AI
  sessions and the next commit can preserve this scope without depending on
  chat history.
- The current Codex-reviewer / Claude-coder execution lane is usable for
  `MP-377` work right now: on 2026-03-13,
  `python3 dev/scripts/devctl.py review-channel --action launch --terminal none --dry-run --format md --refresh-bridge-heartbeat-if-stale`
  passed, refreshed the live markdown-bridge heartbeat, and emitted the
  expected 8 Codex reviewer lanes plus 8 Claude coder lanes. Treat that as
  real execution scaffolding for plan work, not as proof that the
  review-channel / continuous-swarm plans are fully closed.
- The next self-hosting markdown slice is now explicit: keep extending the
  existing `check_active_plan_sync` / docs-governance path, add one governed
  plan-format reference, and bring execution-plan docs into parity with the
  repo's own metadata-header and `Session Resume` contract before claiming
  typed markdown-to-registry closure.
- `Phase 2 - Normalize repo-pack policy and surface generation` now has a
  repo-backed first slice: `repo_governance.surface_generation` owns repo-pack
  metadata/context/surface policy, `devctl render-surfaces` renders or
  validates the governed outputs, `check_instruction_surface_sync` plus
  `docs-check --strict-tooling` enforce template-backed drift, and starter
  bootstrap/template flows seed the same contract for adopter repos.
- The generated-surface path is now hardened enough for broader reuse:
  report-mode surface checks tolerate missing local-only outputs such as
  `CLAUDE.md`, `render-surfaces --write` remains the explicit regeneration
  path, and the maintainer docs/tests now describe and cover that contract.
- The stable public generated-surface sync path remains
  `dev/scripts/checks/check_instruction_surface_sync.py`. Package-local logic
  stays under `dev/scripts/checks/package_layout/`; registries, workflows, and
  rendered docs should keep pointing at the stable public root shim instead of
  drifting to package-internal `check_*` entrypoints.
- Portable onboarding guidance is now aligned with that same repo-pack
  contract: bootstrap/setup docs tell adopters to inspect
  `repo_governance.surface_generation`, then run
  `python3 dev/scripts/devctl.py render-surfaces --write --format md` before
  their first full adoption scan.
- The governance command family now follows the machine-first projection rule
  directly in code. `governance-bootstrap`, `governance-export`,
  `governance-review`, and `render-surfaces` share one output/error helper,
  emit canonical JSON for machine consumers, and keep markdown as the human
  render on top of that payload instead of each command inventing its own
  result-flow shape.
- A follow-up architecture audit on 2026-03-13 confirmed that the current
  shared output path does not dump full JSON to stdout when `--output` is set.
  `write_output()` writes the artifact and only prints `Report saved to: ...`,
  so the remaining token-efficiency problem is not terminal flooding. The real
  gap is that this receipt is still human prose rather than a compact stable
  machine envelope, and the runtime/data-science stack still does not record
  artifact bytes, hashes, or estimated token cost for those machine payloads.
- The next abstraction should therefore not be a blanket rewrite of
  `emit_output()` for every `devctl` command. Many commands remain
  human/terminal-oriented. The better platform seam is a reusable
  machine-artifact emitter for JSON-canonical packet/report surfaces first
  (`governance-*`, `platform-contracts`, `probe-report`, `data-science`,
  `loop-packet`, then later review/autonomy surfaces), with compact machine
  receipts and measurable artifact-cost metadata layered on top of the
  existing generic output helper.
- That next slice is now partially implemented. JSON-canonical surfaces that
  use the new machine-output path write the full compact JSON artifact to disk,
  emit only a compact JSON receipt on stdout when `--format json --output ...`
  is used, and append artifact metadata (`path`, `sha256`, `size_bytes`,
  `estimated_tokens`, `stdout_receipt_size_bytes`) into `devctl` command
  telemetry so the repo can start measuring transport cost instead of only
  command duration/success.
- Self-hosting validation now covers nested command packages instead of
  silently preferring flat roots. `check_architecture_surface_sync.py` can now
  resolve aliased imports such as
  `from .commands.governance import bootstrap as governance_bootstrap`, so the
  governance package move is enforced by the repo's own architecture guard
  rather than living behind a false-positive blind spot.
- Self-hosting layout governance is green on the current tree, but the pass is
  still partly a freeze/baseline result rather than proof that the topology is
  fully decomposed. `check_package_layout.py` is currently preventing new
  sprawl in already-crowded roots such as `dev/scripts/checks`,
  `dev/scripts/devctl`, `dev/scripts/devctl/commands`, and
  `dev/scripts/devctl/tests`; those directories still need further package/test
  splits before the repo can claim the script surface is genuinely tidy.
- The first extraction-boundary hard guard is now live in repo policy.
  `check_platform_layer_boundaries.py` freezes new Python imports from
  Operator Console or shared runtime/platform files into repo-local
  orchestration modules, so the next extraction slices can harden seams
  without waiting for the full repo split first.
- Routed bundle execution now honors the repo-required interpreter too.
  `check-router --execute` rewrites repo-owned `python3 ...` bundle commands
  to the active interpreter before execution, which closes the concrete
  Python-3.10 fallback gap the plan had flagged in self-hosting reliability.
- The first concrete `repo_packs.voiceterm` consumer seam is now real.
  VoiceTerm-specific workflow-plan metadata and review-bridge path defaults
  now live under `dev/scripts/devctl/repo_packs/voiceterm.py`, and the
  Operator Console reads that repo-pack-owned surface instead of importing
  `review_channel` internals or hard-coding active-plan docs inside frontend
  modules.
- `RepoPathConfig` is now a real frozen dataclass exposed as
  `VOICETERM_PATH_CONFIG`. Consumers already span frontend modules,
  review-channel runtime modules, governance ledger modules, autonomy
  parsers, and `devctl` command files through `repo_packs` helper seams.
  Read-only collector helpers
  (`voiceterm_repo_root`, `collect_devctl_git_status`,
  `collect_devctl_mutation_summary`, `collect_devctl_ci_runs`,
  `collect_devctl_quality_backlog`) let the frontend call devctl collection
  through the repo-pack boundary instead of importing forbidden orchestration
  modules directly or using dynamic-import workarounds.
- The latest architecture re-audit tightened the framing without changing the
  direction: external analyzers remain subordinate engines or later adapters
  under the governance control plane, the governed signal taxonomy is explicit
  (`language-engine`, `AI-shape`, `repo-contract` findings), and the first
  portable release stays intentionally narrow instead of trying to extract
  every frontend or workflow loop at once.
- The recent iOS/mobile path cleanup is only partial. Shell scripts now name
  the canonical VoiceTerm paths, but `MobileRelayPreviewData.swift` still
  duplicates literals with only a source-of-truth comment, so that surface
  remains interim documentation rather than a finished repo-pack contract.
- The transitional `review_channel` runtime modules (`core.py`, `state.py`,
  `event_store.py`, `promotion.py`) now read path defaults from
  `VOICETERM_PATH_CONFIG` instead of defining their own literals.
  `parser.py` and `events.py` needed no changes; backward-compat aliases flow
  through the import chain.
- Widened the repo-pack boundary further with 4 more accepted passes:
  `mobile_status.py` now routes review-state loading through
  `repo_packs/review_helpers.py`; 6 command files moved `resolve_repo` /
  `run_capture` off the checks layer into `repo_packs/process_helpers.py`;
  governance ledger modules dropped compile-time `REPO_ROOT` for runtime
  `voiceterm_repo_root()` fallback; and `run_parser.py`,
  `benchmark_parser.py`, `cli_parser/reporting.py` all consume
  `VOICETERM_PATH_CONFIG` for autonomy/report defaults. Remaining duplicate
  defaults in `data_science/metrics.py`, `autonomy/report_helpers.py`,
  `audit_events.py`, and `watchdog/episode.py` migrated onto the same
  config. `repo_packs/voiceterm.py` remains an active shrink target rather
  than a closed contract.
- MP-358 tandem-loop work is now underway alongside the extraction lane:
  fixed `--scope` promotion bug (`86b902c`), added `--auto-promote` with
  end-to-end tests, wired `reviewed_hash_current` into status/launch/
  attention/handoff surfaces, enforced `block_launch` peer-liveness guard,
  and added `REVIEWED_HASH_STALE` attention signal. These are runtime
  contract improvements that complement the repo-pack extraction boundary
  by making the shared runner surfaces honest about bridge truth.
- MP-358 role-profile seam landed (2026-03-15): `runtime/role_profile.py`
  defines `TandemRole`, `RoleProfile`, `TandemProfile`, and
  `role_for_provider()` as the provider-agnostic contract that replaces
  hardcoded provider-name checks across the review-channel modules.
  `check_tandem_consistency.py` guard validates alignment.

### Next actions

Operational reminder: when a meaningful MP-377 slice is green with code,
validation, docs, and reviewer acceptance, stop widening the dirty tree and
prepare a bounded commit/push checkpoint through the normal approval path.

Immediate override for the current tree:

- Accepted 2026-04-04 architecture-audit follow-up: before broader packaging
  or client-migration widening, freeze the extension/adopter closure tranche.
  The required scope is explicit: no-write-safe read-only command semantics,
  fail-closed repo-pack/runtime activation with no silent VoiceTerm fallback,
  a repo-pack-owned `ExtensionBundle` for Codex/Claude/MCP surfaces, and a
  typed `AutomationSpec` for local/CI/Codex/Claude background work.
- If the live review loop is in play, repair the clean-tree
  `reviewer_overdue` state first. Detached publisher/reviewer-supervisor
  runtime is not enough by itself; the missing operational link remains the
  repo-owned persistent Codex reviewer worker/service path that keeps semantic
  review and operator-visible checkpoints moving between Claude passes.
- After reviewer follow-up, land the shared `system-picture` /
  external-review reducer as the next bounded implementation slice. That first
  reducer must carry repo/worktree/service identity, `CollaborationSession`,
  session-capability / worker-fanout state, delegated-worker receipts /
  topology, and stale-write collision controls rather than a generic summary.
- Migrate consumers in the fixed order already accepted in plan authority:
  PyQt6/operator console first, iPhone/mobile second, and Claude remote-loop
  plus external-review surfaces third.

Execution order for this section:

- treat items `1` through `7` as the current `P0` audit-intake tranche
- treat items `8` through `18` as next work that should wait until the current
  tranche is materially frozen
- treat items `19` and higher as later proof/scale work unless the user
  explicitly reprioritizes them

1. Continue turning the remaining audit intake into self-hosting enforcement
   work: the first layer-boundary guard is live, and the next backlog should
   cover the four deterministic blind spots now confirmed by branch review:
   contract-value enforcement, plan-to-runtime parity, authority-source
   validation, and dead authority/API seams. The immediate cheap truth fixes
   inside that tranche are
   `ActionResult.status` domain closure, `context-graph` confidence type
   alignment, and making mypy blocking for the `dev/scripts/devctl` lane
   before broader graph/system-picture expansion.
2. Turn escaped-finding closure into a typed meta-governance contract instead
   of a chat-only principle. The next bounded implementation should add
   finding-class -> prevention-surface routing, require each escaped class to
   close through one deterministic surface (`guard`, typed contract,
   bootstrap/helper contract, smoke test, or bounded debt record), and add
   regression proof plus repo-visible closure writeback in the same slice.
   Use the release-maintenance/import-shim tranche as the seed case, and
   generalize only across equivalent instances governed by the same contract.
3. Freeze the repo-understanding and naming surfaces before more wrappers
   proliferate: define `RepoMapSnapshot` / `MapFocusQuery` /
   `TargetedCheckPlan`, define the JSON-plus-SQLite cache contract, and define
   the guard-backed mapping between canonical backend ids and friendly wrapper
   names.
4. ~~Move the next real seam from frontend path cleanup to transitional
   runtime separation~~ — done enough to accept for this slice. The
   `review_channel` runtime modules now resolve VoiceTerm paths through
   repo-pack/runtime contracts, `mobile_status.py` now loads review status
   through `repo_packs.review_helpers` instead of importing
   `review_channel.*` directly, and the narrow `controller_action.py` /
   `triage_loop.py` checks-layer fit-gap is closed through the devctl-owned
   `process_helpers` seam. The next real seam is governance/report path
   ownership: `governance_review_log.py`,
   `governance/external_findings_log.py`, and their mirrored defaults in
   `data_science/metrics.py` should stop owning raw
   `dev/reports/governance/*` defaults directly, then the follow-up seam is
   `autonomy/run_parser.py` reducing hard-coded VoiceTerm plan/report
   defaults.
5. Keep the iOS/mobile path cleanup marked partial until generated or emitted
   repo-pack-owned metadata replaces duplicate literals in preview/demo
   surfaces; comments alone do not close that seam.
6. Define the installable governance package surface explicitly:
   `pyproject.toml`, build backend, versioning, dependency contract, and stable
   CLI entrypoint(s) for clean-environment installs.
7. ~~Widen `RepoPathConfig` coverage~~ — done. `RepoPathConfig` now has 15
   fields, 13 OC/frontend modules consume `VOICETERM_PATH_CONFIG`, 5
   repo-pack collector helpers replace forbidden imports, and iOS shell
   scripts centralize paths with source-of-truth comments. Only non-blocking
   presentation/help strings and test fixtures retain inline path literals.
8. Finish the compatibility contract, not just the version field:
   document schema-version ownership, migration rules, compatibility checks,
   and rollback expectations alongside repo-pack/platform version pinning.
9. Expand the adapter/frontend migration: `artifact_locator.py`,
   `bridge_sections.py`, and `session_trace_reader.py` are now path-migrated
   to `VOICETERM_PATH_CONFIG`. The remaining deeper couplings are
   `workflow_loop_utils.py`, `loops/comment.py`, the transitional
   `review_channel` runtime, and related read-only consumers which need
   adapter-contract work (replacing direct `subprocess`/`gh` calls and local
   path ownership with `WorkflowAdapter` / repo-pack contracts rather than
   more path migration).
10. Continue `Phase 2 - Normalize repo-pack policy and surface generation` by
   adding explicit repo-pack context-budget profiles and usage-tier guidance
   hooks; the generated surfaces are now policy-owned, but bounded context
   modes still need to become first-class repo-pack behavior too.
11. Promote the missing runtime evidence contracts into the executable
   `governance_runtime` surface: `ContextPack`, `ContextBudgetPolicy`,
   `Finding`, `FindingReview`, `MetricEvent`, and the thin-client snapshot
   states now scattered across operator-console readers.
12. Keep using this section plus the `Progress Log` for session handoff. Do not
   create a second "main plan" or a separate hidden scratch log for `MP-377`.
13. Define the canonical event-history/runtime-evidence contract that unifies
   existing JSONL ledgers (`devctl_events`, governance reviews, watchdog
   episodes, swarm summaries) without collapsing session handoff into the
   future database layer.
14. Define the context-budget contract and first repo-pack usage tiers before
   packaging more AI-facing loops; prompt cost must stay explicit platform
   behavior instead of hidden product debt.
15. Add a machine-artifact control-envelope contract for JSON-canonical
   surfaces so `--output` can produce compact machine receipts plus artifact
   hash/byte/token metadata without forcing the same behavior onto
   human-first commands.
16. Promote the same machine-first projection rule beyond the governance
   command family into review-channel, autonomy, and data-science packet
   surfaces so agents, operators, junior developers, and senior reviewers can
   consume one shared evidence payload at different projection/detail levels.
17. Extend runtime evidence beyond command duration/success: `RunRecord`,
    `devctl_events`, and later data-science rollups need artifact-size,
    artifact-hash, and estimated token fields so the repo can measure whether
    machine-first outputs are actually reducing context cost.
18. Continue burning down the crowded freeze-mode roots that
    `check_package_layout.py` is currently baselining. The next structural
    cleanup work should keep moving real implementation/test code out of flat
    `checks/`, `devctl/`, `commands/`, and `tests/` roots so the repo can later
    ratchet those areas toward stricter package ownership instead of living in
    permanent freeze mode.
19. Tighten structured-ledger coverage so manual/chat-driven fix sessions can
    either emit first-class run records or explicitly declare telemetry gaps
    instead of leaving command-history completeness ambiguous.
20. Increase full-codebase evidence density: use repeated `--adoption-scan`
    audit cycles and wider watchdog coverage so the repo can measure real
    false-positive and cleanup rates across more than the current reviewed
    subset.
21. Make false-positive remediation explicit: each false positive should produce
    a root-cause note and a concrete rule/policy follow-up unless the repo can
    justify leaving it as an intentionally advisory heuristic.
22. Add a replayable rule-quality benchmark path: define the first labeled
    cross-repo corpus and the versioned replay/evaluation flow that future
    DB/ML work must consume instead of relying only on live current-worktree
    scans.
23. Define the waiver/suppression lifecycle so known-noisy signals remain
    visible, expiring governance debt rather than becoming permanent silent
    bypasses.
24. Write explicit platform completion gates so this scope cannot be called
    done after repo split or packaging alone; closure should require
    architecture, pipeline, evidence, and telemetry trust together.
25. Add the repo-pack/platform compatibility guard and exercise it in pilot
    upgrades before treating external adoption as complete.
26. Preserve the platform’s differentiators in public proof, not only private
    plan text: adaptive feedback sizing, three-layer enforcement, artifact-
    backed governed loops, multi-agent review/coding, context budgets, mutation
    remediation, multi-surface control, and self-hosted portability should all
    survive into the durable/public whitepaper.
27. Start the standing Python/Rust pattern-mining loop against this repo and
    external pilot repos so new rule families come from measured evidence, not
    one-off intuition.
28. Measure which current rule families show repeatable AI-quality uplift
    across multiple repos instead of only sounding correct locally; treat
    those empirically supported families as the first true portable
    primitives.
29. Build the first loop-value proof packet for recent successful cleanup
    runs: before/after tests/builds, findings delta by rule family, artifact
    and token cost, reread/skip counts, loops-to-green, artifacts consumed
    per successful change, defer/revert rates, and the first ranked list of
    candidate portable primitives.
30. Keep a living list of common AI-generated bad patterns that still pass all
    current checks so future guard/probe work is driven by measured misses,
    not taste alone.
31. Define the future language-extension contract while Python/Rust are still
    the active lanes so new languages can plug into the same architecture
    instead of creating parallel subsystems later.
32. Land the `check_governance_closure` meta-guard as a concrete `P0`
    enforcement surface: one guard script that verifies (a) every registered
    guard has a corresponding test file, (b) every registered probe has a
    corresponding test file, (c) every registered guard is invoked by at
    least one CI workflow, (d) every function exceeding code-shape limits is
    either fixed or tracked in the exception list, (e) every CI workflow has
    a `timeout-minutes` field, and (f) JSONL evidence writers log warnings
    on parse failures instead of silently skipping corrupted lines. This
    guard makes the governance system self-proving and catches the class of
    gaps found by the 2026-03-17 25-agent architecture audit.
33. Land the two immediate data-integrity fixes that the audit surfaced as
    zero-risk blockers: (a) `jsonl_support.py` must log a warning with line
    number on `json.JSONDecodeError` instead of returning `None` silently,
    and (b) `code_shape_function_exceptions.py` must track the two guard
    functions (`coderabbit_ralph_loop_core.py::execute_loop` at 222 lines,
    `coderabbit_gate_core.py::build_report` at 177 lines) that currently
    exceed the 150-line Python limit without an exception entry.
34. Standardize the devctl command UX contract across all 67+ commands:
    (a) `--format` choices must be `["json", "md", "terminal"]` with
    default `"md"` everywhere, (b) all stderr output must use
    `[command-name] error:` prefix format, (c) all state-modifying commands
    (`autonomy-loop`, `autonomy-benchmark`, `mutation-loop`) must support
    `--dry-run`, (d) all JSON outputs must include a `schema_version` field,
    and (e) `swarm_run` must be renamed to `autonomy-swarm-run` or aliased
    to match the hyphenated naming convention. Add a
    `check_command_ux_consistency` guard that validates these patterns across
    registered commands so drift is caught by CI.
35. Add `timeout-minutes` to the 15 CI workflows that currently lack it:
    `rust_ci.yml` (45 min), `tooling_control_plane.yml` (60 min),
    `coverage.yml` (30 min), `memory_guard.yml` (20 min),
    `parser_fuzz_guard.yml` (30 min), and the remaining 10 workflows
    identified in the 2026-03-17 CI audit. The `check_governance_closure`
    meta-guard should enforce this going forward.

### Resume instructions for the next AI session

1. Read `AGENTS.md`, then `dev/active/INDEX.md`, then
   `dev/active/MASTER_PLAN.md`.
2. Read this file and treat it as the only main active plan for the standalone
   governance product scope.
3. Read this `Session Resume` section and the latest `Progress Log` entries
   before making recommendations or edits.
3.1 If the current shared worktree contains `GUARD_AUDIT_FINDINGS.md` and/or
    `ZGRAPH_RESEARCH_EVIDENCE.md`, consult them as local reference-only
    companions for expanded evidence, ZGraph integration ideas, and proof
    chains. They do not override tracked plan authority; any accepted
    conclusion must be written back into this file, the subordinate
    `platform_authority_loop.md` spec when relevant, and/or `MASTER_PLAN`
    before implementation or review.
3.2 Keep the current closure order explicit. The governed checkpoint-authority
    gap is now closed in repo code: `devctl commit` may proceed when startup
    explicitly says `checkpoint_allowed` / `await_checkpoint` with reviewer
    checkpoint permission, while raw `git commit` remains blocked. In
    parallel, Q55 findings convergence still requires one canonical
    `FindingBacklog` reader/writer: `review-channel --action post --kind
    finding` and `LIVE_RUN.md` import must write the same ledger, while
    dashboard/startup/monitor/bridge/findings-priority all read that same
    snapshot and `governance-review` remains close-out only.
3.3 The next same-lane closure after the authority-snapshot reducer landed is
    now narrower and live-dogfood-backed: keep `review_state`, `compact`,
    and `full` projections on the same `AuthoritySnapshot` contract and keep
    reviewer/Claude coordination on the typed packet lane. The current proof
    packet is `rev_pkt_0394` (`codex -> claude`), and the active follow-on
    packet findings are `rev_pkt_0391` (`auto-mode` phase drift while no
    participants are live), `rev_pkt_0392` (silent
    `review-channel --action watch --follow` zero-match liveness), and
    `rev_pkt_0393` (dashboard/status pending-count drift plus missing
    top-level status fields). Continue consuming and answering Claude through
    review packets instead of chat-only handoff.
3.4 The latest same-lane packet check at `rev_pkt_0396` narrowed the next bug
    again: current in-process startup/session-resume builders no longer
    reproduce the earlier authority mismatch, but `session-resume --format
    json` was still returning exit code `1` when it successfully emitted a
    valid blocked-state packet. Keep the machine-readable contract explicit:
    JSON/bootstrap surfaces may report blocked posture in payload fields
    (`blockers`, `authority_snapshot`, summaries) without treating successful
    emission itself as a command failure.
3.5 `rev_pkt_0393` is now closed in repo code rather than left as packet-only
    dashboard evidence. `DashboardSnapshot` now emits a compact top-level
    header contract (`status`, `owner`, `next_action`, `top_blocker`,
    `pending_count`, `pending_findings_count`, `next_actor`,
    `next_command`), coordination carries integer pending counts instead of
    only prose, and the blocker reducer normalizes stale
    `"N pending review packet(s)"` strings against the typed live packet
    count before the dashboard/status surfaces render them. Keep the raw
    `review_state` payload as the dashboard extraction source when it is
    present so doctor/runtime fields do not disappear during typed
    round-trip projection; continue feeding the typed object into
    `ControlPlaneReadModel` / startup bootstrap separately. The next packet
    work on this lane is now `rev_pkt_0391` / `rev_pkt_0392`.
3.6 `rev_pkt_0392` and the later escalation packet `rev_pkt_0400` are now
    closed in repo code and live dogfood rather than left as packet-only
    watcher evidence. `review-channel --action watch --follow` now uses a
    cheap latest-snapshot resolver on the Step 0 hot path instead of parsing
    every saved graph artifact before first emit, and the watch loop now owns
    one target/status lane via a typed single-flight lifecycle file. Live
    proof on 2026-04-14 showed the first frame emits immediately
    (`watch_started` then `watch_snapshot`), unchanged polls emit explicit
    `watch_heartbeat` frames, a competing watcher exits immediately with
    `single_flight_conflict`, and Ctrl-C emits a final `watch_exit` while the
    persisted watcher state remains one valid JSON document after a
    dogfood-found append-mode regression was patched in the same slice. The
    remaining same-lane packet work is now `rev_pkt_0391`; keep the large
    expired-packet backlog visible as hygiene debt unless it proves causally
    tied to that lane.
3.7 `MP377-P1-T05` is now partially landed as an authority-reader pass rather
    than just a plan note. Context-graph plan nodes, reviewer tracker-plan
    resolution, scoped promotion MP lookup, and `ReviewSnapshot` plan indexing
    now prefer the persisted `PlanRegistry` / `ProjectGovernance` artifact and
    only fall back to raw `INDEX.md` parsing when typed governance is
    unavailable. Focused proof is green in
    `test_plan_resolution.py`, `test_promotion_scope.py`,
    `test_review_snapshot_why.py`, `test_catalog_nodes.py`,
    `test_context_graph.py`, and `test_review_snapshot.py`. Remaining `T05`
    work is the narrower docs-governance/reporting side that still treats
    markdown scans as the registry source. The first maintainer-doc routing
    follow-up is now closed too: `governed_doc_routing.py` prefers typed
    `ProjectGovernance` doc paths before surface-generation context fallbacks,
    and focused docs-governance regressions plus a clean
    `devctl check --profile ci` run are green on that slice.
4. Continue from the listed `Next actions` unless the user explicitly
   reprioritizes.
5. Before ending the session, update both this `Session Resume` section and the
   `Progress Log` with what changed, what remains, and what the next AI should
   do.

## Progress Log

- 2026-04-22: Closed the Phase 0.b proof-tick parity slice without widening
  back into dual-agent mode. `ControlPlaneReadModel` and
  `SessionCachePacket` now carry producer-owned `SurfaceProvenance` from the
  typed review-state tick, review-channel compact/full/actions projections
  copy the same tuple, and `check_review_surface_consistency.py` freezes the
  nine-surface parity contract across coordination, authority,
  control-plane, startup-context, session-resume, status, persisted
  review-state, registry, and bridge compatibility. Focused proof is green on
  the review-surface consistency, control-plane read-model, session-resume,
  and projection-bundle regressions; live surface consistency is green after
  one status projection refresh. Runtime still reports checkpoint-required
  single-agent posture, so dual-agent fanout remains closed.
- 2026-04-21: Closed the Phase 0.a producer-provenance slice for nested
  runtime authority surfaces. `AuthoritySnapshot` and
  `CoordinationSnapshot` now carry the same seven-field proof-tick
  provenance tuple as review-state projections (`snapshot_id`, `zref`,
  `source_identity`, `source_contract`, `source_command`,
  `observed_fields`, `inferred_fields`) by copying producer-owned source
  identity through `attach_surface_provenance()` instead of making later
  parity tests reconstruct it. Focused proof is green for the owning
  startup/coordination suites plus review-state/runtime-doctor and
  session-resume deserialization coverage. The remaining Phase 0.b work is
  to freeze the wider nine-surface parity test over these emitted fields.
- 2026-04-18: Absorbed Claude's four-agent consolidation synthesis into the
  live umbrella plan instead of creating a new active plan doc. `MP-388`
  through `MP-397` now sequence the remaining consolidation work in bounded
  slices: archive four reference-only active docs, land the semantic
  `PlanRegistry` loader and plan-mutation writeback, cut startup/work-intake
  over to `PlanTargetRef` authority, extend the role model with planner /
  auditor / researcher / coordinator, add a typed command registry, and close
  the biggest half-done surfaces through structured checklists, generators,
  orphan detection, and CLI/runtime parity rules. The older `MP377-P1-T05`
  through `MP377-P1-T08` items are now explicitly `blocked` behind that lane
  so startup routing keeps selecting the consolidation work instead of the
  previously parked projection/runtime follow-ups.
- 2026-04-18: Closed the bounded provider-hardcode / prepared-launch drift
  seam in the live `MP-377` / `MP-355` proof. Prepared launch authority now
  derives post-launch `remote_control` continuity from typed
  governance/review-state evidence instead of a single env var while still
  honoring explicit operator-mode overrides first, and the
  current-session/status/coordination reducers now resolve coding/reviewer
  identities from typed collaboration state instead of hardcoded `codex` /
  `claude` packet paths. The same checkpoint keeps
  `event_watch_support.load_target_packets()` backward-compatible across the
  `EventWatchContext` migration so live watch-follow callers do not crash on
  the legacy argument shape. Focused proof is green on
  `test_launch_authority.py`, `test_current_session_projection.py`,
  `test_coordination_snapshot.py`, `test_event_watch_support.py`, and the
  targeted `test_review_packet_inbox.py -k indexes_current_instruction_by_target_agent`
  regression. Fresh `review-channel status` / `doctor` receipts still show
  `runtime_missing`, blank `current_instruction_revision`, and
  `implementer_ack_state=missing`, so this checkpoint explicitly leaves live
  runtime continuity open instead of over-claiming closure.
- 2026-04-18: Tightened the typed collaboration-role contract so role choice
  no longer depends on treating `devctl dogfood` like a universal runtime
  mode. `CollaborationSession` and `AuthoritySnapshot` now carry explicit
  `mutation_owner`, `verification_owner`, and watcher ownership/status fields.
  The active AI should derive who codes, who verifies, and who keeps the
  watcher/dashboard lane live from typed collaboration state first. Dev-mode
  dogfood stays a development evidence ledger layered on top of that runtime
  truth, not the thing that decides the role posture for arbitrary end-user
  sessions.
- 2026-04-17: Closed the live host-process cleanup false block that was still
  freezing governed checkpoints after the earlier pipeline/startup repairs. A
  real detached Codex conductor wrapper remained registry-backed and
  script-running, but `_protected_registered_conductor_pids()` only trusted
  `session.live`, so prepared-head drift flipped the same running conductor
  into a strict `recent_detached` failure without making it safe to reap. The
  bounded fix now protects registry-backed running `session_pid` values based
  on runtime/script liveness rather than broader prepared-head freshness, so
  `process-cleanup --verify` and `host-process-cleanup-post` stay green for a
  still-running conductor while unregistered or pid-less detached wrappers
  continue to fail closed. Focused proof is green on
  `test_process_sweep.py`, targeted `test_process_audit.py`, and live
  `python3 dev/scripts/devctl.py process-cleanup --verify --format json`.
- 2026-04-17: Closed the stale pipeline-recovery mirror that was still making
  the governed checkpoint path look manual. A live dogfood retry proved that
  `pipeline --action abandon` could record `new_state=abandoned` in the
  canonical pipeline artifact and still have the next bridge-backed status
  refresh rehydrate `push_blocked` back into both `review-channel status` and
  `projections/latest/commit_pipeline.json`. The bounded fix keeps the
  canonical pipeline write authoritative: direct `pipeline`
  `abandon` / `recover` / `refresh-authorization` actions now refresh the
  shared review-channel projections immediately after they persist the new
  pipeline payload, so later status/commit reads pick up the updated pipeline
  state instead of replaying the stale `latest/commit_pipeline.json` mirror.
  The same closure typed the expanded pending-reviewer commit gate helper
  against `ReviewState`, which cleared the repo-wide
  `check_python_typed_seams.py` failure that surfaced on the first fresh
  checkpoint retry after the projection fix. Focused proof is green on
  `test_pipeline_command.py`, `test_commit_pending_reviewer_gate.py`,
  `check_python_typed_seams.py`, and `check_code_shape.py`, and the next live
  move is back on the governed checkpoint path instead of another manual
  pipeline detour.
- 2026-04-17: Closed the checkpoint-vs-relaunch deadlock that remained after
  the current-session authority repair. Detached `active_dual_agent`
  runtime-only evidence was still outranking stronger checkpoint truth, so the
  same review-current, over-budget repo state could say
  `attention.status=review_loop_relaunch_required` while startup authority
  already required a checkpoint. The bounded fix now lets checkpoint
  authority preempt detached-runtime recovery when
  `reviewed_hash_current=true`, `review_needed=false`, and typed
  `push_enforcement` says the tree is over budget. `status`, `doctor`,
  `authority_snapshot`, and `startup-context` now converge on
  `checkpoint_required` / `cut_checkpoint` plus the governed
  `devctl commit -m` command, dedupe the startup blocker summary, and keep
  action routing fail-closed by allowing `vcs.stage` / `vcs.commit` while
  still blocking `implementation.edit`. Focused proof is green on
  `test_recovery_assessment.py`, `test_action_routing.py`,
  `test_startup_context.py`, and targeted status regressions in
  `test_review_channel.py`.
- 2026-04-17: Closed the reopened current-session/runtime authority gap that
  dogfood exposed after the packet-attention helper extraction. The reducer
  was still treating missing packet surfaces as explicit clear authority, so
  blank queue state erased prior typed reviewer instructions and one
  canonicalization fixture no longer represented live packet truth. The
  bounded repair now requires explicit packet authority before
  `current_session` clears, ignores reviewer-targeted
  `derived_next_instruction_source.to_agent=codex` queue rows when projecting
  Claude's live instruction, keeps bridge-backed authority fail-closed when
  the live bridge has no authority signal, blocks
  `ImplementationAdmissibility` on missing/empty typed
  `implementation_permission`, and marks `relaunch_review_loop` auto-fixable
  so reviewer-follow relaunch stays bound to the typed recovery decision.
  Focused proof is green on `test_current_session_projection.py`,
  `test_implementation_admissibility.py`, and
  `test_reviewer_follow_restore_policy.py`; maintainer-doc closure for the
  slice also landed so `docs-check --strict-tooling` can treat the behavior as
  repo-owned contract instead of hidden chat state.
- 2026-04-15: Closed `MP377-P1-T04` by persisting governed markdown
  `PlanRegistry` plus per-plan `PlanTargetRef` authority to
  `dev/reports/governance/plan_registry.json`, teaching
  `scan_governed_markdown_contracts()` to reuse that artifact while the
  governed doc set is unchanged, and teaching `build_target_ref()` to reuse
  the persisted target metadata before reopening plan markdown. Focused proof
  is green in `test_governance_draft.py`, `test_work_intake.py`,
  `test_planning_ir.py`, and `test_startup_context.py`; next queued work is
  `MP377-P1-T05` so `INDEX.md` / `MASTER_PLAN.md` / owner-plan markdown can
  become bounded projections over the persisted registry instead of mutable
  execution authority.
- 2026-04-15: Started `MP377-P1-T05` with the first artifact-first authority
  consumer pass instead of another markdown-only plan note. Context-graph plan
  nodes, reviewer tracker-plan resolution, scoped promotion MP lookup, and
  `ReviewSnapshot` plan indexing now prefer the persisted
  `ProjectGovernance.plan_registry` state and only fall back to raw `INDEX.md`
  parsing when typed governance is unavailable. Focused proof is green in
  `test_plan_resolution.py`, `test_promotion_scope.py`,
  `test_review_snapshot_why.py`, `test_catalog_nodes.py`,
  `test_context_graph.py`, and `test_review_snapshot.py`. Remaining `T05`
  scope is the docs-governance/reporting side that still scans markdown for
  registry metadata.
- 2026-04-15: Closed the first docs-governance follow-up on the remaining
  `MP377-P1-T05` read-side scope. `governed_doc_routing.py` now prefers typed
  `ProjectGovernance` doc paths (`docs_authority`, guide roots, scripts
  README, tracker/index roots) before surface-generation context fallbacks,
  and docs-check default composition is covered by new focused regressions in
  `test_governed_doc_routing.py` and `test_docs_check_constants.py` plus
  non-regression proof in `test_governance_draft.py` and a clean
  `python3 dev/scripts/devctl.py check --profile ci` run. Remaining same-lane
  work is narrower reporting/dogfood consumers, not maintainer-doc routing.
- 2026-04-15: Landed the next `MP377-P1-T05` read-side follow-up without
  pretending every `INDEX.md` row is an execution plan. Scoped plan readers
  now resolve typed execution-authority entries first and then typed
  `doc_registry` companion docs before raw `INDEX.md` compatibility fallback,
  which lets `plan_resolution.py` and `promotion.py` stop depending on live
  markdown rows for scoped companion-plan routing. The same slice fixes one
  packet-queue hygiene bug in the live dogfood loop: persisted
  `expired_unresolved_packet_ids` and stale latest-finding ids are now pruned
  against the live reducer before packet inbox state is merged, so
  `open_findings` / reviewer attention stop reviving already-evicted expired
  packets. Focused proof is green in `test_plan_resolution.py`,
  `test_promotion_scope.py`, `test_review_packet_inbox.py`, and
  `test_work_intake.py`; repo-wide `docs-check --strict-tooling`,
  `check_code_shape.py`, `check_review_surface_consistency.py`,
  `check_active_plan_sync.py`, `check_multi_agent_sync.py`, and
  `check_review_channel_bridge.py` are green. Remaining red in
  `check --profile ci` is governance/budget debt (`package-layout` baseline
  debt plus startup-authority dirty-budget), not a regression in this slice.
- 2026-04-15: Closed the live review-channel observability/parity regressions
  surfaced during the dogfood relaunch. The packet miss was not transport
  loss: typed inbox state still carried the live Codex queue, but the
  autogenerated inbox command was too broad and reviewer bootstrap/prompt
  surfaces did not force inbox-first consumption the way implementer bootstrap
  already did. The bounded repair now emits
  `review-channel --action inbox --target <agent> --status pending ...` from
  the shared packet-inbox reducer, adds reviewer inbox-first guidance to the
  session-resume/prompt surfaces, downgrades bridge freshness when
  `active_dual_agent` loses its live reviewer conductor, and makes the shared
  control-plane reducer prefer typed `effective_reviewer_mode` plus live
  implementation authority over stale planned mode / startup-receipt
  fallbacks. Focused reviewer/runtime/auto-mode/session-resume regressions are
  green, so dashboard/control-plane/auto-mode no longer have to claim
  `fresh` / `reviewer_alive=True` while status/doctor already say
  `review_loop_relaunch_required`.
- 2026-04-15: Landed the repo-owned contract for the live dogfood campaign
  instead of leaving the system-test topology in chat. `devctl dogfood
  --record` now persists campaign/linkage metadata alongside each coverage row
  (`campaign_id`, `scenario_id`, `repo_scope`, `repo_label`, `repo_path`,
  `topology`, `lane_role`, `live_run_refs`, `governance_finding_ids`),
  renders that state in the summary/report surface, and carries the same
  linkage into auto-recorded `signal_type=dogfood` governance notes. The same
  slice makes the compatibility findings path explicit too:
  `governance-import-findings` can now ingest `LIVE_RUN.md` through the
  shared markdown parser with repo-scoped `repo_name:Q-ID` sync keys, so
  repeated imports collapse onto canonical external-finding identity instead
  of spawning per-run duplicates. The owner docs now lock the next execution
  order to the real system: VoiceTerm full live loop first, external repo
  matrix second, and no mutating fanout beyond the current startup receipt
  while it still reports `safe_to_fanout=False`.
- 2026-04-15: Closed the startup-authority performance regression behind the
  live `startup-context` stall. The typed startup reducer was still healthy,
  but `build_startup_authority_report()` was calling the import-index
  atomicity scan in a way that re-read committed Python importer files across
  the whole repo from `HEAD` on every bootstrap. The guard now bounds the
  committed-layer scan to the local package scope touched by current Python
  worktree paths, preserving the real split/atomicity check for local edits
  while restoring fast startup receipts on the live repo. Focused
  `test_startup_authority_contract.py -k import_index_atomicity` is green, and
  `startup-context --format summary` now returns the expected
  `checkpoint_before_continue` receipt instead of appearing hung.
- 2026-04-15: Closed the startup contract-ownership projection drift behind
  the stale `startup_surface_tokens_unpopulated` governance finding. The
  platform contract rows already carried startup-surface tokens, but
  `runtime/startup_context_projections.py` was collapsing them to a
  single-token preview before `startup-context --format json` ever rendered
  them, which made the startup contract map look underpopulated. The bounded
  repair now preserves the full token metadata inside `StartupContext`,
  serializes `startup_surface_token_count` plus a two-token preview in the
  startup JSON surface, and removes the stale one-token limiter from
  `runtime/startup_context.py`. Added focused regression coverage in
  `test_startup_context.py`, live `startup-context --format json` now shows
  honest counts (for example `ReviewState` advertises count `5` with preview
  `snapshot_id`, `bridge`) while `startup-context --format summary` remains
  stable on the operator-facing `action` / `reason` / `attention_status`
  lines, `check_platform_contract_closure.py` and `check_code_shape.py` are
  green, local dogfood is recorded as `dogfood-95f32b3f4406`, and
  governance-review finding `2146d8ee3f303af6` is fixed. Packet-state closure
  is clean too: Claude's PASS for the earlier queue hot-path request landed as
  `rev_pkt_0553` and is acked, and the new observer request for this startup
  slice closed with Claude PASS `rev_pkt_0555`, now acked.
- 2026-04-15: Closed the remaining live part of
  `authority_snapshot_3_fields_missing`. The shared `AuthoritySnapshot`
  contract already carried `allowed_actions`, but startup still dropped
  `actor_role` and `actor_identity`, so the first architecture-review finding
  was only partially fixed. The reducer now resolves actor role/identity from
  the same typed startup/coordination payload that already drives
  `allowed_actions`, persists those fields through startup JSON and
  `dev/reports/startup/latest/receipt.json`, and keeps the reducer shape honest
  by moving the new actor-resolution logic into
  `runtime/authority_snapshot_actor.py`. Focused startup/session-resume tests
  are green, live `startup-context --format json` now shows
  `authority_snapshot.actor_role=implementer`,
  `authority_snapshot.actor_identity=claude`, and bounded
  `authority_snapshot.allowed_actions`, `check_platform_contract_closure.py`
  and `check_code_shape.py` are green, local dogfood is recorded as
  `dogfood-52ab6f07e6dd`, and governance-review finding
  `8487d1d61d49efb9` is fixed. Claude-side dogfood also closed:
  `rev_pkt_0556` was posted and acked, Claude PASS landed as `rev_pkt_0557`,
  and Codex acked the result.
- 2026-04-15: Cleared the live guard-bundle blockers that were stopping the
  governed checkpoint on the dirty `MP-377` tree. The failure was concrete:
  `devctl commit` hit one duplicated packet-attention helper pair, five new
  high-parameter functions, and one large dict literal before it could write
  the checkpoint. The repair stayed inside the touched review-channel/runtime
  helpers instead of flattening behavior back into larger files: packet
  attention now resolves through
  `review_channel/current_session_attention.py`, the
  event-projection/reducer/heartbeat/authority helpers now pass typed resolver
  or input objects rather than growing signatures, and
  `session_resume_authority_payload.py` now serializes packet-attention agent
  rows through `asdict()`. Focused proof is green on
  `test_current_session_projection.py`, `test_session_liveness_events.py`,
  targeted `test_startup_context.py` authority-snapshot cases, targeted
  `test_session_resume.py` review-state context/authority roundtrip, and the
  four blocking shape guards
  (`check_function_duplication.py`, `check_structural_similarity.py`,
  `check_parameter_count.py`, `check_python_dict_schema.py`). Local dogfood is
  recorded as `dogfood-baf0d7aa6e50`, and Claude dogfood request `rev_pkt_0558`
  has already closed with PASS `rev_pkt_0559`, now acked. The first governed
  commit retry then failed closed on `attention_revision_stale`, which is the
  right typed behavior because Claude's PASS changed inbox state mid-checkpoint;
  the next retry runs from a fresh startup receipt after the ack.
- 2026-04-15: Closed the governed commit reuse-path `validation_receipt_missing`
  automation gap. `commands/vcs/commit.py` now routes reusable approved
  pipelines through the new `commands/vcs/commit_guard_replay.py` helper
  whenever the validation receipt is missing, stale, or checkpoint-insufficient,
  and the focused regression in `tests/vcs/test_commit_gate.py` proves the
  receipt is rebuilt and the commit records cleanly. Local dogfood is
  `dogfood-fc22bfd092ff`; Claude dogfood request `rev_pkt_0562` is pending.
- 2026-04-15: Closed the governed commit remote-approval self-invalidation
  path that the next live retry exposed. In `remote_control` approval mode,
  `devctl commit` was still entering `vcs.commit` immediately after posting a
  `commit_approval` request, so the new packet could change attention state
  and fail the same run closed on `attention_revision_stale`. The preflight is
  now split through `commands/vcs/commit_preflight.py`, which returns
  `operator_approval_pending` before the commit phase whenever approval is
  still outstanding. The focused regression in `tests/vcs/test_commit_gate.py`
  proves the command stops before `vcs.commit`, and live proof is green too:
  pipeline `pipeline-c773e2555beb` first paused at
  `operator_approval_pending`, operator approval `rev_pkt_0565` was applied
  against generation `gen-4e7c1e308d02`, and the resumed governed path
  recorded code commit `0f66c9d8` before the trailing review-snapshot receipt.
  Local dogfood is `dogfood-3bb9cde459f1`.
- 2026-04-15: Closed the governed push review-snapshot self-staleness loop
  that appeared immediately after the first successful governed commit.
  `review-snapshot --write --receipt-commit` now lands a governed receipt
  shape that refreshes both `dev/audits/REVIEW_SNAPSHOT.md` and `bridge.md`;
  the new shared helper in `runtime/review_snapshot_refresh.py` makes that shape
  explicit and lets both `check_review_snapshot_freshness.py` and
  `runtime/push_authorization.py` inherit the parent code commit for freshness
  and publication authority instead of treating the receipt commit as an
  unrelated head change. Added focused regressions in
  `tests/checks/test_check_review_snapshot_freshness.py` and
  `tests/runtime/test_push_authorization.py`, and kept the existing atomic
  receipt-pipeline tests green. Local dogfood is `dogfood-8f66a5109454`.
  Next step is to rerun `python3 dev/scripts/devctl.py commit -m "Stabilize review-channel authority recovery" --role implementer --format json`
  only if the latest staged tree changed again; otherwise run a fresh startup
  receipt and continue directly through `python3 dev/scripts/devctl.py push --execute --format json`.
- 2026-04-15: Closed the reopened live relaunch-vs-poll-due split inside the
  shared bridge-backed attention classifier. `review-channel --action status`
  had regressed to `attention.status=reviewer_poll_due` whenever freshness was
  present, even if the same typed payload still showed
  `launch_truth=hybrid_claude_only` / detached-runtime evidence and no live
  reviewer. The fix is small but load-bearing:
  `review_channel/attention_classify.py::_classify_startup_attention()` now
  treats detached/hybrid launch truth as `review_loop_relaunch_required`
  before it falls through to reviewer-freshness warnings. Added regression
  coverage in `test_review_channel.py` for the exact live shape
  (`poll_due + hybrid_claude_only -> review_loop_relaunch_required`) and kept
  the existing event-backed hybrid relaunch proof green. Focused pytest proof
  is green, `check_code_shape.py` is green, and live repo proof is green:
  `review-channel --action status --refresh-bridge-heartbeat-if-stale` and
  `startup-context --format summary` now both emit
  `review_loop_relaunch_required` while preserving checkpoint gating as a
  separate boundary. Claude observer dogfood is the next required closure on
  this slice.
- 2026-04-15: Closed the stale remote-control vs local single-agent authority
  split that was still leaving startup/event-backed state behind the live
  reviewer lane. The local takeover writer now retires persisted
  `remote_control_attachment` artifacts through
  `review_channel/remote_control_attachment_artifact.py` when
  `reviewer-heartbeat --reviewer-mode single_agent` records a sanctioned local
  takeover, and `runtime/reviewer_runtime_models.py` no longer treats
  `status=stale` attachments as active transport. The startup/runtime reducer
  side was tightened too: `runtime/control_topology.py` now sanctions
  single-agent authority in both `local_terminal` and `remote_control`
  interaction modes, while the event-backed projection in
  `review_channel/event_projection_bridge.py` plus
  `event_projection_assembly.py` now prefers the live bridge reviewer mode so
  `startup-context` no longer keeps stale daemon `active_dual_agent` metadata
  after a local single-agent takeover. Focused proof is green on
  `test_current_session_projection.py`,
  `test_remote_control_attachment.py`,
  `test_observed_topology.py`, and the targeted reviewer-heartbeat tests in
  `test_review_channel.py`; `check_code_shape.py` and
  `check_platform_contract_closure.py` are green too. Live repo proof is now
  aligned across surfaces: `review-channel --action reviewer-heartbeat
  --reviewer-mode single_agent --reason manual-review` detaches the stale
  `reviewer_runtime.remote_control_attachment`, `review-channel --action status`
  resolves `observed_control_topology=single_agent` with
  `implementation_permission=active`, and `startup-context --format summary`
  now reports `interaction_mode=local_terminal`,
  `observed_control_topology=single_agent`,
  `implementation_permission=active`, and
  `attention_status=checkpoint_required` with only the expected
  checkpoint/resync blockers remaining. Local dogfood is recorded as
  `dogfood-c05252cb0003`; Claude PASS `rev_pkt_0570` for dogfood request
  `rev_pkt_0569` is now acked too, confirming the expected
  `local_terminal`/`single_agent` convergence with no new findings before the
  governed checkpoint retry.
- 2026-04-15: Closed the live chat-implementer topology gap Claude surfaced in
  `rev_pkt_0571`. The collaboration/runtime reducers were already carrying
  `coding_agent=claude`, but they only marked that role live from conductor
  metadata or active attachments. `review_channel/collaboration_session.py`
  now promotes a configured implementer to live when fresh packet-lane
  activity proves the provider is active, using the new generic packet-activity
  helper in `collaboration_session_local_reviewer.py`; and
  `runtime/control_topology.py` now preserves typed live reviewer+implementer
  evidence instead of collapsing it back to `single_agent` just because the
  reviewer lane is still sanctioned `single_agent`. Focused proof is green on
  `test_collaboration_session.py` and `test_observed_topology.py`;
  `check_code_shape.py` and `check_platform_contract_closure.py` are green too.
  Live repo proof now matches the bounded expectation: `review-channel --action
  status` reports `runtime_counts.live_reviewer_total=1`,
  `runtime_counts.live_implementer_total=1`,
  `observed_control_topology=single_implementer_single_reviewer`, and
  `authority_snapshot.observed_control_topology=single_implementer_single_reviewer`,
  while `startup-context --format summary` reports the same observed topology
  with `implementation_permission=active`. `interaction_mode` still stays
  `local_terminal` until a repo-owned `remote_control_attachment` is active,
  so the remote-control transport signal remains a separate follow-up rather
  than being guessed from packet activity alone. Local dogfood is recorded as
  `dogfood-45cbbc2fb48e`; Codex acked Claude finding `rev_pkt_0571` before
  landing the fix and the next required closure is fresh Claude dogfood on the
  bounded topology-vs-interaction split.
- 2026-04-15: Closed the live bridge poll-metadata compatibility drift that
  was blocking governed push after commit `ae95f570`. The render path in
  `review_channel/bridge_projection_metadata.py` was preserving empty
  `Last Codex poll` fields from the existing `bridge.md` snapshot and then
  failing again when event-backed typed state supplied fractional-second UTC
  timestamps. The compatibility reducer now recovers `last_codex_poll_*`
  values from typed bridge state/liveness whenever the snapshot metadata is
  blank and normalizes ISO timestamps to the canonical whole-second
  `YYYY-MM-DDTHH:MM:SSZ` bridge format before local display rendering. The
  regression is locked in `tests/review_channel/test_bridge_render.py`.
  Focused proof is green on that test file plus `check_code_shape.py`; live
  repo proof is green too: `review-channel --action render-bridge` now
  repopulates `bridge.md` with `Last Codex poll: 2026-04-15T20:42:53Z`,
  `Last Codex poll (Local America/New_York): 2026-04-15 16:42:53 EDT`, and
  `check_review_channel_bridge.py` passes again. Local dogfood is recorded as
  `dogfood-2e845091c081`. Claude's pre-commit PASS `rev_pkt_0576` and
  maintenance follow-up `rev_pkt_0577` were both acked while clearing the
  render gate; `rev_pkt_0577` remains backlog context, not an active blocker
  for this governed push retry.
- 2026-04-15: Closed the remaining event-backed compat bridge-projection gap
  that was still blocking governed push after the bridge metadata repair. The
  bridge-backed `latest/review_state.json` already carried the typed compat
  bridge projection, but `projections/latest/review_state.json` was still
  emitting `_compat.bridge_projection=null`, so
  `check_review_surface_consistency.py` reported
  `review_state_bridge_projection: missing` even though the live bridge-backed
  snapshot was correct. `review_channel/event_projection_support.py` now
  backfills the compat bridge projection through
  `build_bridge_projection_state()` whenever event-backed enrichment inherits
  no persisted bridge projection, and
  `review_channel/event_projection_assembly.py` now loads the bridge text plus
  snapshot once and passes the current-session/runtime/packet inputs through
  that compat reducer. Focused proof is green on
  `tests/review_channel/test_event_projection_push.py`; `check_code_shape.py`
  is green too; and live repo proof is green after one bridge-backed status
  refresh, one event-backed inbox refresh, and one startup refresh:
  `check_review_surface_consistency.py` now reports
  `review_state_bridge_projection=snap-401c698949d6` in lockstep with
  `review_state`, `compact`, `turn_authority`, and `startup_context`. Local
  dogfood is recorded as `dogfood-6f0699440b1d`; next step is the governed
  commit/push retry plus fresh Claude dogfood on the landed slice.
- 2026-04-15: Closed the event-backed action-request queue hot path that was
  making `review-channel post` / `inbox` look hung during Codex<->Claude
  coordination. The root cause was not event-log reduction itself:
  `refresh_event_bundle()` timed at about 1.5s on 18.8k events. The slowdown
  was the queue reducer rebuilding a context-graph escalation packet for the
  selected pending `action_request` on every read, which bloated
  `derived_next_instruction_source` and turned simple coordination commands
  into multi-second or timeout-prone operations. The shared queue path now
  skips context-packet construction for selected `action_request` packets
  while keeping the actionable summary plus control metadata intact. Added the
  focused regression in `test_context_injection.py` and kept the existing
  plan-packet action-request tests green. Live proof is green too:
  `review-channel --action inbox --target claude --terminal none --format json
  --execution-mode markdown-bridge --limit 1` now returns in about 2.242s on
  the current repo state, and Claude acked the clean observer request
  `rev_pkt_0547` while the malformed duplicate `rev_pkt_0546` and timing probe
  `rev_pkt_0548` were dismissed to keep the queue clear.
- 2026-04-15: Closed the live `rev_pkt_0534` / `rev_pkt_0535` attention split
  by fixing the producer, not the renderer. Event-backed review-state
  enrichment now attaches typed conductor session state through
  `status_projection_helpers.attach_conductor_session_state()` before
  `build_recovery_assessment()` runs, matching the bridge-backed
  `refresh_status_snapshot()` path. Focused proof is green on
  `test_event_projection_push.py` and the current-session regression, and live
  proof is green on `review-channel --action status --refresh-bridge-heartbeat-if-stale`,
  `startup-context --format json`, and `dashboard --format json`: all three
  now emit `attention.status=review_loop_relaunch_required` while checkpoint
  guidance stays in `advisory_action=checkpoint_before_continue` and
  `push_decision=await_checkpoint`. Claude's follow-up findings
  `rev_pkt_0539`, `rev_pkt_0540`, and `rev_pkt_0541` are acked; the next
  blocker is no longer cross-surface drift but the real runtime boundary
  (reviewer loop not live) plus the authoritative `docs-check
  --strict-tooling` maintainer-doc gate for this `bundle.tooling` slice.
- 2026-04-15: Closed one live governance-review error-handling defect in the
  hot control-plane path instead of leaving `rev_pkt_0535` as background
  signal. `runtime/control_plane_resolve.py::load_git_state()` no longer
  swallows `OSError` / `subprocess.TimeoutExpired` and returns a fake
  `unknown/clean` git snapshot; it now raises `ControlPlaneGitStateError`
  with causal `from exc` context, and `build_control_plane_read_model()` keeps
  that fail-closed behavior instead of suppressing it upstream. Focused proof
  is green on the new `GitStateFailureTests` plus the existing control-plane
  read-model regressions, and `check_code_shape.py` stays green after the
  helper extraction.
- 2026-04-15: Fixed the stale typed-packet visibility bug on the event-backed
  inbox path. `review-channel --action inbox --status expired` was returning an
  empty packet list even while the same report admitted
  `queue.stale_packet_count > 0`, because the reducer only matched literal
  `status=="expired"` rows and ignored the far more common case of pending
  rows whose TTL had elapsed. `filter_inbox_packets()` now treats
  `status=expired` as expired-unresolved semantics, while
  `event_watch_support.load_target_packets()` refuses to stamp
  `delivery_observed_at_utc` on non-pending debug/observer reads. Focused
  regression proof is green on the reducer and event-action tests, live
  `review-channel --action inbox --target codex --status expired --terminal none --format json --limit 5`
  now returns stale packet rows (`rev_pkt_0502`, `rev_pkt_0501`, `rev_pkt_0500`,
  `rev_pkt_0489`, `rev_pkt_0486` at proof time), dev-mode dogfood is recorded
  as `dogfood-503289bbafec`, and Claude observer acceptance landed as
  `rev_pkt_0511`: live expired-inbox visibility PASS, pending-inbox remains
  live-only, and the explicit observer-boundary probe found `0` fresh delivery
  mutations across the sampled stale `action_request` rows.
- 2026-04-15: Closed the follow-up gap Claude reported in `rev_pkt_0512`.
  The first expired-inbox repair kept stale packets out of the live actionable
  queue, but reviewer-facing summaries still trusted stale bridge prose and
  could silently reduce expired-unresolved work to `none` or a stale pending
  count. Added a shared packet-backed open-findings summary path that rebuilds
  inbox truth from packet rows, emits `expired unresolved review packet(s)`
  when the live queue is empty but stale work remains, and reuses that summary
  in event-backed current-session/bridge reducers, control-plane blocker
  reduction, and `session-resume`. Focused proof is green on
  `test_current_session_projection.py`, the new runtime reducer unit test, and
  the new `session-resume` build test. Live proof is also green:
  the event-backed reducer now reports `queue.pending_total=0` together with
  `current_session.open_findings=193 expired unresolved review packet(s)`, and
  `session-resume --role reviewer --format json` now surfaces the same expired
  summary in both `open_findings` and `blockers`. Recorded dev-mode dogfood as
  `dogfood-598ee3d0e5ff`; Claude re-dogfooded the reviewer-facing command
  surface under `dogfood-34c28f1b9410`, posted PASS in `rev_pkt_0515`, and that
  acceptance packet is now acked.
- 2026-04-15: Recorded a new operator-raised design flaw under
  `MP377-P1-T06/T08`: the repo still exposes a split authority model where
  typed packet inbox truth can coexist with bridge-local `Claude Ack`,
  `current_session`, and heartbeat compatibility fallbacks in startup/session
  wait routing. Live evidence this session was contradictory by construction:
  the standing Codex packet watcher accepted and cleared Claude packets, but
  markdown-bridge `review-channel --action status` still refused heartbeat
  refresh because the implementer ACK compatibility section was missing, and
  `startup-context` continued to route toward a stale bridge-local
  `current_slice`. The follow-up slice is to make packet-backed inbox truth plus
  typed liveness the only continue-vs-wait source, leaving bridge prose as a
  compatibility projection instead of a blocker-capable authority path.
- 2026-04-15: Bridge-backed status/ensure now share the live review-state seed
  path used by startup/session-resume instead of the cached status projection.
  Status and bounded ensure-follow both emit the plan-backed MP-377 foundation
  `current_slice`, `current_session.current_instruction=""`, and
  `open_findings=193 expired unresolved review packet(s)`, and the stale
  `Current instruction revision` bridge-validation error is gone when there is
  no live instruction to acknowledge. Persisted `latest/review_state.json` now
  carries the same authority/coordination slice. Remaining blocker after this
  slice is the real approval-boundary/runtime fault only:
  `Reviewer mode is active_dual_agent but no live repo-owned Codex or Claude
  conductor sessions are present`, which still requires an operator-approved
  `review-channel --action launch` / `rollover`. Dogfood record:
  `dogfood-e09b02277d9d`. Claude observer request `rev_pkt_0528` is pending.
- 2026-04-15: Mandatory bootstrap exposed a fresh repo-owned runtime bug in
  the canonical repair path itself: `review-channel --action ensure --follow`
  crashed inside `follow_stream.emit_follow_ndjson_frame` because the
  ensure-follow publisher attached typed `MonitorSnapshotPaths` from
  `write_latest_monitor_snapshot()` directly to the follow report. Fixed the
  serializer boundary instead of the caller by normalizing dataclasses,
  `to_dict()` contracts, and `Path` objects before NDJSON emission. Focused
  proof is green on `python3 -m unittest
  dev.scripts.devctl.tests.review_channel.test_follow_controller
  dev.scripts.devctl.tests.runtime.test_monitor_snapshot`, and the live repair
  command now succeeds in bounded mode with
  `--max-follow-snapshots 1`. Recorded dev-mode dogfood for
  `command:review-channel.ensure_follow` and posted Claude observer
  action-request `rev_pkt_0505` so acceptance/finding traffic stays on the
  repo-owned review channel rather than chat.
- 2026-04-15: Re-read the governed startup/status surfaces and converted the
  operator's "one real plan, one real dogfood loop" directive into explicit
  umbrella-plan execution order instead of more chat-only guidance. The
  current convergence order is now repo-visible:
  `MP377-P1-T04/T05` plan-registry authority first,
  `MP377-P1-T06/T07/T08` runtime snapshot plus mutation plus liveness second,
  then `MP377-P2-T05/T06` dogfood-engine and observer-boundary enforcement.
  The matching dogfood contract is also repo-visible here: Codex implements
  and records dev-mode dogfood, Claude stays in observer/tester mode and
  records findings/acceptance through packets plus dogfood/governance rows,
  and a slice only closes after tests, live command proof, packeted dogfood
  verdict, and `LIVE_RUN.md` closure all agree.
- 2026-04-15: Read the full active-plan set named by the operator,
  reread `dev/audits/LIVE_RUN.md` Q1-Q100, and reconciled that material with
  live runtime evidence from `startup-context`, review-channel inbox,
  `findings-priority`, and `dashboard`. The outcome is not a new plan file;
  it is the consolidated redesign note plus new typed tasks in this umbrella
  plan: single-producer reviewer/runtime closure (`MP377-P1-T06`), mutation
  self-healing against stale projections (`MP377-P1-T07`), typed liveness
  signals (`MP377-P1-T08`), dogfood as the development engine
  (`MP377-P2-T05`), and observer-boundary enforcement (`MP377-P2-T06`).
  The audit clusters driving this order are now explicit too:
  `Q29`, `Q35-Q37`, `Q41-Q50`, `Q51-Q75`, and `Q90-Q100`.
- 2026-04-15: Landed the first concrete read-model repair from that redesign.
  `ControlPlaneReadModel` daemon resolution now treats the OS-backed heartbeat
  artifact as authoritative whenever it exists, instead of letting stale
  bridge/review-state `publisher_running` / `reviewer_supervisor_running`
  booleans override a dead process. This closes the live operator symptom where
  `review-channel status` already reported dead daemons while
  `devctl dashboard` still rendered `Publisher RUNNING`. Focused proof is
  green on `test_control_plane_read_model.py` and the dashboard heartbeat/health
  subset, and live `dashboard --format terminal` now renders
  `Publisher STOPPED`, `Supervisor STOPPED`, and `Active daemons 0` on the repo
  state that originally reproduced the contradiction.
- 2026-04-14: Closed the current review-channel follow-up slice for
  `rev_pkt_0424`, `rev_pkt_0426`, and the bounded `rev_pkt_0428` wake path in
  repo code. Dashboard terminal/markdown renderers now treat repo-owned
  conductor sessions with `alive=true` and no pid as `RUNNING` instead of
  `NO SESSION`, `ControlPlaneReadModel.pending_action_requests` now counts
  only live `kind="action_request"` packets instead of every pending packet
  kind, and the ensure-follow publisher now has a repo-owned
  remote-control-only wake helper that relaunches a stuck Codex reviewer
  session once per unobserved Codex-targeted action request after best-effort
  cleanup of the parked session. Focused proof is green on the new/updated
  regression coverage in `test_dashboard.py`,
  `test_control_plane_read_model.py`,
  `test_follow_controller.py`, and
  `test_follow_controller_reviewer_wake.py`; the broader file-level rerun
  still carries two pre-existing branch-red `test_control_plane_read_model.py`
  phase expectations (`test_push_eligible_from_receipt`,
  `test_guard_fail_overrides_push_eligible`) unrelated to this packet slice.
- 2026-04-14: Closed dogfood packet `rev_pkt_0391`, the `plan_*_review`
  CLI contract drift from `rev_pkt_0389` / `rev_pkt_0412`, and the
  dangerous action-gate portion of `rev_pkt_0413` in repo code. `auto-mode`
  no longer reports push/checkpoint-forward phases when both reviewer and
  implementer are dead; it now falls back to `phase=reviewing` with a
  live-participant-resume transition, and the startup blocker reducer now
  tolerates empty `open_findings` summaries instead of tripping on a
  packet-only backlog. `session-resume` now derives
  `safe_to_continue` / `checkpoint_required` from the shared
  `push_enforcement` truth, while both review-channel projection paths route
  coordination through `load_coordination_snapshot`, so startup-context,
  session-resume, status, and doctor now all block edit/stage/commit against
  the same dirty-budget state instead of splitting permissive vs restrictive.
  The same slice also makes `review-channel --action post` document the
  `plan_gap_review` / `plan_patch_review` requirements in help output
  (`--target-kind plan`, `--target-ref`, `--target-revision`, at least one
  `--anchor-ref`, `--intake-ref`, and `--mutation-op` only for
  `plan_patch_review`). Focused proof is green on
  `test_auto_mode.py`, `test_startup_blocker_decision.py`,
  `test_session_resume.py`, `test_event_projection_push.py`, the
  plan-review/help surface tests in `test_plan_packets.py` and
  `test_review_channel.py`, and on `check_code_shape.py`,
  `check_python_dict_schema.py`, `check_python_cyclic_imports.py`, and
  `check_platform_contract_closure.py`. `rev_pkt_0414` is now acked as the
  next architecture request for a typed WakeSignal / fanout / consumer-
  registry lane after this checkpoint.
- 2026-04-14: Closed dogfood packet `rev_pkt_0393` in repo code. The
  dashboard/status read side now publishes a small top-level JSON header
  contract through `dashboard_header.py`
  (`status`, `owner`, `next_action`, `top_blocker`, `pending_count`,
  `pending_findings_count`, `next_actor`, `next_command`), the health/liveness
  cluster moved into `dashboard_health.py` without breaking the legacy
  `dashboard._build_health_section` / `_read_heartbeat` /
  `_read_conductor_liveness` / `_pid_is_alive` compatibility seams that the
  dashboard tests still import directly, and `build_snapshot` now preserves
  the raw `review_state` payload for dashboard extraction so doctor fields stay
  visible even when the typed round-trip narrows the projection. The same
  slice also makes `coordination.pending_count` / `pending_findings_count`
  integer-first and teaches the blocker reducer to prefer typed pending packet
  totals over stale `"1 pending review packet(s)"` prose when that blocker
  string is otherwise reused across dashboard/status surfaces. Proof is green
  on `test_startup_blocker_decision.py` plus `test_dashboard.py`
  (`227 passed`), and on `check_code_shape.py`,
  `check_python_dict_schema.py`, `check_python_cyclic_imports.py`, and
  `check_platform_contract_closure.py`. Packet-backed follow-on work on this
  lane is now narrowed to `rev_pkt_0391` / `rev_pkt_0392`.
- 2026-04-14: Closed the live `session-resume` JSON exit-code regression from
  dogfood packet `rev_pkt_0396`. The current startup/session-resume builders
  now agree in-process on the single-agent authority path
  (`coordination_state=single_agent_authoritative`,
  `implementation_permission=active`, edit/stage/commit allowed), so the
  remaining concrete CLI bug was the machine-output contract: `session-resume
  --format json` emitted a valid `SessionCachePacket` but still exited `1`
  whenever `blockers != none`. `emit_machine_artifact_output` now supports
  an explicit `exit_zero_on_non_ok` lane, `emit_governance_command_output`
  threads that option through, and `session-resume` uses it only for JSON
  output so receipts can keep `ok=false` while automation still receives an
  exit code `0` on successful emission. Focused proof is green in
  `test_machine_output.py` plus `test_session_resume.py`, and a live
  `python3 dev/scripts/devctl.py session-resume --role implementer --format json`
  run now exits `0` while still reporting
  `blockers="8 pending review packet(s)"`. The next same-lane packet work
  remains `rev_pkt_0391` / `rev_pkt_0392` / `rev_pkt_0393`
  (auto-mode phase drift, silent `watch --follow`, and dashboard pending-count
  drift).
- 2026-04-14: Closed the remaining authority-snapshot parity leak in the
  live review-channel write path instead of leaving it as packet-only dogfood
  evidence. `projection_bundle`, `reviewer_runtime_snapshot`, `status`,
  `session_resume_authority_payload`, `session_resume_support`, and
  `action_routing_coordination` now all reuse the same blocker-aware
  `AuthoritySnapshot` plus startup-derived control-topology truth, so the
  event-backed `review_state.json` bundle and the emitted `compact.json` /
  `full.json` projections now agree on
  `coordination_state=resync_required`,
  `next_command=python3 dev/scripts/devctl.py review-channel --action status --terminal none --format json`,
  `observed_control_topology=single_implementer_single_reviewer`, and
  `implementation_permission=active`. The same dogfood pass also moved
  Codex-to-Claude coordination back onto the typed packet lane via
  `rev_pkt_0394`, which asks Claude to keep reporting authority drift through
  review packets. The next active follow-on findings are now explicit in the
  packet ledger too: `rev_pkt_0391` (`auto-mode` enters `phase=pushing`
  while reviewer/implementer are not live), `rev_pkt_0392`
  (`watch --follow` emits no start/heartbeat/exit signal when zero packets
  match), and `rev_pkt_0393` (dashboard/status pending-count drift and
  missing top-level owner/next-action fields). Persisted `PlanRegistry`
  authority plus markdown projection remains the next foundation closure
  after these live runtime parity regressions.
- 2026-04-14: Closed dogfood packets `rev_pkt_0392` and `rev_pkt_0400` in
  repo code with live proof instead of stopping at unit green. The hot-path
  pacing reader now resolves the newest saved graph snapshot without parsing
  the full snapshot directory, so `review-channel --action watch --follow`
  emits its first frame immediately again on the current repo state. The
  watch loop now also self-governs through a target/status-scoped
  single-flight lifecycle file: one live watcher owns the lane, unchanged
  polls emit `watch_heartbeat`, competing launches exit immediately with
  `single_flight_conflict`, parent loss is treated as a stop condition, and
  Ctrl-C emits a final `watch_exit`. Live dogfood caught one follow-up bug in
  the first pass too: the lifecycle file was opened with `a+`, so repeated
  heartbeats appended multiple JSON documents. That regression was patched in
  the same slice (`touch()` + `r+`) and pinned by
  `test_watch_lifecycle.py`, then re-verified with a real watch-follow run
  whose state file now parses as one JSON object with
  `stop_reason=keyboard_interrupt`. Focused proof is green on
  `test_snapshot.py`, `test_work_intake_pacing_snapshot_preference.py`,
  `test_watch_lifecycle.py`, and the `watch_follow` slice of
  `test_review_channel.py`; live artifacts are
  `/tmp/review_watch_live2.ndjson`, `/tmp/review_watch_conflict2.ndjson`, and
  `dev/reports/review_channel/watchers/watch_claude__pending.json`. Current
  same-lane packet work is now `rev_pkt_0391`; the live queue still reports
  `stale_packet_count=246`, but that backlog is being treated as separate
  hygiene debt unless it re-enters the packet lane as a causal bug.
- 2026-04-13: Closed the first architecture-review follow-up in the owner
  chain instead of leaving `authority_snapshot_3_fields_missing` as a prose
  complaint. `dev/scripts/devctl/runtime/authority_snapshot.py` now carries
  the shared `AuthoritySnapshot` reducer/projector, `StartupContext` and
  `SessionCachePacket` persist that reduced contract directly, and
  `review-channel --action status|doctor` now projects the same object over
  reviewer runtime, current-session ACK state, coordination posture, packet
  target, and next-command routing. The semantics are explicit: active
  dual-agent instruction-revision drift with a stale implementer ACK is now
  the first-class `handshake_stale` authority state, not just a generic
  blocked loop. The next queued foundation work is still bridge-authority
  demotion, then persisted `PlanRegistry` plus markdown projection.
- 2026-04-13: Ingested Claude architecture-review packets `rev_pkt_0375`
  through `rev_pkt_0378` into repo-visible execution state instead of leaving
  them in the typed inbox only. The corresponding architecture findings are
  now present in the canonical `governance-review` ledger
  (`dogfood_finding_id_instability`, `dogfood_read_only_registration_missing`,
  `plan_markdown_projection_missing`, `plan_authority_gap`,
  `bridge_authority_conflict`, `bridge_metadata_parsed_as_authority`,
  `authority_snapshot_3_fields_missing`, `agents_md_dual_purpose_conflict`),
  and the owner-plan execution order is now explicit: authority snapshot
  reduction first, bridge-authority demotion second, persisted
  `PlanRegistry` + markdown projection third, then scenario-runner /
  multi-agent dogfood widening.
- 2026-04-13: Closed the remaining `MP377-P0` findings-write gap. The
  canonical `FindingBacklog` writer now backs `governance-review --record`,
  `devctl dogfood --record --record-governance` can auto-record linked
  `signal_type=dogfood` findings with stable ids plus refreshed
  review-summary artifacts using live target-path defaults and optional
  overrides, and the governance/dogfood ledger helpers now resolve from the
  runtime repo root rather than the baked-in VoiceTerm root. That leaves
  persisted `PlanRegistry` authority plus markdown projection rendering as
  the next foundation closure before the multi-agent dogfood runner expands.
- 2026-04-13: Landed the first repo-owned dogfood engine slice instead of
  keeping system-test coverage in packets and prose. `devctl dogfood` now
  records explicit `DogfoodRun` rows under `dev/reports/dogfood/runs.jsonl`,
  refreshes `dev/reports/dogfood/latest/summary.{md,json}`, derives coverage
  from the live command catalog plus registered guard/probe entrypoints
  instead of fixed counts, and `governance-review` now accepts
  `signal_type=dogfood` so dogfood-discovered failures can close out in the
  canonical findings ledger. The same slice also hardened governed push:
  active bridge preflight now refreshes typed review status and reprojects
  `bridge.md` before the blocking checks run, so stale role-specific marker
  drift no longer strands publication. The next foundation work is to unify
  dogfood failures with stable `FindingBacklog` ids and then move `MP-377`
  plan authority from mutable markdown reads to persisted `PlanRegistry`
  state plus rendered projections.
- 2026-04-13: Closed the live dogfood walkthrough parity regressions in the
  main `MP-377` owner chain instead of leaving them as dashboard/operator
  folklore. `startup-context` now promotes `active_target` from live
  planning/finding state, `session-resume` reuses that same coordination path
  instead of re-deriving stale continuity targets, startup
  `quality_signals` now carries a bounded `finding_backlog` summary,
  `review-channel --action status` can refresh `bridge.md` from typed
  `_compat.bridge_projection` state even when pending reviewer packets still
  exist, dashboard plan counts now prefer typed actionable packet truth, and
  context-graph now exposes `PlanPhase` / `PlanTask` / `FindingBacklog`
  contract nodes plus task-id aliases such as `MP377-P0-T01`. The next proof
  slices should keep following the same rule: every new typed contract or
  route must land with both a producer and a consumer proof, not just a data
  model plus prose.
- 2026-04-12: Absorbed the latest dashboard architecture review into the main
  `MP-377` owner chain instead of leaving it as packet/chat-local guidance.
  The repo already encodes most of the desired architecture, but it is still
  scattered: multiple status surfaces describe the same blocker with
  different vocabularies, findings split across packets/runtime markdown, and
  some agent/dashboard lanes still poll or infer work from message silence.
  The prioritized closure is now explicit in plan state: Phase 0 visibility
  first (`FindingBacklog`, single governed snapshot/root, packet lifecycle
  plus event wake, live tool-call visibility), Phase 1 autonomy second
  (`devctl develop` as a composition surface over those inputs).
- 2026-04-12: Revalidated the default remote-control topology from the
  six-hour dogfood session. The active startup/runtime authority on the
  primary lane already says `worktree_strategy=shared_primary_worktree` and
  default worker fanout zero, so the remote-control reviewer/implementer/
  dashboard trio must share the governed primary checkout unless an explicit
  delegated worker is launched. Isolated worker worktrees remain an opt-in
  fanout capability with their own typed lane/worktree identity and
  worktree-bound commit/push approval; they are not the default path for
  everyday concurrent Claude remote-control plus Codex coding. The rejected
  linked-worktree/shadow-gitdir detour was a workaround caused by checkpoint
  confusion, not part of the architecture. The next closure is to teach this
  default through bootstrap/dashboard/status surfaces so agents stop
  improvising extra checkouts.
- 2026-04-12: Planned the Q55 findings-convergence closure from live dogfood
  evidence instead of more bridge-era prose. `findings-priority` still ranks
  134 `LIVE_RUN.md` findings from markdown parsing, `event_open_findings()`
  currently collapses live state into generic `N pending review packet(s)`
  text, dashboard still shows `Open findings: 0`, and `monitor` emits
  `should_emit_finding=True` with no durable consumer. The next bounded
  closure is now explicit: introduce one repo-owned `FindingBacklog`
  loader/snapshot over canonical finding rows, make
  `review-channel --action post --kind finding` append those rows with stable
  `finding_id` plus a human `Q-ID` projection and packet lineage,
  preserve `governance-review` as the disposition sink against the same ids,
  reroute dashboard/startup/monitor/bridge/findings-priority through that
  reader, and demote `LIVE_RUN.md` to compatibility import/projection only.
- 2026-04-12: Closed the live commit deadlock in the main `MP-377` owner
  chain. The governed commit boundary still treats checkpoint authority as
  narrower than general implementation authority: when startup explicitly
  routes the current lane to `advisory_action=checkpoint_allowed` /
  `push_decision=await_checkpoint` with
  `reviewer_gate.checkpoint_permitted=true`, `devctl commit` may still
  advance the repo-owned checkpoint path while raw `git commit` remains
  blocked. The same dogfood pass also tightened read-side authority for
  review state: when governance still points at the legacy
  `.../review_channel/latest` compatibility root, the loader now prefers the
  sibling event-backed `projections/latest/review_state.json` bundle and
  keeps that path authoritative even for live-refresh callers. The next
  architecture step is shared status/doctor wording plus the single typed
  findings ledger shared by packets, dashboard, and LIVE_RUN-derived triage,
  not another raw-git exception or bridge-era cache.
- 2026-04-12: Closed the next role-portability/runtime-identity slice in the
  main `MP-377` owner chain. Typed review/status consumers now prefer
  provider-neutral reviewer/implementer aliases
  (`reviewer_poll_state`, `last_reviewer_poll_*`, `implementer_ack*`) while
  preserving the legacy `codex_*` / `claude_*` bridge fields as compatibility
  projection only, so role-first launch/bootstrap rules finally line up with
  read-side status truth. The same slice also made governed mutation/publish
  approval worktree-bound: the staged remote-commit pipeline, persisted push
  authorization, latest-push artifact, and current checkout now compare one
  typed `worktree_identity`, fail closed on worker-vs-control-lane drift, and
  project the current/approved worktree identity through startup/push status
  instead of leaving that boundary implicit in shell lore. The next proof is
  the live beta matrix rerun on
  `Codex reviewer + Codex worker implementer + Claude dashboard`, not another
  provider-specific fallback.
- 2026-04-12: Started the explicit provider-role portability closure under the
  main `MP-377` owner chain. The architecture docs already say launch,
  bootstrap, collaboration, and remote-control authority are role-first, but
  the live runtime still carries provider-shaped seams in the default role
  registry, turn-authority helpers, bridge projection names, handoff poll
  fields, and same-provider rollover assumptions. The closure order is now
  explicit and bounded: keep the default remote-control lane on the governed
  shared primary checkout while requested worker fanout is zero, treat
  isolated worker worktrees as explicit delegated-worker fanout only, converge
  the provider-coded surfaces onto typed role/actor assignment over the same
  backend, prove the resulting beta matrix in VoiceTerm, and only then widen
  the same role/mode proof to the external-repo ladder in
  `portable_code_governance.md`.
- 2026-04-11: Closed the governed-push latest-artifact visibility gap inside
  the shared platform owner chain. The canonical `dev/reports/push/latest.json`
  surface now advances through `push_preflight_running`, `push_pending`, and
  the existing post-`git push` publication snapshot instead of staying on the
  last completed report until the next terminal state. Startup also now
  treats a current-head in-flight push artifact as "wait for the running
  governed push" so repo-owned surfaces stop guessing from stale prior
  receipts.
- 2026-04-11: Started the bootstrap/client-vs-core surface slice under
  `MP-377`. The owned change set is intentionally narrow: generated
  instruction surfaces and starter setup docs should now say that the current
  repo is a first-party client/product integration over the portable
  governance platform, while repo packs and typed runtime contracts remain
  backend authority for arbitrary repos. Keep the wording portable so adopter
  repos inherit the same thesis with their own product identity.
- 2026-04-11: Followed that slice with a local-takeover authority correction.
  The current repo policy for this session now resolves back to
  `local_terminal`, and the startup/coordination reducers treat sanctioned
  `single_agent` local takeover as active local implementation authority
  instead of misclassifying it as `remote_control` plus blocked dual-agent
  runtime.
- 2026-04-10: Started the Q64/Q54 bounded intake-governance closure under
  `MP-377`. The first slice keeps both fixes in existing repo-owned surfaces:
  `WorkIntakePacket` now needs one typed `session_pacing` projection derived
  from planning IR plus current graph adjacency so startup can emit a bounded
  research-to-first-patch read set, and `governance-review` needs to accept
  `signal_type=observer` plus optional `finding_type` so observer/self-audit
  evidence reuses the canonical adjudication ledger instead of staying in
  audit prose.
- 2026-04-10: Started Q40/Q42 as the next deterministic action-boundary
  slice after the Q47/Q45/Q43 authority spine. Startup-context now needs to
  split non-destructive `control_recovery_action` hints from destructive
  `recovery_action` authority, prove `recovery_basis` before relaunch or
  termination, and expose a lane edit gate so dashboard/observer callers route
  defects through findings or packets when a live implementer owns the lane.
- 2026-04-10: Started Q47/Q45/Q43 deterministic action-routing closure as a
  bounded authority-loop slice. `startup-context` now projects a typed
  action-routing packet and `agent_lane` permissions for dashboard,
  implementer, observer, and reviewer callers; `devctl commit` now evaluates
  `CommitPermissionDecision` before staging or running guards so
  `implementation_permission=blocked|suspended` cannot be mistaken for commit
  authority. Remaining work is to widen the same packet through status,
  doctor, dashboard, hooks, pre-edit/pre-launch gates, and destructive
  recovery.
- 2026-04-10: Started Q38's observed control-topology closure as a bounded
  startup-authority slice, not a full pack/worktree routing rewrite. The new
  `dev/scripts/devctl/runtime/control_topology.py` reducer derives
  `observed_control_topology` from supervised conductor counts, bridge
  liveness, and runtime counts, maps it to `implementation_permission`, and
  projects both through `startup-context` summary, markdown, and machine-summary
  output. The remaining Q38 closure is the hard gate: bind launch/edit
  permission to these fields plus mandatory pack/worktree lane assignment.
- 2026-04-10: Promoted the issue-to-guard learning-loop audit into the
  existing `MP-377` governance closeout path rather than creating a new plan.
  The first implementation is intentionally small: `FindingReview` remains the
  canonical adjudication row, while `prevention_surface=guard|probe` now emits
  a `GuardPromotionCandidate` queue entry that the governance-review JSON
  summary exposes. Full guard scaffolding, validation, and auto-registration
  remain future work behind that queue.
- 2026-04-09: Closed the next remote-control convergence seam without
  creating a second runtime registry. External Claude phone sessions can now
  be written into typed repo-owned state through
  `review-channel --action attach-remote-control`, persisted as a canonical
  review-status sidecar, and projected back out through
  `ReviewerRuntimeContract`, `ControlPlaneReadModel`, `StartupContext`, and
  `SessionCachePacket`. This is the same `MP-377` pattern as the rest of the
  platform work: one write path, one typed owner, many projections. The
  paired wrapper/hook follow-through matters too: `remote-bridge-loop.sh`
  now records external remote-control presence into typed state instead of
  keeping it only in chat memory, and the managed pre-push hook now prints
  typed next-step guidance from `startup-context` instead of a static
  fallback string.
- 2026-04-09: Closed the next hook-registration self-hosting gap instead of
  treating it as "just config drift." The graph-backed
  `mutation_bypass_graph_closure` guard is now promoted through the same
  portable typed surfaces the rest of `MP-377` is trying to standardize:
  `portable_python.json` enables it in the resolved AI-guard inventory,
  `bundle.tooling` / `bundle.release` plus their owning workflows run the
  public entrypoint directly, and maintainer docs now state the closure rule
  explicitly: a new shared guard is not done until script catalog, typed
  quality policy, bundle/workflow parity, and docs-governance all agree on the
  same lane. This is the practical hook-driven pattern the user keeps pushing
  for: move repeated "remember to wire this up" work into deterministic
  registry + workflow + docs checks so startup/commit/push can trust receipts
  earlier.
- 2026-04-09: Closed the next generated-bootstrap convergence seam under
  `MP-377` without creating a second graph or bootstrap authority. The
  generated bootstrap command inventory now lives in
  `dev/scripts/devctl/governance/system_catalog_bootstrap.py` as typed
  `SystemCatalog` entries with command/contract/plan links and bounded
  inventory relations; `context-graph` consumes those entries directly
  instead of reparsing rendered markdown; and bootstrap capability nodes now
  link into the graph so commands, guards, probes, surfaces, and plan docs
  can be queried from one repo-owned discoverability layer. The startup-token
  budget guard also forced the right boundary into code: rich relations stay
  in `SystemCatalog` / `discover`, while `BootstrapContext` now carries only a
  summarized typed view plus stable handles. Focused proof is green:
  `pytest dev/scripts/devctl/tests/governance/test_system_catalog.py
  dev/scripts/devctl/tests/governance/test_render_surfaces.py
  dev/scripts/devctl/tests/context_graph/test_context_graph.py
  dev/scripts/devctl/tests/context_graph/test_snapshot.py -q --tb=short`
  (`137 passed`), plus `check_parameter_count.py`,
  `check_code_shape.py`, `render-surfaces --write --format md`,
  `check_active_plan_sync.py`, and `check_agents_contract.py`. The next
  follow-up is not "stuff more graph data into startup"; it is a generated
  convergence-audit artifact that both Codex and Claude can consume from the
  same repo-owned path while deeper graph/state detail stays cached on disk.
- 2026-04-09: Closed the reopened MP-384/MP-387 F1 command-boundary parity
  flake. The runtime fix is intentionally narrow: `session-resume` cache
  misses now force a live `load_current_review_state(... prefer_cached_projection=False)`
  snapshot, dashboard resolves governance plus current review state once per
  snapshot before reusing that same typed payload for `load_sources()` and
  `ControlPlaneReadModel`, and the focused parity pytest bundle is green on
  consecutive runs. The remaining follow-up stays inside the same owner chain:
  keep the rest of the read-side consumer inventory on one frozen review-state
  tick, then rerun the live remote-control proof before widening again.
- 2026-04-09: Absorbed the latest typed-authority + guard-intelligence review
  without creating a shadow tracker. Two live outcomes are now explicit in
  the main product plan: first, the repo-owned startup packet reopened
  MP-384/MP-387 F1 on this tree, so the immediate runtime slice is freezing a
  single review-state / coordination proof tick across startup,
  `session-resume`, and `ControlPlaneReadModel` rather than widening new
  architecture work. Second, the guard-intelligence audit was accepted as a
  follow-on inside the existing owner chain, not as a new plan: hard-guard
  improvement should route through canonical guard-to-`Finding` translation
  plus one bounded feedback lens over `governance-review`, quality-feedback,
  scope, and graph churn; prompt-time failure-rule ledger / bad-pattern
  recall / trust-weighting stays with `review_probes.md`; and any adaptive
  routing must remain advisory until replay/corpus proof justifies stronger
  enforcement.
- 2026-04-08: Closed MP-384/MP-387 F1 and F4 (governance-quality-sweep
  lane) by making the three coordination proof surfaces structurally
  unified and the scan-based governance path fail closed on missing
  operator interaction mode. `build_startup_context` no longer builds
  its `CoordinationSnapshot` through a direct
  `build_coordination_snapshot(startup_context=SimpleNamespace(...))`
  path; it now delegates to `load_coordination_snapshot` with the same
  governance + review-state + reviewer-gate it already derived, leaving
  the direct build only as a bare-repo / legacy-fixture fallback. That
  removes the last remaining path where `startup-context --format json`,
  `session-resume --format json`, and `dashboard --format json` could
  silently disagree on `declared_topology`, `observed_topology`,
  `ownership_status`, or `resync_reasons` for one tree. F4 closes a
  separate fail-closed drift in `draft_policy_scan._scan_bridge_config`:
  it now reads `operator_interaction_mode` from
  `repo_governance.bridge_config` and resolves it via
  `resolve_operator_interaction_mode`, so
  `scan_repo_governance(policy={}).bridge_config.operator_interaction_mode`
  returns `unresolved` instead of silently inheriting `BridgeConfig`'s
  `local_terminal` default. Parity is locked in by
  `dev/scripts/devctl/tests/runtime/test_coordination_loader_wiring.py`
  (mock-based structural test plus two end-to-end tests across startup,
  read model, and direct loader) and new scan-path tests in
  `dev/scripts/devctl/tests/runtime/test_operator_mode_fail_closed.py`
  (`TestScanRepoGovernanceFailClosed`).
- 2026-04-08: Reframed the remaining coordination issue as a product-owned
  truth/projection closure gap, not a missing-schema gap. The repo now has
  enough typed coordination truth to answer owned slice, fanout safety,
  topology, and resync posture, but the most load-bearing launch/bootstrap
  surfaces still do not all read the same packet. The next bounded closure in
  `platform_authority_loop.md` + `remote_control_runtime.md` is explicit:
  carry `CoordinationSnapshot` through `ControlPlaneReadModel`, project it in
  `startup-context` summary/machine-summary and dashboard authority surfaces,
  and evaluate whether review-channel retarget + remote-control launch can be
  automated from typed plan/runtime state instead of a manual bridge rewrite.
- 2026-04-09: Closed one bounded repo-pack/read-model authority seam under that
  same truth/projection closure. `mobile-status` now builds
  `ControlPlaneReadModel` against the caller-selected `review_status_dir`
  bundle instead of silently reading the default repo-pack bundle, shared
  control-plane sources/review-state refresh now accept that override, and the
  thin-client review cache only reuses `full.json` / `review_state.json` when
  those projections are at least as fresh as the current `bridge.md` plus
  `review_channel.md`. The VoiceTerm thin-client wrapper now routes through the
  shared repo-pack helper instead of bypassing it. This keeps the remaining
  `MP-377` read-side closure focused on startup/dashboard/session-resume
  parity, minted identity, and live remote-proof orchestration rather than on
  another bundle-selection split.
- 2026-04-08: Closed the first multi-surface consumer loop on top of the new
  bounded coordination reducer. `CoordinationSnapshot` is now projected into
  startup, typed review-state/status, session-resume remote-control bootstrap,
  dashboard, doctor/status, and Claude prompt bootstrap so those surfaces no
  longer tell different stories about topology, fanout safety, worktree
  isolation, or resync need. The key runtime fix is explicit single-agent
  fallback: when the reviewer loop is inactive, bootstrap/dashboard can still
  see the active governed slice from startup/work-intake authority instead of
  treating stale review prose as the only visibility source.
- 2026-04-08: Landed the first bounded coordination projection that sits on
  top of the new planning/work-intake state instead of reopening bridge-only
  inference. `dev/scripts/devctl/platform/coordination_snapshot.py` now
  builds `CoordinationSnapshot` from the existing `WorkIntakePacket`,
  `CollaborationSession`, delegated-worktree receipts, ready gates, and the
  shared concurrent-writer conflict helper. The contract keeps the answer
  small but operational: declared vs observed topology, recommended topology,
  fanout posture, worktree strategy, resync reasons, and bounded actor
  exemplars. `system-picture` is the first consumer, so live repo snapshots
  now show the exact current mismatch in typed form: planned multi-agent
  scaffolding with isolated worker worktrees, but observed `single_agent`
  runtime and inactive reviewer-loop resync still blocking safe fanout.
- 2026-04-08: Landed the first higher-order scheduler reducer as typed code
  instead of another prose-only architecture note. The new
  `dev/scripts/devctl/platform/planning_ir.py` /
  `planning_ir_models.py` pair now builds `PlanningIRSnapshot` beside
  `SystemPicture`, joining live `PlanRegistry` / `PlanTargetRef` selection,
  recent governance-review findings normalized into `FindingRecord`,
  context-graph `scoped_by` ownership edges, and the current
  `WorkIntakeOwnershipState` / `WorkIntakeCoordinationState` projection. The
  first output set is intentionally bounded and operational rather than
  aspirational: rank a few `next_best_slices`, surface
  `concurrent_writer_conflicts`, flag `unowned_hot_paths`, and call out
  `plan_finding_mismatches`. Simulation tests now lock the three critical
  behaviors: active-plan slice ranking, fail-closed single-writer scheduling
  when topology/ownership conflict, and explicit reporting of unowned hot
  files plus off-target findings. The next step is projection and live-loop
  proof, not more raw-state accumulation.
- 2026-04-08: Closed the next bounded truth-source leak in the `MP-377`
  self-hosting lane. Bridge-backed review status/compat reads now prefer the
  persisted typed `current_session` and
  `reviewer_runtime.review_acceptance` state whenever `review_state.json`
  already exists, so live current-instruction/verdict findings no longer
  drift back to raw bridge prose. ReviewSnapshot now also projects first-class
  probe run-state/artifact refs plus current push receipt/authorization refs,
  which keeps external review surfaces grounded in typed emitted evidence
  rather than command-only suggestions. The same lane now pushes startup
  ownership truth through the typed path too: work-intake emits bounded
  dirty-slice ownership state, startup summaries surface that classification,
  and the startup-authority guard fails closed on
  `concurrent_writer_activity` instead of reporting concurrent uncontrolled
  writers as a generic dirty-budget block.
- 2026-04-11: Closed the next remote-control read-side parity gap in the
  `MP-377` owner chain. Single-agent bridge-backed status now merges active
  typed `remote_control_attachment` providers into conductor truth, and the
  shared daemon/read-model reducer treats an attached remote-control provider
  as live implementer authority before it falls back to stale
  `*-conductor.json` metadata. That keeps `review-channel status`, doctor, and
  `ControlPlaneReadModel` aligned during remote-control sessions even when the
  last Claude packet ages past the session-probe freshness window.
- 2026-04-07: Absorbed the ReviewSnapshot hardening audit as routed intake
  rather than a shadow plan. The accepted product-level work is cross-surface
  consistency for the snapshot, contract registration/schema coverage,
  generated-artifact integrity, load-bearing consumers for suggested commands
  and WhyRecord data, and later MCP / Agent SDK ecosystem adapters. Immediate
  path/doc-authority and commit/push slices stay in the subordinate owner
  docs so `MP-377` keeps one main active architecture plan.
- 2026-04-07: Clarified the hook expansion rule for that same intake. Hooks
  are valid trigger/entry surfaces for raw git, provider, session-start, and
  session-stop bypass closure, but they must delegate to typed `devctl`
  commands and verified receipts instead of carrying their own resolver,
  command, policy, or review logic.
- 2026-04-07: Accepted the commit/push validation-cadence correction into the
  main `MP-377` architecture lane. The portable rule is not "run everything on
  every edit" and not "trust an agent to choose fast vs full"; it is to emit a
  deterministic, tree-bound validation plan and receipt from repo policy, then
  require governed checkpoint/commit/push surfaces to consume that receipt.
  This sharpens the existing deterministic-validation lane: missing quality
  evidence must be `unknown` / `stale`, selected bundle/add-on/escalation
  reasons must be inspectable, and heavy proof remains at push/release
  boundaries unless repo-owned routing escalates a smaller slice.
- 2026-04-07: Rechecked the phase ordering after the operator asked whether
  the platform is building future surfaces ahead of their typed architecture.
  The order stays architecture-first: `MP-377` must close startup/repo-pack
  authority plus the narrow VCS validation-plan receipt before relying on
  smarter commit/push cadence; `MP-376` multi-repo matrix work remains the
  pressure-test lane for portability leaks, but Step-0/startup/governed-push
  failures discovered there route back into `MP-377` blockers instead of
  being worked around per adopter; dashboard/operator/frontends stay projection
  work after typed state exists, not a second backend.
- 2026-04-07: Accepted the portability-by-default review into the main product
  lane. The honest state is "portable by design, not yet portable by default":
  typed repo contracts exist, but remaining shared-layer defaults such as
  fixed VoiceTerm paths, bridge/tandem assumptions, local-terminal fallbacks,
  and fixed review/session-cache paths can still make adopters look like
  VoiceTerm unless manually babysat. The next order is hidden-default
  extraction, explicit capability gating, a static portability-drift guard,
  controlled fixture proof, and only then broader real-world repo trials.
  Contract closure should extend `SystemCatalog` / generated binding checks so
  capability and repo-pack fields cannot be added without dashboard,
  session-resume, phone/mobile, CI, and bootstrap projection coverage.
- 2026-04-05: Accepted the next portable architecture correction into the main
  `MP-377` plan after reviewing the user's "types vs comments/docstrings"
  framing against the current codebase and plan chain. The repo already had
  the right direction in `PYTHON_ARCHITECTURE.md`, but the active owner plans
  did not yet state the execution-order rule clearly enough: on governed
  platform paths, prefer typed structure first, validated transitions second,
  derived projections third, and explanatory prose last. The accepted scope is
  intentionally narrower than a repo-wide coding rule. Repo-pack/governance
  policy still decides where the governed boundary starts for any adopter
  repo; inside that boundary, stable concepts should graduate from plan name
  to typed contract to validator to projection to parity proof.
- 2026-04-05: Extended that same architecture correction to cover governed
  semantic docstrings as part of the platform rather than leaving them as chat
  theory. The accepted rule is strict: docstrings can add real value for AI
  navigation and semantic indexing only when they are structured, machine-
  validated, freshness-checked projections over canonical typed contracts.
  Product-owned follow-up is now explicit: define a portable
  `SemanticDocRecord` / `SemanticSymbolRecord`-style contract for selected
  governance symbols, route it through doc-authority/context-graph/discovery/
  bootstrap surfaces, let `ProjectGovernance` / `DocRegistry` own its
  lifecycle, and fail closed when semantic doc claims drift from the owning
  type/state-machine contract.
- 2026-04-05: Accepted the deeper semantic-routing correction after reviewing
  the repo's actual `SystemCatalog`, `AgentDispatchPacket`, `context-graph`,
  and ZGraph evidence. The right fit for this codebase is not "ZGraph as
  control-plane truth." It is "ZGraph as bounded search/ranking over typed
  truth." The plan now records the exact order: continuity/bootstrap first,
  deterministic narrowing second, semantic ranking third, proof/parity
  fourth. Product-owned next work is to turn `SystemCatalog` into the graph
  root, upgrade `AgentDispatchPacket` into a bounded frontier packet, and gate
  any semantic-routing promotion behind measurable non-inferiority on real
  repo tasks.
- 2026-04-05: Added an explicit truth-source convergence note after reviewing
  the user's "one backend truth, multiple projections" framing against the
  live runtime. The architecture target is correct, but the repo still has
  migration-time duplicate shapers: `ControlState` still accepts legacy
  `controller_payload` / `review_payload`, `session-resume` still performs
  some local extraction/reduction, and bridge compatibility surfaces still
  exist. The active plan now records the closure rule plainly: converge those
  readers onto `ControlPlaneReadModel` plus reduced packet contracts, keep
  compatibility payloads fallback-only, and delete overlap instead of letting
  it fossilize.
- 2026-04-05: Captured the self-hardening architecture correction in the main
  `MP-377` product plan after a codepath review of startup/work-intake,
  finding/review ledgers, probe decision packets, external-finding import, and
  quality-feedback snapshots. The accepted conclusion is explicit now:
  the repo already compiles typed evidence and reviewed outcomes, but it does
  not yet close the whole loop automatically. `TypedAction -> ActionResult ->
  RunRecord` is only partially live, misses still become new prevention
  surfaces through manual adjudication, and recommendation output is advisory
  rather than self-promoting policy. Product authority now preserves the
  boundary that should guide the next tranche: auto-fix only predeclared
  invariant violations, emit packets/review for ambiguous or behavior-shaped
  changes, and require candidate invariant capture plus replay/approval before
  any new guard/probe promotion.
- 2026-04-04: Accepted the architecture-audit extension/adopter follow-up into
  canonical `MP-377` plan authority before implementation. The tracked closure
  tranche is now explicit and product-owned: read-only `devctl`/MCP surfaces
  must stop mutating audit/telemetry artifacts implicitly, portable runtime
  Phase 2 must fail closed instead of falling through to VoiceTerm defaults,
  one repo-pack-owned `ExtensionBundle` must generate project-scoped
  Codex/Claude/MCP surfaces from typed governance state, and one
  `AutomationSpec` must let the same governed task run through local
  scheduler, GitHub workflow, Codex Automation, and Claude-facing
  command/agent surfaces without re-encoding policy in each transport.
- 2026-04-04: Re-froze the product-level proof boundary after the latest
  governed push. Branch publication is already recorded, but full green proof
  is blocked by commit-range code-shape debt, not by a missing push. The next
  accepted slice stays inside the existing `system-picture` / publication-
  truth owner chain: align current-target publication semantics across
  startup, review-channel, event-backed projections, and proof surfaces, then
  either land or explicitly debt-log the remaining shape cleanup before
  calling the slice green. The sanctioned many-agent proof path for that work
  is the bridge-gated review launch with `--codex-workers 0 --claude-workers
  3`.
- 2026-04-06: Closed the next self-hosting shape pass on that same post-push
  blocker without changing the underlying review-candidate/recovery contract.
  `review_candidate.py` now delegates text/command parsing and changed-path
  discovery to `candidate_parse.py` / `candidate_paths.py`,
  `recovery_assessment.py` delegates decision/evidence shaping to
  `recovery_decision.py` / `recovery_evidence.py`, and
  `review_state_models.py` re-exports collaboration dataclasses from
  `review_state_collaboration_models.py`. The same slice also clarified the
  reviewer takeover rule for self-hosting interruptions: if a live
  `active_dual_agent` reviewer conductor dies mid-slice, stop the detached
  daemons and re-establish reviewer truth through `single_agent`
  `reviewer-heartbeat` before continuing locally.
- 2026-04-03: Tightened the tracked `MP-377` plan state after re-reviewing the
  new cross-client reducer against the live bridge/runtime handoff. The shared
  `system-picture` / external-review slice now explicitly requires
  repo/worktree/service identity, `CollaborationSession`,
  session-capability / worker-fanout state, delegated-worker receipts /
  topology, and stale-write collision controls so the first PyQt6/mobile/
  remote consumers do not recreate lane ownership locally. The same follow-up
  keeps the operator/runtime truth explicit in plan authority: today’s clean
  tree is still blocked on `reviewer_overdue`, and detached
  publisher/reviewer-supervisor runtime alone is not enough. The missing link
  remains a repo-owned persistent Codex reviewer worker/service path that can
  hold semantic review cadence between Claude passes while 8+8 stays
  conductor-managed scaffolding rather than finished native worker topology.
- 2026-04-03: Promoted the cross-client source-of-truth follow-up into the
  tracked `MP-377` plan chain instead of leaving it as chat guidance. The
  accepted next bounded slice is one generated `system-picture` /
  external-review orientation reducer over typed startup, review, control,
  governance-review, external-findings, and quality-feedback state, emitting
  both a managed repo-owned JSON/Markdown artifact and a compact
  GitHub-visible markdown projection with shared snapshot identity. The
  rollout order is now fixed in plan state too: migrate PyQt6/operator-
  console off `bridge.md`-parsed lane state first, iPhone/mobile off
  compatibility-shaped `mobile-status` payloads second, and Claude remote-
  loop plus external-review surfaces onto typed status plus the generated
  summary third. Those clients remain projections over one backend, not new
  authority owners.
- 2026-04-03: Landed the remote commit pipeline Phase-2 authority cleanup in
  the same `MP-377` owner chain. `ReviewerRuntimeContract` now owns
  `implementer_ack_current`, `implementation_blocked`, and
  `implementation_block_reason`, push/status/startup consumers read those
  typed fields instead of bridge-liveness recomputation, bridge acceptance is
  typed-only instead of prose-regex fallback, and governed push recovery now
  matches the reviewer-owned `approved_target_identity` tree receipt rather
  than raw HEAD equality.
- 2026-04-03: Landed Phase-0 Slice 2 of the remote commit pipeline under the
  same `MP-377` authority loop. Review-channel packet plumbing now accepts a
  dedicated `commit_approval` runtime packet kind with typed
  `pipeline_generation`, `staged_snapshot_hash`, and
  `guard_results_summary` fields, preserves that approval payload through
  `review-channel --action post|ack|apply`, and exposes it through
  reduced packet rows plus typed `ReviewState` parsing without adding a second
  publish-readiness evaluator.
- 2026-04-03: Landed Phase-0 Slice 1 of the remote commit pipeline under the
  active `MP-377` authority loop. `CommitIntentState` and
  `RemoteCommitPipelineContract` now exist as platform/runtime contract rows
  and typed models, flow through `ReviewState`, bridge/event-backed
  review-channel projections, a dedicated `review-channel --action doctor`
  read surface, and the managed `commit_pipeline.json` artifact. The slice
  keeps `recover` as a governed action instead of durable pipeline state,
  promotes `approval_expires_at_utc` and `approved_target_identity` into the
  required contract, and deliberately reuses
  `reviewer_runtime.publish_clear` / `push_decision.review_gate_allows_push`
  for startup push truth instead of adding a second readiness evaluator.
- 2026-04-02: Closed the next self-hosting `MP-377` checks-root extraction
  blocker without inventing a second package-layout regime. The remaining flat
  helpers behind `check_bundle_workflow_parity.py`,
  `check_duplication_audit.py`, `check_naming_consistency.py`, and
  `mutation_ralph_loop_core.py` now live in documented family packages with
  compatibility shims at the root, the `coderabbit_gate_core` package avoids
  root/package duplication by re-exporting through a legacy-module loader, and
  the `naming_consistency` move now proves both package imports and direct
  root-entrypoint script mode. The important product-level closure is that the
  branch-wide `python3 dev/scripts/devctl.py check --profile ci` bundle is
  green again after the package move, so the active extraction lane can move on
  from this crowded-root cluster instead of treating it as permanent
  branch-local debt.
- 2026-04-01: Absorbed the external integration-analysis tranche into the
  canonical `MP-377` owner chain rather than mirroring it as a second roadmap.
  Accepted deltas are now explicit in plan authority: repo-pack-owned
  execution-surface ownership routing, typed onboarding with inference
  provenance and ratification, `DerivedCapabilityContract` plus
  `SessionCapabilityPacket`, and proof-gate language for public readiness
  claims. The same pass kept sequence honest: release-artifact governance and
  supply-chain trust are real scope, but later than the current
  startup-authority / second-repo portability closures.
- 2026-04-01: Landed the first executable organization-role surface under the
  existing `package_layout` seam instead of inventing a second framework.
  `check_package_layout` now loads repo-pack-owned root-role rules, classifies
  files in configured flat roots as compatibility shims, public entrypoints,
  support-module helpers, or uncategorized root implementation, and emits an
  advisory organization section (`organization_review_clean`,
  `organization_role_debt_detected`) beside the existing crowding/baseline
  state. The first self-hosting rule targets `dev/scripts/devctl`, and the
  live report now says the quiet part out loud: no new crowding violation, but
  the root still has too many flat helper files to describe as organized.
- 2026-04-01: Re-audited self-hosting organization against the live tree and
  corrected the next `MP-377` closure accordingly. The current package-layout
  contract is good at freezing drift and tracking compatibility wrappers, but
  it still lets a root stay visually and semantically noisy while the guard is
  green. The immediate plan is now explicit: keep extending the existing
  `package_layout` / shim path rather than inventing a second framework, but
  promote it from crowding-only governance into a repo-pack-owned structure
  policy with package roles plus an AI-readable organization surface.
- 2026-04-01: Landed the next self-hosting package-layout closure in the
  active `MP-377` extraction lane. The crowded `dev/scripts/devctl/commands`
  families now decompose under topical command packages (`check/`,
  `autonomy/`, `docs/`, `process/`, `release/`, `governance/`) while the flat
  root keeps only compatibility shims. The important closure detail is that
  those root files are no longer facade copies: package-layout shim validation
  now accepts thin module-alias wrappers, so legacy import/patch paths still
  resolve to the moved implementation and crowded-root density counts stay
  honest. The remaining follow-up is not to undo the extraction; it is to
  checkpoint the slice and then burn down the inherited code-shape debt on the
  moved implementation modules under their new package paths.
- 2026-04-01: Landed the next `MP-377` runtime-truth closure on top of the
  new `CollaborationSession` contract. Launch/session metadata now derives
  from a typed provider/lane map and persists conductor role truth, packet
  actor/target validation now resolves from typed collaboration/runtime state
  or repo-owned session metadata instead of parser-coded provider ids, and
  the multi-agent sync guard now fails closed when planned `AGENT-*` rows
  leak into runtime truth. This keeps the architecture honest about the
  remaining gap: delegated workers are still receipts, not native runtime
  sessions, and a few recovery/budget surfaces still assume fixed providers.
- 2026-04-01: Landed the next shared runtime contract in the active
  `MP-377` extraction lane. `dev/scripts/devctl/runtime/ReviewState` now
  includes a typed `CollaborationSession` contract, bridge-backed and
  event-backed review-channel emitters both materialize it, and the runtime
  agent registry now projects from that collaboration object instead of
  synthesizing provider rows separately in status and reducer code. The new
  contract is sourced from repo-owned conductor session metadata plus current
  typed review state, which makes the backend honest about the current gap:
  live participants are real, delegated lane receipts are planned-only, and
  the launcher still is not a native worker/session runtime yet. The next
  bounded follow-up remains packet/launch hardcode removal plus the explicit
  planned-topology/runtime-truth guard.
- 2026-03-31: Closed the next startup-repair/runtime parity gap in the active
  `MP-377` self-hosting lane. The refactored review-channel bridge path had
  picked up a required `rollover_dir`, but `startup-context --repair` still
  forwarded only bridge/review/status roots into its bounded repair adapter,
  which made the repo-owned repair path crash on an assertion before it could
  classify or repair `runtime_missing`. Repair runtime resolution now derives
  the governed rollover sibling from the review root and forwards it through
  the same bounded adapter, with regressions proving the repair controller
  stays coherent as review-channel command plumbing keeps moving under the
  broader extraction effort.
- 2026-03-30: Closed one smaller but important self-hosting stale-reader gap
  in the bridge-era review lane without redefining the long-term platform
  boundary. The live compatibility bridge still is not canonical authority,
  but the repo now exposes a typed `implementer_state_hash` alongside
  `current_instruction_revision` on review-channel status/poll surfaces and
  requires that hash on active-dual-agent reviewer checkpoints. This keeps the
  compiler-style contract honest while markdown compatibility remains live:
  stale readers fail closed on Claude-owned state drift instead of silently
  trusting an older poll, and the same pattern stays typed and repo-owned
  rather than turning back into "reread the bridge and hope" chat lore.
- 2026-03-30: Closed the next ownership-boundary gap in that same review lane.
  The problem was not missing information; it was that prompt/bootstrap
  surfaces could still restate policy locally instead of consuming the typed
  owner contract. Reviewer vs implementer startup commands plus explicit
  reviewer takeover now live in runtime-owned `ConductorCapabilityState`,
  review-channel prompt/bridge bootstrap surfaces render from that typed
  contract, and repo policy now teaches `platform_layer_boundaries` to fail
  closed if startup-authority/runtime capability modules import
  `dev.scripts.devctl.review_channel` orchestration directly. That keeps the
  platform thesis honest: if the system already knows a fact in typed state,
  projections consume it instead of re-declaring policy in local strings.
- 2026-03-30: Closed the first bounded startup auto-repair controller slice in
  the same self-hosting lane. `startup-context --repair` now consumes typed startup and
  the same typed `ReviewState` owner that repo-owned `review-channel` status
  refresh produces instead of asking the operator to manually translate those
  surfaces into the next repair command, and it keeps repair ownership honest
  by orchestrating the existing repo-owned `review-channel` repair actions
  directly rather than copying that logic into another runtime package or
  round-tripping through CLI JSON. The repair path is intentionally
  conservative too: one bounded safe fix per invocation, then reread typed
  state. The remaining architecture thesis work is the wider promotion path
  from repeated local repair churn into graph-backed architecture review, not
  more prompt glue.
- 2026-03-29: Closed the bounded startup-thesis checklist item for `MP-377`.
  `dev/config/why_stack.md` now feeds `startup-context` with a concise
  repo/product thesis ahead of SOP/router detail, and the rendered startup
  packet shows those four required commitments (`Mission`,
  `Proof obligation`, `Platform boundaries`, `Current priority`) before the
  task router and guard inventory. The remaining follow-up is deliberately
  smaller than a general startup rewrite: keep the generated bootstrap and
  starter surfaces explicit about the client-vs-core boundary so other repos
  inherit the platform thesis without inheriting VoiceTerm identity.
- 2026-03-28: Landed the first policy-backed publication-cadence contract in
  the tracked `MP-377` runtime owner chain. `repo_governance.push.publication`
  now defines recommendation vs overdue thresholds, `PushEnforcement`
  computes the publication backlog state once from ahead-of-upstream truth,
  and `PushDecisionState` projects shared operator guidance that startup,
  review/status, and startup/context surfaces reuse instead of rebuilding
  stringly push recommendations independently. The slice stays intentionally
  narrow: publication cadence is now typed and shared, while broader
  checkpoint/review/bridge recovery composition remains deferred to the later
  continuation-decision layer.
- 2026-03-28: Captured the release-maintenance escape as a first-class
  architecture miss-closure example instead of treating it as one lucky debug
  run. The same slice exposed three concrete system misses: 1) a moved guard
  still had dead flag semantics and heuristic composition proof, 2) shim
  metadata had become executable authority without repo-root/file-exists
  validation, and 3) the public root-entrypoint / CLI-import path for moved
  commands was not covered strongly enough to fail before the release router.
  Locked the correction into platform architecture rather than chat memory:
  `DEVCTL_ARCHITECTURE.md` now defines the explicit
  `Escape -> classify -> prevention surface -> regression proof -> record
  closure` loop, root entrypoints now count as architecture-owned execution
  contracts instead of "just shims", and the fix path for this tranche is to
  land deterministic prevention surfaces in the same slice
  (architecture-surface import closure, shim-target validation, DRY-guard
  contract tightening, and root-entrypoint smoke coverage) so the class moves
  from remediation toward governed class elimination.
- 2026-03-27: Closed the second feature-branch release-preflight mismatch in
  the same governed lane. `bundle.release` now uses
  `devctl hygiene --strict-release-warnings` so the configured release branch
  stays fully strict while feature branches keep release-maintenance warning
  families visible but non-blocking, and
  `check_publication_sync.py --release-branch-aware` keeps stale publication
  drift visible everywhere but only hard-blocks freshness debt when `HEAD`
  resolves to the configured release branch. The same slice also followed the
  package-layout/self-hosting contract through the implementation: touched
  crowded-root commands/checks/tests moved into topical packages with thin
  compatibility shims so the branch-aware release logic lands without
  widening the self-hosting debt it is trying to govern.
- 2026-03-27: Promoted the compiler-style governance explanation out of local
  scratch notes and into canonical dev/agent surfaces. `AGENTS.md` now tells
  sessions to reason about the system as repo-owned deterministic passes plus
  typed control objects instead of a checklist plus chat memory,
  `dev/guides/AI_GOVERNANCE_PLATFORM.md` now carries the durable
  source-program / control-surface / pass mapping, and the governed
  `claude_instructions.template.md` now echoes that same model at startup.
  `dev/read.md` can therefore retire without losing the architecture framing
  needed by fresh AI/dev sessions.
- 2026-03-27: Accepted the portable baseline-repo contract more explicitly in
  the tracked owner chain. `backlog.md` should stay a shared intake surface,
  not a catch-all architecture ledger, and it can remain empty when there is
  no real queued work. The cross-repo organization answer is one
  repo-pack-owned repo-shape/convention policy layered under the existing
  process doc + execution tracker + shared backlog baseline; larger
  per-slice plan docs remain the escalation path when execution complexity
  actually requires them. Ownership stays split on purpose: `MP-376` for the
  reusable shape/enforcement/discovery contract, `MP-377` for the startup/
  work-intake surface that teaches and routes that contract.
- 2026-03-27: Added the first repo-pack-configured shared backlog contract to
  the live `MP-377` owner chain instead of leaving backlog tracking as either
  hidden local notes or plan-authority leakage. Repo policy now advertises
  `backlog.md`, governance/doc-authority classifies it as `shared_backlog`,
  startup/work-intake can surface it in warm refs plus writeback sinks, and
  the contract stays explicit that backlog is shared intake only until
  promoted into `dev/active/MASTER_PLAN.md` plus the owning active plan.
- 2026-03-27: Captured the missing architecture-intake scope in the tracked
  `MP-377` owner chain instead of leaving it as
  fragile chat context. Locked four same-lane directions into plan state:
  `DecisionTrace` plus typed `current_session` is the explanation chain,
  `bridge.md`/latest/chat/status remain projections, deterministic
  validation/test failures are one governed evidence family rather than the
  whole trust story, and a future `PlanExpectationPacket` should compile
  selected plan truth into machine-usable expectations before reconciliation
  against observed runtime/test evidence.
- 2026-03-27: Added the missing foundation checklist behind that same
  explanation/validation vision. The tracked plan now explicitly carries the
  supporting work for `REPO_ROOT` injection, git/filesystem adapters,
  governance-ledger typing, `GovernanceFinding` aggregate ownership, live
  `validation_plan` execution, failure adapters, strict contract/guard
  markers, boundary-validation models, and the first contract-test suite
  order so implementation does not skip straight to the visible `DecisionTrace`
  layer.
- 2026-03-27: Landed the bounded explainability tranche on existing typed
  surfaces instead of creating a parallel trace roadmap. `DecisionPacket`
  family consumers plus routed startup/task-router/workflow-profile receipts
  now expose `rule_summary`, `match_evidence`, and rejected-rule traces;
  startup markdown/probe renders project that data into compact plain-language
  explanations; canonical probe packets now reuse `practices.py` /
  `SIGNAL_TO_PRACTICE` and add metric explanations for `fan_in`, `fan_out`,
  `bridge_score`, and hotspot rank; and context-graph query/bootstrap outputs
  now explain why nodes matched and ranked. Added the durable companion guide
  `dev/guides/PYTHON_ARCHITECTURE.md` so the platform has one repo-owned
  decision tree for `dict` vs `TypedDict` vs `dataclass` vs boundary models,
  `Protocol`, and repository/service/unit-of-work/dependency-injection
  choices. Kept the provenance-grade `DecisionTrace` family deferred to the
  existing Phase-5b lane.
- 2026-03-27: Closed the first same-lane typed-seam and authority-source
  integrity misses exposed by that rollout. Startup decision helpers now read
  typed `PushEnforcement` directly instead of taking `object` and using
  `getattr`, `probe_design_smells` now catches first-parameter and multiline
  `: object` signatures, and review-channel attention now promotes live
  dual-agent conductor absence to `bridge_contract_error` before checkpoint
  advice can mask the invalid authority state. The same bounded closure now
  also reuses the existing hard-guard lane instead of inventing another
  checker island: `check_python_typed_seams.py` now owns the blocking typed-
  seam lane, and `probe_design_smells` shares that scanner so advisory and
  deterministic enforcement stay on one repo-owned contract. This stays in
  the existing self-hosting blind-spot tranche, not as a new roadmap.
- 2026-03-27: Accepted the "TDD as trust token" follow-up, but narrowed it to
  the platform contract we actually need. The right abstraction is not
  "pytest as a magic green light" or repo-wide coverage thresholds; it is a
  portable deterministic validation-contract family with runner adapters,
  canonical failure-to-`Finding` normalization, executable
  `validation_plan` selectors, and scoped `decision_mode` upgrades only when
  the exact validation contract for one finding passes. This stays in the
  `MP-377` runtime/evidence owner chain, not in probe-only ownership.
- 2026-03-27: Tightened the new explainability/learning-path direction so it
  does not create a second disconnected roadmap or wait on the wrong phase.
  The immediate output-layer work should reuse what already exists:
  `DecisionPacketRecord` as the starting decision shape, routed startup/task-
  router/workflow-profile receipts for `match_evidence` and rejected-rule
  traces, and `dev/scripts/checks/probe_report/practices.py` /
  `SIGNAL_TO_PRACTICE` for the first why/fix teaching content. The full typed
  `DecisionTrace` family remains in the `platform_authority_loop` evidence/
  provenance closure lane; the new instruction is to land the low-effort
  explanation projections first instead of waiting for that deeper phase to
  finish. One additional same-lane omission is now explicit too:
  context-graph/query surfaces need short "why this matched/ranked" summaries
  instead of only node lists, temperatures, and edge counts.
- 2026-03-27: Accepted the user's push to treat Python architecture learning
  and AI decision explainability as one `MP-377` concern instead of two loose
  follow-ups. The resulting plan correction is explicit: authoritative
  runtime explanations should come from a small schema-validated decision-
  record vocabulary rendered from typed decision state, not from open-ended
  prose reasoning; the matching human-learning surface should be one
  platform-owned guide/decision tree for `dict` vs `TypedDict` vs
  `dataclass` vs boundary-validation models, `Protocol`, composition,
  repository/service/unit-of-work, and dependency injection. Locked the
  recommended source spine in plan state too: Cosmic Python (Ch. 1-6, 8,
  13), the official typing docs, Pydantic strict-mode/JSON Schema, and
  FastAPI boundary-model docs, with Pydantic kept at untrusted/serialized
  boundaries rather than promoted to every internal runtime contract.
- 2026-03-27: Re-audited the full owner chain after the latest docs-boundary
  miss instead of assuming the problem was lack of planning. The plan
  direction was already correct; the real gap was restartability and owner
  compression. Locked the next `MP-377` work to one bounded separation
  tranche with repo-visible exit criteria: docs/product boundary,
  fail-closed portable authority, governed-push publish truth, and adopter
  proof. Also recorded the explicit pushback on repo shape in plan state:
  the target is layered separation, not one new catch-all directory.
- 2026-03-27: Followed the authority-closure patch through the remaining
  startup/tandem/push consumers instead of leaving it at docs plus one gate.
  The shared review-state locator can now refresh the bridge-backed typed
  projection before live consumers read it, `startup-context` plus the
  governed push gate inherit that fresher current-session truth, and
  `check_tandem_consistency` now reads the refreshed typed projection instead
  of trusting a stale on-disk snapshot. Added focused regressions for the
  locator, startup gate, and tandem guard, plus reran the startup/tandem/push
  pytest suites.
- 2026-03-27: Landed the first bounded authority-closure patch instead of
  leaving the external-review translation as owner-doc intent only.
  `ProjectGovernance` runtime entries now carry typed artifact/scope
  classification, `startup-context` only trusts typed `review_state.json` for
  reviewer-gate authority and blocks active bridge sessions when that typed
  state is missing, and `work_intake` default warm refs now suppress
  compatibility projections plus lane-specific docs. Added regression proof
  for custom-layout and no-bridge repos and reran focused runtime/governance
  pytest plus `python3 dev/scripts/devctl.py check --profile ci`.
- 2026-03-27: Re-ran the self-hosting docs/organization surfaces before
  reprioritizing the architecture work. The universal-system model is already
  the active `MP-377` / `MP-376` owner chain, but the repo still makes that
  model hard to ingest because the live authority surface is too large and too
  mixed. `doc-authority` now provides the measured baseline (`50` governed
  docs / `45,107` lines, `19` budget violations, `4` authority overlaps,
  `8` consolidation candidates), while `check_package_layout` confirms the
  same self-hosting problem in code structure (four crowded roots and seven
  crowded namespace families). The same owner lane now ratchets those known
  `devctl` hotspots from `freeze` to `strict` on touched edits so the
  existing `package_layout` engine blocks continued flat-root churn instead of
  merely describing it. Promoted the conclusion as owner priority, not a new
  parallel roadmap: the next platform tranche is
  executable doc/organization compression plus development-vs-adopter
  boundary cleanup.
- 2026-03-28: Modularized 7 MP-377 self-hosting modules that exceeded the
  Python 350-line code-shape soft limit. Each was split into a main module
  (public API, constants) plus a sibling helper module (coercion, rendering, or
  session-detection logic). All splits re-export public symbols for backward
  compatibility. Affected modules: `bridge_projection`, `policy_runtime`,
  `startup_context`, `check_router_constants`, `review_channel_bridge_render`,
  `core`, `push_policy`. `check_code_shape` working-tree passes with 0
  violations.
- 2026-03-27: Landed the governed-push architecture closure for this tranche.
  `devctl push` now treats publish truth as staged contract state instead of a
  single binary success, repo policy explicitly gates skip-flag bypasses, and
  the same semantics propagate through the shared push-policy/governance
  surfaces used by `sync` and startup-facing command routing defaults.
- 2026-03-26: Tightened the architecture direction around documentation
  sprawl instead of treating it as cleanup trivia. The repo already has the
  universal markdown/governance plan in the tracked `MP-377` / `MP-376`
  chain; the failure is self-hosting clarity and bounded startup, not missing
  concepts. Current verified self-hosting pressure is concrete: 27
  `dev/active/*.md` docs and 10 root-level markdown entrypoints. Accepted
  next work is therefore absorption-first and budgeted: root/reference docs
  must be audited before archival, `doc-authority` becomes the canonical
  consolidation surface, and portability proof must include custom
  docs-authority/tracker/index/report names instead of assuming VoiceTerm
  filenames.
- 2026-03-26: Re-ran the portability audit specifically against the user's
  "what if another repo has different names/layouts?" bar. The answer is
  partial, not closed: policy-owned discovery and typed registries can carry
  alternate roots once configured, but the core typed contract still seeds
  `AGENTS.md`, `dev/active/INDEX.md`, `dev/active/MASTER_PLAN.md`, and
  `dev/reports/*` on partial payloads, while review-channel/startup/control-
  plane consumers still hardcode `bridge.md` plus `dev/active/*` in several
  places. That gap is now treated as first-class `MP-377` architecture work,
  with `MP-376` owning the custom-layout fixture proof and portability-drift
  detection.
- 2026-03-26: Promoted the next governed-push contract correction from local
  confusion into tracked `MP-377` state. The runtime now distinguishes raw
  git cleanliness (`worktree_clean`) from review-gate allowance
  (`review_gate_allows_push`) and can emit an explicit `await_review`
  startup action for clean-but-unaccepted slices. The same startup/receipt
  path now carries a typed AI-facing `push_decision` answer
  (`await_checkpoint`, `await_review`, `run_devctl_push`, `no_push_needed`)
  so models stop inferring remote actions from mixed booleans. The remaining
  umbrella follow-up is the deeper contract split between continuation-budget
  / edit-safety state and branch-push mechanics so future
  `PushPreflightPacket` / `ActionResult` surfaces do not keep overloading one
  field family with two different jobs. The same lane also needs one
  repo-policy seam for advisory scratch context (`convo.md` in VoiceTerm
  today) so reviewed commits can reach `run_devctl_push` without local
  reference files being misclassified as authored worktree drift.
- 2026-03-28: Closed the next recovery blind spot in that same governed-push
  lane. Typed push stages no longer disappear with terminal output:
  `devctl push` now persists the latest typed push result at
  `dev/reports/push/latest.json`, `PushEnforcement` carries that managed
  artifact into startup authority, and `startup-context` now treats
  `published_remote=true` plus `post_push_green=false` as "publication is
  settled; repair the post-push follow-up" instead of "push unresolved".
  The remaining umbrella closure is still the fuller branch/tree-hash
  `PushPreflightPacket`, not another repo-local push-status heuristic.
- 2026-04-09: Closed the next post-push scoping defect in that same lane.
  Governed push now carries the preflight-resolved `since_ref` into
  diff-sensitive post-push commands instead of resetting follow-up checks to
  `origin/develop` after publication. That keeps publication follow-up bound
  to the same typed branch/upstream truth that preflight, startup, and
  launcher surfaces should already consume; static bundle/docs examples may
  still show the template base, but repo-owned runtime/hook paths must reuse
  the resolved value rather than recomputing branch literals.
- 2026-03-26: Ran a broader portability/architecture audit after the live
  review-channel cutover exposed another "works in VoiceTerm, leaks in
  portable mode" seam. The result is larger than the immediate bug: docs
  already say VoiceTerm should be a client over a portable governance stack,
  but the implementation still allows portable layers to fall back to
  VoiceTerm defaults when repo-pack/governance data is missing. Confirmed
  examples include typed governance defaults for `dev/active/*`,
  `dev/reports/*`, and `bridge.md`, `active_path_config()` falling back to
  `VOICETERM_PATH_CONFIG`, import-time frozen path-config capture in
  review-channel modules, and AI/bootstrap/review prompt text that still
  emits VoiceTerm/tandem assumptions as universal instructions. Accepted
  response: treat this as a first-class `MP-377` portability-governance
  slice, not as incidental cleanup; encode product-thesis/bootstrap intent in
  generated surfaces, add a portability-drift prevention stack, and require
  cross-repo fixture proof instead of relying on future agent memory.
- 2026-03-25: Closed the immediate fail-closed reviewer-loop gap that the
  stalled Codex/Claude bridge exposed. `heartbeat.py` no longer swallows the
  blank padding after `## Poll Status`, bridge validation/state projection now
  surface stale Claude ACK plus empty reviewer status as a typed hard
  contract error instead of warning-only `waiting_on_peer`, and the startup
  family plus `mutation-loop` now honor reviewer-side implementation blocking
  so active-dual-agent review does not silently drift back into reviewer
  coding. This is intentionally not counted as the full bridge migration:
  the next `MP-377` work remains the broader typed `current_session` /
  `ReviewState` consumer cutover and durable repo-owned reviewer-runtime
  liveness.
- 2026-03-25: Re-checked the tree after the probe-loader fix landed. The
  earlier `startup_signals.py` path bug is now closed, so the remaining
  `MP-377` startup gap is the still-unconsumed
  `governance-quality-feedback` signal plus a routing-coherence miss:
  `startup-context` can select `bundle.tooling` while its emitted
  `check-router --since-ref ...` preflight returns `bundle.docs` on the same
  dirty tree. The same rerun also narrowed the graph intake work: `routes_to`
  edges and diff-edge visibility already exist, but guard-edge neighbor noise
  still needs downranking and `scoped_by` coverage still leans on
  docs-policy tooling prefixes instead of active-plan ownership.
- 2026-03-25: Re-verified the latest deep-sweep claims against the live
  command paths before widening `MP-377`. The concrete startup bug is real:
  `startup_signals.py` currently reads a stale probe-summary path while the
  emitted probe artifacts live under the governed `probe_report_root`, so
  `startup-context` and bootstrap `context-graph` silently omit probe data.
  The clean-tree `probe-report` zero-scan result is also real, but it matches
  the current `working-tree` contract; the tracked follow-up is therefore
  repo-pack-aware startup loading, honest startup freshness semantics, and one
  producer-to-consumer smoke suite over the governed startup surfaces, not a
  blanket "run every governance command in CI" mandate.
- 2026-03-24: Accepted the remaining aligned external-review follow-ons into
  the platform architecture without widening the contract surface.
  "Determinism decides if, AI decides how" is now the sequencing rule for the
  next closures: transformation-proof joins belong in `DecisionTrace` /
  `RunRecord`, change-pressure gating stays policy-backed, and any AI
  decision-auditor remains an advisory reviewer rather than a replacement for
  `approval_required` human/operator approval. A deeper same-day pass also
  keeps the intake's strongest self-governance claims but narrows them to the
  architecture the repo actually wants: raw zero-consumer counts stay audit
  evidence, while tracked work becomes explicit follow-up linkage for
  `missing_guard` / `missing_probe`, stable `finding_id`, live-vs-scaffold
  contract status, and meta-guards over authoritative/runtime-complete
  surfaces only.
- 2026-03-23: Closed the next startup-authority bypass in the `MP-377`
  product lane instead of treating the new guard as operator lore. The
  startup family now owns a portable managed `StartupReceipt` rooted in live
  governance/path-root authority rather than a hardcoded VoiceTerm report
  path, `startup-context` is the documented Step 0 gate across the repo's
  bootstrap surfaces, and scoped repo-owned launcher/mutation `devctl`
  commands now fail closed when that receipt is missing/stale or when live
  startup-authority truth is already red. This narrows the remaining closure
  to raw git/pre-commit bypass and broader repo-pack activation work instead
  of the older "the packet exists but nothing requires it" gap.
- 2026-03-22: Landed the first enforcement slice for the new
  architectural-absorption rule without creating another shadow audit surface.
  `governance-review --record` now requires typed finding disposition fields,
  emits `FindingReview` schema v2 rows, and renders the disposition back into
  recent findings. `check_governance_closure` now checks the latest v2 review
  rows for that contract while leaving legacy JSONL rows readable. Focused
  tests passed for `governance-review`, `governance-import-findings`,
  governance CLI dispatch, and `check_governance_closure`. The live
  `check_governance_closure` guard is still red, but only for pre-existing
  repo-wide guard/probe test-coverage and CI-coverage backlog unrelated to
  the new review-disposition check.
- 2026-03-22: Closed the two remaining tranche-1 polish gaps immediately after
  review. The portable finding-review JSON schema template now matches the
  live `FindingReview` v2 contract (schema version, contract id, signal/scan
  enums, disposition fields, and waiver conditional), a deterministic test now
  guards that template against future drift, and one explicit temp-ledger CLI
  proof confirmed the end-to-end path (`governance-review --record` -> JSONL
  v2 row -> summary artifact -> disposition validator returns no errors)
  outside the unit-test helper path.
- 2026-03-22: Tightened the recurring-defect rule into an explicit platform
  completion contract. The plan no longer says only "prefer a reusable
  guard/probe path"; it now requires important findings to be evaluated for
  architectural absorption through approved prevention surfaces or an explicit
  waiver before closure.
- 2026-03-22: Landed the first live `ai_instruction` routing proof in the
  runtime instead of only in audit/plan prose. Ralph now reads canonical probe
  findings from `review_targets.json`, matches them deterministically to
  CodeRabbit backlog file slices, and renders the matched guidance into the
  live remediation prompt. Focused tests cover prompt rendering, exact-path
  matching, dedupe behavior, and the `main()` path that passes the guidance
  through to `invoke_claude()`.
- 2026-03-22: Tightened the tranche-2 route after an architectural smell
  review. Ralph no longer negotiates between `review_targets.json` and
  `review_packet.json`; `review_targets.json` is its only guidance authority.
  The separate `review_packet.json` artifact remains live elsewhere in the repo
  for non-Ralph consumers such as context-graph severity inputs, and the
  CodeRabbit backlog path now carries structured `path` / `line` fields so the
  Ralph matcher only falls back to summary-string parsing for older backlog
  payloads.
- 2026-03-22: Landed the first deterministic produced-but-never-consumed
  meta-guard instead of stopping at the Ralph proof test. The
  `platform_contract_closure` guard now executes a synthetic
  `Finding.ai_instruction` route through the real Ralph consumer path and
  fails if probe artifacts still emit the field but the prompt stops
  carrying it.
- 2026-03-22: Extended that same route proof to the autonomy controller lane
  instead of letting the second consumer depend on unit tests alone.
  `triage-loop` now carries a bounded structured backlog slice, `loop-packet`
  matches it against canonical probe guidance, and
  `platform_contract_closure` now fails if the autonomy terminal draft stops
  carrying matched `ai_instruction` text even though the artifact still
  produces it.
- 2026-03-22: Verified the first external-review follow-up against the live
  branch instead of assuming every smell claim stayed true after cleanup. The
  checker stack still misses two real cases in this lane: there is no
  deterministic rule for dual-authority artifact consumers yet, and
  `probe_stringly_typed` does not currently flag prose-parsed structured
  matching seams. The stronger "junk-drawer module" complaint was stale
  against the cleaned Ralph path by the time this verification ran, so the
  remaining follow-up is guard/probe calibration, not another module split.
- 2026-03-22: Closed the next adoption/coverage follow-up instead of leaving
  Parts 52-54 as new audit prose. Ralph now states the probe-guidance policy
  before the findings list, autonomy prompt generation does the same,
  escalation packets render matched `## Probe Guidance` entries plus stable
  `guidance_refs`, review-channel instruction-source projections preserve
  those refs, and `governance-review --record` now accepts `guidance_id` /
  `guidance_followed` so adoption can be measured in the same ledger as fix
  outcomes. The remaining gap in this tranche is the last `guard-run`
  consumer path plus impact measurement over the still-zero-consumer
  operational artifacts.
- 2026-03-22: Closed that last current `guard-run` closure gap in the same
  lane instead of opening a new guard family. `platform_contract_closure`
  now counts three live `field_route` proofs plus one
  `field_route_family` coverage row, and it fails with
  `field-route-family-incomplete` if the declared Ralph / autonomy /
  `guard-run` consumer set for `Finding.ai_instruction` is missing or
  failing. The next closure work is no longer "wire guard-run"; it is
  widening the same meta-guard pattern to the remaining carried decision
  fields and zero-consumer operational artifacts.
- 2026-03-22: Closed the next quick operational-evidence intake without
  inventing a new packet family. Shared context-escalation packets now load
  bounded recent `finding_reviews` history and latest quality-feedback
  recommendations from the existing governance artifacts, so Ralph/autonomy /
  review-channel / conductor / swarm inherit those two data families through
  the same packet path instead of leaving them display-only. The generated
  bootstrap surfaces and review-channel bootstrap text now also tell agents
  when to escalate from the slim `context-graph --mode bootstrap` helper to
  typed `startup-context` for reviewer/checkpoint truth or richer
  continuity. Remaining write-only backlog here is still watchdog episodes,
  broader decision/adoption metadata, and impact measurement.
- 2026-03-22: Closed the next runtime-consumption seam in the same lane
  instead of leaving the remaining metadata as abstract backlog. Shared
  escalation/context packets now inject bounded watchdog episode digests and
  command-reliability lines from the existing data-science summary artifact,
  matched probe guidance now merges the first live `DecisionPacket`
  behavior gate (`decision_mode`) from the existing probe-summary artifact,
  Ralph/autonomy/`guard-run` consume that gate as approval/auto-apply policy
  instead of report-only text, and `platform_contract_closure` now proves the
  first `DecisionPacket.decision_mode` route family alongside the earlier
  `Finding.ai_instruction` family. The remaining carried-decision backlog is
  now the rest of the typed semantics (`invariants`, `validation_plan`,
  `precedent`, `research_instruction`, `signals`) plus impact measurement
  over the already-routed operational evidence.
- 2026-03-22: Tightened the `MP-377` platform checklist with the next evidence
  intake instead of creating parallel backlog. Part 45 widened the existing
  operational-artifact routing item from prompt-builder-only to broader
  decision-surface consumption, and Part 47 widened the existing graph-routing
  item from dead-edge closure alone to the first quick-win `EDGE_KIND_GUARDS`
  seam plus the missing node-family rollout.
- 2026-03-22: Integrated `UNIVERSAL_SYSTEM_EVIDENCE.md` Parts 42-43 into the
  canonical `MP-377` plan chain. The feedback-loop tranche now explicitly owns
  routing fresh `dev/reports/**` operational artifacts into live prompt
  builders, and the graph lane now explicitly owns landing real
  `EDGE_KIND_GUARDS` / `EDGE_KIND_SCOPED_BY` edges plus widening graph
  consumers beyond escalation-only packets.
- 2026-03-22: Closed the first graph-edge tranche under that same lane without
  inventing a second routing scheme. The live builder now derives `guards`
  coverage from the active quality policy and its scoped roots, while
  `scoped_by` derives only from docs-policy tooling prefixes already used
  elsewhere in governance. The graph
  still needs the missing node families and broader consumers, but the dead
  edge constants are no longer dead code.
- 2026-03-22: Started Part 53 on the same graph lane instead of creating a
  parallel snapshot system. `context-graph` now has a typed
  `ContextGraphSnapshot` writer plus `--save-snapshot`, bootstrap mode
  automatically persists a versioned snapshot under
  `dev/reports/graph_snapshots/`, and focused tests prove both the artifact
  payload and the bootstrap auto-save path. Remaining Part-53 work is snapshot
  diff + trend/drift analysis, not basic artifact capture.
- 2026-03-23: Closed the next Part-53 slice on that same graph lane.
  `context-graph --mode diff --from ... --to ...` now reloads saved
  `ContextGraphSnapshot` artifacts, emits a typed `ContextGraphDelta` with
  added/removed/changed node/edge samples plus temperature/edge-kind deltas,
  and reports a rolling trend summary over recent snapshots. That turns the
  saved graph baselines into live drift answers without creating a parallel
  temporal-analysis tool.
- 2026-03-23: Hardened that same Part-53 diff/trend slice after live review
  found two correctness gaps and one portability gap. Snapshot resolution now
  orders artifacts by capture-time metadata rather than filesystem `mtime`,
  direct-path trend scans skip sibling JSON files that are not real
  `ContextGraphSnapshot` artifacts, and `ContextGraphDelta` anchor/trend paths
  now normalize to portable snapshot-store-relative refs instead of leaking
  machine-local absolute paths. Focused regression coverage now proves the
  mtime-skew case, mixed-directory direct-path case, and normalized path
  output.
- 2026-03-23: Closed the next `MP-377` startup-surface intake gap after a
  focused review found that the platform was generating governance data
  faster than session-start surfaces could consume it. Repo-pack surface
  generation now derives the AI bootstrap steps, key command block, and
  blocking post-edit checklist from typed router/guard authority instead of
  stale policy strings, the generated `CLAUDE.md` surface now names concrete
  `probe-report`, `governance-review --record`, `context-graph --mode diff`,
  and `review-channel` wait/checkpoint/ensure syntax, and the slim
  `context-graph --mode bootstrap` packet now folds bounded probe summary,
  governance-review stats, hotspot guidance, watchdog metrics, and command
  reliability into one startup read. Remaining closure is still to promote
  the same richer evidence family into canonical `startup-context` /
  `WorkIntakePacket` authority so bootstrap helper surfaces stop carrying
  information that the intake packet does not.
- 2026-03-22: Completed the remaining whole-audit mapping into the canonical
  platform chain instead of leaving `A1-A12`, `A22-A30`, and `D/S/E/G`
  partially implied. `platform_authority_loop.md` now carries the blocker +
  startup/memory/path-portability tiers explicitly, while this plan now owns
  the feedback-loop closure (`A1-A4`), the next deterministic hard-guard
  tranche (`A27`), and governance-closeout/self-governance enforcement
  (`A29`, `G1`) in checklist form.
- 2026-03-22: Finished the remaining `SYSTEM_AUDIT.md` mapping into the main
  platform plan instead of leaving `A13-A21` / `T1-T5` partly stranded in
  reference prose. The current canonical split is now explicit: `A13`/`A16`/
  `A17` as `MP-377` `P0` typed-runtime cleanup, `A18`/`A19` as command/output
  contract convergence, and `T3`/`T4`/`T5` as the first platform
  test-hardening matrix. `dev/guides/SYSTEM_AUDIT.md` is now integration-
  complete reference evidence pending retirement after the current Phase 7
  proof/cleanup gate, not a shadow roadmap.
- 2026-03-22: Integrated the root evidence intake into the main `MP-377`
  product plan and corrected the stale subclaims before mirroring them into
  tracker state. The live problem is routing, not missing architecture:
  probe/decision guidance fields still do not reach the AI fix loops,
  `governance-review` is still effectively manual closeout, and
  `ProjectGovernance` routing fields remain mostly report-only. Corrected
  while recording this slice: `decision_packet_from_finding()` already has
  live callers in `dev/scripts/checks/probe_report/decision_packets.py`, and
  some doc-authority metadata is already consumed by `doc_authority.py`; the
  unresolved gap is runtime/control-path consumption.
- 2026-03-21: Captured the supporting guard-audit conclusions into the live
  `MP-377` plan chain instead of leaving them as off-plan analysis. Execution
  state stays here and in `MASTER_PLAN`. Verified against code that the branch
  still leaks VoiceTerm-default repo-pack
  authority, bridge/projection fallback, provider-shaped review-state
  compatibility fields, and typed boundary drift (`ActionResult.status` in
  `vcs.push`, `context-graph` confidence typing) into runtime behavior.
  Accepted sequencing stays deterministic and bounded: cheap typed-boundary
  truth fixes first, startup/path/review authority closure second, executable
  plan-mutation plus first intake/session authority slice third, narrow
  self-governance guards for contract-value domains / plan-runtime parity /
  authority-source integrity / dead authority seams fourth, and only then the
  later `system-picture` / coherence / graph-widening follow-ons.
- 2026-03-21: Added the missing transformation-rule backlog item to the graph
  lane. The current plans already owned bounded blast-radius, architecture
  queries, and fail-closed graph honesty, but they did not yet record the next
  generated-only step: advisory fix-effect / companion-edit prediction on top
  of the same typed graph so context packets can forecast likely fallout
  without turning graph output into authority.
- 2026-03-21: Added the missing system-wide read surface to the platform plan.
  The accepted direction is now explicit: a generated `devctl system-picture`
  composes startup state, plan status, contract chain, guard/doc health,
  topology coverage, mutation-op coverage, and agent-readiness drift into one
  bounded warm-start artifact, with tree-hash / section-hash invalidation so
  later sessions and many-agent runs can reuse the picture without promoting it
  into authority.
- 2026-03-21: Corrected the active-plan self-hosting audit against the repo's
  actual code surface. The governance/runtime architecture is already more
  mature than the earlier markdown-only read suggested: typed contracts such
  as `ProjectGovernance`, `TypedAction`, `ActionResult`, `Finding`,
  `DecisionPacket`, and `ReviewState` already exist in code with tests, while
  later authority-loop nodes such as `WorkIntakePacket`,
  `CollaborationSession`, and the true `PlanRegistry` / `PlanTargetRef`
  loader remain planned `P0`/`P1` work. The real self-hosting gap is now
  tracked explicitly as markdown-contract drift: most execution-plan docs
  already carry the core guarded sections, but plan formatting is still less
  uniform than the code contract layer and `Session Resume` remains sparse.
- 2026-03-21: Landed the first repo-pack-owned VCS command-routing slice as a
  concrete `MP-377` proof point. `repo_governance.push` now carries the
  default remote, development/release branch names, protected-branch rules,
  preflight command, and post-push bundle; `devctl push` consumes the same
  contract as the canonical short-lived branch push path with
  `TypedAction(action_id="vcs.push")` plus `ActionResult`; generated starter
  surfaces now include a policy-backed pre-push hook stub; and legacy
  `sync` / `ship` helpers now read the same repo-pack policy instead of
  embedding branch/remote defaults in Python.
- 2026-03-21: Captured the next graph-hygiene quick wins surfaced by the
  latest code audit. The new tracked gaps are: duplicated `INDEX.md` parsers,
  missing handler/list parity enforcement for the public command surface,
  context-graph temperature drift away from the shared hotspot scorer, the
  need for a real file-pattern trigger table for context routing, and an
  explicit slim-bootstrap budget so the graph layer stays a reducer rather
  than growing back into a preload blob.
- 2026-03-21: Captured the deeper context-graph audit as tracked platform
  scope instead of leaving it as chat-only analysis. The accepted read is that
  the current `context-graph` slice is a good bounded bootstrap/query helper
  but not yet the deterministic effort scheduler: command graph closure is
  still thin, graph honesty needs machine-readable confidence/no-edge states,
  live routing inputs are not yet flowing into the build path, and the graph
  is still file-oriented instead of symbol/test/finding-oriented. The next
  ladder is now explicit here: honesty + command edges first, then typed
  `startup-context` / `WorkIntakePacket`, then live routing inputs, then the
  broader work graph.
- 2026-03-21: Reconciled the larger cross-agent ZGraph/runtime audit with the
  live platform plan. Confirmed the immediate misses are wiring, not
  architecture: the shared topology scan still pulls calibration/transient
  roots (`dev/repo_example_temp/**`, `.claude/worktrees/**`), the current
  build path ignores fresh `file_topology.json` / `review_packet.json` inputs
  so changed/hint/severity channels sit idle, and query confidence still
  over-credits substring/import adjacency. Folded that into the existing
  ladder: scan hygiene plus artifact-backed routing/scoring next, then the
  typed startup/work-intake reducer, then the already-planned work-graph
  expansion. The broader unused data families from that audit (review state,
  governance verdicts, autonomy telemetry, workflow/config/test/platform
  coverage) map to that existing work-graph step rather than to a second plan
  family.
- 2026-03-21: Tightened the accepted interpretation of the broader multi-agent
  audit instead of letting the extra detail drift into an unbounded second
  roadmap. Most of the deeper data richness already belongs to the existing
  work-graph widening step; the newly explicit near-term commitments are
  narrower: the first `WorkIntakePacket` proof must act as a deterministic
  context router rather than another passive packet, the first richer typed
  relation families must include canonical `guards` / `scoped_by` plus one
  operation-semantic producer/consumer path, the first routing proof now also
  explicitly includes staged filtering, bounded multi-hop inference, and a
  small hot-query cache, and parallel readers should collapse onto shared
  typed projections where those projections already exist. Example-repo
  prediction/ROI patterns remain calibration inputs until that simpler proof
  is live.
- 2026-03-21: Captured the missing cross-session warm-start rule explicitly.
  The plans already had startup-context, hot/warm/cold retrieval, adoption
  scans, and SQLite activation, but the end-to-end session flow is now named
  too: first run seeds canonical artifacts, later runs refresh only the
  content-hash/git-diff-invalidated slices, and JSON snapshots remain the
  portable fallback until the SQLite runtime cache is active.
- 2026-03-21: Captured the accepted four-layer execution model for the
  platform plans so context work stops drifting into "load everything and hope
  the model ignores it." The stack is now explicit: hard guards/probes first
  as cheap deterministic classifiers, `ConceptIndex` / ZGraph second as the
  reversible search-space reducer over canonical refs, `HotIndex` /
  `startup-context` / `ContextPack` third as the bounded reconstructed working
  slice, and the reviewer/autonomy/Ralph loops last as the expensive
  fallback/controller layer for unresolved work. That framing now governs
  context-escalation policy, graph honesty, and future controller design.
- 2026-03-21: Accepted the next context-graph rollout order after landing the
  first bounded context-escalation slice. The current green CI/docs state
  should be checkpointed as the first stable Phase-6 context-recovery proof
  before widening graph work again. The next graph ladder is now explicit
  here: fix honest typed plan/doc/command connectivity first, then inject the
  same bounded packet into the remaining backend instruction emitters
  (`review-channel` promotion/event projections and fresh `swarm_run`
  prompts), then run a cross-surface validation matrix for review-channel /
  autonomy / Ralph, and only after that widen into richer graph capabilities
  such as transitive blast radius, test-to-code edges, agent-authored graph
  queries, and generated concept-view flowcharts.
- 2026-03-20: Accepted the native repo-owned context-graph path for the
  hot/warm/cold startup/session-context work. The combined design is now
  explicit: canonical pointer refs from plans/docs/repo-map/evidence artifacts
  remain authority, while `ConceptIndex` and any ZGraph-compatible encoding
  are generated typed-edge layers above those refs. The first implementation
  should stay inside `devctl` as a report-only query surface over existing
  artifacts; optional SQLite/semantic acceleration remains later optimization,
  not authority.
- 2026-03-20: Measured the current docs-system baseline before planning the
  fix. The repo currently has `26` markdown files under `dev/active`
  (`27,462` lines), `15` markdown files under `dev/guides` (`9,874` lines),
  and `1,858` lines across maintainer entry docs (`AGENTS.md` +
  `dev/README.md`).
  The largest active docs are now `ai_governance_platform.md` (`4,969`
  lines), `ide_provider_modularization.md` (`2,935`), `MASTER_PLAN.md`
  (`2,838`), and `memory_studio.md` (`2,075`), with `operator_console.md`
  (`1,978`) and `theme_upgrade.md` (`1,930`) just behind them. This measured
  baseline is now the starting point for the documentation-authority cleanup,
  not a vague “too many docs” complaint.
- 2026-03-20: Tightened the documentation-authority plan from “unify docs”
  into a concrete contract. Accepted additions: one canonical metadata header
  split between plan vs non-plan docs, closed status/owner/role/authority
  taxonomies, class-based line budgets with explicit exception handling, a
  first bounded `check_plan_doc_format.py` guard under the existing
  docs-governance stack, a registry-driven replacement for hardcoded
  plan-sync coverage, and a read-only first-step command
  `devctl doc-authority --format md` that reviewer/coder sessions can use to
  see authority drift before write-mode remediation exists.
- 2026-03-20: Elevated the unified documentation-authority system from
  implicit concern to explicit `MP-377` major priority after re-reviewing the
  full `dev/guides/SYSTEM_AUDIT.md` and the existing repo architecture. The accepted
  shape is not ad hoc doc cleanup: it is one repo-pack-owned docs contract
  (`DocPolicy`), one broader `DocRegistry` over governed markdown surfaces,
  canonical markdown metadata/schema + anchor/formatter rules, hot/warm/cold
  bounded startup context, lifecycle/graduation rules for moving stable
  operational surfaces out of `dev/active`, and docs-governance enforcement
  built on `docs-check`, `check_active_plan_sync`, `hygiene`, and
  `check_architecture_surface_sync`.
- 2026-03-20: Accepted the full tiered `dev/guides/SYSTEM_AUDIT.md` action plan as
  canonical intake that must be mapped into the existing `MP-377` phases
  rather than left in a parallel document. The mapping is now explicit here:
  blocker-tranche security, evidence/feedback loop, bootstrap compression,
  memory/session context, structural debt simplification, surface
  simplification, portability, black-box guard/probe strengthening, and
  test-hardening all stay visible as tracked work inside the canonical plan
  chain instead of living only in the repo-root audit.
- 2026-03-20: Reviewed `dev/guides/SYSTEM_AUDIT.md` intake as architecture,
  not as bulk transcription, and accepted the anti-sprawl/self-hosting pieces
  only where they strengthen the existing platform direction. The chosen path
  is to extend the current package-layout / compatibility-shim governance into
  a broader structure-policy layer over `devctl` root budgets, parser/command
  placement, subsystem file-count budgets, source-of-truth ownership,
  active-doc lifecycle, and shim expiry rather than inventing a second
  unrelated topology system. Also froze the audit-integration retirement rule:
  whole-system audits remain temporary reference evidence, and once accepted
  findings are integrated into canonical plans/docs, the moved audit copy
  should be retired instead of living on as a shadow roadmap.
- 2026-03-20: Accepted the stronger self-hosting critique as plan state. The
  governance engine has to become proof that the governance approach works on
  itself, not just something imposed on downstream repos. Added explicit
  follow-ups for a bounded `Why Stack` product thesis at the top of startup,
  governance-self-hosting calibration of shape limits versus real coupling,
  executable implemented-vs-planned contract labeling, governance-engine
  simplification/compaction, and a later clean-sheet review-channel
  simplification pass once typed runtime authority is stable.
- 2026-03-20: Re-ran the architecture/plan review with code-backed validation
  against `dev/guides/SYSTEM_AUDIT.md` and corrected the tracked order without
  creating a parallel plan. Accepted reprioritization: clear the blocker tranche first
  (daemon attach/auth security, autonomy authority hardening,
  JSONL/evidence-integrity closure, self-governance coverage), then resume the
  authority-loop spine through `startup-context`, `WorkIntakePacket`,
  `CollaborationSession`, and `ContextPack`. Accepted contract boundaries:
  `startup-context` is the canonical bounded startup family rather than a new
  sidecar `bootstrap-context`; `ConceptIndex` stays generated from canonical
  plans/contracts/artifacts; any ZGraph-compatible form is optional generated
  compression/navigation only and must be evaluated against the plain path on
  tokens, latency, task success, citation validity, and unsupported-claim
  rate before it counts as product architecture.
- 2026-03-20: Integrated `dev/guides/SYSTEM_AUDIT.md` into the
  main `MP-377` plan chain without creating a parallel roadmap. The audit
  confirms rather than replaces the active execution order: the highest-
  leverage missing product behavior is still automatic feedback of governed
  quality evidence into AI startup/session context; bootstrap bloat should be
  solved through bounded `startup-context` / `ContextPack` surfaces and a
  hot/warm/cold session-compass model; portability remains the repo-pack /
  path-authority closure already tracked under the authority loop; and
  review-channel / guard-boilerplate simplification stays follow-up cleanup
  after the portable authority loop is in place. The stale
  `dev/scripts/here.md` scratch handoff file is now retired so fresh sessions
  converge on the active plans plus the live bridge instead of a parallel
  prose surface.
- 2026-03-19: Reconciled the validated review-channel/runtime slice with the
  broader architecture draft and froze the current `MP-377` contract
  boundaries. Accepted: one startup-authority path, bridge/state projections
  over `CollaborationSession`, fail-closed resume/auto-demote rules, and a
  real single-agent vs multi-agent proof requirement in Phase 7. Not accepted
  for current `P0`/`P1`: merging `WorkIntakePacket` and
  `CollaborationSession`, replacing intake-backed writer authority with
  optimistic concurrency alone, or downgrading `PlanTargetRef` to
  heading-only targeting. The next concrete slice remains generated
  `project.governance.json` + `PlanRegistry`, `startup-context` /
  `WorkIntakePacket`, `CollaborationSession` projection materialization,
  repo-pack activation, and Phase 5a evidence-identity freeze.
- 2026-03-19: Accepted the portable planning-review loop as part of the
  `MP-377` startup/work-intake closure path. The platform direction now
  requires a repo-neutral `PlanTargetRef` plus `WorkIntakePacket` so plan
  hardening, code review, and operator follow-through share one ingestion
  contract instead of growing repo-specific `plan.md` side channels. Planning
  findings/patch proposals should reuse the existing review-channel packet
  transport, but canonical plan markdown remains single-writer authority and
  mutable targets must resolve by registry-generated stable anchors plus
  target revision rather than brittle surrounding prose or raw line-number
  matching. The proof pass also tightened the missing details: intake packets
  now need explicit writer-lease metadata, plan targets need a normalized
  collision-free anchor-id contract, plan patches need typed mutation ops, and
  non-VoiceTerm adopters need a minimum bootstrap artifact set before planning
  review can be considered portable.
- 2026-03-19: Accepted a final transition-mechanics validator pass for the
  new authority-loop lane and tightened the subordinate `MP-377` sequencing so
  the migration path is explicit, not just the target architecture. The
  authority-loop plan now splits Phase 5 into a Phase 5a evidence-identity
  freeze before the first runtime slice plus a Phase 5b provenance/ledger
  closure after it, requires a compatibility-first repo-pack rollout instead
  of a one-shot Phase 2 cutover, makes legacy governance-review
  schema-version backfill/upgrade work explicit before hard validation,
  records `MP-359` desktop path cleanup as a repo-pack activation dependency,
  and defines cross-repo proof in terms of portable versus repo-structure-
  only guards.
- 2026-03-19: Accepted the platform-authority-loop extraction as the current
  highest-priority subordinate `MP-377` lane and added
  `dev/active/platform_authority_loop.md` as its execution spec. The accepted
  loop is now explicit in repo-visible plan state:
  `ProjectGovernance -> RepoPack -> PlanRegistry -> PlanTargetRef ->
  WorkIntakePacket -> TypedAction -> ActionResult / RunRecord / Finding ->
  ContextPack`. The same update also captured the extra gaps surfaced by the
  final architecture audits so they do not get lost between sessions: full
  `active_path_config()` rewrite scope, bundle/check extensibility,
  platform-wide contract versioning, structured plan-doc schema, provenance
  closure, proof-pack/evaluation schema, and the monorepo-first extraction
  decision.
- 2026-03-17: Accepted the Architectural Knowledge Base direction. Added a new
  "Architectural Knowledge Base (Topic-Keyed AI Context)" section defining
  the concept: auto-capture scripts flag architecturally significant events,
  store them in the SQLite-backed knowledge layer (using the already-defined
  schema in `memory/schema.rs`), organize by topic-keyed chapters with token
  budgets, export as bounded JSON into `ContextPack`, and integrate with
  `ConceptIndex` / ZGraph for graph-traversal-based selective retrieval.
  SQLite runtime activation and evidence-to-memory bridge are `P0`
  prerequisites; the full knowledge-base with auto-capture, chapter budgets,
  and ConceptIndex integration is `P1` item 10. Added 4 new checklist items
  and updated the MASTER_PLAN snapshot with the direction.
- 2026-03-17: Completed a 25-agent comprehensive architecture audit covering
  every major surface in the repo: Rust application (87K LOC, grade A-),
  Python governance (141K LOC, B+), guard system (64 guards, B), probe system
  (26 probes, B-), operator console (31K LOC, B+), CI workflows (30, B-),
  configuration coherence (A), documentation accuracy (A-), command UX (67
  commands, B), cross-repo portability (62/100), error handling (B), AI
  bootstrap (C+), and self-consistency (C). Five critical findings: (1) JSONL
  `jsonl_support.py:14-17` silently skips corrupted lines, undermining ledger
  trust; (2) no self-referential enforcement layer — 6 guards untested, 13
  not in CI, 2 functions exceed limits without exceptions; (3) 88K-token
  bootstrap with no filtered/cached view; (4) portability is engine-deep but
  not product-ready (no `governance-init` wizard); (5) Rust ContextPack and
  Python governance evolved independently with no bridge. Added next-action
  items 30-33 to close the concrete gaps: `check_governance_closure`
  meta-guard, JSONL + exception immediate fixes, command UX standardization
  contract, and CI workflow timeout enforcement. All other findings were
  already covered by existing plan items or the MASTER_PLAN status snapshot.
  The plans are now complete for execution.
- 2026-03-17: Independent review of the live `MP-377` worktree found two
  still-open meta-governance closure gaps that the current green checks do not
  prove away. First, `check_platform_contract_closure.py` currently reports
  success while checking only `8` of the `13` shared contracts exposed by
  `platform-contracts`, and it still does not validate actual review-channel
  emitter/projection payloads against the emitted `ReviewState` shape.
  Second, the core `Finding` / `governance-review` runtime path still allows
  machine-specific IDs through absolute `repo_path` inputs outside the
  `review_probe_report.py` workaround. Accepted sequencing rule: keep Claude's
  live coding slice bounded to `ReviewState` emitter parity plus stable
  review-channel identity first, but record both guard-coverage expansion and
  repo-path normalization/rejection as explicit next `P0` self-hosting follow-
  ups instead of treating the current green guard output as closure.
- 2026-03-17: Accepted a new plan-anchored reporting/evaluation concept under
  `MP-377`: a repo-wide governance-quality-feedback surface that reads the
  existing adjudication ledgers, guard/probe artifacts, watchdog episodes, and
  related data-science inputs to explain false-positive causes, report rule
  quality, and emit a bounded maintainability/evaluation snapshot for AI and
  human operators. Keep it inside the current platform spine instead of
  creating a parallel scoring subsystem: CLI/artifact surfaces first, portable
  repo support through the same repo-pack/evidence contracts, and PyQt6/mobile
  consumers only after the core contract and command are stable. Halstead /
  Maintainability Index work must reuse the existing `MP-378`
  `code_shape_expansion.md` research lane rather than inventing a second
  independent metrics plan.
- 2026-03-17: Refined the scoring contract for that same `MP-377`
  governance-quality-feedback surface. The first single composite
  maintainability score is acceptable only as an interim implementation, not
  the final architecture. The target contract is a transparent multi-lens
  scorecard with explicit evidence coverage and non-black-box explanations:
  `CodeHealthScore` for intrinsic code structure, `GovernanceQualityScore` for
  rule quality / adjudication / cleanup, and `OperabilityScore` for
  time-to-green / queue friction / workflow health. An optional overall summary
  may remain, but only as a secondary gated result that is visibly derived from
  the lens stack. Do not use median as the top-level cross-lens aggregator;
  median can hide a failing lens and should only be considered within one lens
  across related sub-metrics.
- 2026-03-17: Accepted a more concrete AI-driven setup contract for adopter
  repos. The bootstrap path should not stop at starter policy plus setup prose;
  it needs one reviewed repo-local governance document
  (`project.governance.md` as the current working name) that AI can draft from
  deterministic repo evidence and humans can finish with priorities, debt,
  ignore/exclusion intent, and quality goals. The intended flow is now
  explicit: `governance-draft` infers identity, languages, roots, CI/test
  shape, architecture hints, boundary rules, and current baselines; human
  review fills the non-deterministic fields; `governance-bootstrap` and/or a
  later `governance-init` derive repo policy and startup surfaces from that
  approved contract; and later drift scans should suggest contract updates when
  the repo no longer matches the declared model.
- 2026-03-17: Captured the next product-level clarification after maintainer
  review: the platform must separate deterministic agent coding from raw
  unstructured architecture debt, but not demote AI out of the design lane.
  The next contract layer now needs to distinguish repairable findings from
  typed design-choice packets with explicit invariants, options, precedent,
  rationale fields, and validation plans. Long-term product rule is now
  explicit in active state: general AI/dev surfaces should get the fix lane
  plus routed checks, while `design_decision` material must move into a
  reusable decision packet whose policy declares whether the agent may
  auto-apply, should recommend-only, or must wait for approval.
- 2026-03-17: Product intent was tightened again after architecture review: if
  the platform cannot give AI enough typed evidence to reason over the same
  design choice a senior developer can handle, that is a platform failure, not
  a reason to keep a human-only judgment lane. The distinction is autonomy
  mode, not intelligence tier. Decision packets should therefore be the same
  backend contract for AI and humans, with policy only gating whether the AI
  may apply the change, should recommend it, or must explain and wait.
- 2026-03-17: Landed the first concrete decision-packet slice in the canonical
  self-hosting surface: `.probe-allowlist.json` `design_decision` entries now
  emit typed decision packets with `decision_mode`, rationale, optional
  invariants/precedent/validation-plan fields, and the `devctl probe-report`
  markdown/terminal artifacts now present them as AI/human decision packets
  instead of a maintainer-only bucket. The slice also split the new renderer
  code into dedicated helper modules to satisfy package-layout and code-shape
  enforcement; `check --profile ci`, `docs-check --strict-tooling`, and
  `check_active_plan_sync.py` all pass on the resulting implementation.
- 2026-03-17: Ran another architecture pass over the `P0` contract-freeze
  seam after operator feedback and a three-lane review covering contracts,
  AI/dev operating flow, and portability. The next missing layer is now
  explicit in plan state: add a contract-closure/meta-governance guard so
  schema/version structure, packet families, validation routing, and generated
  AI/dev surfaces cannot drift independently. `P0` now says explicitly that
  `platform-contracts` is still a partial blueprint until it covers the full
  contract spine, every durable packet family gets a schema matrix plus
  enforcing guard, `FixPacket` and `DecisionPacket` close through
  `governance-review`, and `surface_generation` must derive workflow semantics
  from structured action/taxonomy metadata instead of repo-policy prose blocks
  alone.
- 2026-03-17: Landed the first code slice of that contract-closure seam in the
  canonical `probe-report` path. Aggregated probe hints now carry stable
  `finding_id` / `rule_id` / `rule_version` metadata before decision-packet
  routing, durable `probe-report` artifact families (`summary`, `file_topology`,
  `review_packet`, `review_targets`) now emit explicit `schema_version` and
  `contract_id` fields, and `.probe-allowlist.json` routing now honors
  `file` + `symbol` + `probe` so multiple probes on one symbol can be routed
  independently. Maintainer docs and the allowlist template now describe the
  versioned root payload shape too. The runtime seam was tightened in the same
  slice so finding identity now builds from a typed seed, decision packets
  project from typed policy inputs instead of long ad hoc parameter lists, and
  the contract file clears the repo's own parameter-count/dict-schema guards.
  Validation is green:
  `python3.11 -m pytest dev/scripts/devctl/tests/test_probe_report.py -q --tb=short`,
  `python3.11 dev/scripts/devctl.py check --profile ci`,
  `python3.11 dev/scripts/devctl.py docs-check --strict-tooling`, and
  `python3.11 dev/scripts/checks/check_active_plan_sync.py`.
- 2026-03-17: Fresh multi-agent architecture review narrowed the next
  executable guard seam: add a new `check_platform_contract_closure.py`
  instead of overloading the existing narrow `platform_contract_sync` guard.
  The new guard should reconcile the plan-owned `P0` contract list,
  `platform-contracts`, runtime models, schema/version matrices, and
  generated AI/dev startup surfaces for the already-real families
  (`TypedAction`, `RunRecord`, `ArtifactStore`, `ControlState`, `ReviewState`,
  `Finding`, `DecisionPacket`, `ProbeReport`, `ReviewPacket`,
  `ReviewTargets`, `FileTopology`, `ProbeAllowlist`) while treating later
  packet families as planned, not implemented. The same review also confirmed
  one portability defect still open in the first finding seam: durable finding
  identity should move off checkout-path hashing and onto stable repo identity
  plus repo-relative path, with absolute repo roots kept only as provenance.
- 2026-03-17: Landed that first bounded contract-closure guard slice. The
  platform blueprint now records runtime-model pointers plus durable artifact
  schema rows for `TypedAction`, `RunRecord`, `ArtifactStore`,
  `ControlState`, `ReviewState`, `Finding`, `DecisionPacket`,
  `ProbeReport`, `ReviewPacket`, `ReviewTargets`, `FileTopology`, and
  `ProbeAllowlist`, and `check_platform_contract_closure.py` now reconciles
  those rows against runtime dataclass fields, emitted schema constants, and
  the repo-policy startup-surface tokens that point operators at
  `platform-contracts`, `render-surfaces`, and the closure guard itself. The
  guard is now registered in the script catalog, quality-policy defaults, repo
  preset/policy, and shared governance bundle so AI/dev surfaces discover it
  through the same authority path instead of through chat memory. Focused
  validation is green:
  `python3.11 -m pytest dev/scripts/devctl/tests/platform/test_platform_contracts.py -q --tb=short`,
  `python3.11 -m pytest dev/scripts/devctl/tests/checks/platform_contract_closure/test_check_platform_contract_closure.py -q --tb=short`,
  and `python3.11 dev/scripts/checks/check_platform_contract_closure.py`.
- 2026-03-17: The first full routed validation pass over this slice exposed a
  real self-hosting execution bug instead of a code-quality regression:
  `check-router` was still shelling repo-owned bundle commands through literal
  `python3`, so machines with `python3` < repo minimum fell back to the wrong
  interpreter and died before the routed lane could even start. Fixed that by
  pushing the same repo-owned shell-command normalization used by
  `tandem-validate` into the shared `devctl` helper path, keeping the old
  compatibility export for tandem support, and re-running the router tests plus
  dry-run lane output until planned commands all used the active interpreter.
  The same cleanup also burned down the remaining self-hosting guard debt from
  this slice: platform contract rows now resolve through focused row modules
  behind a compatibility shim so the catalog stays shape-compliant, and the
  new closure/sync tests share one helper instead of duplicating blueprint
  mutation logic. Focused validation is green:
  `python3.11 -m pytest dev/scripts/devctl/tests/test_check_router.py -q --tb=short`,
  `python3.11 -m pytest dev/scripts/devctl/tests/governance/test_simple_lanes.py -q --tb=short`,
  `python3.11 dev/scripts/devctl.py check-router --since-ref origin/develop --dry-run --execute --format md`,
  `python3.11 dev/scripts/checks/check_code_shape.py`,
  and `python3.11 dev/scripts/checks/check_function_duplication.py`.
- 2026-03-17: Validated a whole-system architecture audit against the current
  repo and `MP-377` state. Accepted the substance, but narrowed the execution
  order. Confirmed in code that probe findings still hash the absolute checkout
  root through `review_probe_report.py` -> `build_finding_id()`, and that hard
  guards still emit family-local violation dicts instead of the canonical
  `Finding` contract used by `probe-report`. Also confirmed that
  `governance-review` already accepts `guard` / `probe` / `audit` review rows,
  so the remaining gap is translation/unification rather than missing ledger
  support. Packaging/install-surface work, `MASTER_PLAN` compaction, function-
  exception migration into policy, and PyQt6/operator-console seam cleanup are
  all valid follow-ups, but they stay sequenced behind the current `P0`
  contract-freeze tranche unless one of them becomes a concrete blocker for
  finding/action contract closure.
- 2026-03-17: Folded in a second public-state architecture audit against the
  current branch and corrected it where the tree has moved. The contract spine
  is still not closed, but the failure mode is now "partial authority" rather
  than "missing from zero": `platform-contracts` already carries current rows
  for `ActionResult`, `Finding`, and `DecisionPacket`, while the remaining `P0`
  problem is that `FixPacket`, taxonomy/map contracts, validation-routing
  ownership, and full closure enforcement are still open. The same audit also
  confirmed three blockers that need to stay explicit in the active plan:
  1) stable identity is still wrong in two places because
  `governance_review_log.py` duplicates the same repo-path-based identity bug
  that `review_probe_report.py` just stopped feeding into `FindingIdentitySeed`;
  2) the current PyQt6/mobile/overlay consumers are still mostly artifact/
  projection-backed thin clients with rebuild fallbacks, not one closed live
  backend/service protocol; and 3) the typed runtime seam still accepts legacy
  nested payload shapes (`controller_payload`, `review_payload`, bridge-liveness
  overlays) too broadly to count as production closure. Also confirmed that
  VoiceTerm-specific assumptions still leak below the intended repo-pack
  boundary (`voiceterm_repo_root()`, `REPO_ROOT`, `voiceterm_daemon`, VoiceTerm
  launcher/branding notes) and should now be treated as boundary-enforcement
  debt, not as harmless transitional defaults.
- 2026-03-17: Captured the next portable coherence-layer scope explicitly so it
  does not get lost behind the current `P0` runtime blockers. The repo already
  has a narrow naming-consistency seed plus strong local code-shape/probe
  coverage, but it still lacks deterministic cross-file coherence checks for
  naming drift, contract-field vocabulary drift (`path` vs `file_path` style
  mismatches), import-pattern drift, and template-structure drift in new files.
  Accepted direction: widen the existing naming/policy path instead of
  inventing a second greenfield subsystem, keep the rules policy-driven and
  portable, start advisory when noise is unknown, and prove value on a small
  reference repo before claiming the layer generalizes.
- 2026-03-17: Tightened the relationship between that coherence layer and the
  existing readability/complexity research. Halstead volume, identifier
  density, cognitive complexity, and later entropy/cohesion metrics should
  feed the coherence system as ranking/prioritization evidence and repair
  hints, but they are not substitutes for repo-policy-backed convention rules.
  The contract should stay: policy defines what "consistent" means for a repo;
  metrics help decide where drift is densest and which fixes are likely to pay
  off first.
- 2026-03-17: Reviewer intake kept one runtime blocker explicit in plan state
  so it does not disappear into the bridge. The first guard-to-`Finding`
  helper landed in `devctl.runtime`, but the current tree still lacks a
  non-test production call path that projects real hard-guard violations
  through that adapter. Until one live guard/report path uses the seam, the
  `P0` evidence-model gap is narrowed but not closed and wording must not
  claim that guards already emit canonical `Finding` records end-to-end.
- 2026-03-17: Captured the next missing authority seam in explicit product
  state: the repo has strong startup ingredients (`AGENTS.md` bootstrap order,
  `check-router`, `orchestrate-status`, `docs-check`, `render-surfaces`,
  `swarm_run`), but still lacks one enforced, repo-pack-aware work-intake path
  that reads active plans plus the current git diff and then tells an AI or
  human exactly which plan scope is active, which bundle/check route applies,
  and which durable sink should receive accepted findings or decisions. The
  end-state here is not VoiceTerm-specific supervision; it is a reusable
  startup-authority surface any adopting repo can drive through its own
  `RepoPack` metadata.
- 2026-03-17: Accepted the stricter closure rule for legacy payload adapters.
  `ControlState` / `ReviewState` compatibility reducers remain necessary
  during migration, but they are now explicitly debt, not acceptable long-term
  authority. New clients or startup surfaces should consume typed runtime
  state first, treat raw nested payloads as edge-only adapters, and require
  parity fixtures before any legacy shape is allowed to survive another phase.
- 2026-03-17: Folded the portable convention-system proposal into the active
  product plan at a more concrete level. The accepted architecture is now:
  repo-policy convention schema, deterministic naming/directory/import guards,
  advisory drift probes for undeclared conventions, and one discovery/report
  surface (`naming-scan` / `naming-report`) that can feed both humans and AI.
  This stays repo-neutral by flowing through the existing quality-policy /
  repo-pack stack, and AI usage should come from startup/work-intake surfaces
  rather than from hand-written chat guidance.
- 2026-03-17: Tightened the AI trust rule for that convention system. Learned
  conventions from `naming-scan` are proposal input only; declared repo policy
  is the blocking authority, and `naming-report` is the AI-readable surface
  that should summarize policy, discovered patterns, current drift findings,
  and recommended checks before a coding slice starts.
- 2026-03-17: Early bootstrap/AI-usability audit reinforced the startup-
  authority work with two concrete requirements: first, startup must collapse
  into a minimal task-scoped surface instead of forcing agents through the full
  maintainer doc stack; second, probe/convention views need filtered outputs so
  an agent can tell which checks matter for the current slice. The same audit
  also surfaced a missing contract-guard opportunity on the daemon seam:
  Rust↔Swift compatibility is guarded today, but Python runtime models remain
  unguarded copies. Accepted follow-up: add a Rust daemon ↔ Python runtime
  parity guard as part of the shared-contract closure work.
- 2026-03-17: Tightened plan ownership and phasing after a focused
  navigability audit. `MASTER_PLAN` already states the real `P0 -> P1 -> P2`
  order, but this plan still reads like one mixed backlog to an AI. Accepted
  routing rule: `MP-267` is repo-local cohesion cleanup only,
  `portable_code_governance.md` owns the reusable convention engine, and this
  plan owns startup/work-intake, grouped command discovery, validation
  routing, and how convention context shows up in generated user/AI surfaces.
- 2026-03-17: Accepted a more specific startup-authority end-state for AI and
  human operators. The missing artifact is not just "better bootstrap docs"
  but one intake packet/surface that answers: active plan, changed scope,
  mapped MP lane, command goal, routed checks, relevant probe/convention
  subset, and the right durable sinks for accepted findings or decisions.
  `RepoMapSnapshot`, `MapFocusQuery`, and `TargetedCheckPlan` now count as
  prerequisites for that bounded intake surface rather than parallel
  nice-to-haves.
- 2026-03-17: Accepted the cache-first architecture for that intake surface.
  The repo should stop re-paying the full bootstrap cost every conversation.
  The concrete path is: run expensive scans once, persist canonical artifacts
  (`plan snapshot`, `command map`, `convention snapshot`, `RepoMapSnapshot`,
  filtered probe summary, targeted-check hints) behind `ArtifactStore`, track
  refresh/invalidation by git diff plus plan/policy hashes, and let
  `startup-context` / work-intake return one bounded packet from those cached
  artifacts. Optional SQL/query acceleration is valid after the canonical JSON
  snapshot contract exists; semantic/vector retrieval is an optimization layer,
  not the authority.
- 2026-03-21: Accepted the next cache-first refinement for that same startup
  path: checkpoint/push should emit one generated repo-pack-owned packet into
  the managed cache/artifact root so the next session can warm from fresh
  repo evidence instead of recomputing the same bounded git/plan/guard/review
  summary. This packet is an accelerator, not authority: it is keyed by tree
  hash / commit sha, invalidated by source drift, safe to delete and rebuild,
  and subordinate to canonical git state, active plans, repo policy, and
  guard/review outputs. Performance target stays "read the fresh packet when
  present, recompute from canonical sources when not" so startup gets faster
  without introducing a shadow memory store.
- 2026-03-17: Accepted the recursive-convergence framing with one important
  sequencing rule. The repo already has partial loops (`guard-run`,
  `probe-report`, Ralph/reviewer reruns), but the full-platform version still
  needs one cached aggregate evidence surface (`master-report`) and one
  measured fixed-point orchestration surface (`converge`). Those commands are
  now tracked as product work, but they must land only after the remaining
  artifact families are schema-versioned and the aggregate evidence contract is
  stable enough to compare iterations honestly.
- 2026-03-17: Ran a cross-surface convergence review across shared runtime,
  review-channel, PyQt6, and iPhone/mobile. Accepted the corrected result into
  plan state: the contract spine is no longer missing from zero, but the main
  shared-state gap is still real. `ReviewState` is emitted in multiple
  producer-specific shapes and normalized by parser compatibility glue; the
  live review loop still treats `bridge.md` as temporary authority; the
  review-channel `project_id` still derives from absolute checkout paths; the
  current mobile relay guard can report green with `matched_pairs: 0`; and
  both Operator Console and iPhone still prefer compatibility payloads or
  markdown-derived state before canonical typed state. Accepted order: unify
  `ReviewState` emission plus stable repo identity first, add daemon/runtime
  parity guard second, then migrate PyQt6/iPhone consumers to typed-state-
  first reads and keep markdown / legacy payloads as fallback-only adapters.
- 2026-03-17: Added the governance-completeness follow-up after the
  overengineering/readability audit. The platform plans now explicitly track
  a meta-guard layer for guard/probe test coverage, CI invocation coverage,
  exception-list completeness, workflow timeouts, and data-as-code/config
  drift. `master-report` and `converge` are now expected to surface
  governance-quality findings, not only product-code findings, so the system
  can prove the health of its own checking mesh.
- 2026-03-17: Verified the adjacent Rust memory lane against code before
  widening the startup-context plan. The repo already has a real first
  generation memory substrate: deterministic retrieval queries (`Recent`,
  `ByTopic`, `ByTask`, `TextSearch`, `Timeline`), signal-routed context
  strategies, exported `ContextPack` builders with token budgets, a real
  `SurvivalIndex`, JSONL persistence, and a staged SQLite schema contract.
  Accepted correction: do not describe that stack as "not built," but also do
  not overclaim it as a finished persistent/query authority. The actual gap is
  integration with governance/runtime evidence. Accepted plan shape: make
  `startup-context` compose cached repo-intelligence artifacts, governance
  evidence, and exported memory receipts/refs; add one deterministic
  `ConceptIndex` navigation artifact above those caches; keep optional
  SQLite/semantic acceleration as a later optimization instead of the
  authority layer.
- 2026-03-17: Burned down the next `MP-377` self-hosting hotspot in the
  review-channel/control-plane seam and fixed a real governance-surface bug in
  the canonical operator path. `dev/scripts/devctl/commands/review_channel.py`
  now routes validation, runtime-path coercion, status enrichment, ensure
  reads, action dispatch, and report emission through smaller typed helpers
  while preserving the same CLI contract and focused test coverage. In the
  same slice, `dev/scripts/devctl/review_probe_report.py` now passes
  `repo_root` into markdown/terminal render helpers so
  `.probe-allowlist.json` design-decision entries actually shape the main
  `devctl probe-report` output instead of only the fallback
  `run_probe_report.py` path. Maintainer-facing probe docs were corrected to
  describe the real allowlist schema (`entries`, `disposition`, file+symbol
  matching). Current local result after the fix/refactor: `probe-report`
  shows `0` active high findings, `14` active medium findings, and `25`
  design decisions, so the next cleanup order is medium-only identifier-
  density debt plus the remaining root shim family budget.
- 2026-03-17: Consolidated repo-wide plan routing after a maintainer review
  exposed that the first-read summary surfaces were still advertising the older
  Theme-first sequence. `MASTER_PLAN` now explicitly points repo-wide strategy
  to `MP-377` first, `INDEX.md` tells agents to read this plan for repo-wide
  status/extraction questions, and Theme/Memory plan headers no longer claim
  primary-lane status. The intended order is now explicit in repo state:
  extract the AI-governance system and shared runtime contracts first, converge
  VoiceTerm/PyQt6/phone/CLI on that backend second, rebind VoiceTerm as a
  first consumer third, then return to the broader Theme/Memory lanes.
- 2026-03-16: Promoted the plain-language `devctl` system map into durable
  repo guidance with `dev/guides/DEVCTL_ARCHITECTURE.md`. The guide now
  explains the whole control-plane shape for AI and human readers: one backend,
  many clients; which layers own policy/runtime/artifacts; how `devctl` fits
  with VoiceTerm, PyQt6, phone/mobile, CI, and hooks; and the portable next
  contracts now requested by the operator. Two product-level follow-ups are
  now explicit in that guide instead of living only in chat: (1) turn the
  narrow current naming check into a repo-policy-backed naming-contract guard
  that any repo can reuse, and (2) promote the existing topology backend
  (`probe_topology_*`, `file_topology.json`, hotspot graphs, review packets)
  into a first-class `devctl map` surface for flowcharts, AI context packets,
  and later hook/slash-command reuse.
- 2026-03-16: Tightened the missing piece in that architecture direction after
  maintainer review. `map` should not stop at topology or diagrams: the public
  contract now needs to combine topology, complexity, hotspot ranking,
  changed-scope overlays, guard/probe/review evidence, and recommended check
  plans so AI can go from "understand the repo" to "run the right bounded
  checks on the risky slice" without inventing the workflow in prompts. The
  storage rule is now explicit too: keep map truth under the shared
  `ArtifactStore` as canonical JSON plus refresh-ledger rows and an optional
  SQLite query index; later memory/database layers may ingest refs to that
  evidence, but they do not replace it as the authority. The naming contract
  is also now explicitly two-layer: stable backend ids plus repo-pack-owned
  friendly wrappers, guarded so simpler beginner/agent UX does not fork
  behavior.
- 2026-03-16: Captured the broader product-shape clarification so scope does
  not drift. The platform is now explicitly defined as a set of standalone,
  repo-portable pieces that must also compose into one integrated agent app.
  The plan now names the missing product-grade pieces that still need to be
  made first-class: unified agent/job/session registry, typed tool/action/
  skill catalog, attach/resume/watch service contract, replay/recovery path,
  repo-intelligence store, evidence-to-memory bridge, workflow presets by user
  goal, observability timeline, product-grade packaging/adoption, multi-repo
  safety, and caller identity/approval.
- 2026-03-16: Converted the open platform backlog into an explicit priority
  ladder so scope does not feel equally urgent everywhere. `P0` is now the
  coherence spine: shared runtime authority, coherence matrix, identity,
  registry, capability discovery, lifecycle, approvals, `map`, evidence
  bridge, parity, and validation routing. `P1` is product-complete behavior:
  packaging/adoption, health/timeline/replay/recovery, generated startup
  surfaces, and full client/mode parity. `P2` is enrichments that should wait
  until `P0`/`P1` are real. This same review also promoted two more likely
  missing glue contracts into the checklist: a backend capability-discovery
  manifest and a typed action-result/error contract.
- 2026-03-16: Accepted the useful parts of a deeper 8-lane architecture audit
  without widening product scope. The real additional glue gaps are now
  explicit here: migrate all evidence families onto the existing canonical
  `Finding` contract, freeze one `ActionResult` envelope for command/service
  outcomes, define one `CommandGoalTaxonomy` for grouped discovery, and make
  schema-version coverage guardable across every durable machine artifact
  family. The same review confirmed that golden cross-client parity remains
  `P0`, and that multi-client write arbitration should stay in the spine
  rather than being deferred as later polish.
- 2026-03-16: Rephased that same audit intake so it does not flatten the
  roadmap. The current execution slice is now explicitly limited to `P0`
  contract-freeze work: the missing contract spine
  (`ActionResult`, `CommandGoalTaxonomy`, `RepoMapSnapshot` /
  `MapFocusQuery` / `TargetedCheckPlan`), the control-plane safety seam
  (service identity/discovery, attach/auth, write arbitration, degraded-mode),
  and the evidence/compatibility seam (`Finding` migration, schema-version
  coverage, artifact taxonomy, deprecation/compatibility, contract-sync).
  Packaging/adoption/client-parity work remains `P1`, and proof/scale work
  such as whitepaper/rule-mining/language expansion remains `P2`.
- 2026-03-16: Accepted the bounded `M67` reviewer-worker status seam. The
  first repo-owned reviewer-worker contract now lives under the extracted
  Python `devctl/review_channel` backend boundary: `review-channel status`,
  `ensure`, `reviewer-heartbeat`, `reviewer-checkpoint`, and the
  bridge-backed `full.json` projection now emit machine-readable
  `reviewer_worker` state, while `ensure --follow` cadence frames surface
  `review_needed` without pretending semantic review completion. This closes
  the first "outside chat" status/loop seam, but not the broader reviewer
  worker problem. Next bounded follow-up: lift the signal-only seam into a
  report-only supervisor/watch path that can keep polling and publishing
  operator-visible updates outside chat before semantic review automation or
  Rust/VoiceTerm host ownership moves further.
- 2026-03-17: Accepted the bounded `M68` report-only reviewer supervisor/watch
  slice. `reviewer-heartbeat --follow` now polls on cadence, refreshes
  reviewer heartbeat through the repo-owned Python `devctl/review_channel`
  seam, and emits operator-visible `reviewer_worker` frames without claiming
  semantic review completion. Current local re-review is green (`122`
  review-channel tests plus `check_review_channel_bridge.py`). The next
  bounded follow-up is now `M69`: add repo-owned detached lifecycle/status
  truth for that supervisor path so it can stay alive and observable outside
  the current terminal/chat session before widening into semantic-review
  automation or Rust/VoiceTerm host ownership.
- 2026-03-16: Recorded the real reviewer-lane failure class explicitly: the
  current Claude implementer path can behave like a persistent worker, but the
  Codex reviewer path still is not a repo-owned persistent worker/service and
  still depends on this chat session staying alive. The repo already has
  heartbeat/checkpoint writers plus a publisher path, but it still does not
  own semantic reviewer polling/re-review/promotion outside chat. Treat that
  as a separate architecture blocker from the current bounded Claude coding
  slice. Required fix: add a repo-owned Codex reviewer worker/supervisor path
  that runs outside chat, polls on cadence, writes reviewer checkpoints, and
  emits operator-visible updates without waiting for user prompts.
- 2026-03-16: Accepted the bounded `M66` publisher-lifecycle attention slice.
  Shared attention/runtime state now distinguishes `failed_start` and
  `detached_exit` instead of collapsing both into generic
  `publisher_missing`, and the focused review-channel/runtime bundle is green
  (`135` passing). This does not change the broader extraction direction:
  the existing VoiceTerm daemon remains the transport/session host path, but
  the first `M67` reviewer-worker implementation should still land under the
  extracted Python `devctl/review_channel` backend seam rather than moving
  reviewer-worker ownership into the Rust/VoiceTerm daemon too early.
- 2026-03-16: Accepted the bounded `M65` detached publisher durability slice.
  The detached-start path now records `failed_start` when the spawned
  publisher is dead on arrival, and `read_publisher_state()` infers
  `detached_exit` when a previously started publisher dies before the next
  controller read without writing its own stop reason. Focused review-channel/
  runtime proof is green (`133` passing). Next bounded follow-up: lift those
  publisher lifecycle outcomes into machine-readable attention/recovery state
  instead of collapsing them into generic `publisher_missing`.
- 2026-03-16: Accepted the bounded `M64` clean-stop slice for follow-backed
  controller runs. `review-channel ensure --follow` now exposes explicit stop
  reasons (`timed_out`, `manual_stop`, `completed`, `output_error`), supports
  `--timeout-minutes`, and writes final publisher state on exit; the focused
  review-channel/runtime bundle is green (`131` passing). New next blocker:
  the detached `--start-publisher-if-missing` launcher path still needs a
  truthful durability contract, because the auto-started publisher can die
  immediately and leave lifecycle ambiguity unless the controller supervises
  or reclassifies that path explicitly.
- 2026-03-16: Accepted the bounded `M63` timeout-escalation slice. The shared
  review/controller path now exposes machine-readable `reviewer_overdue`
  attention above plain stale reviewer heartbeat, threads the overdue
  threshold through `review-channel status`, and proves the overdue/stale
  boundary with the focused review-channel/runtime test bundle (`129`
  passing). Promoted the next bounded lifecycle follow-up to `M64`: freeze the
  first clean stop/shutdown contract for follow-backed controller runs with
  explicit stop reasons, timeout budget, and final state write.
- 2026-03-16: Accepted the bounded `M55` lifecycle-truth slice. The shared
  backend now fails closed when the publisher is required but missing, the
  shared status/runtime path emits `publisher_missing` instead of false-green
  `healthy`, and the focused proof bundle is green (`127` tests). The runtime
  still honestly reports `publisher_missing` in this session because no
  controller-owned publisher is running; that is now truthful attention, not a
  code-shape bug. Promoted the next bounded lifecycle follow-up to `M63`:
  configurable timeout/escalation budgets for reviewer-overdue, coder-wait,
  idle-session, and absolute-run limits.
- 2026-03-16: Recorded the live 5-hour Claude wait as a real architecture
  failure, not just operator annoyance. The current bridge/publisher work can
  still leave Claude parked if reviewer cadence does not advance, which proves
  the controller contract still lacks timeout budgets, overdue escalation, and
  clean stop semantics. Added those as explicit platform requirements:
  configurable reviewer/coder/session timeouts, controller-owned
  `fresh -> overdue -> timed_out` escalation, and stop/shutdown cleanup that
  terminates helper processes and verifies the repo/host is clean.
- 2026-03-16: Re-reviewed the next `M55` lifecycle step after landing
  `--start-publisher-if-missing` on `review-channel ensure`. The new
  start/resume seam is real and focused tests are green, but the controller
  contract is still not honest enough to count as done: in active dual-agent
  mode the backend still reports `ok: true` when the publisher is required but
  missing, and that lifecycle gap is not yet threaded through the shared
  attention/runtime projection path. The next bounded step stays inside the
  same slice: add a machine-readable publisher-missing attention state and
  make `ensure` degrade unless auto-start actually recovers the publisher.
- 2026-03-16: Landed the first concrete `M54` backend-owned publisher slice
  instead of another markdown-only workaround. `review-channel ensure --follow`
  now refreshes reviewer heartbeat on cadence through repo-owned tooling and
  emits structured status frames via the shared output contract, with focused
  proof coverage for follow semantics and heartbeat metadata. This is real
  progress on the controller path, but it does **not** close the lifecycle
  problem yet: the loop still requires an explicit command invocation, so the
  next bounded step remains controller-owned ensure/watch supervision rather
  than more bridge-only polish.
- 2026-03-16: Re-audited the live platform from the operator/adopter angle
  instead of only the local code-review loop and promoted three more missing
  product requirements into `MP-377`. First, the next concrete control-plane
  slice should be a controller-owned `review-channel ensure/watch` path so
  reviewer heartbeat/update publishing and mode-aware liveness stop depending
  on manual chat/markdown refreshes. Second, the user-facing abstraction
  layer still needs repo-pack/policy-configurable aliases, skills, and
  startup surfaces so developers and agent adopters can tune names/defaults
  without patching the portable core. Third, the system still lacks one smart
  maintenance/cleanup surface for plans/index/archive/generated surfaces plus
  stale runtime/report/session residue; that belongs in the shared backend as
  a guarded maintenance contract, not as ad hoc cleanup scripts or manual
  reviewer work.
- 2026-03-15: Re-audited self-hosting organization and multi-agent loop
  enforcement from the product boundary, not only the local bridge. The
  current package-layout system is the right enforcement seam and is already
  blocking new flat growth in crowded roots, but the latest review confirmed
  two remaining platform gaps that should stay explicit in `MP-377`: (1)
  layout governance is still mostly Python-biased/freeze-mode and should be
  generalized through the existing `package_layout` rule model instead of a
  second crowding guard, and (2) implementer completion-stall is still only a
  tandem validator plus prompt guidance, not shared backend attention/runtime
  truth visible to VoiceTerm, PyQt6, phone/mobile, CLI, and generated skills.
- 2026-03-15: Added the missing provider/mode parity and extraction-proof
  gates after re-auditing the system from the operator viewpoint. `MP-377`
  now explicitly requires Codex and Claude to bootstrap from the same
  repo-owned instruction surfaces, run the same routed validation stack, and
  prove parity across `active_dual_agent`, `single_agent`, and `tools_only`
  modes. The same update also makes the standalone-repo plus VoiceTerm
  back-import proof a first-class completion gate instead of an implied future
  cleanup step.
- 2026-03-15: Re-audited the live tandem/control-plane path after the latest
  reviewer-state and validator work. Confirmed the product still wants one
  shared backend for developers, solo agents, dual-agent loops, PyQt6, and
  phone/mobile surfaces, then promoted the missing explicit rules into the
  plan: JSON/typed projections must become the live authority, generated
  agent/developer startup surfaces should come from the same repo-pack policy,
  and local tandem validation must distinguish real code-quality failures from
  offline/network/home-dir environment blockers in release-only checks.
- 2026-03-15: Added the current extraction warning explicitly after the latest
  architecture audit. The repo can keep landing loop/runtime improvements, but
  it should stop widening the embedded VoiceTerm shape while the reusable
  boundary is still being proven. The remaining provider-specific drift is now
  clearly identified as downstream/client work in docs, Operator Console, and
  iOS readers rather than a reason to keep the backend provider-first.
- 2026-03-15: Re-read the active architecture chain after a scope audit and
  tightened the plan language accordingly. `MP-377` now says explicitly that
  the target is the whole system becoming modular and callable from any repo:
  governance core, runtime, adapters, frontends, repo packs, and VoiceTerm as
  a consumer. `MP-340`, `MP-355`, `MP-358`, and `MP-359` remain subordinate
  implementation lanes inside that boundary, not alternate backend
  authorities. New work must now state which shared contract it strengthens
  and which VoiceTerm-embedded assumption it removes or narrows.
- 2026-03-15: Ran a whole-system separation audit instead of another loop-only
  pass and recorded the concrete blockers here. The highest-signal remaining
  coupling is now explicit: 1) portable/runtime/tooling modules still import
  `repo_packs.voiceterm` directly for default policy/report/review paths, 2)
  PyQt6/iOS/Rust consumers still read repo-internal `devctl` modules and
  VoiceTerm path config directly, 3) `bridge.md` is still embedded in live
  runtime/client code instead of being only a temporary projection, and 4)
  VoiceTerm-only env/log/process defaults still leak through shared tooling.
  The execution queue is now separation-first: active repo-pack resolution,
  frontend contract separation, bridge de-authority, then product-integration
  cleanup.
- 2026-03-15: Re-audited `MP-377` against the current repo and the latest
  control-plane thesis. Confirmed the direction remains correct, then promoted
  the missing explicit rules into the plan: external analyzers
  (Ruff/Semgrep/Clippy/Black/etc.) are subordinate engines or later adapters
  under this control plane, the governed signal taxonomy is now explicit
  (`language-engine`, `AI-shape`, `repo-contract` findings), and the first
  portable release stays intentionally narrow instead of blocking on PyQt6,
  mobile, MCP, or full workflow-loop extraction.
- 2026-03-15: Added the missing "prove the loop is worth it" rubric instead of
  leaving value claims implied. `MP-377` now says the product stack is
  `engine tools -> shape rules -> governed loop`, makes the governed loop the
  actual product layer, and requires loop-value proof on correctness
  preservation, structural improvement, cost per successful repair, and
  cross-repo generalization. The same update also made noisy rules, risky
  transformations, token bottlenecks, and still-missed AI failure patterns
  explicit review targets instead of background concerns.
- 2026-03-15: Tightened the thesis language so the scope stays honest. The
  plan now says we are improving the environment the model codes inside rather
  than "teaching the model better code," keeps code-shape separate from the
  agent-memory problem, adds follow-up stability as a measured outcome, and
  names over-modularization plus rule gaming as explicit failure modes to
  guard against when evaluating cleanup rules.
- 2026-03-15: Added the missing artifact-retrieval and guard-quality details
  to the machine-first scope. `MP-377` now says the full artifact stays on
  disk, stdout should be only a compact receipt, hash-aware reread avoidance
  is part of the runtime contract, and JSONL plus an optional SQLite catalog
  is the near-term indexing target rather than a mandatory database runtime.
  The same update also makes rule-quality meta-governance explicit: each
  guard/probe should carry examples, expected benefit, replay coverage, and
  reviewed false-positive/defer/fix stats, and the platform needs a
  meta-guard/report path that flags noisy or non-uplifting rules before they
  silently accumulate.
- 2026-03-15: Re-reviewed the recent iOS/mobile path cleanup and downgraded it
  from "closed seam" to "partial seam." The shell scripts now name the
  canonical VoiceTerm paths, but `MobileRelayPreviewData.swift` still carries
  duplicate literals with only a source-of-truth comment. Keep that surface
  marked interim until generated or emitted repo-pack-owned metadata replaces
  the duplicated literals. The same review pass also added an explicit
  green-slice commit/push reminder so `MP-377` does not keep widening an
  unreviewable dirty tree once a bounded slice is green.
- 2026-03-15: Extended the repo-pack path boundary to iOS/mobile surfaces.
  Shell scripts (`sync_live_bundle_to_simulator.sh`,
  `run_guided_simulator_demo.sh`) now centralize VoiceTerm artifact paths as
  variables with `RepoPathConfig` source-of-truth comments instead of
  inlining them in CLI args. Swift preview data
  (`MobileRelayPreviewData.swift`) now carries a canonical-source comment
  linking back to `repo_packs/voiceterm.py::RepoPathConfig`. Full
  cross-language code generation from repo-pack config is a later phase, but
  the path ownership is now explicit rather than silently scattered.
- 2026-03-15: Widened the Python frontend path boundary to 4 more Operator
  Console modules outside the state package: `logging_support.py`,
  `run.py`, `layout/layout_state.py`, and
  `collaboration/timeline_builder.py`. Added `dev_log_root_rel` and
  `layout_state_rel` to `RepoPathConfig`.
- 2026-03-15: Widened the `repo_packs.voiceterm` boundary from 5 path constants
  to a full `RepoPathConfig` frozen dataclass (13 fields) plus 5 read-only
  collector helpers (`voiceterm_repo_root`, `collect_devctl_git_status`,
  `collect_devctl_mutation_summary`, `collect_devctl_ci_runs`,
  `collect_devctl_quality_backlog`). Migrated 8 Operator Console modules to
  consume `VOICETERM_PATH_CONFIG` instead of defining their own path literals:
  `review_state.py`, `artifact_locator.py`, `bridge_sections.py`,
  `session_trace_reader.py`, `watchdog_snapshot.py`, `ralph_guardrail_snapshot.py`,
  `analytics_snapshot.py`, `quality_snapshot.py`. The last two also dropped their
  forbidden `dev.scripts.devctl.collect` and `dev.scripts.devctl.config` imports
  in favor of repo-pack-owned helpers, removing the frontend-local `importlib`
  workaround after Codex reviewer feedback. All 1328 tests pass,
  platform-layer-boundary guard is green with 0 violations, and `docs-check
  --strict-tooling` is ok.
- 2026-03-14: Started materializing the planned `repo_packs.voiceterm`
  boundary instead of only talking about it in architecture prose. Added
  `dev/scripts/devctl/repo_packs/voiceterm.py` as the first repo-pack-owned
  VoiceTerm metadata/read-only helper surface, moved the Operator Console
  workflow preset definitions onto that module, and replaced
  `phone_status_snapshot.py`'s direct `dev.scripts.devctl.review_channel.*`
  imports with one narrow repo-pack-owned `load_review_payload_from_bridge()`
  helper. That reduces the existing frontend-to-orchestration coupling without
  pretending the full `RepoPathConfig` contract is already finished.
- 2026-03-14: Closed the routed-bundle Python-version mismatch that had still
  been undermining self-hosting reliability. `check-router --execute` used to
  shell the canonical bundle strings verbatim, which meant mixed-runtime
  machines could still run routed `devctl` / guard / pytest commands under an
  older ambient `python3` even though direct `devctl check` and `guard-run`
  already reused the active interpreter. The router now rewrites repo-owned
  `python3 ...` shell commands to the active interpreter before execution,
  shared command helpers cover both script and `-m pytest` forms, and the
  focused router/common tests now pin that contract directly.
- 2026-03-14: Landed the first hard extraction-boundary enforcement slice
  instead of leaving the separation rule in plan prose. The new
  `check_platform_layer_boundaries.py` guard now lives behind repo policy and
  `devctl check --profile ci`, blocks new Operator Console and
  runtime/platform imports that reach directly into repo-local orchestration
  packages, and keeps its implementation plus tests in namespaced helper
  packages so the crowded `dev/scripts/checks` / `dev/scripts/devctl/tests`
  roots do not grow further. The same slice also taught
  `check_test_coverage_parity.py` to recurse into namespaced test packages so
  self-hosting coverage enforcement stays aligned with the package-layout
  direction instead of forcing new tests back into the flat root, and updated
  `check_architecture_surface_sync.py` so repo-enabled AI guards are treated as
  valid bundle/workflow-owned surfaces when they are enforced indirectly
  through `devctl check`.
- 2026-03-14: Added the missing raw external-evidence intake path for the
  future database/ML stack. `devctl governance-import-findings` now imports
  JSON/JSONL pilot findings into
  `dev/reports/governance/external_pilot_findings.jsonl`, writes a repo/check
  coverage summary under `dev/reports/governance/external_findings_latest/`,
  and `data-science` now joins that raw corpus with
  `finding_reviews.jsonl` so adjudication coverage is visible instead of
  pretending every imported finding was confirmed.
- 2026-03-13: Added the first explicit "simple command over policy file"
  façade for vibecoder-facing use. VoiceTerm now carries a focused launcher
  policy at `dev/config/devctl_policies/launcher.json` plus short wrapper
  commands (`launcher-check`, `launcher-probes`, `launcher-policy`) that
  target `scripts/` + `pypi/src` without forcing maintainers to remember raw
  `--quality-policy` paths. The architecture point is now explicit in repo
  state: policy files remain the authority, while human-facing entrypoints may
  project a smaller simpler command vocabulary over them.
- 2026-03-13: Landed the first launcher-lane hard guard rather than only the
  lane shell. `check_command_source_validation.py` now ships as a focused
  pilot guard for `scripts/` + `pypi/src`, the launcher policy enables it
  explicitly, and the two live launcher findings were hardened in the same
  slice: `scripts/python_fallback.py` no longer accepts free-form
  `--codex-args`, while `pypi/src/voiceterm/cli.py` validates repo URL/ref and
  forwarded argv before process launch.
- 2026-03-13: Added the missing self-hosting enforcement intake after the
  latest multi-agent audits. `MP-377` now says explicitly that every external
  audit finding must answer "why didn't the current tools catch this?" in
  repo-visible plan state, and it names the missing rule families instead of
  leaving them implicit: layer-boundary enforcement, portable path
  construction, provider/workflow adapter routing, contract completion,
  schema/platform compatibility, and the first repeatable command-source /
  shell-execution checks.
- 2026-03-13: Tightened the roadmap around the remaining concrete audit misses
  rather than only the abstract architecture. Phase 3 now includes
  `workflow_loop_utils.py` and `loops/comment.py`, Phase 4 now includes the
  deeper console-coupling files (`artifact_locator.py`, `bridge_sections.py`,
  `session_trace_reader.py`), the shared-contract section now states migration
  and rollback expectations beside version fields, and the plan now carries a
  dedicated differentiation section so the public proof pack is not left to
  imply the product thesis by accident.
- 2026-03-12: Created this execution-plan doc to separate two scopes that had
  started to blur together: `MP-376` owns the portable guard/probe engine,
  while this new `MP-377` scope owns the broader reusable product/platform
  extraction across runtime loops, frontends, repo packs, and packaging.
- 2026-03-12: Current architecture truth is now explicit in active state: the
  guard/probe/policy/bootstrap/export path is materially portable, but Ralph,
  mutation orchestration, review-channel/control-plane surfaces, host-process
  hygiene automation, and several frontend projections are still more
  VoiceTerm-local than platform-grade.
- 2026-03-12: Set the target product shape to one shared backend used by CLI,
  PyQt6, overlay/TUI, and phone/mobile surfaces, with VoiceTerm acting as a
  first consumer/repo pack instead of the permanent implementation host.
- 2026-03-12: Added `dev/guides/AI_GOVERNANCE_PLATFORM.md` as the durable
  maintainer-facing "whitepaper plus flowchart" guide for this direction so
  the core thesis is explicit: executable local governance is the authority,
  frontends are adapters, repo packs isolate repo-local behavior, and new
  repos should adopt the system through package + bootstrap instead of manual
  file copying.
- 2026-03-12: Added the first code-facing platform extraction seam under
  `dev/scripts/devctl/platform/` plus the read-only `devctl platform-contracts`
  command. The contract is still a blueprint, not yet the fully migrated
  runtime implementation, but it gives adopters and future frontends one
  machine-readable backend/layer/boundary source of truth instead of forcing
  them to infer the architecture from scattered docs and repo-local modules.
- 2026-03-12: Made repo organization part of the extraction contract rather
  than a cosmetic cleanup task: directory structure should reflect portable
  layers and public entrypoints, while internal helper families move behind
  documented subpackages or package-local directories.
- 2026-03-12: Landed the first executable shared runtime seam under
  `dev/scripts/devctl/runtime/`: `ControlState` is now a real typed contract,
  `devctl mobile-status` emits it alongside the legacy compatibility payloads,
  and the Operator Console phone snapshot loader now consumes that shared
  contract instead of re-deriving review/controller state entirely from ad-hoc
  nested dict access. This is only the first migration seam; review-channel
  packet readers, session metadata readers, collaboration surfaces, and other
  control-plane loops still need to move onto the same backend layer.
- 2026-03-12: Landed the next shared runtime seam beside `ControlState` under
  `dev/scripts/devctl/runtime/`: `ReviewState` now normalizes
  `review_state.json` and `full.json` review-channel artifacts into one typed
  session/queue/bridge/packet/registry contract, and the Operator Console
  review/session/collaboration readers now consume that runtime contract
  instead of re-walking raw review-channel dicts in each surface. This keeps
  `ControlState` as the compact cross-surface summary while moving detailed
  review-channel state into the same backend contract layer rather than leaving
  it trapped in app-local adapters.
- 2026-03-12: Promoted repo organization from a code-shape sidecar into a
  first-class portable guard concept. `check_package_layout.py` now owns
  declarative flat-root, namespace-family, and docs-sync organization rules via
  repo policy, which is the right packaging shape for agentic adoption: the
  engine evaluates structure contracts, while each repo pack decides its own
  filesystem standards.
- 2026-03-12: Added the first concrete `MP-377` migration roadmap directly to
  this active plan: target package names, ownership boundaries, phase-by-phase
  extraction order, split-readiness gates, and the initial file groups to move
  first. The immediate execution stance is now explicit: modularize fully
  in-place first, prove the boundaries with external pilots second, and split
  repositories only after runtime/adapters/frontends stop depending on
  VoiceTerm-local assumptions.
- 2026-03-13: Captured the next architecture-hardening tranche after an
  external product/portability review that largely aligned with the current
  layer model. The review did not change the platform direction; it confirmed
  it and sharpened the missing contract surfaces: freeze the import/layer
  boundary, define one versioned finding/evidence schema, finish compact
  machine receipts plus artifact-cost telemetry, strengthen Python typed/
  boundary enforcement, and preserve a replayable corpus before pushing harder
  toward training or wider rule-surface growth.
- 2026-03-13: Logged a second execution-state warning from maintainership
  review so the architecture plan stays honest about current extraction status.
  The package-layout/shim system is directionally correct, but several signals
  are still "policy says this should exist" rather than "the tree already
  matches": crowded `devctl` roots are passing mostly under freeze-mode,
  `devctl/commands` still has more intended namespaces in docs than in the real
  package tree, root shim counts remain above budget, and bootstrap still has a
  Python-version mismatch on machines where `python3` is 3.10. That evidence
  reinforces the current plan stance: next work is continued decomposition and
  self-hosting reliability, not declaring the packaging boundary finished.
- 2026-03-12: Landed the next executable runtime seam under
  `dev/scripts/devctl/runtime/`: `TypedAction`, `RunRecord`, `ArtifactStore`,
  `ProviderAdapter`, and `WorkflowAdapter` now exist as real typed contract
  records with mapping adapters and focused unit coverage. They are not yet the
  universal execution path for Ralph/review-channel/frontends, but the runtime
  layer now owns more than status snapshots alone, which is the right next
  step before adapterizing the higher-level loops.
- 2026-03-12: Wired `TypedAction` into the first live command path:
  `devctl controller-action` now emits a stable runtime contract in both the
  command report and the persisted controller-mode artifact, so phone/mobile
  surfaces and later adapters can inspect one deterministic operator-action
  payload instead of inferring intent from mixed CLI args and ad-hoc result
  dicts. This is the first non-blueprint execution path under `MP-377`; the
  next candidates should be `review-channel` and Ralph dispatch/remediation
  flows.
- 2026-03-12: Promoted layout governance from “new file placement” into a
  self-hosting platform requirement. The package-layout engine now needs to do
  two things at once: freeze further growth in already crowded flat roots such
  as `dev/scripts/checks` / `dev/scripts/devctl` / `commands` / `tests`, and
  surface that baseline crowding explicitly so external-repo adopters and
  agents can understand the organization contract before drift starts.
- 2026-03-12: Extended the same self-hosting layout governance to crowded flat
  module families. `check_package_layout.py` should now surface families such
  as `devctl/commands/check_*`, `autonomy_*`, `docs_*`, `release_*`, and
  `ship_*` as explicit baseline debt while freezing further flat growth toward
  concrete namespace targets. Thin public wrappers may still stay flat when the
  policy marks them as compatibility shims. This closes a real blind spot:
  directory counts alone were not enough to explain why `commands/` still
  looked like a dumping ground even after crowding rules landed.
- 2026-03-12: Tightened self-hosting/adoption behavior again: `package_layout`
  now emits one blocking baseline violation per crowded root/family during
  `--adoption-scan` instead of only warning about them. That means external
  repos and `devctl` itself can fail a full topology audit for existing layout
  debt without requiring a new file to be added first, while normal working-
  tree mode still preserves the lighter freeze-on-drift behavior.
- 2026-03-12: Validation against `devctl check --profile ci --adoption-scan`
  confirmed the new package-layout behavior, but it also exposed a separate
  portability gap outside this slice: several other guards still assume a clean
  worktree or a real git ref instead of the adoption-scan empty-tree sentinel,
  and tracked deleted files in a migration-heavy worktree can still surface
  parser noise. That follow-up belongs under the same self-hosting/adoption
  hardening track before claiming full portable first-run parity.
- 2026-03-12: Tightened the same layout-governance seam around compatibility
  wrappers. `package_layout/bootstrap.py` now owns the package-local
  import/runtime bridge instead of repeating repo-root fallback logic across
  each module, and compatibility shims are now a portable validated concept:
  wrapper shape is structural, policy can require standard metadata fields, and
  crowded root/family reports can distinguish real implementation density from
  approved transitional shims.
- 2026-03-12: Extended that compatibility-shim contract into the advisory
  review layer too. `probe_compatibility_shims.py` now reuses the same
  portable shim primitive to surface stale wrapper debt
  (missing/expired metadata, broken targets, shim-heavy roots/families), and
  even the fallback `run_probe_report.py` path now resolves probe entrypoints
  from shared policy/registry state instead of carrying a second flat list by
  hand. That is the architecture we want everywhere: one engine primitive,
  repo-owned policy knobs, and thin public runners that stay aligned by
  construction.
- 2026-03-13: Burned down the remaining live `probe_single_use_helpers` debt
  in the current extraction seam. `controller_action.py`, `docs_check.py`,
  `path_audit.py`, and `runtime/control_state.py` now keep only named
  runtime/governance seams instead of one-use private wrappers, and the probe
  packet is down to one real portability signal: the oversized
  `dev/scripts/devctl` root shim population that still needs a package/repo-
  pack extraction pass rather than more local micro-cleanups.
- 2026-03-13: Consolidated the repo-grounded architecture review and full
  staged roadmap directly into this file so `MP-377` now has one main active
  plan linked from the tracker instead of relying on chat transcripts and
  overlapping docs. The explicit working stance is now: this file is the
  canonical active plan for the standalone governance product,
  `dev/active/portable_code_governance.md` remains the narrower engine
  companion, `dev/active/MASTER_PLAN.md` remains the tracker, and immediate
  execution starts with documentation consolidation plus canonical
  policy/config normalization.
- 2026-03-13: Added an explicit `Session Resume` contract to this plan so new
  AI conversations do not restart from scratch. The intended operating model is
  now: this file holds the canonical left-off state for `MP-377`, fresh AI
  sessions must read it before proceeding, and each substantive session should
  refresh both `Session Resume` and `Progress Log` before handoff.
- 2026-03-13: Hardened the repo-facing docs-governance path around this plan.
  `dev/config/devctl_repo_policy.json` now carries a policy-owned
  `tooling_doc_requirement_rules` entry that requires
  `dev/active/ai_governance_platform.md` for platform-scope tooling/policy/
  runtime/extraction changes, and `devctl docs-check` now enforces that rule
  without hardcoding VoiceTerm-only plan logic into the command.
- 2026-03-13: Audited the platform plan for context efficiency and found a real
  architecture gap: `MP-377` previously tracked rule quality, portability, and
  evidence quality, but not whether those gains required unsustainably large
  prompt/context usage. This plan now treats context as a first-class platform
  contract through `ContextPack` and `ContextBudgetPolicy`, adds completion and
  execution gates for bounded context usage, requires usage-tier guidance for
  adopters, and routes context telemetry into future `RunRecord` / event-
  history work so code-quality gains are measured against prompt cost too.
- 2026-03-13: Refactored `devctl docs-check` into
  `dev/scripts/devctl/commands/docs/` so the new canonical-plan enforcement
  path also satisfies the repo's own shape, complexity, parameter-count, and
  dict-schema guards. Validation for that slice included targeted `pytest`
  coverage plus `check_architecture_surface_sync`,
  `check_agents_bundle_render`, `docs-check --strict-tooling`, and
  `check --profile ci`.
- 2026-03-13: Clarified the platform's history model so contributors stop
  mixing session handoff with structured telemetry. The repo now says
  explicitly that `Session Resume` / `Progress Log` are the canonical restart
  surface for `MP-377`, while `devctl_events.jsonl`,
  `finding_reviews.jsonl`, watchdog episodes, and later `RunRecord`
  projections are the machine-readable runtime evidence that should feed
  metrics, optional SQLite indexing, and later ML/ranking layers.
- 2026-03-13: Tightened the operator/handoff rule around those ledgers. The
  repo now says explicitly that agents should not hand-edit command audit
  JSONL, should use `devctl` for command telemetry, should append
  `governance-review --record` rows before handoff for adjudicated findings,
  and should call out any non-`devctl` telemetry gaps in the handoff rather
  than implying complete machine coverage.
- 2026-03-13: Raised the accuracy bar in plan state. The repo now explicitly
  treats broader `--adoption-scan` audit cycles plus richer watchdog evidence
  as a prerequisite for strong platform-accuracy claims, and it now treats
  recorded false positives as rule-quality defects that need root-cause
  analysis and a narrowing/tuning follow-up rather than passive counting.
- 2026-03-13: Expanded the missing-scope list again to cover the next gaps that
  matter before DB/ML/product claims: adjudication coverage metrics, formal
  DB-ingestion/provenance contracts, privacy/redaction rules for structured
  telemetry, and measured promotion criteria for moving advisory probes into
  blocking guard tiers.
- 2026-03-13: Expanded the plan again around long-range trustworthiness gaps
  that the repo already implies but had not made explicit enough: a replayable
  cross-repo rule-quality corpus/harness for regression measurement, and one
  waiver/suppression lifecycle so false positives are narrowed instead of
  quietly converted into permanent exceptions.
- 2026-03-13: Tightened the plan's closure bar and language strategy. `MP-377`
  now says this product is not "done" until architecture, pipeline, telemetry,
  and reviewed-evidence trust are all proven together; it also now makes
  continued Python/Rust pattern mining a standing workstream and defines future
  language support as one shared analyzer-contract problem, not a series of
  repo-specific bolt-ons.
- 2026-03-17: Sequenced that same governance-quality-feedback / knowledge-base
  direction explicitly behind the current `P0` freeze work instead of letting
  it compete with the platform spine. The next coding slice is not "build the
  whole knowledge base now"; it is to close the first real defects exposed by
  the attempted implementation: wire the new surface into the real `devctl`
  command/catalog/artifact path, fix per-check scoring identity to key by
  `(check_id, signal_type)`, stop preserving top-level compatibility drift in
  the canonical `ReviewState` payload, make Halstead snapshot paths portable,
  and add dedicated tests for the new quality-feedback package. Treat the
  broader knowledge-base / topic-chapter / ConceptIndex layer as a later `P1`
  consumer of the `P0` contract/evidence spine, not as permission to bypass
  that spine.
- 2026-03-13: Cleared the immediate scope-loss risk for fresh AI sessions by
  staging `dev/active/ai_governance_platform.md` and
  `dev/guides/AI_GOVERNANCE_PLATFORM.md` in git, then updated `Session Resume`
  so the next conversation can begin directly from Phase 2 / runtime-evidence
  work instead of re-litigating whether the canonical plan is preserved.
- 2026-03-13: Validated the current multi-agent execution path before starting
  Phase 2 work. The bridge-gated dry-run command
  `python3 dev/scripts/devctl.py review-channel --action launch --terminal none --dry-run --format md --refresh-bridge-heartbeat-if-stale`
  passed on the active tree, refreshed `bridge.md`, and confirmed that the
  repo can still launch the planned 8 Codex reviewer lanes plus 8 Claude coder
  lanes from repo-owned state. That means `MP-377` implementation can use the
  existing reviewer/coder system now, while still treating peer-liveness,
  stale-peer recovery, and full hands-off proof as open `MP-358` closure work
  rather than assumed product completeness.
- 2026-03-13: Turned the machine-first output rule into concrete self-hosting
  behavior for the moved governance package. `governance-bootstrap`,
  `governance-export`, `governance-review`, and `render-surfaces` now share a
  package-local output/error helper that treats JSON as the canonical machine
  payload and markdown as the human projection; a new dispatch-level CLI test
  proves parser + `COMMAND_HANDLERS` + JSON output stability across the moved
  governance family; and `check_architecture_surface_sync.py` now resolves
  aliased nested command imports so package-owned command modules are enforced
  correctly instead of being judged by flat-root-only expectations.
- 2026-03-13: Audited the next machine-output step before changing the shared
  helper again. The current `--output` path already avoids full stdout JSON
  dumps because `write_output()` writes the artifact and prints only `Report
  saved to: ...`; the real platform gap is that the receipt is human prose and
  the runtime/data-science stack still does not measure artifact bytes,
  hashes, or estimated tokens. The next slice should add a dedicated
  machine-artifact emitter plus artifact-cost telemetry for JSON-canonical
  surfaces instead of globally forcing every human-oriented `devctl` command
  through the same control-channel contract.
- 2026-03-13: Implemented the first machine-artifact emission slice. The new
  shared machine-output path now powers `governance-*`,
  `platform-contracts`, `probe-report`, `data-science`, and `loop-packet`
  when they emit JSON: `--format json --output ...` writes one compact JSON
  artifact file plus a compact JSON receipt on stdout instead of the old human
  `Report saved to:` string, and `devctl_events` / `data-science` now record
  artifact path/hash/byte/token metrics (including stdout receipt size) so the
  repo can compare context cost against fix quality over time.
- 2026-03-13: Finished the first generated-surface integration pass so the new
  repo-pack surface layer is no longer just files on disk. `render-surfaces`
  is now reachable from the public CLI and `devctl list`, the parser/command
  code moved under governance-owned namespaces instead of adding more crowded
  flat-root modules, and the paired
  `check_instruction_surface_sync.py` guard now runs in
  tooling/release governance bundles and workflows.
- 2026-03-13: Completed the broader repo-pack surface-generation wiring around
  that first pass. `dev/config/devctl_repo_policy.json` now owns
  `repo_governance.surface_generation` for repo-pack metadata, shared template
  context, and governed outputs; portable starter policy/bootstrap flows seed
  the same contract for adopter repos; maintainer docs now document
  `render-surfaces`; and focused regression coverage protects the new parser,
  docs-check messaging, starter-policy generation, and surface reports.
- 2026-03-13: Hardened that Phase 2 generated-surface contract for real
  day-to-day use. `render-surfaces` now treats missing local-only outputs as a
  non-failing report state while keeping `--write` as the explicit materialize
  path, portable starter bootstrap now points adopters at
  `render-surfaces --write`, the durable architecture guide now names the
  generated instruction/starter assets directly, and the focused test surface
  covers both the repo-local report semantics and the bootstrap next-step
  contract.
- 2026-03-13: Re-ran the self-hosting governance proof path after the
  concurrent layout/integration edits settled. These commands passed on the
  current tree under the repo-required Python 3.11 interpreter:
  `devctl render-surfaces --format md`,
  `check_instruction_surface_sync.py`,
  `check_package_layout.py`,
  `check_architecture_surface_sync.py`,
  `check_bundle_workflow_parity.py`,
  `check_guard_enforcement_inventory.py`,
  `check_bundle_registry_dry.py`,
  `pytest dev/scripts/devctl/tests/governance/test_render_surfaces.py dev/scripts/devctl/tests/test_bundle_registry.py dev/scripts/devctl/tests/test_script_catalog.py`,
  `devctl docs-check --strict-tooling`,
  `check_active_plan_sync.py`,
  `check_multi_agent_sync.py`,
  `devctl hygiene --strict-warnings`,
  and elevated `devctl process-cleanup --verify --format md`. The broader
  `devctl check --profile ci` lane still fails, but the remaining red is now
  outside this generated-surface/layout slice: pre-existing shape and
  dict-schema debt in `dev/scripts/devctl/governance/bootstrap_policy.py` and
  `dev/scripts/devctl/governance/surfaces.py`.
- 2026-03-13: Concurrent namespace work briefly re-broke the focused
  generated-surface regression path after that validation snapshot. The active
  runtime helper path is now `dev/scripts/devctl/governance/surface_runtime.py`
  (no separate `surfaces_runtime.py` remains in the current tree), its
  `check_agents_bundle_render` import now resolves package-style pytest runs
  without relying on a flat-root `checks` module, the public guard runner now
  lives at `dev/scripts/checks/check_instruction_surface_sync.py`,
  and the docs-check strict-tooling fixture now points at
  `dev/scripts/devctl/commands/governance/render_surfaces.py` instead of the
  old flat command path. Re-run the focused governance tests before trusting
  any older "targeted pytest passed" note from this date.
- 2026-03-13: Revalidated the same slice again after a larger concurrent
  modularization wave touched much of `dev/scripts/**`. The important nuance
  is now explicit for future sessions: `check_package_layout.py` is green
  because the new generated-surface/governance files are placed correctly and
  the self-hosting rules are blocking new flat-root growth there, but the repo
  still carries freeze-mode crowding in `dev/scripts/checks`,
  `dev/scripts/devctl`, `dev/scripts/devctl/commands`, and
  `dev/scripts/devctl/tests`. The next structural follow-up is therefore not
  more generated-surface wiring; it is continued decomposition of those
  crowded roots while the Phase 2 context-budget/runtime work moves forward.
- 2026-03-13: Fixed a concurrent registry/docs/workflow drift that had pointed
  the generated-surface sync guard at
  `dev/scripts/checks/package_layout/check_instruction_surface_sync.py`.
  Restored the stable public root shim at
  `dev/scripts/checks/check_instruction_surface_sync.py`, kept the
  package-local implementation under `dev/scripts/checks/package_layout/`,
  resynced bundle/workflow/docs/test references, and revalidated with
  `check_instruction_surface_sync.py`, `check_package_layout.py`,
  `check_agents_bundle_render.py`, `check_bundle_workflow_parity.py`,
  `devctl render-surfaces --format md`, `devctl docs-check --strict-tooling`,
  and focused `pytest` over `test_governance_bootstrap.py`,
  `test_render_surfaces.py`, `test_docs_check.py`, and
  `test_check_guard_enforcement_inventory.py`.
- 2026-03-13: Closed the Phase 2 repo-pack surface-generation slice on a green
  self-hosting validation bundle. Portable governance onboarding docs/templates
  now explicitly tell adopters to tighten
  `repo_governance.surface_generation.*` and run
  `python3 dev/scripts/devctl.py render-surfaces --write --format md`, the
  final parameter-count regression in `bootstrap_surfaces.py` was resolved via
  a typed `SurfaceSeed` wrapper, and these end-of-session gates passed on the
  final tree: `devctl check --profile ci`, `devctl docs-check --strict-tooling`,
  `check_active_plan_sync.py`, `check_agents_bundle_render.py --format md`,
  `check_multi_agent_sync.py`, `check_instruction_surface_sync.py --format md`,
  and `check_package_layout.py`. The remaining probe output is advisory only:
  `surface_runtime.py` still carries medium design-smell hints and the broader
  `dev/scripts/devctl` compatibility-shim backlog remains active platform debt.
- 2026-03-13: Started burning down the crowded flat-root governance family
  under `dev/scripts/devctl/commands/` and `dev/scripts/devctl/tests/`.
  `governance-bootstrap`, `governance-export`, and `governance-review` now
  live under `dev/scripts/devctl/commands/governance/`, their focused tests now
  live under `dev/scripts/devctl/tests/governance/`, and
  `dev.scripts.devctl.commands` re-exports the governance modules so repo
  package imports can stay stable without keeping more `governance_*` files in
  the crowded command root.
- 2026-03-13: Validated a consolidated multi-agent gap synthesis against the
  active `MP-377` plan and current repo state. Confirmed that context-budget
  contracts, the finding/review/metric evidence schema, the replayable
  evaluation harness, the promotion/demotion rubric, and the
  waiver/suppression lifecycle were already acknowledged as platform gaps but
  still lived mostly in checklist or narrative form instead of the phase
  roadmap. Promoted those into explicit phase scope, added the missing package
  install surface (`pyproject.toml`, build backend, CLI entrypoint),
  repo-pack-owned path-resolution contract (`RepoPathConfig`), repo-pack /
  platform compatibility requirement, expanded adapter/frontend file lists, and
  added pilot-proof expectations for compatibility and public differentiation
  so extraction does not run ahead of the supporting contracts.
- 2026-03-14: Closed the next instruction-surface governance gap for cross-AI
  portability. The generated `claude_instructions` repo-pack surface now
  carries explicit blocking post-edit verification language, repo policy can
  declare required rendered snippets, `render-surfaces` /
  `check_instruction_surface_sync` fail when those semantics disappear, and the
  governance tests now pin the VoiceTerm-specific done criteria (`bundle.*`
  routing plus `check --profile ci`) so Claude-facing local instructions do
  not silently collapse back into a non-binding command list.
- 2026-03-14: Accepted the next MP-377 command/runtime boundary cuts after
  focused validation. `mobile_status.py` now reads review status through
  `repo_packs.review_helpers.load_mobile_review_state()` instead of importing
  `review_channel.events`, `review_channel.event_store`, or
  `review_channel.state` directly, and the narrow `controller_action.py` /
  `triage_loop.py` checks-layer reroute now uses devctl-owned
  `process_helpers.resolve_repo` / `run_capture` instead of reaching into
  `checks.coderabbit_ralph_loop_core`. That closes the current command-layer
  fit-gap without forcing a larger controller redesign in the same slice and
  moves the next extraction target to governance evidence path ownership plus
  autonomy default-profile ownership.
- 2026-03-29: Closed the bounded MP-377 review-channel authority slice for
  semantic implementer ACK handling. The live path now shares one ACK parser,
  one validator contract, and one implementer prompt contract, bridge-backed
  `current_session` is the authoritative typed source for instruction/ACK
  machine state, `bridge-poll` re-reads the refreshed typed `review_state`
  snapshot before deciding current ACK freshness, and compatibility bridge
  rerendering now prefers typed current-session fields over raw bridge prose
  for machine-deciding live sections. Focused validation is green:
  `python3 -m pytest dev/scripts/devctl/tests/review_channel/test_ack_contract.py -q --tb=short`,
  `python3 -m pytest dev/scripts/devctl/tests/review_channel/test_current_session_projection.py -q --tb=short`,
  `python3 -m pytest dev/scripts/devctl/tests/review_channel/test_bridge_poll.py -q --tb=short`,
  and `python3 -m pytest dev/scripts/devctl/tests/review_channel/test_bridge_render.py -q --tb=short`.
  Remaining follow-up stays explicit here: the broader writer-authority cutover
  still needs typed reviewer-owned prose / wait-reason state and the planned
  `DecisionTrace` chain so bridge markdown can shrink to projection/handoff
  only instead of still hosting some reviewer-authored narrative fields.
- 2026-04-03: Added the maintained reference-only proof ledger at
  `dev/audits/AI_GOVERNANCE_PLATFORM_PROOF_LEDGER.md` so the repo has
  one current answer to "what is proved now, what is still open, what
  cross-repo evidence exists, and how does this differ from the market?"
  without turning transient chat analysis into shadow authority. The ledger is
  intentionally an index over repo-owned artifacts and typed/runtime surfaces
  rather than a second roadmap: it points at `startup-context`,
  `review-channel doctor`, governance-review/data-science/probe summaries,
  external pilot ledgers, and the owning `MP-377` / `MP-376` plans, and it
  carries an explicit upkeep rule to update the same change whenever proof
  claims, commands, or artifact owners move.
- 2026-04-03: Added the generated `devctl system-picture` reducer as the
  command-level source for that ledger so the proof surface can be refreshed
  from typed runtime/evidence artifacts and not only by hand-editing prose.
  The command now owns the bounded machine snapshot plus the tracked
  writeback projection into `dev/audits/AI_GOVERNANCE_PLATFORM_PROOF_LEDGER.md`.

## Audit Evidence

- 2026-04-18 consolidation-plan authoring validation:
  `python3 dev/scripts/devctl.py docs-check --strict-tooling --format md`
  (pass),
  `python3 dev/scripts/checks/check_active_plan_sync.py` (pass), and
  `python3 dev/scripts/devctl.py check-router --execute --keep-going --format md`
  (tooling lane surfaced pre-existing runtime-authority failures in
  `check_review_channel_bridge`, `check_startup_authority_contract`, and
  `check_tandem_consistency`; the new plan-doc edits themselves stayed green
  on the doc-authority and active-plan sync gates).
- Local shared-worktree research companions (reference-only, non-authoritative,
  when present): `GUARD_AUDIT_FINDINGS.md` is the focused guard-audit /
  sequencing synthesis, and `ZGRAPH_RESEARCH_EVIDENCE.md` is the expanded
  supporting evidence set covering ZGraph applications, AI context-injection
  gaps, operator-console ideas, Rust/product surfaces, CI/test/config
  integrations, AGENTS/memory conversion ideas, and related proof chains.
  They are useful implementation/review companions in this workspace, but the
  tracked plan chain remains the canonical execution authority.
- Maintained platform proof index (reference-only, non-authoritative):
  `dev/audits/AI_GOVERNANCE_PLATFORM_PROOF_LEDGER.md` collects the
  current self-hosting POC boundary, market comparison, cross-repo pilot proof
  links, validation commands, and canonical artifact/ledger map in one place.
  Update it when proof claims materially change, but keep accepted execution
  decisions promoted into this plan, `MASTER_PLAN`, and the companion portable
  adoption plan instead of treating the ledger as a second tracker.
- `dev/scripts/checks/package_layout/shim_validation.py`
- `dev/scripts/checks/package_layout/directory_crowding.py`
- `dev/scripts/devctl/tests/checks/package_layout/test_rules.py`
- `dev/scripts/devctl/tests/checks/package_layout/test_support.py`
- `dev/scripts/devctl/governance/push_publication.py`
- `dev/scripts/devctl/runtime/startup_push_decision.py`
- `dev/scripts/devctl/review_channel/state.py`
- `dev/scripts/devctl/platform/contracts.py`
- `dev/scripts/devctl/platform/blueprint.py`
- `dev/scripts/devctl/platform/parser.py`
- `dev/scripts/devctl/commands/platform_contracts.py`
- `dev/scripts/devctl/repo_packs/voiceterm.py`
- `dev/scripts/devctl/runtime/control_state.py`
- `dev/scripts/devctl/runtime/action_contracts.py`
- `dev/scripts/devctl/runtime/dogfood_models.py`
- `dev/scripts/devctl/runtime/dogfood_log.py`
- `dev/scripts/devctl/runtime/dogfood_render.py`
- `dev/scripts/devctl/runtime/dogfood_governance.py`
- `dev/scripts/devctl/runtime/review_state.py`
- `dev/scripts/devctl/governance/live_run_import.py`
- `dev/scripts/devctl/governance/parser.py`
- `dev/scripts/checks/startup_authority_contract/runtime_import_git.py`
- `dev/scripts/checks/startup_authority_contract/runtime_import_atomicity.py`
- `dev/scripts/devctl/commands/reporting/dogfood.py`
- `dev/scripts/devctl/commands/governance/import_findings.py`
- `dev/scripts/devctl/commands/vcs/push.py`
- `dev/scripts/devctl/tests/commands/reporting/test_dogfood.py`
- `dev/scripts/devctl/tests/governance/test_governance_import_findings.py`
- `dev/scripts/devctl/tests/checks/test_startup_authority_contract.py`
- `dev/scripts/devctl/tests/vcs/test_push.py`
- `dev/scripts/checks/check_platform_layer_boundaries.py`
- `dev/scripts/checks/check_architecture_surface_sync.py`
- `dev/scripts/checks/architecture_boundary/command.py`
- `dev/scripts/checks/check_test_coverage_parity.py`
- `dev/scripts/devctl/common.py`
- `dev/scripts/devctl/controller_action_support.py`
- `dev/scripts/devctl/mobile_status_views.py`
- `dev/scripts/devctl/commands/mobile_status.py`
- `dev/scripts/devctl/commands/controller_action.py`
- `dev/scripts/devctl/commands/triage_loop.py`
- `dev/scripts/devctl/repo_packs/review_helpers.py`
- `dev/scripts/devctl/governance_review_log.py`
- `dev/scripts/devctl/governance/external_findings_log.py`
- `dev/scripts/devctl/data_science/metrics.py`
- `dev/scripts/devctl/autonomy/run_parser.py`
- `dev/scripts/devctl/review_channel/core.py`
- `dev/scripts/devctl/review_channel/state.py`
- `dev/scripts/devctl/tests/test_action_contracts.py`
- `dev/scripts/devctl/tests/test_controller_action.py`
- `dev/scripts/devctl/tests/test_check_architecture_surface_sync.py`
- `dev/scripts/devctl/tests/checks/architecture_boundary/test_check_platform_layer_boundaries.py`
- `dev/scripts/devctl/tests/checks/package_layout/test_rules.py`
- `dev/scripts/devctl/tests/test_check_router.py`
- `dev/scripts/devctl/tests/test_check_test_coverage_parity.py`
- `dev/scripts/devctl/tests/test_common.py`
- `app/operator_console/state/review/review_state.py`
- `app/operator_console/state/snapshots/snapshot_builder.py`
- `app/operator_console/state/sessions/session_builder.py`
- `app/operator_console/state/sessions/session_builder_support.py`
- `app/operator_console/collaboration/conversation_state.py`
- `app/operator_console/collaboration/task_board_state.py`
- `app/operator_console/state/snapshots/phone_status_snapshot.py`
- `app/operator_console/workflows/workflow_presets.py`
- `dev/active/portable_code_governance.md`
- `dev/active/autonomous_control_plane.md`
- `dev/active/operator_console.md`
- `dev/active/ralph_guardrail_control_plane.md`
- `dev/guides/AI_GOVERNANCE_PLATFORM.md`
- `dev/guides/DEVELOPMENT.md`
- `dev/guides/PORTABLE_CODE_GOVERNANCE.md`
- `dev/audits/METRICS_SCHEMA.md`
- `dev/scripts/README.md`
- `AGENTS.md`
- `dev/active/MASTER_PLAN.md`
- `dev/active/INDEX.md`
- `dev/config/devctl_repo_policy.json`
- `dev/config/templates/claude_instructions.template.md`
- `dev/scripts/devctl/commands/docs_check.py`
- `dev/scripts/devctl/commands/docs_check_policy.py`
- `dev/scripts/devctl/commands/docs_check_render.py`
- `dev/scripts/devctl/commands/docs/check_runtime.py`
- `dev/scripts/devctl/commands/docs/policy_defaults.py`
- `dev/scripts/devctl/commands/docs/policy_runtime.py`
- `dev/scripts/devctl/commands/docs/render_sections.py`
- `dev/scripts/devctl/commands/governance/render_surfaces.py`
- `dev/scripts/devctl/governance/parser.py`
- `dev/scripts/devctl/governance/bootstrap_surfaces.py`
- `dev/scripts/devctl/governance/surfaces.py`
- `dev/scripts/devctl/governance/surface_runtime.py`
- `dev/scripts/checks/check_instruction_surface_sync.py`
- `dev/scripts/checks/package_layout/instruction_surface_sync.py`
- `dev/scripts/devctl/commands/governance/bootstrap.py`
- `dev/scripts/devctl/commands/governance/export.py`
- `dev/scripts/devctl/commands/governance/review.py`
- `dev/scripts/devctl/tests/governance/test_governance_bootstrap.py`
- `dev/scripts/devctl/tests/governance/test_governance_export.py`
- `dev/scripts/devctl/tests/governance/test_governance_review.py`
- `dev/config/templates/portable_governance_repo_setup.template.md`
- `dev/scripts/devctl/tests/governance/test_render_surfaces.py`
- `dev/scripts/devctl/tests/test_docs_check.py`
- `dev/scripts/devctl/tests/test_docs_check_constants.py`
- `dev/scripts/devctl/tests/quality_policy/test_quality_policy.py`
