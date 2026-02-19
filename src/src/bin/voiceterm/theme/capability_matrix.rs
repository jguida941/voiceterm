//! Framework capability matrix and parity gate (MP-175).
//!
//! Tracks shipped Ratatui widget/symbol families and Crossterm color/input/render
//! capabilities (including synchronized updates and keyboard enhancement flags).
//! Provides a parity gate that validates upgrade deltas before enabling new
//! Theme Studio controls.
//!
//! Gate evidence: TS-G09 (capability fallback), TS-G15 (ecosystem packs).

use super::Theme;

// ---------------------------------------------------------------------------
// Ratatui capability surface
// ---------------------------------------------------------------------------

/// Ratatui widget families available at the pinned crate version.
///
/// Each entry maps to a widget type that Theme Studio may expose controls for.
/// Adding a new entry requires a corresponding style-ID registration and
/// resolver binding before the control can graduate.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub(crate) enum RatatuiWidget {
    Block,
    Paragraph,
    List,
    Table,
    Tabs,
    Chart,
    Sparkline,
    Gauge,
    LineGauge,
    Scrollbar,
    Canvas,
    BarChart,
    Calendar,
    Clear,
}

impl RatatuiWidget {
    /// All widget families shipped with the pinned Ratatui version.
    #[must_use]
    pub(crate) const fn all() -> &'static [Self] {
        &[
            Self::Block,
            Self::Paragraph,
            Self::List,
            Self::Table,
            Self::Tabs,
            Self::Chart,
            Self::Sparkline,
            Self::Gauge,
            Self::LineGauge,
            Self::Scrollbar,
            Self::Canvas,
            Self::BarChart,
            Self::Calendar,
            Self::Clear,
        ]
    }

    /// Human-readable name for display/logging.
    #[must_use]
    pub(crate) const fn name(&self) -> &'static str {
        match self {
            Self::Block => "Block",
            Self::Paragraph => "Paragraph",
            Self::List => "List",
            Self::Table => "Table",
            Self::Tabs => "Tabs",
            Self::Chart => "Chart",
            Self::Sparkline => "Sparkline",
            Self::Gauge => "Gauge",
            Self::LineGauge => "LineGauge",
            Self::Scrollbar => "Scrollbar",
            Self::Canvas => "Canvas",
            Self::BarChart => "BarChart",
            Self::Calendar => "Calendar",
            Self::Clear => "Clear",
        }
    }
}

/// Ratatui symbol families available at the pinned crate version.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub(crate) enum RatatuiSymbolFamily {
    Bar,
    Block,
    Border,
    Braille,
    Line,
    Marker,
    Scrollbar,
    Shade,
}

impl RatatuiSymbolFamily {
    /// All symbol families shipped with the pinned Ratatui version.
    #[must_use]
    pub(crate) const fn all() -> &'static [Self] {
        &[
            Self::Bar,
            Self::Block,
            Self::Border,
            Self::Braille,
            Self::Line,
            Self::Marker,
            Self::Scrollbar,
            Self::Shade,
        ]
    }

    /// Human-readable name for display/logging.
    #[must_use]
    pub(crate) const fn name(&self) -> &'static str {
        match self {
            Self::Bar => "bar",
            Self::Block => "block",
            Self::Border => "border",
            Self::Braille => "braille",
            Self::Line => "line",
            Self::Marker => "marker",
            Self::Scrollbar => "scrollbar",
            Self::Shade => "shade",
        }
    }
}

// ---------------------------------------------------------------------------
// Crossterm capability surface
// ---------------------------------------------------------------------------

/// Crossterm capabilities that influence Theme Studio control availability.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub(crate) enum CrosstermCapability {
    /// 24-bit RGB color support.
    TrueColor,
    /// 256 indexed color support.
    Color256,
    /// Basic 16 ANSI colors.
    Ansi16,
    /// Mouse event capture (button/move/drag).
    MouseEvents,
    /// Focus gain/loss events.
    FocusEvents,
    /// Bracketed paste mode.
    BracketedPaste,
    /// Synchronized terminal updates (BeginSynchronizedUpdate).
    SynchronizedUpdates,
    /// Keyboard enhancement flags (disambiguate key-press/release/repeat).
    KeyboardEnhancement,
    /// Window resize events.
    Resize,
}

