//! Override application — maps runtime override enums to schema overrides
//! and applies them to `StylePack` and `ThemeColors`.

use super::super::runtime_overrides::{
    RuntimeBannerStyleOverride, RuntimeBorderStyleOverride, RuntimeGlyphSetOverride,
    RuntimeIndicatorSetOverride, RuntimeProgressBarFamilyOverride, RuntimeProgressStyleOverride,
    RuntimeStartupStyleOverride, RuntimeStylePackOverrides, RuntimeToastPositionOverride,
    RuntimeToastSeverityModeOverride, RuntimeVoiceSceneStyleOverride,
};
use super::super::style_schema::{
    BannerStyleOverride, BorderStyleOverride, GlyphSetOverride, IndicatorSetOverride,
    ProgressBarFamily as SchemaProgressBarFamily, ProgressStyleOverride, StartupStyleOverride,
    ToastPositionOverride, ToastSeverityMode,
    VoiceSceneStyleOverride as SchemaVoiceSceneStyleOverride,
};
use super::super::{
    BorderSet, GlyphSet, ProgressBarFamily, SpinnerStyle, ThemeColors, VoiceSceneStyle,
    BORDER_DOUBLE, BORDER_HEAVY, BORDER_NONE, BORDER_ROUNDED, BORDER_SINGLE,
};
use super::StylePack;

pub(crate) fn apply_runtime_style_pack_overrides(
    pack: &mut StylePack,
    overrides: RuntimeStylePackOverrides,
) {
    if let Some(border_override) = overrides.border_style_override {
        pack.border_style_override = Some(match border_override {
            RuntimeBorderStyleOverride::Single => BorderStyleOverride::Single,
            RuntimeBorderStyleOverride::Rounded => BorderStyleOverride::Rounded,
            RuntimeBorderStyleOverride::Double => BorderStyleOverride::Double,
            RuntimeBorderStyleOverride::Heavy => BorderStyleOverride::Heavy,
            RuntimeBorderStyleOverride::None => BorderStyleOverride::None,
        });
    }
    if let Some(glyph_override) = overrides.glyph_set_override {
        pack.glyph_set_override = Some(match glyph_override {
            RuntimeGlyphSetOverride::Unicode => GlyphSetOverride::Unicode,
            RuntimeGlyphSetOverride::Ascii => GlyphSetOverride::Ascii,
        });
    }
    if let Some(indicator_override) = overrides.indicator_set_override {
        pack.indicator_set_override = Some(match indicator_override {
            RuntimeIndicatorSetOverride::Ascii => IndicatorSetOverride::Ascii,
            RuntimeIndicatorSetOverride::Dot => IndicatorSetOverride::Dot,
            RuntimeIndicatorSetOverride::Diamond => IndicatorSetOverride::Diamond,
        });
    }
    if let Some(position_override) = overrides.toast_position_override {
        pack.surface_overrides.toast_position = Some(match position_override {
            RuntimeToastPositionOverride::TopRight => ToastPositionOverride::TopRight,
            RuntimeToastPositionOverride::BottomRight => ToastPositionOverride::BottomRight,
            RuntimeToastPositionOverride::TopCenter => ToastPositionOverride::TopCenter,
            RuntimeToastPositionOverride::BottomCenter => ToastPositionOverride::BottomCenter,
        });
    }
    if let Some(startup_override) = overrides.startup_style_override {
        pack.surface_overrides.startup_style = Some(match startup_override {
            RuntimeStartupStyleOverride::Full => StartupStyleOverride::Full,
            RuntimeStartupStyleOverride::Minimal => StartupStyleOverride::Minimal,
            RuntimeStartupStyleOverride::Hidden => StartupStyleOverride::Hidden,
        });
    }
    if let Some(progress_override) = overrides.progress_style_override {
        pack.surface_overrides.progress_style = Some(match progress_override {
            RuntimeProgressStyleOverride::Braille => ProgressStyleOverride::Braille,
            RuntimeProgressStyleOverride::Dots => ProgressStyleOverride::Dots,
            RuntimeProgressStyleOverride::Line => ProgressStyleOverride::Line,
            RuntimeProgressStyleOverride::Block => ProgressStyleOverride::Block,
        });
    }
    if let Some(toast_severity_override) = overrides.toast_severity_mode_override {
        pack.component_overrides.toast_severity_mode = Some(match toast_severity_override {
            RuntimeToastSeverityModeOverride::Icon => ToastSeverityMode::Icon,
            RuntimeToastSeverityModeOverride::Label => ToastSeverityMode::Label,
            RuntimeToastSeverityModeOverride::IconAndLabel => ToastSeverityMode::IconAndLabel,
        });
    }
    if let Some(banner_override) = overrides.banner_style_override {
        pack.component_overrides.banner_style = Some(match banner_override {
            RuntimeBannerStyleOverride::Full => BannerStyleOverride::Full,
            RuntimeBannerStyleOverride::Compact => BannerStyleOverride::Compact,
            RuntimeBannerStyleOverride::Minimal => BannerStyleOverride::Minimal,
            RuntimeBannerStyleOverride::Hidden => BannerStyleOverride::Hidden,
        });
    }
    if let Some(progress_bar_override) = overrides.progress_bar_family_override {
        pack.component_overrides.progress_bar_family = Some(match progress_bar_override {
            RuntimeProgressBarFamilyOverride::Bar => SchemaProgressBarFamily::Bar,
            RuntimeProgressBarFamilyOverride::Compact => SchemaProgressBarFamily::Compact,
            RuntimeProgressBarFamilyOverride::Blocks => SchemaProgressBarFamily::Blocks,
            RuntimeProgressBarFamilyOverride::Braille => SchemaProgressBarFamily::Braille,
        });
    }
    if let Some(scene_override) = overrides.voice_scene_style_override {
        pack.surface_overrides.voice_scene_style = Some(match scene_override {
            RuntimeVoiceSceneStyleOverride::Pulse => SchemaVoiceSceneStyleOverride::Pulse,
            RuntimeVoiceSceneStyleOverride::Static => SchemaVoiceSceneStyleOverride::Static,
            RuntimeVoiceSceneStyleOverride::Minimal => SchemaVoiceSceneStyleOverride::Minimal,
        });
    }
}

