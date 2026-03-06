//! Regression tests for IPC protocol routing, command handling, and session behavior.

use super::protocol::*;
use super::router::*;
use super::session::*;
use crate::audio;
use crate::backend::BackendRegistry;
use crate::codex::{
    build_test_backend_job, reset_session_count, reset_session_count_reset, CodexCliBackend,
    CodexEvent, CodexEventKind, CodexJobStats, RequestMode, TestSignal,
};
use crate::config::AppConfig;
use crate::pty_session::test_pty_session;
use crate::voice::{self, VoiceError};
use crate::{PipelineJsonResult, PipelineMetrics, VoiceJob, VoiceJobMessage};
use clap::Parser;
use crossbeam_channel::bounded;
use std::env;
use std::io;
#[cfg(unix)]
use std::os::unix::io::RawFd;
use std::sync::atomic::{AtomicBool, AtomicUsize, Ordering};
use std::sync::mpsc;
use std::sync::{Arc, Mutex, OnceLock};
use std::thread;
use std::time::{Duration, Instant};

fn new_test_state(mut config: AppConfig) -> IpcState {
    config.persistent_codex = false;
    IpcState {
        config: config.clone(),
        active_provider: Provider::Codex,
        codex_cli_backend: Arc::new(CodexCliBackend::new(config)),
        claude_cmd: "claude".to_string(),
        recorder: None,
        transcriber: None,
        current_job: None,
        current_voice_job: None,
        current_auth_job: None,
        session_id: "test-session".to_string(),
        cancelled: false,
        exit_requested: false,
    }
}

fn ipc_env_lock() -> &'static Mutex<()> {
    static ENV_LOCK: OnceLock<Mutex<()>> = OnceLock::new();
    ENV_LOCK.get_or_init(|| Mutex::new(()))
}

type PythonHook = Box<
    dyn Fn(&AppConfig, Option<Arc<AtomicBool>>) -> anyhow::Result<crate::PipelineJsonResult>
        + Send
        + 'static,
>;

struct AuthHookGuard;

impl Drop for AuthHookGuard {
    fn drop(&mut self) {
        set_auth_flow_hook(None);
    }
}

fn set_auth_hook(hook: AuthFlowHook) -> AuthHookGuard {
    set_auth_flow_hook(Some(hook));
    AuthHookGuard
}

struct PythonHookGuard;

impl Drop for PythonHookGuard {
    fn drop(&mut self) {
        voice::set_python_transcription_hook(None);
    }
}

fn set_python_hook(hook: PythonHook) -> PythonHookGuard {
    voice::set_python_transcription_hook(Some(hook));
    PythonHookGuard
}

#[cfg(unix)]
fn write_stub_script(contents: &str) -> std::path::PathBuf {
    use std::fs;
    use std::os::unix::fs::PermissionsExt;
    use std::time::{SystemTime, UNIX_EPOCH};

    let mut path = std::env::temp_dir();
    let nanos = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap()
        .as_nanos();
    path.push(format!("ipc_stub_{nanos}.sh"));
    fs::write(&path, contents).expect("write stub");
    let mut perms = fs::metadata(&path).expect("stat stub").permissions();
    perms.set_mode(0o755);
    fs::set_permissions(&path, perms).expect("chmod stub");
    path
}

#[cfg(unix)]
fn make_sleeping_claude_job() -> ClaudeJob {
    let child = std::process::Command::new("sleep")
        .arg("5")
        .spawn()
        .expect("spawned child");
    let (_tx, rx) = mpsc::channel();
    ClaudeJob {
        output: ClaudeJobOutput::Piped {
            child,
            stdout_rx: rx,
        },
        started_at: Instant::now(),
        pending_exit: None,
    }
}

#[cfg(unix)]
fn pipe_pair() -> (RawFd, RawFd) {
    let mut fds = [0; 2];
    let result = unsafe { libc::pipe(fds.as_mut_ptr()) };
    assert_eq!(
        result,
        0,
        "pipe() failed with errno {}",
        io::Error::last_os_error()
    );
    (fds[0], fds[1])
}

// -------------------------------------------------------------------------
// Provider Enum Tests
// -------------------------------------------------------------------------

#[test]
fn test_provider_from_str() {
    assert_eq!(Provider::parse_name("codex"), Some(Provider::Codex));
    assert_eq!(Provider::parse_name("CODEX"), Some(Provider::Codex));
    assert_eq!(Provider::parse_name("Codex"), Some(Provider::Codex));

    assert_eq!(Provider::parse_name("claude"), Some(Provider::Claude));
    assert_eq!(Provider::parse_name("CLAUDE"), Some(Provider::Claude));
    assert_eq!(Provider::parse_name("Claude"), Some(Provider::Claude));
    assert_eq!(Provider::parse_name("gemini"), None);
    assert_eq!(Provider::parse_name("aider"), None);
    assert_eq!(Provider::parse_name("opencode"), None);
    assert_eq!(Provider::parse_name("custom"), None);

    assert_eq!(Provider::parse_name("unknown"), None);
    assert_eq!(Provider::parse_name(""), None);
    assert_eq!(Provider::parse_name("openai"), None);
}

#[test]
fn test_provider_parse_name_or_error_message() {
    assert_eq!(
        Provider::parse_name_or_error_message("codex"),
        Ok(Provider::Codex)
    );
    assert!(Provider::parse_name_or_error_message("gemini")
        .is_err_and(|msg| msg.to_string().contains("overlay-only experimental")));
    assert!(Provider::parse_name_or_error_message("aider")
        .is_err_and(|msg| msg.to_string().contains("overlay-only non-IPC")));
    assert!(Provider::parse_name_or_error_message("opencode")
        .is_err_and(|msg| msg.to_string().contains("overlay-only non-IPC")));
    assert!(Provider::parse_name_or_error_message("custom")
        .is_err_and(|msg| msg.to_string().contains("overlay-only non-IPC")));
    assert!(Provider::parse_name_or_error_message("unknown")
        .is_err_and(|msg| msg.to_string().contains("Unknown provider")));
}

#[test]
fn test_provider_from_str_trait() {
    use std::str::FromStr;

    assert_eq!(Provider::from_str("codex"), Ok(Provider::Codex));
    assert_eq!(Provider::from_str("claude"), Ok(Provider::Claude));
    assert!(Provider::from_str("unknown").is_err());
}

#[test]
fn test_provider_as_str() {
    assert_eq!(Provider::Codex.as_str(), "codex");
    assert_eq!(Provider::Claude.as_str(), "claude");
}

#[test]
fn test_provider_auth_command_routes_by_lifecycle() {
    assert_eq!(
        Provider::Codex.auth_command("codex-auth", "claude-auth"),
        "codex-auth"
    );
    assert_eq!(
        Provider::Claude.auth_command("codex-auth", "claude-auth"),
        "claude-auth"
    );
}

#[test]
fn test_provider_auth_success_session_reset_policy() {
    assert!(Provider::Codex.resets_session_on_auth_success());
    assert!(!Provider::Claude.resets_session_on_auth_success());
}

