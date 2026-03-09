//! Theme-switch operations so shortcuts and buttons share one mutation path.

use std::time::{Duration, Instant};

use crossbeam_channel::Sender;
use voiceterm::pty_session::PtyOverlaySession;

use crate::color_mode::ColorMode;
use crate::config::OverlayConfig;
use crate::cycle_index::cycle_index;
use crate::overlays::OverlayMode;
use crate::status_line::StatusLineState;
use crate::terminal::update_pty_winsize;
use crate::theme::{style_pack_theme_lock, Theme};
use crate::theme_picker::THEME_OPTIONS;
use crate::writer::{send_message_blocking, set_status, WriterMessage};

pub(crate) fn cycle_theme(current: Theme, direction: i32) -> Theme {
    let len = THEME_OPTIONS.len();
    if len == 0 {
        return current;
    }
    let idx = THEME_OPTIONS
        .iter()
        .position(|(theme, _, _)| *theme == current)
        .unwrap_or(0);
    let next = cycle_index(idx, len, direction);
    THEME_OPTIONS[next].0
}

pub(crate) fn theme_index_from_theme(theme: Theme) -> usize {
    THEME_OPTIONS
        .iter()
        .position(|(candidate, _, _)| *candidate == theme)
        .unwrap_or(0)
}

pub(crate) fn apply_theme_selection(
    config: &mut OverlayConfig,
    requested: Theme,
    writer_tx: &Sender<WriterMessage>,
    status_clear_deadline: &mut Option<Instant>,
    current_status: &mut Option<String>,
    status_state: &mut StatusLineState,
) -> Theme {
    if let Some(locked_theme) = style_pack_theme_lock() {
        send_message_blocking(
            writer_tx,
            WriterMessage::SetTheme(locked_theme),
            "theme ops: apply locked theme",
        );
        let status = format!("Theme locked by VOICETERM_STYLE_PACK_JSON ({locked_theme})");
        set_status(
            writer_tx,
            status_clear_deadline,
            current_status,
            status_state,
            &status,
            Some(Duration::from_secs(2)),
        );
        return locked_theme;
    }

    config.theme_name = Some(requested.to_string());
    let (resolved, note) = resolve_theme_choice(config, requested);
    send_message_blocking(
        writer_tx,
        WriterMessage::SetTheme(resolved),
        "theme ops: apply selected theme",
    );
    let mut status = if resolved == Theme::None && requested != Theme::None {
        "Theme set: none".to_string()
    } else {
        format!("Theme set: {}", requested)
    };
    if let Some(note) = note {
        status = format!("{status} ({note})");
    }
    set_status(
        writer_tx,
        status_clear_deadline,
        current_status,
        status_state,
        &status,
        Some(Duration::from_secs(2)),
    );
    resolved
}

pub(crate) fn theme_picker_parse_index(digits: &str, total: usize) -> Option<usize> {
    if digits.is_empty() {
        return None;
    }
    let value: usize = digits.parse().ok()?;
    if value == 0 || value > total {
        return None;
    }
    Some(value - 1)
}

pub(crate) fn theme_picker_has_longer_match(prefix: &str, total: usize) -> bool {
    if prefix.is_empty() {
        return false;
    }
    (1..=total).any(|idx| {
        let label = idx.to_string();
        label.len() > prefix.len() && label.starts_with(prefix)
    })
}

#[allow(clippy::too_many_arguments)]
pub(crate) fn apply_theme_picker_index(
    idx: usize,
    theme: &mut Theme,
    config: &mut OverlayConfig,
    writer_tx: &Sender<WriterMessage>,
    status_clear_deadline: &mut Option<Instant>,
    current_status: &mut Option<String>,
    status_state: &mut StatusLineState,
    session: &mut PtyOverlaySession,
    terminal_rows: &mut u16,
    terminal_cols: &mut u16,
    overlay_mode: &mut OverlayMode,
) -> bool {
    let Some((_, name, _)) = THEME_OPTIONS.get(idx) else {
        return false;
    };
    let Some(requested) = Theme::from_name(name) else {
        return false;
    };
    *theme = apply_theme_selection(
        config,
        requested,
        writer_tx,
        status_clear_deadline,
        current_status,
        status_state,
    );
    if style_pack_theme_lock().is_some() {
        return false;
    }
    *overlay_mode = OverlayMode::None;
    send_message_blocking(
        writer_tx,
        WriterMessage::ClearOverlay,
        "theme ops: clear overlay after selection",
    );
    update_pty_winsize(
        session,
        terminal_rows,
        terminal_cols,
        *overlay_mode,
        status_state.hud_style,
        status_state.prompt_suppressed,
    );
    true
}

