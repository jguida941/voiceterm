//! Settings panel rendering so menu state maps to stable terminal output.

use crate::config::{HudBorderStyle, HudRightPanel, HudStyle, LatencyDisplayMode, VoiceSendMode};
use crate::overlay_frame::{
    centered_title_line, display_width, frame_bottom, frame_separator, frame_top, truncate_display,
};
use crate::status_line::Pipeline;
use crate::theme::ThemeColors;

use super::items::{
    settings_overlay_width_for_terminal, SettingsItem, SettingsView, SETTINGS_ITEMS,
    SETTINGS_OVERLAY_FOOTER,
};

pub fn format_settings_overlay(view: &SettingsView<'_>, width: usize) -> String {
    let colors = view.theme.colors();
    let borders = &colors.borders;
    let mut lines = Vec::new();
    let content_width = settings_overlay_width_for_terminal(width);

    lines.push(frame_top(&colors, borders, content_width));
    lines.push(centered_title_line(
        &colors,
        borders,
        "VoiceTerm Settings",
        content_width,
    ));
    lines.push(frame_separator(&colors, borders, content_width));

    for (idx, item) in SETTINGS_ITEMS.iter().enumerate() {
        let selected = idx == view.selected;
        let line = format_settings_row(view, *item, selected, &colors, content_width);
        lines.push(line);
    }

    let selected_item = SETTINGS_ITEMS
        .get(view.selected)
        .copied()
        .unwrap_or(SettingsItem::AutoVoice);
    lines.push(format_description_row(
        &colors,
        content_width,
        setting_description(selected_item),
    ));
    lines.push(frame_separator(&colors, borders, content_width));
    // Footer with clickable close button
    lines.push(centered_title_line(
        &colors,
        borders,
        SETTINGS_OVERLAY_FOOTER,
        content_width,
    ));
    lines.push(frame_bottom(&colors, borders, content_width));

    lines.join("\n")
}

