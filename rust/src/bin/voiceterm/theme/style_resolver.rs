//! Per-component style resolver that maps `(style_id, state)` pairs to
//! concrete color values, using base theme colors as defaults with optional
//! per-component overrides.

#![allow(
    dead_code,
    reason = "Theme Studio v2 style-resolver APIs are staged; not every entrypoint is wired on all runtime paths yet."
)]

use std::collections::HashMap;

use super::color_value::{ColorValue, ResolvedThemeColors, Rgb};

/// Resolved style for a single component in a specific state.
#[derive(Debug, Clone, PartialEq, Eq)]
pub(crate) struct ResolvedComponentStyle {
    pub(crate) fg: ColorValue,
    pub(crate) bg: ColorValue,
    pub(crate) border: ColorValue,
    pub(crate) bold: bool,
    pub(crate) dim: bool,
}

impl Default for ResolvedComponentStyle {
    fn default() -> Self {
        Self {
            fg: ColorValue::Empty,
            bg: ColorValue::Empty,
            border: ColorValue::Empty,
            bold: false,
            dim: false,
        }
    }
}

/// Individual properties on a resolved component style.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub(crate) enum ComponentStyleProperty {
    Foreground,
    Background,
    Border,
    Bold,
    Dim,
}

impl ComponentStyleProperty {
    pub(crate) const ALL: &'static [Self] = &[
        Self::Foreground,
        Self::Background,
        Self::Border,
        Self::Bold,
        Self::Dim,
    ];

    #[must_use]
    pub(crate) fn label(self) -> &'static str {
        match self {
            Self::Foreground => "Foreground",
            Self::Background => "Background",
            Self::Border => "Border",
            Self::Bold => "Bold",
            Self::Dim => "Dim",
        }
    }

    #[must_use]
    fn is_color(self) -> bool {
        matches!(self, Self::Foreground | Self::Background | Self::Border)
    }

    #[must_use]
    fn color_value(self, style: &ResolvedComponentStyle) -> ColorValue {
        match self {
            Self::Foreground => style.fg,
            Self::Background => style.bg,
            Self::Border => style.border,
            Self::Bold | Self::Dim => ColorValue::Empty,
        }
    }

    fn set_color_value(self, style: &mut ResolvedComponentStyle, value: ColorValue) {
        match self {
            Self::Foreground => style.fg = value,
            Self::Background => style.bg = value,
            Self::Border => style.border = value,
            Self::Bold | Self::Dim => {}
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
enum ComponentColorSlot {
    ThemeDefault,
    Empty,
    Recording,
    Processing,
    Success,
    Warning,
    Error,
    Info,
    Dim,
    Border,
    BgPrimary,
    BgSecondary,
}

impl ComponentColorSlot {
    const ALL: &'static [Self] = &[
        Self::ThemeDefault,
        Self::Empty,
        Self::Recording,
        Self::Processing,
        Self::Success,
        Self::Warning,
        Self::Error,
        Self::Info,
        Self::Dim,
        Self::Border,
        Self::BgPrimary,
        Self::BgSecondary,
    ];

    #[must_use]
    fn label(self) -> &'static str {
        match self {
            Self::ThemeDefault => "theme",
            Self::Empty => "empty",
            Self::Recording => "recording",
            Self::Processing => "processing",
            Self::Success => "success",
            Self::Warning => "warning",
            Self::Error => "error",
            Self::Info => "info",
            Self::Dim => "dim",
            Self::Border => "border",
            Self::BgPrimary => "bg-primary",
            Self::BgSecondary => "bg-secondary",
        }
    }

    #[must_use]
    fn resolve(self, base: &ResolvedThemeColors, default: ColorValue) -> ColorValue {
        match self {
            Self::ThemeDefault => default,
            Self::Empty => ColorValue::Empty,
            Self::Recording => base.recording,
            Self::Processing => base.processing,
            Self::Success => base.success,
            Self::Warning => base.warning,
            Self::Error => base.error,
            Self::Info => base.info,
            Self::Dim => base.dim,
            Self::Border => base.border,
            Self::BgPrimary => base.bg_primary,
            Self::BgSecondary => base.bg_secondary,
        }
    }
}

/// Style resolver that combines base theme colors with per-component overrides.
///
/// Operates in parallel with the existing `style_pack.rs` resolver. Consumer
/// files opt in by calling `resolver.resolve()` for specific components.
#[derive(Debug, Clone)]
pub(crate) struct StyleResolver {
    base: ResolvedThemeColors,
    component_overrides: HashMap<(String, String), ResolvedComponentStyle>,
}

