//! Status-line module wiring that keeps multi-row HUD formatting composable.
//!
//! Provides a structured status line with mode indicator, pipeline tag,
//! sensitivity level, status message, and keyboard shortcuts.
//!
//! Now supports a multi-row banner layout with themed borders.
//! Buttons are clickable - click positions are tracked for mouse interaction.

mod animation;
mod buttons;
mod format;
mod layout;
mod right_panel;
mod state;
mod text;

pub use buttons::get_button_positions;
pub use format::format_status_banner;
#[cfg(test)]
pub use layout::status_banner_height;
pub use layout::{status_banner_height_for_state, status_banner_height_with_policy};
pub use state::{
    Pipeline, RecordingState, StatusBanner, StatusLineState, VoiceMode, WakeWordHudState,
    METER_HISTORY_MAX,
};
