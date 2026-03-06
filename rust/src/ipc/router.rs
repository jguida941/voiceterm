//! IPC command router that keeps transport commands decoupled from backend logic.

use crate::voice;
use std::sync::mpsc;
use std::thread;
use std::time::Instant;

use super::protocol::{IpcEvent, Provider};
use super::provider_lifecycle;
use super::session::{run_auth_flow, send_event, AuthJob, IpcState};

// ============================================================================
// Slash Command Parsing
// ============================================================================

#[derive(Debug)]
pub(super) enum ParsedInput {
    /// Wrapper command (handled by us)
    WrapperCommand(WrapperCmd),
    /// Provider command (forwarded to provider)
    ProviderCommand { command: String, args: String },
    /// Plain prompt
    Prompt(String),
}

#[derive(Debug)]
pub(super) enum WrapperCmd {
    Provider(String), // /provider codex|claude (gemini/aider/opencode/custom are non-IPC)
    Codex(String),    // /codex <prompt> - one-off
    Claude(String),   // /claude <prompt> - one-off
    Voice,            // /voice
    Auth(Option<String>), // /auth [provider]
    Status,           // /status
    Capabilities,     // /capabilities
    Help,             // /help
    Exit,             // /exit
}

pub(super) fn parse_input(input: &str) -> ParsedInput {
    let trimmed = input.trim();

    if !trimmed.starts_with('/') {
        return ParsedInput::Prompt(trimmed.to_string());
    }

    let parts: Vec<&str> = trimmed[1..].splitn(2, ' ').collect();
    let cmd = parts[0].to_lowercase();
    let args = parts.get(1).map(|s| s.trim()).unwrap_or("");

    match cmd.as_str() {
        "provider" => ParsedInput::WrapperCommand(WrapperCmd::Provider(args.to_string())),
        "codex" => ParsedInput::WrapperCommand(WrapperCmd::Codex(args.to_string())),
        "claude" => ParsedInput::WrapperCommand(WrapperCmd::Claude(args.to_string())),
        "voice" | "v" => ParsedInput::WrapperCommand(WrapperCmd::Voice),
        "auth" => ParsedInput::WrapperCommand(WrapperCmd::Auth(if args.is_empty() {
            None
        } else {
            Some(args.to_string())
        })),
        "status" => ParsedInput::WrapperCommand(WrapperCmd::Status),
        "capabilities" => ParsedInput::WrapperCommand(WrapperCmd::Capabilities),
        "help" | "h" => ParsedInput::WrapperCommand(WrapperCmd::Help),
        "exit" | "quit" | "q" => ParsedInput::WrapperCommand(WrapperCmd::Exit),
        // All other / commands are forwarded to provider
        _ => ParsedInput::ProviderCommand {
            command: cmd,
            args: args.to_string(),
        },
    }
}

// ============================================================================
// Command Handlers
// ============================================================================

pub(super) fn handle_send_prompt(
    state: &mut IpcState,
    prompt: &str,
    provider_override: Option<String>,
) {
    // Parse input once so wrapper commands can be conditionally allowed during auth.
    let parsed = parse_input(prompt);

    if state.current_auth_job.is_some()
        && !matches!(parsed, ParsedInput::WrapperCommand(WrapperCmd::Exit))
    {
        send_event(&IpcEvent::Error {
            message: "Authentication in progress. Finish /auth before sending prompts.".to_string(),
            recoverable: true,
        });
        return;
    }

    if let ParsedInput::WrapperCommand(cmd) = parsed {
        // Wrapper commands do not use provider overrides. Parsing overrides here
        // can block /exit while auth is active when clients send stale overrides.
        cancel_current_provider_job(state);
        handle_wrapper_command(state, cmd);
        return;
    }

    // Determine which provider to use
    let Some(provider) =
        resolve_provider_or_emit_error(state.active_provider, provider_override.as_deref())
    else {
        return;
    };

    cancel_current_provider_job(state);

    match parsed {
        ParsedInput::ProviderCommand { command, args } => {
            if provider.supports_provider_command_forwarding() {
                let full_prompt = if args.is_empty() {
                    format!("/{command}")
                } else {
                    format!("/{command} {args}")
                };
                start_provider_job(state, provider, &full_prompt);
            } else {
                send_event(&IpcEvent::ProviderError {
                    message: provider.provider_command_mismatch_message(&command, &args),
                });
            }
        }
        ParsedInput::Prompt(p) => {
            start_provider_job(state, provider, &p);
        }
        ParsedInput::WrapperCommand(_) => unreachable!("wrapper commands return early"),
    }
}

fn cancel_current_provider_job(state: &mut IpcState) {
    if let Some(provider) = provider_lifecycle::cancel_active_provider_job(state) {
        emit_cancelled_provider_job_event(provider);
    }
}

fn emit_cancelled_provider_job_event(provider: Provider) {
    send_event(&IpcEvent::JobEnd {
        provider: provider.as_str().to_string(),
        success: false,
        error: Some("Cancelled".to_string()),
    });
}

fn resolve_provider_or_emit_error(
    active_provider: Provider,
    provider_override: Option<&str>,
) -> Option<Provider> {
    match provider_override {
        Some(name) => match Provider::parse_name_or_error_message(name) {
            Ok(provider) => Some(provider),
            Err(message) => {
                send_event(&IpcEvent::Error {
                    message: message.to_string(),
                    recoverable: true,
                });
                None
            }
        },
        None => Some(active_provider),
    }
}

