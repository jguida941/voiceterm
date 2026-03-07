//! Prompt-occlusion state transitions shared by event-loop input/output/periodic paths.
mod detection;
#[cfg(test)]
mod tests;

use super::*;
use crate::hud_debug::{claude_hud_debug_enabled, debug_bytes_preview};
use crate::prompt::occlusion_shared::{
    append_window_chunk, clear_window_state, retain_window_tail, snapshot_window_bytes,
    window_is_expired,
};
use crate::prompt::occlusion_signals as prompt_occlusion_signals;
use crate::runtime_compat;
use detection::{
    evaluate_output_chunk_signals, log_output_chunk_signals, OutputChunkSignals,
    NON_ROLLING_APPROVAL_CARD_SCAN_LINES, NON_ROLLING_APPROVAL_WINDOW_SCAN_TAIL_BYTES,
};
#[cfg(test)]
use std::cell::Cell;

const PROMPT_SUPPRESSION_RELEASE_DEBOUNCE_MS: u64 = 3000;
const STARTUP_READY_RELEASE_DEBOUNCE_MS: u64 = 700;
const TOOL_ACTIVITY_SUPPRESSION_HOLD_MS: u64 = 2200;
const NON_ROLLING_APPROVAL_WINDOW_MAX_BYTES: usize = 12 * 1024;
const NON_ROLLING_APPROVAL_WINDOW_STALE_MS: u64 = 1800;
const NON_ROLLING_APPROVAL_WINDOW_MAX_AGE_MS: u64 = 90_000;
const NON_ROLLING_APPROVAL_WINDOW_INPUT_TAIL_BYTES: usize = 2048;
const NON_ROLLING_CONSECUTIVE_APPROVAL_STICKY_HOLD_MS: u64 = 850;
const APPROVAL_SUPPRESSION_CANONICAL_FEED: &[u8] =
    b"This command requires approval\nDo you want to proceed?\n";
#[cfg(test)]
thread_local! {
    static TEST_ROLLING_DETECTOR_OVERRIDE: Cell<Option<bool>> = const { Cell::new(None) };
}

#[cfg(test)]
pub(super) fn set_test_rolling_detector_override(value: Option<bool>) {
    TEST_ROLLING_DETECTOR_OVERRIDE.with(|cell| cell.set(value));
}

fn append_non_rolling_approval_window(state: &mut EventLoopState, now: Instant, data: &[u8]) {
    append_window_chunk(
        &mut state.prompt.non_rolling_approval_window,
        &mut state.prompt.non_rolling_approval_window_last_update,
        now,
        data,
        NON_ROLLING_APPROVAL_WINDOW_STALE_MS,
        NON_ROLLING_APPROVAL_WINDOW_MAX_BYTES,
    );
}

fn clear_non_rolling_approval_window(state: &mut EventLoopState) {
    clear_window_state(
        &mut state.prompt.non_rolling_approval_window,
        &mut state.prompt.non_rolling_approval_window_last_update,
    );
    state.prompt.non_rolling_release_armed = false;
}

fn clear_non_rolling_sticky_hold(state: &mut EventLoopState) {
    state.prompt.non_rolling_sticky_hold_until = None;
}

fn retain_non_rolling_approval_window_tail(state: &mut EventLoopState, tail_bytes: usize) {
    retain_window_tail(&mut state.prompt.non_rolling_approval_window, tail_bytes);
}

fn maybe_expire_non_rolling_approval_window(state: &mut EventLoopState, now: Instant) {
    if window_is_expired(
        state.prompt.non_rolling_approval_window_last_update,
        now,
        NON_ROLLING_APPROVAL_WINDOW_MAX_AGE_MS,
    ) {
        clear_non_rolling_approval_window(state);
    }
}

fn non_rolling_approval_window_snapshot(state: &EventLoopState) -> Vec<u8> {
    snapshot_window_bytes(&state.prompt.non_rolling_approval_window)
}

fn extend_prompt_suppression_deadline(current: &mut Option<Instant>, candidate: Instant) {
    let next = match current {
        Some(existing) if *existing > candidate => *existing,
        _ => candidate,
    };
    *current = Some(next);
}

