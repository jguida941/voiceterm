use crate::runtime_compat::{
    backend_family_from_env, BackendFamily, HostTimingConfig, RuntimeVariant, TerminalHost,
};
use std::time::{Duration, Instant};

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub(super) struct RuntimeProfile {
    pub(super) terminal_family: TerminalHost,
    pub(super) backend_family: BackendFamily,
    pub(super) runtime_variant: RuntimeVariant,
    pub(super) host_timing: HostTimingConfig,
    pub(super) startup_guard_enabled: bool,
    pub(super) codex_jetbrains: bool,
    pub(super) claude_jetbrains: bool,
    pub(super) cursor_claude: bool,
    pub(super) treat_cr_as_scroll: bool,
    pub(super) flash_sensitive_scroll_profile: bool,
    pub(super) claude_non_scroll_redraw_profile: bool,
    pub(super) scroll_redraw_min_interval: Option<Duration>,
}

impl RuntimeProfile {
    pub(super) fn resolve(terminal_family: TerminalHost, backend_family: BackendFamily) -> Self {
        let host_timing = HostTimingConfig::for_host(terminal_family);
        let runtime_variant = RuntimeVariant::from_parts(terminal_family, backend_family);
        let codex_jetbrains = runtime_variant.is_jetbrains_codex();
        let claude_jetbrains = runtime_variant.is_jetbrains_claude();
        let cursor_claude = runtime_variant.is_cursor_claude();
        Self {
            terminal_family,
            backend_family,
            runtime_variant,
            host_timing,
            startup_guard_enabled: runtime_variant.is_jetbrains_claude(),
            codex_jetbrains,
            claude_jetbrains,
            cursor_claude,
            treat_cr_as_scroll: codex_jetbrains,
            flash_sensitive_scroll_profile: codex_jetbrains || claude_jetbrains || cursor_claude,
            claude_non_scroll_redraw_profile: claude_jetbrains || cursor_claude,
            scroll_redraw_min_interval: host_timing.scroll_redraw_min_interval(backend_family),
        }
    }

    pub(super) fn from_environment(terminal_family: TerminalHost) -> Self {
        Self::resolve(terminal_family, backend_family_from_env())
    }

    #[cfg(test)]
    pub(super) fn with_terminal_family(self, terminal_family: TerminalHost) -> Self {
        Self::resolve(terminal_family, self.backend_family)
    }
}

pub(super) fn is_transient_jetbrains_claude_geometry_collapse(
    claude_jetbrains_profile: bool,
    current_rows: u16,
    current_cols: u16,
    next_rows: u16,
    next_cols: u16,
) -> bool {
    claude_jetbrains_profile
        && current_rows >= 10
        && current_cols > 0
        && next_cols == current_cols
        && next_rows <= 2
}

pub(super) fn claude_jetbrains_has_recent_input(
    now: Instant,
    last_user_input_at: Instant,
    host_timing: HostTimingConfig,
) -> bool {
    host_timing
        .claude_recent_input_window()
        .is_some_and(|window| now.duration_since(last_user_input_at) <= window)
}
