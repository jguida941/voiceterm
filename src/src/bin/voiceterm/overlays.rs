//! Help/settings overlay rendering so panel layout stays centralized and consistent.

use crossbeam_channel::Sender;

use crate::config::OverlayConfig;
use crate::help::{format_help_overlay, help_overlay_height};
use crate::settings::{
    format_settings_overlay, settings_overlay_height, SettingsMenuState, SettingsView,
};
use crate::status_line::StatusLineState;
use crate::theme::{style_pack_theme_lock, Theme};
use crate::theme_picker::{format_theme_picker, theme_picker_height};
use crate::theme_studio::{format_theme_studio, theme_studio_height, ThemeStudioView};
use crate::toast::{format_toast_history_overlay, toast_history_overlay_height, ToastCenter};
use crate::transcript_history::{
    format_transcript_history_overlay, transcript_history_overlay_height, TranscriptHistory,
    TranscriptHistoryState,
};
use crate::writer::{try_send_message, WriterMessage};

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub(crate) enum OverlayMode {
    None,
    Help,
    ThemeStudio,
    ThemePicker,
    Settings,
    TranscriptHistory,
    #[allow(dead_code)]
    ToastHistory,
    #[allow(dead_code)]
    MemoryBrowser,
    #[allow(dead_code)]
    ActionCenter,
}

pub(crate) fn show_settings_overlay(
    writer_tx: &Sender<WriterMessage>,
    theme: Theme,
    cols: u16,
    settings_menu: &SettingsMenuState,
    config: &OverlayConfig,
    status_state: &StatusLineState,
    backend_label: &str,
) {
    let locked_theme = style_pack_theme_lock();
    let effective_theme = locked_theme.unwrap_or(theme);
    let view = SettingsView {
        selected: settings_menu.selected,
        auto_voice_enabled: status_state.auto_voice_enabled,
        wake_word_enabled: config.wake_word,
        wake_word_sensitivity: config.wake_word_sensitivity,
        wake_word_cooldown_ms: config.wake_word_cooldown_ms,
        send_mode: config.voice_send_mode,
        image_mode_enabled: config.image_mode,
        macros_enabled: status_state.macros_enabled,
        sensitivity_db: status_state.sensitivity_db,
        theme: effective_theme,
        theme_locked: locked_theme.is_some(),
        hud_style: status_state.hud_style,
        hud_border_style: config.hud_border_style,
        hud_right_panel: config.hud_right_panel,
        hud_right_panel_recording_only: config.hud_right_panel_recording_only,
        latency_display: status_state.latency_display,
        mouse_enabled: status_state.mouse_enabled,
        backend_label,
        pipeline: status_state.pipeline,
    };
    let content = format_settings_overlay(&view, cols as usize);
    let height = settings_overlay_height();
    let _ = try_send_message(writer_tx, WriterMessage::ShowOverlay { content, height });
}

pub(crate) fn show_theme_picker_overlay(
    writer_tx: &Sender<WriterMessage>,
    theme: Theme,
    selected_idx: usize,
    cols: u16,
    locked_theme: Option<Theme>,
) {
    let content = format_theme_picker(theme, selected_idx, cols as usize, locked_theme);
    let height = theme_picker_height();
    let _ = try_send_message(writer_tx, WriterMessage::ShowOverlay { content, height });
}

pub(crate) fn show_theme_studio_overlay(
    writer_tx: &Sender<WriterMessage>,
    view: &ThemeStudioView,
    cols: u16,
) {
    let content = format_theme_studio(view, cols as usize);
    let height = theme_studio_height();
    let _ = try_send_message(writer_tx, WriterMessage::ShowOverlay { content, height });
}

pub(crate) fn show_help_overlay(writer_tx: &Sender<WriterMessage>, theme: Theme, cols: u16) {
    let content = format_help_overlay(theme, cols as usize);
    let height = help_overlay_height();
    let _ = try_send_message(writer_tx, WriterMessage::ShowOverlay { content, height });
}

