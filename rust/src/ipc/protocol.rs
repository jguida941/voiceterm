//! Typed JSON IPC protocol so frontend/backends exchange stable event contracts.
//!
//! Defines the message types exchanged between the Rust backend and external
//! frontends (e.g., UI clients). Messages are newline-delimited JSON.

use serde::{Deserialize, Serialize};
use std::fmt;
use std::{str::FromStr, sync::OnceLock};

use crate::backend::BackendRegistry;

// ============================================================================
// IPC Events (Rust → client)
// ============================================================================

/// Events emitted by the Rust backend.
///
/// Serialized as JSON with a `"event"` tag field for type discrimination.
#[derive(Debug, Clone, Serialize)]
#[serde(tag = "event")]
pub enum IpcEvent {
    /// Sent once on startup with full capability information
    #[serde(rename = "capabilities")]
    Capabilities {
        /// Unique runtime session id for event correlation.
        session_id: String,
        /// VoiceTerm semantic version.
        version: String,
        /// Whether microphone capture is currently available.
        mic_available: bool,
        /// Active input-device label when microphone is available.
        input_device: Option<String>,
        /// Whether Whisper model is loaded and ready.
        whisper_model_loaded: bool,
        /// Resolved Whisper model path when configured.
        whisper_model_path: Option<String>,
        /// Whether Python fallback is enabled.
        python_fallback_allowed: bool,
        /// Providers available in this runtime.
        providers_available: Vec<String>,
        /// Currently selected provider.
        active_provider: String,
        /// Current working directory for command execution.
        working_dir: String,
        /// Effective Codex command executable.
        codex_cmd: String,
        /// Effective Claude command executable.
        claude_cmd: String,
    },

    /// Provider changed successfully
    #[serde(rename = "provider_changed")]
    ProviderChanged {
        /// Provider name now active after switch.
        provider: String,
    },

    /// Error when trying to use a provider-specific command on wrong provider
    #[serde(rename = "provider_error")]
    ProviderError {
        /// Human-readable explanation of provider mismatch.
        message: String,
    },

    /// Authentication flow started (TTY login)
    #[serde(rename = "auth_start")]
    AuthStart {
        /// Provider currently being authenticated.
        provider: String,
    },

    /// Authentication flow ended
    #[serde(rename = "auth_end")]
    AuthEnd {
        /// Provider that completed authentication.
        provider: String,
        /// Whether authentication succeeded.
        success: bool,
        #[serde(skip_serializing_if = "Option::is_none")]
        /// Optional error message when authentication failed.
        error: Option<String>,
    },

    /// Streaming token from provider
    #[serde(rename = "token")]
    Token {
        /// Incremental output chunk from provider.
        text: String,
    },

    /// Voice capture started
    #[serde(rename = "voice_start")]
    VoiceStart,

    /// Voice capture ended
    #[serde(rename = "voice_end")]
    VoiceEnd {
        #[serde(skip_serializing_if = "Option::is_none")]
        /// Optional error when voice capture failed.
        error: Option<String>,
    },

    /// Transcript ready from voice capture
    #[serde(rename = "transcript")]
    Transcript {
        /// Final transcript text.
        text: String,
        /// End-to-end voice capture duration in milliseconds.
        duration_ms: u64,
    },

    /// Provider job started
    #[serde(rename = "job_start")]
    JobStart {
        /// Provider handling the started job.
        provider: String,
    },

    /// Provider job ended
    #[serde(rename = "job_end")]
    JobEnd {
        /// Provider that handled the completed job.
        provider: String,
        /// Whether provider job ended successfully.
        success: bool,
        #[serde(skip_serializing_if = "Option::is_none")]
        /// Optional failure detail when `success` is false.
        error: Option<String>,
    },

    /// Status update
    #[serde(rename = "status")]
    Status {
        /// Human-readable runtime status message.
        message: String,
    },

    /// Error (recoverable or fatal)
    #[serde(rename = "error")]
    Error {
        /// Human-readable error description.
        message: String,
        /// Whether caller may continue without restarting session.
        recoverable: bool,
    },
}

// ============================================================================
// IPC Commands (client → Rust)
// ============================================================================

/// Commands received from an IPC client
#[derive(Debug, Clone, Deserialize)]
#[serde(tag = "cmd")]
pub enum IpcCommand {
    /// Send a prompt to the active provider
    #[serde(rename = "send_prompt")]
    SendPrompt {
        /// Prompt text to send to the active provider.
        prompt: String,
        /// Optional one-off provider override
        #[serde(default)]
        provider: Option<String>,
    },

    /// Start voice capture
    #[serde(rename = "start_voice")]
    StartVoice,

    /// Cancel current operation
    #[serde(rename = "cancel")]
    Cancel,

    /// Set the active provider
    #[serde(rename = "set_provider")]
    SetProvider {
        /// Provider name to activate.
        provider: String,
    },

    /// Authenticate with provider via /dev/tty login
    #[serde(rename = "auth")]
    Auth {
        #[serde(default)]
        /// Optional provider override for this auth request.
        provider: Option<String>,
    },

    /// Request capabilities (re-emit capabilities event)
    #[serde(rename = "get_capabilities")]
    GetCapabilities,
}

// ============================================================================
// Provider Abstraction
// ============================================================================

