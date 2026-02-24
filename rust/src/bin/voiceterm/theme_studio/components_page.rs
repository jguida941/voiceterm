//! Components page: navigable list of all registered component IDs.
//!
//! Users can browse the 54 component IDs from the component registry and
//! view/edit per-state colors for each component.

#![allow(dead_code)]

/// State for the Components editor page.
#[derive(Debug, Clone)]
pub(crate) struct ComponentsEditorState {
    pub(crate) selected: usize,
    pub(crate) expanded_component: Option<usize>,
    pub(crate) selected_state: usize,
}

impl ComponentsEditorState {
    /// Create initial state.
    #[must_use]
    pub(crate) fn new() -> Self {
        Self {
            selected: 0,
            expanded_component: None,
            selected_state: 0,
        }
    }

    /// Move selection up.
    pub(crate) fn move_up(&mut self) {
        if self.selected > 0 {
            self.selected -= 1;
        }
    }

    /// Move selection down with a maximum bound.
    pub(crate) fn move_down(&mut self, max: usize) {
        if self.selected < max.saturating_sub(1) {
            self.selected += 1;
        }
    }

    /// Toggle expansion of the selected component.
    pub(crate) fn toggle_expand(&mut self) {
        if self.expanded_component == Some(self.selected) {
            self.expanded_component = None;
            self.selected_state = 0;
        } else {
            self.expanded_component = Some(self.selected);
            self.selected_state = 0;
        }
    }

    /// Render the components page as lines with color swatches.
    #[must_use]
    pub(crate) fn render(&self, fg_escape: &str, dim_escape: &str, reset: &str) -> Vec<String> {
        use crate::theme::color_value::palette_to_resolved;
        use crate::theme::style_resolver::StyleResolver;
        use crate::theme::Theme;

        // Build a resolver to show semantic default colors.
        let resolved = palette_to_resolved(&Theme::default().colors());
        let resolver = StyleResolver::new(resolved);

        let mut lines = Vec::new();

        for (i, &(group, components)) in COMPONENT_GROUPS.iter().enumerate() {
            let marker = if i == self.selected { "▸" } else { " " };
            let highlight = if i == self.selected {
                fg_escape
            } else {
                dim_escape
            };
            let count = components.len();
            lines.push(format!(
                " {marker} {highlight}{group}{reset}  {dim_escape}({count} components){reset}"
            ));

            if self.expanded_component == Some(i) {
                let category = group_to_category(group);
                for (ci, component) in components.iter().enumerate() {
                    let style_id = format!("components.{category}.{component}");
                    let style = resolver.resolve(&style_id, "default");
                    let swatch = match style.fg {
                        crate::theme::color_value::ColorValue::Rgb(rgb) => {
                            format!("{}██{}", rgb.to_fg_escape(), reset)
                        }
                        _ => format!("{dim_escape}──{reset}"),
                    };
                    let semantic = semantic_hint(category, component);
                    let connector = if ci + 1 < components.len() {
                        "├─"
                    } else {
                        "└─"
                    };
                    lines.push(format!(
                        "     {dim_escape}{connector}{reset} {swatch} {component}  {dim_escape}{semantic}{reset}"
                    ));
                }
            }
        }

        lines
    }

    /// Total number of component groups.
    #[must_use]
    pub(crate) fn group_count(&self) -> usize {
        COMPONENT_GROUPS.len()
    }
}

/// Hint showing which semantic color field drives a component.
fn semantic_hint(category: &str, name: &str) -> &'static str {
    match (category, name) {
        ("toast", "toast_error") => "→ Error",
        ("toast", "toast_warning") => "→ Warning",
        ("toast", "toast_success") => "→ Success",
        ("toast", "toast_info") => "→ Info",
        ("hud", "status_line") => "→ Recording / Processing",
        ("hud", "meter_bar") => "→ Recording",
        ("hud", _) => "→ Info / Dim",
        ("overlay", "overlay_border") => "→ Border",
        ("overlay", "overlay_title") => "→ Info",
        ("overlay", _) => "→ Dim",
        ("voice", "waveform") => "→ Recording",
        ("voice", "pulse_ring") => "→ Processing",
        ("voice", _) => "→ Info",
        ("progress", "progress_bar") => "→ Processing",
        ("progress", "spinner") => "→ Processing",
        ("banner", _) => "→ Info",
        ("button", "rec_button") => "→ Recording",
        ("button", "stop_button") => "→ Error",
        ("button", _) => "→ Dim",
        ("transcript", _) => "→ Info / Dim",
        ("settings", _) => "→ Info / Dim",
        ("studio", _) => "→ Info",
        _ => "",
    }
}

/// Map display group name to the style resolver category token.
fn group_to_category(group: &str) -> &'static str {
    match group {
        "HUD" => "hud",
        "Buttons" => "button",
        "Toast" => "toast",
        "Overlay Chrome" => "overlay",
        "Theme Studio" => "studio",
        "Voice Scene" => "voice",
        "Transcript" => "transcript",
        "Banner" => "banner",
        "Progress" => "progress",
        "Settings" => "settings",
        _ => "unknown",
    }
}

/// Component groups for browsing. Maps to ComponentId categories.
const COMPONENT_GROUPS: &[(&str, &[&str])] = &[
    (
        "HUD",
        &[
            "status_line",
            "shortcuts_row",
            "meter_bar",
            "latency_badge",
            "queue_badge",
        ],
    ),
    (
        "Buttons",
        &[
            "rec_button",
            "stop_button",
            "settings_button",
            "help_button",
        ],
    ),
    (
        "Toast",
        &[
            "toast_info",
            "toast_success",
            "toast_warning",
            "toast_error",
        ],
    ),
    (
        "Overlay Chrome",
        &["overlay_border", "overlay_title", "overlay_footer"],
    ),
    (
        "Theme Studio",
        &["studio_tab_bar", "studio_color_picker", "studio_swatch"],
    ),
    ("Voice Scene", &["waveform", "pulse_ring", "spectrum_bar"]),
    (
        "Transcript",
        &["transcript_preview", "transcript_history_entry"],
    ),
    ("Banner", &["startup_splash", "banner_text"]),
    ("Progress", &["progress_bar", "spinner"]),
    (
        "Settings",
        &["settings_item", "settings_slider", "settings_toggle"],
    ),
];

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn components_editor_initial_state() {
        let editor = ComponentsEditorState::new();
        assert_eq!(editor.selected, 0);
        assert!(editor.expanded_component.is_none());
    }

    #[test]
    fn components_editor_navigate() {
        let mut editor = ComponentsEditorState::new();
        editor.move_down(10);
        editor.move_down(10);
        assert_eq!(editor.selected, 2);
        editor.move_up();
        assert_eq!(editor.selected, 1);
    }

    #[test]
    fn components_editor_toggle_expand() {
        let mut editor = ComponentsEditorState::new();
        editor.toggle_expand();
        assert_eq!(editor.expanded_component, Some(0));
        editor.toggle_expand();
        assert!(editor.expanded_component.is_none());
    }
}
