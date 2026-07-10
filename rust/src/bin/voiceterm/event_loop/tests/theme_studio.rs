use super::*;

#[test]
fn theme_picker_hotkey_opens_theme_studio_overlay() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.ui.overlay_mode = OverlayMode::None;
    let mut running = true;

    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::ThemePicker,
        &mut running,
    );

    assert!(running);
    assert_eq!(state.ui.overlay_mode, OverlayMode::ThemeStudio);
}

#[test]
fn theme_studio_enter_on_theme_picker_row_opens_theme_picker_overlay() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.ui.overlay_mode = OverlayMode::ThemeStudio;
    state.theme_studio.selected = 0;
    let mut running = true;

    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::EnterKey,
        &mut running,
    );

    assert!(running);
    assert_eq!(state.ui.overlay_mode, OverlayMode::ThemePicker);
}

#[test]
fn theme_studio_enter_on_hud_style_row_cycles_style_and_stays_open() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.ui.overlay_mode = OverlayMode::ThemeStudio;
    state.theme_studio.selected = 1; // HUD style
    state.status_state.hud_style = HudStyle::Full;
    let mut running = true;

    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::EnterKey,
        &mut running,
    );

    assert!(running);
    assert_eq!(state.ui.overlay_mode, OverlayMode::ThemeStudio);
    assert_eq!(state.status_state.hud_style, HudStyle::Minimal);
}

#[test]
fn theme_studio_arrow_left_on_hud_style_row_cycles_backward() {
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.ui.overlay_mode = OverlayMode::ThemeStudio;
    state.theme_studio.selected = 1; // HUD style
    state.status_state.hud_style = HudStyle::Minimal;
    let mut running = true;

    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::Bytes(b"\x1b[D".to_vec()),
        &mut running,
    );

    assert!(running);
    assert_eq!(state.ui.overlay_mode, OverlayMode::ThemeStudio);
    assert_eq!(state.status_state.hud_style, HudStyle::Full);
}

#[test]
fn theme_studio_enter_on_glyph_profile_row_cycles_runtime_override() {
    let _override_guard =
        install_runtime_style_pack_overrides(RuntimeStylePackOverrides::default());
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.ui.overlay_mode = OverlayMode::ThemeStudio;
    state.theme_studio.selected = 5; // Glyph profile
    let mut running = true;

    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::EnterKey,
        &mut running,
    );

    assert!(running);
    assert_eq!(state.ui.overlay_mode, OverlayMode::ThemeStudio);
    let overrides = crate::theme::runtime_style_pack_overrides();
    assert_eq!(
        overrides.glyph_set_override,
        Some(RuntimeGlyphSetOverride::Unicode)
    );
}

#[test]
fn theme_studio_arrow_right_on_indicator_set_row_cycles_runtime_override() {
    let _override_guard =
        install_runtime_style_pack_overrides(RuntimeStylePackOverrides::default());
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.ui.overlay_mode = OverlayMode::ThemeStudio;
    state.theme_studio.selected = 6; // Indicator set
    let mut running = true;

    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::Bytes(b"\x1b[C".to_vec()),
        &mut running,
    );

    assert!(running);
    assert_eq!(state.ui.overlay_mode, OverlayMode::ThemeStudio);
    let overrides = crate::theme::runtime_style_pack_overrides();
    assert_eq!(
        overrides.indicator_set_override,
        Some(RuntimeIndicatorSetOverride::Ascii)
    );
}

#[test]
fn theme_studio_enter_on_progress_spinner_row_cycles_runtime_override() {
    let _override_guard =
        install_runtime_style_pack_overrides(RuntimeStylePackOverrides::default());
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.ui.overlay_mode = OverlayMode::ThemeStudio;
    state.theme_studio.selected = 7; // Progress spinner
    let mut running = true;

    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::EnterKey,
        &mut running,
    );

    assert!(running);
    assert_eq!(state.ui.overlay_mode, OverlayMode::ThemeStudio);
    let overrides = crate::theme::runtime_style_pack_overrides();
    assert_eq!(
        overrides.progress_style_override,
        Some(RuntimeProgressStyleOverride::Braille)
    );
}

