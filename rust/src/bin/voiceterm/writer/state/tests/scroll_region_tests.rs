use super::*;
use std::time::Duration;

// Field evidence 2026-11-04 (VS Code and JetBrains, Codex 0.166): Codex pins its
// composer by declaring a small scroll region (CSI 1;22 r) around its history
// scrolls. A HUD repaint reset the host region to the whole child viewport, so
// Codex's next scroll moved the entire viewport and ran over its own composer;
// only a resize (which makes Codex redeclare) repaired the screen.

fn vscode_codex_state() -> WriterState {
    let mut state = WriterState::with_capture_for_tests(TerminalHost::Other, BackendFamily::Codex);
    state.rows = 24;
    state.cols = 80;
    let mut status = StatusLineState::new();
    status.hud_style = HudStyle::Full;
    state.display.enhanced_status = Some(status);
    state
}

fn force_full_hud_repaint(state: &mut WriterState) -> usize {
    let before = state.captured_output().len();
    state.needs_redraw = true;
    state.display.force_full_banner_redraw = true;
    state.last_output_at = Instant::now() - Duration::from_secs(2);
    state.last_status_draw_at = Instant::now() - Duration::from_secs(2);
    state.maybe_redraw_status();
    before
}

/// Every DECSTBM (CSI Ps ; Ps r) command in `bytes`, in order.
fn scroll_region_commands(bytes: &[u8]) -> Vec<String> {
    let text = String::from_utf8_lossy(bytes).into_owned();
    let mut out = Vec::new();
    let mut rest = text.as_str();
    while let Some(start) = rest.find("\x1b[") {
        let tail = &rest[start + 2..];
        match tail.find(|c: char| !(c.is_ascii_digit() || c == ';')) {
            Some(end) if tail[end..].starts_with('r') => {
                out.push(format!("\x1b[{}r", &tail[..end]));
                rest = &tail[end + 1..];
            }
            Some(end) => rest = &tail[end..],
            None => break,
        }
    }
    out
}

fn painted_region_after_repaint(state: &mut WriterState) -> (String, Vec<String>) {
    let before = force_full_hud_repaint(state);
    let painted = &state.captured_output()[before..];
    (
        String::from_utf8_lossy(painted).into_owned(),
        scroll_region_commands(painted),
    )
}

#[test]
fn hud_repaint_keeps_the_child_declared_scroll_region() {
    with_backend_label_env(Some("codex"), || {
        let mut state = vscode_codex_state();
        // The child declares rows 1..10 as its scrolling area.
        assert!(state.handle_message(WriterMessage::PtyOutput(b"\x1b[1;10r".to_vec())));

        let (painted, regions) = painted_region_after_repaint(&mut state);

        assert!(
            painted.contains("\x1b[21;1H"),
            "the HUD was not repainted: {painted:?}"
        );
        assert_eq!(
            regions.last().map(String::as_str),
            Some("\x1b[1;10r"),
            "a HUD repaint must leave the child's declared scroll region in force; got {regions:?}"
        );
    });
}

#[test]
fn hud_repaint_keeps_a_child_region_declared_across_two_chunks() {
    with_backend_label_env(Some("codex"), || {
        let mut state = vscode_codex_state();
        // The same declaration, split by the PTY read boundary.
        assert!(state.handle_message(WriterMessage::PtyOutput(b"\x1b[1;".to_vec())));
        assert!(state.handle_message(WriterMessage::PtyOutput(b"10r".to_vec())));

        let (_, regions) = painted_region_after_repaint(&mut state);

        assert_eq!(
            regions.last().map(String::as_str),
            Some("\x1b[1;10r"),
            "a declaration split across chunks must still be honored; got {regions:?}"
        );
    });
}

#[test]
fn hud_repaint_imposes_the_child_viewport_after_the_child_resets_its_region() {
    // CSI r means "the whole screen" to the child, and the whole screen the
    // child believes in is its viewport, rows 1..20 here.
    with_backend_label_env(Some("codex"), || {
        let mut state = vscode_codex_state();
        assert!(state.handle_message(WriterMessage::PtyOutput(b"\x1b[1;10r".to_vec())));
        assert!(state.handle_message(WriterMessage::PtyOutput(b"\x1b[r".to_vec())));

        let (_, regions) = painted_region_after_repaint(&mut state);

        assert_eq!(
            regions.last().map(String::as_str),
            Some("\x1b[1;20r"),
            "after a reset the HUD paint must confine scrolling to the child viewport; got {regions:?}"
        );
    });
}

#[test]
fn hud_repaint_clamps_a_child_region_that_exceeds_the_viewport() {
    // A stale declaration from before a shrink must never let the region
    // cover the HUD rows.
    with_backend_label_env(Some("codex"), || {
        let mut state = vscode_codex_state();
        assert!(state.handle_message(WriterMessage::PtyOutput(b"\x1b[1;30r".to_vec())));

        let (_, regions) = painted_region_after_repaint(&mut state);

        assert_eq!(
            regions.last().map(String::as_str),
            Some("\x1b[1;20r"),
            "a declared bottom beyond the viewport must be clamped to it; got {regions:?}"
        );
    });
}
