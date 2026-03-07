//! Chunk-level signal evaluation and debug logging for prompt occlusion.
//!
//! Pure computation over byte slices with no event-loop state mutation.
//! The coordinator in the parent module owns all state transitions.

use crate::hud_debug::{claude_hud_debug_enabled, debug_bytes_preview};
use crate::prompt::occlusion_shared::tail_slice;
use crate::prompt::occlusion_signals as prompt_occlusion_signals;
use voiceterm::log_debug;

pub(super) const NON_ROLLING_APPROVAL_CARD_SCAN_LINES: usize = 64;
pub(super) const NON_ROLLING_APPROVAL_WINDOW_SCAN_TAIL_BYTES: usize = 8192;

/// All computed signal flags from a single output chunk, used by the
/// coordinator to decide suppression transitions and produce debug output.
#[derive(Debug)]
pub(super) struct OutputChunkSignals {
    pub(super) use_rolling_detector: bool,
    pub(super) backend_prompt_guard_enabled: bool,
    pub(super) prompt_guard_enabled: bool,
    pub(super) approval_hint_seen: bool,
    pub(super) rolling_approval_hint_seen: bool,
    pub(super) non_rolling_approval_hint: bool,
    pub(super) saw_tool_activity: bool,
    pub(super) saw_synchronized_cursor_activity: bool,
    pub(super) explicit_approval_hint: bool,
    pub(super) numbered_approval_hint: bool,
    pub(super) explicit_approval_hint_chunk: bool,
    pub(super) numbered_approval_hint_chunk: bool,
    pub(super) explicit_approval_hint_window: bool,
    pub(super) numbered_approval_hint_window: bool,
    pub(super) non_rolling_live_approval_window_hint: bool,
    pub(super) prompt_context_chunk: bool,
    pub(super) prompt_context_window: bool,
    pub(super) ignore_synchronized_candidate: bool,
    pub(super) non_rolling_window_bytes: usize,
}

/// Evaluate all signal flags from an output chunk and optional non-rolling
/// approval window snapshot. No state mutation — the result drives coordinator
/// decisions.
#[must_use]
pub(super) fn evaluate_output_chunk_signals(
    data: &[u8],
    use_rolling_detector: bool,
    backend_prompt_guard_enabled: bool,
    non_rolling_window: Option<&[u8]>,
) -> OutputChunkSignals {
    let explicit_approval_hint_chunk =
        prompt_occlusion_signals::chunk_contains_explicit_approval_hint(data);
    let numbered_approval_hint_chunk =
        prompt_occlusion_signals::chunk_contains_numbered_approval_hint(
            data,
            NON_ROLLING_APPROVAL_CARD_SCAN_LINES,
        );
    let yes_no_approval_hint_chunk =
        use_rolling_detector && prompt_occlusion_signals::chunk_contains_yes_no_approval_hint(data);
    let confirmation_prompt_line_chunk = use_rolling_detector
        && prompt_occlusion_signals::chunk_contains_confirmation_prompt_line(data);
    let prompt_context_chunk =
        prompt_occlusion_signals::chunk_contains_prompt_context_markers(data);

    let approval_window_scan = non_rolling_window
        .map(|window| tail_slice(window, NON_ROLLING_APPROVAL_WINDOW_SCAN_TAIL_BYTES));
    let explicit_approval_hint_window = approval_window_scan.is_some_and(|window| {
        prompt_occlusion_signals::chunk_contains_explicit_approval_hint(window)
    });
    let numbered_approval_hint_window = approval_window_scan.is_some_and(|window| {
        prompt_occlusion_signals::chunk_contains_numbered_approval_hint(
            window,
            NON_ROLLING_APPROVAL_CARD_SCAN_LINES,
        )
    });
    let prompt_context_window = non_rolling_window.is_some_and(|window| {
        prompt_occlusion_signals::chunk_contains_prompt_context_markers(window)
    });
    let explicit_approval_hint = explicit_approval_hint_chunk || explicit_approval_hint_window;
    let numbered_approval_hint = numbered_approval_hint_chunk || numbered_approval_hint_window;
    let rolling_approval_hint_seen = use_rolling_detector
        && prompt_occlusion_signals::rolling_high_confidence_approval_hint(
            explicit_approval_hint_chunk,
            numbered_approval_hint_chunk,
            yes_no_approval_hint_chunk,
            confirmation_prompt_line_chunk,
        );
    let non_rolling_live_approval_window_hint = approval_window_scan.is_some_and(|window| {
        prompt_occlusion_signals::chunk_contains_live_approval_card_hint(
            window,
            NON_ROLLING_APPROVAL_CARD_SCAN_LINES,
        )
    });
    let non_rolling_approval_hint = explicit_approval_hint_chunk
        || numbered_approval_hint_chunk
        || (explicit_approval_hint_window && numbered_approval_hint_window)
        || non_rolling_live_approval_window_hint;
    let approval_hint_seen = if use_rolling_detector {
        rolling_approval_hint_seen
    } else {
        non_rolling_approval_hint
    };
    let prompt_guard_enabled = backend_prompt_guard_enabled
        || prompt_context_chunk
        || prompt_context_window
        || if use_rolling_detector {
            rolling_approval_hint_seen
        } else {
            non_rolling_approval_hint
        };
    let synchronized_cursor_activity_candidate = use_rolling_detector
        && prompt_guard_enabled
        && prompt_occlusion_signals::chunk_contains_synchronized_prompt_activity(data);
    let is_prompt_input_echo_rewrite =
        prompt_occlusion_signals::chunk_is_probable_prompt_input_echo_rewrite(data);
    let ignore_synchronized_candidate = synchronized_cursor_activity_candidate
        && is_prompt_input_echo_rewrite
        && !explicit_approval_hint
        && !numbered_approval_hint;
    let saw_synchronized_cursor_activity =
        synchronized_cursor_activity_candidate && !ignore_synchronized_candidate;
    let saw_tool_activity =
        prompt_guard_enabled && prompt_occlusion_signals::chunk_contains_tool_activity_hint(data);

    OutputChunkSignals {
        use_rolling_detector,
        backend_prompt_guard_enabled,
        prompt_guard_enabled,
        approval_hint_seen,
        rolling_approval_hint_seen,
        non_rolling_approval_hint,
        saw_tool_activity,
        saw_synchronized_cursor_activity,
        explicit_approval_hint,
        numbered_approval_hint,
        explicit_approval_hint_chunk,
        numbered_approval_hint_chunk,
        explicit_approval_hint_window,
        numbered_approval_hint_window,
        non_rolling_live_approval_window_hint,
        prompt_context_chunk,
        prompt_context_window,
        ignore_synchronized_candidate,
        non_rolling_window_bytes: non_rolling_window.map_or(0, <[u8]>::len),
    }
}

