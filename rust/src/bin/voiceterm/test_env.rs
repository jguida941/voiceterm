use std::sync::{Mutex, MutexGuard, OnceLock};
#[cfg(test)]
use std::{
    collections::{BTreeSet, HashMap},
    env,
};

fn shared_env_lock() -> &'static Mutex<()> {
    static ENV_LOCK: OnceLock<Mutex<()>> = OnceLock::new();
    ENV_LOCK.get_or_init(|| Mutex::new(()))
}

pub(crate) fn env_lock() -> MutexGuard<'static, ()> {
    shared_env_lock()
        .lock()
        .unwrap_or_else(|poisoned| poisoned.into_inner())
}

pub(crate) fn with_env_lock<T>(f: impl FnOnce() -> T) -> T {
    let _guard = env_lock();
    f()
}

#[cfg(test)]
pub(crate) const TERMINAL_HOST_ENV_KEYS: &[&str] = &[
    "TERM_PROGRAM",
    "TERMINAL_EMULATOR",
    "KITTY_WINDOW_ID",
    "ITERM_SESSION_ID",
    "PYCHARM_HOSTED",
    "JETBRAINS_IDE",
    "IDEA_INITIAL_DIRECTORY",
    "IDEA_INITIAL_PROJECT",
    "CLION_IDE",
    "WEBSTORM_IDE",
    "CURSOR_TRACE_ID",
    "CURSOR_APP_VERSION",
    "CURSOR_VERSION",
    "CURSOR_BUILD_VERSION",
];

#[cfg(test)]
pub(crate) const COLOR_MODE_ENV_KEYS: &[&str] = &["COLORTERM", "TERM", "NO_COLOR"];

#[cfg(test)]
pub(crate) fn with_env_overrides<T>(
    keys: &[&str],
    pairs: &[(&str, Option<&str>)],
    f: impl FnOnce() -> T,
) -> T {
    with_env_lock(|| {
        let mut scoped_keys = BTreeSet::new();
        scoped_keys.extend(keys.iter().copied());
        scoped_keys.extend(pairs.iter().map(|(key, _)| *key));
        let previous: HashMap<&str, Option<String>> = scoped_keys
            .iter()
            .map(|key| (*key, env::var(key).ok()))
            .collect();
        for key in &scoped_keys {
            env::remove_var(key);
        }
        for (key, value) in pairs {
            match value {
                Some(v) => env::set_var(key, v),
                None => env::remove_var(key),
            }
        }

        let output = f();
        for (key, value) in previous {
            match value {
                Some(v) => env::set_var(key, v),
                None => env::remove_var(key),
            }
        }
        output
    })
}

#[cfg(test)]
pub(crate) fn with_terminal_host_env_overrides<T>(
    pairs: &[(&str, Option<&str>)],
    f: impl FnOnce() -> T,
) -> T {
    with_env_overrides(TERMINAL_HOST_ENV_KEYS, pairs, f)
}

#[cfg(test)]
pub(crate) fn with_terminal_color_env_overrides<T>(
    pairs: &[(&str, Option<&str>)],
    f: impl FnOnce() -> T,
) -> T {
    let mut keys = TERMINAL_HOST_ENV_KEYS.to_vec();
    keys.extend_from_slice(COLOR_MODE_ENV_KEYS);
    with_env_overrides(&keys, pairs, f)
}

#[cfg(test)]
pub(crate) fn default_overlay_config() -> crate::config::OverlayConfig {
    use crate::config::{CaptureOnceFormat, OverlayConfig, VoiceSendMode};
    use clap::Parser;
    use voiceterm::config::AppConfig;

    OverlayConfig {
        help: false,
        app: AppConfig::parse_from(["test"]),
        prompt_regex: None,
        prompt_log: None,
        auto_voice: false,
        auto_voice_idle_ms: 1200,
        transcript_idle_ms: 250,
        capture_once: false,
        capture_once_format: CaptureOnceFormat::Text,
        voice_send_mode: VoiceSendMode::Auto,
        wake_word: false,
        wake_word_sensitivity: 0.55,
        wake_word_cooldown_ms: 2000,
        theme_name: None,
        no_color: false,
        hud_right_panel: crate::config::HudRightPanel::Ribbon,
        hud_border_style: crate::config::HudBorderStyle::Theme,
        hud_right_panel_recording_only: true,
        hud_style: crate::config::HudStyle::Full,
        latency_display: crate::config::LatencyDisplayMode::Short,
        image_mode: false,
        image_capture_command: None,
        dev_mode: false,
        dev_log: false,
        dev_path: None,
        minimal_hud: false,
        backend: "codex".to_string(),
        codex: false,
        claude: false,
        gemini: false,
        login: false,
        theme_file: None,
        export_theme: None,
    }
}
