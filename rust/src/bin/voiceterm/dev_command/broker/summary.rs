use serde_json::Value;

use super::super::{
    truncate_chars, DevTerminalPacket, OUTPUT_EXCERPT_MAX_CHARS, TERMINAL_PACKET_DRAFT_MAX_CHARS,
    TERMINAL_PACKET_ID_MAX_CHARS,
};

pub(crate) fn summarize_json(json: &Value) -> String {
    match json {
        Value::Object(map) => {
            if let Some(summary) = map.get("summary").and_then(Value::as_str) {
                return truncate_chars(summary, OUTPUT_EXCERPT_MAX_CHARS);
            }
            if let Some(message) = map.get("message").and_then(Value::as_str) {
                return truncate_chars(message, OUTPUT_EXCERPT_MAX_CHARS);
            }
            if let Some(process_summary) = summarize_process_command(map) {
                return truncate_chars(&process_summary, OUTPUT_EXCERPT_MAX_CHARS);
            }
            if let Some(review_summary) = summarize_review_channel(map) {
                return truncate_chars(&review_summary, OUTPUT_EXCERPT_MAX_CHARS);
            }
            if let Some(controller_summary) = summarize_controller_action(map) {
                return truncate_chars(&controller_summary, OUTPUT_EXCERPT_MAX_CHARS);
            }
            if let Some(next_action) = first_next_action(map) {
                let summary = format!("next: {next_action}");
                return truncate_chars(&summary, OUTPUT_EXCERPT_MAX_CHARS);
            }
            if let Some(rollup_summary) = summarize_rollup(map) {
                return truncate_chars(&rollup_summary, OUTPUT_EXCERPT_MAX_CHARS);
            }
            if let Some(ci_summary) = summarize_ci_block(map.get("ci")) {
                return truncate_chars(&ci_summary, OUTPUT_EXCERPT_MAX_CHARS);
            }
            let mut keys: Vec<&str> = map.keys().map(String::as_str).collect();
            keys.sort_unstable();
            let preview = keys.into_iter().take(4).collect::<Vec<_>>().join(", ");
            format!("json object keys: {preview}")
        }
        Value::Array(items) => format!("json array [{} items]", items.len()),
        Value::String(value) => truncate_chars(value, OUTPUT_EXCERPT_MAX_CHARS),
        Value::Bool(value) => format!("json bool {value}"),
        Value::Number(value) => format!("json number {value}"),
        Value::Null => "json null".to_string(),
    }
}

pub(crate) fn parse_terminal_packet(json: &Value) -> Option<DevTerminalPacket> {
    let packet = json.get("terminal_packet")?.as_object()?;
    let draft_text = packet
        .get("draft_text")
        .and_then(Value::as_str)
        .map(str::trim)
        .unwrap_or_default();
    if draft_text.is_empty() {
        return None;
    }

    let packet_id = packet
        .get("packet_id")
        .and_then(Value::as_str)
        .map(str::trim)
        .filter(|value| !value.is_empty())
        .unwrap_or("packet");
    let source_command = packet
        .get("source_command")
        .and_then(Value::as_str)
        .map(str::trim)
        .filter(|value| !value.is_empty())
        .unwrap_or("unknown");
    let auto_send = packet
        .get("auto_send")
        .and_then(Value::as_bool)
        .unwrap_or(false);

    Some(DevTerminalPacket {
        packet_id: truncate_chars(packet_id, TERMINAL_PACKET_ID_MAX_CHARS),
        source_command: truncate_chars(source_command, OUTPUT_EXCERPT_MAX_CHARS),
        draft_text: truncate_chars(draft_text, TERMINAL_PACKET_DRAFT_MAX_CHARS),
        auto_send,
    })
}

pub(crate) fn excerpt(value: &str) -> Option<String> {
    let trimmed = value.trim();
    if trimmed.is_empty() {
        return None;
    }
    let normalized = trimmed.replace('\n', " | ");
    Some(truncate_chars(&normalized, OUTPUT_EXCERPT_MAX_CHARS))
}

fn first_next_action(map: &serde_json::Map<String, Value>) -> Option<&str> {
    let actions = map.get("next_actions")?.as_array()?;
    actions.first()?.as_str()
}

fn summarize_rollup(map: &serde_json::Map<String, Value>) -> Option<String> {
    let rollup = map.get("rollup")?.as_object()?;
    let total = rollup.get("total").and_then(Value::as_u64).unwrap_or(0);
    if total == 0 {
        return Some("issues: none".to_string());
    }

    let by_severity = rollup.get("by_severity").and_then(Value::as_object);
    let high = by_severity
        .and_then(|value| value.get("high"))
        .and_then(Value::as_u64)
        .unwrap_or(0);
    let medium = by_severity
        .and_then(|value| value.get("medium"))
        .and_then(Value::as_u64)
        .unwrap_or(0);

    if high > 0 {
        return Some(format!("issues: {total} total ({high} high)"));
    }
    if medium > 0 {
        return Some(format!("issues: {total} total ({medium} medium)"));
    }
    Some(format!("issues: {total} total"))
}

