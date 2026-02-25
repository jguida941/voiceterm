use super::*;

const THEME_STUDIO_HISTORY_LIMIT: usize = 64;
const COLOR_PICKER_HEX_MAX_LEN: usize = 7;

pub(super) fn handle_theme_studio_enter_key(
    state: &mut EventLoopState,
    timers: &mut EventLoopTimers,
    deps: &mut EventLoopDeps,
    running: &mut bool,
) {
    use crate::theme_studio::StudioPage;
    match state.theme_studio_page {
        StudioPage::Home => {
            apply_theme_studio_selection(state, timers, deps, running);
        }
        StudioPage::Colors => {
            if let Some(editor) = state.theme_studio_colors_editor.as_mut() {
                if editor.is_color_field_selected() {
                    if let Some(picker) = editor.picker.as_mut() {
                        if picker.hex_entry_mode && !picker.apply_hex_buffer() {
                            render_theme_studio_overlay_for_state(state, deps);
                            return;
                        }
                        editor.apply_picker();
                    } else {
                        editor.open_picker();
                    }
                    // Apply edited colors to the live runtime theme.
                    #[cfg(not(test))]
                    {
                        let legacy = editor.colors.to_legacy_theme_colors();
                        crate::theme::set_runtime_color_override(legacy);
                    }
                }
                // For indicator/glyph rows, Enter is a no-op (use ←/→).
                render_theme_studio_overlay_for_state(state, deps);
            }
        }
        StudioPage::Borders => {
            // Apply the selected border style override.
            let option = state.theme_studio_borders_page.selected_option();
            let border_override = match option {
                crate::theme_studio::BorderOption::Single => {
                    Some(crate::theme::RuntimeBorderStyleOverride::Single)
                }
                crate::theme_studio::BorderOption::Rounded => {
                    Some(crate::theme::RuntimeBorderStyleOverride::Rounded)
                }
                crate::theme_studio::BorderOption::Double => {
                    Some(crate::theme::RuntimeBorderStyleOverride::Double)
                }
                crate::theme_studio::BorderOption::Heavy => {
                    Some(crate::theme::RuntimeBorderStyleOverride::Heavy)
                }
                crate::theme_studio::BorderOption::None => {
                    Some(crate::theme::RuntimeBorderStyleOverride::None)
                }
            };
            let mut overrides = crate::theme::runtime_style_pack_overrides();
            overrides.border_style_override = border_override;
            crate::theme::set_runtime_style_pack_overrides(overrides);
            render_theme_studio_overlay_for_state(state, deps);
        }
        StudioPage::Components => {
            state.theme_studio_components_editor.toggle_expand();
            render_theme_studio_overlay_for_state(state, deps);
        }
        StudioPage::Preview => {
            // Preview is read-only, Enter does nothing.
            render_theme_studio_overlay_for_state(state, deps);
        }
        StudioPage::Export => {
            let theme = state.theme;
            let status = state.theme_studio_export_page.execute(theme, None);
            let _ = status; // status is rendered in the overlay redraw below
            render_theme_studio_overlay_for_state(state, deps);
        }
    }
}

