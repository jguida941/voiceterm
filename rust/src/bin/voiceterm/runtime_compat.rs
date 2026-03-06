//! Backend + terminal-host compatibility policy for prompt/HUD behavior.

use std::env;
#[cfg(not(test))]
use std::sync::OnceLock;
use std::time::Duration;
#[cfg(test)]
use std::{cell::Cell, thread_local};

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
// reserved-row subtraction. Keep a larger default buffer to tolerate multi-line
// composer wrapping near terminal bottom under heavy output.
const CLAUDE_EXTRA_GAP_ROWS_JETBRAINS: usize = 4;
const CLAUDE_EXTRA_GAP_ROWS_MAX: usize = 20;
const HUD_SAFETY_GAP_ROWS_DEFAULT: usize = 0;
const HUD_SAFETY_GAP_ROWS_CURSOR: usize = 0;
const HUD_SAFETY_GAP_ROWS_JETBRAINS: usize = 0;
const HUD_SAFETY_GAP_ROWS_MAX: usize = 6;
const JETBRAINS_HINT_KEYS: &[&str] = &[
    "PYCHARM_HOSTED",
    "JETBRAINS_IDE",
    "IDEA_INITIAL_DIRECTORY",
    "IDEA_INITIAL_PROJECT",
    "CLION_IDE",
    "WEBSTORM_IDE",
];
const TERMINAL_PROGRAM_KEYS: &[&str] = &["TERM_PROGRAM", "TERMINAL_EMULATOR"];
const CURSOR_HINT_KEYS: &[&str] = &[
    "CURSOR_TRACE_ID",
    "CURSOR_APP_VERSION",
    "CURSOR_VERSION",
    "CURSOR_BUILD_VERSION",
];

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

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub(crate) struct HostTimingConfig {
    preclear_cooldown_ms: u64,
    typing_redraw_hold_ms: u64,
    codex_scroll_redraw_min_interval_ms: u64,
    claude_scroll_redraw_min_interval_ms: u64,
    claude_non_scroll_redraw_min_interval_ms: u64,
    claude_idle_redraw_hold_ms: u64,
    claude_scroll_idle_redraw_hold_ms: u64,
    codex_scroll_idle_redraw_hold_ms: u64,
    claude_banner_preclear_cooldown_ms: u64,
    claude_cursor_restore_settle_ms: u64,
    claude_composer_repair_delay_ms: u64,
    claude_composer_repair_quiet_ms: u64,
    claude_recent_input_window_ms: u64,
    claude_resize_repair_window_ms: u64,
    claude_destructive_clear_repaint_cooldown_ms: u64,
    claude_input_repair_delay_ms: u64,
}