fn should_use_rolling_prompt_detector() -> bool {
    #[cfg(test)]
    {
        if let Some(override_value) = TEST_ROLLING_DETECTOR_OVERRIDE.with(Cell::get) {
            return override_value;
        }
        true
    }
    #[cfg(not(test))]
    {
        matches!(
            runtime_compat::detect_terminal_host(),
            runtime_compat::TerminalHost::JetBrains
        )
    }
}

/// Apply prompt suppression state and propagate dependent runtime side effects.
pub(super) fn apply_prompt_suppression(
    state: &mut EventLoopState,
    deps: &mut EventLoopDeps,
    suppressed: bool,
) {
    let was_suppressed = state.status_state.prompt_suppressed;
    if was_suppressed == suppressed {
        return;
    }
    if claude_hud_debug_enabled() {
        log_debug(&format!(
            "[claude-hud-debug] suppression transition {} -> {} (rows={}, cols={}, overlay={:?}, hud_style={:?})",
            was_suppressed,
            suppressed,
            state.ui.terminal_rows,
            state.ui.terminal_cols,
            state.ui.overlay_mode,
            state.status_state.hud_style
        ));
    }

    // Re-resolve geometry before changing PTY row budgets so suppress/unsuppress
    // transitions do not apply stale dimensions after IDE terminal reattach.
    let previous_rows = state.ui.terminal_rows;
    let previous_cols = state.ui.terminal_cols;
    state.ui.terminal_rows = crate::terminal::resolved_rows(state.ui.terminal_rows);
    state.ui.terminal_cols = crate::terminal::resolved_cols(state.ui.terminal_cols);
    if state.ui.terminal_rows != previous_rows || state.ui.terminal_cols != previous_cols {
        let _ = deps.writer_tx.send(WriterMessage::Resize {
            rows: state.ui.terminal_rows,
            cols: state.ui.terminal_cols,
        });
    }

    state.status_state.prompt_suppressed = suppressed;
    if !suppressed {
        clear_non_rolling_approval_window(state);
        clear_non_rolling_sticky_hold(state);
    }
    apply_pty_winsize(
        &mut deps.session,
        state.ui.terminal_rows,
        state.ui.terminal_cols,
        state.ui.overlay_mode,
        state.status_state.hud_style,
        state.status_state.prompt_suppressed,
    );
    // Clear before redraw so anchor transitions do not leave stale frame lines.
    let _ = deps.writer_tx.send(WriterMessage::ClearStatus);
    let _ = deps
        .writer_tx
        .send(WriterMessage::EnhancedStatus(state.status_state.clone()));
    if claude_hud_debug_enabled() {
        log_debug(&format!(
            "[claude-hud-debug] suppression dispatch: ClearStatus + EnhancedStatus (suppressed={}, hud_style={:?}, rows={}, cols={})",
            suppressed,
            state.status_state.hud_style,
            state.ui.terminal_rows,
            state.ui.terminal_cols
        ));
    }
    if state.status_state.mouse_enabled {
        update_button_registry(
            &deps.button_registry,
            &state.status_state,
            state.ui.overlay_mode,
            state.ui.terminal_cols,
            state.theme,
        );
    }
}