#[test]
fn test_provider_ipc_capability_labels_derive_from_supported_set() {
    let mut expected_providers = Vec::new();
    for backend_name in BackendRegistry::new().available_backends() {
        if let Some(provider) = Provider::parse_name(backend_name) {
            if !expected_providers.contains(&provider) {
                expected_providers.push(provider);
            }
        }
    }
    if expected_providers.is_empty() {
        expected_providers.extend([Provider::Codex, Provider::Claude]);
    }

    assert_eq!(Provider::ipc_supported(), expected_providers.as_slice());
    let expected = expected_providers
        .iter()
        .map(|provider| provider.as_str().to_string())
        .collect::<Vec<_>>();
    assert_eq!(Provider::ipc_capability_labels(), expected);
    assert_eq!(
        Provider::default_ipc(),
        expected_providers
            .first()
            .copied()
            .unwrap_or(Provider::Codex)
    );
}

#[test]
fn ipc_state_invalid_voiceterm_provider_emits_recoverable_startup_error() {
    let _env_guard = ipc_env_lock()
        .lock()
        .unwrap_or_else(|poisoned| poisoned.into_inner());
    let previous_override = env::var("VOICETERM_PROVIDER").ok();
    env::set_var("VOICETERM_PROVIDER", "gemini");

    let snapshot = event_snapshot();
    let state = IpcState::new(AppConfig::parse_from(["test-app"]));
    let events = events_since(snapshot);

    match previous_override {
        Some(value) => env::set_var("VOICETERM_PROVIDER", value),
        None => env::remove_var("VOICETERM_PROVIDER"),
    }

    assert_eq!(state.active_provider, Provider::default_ipc());
    assert!(events.iter().any(|event| {
        matches!(
            event,
            IpcEvent::Error {
                message,
                recoverable: true
            } if message.contains("Invalid VOICETERM_PROVIDER override")
                && message.contains("overlay-only experimental")
        )
    }));
}

#[test]
fn utf8_prefix_truncates_by_chars_not_bytes() {
    let preview = utf8_prefix("a😀b", 2);
    assert_eq!(preview, "a😀");
}

// -------------------------------------------------------------------------
// Input Parsing Tests
// -------------------------------------------------------------------------

#[test]
fn test_parse_plain_prompt() {
    match parse_input("hello world") {
        ParsedInput::Prompt(p) => assert_eq!(p, "hello world"),
        _ => panic!("Expected Prompt"),
    }

    match parse_input("  hello world  ") {
        ParsedInput::Prompt(p) => assert_eq!(p, "hello world"),
        _ => panic!("Expected Prompt with trimmed content"),
    }
}

#[test]
fn test_parse_wrapper_commands() {
    // /provider
    match parse_input("/provider codex") {
        ParsedInput::WrapperCommand(WrapperCmd::Provider(p)) => assert_eq!(p, "codex"),
        _ => panic!("Expected Provider command"),
    }

    // /codex
    match parse_input("/codex hello world") {
        ParsedInput::WrapperCommand(WrapperCmd::Codex(p)) => assert_eq!(p, "hello world"),
        _ => panic!("Expected Codex command"),
    }

    // /claude
    match parse_input("/claude hello world") {
        ParsedInput::WrapperCommand(WrapperCmd::Claude(p)) => assert_eq!(p, "hello world"),
        _ => panic!("Expected Claude command"),
    }

    // /voice
    match parse_input("/voice") {
        ParsedInput::WrapperCommand(WrapperCmd::Voice) => {}
        _ => panic!("Expected Voice command"),
    }

    // /auth (default provider)
    match parse_input("/auth") {
        ParsedInput::WrapperCommand(WrapperCmd::Auth(None)) => {}
        _ => panic!("Expected Auth command with default provider"),
    }

    // /auth codex
    match parse_input("/auth codex") {
        ParsedInput::WrapperCommand(WrapperCmd::Auth(Some(provider))) => {
            assert_eq!(provider, "codex");
        }
        _ => panic!("Expected Auth command with provider"),
    }

    // /v (alias)
    match parse_input("/v") {
        ParsedInput::WrapperCommand(WrapperCmd::Voice) => {}
        _ => panic!("Expected Voice command from alias"),
    }

    // /status
    match parse_input("/status") {
        ParsedInput::WrapperCommand(WrapperCmd::Status) => {}
        _ => panic!("Expected Status command"),
    }

    // /help
    match parse_input("/help") {
        ParsedInput::WrapperCommand(WrapperCmd::Help) => {}
        _ => panic!("Expected Help command"),
    }

    // /h (alias)
    match parse_input("/h") {
        ParsedInput::WrapperCommand(WrapperCmd::Help) => {}
        _ => panic!("Expected Help command from alias"),
    }

    // /exit
    match parse_input("/exit") {
        ParsedInput::WrapperCommand(WrapperCmd::Exit) => {}
        _ => panic!("Expected Exit command"),
    }

    // /quit (alias)
    match parse_input("/quit") {
        ParsedInput::WrapperCommand(WrapperCmd::Exit) => {}
        _ => panic!("Expected Exit command from quit alias"),
    }

    // /q (alias)
    match parse_input("/q") {
        ParsedInput::WrapperCommand(WrapperCmd::Exit) => {}
        _ => panic!("Expected Exit command from q alias"),
    }
}

#[test]
fn test_parse_provider_commands() {
    // Provider-specific commands should be forwarded to Codex
    match parse_input("/model gpt-4") {
        ParsedInput::ProviderCommand { command, args } => {
            assert_eq!(command, "model");
            assert_eq!(args, "gpt-4");
        }
        _ => panic!("Expected ProviderCommand"),
    }

    match parse_input("/context") {
        ParsedInput::ProviderCommand { command, args } => {
            assert_eq!(command, "context");
            assert_eq!(args, "");
        }
        _ => panic!("Expected ProviderCommand with no args"),
    }

    match parse_input("/run bash -c 'echo hello'") {
        ParsedInput::ProviderCommand { command, args } => {
            assert_eq!(command, "run");
            assert_eq!(args, "bash -c 'echo hello'");
        }
        _ => panic!("Expected ProviderCommand with complex args"),
    }
}

#[test]
fn test_parse_case_insensitive() {
    // Commands should be case-insensitive
    match parse_input("/PROVIDER codex") {
        ParsedInput::WrapperCommand(WrapperCmd::Provider(_)) => {}
        _ => panic!("Expected Provider command (uppercase)"),
    }

    match parse_input("/Provider codex") {
        ParsedInput::WrapperCommand(WrapperCmd::Provider(_)) => {}
        _ => panic!("Expected Provider command (mixed case)"),
    }

    match parse_input("/CODEX hello") {
        ParsedInput::WrapperCommand(WrapperCmd::Codex(_)) => {}
        _ => panic!("Expected Codex command (uppercase)"),
    }
}

#[test]
fn test_parse_capabilities_command() {
    match parse_input("/capabilities") {
        ParsedInput::WrapperCommand(WrapperCmd::Capabilities) => {}
        _ => panic!("Expected Capabilities command"),
    }
}

#[test]
fn emit_capabilities_reports_state() {
    let snapshot = event_snapshot();
    let mut config = AppConfig::parse_from(["test-app", "--no-python-fallback"]);
    config.whisper_model_path = None;
    let state = new_test_state(config);

    state.emit_capabilities();

    let events = events_since(snapshot);
    let caps = events.iter().find_map(|event| match event {
        IpcEvent::Capabilities {
            mic_available,
            whisper_model_loaded,
            python_fallback_allowed,
            providers_available,
            active_provider,
            ..
        } => Some((
            *mic_available,
            *whisper_model_loaded,
            *python_fallback_allowed,
            providers_available.clone(),
            active_provider.clone(),
        )),
        _ => None,
    });
    assert!(caps.is_some());
    let (
        mic_available,
        whisper_loaded,
        python_fallback_allowed,
        providers_available,
        active_provider,
    ) = caps.unwrap();
    assert!(!mic_available);
    assert!(!whisper_loaded);
    assert!(!python_fallback_allowed);
    assert_eq!(providers_available, Provider::ipc_capability_labels());
    assert_eq!(active_provider, "codex");
}

