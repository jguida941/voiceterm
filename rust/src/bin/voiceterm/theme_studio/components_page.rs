//! Components page: local preview editor for component/state style resolution.
//!
//! This slice stays intentionally bounded for `MP-166`: the page now has a
//! real drill-down model for groups, components, states, and editable style
//! properties, but the edits remain local to the page until the wider runtime
//! persistence path is wired.

#![allow(
    dead_code,
    reason = "Theme Studio components page is staged for the bounded MP-166 slice while broader runtime persistence stays pending."
)]

use crate::theme::color_value::{palette_to_resolved, ColorValue};
use crate::theme::style_resolver::{format_color_value, ComponentStyleProperty, StyleResolver};
use crate::theme::Theme;

use super::nav::{select_next, select_prev};

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
struct ComponentEntry {
    label: &'static str,
    style_id: &'static str,
    states: &'static [&'static str],
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
struct ComponentGroup {
    label: &'static str,
    components: &'static [ComponentEntry],
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
enum VisibleRow {
    Group(usize),
    Component {
        group: usize,
        component: usize,
    },
    State {
        group: usize,
        component: usize,
        state: usize,
    },
    Property {
        group: usize,
        component: usize,
        state: usize,
        property: ComponentStyleProperty,
    },
}

/// State for the Components editor page.
#[derive(Debug, Clone)]
pub(crate) struct ComponentsEditorState {
    selected: usize,
    expanded_group: Option<usize>,
    expanded_component: Option<(usize, usize)>,
    expanded_state: Option<(usize, usize, usize)>,
    resolver: StyleResolver,
}

impl ComponentsEditorState {
    /// Create initial state.
    #[must_use]
    pub(crate) fn new() -> Self {
        let resolved = palette_to_resolved(&Theme::default().colors());
        Self {
            selected: 0,
            expanded_group: None,
            expanded_component: None,
            expanded_state: None,
            resolver: StyleResolver::new(resolved),
        }
    }

    /// Select previous visible row.
    pub(crate) fn select_prev(&mut self) {
        select_prev(&mut self.selected);
    }

    /// Select next visible row.
    pub(crate) fn select_next(&mut self, _max: usize) {
        let visible_count = self.visible_rows().len();
        select_next(&mut self.selected, visible_count);
    }

    /// Activate the selected row.
    ///
    /// `Enter` expands groups, components, and states. On property rows it
    /// cycles the selected style property through the bounded preview options.
    pub(crate) fn toggle_expand(&mut self) {
        let Some(row) = self.visible_rows().get(self.selected).copied() else {
            return;
        };

        match row {
            VisibleRow::Group(group) => self.toggle_group(group),
            VisibleRow::Component { group, component } => self.toggle_component(group, component),
            VisibleRow::State {
                group,
                component,
                state,
            } => self.toggle_state(group, component, state),
            VisibleRow::Property {
                group,
                component,
                state,
                property,
            } => {
                let entry = component_entry(group, component);
                let state_name = entry.states[state];
                self.resolver
                    .cycle_property(entry.style_id, state_name, property);
            }
        }

        self.clamp_selected();
    }

    /// Render the components page as a drill-down list with local preview rows.
    #[must_use]
    pub(crate) fn render(&self, fg_escape: &str, dim_escape: &str, reset: &str) -> Vec<String> {
        let mut lines = vec![format!(
            " {dim_escape}Enter expands rows and cycles fields. Edits stay local to this page until runtime persistence lands.{reset}"
        )];

        lines.extend(self.render_selection_summary(fg_escape, dim_escape, reset));
        lines.push(String::new());

        for (index, row) in self.visible_rows().iter().enumerate() {
            let selected = index == self.selected;
            lines.push(self.render_row(*row, selected, fg_escape, dim_escape, reset));
        }

        lines
    }

    /// Total number of visible rows that can be navigated.
    #[must_use]
    pub(crate) fn group_count(&self) -> usize {
        self.visible_rows().len()
    }

    fn toggle_group(&mut self, group: usize) {
        if self.expanded_group == Some(group) {
            self.expanded_group = None;
            self.expanded_component = None;
            self.expanded_state = None;
            return;
        }

        self.expanded_group = Some(group);
        self.expanded_component = None;
        self.expanded_state = None;
    }