pub(crate) fn show_toast_history_overlay(
    writer_tx: &Sender<WriterMessage>,
    toast_center: &ToastCenter,
    theme: Theme,
    cols: u16,
) {
    let content = format_toast_history_overlay(toast_center, theme, cols as usize);
    let height = toast_history_overlay_height(toast_center);
    let _ = try_send_message(writer_tx, WriterMessage::ShowOverlay { content, height });
}

pub(crate) fn show_transcript_history_overlay(
    writer_tx: &Sender<WriterMessage>,
    history: &TranscriptHistory,
    history_state: &TranscriptHistoryState,
    theme: Theme,
    cols: u16,
) {
    let content = format_transcript_history_overlay(history, history_state, theme, cols as usize);
    let height = transcript_history_overlay_height();
    let _ = try_send_message(writer_tx, WriterMessage::ShowOverlay { content, height });
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::config::{HudBorderStyle, HudRightPanel, HudStyle};
    use crate::status_line::Pipeline;
    use clap::Parser;
    use crossbeam_channel::bounded;

    #[test]
    fn show_settings_overlay_sends_overlay() {
        let config = OverlayConfig::parse_from(["test-app"]);
        let settings_menu = SettingsMenuState::new();
        let mut status_state = StatusLineState::new();
        status_state.pipeline = Pipeline::Rust;
        let (writer_tx, writer_rx) = bounded(4);
        show_settings_overlay(
            &writer_tx,
            Theme::Coral,
            80,
            &settings_menu,
            &config,
            &status_state,
            "codex",
        );
        match writer_rx
            .recv_timeout(std::time::Duration::from_millis(200))
            .expect("overlay message")
        {
            WriterMessage::ShowOverlay { height, .. } => {
                assert_eq!(height, settings_overlay_height());
            }
            other => panic!("unexpected writer message: {other:?}"),
        }
    }

    #[test]
    fn show_theme_picker_overlay_sends_overlay() {
        let (writer_tx, writer_rx) = bounded(4);
        show_theme_picker_overlay(&writer_tx, Theme::Coral, 0, 80, None);
        match writer_rx
            .recv_timeout(std::time::Duration::from_millis(200))
            .expect("overlay message")
        {
            WriterMessage::ShowOverlay { content, height } => {
                assert_eq!(height, theme_picker_height());
                assert!(!content.is_empty());
            }
            other => panic!("unexpected writer message: {other:?}"),
        }
    }

    #[test]
    fn show_theme_studio_overlay_sends_overlay() {
        let (writer_tx, writer_rx) = bounded(4);
        let view = ThemeStudioView {
            theme: Theme::Coral,
            selected: 0,
            hud_style: HudStyle::Full,
            hud_border_style: HudBorderStyle::Theme,
            hud_right_panel: HudRightPanel::Ribbon,
            hud_right_panel_recording_only: true,
            border_style_override: None,
            glyph_set_override: None,
            indicator_set_override: None,
            progress_style_override: None,
            progress_bar_family_override: None,
            voice_scene_style_override: None,
            toast_position_override: None,
            startup_style_override: None,
            toast_severity_mode_override: None,
            banner_style_override: None,
            undo_available: false,
            redo_available: false,
            runtime_overrides_dirty: false,
        };
        show_theme_studio_overlay(&writer_tx, &view, 80);
        match writer_rx
            .recv_timeout(std::time::Duration::from_millis(200))
            .expect("overlay message")
        {
            WriterMessage::ShowOverlay { content, height } => {
                assert_eq!(height, theme_studio_height());
                assert!(content.contains("Theme Studio"));
            }
            other => panic!("unexpected writer message: {other:?}"),
        }
    }

    #[test]
    fn show_help_overlay_sends_overlay() {
        let (writer_tx, writer_rx) = bounded(4);
        show_help_overlay(&writer_tx, Theme::Coral, 80);
        match writer_rx
            .recv_timeout(std::time::Duration::from_millis(200))
            .expect("overlay message")
        {
            WriterMessage::ShowOverlay { content, height } => {
                assert_eq!(height, help_overlay_height());
                assert!(content.contains("Shortcuts"));
            }
            other => panic!("unexpected writer message: {other:?}"),
        }
    }
}
