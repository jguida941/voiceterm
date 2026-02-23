pub(super) fn cycle_runtime_glyph_set_override(
    current: Option<crate::theme::RuntimeGlyphSetOverride>,
    direction: i32,
) -> Option<crate::theme::RuntimeGlyphSetOverride> {
    let values = [
        None,
        Some(crate::theme::RuntimeGlyphSetOverride::Unicode),
        Some(crate::theme::RuntimeGlyphSetOverride::Ascii),
    ];
    let current_idx = values
        .iter()
        .position(|value| *value == current)
        .unwrap_or(0);
    let next_idx = cycle_override_index(current_idx, values.len(), direction);
    values[next_idx]
}

pub(super) fn cycle_runtime_indicator_set_override(
    current: Option<crate::theme::RuntimeIndicatorSetOverride>,
    direction: i32,
) -> Option<crate::theme::RuntimeIndicatorSetOverride> {
    let values = [
        None,
        Some(crate::theme::RuntimeIndicatorSetOverride::Ascii),
        Some(crate::theme::RuntimeIndicatorSetOverride::Dot),
        Some(crate::theme::RuntimeIndicatorSetOverride::Diamond),
    ];
    let current_idx = values
        .iter()
        .position(|value| *value == current)
        .unwrap_or(0);
    let next_idx = cycle_override_index(current_idx, values.len(), direction);
    values[next_idx]
}

pub(super) fn cycle_runtime_border_style_override(
    current: Option<crate::theme::RuntimeBorderStyleOverride>,
    direction: i32,
) -> Option<crate::theme::RuntimeBorderStyleOverride> {
    let values = [
        None,
        Some(crate::theme::RuntimeBorderStyleOverride::Single),
        Some(crate::theme::RuntimeBorderStyleOverride::Rounded),
        Some(crate::theme::RuntimeBorderStyleOverride::Double),
        Some(crate::theme::RuntimeBorderStyleOverride::Heavy),
        Some(crate::theme::RuntimeBorderStyleOverride::None),
    ];
    let current_idx = values
        .iter()
        .position(|value| *value == current)
        .unwrap_or(0);
    let next_idx = cycle_override_index(current_idx, values.len(), direction);
    values[next_idx]
}

pub(super) fn cycle_runtime_progress_style_override(
    current: Option<crate::theme::RuntimeProgressStyleOverride>,
    direction: i32,
) -> Option<crate::theme::RuntimeProgressStyleOverride> {
    let values = [
        None,
        Some(crate::theme::RuntimeProgressStyleOverride::Braille),
        Some(crate::theme::RuntimeProgressStyleOverride::Dots),
        Some(crate::theme::RuntimeProgressStyleOverride::Line),
        Some(crate::theme::RuntimeProgressStyleOverride::Block),
    ];
    let current_idx = values
        .iter()
        .position(|value| *value == current)
        .unwrap_or(0);
    let next_idx = cycle_override_index(current_idx, values.len(), direction);
    values[next_idx]
}

pub(super) fn cycle_runtime_progress_bar_family_override(
    current: Option<crate::theme::RuntimeProgressBarFamilyOverride>,
    direction: i32,
) -> Option<crate::theme::RuntimeProgressBarFamilyOverride> {
    let values = [
        None,
        Some(crate::theme::RuntimeProgressBarFamilyOverride::Bar),
        Some(crate::theme::RuntimeProgressBarFamilyOverride::Compact),
        Some(crate::theme::RuntimeProgressBarFamilyOverride::Blocks),
        Some(crate::theme::RuntimeProgressBarFamilyOverride::Braille),
    ];
    let current_idx = values
        .iter()
        .position(|value| *value == current)
        .unwrap_or(0);
    let next_idx = cycle_override_index(current_idx, values.len(), direction);
    values[next_idx]
}