/// Feed PTY output into prompt tracking + occlusion detection and synchronize HUD suppression.
pub(super) fn feed_prompt_output_and_sync(
    state: &mut EventLoopState,
    timers: &mut EventLoopTimers,
    deps: &mut EventLoopDeps,
    now: Instant,
    data: &[u8],
) {
    let use_rolling_detector = should_use_rolling_prompt_detector();
    let backend_prompt_guard_enabled =
        runtime_compat::backend_supports_prompt_occlusion_guard(&deps.backend_label);

    // Phase 1: Update non-rolling approval window state from new data.
    if !use_rolling_detector {
        update_non_rolling_window_on_output(state, now, data);
    }
    let non_rolling_window = if !use_rolling_detector {
        Some(non_rolling_approval_window_snapshot(state))
    } else {
        None
    };

    // Phase 2: Evaluate all signal flags from the chunk + window.
    let signals = evaluate_output_chunk_signals(
        data,
        use_rolling_detector,
        backend_prompt_guard_enabled,
        non_rolling_window.as_deref(),
    );
    log_non_rolling_anomaly_if_needed(state, &signals, &non_rolling_window);
    log_output_chunk_signals(
        &signals,
        data,
        &deps.backend_label,
        state.status_state.prompt_suppressed,
        non_rolling_window.as_deref(),
    );

    // Phase 3: Apply suppression decisions based on computed signals.
    apply_suppression_from_chunk_signals(state, timers, deps, now, data, &signals);

    // Phase 4: Feed detector and sync.
    feed_detector_and_apply_latch(state, timers, deps, data, &signals);
    sync_prompt_suppression_from_detector(state, timers, deps, now);
    if signals.approval_hint_seen && !state.status_state.prompt_suppressed {
        log_debug(&format!(
            "[claude-hud-anomaly] prompt overlap risk: approval hint seen while HUD suppression is inactive (rolling={}, backend_label=\"{}\", explicit_chunk={}, explicit_window={}, numbered_chunk={}, numbered_window={}, rows={}, cols={}, hud_style={:?}, overlay={:?})",
            signals.use_rolling_detector,
            deps.backend_label,
            signals.explicit_approval_hint_chunk,
            signals.explicit_approval_hint_window,
            signals.numbered_approval_hint_chunk,
            signals.numbered_approval_hint_window,
            state.ui.terminal_rows,
            state.ui.terminal_cols,
            state.status_state.hud_style,
            state.ui.overlay_mode
        ));
    }
}

/// Update the non-rolling approval window with new output data.
fn update_non_rolling_window_on_output(state: &mut EventLoopState, now: Instant, data: &[u8]) {
    let explicit_hint = prompt_occlusion_signals::chunk_contains_explicit_approval_hint(data);
    let numbered_hint = prompt_occlusion_signals::chunk_contains_numbered_approval_hint(
        data,
        NON_ROLLING_APPROVAL_CARD_SCAN_LINES,
    );
    append_non_rolling_approval_window(state, now, data);
    if explicit_hint || numbered_hint {
        state.prompt.non_rolling_release_armed = false;
    } else if state.prompt.non_rolling_release_armed {
        if prompt_occlusion_signals::chunk_contains_substantial_non_prompt_activity(
            data,
            NON_ROLLING_APPROVAL_CARD_SCAN_LINES,
        ) {
            if claude_hud_debug_enabled() {
                log_debug(
                    "[claude-hud-debug] non-rolling release arm consumed: substantial post-input activity detected",
                );
            }
            clear_non_rolling_approval_window(state);
        } else if claude_hud_debug_enabled() {
            log_debug(
                "[claude-hud-debug] non-rolling release arm deferred: post-input chunk lacks substantial non-prompt activity",
            );
        }
    }
}

/// Log anomaly when explicit approval hint appears without numbered match in non-rolling mode.
fn log_non_rolling_anomaly_if_needed(
    state: &EventLoopState,
    signals: &OutputChunkSignals,
    non_rolling_window: &Option<Vec<u8>>,
) {
    if signals.use_rolling_detector
        || !signals.prompt_guard_enabled
        || !signals.explicit_approval_hint
        || signals.numbered_approval_hint
        || state.status_state.prompt_suppressed
    {
        return;
    }
    log_debug(&format!(
        "[claude-hud-anomaly] explicit approval hint seen without numbered-match in non-rolling mode (chunk_explicit={}, window_explicit={}, chunk_numbered={}, window_numbered={}, window_live={}, window_bytes={}, rows={}, cols={})",
        signals.explicit_approval_hint_chunk,
        signals.explicit_approval_hint_window,
        signals.numbered_approval_hint_chunk,
        signals.numbered_approval_hint_window,
        signals.non_rolling_live_approval_window_hint,
        non_rolling_window.as_ref().map_or(0, Vec::len),
        state.ui.terminal_rows,
        state.ui.terminal_cols
    ));
}

