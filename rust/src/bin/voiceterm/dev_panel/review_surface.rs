//! Review surface: three-lane layout + single-column view for the active
//! review artifact or structured review-channel projection.

use super::review_surface_lanes::{
    claude_lane_lines, codex_lane_lines, lane_column_widths, lane_content_row, lane_heading_row,
    lane_separator_line, lane_wrap_widths, operator_lane_lines,
};
use super::{dev_panel_height, panel_inner_width, panel_width, review_content_line, wrap_text};
use crate::dev_command::{DevPanelState, ReviewArtifactState, ReviewViewMode};
use crate::overlay_frame::{centered_title_line, frame_bottom, frame_separator, frame_top};
use crate::scrollable::Scrollable;
use crate::theme::{overlay_close_symbol, overlay_separator, resolved_overlay_border_set, Theme};

/// Number of visible content rows in the review surface.
/// In lane mode (parsed + artifact loaded), the three-lane chrome adds 2 extra
/// rows (lane heading + two lane separators vs one frame separator), so
/// `lane_mode=true` returns 2 fewer rows.
pub fn review_visible_rows(lane_mode: bool) -> usize {
    // Non-lane chrome: top, title, separator, separator, footer, bottom = 6
    // Lane chrome: top, title, lane_top_sep, heading, lane_mid_sep,
    //              lane_bottom_sep, footer, bottom = 8
    let chrome = if lane_mode { 8 } else { 6 };
    dev_panel_height().saturating_sub(chrome)
}

/// Visible scroll rows after accounting for any non-scrollable banner rows.
pub fn review_scroll_visible_rows(commands: &DevPanelState) -> usize {
    let lane_mode = commands.review().is_lane_mode();
    let visible_rows = review_visible_rows(lane_mode);
    if lane_mode && commands.review().load_error().is_some() {
        visible_rows.saturating_sub(1)
    } else {
        visible_rows
    }
}

/// Total content lines the review surface would produce for the current artifact.
/// Used by the scroll handler to compute scroll bounds. In lane mode, the count
/// is the max height of the three lane columns (scroll applies uniformly).
pub fn review_content_line_count(commands: &DevPanelState, terminal_width: usize) -> usize {
    let inner_width = panel_inner_width(terminal_width);
    let state = commands.review();
    if let Some(artifact) = state.is_lane_mode().then(|| state.artifact()).flatten() {
        let widths = lane_column_widths(inner_width);
        let wrap = lane_wrap_widths(widths);
        let left = codex_lane_lines(artifact, wrap[0]);
        let mid = claude_lane_lines(artifact, wrap[1]);
        let right = operator_lane_lines(artifact, wrap[2]);
        left.len().max(mid.len()).max(right.len())
    } else {
        review_content_lines(state, inner_width).len()
    }
}

