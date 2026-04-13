# Continuous Codex/Claude Swarm Plan

Status: execution mirrored in `dev/active/MASTER_PLAN.md` (MP-358)
Execution plan contract: required
Owner lane: Review-control/continuous automation

## Scope

Build a local-first, self-sustaining reviewer/coder loop in this repo before
attempting any reusable template extraction. The current live proof harness is
still Codex-reviewer / Claude-coder, but closure for this plan requires the
same backend to support any supported provider in reviewer, implementer, or
dashboard/operator roles without reopening a second control plane or making the
phone operator manage git/worktree mechanics directly.

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
   `bridge.md` remains the current-state bridge while the markdown path is
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
6.1 When the structured review queue is available, Claude-side repolls and
    bounded wait wakeups must consume both reviewer-owned bridge state and the
    Claude-targeted `review-channel inbox/watch` surface on the same cadence.
    The loop is not healthy if direct reviewer packets depend on user chat
    relay to become visible.
7. Context rotation triggers when estimated remaining context drops below 50%.
   The current atomic step must finish first, then the handoff write/launch/ack
   sequence runs, then the old terminals exit.
8. Old terminals never close until the fresh conductor sessions acknowledge the
   handoff in repo-visible state.
9. Any later template extraction must be carved from a modular, repo-proven
   core/profile boundary rather than from the current hardcoded VoiceTerm path.
10. The transitional markdown bridge, generated skills/docs, PyQt6 launch
    surfaces, and phone/mobile clients are all clients over the same
    repo-owned loop/backend. MP-358 may harden the conductor and launcher, but
    it may not fork task/plan authority into surface-local state.
11. Solo-developer and single-agent operation must reuse the same backend and
    validator path. The difference between "developer mode" and "agent mode"
    is an honest `reviewer_mode` value plus UI affordances, not a second
    backend or a different check stack.
12. `MP-358` is not the product boundary. This loop is one local proof harness
    inside the modular/callable platform tracked under `MP-377`, so loop work
    is only valid when it preserves or improves the shared backend/runtime/
    repo-pack boundary instead of deepening VoiceTerm-specific coupling.
13. The current local proof harness still uses Codex as the sole conductor and
    final reviewer, but that is provisional execution state, not backend law.
    Closure for this plan requires any supported provider assigned the typed
    reviewer role to own reviewer truth, next-slice promotion, and
    accept/rework decisions over the same backend contracts.
14. The current local proof harness still lets Claude fan out many bounded
    coding workers, but only behind one Claude conductor. Closure for this
    plan requires the same worker-fanout and scope guardrails to hold when the
    implementer role is assigned to another supported provider.
14.1 Worker fan-out must be plan-derived and deterministic. Conductors assign
    lanes from the active `WorkIntakePacket` / selected `PlanTargetRef` /
    `PlanExpectationPacket`, and each worker receives one bounded scope:
    role, owned target or issue cluster, owned worktree/path set, allowed
    command family, required guards, and expected evidence.
15. Every non-trivial runtime, tooling, or cross-surface slice must keep a
    separate architecture-fit reviewer lane on the Codex side. Green checks
    do not waive architecture drift; architecture-fit findings flow back
    through the Codex conductor before acceptance.
15.1 Lane-count capacity is not scope authority. An 8+8 swarm means the repo
     can host up to that many bounded lanes under the shared bridge, not that
     workers may widen into repo-wide scanning or self-assigned side quests.
16. Automated checks are necessary but not sufficient. Non-trivial runtime,
    tooling, governance, or AI-workflow changes are not closed until the
    same slice also survives the standing typed-system dogfood loop: Codex
    and Claude must discover their role and next step from typed repo-owned
    surfaces, communicate through packets/inbox/watch/ack instead of chat
    relay, and rerun the same slice after fixes until operator narration is
    no longer required beyond product intent, approval boundaries, or manual
    physical validation.

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
6. `dev/active/ai_governance_platform.md` owns the full-system modular/callable
   boundary. Any MP-358 slice that makes the loop cleaner locally but widens
   direct VoiceTerm coupling, duplicates backend logic, or creates a separate
   dev-only control plane is out of bounds.

## Execution Checklist

### Phase 0 - Contract And Diagnostics

- [x] Freeze the initial local-first operating contract for this loop:
      task promotion order, the 50% context-rotation threshold, and
      terminal-rotation ACK rules.
- [x] Extend that contract with explicit peer-heartbeat state names and
      stale-peer handling so implementation does not invent them ad hoc.
      Landed in `dev/scripts/devctl/review_channel/peer_liveness.py` as
      `CodexPollState`, `OverallLivenessState`, `AttentionStatus` StrEnums,
      `CODEX_POLL_DUE_AFTER_SECONDS` / `CODEX_POLL_STALE_AFTER_SECONDS`
      threshold constants, and `STALE_PEER_RECOVERY` contract mapping each
      attention state to its guard behavior and recovery action. All string
      literals in `handoff.py`, `state.py`, `attention.py`, and
      `status_projection.py` now import from the canonical enums.
- [x] Classify current issues into:
      `verified-current`, `field-report-intermittent`, or `obsolete`.
      Classification completed 2026-03-13 against live code, 54 passing
      review-channel tests, and verified CLI dry-runs.

      **obsolete** (fixed with code + test evidence):
      - "Five-minute heartbeat aged out so launcher just dies":
        `--refresh-bridge-heartbeat-if-stale` refreshes stale heartbeat on
        launch; real corruption still fails closed with structured error +
        recovery command.
      - "Two terminals exist masquerading as healthy loop": launcher now
        waits for `Last Codex poll` to advance after opening terminals and
        fails closed when reviewer heartbeat never appears.
      - "Host hygiene: active conductors misclassified as stale at 600s":
        `review_channel_conductor` match scope keeps supervised conductors
        visible without tripping stale-process failures; `process-audit
        --strict` shows `active_supervised_conductors` correctly.
      - "Stale-peer detection not machine-readable": `attention` contract
        in status projection provides `status`, `owner`,
        `recommended_action`, and `recommended_command` for every attention
        state. Auto-recovery is a separate Phase 2 deliverable.
      - "Launcher doesn't prove full bridge guard before bootstrap":
        launcher now requires green bridge guard before launch; fails
        closed on stale bridge with structured error.
      - "Zero-second ACK wait accepted silently": launcher rejects
        zero-second ACK waits fail-closed; default is 180 seconds.

      **field-report-intermittent** (mitigated, not fully proven):
      - "Both conductors stopped after a summary": anti-stall supervision
        (`restart-on-clean-exit`) relaunches on clean provider exit, and
        bootstrap prompt explicitly forbids exiting on summary or
        `waiting_on_peer`. Root cause (provider compliance) is
        unverifiable by repo tools alone; stays in scope as regression
        hardening per Locked Decision #4.

      **verified-current** (genuine open work in later phases):
      - Automatic next-task promotion not proven end-to-end: typed
        `--action promote` works and refuses to overwrite active
        instructions, but invocation still depends on conductor
        discipline, not a repo-owned queue executor (Phase 2).
      - Stale-peer auto-recovery: detection is machine-readable and
        recovery commands are recommended, but no automatic relaunch of
        the missing side (Phase 2).
      - 2-3 min poll / five-minute heartbeat contract not fully enforced:
        detection/reporting works via bridge guard + attention, but
        enforcement depends on provider compliance — inherent
        architectural boundary (Phase 2).
      - Context rotation not auto-triggered at 50% threshold: manual
        `--action rollover` works and produces structured handoff bundles,
        but no automatic detection of remaining context (Phase 3).
- [x] Record the current report-level stale-peer freshness threshold and
      bridge state names so implementation does not invent them ad hoc:
      `fresh | stale | waiting_on_peer`, with the Codex poll considered
      stale after 300 seconds (five-minute heartbeat window) without a new
      reviewer heartbeat and poll-due after 180 seconds (2-3 minute
      reviewer cadence). Canonical source:
      `dev/scripts/devctl/review_channel/peer_liveness.py`.