#[test]
fn handle_set_provider_emits_events() {
    let snapshot = event_snapshot();
    let mut state = new_test_state(AppConfig::parse_from(["test-app"]));

    handle_set_provider(&mut state, "claude");
    assert_eq!(state.active_provider, Provider::Claude);
    let events = events_since(snapshot);
    assert!(events.iter().any(|event| {
        matches!(event, IpcEvent::ProviderChanged { provider } if provider == "claude")
    }));

    let snapshot = event_snapshot();
    handle_set_provider(&mut state, "unknown");
    let events = events_since(snapshot);
    assert!(events.iter().any(|event| {
        matches!(event, IpcEvent::Error { message, .. } if message.contains("Unknown provider"))
    }));

    let snapshot = event_snapshot();
    handle_set_provider(&mut state, "gemini");
    let events = events_since(snapshot);
    assert!(events.iter().any(|event| {
        matches!(event, IpcEvent::Error { message, .. } if message.contains("overlay-only experimental"))
    }));

    for provider in ["aider", "opencode", "custom"] {
        let snapshot = event_snapshot();
        handle_set_provider(&mut state, provider);
        let events = events_since(snapshot);
        assert!(events.iter().any(|event| {
            matches!(event, IpcEvent::Error { message, .. } if message.contains("overlay-only non-IPC"))
        }));
    }
}

#[test]
fn handle_send_prompt_blocks_during_auth() {
    let snapshot = event_snapshot();
    let mut state = new_test_state(AppConfig::parse_from(["test-app"]));
    let (_tx, rx) = mpsc::channel();
    state.current_auth_job = Some(AuthJob {
        provider: Provider::Codex,
        receiver: rx,
        started_at: Instant::now(),
    });

    handle_send_prompt(&mut state, "hello", None);
    let events = events_since(snapshot);
    assert!(events.iter().any(|event| {
            matches!(event, IpcEvent::Error { message, .. } if message.contains("Authentication in progress"))
        }));
}

#[test]
fn handle_send_prompt_rejects_provider_commands_on_claude() {
    let snapshot = event_snapshot();
    let mut state = new_test_state(AppConfig::parse_from(["test-app"]));
    state.active_provider = Provider::Claude;

    handle_send_prompt(&mut state, "/model gpt-4", None);

    let events = events_since(snapshot);
    assert!(events.iter().any(|event| {
        matches!(event, IpcEvent::ProviderError { message } if message.contains("Codex command"))
    }));
}

#[test]
fn handle_send_prompt_rejects_invalid_provider_override() {
    let snapshot = event_snapshot();
    let mut state = new_test_state(AppConfig::parse_from(["test-app"]));
    state.active_provider = Provider::Claude;

    handle_send_prompt(&mut state, "hello", Some("gemini".to_string()));

    let events = events_since(snapshot);
    assert!(events.iter().any(|event| {
        matches!(event, IpcEvent::Error { message, .. } if message.contains("overlay-only experimental"))
    }));
    assert!(state.current_job.is_none());
}

#[test]
fn handle_send_prompt_rejects_overlay_only_non_ipc_provider_overrides() {
    for provider in ["aider", "opencode", "custom"] {
        let snapshot = event_snapshot();
        let mut state = new_test_state(AppConfig::parse_from(["test-app"]));
        state.active_provider = Provider::Claude;

        handle_send_prompt(&mut state, "hello", Some(provider.to_string()));

        let events = events_since(snapshot);
        assert!(events.iter().any(|event| {
            matches!(event, IpcEvent::Error { message, .. } if message.contains("overlay-only non-IPC"))
        }));
        assert!(state.current_job.is_none());
    }
}

#[test]
fn handle_send_prompt_invalid_provider_override_keeps_active_job() {
    let snapshot = event_snapshot();
    let mut state = new_test_state(AppConfig::parse_from(["test-app"]));
    state.current_job = Some(ActiveJob::Codex(build_test_backend_job(
        Vec::new(),
        TestSignal::Ready,
    )));

    handle_send_prompt(&mut state, "hello", Some("gemini".to_string()));

    let events = events_since(snapshot);
    assert!(events.iter().any(|event| {
        matches!(event, IpcEvent::Error { message, .. } if message.contains("overlay-only experimental"))
    }));
    assert!(state.current_job.is_some());
}

#[test]
fn handle_auth_command_rejects_invalid_provider_override() {
    let snapshot = event_snapshot();
    let mut state = new_test_state(AppConfig::parse_from(["test-app"]));

    handle_auth_command(&mut state, Some("gemini".to_string()));

    let events = events_since(snapshot);
    assert!(events.iter().any(|event| {
        matches!(event, IpcEvent::Error { message, .. } if message.contains("overlay-only experimental"))
    }));
    assert!(state.current_auth_job.is_none());
}

#[test]
fn handle_auth_command_rejects_overlay_only_non_ipc_provider_overrides() {
    for provider in ["aider", "opencode", "custom"] {
        let snapshot = event_snapshot();
        let mut state = new_test_state(AppConfig::parse_from(["test-app"]));

        handle_auth_command(&mut state, Some(provider.to_string()));

        let events = events_since(snapshot);
        assert!(events.iter().any(|event| {
            matches!(event, IpcEvent::Error { message, .. } if message.contains("overlay-only non-IPC"))
        }));
        assert!(state.current_auth_job.is_none());
    }
}

#[test]
fn handle_wrapper_help_emits_status() {
    let snapshot = event_snapshot();
    let mut state = new_test_state(AppConfig::parse_from(["test-app"]));
    handle_wrapper_command(&mut state, WrapperCmd::Help);
    let events = events_since(snapshot);
    assert!(events.iter().any(|event| {
        matches!(event, IpcEvent::Status { message } if message.contains("Commands:"))
    }));
}

#[test]
fn handle_wrapper_status_emits_capabilities() {
    let snapshot = event_snapshot();
    let mut state = new_test_state(AppConfig::parse_from(["test-app"]));
    handle_wrapper_command(&mut state, WrapperCmd::Status);
    let events = events_since(snapshot);
    assert!(events
        .iter()
        .any(|event| matches!(event, IpcEvent::Capabilities { .. })));
}

#[test]
fn handle_wrapper_capabilities_emits_capabilities() {
    let snapshot = event_snapshot();
    let mut state = new_test_state(AppConfig::parse_from(["test-app"]));
    handle_wrapper_command(&mut state, WrapperCmd::Capabilities);
    let events = events_since(snapshot);
    assert!(events
        .iter()
        .any(|event| matches!(event, IpcEvent::Capabilities { .. })));
}

