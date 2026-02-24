//! Themed CLI help renderer so `--help` is grouped and easier to scan.

use std::collections::BTreeMap;

use clap::{Arg, CommandFactory};
use crossterm::terminal::size as terminal_size;

use crate::banner::VERSION;
use crate::config::OverlayConfig;
use crate::overlay_frame::{
    centered_title_line, display_width, frame_bottom, frame_separator, frame_top, truncate_display,
};
use crate::theme::{resolved_overlay_border_set, BorderSet, Theme, ThemeColors};

const MIN_HELP_WIDTH: usize = 72;
const MAX_HELP_WIDTH: usize = 120;
const DEFAULT_HELP_WIDTH: usize = 100;
const FLAG_COL_MIN: usize = 24;
const FLAG_COL_MAX: usize = 42;
const FLAG_LABEL_PREFIX: &str = "> ";
const HELP_FOOTER: &str = "Tip: use --no-color or NO_COLOR=1 for plain output";

struct GroupSpec {
    title: &'static str,
    longs: &'static [&'static str],
}

const GROUPS: &[GroupSpec] = &[
    GroupSpec {
        title: "Backend",
        longs: &[
            "backend",
            "codex",
            "claude",
            "gemini",
            "login",
            "codex-cmd",
            "claude-cmd",
            "codex-arg",
            "persistent-codex",
            "claude-skip-permissions",
        ],
    },
    GroupSpec {
        title: "Voice",
        longs: &[
            "auto-voice",
            "voice-send-mode",
            "wake-word",
            "wake-word-sensitivity",
            "wake-word-cooldown-ms",
            "image-mode",
            "image-capture-command",
            "input-device",
            "auto-voice-idle-ms",
            "transcript-idle-ms",
        ],
    },
    GroupSpec {
        title: "Appearance",
        longs: &[
            "theme",
            "theme-file",
            "export-theme",
            "no-color",
            "hud-style",
            "minimal-hud",
            "hud-right-panel",
            "hud-border-style",
            "hud-right-panel-recording-only",
            "latency-display",
            "term",
        ],
    },
    GroupSpec {
        title: "STT / VAD",
        longs: &[
            "whisper-cmd",
            "whisper-model",
            "whisper-model-path",
            "whisper-beam-size",
            "whisper-temperature",
            "lang",
            "voice-sample-rate",
            "voice-vad-threshold-db",
            "voice-vad-engine",
            "voice-vad-frame-ms",
            "voice-vad-smoothing-frames",
        ],
    },
    GroupSpec {
        title: "Pipeline",
        longs: &[
            "python-cmd",
            "pipeline-script",
            "ffmpeg-cmd",
            "ffmpeg-device",
            "seconds",
            "voice-max-capture-ms",
            "voice-silence-tail-ms",
            "voice-min-speech-ms-before-stt",
            "voice-lookback-ms",
            "voice-buffer-ms",
            "voice-channel-capacity",
            "voice-stt-timeout-ms",
            "no-python-fallback",
        ],
    },
    GroupSpec {
        title: "Notifications / Logging",
        longs: &[
            "sounds",
            "sound-on-complete",
            "sound-on-error",
            "logs",
            "no-logs",
            "log-content",
            "log-timings",
            "session-memory",
            "session-memory-path",
            "prompt-regex",
            "prompt-log",
        ],
    },
    GroupSpec {
        title: "Diagnostics",
        longs: &[
            "doctor",
            "mic-meter",
            "mic-meter-ambient-ms",
            "mic-meter-speech-ms",
            "list-input-devices",
            "dev",
            "dev-log",
            "dev-path",
            "json-ipc",
            "help",
            "version",
        ],
    },
];

#[derive(Clone)]
struct HelpArgMeta {
    id: String,
    long: Option<String>,
    short: Option<char>,
    value_hint: String,
    help: String,
    defaults: Vec<String>,
    env: Option<String>,
    takes_value: bool,
}

