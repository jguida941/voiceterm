//! Software scroll fence for hosts that ignore DECSTBM (JediTerm).
//!
//! Without a scroll region nothing stops the child from walking its cursor
//! below the viewport it was told it has, and a line feed on the host's real
//! bottom row then scrolls the HUD rows away (field capture 2026-11-04,
//! PyCharm + Claude). This tracks the child's cursor row through its output
//! and replaces a line feed on the last viewport row with a viewport-only
//! scroll: delete a line at row 1, insert one at the viewport bottom. Every
//! line operation is emitted as a delete/insert pair so the rows below the
//! viewport shift and shift back inside one write and never move on screen.

const MAX_CARRY_BYTES: usize = 64;

#[derive(Debug, Default)]
pub(super) struct ViewportFence {
    row: u16,
    col: u16,
    carry: Vec<u8>,
    dec_saved: Option<(u16, u16)>,
    /// The child saved its cursor with DECSC and has not restored it yet, so
    /// the fence must not borrow that slot.
    dec_save_active: bool,
    ansi_saved: Option<(u16, u16)>,
}

#[derive(Clone, Copy)]
struct Geometry {
    bottom: u16,
    rows: u16,
    cols: u16,
    fenced: bool,
}

enum Escape {
    Incomplete,
    Complete(usize),
}

impl ViewportFence {
    /// The host geometry changed; the real cursor position is unknown until the
    /// child positions absolutely again, so keep the model inside the viewport.
    pub(super) fn on_resize(&mut self, bottom: u16) {
        self.row = self.row.clamp(1, bottom.max(1));
        self.col = self.col.max(1);
    }

    /// Translate one chunk of child output for a host without a scroll region.
    /// `bottom` is the last row of the child viewport; `rows`/`cols` the host.
    pub(super) fn translate(&mut self, bytes: &[u8], bottom: u16, rows: u16, cols: u16) -> Vec<u8> {
        let rows = rows.max(1);
        let cols = cols.max(1);
        let bottom = if bottom == 0 { rows } else { bottom.min(rows) };
        let g = Geometry {
            bottom,
            rows,
            cols,
            fenced: bottom < rows,
        };
        if self.row == 0 {
            self.row = 1;
            self.col = 1;
        }
        let mut stream = std::mem::take(&mut self.carry);
        stream.extend_from_slice(bytes);
        let mut out = Vec::with_capacity(stream.len() + 64);
        let mut i = 0;
        while i < stream.len() {
            let b = stream[i];
            match b {
                0x1b => match escape_len(&stream[i..]) {
                    Escape::Incomplete => {
                        self.carry = stream[i..].to_vec();
                        if self.carry.len() > MAX_CARRY_BYTES {
                            out.extend_from_slice(&self.carry);
                            self.carry.clear();
                        }
                        break;
                    }
                    Escape::Complete(len) => {
                        let seq = &stream[i..i + len];
                        self.apply_escape(seq, &g, &mut out);
                        i += len;
                    }
                },
                b'\n' | 0x0b | 0x0c => {
                    self.line_feed(b, &g, &mut out);
                    i += 1;
                }
                b'\r' => {
                    self.col = 1;
                    out.push(b);
                    i += 1;
                }
                0x08 => {
                    self.col = self.col.saturating_sub(1).max(1);
                    out.push(b);
                    i += 1;
                }
                0x09 => {
                    self.col = (self.col / 8 * 8 + 9).min(g.cols);
                    out.push(b);
                    i += 1;
                }
                _ => {
                    if b & 0b1100_0000 != 0b1000_0000 && b >= 0x20 {
                        if self.col > g.cols {
                            // Deferred wrap: this glyph starts a new line.
                            self.col = 1;
                            if g.fenced && self.row >= g.bottom {
                                self.row = g.bottom;
                                self.scroll_viewport(&g, true, 1, &mut out);
                                out.extend_from_slice(format!("\x1b[{};1H", g.bottom).as_bytes());
                            } else {
                                self.row = (self.row + 1).min(g.rows);
                            }
                        }
                        self.col += 1;
                    }
                    out.push(b);
                    i += 1;
                }
            }
        }
        out
    }

