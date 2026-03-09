//! Dev panel overlay: guarded operator cockpit with typed actions plus
//! structured control/review/handoff/memory pages.
//!
//! Submodules handle each page's rendering; shared layout helpers live here.

use unicode_width::UnicodeWidthChar;

use crate::dev_command::{ActionCatalog, DevPanelState};
use crate::overlay_frame::{display_width, truncate_display};
use crate::theme::ThemeColors;

mod actions_page;
mod cockpit_page;
mod review_surface;

use crate::dev_command::DevPanelTab;
pub use actions_page::{dev_panel_footer, format_dev_panel};

/// Return the footer string for the currently active dev panel tab.
/// Mouse close-hitbox and the renderers both use this so footer centering
/// stays exact even when the active view adds dynamic labels or scroll info.
pub(crate) fn dev_panel_active_footer(
    colors: &crate::theme::ThemeColors,
    commands: &DevPanelState,
    terminal_width: usize,
) -> String {
    match commands.active_tab() {
        DevPanelTab::Actions => dev_panel_footer(colors),
        DevPanelTab::Review => {
            review_surface::review_surface_footer(colors, commands, terminal_width)
        }
        DevPanelTab::Control | DevPanelTab::Ops | DevPanelTab::Handoff | DevPanelTab::Memory => {
            let total = cockpit_page::cockpit_content_line_count(commands, commands.active_tab());
            cockpit_page::cockpit_page_footer(colors, commands, commands.active_tab(), total)
        }
    }
}
pub use cockpit_page::{cockpit_content_line_count, cockpit_visible_rows, format_cockpit_page};
#[cfg(test)]
pub use review_surface::review_visible_rows;
pub use review_surface::{
    format_review_surface, review_content_line_count, review_scroll_visible_rows,
};

const DEV_PANEL_MIN_WIDTH: usize = 52;
const DEV_PANEL_MAX_WIDTH: usize = 92;

pub fn panel_width(width: usize) -> usize {
    width.clamp(DEV_PANEL_MIN_WIDTH, DEV_PANEL_MAX_WIDTH)
}

pub fn panel_inner_width(width: usize) -> usize {
    panel_width(width).saturating_sub(2)
}

pub fn dev_panel_height() -> usize {
    // 24 fixed chrome lines (frame/title/separators/sections/stat rows/footer/profile)
    // plus one command row per action catalog entry.
    24 + ActionCatalog::DEFAULT_LEN
}

// ---------------------------------------------------------------------------
// Shared rendering helpers used by multiple submodules
// ---------------------------------------------------------------------------

/// Render a single padded content line between the two outer frame borders.
/// Detects section headers (▸ prefix) and styles them with the info color.
fn review_content_line(colors: &ThemeColors, text: &str, inner_width: usize) -> String {
    let borders = &colors.borders;
    if text.is_empty() {
        let pad = " ".repeat(inner_width);
        return format!(
            "{}{}{}{}{}{}",
            colors.border, borders.vertical, pad, colors.border, borders.vertical, colors.reset
        );
    }

    let padded = format!(" {text}");
    let clipped = truncate_display(&padded, inner_width);
    let pad = " ".repeat(inner_width.saturating_sub(display_width(&clipped)));
    let is_header = text.starts_with('\u{25B8}');

    if is_header {
        format!(
            "{}{}{}{}{}{}{}{}",
            colors.border,
            borders.vertical,
            colors.info,
            clipped,
            pad,
            colors.border,
            borders.vertical,
            colors.reset
        )
    } else {
        format!(
            "{}{}{}{}{}{}{}{}",
            colors.border,
            borders.vertical,
            colors.reset,
            clipped,
            pad,
            colors.border,
            borders.vertical,
            colors.reset
        )
    }
}

/// Render a label-value row for the Actions page. Also used by the command
/// line renderer within the same page.
fn value_line(colors: &ThemeColors, label: &str, value: &str, width: usize) -> String {
    let borders = &colors.borders;
    let inner_width = width.saturating_sub(2);
    let label_width = 17;
    let value_width = inner_width.saturating_sub(label_width + 3);
    let prefix = format!(" {:<label_width$} ", label, label_width = label_width);
    let value = truncate_display(value, value_width);
    let value_pad = " ".repeat(value_width.saturating_sub(display_width(&value)));
    format!(
        "{}{}{}{}{}{}{}{}{}{}",
        colors.border,
        borders.vertical,
        colors.info,
        prefix,
        colors.reset,
        value,
        value_pad,
        colors.border,
        borders.vertical,
        colors.reset
    )
}