impl HelpArgMeta {
    fn from_arg(arg: &Arg) -> Self {
        let help = arg
            .get_help()
            .or_else(|| arg.get_long_help())
            .map(std::string::ToString::to_string)
            .unwrap_or_default();
        let defaults = arg
            .get_default_values()
            .iter()
            .map(|value| value.to_string_lossy().to_string())
            .collect();
        let env = arg
            .get_env()
            .map(|value| value.to_string_lossy().to_string());
        let takes_value = arg.get_action().takes_values();

        Self {
            id: arg.get_id().to_string(),
            long: arg.get_long().map(str::to_string),
            short: arg.get_short(),
            value_hint: value_hint_for_arg(arg),
            help,
            defaults,
            env,
            takes_value,
        }
    }

    fn label(&self) -> String {
        match (self.short, self.long.as_deref()) {
            (Some(short), Some(long)) => format!("-{short}, --{long}{}", self.value_hint),
            (None, Some(long)) => format!("--{long}{}", self.value_hint),
            (Some(short), None) => format!("-{short}{}", self.value_hint),
            (None, None) => self.id.clone(),
        }
    }

    fn details(&self) -> Vec<String> {
        let mut details = Vec::new();
        if let Some(env) = &self.env {
            details.push(format!("[env: {env}]"));
        }
        if let Some(default) = default_detail(self) {
            details.push(format!("[default: {default}]"));
        }
        if details.is_empty() {
            Vec::new()
        } else {
            vec![details.join(" ")]
        }
    }
}

struct HelpSection {
    title: &'static str,
    entries: Vec<HelpArgMeta>,
}

pub(crate) fn print_themed_help(theme: Theme) {
    println!("{}", render_themed_help(theme));
}

pub(crate) fn render_themed_help(theme: Theme) -> String {
    let mut colors = help_palette(theme.colors());
    colors.borders = resolved_overlay_border_set(theme);
    let borders = &colors.borders;
    let section_color = help_section_color(&colors);
    let flag_color = help_flag_color(&colors);
    let description_color = help_description_color(&colors);
    let usage_color = help_usage_color(&colors);
    let width = resolved_help_width();
    let inner_width = width.saturating_sub(2);

    let mut lines = Vec::new();
    lines.push(frame_top(&colors, borders, width));
    lines.push(centered_title_line(
        &colors,
        borders,
        &format!("VoiceTerm v{VERSION}"),
        width,
    ));
    lines.push(centered_title_line(
        &colors,
        borders,
        "Themed, grouped CLI help",
        width,
    ));
    lines.push(frame_separator(&colors, borders, width));
    lines.push(format_content_line(
        &colors,
        borders,
        width,
        " Usage: voiceterm [OPTIONS]",
        usage_color,
    ));
    lines.push(format_content_line(
        &colors,
        borders,
        width,
        &format!(" Theme: {}", theme),
        colors.dim,
    ));
    lines.push(frame_separator(&colors, borders, width));

    let sections = grouped_sections();
    let flag_col = section_flag_col_width(&sections, inner_width);
    for (idx, section) in sections.iter().enumerate() {
        lines.push(format_content_line(
            &colors,
            borders,
            width,
            &format!(" [{}]", section.title),
            section_color,
        ));
        lines.push(blank_content_line(&colors, borders, width));
        for (entry_idx, entry) in section.entries.iter().enumerate() {
            let label = entry.label();
            lines.extend(format_flag_lines(
                &colors,
                borders,
                width,
                &label,
                &entry.help,
                flag_col,
                FlagLineColors {
                    flag: flag_color,
                    description: description_color,
                },
            ));
            for detail in entry.details() {
                lines.push(format_content_line(
                    &colors,
                    borders,
                    width,
                    &format!("   {detail}"),
                    colors.dim,
                ));
            }
            if entry_idx + 1 < section.entries.len() {
                lines.push(blank_content_line(&colors, borders, width));
            }
        }
        if idx + 1 < sections.len() {
            lines.push(frame_separator(&colors, borders, width));
        }
    }

    lines.push(frame_separator(&colors, borders, width));
    lines.push(format_content_line(
        &colors,
        borders,
        width,
        HELP_FOOTER,
        colors.dim,
    ));
    lines.push(frame_bottom(&colors, borders, width));
    lines.join("\n")
}

