//! Shared prompt-occlusion helpers that are provider-neutral.

use std::collections::VecDeque;
use std::time::Instant;

use crate::ansi::strip_ansi_preserve_controls;

pub(crate) fn append_window_chunk(
    window: &mut VecDeque<u8>,
    last_update: &mut Option<Instant>,
    now: Instant,
    data: &[u8],
    stale_window_ms: u64,
    max_bytes: usize,
) {
    if data.is_empty() {
        return;
    }
    if last_update
        .as_ref()
        .is_some_and(|last| now.duration_since(*last).as_millis() > u128::from(stale_window_ms))
    {
        window.clear();
    }
    *last_update = Some(now);
    let normalized = strip_ansi_preserve_controls(data);
    window.extend(normalized);
    while window.len() > max_bytes {
        let _ = window.pop_front();
    }
}

pub(crate) fn clear_window_state(window: &mut VecDeque<u8>, last_update: &mut Option<Instant>) {
    window.clear();
    *last_update = None;
}

pub(crate) fn retain_window_tail(window: &mut VecDeque<u8>, tail_bytes: usize) {
    while window.len() > tail_bytes {
        let _ = window.pop_front();
    }
}

pub(crate) fn window_is_expired(
    last_update: Option<Instant>,
    now: Instant,
    max_age_ms: u64,
) -> bool {
    last_update
        .as_ref()
        .is_some_and(|last| now.duration_since(*last).as_millis() > u128::from(max_age_ms))
}

pub(crate) fn snapshot_window_bytes(window: &VecDeque<u8>) -> Vec<u8> {
    window.iter().copied().collect()
}

pub(crate) fn tail_slice(bytes: &[u8], tail_bytes: usize) -> &[u8] {
    if bytes.len() <= tail_bytes {
        return bytes;
    }
    &bytes[bytes.len().saturating_sub(tail_bytes)..]
}

pub(crate) fn normalize_signal_text(bytes: &[u8]) -> String {
    let mut normalized = String::with_capacity(bytes.len());
    let mut prev_space = false;
    for ch in String::from_utf8_lossy(bytes).chars() {
        let lower = ch.to_ascii_lowercase();
        if lower.is_ascii_alphanumeric() || matches!(lower, ':' | '*' | '/' | '.' | '_' | '-') {
            normalized.push(lower);
            prev_space = false;
            continue;
        }
        if !prev_space {
            normalized.push(' ');
            prev_space = true;
        }
    }
    normalized
}

pub(crate) fn bytes_contains_sequence(bytes: &[u8], needle: &[u8]) -> bool {
    if needle.is_empty() {
        return true;
    }
    bytes.windows(needle.len()).any(|window| window == needle)
}

pub(crate) fn bytes_contains_cursor_up_csi_at_least(bytes: &[u8], min_rows: u16) -> bool {
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
                    if parse_single_csi_param_u16(params).is_some_and(|rows| rows >= min_rows) {
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

fn parse_single_csi_param_u16(params: &[u8]) -> Option<u16> {
    if params.is_empty() {
        return Some(1);
    }
    if params.iter().all(u8::is_ascii_digit) {
        std::str::from_utf8(params).ok()?.parse::<u16>().ok()
    } else {
        None
    }
}
