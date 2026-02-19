//! RuleProfile no-code visual automation (MP-182).
//!
//! Implements threshold/context/state-driven style overrides with deterministic
//! priority semantics, preview tooling support, and snapshot coverage.
//!
//! Gate evidence: TS-G14 (rule engine), TS-G05 (studio controls),
//! TS-G06 (snapshot matrix).

use serde::Deserialize;

// ---------------------------------------------------------------------------
// Rule conditions
// ---------------------------------------------------------------------------

/// A condition that determines when a style rule applies.
#[derive(Debug, Clone, PartialEq, Deserialize)]
#[serde(tag = "type", rename_all = "kebab-case")]
pub(crate) enum RuleCondition {
    /// Voice pipeline state matches.
    VoiceState { state: VoiceStateCondition },
    /// Numeric metric is within a threshold band.
    Threshold {
        metric: ThresholdMetric,
        #[serde(default)]
        min: Option<f64>,
        #[serde(default)]
        max: Option<f64>,
    },
    /// Active backend matches.
    Backend { backend: String },
    /// Terminal capability is present or absent.
    Capability { capability: String, present: bool },
    /// Color mode matches.
    ColorMode { mode: String },
    /// Boolean AND of sub-conditions (all must match).
    All { conditions: Vec<RuleCondition> },
    /// Boolean OR of sub-conditions (at least one must match).
    Any { conditions: Vec<RuleCondition> },
}

/// Voice pipeline states for condition matching.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Deserialize)]
#[serde(rename_all = "kebab-case")]
pub(crate) enum VoiceStateCondition {
    Idle,
    Listening,
    Recording,
    Processing,
    Responding,
}

impl VoiceStateCondition {
    /// Human-readable label.
    #[must_use]
    pub(crate) const fn label(&self) -> &'static str {
        match self {
            Self::Idle => "idle",
            Self::Listening => "listening",
            Self::Recording => "recording",
            Self::Processing => "processing",
            Self::Responding => "responding",
        }
    }
}

/// Metrics available for threshold conditions.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Deserialize)]
#[serde(rename_all = "kebab-case")]
pub(crate) enum ThresholdMetric {
    /// Queue depth (number of pending items).
    QueueDepth,
    /// Latency in milliseconds.
    LatencyMs,
    /// Audio level in dB.
    AudioLevelDb,
    /// Terminal width in columns.
    TerminalWidth,
    /// Terminal height in rows.
    TerminalHeight,
}

impl ThresholdMetric {
    /// Human-readable label.
    #[must_use]
    pub(crate) const fn label(&self) -> &'static str {
        match self {
            Self::QueueDepth => "queue-depth",
            Self::LatencyMs => "latency-ms",
            Self::AudioLevelDb => "audio-level-db",
            Self::TerminalWidth => "terminal-width",
            Self::TerminalHeight => "terminal-height",
        }
    }
}

// ---------------------------------------------------------------------------
// Rule actions (style overrides)
// ---------------------------------------------------------------------------

/// A style override to apply when a rule's condition matches.
#[derive(Debug, Clone, PartialEq, Deserialize)]
#[serde(rename_all = "kebab-case")]
pub(crate) struct StyleOverride {
    /// Target style ID to override (e.g., "core.status-line.recording").
    pub(crate) target_style_id: String,
    /// Override key-value pairs.
    pub(crate) overrides: Vec<OverrideEntry>,
}

/// A single key-value override entry.
#[derive(Debug, Clone, PartialEq, Deserialize)]
pub(crate) struct OverrideEntry {
    /// Property name (e.g., "fg_color", "border_style", "glyph").
    pub(crate) key: String,
    /// Property value (string representation; parsed by the resolver).
    pub(crate) value: String,
}

// ---------------------------------------------------------------------------
// Rule definition
// ---------------------------------------------------------------------------

