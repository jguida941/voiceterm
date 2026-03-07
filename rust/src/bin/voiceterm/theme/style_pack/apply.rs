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

macro_rules! impl_runtime_override_conversion {
    ($runtime:ty => $schema:ty { $($variant:ident),+ $(,)? }) => {
        impl From<$runtime> for $schema {
            fn from(value: $runtime) -> Self {
                match value {
                    $(
                        <$runtime>::$variant => <$schema>::$variant,
                    )+
                }
            }
        }
    };
}

impl_runtime_override_conversion!(
    RuntimeBorderStyleOverride => BorderStyleOverride { Single, Rounded, Double, Heavy, None }
);
impl_runtime_override_conversion!(RuntimeGlyphSetOverride => GlyphSetOverride { Unicode, Ascii });
impl_runtime_override_conversion!(
    RuntimeIndicatorSetOverride => IndicatorSetOverride { Ascii, Dot, Diamond }
);
impl_runtime_override_conversion!(
    RuntimeToastPositionOverride => ToastPositionOverride {
        TopRight,
        BottomRight,
        TopCenter,
        BottomCenter
    }
);
impl_runtime_override_conversion!(
    RuntimeStartupStyleOverride => StartupStyleOverride { Full, Minimal, Hidden }
);
impl_runtime_override_conversion!(
    RuntimeProgressStyleOverride => ProgressStyleOverride { Braille, Dots, Line, Block }
);
impl_runtime_override_conversion!(
    RuntimeToastSeverityModeOverride => ToastSeverityMode { Icon, Label, IconAndLabel }
);
impl_runtime_override_conversion!(
    RuntimeBannerStyleOverride => BannerStyleOverride { Full, Compact, Minimal, Hidden }
);
impl_runtime_override_conversion!(
    RuntimeProgressBarFamilyOverride => SchemaProgressBarFamily {
        Bar,
        Compact,
        Blocks,
        Braille
    }
);
impl_runtime_override_conversion!(
    RuntimeVoiceSceneStyleOverride => SchemaVoiceSceneStyleOverride { Pulse, Static, Minimal }
);

fn apply_runtime_override<Runtime, Schema>(
    target: &mut Option<Schema>,
    override_value: Option<Runtime>,
) where
    Runtime: Into<Schema>,
{
    if let Some(override_value) = override_value {
        *target = Some(override_value.into());
    }
}

pub(crate) fn apply_runtime_style_pack_overrides(
    pack: &mut StylePack,
    overrides: RuntimeStylePackOverrides,
) {
    apply_runtime_override(
        &mut pack.border_style_override,
        overrides.border_style_override,
    );
    apply_runtime_override(&mut pack.glyph_set_override, overrides.glyph_set_override);
    apply_runtime_override(
        &mut pack.indicator_set_override,
        overrides.indicator_set_override,
    );
    apply_runtime_override(
        &mut pack.surface_overrides.toast_position,
        overrides.toast_position_override,
    );
    apply_runtime_override(
        &mut pack.surface_overrides.startup_style,
        overrides.startup_style_override,
    );
    apply_runtime_override(
        &mut pack.surface_overrides.progress_style,
        overrides.progress_style_override,
    );
    apply_runtime_override(
        &mut pack.component_overrides.toast_severity_mode,
        overrides.toast_severity_mode_override,
    );
    apply_runtime_override(
        &mut pack.component_overrides.banner_style,
        overrides.banner_style_override,
    );
    apply_runtime_override(
        &mut pack.component_overrides.progress_bar_family,
        overrides.progress_bar_family_override,
    );
    apply_runtime_override(
        &mut pack.surface_overrides.voice_scene_style,
        overrides.voice_scene_style_override,
    );
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