impl CrosstermCapability {
    /// All capabilities in the pinned Crossterm version.
    #[must_use]
    pub(crate) const fn all() -> &'static [Self] {
        &[
            Self::TrueColor,
            Self::Color256,
            Self::Ansi16,
            Self::MouseEvents,
            Self::FocusEvents,
            Self::BracketedPaste,
            Self::SynchronizedUpdates,
            Self::KeyboardEnhancement,
            Self::Resize,
        ]
    }

    /// Human-readable name for display/logging.
    #[must_use]
    pub(crate) const fn name(&self) -> &'static str {
        match self {
            Self::TrueColor => "truecolor",
            Self::Color256 => "color256",
            Self::Ansi16 => "ansi16",
            Self::MouseEvents => "mouse_events",
            Self::FocusEvents => "focus_events",
            Self::BracketedPaste => "bracketed_paste",
            Self::SynchronizedUpdates => "synchronized_updates",
            Self::KeyboardEnhancement => "keyboard_enhancement",
            Self::Resize => "resize",
        }
    }
}

// ---------------------------------------------------------------------------
// Capability snapshot (pinned version baseline)
// ---------------------------------------------------------------------------

/// Pinned framework versions for the current release.
pub(crate) const PINNED_RATATUI_VERSION: &str = "0.26";
pub(crate) const PINNED_CROSSTERM_VERSION: &str = "0.27";

/// Snapshot of the framework capability baseline at the pinned versions.
#[derive(Debug, Clone, PartialEq, Eq)]
pub(crate) struct FrameworkCapabilitySnapshot {
    pub(crate) ratatui_version: &'static str,
    pub(crate) crossterm_version: &'static str,
    pub(crate) ratatui_widgets: &'static [RatatuiWidget],
    pub(crate) ratatui_symbols: &'static [RatatuiSymbolFamily],
    pub(crate) crossterm_capabilities: &'static [CrosstermCapability],
}

/// Return the capability snapshot for the current pinned framework versions.
#[must_use]
pub(crate) fn current_capability_snapshot() -> FrameworkCapabilitySnapshot {
    FrameworkCapabilitySnapshot {
        ratatui_version: PINNED_RATATUI_VERSION,
        crossterm_version: PINNED_CROSSTERM_VERSION,
        ratatui_widgets: RatatuiWidget::all(),
        ratatui_symbols: RatatuiSymbolFamily::all(),
        crossterm_capabilities: CrosstermCapability::all(),
    }
}

// ---------------------------------------------------------------------------
// Parity gate
// ---------------------------------------------------------------------------

/// Result of a capability parity check.
#[derive(Debug, Clone, PartialEq, Eq)]
pub(crate) struct ParityCheckResult {
    /// Widget families that lack style-ID registration.
    pub(crate) unregistered_widgets: Vec<&'static str>,
    /// Symbol families that lack resolver bindings.
    pub(crate) unmapped_symbols: Vec<&'static str>,
    /// Whether the gate passes (all widgets registered, all symbols mapped).
    pub(crate) passed: bool,
}

/// Registered widget families that have style-ID and resolver bindings.
///
/// This allowlist grows as Theme Studio controls are implemented for each
/// widget family. A widget not in this list blocks its Studio control from
/// graduating.
const REGISTERED_WIDGET_STYLE_IDS: &[RatatuiWidget] = &[
    RatatuiWidget::Block,
    RatatuiWidget::Paragraph,
    RatatuiWidget::List,
    RatatuiWidget::Table,
    RatatuiWidget::Tabs,
    RatatuiWidget::Chart,
    RatatuiWidget::Sparkline,
    RatatuiWidget::Gauge,
    RatatuiWidget::LineGauge,
    RatatuiWidget::Scrollbar,
    RatatuiWidget::BarChart,
    RatatuiWidget::Clear,
];

/// Symbol families with resolver bindings in the style-pack system.
const MAPPED_SYMBOL_FAMILIES: &[RatatuiSymbolFamily] = &[
    RatatuiSymbolFamily::Bar,
    RatatuiSymbolFamily::Block,
    RatatuiSymbolFamily::Border,
    RatatuiSymbolFamily::Braille,
    RatatuiSymbolFamily::Line,
    RatatuiSymbolFamily::Scrollbar,
    RatatuiSymbolFamily::Shade,
];

/// Run the capability parity gate for the current framework baseline.
///
/// Returns which widgets and symbols still lack registration/mapping so
/// callers can determine if new Studio controls should be blocked.
#[must_use]
pub(crate) fn check_parity() -> ParityCheckResult {
    let snapshot = current_capability_snapshot();

    let unregistered_widgets: Vec<&'static str> = snapshot
        .ratatui_widgets
        .iter()
        .filter(|w| !REGISTERED_WIDGET_STYLE_IDS.contains(w))
        .map(|w| w.name())
        .collect();

    let unmapped_symbols: Vec<&'static str> = snapshot
        .ratatui_symbols
        .iter()
        .filter(|s| !MAPPED_SYMBOL_FAMILIES.contains(s))
        .map(|s| s.name())
        .collect();

    let passed = unregistered_widgets.is_empty() && unmapped_symbols.is_empty();

    ParityCheckResult {
        unregistered_widgets,
        unmapped_symbols,
        passed,
    }
}

