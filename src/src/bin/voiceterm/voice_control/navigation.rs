//! Built-in voice navigation actions and clipboard helpers.

use crossbeam_channel::Sender;
use std::io::Write;
use std::process::{Command, Stdio};
use std::time::{Duration, Instant};
use voiceterm::log_debug;

use crate::config::VoiceSendMode;
use crate::prompt::PromptTracker;
use crate::status_line::{RecordingState, StatusLineState};
use crate::transcript::{send_transcript, TranscriptSession};
use crate::writer::{set_status, WriterMessage};

use super::transcript_preview::format_transcript_preview;
use super::STATUS_TOAST_SECS;

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(super) enum VoiceNavigationAction {
    ScrollUp,
    ScrollDown,
    SendStagedInput,
    CopyLastError,
    ShowLastError,
    ExplainLastError,
}

pub(super) fn parse_voice_navigation_action(text: &str) -> Option<VoiceNavigationAction> {
    let normalized_tokens = normalize_navigation_tokens(text);
    let command_tokens = strip_assistant_address_prefix(&normalized_tokens);
    let normalized = command_tokens.join(" ");
    match normalized.as_str() {
        "scroll up" | "voice scroll up" | "page up" => Some(VoiceNavigationAction::ScrollUp),
        "scroll down" | "voice scroll down" | "page down" => {
            Some(VoiceNavigationAction::ScrollDown)
        }
        "send" | "send it" | "send now" | "send message" | "submit" | "submit now" => {
            Some(VoiceNavigationAction::SendStagedInput)
        }
        "copy last error" | "copy the last error" => Some(VoiceNavigationAction::CopyLastError),
        "show last error" | "what was the last error" => Some(VoiceNavigationAction::ShowLastError),
        "explain last error" | "explain the last error" => {
            Some(VoiceNavigationAction::ExplainLastError)
        }
        _ => None,
    }
}

fn normalize_navigation_tokens(text: &str) -> Vec<String> {
    let cleaned_tokens: Vec<String> = text
        .split_whitespace()
        .filter_map(|token| {
            let cleaned = token.trim_matches(|c: char| !c.is_ascii_alphanumeric());
            if cleaned.is_empty() {
                None
            } else {
                Some(cleaned.to_ascii_lowercase())
            }
        })
        .collect();
    let mut canonical = Vec::with_capacity(cleaned_tokens.len());
    let mut idx = 0;
    while idx < cleaned_tokens.len() {
        if idx + 1 < cleaned_tokens.len() {
            if cleaned_tokens[idx] == "code" && cleaned_tokens[idx + 1] == "x" {
                canonical.push("codex".to_string());
                idx += 2;
                continue;
            }
            if cleaned_tokens[idx] == "voice" && cleaned_tokens[idx + 1] == "term" {
                canonical.push("voiceterm".to_string());
                idx += 2;
                continue;
            }
        }
        let token = match cleaned_tokens[idx].as_str() {
            "codec" | "codecs" | "kodak" | "kodaks" | "kodex" => "codex",
            other => other,
        };
        canonical.push(token.to_string());
        idx += 1;
    }
    canonical
}

fn strip_assistant_address_prefix(tokens: &[String]) -> &[String] {
    let mut start = 0;
    if tokens
        .first()
        .is_some_and(|token| matches!(token.as_str(), "hey" | "ok" | "okay"))
    {
        start += 1;
    }
    if tokens
        .get(start)
        .is_some_and(|token| matches!(token.as_str(), "codex" | "claude" | "gemini" | "voiceterm"))
    {
        start += 1;
    }
    &tokens[start..]
}

pub(super) fn resolve_voice_navigation_action(
    text: &str,
    macro_matched: bool,
) -> Option<VoiceNavigationAction> {
    if macro_matched {
        return None;
    }
    parse_voice_navigation_action(text)
}

