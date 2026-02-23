use super::*;
use crate::buttons::ButtonAction;
use crate::buttons::ButtonRegistry;
use crate::overlays::OverlayMode;
use crate::status_line::StatusLineState;
use crate::theme::Theme;
use crate::voice_control::VoiceManager;
use clap::Parser;
use crossbeam_channel::bounded;

fn make_context<'a>(
    config: &'a mut OverlayConfig,
    voice_manager: &'a mut VoiceManager,
    writer_tx: &'a Sender<WriterMessage>,
    status_clear_deadline: &'a mut Option<Instant>,
    current_status: &'a mut Option<String>,
    status_state: &'a mut StatusLineState,
    auto_voice_enabled: &'a mut bool,
    last_auto_trigger_at: &'a mut Option<Instant>,
    recording_started_at: &'a mut Option<Instant>,
    preview_clear_deadline: &'a mut Option<Instant>,
    last_meter_update: &'a mut Instant,
    button_registry: &'a ButtonRegistry,
    terminal_rows: &'a mut u16,
    terminal_cols: &'a mut u16,
    theme: &'a mut Theme,
) -> SettingsActionContext<'a> {
    SettingsActionContext {
        config,
        status: SettingsStatusContext {
            status_state,
            writer_tx,
            status_clear_deadline,
            current_status,
            preview_clear_deadline,
            last_meter_update,
        },
        voice: SettingsVoiceContext {
            auto_voice_enabled,
            auto_voice_paused_by_user: None,
            voice_manager,
            last_auto_trigger_at,
            recording_started_at,
        },
        hud: SettingsHudContext {
            button_registry,
            overlay_mode: OverlayMode::None,
            terminal_rows,
            terminal_cols,
            theme,
            pty_session: None,
        },
    }
}

#[test]
fn toggle_send_mode_updates_state_and_status() {
    let mut config = OverlayConfig::parse_from(["test-app"]);
    let mut voice_manager = VoiceManager::new(config.app.clone());
    let (writer_tx, writer_rx) = bounded(4);
    let mut status_clear_deadline = None;
    let mut current_status = None;
    let mut status_state = StatusLineState::new();
    let mut auto_voice_enabled = false;
    let mut last_auto_trigger_at = None;
    let mut recording_started_at = None;
    let mut preview_clear_deadline = None;
    let mut last_meter_update = Instant::now();
    let button_registry = ButtonRegistry::new();
    let mut terminal_rows = 24;
    let mut terminal_cols = 80;
    let mut theme = Theme::Coral;

    {
        let mut ctx = make_context(
            &mut config,
            &mut voice_manager,
            &writer_tx,
            &mut status_clear_deadline,
            &mut current_status,
            &mut status_state,
            &mut auto_voice_enabled,
            &mut last_auto_trigger_at,
            &mut recording_started_at,
            &mut preview_clear_deadline,
            &mut last_meter_update,
            &button_registry,
            &mut terminal_rows,
            &mut terminal_cols,
            &mut theme,
        );
        ctx.toggle_send_mode();
    }
    assert_eq!(config.voice_send_mode, VoiceSendMode::Insert);
    assert_eq!(status_state.send_mode, VoiceSendMode::Insert);
    status_state.insert_pending_send = true;
    match writer_rx
        .recv_timeout(Duration::from_millis(200))
        .expect("status message")
    {
        WriterMessage::EnhancedStatus(state) => {
            assert_eq!(state.message, "Edit mode: press Enter to send");
        }
        other => panic!("unexpected writer message: {other:?}"),
    }

    status_state.recording_duration = Some(1.7);
    status_state.meter_db = Some(-40.0);
    status_state.meter_levels.push(-40.0);
    status_state.transcript_preview = Some("stale preview".to_string());
    {
        let mut ctx = make_context(
            &mut config,
            &mut voice_manager,
            &writer_tx,
            &mut status_clear_deadline,
            &mut current_status,
            &mut status_state,
            &mut auto_voice_enabled,
            &mut last_auto_trigger_at,
            &mut recording_started_at,
            &mut preview_clear_deadline,
            &mut last_meter_update,
            &button_registry,
            &mut terminal_rows,
            &mut terminal_cols,
            &mut theme,
        );
        ctx.toggle_send_mode();
    }
    assert_eq!(config.voice_send_mode, VoiceSendMode::Auto);
    assert_eq!(status_state.send_mode, VoiceSendMode::Auto);
    assert!(!status_state.insert_pending_send);
    match writer_rx
        .recv_timeout(Duration::from_millis(200))
        .expect("status message")
    {
        WriterMessage::EnhancedStatus(state) => {
            assert!(state.message.contains("auto"));
        }
        other => panic!("unexpected writer message: {other:?}"),
    }
}

