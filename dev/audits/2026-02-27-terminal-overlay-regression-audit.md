# Terminal Overlay Regression Audit (JetBrains/Cursor, Claude/Codex)

Date: 2026-02-27  
Scope: `MP-226` prompt-occlusion reliability and startup/resume HUD stability

## Objective

Create one canonical audit trail for the current overlay regressions so fixes are
applied one issue at a time and validated without cross-profile regressions.

## Active Problem Matrix

| ID | Surface | Symptom | Current status |
|---|---|---|---|
| `OVR-01` | Claude + JetBrains | HUD can flash/stack during thinking/tool output | fix landed; pending manual repro |
| `OVR-02` | Claude + JetBrains/Cursor | Approval cards can be obscured by HUD | fix landed; pending manual repro |
| `OVR-03` | Claude + JetBrains | HUD hide/re-show can return at wrong anchor after tool phase | fix landed; pending manual repro |
| `OVR-04` | Codex + JetBrains | HUD can fail to show until user types (**Priority 1**) | fix landed; pending manual repro |
| `OVR-05` | Claude + Cursor | Approval option rows (for example 3rd option) can still be overwritten | fix landed; pending manual repro |
| `OVR-06` | Claude + Cursor | Intermittent stale HUD border fragments remain visible behind `Tool use` approval cards during long/multi-step runs | fix landed; pending manual repro |
| `OVR-07` | Claude + JetBrains | Approval card can render only options 1-2 while option 3 is clipped/hidden behind HUD area | fix landed; pending manual repro |
| `OVR-08` | Claude + Cursor | HUD is visible on load, then disappears immediately after first typed key in normal composer mode (non-approval flow) | investigation in progress |
| `OVR-09` | Claude + Cursor | Full-HUD frame blocks can be scrolled/duplicated into transcript content after large tool-result output (for example summary headings + wrapped sections) | investigation in progress |
| `OVR-10` | Claude + Cursor | Minimal HUD row can disappear while typing and return only after editor-control actions (for example `Ctrl+U`) | investigation in progress |

## What Was Tried (chronological)

1. Prompt suppression split into explicit helper path (`event_loop/prompt_occlusion.rs`) and applied from output + periodic loops.
2. Claude prompt detector tightened to high-confidence patterns (approval/worktree/multi-tool) to avoid generic composer false positives.
3. Tool-activity suppression added for active `Bash(...)` output with short timeout and interrupt-aware release markers.
4. Suppression transition now sends `ClearStatus` before `EnhancedStatus` on both suppress and unsuppress.
5. Writer redraw policy differentiated by terminal family (`JetBrains`, `Cursor`, `Other`) and backend profile (`codex_jetbrains`) to reduce Cursor/Codex flashing.
6. Startup guard for Claude+JetBrains added to avoid first-frame collisions.

## Confirmed Root Cause Cluster

The same low-level failure mode is hitting multiple symptoms:

1. IDE terminal size probes can transiently return zero rows/cols at startup or
   suppression resume boundaries.
2. Zero geometry causes `apply_pty_winsize(...)` no-op paths, so prompt-safe row
   reservations are not always restored when HUD reappears.
3. Writer redraw can remain pending while geometry is unresolved, making HUD
   appear only after later terminal activity (typing/output/resize).

## Fixes Applied In This Pass

1. `terminal.rs`: hardened `resolved_rows`/`resolved_cols` to normalize zero-size
   probes via env fallback (`LINES`/`COLUMNS`) or defaults (`24x80`).
2. `writer/state.rs`: normalized zero-size reads in `read_terminal_size()` so
   startup redraw can proceed without waiting for user input.
3. Added focused tests for zero-size normalization and writer fallback redraw.
4. `prompt/claude_prompt_detect.rs`: added numbered approval-card detection so
   option-only cards (`1/2/3`) still trigger prompt suppression when header text
   is sparse or delayed.
5. `event_loop/prompt_occlusion.rs`: suppression transition now emits a writer
   resize sync when geometry normalization changes (for example `0x0 -> 24x80`)
   before clear/redraw messages, reducing wrong-anchor resume risk.
6. `writer/state.rs`: Cursor pre-clear policy now allows pending `ClearStatus`
   suppression transitions to scrub stale border fragments while keeping normal
   Cursor typing jitter guard behavior.
7. `writer/state.rs`: transition redraw path refreshes terminal dimensions prior
   to clear/repaint so stale cached geometry cannot anchor the HUD incorrectly
   after tool/suppression phases.
8. `writer/state.rs`: JetBrains pre-clear now respects a short cooldown during
   streaming output so non-Codex Claude sessions avoid repeated flash/stack
   churn while still applying periodic stale-frame cleanup.
9. `writer/state.rs`: Claude redraw policy now throttles scroll-triggered full
   HUD redraw in Cursor and suppresses per-chunk redraw requests for
   flash-sensitive IDE profiles (`JetBrains+Claude`, `JetBrains+Codex`,
   `Cursor+Claude`) unless a forced full redraw or transition pre-clear occurs.
10. `writer/state.rs`: removed Cursor Claude banner-recovery pre-clear loop so
    PTY streaming no longer forces repeated clear->redraw flashes every cooldown
    interval.
11. `writer/state.rs`: `ClearStatus` now forces an immediate transition redraw,
    and `EnhancedStatus` no longer cancels a pending clear transition, fixing a
    race where stale HUD rows remained over approval option lines.
12. `event_loop/prompt_occlusion.rs`: added suppression-release debounce
    (`3s`) so HUD does not reappear between closely spaced prompt/tool state
    transitions while approval cards are still active.
13. `event_loop/prompt_occlusion.rs`: suppression sync now consumes the event
    loop tick timestamp instead of wall-clock calls, enabling deterministic
    timed behavior and test coverage for delayed release.

## Validation Evidence (this pass)

Commands:

