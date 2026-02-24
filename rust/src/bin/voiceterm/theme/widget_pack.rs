//! Curated widget-pack integration lane (MP-180).
//!
//! Implements a style-ID/allowlist-gated widget-pack system for curated
//! third-party widgets (tui-widgets family, tui-textarea, tui-tree-widget,
//! throbber-widgets-tui), with parity tests before feature flags graduate.
//!
//! Gate evidence: TS-G15 (ecosystem packs), TS-G05 (studio controls),
//! TS-G06 (snapshot matrix).

// ---------------------------------------------------------------------------
// Widget pack registry
// ---------------------------------------------------------------------------

/// Integration maturity level for a widget pack.
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord)]
pub(crate) enum PackMaturity {
    /// Evaluated but not yet integrated.
    Candidate,
    /// Integrated behind a feature flag; parity tests required before graduation.
    Pilot,
    /// Passed parity tests; feature flag removed; available in release builds.
    Graduated,
    /// Removed or superseded.
    Retired,
}

impl PackMaturity {
    /// Human-readable label.
    #[must_use]
    pub(crate) const fn label(&self) -> &'static str {
        match self {
            Self::Candidate => "candidate",
            Self::Pilot => "pilot",
            Self::Graduated => "graduated",
            Self::Retired => "retired",
        }
    }

    /// Whether this maturity level allows runtime use.
    #[must_use]
    pub(crate) const fn is_active(&self) -> bool {
        matches!(self, Self::Pilot | Self::Graduated)
    }
}

/// Style-ID scope for a widget pack.
///
/// Each widget pack gets a namespace prefix for its style IDs so there are
/// no collisions with core style IDs or other packs.
#[derive(Debug, Clone, PartialEq, Eq)]
pub(crate) struct StyleIdScope {
    /// Namespace prefix (e.g., "pack.tui-textarea").
    pub(crate) prefix: &'static str,
    /// Style IDs registered under this scope.
    pub(crate) ids: &'static [&'static str],
}

/// Widget pack registration entry.
#[derive(Debug, Clone, PartialEq, Eq)]
pub(crate) struct WidgetPackEntry {
    /// Crate name (must match dependency_baseline compatibility matrix).
    pub(crate) crate_name: &'static str,
    /// Human-readable display name.
    pub(crate) display_name: &'static str,
    /// Current maturity level.
    pub(crate) maturity: PackMaturity,
    /// Style-ID scope for this pack.
    pub(crate) style_scope: StyleIdScope,
    /// Parity requirements that must pass before graduation.
    pub(crate) parity_requirements: &'static [ParityRequirement],
}

/// A parity requirement that must pass before a widget pack graduates.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub(crate) enum ParityRequirement {
    /// All style IDs must be registered in the component registry.
    StyleIdRegistration,
    /// All style IDs must have resolver bindings.
    ResolverBinding,
    /// All style IDs must have Studio control mappings.
    StudioControlMapping,
    /// Snapshot tests must cover default + focused + selected states.
    SnapshotCoverage,
    /// Accessibility fallback (ASCII-safe rendering) must work.
    AccessibilityFallback,
}

impl ParityRequirement {
    /// Human-readable label.
    #[must_use]
    pub(crate) const fn label(&self) -> &'static str {
        match self {
            Self::StyleIdRegistration => "style-id-registration",
            Self::ResolverBinding => "resolver-binding",
            Self::StudioControlMapping => "studio-control-mapping",
            Self::SnapshotCoverage => "snapshot-coverage",
            Self::AccessibilityFallback => "accessibility-fallback",
        }
    }
}

// ---------------------------------------------------------------------------
// Allowlist registry
// ---------------------------------------------------------------------------

