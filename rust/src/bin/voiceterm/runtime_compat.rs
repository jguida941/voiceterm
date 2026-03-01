//! Backend + terminal-host compatibility policy for prompt/HUD behavior.

use std::env;

// Gap rows previously provided buffer space for the ToolExecution
// suppress/unsuppress cycle which toggled PTY winsize rapidly.  That cycle
// has been removed — the overlay is now stable during tool execution — so
// gap rows are zeroed out.  Users who need extra buffer can override via
// VOICETERM_CLAUDE_EXTRA_GAP_ROWS / VOICETERM_HUD_SAFETY_GAP_ROWS.
// Claude's interactive UI (especially in VS Code/Cursor integrated terminals)
// benefits from extra bottom spacing so composer/prompt rows stay above HUD.
const CLAUDE_EXTRA_GAP_ROWS_DEFAULT: usize = 5;
const CLAUDE_EXTRA_GAP_ROWS_CURSOR: usize = 12;
// JetBrains HUD overlap buffer: JediTerm does not support DECSTBM scroll
// regions, so the only separation between Claude's prompt and the HUD is the
// reserved-row subtraction.  2 rows provide a safer buffer zone for prompt
// placement while keeping most of the viewport available to Claude's TUI.
const CLAUDE_EXTRA_GAP_ROWS_JETBRAINS: usize = 2;
const CLAUDE_EXTRA_GAP_ROWS_MAX: usize = 20;
const HUD_SAFETY_GAP_ROWS_DEFAULT: usize = 0;
const HUD_SAFETY_GAP_ROWS_CURSOR: usize = 0;
const HUD_SAFETY_GAP_ROWS_JETBRAINS: usize = 0;
const HUD_SAFETY_GAP_ROWS_MAX: usize = 6;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub(crate) enum BackendFamily {
    Claude,
    Codex,
    Gemini,
    Other,
}

