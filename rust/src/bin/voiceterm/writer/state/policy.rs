use super::super::render::{build_clear_bottom_rows_bytes, build_clear_bottom_rows_cup_only_bytes};
use super::chunk_analysis::{
    pty_output_can_mutate_cursor_line, pty_output_contains_destructive_clear,
};
use super::display::{preclear_height, DisplayState};
#[cfg(test)]
use crate::runtime_compat::BackendFamily;
use crate::runtime_compat::{HostTimingConfig, RuntimeVariant, TerminalHost};
use std::time::{Duration, Instant};

#[derive(Clone, Copy)]
pub(super) struct PreclearPolicyContext<'a> {
    pub(super) family: TerminalHost,
    pub(super) display: &'a DisplayState,
    pub(super) status_clear_pending: bool,
    pub(super) may_scroll_rows: bool,
    pub(super) codex_jetbrains: bool,
    pub(super) cursor_claude_startup_preclear: bool,
    pub(super) cursor_claude_banner_preclear: bool,
    pub(super) claude_jetbrains_banner_preclear: bool,
    pub(super) claude_jetbrains_cup_preclear_safe: bool,
    pub(super) claude_jetbrains_legacy_preclear_safe: bool,
    pub(super) in_resize_repair_window: bool,
    pub(super) preclear_blocked_for_recent_input: bool,
    pub(super) claude_jetbrains_destructive_clear: bool,
    pub(super) now: Instant,
    pub(super) last_preclear_at: Instant,
}

#[derive(Debug, Clone, Copy, Default, PartialEq, Eq)]
pub(super) struct PreclearPolicy {
    pub(super) should_preclear: bool,
    pub(super) use_cup_only_clear: bool,
    pub(super) force_redraw_after_preclear: bool,
    pub(super) force_full_banner_redraw: bool,
    pub(super) needs_redraw: bool,
    pub(super) consume_cursor_startup_preclear: bool,
}

#[derive(Debug, Clone, Copy, Default, PartialEq, Eq)]
pub(super) struct PreclearOutcome {
    pub(super) pre_cleared: bool,
    pub(super) force_redraw_after_preclear: bool,
    pub(super) force_full_banner_redraw: bool,
    pub(super) needs_redraw: bool,
    pub(super) consume_cursor_startup_preclear: bool,
}

impl PreclearPolicy {
    pub(super) fn resolve(ctx: PreclearPolicyContext<'_>) -> Self {
        let profile_should_preclear = should_preclear_bottom_rows(
            ctx.family,
            ctx.may_scroll_rows,
            ctx.display,
            ctx.status_clear_pending,
            ctx.codex_jetbrains,
            ctx.cursor_claude_startup_preclear,
            ctx.cursor_claude_banner_preclear,
            ctx.claude_jetbrains_banner_preclear,
            ctx.claude_jetbrains_cup_preclear_safe,
            ctx.now,
            ctx.last_preclear_at,
        );
        let should_preclear = (profile_should_preclear
            || ctx.claude_jetbrains_legacy_preclear_safe
            || (ctx.claude_jetbrains_banner_preclear && ctx.in_resize_repair_window))
            && !ctx.claude_jetbrains_destructive_clear
            && !ctx.preclear_blocked_for_recent_input;
        Self {
            should_preclear,
            use_cup_only_clear: should_preclear && ctx.claude_jetbrains_cup_preclear_safe,
            force_redraw_after_preclear: ctx.cursor_claude_banner_preclear
                || (ctx.claude_jetbrains_banner_preclear && ctx.in_resize_repair_window),
            force_full_banner_redraw: ctx.cursor_claude_banner_preclear
                || ctx.claude_jetbrains_banner_preclear,
            needs_redraw: ctx.claude_jetbrains_banner_preclear,
            consume_cursor_startup_preclear: ctx.cursor_claude_startup_preclear,
        }
    }

    pub(super) fn build_preclear_bytes(self, rows: u16, height: usize) -> Vec<u8> {
        if !self.should_preclear {
            return Vec::new();
        }
        if self.use_cup_only_clear {
            build_clear_bottom_rows_cup_only_bytes(rows, height)
        } else {
            build_clear_bottom_rows_bytes(rows, height)
        }
    }

