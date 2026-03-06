const CLAUDE_LONG_THINK_STATUS_MARKERS: &[&[u8]] = &[
    b"baked for ",
    b"brewed for ",
    b"churned for ",
    b"cogitated for ",
    b"cooked for ",
    b"crunched for ",
    b"worked for ",
    b"simmered for ",
    b"sauteed for ",
    b"toasted for ",
    b"marinated for ",
    b"whisked for ",
    b"boondoggling",
    b"waddling",
    b"hashing",
    b"metamorphosing",
    b"enchanting",
    b"ruminating",
    b"evaporating",
];

pub(super) fn pty_output_can_mutate_cursor_line(bytes: &[u8]) -> bool {
    if bytes.iter().any(|byte| matches!(byte, b'\r' | 0x08 | 0x7f)) {
        return true;
    }
    contains_cursor_mutation_csi(bytes)
}

fn csi_param_contains_token(params: &[u8], token: u8) -> bool {
    if params.is_empty() {
        return false;
    }
    let mut start = 0usize;
    while start < params.len() {
        let mut end = start;
        while end < params.len() && params[end] != b';' {
            end += 1;
        }
        let slice = &params[start..end];
        if slice.len() == 1 && slice[0] == token {
            return true;
        }
        start = end.saturating_add(1);
    }
    false
}

pub(super) fn pty_output_contains_destructive_clear(bytes: &[u8]) -> bool {
    let mut idx = 0usize;
    while idx + 1 < bytes.len() {
        if bytes[idx] != 0x1b {
            idx += 1;
            continue;
        }
        let next = bytes[idx + 1];
        if next == b'c' {
            // RIS (ESC c) resets terminal state and clears visible content.
            return true;
        }
        if next != b'[' {
            idx += 2;
            continue;
        }
        let mut cursor = idx + 2;
        while cursor < bytes.len() {
            let byte = bytes[cursor];
            if (0x40..=0x7e).contains(&byte) {
                if byte == b'J' {
                    let params = &bytes[idx + 2..cursor];
                    if csi_param_contains_token(params, b'2')
                        || csi_param_contains_token(params, b'3')
                    {
                        return true;
                    }
                }
                idx = cursor + 1;
                break;
            }
            cursor += 1;
        }
        if cursor >= bytes.len() {
            break;
        }
    }
    false
}

pub(super) fn pty_output_contains_erase_display(bytes: &[u8]) -> bool {
    let mut idx = 0usize;
    while idx + 1 < bytes.len() {
        if bytes[idx] != 0x1b || bytes[idx + 1] != b'[' {
            idx += 1;
            continue;
        }
        let mut cursor = idx + 2;
        while cursor < bytes.len() {
            let byte = bytes[cursor];
            if (0x40..=0x7e).contains(&byte) {
                if byte == b'J' {
                    return true;
                }
                idx = cursor + 1;
                break;
            }
            cursor += 1;
        }
        if cursor >= bytes.len() {
            break;
        }
    }
    false
}

fn contains_cursor_mutation_csi(bytes: &[u8]) -> bool {
    let mut idx = 0usize;
    while idx + 2 < bytes.len() {
        if bytes[idx] != 0x1b || bytes[idx + 1] != b'[' {
            idx += 1;
            continue;
        }
        let mut cursor = idx + 2;
        while cursor < bytes.len() {
            let byte = bytes[cursor];
            if (0x40..=0x7e).contains(&byte) {
                return matches!(
                    byte,
                    b'A' | b'B'
                        | b'C'
                        | b'D'
                        | b'E'
                        | b'F'
                        | b'G'
                        | b'H'
                        | b'f'
                        | b'd'
                        | b'J'
                        | b'K'
                        | b's'
                        | b'u'
                );
            }
            cursor += 1;
        }
        // Truncated CSI sequence: defer until next chunk.
        return false;
    }
    false
}

fn bytes_contains_sequence(bytes: &[u8], needle: &[u8]) -> bool {
    !needle.is_empty()
        && bytes.len() >= needle.len()
        && bytes.windows(needle.len()).any(|window| window == needle)
}

fn bytes_contains_sequence_ascii_case_insensitive(bytes: &[u8], needle: &[u8]) -> bool {
    !needle.is_empty()
        && bytes.len() >= needle.len()
        && bytes
            .windows(needle.len())
            .any(|window| window.eq_ignore_ascii_case(needle))
}

fn bytes_contains_any_ascii_case_insensitive(bytes: &[u8], needles: &[&[u8]]) -> bool {
    needles
        .iter()
        .any(|needle| bytes_contains_sequence_ascii_case_insensitive(bytes, needle))
}

