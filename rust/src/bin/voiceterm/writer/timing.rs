use std::time::{Duration, Instant};

use crate::runtime_compat::{BackendFamily, HostTimingConfig, TerminalHost};

const STATUS_IDLE_MS: u64 = 50;
const STATUS_MAX_WAIT_MS: u64 = 150;
const PRIORITY_STATUS_IDLE_MS: u64 = 12;
const PRIORITY_STATUS_MAX_WAIT_MS: u64 = 40;

#[derive(Debug, Clone, Copy)]
pub(super) struct IdleRedrawTimingContext {
    pub(super) now: Instant,
    pub(super) terminal_family: TerminalHost,
    pub(super) backend_family: BackendFamily,
    pub(super) host_timing: HostTimingConfig,
    pub(super) since_output: Duration,
    pub(super) since_draw: Duration,
    pub(super) suppression_transition_pending: bool,
    pub(super) force_redraw_after_preclear: bool,
    pub(super) in_resize_repair_window: bool,
    pub(super) display_force_full_banner_redraw: bool,
    pub(super) pending_has_any: bool,
    pub(super) pending_overlay_panel_present: bool,
    pub(super) pending_clear_overlay: bool,
    pub(super) pending_clear_status: bool,
    pub(super) jetbrains_composer_repair_due: Option<Instant>,
    pub(super) jetbrains_repair_skip_quiet_window: bool,
    pub(super) jetbrains_dec_cursor_saved_active: bool,
    pub(super) jetbrains_ansi_cursor_saved_active: bool,
    pub(super) jetbrains_cursor_restore_settle_until: Option<Instant>,
}

#[derive(Debug, Clone, Copy, Default, PartialEq, Eq)]
pub(super) struct IdleRedrawTiming {
    pub(super) defer_redraw: bool,
    pub(super) clear_cursor_restore_settle_until: bool,
}

pub(super) fn should_defer_non_urgent_redraw_for_recent_input(
    terminal_family: TerminalHost,
    now: Instant,
    last_user_input_at: Instant,
) -> bool {
    // Defer non-urgent HUD redraws while the user is actively typing on all
    // terminal/backend combinations to avoid cursor flicker from HUD repaints.
    let hold = HostTimingConfig::for_host(terminal_family).typing_redraw_hold();
    now.duration_since(last_user_input_at) < hold
}

