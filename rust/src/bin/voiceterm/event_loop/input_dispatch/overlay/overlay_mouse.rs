//! Overlay mouse interaction helpers extracted from input dispatch.

use super::*;
use crate::dev_panel::{
    dev_panel_footer, dev_panel_height, dev_panel_inner_width_for_terminal,
    dev_panel_width_for_terminal,
};
use crate::transcript_history::transcript_history_visible_rows;

pub(super) fn handle_overlay_mouse_click(
    state: &mut EventLoopState,
    timers: &mut EventLoopTimers,
    deps: &mut EventLoopDeps,
    running: &mut bool,
    x: u16,
    y: u16,
) {
    if !state.status_state.mouse_enabled {
        return;
    }

    let overlay_height = match state.ui.overlay_mode {
        OverlayMode::DevPanel => dev_panel_height(),
        OverlayMode::Help => help_overlay_height(),
        OverlayMode::ThemeStudio => theme_studio_height(),
        OverlayMode::ThemePicker => theme_picker_height(),
        OverlayMode::Settings => settings_overlay_height(),
        OverlayMode::TranscriptHistory => transcript_history_overlay_height(),
        OverlayMode::ToastHistory => {
            crate::toast::toast_history_overlay_height(&state.toast_center)
        }
        OverlayMode::None => 0,
    };
    if overlay_height == 0 {
        return;
    }
    if state.ui.terminal_rows == 0 {
        return;
    }
    let overlay_top_y = state
        .ui
        .terminal_rows
        .saturating_sub(overlay_height as u16)
        .saturating_add(1);
    if !(overlay_top_y..=state.ui.terminal_rows).contains(&y) {
        return;
    }
    let overlay_row = (y - overlay_top_y) as usize + 1;
    let cols = resolved_cols(state.ui.terminal_cols) as usize;

    let (overlay_width, inner_width, footer_title) = match state.ui.overlay_mode {
        OverlayMode::DevPanel => (
            dev_panel_width_for_terminal(cols),
            dev_panel_inner_width_for_terminal(cols),
            dev_panel_footer(&state.theme.colors()),
        ),
        OverlayMode::Help => (
            help_overlay_width_for_terminal(cols),
            help_overlay_inner_width_for_terminal(cols),
            help_overlay_footer(&state.theme.colors()),
        ),
        OverlayMode::ThemeStudio => (
            theme_studio_total_width_for_terminal(cols),
            theme_studio_inner_width_for_terminal(cols),
            theme_studio_footer(&state.theme.colors()),
        ),
        OverlayMode::ThemePicker => (
            theme_picker_total_width_for_terminal(cols),
            theme_picker_inner_width_for_terminal(cols),
            theme_picker_footer(&state.theme.colors(), style_pack_theme_lock()),
        ),
        OverlayMode::Settings => (
            settings_overlay_width_for_terminal(cols),
            settings_overlay_inner_width_for_terminal(cols),
            settings_overlay_footer(&state.theme.colors()),
        ),
        OverlayMode::TranscriptHistory => (
            crate::transcript_history::transcript_history_overlay_width(cols),
            crate::transcript_history::transcript_history_overlay_inner_width(cols),
            crate::transcript_history::transcript_history_overlay_footer(&state.theme.colors()),
        ),
        OverlayMode::ToastHistory => {
            // Toast history overlay uses full-width panel with standard close footer.
            let toast_width = cols.min(60);
            let toast_inner = toast_width.saturating_sub(4);
            let colors = state.theme.colors();
            let sep = crate::theme::overlay_separator(colors.glyph_set);
            let close_sym = crate::theme::overlay_close_symbol(colors.glyph_set);
            let footer = format!(
                "[{close_sym}] close {sep} {} total",
                state.toast_center.history_count()
            );
            (toast_width, toast_inner, footer)
        }
        OverlayMode::None => (0, 0, String::new()),
    };

    if overlay_width == 0 {
        return;
    }
    let centered_overlay_left = cols.saturating_sub(overlay_width) / 2 + 1;
    let centered_overlay_right = centered_overlay_left.saturating_add(overlay_width);
    let x_usize = x as usize;
    let centered_hit = x_usize >= centered_overlay_left && x_usize < centered_overlay_right;
    let rel_x = if centered_hit {
        x_usize
            .saturating_sub(centered_overlay_left)
            .saturating_add(1)
    } else if (1..=overlay_width).contains(&x_usize) {
        x_usize
    } else {
        return;
    };

    let footer_row = overlay_height.saturating_sub(1);
    if overlay_row == footer_row {
        let title_len = crate::overlay_frame::display_width(&footer_title);
        let left_pad = inner_width.saturating_sub(title_len) / 2;
        let close_prefix = footer_close_prefix(&footer_title);
        let close_len = crate::overlay_frame::display_width(close_prefix);
        let close_start = 2usize.saturating_add(left_pad);
        let close_end = close_start.saturating_add(close_len.saturating_sub(1));
        if rel_x >= close_start && rel_x <= close_end {
            close_overlay(state, deps, true);
        }
        return;
    }

    if state.ui.overlay_mode == OverlayMode::ThemePicker {
        let options_start = THEME_PICKER_OPTION_START_ROW;
        let options_end = options_start.saturating_add(THEME_OPTIONS.len().saturating_sub(1));
        if overlay_row >= options_start
            && overlay_row <= options_end
            && rel_x > 1
            && rel_x < overlay_width
        {
            let idx = overlay_row.saturating_sub(options_start);
            super::apply_theme_picker_selection(state, timers, deps, idx);
        }
        return;
    }

    if state.ui.overlay_mode == OverlayMode::ThemeStudio {
        let options_start = THEME_STUDIO_OPTION_START_ROW;
        let options_end = options_start.saturating_add(THEME_STUDIO_ITEMS.len().saturating_sub(1));
        if overlay_row >= options_start
            && overlay_row <= options_end
            && rel_x > 1
            && rel_x < overlay_width
        {
            state.theme_studio.selected = overlay_row.saturating_sub(options_start);
            super::theme_studio_input::apply_theme_studio_selection(state, timers, deps, running);
            if state.ui.overlay_mode == OverlayMode::ThemeStudio {
                render_theme_studio_overlay_for_state(state, deps);
            }
        }
        return;
    }

    if state.ui.overlay_mode == OverlayMode::TranscriptHistory {
        let entry_start = crate::transcript_history::TRANSCRIPT_HISTORY_ENTRY_START_ROW;
        let visible = transcript_history_visible_rows();
        let entry_end = entry_start.saturating_add(visible.saturating_sub(1));
        if overlay_row >= entry_start
            && overlay_row <= entry_end
            && rel_x > 1
            && rel_x < overlay_width
        {
            let display_idx = overlay_row.saturating_sub(entry_start);
            let abs_idx = state.transcript_history_state.scroll_offset + display_idx;
            if abs_idx < state.transcript_history_state.filtered_indices.len() {
                state.transcript_history_state.selected = abs_idx;
                render_transcript_history_overlay_for_state(state, deps);
            }
        }
        return;
    }

    if state.ui.overlay_mode == OverlayMode::Settings {
        let options_start = SETTINGS_OPTION_START_ROW;
        let options_end = options_start.saturating_add(SETTINGS_ITEMS.len().saturating_sub(1));
        if overlay_row < options_start
            || overlay_row > options_end
            || rel_x <= 1
            || rel_x >= overlay_width
        {
            return;
        }

        let selected_idx = overlay_row.saturating_sub(options_start);
        state.settings.menu.selected = selected_idx.min(SETTINGS_ITEMS.len().saturating_sub(1));

        let selected = state.settings.menu.selected_item();
        match selected {
            SettingsItem::Backend | SettingsItem::Pipeline => {}
            SettingsItem::Close => {
                close_overlay(state, deps, false);
                return;
            }
            SettingsItem::Quit => {
                *running = false;
                return;
            }
            _ => {
                let direction = settings_mouse_direction_for_item(state, selected, rel_x);
                let _ = super::run_settings_item_action(
                    state,
                    timers,
                    deps,
                    selected,
                    direction,
                    state.ui.overlay_mode,
                );
            }
        }

        if state.ui.overlay_mode == OverlayMode::Settings {
            render_settings_overlay_for_state(state, deps);
        }
    }
}