impl HostTimingConfig {
    pub(crate) const fn for_host(host: TerminalHost) -> Self {
        match host {
            TerminalHost::JetBrains => Self {
                preclear_cooldown_ms: 260,
                typing_redraw_hold_ms: 250,
                codex_scroll_redraw_min_interval_ms: 320,
                claude_scroll_redraw_min_interval_ms: 150,
                claude_non_scroll_redraw_min_interval_ms: 700,
                claude_idle_redraw_hold_ms: 500,
                claude_scroll_idle_redraw_hold_ms: 200,
                codex_scroll_idle_redraw_hold_ms: 320,
                claude_banner_preclear_cooldown_ms: 90,
                claude_cursor_restore_settle_ms: 140,
                claude_composer_repair_delay_ms: 140,
                claude_composer_repair_quiet_ms: 700,
                claude_recent_input_window_ms: 1500,
                claude_resize_repair_window_ms: 600,
                claude_destructive_clear_repaint_cooldown_ms: 220,
                claude_input_repair_delay_ms: 140,
            },
            TerminalHost::Cursor => Self {
                preclear_cooldown_ms: 220,
                typing_redraw_hold_ms: 450,
                codex_scroll_redraw_min_interval_ms: 0,
                claude_scroll_redraw_min_interval_ms: 900,
                claude_non_scroll_redraw_min_interval_ms: 700,
                claude_idle_redraw_hold_ms: 0,
                claude_scroll_idle_redraw_hold_ms: 0,
                codex_scroll_idle_redraw_hold_ms: 0,
                claude_banner_preclear_cooldown_ms: 0,
                claude_cursor_restore_settle_ms: 0,
                claude_composer_repair_delay_ms: 0,
                claude_composer_repair_quiet_ms: 0,
                claude_recent_input_window_ms: 0,
                claude_resize_repair_window_ms: 0,
                claude_destructive_clear_repaint_cooldown_ms: 0,
                claude_input_repair_delay_ms: 140,
            },
            TerminalHost::Other => Self {
                preclear_cooldown_ms: 0,
                typing_redraw_hold_ms: 250,
                codex_scroll_redraw_min_interval_ms: 0,
                claude_scroll_redraw_min_interval_ms: 0,
                claude_non_scroll_redraw_min_interval_ms: 0,
                claude_idle_redraw_hold_ms: 0,
                claude_scroll_idle_redraw_hold_ms: 0,
                codex_scroll_idle_redraw_hold_ms: 0,
                claude_banner_preclear_cooldown_ms: 0,
                claude_cursor_restore_settle_ms: 0,
                claude_composer_repair_delay_ms: 0,
                claude_composer_repair_quiet_ms: 0,
                claude_recent_input_window_ms: 0,
                claude_resize_repair_window_ms: 0,
                claude_destructive_clear_repaint_cooldown_ms: 0,
                claude_input_repair_delay_ms: 0,
            },
        }
    }

    pub(crate) fn preclear_cooldown(self) -> Duration {
        Duration::from_millis(self.preclear_cooldown_ms)
    }

    pub(crate) fn typing_redraw_hold(self) -> Duration {
        Duration::from_millis(self.typing_redraw_hold_ms)
    }

    pub(crate) fn scroll_redraw_min_interval(self, backend: BackendFamily) -> Option<Duration> {
        let interval_ms = match backend {
            BackendFamily::Codex => self.codex_scroll_redraw_min_interval_ms,
            BackendFamily::Claude => self.claude_scroll_redraw_min_interval_ms,
            BackendFamily::Gemini | BackendFamily::Other => 0,
        };
        if interval_ms == 0 {
            None
        } else {
            Some(Duration::from_millis(interval_ms))
        }
    }

    pub(crate) fn scroll_idle_redraw_hold(self, backend: BackendFamily) -> Option<Duration> {
        let hold_ms = match backend {
            BackendFamily::Codex => self.codex_scroll_idle_redraw_hold_ms,
            BackendFamily::Claude => self.claude_scroll_idle_redraw_hold_ms,
            BackendFamily::Gemini | BackendFamily::Other => 0,
        };
        if hold_ms == 0 {
            None
        } else {
            Some(Duration::from_millis(hold_ms))
        }
    }

    pub(crate) fn claude_non_scroll_redraw_min_interval(self) -> Option<Duration> {
        if self.claude_non_scroll_redraw_min_interval_ms == 0 {
            None
        } else {
            Some(Duration::from_millis(
                self.claude_non_scroll_redraw_min_interval_ms,
            ))
        }
    }

    pub(crate) fn claude_idle_redraw_hold(self) -> Option<Duration> {
        if self.claude_idle_redraw_hold_ms == 0 {
            None
        } else {
            Some(Duration::from_millis(self.claude_idle_redraw_hold_ms))
        }
    }

    pub(crate) fn claude_banner_preclear_cooldown(self) -> Option<Duration> {
        if self.claude_banner_preclear_cooldown_ms == 0 {
            None
        } else {
            Some(Duration::from_millis(
                self.claude_banner_preclear_cooldown_ms,
            ))
        }
    }

    pub(crate) fn claude_cursor_restore_settle(self) -> Option<Duration> {
        if self.claude_cursor_restore_settle_ms == 0 {
            None
        } else {
            Some(Duration::from_millis(self.claude_cursor_restore_settle_ms))
        }
    }

    pub(crate) fn claude_composer_repair_delay(self) -> Option<Duration> {
        if self.claude_composer_repair_delay_ms == 0 {
            None
        } else {
            Some(Duration::from_millis(self.claude_composer_repair_delay_ms))
        }
    }