```bash
cd rust && cargo test --bin voiceterm writer::state::tests:: -- --nocapture
cd rust && cargo test --bin voiceterm prompt::claude_prompt_detect::tests:: -- --nocapture
cd rust && cargo test --bin voiceterm set_claude_prompt_suppression -- --nocapture
cd rust && cargo test --bin voiceterm periodic_tasks_clear_stale_prompt_suppression_without_new_output -- --nocapture
python3 dev/scripts/devctl.py check --profile ci
```

Result summary:

- Writer-state tests: pass
- Prompt-detector tests: pass
- Prompt-suppression event-loop tests: pass
- Full CI profile (`devctl check --profile ci`): pass
- Remaining whole-tree blockers outside this overlay scope:
  - `check_code_shape` soft-limit violations in already-large files
    `writer/state.rs` and `prompt/claude_prompt_detect.rs`
  - `check_rust_lint_debt` unwrap/expect growth in pre-existing
    `memory/*` and `runtime_compat.rs` worktree deltas

## Validation Evidence (2026-02-28, flashing follow-up)

Commands:

```bash
cd rust && cargo fmt --check
cd rust && cargo test --bin voiceterm writer::state::tests:: -- --nocapture
cd rust && cargo test --bin voiceterm
cd rust && cargo build --release --bin voiceterm
```

Result summary:

- `writer::state` tests: pass (`28/28`)
- full `voiceterm` tests: pass (`1265/1265`)
- release build: pass
- manual IDE repro still required for:
  - JetBrains + Claude flashing under heavy output + typing
  - Cursor + Claude flashing/stacked border fragments under heavy output + typing

## Validation Evidence (2026-02-28, suppression debounce + clear race follow-up)

Commands:

```bash
cd rust && cargo fmt --check
cd rust && cargo test --bin voiceterm confirmation_bytes_defer_claude_prompt_clear_until_periodic_tick -- --nocapture
cd rust && cargo test --bin voiceterm numeric_approval_choice_defer_claude_prompt_clear_until_periodic_tick -- --nocapture
cd rust && cargo test --bin voiceterm periodic_tasks_clear_stale_prompt_suppression_without_new_output -- --nocapture
cd rust && cargo test --bin voiceterm writer::state::tests:: -- --nocapture
cd rust && cargo test --bin voiceterm
cd rust && cargo build --release --bin voiceterm
```

Result summary:

- suppression-debounce event-loop tests: pass
- writer-state tests: pass (`28/28`)
- full `voiceterm` tests: pass (`1265/1265`)
- release build: pass
- manual IDE repro still required for final closure of `OVR-01/05/06/07`

## Next Work Sequence (strict single-issue loop)

1. Reproduce and close `OVR-04` (Codex+JetBrains startup HUD missing until typing) and confirm startup overlay appears without any keypress.
2. Reproduce and close `OVR-05` (Claude+Cursor approval option overwrite) with
   screenshot + terminal geometry capture.
3. Reproduce and close `OVR-07` (Claude+JetBrains option-3 clipping) by validating row-budget reservation while approval cards are active.
4. Reproduce and close `OVR-06` (Claude+Cursor stale border fragments behind approval cards) with
   writer redraw/pre-clear trace around tool-card transitions.
5. Reproduce and close `OVR-01` (Claude+JetBrains flash during thinking).
6. Re-run matrix smoke:
   - JetBrains: Claude + Codex
   - Cursor: Claude + Codex
7. Only after matrix passes, proceed to unrelated UX/tooling tasks.

## Guardrails

1. Keep backend-host policy explicit (`runtime_compat` + writer terminal family),
   not implicit global behavior.
2. Keep suppression transitions idempotent and clear-before-redraw.
3. Do not merge prompt-related changes without targeted tests for:
   - suppression detect
   - suppression release
   - startup/resume redraw with unavailable terminal geometry

## New Evidence (2026-02-27, user repro)

Observed in Cursor + Claude during `Tool use` approval flow:

1. HUD is mostly suppressed as expected.
2. Residual HUD border segments (`═`, corner/border fragments) remain in the
   upper tool-card area.
3. Prompt options remain readable in this capture, but stale fragments indicate
   an incomplete clear/repaint window under extended tool output.

Interpretation:

- This is not primarily a prompt-detection miss; it is a writer clear/redraw
  synchronization artifact during suppression transitions under continuous tool output.

## New Evidence (2026-02-27, user repro #2)

Observed in JetBrains + Claude during `Bash command` approval flow:

1. Approval card text is visible, but only options 1 and 2 are reliably shown.
2. Option 3 (`No`) is clipped/hidden at the bottom where HUD rows are present.
3. HUD remains visible instead of fully yielding prompt-safe rows for this card.

Interpretation:

- This is a prompt-safe row-budget failure for JetBrains+Claude approval cards
  (insufficient reserved rows while approval UI is active), separate from Cursor stale-fragment behavior.

## New Evidence (2026-02-28, user repro #3)

Observed in Cursor + Claude during normal composer typing (no approval card):

1. HUD is visible immediately after startup.
2. User types one key (for example `d`) in the Claude composer.
3. HUD disappears right after the keypress.

Interpretation:

- This appears to be a Claude+Cursor suppression/redraw-state transition during
  normal typing, not only during approval cards.
- We need transition-level logs to prove whether this is:
  - false prompt-suppression activation, or
  - writer redraw deferral after backend cursor-line mutation.

## Diagnostics Instrumentation Attempt (2026-02-28, in progress)

Added a gated tracing path for this exact failure mode:

1. New env flag: `VOICETERM_DEBUG_CLAUDE_HUD=1`.
2. `event_loop/prompt_occlusion.rs` now logs:
   - suppression transition `false -> true` / `true -> false`
   - suppression trigger reason (`tool-activity`, `explicit approval hint`,
     rolling-detector activate/release, input-resolution candidate)
   - compact output/input byte previews for repro correlation.
3. `writer/state.rs` now logs for Claude+Cursor:
   - PTY chunk classification (`may_scroll`, `preclear`, redraw-force flags)
   - redraw deferral decisions during typing hold
   - redraw commit events (banner/overlay/status state).

Expected outcome:

- Repro logs should show a linear keypress trace (`input` -> `pty output` ->
  `suppression/redraw decision`) so we can identify the precise branch that
  hides the HUD after typing.