fn summarize_ci_block(ci_value: Option<&Value>) -> Option<String> {
    let ci = ci_value?.as_object()?;
    if let Some(error) = ci.get("error").and_then(Value::as_str) {
        return Some(format!("CI error: {error}"));
    }

    let runs = ci.get("runs")?.as_array()?;
    if runs.is_empty() {
        return Some("CI: no recent runs".to_string());
    }

    let mut failing = 0_u64;
    let mut passing = 0_u64;
    let mut running = 0_u64;

    for run in runs {
        let Some(row) = run.as_object() else {
            continue;
        };
        let status = row.get("status").and_then(Value::as_str).unwrap_or("");
        let conclusion = row.get("conclusion").and_then(Value::as_str);

        if status != "completed" || conclusion.is_none() {
            running += 1;
            continue;
        }

        match conclusion {
            Some("success") => passing += 1,
            Some("skipped" | "neutral") => {}
            Some(_) => failing += 1,
            None => running += 1,
        }
    }

    let total = runs.len() as u64;
    if failing > 0 {
        return Some(format!("CI failing: {failing}/{total} failed"));
    }
    if running > 0 {
        return Some(format!("CI running: {running} in progress"));
    }
    Some(format!("CI green: {passing}/{total} passed"))
}

fn summarize_process_command(map: &serde_json::Map<String, Value>) -> Option<String> {
    let command = map.get("command").and_then(Value::as_str)?;
    match command {
        "process-audit" => summarize_process_audit(map),
        "process-cleanup" => summarize_process_cleanup(map),
        "process-watch" => summarize_process_watch(map),
        _ => None,
    }
}

fn summarize_review_channel(map: &serde_json::Map<String, Value>) -> Option<String> {
    if map.get("command").and_then(Value::as_str)? != "review-channel" {
        return None;
    }
    let action = map
        .get("action")
        .and_then(Value::as_str)
        .unwrap_or("unknown");
    let ok = map.get("ok").and_then(Value::as_bool).unwrap_or(false);
    let launched = map
        .get("launched")
        .and_then(Value::as_bool)
        .unwrap_or(false);
    let codex = map
        .get("codex_lane_count")
        .and_then(Value::as_u64)
        .unwrap_or(0);
    let claude = map
        .get("claude_lane_count")
        .and_then(Value::as_u64)
        .unwrap_or(0);
    match action {
        "launch" if launched && ok => Some(format!(
            "swarm launched: {codex} codex / {claude} claude lanes"
        )),
        "launch" if ok => Some(format!(
            "swarm dry-run ok: {codex} codex / {claude} claude lanes"
        )),
        "rollover" if ok => {
            let ack = map
                .get("handoff_ack_required")
                .and_then(Value::as_bool)
                .unwrap_or(false);
            let state = if ack {
                "ack wait armed"
            } else {
                "handoff ready"
            };
            Some(format!("swarm rollover ok: {state}"))
        }
        "launch" => Some("swarm launch failed".to_string()),
        "rollover" => Some("swarm rollover failed".to_string()),
        _ => Some(format!("review-channel: {action}")),
    }
}

fn summarize_controller_action(map: &serde_json::Map<String, Value>) -> Option<String> {
    if map.get("command").and_then(Value::as_str)? != "controller-action" {
        return None;
    }
    let action = map
        .get("action")
        .and_then(Value::as_str)
        .unwrap_or("unknown");
    let ok = map.get("ok").and_then(Value::as_bool).unwrap_or(false);
    let reason = map.get("reason").and_then(Value::as_str).unwrap_or("n/a");
    if ok {
        Some(format!("controller {action}: {reason}"))
    } else {
        Some(format!("controller {action}: failed ({reason})"))
    }
}

fn summarize_process_audit(map: &serde_json::Map<String, Value>) -> Option<String> {
    let total = map
        .get("total_detected")
        .and_then(Value::as_u64)
        .unwrap_or(0);
    let orphaned = map
        .get("orphaned_count")
        .and_then(Value::as_u64)
        .unwrap_or(0);
    let stale = map
        .get("stale_active_count")
        .and_then(Value::as_u64)
        .unwrap_or(0);
    let ok = map.get("ok").and_then(Value::as_bool).unwrap_or(false);
    if ok && total == 0 {
        return Some("processes clean".to_string());
    }
    Some(format!(
        "processes: {total} total ({orphaned} orphaned, {stale} stale)"
    ))
}

fn summarize_process_cleanup(map: &serde_json::Map<String, Value>) -> Option<String> {
    let cleanup_targets = map
        .get("cleanup_target_count")
        .and_then(Value::as_u64)
        .unwrap_or(0);
    let killed = map.get("killed_count").and_then(Value::as_u64).unwrap_or(0);
    let ok = map.get("ok").and_then(Value::as_bool).unwrap_or(false);
    if ok {
        if cleanup_targets == 0 {
            return Some("cleanup ok: no targets".to_string());
        }
        return Some(format!("cleanup ok: {killed}/{cleanup_targets} killed"));
    }
    Some(format!("cleanup alert: {killed}/{cleanup_targets} killed"))
}

fn summarize_process_watch(map: &serde_json::Map<String, Value>) -> Option<String> {
    let iterations = map
        .get("iterations_run")
        .and_then(Value::as_u64)
        .unwrap_or(0);
    let stop_reason = map
        .get("stop_reason")
        .and_then(Value::as_str)
        .unwrap_or("unknown");
    let ok = map.get("ok").and_then(Value::as_bool).unwrap_or(false);
    let final_detected = map
        .get("final_audit")
        .and_then(Value::as_object)
        .and_then(|audit| audit.get("total_detected"))
        .and_then(Value::as_u64)
        .unwrap_or(0);
    if ok {
        return Some(format!(
            "watch clean after {iterations} iterations ({stop_reason})"
        ));
    }
    Some(format!(
        "watch alert: {final_detected} detected ({stop_reason})"
    ))
}