    pub(super) fn outcome(self, pre_cleared: bool) -> PreclearOutcome {
        PreclearOutcome {
            pre_cleared,
            force_redraw_after_preclear: pre_cleared && self.force_redraw_after_preclear,
            force_full_banner_redraw: pre_cleared && self.force_full_banner_redraw,
            needs_redraw: pre_cleared && self.needs_redraw,
            consume_cursor_startup_preclear: pre_cleared && self.consume_cursor_startup_preclear,
        }
    }
}

#[derive(Clone, Copy)]
pub(super) struct RedrawPolicyContext<'a> {
    pub(super) family: TerminalHost,
    pub(super) runtime_variant: RuntimeVariant,
    pub(super) bytes: &'a [u8],
    pub(super) now: Instant,
    pub(super) last_scroll_redraw_at: Instant,
    pub(super) scroll_redraw_min_interval: Option<Duration>,
    pub(super) may_scroll_rows: bool,
    pub(super) display_force_full_banner_redraw: bool,
    pub(super) display_has_enhanced_status: bool,
    pub(super) display_has_unsuppressed_enhanced_status: bool,
    pub(super) display_should_force_full_banner_redraw_on_output: bool,
    pub(super) pending_clear_status: bool,
    pub(super) pending_clear_overlay: bool,
    pub(super) pending_overlay_panel_present: bool,
    pub(super) preclear_outcome: PreclearOutcome,
    pub(super) flash_sensitive_scroll_profile: bool,
    pub(super) claude_non_scroll_redraw_profile: bool,
    pub(super) claude_jetbrains_non_scroll_cursor_mutation: bool,
    pub(super) claude_jetbrains_composer_keystroke: bool,
    pub(super) claude_jetbrains_destructive_clear: bool,
    pub(super) claude_jetbrains_chunk_touches_cursor_save_restore: bool,
    pub(super) jetbrains_dec_cursor_saved_active: bool,
    pub(super) jetbrains_ansi_cursor_saved_active: bool,
    pub(super) claude_jetbrains_recent_destructive_clear_repaint: bool,
}

#[derive(Debug, Clone, Copy, Default, PartialEq, Eq)]
pub(super) struct RedrawPolicy {
    pub(super) force_full_banner_redraw: bool,
    pub(super) force_redraw_after_preclear: bool,
    pub(super) needs_redraw: bool,
    pub(super) update_last_scroll_redraw_at: bool,
    pub(super) output_redraw_needed: bool,
    pub(super) non_scroll_line_mutation: bool,
    pub(super) destructive_clear_repaint: bool,
    pub(super) jetbrains_claude_destructive_clear_repaint: bool,
    pub(super) immediate_reanchor_allowed: bool,
    pub(super) update_jetbrains_last_destructive_clear_repaint_at: bool,
    pub(super) schedule_jetbrains_destructive_clear_repair: bool,
    pub(super) jetbrains_repair_skip_quiet_window: bool,
}

