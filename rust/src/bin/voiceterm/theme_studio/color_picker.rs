//! Terminal-native RGB color picker widget.
//!
//! Renders three slider channels (R, G, B) with a live preview swatch.
//! Used by the Colors page when editing individual semantic color fields.

use crate::theme::color_value::Rgb;

/// Active channel in the color picker.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
pub(crate) enum PickerChannel {
    #[default]
    Red,
    Green,
    Blue,
}

impl PickerChannel {
    /// Move to the next channel (Down arrow).
    #[must_use]
    pub(crate) fn next(self) -> Self {
        match self {
            Self::Red => Self::Green,
            Self::Green => Self::Blue,
            Self::Blue => Self::Red,
        }
    }

    /// Move to the previous channel (Up arrow).
    #[must_use]
    pub(crate) fn prev(self) -> Self {
        match self {
            Self::Red => Self::Blue,
            Self::Green => Self::Red,
            Self::Blue => Self::Green,
        }
    }
}

/// State for the inline color picker widget.
#[derive(Debug, Clone, PartialEq, Eq)]
pub(crate) struct ColorPickerState {
    pub(crate) rgb: Rgb,
    pub(crate) channel: PickerChannel,
    pub(crate) hex_entry_mode: bool,
    pub(crate) hex_buffer: String,
}

impl ColorPickerState {
    /// Create a new color picker initialized to the given color.
    #[must_use]
    pub(crate) fn new(rgb: Rgb) -> Self {
        Self {
            rgb,
            channel: PickerChannel::Red,
            hex_entry_mode: false,
            hex_buffer: String::new(),
        }
    }

    /// Adjust the active channel by `delta` (clamped to 0..=255).
    pub(crate) fn adjust_channel(&mut self, delta: i16) {
        let channel_val = match self.channel {
            PickerChannel::Red => &mut self.rgb.r,
            PickerChannel::Green => &mut self.rgb.g,
            PickerChannel::Blue => &mut self.rgb.b,
        };
        let new_val = i16::from(*channel_val) + delta;
        *channel_val = new_val.clamp(0, 255) as u8;
    }

    /// Render the color picker as a multi-line string.
    ///
    /// ```text
    ///  R: [====████████========] 111
    ///  G: [==========████████==] 177
    ///  B: [████████████████████] 255
    ///
    ///  Preview: ████████ sample text
    ///
    ///  Hex: #6fb1ff  [Enter to apply]
    /// ```
    #[must_use]
    pub(crate) fn render(&self, fg_escape: &str, reset: &str) -> Vec<String> {
        let mut lines = Vec::with_capacity(7);

        // Channel sliders.
        lines.push(self.render_channel_line('R', self.rgb.r, PickerChannel::Red, fg_escape, reset));
        lines.push(self.render_channel_line(
            'G',
            self.rgb.g,
            PickerChannel::Green,
            fg_escape,
            reset,
        ));
        lines.push(self.render_channel_line(
            'B',
            self.rgb.b,
            PickerChannel::Blue,
            fg_escape,
            reset,
        ));

        lines.push(String::new());

        // Preview swatch.
        let swatch_escape = self.rgb.to_fg_escape();
        lines.push(format!(
            " Preview: {swatch_escape}████████ sample text{reset}"
        ));

        lines.push(String::new());

        // Hex value.
        if self.hex_entry_mode {
            lines.push(format!(
                " Hex: {}{reset}  [Enter to apply]",
                if self.hex_buffer.is_empty() {
                    "#".to_string()
                } else {
                    self.hex_buffer.clone()
                }
            ));
        } else {
            lines.push(format!(" Hex: {}  [h for hex entry]", self.rgb.to_hex()));
        }

        lines
    }

    fn render_channel_line(
        &self,
        label: char,
        value: u8,
        channel: PickerChannel,
        fg_escape: &str,
        reset: &str,
    ) -> String {
        const SLIDER_WIDTH: usize = 20;
        let filled = (usize::from(value) * SLIDER_WIDTH) / 255;
        let empty = SLIDER_WIDTH - filled;
        let active_marker = if self.channel == channel { ">" } else { " " };

        format!(
            "{active_marker}{label}: [{fg_escape}{}{reset}{}] {:>3}",
            "█".repeat(filled),
            "░".repeat(empty),
            value,
        )
    }

    /// Try to apply the hex buffer as a new color.
    /// Returns `true` if successful.
    pub(crate) fn apply_hex_buffer(&mut self) -> bool {
        if let Some(rgb) = Rgb::from_hex(&self.hex_buffer) {
            self.rgb = rgb;
            self.hex_entry_mode = false;
            self.hex_buffer.clear();
            true
        } else {
            false
        }
    }

    /// Toggle hex entry mode.
    pub(crate) fn toggle_hex_mode(&mut self) {
        self.hex_entry_mode = !self.hex_entry_mode;
        if self.hex_entry_mode {
            self.hex_buffer = "#".to_string();
        } else {
            self.hex_buffer.clear();
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn color_picker_adjust_clamps() {
        let mut picker = ColorPickerState::new(Rgb {
            r: 250,
            g: 5,
            b: 128,
        });

        picker.channel = PickerChannel::Red;
        picker.adjust_channel(10);
        assert_eq!(picker.rgb.r, 255); // clamped

        picker.channel = PickerChannel::Green;
        picker.adjust_channel(-10);
        assert_eq!(picker.rgb.g, 0); // clamped

        picker.channel = PickerChannel::Blue;
        picker.adjust_channel(-1);
        assert_eq!(picker.rgb.b, 127);
    }

    #[test]
    fn color_picker_channel_cycling() {
        let mut ch = PickerChannel::Red;
        ch = ch.next();
        assert_eq!(ch, PickerChannel::Green);
        ch = ch.next();
        assert_eq!(ch, PickerChannel::Blue);
        ch = ch.next();
        assert_eq!(ch, PickerChannel::Red);

        ch = ch.prev();
        assert_eq!(ch, PickerChannel::Blue);
    }

    #[test]
    fn color_picker_render_produces_lines() {
        let picker = ColorPickerState::new(Rgb {
            r: 111,
            g: 177,
            b: 255,
        });
        let lines = picker.render("", "");
        assert_eq!(lines.len(), 7);
        assert!(lines[0].contains("R:"));
        assert!(lines[1].contains("G:"));
        assert!(lines[2].contains("B:"));
        assert!(lines[4].contains("Preview:"));
        assert!(lines[6].contains("Hex:"));
    }

    #[test]
    fn color_picker_hex_entry_roundtrip() {
        let mut picker = ColorPickerState::new(Rgb { r: 0, g: 0, b: 0 });
        picker.toggle_hex_mode();
        assert!(picker.hex_entry_mode);

        picker.hex_buffer = "#ff5500".to_string();
        assert!(picker.apply_hex_buffer());
        assert_eq!(
            picker.rgb,
            Rgb {
                r: 255,
                g: 85,
                b: 0
            }
        );
        assert!(!picker.hex_entry_mode);
    }

    #[test]
    fn color_picker_hex_entry_rejects_invalid() {
        let mut picker = ColorPickerState::new(Rgb {
            r: 100,
            g: 100,
            b: 100,
        });
        picker.hex_entry_mode = true;
        picker.hex_buffer = "#GGHHII".to_string();
        assert!(!picker.apply_hex_buffer());
        assert_eq!(
            picker.rgb,
            Rgb {
                r: 100,
                g: 100,
                b: 100
            }
        ); // unchanged
    }
}
