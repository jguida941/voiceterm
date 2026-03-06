use crossterm::terminal::size as terminal_size;
use std::io::{self, Write};
use std::time::{Duration, Instant};
#[cfg(test)]
use std::{cell::Cell, thread_local};
use voiceterm::log_debug;

use super::mouse::{
    append_mouse_enable_sequence, disable_mouse, enable_mouse, mouse_enable_sequence_len,
    pty_chunk_disables_mouse_tracking,
};
use super::render::{
    clear_overlay_panel, clear_status_banner, clear_status_banner_at, clear_status_line,
    terminal_host, write_overlay_panel, write_status_banner, write_status_line,
};
use super::timing::{
    resolve_idle_redraw_timing, should_defer_non_urgent_redraw_for_recent_input,
    IdleRedrawTimingContext,
};
use super::WriterMessage;
use crate::config::HudBorderStyle;
use crate::hud_debug::{claude_hud_debug_enabled, debug_bytes_preview};
#[cfg(test)]
use crate::runtime_compat::BackendFamily;
use crate::runtime_compat::{HostTimingConfig, TerminalHost};
use crate::status_line::format_status_banner;
#[cfg(test)]
use crate::status_line::StatusLineState;
use crate::theme::Theme;
use crate::HudStyle;

const OUTPUT_FLUSH_INTERVAL_MS: u64 = 16;
#[cfg(test)]
const CURSOR_CLAUDE_BANNER_PRECLEAR_COOLDOWN_MS: u64 = 180;
const STARTUP_SCREEN_CLEAR: &[u8] = b"\x1b[2J\x1b[H";
#[cfg(test)]
const CURSOR_PRECLEAR_COOLDOWN_MS: u64 = 220;
#[cfg(test)]
const CLAUDE_JETBRAINS_BANNER_PRECLEAR_COOLDOWN_MS: u64 = 90;
#[cfg(test)]
const CLAUDE_JETBRAINS_IDLE_REDRAW_HOLD_MS: u64 = 500;
#[cfg(test)]
const JETBRAINS_PRECLEAR_COOLDOWN_MS: u64 = 260;
#[cfg(test)]
const CODEX_JETBRAINS_SCROLL_REDRAW_MIN_INTERVAL_MS: u64 = 320;
#[cfg(test)]
const CLAUDE_JETBRAINS_SCROLL_REDRAW_MIN_INTERVAL_MS: u64 = 150;
#[cfg(test)]
const CLAUDE_CURSOR_SCROLL_REDRAW_MIN_INTERVAL_MS: u64 = 900;
#[cfg(test)]
const CURSOR_CLAUDE_TYPING_REDRAW_HOLD_MS: u64 = 450;
#[cfg(test)]
const CLAUDE_JETBRAINS_COMPOSER_REPAIR_QUIET_MS: u64 = 700;
#[cfg(test)]
const CLAUDE_JETBRAINS_COMPOSER_RECENT_INPUT_MS: u64 = 1500;
#[cfg(test)]
const CLAUDE_IDE_NON_SCROLL_REDRAW_MIN_INTERVAL_MS: u64 = 700;
#[cfg(test)]
const TYPING_REDRAW_HOLD_MS: u64 = 250;

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
        return Err(io::Error::other("terminal size unavailable"));
    }
    Ok((cols, rows))
}

#[cfg(test)]
use self::chunk_analysis::bytes_contains_short_cursor_up_csi;
use self::chunk_analysis::{
    chunk_looks_like_claude_composer_keystroke,
    chunk_looks_like_claude_synchronized_cursor_rewrite,
    pty_chunk_starts_with_absolute_cursor_position, pty_output_can_mutate_cursor_line,
    pty_output_contains_destructive_clear, pty_output_contains_erase_display,
    track_cursor_save_restore,
};
#[cfg(test)]
use self::display::should_use_previous_banner_lines;
use self::display::{
    is_unsuppressed_full_hud, preclear_height, should_use_previous_banner_lines_for_profile,
    status_clear_height_for_redraw, DisplayState, OverlayPanel, PendingState,
};
#[cfg(test)]
use self::policy::scroll_redraw_min_interval_for_profile;
#[cfg(test)]
use self::policy::{
    should_force_non_scroll_banner_redraw, should_force_scroll_full_redraw,
    should_preclear_bottom_rows,
};
use self::policy::{
    PreclearOutcome, PreclearPolicy, PreclearPolicyContext, RedrawPolicy, RedrawPolicyContext,
};
use self::profile::{
    claude_jetbrains_has_recent_input, is_transient_jetbrains_claude_geometry_collapse,
    RuntimeProfile,
};
pub(super) struct WriterState {
    stdout: io::Stdout,
    runtime_profile: RuntimeProfile,
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
    cursor_startup_screen_clear_pending: bool,
    jetbrains_claude_last_destructive_clear_repaint_at: Option<Instant>,
    theme: Theme,
    mouse_enabled: bool,
    cursor_startup_scroll_preclear_pending: bool,
}

impl WriterState {
    pub(super) fn new() -> Self {
        let runtime_profile = RuntimeProfile::from_environment(terminal_host());
        Self::with_runtime_profile(runtime_profile)
    }

