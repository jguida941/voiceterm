//! Toast notification center with auto-dismiss, severity, and history review.
//!
//! Provides a runtime notification surface for transient user feedback messages.
//! Toasts auto-dismiss after a configurable duration and are categorized by
//! severity. A bounded history ring is kept for later review.

use std::collections::VecDeque;
use std::time::{Duration, Instant};

use crate::overlay_frame::{
    centered_title_line, display_width, frame_bottom, frame_top, truncate_display,
};
use crate::theme::{
    overlay_close_symbol, overlay_separator, BorderSet, GlyphSet, Theme, ThemeColors,
};

/// Maximum number of toasts kept in the history ring.
pub(crate) const TOAST_HISTORY_MAX: usize = 50;

/// Default auto-dismiss duration for info/success toasts.
pub(crate) const DEFAULT_DISMISS_MS: u64 = 4_000;

/// Auto-dismiss duration for warning toasts.
pub(crate) const WARNING_DISMISS_MS: u64 = 6_000;

/// Auto-dismiss duration for error toasts.
pub(crate) const ERROR_DISMISS_MS: u64 = 8_000;

/// Maximum number of toasts visible simultaneously.
pub(crate) const MAX_VISIBLE_TOASTS: usize = 3;

/// Toast severity level.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub(crate) enum ToastSeverity {
    Info,
    Success,
    Warning,
    Error,
}

impl ToastSeverity {
    /// ANSI color code for this severity using theme colors.
    #[must_use]
    pub(crate) fn color<'a>(&self, colors: &'a ThemeColors) -> &'a str {
        match self {
            Self::Info => colors.info,
            Self::Success => colors.success,
            Self::Warning => colors.warning,
            Self::Error => colors.error,
        }
    }

    /// Severity label for display.
    #[must_use]
    pub(crate) fn label(&self) -> &'static str {
        match self {
            Self::Info => "INFO",
            Self::Success => "OK",
            Self::Warning => "WARN",
            Self::Error => "ERR",
        }
    }

    /// Severity icon by glyph set.
    #[must_use]
    pub(crate) fn icon(&self, glyph_set: GlyphSet) -> &'static str {
        match glyph_set {
            GlyphSet::Unicode => match self {
                Self::Info => "ℹ",
                Self::Success => "✓",
                Self::Warning => "⚠",
                Self::Error => "✗",
            },
            GlyphSet::Ascii => match self {
                Self::Info => "i",
                Self::Success => "+",
                Self::Warning => "!",
                Self::Error => "x",
            },
        }
    }

    /// Default auto-dismiss duration for this severity.
    #[must_use]
    pub(crate) fn default_dismiss_duration(&self) -> Duration {
        match self {
            Self::Info | Self::Success => Duration::from_millis(DEFAULT_DISMISS_MS),
            Self::Warning => Duration::from_millis(WARNING_DISMISS_MS),
            Self::Error => Duration::from_millis(ERROR_DISMISS_MS),
        }
    }
}

/// A single toast notification.
#[derive(Debug, Clone)]
pub(crate) struct Toast {
    /// Unique monotonic ID for ordering.
    pub(crate) id: u64,
    /// Severity level.
    pub(crate) severity: ToastSeverity,
    /// Message text.
    pub(crate) message: String,
    /// When this toast was created.
    pub(crate) created_at: Instant,
    /// When this toast should auto-dismiss.
    pub(crate) dismiss_at: Instant,
    /// Whether the user explicitly dismissed this toast.
    pub(crate) dismissed: bool,
}

/// Toast notification center state.
#[derive(Debug)]
pub(crate) struct ToastCenter {
    /// Currently active (visible) toasts.
    active: VecDeque<Toast>,
    /// History ring of all toasts (including dismissed).
    history: VecDeque<Toast>,
    /// Monotonic ID counter.
    next_id: u64,
}

impl ToastCenter {
    /// Create a new empty toast center.
    #[must_use]
    pub(crate) fn new() -> Self {
        Self {
            active: VecDeque::new(),
            history: VecDeque::new(),
            next_id: 0,
        }
    }

