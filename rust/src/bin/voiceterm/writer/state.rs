use crossterm::terminal::size as terminal_size;
use std::io::{self, Write};
use std::time::{Duration, Instant};
use voiceterm::log_debug;

use super::mouse::{disable_mouse, enable_mouse};
use super::render::{
    build_clear_bottom_rows_bytes, clear_overlay_panel, clear_status_banner, clear_status_line,
    is_jetbrains_terminal, write_overlay_panel, write_status_banner, write_status_line,
};
use super::WriterMessage;
use crate::status_line::{format_status_banner, StatusLineState};
use crate::theme::Theme;

const OUTPUT_FLUSH_INTERVAL_MS: u64 = 16;

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
    banner_lines: Vec<String>,
    force_full_banner_redraw: bool,
}

impl DisplayState {
    fn has_any(&self) -> bool {
        self.status.is_some() || self.enhanced_status.is_some() || self.overlay_panel.is_some()
    }

    fn should_force_full_banner_redraw_on_output(&self) -> bool {
        if self.overlay_panel.is_some() || self.status.is_some() {
            return true;
        }
        // Multi-row HUDs need full repaint after terminal row scrolling.
        // Single-row HUDs are more stable and should avoid full repaint flicker.
        self.banner_height > 1
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

pub(super) struct WriterState {
    stdout: io::Stdout,
    display: DisplayState,
    pending: PendingState,
    needs_redraw: bool,
    rows: u16,
    cols: u16,
    pty_line_col_estimate: usize,
    last_output_at: Instant,
    last_output_flush_at: Instant,
    last_status_draw_at: Instant,
    theme: Theme,
    mouse_enabled: bool,
}

impl WriterState {
    pub(super) fn new() -> Self {
        Self {
            stdout: io::stdout(),
            display: DisplayState::default(),
            pending: PendingState::default(),
            needs_redraw: false,
            rows: 0,
            cols: 0,
            pty_line_col_estimate: 0,
            last_output_at: Instant::now(),
            last_output_flush_at: Instant::now(),
            last_status_draw_at: Instant::now(),
            theme: Theme::default(),
            mouse_enabled: false,
        }
    }

    pub(super) fn handle_message(&mut self, message: WriterMessage) -> bool {
        match message {
            WriterMessage::PtyOutput(bytes) => {
                let may_scroll_rows = pty_output_may_scroll_rows(
                    self.cols as usize,
                    &mut self.pty_line_col_estimate,
                    &bytes,
                );
                // Pre-clear can prevent ghost rows in JetBrains terminals but causes
                // visible flash in Cursor-style terminals.
                let pre_clear = if may_scroll_rows && is_jetbrains_terminal() {
                    if let Some(panel) = self.display.overlay_panel.as_ref() {
                        build_clear_bottom_rows_bytes(self.rows, panel.height)
                    } else if self.display.banner_height > 1 {
                        build_clear_bottom_rows_bytes(self.rows, self.display.banner_height)
                    } else {
                        Vec::new()
                    }
                } else {
                    Vec::new()
                };

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
                let now = Instant::now();
                self.last_output_at = now;
                if self.display.has_any() {
                    // PTY output may scroll/overwrite the HUD rows even if banner text did not
                    // change. Gemini compact HUD reserves a stable single row, so avoid forcing
                    // full repaint there to reduce textbox flicker while output streams.
                    // Only force full repaint when output can actually scroll rows.
                    if may_scroll_rows && self.display.should_force_full_banner_redraw_on_output() {
                        self.display.force_full_banner_redraw = true;
                    }
                    self.needs_redraw = true;
                }
                if now.duration_since(self.last_output_flush_at)
                    >= Duration::from_millis(OUTPUT_FLUSH_INTERVAL_MS)
                    || bytes.contains(&b'\n')
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
            }
            WriterMessage::Status { text } => {
                self.pending.status = Some(text);
                self.pending.enhanced_status = None;
                self.pending.clear_status = false;
                self.needs_redraw = true;
                self.maybe_redraw_status();
            }
            WriterMessage::EnhancedStatus(state) => {
                self.pending.enhanced_status = Some(state);
                self.pending.status = None;
                self.pending.clear_status = false;
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
                self.pending.status = None;
                self.pending.enhanced_status = None;
                self.pending.clear_status = true;
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
                    self.display.force_full_banner_redraw = true;
                    let _ = self.stdout.flush();
                }
                self.rows = rows;
                self.cols = cols;
                self.pty_line_col_estimate = 0;
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
        if !self.needs_redraw {
            return;
        }
        let since_output = self.last_output_at.elapsed();
        let since_draw = self.last_status_draw_at.elapsed();

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

        if since_output < Duration::from_millis(idle_ms)
            && since_draw < Duration::from_millis(max_wait_ms)
        {
            return;
        }
        if self.rows == 0 || self.cols == 0 {
            if let Ok((c, r)) = terminal_size() {
                self.rows = r;
                self.cols = c;
            }
        }
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
            let rows = self.rows;
            let cols = self.cols;
            let theme = self.theme;
            let (
                stdout,
                overlay_panel,
                enhanced_status,
                status,
                current_banner_height,
                current_banner_lines,
                force_full_banner_redraw,
            ) = (
                &mut self.stdout,
                &self.display.overlay_panel,
                &self.display.enhanced_status,
                &self.display.status,
                &mut self.display.banner_height,
                &mut self.display.banner_lines,
                &mut self.display.force_full_banner_redraw,
            );
            if let Some(panel) = overlay_panel.as_ref() {
                let _ = write_overlay_panel(stdout, panel, rows);
            } else if let Some(state) = enhanced_status.as_ref() {
                let banner = format_status_banner(state, theme, cols as usize);
                // Avoid full-frame clear on every redraw; only clear when banner shrinks.
                // write_status_banner already clears each line it writes.
                let clear_height =
                    status_clear_height_for_redraw(*current_banner_height, banner.height);
                if clear_height > 0 {
                    let _ = clear_status_banner(stdout, rows, clear_height);
                }
                *current_banner_height = banner.height;
                let previous_lines = if *force_full_banner_redraw {
                    None
                } else {
                    Some(current_banner_lines.as_slice())
                };
                let _ = write_status_banner(stdout, &banner, rows, previous_lines);
                *current_banner_lines = banner.lines.clone();
                *force_full_banner_redraw = false;
            } else if let Some(text) = status.as_deref() {
                let _ = write_status_line(stdout, text, rows, cols, theme);
                current_banner_lines.clear();
                *force_full_banner_redraw = true;
            }
            stdout.flush().err()
        };
        self.needs_redraw = false;
        self.last_status_draw_at = Instant::now();
        if let Some(err) = flush_error {
            log_debug(&format!("status redraw flush failed: {err}"));
        }
    }
}

fn pty_output_may_scroll_rows(cols: usize, line_col_estimate: &mut usize, bytes: &[u8]) -> bool {
    if bytes.is_empty() {
        return false;
    }
    // Treat unknown terminal width as potentially scrolling when explicit line breaks appear.
    if cols == 0 {
        if bytes.contains(&b'\n') || bytes.contains(&b'\r') {
            *line_col_estimate = 0;
            return true;
        }
        return false;
    }

    let mut may_scroll = false;
    for &byte in bytes {
        match byte {
            b'\n' | b'\r' => {
                may_scroll = true;
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
    }
    may_scroll
}

#[cfg(test)]
mod tests {
    use super::*;

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
    fn pty_output_may_scroll_rows_tracks_wrapping_without_newline() {
        let mut col = 0usize;
        assert!(!pty_output_may_scroll_rows(10, &mut col, b"hello"));
        assert_eq!(col, 5);

        // Crosses terminal width boundary without an explicit newline byte.
        assert!(pty_output_may_scroll_rows(10, &mut col, b" world"));
        assert_eq!(col, 1);
    }

    #[test]
    fn pty_output_may_scroll_rows_flags_newline_and_resets_column() {
        let mut col = 7usize;
        assert!(pty_output_may_scroll_rows(80, &mut col, b"\nnext"));
        assert_eq!(col, 4);
    }

    #[test]
    fn non_scrolling_output_does_not_force_full_banner_redraw() {
        let mut state = WriterState::new();
        state.rows = 24;
        state.cols = 120;
        state.display.enhanced_status = Some(StatusLineState::new());
        state.display.banner_height = 4;
        state.display.force_full_banner_redraw = false;

        assert!(state.handle_message(WriterMessage::PtyOutput(vec![b'a'])));
        assert!(!state.display.force_full_banner_redraw);
    }

    #[test]
    fn scrolling_output_forces_full_banner_redraw_for_multi_row_hud() {
        let mut state = WriterState::new();
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
        state.rows = 24;
        state.cols = 120;
        state.display.enhanced_status = Some(StatusLineState::new());
        state.display.banner_height = 1;
        state.display.force_full_banner_redraw = false;

        assert!(state.handle_message(WriterMessage::PtyOutput(vec![b'\n'])));
        assert!(!state.display.force_full_banner_redraw);
    }
}
