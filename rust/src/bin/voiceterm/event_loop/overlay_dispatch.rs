//! Overlay transition helpers extracted from the core event loop.

use super::*;

pub(super) fn render_help_overlay_for_state(state: &EventLoopState, deps: &EventLoopDeps) {
    let cols = resolved_cols(state.terminal_cols);
    show_help_overlay(&deps.writer_tx, state.theme, cols);
}

pub(super) fn render_dev_panel_overlay_for_state(state: &EventLoopState, deps: &EventLoopDeps) {
    let cols = resolved_cols(state.terminal_cols);
    let snapshot = state
        .dev_mode_stats
        .as_ref()
        .map(voiceterm::devtools::DevModeStats::snapshot);
    show_dev_panel_overlay(
        &deps.writer_tx,
        state.theme,
        snapshot,
        state.config.dev_log,
        state.config.dev_path.as_deref(),
        &state.dev_panel_commands,
        cols,
    );
}

pub(super) fn render_theme_picker_overlay_for_state(state: &EventLoopState, deps: &EventLoopDeps) {
    let cols = resolved_cols(state.terminal_cols);
    let locked_theme = style_pack_theme_lock();
    let display_theme = locked_theme.unwrap_or(state.theme);
    let selected_idx = locked_theme
        .map(theme_index_from_theme)
        .unwrap_or(state.theme_picker_selected);
    show_theme_picker_overlay(
        &deps.writer_tx,
        display_theme,
        selected_idx,
        cols,
        locked_theme,
    );
}

pub(super) fn render_theme_studio_overlay_for_state(state: &EventLoopState, deps: &EventLoopDeps) {
    use crate::theme_studio::{format_tab_bar, StudioPage};

    let cols = resolved_cols(state.terminal_cols);

    match state.theme_studio_page {
        StudioPage::Home => {
            // Original home page rendering — unchanged.
            let selected = state
                .theme_studio_selected
                .min(THEME_STUDIO_ITEMS.len().saturating_sub(1));
            let style_pack_overrides = runtime_style_pack_overrides();
            let view = ThemeStudioView {
                theme: state.theme,
                selected,
                hud_style: state.status_state.hud_style,
                hud_border_style: state.config.hud_border_style,
                hud_right_panel: state.config.hud_right_panel,
                hud_right_panel_recording_only: state.config.hud_right_panel_recording_only,
                border_style_override: style_pack_overrides.border_style_override,
                glyph_set_override: style_pack_overrides.glyph_set_override,
                indicator_set_override: style_pack_overrides.indicator_set_override,
                progress_style_override: style_pack_overrides.progress_style_override,
                progress_bar_family_override: style_pack_overrides.progress_bar_family_override,
                voice_scene_style_override: style_pack_overrides.voice_scene_style_override,
                toast_position_override: style_pack_overrides.toast_position_override,
                startup_style_override: style_pack_overrides.startup_style_override,
                toast_severity_mode_override: style_pack_overrides.toast_severity_mode_override,
                banner_style_override: style_pack_overrides.banner_style_override,
                undo_available: !state.theme_studio_undo_history.is_empty(),
                redo_available: !state.theme_studio_redo_history.is_empty(),
                runtime_overrides_dirty: style_pack_overrides
                    != RuntimeStylePackOverrides::default(),
            };
            show_theme_studio_overlay(&deps.writer_tx, &view, cols);
        }
        page => {
            // Non-home pages: render tab bar + page content.
            let colors = state.theme.colors();
            let inner_width = theme_studio_inner_width_for_terminal(cols as usize);
            let tab_bar = format_tab_bar(page, &colors, inner_width);

            let page_lines: Vec<String> = match page {
                StudioPage::Colors => {
                    if let Some(ref editor) = state.theme_studio_colors_editor {
                        editor.render(colors.info, colors.dim, colors.reset)
                    } else {
                        vec![" (open Colors page to initialize editor)".to_string()]
                    }
                }
                StudioPage::Borders => {
                    state
                        .theme_studio_borders_page
                        .render(colors.info, colors.dim, colors.reset)
                }
                StudioPage::Components => state.theme_studio_components_editor.render(
                    colors.info,
                    colors.dim,
                    colors.reset,
                ),
                StudioPage::Preview => state.theme_studio_preview_page.render(&colors),
                StudioPage::Export => {
                    let ep = &state.theme_studio_export_page;
                    let mut lines: Vec<String> = crate::theme_studio::ExportAction::ALL
                        .iter()
                        .enumerate()
                        .map(|(i, action): (usize, &crate::theme_studio::ExportAction)| {
                            let marker = if i == ep.selected { "▸" } else { " " };
                            format!(
                                " {} {}  {}{}{}",
                                marker,
                                action.label(),
                                colors.dim,
                                action.description(),
                                colors.reset
                            )
                        })
                        .collect();
                    if let Some(ref status) = ep.last_status {
                        lines.push(String::new());
                        lines.push(format!(" {}{}{}", colors.info, status, colors.reset));
                    }
                    lines
                }
                StudioPage::Home => {
                    log_debug(
                        "theme studio home page reached non-home renderer branch; using fallback",
                    );
                    vec![" (theme studio fallback; press Esc and reopen)".to_string()]
                }
            };

            let mut content = String::new();
            content.push_str(&tab_bar);
            content.push('\n');
            for line in &page_lines {
                content.push_str(line);
                content.push('\n');
            }

            // Footer hint.
            content.push_str(&format!(
                "\n {}Tab{}/{}Shift+Tab{} switch pages  {}Esc{} close",
                colors.info, colors.reset, colors.info, colors.reset, colors.dim, colors.reset,
            ));

            let height = 2 + page_lines.len() + 2; // tab bar + lines + footer
            let _ = crate::writer::try_send_message(
                &deps.writer_tx,
                WriterMessage::ShowOverlay { content, height },
            );
        }
    }
}

