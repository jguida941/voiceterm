use crate::process_signal::signal_process_group_or_pid;
use crate::pty_session::PtyCliSession;
use crate::{log_debug, log_debug_content};
use std::env;
use std::io::{self, BufRead};
use std::sync::mpsc::{self, Sender};
use std::thread;
use std::time::{Duration, Instant};

use super::{utf8_prefix, ClaudeJob, ClaudeJobOutput};

pub(super) fn terminate_piped_child(child: &mut std::process::Child) {
    #[cfg(unix)]
    {
        let Some(pid) = i32::try_from(child.id()).ok() else {
            log_debug("Claude job: child pid out of i32 range, using direct kill");
            let _ = child.kill();
            let _ = child.wait();
            return;
        };

        let _ = signal_process_group_or_pid(pid, libc::SIGTERM, true);
        let deadline = Instant::now() + Duration::from_millis(150);
        while Instant::now() < deadline {
            match child.try_wait() {
                Ok(Some(_)) => return,
                Ok(None) => thread::sleep(Duration::from_millis(10)),
                Err(_) => break,
            }
        }
        let _ = signal_process_group_or_pid(pid, libc::SIGKILL, true);
    }

    #[cfg(not(unix))]
    {
        let _ = child.kill();
    }

    let _ = child.wait();
}

fn build_claude_args(prompt: &str, skip_permissions: bool) -> Vec<String> {
    let mut args = vec!["--print".to_string()];
    if skip_permissions {
        args.push("--dangerously-skip-permissions".to_string());
    }
    args.push(prompt.to_string());
    args
}

fn current_working_dir_string() -> String {
    env::current_dir()
        .map(|path| path.display().to_string())
        .unwrap_or_else(|_| ".".to_string())
}

fn new_claude_job(output: ClaudeJobOutput) -> ClaudeJob {
    ClaudeJob {
        output,
        started_at: Instant::now(),
        pending_exit: None,
    }
}

fn start_claude_pty_job(
    claude_cmd: &str,
    args: &[String],
    term_value: &str,
) -> Result<ClaudeJob, String> {
    let working_dir = current_working_dir_string();
    let session = PtyCliSession::new(claude_cmd, &working_dir, args, term_value)
        .map_err(|err| format!("Failed to start Claude PTY: {err:#}"))?;
    log_debug("Claude job started (PTY)");
    Ok(new_claude_job(ClaudeJobOutput::Pty { session }))
}

fn spawn_claude_reader_thread<R, F>(source: R, tx: Sender<String>, mut map_line: F)
where
    R: io::Read + Send + 'static,
    F: FnMut(String) -> Option<String> + Send + 'static,
{
    thread::spawn(move || {
        let reader = io::BufReader::new(source);
        for line in reader.lines().map_while(Result::ok) {
            let Some(output_line) = map_line(line) else {
                continue;
            };
            if tx.send(output_line).is_err() {
                break;
            }
        }
    });
}

fn spawn_claude_stdout_reader_thread(stdout: std::process::ChildStdout, tx: Sender<String>) {
    spawn_claude_reader_thread(stdout, tx, Some);
}

fn spawn_claude_stderr_reader_thread(stderr: std::process::ChildStderr, tx: Sender<String>) {
    spawn_claude_reader_thread(stderr, tx, |line| {
        // Only show non-empty stderr lines.
        if line.trim().is_empty() {
            None
        } else {
            Some(format!("[info] {line}"))
        }
    });
}

fn start_claude_piped_job(claude_cmd: &str, args: &[String]) -> Result<ClaudeJob, String> {
    use std::process::{Command, Stdio};

    let mut command = Command::new(claude_cmd);
    command.args(args);
    let mut child = command
        .stdin(Stdio::null())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .map_err(|e| format!("Failed to start claude: {e}"))?;

    let stdout = child.stdout.take().ok_or("Failed to capture stdout")?;
    let stderr = child.stderr.take().ok_or("Failed to capture stderr")?;

    let (tx, rx) = mpsc::channel();
    spawn_claude_stdout_reader_thread(stdout, tx.clone());
    spawn_claude_stderr_reader_thread(stderr, tx);

    log_debug("Claude job started");
    Ok(new_claude_job(ClaudeJobOutput::Piped {
        child,
        stdout_rx: rx,
    }))
}

pub(super) fn start_claude_job(
    claude_cmd: &str,
    prompt: &str,
    skip_permissions: bool,
    term_value: &str,
    use_pty: bool,
) -> Result<ClaudeJob, String> {
    log_debug_content(&format!(
        "Starting Claude job with prompt: {}...",
        utf8_prefix(prompt, 30)
    ));

    // Use --print with --dangerously-skip-permissions for non-interactive operation.
    // Prefer PTY when enabled so thinking/tool call output streams in real time.
    let args = build_claude_args(prompt, skip_permissions);

    if use_pty {
        match start_claude_pty_job(claude_cmd, &args, term_value) {
            Ok(job) => return Ok(job),
            Err(err) => {
                log_debug(&format!("Claude PTY failed, falling back to pipes: {err}"));
            }
        }
    }

    start_claude_piped_job(claude_cmd, &args)
}
