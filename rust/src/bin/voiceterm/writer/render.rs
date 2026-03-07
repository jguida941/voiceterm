use std::io::{self, Write};

use crate::runtime_compat::{
    detect_terminal_host, should_toggle_cursor_visibility_for_redraw, TerminalHost,
};
use crate::status_line::StatusBanner;
use crate::status_style::StatusType;
use crate::theme::Theme;

use super::sanitize::{
    sanitize_status, status_text_display_width, truncate_ansi_line, truncate_status,
};
use super::state::display::OverlayPanel;

// Use combined ANSI+DEC for non-JetBrains terminals so cursor save/restore
// survives hosts that only implement one variant.
const SAVE_CURSOR_COMBINED: &[u8] = b"\x1b[s\x1b7";
const RESTORE_CURSOR_COMBINED: &[u8] = b"\x1b[u\x1b8";
// DEC-only variants for JetBrains/JediTerm.  JediTerm does NOT implement
// CSI s / CSI u (ANSI cursor save/restore) — only DEC DECSC/DECRC
// (\x1b7 / \x1b8) is supported.  Sending unsupported ANSI sequences
// before DEC can cause JediTerm to misparse the stream, leaving the
// cursor stuck in the HUD area.  Scroll regions are disabled for
// JetBrains, so DEC restore resetting scroll margins is a non-issue.
const SAVE_CURSOR_DEC: &[u8] = b"\x1b7";
const RESTORE_CURSOR_DEC: &[u8] = b"\x1b8";
const WRAP_DISABLE: &[u8] = b"\x1b[?7l";
const WRAP_ENABLE: &[u8] = b"\x1b[?7h";
const CURSOR_HIDE: &[u8] = b"\x1b[?25l";
const CURSOR_SHOW: &[u8] = b"\x1b[?25h";
const SGR_RESET: &[u8] = b"\x1b[0m";
/// Synchronized-output mode 2026: terminal buffers all writes between
/// BSU/ESU and renders them as a single atomic frame.  Terminals that
/// do not support it silently ignore the sequence.
const SYNC_BEGIN: &[u8] = b"\x1b[?2026h";
const SYNC_END: &[u8] = b"\x1b[?2026l";

pub(super) fn terminal_host() -> TerminalHost {
    detect_terminal_host()
}

fn save_cursor_sequence_for_family(family: TerminalHost) -> &'static [u8] {
    match family {
        // JetBrains/JediTerm only supports DEC DECSC (\x1b7).  CSI s is
        // not implemented and sending it can cause parse confusion.
        // Scroll regions are disabled for JetBrains, so DEC restore
        // resetting margins is a non-issue.
        TerminalHost::JetBrains => SAVE_CURSOR_DEC,
        TerminalHost::Cursor | TerminalHost::Other => SAVE_CURSOR_COMBINED,
    }
}

fn restore_cursor_sequence_for_family(family: TerminalHost) -> &'static [u8] {
    match family {
        TerminalHost::JetBrains => RESTORE_CURSOR_DEC,
        TerminalHost::Cursor | TerminalHost::Other => RESTORE_CURSOR_COMBINED,
    }
}

fn should_disable_autowrap_during_redraw() -> bool {
    false
}

fn should_hide_cursor_during_redraw_for_family(family: TerminalHost) -> bool {
    // Keep cursor visibility untouched on all families. In JetBrains, forcing
    // hide/show around HUD redraws can leave the input caret missing when a
    // restore sequence is dropped under rapid refresh.
    let _ = family;
    false
}

fn push_cursor_prefix(sequence: &mut Vec<u8>) {
    let family = terminal_host();
    if family != TerminalHost::JetBrains {
        sequence.extend_from_slice(SYNC_BEGIN);
    }
    // Hide cursor for non-Claude JetBrains backends (Codex) to prevent
    // a block-cursor artifact at the end of the last HUD row during
    // redraw.  Claude's rapid TUI refresh can drop the show-cursor
    // restore, so it is excluded.
    if should_toggle_cursor_visibility_for_redraw(family) {
        sequence.extend_from_slice(CURSOR_HIDE);
    }
    sequence.extend_from_slice(save_cursor_sequence_for_family(family));
    if family != TerminalHost::JetBrains {
        if should_disable_autowrap_during_redraw() {
            sequence.extend_from_slice(WRAP_DISABLE);
        }
        if should_hide_cursor_during_redraw_for_family(family) {
            sequence.extend_from_slice(CURSOR_HIDE);
        }
    }
}