    fn line_feed(&mut self, byte: u8, g: &Geometry, out: &mut Vec<u8>) {
        if g.fenced && self.row >= g.bottom {
            self.row = g.bottom;
            self.with_cursor_kept(g, out, |fence, out| fence.scroll_viewport(g, true, 1, out));
        } else {
            self.row = (self.row + 1).min(g.rows);
            out.push(byte);
        }
    }

    /// Run a line operation and bring the cursor back to where the child left
    /// it. DECSC/DECRC return the cursor to its true position whatever the
    /// model believes; the model's own position is used only while the child
    /// holds the DEC slot or a deferred wrap is pending, which DECRC would
    /// revive but the replaced motion would have cleared.
    fn with_cursor_kept(
        &mut self,
        g: &Geometry,
        out: &mut Vec<u8>,
        body: impl FnOnce(&mut Self, &mut Vec<u8>),
    ) {
        if self.dec_save_active || self.col > g.cols {
            body(self, out);
            self.cup_to_model(g, out);
        } else {
            out.extend_from_slice(b"\x1b7");
            body(self, out);
            out.extend_from_slice(b"\x1b8");
        }
    }

    fn cup_to_model(&self, g: &Geometry, out: &mut Vec<u8>) {
        out.extend_from_slice(
            format!(
                "\x1b[{};{}H",
                self.row.clamp(1, g.rows),
                self.col.clamp(1, g.cols)
            )
            .as_bytes(),
        );
    }

    /// Scroll rows 1..=bottom by `n` lines, up or down, leaving the rows below
    /// the viewport where they are.
    fn scroll_viewport(&self, g: &Geometry, up: bool, n: u16, out: &mut Vec<u8>) {
        let n = n.clamp(1, g.bottom);
        let edge = g.bottom - n + 1;
        if up {
            delete_then_insert(1, edge, n, out);
        } else {
            delete_then_insert(edge, 1, n, out);
        }
    }

    fn apply_escape(&mut self, seq: &[u8], g: &Geometry, out: &mut Vec<u8>) {
        if seq.len() >= 2 && seq[1] == b'[' {
            self.apply_csi(seq, g, out);
            return;
        }
        match seq.get(1).copied() {
            Some(b'7') => {
                self.dec_saved = Some((self.row, self.col));
                self.dec_save_active = true;
            }
            Some(b'8') => {
                if let Some((r, c)) = self.dec_saved {
                    self.row = r;
                    self.col = c;
                }
                self.dec_save_active = false;
            }
            Some(b'D') => {
                self.line_feed(b'\n', g, out);
                return;
            }
            Some(b'E') => {
                self.col = 1;
                out.push(b'\r');
                self.line_feed(b'\n', g, out);
                return;
            }
            Some(b'M') => {
                if g.fenced && self.row <= 1 {
                    self.row = 1;
                    self.with_cursor_kept(g, out, |fence, out| {
                        fence.scroll_viewport(g, false, 1, out)
                    });
                    return;
                }
                self.row = self.row.saturating_sub(1).max(1);
            }
            Some(b'c') => {
                self.row = 1;
                self.col = 1;
                self.dec_saved = None;
                self.dec_save_active = false;
                self.ansi_saved = None;
            }
            _ => {}
        }
        out.extend_from_slice(seq);
    }

