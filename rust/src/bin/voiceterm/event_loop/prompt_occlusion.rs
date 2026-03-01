//! Prompt-occlusion state transitions shared by event-loop input/output/periodic paths.

use super::*;
use crate::runtime_compat;
#[cfg(test)]
use std::cell::Cell;
use std::sync::OnceLock;

const PROMPT_SUPPRESSION_RELEASE_DEBOUNCE_MS: u64 = 3000;
const TOOL_ACTIVITY_SUPPRESSION_HOLD_MS: u64 = 2200;
const NON_ROLLING_APPROVAL_WINDOW_MAX_BYTES: usize = 12 * 1024;
const NON_ROLLING_APPROVAL_WINDOW_STALE_MS: u64 = 1800;
const NON_ROLLING_APPROVAL_WINDOW_MAX_AGE_MS: u64 = 90_000;
const NON_ROLLING_APPROVAL_WINDOW_INPUT_TAIL_BYTES: usize = 2048;
const NON_ROLLING_APPROVAL_WINDOW_SCAN_TAIL_BYTES: usize = 8192;
const NON_ROLLING_APPROVAL_CARD_SCAN_LINES: usize = 64;
const NON_ROLLING_CONSECUTIVE_APPROVAL_STICKY_HOLD_MS: u64 = 850;
const APPROVAL_SUPPRESSION_CANONICAL_FEED: &[u8] =
    b"This command requires approval\nDo you want to proceed?\n";
const CLAUDE_HUD_DEBUG_ENV: &str = "VOICETERM_DEBUG_CLAUDE_HUD";

#[cfg(test)]
thread_local! {
    static TEST_ROLLING_DETECTOR_OVERRIDE: Cell<Option<bool>> = const { Cell::new(None) };
}

#[cfg(test)]
pub(super) fn set_test_rolling_detector_override(value: Option<bool>) {
    TEST_ROLLING_DETECTOR_OVERRIDE.with(|cell| cell.set(value));
}

fn parse_debug_env_flag(raw: &str) -> bool {
    matches!(
        raw.trim().to_ascii_lowercase().as_str(),
        "1" | "true" | "yes" | "on" | "debug"
    )
}

fn claude_hud_debug_enabled() -> bool {
    static ENABLED: OnceLock<bool> = OnceLock::new();
    *ENABLED.get_or_init(|| {
        std::env::var(CLAUDE_HUD_DEBUG_ENV)
            .map(|raw| parse_debug_env_flag(&raw))
            // Keep prompt-occlusion traces on by default in debug/dev builds so
            // real Cursor regressions are diagnosable without env-var misses.
            .unwrap_or(cfg!(debug_assertions))
    })
}

fn debug_bytes_preview(bytes: &[u8], max_chars: usize) -> String {
    let text = String::from_utf8_lossy(bytes);
    let mut out = String::new();
    for (count, ch) in text.chars().enumerate() {
        if count >= max_chars {
            out.push_str("...");
            break;
        }
        for escaped in ch.escape_default() {
            out.push(escaped);
        }
    }
    out
}

fn strip_ansi_for_approval_window(bytes: &[u8]) -> Vec<u8> {
    let mut stripped = Vec::with_capacity(bytes.len());
    let mut idx = 0usize;
    while idx < bytes.len() {
        let byte = bytes[idx];
        if byte == 0x1b {
            if idx + 1 < bytes.len() && bytes[idx + 1] == b'[' {
                idx += 2;
                while idx < bytes.len() {
                    if (0x40..=0x7e).contains(&bytes[idx]) {
                        idx += 1;
                        break;
                    }
                    idx += 1;
                }
            } else {
                idx += 2usize.min(bytes.len().saturating_sub(idx));
            }
            continue;
        }
        match byte {
            b'\n' | b'\r' | b'\t' => stripped.push(byte),
            byte if !byte.is_ascii_control() => stripped.push(byte),
            _ => {}
        }
        idx += 1;
    }
    stripped
}