/// A complete style rule with condition, action, and priority.
#[derive(Debug, Clone, PartialEq, Deserialize)]
pub(crate) struct StyleRule {
    /// Unique rule identifier.
    pub(crate) id: String,
    /// Human-readable label for Studio display.
    pub(crate) label: String,
    /// When this rule applies.
    pub(crate) condition: RuleCondition,
    /// What style changes to apply.
    pub(crate) style_overrides: Vec<StyleOverride>,
    /// Priority for conflict resolution (higher wins).
    pub(crate) priority: i32,
    /// Whether the rule is enabled.
    #[serde(default = "default_enabled")]
    pub(crate) enabled: bool,
}

fn default_enabled() -> bool {
    true
}

// ---------------------------------------------------------------------------
// RuleProfile
// ---------------------------------------------------------------------------

/// Collection of style rules forming a complete rule profile.
#[derive(Debug, Clone, PartialEq, Deserialize)]
pub(crate) struct RuleProfile {
    /// Profile name.
    pub(crate) name: String,
    /// Ordered list of rules.
    pub(crate) rules: Vec<StyleRule>,
}

impl RuleProfile {
    /// Create an empty rule profile.
    #[must_use]
    pub(crate) fn empty(name: &str) -> Self {
        Self {
            name: name.to_string(),
            rules: Vec::new(),
        }
    }

    /// Return only enabled rules, sorted by priority (highest first).
    #[must_use]
    pub(crate) fn active_rules(&self) -> Vec<&StyleRule> {
        let mut active: Vec<&StyleRule> = self.rules.iter().filter(|r| r.enabled).collect();
        active.sort_by(|a, b| b.priority.cmp(&a.priority));
        active
    }

    /// Add a rule. Returns `Err` if a rule with the same ID already exists.
    pub(crate) fn add_rule(&mut self, rule: StyleRule) -> Result<(), RuleProfileError> {
        if self.rules.iter().any(|r| r.id == rule.id) {
            return Err(RuleProfileError::DuplicateRuleId(rule.id));
        }
        self.rules.push(rule);
        Ok(())
    }

    /// Remove a rule by ID. Returns `Err` if not found.
    pub(crate) fn remove_rule(&mut self, rule_id: &str) -> Result<StyleRule, RuleProfileError> {
        let idx = self
            .rules
            .iter()
            .position(|r| r.id == rule_id)
            .ok_or_else(|| RuleProfileError::RuleNotFound(rule_id.to_string()))?;
        Ok(self.rules.remove(idx))
    }

    /// Toggle a rule's enabled state. Returns `Err` if not found.
    pub(crate) fn toggle_rule(&mut self, rule_id: &str) -> Result<bool, RuleProfileError> {
        let rule = self
            .rules
            .iter_mut()
            .find(|r| r.id == rule_id)
            .ok_or_else(|| RuleProfileError::RuleNotFound(rule_id.to_string()))?;
        rule.enabled = !rule.enabled;
        Ok(rule.enabled)
    }
}

/// Errors from rule profile operations.
#[derive(Debug, Clone, PartialEq, Eq)]
pub(crate) enum RuleProfileError {
    DuplicateRuleId(String),
    RuleNotFound(String),
}

impl std::fmt::Display for RuleProfileError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::DuplicateRuleId(id) => write!(f, "duplicate rule ID: {id}"),
            Self::RuleNotFound(id) => write!(f, "rule not found: {id}"),
        }
    }
}

impl std::error::Error for RuleProfileError {}

// ---------------------------------------------------------------------------
// Rule evaluation engine
// ---------------------------------------------------------------------------

/// Runtime context for rule condition evaluation.
#[derive(Debug, Clone)]
pub(crate) struct RuleEvalContext {
    pub(crate) voice_state: VoiceStateCondition,
    pub(crate) queue_depth: u32,
    pub(crate) latency_ms: f64,
    pub(crate) audio_level_db: f64,
    pub(crate) terminal_width: u16,
    pub(crate) terminal_height: u16,
    pub(crate) backend: String,
    pub(crate) capabilities: Vec<String>,
    pub(crate) color_mode: String,
}