pub(super) fn cycle_runtime_voice_scene_style_override(
    current: Option<crate::theme::RuntimeVoiceSceneStyleOverride>,
    direction: i32,
) -> Option<crate::theme::RuntimeVoiceSceneStyleOverride> {
    let values = [
        None,
        Some(crate::theme::RuntimeVoiceSceneStyleOverride::Pulse),
        Some(crate::theme::RuntimeVoiceSceneStyleOverride::Static),
        Some(crate::theme::RuntimeVoiceSceneStyleOverride::Minimal),
    ];
    let current_idx = values
        .iter()
        .position(|value| *value == current)
        .unwrap_or(0);
    let next_idx = cycle_override_index(current_idx, values.len(), direction);
    values[next_idx]
}

pub(super) fn cycle_runtime_toast_position_override(
    current: Option<crate::theme::RuntimeToastPositionOverride>,
    direction: i32,
) -> Option<crate::theme::RuntimeToastPositionOverride> {
    let values = [
        None,
        Some(crate::theme::RuntimeToastPositionOverride::TopRight),
        Some(crate::theme::RuntimeToastPositionOverride::BottomRight),
        Some(crate::theme::RuntimeToastPositionOverride::TopCenter),
        Some(crate::theme::RuntimeToastPositionOverride::BottomCenter),
    ];
    let current_idx = values
        .iter()
        .position(|value| *value == current)
        .unwrap_or(0);
    let next_idx = cycle_override_index(current_idx, values.len(), direction);
    values[next_idx]
}

pub(super) fn cycle_runtime_startup_style_override(
    current: Option<crate::theme::RuntimeStartupStyleOverride>,
    direction: i32,
) -> Option<crate::theme::RuntimeStartupStyleOverride> {
    let values = [
        None,
        Some(crate::theme::RuntimeStartupStyleOverride::Full),
        Some(crate::theme::RuntimeStartupStyleOverride::Minimal),
        Some(crate::theme::RuntimeStartupStyleOverride::Hidden),
    ];
    let current_idx = values
        .iter()
        .position(|value| *value == current)
        .unwrap_or(0);
    let next_idx = cycle_override_index(current_idx, values.len(), direction);
    values[next_idx]
}

pub(super) fn cycle_runtime_toast_severity_mode_override(
    current: Option<crate::theme::RuntimeToastSeverityModeOverride>,
    direction: i32,
) -> Option<crate::theme::RuntimeToastSeverityModeOverride> {
    let values = [
        None,
        Some(crate::theme::RuntimeToastSeverityModeOverride::Icon),
        Some(crate::theme::RuntimeToastSeverityModeOverride::Label),
        Some(crate::theme::RuntimeToastSeverityModeOverride::IconAndLabel),
    ];
    let current_idx = values
        .iter()
        .position(|value| *value == current)
        .unwrap_or(0);
    let next_idx = cycle_override_index(current_idx, values.len(), direction);
    values[next_idx]
}

pub(super) fn cycle_runtime_banner_style_override(
    current: Option<crate::theme::RuntimeBannerStyleOverride>,
    direction: i32,
) -> Option<crate::theme::RuntimeBannerStyleOverride> {
    let values = [
        None,
        Some(crate::theme::RuntimeBannerStyleOverride::Full),
        Some(crate::theme::RuntimeBannerStyleOverride::Compact),
        Some(crate::theme::RuntimeBannerStyleOverride::Minimal),
        Some(crate::theme::RuntimeBannerStyleOverride::Hidden),
    ];
    let current_idx = values
        .iter()
        .position(|value| *value == current)
        .unwrap_or(0);
    let next_idx = cycle_override_index(current_idx, values.len(), direction);
    values[next_idx]
}

fn cycle_override_index(current_idx: usize, len: usize, direction: i32) -> usize {
    if len == 0 {
        return 0;
    }
    if direction < 0 {
        if current_idx == 0 {
            len - 1
        } else {
            current_idx - 1
        }
    } else {
        (current_idx + 1) % len
    }
}