fn resolved_help_width() -> usize {
    terminal_size()
        .map(|(cols, _)| cols as usize)
        .unwrap_or(DEFAULT_HELP_WIDTH)
        .clamp(MIN_HELP_WIDTH, MAX_HELP_WIDTH)
}

fn format_content_line(
    colors: &ThemeColors,
    borders: &BorderSet,
    width: usize,
    text: &str,
    color: &str,
) -> String {
    let inner_width = width.saturating_sub(2);
    let clipped = truncate_display(text, inner_width);
    let padding = " ".repeat(inner_width.saturating_sub(display_width(&clipped)));
    let body = if color.is_empty() {
        clipped
    } else {
        format!("{color}{clipped}{}", colors.reset)
    };
    format!(
        "{}{}{}{}{}{}{}{}",
        colors.border,
        borders.vertical,
        colors.reset,
        body,
        padding,
        colors.border,
        borders.vertical,
        colors.reset
    )
}

fn blank_content_line(colors: &ThemeColors, borders: &BorderSet, width: usize) -> String {
    format_content_line(colors, borders, width, "", "")
}

struct FlagLineColors<'a> {
    flag: &'a str,
    description: &'a str,
}

fn format_flag_lines(
    colors: &ThemeColors,
    borders: &BorderSet,
    width: usize,
    label: &str,
    description: &str,
    label_col: usize,
    line_colors: FlagLineColors<'_>,
) -> Vec<String> {
    let inner_width = width.saturating_sub(2);
    let label = truncate_display(&format!("{FLAG_LABEL_PREFIX}{label}"), label_col);
    let label_pad = " ".repeat(label_col.saturating_sub(display_width(&label)));
    let desc_col = inner_width.saturating_sub(label_col + 2);
    let wrapped_desc = wrap_words(description, desc_col);
    let mut out = Vec::new();

    for (idx, chunk) in wrapped_desc.iter().enumerate() {
        let desc_pad = " ".repeat(desc_col.saturating_sub(display_width(chunk)));
        let description_body = if line_colors.description.is_empty() {
            format!("{chunk}{desc_pad}")
        } else {
            format!(
                "{}{chunk}{}{desc_pad}",
                line_colors.description, colors.reset
            )
        };
        let body = if idx == 0 {
            if line_colors.flag.is_empty() {
                format!(" {label}{label_pad} {description_body}")
            } else {
                format!(
                    " {}{}{}{} {}",
                    line_colors.flag, label, colors.reset, label_pad, description_body
                )
            }
        } else {
            format!(" {} {}", " ".repeat(label_col), description_body)
        };

        out.push(format!(
            "{}{}{}{}{}{}{}{}",
            colors.border,
            borders.vertical,
            colors.reset,
            body,
            "",
            colors.border,
            borders.vertical,
            colors.reset
        ));
    }

    out
}

fn help_section_color(colors: &ThemeColors) -> &str {
    if !colors.success.is_empty() {
        return colors.success;
    }
    if !colors.processing.is_empty() {
        return colors.processing;
    }
    if !colors.warning.is_empty() {
        return colors.warning;
    }
    if !colors.recording.is_empty() {
        return colors.recording;
    }
    colors.info
}

fn help_flag_color(colors: &ThemeColors) -> &str {
    if !colors.warning.is_empty() {
        return colors.warning;
    }
    if !colors.recording.is_empty() {
        return colors.recording;
    }
    colors.info
}