impl Default for RuleEvalContext {
    fn default() -> Self {
        Self {
            voice_state: VoiceStateCondition::Idle,
            queue_depth: 0,
            latency_ms: 0.0,
            audio_level_db: -60.0,
            terminal_width: 80,
            terminal_height: 24,
            backend: String::new(),
            capabilities: Vec::new(),
            color_mode: "truecolor".to_string(),
        }
    }
}

/// Evaluate a rule condition against the current runtime context.
///
/// Returns `true` if the condition matches.
#[must_use]
pub(crate) fn evaluate_condition(condition: &RuleCondition, ctx: &RuleEvalContext) -> bool {
    match condition {
        RuleCondition::VoiceState { state } => ctx.voice_state == *state,
        RuleCondition::Threshold { metric, min, max } => {
            let value = match metric {
                ThresholdMetric::QueueDepth => ctx.queue_depth as f64,
                ThresholdMetric::LatencyMs => ctx.latency_ms,
                ThresholdMetric::AudioLevelDb => ctx.audio_level_db,
                ThresholdMetric::TerminalWidth => ctx.terminal_width as f64,
                ThresholdMetric::TerminalHeight => ctx.terminal_height as f64,
            };
            let above_min = min.is_none_or(|m| value >= m);
            let below_max = max.is_none_or(|m| value <= m);
            above_min && below_max
        }
        RuleCondition::Backend { backend } => ctx.backend == *backend,
        RuleCondition::Capability {
            capability,
            present,
        } => {
            let has = ctx.capabilities.iter().any(|c| c == capability);
            has == *present
        }
        RuleCondition::ColorMode { mode } => ctx.color_mode == *mode,
        RuleCondition::All { conditions } => conditions.iter().all(|c| evaluate_condition(c, ctx)),
        RuleCondition::Any { conditions } => conditions.iter().any(|c| evaluate_condition(c, ctx)),
    }
}

/// Resolved style override from rule evaluation.
///
/// Contains the winning overrides after priority-based conflict resolution.
#[derive(Debug, Clone, PartialEq)]
pub(crate) struct ResolvedOverrides {
    /// Map from style-ID to winning override entries.
    /// Uses a Vec of tuples to avoid extra dependencies.
    pub(crate) entries: Vec<(String, Vec<OverrideEntry>)>,
}

/// Evaluate all rules in a profile and return the resolved overrides.
///
/// Rules are evaluated in priority order (highest first). For each target
/// style ID, the first matching rule wins for each property key
/// (deterministic priority semantics).
#[must_use]
pub(crate) fn evaluate_rules(profile: &RuleProfile, ctx: &RuleEvalContext) -> ResolvedOverrides {
    let active = profile.active_rules();
    let mut resolved: Vec<(String, Vec<OverrideEntry>)> = Vec::new();

    for rule in active {
        if !evaluate_condition(&rule.condition, ctx) {
            continue;
        }

        for style_override in &rule.style_overrides {
            let target = &style_override.target_style_id;

            // Find or create the entry for this target.
            let entry = if let Some(pos) = resolved.iter().position(|(id, _)| id == target) {
                &mut resolved[pos].1
            } else {
                resolved.push((target.clone(), Vec::new()));
                let last = resolved.len() - 1;
                &mut resolved[last].1
            };

            // Add override entries that don't already exist (first wins).
            for override_entry in &style_override.overrides {
                if !entry.iter().any(|e| e.key == override_entry.key) {
                    entry.push(override_entry.clone());
                }
            }
        }
    }

    ResolvedOverrides { entries: resolved }
}

// ---------------------------------------------------------------------------
// Preview support
// ---------------------------------------------------------------------------

/// Preview a rule profile against a simulated context without applying.
///
/// Returns which rules would match and what overrides would result.
#[must_use]
pub(crate) fn preview_rules(profile: &RuleProfile, ctx: &RuleEvalContext) -> Vec<RulePreviewEntry> {
    profile
        .active_rules()
        .into_iter()
        .map(|rule| {
            let matches = evaluate_condition(&rule.condition, ctx);
            RulePreviewEntry {
                rule_id: rule.id.clone(),
                rule_label: rule.label.clone(),
                priority: rule.priority,
                matches,
                affected_targets: if matches {
                    rule.style_overrides
                        .iter()
                        .map(|so| so.target_style_id.clone())
                        .collect()
                } else {
                    Vec::new()
                },
            }
        })
        .collect()
}