    fn toggle_component(&mut self, group: usize, component: usize) {
        self.expanded_group = Some(group);
        if self.expanded_component == Some((group, component)) {
            self.expanded_component = None;
            self.expanded_state = None;
            return;
        }

        self.expanded_component = Some((group, component));
        self.expanded_state = None;
    }

    fn toggle_state(&mut self, group: usize, component: usize, state: usize) {
        self.expanded_group = Some(group);
        self.expanded_component = Some((group, component));
        if self.expanded_state == Some((group, component, state)) {
            self.expanded_state = None;
            return;
        }

        self.expanded_state = Some((group, component, state));
    }

    fn clamp_selected(&mut self) {
        let visible_count = self.visible_rows().len();
        if visible_count == 0 {
            self.selected = 0;
            return;
        }
        self.selected = self.selected.min(visible_count.saturating_sub(1));
    }

    fn render_selection_summary(
        &self,
        fg_escape: &str,
        dim_escape: &str,
        reset: &str,
    ) -> Vec<String> {
        let Some(row) = self.visible_rows().get(self.selected).copied() else {
            return vec![format!(" {dim_escape}No component rows available.{reset}")];
        };

        match row {
            VisibleRow::Group(group) => {
                let entry_count = COMPONENT_GROUPS[group].components.len();
                vec![format!(
                    " {fg_escape}{}{reset}  {dim_escape}{entry_count} components in the current drill-down group.{reset}",
                    COMPONENT_GROUPS[group].label
                )]
            }
            VisibleRow::Component { group, component } => {
                let entry = component_entry(group, component);
                vec![format!(
                    " {fg_escape}{}{reset}  {dim_escape}{} states on {}.{reset}",
                    entry.style_id,
                    entry.states.len(),
                    entry.label
                )]
            }
            VisibleRow::State {
                group,
                component,
                state,
            }
            | VisibleRow::Property {
                group,
                component,
                state,
                ..
            } => {
                let entry = component_entry(group, component);
                let state_name = entry.states[state];
                let style = self.resolver.resolve(entry.style_id, state_name);
                let source = if self.resolver.has_override(entry.style_id, state_name) {
                    "local override"
                } else {
                    "theme default"
                };
                vec![
                    format!(
                        " {fg_escape}{}{reset} / {fg_escape}{}{reset}  {dim_escape}{source}{reset}",
                        entry.style_id, state_name
                    ),
                    format!(
                        " {dim_escape}preview:{reset} fg {}  bg {}  border {}  flags {}",
                        color_chip(style.fg, dim_escape, reset),
                        format_color_value(style.bg),
                        format_color_value(style.border),
                        style_flags_label(style.bold, style.dim),
                    ),
                ]
            }
        }
    }

    fn render_row(
        &self,
        row: VisibleRow,
        selected: bool,
        fg_escape: &str,
        dim_escape: &str,
        reset: &str,
    ) -> String {
        match row {
            VisibleRow::Group(group) => {
                let entry = &COMPONENT_GROUPS[group];
                let marker = if selected { "▸" } else { " " };
                let disclosure = if self.expanded_group == Some(group) {
                    "[-]"
                } else {
                    "[+]"
                };
                let label_color = if selected { fg_escape } else { dim_escape };
                format!(
                    " {marker} {disclosure} {label_color}{:<18}{reset} {dim_escape}({} components){reset}",
                    entry.label,
                    entry.components.len()
                )
            }
            VisibleRow::Component { group, component } => {
                let entry = component_entry(group, component);
                let marker = if selected { "▸" } else { " " };
                let disclosure = if self.expanded_component == Some((group, component)) {
                    "[-]"
                } else {
                    "[+]"
                };
                let label_color = if selected { fg_escape } else { reset };
                let override_count = entry
                    .states
                    .iter()
                    .filter(|state| self.resolver.has_override(entry.style_id, state))
                    .count();
                let override_label = if override_count == 0 {
                    format!("{dim_escape}theme{reset}")
                } else {
                    format!("{fg_escape}{override_count} edited{reset}")
                };
                format!(
                    "     {marker} {disclosure} {label_color}{:<18}{reset} {dim_escape}{}{reset}  {override_label}",
                    entry.label,
                    entry.style_id
                )
            }
            VisibleRow::State {
                group,
                component,
                state,
            } => {
                let entry = component_entry(group, component);
                let state_name = entry.states[state];
                let marker = if selected { "▸" } else { " " };
                let disclosure = if self.expanded_state == Some((group, component, state)) {
                    "[-]"
                } else {
                    "[+]"
                };
                let style = self.resolver.resolve(entry.style_id, state_name);
                let label_color = if selected { fg_escape } else { reset };
                let source = if self.resolver.has_override(entry.style_id, state_name) {
                    "edited"
                } else {
                    "theme"
                };
                format!(
                    "         {marker} {disclosure} {label_color}{:<12}{reset} fg {}  {dim_escape}{source}{reset}",
                    state_name,
                    color_chip(style.fg, dim_escape, reset),
                )
            }
            VisibleRow::Property {
                group,
                component,
                state,
                property,
            } => {
                let entry = component_entry(group, component);
                let state_name = entry.states[state];
                let marker = if selected { "▸" } else { " " };
                let label_color = if selected { fg_escape } else { dim_escape };
                let value =
                    self.resolver
                        .property_value_label(entry.style_id, state_name, property);
                let hint = if selected { "  [Enter cycles]" } else { "" };
                format!(
                    "             {marker} {label_color}{:<10}{reset} {value}{hint}",
                    property.label()
                )
            }
        }
    }