#[test]
fn toggle_image_mode_updates_config_state_and_status() {
    let mut config = OverlayConfig::parse_from(["test-app"]);
    let mut voice_manager = VoiceManager::new(config.app.clone());
    let (writer_tx, writer_rx) = bounded(4);
    let mut status_clear_deadline = None;
    let mut current_status = None;
    let mut status_state = StatusLineState::new();
    let mut auto_voice_enabled = false;
    let mut last_auto_trigger_at = None;
    let mut recording_started_at = None;
    let mut preview_clear_deadline = None;
    let mut last_meter_update = Instant::now();
    let button_registry = ButtonRegistry::new();
    let mut terminal_rows = 24;
    let mut terminal_cols = 80;
    let mut theme = Theme::Coral;

    {
        let mut ctx = make_context(
            &mut config,
            &mut voice_manager,
            &writer_tx,
            &mut status_clear_deadline,
            &mut current_status,
            &mut status_state,
            &mut auto_voice_enabled,
            &mut last_auto_trigger_at,
            &mut recording_started_at,
            &mut preview_clear_deadline,
            &mut last_meter_update,
            &button_registry,
            &mut terminal_rows,
            &mut terminal_cols,
            &mut theme,
        );
        ctx.toggle_image_mode();
    }

    assert!(config.image_mode);
    assert!(status_state.image_mode_enabled);
    match writer_rx
        .recv_timeout(Duration::from_millis(200))
        .expect("status message")
    {
        WriterMessage::EnhancedStatus(state) => {
            assert!(state.message.contains("Image mode: ON"));
        }
        other => panic!("unexpected writer message: {other:?}"),
    }
}

#[test]
fn toggle_macros_enabled_updates_state_and_status() {
    let mut config = OverlayConfig::parse_from(["test-app"]);
    let mut voice_manager = VoiceManager::new(config.app.clone());
    let (writer_tx, writer_rx) = bounded(4);
    let mut status_clear_deadline = None;
    let mut current_status = None;
    let mut status_state = StatusLineState::new();
    let mut auto_voice_enabled = false;
    let mut last_auto_trigger_at = None;
    let mut recording_started_at = None;
    let mut preview_clear_deadline = None;
    let mut last_meter_update = Instant::now();
    let button_registry = ButtonRegistry::new();
    let mut terminal_rows = 24;
    let mut terminal_cols = 80;
    let mut theme = Theme::Coral;

    {
        let mut ctx = make_context(
            &mut config,
            &mut voice_manager,
            &writer_tx,
            &mut status_clear_deadline,
            &mut current_status,
            &mut status_state,
            &mut auto_voice_enabled,
            &mut last_auto_trigger_at,
            &mut recording_started_at,
            &mut preview_clear_deadline,
            &mut last_meter_update,
            &button_registry,
            &mut terminal_rows,
            &mut terminal_cols,
            &mut theme,
        );
        ctx.toggle_macros_enabled();
    }
    assert!(status_state.macros_enabled);
    match writer_rx
        .recv_timeout(Duration::from_millis(200))
        .expect("status message")
    {
        WriterMessage::EnhancedStatus(state) => {
            assert!(state.message.contains("Macros: ON"));
        }
        other => panic!("unexpected writer message: {other:?}"),
    }

    {
        let mut ctx = make_context(
            &mut config,
            &mut voice_manager,
            &writer_tx,
            &mut status_clear_deadline,
            &mut current_status,
            &mut status_state,
            &mut auto_voice_enabled,
            &mut last_auto_trigger_at,
            &mut recording_started_at,
            &mut preview_clear_deadline,
            &mut last_meter_update,
            &button_registry,
            &mut terminal_rows,
            &mut terminal_cols,
            &mut theme,
        );
        ctx.toggle_macros_enabled();
    }
    assert!(!status_state.macros_enabled);
    match writer_rx
        .recv_timeout(Duration::from_millis(200))
        .expect("status message")
    {
        WriterMessage::EnhancedStatus(state) => {
            assert!(state.message.contains("Macros: OFF"));
        }
        other => panic!("unexpected writer message: {other:?}"),
    }
}