/// Render the review surface tab of the Dev panel.
/// In parsed mode with a loaded artifact, renders three side-by-side lane
/// columns (Codex, Claude, Review/Operator). Otherwise renders a single-column
/// view (raw artifact/projection text, error state, or empty placeholder).
pub fn format_review_surface(theme: Theme, commands: &DevPanelState, width: usize) -> String {
    let mut colors = theme.colors();
    colors.borders = resolved_overlay_border_set(theme);
    let borders = &colors.borders;
    let content_width = panel_width(width);
    let inner_width = content_width.saturating_sub(2);
    let scroll_offset = commands.review().scroll_offset();
    let view_label = commands.review().view_mode().label();
    let lane_artifact = commands
        .review()
        .is_lane_mode()
        .then(|| commands.review().artifact())
        .flatten();
    let footer = review_surface_footer(&colors, commands, width);

    let mut lines = vec![
        frame_top(&colors, borders, content_width),
        centered_title_line(
            &colors,
            borders,
            &format!("VoiceTerm - Review Channel [{view_label}]"),
            content_width,
        ),
    ];

    if let Some(artifact) = lane_artifact {
        let widths = lane_column_widths(inner_width);
        let wrap = lane_wrap_widths(widths);
        let left = codex_lane_lines(artifact, wrap[0]);
        let mid = claude_lane_lines(artifact, wrap[1]);
        let right = operator_lane_lines(artifact, wrap[2]);
        let total_rows = left.len().max(mid.len()).max(right.len());
        let visible_rows = review_scroll_visible_rows(commands);

        // Stale annotation when the artifact is retained across a reload failure.
        if let Some(error) = commands.review().load_error() {
            let stale_msg = format!("  STALE — last reload failed: {error}");
            lines.push(review_content_line(&colors, &stale_msg, inner_width));
        }

        // Lane chrome: top separator, heading row, mid separator
        lines.push(lane_separator_line(&colors, widths, borders.t_top));
        lines.push(lane_heading_row(&colors, widths));
        lines.push(lane_separator_line(&colors, widths, borders.cross));

        // Scrollable lane content
        let start = scroll_offset.min(total_rows);
        let end = (start + visible_rows).min(total_rows);
        for i in start..end {
            let l = left.get(i).map_or("", String::as_str);
            let m = mid.get(i).map_or("", String::as_str);
            let r = right.get(i).map_or("", String::as_str);
            lines.push(lane_content_row(&colors, [l, m, r], widths));
        }
        for _ in (end - start)..visible_rows {
            lines.push(lane_content_row(&colors, ["", "", ""], widths));
        }

        // Bottom lane separator
        lines.push(lane_separator_line(&colors, widths, borders.t_bottom));

        lines.push(centered_title_line(
            &colors,
            borders,
            &footer,
            content_width,
        ));
        lines.push(frame_bottom(&colors, borders, content_width));
    } else {
        // Single-column path: raw view, error state, or no artifact
        let content_lines = review_content_lines(commands.review(), inner_width);
        let total_lines = content_lines.len();
        let visible_rows = review_visible_rows(false);

        lines.push(frame_separator(&colors, borders, content_width));

        let start = scroll_offset.min(total_lines);
        let end = (start + visible_rows).min(total_lines);
        for line in &content_lines[start..end] {
            lines.push(review_content_line(&colors, line, inner_width));
        }
        for _ in (end - start)..visible_rows {
            lines.push(review_content_line(&colors, "", inner_width));
        }

        lines.push(frame_separator(&colors, borders, content_width));
        lines.push(centered_title_line(
            &colors,
            borders,
            &footer,
            content_width,
        ));
        lines.push(frame_bottom(&colors, borders, content_width));
    }

    lines.join("\n")
}

pub(crate) fn review_surface_footer(
    colors: &crate::theme::ThemeColors,
    commands: &DevPanelState,
    terminal_width: usize,
) -> String {
    let close = overlay_close_symbol(colors.glyph_set);
    let sep = overlay_separator(colors.glyph_set);
    let total_lines = review_content_line_count(commands, terminal_width);
    let visible_rows = review_scroll_visible_rows(commands);
    let scroll_offset = commands.review().scroll_offset();
    let scroll_info = if total_lines > visible_rows {
        let max_pos = total_lines.saturating_sub(visible_rows) + 1;
        let cur_pos = scroll_offset.min(max_pos.saturating_sub(1)) + 1;
        format!(" [{cur_pos}/{max_pos}]")
    } else {
        String::new()
    };
    format!(
        "[{close}] close {sep} Tab next {sep} r {} {sep} Enter reload{scroll_info}",
        commands.review().view_mode().label()
    )
}

// ---------------------------------------------------------------------------
// Content projection helpers
// ---------------------------------------------------------------------------

fn review_content_lines(state: &ReviewArtifactState, inner_width: usize) -> Vec<String> {
    if let Some(error) = state.load_error() {
        if state.artifact().is_none() {
            return vec![
                format!("  Error: {error}"),
                String::new(),
                "  Press Enter to reload, or Tab to switch back".to_string(),
            ];
        }
        // Artifact retained from last successful load — show it with stale annotation.
        let mut lines = vec![
            format!("  STALE — last reload failed: {error}"),
            String::new(),
        ];
        lines.extend(match state.view_mode() {
            ReviewViewMode::Raw => raw_content_lines(state, inner_width),
            ReviewViewMode::Parsed => parsed_content_lines(state, inner_width),
        });
        return lines;
    }
    if state.artifact().is_none() {
        return vec![
            "  No review artifact loaded".to_string(),
            String::new(),
            "  Press Enter to load the latest review artifact".to_string(),
        ];
    }

    match state.view_mode() {
        ReviewViewMode::Raw => raw_content_lines(state, inner_width),
        ReviewViewMode::Parsed => parsed_content_lines(state, inner_width),
    }
}

