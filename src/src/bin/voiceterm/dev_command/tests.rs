use super::*;
use std::fs;
use std::path::PathBuf;
use std::sync::atomic::{AtomicU64, Ordering};
use std::thread;
use std::time::{SystemTime, UNIX_EPOCH};

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
    assert_eq!(DevCommandKind::ALL.len(), 5);
    assert_eq!(DevCommandKind::Status.label(), "status");
    assert!(!DevCommandKind::Status.is_mutating());
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
}

#[test]
fn panel_state_tracks_selection_and_confirmations() {
    let mut state = DevPanelCommandState::default();
    assert_eq!(state.selected_command(), DevCommandKind::Status);

    state.move_selection(1);
    assert_eq!(state.selected_command(), DevCommandKind::Report);

    state.select_index(4);
    assert_eq!(state.selected_command(), DevCommandKind::Sync);

    state.request_confirmation(DevCommandKind::Sync);
    assert_eq!(state.pending_confirmation(), Some(DevCommandKind::Sync));

    state.clear_pending_confirmation();
    assert_eq!(state.pending_confirmation(), None);
}

#[test]
fn summary_for_json_payload_prefers_summary_fields() {
    let payload: Value = serde_json::json!({
        "summary": "all checks green",
        "extra": "ignored"
    });
    assert_eq!(summarize_json_payload(&payload), "all checks green");
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
    assert_eq!(summarize_json_payload(&payload), "CI failing: 1/2 failed");
}

#[test]
fn summary_for_ci_payload_reports_errors() {
    let payload: Value = serde_json::json!({
        "ci": {"error": "gh unavailable"}
    });
    assert_eq!(summarize_json_payload(&payload), "CI error: gh unavailable");
}

#[test]
fn summary_for_triage_payload_prefers_next_action() {
    let payload: Value = serde_json::json!({
        "rollup": {"total": 2, "by_severity": {"high": 1}},
        "next_actions": ["Run status --ci to inspect failed workflows."]
    });
    assert_eq!(
        summarize_json_payload(&payload),
        "next: Run status --ci to inspect failed workflows."
    );
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
        if let Some(update) = broker.try_recv_update() {
            if let DevCommandUpdate::Completed(done) = update {
                completion = Some(done);
                break;
            }
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
fn resolve_devctl_repo_root_finds_parent_repo_from_src_working_dir() -> TestResult {
    let repo_root = make_temp_dir("devctl-root")?;
    write_devctl_stub(&repo_root)?;
    let src_root = repo_root.join("src");
    fs::create_dir_all(&src_root)?;

    let resolved = resolve_devctl_repo_root(&src_root);
    assert_eq!(resolved, repo_root);

    let _ = fs::remove_dir_all(repo_root);
    Ok(())
}

#[test]
fn resolve_devctl_repo_root_falls_back_to_manifest_parent_when_cwd_is_outside_repo() -> TestResult {
    let outside = make_temp_dir("devctl-missing-root")?;
    let resolved = resolve_devctl_repo_root(&outside);
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