- [x] Define the minimum repo-visible handoff payload:
      current blocker set, next action, reviewed worktree hash, owned lanes,
      current atomic step, and launch ACK state. Landed in
      `dev/scripts/devctl/review_channel/handoff.py` as structured
      `resume_state` output inside
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
- [x] Keep docstrings/comments/variable names simple and explicit; remove mixed
      responsibilities and duplicated path/prompt logic where possible.
      Verified 2026-03-28: 7 oversized modules split into 14 focused modules
      (MP-377 code-shape slice). Prompt logic cleanly separated across
      prompt.py/prompt_sections.py/prompt_contract.py/prompt_guards.py.
      Path constants resolved through repo-pack config in core.py.
      attention.py priority chain reordered for correctness. No TODOs/FIXMEs
      remain. Probe findings are identifier-density advisory only.

### Phase 2 - Continuous Loop Behavior

- [x] Implement automatic next-task promotion so the conductor does not stop
      after one accepted slice while scoped work still exists.
      Landed: `--auto-promote` flag wired into launch/status actions
      (`review_channel_bridge_action_support.py`). When the bridge is in a
      promotable state (accepted verdict, clear findings, idle instruction),
      the next unchecked plan item is promoted into the bridge instruction
      automatically. End-to-end proven with 2 focused tests (`5239d88`).
- [x] Keep bridge truth synchronized when the reviewer heartbeat advances:
      `bridge.md`, `latest.md`, and `review_state.json` must move the
      reviewed hash, current verdict, open findings, plan alignment, and next
      instruction together instead of advertising a fresh heartbeat on stale
      review state or a completed task.
      Re-audited 2026-03-28: repo-owned reviewer writes already couple this
      path. `review-channel --action reviewer-checkpoint` atomically advances
      reviewed hash, verdict, findings, instruction, and `Last Codex poll`,
      while `review-channel --action promote` / instruction rewrites refresh
      the same reviewer metadata in one transform. The remaining open gap is
      not another writer primitive; it is fail-closed reviewer discipline and
      guard coverage so Codex does not bypass those repo-owned paths with raw
      `bridge.md` edits or other out-of-band reviewer-owned rewrites.
      Partial: `reviewed_hash_current` is threaded through all surfaces
      (liveness, attention, status, launch, handoff, review_state.json,
      latest.md). Heartbeat refresh no longer advances the reviewed hash
      (`8b72f30`) — only real reviews do. Auto-promote blocks on stale
      hash (`6cfb670`). `REVIEWED_HASH_STALE` attention fires with
      recovery guidance. 2026-03-22 bounded loop follow-up landed:
      active-dual-agent attention/bridge-poll now emit
      `review_follow_up_required` when implementer-owned tree changes make
      reviewer state stale under a live reviewer supervisor, so the loop stops
      looking generically "done" while Codex still owes a re-review pass.
      Full verdict/findings/instruction synchronization (making those fields
      move atomically with the hash) is still open — that requires Codex-owned
      bridge write behavior, not tool-only changes.
      Closed 2026-03-28: tool-side complete (reviewer-checkpoint atomic writes),
      guard coverage in place (REVIEW_FOLLOW_UP_REQUIRED fires on stale reviewed
      hash, check_review_channel_bridge validates metadata consistency, attention
      priority fix ensures reviewer-turn outranks checkpoint). Remaining Codex-
      side discipline gap is documented and enforced by detection, not prevention.
- [x] Keep reviewer packet visibility synchronized with the same loop contract:
      when the structured review queue is available, Claude-side
      `implementer-wait` / repoll behavior must wake on fresh Claude-targeted
      packets as well as bridge changes, and the conductor prompt/launcher
      path must require inbox/watch polling on the same cadence so direct
      reviewer packets are not lost behind bridge-only polling.
      Closed 2026-03-28: conductor prompt contract (prompt_sections.py)
      now requires inbox/watch polling on each repoll alongside bridge reads.
      `bridge-poll` returns `next_turn_role` and `review_needed` for packet-
      aware turn detection. Event-backed inbox/watch CLI actions are registered
      in the parser and will operate over the same path once the reducer lands.
- [ ] Converge reviewer-turn authority across `bridge-poll`,
      `implementer-wait`, `reviewer-wait`, `status`, `doctor`, and
      `startup-context`. The same declared `active_dual_agent` loop must not
      report `next_turn_reason=up_to_date` in one surface while typed runtime
      demotes the loop to `tools_only` / `review_loop_relaunch_required` in
      another. `bridge-poll` should consume the same launch-truth /
      `effective_reviewer_mode` / typed attention authority that
      `status`/`doctor`/`startup-context` already read instead of deciding
      liveness and turn ownership solely from bridge freshness plus
      reviewed-hash heuristics. Startup stays a consumer of this authority;
      the repair target is bridge-poll + wait parity, not a reverse startup
      dependency on bridge-poll.
- [ ] Eliminate the reviewed-current completion dead zone. When the current
      tree is already reviewed, the implementer has posted a substantive
      completion/update for the current instruction, and there is no explicit
      reviewer-owned wait/promotion state, the next turn must route back to the
      reviewer as an explicit promotion/re-review/recovery state rather than
      falling through to `up_to_date`.
- [ ] Add one typed turn-authority projection over reviewer runtime, current
      session, and queue/packet inputs before widening stale-peer automation
      again. `next_turn_role` / `next_turn_reason` should become projections
      over that shared contract instead of hand-coded branch logic split across
      `bridge-poll`, wait helpers, prompt guards, and startup consumers.
- [ ] After that shared turn-authority projection lands, migrate the remaining
      reviewer-side decision consumers that still make local liveness/recovery
      choices: launch-attention gating in `bridge_runtime_state.py`, stale-
      implementer recovery validation in `recover_support.py`, reviewer follow-
      up packet triggering in `reviewer_follow_packet_guard.py`, and auto-
      recover/rollover logic in `reviewer_follow_recovery.py`. Do not widen
      this item into producer/projection helpers that are supposed to stay
      upstream and fail-closed.
- [ ] Extend repo guards so bridge-poll parity is enforced, not just assumed.
      `check_review_surface_consistency.py` currently proves snapshot parity
      across startup/review-state/compact/commit-pipeline artifacts, but it
      does not verify that `bridge-poll` matches the same typed reviewer-
      runtime / turn-authority snapshot. Add compatible bridge-poll parity
      metadata and fail the guard when those surfaces diverge.
- [ ] Add focused parity proof for that repair path: `bridge-poll`, `status`,
      `doctor`, `implementer-wait`, `reviewer-wait`, and `startup-context`
      must all agree on reviewer-loop-not-live demotion, reviewer-owned
      follow-up after reviewed-current completion, preserved reviewer-owned
      wait states, and the allowed recovery action for that state.
- [ ] Add a repo-owned reviewer liveness emitter so inactive modes stay
      current without faking review truth. `reviewer-heartbeat` and
      `reviewer-checkpoint` are now separate writes, but the loop still lacks
      a persistent timer/daemon/session-owned caller that keeps
      `single_agent`, `tools_only`, `paused`, and `offline` visibly alive
      without manual refreshes.
- [ ] Expose one thin mode switch over the shared backend instead of a dev-only
      fork. Human-facing controls may offer `agents` / `developer` shorthands
      and later PyQt6/phone toggles, but they must normalize onto the same
      canonical reviewer-mode contract and routed validation path.
- [x] Add peer-liveness guards:
      Claude cannot start new coding work on stale Codex review state, and
      Codex cannot keep issuing new fix cycles on stale Claude state.
      Landed: `_run_bridge_action` now checks `guard_behavior: block_launch`
      from the `STALE_PEER_RECOVERY` contract and refuses to open sessions
      when reviewer heartbeat is missing or stale (`b2e2101`).
