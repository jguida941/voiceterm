use super::*;
use crate::test_env::env_lock;
use crate::theme::runtime_overrides::{
    RuntimeBannerStyleOverride, RuntimeBorderStyleOverride, RuntimeGlyphSetOverride,
    RuntimeIndicatorSetOverride, RuntimeProgressBarFamilyOverride, RuntimeProgressStyleOverride,
    RuntimeStartupStyleOverride, RuntimeStylePackOverrides, RuntimeToastPositionOverride,
    RuntimeToastSeverityModeOverride, RuntimeVoiceSceneStyleOverride,
};
use crate::theme::style_schema::{
    BannerStyleOverride, StartupStyleOverride, ToastPositionOverride, ToastSeverityMode,
};
use crate::theme::{
    GlyphSet, ProgressBarFamily, SpinnerStyle, VoiceSceneStyle, BORDER_HEAVY, BORDER_NONE,
    BORDER_ROUNDED,
};

struct RuntimeOverridesGuard {
    previous: RuntimeStylePackOverrides,
}

impl Drop for RuntimeOverridesGuard {
    fn drop(&mut self) {
        set_runtime_style_pack_overrides(self.previous);
    }
}

fn install_runtime_overrides(overrides: RuntimeStylePackOverrides) -> RuntimeOverridesGuard {
    let previous = runtime_style_pack_overrides();
    set_runtime_style_pack_overrides(overrides);
    RuntimeOverridesGuard { previous }
}

#[test]
fn style_pack_built_in_uses_current_schema_version() {
    let pack = StylePack::built_in(Theme::Codex);
    assert_eq!(pack.schema_version, STYLE_PACK_RUNTIME_VERSION);
    assert_eq!(pack.base_theme, Theme::Codex);
    assert_eq!(pack.border_style_override, None);
    assert_eq!(pack.indicator_set_override, None);
    assert_eq!(pack.glyph_set_override, None);
}

#[test]
fn resolve_theme_colors_matches_legacy_palette_map() {
    let themes = [
        Theme::Coral,
        Theme::Claude,
        Theme::Codex,
        Theme::ChatGpt,
        Theme::Catppuccin,
        Theme::Dracula,
        Theme::Nord,
        Theme::TokyoNight,
        Theme::Gruvbox,
        Theme::Ansi,
        Theme::None,
    ];

    for theme in themes {
        assert_eq!(
            resolve_theme_colors_with_payload(theme, None),
            base_theme_colors(theme)
        );
    }
}

#[test]
fn resolve_theme_colors_with_payload_uses_schema_base_theme() {
    let payload = r#"{"version":3,"profile":"ops","base_theme":"dracula"}"#;
    assert_eq!(
        resolve_theme_colors_with_payload(Theme::Codex, Some(payload)),
        THEME_DRACULA
    );
}

#[test]
fn resolve_theme_colors_with_payload_migrates_legacy_schema() {
    let payload = r#"{"version":1,"theme":"nord"}"#;
    assert_eq!(
        resolve_theme_colors_with_payload(Theme::Coral, Some(payload)),
        THEME_NORD
    );
}

#[test]
fn resolve_theme_colors_with_payload_falls_back_to_requested_theme_when_invalid() {
    let payload = r#"{"version":"bad","base_theme":"dracula"}"#;
    assert_eq!(
        resolve_theme_colors_with_payload(Theme::Coral, Some(payload)),
        THEME_CORAL
    );
}

#[test]
fn resolve_style_pack_colors_falls_back_to_base_theme_for_unsupported_schema_version() {
    let unsupported = StylePack::with_schema_version(Theme::Codex, u16::MAX);
    assert_eq!(resolve_style_pack_colors(unsupported), THEME_CODEX);
}

#[test]
fn resolve_theme_colors_with_payload_applies_border_style_override() {
    let payload = r#"{
            "version":3,
            "profile":"ops",
            "base_theme":"codex",
            "overrides":{"border_style":"none"}
        }"#;
    let colors = resolve_theme_colors_with_payload(Theme::Codex, Some(payload));
    assert_eq!(colors.borders, BORDER_NONE);
}

