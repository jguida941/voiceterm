//! RuleProfile no-code visual automation (MP-182).
//!
//! Type definitions for rule conditions, actions, and profile management.
//! The evaluation engine lives in the `eval` submodule (MP-265 decomposition).
//!
//! Gate evidence: TS-G14 (rule engine), TS-G05 (studio controls),
//! TS-G06 (snapshot matrix).

mod eval;

#[cfg(test)]
pub(crate) use eval::{evaluate_condition, evaluate_rules, parse_rule_profile, preview_rules};

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
// Rule evaluation context
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

#[cfg(test)]
mod tests;
