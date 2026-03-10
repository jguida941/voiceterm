use std::io::{Error, ErrorKind};
use std::path::Path;

use serde_json::{Map, Value};

use super::artifact::{parse_review_artifact, ReviewArtifact, ReviewContextPackRef};

#[derive(Debug, Clone)]
pub(crate) struct ReviewArtifactDocument {
    pub(crate) artifact: ReviewArtifact,
    pub(crate) raw_content: String,
}

pub(crate) fn load_review_artifact_document(
    path: &Path,
) -> std::io::Result<ReviewArtifactDocument> {
    let raw_content = std::fs::read_to_string(path)?;
    let artifact = if path.extension().and_then(|value| value.to_str()) == Some("json") {
        parse_review_projection_artifact(&raw_content)?
    } else {
        parse_review_artifact(&raw_content)
    };
    Ok(ReviewArtifactDocument {
        artifact,
        raw_content,
    })
}

fn parse_review_projection_artifact(raw_content: &str) -> std::io::Result<ReviewArtifact> {
    let payload: Value = serde_json::from_str(raw_content).map_err(|err| {
        invalid_projection_error(format!("invalid review-channel projection JSON: {err}"))
    })?;
    let review_state = extract_review_state(&payload)?;
    Ok(review_artifact_from_review_state(review_state))
}

fn extract_review_state(payload: &Value) -> std::io::Result<&Map<String, Value>> {
    if let Some(review_state) = payload
        .as_object()
        .and_then(|root| root.get("review_state"))
        .and_then(Value::as_object)
    {
        return Ok(review_state);
    }
    let root = payload.as_object().ok_or_else(|| {
        invalid_projection_error("review-channel projection must be a JSON object")
    })?;
    if root.get("command").and_then(Value::as_str) != Some("review-channel") {
        return Err(invalid_projection_error(
            "review-channel projection is missing the expected command marker",
        ));
    }
    Ok(root)
}

fn review_artifact_from_review_state(review_state: &Map<String, Value>) -> ReviewArtifact {
    let bridge = object_field(review_state, "bridge");
    let agents = array_field(review_state, "agents");
    let packets = array_field(review_state, "packets");
    let queue = object_field(review_state, "queue");
    let review = object_field(review_state, "review");
    let warnings = array_field(review_state, "warnings");
    let errors = array_field(review_state, "errors");

    ReviewArtifact {
        verdict: first_nonempty([
            bridge.and_then(|value| string_field(value, "current_verdict")),
            derive_verdict(review_state, queue, warnings, errors),
        ]),
        findings: first_nonempty([
            bridge.and_then(|value| string_field(value, "open_findings")),
            derive_findings(packets, warnings, errors),
        ]),
        instruction: first_nonempty([
            bridge.and_then(|value| string_field(value, "current_instruction")),
            derive_instruction(packets),
        ]),
        poll_status: first_nonempty([
            bridge.and_then(|value| string_field(value, "poll_status")),
            derive_poll_status(review_state, queue),
        ]),
        claude_ack: first_nonempty([
            bridge.and_then(|value| string_field(value, "claude_ack")),
            derive_claude_ack(packets),
        ]),
        claude_status: first_nonempty([
            bridge.and_then(|value| string_field(value, "claude_status")),
            derive_claude_status(agents),
        ]),
        claude_questions: bridge
            .and_then(|value| string_field(value, "claude_questions"))
            .unwrap_or_default(),
        last_reviewed_scope: first_nonempty([
            bridge.and_then(|value| string_field(value, "last_reviewed_scope")),
            derive_last_reviewed_scope(review),
        ]),
        last_codex_poll: first_nonempty([
            bridge.and_then(|value| string_field(value, "last_codex_poll_utc")),
            string_field(review_state, "timestamp"),
        ]),
        last_codex_poll_local: bridge
            .and_then(|value| string_field(value, "last_codex_poll_local"))
            .unwrap_or_default(),
        last_worktree_hash: bridge
            .and_then(|value| string_field(value, "last_worktree_hash"))
            .unwrap_or_default(),
        context_pack_refs: collect_context_pack_refs(packets),
    }
}

fn collect_context_pack_refs(packets: &[Value]) -> Vec<ReviewContextPackRef> {
    let mut refs = Vec::new();
    for packet in packets.iter().filter_map(Value::as_object) {
        let Some(context_pack_refs) = packet.get("context_pack_refs").and_then(Value::as_array)
        else {
            continue;
        };
        for context_pack_ref in context_pack_refs {
            let Some(parsed) = parse_context_pack_ref(context_pack_ref) else {
                continue;
            };
            if !refs.contains(&parsed) {
                refs.push(parsed);
            }
        }
    }
    refs
}

fn parse_context_pack_ref(value: &Value) -> Option<ReviewContextPackRef> {
    let row = value.as_object()?;
    let pack_kind = normalize_pack_kind(string_field(row, "pack_kind")?);
    let pack_ref = string_field(row, "pack_ref")?;
    let adapter_profile = string_field(row, "adapter_profile").unwrap_or_default();
    let generated_at_utc = first_nonempty([
        string_field(row, "generated_at_utc"),
        string_field(row, "generated_at"),
    ]);
    Some(ReviewContextPackRef {
        pack_kind,
        pack_ref,
        adapter_profile,
        generated_at_utc,
    })
}

fn normalize_pack_kind(pack_kind: String) -> String {
    match pack_kind.as_str() {
        "session_handoff" => "handoff_pack".to_string(),
        _ => pack_kind,
    }
}

