# Continuous Codex/Claude Swarm Plan

Status: execution mirrored in `dev/active/MASTER_PLAN.md` (MP-358)
Execution plan contract: required
Owner lane: Review-control/continuous automation

## Scope

Build a local-first, self-sustaining Codex-reviewer / Claude-coder loop in this
repo before attempting any reusable template extraction.

This plan covers:

1. The current `devctl review-channel --action launch` bootstrap path and the
   follow-on loop behavior needed so the launched conductors keep working
   through scoped plan items instead of stopping after one accepted slice.
2. Modularization and clean-code hardening of the Python launcher/orchestration
   path: smaller modules, explicit names, clear docstrings, sparse comments
   only where they add value, and regression tests for failure paths.
3. Peer-liveness guardrails so Claude does not continue coding when Codex is no
   longer actively reviewing, and Codex does not keep issuing new review/fix
   cycles against a stale Claude session.
4. Context-rotation handoff behavior: when either conductor drops below the
   configured remaining-context threshold, both sides finish the current atomic
   step, write current state into the markdown bridge plus handoff artifacts,
   launch fresh terminals, and only then retire the old terminals.
5. Host-process hygiene for all of the above so stale launcher/test sessions do
   not accumulate detached `voiceterm-*` or repo-tooling process trees.
6. A later portable-template phase, but only after the local VoiceTerm loop is
   proven stable end-to-end on this codebase.

Out of scope until the local proof gate is green:

1. Generalized extraction of the current launcher into a cross-repo kit.
2. Provider-first support beyond Codex and Claude.
3. Hidden memory-only handoff or true shared free-form writes into one live
   terminal.

## Locked Decisions

1. Local proof comes first. Do not template the current loop before it works
   here with minimal operator babysitting.
2. `dev/active/MASTER_PLAN.md` remains the canonical task tracker and
   `code_audit.md` remains the current-state bridge while the markdown path is
   active.
3. The continuous loop must keep going while scoped work remains:
   current blockers first, then the next unchecked scoped plan item, then the
   next declared scoped task in `MASTER_PLAN`.
4. Field reports that are not currently reproducible still stay in scope as
   regression-hardening requirements until they are either re-reproduced and
   fixed or proved obsolete with tests/guards.
5. Peer freshness is mandatory before a new handoff cycle starts:
   Claude must not claim new coding work from a stale Codex review state, and
   Codex must not keep posting fresh fix requests to a stale Claude lane.
6. Use the current poll contract as the base behavior:
   Codex reviews the non-audit tree every 2-3 minutes while code is moving and
   emits operator-visible heartbeats every 5 minutes.
7. Context rotation triggers when estimated remaining context drops below 50%.
   The current atomic step must finish first, then the handoff write/launch/ack
   sequence runs, then the old terminals exit.
8. Old terminals never close until the fresh conductor sessions acknowledge the
   handoff in repo-visible state.
9. Any later template extraction must be carved from a modular, repo-proven
   core/profile boundary rather than from the current hardcoded VoiceTerm path.

## Cross-Plan Dependencies

1. `dev/active/review_channel.md` owns the review-channel bridge/state model,
   conductor ownership rules, and shared-screen direction for MP-355.
2. `dev/active/autonomous_control_plane.md` owns the broader controller-state,
   continuous-run, learning-loop, and staged template-extraction direction for
   MP-340.
3. `dev/active/host_process_hygiene.md` owns the required host cleanup/audit
   guarantees for stale local sessions, detached test helpers, and post-run
   verification.
4. `dev/active/memory_studio.md` owns `session_handoff`, `handoff_pack`, and
   `survival_index` semantics used to survive compaction/restart boundaries.
5. `AGENTS.md`, `dev/scripts/README.md`, and `dev/guides/DEVCTL_AUTOGUIDE.md`
   remain the policy/docs authority for command usage and guard expectations.

## Execution Checklist

### Phase 0 - Contract And Diagnostics

- [x] Freeze the initial local-first operating contract for this loop:
      task promotion order, the 50% context-rotation threshold, and
      terminal-rotation ACK rules.