## Current Status Snapshot (2026-02-28)

This snapshot is the anti-cycle baseline for the next passes.

### What is currently improved (do not regress)

1. Claude keypress-triggered immediate flash/disappear behavior is significantly reduced versus earlier passes.
2. Approval-card suppression behavior is more stable than initial MP-226 repros.
3. Prompt suppression transitions are now observable in logs (`VOICETERM_DEBUG_CLAUDE_HUD=1`).

### What is still broken (active blockers)

1. Cursor + Claude can still show stale HUD block fragments inside transcript content (mid-screen border/text artifacts).
2. Cursor + Claude can still show content/HUD overwrite collisions under heavy wrapped output.
3. Regression risk remains high: fixes in one lane can reintroduce flicker or keypress behavior regressions in another lane.

## Anti-Cycle Execution Contract (Required For Next Attempt)

### Attempt goal

Fix stale mid-screen HUD block/overwrite artifacts **without** reintroducing:
- keypress flicker/disappear regressions
- keyboard input/navigation regressions

### Locked surfaces for this attempt (must not change)

1. Prompt-suppression pattern list and semantic triggers (`claude_prompt_detect` matching rules).
2. Keyboard input routing semantics in `event_loop/input_dispatch.rs`.
3. Typing-hold timing values unless evidence proves timing is root cause.

### Allowed surfaces for this attempt

1. Writer anchor/clear/repaint sequencing (`writer/state.rs`, `writer/render.rs`).
2. Geometry reconciliation/sync handoff (`event_loop/periodic_tasks.rs`, writer resize handling).
3. Stale-frame cleanup policy that is explicitly bounded to Cursor+Claude anchor drift.

### Stop conditions (declare failure, do not widen scope)

1. Any change that reintroduces keypress flicker/disappear in Cursor+Claude.
2. Any change that breaks keyboard navigation/editing flows.
3. Any fix requiring simultaneous modifications across suppression logic + keyboard routing + writer timing in one pass.

If any stop condition hits: revert that attempt scope and start a new constrained attempt.

## Attempt Ledger Template (Use Every Pass)

Append one entry per attempt:

1. `Attempt ID` (for example `A1-anchor-clear`, `A2-geometry-sync`).
2. `Hypothesis` (single root-cause statement).
3. `Changed files` (exact list).
4. `No-regression checks` (keypress flicker, keyboard navigation, approval-card visibility).
5. `Result` (`pass`, `partial`, `fail`) with screenshot + log evidence refs.
6. `Next decision` (`promote`, `rollback`, `new constrained attempt`).

This ledger is mandatory to prevent repeating previously failed mixed-scope fixes.

## Attempt Ledger

### A1-tool-activity-false-positive (2026-02-28)

1. Hypothesis:
   Tool-activity suppression is overmatching plain transcript headings
   (`Bash Commands:` / `Web Searches:`), causing non-approval HUD suppression
   churn and downstream redraw/overwrite artifacts during normal typing/output.
2. Changed files:
   - `rust/src/bin/voiceterm/event_loop/prompt_occlusion.rs`
3. Change summary:
   - Tightened `chunk_contains_tool_activity_hint(...)`:
     - `starts_with(\"bash command\")` -> exact `== \"bash command\"`
     - narrowed `more tool use/call` detection to explicit `+N` patterns
     - kept explicit runtime tool signatures (`Bash(...)`, `Web Search(...)`).
   - Added regression tests to ensure plain transcript headings do not trigger suppression.
4. No-regression checks executed:
   - `cd rust && cargo test --bin voiceterm event_loop::prompt_occlusion::tests:: -- --nocapture`
   - `cd rust && cargo test --bin voiceterm handle_output_chunk_tool_activity_suppresses_hud_until_quiet_window -- --nocapture`
5. Result:
   - `partial` (code/tests pass; manual repro validation still pending).
6. Next decision:
   - Run manual Claude+Cursor repro with `VOICETERM_DEBUG_CLAUDE_HUD=1`.
   - If overwrite/min-hud disappearance persists, proceed to `A2-anchor-clear`
     constrained to writer geometry/clear sequencing only.

### A2-anchor-clear-and-idle-repair (2026-02-28)

1. Hypothesis:
   Two independent writer issues are causing current regressions:
   - stale old-banner anchors are not always scrubbed when frame anchor drifts
     (leaving duplicated/overwritten HUD blocks in transcript content),
   - minimal HUD can be clobbered by Cursor+Claude typing output without a
     follow-up redraw when no scroll/CSI mutation classifier is triggered.
2. Changed files:
   - `rust/src/bin/voiceterm/writer/render.rs`
   - `rust/src/bin/voiceterm/writer/state.rs`
   - (paired with A1 scope) `rust/src/bin/voiceterm/event_loop/prompt_occlusion.rs`
3. Change summary:
   - Added explicit anchor-clear helper `clear_status_banner_at(...)` in writer render path.
   - Writer now tracks `banner_anchor_row` and clears old anchor rows when anchor changes.
   - Added low-rate Cursor+Claude typing repair path:
     `UserInputActivity` schedules a short delayed repair redraw so minimal HUD
     recovers after typing bursts even when output classifier does not mark
     scroll/CSI mutation damage.
4. No-regression checks executed:
   - `cd rust && cargo test --bin voiceterm event_loop::prompt_occlusion::tests:: -- --nocapture`
   - `cd rust && cargo test --bin voiceterm writer::render::tests:: -- --nocapture`
   - `cd rust && cargo test --bin voiceterm writer::state::tests:: -- --nocapture`
5. Result:
   - `partial` (automated checks pass; manual Cursor+Claude validation pending).
6. Next decision:
   - Re-run your exact screenshot repro sequence (parallel web/bash tool output + typing).
   - If duplicate/overwrite persists, move to `A3-geometry-trace` and capture
     per-frame rows/anchor transitions before any further behavior changes.

### A2.1-minimal-hud-typing-non-defer (2026-02-28)

