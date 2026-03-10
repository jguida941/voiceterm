use super::*;
use crate::scrollable::Scrollable;
use std::fs;
use std::path::PathBuf;
use std::sync::atomic::{AtomicU64, Ordering};
use std::time::{SystemTime, UNIX_EPOCH};

fn make_temp_dir(prefix: &str) -> Result<PathBuf, Box<dyn std::error::Error>> {
    static COUNTER: AtomicU64 = AtomicU64::new(0);
    let now = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_nanos();
    let dir = std::env::temp_dir().join(format!(
        "voiceterm-review-artifact-{prefix}-{now}-{}",
        COUNTER.fetch_add(1, Ordering::Relaxed)
    ));
    fs::create_dir_all(&dir)?;
    Ok(dir)
}

#[test]
fn parse_review_artifact_extracts_sections() {
    let content = "\
# Code Audit Channel

## Current Verdict

- Slice is accepted.

## Open Findings

- No blocker.

## Current Instruction For Claude

1. Do the thing.
2. Do the other thing.

## Claude Ack

- acknowledged

## Poll Status

- Codex polling mode: active

## Claude Status

- Session 5
";
    let mut state = ReviewArtifactState::default();
    state.load_from_content(content);
    let artifact = state.artifact().expect("artifact should parse");
    assert!(artifact.verdict.contains("Slice is accepted"));
    assert!(artifact.findings.contains("No blocker"));
    assert!(artifact.instruction.contains("Do the thing"));
    assert!(artifact.claude_ack.contains("acknowledged"));
    assert!(artifact.poll_status.contains("Codex polling mode"));
    assert!(artifact.claude_status.contains("Session 5"));
}

#[test]
fn bridge_critical_parse_extracts_handoff_sections() {
    let content = "\
## Open Findings

- Blocker one.

## Claude Questions

- Do we keep the cached bridge state on read failure?

## Last Reviewed Scope

- rust/src/bin/voiceterm/dev_command/review_artifact.rs
- rust/src/bin/voiceterm/event_loop/dev_panel_commands/snapshots.rs
";
    let mut state = ReviewArtifactState::default();
    state.load_from_content(content);
    let artifact = state.artifact().expect("artifact should parse");
    assert!(artifact.findings.contains("Blocker one"));
    assert!(artifact.claude_questions.contains("cached bridge state"));
    assert!(artifact
        .last_reviewed_scope
        .contains("rust/src/bin/voiceterm/dev_command/review_artifact.rs"));
    assert!(artifact
        .last_reviewed_scope
        .contains("rust/src/bin/voiceterm/event_loop/dev_panel_commands/snapshots.rs"));
}

#[test]
fn parse_review_artifact_handles_missing_sections() {
    let content = "## Current Verdict\n\n- Green.\n";
    let mut state = ReviewArtifactState::default();
    state.load_from_content(content);
    let artifact = state.artifact().expect("artifact should parse");
    assert!(artifact.verdict.contains("Green"));
    assert!(artifact.findings.is_empty());
    assert!(artifact.instruction.is_empty());
}

#[test]
fn find_review_artifact_path_uses_working_dir_fallback() -> Result<(), Box<dyn std::error::Error>> {
    let repo_root = make_temp_dir("working-dir-fallback")?;
    let nested = repo_root.join("nested").join("shell");
    fs::create_dir_all(&nested)?;
    let expected = repo_root.join("code_audit.md");
    fs::write(&expected, "# temp review artifact\n")?;

    let resolved = find_review_artifact_path(None, Some(&nested));
    assert_eq!(resolved.as_deref(), Some(expected.as_path()));

    let _ = fs::remove_dir_all(repo_root);
    Ok(())
}