#[test]
fn resolved_overlay_border_set_uses_component_override_when_present() {
    let payload = r#"{
            "version":4,
            "profile":"ops",
            "base_theme":"codex",
            "overrides":{"border_style":"none"},
            "components":{"overlay_border":"rounded"}
        }"#;
    assert_eq!(
        resolved_overlay_border_set_with_payload(Theme::Codex, Some(payload)),
        BORDER_ROUNDED
    );
}

#[test]
fn resolved_hud_border_set_uses_component_override_when_present() {
    let payload = r#"{
            "version":4,
            "profile":"ops",
            "base_theme":"codex",
            "overrides":{"border_style":"single"},
            "components":{"hud_border":"heavy"}
        }"#;
    assert_eq!(
        resolved_hud_border_set_with_payload(Theme::Codex, Some(payload)),
        BORDER_HEAVY
    );
}

#[test]
fn resolved_component_border_sets_fall_back_to_global_border_override() {
    let payload = r#"{
            "version":4,
            "profile":"ops",
            "base_theme":"codex",
            "overrides":{"border_style":"none"}
        }"#;
    assert_eq!(
        resolved_overlay_border_set_with_payload(Theme::Codex, Some(payload)),
        BORDER_NONE
    );
    assert_eq!(
        resolved_hud_border_set_with_payload(Theme::Codex, Some(payload)),
        BORDER_NONE
    );
}

#[test]
fn resolve_theme_colors_with_payload_applies_indicator_override() {
    let payload = r#"{
            "version":3,
            "profile":"ops",
            "base_theme":"codex",
            "overrides":{"indicators":"ascii"}
        }"#;
    let colors = resolve_theme_colors_with_payload(Theme::Codex, Some(payload));
    assert_eq!(colors.indicator_rec, "*");
    assert_eq!(colors.indicator_auto, "@");
    assert_eq!(colors.indicator_manual, ">");
    assert_eq!(colors.indicator_idle, "-");
    assert_eq!(colors.indicator_processing, "~");
    assert_eq!(colors.indicator_responding, ">");
}

#[test]
fn resolve_theme_colors_with_payload_applies_glyph_override() {
    let payload = r#"{
            "version":3,
            "profile":"ops",
            "base_theme":"codex",
            "overrides":{"glyphs":"ascii"}
        }"#;
    let colors = resolve_theme_colors_with_payload(Theme::Codex, Some(payload));
    assert_eq!(colors.glyph_set, GlyphSet::Ascii);
}

#[test]
fn resolve_theme_colors_with_payload_applies_progress_style_override() {
    let payload = r#"{
            "version":4,
            "profile":"ops",
            "base_theme":"codex",
            "surfaces":{"progress_style":"dots"}
        }"#;
    let colors = resolve_theme_colors_with_payload(Theme::Codex, Some(payload));
    assert_eq!(colors.spinner_style, SpinnerStyle::Dots);
}

#[test]
fn resolve_theme_colors_with_payload_applies_progress_bar_family_override() {
    let payload = r#"{
            "version":4,
            "profile":"ops",
            "base_theme":"codex",
            "components":{"progress_bar_family":"blocks"}
        }"#;
    let colors = resolve_theme_colors_with_payload(Theme::Codex, Some(payload));
    assert_eq!(colors.progress_bar_family, ProgressBarFamily::Blocks);
}

#[test]
fn resolve_theme_colors_with_payload_applies_voice_scene_style_override() {
    let payload = r#"{
            "version":4,
            "profile":"ops",
            "base_theme":"codex",
            "surfaces":{"voice_scene_style":"minimal"}
        }"#;
    let colors = resolve_theme_colors_with_payload(Theme::Codex, Some(payload));
    assert_eq!(colors.voice_scene_style, VoiceSceneStyle::Minimal);
}

#[test]
fn resolve_theme_colors_applies_runtime_glyph_override() {
    let _guard = install_runtime_overrides(RuntimeStylePackOverrides {
        glyph_set_override: Some(RuntimeGlyphSetOverride::Ascii),
        ..RuntimeStylePackOverrides::default()
    });
    let colors = resolve_theme_colors(Theme::Codex);
    assert_eq!(colors.glyph_set, GlyphSet::Ascii);
}

