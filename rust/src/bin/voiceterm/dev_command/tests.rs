use super::*;
use serde_json::Value;
use std::fs;
use std::path::{Path, PathBuf};
use std::sync::atomic::{AtomicU64, Ordering};
use std::thread;
use std::time::{Duration, Instant, SystemTime, UNIX_EPOCH};

type TestResult = Result<(), Box<dyn std::error::Error>>;

fn make_temp_dir(prefix: &str) -> Result<PathBuf, Box<dyn std::error::Error>> {
    static COUNTER: AtomicU64 = AtomicU64::new(0);
    let now = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_nanos();
    let dir = std::env::temp_dir().join(format!(
        "voiceterm-{prefix}-{now}-{}",
        COUNTER.fetch_add(1, Ordering::Relaxed)
    ));
    fs::create_dir_all(&dir)?;
    Ok(dir)
}

fn write_devctl_stub(repo_root: &Path) -> Result<(), Box<dyn std::error::Error>> {
    let script = devctl_script_path(repo_root);
    if let Some(parent) = script.parent() {
        fs::create_dir_all(parent)?;
    }
    fs::write(
        script,
        "import json\nprint(json.dumps({'summary': 'stub ok'}))\n",
    )?;
    Ok(())
}

#[test]
fn command_allowlist_is_stable() {
    assert_eq!(DevCommandKind::ALL.len(), 14);
    assert_eq!(DevCommandKind::Status.label(), "status");
    assert_eq!(DevCommandKind::LoopPacket.label(), "loop-packet");
    assert_eq!(DevCommandKind::ProcessAudit.label(), "process-audit");
    assert_eq!(DevCommandKind::ReviewLaunchDryRun.label(), "swarm-dry-run");
    assert_eq!(DevCommandKind::ReviewLaunchLive.label(), "start-swarm");
    assert_eq!(DevCommandKind::ReviewRollover.label(), "swarm-rollover");
    assert_eq!(DevCommandKind::PauseLoop.label(), "pause-loop");
    assert_eq!(DevCommandKind::ResumeLoop.label(), "resume-loop");
    assert!(!DevCommandKind::Status.is_mutating());
    assert!(!DevCommandKind::ProcessAudit.is_mutating());
    assert!(!DevCommandKind::ReviewLaunchDryRun.is_mutating());
    assert!(DevCommandKind::ReviewLaunchLive.is_mutating());
    assert!(DevCommandKind::ReviewRollover.is_mutating());
    assert!(DevCommandKind::PauseLoop.is_mutating());
    assert!(DevCommandKind::ResumeLoop.is_mutating());
    assert!(DevCommandKind::ProcessCleanup.is_mutating());
    assert!(DevCommandKind::Sync.is_mutating());
    assert_eq!(
        DevCommandKind::Status.devctl_args(),
        &["status", "--ci", "--format", "json"]
    );
    assert_eq!(
        DevCommandKind::Report.devctl_args(),
        &["report", "--ci", "--format", "json"]
    );
    assert_eq!(
        DevCommandKind::Triage.devctl_args(),
        &["triage", "--ci", "--format", "json", "--no-cihub"]
    );
    assert_eq!(
        DevCommandKind::ProcessAudit.devctl_args(),
        &["process-audit", "--strict", "--format", "json"]
    );
    assert_eq!(
        DevCommandKind::ProcessWatch.devctl_args(),
        &[
            "process-watch",
            "--strict",
            "--iterations",
            "3",
            "--interval-seconds",
            "5",
            "--stop-on-clean",
            "--format",
            "json"
        ]
    );
    assert_eq!(
        DevCommandKind::LoopPacket.devctl_args(),
        &["loop-packet", "--format", "json"]
    );
    assert_eq!(
        DevCommandKind::ReviewLaunchDryRun.devctl_args(),
        &[
            "review-channel",
            "--action",
            "launch",
            "--terminal",
            "none",
            "--dry-run",
            "--format",
            "json"
        ]
    );
    assert_eq!(
        DevCommandKind::ReviewLaunchLive.devctl_args(),
        &["review-channel", "--action", "launch", "--format", "json"]
    );
    assert_eq!(
        DevCommandKind::ReviewRollover.devctl_args(),
        &[
            "review-channel",
            "--action",
            "rollover",
            "--rollover-threshold-pct",
            "50",
            "--await-ack-seconds",
            "60",
            "--format",
            "json"
        ]
    );
    assert_eq!(
        DevCommandKind::PauseLoop.devctl_args(),
        &[
            "controller-action",
            "--action",
            "pause-loop",
            "--format",
            "json"
        ]
    );
    assert_eq!(
        DevCommandKind::ResumeLoop.devctl_args(),
        &[
            "controller-action",
            "--action",
            "resume-loop",
            "--format",
            "json"
        ]
    );
    assert_eq!(
        DevCommandKind::ProcessCleanup.devctl_args(),
        &["process-cleanup", "--verify", "--format", "json"]
    );
}

