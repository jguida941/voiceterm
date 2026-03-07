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
    let ctx = sample_context();
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
    let ctx = sample_context();
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
    let ctx = sample_context();
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
    let ctx = sample_context();
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
    let ctx = sample_context();
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

    let ctx = sample_context();
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

    let ctx = sample_context();
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
    let ctx = sample_context();
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
    let ctx = sample_context();
    let loud = RuleCondition::Threshold {
        metric: ThresholdMetric::AudioLevelDb,
        min: Some(-30.0),
        max: Some(-10.0),
    };
    assert!(evaluate_condition(&loud, &ctx));
}