fn push_cursor_suffix(sequence: &mut Vec<u8>) {
    let family = terminal_host();
    if family != TerminalHost::JetBrains {
        if should_disable_autowrap_during_redraw() {
            sequence.extend_from_slice(WRAP_ENABLE);
        }
        if should_hide_cursor_during_redraw_for_family(family) {
            sequence.extend_from_slice(CURSOR_SHOW);
        }
    }
    sequence.extend_from_slice(restore_cursor_sequence_for_family(family));
    if family != TerminalHost::JetBrains {
        sequence.extend_from_slice(SYNC_END);
    }
    // Show cursor after restore for non-Claude JetBrains backends.
    if should_toggle_cursor_visibility_for_redraw(family) {
        sequence.extend_from_slice(CURSOR_SHOW);
    }
}

pub(super) fn write_status_line(
    stdout: &mut dyn Write,
    text: &str,
    rows: u16,
    cols: u16,
    theme: Theme,
) -> io::Result<()> {
    if rows == 0 || cols == 0 {
        return Ok(());
    }
    let sanitized = sanitize_status(text);
    let status_type = StatusType::from_message(&sanitized);
    let display_width = status_type.prefix_display_width() + status_text_display_width(&sanitized);
    let prefix = status_type.prefix_with_theme(theme);
    let formatted = if display_width <= cols as usize {
        format!("{prefix}{sanitized}")
    } else {
        // Truncate the text portion, keeping room for the prefix
        let max_text_len = (cols as usize).saturating_sub(status_type.prefix_display_width());
        let truncated = truncate_status(&sanitized, max_text_len);
        format!("{prefix}{truncated}")
    };
    let mut sequence = Vec::new();
    push_cursor_prefix(&mut sequence);
    sequence.extend_from_slice(format!("\x1b[{rows};1H").as_bytes());
    // Start from a known attribute baseline so stale backend styles
    // (underline/inverse/etc.) cannot leak into HUD text.
    sequence.extend_from_slice(SGR_RESET);
    sequence.extend_from_slice(formatted.as_bytes());
    // Always reset attributes before clearing trailing space so prompt/input
    // text cannot inherit a stale HUD color context.
    sequence.extend_from_slice(SGR_RESET);
    // Clear only the remainder of the line to avoid clear-then-paint flicker.
    sequence.extend_from_slice(b"\x1b[K");
    push_cursor_suffix(&mut sequence);
    stdout.write_all(&sequence)
}

