//! Export page: TOML export, import, and clipboard operations.
//!
//! Allows users to:
//! - Export the current theme to a `.toml` file in `~/.config/voiceterm/themes/`
//! - Import a theme from a file path
//! - Copy TOML to clipboard (via OSC 52 if supported)

#![allow(
    dead_code,
    reason = "Theme Studio export UI is scaffolded ahead of full runtime navigation wiring."
)]

use crate::theme::color_value::{palette_to_resolved, ResolvedThemeColors};
use crate::theme::theme_dir::ensure_theme_dir;
use crate::theme::theme_file::export_theme_file;
use crate::theme::Theme;

use super::nav::{select_next, select_prev};

/// State for the Export page.
#[derive(Debug, Clone)]
pub(crate) struct ExportPageState {
    pub(crate) selected: usize,
    pub(crate) last_export_path: Option<String>,
    pub(crate) last_status: Option<String>,
    pending_clipboard_copy: Option<Vec<u8>>,
}

/// Available actions on the export page.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub(crate) enum ExportAction {
    ExportToml,
    CopyToClipboard,
    ImportFile,
}

impl ExportAction {
    pub(crate) const ALL: &'static [Self] =
        &[Self::ExportToml, Self::CopyToClipboard, Self::ImportFile];

    #[must_use]
    pub(crate) fn label(self) -> &'static str {
        match self {
            Self::ExportToml => "Export to TOML file",
            Self::CopyToClipboard => "Copy TOML to clipboard",
            Self::ImportFile => "Import from file",
        }
    }

    #[must_use]
    pub(crate) fn description(self) -> &'static str {
        match self {
            Self::ExportToml => "Save current theme as .toml to ~/.config/voiceterm/themes/",
            Self::CopyToClipboard => "Copy theme TOML to clipboard via OSC 52",
            Self::ImportFile => "Load a .toml theme file from disk",
        }
    }
}

impl ExportPageState {
    /// Create initial state.
    #[must_use]
    pub(crate) fn new() -> Self {
        Self {
            selected: 0,
            last_export_path: None,
            last_status: None,
            pending_clipboard_copy: None,
        }
    }

    /// Get the currently selected action.
    #[must_use]
    pub(crate) fn selected_action(&self) -> ExportAction {
        ExportAction::ALL
            .get(self.selected)
            .copied()
            .unwrap_or(ExportAction::ExportToml)
    }

    /// Select previous action.
    pub(crate) fn select_prev(&mut self) {
        select_prev(&mut self.selected);
    }

    /// Select next action.
    pub(crate) fn select_next(&mut self) {
        select_next(&mut self.selected, ExportAction::ALL.len());
    }

    /// Execute the currently selected action.
    pub(crate) fn execute(&mut self, theme: Theme, colors: Option<&ResolvedThemeColors>) -> &str {
        self.pending_clipboard_copy = None;
        let resolved;
        let colors = match colors {
            Some(c) => c,
            None => {
                resolved = palette_to_resolved(&theme.colors());
                &resolved
            }
        };

        match self.selected_action() {
            ExportAction::ExportToml => self.do_export_toml(theme, colors),
            ExportAction::CopyToClipboard => self.do_copy_clipboard(theme, colors),
            ExportAction::ImportFile => {
                self.last_status = Some("Import: set VOICETERM_THEME_FILE and restart".into());
                self.last_status_or_default()
            }
        }
    }

    fn do_export_toml(&mut self, theme: Theme, colors: &ResolvedThemeColors) -> &str {
        let name = format!("{theme}");
        let toml = export_theme_file(colors, Some(&name), Some(&name));

        match ensure_theme_dir() {
            Ok(dir) => {
                let filename = format!("{name}.toml");
                let path = dir.join(&filename);
                match std::fs::write(&path, &toml) {
                    Ok(()) => {
                        let p = path.display().to_string();
                        self.last_export_path = Some(p.clone());
                        self.last_status = Some(format!("Exported to {p}"));
                    }
                    Err(e) => {
                        self.last_status = Some(format!("Write failed: {e}"));
                    }
                }
            }
            Err(e) => {
                self.last_status = Some(format!("Dir error: {e}"));
            }
        }
        self.last_status_or_default()
    }

    fn do_copy_clipboard(&mut self, theme: Theme, colors: &ResolvedThemeColors) -> &str {
        let name = format!("{theme}");
        let toml = export_theme_file(colors, Some(&name), Some(&name));
        self.pending_clipboard_copy = Some(crate::writer::osc52_copy_bytes(&toml));
        self.last_status = Some("Copied TOML to clipboard (OSC 52)".into());
        self.last_status_or_default()
    }

    pub(crate) fn take_pending_clipboard_copy(&mut self) -> Option<Vec<u8>> {
        self.pending_clipboard_copy.take()
    }

    fn last_status_or_default(&self) -> &str {
        self.last_status
            .as_deref()
            .unwrap_or("Theme Studio export status unavailable")
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn export_page_initial_state() {
        let page = ExportPageState::new();
        assert_eq!(page.selected, 0);
        assert_eq!(page.selected_action(), ExportAction::ExportToml);
        assert!(page.last_export_path.is_none());
        assert!(page.pending_clipboard_copy.is_none());
    }

    #[test]
    fn export_page_navigate() {
        let mut page = ExportPageState::new();
        page.select_next();
        assert_eq!(page.selected_action(), ExportAction::CopyToClipboard);
        page.select_next();
        assert_eq!(page.selected_action(), ExportAction::ImportFile);
        page.select_next(); // should not go past end
        assert_eq!(page.selected_action(), ExportAction::ImportFile);
        page.select_prev();
        assert_eq!(page.selected_action(), ExportAction::CopyToClipboard);
    }

    #[test]
    fn export_action_labels_nonempty() {
        for action in ExportAction::ALL {
            assert!(!action.label().is_empty());
            assert!(!action.description().is_empty());
        }
    }

    #[test]
    fn copy_to_clipboard_stages_writer_payload() {
        let mut page = ExportPageState::new();
        page.selected = 1;

        let status = page.execute(Theme::Coral, None);

        assert_eq!(status, "Copied TOML to clipboard (OSC 52)");
        let payload = page
            .take_pending_clipboard_copy()
            .expect("copy action should stage OSC 52 bytes");
        assert!(payload.starts_with(b"\x1b]52;c;"));
        assert!(payload.ends_with(b"\x07"));
        assert!(page.take_pending_clipboard_copy().is_none());
    }
}
