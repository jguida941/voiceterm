# Local Backlog (Reference Only)

This backlog is intentionally local-only, reference-only, and is not user-facing.
Local backlog items use `LB-*` IDs so they never collide with canonical `MP-*`
tracking in `dev/active/MASTER_PLAN.md`.

Shared repo-visible backlog note:
- Canonical shared backlog lives at [`../../backlog.md`](../../backlog.md).
- Keep this file for local/private scratch or deferred notes that should not
  become shared AI/runtime intake yet.

Execution authority note:
- Items in this file are not active execution state.
- To execute an item, promote it into `dev/active/MASTER_PLAN.md` as `MP-*`
  scope first.

## Priority: 
**Scheduled to fix Feb 16th. Somewhere in Version .70-80**
- [ ] LB-145 Eliminate startup cursor/ANSI escape artifacts shown in Cursor (Codex and Claude backends), with focus on the splash-screen teardown to VoiceTerm HUD handoff window where artifacts appear before full load.
- [ ] LB-146 Improve controls-row bracket styling so `[` `]` tokens track active theme colors and selected states use stronger contrast/readability (especially for arrow-mode focus visibility).
- [ ] LB-147 Fix Cursor-only mouse-mode scroll conflict: with mouse mode ON, chat/conversation scroll should still work in Cursor for both Codex and Claude backends; preserve current JetBrains behavior (works today in PyCharm/JetBrains), keep architecture/change scope explicitly Cursor-specific, and require JetBrains non-regression validation so the Cursor fix does not break JetBrains scrolling.
- [ ] LB-148 Re-audit displayed latency math against user-perceived responsiveness: validate short-vs-long utterance behavior with `latency_audit` traces, confirm whether `display_ms` should remain post-capture-only or expose additional timing breakdowns, and align formula/docs/tests with proven measurement semantics.
- [ ] LB-149 Investigate unexpected idle `codex-aarch64-apple-darwin` process fan-out in Activity Monitor when only a small number of Codex/VoiceTerm terminals are open (user report: ~3 idle terminals but many Codex processes); capture reproducible process trees and startup/shutdown traces, identify ownership/orphaning source, and define required cleanup or lifecycle guardrails.
- [ ] LB-151 Voice-mode recognition hardening for wake/send phrases: review voice logs with repeated spoken variants (`codex`, `codecs`, `cloud`, and close phonetic variants) plus repeated "hey send" utterances, measure miss vs false-positive rates, and tune wake/intent matching thresholds, phrase maps, and debounce windows for reliable trigger behavior without any yes/no confirmation prompt.
- [ ] LB-152 Voice macros mode reliability pass: run a focused validation matrix for voice macro invocation/end-to-end send flow in both cloud and local transcription paths, capture flaky recognition cases, and document required parser/matcher/test updates before promoting macro-mode defaults.
- [ ] LB-160 Voice macros hands-on testing session: walk through voice macro logs with Codex in a live debugging session, test each macro trigger end-to-end, identify and fix issues together, and validate the feature is ready for users before removing the "still in development" note from README.
- [ ] LB-161 Retire or migrate the transitional `devctl review-channel --action launch` bootstrap once the markdown bridge is no longer the canonical coordination path: when overlay-native/shared-screen review launch becomes the sanctioned entrypoint or `review_channel.md` marks the bridge inactive, either route the command to the new overlay-native launcher or delete the transitional bridge-gated launcher so it does not linger as a stale parallel control surface.
- [ ] LB-153 Add per-user pronunciation/alias profile for wake + command phrases (for example `codex`, `codecs`, `claude`, `cloud`) with weighted matching and correction-driven auto-learning from accepted/rejected transcripts.
- [ ] LB-154 Add explicit overlay voice-state machine (`command`, `dictation`, `sleep`) with persistent on-screen mode indicator plus low-friction transitions so normal speech is not misparsed as control commands.
- [ ] LB-155 Add wake-word/speech calibration wizard per microphone/environment (sensitivity + noise floor + phrase rehearsal), storing profile-specific thresholds and surfacing miss/false-trigger diagnostics in logs.
- [ ] LB-156 Add cross-provider intent router so one spoken command grammar maps cleanly to Codex and Claude backend actions, reducing provider-specific phrasing differences in day-to-day use.
- [ ] LB-157 Process orphan-prevention hardening: add startup/shutdown sweeps and watchdog checks so stale `cargo test --bin voiceterm` and detached `target/debug/deps/voiceterm-*` processes (`PPID=1`) are detected/reaped automatically, with an auditable `devctl` process-health command and CI/test-lane post-run orphan assertions.
- [ ] LB-158 Investigate startup overlay initialization gap in Cursor+Codex sessions: when launching VoiceTerm after login and entering Codex in Cursor, overlay/HUD can start in a not-loaded/blank state until later redraw. Capture reproducible logs/screenshots (`voiceterm --logs --codex`), verify first-frame geometry + redraw sequencing, and keep JetBrains non-regression validation in scope.
- [ ] LB-159 Terminal resize event leaks into transcript history mode: resize handler runs consolidated overlay/main-menu logic even when transcript history mode is active. Add mode guard so resize dispatch only triggers overlay/menu layout recalculation when the overlay is actually open; transcript history mode should handle resize independently without triggering overlay-specific paths.



## Possible features (Not Scheduled)
**Do not do this without explicit permission, some of this hasnt been decided on yet.**
- [ ] LB-016 Stress test heavy I/O for bounded-memory behavior.
  - **2026-03-05 finding:** Overlay stress test passed in Cursor terminal with 32 parallel tool calls (~20k+ lines of content), 3 async background agents completing at staggered intervals (30s–67s), and 25.5KB grep result auto-persisted to disk. No overflow or rendering artifacts observed. Writer thread's `recv_timeout(25ms)` + `try_recv()` drain loop handled async agent arrivals cleanly. The `height.min(rows).min(lines.len())` triple-clamp in `write_overlay_panel` (render.rs:383) and `saturating_sub()` arithmetic prevented panics. JetBrains testing pending.
- [ ] LB-150 Validate overlay rendering stability under heavy parallel output on JetBrains terminals (PyCharm/IntelliJ). Known fragile path: JetBrains+Claude during long parallel tool calls can cause HUD/transcript overlap at turn completion (README.md:209-214). JetBrains lacks scroll region support (DECSTBM) and relies on PTY row reduction instead. Confirm whether the "resize once" workaround is still needed or if current full-HUD-repaint + DEC-only cursor policy is sufficient. Cross-ref LB-016 stress test methodology.
- [ ] LB-031 Add PTY health monitoring for hung process detection.
- [ ] LB-032 Add retry logic for transient audio device failures.
- [ ] LB-033 Add benchmarks to CI for latency regression detection.
- [ ] LB-034 Add mic-meter hotkey for calibration.
- [ ] LB-037 Consider configurable PTY output channel capacity.
- [ ] LB-103 Add searchable command palette for settings/actions/macros with keyboard-first flow.
- [ ] LB-106 Add hybrid voice+keyboard transcript input panel for correction and selective send.
- [ ] LB-107 Add session dashboard with voice metrics (latency/WPM/error rate) and export path.
- [ ] LB-108 Prototype contextual autocomplete/suggestion dropdowns for macros/corrections.
- [ ] LB-109 Evaluate block-based voice command history UI against PTY/session constraints.