fn format_settings_row(
    view: &SettingsView<'_>,
    item: SettingsItem,
    selected: bool,
    colors: &ThemeColors,
    width: usize,
) -> String {
    const LABEL_WIDTH: usize = 15;
    let marker = if selected { "▸" } else { " " };
    let read_only = matches!(item, SettingsItem::Backend | SettingsItem::Pipeline);

    let row_text = match item {
        SettingsItem::AutoVoice => format!(
            "{marker} {:<width$} {}",
            "Auto-voice",
            toggle_button(view.auto_voice_enabled),
            width = LABEL_WIDTH
        ),
        SettingsItem::WakeWord => format!(
            "{marker} {:<width$} {}",
            "Wake word",
            toggle_button(view.wake_word_enabled),
            width = LABEL_WIDTH
        ),
        SettingsItem::WakeSensitivity => {
            let slider = format_normalized_slider(view.wake_word_sensitivity, 14);
            format!(
                "{marker} {:<width$} {slider} {:>3.0}% (0-100%)",
                "Wake sensitivity",
                view.wake_word_sensitivity * 100.0,
                width = LABEL_WIDTH
            )
        }
        SettingsItem::WakeCooldown => format!(
            "{marker} {:<width$} {}",
            "Wake cooldown",
            button_label(&format!("{} ms", view.wake_word_cooldown_ms)),
            width = LABEL_WIDTH
        ),
        SettingsItem::SendMode => format!(
            "{marker} {:<width$} {}",
            "Send mode",
            mode_button(view.send_mode),
            width = LABEL_WIDTH
        ),
        SettingsItem::Macros => format!(
            "{marker} {:<width$} {}",
            "Macros",
            toggle_button(view.macros_enabled),
            width = LABEL_WIDTH
        ),
        SettingsItem::Sensitivity => {
            let slider = format_slider(view.sensitivity_db, 14);
            format!(
                "{marker} {:<width$} {slider} {:>4.0} dB (-80..-10)",
                "Sensitivity",
                view.sensitivity_db,
                width = LABEL_WIDTH
            )
        }
        SettingsItem::Theme => format!(
            "{marker} {:<width$} {}",
            "Theme",
            button_label(&view.theme.to_string()),
            width = LABEL_WIDTH
        ),
        SettingsItem::HudStyle => format!(
            "{marker} {:<width$} {}",
            "HUD style",
            hud_style_button(view.hud_style),
            width = LABEL_WIDTH
        ),
        SettingsItem::HudBorders => format!(
            "{marker} {:<width$} {}",
            "Borders",
            hud_border_style_button(view.hud_border_style),
            width = LABEL_WIDTH
        ),
        SettingsItem::HudPanel => format!(
            "{marker} {:<width$} {}",
            "Right panel",
            hud_panel_button(view.hud_right_panel),
            width = LABEL_WIDTH
        ),
        SettingsItem::HudAnimate => format!(
            "{marker} {:<width$} {}",
            "Anim rec-only",
            toggle_button(view.hud_right_panel_recording_only),
            width = LABEL_WIDTH
        ),
        SettingsItem::Latency => format!(
            "{marker} {:<width$} {}",
            "Latency",
            latency_mode_button(view.latency_display),
            width = LABEL_WIDTH
        ),
        SettingsItem::Mouse => format!(
            "{marker} {:<width$} {}",
            "Mouse",
            toggle_button(view.mouse_enabled),
            width = LABEL_WIDTH
        ),
        SettingsItem::Backend => format!(
            "{marker} {:<width$} {} (read-only)",
            "Backend",
            view.backend_label,
            width = LABEL_WIDTH
        ),
        SettingsItem::Pipeline => format!(
            "{marker} {:<width$} {} (read-only)",
            "Pipeline",
            pipeline_label(view.pipeline),
            width = LABEL_WIDTH
        ),
        SettingsItem::Close => format!("{marker} {}", button_label("Close")),
        SettingsItem::Quit => format!("{marker} {}", button_label("Quit VoiceTerm")),
    };

    format_menu_row(colors, width, &row_text, selected, read_only)
}

fn pipeline_label(pipeline: Pipeline) -> &'static str {
    match pipeline {
        Pipeline::Rust => "Rust",
        Pipeline::Python => "Python",
    }
}

fn toggle_button(enabled: bool) -> String {
    if enabled {
        button_label("ON")
    } else {
        button_label("OFF")
    }
}

fn mode_button(mode: VoiceSendMode) -> String {
    match mode {
        VoiceSendMode::Auto => button_label("Auto"),
        VoiceSendMode::Insert => button_label("Edit"),
    }
}

fn hud_panel_button(panel: HudRightPanel) -> String {
    match panel {
        HudRightPanel::Off => button_label("Off"),
        HudRightPanel::Ribbon => button_label("Ribbon"),
        HudRightPanel::Dots => button_label("Dots"),
        HudRightPanel::Heartbeat => button_label("Heartbeat"),
    }
}

fn hud_style_button(style: HudStyle) -> String {
    match style {
        HudStyle::Full => button_label("Full"),
        HudStyle::Minimal => button_label("Minimal"),
        HudStyle::Hidden => button_label("Hidden"),
    }
}

fn hud_border_style_button(style: HudBorderStyle) -> String {
    match style {
        HudBorderStyle::Theme => button_label("Theme"),
        HudBorderStyle::Single => button_label("Single"),
        HudBorderStyle::Rounded => button_label("Rounded"),
        HudBorderStyle::Double => button_label("Double"),
        HudBorderStyle::Heavy => button_label("Heavy"),
        HudBorderStyle::None => button_label("None"),
    }
}

fn latency_mode_button(mode: LatencyDisplayMode) -> String {
    match mode {
        LatencyDisplayMode::Off => button_label("Off"),
        LatencyDisplayMode::Short => button_label("Nms"),
        LatencyDisplayMode::Label => button_label("Latency: Nms"),
    }
}