/// Preview entry for a single rule.
#[derive(Debug, Clone, PartialEq)]
pub(crate) struct RulePreviewEntry {
    pub(crate) rule_id: String,
    pub(crate) rule_label: String,
    pub(crate) priority: i32,
    pub(crate) matches: bool,
    pub(crate) affected_targets: Vec<String>,
}

// ---------------------------------------------------------------------------
// JSON parsing
// ---------------------------------------------------------------------------

/// Parse a RuleProfile from a JSON string.
pub(crate) fn parse_rule_profile(json: &str) -> Result<RuleProfile, String> {
    serde_json::from_str(json).map_err(|e| format!("invalid rule profile JSON: {e}"))
}

#[cfg(test)]
mod tests {
    use super::*;

    fn sample_rule(id: &str, priority: i32, condition: RuleCondition) -> StyleRule {
        StyleRule {
            id: id.to_string(),
            label: format!("Test rule {id}"),
            condition,
            style_overrides: vec![StyleOverride {
                target_style_id: "core.status-line.recording".to_string(),
                overrides: vec![OverrideEntry {
                    key: "fg_color".to_string(),
                    value: "#ff0000".to_string(),
                }],
            }],
            priority,
            enabled: true,
        }
    }

    fn sample_context() -> RuleEvalContext {
        RuleEvalContext {
            voice_state: VoiceStateCondition::Recording,
            queue_depth: 3,
            latency_ms: 250.0,
            audio_level_db: -20.0,
            terminal_width: 120,
            terminal_height: 40,
            backend: "codex".to_string(),
            capabilities: vec!["truecolor".to_string(), "mouse_events".to_string()],
            color_mode: "truecolor".to_string(),
        }
    }

    #[test]
    fn empty_profile_has_no_rules() {
        let profile = RuleProfile::empty("test");
        assert!(profile.rules.is_empty());
        assert!(profile.active_rules().is_empty());
    }

    #[test]
    fn add_rule_succeeds() {
        let mut profile = RuleProfile::empty("test");
        let rule = sample_rule(
            "r1",
            10,
            RuleCondition::VoiceState {
                state: VoiceStateCondition::Idle,
            },
        );
        assert!(profile.add_rule(rule).is_ok());
        assert_eq!(profile.rules.len(), 1);
    }

    #[test]
    fn add_duplicate_rule_fails() {
        let mut profile = RuleProfile::empty("test");
        let rule1 = sample_rule(
            "r1",
            10,
            RuleCondition::VoiceState {
                state: VoiceStateCondition::Idle,
            },
        );
        let rule2 = sample_rule(
            "r1",
            20,
            RuleCondition::VoiceState {
                state: VoiceStateCondition::Recording,
            },
        );
        assert!(profile.add_rule(rule1).is_ok());
        assert_eq!(
            profile.add_rule(rule2),
            Err(RuleProfileError::DuplicateRuleId("r1".to_string()))
        );
    }

    #[test]
    fn remove_rule_succeeds() {
        let mut profile = RuleProfile::empty("test");
        let rule = sample_rule(
            "r1",
            10,
            RuleCondition::VoiceState {
                state: VoiceStateCondition::Idle,
            },
        );
        profile.add_rule(rule).unwrap();
        let removed = profile.remove_rule("r1").unwrap();
        assert_eq!(removed.id, "r1");
        assert!(profile.rules.is_empty());
    }

    #[test]
    fn remove_nonexistent_rule_fails() {
        let mut profile = RuleProfile::empty("test");
        assert_eq!(
            profile.remove_rule("nonexistent"),
            Err(RuleProfileError::RuleNotFound("nonexistent".to_string()))
        );
    }

