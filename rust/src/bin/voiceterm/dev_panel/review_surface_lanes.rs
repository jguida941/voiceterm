//! Three-lane rendering helpers for the Dev-panel review surface.

use super::wrap_text;
use crate::dev_command::ReviewArtifact;
use crate::overlay_frame::{display_width, truncate_display};
use crate::theme::ThemeColors;

/// Compute the width of each of the three lane columns given the total
/// inner width (between the two outer frame borders). Two characters are
/// reserved for the two inner lane separator verticals.
pub(super) fn lane_column_widths(inner_width: usize) -> [usize; 3] {
    let usable = inner_width.saturating_sub(2);
    let base = usable / 3;
    let remainder = usable - 2 * base;
    [base, base, remainder]
}

/// Per-lane text wrap widths. Each lane reserves 2 chars of left margin
/// inside its column for readability (1-space pad added by the row renderer
/// + the content's own indentation in `lane_section_lines`).
pub(super) fn lane_wrap_widths(widths: [usize; 3]) -> [usize; 3] {
    [
        widths[0].saturating_sub(2),
        widths[1].saturating_sub(2),
        widths[2].saturating_sub(2),
    ]
}

/// Horizontal rule row with junction characters between lanes.
/// `junction` is the character placed at each inner lane boundary:
/// `t_top` (┬) for the top, `cross` (┼) for the mid, `t_bottom` (┴) for the bottom.
pub(super) fn lane_separator_line(
    colors: &ThemeColors,
    widths: [usize; 3],
    junction: char,
) -> String {
    let borders = &colors.borders;
    let hz = borders.horizontal;
    let mut out = format!("{}{}", colors.border, borders.t_left);
    for (i, &w) in widths.iter().enumerate() {
        let segment: String = std::iter::repeat_n(hz, w).collect();
        out.push_str(&segment);
        if i < 2 {
            out.push(junction);
        }
    }
    out.push(borders.t_right);
    out.push_str(colors.reset);
    out
}

/// Lane heading row: left-aligned lane names styled with info color.
pub(super) fn lane_heading_row(colors: &ThemeColors, widths: [usize; 3]) -> String {
    let borders = &colors.borders;
    let headings = ["Codex", "Claude", "Review / Operator"];
    let mut out = format!("{}{}", colors.border, borders.vertical);
    for (heading, &w) in headings.iter().zip(widths.iter()) {
        let text = format!(" {heading}");
        let clipped = truncate_display(&text, w);
        let pad = " ".repeat(w.saturating_sub(display_width(&clipped)));
        out.push_str(&format!("{}{}{}", colors.info, clipped, pad));
        out.push_str(&format!("{}{}", colors.border, borders.vertical));
    }
    out.push_str(colors.reset);
    out
}

/// Render one row of the three-lane content area with per-cell header detection.
pub(super) fn lane_content_row(
    colors: &ThemeColors,
    cells: [&str; 3],
    widths: [usize; 3],
) -> String {
    let borders = &colors.borders;
    let mut out = format!("{}{}", colors.border, borders.vertical);
    for (cell, &w) in cells.iter().zip(widths.iter()) {
        let is_header = cell.starts_with('\u{25B8}');
        if cell.is_empty() {
            let pad = " ".repeat(w);
            out.push_str(&format!("{}{}", colors.reset, pad));
        } else {
            let text = format!(" {cell}");
            let clipped = truncate_display(&text, w);
            let pad = " ".repeat(w.saturating_sub(display_width(&clipped)));
            if is_header {
                out.push_str(&format!("{}{}{}", colors.info, clipped, pad));
            } else {
                out.push_str(&format!("{}{}{}", colors.reset, clipped, pad));
            }
        }
        out.push_str(&format!("{}{}", colors.border, borders.vertical));
    }
    out.push_str(colors.reset);
    out
}

/// Content lines for the Codex lane: verdict, findings, poll status.
pub(super) fn codex_lane_lines(artifact: &ReviewArtifact, wrap_width: usize) -> Vec<String> {
    let lines = lane_section_lines(
        &[
            ("Verdict", artifact.verdict.as_str()),
            ("Findings", artifact.findings.as_str()),
            ("Poll Status", artifact.poll_status.as_str()),
        ],
        wrap_width,
    );
    if lines.is_empty() {
        return vec!["  (no Codex activity)".to_string()];
    }
    lines
}

/// Content lines for the Claude lane: status, acknowledgment.
pub(super) fn claude_lane_lines(artifact: &ReviewArtifact, wrap_width: usize) -> Vec<String> {
    let lines = lane_section_lines(
        &[
            ("Status", artifact.claude_status.as_str()),
            ("Ack", artifact.claude_ack.as_str()),
        ],
        wrap_width,
    );
    if lines.is_empty() {
        return vec!["  (no Claude activity)".to_string()];
    }
    lines
}

/// Content lines for the Operator lane: bridge metadata + instruction.
pub(super) fn operator_lane_lines(artifact: &ReviewArtifact, wrap_width: usize) -> Vec<String> {
    let mut lines = Vec::new();

    // Bridge-critical metadata (poll timestamps, worktree hash)
    let header_fields = [
        ("Poll UTC", artifact.last_codex_poll.as_str()),
        ("Poll local", artifact.last_codex_poll_local.as_str()),
        ("Tree hash", artifact.last_worktree_hash.as_str()),
    ];
    let has_bridge = header_fields.iter().any(|(_, v)| !v.is_empty());
    if has_bridge {
        lines.push("\u{25B8} Bridge State".to_string());
        for (label, value) in &header_fields {
            if !value.is_empty() {
                for wrapped in wrap_text(&format!("{label}: {value}"), wrap_width) {
                    lines.push(format!("  {wrapped}"));
                }
            }
        }
        lines.push(String::new());
    }

    // Instruction section
    lines.extend(lane_section_lines(
        &[("Instruction", artifact.instruction.as_str())],
        wrap_width,
    ));
    append_context_pack_lines(&mut lines, artifact, wrap_width);

    if lines.is_empty() {
        return vec!["  (no active instruction)".to_string()];
    }
    lines
}

fn append_context_pack_lines(
    lines: &mut Vec<String>,
    artifact: &ReviewArtifact,
    wrap_width: usize,
) {
    if artifact.context_pack_refs.is_empty() {
        return;
    }
    if !lines.is_empty() {
        lines.push(String::new());
    }
    lines.push("\u{25B8} Context Packs".to_string());
    for context_pack_ref in &artifact.context_pack_refs {
        for wrapped in wrap_text(&context_pack_ref.summary_line(), wrap_width) {
            lines.push(format!("  {wrapped}"));
        }
    }
    lines.push(String::new());
}

/// Generate content lines for an ordered list of sections within a lane.
fn lane_section_lines(sections: &[(&str, &str)], wrap_width: usize) -> Vec<String> {
    let mut lines = Vec::new();
    for (name, content) in sections {
        if content.is_empty() {
            continue;
        }
        lines.push(format!("\u{25B8} {name}"));
        for source_line in content.lines() {
            let trimmed = source_line.trim();
            if trimmed.is_empty() {
                lines.push(String::new());
            } else {
                for wrapped in wrap_text(trimmed, wrap_width) {
                    lines.push(format!("  {wrapped}"));
                }
            }
        }
        lines.push(String::new());
    }
    lines
}