1. Hypothesis:
   Cursor+Claude typing-hold redraw deferral is too aggressive for minimal HUD
   (`banner_height == 1`), allowing one-row HUD clobber to persist until an
   unrelated control/event redraw occurs.
2. Changed files:
   - `rust/src/bin/voiceterm/writer/state.rs`
3. Change summary:
   - Kept typing-hold deferral for full HUD behavior.
   - Added a minimal-HUD recovery exception: when Cursor+Claude has an active
     one-row HUD, non-urgent redraw is no longer deferred during typing hold.
4. No-regression checks executed:
   - `cd rust && cargo test --bin voiceterm writer::state::tests::maybe_redraw_status_defers_non_urgent_redraw_while_user_typing_in_cursor_claude -- --nocapture`
   - `cd rust && cargo test --bin voiceterm writer::state::tests::maybe_redraw_status_does_not_defer_minimal_hud_recovery_in_cursor_claude -- --nocapture`
   - `cd rust && cargo test --bin voiceterm writer::state::tests::user_input_activity_schedules_cursor_claude_repair_redraw -- --nocapture`
   - `cd rust && cargo build --bin voiceterm`
5. Result:
   - `partial` (automated checks pass; manual validation pending).
6. Next decision:
   - Validate minimal-HUD typing stability with latest local binary.
   - If full-HUD overwrite duplicates persist independently, continue with
     `A3-geometry-trace` (anchor/rows sequence capture only).

### A2.2-cursor-claude-transition-cause-tracing (2026-02-28)

1. Hypothesis:
   We are still cycling because logs do not currently explain *why* writer
   transitions between `banner_height` states while typing in Cursor+Claude.
2. Changed files:
   - `rust/src/bin/voiceterm/writer/state.rs`
3. Change summary:
   - Added Claude+Cursor debug logs (gated by `VOICETERM_DEBUG_CLAUDE_HUD=1`)
     for:
     - `UserInputActivity` scheduling (`repair_due_in_ms`)
     - enhanced-status render decisions (`prev/next banner height`,
       `hud_style`, `prompt_suppressed`, message preview)
     - redraw commits with transition flags
       (`changed_banner_height`, `changed_hud_style`,
       `changed_prompt_suppressed`).
   - Fixed trace accounting so `changed_hud_style` and
     `changed_prompt_suppressed` are computed against pre-apply state.
4. No-regression checks executed:
   - `cd rust && cargo fmt --all`
   - `cd rust && cargo test --bin voiceterm writer::state::tests:: -- --nocapture`
   - `cd rust && cargo build --bin voiceterm`
5. Result:
   - `partial` (instrumentation landed and local repro logs are now causal).
   - Controlled local Cursor+Claude repro with `d`, `Ctrl+U`, `d` showed:
     - no `suppression candidate` lines in the run,
     - `prompt_suppressed=false` during typing transitions,
     - `banner_height 4 -> 1` tied to explicit `hud_style Full -> Minimal`
       transition,
     - `banner_height 0` only on shutdown in this run.
6. Next decision:
   - Use new causal logs on the user's real repro sequence (parallel tool output
     + typing) to determine whether disappearance is:
     - prompt suppression (`prompt_suppressed=true`), or
     - writer repaint race with `prompt_suppressed=false`.
   - If still `prompt_suppressed=false`, proceed with constrained
     `A3-writer-repaint-race` (no prompt-detector changes).

### A2.3-cursor-claude-geometry-anchor-trace-and-stress (2026-02-28)

1. Hypothesis:
   Remaining overwrite/vanish reports may be geometry/anchor drift under Cursor
   redraw pressure, not prompt suppression.
2. Changed files:
   - `rust/src/bin/voiceterm/writer/state.rs`
3. Change summary:
   - Extended Claude+Cursor debug logs with geometry/anchor fields:
     - user input activity now logs `rows`, `cols`, `banner_height`,
       `anchor_row`
     - enhanced-status decisions now log `rows`, `cols`, `prev_anchor_row`,
       `next_anchor_row`
     - redraw commits now log `rows`, `cols`, `anchor_row`
   - This makes wrong-row/mid-screen HUD placement diagnosable from logs alone.
4. No-regression checks executed:
   - `cd rust && cargo fmt --all`
   - `cd rust && cargo test --bin voiceterm writer::state::tests:: -- --nocapture`
   - `cd rust && cargo build --bin voiceterm`
5. Result:
   - `partial` (instrumentation + stress harness green locally).
   - Automated 4-session Cursor+Claude stress loop results (`expect` harness):
     - `suppression_candidate=0`
     - `suppression_transition=0`
     - `repair_redraw_fired=4`
     - `sessions=4`
     - `suspicious_sessions=0` (no `banner_height=0` before exit windows)
     - sampled transitions kept stable geometry in this environment:
       `rows=24`, `cols=80`, anchors `21 -> 24` for `Full -> Minimal`.
6. Next decision:
   - Run same tracing on user real-world Cursor repro where overwrite appears.
   - If geometry/anchor stays stable while visuals still fail, move to
     constrained repaint ordering fix (`A3-writer-repaint-race`).

### A2.4-cursor-tool-activity-false-suppression-breaker (2026-02-28)

1. Hypothesis:
   Cursor+Claude keypress-hide regressions are caused by non-rolling
   tool-activity hint matches (for example `Web Search(...)` redraw text)
   engaging prompt suppression in normal composer flow.
2. Changed files:
   - `rust/src/bin/voiceterm/event_loop/prompt_occlusion.rs`
3. Change summary:
   - Kept tool-activity hold-window extension, but restricted
     **tool-activity-only suppression engagement** to rolling-detector hosts
     (JetBrains path), so Cursor transcript redraw text can no longer
     re-hide HUD on ordinary typing.
   - Added non-rolling numbered approval-card hint detection (`1/2/3` + yes/no
     semantics) so Cursor still suppresses HUD for real approval cards even
     without full approval prose.
   - Added debug marker when non-rolling hosts intentionally ignore
     tool-activity-only suppression candidates.