fn help_description_color(colors: &ThemeColors) -> &str {
    if !colors.info.is_empty() {
        return colors.info;
    }
    if !colors.processing.is_empty() {
        return colors.processing;
    }
    if !colors.reset.is_empty() {
        return colors.reset;
    }
    ""
}

fn help_usage_color(colors: &ThemeColors) -> &str {
    colors.dim
}

fn help_palette(mut colors: ThemeColors) -> ThemeColors {
    // Keep help borders quiet so one accent family (flags/section headers) leads the scan path.
    if !colors.dim.is_empty() {
        colors.border = colors.dim;
    }
    colors
}

fn grouped_sections() -> Vec<HelpSection> {
    let mut by_long = BTreeMap::<String, HelpArgMeta>::new();
    let mut no_long = Vec::<HelpArgMeta>::new();

    for entry in collect_help_args() {
        if let Some(long) = &entry.long {
            by_long.insert(long.clone(), entry);
        } else {
            no_long.push(entry);
        }
    }

    let mut sections = Vec::new();
    for spec in GROUPS {
        let mut entries = Vec::new();
        for long in spec.longs {
            if let Some(entry) = by_long.remove(*long) {
                entries.push(entry);
            }
        }
        if !entries.is_empty() {
            sections.push(HelpSection {
                title: spec.title,
                entries,
            });
        }
    }

    if !by_long.is_empty() || !no_long.is_empty() {
        let mut entries: Vec<HelpArgMeta> = by_long.into_values().collect();
        entries.extend(no_long);
        entries.sort_by_key(HelpArgMeta::label);
        sections.push(HelpSection {
            title: "Other",
            entries,
        });
    }

    sections
}

fn collect_help_args() -> Vec<HelpArgMeta> {
    let command = OverlayConfig::command();
    command
        .get_arguments()
        .filter(|arg| !arg.is_hide_set())
        .map(HelpArgMeta::from_arg)
        .collect()
}

fn section_flag_col_width(sections: &[HelpSection], inner_width: usize) -> usize {
    let widest_label = sections
        .iter()
        .flat_map(|section| &section.entries)
        .map(HelpArgMeta::label)
        .map(|label| display_width(FLAG_LABEL_PREFIX) + display_width(&label))
        .max()
        .unwrap_or(FLAG_COL_MIN);
    let by_inner_width = inner_width.saturating_sub(18).max(FLAG_COL_MIN);
    widest_label
        .clamp(FLAG_COL_MIN, FLAG_COL_MAX)
        .min(by_inner_width)
}

fn default_detail(meta: &HelpArgMeta) -> Option<String> {
    if meta.defaults.is_empty() {
        return None;
    }
    if !meta.takes_value
        && meta.defaults.len() == 1
        && meta
            .defaults
            .first()
            .is_some_and(|value| value.eq_ignore_ascii_case("false"))
    {
        return None;
    }
    Some(meta.defaults.join(", "))
}

fn value_hint_for_arg(arg: &Arg) -> String {
    if !arg.get_action().takes_values() {
        return String::new();
    }
    if let Some(name) = arg
        .get_value_names()
        .and_then(|names| names.first().map(std::string::ToString::to_string))
    {
        if name.len() <= 12 {
            return format!(" <{name}>");
        }
    }
    " <VALUE>".to_string()
}

