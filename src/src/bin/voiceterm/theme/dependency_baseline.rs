//! Dependency baseline strategy for Theme Studio ecosystem packs (MP-179).
//!
//! Enforces Ratatui/Crossterm version pin policy, compatibility matrix, and
//! staged upgrade plan so third-party widget adoption does not fragment
//! resolver/studio parity.
//!
//! Gate evidence: TS-G15 (ecosystem packs).

// ---------------------------------------------------------------------------
// Version pin policy
// ---------------------------------------------------------------------------

/// Pinned dependency version with compatibility bounds.
#[derive(Debug, Clone, PartialEq, Eq)]
pub(crate) struct DependencyPin {
    /// Crate name.
    pub(crate) name: &'static str,
    /// Pinned version string (from Cargo.toml).
    pub(crate) pinned_version: &'static str,
    /// Minimum compatible version for ecosystem packs.
    pub(crate) min_compatible: &'static str,
    /// Maximum compatible version (exclusive upper bound).
    pub(crate) max_compatible: &'static str,
    /// Whether default features are disabled.
    pub(crate) no_default_features: bool,
    /// Explicit features enabled.
    pub(crate) features: &'static [&'static str],
}

/// Core framework dependency pins for the current release.
pub(crate) const RATATUI_PIN: DependencyPin = DependencyPin {
    name: "ratatui",
    pinned_version: "0.26",
    min_compatible: "0.26.0",
    max_compatible: "0.27.0",
    no_default_features: true,
    features: &["crossterm"],
};

pub(crate) const CROSSTERM_PIN: DependencyPin = DependencyPin {
    name: "crossterm",
    pinned_version: "0.27",
    min_compatible: "0.27.0",
    max_compatible: "0.28.0",
    no_default_features: false,
    features: &[],
};

/// All core framework pins.
pub(crate) const CORE_PINS: &[&DependencyPin] = &[&RATATUI_PIN, &CROSSTERM_PIN];

// ---------------------------------------------------------------------------
// Compatibility matrix
// ---------------------------------------------------------------------------

/// Compatibility status of a third-party crate against core pins.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub(crate) enum CompatibilityStatus {
    /// Fully compatible with pinned versions.
    Compatible,
    /// Compatible but requires version constraint (e.g., specific feature flag).
    ConditionallyCompatible,
    /// Incompatible with current pins (requires upgrade first).
    Incompatible,
    /// Not yet evaluated.
    Unknown,
}

impl CompatibilityStatus {
    /// Human-readable label.
    #[must_use]
    pub(crate) const fn label(&self) -> &'static str {
        match self {
            Self::Compatible => "compatible",
            Self::ConditionallyCompatible => "conditionally-compatible",
            Self::Incompatible => "incompatible",
            Self::Unknown => "unknown",
        }
    }

    /// Whether this status allows widget-pack adoption.
    #[must_use]
    pub(crate) const fn allows_adoption(&self) -> bool {
        matches!(self, Self::Compatible | Self::ConditionallyCompatible)
    }
}

/// Compatibility matrix entry for a third-party crate.
#[derive(Debug, Clone, PartialEq, Eq)]
pub(crate) struct CompatibilityEntry {
    /// Crate name.
    pub(crate) crate_name: &'static str,
    /// Evaluated version range.
    pub(crate) version_range: &'static str,
    /// Status against ratatui pin.
    pub(crate) ratatui_compat: CompatibilityStatus,
    /// Status against crossterm pin.
    pub(crate) crossterm_compat: CompatibilityStatus,
    /// Notes for maintainers.
    pub(crate) notes: &'static str,
}

impl CompatibilityEntry {
    /// Overall compatibility (both core deps must allow adoption).
    #[must_use]
    pub(crate) fn overall_status(&self) -> CompatibilityStatus {
        if self.ratatui_compat == CompatibilityStatus::Incompatible
            || self.crossterm_compat == CompatibilityStatus::Incompatible
        {
            return CompatibilityStatus::Incompatible;
        }
        if self.ratatui_compat == CompatibilityStatus::Unknown
            || self.crossterm_compat == CompatibilityStatus::Unknown
        {
            return CompatibilityStatus::Unknown;
        }
        if self.ratatui_compat == CompatibilityStatus::ConditionallyCompatible
            || self.crossterm_compat == CompatibilityStatus::ConditionallyCompatible
        {
            return CompatibilityStatus::ConditionallyCompatible;
        }
        CompatibilityStatus::Compatible
    }
}