4. No-regression checks executed:
   - `cd rust && cargo fmt --all`
   - `cd rust && cargo test --bin voiceterm prompt_occlusion -- --nocapture`
   - `cd rust && cargo test --bin voiceterm confirmation_bytes_defer_claude_prompt_clear_until_periodic_tick -- --nocapture`
   - `cd rust && cargo build --bin voiceterm`
5. Result:
   - `partial` (local tests/build pass; user environment manual repro pending).
6. Next decision:
   - Re-run user Cursor+Claude typing repro and confirm no immediate HUD hide
     after first keypress.
   - If hide still occurs, inspect whether any `suppression transition false -> true`
     line appears near keypress. If none, proceed to constrained writer redraw
     race fix (`A3-writer-repaint-race`).

### A2.5-one-shot-chained-repro-and-log-tail (2026-02-28)

1. Hypothesis:
   The updated non-rolling suppression policy should prevent keypress-triggered
   HUD suppression in ordinary Cursor+Claude typing.
2. Changed files:
   - none (execution/evidence only)
3. Run summary:
   - Executed one chained command sequence end-to-end:
     - build
     - clear temp log
     - run `voiceterm --logs --claude` with `VOICETERM_DEBUG_CLAUDE_HUD=1`
     - inject typed key
     - quit
     - run `rg ... | tail`
4. Evidence snapshot:
   - No `suppression candidate` or `suppression transition` matches were emitted
     in this run-tail filter.
   - Repeated `user input activity` + `redraw committed` traces stayed at
     `prompt_suppressed=Some(false)` with stable full-HUD anchor rows.
5. Result:
   - `partial` (local one-shot repro + logging path behaved as expected; user
     real-session repro is still the source of truth for closure).
6. Next decision:
   - Run the same one-shot flow in the user’s exact failing interaction path.
   - If suppression lines remain absent while HUD still disappears/overwrites,
     escalate to writer-only repaint ordering investigation (`A3`).

### A2.6-preclear-full-redraw-enforcement (2026-02-28)

1. Hypothesis:
   Cursor+Claude pre-clear transitions can blank HUD rows when the follow-up
   redraw reuses line-diff cache (`previous_lines`) against stale terminal state.
2. Changed files:
   - `rust/src/bin/voiceterm/writer/state.rs`
3. Change summary:
   - Cursor+Claude pre-clear path now explicitly sets
     `display.force_full_banner_redraw = true` together with
     `force_redraw_after_preclear = true`.
   - Added transition draw guard so any redraw with
     `force_redraw_after_preclear` disables previous-line diff reuse and forces
     full banner repaint.
   - Added explicit debug trace:
     `transition redraw mode: full|line-diff (...)`
   - Added unit regression helper coverage:
     `transition_redraw_after_preclear_disables_previous_line_diff`.
4. No-regression checks executed:
   - `cd rust && cargo fmt --all`
   - `cd rust && cargo test --bin voiceterm writer::state::tests:: -- --nocapture`
   - `cd rust && cargo test --bin voiceterm writer::state::tests::transition_redraw_after_preclear_disables_previous_line_diff -- --nocapture`
   - `cd rust && cargo build --bin voiceterm`
5. Result:
   - `partial` (writer regression guard and build/tests pass locally; manual
     Cursor+Claude failing-path confirmation still required).
6. Next decision:
   - Re-run user failing path with high-output Claude tool activity + typing.
   - Confirm `transition redraw mode: full` appears on pre-clear frames.
   - If visual overwrite remains with full transition redraws, move to
     writer-only ordering/flush investigation (`A3-writer-repaint-race`).

### A2.7-non-rolling-split-approval-window-and-repair-deadline-hardening (2026-02-28)

1. Hypothesis:
   Cursor non-rolling suppression still misses approval cards when Claude emits
   prompt prose and numbered options in separate chunks, and one-row HUD repair
   can still be skipped when a future repair deadline is cleared by an unrelated
   redraw before the deadline fires.
2. Changed files:
   - `rust/src/bin/voiceterm/event_state.rs`
   - `rust/src/bin/voiceterm/main.rs`
   - `rust/src/bin/voiceterm/event_loop/tests.rs`
   - `rust/src/bin/voiceterm/event_loop/prompt_occlusion.rs`
   - `rust/src/bin/voiceterm/writer/state.rs`
   - `dev/active/MASTER_PLAN.md`
   - `dev/audits/2026-02-27-terminal-overlay-regression-audit.md`
3. Change summary:
   - Added a short ANSI-stripped non-rolling approval rolling window (bounded
     bytes + stale-time reset) and evaluate approval hints against both:
     - current chunk (`chunk_*`)
     - rolling window tail (`window_*`)
   - Added debug traces for non-rolling approval scans and candidate source
     attribution so future repros show *why* suppression did/did not engage.
   - Expanded numbered approval detection to include explicit two-option cards
     (`1. Yes` / `2. No`) without requiring option 3 in the same chunk.
   - Cleared the non-rolling approval window on suppression release and on
     prompt-resolution input to prevent stale-card relatch loops.
   - Hardened Cursor+Claude writer repair scheduling so:
     - repair can schedule when enhanced status is pending (not only already displayed),
     - future repair deadlines survive unrelated redraws until due.
4. No-regression checks executed:
   - `cd rust && cargo fmt --all`
   - `cd rust && cargo test --bin voiceterm event_loop::prompt_occlusion::tests:: -- --nocapture`
   - `cd rust && cargo test --bin voiceterm writer::state::tests:: -- --nocapture`
   - `cd rust && cargo test --bin voiceterm confirmation_bytes_defer_claude_prompt_clear_until_periodic_tick -- --nocapture`
   - `cd rust && cargo test --bin voiceterm numeric_approval_choice_defer_claude_prompt_clear_until_periodic_tick -- --nocapture`
   - `cd rust && cargo test --bin voiceterm periodic_tasks_clear_stale_prompt_suppression_without_new_output -- --nocapture`
   - `cd rust && cargo build --bin voiceterm`
5. Result:
   - `partial` (all targeted build/tests pass; user’s exact Cursor+Claude manual
     repro sequence still required to close OVR-08/09/10).