/// Write a multi-line status banner at the bottom of the terminal.
pub(super) fn write_status_banner(
    stdout: &mut dyn Write,
    banner: &StatusBanner,
    rows: u16,
    cols: u16,
    previous_lines: Option<&[String]>,
) -> io::Result<()> {
    if rows == 0 || cols == 0 || banner.height == 0 {
        return Ok(());
    }
    let height = banner.height.min(rows as usize);
    let start_row = rows.saturating_sub(height as u16).saturating_add(1);
    let row_max_width = banner_row_max_render_width(terminal_host(), height, cols);

    let mut sequence = Vec::new();
    let mut any_changed = false;

    for (idx, line) in banner.lines.iter().take(height).enumerate() {
        if previous_lines
            .and_then(|lines| lines.get(idx))
            .is_some_and(|prev| prev == line)
        {
            continue;
        }
        if !any_changed {
            push_cursor_prefix(&mut sequence);
            any_changed = true;
        }
        let row = start_row + idx as u16;
        sequence.extend_from_slice(format!("\x1b[{row};1H").as_bytes()); // Move to row
                                                                         // Normalize attributes per row; some terminal backends leave
                                                                         // decoration flags active across cursor movement.
        sequence.extend_from_slice(SGR_RESET);
        let rendered = truncate_ansi_line(line, row_max_width);
        sequence.extend_from_slice(rendered.as_bytes()); // Write content
                                                         // Ensure clear-to-EOL runs in default attributes so the prompt row
                                                         // never picks up dim/hidden HUD styling.
        sequence.extend_from_slice(SGR_RESET);
        sequence.extend_from_slice(b"\x1b[K"); // Clear any trailing stale content
    }

    if !any_changed {
        return Ok(());
    }

    // INVARIANT — HUD scroll region: Set scroll region to confine PTY scrolling
    // above the HUD.  This is the same technique tmux uses for its status bar
    // — the child process can only scroll within rows 1..=(rows - height),
    // keeping the HUD rows untouched by normal terminal output.  Without this,
    // Claude Code's output scrolls into the HUD area and overlaps the status
    // bar.  The paired reset lives in clear_status_banner().  DO NOT remove
    // either side without removing the other — mismatched scroll regions break
    // terminal output.
    //
    // EXCEPTION: JetBrains/JediTerm does NOT support scroll regions correctly.
    // Setting DECSTBM causes stacked/duplicated HUD frames and garbled approval
    // card text.  The PTY row reduction (startup_pty_geometry + apply_pty_winsize)
    // is sufficient for JetBrains — skip the scroll region there.
    if terminal_host() != TerminalHost::JetBrains {
        let scroll_bottom = rows.saturating_sub(height as u16);
        if scroll_bottom >= 1 {
            sequence.extend_from_slice(format!("\x1b[1;{scroll_bottom}r").as_bytes());
        }
    }

    push_cursor_suffix(&mut sequence);

    stdout.write_all(&sequence)
}

fn banner_row_max_render_width(family: TerminalHost, banner_height: usize, cols: u16) -> usize {
    let cols = cols as usize;
    if cols == 0 {
        return 0;
    }
    if family == TerminalHost::JetBrains && banner_height <= 1 {
        // JetBrains can still auto-wrap single-row HUD strips under rapid redraw.
        // Keep a one-column safety margin so status refreshes cannot scroll-stretch.
        cols.saturating_sub(1).max(1)
    } else {
        cols
    }
}

fn overlay_row_max_render_width(family: TerminalHost, cols: u16) -> usize {
    let cols = cols as usize;
    if cols == 0 {
        return 0;
    }
    if matches!(family, TerminalHost::JetBrains | TerminalHost::Cursor) {
        // IDE-integrated terminals can wrap when overlay rows land exactly on
        // the last column after a resize. Keep a one-column guard.
        cols.saturating_sub(1).max(1)
    } else {
        cols
    }
}

/// Build escape bytes that clear the bottom `height` rows of the terminal.
///
/// Used to pre-clear the HUD **before** PTY output is written.  When terminal
/// scrolling pushes old HUD content upward, blank rows scroll up instead of
/// stale frames, preventing the visible ghost-duplicate artefact.
pub(super) fn build_clear_bottom_rows_bytes(rows: u16, height: usize) -> Vec<u8> {
    if rows == 0 || height == 0 {
        return Vec::new();
    }
    let clear_height = height.min(rows as usize);
    let start_row = rows.saturating_sub(clear_height as u16).saturating_add(1);
    let mut sequence = Vec::new();
    push_cursor_prefix(&mut sequence);
    for idx in 0..clear_height {
        let row = start_row + idx as u16;
        sequence.extend_from_slice(format!("\x1b[{row};1H").as_bytes());
        sequence.extend_from_slice(SGR_RESET);
        sequence.extend_from_slice(b"\x1b[2K");
    }
    push_cursor_suffix(&mut sequence);
    sequence
}