    /// Push a new toast notification.
    pub(crate) fn push(&mut self, severity: ToastSeverity, message: impl Into<String>) {
        let now = Instant::now();
        let dismiss_at = now + severity.default_dismiss_duration();
        let toast = Toast {
            id: self.next_id,
            severity,
            message: message.into(),
            created_at: now,
            dismiss_at,
            dismissed: false,
        };
        self.next_id += 1;

        // Evict oldest active toast if at capacity.
        if self.active.len() >= MAX_VISIBLE_TOASTS {
            if let Some(mut evicted) = self.active.pop_front() {
                evicted.dismissed = true;
                self.push_history(evicted);
            }
        }

        self.active.push_back(toast);
    }

    /// Push a toast with a custom dismiss duration.
    pub(crate) fn push_with_duration(
        &mut self,
        severity: ToastSeverity,
        message: impl Into<String>,
        dismiss_after: Duration,
    ) {
        let now = Instant::now();
        let toast = Toast {
            id: self.next_id,
            severity,
            message: message.into(),
            created_at: now,
            dismiss_at: now + dismiss_after,
            dismissed: false,
        };
        self.next_id += 1;

        if self.active.len() >= MAX_VISIBLE_TOASTS {
            if let Some(mut evicted) = self.active.pop_front() {
                evicted.dismissed = true;
                self.push_history(evicted);
            }
        }

        self.active.push_back(toast);
    }

    /// Tick the toast center: dismiss expired toasts.
    /// Returns `true` if any toasts were dismissed (caller should redraw).
    pub(crate) fn tick(&mut self) -> bool {
        let now = Instant::now();
        let before = self.active.len();
        let mut expired = Vec::new();

        self.active.retain(|toast| {
            if toast.dismissed || now >= toast.dismiss_at {
                expired.push(toast.clone());
                false
            } else {
                true
            }
        });

        for mut toast in expired {
            toast.dismissed = true;
            self.push_history(toast);
        }

        self.active.len() != before
    }

    /// Dismiss the most recent active toast (user action).
    pub(crate) fn dismiss_latest(&mut self) -> bool {
        if let Some(mut toast) = self.active.pop_back() {
            toast.dismissed = true;
            self.push_history(toast);
            true
        } else {
            false
        }
    }

    /// Dismiss all active toasts.
    pub(crate) fn dismiss_all(&mut self) {
        while let Some(mut toast) = self.active.pop_front() {
            toast.dismissed = true;
            self.push_history(toast);
        }
    }

    /// Number of currently active (visible) toasts.
    #[must_use]
    pub(crate) fn active_count(&self) -> usize {
        self.active.len()
    }

    /// Active toasts in display order (oldest first).
    #[must_use]
    pub(crate) fn active_toasts(&self) -> &VecDeque<Toast> {
        &self.active
    }

    /// History entries (oldest first, bounded by `TOAST_HISTORY_MAX`).
    #[must_use]
    pub(crate) fn history(&self) -> &VecDeque<Toast> {
        &self.history
    }

    /// Number of history entries.
    #[must_use]
    pub(crate) fn history_count(&self) -> usize {
        self.history.len()
    }

    fn push_history(&mut self, toast: Toast) {
        if self.history.len() >= TOAST_HISTORY_MAX {
            self.history.pop_front();
        }
        self.history.push_back(toast);
    }
}

impl Default for ToastCenter {
    fn default() -> Self {
        Self::new()
    }
}

/// Format a single toast line for inline HUD display.
#[must_use]
pub(crate) fn format_toast_inline(toast: &Toast, colors: &ThemeColors, max_width: usize) -> String {
    let icon = toast.severity.icon(colors.glyph_set);
    let severity_color = toast.severity.color(colors);
    let prefix = format!("[{}]", toast.severity.label());
    // Calculate visible content budget: icon + space + prefix + space + message
    let prefix_width = display_width(icon) + 1 + display_width(&prefix) + 1;
    let msg_budget = max_width.saturating_sub(prefix_width);
    let truncated_msg = truncate_display(&toast.message, msg_budget);
    format!(
        "{severity_color}{icon} {prefix}{reset} {truncated_msg}",
        reset = colors.reset,
    )
}

/// Format a toast history overlay panel for review.
fn framed_toast_history_row(
    colors: &ThemeColors,
    borders: &BorderSet,
    width: usize,
    content: &str,
    content_width: usize,
) -> String {
    let body_width = width.saturating_sub(4);
    let row_padding = body_width.saturating_sub(content_width);

    format!(
        "{}{}{} {content}{} {}{}{}",
        colors.border,
        borders.vertical,
        colors.reset,
        " ".repeat(row_padding),
        colors.border,
        borders.vertical,
        colors.reset,
    )
}