fn copy_to_clipboard_command(text: &str, program: &str, args: &[&str]) -> anyhow::Result<()> {
    let mut child = Command::new(program)
        .args(args)
        .stdin(Stdio::piped())
        .spawn()
        .map_err(|err| anyhow::anyhow!("failed to launch {program}: {err}"))?;
    if let Some(stdin) = child.stdin.as_mut() {
        stdin
            .write_all(text.as_bytes())
            .map_err(|err| anyhow::anyhow!("failed to write {program} stdin: {err}"))?;
    }
    let status = child
        .wait()
        .map_err(|err| anyhow::anyhow!("failed to wait for {program}: {err}"))?;
    if status.success() {
        Ok(())
    } else {
        Err(anyhow::anyhow!("{program} exited with status {status}"))
    }
}

fn copy_to_clipboard(text: &str) -> anyhow::Result<()> {
    #[cfg(target_os = "macos")]
    {
        copy_to_clipboard_command(text, "pbcopy", &[])
    }
    #[cfg(target_os = "linux")]
    {
        let mut failures = Vec::new();
        let candidates: [(&str, &[&str]); 3] = [
            ("wl-copy", &[]),
            ("xclip", &["-selection", "clipboard"]),
            ("xsel", &["--clipboard", "--input"]),
        ];
        for (program, args) in candidates {
            match copy_to_clipboard_command(text, program, args) {
                Ok(()) => return Ok(()),
                Err(err) => failures.push(format!("{program}: {err}")),
            }
        }
        Err(anyhow::anyhow!(
            "clipboard copy unavailable on Linux (tried wl-copy, xclip, xsel): {}",
            failures.join("; ")
        ))
    }
    #[cfg(not(any(target_os = "macos", target_os = "linux")))]
    {
        let _ = text;
        Err(anyhow::anyhow!(
            "clipboard copy is not implemented on this platform"
        ))
    }
}

