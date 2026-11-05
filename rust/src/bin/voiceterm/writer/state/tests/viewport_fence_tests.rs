use super::*;
use crate::test_env::{with_env_overrides, TERMINAL_HOST_ENV_KEYS};

// Field-evidence regression test; see the commit message for the background.
fn fenced_state(host: TerminalHost) -> WriterState {
    // Capturing writer with a full HUD on a 32-row host
    let mut state = WriterState::with_capture_for_tests(host, BackendFamily::Claude);
    state.rows = 32;
    state.cols = 100;
    let mut status = StatusLineState::new();
    status.hud_style = HudStyle::Full;
    state.display.enhanced_status = Some(status);
    state
}

fn viewport_bottom() -> u16 {
    crate::terminal::child_viewport_rows_for_banner(32, 100, HudStyle::Full, false)
}

const JETBRAINS_ENV: &[(&str, Option<&str>)] = &[
    ("TERMINAL_EMULATOR", Some("JetBrains-JediTerm")),
    ("VOICETERM_BACKEND_LABEL", Some("claude")),
];
const PLAIN_ENV: &[(&str, Option<&str>)] = &[("VOICETERM_BACKEND_LABEL", Some("claude"))];

/// One environment override (one lock) that pins both the terminal host and the
/// backend label the viewport computation reads.
fn with_fence_env<T>(pairs: &[(&str, Option<&str>)], f: impl FnOnce() -> T) -> T {
    let mut keys = TERMINAL_HOST_ENV_KEYS.to_vec();
    keys.push("VOICETERM_BACKEND_LABEL");
    with_env_overrides(&keys, pairs, f)
}

#[test]
fn newline_on_the_viewport_bottom_scrolls_only_the_viewport_on_jetbrains() {
    with_fence_env(JETBRAINS_ENV, || {
        {
            let mut state = fenced_state(TerminalHost::JetBrains);
            let bottom = viewport_bottom();

            // The child prints on the last row of its viewport
            let last_row = format!("\x1b[{bottom};1Hlast line of the viewport");
            assert!(state.handle_message(WriterMessage::PtyOutput(last_row.into_bytes())));
            let before = state.captured_output().len();

            // The child emits a newline there (the PTY already added the CR)
            let delivered = state.handle_message(WriterMessage::PtyOutput(b"\r\n".to_vec()));

            // Require the writer to have accepted the chunk
            assert!(delivered);

            // Require a viewport-only scroll instead of a raw line feed
            let host = &state.captured_output()[before..];
            let delete_top = b"\x1b[1;1H\x1b[M".as_slice();
            let insert_at_bottom = format!("\x1b[{};1H\x1b[L", bottom).into_bytes();
            assert!(
                !host.contains(&b'\n')
                    && host.windows(delete_top.len()).any(|w| w == delete_top)
                    && host.windows(insert_at_bottom.len()).any(|w| w == insert_at_bottom.as_slice()),
                "a newline on the viewport bottom must reach the host as a viewport-only scroll (delete row 1, insert row {}), got {:?}",
                bottom,
                String::from_utf8_lossy(host)
            );
        }
    });
}

#[test]
fn newline_above_the_viewport_bottom_passes_through_on_jetbrains() {
    with_fence_env(JETBRAINS_ENV, || {
        {
            let mut state = fenced_state(TerminalHost::JetBrains);
            let bottom = viewport_bottom();

            // The child prints one row above its viewport bottom
            let row = format!("\x1b[{};1Hnot the last row", bottom - 1);
            assert!(state.handle_message(WriterMessage::PtyOutput(row.into_bytes())));
            let before = state.captured_output().len();

            // The child emits a newline there
            let delivered = state.handle_message(WriterMessage::PtyOutput(b"\r\n".to_vec()));

            // Require the writer to have accepted the chunk
            assert!(delivered);

            // Require the newline forwarded verbatim with no line edits
            let host = &state.captured_output()[before..];
            assert!(
                host.ends_with(b"\r\n") && !host.windows(3).any(|w| w == b"\x1b[M"),
                "a newline above the bottom must pass through untouched, got {:?}",
                String::from_utf8_lossy(host)
            );
        }
    });
}

#[test]
fn newline_on_the_viewport_bottom_passes_through_where_a_real_region_exists() {
    with_fence_env(PLAIN_ENV, || {
        {
            let mut state = fenced_state(TerminalHost::Other);
            let bottom = viewport_bottom();

            // A VS Code-like host where the writer sets a real scroll region
            let last_row = format!("\x1b[{bottom};1Hlast line of the viewport");
            assert!(state.handle_message(WriterMessage::PtyOutput(last_row.into_bytes())));
            let before = state.captured_output().len();

            // The child emits a newline on its bottom row
            let delivered = state.handle_message(WriterMessage::PtyOutput(b"\r\n".to_vec()));

            // Require the writer to have accepted the chunk
            assert!(delivered);

            // Require the newline forwarded verbatim
            let host = &state.captured_output()[before..];
            assert!(
                host.ends_with(b"\r\n") && !host.windows(3).any(|w| w == b"\x1b[M"),
                "with a real region the terminal scrolls correctly on its own; got {:?}",
                String::from_utf8_lossy(host)
            );
        }
    });
}