#[test]
fn panel_state_tracks_selection_and_confirmations() {
    let mut state = DevPanelState::default();
    assert_eq!(state.selected_command(), DevCommandKind::Status);
    assert_eq!(state.execution_profile(), ExecutionProfile::Guarded);

    state.move_selection(1);
    assert_eq!(state.selected_command(), DevCommandKind::Report);

    let sync_index = ActionCatalog::default_catalog()
        .find_by_id("devctl_sync")
        .expect("sync action should exist")
        .0;
    state.select_index(sync_index);
    assert_eq!(state.selected_command(), DevCommandKind::Sync);

    state.request_confirmation_at(sync_index);
    assert_eq!(state.pending_confirmation_index(), Some(sync_index));

    state.clear_pending_confirmation();
    assert_eq!(state.pending_confirmation_index(), None);
}

#[test]
fn summary_for_json_payload_prefers_summary_fields() {
    let payload: Value = serde_json::json!({
        "summary": "all checks green",
        "extra": "ignored"
    });
    assert_eq!(summarize_json(&payload), "all checks green");
}

#[test]
fn summary_for_ci_payload_reports_failures() {
    let payload: Value = serde_json::json!({
        "ci": {
            "runs": [
                {"status": "completed", "conclusion": "success"},
                {"status": "completed", "conclusion": "failure"}
            ]
        }
    });
    assert_eq!(summarize_json(&payload), "CI failing: 1/2 failed");
}

#[test]
fn summary_for_ci_payload_reports_errors() {
    let payload: Value = serde_json::json!({
        "ci": {"error": "gh unavailable"}
    });
    assert_eq!(summarize_json(&payload), "CI error: gh unavailable");
}

#[test]
fn summary_for_triage_payload_prefers_next_action() {
    let payload: Value = serde_json::json!({
        "rollup": {"total": 2, "by_severity": {"high": 1}},
        "next_actions": ["Run status --ci to inspect failed workflows."]
    });
    assert_eq!(
        summarize_json(&payload),
        "next: Run status --ci to inspect failed workflows."
    );
}

#[test]
fn summary_for_process_audit_payload_reports_counts() {
    let payload: Value = serde_json::json!({
        "command": "process-audit",
        "total_detected": 3,
        "orphaned_count": 1,
        "stale_active_count": 1,
        "ok": false
    });
    assert_eq!(
        summarize_json(&payload),
        "processes: 3 total (1 orphaned, 1 stale)"
    );
}

#[test]
fn summary_for_process_cleanup_payload_reports_kill_counts() {
    let payload: Value = serde_json::json!({
        "command": "process-cleanup",
        "cleanup_target_count": 2,
        "killed_count": 2,
        "ok": true
    });
    assert_eq!(summarize_json(&payload), "cleanup ok: 2/2 killed");
}