#[test]
fn handle_wrapper_requires_prompt_for_codex_and_claude() {
    let snapshot = event_snapshot();
    let mut state = new_test_state(AppConfig::parse_from(["test-app"]));
    handle_wrapper_command(&mut state, WrapperCmd::Codex(String::new()));
    handle_wrapper_command(&mut state, WrapperCmd::Claude(String::new()));
    let events = events_since(snapshot);
    assert!(events.iter().any(|event| {
        matches!(event, IpcEvent::Error { message, .. } if message.contains("Usage: /codex"))
    }));
    assert!(events.iter().any(|event| {
        matches!(event, IpcEvent::Error { message, .. } if message.contains("Usage: /claude"))
    }));
}

#[test]
fn handle_wrapper_exit_requests_graceful_shutdown() {
    let snapshot = event_snapshot();
    let mut state = new_test_state(AppConfig::parse_from(["test-app"]));

    handle_wrapper_command(&mut state, WrapperCmd::Exit);

    assert!(state.exit_requested);
    assert!(state.cancelled);
    let events = events_since(snapshot);
    assert!(events.iter().any(|event| {
        matches!(event, IpcEvent::Status { message } if message.contains("Exit requested"))
    }));
}

#[test]
fn handle_send_prompt_allows_exit_during_auth() {
    let snapshot = event_snapshot();
    let mut state = new_test_state(AppConfig::parse_from(["test-app"]));
    let (_tx, rx) = mpsc::channel();
    state.current_auth_job = Some(AuthJob {
        provider: Provider::Codex,
        receiver: rx,
        started_at: Instant::now(),
    });

    handle_send_prompt(&mut state, "/exit", None);

    assert!(state.exit_requested);
    let events = events_since(snapshot);
    assert!(events.iter().any(|event| {
        matches!(event, IpcEvent::Status { message } if message.contains("Exit requested"))
    }));
}

#[test]
fn handle_send_prompt_allows_exit_during_auth_with_invalid_provider_override() {
    let snapshot = event_snapshot();
    let mut state = new_test_state(AppConfig::parse_from(["test-app"]));
    let (_tx, rx) = mpsc::channel();
    state.current_auth_job = Some(AuthJob {
        provider: Provider::Codex,
        receiver: rx,
        started_at: Instant::now(),
    });

    handle_send_prompt(&mut state, "/exit", Some("gemini".to_string()));

    assert!(state.exit_requested);
    let events = events_since(snapshot);
    assert!(events.iter().any(|event| {
        matches!(event, IpcEvent::Status { message } if message.contains("Exit requested"))
    }));
    assert!(!events.iter().any(|event| {
        matches!(event, IpcEvent::Error { message, .. } if message.contains("overlay-only experimental"))
    }));
}

#[test]
fn handle_send_prompt_wrapper_command_ignores_invalid_provider_override() {
    let snapshot = event_snapshot();
    let mut state = new_test_state(AppConfig::parse_from(["test-app"]));

    handle_send_prompt(&mut state, "/help", Some("gemini".to_string()));

    let events = events_since(snapshot);
    assert!(events.iter().any(
        |event| matches!(event, IpcEvent::Status { message } if message.contains("Commands:"))
    ));
    assert!(!events.iter().any(|event| {
        matches!(event, IpcEvent::Error { message, .. } if message.contains("overlay-only experimental"))
    }));
}

#[test]
fn handle_send_prompt_wrapper_command_cancels_active_job_with_job_end_event() {
    let snapshot = event_snapshot();
    let mut state = new_test_state(AppConfig::parse_from(["test-app"]));
    state.current_job = Some(ActiveJob::Codex(build_test_backend_job(
        Vec::new(),
        TestSignal::Ready,
    )));

    handle_send_prompt(&mut state, "/help", None);

    assert!(state.current_job.is_none());
    let events = events_since(snapshot);
    assert!(events.iter().any(|event| {
        matches!(
            event,
            IpcEvent::JobEnd {
                provider,
                success,
                error
            } if provider == "codex" && !*success && error.as_deref() == Some("Cancelled")
        )
    }));
}

#[cfg(unix)]
#[test]
fn handle_send_prompt_wrapper_command_cancels_active_claude_job_with_job_end_event() {
    let snapshot = event_snapshot();
    let mut state = new_test_state(AppConfig::parse_from(["test-app"]));
    state.current_job = Some(ActiveJob::Claude(make_sleeping_claude_job()));

    handle_send_prompt(&mut state, "/help", None);

    assert!(state.current_job.is_none());
    let events = events_since(snapshot);
    assert!(events.iter().any(|event| {
        matches!(
            event,
            IpcEvent::JobEnd {
                provider,
                success,
                error
            } if provider == "claude" && !*success && error.as_deref() == Some("Cancelled")
        )
    }));
}

#[test]
fn handle_send_prompt_new_prompt_cancels_active_job_with_job_end_event() {
    let snapshot = event_snapshot();
    let mut state = new_test_state(AppConfig::parse_from(["test-app"]));
    state.current_job = Some(ActiveJob::Codex(build_test_backend_job(
        Vec::new(),
        TestSignal::Ready,
    )));

    handle_send_prompt(&mut state, "hello", None);

    let events = events_since(snapshot);
    assert!(events.iter().any(|event| {
        matches!(
            event,
            IpcEvent::JobEnd {
                provider,
                success,
                error
            } if provider == "codex" && !*success && error.as_deref() == Some("Cancelled")
        )
    }));
    assert!(events
        .iter()
        .any(|event| { matches!(event, IpcEvent::JobStart { provider } if provider == "codex") }));
}

#[test]
fn run_ipc_mode_emits_capabilities_on_start() {
    let snapshot = event_snapshot();
    let config = AppConfig::parse_from(["test-app"]);
    run_ipc_mode(config).unwrap();
    let events = events_since(snapshot);
    assert!(events
        .iter()
        .any(|event| matches!(event, IpcEvent::Capabilities { .. })));
}

#[test]
fn run_ipc_loop_processes_commands() {
    let snapshot = event_snapshot();
    let mut state = new_test_state(AppConfig::parse_from(["test-app"]));
    let (tx, rx) = mpsc::channel();
    tx.send(IpcCommand::GetCapabilities).unwrap();
    tx.send(IpcCommand::SetProvider {
        provider: "claude".to_string(),
    })
    .unwrap();
    drop(tx);
    run_ipc_loop(&mut state, &rx, Some(10)).unwrap();
    let events = events_since(snapshot);
    assert!(events
        .iter()
        .any(|event| matches!(event, IpcEvent::Capabilities { .. })));
    assert!(events.iter().any(|event| {
        matches!(event, IpcEvent::ProviderChanged { provider } if provider == "claude")
    }));
}