pub(super) fn render_transcript_history_overlay_for_state(
    state: &EventLoopState,
    deps: &EventLoopDeps,
) {
    let cols = resolved_cols(state.terminal_cols);
    show_transcript_history_overlay(
        &deps.writer_tx,
        &state.transcript_history,
        &state.transcript_history_state,
        state.theme,
        cols,
    );
}

pub(super) fn render_toast_history_overlay_for_state(state: &EventLoopState, deps: &EventLoopDeps) {
    let cols = resolved_cols(state.terminal_cols);
    show_toast_history_overlay(&deps.writer_tx, &state.toast_center, state.theme, cols);
}

pub(super) fn render_settings_overlay_for_state(state: &EventLoopState, deps: &EventLoopDeps) {
    let cols = resolved_cols(state.terminal_cols);
    show_settings_overlay(
        &deps.writer_tx,
        state.theme,
        cols,
        &state.settings_menu,
        &state.config,
        &state.status_state,
        &deps.backend_label,
    );
}

pub(super) fn close_overlay(
    state: &mut EventLoopState,
    deps: &mut EventLoopDeps,
    refresh_buttons: bool,
) {
    state.overlay_mode = OverlayMode::None;
    let _ = deps.writer_tx.send(WriterMessage::ClearOverlay);
    sync_overlay_winsize(state, deps);
    if refresh_buttons {
        refresh_button_registry_if_mouse(state, deps);
    }
}

pub(super) fn open_help_overlay(state: &mut EventLoopState, deps: &mut EventLoopDeps) {
    state.overlay_mode = OverlayMode::Help;
    sync_overlay_winsize(state, deps);
    render_help_overlay_for_state(state, deps);
}

pub(super) fn open_dev_panel_overlay(state: &mut EventLoopState, deps: &mut EventLoopDeps) {
    state.overlay_mode = OverlayMode::DevPanel;
    sync_overlay_winsize(state, deps);
    render_dev_panel_overlay_for_state(state, deps);
}

pub(super) fn open_settings_overlay(state: &mut EventLoopState, deps: &mut EventLoopDeps) {
    state.overlay_mode = OverlayMode::Settings;
    sync_overlay_winsize(state, deps);
    render_settings_overlay_for_state(state, deps);
}

pub(super) fn open_theme_picker_overlay(
    state: &mut EventLoopState,
    timers: &mut EventLoopTimers,
    deps: &mut EventLoopDeps,
) {
    state.overlay_mode = OverlayMode::ThemePicker;
    sync_overlay_winsize(state, deps);
    reset_theme_picker_selection(state, timers);
    render_theme_picker_overlay_for_state(state, deps);
}

pub(super) fn open_theme_studio_overlay(state: &mut EventLoopState, deps: &mut EventLoopDeps) {
    state.overlay_mode = OverlayMode::ThemeStudio;
    reset_theme_studio_selection(state);
    sync_overlay_winsize(state, deps);
    render_theme_studio_overlay_for_state(state, deps);
}

pub(super) fn open_transcript_history_overlay(
    state: &mut EventLoopState,
    deps: &mut EventLoopDeps,
) {
    state.overlay_mode = OverlayMode::TranscriptHistory;
    state.transcript_history.flush_pending_stream_lines();
    state
        .transcript_history_state
        .refresh_filter(&state.transcript_history);
    sync_overlay_winsize(state, deps);
    render_transcript_history_overlay_for_state(state, deps);
}

pub(super) fn open_toast_history_overlay(state: &mut EventLoopState, deps: &mut EventLoopDeps) {
    state.overlay_mode = OverlayMode::ToastHistory;
    sync_overlay_winsize(state, deps);
    render_toast_history_overlay_for_state(state, deps);
}