impl BackendFamily {
    pub(crate) fn from_label(label: &str) -> Self {
        let lowered = label.to_ascii_lowercase();
        if lowered.contains("claude") {
            Self::Claude
        } else if lowered.contains("codex") {
            Self::Codex
        } else if lowered.contains("gemini") {
            Self::Gemini
        } else {
            Self::Other
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub(crate) enum TerminalHost {
    JetBrains,
    Cursor,
    Other,
}

pub(crate) fn backend_family_from_env() -> BackendFamily {
    env::var("VOICETERM_BACKEND_LABEL")
        .map(|label| BackendFamily::from_label(&label))
        .unwrap_or(BackendFamily::Other)
}

pub(crate) fn backend_supports_prompt_occlusion_guard(backend_label: &str) -> bool {
    BackendFamily::from_label(backend_label) == BackendFamily::Claude
}

pub(crate) fn contains_jetbrains_hint(value: &str) -> bool {
    let lowered = value.to_ascii_lowercase();
    lowered.contains("jetbrains")
        || lowered.contains("jediterm")
        || lowered.contains("pycharm")
        || lowered.contains("intellij")
        || lowered.contains("idea")
}

pub(crate) fn detect_terminal_host() -> TerminalHost {
    const JETBRAINS_HINT_KEYS: &[&str] = &[
        "PYCHARM_HOSTED",
        "JETBRAINS_IDE",
        "IDEA_INITIAL_DIRECTORY",
        "IDEA_INITIAL_PROJECT",
        "CLION_IDE",
        "WEBSTORM_IDE",
    ];

    if JETBRAINS_HINT_KEYS
        .iter()
        .any(|key| env::var(key).map(|v| !v.trim().is_empty()).unwrap_or(false))
    {
        return TerminalHost::JetBrains;
    }

    for key in ["TERM_PROGRAM", "TERMINAL_EMULATOR"] {
        if let Ok(value) = env::var(key) {
            if contains_jetbrains_hint(&value) {
                return TerminalHost::JetBrains;
            }
            if value.to_ascii_lowercase().contains("cursor") {
                return TerminalHost::Cursor;
            }
        }
    }

    for key in [
        "CURSOR_TRACE_ID",
        "CURSOR_APP_VERSION",
        "CURSOR_VERSION",
        "CURSOR_BUILD_VERSION",
    ] {
        if env::var(key).map(|v| !v.trim().is_empty()).unwrap_or(false) {
            return TerminalHost::Cursor;
        }
    }

    TerminalHost::Other
}

pub(crate) fn is_jetbrains_terminal() -> bool {
    detect_terminal_host() == TerminalHost::JetBrains
}

pub(crate) fn parse_claude_extra_gap_rows(
    override_value: Option<&str>,
    terminal_host: TerminalHost,
) -> usize {
    if let Some(raw) = override_value {
        if let Ok(parsed) = raw.trim().parse::<usize>() {
            return parsed.min(CLAUDE_EXTRA_GAP_ROWS_MAX);
        }
    }
    match terminal_host {
        TerminalHost::JetBrains => CLAUDE_EXTRA_GAP_ROWS_JETBRAINS,
        TerminalHost::Cursor => CLAUDE_EXTRA_GAP_ROWS_CURSOR,
        TerminalHost::Other => CLAUDE_EXTRA_GAP_ROWS_DEFAULT,
    }
}

pub(crate) fn parse_hud_safety_gap_rows(
    override_value: Option<&str>,
    terminal_host: TerminalHost,
) -> usize {
    if let Some(raw) = override_value {
        if let Ok(parsed) = raw.trim().parse::<usize>() {
            return parsed.min(HUD_SAFETY_GAP_ROWS_MAX);
        }
    }
    match terminal_host {
        TerminalHost::JetBrains => HUD_SAFETY_GAP_ROWS_JETBRAINS,
        TerminalHost::Cursor => HUD_SAFETY_GAP_ROWS_CURSOR,
        TerminalHost::Other => HUD_SAFETY_GAP_ROWS_DEFAULT,
    }
}

pub(crate) fn resolved_claude_extra_gap_rows() -> usize {
    let override_value = env::var("VOICETERM_CLAUDE_EXTRA_GAP_ROWS").ok();
    parse_claude_extra_gap_rows(override_value.as_deref(), detect_terminal_host())
}

pub(crate) fn resolved_hud_safety_gap_rows() -> usize {
    let override_value = env::var("VOICETERM_HUD_SAFETY_GAP_ROWS").ok();
    parse_hud_safety_gap_rows(override_value.as_deref(), detect_terminal_host())
}

pub(crate) fn should_enable_claude_startup_guard(backend_label: &str) -> bool {
    BackendFamily::from_label(backend_label) == BackendFamily::Claude && is_jetbrains_terminal()
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::sync::{Mutex, OnceLock};

    fn with_env_lock<T>(f: impl FnOnce() -> T) -> T {
        static ENV_LOCK: OnceLock<Mutex<()>> = OnceLock::new();
        let lock = ENV_LOCK.get_or_init(|| Mutex::new(()));
        let _guard = lock.lock().expect("env lock poisoned");
        f()
    }

    fn with_terminal_env<T>(overrides: &[(&str, Option<&str>)], f: impl FnOnce() -> T) -> T {
        with_env_lock(|| {
            const KEYS: &[&str] = &[
                "PYCHARM_HOSTED",
                "JETBRAINS_IDE",
                "IDEA_INITIAL_DIRECTORY",
                "IDEA_INITIAL_PROJECT",
                "CLION_IDE",
                "WEBSTORM_IDE",
                "TERM_PROGRAM",
                "TERMINAL_EMULATOR",
                "CURSOR_TRACE_ID",
                "CURSOR_APP_VERSION",
                "CURSOR_VERSION",
                "CURSOR_BUILD_VERSION",
            ];
            let prev: Vec<(String, Option<String>)> = KEYS
                .iter()
                .map(|key| ((*key).to_string(), env::var(key).ok()))
                .collect();
            for key in KEYS {
                env::remove_var(key);
            }
            for (key, value) in overrides {
                match value {
                    Some(v) => env::set_var(key, v),
                    None => env::remove_var(key),
                }
            }

            let out = f();

            for (key, value) in prev {
                match value {
                    Some(v) => env::set_var(key, v),
                    None => env::remove_var(key),
                }
            }
            out
        })
    }

    #[test]
    fn backend_family_classifies_known_labels() {
        assert_eq!(
            BackendFamily::from_label("Claude Code"),
            BackendFamily::Claude
        );
        assert_eq!(BackendFamily::from_label("codex"), BackendFamily::Codex);
        assert_eq!(BackendFamily::from_label("gemini"), BackendFamily::Gemini);
        assert_eq!(
            BackendFamily::from_label("custom-cli"),
            BackendFamily::Other
        );
    }

    #[test]
    fn contains_jetbrains_hint_matches_expected_values() {
        assert!(contains_jetbrains_hint("JetBrains Gateway"));
        assert!(contains_jetbrains_hint("JetBrains-JediTerm"));
        assert!(contains_jetbrains_hint("PyCharm"));
        assert!(contains_jetbrains_hint("IntelliJ"));
        assert!(!contains_jetbrains_hint("xterm-256color"));
        assert!(!contains_jetbrains_hint("cursor"));
    }

    #[test]
    fn detect_terminal_host_handles_jetbrains_and_cursor() {
        with_terminal_env(&[], || {
            assert_eq!(detect_terminal_host(), TerminalHost::Other);
        });
        with_terminal_env(&[("PYCHARM_HOSTED", Some("1"))], || {
            assert_eq!(detect_terminal_host(), TerminalHost::JetBrains);
        });
        with_terminal_env(&[("TERM_PROGRAM", Some("Cursor"))], || {
            assert_eq!(detect_terminal_host(), TerminalHost::Cursor);
        });
    }

    #[test]
    fn parse_claude_extra_gap_rows_uses_defaults_and_clamps() {
        assert_eq!(
            parse_claude_extra_gap_rows(None, TerminalHost::Other),
            CLAUDE_EXTRA_GAP_ROWS_DEFAULT
        );
        assert_eq!(
            parse_claude_extra_gap_rows(None, TerminalHost::Cursor),
            CLAUDE_EXTRA_GAP_ROWS_CURSOR
        );
        assert_eq!(
            parse_claude_extra_gap_rows(None, TerminalHost::JetBrains),
            CLAUDE_EXTRA_GAP_ROWS_JETBRAINS
        );
        assert_eq!(
            parse_claude_extra_gap_rows(Some("999"), TerminalHost::Other),
            CLAUDE_EXTRA_GAP_ROWS_MAX
        );
    }

    #[test]
    fn parse_hud_safety_gap_rows_uses_defaults_and_clamps() {
        assert_eq!(
            parse_hud_safety_gap_rows(None, TerminalHost::Other),
            HUD_SAFETY_GAP_ROWS_DEFAULT
        );
        assert_eq!(
            parse_hud_safety_gap_rows(None, TerminalHost::Cursor),
            HUD_SAFETY_GAP_ROWS_CURSOR
        );
        assert_eq!(
            parse_hud_safety_gap_rows(None, TerminalHost::JetBrains),
            HUD_SAFETY_GAP_ROWS_JETBRAINS
        );
        assert_eq!(
            parse_hud_safety_gap_rows(Some("999"), TerminalHost::Other),
            HUD_SAFETY_GAP_ROWS_MAX
        );
    }

    #[test]
    fn startup_guard_only_for_claude_on_jetbrains() {
        with_terminal_env(&[("PYCHARM_HOSTED", Some("1"))], || {
            assert!(should_enable_claude_startup_guard("claude"));
            assert!(should_enable_claude_startup_guard("Claude Code"));
            assert!(!should_enable_claude_startup_guard("codex"));
        });
        with_terminal_env(&[], || {
            assert!(!should_enable_claude_startup_guard("claude"));
        });
    }
}