#[test]
fn theme_studio_enter_on_progress_bars_row_cycles_runtime_override() {
    let _override_guard =
        install_runtime_style_pack_overrides(RuntimeStylePackOverrides::default());
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.ui.overlay_mode = OverlayMode::ThemeStudio;
    state.theme_studio.selected = 8; // Progress bars
    let mut running = true;

    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::EnterKey,
        &mut running,
    );

    assert!(running);
    assert_eq!(state.ui.overlay_mode, OverlayMode::ThemeStudio);
    let overrides = crate::theme::runtime_style_pack_overrides();
    assert_eq!(
        overrides.progress_bar_family_override,
        Some(RuntimeProgressBarFamilyOverride::Bar)
    );
}

#[test]
fn theme_studio_enter_on_theme_borders_row_cycles_runtime_override() {
    let _override_guard =
        install_runtime_style_pack_overrides(RuntimeStylePackOverrides::default());
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.ui.overlay_mode = OverlayMode::ThemeStudio;
    state.theme_studio.selected = 9; // Theme borders
    let mut running = true;

    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::EnterKey,
        &mut running,
    );

    assert!(running);
    assert_eq!(state.ui.overlay_mode, OverlayMode::ThemeStudio);
    let overrides = crate::theme::runtime_style_pack_overrides();
    assert_eq!(
        overrides.border_style_override,
        Some(RuntimeBorderStyleOverride::Single)
    );
}

#[test]
fn theme_studio_enter_on_voice_scene_row_cycles_runtime_override() {
    let _override_guard =
        install_runtime_style_pack_overrides(RuntimeStylePackOverrides::default());
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.ui.overlay_mode = OverlayMode::ThemeStudio;
    state.theme_studio.selected = 10; // Voice scene
    let mut running = true;

    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::EnterKey,
        &mut running,
    );

    assert!(running);
    assert_eq!(state.ui.overlay_mode, OverlayMode::ThemeStudio);
    let overrides = crate::theme::runtime_style_pack_overrides();
    assert_eq!(
        overrides.voice_scene_style_override,
        Some(RuntimeVoiceSceneStyleOverride::Pulse)
    );
}

#[test]
fn theme_studio_enter_on_toast_position_row_cycles_runtime_override() {
    let _override_guard =
        install_runtime_style_pack_overrides(RuntimeStylePackOverrides::default());
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.ui.overlay_mode = OverlayMode::ThemeStudio;
    state.theme_studio.selected = 11; // Toast position
    let mut running = true;

    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::EnterKey,
        &mut running,
    );

    assert!(running);
    assert_eq!(state.ui.overlay_mode, OverlayMode::ThemeStudio);
    let overrides = crate::theme::runtime_style_pack_overrides();
    assert_eq!(
        overrides.toast_position_override,
        Some(RuntimeToastPositionOverride::TopRight)
    );
}

#[test]
fn theme_studio_enter_on_startup_splash_row_cycles_runtime_override() {
    let _override_guard =
        install_runtime_style_pack_overrides(RuntimeStylePackOverrides::default());
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.ui.overlay_mode = OverlayMode::ThemeStudio;
    state.theme_studio.selected = 12; // Startup splash
    let mut running = true;

    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::EnterKey,
        &mut running,
    );

    assert!(running);
    assert_eq!(state.ui.overlay_mode, OverlayMode::ThemeStudio);
    let overrides = crate::theme::runtime_style_pack_overrides();
    assert_eq!(
        overrides.startup_style_override,
        Some(RuntimeStartupStyleOverride::Full)
    );
}

#[test]
fn theme_studio_enter_on_toast_severity_row_cycles_runtime_override() {
    let _override_guard =
        install_runtime_style_pack_overrides(RuntimeStylePackOverrides::default());
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.ui.overlay_mode = OverlayMode::ThemeStudio;
    state.theme_studio.selected = 13; // Toast severity
    let mut running = true;

    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::EnterKey,
        &mut running,
    );

    assert!(running);
    assert_eq!(state.ui.overlay_mode, OverlayMode::ThemeStudio);
    let overrides = crate::theme::runtime_style_pack_overrides();
    assert_eq!(
        overrides.toast_severity_mode_override,
        Some(RuntimeToastSeverityModeOverride::Icon)
    );
}