/// Build bottom-row clear bytes without cursor save/restore.
///
/// JetBrains+Claude uses DEC save/restore (`\x1b7`/`\x1b8`) internally for its
/// own UI; using the same slot in VoiceTerm pre-clear can corrupt Claude's
/// cursor state. This variant is CUP-only and should only be used when the
/// following PTY chunk starts with an absolute cursor-positioning sequence.
pub(super) fn build_clear_bottom_rows_cup_only_bytes(rows: u16, height: usize) -> Vec<u8> {
    if rows == 0 || height == 0 {
        return Vec::new();
    }
    let clear_height = height.min(rows as usize);
    let start_row = rows.saturating_sub(clear_height as u16).saturating_add(1);
    let mut sequence = Vec::new();
    for idx in 0..clear_height {
        let row = start_row + idx as u16;
        sequence.extend_from_slice(format!("\x1b[{row};1H").as_bytes());
        sequence.extend_from_slice(SGR_RESET);
        sequence.extend_from_slice(b"\x1b[2K");
    }
    sequence
}

/// Clear a multi-line status banner.
/// Also clears extra rows above to catch ghost content from terminal scrolling.
pub(super) fn clear_status_banner(
    stdout: &mut dyn Write,
    rows: u16,
    height: usize,
) -> io::Result<()> {
    if rows == 0 || height == 0 {
        return Ok(());
    }
    // Only clear the banner rows to avoid erasing PTY content above the HUD.
    let clear_height = height.min(rows as usize);
    let start_row = rows.saturating_sub(clear_height as u16).saturating_add(1);

    let mut sequence = Vec::new();
    push_cursor_prefix(&mut sequence);

    for idx in 0..clear_height {
        let row = start_row + idx as u16;
        sequence.extend_from_slice(format!("\x1b[{row};1H").as_bytes()); // Move to row
        sequence.extend_from_slice(SGR_RESET);
        sequence.extend_from_slice(b"\x1b[2K"); // Clear line
    }

    // INVARIANT — HUD scroll region: Reset scroll region to the full terminal
    // now that the HUD is removed.  This is the paired reset for the scroll
    // region set in write_status_banner().  DO NOT remove — without this reset,
    // the terminal stays locked to a smaller scroll area after the HUD clears.
    // Skipped on JetBrains/JediTerm (see write_status_banner for rationale).
    if terminal_host() != TerminalHost::JetBrains {
        sequence.extend_from_slice(format!("\x1b[1;{rows}r").as_bytes());
    }

    push_cursor_suffix(&mut sequence);
    stdout.write_all(&sequence)
}

/// Clear a status-banner frame anchored at an explicit start row.
///
/// This is used when the writer detects that banner anchor drifted (for example
/// from stale geometry) and needs to scrub an old frame that is no longer at
/// the current terminal bottom rows.
pub(super) fn clear_status_banner_at(
    stdout: &mut dyn Write,
    start_row: u16,
    height: usize,
) -> io::Result<()> {
    if start_row == 0 || height == 0 {
        return Ok(());
    }
    let mut sequence = Vec::new();
    push_cursor_prefix(&mut sequence);
    for idx in 0..height {
        let row = start_row.saturating_add(idx as u16);
        sequence.extend_from_slice(format!("\x1b[{row};1H").as_bytes());
        sequence.extend_from_slice(SGR_RESET);
        sequence.extend_from_slice(b"\x1b[2K");
    }
    push_cursor_suffix(&mut sequence);
    stdout.write_all(&sequence)
}

pub(super) fn clear_status_line(stdout: &mut dyn Write, rows: u16, cols: u16) -> io::Result<()> {
    if rows == 0 || cols == 0 {
        return Ok(());
    }
    let mut sequence = Vec::new();
    push_cursor_prefix(&mut sequence);
    sequence.extend_from_slice(format!("\x1b[{rows};1H").as_bytes());
    sequence.extend_from_slice(SGR_RESET);
    sequence.extend_from_slice(b"\x1b[2K");
    push_cursor_suffix(&mut sequence);
    stdout.write_all(&sequence)
}

