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
use crate::status_line::{RecordingState, StatusLineState, VoiceMode, WakeWordHudState};
use crate::terminal::update_pty_winsize;
use crate::theme::Theme;
use crate::theme_ops::{apply_theme_selection, cycle_theme};
use crate::voice_control::{
    clear_capture_metrics, reset_capture_visuals, start_voice_capture, VoiceManager,
};
use crate::writer::{set_status, try_send_message, WriterMessage};

const WAKE_WORD_SENSITIVITY_MIN: f32 = 0.0;
const WAKE_WORD_SENSITIVITY_MAX: f32 = 1.0;
const WAKE_WORD_COOLDOWN_OPTIONS_MS: &[u64] = &[500, 1000, 1500, 2000, 3000, 5000, 8000, 10_000];

pub(crate) struct SettingsStatusContext<'a> {
    pub(crate) status_state: &'a mut StatusLineState,
    pub(crate) writer_tx: &'a Sender<WriterMessage>,
    pub(crate) status_clear_deadline: &'a mut Option<Instant>,
    pub(crate) current_status: &'a mut Option<String>,
    pub(crate) preview_clear_deadline: &'a mut Option<Instant>,
    pub(crate) last_meter_update: &'a mut Instant,
}

pub(crate) struct SettingsVoiceContext<'a> {
    pub(crate) auto_voice_enabled: &'a mut bool,
    pub(crate) voice_manager: &'a mut VoiceManager,
    pub(crate) last_auto_trigger_at: &'a mut Option<Instant>,
    pub(crate) recording_started_at: &'a mut Option<Instant>,
}

pub(crate) struct SettingsHudContext<'a> {
    pub(crate) button_registry: &'a ButtonRegistry,
    pub(crate) overlay_mode: OverlayMode,
    pub(crate) terminal_rows: &'a mut u16,
    pub(crate) terminal_cols: &'a mut u16,
    pub(crate) theme: &'a mut Theme,
    pub(crate) pty_session: Option<&'a mut PtyOverlaySession>,
}

pub(crate) struct SettingsActionContext<'a> {
    pub(crate) config: &'a mut OverlayConfig,
    pub(crate) status: SettingsStatusContext<'a>,
    pub(crate) voice: SettingsVoiceContext<'a>,
    pub(crate) hud: SettingsHudContext<'a>,
}