#[test]
fn run_ipc_loop_processes_active_jobs() {
    let snapshot = event_snapshot();
    let mut state = new_test_state(AppConfig::parse_from(["test-app"]));

    let now = Instant::now();
    let stats = CodexJobStats {
        backend_type: "cli",
        started_at: now,
        first_token_at: None,
        finished_at: now,
        tokens_received: 0,
        bytes_transferred: 0,
        pty_attempts: 0,
        cli_fallback_used: false,
        disable_pty: false,
    };
    let events = vec![CodexEvent {
        job_id: 1,
        kind: CodexEventKind::Finished {
            lines: vec!["ok".to_string()],
            status: "ok".to_string(),
            stats,
        },
    }];
    state.current_job = Some(ActiveJob::Codex(build_test_backend_job(
        events,
        TestSignal::Ready,
    )));

    let (voice_tx, voice_rx) = mpsc::channel();
    voice_tx
        .send(VoiceJobMessage::Transcript {
            text: "hello".to_string(),
            source: voice::VoiceCaptureSource::Native,
            metrics: None,
        })
        .unwrap();
    state.current_voice_job = Some(VoiceJob {
        receiver: voice_rx,
        handle: None,
        stop_flag: Arc::new(AtomicBool::new(false)),
        capture_active: Arc::new(AtomicBool::new(false)),
    });

    let (auth_tx, auth_rx) = mpsc::channel();
    auth_tx.send(Ok(())).unwrap();
    state.current_auth_job = Some(AuthJob {
        provider: Provider::Codex,
        receiver: auth_rx,
        started_at: Instant::now(),
    });

    let (_cmd_tx, cmd_rx) = mpsc::channel();
    run_ipc_loop(&mut state, &cmd_rx, Some(2)).unwrap();

    assert!(state.current_job.is_none());
    assert!(state.current_voice_job.is_none());
    assert!(state.current_auth_job.is_none());

    let events = events_since(snapshot);
    assert!(events.iter().any(|event| {
        matches!(event, IpcEvent::JobEnd { provider, success, .. } if provider == "codex" && *success)
    }));
    assert!(events
        .iter()
        .any(|event| { matches!(event, IpcEvent::Transcript { text, .. } if text == "hello") }));
    assert!(events.iter().any(|event| {
        matches!(event, IpcEvent::AuthEnd { provider, success, .. } if provider == "codex" && *success)
    }));
}

#[test]
fn run_ipc_loop_respects_max_loops_with_live_channel() {
    ipc_loop_count_reset();
    let mut state = new_test_state(AppConfig::parse_from(["test-app"]));
    let (_tx, rx) = mpsc::channel();
    let start = Instant::now();
    run_ipc_loop(&mut state, &rx, Some(3)).unwrap();
    assert_eq!(ipc_loop_count(), 3);
    assert!(start.elapsed() < Duration::from_secs(1));
}

#[test]
fn ipc_guard_trips_only_after_threshold() {
    assert!(!ipc_guard_tripped(Duration::from_secs(1)));
    assert!(!ipc_guard_tripped(Duration::from_secs(2)));
    assert!(ipc_guard_tripped(
        Duration::from_secs(2) + Duration::from_millis(1)
    ));
}

#[test]
fn run_ipc_loop_breaks_when_limit_zero() {
    ipc_loop_count_reset();
    let mut state = new_test_state(AppConfig::parse_from(["test-app"]));
    let (_tx, rx) = mpsc::channel();
    run_ipc_loop(&mut state, &rx, Some(0)).unwrap();
    assert_eq!(ipc_loop_count(), 1);
}

#[test]
fn run_ipc_loop_exits_when_graceful_exit_requested_and_idle() {
    let mut state = new_test_state(AppConfig::parse_from(["test-app"]));
    state.exit_requested = true;
    let (_tx, rx) = mpsc::channel();
    let start = Instant::now();
    run_ipc_loop(&mut state, &rx, Some(1000)).unwrap();
    assert!(start.elapsed() < Duration::from_millis(50));
}

#[cfg(unix)]
#[test]
fn start_provider_job_codex_emits_completion() {
    let snapshot = event_snapshot();
    let mut config = AppConfig::parse_from(["test-app"]);
    config.codex_cmd = "/path/does/not/exist".to_string();
    let mut state = new_test_state(config);

    start_provider_job(&mut state, Provider::Codex, "hello");

    let start = Instant::now();
    while start.elapsed() < Duration::from_secs(2) {
        if let Some(ActiveJob::Codex(job)) = &mut state.current_job {
            if process_codex_events(job, false) {
                state.current_job = None;
                break;
            }
        }
        thread::sleep(Duration::from_millis(10));
    }

    assert!(state.current_job.is_none(), "codex job did not complete");
    let events = events_since(snapshot);
    assert!(events
        .iter()
        .any(|event| { matches!(event, IpcEvent::JobStart { provider } if provider == "codex") }));
    assert!(events.iter().any(|event| {
            matches!(event, IpcEvent::JobEnd { provider, success, .. } if provider == "codex" && !*success)
        }));
}

#[cfg(unix)]
#[test]
fn process_claude_events_emits_tokens_and_end() {
    let snapshot = event_snapshot();
    let (tx, rx) = mpsc::channel();
    tx.send("hello from claude".to_string()).unwrap();
    let child = std::process::Command::new("true")
        .spawn()
        .expect("spawned child");
    let mut job = ClaudeJob {
        output: ClaudeJobOutput::Piped {
            child,
            stdout_rx: rx,
        },
        started_at: Instant::now(),
        pending_exit: None,
    };

    assert!(!process_claude_events(&mut job, false));
    let start = Instant::now();
    let mut finished = false;
    while start.elapsed() < Duration::from_secs(1) {
        if process_claude_events(&mut job, false) {
            finished = true;
            break;
        }
        thread::sleep(Duration::from_millis(10));
    }
    assert!(finished);
    let events = events_since(snapshot);
    assert!(events
        .iter()
        .any(|event| matches!(event, IpcEvent::Token { .. })));
    assert!(events.iter().any(|event| {
        matches!(event, IpcEvent::JobEnd { provider, .. } if provider == "claude")
    }));
}

#[cfg(unix)]
#[test]
fn claude_job_cancel_kills_piped_child() {
    let (_tx, rx) = mpsc::channel();
    let child = std::process::Command::new("sleep")
        .arg("5")
        .spawn()
        .expect("spawned child");
    let mut job = ClaudeJob {
        output: ClaudeJobOutput::Piped {
            child,
            stdout_rx: rx,
        },
        started_at: Instant::now(),
        pending_exit: None,
    };

    job.cancel();

    if let ClaudeJobOutput::Piped { child, .. } = &mut job.output {
        let start = Instant::now();
        let mut exited = false;
        while start.elapsed() < Duration::from_millis(200) {
            if let Ok(Some(_)) = child.try_wait() {
                exited = true;
                break;
            }
            thread::sleep(Duration::from_millis(10));
        }
        if !exited {
            let _ = child.kill();
            let _ = child.wait();
            panic!("claude piped child still running after cancel");
        }
    }
}

#[cfg(unix)]
#[test]
fn claude_job_cancel_sends_ctrl_c_for_pty() {
    let (read_fd, write_fd) = pipe_pair();
    let (_tx, rx) = bounded(1);
    let session = test_pty_session(write_fd, -1, -1, rx);
    let mut job = ClaudeJob {
        output: ClaudeJobOutput::Pty { session },
        started_at: Instant::now(),
        pending_exit: None,
    };

    job.cancel();

    let mut buf = [0u8; 8];
    let n = unsafe { libc::read(read_fd, buf.as_mut_ptr() as *mut _, buf.len()) };
    unsafe { libc::close(read_fd) };
    assert!(n > 0);
    assert_eq!(buf[0], 0x03);
}

#[cfg(unix)]
#[test]
fn process_claude_events_pty_ignores_empty_output() {
    let snapshot = event_snapshot();
    let (tx, rx) = bounded(1);
    tx.send(Vec::new()).unwrap();
    let session = test_pty_session(-1, -1, -1, rx);
    let mut job = ClaudeJob {
        output: ClaudeJobOutput::Pty { session },
        started_at: Instant::now(),
        pending_exit: None,
    };

    assert!(!process_claude_events(&mut job, false));
    let events = events_since(snapshot);
    assert!(
        !events
            .iter()
            .any(|event| matches!(event, IpcEvent::Token { .. })),
        "empty PTY output should not emit tokens"
    );
}

