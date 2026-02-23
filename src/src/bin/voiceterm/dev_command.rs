//! Dev-only command broker and panel state for control-plane actions.

use std::fs::{self, File};
use std::path::{Path, PathBuf};
use std::process::{Child, Command, ExitStatus, Stdio};
use std::thread::{self, JoinHandle};
use std::time::{Duration, Instant, SystemTime, UNIX_EPOCH};

use crossbeam_channel::{unbounded, Receiver, Sender};
use serde_json::Value;

const DEV_COMMAND_POLL_INTERVAL: Duration = Duration::from_millis(25);
const DEV_COMMAND_TIMEOUT: Duration = Duration::from_secs(90);
const OUTPUT_EXCERPT_MAX_CHARS: usize = 180;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub(crate) enum DevCommandKind {
    Status,
    Report,
    Triage,
    Security,
    Sync,
}

impl DevCommandKind {
    pub(crate) const ALL: [Self; 5] = [
        Self::Status,
        Self::Report,
        Self::Triage,
        Self::Security,
        Self::Sync,
    ];

    pub(crate) fn label(self) -> &'static str {
        match self {
            Self::Status => "status",
            Self::Report => "report",
            Self::Triage => "triage",
            Self::Security => "security",
            Self::Sync => "sync",
        }
    }

    pub(crate) fn is_mutating(self) -> bool {
        matches!(self, Self::Sync)
    }

    fn devctl_args(self) -> &'static [&'static str] {
        match self {
            Self::Status => &["status", "--ci", "--format", "json"],
            Self::Report => &["report", "--ci", "--format", "json"],
            Self::Triage => &["triage", "--ci", "--format", "json", "--no-cihub"],
            Self::Security => &["security", "--format", "json", "--offline"],
            Self::Sync => &["sync", "--format", "json"],
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub(crate) enum DevCommandStatus {
    Success,
    Failed,
    Cancelled,
    TimedOut,
    JsonError,
    SpawnError,
    Rejected,
}

impl DevCommandStatus {
    pub(crate) fn label(self) -> &'static str {
        match self {
            Self::Success => "ok",
            Self::Failed => "failed",
            Self::Cancelled => "cancelled",
            Self::TimedOut => "timeout",
            Self::JsonError => "json-error",
            Self::SpawnError => "spawn-error",
            Self::Rejected => "rejected",
        }
    }
}

#[derive(Debug, Clone)]
pub(crate) struct DevCommandCompletion {
    pub(crate) request_id: u64,
    pub(crate) command: DevCommandKind,
    pub(crate) status: DevCommandStatus,
    pub(crate) duration_ms: u64,
    pub(crate) summary: String,
    pub(crate) stdout_excerpt: Option<String>,
    pub(crate) stderr_excerpt: Option<String>,
}

#[derive(Debug, Clone)]
pub(crate) enum DevCommandUpdate {
    Started {
        request_id: u64,
        command: DevCommandKind,
    },
    Completed(DevCommandCompletion),
}

#[derive(Debug, Clone, Copy)]
struct InFlightCommand {
    request_id: u64,
    command: DevCommandKind,
    started_at: Instant,
}

#[derive(Debug, Clone, Default)]
pub(crate) struct DevPanelCommandState {
    selected_index: usize,
    pending_confirmation: Option<DevCommandKind>,
    in_flight: Option<InFlightCommand>,
    last_completion: Option<DevCommandCompletion>,
}

impl DevPanelCommandState {
    pub(crate) fn selected_command(&self) -> DevCommandKind {
        DevCommandKind::ALL[self
            .selected_index
            .min(DevCommandKind::ALL.len().saturating_sub(1))]
    }

    pub(crate) fn move_selection(&mut self, delta: i32) {
        if DevCommandKind::ALL.is_empty() {
            self.selected_index = 0;
            return;
        }
        let total = i32::try_from(DevCommandKind::ALL.len()).unwrap_or(1);
        let current = i32::try_from(self.selected_index).unwrap_or(0);
        let next = (current + delta).rem_euclid(total);
        self.selected_index = usize::try_from(next).unwrap_or(0);
        self.pending_confirmation = None;
    }

    pub(crate) fn select_index(&mut self, index: usize) {
        if index < DevCommandKind::ALL.len() {
            self.selected_index = index;
            self.pending_confirmation = None;
        }
    }

    pub(crate) fn request_confirmation(&mut self, command: DevCommandKind) {
        self.pending_confirmation = Some(command);
    }

    pub(crate) fn clear_pending_confirmation(&mut self) {
        self.pending_confirmation = None;
    }

    pub(crate) fn pending_confirmation(&self) -> Option<DevCommandKind> {
        self.pending_confirmation
    }

    pub(crate) fn running_request_id(&self) -> Option<u64> {
        self.in_flight.map(|in_flight| in_flight.request_id)
    }

    pub(crate) fn register_launch(&mut self, request_id: u64, command: DevCommandKind) {
        self.in_flight = Some(InFlightCommand {
            request_id,
            command,
            started_at: Instant::now(),
        });
        self.pending_confirmation = None;
    }

    pub(crate) fn apply_update(&mut self, update: DevCommandUpdate) {
        match update {
            DevCommandUpdate::Started {
                request_id,
                command,
            } => {
                if self
                    .in_flight
                    .map_or(true, |existing| existing.request_id == request_id)
                {
                    self.in_flight = Some(InFlightCommand {
                        request_id,
                        command,
                        started_at: Instant::now(),
                    });
                }
            }
            DevCommandUpdate::Completed(completion) => {
                if self
                    .in_flight
                    .is_some_and(|existing| existing.request_id == completion.request_id)
                {
                    self.in_flight = None;
                }
                self.pending_confirmation = None;
                self.last_completion = Some(completion);
            }
        }
    }

    pub(crate) fn status_for(&self, command: DevCommandKind, now: Instant) -> String {
        if let Some(in_flight) = self.in_flight {
            if in_flight.command == command {
                let elapsed_secs = now.duration_since(in_flight.started_at).as_secs_f32();
                return format!("running ({elapsed_secs:.1}s)");
            }
        }

        if let Some(completion) = self.last_completion.as_ref() {
            if completion.command == command {
                return format!(
                    "{} ({}ms)",
                    completion.status.label(),
                    completion.duration_ms
                );
            }
        }

        "idle".to_string()
    }

    pub(crate) fn active_summary(&self, now: Instant) -> String {
        if let Some(command) = self.pending_confirmation {
            return format!(
                "confirm '{}' (press Enter again; Esc/arrows clear)",
                command.label()
            );
        }

        if let Some(in_flight) = self.in_flight {
            let elapsed_secs = now.duration_since(in_flight.started_at).as_secs_f32();
            return format!(
                "running '{}' for {elapsed_secs:.1}s",
                in_flight.command.label()
            );
        }

        "idle".to_string()
    }

    pub(crate) fn last_summary(&self) -> String {
        let Some(completion) = self.last_completion.as_ref() else {
            return "none".to_string();
        };

        let mut summary = format!(
            "{} {}: {}",
            completion.command.label(),
            completion.status.label(),
            completion.summary
        );

        if let Some(stderr_excerpt) = completion.stderr_excerpt.as_deref() {
            summary.push_str(" | stderr: ");
            summary.push_str(stderr_excerpt);
        } else if let Some(stdout_excerpt) = completion.stdout_excerpt.as_deref() {
            summary.push_str(" | out: ");
            summary.push_str(stdout_excerpt);
        }

        truncate_chars(&summary, OUTPUT_EXCERPT_MAX_CHARS)
    }
}

enum BrokerRequest {
    Run {
        request_id: u64,
        command: DevCommandKind,
    },
    Cancel {
        request_id: u64,
    },
    Shutdown,
}

struct RunningProcess {
    request_id: u64,
    command: DevCommandKind,
    started_at: Instant,
    child: Child,
    stdout_path: PathBuf,
    stderr_path: PathBuf,
}

pub(crate) struct DevCommandBroker {
    request_tx: Sender<BrokerRequest>,
    update_rx: Receiver<DevCommandUpdate>,
    worker: Option<JoinHandle<()>>,
    next_request_id: u64,
}

impl DevCommandBroker {
    pub(crate) fn spawn(working_dir: PathBuf) -> Self {
        let (request_tx, request_rx) = unbounded();
        let (update_tx, update_rx) = unbounded();
        let worker = thread::spawn(move || broker_worker(working_dir, request_rx, update_tx));
        Self {
            request_tx,
            update_rx,
            worker: Some(worker),
            next_request_id: 1,
        }
    }

    pub(crate) fn run_command(&mut self, command: DevCommandKind) -> Result<u64, String> {
        let request_id = self.next_request_id;
        self.next_request_id = self.next_request_id.saturating_add(1);
        self.request_tx
            .send(BrokerRequest::Run {
                request_id,
                command,
            })
            .map_err(|_| "dev command broker unavailable".to_string())?;
        Ok(request_id)
    }

    pub(crate) fn cancel_command(&self, request_id: u64) -> Result<(), String> {
        self.request_tx
            .send(BrokerRequest::Cancel { request_id })
            .map_err(|_| "dev command broker unavailable".to_string())
    }

    pub(crate) fn try_recv_update(&self) -> Option<DevCommandUpdate> {
        self.update_rx.try_recv().ok()
    }
}

impl Drop for DevCommandBroker {
    fn drop(&mut self) {
        let _ = self.request_tx.send(BrokerRequest::Shutdown);
        if let Some(worker) = self.worker.take() {
            let _ = worker.join();
        }
    }
}

fn broker_worker(
    working_dir: PathBuf,
    request_rx: Receiver<BrokerRequest>,
    update_tx: Sender<DevCommandUpdate>,
) {
    let mut running: Option<RunningProcess> = None;

    loop {
        if let Some(process) = running.take() {
            let mut process_slot = Some(process);
            while let Ok(request) = request_rx.try_recv() {
                let active_ref = process_slot.as_ref();
                match request {
                    BrokerRequest::Run {
                        request_id,
                        command,
                    } => {
                        let busy_label = active_ref
                            .map(|active| active.command.label())
                            .unwrap_or("unknown");
                        let completion = DevCommandCompletion {
                            request_id,
                            command,
                            status: DevCommandStatus::Rejected,
                            duration_ms: 0,
                            summary: format!("busy: '{busy_label}' still running"),
                            stdout_excerpt: None,
                            stderr_excerpt: None,
                        };
                        let _ = update_tx.send(DevCommandUpdate::Completed(completion));
                    }
                    BrokerRequest::Cancel { request_id } => {
                        let should_cancel =
                            active_ref.is_some_and(|active| request_id == active.request_id);
                        if should_cancel {
                            if let Some(mut active) = process_slot.take() {
                                terminate_child(&mut active.child);
                                let completion = completion_for_terminated_process(
                                    active,
                                    DevCommandStatus::Cancelled,
                                    "cancelled by user",
                                );
                                let _ = update_tx.send(DevCommandUpdate::Completed(completion));
                            }
                            break;
                        }
                    }
                    BrokerRequest::Shutdown => {
                        if let Some(mut active) = process_slot.take() {
                            terminate_child(&mut active.child);
                            let completion = completion_for_terminated_process(
                                active,
                                DevCommandStatus::Cancelled,
                                "cancelled during shutdown",
                            );
                            let _ = update_tx.send(DevCommandUpdate::Completed(completion));
                        }
                        return;
                    }
                }
            }

            let Some(mut process) = process_slot else {
                continue;
            };

            match process.child.try_wait() {
                Ok(Some(status)) => {
                    let completion = completion_from_exit_status(process, status);
                    let _ = update_tx.send(DevCommandUpdate::Completed(completion));
                }
                Ok(None) => {
                    if process.started_at.elapsed() >= DEV_COMMAND_TIMEOUT {
                        terminate_child(&mut process.child);
                        let completion = completion_for_terminated_process(
                            process,
                            DevCommandStatus::TimedOut,
                            "timed out",
                        );
                        let _ = update_tx.send(DevCommandUpdate::Completed(completion));
                    } else {
                        running = Some(process);
                        thread::sleep(DEV_COMMAND_POLL_INTERVAL);
                    }
                }
                Err(err) => {
                    let completion = completion_for_error(process, err.to_string());
                    let _ = update_tx.send(DevCommandUpdate::Completed(completion));
                }
            }
            continue;
        }

        let request = match request_rx.recv() {
            Ok(request) => request,
            Err(_) => return,
        };

        match request {
            BrokerRequest::Run {
                request_id,
                command,
            } => match spawn_process(&working_dir, request_id, command) {
                Ok(process) => {
                    let _ = update_tx.send(DevCommandUpdate::Started {
                        request_id,
                        command,
                    });
                    running = Some(process);
                }
                Err(err) => {
                    let completion = DevCommandCompletion {
                        request_id,
                        command,
                        status: DevCommandStatus::SpawnError,
                        duration_ms: 0,
                        summary: format!("spawn failed: {err}"),
                        stdout_excerpt: None,
                        stderr_excerpt: None,
                    };
                    let _ = update_tx.send(DevCommandUpdate::Completed(completion));
                }
            },
            BrokerRequest::Cancel { .. } => {}
            BrokerRequest::Shutdown => return,
        }
    }
}

fn spawn_process(
    working_dir: &Path,
    request_id: u64,
    command: DevCommandKind,
) -> std::io::Result<RunningProcess> {
    let stdout_path = temporary_output_path(request_id, "stdout");
    let stderr_path = temporary_output_path(request_id, "stderr");
    let stdout_file = File::create(&stdout_path)?;
    let stderr_file = File::create(&stderr_path)?;

    let devctl_repo_root = resolve_devctl_repo_root(working_dir);
    let devctl_script = devctl_script_path(&devctl_repo_root);
    let mut process = Command::new("python3");
    process
        .current_dir(&devctl_repo_root)
        .arg(devctl_script)
        .args(command.devctl_args())
        .stdin(Stdio::null())
        .stdout(Stdio::from(stdout_file))
        .stderr(Stdio::from(stderr_file));

    let child = process.spawn()?;

    Ok(RunningProcess {
        request_id,
        command,
        started_at: Instant::now(),
        child,
        stdout_path,
        stderr_path,
    })
}

fn resolve_devctl_repo_root(working_dir: &Path) -> PathBuf {
    for ancestor in working_dir.ancestors() {
        if devctl_script_path(ancestor).is_file() {
            return ancestor.to_path_buf();
        }
    }
    let manifest_dir = Path::new(env!("CARGO_MANIFEST_DIR"));
    let repo_root = manifest_dir.parent().unwrap_or(manifest_dir);
    if devctl_script_path(repo_root).is_file() {
        return repo_root.to_path_buf();
    }
    working_dir.to_path_buf()
}

fn devctl_script_path(repo_root: &Path) -> PathBuf {
    repo_root.join("dev").join("scripts").join("devctl.py")
}

fn completion_from_exit_status(
    process: RunningProcess,
    status: ExitStatus,
) -> DevCommandCompletion {
    let duration_ms = process.started_at.elapsed().as_millis() as u64;
    let stdout = read_text_file(&process.stdout_path);
    let stderr = read_text_file(&process.stderr_path);
    cleanup_temp_files(&process.stdout_path, &process.stderr_path);

    if status.success() {
        return match serde_json::from_str::<Value>(&stdout) {
            Ok(json) => DevCommandCompletion {
                request_id: process.request_id,
                command: process.command,
                status: DevCommandStatus::Success,
                duration_ms,
                summary: summarize_json_payload(&json),
                stdout_excerpt: excerpt(&stdout),
                stderr_excerpt: excerpt(&stderr),
            },
            Err(err) => DevCommandCompletion {
                request_id: process.request_id,
                command: process.command,
                status: DevCommandStatus::JsonError,
                duration_ms,
                summary: format!("invalid JSON output: {err}"),
                stdout_excerpt: excerpt(&stdout),
                stderr_excerpt: excerpt(&stderr),
            },
        };
    }

    let summary = if let Some(code) = status.code() {
        format!("exit code {code}")
    } else {
        "terminated by signal".to_string()
    };

    DevCommandCompletion {
        request_id: process.request_id,
        command: process.command,
        status: DevCommandStatus::Failed,
        duration_ms,
        summary,
        stdout_excerpt: excerpt(&stdout),
        stderr_excerpt: excerpt(&stderr),
    }
}

fn completion_for_terminated_process(
    mut process: RunningProcess,
    status: DevCommandStatus,
    summary: &str,
) -> DevCommandCompletion {
    let _ = process.child.wait();
    let duration_ms = process.started_at.elapsed().as_millis() as u64;
    let stdout = read_text_file(&process.stdout_path);
    let stderr = read_text_file(&process.stderr_path);
    cleanup_temp_files(&process.stdout_path, &process.stderr_path);
    DevCommandCompletion {
        request_id: process.request_id,
        command: process.command,
        status,
        duration_ms,
        summary: summary.to_string(),
        stdout_excerpt: excerpt(&stdout),
        stderr_excerpt: excerpt(&stderr),
    }
}

fn completion_for_error(process: RunningProcess, error: String) -> DevCommandCompletion {
    let duration_ms = process.started_at.elapsed().as_millis() as u64;
    let stdout = read_text_file(&process.stdout_path);
    let stderr = read_text_file(&process.stderr_path);
    cleanup_temp_files(&process.stdout_path, &process.stderr_path);
    DevCommandCompletion {
        request_id: process.request_id,
        command: process.command,
        status: DevCommandStatus::Failed,
        duration_ms,
        summary: format!("process status error: {error}"),
        stdout_excerpt: excerpt(&stdout),
        stderr_excerpt: excerpt(&stderr),
    }
}

fn terminate_child(child: &mut Child) {
    let _ = child.kill();
    let _ = child.wait();
}

fn temporary_output_path(request_id: u64, stream: &str) -> PathBuf {
    let now_nanos = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_nanos();
    std::env::temp_dir().join(format!(
        "voiceterm-devctl-{stream}-{}-{request_id}-{now_nanos}.log",
        std::process::id()
    ))
}

fn read_text_file(path: &Path) -> String {
    fs::read(path)
        .map(|bytes| String::from_utf8_lossy(&bytes).into_owned())
        .unwrap_or_default()
}

fn cleanup_temp_files(stdout_path: &Path, stderr_path: &Path) {
    let _ = fs::remove_file(stdout_path);
    let _ = fs::remove_file(stderr_path);
}

fn summarize_json_payload(json: &Value) -> String {
    match json {
        Value::Object(map) => {
            if let Some(summary) = map.get("summary").and_then(Value::as_str) {
                return truncate_chars(summary, OUTPUT_EXCERPT_MAX_CHARS);
            }
            if let Some(message) = map.get("message").and_then(Value::as_str) {
                return truncate_chars(message, OUTPUT_EXCERPT_MAX_CHARS);
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

fn excerpt(value: &str) -> Option<String> {
    let trimmed = value.trim();
    if trimmed.is_empty() {
        return None;
    }
    let normalized = trimmed.replace('\n', " | ");
    Some(truncate_chars(&normalized, OUTPUT_EXCERPT_MAX_CHARS))
}

fn truncate_chars(value: &str, max_chars: usize) -> String {
    let mut chars = value.chars();
    let truncated: String = chars.by_ref().take(max_chars).collect();
    if chars.next().is_some() {
        format!("{truncated}...")
    } else {
        truncated
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::thread;

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
    fn broker_executes_status_and_emits_completion() {
        let working_dir = match std::env::current_dir() {
            Ok(path) => path,
            Err(err) => panic!("current dir lookup failed: {err}"),
        };
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
    }

    #[test]
    fn resolve_devctl_repo_root_finds_parent_repo_from_src_working_dir() {
        let src_root = Path::new(env!("CARGO_MANIFEST_DIR"));
        let resolved = resolve_devctl_repo_root(src_root);
        assert!(devctl_script_path(&resolved).is_file());
        assert_eq!(resolved, src_root.parent().unwrap_or(src_root));
    }

    #[test]
    fn resolve_devctl_repo_root_falls_back_to_manifest_parent_when_cwd_is_outside_repo() {
        let outside = std::env::temp_dir().join("voiceterm-devctl-missing-root");
        let resolved = resolve_devctl_repo_root(&outside);
        assert!(devctl_script_path(&resolved).is_file());
        let manifest_dir = Path::new(env!("CARGO_MANIFEST_DIR"));
        assert_eq!(resolved, manifest_dir.parent().unwrap_or(manifest_dir));
    }
}
