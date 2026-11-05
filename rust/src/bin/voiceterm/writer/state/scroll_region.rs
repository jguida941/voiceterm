//! Tracks the scroll region the child last declared so HUD paints can restore it.
//!
//! Codex pins its composer by declaring a small DECSTBM region around its history
//! scrolls. A HUD paint that resets the region to the whole child viewport makes
//! the child's next scroll move the entire viewport, which runs over the child's
//! own bottom rows until the child redeclares (field evidence 2026-11-04).

/// Longest partial CSI sequence kept between PTY chunks.
const MAX_CARRY_BYTES: usize = 32;

#[derive(Debug, Clone, Default)]
pub(super) struct ChildScrollRegionTracker {
    declared: Option<(u16, u16)>,
    carry: Vec<u8>,
}

impl ChildScrollRegionTracker {
    /// The region the child last declared, or `None` after `CSI r` / before any.
    pub(super) fn declared(&self) -> Option<(u16, u16)> {
        self.declared
    }

    /// Scan one PTY chunk for DECSTBM commands, honoring sequences split across
    /// chunk boundaries.
    pub(super) fn observe(&mut self, bytes: &[u8]) {
        let mut stream = std::mem::take(&mut self.carry);
        stream.extend_from_slice(bytes);
        let mut idx = 0;
        while idx < stream.len() {
            if stream[idx] != 0x1b {
                idx += 1;
                continue;
            }
            if idx + 1 >= stream.len() {
                self.carry = stream[idx..].to_vec();
                break;
            }
            if stream[idx + 1] != b'[' {
                idx += 1;
                continue;
            }
            let params_start = idx + 2;
            let mut cursor = params_start;
            while cursor < stream.len()
                && (stream[cursor].is_ascii_digit() || stream[cursor] == b';')
            {
                cursor += 1;
            }
            if cursor >= stream.len() {
                self.carry = stream[idx..].to_vec();
                break;
            }
            if stream[cursor] == b'r' {
                // `CSI r` resets; an invalid pair (top >= bottom) is ignored by
                // terminals and therefore also leaves the tracked region alone.
                match parse_region(&stream[params_start..cursor]) {
                    Parsed::Reset => self.declared = None,
                    Parsed::Region(top, bottom) => self.declared = Some((top, bottom)),
                    Parsed::Invalid => {}
                }
            }
            idx = cursor + 1;
        }
        if self.carry.len() > MAX_CARRY_BYTES {
            self.carry.clear();
        }
    }
}

enum Parsed {
    Reset,
    Region(u16, u16),
    Invalid,
}

fn parse_region(params: &[u8]) -> Parsed {
    if params.is_empty() {
        return Parsed::Reset;
    }
    let mut fields = params.split(|b| *b == b';');
    let top = fields.next().map(parse_or_default).unwrap_or(0);
    let bottom = fields.next().map(parse_or_default).unwrap_or(0);
    let top = if top == 0 { 1 } else { top };
    // An omitted or zero bottom means the last row the child believes in; the
    // caller clamps it to the real child viewport.
    let bottom = if bottom == 0 { u16::MAX } else { bottom };
    if top >= bottom {
        Parsed::Invalid
    } else {
        Parsed::Region(top, bottom)
    }
}

fn parse_or_default(field: &[u8]) -> u16 {
    field.iter().fold(0u16, |acc, b| {
        acc.saturating_mul(10).saturating_add((b - b'0') as u16)
    })
}

/// The scroll region a HUD paint must leave on the host: the child's declared
/// region clamped to its viewport, or the whole viewport when it declared none.
pub(super) fn host_scroll_region(declared: Option<(u16, u16)>, viewport_bottom: u16) -> (u16, u16) {
    let limit = viewport_bottom.max(1);
    match declared {
        Some((top, bottom)) => {
            let bottom = bottom.min(limit).max(1);
            (top.max(1).min(bottom), bottom)
        }
        None => (1, limit),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn tracker_records_a_declared_region_and_a_reset() {
        let mut tracker = ChildScrollRegionTracker::default();
        tracker.observe(b"text\x1b[1;22rmore");
        assert_eq!(tracker.declared(), Some((1, 22)));
        tracker.observe(b"\x1b[r");
        assert_eq!(tracker.declared(), None);
    }

    #[test]
    fn tracker_joins_a_declaration_split_across_chunks() {
        let mut tracker = ChildScrollRegionTracker::default();
        tracker.observe(b"\x1b");
        tracker.observe(b"[5;");
        tracker.observe(b"18r");
        assert_eq!(tracker.declared(), Some((5, 18)));
    }

    #[test]
    fn tracker_ignores_private_modes_other_finals_and_invalid_pairs() {
        let mut tracker = ChildScrollRegionTracker::default();
        tracker.observe(b"\x1b[1;22r");
        tracker.observe(b"\x1b[?1000r\x1b[3;4H\x1b[2K\x1b[9;3r");
        assert_eq!(tracker.declared(), Some((1, 22)));
    }

    #[test]
    fn omitted_bottom_means_the_child_full_height() {
        let mut tracker = ChildScrollRegionTracker::default();
        tracker.observe(b"\x1b[5r");
        assert_eq!(tracker.declared(), Some((5, u16::MAX)));
        assert_eq!(host_scroll_region(tracker.declared(), 20), (5, 20));
    }

    #[test]
    fn host_region_clamps_to_the_viewport_and_defaults_to_it() {
        assert_eq!(host_scroll_region(Some((1, 10)), 20), (1, 10));
        assert_eq!(host_scroll_region(Some((1, 30)), 20), (1, 20));
        assert_eq!(host_scroll_region(Some((25, 30)), 20), (20, 20));
        assert_eq!(host_scroll_region(None, 20), (1, 20));
        assert_eq!(host_scroll_region(None, 0), (1, 1));
    }
}