/// Apply suppression from tool activity or synchronized cursor rewrites.
fn apply_suppression_from_chunk_signals(
    state: &mut EventLoopState,
    timers: &mut EventLoopTimers,
    deps: &mut EventLoopDeps,
    now: Instant,
    _data: &[u8],
    signals: &OutputChunkSignals,
) {
    if !signals.saw_tool_activity && !signals.saw_synchronized_cursor_activity {
        return;
    }
    let rolling_fast_suppress_allowed = !signals.use_rolling_detector || signals.approval_hint_seen;
    if claude_hud_debug_enabled() {
        if signals.saw_synchronized_cursor_activity {
            log_debug("[claude-hud-debug] suppression candidate: synchronized cursor rewrite");
        } else {
            log_debug("[claude-hud-debug] suppression candidate: tool-activity hint");
        }
    }
    if rolling_fast_suppress_allowed || state.status_state.prompt_suppressed {
        extend_prompt_suppression_deadline(
            &mut timers.prompt_suppression_release_not_before,
            now + Duration::from_millis(TOOL_ACTIVITY_SUPPRESSION_HOLD_MS),
        );
    }
    // Tool-activity lines are noisy in Cursor transcript redraws and can
    // spuriously hide HUD while typing. Only rolling-detector hosts
    // (JetBrains) can engage suppression from tool-activity alone.
    if signals.use_rolling_detector {
        if rolling_fast_suppress_allowed && !state.status_state.prompt_suppressed {
            apply_prompt_suppression(state, deps, true);
        } else if claude_hud_debug_enabled() && !state.status_state.prompt_suppressed {
            log_debug(
                "[claude-hud-debug] suppression candidate ignored: synchronized/tool activity without approval hints",
            );
        }
    } else if claude_hud_debug_enabled() && !state.status_state.prompt_suppressed {
        log_debug(
            "[claude-hud-debug] suppression candidate ignored: tool-activity hint on non-rolling host",
        );
    }
}

/// Feed detector and apply non-rolling/rolling latch suppression.
fn feed_detector_and_apply_latch(
    state: &mut EventLoopState,
    timers: &mut EventLoopTimers,
    deps: &mut EventLoopDeps,
    data: &[u8],
    signals: &OutputChunkSignals,
) {
    state.prompt.tracker.feed_output(data);
    if signals.use_rolling_detector {
        let _ = state.prompt.occlusion_detector.feed_output(data);
        // Claude approval cards can arrive with styling/fragmentation that may
        // evade a single rolling parse pass. When explicit approval phrases are
        // paired with live choice markers, feed a canonical phrase so suppression
        // engages deterministically.
        if signals.prompt_guard_enabled
            && !state.prompt.occlusion_detector.should_suppress_hud()
            && signals.rolling_approval_hint_seen
        {
            if claude_hud_debug_enabled() {
                log_debug("[claude-hud-debug] suppression candidate: explicit approval hint (rolling detector canonical feed)");
            }
            let _ = state
                .prompt
                .occlusion_detector
                .feed_output(APPROVAL_SUPPRESSION_CANONICAL_FEED);
        }
    } else if signals.prompt_guard_enabled
        && signals.non_rolling_approval_hint
        && !(state.prompt.non_rolling_release_armed
            && !signals.explicit_approval_hint_chunk
            && !signals.numbered_approval_hint_chunk)
    {
        if claude_hud_debug_enabled() {
            if signals.explicit_approval_hint {
                log_debug(
                    "[claude-hud-debug] suppression candidate: explicit approval hint (non-rolling latch)",
                );
            }
            if signals.numbered_approval_hint {
                log_debug(
                    "[claude-hud-debug] suppression candidate: numbered approval hint (non-rolling latch)",
                );
            }
            log_debug(&format!(
                "[claude-hud-debug] suppression candidate source (non-rolling): explicit_chunk={}, explicit_window={}, numbered_chunk={}, numbered_window={}, window_live={}",
                signals.explicit_approval_hint_chunk,
                signals.explicit_approval_hint_window,
                signals.numbered_approval_hint_chunk,
                signals.numbered_approval_hint_window,
                signals.non_rolling_live_approval_window_hint
            ));
        }
        // Non-JetBrains Claude hosts (for example VS Code/Cursor integrated terminals)
        // are prone to noisy rolling-detector transitions while typing. Use an explicit
        // hint latch instead of rolling context in those hosts.
        extend_prompt_suppression_deadline(
            &mut timers.prompt_suppression_release_not_before,
            Instant::now() + Duration::from_millis(PROMPT_SUPPRESSION_RELEASE_DEBOUNCE_MS),
        );
        if !state.status_state.prompt_suppressed {
            apply_prompt_suppression(state, deps, true);
        }
    } else if claude_hud_debug_enabled()
        && state.prompt.non_rolling_release_armed
        && signals.non_rolling_approval_hint
        && !signals.explicit_approval_hint_chunk
        && !signals.numbered_approval_hint_chunk
    {
        log_debug(
            "[claude-hud-debug] suppression relatch deferred: release-armed state with window-only approval hints",
        );
    }
}