pub(super) fn write_overlay_panel(
    stdout: &mut dyn Write,
    panel: &OverlayPanel,
    rows: u16,
    cols: u16,
) -> io::Result<()> {
    if rows == 0 || cols == 0 {
        return Ok(());
    }
    let max_width = overlay_row_max_render_width(terminal_host(), cols);
    let lines: Vec<&str> = panel.content.lines().collect();
    let height = panel.height.min(lines.len()).min(rows as usize);
    let start_row = rows.saturating_sub(height as u16).saturating_add(1);
    let mut sequence = Vec::new();
    push_cursor_prefix(&mut sequence);
    for (idx, line) in lines.iter().take(height).enumerate() {
        let row = start_row + idx as u16;
        sequence.extend_from_slice(format!("\x1b[{row};1H").as_bytes());
        // Overlay rows must clear inherited styles first so Cursor does not
        // render stale underline/strike decoration across panel content.
        sequence.extend_from_slice(SGR_RESET);
        let truncated = truncate_ansi_line(line, max_width);
        sequence.extend_from_slice(truncated.as_bytes());
        sequence.extend_from_slice(SGR_RESET);
        sequence.extend_from_slice(b"\x1b[K");
    }
    push_cursor_suffix(&mut sequence);
    stdout.write_all(&sequence)
}