fn raw_content_lines(state: &ReviewArtifactState, inner_width: usize) -> Vec<String> {
    let raw = state.raw_content();
    if raw.is_empty() {
        return vec!["  (empty file)".to_string()];
    }

    let wrap_width = inner_width.saturating_sub(4);
    let mut lines = Vec::new();
    for source_line in raw.lines() {
        if source_line.trim().is_empty() {
            lines.push(String::new());
        } else {
            for wrapped in wrap_text(source_line, wrap_width) {
                lines.push(format!("  {wrapped}"));
            }
        }
    }
    lines
}

fn parsed_content_lines(state: &ReviewArtifactState, inner_width: usize) -> Vec<String> {
    let Some(artifact) = state.artifact() else {
        return vec!["  No review artifact loaded".to_string()];
    };

    // Bridge-critical header metadata rendered as a compact status bar.
    let header_fields: [(&str, &str); 3] = [
        ("Last poll (UTC)", &artifact.last_codex_poll),
        ("Last poll (local)", &artifact.last_codex_poll_local),
        ("Worktree hash", &artifact.last_worktree_hash),
    ];

    let wrap_width = inner_width.saturating_sub(4);
    let mut lines = Vec::new();
    let has_header = header_fields.iter().any(|(_, v)| !v.is_empty());
    if has_header {
        lines.push("\u{25B8} Bridge State".to_string());
        for (label, value) in &header_fields {
            if !value.is_empty() {
                lines.push(format!("  {label}: {value}"));
            }
        }
        lines.push(String::new());
    }

    let sections: [(&str, &str); 6] = [
        ("Verdict", &artifact.verdict),
        ("Findings", &artifact.findings),
        ("Instruction", &artifact.instruction),
        ("Poll Status", &artifact.poll_status),
        ("Claude Ack", &artifact.claude_ack),
        ("Claude Status", &artifact.claude_status),
    ];

    for (name, content) in &sections {
        if content.is_empty() {
            continue;
        }
        lines.push(format!("\u{25B8} {name}"));
        for source_line in content.lines() {
            let trimmed = source_line.trim();
            if trimmed.is_empty() {
                lines.push(String::new());
                continue;
            }
            for wrapped in wrap_text(trimmed, wrap_width) {
                lines.push(format!("  {wrapped}"));
            }
        }
        lines.push(String::new());
    }
    lines
}

#[cfg(test)]
mod tests {
    use crate::dev_command::{DevPanelState, ReviewArtifact, ReviewContextPackRef, ReviewViewMode};
    use crate::dev_panel::dev_panel_height;
    use crate::theme::Theme;

    use super::*;

    #[test]
    fn format_review_surface_line_count_matches_height() {
        let command_state = DevPanelState::default();
        let panel = format_review_surface(Theme::Codex, &command_state, 96);
        assert_eq!(panel.lines().count(), dev_panel_height());
    }

    #[test]
    fn format_review_surface_shows_fallback_when_not_loaded() {
        let command_state = DevPanelState::default();
        let panel = format_review_surface(Theme::Coral, &command_state, 96);
        assert!(panel.contains("Review Channel"));
        assert!(panel.contains("No review artifact loaded"));
    }

    #[test]
    fn format_review_surface_shows_loaded_content() {
        let mut command_state = DevPanelState::default();
        command_state.review_mut().load_from_content(
            "## Current Verdict\n\n- Slice accepted.\n\n## Open Findings\n\n- No blocker.\n",
        );
        let panel = format_review_surface(Theme::Coral, &command_state, 96);
        assert!(panel.contains("Review Channel"));
        assert!(panel.contains("Verdict"));
        assert!(panel.contains("Slice accepted"));
        assert!(panel.contains("Findings"));
        assert!(panel.contains("No blocker"));
    }

