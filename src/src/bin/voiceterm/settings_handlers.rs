//! Settings action handlers so runtime config and HUD state change atomically.

use std::time::{Duration, Instant};

use crossbeam_channel::Sender;
use voiceterm::pty_session::PtyOverlaySession;
use voiceterm::VoiceCaptureTrigger;

use crate::button_handlers::update_button_registry;
use crate::buttons::ButtonRegistry;
use crate::config::{
    HudBorderStyle, HudRightPanel, HudStyle, LatencyDisplayMode, OverlayConfig, VoiceSendMode,
};
use crate::log_debug;
use crate::overlays::OverlayMode;
use crate::status_line::{RecordingState, StatusLineState, VoiceMode};
use crate::terminal::update_pty_winsize;
use crate::theme::Theme;
use crate::theme_ops::{apply_theme_selection, cycle_theme};
use crate::voice_control::{
    clear_capture_metrics, reset_capture_visuals, start_voice_capture, VoiceManager,
};
use crate::writer::{set_status, try_send_message, WriterMessage};

pub(crate) struct SettingsActionContext<'a> {
    pub(crate) config: &'a mut OverlayConfig,
    pub(crate) status_state: &'a mut StatusLineState,
    pub(crate) auto_voice_enabled: &'a mut bool,
    pub(crate) voice_manager: &'a mut VoiceManager,
    pub(crate) writer_tx: &'a Sender<WriterMessage>,
    pub(crate) status_clear_deadline: &'a mut Option<Instant>,
    pub(crate) current_status: &'a mut Option<String>,
    pub(crate) last_auto_trigger_at: &'a mut Option<Instant>,
    pub(crate) recording_started_at: &'a mut Option<Instant>,
    pub(crate) preview_clear_deadline: &'a mut Option<Instant>,
    pub(crate) last_meter_update: &'a mut Instant,
    pub(crate) button_registry: &'a ButtonRegistry,
    pub(crate) overlay_mode: OverlayMode,
    pub(crate) terminal_rows: &'a mut u16,
    pub(crate) terminal_cols: &'a mut u16,
    pub(crate) theme: &'a mut Theme,
    pub(crate) pty_session: Option<&'a mut PtyOverlaySession>,
}

impl<'a> SettingsActionContext<'a> {
    #[allow(clippy::too_many_arguments)]
    pub(crate) fn new(
        config: &'a mut OverlayConfig,
        status_state: &'a mut StatusLineState,
        auto_voice_enabled: &'a mut bool,
        voice_manager: &'a mut VoiceManager,
        writer_tx: &'a Sender<WriterMessage>,
        status_clear_deadline: &'a mut Option<Instant>,
        current_status: &'a mut Option<String>,
        last_auto_trigger_at: &'a mut Option<Instant>,
        recording_started_at: &'a mut Option<Instant>,
        preview_clear_deadline: &'a mut Option<Instant>,
        last_meter_update: &'a mut Instant,
        button_registry: &'a ButtonRegistry,
        overlay_mode: OverlayMode,
        terminal_rows: &'a mut u16,
        terminal_cols: &'a mut u16,
        theme: &'a mut Theme,
        pty_session: Option<&'a mut PtyOverlaySession>,
    ) -> Self {
        Self {
            config,
            status_state,
            auto_voice_enabled,
            voice_manager,
            writer_tx,
            status_clear_deadline,
            current_status,
            last_auto_trigger_at,
            recording_started_at,
            preview_clear_deadline,
            last_meter_update,
            button_registry,
            overlay_mode,
            terminal_rows,
            terminal_cols,
            theme,
            pty_session,
        }
    }

