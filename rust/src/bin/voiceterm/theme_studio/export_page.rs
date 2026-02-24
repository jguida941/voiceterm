//! Export page: TOML export, import, and clipboard operations.
//!
//! Allows users to:
//! - Export the current theme to a `.toml` file in `~/.config/voiceterm/themes/`
//! - Import a theme from a file path
//! - Copy TOML to clipboard (via OSC 52 if supported)

#![allow(dead_code)]

use crate::theme::color_value::{palette_to_resolved, ResolvedThemeColors};
use crate::theme::theme_dir::ensure_theme_dir;
use crate::theme::theme_file::export_theme_file;
use crate::theme::Theme;

/// State for the Export page.
#[derive(Debug, Clone)]
pub(crate) struct ExportPageState {
    pub(crate) selected: usize,
    pub(crate) last_export_path: Option<String>,
    pub(crate) last_status: Option<String>,
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

    /// Move selection up.
    pub(crate) fn move_up(&mut self) {
        if self.selected > 0 {
            self.selected -= 1;
        }
    }

    /// Move selection down.
    pub(crate) fn move_down(&mut self) {
        if self.selected < ExportAction::ALL.len() - 1 {
            self.selected += 1;
        }
    }

    /// Execute the currently selected action.
    pub(crate) fn execute(&mut self, theme: Theme, colors: Option<&ResolvedThemeColors>) -> &str {
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

        // OSC 52 clipboard: \x1b]52;c;<base64>\x07
        use std::io::Write;
        let encoded = base64_encode(toml.as_bytes());
        let osc = format!("\x1b]52;c;{encoded}\x07");
        let _ = std::io::stdout().write_all(osc.as_bytes());
        let _ = std::io::stdout().flush();

        self.last_status = Some("Copied TOML to clipboard (OSC 52)".into());
        self.last_status_or_default()
    }

    fn last_status_or_default(&self) -> &str {
        self.last_status
            .as_deref()
            .unwrap_or("Theme Studio export status unavailable")
    }
}

/// Minimal base64 encoder (no external dependency needed).
fn base64_encode(input: &[u8]) -> String {
    const CHARS: &[u8; 64] = b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
    let mut out = String::with_capacity((input.len() + 2) / 3 * 4);
    for chunk in input.chunks(3) {
        let b0 = chunk[0] as u32;
        let b1 = if chunk.len() > 1 { chunk[1] as u32 } else { 0 };
        let b2 = if chunk.len() > 2 { chunk[2] as u32 } else { 0 };
        let triple = (b0 << 16) | (b1 << 8) | b2;
        out.push(CHARS[((triple >> 18) & 0x3F) as usize] as char);
        out.push(CHARS[((triple >> 12) & 0x3F) as usize] as char);
        if chunk.len() > 1 {
            out.push(CHARS[((triple >> 6) & 0x3F) as usize] as char);
        } else {
            out.push('=');
        }
        if chunk.len() > 2 {
            out.push(CHARS[(triple & 0x3F) as usize] as char);
        } else {
            out.push('=');
        }
    }
    out
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
    }

    #[test]
    fn export_page_navigate() {
        let mut page = ExportPageState::new();
        page.move_down();
        assert_eq!(page.selected_action(), ExportAction::CopyToClipboard);
        page.move_down();
        assert_eq!(page.selected_action(), ExportAction::ImportFile);
        page.move_down(); // should not go past end
        assert_eq!(page.selected_action(), ExportAction::ImportFile);
        page.move_up();
        assert_eq!(page.selected_action(), ExportAction::CopyToClipboard);
    }

    #[test]
    fn export_action_labels_nonempty() {
        for action in ExportAction::ALL {
            assert!(!action.label().is_empty());
            assert!(!action.description().is_empty());
        }
    }
}
