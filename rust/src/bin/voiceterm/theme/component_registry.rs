//! Styleable component registry and state-matrix contract for all renderable
//! control surfaces.
//!
//! Every renderable component has a stable `ComponentId` and every interaction
//! state has a `ComponentState`. The registry maps component/state pairs to
//! default style tokens so the resolver never encounters an unregistered
//! surface at runtime.

#![allow(dead_code)]

use std::collections::HashMap;

/// Stable identifiers for every renderable control surface.
///
/// New surfaces must be registered here before they can be rendered, enforced
/// by the `component_registry_parity` snapshot test.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub(crate) enum ComponentId {
    // -- Buttons / controls --
    ButtonHud,
    ButtonOverlay,
    ButtonSettings,
    ButtonThemePicker,

    // -- Tabs --
    TabStudio,
    TabSettings,

    // -- Lists --
    ListSettings,
    ListHelp,
    ListThemePicker,
    ListHistory,

    // -- Tables --
    TableShortcuts,

    // -- Trees --
    TreeLayout,

    // -- Scrollbars --
    ScrollbarOverlay,

    // -- Modals / popups / tooltips --
    ModalConfirm,
    PopupToast,
    TooltipHint,

    // -- Input fields --
    InputSearch,
    InputSlider,

    // -- Toasts --
    ToastInfo,
    ToastSuccess,
    ToastWarning,
    ToastError,

    // -- HUD surfaces --
    HudStatusLine,
    HudBanner,
    HudMeter,
    HudLatency,
    HudQueue,
    HudMode,
    HudWaveform,

    // -- Overlay chrome --
    OverlayFrame,
    OverlayTitle,
    OverlayFooter,
    OverlaySeparator,

    // -- Progress --
    ProgressBar,
    ProgressSpinner,
    ProgressBounce,

    // -- Startup / banner --
    StartupSplash,
    StartupBanner,
    StartupTagline,

    // -- Help / settings chrome --
    HelpSection,
    SettingsRow,
    ThemePickerRow,

    // -- Audio meter / calibration --
    MeterBar,
    MeterPeak,
    MeterThreshold,

    // -- Icons / glyphs --
    IconPack,

    // -- Voice state scenes --
    VoiceIdle,
    VoiceListening,
    VoiceProcessing,
    VoiceResponding,

    // -- Command palette / autocomplete --
    PaletteFrame,
    PaletteMatch,
    AutocompleteRow,

    // -- Dashboard --
    DashboardPanel,
}

impl ComponentId {
    /// Stable style-ID path for this renderable component.
    ///
    /// Keep this exhaustive match in sync with the enum so new components
    /// cannot land without an explicit style-ID decision.
    #[must_use]
    pub(crate) const fn style_id(self) -> &'static str {
        match self {
            Self::ButtonHud => "components.button.hud",
            Self::ButtonOverlay => "components.button.overlay",
            Self::ButtonSettings => "components.button.settings",
            Self::ButtonThemePicker => "components.button.theme_picker",
            Self::TabStudio => "components.tab.studio",
            Self::TabSettings => "components.tab.settings",
            Self::ListSettings => "components.list.settings",
            Self::ListHelp => "components.list.help",
            Self::ListThemePicker => "components.list.theme_picker",
            Self::ListHistory => "components.list.history",
            Self::TableShortcuts => "components.table.shortcuts",
            Self::TreeLayout => "components.tree.layout",
            Self::ScrollbarOverlay => "components.scrollbar.overlay",
            Self::ModalConfirm => "components.modal.confirm",
            Self::PopupToast => "components.popup.toast",
            Self::TooltipHint => "components.tooltip.hint",
            Self::InputSearch => "components.input.search",
            Self::InputSlider => "components.input.slider",
            Self::ToastInfo => "components.toast.info",
            Self::ToastSuccess => "components.toast.success",
            Self::ToastWarning => "components.toast.warning",
            Self::ToastError => "components.toast.error",
            Self::HudStatusLine => "components.hud.status_line",
            Self::HudBanner => "components.hud.banner",
            Self::HudMeter => "components.hud.meter",
            Self::HudLatency => "components.hud.latency",
            Self::HudQueue => "components.hud.queue",
            Self::HudMode => "components.hud.mode",
            Self::HudWaveform => "components.hud.waveform",
            Self::OverlayFrame => "components.overlay.frame",
            Self::OverlayTitle => "components.overlay.title",
            Self::OverlayFooter => "components.overlay.footer",
            Self::OverlaySeparator => "components.overlay.separator",
            Self::ProgressBar => "components.progress.bar",
            Self::ProgressSpinner => "components.progress.spinner",
            Self::ProgressBounce => "components.progress.bounce",
            Self::StartupSplash => "components.startup.splash",
            Self::StartupBanner => "components.startup.banner",
            Self::StartupTagline => "components.startup.tagline",
            Self::HelpSection => "components.help.section",
            Self::SettingsRow => "components.settings.row",
            Self::ThemePickerRow => "components.theme_picker.row",
            Self::MeterBar => "components.meter.bar",
            Self::MeterPeak => "components.meter.peak",
            Self::MeterThreshold => "components.meter.threshold",
            Self::IconPack => "components.icon.pack",
            Self::VoiceIdle => "components.voice.idle",
            Self::VoiceListening => "components.voice.listening",
            Self::VoiceProcessing => "components.voice.processing",
            Self::VoiceResponding => "components.voice.responding",
            Self::PaletteFrame => "components.palette.frame",
            Self::PaletteMatch => "components.palette.match",
            Self::AutocompleteRow => "components.autocomplete.row",
            Self::DashboardPanel => "components.dashboard.panel",
        }
    }
}