fn append_non_rolling_approval_window(state: &mut EventLoopState, now: Instant, data: &[u8]) {
    if data.is_empty() {
        return;
    }
    if state
        .prompt
        .non_rolling_approval_window_last_update
        .is_some_and(|last| {
            now.duration_since(last).as_millis() > u128::from(NON_ROLLING_APPROVAL_WINDOW_STALE_MS)
        })
    {
        state.prompt.non_rolling_approval_window.clear();
    }
    state.prompt.non_rolling_approval_window_last_update = Some(now);
    let normalized = strip_ansi_for_approval_window(data);
    state.prompt.non_rolling_approval_window.extend(normalized);
    while state.prompt.non_rolling_approval_window.len() > NON_ROLLING_APPROVAL_WINDOW_MAX_BYTES {
        let _ = state.prompt.non_rolling_approval_window.pop_front();
    }
}

fn clear_non_rolling_approval_window(state: &mut EventLoopState) {
    state.prompt.non_rolling_approval_window.clear();
    state.prompt.non_rolling_approval_window_last_update = None;
    state.prompt.non_rolling_release_armed = false;
}

fn clear_non_rolling_sticky_hold(state: &mut EventLoopState) {
    state.prompt.non_rolling_sticky_hold_until = None;
}

fn retain_non_rolling_approval_window_tail(state: &mut EventLoopState, tail_bytes: usize) {
    while state.prompt.non_rolling_approval_window.len() > tail_bytes {
        let _ = state.prompt.non_rolling_approval_window.pop_front();
    }
}

fn maybe_expire_non_rolling_approval_window(state: &mut EventLoopState, now: Instant) {
    if state
        .prompt
        .non_rolling_approval_window_last_update
        .is_some_and(|last| {
            now.duration_since(last).as_millis()
                > u128::from(NON_ROLLING_APPROVAL_WINDOW_MAX_AGE_MS)
        })
    {
        clear_non_rolling_approval_window(state);
    }
}

fn non_rolling_approval_window_snapshot(state: &EventLoopState) -> Vec<u8> {
    state
        .prompt
        .non_rolling_approval_window
        .iter()
        .copied()
        .collect()
}

fn tail_slice(bytes: &[u8], tail_bytes: usize) -> &[u8] {
    if bytes.len() <= tail_bytes {
        return bytes;
    }
    &bytes[bytes.len().saturating_sub(tail_bytes)..]
}

fn normalize_approval_hint_text(bytes: &[u8]) -> String {
    let mut normalized = String::with_capacity(bytes.len());
    let mut prev_space = false;
    for ch in String::from_utf8_lossy(bytes).chars() {
        let lower = ch.to_ascii_lowercase();
        if lower.is_ascii_alphanumeric() || matches!(lower, ':' | '*' | '/' | '.' | '_' | '-') {
            normalized.push(lower);
            prev_space = false;
            continue;
        }
        if !prev_space {
            normalized.push(' ');
            prev_space = true;
        }
    }
    normalized
}

fn chunk_contains_explicit_approval_hint(bytes: &[u8]) -> bool {
    if bytes.is_empty() {
        return false;
    }
    let stripped = strip_ansi_for_approval_window(bytes);
    if stripped.is_empty() {
        return false;
    }
    let raw_lower = String::from_utf8_lossy(&stripped).to_ascii_lowercase();
    if raw_lower.contains("this command requires approval")
        || raw_lower.contains("thiscommandrequiresapproval")
    {
        return true;
    }
    let line_starts_with_prompt_question = raw_lower.lines().any(|line| {
        let lowered = normalize_approval_card_line(line);
        lowered.starts_with("do you want to proceed") || lowered.starts_with("doyouwanttoproceed")
    });
    if line_starts_with_prompt_question {
        return true;
    }
    let normalized = normalize_approval_hint_text(&stripped);
    let compact: String = normalized
        .chars()
        .filter(|ch| !ch.is_ascii_whitespace())
        .collect();
    normalized.contains("this command requires approval")
        || compact.contains("thiscommandrequiresapproval")
        || normalized.starts_with("do you want to proceed")
        || compact.starts_with("doyouwanttoproceed")
        || ((normalized.contains("yes and don t ask again for")
            || compact.contains("yesanddontaskagainfor"))
            && normalized.contains("1")
            && normalized.contains("2"))
}

fn chunk_contains_claude_prompt_context(bytes: &[u8]) -> bool {
    if bytes.is_empty() {
        return false;
    }
    let normalized = normalize_approval_hint_text(bytes);
    normalized.contains("claude wants to")
        || normalized.contains("what should claude do instead")
        || normalized.contains("tool use")
        || normalized.contains("claude code")
}