#[cfg(unix)]
#[test]
fn process_claude_events_pty_exits_without_trailing_output() {
    let snapshot = event_snapshot();
    let (_tx, rx) = bounded(1);
    let mut child = std::process::Command::new("true")
        .spawn()
        .expect("spawned child");
    let pid = child.id() as i32;
    thread::sleep(Duration::from_millis(10));
    let session = test_pty_session(-1, -1, pid, rx);
    let mut job = ClaudeJob {
        output: ClaudeJobOutput::Pty { session },
        started_at: Instant::now(),
        pending_exit: None,
    };

    let start = Instant::now();
    let mut done = false;
    while start.elapsed() < Duration::from_millis(200) {
        if process_claude_events(&mut job, false) {
            done = true;
            break;
        }
        thread::sleep(Duration::from_millis(10));
    }
    assert!(done, "job should end promptly without trailing output");
    assert!(job.pending_exit.is_none());
    let events = events_since(snapshot);
    assert!(
        events.iter().any(
            |event| matches!(event, IpcEvent::JobEnd { provider, .. } if provider == "claude")
        ),
        "expected JobEnd for claude PTY job"
    );
    let _ = child.wait();
}

#[test]
fn process_voice_events_handles_transcript() {
    let snapshot = event_snapshot();
    let (tx, rx) = mpsc::channel();
    let job = VoiceJob {
        receiver: rx,
        handle: None,
        stop_flag: Arc::new(AtomicBool::new(false)),
        capture_active: Arc::new(AtomicBool::new(false)),
    };
    tx.send(VoiceJobMessage::Transcript {
        text: "hello".to_string(),
        source: voice::VoiceCaptureSource::Native,
        metrics: Some(audio::CaptureMetrics {
            capture_ms: 123,
            ..Default::default()
        }),
    })
    .unwrap();

    assert!(process_voice_events(&job, false));

    let events = events_since(snapshot);
    assert!(events
        .iter()
        .any(|event| { matches!(event, IpcEvent::VoiceEnd { error } if error.is_none()) }));
    assert!(events.iter().any(|event| {
        matches!(event, IpcEvent::Transcript { text, duration_ms } if text == "hello" && *duration_ms == 123)
    }));
}

#[test]
fn process_voice_events_handles_empty() {
    let snapshot = event_snapshot();
    let (tx, rx) = mpsc::channel();
    let job = VoiceJob {
        receiver: rx,
        handle: None,
        stop_flag: Arc::new(AtomicBool::new(false)),
        capture_active: Arc::new(AtomicBool::new(false)),
    };
    tx.send(VoiceJobMessage::Empty {
        source: voice::VoiceCaptureSource::Native,
        metrics: None,
    })
    .unwrap();

    assert!(process_voice_events(&job, false));
    let events = events_since(snapshot);
    assert!(events.iter().any(|event| {
            matches!(event, IpcEvent::VoiceEnd { error } if error.as_deref() == Some("No speech detected"))
        }));
}

#[test]
fn process_voice_events_handles_error() {
    let snapshot = event_snapshot();
    let (tx, rx) = mpsc::channel();
    let job = VoiceJob {
        receiver: rx,
        handle: None,
        stop_flag: Arc::new(AtomicBool::new(false)),
        capture_active: Arc::new(AtomicBool::new(false)),
    };
    tx.send(VoiceJobMessage::Error(VoiceError::Message(
        "boom".to_string(),
    )))
    .unwrap();

    assert!(process_voice_events(&job, false));
    let events = events_since(snapshot);
    assert!(events.iter().any(|event| {
        matches!(event, IpcEvent::VoiceEnd { error } if error.as_deref() == Some("boom"))
    }));
}

#[test]
fn process_voice_events_handles_disconnect() {
    let snapshot = event_snapshot();
    let (tx, rx) = mpsc::channel();
    drop(tx);
    let job = VoiceJob {
        receiver: rx,
        handle: None,
        stop_flag: Arc::new(AtomicBool::new(false)),
        capture_active: Arc::new(AtomicBool::new(false)),
    };

    assert!(process_voice_events(&job, false));
    let events = events_since(snapshot);
    assert!(events.iter().any(|event| {
            matches!(event, IpcEvent::VoiceEnd { error } if error.as_deref() == Some("Voice worker disconnected"))
        }));
}

#[test]
fn process_auth_events_emits_success_and_capabilities() {
    let snapshot = event_snapshot();
    let mut state = new_test_state(AppConfig::parse_from(["test-app"]));
    let (tx, rx) = mpsc::channel();
    state.current_auth_job = Some(AuthJob {
        provider: Provider::Codex,
        receiver: rx,
        started_at: Instant::now(),
    });
    tx.send(Ok(())).unwrap();

    assert!(process_auth_events(&mut state));
    let events = events_since(snapshot);
    assert!(events
        .iter()
        .any(|event| matches!(event, IpcEvent::AuthEnd { success: true, .. })));
    assert!(events
        .iter()
        .any(|event| matches!(event, IpcEvent::Capabilities { .. })));
}

#[test]
fn ipc_loop_count_reset_clears_count() {
    ipc_loop_count_set(5);
    assert_eq!(ipc_loop_count(), 5);
    ipc_loop_count_reset();
    assert_eq!(ipc_loop_count(), 0);
}

#[test]
fn set_auth_flow_hook_overrides_auth_flow() {
    struct HookReset;
    impl Drop for HookReset {
        fn drop(&mut self) {
            set_auth_flow_hook(None);
        }
    }

    let calls = Arc::new(AtomicUsize::new(0));
    let calls_clone = Arc::clone(&calls);
    set_auth_flow_hook(Some(Box::new(move |provider, codex_cmd, claude_cmd| {
        calls_clone.fetch_add(1, Ordering::SeqCst);
        assert_eq!(provider, Provider::Codex);
        assert_eq!(codex_cmd, "codex-bin");
        assert_eq!(claude_cmd, "claude-bin");
        Ok(())
    })));
    let _reset = HookReset;

    let result = run_auth_flow(Provider::Codex, "codex-bin", "claude-bin");
    assert!(result.is_ok());
    assert_eq!(calls.load(Ordering::SeqCst), 1);
}

#[test]
fn process_auth_events_resets_session_for_successful_codex() {
    reset_session_count_reset();
    let mut state = new_test_state(AppConfig::parse_from(["test-app"]));
    let (tx, rx) = mpsc::channel();
    state.current_auth_job = Some(AuthJob {
        provider: Provider::Codex,
        receiver: rx,
        started_at: Instant::now(),
    });
    tx.send(Ok(())).unwrap();

    assert!(process_auth_events(&mut state));
    assert_eq!(reset_session_count(), 1);
}

#[test]
fn process_auth_events_does_not_reset_on_failed_codex() {
    reset_session_count_reset();
    let mut state = new_test_state(AppConfig::parse_from(["test-app"]));
    let (tx, rx) = mpsc::channel();
    state.current_auth_job = Some(AuthJob {
        provider: Provider::Codex,
        receiver: rx,
        started_at: Instant::now(),
    });
    tx.send(Err("nope".to_string())).unwrap();

    assert!(process_auth_events(&mut state));
    assert_eq!(reset_session_count(), 0);
}