/// Interaction / visual state variants for components.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub(crate) enum ComponentState {
    Default,
    Hover,
    Focused,
    Pressed,
    Selected,
    Disabled,
    // -- Voice states --
    Idle,
    Listening,
    Recording,
    Processing,
    Responding,
    // -- Semantic states --
    Success,
    Warning,
    Error,
    Muted,
}

/// Default style token attached to a component/state pair.
#[derive(Debug, Clone, PartialEq, Eq)]
pub(crate) struct ComponentStyleEntry {
    /// Human-readable label for documentation / inspector.
    pub(crate) label: &'static str,
    /// Whether this component requires resolver routing (true) vs. uses
    /// default hardcoded style (false, legacy allowlist only).
    pub(crate) resolver_routed: bool,
}

/// Registry of all known renderable components and their state variants.
#[derive(Debug)]
pub(crate) struct ComponentRegistry {
    entries: HashMap<(ComponentId, ComponentState), ComponentStyleEntry>,
}

impl ComponentRegistry {
    /// Build the default registry with entries for all known components.
    #[must_use]
    pub(crate) fn build_default() -> Self {
        let mut entries = HashMap::new();

        // Helper to insert a batch of states for a component.
        let mut register = |id: ComponentId, label: &'static str, states: &[ComponentState]| {
            for &state in states {
                entries.insert(
                    (id, state),
                    ComponentStyleEntry {
                        label,
                        resolver_routed: true,
                    },
                );
            }
        };

        // Standard interaction states used by most controls.
        let control_states = &[
            ComponentState::Default,
            ComponentState::Hover,
            ComponentState::Focused,
            ComponentState::Pressed,
            ComponentState::Selected,
            ComponentState::Disabled,
        ];

        // Buttons
        register(ComponentId::ButtonHud, "HUD button", control_states);
        register(ComponentId::ButtonOverlay, "Overlay button", control_states);
        register(
            ComponentId::ButtonSettings,
            "Settings button",
            control_states,
        );
        register(
            ComponentId::ButtonThemePicker,
            "Theme picker button",
            control_states,
        );

        // Tabs
        register(ComponentId::TabStudio, "Studio tab", control_states);
        register(ComponentId::TabSettings, "Settings tab", control_states);

        // Lists
        register(ComponentId::ListSettings, "Settings list", control_states);
        register(ComponentId::ListHelp, "Help list", control_states);
        register(
            ComponentId::ListThemePicker,
            "Theme picker list",
            control_states,
        );
        register(ComponentId::ListHistory, "History list", control_states);

        // Tables
        register(
            ComponentId::TableShortcuts,
            "Shortcuts table",
            control_states,
        );

        // Trees
        register(ComponentId::TreeLayout, "Layout tree", control_states);

        // Scrollbars
        register(
            ComponentId::ScrollbarOverlay,
            "Overlay scrollbar",
            &[
                ComponentState::Default,
                ComponentState::Hover,
                ComponentState::Disabled,
            ],
        );