    fn apply_csi(&mut self, seq: &[u8], g: &Geometry, out: &mut Vec<u8>) {
        let final_byte = seq[seq.len() - 1];
        let body = &seq[2..seq.len() - 1];
        let private = body
            .first()
            .is_some_and(|b| matches!(b, b'?' | b'>' | b'<' | b'='));
        let params: Vec<u16> = if private {
            Vec::new()
        } else {
            body.split(|b| *b == b';')
                .map(|p| {
                    p.iter()
                        .take_while(|b| b.is_ascii_digit())
                        .fold(0u16, |a, b| {
                            a.saturating_mul(10).saturating_add((b - b'0') as u16)
                        })
                })
                .collect()
        };
        let n = params.first().copied().filter(|v| *v > 0).unwrap_or(1);
        let limit = if g.fenced { g.bottom } else { g.rows };
        match final_byte {
            b'A' => self.row = self.row.saturating_sub(n).max(1),
            b'B' | b'e' => {
                let step = n.min(limit.saturating_sub(self.row));
                self.row += step;
                if step != n {
                    if step > 0 {
                        out.extend_from_slice(format!("\x1b[{step}B").as_bytes());
                    }
                    return;
                }
            }
            b'E' => {
                let step = n.min(limit.saturating_sub(self.row));
                self.row += step;
                self.col = 1;
                if step != n {
                    out.push(b'\r');
                    if step > 0 {
                        out.extend_from_slice(format!("\x1b[{step}B").as_bytes());
                    }
                    return;
                }
            }
            b'F' => {
                self.row = self.row.saturating_sub(n).max(1);
                self.col = 1;
            }
            b'C' | b'a' => self.col = (self.col + n).min(g.cols),
            b'D' => self.col = self.col.saturating_sub(n).max(1),
            b'G' | b'`' => self.col = n.min(g.cols),
            b'd' => self.row = n.min(g.rows),
            b'H' | b'f' => {
                self.row = n.min(g.rows);
                self.col = params
                    .get(1)
                    .copied()
                    .filter(|v| *v > 0)
                    .unwrap_or(1)
                    .min(g.cols);
            }
            b'L' | b'M' if g.fenced && self.row <= g.bottom => {
                // A child insert/delete inside the viewport must push rows out
                // at the viewport bottom, not at the bottom of the screen.
                let row = self.row;
                let n = n.min(g.bottom - row + 1);
                let edge = g.bottom - n + 1;
                self.with_cursor_kept(g, out, |_, out| {
                    if final_byte == b'L' {
                        delete_then_insert(edge, row, n, out);
                    } else {
                        delete_then_insert(row, edge, n, out);
                    }
                });
                return;
            }
            b'S' | b'T' if g.fenced => {
                let up = final_byte == b'S';
                self.with_cursor_kept(g, out, |fence, out| fence.scroll_viewport(g, up, n, out));
                return;
            }
            b's' if !private => self.ansi_saved = Some((self.row, self.col)),
            b'u' if !private => {
                if let Some((r, c)) = self.ansi_saved {
                    self.row = r;
                    self.col = c;
                }
            }
            _ => {}
        }
        out.extend_from_slice(seq);
    }
}

/// Delete `n` lines at `delete_at`, then insert `n` lines at `insert_at`. The
/// rows below both positions move down and back up within the pair, so a
/// HUD below the viewport ends exactly where it started.
fn delete_then_insert(delete_at: u16, insert_at: u16, n: u16, out: &mut Vec<u8>) {
    let count = if n == 1 { String::new() } else { n.to_string() };
    out.extend_from_slice(
        format!("\x1b[{delete_at};1H\x1b[{count}M\x1b[{insert_at};1H\x1b[{count}L").as_bytes(),
    );
}