/// Format a toast history overlay panel for review.
#[must_use]
pub(crate) fn format_toast_history_overlay(
    center: &ToastCenter,
    theme: Theme,
    width: usize,
) -> String {
    let width = width.max(4);
    let colors = theme.colors();
    let borders = &colors.borders;
    let sep = overlay_separator(colors.glyph_set);
    let close_sym = overlay_close_symbol(colors.glyph_set);

    let mut lines = Vec::new();
    lines.push(frame_top(&colors, borders, width));

    let title = format!("Toast History ({} entries)", center.history_count());
    lines.push(centered_title_line(&colors, borders, &title, width));

    // Content rows
    let body_width = width.saturating_sub(4); // side borders + one-space left/right padding
    if center.history.is_empty() {
        let empty_msg = "No notifications yet.";
        let clipped_msg = truncate_display(empty_msg, body_width);
        let padding = body_width.saturating_sub(display_width(&clipped_msg));
        let left_pad = padding / 2;
        let right_pad = padding - left_pad;
        let centered = format!(
            "{}{}{}{}{}",
            " ".repeat(left_pad),
            colors.dim,
            clipped_msg,
            colors.reset,
            " ".repeat(right_pad),
        );
        lines.push(framed_toast_history_row(
            &colors, borders, width, &centered, body_width,
        ));
    } else {
        // Show most recent entries (up to 10 visible in overlay).
        let visible_count = center.history.len().min(10);
        let start = center.history.len().saturating_sub(visible_count);
        for toast in center.history.iter().skip(start) {
            let icon = toast.severity.icon(colors.glyph_set);
            let severity_color = toast.severity.color(&colors);
            let label = toast.severity.label();
            let prefix = format!("{icon} [{label}]");
            let plain_content = format!("{prefix} {}", toast.message);
            let clipped = truncate_display(&plain_content, body_width);
            let clipped_width = display_width(&clipped);
            let content = if let Some(rest) = clipped.strip_prefix(&prefix) {
                format!("{severity_color}{prefix}{}{}", colors.reset, rest)
            } else {
                format!("{severity_color}{clipped}{}", colors.reset)
            };
            lines.push(framed_toast_history_row(
                &colors,
                borders,
                width,
                &content,
                clipped_width,
            ));
        }
    }

    // Footer
    let footer = format!(
        "[{close_sym}] close {sep} {count} total",
        count = center.history_count()
    );
    lines.push(centered_title_line(&colors, borders, &footer, width));
    lines.push(frame_bottom(&colors, borders, width));

    lines.join("\n")
}

/// Height of the toast history overlay in terminal rows.
#[must_use]
pub(crate) fn toast_history_overlay_height(center: &ToastCenter) -> usize {
    let content_rows = if center.history.is_empty() {
        1
    } else {
        center.history.len().min(10)
    };
    // top border + title + content rows + footer + bottom border
    content_rows + 4
}

#[cfg(test)]
mod tests {
    use super::*;

    fn strip_ansi_sgr(input: &str) -> String {
        let mut out = String::with_capacity(input.len());
        let mut in_escape = false;
        for ch in input.chars() {
            if ch == '\x1b' {
                in_escape = true;
                continue;
            }
            if in_escape {
                if ch == 'm' {
                    in_escape = false;
                }
                continue;
            }
            out.push(ch);
        }
        out
    }

    #[test]
    fn toast_severity_labels() {
        assert_eq!(ToastSeverity::Info.label(), "INFO");
        assert_eq!(ToastSeverity::Success.label(), "OK");
        assert_eq!(ToastSeverity::Warning.label(), "WARN");
        assert_eq!(ToastSeverity::Error.label(), "ERR");
    }

    #[test]
    fn toast_severity_icons_by_glyph_set() {
        assert_eq!(ToastSeverity::Info.icon(GlyphSet::Unicode), "ℹ");
        assert_eq!(ToastSeverity::Info.icon(GlyphSet::Ascii), "i");
        assert_eq!(ToastSeverity::Success.icon(GlyphSet::Unicode), "✓");
        assert_eq!(ToastSeverity::Success.icon(GlyphSet::Ascii), "+");
        assert_eq!(ToastSeverity::Warning.icon(GlyphSet::Unicode), "⚠");
        assert_eq!(ToastSeverity::Warning.icon(GlyphSet::Ascii), "!");
        assert_eq!(ToastSeverity::Error.icon(GlyphSet::Unicode), "✗");
        assert_eq!(ToastSeverity::Error.icon(GlyphSet::Ascii), "x");
    }