impl StyleResolver {
    /// Create a new resolver with the given base theme colors.
    #[must_use]
    pub(crate) fn new(base: ResolvedThemeColors) -> Self {
        Self {
            base,
            component_overrides: HashMap::new(),
        }
    }

    /// Resolve the style for a component in a given state.
    ///
    /// Returns the override if one exists, otherwise falls back to the
    /// semantic default style for the component/state pair.
    #[must_use]
    pub(crate) fn resolve(&self, style_id: &str, state: &str) -> ResolvedComponentStyle {
        if let Some(override_style) = self
            .component_overrides
            .get(&(style_id.to_string(), state.to_string()))
        {
            return override_style.clone();
        }
        self.default_style_for(style_id, state)
    }

    /// Resolve the semantic default style for a component/state pair.
    #[must_use]
    pub(crate) fn resolve_default(&self, style_id: &str, state: &str) -> ResolvedComponentStyle {
        self.default_style_for(style_id, state)
    }

    /// Set a per-component/state style override.
    pub(crate) fn set_override(
        &mut self,
        style_id: &str,
        state: &str,
        style: ResolvedComponentStyle,
    ) {
        self.component_overrides
            .insert((style_id.to_string(), state.to_string()), style);
    }

    /// Remove a per-component/state style override.
    pub(crate) fn clear_override(&mut self, style_id: &str, state: &str) {
        self.component_overrides
            .remove(&(style_id.to_string(), state.to_string()));
    }

    /// Whether a specific component/state pair has a local override.
    #[must_use]
    pub(crate) fn has_override(&self, style_id: &str, state: &str) -> bool {
        self.component_overrides
            .contains_key(&(style_id.to_string(), state.to_string()))
    }

    /// Cycle a single property on a component/state pair for local preview editing.
    pub(crate) fn cycle_property(
        &mut self,
        style_id: &str,
        state: &str,
        property: ComponentStyleProperty,
    ) -> ResolvedComponentStyle {
        let default_style = self.default_style_for(style_id, state);
        let mut next_style = self.resolve(style_id, state);

        if property.is_color() {
            let default_value = property.color_value(&default_style);
            let current_value = property.color_value(&next_style);
            let current_slot = self.color_slot_for(current_value, default_value);
            let next_slot = advance_color_slot(current_slot);
            property.set_color_value(
                &mut next_style,
                next_slot.resolve(&self.base, default_value),
            );
        } else {
            match property {
                ComponentStyleProperty::Bold => next_style.bold = !next_style.bold,
                ComponentStyleProperty::Dim => next_style.dim = !next_style.dim,
                ComponentStyleProperty::Foreground
                | ComponentStyleProperty::Background
                | ComponentStyleProperty::Border => {}
            }
        }

        self.persist_preview_edit(style_id, state, next_style.clone(), default_style);
        next_style
    }

    /// Human-readable label for the current value of a style property.
    #[must_use]
    pub(crate) fn property_value_label(
        &self,
        style_id: &str,
        state: &str,
        property: ComponentStyleProperty,
    ) -> String {
        let current_style = self.resolve(style_id, state);
        let default_style = self.default_style_for(style_id, state);

        if property.is_color() {
            let current_value = property.color_value(&current_style);
            let default_value = property.color_value(&default_style);
            let slot = self.color_slot_for(current_value, default_value);
            let detail = format_color_value(current_value);
            return format!("{} ({detail})", slot.label());
        }

        let enabled = match property {
            ComponentStyleProperty::Bold => current_style.bold,
            ComponentStyleProperty::Dim => current_style.dim,
            ComponentStyleProperty::Foreground
            | ComponentStyleProperty::Background
            | ComponentStyleProperty::Border => false,
        };
        if enabled {
            "on".to_string()
        } else {
            "off".to_string()
        }
    }

    /// Access the underlying base theme colors.
    #[must_use]
    pub(crate) fn base_colors(&self) -> &ResolvedThemeColors {
        &self.base
    }

    fn persist_preview_edit(
        &mut self,
        style_id: &str,
        state: &str,
        next_style: ResolvedComponentStyle,
        default_style: ResolvedComponentStyle,
    ) {
        if next_style == default_style {
            self.clear_override(style_id, state);
        } else {
            self.set_override(style_id, state, next_style);
        }
    }