- [ ] Define and implement the stale-peer recovery path:
      mark the bridge as waiting on peer, relaunch or re-seed the missing side,
      and resume from the last confirmed bridge state.
      Partial: `WAITING_ON_PEER` and `block_launch` are now enforced.
      `--refresh-bridge-heartbeat-if-stale` is the bounded recovery path for
      stale heartbeats. `STALE_PEER_RECOVERY` recommends relaunch commands.
      `review-channel --action recover --recover-provider claude` is now the
      bounded repo-owned stale-implementer replacement path, and
      `reviewer-heartbeat --follow` auto-escalates repeated unchanged stale
      implementer state through that single-side recovery path instead of
      leaving the loop parked on polling prose forever. The same
      reviewer-follow loop now auto-escalates repeated unchanged stale
      reviewer/runtime states through the existing repo-owned
      `review-channel --action rollover` path, reusing the structured
      handoff bundle plus visible rollover-ACK contract instead of relying on
      manual remote-control restarts. Generalized automatic relaunch of
      whichever peer is missing still remains open Phase 3/4 work.
- [x] Promote implementer completion-stall into shared backend attention state
      instead of keeping it tandem-only. The same reducer that powers
      `check_tandem_consistency.py` should also drive review-channel
      `AttentionStatus`, status projections, and downstream VoiceTerm/PyQt6/
      phone/CLI surfaces so "Claude parked on review/polling" is visible as
      repo-owned runtime truth rather than only prompt text plus an on-demand
      validator.
      Verified 2026-03-28: `IMPLEMENTER_COMPLETION_STALL` is already an
      `AttentionStatus` in attention.py, threaded through status_projection.py,
      event_projection.py, peer_liveness.py, peer_recovery.py,
      bridge_validation.py, and handoff.py/handoff_constants.py. The stall
      flag flows from bridge liveness through the shared attention contract
      to all downstream surfaces.
- [x] Ensure the loop uses one master document chain:
      `MASTER_PLAN` -> relevant active-plan checklist -> `bridge.md`
      current-state bridge.
- [ ] Keep tracker/runbook truth aligned when launcher blockers change state:
      `MASTER_PLAN`, `review_channel.md`, and `continuous_swarm.md` may not
      simultaneously describe the same bridge-bootstrap blocker as both open
      and obsolete/closed.
- [x] Keep cadence and live-session metadata honest:
      `poll_due` remains the 180-second reviewer cadence, `stale` remains the
      300-second heartbeat window, the bridge prose must match those thresholds,
      and `latest/sessions/*.json` plus `review-channel --action status` must
      describe the actually active conductor instance or clearly report none.
- [x] Add `--scope` / `--plan` flag to `review-channel --action launch` so
      the launcher can re-scope `Current Instruction For Claude` automatically
      from a named active-plan doc instead of requiring manual bridge edits
      before every new task. Landed in `review_channel/promotion.py`
      (`resolve_scope_plan_path`, `scope_bridge_instruction`) and
      `commands/review_channel_bridge_support.py` (`apply_scope_if_requested`).
      The launch report now returns the promotion candidate instead of `null`
      when `--scope` is used.

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

### Phase 5 - Standing Typed-System Dogfood Protocol

- [ ] Make live role-rotation proof a standing development rule instead of a
      one-off milestone. Every non-trivial slice must be re-proven by actual
      agents over the shared typed backend before it is called done.
- [ ] Run a bounded role matrix on each qualifying slice:
      `Codex reviewer`, `Codex dashboard`, `Codex implementer`, `Claude
      reviewer`, `Claude dashboard`, and `Claude implementer` must each be
      exercised through the same typed surfaces when the architecture claims
      that role is supported.
- [ ] Require the same typed bootstrap stack for every lane in that matrix:
      `startup-context --role ...`, `session-resume --role ...`,
      `review-channel --action status|doctor|inbox|watch|ack`, and the
      governed `devctl commit` / `devctl push` path when mutation is in
      scope. If an agent still needs chat-local explanation to know what to
      run next, log that as a live failure instead of treating it as normal
      operator help.
- [ ] Keep one live dashboard/operator lane active during each dogfood run
      and require the other agent lanes to communicate what they see through
      typed packets. Status reports, role confusion, unexpected blockers, and
      read-model drift should be visible in packet history, not just bridge
      prose or chat narration.
- [ ] Treat event-driven packet wake as the default transport for the standing
      loop. Reviewer, dashboard, and implementer lanes should share one
      event-backed packet stream, with timer polling kept only as degraded
      fallback or watchdog evidence.
- [ ] Treat every mismatch between typed surfaces and agent behavior as a
      first-class defect. If an agent cannot find the right role, misses the
      inbox, misreads startup authority, chooses the wrong recovery command,
      or fails to recognize the governed mutation path, record that failure in
      `dev/audits/LIVE_RUN.md`, tie it to the owning plan, fix it, and rerun
      the same matrix slice until the agents self-orient correctly.
- [ ] Keep a standing priority queue for this protocol sourced from live
      findings and architecture owner docs. The current queue is:
      `LIVE_RUN Q76-Q80 consumer wiring`, `Q83/Q85 single-surface truth`,
      `Q20 packet lifecycle/history convergence`, `Q13 remote-control
      commit/push proof`, then `Q46/Q48/Q65 role/system-picture/authority
      convergence`.
- [ ] Use sidecar research agents continuously during the live loop, not just
      after it stalls. One agent should mine `LIVE_RUN.md`, one should map
      active-plan promises versus reality, and one should audit code/test
      coverage so the reviewer/implementer/dashboard conductors can stay in
      role while the sidecars surface the next bounded architectural miss.

## Progress Log

- 2026-04-13: Made the reviewer-side wake path obey typed inbox authority
  instead of reconstructing it from raw pending-packet scans. Reviewer wait
  now loads `packet_inbox` from the governed status/report projection, fails
  closed when that typed inbox is missing, and wakes separately on actionable
  packets versus Codex-targeted findings instead of collapsing both into one
  loose pending bucket. Reviewer follow now surfaces reviewer packet state
  from the same typed `packet_inbox` contract and reports the source
  explicitly as `typed_packet_inbox` rather than falling back to raw event
  scans. Focused proof is green: `python3 -m pytest
  dev/scripts/devctl/tests/review_channel/test_reviewer_wait.py -q` (`43
  passed`) and `python3 -m pytest
  dev/scripts/devctl/tests/review_channel/test_review_channel.py -q -k
  "test_reviewer_follow_frame_surfaces_latest_claude_packet"` (`1 passed`).
  The next gap is no longer packet discovery; it is the governed checkpoint
  path still stopping at `checkpoint_required` / `pipeline_state=guards_failed`
  instead of completing the real commit proof from the writable implementer
  lane.
- 2026-04-13: Closed the current-instruction split between live
  `review-channel status`, the persisted typed `review_state.json`, and the
  synchronized `bridge.md` metadata. The bridge compatibility sanitizer now
  preserves nested reviewer instruction bullets instead of flattening them
  into lossy top-level items, the bridge projection metadata path now
  recomputes `current_instruction_revision` from typed `current_session`
  authority instead of replaying stale compat metadata, and the status bundle
  writer now serializes the already-computed authoritative `current_session`
  instead of recomputing it from stale prior cache on the write path. Focused
  `test_bridge_render.py`, `test_current_session_projection.py`, and
  `test_review_channel.py` regressions are green, and the live status surface
  now agrees with both `bridge.md` and `review_state.json` on canonical
  instruction revision `489ded7b0f43`. The remaining bridge/status warning is
  now narrower and real: stale `Claude Status` compatibility content is still
  drifting from typed `current_session`, so the next slice should either
  project implementer status from typed runtime/packet state or clear stale
  bridge-only status instead of preserving it as faux authority.
- 2026-04-13: Closed the first manual packet-watch seam in the live Codex
  reviewer loop. `review-channel --action reviewer-wait` now treats the
  newest Codex-targeted pending packet id as part of its wake contract, so a
  reviewer-side bounded wait exits when fresh typed work arrives instead of
  relying on a separately started `watch --follow` process or chat relay.
  Focused `test_reviewer_wait.py` regressions and the swapped-role reviewer
  prompt contract are green. The remaining packet-watch gap is now narrower
  and explicit: bootstrap/runtime still need to auto-start long-lived packet
  follow for live sessions, and `status|doctor` still need to prefer the
  event-backed typed loader so queue truth and dashboard truth converge.