fn button_label(label: &str) -> String {
    format!("[ {label} ]")
}

fn format_slider(value_db: f32, width: usize) -> String {
    let min_db = -80.0;
    let max_db = -10.0;
    let clamped = value_db.clamp(min_db, max_db);
    let ratio = if (max_db - min_db).abs() < f32::EPSILON {
        0.0
    } else {
        (clamped - min_db) / (max_db - min_db)
    };
    let pos = ((width.saturating_sub(1)) as f32 * ratio).round() as usize;
    let mut bar = String::with_capacity(width);
    for idx in 0..width {
        if idx == pos {
            bar.push('●');
        } else {
            bar.push('─');
        }
    }
    bar
}

fn format_normalized_slider(value: f32, width: usize) -> String {
    let clamped = value.clamp(0.0, 1.0);
    let pos = ((width.saturating_sub(1)) as f32 * clamped).round() as usize;
    let mut bar = String::with_capacity(width);
    for idx in 0..width {
        if idx == pos {
            bar.push('●');
        } else {
            bar.push('─');
        }
    }
    bar
}

fn format_menu_row(
    colors: &ThemeColors,
    width: usize,
    text: &str,
    selected: bool,
    read_only: bool,
) -> String {
    let borders = &colors.borders;
    let inner_width = width.saturating_sub(2);
    let clipped = truncate_display(text, inner_width);
    let padded = format!(
        "{clipped}{}",
        " ".repeat(inner_width.saturating_sub(display_width(&clipped)))
    );
    let styled = if selected {
        if read_only {
            format!("{}{}{}", colors.dim, padded, colors.reset)
        } else {
            format!("{}{}{}", colors.info, padded, colors.reset)
        }
    } else if read_only {
        format!("{}{}{}", colors.dim, padded, colors.reset)
    } else {
        padded
    };

    format!(
        "{}{}{}{}{}{}{}",
        colors.border,
        borders.vertical,
        colors.reset,
        styled,
        colors.border,
        borders.vertical,
        colors.reset
    )
}

fn format_description_row(colors: &ThemeColors, width: usize, description: &str) -> String {
    let borders = &colors.borders;
    let inner_width = width.saturating_sub(2);
    let text = format!(" tip: {description}");
    let clipped = truncate_display(&text, inner_width);
    let pad = " ".repeat(inner_width.saturating_sub(display_width(&clipped)));
    format!(
        "{}{}{}{}{}{}{}{}",
        colors.border,
        borders.vertical,
        colors.dim,
        clipped,
        pad,
        colors.border,
        borders.vertical,
        colors.reset
    )
}