#[test]
fn summary_for_process_watch_payload_reports_clean_stop() {
    let payload: Value = serde_json::json!({
        "command": "process-watch",
        "iterations_run": 2,
        "stop_reason": "clean",
        "final_audit": {"total_detected": 0},
        "ok": true
    });
    assert_eq!(
        summarize_json(&payload),
        "watch clean after 2 iterations (clean)"
    );
}

#[test]
fn parse_terminal_packet_extracts_draft_and_guard_flags() {
    let payload: Value = serde_json::json!({
        "summary": "packet ready",
        "terminal_packet": {
            "packet_id": "abc123",
            "source_command": "triage-loop",
            "draft_text": "review backlog and propose bounded fix",
            "auto_send": false
        }
    });
    let packet = parse_terminal_packet(&payload).expect("packet should parse");
    assert_eq!(packet.packet_id, "abc123");
    assert_eq!(packet.source_command, "triage-loop");
    assert_eq!(packet.draft_text, "review backlog and propose bounded fix");
    assert!(!packet.auto_send);
}

#[test]
fn excerpt_compacts_multiline_output() {
    let line = excerpt("hello\nworld\n").unwrap_or_default();
    assert_eq!(line, "hello | world");
}

#[test]
fn broker_executes_status_and_emits_completion() -> TestResult {
    let repo_root = make_temp_dir("dev-command-broker")?;
    write_devctl_stub(&repo_root)?;
    let working_dir = repo_root.join("src");
    fs::create_dir_all(&working_dir)?;

    let mut broker = DevCommandBroker::spawn(working_dir);
    let request_id = match broker.run_command(DevCommandKind::Status) {
        Ok(request_id) => request_id,
        Err(err) => panic!("queue status command failed: {err}"),
    };

    let deadline = Instant::now() + Duration::from_secs(15);
    let mut completion: Option<DevCommandCompletion> = None;
    while Instant::now() < deadline {
        if let Some(DevCommandUpdate::Completed(done)) = broker.try_recv_update() {
            completion = Some(done);
            break;
        }
        thread::sleep(Duration::from_millis(20));
    }

    let completion = match completion {
        Some(completion) => completion,
        None => panic!("expected completion update"),
    };
    assert_eq!(completion.request_id, request_id);
    assert_eq!(completion.command, DevCommandKind::Status);
    assert_eq!(completion.status, DevCommandStatus::Success);

    let _ = fs::remove_dir_all(repo_root);
    Ok(())
}

#[test]
fn find_devctl_root_finds_parent_repo_from_src_working_dir() -> TestResult {
    let repo_root = make_temp_dir("devctl-root")?;
    write_devctl_stub(&repo_root)?;
    let src_root = repo_root.join("src");
    fs::create_dir_all(&src_root)?;

    let resolved = find_devctl_root(&src_root);
    assert_eq!(resolved, repo_root);

    let _ = fs::remove_dir_all(repo_root);
    Ok(())
}

#[test]
fn execution_profile_cycles_through_all_variants() {
    let mut profile = ExecutionProfile::default();
    assert_eq!(profile, ExecutionProfile::Guarded);
    assert!(!profile.is_unsafe());

    profile = profile.cycle();
    assert_eq!(profile, ExecutionProfile::AiAssistedGuarded);
    assert!(!profile.is_unsafe());

    profile = profile.cycle();
    assert_eq!(profile, ExecutionProfile::UnsafeDirect);
    assert!(profile.is_unsafe());

    profile = profile.cycle();
    assert_eq!(profile, ExecutionProfile::Guarded);
}

#[test]
fn action_catalog_default_matches_command_allowlist() {
    let catalog = ActionCatalog::default_catalog();
    assert_eq!(catalog.len(), DevCommandKind::ALL.len());
    assert_eq!(catalog.len(), ActionCatalog::DEFAULT_LEN);
    assert!(!catalog.is_empty());

    for kind in DevCommandKind::ALL {
        let found = catalog.find_by_dev_command(kind);
        assert!(found.is_some(), "catalog should contain {:?}", kind);
    }
}

