use super::*;
use crate::theme::GlyphSet;

#[test]
fn format_left_section_uses_ascii_pipe_separator() {
    let mut colors = Theme::Codex.colors();
    colors.glyph_set = GlyphSet::Ascii;
    let state = StatusLineState::new();
    let rendered = format_left_section(&state, &colors);
    let plain = strip_ansi(&rendered);
    assert!(
        plain.contains('|'),
        "ASCII mode should use '|' separator in left section, got: {plain}"
    );
    assert!(
        !plain.contains('\u{2502}'),
        "ASCII mode must not contain Unicode box-drawing separator, got: {plain}"
    );
}

#[test]
fn format_left_section_recording_uses_ascii_pipe_separator() {
    let mut colors = Theme::Codex.colors();
    colors.glyph_set = GlyphSet::Ascii;
    let mut state = StatusLineState::new();
    state.recording_state = RecordingState::Recording;
    let rendered = format_left_section(&state, &colors);
    let plain = strip_ansi(&rendered);
    assert!(
        plain.contains('|'),
        "ASCII mode should use '|' separator during recording, got: {plain}"
    );
}

#[test]
fn format_shortcuts_uses_ascii_pipe_separator() {
    let mut colors = Theme::Codex.colors();
    colors.glyph_set = GlyphSet::Ascii;
    let rendered = format_shortcuts(&colors);
    let plain = strip_ansi(&rendered);
    assert!(
        plain.contains('|'),
        "ASCII mode should use '|' separator in shortcuts, got: {plain}"
    );
    assert!(
        !plain.contains('\u{2502}'),
        "ASCII mode must not contain Unicode box-drawing separator in shortcuts, got: {plain}"
    );
}

#[test]
fn hidden_launcher_text_uses_ascii_pipe_separator() {
    let mut colors = Theme::Codex.colors();
    colors.glyph_set = GlyphSet::Ascii;
    let state = StatusLineState::new();
    let (rendered, _) = format_hidden_launcher_with_buttons(&state, &colors, 80);
    let plain = strip_ansi(&rendered);
    assert!(
        plain.contains('|'),
        "ASCII mode should use '|' separator in hidden launcher, got: {plain}"
    );
    assert!(
        !plain.contains('\u{00B7}'),
        "ASCII mode must not contain Unicode middle-dot in hidden launcher, got: {plain}"
    );
}

#[test]
fn format_left_compact_uses_ascii_pipe_separator() {
    let mut colors = Theme::Codex.colors();
    colors.glyph_set = GlyphSet::Ascii;
    let state = StatusLineState::new();
    let rendered = format_left_compact(&state, &colors);
    let plain = strip_ansi(&rendered);
    assert!(
        plain.contains('|'),
        "ASCII mode should use '|' separator in compact left section, got: {plain}"
    );
    assert!(
        !plain.contains('\u{2502}'),
        "ASCII mode must not contain Unicode box-drawing separator in compact left section, got: {plain}"
    );
}

#[test]
fn format_compact_uses_ascii_safe_module_separator() {
    let mut colors = Theme::Codex.colors();
    colors.glyph_set = GlyphSet::Ascii;
    let mut state = StatusLineState::new();
    state.recording_state = RecordingState::Recording;
    state.queue_depth = 2;
    state.last_latency_ms = Some(123);
    state.meter_db = Some(-18.0);
    state.meter_levels = vec![-44.0, -31.0, -24.0, -18.0];
    let rendered = format_compact(&state, &colors, Theme::Codex, 80);
    let plain = strip_ansi(&rendered);
    assert!(
        plain.contains('|'),
        "ASCII mode should use '|' separator in compact status output, got: {plain}"
    );
    assert!(
        !plain.contains('\u{00B7}'),
        "ASCII mode must not contain Unicode middle-dot in compact status output, got: {plain}"
    );
    assert!(
        !plain.contains('\u{2502}'),
        "ASCII mode must not contain Unicode box-drawing separator in compact status output, got: {plain}"
    );
}

#[test]
fn format_shortcuts_compact_uses_ascii_pipe_separator() {
    let mut colors = Theme::Codex.colors();
    colors.glyph_set = GlyphSet::Ascii;
    let rendered = format_shortcuts_compact(&colors);
    let plain = strip_ansi(&rendered);
    assert!(
        plain.contains('|'),
        "ASCII mode should use '|' separator in compact shortcuts, got: {plain}"
    );
    assert!(
        !plain.contains('\u{00B7}'),
        "ASCII mode must not contain Unicode middle-dot in compact shortcuts, got: {plain}"
    );
}

#[test]
fn format_full_single_line_banner_uses_ascii_safe_separators() {
    let mut colors = Theme::Codex.colors();
    colors.glyph_set = GlyphSet::Ascii;
    colors.indicator_idle = "-";
    let mut state = StatusLineState::new();
    state.hud_style = HudStyle::Full;
    state.full_hud_single_line = true;
    state.recording_duration = Some(4.2);
    state.meter_db = Some(-21.0);
    state.message = "Ready".to_string();

    let banner = format_full_single_line_banner(&state, &colors, Theme::Codex, 140);
    let plain = strip_ansi(&banner.lines[0]);
    assert!(
        plain.contains('|'),
        "ASCII mode should use '|' separator in single-line full HUD, got: {plain}"
    );
    assert!(
        !plain.contains('\u{00B7}'),
        "ASCII mode must not contain Unicode middle-dot in single-line full HUD, got: {plain}"
    );
    assert!(
        !plain.contains('\u{2502}'),
        "ASCII mode must not contain Unicode box-drawing separator in single-line full HUD, got: {plain}"
    );
}
