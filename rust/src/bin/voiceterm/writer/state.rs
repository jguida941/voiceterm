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
const STARTUP_SCREEN_CLEAR: &[u8] = b"\x1b[2J\x1b[H";

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

use self::adapter_state::WriterAdapterState;
#[cfg(test)]
use self::chunk_analysis::bytes_contains_short_cursor_up_csi;
use self::chunk_analysis::{
    chunk_looks_like_claude_composer_keystroke,
    chunk_looks_like_claude_synchronized_cursor_rewrite,
    pty_chunk_starts_with_absolute_cursor_position, pty_output_can_mutate_cursor_line,
    pty_output_contains_destructive_clear, pty_output_contains_erase_display,
    track_cursor_save_restore,
};
use self::codex_overlay::CodexOverlayIsolation;
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

/// `Stdout` is line-buffered on terminals, so a PTY chunk containing a newline
/// can become visible even when VoiceTerm deliberately postpones `flush()`
/// until after its HUD repaint. JetBrains+Codex needs true explicit-flush
/// buffering so pre-clear, PTY output, and the replacement HUD reach JediTerm
/// as one write. Other runtime variants keep the direct stdout path unchanged.
struct DeferredWriter<W: Write> {
    inner: W,
    pending: Vec<u8>,
}

impl<W: Write> DeferredWriter<W> {
    fn new(inner: W) -> Self {
        Self {
            inner,
            pending: Vec::new(),
        }
    }

    #[cfg(test)]
    fn inner(&self) -> &W {
        &self.inner
    }
}

impl<W: Write> Write for DeferredWriter<W> {
    fn write(&mut self, bytes: &[u8]) -> io::Result<usize> {
        self.pending.extend_from_slice(bytes);
        Ok(bytes.len())
    }

    fn flush(&mut self) -> io::Result<()> {
        if !self.pending.is_empty() {
            self.inner.write_all(&self.pending)?;
            self.pending.clear();
        }
        self.inner.flush()
    }
}

impl<W: Write> Drop for DeferredWriter<W> {
    fn drop(&mut self) {
        let _ = self.flush();
    }
}

enum WriterOutput {
    Direct(io::Stdout),
    JetBrainsCodex(DeferredWriter<io::Stdout>),
    #[cfg(test)]
    Capture(Vec<u8>),
}

impl WriterOutput {
    fn for_runtime_profile(profile: RuntimeProfile) -> Self {
        if profile.runtime_variant.is_jetbrains_codex() {
            Self::JetBrainsCodex(DeferredWriter::new(io::stdout()))
        } else {
            Self::Direct(io::stdout())
        }
    }

    #[cfg(test)]
    fn is_jetbrains_codex_buffered(&self) -> bool {
        matches!(self, Self::JetBrainsCodex(_))
    }
}

impl Write for WriterOutput {
    fn write(&mut self, bytes: &[u8]) -> io::Result<usize> {
        match self {
            Self::Direct(stdout) => stdout.write(bytes),
            Self::JetBrainsCodex(stdout) => stdout.write(bytes),
            #[cfg(test)]
            Self::Capture(sink) => sink.write(bytes),
        }
    }

    fn flush(&mut self) -> io::Result<()> {
        match self {
            Self::Direct(stdout) => stdout.flush(),
            Self::JetBrainsCodex(stdout) => stdout.flush(),
            #[cfg(test)]
            Self::Capture(_) => Ok(()),
        }
    }
}