- 2026-04-12: Logged a fresh live-monitoring defect from the home-desk dogfood
  continuation. The monitoring lane treated an older Codex `TASK COMPLETE`
  boundary as if the review lane were still the active wait target, even
  though the operator was using a newer visible Codex terminal and Claude had
  already posted new pending findings into the Codex inbox. Live evidence:
  `agent-mind` reported the last completed Codex rollout at 2026-04-12
  22:52:50Z, host `ps` still showed two local Codex terminals (`ttys018`,
  `ttys019`), and `review-channel --action inbox --target codex --status
  pending --format json` still contained five unread Claude packets
  (`rev_pkt_0269` through `rev_pkt_0263`). The runtime issue is now explicit:
  completion is not treated as a hard liveness boundary, and the dogfood loop
  still lacks built-in inbox-first waiting after a slice closes. Keep this in
  the standing queue until the monitor/wait path reads task completion plus
  packet backlog together and fails closed on unread targeted packets.
- 2026-04-12: Closed the universal operator ACK/apply bypass on typed review
  packets. `review-channel` packet transitions now require the addressed lane
  to ack/apply its own packets, while `system`-targeted runtime approvals stay
  operator-owned for the governed commit/push path. Focused plan-packet
  regressions plus the governed commit/approval tests that rely on
  operator-applied `commit_approval` packets are green, and the live queue
  proved the cross-agent handshake again when Claude acked `rev_pkt_0267`
  after the startup-receipt role fix landed. The next live blocker is no
  longer packet impersonation; it is dashboard-centered approval flow and
  queue convergence for the real remote-control commit/push proof.
- 2026-04-12: Closed one of the live self-orientation seams in the standing
  typed-system dogfood loop. `session-resume` was already role-aware, but
  `startup-context` still flattened reviewer and implementer lanes back into
  the same generic checkpoint rerun text even when the live blocker was only
  `checkpoint_required`. The startup receipt path now carries the caller lane
  into the first-hop `next=` command and persisted receipt intent, so live
  reviewer startup says to run reviewer bootstrap and live implementer startup
  says to run implementer bootstrap before the checkpoint/approval sequence.
  Focused `startup_context`, `startup_receipt`, and `startup_gate`
  regressions are green, and the next live blocker exposed by typed state is
  narrower: packet ACK/application authority still needs role validation and
  inbox-first handling before the remote-control commit/push proof can close.
- 2026-04-12: Promoted the local-proof loop into a standing typed-system
  dogfood protocol instead of treating live AI runs as an occasional sanity
  check. The repo already has the typed backend pieces (`startup-context`,
  `session-resume`, review-channel packets, status/doctor, governed
  commit/push, dashboard/monitor), but the live failure mode is now explicit:
  a slice is not done if Codex or Claude still needs operator narration to
  know its role, the next command, or the packet lane. The standing closure
  rule is now frozen in this owner doc: run the role matrix, keep a live
  dashboard lane watching the other agents through typed state, log every
  agent-confusion miss to `LIVE_RUN.md`, fix it in the owning runtime/plan
  surface, and rerun the same slice until the agents self-orient.
- 2026-04-12: Started the role-portability + phone-operator execution slice.
  The active docs already require one shared backend for developers, agents,
  and remote-control clients, but the live local proof still speaks in
  `Codex reviewer` / `Claude coder` terms and still exposes provider-shaped
  authority seams. The new closure order is explicit: keep the phone-attached
  primary worktree as the control/dashboard lane, move mutating implementation
  work into reusable isolated worker worktrees, replace provider-coded role
  defaults and turn-authority assumptions with typed role assignment, and then
  rerun the beta matrix as `Codex reviewer + Codex worker implementer + Claude
  dashboard` before widening to swapped reviewer/implementer assignments.

- 2026-04-05: Closed two operator-facing review-loop safety gaps on the same
  `MP-358` slice. The live recovery-command authority now recommends visible
  `--terminal terminal-app` relaunch/recover commands by default for local
  terminal sessions and keeps `remote_control` sessions headless, so repo-
  owned status/doctor/startup surfaces stop steering AI launch decisions
  toward hidden conductors on a desktop machine. The same slice now derives
  explicit visibility state from existing session metadata and emits it as
  typed runtime state (`reviewer_runtime.conductor_visibility` and reviewer
  `session_owner.session_visibility`) instead of forcing operators or AI to
  infer "headless vs visible vs mixed" from raw `terminal_window_id` values.
  Focused recovery/launcher/runtime-doctor regressions are green.

- 2026-04-05: Tightened the reviewer-follow stale-runtime recovery seam so it
  now obeys the typed recovery command instead of inventing a second stale-
  reviewer policy. `reviewer_follow_recovery.py` now suppresses the legacy
  peer-stale `rollover` path whenever `recovery_assessment` /
  `recovery_action_allowed` says the correct repair is `launch`, and
  auto-launch only fires when the typed decision explicitly marks relaunch as
  auto-fixable. When relaunch stays approval-gated, the follow loop now fails
  closed and relies on the existing queued reviewer-turn packet instead of
  taking the wrong side effect. Focused reviewer-follow regressions now cover
  typed launch preference, approval-gated no-auto-launch, skipped restore when
  review is not needed, and helper-level rollover fallback.

- 2026-04-03: Landed Slice 1 and Slice 1.5 of the review-loop authority
  repair on the live `MP-358` lane. The new shared
  `review_channel/turn_authority.py` projection now derives reviewer mode /
  effective mode, launch truth, attention, recovery permission,
  implementation-block state, and next-turn routing from typed `review_state`
  plus the bridge-only reviewer wait markers, and `bridge-poll` consumes that
  shared projection instead of keeping its own local turn-state branch tree.
  `check_review_surface_consistency.py` now also proves `bridge-poll` matches
  the same typed snapshot/turn-authority payload, so parity drift fails as a
  guard instead of surviving until another manual loop audit. Focused
  `bridge-poll`, guard, status-adjacent, and wait-adjacent regressions are
  green. Remaining next slice is the reviewer-accepted implementer baseline
  for the reviewed-current completion dead zone, then the follow-on wait and
  recovery consumer migrations already listed below.

- 2026-04-03: Revalidated the provisional repair plan against an external
  multi-agent audit before promoting it into owner docs. Confirmed the core
  gaps: `bridge-poll` still derives turn state locally instead of consuming
  `ReviewerRuntimeContract`, reviewer checkpoints still do not persist a
  reviewer-accepted implementer-state baseline, and existing guard coverage
  still omits bridge-poll parity. Refined two scope boundaries at the same
  time: wait consumers already read typed attention/effective-mode data so
  their gap is contract completeness rather than total isolation, and startup
  launch gating is already aligned through `startup-context` so bridge-poll
  must converge to startup/status/doctor authority, not the reverse. The
  plan artifact now reflects that narrower repair: shared typed turn-authority
  projection first, parity guard slice next, reviewer-accepted implementer
  baseline after that, then wait/recovery semantics and end-to-end parity
  proof.

- 2026-04-03: Ran one more alignment pass against the latest multi-agent
  critique and tightened the surface inventory. The review was right that a
  few more reviewer-side consumers still make local liveness/recovery
  decisions beyond `bridge-poll` and the two wait loops, but the raw "10 total
  authority gaps" framing overcounted by including upstream producer/
  compatibility helpers. The canonical follow-on set is now explicit in this
  plan: `bridge_runtime_state.py`, `recover_support.py`,
  `reviewer_follow_packet_guard.py`, and `reviewer_follow_recovery.py` must
  migrate after the shared turn-authority projection lands, while
  `status_projection_*` and `event_projection_*` stay classified as upstream
  fail-closed producers rather than separate turn-authority owners.