/// Pre-evaluated compatibility matrix for candidate widget-pack crates.
///
/// Each entry is evaluated against the pinned ratatui/crossterm versions.
/// Entries marked `Compatible` can be adopted under widget-pack allowlist
/// gates (MP-180). Entries marked `Incompatible` are blocked until the
/// staged upgrade plan resolves the version conflict.
pub(crate) const COMPATIBILITY_MATRIX: &[CompatibilityEntry] = &[
    CompatibilityEntry {
        crate_name: "tui-textarea",
        version_range: ">=0.4,<0.7",
        ratatui_compat: CompatibilityStatus::Compatible,
        crossterm_compat: CompatibilityStatus::Compatible,
        notes: "0.4.x series targets ratatui 0.26; 0.7+ requires ratatui >=0.28",
    },
    CompatibilityEntry {
        crate_name: "tui-tree-widget",
        version_range: ">=0.19,<0.22",
        ratatui_compat: CompatibilityStatus::Compatible,
        crossterm_compat: CompatibilityStatus::Compatible,
        notes: "0.19-0.21 series targets ratatui 0.26",
    },
    CompatibilityEntry {
        crate_name: "throbber-widgets-tui",
        version_range: ">=0.6,<0.8",
        ratatui_compat: CompatibilityStatus::Compatible,
        crossterm_compat: CompatibilityStatus::Compatible,
        notes: "0.6-0.7 series compatible with ratatui 0.26",
    },
    CompatibilityEntry {
        crate_name: "tui-popup",
        version_range: ">=0.3,<0.5",
        ratatui_compat: CompatibilityStatus::Compatible,
        crossterm_compat: CompatibilityStatus::Compatible,
        notes: "tui-widgets family; 0.3-0.4 targets ratatui 0.26",
    },
    CompatibilityEntry {
        crate_name: "tui-scrollview",
        version_range: ">=0.3,<0.5",
        ratatui_compat: CompatibilityStatus::Compatible,
        crossterm_compat: CompatibilityStatus::Compatible,
        notes: "tui-widgets family; 0.3-0.4 targets ratatui 0.26",
    },
    CompatibilityEntry {
        crate_name: "tui-big-text",
        version_range: ">=0.4,<0.6",
        ratatui_compat: CompatibilityStatus::Compatible,
        crossterm_compat: CompatibilityStatus::Compatible,
        notes: "tui-widgets family; 0.4-0.5 targets ratatui 0.26",
    },
    CompatibilityEntry {
        crate_name: "tui-prompts",
        version_range: ">=0.3,<0.5",
        ratatui_compat: CompatibilityStatus::Compatible,
        crossterm_compat: CompatibilityStatus::Compatible,
        notes: "tui-widgets family; 0.3-0.4 targets ratatui 0.26",
    },
    CompatibilityEntry {
        crate_name: "ratatui-image",
        version_range: ">=1.0,<2.0",
        ratatui_compat: CompatibilityStatus::ConditionallyCompatible,
        crossterm_compat: CompatibilityStatus::Compatible,
        notes: "requires feature-gated image protocol; verify ratatui 0.26 compat per release",
    },
    CompatibilityEntry {
        crate_name: "tuirealm",
        version_range: ">=1.9,<2.0",
        ratatui_compat: CompatibilityStatus::Incompatible,
        crossterm_compat: CompatibilityStatus::Incompatible,
        notes: "heavy framework with own event model; deferred until architectural decision",
    },
];

// ---------------------------------------------------------------------------
// Staged upgrade plan
// ---------------------------------------------------------------------------

/// An upgrade step in the staged plan.
#[derive(Debug, Clone, PartialEq, Eq)]
pub(crate) struct UpgradeStep {
    /// Crate being upgraded.
    pub(crate) crate_name: &'static str,
    /// Target version.
    pub(crate) target_version: &'static str,
    /// Prerequisites that must be complete first.
    pub(crate) prerequisites: &'static [&'static str],
    /// Validation steps.
    pub(crate) validation: &'static [&'static str],
}

