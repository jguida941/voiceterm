//! Mouse-tracking escape-sequence controls so HUD click handling is explicit.

use std::io::Write;
use voiceterm::log_debug;

// SGR mouse mode escape sequences
// Enable basic mouse reporting + SGR extended coordinates
const MOUSE_ENABLE: &[u8] = b"\x1b[?1000h\x1b[?1006h";
// Disable mouse reporting
const MOUSE_DISABLE: &[u8] = b"\x1b[?1006l\x1b[?1000l";

/// Enable SGR mouse tracking for clickable buttons.
pub(super) fn enable_mouse(stdout: &mut dyn Write, mouse_enabled: &mut bool) {
    if !*mouse_enabled {
        if let Err(err) = stdout.write_all(MOUSE_ENABLE) {
            log_debug(&format!("mouse enable failed: {err}"));
        }
        let _ = stdout.flush();
        *mouse_enabled = true;
    }
}

/// Disable mouse tracking.
pub(super) fn disable_mouse(stdout: &mut dyn Write, mouse_enabled: &mut bool) {
    if *mouse_enabled {
        if let Err(err) = stdout.write_all(MOUSE_DISABLE) {
            log_debug(&format!("mouse disable failed: {err}"));
        }
        let _ = stdout.flush();
        *mouse_enabled = false;
    }
}

pub(super) const fn mouse_enable_sequence_len() -> usize {
    MOUSE_ENABLE.len()
}

pub(super) fn append_mouse_enable_sequence(sequence: &mut Vec<u8>) {
    sequence.extend_from_slice(MOUSE_ENABLE);
}

fn is_mouse_mode_param(value: u16) -> bool {
    matches!(value, 1000 | 1006)
}

pub(super) fn pty_chunk_disables_mouse_tracking(bytes: &[u8]) -> bool {
    let mut idx = 0;
    while idx + 3 < bytes.len() {
        if bytes[idx] == 0x1b && bytes[idx + 1] == b'[' && bytes[idx + 2] == b'?' {
            let mut cursor = idx + 3;
            let mut saw_digit = false;
            let mut value: u16 = 0;
            let mut saw_mouse_param = false;
            while cursor < bytes.len() {
                match bytes[cursor] {
                    b'0'..=b'9' => {
                        saw_digit = true;
                        let digit = (bytes[cursor] - b'0') as u16;
                        value = value.saturating_mul(10).saturating_add(digit);
                        cursor += 1;
                    }
                    b';' => {
                        if saw_digit {
                            if is_mouse_mode_param(value) {
                                saw_mouse_param = true;
                            }
                            value = 0;
                            saw_digit = false;
                        }
                        cursor += 1;
                    }
                    final_byte => {
                        if saw_digit && is_mouse_mode_param(value) {
                            saw_mouse_param = true;
                        }
                        if final_byte == b'l' && saw_mouse_param {
                            return true;
                        }
                        break;
                    }
                }
            }
            idx = cursor.saturating_add(1);
            continue;
        }
        idx += 1;
    }
    false
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn pty_chunk_detects_simple_mouse_disable_sequences() {
        assert!(pty_chunk_disables_mouse_tracking(b"\x1b[?1000l"));
        assert!(pty_chunk_disables_mouse_tracking(b"\x1b[?1006l"));
    }

    #[test]
    fn pty_chunk_detects_combined_private_mode_disable_sequence() {
        assert!(pty_chunk_disables_mouse_tracking(
            b"\x1b[?25l\x1b[?1000;1002;1006l"
        ));
    }

    #[test]
    fn pty_chunk_ignores_enable_or_non_mouse_sequences() {
        assert!(!pty_chunk_disables_mouse_tracking(
            b"\x1b[?1000h\x1b[?1006h"
        ));
        assert!(!pty_chunk_disables_mouse_tracking(b"\x1b[?25l"));
        assert!(!pty_chunk_disables_mouse_tracking(b"\x1b[31m"));
    }

    #[test]
    fn pty_chunk_ignores_incomplete_private_mode_sequences() {
        assert!(!pty_chunk_disables_mouse_tracking(b"\x1b[?1000"));
        assert!(!pty_chunk_disables_mouse_tracking(b"\x1b[?1000;1006"));
    }

    #[test]
    fn append_mouse_enable_sequence_appends_expected_bytes() {
        let mut sequence = b"abc".to_vec();
        append_mouse_enable_sequence(&mut sequence);
        assert_eq!(sequence, b"abc\x1b[?1000h\x1b[?1006h");
    }
}
