//! Python speech-to-text fallback used when native capture is unavailable.

use std::{
    io::Read,
    process::{Command, Stdio},
    sync::{
        atomic::{AtomicBool, Ordering},
        Arc,
    },
    thread,
    time::{Duration, Instant},
};

use crate::{config::AppConfig, log_debug};
use anyhow::{anyhow, Context, Result};
use serde::Deserialize;

/// JSON payload emitted by the bundled Python fallback pipeline.
#[derive(Debug, Deserialize)]
pub(crate) struct PipelineJsonResult {
    pub(crate) transcript: String,
    #[allow(
        dead_code,
        reason = "Fallback payload field retained for compatibility with Python pipeline output."
    )]
    pub(crate) prompt: String,
    #[serde(default)]
    #[allow(
        dead_code,
        reason = "Fallback payload field retained for compatibility with Python pipeline output."
    )]
    pub(crate) codex_output: Option<String>,
    #[serde(default)]
    pub(crate) metrics: PipelineMetrics,
}

/// Optional timing metadata emitted by the Python helper.
#[derive(Debug, Deserialize, Default, Clone, Copy)]
pub(crate) struct PipelineMetrics {
    #[serde(default)]
    pub(crate) record_s: f64,
    #[serde(default)]
    pub(crate) stt_s: f64,
    #[serde(default)]
    pub(crate) codex_s: f64,
    #[serde(default)]
    pub(crate) total_s: f64,
}

/// Execute the Python pipeline and parse its JSON result for STT fallback.
pub(crate) fn run_python_transcription(
    config: &AppConfig,
    stop_flag: Option<Arc<AtomicBool>>,
) -> Result<PipelineJsonResult> {
    let mut cmd = Command::new(&config.python_cmd);
    cmd.arg(&config.pipeline_script);
    cmd.args(["--seconds", &config.seconds.to_string()]);
    cmd.args(["--lang", &config.lang]);
    cmd.args(["--ffmpeg-cmd", &config.ffmpeg_cmd]);
    if let Some(device) = &config.ffmpeg_device {
        cmd.args(["--ffmpeg-device", device]);
    }
    cmd.args(["--whisper-cmd", &config.whisper_cmd]);
    cmd.args(["--whisper-model", &config.whisper_model]);
    if let Some(model_path) = &config.whisper_model_path {
        cmd.args(["--whisper-model-path", model_path]);
    }
    cmd.args(["--codex-cmd", &config.codex_cmd]);
    for arg in &config.codex_args {
        cmd.arg(format!("--codex-arg={arg}"));
    }
    cmd.arg("--no-codex");
    cmd.arg("--emit-json");
    cmd.stdout(Stdio::piped());
    cmd.stderr(Stdio::piped());

    log_debug("Invoking python fallback for transcription");
    let call_started = Instant::now();
    let (status, stdout_bytes, stderr_bytes) = if let Some(flag) = stop_flag {
        let mut child = cmd
            .spawn()
            .context("failed to run python fallback pipeline")?;
        let mut stdout = child
            .stdout
            .take()
            .context("failed to capture python fallback stdout")?;
        let mut stderr = child
            .stderr
            .take()
            .context("failed to capture python fallback stderr")?;
        loop {
            if flag.load(Ordering::Relaxed) {
                let _ = child.kill();
                let _ = child.wait();
                return Err(anyhow!("python fallback cancelled"));
            }
            match child.try_wait() {
                Ok(Some(status)) => {
                    let mut out = Vec::new();
                    let mut err = Vec::new();
                    stdout
                        .read_to_end(&mut out)
                        .context("failed to read python fallback stdout")?;
                    stderr
                        .read_to_end(&mut err)
                        .context("failed to read python fallback stderr")?;
                    break (status, out, err);
                }
                Ok(None) => thread::sleep(Duration::from_millis(50)),
                Err(err) => return Err(anyhow!("python fallback wait failed: {err}")),
            }
        }
    } else {
        let output = cmd
            .output()
            .context("failed to run python fallback pipeline")?;
        (output.status, output.stdout, output.stderr)
    };

    let stdout = String::from_utf8_lossy(&stdout_bytes).to_string();
    let stderr = String::from_utf8_lossy(&stderr_bytes).to_string();
    if !status.success() {
        return Err(anyhow!(
            "python fallback failed with status {}.\nstdout:\n{}\nstderr:\n{}",
            status,
            stdout.trim(),
            stderr.trim()
        ));
    }

    let mut parsed: Option<PipelineJsonResult> = None;
    let mut last_parse_error: Option<(String, serde_json::Error)> = None;
    let stdout_trimmed = stdout.trim();
    if !stdout_trimmed.is_empty() {
        match serde_json::from_str::<PipelineJsonResult>(stdout_trimmed) {
            Ok(json) => parsed = Some(json),
            Err(err) => last_parse_error = Some((stdout_trimmed.to_string(), err)),
        }
    }

    if parsed.is_none() {
        for line in stdout.lines().rev() {
            let mut trimmed = line.trim();
            if let Some(rest) = trimmed.strip_prefix("JSON:") {
                trimmed = rest.trim();
            }
            if !(trimmed.starts_with('{') && trimmed.ends_with('}')) {
                continue;
            }
            match serde_json::from_str::<PipelineJsonResult>(trimmed) {
                Ok(json) => {
                    parsed = Some(json);
                    break;
                }
                Err(err) => last_parse_error = Some((trimmed.to_string(), err)),
            }
        }
    }

    let parsed = match parsed {
        Some(json) => {
            if let Some((line, err)) = last_parse_error {
                log_debug(&format!(
                    "Python fallback JSON parse warnings (last error: {err} on `{line}`)"
                ));
            }
            json
        }
        None => {
            let mut error = anyhow!(
                "python fallback did not emit JSON.\nstdout:\n{}\nstderr:\n{}",
                stdout.trim(),
                stderr.trim()
            );
            if let Some((line, parse_err)) = last_parse_error {
                error = error.context(format!("last JSON parse failure `{line}`: {parse_err}"));
            }
            return Err(error);
        }
    };
    if config.log_timings {
        let elapsed = call_started.elapsed().as_secs_f64();
        log_debug(&format!(
            "timing|phase=python_pipeline|record_s={:.3}|stt_s={:.3}|codex_s={:.3}|total_s={:.3}|rust_elapsed_s={:.3}",
            parsed.metrics.record_s,
            parsed.metrics.stt_s,
            parsed.metrics.codex_s,
            parsed.metrics.total_s,
            elapsed,
        ));
    }
    Ok(parsed)
}
