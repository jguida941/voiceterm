//! Theme Studio multi-page editor for no-code full-surface customization.
//!
//! The home page preserves the original cycle-button interface. Additional
//! pages provide color editing, component customization, and TOML export.

mod borders_page;
mod color_picker;
mod colors_page;
mod components_page;
mod export_page;
mod home_page;
mod nav;
mod preview_page;

// Re-export all items from home_page for backward compatibility.
pub(crate) use home_page::{
    format_theme_studio, theme_studio_footer, theme_studio_height,
    theme_studio_inner_width_for_terminal, theme_studio_item_at,
    theme_studio_total_width_for_terminal, ThemeStudioItem, ThemeStudioView, THEME_STUDIO_ITEMS,
    THEME_STUDIO_OPTION_START_ROW,
};

pub(crate) use borders_page::{BorderOption, BordersPageState};
pub(crate) use colors_page::{ColorField, ColorsEditorState};
pub(crate) use components_page::ComponentsEditorState;
pub(crate) use export_page::{ExportAction, ExportPageState};
pub(crate) use preview_page::PreviewPageState;

/// Active page within the multi-page Theme Studio.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
pub(crate) enum StudioPage {
    /// Original cycle-button interface (backward compatible).
    #[default]
    Home,
    /// Semantic color editing with inline color picker.
    Colors,
    /// Border style picker and preview.
    Borders,
    /// Per-component style overrides.
    Components,
    /// Live preview of HUD/toast/overlay with current theme.
    Preview,
    /// TOML export / import.
    Export,
}

impl StudioPage {
    /// All pages in tab-bar order.
    pub(crate) const ALL: &'static [Self] = &[
        Self::Home,
        Self::Colors,
        Self::Borders,
        Self::Components,
        Self::Preview,
        Self::Export,
    ];

    /// Display label for the tab bar.
    #[must_use]
    pub(crate) fn label(self) -> &'static str {
        match self {
            Self::Home => "Home",
            Self::Colors => "Colors",
            Self::Borders => "Borders",
            Self::Components => "Components",
            Self::Preview => "Preview",
            Self::Export => "Export",
        }
    }

    /// Cycle to the next page (Tab key).
    #[must_use]
    pub(crate) fn next(self) -> Self {
        match self {
            Self::Home => Self::Colors,
            Self::Colors => Self::Borders,
            Self::Borders => Self::Components,
            Self::Components => Self::Preview,
            Self::Preview => Self::Export,
            Self::Export => Self::Home,
        }
    }

    /// Cycle to the previous page (Shift+Tab).
    #[must_use]
    pub(crate) fn prev(self) -> Self {
        match self {
            Self::Home => Self::Export,
            Self::Colors => Self::Home,
            Self::Borders => Self::Colors,
            Self::Components => Self::Borders,
            Self::Preview => Self::Components,
            Self::Export => Self::Preview,
        }
    }
}

/// Render the tab bar for the multi-page studio.
#[must_use]
pub(crate) fn format_tab_bar(
    active: StudioPage,
    colors: &crate::theme::ThemeColors,
    inner_width: usize,
) -> String {
    let mut bar = String::new();
    for (i, page) in StudioPage::ALL.iter().enumerate() {
        if i > 0 {
            bar.push_str(" | ");
        }
        if *page == active {
            bar.push_str(&format!("{}{}{}", colors.info, page.label(), colors.reset));
        } else {
            bar.push_str(&format!("{}{}{}", colors.dim, page.label(), colors.reset));
        }
    }

    // Pad to inner_width.
    let plain_len: usize = StudioPage::ALL
        .iter()
        .map(|p| p.label().len())
        .sum::<usize>()
        + (StudioPage::ALL.len() - 1) * 3; // " | " separators
    let padding = inner_width.saturating_sub(plain_len);
    let left_pad = padding / 2;
    let right_pad = padding - left_pad;

    format!(
        "{}{}{}{}{}{}{}{}",
        colors.border,
        colors.borders.vertical,
        colors.reset,
        " ".repeat(left_pad),
        bar,
        " ".repeat(right_pad),
        colors.border,
        colors.borders.vertical,
    )
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn studio_page_next_cycles_through_all() {
        let mut page = StudioPage::Home;
        for expected in &[
            StudioPage::Colors,
            StudioPage::Borders,
            StudioPage::Components,
            StudioPage::Preview,
            StudioPage::Export,
            StudioPage::Home,
        ] {
            page = page.next();
            assert_eq!(page, *expected);
        }
    }

    #[test]
    fn studio_page_prev_cycles_backwards() {
        let mut page = StudioPage::Home;
        for expected in &[
            StudioPage::Export,
            StudioPage::Preview,
            StudioPage::Components,
            StudioPage::Borders,
            StudioPage::Colors,
            StudioPage::Home,
        ] {
            page = page.prev();
            assert_eq!(page, *expected);
        }
    }

    #[test]
    fn studio_page_labels_are_nonempty() {
        for page in StudioPage::ALL {
            assert!(!page.label().is_empty());
        }
    }
}
