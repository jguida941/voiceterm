//! Settings overlay wiring so menu rendering and actions evolve together.

mod items;
mod render;
mod state;

pub use items::{
    settings_overlay_footer, settings_overlay_height, settings_overlay_inner_width_for_terminal,
    settings_overlay_width_for_terminal, SettingsItem, SettingsView, SETTINGS_ITEMS,
    SETTINGS_OPTION_START_ROW,
};
pub use render::format_settings_overlay;
pub use state::SettingsMenuState;