- 2026-04-03: Audited the current live-loop deadlock against repo-owned status,
  startup, and bridge surfaces and recorded the bounded repair slice in this
  plan instead of another shadow note. Two mismatches are now explicit:
  `review-channel --action bridge-poll` can still report
  `next_turn_reason=up_to_date` from bridge/hash freshness while typed
  `status` / `startup-context` demote the same declared `active_dual_agent`
  loop to `tools_only` / `review_loop_relaunch_required` when launch truth
  shows no live repo-owned Codex conductor, and the loop still has a
  reviewed-current completion dead zone where Claude can post a substantive
  slice-complete update yet no explicit reviewer-owned promotion/follow-up
  state is emitted. The bounded fix order is now frozen here: converge turn
  authority onto the typed reviewer-runtime contract first, then add explicit
  reviewer-owned completion/promotion semantics, then prove parity across
  bridge-poll, wait, status, doctor, and startup surfaces before widening any
  more stale-peer or remote-control automation.

- 2026-04-03: Ran a bounded architecture audit on the live reviewer/coder
  deadlock before widening into code changes. Confirmed two separate contract
  gaps: `bridge-poll` still uses a weaker liveness model than
  `status`/`startup-context`, and it also lacks a typed reviewer-accepted
  implementer-state baseline, so Codex can still owe verdict/promotion even
  when the reviewed tree hash already matches the worktree. Wrote the
  provisional repair plan at
  `dev/reports/review_channel/2026-04-03-review-loop-authority-repair-plan.md`
  for Claude review before promoting the accepted slices into canonical owner
  plans.
- 2026-04-02: Closed the first reviewer-side stale-peer auto-recovery slice
  for the phone-steered loop without inventing a new remote-control path.
  `reviewer-heartbeat --follow` now detects repeated unchanged stale reviewer
  states (`runtime_missing`, stale/missing/overdue reviewer heartbeat, and
  `review_loop_relaunch_required`) and triggers the existing repo-owned
  `review-channel --action rollover` flow directly. The trigger reuses the
  structured `HandoffBundle`, visible rollover ACK contract, and launch
  records already owned by the review-channel runtime; focused reviewer-follow
  regression coverage now proves both the positive trigger and the inactive-
  mode fail-closed case.
- 2026-04-02: Hardened the phone-steered remote-control wrapper for the local
  loop without pretending the missing reviewer-runtime architecture already
  exists. `dev/scripts/remote-bridge-loop.sh` now syncs the project-local
  `/project:bridge-loop` slash command from the tracked
  `dev/scripts/remote_bridge_prompt.md` source, fails early on `claude auth
  status`, surfaces typed `review-channel --action status` health before
  opening remote control, can optionally relaunch the sanctioned
  `review-channel --action launch` pair when the loop is inactive, and cleans
  up `caffeinate` on exit instead of leaking a stray keep-awake process. The
  paired prompt now treats typed review-channel status as canonical for live
  health, relays `bridge.md` Codex state to the phone user, and only uses the
  sanctioned `launch`, `ensure`, and `recover --recover-provider claude`
  recovery paths instead of an invented Codex-only recover command. Next step:
  prove one live remote-control loop end-to-end and decide whether this stays
  a repo-local compatibility wrapper or graduates into a repo-owned `devctl`
  surface.
- 2026-04-09: Tightened the same phone-steered wrapper so it consumes repo-
  owned typed next-step truth instead of generic launch hints. The wrapper now
  surfaces `review-channel status` top-level `recommended_command` plus
  `doctor.decision_command`, prefers a typed review-channel recovery command
  when `--bootstrap-review-channel` is requested, and only falls back to the
  full `launch` pair when no typed recovery path exists. The paired remote
  Claude prompt also now starts from `session-resume --role implementer
  --format bootstrap` and uses governed `devctl commit` / `devctl push`
  rather than raw git so the external phone session stays on the same typed
  repo-owned control path as local sessions.
- 2026-03-28: Re-audited the W1 bridge-truth-sync item against the actual
  reviewer write paths after Claude flagged a likely overstatement in the
  checklist text. Confirmed the repo-owned tooling side is already in place:
  `review-channel --action reviewer-checkpoint` atomically rewrites reviewed
  hash, verdict, findings, instruction, and `Last Codex poll`, and the
  repo-owned promote/instruction-rewrite path also refreshes reviewer
  metadata in the same transform. Narrowed the remaining open work
  accordingly: keep Codex on repo-owned reviewer writes only, and add the
  guard/prompt/contract coverage needed so raw `bridge.md` edits cannot
  silently bypass that synchronized path.
- 2026-03-25: Closed the next stale-implementer recovery gap without
  overstating it into a full loop restart. Review attention now distinguishes
  `implementer_relaunch_required`, `review-channel --action recover
  --recover-provider claude` launches only a fresh Claude conductor for that
  state, and `reviewer-heartbeat --follow` now auto-escalates repeated
  unchanged stale-implementer progress through that narrower repo-owned
  recovery path instead of invoking full rollover or sitting forever on raw
  polling prose. Generalized stale-peer recovery and end-to-end local proof
  still remain open.
- 2026-03-22: Closed the next reviewer-to-Claude wait-surface gap in the live
  local loop. `review-channel --action implementer-wait` now exposes typed
  attention context directly in the stable wait report (`wait_attention_*`)
  and specializes reviewer-update/timeout messages for
  `review_follow_up_required` and `claude_ack_stale` instead of collapsing
  everything into generic "Holding for Codex review" text. The markdown wait
  projection renders the same typed context so `tail -5`, `latest.md`, and
  other operator/implementer surfaces can see why the loop is paused without
  guessing from stale prose.
- 2026-03-22: Landed the reviewer-side parity step from the same loop-hardening
  lane. `review-channel --action reviewer-wait` now exports the same typed
  wait-attention surface and state-specific wake/timeout/unhealthy messages,
  markdown wait rendering covers reviewer-wait payloads, and the reviewer
  prompt contract now explicitly routes Codex onto `reviewer-wait` instead of
  ad-hoc sleep loops when parked on Claude progress.
- 2026-03-20: Closed the next reviewer-to-Claude visibility gap in the live
  local loop. `review-channel --action implementer-wait` now folds the newest
  pending Claude-targeted review packet into its wake token, so the repo-owned
  bounded wait path wakes on fresh reviewer packets as well as reviewer-owned
  bridge changes. The Claude prompt surface and bridge/test fixtures now
  require packet inbox/watch polling alongside bridge polling on the same
  cadence so the dual-agent loop no longer depends on human chat relay to make
  reviewer packets visible.
- 2026-03-19: Replaced the unsafe Claude-side raw bridge poller with a
  repo-owned bounded wait path. `review-channel --action implementer-wait`
  now polls on the normal review cadence, wakes only when reviewer-owned
  bridge content changes, fails closed when the reviewer loop is unhealthy,
  and times out after one hour by default instead of leaving a background
  `sleep 300` shell loop behind. Prompt guidance and maintainer docs now
  point the implementer lane at this command so the live loop can wait
  safely without relying on later process cleanup.
- 2026-03-19: Closed the next reviewer-loop honesty gap on the Codex-side
  `ensure` auto-heal path. Reviewer-supervisor restarts now re-read status
  after detached-start verification fails, so `ensure` reports the persisted
  failed-start lifecycle instead of the stale pre-restart snapshot. The same
  slice also moved that restart logic into
  `commands/review_channel/_ensure_supervisor.py` to keep `ensure.py` under
  the Python soft limit while preserving the repo-owned persistent reviewer
  loop contract. Validation: `python3 -m pytest
  dev/scripts/devctl/tests/test_review_channel.py -q`, `python3
  dev/scripts/devctl.py check --profile quick --skip-fmt --skip-clippy
  --no-parallel`, and `python3 dev/scripts/devctl.py check --profile ci
  --skip-fmt --skip-clippy --no-parallel`.
