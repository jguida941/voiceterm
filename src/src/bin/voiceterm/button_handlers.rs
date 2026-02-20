//! Button-action handlers so HUD interactions mutate runtime state consistently.

use std::time::{Duration, Instant};

use crossbeam_channel::Sender;
use voiceterm::pty_session::PtyOverlaySession;
use voiceterm::VoiceCaptureTrigger;

use crate::buttons::{ButtonAction, ButtonRegistry};
use crate::config::{HudStyle, OverlayConfig};
use crate::log_debug;
use crate::overlays::{
    show_help_overlay, show_settings_overlay, show_theme_studio_overlay, OverlayMode,
};
use crate::settings::SettingsMenuState;
use crate::settings_handlers::{
    SettingsActionContext, SettingsHudContext, SettingsStatusContext, SettingsVoiceContext,
};
use crate::status_line::{get_button_positions, status_banner_height_for_state, StatusLineState};
use crate::terminal::{resolved_cols, update_pty_winsize};
use crate::theme::{runtime_style_pack_overrides, Theme};
use crate::theme_studio::{ThemeStudioView, THEME_STUDIO_ITEMS};
use crate::voice_control::{reset_capture_visuals, start_voice_capture, VoiceManager};
use crate::writer::{send_enhanced_status, set_status, WriterMessage};

pub(crate) struct ButtonActionContext<'a> {
    pub(crate) overlay_mode: &'a mut OverlayMode,
    pub(crate) settings_menu: &'a mut SettingsMenuState,
    pub(crate) theme_studio_selected: &'a mut usize,
    pub(crate) config: &'a mut OverlayConfig,
    pub(crate) status_state: &'a mut StatusLineState,
    pub(crate) auto_voice_enabled: &'a mut bool,
    pub(crate) auto_voice_paused_by_user: &'a mut bool,
    pub(crate) voice_manager: &'a mut VoiceManager,
    pub(crate) session: &'a mut PtyOverlaySession,
    pub(crate) writer_tx: &'a Sender<WriterMessage>,
    pub(crate) status_clear_deadline: &'a mut Option<Instant>,
    pub(crate) current_status: &'a mut Option<String>,
    pub(crate) recording_started_at: &'a mut Option<Instant>,
    pub(crate) preview_clear_deadline: &'a mut Option<Instant>,
    pub(crate) last_meter_update: &'a mut Instant,
    pub(crate) last_auto_trigger_at: &'a mut Option<Instant>,
    pub(crate) terminal_rows: &'a mut u16,
    pub(crate) terminal_cols: &'a mut u16,
    pub(crate) backend_label: &'a str,
    pub(crate) theme: &'a mut Theme,
    pub(crate) button_registry: &'a ButtonRegistry,
}