#[test]
fn resolve_theme_colors_applies_runtime_indicator_override() {
    let _guard = install_runtime_overrides(RuntimeStylePackOverrides {
        indicator_set_override: Some(RuntimeIndicatorSetOverride::Diamond),
        ..RuntimeStylePackOverrides::default()
    });
    let colors = resolve_theme_colors(Theme::Codex);
    assert_eq!(colors.indicator_rec, "◆");
    assert_eq!(colors.indicator_processing, "◈");
}

#[test]
fn resolve_theme_colors_applies_runtime_border_override() {
    let _guard = install_runtime_overrides(RuntimeStylePackOverrides {
        border_style_override: Some(RuntimeBorderStyleOverride::None),
        ..RuntimeStylePackOverrides::default()
    });
    let colors = resolve_theme_colors(Theme::Codex);
    assert_eq!(colors.borders, BORDER_NONE);
}

#[test]
fn resolve_theme_colors_applies_runtime_progress_style_override() {
    let _guard = install_runtime_overrides(RuntimeStylePackOverrides {
        progress_style_override: Some(RuntimeProgressStyleOverride::Line),
        ..RuntimeStylePackOverrides::default()
    });
    let colors = resolve_theme_colors(Theme::Codex);
    assert_eq!(colors.spinner_style, SpinnerStyle::Line);
}

#[test]
fn resolve_theme_colors_applies_runtime_progress_bar_family_override() {
    let _guard = install_runtime_overrides(RuntimeStylePackOverrides {
        progress_bar_family_override: Some(RuntimeProgressBarFamilyOverride::Braille),
        ..RuntimeStylePackOverrides::default()
    });
    let colors = resolve_theme_colors(Theme::Codex);
    assert_eq!(colors.progress_bar_family, ProgressBarFamily::Braille);
}

#[test]
fn resolve_theme_colors_applies_runtime_voice_scene_style_override() {
    let _guard = install_runtime_overrides(RuntimeStylePackOverrides {
        voice_scene_style_override: Some(RuntimeVoiceSceneStyleOverride::Pulse),
        ..RuntimeStylePackOverrides::default()
    });
    let colors = resolve_theme_colors(Theme::Codex);
    assert_eq!(colors.voice_scene_style, VoiceSceneStyle::Pulse);
}

#[test]
fn style_pack_theme_override_from_payload_reads_valid_base_theme() {
    let payload = r#"{"version":3,"profile":"ops","base_theme":"dracula"}"#;
    assert_eq!(
        style_pack_theme_override_from_payload(Some(payload)),
        Some(Theme::Dracula)
    );
}

#[test]
fn style_pack_theme_override_from_payload_ignores_invalid_payload() {
    let payload = r#"{"version":"bad","base_theme":"dracula"}"#;
    assert_eq!(style_pack_theme_override_from_payload(Some(payload)), None);
}

#[test]
fn resolve_theme_colors_ignores_style_pack_env_without_test_opt_in() {
    let _guard = env_lock();
    let prev_style_pack = std::env::var(STYLE_PACK_SCHEMA_ENV).ok();
    let prev_opt_in = std::env::var(STYLE_PACK_TEST_ENV_OPT_IN).ok();

    std::env::set_var(
        STYLE_PACK_SCHEMA_ENV,
        r#"{"version":3,"profile":"ops","base_theme":"codex"}"#,
    );
    std::env::remove_var(STYLE_PACK_TEST_ENV_OPT_IN);

    assert_eq!(resolve_theme_colors(Theme::Coral), THEME_CORAL);
    assert_eq!(locked_style_pack_theme(), None);

    match prev_style_pack {
        Some(value) => std::env::set_var(STYLE_PACK_SCHEMA_ENV, value),
        None => std::env::remove_var(STYLE_PACK_SCHEMA_ENV),
    }
    match prev_opt_in {
        Some(value) => std::env::set_var(STYLE_PACK_TEST_ENV_OPT_IN, value),
        None => std::env::remove_var(STYLE_PACK_TEST_ENV_OPT_IN),
    }
}