- 2026-04-03: Reconciled the live 8+8 bridge model against the current clean
  tree handoff and the overdue reviewer runtime. The missing operational link
  is now explicit here too: detached publisher/reviewer-supervisor runtime is
  necessary but not sufficient for autonomous swarm continuity, because the
  repo still lacks a persistent Codex reviewer worker/service path that keeps
  semantic review, promotion, and operator-visible checkpoints moving between
  Claude passes. Until that lands, 8+8 remains conductor-managed capacity over
  one shared backend. Requested worker budget and delegated-lane truth must
  keep flowing through `CollaborationSession` / `DelegatedWorkPacket`
  projections rather than bridge-local guesswork or "all workers share the
  same context" assumptions.
- 2026-03-17: Clarified the many-agent operating model for `MP-358`. Codex
  remains the sole conductor and final reviewer, Claude may fan out many
  bounded coding workers only behind one Claude conductor, and every
  non-trivial slice now requires a separate Codex-side architecture-fit
  reviewer before acceptance. The loop direction stays one shared backend plus
  conductor-owned bridge/state writes, not a second worker-owned control
  plane.
- 2026-03-27 plan-driven swarm-scoping follow-up: the many-agent model now
  also freezes where worker scope comes from. Future swarms should compile
  lane roles from active plan authority (`WorkIntakePacket`,
  `PlanExpectationPacket`, owned issue cluster/target refs) so workers are
  assigned exact roles, worktrees, command families, and evidence contracts
  instead of "read the repo and help" prompts. Capacity stays 8+8, but the
  role map is regenerated per plan slice rather than treated as a permanent
  static table.
- 2026-03-15: Closed the next scope-drift miss on the operator-docs path.
  `DEVCTL_AUTOGUIDE.md` had durable system knowledge in prose but no
  deterministic sync contract, so `docs-check --strict-tooling` could stay
  green while the playbook silently omitted major control-plane surfaces. The
  repo now has `check_guide_contract_sync.py`, wired into docs governance,
  tooling/release workflows, and the shared bundle registry, plus a new
  `System Coverage Map` section in `DEVCTL_AUTOGUIDE.md` that keeps
  policy/contract/governance, launcher, mutation/compatibility, and
  queue/device/recovery helpers in explicit scope for Codex, Claude, and
  maintainers.
- 2026-03-15: Hardened the new guide-contract guard after the first live audit.
  The initial `check_guide_contract_sync.py` pass only verified whole-file
  substrings, which meant the `System Coverage Map` could drift while the same
  command names still existed elsewhere in `DEVCTL_AUTOGUIDE.md`. The repo
  policy now supports section-scoped `required_sections`, the guard validates
  heading-local coverage, and the autoguide contract now pins the shared
  review/runtime/operator surfaces (`render-surfaces`, `review-channel`,
  `tandem-validate`, `reviewer-heartbeat`, `reviewer-checkpoint`,
  `swarm_run`, `mobile-status`, `phone-status`, `controller-action`,
  `orchestrate-*`, `integrations-*`, `mcp`) instead of over-weighting only
  VoiceTerm-local convenience wrappers.
- 2026-03-15: Re-activated the markdown bridge as a live `active_dual_agent`
  reviewer path through `review-channel --action reviewer-checkpoint` after it
  had drifted back to `single_agent`, then finished the role-owned tandem
  guard split so `dev/scripts/checks/tandem_consistency/checks.py` is a thin
  compatibility facade over `reviewer_checks.py`,
  `implementer_checks.py`, `operator_checks.py`, and
  `system_checks.py`. Focused tandem/review-channel tests and bridge/docs
  governance are green again. The same review pass also confirmed the next
  real loop-hardening gap: completion-stall is now a hard tandem guard, but it
  is still not a first-class review-channel attention signal that shared
  backend clients can render consistently.
- 2026-03-15: Closed the next real loop-stall gap by turning "Claude says the
  slice is done / instruction unchanged / continuing to poll" into hard
  enforcement instead of prose. `check_tandem_consistency.py` now includes an
  `implementer_completion_stall` check that fails when Claude-owned
  status/ack text parks on reviewer promotion/polling while the current bridge
  instruction is still active and not in an explicit reviewer-owned wait
  state. The repo-owned reviewer writer also now strips stale reviewer-mode
  prose from `Poll Status`, and the bridge guard fails when `Poll Status`
  contradicts header `Reviewer mode`, so the backup markdown bridge cannot
  silently rot into conflicting live states. The shared Claude instruction
  surface (`claude_instructions.template.md` -> `CLAUDE.md`) now mirrors the
  same anti-stall rule.
- 2026-03-15: Re-audited the current loop after landing the reviewer-state
  writer split and the routed `tandem-validate` lane. Confirmed the core
  direction is right, then recorded the remaining architectural truth:
  inactive modes are now honest (`single_agent`, `tools_only`, `paused`,
  `offline`) and share the same backend, but the repo still needs a
  persistent reviewer-liveness emitter, a thin shared mode toggle surface, and
  JSON-first authority so markdown no longer acts like the live source of
  truth by accident.
- 2026-03-15: Re-read the broader architecture plan after a scope audit and
  tightened the local-proof framing. `MP-358` now explicitly records that it
  is one proving lane inside the full-system modular/callable extraction under
  `MP-377`, not the product boundary by itself. Future loop work must name the
  shared backend/runtime contract it strengthens and must not justify new
  VoiceTerm-embedded or dev-only control paths.
- 2026-03-15: Landed repo-owned reviewer-state actions for the markdown bridge
  and mode-aware stale handling. `review-channel --action reviewer-heartbeat`
  now updates liveness plus `Reviewer mode` without faking a new reviewed hash,
  while `review-channel --action reviewer-checkpoint` atomically advances
  reviewed hash, verdict, findings, instruction, and reviewed scope after a
  real review pass. The bridge and tandem guards now treat
  `single_agent` / `tools_only` / `paused` / `offline` as honest inactive
  modes instead of stale dual-agent failure, which gives developers and solo
  AI runs the same backend without a second control plane.
- 2026-03-15: Replaced the narrow hand-maintained tandem validation checklist
  with a repo-owned `devctl tandem-validate` lane for MP-358. The command now
  resolves the real AGENTS lane and risk add-ons through `check-router`,
  executes that routed bundle, and reruns final `check_review_channel_bridge`
  / `check_tandem_consistency` postflight checks so Codex/Claude sessions use
  the same validation authority as maintainers instead of grepping for a small
  custom command list. Maintainer docs (`dev/scripts/README.md`,
  `dev/guides/DEVELOPMENT.md`) now point tandem sessions at that wrapper.
- 2026-03-15: Landed tandem-consistency guard and role-profile seam (MP-358).
  `runtime/role_profile.py` defines `TandemRole`, `RoleProfile`,
  `TandemProfile`, and `role_for_provider()`. `check_tandem_consistency.py`
  validates alignment across peer-liveness, event-reducer, status-projection,
  launch, prompt, and handoff. Wired into `bundle.tooling`, CI workflows,
  quality-policy presets, and `VOICETERM_ONLY_AI_GUARD_IDS`. Cursor agent entry
  added to event-reducer and status-projection (3-agent roster becomes 4).
  `pending_cursor` added to `ReviewQueueState` and queue output.
- 2026-03-15: Made the launcher bridge-optional in auto execution mode.
  `ensure_launcher_prereqs`, `bridge_launch_state`, heartbeat refresh,
  `scope_bridge_instruction`, `promote_bridge_instruction`, bridge guard,
  and auto-promote all gate bridge reads/writes behind `bridge_path.exists()`.
  When the bridge is absent, the launcher falls through to lane parsing from
  `review_channel.md` and constructs an empty `BridgeSnapshot`. Commits:
  `7c9c901`, `89c6742`, `63a6c62`, `2e30bd6`, `37acd1b`.
- 2026-03-15: Ran 8-lane audit. Key findings: no typed backend API layer,
  `PhoneControlSnapshot`/`operator_decisions` are surface-local authority
  leaks, `review_state` naming overloaded in `event_reducer.py` (defer
  rename), plan set is healthy with one minor MP-376/377 boundary note.