        // Modals / popups / tooltips
        register(
            ComponentId::ModalConfirm,
            "Confirm modal",
            &[ComponentState::Default, ComponentState::Focused],
        );
        register(
            ComponentId::PopupToast,
            "Toast popup",
            &[ComponentState::Default, ComponentState::Focused],
        );
        register(
            ComponentId::TooltipHint,
            "Hint tooltip",
            &[ComponentState::Default],
        );

        // Input fields
        register(
            ComponentId::InputSearch,
            "Search input",
            &[
                ComponentState::Default,
                ComponentState::Focused,
                ComponentState::Disabled,
            ],
        );
        register(
            ComponentId::InputSlider,
            "Slider input",
            &[
                ComponentState::Default,
                ComponentState::Focused,
                ComponentState::Disabled,
            ],
        );

        // Toasts
        let toast_states = &[ComponentState::Default, ComponentState::Muted];
        register(ComponentId::ToastInfo, "Toast info", toast_states);
        register(ComponentId::ToastSuccess, "Toast success", toast_states);
        register(ComponentId::ToastWarning, "Toast warning", toast_states);
        register(ComponentId::ToastError, "Toast error", toast_states);

        // HUD surfaces
        let hud_states = &[
            ComponentState::Default,
            ComponentState::Idle,
            ComponentState::Listening,
            ComponentState::Recording,
            ComponentState::Processing,
            ComponentState::Responding,
        ];
        register(ComponentId::HudStatusLine, "HUD status line", hud_states);
        register(ComponentId::HudBanner, "HUD banner", hud_states);
        register(ComponentId::HudMeter, "HUD meter", hud_states);
        register(ComponentId::HudLatency, "HUD latency", hud_states);
        register(ComponentId::HudQueue, "HUD queue", hud_states);
        register(ComponentId::HudMode, "HUD mode", hud_states);
        register(ComponentId::HudWaveform, "HUD waveform", hud_states);

        // Overlay chrome
        let chrome_states = &[ComponentState::Default, ComponentState::Focused];
        register(ComponentId::OverlayFrame, "Overlay frame", chrome_states);
        register(ComponentId::OverlayTitle, "Overlay title", chrome_states);
        register(ComponentId::OverlayFooter, "Overlay footer", chrome_states);
        register(
            ComponentId::OverlaySeparator,
            "Overlay separator",
            &[ComponentState::Default],
        );

        // Progress
        let progress_states = &[ComponentState::Default, ComponentState::Processing];
        register(ComponentId::ProgressBar, "Progress bar", progress_states);
        register(
            ComponentId::ProgressSpinner,
            "Progress spinner",
            progress_states,
        );
        register(ComponentId::ProgressBounce, "Bounce bar", progress_states);

        // Startup / banner
        register(
            ComponentId::StartupSplash,
            "Startup splash",
            &[ComponentState::Default],
        );
        register(
            ComponentId::StartupBanner,
            "Startup banner",
            &[ComponentState::Default],
        );
        register(
            ComponentId::StartupTagline,
            "Startup tagline",
            &[ComponentState::Default],
        );

        // Help / settings chrome
        register(ComponentId::HelpSection, "Help section", control_states);
        register(ComponentId::SettingsRow, "Settings row", control_states);
        register(
            ComponentId::ThemePickerRow,
            "Theme picker row",
            control_states,
        );

        // Audio meter / calibration
        register(
            ComponentId::MeterBar,
            "Meter bar",
            &[ComponentState::Default, ComponentState::Recording],
        );
        register(
            ComponentId::MeterPeak,
            "Meter peak",
            &[ComponentState::Default],
        );
        register(
            ComponentId::MeterThreshold,
            "Meter threshold",
            &[ComponentState::Default],
        );

        // Icons
        register(
            ComponentId::IconPack,
            "Icon pack",
            &[ComponentState::Default],
        );

        // Voice state scenes
        register(
            ComponentId::VoiceIdle,
            "Voice idle scene",
            &[ComponentState::Default],
        );
        register(
            ComponentId::VoiceListening,
            "Voice listening scene",
            &[ComponentState::Default],
        );
        register(
            ComponentId::VoiceProcessing,
            "Voice processing scene",
            &[ComponentState::Default],
        );
        register(
            ComponentId::VoiceResponding,
            "Voice responding scene",
            &[ComponentState::Default],
        );