#[test]
fn adjust_sensitivity_updates_threshold_and_message() {
    let mut config = OverlayConfig::parse_from(["test-app"]);
    let mut voice_manager = VoiceManager::new(config.app.clone());
    let (writer_tx, writer_rx) = bounded(4);
    let mut status_clear_deadline = None;
    let mut current_status = None;
    let mut status_state = StatusLineState::new();
    let mut auto_voice_enabled = false;
    let mut last_auto_trigger_at = None;
    let mut recording_started_at = None;
    let mut preview_clear_deadline = None;
    let mut last_meter_update = Instant::now();
    let button_registry = ButtonRegistry::new();
    let mut terminal_rows = 24;
    let mut terminal_cols = 80;
    let mut theme = Theme::Coral;

    {
        let mut ctx = make_context(
            &mut config,
            &mut voice_manager,
            &writer_tx,
            &mut status_clear_deadline,
            &mut current_status,
            &mut status_state,
            &mut auto_voice_enabled,
            &mut last_auto_trigger_at,
            &mut recording_started_at,
            &mut preview_clear_deadline,
            &mut last_meter_update,
            &button_registry,
            &mut terminal_rows,
            &mut terminal_cols,
            &mut theme,
        );
        ctx.adjust_sensitivity(5.0);
    }
    let up_threshold = status_state.sensitivity_db;
    match writer_rx
        .recv_timeout(Duration::from_millis(200))
        .expect("status message")
    {
        WriterMessage::EnhancedStatus(state) => {
            assert!(state.message.contains("less sensitive"));
        }
        other => panic!("unexpected writer message: {other:?}"),
    }

    {
        let mut ctx = make_context(
            &mut config,
            &mut voice_manager,
            &writer_tx,
            &mut status_clear_deadline,
            &mut current_status,
            &mut status_state,
            &mut auto_voice_enabled,
            &mut last_auto_trigger_at,
            &mut recording_started_at,
            &mut preview_clear_deadline,
            &mut last_meter_update,
            &button_registry,
            &mut terminal_rows,
            &mut terminal_cols,
            &mut theme,
        );
        ctx.adjust_sensitivity(-5.0);
    }
    assert!(status_state.sensitivity_db < up_threshold);
    match writer_rx
        .recv_timeout(Duration::from_millis(200))
        .expect("status message")
    {
        WriterMessage::EnhancedStatus(state) => {
            assert!(state.message.contains("more sensitive"));
        }
        other => panic!("unexpected writer message: {other:?}"),
    }
}

#[test]
fn cycle_hud_right_panel_wraps() {
    assert_eq!(
        cycle_hud_right_panel(HudRightPanel::Ribbon, 1),
        HudRightPanel::Dots
    );
    assert_eq!(
        cycle_hud_right_panel(HudRightPanel::Ribbon, -1),
        HudRightPanel::Off
    );
    assert_eq!(
        cycle_hud_right_panel(HudRightPanel::Off, 1),
        HudRightPanel::Ribbon
    );
}

#[test]
fn cycle_hud_border_style_wraps() {
    assert_eq!(
        cycle_hud_border_style(HudBorderStyle::Theme, 1),
        HudBorderStyle::Single
    );
    assert_eq!(
        cycle_hud_border_style(HudBorderStyle::Theme, -1),
        HudBorderStyle::None
    );
    assert_eq!(
        cycle_hud_border_style(HudBorderStyle::None, 1),
        HudBorderStyle::Theme
    );
}

#[test]
fn cycle_hud_panel_updates_state_and_status() {
    let mut config = OverlayConfig::parse_from(["test-app"]);
    let mut voice_manager = VoiceManager::new(config.app.clone());
    let (writer_tx, writer_rx) = bounded(4);
    let mut status_clear_deadline = None;
    let mut current_status = None;
    let mut status_state = StatusLineState::new();
    let mut auto_voice_enabled = false;
    let mut last_auto_trigger_at = None;
    let mut recording_started_at = None;
    let mut preview_clear_deadline = None;
    let mut last_meter_update = Instant::now();
    let button_registry = ButtonRegistry::new();
    let mut terminal_rows = 24;
    let mut terminal_cols = 80;
    let mut theme = Theme::Coral;

    let mut ctx = make_context(
        &mut config,
        &mut voice_manager,
        &writer_tx,
        &mut status_clear_deadline,
        &mut current_status,
        &mut status_state,
        &mut auto_voice_enabled,
        &mut last_auto_trigger_at,
        &mut recording_started_at,
        &mut preview_clear_deadline,
        &mut last_meter_update,
        &button_registry,
        &mut terminal_rows,
        &mut terminal_cols,
        &mut theme,
    );

    ctx.cycle_hud_panel(1);
    assert_eq!(config.hud_right_panel, HudRightPanel::Dots);
    assert_eq!(status_state.hud_right_panel, HudRightPanel::Dots);
    match writer_rx
        .recv_timeout(Duration::from_millis(200))
        .expect("status message")
    {
        WriterMessage::EnhancedStatus(state) => {
            assert!(state.message.contains("HUD right panel"));
        }
        other => panic!("unexpected writer message: {other:?}"),
    }
}