/// Validate that a theme's capabilities are compatible with the current
/// framework baseline. Returns `true` if the theme does not require any
/// capability that is missing from the snapshot.
#[must_use]
pub(crate) fn theme_capability_compatible(theme: Theme) -> bool {
    // Truecolor themes require the truecolor crossterm capability.
    // Non-truecolor themes work with any color depth.
    if theme.is_truecolor() {
        return CrosstermCapability::all().contains(&CrosstermCapability::TrueColor);
    }
    true
}

// ---------------------------------------------------------------------------
// Upgrade delta tracking
// ---------------------------------------------------------------------------

/// Represents a capability delta between two framework versions.
#[derive(Debug, Clone, PartialEq, Eq)]
pub(crate) struct UpgradeDelta {
    pub(crate) added_widgets: Vec<&'static str>,
    pub(crate) removed_widgets: Vec<&'static str>,
    pub(crate) added_symbols: Vec<&'static str>,
    pub(crate) removed_symbols: Vec<&'static str>,
    pub(crate) added_capabilities: Vec<&'static str>,
    pub(crate) removed_capabilities: Vec<&'static str>,
}

impl UpgradeDelta {
    /// Check if the delta introduces any breaking changes.
    #[must_use]
    pub(crate) fn has_breaking_changes(&self) -> bool {
        !self.removed_widgets.is_empty()
            || !self.removed_symbols.is_empty()
            || !self.removed_capabilities.is_empty()
    }

    /// Check if the delta is empty (no changes).
    #[must_use]
    pub(crate) fn is_empty(&self) -> bool {
        self.added_widgets.is_empty()
            && self.removed_widgets.is_empty()
            && self.added_symbols.is_empty()
            && self.removed_symbols.is_empty()
            && self.added_capabilities.is_empty()
            && self.removed_capabilities.is_empty()
    }
}