    #[must_use]
    fn color_slot_for(&self, current: ColorValue, default: ColorValue) -> ComponentColorSlot {
        ComponentColorSlot::ALL
            .iter()
            .copied()
            .find(|slot| slot.resolve(&self.base, default) == current)
            .unwrap_or(ComponentColorSlot::ThemeDefault)
    }

    /// Determine the default semantic style for a component/state pair.
    ///
    /// Maps well-known component paths to their semantic theme colors.
    #[must_use]
    fn default_style_for(&self, style_id: &str, state: &str) -> ResolvedComponentStyle {
        let Some((category, name)) = parse_style_id(style_id) else {
            return ResolvedComponentStyle::default();
        };

        if let Some(state_style) = self.state_specific_style(category, name, state) {
            return state_style;
        }

        self.base_style_for(category, name)
    }

    #[must_use]
    fn state_specific_style(
        &self,
        category: &str,
        name: &str,
        state: &str,
    ) -> Option<ResolvedComponentStyle> {
        let base = &self.base;

        let style = match (category, name, state) {
            ("toast", _, "muted") => component_style(base.dim, ColorValue::Empty, false, true),
            ("overlay", "frame" | "separator", "focused") => {
                component_style(base.border, base.border, true, false)
            }
            ("overlay", "title", "focused") => component_style(base.info, base.border, true, false),
            ("overlay", "footer", "focused") => {
                component_style(base.info, base.border, false, false)
            }
            (_, _, "hover") => component_style(base.info, ColorValue::Empty, false, false),
            (_, _, "focused" | "selected") => {
                component_style(base.info, ColorValue::Empty, true, false)
            }
            (_, _, "pressed") => component_style(base.processing, ColorValue::Empty, true, false),
            (_, _, "disabled" | "muted") => {
                component_style(base.dim, ColorValue::Empty, false, true)
            }
            (_, _, "idle") => component_style(base.dim, ColorValue::Empty, false, false),
            (_, _, "listening" | "recording") => {
                component_style(base.recording, ColorValue::Empty, false, false)
            }
            (_, _, "processing") => {
                component_style(base.processing, ColorValue::Empty, false, false)
            }
            (_, _, "responding") => component_style(base.info, ColorValue::Empty, false, false),
            (_, _, "success") => component_style(base.success, ColorValue::Empty, false, false),
            (_, _, "warning") => component_style(base.warning, ColorValue::Empty, false, false),
            (_, _, "error") => component_style(base.error, ColorValue::Empty, false, false),
            _ => return None,
        };

        Some(style)
    }

    #[must_use]
    fn base_style_for(&self, category: &str, name: &str) -> ResolvedComponentStyle {
        let base = &self.base;

        match (category, name) {
            ("toast", "info") => component_style(base.info, ColorValue::Empty, false, false),
            ("toast", "success") => component_style(base.success, ColorValue::Empty, false, false),
            ("toast", "warning") => component_style(base.warning, ColorValue::Empty, false, false),
            ("toast", "error") => component_style(base.error, ColorValue::Empty, false, false),
            ("hud", "status_line" | "banner" | "mode") => {
                component_style(base.info, base.border, true, false)
            }
            ("hud", _) => component_style(base.info, ColorValue::Empty, false, false),
            ("overlay", "frame" | "separator") => {
                component_style(base.border, base.border, false, false)
            }
            ("overlay", "title") => component_style(base.info, base.border, true, false),
            ("overlay", "footer") => component_style(base.dim, base.border, false, false),
            ("progress", _) => component_style(base.dim, ColorValue::Empty, false, false),
            ("startup", "splash" | "banner") => {
                component_style(base.info, ColorValue::Empty, true, false)
            }
            ("startup", "tagline") => component_style(base.dim, ColorValue::Empty, false, false),
            ("meter", "peak" | "threshold") => {
                component_style(base.warning, ColorValue::Empty, false, false)
            }
            ("meter", _) => component_style(base.dim, ColorValue::Empty, false, false),
            ("voice", "idle") => component_style(base.dim, ColorValue::Empty, false, false),
            ("voice", "listening") => {
                component_style(base.recording, ColorValue::Empty, false, false)
            }
            ("voice", "processing") => {
                component_style(base.processing, ColorValue::Empty, false, false)
            }
            ("voice", "responding") => component_style(base.info, ColorValue::Empty, false, false),
            (
                "button" | "tab" | "list" | "settings" | "help" | "theme_picker" | "palette"
                | "autocomplete" | "input" | "table" | "tree" | "scrollbar" | "modal" | "popup"
                | "tooltip" | "dashboard",
                _,
            ) => component_style(base.info, ColorValue::Empty, false, false),
            ("icon", _) => component_style(base.info, ColorValue::Empty, false, false),
            _ => ResolvedComponentStyle::default(),
        }
    }
}