#[test]
fn cycle_hud_border_style_updates_state_and_status() {
    let mut config = OverlayConfig::parse_from(["test-app"]);
    let mut voice_manager = VoiceManager::new(config.app.clone());
    let (writer_tx, writer_rx) = bounded(4);
    let mut status_clear_deadline = None;
    let mut current_status = None;
    let mut status_state = StatusLineState::new();
    let mut auto_voice_enabled = false;
    let mut last_auto_trigger_at = None;
    let mut recording_started_at = None;
    let mut preview_clear_deadline = None;
    let mut last_meter_update = Instant::now();
    let button_registry = ButtonRegistry::new();
    let mut terminal_rows = 24;
    let mut terminal_cols = 80;
    let mut theme = Theme::Coral;

    let mut ctx = make_context(
        &mut config,
        &mut voice_manager,
        &writer_tx,
        &mut status_clear_deadline,
        &mut current_status,
        &mut status_state,
        &mut auto_voice_enabled,
        &mut last_auto_trigger_at,
        &mut recording_started_at,
        &mut preview_clear_deadline,
        &mut last_meter_update,
        &button_registry,
        &mut terminal_rows,
        &mut terminal_cols,
        &mut theme,
    );

    ctx.cycle_hud_border_style(1);
    assert_eq!(config.hud_border_style, HudBorderStyle::Single);
    assert_eq!(status_state.hud_border_style, HudBorderStyle::Single);
    match writer_rx
        .recv_timeout(Duration::from_millis(200))
        .expect("status message")
    {
        WriterMessage::EnhancedStatus(state) => {
            assert!(state.message.contains("HUD borders"));
        }
        other => panic!("unexpected writer message: {other:?}"),
    }
}

#[test]
fn cycle_hud_style_wraps() {
    assert_eq!(cycle_hud_style(HudStyle::Full, 1), HudStyle::Minimal);
    assert_eq!(cycle_hud_style(HudStyle::Full, -1), HudStyle::Hidden);
    assert_eq!(cycle_hud_style(HudStyle::Hidden, 1), HudStyle::Full);
}

#[test]
fn cycle_latency_display_wraps() {
    assert_eq!(
        cycle_latency_display(LatencyDisplayMode::Short, 1),
        LatencyDisplayMode::Label
    );
    assert_eq!(
        cycle_latency_display(LatencyDisplayMode::Label, 1),
        LatencyDisplayMode::Off
    );
    assert_eq!(
        cycle_latency_display(LatencyDisplayMode::Off, 1),
        LatencyDisplayMode::Short
    );
}

#[test]
fn cycle_latency_display_updates_state_and_status() {
    let mut config = OverlayConfig::parse_from(["test-app"]);
    let mut voice_manager = VoiceManager::new(config.app.clone());
    let (writer_tx, writer_rx) = bounded(4);
    let mut status_clear_deadline = None;
    let mut current_status = None;
    let mut status_state = StatusLineState::new();
    let mut auto_voice_enabled = false;
    let mut last_auto_trigger_at = None;
    let mut recording_started_at = None;
    let mut preview_clear_deadline = None;
    let mut last_meter_update = Instant::now();
    let button_registry = ButtonRegistry::new();
    let mut terminal_rows = 24;
    let mut terminal_cols = 80;
    let mut theme = Theme::Coral;

    let mut ctx = make_context(
        &mut config,
        &mut voice_manager,
        &writer_tx,
        &mut status_clear_deadline,
        &mut current_status,
        &mut status_state,
        &mut auto_voice_enabled,
        &mut last_auto_trigger_at,
        &mut recording_started_at,
        &mut preview_clear_deadline,
        &mut last_meter_update,
        &button_registry,
        &mut terminal_rows,
        &mut terminal_cols,
        &mut theme,
    );

    ctx.cycle_latency_display(1);
    assert_eq!(config.latency_display, LatencyDisplayMode::Label);
    assert_eq!(status_state.latency_display, LatencyDisplayMode::Label);
    match writer_rx
        .recv_timeout(Duration::from_millis(200))
        .expect("status message")
    {
        WriterMessage::EnhancedStatus(state) => {
            assert!(state.message.contains("Latency display"));
        }
        other => panic!("unexpected writer message: {other:?}"),
    }
}

#[test]
fn cycle_hud_style_updates_state_and_status() {
    let mut config = OverlayConfig::parse_from(["test-app"]);
    let mut voice_manager = VoiceManager::new(config.app.clone());
    let (writer_tx, writer_rx) = bounded(4);
    let mut status_clear_deadline = None;
    let mut current_status = None;
    let mut status_state = StatusLineState::new();
    status_state.hidden_launcher_collapsed = true;
    let mut auto_voice_enabled = false;
    let mut last_auto_trigger_at = None;
    let mut recording_started_at = None;
    let mut preview_clear_deadline = None;
    let mut last_meter_update = Instant::now();
    let button_registry = ButtonRegistry::new();
    let mut terminal_rows = 24;
    let mut terminal_cols = 80;
    let mut theme = Theme::Coral;

    let mut ctx = make_context(
        &mut config,
        &mut voice_manager,
        &writer_tx,
        &mut status_clear_deadline,
        &mut current_status,
        &mut status_state,
        &mut auto_voice_enabled,
        &mut last_auto_trigger_at,
        &mut recording_started_at,
        &mut preview_clear_deadline,
        &mut last_meter_update,
        &button_registry,
        &mut terminal_rows,
        &mut terminal_cols,
        &mut theme,
    );

    ctx.cycle_hud_style(1);
    assert_eq!(status_state.hud_style, HudStyle::Minimal);
    assert!(!status_state.hidden_launcher_collapsed);
    match writer_rx
        .recv_timeout(Duration::from_millis(200))
        .expect("status message")
    {
        WriterMessage::EnhancedStatus(state) => {
            assert!(state.message.contains("HUD style"));
        }
        other => panic!("unexpected writer message: {other:?}"),
    }
}