pub(super) fn clear_overlay_panel(
    stdout: &mut dyn Write,
    rows: u16,
    height: usize,
) -> io::Result<()> {
    if rows == 0 {
        return Ok(());
    }
    let height = height.min(rows as usize);
    let start_row = rows.saturating_sub(height as u16).saturating_add(1);
    let mut sequence = Vec::new();
    push_cursor_prefix(&mut sequence);
    for idx in 0..height {
        let row = start_row + idx as u16;
        sequence.extend_from_slice(format!("\x1b[{row};1H").as_bytes());
        sequence.extend_from_slice(SGR_RESET);
        sequence.extend_from_slice(b"\x1b[2K");
    }
    push_cursor_suffix(&mut sequence);
    stdout.write_all(&sequence)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn write_and_clear_status_line_respect_dimensions() {
        let theme = Theme::Coral;
        let mut buf = Vec::new();
        write_status_line(&mut buf, "hi", 0, 10, theme).unwrap();
        assert!(buf.is_empty());

        write_status_line(&mut buf, "hi", 2, 0, theme).unwrap();
        assert!(buf.is_empty());

        write_status_line(&mut buf, "hi", 2, 80, theme).unwrap();
        let output = String::from_utf8_lossy(&buf);
        assert!(output.contains("\u{1b}[2;1H"));
        assert!(output.contains("hi"));
        // Should contain color codes (info prefix for generic message)
        assert!(output.contains("\u{1b}[94m")); // Blue for info

        buf.clear();
        clear_status_line(&mut buf, 2, 10).unwrap();
        let output = String::from_utf8_lossy(&buf);
        assert!(output.contains("\u{1b}[2;1H"));

        buf.clear();
        clear_status_line(&mut buf, 2, 0).unwrap();
        assert!(buf.is_empty());
    }

    #[test]
    fn write_status_line_includes_colored_prefix() {
        let theme = Theme::Coral;
        let mut buf = Vec::new();
        write_status_line(&mut buf, "Listening Manual Mode", 2, 80, theme).unwrap();
        let output = String::from_utf8_lossy(&buf);
        // Recording status should have red prefix
        assert!(output.contains("\u{1b}[91m")); // Red
        let expected_recording_prefix = format!("{} REC", theme.colors().indicator_rec);
        assert!(output.contains(&expected_recording_prefix));

        buf.clear();
        write_status_line(&mut buf, "Processing...", 2, 80, theme).unwrap();
        let output = String::from_utf8_lossy(&buf);
        // Processing status should have yellow prefix
        assert!(output.contains("\u{1b}[93m")); // Yellow
        assert!(output.contains("◐"));

        buf.clear();
        write_status_line(&mut buf, "Transcript ready", 2, 80, theme).unwrap();
        let output = String::from_utf8_lossy(&buf);
        // Success status should have green prefix
        assert!(output.contains("\u{1b}[92m")); // Green
        assert!(output.contains("✓"));
    }

    #[test]
    fn write_status_line_truncation_preserves_status_type() {
        let theme = Theme::Coral;
        let mut buf = Vec::new();
        let long_msg = "Transcript ready (with extra detail)";
        // Force truncation so the status keyword would be removed from the visible text.
        write_status_line(&mut buf, long_msg, 2, 12, theme).unwrap();
        let output = String::from_utf8_lossy(&buf);
        // Success status should still have green prefix even if text is truncated.
        assert!(output.contains("\u{1b}[92m")); // Green
        assert!(output.contains("✓"));
    }

    #[test]
    fn write_status_line_truncates_unicode_by_display_width() {
        let mut buf = Vec::new();
        write_status_line(&mut buf, "界界界", 2, 5, Theme::None).unwrap();
        let output = String::from_utf8_lossy(&buf);
        assert_eq!(output.matches('界').count(), 1);
    }

    #[test]
    fn write_status_line_respects_no_color_theme() {
        let mut buf = Vec::new();
        write_status_line(&mut buf, "Processing...", 2, 80, Theme::None).unwrap();
        let output = String::from_utf8_lossy(&buf);
        // Should have the indicator but no escape codes for color
        assert!(output.contains("◐"));
        assert!(output.contains("Processing..."));
        // The only escape codes should be cursor positioning, not color
        let color_codes = output.matches("\u{1b}[9").count();
        assert_eq!(color_codes, 0, "Should not contain color codes");
    }

    #[test]
    fn cursor_terminal_uses_combined_cursor_save_restore_sequences() {
        assert_eq!(
            save_cursor_sequence_for_family(TerminalHost::Cursor),
            SAVE_CURSOR_COMBINED
        );
        assert_eq!(
            restore_cursor_sequence_for_family(TerminalHost::Cursor),
            RESTORE_CURSOR_COMBINED
        );
    }

    #[test]
    fn jetbrains_terminal_uses_dec_only_cursor_save_restore_sequences() {
        assert_eq!(
            save_cursor_sequence_for_family(TerminalHost::JetBrains),
            SAVE_CURSOR_DEC
        );
        assert_eq!(
            restore_cursor_sequence_for_family(TerminalHost::JetBrains),
            RESTORE_CURSOR_DEC
        );
    }

    #[test]
    fn cursor_hide_policy_keeps_visibility_unchanged_for_all_terminals() {
        assert!(!should_hide_cursor_during_redraw_for_family(
            TerminalHost::JetBrains
        ));
        assert!(!should_hide_cursor_during_redraw_for_family(
            TerminalHost::Cursor
        ));
        assert!(!should_hide_cursor_during_redraw_for_family(
            TerminalHost::Other
        ));
    }

    #[test]
    fn write_status_banner_full_hud_clears_trailing_content() {
        let mut buf = Vec::new();
        let banner = StatusBanner::new(vec![
            "top".to_string(),
            "main".to_string(),
            "shortcuts".to_string(),
            "bottom".to_string(),
        ]);

        write_status_banner(&mut buf, &banner, 24, 80, None).unwrap();
        let output = String::from_utf8_lossy(&buf);
        assert!(output.contains("\u{1b}[21;1H\u{1b}[0m"));
        assert!(output.contains("\u{1b}[K"));
    }

    #[test]
    fn write_status_banner_single_line_keeps_trailing_clear() {
        let mut buf = Vec::new();
        let banner = StatusBanner::new(vec!["minimal hud".to_string()]);

        write_status_banner(&mut buf, &banner, 24, 80, None).unwrap();
        let output = String::from_utf8_lossy(&buf);
        assert!(output.contains("\u{1b}[24;1H\u{1b}[0m"));
        assert!(output.contains("\u{1b}[K"));
    }

    #[test]
    fn clear_status_banner_at_clears_expected_rows() {
        let mut buf = Vec::new();
        clear_status_banner_at(&mut buf, 10, 3).unwrap();
        let output = String::from_utf8_lossy(&buf);
        assert!(output.contains("\u{1b}[10;1H\u{1b}[0m\u{1b}[2K"));
        assert!(output.contains("\u{1b}[11;1H\u{1b}[0m\u{1b}[2K"));
        assert!(output.contains("\u{1b}[12;1H\u{1b}[0m\u{1b}[2K"));
        assert!(output.contains("\u{1b}[2K"));
    }

    #[test]
    fn write_status_banner_skips_unchanged_lines_when_previous_provided() {
        let mut buf = Vec::new();
        let previous = vec![
            "top".to_string(),
            "main old".to_string(),
            "shortcuts".to_string(),
            "bottom".to_string(),
        ];
        let banner = StatusBanner::new(vec![
            "top".to_string(),
            "main new".to_string(),
            "shortcuts".to_string(),
            "bottom".to_string(),
        ]);

        write_status_banner(&mut buf, &banner, 24, 80, Some(&previous)).unwrap();
        let output = String::from_utf8_lossy(&buf);

        // Only row 22 (the main row in a 4-line banner at 24 rows) should redraw.
        assert!(output.contains("\u{1b}[22;1H"));
        assert!(!output.contains("\u{1b}[21;1H"));
        assert!(!output.contains("\u{1b}[23;1H"));
        assert!(!output.contains("\u{1b}[24;1H"));
    }

    #[test]
    fn banner_row_max_render_width_applies_jetbrains_single_row_safety_margin() {
        assert_eq!(
            banner_row_max_render_width(TerminalHost::JetBrains, 1, 80),
            79
        );
        assert_eq!(
            banner_row_max_render_width(TerminalHost::JetBrains, 4, 80),
            80
        );
        assert_eq!(banner_row_max_render_width(TerminalHost::Cursor, 1, 80), 80);
    }

    #[test]
    fn overlay_row_max_render_width_applies_ide_terminal_safety_margin() {
        assert_eq!(
            overlay_row_max_render_width(TerminalHost::JetBrains, 80),
            79
        );
        assert_eq!(overlay_row_max_render_width(TerminalHost::Cursor, 80), 79);
        assert_eq!(overlay_row_max_render_width(TerminalHost::Other, 80), 80);
    }

    #[test]
    fn cup_only_bottom_clear_avoids_cursor_save_restore_sequences() {
        let output = build_clear_bottom_rows_cup_only_bytes(24, 2);
        let rendered = String::from_utf8_lossy(&output);
        assert!(rendered.contains("\u{1b}[23;1H\u{1b}[0m\u{1b}[2K"));
        assert!(rendered.contains("\u{1b}[24;1H\u{1b}[0m\u{1b}[2K"));
        assert!(!rendered.contains("\u{1b}[s"));
        assert!(!rendered.contains("\u{1b}[u"));
        assert!(!rendered.contains("\u{1b}7"));
        assert!(!rendered.contains("\u{1b}8"));
    }

    #[test]
    fn write_overlay_panel_resets_attributes_before_content_and_clear() {
        let mut buf = Vec::new();
        let panel = OverlayPanel {
            content: "row one\nrow two".to_string(),
            height: 2,
        };

        write_overlay_panel(&mut buf, &panel, 24, 80).unwrap();
        let output = String::from_utf8_lossy(&buf);
        assert!(output.contains("\u{1b}[23;1H\u{1b}[0mrow one\u{1b}[0m\u{1b}[K"));
        assert!(output.contains("\u{1b}[24;1H\u{1b}[0mrow two\u{1b}[0m\u{1b}[K"));
    }

    #[test]
    fn clear_overlay_panel_resets_attributes_before_line_erase() {
        let mut buf = Vec::new();
        clear_overlay_panel(&mut buf, 24, 2).unwrap();
        let output = String::from_utf8_lossy(&buf);
        assert!(output.contains("\u{1b}[23;1H\u{1b}[0m\u{1b}[2K"));
        assert!(output.contains("\u{1b}[24;1H\u{1b}[0m\u{1b}[2K"));
    }
}