impl<'a> ButtonActionContext<'a> {
    pub(crate) fn handle_action(&mut self, action: ButtonAction) {
        if *self.overlay_mode != OverlayMode::None {
            return;
        }

        match action {
            ButtonAction::VoiceTrigger => {
                if self.status_state.recording_state
                    == crate::status_line::RecordingState::Recording
                {
                    if self.voice_manager.cancel_capture() {
                        if *self.auto_voice_enabled {
                            *self.auto_voice_paused_by_user = true;
                        }
                        self.status_state.recording_state =
                            crate::status_line::RecordingState::Idle;
                        crate::voice_control::clear_capture_metrics(self.status_state);
                        *self.recording_started_at = None;
                        set_status(
                            self.writer_tx,
                            self.status_clear_deadline,
                            self.current_status,
                            self.status_state,
                            "Capture stopped",
                            Some(Duration::from_secs(2)),
                        );
                    }
                } else {
                    let trigger = if *self.auto_voice_enabled {
                        VoiceCaptureTrigger::Auto
                    } else {
                        VoiceCaptureTrigger::Manual
                    };
                    if let Err(err) = start_voice_capture(
                        self.voice_manager,
                        trigger,
                        self.writer_tx,
                        self.status_clear_deadline,
                        self.current_status,
                        self.status_state,
                    ) {
                        set_status(
                            self.writer_tx,
                            self.status_clear_deadline,
                            self.current_status,
                            self.status_state,
                            &crate::status_messages::with_log_path("Voice capture failed"),
                            Some(Duration::from_secs(2)),
                        );
                        log_debug(&format!("voice capture failed: {err:#}"));
                    } else {
                        *self.auto_voice_paused_by_user = false;
                        *self.recording_started_at = Some(Instant::now());
                        reset_capture_visuals(
                            self.status_state,
                            self.preview_clear_deadline,
                            self.last_meter_update,
                        );
                    }
                }
            }
            ButtonAction::ToggleAutoVoice => {
                self.toggle_auto_voice();
            }
            ButtonAction::ToggleSendMode => {
                self.toggle_send_mode();
            }
            ButtonAction::SettingsToggle => {
                self.open_settings_overlay();
            }
            ButtonAction::ToggleHudStyle => {
                if self.status_state.hud_style == HudStyle::Hidden
                    && self.status_state.hidden_launcher_collapsed
                {
                    self.status_state.hidden_launcher_collapsed = false;
                } else {
                    self.with_settings_context(|settings_ctx| settings_ctx.cycle_hud_style(1));
                }
            }
            ButtonAction::CollapseHiddenLauncher => {
                self.status_state.hidden_launcher_collapsed = true;
            }
            ButtonAction::HudBack => {
                self.with_settings_context(|settings_ctx| settings_ctx.cycle_hud_style(-1));
            }
            ButtonAction::HelpToggle => {
                self.open_help_overlay();
            }
            ButtonAction::ThemePicker => {
                self.open_theme_studio_overlay();
            }
        }

        if self.status_state.mouse_enabled {
            update_button_registry(
                self.button_registry,
                self.status_state,
                *self.overlay_mode,
                *self.terminal_cols,
                *self.theme,
            );
        }
    }

    fn with_settings_context<F>(&mut self, apply: F)
    where
        F: for<'ctx> FnOnce(&mut SettingsActionContext<'ctx>),
    {
        let mut settings_ctx = self.settings_context();
        apply(&mut settings_ctx);
    }

    fn toggle_auto_voice(&mut self) {
        let mut settings_ctx = self.settings_context();
        settings_ctx.toggle_auto_voice();
    }

    fn toggle_send_mode(&mut self) {
        let mut settings_ctx = self.settings_context();
        settings_ctx.toggle_send_mode();
    }

    fn sync_overlay_winsize(&mut self) {
        update_pty_winsize(
            self.session,
            self.terminal_rows,
            self.terminal_cols,
            *self.overlay_mode,
            self.status_state.hud_style,
            self.status_state.claude_prompt_suppressed,
        );
    }

    fn open_settings_overlay(&mut self) {
        *self.overlay_mode = OverlayMode::Settings;
        self.sync_overlay_winsize();
        let cols = resolved_cols(*self.terminal_cols);
        show_settings_overlay(
            self.writer_tx,
            *self.theme,
            cols,
            self.settings_menu,
            self.config,
            self.status_state,
            self.backend_label,
        );
    }

    fn open_help_overlay(&mut self) {
        *self.overlay_mode = OverlayMode::Help;
        self.sync_overlay_winsize();
        let cols = resolved_cols(*self.terminal_cols);
        show_help_overlay(self.writer_tx, *self.theme, cols);
    }

    fn open_theme_studio_overlay(&mut self) {
        *self.overlay_mode = OverlayMode::ThemeStudio;
        self.sync_overlay_winsize();
        let cols = resolved_cols(*self.terminal_cols);
        if THEME_STUDIO_ITEMS.is_empty() {
            *self.theme_studio_selected = 0;
        } else {
            *self.theme_studio_selected =
                (*self.theme_studio_selected).min(THEME_STUDIO_ITEMS.len().saturating_sub(1));
        }
        let style_pack_overrides = runtime_style_pack_overrides();
        let view = ThemeStudioView {
            theme: *self.theme,
            selected: *self.theme_studio_selected,
            hud_style: self.status_state.hud_style,
            hud_border_style: self.config.hud_border_style,
            hud_right_panel: self.config.hud_right_panel,
            hud_right_panel_recording_only: self.config.hud_right_panel_recording_only,
            border_style_override: style_pack_overrides.border_style_override,
            glyph_set_override: style_pack_overrides.glyph_set_override,
            indicator_set_override: style_pack_overrides.indicator_set_override,
        };
        show_theme_studio_overlay(self.writer_tx, &view, cols);
    }

    fn settings_context(&mut self) -> SettingsActionContext<'_> {
        SettingsActionContext {
            config: &mut *self.config,
            status: SettingsStatusContext {
                status_state: &mut *self.status_state,
                writer_tx: self.writer_tx,
                status_clear_deadline: &mut *self.status_clear_deadline,
                current_status: &mut *self.current_status,
                preview_clear_deadline: &mut *self.preview_clear_deadline,
                last_meter_update: &mut *self.last_meter_update,
            },
            voice: SettingsVoiceContext {
                auto_voice_enabled: &mut *self.auto_voice_enabled,
                auto_voice_paused_by_user: Some(&mut *self.auto_voice_paused_by_user),
                voice_manager: &mut *self.voice_manager,
                last_auto_trigger_at: &mut *self.last_auto_trigger_at,
                recording_started_at: &mut *self.recording_started_at,
            },
            hud: SettingsHudContext {
                button_registry: self.button_registry,
                overlay_mode: *self.overlay_mode,
                terminal_rows: &mut *self.terminal_rows,
                terminal_cols: &mut *self.terminal_cols,
                theme: &mut *self.theme,
                pty_session: Some(&mut *self.session),
            },
        }
    }
}