/// Reconcile runtime suppression state from the occlusion detector.
pub(super) fn sync_prompt_suppression_from_detector(
    state: &mut EventLoopState,
    timers: &mut EventLoopTimers,
    deps: &mut EventLoopDeps,
    now: Instant,
) {
    let use_rolling_detector = should_use_rolling_prompt_detector();
    if !use_rolling_detector {
        maybe_expire_non_rolling_approval_window(state, now);
    }
    let should_suppress_hud =
        use_rolling_detector && state.prompt.occlusion_detector.should_suppress_hud();
    let ready_marker_resolution_kind = if use_rolling_detector {
        state
            .prompt
            .occlusion_detector
            .take_ready_marker_resolution_kind()
    } else {
        None
    };
    if use_rolling_detector && should_suppress_hud {
        if claude_hud_debug_enabled() && !state.status_state.prompt_suppressed {
            log_debug("[claude-hud-debug] suppression engage: rolling detector active");
        }
        timers.prompt_suppression_release_not_before =
            Some(now + Duration::from_millis(PROMPT_SUPPRESSION_RELEASE_DEBOUNCE_MS));
        if !state.status_state.prompt_suppressed {
            apply_prompt_suppression(state, deps, true);
        }
        return;
    }

    if !state.status_state.prompt_suppressed {
        timers.prompt_suppression_release_not_before = None;
        clear_non_rolling_sticky_hold(state);
        return;
    }

    if matches!(
        ready_marker_resolution_kind,
        Some(crate::prompt::PromptType::StartupGuard)
    ) {
        // Startup-ready markers can arrive immediately before Claude emits
        // synchronized cursor rewrites in JetBrains. Releasing suppression
        // instantly here causes prompt-suppression flapping and PTY row-budget
        // thrash during startup/resize. Keep the normal debounce gate.
        extend_prompt_suppression_deadline(
            &mut timers.prompt_suppression_release_not_before,
            now + Duration::from_millis(STARTUP_READY_RELEASE_DEBOUNCE_MS),
        );
        if claude_hud_debug_enabled() {
            log_debug(
                "[claude-hud-debug] suppression release arm: startup guard ready marker (short debounce)",
            );
        }
    }

    if !use_rolling_detector && state.status_state.prompt_suppressed {
        if let Some(not_before) = timers.prompt_suppression_release_not_before {
            if now < not_before {
                return;
            }
        } else {
            // Non-rolling suppression requires an explicit release arm from
            // user approval input (Enter/1/2/3/y/n/etc).
            return;
        }
        let approval_window_snapshot = non_rolling_approval_window_snapshot(state);
        let approval_window_scan = crate::prompt::occlusion_shared::tail_slice(
            &approval_window_snapshot,
            NON_ROLLING_APPROVAL_WINDOW_SCAN_TAIL_BYTES,
        );
        let approval_window_still_active =
            prompt_occlusion_signals::chunk_contains_live_approval_card_hint(
                approval_window_scan,
                NON_ROLLING_APPROVAL_CARD_SCAN_LINES,
            );
        if approval_window_still_active {
            if claude_hud_debug_enabled() {
                log_debug(
                    "[claude-hud-debug] suppression hold: non-rolling approval window still populated",
                );
            }
            return;
        }
        if state
            .prompt
            .non_rolling_sticky_hold_until
            .is_some_and(|hold_until| now < hold_until)
        {
            if claude_hud_debug_enabled() {
                let remaining_ms = state
                    .prompt
                    .non_rolling_sticky_hold_until
                    .map(|hold_until| hold_until.saturating_duration_since(now).as_millis())
                    .unwrap_or(0);
                log_debug(&format!(
                    "[claude-hud-debug] suppression hold: sticky rapid-approval window active (remaining_ms={remaining_ms})",
                ));
            }
            return;
        }
        clear_non_rolling_sticky_hold(state);
        timers.prompt_suppression_release_not_before = None;
        if claude_hud_debug_enabled() {
            log_debug(
                "[claude-hud-debug] suppression release: non-rolling approval window drained after input",
            );
        }
        apply_prompt_suppression(state, deps, false);
        return;
    }

    if let Some(not_before) = timers.prompt_suppression_release_not_before {
        if now < not_before {
            return;
        }
    }
    timers.prompt_suppression_release_not_before = None;
    if state.status_state.prompt_suppressed {
        if claude_hud_debug_enabled() && !should_suppress_hud {
            log_debug(
                "[claude-hud-debug] suppression release: debounce elapsed and detector inactive",
            );
        }
        apply_prompt_suppression(state, deps, should_suppress_hud);
    }
}