fn normalize_approval_card_line(line: &str) -> String {
    let trimmed = line.trim_start();
    let trimmed = trimmed
        .trim_start_matches(|ch: char| {
            matches!(
                ch,
                '•' | '*'
                    | '-'
                    | '└'
                    | '│'
                    | '⏺'
                    | '›'
                    | '❯'
                    | '>'
                    | '→'
                    | '·'
                    | '▸'
                    | '▶'
                    | '◂'
            )
        })
        .trim_start();
    let trimmed = if let Some(rest) = trimmed.strip_prefix("o ") {
        rest
    } else if let Some(rest) = trimmed.strip_prefix('o') {
        if rest
            .chars()
            .next()
            .is_some_and(|ch| ch.is_ascii_digit() || matches!(ch, '.' | ')' | ':' | ' '))
        {
            rest
        } else {
            trimmed
        }
    } else {
        trimmed
    };
    trimmed.to_ascii_lowercase()
}

fn starts_with_numbered_option(line: &str, option: u8) -> bool {
    if line.len() < 2 {
        return false;
    }
    let first = option as char;
    let bytes = line.as_bytes();
    bytes[0] == first as u8 && matches!(bytes[1], b'.' | b')' | b':' | b' ')
}

fn chunk_contains_numbered_approval_hint(bytes: &[u8]) -> bool {
    if bytes.is_empty() {
        return false;
    }
    let text = String::from_utf8_lossy(bytes);
    let mut has_option_1 = false;
    let mut has_option_2 = false;
    let mut has_option_3 = false;
    let mut has_yes = false;
    let mut has_no = false;
    let mut has_approval_text = false;
    let mut has_dont_ask_again = false;

    for line in text
        .lines()
        .rev()
        .take(NON_ROLLING_APPROVAL_CARD_SCAN_LINES)
    {
        let lowered = normalize_approval_card_line(line);
        if starts_with_numbered_option(&lowered, b'1') {
            has_option_1 = true;
        }
        if starts_with_numbered_option(&lowered, b'2') {
            has_option_2 = true;
        }
        if starts_with_numbered_option(&lowered, b'3') {
            has_option_3 = true;
        }
        if lowered.contains(" yes") || lowered.starts_with("yes") {
            has_yes = true;
        }
        if lowered.contains(".yes") || lowered.contains(")yes") || lowered.contains(":yes") {
            has_yes = true;
        }
        if lowered.contains(" no") || lowered.starts_with("no") {
            has_no = true;
        }
        if lowered.contains(".no") || lowered.contains(")no") || lowered.contains(":no") {
            has_no = true;
        }
        if lowered.contains("don't ask again") || lowered.contains("dont ask again") {
            has_dont_ask_again = true;
        }
        if lowered.contains("do you want")
            || lowered.contains("requires approval")
            || lowered.contains("allow this command")
            || lowered.contains("approve this action")
        {
            has_approval_text = true;
        }
    }

    let has_numbered_options = has_option_1
        && has_option_2
        && (has_option_3 || has_no || has_approval_text || has_dont_ask_again);
    let has_approval_semantics = has_dont_ask_again || has_approval_text || (has_yes && has_no);
    has_numbered_options && has_approval_semantics
}

fn chunk_contains_live_approval_card_hint(bytes: &[u8]) -> bool {
    chunk_contains_explicit_approval_hint(bytes) && chunk_contains_numbered_approval_hint(bytes)
}

fn chunk_contains_substantial_non_prompt_activity(bytes: &[u8]) -> bool {
    if bytes.is_empty() {
        return false;
    }
    let stripped = strip_ansi_for_approval_window(bytes);
    if stripped.is_empty() {
        return false;
    }
    let text = String::from_utf8_lossy(&stripped);
    let trimmed = text.trim();
    if trimmed.is_empty() {
        return false;
    }
    let compact: String = trimmed
        .chars()
        .filter(|ch| !ch.is_ascii_whitespace())
        .collect();
    if compact.is_empty() {
        return false;
    }
    let compact_lower = compact.to_ascii_lowercase();
    if matches!(
        compact_lower.as_str(),
        "1" | "2" | "3" | "y" | "n" | "yes" | "no" | "enter"
    ) {
        return false;
    }
    if compact_lower.len() < 8 {
        return false;
    }
    if chunk_contains_explicit_approval_hint(&stripped)
        || chunk_contains_numbered_approval_hint(&stripped)
        || chunk_contains_claude_prompt_context(&stripped)
    {
        return false;
    }
    true
}

