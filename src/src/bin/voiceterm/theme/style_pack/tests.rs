use super::*;
use std::sync::{Mutex, OnceLock};

static ENV_GUARD: OnceLock<Mutex<()>> = OnceLock::new();

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
    let _guard = ENV_GUARD
        .get_or_init(|| Mutex::new(()))
        .lock()
        .unwrap_or_else(|e| e.into_inner());
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
    let _guard = ENV_GUARD
        .get_or_init(|| Mutex::new(()))
        .lock()
        .unwrap_or_else(|e| e.into_inner());
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