/// Supported providers
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Provider {
    /// OpenAI Codex CLI provider.
    Codex,
    /// Anthropic Claude CLI provider.
    Claude,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub(crate) enum ProviderLifecycle {
    CodexCli,
    ClaudeCli,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub(crate) enum ProviderNameResolution {
    Supported(Provider),
    UnsupportedNonIpc(OverlayOnlyBackendClass),
    Unknown,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub(crate) struct ProviderNameError(String);

impl ProviderNameError {
    fn new(message: String) -> Self {
        Self(message)
    }
}

impl fmt::Display for ProviderNameError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str(&self.0)
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub(crate) enum OverlayOnlyBackendClass {
    GeminiExperimental,
    Aider,
    OpenCode,
    Custom,
}

impl OverlayOnlyBackendClass {
    fn parse(label: &str) -> Option<Self> {
        if label.eq_ignore_ascii_case("gemini") {
            Some(Self::GeminiExperimental)
        } else if label.eq_ignore_ascii_case("aider") {
            Some(Self::Aider)
        } else if label.eq_ignore_ascii_case("opencode") {
            Some(Self::OpenCode)
        } else if label.eq_ignore_ascii_case("custom") {
            Some(Self::Custom)
        } else {
            None
        }
    }

    fn classification(self) -> &'static str {
        match self {
            Self::GeminiExperimental => "overlay-only experimental backend",
            Self::Aider | Self::OpenCode | Self::Custom => "overlay-only non-IPC backend",
        }
    }
}

impl Provider {
    pub(crate) fn ipc_supported() -> &'static [Provider] {
        static IPC_SUPPORTED: OnceLock<Vec<Provider>> = OnceLock::new();
        IPC_SUPPORTED
            .get_or_init(|| {
                let mut discovered = Vec::new();
                for backend_name in BackendRegistry::new().available_backends() {
                    if let Some(provider) = Provider::parse_name(backend_name) {
                        if !discovered.contains(&provider) {
                            discovered.push(provider);
                        }
                    }
                }

                // Keep the legacy fallback contract if discovery yields no IPC providers.
                if discovered.is_empty() {
                    discovered.extend([Provider::Codex, Provider::Claude]);
                }

                discovered
            })
            .as_slice()
    }

    pub(crate) fn ipc_capability_labels() -> Vec<String> {
        Self::ipc_supported()
            .iter()
            .map(|provider| provider.as_str().to_string())
            .collect()
    }

    pub(crate) fn default_ipc() -> Self {
        Self::ipc_supported()
            .first()
            .copied()
            .unwrap_or(Provider::Codex)
    }

    pub(crate) fn lifecycle(self) -> ProviderLifecycle {
        match self {
            Provider::Codex => ProviderLifecycle::CodexCli,
            Provider::Claude => ProviderLifecycle::ClaudeCli,
        }
    }

    pub(crate) fn supports_provider_command_forwarding(self) -> bool {
        matches!(self.lifecycle(), ProviderLifecycle::CodexCli)
    }

    pub(crate) fn auth_command<'a>(self, codex_cmd: &'a str, claude_cmd: &'a str) -> &'a str {
        match self.lifecycle() {
            ProviderLifecycle::CodexCli => codex_cmd,
            ProviderLifecycle::ClaudeCli => claude_cmd,
        }
    }

    pub(crate) fn resets_session_on_auth_success(self) -> bool {
        matches!(self.lifecycle(), ProviderLifecycle::CodexCli)
    }

    pub(crate) fn provider_command_mismatch_message(self, command: &str, args: &str) -> String {
        let command_hint = if args.is_empty() {
            format!("/{command}")
        } else {
            format!("/{command} {args}")
        };
        format!(
            "/{command} is a Codex command. Switch with /provider codex or use /codex {command_hint}"
        )
    }

    pub(crate) fn resolve_name(s: &str) -> ProviderNameResolution {
        let normalized = s.trim();
        if normalized.eq_ignore_ascii_case("codex") {
            ProviderNameResolution::Supported(Provider::Codex)
        } else if normalized.eq_ignore_ascii_case("claude") {
            ProviderNameResolution::Supported(Provider::Claude)
        } else if let Some(classification) = OverlayOnlyBackendClass::parse(normalized) {
            ProviderNameResolution::UnsupportedNonIpc(classification)
        } else {
            ProviderNameResolution::Unknown
        }
    }

    pub(crate) fn as_str(&self) -> &'static str {
        match self {
            Provider::Codex => "codex",
            Provider::Claude => "claude",
        }
    }

    pub(crate) fn parse_name(s: &str) -> Option<Self> {
        match Self::resolve_name(s) {
            ProviderNameResolution::Supported(provider) => Some(provider),
            ProviderNameResolution::UnsupportedNonIpc(_) | ProviderNameResolution::Unknown => None,
        }
    }

    pub(crate) fn parse_name_or_error_message(s: &str) -> Result<Self, ProviderNameError> {
        if let Some(provider) = Self::parse_name(s) {
            return Ok(provider);
        }
        let supported_provider_hint = Self::ipc_capability_labels()
            .iter()
            .map(|name| format!("'{name}'"))
            .collect::<Vec<_>>()
            .join(" or ");
        let requested = s.trim();
        let label = if requested.is_empty() {
            "<empty>"
        } else {
            requested
        };
        match Self::resolve_name(s) {
            ProviderNameResolution::Supported(provider) => Ok(provider),
            ProviderNameResolution::UnsupportedNonIpc(classification) => Err(ProviderNameError::new(format!(
                "Provider '{label}' is classified as an {} and is unavailable in IPC mode. Use {supported_provider_hint}.",
                classification.classification()
            ))),
            ProviderNameResolution::Unknown => {
                Err(ProviderNameError::new(format!(
                    "Unknown provider: {label}. Use {supported_provider_hint}."
                )))
            }
        }
    }
}

impl FromStr for Provider {
    type Err = &'static str;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        match Provider::resolve_name(s) {
            ProviderNameResolution::Supported(provider) => Ok(provider),
            ProviderNameResolution::UnsupportedNonIpc(_) => {
                Err("provider is not available in IPC mode")
            }
            ProviderNameResolution::Unknown => Err("unknown provider"),
        }
    }
}
