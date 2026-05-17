# Guard System Audit Findings — 2026-03-21

## Status

- Canonical role: reference evidence for `MP-377` self-governance and
  authority-loop closure.
- Paired full reference: `ZGRAPH_RESEARCH_EVIDENCE.md` preserves the broader
  ZGraph/research backlog, integration maps, and later-phase product/CI/test/
  memory angles. Keep this file focused; do not delete the long-form reference.
- Scope: deterministic guard/probe blind spots confirmed against the current
  `feature/governance-quality-sweep` branch.
- Main conclusion: integrate these findings into the existing
  `ai_governance_platform` / `platform_authority_loop` sequence instead of
  starting a parallel graph-first roadmap.
- Non-goal: widen ZGraph or `context-graph` semantics before startup
  authority, repo-pack activation, typed review-state cutover, and executable
  plan mutation are closed.

## Confirmed Branch Facts

The current branch still shows these runtime-behind-docs gaps:

1. `startup_context.py` is still advisory and still falls back to parsing
   `bridge.md` when typed review-state projections are absent.
2. `active_path_config()` still silently falls back to
   `VOICETERM_PATH_CONFIG`, and `set_active_path_config()` currently has no
   non-self callers.
3. The runtime review-state layer still carries provider-shaped fields, and
   the parser still defaults a missing reviewer mode to `active_dual_agent`.
4. `ActionResult.status` documents a closed outcome set
   (`pass|fail|unknown|defer`), but `vcs.push` still emits business-state
   strings outside that domain.
5. `plan_patch_review` apply flow is still packet-state progress, not proven
   canonical plan mutation with freshness/lease enforcement.
6. `ContextGraphQueryPayload.confidence` expects `float` while
   `QueryResult.confidence` is currently `str`, and the command path passes it
   through unchanged.
7. Mypy already detects part of the current drift, but the workflow still
   keeps the tooling lane advisory with `continue-on-error: true`.

## What The Audit Got Right

The high-value part of the original scratch audit is the diagnosis, not the
temptation to widen scope too early.

### 1. Contract-Value Enforcement Is Missing

The repo has contract-shape enforcement, but not enough contract-value
enforcement.

Concrete examples:

- `ActionResult.status` claims a closed value domain while `vcs.push` emits
  values outside that set.
- `context-graph` query/result confidence fields disagree on type and still
  pass through the live command path.

This is not a "more guards" problem. It is a "typed boundaries are currently
allowed to lie" problem.

### 2. Plan-To-Runtime Parity Is Still Open

The active plans are ahead of the runtime in several places.

Concrete examples:

- `platform_authority_loop.md` says startup must not auto-enter
  `active_dual_agent` without explicit policy/operator choice, while
  `review_state_parser.py` still defaults to it.
- planning packets define valid mutation ops, but the inspected apply path
  still shows packet-state transition rather than canonical plan mutation.
- `StartupContext`, `ProjectGovernance`, and related typed surfaces exist, but
  the full `WorkIntakePacket` / `CollaborationSession` authority chain is not
  yet executable runtime state.

### 3. Authority-Source Validation Is Still Missing

The repo has the right target architecture, but the current control path still
accepts compatibility seams as live authority.

Concrete examples:

- startup still falls back to parsing `bridge.md`
- repo-pack path activation still falls back to VoiceTerm defaults
- provider-shaped fields remain in the canonical review-state middle layer

This is the main reason portability is still documented more strongly than it
is enforced.

### 4. Dead Authority Seams Need Detection

The audit was also right that exported authority seams can exist without real
runtime use.

Concrete example:

- `set_active_path_config()` is defined as the repo-pack activation hook but
  currently has no non-self callers

This should become a narrow deterministic check on exported authority seams,
not a noisy generic dead-code pass over the whole repo.

## Smarter Fix Shape

Do not solve this with one huge "mega audit" guard.

The better shape is:

1. Fix the cheapest typed-boundary truth gaps first.
2. Close the runtime authority seams those gaps expose.
3. Add a small set of narrow deterministic guards/extensions that each own one
   crisp contract.
4. Only after that, widen `system-picture`, `check_system_coherence.py`, and
   later graph/navigation reducers.

That keeps the system deterministic and keeps generated navigation layers from
masking runtime drift.

## Immediate Cheap Truth Fixes

These should land before broader graph/system-picture work:

1. Close the `ActionResult.status` domain so typed command results cannot emit
   business-state strings outside `ActionOutcome.ALL`.
