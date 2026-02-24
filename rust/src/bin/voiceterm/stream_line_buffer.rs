//! Shared bounded line buffer for newline-delimited PTY stream capture.

/// Bounded stream-line buffer with truncation marker semantics.
#[derive(Debug, Clone)]
pub(crate) struct StreamLineBuffer {
    buffer: String,
    truncated: bool,
    max_bytes: usize,
}

impl StreamLineBuffer {
    pub(crate) fn new(max_bytes: usize) -> Self {
        Self {
            buffer: String::new(),
            truncated: false,
            max_bytes,
        }
    }

    pub(crate) fn push_char(&mut self, ch: char) {
        if self.buffer.len() < self.max_bytes {
            self.buffer.push(ch);
        } else {
            self.truncated = true;
        }
    }

    pub(crate) fn pop_char(&mut self) {
        self.buffer.pop();
    }

    pub(crate) fn take_line(&mut self) -> Option<String> {
        let trimmed = self.buffer.trim();
        if trimmed.is_empty() {
            self.buffer.clear();
            self.truncated = false;
            return None;
        }

        let mut line = trimmed.to_string();
        if self.truncated {
            line.push_str(" ...");
        }
        self.buffer.clear();
        self.truncated = false;
        Some(line)
    }
}

#[cfg(test)]
mod tests {
    use super::StreamLineBuffer;

    #[test]
    fn take_line_trims_and_resets_state() {
        let mut line = StreamLineBuffer::new(32);
        line.push_char(' ');
        line.push_char('o');
        line.push_char('k');
        line.push_char(' ');
        assert_eq!(line.take_line().as_deref(), Some("ok"));
        assert_eq!(line.take_line(), None);
    }

    #[test]
    fn take_line_marks_truncation_suffix() {
        let mut line = StreamLineBuffer::new(2);
        line.push_char('h');
        line.push_char('i');
        line.push_char('!');
        assert_eq!(line.take_line().as_deref(), Some("hi ..."));
    }
}