fn wrap_words(text: &str, max_width: usize) -> Vec<String> {
    if max_width == 0 {
        return vec![String::new()];
    }
    if text.trim().is_empty() {
        return vec![String::new()];
    }

    let mut lines = Vec::new();
    let mut current = String::new();
    for word in text.split_whitespace() {
        let word_width = display_width(word);
        let current_width = display_width(&current);
        let needs_space = !current.is_empty();
        let proposed_width = current_width + usize::from(needs_space) + word_width;

        if proposed_width <= max_width {
            if needs_space {
                current.push(' ');
            }
            current.push_str(word);
            continue;
        }

        if !current.is_empty() {
            lines.push(current);
            current = String::new();
        }

        if word_width <= max_width {
            current.push_str(word);
            continue;
        }

        let mut remainder = word.to_string();
        while !remainder.is_empty() {
            let chunk = truncate_display(&remainder, max_width);
            let chunk_len = chunk.len();
            lines.push(chunk);
            remainder = remainder[chunk_len..].to_string();
        }
    }

    if !current.is_empty() {
        lines.push(current);
    }
    if lines.is_empty() {
        lines.push(String::new());
    }
    lines
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn grouped_help_contains_expected_sections() {
        let rendered = render_themed_help(Theme::None);
        assert!(rendered.contains("Backend"));
        assert!(rendered.contains("Voice"));
        assert!(rendered.contains("Appearance"));
        assert!(rendered.contains("Diagnostics"));
        assert!(rendered.contains("--backend"));
        assert!(rendered.contains("--voice-send-mode"));
    }

    #[test]
    fn grouped_help_no_color_has_no_ansi_sequences() {
        let rendered = render_themed_help(Theme::None);
        assert!(!rendered.contains("\x1b[3"));
        assert!(!rendered.contains("\x1b[9"));
        assert!(rendered.contains("Usage: voiceterm [OPTIONS]"));
    }

    #[test]
    fn grouped_help_codex_has_dual_tone_accents() {
        let colors = Theme::Codex.colors();
        let rendered = render_themed_help(Theme::Codex);
        assert!(rendered.contains(&format!("{} [Diagnostics]{}", colors.success, colors.reset)));
        assert!(rendered.contains(&format!("{}> --backend", colors.warning)));
    }

    #[test]
    fn grouped_help_codex_uses_distinct_description_color() {
        let colors = Theme::Codex.colors();
        let rendered = render_themed_help(Theme::Codex);
        assert!(rendered.contains(&format!("{}Backend CLI to run", colors.info)));
        assert!(!colors.info.is_empty());
        assert_ne!(colors.info, colors.warning);
    }

    #[test]
    fn grouped_help_uses_hacker_style_labels() {
        let rendered = render_themed_help(Theme::None);
        assert!(rendered.contains("[Backend]"));
        assert!(rendered.contains("> --backend"));
    }

    #[test]
    fn grouped_help_uses_dim_borders_for_codex_theme() {
        let colors = Theme::Codex.colors();
        let rendered = render_themed_help(Theme::Codex);
        assert!(rendered.contains(&format!("{}{}", colors.dim, colors.borders.top_left)));
    }

    #[test]
    fn wrap_words_breaks_long_text_without_exceeding_width() {
        let lines = wrap_words("alpha beta-gamma-delta epsilon", 10);
        assert!(lines.iter().all(|line| display_width(line) <= 10));
        assert!(lines.len() >= 3);
    }

    #[test]
    fn wrap_words_long_token_does_not_append_trailing_empty_line() {
        let lines = wrap_words("abcdefghijklmnop", 5);
        assert_eq!(lines, vec!["abcde", "fghij", "klmno", "p"]);
        assert!(!lines.last().is_some_and(String::is_empty));
    }

    #[test]
    fn all_long_flags_are_grouped_or_other() {
        let unknown = collect_help_args()
            .into_iter()
            .filter_map(|entry| entry.long)
            .filter(|long| {
                !GROUPS
                    .iter()
                    .any(|group| group.longs.contains(&long.as_str()))
            })
            .collect::<Vec<_>>();
        assert!(
            unknown.is_empty(),
            "unmapped long flags in custom help groups: {unknown:?}"
        );
    }

    #[test]
    fn default_detail_skips_false_for_switches() {
        let entry = HelpArgMeta {
            id: "help".to_string(),
            long: Some("help".to_string()),
            short: Some('h'),
            value_hint: String::new(),
            help: "Show help".to_string(),
            defaults: vec!["false".to_string()],
            env: None,
            takes_value: false,
        };
        assert!(default_detail(&entry).is_none());
    }
}