/// Word-wrap text at display-width boundaries. Handles multi-byte and
/// wide (CJK) characters correctly by using per-character width measurement.
fn wrap_text(text: &str, max_width: usize) -> Vec<String> {
    if max_width == 0 || text.is_empty() {
        return vec![text.to_string()];
    }

    let mut lines = Vec::new();
    let mut current = String::new();
    let mut current_width = 0;

    for word in text.split_whitespace() {
        let word_width = display_width(word);
        if current_width > 0 && current_width + 1 + word_width > max_width {
            lines.push(current);
            current = String::new();
            current_width = 0;
        }
        if current_width > 0 {
            current.push(' ');
            current_width += 1;
        }
        if word_width > max_width && current.is_empty() {
            // Split by display width so multi-byte/wide chars don't panic.
            let mut chunk = String::new();
            let mut chunk_width = 0;
            for ch in word.chars() {
                let ch_width = UnicodeWidthChar::width(ch).unwrap_or(0);
                if chunk_width + ch_width > max_width && !chunk.is_empty() {
                    lines.push(chunk);
                    chunk = String::new();
                    chunk_width = 0;
                }
                chunk.push(ch);
                chunk_width += ch_width;
            }
            current = chunk;
            current_width = chunk_width;
        } else {
            current.push_str(word);
            current_width += word_width;
        }
    }
    if !current.is_empty() {
        lines.push(current);
    }
    if lines.is_empty() {
        lines.push(String::new());
    }
    lines
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::theme::Theme;

    #[test]
    fn wrap_text_splits_long_lines() {
        let text = "This is a fairly long line that should be wrapped at the boundary";
        let wrapped = wrap_text(text, 20);
        assert!(wrapped.len() > 1);
        for line in &wrapped {
            assert!(display_width(line) <= 20);
        }
    }

    #[test]
    fn wrap_text_handles_multibyte_chars_without_panic() {
        // CJK characters are 2 display columns each; emoji varies.
        // This must not panic on multi-byte boundaries.
        let text = "你好世界这是测试";
        let wrapped = wrap_text(text, 6);
        assert!(wrapped.len() > 1, "CJK text should wrap");
        for line in &wrapped {
            assert!(display_width(line) <= 6, "line too wide: {line}");
        }
    }

    #[test]
    fn wrap_text_empty_input_returns_single_empty() {
        assert_eq!(wrap_text("", 20), vec![""]);
    }

    #[test]
    fn wrap_text_zero_width_returns_original() {
        assert_eq!(wrap_text("hello world", 0), vec!["hello world"]);
    }

    #[test]
    fn wrap_text_single_long_word_splits_by_char() {
        let wrapped = wrap_text("abcdefghij", 5);
        assert_eq!(wrapped, vec!["abcde", "fghij"]);
    }

    #[test]
    fn wrap_text_whitespace_only_returns_empty() {
        assert_eq!(wrap_text("   ", 10), vec![""]);
    }

    #[test]
    fn dev_panel_active_footer_tracks_review_view_mode() {
        let mut commands = DevPanelState::default();
        commands.set_tab(DevPanelTab::Review);
        commands
            .review_mut()
            .load_from_content("# Code Audit\n\n## Current Verdict\n\n- ok\n");
        commands.review_mut().toggle_view_mode();

        let footer = dev_panel_active_footer(&Theme::Coral.colors(), &commands, 96);
        assert!(
            footer.contains("r raw"),
            "footer reflects the raw review view"
        );
    }

    #[test]
    fn dev_panel_active_footer_tracks_cockpit_scroll_position() {
        let mut commands = DevPanelState::default();
        commands.set_tab(DevPanelTab::Control);
        commands.set_memory_snapshot(crate::dev_command::MemoryStatusSnapshot {
            mode_label: "Assist".to_string(),
            capture_allowed: true,
            retrieval_allowed: true,
            events_ingested: 42,
            events_rejected: 1,
            index_size: 41,
            session_id: "footer-scroll".to_string(),
        });
        commands.set_git_snapshot(crate::dev_command::GitStatusSnapshot {
            branch: "develop".to_string(),
            dirty_count: 6,
            untracked_count: 3,
            ahead: 2,
            behind: 0,
            last_commit: "abc1234 footer scroll test".to_string(),
            changed_files: vec![
                " M rust/src/bin/voiceterm/dev_panel/mod.rs".to_string(),
                " M rust/src/bin/voiceterm/dev_panel/cockpit_page/mod.rs".to_string(),
                "?? notes/footer.txt".to_string(),
            ],
            recent_commits: vec![
                "abc1234 footer scroll test".to_string(),
                "def5678 previous".to_string(),
            ],
            diff_stat: "4 files changed, 80 insertions(+), 12 deletions(-)".to_string(),
            has_error: false,
            error_message: String::new(),
        });
        commands.review_mut().load_from_content(
            "# Code Audit\n\n\
             - Last Codex poll: `2026-03-09T10:00:00Z`\n\
             - Last non-audit worktree hash: `abc123def456`\n\n\
             ## Current Verdict\n\n- Scroll fixture active.\n",
        );
        commands.set_runtime_diagnostics(crate::dev_command::RuntimeDiagnosticsSnapshot {
            terminal_host: "Cursor".to_string(),
            backend_label: "codex".to_string(),
            terminal_rows: 40,
            terminal_cols: 120,
            theme_name: "Coral".to_string(),
            auto_voice: "Off".to_string(),
            overlay_mode: "DevPanel".to_string(),
            voice_mode: "Idle".to_string(),
            recording_state: "Idle".to_string(),
            dev_mode: true,
            dev_log: false,
            session_uptime_secs: 42.0,
            transcripts: 3,
            errors: 0,
        });
        let total = cockpit_content_line_count(&commands, DevPanelTab::Control);
        let visible = cockpit_visible_rows();
        assert!(
            total > visible,
            "control content should be scrollable in this test"
        );

        commands.cockpit_scroll_down(2, total.saturating_sub(visible));

        let footer = dev_panel_active_footer(&Theme::Coral.colors(), &commands, 96);
        assert!(footer.contains('['), "footer includes scroll position");
    }
}