impl SettingsActionContext<'_> {
    fn set_transient_status(&mut self, msg: &str, ttl: Duration) {
        set_status(
            self.status.writer_tx,
            self.status.status_clear_deadline,
            self.status.current_status,
            self.status.status_state,
            msg,
            Some(ttl),
        );
    }

    fn reset_voice_visuals(&mut self) {
        reset_capture_visuals(
            self.status.status_state,
            self.status.preview_clear_deadline,
            self.status.last_meter_update,
        );
    }

    pub(crate) fn toggle_auto_voice(&mut self) {
        *self.voice.auto_voice_enabled = !*self.voice.auto_voice_enabled;
        self.status.status_state.auto_voice_enabled = *self.voice.auto_voice_enabled;
        self.status.status_state.voice_mode = if *self.voice.auto_voice_enabled {
            VoiceMode::Auto
        } else {
            VoiceMode::Manual
        };
        let msg = if *self.voice.auto_voice_enabled {
            if self.voice.voice_manager.is_idle() {
                if let Err(err) = start_voice_capture(
                    self.voice.voice_manager,
                    VoiceCaptureTrigger::Auto,
                    self.status.writer_tx,
                    self.status.status_clear_deadline,
                    self.status.current_status,
                    self.status.status_state,
                ) {
                    log_debug(&format!("auto voice capture failed: {err:#}"));
                } else {
                    let now = Instant::now();
                    *self.voice.last_auto_trigger_at = Some(now);
                    *self.voice.recording_started_at = Some(now);
                    self.reset_voice_visuals();
                }
            }
            "Auto-voice enabled"
        } else {
            let cancelled = self.voice.voice_manager.cancel_capture();
            if cancelled {
                self.status.status_state.recording_state = RecordingState::Idle;
                *self.voice.recording_started_at = None;
            }
            clear_capture_metrics(self.status.status_state);
            self.reset_voice_visuals();
            if cancelled {
                "Auto-voice disabled (capture cancelled)"
            } else {
                "Auto-voice disabled"
            }
        };
        self.set_transient_status(msg, Duration::from_secs(2));
    }

    pub(crate) fn toggle_wake_word(&mut self) {
        self.config.wake_word = !self.config.wake_word;
        self.status.status_state.wake_word_state = if self.config.wake_word {
            if self.voice.voice_manager.is_idle() {
                WakeWordHudState::Listening
            } else {
                WakeWordHudState::Paused
            }
        } else {
            WakeWordHudState::Off
        };
        let msg = if self.config.wake_word {
            "Wake word: ON"
        } else {
            "Wake word: OFF"
        };
        self.set_transient_status(msg, Duration::from_secs(2));
    }

    pub(crate) fn adjust_wake_word_sensitivity(&mut self, delta: f32) {
        let next = (self.config.wake_word_sensitivity + delta)
            .clamp(WAKE_WORD_SENSITIVITY_MIN, WAKE_WORD_SENSITIVITY_MAX);
        self.config.wake_word_sensitivity = (next * 100.0).round() / 100.0;
        let percent = self.config.wake_word_sensitivity * 100.0;
        let direction = if delta >= 0.0 {
            "more sensitive"
        } else {
            "less sensitive"
        };
        let msg = format!("Wake-word sensitivity: {percent:.0}% ({direction})");
        self.set_transient_status(&msg, Duration::from_secs(3));
    }

    pub(crate) fn cycle_wake_word_cooldown(&mut self, direction: i32) {
        self.config.wake_word_cooldown_ms = cycle_option(
            WAKE_WORD_COOLDOWN_OPTIONS_MS,
            self.config.wake_word_cooldown_ms,
            direction,
        );
        let msg = format!(
            "Wake-word cooldown: {} ms",
            self.config.wake_word_cooldown_ms
        );
        self.set_transient_status(&msg, Duration::from_secs(3));
    }

    pub(crate) fn toggle_send_mode(&mut self) {
        self.config.voice_send_mode = match self.config.voice_send_mode {
            VoiceSendMode::Auto => VoiceSendMode::Insert,
            VoiceSendMode::Insert => VoiceSendMode::Auto,
        };
        self.status.status_state.send_mode = self.config.voice_send_mode;
        if self.config.voice_send_mode == VoiceSendMode::Auto {
            self.status.status_state.insert_pending_send = false;
        }
        let msg = match self.config.voice_send_mode {
            VoiceSendMode::Auto => "Send mode: auto (sends Enter)",
            VoiceSendMode::Insert => "Edit mode: press Enter to send",
        };
        self.set_transient_status(msg, Duration::from_secs(3));
    }

    pub(crate) fn toggle_macros_enabled(&mut self) {
        self.status.status_state.macros_enabled = !self.status.status_state.macros_enabled;
        let msg = if self.status.status_state.macros_enabled {
            "Macros: ON"
        } else {
            "Macros: OFF"
        };
        self.set_transient_status(msg, Duration::from_secs(3));
    }

    pub(crate) fn adjust_sensitivity(&mut self, delta_db: f32) {
        let threshold_db = self.voice.voice_manager.adjust_sensitivity(delta_db);
        self.status.status_state.sensitivity_db = threshold_db;
        let direction = if delta_db >= 0.0 {
            "less sensitive"
        } else {
            "more sensitive"
        };
        let msg = format!("Mic sensitivity: {threshold_db:.0} dB ({direction})");
        self.set_transient_status(&msg, Duration::from_secs(3));
    }

    pub(crate) fn cycle_theme(&mut self, direction: i32) {
        let next = cycle_theme(*self.hud.theme, direction);
        *self.hud.theme = apply_theme_selection(
            self.config,
            next,
            self.status.writer_tx,
            self.status.status_clear_deadline,
            self.status.current_status,
            self.status.status_state,
        );
    }

    pub(crate) fn cycle_hud_panel(&mut self, direction: i32) {
        self.config.hud_right_panel = cycle_hud_right_panel(self.config.hud_right_panel, direction);
        self.status.status_state.hud_right_panel = self.config.hud_right_panel;
        let label = format!("HUD right panel: {}", self.config.hud_right_panel);
        self.set_transient_status(&label, Duration::from_secs(2));
    }

    pub(crate) fn cycle_hud_border_style(&mut self, direction: i32) {
        self.config.hud_border_style =
            cycle_hud_border_style(self.config.hud_border_style, direction);
        self.status.status_state.hud_border_style = self.config.hud_border_style;
        let label = format!("HUD borders: {}", self.config.hud_border_style);
        self.set_transient_status(&label, Duration::from_secs(2));
    }

    pub(crate) fn cycle_hud_style(&mut self, direction: i32) {
        self.status.status_state.hud_style =
            cycle_hud_style(self.status.status_state.hud_style, direction);
        self.status.status_state.hidden_launcher_collapsed = false;
        let label = format!("HUD style: {}", self.status.status_state.hud_style);
        self.set_transient_status(&label, Duration::from_secs(2));
        if let Some(session) = self.hud.pty_session.as_mut() {
            update_pty_winsize(
                session,
                self.hud.terminal_rows,
                self.hud.terminal_cols,
                self.hud.overlay_mode,
                self.status.status_state.hud_style,
            );
        }
    }

    pub(crate) fn toggle_hud_panel_recording_only(&mut self) {
        self.config.hud_right_panel_recording_only = !self.config.hud_right_panel_recording_only;
        self.status.status_state.hud_right_panel_recording_only =
            self.config.hud_right_panel_recording_only;
        let label = if self.config.hud_right_panel_recording_only {
            "HUD right panel: recording-only"
        } else {
            "HUD right panel: always on"
        };
        self.set_transient_status(label, Duration::from_secs(2));
    }

    pub(crate) fn cycle_latency_display(&mut self, direction: i32) {
        self.config.latency_display = cycle_latency_display(self.config.latency_display, direction);
        self.status.status_state.latency_display = self.config.latency_display;
        let label = match self.config.latency_display {
            LatencyDisplayMode::Off => "Latency display: OFF",
            LatencyDisplayMode::Short => "Latency display: Nms",
            LatencyDisplayMode::Label => "Latency display: Latency: Nms",
        };
        self.set_transient_status(label, Duration::from_secs(2));
    }

    pub(crate) fn toggle_mouse(&mut self) {
        self.status.status_state.mouse_enabled = !self.status.status_state.mouse_enabled;
        if self.status.status_state.mouse_enabled {
            let _ = try_send_message(self.status.writer_tx, WriterMessage::EnableMouse);
            update_button_registry(
                self.hud.button_registry,
                self.status.status_state,
                self.hud.overlay_mode,
                *self.hud.terminal_cols,
                *self.hud.theme,
            );
            self.set_transient_status("Mouse: ON - click HUD buttons", Duration::from_secs(2));
        } else {
            let _ = try_send_message(self.status.writer_tx, WriterMessage::DisableMouse);
            self.hud.button_registry.clear();
            self.status.status_state.hud_button_focus = None;
            self.set_transient_status("Mouse: OFF", Duration::from_secs(2));
        }
    }
}

fn cycle_option<T>(options: &[T], current: T, direction: i32) -> T
where
    T: Copy + PartialEq,
{
    let len = options.len();
    if len == 0 {
        return current;
    }
    let idx = options
        .iter()
        .position(|item| *item == current)
        .unwrap_or(0);
    let len_i64 = i64::try_from(len).unwrap_or(1);
    let idx_i64 = i64::try_from(idx).unwrap_or(0);
    let next_i64 = (idx_i64 + i64::from(direction)).rem_euclid(len_i64);
    let next = usize::try_from(next_i64).unwrap_or(0);
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