- [ ] Extend that contract with explicit peer-heartbeat state names and
      stale-peer handling so implementation does not invent them ad hoc.
- [ ] Classify current issues into:
      `verified-current`, `field-report-intermittent`, or `obsolete`.
- [x] Record the current report-level stale-peer freshness threshold and
      bridge state names so implementation does not invent them ad hoc:
      `fresh | stale | waiting_on_peer`, with the Codex poll considered
      stale after 600 seconds without a new reviewer heartbeat.
- [x] Define the minimum repo-visible handoff payload:
      current blocker set, next action, reviewed worktree hash, owned lanes,
      current atomic step, and launch ACK state. Landed in
      `review_channel_handoff.py` as structured `resume_state` output inside
      the rollover handoff bundle (`handoff.json` + `handoff.md`), with
      review-channel regression coverage.

### Phase 1 - Launcher And Code-Quality Hardening

- [x] Modularize the current review-channel launcher/orchestration helpers into
      smaller files with explicit names and single responsibilities.
- [x] Guarantee structured report output on failure paths as well as success
      paths for `review-channel --action launch`.
- [x] Add/refresh unit coverage for:
      dry-run success, inactive bridge, and failure-before-launch report
      rendering.
- [x] Add the remaining launch regression coverage for:
      missing CLI and terminal-profile fallback warnings.
- [ ] Keep docstrings/comments/variable names simple and explicit; remove mixed
      responsibilities and duplicated path/prompt logic where possible.

### Phase 2 - Continuous Loop Behavior

- [ ] Implement automatic next-task promotion so the conductor does not stop
      after one accepted slice while scoped work still exists.
- [ ] Add peer-liveness guards:
      Claude cannot start new coding work on stale Codex review state, and
      Codex cannot keep issuing new fix cycles on stale Claude state.
- [ ] Define and implement the stale-peer recovery path:
      mark the bridge as waiting on peer, relaunch or re-seed the missing side,
      and resume from the last confirmed bridge state.
- [ ] Ensure the loop uses one master document chain:
      `MASTER_PLAN` -> relevant active-plan checklist -> `code_audit.md`
      current-state bridge.

### Phase 3 - Context Rotation And Handoff

- [ ] Add a remaining-context estimator that is conservative and repo-visible.
- [x] Land the initial repo-visible rollover path for the 50% threshold:
      write bridge + handoff artifacts, surface the exact fresh-session ACK
      lines, and allow the launcher to wait for visible ACK before the
      retiring session exits.
- [ ] Auto-trigger the rollover flow when remaining context drops below 50%
      instead of relying on conductor judgment to invoke `--action rollover`.
- [ ] Persist the handoff state through repo-visible artifacts only; no hidden
      session-memory dependence is allowed.
- [ ] Verify old sessions and test helpers do not leave stale repo-related host
      processes after rotation or guard-driven relaunch.

### Phase 4 - Local Proof And Template Gate

- [ ] Prove the loop can continue across multiple scoped tasks with no manual
      restart and no lost blocker/next-action state.
- [ ] Capture proof evidence for:
      next-task promotion, stale-peer pause/recovery, context rotation, and
      post-rotation host cleanliness.
- [ ] Only after the local proof is green, open the reusable-template
      extraction tranche and carve it from the proven modular core/profile
      boundary rather than the current repo-hardcoded path.

## Progress Log

- 2026-03-09: Closed the next launcher self-heal gap exposed by live Operator
  Console use. `review-channel --action launch` and `--action rollover` now
  accept `--refresh-bridge-heartbeat-if-stale`, which refreshes the
  markdown-bridge reviewer heartbeat metadata plus the non-audit worktree hash
  through a typed repo-owned path when stale/missing heartbeat metadata is the
  only launch blocker. Real bridge corruption or missing live launch state
  (`Claude Ack`, `Last Reviewed Scope`, idle next action, missing headings,
  etc.) still fail closed. This narrows the old “five-minute heartbeat aged
  out so the launcher just dies” operator path without pretending stale-peer
  recovery is solved.
