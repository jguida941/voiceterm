//! Settings item metadata so menus render and dispatch actions from one schema.

use crate::config::{HudBorderStyle, HudRightPanel, HudStyle, LatencyDisplayMode, VoiceSendMode};
use crate::status_line::Pipeline;
use crate::theme::Theme;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum SettingsItem {
    AutoVoice,
    WakeWord,
    WakeSensitivity,
    WakeCooldown,
    SendMode,
    ImageMode,
    Macros,
    Sensitivity,
    Theme,
    HudStyle,
    HudBorders,
    HudPanel,
    HudAnimate,
    Latency,
    Mouse,
    Backend,
    Pipeline,
    Close,
    Quit,
}

pub const SETTINGS_ITEMS: &[SettingsItem] = &[
    SettingsItem::AutoVoice,
    SettingsItem::WakeWord,
    SettingsItem::WakeSensitivity,
    SettingsItem::WakeCooldown,
    SettingsItem::SendMode,
    SettingsItem::ImageMode,
    SettingsItem::Macros,
    SettingsItem::Sensitivity,
    SettingsItem::Latency,
    SettingsItem::Mouse,
    SettingsItem::Backend,
    SettingsItem::Pipeline,
    SettingsItem::Close,
    SettingsItem::Quit,
];

pub const SETTINGS_OPTION_START_ROW: usize = 4;

pub struct SettingsView<'a> {
    pub selected: usize,
    pub auto_voice_enabled: bool,
    pub wake_word_enabled: bool,
    pub wake_word_sensitivity: f32,
    pub wake_word_cooldown_ms: u64,
    pub send_mode: VoiceSendMode,
    pub image_mode_enabled: bool,
    pub macros_enabled: bool,
    pub sensitivity_db: f32,
    pub theme: Theme,
    pub theme_locked: bool,
    pub hud_style: HudStyle,
    pub hud_border_style: HudBorderStyle,
    pub hud_right_panel: HudRightPanel,
    pub hud_right_panel_recording_only: bool,
    pub latency_display: LatencyDisplayMode,
    pub mouse_enabled: bool,
    pub backend_label: &'a str,
    pub pipeline: Pipeline,
}