/// Clear suppression after detector timeout while idle, without re-asserting suppression.
pub(super) fn clear_expired_prompt_suppression(
    state: &mut EventLoopState,
    timers: &mut EventLoopTimers,
    deps: &mut EventLoopDeps,
    now: Instant,
) {
    sync_prompt_suppression_from_detector(state, timers, deps, now);
}

/// Register raw input bytes with the detector; reconciliation is deferred to output/periodic ticks.
pub(super) fn register_prompt_resolution_candidate(
    state: &mut EventLoopState,
    timers: &mut EventLoopTimers,
    bytes: &[u8],
) {
    if !state.status_state.prompt_suppressed || bytes.is_empty() {
        return;
    }
    if should_use_rolling_prompt_detector() {
        let should_resolve = state
            .prompt
            .occlusion_detector
            .should_resolve_on_input(bytes);
        if claude_hud_debug_enabled() {
            log_debug(&format!(
                "[claude-hud-debug] input resolution candidate (rolling=true, resolve={}): \"{}\"",
                should_resolve,
                debug_bytes_preview(bytes, 48)
            ));
        }
        if should_resolve {
            state.prompt.occlusion_detector.on_user_input();
            clear_non_rolling_approval_window(state);
        }
        return;
    }
    let should_resolve =
        prompt_occlusion_signals::should_resolve_prompt_suppression_on_input_without_detector(
            bytes,
        );
    if claude_hud_debug_enabled() {
        log_debug(&format!(
            "[claude-hud-debug] input resolution candidate (rolling=false, resolve={}): \"{}\"",
            should_resolve,
            debug_bytes_preview(bytes, 48)
        ));
    }
    if should_resolve {
        let hold_until =
            Instant::now() + Duration::from_millis(NON_ROLLING_CONSECUTIVE_APPROVAL_STICKY_HOLD_MS);
        state.prompt.occlusion_detector.on_user_input();
        // Keep only the freshest approval window tail after input so release
        // decisions track currently visible approval lines instead of stale
        // historical prompt text.
        retain_non_rolling_approval_window_tail(
            state,
            NON_ROLLING_APPROVAL_WINDOW_INPUT_TAIL_BYTES,
        );
        state.prompt.non_rolling_release_armed = true;
        state.prompt.non_rolling_sticky_hold_until = Some(hold_until);
        if claude_hud_debug_enabled() {
            log_debug(&format!(
                "[claude-hud-debug] non-rolling sticky hold armed for rapid approvals (hold_ms={NON_ROLLING_CONSECUTIVE_APPROVAL_STICKY_HOLD_MS})",
            ));
        }
        timers.prompt_suppression_release_not_before = Some(Instant::now());
    }
}