    #[test]
    fn format_review_surface_shows_error_state() {
        let mut command_state = DevPanelState::default();
        command_state
            .review_mut()
            .set_load_error("file not found".to_string());
        let panel = format_review_surface(Theme::Coral, &command_state, 96);
        assert!(panel.contains("file not found"));
    }

    #[test]
    fn format_review_surface_shows_bridge_state_header() {
        let mut command_state = DevPanelState::default();
        command_state.review_mut().load_from_content(
            "# Code Audit\n\n\
             - Last Codex poll: `2026-03-08T08:29:37Z`\n\
             - Last Codex poll (Local America/New_York): `2026-03-08 04:29:37 EDT`\n\
             - Last non-audit worktree hash: `abc123`\n\n\
             ## Current Verdict\n\n- ok\n",
        );
        let panel = format_review_surface(Theme::Coral, &command_state, 96);
        assert!(
            panel.contains("Bridge State"),
            "should render bridge header"
        );
        assert!(
            panel.contains("2026-03-08T08:29:37Z"),
            "should show UTC poll"
        );
        assert!(panel.contains("04:29:37 EDT"), "should show local poll");
        assert!(panel.contains("abc123"), "should show worktree hash");
        assert!(panel.contains("Verdict"), "should still show sections");
    }

    #[test]
    fn format_review_surface_no_bridge_when_missing_metadata() {
        let mut command_state = DevPanelState::default();
        command_state
            .review_mut()
            .load_from_content("## Current Verdict\n\n- ok\n");
        let panel = format_review_surface(Theme::Coral, &command_state, 96);
        assert!(
            !panel.contains("Bridge State"),
            "no bridge header without metadata"
        );
    }

    #[test]
    fn format_review_surface_raw_view_shows_markdown() {
        let mut command_state = DevPanelState::default();
        let content = "# Code Audit\n\n## Current Verdict\n\n- ok\n";
        command_state.review_mut().load_from_content(content);
        command_state.review_mut().toggle_view_mode();
        assert_eq!(command_state.review().view_mode(), ReviewViewMode::Raw);
        let panel = format_review_surface(Theme::Coral, &command_state, 96);
        assert!(panel.contains("[raw]"), "title should show [raw]");
        assert!(
            panel.contains("# Code Audit"),
            "should show raw markdown heading"
        );
        assert!(
            panel.contains("## Current Verdict"),
            "should show raw section heading"
        );
    }

    #[test]
    fn format_review_surface_parsed_view_is_default() {
        let mut command_state = DevPanelState::default();
        command_state
            .review_mut()
            .load_from_content("## Current Verdict\n\n- ok\n");
        let panel = format_review_surface(Theme::Coral, &command_state, 96);
        assert!(panel.contains("[parsed]"), "title should show [parsed]");
        assert!(
            panel.contains("Verdict"),
            "should show parsed section label"
        );
    }

    #[test]
    fn toggle_view_mode_resets_scroll() {
        let mut command_state = DevPanelState::default();
        let long = "## Current Verdict\n\n- L1\n- L2\n- L3\n- L4\n- L5\n";
        command_state.review_mut().load_from_content(long);
        command_state.review_mut().scroll_down(5, 10);
        assert_eq!(command_state.review().scroll_offset(), 5);

        command_state.review_mut().toggle_view_mode();
        assert_eq!(
            command_state.review().scroll_offset(),
            0,
            "toggle must reset scroll"
        );
    }

    #[test]
    fn view_mode_toggle_cycles() {
        let mut command_state = DevPanelState::default();
        assert_eq!(command_state.review().view_mode(), ReviewViewMode::Parsed);
        command_state.review_mut().toggle_view_mode();
        assert_eq!(command_state.review().view_mode(), ReviewViewMode::Raw);
        command_state.review_mut().toggle_view_mode();
        assert_eq!(command_state.review().view_mode(), ReviewViewMode::Parsed);
    }