#[test]
fn toggle_auto_voice_updates_state_and_status() {
    let mut config = OverlayConfig::parse_from(["test-app"]);
    config.app.no_python_fallback = true;
    let mut voice_manager = VoiceManager::new(config.app.clone());
    let (writer_tx, writer_rx) = bounded(4);
    let mut status_clear_deadline = None;
    let mut current_status = None;
    let mut status_state = StatusLineState::new();
    let mut auto_voice_enabled = false;
    let mut last_auto_trigger_at = None;
    let mut recording_started_at = None;
    let mut preview_clear_deadline = None;
    let mut last_meter_update = Instant::now();
    let button_registry = ButtonRegistry::new();
    let mut terminal_rows = 24;
    let mut terminal_cols = 80;
    let mut theme = Theme::Coral;

    {
        let mut ctx = make_context(
            &mut config,
            &mut voice_manager,
            &writer_tx,
            &mut status_clear_deadline,
            &mut current_status,
            &mut status_state,
            &mut auto_voice_enabled,
            &mut last_auto_trigger_at,
            &mut recording_started_at,
            &mut preview_clear_deadline,
            &mut last_meter_update,
            &button_registry,
            &mut terminal_rows,
            &mut terminal_cols,
            &mut theme,
        );
        ctx.toggle_auto_voice();
    }
    assert!(auto_voice_enabled);
    assert_eq!(status_state.voice_mode, VoiceMode::Auto);
    let mut saw_enabled = false;
    for _ in 0..3 {
        match writer_rx.recv_timeout(Duration::from_millis(200)) {
            Ok(WriterMessage::EnhancedStatus(state)) => {
                if state.message.contains("Auto-voice enabled") {
                    saw_enabled = true;
                    break;
                }
            }
            Ok(other) => panic!("unexpected writer message: {other:?}"),
            Err(_) => break,
        }
    }
    assert!(saw_enabled, "expected Auto-voice enabled status");

    status_state.transcript_preview = Some("stale".to_string());
    preview_clear_deadline = Some(Instant::now() + Duration::from_secs(5));
    let meter_before_disable = Instant::now() - Duration::from_secs(10);
    last_meter_update = meter_before_disable;

    {
        let mut ctx = make_context(
            &mut config,
            &mut voice_manager,
            &writer_tx,
            &mut status_clear_deadline,
            &mut current_status,
            &mut status_state,
            &mut auto_voice_enabled,
            &mut last_auto_trigger_at,
            &mut recording_started_at,
            &mut preview_clear_deadline,
            &mut last_meter_update,
            &button_registry,
            &mut terminal_rows,
            &mut terminal_cols,
            &mut theme,
        );
        ctx.toggle_auto_voice();
    }
    assert!(!auto_voice_enabled);
    assert_eq!(status_state.voice_mode, VoiceMode::Manual);
    assert!(status_state.recording_duration.is_none());
    assert!(status_state.meter_db.is_none());
    assert!(status_state.meter_levels.is_empty());
    assert!(status_state.transcript_preview.is_none());
    assert!(preview_clear_deadline.is_none());
    assert!(last_meter_update > meter_before_disable);
    match writer_rx
        .recv_timeout(Duration::from_millis(200))
        .expect("status message")
    {
        WriterMessage::EnhancedStatus(state) => {
            assert!(state.message.contains("Auto-voice disabled"));
        }
        other => panic!("unexpected writer message: {other:?}"),
    }
}

