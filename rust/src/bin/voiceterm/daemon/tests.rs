//! Unit tests for the daemon hub protocol and registry.

use super::client_codec::{decode_command, encode_event};
use super::session_registry::SessionRegistry;
use super::types::*;

#[test]
fn command_roundtrip_spawn_agent() {
    let json = r#"{"cmd":"spawn_agent","provider":"claude","label":"reviewer-1"}"#;
    let cmd = decode_command(json).unwrap();
    match cmd {
        DaemonCommand::SpawnAgent {
            provider,
            label,
            working_dir,
            initial_prompt,
        } => {
            assert_eq!(provider, "claude");
            assert_eq!(label.as_deref(), Some("reviewer-1"));
            assert!(working_dir.is_none());
            assert!(initial_prompt.is_none());
        }
        _ => panic!("expected SpawnAgent"),
    }
}

#[test]
fn command_roundtrip_send_to_agent() {
    let json = r#"{"cmd":"send_to_agent","session_id":"a1","text":"hello"}"#;
    let cmd = decode_command(json).unwrap();
    match cmd {
        DaemonCommand::SendToAgent { session_id, text } => {
            assert_eq!(session_id, "a1");
            assert_eq!(text, "hello");
        }
        _ => panic!("expected SendToAgent"),
    }
}

#[test]
fn command_roundtrip_kill() {
    let json = r#"{"cmd":"kill_agent","session_id":"a1"}"#;
    let cmd = decode_command(json).unwrap();
    assert!(matches!(cmd, DaemonCommand::KillAgent { .. }));
}

#[test]
fn command_roundtrip_list() {
    let json = r#"{"cmd":"list_agents"}"#;
    let cmd = decode_command(json).unwrap();
    assert!(matches!(cmd, DaemonCommand::ListAgents));
}

#[test]
fn command_roundtrip_status() {
    let json = r#"{"cmd":"get_status"}"#;
    let cmd = decode_command(json).unwrap();
    assert!(matches!(cmd, DaemonCommand::GetStatus));
}

#[test]
fn command_roundtrip_shutdown() {
    let json = r#"{"cmd":"shutdown"}"#;
    let cmd = decode_command(json).unwrap();
    assert!(matches!(cmd, DaemonCommand::Shutdown));
}

#[test]
fn event_agent_spawned_serializes() {
    let event = DaemonEvent::AgentSpawned {
        session_id: "agent_1".to_string(),
        provider: "claude".to_string(),
        label: "reviewer".to_string(),
        working_dir: "/tmp".to_string(),
        pid: 12345,
    };
    let json = encode_event(&event);
    assert!(json.contains(r#""event":"agent_spawned""#));
    assert!(json.contains("12345"));
}

#[test]
fn event_agent_output_serializes() {
    let event = DaemonEvent::AgentOutput {
        session_id: "a1".to_string(),
        text: "thinking...".to_string(),
    };
    let json = encode_event(&event);
    assert!(json.contains(r#""event":"agent_output""#));
    assert!(json.contains("thinking..."));
}

#[test]
fn event_daemon_status_serializes() {
    let event = DaemonEvent::DaemonStatus {
        version: "1.1.1".to_string(),
        active_agents: 3,
        connected_clients: 2,
        uptime_secs: 42.5,
    };
    let json = encode_event(&event);
    let parsed: serde_json::Value = serde_json::from_str(&json).unwrap();
    assert_eq!(parsed["event"], "daemon_status");
    assert_eq!(parsed["active_agents"], 3);
}

#[test]
fn event_error_omits_null_session_id() {
    let event = DaemonEvent::Error {
        message: "oops".to_string(),
        session_id: None,
    };
    let json = encode_event(&event);
    assert!(!json.contains("session_id"));
}

#[test]
fn registry_insert_and_list() {
    let registry = SessionRegistry::new();
    assert_eq!(registry.len(), 0);
    assert!(registry.list().is_empty());
}

#[test]
fn session_id_contains_agent_prefix() {
    let id = SessionId::new();
    assert!(id.0.starts_with("agent_"));
}

#[test]
fn client_id_contains_transport_prefix() {
    let unix_id = ClientId::new("unix");
    assert!(unix_id.0.starts_with("unix_"));
    let ws_id = ClientId::new("ws");
    assert!(ws_id.0.starts_with("ws_"));
}

#[test]
fn default_socket_path_ends_with_control_sock() {
    let path = DaemonConfig::default_socket_path();
    assert!(path.ends_with("control.sock"));
    assert!(path.to_string_lossy().contains(".voiceterm"));
}