/// Staged upgrade plan for moving to newer framework versions.
///
/// This plan ensures that each upgrade step is validated before proceeding,
/// and that ecosystem-pack compatibility is re-verified at each stage.
pub(crate) const STAGED_UPGRADE_PLAN: &[UpgradeStep] = &[
    UpgradeStep {
        crate_name: "crossterm",
        target_version: "0.28",
        prerequisites: &[
            "audit crossterm 0.28 changelog for breaking input/event changes",
            "verify keyboard enhancement flag compatibility",
            "verify synchronized update compatibility",
        ],
        validation: &[
            "cargo test --bin voiceterm",
            "devctl check --profile ci",
            "re-run terminal compatibility matrix tests",
        ],
    },
    UpgradeStep {
        crate_name: "ratatui",
        target_version: "0.27",
        prerequisites: &[
            "crossterm upgrade to 0.28 must land first",
            "audit ratatui 0.27 changelog for widget API changes",
            "verify symbol family backward compatibility",
            "update capability_matrix.rs snapshot",
        ],
        validation: &[
            "cargo test --bin voiceterm",
            "devctl check --profile ci",
            "re-run capability parity gate",
            "re-evaluate COMPATIBILITY_MATRIX entries",
        ],
    },
];

// ---------------------------------------------------------------------------
// Policy checks
// ---------------------------------------------------------------------------

/// Check if a crate at a given version is compatible with current pins.
///
/// Returns the matching compatibility entry if one exists.
#[must_use]
pub(crate) fn check_crate_compatibility(crate_name: &str) -> Option<&'static CompatibilityEntry> {
    COMPATIBILITY_MATRIX
        .iter()
        .find(|entry| entry.crate_name == crate_name)
}