fn parse_single_csi_param_u16(params: &[u8]) -> Option<u16> {
    if params.is_empty() {
        return Some(1);
    }
    if params.contains(&b';') {
        return None;
    }
    let mut value: u16 = 0;
    for &byte in params {
        if !byte.is_ascii_digit() {
            return None;
        }
        value = value
            .saturating_mul(10)
            .saturating_add((byte - b'0') as u16);
    }
    if value == 0 {
        Some(1)
    } else {
        Some(value)
    }
}

pub(super) fn bytes_contains_short_cursor_up_csi(bytes: &[u8]) -> bool {
    bytes_contains_cursor_up_csi_at_least(bytes, 1, Some(3))
}

fn bytes_contains_cursor_up_csi_at_least(
    bytes: &[u8],
    min_rows: u16,
    max_rows: Option<u16>,
) -> bool {
    let mut idx = 0usize;
    while idx + 2 < bytes.len() {
        if bytes[idx] != 0x1b || bytes[idx + 1] != b'[' {
            idx += 1;
            continue;
        }
        let mut cursor = idx + 2;
        while cursor < bytes.len() {
            let byte = bytes[cursor];
            if (0x40..=0x7e).contains(&byte) {
                if byte == b'A' {
                    let params = &bytes[idx + 2..cursor];
                    if let Some(rows_up) = parse_single_csi_param_u16(params) {
                        let within_max = max_rows.is_none_or(|max| rows_up <= max);
                        if rows_up >= min_rows && within_max {
                            return true;
                        }
                    }
                }
                idx = cursor + 1;
                break;
            }
            cursor += 1;
        }
        if cursor >= bytes.len() {
            break;
        }
    }
    false
}

pub(super) fn chunk_looks_like_claude_composer_keystroke(bytes: &[u8]) -> bool {
    if bytes.len() < 24 {
        return false;
    }
    // Claude composer updates in JetBrains arrive as synchronized-output
    // packets and include short cursor-up edits (typically 1A/2A/3A). Long
    // wrapped-input packets can exceed 512 bytes and use several variants, so
    // avoid matching a single exact shape.
    let synchronized_packet = bytes_contains_sequence(bytes, b"\x1b[?2026h")
        && bytes_contains_sequence(bytes, b"\x1b[?2026l");
    if !synchronized_packet {
        return false;
    }
    let has_short_cursor_up = bytes_contains_short_cursor_up_csi(bytes);
    let has_inverse_cursor_marker =
        bytes_contains_sequence(bytes, b"\x1b[7m") && bytes_contains_sequence(bytes, b"\x1b[27m");
    let has_inline_line_erase = bytes_contains_sequence(bytes, b"\x1b[2K");
    has_short_cursor_up && (has_inverse_cursor_marker || has_inline_line_erase)
}

pub(super) fn chunk_looks_like_claude_synchronized_cursor_rewrite(bytes: &[u8]) -> bool {
    if bytes.len() < 24 {
        return false;
    }
    let synchronized_packet = bytes_contains_sequence(bytes, b"\x1b[?2026h")
        && bytes_contains_sequence(bytes, b"\x1b[?2026l");
    if !synchronized_packet {
        return false;
    }
    let has_cursor_up = bytes_contains_cursor_up_csi_at_least(bytes, 2, None);
    if !has_cursor_up {
        return false;
    }
    let has_large_cursor_up = bytes_contains_cursor_up_csi_at_least(bytes, 4, None);
    let has_status_text =
        bytes_contains_any_ascii_case_insensitive(
            bytes,
            &[b"(thinking)", b"shortcuts", b"press", b"ctrl+o to expand"],
        ) || bytes_contains_any_ascii_case_insensitive(bytes, CLAUDE_LONG_THINK_STATUS_MARKERS);
    let has_inline_line_erase = bytes_contains_sequence(bytes, b"\x1b[2K");
    has_status_text || (has_large_cursor_up && has_inline_line_erase)
}

