/// Runtime glyph-profile override applied on top of resolved style-pack payloads.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub(crate) enum RuntimeGlyphSetOverride {
    Unicode,
    Ascii,
}

/// Runtime indicator-profile override applied on top of resolved style-pack payloads.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub(crate) enum RuntimeIndicatorSetOverride {
    Ascii,
    Dot,
    Diamond,
}

/// Runtime progress-spinner override applied on top of resolved style-pack payloads.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub(crate) enum RuntimeProgressStyleOverride {
    Braille,
    Dots,
    Line,
    Block,
}

/// Runtime progress-bar-family override applied on top of resolved style-pack payloads.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub(crate) enum RuntimeProgressBarFamilyOverride {
    Bar,
    Compact,
    Blocks,
    Braille,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub(crate) enum RuntimeToastPositionOverride {
    TopRight,
    BottomRight,
    TopCenter,
    BottomCenter,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub(crate) enum RuntimeStartupStyleOverride {
    Full,
    Minimal,
    Hidden,
}

/// Runtime voice-scene override applied on top of resolved style-pack payloads.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub(crate) enum RuntimeVoiceSceneStyleOverride {
    Pulse,
    Static,
    Minimal,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub(crate) enum RuntimeToastSeverityModeOverride {
    Icon,
    Label,
    IconAndLabel,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub(crate) enum RuntimeBannerStyleOverride {
    Full,
    Compact,
    Minimal,
    Hidden,
}

/// Runtime border-style override applied on top of resolved style-pack payloads.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub(crate) enum RuntimeBorderStyleOverride {
    Single,
    Rounded,
    Double,
    Heavy,
    None,
}

/// Runtime Theme Studio overrides applied after style-pack payload resolution.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
pub(crate) struct RuntimeStylePackOverrides {
    pub(crate) border_style_override: Option<RuntimeBorderStyleOverride>,
    pub(crate) glyph_set_override: Option<RuntimeGlyphSetOverride>,
    pub(crate) indicator_set_override: Option<RuntimeIndicatorSetOverride>,
    pub(crate) toast_position_override: Option<RuntimeToastPositionOverride>,
    pub(crate) startup_style_override: Option<RuntimeStartupStyleOverride>,
    pub(crate) progress_style_override: Option<RuntimeProgressStyleOverride>,
    pub(crate) toast_severity_mode_override: Option<RuntimeToastSeverityModeOverride>,
    pub(crate) banner_style_override: Option<RuntimeBannerStyleOverride>,
    pub(crate) progress_bar_family_override: Option<RuntimeProgressBarFamilyOverride>,
    pub(crate) voice_scene_style_override: Option<RuntimeVoiceSceneStyleOverride>,
}