/// Check if all proposed widget-pack dependencies are compatible.
///
/// Returns the list of crate names that fail compatibility.
#[must_use]
pub(crate) fn check_pack_compatibility<'a>(crate_names: &'a [&'a str]) -> Vec<&'a str> {
    crate_names
        .iter()
        .copied()
        .filter(|name| {
            check_crate_compatibility(name)
                .map(|entry| !entry.overall_status().allows_adoption())
                .unwrap_or(true) // Unknown crates are blocked
        })
        .collect()
}

/// Validate that a dependency pin matches the expected Cargo.toml version.
///
/// This is a static assertion helper for CI/test use.
#[must_use]
pub(crate) fn validate_pin_against_cargo(
    pin: &DependencyPin,
    cargo_version: &str,
) -> bool {
    cargo_version.starts_with(pin.pinned_version)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn core_pins_include_ratatui_and_crossterm() {
        let names: Vec<&str> = CORE_PINS.iter().map(|p| p.name).collect();
        assert!(names.contains(&"ratatui"));
        assert!(names.contains(&"crossterm"));
    }

    #[test]
    fn ratatui_pin_matches_cargo_toml_version() {
        // The Cargo.toml pins ratatui = "0.26".
        assert!(validate_pin_against_cargo(&RATATUI_PIN, "0.26"));
        assert!(!validate_pin_against_cargo(&RATATUI_PIN, "0.27"));
    }

    #[test]
    fn crossterm_pin_matches_cargo_toml_version() {
        // The Cargo.toml pins crossterm = "0.27".
        assert!(validate_pin_against_cargo(&CROSSTERM_PIN, "0.27"));
        assert!(!validate_pin_against_cargo(&CROSSTERM_PIN, "0.28"));
    }

    #[test]
    fn compatibility_matrix_has_entries() {
        assert!(
            !COMPATIBILITY_MATRIX.is_empty(),
            "compatibility matrix should not be empty"
        );
    }

    #[test]
    fn compatible_entries_allow_adoption() {
        for entry in COMPATIBILITY_MATRIX {
            if entry.overall_status() == CompatibilityStatus::Compatible {
                assert!(
                    entry.overall_status().allows_adoption(),
                    "{} should allow adoption",
                    entry.crate_name
                );
            }
        }
    }

    #[test]
    fn incompatible_entries_block_adoption() {
        for entry in COMPATIBILITY_MATRIX {
            if entry.overall_status() == CompatibilityStatus::Incompatible {
                assert!(
                    !entry.overall_status().allows_adoption(),
                    "{} should block adoption",
                    entry.crate_name
                );
            }
        }
    }

    #[test]
    fn check_crate_compatibility_finds_known_crates() {
        assert!(check_crate_compatibility("tui-textarea").is_some());
        assert!(check_crate_compatibility("tui-tree-widget").is_some());
        assert!(check_crate_compatibility("throbber-widgets-tui").is_some());
    }

    #[test]
    fn check_crate_compatibility_returns_none_for_unknown() {
        assert!(check_crate_compatibility("nonexistent-crate").is_none());
    }

    #[test]
    fn check_pack_compatibility_blocks_incompatible_crates() {
        let blocked = check_pack_compatibility(&["tui-textarea", "tuirealm"]);
        assert!(
            blocked.contains(&"tuirealm"),
            "tuirealm should be blocked: {:?}",
            blocked
        );
        assert!(
            !blocked.contains(&"tui-textarea"),
            "tui-textarea should not be blocked: {:?}",
            blocked
        );
    }

    #[test]
    fn check_pack_compatibility_blocks_unknown_crates() {
        let blocked = check_pack_compatibility(&["unknown-widget-crate"]);
        assert!(blocked.contains(&"unknown-widget-crate"));
    }

    #[test]
    fn staged_upgrade_plan_has_steps() {
        assert!(!STAGED_UPGRADE_PLAN.is_empty());
    }

    #[test]
    fn staged_upgrade_plan_crossterm_before_ratatui() {
        let crossterm_idx = STAGED_UPGRADE_PLAN
            .iter()
            .position(|s| s.crate_name == "crossterm")
            .expect("crossterm step exists");
        let ratatui_idx = STAGED_UPGRADE_PLAN
            .iter()
            .position(|s| s.crate_name == "ratatui")
            .expect("ratatui step exists");
        assert!(
            crossterm_idx < ratatui_idx,
            "crossterm upgrade must precede ratatui upgrade"
        );
    }

    #[test]
    fn ratatui_upgrade_prerequisites_reference_crossterm() {
        let ratatui_step = STAGED_UPGRADE_PLAN
            .iter()
            .find(|s| s.crate_name == "ratatui")
            .expect("ratatui step exists");
        let has_crossterm_prereq = ratatui_step
            .prerequisites
            .iter()
            .any(|p| p.to_lowercase().contains("crossterm"));
        assert!(
            has_crossterm_prereq,
            "ratatui upgrade must reference crossterm as prerequisite"
        );
    }

    #[test]
    fn compatibility_status_labels_are_non_empty() {
        let statuses = [
            CompatibilityStatus::Compatible,
            CompatibilityStatus::ConditionallyCompatible,
            CompatibilityStatus::Incompatible,
            CompatibilityStatus::Unknown,
        ];
        for status in &statuses {
            assert!(!status.label().is_empty());
        }
    }

    #[test]
    fn overall_status_incompatible_when_either_dep_incompatible() {
        let entry = CompatibilityEntry {
            crate_name: "test",
            version_range: ">=1.0",
            ratatui_compat: CompatibilityStatus::Compatible,
            crossterm_compat: CompatibilityStatus::Incompatible,
            notes: "",
        };
        assert_eq!(entry.overall_status(), CompatibilityStatus::Incompatible);
    }

    #[test]
    fn overall_status_unknown_when_either_dep_unknown() {
        let entry = CompatibilityEntry {
            crate_name: "test",
            version_range: ">=1.0",
            ratatui_compat: CompatibilityStatus::Compatible,
            crossterm_compat: CompatibilityStatus::Unknown,
            notes: "",
        };
        assert_eq!(entry.overall_status(), CompatibilityStatus::Unknown);
    }

    #[test]
    fn overall_status_conditionally_compatible_propagates() {
        let entry = CompatibilityEntry {
            crate_name: "test",
            version_range: ">=1.0",
            ratatui_compat: CompatibilityStatus::ConditionallyCompatible,
            crossterm_compat: CompatibilityStatus::Compatible,
            notes: "",
        };
        assert_eq!(
            entry.overall_status(),
            CompatibilityStatus::ConditionallyCompatible
        );
    }

    #[test]
    fn dependency_pin_features_match_cargo_toml() {
        assert_eq!(RATATUI_PIN.features, &["crossterm"]);
        assert!(RATATUI_PIN.no_default_features);
        assert!(!CROSSTERM_PIN.no_default_features);
    }

    #[test]
    fn tui_widgets_family_entries_are_compatible() {
        let tui_widgets_crates = [
            "tui-popup",
            "tui-scrollview",
            "tui-big-text",
            "tui-prompts",
        ];
        for crate_name in &tui_widgets_crates {
            let entry = check_crate_compatibility(crate_name)
                .unwrap_or_else(|| panic!("{crate_name} should be in compatibility matrix"));
            assert!(
                entry.overall_status().allows_adoption(),
                "{crate_name} should be adoptable"
            );
        }
    }
}