#[test]
fn resolve_theme_colors_reads_style_pack_env_when_test_opted_in() {
    let _guard = env_lock();
    let prev_style_pack = std::env::var(STYLE_PACK_SCHEMA_ENV).ok();
    let prev_opt_in = std::env::var(STYLE_PACK_TEST_ENV_OPT_IN).ok();

    std::env::set_var(
        STYLE_PACK_SCHEMA_ENV,
        r#"{"version":3,"profile":"ops","base_theme":"codex"}"#,
    );
    std::env::set_var(STYLE_PACK_TEST_ENV_OPT_IN, "1");

    assert_eq!(resolve_theme_colors(Theme::Coral), THEME_CODEX);
    assert_eq!(locked_style_pack_theme(), Some(Theme::Codex));

    match prev_style_pack {
        Some(value) => std::env::set_var(STYLE_PACK_SCHEMA_ENV, value),
        None => std::env::remove_var(STYLE_PACK_SCHEMA_ENV),
    }
    match prev_opt_in {
        Some(value) => std::env::set_var(STYLE_PACK_TEST_ENV_OPT_IN, value),
        None => std::env::remove_var(STYLE_PACK_TEST_ENV_OPT_IN),
    }
}

// -- Runtime theme-file override tests --

/// RAII guard that restores the thread-local theme file override on drop.
struct ThemeFileOverrideGuard {
    previous: Option<String>,
}

impl ThemeFileOverrideGuard {
    fn push(path: Option<String>) -> Self {
        let previous = runtime_theme_file_override();
        RUNTIME_THEME_FILE_OVERRIDE_TEST.with(|slot| *slot.borrow_mut() = path);
        Self { previous }
    }
}

impl Drop for ThemeFileOverrideGuard {
    fn drop(&mut self) {
        RUNTIME_THEME_FILE_OVERRIDE_TEST.with(|slot| *slot.borrow_mut() = self.previous.take());
    }
}

#[test]
fn runtime_theme_file_override_roundtrip() {
    let _guard = ThemeFileOverrideGuard::push(Some("/tmp/test.toml".into()));
    assert_eq!(runtime_theme_file_override(), Some("/tmp/test.toml".into()));
}

#[test]
fn runtime_theme_file_override_none_by_default() {
    let _guard = ThemeFileOverrideGuard::push(None);
    assert_eq!(runtime_theme_file_override(), None);
}

#[test]
fn set_runtime_theme_file_override_writes_to_thread_local() {
    let _guard = ThemeFileOverrideGuard::push(None);
    set_runtime_theme_file_override(Some("/tmp/custom.toml".into()));
    assert_eq!(
        runtime_theme_file_override(),
        Some("/tmp/custom.toml".into())
    );
}

#[test]
fn set_runtime_theme_file_override_clears_with_none() {
    let _guard = ThemeFileOverrideGuard::push(Some("/tmp/active.toml".into()));
    set_runtime_theme_file_override(None);
    assert_eq!(runtime_theme_file_override(), None);
}

// -- Persisted payload resolver precedence tests --

#[test]
fn resolved_toast_position_returns_none_without_payload_or_override() {
    let _env = env_lock();
    let prev_sp = std::env::var(STYLE_PACK_SCHEMA_ENV).ok();
    let prev_oi = std::env::var(STYLE_PACK_TEST_ENV_OPT_IN).ok();
    std::env::remove_var(STYLE_PACK_SCHEMA_ENV);
    std::env::remove_var(STYLE_PACK_TEST_ENV_OPT_IN);

    let _guard = install_runtime_overrides(RuntimeStylePackOverrides::default());
    assert_eq!(resolved_toast_position(Theme::Codex), None);

    match prev_sp {
        Some(v) => std::env::set_var(STYLE_PACK_SCHEMA_ENV, v),
        None => std::env::remove_var(STYLE_PACK_SCHEMA_ENV),
    }
    match prev_oi {
        Some(v) => std::env::set_var(STYLE_PACK_TEST_ENV_OPT_IN, v),
        None => std::env::remove_var(STYLE_PACK_TEST_ENV_OPT_IN),
    }
}