    pub(crate) fn toggle_auto_voice(&mut self) {
        *self.auto_voice_enabled = !*self.auto_voice_enabled;
        self.status_state.auto_voice_enabled = *self.auto_voice_enabled;
        self.status_state.voice_mode = if *self.auto_voice_enabled {
            VoiceMode::Auto
        } else {
            VoiceMode::Manual
        };
        let msg = if *self.auto_voice_enabled {
            if self.voice_manager.is_idle() {
                if let Err(err) = start_voice_capture(
                    self.voice_manager,
                    VoiceCaptureTrigger::Auto,
                    self.writer_tx,
                    self.status_clear_deadline,
                    self.current_status,
                    self.status_state,
                ) {
                    log_debug(&format!("auto voice capture failed: {err:#}"));
                } else {
                    let now = Instant::now();
                    *self.last_auto_trigger_at = Some(now);
                    *self.recording_started_at = Some(now);
                    reset_capture_visuals(
                        self.status_state,
                        self.preview_clear_deadline,
                        self.last_meter_update,
                    );
                }
            }
            "Auto-voice enabled"
        } else {
            let cancelled = self.voice_manager.cancel_capture();
            if cancelled {
                self.status_state.recording_state = RecordingState::Idle;
                *self.recording_started_at = None;
            }
            clear_capture_metrics(self.status_state);
            reset_capture_visuals(
                self.status_state,
                self.preview_clear_deadline,
                self.last_meter_update,
            );
            if cancelled {
                "Auto-voice disabled (capture cancelled)"
            } else {
                "Auto-voice disabled"
            }
        };
        set_status(
            self.writer_tx,
            self.status_clear_deadline,
            self.current_status,
            self.status_state,
            msg,
            Some(Duration::from_secs(2)),
        );
    }

    pub(crate) fn toggle_send_mode(&mut self) {
        self.config.voice_send_mode = match self.config.voice_send_mode {
            VoiceSendMode::Auto => VoiceSendMode::Insert,
            VoiceSendMode::Insert => VoiceSendMode::Auto,
        };
        self.status_state.send_mode = self.config.voice_send_mode;
        let msg = match self.config.voice_send_mode {
            VoiceSendMode::Auto => "Send mode: auto (sends Enter)",
            VoiceSendMode::Insert => "Edit mode: press Enter to send",
        };
        set_status(
            self.writer_tx,
            self.status_clear_deadline,
            self.current_status,
            self.status_state,
            msg,
            Some(Duration::from_secs(3)),
        );
    }

    pub(crate) fn toggle_macros_enabled(&mut self) {
        self.status_state.macros_enabled = !self.status_state.macros_enabled;
        let msg = if self.status_state.macros_enabled {
            "Macros: ON"
        } else {
            "Macros: OFF"
        };
        set_status(
            self.writer_tx,
            self.status_clear_deadline,
            self.current_status,
            self.status_state,
            msg,
            Some(Duration::from_secs(3)),
        );
    }

    pub(crate) fn adjust_sensitivity(&mut self, delta_db: f32) {
        let threshold_db = self.voice_manager.adjust_sensitivity(delta_db);
        self.status_state.sensitivity_db = threshold_db;
        let direction = if delta_db >= 0.0 {
            "less sensitive"
        } else {
            "more sensitive"
        };
        let msg = format!("Mic sensitivity: {threshold_db:.0} dB ({direction})");
        set_status(
            self.writer_tx,
            self.status_clear_deadline,
            self.current_status,
            self.status_state,
            &msg,
            Some(Duration::from_secs(3)),
        );
    }

    pub(crate) fn cycle_theme(&mut self, direction: i32) {
        let next = cycle_theme(*self.theme, direction);
        *self.theme = apply_theme_selection(
            self.config,
            next,
            self.writer_tx,
            self.status_clear_deadline,
            self.current_status,
            self.status_state,
        );
    }

    pub(crate) fn update_hud_panel(&mut self, direction: i32) {
        self.config.hud_right_panel = cycle_hud_right_panel(self.config.hud_right_panel, direction);
        self.status_state.hud_right_panel = self.config.hud_right_panel;
        let label = format!("HUD right panel: {}", self.config.hud_right_panel);
        set_status(
            self.writer_tx,
            self.status_clear_deadline,
            self.current_status,
            self.status_state,
            &label,
            Some(Duration::from_secs(2)),
        );
    }

    pub(crate) fn update_hud_border_style(&mut self, direction: i32) {
        self.config.hud_border_style =
            cycle_hud_border_style(self.config.hud_border_style, direction);
        self.status_state.hud_border_style = self.config.hud_border_style;
        let label = format!("HUD borders: {}", self.config.hud_border_style);
        set_status(
            self.writer_tx,
            self.status_clear_deadline,
            self.current_status,
            self.status_state,
            &label,
            Some(Duration::from_secs(2)),
        );
    }

    pub(crate) fn update_hud_style(&mut self, direction: i32) {
        self.status_state.hud_style = cycle_hud_style(self.status_state.hud_style, direction);
        let label = format!("HUD style: {}", self.status_state.hud_style);
        set_status(
            self.writer_tx,
            self.status_clear_deadline,
            self.current_status,
            self.status_state,
            &label,
            Some(Duration::from_secs(2)),
        );
        if let Some(session) = self.pty_session.as_mut() {
            update_pty_winsize(
                session,
                self.terminal_rows,
                self.terminal_cols,
                self.overlay_mode,
                self.status_state.hud_style,
            );
        }
    }