/// Length of the escape sequence starting at `s[0] == ESC`, or `Incomplete`.
fn escape_len(s: &[u8]) -> Escape {
    let Some(&kind) = s.get(1) else {
        return Escape::Incomplete;
    };
    match kind {
        b'[' => {
            let mut i = 2;
            while i < s.len() && (0x30..=0x3f).contains(&s[i]) {
                i += 1;
            }
            while i < s.len() && (0x20..=0x2f).contains(&s[i]) {
                i += 1;
            }
            match s.get(i) {
                Some(_) => Escape::Complete(i + 1),
                None => Escape::Incomplete,
            }
        }
        b']' | b'P' | b'_' | b'^' | b'X' => {
            // OSC/DCS/APC/PM/SOS: terminated by BEL or ST (ESC \).
            let mut i = 2;
            while i < s.len() {
                if s[i] == 0x07 {
                    return Escape::Complete(i + 1);
                }
                if s[i] == 0x1b {
                    return match s.get(i + 1) {
                        Some(b'\\') => Escape::Complete(i + 2),
                        Some(_) => Escape::Complete(i),
                        None => Escape::Incomplete,
                    };
                }
                i += 1;
            }
            Escape::Incomplete
        }
        b if (0x20..=0x2f).contains(&b) => {
            let mut i = 2;
            while i < s.len() && (0x20..=0x2f).contains(&s[i]) {
                i += 1;
            }
            if i < s.len() {
                Escape::Complete(i + 1)
            } else {
                Escape::Incomplete
            }
        }
        _ => Escape::Complete(2),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn fence_at(row: u16) -> ViewportFence {
        let mut f = ViewportFence::default();
        f.translate(format!("\x1b[{row};1H").as_bytes(), 24, 32, 80);
        f
    }

    #[test]
    fn line_feed_above_the_bottom_passes_through_and_tracks_the_row() {
        let mut f = fence_at(5);
        let out = f.translate(b"abc\r\n", 24, 32, 80);
        assert_eq!(out, b"abc\r\n");
        assert_eq!((f.row, f.col), (6, 1));
    }

    #[test]
    fn line_feed_on_the_bottom_becomes_a_viewport_scroll_around_a_saved_cursor() {
        let mut f = fence_at(24);
        let out = f.translate(b"x\n", 24, 32, 80);
        assert_eq!(out, b"x\x1b7\x1b[1;1H\x1b[M\x1b[24;1H\x1b[L\x1b8");
        assert_eq!(f.row, 24);
    }

    #[test]
    fn line_feed_on_the_bottom_uses_the_model_position_while_the_child_holds_decsc() {
        let mut f = fence_at(24);
        let out = f.translate(b"\x1b7xy\n", 24, 32, 80);
        assert_eq!(out, b"\x1b7xy\x1b[1;1H\x1b[M\x1b[24;1H\x1b[L\x1b[24;3H");
        assert!(!out.contains(&b'\n'));
    }

    #[test]
    fn cursor_down_is_clamped_to_the_viewport() {
        let mut f = fence_at(22);
        let out = f.translate(b"\x1b[5B", 24, 32, 80);
        assert_eq!(out, b"\x1b[2B");
        assert_eq!(f.row, 24);
    }

    #[test]
    fn reverse_index_on_the_top_row_becomes_a_viewport_scroll_down() {
        let mut f = fence_at(1);
        let out = f.translate(b"\x1bM", 24, 32, 80);
        assert_eq!(out, b"\x1b7\x1b[24;1H\x1b[M\x1b[1;1H\x1b[L\x1b8");
        assert_eq!(f.row, 1);
    }

    #[test]
    fn child_insert_line_pushes_rows_out_at_the_viewport_bottom() {
        let mut f = fence_at(10);
        let out = f.translate(b"\x1b[2L", 24, 32, 80);
        assert_eq!(out, b"\x1b7\x1b[23;1H\x1b[2M\x1b[10;1H\x1b[2L\x1b8");
        let out = f.translate(b"\x1b[M", 24, 32, 80);
        assert_eq!(out, b"\x1b7\x1b[10;1H\x1b[M\x1b[24;1H\x1b[L\x1b8");
    }

    #[test]
    fn unfenced_hosts_and_hidden_huds_pass_everything_through() {
        let mut f = fence_at(32);
        let out = f.translate(b"end\n", 32, 32, 80);
        assert_eq!(out, b"end\n");
    }

    #[test]
    fn sequences_split_across_chunks_are_joined_and_osc_passes_through() {
        let mut f = fence_at(24);
        let first = f.translate(b"\x1b]0;title\x07\x1b[", 24, 32, 80);
        assert_eq!(first, b"\x1b]0;title\x07");
        let second = f.translate(b"3A", 24, 32, 80);
        assert_eq!(second, b"\x1b[3A");
        assert_eq!(f.row, 21);
    }
}