- 2026-03-15: Landed three bounded MP-358 slices:
  1. Fixed `--scope` promotion bug: `apply_scope_if_requested()` now returns
     the `PromotionCandidate`, launch report shows real `promotion` data
     instead of `null`. Added `--auto-promote` CLI flag. (`86b902c`)
  2. Wired `reviewed_hash_current` into live callers: `bridge_launch_state()`
     and `refresh_status_snapshot()` compute current worktree hash and pass it
     to `summarize_bridge_liveness()`. Status output shows `true/false`. (`0935dc8`)
  3. Added `REVIEWED_HASH_STALE` attention signal: fires when all
     higher-priority checks pass but the reviewed tree hash doesn't match the
     current worktree. Recovery contract recommends Codex re-review. (`4ae9830`)
- 2026-03-13: Validated the next bridge-truth drift after the Phase 0
  classification write. The bridge header heartbeat/hash advanced to
  `2026-03-14T02:17:03Z` / `95a196f52cce...`, but `bridge.md` still clears
  reviewed hash `6d277...`, still points `Plan Alignment` at
  `review_probes.md`, and still instructs Claude to rerun the already-complete
  Phase 0 classification while `dev/reports/review_channel/latest/latest.md`
  already derives the Phase 1 cleanup item. The same audit also confirmed live
  session provenance drift: `latest/sessions/*.json` rewrote to a new
  `review-channel-launch-gbh8czwt` temp dir while the still-running Codex
  conductor process remained on the older `review-channel-launch-38a4x4q_`
  script path and `review-channel --action status --format json` reported
  `sessions: []`. Added Phase 2 follow-ups for bridge truth synchronization,
  tracker/runbook closure parity, and cadence/session metadata honesty so these
  regressions are tracked as loop-behavior debt instead of being mistaken for
  fresh proof.
- 2026-03-13: Completed the Phase 0 issue classification against live code,
  54 passing review-channel tests, and verified CLI dry-runs. Result: 6
  issues classified `obsolete` (heartbeat-aged-out launcher death,
  two-terminals-masquerading-as-healthy, host-hygiene conductor
  misclassification, stale-peer detection not machine-readable, launcher
  missing bridge guard, zero-second ACK acceptance), 1 classified
  `field-report-intermittent` (both-conductors-stopped-after-summary,
  mitigated by anti-stall supervision but root cause is provider
  compliance), and 4 classified `verified-current` (automatic next-task
  promotion, stale-peer auto-recovery, heartbeat contract enforcement,
  context rotation auto-trigger) which map to open Phase 2-3 checklist
  items. Phase 0 contract and diagnostics items are now fully closed.
- 2026-03-13: Closed the next proof-of-liveness gap exposed by the broken live
  reviewer session. `review-channel --action launch --terminal terminal-app`
  now waits for `Last Codex poll` to advance after the windows open and fails
  closed when the reviewer heartbeat never appears, so "two terminals exist"
  no longer masquerades as a healthy Codex/Claude loop. The same slice also
  turns stale-peer detection into a machine-readable `attention` contract on
  the bridge-backed `review_state` payload and carries that signal into the
  PyQt6 Operator Console snapshot warnings, which gives the desktop shell a
  repo-owned way to say "Codex is stale / Claude ACK is missing / poll is due"
  instead of relying on provider memory or operator guesswork. A same-slice
  follow-up split that attention/launch logic into dedicated review-channel
  modules and now drives Codex/operator lane health plus session stats from the
  same attention state, so the default desktop workbench shows the loop as
  stale even before the operator opens a diagnostics report.
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
  `bridge.md` conductor loop, `swarm_run`/`autonomy-swarm`/
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
  conductors receive exact ACK lines they must write into `bridge.md`, and
  the command can wait for those visible ACKs before the retiring session exits.

- 2026-04-12: Home-desk dogfood closed the immediate code-shape and packet
  liveness blockers from Claude's live findings, but the governed commit proof
  still surfaced a sandbox authority gap. `devctl commit` now reports the
  stage failure truthfully as `git_index_write_blocked` when `.git/index.lock`
  cannot be created, instead of collapsing the failure into a generic staged
  tree hash error. Remaining work is to keep that approval/sandbox boundary
  repo-visible and finish the role-enforced remote-control commit proof
  without relying on chat-local explanation.
- 2026-04-13: Converted packet attention from an observer convention into a
  typed execution prerequisite. The live review-state now carries one
  canonical `packet_inbox` reducer, startup/session-resume/reviewer-follow
  project that same wake/focus state, and governed stage/commit now fail
  closed with `attention_revision_stale` when the write lane tries to proceed
  on an out-of-date startup receipt. This is the first standing proof that
  "system knows" and "system governs" are being merged in the live loop rather
  than left as independent dashboard prose.
- 2026-04-13: Tightened that same stale-attention gate after the next dogfood
  checkpoint proof exposed a false positive. The write lane no longer treats
  expired unresolved packet history as actionable attention for
  `attention_revision_stale`; stage/commit now reserve the hard block for live
  findings or pending actionable packet rows, which restores parity with the
  implementer bootstrap packet saying `attention: inactive` and
  `commit current work, then rerun startup-context` while old packet debt
  remains visible in the typed inbox/report surfaces.
- 2026-04-13: Removed the next helper detour from the live control path. The
  queue reducer is now the only packet selector allowed to derive a typed next
  instruction; `event_current_instruction()` and `current_focus_line()` no
  longer recompute instruction/focus from bridge text or raw packet summaries.
  This narrows the remaining live mismatch to one compatibility seam:
  markdown-bridge `review-channel status` still renders with typed-current-
  session drift warnings, so the next closure is to make that bridge-mode
  status path consume typed current-session truth directly.
- 2026-04-13: Narrowed the markdown-bridge status corruption bug to the
  bridge/status authority chooser. `refresh_status_snapshot()` now seeds
  prior typed authority from the canonical review-state resolver instead of
  blindly trusting `dev/reports/review_channel/latest/review_state.json`,
  stale/overdue bridge state no longer overwrites a substantive typed
  `current_session`, and a placeholder typed session can recover from live
  bridge instruction instead of collapsing to blank. Live proof: top-level
  `review-channel status` again reports `current_instruction_revision=
  3b3fad692219` after sync instead of zeroing the instruction on readback.
  Remaining gap: the written compatibility projection still lags the
  in-memory status surface, so bridge/status write convergence is not fully
  closed yet and the governed checkpoint proof is still blocked on
  `checkpoint_required` plus `pipeline_state=guards_failed`.

## Session Resume

- Current status: the markdown-bridge status lane no longer invents current-
  instruction or `Claude Status` drift. The live operator surface,
  `bridge.md`, and typed `review_state.json` now converge on canonical
  current-session instruction revision `25989d87c56c`, and stale bridge-only
  implementer status is cleared during status sync instead of surviving as
  faux authority.
- Current status: the remaining live bridge warning is real compatibility
  drift, not selector corruption. `review-channel status` still reports
  `checkpoint_required`, `pipeline_state=guards_failed`, and
  `recommended_command=python3 dev/scripts/devctl.py commit -m \"<descriptive message>\"`
  because the worktree is over checkpoint budget.
- Current status: Claude/Codex typed packet traffic is still the required
  control path. The next session should keep packet visibility live and treat
  `dev/reports/review_channel/latest/latest.md` as compatibility output only
  until its remaining consumers are audited and demoted.
- Current status: the stale `attention_revision_stale` false positive is now
  gone for the local implementer lane. After refreshing `startup-context`, the
  governed checkpoint proof reaches the real sandbox boundary again and stops
  at `git_index_write_blocked` because this Codex session still cannot create
  `.git/index.lock`; the remaining closure is execution-environment authority,
  not packet-attention drift.
- Current status: reviewer-side wake handling now reads the typed
  `packet_inbox` contract instead of raw pending-packet scans. Reviewer wait
  fails closed when typed inbox state is missing, and reviewer follow reports
  packet attention from `typed_packet_inbox` rather than inventing wake state
  from fallback event scans.