#[test]
fn toggle_wake_word_updates_state_and_status() {
    let mut config = OverlayConfig::parse_from(["test-app"]);
    let mut voice_manager = VoiceManager::new(config.app.clone());
    let (writer_tx, writer_rx) = bounded(4);
    let mut status_clear_deadline = None;
    let mut current_status = None;
    let mut status_state = StatusLineState::new();
    let mut auto_voice_enabled = false;
    let mut last_auto_trigger_at = None;
    let mut recording_started_at = None;
    let mut preview_clear_deadline = None;
    let mut last_meter_update = Instant::now();
    let button_registry = ButtonRegistry::new();
    let mut terminal_rows = 24;
    let mut terminal_cols = 80;
    let mut theme = Theme::Coral;

    {
        let mut ctx = make_context(
            &mut config,
            &mut voice_manager,
            &writer_tx,
            &mut status_clear_deadline,
            &mut current_status,
            &mut status_state,
            &mut auto_voice_enabled,
            &mut last_auto_trigger_at,
            &mut recording_started_at,
            &mut preview_clear_deadline,
            &mut last_meter_update,
            &button_registry,
            &mut terminal_rows,
            &mut terminal_cols,
            &mut theme,
        );
        ctx.toggle_wake_word();
    }
    assert!(config.wake_word);
    assert_eq!(
        status_state.wake_word_state,
        crate::status_line::WakeWordHudState::Listening
    );
    match writer_rx
        .recv_timeout(Duration::from_millis(200))
        .expect("status message")
    {
        WriterMessage::EnhancedStatus(state) => {
            assert!(state.message.contains("Wake word: ON"));
        }
        other => panic!("unexpected writer message: {other:?}"),
    }

    {
        let mut ctx = make_context(
            &mut config,
            &mut voice_manager,
            &writer_tx,
            &mut status_clear_deadline,
            &mut current_status,
            &mut status_state,
            &mut auto_voice_enabled,
            &mut last_auto_trigger_at,
            &mut recording_started_at,
            &mut preview_clear_deadline,
            &mut last_meter_update,
            &button_registry,
            &mut terminal_rows,
            &mut terminal_cols,
            &mut theme,
        );
        ctx.toggle_wake_word();
    }
    assert!(!config.wake_word);
    assert_eq!(
        status_state.wake_word_state,
        crate::status_line::WakeWordHudState::Off
    );
    match writer_rx
        .recv_timeout(Duration::from_millis(200))
        .expect("status message")
    {
        WriterMessage::EnhancedStatus(state) => {
            assert!(state.message.contains("Wake word: OFF"));
        }
        other => panic!("unexpected writer message: {other:?}"),
    }
}

#[test]
fn adjust_wake_word_sensitivity_clamps_and_reports() {
    let mut config = OverlayConfig::parse_from(["test-app"]);
    let mut voice_manager = VoiceManager::new(config.app.clone());
    let (writer_tx, writer_rx) = bounded(4);
    let mut status_clear_deadline = None;
    let mut current_status = None;
    let mut status_state = StatusLineState::new();
    let mut auto_voice_enabled = false;
    let mut last_auto_trigger_at = None;
    let mut recording_started_at = None;
    let mut preview_clear_deadline = None;
    let mut last_meter_update = Instant::now();
    let button_registry = ButtonRegistry::new();
    let mut terminal_rows = 24;
    let mut terminal_cols = 80;
    let mut theme = Theme::Coral;

    {
        let mut ctx = make_context(
            &mut config,
            &mut voice_manager,
            &writer_tx,
            &mut status_clear_deadline,
            &mut current_status,
            &mut status_state,
            &mut auto_voice_enabled,
            &mut last_auto_trigger_at,
            &mut recording_started_at,
            &mut preview_clear_deadline,
            &mut last_meter_update,
            &button_registry,
            &mut terminal_rows,
            &mut terminal_cols,
            &mut theme,
        );
        ctx.adjust_wake_word_sensitivity(0.8);
    }
    assert!((config.wake_word_sensitivity - 1.0).abs() < f32::EPSILON);
    match writer_rx
        .recv_timeout(Duration::from_millis(200))
        .expect("status message")
    {
        WriterMessage::EnhancedStatus(state) => {
            assert!(state.message.contains("100%"));
            assert!(state.message.contains("more sensitive"));
        }
        other => panic!("unexpected writer message: {other:?}"),
    }

    {
        let mut ctx = make_context(
            &mut config,
            &mut voice_manager,
            &writer_tx,
            &mut status_clear_deadline,
            &mut current_status,
            &mut status_state,
            &mut auto_voice_enabled,
            &mut last_auto_trigger_at,
            &mut recording_started_at,
            &mut preview_clear_deadline,
            &mut last_meter_update,
            &button_registry,
            &mut terminal_rows,
            &mut terminal_cols,
            &mut theme,
        );
        ctx.adjust_wake_word_sensitivity(-2.0);
    }
    assert!((config.wake_word_sensitivity - 0.0).abs() < f32::EPSILON);
    match writer_rx
        .recv_timeout(Duration::from_millis(200))
        .expect("status message")
    {
        WriterMessage::EnhancedStatus(state) => {
            assert!(state.message.contains("0%"));
            assert!(state.message.contains("less sensitive"));
        }
        other => panic!("unexpected writer message: {other:?}"),
    }
}

