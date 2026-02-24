//! Overlay configuration assembly so CLI flags and backend defaults resolve consistently.

mod backend;
mod cli;
mod theme;
mod util;

pub(crate) use cli::{
    HudBorderStyle, HudRightPanel, HudStyle, LatencyDisplayMode, OverlayConfig, VoiceSendMode,
    DEFAULT_WAKE_WORD_COOLDOWN_MS, DEFAULT_WAKE_WORD_SENSITIVITY, MAX_WAKE_WORD_COOLDOWN_MS,
    MIN_WAKE_WORD_COOLDOWN_MS,
};