    #[test]
    fn lane_mode_shows_all_three_lane_headings() {
        let mut command_state = DevPanelState::default();
        command_state.review_mut().load_from_content(
            "## Current Verdict\n\n- Accepted.\n\n\
             ## Claude Status\n\n- Phase E in progress.\n\n\
             ## Current Instruction For Claude\n\n1. Build lane layout.\n",
        );
        let panel = format_review_surface(Theme::Coral, &command_state, 96);
        assert!(
            panel.contains("Codex"),
            "Codex lane heading must be visible"
        );
        assert!(
            panel.contains("Claude"),
            "Claude lane heading must be visible"
        );
        assert!(
            panel.contains("Review / Operator"),
            "Operator lane heading must be visible"
        );
    }

    #[test]
    fn lane_mode_routes_content_to_correct_lanes() {
        let mut command_state = DevPanelState::default();
        command_state.review_mut().load_from_content(
            "# Code Audit\n\n\
             - Last Codex poll: `2026-03-08T09:00:00Z`\n\
             - Last non-audit worktree hash: `deadbeef`\n\n\
             ## Current Verdict\n\n- Slice accepted.\n\n\
             ## Open Findings\n\n- No blocker.\n\n\
             ## Claude Status\n\n- Session 6.\n\n\
             ## Claude Ack\n\n- acknowledged.\n\n\
             ## Current Instruction For Claude\n\n1. Build lanes.\n\n\
             ## Poll Status\n\n- active watch.\n",
        );
        let panel = format_review_surface(Theme::Coral, &command_state, 96);

        // Codex lane should contain its sections
        assert!(panel.contains("Verdict"), "Codex lane: Verdict");
        assert!(
            panel.contains("Slice accepted"),
            "Codex lane: verdict content"
        );
        assert!(panel.contains("Findings"), "Codex lane: Findings");
        assert!(panel.contains("Poll Status"), "Codex lane: Poll Status");

        // Claude lane should contain its sections
        assert!(panel.contains("Status"), "Claude lane: Status");
        assert!(panel.contains("Session 6"), "Claude lane: status content");
        assert!(panel.contains("Ack"), "Claude lane: Ack");

        // Operator lane should contain bridge metadata + instruction
        assert!(
            panel.contains("Bridge State"),
            "Operator lane: bridge header"
        );
        assert!(panel.contains("deadbeef"), "Operator lane: worktree hash");
        assert!(panel.contains("Instruction"), "Operator lane: Instruction");
        assert!(
            panel.contains("Build lanes"),
            "Operator lane: instruction content"
        );
    }

    #[test]
    fn operator_lane_shows_context_pack_refs_from_structured_artifact() {
        let lines = operator_lane_lines(
            &ReviewArtifact {
                instruction: "Use attached packs.".to_string(),
                context_pack_refs: vec![ReviewContextPackRef {
                    pack_kind: "task_pack".to_string(),
                    pack_ref: ".voiceterm/memory/exports/task_pack.json".to_string(),
                    adapter_profile: "canonical".to_string(),
                    generated_at_utc: "2026-03-09T13:25:00Z".to_string(),
                }],
                ..Default::default()
            },
            64,
        );
        let rendered = lines.join("\n");
        assert!(rendered.contains("Context Packs"));
        assert!(rendered.contains("task_pack"));
        assert!(rendered.contains("task_pack.json"));
    }

    #[test]
    fn lane_mode_line_count_matches_height() {
        let mut command_state = DevPanelState::default();
        command_state
            .review_mut()
            .load_from_content("## Current Verdict\n\n- ok\n\n## Claude Status\n\n- working\n");
        // Parsed mode + loaded artifact → lane mode
        assert!(command_state.review().is_lane_mode());
        let panel = format_review_surface(Theme::Codex, &command_state, 96);
        assert_eq!(
            panel.lines().count(),
            dev_panel_height(),
            "lane mode output must match dev_panel_height()"
        );
    }

