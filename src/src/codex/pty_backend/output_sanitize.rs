use strip_ansi_escapes::strip;

/// Normalize CR/LF pairs, strip ANSI, and guarantee clean UTF-8 suitable for the TUI.
pub fn sanitize_pty_output(raw: &[u8]) -> String {
    if raw.is_empty() {
        return String::new();
    }

    let normalized = normalize_control_bytes(raw);
    let ansi_free = strip(&normalized);
    let mut text = String::from_utf8_lossy(&ansi_free).to_string();
    if raw.last() == Some(&b'\n') && !text.ends_with('\n') {
        text.push('\n');
    }
    text
}

/// Split normalized text into UI-ready lines for terminal rendering.
pub fn prepare_for_display(text: &str) -> Vec<String> {
    text.lines().map(|line| line.to_string()).collect()
}

pub(in crate::codex) fn normalize_control_bytes(raw: &[u8]) -> Vec<u8> {
    let mut output = Vec::with_capacity(raw.len());
    let mut idx = 0;
    let mut line_start = 0usize;
    let mut guard = init_guard(raw.len());

    while idx < raw.len() {
        if !step_guard(&mut guard) {
            break;
        }
        match raw[idx] {
            b'\r' => {
                if raw.get(idx + 1) == Some(&b'\n') {
                    output.push(b'\n');
                    idx += 2;
                    line_start = output.len();
                    continue;
                }
                output.truncate(line_start);
                idx += 1;
            }
            b'\n' => {
                output.push(b'\n');
                idx += 1;
                line_start = output.len();
            }
            b'\x08' => {
                idx += 1;
                let removed_newline = pop_last_codepoint(&mut output);
                if removed_newline {
                    line_start = current_line_start(&output);
                }
            }
            0 => {
                idx += 1;
            }
            0x1B => {
                if let Some(next) = raw.get(idx + 1) {
                    if *next == b']' {
                        // Skip OSC sequences entirely.
                        idx = skip_osc_sequence(raw, idx + 2);
                        continue;
                    } else if *next == b'[' {
                        // Skip all CSI sequences; strip control escapes from rendered text.
                        if let Some((end, _final_byte)) = find_csi_sequence(raw, idx) {
                            idx = end + 1;
                            continue;
                        }
                    } else if *next == b'(' || *next == b')' {
                        // Skip character set designation sequences (ESC ( or ESC )).
                        idx += 3;
                        continue;
                    } else if *next == b'>' || *next == b'=' {
                        // Skip keypad mode sequences.
                        idx += 2;
                        continue;
                    }
                }
                output.push(raw[idx]);
                idx += 1;
            }
            byte => {
                output.push(byte);
                idx += 1;
            }
        }
        line_start = clamp_line_start(line_start, &output);
    }

    output
}

pub(in crate::codex) fn init_guard(len: usize) -> usize {
    len.saturating_mul(4).max(16)
}

pub(in crate::codex) fn step_guard(guard: &mut usize) -> bool {
    if *guard == 0 {
        return false;
    }
    *guard -= 1;
    true
}

pub(in crate::codex) fn pop_last_codepoint(buf: &mut Vec<u8>) -> bool {
    if buf.is_empty() {
        return false;
    }
    if buf.last() == Some(&b'\n') {
        buf.pop();
        return true;
    }
    while let Some(byte) = buf.pop() {
        if (byte & 0b1100_0000) != 0b1000_0000 {
            break;
        }
    }
    false
}

pub(in crate::codex) fn current_line_start(buf: &[u8]) -> usize {
    buf.iter()
        .rposition(|&b| b == b'\n')
        .map(|pos| pos + 1)
        .unwrap_or(0)
}

pub(in crate::codex) fn clamp_line_start(line_start: usize, buf: &[u8]) -> usize {
    if line_start > buf.len() {
        current_line_start(buf)
    } else {
        line_start
    }
}

pub(in crate::codex) fn skip_osc_sequence(bytes: &[u8], mut cursor: usize) -> usize {
    while cursor < bytes.len() {
        match bytes[cursor] {
            0x07 => return cursor + 1,
            0x1B if cursor + 1 < bytes.len() && bytes[cursor + 1] == b'\\' => {
                return cursor + 2;
            }
            _ => {}
        }
        cursor += 1;
    }
    cursor
}

pub(in crate::codex) fn find_csi_sequence(bytes: &[u8], start: usize) -> Option<(usize, u8)> {
    if bytes.get(start)? != &0x1B || bytes.get(start + 1)? != &b'[' {
        return None;
    }
    for (idx, b) in bytes.iter().enumerate().skip(start + 2) {
        if (0x40..=0x7E).contains(b) {
            return Some((idx, *b));
        }
    }
    None
}
