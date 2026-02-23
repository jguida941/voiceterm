//! Rule evaluation engine: condition matching, priority-based conflict
//! resolution, and preview tooling support.
//!
//! Extracted from `rule_profile.rs` (MP-265 module decomposition).

use super::{OverrideEntry, RuleCondition, RuleEvalContext, RuleProfile, ThresholdMetric};

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
            let above_min = min.map_or(true, |m| value >= m);
            let below_max = max.map_or(true, |m| value <= m);
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
