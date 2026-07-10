#![allow(
    dead_code,
    reason = "Shared status-line test helpers are imported selectively by sibling test modules."
)]

use crate::status_line::mode_indicator::recording_indicator_color;
use crate::status_line::right_panel::{meter_level_color, scene_should_animate};
use crate::theme::{Theme, VoiceSceneStyle};

pub(super) fn assert_recording_indicator_color_pulses_with_theme_palette() {
    for theme in [
        Theme::Ansi,
        Theme::Claude,
        Theme::Codex,
        Theme::TokyoNight,
        Theme::Coral,
        Theme::ChatGpt,
    ] {
        let colors = theme.colors();
        let pulse = recording_indicator_color(&colors);
        assert!(pulse == colors.recording || pulse == colors.dim);
    }
}

pub(super) fn assert_meter_level_color_boundaries_are_exclusive() {
    let colors = Theme::Coral.colors();

    assert_eq!(meter_level_color(-31.0, &colors), colors.success);
    assert_eq!(meter_level_color(-30.0, &colors), colors.warning);
    assert_eq!(meter_level_color(-19.0, &colors), colors.warning);
    assert_eq!(meter_level_color(-18.0, &colors), colors.error);
}

pub(super) fn assert_heartbeat_helpers_cover_truth_table() {
    assert!(scene_should_animate(VoiceSceneStyle::Theme, false, false));
    assert!(scene_should_animate(VoiceSceneStyle::Theme, false, true));
    assert!(!scene_should_animate(VoiceSceneStyle::Theme, true, false));
    assert!(scene_should_animate(VoiceSceneStyle::Theme, true, true));
    assert!(scene_should_animate(VoiceSceneStyle::Pulse, true, false));
    assert!(!scene_should_animate(VoiceSceneStyle::Static, false, true));
}