    fn visible_rows(&self) -> Vec<VisibleRow> {
        let mut rows = Vec::new();

        for (group_idx, group) in COMPONENT_GROUPS.iter().enumerate() {
            rows.push(VisibleRow::Group(group_idx));

            if self.expanded_group != Some(group_idx) {
                continue;
            }

            for (component_idx, entry) in group.components.iter().enumerate() {
                rows.push(VisibleRow::Component {
                    group: group_idx,
                    component: component_idx,
                });

                if self.expanded_component != Some((group_idx, component_idx)) {
                    continue;
                }

                for (state_idx, _) in entry.states.iter().enumerate() {
                    rows.push(VisibleRow::State {
                        group: group_idx,
                        component: component_idx,
                        state: state_idx,
                    });

                    if self.expanded_state != Some((group_idx, component_idx, state_idx)) {
                        continue;
                    }

                    for property in ComponentStyleProperty::ALL {
                        rows.push(VisibleRow::Property {
                            group: group_idx,
                            component: component_idx,
                            state: state_idx,
                            property: *property,
                        });
                    }
                }
            }
        }

        rows
    }
}

const CONTROL_STATES: &[&str] = &[
    "default", "hover", "focused", "pressed", "selected", "disabled",
];
const FOCUS_STATES: &[&str] = &["default", "focused"];
const TOAST_STATES: &[&str] = &["default", "muted"];
const HUD_STATES: &[&str] = &[
    "default",
    "idle",
    "listening",
    "recording",
    "processing",
    "responding",
];
const PROGRESS_STATES: &[&str] = &["default", "processing"];
const SIMPLE_STATES: &[&str] = &["default"];
const PALETTE_MATCH_STATES: &[&str] = &["default", "selected"];
const AUTOCOMPLETE_STATES: &[&str] = &["default", "selected", "hover"];
const METER_STATES: &[&str] = &["default", "recording"];

const BUTTON_COMPONENTS: &[ComponentEntry] = &[
    ComponentEntry {
        label: "HUD button",
        style_id: "components.button.hud",
        states: CONTROL_STATES,
    },
    ComponentEntry {
        label: "Overlay button",
        style_id: "components.button.overlay",
        states: CONTROL_STATES,
    },
    ComponentEntry {
        label: "Settings button",
        style_id: "components.button.settings",
        states: CONTROL_STATES,
    },
    ComponentEntry {
        label: "Theme picker button",
        style_id: "components.button.theme_picker",
        states: CONTROL_STATES,
    },
];

const LIST_COMPONENTS: &[ComponentEntry] = &[
    ComponentEntry {
        label: "Settings list",
        style_id: "components.list.settings",
        states: CONTROL_STATES,
    },
    ComponentEntry {
        label: "Help list",
        style_id: "components.list.help",
        states: CONTROL_STATES,
    },
    ComponentEntry {
        label: "Theme picker list",
        style_id: "components.list.theme_picker",
        states: CONTROL_STATES,
    },
    ComponentEntry {
        label: "History list",
        style_id: "components.list.history",
        states: CONTROL_STATES,
    },
    ComponentEntry {
        label: "Settings row",
        style_id: "components.settings.row",
        states: CONTROL_STATES,
    },
    ComponentEntry {
        label: "Theme picker row",
        style_id: "components.theme_picker.row",
        states: CONTROL_STATES,
    },
];

const TOAST_COMPONENTS: &[ComponentEntry] = &[
    ComponentEntry {
        label: "Toast info",
        style_id: "components.toast.info",
        states: TOAST_STATES,
    },
    ComponentEntry {
        label: "Toast success",
        style_id: "components.toast.success",
        states: TOAST_STATES,
    },
    ComponentEntry {
        label: "Toast warning",
        style_id: "components.toast.warning",
        states: TOAST_STATES,
    },
    ComponentEntry {
        label: "Toast error",
        style_id: "components.toast.error",
        states: TOAST_STATES,
    },
];

const HUD_COMPONENTS: &[ComponentEntry] = &[
    ComponentEntry {
        label: "Status line",
        style_id: "components.hud.status_line",
        states: HUD_STATES,
    },
    ComponentEntry {
        label: "HUD banner",
        style_id: "components.hud.banner",
        states: HUD_STATES,
    },
    ComponentEntry {
        label: "HUD meter",
        style_id: "components.hud.meter",
        states: HUD_STATES,
    },
    ComponentEntry {
        label: "HUD latency",
        style_id: "components.hud.latency",
        states: HUD_STATES,
    },
    ComponentEntry {
        label: "HUD queue",
        style_id: "components.hud.queue",
        states: HUD_STATES,
    },
];

const OVERLAY_COMPONENTS: &[ComponentEntry] = &[
    ComponentEntry {
        label: "Overlay frame",
        style_id: "components.overlay.frame",
        states: FOCUS_STATES,
    },
    ComponentEntry {
        label: "Overlay title",
        style_id: "components.overlay.title",
        states: FOCUS_STATES,
    },
    ComponentEntry {
        label: "Overlay footer",
        style_id: "components.overlay.footer",
        states: FOCUS_STATES,
    },
    ComponentEntry {
        label: "Overlay separator",
        style_id: "components.overlay.separator",
        states: SIMPLE_STATES,
    },
];

const PROGRESS_COMPONENTS: &[ComponentEntry] = &[
    ComponentEntry {
        label: "Progress bar",
        style_id: "components.progress.bar",
        states: PROGRESS_STATES,
    },
    ComponentEntry {
        label: "Progress spinner",
        style_id: "components.progress.spinner",
        states: PROGRESS_STATES,
    },
    ComponentEntry {
        label: "Progress bounce",
        style_id: "components.progress.bounce",
        states: PROGRESS_STATES,
    },
];

const STARTUP_COMPONENTS: &[ComponentEntry] = &[
    ComponentEntry {
        label: "Startup splash",
        style_id: "components.startup.splash",
        states: SIMPLE_STATES,
    },
    ComponentEntry {
        label: "Startup banner",
        style_id: "components.startup.banner",
        states: SIMPLE_STATES,
    },
    ComponentEntry {
        label: "Startup tagline",
        style_id: "components.startup.tagline",
        states: SIMPLE_STATES,
    },
];

const VOICE_COMPONENTS: &[ComponentEntry] = &[
    ComponentEntry {
        label: "Voice idle",
        style_id: "components.voice.idle",
        states: SIMPLE_STATES,
    },
    ComponentEntry {
        label: "Voice listening",
        style_id: "components.voice.listening",
        states: SIMPLE_STATES,
    },
    ComponentEntry {
        label: "Voice processing",
        style_id: "components.voice.processing",
        states: SIMPLE_STATES,
    },
    ComponentEntry {
        label: "Voice responding",
        style_id: "components.voice.responding",
        states: SIMPLE_STATES,
    },
];

const COMMAND_COMPONENTS: &[ComponentEntry] = &[
    ComponentEntry {
        label: "Palette frame",
        style_id: "components.palette.frame",
        states: FOCUS_STATES,
    },
    ComponentEntry {
        label: "Palette match",
        style_id: "components.palette.match",
        states: PALETTE_MATCH_STATES,
    },
    ComponentEntry {
        label: "Autocomplete row",
        style_id: "components.autocomplete.row",
        states: AUTOCOMPLETE_STATES,
    },
];

const METER_COMPONENTS: &[ComponentEntry] = &[
    ComponentEntry {
        label: "Meter bar",
        style_id: "components.meter.bar",
        states: METER_STATES,
    },
    ComponentEntry {
        label: "Meter peak",
        style_id: "components.meter.peak",
        states: SIMPLE_STATES,
    },
    ComponentEntry {
        label: "Meter threshold",
        style_id: "components.meter.threshold",
        states: SIMPLE_STATES,
    },
    ComponentEntry {
        label: "Icon pack",
        style_id: "components.icon.pack",
        states: SIMPLE_STATES,
    },
];

const COMPONENT_GROUPS: &[ComponentGroup] = &[
    ComponentGroup {
        label: "Buttons",
        components: BUTTON_COMPONENTS,
    },
    ComponentGroup {
        label: "Lists & Rows",
        components: LIST_COMPONENTS,
    },
    ComponentGroup {
        label: "Toast",
        components: TOAST_COMPONENTS,
    },
    ComponentGroup {
        label: "HUD",
        components: HUD_COMPONENTS,
    },
    ComponentGroup {
        label: "Overlay",
        components: OVERLAY_COMPONENTS,
    },
    ComponentGroup {
        label: "Progress",
        components: PROGRESS_COMPONENTS,
    },
    ComponentGroup {
        label: "Startup",
        components: STARTUP_COMPONENTS,
    },
    ComponentGroup {
        label: "Voice Scene",
        components: VOICE_COMPONENTS,
    },
    ComponentGroup {
        label: "Command Palette",
        components: COMMAND_COMPONENTS,
    },
    ComponentGroup {
        label: "Meter & Icons",
        components: METER_COMPONENTS,
    },
];

fn component_entry(group: usize, component: usize) -> &'static ComponentEntry {
    &COMPONENT_GROUPS[group].components[component]
}