    #[test]
    fn toast_severity_dismiss_durations() {
        assert_eq!(
            ToastSeverity::Info.default_dismiss_duration(),
            Duration::from_millis(DEFAULT_DISMISS_MS)
        );
        assert_eq!(
            ToastSeverity::Success.default_dismiss_duration(),
            Duration::from_millis(DEFAULT_DISMISS_MS)
        );
        assert_eq!(
            ToastSeverity::Warning.default_dismiss_duration(),
            Duration::from_millis(WARNING_DISMISS_MS)
        );
        assert_eq!(
            ToastSeverity::Error.default_dismiss_duration(),
            Duration::from_millis(ERROR_DISMISS_MS)
        );
    }

    #[test]
    fn toast_center_push_and_active_count() {
        let mut center = ToastCenter::new();
        assert_eq!(center.active_count(), 0);

        center.push(ToastSeverity::Info, "hello");
        assert_eq!(center.active_count(), 1);
        assert_eq!(center.active_toasts()[0].message, "hello");
        assert_eq!(center.active_toasts()[0].severity, ToastSeverity::Info);
    }

    #[test]
    fn toast_center_evicts_oldest_when_at_capacity() {
        let mut center = ToastCenter::new();
        for i in 0..MAX_VISIBLE_TOASTS {
            center.push(ToastSeverity::Info, format!("msg-{i}"));
        }
        assert_eq!(center.active_count(), MAX_VISIBLE_TOASTS);
        assert_eq!(center.history_count(), 0);

        // One more should evict the oldest.
        center.push(ToastSeverity::Warning, "overflow");
        assert_eq!(center.active_count(), MAX_VISIBLE_TOASTS);
        assert_eq!(center.history_count(), 1);
        assert_eq!(center.history()[0].message, "msg-0");
        assert!(center.history()[0].dismissed);
    }

    #[test]
    fn toast_center_tick_dismisses_expired() {
        let mut center = ToastCenter::new();
        center.push_with_duration(ToastSeverity::Info, "ephemeral", Duration::from_millis(0));
        assert_eq!(center.active_count(), 1);

        // Tick should dismiss the zero-duration toast.
        std::thread::sleep(Duration::from_millis(1));
        let changed = center.tick();
        assert!(changed);
        assert_eq!(center.active_count(), 0);
        assert_eq!(center.history_count(), 1);
    }

    #[test]
    fn toast_center_dismiss_latest() {
        let mut center = ToastCenter::new();
        center.push(ToastSeverity::Info, "first");
        center.push(ToastSeverity::Error, "second");
        assert_eq!(center.active_count(), 2);

        let dismissed = center.dismiss_latest();
        assert!(dismissed);
        assert_eq!(center.active_count(), 1);
        assert_eq!(center.active_toasts()[0].message, "first");
        assert_eq!(center.history_count(), 1);
        assert_eq!(center.history()[0].message, "second");
    }

    #[test]
    fn toast_center_dismiss_all() {
        let mut center = ToastCenter::new();
        center.push(ToastSeverity::Info, "a");
        center.push(ToastSeverity::Warning, "b");
        center.push(ToastSeverity::Error, "c");

        center.dismiss_all();
        assert_eq!(center.active_count(), 0);
        assert_eq!(center.history_count(), 3);
    }

    #[test]
    fn toast_center_history_is_bounded() {
        let mut center = ToastCenter::new();
        for i in 0..(TOAST_HISTORY_MAX + 10) {
            center.push_with_duration(
                ToastSeverity::Info,
                format!("msg-{i}"),
                Duration::from_millis(0),
            );
        }
        std::thread::sleep(Duration::from_millis(1));
        center.tick();
        assert!(center.history_count() <= TOAST_HISTORY_MAX);
    }

    #[test]
    fn toast_center_dismiss_latest_on_empty_returns_false() {
        let mut center = ToastCenter::new();
        assert!(!center.dismiss_latest());
    }

    #[test]
    fn toast_center_default_creates_empty() {
        let center = ToastCenter::default();
        assert_eq!(center.active_count(), 0);
        assert_eq!(center.history_count(), 0);
    }