    #[test]
    fn toggle_rule_flips_enabled_state() {
        let mut profile = RuleProfile::empty("test");
        let rule = sample_rule(
            "r1",
            10,
            RuleCondition::VoiceState {
                state: VoiceStateCondition::Idle,
            },
        );
        profile.add_rule(rule).unwrap();
        assert!(profile.rules[0].enabled);
        let new_state = profile.toggle_rule("r1").unwrap();
        assert!(!new_state);
        assert!(!profile.rules[0].enabled);
    }

    #[test]
    fn active_rules_sorted_by_priority_descending() {
        let mut profile = RuleProfile::empty("test");
        profile
            .add_rule(sample_rule(
                "low",
                1,
                RuleCondition::VoiceState {
                    state: VoiceStateCondition::Idle,
                },
            ))
            .unwrap();
        profile
            .add_rule(sample_rule(
                "high",
                100,
                RuleCondition::VoiceState {
                    state: VoiceStateCondition::Recording,
                },
            ))
            .unwrap();
        profile
            .add_rule(sample_rule(
                "mid",
                50,
                RuleCondition::VoiceState {
                    state: VoiceStateCondition::Processing,
                },
            ))
            .unwrap();

        let active = profile.active_rules();
        assert_eq!(active.len(), 3);
        assert_eq!(active[0].id, "high");
        assert_eq!(active[1].id, "mid");
        assert_eq!(active[2].id, "low");
    }

    #[test]
    fn active_rules_excludes_disabled() {
        let mut profile = RuleProfile::empty("test");
        let mut rule = sample_rule(
            "disabled",
            10,
            RuleCondition::VoiceState {
                state: VoiceStateCondition::Idle,
            },
        );
        rule.enabled = false;
        profile.add_rule(rule).unwrap();
        assert!(profile.active_rules().is_empty());
    }

    #[test]
    fn evaluate_voice_state_condition() {
        let ctx = sample_context();
        let cond = RuleCondition::VoiceState {
            state: VoiceStateCondition::Recording,
        };
        assert!(evaluate_condition(&cond, &ctx));

        let cond_idle = RuleCondition::VoiceState {
            state: VoiceStateCondition::Idle,
        };
        assert!(!evaluate_condition(&cond_idle, &ctx));
    }

    #[test]
    fn evaluate_threshold_condition_min_only() {
        let ctx = sample_context(); // latency_ms = 250.0
        let cond = RuleCondition::Threshold {
            metric: ThresholdMetric::LatencyMs,
            min: Some(200.0),
            max: None,
        };
        assert!(evaluate_condition(&cond, &ctx));

        let cond_high = RuleCondition::Threshold {
            metric: ThresholdMetric::LatencyMs,
            min: Some(300.0),
            max: None,
        };
        assert!(!evaluate_condition(&cond_high, &ctx));
    }

    #[test]
    fn evaluate_threshold_condition_range() {
        let ctx = sample_context(); // queue_depth = 3
        let cond = RuleCondition::Threshold {
            metric: ThresholdMetric::QueueDepth,
            min: Some(1.0),
            max: Some(5.0),
        };
        assert!(evaluate_condition(&cond, &ctx));

        let cond_narrow = RuleCondition::Threshold {
            metric: ThresholdMetric::QueueDepth,
            min: Some(5.0),
            max: Some(10.0),
        };
        assert!(!evaluate_condition(&cond_narrow, &ctx));
    }

    #[test]
    fn evaluate_threshold_condition_no_bounds() {
        let ctx = sample_context();
        let cond = RuleCondition::Threshold {
            metric: ThresholdMetric::LatencyMs,
            min: None,
            max: None,
        };
        assert!(evaluate_condition(&cond, &ctx));
    }

    #[test]
    fn evaluate_backend_condition() {
        let ctx = sample_context(); // backend = "codex"
        let cond_match = RuleCondition::Backend {
            backend: "codex".to_string(),
        };
        assert!(evaluate_condition(&cond_match, &ctx));

        let cond_no_match = RuleCondition::Backend {
            backend: "claude".to_string(),
        };
        assert!(!evaluate_condition(&cond_no_match, &ctx));
    }