pub(super) fn pty_chunk_starts_with_absolute_cursor_position(bytes: &[u8]) -> bool {
    if bytes.is_empty() {
        return false;
    }

    let mut idx = 0usize;
    let mut saw_absolute = false;
    let mut saw_disallowed_before_absolute = false;
    while idx < bytes.len() {
        let byte = bytes[idx];
        if byte == 0x1b {
            if idx + 1 >= bytes.len() {
                return false;
            }
            match bytes[idx + 1] {
                b'[' => {
                    let mut cursor = idx + 2;
                    while cursor < bytes.len() {
                        let final_byte = bytes[cursor];
                        if (0x40..=0x7e).contains(&final_byte) {
                            if matches!(final_byte, b'H' | b'f' | b'd' | b'G') {
                                if saw_disallowed_before_absolute {
                                    return false;
                                }
                                saw_absolute = true;
                                idx = cursor + 1;
                                break;
                            }
                            if !saw_absolute {
                                // Allow style/mode setup before absolute CUP.
                                if !matches!(final_byte, b'm' | b'h' | b'l') {
                                    return false;
                                }
                            }
                            idx = cursor + 1;
                            break;
                        }
                        cursor += 1;
                    }
                    if cursor >= bytes.len() {
                        return false;
                    }
                    continue;
                }
                b']' => {
                    // OSC: skip until BEL or ST (ESC \).
                    let mut cursor = idx + 2;
                    let mut terminated = false;
                    while cursor < bytes.len() {
                        if bytes[cursor] == 0x07 {
                            terminated = true;
                            cursor += 1;
                            break;
                        }
                        if bytes[cursor] == 0x1b
                            && cursor + 1 < bytes.len()
                            && bytes[cursor + 1] == b'\\'
                        {
                            terminated = true;
                            cursor += 2;
                            break;
                        }
                        cursor += 1;
                    }
                    if !terminated {
                        return false;
                    }
                    idx = cursor;
                    continue;
                }
                b'7' | b'8' => {
                    // Disallow DEC save/restore before first absolute move.
                    // If we pre-clear first, Claude's leading DECSC would save
                    // our clear cursor location, then DECRC can jump back into
                    // HUD rows and smear border fragments into transcript.
                    if !saw_absolute {
                        saw_disallowed_before_absolute = true;
                    }
                    idx += 2;
                    continue;
                }
                _ => {
                    idx += 2;
                    continue;
                }
            }
        }

        if byte.is_ascii_control() {
            if byte == b'\0' {
                idx += 1;
                continue;
            }
            // Any non-null control before absolute positioning is unsafe.
            if !saw_absolute {
                return false;
            }
            idx += 1;
            continue;
        }

        // First printable byte must occur after absolute cursor positioning.
        return saw_absolute;
    }
    saw_absolute
}

const CURSOR_TRACKER_MAX_CARRY_BYTES: usize = 256;

pub(super) fn track_cursor_save_restore(
    dec_active: bool,
    ansi_active: bool,
    carry: &[u8],
    bytes: &[u8],
) -> (bool, bool, bool, bool, Vec<u8>) {
    let mut stream = Vec::with_capacity(carry.len() + bytes.len());
    stream.extend_from_slice(carry);
    stream.extend_from_slice(bytes);

    let mut idx = 0usize;
    let mut dec_active_state = dec_active;
    let mut ansi_active_state = ansi_active;
    let mut saw_save = false;
    let mut saw_restore = false;
    let mut carry_start = None;

    while idx < stream.len() {
        if stream[idx] != 0x1b {
            idx += 1;
            continue;
        }

        if idx + 1 >= stream.len() {
            carry_start = Some(idx);
            break;
        }

        let esc_idx = idx;
        match stream[idx + 1] {
            b'7' => {
                dec_active_state = true;
                saw_save = true;
                idx += 2;
            }
            b'8' => {
                dec_active_state = false;
                saw_restore = true;
                idx += 2;
            }
            b'[' => {
                idx += 2;
                let mut saw_final = false;
                while idx < stream.len() {
                    let byte = stream[idx];
                    idx += 1;
                    if (0x40..=0x7e).contains(&byte) {
                        saw_final = true;
                        if byte == b's' {
                            ansi_active_state = true;
                            saw_save = true;
                        } else if byte == b'u' {
                            ansi_active_state = false;
                            saw_restore = true;
                        }
                        break;
                    }
                }
                if !saw_final {
                    carry_start = Some(esc_idx);
                    break;
                }
            }
            b']' => {
                idx += 2;
                let mut terminated = false;
                while idx < stream.len() {
                    if stream[idx] == 0x07 {
                        terminated = true;
                        idx += 1;
                        break;
                    }
                    if stream[idx] == 0x1b && idx + 1 < stream.len() && stream[idx + 1] == b'\\' {
                        terminated = true;
                        idx += 2;
                        break;
                    }
                    idx += 1;
                }
                if !terminated {
                    carry_start = Some(esc_idx);
                    break;
                }
            }
            _ => {
                idx += 2;
            }
        }
    }

    let mut next_carry = carry_start.map_or_else(Vec::new, |start| stream[start..].to_vec());
    if next_carry.len() > CURSOR_TRACKER_MAX_CARRY_BYTES {
        next_carry.truncate(CURSOR_TRACKER_MAX_CARRY_BYTES);
    }

    (
        dec_active_state,
        ansi_active_state,
        saw_save,
        saw_restore,
        next_carry,
    )
}