6. Next decision:
   - Run one real failing path with `VOICETERM_DEBUG_CLAUDE_HUD=1` and verify:
     - non-rolling scan lines include `chunk_*`/`window_*` source booleans,
     - suppression transitions occur only on real approval cards,
     - no “disappear until refresh” one-row HUD events during normal typing.

### A2.8-cursor-non-rolling-release-gate-and-row-budget-tracing (2026-02-28)

1. Hypothesis:
   Cursor+Claude overlap/disappear regressions persist because non-rolling
   suppression can release/re-arm without stable prompt-context evidence and we
   lacked row-budget traces proving when PTY reserved rows diverge from expected
   HUD spacing during approval/tool flows.
2. Changed files:
   - `rust/src/bin/voiceterm/event_loop/prompt_occlusion.rs`
   - `rust/src/bin/voiceterm/runtime_compat.rs`
   - `rust/src/bin/voiceterm/terminal.rs`
   - `dev/active/MASTER_PLAN.md`
   - `dev/audits/2026-02-27-terminal-overlay-regression-audit.md`
3. Change summary:
   - Added non-rolling prompt-context fallback (`Tool use`, `Claude wants to`,
     `What should Claude do instead?`) so suppression/latch decisions can still
     engage when backend labels are missing or normalized unexpectedly.
   - Tightened non-rolling release: suppression now requires explicit
     input-resolution arming plus drained approval window (debounce-only release
     no longer unsuppresses while card context is still live).
   - Added non-rolling approval-window max-age expiry to prevent stale window
     latches across long idle spans.
   - Increased Cursor Claude extra gap rows (`8 -> 10`) and added
     `apply_pty_winsize` debug traces showing backend/mode/rows/cols/reserved
     rows/PTY rows/hud style/suppression state per resize path.
4. No-regression checks executed:
   - `cd rust && cargo fmt --all`
   - `cd rust && cargo test --bin voiceterm event_loop::prompt_occlusion::tests:: -- --nocapture`
   - `cd rust && cargo test --bin voiceterm writer::state::tests:: -- --nocapture`
   - `cd rust && cargo test --bin voiceterm`
   - `cd rust && cargo build --bin voiceterm`
   - `python3 dev/scripts/devctl.py check --profile ci`
5. Result:
   - `partial` (all automated checks pass; user-side Cursor+Claude manual repro
     remains required to confirm `OVR-05/08/09/10` closure).
   - Pseudo-TTY scripted repro (`type d`, `Enter`, `Ctrl+C`) emitted:
     - no suppression candidates/transitions
     - stable redraw commits at `banner_height=4`, `prompt_suppressed=false`
     - row-budget trace `reserved_rows=14` (`Full HUD 4 + Cursor Claude gap 10`)
6. Next decision:
   - Run one user repro with `VOICETERM_DEBUG_CLAUDE_HUD=1`, then inspect:
     - suppression triggers (`explicit`/`numbered`/`tool-activity ignored`)
     - suppression transitions
     - row-budget traces from `apply_pty_winsize` (`reserved_rows`, `pty_rows`)
     - redraw commits (`rows`, `cols`, `anchor_row`)
   - If overlap persists while suppression remains correctly gated, proceed to
     constrained writer-only placement change (fixed bottom offset floor for
     long approval/tool blocks in Cursor host path).

### A2.9-high-confidence-approval-guard-and-nonrolling-test-coverage (2026-02-28)

1. Hypothesis:
   Approval-card suppression can still fail in real Cursor sessions if backend
   label routing is noisy, because non-rolling suppression latched only when
   `prompt_guard_enabled` was true from backend/context markers.
2. Changed files:
   - `rust/src/bin/voiceterm/event_loop/prompt_occlusion.rs`
   - `rust/src/bin/voiceterm/event_loop/tests.rs`
3. Change summary:
   - Promoted explicit/numbered approval hints into `prompt_guard_enabled` so
     high-confidence approval cards suppress HUD even when backend label checks
     are temporarily unavailable.
   - Extended debug output chunk logging with `backend_label` and
     `prompt_guard` booleans to make guard-path decisions obvious in runtime
     traces.
   - Added deterministic non-rolling test coverage using a thread-local rolling
     detector override (test-only), avoiding global env mutation races:
     - `nonrolling_explicit_approval_card_suppresses_without_backend_label`
     - `nonrolling_tool_activity_hint_does_not_suppress_without_approval_card`
4. No-regression checks executed:
   - `cd rust && cargo fmt --all`
   - `cd rust && cargo test --bin voiceterm nonrolling_explicit_approval_card_suppresses_without_backend_label -- --nocapture`
   - `cd rust && cargo test --bin voiceterm nonrolling_tool_activity_hint_does_not_suppress_without_approval_card -- --nocapture`
   - `cd rust && cargo test --bin voiceterm numeric_approval_choice_defer_claude_prompt_clear_until_periodic_tick -- --nocapture`
   - `python3 dev/scripts/devctl.py check --profile ci`
5. Result:
   - `partial` (all automated checks pass; real Cursor+Claude manual repro is
     still required for closure because the failing path depends on live Claude
     approval/tool output cadence).
6. Next decision:
   - Run one real failing Cursor+Claude sequence and confirm logs now show:
     - `backend_label="<...>"` for every relevant output chunk
     - `prompt_guard=true` on approval-card chunks even if backend guard is false
     - suppression transition when approval card appears
   - If suppression still does not engage on real card output, add raw
   ANSI-stripped chunk dump capture around approval UI boundaries and tighten
   numbered-option normalization against Cursor styling escapes.

### A2.10-stress-harness-fidelity-plus-release-arm-and-transition-race-hardening (2026-03-01)

1. Hypothesis:
   We were still cycling because two different failures were mixed together:
   - non-rolling release-arm consumed too early from weak post-input chunks,
   - stress harness counted stale scrollback markers as active overlap/missing HUD.
   A writer transition race under typing-hold also delayed suppression-state
   redraws after `ClearStatus -> EnhancedStatus`.