#[test]
fn theme_studio_enter_on_banner_style_row_cycles_runtime_override() {
    let _override_guard =
        install_runtime_style_pack_overrides(RuntimeStylePackOverrides::default());
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.ui.overlay_mode = OverlayMode::ThemeStudio;
    state.theme_studio.selected = 14; // Banner style
    let mut running = true;

    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::EnterKey,
        &mut running,
    );

    assert!(running);
    assert_eq!(state.ui.overlay_mode, OverlayMode::ThemeStudio);
    let overrides = crate::theme::runtime_style_pack_overrides();
    assert_eq!(
        overrides.banner_style_override,
        Some(RuntimeBannerStyleOverride::Full)
    );
}

#[test]
fn theme_studio_enter_on_undo_row_reverts_latest_runtime_override_edit() {
    let _override_guard =
        install_runtime_style_pack_overrides(RuntimeStylePackOverrides::default());
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.ui.overlay_mode = OverlayMode::ThemeStudio;
    state.theme_studio.selected = 5; // Glyph profile
    let mut running = true;

    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::EnterKey,
        &mut running,
    );
    assert_eq!(
        crate::theme::runtime_style_pack_overrides().glyph_set_override,
        Some(RuntimeGlyphSetOverride::Unicode)
    );
    assert_eq!(state.theme_studio.undo_history.len(), 1);
    assert!(state.theme_studio.redo_history.is_empty());

    state.theme_studio.selected = 15; // Undo edit
    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::EnterKey,
        &mut running,
    );

    assert!(running);
    assert_eq!(state.ui.overlay_mode, OverlayMode::ThemeStudio);
    assert_eq!(
        crate::theme::runtime_style_pack_overrides().glyph_set_override,
        None
    );
    assert!(state.theme_studio.undo_history.is_empty());
    assert_eq!(state.theme_studio.redo_history.len(), 1);
}

#[test]
fn theme_studio_enter_on_redo_row_reapplies_runtime_override_edit() {
    let _override_guard =
        install_runtime_style_pack_overrides(RuntimeStylePackOverrides::default());
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.ui.overlay_mode = OverlayMode::ThemeStudio;
    let mut running = true;

    state.theme_studio.selected = 5; // Glyph profile
    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::EnterKey,
        &mut running,
    );
    state.theme_studio.selected = 15; // Undo edit
    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::EnterKey,
        &mut running,
    );

    state.theme_studio.selected = 16; // Redo edit
    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::EnterKey,
        &mut running,
    );

    assert!(running);
    assert_eq!(state.ui.overlay_mode, OverlayMode::ThemeStudio);
    assert_eq!(
        crate::theme::runtime_style_pack_overrides().glyph_set_override,
        Some(RuntimeGlyphSetOverride::Unicode)
    );
    assert_eq!(state.theme_studio.undo_history.len(), 1);
    assert!(state.theme_studio.redo_history.is_empty());
}

#[test]
fn theme_studio_enter_on_rollback_row_clears_runtime_overrides() {
    let _override_guard =
        install_runtime_style_pack_overrides(RuntimeStylePackOverrides::default());
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.ui.overlay_mode = OverlayMode::ThemeStudio;
    let mut running = true;

    state.theme_studio.selected = 5; // Glyph profile
    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::EnterKey,
        &mut running,
    );
    state.theme_studio.selected = 6; // Indicator set
    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::EnterKey,
        &mut running,
    );
    assert_eq!(
        crate::theme::runtime_style_pack_overrides().glyph_set_override,
        Some(RuntimeGlyphSetOverride::Unicode)
    );
    assert_eq!(
        crate::theme::runtime_style_pack_overrides().indicator_set_override,
        Some(RuntimeIndicatorSetOverride::Ascii)
    );

    state.theme_studio.selected = 17; // Rollback edits
    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::EnterKey,
        &mut running,
    );

    assert!(running);
    assert_eq!(state.ui.overlay_mode, OverlayMode::ThemeStudio);
    assert_eq!(
        crate::theme::runtime_style_pack_overrides(),
        RuntimeStylePackOverrides::default()
    );
    assert!(state.theme_studio.undo_history.len() >= 2);
    assert!(state.theme_studio.redo_history.is_empty());
}