fn advance_color_slot(current: ComponentColorSlot) -> ComponentColorSlot {
    let current_idx = ComponentColorSlot::ALL
        .iter()
        .position(|slot| *slot == current)
        .unwrap_or(0);
    let next_idx = (current_idx + 1) % ComponentColorSlot::ALL.len();
    ComponentColorSlot::ALL[next_idx]
}

#[must_use]
fn parse_style_id(style_id: &str) -> Option<(&str, &str)> {
    let parts: Vec<&str> = style_id.split('.').collect();
    match parts.as_slice() {
        ["components", category, name] => Some((*category, *name)),
        _ => None,
    }
}

#[must_use]
fn component_style(
    fg: ColorValue,
    border: ColorValue,
    bold: bool,
    dim: bool,
) -> ResolvedComponentStyle {
    ResolvedComponentStyle {
        fg,
        bg: ColorValue::Empty,
        border,
        bold,
        dim,
    }
}

#[must_use]
pub(crate) fn format_color_value(value: ColorValue) -> String {
    match value {
        ColorValue::Rgb(rgb) => rgb.to_hex(),
        ColorValue::Ansi16(code) => format!("ansi {code}"),
        ColorValue::Reset => "reset".to_string(),
        ColorValue::Empty => "empty".to_string(),
    }
}

// ---------------------------------------------------------------------------
// TOML component override parsing
// ---------------------------------------------------------------------------