impl RedrawPolicy {
    pub(super) fn resolve(ctx: RedrawPolicyContext<'_>) -> Self {
        let runtime_variant = ctx.runtime_variant;
        let jetbrains_claude_runtime = runtime_variant.is_jetbrains_claude();
        let jetbrains_codex_runtime = runtime_variant.is_jetbrains_codex();
        let cursor_claude_runtime = runtime_variant.is_cursor_claude();
        let mut policy = Self {
            force_full_banner_redraw: ctx.display_force_full_banner_redraw,
            ..Self::default()
        };
        let mut last_scroll_redraw_at = ctx.last_scroll_redraw_at;

        if ctx.may_scroll_rows
            && ctx.display_should_force_full_banner_redraw_on_output
            && should_force_scroll_full_redraw(
                ctx.scroll_redraw_min_interval,
                ctx.now,
                last_scroll_redraw_at,
            )
        {
            policy.force_full_banner_redraw = true;
            policy.update_last_scroll_redraw_at = true;
            last_scroll_redraw_at = ctx.now;
        }

        policy.non_scroll_line_mutation = if ctx.family != TerminalHost::JetBrains {
            let result = should_force_non_scroll_banner_redraw(
                ctx.family,
                ctx.claude_non_scroll_redraw_profile,
                ctx.may_scroll_rows,
                ctx.display_has_enhanced_status,
                ctx.bytes,
                ctx.now,
                last_scroll_redraw_at,
            );
            if result {
                policy.force_full_banner_redraw = true;
                policy.update_last_scroll_redraw_at = true;
            }
            result
        } else {
            false
        };

        if cursor_claude_runtime
            && !ctx.may_scroll_rows
            && ctx.display_has_enhanced_status
            && pty_output_can_mutate_cursor_line(ctx.bytes)
        {
            policy.force_full_banner_redraw = true;
            policy.force_redraw_after_preclear = true;
        }

        let cursor_claude_destructive_clear_repaint = cursor_claude_runtime
            && ctx.display_has_unsuppressed_enhanced_status
            && pty_output_contains_destructive_clear(ctx.bytes);
        policy.jetbrains_claude_destructive_clear_repaint = ctx.claude_jetbrains_destructive_clear;
        policy.destructive_clear_repaint = cursor_claude_destructive_clear_repaint
            || policy.jetbrains_claude_destructive_clear_repaint;
        if policy.destructive_clear_repaint {
            policy.force_full_banner_redraw = true;
            let jetbrains_cursor_slot_busy = jetbrains_claude_runtime
                && (ctx.claude_jetbrains_chunk_touches_cursor_save_restore
                    || ctx.jetbrains_dec_cursor_saved_active
                    || ctx.jetbrains_ansi_cursor_saved_active);
            policy.immediate_reanchor_allowed = !(jetbrains_cursor_slot_busy
                || (policy.jetbrains_claude_destructive_clear_repaint
                    && ctx.claude_jetbrains_recent_destructive_clear_repaint));
            if policy.immediate_reanchor_allowed {
                policy.force_redraw_after_preclear = true;
                policy.update_jetbrains_last_destructive_clear_repaint_at =
                    policy.jetbrains_claude_destructive_clear_repaint;
            }
            policy.needs_redraw = true;
            policy.update_last_scroll_redraw_at = true;
            if policy.jetbrains_claude_destructive_clear_repaint {
                policy.schedule_jetbrains_destructive_clear_repair = true;
                policy.jetbrains_repair_skip_quiet_window = true;
            }
        }

        if ctx.preclear_outcome.pre_cleared
            && ctx.family == TerminalHost::JetBrains
            && matches!(runtime_variant, RuntimeVariant::Generic)
        {
            let transition_sensitive_preclear = ctx.pending_clear_status
                || ctx.pending_clear_overlay
                || ctx.pending_overlay_panel_present;
            if transition_sensitive_preclear {
                // Transition clears need immediate repaint to avoid stale
                // border fragments during prompt/overlay handoff.
                policy.force_redraw_after_preclear = true;
            }
        }

        policy.output_redraw_needed = if jetbrains_claude_runtime {
            if ctx.may_scroll_rows {
                policy.force_full_banner_redraw = true;
                policy.needs_redraw = true;
            }
            if ctx.claude_jetbrains_non_scroll_cursor_mutation {
                policy.force_full_banner_redraw = true;
                policy.needs_redraw = true;
            }
            if ctx.claude_jetbrains_composer_keystroke {
                policy.needs_redraw = true;
            }
            // JetBrains+Claude redraw is idle-gated; avoid immediate redraw.
            false
        } else if jetbrains_codex_runtime {
            if ctx.may_scroll_rows {
                policy.force_full_banner_redraw = true;
                policy.needs_redraw = true;
            }
            ctx.preclear_outcome.pre_cleared
                || policy.non_scroll_line_mutation
                || policy.destructive_clear_repaint
        } else {
            policy.force_full_banner_redraw
                || ctx.preclear_outcome.pre_cleared
                || policy.non_scroll_line_mutation
                || policy.destructive_clear_repaint
                || (ctx.may_scroll_rows && !ctx.flash_sensitive_scroll_profile)
        };
        if policy.output_redraw_needed {
            policy.needs_redraw = true;
        }
        policy
    }
}