pub(super) struct WriterState {
    stdout: WriterOutput,
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
    adapter_state: WriterAdapterState,
    theme: Theme,
    mouse_enabled: bool,
    codex_overlay_isolation: CodexOverlayIsolation,
    child_scroll_region: scroll_region::ChildScrollRegionTracker,
    /// Incomplete trailing UTF-8 sequence from the last PTY chunk, written only
    /// once the child completes it so no HUD paint can land inside a character.
    utf8_tail: Vec<u8>,
    viewport_fence: viewport_fence::ViewportFence,
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
            stdout: WriterOutput::for_runtime_profile(runtime_profile),
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
            adapter_state: WriterAdapterState::for_runtime_profile(runtime_profile),
            theme: Theme::default(),
            mouse_enabled: false,
            codex_overlay_isolation: CodexOverlayIsolation::default(),
            child_scroll_region: scroll_region::ChildScrollRegionTracker::default(),
            utf8_tail: Vec::new(),
            viewport_fence: viewport_fence::ViewportFence::default(),
        }
    }

    /// Prepend the held tail and split off a trailing incomplete UTF-8 sequence,
    /// which stays held until the next chunk completes it.
    fn take_utf8_complete_prefix(&mut self, bytes: Vec<u8>) -> Vec<u8> {
        let mut stream = std::mem::take(&mut self.utf8_tail);
        stream.extend_from_slice(&bytes);
        let split = incomplete_utf8_tail_start(&stream);
        self.utf8_tail = stream.split_off(split);
        stream
    }

    /// Last row of the child viewport for the HUD currently shown (or pending).
    fn child_viewport_bottom(&self) -> u16 {
        let state = self
            .display
            .enhanced_status
            .as_ref()
            .or(self.pending.enhanced_status.as_ref());
        match state {
            Some(state) => crate::terminal::child_viewport_rows_for_banner(
                self.rows,
                self.cols,
                state.hud_style,
                state.prompt_suppressed,
            ),
            None => self.rows,
        }
    }

    /// JediTerm ignores DECSTBM, so the writer sets no region there and must
    /// fence the child viewport in software instead (Codex keeps its own path).
    fn fences_child_viewport(&self) -> bool {
        self.runtime_profile.terminal_family == TerminalHost::JetBrains
            && !self.runtime_profile.runtime_variant.is_jetbrains_codex()
    }

    fn terminal_family(&self) -> TerminalHost {
        self.runtime_profile.terminal_family
    }

    /// A writer whose output is captured in memory, for tests that judge the
    /// exact bytes a HUD paint leaves on the host terminal.
    #[cfg(test)]
    pub(super) fn with_capture_for_tests(
        terminal_family: TerminalHost,
        backend_family: BackendFamily,
    ) -> Self {
        let mut state =
            Self::with_runtime_profile(RuntimeProfile::resolve(terminal_family, backend_family));
        state.stdout = WriterOutput::Capture(Vec::new());
        state
    }

    #[cfg(test)]
    pub(super) fn captured_output(&self) -> &[u8] {
        match &self.stdout {
            WriterOutput::Capture(bytes) => bytes,
            _ => &[],
        }
    }

    #[cfg(test)]
    fn set_terminal_family_for_tests(&mut self, terminal_family: TerminalHost) {
        self.runtime_profile = self.runtime_profile.with_terminal_family(terminal_family);
        self.stdout = WriterOutput::for_runtime_profile(self.runtime_profile);
        self.adapter_state = WriterAdapterState::for_runtime_profile(self.runtime_profile);
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
            self.adapter_state
                .set_cursor_startup_scroll_preclear_pending(false);
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
            self.adapter_state
                .set_jetbrains_claude_last_destructive_clear_repaint_at(Some(now));
        }
        if redraw_policy.schedule_jetbrains_destructive_clear_repair
            && self
                .adapter_state
                .jetbrains_claude_composer_repair_due()
                .is_none()
        {
            let repair_due = now
                + self
                    .host_timing()
                    .claude_composer_repair_delay()
                    .unwrap_or_default();
            self.adapter_state
                .set_jetbrains_claude_composer_repair_due(Some(repair_due));
            if claude_hud_debug_enabled() {
                log_debug(&format!(
                    "[claude-hud-debug] scheduled jetbrains+claude destructive-clear repair redraw (due_in_ms={})",
                    repair_due.saturating_duration_since(now).as_millis()
                ));
            }
        }
        if redraw_policy.jetbrains_repair_skip_quiet_window {
            self.adapter_state
                .set_jetbrains_claude_repair_skip_quiet_window(true);
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

mod adapter_state;
mod chunk_analysis;
use chunk_analysis::incomplete_utf8_tail_start;
mod codex_overlay;
mod dispatch;
mod dispatch_pty;
pub(super) mod display;
mod policy;
mod profile;
mod redraw;
mod redraw_support;
mod scroll_region;
mod viewport_fence;

#[cfg(test)]
mod tests;