#[test]
fn find_review_artifact_path_prefers_markdown_bridge_when_present(
) -> Result<(), Box<dyn std::error::Error>> {
    let repo_root = make_temp_dir("bridge-priority")?;
    let nested = repo_root.join("nested").join("shell");
    fs::create_dir_all(&nested)?;
    let event_root = repo_root.join("dev/reports/review_channel");
    fs::create_dir_all(event_root.join("events"))?;
    fs::create_dir_all(event_root.join("projections/latest"))?;
    fs::write(event_root.join("events/trace.ndjson"), "{}\n")?;
    let event_projection = event_root.join("projections/latest/full.json");
    fs::write(
        &event_projection,
        r#"{"command":"review-channel","review_state":{"command":"review-channel","timestamp":"2026-03-09T13:20:00Z","review":{"review_channel_path":"dev/active/review_channel.md"},"queue":{"pending_total":0,"stale_packet_count":0},"agents":[],"packets":[],"warnings":[],"errors":[]}}"#,
    )?;
    let expected = repo_root.join("code_audit.md");
    fs::write(&expected, "# live markdown bridge\n")?;

    let resolved = find_review_artifact_path(None, Some(&nested));
    assert_eq!(resolved.as_deref(), Some(expected.as_path()));

    let _ = fs::remove_dir_all(repo_root);
    Ok(())
}

#[test]
fn find_review_artifact_path_falls_back_to_event_backed_projection_when_bridge_missing(
) -> Result<(), Box<dyn std::error::Error>> {
    let repo_root = make_temp_dir("event-fallback")?;
    let nested = repo_root.join("nested").join("shell");
    fs::create_dir_all(&nested)?;
    let event_root = repo_root.join("dev/reports/review_channel");
    fs::create_dir_all(event_root.join("events"))?;
    fs::create_dir_all(event_root.join("projections/latest"))?;
    fs::write(event_root.join("events/trace.ndjson"), "{}\n")?;
    let expected = event_root.join("projections/latest/full.json");
    fs::write(
        &expected,
        r#"{"command":"review-channel","review_state":{"command":"review-channel","timestamp":"2026-03-09T13:20:00Z","review":{"review_channel_path":"dev/active/review_channel.md"},"queue":{"pending_total":0,"stale_packet_count":0},"agents":[],"packets":[],"warnings":[],"errors":[]}}"#,
    )?;

    let resolved = find_review_artifact_path(None, Some(&nested));
    assert_eq!(resolved.as_deref(), Some(expected.as_path()));

    let _ = fs::remove_dir_all(repo_root);
    Ok(())
}

#[test]
fn find_review_artifact_path_ignores_corrupt_event_projection_when_bridge_exists(
) -> Result<(), Box<dyn std::error::Error>> {
    let repo_root = make_temp_dir("bridge-over-corrupt-event")?;
    let nested = repo_root.join("nested").join("shell");
    fs::create_dir_all(&nested)?;
    let event_root = repo_root.join("dev/reports/review_channel");
    fs::create_dir_all(event_root.join("events"))?;
    fs::create_dir_all(event_root.join("projections/latest"))?;
    fs::write(event_root.join("events/trace.ndjson"), "{}\n")?;
    fs::write(event_root.join("projections/latest/full.json"), "{not-json")?;
    let expected = repo_root.join("code_audit.md");
    fs::write(&expected, "# live markdown bridge\n")?;

    let resolved = find_review_artifact_path(None, Some(&nested));
    assert_eq!(resolved.as_deref(), Some(expected.as_path()));

    let _ = fs::remove_dir_all(repo_root);
    Ok(())
}