fn color_chip(color: ColorValue, dim_escape: &str, reset: &str) -> String {
    match color {
        ColorValue::Rgb(rgb) => format!("{}██{}", rgb.to_fg_escape(), reset),
        ColorValue::Ansi16(code) => format!("\x1b[{code}m██{reset}"),
        ColorValue::Reset => format!("{dim_escape}rst{reset}"),
        ColorValue::Empty => format!("{dim_escape}--{reset}"),
    }
}

fn style_flags_label(bold: bool, dim: bool) -> &'static str {
    match (bold, dim) {
        (true, true) => "bold + dim",
        (true, false) => "bold",
        (false, true) => "dim",
        (false, false) => "plain",
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn components_editor_initial_state() {
        let editor = ComponentsEditorState::new();
        assert_eq!(editor.selected, 0);
        assert_eq!(editor.group_count(), COMPONENT_GROUPS.len());
        assert!(editor.expanded_group.is_none());
    }

    #[test]
    fn components_editor_drilldown_expands_group_component_and_state() {
        let mut editor = ComponentsEditorState::new();
        editor.toggle_expand();
        assert_eq!(editor.expanded_group, Some(0));

        editor.select_next(editor.group_count());
        editor.toggle_expand();
        assert_eq!(editor.expanded_component, Some((0, 0)));

        editor.select_next(editor.group_count());
        editor.toggle_expand();
        assert_eq!(editor.expanded_state, Some((0, 0, 0)));
    }

    #[test]
    fn components_editor_property_toggle_creates_local_override() {
        let mut editor = ComponentsEditorState::new();
        editor.toggle_expand();
        editor.select_next(editor.group_count());
        editor.toggle_expand();
        editor.select_next(editor.group_count());
        editor.toggle_expand();

        editor.select_next(editor.group_count());
        editor.toggle_expand();

        assert!(editor
            .resolver
            .has_override("components.button.hud", "default"));
    }

    #[test]
    fn components_editor_render_includes_canonical_style_ids() {
        let mut editor = ComponentsEditorState::new();
        editor.toggle_expand();
        let lines = editor.render("", "", "");

        assert!(lines
            .iter()
            .any(|line| line.contains("components.button.hud")));
        assert!(lines
            .iter()
            .any(|line| line.contains("Edits stay local to this page")));
    }
}
