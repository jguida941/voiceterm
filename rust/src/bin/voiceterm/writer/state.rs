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
    build_clear_bottom_rows_bytes, clear_overlay_panel, clear_status_banner,
    clear_status_banner_at, clear_status_line, terminal_family, write_overlay_panel,
    write_status_banner, write_status_line, TerminalFamily,
};
use super::WriterMessage;
use crate::status_line::{format_status_banner, StatusLineState};
use crate::theme::Theme;

const OUTPUT_FLUSH_INTERVAL_MS: u64 = 16;
const CURSOR_PRECLEAR_COOLDOWN_MS: u64 = 220;
#[cfg(test)]
const CURSOR_CLAUDE_BANNER_PRECLEAR_COOLDOWN_MS: u64 = 180;
const JETBRAINS_PRECLEAR_COOLDOWN_MS: u64 = 260;
const CODEX_JETBRAINS_SCROLL_REDRAW_MIN_INTERVAL_MS: u64 = 320;
const CLAUDE_JETBRAINS_SCROLL_REDRAW_MIN_INTERVAL_MS: u64 = 420;
const CLAUDE_CURSOR_SCROLL_REDRAW_MIN_INTERVAL_MS: u64 = 900;
const CURSOR_CLAUDE_TYPING_REDRAW_HOLD_MS: u64 = 450;
const CLAUDE_IDE_NON_SCROLL_REDRAW_MIN_INTERVAL_MS: u64 = 700;
const CLAUDE_HUD_DEBUG_ENV: &str = "VOICETERM_DEBUG_CLAUDE_HUD";

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
            TerminalFamily::Cursor | TerminalFamily::JetBrains | TerminalFamily::Other => {
                self.banner_height > 1
            }
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
    now: Instant,
    last_preclear_at: Instant,
) -> bool {
    if !may_scroll_rows || preclear_height(display) == 0 {
        return false;
    }
    match family {
        // Keep JetBrains pre-clear for transition-sensitive paths only.
        // Continuous pre-clear during streaming output can visibly flash.
        TerminalFamily::JetBrains => {
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
                let cursor_claude =
                    self.terminal_family == TerminalFamily::Cursor && claude_backend;
                let claude_hud_debug = claude_hud_debug_enabled() && cursor_claude;
                let claude_non_scroll_redraw_profile = claude_jetbrains || cursor_claude;
                let scroll_redraw_min_interval =
                    if self.terminal_family == TerminalFamily::JetBrains {
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
                    } else if cursor_claude {
                        Some(Duration::from_millis(
                            CLAUDE_CURSOR_SCROLL_REDRAW_MIN_INTERVAL_MS,
                        ))
                    } else {
                        None
                    };
                let flash_sensitive_scroll_profile =
                    codex_jetbrains || claude_jetbrains || cursor_claude;
                let may_scroll_rows = pty_output_may_scroll_rows(
                    self.cols as usize,
                    &mut self.pty_line_col_estimate,
                    &bytes,
                    // JetBrains Codex frequently uses CR-driven progress/status
                    // updates. Treat CR bursts as scroll-like so periodic HUD
                    // redraw still happens without requiring user input.
                    codex_jetbrains,
                );
                let now = Instant::now();
                let cursor_claude_startup_preclear =
                    cursor_claude && self.cursor_startup_scroll_preclear_pending;
                // Cursor + Claude needs banner pre-clear whenever output can
                // scroll rows (explicit newline or terminal-width wrapping);
                // otherwise HUD chrome can leak into transcript history.
                let cursor_claude_banner_preclear =
                    cursor_claude && self.display.overlay_panel.is_none();
                let should_preclear = should_preclear_bottom_rows(
                    self.terminal_family,
                    may_scroll_rows,
                    &self.display,
                    self.pending.clear_status,
                    codex_jetbrains,
                    cursor_claude_startup_preclear,
                    cursor_claude_banner_preclear,
                    now,
                    self.last_preclear_at,
                );
                let pre_clear = if should_preclear {
                    build_clear_bottom_rows_bytes(self.rows, preclear_height(&self.display))
                } else {
                    Vec::new()
                };
                let pre_cleared = !pre_clear.is_empty();
                if claude_hud_debug {
                    log_debug(&format!(
                        "[claude-hud-debug] writer pty chunk (bytes={}, may_scroll={}, preclear={}, force_full_before={}, force_after_preclear_before={}, pending_clear_status={}, pending_clear_overlay={}): \"{}\"",
                        bytes.len(),
                        may_scroll_rows,
                        pre_cleared,
                        self.display.force_full_banner_redraw,
                        self.force_redraw_after_preclear,
                        self.pending.clear_status,
                        self.pending.clear_overlay,
                        debug_bytes_preview(&bytes, 120)
                    ));
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
                    }
                }
                self.last_output_at = now;
                if self.display.has_any() {
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
                    let non_scroll_line_mutation = should_force_non_scroll_banner_redraw(
                        claude_non_scroll_redraw_profile,
                        may_scroll_rows,
                        self.display.enhanced_status.is_some(),
                        &bytes,
                        now,
                        self.last_scroll_redraw_at,
                    );
                    if non_scroll_line_mutation {
                        self.display.force_full_banner_redraw = true;
                        self.last_scroll_redraw_at = now;
                    }
                    // Cursor+Claude: Claude Code redraws its own status hints on
                    // every keystroke echo, actively clearing the bottom rows where
                    // the HUD lives.  The 700ms non-scroll throttle above is too
                    // slow; force an immediate full HUD repaint whenever cursor-
                    // mutating CSI is detected so the HUD doesn't stay erased.
                    if cursor_claude
                        && !may_scroll_rows
                        && self.display.enhanced_status.is_some()
                        && pty_output_can_mutate_cursor_line(&bytes)
                    {
                        self.display.force_full_banner_redraw = true;
                        self.force_redraw_after_preclear = true;
                    }
                    let destructive_clear_repaint = cursor_claude
                        && self
                            .display
                            .enhanced_status
                            .as_ref()
                            .is_some_and(|status| !status.claude_prompt_suppressed)
                        && pty_output_contains_destructive_clear(&bytes);
                    if destructive_clear_repaint {
                        // Cursor+Claude frequently emits full-screen clear sequences
                        // while streaming output. Repaint HUD immediately so it does
                        // not stay wiped until typing-hold debounce elapses.
                        self.display.force_full_banner_redraw = true;
                        self.force_redraw_after_preclear = true;
                        self.last_scroll_redraw_at = now;
                        if claude_hud_debug {
                            log_debug(
                                "[claude-hud-debug] forcing immediate redraw after destructive clear sequence",
                            );
                        }
                    }
                    if pre_cleared
                        && self.terminal_family == TerminalFamily::JetBrains
                        && !codex_jetbrains
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
                    let output_redraw_needed = self.display.force_full_banner_redraw
                        || pre_cleared
                        || non_scroll_line_mutation
                        || destructive_clear_repaint
                        || (may_scroll_rows && !flash_sensitive_scroll_profile);
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
                if self.display.has_any() || self.pending.has_any() {
                    self.needs_redraw = true;
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
                if self.terminal_family == TerminalFamily::Cursor
                    && is_claude_backend()
                    && self.display.overlay_panel.is_none()
                    && (self.display.enhanced_status.is_some()
                        || self.pending.enhanced_status.is_some())
                {
                    // Cursor+Claude can clear bottom HUD rows during typing
                    // bursts without emitting a scroll/CSI pattern we can
                    // classify. Schedule one low-rate repair redraw shortly
                    // after typing settles.
                    let repair_due = now + Duration::from_millis(140);
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
        let claude_cursor_debug = claude_hud_debug_enabled()
            && self.terminal_family == TerminalFamily::Cursor
            && is_claude_backend();
        if !self.needs_redraw {
            if let Some(due) = self.cursor_claude_input_repair_due {
                if self.terminal_family == TerminalFamily::Cursor
                    && is_claude_backend()
                    && self.display.overlay_panel.is_none()
                    && (self.display.enhanced_status.is_some()
                        || self.pending.enhanced_status.is_some())
                    && Instant::now() >= due
                {
                    self.display.force_full_banner_redraw = true;
                    self.force_redraw_after_preclear = true;
                    self.needs_redraw = true;
                    self.cursor_claude_input_repair_due = None;
                    if claude_cursor_debug {
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
        let now = Instant::now();
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
        let idle_ms = if priority_update_pending {
            PRIORITY_STATUS_IDLE_MS
        } else {
            STATUS_IDLE_MS
        };
        let max_wait_ms = if priority_update_pending {
            PRIORITY_STATUS_MAX_WAIT_MS
        } else {
            STATUS_MAX_WAIT_MS
        };

        if !self.force_redraw_after_preclear
            && !suppression_transition_pending
            && since_output < Duration::from_millis(idle_ms)
            && since_draw < Duration::from_millis(max_wait_ms)
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
                if self.rows != r || self.cols != c {
                    self.rows = r;
                    self.cols = c;
                    self.pty_line_col_estimate = 0;
                }
            }
        }
        if self.rows == 0 || self.cols == 0 {
            if let Ok((c, r)) = read_terminal_size() {
                self.rows = r;
                self.cols = c;
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
                let banner = format_status_banner(state, theme, cols as usize);
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
                let use_previous_lines = should_use_previous_banner_lines(
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
                let _ = write_status_banner(stdout, &banner, rows, previous_lines);
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
mod tests {
    use super::*;
    use crate::HudStyle;
    use std::env;
    use std::sync::{Mutex, OnceLock};

    fn with_backend_label_env<T>(backend_label: Option<&str>, f: impl FnOnce() -> T) -> T {
        static ENV_LOCK: OnceLock<Mutex<()>> = OnceLock::new();
        let lock = ENV_LOCK.get_or_init(|| Mutex::new(()));
        let _guard = lock.lock().expect("env lock poisoned");

        let prev = env::var("VOICETERM_BACKEND_LABEL").ok();
        match backend_label {
            Some(label) => env::set_var("VOICETERM_BACKEND_LABEL", label),
            None => env::remove_var("VOICETERM_BACKEND_LABEL"),
        }

        let out = f();

        match prev {
            Some(value) => env::set_var("VOICETERM_BACKEND_LABEL", value),
            None => env::remove_var("VOICETERM_BACKEND_LABEL"),
        }
        out
    }

    #[test]
    fn resize_ignores_unchanged_dimensions() {
        let mut state = WriterState::new();
        state.rows = 40;
        state.cols = 120;

        assert!(state.handle_message(WriterMessage::Resize {
            rows: 40,
            cols: 120
        }));
        assert_eq!(state.rows, 40);
        assert_eq!(state.cols, 120);
        assert!(!state.needs_redraw);
    }

    #[test]
    fn resize_updates_dimensions_when_changed() {
        let mut state = WriterState::new();
        state.rows = 24;
        state.cols = 80;
        state.pty_line_col_estimate = 12;

        assert!(state.handle_message(WriterMessage::Resize {
            rows: 30,
            cols: 100
        }));
        assert_eq!(state.rows, 30);
        assert_eq!(state.cols, 100);
        assert_eq!(state.pty_line_col_estimate, 0);
    }

    #[test]
    fn status_clear_height_only_when_banner_shrinks() {
        assert_eq!(status_clear_height_for_redraw(4, 4), 0);
        assert_eq!(status_clear_height_for_redraw(3, 5), 0);
        assert_eq!(status_clear_height_for_redraw(5, 3), 5);
    }

    #[test]
    fn should_preclear_bottom_rows_jetbrains_skips_banner_preclear_without_transition() {
        let display = DisplayState {
            banner_height: 4,
            preclear_banner_height: 4,
            ..DisplayState::default()
        };
        let now = Instant::now();
        assert!(!should_preclear_bottom_rows(
            TerminalFamily::JetBrains,
            true,
            &display,
            false,
            false,
            false,
            false,
            now,
            now - Duration::from_millis(JETBRAINS_PRECLEAR_COOLDOWN_MS)
        ));
    }

    #[test]
    fn should_preclear_bottom_rows_jetbrains_preclears_on_pending_status_transition() {
        let display = DisplayState {
            banner_height: 4,
            preclear_banner_height: 4,
            ..DisplayState::default()
        };
        let now = Instant::now();
        assert!(should_preclear_bottom_rows(
            TerminalFamily::JetBrains,
            true,
            &display,
            true,
            false,
            false,
            false,
            now,
            now - Duration::from_millis(JETBRAINS_PRECLEAR_COOLDOWN_MS)
        ));
    }

    #[test]
    fn should_preclear_bottom_rows_jetbrains_codex_skips_preclear_even_on_transition() {
        let display = DisplayState {
            banner_height: 4,
            preclear_banner_height: 4,
            ..DisplayState::default()
        };
        assert!(!should_preclear_bottom_rows(
            TerminalFamily::JetBrains,
            true,
            &display,
            true,
            true,
            false,
            false,
            Instant::now(),
            Instant::now() - Duration::from_millis(JETBRAINS_PRECLEAR_COOLDOWN_MS)
        ));
    }

    #[test]
    fn should_preclear_bottom_rows_jetbrains_respects_cooldown() {
        let display = DisplayState {
            banner_height: 4,
            preclear_banner_height: 4,
            ..DisplayState::default()
        };
        let now = Instant::now();
        assert!(!should_preclear_bottom_rows(
            TerminalFamily::JetBrains,
            true,
            &display,
            true,
            false,
            false,
            false,
            now,
            now
        ));
    }

    #[test]
    fn should_preclear_bottom_rows_cursor_respects_cooldown() {
        let display = DisplayState {
            overlay_panel: Some(OverlayPanel {
                content: "panel".to_string(),
                height: 4,
            }),
            ..DisplayState::default()
        };
        let now = Instant::now();
        assert!(!should_preclear_bottom_rows(
            TerminalFamily::Cursor,
            true,
            &display,
            false,
            false,
            false,
            false,
            now,
            now
        ));
        assert!(should_preclear_bottom_rows(
            TerminalFamily::Cursor,
            true,
            &display,
            false,
            false,
            false,
            false,
            now,
            now - Duration::from_millis(CURSOR_PRECLEAR_COOLDOWN_MS)
        ));
    }

    #[test]
    fn should_preclear_bottom_rows_cursor_skips_banner_only_preclear() {
        let display = DisplayState {
            banner_height: 4,
            preclear_banner_height: 4,
            ..DisplayState::default()
        };
        let now = Instant::now();
        assert!(!should_preclear_bottom_rows(
            TerminalFamily::Cursor,
            true,
            &display,
            false,
            false,
            false,
            false,
            now,
            now - Duration::from_millis(CURSOR_PRECLEAR_COOLDOWN_MS)
        ));
    }

    #[test]
    fn should_preclear_bottom_rows_cursor_claude_skips_banner_only_preclear() {
        let display = DisplayState {
            enhanced_status: Some(StatusLineState::new()),
            banner_height: 4,
            preclear_banner_height: 4,
            ..DisplayState::default()
        };
        let now = Instant::now();
        assert!(!should_preclear_bottom_rows(
            TerminalFamily::Cursor,
            true,
            &display,
            false,
            false,
            false,
            false,
            now,
            now - Duration::from_millis(CURSOR_PRECLEAR_COOLDOWN_MS)
        ));
    }

    #[test]
    fn should_preclear_bottom_rows_cursor_claude_preclears_once_for_startup_scroll() {
        let display = DisplayState {
            enhanced_status: Some(StatusLineState::new()),
            banner_height: 4,
            preclear_banner_height: 4,
            ..DisplayState::default()
        };
        let now = Instant::now();
        assert!(should_preclear_bottom_rows(
            TerminalFamily::Cursor,
            true,
            &display,
            false,
            false,
            true,
            false,
            now,
            now - Duration::from_millis(CURSOR_PRECLEAR_COOLDOWN_MS)
        ));
    }

    #[test]
    fn should_preclear_bottom_rows_cursor_claude_preclears_banner_without_cadence_gate() {
        let mut status = StatusLineState::new();
        status.claude_prompt_suppressed = false;
        let display = DisplayState {
            enhanced_status: Some(status),
            banner_height: 4,
            preclear_banner_height: 4,
            ..DisplayState::default()
        };
        let now = Instant::now();
        assert!(should_preclear_bottom_rows(
            TerminalFamily::Cursor,
            true,
            &display,
            false,
            false,
            false,
            true,
            now,
            now
        ));
    }

    #[test]
    fn enhanced_status_does_not_cancel_pending_clear_status() {
        let mut state = WriterState::new();
        state.rows = 24;
        state.cols = 120;
        state.pending.clear_status = true;
        state.last_output_at = Instant::now();
        state.last_status_draw_at = Instant::now();

        // EnhancedStatus should preserve an already-pending clear transition.
        assert!(state.pending.clear_status);

        let mut suppressed = StatusLineState::new();
        suppressed.claude_prompt_suppressed = true;
        assert!(state.handle_message(WriterMessage::EnhancedStatus(suppressed)));
        assert!(
            state.pending.clear_status,
            "suppression transitions must preserve pending clear until it is applied"
        );
    }

    #[test]
    fn should_preclear_bottom_rows_cursor_preclears_for_pending_status_clear() {
        let display = DisplayState {
            banner_height: 4,
            preclear_banner_height: 4,
            ..DisplayState::default()
        };
        let now = Instant::now();
        assert!(should_preclear_bottom_rows(
            TerminalFamily::Cursor,
            true,
            &display,
            true,
            false,
            false,
            false,
            now,
            now - Duration::from_millis(CURSOR_PRECLEAR_COOLDOWN_MS)
        ));
    }

    #[test]
    fn should_preclear_bottom_rows_other_terminal_uses_legacy_behavior() {
        let display = DisplayState {
            banner_height: 4,
            preclear_banner_height: 4,
            ..DisplayState::default()
        };
        assert!(should_preclear_bottom_rows(
            TerminalFamily::Other,
            true,
            &display,
            false,
            false,
            false,
            false,
            Instant::now(),
            Instant::now()
        ));
    }

    #[test]
    fn should_force_scroll_full_redraw_without_interval_always_true() {
        let now = Instant::now();
        assert!(should_force_scroll_full_redraw(None, now, now));
    }

    #[test]
    fn should_force_scroll_full_redraw_respects_interval_when_configured() {
        let now = Instant::now();
        let interval = Duration::from_millis(CODEX_JETBRAINS_SCROLL_REDRAW_MIN_INTERVAL_MS);
        assert!(!should_force_scroll_full_redraw(Some(interval), now, now));
        assert!(should_force_scroll_full_redraw(
            Some(interval),
            now,
            now - Duration::from_millis(CODEX_JETBRAINS_SCROLL_REDRAW_MIN_INTERVAL_MS)
        ));
    }

    #[test]
    fn pty_output_can_mutate_cursor_line_detects_echo_like_chunks() {
        assert!(pty_output_can_mutate_cursor_line(b"\rprompt"));
        assert!(pty_output_can_mutate_cursor_line(b"\x08"));
        assert!(pty_output_can_mutate_cursor_line(b"\x1b[2K"));
        assert!(!pty_output_can_mutate_cursor_line(b"\n"));
        assert!(!pty_output_can_mutate_cursor_line(b"\x1b[32mok\x1b[0m"));
    }

    #[test]
    fn should_force_non_scroll_banner_redraw_requires_claude_flash_profile_and_interval() {
        let now = Instant::now();
        let interval = Duration::from_millis(CLAUDE_IDE_NON_SCROLL_REDRAW_MIN_INTERVAL_MS);
        assert!(!should_force_non_scroll_banner_redraw(
            false,
            false,
            true,
            b"a",
            now,
            now - interval
        ));
        assert!(!should_force_non_scroll_banner_redraw(
            true,
            false,
            true,
            b"\n",
            now,
            now - interval
        ));
        assert!(!should_force_non_scroll_banner_redraw(
            true, false, true, b"a", now, now
        ));
        assert!(should_force_non_scroll_banner_redraw(
            true,
            false,
            true,
            b"\r",
            now,
            now - interval
        ));
    }

    #[test]
    fn defer_non_urgent_redraw_for_recent_input_applies_to_all_terminals() {
        let now = Instant::now();
        // Cursor uses the longer hold window
        assert!(should_defer_non_urgent_redraw_for_recent_input(
            TerminalFamily::Cursor,
            true,
            now,
            now - Duration::from_millis(CURSOR_CLAUDE_TYPING_REDRAW_HOLD_MS / 2)
        ));
        // Non-Claude Cursor still defers
        assert!(should_defer_non_urgent_redraw_for_recent_input(
            TerminalFamily::Cursor,
            false,
            now,
            now - Duration::from_millis(CURSOR_CLAUDE_TYPING_REDRAW_HOLD_MS / 2)
        ));
        // JetBrains defers with the shorter hold window
        assert!(should_defer_non_urgent_redraw_for_recent_input(
            TerminalFamily::JetBrains,
            true,
            now,
            now - Duration::from_millis(TYPING_REDRAW_HOLD_MS / 2)
        ));
        // Other terminals defer too
        assert!(should_defer_non_urgent_redraw_for_recent_input(
            TerminalFamily::Other,
            false,
            now,
            now - Duration::from_millis(TYPING_REDRAW_HOLD_MS / 2)
        ));
        // Cursor expires after its hold window
        assert!(!should_defer_non_urgent_redraw_for_recent_input(
            TerminalFamily::Cursor,
            true,
            now,
            now - Duration::from_millis(CURSOR_CLAUDE_TYPING_REDRAW_HOLD_MS + 10)
        ));
        // Other expires after the shorter hold window
        assert!(!should_defer_non_urgent_redraw_for_recent_input(
            TerminalFamily::Other,
            true,
            now,
            now - Duration::from_millis(TYPING_REDRAW_HOLD_MS + 10)
        ));
    }

    #[test]
    fn maybe_redraw_status_defers_non_urgent_redraw_while_user_typing_in_cursor_claude() {
        with_backend_label_env(Some("claude"), || {
            let mut state = WriterState::new();
            state.terminal_family = TerminalFamily::Cursor;
            state.rows = 24;
            state.cols = 120;
            state.display.enhanced_status = Some(StatusLineState::new());
            state.needs_redraw = true;
            state.last_output_at = Instant::now() - Duration::from_millis(320);
            state.last_status_draw_at = Instant::now() - Duration::from_millis(80);
            assert!(state.handle_message(WriterMessage::UserInputActivity));

            state.maybe_redraw_status();
            assert!(
                state.needs_redraw,
                "recent typing should defer non-urgent redraw in cursor+claude"
            );
        });
    }

    #[test]
    fn maybe_redraw_status_does_not_defer_minimal_hud_recovery_in_cursor_claude() {
        with_backend_label_env(Some("claude"), || {
            let mut state = WriterState::new();
            state.terminal_family = TerminalFamily::Cursor;
            state.rows = 24;
            state.cols = 120;
            state.display.enhanced_status = Some(StatusLineState::new());
            state.display.banner_height = 1;
            state.needs_redraw = true;
            state.last_output_at = Instant::now() - Duration::from_millis(320);
            state.last_status_draw_at = Instant::now() - Duration::from_millis(80);
            assert!(state.handle_message(WriterMessage::UserInputActivity));

            state.maybe_redraw_status();
            assert!(
                !state.needs_redraw,
                "minimal HUD in cursor+claude should be redrawn even during typing hold"
            );
        });
    }

    #[test]
    fn maybe_redraw_status_defers_non_urgent_redraw_while_user_typing_on_standard_terminal() {
        with_backend_label_env(None, || {
            let mut state = WriterState::new();
            state.terminal_family = TerminalFamily::Other;
            state.rows = 24;
            state.cols = 120;
            state.display.enhanced_status = Some(StatusLineState::new());
            state.needs_redraw = true;
            state.last_output_at = Instant::now() - Duration::from_millis(320);
            state.last_status_draw_at = Instant::now() - Duration::from_millis(80);
            assert!(state.handle_message(WriterMessage::UserInputActivity));

            state.maybe_redraw_status();
            assert!(
                state.needs_redraw,
                "recent typing should defer non-urgent redraw on standard terminals"
            );
        });
    }

    #[test]
    fn user_input_activity_schedules_cursor_claude_repair_redraw() {
        with_backend_label_env(Some("claude"), || {
            let mut state = WriterState::new();
            state.terminal_family = TerminalFamily::Cursor;
            state.rows = 24;
            state.cols = 120;
            state.display.enhanced_status = Some(StatusLineState::new());
            assert!(state.handle_message(WriterMessage::UserInputActivity));
            assert!(
                state.cursor_claude_input_repair_due.is_some(),
                "cursor+claude user input should schedule repair redraw deadline"
            );
        });
    }

    #[test]
    fn user_input_activity_schedules_repair_when_status_is_pending() {
        with_backend_label_env(Some("claude"), || {
            let mut state = WriterState::new();
            state.terminal_family = TerminalFamily::Cursor;
            state.rows = 24;
            state.cols = 120;
            state.pending.enhanced_status = Some(StatusLineState::new());
            assert!(state.handle_message(WriterMessage::UserInputActivity));
            assert!(
                state.cursor_claude_input_repair_due.is_some(),
                "pending enhanced status should still schedule a repair redraw window"
            );
        });
    }

    #[test]
    fn scheduled_cursor_claude_repair_redraw_fires_without_pending_status_update() {
        with_backend_label_env(Some("claude"), || {
            let mut state = WriterState::new();
            state.terminal_family = TerminalFamily::Cursor;
            state.rows = 24;
            state.cols = 120;
            state.display.enhanced_status = Some(StatusLineState::new());
            state.cursor_claude_input_repair_due = Some(Instant::now() - Duration::from_millis(1));
            state.needs_redraw = false;
            state.maybe_redraw_status();
            assert!(
                state.cursor_claude_input_repair_due.is_none(),
                "repair redraw deadline should be consumed after redraw"
            );
            assert!(!state.needs_redraw);
        });
    }

    #[test]
    fn unrelated_redraw_keeps_future_cursor_claude_repair_deadline() {
        with_backend_label_env(Some("claude"), || {
            let mut state = WriterState::new();
            state.terminal_family = TerminalFamily::Cursor;
            state.rows = 24;
            state.cols = 120;
            state.display.enhanced_status = Some(StatusLineState::new());
            state.display.status = Some("ready".to_string());
            state.needs_redraw = true;
            state.force_redraw_after_preclear = true;
            state.cursor_claude_input_repair_due =
                Some(Instant::now() + Duration::from_millis(250));
            state.maybe_redraw_status();
            assert!(
                state.cursor_claude_input_repair_due.is_some(),
                "future repair deadline should survive unrelated redraws"
            );
        });
    }

    #[test]
    fn maybe_redraw_status_throttles_when_no_priority_or_preclear_force() {
        let mut state = WriterState::new();
        state.rows = 24;
        state.cols = 120;
        state.display.status = Some("Processing...".to_string());
        state.needs_redraw = true;
        state.last_output_at = Instant::now();
        state.last_status_draw_at = Instant::now();

        state.maybe_redraw_status();
        assert!(state.needs_redraw);
    }

    #[test]
    fn maybe_redraw_status_skips_throttle_when_preclear_force_is_set() {
        let mut state = WriterState::new();
        state.rows = 24;
        state.cols = 120;
        state.display.status = Some("Processing...".to_string());
        state.needs_redraw = true;
        state.force_redraw_after_preclear = true;
        state.last_output_at = Instant::now();
        state.last_status_draw_at = Instant::now();

        state.maybe_redraw_status();
        assert!(!state.needs_redraw);
        assert!(!state.force_redraw_after_preclear);
    }

    fn hook_terminal_size_error() -> io::Result<(u16, u16)> {
        Err(io::Error::other("terminal unavailable"))
    }

    fn hook_terminal_size_zero() -> io::Result<(u16, u16)> {
        Ok((0, 0))
    }

    #[test]
    fn maybe_redraw_status_falls_back_when_terminal_size_call_fails() {
        struct HookGuard;
        impl Drop for HookGuard {
            fn drop(&mut self) {
                set_terminal_size_hook(None);
            }
        }

        set_terminal_size_hook(Some(hook_terminal_size_error));
        let _guard = HookGuard;

        let mut state = WriterState::new();
        state.rows = 0;
        state.cols = 0;
        state.pending.enhanced_status = Some(StatusLineState::new());
        state.needs_redraw = true;
        state.force_redraw_after_preclear = true;

        state.maybe_redraw_status();

        assert!(state.rows > 0);
        assert!(state.cols > 0);
        assert!(!state.needs_redraw);
        assert!(state.pending.enhanced_status.is_none());
        assert!(state.display.enhanced_status.is_some());
    }

    #[test]
    fn maybe_redraw_status_falls_back_when_terminal_reports_zero_size() {
        struct HookGuard;
        impl Drop for HookGuard {
            fn drop(&mut self) {
                set_terminal_size_hook(None);
            }
        }

        set_terminal_size_hook(Some(hook_terminal_size_zero));
        let _guard = HookGuard;

        let mut state = WriterState::new();
        state.rows = 0;
        state.cols = 0;
        state.pending.enhanced_status = Some(StatusLineState::new());
        state.needs_redraw = true;
        state.force_redraw_after_preclear = true;

        state.maybe_redraw_status();

        assert!(state.rows > 0);
        assert!(state.cols > 0);
        assert!(!state.needs_redraw);
        assert!(state.display.enhanced_status.is_some());
    }

    #[test]
    fn pty_output_may_scroll_rows_tracks_wrapping_without_newline() {
        let mut col = 0usize;
        assert!(!pty_output_may_scroll_rows(10, &mut col, b"hello", false));
        assert_eq!(col, 5);

        // Crosses terminal width boundary without an explicit newline byte.
        assert!(pty_output_may_scroll_rows(10, &mut col, b" world", false));
        assert_eq!(col, 1);
    }

    #[test]
    fn pty_output_may_scroll_rows_flags_newline_and_resets_column() {
        let mut col = 7usize;
        assert!(pty_output_may_scroll_rows(80, &mut col, b"\nnext", false));
        assert_eq!(col, 4);
    }

    #[test]
    fn pty_output_may_scroll_rows_treats_carriage_return_as_same_row_rewind() {
        let mut col = 12usize;
        assert!(!pty_output_may_scroll_rows(
            80,
            &mut col,
            b"\rprompt",
            false
        ));
        assert_eq!(col, 6);
    }

    #[test]
    fn pty_output_may_scroll_rows_can_treat_carriage_return_as_scroll_for_codex_jetbrains() {
        let mut col = 12usize;
        assert!(pty_output_may_scroll_rows(80, &mut col, b"\rprompt", true));
        assert_eq!(col, 6);
    }

    #[test]
    fn non_scrolling_output_does_not_force_full_banner_redraw() {
        let mut state = WriterState::new();
        state.terminal_family = TerminalFamily::Other;
        state.rows = 24;
        state.cols = 120;
        state.display.enhanced_status = Some(StatusLineState::new());
        state.display.banner_height = 4;
        state.display.force_full_banner_redraw = false;

        assert!(state.handle_message(WriterMessage::PtyOutput(vec![b'a'])));
        assert!(!state.display.force_full_banner_redraw);
        assert!(
            !state.needs_redraw,
            "non-scrolling single-line echo should not trigger HUD redraw flicker"
        );
    }

    #[test]
    fn scrolling_output_forces_full_banner_redraw_for_multi_row_hud() {
        let mut state = WriterState::new();
        state.terminal_family = TerminalFamily::Other;
        state.rows = 24;
        state.cols = 120;
        state.display.enhanced_status = Some(StatusLineState::new());
        state.display.banner_height = 4;
        state.display.force_full_banner_redraw = false;

        assert!(state.handle_message(WriterMessage::PtyOutput(vec![b'\n'])));
        assert!(state.display.force_full_banner_redraw);
    }

    #[test]
    fn scrolling_output_forces_full_banner_redraw_for_single_row_hud() {
        let mut state = WriterState::new();
        state.terminal_family = TerminalFamily::Other;
        state.rows = 24;
        state.cols = 120;
        state.display.enhanced_status = Some(StatusLineState::new());
        state.display.banner_height = 1;
        state.display.force_full_banner_redraw = false;

        assert!(state.handle_message(WriterMessage::PtyOutput(vec![b'\n'])));
        assert!(!state.display.force_full_banner_redraw);
    }

    #[test]
    fn jetbrains_scroll_output_redraw_state_matches_backend_policy() {
        let mut state = WriterState::new();
        state.terminal_family = TerminalFamily::JetBrains;
        state.rows = 24;
        state.cols = 120;
        state.display.enhanced_status = Some(StatusLineState::new());
        state.display.banner_height = 4;
        state.display.force_full_banner_redraw = false;

        assert!(state.handle_message(WriterMessage::PtyOutput(vec![b'\n'])));
        if is_codex_backend() {
            assert!(state.needs_redraw);
        } else {
            // Claude/JetBrains keeps redraw pending (instead of forcing every
            // pre-clear to repaint immediately) to reduce visible flashing.
            assert!(state.needs_redraw);
            assert!(!state.force_redraw_after_preclear);
        }
    }

    #[test]
    fn cursor_scrolling_output_marks_full_banner_for_redraw() {
        with_backend_label_env(Some("codex"), || {
            let mut state = WriterState::new();
            state.terminal_family = TerminalFamily::Cursor;
            state.rows = 24;
            state.cols = 120;
            state.display.enhanced_status = Some(StatusLineState::new());
            state.display.banner_height = 4;
            state.display.force_full_banner_redraw = false;
            state.last_preclear_at =
                Instant::now() - Duration::from_millis(CURSOR_PRECLEAR_COOLDOWN_MS);

            assert!(state.handle_message(WriterMessage::PtyOutput(vec![b'\n'])));
            assert!(state.needs_redraw);
            assert!(state.display.force_full_banner_redraw);
        });
    }

    #[test]
    fn cursor_claude_banner_preclear_requests_redraw_on_scrolling_newline_output() {
        with_backend_label_env(Some("claude"), || {
            let mut state = WriterState::new();
            state.terminal_family = TerminalFamily::Cursor;
            state.rows = 24;
            state.cols = 120;
            state.display.enhanced_status = Some(StatusLineState::new());
            state.display.banner_height = 4;
            state.display.preclear_banner_height = 4;
            state.display.force_full_banner_redraw = false;
            state.cursor_startup_scroll_preclear_pending = false;
            state.last_preclear_at =
                Instant::now() - Duration::from_millis(CURSOR_CLAUDE_BANNER_PRECLEAR_COOLDOWN_MS);
            state.last_scroll_redraw_at = Instant::now();

            assert!(state.handle_message(WriterMessage::PtyOutput(vec![b'\n'])));
            assert!(
                !state.needs_redraw,
                "cursor+claude preclear should redraw in the same cycle (no pending blink frame)"
            );
        });
    }

    #[test]
    fn transition_redraw_after_preclear_disables_previous_line_diff() {
        assert!(!should_use_previous_banner_lines(false, true));
        assert!(!should_use_previous_banner_lines(true, true));
        assert!(!should_use_previous_banner_lines(true, false));
        assert!(should_use_previous_banner_lines(false, false));
    }

    #[test]
    fn pty_output_may_scroll_rows_skips_csi_escape_sequences() {
        let mut col = 0usize;
        // CSI sequence parameters should NOT count as printable characters.
        // "\x1b[31m" is SGR (3 param bytes + final 'm') — column should stay 0.
        assert!(!pty_output_may_scroll_rows(
            80,
            &mut col,
            b"\x1b[31m",
            false
        ));
        assert_eq!(col, 0, "CSI params must not inflate column estimate");
    }

    #[test]
    fn pty_output_may_scroll_rows_handles_mixed_csi_and_printable() {
        let mut col = 0usize;
        // "\x1b[32mHi" — SGR skipped, then 'H' and 'i' count as 2 printable chars.
        assert!(!pty_output_may_scroll_rows(
            80,
            &mut col,
            b"\x1b[32mHi",
            false
        ));
        assert_eq!(col, 2, "only printable bytes after CSI should count");
    }

    #[test]
    fn pty_output_may_scroll_rows_skips_two_byte_escape_sequences() {
        let mut col = 0usize;
        // ESC 7 (save cursor) + ESC 8 (restore cursor) — both should be skipped.
        assert!(!pty_output_may_scroll_rows(
            80,
            &mut col,
            b"\x1b7\x1b8ab",
            false
        ));
        assert_eq!(
            col, 2,
            "two-byte escapes should be skipped, only 'ab' counted"
        );
    }

    #[test]
    fn pty_output_may_scroll_rows_sgr_does_not_cause_false_scroll() {
        let mut col = 0usize;
        // 8-column terminal: "Hi" (2 cols) + SGR "\x1b[0;38;5;196m" + "!" (1 col) = 3 cols total.
        // Before the fix, SGR parameter bytes inflated the estimate past 8, causing false scroll.
        let payload = b"Hi\x1b[0;38;5;196m!";
        assert!(!pty_output_may_scroll_rows(8, &mut col, payload, false));
        assert_eq!(col, 3, "SGR color codes must not cause false wrap-scroll");
    }

    #[test]
    fn pty_output_contains_destructive_clear_detects_screen_clear_sequences() {
        assert!(pty_output_contains_destructive_clear(b"\x1b[2J\x1b[H"));
        assert!(pty_output_contains_destructive_clear(b"\x1b[3J"));
        assert!(pty_output_contains_destructive_clear(b"\x1bc"));
    }

    #[test]
    fn pty_output_contains_destructive_clear_ignores_non_destructive_sequences() {
        assert!(!pty_output_contains_destructive_clear(b"\x1b[0J"));
        assert!(!pty_output_contains_destructive_clear(b"\x1b[K"));
        assert!(!pty_output_contains_destructive_clear(b"plain output"));
    }

    #[test]
    fn cursor_claude_suppression_transition_bypasses_typing_hold_deferral() {
        with_backend_label_env(Some("claude"), || {
            let mut state = WriterState::new();
            state.terminal_family = TerminalFamily::Cursor;
            state.rows = 24;
            state.cols = 120;
            state.display.banner_height = 0;
            state.display.preclear_banner_height = 1;
            state.last_user_input_at = Instant::now();
            state.last_output_at = Instant::now() - Duration::from_millis(200);
            state.last_status_draw_at = Instant::now() - Duration::from_millis(200);

            let mut suppressed = StatusLineState::new();
            suppressed.hud_style = HudStyle::Minimal;
            suppressed.claude_prompt_suppressed = true;
            state.display.enhanced_status = Some(suppressed.clone());

            let mut unsuppressed = suppressed;
            unsuppressed.claude_prompt_suppressed = false;

            assert!(state.handle_message(WriterMessage::EnhancedStatus(unsuppressed)));
            assert!(
                !state.needs_redraw,
                "suppression state transitions must bypass typing-hold deferral so HUD state syncs immediately"
            );
            assert_eq!(state.display.banner_height, 1);
            assert!(state
                .display
                .enhanced_status
                .as_ref()
                .is_some_and(|status| !status.claude_prompt_suppressed));
        });
    }

    #[test]
    fn cursor_claude_post_clear_enhanced_status_bypasses_typing_hold_deferral() {
        with_backend_label_env(Some("claude"), || {
            let mut state = WriterState::new();
            state.terminal_family = TerminalFamily::Cursor;
            state.rows = 24;
            state.cols = 120;
            state.display.banner_height = 0;
            state.display.preclear_banner_height = 1;
            state.display.enhanced_status = None;
            state.last_user_input_at = Instant::now();
            state.last_output_at = Instant::now() - Duration::from_millis(200);
            state.last_status_draw_at = Instant::now() - Duration::from_millis(200);

            let mut next = StatusLineState::new();
            next.hud_style = HudStyle::Minimal;
            next.claude_prompt_suppressed = false;

            assert!(state.handle_message(WriterMessage::EnhancedStatus(next)));
            assert!(
                !state.needs_redraw,
                "EnhancedStatus posted after ClearStatus must redraw immediately in typing-hold windows"
            );
            assert_eq!(state.display.banner_height, 1);
        });
    }

    #[test]
    fn cursor_claude_non_scroll_csi_mutation_triggers_redraw() {
        with_backend_label_env(Some("claude"), || {
            let mut state = WriterState::new();
            state.terminal_family = TerminalFamily::Cursor;
            state.rows = 24;
            state.cols = 120;
            state.display.enhanced_status = Some(StatusLineState::new());
            state.display.banner_height = 4;
            state.display.preclear_banner_height = 4;
            state.display.force_full_banner_redraw = false;
            state.cursor_startup_scroll_preclear_pending = false;
            // Simulate recent user typing so the typing-hold deferral is active.
            state.last_user_input_at = Instant::now();
            state.last_scroll_redraw_at = Instant::now();

            // Non-scrolling CSI cursor mutation: "\x1b[2K" (erase line) with no newline.
            // Claude Code emits these on every keystroke echo, clearing the HUD rows.
            // The forced redraw should bypass the typing-hold deferral and actually
            // repaint the HUD in the same cycle (needs_redraw consumed = false).
            assert!(state.handle_message(WriterMessage::PtyOutput(b"\x1b[2K".to_vec())));
            assert!(
                !state.needs_redraw,
                "Cursor+Claude must repaint HUD immediately after non-scrolling CSI mutation \
                 (force_redraw_after_preclear should bypass typing-hold deferral)"
            );
        });
    }

    #[test]
    fn cursor_claude_banner_preclear_handles_wrap_scroll_without_newline() {
        with_backend_label_env(Some("claude"), || {
            let mut state = WriterState::new();
            state.terminal_family = TerminalFamily::Cursor;
            state.rows = 24;
            state.cols = 10;
            state.display.enhanced_status = Some(StatusLineState::new());
            state.display.banner_height = 4;
            state.display.preclear_banner_height = 4;
            state.display.force_full_banner_redraw = false;
            state.cursor_startup_scroll_preclear_pending = false;
            state.last_preclear_at =
                Instant::now() - Duration::from_millis(CURSOR_CLAUDE_BANNER_PRECLEAR_COOLDOWN_MS);
            state.last_scroll_redraw_at = Instant::now();

            assert!(state.handle_message(WriterMessage::PtyOutput(b"hello world".to_vec())));
            assert!(
                !state.needs_redraw,
                "wrap-driven scroll should trigger same-cycle preclear+redraw even without explicit newline"
            );
        });
    }
}