#[test]
fn load_review_artifact_document_parses_bridge_projection_json(
) -> Result<(), Box<dyn std::error::Error>> {
    let repo_root = make_temp_dir("bridge-projection-json")?;
    let full_path = repo_root.join("full.json");
    fs::write(
        &full_path,
        r#"{
  "command": "review-channel",
  "review_state": {
    "command": "review-channel",
    "timestamp": "2026-03-09T13:20:00Z",
    "queue": {"pending_total": 0, "stale_packet_count": 0},
    "review": {"surface_mode": "markdown-bridge", "review_channel_path": "dev/active/review_channel.md"},
    "agents": [],
    "packets": [],
    "warnings": [],
    "errors": [],
    "bridge": {
      "last_codex_poll_utc": "2026-03-09T13:18:00Z",
      "last_codex_poll_local": "2026-03-09 09:18:00 EDT",
      "last_worktree_hash": "abc123",
      "current_verdict": "- still in progress",
      "open_findings": "- blocker one",
      "current_instruction": "- keep the slice bounded",
      "poll_status": "- active reviewer loop",
      "claude_status": "- implementing",
      "claude_ack": "- acknowledged",
      "claude_questions": "- none",
      "last_reviewed_scope": "- code_audit.md"
    }
  }
}"#,
    )?;

    let document = load_review_artifact_document(&full_path)?;
    assert!(document.raw_content.contains("\"review_state\""));
    assert_eq!(document.artifact.last_codex_poll, "2026-03-09T13:18:00Z");
    assert_eq!(
        document.artifact.last_codex_poll_local,
        "2026-03-09 09:18:00 EDT"
    );
    assert_eq!(document.artifact.last_worktree_hash, "abc123");
    assert!(document.artifact.verdict.contains("still in progress"));
    assert!(document.artifact.findings.contains("blocker one"));
    assert!(document
        .artifact
        .instruction
        .contains("keep the slice bounded"));
    assert!(document
        .artifact
        .poll_status
        .contains("active reviewer loop"));
    assert!(document.artifact.claude_status.contains("implementing"));
    assert!(document.artifact.claude_ack.contains("acknowledged"));
    assert!(document.artifact.claude_questions.contains("none"));
    assert!(document
        .artifact
        .last_reviewed_scope
        .contains("code_audit.md"));

    let _ = fs::remove_dir_all(repo_root);
    Ok(())
}

#[test]
fn load_review_artifact_document_rejects_invalid_event_backed_projection_json(
) -> Result<(), Box<dyn std::error::Error>> {
    let repo_root = make_temp_dir("invalid-event-projection-json")?;
    let state_path = repo_root.join("latest.json");
    fs::write(&state_path, "{not-json")?;

    let err = load_review_artifact_document(&state_path).expect_err("invalid JSON must fail");
    assert_eq!(err.kind(), std::io::ErrorKind::InvalidData);
    assert!(err
        .to_string()
        .contains("invalid review-channel projection JSON"));

    let _ = fs::remove_dir_all(repo_root);
    Ok(())
}

#[test]
fn load_review_artifact_document_derives_event_backed_summary_fields(
) -> Result<(), Box<dyn std::error::Error>> {
    let repo_root = make_temp_dir("event-projection-json")?;
    let state_path = repo_root.join("latest.json");
    fs::write(
        &state_path,
        r#"{
  "command": "review-channel",
  "timestamp": "2026-03-09T13:25:00Z",
  "ok": true,
  "review": {
    "surface_mode": "event-backed",
    "review_channel_path": "dev/active/review_channel.md"
  },
  "queue": {
    "pending_total": 1,
    "stale_packet_count": 0
  },
  "agents": [
    {
      "agent_id": "claude",
      "job_status": "implementing",
      "assigned_job": "Fix the event-backed heartbeat"
    }
  ],
  "packets": [
    {
      "packet_id": "pkt-1",
      "summary": "Fix the event-backed heartbeat",
      "status": "pending",
      "to_agent": "claude",
      "from_agent": "codex",
      "context_pack_refs": [
        {
          "pack_kind": "task_pack",
          "pack_ref": ".voiceterm/memory/exports/task_pack.json",
          "adapter_profile": "canonical",
          "generated_at_utc": "2026-03-09T13:22:00Z"
        },
        {
          "pack_kind": "session_handoff",
          "pack_ref": ".voiceterm/memory/exports/session_handoff.json",
          "adapter_profile": "claude"
        }
      ]
    }
  ],
  "warnings": [],
  "errors": []
}"#,
    )?;

    let document = load_review_artifact_document(&state_path)?;
    assert_eq!(document.artifact.last_codex_poll, "2026-03-09T13:25:00Z");
    assert!(document.artifact.verdict.contains("review queue active"));
    assert!(document
        .artifact
        .findings
        .contains("Fix the event-backed heartbeat"));
    assert!(document
        .artifact
        .instruction
        .contains("Fix the event-backed heartbeat"));
    assert!(document
        .artifact
        .poll_status
        .contains("event-backed queue active"));
    assert!(document
        .artifact
        .claude_status
        .contains("implementing: Fix the event-backed heartbeat"));
    assert_eq!(document.artifact.context_pack_refs.len(), 2);
    assert_eq!(
        document.artifact.context_pack_refs[0].pack_kind,
        "task_pack"
    );
    assert_eq!(
        document.artifact.context_pack_refs[0].pack_ref,
        ".voiceterm/memory/exports/task_pack.json"
    );
    assert_eq!(
        document.artifact.context_pack_refs[1].pack_kind,
        "handoff_pack"
    );
    assert!(document
        .artifact
        .last_reviewed_scope
        .contains("dev/active/review_channel.md"));

    let _ = fs::remove_dir_all(repo_root);
    Ok(())
}

