use std::fs;
use std::path::Path;
use std::process::ExitStatus;

use serde_json::Value;

use super::super::{DevCommandCompletion, DevCommandStatus};
use super::summary::{excerpt, parse_terminal_packet, summarize_json};
use super::RunningProcess;

pub(super) fn completion_from_exit(
    process: RunningProcess,
    status: ExitStatus,
) -> DevCommandCompletion {
    let out = ProcessOutput::collect(&process);

    if status.success() {
        return match serde_json::from_str::<Value>(&out.stdout) {
            Ok(json) => {
                let terminal_packet = parse_terminal_packet(&json);
                DevCommandCompletion {
                    request_id: process.request_id,
                    command: process.command,
                    status: DevCommandStatus::Success,
                    duration_ms: out.duration_ms,
                    summary: summarize_json(&json),
                    stdout_excerpt: excerpt(&out.stdout),
                    stderr_excerpt: excerpt(&out.stderr),
                    terminal_packet,
                }
            }
            Err(err) => DevCommandCompletion {
                request_id: process.request_id,
                command: process.command,
                status: DevCommandStatus::JsonError,
                duration_ms: out.duration_ms,
                summary: format!("invalid JSON output: {err}"),
                stdout_excerpt: excerpt(&out.stdout),
                stderr_excerpt: excerpt(&out.stderr),
                terminal_packet: None,
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
        duration_ms: out.duration_ms,
        summary,
        stdout_excerpt: excerpt(&out.stdout),
        stderr_excerpt: excerpt(&out.stderr),
        terminal_packet: None,
    }
}

pub(super) fn completion_for_terminated(
    process: RunningProcess,
    status: DevCommandStatus,
    summary: &str,
) -> DevCommandCompletion {
    let out = ProcessOutput::collect(&process);
    DevCommandCompletion {
        request_id: process.request_id,
        command: process.command,
        status,
        duration_ms: out.duration_ms,
        summary: summary.to_string(),
        stdout_excerpt: excerpt(&out.stdout),
        stderr_excerpt: excerpt(&out.stderr),
        terminal_packet: None,
    }
}

pub(super) fn completion_for_error(process: RunningProcess, error: String) -> DevCommandCompletion {
    let out = ProcessOutput::collect(&process);
    DevCommandCompletion {
        request_id: process.request_id,
        command: process.command,
        status: DevCommandStatus::Failed,
        duration_ms: out.duration_ms,
        summary: format!("process status error: {error}"),
        stdout_excerpt: excerpt(&out.stdout),
        stderr_excerpt: excerpt(&out.stderr),
        terminal_packet: None,
    }
}

pub(super) fn cleanup_temp_files(stdout_path: &Path, stderr_path: &Path) {
    let _ = fs::remove_file(stdout_path);
    let _ = fs::remove_file(stderr_path);
}

struct ProcessOutput {
    duration_ms: u64,
    stdout: String,
    stderr: String,
}

impl ProcessOutput {
    fn collect(process: &RunningProcess) -> Self {
        let duration_ms = process.started_at.elapsed().as_millis() as u64;
        let stdout = read_text_file(&process.stdout_path);
        let stderr = read_text_file(&process.stderr_path);
        cleanup_temp_files(&process.stdout_path, &process.stderr_path);
        Self {
            duration_ms,
            stdout,
            stderr,
        }
    }
}

fn read_text_file(path: &Path) -> String {
    fs::read(path)
        .map(|bytes| String::from_utf8_lossy(&bytes).into_owned())
        .unwrap_or_default()
}