pub(super) fn resolve_idle_redraw_timing(ctx: IdleRedrawTimingContext) -> IdleRedrawTiming {
    let mut timing = IdleRedrawTiming::default();
    let clean_pending_state = !ctx.pending_overlay_panel_present
        && !ctx.pending_clear_overlay
        && !ctx.pending_clear_status
        && !ctx.suppression_transition_pending;
    let claude_jetbrains = ctx.terminal_family == TerminalHost::JetBrains
        && ctx.backend_family == BackendFamily::Claude;
    let jetbrains_composer_repair_armed =
        claude_jetbrains && ctx.jetbrains_composer_repair_due.is_some();
    let jetbrains_composer_repair_ready = ctx
        .jetbrains_composer_repair_due
        .is_some_and(|due| ctx.now >= due);

    if claude_jetbrains
        && jetbrains_composer_repair_armed
        && !jetbrains_composer_repair_ready
        && clean_pending_state
        && !ctx.force_redraw_after_preclear
    {
        timing.defer_redraw = true;
        return timing;
    }

    if claude_jetbrains
        && jetbrains_composer_repair_ready
        && clean_pending_state
        && !ctx.force_redraw_after_preclear
        && !ctx.jetbrains_repair_skip_quiet_window
        && ctx.since_output
            < ctx
                .host_timing
                .claude_composer_repair_quiet()
                .unwrap_or_default()
    {
        timing.defer_redraw = true;
        return timing;
    }

    if claude_jetbrains
        && !ctx.force_redraw_after_preclear
        && (ctx.jetbrains_dec_cursor_saved_active || ctx.jetbrains_ansi_cursor_saved_active)
    {
        timing.defer_redraw = true;
        return timing;
    }

    if claude_jetbrains
        && !ctx.force_redraw_after_preclear
        && ctx
            .jetbrains_cursor_restore_settle_until
            .is_some_and(|until| ctx.now < until)
    {
        timing.defer_redraw = true;
        return timing;
    }
    if claude_jetbrains
        && ctx
            .jetbrains_cursor_restore_settle_until
            .is_some_and(|until| ctx.now >= until)
    {
        timing.clear_cursor_restore_settle_until = true;
    }

    let claude_jetbrains_idle_gated_redraw = claude_jetbrains
        && !jetbrains_composer_repair_armed
        && !ctx.force_redraw_after_preclear
        && !ctx.in_resize_repair_window
        && clean_pending_state;
    let codex_jetbrains = ctx.terminal_family == TerminalHost::JetBrains
        && ctx.backend_family == BackendFamily::Codex;
    let codex_jetbrains_idle_gated_redraw = codex_jetbrains
        && ctx.display_force_full_banner_redraw
        && !ctx.force_redraw_after_preclear
        && clean_pending_state;

    let idle_hold = if claude_jetbrains_idle_gated_redraw {
        if ctx.display_force_full_banner_redraw {
            ctx.host_timing
                .scroll_idle_redraw_hold(BackendFamily::Claude)
                .unwrap_or_default()
        } else {
            ctx.host_timing
                .claude_idle_redraw_hold()
                .unwrap_or_default()
        }
    } else if codex_jetbrains_idle_gated_redraw {
        ctx.host_timing
            .scroll_idle_redraw_hold(BackendFamily::Codex)
            .unwrap_or_default()
    } else if ctx.pending_has_any {
        Duration::from_millis(PRIORITY_STATUS_IDLE_MS)
    } else {
        Duration::from_millis(STATUS_IDLE_MS)
    };
    let max_wait = if ctx.pending_has_any {
        Duration::from_millis(PRIORITY_STATUS_MAX_WAIT_MS)
    } else {
        Duration::from_millis(STATUS_MAX_WAIT_MS)
    };

    let jetbrains_idle_gated =
        claude_jetbrains_idle_gated_redraw || codex_jetbrains_idle_gated_redraw;
    let should_throttle_for_output = if jetbrains_idle_gated {
        // JetBrains+Claude/Codex can emit bursty chunks with brief gaps.
        // Redrawing in those gaps causes smeared HUD rows.
        ctx.since_output < idle_hold
    } else {
        ctx.since_output < idle_hold && ctx.since_draw < max_wait
    };

    if !ctx.force_redraw_after_preclear
        && !ctx.suppression_transition_pending
        && should_throttle_for_output
    {
        timing.defer_redraw = true;
    }

    timing
}

#[cfg(test)]
mod tests {
    use super::*;

    fn idle_context() -> IdleRedrawTimingContext {
        let now = Instant::now();
        IdleRedrawTimingContext {
            now,
            terminal_family: TerminalHost::Other,
            backend_family: BackendFamily::Other,
            host_timing: HostTimingConfig::for_host(TerminalHost::Other),
            since_output: Duration::from_millis(0),
            since_draw: Duration::from_millis(0),
            suppression_transition_pending: false,
            force_redraw_after_preclear: false,
            in_resize_repair_window: false,
            display_force_full_banner_redraw: false,
            pending_has_any: false,
            pending_overlay_panel_present: false,
            pending_clear_overlay: false,
            pending_clear_status: false,
            jetbrains_composer_repair_due: None,
            jetbrains_repair_skip_quiet_window: false,
            jetbrains_dec_cursor_saved_active: false,
            jetbrains_ansi_cursor_saved_active: false,
            jetbrains_cursor_restore_settle_until: None,
        }
    }