#[test]
fn review_artifact_state_load_and_scroll() {
    let content = "## Current Verdict\n\n- Line 1.\n- Line 2.\n";
    let mut state = ReviewArtifactState::default();
    assert!(state.artifact().is_none());

    state.load_from_content(content);
    assert!(state.artifact().is_some());
    assert!(state.load_error().is_none());
    assert_eq!(state.scroll_offset(), 0);

    state.scroll_down(3, 10);
    assert_eq!(state.scroll_offset(), 3);

    state.scroll_up(1);
    assert_eq!(state.scroll_offset(), 2);

    state.scroll_down(20, 10);
    assert_eq!(state.scroll_offset(), 10);
}

#[test]
fn bridge_critical_review_artifact_state_error_retains_last_loaded_artifact() {
    let mut state = ReviewArtifactState::default();
    state.load_from_content("## Open Findings\n\n- blocker\n\n## Claude Questions\n\n- question\n");
    assert!(state.artifact().is_some());

    state.set_load_error("file not found".to_string());
    let artifact = state.artifact().expect("last good artifact should remain");
    assert!(artifact.findings.contains("blocker"));
    assert!(artifact.claude_questions.contains("question"));
    assert_eq!(state.load_error(), Some("file not found"));
}

#[test]
fn set_load_error_preserves_scroll_offset_when_artifact_exists() {
    let mut state = ReviewArtifactState::default();
    state.load_from_content("## Current Verdict\n\n- Line 1\n- Line 2\n");
    state.scroll_down(5, 10);
    assert_eq!(state.scroll_offset(), 5);

    state.set_load_error("read error".to_string());
    assert_eq!(
        state.scroll_offset(),
        5,
        "scroll should stay stable when a stale artifact remains available"
    );
}

#[test]
fn load_shorter_content_resets_scroll_offset() {
    let mut state = ReviewArtifactState::default();
    let long = "## Current Verdict\n\n- L1\n- L2\n- L3\n- L4\n- L5\n- L6\n- L7\n- L8\n";
    state.load_from_content(long);
    state.scroll_down(6, 10);
    assert_eq!(state.scroll_offset(), 6);

    let short = "## Current Verdict\n\n- ok\n";
    state.load_from_content(short);
    assert_eq!(
        state.scroll_offset(),
        0,
        "scroll must reset on shorter content"
    );
}

#[test]
fn parse_review_artifact_extracts_header_metadata() {
    let content = "\
# Code Audit Channel

- Started: `2026-03-07T22:17:12Z`
- Mode: active review
- Last Codex poll: `2026-03-08T08:29:37Z`
- Last Codex poll (Local America/New_York): `2026-03-08 04:29:37 EDT`
- Last non-audit worktree hash: `abc123def`

## Current Verdict

- Green.
";
    let mut state = ReviewArtifactState::default();
    state.load_from_content(content);
    let artifact = state.artifact().expect("artifact should parse");
    assert_eq!(artifact.last_codex_poll, "2026-03-08T08:29:37Z");
    assert_eq!(artifact.last_codex_poll_local, "2026-03-08 04:29:37 EDT");
    assert_eq!(artifact.last_worktree_hash, "abc123def");
    assert!(artifact.verdict.contains("Green"));
}