#[test]
fn process_auth_events_does_not_reset_on_successful_claude() {
    reset_session_count_reset();
    let mut state = new_test_state(AppConfig::parse_from(["test-app"]));
    let (tx, rx) = mpsc::channel();
    state.current_auth_job = Some(AuthJob {
        provider: Provider::Claude,
        receiver: rx,
        started_at: Instant::now(),
    });
    tx.send(Ok(())).unwrap();

    assert!(process_auth_events(&mut state));
    assert_eq!(reset_session_count(), 0);
}

#[test]
fn process_auth_events_emits_error() {
    let snapshot = event_snapshot();
    let mut state = new_test_state(AppConfig::parse_from(["test-app"]));
    let (tx, rx) = mpsc::channel();
    state.current_auth_job = Some(AuthJob {
        provider: Provider::Claude,
        receiver: rx,
        started_at: Instant::now(),
    });
    tx.send(Err("nope".to_string())).unwrap();

    assert!(process_auth_events(&mut state));
    let events = events_since(snapshot);
    assert!(events.iter().any(|event| {
            matches!(event, IpcEvent::AuthEnd { success: false, error, .. } if error.as_deref() == Some("nope"))
        }));
}

#[test]
fn process_auth_events_handles_disconnect() {
    let snapshot = event_snapshot();
    let mut state = new_test_state(AppConfig::parse_from(["test-app"]));
    let (tx, rx) = mpsc::channel();
    drop(tx);
    state.current_auth_job = Some(AuthJob {
        provider: Provider::Codex,
        receiver: rx,
        started_at: Instant::now(),
    });

    assert!(process_auth_events(&mut state));
    let events = events_since(snapshot);
    assert!(events.iter().any(|event| {
            matches!(event, IpcEvent::AuthEnd { success: false, error, .. } if error.as_deref() == Some("Auth worker disconnected"))
        }));
}

#[test]
fn process_auth_events_times_out_stalled_job() {
    let snapshot = event_snapshot();
    let mut state = new_test_state(AppConfig::parse_from(["test-app"]));
    let (_tx, rx) = mpsc::channel();
    state.current_auth_job = Some(AuthJob {
        provider: Provider::Claude,
        receiver: rx,
        started_at: Instant::now(),
    });

    thread::sleep(Duration::from_millis(60));
    assert!(process_auth_events(&mut state));
    let events = events_since(snapshot);
    assert!(events.iter().any(|event| {
        matches!(
            event,
            IpcEvent::AuthEnd { success: false, error, .. }
                if error.as_deref().is_some_and(|msg| msg.contains("timed out"))
        )
    }));
    assert!(events
        .iter()
        .any(|event| matches!(event, IpcEvent::Capabilities { .. })));
}

#[test]
fn handle_cancel_clears_voice_job() {
    let snapshot = event_snapshot();
    let mut state = new_test_state(AppConfig::parse_from(["test-app"]));
    let (_tx, rx) = mpsc::channel();
    state.current_voice_job = Some(VoiceJob {
        receiver: rx,
        handle: None,
        stop_flag: Arc::new(AtomicBool::new(false)),
        capture_active: Arc::new(AtomicBool::new(false)),
    });

    handle_cancel(&mut state);

    assert!(state.current_voice_job.is_none());
    let events = events_since(snapshot);
    assert!(events.iter().any(|event| {
        matches!(event, IpcEvent::VoiceEnd { error } if error.as_deref() == Some("Cancelled"))
    }));
}

#[cfg(unix)]
#[test]
fn handle_cancel_clears_provider_job_with_job_end_event() {
    let snapshot = event_snapshot();
    let mut state = new_test_state(AppConfig::parse_from(["test-app"]));
    state.current_job = Some(ActiveJob::Claude(make_sleeping_claude_job()));

    handle_cancel(&mut state);

    assert!(state.current_job.is_none());
    let events = events_since(snapshot);
    assert!(events.iter().any(|event| {
        matches!(
            event,
            IpcEvent::JobEnd {
                provider,
                success,
                error
            } if provider == "claude" && !*success && error.as_deref() == Some("Cancelled")
        )
    }));
}

#[test]
fn handle_start_voice_errors_when_auth_in_progress() {
    let snapshot = event_snapshot();
    let mut state = new_test_state(AppConfig::parse_from(["test-app"]));
    let (_tx, rx) = mpsc::channel();
    state.current_auth_job = Some(AuthJob {
        provider: Provider::Codex,
        receiver: rx,
        started_at: Instant::now(),
    });

    handle_start_voice(&mut state);
    let events = events_since(snapshot);
    assert!(events.iter().any(|event| {
            matches!(event, IpcEvent::Error { message, .. } if message.contains("Authentication in progress"))
        }));
}

#[test]
fn handle_start_voice_errors_when_already_running() {
    let snapshot = event_snapshot();
    let mut state = new_test_state(AppConfig::parse_from(["test-app"]));
    let (_tx, rx) = mpsc::channel();
    state.current_voice_job = Some(VoiceJob {
        receiver: rx,
        handle: None,
        stop_flag: Arc::new(AtomicBool::new(false)),
        capture_active: Arc::new(AtomicBool::new(false)),
    });

    handle_start_voice(&mut state);
    let events = events_since(snapshot);
    assert!(events.iter().any(|event| {
            matches!(event, IpcEvent::Error { message, .. } if message.contains("Voice capture already in progress"))
        }));
}

#[test]
fn handle_start_voice_errors_when_no_mic_and_no_python() {
    let snapshot = event_snapshot();
    let config = AppConfig::parse_from(["test-app", "--no-python-fallback"]);
    let mut state = new_test_state(config);
    state.recorder = None;

    handle_start_voice(&mut state);
    let events = events_since(snapshot);
    assert!(events.iter().any(|event| {
            matches!(event, IpcEvent::Error { message, .. } if message.contains("No microphone available"))
        }));
}

#[test]
fn handle_start_voice_starts_python_fallback_job() {
    let snapshot = event_snapshot();
    let mut state = new_test_state(AppConfig::parse_from(["test-app"]));
    let _hook = set_python_hook(Box::new(|_cfg, _stop| {
        Ok(PipelineJsonResult {
            transcript: "hello voice".to_string(),
            prompt: String::new(),
            codex_output: None,
            metrics: PipelineMetrics::default(),
        })
    }));

    handle_start_voice(&mut state);

    let start = Instant::now();
    while start.elapsed() < Duration::from_secs(1) {
        if let Some(job) = &state.current_voice_job {
            if process_voice_events(job, false) {
                state.current_voice_job = None;
                break;
            }
        }
        thread::sleep(Duration::from_millis(10));
    }

    let events = events_since(snapshot);
    assert!(events
        .iter()
        .any(|event| matches!(event, IpcEvent::VoiceStart)));
    assert!(events.iter().any(|event| {
        matches!(event, IpcEvent::Transcript { text, .. } if text == "hello voice")
    }));
    assert!(events
        .iter()
        .any(|event| { matches!(event, IpcEvent::VoiceEnd { error } if error.is_none()) }));
}