    #[test]
    fn format_toast_inline_truncates_long_message() {
        let colors = Theme::None.colors();
        let mut center = ToastCenter::new();
        center.push(ToastSeverity::Info, "A".repeat(200));
        let toast = &center.active_toasts()[0];
        let formatted = format_toast_inline(toast, &colors, 40);
        // Should not exceed reasonable display width (excluding ANSI codes).
        assert!(formatted.len() < 300);
    }

    #[test]
    fn format_toast_history_overlay_empty_center() {
        let center = ToastCenter::new();
        let output = format_toast_history_overlay(&center, Theme::None, 50);
        assert!(output.contains("No notifications yet"));
        assert!(output.contains("0 total"));
    }

    #[test]
    fn format_toast_history_overlay_with_entries() {
        let mut center = ToastCenter::new();
        center.push(ToastSeverity::Info, "first toast");
        center.push(ToastSeverity::Error, "error toast");
        // Move to history.
        center.dismiss_all();

        let output = format_toast_history_overlay(&center, Theme::None, 60);
        assert!(output.contains("first toast"));
        assert!(output.contains("error toast"));
        assert!(output.contains("2 total"));
    }

    #[test]
    fn toast_history_overlay_rows_match_target_width() {
        let mut center = ToastCenter::new();
        center.push(ToastSeverity::Info, "HUD right panel: recording-only");
        center.push(ToastSeverity::Error, "Theme set: gruvbox");
        center.dismiss_all();

        let width = 60;
        let output = format_toast_history_overlay(&center, Theme::Coral, width);
        assert!(!output.contains('\r'));

        for (idx, line) in output.lines().enumerate() {
            let visible = strip_ansi_sgr(line);
            assert_eq!(
                display_width(&visible),
                width,
                "line {idx} should keep exact overlay width"
            );
        }
    }

    #[test]
    fn toast_history_overlay_height_empty() {
        let center = ToastCenter::new();
        // top + title + 1 content row + footer + bottom = 5
        assert_eq!(toast_history_overlay_height(&center), 5);
    }

    #[test]
    fn toast_history_overlay_height_with_entries() {
        let mut center = ToastCenter::new();
        for i in 0..5 {
            center.push(ToastSeverity::Info, format!("msg-{i}"));
        }
        center.dismiss_all();
        // top + title + 5 content rows + footer + bottom = 9
        assert_eq!(toast_history_overlay_height(&center), 9);
    }

    #[test]
    fn toast_history_overlay_height_caps_at_10_content_rows() {
        let mut center = ToastCenter::new();
        for i in 0..20 {
            center.push_with_duration(
                ToastSeverity::Info,
                format!("msg-{i}"),
                Duration::from_millis(0),
            );
        }
        std::thread::sleep(Duration::from_millis(1));
        center.tick();
        // top + title + 10 content rows + footer + bottom = 14
        assert_eq!(toast_history_overlay_height(&center), 14);
    }

    #[test]
    fn push_with_duration_creates_toast_with_custom_dismiss() {
        let mut center = ToastCenter::new();
        center.push_with_duration(ToastSeverity::Warning, "custom", Duration::from_secs(60));
        assert_eq!(center.active_count(), 1);
        let toast = &center.active_toasts()[0];
        assert_eq!(toast.severity, ToastSeverity::Warning);
        assert_eq!(toast.message, "custom");
        // Should not dismiss for at least a long while.
        assert!(!center.tick());
    }

    #[test]
    fn toast_ids_are_monotonically_increasing() {
        let mut center = ToastCenter::new();
        center.push(ToastSeverity::Info, "a");
        center.push(ToastSeverity::Info, "b");
        center.push(ToastSeverity::Info, "c");
        let ids: Vec<u64> = center.active_toasts().iter().map(|t| t.id).collect();
        assert_eq!(ids, vec![0, 1, 2]);
    }

    #[test]
    fn toast_severity_colors_use_theme() {
        let colors = Theme::Coral.colors();
        assert_eq!(ToastSeverity::Info.color(&colors), colors.info);
        assert_eq!(ToastSeverity::Success.color(&colors), colors.success);
        assert_eq!(ToastSeverity::Warning.color(&colors), colors.warning);
        assert_eq!(ToastSeverity::Error.color(&colors), colors.error);
    }
}