pub(super) fn should_preclear_bottom_rows(
    family: TerminalHost,
    may_scroll_rows: bool,
    display: &DisplayState,
    status_clear_pending: bool,
    codex_jetbrains: bool,
    cursor_claude_startup_preclear: bool,
    cursor_claude_banner_preclear: bool,
    claude_jetbrains_banner_preclear: bool,
    claude_jetbrains_cup_preclear_safe: bool,
    now: Instant,
    last_preclear_at: Instant,
) -> bool {
    if !may_scroll_rows || preclear_height(display) == 0 {
        return false;
    }
    let host_timing = HostTimingConfig::for_host(family);
    match family {
        TerminalHost::JetBrains => {
            if claude_jetbrains_banner_preclear {
                // JetBrains + Claude: only run pre-clear when the chunk begins
                // with absolute cursor positioning. This allows a CUP-only
                // pre-clear (no DEC save/restore slot collision) without
                // risking prompt/input jumps to row 1.
                return claude_jetbrains_cup_preclear_safe
                    && host_timing
                        .claude_banner_preclear_cooldown()
                        .is_some_and(|cooldown| now.duration_since(last_preclear_at) >= cooldown);
            }
            // Codex and other backends: keep conservative transition-only pre-clear.
            (status_clear_pending || display.overlay_panel.is_some())
                && !codex_jetbrains
                && now.duration_since(last_preclear_at) >= host_timing.preclear_cooldown()
        }
        // Cursor should avoid banner pre-clear because it can visibly jitter the
        // active composer line while typing during heavy tool output. Keep a
        // conservative pre-clear path for explicit overlay panels and
        // suppression clear transitions that must scrub stale border fragments.
        // Also allow one startup pre-clear in Claude mode so first-frame HUD
        // rows do not get scrolled into duplicate ghost fragments.
        TerminalHost::Cursor => {
            let transition_preclear = display.overlay_panel.is_some()
                || status_clear_pending
                || cursor_claude_startup_preclear;
            if transition_preclear {
                return now.duration_since(last_preclear_at) >= host_timing.preclear_cooldown();
            }
            if cursor_claude_banner_preclear {
                // Cursor+Claude scroll streams can smear HUD rows into transcript
                // history if we wait for cadence windows; pre-clear every
                // scrolling chunk and redraw immediately.
                return true;
            }
            false
        }
        // Preserve legacy behavior for non-profiled terminals.
        TerminalHost::Other => true,
    }
}

#[cfg(test)]
pub(super) fn scroll_redraw_min_interval_for_profile(
    family: TerminalHost,
    codex_backend: bool,
    claude_backend: bool,
) -> Option<Duration> {
    let host_timing = HostTimingConfig::for_host(family);
    let backend = if codex_backend {
        BackendFamily::Codex
    } else if claude_backend {
        BackendFamily::Claude
    } else {
        BackendFamily::Other
    };
    host_timing.scroll_redraw_min_interval(backend)
}

pub(super) fn should_force_scroll_full_redraw(
    min_interval: Option<Duration>,
    now: Instant,
    last_scroll_redraw_at: Instant,
) -> bool {
    if let Some(interval) = min_interval {
        return now.duration_since(last_scroll_redraw_at) >= interval;
    }
    true
}

pub(super) fn should_force_non_scroll_banner_redraw(
    terminal_family: TerminalHost,
    claude_flash_profile: bool,
    may_scroll_rows: bool,
    has_enhanced_status: bool,
    bytes: &[u8],
    now: Instant,
    last_scroll_redraw_at: Instant,
) -> bool {
    let min_interval =
        HostTimingConfig::for_host(terminal_family).claude_non_scroll_redraw_min_interval();
    claude_flash_profile
        && !may_scroll_rows
        && has_enhanced_status
        && pty_output_can_mutate_cursor_line(bytes)
        && min_interval.is_some()
        && should_force_scroll_full_redraw(min_interval, now, last_scroll_redraw_at)
}
