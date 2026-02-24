//! HUD queue module so pending transcript depth is visible at a glance.
//!
//! Shows the number of pending transcripts in queue: "Q: 2"

use super::{display_width, HudModule, HudState};
use crate::theme::hud_queue_icon;

/// Queue depth module showing pending transcript count.
pub struct QueueModule;

impl QueueModule {
    /// Create a new queue module.
    pub fn new() -> Self {
        Self
    }
}

impl Default for QueueModule {
    fn default() -> Self {
        Self::new()
    }
}

impl HudModule for QueueModule {
    fn id(&self) -> &'static str {
        "queue"
    }

    fn render(&self, state: &HudState, max_width: usize) -> String {
        if max_width < self.min_width() {
            return String::new();
        }

        // Only show queue indicator if there are pending items
        if state.queue_depth == 0 {
            return String::new();
        }

        let icon = hud_queue_icon(state.glyph_set);
        let full = format!("{icon}: {}", state.queue_depth);
        if display_width(&full) <= max_width {
            full
        } else if max_width >= 2 {
            // Ultra compact
            format!("{icon}{}", state.queue_depth)
        } else {
            String::new()
        }
    }

    fn min_width(&self) -> usize {
        // Minimum: "Q1" = 2 chars
        2
    }

    fn priority(&self) -> u8 {
        240
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn queue_module_id() {
        let module = QueueModule::new();
        assert_eq!(module.id(), "queue");
    }

    #[test]
    fn queue_module_min_width() {
        let module = QueueModule::new();
        assert_eq!(module.min_width(), 2);
    }

    #[test]
    fn queue_module_priority_is_stable() {
        let module = QueueModule::new();
        assert_eq!(module.priority(), 240);
    }

    #[test]
    fn queue_module_tick_interval() {
        let module = QueueModule::new();
        // Queue is event-driven, no tick
        assert!(module.tick_interval().is_none());
    }

    #[test]
    fn queue_module_render_empty() {
        let module = QueueModule::new();
        let state = HudState {
            queue_depth: 0,
            ..Default::default()
        };
        let output = module.render(&state, 10);
        // Empty queue shows nothing
        assert!(output.is_empty());
    }

    #[test]
    fn queue_module_render_with_items() {
        let module = QueueModule::new();
        let state = HudState {
            queue_depth: 2,
            ..Default::default()
        };
        let output = module.render(&state, 10);
        assert!(output.contains('▤'));
        assert!(output.contains("2"));
    }

    #[test]
    fn queue_module_render_many_items() {
        let module = QueueModule::new();
        let state = HudState {
            queue_depth: 15,
            ..Default::default()
        };
        let output = module.render(&state, 10);
        assert!(output.contains("15"));
    }

    #[test]
    fn queue_module_render_narrow() {
        let module = QueueModule::new();
        let state = HudState {
            queue_depth: 2,
            ..Default::default()
        };
        // Too narrow
        let output = module.render(&state, 1);
        assert!(output.is_empty());
    }

    #[test]
    fn queue_module_render_compact() {
        let module = QueueModule::new();
        let state = HudState {
            queue_depth: 3,
            ..Default::default()
        };
        // Just enough for compact
        let output = module.render(&state, 2);
        assert!(output.contains('▤'));
        assert!(output.contains("3"));
    }

    #[test]
    fn queue_module_render_full() {
        let module = QueueModule::new();
        let state = HudState {
            queue_depth: 5,
            ..Default::default()
        };
        let output = module.render(&state, 10);
        assert_eq!(output, "▤: 5");
    }

    #[test]
    fn queue_module_respects_ascii_glyph_set() {
        let module = QueueModule::new();
        let state = HudState {
            queue_depth: 4,
            glyph_set: crate::theme::GlyphSet::Ascii,
            ..Default::default()
        };
        let output = module.render(&state, 10);
        assert_eq!(output, "Q: 4");
    }
}
