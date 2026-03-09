//! Ops snapshot capture for the Dev-panel Ops page.

use super::super::*;
use serde_json::Value;
use std::path::Path;
use std::process::Command;

pub(in super::super) fn refresh_ops_snapshot(state: &mut EventLoopState) {
    let repo_root = crate::dev_command::find_devctl_root(Path::new(&state.working_dir));
    let snapshot = crate::dev_command::OpsSnapshot {
        process_audit: capture_process_audit(&repo_root),
        triage: capture_triage(&repo_root),
    };
    state.dev_panel_commands.set_ops_snapshot(snapshot);
}

#[derive(Debug)]
struct JsonCapture {
    json: Option<Value>,
    stderr: String,
    error: Option<String>,
}

fn capture_process_audit(repo_root: &Path) -> crate::dev_command::ProcessAuditSnapshot {
    parse_process_audit_capture(run_devctl_json(
        repo_root,
        &["process-audit", "--strict", "--format", "json"],
    ))
}

fn capture_triage(repo_root: &Path) -> crate::dev_command::OpsTriageSnapshot {
    parse_triage_capture(run_devctl_json(
        repo_root,
        &["triage", "--ci", "--format", "json", "--no-cihub"],
    ))
}

fn run_devctl_json(repo_root: &Path, args: &[&str]) -> JsonCapture {
    let script = crate::dev_command::devctl_script_path(repo_root);
    let output = match Command::new("python3")
        .current_dir(repo_root)
        .arg(script)
        .args(args)
        .output()
    {
        Ok(output) => output,
        Err(err) => {
            return JsonCapture {
                json: None,
                stderr: String::new(),
                error: Some(format!("failed to run devctl {}: {err}", args.join(" "))),
            };
        }
    };

    let stdout = String::from_utf8_lossy(&output.stdout).into_owned();
    let stderr = String::from_utf8_lossy(&output.stderr).trim().to_string();
    let stdout_trimmed = stdout.trim();

    let json = if stdout_trimmed.is_empty() {
        None
    } else {
        match serde_json::from_str::<Value>(stdout_trimmed) {
            Ok(value) => Some(value),
            Err(err) => {
                return JsonCapture {
                    json: None,
                    stderr,
                    error: Some(format!(
                        "invalid JSON from devctl {}: {err}",
                        args.join(" ")
                    )),
                };
            }
        }
    };

    JsonCapture {
        json,
        stderr,
        error: None,
    }
}

fn parse_process_audit_capture(capture: JsonCapture) -> crate::dev_command::ProcessAuditSnapshot {
    let mut snapshot = crate::dev_command::ProcessAuditSnapshot::default();

    if let Some(error) = capture.error {
        snapshot.error_message = error;
        if !capture.stderr.is_empty() {
            snapshot.headline = capture.stderr;
        }
        return snapshot;
    }

    let Some(json) = capture.json else {
        snapshot.error_message = "process-audit returned no JSON output".to_string();
        if !capture.stderr.is_empty() {
            snapshot.headline = capture.stderr;
        }
        return snapshot;
    };

    let Some(map) = json.as_object() else {
        snapshot.error_message = "process-audit returned a non-object JSON payload".to_string();
        return snapshot;
    };

    snapshot.captured_at = string_field(map, "timestamp");
    snapshot.strict = bool_field(map, "strict");
    snapshot.total_detected = usize_field(map, "total_detected");
    snapshot.orphaned_count = usize_field(map, "orphaned_count");
    snapshot.stale_active_count = usize_field(map, "stale_active_count");
    snapshot.active_recent_count = usize_field(map, "active_recent_count");
    snapshot.recent_detached_count = usize_field(map, "recent_detached_count");
    snapshot.active_recent_blocking_count = usize_field(map, "active_recent_blocking_count");
    snapshot.active_recent_advisory_count = usize_field(map, "active_recent_advisory_count");
    snapshot.ok = bool_field(map, "ok");

    let warnings = string_array_field(map, "warnings");
    let errors = string_array_field(map, "errors");
    snapshot.warning_count = warnings.len();
    snapshot.error_count = errors.len();
    snapshot.headline = errors
        .first()
        .cloned()
        .or_else(|| warnings.first().cloned())
        .or_else(|| (!capture.stderr.is_empty()).then_some(capture.stderr))
        .unwrap_or_default();

    snapshot
}