    #[test]
    fn evaluate_capability_condition_present() {
        let ctx = sample_context(); // capabilities = ["truecolor", "mouse_events"]
        let cond = RuleCondition::Capability {
            capability: "truecolor".to_string(),
            present: true,
        };
        assert!(evaluate_condition(&cond, &ctx));

        let cond_absent = RuleCondition::Capability {
            capability: "sixel".to_string(),
            present: true,
        };
        assert!(!evaluate_condition(&cond_absent, &ctx));
    }

    #[test]
    fn evaluate_capability_condition_absent() {
        let ctx = sample_context();
        let cond = RuleCondition::Capability {
            capability: "sixel".to_string(),
            present: false,
        };
        assert!(evaluate_condition(&cond, &ctx));
    }

    #[test]
    fn evaluate_color_mode_condition() {
        let ctx = sample_context(); // color_mode = "truecolor"
        let cond = RuleCondition::ColorMode {
            mode: "truecolor".to_string(),
        };
        assert!(evaluate_condition(&cond, &ctx));
    }

    #[test]
    fn evaluate_all_condition() {
        let ctx = sample_context();
        let cond = RuleCondition::All {
            conditions: vec![
                RuleCondition::VoiceState {
                    state: VoiceStateCondition::Recording,
                },
                RuleCondition::Backend {
                    backend: "codex".to_string(),
                },
            ],
        };
        assert!(evaluate_condition(&cond, &ctx));

        let cond_fail = RuleCondition::All {
            conditions: vec![
                RuleCondition::VoiceState {
                    state: VoiceStateCondition::Recording,
                },
                RuleCondition::Backend {
                    backend: "claude".to_string(),
                },
            ],
        };
        assert!(!evaluate_condition(&cond_fail, &ctx));
    }

    #[test]
    fn evaluate_any_condition() {
        let ctx = sample_context();
        let cond = RuleCondition::Any {
            conditions: vec![
                RuleCondition::VoiceState {
                    state: VoiceStateCondition::Idle,
                },
                RuleCondition::Backend {
                    backend: "codex".to_string(),
                },
            ],
        };
        assert!(evaluate_condition(&cond, &ctx));

        let cond_fail = RuleCondition::Any {
            conditions: vec![
                RuleCondition::VoiceState {
                    state: VoiceStateCondition::Idle,
                },
                RuleCondition::Backend {
                    backend: "claude".to_string(),
                },
            ],
        };
        assert!(!evaluate_condition(&cond_fail, &ctx));
    }

    #[test]
    fn evaluate_empty_all_is_true() {
        let ctx = sample_context();
        let cond = RuleCondition::All { conditions: vec![] };
        assert!(evaluate_condition(&cond, &ctx));
    }

    #[test]
    fn evaluate_empty_any_is_false() {
        let ctx = sample_context();
        let cond = RuleCondition::Any { conditions: vec![] };
        assert!(!evaluate_condition(&cond, &ctx));
    }

    #[test]
    fn evaluate_rules_applies_highest_priority_first() {
        let mut profile = RuleProfile::empty("test");

        let low_rule = StyleRule {
            id: "low".to_string(),
            label: "Low priority".to_string(),
            condition: RuleCondition::VoiceState {
                state: VoiceStateCondition::Recording,
            },
            style_overrides: vec![StyleOverride {
                target_style_id: "core.status".to_string(),
                overrides: vec![OverrideEntry {
                    key: "fg_color".to_string(),
                    value: "#0000ff".to_string(),
                }],
            }],
            priority: 1,
            enabled: true,
        };

        let high_rule = StyleRule {
            id: "high".to_string(),
            label: "High priority".to_string(),
            condition: RuleCondition::VoiceState {
                state: VoiceStateCondition::Recording,
            },
            style_overrides: vec![StyleOverride {
                target_style_id: "core.status".to_string(),
                overrides: vec![OverrideEntry {
                    key: "fg_color".to_string(),
                    value: "#ff0000".to_string(),
                }],
            }],
            priority: 100,
            enabled: true,
        };

        profile.add_rule(low_rule).unwrap();
        profile.add_rule(high_rule).unwrap();

        let ctx = sample_context();
        let resolved = evaluate_rules(&profile, &ctx);

        // The "core.status" entry should have the high-priority color.
        let core_status = resolved
            .entries
            .iter()
            .find(|(id, _)| id == "core.status")
            .expect("core.status should be in resolved overrides");
        assert_eq!(core_status.1.len(), 1);
        assert_eq!(core_status.1[0].value, "#ff0000");
    }