/// All registered widget packs in the system.
pub(crate) const WIDGET_PACK_REGISTRY: &[WidgetPackEntry] = &[
    WidgetPackEntry {
        crate_name: "tui-textarea",
        display_name: "Text Area",
        maturity: PackMaturity::Pilot,
        style_scope: StyleIdScope {
            prefix: "pack.tui-textarea",
            ids: &[
                "pack.tui-textarea.editor",
                "pack.tui-textarea.editor.focused",
                "pack.tui-textarea.editor.disabled",
                "pack.tui-textarea.line-numbers",
                "pack.tui-textarea.cursor",
                "pack.tui-textarea.selection",
            ],
        },
        parity_requirements: &[
            ParityRequirement::StyleIdRegistration,
            ParityRequirement::ResolverBinding,
            ParityRequirement::StudioControlMapping,
            ParityRequirement::SnapshotCoverage,
            ParityRequirement::AccessibilityFallback,
        ],
    },
    WidgetPackEntry {
        crate_name: "tui-tree-widget",
        display_name: "Tree View",
        maturity: PackMaturity::Pilot,
        style_scope: StyleIdScope {
            prefix: "pack.tui-tree-widget",
            ids: &[
                "pack.tui-tree-widget.node",
                "pack.tui-tree-widget.node.focused",
                "pack.tui-tree-widget.node.selected",
                "pack.tui-tree-widget.node.expanded",
                "pack.tui-tree-widget.node.collapsed",
                "pack.tui-tree-widget.indent-guide",
            ],
        },
        parity_requirements: &[
            ParityRequirement::StyleIdRegistration,
            ParityRequirement::ResolverBinding,
            ParityRequirement::StudioControlMapping,
            ParityRequirement::SnapshotCoverage,
        ],
    },
    WidgetPackEntry {
        crate_name: "throbber-widgets-tui",
        display_name: "Throbber / Spinner",
        maturity: PackMaturity::Pilot,
        style_scope: StyleIdScope {
            prefix: "pack.throbber",
            ids: &[
                "pack.throbber.spinner",
                "pack.throbber.spinner.active",
                "pack.throbber.spinner.complete",
                "pack.throbber.label",
            ],
        },
        parity_requirements: &[
            ParityRequirement::StyleIdRegistration,
            ParityRequirement::ResolverBinding,
            ParityRequirement::SnapshotCoverage,
        ],
    },
    WidgetPackEntry {
        crate_name: "tui-popup",
        display_name: "Popup",
        maturity: PackMaturity::Candidate,
        style_scope: StyleIdScope {
            prefix: "pack.tui-popup",
            ids: &[
                "pack.tui-popup.frame",
                "pack.tui-popup.title",
                "pack.tui-popup.content",
                "pack.tui-popup.backdrop",
            ],
        },
        parity_requirements: &[
            ParityRequirement::StyleIdRegistration,
            ParityRequirement::ResolverBinding,
            ParityRequirement::StudioControlMapping,
            ParityRequirement::SnapshotCoverage,
        ],
    },
    WidgetPackEntry {
        crate_name: "tui-scrollview",
        display_name: "Scroll View",
        maturity: PackMaturity::Candidate,
        style_scope: StyleIdScope {
            prefix: "pack.tui-scrollview",
            ids: &[
                "pack.tui-scrollview.content",
                "pack.tui-scrollview.scrollbar",
                "pack.tui-scrollview.scrollbar.thumb",
            ],
        },
        parity_requirements: &[
            ParityRequirement::StyleIdRegistration,
            ParityRequirement::ResolverBinding,
            ParityRequirement::SnapshotCoverage,
        ],
    },
    WidgetPackEntry {
        crate_name: "tui-big-text",
        display_name: "Big Text",
        maturity: PackMaturity::Candidate,
        style_scope: StyleIdScope {
            prefix: "pack.tui-big-text",
            ids: &["pack.tui-big-text.text", "pack.tui-big-text.text.accent"],
        },
        parity_requirements: &[
            ParityRequirement::StyleIdRegistration,
            ParityRequirement::ResolverBinding,
            ParityRequirement::SnapshotCoverage,
        ],
    },
];

// ---------------------------------------------------------------------------
// Allowlist queries
// ---------------------------------------------------------------------------

/// Look up a widget pack by crate name.
#[must_use]
pub(crate) fn find_pack(crate_name: &str) -> Option<&'static WidgetPackEntry> {
    WIDGET_PACK_REGISTRY
        .iter()
        .find(|entry| entry.crate_name == crate_name)
}

/// Return all packs at or above a given maturity level.
#[must_use]
pub(crate) fn packs_at_maturity(min_maturity: PackMaturity) -> Vec<&'static WidgetPackEntry> {
    WIDGET_PACK_REGISTRY
        .iter()
        .filter(|entry| entry.maturity >= min_maturity)
        .collect()
}

/// Return all active packs (Pilot or Graduated).
#[must_use]
pub(crate) fn active_packs() -> Vec<&'static WidgetPackEntry> {
    WIDGET_PACK_REGISTRY
        .iter()
        .filter(|entry| entry.maturity.is_active())
        .collect()
}

