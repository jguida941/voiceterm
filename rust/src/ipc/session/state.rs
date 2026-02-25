use super::super::protocol::{IpcEvent, Provider};
use super::{send_event, IpcState, USE_PTY};
use crate::codex::CodexCliBackend;
use crate::config::AppConfig;
use crate::{audio, log_debug, stt};
use std::env;
use std::sync::{Arc, Mutex};

impl IpcState {
    pub(in crate::ipc) fn new(mut config: AppConfig) -> Self {
        // Keep test/mutant runs deterministic by disabling PTY when toggled off.
        if !USE_PTY {
            config.persistent_codex = false;
            log_debug("PTY disabled via USE_PTY toggle");
        }

        // Session id is emitted in capabilities so clients can correlate events.
        let session_id = format!(
            "{:x}",
            std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap_or_default()
                .as_millis()
        );

        // Use already validated command values from config parsing.
        let claude_cmd = config.claude_cmd.clone();

        // Backend is shared so concurrent jobs can be cancelled from multiple paths.
        let codex_cli_backend = Arc::new(CodexCliBackend::new(config.clone()));

        // Allow env override so wrappers can pin provider without extra flags.
        let default_provider = env::var("VOICETERM_PROVIDER")
            .ok()
            .and_then(|s| Provider::parse_name(&s))
            .unwrap_or(Provider::Codex);

        // Recorder/transcriber are optional so IPC still works without voice dependencies.
        let recorder = match audio::Recorder::new(config.input_device.as_deref()) {
            Ok(r) => {
                log_debug("Audio recorder initialized");
                Some(Arc::new(Mutex::new(r)))
            }
            Err(e) => {
                log_debug(&format!("Audio recorder not available: {e}"));
                None
            }
        };

        // Load STT lazily from config path; failures remain recoverable.
        let transcriber = if let Some(model_path) = &config.whisper_model_path {
            match stt::Transcriber::new(model_path) {
                Ok(t) => {
                    log_debug("Whisper transcriber initialized");
                    Some(Arc::new(Mutex::new(t)))
                }
                Err(e) => {
                    log_debug(&format!("Whisper not available: {e}"));
                    None
                }
            }
        } else {
            log_debug("No whisper model path configured");
            None
        };

        Self {
            config,
            active_provider: default_provider,
            codex_cli_backend,
            claude_cmd,
            recorder,
            transcriber,
            current_job: None,
            current_voice_job: None,
            current_auth_job: None,
            session_id,
            cancelled: false,
            exit_requested: false,
        }
    }

    pub(in crate::ipc) fn emit_capabilities(&self) {
        let providers = vec!["codex".to_string(), "claude".to_string()];

        // Device name is included in capabilities for client-side diagnostics.
        let input_device = self.recorder.as_ref().map(|r| {
            r.lock()
                .map(|recorder| recorder.device_name())
                .unwrap_or_else(|_| "Unknown Device".to_string())
        });

        send_event(&IpcEvent::Capabilities {
            session_id: self.session_id.clone(),
            version: env!("CARGO_PKG_VERSION").to_string(),
            mic_available: self.recorder.is_some(),
            input_device,
            whisper_model_loaded: self.transcriber.is_some(),
            whisper_model_path: self.config.whisper_model_path.clone(),
            python_fallback_allowed: !self.config.no_python_fallback,
            providers_available: providers,
            active_provider: self.active_provider.as_str().to_string(),
            working_dir: env::current_dir()
                .map(|p| p.display().to_string())
                .unwrap_or_else(|_| ".".to_string()),
            codex_cmd: self.config.codex_cmd.clone(),
            claude_cmd: self.claude_cmd.clone(),
        });
    }
}