pub(crate) fn update_button_registry(
    registry: &ButtonRegistry,
    status_state: &StatusLineState,
    overlay_mode: OverlayMode,
    terminal_cols: u16,
    theme: Theme,
) {
    registry.clear();
    if overlay_mode != OverlayMode::None {
        registry.set_hud_offset(0);
        return;
    }
    let banner_height = status_banner_height_for_state(terminal_cols as usize, status_state);
    registry.set_hud_offset(banner_height as u16);
    let positions = get_button_positions(status_state, theme, terminal_cols as usize);
    for pos in positions {
        registry.register(pos.start_x, pos.end_x, pos.row, pos.action);
    }
}

pub(crate) fn advance_hud_button_focus(
    status_state: &mut StatusLineState,
    overlay_mode: OverlayMode,
    terminal_cols: u16,
    theme: Theme,
    direction: i32,
) -> bool {
    let actions = visible_button_actions(status_state, overlay_mode, terminal_cols, theme);
    if actions.is_empty() {
        if status_state.hud_button_focus.is_some() {
            status_state.hud_button_focus = None;
            return true;
        }
        return false;
    }

    let idx = match status_state
        .hud_button_focus
        .and_then(|action| actions.iter().position(|candidate| *candidate == action))
    {
        Some(current_idx) => {
            let len_i64 = i64::try_from(actions.len()).unwrap_or(1);
            let current_i64 = i64::try_from(current_idx).unwrap_or(0);
            let next_i64 = (current_i64 + i64::from(direction)).rem_euclid(len_i64);
            usize::try_from(next_i64).unwrap_or(0)
        }
        None => {
            if direction >= 0 {
                0
            } else {
                actions.len().saturating_sub(1)
            }
        }
    };

    let next_action = actions[idx];
    if status_state.hud_button_focus == Some(next_action) {
        return false;
    }
    status_state.hud_button_focus = Some(next_action);
    true
}

pub(crate) fn send_enhanced_status_with_buttons(
    writer_tx: &Sender<WriterMessage>,
    button_registry: &ButtonRegistry,
    status_state: &StatusLineState,
    overlay_mode: OverlayMode,
    terminal_cols: u16,
    theme: Theme,
) {
    send_enhanced_status(writer_tx, status_state);
    if status_state.mouse_enabled {
        update_button_registry(
            button_registry,
            status_state,
            overlay_mode,
            terminal_cols,
            theme,
        );
    }
}

fn visible_button_actions(
    status_state: &StatusLineState,
    overlay_mode: OverlayMode,
    terminal_cols: u16,
    theme: Theme,
) -> Vec<ButtonAction> {
    if overlay_mode != OverlayMode::None {
        return Vec::new();
    }
    let mut positions = get_button_positions(status_state, theme, terminal_cols as usize);
    positions.sort_by_key(|pos| pos.start_x);
    positions.into_iter().map(|pos| pos.action).collect()
}