2. Changed files:
   - `rust/src/bin/voiceterm/event_loop/prompt_occlusion.rs`
   - `rust/src/bin/voiceterm/event_loop/tests.rs`
   - `rust/src/bin/voiceterm/writer/state.rs`
   - `dev/scripts/tests/claude_hud_stress.py`
3. Change summary:
   - Added `chunk_contains_substantial_non_prompt_activity(...)` and gated
     non-rolling release-arm consumption so tiny echo/control chunks no longer
     clear approval context.
   - Added non-rolling relatch deferral while release-armed when only
     window-stale approval hints remain (no fresh chunk markers).
   - Added targeted tests:
     - `substantial_non_prompt_activity_ignores_choice_echo`
     - `substantial_non_prompt_activity_detects_post_approval_output`
     - `nonrolling_release_arm_defers_on_echo_chunk_until_substantial_output`
   - Hardened writer typing-hold urgency detection for suppression transitions,
     including post-`ClearStatus` transition updates where display snapshot is
     temporarily `None`.
   - Added writer regression tests:
     - `cursor_claude_suppression_transition_bypasses_typing_hold_deferral`
     - `cursor_claude_post_clear_enhanced_status_bypasses_typing_hold_deferral`
   - Stress harness now evaluates markers from visible viewport rows (not full
     scrollback) and includes `[back` as a minimal-HUD marker.
4. No-regression checks executed:
   - `cd rust && cargo test --bin voiceterm substantial_non_prompt_activity_detects_post_approval_output -- --nocapture`
   - `cd rust && cargo test --bin voiceterm substantial_non_prompt_activity_ignores_choice_echo -- --nocapture`
   - `cd rust && cargo test --bin voiceterm nonrolling_release_arm_defers_on_echo_chunk_until_substantial_output -- --nocapture`
   - `cd rust && cargo test --bin voiceterm nonrolling_stale_explicit_text_does_not_retrigger_suppression -- --nocapture`
   - `cd rust && cargo test --bin voiceterm cursor_claude_suppression_transition_bypasses_typing_hold_deferral -- --nocapture`
   - `cd rust && cargo test --bin voiceterm cursor_claude_post_clear_enhanced_status_bypasses_typing_hold_deferral -- --nocapture`
   - `python3 -m py_compile dev/scripts/tests/claude_hud_stress.py`
5. Stress evidence artifacts:
   - `dev/reports/audits/claude_hud_stress/20260301T101457Z` (post release-arm gating)
   - `dev/reports/audits/claude_hud_stress/20260301T102006Z` (post writer urgency v1)
   - `dev/reports/audits/claude_hud_stress/20260301T102411Z` (post writer urgency v2)
   - `dev/reports/audits/claude_hud_stress/20260301T102858Z` (post writer idle-throttle transition bypass)
6. Result:
   - `partial`
   - Improvements:
     - deterministic release-arm logs now distinguish consumed vs deferred paths,
     - approval+HUD overlap frames reduced relative to earlier failing baselines.
   - Remaining:
     - intermittent approval frames still capture HUD row in stress runs
       (`approval_with_hud_frames` non-empty),
     - prolonged "HUD missing" flags still appear in stress summaries and need
       additional marker/visibility validation against writer redraw commits.
     - overlap counts remain non-deterministic run-to-run under the same prompt
       load (for example `2` frames in `20260301T102411Z` vs `6` in
       `20260301T102858Z`), so current fixes are not sufficient for closure.
7. Next decision:
   - Add a transition-safe hold policy for rapid consecutive approvals in
     Cursor+Claude (avoid unsuppress between adjacent approval cards).
   - Extend stress harness with line-position checks (bottom-row HUD anchor
     expectation) so "visible but text-clipped" and "actually absent" are
     measured separately.
   - Correlate frame timestamps to suppression transitions directly in summary
     output to remove manual log-frame mapping.

### A2.11-sticky-nonrolling-hold-and-frame-log-correlation (2026-03-01)

1. Hypothesis:
   Intermittent overlap persisted because non-rolling suppression could release
   between rapid consecutive approval cards. Stress summaries also lacked
   deterministic frame-to-log mapping, so overlap vs stale-marker cases were
   still mixed.
2. Changed files:
   - `rust/src/bin/voiceterm/event_state.rs`
   - `rust/src/bin/voiceterm/main.rs`
   - `rust/src/bin/voiceterm/event_loop/prompt_occlusion.rs`
   - `rust/src/bin/voiceterm/event_loop/tests.rs`
   - `dev/scripts/tests/claude_hud_stress.py`
3. Change summary:
   - Added non-rolling sticky suppression hold
     (`NON_ROLLING_CONSECUTIVE_APPROVAL_STICKY_HOLD_MS=850`) armed on approval
     input-resolution bytes (`Enter`, `1/2/3`, `y/n`, etc).
   - Non-rolling unsuppress path now blocks release while sticky hold is active
     even when approval window has already drained, preventing transient HUD
     re-appearance between back-to-back approval cards.
   - Hold state now clears explicitly when suppression is released.
   - Updated/added event-loop tests:
     - `nonrolling_stale_explicit_text_does_not_retrigger_suppression` (now
       validates hold before final unsuppress),
     - `nonrolling_release_arm_defers_on_echo_chunk_until_substantial_output`
       (now validates hold before final unsuppress),
     - `nonrolling_sticky_hold_covers_rapid_consecutive_approvals` (new).
   - Stress harness now captures per-frame epoch timestamps, adds bottom-row
     HUD visibility gating (`--hud-bottom-rows`), parses suppression-transition
     + redraw-commit log events, and emits frame-level correlation metadata and
     commit-correlated anomaly buckets.
4. No-regression checks executed:
   - `cd rust && cargo fmt --all`
   - `cd rust && cargo test --bin voiceterm nonrolling_ -- --nocapture`
   - `cd rust && cargo test --bin voiceterm substantial_non_prompt_activity_ -- --nocapture`
   - `python3 -m py_compile dev/scripts/tests/claude_hud_stress.py`