    #[test]
    fn evaluate_rules_skips_non_matching_rules() {
        let mut profile = RuleProfile::empty("test");
        profile
            .add_rule(sample_rule(
                "r1",
                10,
                RuleCondition::VoiceState {
                    state: VoiceStateCondition::Idle,
                },
            ))
            .unwrap();

        let ctx = sample_context(); // voice_state = Recording, not Idle
        let resolved = evaluate_rules(&profile, &ctx);
        assert!(resolved.entries.is_empty());
    }

    #[test]
    fn evaluate_rules_merges_non_conflicting_properties() {
        let mut profile = RuleProfile::empty("test");

        let rule1 = StyleRule {
            id: "color".to_string(),
            label: "Color rule".to_string(),
            condition: RuleCondition::VoiceState {
                state: VoiceStateCondition::Recording,
            },
            style_overrides: vec![StyleOverride {
                target_style_id: "core.status".to_string(),
                overrides: vec![OverrideEntry {
                    key: "fg_color".to_string(),
                    value: "#ff0000".to_string(),
                }],
            }],
            priority: 10,
            enabled: true,
        };

        let rule2 = StyleRule {
            id: "border".to_string(),
            label: "Border rule".to_string(),
            condition: RuleCondition::VoiceState {
                state: VoiceStateCondition::Recording,
            },
            style_overrides: vec![StyleOverride {
                target_style_id: "core.status".to_string(),
                overrides: vec![OverrideEntry {
                    key: "border_style".to_string(),
                    value: "heavy".to_string(),
                }],
            }],
            priority: 5,
            enabled: true,
        };

        profile.add_rule(rule1).unwrap();
        profile.add_rule(rule2).unwrap();

        let ctx = sample_context();
        let resolved = evaluate_rules(&profile, &ctx);

        let core_status = resolved
            .entries
            .iter()
            .find(|(id, _)| id == "core.status")
            .expect("core.status should be in resolved overrides");
        // Both non-conflicting properties should be present.
        assert_eq!(core_status.1.len(), 2);
    }

    #[test]
    fn preview_rules_shows_matching_status() {
        let mut profile = RuleProfile::empty("test");
        profile
            .add_rule(sample_rule(
                "match",
                10,
                RuleCondition::VoiceState {
                    state: VoiceStateCondition::Recording,
                },
            ))
            .unwrap();
        profile
            .add_rule(sample_rule(
                "no-match",
                5,
                RuleCondition::VoiceState {
                    state: VoiceStateCondition::Idle,
                },
            ))
            .unwrap();

        let ctx = sample_context();
        let preview = preview_rules(&profile, &ctx);

        assert_eq!(preview.len(), 2);
        let matching = preview.iter().find(|p| p.rule_id == "match").unwrap();
        assert!(matching.matches);
        assert!(!matching.affected_targets.is_empty());

        let non_matching = preview.iter().find(|p| p.rule_id == "no-match").unwrap();
        assert!(!non_matching.matches);
        assert!(non_matching.affected_targets.is_empty());
    }

