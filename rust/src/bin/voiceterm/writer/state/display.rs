use crate::runtime_compat::TerminalHost;
use crate::status_line::StatusLineState;
use crate::HudStyle;

#[derive(Debug, Clone)]
pub(in super::super) struct OverlayPanel {
    pub(in super::super) content: String,
    pub(in super::super) height: usize,
}

#[derive(Debug, Default)]
pub(super) struct DisplayState {
    pub(super) status: Option<String>,
    pub(super) enhanced_status: Option<StatusLineState>,
    pub(super) overlay_panel: Option<OverlayPanel>,
    pub(super) banner_height: usize,
    /// Last non-zero banner height, kept across prompt-suppression transitions
    /// so pre-clear continues to scrub HUD rows even when the banner is hidden.
    pub(super) preclear_banner_height: usize,
    /// Last absolute start-row anchor where a banner frame was rendered.
    /// Used to scrub stale frames if anchor drifts due geometry timing.
    pub(super) banner_anchor_row: Option<u16>,
    pub(super) banner_lines: Vec<String>,
    pub(super) force_full_banner_redraw: bool,
}

impl DisplayState {
    pub(super) fn has_any(&self) -> bool {
        self.status.is_some() || self.enhanced_status.is_some() || self.overlay_panel.is_some()
    }

    pub(super) fn should_force_full_banner_redraw_on_output(
        &self,
        terminal_family: TerminalHost,
    ) -> bool {
        if self.overlay_panel.is_some() || self.status.is_some() {
            return true;
        }
        // Multi-row HUDs need full repaint after terminal row scrolling.
        // On Cursor, skipping this can leave only the changing main row visible
        // while border/buttons rows scroll away under heavy output.
        match terminal_family {
            // JetBrains: suppress output-triggered HUD redraw when Claude
            // is active. Claude Code's TUI uses DEC save/restore (\x1b7/\x1b8)
            // in its own rendering; the save slot is shared globally, so our
            // HUD redraw's \x1b7 can be overwritten by Claude's output before
            // our \x1b8 fires, leaving the cursor stuck inside the HUD.
            // The HUD still redraws on timer ticks when output is idle.
            TerminalHost::JetBrains => false,
            TerminalHost::Cursor | TerminalHost::Other => self.banner_height > 1,
        }
    }
}

#[derive(Debug, Default)]
pub(super) struct PendingState {
    pub(super) status: Option<String>,
    pub(super) enhanced_status: Option<StatusLineState>,
    pub(super) overlay_panel: Option<OverlayPanel>,
    pub(super) clear_status: bool,
    pub(super) clear_overlay: bool,
}

impl PendingState {
    pub(super) fn has_any(&self) -> bool {
        self.status.is_some()
            || self.enhanced_status.is_some()
            || self.overlay_panel.is_some()
            || self.clear_status
            || self.clear_overlay
    }
}

pub(super) fn status_clear_height_for_redraw(current_height: usize, next_height: usize) -> usize {
    if current_height > next_height {
        current_height
    } else {
        0
    }
}

pub(super) fn should_use_previous_banner_lines(
    force_full_banner_redraw: bool,
    force_redraw_after_preclear: bool,
) -> bool {
    // Transition redraws that follow a pre-clear must repaint all HUD lines.
    // The terminal rows were already wiped; reusing cached previous-lines can
    // skip writes and leave the HUD visually blank.
    !force_full_banner_redraw && !force_redraw_after_preclear
}

pub(super) fn should_use_previous_banner_lines_for_profile(
    terminal_family: TerminalHost,
    force_full_banner_redraw: bool,
    force_redraw_after_preclear: bool,
) -> bool {
    if terminal_family == TerminalHost::JetBrains {
        // JediTerm can leave stale prompt/input text in unchanged HUD lanes
        // when line-diff redraw skips rows. Always repaint all banner rows.
        // This applies to both Claude and Codex backends; scrolling output
        // pushes HUD rows off screen and line-diff skips rewriting them.
        return false;
    }
    should_use_previous_banner_lines(force_full_banner_redraw, force_redraw_after_preclear)
}

pub(super) fn preclear_height(display: &DisplayState) -> usize {
    if let Some(panel) = display.overlay_panel.as_ref() {
        panel.height
    } else if display.preclear_banner_height > 1 {
        // Use preclear_banner_height (last non-zero value) instead of
        // banner_height so prompt-suppression transitions don't disable
        // pre-clear and allow old HUD frames to scroll into the content area.
        display.preclear_banner_height
    } else {
        0
    }
}

pub(super) fn is_unsuppressed_full_hud(state: &StatusLineState) -> bool {
    !state.prompt_suppressed && state.hud_style == HudStyle::Full
}