pub(super) fn handle_wrapper_command(state: &mut IpcState, cmd: WrapperCmd) {
    match cmd {
        WrapperCmd::Provider(p) => {
            handle_set_provider(state, &p);
        }
        WrapperCmd::Codex(prompt) => {
            if !prompt.is_empty() {
                start_provider_job(state, Provider::Codex, &prompt);
            } else {
                send_event(&IpcEvent::Error {
                    message: "Usage: /codex <prompt>".to_string(),
                    recoverable: true,
                });
            }
        }
        WrapperCmd::Claude(prompt) => {
            if !prompt.is_empty() {
                start_provider_job(state, Provider::Claude, &prompt);
            } else {
                send_event(&IpcEvent::Error {
                    message: "Usage: /claude <prompt>".to_string(),
                    recoverable: true,
                });
            }
        }
        WrapperCmd::Voice => {
            handle_start_voice(state);
        }
        WrapperCmd::Auth(provider) => {
            handle_auth_command(state, provider);
        }
        WrapperCmd::Status => {
            state.emit_capabilities();
        }
        WrapperCmd::Capabilities => {
            state.emit_capabilities();
        }
        WrapperCmd::Help => {
            send_event(&IpcEvent::Status {
                message: format!(
                    "Commands: /provider, /codex, /claude, /auth, /voice, /status, /help, /exit. All other / commands forwarded to {}. Non-IPC overlay-only backends are unavailable in IPC mode (gemini is experimental; aider/opencode/custom are non-IPC).",
                    Provider::default_ipc().as_str()
                ),
            });
        }
        WrapperCmd::Exit => {
            handle_exit(state);
        }
    }
}

pub(super) fn start_provider_job(state: &mut IpcState, provider: Provider, prompt: &str) {
    provider_lifecycle::start_provider_job(state, provider, prompt);
}

pub(super) fn handle_start_voice(state: &mut IpcState) {
    if state.current_auth_job.is_some() {
        send_event(&IpcEvent::Error {
            message: "Authentication in progress. Finish /auth before starting voice.".to_string(),
            recoverable: true,
        });
        return;
    }

    if state.current_voice_job.is_some() {
        send_event(&IpcEvent::Error {
            message: "Voice capture already in progress".to_string(),
            recoverable: true,
        });
        return;
    }

    if state.recorder.is_none() && state.config.no_python_fallback {
        send_event(&IpcEvent::Error {
            message: "No microphone available and Python fallback disabled".to_string(),
            recoverable: true,
        });
        return;
    }

    send_event(&IpcEvent::VoiceStart);

    let job = voice::start_voice_job(
        state.recorder.clone(),
        state.transcriber.clone(),
        state.config.clone(),
        None,
    );
    state.current_voice_job = Some(job);
}

fn cancel_active_jobs(state: &mut IpcState) {
    cancel_current_provider_job(state);

    if state.current_voice_job.is_some() {
        send_event(&IpcEvent::VoiceEnd {
            error: Some("Cancelled".to_string()),
        });
        state.current_voice_job = None;
    }
}

pub(super) fn handle_cancel(state: &mut IpcState) {
    state.cancelled = true;

    if state.current_auth_job.is_some() {
        send_event(&IpcEvent::Error {
            message: "Authentication in progress. Cancel from the provider prompt.".to_string(),
            recoverable: true,
        });
        return;
    }

    cancel_active_jobs(state);
}

pub(super) fn handle_exit(state: &mut IpcState) {
    state.cancelled = true;
    state.exit_requested = true;
    cancel_active_jobs(state);

    if state.current_auth_job.is_some() {
        send_event(&IpcEvent::Status {
            message: "Exit requested; waiting for authentication flow to finish.".to_string(),
        });
    } else {
        send_event(&IpcEvent::Status {
            message: "Exit requested; shutting down IPC loop.".to_string(),
        });
    }
}

pub(super) fn handle_set_provider(state: &mut IpcState, provider_str: &str) {
    match Provider::parse_name_or_error_message(provider_str) {
        Ok(provider) => {
            state.active_provider = provider;
            send_event(&IpcEvent::ProviderChanged {
                provider: provider.as_str().to_string(),
            });
        }
        Err(message) => {
            send_event(&IpcEvent::Error {
                message: message.to_string(),
                recoverable: true,
            });
        }
    }
}

pub(super) fn handle_auth_command(state: &mut IpcState, provider_override: Option<String>) {
    if state.current_auth_job.is_some() {
        send_event(&IpcEvent::Error {
            message: "Authentication already in progress".to_string(),
            recoverable: true,
        });
        return;
    }

    if state.current_job.is_some() || state.current_voice_job.is_some() {
        send_event(&IpcEvent::Error {
            message: "Finish active work before running /auth".to_string(),
            recoverable: true,
        });
        return;
    }

    let Some(provider) =
        resolve_provider_or_emit_error(state.active_provider, provider_override.as_deref())
    else {
        return;
    };

    send_event(&IpcEvent::AuthStart {
        provider: provider.as_str().to_string(),
    });

    let codex_cmd = state.config.codex_cmd.clone();
    let claude_cmd = state.claude_cmd.clone();
    let (auth_result_tx, auth_result_rx) = mpsc::channel();

    thread::spawn(move || {
        let result = run_auth_flow(provider, &codex_cmd, &claude_cmd);
        let _ = auth_result_tx.send(result);
    });

    state.current_auth_job = Some(AuthJob {
        provider,
        receiver: auth_result_rx,
        started_at: Instant::now(),
    });
}