    pub(crate) fn toggle_hud_panel_recording_only(&mut self) {
        self.config.hud_right_panel_recording_only = !self.config.hud_right_panel_recording_only;
        self.status_state.hud_right_panel_recording_only =
            self.config.hud_right_panel_recording_only;
        let label = if self.config.hud_right_panel_recording_only {
            "HUD right panel: recording-only"
        } else {
            "HUD right panel: always on"
        };
        set_status(
            self.writer_tx,
            self.status_clear_deadline,
            self.current_status,
            self.status_state,
            label,
            Some(Duration::from_secs(2)),
        );
    }

    pub(crate) fn cycle_latency_display(&mut self, direction: i32) {
        self.config.latency_display = cycle_latency_display(self.config.latency_display, direction);
        self.status_state.latency_display = self.config.latency_display;
        let label = match self.config.latency_display {
            LatencyDisplayMode::Off => "Latency display: OFF",
            LatencyDisplayMode::Short => "Latency display: Nms",
            LatencyDisplayMode::Label => "Latency display: Latency: Nms",
        };
        set_status(
            self.writer_tx,
            self.status_clear_deadline,
            self.current_status,
            self.status_state,
            label,
            Some(Duration::from_secs(2)),
        );
    }

    pub(crate) fn toggle_mouse(&mut self) {
        self.status_state.mouse_enabled = !self.status_state.mouse_enabled;
        if self.status_state.mouse_enabled {
            let _ = try_send_message(self.writer_tx, WriterMessage::EnableMouse);
            update_button_registry(
                self.button_registry,
                self.status_state,
                self.overlay_mode,
                *self.terminal_cols,
                *self.theme,
            );
            set_status(
                self.writer_tx,
                self.status_clear_deadline,
                self.current_status,
                self.status_state,
                "Mouse: ON - click HUD buttons",
                Some(Duration::from_secs(2)),
            );
        } else {
            let _ = try_send_message(self.writer_tx, WriterMessage::DisableMouse);
            self.button_registry.clear();
            self.status_state.hud_button_focus = None;
            set_status(
                self.writer_tx,
                self.status_clear_deadline,
                self.current_status,
                self.status_state,
                "Mouse: OFF",
                Some(Duration::from_secs(2)),
            );
        }
    }
}

fn cycle_option<T>(options: &[T], current: T, direction: i32) -> T
where
    T: Copy + PartialEq,
{
    let len = options.len() as i32;
    if len == 0 {
        return current;
    }
    let idx = options
        .iter()
        .position(|item| *item == current)
        .unwrap_or(0) as i32;
    let next = (idx + direction).rem_euclid(len) as usize;
    options[next]
}

fn cycle_hud_right_panel(current: HudRightPanel, direction: i32) -> HudRightPanel {
    const OPTIONS: &[HudRightPanel] = &[
        HudRightPanel::Ribbon,
        HudRightPanel::Dots,
        HudRightPanel::Heartbeat,
        HudRightPanel::Off,
    ];
    cycle_option(OPTIONS, current, direction)
}

fn cycle_hud_border_style(current: HudBorderStyle, direction: i32) -> HudBorderStyle {
    const OPTIONS: &[HudBorderStyle] = &[
        HudBorderStyle::Theme,
        HudBorderStyle::Single,
        HudBorderStyle::Rounded,
        HudBorderStyle::Double,
        HudBorderStyle::Heavy,
        HudBorderStyle::None,
    ];
    cycle_option(OPTIONS, current, direction)
}

fn cycle_hud_style(current: HudStyle, direction: i32) -> HudStyle {
    const OPTIONS: &[HudStyle] = &[HudStyle::Full, HudStyle::Minimal, HudStyle::Hidden];
    cycle_option(OPTIONS, current, direction)
}

fn cycle_latency_display(current: LatencyDisplayMode, direction: i32) -> LatencyDisplayMode {
    const OPTIONS: &[LatencyDisplayMode] = &[
        LatencyDisplayMode::Short,
        LatencyDisplayMode::Label,
        LatencyDisplayMode::Off,
    ];
    cycle_option(OPTIONS, current, direction)
}

#[cfg(test)]
mod tests;