#[test]
fn action_catalog_find_by_id_works() {
    let catalog = ActionCatalog::default_catalog();
    let (index, entry) = catalog
        .find_by_id("devctl_status")
        .expect("should find status");
    assert_eq!(index, 0);
    assert_eq!(entry.label(), "status");
    assert_eq!(entry.category(), ActionCategory::ReadOnly);

    let (index, entry) = catalog.find_by_id("devctl_sync").expect("should find sync");
    assert_eq!(index, 10);
    assert_eq!(entry.label(), "sync");
    assert_eq!(entry.category(), ActionCategory::Mutating);

    assert!(catalog.find_by_id("nonexistent").is_none());
}

#[test]
fn policy_resolution_read_only_always_safe() {
    let catalog = ActionCatalog::default_catalog();
    let (_, entry) = catalog.find_by_dev_command(DevCommandKind::Status).unwrap();

    assert_eq!(
        entry.resolve_policy(ExecutionProfile::Guarded),
        PolicyOutcome::SafeAutoApply
    );
    assert_eq!(
        entry.resolve_policy(ExecutionProfile::AiAssistedGuarded),
        PolicyOutcome::SafeAutoApply
    );
    assert_eq!(
        entry.resolve_policy(ExecutionProfile::UnsafeDirect),
        PolicyOutcome::SafeAutoApply
    );
}

#[test]
fn policy_resolution_mutating_requires_approval_under_guarded() {
    let catalog = ActionCatalog::default_catalog();
    let (_, entry) = catalog.find_by_dev_command(DevCommandKind::Sync).unwrap();

    assert_eq!(
        entry.resolve_policy(ExecutionProfile::Guarded),
        PolicyOutcome::OperatorApprovalRequired
    );
    assert_eq!(
        entry.resolve_policy(ExecutionProfile::AiAssistedGuarded),
        PolicyOutcome::OperatorApprovalRequired
    );
    assert_eq!(
        entry.resolve_policy(ExecutionProfile::UnsafeDirect),
        PolicyOutcome::StageDraft
    );
}

#[test]
fn panel_state_execution_profile_cycles() {
    let mut state = DevPanelState::default();
    assert_eq!(state.execution_profile(), ExecutionProfile::Guarded);

    state.cycle_execution_profile();
    assert_eq!(
        state.execution_profile(),
        ExecutionProfile::AiAssistedGuarded
    );

    state.cycle_execution_profile();
    assert_eq!(state.execution_profile(), ExecutionProfile::UnsafeDirect);

    state.cycle_execution_profile();
    assert_eq!(state.execution_profile(), ExecutionProfile::Guarded);
}

#[test]
fn panel_state_selected_policy_reflects_profile() {
    let mut state = DevPanelState::default();
    // Index 0 = status (ReadOnly) → always SafeAutoApply
    assert_eq!(state.selected_policy(), PolicyOutcome::SafeAutoApply);

    // sync (Mutating) → depends on profile
    let sync_index = ActionCatalog::default_catalog()
        .find_by_id("devctl_sync")
        .expect("sync action should exist")
        .0;
    state.select_index(sync_index);
    assert_eq!(
        state.selected_policy(),
        PolicyOutcome::OperatorApprovalRequired
    );

    state.set_execution_profile(ExecutionProfile::UnsafeDirect);
    assert_eq!(state.selected_policy(), PolicyOutcome::StageDraft);
}

#[test]
fn find_devctl_root_falls_back_to_manifest_parent_when_cwd_is_outside_repo() -> TestResult {
    let outside = make_temp_dir("devctl-missing-root")?;
    let resolved = find_devctl_root(&outside);
    let manifest_dir = Path::new(env!("CARGO_MANIFEST_DIR"));
    let repo_root = manifest_dir.parent().unwrap_or(manifest_dir);
    let expected = if devctl_script_path(repo_root).is_file() {
        repo_root.to_path_buf()
    } else {
        outside.clone()
    };
    assert_eq!(resolved, expected);

    let _ = fs::remove_dir_all(outside);
    Ok(())
}
