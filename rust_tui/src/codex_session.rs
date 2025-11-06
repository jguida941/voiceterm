use std::io::{BufRead, BufReader, Write};
use std::process::{Command, Stdio, Child, ChildStdin, ChildStdout};
use std::sync::{Arc, Mutex};
use std::thread;
use std::time::Duration;
use anyhow::{Result, Context, bail};
use crossbeam_channel::{bounded, Sender, Receiver};

pub enum CodexOutput {
    Stdout(String),
    Stderr(String),
    Terminated,
}

/// Manages a persistent Codex session that stays alive between interactions
pub struct CodexSession {
    process: Option<Child>,
    stdin: Option<ChildStdin>,
    output_rx: Receiver<CodexOutput>,
    output_tx: Sender<CodexOutput>,
    is_ready: Arc<Mutex<bool>>,
}

impl CodexSession {
    /// Start a new Codex session that persists between messages
    pub fn new(codex_cmd: &str, working_dir: &str) -> Result<Self> {
        log::info!("Starting persistent Codex session...");

        // Create channel for output streaming
        let (tx, rx) = bounded(100);

        // Start Codex in interactive mode
        let mut cmd = Command::new(codex_cmd);
        cmd.current_dir(working_dir)
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .env("TERM", "xterm-256color");

        let mut child = cmd.spawn()
            .with_context(|| format!("Failed to start Codex: {}", codex_cmd))?;

        // Take ownership of stdin
        let stdin = child.stdin.take()
            .ok_or_else(|| anyhow::anyhow!("Failed to capture stdin"))?;

        // Take ownership of stdout for streaming
        let stdout = child.stdout.take()
            .ok_or_else(|| anyhow::anyhow!("Failed to capture stdout"))?;

        let stderr = child.stderr.take()
            .ok_or_else(|| anyhow::anyhow!("Failed to capture stderr"))?;

        let is_ready = Arc::new(Mutex::new(false));

        // Spawn thread to read stdout
        let tx_stdout = tx.clone();
        let ready_flag = is_ready.clone();
        thread::spawn(move || {
            let reader = BufReader::new(stdout);
            for line in reader.lines() {
                match line {
                    Ok(text) => {
                        // Check if Codex is ready
                        if text.contains("Ready") || text.contains(">") || text.contains("$") {
                            *ready_flag.lock().unwrap() = true;
                        }

                        if tx_stdout.send(CodexOutput::Stdout(text)).is_err() {
                            break;
                        }
                    }
                    Err(e) => {
                        log::error!("Error reading stdout: {}", e);
                        break;
                    }
                }
            }
            let _ = tx_stdout.send(CodexOutput::Terminated);
        });

        // Spawn thread to read stderr
        let tx_stderr = tx.clone();
        thread::spawn(move || {
            let reader = BufReader::new(stderr);
            for line in reader.lines() {
                match line {
                    Ok(text) => {
                        if tx_stderr.send(CodexOutput::Stderr(text)).is_err() {
                            break;
                        }
                    }
                    Err(e) => {
                        log::error!("Error reading stderr: {}", e);
                        break;
                    }
                }
            }
        });

        // Wait a moment for Codex to initialize
        thread::sleep(Duration::from_millis(500));

        Ok(Self {
            process: Some(child),
            stdin: Some(stdin),
            output_rx: rx,
            output_tx: tx,
            is_ready,
        })
    }

    /// Send a prompt to the persistent Codex session
    pub fn send_prompt(&mut self, prompt: &str) -> Result<()> {
        let stdin = self.stdin.as_mut()
            .ok_or_else(|| anyhow::anyhow!("Codex session not initialized"))?;

        log::debug!("Sending prompt to Codex: {}", prompt);

        // Write prompt to Codex stdin
        writeln!(stdin, "{}", prompt)
            .context("Failed to write prompt to Codex")?;

        stdin.flush()
            .context("Failed to flush stdin")?;

        Ok(())
    }

    /// Read available output from Codex (non-blocking)
    pub fn read_output(&self) -> Vec<String> {
        let mut output = Vec::new();

        // Try to read all available output
        while let Ok(msg) = self.output_rx.try_recv() {
            match msg {
                CodexOutput::Stdout(line) => output.push(line),
                CodexOutput::Stderr(line) => {
                    log::warn!("Codex stderr: {}", line);
                    output.push(format!("[Error] {}", line));
                }
                CodexOutput::Terminated => {
                    log::error!("Codex process terminated unexpectedly");
                    output.push("[Codex terminated]".to_string());
                    break;
                }
            }
        }

        output
    }

    /// Read output with timeout (blocking)
    pub fn read_output_timeout(&self, timeout: Duration) -> Vec<String> {
        let mut output = Vec::new();
        let start = std::time::Instant::now();

        while start.elapsed() < timeout {
            match self.output_rx.recv_timeout(Duration::from_millis(100)) {
                Ok(CodexOutput::Stdout(line)) => output.push(line),
                Ok(CodexOutput::Stderr(line)) => {
                    log::warn!("Codex stderr: {}", line);
                    output.push(format!("[Error] {}", line));
                }
                Ok(CodexOutput::Terminated) => {
                    log::error!("Codex process terminated");
                    output.push("[Codex terminated]".to_string());
                    break;
                }
                Err(_) => {
                    // Timeout, check if we have enough output
                    if !output.is_empty() && output.last().unwrap().contains(">") {
                        break; // Likely reached a prompt
                    }
                }
            }
        }

        output
    }

    /// Check if Codex session is still alive
    pub fn is_alive(&mut self) -> bool {
        if let Some(ref mut process) = self.process {
            match process.try_wait() {
                Ok(None) => true,  // Still running
                Ok(Some(status)) => {
                    log::warn!("Codex exited with: {}", status);
                    false
                }
                Err(e) => {
                    log::error!("Error checking Codex status: {}", e);
                    false
                }
            }
        } else {
            false
        }
    }

    /// Check if Codex is ready to receive input
    pub fn is_ready(&self) -> bool {
        *self.is_ready.lock().unwrap()
    }

    /// Restart the session if it died
    pub fn restart(&mut self, codex_cmd: &str, working_dir: &str) -> Result<()> {
        log::info!("Restarting Codex session...");

        // Kill existing process if any
        self.terminate();

        // Create new session and swap
        let mut new = Self::new(codex_cmd, working_dir)?;
        std::mem::swap(self, &mut new);
        // old session (now in 'new') will be dropped and cleaned up

        Ok(())
    }

    /// Gracefully terminate the Codex session
    pub fn terminate(&mut self) {
        // Try to send exit command first
        if let Some(ref mut stdin) = self.stdin {
            let _ = writeln!(stdin, "exit");
            let _ = stdin.flush();
        }

        // Give it a moment to exit gracefully
        thread::sleep(Duration::from_millis(100));

        // Force kill if still running
        if let Some(ref mut process) = self.process {
            match process.try_wait() {
                Ok(None) => {
                    // Still running, force kill
                    let _ = process.kill();
                    let _ = process.wait();
                }
                _ => {}
            }
        }

        self.process = None;
        self.stdin = None;
    }
}

impl Drop for CodexSession {
    fn drop(&mut self) {
        self.terminate();
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_session_lifecycle() {
        // This would need a mock Codex for testing
        // For now, we'll implement integration tests separately
    }
}