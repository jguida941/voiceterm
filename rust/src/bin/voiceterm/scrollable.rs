//! Shared scroll-offset trait for overlay panels that need vertical scrolling.
//!
//! This trait provides shared saturating scroll math for overlay panels.

/// Vertical scroll behaviour for any overlay panel that tracks a `scroll_offset`.
///
/// Implementors supply a mutable offset accessor; the default `scroll_up` and
/// `scroll_down` implementations handle the clamping arithmetic.
pub(crate) trait Scrollable {
    /// Mutable reference to the scroll position, used by the default methods.
    fn scroll_offset_mut(&mut self) -> &mut usize;

    /// Move the viewport up by `amount` lines, clamping at zero.
    fn scroll_up(&mut self, amount: usize) {
        let offset = self.scroll_offset_mut();
        *offset = offset.saturating_sub(amount);
    }

    /// Move the viewport down by `amount` lines, clamping at `max_offset`.
    fn scroll_down(&mut self, amount: usize, max_offset: usize) {
        let offset = self.scroll_offset_mut();
        *offset = (*offset + amount).min(max_offset);
    }
}
