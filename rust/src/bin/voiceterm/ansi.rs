//! Shared ANSI/control stripping helpers used across runtime + tests.

use vte::{Parser as VteParser, Perform};

pub(crate) fn strip_ansi_preserve_controls(bytes: &[u8]) -> Vec<u8> {
    struct ControlStripper {
        output: Vec<u8>,
    }

    impl Perform for ControlStripper {
        fn print(&mut self, c: char) {
            let mut buf = [0u8; 4];
            let encoded = c.encode_utf8(&mut buf);
            self.output.extend_from_slice(encoded.as_bytes());
        }

        fn execute(&mut self, byte: u8) {
            match byte {
                b'\n' | b'\r' | b'\t' => self.output.push(byte),
                _ => {}
            }
        }
    }

    let mut parser = VteParser::new();
    let mut stripper = ControlStripper {
        output: Vec::with_capacity(bytes.len()),
    };
    parser.advance(&mut stripper, bytes);
    stripper.output
}

pub(crate) fn strip_ansi(input: &str) -> String {
    String::from_utf8_lossy(&strip_ansi_preserve_controls(input.as_bytes())).into_owned()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn strip_ansi_removes_escape_sequences() {
        assert_eq!(strip_ansi("\x1b[31mhello\x1b[0m"), "hello");
    }

    #[test]
    fn strip_ansi_preserves_line_controls() {
        assert_eq!(strip_ansi("a\tb\r\n"), "a\tb\r\n");
    }
}
