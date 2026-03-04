use crossterm::terminal::size as terminal_size;
use std::env;
use std::io::{self, Write};
use std::sync::OnceLock;
use std::time::{Duration, Instant};
#[cfg(test)]
use std::{cell::Cell, thread_local};
use voiceterm::log_debug;

use super::mouse::{disable_mouse, enable_mouse};
use super::render::{
    build_clear_bottom_rows_bytes, build_clear_bottom_rows_cup_only_bytes, clear_overlay_panel,
    clear_status_banner, clear_status_banner_at, clear_status_line, terminal_family,
    write_overlay_panel, write_status_banner, write_status_line, TerminalFamily,
};
use super::WriterMessage;
use crate::config::HudBorderStyle;
use crate::status_line::{format_status_banner, StatusLineState};
use crate::theme::Theme;
use crate::HudStyle;

const OUTPUT_FLUSH_INTERVAL_MS: u64 = 16;
const CURSOR_PRECLEAR_COOLDOWN_MS: u64 = 220;
#[cfg(test)]
const CURSOR_CLAUDE_BANNER_PRECLEAR_COOLDOWN_MS: u64 = 180;
const CLAUDE_JETBRAINS_BANNER_PRECLEAR_COOLDOWN_MS: u64 = 90;
const CLAUDE_JETBRAINS_IDLE_REDRAW_HOLD_MS: u64 = 500;
const CLAUDE_JETBRAINS_SCROLL_IDLE_REDRAW_HOLD_MS: u64 = 200;
const JETBRAINS_PRECLEAR_COOLDOWN_MS: u64 = 260;
const CODEX_JETBRAINS_SCROLL_REDRAW_MIN_INTERVAL_MS: u64 = 320;
const CODEX_JETBRAINS_SCROLL_IDLE_REDRAW_HOLD_MS: u64 = 320;
const CLAUDE_JETBRAINS_SCROLL_REDRAW_MIN_INTERVAL_MS: u64 = 150;
const CLAUDE_CURSOR_SCROLL_REDRAW_MIN_INTERVAL_MS: u64 = 900;
const CURSOR_CLAUDE_TYPING_REDRAW_HOLD_MS: u64 = 450;
const CURSOR_CLAUDE_INPUT_REPAIR_DELAY_MS: u64 = 140;
const CLAUDE_JETBRAINS_CURSOR_RESTORE_SETTLE_MS: u64 = 140;
const CLAUDE_JETBRAINS_COMPOSER_REPAIR_DELAY_MS: u64 = 140;
const CLAUDE_JETBRAINS_COMPOSER_REPAIR_QUIET_MS: u64 = 700;
const CLAUDE_JETBRAINS_COMPOSER_RECENT_INPUT_MS: u64 = 1500;
const CLAUDE_JETBRAINS_RESIZE_REPAIR_WINDOW_MS: u64 = 600;
const CLAUDE_JETBRAINS_DESTRUCTIVE_CLEAR_IMMEDIATE_REPAINT_COOLDOWN_MS: u64 = 220;
const CLAUDE_JETBRAINS_STARTUP_SCREEN_CLEAR: &[u8] = b"\x1b[2J\x1b[H";
const CLAUDE_IDE_NON_SCROLL_REDRAW_MIN_INTERVAL_MS: u64 = 700;
const CLAUDE_HUD_DEBUG_ENV: &str = "VOICETERM_DEBUG_CLAUDE_HUD";
const CLAUDE_LONG_THINK_STATUS_MARKERS: &[&[u8]] = &[
    b"baked for ",
    b"brewed for ",
    b"churned for ",
    b"cogitated for ",
    b"cooked for ",
    b"crunched for ",
    b"worked for ",
    b"simmered for ",
    b"sauteed for ",
    b"toasted for ",
    b"marinated for ",
    b"whisked for ",
    b"boondoggling",
    b"waddling",
    b"hashing",
    b"metamorphosing",
    b"enchanting",
    b"ruminating",
    b"evaporating",
];

fn parse_debug_env_flag(raw: &str) -> bool {
    matches!(
        raw.trim().to_ascii_lowercase().as_str(),
        "1" | "true" | "yes" | "on" | "debug"
    )
}

