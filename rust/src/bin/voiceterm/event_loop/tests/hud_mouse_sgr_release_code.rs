//! PyCharm-style hover reports (SGR code 3, uppercase M) must never act as a click.

use super::*;
use crate::input::InputParser;

// PyCharm 2024.3 encodes pointer motion as SGR button code 3 with the uppercase
// M final; that report over [set] must leave the HUD alone while a real press
// still opens Settings.
#[test]
fn hud_ignores_sgr_release_code_hover_over_settings_button() {
    // Event loop state with a live PTY child
    let (mut state, mut timers, mut deps, _writer_rx, _input_tx) = build_harness("cat", &[], 64);
    let cols = state.ui.terminal_cols as usize;
    let rows = state.ui.terminal_rows;

    // Locate the settings button on the live HUD geometry
    let settings = crate::status_line::get_button_positions(&state.status_state, state.theme, cols)
        .into_iter()
        .find(|pos| pos.action == ButtonAction::SettingsToggle)
        .expect("settings button is visible on the full HUD");
    let x = settings.start_x;
    let y = rows.saturating_sub(settings.row).saturating_add(1);

    // Require no overlay before any pointer input
    assert_eq!(state.ui.overlay_mode, OverlayMode::None);

    // SGR code 3 uppercase M report over the settings button
    let hover = format!("\x1b[<3;{x};{y}M");
    let mut parser = InputParser::new();
    let mut events = Vec::new();
    parser.consume_bytes(hover.as_bytes(), &mut events);
    parser.flush_pending(&mut events);

    // Dispatch every event the parser emitted for the hover report
    let mut running = true;
    for event in events {
        handle_input_event(&mut state, &mut timers, &mut deps, event, &mut running);
    }

    // Require the HUD untouched by the code 3 hover report
    assert!(
        running && state.ui.overlay_mode == OverlayMode::None,
        "code-3 hover over [set] changed the HUD: overlay={:?}, running={running}",
        state.ui.overlay_mode
    );

    // SGR left press (cb 0) at the same coordinates
    let press = format!("\x1b[<0;{x};{y}M");
    let mut control_events = Vec::new();
    parser.consume_bytes(press.as_bytes(), &mut control_events);
    parser.flush_pending(&mut control_events);

    // Dispatch the control press through the event loop
    for event in control_events {
        handle_input_event(&mut state, &mut timers, &mut deps, event, &mut running);
    }

    // Require a real press to still open settings
    assert_eq!(state.ui.overlay_mode, OverlayMode::Settings);
    assert!(running);
}