fn setting_description(item: SettingsItem) -> &'static str {
    match item {
        SettingsItem::AutoVoice => "Enable continuous listening and auto-rearm behavior.",
        SettingsItem::WakeWord => "Toggle always-listening wake detector.",
        SettingsItem::WakeSensitivity => "Higher % is more sensitive to wake phrases.",
        SettingsItem::WakeCooldown => "Minimum delay between consecutive wake triggers.",
        SettingsItem::SendMode => "Auto sends transcript immediately; Edit stages text first.",
        SettingsItem::Macros => "Apply phrase macros before transcript delivery.",
        SettingsItem::Sensitivity => "Voice activity threshold for speech detection.",
        SettingsItem::Theme => "Open theme picker to choose visual palette.",
        SettingsItem::HudStyle => "Switch between Full, Minimal, and Hidden HUD.",
        SettingsItem::HudBorders => "Choose HUD border style and framing.",
        SettingsItem::HudPanel => "Select right-panel telemetry widget mode.",
        SettingsItem::HudAnimate => "When ON, right-panel animates during recording only.",
        SettingsItem::Latency => "Control visibility format of STT latency badge.",
        SettingsItem::Mouse => "Enable clickable HUD controls and overlay rows.",
        SettingsItem::Backend => "Current backend provider for this session (read-only).",
        SettingsItem::Pipeline => "Active voice pipeline implementation (read-only).",
        SettingsItem::Close => "Close settings overlay and return to HUD.",
        SettingsItem::Quit => "Exit VoiceTerm immediately.",
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::config::{
        HudBorderStyle, HudRightPanel, HudStyle, LatencyDisplayMode, VoiceSendMode,
    };
    use crate::settings::settings_overlay_height;
    use crate::status_line::Pipeline;
    use crate::theme::Theme;

    #[test]
    fn settings_overlay_height_matches_items() {
        let height = settings_overlay_height();
        assert_eq!(height, SETTINGS_ITEMS.len() + 7);
    }

    #[test]
    fn settings_overlay_uses_edit_label_for_insert_send_mode() {
        let view = SettingsView {
            selected: 1,
            auto_voice_enabled: false,
            wake_word_enabled: false,
            wake_word_sensitivity: 0.55,
            wake_word_cooldown_ms: 2000,
            send_mode: VoiceSendMode::Insert,
            macros_enabled: true,
            sensitivity_db: -35.0,
            theme: Theme::Coral,
            hud_style: HudStyle::Full,
            hud_border_style: HudBorderStyle::Theme,
            hud_right_panel: HudRightPanel::Off,
            hud_right_panel_recording_only: false,
            latency_display: LatencyDisplayMode::Short,
            mouse_enabled: true,
            backend_label: "codex",
            pipeline: Pipeline::Rust,
        };
        let rendered = format_settings_overlay(&view, 90);
        assert!(rendered.contains("Send mode"));
        assert!(rendered.contains("[ Edit ]"));
        assert!(!rendered.contains("[ Insert ]"));
    }

    #[test]
    fn settings_overlay_renders_selected_item_description() {
        let view = SettingsView {
            selected: SETTINGS_ITEMS
                .iter()
                .position(|item| *item == SettingsItem::WakeSensitivity)
                .expect("wake sensitivity item exists"),
            auto_voice_enabled: false,
            wake_word_enabled: false,
            wake_word_sensitivity: 0.55,
            wake_word_cooldown_ms: 2000,
            send_mode: VoiceSendMode::Auto,
            macros_enabled: true,
            sensitivity_db: -35.0,
            theme: Theme::Coral,
            hud_style: HudStyle::Full,
            hud_border_style: HudBorderStyle::Theme,
            hud_right_panel: HudRightPanel::Off,
            hud_right_panel_recording_only: false,
            latency_display: LatencyDisplayMode::Short,
            mouse_enabled: true,
            backend_label: "codex",
            pipeline: Pipeline::Rust,
        };
        let rendered = format_settings_overlay(&view, 90);
        assert!(rendered.contains("tip: Higher % is more sensitive"));
    }

    #[test]
    fn settings_overlay_marks_backend_as_read_only() {
        let view = SettingsView {
            selected: SETTINGS_ITEMS
                .iter()
                .position(|item| *item == SettingsItem::Backend)
                .expect("backend item exists"),
            auto_voice_enabled: false,
            wake_word_enabled: false,
            wake_word_sensitivity: 0.55,
            wake_word_cooldown_ms: 2000,
            send_mode: VoiceSendMode::Auto,
            macros_enabled: true,
            sensitivity_db: -35.0,
            theme: Theme::Coral,
            hud_style: HudStyle::Full,
            hud_border_style: HudBorderStyle::Theme,
            hud_right_panel: HudRightPanel::Off,
            hud_right_panel_recording_only: false,
            latency_display: LatencyDisplayMode::Short,
            mouse_enabled: true,
            backend_label: "codex",
            pipeline: Pipeline::Rust,
        };
        let rendered = format_settings_overlay(&view, 90);
        assert!(rendered.contains("Backend"));
        assert!(rendered.contains("(read-only)"));
    }
}