    #[test]
    fn parse_rule_profile_from_json() {
        let json = r##"{
            "name": "test-profile",
            "rules": [
                {
                    "id": "r1",
                    "label": "High latency warning",
                    "condition": {
                        "type": "threshold",
                        "metric": "latency-ms",
                        "min": 500.0
                    },
                    "style_overrides": [
                        {
                            "target-style-id": "core.latency-badge",
                            "overrides": [
                                {"key": "fg_color", "value": "#ff0000"}
                            ]
                        }
                    ],
                    "priority": 50,
                    "enabled": true
                }
            ]
        }"##;

        let profile = parse_rule_profile(json).expect("should parse");
        assert_eq!(profile.name, "test-profile");
        assert_eq!(profile.rules.len(), 1);
        assert_eq!(profile.rules[0].id, "r1");
        assert_eq!(profile.rules[0].priority, 50);
    }

    #[test]
    fn parse_rule_profile_with_nested_conditions() {
        let json = r#"{
            "name": "nested",
            "rules": [
                {
                    "id": "complex",
                    "label": "Complex condition",
                    "condition": {
                        "type": "all",
                        "conditions": [
                            {"type": "voice-state", "state": "recording"},
                            {"type": "threshold", "metric": "queue-depth", "min": 2.0, "max": 10.0}
                        ]
                    },
                    "style_overrides": [],
                    "priority": 10,
                    "enabled": true
                }
            ]
        }"#;

        let profile = parse_rule_profile(json).expect("should parse");
        assert_eq!(profile.rules[0].id, "complex");

        let ctx = sample_context(); // Recording + queue_depth=3
        assert!(evaluate_condition(&profile.rules[0].condition, &ctx));
    }

    #[test]
    fn parse_rule_profile_invalid_json() {
        let result = parse_rule_profile("not json");
        assert!(result.is_err());
    }

    #[test]
    fn voice_state_condition_labels_are_non_empty() {
        let states = [
            VoiceStateCondition::Idle,
            VoiceStateCondition::Listening,
            VoiceStateCondition::Recording,
            VoiceStateCondition::Processing,
            VoiceStateCondition::Responding,
        ];
        for state in &states {
            assert!(!state.label().is_empty());
        }
    }

    #[test]
    fn threshold_metric_labels_are_non_empty() {
        let metrics = [
            ThresholdMetric::QueueDepth,
            ThresholdMetric::LatencyMs,
            ThresholdMetric::AudioLevelDb,
            ThresholdMetric::TerminalWidth,
            ThresholdMetric::TerminalHeight,
        ];
        for metric in &metrics {
            assert!(!metric.label().is_empty());
        }
    }

    #[test]
    fn rule_profile_error_display() {
        let dup = RuleProfileError::DuplicateRuleId("r1".to_string());
        assert!(format!("{dup}").contains("r1"));

        let not_found = RuleProfileError::RuleNotFound("r2".to_string());
        assert!(format!("{not_found}").contains("r2"));
    }

    #[test]
    fn default_rule_eval_context() {
        let ctx = RuleEvalContext::default();
        assert_eq!(ctx.voice_state, VoiceStateCondition::Idle);
        assert_eq!(ctx.queue_depth, 0);
        assert_eq!(ctx.terminal_width, 80);
        assert_eq!(ctx.terminal_height, 24);
    }

    #[test]
    fn evaluate_terminal_dimension_thresholds() {
        let ctx = sample_context(); // width=120, height=40
        let wide = RuleCondition::Threshold {
            metric: ThresholdMetric::TerminalWidth,
            min: Some(100.0),
            max: None,
        };
        assert!(evaluate_condition(&wide, &ctx));

        let narrow = RuleCondition::Threshold {
            metric: ThresholdMetric::TerminalWidth,
            min: None,
            max: Some(80.0),
        };
        assert!(!evaluate_condition(&narrow, &ctx));
    }

    #[test]
    fn evaluate_audio_level_threshold() {
        let ctx = sample_context(); // audio_level_db = -20.0
        let loud = RuleCondition::Threshold {
            metric: ThresholdMetric::AudioLevelDb,
            min: Some(-30.0),
            max: Some(-10.0),
        };
        assert!(evaluate_condition(&loud, &ctx));
    }
}
