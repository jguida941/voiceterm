//! Input-thread bootstrap so stdin capture stays isolated from render/event logic.

use crossbeam_channel::Sender;
use std::io::{self, Read};
use std::thread;
use voiceterm::log_debug;

use crate::arrow_keys::is_arrow_escape_noise;
use crate::input::event::InputEvent;
use crate::input::parser::InputParser;

const INPUT_DEBUG_ENV: &str = "VOICETERM_DEBUG_INPUT";
const INPUT_DEBUG_MAX_BYTES: usize = 64;
fn input_debug_enabled() -> bool {
    std::env::var(INPUT_DEBUG_ENV).is_ok()
}

fn format_debug_bytes(bytes: &[u8]) -> String {
    let sample_len = bytes.len().min(INPUT_DEBUG_MAX_BYTES);
    let mut out = String::new();
    for (idx, byte) in bytes.iter().take(sample_len).enumerate() {
        if idx > 0 {
            out.push(' ');
        }
        out.push_str(&format!("{byte:02x}"));
    }
    if bytes.len() > sample_len {
        out.push_str(" ...");
    }
    out
}

#[inline]
fn should_log_event_debug(debug_input: bool, events: &[InputEvent]) -> bool {
    debug_input && !events.is_empty()
}

pub(crate) fn spawn_input_thread(tx: Sender<InputEvent>) -> thread::JoinHandle<()> {
    thread::spawn(move || {
        let mut stdin = io::stdin();
        let mut buf = [0u8; 1024];
        let mut parser = InputParser::new();
        let debug_input = input_debug_enabled();
        loop {
            let n = match stdin.read(&mut buf) {
                Ok(0) => break,
                Ok(n) => n,
                Err(err) => {
                    log_debug(&format!("stdin read error: {err}"));
                    break;
                }
            };
            if debug_input {
                log_debug(&format!(
                    "input bytes ({}): {}",
                    n,
                    format_debug_bytes(&buf[..n])
                ));
            }
            let mut events = Vec::new();
            parser.consume_bytes(&buf[..n], &mut events);
            parser.flush_pending(&mut events);
            if should_log_event_debug(debug_input, &events) {
                log_debug(&format!("input events: {events:?}"));
            }
            for event in events {
                if debug_input {
                    if let InputEvent::Bytes(bytes) = &event {
                        if is_arrow_escape_noise(bytes) {
                            log_debug(&format!(
                                "startup escape candidate: {}",
                                format_debug_bytes(bytes)
                            ));
                        }
                    }
                }
                if tx.send(event).is_err() {
                    return;
                }
            }
        }
    })
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::sync::{Mutex, OnceLock};

    fn env_lock() -> &'static Mutex<()> {
        static ENV_LOCK: OnceLock<Mutex<()>> = OnceLock::new();
        ENV_LOCK.get_or_init(|| Mutex::new(()))
    }

    #[test]
    fn input_debug_enabled_reflects_env_presence() {
        let _guard = env_lock().lock().expect("env lock");
        std::env::remove_var(INPUT_DEBUG_ENV);
        assert!(!input_debug_enabled());
        std::env::set_var(INPUT_DEBUG_ENV, "1");
        assert!(input_debug_enabled());
        std::env::remove_var(INPUT_DEBUG_ENV);
    }

    #[test]
    fn format_debug_bytes_formats_hex_pairs_with_spaces() {
        assert_eq!(format_debug_bytes(&[0x1b, 0x41, 0x7f]), "1b 41 7f");
        assert_eq!(format_debug_bytes(&[]), "");
    }

    #[test]
    fn format_debug_bytes_truncates_and_appends_ellipsis_when_over_limit() {
        let bytes = vec![0xab; INPUT_DEBUG_MAX_BYTES + 1];
        let rendered = format_debug_bytes(&bytes);
        assert!(rendered.ends_with(" ..."));
        let body = rendered.trim_end_matches(" ...");
        assert_eq!(body.split(' ').count(), INPUT_DEBUG_MAX_BYTES);
    }

    #[test]
    fn should_log_event_debug_requires_debug_and_non_empty_events() {
        assert!(!should_log_event_debug(false, &[InputEvent::Exit]));
        assert!(!should_log_event_debug(true, &[]));
        assert!(should_log_event_debug(true, &[InputEvent::Exit]));
    }
}