#[test]
fn handle_auth_command_rejects_unknown_provider() {
    let snapshot = event_snapshot();
    let mut state = new_test_state(AppConfig::parse_from(["test-app"]));
    handle_auth_command(&mut state, Some("unknown".to_string()));
    let events = events_since(snapshot);
    assert!(events.iter().any(|event| {
        matches!(event, IpcEvent::Error { message, .. } if message.contains("Unknown provider"))
    }));
}

#[test]
fn handle_auth_command_rejects_when_active() {
    let snapshot = event_snapshot();
    let mut state = new_test_state(AppConfig::parse_from(["test-app"]));
    let (_tx, rx) = mpsc::channel();
    state.current_voice_job = Some(VoiceJob {
        receiver: rx,
        handle: None,
        stop_flag: Arc::new(AtomicBool::new(false)),
        capture_active: Arc::new(AtomicBool::new(false)),
    });

    handle_auth_command(&mut state, None);
    let events = events_since(snapshot);
    assert!(events.iter().any(|event| {
        matches!(event, IpcEvent::Error { message, .. } if message.contains("Finish active work"))
    }));
}

#[test]
fn handle_auth_command_starts_job_and_completes() {
    let snapshot = event_snapshot();
    let mut state = new_test_state(AppConfig::parse_from(["test-app"]));
    let _guard = set_auth_hook(Box::new(|_provider, _codex, _claude| Ok(())));

    handle_auth_command(&mut state, None);
    assert!(state.current_auth_job.is_some());

    let start = Instant::now();
    while start.elapsed() < Duration::from_secs(1) {
        if process_auth_events(&mut state) {
            break;
        }
        thread::sleep(Duration::from_millis(10));
    }

    let events = events_since(snapshot);
    assert!(events
        .iter()
        .any(|event| matches!(event, IpcEvent::AuthStart { .. })));
    assert!(events
        .iter()
        .any(|event| matches!(event, IpcEvent::AuthEnd { success: true, .. })));
}

#[cfg(unix)]
#[test]
fn start_claude_job_emits_stdout_and_stderr() {
    use std::fs;

    let snapshot = event_snapshot();
    let script = write_stub_script("#!/bin/sh\necho out-line\necho '' 1>&2\necho err-line 1>&2\n");
    let mut job =
        start_claude_job(script.to_str().unwrap(), "prompt", false, "xterm-256color").unwrap();

    let start = Instant::now();
    let mut finished = false;
    let mut saw_out = false;
    let mut saw_err = false;
    while start.elapsed() < Duration::from_secs(5) {
        if process_claude_events(&mut job, false) {
            finished = true;
        }
        let events = events_since(snapshot);
        saw_out = events
            .iter()
            .any(|event| matches!(event, IpcEvent::Token { text } if text.contains("out-line")));
        saw_err = events
            .iter()
            .any(|event| matches!(event, IpcEvent::Token { text } if text.contains("err-line")));
        if finished && saw_out && saw_err {
            break;
        }
        thread::sleep(Duration::from_millis(10));
    }

    assert!(finished, "piped Claude job did not finish");
    assert!(saw_out, "expected piped stdout token");
    assert!(saw_err, "expected piped stderr token");

    let _ = fs::remove_file(script);
}

#[cfg(unix)]
#[test]
fn start_claude_job_with_pty_emits_output() {
    use std::fs;

    let snapshot = event_snapshot();
    let script = write_stub_script("#!/bin/sh\necho out-line\necho err-line 1>&2\n");
    let mut job =
        start_claude_job_with_pty(script.to_str().unwrap(), "prompt", false, "xterm-256color")
            .unwrap();

    let start = Instant::now();
    let mut finished = false;
    let mut saw_out = false;
    let mut saw_err = false;
    while start.elapsed() < Duration::from_secs(5) {
        if process_claude_events(&mut job, false) {
            finished = true;
        }
        let events = events_since(snapshot);
        saw_out = events
            .iter()
            .any(|event| matches!(event, IpcEvent::Token { text } if text.contains("out-line")));
        saw_err = events
            .iter()
            .any(|event| matches!(event, IpcEvent::Token { text } if text.contains("err-line")));
        if finished && saw_out && saw_err {
            break;
        }
        thread::sleep(Duration::from_millis(10));
    }

    assert!(finished, "PTY job did not finish");
    assert!(saw_out, "expected PTY stdout token");
    assert!(saw_err, "expected PTY stderr token");

    let _ = fs::remove_file(script);
}

#[cfg(unix)]
#[test]
fn process_claude_events_handles_cancel() {
    let snapshot = event_snapshot();
    let child = std::process::Command::new("sleep")
        .arg("1")
        .spawn()
        .expect("spawned child");
    let (_tx, rx) = mpsc::channel();
    let mut job = ClaudeJob {
        output: ClaudeJobOutput::Piped {
            child,
            stdout_rx: rx,
        },
        started_at: Instant::now(),
        pending_exit: None,
    };

    assert!(process_claude_events(&mut job, true));
    let _ = events_since(snapshot);
}

#[test]
fn process_codex_events_emits_tokens_and_status() {
    let snapshot = event_snapshot();
    let job_id = 42;
    let events = vec![
        CodexEvent {
            job_id,
            kind: CodexEventKind::Started {
                mode: RequestMode::Chat,
            },
        },
        CodexEvent {
            job_id,
            kind: CodexEventKind::Status {
                message: "hello".to_string(),
            },
        },
        CodexEvent {
            job_id,
            kind: CodexEventKind::Token {
                text: "token".to_string(),
            },
        },
    ];
    let mut job = build_test_backend_job(events, TestSignal::Ready);

    assert!(!process_codex_events(&mut job, false));
    let events = events_since(snapshot);
    assert!(events
        .iter()
        .any(|event| matches!(event, IpcEvent::Status { message } if message == "Processing...")));
    assert!(events
        .iter()
        .any(|event| matches!(event, IpcEvent::Status { message } if message == "hello")));
    assert!(events
        .iter()
        .any(|event| matches!(event, IpcEvent::Token { text } if text == "token")));
}

#[test]
fn process_codex_events_finishes_job() {
    let snapshot = event_snapshot();
    let now = Instant::now();
    let stats = CodexJobStats {
        backend_type: "cli",
        started_at: now,
        first_token_at: None,
        finished_at: now,
        tokens_received: 0,
        bytes_transferred: 0,
        pty_attempts: 0,
        cli_fallback_used: false,
        disable_pty: false,
    };
    let events = vec![CodexEvent {
        job_id: 1,
        kind: CodexEventKind::Finished {
            lines: vec!["done".to_string()],
            status: "ok".to_string(),
            stats,
        },
    }];
    let mut job = build_test_backend_job(events, TestSignal::Ready);

    assert!(process_codex_events(&mut job, false));
    let events = events_since(snapshot);
    assert!(events
        .iter()
        .any(|event| { matches!(event, IpcEvent::Token { text } if text.contains("done")) }));
    assert!(events.iter().any(|event| {
            matches!(event, IpcEvent::JobEnd { provider, success, .. } if provider == "codex" && *success)
        }));
}

#[test]
fn process_codex_events_disconnected_sends_end() {
    let snapshot = event_snapshot();
    let mut job = build_test_backend_job(Vec::new(), TestSignal::Disconnected);

    assert!(process_codex_events(&mut job, false));
    let events = events_since(snapshot);
    assert!(events.iter().any(|event| {
            matches!(event, IpcEvent::JobEnd { provider, success, .. } if provider == "codex" && *success)
        }));
}

mod protocol_codec_tests;