#[test]
fn resolved_toast_position_reads_persisted_payload() {
    let _env = env_lock();
    let prev_sp = std::env::var(STYLE_PACK_SCHEMA_ENV).ok();
    let prev_oi = std::env::var(STYLE_PACK_TEST_ENV_OPT_IN).ok();

    std::env::set_var(
        STYLE_PACK_SCHEMA_ENV,
        r#"{"version":3,"profile":"test","base_theme":"codex","surfaces":{"toast_position":"top-right"}}"#,
    );
    std::env::set_var(STYLE_PACK_TEST_ENV_OPT_IN, "1");

    let _guard = install_runtime_overrides(RuntimeStylePackOverrides::default());
    assert_eq!(
        resolved_toast_position(Theme::Codex),
        Some(ToastPositionOverride::TopRight),
    );

    match prev_sp {
        Some(v) => std::env::set_var(STYLE_PACK_SCHEMA_ENV, v),
        None => std::env::remove_var(STYLE_PACK_SCHEMA_ENV),
    }
    match prev_oi {
        Some(v) => std::env::set_var(STYLE_PACK_TEST_ENV_OPT_IN, v),
        None => std::env::remove_var(STYLE_PACK_TEST_ENV_OPT_IN),
    }
}

#[test]
fn resolved_toast_position_runtime_override_wins_over_payload() {
    let _env = env_lock();
    let prev_sp = std::env::var(STYLE_PACK_SCHEMA_ENV).ok();
    let prev_oi = std::env::var(STYLE_PACK_TEST_ENV_OPT_IN).ok();

    std::env::set_var(
        STYLE_PACK_SCHEMA_ENV,
        r#"{"version":3,"profile":"test","base_theme":"codex","surfaces":{"toast_position":"top-right"}}"#,
    );
    std::env::set_var(STYLE_PACK_TEST_ENV_OPT_IN, "1");

    let _guard = install_runtime_overrides(RuntimeStylePackOverrides {
        toast_position_override: Some(RuntimeToastPositionOverride::BottomCenter),
        ..RuntimeStylePackOverrides::default()
    });
    assert_eq!(
        resolved_toast_position(Theme::Codex),
        Some(ToastPositionOverride::BottomCenter),
    );

    match prev_sp {
        Some(v) => std::env::set_var(STYLE_PACK_SCHEMA_ENV, v),
        None => std::env::remove_var(STYLE_PACK_SCHEMA_ENV),
    }
    match prev_oi {
        Some(v) => std::env::set_var(STYLE_PACK_TEST_ENV_OPT_IN, v),
        None => std::env::remove_var(STYLE_PACK_TEST_ENV_OPT_IN),
    }
}

#[test]
fn resolved_banner_style_reads_persisted_payload() {
    let _env = env_lock();
    let prev_sp = std::env::var(STYLE_PACK_SCHEMA_ENV).ok();
    let prev_oi = std::env::var(STYLE_PACK_TEST_ENV_OPT_IN).ok();

    std::env::set_var(
        STYLE_PACK_SCHEMA_ENV,
        r#"{"version":4,"profile":"test","base_theme":"codex","components":{"banner_style":"compact"}}"#,
    );
    std::env::set_var(STYLE_PACK_TEST_ENV_OPT_IN, "1");

    let _guard = install_runtime_overrides(RuntimeStylePackOverrides::default());
    assert_eq!(
        resolved_banner_style(Theme::Codex),
        Some(BannerStyleOverride::Compact),
    );

    match prev_sp {
        Some(v) => std::env::set_var(STYLE_PACK_SCHEMA_ENV, v),
        None => std::env::remove_var(STYLE_PACK_SCHEMA_ENV),
    }
    match prev_oi {
        Some(v) => std::env::set_var(STYLE_PACK_TEST_ENV_OPT_IN, v),
        None => std::env::remove_var(STYLE_PACK_TEST_ENV_OPT_IN),
    }
}

