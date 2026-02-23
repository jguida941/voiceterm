//! Image capture helpers for picture-assisted prompts.

use anyhow::{anyhow, Context, Result};
use std::env;
use std::fs;
use std::path::{Path, PathBuf};
use std::process::Command;
use std::time::{SystemTime, UNIX_EPOCH};

use crate::config::{OverlayConfig, VoiceSendMode};

const IMAGE_CAPTURE_DIR: &str = ".voiceterm/captures";
const IMAGE_CAPTURE_PATH_ENV: &str = "VOICETERM_IMAGE_PATH";

pub(crate) struct ImagePrompt {
    pub(crate) text: String,
    pub(crate) auto_sent: bool,
}

pub(crate) fn capture_image(config: &OverlayConfig) -> Result<PathBuf> {
    let path = next_capture_path()?;
    run_capture_command(config, &path)?;

    let metadata = fs::metadata(&path)
        .with_context(|| format!("captured file missing: {}", path.display()))?;
    if metadata.len() == 0 {
        return Err(anyhow!("captured image is empty"));
    }

    Ok(path)
}

pub(crate) fn build_image_prompt(path: &Path, send_mode: VoiceSendMode) -> ImagePrompt {
    let auto_sent = matches!(send_mode, VoiceSendMode::Auto);
    let mut text = format!("Please analyze this image file: {}\n", path.display());
    if !auto_sent {
        text.pop();
    }
    ImagePrompt { text, auto_sent }
}

fn next_capture_path() -> Result<PathBuf> {
    let working_dir = env::current_dir().context("resolve current directory")?;
    let capture_dir = working_dir.join(IMAGE_CAPTURE_DIR);
    fs::create_dir_all(&capture_dir)
        .with_context(|| format!("create image capture dir: {}", capture_dir.display()))?;
    let millis = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_millis();
    Ok(capture_dir.join(format!("capture-{millis}.png")))
}

fn run_capture_command(config: &OverlayConfig, image_path: &Path) -> Result<()> {
    if let Some(command) = config.image_capture_command.as_deref() {
        return run_custom_capture_command(command, image_path);
    }
    run_default_capture_command(image_path)
}

fn run_custom_capture_command(command: &str, image_path: &Path) -> Result<()> {
    let status = Command::new("sh")
        .arg("-lc")
        .arg(command)
        .env(IMAGE_CAPTURE_PATH_ENV, image_path)
        .status()
        .with_context(|| format!("launch custom image capture command: {command}"))?;
    if status.success() {
        Ok(())
    } else {
        Err(anyhow!(
            "custom image capture command exited with status {status}"
        ))
    }
}

#[cfg(target_os = "macos")]
fn run_default_capture_command(image_path: &Path) -> Result<()> {
    let status = Command::new("screencapture")
        .arg("-x")
        .arg(image_path)
        .status()
        .context("launch screencapture")?;
    if status.success() {
        Ok(())
    } else {
        Err(anyhow!("screencapture exited with status {status}"))
    }
}

#[cfg(not(target_os = "macos"))]
fn run_default_capture_command(_image_path: &Path) -> Result<()> {
    Err(anyhow!(
        "no default image capture command on this platform; set --image-capture-command"
    ))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn build_image_prompt_auto_mode_appends_newline() {
        let prompt = build_image_prompt(Path::new("/tmp/pic.png"), VoiceSendMode::Auto);
        assert!(prompt.auto_sent);
        assert!(prompt.text.ends_with('\n'));
    }

    #[test]
    fn build_image_prompt_insert_mode_stages_without_newline() {
        let prompt = build_image_prompt(Path::new("/tmp/pic.png"), VoiceSendMode::Insert);
        assert!(!prompt.auto_sent);
        assert!(!prompt.text.ends_with('\n'));
    }

    #[test]
    fn next_capture_path_uses_png_extension() {
        let path = match next_capture_path() {
            Ok(path) => path,
            Err(err) => panic!("capture path error: {err}"),
        };
        assert_eq!(path.extension().and_then(|ext| ext.to_str()), Some("png"));
    }
}