/// Parse a TOML component style entry into a `ResolvedComponentStyle`.
///
/// Used by `theme_file.rs` when processing `[components.X.Y]` sections.
pub(crate) fn parse_component_style_entry(
    fg: Option<&str>,
    bg: Option<&str>,
    bold: bool,
    dim: bool,
    palette: &std::collections::HashMap<String, String>,
) -> Result<ResolvedComponentStyle, super::theme_file::ThemeFileError> {
    let resolve_opt =
        |token: Option<&str>| -> Result<ColorValue, super::theme_file::ThemeFileError> {
            match token {
                None => Ok(ColorValue::Empty),
                Some(t) if t.starts_with('#') => {
                    let rgb = Rgb::from_hex(t)
                        .ok_or_else(|| super::theme_file::ThemeFileError::InvalidHex(t.into()))?;
                    Ok(ColorValue::Rgb(rgb))
                }
                Some(t) => {
                    let hex = palette.get(t).ok_or_else(|| {
                        super::theme_file::ThemeFileError::UnknownPaletteRef(t.into())
                    })?;
                    let rgb = Rgb::from_hex(hex).ok_or_else(|| {
                        super::theme_file::ThemeFileError::InvalidHex(hex.clone())
                    })?;
                    Ok(ColorValue::Rgb(rgb))
                }
            }
        };

    Ok(ResolvedComponentStyle {
        fg: resolve_opt(fg)?,
        bg: resolve_opt(bg)?,
        border: ColorValue::Empty,
        bold,
        dim,
    })
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

#[cfg(test)]
mod tests {
    use super::*;
    use crate::theme::{color_value::palette_to_resolved, Theme};

    fn codex_resolver() -> StyleResolver {
        let resolved = palette_to_resolved(&Theme::Codex.colors());
        StyleResolver::new(resolved)
    }

    #[test]
    fn resolver_returns_semantic_defaults_for_toast_error() {
        let resolver = codex_resolver();
        let style = resolver.resolve("components.toast.error", "default");
        let base = palette_to_resolved(&Theme::Codex.colors());
        assert_eq!(style.fg, base.error);
    }

    #[test]
    fn resolver_returns_semantic_defaults_for_hud_recording() {
        let resolver = codex_resolver();
        let style = resolver.resolve("components.hud.status_line", "recording");
        let base = palette_to_resolved(&Theme::Codex.colors());
        assert_eq!(style.fg, base.recording);
    }

    #[test]
    fn resolver_returns_border_defaults_for_overlay_frame() {
        let resolver = codex_resolver();
        let style = resolver.resolve("components.overlay.frame", "default");
        let base = palette_to_resolved(&Theme::Codex.colors());
        assert_eq!(style.fg, base.border);
        assert_eq!(style.border, base.border);
    }

    #[test]
    fn resolver_returns_processing_defaults_for_voice_scene() {
        let resolver = codex_resolver();
        let style = resolver.resolve("components.voice.processing", "default");
        let base = palette_to_resolved(&Theme::Codex.colors());
        assert_eq!(style.fg, base.processing);
    }

    #[test]
    fn override_takes_precedence() {
        let mut resolver = codex_resolver();
        let custom = ResolvedComponentStyle {
            fg: ColorValue::Rgb(Rgb { r: 255, g: 0, b: 0 }),
            bg: ColorValue::Empty,
            border: ColorValue::Empty,
            bold: true,
            dim: false,
        };
        resolver.set_override("components.toast.error", "default", custom.clone());

        let style = resolver.resolve("components.toast.error", "default");
        assert_eq!(style, custom);
    }

    #[test]
    fn clear_override_reverts_to_default() {
        let mut resolver = codex_resolver();
        let custom = ResolvedComponentStyle {
            fg: ColorValue::Rgb(Rgb { r: 255, g: 0, b: 0 }),
            ..ResolvedComponentStyle::default()
        };
        resolver.set_override("components.toast.error", "default", custom);
        resolver.clear_override("components.toast.error", "default");

        let style = resolver.resolve("components.toast.error", "default");
        let base = palette_to_resolved(&Theme::Codex.colors());
        assert_eq!(style.fg, base.error);
    }

    #[test]
    fn cycle_property_tracks_local_preview_override() {
        let mut resolver = codex_resolver();
        let default_style = resolver.resolve_default("components.toast.error", "default");
        let edited = resolver.cycle_property(
            "components.toast.error",
            "default",
            ComponentStyleProperty::Foreground,
        );

        assert_ne!(edited.fg, default_style.fg);
        assert!(resolver.has_override("components.toast.error", "default"));
    }

    #[test]
    fn cycle_property_toggles_bold_flag() {
        let mut resolver = codex_resolver();
        let edited = resolver.cycle_property(
            "components.overlay.title",
            "default",
            ComponentStyleProperty::Bold,
        );

        assert!(
            resolver
                .resolve_default("components.overlay.title", "default")
                .bold
        );
        assert!(!edited.bold);
        assert!(resolver.has_override("components.overlay.title", "default"));
    }

    #[test]
    fn property_value_label_uses_theme_label_for_default_color() {
        let resolver = codex_resolver();
        let label = resolver.property_value_label(
            "components.toast.error",
            "default",
            ComponentStyleProperty::Foreground,
        );

        assert!(label.starts_with("theme"));
    }

    #[test]
    fn resolver_returns_dim_for_disabled_state() {
        let resolver = codex_resolver();
        let style = resolver.resolve("components.button.hud", "disabled");
        let base = palette_to_resolved(&Theme::Codex.colors());
        assert_eq!(style.fg, base.dim);
        assert!(style.dim);
    }

    #[test]
    fn resolver_returns_default_for_unknown_component() {
        let resolver = codex_resolver();
        let style = resolver.resolve("components.unknown.widget", "default");
        assert_eq!(style, ResolvedComponentStyle::default());
    }

    #[test]
    fn parse_component_style_entry_with_hex() {
        let palette = std::collections::HashMap::new();
        let style = match parse_component_style_entry(Some("#ff5555"), None, true, false, &palette)
        {
            Ok(style) => style,
            Err(err) => panic!("failed to parse style entry with hex: {err}"),
        };
        assert_eq!(
            style.fg,
            ColorValue::Rgb(Rgb {
                r: 255,
                g: 85,
                b: 85
            })
        );
        assert!(style.bold);
    }

    #[test]
    fn parse_component_style_entry_with_palette_ref() {
        let mut palette = std::collections::HashMap::new();
        palette.insert("myred".to_string(), "#ff0000".to_string());
        let style = match parse_component_style_entry(Some("myred"), None, false, false, &palette) {
            Ok(style) => style,
            Err(err) => panic!("failed to parse style entry with palette ref: {err}"),
        };
        assert_eq!(style.fg, ColorValue::Rgb(Rgb { r: 255, g: 0, b: 0 }));
    }
}