#[must_use]
pub(crate) fn resolve_border_set(
    base: BorderSet,
    override_value: Option<BorderStyleOverride>,
) -> BorderSet {
    match override_value {
        None | Some(BorderStyleOverride::Theme) => base,
        Some(BorderStyleOverride::Single) => BORDER_SINGLE,
        Some(BorderStyleOverride::Rounded) => BORDER_ROUNDED,
        Some(BorderStyleOverride::Double) => BORDER_DOUBLE,
        Some(BorderStyleOverride::Heavy) => BORDER_HEAVY,
        Some(BorderStyleOverride::None) => BORDER_NONE,
    }
}

pub(crate) fn apply_border_style_override(
    colors: &mut ThemeColors,
    override_value: Option<BorderStyleOverride>,
) {
    colors.borders = resolve_border_set(colors.borders, override_value);
}

pub(crate) fn apply_indicator_set_override(
    colors: &mut ThemeColors,
    override_value: Option<IndicatorSetOverride>,
) {
    let Some(override_value) = override_value else {
        return;
    };
    let (rec, auto, manual, idle, processing, responding) = match override_value {
        IndicatorSetOverride::Theme => (
            colors.indicator_rec,
            colors.indicator_auto,
            colors.indicator_manual,
            colors.indicator_idle,
            colors.indicator_processing,
            colors.indicator_responding,
        ),
        IndicatorSetOverride::Ascii => ("*", "@", ">", "-", "~", ">"),
        IndicatorSetOverride::Dot => ("●", "◎", "▶", "○", "◐", "↺"),
        IndicatorSetOverride::Diamond => ("◆", "◇", "▸", "·", "◈", "▸"),
    };
    colors.indicator_rec = rec;
    colors.indicator_auto = auto;
    colors.indicator_manual = manual;
    colors.indicator_idle = idle;
    colors.indicator_processing = processing;
    colors.indicator_responding = responding;
}

pub(crate) fn apply_glyph_set_override(
    colors: &mut ThemeColors,
    override_value: Option<GlyphSetOverride>,
) {
    let Some(override_value) = override_value else {
        return;
    };
    colors.glyph_set = match override_value {
        GlyphSetOverride::Theme => colors.glyph_set,
        GlyphSetOverride::Unicode => GlyphSet::Unicode,
        GlyphSetOverride::Ascii => GlyphSet::Ascii,
    };
}

pub(crate) fn apply_progress_style_override(
    colors: &mut ThemeColors,
    override_value: Option<ProgressStyleOverride>,
) {
    let Some(override_value) = override_value else {
        return;
    };
    colors.spinner_style = match override_value {
        ProgressStyleOverride::Theme => colors.spinner_style,
        ProgressStyleOverride::Braille => SpinnerStyle::Braille,
        ProgressStyleOverride::Dots => SpinnerStyle::Dots,
        ProgressStyleOverride::Line => SpinnerStyle::Line,
        ProgressStyleOverride::Block => SpinnerStyle::Block,
    };
}

pub(crate) fn apply_progress_bar_family_override(
    colors: &mut ThemeColors,
    override_value: Option<SchemaProgressBarFamily>,
) {
    let Some(override_value) = override_value else {
        return;
    };
    colors.progress_bar_family = match override_value {
        SchemaProgressBarFamily::Theme => colors.progress_bar_family,
        SchemaProgressBarFamily::Bar => ProgressBarFamily::Bar,
        SchemaProgressBarFamily::Compact => ProgressBarFamily::Compact,
        SchemaProgressBarFamily::Blocks => ProgressBarFamily::Blocks,
        SchemaProgressBarFamily::Braille => ProgressBarFamily::Braille,
    };
}

pub(crate) fn apply_voice_scene_style_override(
    colors: &mut ThemeColors,
    override_value: Option<SchemaVoiceSceneStyleOverride>,
) {
    let Some(override_value) = override_value else {
        return;
    };
    colors.voice_scene_style = match override_value {
        SchemaVoiceSceneStyleOverride::Theme => colors.voice_scene_style,
        SchemaVoiceSceneStyleOverride::Pulse => VoiceSceneStyle::Pulse,
        SchemaVoiceSceneStyleOverride::Static => VoiceSceneStyle::Static,
        SchemaVoiceSceneStyleOverride::Minimal => VoiceSceneStyle::Minimal,
    };
}