fn parse_triage_capture(capture: JsonCapture) -> crate::dev_command::OpsTriageSnapshot {
    let mut snapshot = crate::dev_command::OpsTriageSnapshot::default();

    if let Some(error) = capture.error {
        snapshot.error_message = error;
        return snapshot;
    }

    let Some(json) = capture.json else {
        snapshot.error_message = "triage returned no JSON output".to_string();
        return snapshot;
    };

    let Some(map) = json.as_object() else {
        snapshot.error_message = "triage returned a non-object JSON payload".to_string();
        return snapshot;
    };

    snapshot.captured_at = string_field(map, "timestamp");
    snapshot.warning_count = string_array_field(map, "warnings").len();
    snapshot.external_input_count = map
        .get("external_inputs")
        .and_then(Value::as_array)
        .map_or(0, Vec::len);
    snapshot.next_action = map
        .get("next_actions")
        .and_then(Value::as_array)
        .and_then(|items| items.first())
        .and_then(Value::as_str)
        .unwrap_or_default()
        .to_string();

    if let Some(rollup) = map.get("rollup").and_then(Value::as_object) {
        snapshot.total_issues = usize_value(rollup.get("total"));
        if let Some(by_severity) = rollup.get("by_severity").and_then(Value::as_object) {
            snapshot.high_count = usize_value(by_severity.get("high"));
            snapshot.medium_count = usize_value(by_severity.get("medium"));
        }
    }

    snapshot.summary = if !snapshot.next_action.is_empty() {
        format!("next: {}", snapshot.next_action)
    } else if snapshot.total_issues == 0 {
        "issues: none".to_string()
    } else if snapshot.high_count > 0 {
        format!(
            "issues: {} total ({} high)",
            snapshot.total_issues, snapshot.high_count
        )
    } else if snapshot.medium_count > 0 {
        format!(
            "issues: {} total ({} medium)",
            snapshot.total_issues, snapshot.medium_count
        )
    } else {
        format!("issues: {} total", snapshot.total_issues)
    };

    snapshot
}

fn string_field(map: &serde_json::Map<String, Value>, key: &str) -> String {
    map.get(key)
        .and_then(Value::as_str)
        .unwrap_or_default()
        .to_string()
}

fn bool_field(map: &serde_json::Map<String, Value>, key: &str) -> bool {
    map.get(key).and_then(Value::as_bool).unwrap_or(false)
}

fn usize_field(map: &serde_json::Map<String, Value>, key: &str) -> usize {
    usize_value(map.get(key))
}

fn usize_value(value: Option<&Value>) -> usize {
    value
        .and_then(Value::as_u64)
        .and_then(|count| usize::try_from(count).ok())
        .unwrap_or(0)
}

fn string_array_field(map: &serde_json::Map<String, Value>, key: &str) -> Vec<String> {
    map.get(key)
        .and_then(Value::as_array)
        .map(|items| {
            items
                .iter()
                .filter_map(Value::as_str)
                .map(ToString::to_string)
                .collect()
        })
        .unwrap_or_default()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn parse_process_audit_capture_reads_counts_and_headline() {
        let capture = JsonCapture {
            json: Some(serde_json::json!({
                "timestamp": "2026-03-09T00:00:00Z",
                "strict": true,
                "total_detected": 4,
                "orphaned_count": 1,
                "stale_active_count": 1,
                "active_recent_count": 2,
                "recent_detached_count": 1,
                "active_recent_blocking_count": 1,
                "active_recent_advisory_count": 1,
                "warnings": ["recent detached warning"],
                "errors": ["orphaned process found"],
                "ok": false
            })),
            stderr: String::new(),
            error: None,
        };

        let snapshot = parse_process_audit_capture(capture);
        assert_eq!(snapshot.total_detected, 4);
        assert_eq!(snapshot.orphaned_count, 1);
        assert_eq!(snapshot.recent_detached_count, 1);
        assert_eq!(snapshot.warning_count, 1);
        assert_eq!(snapshot.error_count, 1);
        assert_eq!(snapshot.headline, "orphaned process found");
        assert!(!snapshot.ok);
    }

    #[test]
    fn parse_triage_capture_prefers_next_action_summary() {
        let capture = JsonCapture {
            json: Some(serde_json::json!({
                "timestamp": "2026-03-09T00:00:00Z",
                "warnings": ["cihub skipped"],
                "external_inputs": [{"path": "/tmp/external.json"}],
                "rollup": {
                    "total": 3,
                    "by_severity": {"high": 1, "medium": 1}
                },
                "next_actions": ["Run process-audit to inspect leaked helpers."]
            })),
            stderr: String::new(),
            error: None,
        };

        let snapshot = parse_triage_capture(capture);
        assert_eq!(snapshot.total_issues, 3);
        assert_eq!(snapshot.high_count, 1);
        assert_eq!(snapshot.medium_count, 1);
        assert_eq!(snapshot.warning_count, 1);
        assert_eq!(snapshot.external_input_count, 1);
        assert_eq!(
            snapshot.summary,
            "next: Run process-audit to inspect leaked helpers."
        );
    }
}