    fn with_runtime_profile(runtime_profile: RuntimeProfile) -> Self {
        let cursor_timing = HostTimingConfig::for_host(TerminalHost::Cursor);
        let scroll_redraw_min_interval = runtime_profile
            .scroll_redraw_min_interval
            .unwrap_or_default();
        Self {
            stdout: io::stdout(),
            runtime_profile,
            display: DisplayState::default(),
            pending: PendingState::default(),
            needs_redraw: false,
            rows: 0,
            cols: 0,
            pty_line_col_estimate: 0,
            force_redraw_after_preclear: false,
            last_preclear_at: Instant::now() - cursor_timing.preclear_cooldown(),
            last_scroll_redraw_at: Instant::now() - scroll_redraw_min_interval,
            last_output_at: Instant::now(),
            last_output_flush_at: Instant::now(),
            last_status_draw_at: Instant::now(),
            last_user_input_at: Instant::now() - cursor_timing.typing_redraw_hold(),
            cursor_claude_input_repair_due: None,
            jetbrains_dec_cursor_saved_active: false,
            jetbrains_ansi_cursor_saved_active: false,
            jetbrains_cursor_restore_settle_until: None,
            jetbrains_cursor_escape_carry: Vec::new(),
            jetbrains_claude_composer_repair_due: None,
            jetbrains_claude_repair_skip_quiet_window: false,
            jetbrains_claude_resize_repair_until: None,
            jetbrains_claude_startup_screen_clear_pending: true,
            cursor_startup_screen_clear_pending: runtime_profile.terminal_family
                == TerminalHost::Cursor,
            jetbrains_claude_last_destructive_clear_repaint_at: None,
            theme: Theme::default(),
            mouse_enabled: false,
            cursor_startup_scroll_preclear_pending: true,
        }
    }

    fn terminal_family(&self) -> TerminalHost {
        self.runtime_profile.terminal_family
    }

    #[cfg(test)]
    fn set_terminal_family_for_tests(&mut self, terminal_family: TerminalHost) {
        self.runtime_profile = self.runtime_profile.with_terminal_family(terminal_family);
    }

    fn host_timing(&self) -> HostTimingConfig {
        self.runtime_profile.host_timing
    }

    fn run_preclear_policy_pipeline(
        &self,
        context: PreclearPolicyContext<'_>,
    ) -> (Vec<u8>, PreclearOutcome) {
        let preclear_policy = PreclearPolicy::resolve(context);
        let pre_clear =
            preclear_policy.build_preclear_bytes(self.rows, preclear_height(&self.display));
        let preclear_outcome = preclear_policy.outcome(!pre_clear.is_empty());
        (pre_clear, preclear_outcome)
    }

    fn run_redraw_policy_pipeline(&self, context: RedrawPolicyContext<'_>) -> RedrawPolicy {
        RedrawPolicy::resolve(context)
    }

    fn apply_preclear_outcome(&mut self, preclear_outcome: PreclearOutcome, now: Instant) {
        if preclear_outcome.pre_cleared {
            self.last_preclear_at = now;
        }
        if preclear_outcome.consume_cursor_startup_preclear {
            self.cursor_startup_scroll_preclear_pending = false;
        }
        if preclear_outcome.force_redraw_after_preclear {
            // Keep redraw in the same cycle as pre-clear so the HUD
            // does not visibly blink off during streaming output.
            self.force_redraw_after_preclear = true;
        }
        if preclear_outcome.force_full_banner_redraw {
            // After pre-clear, the terminal no longer contains prior
            // banner lines. Force a full repaint instead of line-diff.
            self.display.force_full_banner_redraw = true;
        }
        if preclear_outcome.needs_redraw {
            // JetBrains+Claude redraw must stay idle-gated to avoid
            // DECSC/DECRC collision while Claude is streaming.
            self.needs_redraw = true;
        }
    }

    fn apply_redraw_policy_outcome(
        &mut self,
        redraw_policy: RedrawPolicy,
        now: Instant,
        claude_hud_debug: bool,
    ) {
        if redraw_policy.force_full_banner_redraw {
            self.display.force_full_banner_redraw = true;
        }
        if redraw_policy.force_redraw_after_preclear {
            self.force_redraw_after_preclear = true;
        }
        if redraw_policy.needs_redraw {
            self.needs_redraw = true;
        }
        if redraw_policy.update_last_scroll_redraw_at {
            self.last_scroll_redraw_at = now;
        }
        if redraw_policy.update_jetbrains_last_destructive_clear_repaint_at {
            self.jetbrains_claude_last_destructive_clear_repaint_at = Some(now);
        }
        if redraw_policy.schedule_jetbrains_destructive_clear_repair
            && self.jetbrains_claude_composer_repair_due.is_none()
        {
            let repair_due = now
                + self
                    .host_timing()
                    .claude_composer_repair_delay()
                    .unwrap_or_default();
            self.jetbrains_claude_composer_repair_due = Some(repair_due);
            if claude_hud_debug_enabled() {
                log_debug(&format!(
                    "[claude-hud-debug] scheduled jetbrains+claude destructive-clear repair redraw (due_in_ms={})",
                    repair_due.saturating_duration_since(now).as_millis()
                ));
            }
        }
        if redraw_policy.jetbrains_repair_skip_quiet_window {
            self.jetbrains_claude_repair_skip_quiet_window = true;
        }
        if redraw_policy.destructive_clear_repaint && claude_hud_debug {
            if redraw_policy.jetbrains_claude_destructive_clear_repaint {
                if redraw_policy.immediate_reanchor_allowed {
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

    pub(super) fn handle_message(&mut self, message: WriterMessage) -> bool {
        self.dispatch_message(message)
    }
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

mod chunk_analysis;
mod dispatch;
pub(super) mod display;
mod policy;
mod profile;
mod redraw;

#[cfg(test)]
mod tests;