/// Compute the delta between two capability snapshots.
#[must_use]
pub(crate) fn compute_upgrade_delta(
    from: &FrameworkCapabilitySnapshot,
    to: &FrameworkCapabilitySnapshot,
) -> UpgradeDelta {
    let added_widgets: Vec<&'static str> = to
        .ratatui_widgets
        .iter()
        .filter(|w| !from.ratatui_widgets.contains(w))
        .map(|w| w.name())
        .collect();

    let removed_widgets: Vec<&'static str> = from
        .ratatui_widgets
        .iter()
        .filter(|w| !to.ratatui_widgets.contains(w))
        .map(|w| w.name())
        .collect();

    let added_symbols: Vec<&'static str> = to
        .ratatui_symbols
        .iter()
        .filter(|s| !from.ratatui_symbols.contains(s))
        .map(|s| s.name())
        .collect();

    let removed_symbols: Vec<&'static str> = from
        .ratatui_symbols
        .iter()
        .filter(|s| !to.ratatui_symbols.contains(s))
        .map(|s| s.name())
        .collect();

    let added_capabilities: Vec<&'static str> = to
        .crossterm_capabilities
        .iter()
        .filter(|c| !from.crossterm_capabilities.contains(c))
        .map(|c| c.name())
        .collect();

    let removed_capabilities: Vec<&'static str> = from
        .crossterm_capabilities
        .iter()
        .filter(|c| !to.crossterm_capabilities.contains(c))
        .map(|c| c.name())
        .collect();

    UpgradeDelta {
        added_widgets,
        removed_widgets,
        added_symbols,
        removed_symbols,
        added_capabilities,
        removed_capabilities,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn current_snapshot_has_pinned_versions() {
        let snap = current_capability_snapshot();
        assert_eq!(snap.ratatui_version, "0.26");
        assert_eq!(snap.crossterm_version, "0.27");
    }

    #[test]
    fn current_snapshot_lists_all_widget_families() {
        let snap = current_capability_snapshot();
        assert_eq!(snap.ratatui_widgets.len(), RatatuiWidget::all().len());
        for w in RatatuiWidget::all() {
            assert!(snap.ratatui_widgets.contains(w), "missing widget: {}", w.name());
        }
    }

    #[test]
    fn current_snapshot_lists_all_symbol_families() {
        let snap = current_capability_snapshot();
        assert_eq!(snap.ratatui_symbols.len(), RatatuiSymbolFamily::all().len());
        for s in RatatuiSymbolFamily::all() {
            assert!(snap.ratatui_symbols.contains(s), "missing symbol: {}", s.name());
        }
    }

    #[test]
    fn current_snapshot_lists_all_crossterm_capabilities() {
        let snap = current_capability_snapshot();
        assert_eq!(
            snap.crossterm_capabilities.len(),
            CrosstermCapability::all().len()
        );
        for c in CrosstermCapability::all() {
            assert!(
                snap.crossterm_capabilities.contains(c),
                "missing capability: {}",
                c.name()
            );
        }
    }

    #[test]
    fn parity_gate_detects_unregistered_widgets() {
        let result = check_parity();
        // Canvas and Calendar are not yet in REGISTERED_WIDGET_STYLE_IDS.
        assert!(
            result.unregistered_widgets.contains(&"Canvas"),
            "Canvas should be unregistered: {:?}",
            result.unregistered_widgets
        );
        assert!(
            result.unregistered_widgets.contains(&"Calendar"),
            "Calendar should be unregistered: {:?}",
            result.unregistered_widgets
        );
    }

    #[test]
    fn parity_gate_detects_unmapped_symbols() {
        let result = check_parity();
        // Marker is not yet in MAPPED_SYMBOL_FAMILIES.
        assert!(
            result.unmapped_symbols.contains(&"marker"),
            "marker should be unmapped: {:?}",
            result.unmapped_symbols
        );
    }

    #[test]
    fn parity_gate_fails_when_gaps_exist() {
        let result = check_parity();
        assert!(
            !result.passed,
            "parity gate should fail with known gaps"
        );
    }

    #[test]
    fn theme_capability_compatible_truecolor_themes() {
        assert!(theme_capability_compatible(Theme::Codex));
        assert!(theme_capability_compatible(Theme::Claude));
        assert!(theme_capability_compatible(Theme::Dracula));
    }

    #[test]
    fn theme_capability_compatible_non_truecolor_themes() {
        assert!(theme_capability_compatible(Theme::Coral));
        assert!(theme_capability_compatible(Theme::Ansi));
        assert!(theme_capability_compatible(Theme::None));
    }

    #[test]
    fn upgrade_delta_same_snapshot_is_empty() {
        let snap = current_capability_snapshot();
        let delta = compute_upgrade_delta(&snap, &snap);
        assert!(delta.is_empty());
        assert!(!delta.has_breaking_changes());
    }

    #[test]
    fn upgrade_delta_detects_added_widgets() {
        let from = FrameworkCapabilitySnapshot {
            ratatui_version: "0.25",
            crossterm_version: "0.27",
            ratatui_widgets: &[RatatuiWidget::Block, RatatuiWidget::Paragraph],
            ratatui_symbols: RatatuiSymbolFamily::all(),
            crossterm_capabilities: CrosstermCapability::all(),
        };
        let to = current_capability_snapshot();
        let delta = compute_upgrade_delta(&from, &to);
        assert!(!delta.added_widgets.is_empty());
        assert!(!delta.is_empty());
    }

    #[test]
    fn upgrade_delta_detects_removed_widgets_as_breaking() {
        let to = FrameworkCapabilitySnapshot {
            ratatui_version: "0.27",
            crossterm_version: "0.28",
            ratatui_widgets: &[RatatuiWidget::Block],
            ratatui_symbols: RatatuiSymbolFamily::all(),
            crossterm_capabilities: CrosstermCapability::all(),
        };
        let from = current_capability_snapshot();
        let delta = compute_upgrade_delta(&from, &to);
        assert!(delta.has_breaking_changes());
        assert!(!delta.removed_widgets.is_empty());
    }

    #[test]
    fn widget_names_are_non_empty() {
        for w in RatatuiWidget::all() {
            assert!(!w.name().is_empty());
        }
    }

    #[test]
    fn symbol_family_names_are_non_empty() {
        for s in RatatuiSymbolFamily::all() {
            assert!(!s.name().is_empty());
        }
    }

    #[test]
    fn crossterm_capability_names_are_non_empty() {
        for c in CrosstermCapability::all() {
            assert!(!c.name().is_empty());
        }
    }

    #[test]
    fn snapshot_equality() {
        let a = current_capability_snapshot();
        let b = current_capability_snapshot();
        assert_eq!(a, b);
    }

    #[test]
    fn upgrade_delta_detects_removed_capabilities() {
        let from = current_capability_snapshot();
        let to = FrameworkCapabilitySnapshot {
            ratatui_version: "0.27",
            crossterm_version: "0.28",
            ratatui_widgets: RatatuiWidget::all(),
            ratatui_symbols: RatatuiSymbolFamily::all(),
            crossterm_capabilities: &[CrosstermCapability::TrueColor],
        };
        let delta = compute_upgrade_delta(&from, &to);
        assert!(delta.has_breaking_changes());
        assert!(!delta.removed_capabilities.is_empty());
    }
}