#[test]
fn parse_review_artifact_missing_header_metadata_defaults_empty() {
    let content = "## Current Verdict\n\n- ok\n";
    let mut state = ReviewArtifactState::default();
    state.load_from_content(content);
    let artifact = state.artifact().expect("artifact should parse");
    assert!(artifact.last_codex_poll.is_empty());
    assert!(artifact.last_codex_poll_local.is_empty());
    assert!(artifact.last_worktree_hash.is_empty());
}

#[test]
fn parse_review_artifact_empty_backtick_values_produce_empty() {
    let content =
        "- Last Codex poll: ``\n- Last non-audit worktree hash: ``\n## Current Verdict\n\n- ok\n";
    let mut state = ReviewArtifactState::default();
    state.load_from_content(content);
    let artifact = state.artifact().expect("artifact should parse");
    assert!(artifact.last_codex_poll.is_empty());
    assert!(artifact.last_worktree_hash.is_empty());
    assert!(artifact.verdict.contains("ok"));
}

#[test]
fn parse_review_artifact_ignores_unknown_sections() {
    let content =
        "## Current Verdict\n\n- ok\n\n## Random Unknown Section\n\n- whatever\n\n## Open Findings\n\n- none\n";
    let mut state = ReviewArtifactState::default();
    state.load_from_content(content);
    let artifact = state.artifact().expect("artifact should parse");
    assert!(artifact.verdict.contains("ok"));
    assert!(artifact.findings.contains("none"));
}

#[test]
fn dev_panel_tab_next_cycles_through_all_pages() {
    let tab = DevPanelTab::Actions;
    assert_eq!(tab.next(), DevPanelTab::Handoff);
    assert_eq!(tab.next().next(), DevPanelTab::Memory);
    assert_eq!(tab.next().next().next(), DevPanelTab::Control);
    assert_eq!(tab.next().next().next().next(), DevPanelTab::Ops);
    assert_eq!(tab.next().next().next().next().next(), DevPanelTab::Review);
    assert_eq!(
        tab.next().next().next().next().next().next(),
        DevPanelTab::Actions
    );
}

#[test]
fn dev_panel_tab_prev_cycles_backward() {
    let tab = DevPanelTab::Actions;
    assert_eq!(tab.prev(), DevPanelTab::Review);
    assert_eq!(tab.prev().prev(), DevPanelTab::Ops);
    assert_eq!(tab.prev().prev().prev(), DevPanelTab::Control);
    assert_eq!(tab.prev().prev().prev().prev(), DevPanelTab::Memory);
    assert_eq!(tab.prev().prev().prev().prev().prev(), DevPanelTab::Handoff);
    assert_eq!(
        tab.prev().prev().prev().prev().prev().prev(),
        DevPanelTab::Actions
    );
}

#[test]
fn dev_panel_tab_label_matches_variant() {
    assert_eq!(DevPanelTab::Control.label(), "Control");
    assert_eq!(DevPanelTab::Ops.label(), "Ops");
    assert_eq!(DevPanelTab::Review.label(), "Review");
    assert_eq!(DevPanelTab::Actions.label(), "Actions");
    assert_eq!(DevPanelTab::Handoff.label(), "Handoff");
    assert_eq!(DevPanelTab::Memory.label(), "Memory");
}

#[test]
fn review_view_mode_toggle_cycles() {
    let mode = ReviewViewMode::Parsed;
    assert_eq!(mode.toggle(), ReviewViewMode::Raw);
    assert_eq!(mode.toggle().toggle(), ReviewViewMode::Parsed);
}

#[test]
fn review_view_mode_labels() {
    assert_eq!(ReviewViewMode::Parsed.label(), "parsed");
    assert_eq!(ReviewViewMode::Raw.label(), "raw");
}

#[test]
fn load_from_content_stores_raw_content() {
    let content = "## Current Verdict\n\n- ok\n";
    let mut state = ReviewArtifactState::default();
    state.load_from_content(content);
    assert_eq!(state.raw_content(), content);
}

#[test]
fn toggle_view_mode_resets_scroll_offset() {
    let mut state = ReviewArtifactState::default();
    state.load_from_content("## Current Verdict\n\n- L1\n- L2\n");
    state.scroll_down(5, 10);
    assert_eq!(state.scroll_offset(), 5);
    state.toggle_view_mode();
    assert_eq!(state.scroll_offset(), 0);
    assert_eq!(state.view_mode(), ReviewViewMode::Raw);
}

