use crate::audio_meter::format_waveform;
use crate::config::HudRightPanel;
use crate::theme::{waveform_bars, GlyphSet, Theme, ThemeColors, VoiceSceneStyle};

use super::animation::heartbeat_glyph;
use super::state::{RecordingState, StatusLineState};
use super::text::truncate_display;

const RIGHT_PANEL_MAX_WAVEFORM_WIDTH: usize = 20;
const RIGHT_PANEL_MIN_CONTENT_WIDTH: usize = 4;
const LEVEL_WARNING_DB: f32 = -30.0;
const LEVEL_ERROR_DB: f32 = -18.0;

fn dim_waveform_placeholder(width: usize, colors: &ThemeColors) -> String {
    let mut result = String::with_capacity(width + colors.success.len() + colors.reset.len());
    let bars = waveform_bars(colors.glyph_set);
    result.push_str(colors.success);
    for _ in 0..width {
        result.push(bars[0]);
    }
    result.push_str(colors.reset);
    result
}

fn format_panel_brackets(content: &str, colors: &ThemeColors) -> String {
    let mut result =
        String::with_capacity(content.len() + colors.dim.len() * 2 + colors.reset.len() * 2 + 2);
    result.push_str(colors.dim);
    result.push('[');
    result.push_str(colors.reset);
    result.push_str(content);
    result.push_str(colors.dim);
    result.push(']');
    result.push_str(colors.reset);
    result
}

pub(super) fn format_right_panel(
    state: &StatusLineState,
    colors: &ThemeColors,
    theme: Theme,
    max_width: usize,
) -> String {
    if max_width == 0 {
        return String::new();
    }

    let mode = state.hud_right_panel;
    if mode == HudRightPanel::Off {
        return String::new();
    }
    let recording_active = state.recording_state == RecordingState::Recording;
    let scene_style = colors.voice_scene_style;
    let animate_panel = scene_should_animate(
        scene_style,
        state.hud_right_panel_recording_only,
        recording_active,
    );

    let content_width = max_width.saturating_sub(1);
    if content_width < RIGHT_PANEL_MIN_CONTENT_WIDTH {
        return " ".repeat(max_width);
    }

    let show_live = animate_panel && !state.meter_levels.is_empty();
    let panel_width = content_width;

    let panel = match mode {
        HudRightPanel::Ribbon => {
            let reserved = 2;
            let available = panel_width.saturating_sub(reserved);
            let max_wave_width = if scene_style == VoiceSceneStyle::Minimal {
                8
            } else {
                RIGHT_PANEL_MAX_WAVEFORM_WIDTH
            };
            let wave_width = available.min(max_wave_width);
            let waveform = if show_live {
                format_waveform(&state.meter_levels, wave_width, theme)
            } else {
                dim_waveform_placeholder(wave_width, colors)
            };
            format_panel_brackets(&waveform, colors)
        }
        HudRightPanel::Dots => {
            let idle_level = scene_idle_level(scene_style);
            let active = if animate_panel {
                state.meter_db.unwrap_or(idle_level)
            } else {
                idle_level
            };
            truncate_display(
                &format_pulse_dots(active, colors, scene_dot_count(scene_style)),
                panel_width,
            )
        }
        HudRightPanel::Heartbeat => {
            truncate_display(&format_heartbeat_panel(state, colors), panel_width)
        }
        HudRightPanel::Off => String::new(),
    };

    if panel.is_empty() {
        return String::new();
    }

    truncate_display(&panel, max_width)
}

#[inline]
pub(super) fn format_pulse_dots(level_db: f32, colors: &ThemeColors, dots: usize) -> String {
    let normalized = ((level_db + 60.0) / 60.0).clamp(0.0, 1.0);
    let dots = dots.max(1);
    let active = (normalized * dots as f32).round() as usize;
    let color = meter_level_color(level_db, colors);
    let mut result = String::with_capacity(128);
    result.push_str(colors.dim);
    result.push('[');
    for idx in 0..dots {
        if idx < active {
            result.push_str(color);
            result.push('•');
            result.push_str(colors.reset);
        } else {
            result.push_str(colors.dim);
            result.push('·');
            result.push_str(colors.reset);
        }
    }
    result.push_str(colors.dim);
    result.push(']');
    result.push_str(colors.reset);
    result
}

#[inline]
pub(super) fn meter_level_color(level_db: f32, colors: &ThemeColors) -> &str {
    if level_db < LEVEL_WARNING_DB {
        colors.success
    } else if level_db < LEVEL_ERROR_DB {
        colors.warning
    } else {
        colors.error
    }
}

#[inline]
pub(super) fn scene_should_animate(
    scene_style: VoiceSceneStyle,
    recording_only: bool,
    recording_active: bool,
) -> bool {
    match scene_style {
        VoiceSceneStyle::Theme => !recording_only || recording_active,
        VoiceSceneStyle::Pulse => true,
        VoiceSceneStyle::Static | VoiceSceneStyle::Minimal => false,
    }
}