#[test]
fn cycle_wake_word_cooldown_wraps_and_reports() {
    let mut config = OverlayConfig::parse_from(["test-app"]);
    let mut voice_manager = VoiceManager::new(config.app.clone());
    let (writer_tx, writer_rx) = bounded(6);
    let mut status_clear_deadline = None;
    let mut current_status = None;
    let mut status_state = StatusLineState::new();
    let mut auto_voice_enabled = false;
    let mut last_auto_trigger_at = None;
    let mut recording_started_at = None;
    let mut preview_clear_deadline = None;
    let mut last_meter_update = Instant::now();
    let button_registry = ButtonRegistry::new();
    let mut terminal_rows = 24;
    let mut terminal_cols = 80;
    let mut theme = Theme::Coral;

    {
        let mut ctx = make_context(
            &mut config,
            &mut voice_manager,
            &writer_tx,
            &mut status_clear_deadline,
            &mut current_status,
            &mut status_state,
            &mut auto_voice_enabled,
            &mut last_auto_trigger_at,
            &mut recording_started_at,
            &mut preview_clear_deadline,
            &mut last_meter_update,
            &button_registry,
            &mut terminal_rows,
            &mut terminal_cols,
            &mut theme,
        );
        ctx.cycle_wake_word_cooldown(1);
    }
    assert_eq!(config.wake_word_cooldown_ms, 3000);
    match writer_rx
        .recv_timeout(Duration::from_millis(200))
        .expect("status message")
    {
        WriterMessage::EnhancedStatus(state) => {
            assert!(state.message.contains("3000 ms"));
        }
        other => panic!("unexpected writer message: {other:?}"),
    }

    config.wake_word_cooldown_ms = 500;
    {
        let mut ctx = make_context(
            &mut config,
            &mut voice_manager,
            &writer_tx,
            &mut status_clear_deadline,
            &mut current_status,
            &mut status_state,
            &mut auto_voice_enabled,
            &mut last_auto_trigger_at,
            &mut recording_started_at,
            &mut preview_clear_deadline,
            &mut last_meter_update,
            &button_registry,
            &mut terminal_rows,
            &mut terminal_cols,
            &mut theme,
        );
        ctx.cycle_wake_word_cooldown(-1);
    }
    assert_eq!(config.wake_word_cooldown_ms, 10_000);
    match writer_rx
        .recv_timeout(Duration::from_millis(200))
        .expect("status message")
    {
        WriterMessage::EnhancedStatus(state) => {
            assert!(state.message.contains("10000 ms"));
        }
        other => panic!("unexpected writer message: {other:?}"),
    }
}

#[test]
fn cycle_theme_updates_selected_theme() {
    let mut config = OverlayConfig::parse_from(["test-app"]);
    let mut voice_manager = VoiceManager::new(config.app.clone());
    let (writer_tx, _writer_rx) = bounded(4);
    let mut status_clear_deadline = None;
    let mut current_status = None;
    let mut status_state = StatusLineState::new();
    let mut auto_voice_enabled = false;
    let mut last_auto_trigger_at = None;
    let mut recording_started_at = None;
    let mut preview_clear_deadline = None;
    let mut last_meter_update = Instant::now();
    let button_registry = ButtonRegistry::new();
    let mut terminal_rows = 24;
    let mut terminal_cols = 80;
    let mut theme = Theme::Coral;

    let previous = theme;
    let mut ctx = make_context(
        &mut config,
        &mut voice_manager,
        &writer_tx,
        &mut status_clear_deadline,
        &mut current_status,
        &mut status_state,
        &mut auto_voice_enabled,
        &mut last_auto_trigger_at,
        &mut recording_started_at,
        &mut preview_clear_deadline,
        &mut last_meter_update,
        &button_registry,
        &mut terminal_rows,
        &mut terminal_cols,
        &mut theme,
    );

    ctx.cycle_theme(1);
    assert_ne!(theme, previous);
}