#[test]
fn content_changed_detects_same_length_edits() {
    let original = "## Current Verdict\n\n- AAAA\n";
    let edited = "## Current Verdict\n\n- BBBB\n";
    assert_eq!(
        original.len(),
        edited.len(),
        "precondition: same byte length"
    );

    let mut state = ReviewArtifactState::default();
    state.load_from_content(original);
    assert!(
        state.content_changed(edited),
        "same-length but different content must be detected as changed"
    );
}

#[test]
fn bridge_critical_content_changed_after_error_even_when_content_matches_last_success() {
    let content = "## Open Findings\n\n- blocker\n";
    let mut state = ReviewArtifactState::default();
    state.load_from_content(content);

    state.set_load_error("transient read failure".to_string());

    assert!(
        state.content_changed(content),
        "a successful read after an error must reload to clear the stale error state"
    );
}

#[test]
fn content_changed_returns_false_for_identical_content() {
    let content = "## Current Verdict\n\n- ok\n";
    let mut state = ReviewArtifactState::default();
    state.load_from_content(content);
    assert!(
        !state.content_changed(content),
        "identical content must not be flagged as changed"
    );
}

#[test]
fn content_changed_returns_true_when_never_loaded() {
    let state = ReviewArtifactState::default();
    assert!(
        state.content_changed("anything"),
        "no artifact loaded yet -> always changed"
    );
}

#[test]
fn parse_review_artifact_extracts_last_reviewed_scope_and_claude_questions() {
    let content = "\
## Current Verdict

- Green.

## Last Reviewed Scope

- `code_audit.md`
- `AGENTS.md`
- `rust/src/bin/voiceterm/event_loop/tests.rs`

## Claude Questions

- None recorded.

## Open Findings

- No blocker.
";
    let mut state = ReviewArtifactState::default();
    state.load_from_content(content);
    let artifact = state.artifact().expect("artifact should parse");
    assert!(artifact.last_reviewed_scope.contains("code_audit.md"));
    assert!(artifact.last_reviewed_scope.contains("event_loop/tests.rs"));
    assert!(artifact.claude_questions.contains("None recorded"));
    assert!(artifact.findings.contains("No blocker"));
}

#[test]
fn first_meaningful_line_extracts_content() {
    assert_eq!(first_meaningful_line("- hello world"), "hello world");
    assert_eq!(first_meaningful_line("\n\n  - foo\n- bar"), "foo");
    assert_eq!(first_meaningful_line(""), "");
    assert_eq!(first_meaningful_line("plain text"), "plain text");
}

#[test]
fn parse_scope_list_extracts_bullet_items() {
    let text = "- `code_audit.md`\n- `AGENTS.md`\n\n- `rust/src/event_loop.rs`\n";
    let items = parse_scope_list(text);
    assert_eq!(items.len(), 3);
    assert_eq!(items[0], "`code_audit.md`");
    assert_eq!(items[1], "`AGENTS.md`");
    assert_eq!(items[2], "`rust/src/event_loop.rs`");
}

#[test]
fn parse_scope_list_ignores_empty_and_heading_lines() {
    let text = "## Some Heading\n\n- item one\n\n\n- item two\n";
    let items = parse_scope_list(text);
    assert_eq!(items.len(), 2);
    assert_eq!(items[0], "item one");
    assert_eq!(items[1], "item two");
}

#[test]
fn bridge_status_summary_formats_poll_data() {
    let artifact = ReviewArtifact {
        last_codex_poll: "2026-03-08T09:00:00Z".to_string(),
        last_worktree_hash: "abc123def456789".to_string(),
        ..Default::default()
    };
    let summary = artifact
        .bridge_status_summary()
        .expect("summary should exist");
    assert!(summary.contains("2026-03-08T09:00:00Z"));
    assert!(summary.contains("abc123def456"));
}

#[test]
fn bridge_status_summary_returns_none_without_poll() {
    let artifact = ReviewArtifact::default();
    assert!(artifact.bridge_status_summary().is_none());
}
