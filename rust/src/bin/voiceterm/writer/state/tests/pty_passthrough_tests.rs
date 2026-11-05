use super::*;
use std::time::Duration;

// Field bug (VS Code + Claude): replacement glyphs appeared inside a box-drawing
// rule of Claude's composer border. The PTY reader forwards raw read() chunks, so
// a multibyte character can straddle two chunks; a HUD repaint written between
// them corrupts that character on the host terminal.
fn vscode_claude_state() -> WriterState {
    // Capturing writer for a VS code-like host with claude
    let mut state = WriterState::with_capture_for_tests(TerminalHost::Other, BackendFamily::Claude);
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

#[test]
fn hud_repaint_never_splits_a_multibyte_character_from_the_child() {
    with_backend_label_env(Some("claude"), || {
        let mut state = vscode_claude_state();

        // Two of the three bytes of U+2500 arrive first
        assert!(state.handle_message(WriterMessage::PtyOutput(b"rule: \xe2\x94".to_vec())));

        // Force a full HUD repaint while the character is incomplete
        let before = force_full_hud_repaint(&mut state);

        // Require the repaint to have emitted bytes
        assert!(
            state.captured_output().len() > before,
            "the repaint must have emitted bytes for this test to mean anything"
        );

        // Deliver the final byte and the rest of the line
        let delivered = state.handle_message(WriterMessage::PtyOutput(b"\x80 end".to_vec()));

        // Require the writer to have accepted the final chunk
        assert!(
            delivered,
            "the writer must keep running after the final chunk"
        );

        // Require the child character whole right before its trailing text
        // Judged on the child's own character, not the HUD border drawn with the
        // same glyph: the three bytes before the child's " end" must be U+2500.
        let out = state.captured_output();
        let end = out
            .windows(4)
            .position(|w| w == b" end")
            .expect("the child's trailing text must be written");
        assert_eq!(
            &out[end - 3..end],
            b"\xe2\x94\x80",
            "the child's multibyte character must reach the host terminal whole, never with HUD bytes inside it: {:?}",
            String::from_utf8_lossy(&out[end.saturating_sub(40)..end + 4])
        );
    });
}

#[test]
fn complete_child_output_is_written_before_the_repaint_unchanged() {
    with_backend_label_env(Some("claude"), || {
        let mut state = vscode_claude_state();

        // A complete line of child output
        assert!(state.handle_message(WriterMessage::PtyOutput(
            "rule: \u{2500} end".as_bytes().to_vec()
        )));
        let before = state.captured_output().len();

        // Force a full HUD repaint
        force_full_hud_repaint(&mut state);

        // Require the line written immediately and verbatim, then a repaint
        let out = state.captured_output();
        assert!(
            out[..before].ends_with("rule: \u{2500} end".as_bytes()),
            "complete child output must be written immediately and verbatim: {:?}",
            String::from_utf8_lossy(&out[..before])
        );
        assert!(out.len() > before, "the repaint must still happen");
    });
}