fn derive_verdict(
    review_state: &Map<String, Value>,
    queue: Option<&Map<String, Value>>,
    warnings: &[Value],
    errors: &[Value],
) -> Option<String> {
    if !errors.is_empty() {
        return Some("- review-channel state has active errors".to_string());
    }
    if !warnings.is_empty() {
        return Some("- review-channel state has active warnings".to_string());
    }
    let pending_total = queue
        .and_then(|value| value.get("pending_total"))
        .and_then(Value::as_u64)
        .unwrap_or(0);
    if pending_total > 0 {
        return Some(format!("- review queue active ({pending_total} pending)"));
    }
    if review_state
        .get("ok")
        .and_then(Value::as_bool)
        .unwrap_or(false)
    {
        return Some("- structured review state loaded".to_string());
    }
    None
}

fn derive_findings(packets: &[Value], warnings: &[Value], errors: &[Value]) -> Option<String> {
    let messages = if !errors.is_empty() {
        string_list(errors)
    } else if !warnings.is_empty() {
        string_list(warnings)
    } else {
        packet_summaries(packets, Some("pending"))
            .into_iter()
            .take(3)
            .collect()
    };
    if messages.is_empty() {
        None
    } else {
        Some(bullet_lines(messages))
    }
}

fn derive_instruction(packets: &[Value]) -> Option<String> {
    packet_summaries(packets, Some("pending"))
        .into_iter()
        .next()
        .map(|summary| format!("- {summary}"))
}

fn derive_poll_status(
    review_state: &Map<String, Value>,
    queue: Option<&Map<String, Value>>,
) -> Option<String> {
    let stale_packet_count = queue
        .and_then(|value| value.get("stale_packet_count"))
        .and_then(Value::as_u64)
        .unwrap_or(0);
    if stale_packet_count > 0 {
        return Some(format!(
            "- event-backed queue stale ({stale_packet_count} expired packets)"
        ));
    }
    let pending_total = queue
        .and_then(|value| value.get("pending_total"))
        .and_then(Value::as_u64)
        .unwrap_or(0);
    if pending_total > 0 {
        return Some(format!(
            "- event-backed queue active ({pending_total} pending)"
        ));
    }
    if review_state
        .get("ok")
        .and_then(Value::as_bool)
        .unwrap_or(false)
    {
        return Some("- event-backed review state current".to_string());
    }
    None
}

fn derive_claude_status(agents: &[Value]) -> Option<String> {
    let claude = find_agent(agents, "claude")?;
    let job_status = string_field(claude, "job_status").unwrap_or_else(|| "waiting".to_string());
    let assigned_job = string_field(claude, "assigned_job").unwrap_or_default();
    if assigned_job.is_empty() {
        Some(format!("- {job_status}"))
    } else {
        Some(format!("- {job_status}: {assigned_job}"))
    }
}

fn derive_claude_ack(packets: &[Value]) -> Option<String> {
    packets
        .iter()
        .filter_map(Value::as_object)
        .find(|packet| {
            packet.get("to_agent").and_then(Value::as_str) == Some("claude")
                && matches!(
                    packet.get("status").and_then(Value::as_str),
                    Some("acked" | "applied" | "dismissed")
                )
        })
        .and_then(|packet| packet.get("status").and_then(Value::as_str))
        .map(|status| format!("- latest packet status: {status}"))
}

fn derive_last_reviewed_scope(review: Option<&Map<String, Value>>) -> Option<String> {
    let review = review?;
    let path = string_field(review, "review_channel_path")?;
    Some(format!("- {path}"))
}

fn packet_summaries(packets: &[Value], status: Option<&str>) -> Vec<String> {
    packets
        .iter()
        .filter_map(Value::as_object)
        .filter(|packet| match status {
            Some(expected) => packet.get("status").and_then(Value::as_str) == Some(expected),
            None => true,
        })
        .filter_map(|packet| string_field(packet, "summary"))
        .collect()
}

fn string_list(values: &[Value]) -> Vec<String> {
    values
        .iter()
        .filter_map(Value::as_str)
        .map(clean_projection_text)
        .filter(|value| !value.is_empty())
        .collect()
}

fn find_agent<'a>(agents: &'a [Value], agent_id: &str) -> Option<&'a Map<String, Value>> {
    agents
        .iter()
        .filter_map(Value::as_object)
        .find(|agent| agent.get("agent_id").and_then(Value::as_str) == Some(agent_id))
}

fn object_field<'a>(map: &'a Map<String, Value>, key: &str) -> Option<&'a Map<String, Value>> {
    map.get(key).and_then(Value::as_object)
}

fn array_field<'a>(map: &'a Map<String, Value>, key: &str) -> &'a [Value] {
    map.get(key)
        .and_then(Value::as_array)
        .map(Vec::as_slice)
        .unwrap_or(&[])
}

fn string_field(map: &Map<String, Value>, key: &str) -> Option<String> {
    map.get(key)
        .and_then(Value::as_str)
        .map(clean_projection_text)
        .filter(|value| !value.is_empty())
}

fn clean_projection_text(raw: &str) -> String {
    let trimmed = raw.trim();
    if trimmed.is_empty() || matches!(trimmed, "(missing)" | "n/a" | "None") {
        String::new()
    } else {
        trimmed.to_string()
    }
}

fn first_nonempty(values: [Option<String>; 2]) -> String {
    values
        .into_iter()
        .flatten()
        .find(|value| !value.trim().is_empty())
        .unwrap_or_default()
}

fn bullet_lines(lines: Vec<String>) -> String {
    lines
        .into_iter()
        .map(|line| {
            if line.starts_with('-') || line.starts_with('*') {
                line
            } else {
                format!("- {line}")
            }
        })
        .collect::<Vec<_>>()
        .join("\n")
}

fn invalid_projection_error(message: impl Into<String>) -> Error {
    Error::new(ErrorKind::InvalidData, message.into())
}