2. Align `context-graph` confidence typing end-to-end.
3. Make mypy blocking for the `dev/scripts/devctl` lane instead of leaving
   known contract drift advisory-only.

These are cheap, deterministic wins and remove fake typing immediately.

## Guard Families To Add Or Tighten

Prefer narrow guards or focused extensions to existing guards over a monolith.

### Contract-Value Domain Enforcement

Purpose:

- verify that producers of typed runtime contracts emit values inside declared
  enums / literals / frozen sets

First targets:

- `ActionResult.status`
- `context-graph` query/result confidence
- later `Finding`, `DecisionPacket`, and `RunRecord` domains

Preferred implementation shape:

- either extend `check_platform_contract_closure.py` with value-domain checks
  for selected contracts, or add one narrow `check_contract_value_domains.py`
  that reads the same runtime contract catalog

### Plan-To-Runtime Parity Enforcement

Purpose:

- verify that locked decisions and declared runtime/mutation contracts are
  actually reflected in code defaults and handler registries

First targets:

- no implicit `active_dual_agent` default without policy/operator choice
- declared plan mutation ops must have executable handlers
- later `WorkIntakePacket` / `CollaborationSession` parity closure

Preferred implementation shape:

- extend the current active-plan/docs-governance path and
  `platform-contracts` surfaces rather than inventing a second plan parser

### Authority-Source Integrity Enforcement

Purpose:

- reject compatibility seams acting like hidden runtime authority

First targets:

- bridge/prose parsing on startup paths after typed projection exists
- VoiceTerm-default repo-pack/path fallback in portable startup/runtime paths
- provider-shaped review-state fields in the middle layer

Preferred implementation shape:

- one narrow authority-source guard plus focused parity tests around startup,
  repo-pack activation, and review-state parsing

### Dead Authority Seam Detection

Purpose:

- detect exported authority hooks that are never used by real runtime code

First targets:

- `set_active_path_config()`
- later other exported activation/setter seams in repo-pack/runtime authority

Preferred implementation shape:

- a narrow exported-authority usage guard, not a general-purpose dead-code
  scanner for the entire repo

## Accepted Sequencing

The accepted `MP-377` order after reviewing the branch is:

1. cheap typed-boundary truth fixes
2. startup/review/path authority closure
3. executable plan mutation plus the smallest real
   `PlanRegistry` / `PlanTargetRef` / `WorkIntakePacket` slice
4. deterministic self-governance guards for value domains, plan/runtime parity,
   authority sources, and dead authority seams
5. `system-picture` plus `check_system_coherence.py`
6. richer graph / ZGraph navigation and compression work

## ZGraph Direction

ZGraph-compatible navigation is still compatible with a deterministic system.
The key rule is the same one already accepted in `MP-377`:

- keep graph outputs generated-only
- keep canonical plan/runtime/policy/evidence pointers authoritative
- use graph layers to compress or explain scope, not to replace startup or
  runtime authority

The next problem is not richer graph meaning. The next problem is executable
authority closure.

## Expanded Research Backlog Preserved

The longer-form research backlog should stay preserved as later-phase plan
scope, not get mistaken for deleted ideas just because the immediate
authority-loop slice is narrower.

These themes remain accepted:

- semantic compressed pointers / `ConceptIndex` / ZGraph-compatible
  navigation as generated reducers over canonical refs
- long-term AI memory via topic-keyed knowledge chapters, decision shapes,
  execution traces, and bounded cross-session recall
- cross-domain graph expansion over git history, tests, CI/workflows, plan
  execution state, and governed docs
- `dev/repo_example_temp/**` pattern intake as calibration material, not as
  second authority
- typed context-injection / escalation policy instead of ad hoc prompt growth
- later workflow DAG views, smart test selection, compliance/drift audits, AI
  observability, and guard-challenge corpus generation
- governed-prose to typed-constraint extraction for surfaces such as
  `AGENTS.md` and related doc-policy/runtime contracts

The sequencing rule does not reject those ideas. It only says they must widen
after startup/path/review authority closure and the first executable intake /
plan-mutation path are real.

## Plan Integration

This audit is now intended to be tracked through:

- `AGENTS.md` source-of-truth routing
- `dev/active/MASTER_PLAN.md`
- `dev/active/ai_governance_platform.md`
- `dev/active/platform_authority_loop.md`

Those plan surfaces should carry the execution-affecting conclusions. This
file is reference evidence, not a second execution tracker.
