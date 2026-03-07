use super::*;

pub(super) struct RedrawContext {
    pub(super) now: Instant,
    pub(super) cursor_input_repair_profile: bool,
    pub(super) jetbrains_prompt_guard_profile: bool,
    pub(super) claude_cursor_debug: bool,
    pub(super) suppression_transition_pending: bool,
}

pub(super) struct RedrawSnapshot {
    pub(super) previous_banner_height: usize,
    pub(super) previous_hud_style: Option<HudStyle>,
    pub(super) previous_prompt_suppressed: Option<bool>,
}

pub(super) fn build_redraw_render_state(
    state: &crate::status_line::StatusLineState,
    jetbrains_prompt_guard_profile: bool,
) -> crate::status_line::StatusLineState {
    let mut render_state = state.clone();
    if jetbrains_prompt_guard_profile
        && !render_state.prompt_suppressed
        && render_state.hud_style == HudStyle::Full
    {
        // JetBrains+Claude fallback: keep full-HUD semantics but collapse
        // the full frame into a single-line strip to avoid row drift under
        // synchronized clear/redraw bursts in JetBrains.
        if claude_hud_debug_enabled() {
            log_debug("[claude-hud-debug] applying jetbrains+claude full-hud one-line fallback");
        }
        render_state.hud_border_style = HudBorderStyle::None;
        render_state.full_hud_single_line = true;
    }
    render_state
}

pub(super) fn redraw_anchor_row(rows: u16, banner_height: usize) -> Option<u16> {
    if banner_height == 0 || rows == 0 {
        return None;
    }
    Some(
        rows.saturating_sub(banner_height.min(rows as usize) as u16)
            .saturating_add(1),
    )
}