#[test]
fn theme_studio_colors_page_arrow_right_on_indicator_selector_cycles_runtime_override() {
    let _override_guard =
        install_runtime_style_pack_overrides(RuntimeStylePackOverrides::default());
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.ui.overlay_mode = OverlayMode::ThemeStudio;
    state.theme_studio.page = crate::theme_studio::StudioPage::Colors;
    state.theme_studio.colors_editor =
        Some(crate::theme_studio::ColorsEditorState::new(state.theme));
    let mut running = true;

    let color_field_count = crate::theme_studio::ColorField::ALL.len();
    {
        let editor = state
            .theme_studio
            .colors_editor
            .as_mut()
            .expect("colors editor is initialized");
        editor.selected = color_field_count;
        editor.indicator_set = None;
    }

    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::Bytes(b"\x1b[C".to_vec()),
        &mut running,
    );

    assert!(running);
    assert_eq!(state.ui.overlay_mode, OverlayMode::ThemeStudio);
    let overrides = crate::theme::runtime_style_pack_overrides();
    assert_eq!(
        overrides.indicator_set_override,
        Some(RuntimeIndicatorSetOverride::Ascii)
    );
    let editor = state
        .theme_studio
        .colors_editor
        .as_ref()
        .expect("colors editor persists");
    assert_eq!(
        editor.indicator_set,
        Some(RuntimeIndicatorSetOverride::Ascii)
    );
    assert!(editor.picker.is_none());
}

#[test]
fn theme_studio_colors_page_arrow_right_on_glyph_selector_cycles_runtime_override() {
    let _override_guard =
        install_runtime_style_pack_overrides(RuntimeStylePackOverrides::default());
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.ui.overlay_mode = OverlayMode::ThemeStudio;
    state.theme_studio.page = crate::theme_studio::StudioPage::Colors;
    state.theme_studio.colors_editor =
        Some(crate::theme_studio::ColorsEditorState::new(state.theme));
    let mut running = true;

    let color_field_count = crate::theme_studio::ColorField::ALL.len();
    {
        let editor = state
            .theme_studio
            .colors_editor
            .as_mut()
            .expect("colors editor is initialized");
        editor.selected = color_field_count + 1;
        editor.glyph_set = None;
    }

    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::Bytes(b"\x1b[C".to_vec()),
        &mut running,
    );

    assert!(running);
    assert_eq!(state.ui.overlay_mode, OverlayMode::ThemeStudio);
    let overrides = crate::theme::runtime_style_pack_overrides();
    assert_eq!(
        overrides.glyph_set_override,
        Some(RuntimeGlyphSetOverride::Unicode)
    );
    let editor = state
        .theme_studio
        .colors_editor
        .as_ref()
        .expect("colors editor persists");
    assert_eq!(editor.glyph_set, Some(RuntimeGlyphSetOverride::Unicode));
    assert!(editor.picker.is_none());
}

#[test]
fn theme_studio_colors_page_enter_on_indicator_selector_is_noop_for_picker() {
    let _override_guard =
        install_runtime_style_pack_overrides(RuntimeStylePackOverrides::default());
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.ui.overlay_mode = OverlayMode::ThemeStudio;
    state.theme_studio.page = crate::theme_studio::StudioPage::Colors;
    state.theme_studio.colors_editor =
        Some(crate::theme_studio::ColorsEditorState::new(state.theme));
    let mut running = true;

    let color_field_count = crate::theme_studio::ColorField::ALL.len();
    {
        let editor = state
            .theme_studio
            .colors_editor
            .as_mut()
            .expect("colors editor is initialized");
        editor.selected = color_field_count;
        editor.picker = None;
    }

    handle_input_event(
        &mut state,
        &mut timers,
        &mut deps,
        InputEvent::EnterKey,
        &mut running,
    );

    assert!(running);
    assert_eq!(state.ui.overlay_mode, OverlayMode::ThemeStudio);
    let editor = state
        .theme_studio
        .colors_editor
        .as_ref()
        .expect("colors editor persists");
    assert!(editor.picker.is_none());
    assert_eq!(
        crate::theme::runtime_style_pack_overrides(),
        RuntimeStylePackOverrides::default()
    );
}