- 2026-03-09: Closed the two follow-ups from the latest live proof without
  overstating the remaining work. Host hygiene/process audit now classifies
  attached review-channel conductor trees under a dedicated
  `review_channel_conductor` scope so intentionally supervised Codex/Claude
  sessions stay visible in reports but no longer trip stale-process failures at
  the 600-second threshold; detached/backgrounded conductor trees still fail
  strict audit/cleanup as leaked repo processes. The bridge path also now has a
  typed repo-owned `review-channel --action promote` command plus status
  projection support for the derived next unchecked checklist item from the
  configured active plan. This closes the old “manual next instruction only”
  gap, but full end-to-end automatic promotion proof is still open because the
  conductors must still invoke the typed promotion path at the right boundary
  and stale-peer recovery remains unfinished.
- 2026-03-09: The live proof exposed a real host-hygiene mismatch that remains
  open under MP-358. `devctl hygiene --strict-warnings` still treats active
  review-channel conductors as stale repo-related processes once they have been
  running for 600 seconds, even when the supervised Codex/Claude sessions are
  intentionally alive and still writing to the session logs. The cleanup/audit
  path must learn to distinguish deliberate long-running conductors from leaked
  repo helpers before the continuous loop can be called host-hygiene clean.
- 2026-03-09: Ran a real local launcher proof on the dirty tree after landing
  the anti-stall supervision slice. `check_review_channel_bridge.py` had to be
  refreshed back to green with a current `Last Codex poll`, then
  `review-channel --action launch --terminal terminal-app` opened both
  supervised conductor sessions and wrote fresh session artifacts under
  `dev/reports/review_channel/latest/sessions/`. A timed follow-up showed both
  log files still growing while the corresponding Codex/Claude provider
  processes remained alive. This is useful evidence that the launcher no longer
  drops the terminals immediately after bootstrap, but it is still only partial
  proof because the queue did not yet demonstrate a full automatic next-task
  promotion cycle.
- 2026-03-09: Landed the first launcher-side anti-stall supervision slice for
  MP-358. Generated `review-channel --action launch` scripts now relaunch the
  same Codex/Claude conductor in-place when the provider exits cleanly, log an
  explicit restart notice in the terminal transcript, and still stop
  fail-closed on non-zero exits so auth/CLI failures stay visible instead of
  spinning forever. The bootstrap prompt now also states the missing liveness
  contract directly: `waiting_on_peer` is a live polling state, not terminal,
  bridge summaries are never permission to exit, Codex must promote the next
  scoped plan item after Claude lands a slice, and Claude must keep polling for
  the next instruction instead of quitting after posting one summary. This
  narrows the field-reported “both conductors stopped after a summary” failure,
  but automatic next-task promotion is still not proven end-to-end because the
  tool still depends on provider compliance rather than an explicit repo-owned
  queue executor.
- 2026-03-09: Re-reviewed MP-358 after the latest bridge-hardening tranche.
  The loop now records explicit `fresh | stale | waiting_on_peer` liveness and
  rejects zero-second ACK waits fail-closed, but the launcher still does not
  prove the full bridge guard before bootstrap, the 2-3 minute poll /
  five-minute heartbeat contract is not fully enforced end-to-end, automatic
  next-task promotion is still conductor discipline rather than a finished tool
  contract, and stale-peer recovery remains open. Keep the local loop in
  reviewer-driven continuous mode until those gaps and the remaining host-
  cleanliness follow-ups are closed.
- 2026-03-09: Closed the minimum repo-visible handoff-payload contract for
  MP-358. `review-channel --action rollover` now writes a structured
  `resume_state` block into the repo-visible handoff bundle with current
  blockers, next action, reviewed non-audit worktree hash, grouped Codex /
  Claude owned lanes, the current atomic step, and the required launch ACK
  lines marked pending until the fresh conductors acknowledge them. Focused
  review-channel regression coverage now asserts the new handoff contract in
  both JSON and markdown artifacts so the rollover path stays repo-visible and
  deterministic instead of relying on hidden session state.
