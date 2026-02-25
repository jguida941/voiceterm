//! Borders page: cycle through border styles with live preview.
//!
//! Displays all available border styles and lets users select one with
//! arrow keys and Enter to apply.

use crate::theme::{
    BorderSet, BORDER_DOUBLE, BORDER_HEAVY, BORDER_NONE, BORDER_ROUNDED, BORDER_SINGLE,
};

use super::nav::{select_next, select_prev};

/// Available border style options.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub(crate) enum BorderOption {
    Single,
    Rounded,
    Double,
    Heavy,
    None,
}

impl BorderOption {
    pub(crate) const ALL: &'static [Self] = &[
        Self::Single,
        Self::Rounded,
        Self::Double,
        Self::Heavy,
        Self::None,
    ];

    #[must_use]
    pub(crate) fn label(self) -> &'static str {
        match self {
            Self::Single => "Single",
            Self::Rounded => "Rounded",
            Self::Double => "Double",
            Self::Heavy => "Heavy",
            Self::None => "None",
        }
    }

    #[must_use]
    pub(crate) fn border_set(self) -> &'static BorderSet {
        match self {
            Self::Single => &BORDER_SINGLE,
            Self::Rounded => &BORDER_ROUNDED,
            Self::Double => &BORDER_DOUBLE,
            Self::Heavy => &BORDER_HEAVY,
            Self::None => &BORDER_NONE,
        }
    }
}

/// State for the Borders page.
#[derive(Debug, Clone)]
pub(crate) struct BordersPageState {
    pub(crate) selected: usize,
}

impl BordersPageState {
    #[must_use]
    pub(crate) fn new() -> Self {
        Self { selected: 0 }
    }

    pub(crate) fn select_prev(&mut self) {
        select_prev(&mut self.selected);
    }

    pub(crate) fn select_next(&mut self) {
        select_next(&mut self.selected, BorderOption::ALL.len());
    }

    #[must_use]
    pub(crate) fn selected_option(&self) -> BorderOption {
        BorderOption::ALL
            .get(self.selected)
            .copied()
            .unwrap_or(BorderOption::Single)
    }

    /// Render the borders page as lines with live border previews.
    #[must_use]
    pub(crate) fn render(&self, fg_escape: &str, dim_escape: &str, reset: &str) -> Vec<String> {
        let mut lines = Vec::new();

        for (i, option) in BorderOption::ALL.iter().enumerate() {
            let marker = if i == self.selected { "▸" } else { " " };
            let highlight = if i == self.selected {
                fg_escape
            } else {
                dim_escape
            };
            let bs = option.border_set();

            // Show the style name and a mini border preview.
            lines.push(format!(
                " {marker} {highlight}{:<10}{reset}  {bs_tl}{bs_h}{bs_h}{bs_h}{bs_h}{bs_h}{bs_tr}",
                option.label(),
                bs_tl = bs.top_left,
                bs_h = bs.horizontal,
                bs_tr = bs.top_right,
            ));
            lines.push(format!(
                "                      {bs_v}     {bs_v}",
                bs_v = bs.vertical,
            ));
            lines.push(format!(
                "                      {bs_bl}{bs_h}{bs_h}{bs_h}{bs_h}{bs_h}{bs_br}",
                bs_bl = bs.bottom_left,
                bs_h = bs.horizontal,
                bs_br = bs.bottom_right,
            ));
        }

        lines
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn borders_page_initial_state() {
        let page = BordersPageState::new();
        assert_eq!(page.selected, 0);
        assert_eq!(page.selected_option(), BorderOption::Single);
    }

    #[test]
    fn borders_page_navigate() {
        let mut page = BordersPageState::new();
        page.select_next();
        assert_eq!(page.selected_option(), BorderOption::Rounded);
        page.select_next();
        assert_eq!(page.selected_option(), BorderOption::Double);
        page.select_prev();
        assert_eq!(page.selected_option(), BorderOption::Rounded);
    }

    #[test]
    fn borders_page_render_nonempty() {
        let page = BordersPageState::new();
        let lines = page.render("", "", "");
        assert!(!lines.is_empty());
        assert!(lines[0].contains("Single"));
    }

    #[test]
    fn borders_page_all_options_have_labels() {
        for opt in BorderOption::ALL {
            assert!(!opt.label().is_empty());
        }
    }
}