/// Check if a style ID belongs to a registered widget pack.
#[must_use]
pub(crate) fn style_id_is_pack_owned(style_id: &str) -> bool {
    WIDGET_PACK_REGISTRY
        .iter()
        .any(|entry| style_id.starts_with(entry.style_scope.prefix))
}

/// Return the owning pack for a style ID, if any.
#[must_use]
pub(crate) fn owning_pack_for_style_id(style_id: &str) -> Option<&'static WidgetPackEntry> {
    WIDGET_PACK_REGISTRY
        .iter()
        .find(|entry| style_id.starts_with(entry.style_scope.prefix))
}

// ---------------------------------------------------------------------------
// Graduation gate
// ---------------------------------------------------------------------------

/// Result of a graduation check for a widget pack.
#[derive(Debug, Clone, PartialEq, Eq)]
pub(crate) struct GraduationCheckResult {
    pub(crate) crate_name: &'static str,
    pub(crate) current_maturity: PackMaturity,
    /// Requirements that are not yet met.
    pub(crate) unmet_requirements: Vec<&'static str>,
    /// Whether the pack can graduate.
    pub(crate) can_graduate: bool,
}

/// Check if a pilot-stage widget pack can graduate to released status.
///
/// In this initial implementation, graduation requires that the pack is at
/// Pilot maturity and has no unmet parity requirements. The actual parity
/// test results would be supplied by CI; here we check structural readiness.
#[must_use]
pub(crate) fn check_graduation(crate_name: &str) -> GraduationCheckResult {
    let Some(pack) = find_pack(crate_name) else {
        return GraduationCheckResult {
            crate_name: "unknown",
            current_maturity: PackMaturity::Candidate,
            unmet_requirements: vec!["pack not found in registry"],
            can_graduate: false,
        };
    };

    if pack.maturity != PackMaturity::Pilot {
        return GraduationCheckResult {
            crate_name: pack.crate_name,
            current_maturity: pack.maturity,
            unmet_requirements: vec!["pack is not at pilot maturity"],
            can_graduate: false,
        };
    }

    // In a full implementation, we would check actual test results here.
    // For now, report all parity requirements as structurally unmet
    // (they need CI evidence to pass).
    let unmet: Vec<&'static str> = pack
        .parity_requirements
        .iter()
        .map(ParityRequirement::label)
        .collect();

    GraduationCheckResult {
        crate_name: pack.crate_name,
        current_maturity: pack.maturity,
        unmet_requirements: unmet.clone(),
        can_graduate: unmet.is_empty(),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn registry_has_entries() {
        assert!(
            !WIDGET_PACK_REGISTRY.is_empty(),
            "widget pack registry should not be empty"
        );
    }

    #[test]
    fn all_packs_have_non_empty_names() {
        for pack in WIDGET_PACK_REGISTRY {
            assert!(!pack.crate_name.is_empty());
            assert!(!pack.display_name.is_empty());
        }
    }

    #[test]
    fn all_packs_have_non_empty_style_scopes() {
        for pack in WIDGET_PACK_REGISTRY {
            assert!(
                !pack.style_scope.prefix.is_empty(),
                "{} has empty style scope prefix",
                pack.crate_name
            );
            assert!(
                !pack.style_scope.ids.is_empty(),
                "{} has no registered style IDs",
                pack.crate_name
            );
        }
    }

    #[test]
    fn all_style_ids_start_with_scope_prefix() {
        for pack in WIDGET_PACK_REGISTRY {
            for id in pack.style_scope.ids {
                assert!(
                    id.starts_with(pack.style_scope.prefix),
                    "style ID '{}' does not start with prefix '{}'",
                    id,
                    pack.style_scope.prefix
                );
            }
        }
    }

    #[test]
    fn style_id_scopes_do_not_overlap() {
        for (i, a) in WIDGET_PACK_REGISTRY.iter().enumerate() {
            for b in &WIDGET_PACK_REGISTRY[i + 1..] {
                assert!(
                    !a.style_scope.prefix.starts_with(b.style_scope.prefix)
                        && !b.style_scope.prefix.starts_with(a.style_scope.prefix),
                    "overlapping style scopes: '{}' and '{}'",
                    a.style_scope.prefix,
                    b.style_scope.prefix
                );
            }
        }
    }

    #[test]
    fn find_pack_returns_known_packs() {
        assert!(find_pack("tui-textarea").is_some());
        assert!(find_pack("tui-tree-widget").is_some());
        assert!(find_pack("throbber-widgets-tui").is_some());
        assert!(find_pack("tui-popup").is_some());
    }

    #[test]
    fn find_pack_returns_none_for_unknown() {
        assert!(find_pack("nonexistent-widget").is_none());
    }

    #[test]
    fn active_packs_includes_pilot_and_graduated() {
        let active = active_packs();
        for pack in &active {
            assert!(
                pack.maturity.is_active(),
                "{} should be active but is {:?}",
                pack.crate_name,
                pack.maturity
            );
        }
    }

    #[test]
    fn pilot_packs_exist_in_registry() {
        let pilots = packs_at_maturity(PackMaturity::Pilot);
        assert!(!pilots.is_empty(), "should have at least one pilot pack");
        for pack in &pilots {
            assert!(pack.maturity >= PackMaturity::Pilot);
        }
    }

    #[test]
    fn candidate_packs_exist_in_registry() {
        let candidates: Vec<_> = WIDGET_PACK_REGISTRY
            .iter()
            .filter(|p| p.maturity == PackMaturity::Candidate)
            .collect();
        assert!(
            !candidates.is_empty(),
            "should have at least one candidate pack"
        );
    }

    #[test]
    fn style_id_is_pack_owned_detects_pack_ids() {
        assert!(style_id_is_pack_owned("pack.tui-textarea.editor"));
        assert!(style_id_is_pack_owned("pack.throbber.spinner"));
        assert!(!style_id_is_pack_owned("core.status-line.recording"));
    }

    #[test]
    fn owning_pack_for_style_id_finds_correct_pack() {
        let pack = owning_pack_for_style_id("pack.tui-textarea.editor.focused");
        assert!(pack.is_some());
        assert_eq!(pack.unwrap().crate_name, "tui-textarea");
    }

    #[test]
    fn owning_pack_for_style_id_returns_none_for_core_ids() {
        assert!(owning_pack_for_style_id("core.status-line").is_none());
    }

    #[test]
    fn graduation_check_blocks_pilot_packs_with_unmet_requirements() {
        let result = check_graduation("tui-textarea");
        assert_eq!(result.current_maturity, PackMaturity::Pilot);
        assert!(!result.can_graduate);
        assert!(!result.unmet_requirements.is_empty());
    }

    #[test]
    fn graduation_check_rejects_candidate_packs() {
        let result = check_graduation("tui-popup");
        assert_eq!(result.current_maturity, PackMaturity::Candidate);
        assert!(!result.can_graduate);
    }

    #[test]
    fn graduation_check_rejects_unknown_packs() {
        let result = check_graduation("nonexistent");
        assert!(!result.can_graduate);
        assert!(result
            .unmet_requirements
            .contains(&"pack not found in registry"));
    }

    #[test]
    fn all_packs_have_parity_requirements() {
        for pack in WIDGET_PACK_REGISTRY {
            assert!(
                !pack.parity_requirements.is_empty(),
                "{} has no parity requirements",
                pack.crate_name
            );
        }
    }

    #[test]
    fn maturity_labels_are_non_empty() {
        let levels = [
            PackMaturity::Candidate,
            PackMaturity::Pilot,
            PackMaturity::Graduated,
            PackMaturity::Retired,
        ];
        for level in &levels {
            assert!(!level.label().is_empty());
        }
    }

    #[test]
    fn parity_requirement_labels_are_non_empty() {
        let reqs = [
            ParityRequirement::StyleIdRegistration,
            ParityRequirement::ResolverBinding,
            ParityRequirement::StudioControlMapping,
            ParityRequirement::SnapshotCoverage,
            ParityRequirement::AccessibilityFallback,
        ];
        for req in &reqs {
            assert!(!req.label().is_empty());
        }
    }

    #[test]
    fn maturity_ordering_is_correct() {
        assert!(PackMaturity::Candidate < PackMaturity::Pilot);
        assert!(PackMaturity::Pilot < PackMaturity::Graduated);
        assert!(PackMaturity::Graduated < PackMaturity::Retired);
    }

    #[test]
    fn pilot_and_graduated_are_active() {
        assert!(PackMaturity::Pilot.is_active());
        assert!(PackMaturity::Graduated.is_active());
        assert!(!PackMaturity::Candidate.is_active());
        assert!(!PackMaturity::Retired.is_active());
    }
}
