use super::*;

// -------------------------------------------------------------------------
// IPC Command Deserialization Tests
// -------------------------------------------------------------------------

#[test]
fn test_deserialize_send_prompt() {
    let json = r#"{"cmd": "send_prompt", "prompt": "hello world"}"#;
    let cmd: IpcCommand = serde_json::from_str(json).unwrap();
    match cmd {
        IpcCommand::SendPrompt { prompt, provider } => {
            assert_eq!(prompt, "hello world");
            assert!(provider.is_none());
        }
        _ => panic!("Expected SendPrompt"),
    }
}

#[test]
fn test_deserialize_send_prompt_with_provider() {
    let json = r#"{"cmd": "send_prompt", "prompt": "hello", "provider": "claude"}"#;
    let cmd: IpcCommand = serde_json::from_str(json).unwrap();
    match cmd {
        IpcCommand::SendPrompt { prompt, provider } => {
            assert_eq!(prompt, "hello");
            assert_eq!(provider, Some("claude".to_string()));
        }
        _ => panic!("Expected SendPrompt with provider"),
    }
}

#[test]
fn test_deserialize_start_voice() {
    let json = r#"{"cmd": "start_voice"}"#;
    let cmd: IpcCommand = serde_json::from_str(json).unwrap();
    assert!(matches!(cmd, IpcCommand::StartVoice));
}

#[test]
fn test_deserialize_cancel() {
    let json = r#"{"cmd": "cancel"}"#;
    let cmd: IpcCommand = serde_json::from_str(json).unwrap();
    assert!(matches!(cmd, IpcCommand::Cancel));
}

#[test]
fn test_deserialize_set_provider() {
    let json = r#"{"cmd": "set_provider", "provider": "claude"}"#;
    let cmd: IpcCommand = serde_json::from_str(json).unwrap();
    match cmd {
        IpcCommand::SetProvider { provider } => assert_eq!(provider, "claude"),
        _ => panic!("Expected SetProvider"),
    }
}

#[test]
fn test_deserialize_auth() {
    let json = r#"{"cmd": "auth", "provider": "codex"}"#;
    let cmd: IpcCommand = serde_json::from_str(json).unwrap();
    match cmd {
        IpcCommand::Auth { provider } => {
            assert_eq!(provider, Some("codex".to_string()));
        }
        _ => panic!("Expected Auth"),
    }
}

#[test]
fn test_deserialize_get_capabilities() {
    let json = r#"{"cmd": "get_capabilities"}"#;
    let cmd: IpcCommand = serde_json::from_str(json).unwrap();
    assert!(matches!(cmd, IpcCommand::GetCapabilities));
}

// -------------------------------------------------------------------------
// IPC Event Serialization Tests
// -------------------------------------------------------------------------

#[test]
fn test_serialize_capabilities_event() {
    let event = IpcEvent::Capabilities {
        session_id: "test123".to_string(),
        version: env!("CARGO_PKG_VERSION").to_string(),
        mic_available: true,
        input_device: Some("Default".to_string()),
        whisper_model_loaded: true,
        whisper_model_path: Some("/path/to/model".to_string()),
        python_fallback_allowed: true,
        providers_available: vec!["codex".to_string(), "claude".to_string()],
        active_provider: "codex".to_string(),
        working_dir: "/home/user".to_string(),
        codex_cmd: "codex".to_string(),
        claude_cmd: "claude".to_string(),
    };

    let json = serde_json::to_string(&event).unwrap();
    assert!(json.contains(r#""event":"capabilities""#));
    assert!(json.contains(r#""session_id":"test123""#));
    assert!(json.contains(r#""mic_available":true"#));
}

#[test]
fn test_serialize_token_event() {
    let event = IpcEvent::Token {
        text: "Hello world".to_string(),
    };

    let json = serde_json::to_string(&event).unwrap();
    assert!(json.contains(r#""event":"token""#));
    assert!(json.contains(r#""text":"Hello world""#));
}

#[test]
fn test_serialize_job_events() {
    let start = IpcEvent::JobStart {
        provider: "codex".to_string(),
    };
    let json = serde_json::to_string(&start).unwrap();
    assert!(json.contains(r#""event":"job_start""#));
    assert!(json.contains(r#""provider":"codex""#));

    let end = IpcEvent::JobEnd {
        provider: "claude".to_string(),
        success: true,
        error: None,
    };
    let json = serde_json::to_string(&end).unwrap();
    assert!(json.contains(r#""event":"job_end""#));
    assert!(json.contains(r#""success":true"#));
    assert!(!json.contains("error")); // skip_serializing_if = None

    let end_error = IpcEvent::JobEnd {
        provider: "claude".to_string(),
        success: false,
        error: Some("Connection failed".to_string()),
    };
    let json = serde_json::to_string(&end_error).unwrap();
    assert!(json.contains(r#""error":"Connection failed""#));
}

#[test]
fn test_serialize_provider_changed() {
    let event = IpcEvent::ProviderChanged {
        provider: "claude".to_string(),
    };
    let json = serde_json::to_string(&event).unwrap();
    assert!(json.contains(r#""event":"provider_changed""#));
    assert!(json.contains(r#""provider":"claude""#));
}

#[test]
fn test_serialize_auth_events() {
    let start = IpcEvent::AuthStart {
        provider: "codex".to_string(),
    };
    let json = serde_json::to_string(&start).unwrap();
    assert!(json.contains(r#""event":"auth_start""#));
    assert!(json.contains(r#""provider":"codex""#));

    let end = IpcEvent::AuthEnd {
        provider: "codex".to_string(),
        success: true,
        error: None,
    };
    let json = serde_json::to_string(&end).unwrap();
    assert!(json.contains(r#""event":"auth_end""#));
    assert!(json.contains(r#""success":true"#));
    assert!(!json.contains("error"));

    let end_error = IpcEvent::AuthEnd {
        provider: "claude".to_string(),
        success: false,
        error: Some("login failed".to_string()),
    };
    let json = serde_json::to_string(&end_error).unwrap();
    assert!(json.contains(r#""provider":"claude""#));
    assert!(json.contains(r#""error":"login failed""#));
}

#[test]
fn test_serialize_voice_events() {
    let start = IpcEvent::VoiceStart;
    let json = serde_json::to_string(&start).unwrap();
    assert!(json.contains(r#""event":"voice_start""#));

    let end_ok = IpcEvent::VoiceEnd { error: None };
    let json = serde_json::to_string(&end_ok).unwrap();
    assert!(json.contains(r#""event":"voice_end""#));
    assert!(!json.contains("error"));

    let end_err = IpcEvent::VoiceEnd {
        error: Some("Mic unavailable".to_string()),
    };
    let json = serde_json::to_string(&end_err).unwrap();
    assert!(json.contains(r#""error":"Mic unavailable""#));

    let transcript = IpcEvent::Transcript {
        text: "Hello".to_string(),
        duration_ms: 500,
    };
    let json = serde_json::to_string(&transcript).unwrap();
    assert!(json.contains(r#""event":"transcript""#));
    assert!(json.contains(r#""text":"Hello""#));
    assert!(json.contains(r#""duration_ms":500"#));
}

#[test]
fn test_serialize_error_event() {
    let event = IpcEvent::Error {
        message: "Something went wrong".to_string(),
        recoverable: true,
    };
    let json = serde_json::to_string(&event).unwrap();
    assert!(json.contains(r#""event":"error""#));
    assert!(json.contains(r#""message":"Something went wrong""#));
    assert!(json.contains(r#""recoverable":true"#));
}
