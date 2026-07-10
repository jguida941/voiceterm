//! Clipboard operations for the dev-panel handoff prompt.

use super::super::*;

/// Copy the fresh-conversation prompt from the Handoff snapshot to the system
/// clipboard via OSC 52. This is a read-side affordance — no files modified.
pub(in super::super) fn copy_handoff_prompt_to_clipboard(
    state: &mut EventLoopState,
    timers: &mut EventLoopTimers,
    deps: &EventLoopDeps,
) {
    let prompt = state
        .dev_panel_commands
        .handoff_snapshot()
        .map(|s| s.fresh_prompt.as_str())
        .unwrap_or("");

    if prompt.is_empty() {
        super::set_dev_status(
            state,
            timers,
            deps,
            "No prompt to copy — press Enter to refresh first",
            Some(Duration::from_secs(2)),
        );
        return;
    }

    // Route OSC 52 through the shared writer so clipboard escapes stay ordered
    // with overlays, HUD redraws, and other terminal output.
    let _ = deps
        .writer_tx
        .send(crate::writer::WriterMessage::TerminalBytes(
            crate::writer::osc52_copy_bytes(prompt),
        ));

    super::set_dev_status(
        state,
        timers,
        deps,
        "Prompt copied to clipboard (OSC 52)",
        Some(Duration::from_secs(2)),
    );
}

#[cfg(test)]
mod clipboard_tests {
    #[test]
    fn osc52_copy_bytes_roundtrip() {
        let encoded = crate::writer::osc52_copy_bytes("Hello, clipboard!");
        assert_eq!(encoded, b"\x1b]52;c;SGVsbG8sIGNsaXBib2FyZCE=\x07");
    }

    #[test]
    fn osc52_copy_bytes_handles_empty_payload() {
        let encoded = crate::writer::osc52_copy_bytes("");
        assert_eq!(encoded, b"\x1b]52;c;\x07");
    }
}