fn normalize_tool_activity_line(line: &str) -> String {
    line.trim_start()
        .trim_start_matches(|ch: char| {
            matches!(
                ch,
                '•' | '*' | '-' | '└' | '│' | '⏺' | '›' | '❯' | '>' | '→' | '·'
            )
        })
        .trim_start()
        .to_ascii_lowercase()
}

fn chunk_contains_tool_activity_hint(bytes: &[u8]) -> bool {
    if bytes.is_empty() {
        return false;
    }
    let text = String::from_utf8_lossy(bytes);
    for line in text.lines().rev().take(12) {
        let lowered = normalize_tool_activity_line(line);
        if lowered.starts_with("bash(")
            || lowered == "bash command"
            || lowered.starts_with("web search(")
            || lowered.starts_with("google search(")
            || lowered.contains("running tools")
            || lowered.contains("+1 more tool use")
            || lowered.contains("+2 more tool use")
            || lowered.contains("+3 more tool use")
            || lowered.contains("+4 more tool use")
            || lowered.contains("+5 more tool use")
            || lowered.contains("+1 more tool call")
            || lowered.contains("+2 more tool call")
            || lowered.contains("+3 more tool call")
            || lowered.contains("+4 more tool call")
            || lowered.contains("+5 more tool call")
        {
            return true;
        }
    }
    false
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

fn should_resolve_prompt_suppression_on_input_without_detector(bytes: &[u8]) -> bool {
    matches!(
        bytes,
        [b'\r']
            | [b'\n']
            | [b'y']
            | [b'Y']
            | [b'n']
            | [b'N']
            | [b'1']
            | [b'2']
            | [b'3']
            | [0x03]
            | [0x04]
            | [0x1b]
    )
}

/// Apply prompt suppression state and propagate dependent runtime side effects.
pub(super) fn apply_prompt_suppression(
    state: &mut EventLoopState,
    deps: &mut EventLoopDeps,
    suppressed: bool,
) {
    let was_suppressed = state.status_state.claude_prompt_suppressed;
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

    state.status_state.claude_prompt_suppressed = suppressed;
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
        state.status_state.claude_prompt_suppressed,
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
    let backend_prompt_guard_enabled =
        runtime_compat::backend_supports_prompt_occlusion_guard(&deps.backend_label);
    let use_rolling_detector = should_use_rolling_prompt_detector();
    let explicit_approval_hint_chunk = chunk_contains_explicit_approval_hint(data);
    let numbered_approval_hint_chunk =
        !use_rolling_detector && chunk_contains_numbered_approval_hint(data);
    let claude_prompt_context_chunk = chunk_contains_claude_prompt_context(data);
    if !use_rolling_detector {
        append_non_rolling_approval_window(state, now, data);
        if explicit_approval_hint_chunk || numbered_approval_hint_chunk {
            state.prompt.non_rolling_release_armed = false;
        } else if state.prompt.non_rolling_release_armed {
            if chunk_contains_substantial_non_prompt_activity(data) {
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
    let non_rolling_window = if !use_rolling_detector {
        Some(non_rolling_approval_window_snapshot(state))
    } else {
        None
    };
    let approval_window_scan = non_rolling_window
        .as_ref()
        .map(|window| tail_slice(window, NON_ROLLING_APPROVAL_WINDOW_SCAN_TAIL_BYTES));
    let explicit_approval_hint_window = approval_window_scan
        .as_ref()
        .is_some_and(|window| chunk_contains_explicit_approval_hint(window));
    let numbered_approval_hint_window = approval_window_scan
        .as_ref()
        .is_some_and(|window| chunk_contains_numbered_approval_hint(window));
    let claude_prompt_context_window = non_rolling_window
        .as_ref()
        .is_some_and(|window| chunk_contains_claude_prompt_context(window));
    let explicit_approval_hint = explicit_approval_hint_chunk || explicit_approval_hint_window;
    let numbered_approval_hint = numbered_approval_hint_chunk || numbered_approval_hint_window;
    let non_rolling_live_approval_window_hint = approval_window_scan
        .as_ref()
        .is_some_and(|window| chunk_contains_live_approval_card_hint(window));
    let non_rolling_approval_hint = explicit_approval_hint_chunk
        || numbered_approval_hint_chunk
        || (explicit_approval_hint_chunk && numbered_approval_hint_window)
        || (explicit_approval_hint_window && numbered_approval_hint_window)
        || non_rolling_live_approval_window_hint;
    let approval_hint_seen = if use_rolling_detector {
        explicit_approval_hint || numbered_approval_hint
    } else {
        non_rolling_approval_hint
    };
    let prompt_guard_enabled = backend_prompt_guard_enabled
        || claude_prompt_context_chunk
        || claude_prompt_context_window
        // High-confidence approval hints should still engage guard behavior even
        // when backend labeling is noisy in integrated terminals.
        || if use_rolling_detector {
            explicit_approval_hint || numbered_approval_hint
        } else {
            non_rolling_approval_hint
        };
    if !use_rolling_detector
        && prompt_guard_enabled
        && explicit_approval_hint
        && !numbered_approval_hint
        && !state.status_state.claude_prompt_suppressed
    {
        log_debug(&format!(
            "[claude-hud-anomaly] explicit approval hint seen without numbered-match in non-rolling mode (chunk_explicit={}, window_explicit={}, chunk_numbered={}, window_numbered={}, window_live={}, window_bytes={}, rows={}, cols={})",
            explicit_approval_hint_chunk,
            explicit_approval_hint_window,
            numbered_approval_hint_chunk,
            numbered_approval_hint_window,
            non_rolling_live_approval_window_hint,
            non_rolling_window.as_ref().map_or(0, Vec::len),
            state.ui.terminal_rows,
            state.ui.terminal_cols
        ));
    }
    let saw_tool_activity = prompt_guard_enabled && chunk_contains_tool_activity_hint(data);
    if claude_hud_debug_enabled() && !data.is_empty() {
        log_debug(&format!(
            "[claude-hud-debug] output chunk (rolling={}, suppressed={}, bytes={}, backend_label=\"{}\", backend_guard={}, prompt_guard={}, fallback_context_chunk={}, fallback_context_window={}): \"{}\"",
            use_rolling_detector,
            state.status_state.claude_prompt_suppressed,
            data.len(),
            deps.backend_label,
            backend_prompt_guard_enabled,
            prompt_guard_enabled,
            claude_prompt_context_chunk,
            claude_prompt_context_window,
            debug_bytes_preview(data, 120)
        ));
        if !backend_prompt_guard_enabled
            && prompt_guard_enabled
            && (explicit_approval_hint || numbered_approval_hint)
        {
            log_debug(
                "[claude-hud-debug] prompt guard fallback engaged from Claude prompt context markers",
            );
        }
        if !use_rolling_detector {
            log_debug(&format!(
                "[claude-hud-debug] non-rolling approval scan (chunk_explicit={}, window_explicit={}, chunk_numbered={}, window_numbered={}, window_live={}, window_context={}, window_bytes={})",
                explicit_approval_hint_chunk,
                explicit_approval_hint_window,
                numbered_approval_hint_chunk,
                numbered_approval_hint_window,
                non_rolling_live_approval_window_hint,
                claude_prompt_context_window,
                non_rolling_window.as_ref().map_or(0, Vec::len)
            ));
            if let Some(window) = non_rolling_window.as_ref() {
                log_debug(&format!(
                    "[claude-hud-debug] non-rolling approval window tail: \"{}\"",
                    debug_bytes_preview(window, 180)
                ));
            }
        }
    }
    if saw_tool_activity {
        if claude_hud_debug_enabled() {
            log_debug("[claude-hud-debug] suppression candidate: tool-activity hint");
        }
        extend_prompt_suppression_deadline(
            &mut timers.prompt_suppression_release_not_before,
            now + Duration::from_millis(TOOL_ACTIVITY_SUPPRESSION_HOLD_MS),
        );
        // Tool-activity lines are noisy in Cursor transcript redraws and can
        // spuriously hide HUD while typing. Only rolling-detector hosts
        // (JetBrains) can engage suppression from tool-activity alone.
        if use_rolling_detector {
            if !state.status_state.claude_prompt_suppressed {
                apply_prompt_suppression(state, deps, true);
            }
        } else if claude_hud_debug_enabled() && !state.status_state.claude_prompt_suppressed {
            log_debug(
                "[claude-hud-debug] suppression candidate ignored: tool-activity hint on non-rolling host",
            );
        }
    }

    state.prompt.tracker.feed_output(data);
    if use_rolling_detector {
        let _ = state.prompt.occlusion_detector.feed_output(data);
        // Claude approval cards can arrive with styling/fragmentation that may
        // evade a single rolling parse pass. When explicit approval phrases are
        // present, feed a canonical phrase so suppression engages deterministically.
        if prompt_guard_enabled
            && !state.prompt.occlusion_detector.should_suppress_hud()
            && explicit_approval_hint
        {
            if claude_hud_debug_enabled() {
                log_debug("[claude-hud-debug] suppression candidate: explicit approval hint (rolling detector canonical feed)");
            }
            let _ = state
                .prompt
                .occlusion_detector
                .feed_output(APPROVAL_SUPPRESSION_CANONICAL_FEED);
        }
    } else if prompt_guard_enabled
        && non_rolling_approval_hint
        && !(state.prompt.non_rolling_release_armed
            && !explicit_approval_hint_chunk
            && !numbered_approval_hint_chunk)
    {
        if claude_hud_debug_enabled() {
            if explicit_approval_hint {
                log_debug(
                    "[claude-hud-debug] suppression candidate: explicit approval hint (non-rolling latch)",
                );
            }
            if numbered_approval_hint {
                log_debug(
                    "[claude-hud-debug] suppression candidate: numbered approval hint (non-rolling latch)",
                );
            }
            log_debug(&format!(
                "[claude-hud-debug] suppression candidate source (non-rolling): explicit_chunk={}, explicit_window={}, numbered_chunk={}, numbered_window={}, window_live={}",
                explicit_approval_hint_chunk,
                explicit_approval_hint_window,
                numbered_approval_hint_chunk,
                numbered_approval_hint_window,
                non_rolling_live_approval_window_hint
            ));
        }
        // Non-JetBrains Claude hosts (for example VS Code/Cursor integrated terminals)
        // are prone to noisy rolling-detector transitions while typing. Use an explicit
        // hint latch instead of rolling context in those hosts.
        extend_prompt_suppression_deadline(
            &mut timers.prompt_suppression_release_not_before,
            now + Duration::from_millis(PROMPT_SUPPRESSION_RELEASE_DEBOUNCE_MS),
        );
        if !state.status_state.claude_prompt_suppressed {
            apply_prompt_suppression(state, deps, true);
        }
    } else if claude_hud_debug_enabled()
        && state.prompt.non_rolling_release_armed
        && non_rolling_approval_hint
        && !explicit_approval_hint_chunk
        && !numbered_approval_hint_chunk
    {
        log_debug(
            "[claude-hud-debug] suppression relatch deferred: release-armed state with window-only approval hints",
        );
    }
    sync_prompt_suppression_from_detector(state, timers, deps, now);
    if approval_hint_seen && !state.status_state.claude_prompt_suppressed {
        log_debug(&format!(
            "[claude-hud-anomaly] prompt overlap risk: approval hint seen while HUD suppression is inactive (rolling={}, backend_label=\"{}\", explicit_chunk={}, explicit_window={}, numbered_chunk={}, numbered_window={}, rows={}, cols={}, hud_style={:?}, overlay={:?})",
            use_rolling_detector,
            deps.backend_label,
            explicit_approval_hint_chunk,
            explicit_approval_hint_window,
            numbered_approval_hint_chunk,
            numbered_approval_hint_window,
            state.ui.terminal_rows,
            state.ui.terminal_cols,
            state.status_state.hud_style,
            state.ui.overlay_mode
        ));
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
        if claude_hud_debug_enabled() && !state.status_state.claude_prompt_suppressed {
            log_debug("[claude-hud-debug] suppression engage: rolling detector active");
        }
        timers.prompt_suppression_release_not_before =
            Some(now + Duration::from_millis(PROMPT_SUPPRESSION_RELEASE_DEBOUNCE_MS));
        if !state.status_state.claude_prompt_suppressed {
            apply_prompt_suppression(state, deps, true);
        }
        return;
    }

    if !state.status_state.claude_prompt_suppressed {
        timers.prompt_suppression_release_not_before = None;
        clear_non_rolling_sticky_hold(state);
        return;
    }

    if matches!(
        ready_marker_resolution_kind,
        Some(crate::prompt::claude_prompt_detect::PromptType::StartupGuard)
    ) {
        if claude_hud_debug_enabled() {
            log_debug("[claude-hud-debug] suppression release: startup guard ready marker");
        }
        timers.prompt_suppression_release_not_before = None;
        apply_prompt_suppression(state, deps, false);
        return;
    }

    if !use_rolling_detector && state.status_state.claude_prompt_suppressed {
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
        let approval_window_scan = tail_slice(
            &approval_window_snapshot,
            NON_ROLLING_APPROVAL_WINDOW_SCAN_TAIL_BYTES,
        );
        let approval_window_still_active =
            chunk_contains_live_approval_card_hint(approval_window_scan);
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
    if state.status_state.claude_prompt_suppressed {
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
    if !state.status_state.claude_prompt_suppressed || bytes.is_empty() {
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
    let should_resolve = should_resolve_prompt_suppression_on_input_without_detector(bytes);
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

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn explicit_approval_hint_detects_cargo_prompt_variant() {
        let bytes = "Bash command\ncargo --version\nShow Cargo version\n\nThis command requires approval\n\nDo you want to proceed?\n› 1. Yes\n2. Yes, and don’t ask again for: cargo:*\n3. No\n"
            .as_bytes();
        assert!(chunk_contains_explicit_approval_hint(bytes));
    }

    #[test]
    fn explicit_approval_hint_detects_compact_spacing_variant() {
        let bytes = b"Doyouwanttoproceed?\n1.Yes\n2.Yes,anddon'taskagainfor:WebSearch:*\n";
        assert!(chunk_contains_explicit_approval_hint(bytes));
    }

    #[test]
    fn explicit_approval_hint_ignores_unrelated_output() {
        assert!(!chunk_contains_explicit_approval_hint(
            b"Web Search(\"rust async await\")\nDid 1 search in 8s\n"
        ));
    }

    #[test]
    fn explicit_approval_hint_ignores_embedded_recap_phrase() {
        assert!(!chunk_contains_explicit_approval_hint(
            b"Recap: earlier output included \"Do you want to proceed?\" before approval.\n"
        ));
    }

    #[test]
    fn explicit_approval_hint_detects_prompt_question_line_start() {
        assert!(chunk_contains_explicit_approval_hint(
            b"  Do you want to proceed?\n"
        ));
    }

    #[test]
    fn explicit_approval_hint_detects_ansi_styled_prompt_question() {
        assert!(chunk_contains_explicit_approval_hint(
            b"\x1b[37mDo you want to proceed?\x1b[39m\n"
        ));
    }

    #[test]
    fn claude_prompt_context_detects_tool_use_card() {
        assert!(chunk_contains_claude_prompt_context(
            b"Tool use\nClaude wants to search the web for rust terminal ui\n"
        ));
    }

    #[test]
    fn numbered_approval_hint_detects_sparse_card() {
        assert!(chunk_contains_numbered_approval_hint(
            b"1. Yes\n2. Yes, and don't ask again for this command\n3. No\n"
        ));
    }

    #[test]
    fn numbered_approval_hint_detects_selected_chevron_card() {
        assert!(chunk_contains_numbered_approval_hint(
            b"\xE2\x80\xBA 1. Yes\n2. Yes, and don't ask again for this command\n"
        ));
    }

    #[test]
    fn numbered_approval_hint_detects_two_option_yes_no_card() {
        assert!(chunk_contains_numbered_approval_hint(b"1. Yes\n2. No\n"));
    }

    #[test]
    fn numbered_approval_hint_detects_selected_o_prefix_variant() {
        assert!(chunk_contains_numbered_approval_hint(b"o 1. Yes\n2. No\n"));
    }

    #[test]
    fn numbered_approval_hint_detects_compact_prefix_variant() {
        assert!(chunk_contains_numbered_approval_hint(
            b"\xE2\x9D\xAF1.Yes\n2.No\n"
        ));
    }

    #[test]
    fn numbered_approval_hint_detects_space_separator_variant() {
        assert!(chunk_contains_numbered_approval_hint(b"1 Yes\n2 No\n"));
    }

    #[test]
    fn numbered_approval_hint_detects_wrapped_long_option_cards() {
        let mut card =
            String::from("This command requires approval\nDo you want to proceed?\n1. Yes\n");
        for _ in 0..40 {
            card.push_str("/Users/jguida941/testing_upgrade/codex-voice/rust\n");
        }
        card.push_str("2. Yes, and don't ask again for Web Search commands in this directory\n");
        card.push_str("3. No\n");
        assert!(chunk_contains_numbered_approval_hint(card.as_bytes()));
    }

    #[test]
    fn numbered_approval_hint_ignores_plain_numbered_list() {
        assert!(!chunk_contains_numbered_approval_hint(
            b"1. alpha\n2. beta\n3. gamma\n"
        ));
    }

    #[test]
    fn live_approval_card_hint_requires_explicit_and_numbered_signals() {
        assert!(chunk_contains_live_approval_card_hint(
            b"This command requires approval\nDo you want to proceed?\n1. Yes\n2. No\n"
        ));
        assert!(!chunk_contains_live_approval_card_hint(
            b"Recap: Do you want to proceed with this plan later?\n"
        ));
        assert!(!chunk_contains_live_approval_card_hint(
            b"1. alpha\n2. beta\n3. gamma\n"
        ));
    }

    #[test]
    fn substantial_non_prompt_activity_ignores_choice_echo() {
        assert!(!chunk_contains_substantial_non_prompt_activity(b"1\n"));
        assert!(!chunk_contains_substantial_non_prompt_activity(b"yes\n"));
        assert!(!chunk_contains_substantial_non_prompt_activity(
            b"\x1b[2K\r\n"
        ));
    }

    #[test]
    fn substantial_non_prompt_activity_detects_post_approval_output() {
        assert!(chunk_contains_substantial_non_prompt_activity(
            b"Approval accepted. Continuing execution...\n"
        ));
    }

    #[test]
    fn approval_hint_detects_split_card_when_chunks_are_merged() {
        let chunk_a = b"This command requires approval\nDo you want to proceed?\n";
        let chunk_b = b"1. Yes\n2. Yes, and don't ask again for this command\n";
        assert!(chunk_contains_explicit_approval_hint(chunk_a));
        assert!(!chunk_contains_numbered_approval_hint(chunk_a));
        assert!(chunk_contains_numbered_approval_hint(chunk_b));
        let mut merged = Vec::new();
        merged.extend_from_slice(chunk_a);
        merged.extend_from_slice(chunk_b);
        assert!(chunk_contains_explicit_approval_hint(&merged));
        assert!(chunk_contains_numbered_approval_hint(&merged));
    }

    #[test]
    fn tool_activity_hint_detects_bash_tool_line() {
        assert!(chunk_contains_tool_activity_hint(
            b"Bash(echo $SHELL)\nDid 1 run in 0.1s\n"
        ));
    }

    #[test]
    fn tool_activity_hint_detects_web_search_line() {
        assert!(chunk_contains_tool_activity_hint(
            b"Web Search(\"rust async await\")\nDid 1 search in 8s\n"
        ));
    }

    #[test]
    fn tool_activity_hint_ignores_plain_bash_commands_heading() {
        assert!(!chunk_contains_tool_activity_hint(
            b"Bash Commands:\n1. Echo -- printed hello\n"
        ));
    }

    #[test]
    fn tool_activity_hint_ignores_plain_web_searches_heading() {
        assert!(!chunk_contains_tool_activity_hint(
            b"Web Searches:\n1. Rust TUI rendering -- Ratatui dominates\n"
        ));
    }

    #[test]
    fn tool_activity_hint_ignores_unrelated_output() {
        assert!(!chunk_contains_tool_activity_hint(
            b"transcript ready\nall checks passed\n"
        ));
    }
}