fn claude_hud_debug_enabled() -> bool {
    static ENABLED: OnceLock<bool> = OnceLock::new();
    *ENABLED.get_or_init(|| {
        env::var(CLAUDE_HUD_DEBUG_ENV)
            .map(|raw| parse_debug_env_flag(&raw))
            // In debug/dev binaries, default this on so real-world repros
            // capture enough evidence even if the env var was omitted.
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

fn debug_text_preview(text: &str, max_chars: usize) -> String {
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

fn log_claude_hud_anomaly(message: &str) {
    if claude_hud_debug_enabled() {
        log_debug(&format!("[claude-hud-anomaly] {message}"));
    }
}

#[cfg(test)]
type TerminalSizeHook = fn() -> io::Result<(u16, u16)>;

#[cfg(test)]
thread_local! {
    static TERMINAL_SIZE_HOOK: Cell<Option<TerminalSizeHook>> = const { Cell::new(None) };
}

#[cfg(test)]
fn set_terminal_size_hook(hook: Option<TerminalSizeHook>) {
    TERMINAL_SIZE_HOOK.with(|slot| slot.set(hook));
}

fn normalize_terminal_size(cols: u16, rows: u16) -> (u16, u16) {
    let normalized_cols = if cols == 0 {
        crate::terminal::resolved_cols(0)
    } else {
        cols
    };
    let normalized_rows = if rows == 0 {
        crate::terminal::resolved_rows(0)
    } else {
        rows
    };
    (normalized_cols, normalized_rows)
}

fn read_terminal_size() -> io::Result<(u16, u16)> {
    let measured = {
        #[cfg(test)]
        {
            if let Some(hook) = TERMINAL_SIZE_HOOK.with(|slot| slot.get()) {
                hook()
            } else {
                terminal_size()
            }
        }
        #[cfg(not(test))]
        {
            terminal_size()
        }
    };

    let (cols, rows) = match measured {
        Ok((cols, rows)) => normalize_terminal_size(cols, rows),
        Err(_) => normalize_terminal_size(0, 0),
    };
    if cols == 0 || rows == 0 {
        return Err(io::Error::new(
            io::ErrorKind::Other,
            "terminal size unavailable",
        ));
    }
    Ok((cols, rows))
}

fn backend_label_contains(pattern: &str) -> bool {
    env::var("VOICETERM_BACKEND_LABEL")
        .map(|label| label.to_ascii_lowercase().contains(pattern))
        .unwrap_or(false)
}

fn is_codex_backend() -> bool {
    backend_label_contains("codex")
}

fn is_claude_backend() -> bool {
    backend_label_contains("claude")
}

fn is_transient_jetbrains_claude_geometry_collapse(
    terminal_family: TerminalFamily,
    claude_backend: bool,
    current_rows: u16,
    current_cols: u16,
    next_rows: u16,
    next_cols: u16,
) -> bool {
    terminal_family == TerminalFamily::JetBrains
        && claude_backend
        && current_rows >= 10
        && current_cols > 0
        && next_cols == current_cols
        && next_rows <= 2
}

fn claude_jetbrains_has_recent_input(now: Instant, last_user_input_at: Instant) -> bool {
    now.duration_since(last_user_input_at)
        <= Duration::from_millis(CLAUDE_JETBRAINS_COMPOSER_RECENT_INPUT_MS)
}

#[derive(Debug, Clone)]
pub(super) struct OverlayPanel {
    pub(super) content: String,
    pub(super) height: usize,
}

#[derive(Debug, Default)]
struct DisplayState {
    status: Option<String>,
    enhanced_status: Option<StatusLineState>,
    overlay_panel: Option<OverlayPanel>,
    banner_height: usize,
    /// Last non-zero banner height, kept across prompt-suppression transitions
    /// so pre-clear continues to scrub HUD rows even when the banner is hidden.
    preclear_banner_height: usize,
    /// Last absolute start-row anchor where a banner frame was rendered.
    /// Used to scrub stale frames if anchor drifts due geometry timing.
    banner_anchor_row: Option<u16>,
    banner_lines: Vec<String>,
    force_full_banner_redraw: bool,
}

impl DisplayState {
    fn has_any(&self) -> bool {
        self.status.is_some() || self.enhanced_status.is_some() || self.overlay_panel.is_some()
    }

    fn should_force_full_banner_redraw_on_output(&self, terminal_family: TerminalFamily) -> bool {
        if self.overlay_panel.is_some() || self.status.is_some() {
            return true;
        }
        // Multi-row HUDs need full repaint after terminal row scrolling.
        // On Cursor, skipping this can leave only the changing main row visible
        // while border/buttons rows scroll away under heavy output.
        match terminal_family {
            // JetBrains: suppress output-triggered HUD redraw when Claude
            // is active.  Claude Code's TUI uses DEC save/restore (\x1b7/\x1b8)
            // in its own rendering; the save slot is shared globally, so our
            // HUD redraw's \x1b7 can be overwritten by Claude's output before
            // our \x1b8 fires, leaving the cursor stuck inside the HUD.
            // The HUD still redraws on timer ticks when output is idle.
            TerminalFamily::JetBrains => false,
            TerminalFamily::Cursor | TerminalFamily::Other => self.banner_height > 1,
        }
    }
}

#[derive(Debug, Default)]
struct PendingState {
    status: Option<String>,
    enhanced_status: Option<StatusLineState>,
    overlay_panel: Option<OverlayPanel>,
    clear_status: bool,
    clear_overlay: bool,
}

impl PendingState {
    fn has_any(&self) -> bool {
        self.status.is_some()
            || self.enhanced_status.is_some()
            || self.overlay_panel.is_some()
            || self.clear_status
            || self.clear_overlay
    }
}

fn status_clear_height_for_redraw(current_height: usize, next_height: usize) -> usize {
    if current_height > next_height {
        current_height
    } else {
        0
    }
}

fn should_use_previous_banner_lines(
    force_full_banner_redraw: bool,
    force_redraw_after_preclear: bool,
) -> bool {
    // Transition redraws that follow a pre-clear must repaint all HUD lines.
    // The terminal rows were already wiped; reusing cached previous-lines can
    // skip writes and leave the HUD visually blank.
    !force_full_banner_redraw && !force_redraw_after_preclear
}

fn should_use_previous_banner_lines_for_profile(
    terminal_family: TerminalFamily,
    force_full_banner_redraw: bool,
    force_redraw_after_preclear: bool,
) -> bool {
    if terminal_family == TerminalFamily::JetBrains {
        // JediTerm can leave stale prompt/input text in unchanged HUD lanes
        // when line-diff redraw skips rows. Always repaint all banner rows.
        // This applies to both Claude and Codex backends — scrolling output
        // pushes HUD rows off screen and line-diff skips rewriting them.
        return false;
    }
    should_use_previous_banner_lines(force_full_banner_redraw, force_redraw_after_preclear)
}

fn preclear_height(display: &DisplayState) -> usize {
    if let Some(panel) = display.overlay_panel.as_ref() {
        panel.height
    } else if display.preclear_banner_height > 1 {
        // Use preclear_banner_height (last non-zero value) instead of
        // banner_height so prompt-suppression transitions don't disable
        // pre-clear and allow old HUD frames to scroll into the content area.
        display.preclear_banner_height
    } else {
        0
    }
}

fn should_preclear_bottom_rows(
    family: TerminalFamily,
    may_scroll_rows: bool,
    display: &DisplayState,
    status_clear_pending: bool,
    codex_jetbrains: bool,
    cursor_claude_startup_preclear: bool,
    cursor_claude_banner_preclear: bool,
    claude_jetbrains_banner_preclear: bool,
    claude_jetbrains_cup_preclear_safe: bool,
    now: Instant,
    last_preclear_at: Instant,
) -> bool {
    if !may_scroll_rows || preclear_height(display) == 0 {
        return false;
    }
    match family {
        TerminalFamily::JetBrains => {
            if claude_jetbrains_banner_preclear {
                // JetBrains + Claude: only run pre-clear when the chunk begins
                // with absolute cursor positioning. This allows a CUP-only
                // pre-clear (no DEC save/restore slot collision) without
                // risking prompt/input jumps to row 1.
                return claude_jetbrains_cup_preclear_safe
                    && now.duration_since(last_preclear_at)
                        >= Duration::from_millis(CLAUDE_JETBRAINS_BANNER_PRECLEAR_COOLDOWN_MS);
            }
            // Codex and other backends: keep conservative transition-only pre-clear.
            (status_clear_pending || display.overlay_panel.is_some())
                && !codex_jetbrains
                && now.duration_since(last_preclear_at)
                    >= Duration::from_millis(JETBRAINS_PRECLEAR_COOLDOWN_MS)
        }
        // Cursor should avoid banner pre-clear because it can visibly jitter the
        // active composer line while typing during heavy tool output. Keep a
        // conservative pre-clear path for explicit overlay panels and
        // suppression clear transitions that must scrub stale border fragments.
        // Also allow one startup pre-clear in Claude mode so first-frame HUD
        // rows do not get scrolled into duplicate ghost fragments.
        TerminalFamily::Cursor => {
            let transition_preclear = display.overlay_panel.is_some()
                || status_clear_pending
                || cursor_claude_startup_preclear;
            if transition_preclear {
                return now.duration_since(last_preclear_at)
                    >= Duration::from_millis(CURSOR_PRECLEAR_COOLDOWN_MS);
            }
            if cursor_claude_banner_preclear {
                // Cursor+Claude scroll streams can smear HUD rows into transcript
                // history if we wait for cadence windows; pre-clear every
                // scrolling chunk and redraw immediately.
                return true;
            }
            false
        }
        // Preserve legacy behavior for non-profiled terminals.
        TerminalFamily::Other => true,
    }
}

fn scroll_redraw_min_interval_for_profile(
    family: TerminalFamily,
    codex_backend: bool,
    claude_backend: bool,
) -> Option<Duration> {
    if family == TerminalFamily::JetBrains {
        if codex_backend {
            Some(Duration::from_millis(
                CODEX_JETBRAINS_SCROLL_REDRAW_MIN_INTERVAL_MS,
            ))
        } else if claude_backend {
            Some(Duration::from_millis(
                CLAUDE_JETBRAINS_SCROLL_REDRAW_MIN_INTERVAL_MS,
            ))
        } else {
            None
        }
    } else if family == TerminalFamily::Cursor && claude_backend {
        Some(Duration::from_millis(
            CLAUDE_CURSOR_SCROLL_REDRAW_MIN_INTERVAL_MS,
        ))
    } else {
        None
    }
}

fn should_force_scroll_full_redraw(
    min_interval: Option<Duration>,
    now: Instant,
    last_scroll_redraw_at: Instant,
) -> bool {
    if let Some(interval) = min_interval {
        return now.duration_since(last_scroll_redraw_at) >= interval;
    }
    true
}

fn pty_output_can_mutate_cursor_line(bytes: &[u8]) -> bool {
    if bytes.iter().any(|byte| matches!(byte, b'\r' | 0x08 | 0x7f)) {
        return true;
    }
    contains_cursor_mutation_csi(bytes)
}

fn csi_param_contains_token(params: &[u8], token: u8) -> bool {
    if params.is_empty() {
        return false;
    }
    let mut start = 0usize;
    while start < params.len() {
        let mut end = start;
        while end < params.len() && params[end] != b';' {
            end += 1;
        }
        let slice = &params[start..end];
        if slice.len() == 1 && slice[0] == token {
            return true;
        }
        start = end.saturating_add(1);
    }
    false
}

fn pty_output_contains_destructive_clear(bytes: &[u8]) -> bool {
    let mut idx = 0usize;
    while idx + 1 < bytes.len() {
        if bytes[idx] != 0x1b {
            idx += 1;
            continue;
        }
        let next = bytes[idx + 1];
        if next == b'c' {
            // RIS (ESC c) resets terminal state and clears visible content.
            return true;
        }
        if next != b'[' {
            idx += 2;
            continue;
        }
        let mut cursor = idx + 2;
        while cursor < bytes.len() {
            let byte = bytes[cursor];
            if (0x40..=0x7e).contains(&byte) {
                if byte == b'J' {
                    let params = &bytes[idx + 2..cursor];
                    if csi_param_contains_token(params, b'2')
                        || csi_param_contains_token(params, b'3')
                    {
                        return true;
                    }
                }
                idx = cursor + 1;
                break;
            }
            cursor += 1;
        }
        if cursor >= bytes.len() {
            break;
        }
    }
    false
}

fn contains_cursor_mutation_csi(bytes: &[u8]) -> bool {
    let mut idx = 0usize;
    while idx + 2 < bytes.len() {
        if bytes[idx] != 0x1b || bytes[idx + 1] != b'[' {
            idx += 1;
            continue;
        }
        let mut cursor = idx + 2;
        while cursor < bytes.len() {
            let byte = bytes[cursor];
            if (0x40..=0x7e).contains(&byte) {
                return matches!(
                    byte,
                    b'A' | b'B'
                        | b'C'
                        | b'D'
                        | b'E'
                        | b'F'
                        | b'G'
                        | b'H'
                        | b'f'
                        | b'd'
                        | b'J'
                        | b'K'
                        | b's'
                        | b'u'
                );
            }
            cursor += 1;
        }
        // Truncated CSI sequence: defer until next chunk.
        return false;
    }
    false
}

fn bytes_contains_sequence(bytes: &[u8], needle: &[u8]) -> bool {
    !needle.is_empty()
        && bytes.len() >= needle.len()
        && bytes.windows(needle.len()).any(|window| window == needle)
}

fn bytes_contains_sequence_ascii_case_insensitive(bytes: &[u8], needle: &[u8]) -> bool {
    !needle.is_empty()
        && bytes.len() >= needle.len()
        && bytes
            .windows(needle.len())
            .any(|window| window.eq_ignore_ascii_case(needle))
}

fn bytes_contains_any_ascii_case_insensitive(bytes: &[u8], needles: &[&[u8]]) -> bool {
    needles
        .iter()
        .any(|needle| bytes_contains_sequence_ascii_case_insensitive(bytes, needle))
}

fn parse_single_csi_param_u16(params: &[u8]) -> Option<u16> {
    if params.is_empty() {
        return Some(1);
    }
    if params.contains(&b';') {
        return None;
    }
    let mut value: u16 = 0;
    for &byte in params {
        if !byte.is_ascii_digit() {
            return None;
        }
        value = value
            .saturating_mul(10)
            .saturating_add((byte - b'0') as u16);
    }
    if value == 0 {
        Some(1)
    } else {
        Some(value)
    }
}

fn bytes_contains_short_cursor_up_csi(bytes: &[u8]) -> bool {
    bytes_contains_cursor_up_csi_at_least(bytes, 1, Some(3))
}

fn bytes_contains_cursor_up_csi_at_least(
    bytes: &[u8],
    min_rows: u16,
    max_rows: Option<u16>,
) -> bool {
    let mut idx = 0usize;
    while idx + 2 < bytes.len() {
        if bytes[idx] != 0x1b || bytes[idx + 1] != b'[' {
            idx += 1;
            continue;
        }
        let mut cursor = idx + 2;
        while cursor < bytes.len() {
            let byte = bytes[cursor];
            if (0x40..=0x7e).contains(&byte) {
                if byte == b'A' {
                    let params = &bytes[idx + 2..cursor];
                    if let Some(rows_up) = parse_single_csi_param_u16(params) {
                        let within_max = max_rows.map_or(true, |max| rows_up <= max);
                        if rows_up >= min_rows && within_max {
                            return true;
                        }
                    }
                }
                idx = cursor + 1;
                break;
            }
            cursor += 1;
        }
        if cursor >= bytes.len() {
            break;
        }
    }
    false
}

fn chunk_looks_like_claude_composer_keystroke(bytes: &[u8]) -> bool {
    if bytes.len() < 24 {
        return false;
    }
    // Claude composer updates in JetBrains arrive as synchronized-output
    // packets and include short cursor-up edits (typically 1A/2A/3A).  Long
    // wrapped-input packets can exceed 512 bytes and use several variants, so
    // avoid matching a single exact shape.
    let synchronized_packet = bytes_contains_sequence(bytes, b"\x1b[?2026h")
        && bytes_contains_sequence(bytes, b"\x1b[?2026l");
    if !synchronized_packet {
        return false;
    }
    let has_short_cursor_up = bytes_contains_short_cursor_up_csi(bytes);
    let has_inverse_cursor_marker =
        bytes_contains_sequence(bytes, b"\x1b[7m") && bytes_contains_sequence(bytes, b"\x1b[27m");
    let has_inline_line_erase = bytes_contains_sequence(bytes, b"\x1b[2K");
    has_short_cursor_up && (has_inverse_cursor_marker || has_inline_line_erase)
}

fn chunk_looks_like_claude_synchronized_cursor_rewrite(bytes: &[u8]) -> bool {
    if bytes.len() < 24 {
        return false;
    }
    let synchronized_packet = bytes_contains_sequence(bytes, b"\x1b[?2026h")
        && bytes_contains_sequence(bytes, b"\x1b[?2026l");
    if !synchronized_packet {
        return false;
    }
    let has_cursor_up = bytes_contains_cursor_up_csi_at_least(bytes, 2, None);
    if !has_cursor_up {
        return false;
    }
    let has_large_cursor_up = bytes_contains_cursor_up_csi_at_least(bytes, 4, None);
    let has_status_text =
        bytes_contains_any_ascii_case_insensitive(
            bytes,
            &[b"(thinking)", b"shortcuts", b"press", b"ctrl+o to expand"],
        ) || bytes_contains_any_ascii_case_insensitive(bytes, CLAUDE_LONG_THINK_STATUS_MARKERS);
    let has_inline_line_erase = bytes_contains_sequence(bytes, b"\x1b[2K");
    has_status_text || (has_large_cursor_up && has_inline_line_erase)
}

fn pty_chunk_starts_with_absolute_cursor_position(bytes: &[u8]) -> bool {
    if bytes.is_empty() {
        return false;
    }

    let mut idx = 0usize;
    let mut saw_absolute = false;
    let mut saw_disallowed_before_absolute = false;
    while idx < bytes.len() {
        let byte = bytes[idx];
        if byte == 0x1b {
            if idx + 1 >= bytes.len() {
                return false;
            }
            match bytes[idx + 1] {
                b'[' => {
                    let mut cursor = idx + 2;
                    while cursor < bytes.len() {
                        let final_byte = bytes[cursor];
                        if (0x40..=0x7e).contains(&final_byte) {
                            if matches!(final_byte, b'H' | b'f' | b'd' | b'G') {
                                if saw_disallowed_before_absolute {
                                    return false;
                                }
                                saw_absolute = true;
                                idx = cursor + 1;
                                break;
                            }
                            if !saw_absolute {
                                // Allow style/mode setup before absolute CUP.
                                if !matches!(final_byte, b'm' | b'h' | b'l') {
                                    return false;
                                }
                            }
                            idx = cursor + 1;
                            break;
                        }
                        cursor += 1;
                    }
                    if cursor >= bytes.len() {
                        return false;
                    }
                    continue;
                }
                b']' => {
                    // OSC: skip until BEL or ST (ESC \).
                    let mut cursor = idx + 2;
                    let mut terminated = false;
                    while cursor < bytes.len() {
                        if bytes[cursor] == 0x07 {
                            terminated = true;
                            cursor += 1;
                            break;
                        }
                        if bytes[cursor] == 0x1b
                            && cursor + 1 < bytes.len()
                            && bytes[cursor + 1] == b'\\'
                        {
                            terminated = true;
                            cursor += 2;
                            break;
                        }
                        cursor += 1;
                    }
                    if !terminated {
                        return false;
                    }
                    idx = cursor;
                    continue;
                }
                b'7' | b'8' => {
                    // Disallow DEC save/restore before first absolute move.
                    // If we pre-clear first, Claude's leading DECSC would save
                    // our clear cursor location, then DECRC can jump back into
                    // HUD rows and smear border fragments into transcript.
                    if !saw_absolute {
                        saw_disallowed_before_absolute = true;
                    }
                    idx += 2;
                    continue;
                }
                _ => {
                    idx += 2;
                    continue;
                }
            }
        }

        if byte.is_ascii_control() {
            if byte == b'\0' {
                idx += 1;
                continue;
            }
            // Any non-null control before absolute positioning is unsafe.
            if !saw_absolute {
                return false;
            }
            idx += 1;
            continue;
        }

        // First printable byte must occur after absolute cursor positioning.
        return saw_absolute;
    }
    saw_absolute
}

fn should_force_non_scroll_banner_redraw(
    claude_flash_profile: bool,
    may_scroll_rows: bool,
    has_enhanced_status: bool,
    bytes: &[u8],
    now: Instant,
    last_scroll_redraw_at: Instant,
) -> bool {
    claude_flash_profile
        && !may_scroll_rows
        && has_enhanced_status
        && pty_output_can_mutate_cursor_line(bytes)
        && should_force_scroll_full_redraw(
            Some(Duration::from_millis(
                CLAUDE_IDE_NON_SCROLL_REDRAW_MIN_INTERVAL_MS,
            )),
            now,
            last_scroll_redraw_at,
        )
}

fn is_unsuppressed_full_hud(state: &StatusLineState) -> bool {
    !state.claude_prompt_suppressed && state.hud_style == HudStyle::Full
}

const CURSOR_TRACKER_MAX_CARRY_BYTES: usize = 256;

fn track_cursor_save_restore(
    dec_active: bool,
    ansi_active: bool,
    carry: &[u8],
    bytes: &[u8],
) -> (bool, bool, bool, bool, Vec<u8>) {
    let mut stream = Vec::with_capacity(carry.len() + bytes.len());
    stream.extend_from_slice(carry);
    stream.extend_from_slice(bytes);

    let mut idx = 0usize;
    let mut dec_active_state = dec_active;
    let mut ansi_active_state = ansi_active;
    let mut saw_save = false;
    let mut saw_restore = false;
    let mut carry_start = None;

    while idx < stream.len() {
        if stream[idx] != 0x1b {
            idx += 1;
            continue;
        }

        if idx + 1 >= stream.len() {
            carry_start = Some(idx);
            break;
        }

        let esc_idx = idx;
        match stream[idx + 1] {
            b'7' => {
                dec_active_state = true;
                saw_save = true;
                idx += 2;
            }
            b'8' => {
                dec_active_state = false;
                saw_restore = true;
                idx += 2;
            }
            b'[' => {
                idx += 2;
                let mut saw_final = false;
                while idx < stream.len() {
                    let byte = stream[idx];
                    idx += 1;
                    if (0x40..=0x7e).contains(&byte) {
                        saw_final = true;
                        if byte == b's' {
                            ansi_active_state = true;
                            saw_save = true;
                        } else if byte == b'u' {
                            ansi_active_state = false;
                            saw_restore = true;
                        }
                        break;
                    }
                }
                if !saw_final {
                    carry_start = Some(esc_idx);
                    break;
                }
            }
            b']' => {
                idx += 2;
                let mut terminated = false;
                while idx < stream.len() {
                    if stream[idx] == 0x07 {
                        terminated = true;
                        idx += 1;
                        break;
                    }
                    if stream[idx] == 0x1b && idx + 1 < stream.len() && stream[idx + 1] == b'\\' {
                        terminated = true;
                        idx += 2;
                        break;
                    }
                    idx += 1;
                }
                if !terminated {
                    carry_start = Some(esc_idx);
                    break;
                }
            }
            _ => {
                idx += 2;
            }
        }
    }

    let mut next_carry = carry_start.map_or_else(Vec::new, |start| stream[start..].to_vec());
    if next_carry.len() > CURSOR_TRACKER_MAX_CARRY_BYTES {
        next_carry.truncate(CURSOR_TRACKER_MAX_CARRY_BYTES);
    }

    (
        dec_active_state,
        ansi_active_state,
        saw_save,
        saw_restore,
        next_carry,
    )
}

pub(super) struct WriterState {
    stdout: io::Stdout,
    terminal_family: TerminalFamily,
    display: DisplayState,
    pending: PendingState,
    needs_redraw: bool,
    rows: u16,
    cols: u16,
    pty_line_col_estimate: usize,
    force_redraw_after_preclear: bool,
    last_preclear_at: Instant,
    last_scroll_redraw_at: Instant,
    last_output_at: Instant,
    last_output_flush_at: Instant,
    last_status_draw_at: Instant,
    last_user_input_at: Instant,
    cursor_claude_input_repair_due: Option<Instant>,
    jetbrains_dec_cursor_saved_active: bool,
    jetbrains_ansi_cursor_saved_active: bool,
    jetbrains_cursor_restore_settle_until: Option<Instant>,
    jetbrains_cursor_escape_carry: Vec<u8>,
    jetbrains_claude_composer_repair_due: Option<Instant>,
    jetbrains_claude_repair_skip_quiet_window: bool,
    jetbrains_claude_resize_repair_until: Option<Instant>,
    jetbrains_claude_startup_screen_clear_pending: bool,
    jetbrains_claude_last_destructive_clear_repaint_at: Option<Instant>,
    theme: Theme,
    mouse_enabled: bool,
    cursor_startup_scroll_preclear_pending: bool,
}

impl WriterState {
    pub(super) fn new() -> Self {
        Self {
            stdout: io::stdout(),
            terminal_family: terminal_family(),
            display: DisplayState::default(),
            pending: PendingState::default(),
            needs_redraw: false,
            rows: 0,
            cols: 0,
            pty_line_col_estimate: 0,
            force_redraw_after_preclear: false,
            last_preclear_at: Instant::now() - Duration::from_millis(CURSOR_PRECLEAR_COOLDOWN_MS),
            last_scroll_redraw_at: Instant::now()
                - Duration::from_millis(CLAUDE_JETBRAINS_SCROLL_REDRAW_MIN_INTERVAL_MS),
            last_output_at: Instant::now(),
            last_output_flush_at: Instant::now(),
            last_status_draw_at: Instant::now(),
            last_user_input_at: Instant::now()
                - Duration::from_millis(CURSOR_CLAUDE_TYPING_REDRAW_HOLD_MS),
            cursor_claude_input_repair_due: None,
            jetbrains_dec_cursor_saved_active: false,
            jetbrains_ansi_cursor_saved_active: false,
            jetbrains_cursor_restore_settle_until: None,
            jetbrains_cursor_escape_carry: Vec::new(),
            jetbrains_claude_composer_repair_due: None,
            jetbrains_claude_repair_skip_quiet_window: false,
            jetbrains_claude_resize_repair_until: None,
            jetbrains_claude_startup_screen_clear_pending: true,
            jetbrains_claude_last_destructive_clear_repaint_at: None,
            theme: Theme::default(),
            mouse_enabled: false,
            cursor_startup_scroll_preclear_pending: true,
        }
    }

    pub(super) fn handle_message(&mut self, message: WriterMessage) -> bool {
        match message {
            WriterMessage::PtyOutput(bytes) => {
                let codex_backend = is_codex_backend();
                let claude_backend = is_claude_backend();
                let codex_jetbrains =
                    self.terminal_family == TerminalFamily::JetBrains && codex_backend;
                let claude_jetbrains =
                    self.terminal_family == TerminalFamily::JetBrains && claude_backend;
                let jetbrains_claude_startup_clear =
                    claude_jetbrains && self.jetbrains_claude_startup_screen_clear_pending;
                if jetbrains_claude_startup_clear {
                    self.jetbrains_claude_startup_screen_clear_pending = false;
                }
                let cursor_claude =
                    self.terminal_family == TerminalFamily::Cursor && claude_backend;
                let claude_hud_debug =
                    claude_hud_debug_enabled() && (cursor_claude || claude_jetbrains);
                let claude_non_scroll_redraw_profile = claude_jetbrains || cursor_claude;
                let scroll_redraw_min_interval = scroll_redraw_min_interval_for_profile(
                    self.terminal_family,
                    codex_backend,
                    claude_backend,
                );
                let flash_sensitive_scroll_profile =
                    codex_jetbrains || claude_jetbrains || cursor_claude;
                let may_scroll_rows = pty_output_may_scroll_rows(
                    self.cols as usize,
                    &mut self.pty_line_col_estimate,
                    &bytes,
                    // Treat CR bursts as scroll-like for Codex/JetBrains HUD cadence.
                    codex_jetbrains,
                );
                let now = Instant::now();
                let claude_jetbrains_recent_input = claude_jetbrains
                    && claude_jetbrains_has_recent_input(now, self.last_user_input_at);
                let claude_jetbrains_composer_keystroke = claude_jetbrains_recent_input
                    && chunk_looks_like_claude_composer_keystroke(&bytes);
                let claude_jetbrains_full_hud_active = claude_jetbrains
                    && self.display.overlay_panel.is_none()
                    && (self
                        .display
                        .enhanced_status
                        .as_ref()
                        .is_some_and(is_unsuppressed_full_hud)
                        || self
                            .pending
                            .enhanced_status
                            .as_ref()
                            .is_some_and(is_unsuppressed_full_hud));
                let claude_jetbrains_synchronized_cursor_rewrite = claude_jetbrains
                    && claude_jetbrains_full_hud_active
                    && chunk_looks_like_claude_synchronized_cursor_rewrite(&bytes);
                let claude_jetbrains_non_scroll_cursor_mutation = claude_jetbrains
                    && claude_jetbrains_full_hud_active
                    && pty_output_can_mutate_cursor_line(&bytes)
                    && ((!may_scroll_rows && claude_jetbrains_recent_input)
                        || claude_jetbrains_synchronized_cursor_rewrite);
                let claude_jetbrains_destructive_clear = claude_jetbrains
                    && claude_jetbrains_full_hud_active
                    && pty_output_contains_destructive_clear(&bytes);
                let claude_jetbrains_recent_destructive_clear_repaint = claude_jetbrains
                    && self
                        .jetbrains_claude_last_destructive_clear_repaint_at
                        .is_some_and(|last| {
                            now.duration_since(last)
                                < Duration::from_millis(
                                    CLAUDE_JETBRAINS_DESTRUCTIVE_CLEAR_IMMEDIATE_REPAINT_COOLDOWN_MS,
                                )
                        });
                let mut claude_jetbrains_chunk_touches_cursor_save_restore = false;
                if claude_jetbrains {
                    let (
                        dec_active_after_chunk,
                        ansi_active_after_chunk,
                        saw_save,
                        saw_restore,
                        next_escape_carry,
                    ) = track_cursor_save_restore(
                        self.jetbrains_dec_cursor_saved_active,
                        self.jetbrains_ansi_cursor_saved_active,
                        &self.jetbrains_cursor_escape_carry,
                        &bytes,
                    );
                    claude_jetbrains_chunk_touches_cursor_save_restore = saw_save || saw_restore;
                    self.jetbrains_dec_cursor_saved_active = dec_active_after_chunk;
                    self.jetbrains_ansi_cursor_saved_active = ansi_active_after_chunk;
                    self.jetbrains_cursor_escape_carry = next_escape_carry;
                    if saw_save {
                        self.jetbrains_cursor_restore_settle_until = None;
                    }
                    if saw_restore || (!dec_active_after_chunk && !ansi_active_after_chunk) {
                        self.jetbrains_cursor_restore_settle_until = Some(
                            now + Duration::from_millis(CLAUDE_JETBRAINS_CURSOR_RESTORE_SETTLE_MS),
                        );
                    }
                }
                let cursor_claude_startup_preclear =
                    cursor_claude && self.cursor_startup_scroll_preclear_pending;
                let cursor_claude_banner_preclear =
                    cursor_claude && self.display.overlay_panel.is_none();
                // JetBrains+Claude uses CUP-only pre-clear when chunks start
                // with absolute positioning to avoid stacked HUD ghost rows.
                let claude_jetbrains_banner_preclear =
                    claude_jetbrains && self.display.overlay_panel.is_none();
                let claude_jetbrains_cup_preclear_safe = claude_jetbrains_banner_preclear
                    && (pty_chunk_starts_with_absolute_cursor_position(&bytes)
                        || claude_jetbrains_synchronized_cursor_rewrite);
                let preclear_blocked_for_recent_input = claude_jetbrains
                    && should_defer_non_urgent_redraw_for_recent_input(
                        self.terminal_family,
                        claude_backend,
                        now,
                        self.last_user_input_at,
                    );
                let profile_should_preclear = should_preclear_bottom_rows(
                    self.terminal_family,
                    may_scroll_rows,
                    &self.display,
                    self.pending.clear_status,
                    codex_jetbrains,
                    cursor_claude_startup_preclear,
                    cursor_claude_banner_preclear,
                    claude_jetbrains_banner_preclear,
                    claude_jetbrains_cup_preclear_safe,
                    now,
                    self.last_preclear_at,
                );
                let claude_jetbrains_legacy_preclear_safe = claude_jetbrains_banner_preclear
                    && may_scroll_rows
                    && !claude_jetbrains_cup_preclear_safe
                    && !claude_jetbrains_chunk_touches_cursor_save_restore
                    && !self.jetbrains_dec_cursor_saved_active
                    && !self.jetbrains_ansi_cursor_saved_active
                    && now.duration_since(self.last_preclear_at)
                        >= Duration::from_millis(CLAUDE_JETBRAINS_BANNER_PRECLEAR_COOLDOWN_MS);
                let in_resize_repair_window = claude_jetbrains
                    && self
                        .jetbrains_claude_resize_repair_until
                        .is_some_and(|until| now < until);
                let should_preclear = (profile_should_preclear
                    || claude_jetbrains_legacy_preclear_safe
                    || (claude_jetbrains_banner_preclear && in_resize_repair_window))
                    && !claude_jetbrains_destructive_clear
                    && !preclear_blocked_for_recent_input;
                let pre_clear = if should_preclear {
                    if claude_jetbrains_cup_preclear_safe {
                        build_clear_bottom_rows_cup_only_bytes(
                            self.rows,
                            preclear_height(&self.display),
                        )
                    } else {
                        build_clear_bottom_rows_bytes(self.rows, preclear_height(&self.display))
                    }
                } else {
                    Vec::new()
                };
                let pre_cleared = !pre_clear.is_empty();
                if claude_hud_debug {
                    log_debug(&format!(
                        "[claude-hud-debug] writer pty chunk (bytes={}, may_scroll={}, preclear={}, startup_clear={}, force_full_before={}, force_after_preclear_before={}, pending_clear_status={}, pending_clear_overlay={}): \"{}\"",
                        bytes.len(),
                        may_scroll_rows,
                        pre_cleared,
                        jetbrains_claude_startup_clear,
                        self.display.force_full_banner_redraw,
                        self.force_redraw_after_preclear,
                        self.pending.clear_status,
                        self.pending.clear_overlay,
                        debug_bytes_preview(&bytes, 120)
                    ));
                }

                if jetbrains_claude_startup_clear {
                    if let Err(err) = self.stdout.write_all(CLAUDE_JETBRAINS_STARTUP_SCREEN_CLEAR) {
                        log_debug(&format!("startup screen clear write failed: {err}"));
                        return false;
                    }
                }
                let write_result = if pre_clear.is_empty() {
                    self.stdout.write_all(&bytes)
                } else {
                    let mut combined = pre_clear;
                    combined.extend_from_slice(&bytes);
                    self.stdout.write_all(&combined)
                };
                if let Err(err) = write_result {
                    log_debug(&format!("stdout write_all failed: {err}"));
                    return false;
                }
                if pre_cleared {
                    self.last_preclear_at = now;
                    if cursor_claude_startup_preclear {
                        self.cursor_startup_scroll_preclear_pending = false;
                    }
                    if cursor_claude_banner_preclear {
                        // Keep redraw in the same cycle as pre-clear so the HUD
                        // does not visibly blink off during streaming output.
                        self.force_redraw_after_preclear = true;
                        // After pre-clear, the terminal no longer contains prior
                        // banner lines. Force a full repaint instead of line-diff.
                        self.display.force_full_banner_redraw = true;
                    } else if claude_jetbrains_banner_preclear {
                        // JetBrains+Claude redraw must stay idle-gated to avoid
                        // DECSC/DECRC collision while Claude is streaming.
                        self.display.force_full_banner_redraw = true;
                        self.needs_redraw = true;
                        if in_resize_repair_window {
                            self.force_redraw_after_preclear = true;
                        }
                    }
                }
                self.last_output_at = now;
                if self.display.has_any() {
                    let claude_jetbrains_immediate_keystroke_repaint =
                        claude_jetbrains_composer_keystroke
                            && !claude_jetbrains_chunk_touches_cursor_save_restore
                            && !self.jetbrains_dec_cursor_saved_active
                            && !self.jetbrains_ansi_cursor_saved_active;
                    if claude_jetbrains_immediate_keystroke_repaint {
                        // JetBrains+Claude composer keystroke packets can wipe HUD rows
                        // instantly (cursor-up + inline erase). Repaint in the same cycle
                        // to avoid visible per-keystroke blink.
                        self.display.force_full_banner_redraw = true;
                        self.force_redraw_after_preclear = true;
                        self.needs_redraw = true;
                        self.jetbrains_cursor_restore_settle_until = None;
                        self.jetbrains_claude_composer_repair_due = None;
                        self.jetbrains_claude_repair_skip_quiet_window = false;
                    }
                    if claude_jetbrains_synchronized_cursor_rewrite
                        && !claude_jetbrains_immediate_keystroke_repaint
                    {
                        // Claude's synchronized cursor rewrite packets can touch HUD
                        // rows for multiple consecutive chunks. Do not repaint
                        // immediately per chunk; rely on the coalesced repair marker
                        // below so JetBrains+Claude redraws once after the burst.
                        self.display.force_full_banner_redraw = true;
                        self.needs_redraw = true;
                        self.jetbrains_cursor_restore_settle_until = None;
                    }
                    if claude_jetbrains_composer_keystroke
                        || claude_jetbrains_non_scroll_cursor_mutation
                    {
                        // JetBrains+Claude cursor-mutation packets are volatile.
                        // Keep one pending repair marker per burst, then redraw
                        // only after the burst settles; repeated re-arming inside
                        // the same burst can retrigger redraw races.
                        let hud_active = self.display.overlay_panel.is_none()
                            && (self
                                .display
                                .enhanced_status
                                .as_ref()
                                .is_some_and(|state| !state.claude_prompt_suppressed)
                                || self
                                    .pending
                                    .enhanced_status
                                    .as_ref()
                                    .is_some_and(|state| !state.claude_prompt_suppressed));
                        if hud_active && !claude_jetbrains_immediate_keystroke_repaint {
                            self.display.force_full_banner_redraw = true;
                            self.needs_redraw = true;
                            if self.jetbrains_claude_composer_repair_due.is_none() {
                                let repair_due = now
                                    + Duration::from_millis(
                                        CLAUDE_JETBRAINS_COMPOSER_REPAIR_DELAY_MS,
                                    );
                                self.jetbrains_claude_composer_repair_due = Some(repair_due);
                                // Keep repair redraws quiet-window gated by default.
                                // Immediate bypass during continuous synchronized packets
                                // can retrigger redraw races and stacked HUD remnants.
                                self.jetbrains_claude_repair_skip_quiet_window = false;
                                if claude_hud_debug_enabled() {
                                    log_debug(&format!(
                                        "[claude-hud-debug] scheduled jetbrains+claude composer repair redraw (due_in_ms={})",
                                        repair_due.saturating_duration_since(now).as_millis()
                                    ));
                                }
                            }
                        }
                    }
                    // PTY output may scroll/overwrite the HUD rows even if banner text did not
                    // change. Gemini compact HUD reserves a stable single row, so avoid forcing
                    // full repaint there to reduce textbox flicker while output streams.
                    // Only force full repaint when output can actually scroll rows.
                    if may_scroll_rows
                        && self
                            .display
                            .should_force_full_banner_redraw_on_output(self.terminal_family)
                        && should_force_scroll_full_redraw(
                            scroll_redraw_min_interval,
                            now,
                            self.last_scroll_redraw_at,
                        )
                    {
                        self.display.force_full_banner_redraw = true;
                        self.last_scroll_redraw_at = now;
                    }
                    // Claude IDE terminals can emit non-scrolling echo updates while
                    // the cursor briefly sits in HUD rows. Without occasional full
                    // banner rewrites, line-diff redraw can skip repaint and leave
                    // typed fragments visible inside the HUD.
                    //
                    // JetBrains: skip ALL output-triggered HUD redraws.  Claude
                    // Code's TUI shares the DEC save/restore slot (\x1b7/\x1b8),
                    // so redrawing the HUD during active PTY output corrupts
                    // cursor position.  HUD redraws happen on timer ticks when
                    // output is idle instead.
                    let non_scroll_line_mutation =
                        if self.terminal_family != TerminalFamily::JetBrains {
                            let result = should_force_non_scroll_banner_redraw(
                                claude_non_scroll_redraw_profile,
                                may_scroll_rows,
                                self.display.enhanced_status.is_some(),
                                &bytes,
                                now,
                                self.last_scroll_redraw_at,
                            );
                            if result {
                                self.display.force_full_banner_redraw = true;
                                self.last_scroll_redraw_at = now;
                            }
                            result
                        } else {
                            false
                        };
                    // Cursor+Claude: Claude Code redraws its own status hints on
                    // every keystroke echo, actively clearing the bottom rows where
                    // the HUD lives.  The 700ms non-scroll throttle above is too
                    // slow; force an immediate full HUD repaint whenever cursor-
                    // mutating CSI is detected so the HUD doesn't stay erased.
                    // (Skipped on JetBrains — see note above.)
                    if cursor_claude
                        && !may_scroll_rows
                        && self.display.enhanced_status.is_some()
                        && pty_output_can_mutate_cursor_line(&bytes)
                    {
                        self.display.force_full_banner_redraw = true;
                        self.force_redraw_after_preclear = true;
                    }
                    // (Skipped on JetBrains — see note above.)
                    let cursor_claude_destructive_clear_repaint = cursor_claude
                        && self
                            .display
                            .enhanced_status
                            .as_ref()
                            .is_some_and(|status| !status.claude_prompt_suppressed)
                        && pty_output_contains_destructive_clear(&bytes);
                    let jetbrains_claude_destructive_clear_repaint =
                        claude_jetbrains_destructive_clear;
                    let destructive_clear_repaint = cursor_claude_destructive_clear_repaint
                        || jetbrains_claude_destructive_clear_repaint;
                    if destructive_clear_repaint {
                        // Destructive clears can erase HUD/input anchor rows.
                        // Cursor+Claude always repaints immediately. For
                        // JetBrains+Claude, repaint immediately only when the
                        // shared cursor save/restore slot is not active; otherwise
                        // arm a near-term repair that bypasses the quiet window.
                        self.display.force_full_banner_redraw = true;
                        let jetbrains_cursor_slot_busy = claude_jetbrains
                            && (claude_jetbrains_chunk_touches_cursor_save_restore
                                || self.jetbrains_dec_cursor_saved_active
                                || self.jetbrains_ansi_cursor_saved_active);
                        let immediate_reanchor_allowed = !jetbrains_cursor_slot_busy
                            && !(jetbrains_claude_destructive_clear_repaint
                                && claude_jetbrains_recent_destructive_clear_repaint);
                        if immediate_reanchor_allowed {
                            self.force_redraw_after_preclear = true;
                            if jetbrains_claude_destructive_clear_repaint {
                                self.jetbrains_claude_last_destructive_clear_repaint_at = Some(now);
                            }
                        }
                        self.needs_redraw = true;
                        self.last_scroll_redraw_at = now;
                        if jetbrains_claude_destructive_clear_repaint {
                            if self.jetbrains_claude_composer_repair_due.is_none() {
                                let repair_due = now
                                    + Duration::from_millis(
                                        CLAUDE_JETBRAINS_COMPOSER_REPAIR_DELAY_MS,
                                    );
                                self.jetbrains_claude_composer_repair_due = Some(repair_due);
                                if claude_hud_debug_enabled() {
                                    log_debug(&format!(
                                        "[claude-hud-debug] scheduled jetbrains+claude destructive-clear repair redraw (due_in_ms={})",
                                        repair_due.saturating_duration_since(now).as_millis()
                                    ));
                                }
                            }
                            self.jetbrains_claude_repair_skip_quiet_window = true;
                        }
                        if claude_hud_debug {
                            if jetbrains_claude_destructive_clear_repaint {
                                if immediate_reanchor_allowed {
                                    log_debug(
                                        "[claude-hud-debug] forcing redraw after destructive clear sequence (jetbrains+claude)",
                                    );
                                } else {
                                    log_debug(
                                        "[claude-hud-debug] destructive clear redraw throttled; using deferred repair (jetbrains+claude)",
                                    );
                                }
                            } else {
                                log_debug(
                                    "[claude-hud-debug] forcing immediate redraw after destructive clear sequence",
                                );
                            }
                        }
                    }
                    if pre_cleared
                        && self.terminal_family == TerminalFamily::JetBrains
                        && !codex_jetbrains
                        && !claude_jetbrains
                    {
                        let transition_sensitive_preclear = self.pending.clear_status
                            || self.pending.clear_overlay
                            || self.pending.overlay_panel.is_some();
                        if transition_sensitive_preclear {
                            // Transition clears need immediate repaint to avoid
                            // stale border fragments during prompt/overlay handoff.
                            self.force_redraw_after_preclear = true;
                        }
                    }
                    let output_redraw_needed = if claude_jetbrains {
                        // JetBrains + Claude: don't redraw the HUD
                        // synchronously in this output cycle (cursor
                        // save/restore conflicts with Claude's own
                        // \x1b7/\x1b8).  Instead, mark force_full so the
                        // idle-gated redraw in maybe_redraw_status repaints
                        // all lines (the HUD was scrolled away).  Set
                        // needs_redraw so the idle check actually fires —
                        // the since_output < idle_ms guard in
                        // maybe_redraw_status will defer until output
                        // settles.
                        if may_scroll_rows {
                            self.display.force_full_banner_redraw = true;
                            self.needs_redraw = true;
                        }
                        if claude_jetbrains_non_scroll_cursor_mutation {
                            self.display.force_full_banner_redraw = true;
                            self.needs_redraw = true;
                        }
                        if claude_jetbrains_composer_keystroke {
                            self.needs_redraw = true;
                        }
                        // Return false so the immediate maybe_redraw_status
                        // call below doesn't double-set.
                        false
                    } else if codex_jetbrains {
                        // JetBrains + Codex: defer scroll-triggered redraws
                        // to the idle-gated timer.  JediTerm lacks scroll
                        // regions, so painting the HUD mid-scroll leaves
                        // ghost frames in the scrollback.  Setting the flags
                        // here lets maybe_redraw_status repaint once output
                        // settles (320ms idle hold).
                        if may_scroll_rows {
                            self.display.force_full_banner_redraw = true;
                            self.needs_redraw = true;
                        }
                        // Non-scroll events use normal triggers.
                        pre_cleared || non_scroll_line_mutation || destructive_clear_repaint
                    } else {
                        self.display.force_full_banner_redraw
                            || pre_cleared
                            || non_scroll_line_mutation
                            || destructive_clear_repaint
                            || (may_scroll_rows && !flash_sensitive_scroll_profile)
                    };
                    if output_redraw_needed {
                        self.needs_redraw = true;
                    }
                }
                // When force_redraw_after_preclear is set, skip this intermediate
                // flush so the PTY output and the HUD redraw are sent to the
                // terminal in a single atomic batch via maybe_redraw_status's
                // flush.  Without this, the terminal paints the cleared HUD rows
                // before the HUD redraw arrives, producing visible flicker.
                if !self.force_redraw_after_preclear
                    && (now.duration_since(self.last_output_flush_at)
                        >= Duration::from_millis(OUTPUT_FLUSH_INTERVAL_MS)
                        || bytes.contains(&b'\n'))
                {
                    if let Err(err) = self.stdout.flush() {
                        log_debug(&format!("stdout flush failed: {err}"));
                    } else {
                        self.last_output_flush_at = now;
                    }
                }
                // Keep overlays/HUD responsive while PTY output is continuous.
                // Without this, recv_timeout-based redraws can be starved.
                self.maybe_redraw_status();
                if claude_hud_debug {
                    log_debug(&format!(
                        "[claude-hud-debug] writer pty post (needs_redraw={}, force_full_after={}, force_after_preclear_after={}, banner_height={}, preclear_banner_height={})",
                        self.needs_redraw,
                        self.display.force_full_banner_redraw,
                        self.force_redraw_after_preclear,
                        self.display.banner_height,
                        self.display.preclear_banner_height
                    ));
                }
            }
            WriterMessage::Status { text } => {
                self.pending.status = Some(text);
                self.pending.enhanced_status = None;
                self.needs_redraw = true;
                self.maybe_redraw_status();
            }
            WriterMessage::EnhancedStatus(state) => {
                if claude_hud_debug_enabled()
                    && self.terminal_family == TerminalFamily::Cursor
                    && is_claude_backend()
                {
                    log_debug(&format!(
                        "[claude-hud-debug] writer received EnhancedStatus (rows={}, cols={}, hud_style={:?}, prompt_suppressed={}, message=\"{}\")",
                        self.rows,
                        self.cols,
                        state.hud_style,
                        state.claude_prompt_suppressed,
                        debug_text_preview(&state.message, 72)
                    ));
                }
                self.pending.enhanced_status = Some(state);
                self.pending.status = None;
                self.needs_redraw = true;
                self.maybe_redraw_status();
            }
            WriterMessage::ShowOverlay { content, height } => {
                self.pending.overlay_panel = Some(OverlayPanel { content, height });
                self.pending.clear_overlay = false;
                self.needs_redraw = true;
                self.maybe_redraw_status();
            }
            WriterMessage::ClearOverlay => {
                self.pending.overlay_panel = None;
                self.pending.clear_overlay = true;
                self.needs_redraw = true;
                self.maybe_redraw_status();
            }
            WriterMessage::ClearStatus => {
                if claude_hud_debug_enabled()
                    && self.terminal_family == TerminalFamily::Cursor
                    && is_claude_backend()
                {
                    let hud_style = self
                        .display
                        .enhanced_status
                        .as_ref()
                        .map(|state| state.hud_style);
                    let prompt_suppressed = self
                        .display
                        .enhanced_status
                        .as_ref()
                        .map(|state| state.claude_prompt_suppressed);
                    log_debug(&format!(
                        "[claude-hud-debug] writer received ClearStatus (rows={}, cols={}, banner_height={}, anchor_row={:?}, hud_style={:?}, prompt_suppressed={:?})",
                        self.rows,
                        self.cols,
                        self.display.banner_height,
                        self.display.banner_anchor_row,
                        hud_style,
                        prompt_suppressed
                    ));
                }
                self.pending.status = None;
                self.pending.enhanced_status = None;
                self.pending.clear_status = true;
                // Clear transitions should not wait behind output-throttle windows.
                self.force_redraw_after_preclear = true;
                self.needs_redraw = true;
                self.maybe_redraw_status();
            }
            WriterMessage::Bell { count } => {
                let sequence = vec![0x07; count.max(1) as usize];
                if let Err(err) = self.stdout.write_all(&sequence) {
                    log_debug(&format!("bell write failed: {err}"));
                }
                if let Err(err) = self.stdout.flush() {
                    log_debug(&format!("bell flush failed: {err}"));
                }
            }
            WriterMessage::Resize { rows, cols } => {
                if is_transient_jetbrains_claude_geometry_collapse(
                    self.terminal_family,
                    is_claude_backend(),
                    self.rows,
                    self.cols,
                    rows,
                    cols,
                ) {
                    if claude_hud_debug_enabled() {
                        log_debug(&format!(
                            "[claude-hud-debug] ignoring transient resize collapse sample (current_rows={}, current_cols={}, new_rows={}, new_cols={})",
                            self.rows, self.cols, rows, cols
                        ));
                    }
                    return true;
                }
                if self.rows == rows && self.cols == cols {
                    return true;
                }
                if claude_hud_debug_enabled()
                    && self.terminal_family == TerminalFamily::Cursor
                    && is_claude_backend()
                {
                    log_debug(&format!(
                        "[claude-hud-debug] writer received Resize (old_rows={}, old_cols={}, new_rows={}, new_cols={})",
                        self.rows, self.cols, rows, cols
                    ));
                }
                if self.rows > 0 {
                    // Clear HUD/overlay at the old terminal geometry before moving to the new one.
                    // This prevents stale frames when startup rows are briefly reported incorrectly.
                    if let Some(panel) = self.display.overlay_panel.as_ref() {
                        let _ = clear_overlay_panel(&mut self.stdout, self.rows, panel.height);
                    }
                    if self.display.banner_height > 1 {
                        let _ = clear_status_banner(
                            &mut self.stdout,
                            self.rows,
                            self.display.banner_height,
                        );
                    } else if self.display.status.is_some()
                        || self.display.enhanced_status.is_some()
                    {
                        let _ = clear_status_line(&mut self.stdout, self.rows, self.cols.max(1));
                    }
                    self.display.banner_lines.clear();
                    self.display.banner_anchor_row = None;
                    self.display.force_full_banner_redraw = true;
                    let _ = self.stdout.flush();
                }
                self.rows = rows;
                self.cols = cols;
                self.pty_line_col_estimate = 0;
                self.force_redraw_after_preclear = false;
                self.last_preclear_at =
                    Instant::now() - Duration::from_millis(CURSOR_PRECLEAR_COOLDOWN_MS);
                self.last_scroll_redraw_at = Instant::now()
                    - Duration::from_millis(CLAUDE_JETBRAINS_SCROLL_REDRAW_MIN_INTERVAL_MS);
                self.cursor_startup_scroll_preclear_pending = true;
                self.jetbrains_dec_cursor_saved_active = false;
                self.jetbrains_ansi_cursor_saved_active = false;
                self.jetbrains_cursor_restore_settle_until = None;
                self.jetbrains_cursor_escape_carry.clear();
                self.jetbrains_claude_composer_repair_due = None;
                self.jetbrains_claude_repair_skip_quiet_window = false;
                if self.display.has_any() || self.pending.has_any() {
                    self.needs_redraw = true;
                    self.force_redraw_after_preclear = true;
                }
                if self.terminal_family == TerminalFamily::JetBrains && is_claude_backend() {
                    self.jetbrains_claude_resize_repair_until = Some(
                        Instant::now()
                            + Duration::from_millis(CLAUDE_JETBRAINS_RESIZE_REPAIR_WINDOW_MS),
                    );
                }
                self.maybe_redraw_status();
            }
            WriterMessage::SetTheme(new_theme) => {
                self.theme = new_theme;
                if self.display.has_any() {
                    self.needs_redraw = true;
                }
            }
            WriterMessage::EnableMouse => {
                enable_mouse(&mut self.stdout, &mut self.mouse_enabled);
            }
            WriterMessage::DisableMouse => {
                disable_mouse(&mut self.stdout, &mut self.mouse_enabled);
            }
            WriterMessage::UserInputActivity => {
                let now = Instant::now();
                self.last_user_input_at = now;
                let claude_backend = is_claude_backend();
                let cursor_claude =
                    self.terminal_family == TerminalFamily::Cursor && claude_backend;
                if cursor_claude
                    && self.display.overlay_panel.is_none()
                    && (self.display.enhanced_status.is_some()
                        || self.pending.enhanced_status.is_some())
                {
                    // Cursor+Claude can clear bottom HUD rows
                    // during typing bursts without emitting a scroll/CSI
                    // pattern we can classify. Schedule one low-rate repair
                    // redraw shortly after typing settles.
                    let repair_due =
                        now + Duration::from_millis(CURSOR_CLAUDE_INPUT_REPAIR_DELAY_MS);
                    self.cursor_claude_input_repair_due = Some(repair_due);
                    if claude_hud_debug_enabled() {
                        let hud_style = self
                            .display
                            .enhanced_status
                            .as_ref()
                            .map(|state| state.hud_style);
                        let prompt_suppressed = self
                            .display
                            .enhanced_status
                            .as_ref()
                            .map(|state| state.claude_prompt_suppressed);
                        log_debug(&format!(
                            "[claude-hud-debug] user input activity (rows={}, cols={}, banner_height={}, anchor_row={:?}, hud_style={:?}, prompt_suppressed={:?}, repair_due_in_ms={})",
                            self.rows,
                            self.cols,
                            self.display.banner_height,
                            self.display.banner_anchor_row,
                            hud_style,
                            prompt_suppressed,
                            repair_due.saturating_duration_since(now).as_millis()
                        ));
                    }
                    if let Some(state) = self.display.enhanced_status.as_ref() {
                        if !state.claude_prompt_suppressed && self.display.banner_height == 0 {
                            log_claude_hud_anomaly(&format!(
                                "user input observed unsuppressed HUD with zero banner height before repair scheduling (rows={}, cols={}, anchor_row={:?}, hud_style={:?})",
                                self.rows,
                                self.cols,
                                self.display.banner_anchor_row,
                                state.hud_style
                            ));
                        }
                    }
                }
            }
            WriterMessage::Shutdown => {
                // Disable mouse before exiting to restore terminal state
                disable_mouse(&mut self.stdout, &mut self.mouse_enabled);
                return false;
            }
        }
        true
    }

    pub(super) fn maybe_redraw_status(&mut self) {
        const STATUS_IDLE_MS: u64 = 50;
        const STATUS_MAX_WAIT_MS: u64 = 150;
        const PRIORITY_STATUS_IDLE_MS: u64 = 12;
        const PRIORITY_STATUS_MAX_WAIT_MS: u64 = 40;
        let now = Instant::now();
        let claude_cursor_debug = claude_hud_debug_enabled()
            && self.terminal_family == TerminalFamily::Cursor
            && is_claude_backend();
        if !self.needs_redraw {
            if let Some(due) = self.cursor_claude_input_repair_due {
                let claude_backend = is_claude_backend();
                let cursor_claude =
                    self.terminal_family == TerminalFamily::Cursor && claude_backend;
                if cursor_claude
                    && self.display.overlay_panel.is_none()
                    && (self.display.enhanced_status.is_some()
                        || self.pending.enhanced_status.is_some())
                    && now >= due
                {
                    self.display.force_full_banner_redraw = true;
                    if cursor_claude {
                        self.force_redraw_after_preclear = true;
                    }
                    self.needs_redraw = true;
                    self.cursor_claude_input_repair_due = None;
                    if claude_hud_debug_enabled() {
                        log_debug(
                            "[claude-hud-debug] scheduled cursor+claude HUD repair redraw fired",
                        );
                    }
                } else {
                    return;
                }
            } else {
                return;
            }
        }
        let since_output = now.duration_since(self.last_output_at);
        let since_draw = now.duration_since(self.last_status_draw_at);
        let suppression_transition_pending =
            self.pending
                .enhanced_status
                .as_ref()
                .is_some_and(|pending_state| {
                    self.display.enhanced_status.as_ref().map_or(
                        // Transition updates immediately following ClearStatus
                        // have no display snapshot but still need urgent redraw.
                        self.display.preclear_banner_height > 0,
                        |display_state| {
                            pending_state.claude_prompt_suppressed
                                != display_state.claude_prompt_suppressed
                        },
                    )
                });

        // In Claude/Cursor, keep the HUD stable while the user is actively
        // typing in the composer to prevent cursor flicker and redraw jitter.
        if should_defer_non_urgent_redraw_for_recent_input(
            self.terminal_family,
            is_claude_backend(),
            now,
            self.last_user_input_at,
        ) && !self.force_redraw_after_preclear
        {
            let minimal_hud_recovery = self.terminal_family == TerminalFamily::Cursor
                && is_claude_backend()
                && self.display.overlay_panel.is_none()
                && self.display.enhanced_status.is_some()
                && self.display.banner_height == 1;
            let urgent = self.pending.overlay_panel.is_some()
                || self.pending.clear_overlay
                || self.pending.clear_status
                || suppression_transition_pending;
            if claude_cursor_debug {
                log_debug(&format!(
                    "[claude-hud-debug] redraw deferred for recent input (needs_redraw={}, urgent={}, suppression_transition_pending={}, minimal_hud_recovery={}, pending_has_any={}, force_full={}, force_after_preclear={})",
                    self.needs_redraw,
                    urgent,
                    suppression_transition_pending,
                    minimal_hud_recovery,
                    self.pending.has_any(),
                    self.display.force_full_banner_redraw,
                    self.force_redraw_after_preclear
                ));
            }
            if !urgent && !minimal_hud_recovery {
                return;
            }
        }

        // Prioritize explicit status/overlay updates over passive PTY-driven repaints.
        // This keeps settings navigation and meter changes reactive under heavy backend output.
        let priority_update_pending = self.pending.has_any();
        let claude_jetbrains =
            self.terminal_family == TerminalFamily::JetBrains && is_claude_backend();
        let jetbrains_composer_repair_armed =
            claude_jetbrains && self.jetbrains_claude_composer_repair_due.is_some();
        let jetbrains_composer_repair_ready = self
            .jetbrains_claude_composer_repair_due
            .is_some_and(|due| now >= due);
        if claude_jetbrains
            && jetbrains_composer_repair_armed
            && !jetbrains_composer_repair_ready
            && self.pending.overlay_panel.is_none()
            && !self.pending.clear_overlay
            && !self.pending.clear_status
            && !suppression_transition_pending
            && !self.force_redraw_after_preclear
        {
            return;
        }
        if claude_jetbrains
            && jetbrains_composer_repair_ready
            && self.pending.overlay_panel.is_none()
            && !self.pending.clear_overlay
            && !self.pending.clear_status
            && !suppression_transition_pending
            && !self.force_redraw_after_preclear
            && !self.jetbrains_claude_repair_skip_quiet_window
            && since_output < Duration::from_millis(CLAUDE_JETBRAINS_COMPOSER_REPAIR_QUIET_MS)
        {
            return;
        }
        if claude_jetbrains
            && !self.force_redraw_after_preclear
            && (self.jetbrains_dec_cursor_saved_active || self.jetbrains_ansi_cursor_saved_active)
        {
            return;
        }
        if claude_jetbrains
            && !self.force_redraw_after_preclear
            && self
                .jetbrains_cursor_restore_settle_until
                .is_some_and(|until| now < until)
        {
            return;
        }
        if claude_jetbrains
            && self
                .jetbrains_cursor_restore_settle_until
                .is_some_and(|until| now >= until)
        {
            self.jetbrains_cursor_restore_settle_until = None;
        }
        let in_resize_repair_window = self
            .jetbrains_claude_resize_repair_until
            .is_some_and(|until| now < until);
        let claude_jetbrains_idle_gated_redraw = claude_jetbrains
            && !jetbrains_composer_repair_armed
            && !self.force_redraw_after_preclear
            && !in_resize_repair_window
            && self.pending.overlay_panel.is_none()
            && !self.pending.clear_overlay
            && !self.pending.clear_status
            && !suppression_transition_pending;
        let codex_jetbrains =
            self.terminal_family == TerminalFamily::JetBrains && is_codex_backend();
        // Codex+JetBrains: idle-gate scroll-triggered redraws so the HUD
        // is only repainted once output settles.  JediTerm lacks scroll
        // regions, so painting mid-scroll leaves ghost HUD frames.
        let codex_jetbrains_idle_gated_redraw = codex_jetbrains
            && self.display.force_full_banner_redraw
            && !self.force_redraw_after_preclear
            && self.pending.overlay_panel.is_none()
            && !self.pending.clear_overlay
            && !self.pending.clear_status
            && !suppression_transition_pending;
        let idle_ms = if claude_jetbrains_idle_gated_redraw {
            // Use shorter idle hold when the HUD was smeared by scrolling output
            // and needs a full repaint. Keep the full 500ms for passive redraws
            // to avoid redrawing in gaps between bursty non-scroll chunks.
            if self.display.force_full_banner_redraw {
                CLAUDE_JETBRAINS_SCROLL_IDLE_REDRAW_HOLD_MS
            } else {
                CLAUDE_JETBRAINS_IDLE_REDRAW_HOLD_MS
            }
        } else if codex_jetbrains_idle_gated_redraw {
            CODEX_JETBRAINS_SCROLL_IDLE_REDRAW_HOLD_MS
        } else if priority_update_pending {
            PRIORITY_STATUS_IDLE_MS
        } else {
            STATUS_IDLE_MS
        };
        let max_wait_ms = if priority_update_pending {
            PRIORITY_STATUS_MAX_WAIT_MS
        } else {
            STATUS_MAX_WAIT_MS
        };

        let jetbrains_idle_gated =
            claude_jetbrains_idle_gated_redraw || codex_jetbrains_idle_gated_redraw;
        let should_throttle_for_output = if jetbrains_idle_gated {
            // JetBrains+Claude/Codex can emit bursty chunks with brief gaps;
            // if we redraw HUD in those gaps, the next scroll chunk can drag
            // HUD chrome into transcript lines. Require true idle settle.
            since_output < Duration::from_millis(idle_ms)
        } else {
            since_output < Duration::from_millis(idle_ms)
                && since_draw < Duration::from_millis(max_wait_ms)
        };

        if !self.force_redraw_after_preclear
            && !suppression_transition_pending
            && should_throttle_for_output
        {
            return;
        }
        // Clear/transition redraws are anchor-sensitive. Refresh terminal size
        // once before clearing so stale row/col caches do not place the HUD at
        // a wrong origin after prompt/tool phases.
        if self.pending.clear_status
            || self.pending.clear_overlay
            || self.force_redraw_after_preclear
        {
            if let Ok((c, r)) = read_terminal_size() {
                if is_transient_jetbrains_claude_geometry_collapse(
                    self.terminal_family,
                    is_claude_backend(),
                    self.rows,
                    self.cols,
                    r,
                    c,
                ) {
                    if claude_hud_debug_enabled() {
                        log_debug(&format!(
                            "[claude-hud-debug] ignoring transient redraw geometry sample (current_rows={}, current_cols={}, measured_rows={}, measured_cols={})",
                            self.rows, self.cols, r, c
                        ));
                    }
                } else if self.rows != r || self.cols != c {
                    self.rows = r;
                    self.cols = c;
                    self.pty_line_col_estimate = 0;
                }
            }
        }
        if self.rows == 0 || self.cols == 0 {
            if let Ok((c, r)) = read_terminal_size() {
                if !is_transient_jetbrains_claude_geometry_collapse(
                    self.terminal_family,
                    is_claude_backend(),
                    self.rows,
                    self.cols,
                    r,
                    c,
                ) {
                    self.rows = r;
                    self.cols = c;
                }
            }
        }
        if self.rows == 0 || self.cols == 0 {
            // Keep pending redraw state intact and retry on the next writer tick.
            // This prevents startup HUD loss when IDE terminals briefly report no size.
            return;
        }
        let previous_banner_height = self.display.banner_height;
        let previous_hud_style = self
            .display
            .enhanced_status
            .as_ref()
            .map(|state| state.hud_style);
        let previous_prompt_suppressed = self
            .display
            .enhanced_status
            .as_ref()
            .map(|state| state.claude_prompt_suppressed);
        if self.pending.clear_status {
            let current_banner_height = self.display.banner_height;
            if current_banner_height > 1 {
                let _ = clear_status_banner(&mut self.stdout, self.rows, current_banner_height);
            } else {
                let _ = clear_status_line(&mut self.stdout, self.rows, self.cols);
            }
            self.display.status = None;
            self.display.enhanced_status = None;
            self.display.banner_height = 0;
            self.display.banner_anchor_row = None;
            self.display.banner_lines.clear();
            self.display.force_full_banner_redraw = true;
            self.pending.clear_status = false;
        }
        if self.pending.clear_overlay {
            if let Some(panel) = self.display.overlay_panel.as_ref() {
                let _ = clear_overlay_panel(&mut self.stdout, self.rows, panel.height);
            }
            self.display.overlay_panel = None;
            // Overlay clears underlying rows; force next HUD paint to redraw all banner lines.
            self.display.banner_lines.clear();
            self.display.force_full_banner_redraw = true;
            self.pending.clear_overlay = false;
        }
        if let Some(panel) = self.pending.overlay_panel.as_ref() {
            if let Some(current) = self.display.overlay_panel.as_ref() {
                if current.height != panel.height {
                    let _ = clear_overlay_panel(&mut self.stdout, self.rows, current.height);
                }
            }
        }
        if let Some(panel) = self.pending.overlay_panel.take() {
            self.display.overlay_panel = Some(panel);
        }
        if let Some(state) = self.pending.enhanced_status.take() {
            self.display.enhanced_status = Some(state);
            self.display.status = None;
        }
        if let Some(text) = self.pending.status.take() {
            self.display.status = Some(text);
            self.display.enhanced_status = None;
        }

        let flush_error = {
            let force_redraw_after_preclear = self.force_redraw_after_preclear;
            let rows = self.rows;
            let cols = self.cols;
            let theme = self.theme;
            let (
                stdout,
                overlay_panel,
                enhanced_status,
                status,
                current_banner_height,
                preclear_banner_height,
                banner_anchor_row,
                current_banner_lines,
                force_full_banner_redraw,
            ) = (
                &mut self.stdout,
                &self.display.overlay_panel,
                &self.display.enhanced_status,
                &self.display.status,
                &mut self.display.banner_height,
                &mut self.display.preclear_banner_height,
                &mut self.display.banner_anchor_row,
                &mut self.display.banner_lines,
                &mut self.display.force_full_banner_redraw,
            );
            if let Some(panel) = overlay_panel.as_ref() {
                let _ = write_overlay_panel(stdout, panel, rows, cols);
            } else if let Some(state) = enhanced_status.as_ref() {
                let mut render_state = state.clone();
                if self.terminal_family == TerminalFamily::JetBrains
                    && is_claude_backend()
                    && !render_state.claude_prompt_suppressed
                    && render_state.hud_style == HudStyle::Full
                {
                    // JetBrains+Claude fallback: keep full-HUD semantics but collapse
                    // the full frame into a single-line strip to avoid row drift under
                    // synchronized clear/redraw bursts in JetBrains.
                    if claude_hud_debug_enabled() {
                        log_debug(
                            "[claude-hud-debug] applying jetbrains+claude full-hud one-line fallback",
                        );
                    }
                    render_state.hud_border_style = HudBorderStyle::None;
                    render_state.full_hud_single_line = true;
                }
                let banner = format_status_banner(&render_state, theme, cols as usize);
                let new_anchor_row = if banner.height == 0 || rows == 0 {
                    None
                } else {
                    Some(
                        rows.saturating_sub(banner.height.min(rows as usize) as u16)
                            .saturating_add(1),
                    )
                };
                if claude_cursor_debug {
                    let next_hud_style = state.hud_style;
                    let next_prompt_suppressed = state.claude_prompt_suppressed;
                    let banner_height_changed = *current_banner_height != banner.height;
                    let hud_changed = previous_hud_style != Some(next_hud_style);
                    let suppression_changed =
                        previous_prompt_suppressed != Some(next_prompt_suppressed);
                    if banner_height_changed || hud_changed || suppression_changed {
                        log_debug(&format!(
                            "[claude-hud-debug] enhanced status render decision (rows={}, cols={}, prev_banner_height={}, next_banner_height={}, prev_anchor_row={:?}, next_anchor_row={:?}, hud_style={:?}, prompt_suppressed={}, message=\"{}\")",
                            rows,
                            cols,
                            *current_banner_height,
                            banner.height,
                            *banner_anchor_row,
                            new_anchor_row,
                            next_hud_style,
                            next_prompt_suppressed,
                            debug_text_preview(&state.message, 72)
                        ));
                    }
                }
                if let (Some(previous_anchor), Some(next_anchor)) =
                    (*banner_anchor_row, new_anchor_row)
                {
                    if previous_anchor != next_anchor && *current_banner_height > 0 {
                        let _ =
                            clear_status_banner_at(stdout, previous_anchor, *current_banner_height);
                    }
                }
                // Avoid full-frame clear on every redraw; only clear when banner shrinks.
                // write_status_banner already clears each line it writes.
                let clear_height =
                    status_clear_height_for_redraw(*current_banner_height, banner.height);
                if clear_height > 0 {
                    let _ = clear_status_banner(stdout, rows, clear_height);
                }
                *current_banner_height = banner.height;
                // Track last non-zero height so pre-clear keeps working during
                // prompt suppression (when format_status_banner returns height 0).
                if banner.height > 0 {
                    *preclear_banner_height = banner.height;
                }
                *banner_anchor_row = new_anchor_row;
                let use_previous_lines = should_use_previous_banner_lines_for_profile(
                    self.terminal_family,
                    *force_full_banner_redraw,
                    force_redraw_after_preclear,
                );
                if claude_cursor_debug && force_redraw_after_preclear {
                    log_debug(&format!(
                        "[claude-hud-debug] transition redraw mode: {} (force_full_banner_redraw={}, preclear_transition={})",
                        if use_previous_lines { "line-diff" } else { "full" },
                        *force_full_banner_redraw,
                        force_redraw_after_preclear
                    ));
                }
                let previous_lines = if use_previous_lines {
                    Some(current_banner_lines.as_slice())
                } else {
                    None
                };
                let _ = write_status_banner(stdout, &banner, rows, cols, previous_lines);
                *current_banner_lines = banner.lines.clone();
                *force_full_banner_redraw = false;
            } else if let Some(text) = status.as_deref() {
                let _ = write_status_line(stdout, text, rows, cols, theme);
                *banner_anchor_row = None;
                current_banner_lines.clear();
                *force_full_banner_redraw = true;
            }
            stdout.flush().err()
        };
        self.needs_redraw = false;
        self.force_redraw_after_preclear = false;
        if self
            .jetbrains_claude_composer_repair_due
            .is_some_and(|due| now >= due)
        {
            self.jetbrains_claude_composer_repair_due = None;
            self.jetbrains_claude_repair_skip_quiet_window = false;
            if claude_jetbrains && jetbrains_composer_repair_ready && claude_hud_debug_enabled() {
                log_debug("[claude-hud-debug] jetbrains+claude composer repair redraw committed");
            }
        }
        if self
            .jetbrains_claude_resize_repair_until
            .is_some_and(|until| now >= until)
        {
            self.jetbrains_claude_resize_repair_until = None;
        }
        if self
            .cursor_claude_input_repair_due
            .is_some_and(|due| now >= due)
        {
            self.cursor_claude_input_repair_due = None;
        }
        self.last_status_draw_at = now;
        if claude_cursor_debug {
            let current_hud_style = self
                .display
                .enhanced_status
                .as_ref()
                .map(|state| state.hud_style);
            let current_prompt_suppressed = self
                .display
                .enhanced_status
                .as_ref()
                .map(|state| state.claude_prompt_suppressed);
            log_debug(&format!(
                "[claude-hud-debug] redraw committed (rows={}, cols={}, banner_height={}, anchor_row={:?}, has_enhanced={}, has_overlay={}, has_status={}, hud_style={:?}, prompt_suppressed={:?}, changed_banner_height={}, changed_hud_style={}, changed_prompt_suppressed={})",
                self.rows,
                self.cols,
                self.display.banner_height,
                self.display.banner_anchor_row,
                self.display.enhanced_status.is_some(),
                self.display.overlay_panel.is_some(),
                self.display.status.is_some(),
                current_hud_style,
                current_prompt_suppressed,
                previous_banner_height != self.display.banner_height,
                previous_hud_style != current_hud_style,
                previous_prompt_suppressed != current_prompt_suppressed
            ));
        }
        if self.terminal_family == TerminalFamily::Cursor
            && is_claude_backend()
            && self.display.overlay_panel.is_none()
        {
            if let Some(state) = self.display.enhanced_status.as_ref() {
                if !state.claude_prompt_suppressed && self.display.banner_height == 0 {
                    log_claude_hud_anomaly(&format!(
                        "unsuppressed HUD committed with zero banner height (rows={}, cols={}, anchor_row={:?}, hud_style={:?}, needs_redraw={})",
                        self.rows,
                        self.cols,
                        self.display.banner_anchor_row,
                        state.hud_style,
                        self.needs_redraw
                    ));
                }
                if state.claude_prompt_suppressed && self.display.banner_height > 0 {
                    log_claude_hud_anomaly(&format!(
                        "suppressed HUD committed with non-zero banner height (rows={}, cols={}, banner_height={}, anchor_row={:?}, hud_style={:?})",
                        self.rows,
                        self.cols,
                        self.display.banner_height,
                        self.display.banner_anchor_row,
                        state.hud_style
                    ));
                }
            }
        }
        if let Some(err) = flush_error {
            log_debug(&format!("status redraw flush failed: {err}"));
        }
    }
}

/// Typing-hold redraw deferral constant for standard (non-Cursor) terminals.
/// Shorter than the Cursor value because standard terminals handle cursor
/// save/restore more reliably, but still long enough to batch rapid keystrokes.
const TYPING_REDRAW_HOLD_MS: u64 = 250;

fn should_defer_non_urgent_redraw_for_recent_input(
    terminal_family: TerminalFamily,
    _claude_backend: bool,
    now: Instant,
    last_user_input_at: Instant,
) -> bool {
    // Defer non-urgent HUD redraws while the user is actively typing on ALL
    // terminal/backend combinations.  Without this, every HUD repaint moves
    // the cursor to the bottom rows and back, producing visible flicker on
    // every keystroke.
    let hold_ms = match terminal_family {
        TerminalFamily::Cursor => CURSOR_CLAUDE_TYPING_REDRAW_HOLD_MS,
        _ => TYPING_REDRAW_HOLD_MS,
    };
    now.duration_since(last_user_input_at) < Duration::from_millis(hold_ms)
}

fn pty_output_may_scroll_rows(
    cols: usize,
    line_col_estimate: &mut usize,
    bytes: &[u8],
    treat_cr_as_scroll: bool,
) -> bool {
    if bytes.is_empty() {
        return false;
    }
    // Treat unknown terminal width as potentially scrolling when explicit line breaks appear.
    // Carriage return alone rewinds the current row and should not be treated as vertical scroll.
    if cols == 0 {
        if bytes.contains(&b'\n') || (treat_cr_as_scroll && bytes.contains(&b'\r')) {
            *line_col_estimate = 0;
            return true;
        }
        if bytes.contains(&b'\r') {
            *line_col_estimate = 0;
        }
        return false;
    }

    let mut may_scroll = false;
    let mut idx = 0usize;
    while idx < bytes.len() {
        let byte = bytes[idx];
        // Skip ANSI escape sequences so parameter bytes don't inflate column count.
        if byte == 0x1b {
            if idx + 1 < bytes.len() && bytes[idx + 1] == b'[' {
                // CSI sequence: skip until final byte in 0x40..=0x7E.
                idx += 2;
                while idx < bytes.len() {
                    if (0x40..=0x7e).contains(&bytes[idx]) {
                        // CSI S/T scroll the terminal content vertically. Count
                        // them as potential row movement so JetBrains+Codex can
                        // re-arm HUD repaint after resize-driven scroll bursts.
                        if matches!(bytes[idx], b'S' | b'T') {
                            may_scroll = true;
                            *line_col_estimate = 0;
                        }
                        idx += 1;
                        break;
                    }
                    idx += 1;
                }
            } else {
                // Two-byte escape (e.g. ESC 7, ESC 8): skip ESC + next byte.
                idx += 2;
            }
            continue;
        }
        match byte {
            b'\n' => {
                may_scroll = true;
                *line_col_estimate = 0;
            }
            b'\r' => {
                if treat_cr_as_scroll {
                    may_scroll = true;
                }
                *line_col_estimate = 0;
            }
            0x08 => {
                *line_col_estimate = line_col_estimate.saturating_sub(1);
            }
            b'\t' => {
                let next_tab = ((*line_col_estimate / 8) + 1) * 8;
                if next_tab >= cols {
                    may_scroll = true;
                    *line_col_estimate = 0;
                } else {
                    *line_col_estimate = next_tab;
                }
            }
            byte if !byte.is_ascii_control() => {
                *line_col_estimate += 1;
                if *line_col_estimate >= cols {
                    may_scroll = true;
                    *line_col_estimate = 0;
                }
            }
            _ => {}
        }
        idx += 1;
    }
    may_scroll
}

#[cfg(test)]
mod tests;
