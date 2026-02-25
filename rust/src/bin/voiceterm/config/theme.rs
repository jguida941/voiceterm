//! Theme resolution policy so color mode, flags, and backend defaults agree.

use crate::color_mode::ColorMode;
use crate::config::cli::OverlayConfig;
use crate::theme::Theme;

impl OverlayConfig {
    /// Get the resolved theme, respecting --no-color/NO_COLOR and backend defaults.
    pub(crate) fn theme_for_backend(&self, backend_label: &str) -> Theme {
        if self.no_color {
            return Theme::None;
        }
        let requested = self
            .theme_name
            .as_deref()
            .and_then(Theme::from_name)
            .unwrap_or_else(|| default_theme_for_backend(backend_label));
        let mode = self.color_mode();
        if !mode.supports_color() {
            Theme::None
        } else if matches!(mode, ColorMode::Ansi16) {
            requested.fallback_for_ansi()
        } else {
            requested
        }
    }

    /// Get the detected color mode for the terminal.
    pub(crate) fn color_mode(&self) -> ColorMode {
        if self.no_color {
            ColorMode::None
        } else {
            ColorMode::detect()
        }
    }
}

pub(crate) fn default_theme_for_backend(backend_label: &str) -> Theme {
    match backend_label.to_lowercase().as_str() {
        "claude" => Theme::Claude,
        "codex" => Theme::Codex,
        _ => Theme::Coral,
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::config::cli::OverlayConfig;
    use clap::Parser;
    use std::collections::BTreeSet;
    use std::sync::{Mutex, OnceLock};

    static ENV_GUARD: OnceLock<Mutex<()>> = OnceLock::new();

    fn with_env_vars<T>(pairs: &[(&str, Option<&str>)], f: impl FnOnce() -> T) -> T {
        let _guard = ENV_GUARD
            .get_or_init(|| Mutex::new(()))
            .lock()
            .unwrap_or_else(|e| e.into_inner());
        let mut keys: BTreeSet<&str> = BTreeSet::from([
            "COLORTERM",
            "TERM",
            "NO_COLOR",
            "TERM_PROGRAM",
            "TERMINAL_EMULATOR",
            "PYCHARM_HOSTED",
            "JETBRAINS_IDE",
            "IDEA_INITIAL_DIRECTORY",
            "IDEA_INITIAL_PROJECT",
            "CLION_IDE",
        ]);
        for (key, _) in pairs {
            keys.insert(key);
        }
        let prev: Vec<(String, Option<String>)> = keys
            .iter()
            .map(|key| ((*key).to_string(), std::env::var(key).ok()))
            .collect();
        for (key, value) in pairs {
            match value {
                Some(v) => std::env::set_var(key, v),
                None => std::env::remove_var(key),
            }
        }
        let result = f();
        for (key, value) in prev {
            match value {
                Some(v) => std::env::set_var(key, v),
                None => std::env::remove_var(key),
            }
        }
        result
    }

    fn with_truecolor_env<T>(f: impl FnOnce() -> T) -> T {
        with_env_vars(
            &[
                ("COLORTERM", Some("truecolor")),
                ("TERM", Some("xterm-256color")),
                ("NO_COLOR", None),
            ],
            f,
        )
    }

    #[test]
    fn default_theme_for_backend_maps_expected() {
        assert_eq!(default_theme_for_backend("claude"), Theme::Claude);
        assert_eq!(default_theme_for_backend("codex"), Theme::Codex);
        assert_eq!(default_theme_for_backend("custom"), Theme::Coral);
    }

    #[test]
    fn theme_for_backend_uses_backend_default_when_unset() {
        with_truecolor_env(|| {
            let config = OverlayConfig::parse_from(["test"]);
            assert!(config.theme_name.is_none());
            assert_eq!(config.theme_for_backend("claude"), Theme::Claude);
            assert_eq!(config.theme_for_backend("codex"), Theme::Codex);
            assert_eq!(config.theme_for_backend("custom"), Theme::Coral);
        });
    }

    #[test]
    fn theme_for_backend_keeps_requested_theme_on_256color_term() {
        with_env_vars(
            &[
                ("COLORTERM", None),
                ("TERM", Some("xterm-256color")),
                ("NO_COLOR", None),
                ("TERM_PROGRAM", None),
                ("TERMINAL_EMULATOR", None),
            ],
            || {
                let config = OverlayConfig::parse_from(["test", "--theme", "dracula"]);
                assert_eq!(config.theme_for_backend("codex"), Theme::Dracula);
            },
        );
    }

    #[test]
    fn theme_for_backend_keeps_requested_theme_on_truecolor_term() {
        with_truecolor_env(|| {
            let config = OverlayConfig::parse_from(["test", "--theme", "dracula"]);
            assert_eq!(config.theme_for_backend("codex"), Theme::Dracula);
        });
    }

    #[test]
    fn theme_for_backend_keeps_ansi_fallback_on_ansi16_term() {
        with_env_vars(
            &[
                ("COLORTERM", None),
                ("TERM", Some("xterm")),
                ("NO_COLOR", None),
                ("TERM_PROGRAM", None),
                ("TERMINAL_EMULATOR", None),
                ("PYCHARM_HOSTED", None),
                ("JETBRAINS_IDE", None),
                ("IDEA_INITIAL_DIRECTORY", None),
                ("IDEA_INITIAL_PROJECT", None),
                ("CLION_IDE", None),
            ],
            || {
                let config = OverlayConfig::parse_from(["test", "--theme", "dracula"]);
                assert_eq!(config.theme_for_backend("codex"), Theme::Ansi);
            },
        );
    }

    #[test]
    fn theme_for_backend_honors_no_color_env_even_when_flag_is_unset() {
        with_env_vars(
            &[
                ("COLORTERM", Some("truecolor")),
                ("TERM", Some("xterm-256color")),
                ("NO_COLOR", Some("1")),
            ],
            || {
                let config = OverlayConfig::parse_from(["test", "--theme", "dracula"]);
                assert!(!config.no_color, "--no-color flag is intentionally unset");
                assert_eq!(config.theme_for_backend("codex"), Theme::None);
            },
        );
    }
}