pub(super) fn handle_theme_studio_bytes(
    state: &mut EventLoopState,
    timers: &mut EventLoopTimers,
    deps: &mut EventLoopDeps,
    bytes: &[u8],
) {
    use crate::theme_studio::StudioPage;
    if bytes == [0x1b] {
        // Esc: if color picker is open, close it; otherwise close overlay.
        if state.theme_studio_page == StudioPage::Colors {
            if let Some(editor) = state.theme_studio_colors_editor.as_mut() {
                if editor.picker.is_some() {
                    editor.picker = None;
                    render_theme_studio_overlay_for_state(state, deps);
                    return;
                }
            }
        }
        close_overlay(state, deps, false);
        return;
    }

    if bytes == [0x09] {
        // Tab: switch to next studio page.
        state.theme_studio_page = state.theme_studio_page.next();
        ensure_studio_page_state(state);
        render_theme_studio_overlay_for_state(state, deps);
        return;
    }

    if bytes == [0x1b, 0x5b, 0x5a] {
        // Shift+Tab (ESC [ Z): switch to previous studio page.
        state.theme_studio_page = state.theme_studio_page.prev();
        ensure_studio_page_state(state);
        render_theme_studio_overlay_for_state(state, deps);
        return;
    }

    let mut should_redraw = false;
    match state.theme_studio_page {
        StudioPage::Home => {
            for key in parse_arrow_keys(bytes) {
                match key {
                    ArrowKey::Up => {
                        if state.theme_studio_selected > 0 {
                            state.theme_studio_selected =
                                state.theme_studio_selected.saturating_sub(1);
                            should_redraw = true;
                        }
                    }
                    ArrowKey::Down => {
                        let max = THEME_STUDIO_ITEMS.len().saturating_sub(1);
                        if state.theme_studio_selected < max {
                            state.theme_studio_selected += 1;
                            should_redraw = true;
                        }
                    }
                    ArrowKey::Left => {
                        should_redraw |= apply_theme_studio_adjustment(state, timers, deps, -1);
                    }
                    ArrowKey::Right => {
                        should_redraw |= apply_theme_studio_adjustment(state, timers, deps, 1);
                    }
                }
            }
        }
        StudioPage::Colors => {
            if let Some(editor) = state.theme_studio_colors_editor.as_mut() {
                if editor.picker.is_some() {
                    should_redraw |= handle_color_picker_text_input(editor, bytes);
                    let mut color_changed = false;
                    if let Some(picker) = editor.picker.as_mut() {
                        for key in parse_arrow_keys(bytes) {
                            match key {
                                ArrowKey::Up => {
                                    picker.channel = picker.channel.prev();
                                    should_redraw = true;
                                }
                                ArrowKey::Down => {
                                    picker.channel = picker.channel.next();
                                    should_redraw = true;
                                }
                                ArrowKey::Left => {
                                    picker.adjust_channel(-1);
                                    color_changed = true;
                                    should_redraw = true;
                                }
                                ArrowKey::Right => {
                                    picker.adjust_channel(1);
                                    color_changed = true;
                                    should_redraw = true;
                                }
                            }
                        }
                    }
                    // Live-preview: apply current picker color as the user drags sliders.
                    if color_changed {
                        if let Some(ref picker) = editor.picker {
                            let field = editor.selected_field();
                            field.set(
                                &mut editor.colors,
                                crate::theme::color_value::ColorValue::Rgb(picker.rgb),
                            );
                        }
                        #[cfg(not(test))]
                        {
                            let legacy = editor.colors.to_legacy_theme_colors();
                            crate::theme::set_runtime_color_override(legacy);
                        }
                    }
                } else {
                    for key in parse_arrow_keys(bytes) {
                        match key {
                            ArrowKey::Up => {
                                editor.select_prev();
                                should_redraw = true;
                            }
                            ArrowKey::Down => {
                                editor.select_next();
                                should_redraw = true;
                            }
                            ArrowKey::Left | ArrowKey::Right => {
                                let dir = if matches!(key, ArrowKey::Right) {
                                    1
                                } else {
                                    -1
                                };
                                let field_count = crate::theme_studio::ColorField::ALL.len();
                                if editor.selected == field_count {
                                    // Indicator set selector.
                                    if editor.cycle_indicator_set(dir) {
                                        let mut overrides =
                                            crate::theme::runtime_style_pack_overrides();
                                        overrides.indicator_set_override = editor.indicator_set;
                                        crate::theme::set_runtime_style_pack_overrides(overrides);
                                        should_redraw = true;
                                    }
                                } else if editor.selected == field_count + 1 {
                                    // Glyph set selector.
                                    if editor.cycle_glyph_set(dir) {
                                        let mut overrides =
                                            crate::theme::runtime_style_pack_overrides();
                                        overrides.glyph_set_override = editor.glyph_set;
                                        crate::theme::set_runtime_style_pack_overrides(overrides);
                                        should_redraw = true;
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        StudioPage::Borders => {
            for key in parse_arrow_keys(bytes) {
                match key {
                    ArrowKey::Up => {
                        state.theme_studio_borders_page.select_prev();
                        should_redraw = true;
                    }
                    ArrowKey::Down => {
                        state.theme_studio_borders_page.select_next();
                        should_redraw = true;
                    }
                    ArrowKey::Left | ArrowKey::Right => {}
                }
            }
        }
        StudioPage::Components => {
            for key in parse_arrow_keys(bytes) {
                match key {
                    ArrowKey::Up => {
                        state.theme_studio_components_editor.select_prev();
                        should_redraw = true;
                    }
                    ArrowKey::Down => {
                        let max = state.theme_studio_components_editor.group_count();
                        state.theme_studio_components_editor.select_next(max);
                        should_redraw = true;
                    }
                    ArrowKey::Left | ArrowKey::Right => {}
                }
            }
        }
        StudioPage::Preview => {
            for key in parse_arrow_keys(bytes) {
                match key {
                    ArrowKey::Up => {
                        state.theme_studio_preview_page.scroll_up();
                        should_redraw = true;
                    }
                    ArrowKey::Down => {
                        state.theme_studio_preview_page.scroll_down(20, 10);
                        should_redraw = true;
                    }
                    ArrowKey::Left | ArrowKey::Right => {}
                }
            }
        }
        StudioPage::Export => {
            for key in parse_arrow_keys(bytes) {
                match key {
                    ArrowKey::Up => {
                        state.theme_studio_export_page.select_prev();
                        should_redraw = true;
                    }
                    ArrowKey::Down => {
                        state.theme_studio_export_page.select_next();
                        should_redraw = true;
                    }
                    ArrowKey::Left | ArrowKey::Right => {}
                }
            }
        }
    }

    if should_redraw {
        render_theme_studio_overlay_for_state(state, deps);
    }
}

/// Lazily initialize page-specific state when switching studio pages.
pub(super) fn ensure_studio_page_state(state: &mut EventLoopState) {
    use crate::theme_studio::{ColorsEditorState, StudioPage};
    if state.theme_studio_page == StudioPage::Colors && state.theme_studio_colors_editor.is_none() {
        state.theme_studio_colors_editor = Some(ColorsEditorState::new(state.theme));
    }
}

fn handle_color_picker_text_input(
    editor: &mut crate::theme_studio::ColorsEditorState,
    bytes: &[u8],
) -> bool {
    let Some(picker) = editor.picker.as_mut() else {
        return false;
    };
    if bytes.len() != 1 {
        return false;
    }
    match bytes[0] {
        b'h' | b'H' => {
            picker.toggle_hex_mode();
            true
        }
        0x08 | 0x7f => {
            if picker.hex_entry_mode && picker.hex_buffer.len() > 1 {
                picker.hex_buffer.pop();
                true
            } else {
                false
            }
        }
        b'#' => {
            if picker.hex_entry_mode && picker.hex_buffer.is_empty() {
                picker.hex_buffer.push('#');
                true
            } else {
                false
            }
        }
        b'0'..=b'9' | b'a'..=b'f' | b'A'..=b'F' => {
            if picker.hex_entry_mode && picker.hex_buffer.len() < COLOR_PICKER_HEX_MAX_LEN {
                if picker.hex_buffer.is_empty() {
                    picker.hex_buffer.push('#');
                }
                picker
                    .hex_buffer
                    .push((bytes[0] as char).to_ascii_lowercase());
                true
            } else {
                false
            }
        }
        _ => false,
    }
}

fn apply_theme_studio_adjustment(
    state: &mut EventLoopState,
    timers: &mut EventLoopTimers,
    deps: &mut EventLoopDeps,
    direction: i32,
) -> bool {
    match theme_studio_item_at(state.theme_studio_selected) {
        ThemeStudioItem::HudStyle => super::run_settings_item_action(
            state,
            timers,
            deps,
            SettingsItem::HudStyle,
            direction,
            OverlayMode::ThemeStudio,
        ),
        ThemeStudioItem::HudBorders => super::run_settings_item_action(
            state,
            timers,
            deps,
            SettingsItem::HudBorders,
            direction,
            OverlayMode::ThemeStudio,
        ),
        ThemeStudioItem::HudPanel => super::run_settings_item_action(
            state,
            timers,
            deps,
            SettingsItem::HudPanel,
            direction,
            OverlayMode::ThemeStudio,
        ),
        ThemeStudioItem::HudAnimate => super::run_settings_item_action(
            state,
            timers,
            deps,
            SettingsItem::HudAnimate,
            direction,
            OverlayMode::ThemeStudio,
        ),
        ThemeStudioItem::ColorsGlyphs => {
            apply_theme_studio_runtime_override_edit(state, |overrides| {
                overrides.glyph_set_override = super::cycle_runtime_glyph_set_override(
                    overrides.glyph_set_override,
                    direction,
                );
            })
        }
        ThemeStudioItem::LayoutMotion => {
            apply_theme_studio_runtime_override_edit(state, |overrides| {
                overrides.indicator_set_override = super::cycle_runtime_indicator_set_override(
                    overrides.indicator_set_override,
                    direction,
                );
            })
        }
        ThemeStudioItem::ProgressSpinner => {
            apply_theme_studio_runtime_override_edit(state, |overrides| {
                overrides.progress_style_override = super::cycle_runtime_progress_style_override(
                    overrides.progress_style_override,
                    direction,
                );
            })
        }
        ThemeStudioItem::ProgressBars => {
            apply_theme_studio_runtime_override_edit(state, |overrides| {
                overrides.progress_bar_family_override =
                    super::cycle_runtime_progress_bar_family_override(
                        overrides.progress_bar_family_override,
                        direction,
                    );
            })
        }
        ThemeStudioItem::ThemeBorders => {
            apply_theme_studio_runtime_override_edit(state, |overrides| {
                overrides.border_style_override = super::cycle_runtime_border_style_override(
                    overrides.border_style_override,
                    direction,
                );
            })
        }
        ThemeStudioItem::VoiceScene => {
            apply_theme_studio_runtime_override_edit(state, |overrides| {
                overrides.voice_scene_style_override =
                    super::cycle_runtime_voice_scene_style_override(
                        overrides.voice_scene_style_override,
                        direction,
                    );
            })
        }
        ThemeStudioItem::ToastPosition => {
            apply_theme_studio_runtime_override_edit(state, |overrides| {
                overrides.toast_position_override = super::cycle_runtime_toast_position_override(
                    overrides.toast_position_override,
                    direction,
                );
            })
        }
        ThemeStudioItem::StartupSplash => {
            apply_theme_studio_runtime_override_edit(state, |overrides| {
                overrides.startup_style_override = super::cycle_runtime_startup_style_override(
                    overrides.startup_style_override,
                    direction,
                );
            })
        }
        ThemeStudioItem::ToastSeverity => {
            apply_theme_studio_runtime_override_edit(state, |overrides| {
                overrides.toast_severity_mode_override =
                    super::cycle_runtime_toast_severity_mode_override(
                        overrides.toast_severity_mode_override,
                        direction,
                    );
            })
        }
        ThemeStudioItem::BannerStyle => {
            apply_theme_studio_runtime_override_edit(state, |overrides| {
                overrides.banner_style_override = super::cycle_runtime_banner_style_override(
                    overrides.banner_style_override,
                    direction,
                );
            })
        }
        ThemeStudioItem::UndoEdit => {
            if direction == 0 {
                theme_studio_undo_runtime_override_edit(state)
            } else {
                false
            }
        }
        ThemeStudioItem::RedoEdit => {
            if direction == 0 {
                theme_studio_redo_runtime_override_edit(state)
            } else {
                false
            }
        }
        ThemeStudioItem::RollbackEdits => {
            if direction == 0 {
                theme_studio_rollback_runtime_override_edits(state)
            } else {
                false
            }
        }
        _ => false,
    }
}

pub(super) fn apply_theme_studio_selection(
    state: &mut EventLoopState,
    timers: &mut EventLoopTimers,
    deps: &mut EventLoopDeps,
    running: &mut bool,
) {
    match theme_studio_item_at(state.theme_studio_selected) {
        ThemeStudioItem::ThemePicker => {
            open_theme_picker_overlay(state, timers, deps);
        }
        ThemeStudioItem::HudStyle
        | ThemeStudioItem::HudBorders
        | ThemeStudioItem::HudPanel
        | ThemeStudioItem::HudAnimate
        | ThemeStudioItem::ColorsGlyphs
        | ThemeStudioItem::LayoutMotion
        | ThemeStudioItem::ProgressSpinner
        | ThemeStudioItem::ProgressBars
        | ThemeStudioItem::ThemeBorders
        | ThemeStudioItem::VoiceScene
        | ThemeStudioItem::ToastPosition
        | ThemeStudioItem::StartupSplash
        | ThemeStudioItem::ToastSeverity
        | ThemeStudioItem::BannerStyle => {
            if apply_theme_studio_adjustment(state, timers, deps, 1)
                && state.overlay_mode == OverlayMode::ThemeStudio
            {
                render_theme_studio_overlay_for_state(state, deps);
            }
        }
        ThemeStudioItem::UndoEdit | ThemeStudioItem::RedoEdit | ThemeStudioItem::RollbackEdits => {
            if apply_theme_studio_adjustment(state, timers, deps, 0)
                && state.overlay_mode == OverlayMode::ThemeStudio
            {
                render_theme_studio_overlay_for_state(state, deps);
            }
        }
        ThemeStudioItem::Close => {
            close_overlay(state, deps, false);
        }
    }
    if !*running {
        close_overlay(state, deps, false);
    }
}

fn push_theme_studio_history_entry(
    history: &mut Vec<crate::theme::RuntimeStylePackOverrides>,
    overrides: crate::theme::RuntimeStylePackOverrides,
) {
    if history.len() >= THEME_STUDIO_HISTORY_LIMIT {
        history.remove(0);
    }
    history.push(overrides);
}

fn apply_theme_studio_runtime_override_edit(
    state: &mut EventLoopState,
    edit: impl FnOnce(&mut crate::theme::RuntimeStylePackOverrides),
) -> bool {
    let mut next = crate::theme::runtime_style_pack_overrides();
    let previous = next;
    edit(&mut next);
    if next == previous {
        return false;
    }
    push_theme_studio_history_entry(&mut state.theme_studio_undo_history, previous);
    state.theme_studio_redo_history.clear();
    crate::theme::set_runtime_style_pack_overrides(next);
    true
}

fn theme_studio_undo_runtime_override_edit(state: &mut EventLoopState) -> bool {
    let Some(previous) = state.theme_studio_undo_history.pop() else {
        return false;
    };
    let current = crate::theme::runtime_style_pack_overrides();
    push_theme_studio_history_entry(&mut state.theme_studio_redo_history, current);
    crate::theme::set_runtime_style_pack_overrides(previous);
    true
}

fn theme_studio_redo_runtime_override_edit(state: &mut EventLoopState) -> bool {
    let Some(next) = state.theme_studio_redo_history.pop() else {
        return false;
    };
    let current = crate::theme::runtime_style_pack_overrides();
    push_theme_studio_history_entry(&mut state.theme_studio_undo_history, current);
    crate::theme::set_runtime_style_pack_overrides(next);
    true
}

fn theme_studio_rollback_runtime_override_edits(state: &mut EventLoopState) -> bool {
    let current = crate::theme::runtime_style_pack_overrides();
    let defaults = crate::theme::RuntimeStylePackOverrides::default();
    if current == defaults {
        return false;
    }
    push_theme_studio_history_entry(&mut state.theme_studio_undo_history, current);
    state.theme_studio_redo_history.clear();
    crate::theme::set_runtime_style_pack_overrides(defaults);
    true
}