#[test]
fn toggle_hud_panel_recording_only_toggles_and_reports_status() {
    let mut config = OverlayConfig::parse_from(["test-app"]);
    let mut voice_manager = VoiceManager::new(config.app.clone());
    let (writer_tx, writer_rx) = bounded(4);
    let mut status_clear_deadline = None;
    let mut current_status = None;
    let mut status_state = StatusLineState::new();
    let mut auto_voice_enabled = false;
    let mut last_auto_trigger_at = None;
    let mut recording_started_at = None;
    let mut preview_clear_deadline = None;
    let mut last_meter_update = Instant::now();
    let button_registry = ButtonRegistry::new();
    let mut terminal_rows = 24;
    let mut terminal_cols = 80;
    let mut theme = Theme::Coral;

    let initial = config.hud_right_panel_recording_only;
    {
        let mut ctx = make_context(
            &mut config,
            &mut voice_manager,
            &writer_tx,
            &mut status_clear_deadline,
            &mut current_status,
            &mut status_state,
            &mut auto_voice_enabled,
            &mut last_auto_trigger_at,
            &mut recording_started_at,
            &mut preview_clear_deadline,
            &mut last_meter_update,
            &button_registry,
            &mut terminal_rows,
            &mut terminal_cols,
            &mut theme,
        );
        ctx.toggle_hud_panel_recording_only();
    }
    assert_eq!(config.hud_right_panel_recording_only, !initial);
    assert_eq!(status_state.hud_right_panel_recording_only, !initial);
    match writer_rx
        .recv_timeout(Duration::from_millis(200))
        .expect("status message")
    {
        WriterMessage::EnhancedStatus(state) => {
            if !initial {
                assert!(state.message.contains("recording-only"));
            } else {
                assert!(state.message.contains("always on"));
            }
        }
        other => panic!("unexpected writer message: {other:?}"),
    }

    {
        let mut ctx = make_context(
            &mut config,
            &mut voice_manager,
            &writer_tx,
            &mut status_clear_deadline,
            &mut current_status,
            &mut status_state,
            &mut auto_voice_enabled,
            &mut last_auto_trigger_at,
            &mut recording_started_at,
            &mut preview_clear_deadline,
            &mut last_meter_update,
            &button_registry,
            &mut terminal_rows,
            &mut terminal_cols,
            &mut theme,
        );
        ctx.toggle_hud_panel_recording_only();
    }
    assert_eq!(config.hud_right_panel_recording_only, initial);
    assert_eq!(status_state.hud_right_panel_recording_only, initial);
    match writer_rx
        .recv_timeout(Duration::from_millis(200))
        .expect("status message")
    {
        WriterMessage::EnhancedStatus(state) => {
            if !initial {
                assert!(state.message.contains("always on"));
            } else {
                assert!(state.message.contains("recording-only"));
            }
        }
        other => panic!("unexpected writer message: {other:?}"),
    }
}

#[test]
fn toggle_mouse_toggles_state_and_emits_enable_disable_messages() {
    let mut config = OverlayConfig::parse_from(["test-app"]);
    let mut voice_manager = VoiceManager::new(config.app.clone());
    let (writer_tx, writer_rx) = bounded(8);
    let mut status_clear_deadline = None;
    let mut current_status = None;
    let mut status_state = StatusLineState::new();
    status_state.mouse_enabled = false;
    let mut auto_voice_enabled = false;
    let mut last_auto_trigger_at = None;
    let mut recording_started_at = None;
    let mut preview_clear_deadline = None;
    let mut last_meter_update = Instant::now();
    let button_registry = ButtonRegistry::new();
    let mut terminal_rows = 24;
    let mut terminal_cols = 80;
    let mut theme = Theme::Coral;

    {
        let mut ctx = make_context(
            &mut config,
            &mut voice_manager,
            &writer_tx,
            &mut status_clear_deadline,
            &mut current_status,
            &mut status_state,
            &mut auto_voice_enabled,
            &mut last_auto_trigger_at,
            &mut recording_started_at,
            &mut preview_clear_deadline,
            &mut last_meter_update,
            &button_registry,
            &mut terminal_rows,
            &mut terminal_cols,
            &mut theme,
        );
        ctx.toggle_mouse();
    }
    assert!(status_state.mouse_enabled);
    match writer_rx
        .recv_timeout(Duration::from_millis(200))
        .expect("mouse enable message")
    {
        WriterMessage::EnableMouse => {}
        other => panic!("unexpected writer message: {other:?}"),
    }
    match writer_rx
        .recv_timeout(Duration::from_millis(200))
        .expect("mouse status message")
    {
        WriterMessage::EnhancedStatus(state) => {
            assert!(state.message.contains("Mouse: ON"));
        }
        other => panic!("unexpected writer message: {other:?}"),
    }

    status_state.hud_button_focus = Some(ButtonAction::VoiceTrigger);
    {
        let mut ctx = make_context(
            &mut config,
            &mut voice_manager,
            &writer_tx,
            &mut status_clear_deadline,
            &mut current_status,
            &mut status_state,
            &mut auto_voice_enabled,
            &mut last_auto_trigger_at,
            &mut recording_started_at,
            &mut preview_clear_deadline,
            &mut last_meter_update,
            &button_registry,
            &mut terminal_rows,
            &mut terminal_cols,
            &mut theme,
        );
        ctx.toggle_mouse();
    }
    assert!(!status_state.mouse_enabled);
    assert!(button_registry.all_buttons().is_empty());
    assert!(status_state.hud_button_focus.is_none());
    match writer_rx
        .recv_timeout(Duration::from_millis(200))
        .expect("mouse disable message")
    {
        WriterMessage::DisableMouse => {}
        other => panic!("unexpected writer message: {other:?}"),
    }
    match writer_rx
        .recv_timeout(Duration::from_millis(200))
        .expect("mouse off status message")
    {
        WriterMessage::EnhancedStatus(state) => {
            assert!(state.message.contains("Mouse: OFF"));
        }
        other => panic!("unexpected writer message: {other:?}"),
    }
}