#[test]
fn reset_theme_picker_selection_resets_index_and_digits() {
    let (mut state, mut timers, _deps, _writer_rx, _input_tx) = build_harness("cat", &[], 8);
    state.theme = Theme::Codex;
    state.theme_studio.picker_selected = theme_index_from_theme(Theme::Claude);
    state.theme_studio.picker_digits = "12".to_string();
    timers.theme_picker_digit_deadline = Some(Instant::now() + Duration::from_millis(300));

    reset_theme_picker_selection(&mut state, &mut timers);

    let expected_theme = style_pack_theme_lock().unwrap_or(state.theme);
    assert_eq!(
        state.theme_studio.picker_selected,
        theme_index_from_theme(expected_theme)
    );
    assert!(state.theme_studio.picker_digits.is_empty());
    assert!(timers.theme_picker_digit_deadline.is_none());
}

#[test]
fn apply_settings_item_action_theme_zero_direction_matches_positive_step() {
    let (mut zero_state, mut zero_timers, mut zero_deps, _zero_writer_rx, _zero_input_tx) =
        build_harness("cat", &[], 8);
    let (mut plus_state, mut plus_timers, mut plus_deps, _plus_writer_rx, _plus_input_tx) =
        build_harness("cat", &[], 8);
    zero_state.status_state.hud_style = HudStyle::Full;
    plus_state.status_state.hud_style = HudStyle::Full;

    let zero_overlay = zero_state.ui.overlay_mode;
    {
        let mut zero_ctx = settings_action_context(
            &mut zero_state,
            &mut zero_timers,
            &mut zero_deps,
            zero_overlay,
        );
        assert!(apply_settings_item_action(
            SettingsItem::HudStyle,
            0,
            &mut zero_ctx
        ));
    }

    let plus_overlay = plus_state.ui.overlay_mode;
    {
        let mut plus_ctx = settings_action_context(
            &mut plus_state,
            &mut plus_timers,
            &mut plus_deps,
            plus_overlay,
        );
        assert!(apply_settings_item_action(
            SettingsItem::HudStyle,
            1,
            &mut plus_ctx
        ));
    }

    assert_eq!(
        zero_state.status_state.hud_style,
        plus_state.status_state.hud_style
    );
}

#[test]
fn apply_settings_item_action_theme_negative_direction_differs_from_positive_step() {
    let (mut minus_state, mut minus_timers, mut minus_deps, _minus_writer_rx, _minus_input_tx) =
        build_harness("cat", &[], 8);
    let (mut plus_state, mut plus_timers, mut plus_deps, _plus_writer_rx, _plus_input_tx) =
        build_harness("cat", &[], 8);
    minus_state.status_state.hud_style = HudStyle::Full;
    plus_state.status_state.hud_style = HudStyle::Full;

    let minus_overlay = minus_state.ui.overlay_mode;
    {
        let mut minus_ctx = settings_action_context(
            &mut minus_state,
            &mut minus_timers,
            &mut minus_deps,
            minus_overlay,
        );
        assert!(apply_settings_item_action(
            SettingsItem::HudStyle,
            -1,
            &mut minus_ctx
        ));
    }

    let plus_overlay = plus_state.ui.overlay_mode;
    {
        let mut plus_ctx = settings_action_context(
            &mut plus_state,
            &mut plus_timers,
            &mut plus_deps,
            plus_overlay,
        );
        assert!(apply_settings_item_action(
            SettingsItem::HudStyle,
            1,
            &mut plus_ctx
        ));
    }

    assert_ne!(
        minus_state.status_state.hud_style,
        plus_state.status_state.hud_style
    );
}