#[test]
fn resolved_banner_style_runtime_override_wins_over_payload() {
    let _env = env_lock();
    let prev_sp = std::env::var(STYLE_PACK_SCHEMA_ENV).ok();
    let prev_oi = std::env::var(STYLE_PACK_TEST_ENV_OPT_IN).ok();

    std::env::set_var(
        STYLE_PACK_SCHEMA_ENV,
        r#"{"version":4,"profile":"test","base_theme":"codex","components":{"banner_style":"compact"}}"#,
    );
    std::env::set_var(STYLE_PACK_TEST_ENV_OPT_IN, "1");

    let _guard = install_runtime_overrides(RuntimeStylePackOverrides {
        banner_style_override: Some(RuntimeBannerStyleOverride::Hidden),
        ..RuntimeStylePackOverrides::default()
    });
    assert_eq!(
        resolved_banner_style(Theme::Codex),
        Some(BannerStyleOverride::Hidden),
    );

    match prev_sp {
        Some(v) => std::env::set_var(STYLE_PACK_SCHEMA_ENV, v),
        None => std::env::remove_var(STYLE_PACK_SCHEMA_ENV),
    }
    match prev_oi {
        Some(v) => std::env::set_var(STYLE_PACK_TEST_ENV_OPT_IN, v),
        None => std::env::remove_var(STYLE_PACK_TEST_ENV_OPT_IN),
    }
}

// -- resolved_startup_style precedence tests --

#[test]
fn resolved_startup_style_returns_none_without_payload_or_override() {
    let _env = env_lock();
    let prev_sp = std::env::var(STYLE_PACK_SCHEMA_ENV).ok();
    let prev_oi = std::env::var(STYLE_PACK_TEST_ENV_OPT_IN).ok();
    std::env::remove_var(STYLE_PACK_SCHEMA_ENV);
    std::env::remove_var(STYLE_PACK_TEST_ENV_OPT_IN);

    let _guard = install_runtime_overrides(RuntimeStylePackOverrides::default());
    assert_eq!(resolved_startup_style(Theme::Codex), None);

    match prev_sp {
        Some(v) => std::env::set_var(STYLE_PACK_SCHEMA_ENV, v),
        None => std::env::remove_var(STYLE_PACK_SCHEMA_ENV),
    }
    match prev_oi {
        Some(v) => std::env::set_var(STYLE_PACK_TEST_ENV_OPT_IN, v),
        None => std::env::remove_var(STYLE_PACK_TEST_ENV_OPT_IN),
    }
}

#[test]
fn resolved_startup_style_reads_persisted_payload() {
    let _env = env_lock();
    let prev_sp = std::env::var(STYLE_PACK_SCHEMA_ENV).ok();
    let prev_oi = std::env::var(STYLE_PACK_TEST_ENV_OPT_IN).ok();

    std::env::set_var(
        STYLE_PACK_SCHEMA_ENV,
        r#"{"version":3,"profile":"test","base_theme":"codex","surfaces":{"startup_style":"minimal"}}"#,
    );
    std::env::set_var(STYLE_PACK_TEST_ENV_OPT_IN, "1");

    let _guard = install_runtime_overrides(RuntimeStylePackOverrides::default());
    assert_eq!(
        resolved_startup_style(Theme::Codex),
        Some(StartupStyleOverride::Minimal),
    );

    match prev_sp {
        Some(v) => std::env::set_var(STYLE_PACK_SCHEMA_ENV, v),
        None => std::env::remove_var(STYLE_PACK_SCHEMA_ENV),
    }
    match prev_oi {
        Some(v) => std::env::set_var(STYLE_PACK_TEST_ENV_OPT_IN, v),
        None => std::env::remove_var(STYLE_PACK_TEST_ENV_OPT_IN),
    }
}

#[test]
fn resolved_startup_style_runtime_override_wins_over_payload() {
    let _env = env_lock();
    let prev_sp = std::env::var(STYLE_PACK_SCHEMA_ENV).ok();
    let prev_oi = std::env::var(STYLE_PACK_TEST_ENV_OPT_IN).ok();

    std::env::set_var(
        STYLE_PACK_SCHEMA_ENV,
        r#"{"version":3,"profile":"test","base_theme":"codex","surfaces":{"startup_style":"minimal"}}"#,
    );
    std::env::set_var(STYLE_PACK_TEST_ENV_OPT_IN, "1");

    let _guard = install_runtime_overrides(RuntimeStylePackOverrides {
        startup_style_override: Some(RuntimeStartupStyleOverride::Hidden),
        ..RuntimeStylePackOverrides::default()
    });
    assert_eq!(
        resolved_startup_style(Theme::Codex),
        Some(StartupStyleOverride::Hidden),
    );

    match prev_sp {
        Some(v) => std::env::set_var(STYLE_PACK_SCHEMA_ENV, v),
        None => std::env::remove_var(STYLE_PACK_SCHEMA_ENV),
    }
    match prev_oi {
        Some(v) => std::env::set_var(STYLE_PACK_TEST_ENV_OPT_IN, v),
        None => std::env::remove_var(STYLE_PACK_TEST_ENV_OPT_IN),
    }
}