pub(super) fn execute_voice_navigation_action<S: TranscriptSession>(
    action: VoiceNavigationAction,
    prompt_tracker: &PromptTracker,
    session: &mut S,
    writer_tx: &Sender<WriterMessage>,
    status_clear_deadline: &mut Option<Instant>,
    current_status: &mut Option<String>,
    status_state: &mut StatusLineState,
) -> bool {
    match action {
        VoiceNavigationAction::SendStagedInput => {
            if !status_state.insert_pending_send && status_state.send_mode == VoiceSendMode::Insert
            {
                set_status(
                    writer_tx,
                    status_clear_deadline,
                    current_status,
                    status_state,
                    "Nothing to send",
                    Some(Duration::from_secs(STATUS_TOAST_SECS)),
                );
                return false;
            }
            match session.send_text("\r") {
                Ok(()) => {
                    status_state.insert_pending_send = false;
                    status_state.recording_state = RecordingState::Responding;
                    set_status(
                        writer_tx,
                        status_clear_deadline,
                        current_status,
                        status_state,
                        "Voice command: send",
                        Some(Duration::from_secs(STATUS_TOAST_SECS)),
                    );
                    true
                }
                Err(err) => {
                    log_debug(&format!("voice command send failed: {err:#}"));
                    set_status(
                        writer_tx,
                        status_clear_deadline,
                        current_status,
                        status_state,
                        "Voice command failed: send",
                        Some(Duration::from_secs(STATUS_TOAST_SECS)),
                    );
                    false
                }
            }
        }
        VoiceNavigationAction::ScrollUp => match session.send_text("\u{1b}[5~") {
            Ok(()) => {
                set_status(
                    writer_tx,
                    status_clear_deadline,
                    current_status,
                    status_state,
                    "Voice command: scroll up",
                    Some(Duration::from_secs(STATUS_TOAST_SECS)),
                );
                false
            }
            Err(err) => {
                log_debug(&format!("voice command scroll up failed: {err:#}"));
                set_status(
                    writer_tx,
                    status_clear_deadline,
                    current_status,
                    status_state,
                    "Voice command failed: scroll up",
                    Some(Duration::from_secs(STATUS_TOAST_SECS)),
                );
                false
            }
        },
        VoiceNavigationAction::ScrollDown => match session.send_text("\u{1b}[6~") {
            Ok(()) => {
                set_status(
                    writer_tx,
                    status_clear_deadline,
                    current_status,
                    status_state,
                    "Voice command: scroll down",
                    Some(Duration::from_secs(STATUS_TOAST_SECS)),
                );
                false
            }
            Err(err) => {
                log_debug(&format!("voice command scroll down failed: {err:#}"));
                set_status(
                    writer_tx,
                    status_clear_deadline,
                    current_status,
                    status_state,
                    "Voice command failed: scroll down",
                    Some(Duration::from_secs(STATUS_TOAST_SECS)),
                );
                false
            }
        },
        VoiceNavigationAction::ShowLastError => {
            if let Some(last_error) = prompt_tracker.last_error_line() {
                let preview = format_transcript_preview(last_error, 72);
                let status = format!("Last error: {preview}");
                set_status(
                    writer_tx,
                    status_clear_deadline,
                    current_status,
                    status_state,
                    &status,
                    Some(Duration::from_secs(STATUS_TOAST_SECS)),
                );
            } else {
                set_status(
                    writer_tx,
                    status_clear_deadline,
                    current_status,
                    status_state,
                    "No error captured yet",
                    Some(Duration::from_secs(STATUS_TOAST_SECS)),
                );
            }
            false
        }
        VoiceNavigationAction::CopyLastError => {
            let Some(last_error) = prompt_tracker.last_error_line() else {
                set_status(
                    writer_tx,
                    status_clear_deadline,
                    current_status,
                    status_state,
                    "No error captured to copy",
                    Some(Duration::from_secs(STATUS_TOAST_SECS)),
                );
                return false;
            };
            match copy_to_clipboard(last_error) {
                Ok(()) => {
                    set_status(
                        writer_tx,
                        status_clear_deadline,
                        current_status,
                        status_state,
                        "Voice command: copied last error",
                        Some(Duration::from_secs(STATUS_TOAST_SECS)),
                    );
                }
                Err(err) => {
                    log_debug(&format!("voice command copy failed: {err:#}"));
                    set_status(
                        writer_tx,
                        status_clear_deadline,
                        current_status,
                        status_state,
                        "Voice command failed: copy last error",
                        Some(Duration::from_secs(STATUS_TOAST_SECS)),
                    );
                }
            }
            false
        }
        VoiceNavigationAction::ExplainLastError => {
            let Some(last_error) = prompt_tracker.last_error_line() else {
                set_status(
                    writer_tx,
                    status_clear_deadline,
                    current_status,
                    status_state,
                    "No error captured to explain",
                    Some(Duration::from_secs(STATUS_TOAST_SECS)),
                );
                return false;
            };
            let explain_prompt =
                format!("Explain this terminal error and suggest a fix:\n\n{last_error}");
            match send_transcript(session, &explain_prompt, VoiceSendMode::Auto) {
                Ok(sent_newline) => {
                    status_state.recording_state = RecordingState::Responding;
                    set_status(
                        writer_tx,
                        status_clear_deadline,
                        current_status,
                        status_state,
                        "Voice command: explain last error",
                        Some(Duration::from_secs(STATUS_TOAST_SECS)),
                    );
                    sent_newline
                }
                Err(err) => {
                    log_debug(&format!("voice command explain failed: {err:#}"));
                    set_status(
                        writer_tx,
                        status_clear_deadline,
                        current_status,
                        status_state,
                        "Voice command failed: explain last error",
                        Some(Duration::from_secs(STATUS_TOAST_SECS)),
                    );
                    false
                }
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::prompt::PromptLogger;

    #[derive(Default)]
    struct StubSession {
        sent: Vec<String>,
        sent_with_newline: Vec<String>,
    }

    impl TranscriptSession for StubSession {
        fn send_text(&mut self, text: &str) -> anyhow::Result<()> {
            self.sent.push(text.to_string());
            Ok(())
        }

        fn send_text_with_newline(&mut self, text: &str) -> anyhow::Result<()> {
            self.sent_with_newline.push(text.to_string());
            Ok(())
        }
    }

    #[test]
    fn parse_voice_navigation_action_maps_supported_phrases() {
        assert_eq!(
            parse_voice_navigation_action("scroll up"),
            Some(VoiceNavigationAction::ScrollUp)
        );
        assert_eq!(
            parse_voice_navigation_action("voice scroll down"),
            Some(VoiceNavigationAction::ScrollDown)
        );
        assert_eq!(
            parse_voice_navigation_action("send message"),
            Some(VoiceNavigationAction::SendStagedInput)
        );
        assert_eq!(
            parse_voice_navigation_action("send it"),
            Some(VoiceNavigationAction::SendStagedInput)
        );
        assert_eq!(
            parse_voice_navigation_action("send now"),
            Some(VoiceNavigationAction::SendStagedInput)
        );
        assert_eq!(
            parse_voice_navigation_action("send."),
            Some(VoiceNavigationAction::SendStagedInput)
        );
        assert_eq!(
            parse_voice_navigation_action("submit"),
            Some(VoiceNavigationAction::SendStagedInput)
        );
        assert_eq!(
            parse_voice_navigation_action("submit now"),
            Some(VoiceNavigationAction::SendStagedInput)
        );
        assert_eq!(
            parse_voice_navigation_action("codex send"),
            Some(VoiceNavigationAction::SendStagedInput)
        );
        assert_eq!(
            parse_voice_navigation_action("hey claude send"),
            Some(VoiceNavigationAction::SendStagedInput)
        );
        assert_eq!(
            parse_voice_navigation_action("code x send"),
            Some(VoiceNavigationAction::SendStagedInput)
        );
        assert_eq!(
            parse_voice_navigation_action("copy last error"),
            Some(VoiceNavigationAction::CopyLastError)
        );
        assert_eq!(
            parse_voice_navigation_action("show last error"),
            Some(VoiceNavigationAction::ShowLastError)
        );
        assert_eq!(
            parse_voice_navigation_action("explain the last error"),
            Some(VoiceNavigationAction::ExplainLastError)
        );
        assert_eq!(parse_voice_navigation_action("run tests"), None);
    }

    #[test]
    fn resolve_voice_navigation_action_skips_builtins_when_macro_matched() {
        assert_eq!(resolve_voice_navigation_action("scroll up", true), None);
        assert_eq!(resolve_voice_navigation_action("send", true), None);
        assert_eq!(
            resolve_voice_navigation_action("voice scroll up", false),
            Some(VoiceNavigationAction::ScrollUp)
        );
    }

    #[test]
    fn execute_voice_navigation_scroll_up_sends_pageup_escape() {
        let mut session = StubSession::default();
        let mut status_state = StatusLineState::new();
        let (writer_tx, _writer_rx) = crossbeam_channel::unbounded();
        let mut deadline = None;
        let mut current_status = None;
        let mut prompt_tracker = PromptTracker::new(None, true, PromptLogger::new(None));
        prompt_tracker.feed_output(b"ready\n");

        let sent_newline = execute_voice_navigation_action(
            VoiceNavigationAction::ScrollUp,
            &prompt_tracker,
            &mut session,
            &writer_tx,
            &mut deadline,
            &mut current_status,
            &mut status_state,
        );

        assert!(!sent_newline);
        assert_eq!(session.sent, vec!["\u{1b}[5~".to_string()]);
        assert!(status_state.message.contains("scroll up"));
    }

    #[test]
    fn execute_voice_navigation_send_submits_staged_insert_text() {
        let mut session = StubSession::default();
        let mut status_state = StatusLineState::new();
        status_state.insert_pending_send = true;
        let (writer_tx, _writer_rx) = crossbeam_channel::unbounded();
        let mut deadline = None;
        let mut current_status = None;
        let mut prompt_tracker = PromptTracker::new(None, true, PromptLogger::new(None));
        prompt_tracker.feed_output(b"ready\n");

        let sent_newline = execute_voice_navigation_action(
            VoiceNavigationAction::SendStagedInput,
            &prompt_tracker,
            &mut session,
            &writer_tx,
            &mut deadline,
            &mut current_status,
            &mut status_state,
        );

        assert!(sent_newline);
        assert_eq!(session.sent, vec!["\r".to_string()]);
        assert_eq!(status_state.recording_state, RecordingState::Responding);
        assert!(!status_state.insert_pending_send);
        assert!(status_state.message.contains("Voice command: send"));
    }

    #[test]
    fn execute_voice_navigation_send_without_staged_text_sets_status() {
        let mut session = StubSession::default();
        let mut status_state = StatusLineState::new();
        status_state.send_mode = VoiceSendMode::Insert;
        let (writer_tx, _writer_rx) = crossbeam_channel::unbounded();
        let mut deadline = None;
        let mut current_status = None;
        let mut prompt_tracker = PromptTracker::new(None, true, PromptLogger::new(None));
        prompt_tracker.feed_output(b"ready\n");

        let sent_newline = execute_voice_navigation_action(
            VoiceNavigationAction::SendStagedInput,
            &prompt_tracker,
            &mut session,
            &writer_tx,
            &mut deadline,
            &mut current_status,
            &mut status_state,
        );

        assert!(!sent_newline);
        assert!(session.sent.is_empty());
        assert!(status_state.message.contains("Nothing to send"));
    }

    #[test]
    fn execute_voice_navigation_send_without_staged_text_still_submits_in_auto_mode() {
        let mut session = StubSession::default();
        let mut status_state = StatusLineState::new();
        status_state.send_mode = VoiceSendMode::Auto;
        let (writer_tx, _writer_rx) = crossbeam_channel::unbounded();
        let mut deadline = None;
        let mut current_status = None;
        let mut prompt_tracker = PromptTracker::new(None, true, PromptLogger::new(None));
        prompt_tracker.feed_output(b"ready\n");

        let sent_newline = execute_voice_navigation_action(
            VoiceNavigationAction::SendStagedInput,
            &prompt_tracker,
            &mut session,
            &writer_tx,
            &mut deadline,
            &mut current_status,
            &mut status_state,
        );

        assert!(sent_newline);
        assert_eq!(session.sent, vec!["\r".to_string()]);
        assert!(status_state.message.contains("Voice command: send"));
    }

    #[test]
    fn execute_voice_navigation_show_last_error_updates_status() {
        let mut session = StubSession::default();
        let mut status_state = StatusLineState::new();
        let (writer_tx, _writer_rx) = crossbeam_channel::unbounded();
        let mut deadline = None;
        let mut current_status = None;
        let mut prompt_tracker = PromptTracker::new(None, true, PromptLogger::new(None));
        prompt_tracker.feed_output(b"compile error: missing semicolon\n");

        let sent_newline = execute_voice_navigation_action(
            VoiceNavigationAction::ShowLastError,
            &prompt_tracker,
            &mut session,
            &writer_tx,
            &mut deadline,
            &mut current_status,
            &mut status_state,
        );

        assert!(!sent_newline);
        assert!(status_state.message.contains("Last error:"));
        assert!(status_state.message.contains("missing semicolon"));
    }

    #[test]
    fn execute_voice_navigation_copy_last_error_without_capture_sets_status() {
        let mut session = StubSession::default();
        let mut status_state = StatusLineState::new();
        let (writer_tx, _writer_rx) = crossbeam_channel::unbounded();
        let mut deadline = None;
        let mut current_status = None;
        let prompt_tracker = PromptTracker::new(None, true, PromptLogger::new(None));

        let sent_newline = execute_voice_navigation_action(
            VoiceNavigationAction::CopyLastError,
            &prompt_tracker,
            &mut session,
            &writer_tx,
            &mut deadline,
            &mut current_status,
            &mut status_state,
        );

        assert!(!sent_newline);
        assert!(status_state.message.contains("No error captured to copy"));
    }

    #[test]
    fn execute_voice_navigation_explain_last_error_sends_prompt() {
        let mut session = StubSession::default();
        let mut status_state = StatusLineState::new();
        let (writer_tx, _writer_rx) = crossbeam_channel::unbounded();
        let mut deadline = None;
        let mut current_status = None;
        let mut prompt_tracker = PromptTracker::new(None, true, PromptLogger::new(None));
        prompt_tracker.feed_output(b"fatal error: invalid token\n");

        let sent_newline = execute_voice_navigation_action(
            VoiceNavigationAction::ExplainLastError,
            &prompt_tracker,
            &mut session,
            &writer_tx,
            &mut deadline,
            &mut current_status,
            &mut status_state,
        );

        assert!(sent_newline);
        assert_eq!(status_state.recording_state, RecordingState::Responding);
        assert_eq!(session.sent_with_newline.len(), 1);
        assert!(session.sent_with_newline[0].contains("fatal error: invalid token"));
    }
}