/// Emit debug trace for the computed chunk signals. Only writes when
/// `claude_hud_debug_enabled()` is active and the chunk is non-empty.
pub(super) fn log_output_chunk_signals(
    signals: &OutputChunkSignals,
    data: &[u8],
    backend_label: &str,
    suppressed: bool,
    non_rolling_window: Option<&[u8]>,
) {
    if !claude_hud_debug_enabled() || data.is_empty() {
        return;
    }
    log_debug(&format!(
        "[claude-hud-debug] output chunk (rolling={}, suppressed={}, bytes={}, backend_label=\"{}\", backend_guard={}, prompt_guard={}, fallback_context_chunk={}, fallback_context_window={}): \"{}\"",
        signals.use_rolling_detector,
        suppressed,
        data.len(),
        backend_label,
        signals.backend_prompt_guard_enabled,
        signals.prompt_guard_enabled,
        signals.prompt_context_chunk,
        signals.prompt_context_window,
        debug_bytes_preview(data, 120)
    ));
    if !signals.backend_prompt_guard_enabled
        && signals.prompt_guard_enabled
        && (signals.explicit_approval_hint || signals.numbered_approval_hint)
    {
        log_debug(
            "[claude-hud-debug] prompt guard fallback engaged from Claude prompt context markers",
        );
    }
    if !signals.use_rolling_detector {
        log_debug(&format!(
            "[claude-hud-debug] non-rolling approval scan (chunk_explicit={}, window_explicit={}, chunk_numbered={}, window_numbered={}, window_live={}, window_context={}, window_bytes={})",
            signals.explicit_approval_hint_chunk,
            signals.explicit_approval_hint_window,
            signals.numbered_approval_hint_chunk,
            signals.numbered_approval_hint_window,
            signals.non_rolling_live_approval_window_hint,
            signals.prompt_context_window,
            signals.non_rolling_window_bytes
        ));
        if let Some(window) = non_rolling_window {
            log_debug(&format!(
                "[claude-hud-debug] non-rolling approval window tail: \"{}\"",
                debug_bytes_preview(window, 180)
            ));
        }
    } else if signals.explicit_approval_hint_chunk && !signals.rolling_approval_hint_seen {
        log_debug(
            "[claude-hud-debug] rolling approval text ignored without live approval-choice markers",
        );
    }
    if signals.ignore_synchronized_candidate {
        log_debug(
            "[claude-hud-debug] suppression candidate ignored: synchronized prompt-input echo rewrite",
        );
    }
}