- Next action: keep Claude/Codex packet traffic live, audit `latest.md` /
  bridge compatibility consumers, then take the next real blocker: the
  governed checkpoint proof from the correct writable implementer lane with
  Claude driving the typed dashboard/operator packets.
- Current status: bridge/status no longer split current-instruction authority.
  The live operator surface, `bridge.md`, and typed `review_state.json` now
  all agree on canonical instruction revision `489ded7b0f43`; the false
  instruction-revision drift warning is gone.
- Next action: keep Claude/Codex packet traffic live, then take the remaining
  real bridge drift seam: either source `Claude Status` from typed runtime /
  packet state or fail closed by clearing stale bridge-only implementer status
  during status sync, then rerun the live dashboard proof.
- Current status: packet attention is no longer just something the dashboard
  or operator is supposed to notice. The typed loop now stores one canonical
  `packet_inbox`, and stale inbox attention can revoke stage/commit authority
  until the lane reloads startup/session state.
- Next action: keep Claude/Codex packet traffic live, but take the next
  convergence slice at `current_instruction`: dashboard/status/current-session
  must share one selector chain so findings never masquerade as instructions
  in one surface while another surface keeps the old bridge instruction.
- Current status: the typed selector chain is narrower now. Queue/current-
  session/dashboard tests are green, and the only live instruction split still
  visible is the markdown-bridge status lane warning that its compatibility
  sections drift from typed `current_session`.
- Next action: collapse markdown-bridge `review-channel status` onto the same
  typed current-session/current-focus selector or force bridge rewrite before
  operator-visible render, then rerun the live Claude/Codex proof from the
  typed packet lane.
- Current status: markdown-bridge status no longer blanks the live instruction
  revision during refresh, and Claude has the typed update as `rev_pkt_0315`.
  The remaining split is narrower: the operator-facing status output holds the
  recovered instruction revision, but the written `latest/review_state.json`
  current-session payload still lags that in-memory report.
- Next action: finish the bridge/status write-side convergence so the written
  typed projection matches the rendered status surface, expose `packet_inbox`
  in startup/session-resume bootstrap output, then rerun the governed
  checkpoint proof from the correct local implementer lane with Claude driving
  dashboard packets.
- Current status: the home-desk loop plus the latest dashboard packets pushed
  the standing dogfood protocol past simple packet-watch bugs. The remaining
  blockers are now Phase-0 visibility gaps: ungrounded findings, split status
  surfaces, incomplete packet lifecycle/wake, and dashboard blindness to live
  tool-call progress.
- Next action: keep the live loop on typed surfaces, but do not widen into
  more autonomy until those visibility seams close in the owner docs.
- Current status: reviewer-side bounded waits no longer require a separately
  started packet watcher. `review-channel --action reviewer-wait` now wakes
  on the newest Codex-targeted pending packet id as well as worktree / ACK /
  implementer-state changes, and the reviewer prompt contract now treats the
  standalone watch surface as optional observer tooling instead of required
  operator setup.
- Next action: keep the repo-owned Codex packet watch live for observer proof,
  but treat the remaining packet-watch gap as a launcher/runtime issue: move
  packet-follow startup into `review-channel launch|ensure` and collapse
  `status|doctor` onto the event-backed typed loader so packet truth and
  dashboard truth stop diverging.
- Current status: the latest home-desk continuation proved another monitor gap
  rather than user error. Codex had already hit `TASK COMPLETE`, Claude had
  pending findings queued for Codex, and the loop still behaved as if waiting
  state were clean.
- Next action: fix the stale completion/session-count trust chain and add
  inbox-first wait handling so a completed Codex slice cannot silently ignore
  new Claude-targeted packets.
- Current status: packet transitions no longer allow the universal operator
  bypass across another agent's lane; Claude also acked the latest Codex
  system notice through the typed queue.
- Next action: keep the dashboard packet watch/inbox active, prove the
  `commit_approval` request -> ack/apply -> governed commit path from the
  actual remote-control lane, and fix any remaining queue selection drift if
  Claude's dashboard surfaces still center Codex-targeted work instead of its
  own runtime approvals.
- Current status: the first startup receipt now self-orients reviewer and
  implementer lanes instead of flattening both to one generic checkpoint
  rerun step.
- Next action: keep the live Claude packet watch running, fix the typed
  ACK/apply authority seam (`Ack command has no role validation — any agent
  can ack any packet regardless of target`), then rerun the commit-approval ->
  apply -> governed commit/push proof from the actual remote-control lane.
- Current status: resume from the standing typed-system dogfood protocol, not
  from a test-only or human-orchestrated view of the loop.
- Next action: keep Codex and Claude in real roles over the typed backend,
  require packet-visible communication plus role-specific bootstrap receipts,
  and treat every place where an agent still needs chat-local explanation as a
  live defect that must be logged, fixed, and rerun.
- Current standing priority queue:
  `LIVE_RUN Q76-Q80 consumer wiring`, `Q83/Q85 single-surface truth`,
  `Q20 packet lifecycle/history convergence`, `Q13 remote-control
  commit/push proof`, `Q46/Q48/Q65 role/system-picture/authority seams`.
- Current status: the latest governed commit attempt from the Codex lane
  cleared the local code-shape blockers but failed at the git-index write
  boundary because the sandbox could not create `.git/index.lock`.
- Next action: keep Claude packet watch/inbox live, land caller-role commit
  enforcement so the dashboard lane cannot seize the commit path, then rerun
  the governed commit with the required filesystem authority and continue to
  governed push proof.
- Current status: caller-role commit enforcement is now live in the governed
  `devctl commit` path. Review-channel conductors export `DEVCTL_CALLER_ROLE`,
  `devctl commit --role <lane>` exists for wrappers/tests, and dashboard /
  observer / default reviewer lanes now fail closed before staging instead of
  reaching the git-index or approval path.
- Current status: packet watchers also got a live queue fix. `watch --follow`
  now re-emits when `stale_packet_count` changes, so the typed listener can
  see pending->stale transitions instead of only packet-id churn.
- Next action: rerun the governed commit from the implementer-owned lane with
  escalated filesystem authority, then prove the remote-control operator
  approval -> governed commit -> governed push cycle from the real Claude
  dashboard lane.
- Current status: resume from the new role-portability closure slice, not from
  another Codex/Claude-only loop hardening pass.
- Next action: patch the typed role registry and turn-authority/read-model
  seams first, then prove the hidden primary-control plus worker-worktree
  operating model with `Codex reviewer + Codex worker implementer + Claude
  phone dashboard` before widening to swapped-role tests.
- Current status: this plan remains active; the highest-priority open slice is
  reviewer-turn authority convergence for the live Codex/Claude loop.
- Next action: resume at Slice 2 of the 2026-04-03 repair order. Persist the
  reviewer-accepted implementer-state baseline on the typed reviewer
  acceptance/runtime surface, then thread that semantic baseline through
  `bridge-poll` and the wait/recovery proof without reopening a second turn-
  authority owner.
- Context rule: treat `dev/active/review_channel.md` as the bridge/runtime
  model owner and `dev/active/platform_authority_loop.md` as the startup-
  authority consumer owner while this `MP-358` plan remains the execution
  driver for the local loop repair.
- Context rule: treat `dev/active/MASTER_PLAN.md` as tracker authority and
  load only the local sections needed for the active checklist item.

## Audit Evidence

- `python3.11 dev/scripts/devctl.py review-channel --action status --terminal none --format md`
  - 2026-03-13 local run: stale after the 300-second heartbeat window; bridge
    still advertises a stale Phase 0 instruction while the latest derived-next
    projection has already advanced to Phase 1
- `python3.11 dev/scripts/devctl.py review-channel --action status --terminal none --format json`
  - 2026-03-13 local run: `sessions: []` even while repo-owned conductor
    processes were still present
- `ps -axo pid,ppid,etime,command | rg 'review-channel-launch-'`
  - 2026-03-13 local run: live Codex conductor still running from the older
    `review-channel-launch-38a4x4q_` script path while latest session metadata
    pointed at `review-channel-launch-gbh8czwt`
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