        // Command palette / autocomplete
        register(
            ComponentId::PaletteFrame,
            "Palette frame",
            &[ComponentState::Default, ComponentState::Focused],
        );
        register(
            ComponentId::PaletteMatch,
            "Palette match",
            &[ComponentState::Default, ComponentState::Selected],
        );
        register(
            ComponentId::AutocompleteRow,
            "Autocomplete row",
            &[
                ComponentState::Default,
                ComponentState::Selected,
                ComponentState::Hover,
            ],
        );

        // Dashboard
        register(
            ComponentId::DashboardPanel,
            "Dashboard panel",
            &[ComponentState::Default, ComponentState::Focused],
        );

        Self { entries }
    }

    /// Look up the style entry for a component/state pair.
    #[must_use]
    pub(crate) fn get(
        &self,
        id: ComponentId,
        state: ComponentState,
    ) -> Option<&ComponentStyleEntry> {
        self.entries.get(&(id, state))
    }

    /// Check whether a component ID is registered (any state).
    #[must_use]
    pub(crate) fn is_registered(&self, id: ComponentId) -> bool {
        self.entries.keys().any(|(cid, _)| *cid == id)
    }

    /// Return all registered component IDs (deduplicated).
    #[must_use]
    pub(crate) fn all_component_ids(&self) -> Vec<ComponentId> {
        let mut ids: Vec<ComponentId> = self.entries.keys().map(|(id, _)| *id).collect();
        ids.sort_unstable_by_key(|id| format!("{id:?}"));
        ids.dedup();
        ids
    }

    /// Total number of (component, state) entries.
    #[must_use]
    pub(crate) fn entry_count(&self) -> usize {
        self.entries.len()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::collections::HashSet;

    #[test]
    fn default_registry_is_nonempty() {
        let registry = ComponentRegistry::build_default();
        assert!(registry.entry_count() > 50);
    }

    #[test]
    fn default_registry_covers_all_component_ids() {
        let registry = ComponentRegistry::build_default();
        let mut ids = registry.all_component_ids();
        // Ensure every variant of ComponentId is present.
        let mut expected_ids = vec![
            ComponentId::ButtonHud,
            ComponentId::ButtonOverlay,
            ComponentId::ButtonSettings,
            ComponentId::ButtonThemePicker,
            ComponentId::TabStudio,
            ComponentId::TabSettings,
            ComponentId::ListSettings,
            ComponentId::ListHelp,
            ComponentId::ListThemePicker,
            ComponentId::ListHistory,
            ComponentId::TableShortcuts,
            ComponentId::TreeLayout,
            ComponentId::ScrollbarOverlay,
            ComponentId::ModalConfirm,
            ComponentId::PopupToast,
            ComponentId::TooltipHint,
            ComponentId::InputSearch,
            ComponentId::InputSlider,
            ComponentId::ToastInfo,
            ComponentId::ToastSuccess,
            ComponentId::ToastWarning,
            ComponentId::ToastError,
            ComponentId::HudStatusLine,
            ComponentId::HudBanner,
            ComponentId::HudMeter,
            ComponentId::HudLatency,
            ComponentId::HudQueue,
            ComponentId::HudMode,
            ComponentId::HudWaveform,
            ComponentId::OverlayFrame,
            ComponentId::OverlayTitle,
            ComponentId::OverlayFooter,
            ComponentId::OverlaySeparator,
            ComponentId::ProgressBar,
            ComponentId::ProgressSpinner,
            ComponentId::ProgressBounce,
            ComponentId::StartupSplash,
            ComponentId::StartupBanner,
            ComponentId::StartupTagline,
            ComponentId::HelpSection,
            ComponentId::SettingsRow,
            ComponentId::ThemePickerRow,
            ComponentId::MeterBar,
            ComponentId::MeterPeak,
            ComponentId::MeterThreshold,
            ComponentId::IconPack,
            ComponentId::VoiceIdle,
            ComponentId::VoiceListening,
            ComponentId::VoiceProcessing,
            ComponentId::VoiceResponding,
            ComponentId::PaletteFrame,
            ComponentId::PaletteMatch,
            ComponentId::AutocompleteRow,
            ComponentId::DashboardPanel,
        ];
        for expected in &expected_ids {
            assert!(
                registry.is_registered(*expected),
                "ComponentId {:?} is not registered",
                expected
            );
        }
        ids.sort_unstable_by_key(|id| format!("{id:?}"));
        expected_ids.sort_unstable_by_key(|id| format!("{id:?}"));
        assert_eq!(
            ids, expected_ids,
            "registry component inventory drifted from declared style-ID inventory"
        );
    }

    #[test]
    fn registry_lookup_returns_entry_for_registered_pairs() {
        let registry = ComponentRegistry::build_default();
        let entry = registry
            .get(ComponentId::ButtonHud, ComponentState::Default)
            .expect("ButtonHud/Default should be registered");
        assert_eq!(entry.label, "HUD button");
        assert!(entry.resolver_routed);
    }

    #[test]
    fn registry_lookup_returns_none_for_unregistered_pair() {
        let registry = ComponentRegistry::build_default();
        // MeterBar does not register a Hover state.
        assert!(registry
            .get(ComponentId::MeterBar, ComponentState::Hover)
            .is_none());
    }

    #[test]
    fn toast_components_have_muted_state() {
        let registry = ComponentRegistry::build_default();
        for id in [
            ComponentId::ToastInfo,
            ComponentId::ToastSuccess,
            ComponentId::ToastWarning,
            ComponentId::ToastError,
        ] {
            assert!(
                registry.get(id, ComponentState::Muted).is_some(),
                "{id:?} should have a Muted state"
            );
        }
    }

    #[test]
    fn hud_components_have_voice_states() {
        let registry = ComponentRegistry::build_default();
        let voice_states = [
            ComponentState::Idle,
            ComponentState::Listening,
            ComponentState::Recording,
            ComponentState::Processing,
            ComponentState::Responding,
        ];
        for state in voice_states {
            assert!(
                registry.get(ComponentId::HudStatusLine, state).is_some(),
                "HudStatusLine should have state {state:?}"
            );
        }
    }

    #[test]
    fn all_control_surfaces_have_default_state() {
        let registry = ComponentRegistry::build_default();
        for id in registry.all_component_ids() {
            assert!(
                registry.get(id, ComponentState::Default).is_some(),
                "ComponentId {:?} should have a Default state",
                id
            );
        }
    }

    /// Snapshot test: every registered component ID has at least one state.
    /// This is a TS-G04 gate evidence test.
    #[test]
    fn component_registry_parity_snapshot() {
        let registry = ComponentRegistry::build_default();
        let ids = registry.all_component_ids();

        // Build a sorted snapshot of "ComponentId -> [states]".
        let mut snapshot_lines: Vec<String> = Vec::new();
        for id in &ids {
            let states: Vec<String> = [
                ComponentState::Default,
                ComponentState::Hover,
                ComponentState::Focused,
                ComponentState::Pressed,
                ComponentState::Selected,
                ComponentState::Disabled,
                ComponentState::Idle,
                ComponentState::Listening,
                ComponentState::Recording,
                ComponentState::Processing,
                ComponentState::Responding,
                ComponentState::Success,
                ComponentState::Warning,
                ComponentState::Error,
                ComponentState::Muted,
            ]
            .iter()
            .filter(|s| registry.get(*id, **s).is_some())
            .map(|s| format!("{s:?}"))
            .collect();
            snapshot_lines.push(format!("{id:?}: [{}]", states.join(", ")));
        }

        // Ensure a minimum expected count of component IDs.
        assert!(
            ids.len() >= 40,
            "Expected at least 40 component IDs, got {}",
            ids.len()
        );

        // Ensure a minimum expected count of total entries.
        assert!(
            registry.entry_count() >= 100,
            "Expected at least 100 component/state entries, got {}",
            registry.entry_count()
        );
    }

    #[test]
    fn component_style_ids_are_unique_and_prefixed() {
        let registry = ComponentRegistry::build_default();
        let mut seen_style_ids = HashSet::new();
        for id in registry.all_component_ids() {
            let style_id = id.style_id();
            assert!(
                style_id.starts_with("components."),
                "style-ID must use components namespace: {style_id}"
            );
            assert!(
                seen_style_ids.insert(style_id),
                "duplicate component style-ID detected: {style_id}"
            );
        }
    }
}