    pub(crate) fn claude_composer_repair_quiet(self) -> Option<Duration> {
        if self.claude_composer_repair_quiet_ms == 0 {
            None
        } else {
            Some(Duration::from_millis(self.claude_composer_repair_quiet_ms))
        }
    }

    pub(crate) fn claude_recent_input_window(self) -> Option<Duration> {
        if self.claude_recent_input_window_ms == 0 {
            None
        } else {
            Some(Duration::from_millis(self.claude_recent_input_window_ms))
        }
    }

    pub(crate) fn claude_resize_repair_window(self) -> Option<Duration> {
        if self.claude_resize_repair_window_ms == 0 {
            None
        } else {
            Some(Duration::from_millis(self.claude_resize_repair_window_ms))
        }
    }

    pub(crate) fn claude_destructive_clear_repaint_cooldown(self) -> Option<Duration> {
        if self.claude_destructive_clear_repaint_cooldown_ms == 0 {
            None
        } else {
            Some(Duration::from_millis(
                self.claude_destructive_clear_repaint_cooldown_ms,
            ))
        }
    }

    pub(crate) fn claude_input_repair_delay(self) -> Option<Duration> {
        if self.claude_input_repair_delay_ms == 0 {
            None
        } else {
            Some(Duration::from_millis(self.claude_input_repair_delay_ms))
        }
    }
}

#[cfg(not(test))]
static TERMINAL_HOST_CACHE: OnceLock<TerminalHost> = OnceLock::new();

#[cfg(test)]
thread_local! {
    static TERMINAL_HOST_OVERRIDE: Cell<Option<TerminalHost>> = const { Cell::new(None) };
}

#[cfg(test)]
fn terminal_host_override() -> Option<TerminalHost> {
    TERMINAL_HOST_OVERRIDE.with(|slot| slot.get())
}