#[inline]
fn scene_idle_level(scene_style: VoiceSceneStyle) -> f32 {
    match scene_style {
        VoiceSceneStyle::Static => -42.0,
        VoiceSceneStyle::Minimal => -50.0,
        VoiceSceneStyle::Theme | VoiceSceneStyle::Pulse => -60.0,
    }
}

#[inline]
fn scene_dot_count(scene_style: VoiceSceneStyle) -> usize {
    if scene_style == VoiceSceneStyle::Minimal {
        3
    } else {
        5
    }
}

#[inline]
pub(super) fn heartbeat_color(animate: bool, is_peak: bool, colors: &ThemeColors) -> &str {
    if animate && is_peak {
        colors.info
    } else {
        colors.dim
    }
}

pub(super) fn format_heartbeat_panel(state: &StatusLineState, colors: &ThemeColors) -> String {
    let animate = scene_should_animate(
        colors.voice_scene_style,
        state.hud_right_panel_recording_only,
        state.recording_state == RecordingState::Recording,
    );
    let (glyph, is_peak) = heartbeat_glyph(animate);

    let mut content = String::with_capacity(16);
    let color = heartbeat_color(animate, is_peak, colors);
    content.push_str(color);
    content.push(glyph);
    content.push_str(colors.reset);

    format_panel_brackets(&content, colors)
}

pub(super) fn format_minimal_right_panel(
    state: &StatusLineState,
    colors: &ThemeColors,
) -> Option<String> {
    if state.hud_right_panel == HudRightPanel::Off {
        return None;
    }
    let recording_active = state.recording_state == RecordingState::Recording;
    let scene_style = colors.voice_scene_style;
    let animate_panel = scene_should_animate(
        scene_style,
        state.hud_right_panel_recording_only,
        recording_active,
    );

    let panel = match state.hud_right_panel {
        HudRightPanel::Ribbon => {
            let levels = if animate_panel {
                &state.meter_levels
            } else {
                &[][..]
            };
            let waveform_width = if scene_style == VoiceSceneStyle::Minimal {
                4
            } else {
                6
            };
            let waveform = minimal_waveform(levels, waveform_width, colors);
            format!(
                "{}[{}{}{}]{}",
                colors.dim, colors.reset, waveform, colors.dim, colors.reset
            )
        }
        HudRightPanel::Dots => {
            let idle_level = scene_idle_level(scene_style);
            let level = if animate_panel {
                state.meter_db.unwrap_or(idle_level)
            } else {
                idle_level
            };
            minimal_pulse_dots(level, colors, scene_dot_count(scene_style))
        }
        HudRightPanel::Heartbeat => {
            let animate = scene_should_animate(
                scene_style,
                state.hud_right_panel_recording_only,
                recording_active,
            );
            let (glyph, is_peak) = heartbeat_glyph(animate);
            let color = if is_peak { colors.info } else { colors.dim };
            format!(
                "{}[{}{}{}{}]{}",
                colors.dim, colors.reset, color, glyph, colors.reset, colors.reset
            )
        }
        HudRightPanel::Off => return None,
    };
    Some(panel)
}

pub(super) fn minimal_waveform(levels: &[f32], width: usize, colors: &ThemeColors) -> String {
    let glyphs = waveform_bars(colors.glyph_set);
    if width == 0 {
        return String::new();
    }
    if levels.is_empty() {
        // Match full HUD behavior: keep idle placeholder in theme accent.
        return format!(
            "{}{}{}",
            colors.success,
            glyphs[0].to_string().repeat(width),
            colors.reset
        );
    }

    let mut out = String::with_capacity(width * 8);
    let start = levels.len().saturating_sub(width);
    let slice = &levels[start..];
    if slice.len() < width {
        out.push_str(colors.dim);
        out.push_str(&glyphs[0].to_string().repeat(width - slice.len()));
        out.push_str(colors.reset);
    }
    for db in slice {
        let normalized = ((*db + 60.0) / 60.0).clamp(0.0, 1.0);
        let idx = (normalized * (glyphs.len() as f32 - 1.0)) as usize;
        let color = meter_level_color(*db, colors);
        out.push_str(color);
        out.push(glyphs[idx]);
        out.push_str(colors.reset);
    }
    out
}

pub(super) fn minimal_pulse_dots(level_db: f32, colors: &ThemeColors, dots: usize) -> String {
    let normalized = ((level_db + 60.0) / 60.0).clamp(0.0, 1.0);
    let dots = dots.max(1);
    let active = (normalized * dots as f32).round() as usize;
    let (active_glyph, idle_glyph) = match colors.glyph_set {
        GlyphSet::Unicode => ('•', '·'),
        GlyphSet::Ascii => ('*', '.'),
    };
    let color = meter_level_color(level_db, colors);
    let mut result = String::with_capacity(64);
    result.push_str(colors.dim);
    result.push('[');
    result.push_str(colors.reset);
    for idx in 0..dots {
        if idx < active {
            result.push_str(color);
            result.push(active_glyph);
            result.push_str(colors.reset);
        } else {
            result.push_str(colors.dim);
            result.push(idle_glyph);
            result.push_str(colors.reset);
        }
    }
    result.push_str(colors.dim);
    result.push(']');
    result.push_str(colors.reset);
    result
}