    #[test]
    fn lane_mode_empty_lanes_show_fallback_text() {
        let mut command_state = DevPanelState::default();
        // Only Codex Verdict populated — Claude and Operator lanes should be empty-state
        command_state
            .review_mut()
            .load_from_content("## Current Verdict\n\n- ok\n");
        let panel = format_review_surface(Theme::Coral, &command_state, 96);
        assert!(
            panel.contains("no Claude activity"),
            "empty Claude lane must show fallback"
        );
        assert!(
            panel.contains("no active instruction"),
            "empty Operator lane must show fallback"
        );
        // Codex lane still has content
        assert!(panel.contains("Verdict"), "Codex lane should have Verdict");
    }

    #[test]
    fn lane_mode_all_lanes_empty_shows_all_fallbacks() {
        let mut command_state = DevPanelState::default();
        // Artifact present but all sections empty (only an unrecognized heading)
        command_state
            .review_mut()
            .load_from_content("## Unknown Section\n\n- ignored\n");
        let panel = format_review_surface(Theme::Coral, &command_state, 96);
        assert!(panel.contains("no Codex activity"), "empty Codex fallback");
        assert!(
            panel.contains("no Claude activity"),
            "empty Claude fallback"
        );
        assert!(
            panel.contains("no active instruction"),
            "empty Operator fallback"
        );
    }

    #[test]
    fn raw_mode_still_works_after_lane_refactor() {
        let mut command_state = DevPanelState::default();
        let content = "# Code Audit\n\n## Current Verdict\n\n- ok\n";
        command_state.review_mut().load_from_content(content);
        command_state.review_mut().toggle_view_mode();
        assert_eq!(command_state.review().view_mode(), ReviewViewMode::Raw);
        assert!(!command_state.review().is_lane_mode());

        let panel = format_review_surface(Theme::Coral, &command_state, 96);
        assert!(panel.contains("[raw]"), "title should show [raw]");
        assert!(panel.contains("# Code Audit"), "raw heading visible");
        assert!(
            panel.contains("## Current Verdict"),
            "raw section heading visible"
        );
        assert_eq!(
            panel.lines().count(),
            dev_panel_height(),
            "raw mode line count must match"
        );
    }

    #[test]
    fn stale_error_shows_retained_artifact_with_annotation() {
        let mut command_state = DevPanelState::default();
        command_state.review_mut().load_from_content(
            "## Current Verdict\n\n- Accepted.\n\n## Open Findings\n\n- No blocker.\n",
        );
        // Simulate a transient reload failure after successful parse.
        command_state
            .review_mut()
            .set_load_error("permission denied".to_string());
        assert!(
            command_state.review().artifact().is_some(),
            "artifact must be retained across error"
        );

        let panel = format_review_surface(Theme::Coral, &command_state, 96);
        assert!(panel.contains("STALE"), "stale annotation must be visible");
        assert!(
            panel.contains("permission denied"),
            "error message must appear in annotation"
        );
        assert!(
            panel.contains("Verdict"),
            "retained artifact content must still render"
        );
    }

    #[test]
    fn stale_lane_footer_uses_reduced_visible_rows_for_scroll_suffix() {
        let mut command_state = DevPanelState::default();
        let verdict_lines = (1..=40)
            .map(|idx| format!("- verdict-row-{idx:03}"))
            .collect::<Vec<_>>()
            .join("\n");
        let content =
            format!("## Current Verdict\n\n{verdict_lines}\n\n## Claude Status\n\n- synced\n");
        command_state.review_mut().load_from_content(&content);
        command_state
            .review_mut()
            .set_load_error("permission denied".to_string());

        let visible = review_scroll_visible_rows(&command_state);
        let total = review_content_line_count(&command_state, 96);
        let max_offset = total.saturating_sub(visible);
        command_state
            .review_mut()
            .scroll_down(max_offset, max_offset);

        let footer = review_surface_footer(&Theme::Coral.colors(), &command_state, 96);
        let max_pos = max_offset + 1;
        assert!(
            footer.contains(&format!("[{max_pos}/{max_pos}]")),
            "footer should use the stale-banner-adjusted visible rows: {footer}"
        );
    }
}