- 2026-03-09: Tightened the report-only peer-freshness slice without widening
  into auto-recovery. The launcher/handoff path now treats missing Claude
  status as part of `waiting_on_peer`, the generated conductor prompt includes
  `open_findings_present` plus `claude_status_present` alongside the existing
  bridge liveness fields, and the review-channel regression suite now covers
  the machine-readable liveness reduction, missing-provider-CLI failure, and
  missing Terminal.app profile warning paths. This records the current
  report-level state contract explicitly: `fresh | stale | waiting_on_peer`
  with the Codex poll marked stale after 600 seconds.

- 2026-03-09: Synced the MP-358 checklist to current code so execution state
  matches the repo. The initial local-first contract, launcher module split,
  structured launch/failure report path, and first repo-visible rollover +
  ACK slice are now marked as landed; stale-peer state modeling, missing-CLI /
  terminal-profile warning coverage, automatic threshold detection, and
  end-to-end proof remain open.

- 2026-03-08: Added `dev/guides/AGENT_COLLABORATION_SYSTEM.md` as a
  plain-language explainer for the live Codex/Claude collaboration model. The
  guide maps the current bridge-gated `review-channel` bootstrap, the
  `code_audit.md` conductor loop, `swarm_run`/`autonomy-swarm`/
  `autonomy-loop` layering, artifact roots, and the current-versus-planned
  boundary so operators can inspect the whole system from one doc instead of
  stitching it together from plan files and command references. It also makes
  the naming boundary explicit: swarm execution is one feature inside the
  broader collaboration system, not the name of the whole system.
- 2026-03-08: Opened MP-358 to track the local-first continuous reviewer/coder
  loop as its own execution slice instead of burying launcher, peer-liveness,
  context-rotation, and later template-extraction concerns across multiple
  docs. The immediate goal is proving the loop on VoiceTerm first; reusable
  templating stays phase-gated behind that proof.
- 2026-03-08: Rechecked the two field reports that motivated this plan before
  writing the scope. Current local state does not reproduce either one:
  `python3 dev/scripts/devctl.py review-channel --action launch --terminal none
  --dry-run --format json` returns a structured success report, and
  `python3 dev/scripts/devctl.py process-audit --strict --format md` is clean.
  Those reports therefore stay in scope as regression-hardening requirements
  until they are either re-reproduced and fixed or explicitly retired by
  targeted tests/guards.
- 2026-03-08: Landed the first anti-compaction rollover slice in the
  transitional `review-channel` launcher. Conductors now get a repo-owned
  `--action rollover` command in their bootstrap prompt, the enforced
  threshold is now 50% remaining context, rollover writes a repo-visible
  handoff bundle under `dev/reports/review_channel/rollovers/`, fresh
  conductors receive exact ACK lines they must write into `code_audit.md`, and
  the command can wait for those visible ACKs before the retiring session exits.

## Audit Evidence

- `python3 dev/scripts/checks/check_review_channel_bridge.py --format md`
  - 2026-03-09 local run after heartbeat refresh: pass
- `python3 dev/scripts/devctl.py review-channel --action launch --terminal none --dry-run --format json`
  - 2026-03-09 local run: pass
  - 2026-03-08 local run: pass
- `python3 dev/scripts/devctl.py review-channel --action launch --terminal terminal-app --format json`
  - 2026-03-09 local run: pass; live Terminal.app launch opened supervised
    Codex/Claude sessions and both session logs kept growing over a timed
    follow-up
- `python3 dev/scripts/devctl.py review-channel --action rollover --terminal none --dry-run --format json`
  - 2026-03-09 local run: pass
  - 2026-03-08 local run: pass
- `python3 -m unittest dev.scripts.devctl.tests.test_review_channel`
  - 2026-03-09 local run: pass
  - 2026-03-08 local run: pass
- `python3 dev/scripts/devctl.py docs-check --strict-tooling`
  - 2026-03-09 local run: pass
- `python3 dev/scripts/devctl.py hygiene --strict-warnings`
  - 2026-03-09 local run: expected red for two currently open issues: the
    existing publication-sync drift and active review-channel conductor
    processes being misclassified as stale once they exceed the current
    600-second host-hygiene threshold
- `python3 dev/scripts/devctl.py process-audit --strict --format md`
  - 2026-03-08 local run: pass