// -- resolved_toast_severity_mode precedence tests --

#[test]
fn resolved_toast_severity_mode_returns_none_without_payload_or_override() {
    let _env = env_lock();
    let prev_sp = std::env::var(STYLE_PACK_SCHEMA_ENV).ok();
    let prev_oi = std::env::var(STYLE_PACK_TEST_ENV_OPT_IN).ok();
    std::env::remove_var(STYLE_PACK_SCHEMA_ENV);
    std::env::remove_var(STYLE_PACK_TEST_ENV_OPT_IN);

    let _guard = install_runtime_overrides(RuntimeStylePackOverrides::default());
    assert_eq!(resolved_toast_severity_mode(Theme::Codex), None);

    match prev_sp {
        Some(v) => std::env::set_var(STYLE_PACK_SCHEMA_ENV, v),
        None => std::env::remove_var(STYLE_PACK_SCHEMA_ENV),
    }
    match prev_oi {
        Some(v) => std::env::set_var(STYLE_PACK_TEST_ENV_OPT_IN, v),
        None => std::env::remove_var(STYLE_PACK_TEST_ENV_OPT_IN),
    }
}

#[test]
fn resolved_toast_severity_mode_reads_persisted_payload() {
    let _env = env_lock();
    let prev_sp = std::env::var(STYLE_PACK_SCHEMA_ENV).ok();
    let prev_oi = std::env::var(STYLE_PACK_TEST_ENV_OPT_IN).ok();

    std::env::set_var(
        STYLE_PACK_SCHEMA_ENV,
        r#"{"version":4,"profile":"test","base_theme":"codex","components":{"toast_severity_mode":"icon-and-label"}}"#,
    );
    std::env::set_var(STYLE_PACK_TEST_ENV_OPT_IN, "1");

    let _guard = install_runtime_overrides(RuntimeStylePackOverrides::default());
    assert_eq!(
        resolved_toast_severity_mode(Theme::Codex),
        Some(ToastSeverityMode::IconAndLabel),
    );

    match prev_sp {
        Some(v) => std::env::set_var(STYLE_PACK_SCHEMA_ENV, v),
        None => std::env::remove_var(STYLE_PACK_SCHEMA_ENV),
    }
    match prev_oi {
        Some(v) => std::env::set_var(STYLE_PACK_TEST_ENV_OPT_IN, v),
        None => std::env::remove_var(STYLE_PACK_TEST_ENV_OPT_IN),
    }
}

#[test]
fn resolved_toast_severity_mode_runtime_override_wins_over_payload() {
    let _env = env_lock();
    let prev_sp = std::env::var(STYLE_PACK_SCHEMA_ENV).ok();
    let prev_oi = std::env::var(STYLE_PACK_TEST_ENV_OPT_IN).ok();

    std::env::set_var(
        STYLE_PACK_SCHEMA_ENV,
        r#"{"version":4,"profile":"test","base_theme":"codex","components":{"toast_severity_mode":"icon-and-label"}}"#,
    );
    std::env::set_var(STYLE_PACK_TEST_ENV_OPT_IN, "1");

    let _guard = install_runtime_overrides(RuntimeStylePackOverrides {
        toast_severity_mode_override: Some(RuntimeToastSeverityModeOverride::Label),
        ..RuntimeStylePackOverrides::default()
    });
    assert_eq!(
        resolved_toast_severity_mode(Theme::Codex),
        Some(ToastSeverityMode::Label),
    );

    match prev_sp {
        Some(v) => std::env::set_var(STYLE_PACK_SCHEMA_ENV, v),
        None => std::env::remove_var(STYLE_PACK_SCHEMA_ENV),
    }
    match prev_oi {
        Some(v) => std::env::set_var(STYLE_PACK_TEST_ENV_OPT_IN, v),
        None => std::env::remove_var(STYLE_PACK_TEST_ENV_OPT_IN),
    }
}
