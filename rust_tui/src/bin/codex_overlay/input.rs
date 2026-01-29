use crossbeam_channel::Sender;
use rust_tui::log_debug;
use std::io::{self, Read};
use std::thread;

#[derive(Debug, PartialEq, Eq)]
pub(crate) enum InputEvent {
    Bytes(Vec<u8>),
    VoiceTrigger,
    ToggleAutoVoice,
    ToggleSendMode,
    IncreaseSensitivity,
    DecreaseSensitivity,
    EnterKey,
    Exit,
}

pub(crate) fn spawn_input_thread(tx: Sender<InputEvent>) -> thread::JoinHandle<()> {
    thread::spawn(move || {
        let mut stdin = io::stdin();
        let mut buf = [0u8; 1024];
        let mut parser = InputParser::new();
        loop {
            let n = match stdin.read(&mut buf) {
                Ok(0) => break,
                Ok(n) => n,
                Err(err) => {
                    log_debug(&format!("stdin read error: {err}"));
                    break;
                }
            };
            let mut events = Vec::new();
            parser.consume_bytes(&buf[..n], &mut events);
            parser.flush_pending(&mut events);
            for event in events {
                if tx.send(event).is_err() {
                    return;
                }
            }
        }
    })
}

struct InputParser {
    pending: Vec<u8>,
    skip_lf: bool,
    esc_buffer: Option<Vec<u8>>,
}

impl InputParser {
    fn new() -> Self {
        Self {
            pending: Vec::new(),
            skip_lf: false,
            esc_buffer: None,
        }
    }

    fn consume_bytes(&mut self, bytes: &[u8], out: &mut Vec<InputEvent>) {
        for &byte in bytes {
            if self.consume_escape(byte) {
                continue;
            }
            if self.skip_lf {
                if byte == 0x0a {
                    self.skip_lf = false;
                    continue;
                }
                self.skip_lf = false;
            }

            match byte {
                0x11 => {
                    self.flush_pending(out);
                    out.push(InputEvent::Exit);
                }
                0x12 => {
                    self.flush_pending(out);
                    out.push(InputEvent::VoiceTrigger);
                }
                0x16 => {
                    self.flush_pending(out);
                    out.push(InputEvent::ToggleAutoVoice);
                }
                0x14 => {
                    self.flush_pending(out);
                    out.push(InputEvent::ToggleSendMode);
                }
                0x1d => {
                    self.flush_pending(out);
                    out.push(InputEvent::IncreaseSensitivity);
                }
                0x1c => {
                    self.flush_pending(out);
                    out.push(InputEvent::DecreaseSensitivity);
                }
                0x1f => {
                    self.flush_pending(out);
                    out.push(InputEvent::DecreaseSensitivity);
                }
                0x0d | 0x0a => {
                    self.flush_pending(out);
                    out.push(InputEvent::EnterKey);
                    if byte == 0x0d {
                        self.skip_lf = true;
                    }
                }
                _ => self.pending.push(byte),
            }
        }
    }

    fn consume_escape(&mut self, byte: u8) -> bool {
        const MAX_CSI_LEN: usize = 32;

        if let Some(ref mut buffer) = self.esc_buffer {
            buffer.push(byte);
            if buffer.len() == 2 && buffer[1] != b'[' {
                self.pending.extend_from_slice(buffer);
                self.esc_buffer = None;
                return true;
            }

            if buffer.len() >= 2 && buffer[1] == b'[' {
                if buffer.len() >= 3 && is_csi_final(byte) {
                    if is_csi_u_numeric(buffer) {
                        self.esc_buffer = None;
                    } else {
                        self.pending.extend_from_slice(buffer);
                        self.esc_buffer = None;
                    }
                    return true;
                }
                if buffer.len() > MAX_CSI_LEN {
                    self.pending.extend_from_slice(buffer);
                    self.esc_buffer = None;
                    return true;
                }
                return true;
            }

            if buffer.len() > MAX_CSI_LEN {
                self.pending.extend_from_slice(buffer);
                self.esc_buffer = None;
            }
            return true;
        }

        if byte == 0x1b {
            self.esc_buffer = Some(vec![byte]);
            return true;
        }
        false
    }

    fn flush_pending(&mut self, out: &mut Vec<InputEvent>) {
        if let Some(buffer) = self.esc_buffer.take() {
            self.pending.extend_from_slice(&buffer);
        }
        if !self.pending.is_empty() {
            out.push(InputEvent::Bytes(std::mem::take(&mut self.pending)));
        }
    }
}

fn is_csi_final(byte: u8) -> bool {
    (0x40..=0x7e).contains(&byte)
}

fn is_csi_u_numeric(buffer: &[u8]) -> bool {
    if buffer.len() < 3 {
        return false;
    }
    if buffer[0] != 0x1b || buffer[1] != b'[' || *buffer.last().unwrap() != b'u' {
        return false;
    }
    buffer[2..buffer.len() - 1]
        .iter()
        .all(|b| b.is_ascii_digit() || *b == b';')
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn input_parser_emits_bytes_and_controls() {
        let mut parser = InputParser::new();
        let mut out = Vec::new();
        parser.consume_bytes(b"hi\x12there", &mut out);
        parser.flush_pending(&mut out);
        assert_eq!(out.len(), 3);
        assert_eq!(out[0], InputEvent::Bytes(b"hi".to_vec()));
        assert_eq!(out[1], InputEvent::VoiceTrigger);
        assert_eq!(out[2], InputEvent::Bytes(b"there".to_vec()));
    }

    #[test]
    fn input_parser_maps_control_keys() {
        let mut parser = InputParser::new();
        let mut out = Vec::new();
        parser.consume_bytes(&[0x11, 0x16, 0x14, 0x1d, 0x1c, 0x1f], &mut out);
        parser.flush_pending(&mut out);
        assert_eq!(
            out,
            vec![
                InputEvent::Exit,
                InputEvent::ToggleAutoVoice,
                InputEvent::ToggleSendMode,
                InputEvent::IncreaseSensitivity,
                InputEvent::DecreaseSensitivity,
                InputEvent::DecreaseSensitivity,
            ]
        );
    }

    #[test]
    fn input_parser_skips_lf_after_cr() {
        let mut parser = InputParser::new();
        let mut out = Vec::new();
        parser.consume_bytes(b"a\r\n", &mut out);
        parser.flush_pending(&mut out);
        assert_eq!(
            out,
            vec![InputEvent::Bytes(b"a".to_vec()), InputEvent::EnterKey]
        );
    }

    #[test]
    fn input_parser_keeps_non_lf_after_cr() {
        let mut parser = InputParser::new();
        let mut out = Vec::new();
        parser.consume_bytes(b"a\rb", &mut out);
        parser.flush_pending(&mut out);
        assert_eq!(
            out,
            vec![
                InputEvent::Bytes(b"a".to_vec()),
                InputEvent::EnterKey,
                InputEvent::Bytes(b"b".to_vec())
            ]
        );
    }

    #[test]
    fn input_parser_drops_csi_u_sequences() {
        let mut parser = InputParser::new();
        let mut out = Vec::new();
        parser.consume_bytes(b"\x1b[48;0;0u", &mut out);
        parser.flush_pending(&mut out);
        assert!(out.is_empty());
    }

    #[test]
    fn input_parser_preserves_arrow_sequences() {
        let mut parser = InputParser::new();
        let mut out = Vec::new();
        parser.consume_bytes(b"\x1b[A", &mut out);
        parser.flush_pending(&mut out);
        assert_eq!(out.len(), 1);
        assert_eq!(out[0], InputEvent::Bytes(b"\x1b[A".to_vec()));
    }
}