fn footer_close_prefix(footer_title: &str) -> &str {
    let dot_split = footer_title.split('·').next().unwrap_or(footer_title);
    dot_split.split('|').next().unwrap_or(dot_split).trim_end()
}

const SETTINGS_SLIDER_LABEL_WIDTH: usize = 15;
const SETTINGS_SLIDER_WIDTH: usize = 14;
const SETTINGS_SLIDER_START_REL_X: usize = 2 + 1 + 1 + SETTINGS_SLIDER_LABEL_WIDTH + 1;
const SETTINGS_VAD_MIN_DB: f32 = -80.0;
const SETTINGS_VAD_MAX_DB: f32 = -10.0;

fn settings_mouse_direction_for_item(
    state: &EventLoopState,
    selected: SettingsItem,
    rel_x: usize,
) -> i32 {
    match selected {
        SettingsItem::Sensitivity => {
            let knob = slider_knob_index_for_range(
                state.status_state.sensitivity_db,
                SETTINGS_VAD_MIN_DB,
                SETTINGS_VAD_MAX_DB,
                SETTINGS_SLIDER_WIDTH,
            );
            slider_direction_from_click(
                rel_x,
                SETTINGS_SLIDER_START_REL_X,
                SETTINGS_SLIDER_WIDTH,
                knob,
            )
            .unwrap_or(1)
        }
        SettingsItem::WakeSensitivity => {
            let knob = slider_knob_index_for_range(
                state.config.wake_word_sensitivity,
                0.0,
                1.0,
                SETTINGS_SLIDER_WIDTH,
            );
            slider_direction_from_click(
                rel_x,
                SETTINGS_SLIDER_START_REL_X,
                SETTINGS_SLIDER_WIDTH,
                knob,
            )
            .unwrap_or(1)
        }
        _ => 1,
    }
}