5. Stress execution note:
   - Local sandbox run attempt failed to keep a detached `screen` session
     (`No screen session found`), so this pass could not emit fresh stress
     artifacts from this environment.
6. Result:
   - `partial`
   - Runtime hold logic + correlation instrumentation are landed and covered by
     tests.
   - Fresh stress evidence is still required on a host where detached `screen`
     sessions can persist long enough to run the harness end-to-end.
7. Next decision:
   - Re-run `dev/scripts/tests/claude_hud_stress.py` in full-access terminal
     mode and compare:
     - `approval_with_hud_suppressed_commit_frames`
     - `hud_missing_unsuppressed_commit_frames`
     - frame-level `correlation.latest_redraw_prompt_suppressed` around each
       overlap candidate.
   - If overlap remains non-zero with suppressed redraw commits aligned, add a
     writer-side bottom-anchor assertion log on suppression transitions to prove
     row placement in the same timestamp window.

### A2.12-wrapped-approval-depth-and-mismatch-anomaly-tracing (2026-03-01)

1. Hypothesis:
   Approval prompts that include long wrapped option text/paths can exceed
   non-rolling scan depth, causing numbered-option detection misses and HUD
   overlap on later approval cards in Cursor+Claude runs.
2. Changed files:
   - `rust/src/bin/voiceterm/event_loop/prompt_occlusion.rs`
   - `rust/src/bin/voiceterm/event_loop/tests.rs`
   - `dev/active/MASTER_PLAN.md`
   - `dev/audits/2026-02-27-terminal-overlay-regression-audit.md`
3. Change summary:
   - Increased non-rolling approval window scan depth:
     - `NON_ROLLING_APPROVAL_WINDOW_SCAN_TAIL_BYTES`: `2048 -> 8192`
     - `NON_ROLLING_APPROVAL_WINDOW_INPUT_TAIL_BYTES`: `512 -> 2048`
     - numbered-card line scan: `12 -> 64` lines
   - Added runtime anomaly logging when explicit approval phrases are present
     but numbered-option matching fails on non-rolling hosts:
     - `[claude-hud-anomaly] explicit approval hint seen without numbered-match ...`
   - Added regression coverage for wrapped/long approval cards:
     - `numbered_approval_hint_detects_wrapped_long_option_cards`
     - `nonrolling_long_wrapped_approval_card_still_suppresses`
4. No-regression checks executed:
   - `cd rust && cargo test --bin voiceterm numbered_approval_hint_detects_wrapped_long_option_cards -- --nocapture`
   - `cd rust && cargo test --bin voiceterm nonrolling_long_wrapped_approval_card_still_suppresses -- --nocapture`
   - `cd rust && cargo test --bin voiceterm nonrolling_stale_explicit_text_does_not_retrigger_suppression -- --nocapture`
   - `cd rust && cargo test --bin voiceterm nonrolling_release_arm_defers_on_echo_chunk_until_substantial_output -- --nocapture`
   - `cd rust && cargo build --bin voiceterm`
5. Stress evidence artifacts:
   - `dev/reports/audits/claude_hud_stress/20260301T105025Z`
   - `dev/reports/audits/claude_hud_stress/20260301T104454Z`
6. Result:
   - `partial`
   - Local stress runs reported `anomaly_total=0` with repeated approvals.
   - New mismatch anomaly log had `0` hits in the latest run.
   - User-host manual repro remains authoritative for closure, especially for:
     - approval-card option rows still being visually obscured,
     - lingering transcript overwrite perception near final summary blocks.
7. Next decision:
   - Run one user-host repro with the same stress prompt and capture:
     - screenshot timestamps,
     - `suppression transition` lines,
     - `explicit approval hint seen without numbered-match` lines.
   - If mismatch anomaly remains zero while overlap still appears, shift next
     pass to writer row-placement policy (reserved-row floor / bottom anchor)
     rather than prompt detection.

## Operator Command Notes (macOS temp-path safe)

Use this exact path-safe command to avoid permission noise and wrapped-path errors:

```bash
LOG="$(python3 -c 'import tempfile,os;print(os.path.join(tempfile.gettempdir(),\"voiceterm_tui.log\"))')"
rg -n "claude-hud-debug|suppression candidate|scheduled cursor\+claude HUD repair redraw fired" "$LOG" | tail -n 200
```

For transition-cause tracing in Cursor+Claude runs, add:

```bash
LOG="$(python3 -c 'import tempfile,os;print(os.path.join(tempfile.gettempdir(),\"voiceterm_tui.log\"))')"
rg -n "user input activity|enhanced status render decision|redraw committed \(banner_height=.*hud_style=|suppression transition" "$LOG" | tail -n 200
```

For geometry/anchor tracing (latest instrumentation):

```bash
LOG="$(python3 -c 'import tempfile,os;print(os.path.join(tempfile.gettempdir(),\"voiceterm_tui.log\"))')"
rg -n "user input activity|enhanced status render decision|redraw committed \(rows=|suppression transition" "$LOG" | tail -n 200
```

For non-rolling suppression-path validation in Cursor+Claude:

```bash
LOG="$(python3 -c 'import tempfile,os;print(os.path.join(tempfile.gettempdir(),\"voiceterm_tui.log\"))')"
rg -n "suppression candidate: tool-activity hint|suppression candidate ignored: tool-activity hint on non-rolling host|suppression candidate: explicit approval hint|suppression candidate: numbered approval hint|suppression transition" "$LOG" | tail -n 240
```

For transition redraw-mode validation (pre-clear frames must be full redraw):

```bash
LOG="$(python3 -c 'import tempfile,os;print(os.path.join(tempfile.gettempdir(),"voiceterm_tui.log"))')"
rg -n "transition redraw mode|user input activity|redraw committed \(rows=|suppression transition" "$LOG" | tail -n 260
```

Copy-safe Python temp-log path helper (avoids wrapped `python -c` syntax errors):

```bash
LOG="$(python3 - <<'PY'
import os
import tempfile
print(os.path.join(tempfile.gettempdir(), "voiceterm_tui.log"))
PY
)"
echo "$LOG"
```
