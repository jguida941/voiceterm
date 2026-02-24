//! Per-component style resolver that maps (ComponentId, ComponentState) pairs
//! to concrete color values, using base theme colors as defaults with optional
//! per-component overrides.

#![allow(dead_code)]

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

/// Style resolver that combines base theme colors with per-component overrides.
///
/// Operates in parallel with the existing `style_pack.rs` resolver — consumer
/// files opt in by calling `resolver.resolve()` for specific components.
#[derive(Debug)]
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

    /// Determine the default semantic style for a component/state pair.
    ///
    /// Maps well-known component paths to their semantic theme colors.
    #[must_use]
    fn default_style_for(&self, style_id: &str, state: &str) -> ResolvedComponentStyle {
        let base = &self.base;

        // Extract the component category and specific component from the style-ID.
        // Format: "components.{category}.{name}"
        let parts: Vec<&str> = style_id.split('.').collect();
        let (category, name) = match parts.as_slice() {
            [_, cat, name] => (*cat, *name),
            _ => return ResolvedComponentStyle::default(),
        };

        match (category, name, state) {
            // Toast components map to their semantic color.
            ("toast", "error", _) => ResolvedComponentStyle {
                fg: base.error,
                ..ResolvedComponentStyle::default()
            },
            ("toast", "warning", _) => ResolvedComponentStyle {
                fg: base.warning,
                ..ResolvedComponentStyle::default()
            },
            ("toast", "success", _) => ResolvedComponentStyle {
                fg: base.success,
                ..ResolvedComponentStyle::default()
            },
            ("toast", "info", _) => ResolvedComponentStyle {
                fg: base.info,
                ..ResolvedComponentStyle::default()
            },

            // HUD components map to voice-state colors.
            ("hud", _, "recording") => ResolvedComponentStyle {
                fg: base.recording,
                ..ResolvedComponentStyle::default()
            },
            ("hud", _, "processing") => ResolvedComponentStyle {
                fg: base.processing,
                ..ResolvedComponentStyle::default()
            },
            ("hud", _, "responding") => ResolvedComponentStyle {
                fg: base.info,
                ..ResolvedComponentStyle::default()
            },
            ("hud", _, "idle") => ResolvedComponentStyle {
                fg: base.dim,
                ..ResolvedComponentStyle::default()
            },

            // Overlay chrome.
            ("overlay", "frame" | "separator", _) => ResolvedComponentStyle {
                fg: base.border,
                ..ResolvedComponentStyle::default()
            },
            ("overlay", "title", _) => ResolvedComponentStyle {
                fg: base.info,
                bold: true,
                ..ResolvedComponentStyle::default()
            },

            // Progress components.
            ("progress", _, "processing") => ResolvedComponentStyle {
                fg: base.processing,
                ..ResolvedComponentStyle::default()
            },
            ("progress", _, _) => ResolvedComponentStyle {
                fg: base.dim,
                ..ResolvedComponentStyle::default()
            },

            // Voice scenes.
            ("voice", "listening", _) => ResolvedComponentStyle {
                fg: base.recording,
                ..ResolvedComponentStyle::default()
            },
            ("voice", "processing", _) => ResolvedComponentStyle {
                fg: base.processing,
                ..ResolvedComponentStyle::default()
            },
            ("voice", "responding", _) => ResolvedComponentStyle {
                fg: base.info,
                ..ResolvedComponentStyle::default()
            },
            ("voice", "idle", _) => ResolvedComponentStyle {
                fg: base.dim,
                ..ResolvedComponentStyle::default()
            },

            // Default: use dim for non-focused, info for focused/selected.
            (_, _, "focused" | "selected") => ResolvedComponentStyle {
                fg: base.info,
                ..ResolvedComponentStyle::default()
            },
            (_, _, "disabled" | "muted") => ResolvedComponentStyle {
                fg: base.dim,
                dim: true,
                ..ResolvedComponentStyle::default()
            },

            // Catch-all default.
            _ => ResolvedComponentStyle::default(),
        }
    }

    /// Access the underlying base theme colors.
    #[must_use]
    pub(crate) fn base_colors(&self) -> &ResolvedThemeColors {
        &self.base
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
    fn resolver_returns_semantic_defaults_for_toast_success() {
        let resolver = codex_resolver();
        let style = resolver.resolve("components.toast.success", "default");
        let base = palette_to_resolved(&Theme::Codex.colors());
        assert_eq!(style.fg, base.success);
    }

    #[test]
    fn resolver_returns_semantic_defaults_for_hud_recording() {
        let resolver = codex_resolver();
        let style = resolver.resolve("components.hud.status_line", "recording");
        let base = palette_to_resolved(&Theme::Codex.colors());
        assert_eq!(style.fg, base.recording);
    }

    #[test]
    fn resolver_returns_semantic_defaults_for_hud_processing() {
        let resolver = codex_resolver();
        let style = resolver.resolve("components.hud.status_line", "processing");
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
    fn resolver_returns_dim_for_disabled_state() {
        let resolver = codex_resolver();
        let style = resolver.resolve("components.button.hud", "disabled");
        let base = palette_to_resolved(&Theme::Codex.colors());
        assert_eq!(style.fg, base.dim);
        assert!(style.dim);
    }

    #[test]
    fn resolver_returns_info_for_focused_state() {
        let resolver = codex_resolver();
        let style = resolver.resolve("components.button.hud", "focused");
        let base = palette_to_resolved(&Theme::Codex.colors());
        assert_eq!(style.fg, base.info);
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