fn slider_direction_from_click(
    rel_x: usize,
    slider_start: usize,
    slider_width: usize,
    knob_index: usize,
) -> Option<i32> {
    if slider_width == 0 {
        return None;
    }
    let slider_end = slider_start.saturating_add(slider_width.saturating_sub(1));
    if rel_x < slider_start || rel_x > slider_end {
        return None;
    }
    let knob_x = slider_start.saturating_add(knob_index.min(slider_width.saturating_sub(1)));
    if rel_x < knob_x {
        Some(-1)
    } else if rel_x > knob_x {
        Some(1)
    } else {
        Some(0)
    }
}

fn slider_knob_index_for_range(value: f32, min: f32, max: f32, width: usize) -> usize {
    if width <= 1 {
        return 0;
    }
    let clamped = value.clamp(min, max);
    let ratio = if (max - min).abs() < f32::EPSILON {
        0.0
    } else {
        (clamped - min) / (max - min)
    };
    ((width.saturating_sub(1)) as f32 * ratio).round() as usize
}

#[cfg(test)]
mod tests {
    use super::{
        footer_close_prefix, slider_direction_from_click, slider_knob_index_for_range,
        SETTINGS_SLIDER_START_REL_X, SETTINGS_VAD_MAX_DB,
    };

    #[test]
    fn footer_close_prefix_extracts_close_label_before_dot_and_pipe() {
        let footer = "[x] close | up/down move | Enter select · Click/Tap select";
        assert_eq!(footer_close_prefix(footer), "[x] close");
    }

    #[test]
    fn footer_close_prefix_falls_back_when_separators_are_missing() {
        assert_eq!(footer_close_prefix("close only"), "close only");
    }

    #[test]
    fn slider_constants_match_expected_overlay_geometry() {
        assert_eq!(SETTINGS_SLIDER_START_REL_X, 20);
        assert_eq!(SETTINGS_VAD_MAX_DB, -10.0);
    }

    #[test]
    fn slider_direction_handles_empty_and_out_of_range_clicks() {
        assert_eq!(slider_direction_from_click(3, 3, 0, 0), None);
        assert_eq!(slider_direction_from_click(2, 3, 5, 0), None);
        assert_eq!(slider_direction_from_click(8, 3, 5, 0), None);
    }

    #[test]
    fn slider_direction_maps_left_right_and_knob_hit() {
        let slider_start = 3;
        let slider_width = 5;
        let knob_index = 2;

        assert_eq!(
            slider_direction_from_click(4, slider_start, slider_width, knob_index),
            Some(-1)
        );
        assert_eq!(
            slider_direction_from_click(5, slider_start, slider_width, knob_index),
            Some(0)
        );
        assert_eq!(
            slider_direction_from_click(6, slider_start, slider_width, knob_index),
            Some(1)
        );
    }

    #[test]
    fn slider_knob_index_uses_zero_when_width_is_one_or_less() {
        assert_eq!(slider_knob_index_for_range(10.0, 0.0, 100.0, 0), 0);
        assert_eq!(slider_knob_index_for_range(10.0, 0.0, 100.0, 1), 0);
    }

    #[test]
    fn slider_knob_index_uses_epsilon_guard_for_near_zero_span() {
        let min = 0.0;
        let almost_equal = f32::EPSILON * 0.5;
        let exactly_epsilon = f32::EPSILON;
        let width = 11;

        assert_eq!(
            slider_knob_index_for_range(almost_equal, min, almost_equal, width),
            0
        );
        assert_eq!(
            slider_knob_index_for_range(exactly_epsilon, min, exactly_epsilon, width),
            width - 1
        );
    }

    #[test]
    fn slider_knob_index_scales_linearly_across_range() {
        let width = 11;
        assert_eq!(slider_knob_index_for_range(-1.0, -1.0, 1.0, width), 0);
        assert_eq!(slider_knob_index_for_range(0.0, -1.0, 1.0, width), 5);
        assert_eq!(
            slider_knob_index_for_range(1.0, -1.0, 1.0, width),
            width - 1
        );
    }

    #[test]
    fn slider_knob_index_clamps_outside_range() {
        let width = 11;
        assert_eq!(slider_knob_index_for_range(-10.0, 0.0, 100.0, width), 0);
        assert_eq!(
            slider_knob_index_for_range(1000.0, 0.0, 100.0, width),
            width - 1
        );
    }
}