    #[test]
    fn typing_redraw_hold_uses_host_timing_windows() {
        let now = Instant::now();
        assert!(should_defer_non_urgent_redraw_for_recent_input(
            TerminalHost::Cursor,
            now,
            now - Duration::from_millis(225)
        ));
        assert!(!should_defer_non_urgent_redraw_for_recent_input(
            TerminalHost::Cursor,
            now,
            now - Duration::from_millis(460)
        ));
        assert!(should_defer_non_urgent_redraw_for_recent_input(
            TerminalHost::Other,
            now,
            now - Duration::from_millis(125)
        ));
        assert!(!should_defer_non_urgent_redraw_for_recent_input(
            TerminalHost::Other,
            now,
            now - Duration::from_millis(260)
        ));
    }

    #[test]
    fn idle_redraw_timing_uses_jetbrains_claude_scroll_hold_window() {
        let mut ctx = idle_context();
        ctx.terminal_family = TerminalHost::JetBrains;
        ctx.backend_family = BackendFamily::Claude;
        ctx.host_timing = HostTimingConfig::for_host(TerminalHost::JetBrains);
        ctx.display_force_full_banner_redraw = true;
        ctx.since_output = Duration::from_millis(120);
        ctx.since_draw = Duration::from_millis(900);
        assert!(resolve_idle_redraw_timing(ctx).defer_redraw);

        ctx.since_output = Duration::from_millis(250);
        assert!(!resolve_idle_redraw_timing(ctx).defer_redraw);
    }

    #[test]
    fn idle_redraw_timing_uses_jetbrains_codex_scroll_hold_window() {
        let mut ctx = idle_context();
        ctx.terminal_family = TerminalHost::JetBrains;
        ctx.backend_family = BackendFamily::Codex;
        ctx.host_timing = HostTimingConfig::for_host(TerminalHost::JetBrains);
        ctx.display_force_full_banner_redraw = true;
        ctx.since_output = Duration::from_millis(220);
        ctx.since_draw = Duration::from_millis(900);
        assert!(resolve_idle_redraw_timing(ctx).defer_redraw);

        ctx.since_output = Duration::from_millis(340);
        assert!(!resolve_idle_redraw_timing(ctx).defer_redraw);
    }

    #[test]
    fn idle_redraw_timing_honors_priority_max_wait_for_non_jetbrains_hosts() {
        let mut ctx = idle_context();
        ctx.pending_has_any = true;
        ctx.since_output = Duration::from_millis(8);
        ctx.since_draw = Duration::from_millis(20);
        assert!(resolve_idle_redraw_timing(ctx).defer_redraw);

        ctx.since_draw = Duration::from_millis(55);
        assert!(!resolve_idle_redraw_timing(ctx).defer_redraw);
    }

    #[test]
    fn idle_redraw_timing_applies_jetbrains_claude_composer_quiet_window() {
        let mut ctx = idle_context();
        ctx.terminal_family = TerminalHost::JetBrains;
        ctx.backend_family = BackendFamily::Claude;
        ctx.host_timing = HostTimingConfig::for_host(TerminalHost::JetBrains);
        ctx.jetbrains_composer_repair_due = Some(ctx.now - Duration::from_millis(1));
        ctx.since_output = Duration::from_millis(100);
        ctx.since_draw = Duration::from_millis(500);
        assert!(resolve_idle_redraw_timing(ctx).defer_redraw);

        ctx.jetbrains_repair_skip_quiet_window = true;
        assert!(!resolve_idle_redraw_timing(ctx).defer_redraw);
    }

    #[test]
    fn idle_redraw_timing_clears_expired_cursor_restore_settle_window() {
        let mut ctx = idle_context();
        ctx.terminal_family = TerminalHost::JetBrains;
        ctx.backend_family = BackendFamily::Claude;
        ctx.host_timing = HostTimingConfig::for_host(TerminalHost::JetBrains);
        ctx.jetbrains_cursor_restore_settle_until = Some(ctx.now - Duration::from_millis(1));
        ctx.since_output = Duration::from_millis(500);
        ctx.since_draw = Duration::from_millis(500);
        let timing = resolve_idle_redraw_timing(ctx);
        assert!(timing.clear_cursor_restore_settle_until);
        assert!(!timing.defer_redraw);
    }
}