fn resolve_theme_choice(config: &OverlayConfig, requested: Theme) -> (Theme, Option<&'static str>) {
    if config.no_color || std::env::var("NO_COLOR").is_ok() {
        return (Theme::None, Some("colors disabled"));
    }
    let mode = config.color_mode();
    if !mode.supports_color() {
        return (Theme::None, Some("no color support"));
    }
    if matches!(mode, ColorMode::Ansi16) {
        let resolved = requested.fallback_for_ansi();
        if resolved != requested {
            return (resolved, Some("ansi fallback"));
        }
        return (resolved, None);
    }
    (requested, None)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::test_env::with_terminal_color_env_overrides;
    use clap::Parser;
    use crossbeam_channel::bounded;

    fn with_theme_env<T>(pairs: &[(&str, Option<&str>)], f: impl FnOnce() -> T) -> T {
        with_terminal_color_env_overrides(pairs, f)
    }

    #[test]
    fn cycle_theme_moves_relative_to_current_option_order() {
        assert_eq!(cycle_theme(Theme::Coral, 1), Theme::Catppuccin);
        assert_eq!(cycle_theme(Theme::Coral, -1), Theme::Codex);
    }

    #[test]
    fn cycle_theme_wraps_at_ends_of_theme_list() {
        assert_eq!(cycle_theme(Theme::ChatGpt, -1), Theme::None);
        assert_eq!(cycle_theme(Theme::None, 1), Theme::ChatGpt);
    }

    #[test]
    fn resolve_theme_choice_keeps_theme_on_256color() {
        with_theme_env(
            &[
                ("COLORTERM", None),
                ("TERM", Some("xterm-256color")),
                ("NO_COLOR", None),
                ("TERM_PROGRAM", None),
                ("TERMINAL_EMULATOR", None),
            ],
            || {
                let config = OverlayConfig::parse_from(["test"]);
                let (resolved, note) = resolve_theme_choice(&config, Theme::Dracula);
                assert_eq!(resolved, Theme::Dracula);
                assert_eq!(note, None);
            },
        );
    }

    #[test]
    fn resolve_theme_choice_keeps_theme_on_truecolor() {
        with_theme_env(
            &[
                ("COLORTERM", Some("truecolor")),
                ("TERM", Some("xterm-256color")),
                ("NO_COLOR", None),
            ],
            || {
                let config = OverlayConfig::parse_from(["test"]);
                let (resolved, note) = resolve_theme_choice(&config, Theme::Dracula);
                assert_eq!(resolved, Theme::Dracula);
                assert_eq!(note, None);
            },
        );
    }

    #[test]
    fn resolve_theme_choice_falls_back_on_ansi16_term() {
        with_theme_env(
            &[
                ("COLORTERM", None),
                ("TERM", Some("xterm")),
                ("NO_COLOR", None),
                ("TERM_PROGRAM", None),
                ("TERMINAL_EMULATOR", None),
            ],
            || {
                let config = OverlayConfig::parse_from(["test"]);
                let (resolved, note) = resolve_theme_choice(&config, Theme::Dracula);
                assert_eq!(resolved, Theme::Ansi);
                assert_eq!(note, Some("ansi fallback"));
            },
        );
    }

    #[test]
    fn apply_theme_selection_reports_style_pack_lock() {
        with_terminal_color_env_overrides(
            &[
                (
                    "VOICETERM_STYLE_PACK_JSON",
                    Some(r#"{"version":2,"profile":"ops","base_theme":"codex"}"#),
                ),
                ("VOICETERM_TEST_ENABLE_STYLE_PACK_ENV", Some("1")),
            ],
            || {
                let mut config = OverlayConfig::parse_from(["test"]);
                let (writer_tx, _writer_rx) = bounded(4);
                let mut status_clear_deadline = None;
                let mut current_status = None;
                let mut status_state = StatusLineState::new();

                let resolved = apply_theme_selection(
                    &mut config,
                    Theme::Dracula,
                    &writer_tx,
                    &mut status_clear_deadline,
                    &mut current_status,
                    &mut status_state,
                );

                assert_eq!(resolved, Theme::Codex);
                assert_eq!(config.theme_name, None);
                assert_eq!(
                    current_status.as_deref(),
                    Some("Theme locked by VOICETERM_STYLE_PACK_JSON (codex)")
                );
            },
        );
    }
}