#[cfg(test)]
pub(crate) fn set_terminal_host_override(host: Option<TerminalHost>) {
    TERMINAL_HOST_OVERRIDE.with(|slot| slot.set(host));
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

fn detect_terminal_host_from_env() -> TerminalHost {
    if JETBRAINS_HINT_KEYS
        .iter()
        .any(|key| env::var(key).map(|v| !v.trim().is_empty()).unwrap_or(false))
    {
        return TerminalHost::JetBrains;
    }

    for key in TERMINAL_PROGRAM_KEYS {
        if let Ok(value) = env::var(key) {
            if contains_jetbrains_hint(&value) {
                return TerminalHost::JetBrains;
            }
            if value.to_ascii_lowercase().contains("cursor") {
                return TerminalHost::Cursor;
            }
        }
    }

    for key in CURSOR_HINT_KEYS {
        if env::var(key).map(|v| !v.trim().is_empty()).unwrap_or(false) {
            return TerminalHost::Cursor;
        }
    }

    TerminalHost::Other
}

pub(crate) fn detect_terminal_host() -> TerminalHost {
    #[cfg(test)]
    if let Some(host) = terminal_host_override() {
        return host;
    }

    #[cfg(not(test))]
    {
        *TERMINAL_HOST_CACHE.get_or_init(detect_terminal_host_from_env)
    }
    #[cfg(test)]
    {
        detect_terminal_host_from_env()
    }
}

pub(crate) fn is_jetbrains_terminal() -> bool {
    detect_terminal_host() == TerminalHost::JetBrains
}

pub(crate) fn should_force_single_line_full_hud(
    backend_family: BackendFamily,
    terminal_host: TerminalHost,
) -> bool {
    backend_family == BackendFamily::Claude && terminal_host == TerminalHost::JetBrains
}

pub(crate) fn should_force_single_line_full_hud_for_env() -> bool {
    should_force_single_line_full_hud(backend_family_from_env(), detect_terminal_host())
}

pub(crate) fn should_toggle_cursor_visibility_for_redraw(terminal_host: TerminalHost) -> bool {
    terminal_host == TerminalHost::JetBrains && backend_family_from_env() != BackendFamily::Claude
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
    use crate::test_env::with_terminal_host_env_overrides;
    use rstest::rstest;

    struct TerminalHostOverrideGuard {
        previous: Option<TerminalHost>,
    }

    impl TerminalHostOverrideGuard {
        fn push(override_host: Option<TerminalHost>) -> Self {
            let previous = terminal_host_override();
            set_terminal_host_override(override_host);
            Self { previous }
        }
    }

    impl Drop for TerminalHostOverrideGuard {
        fn drop(&mut self) {
            set_terminal_host_override(self.previous);
        }
    }

    fn with_terminal_host_override<T>(
        override_host: Option<TerminalHost>,
        f: impl FnOnce() -> T,
    ) -> T {
        let _guard = TerminalHostOverrideGuard::push(override_host);
        f()
    }

    fn with_terminal_env<T>(overrides: &[(&str, Option<&str>)], f: impl FnOnce() -> T) -> T {
        with_terminal_host_env_overrides(overrides, || with_terminal_host_override(None, f))
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
    fn host_timing_config_matches_phase2a_baseline_values() {
        let jetbrains = HostTimingConfig::for_host(TerminalHost::JetBrains);
        let cursor = HostTimingConfig::for_host(TerminalHost::Cursor);
        let other = HostTimingConfig::for_host(TerminalHost::Other);

        assert_eq!(jetbrains.preclear_cooldown(), Duration::from_millis(260));
        assert_eq!(cursor.preclear_cooldown(), Duration::from_millis(220));
        assert_eq!(cursor.typing_redraw_hold(), Duration::from_millis(450));
        assert_eq!(other.typing_redraw_hold(), Duration::from_millis(250));

        assert_eq!(
            jetbrains.scroll_redraw_min_interval(BackendFamily::Codex),
            Some(Duration::from_millis(320))
        );
        assert_eq!(
            jetbrains.scroll_redraw_min_interval(BackendFamily::Claude),
            Some(Duration::from_millis(150))
        );
        assert_eq!(
            cursor.scroll_redraw_min_interval(BackendFamily::Claude),
            Some(Duration::from_millis(900))
        );
        assert_eq!(
            other.scroll_redraw_min_interval(BackendFamily::Claude),
            None
        );
    }

    #[test]
    fn host_timing_config_claude_jetbrains_helpers_are_present_only_on_jetbrains() {
        let jetbrains = HostTimingConfig::for_host(TerminalHost::JetBrains);
        let cursor = HostTimingConfig::for_host(TerminalHost::Cursor);

        assert_eq!(
            jetbrains.claude_banner_preclear_cooldown(),
            Some(Duration::from_millis(90))
        );
        assert_eq!(
            jetbrains.claude_composer_repair_quiet(),
            Some(Duration::from_millis(700))
        );
        assert_eq!(
            jetbrains.claude_destructive_clear_repaint_cooldown(),
            Some(Duration::from_millis(220))
        );
        assert_eq!(cursor.claude_banner_preclear_cooldown(), None);
        assert_eq!(cursor.claude_composer_repair_quiet(), None);
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
            assert_eq!(detect_terminal_host_from_env(), TerminalHost::Other);
        });
        with_terminal_env(&[("PYCHARM_HOSTED", Some("1"))], || {
            assert_eq!(detect_terminal_host_from_env(), TerminalHost::JetBrains);
        });
        with_terminal_env(&[("TERM_PROGRAM", Some("Cursor"))], || {
            assert_eq!(detect_terminal_host_from_env(), TerminalHost::Cursor);
        });
    }

    #[test]
    fn detect_terminal_host_allows_thread_local_override() {
        with_terminal_env(&[("PYCHARM_HOSTED", Some("1"))], || {
            assert_eq!(detect_terminal_host(), TerminalHost::JetBrains);
            with_terminal_host_override(Some(TerminalHost::Cursor), || {
                assert_eq!(detect_terminal_host(), TerminalHost::Cursor);
            });
            assert_eq!(detect_terminal_host(), TerminalHost::JetBrains);
        });
    }

    #[test]
    fn detect_terminal_host_override_resets_after_panic() {
        with_terminal_env(&[("PYCHARM_HOSTED", Some("1"))], || {
            assert_eq!(detect_terminal_host(), TerminalHost::JetBrains);
            let panic_result = std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| {
                with_terminal_host_override(Some(TerminalHost::Cursor), || {
                    assert_eq!(detect_terminal_host(), TerminalHost::Cursor);
                    panic!("intentional panic to verify override reset");
                });
            }));
            assert!(panic_result.is_err());
            assert_eq!(detect_terminal_host(), TerminalHost::JetBrains);
        });
    }

    #[rstest]
    #[case(TerminalHost::Other, CLAUDE_EXTRA_GAP_ROWS_DEFAULT)]
    #[case(TerminalHost::Cursor, CLAUDE_EXTRA_GAP_ROWS_CURSOR)]
    #[case(TerminalHost::JetBrains, CLAUDE_EXTRA_GAP_ROWS_JETBRAINS)]
    fn parse_claude_extra_gap_rows_uses_host_defaults(
        #[case] host: TerminalHost,
        #[case] expected: usize,
    ) {
        assert_eq!(parse_claude_extra_gap_rows(None, host), expected);
    }

    #[test]
    fn parse_claude_extra_gap_rows_clamps_override() {
        assert_eq!(
            parse_claude_extra_gap_rows(Some("999"), TerminalHost::Other),
            CLAUDE_EXTRA_GAP_ROWS_MAX
        );
    }

    #[rstest]
    #[case(TerminalHost::Other, HUD_SAFETY_GAP_ROWS_DEFAULT)]
    #[case(TerminalHost::Cursor, HUD_SAFETY_GAP_ROWS_CURSOR)]
    #[case(TerminalHost::JetBrains, HUD_SAFETY_GAP_ROWS_JETBRAINS)]
    fn parse_hud_safety_gap_rows_uses_host_defaults(
        #[case] host: TerminalHost,
        #[case] expected: usize,
    ) {
        assert_eq!(parse_hud_safety_gap_rows(None, host), expected);
    }

    #[test]
    fn parse_hud_safety_gap_rows_clamps_override() {
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

    #[test]
    fn single_line_full_hud_policy_only_for_claude_on_jetbrains() {
        assert!(should_force_single_line_full_hud(
            BackendFamily::Claude,
            TerminalHost::JetBrains
        ));
        assert!(!should_force_single_line_full_hud(
            BackendFamily::Codex,
            TerminalHost::JetBrains
        ));
        assert!(!should_force_single_line_full_hud(
            BackendFamily::Claude,
            TerminalHost::Cursor
        ));
    }

    #[test]
    fn cursor_visibility_toggle_policy_only_for_non_claude_jetbrains() {
        with_terminal_env(&[("PYCHARM_HOSTED", Some("1"))], || {
            let previous_backend = env::var("VOICETERM_BACKEND_LABEL").ok();
            env::set_var("VOICETERM_BACKEND_LABEL", "codex");
            assert!(should_toggle_cursor_visibility_for_redraw(
                TerminalHost::JetBrains
            ));
            env::set_var("VOICETERM_BACKEND_LABEL", "claude");
            assert!(!should_toggle_cursor_visibility_for_redraw(
                TerminalHost::JetBrains
            ));
            if let Some(value) = previous_backend.as_deref() {
                env::set_var("VOICETERM_BACKEND_LABEL", value);
            } else {
                env::remove_var("VOICETERM_BACKEND_LABEL");
            }
        });
        with_terminal_env(&[], || {
            let previous_backend = env::var("VOICETERM_BACKEND_LABEL").ok();
            env::set_var("VOICETERM_BACKEND_LABEL", "codex");
            assert!(!should_toggle_cursor_visibility_for_redraw(
                TerminalHost::Cursor
            ));
            if let Some(value) = previous_backend.as_deref() {
                env::set_var("VOICETERM_BACKEND_LABEL", value);
            } else {
                env::remove_var("VOICETERM_BACKEND_LABEL");
            }
        });
    }
}
