//! Preview page: read-only live preview of HUD, toast, and overlay elements
//! rendered with the current theme.
//!
//! Shows sample mock-ups so users can see how their customizations look
//! without leaving the Theme Studio.

/// State for the Preview page.
#[derive(Debug, Clone)]
pub(crate) struct PreviewPageState {
    pub(crate) scroll_offset: usize,
}

impl PreviewPageState {
    #[must_use]
    pub(crate) fn new() -> Self {
        Self { scroll_offset: 0 }
    }

    pub(crate) fn scroll_up(&mut self) {
        self.scroll_offset = self.scroll_offset.saturating_sub(1);
    }

    pub(crate) fn scroll_down(&mut self, max_lines: usize, visible: usize) {
        if max_lines > visible && self.scroll_offset < max_lines - visible {
            self.scroll_offset += 1;
        }
    }

    /// Render a preview of various themed components.
    #[must_use]
    pub(crate) fn render(&self, colors: &crate::theme::ThemeColors) -> Vec<String> {
        let mut lines = Vec::new();

        // Section: Status Line Preview
        lines.push(format!(" {}── Status Line ──{}", colors.info, colors.reset));
        lines.push(format!(
            "  {}Recording{} | {}Processing{} | {}Success{}",
            colors.recording,
            colors.reset,
            colors.processing,
            colors.reset,
            colors.success,
            colors.reset,
        ));
        lines.push(format!(
            "  {}Warning{} | {}Error{} | {}Info{}",
            colors.warning, colors.reset, colors.error, colors.reset, colors.info, colors.reset,
        ));
        lines.push(String::new());

        // Section: Indicators
        lines.push(format!(" {}── Indicators ──{}", colors.info, colors.reset));
        lines.push(format!(
            "  Rec: {}{}{}  Auto: {}{}{}  Processing: {}{}{}",
            colors.recording,
            colors.indicator_rec,
            colors.reset,
            colors.info,
            colors.indicator_auto,
            colors.reset,
            colors.processing,
            colors.indicator_processing,
            colors.reset,
        ));
        lines.push(String::new());

        // Section: Toast Preview
        lines.push(format!(
            " {}── Toast Styles ──{}",
            colors.info, colors.reset
        ));
        lines.push(format!(
            "  {}[info]{} Sample info toast",
            colors.info, colors.reset,
        ));
        lines.push(format!(
            "  {}[success]{} Sample success toast",
            colors.success, colors.reset,
        ));
        lines.push(format!(
            "  {}[warning]{} Sample warning toast",
            colors.warning, colors.reset,
        ));
        lines.push(format!(
            "  {}[error]{} Sample error toast",
            colors.error, colors.reset,
        ));
        lines.push(String::new());

        // Section: Borders
        let bs = &colors.borders;
        lines.push(format!(
            " {}── Border Preview ──{}",
            colors.info, colors.reset
        ));
        lines.push(format!(
            "  {}{}{}{}{}{}{}{}{} {}Border style{}",
            colors.border,
            bs.top_left,
            bs.horizontal,
            bs.horizontal,
            bs.horizontal,
            bs.horizontal,
            bs.horizontal,
            bs.top_right,
            colors.reset,
            colors.dim,
            colors.reset,
        ));
        lines.push(format!(
            "  {}{}     {}{}",
            colors.border, bs.vertical, bs.vertical, colors.reset,
        ));
        lines.push(format!(
            "  {}{}{}{}{}{}{}{}{}",
            colors.border,
            bs.bottom_left,
            bs.horizontal,
            bs.horizontal,
            bs.horizontal,
            bs.horizontal,
            bs.horizontal,
            bs.bottom_right,
            colors.reset,
        ));
        lines.push(String::new());

        // Section: Dim/Reset
        lines.push(format!(" {}── Dim Text ──{}", colors.info, colors.reset));
        lines.push(format!(
            "  {}This is dim/muted text used for secondary info.{}",
            colors.dim, colors.reset,
        ));

        lines
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::theme::Theme;

    #[test]
    fn preview_page_initial_state() {
        let page = PreviewPageState::new();
        assert_eq!(page.scroll_offset, 0);
    }

    #[test]
    fn preview_page_scroll() {
        let mut page = PreviewPageState::new();
        page.scroll_down(20, 10);
        assert_eq!(page.scroll_offset, 1);
        page.scroll_up();
        assert_eq!(page.scroll_offset, 0);
        page.scroll_up(); // shouldn't go below 0
        assert_eq!(page.scroll_offset, 0);
    }

    #[test]
    fn preview_page_render_nonempty() {
        let page = PreviewPageState::new();
        let colors = Theme::Codex.colors();
        let lines = page.render(&colors);
        assert!(!lines.is_empty());
        assert!(lines[0].contains("Status Line"));
    }
}
