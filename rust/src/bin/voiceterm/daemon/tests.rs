//! Unit tests for the daemon hub protocol and registry.

use std::sync::atomic::AtomicBool;
use std::sync::atomic::Ordering;
use std::sync::Arc;

use tokio::sync::mpsc;

use super::agent_driver::{AgentHandle, StartupGate};
use super::client_codec::{decode_command, encode_event};
use super::event_bus::EventBus;
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
        socket_path: "/tmp/voiceterm.sock".to_string(),
        ws_port: Some(9876),
        ws_url: Some("ws://127.0.0.1:9876".to_string()),
        lifecycle: DaemonLifecycleState::Running,
        primary_attach: DaemonAttachTransport::WebSocket,
        pid: 4242,
        started_at_unix_ms: 123_456,
        working_dir: "/tmp/repo".to_string(),
        memory_mode: "assist".to_string(),
    };
    let json = encode_event(&event);
    let parsed: serde_json::Value = serde_json::from_str(&json).unwrap();
    assert_eq!(parsed["event"], "daemon_status");
    assert_eq!(parsed["active_agents"], 3);
    assert_eq!(parsed["lifecycle"], "running");
    assert_eq!(parsed["primary_attach"], "web_socket");
    assert_eq!(parsed["socket_path"], "/tmp/voiceterm.sock");
    assert_eq!(parsed["ws_url"], "ws://127.0.0.1:9876");
    assert_eq!(parsed["memory_mode"], "assist");
}

#[test]
fn event_daemon_ready_serializes_attach_metadata() {
    let event = DaemonEvent::DaemonReady {
        version: "1.1.1".to_string(),
        socket_path: "/tmp/voiceterm.sock".to_string(),
        ws_port: None,
        ws_url: None,
        lifecycle: DaemonLifecycleState::Running,
        primary_attach: DaemonAttachTransport::UnixSocket,
        pid: 9001,
        started_at_unix_ms: 777,
        working_dir: "/tmp/repo".to_string(),
        memory_mode: "capture_only".to_string(),
    };
    let json = encode_event(&event);
    let parsed: serde_json::Value = serde_json::from_str(&json).unwrap();
    assert_eq!(parsed["event"], "daemon_ready");
    assert_eq!(parsed["primary_attach"], "unix_socket");
    assert_eq!(parsed["pid"], 9001);
    assert_eq!(parsed["working_dir"], "/tmp/repo");
    assert_eq!(parsed["memory_mode"], "capture_only");
    assert!(parsed.get("ws_url").is_none());
}

#[test]
fn late_subscriber_receives_latest_lifecycle_snapshot() {
    let event_bus = EventBus::new();
    event_bus.broadcast(DaemonEvent::DaemonReady {
        version: "1.1.1".to_string(),
        socket_path: "/tmp/voiceterm.sock".to_string(),
        ws_port: Some(9876),
        ws_url: Some("ws://127.0.0.1:9876".to_string()),
        lifecycle: DaemonLifecycleState::Running,
        primary_attach: DaemonAttachTransport::WebSocket,
        pid: 4242,
        started_at_unix_ms: 123_456,
        working_dir: "/tmp/repo".to_string(),
        memory_mode: "assist".to_string(),
    });

    let (_rx, snapshot, _agent_list) = event_bus.subscribe_with_snapshot();
    let snapshot = snapshot.expect("late subscriber should receive lifecycle snapshot");
    match snapshot {
        DaemonEvent::DaemonReady {
            lifecycle,
            primary_attach,
            ws_url,
            ..
        } => {
            assert_eq!(lifecycle, DaemonLifecycleState::Running);
            assert_eq!(primary_attach, DaemonAttachTransport::WebSocket);
            assert_eq!(ws_url.as_deref(), Some("ws://127.0.0.1:9876"));
        }
        other => panic!("expected DaemonReady snapshot, got {other:?}"),
    }
}

#[test]
fn lifecycle_snapshot_tracks_latest_status_only() {
    let event_bus = EventBus::new();
    event_bus.broadcast(DaemonEvent::DaemonReady {
        version: "1.1.1".to_string(),
        socket_path: "/tmp/voiceterm.sock".to_string(),
        ws_port: None,
        ws_url: None,
        lifecycle: DaemonLifecycleState::Running,
        primary_attach: DaemonAttachTransport::UnixSocket,
        pid: 1111,
        started_at_unix_ms: 1,
        working_dir: "/tmp/repo".to_string(),
        memory_mode: "assist".to_string(),
    });
    event_bus.broadcast(DaemonEvent::AgentSpawned {
        session_id: "agent_1".to_string(),
        provider: "claude".to_string(),
        label: "reviewer".to_string(),
        working_dir: "/tmp/repo".to_string(),
        pid: 2222,
    });
    event_bus.broadcast(DaemonEvent::DaemonStatus {
        version: "1.1.1".to_string(),
        active_agents: 1,
        connected_clients: 2,
        uptime_secs: 42.5,
        socket_path: "/tmp/voiceterm.sock".to_string(),
        ws_port: None,
        ws_url: None,
        lifecycle: DaemonLifecycleState::Running,
        primary_attach: DaemonAttachTransport::UnixSocket,
        pid: 1111,
        started_at_unix_ms: 1,
        working_dir: "/tmp/repo".to_string(),
        memory_mode: "assist".to_string(),
    });

    let (_rx, snapshot, _agent_list) = event_bus.subscribe_with_snapshot();
    let snapshot = snapshot.expect("late subscriber should receive latest lifecycle snapshot");
    match snapshot {
        DaemonEvent::DaemonStatus {
            active_agents,
            connected_clients,
            ..
        } => {
            assert_eq!(active_agents, 1);
            assert_eq!(connected_clients, 2);
        }
        other => panic!("expected DaemonStatus snapshot, got {other:?}"),
    }
}

#[test]
fn late_subscriber_receives_agent_list_snapshot() {
    let event_bus = EventBus::new();

    // Broadcast a lifecycle event and an agent_list event
    event_bus.broadcast(DaemonEvent::DaemonReady {
        version: "1.1.1".to_string(),
        socket_path: "/tmp/test.sock".to_string(),
        ws_port: Some(9876),
        ws_url: Some("ws://localhost:9876".to_string()),
        lifecycle: super::types::DaemonLifecycleState::Running,
        primary_attach: super::types::DaemonAttachTransport::WebSocket,
        pid: 4242,
        started_at_unix_ms: 100_000,
        working_dir: "/tmp/repo".to_string(),
        memory_mode: "assist".to_string(),
    });
    event_bus.broadcast(DaemonEvent::AgentList {
        agents: vec![super::types::AgentInfo {
            session_id: "agent_1".to_string(),
            provider: "claude".to_string(),
            label: "test-agent".to_string(),
            working_dir: "/tmp/repo".to_string(),
            pid: 12345,
            is_alive: true,
        }],
    });

    // Late subscriber should get both snapshots
    let (_rx, lifecycle, agent_list) = event_bus.subscribe_with_snapshot();
    assert!(lifecycle.is_some(), "should receive lifecycle snapshot");
    assert!(agent_list.is_some(), "should receive agent_list snapshot");
    match agent_list.unwrap() {
        DaemonEvent::AgentList { agents } => {
            assert_eq!(agents.len(), 1);
            assert_eq!(agents[0].label, "test-agent");
        }
        other => panic!("expected AgentList snapshot, got {other:?}"),
    }
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
fn registry_prune_dead_removes_exited_sessions() {
    let mut registry = SessionRegistry::new();
    registry.insert(test_handle("agent_live", true));
    registry.insert(test_handle("agent_dead", false));

    assert_eq!(registry.prune_dead(), 1);
    assert_eq!(registry.len(), 1);
    assert_eq!(registry.list()[0].session_id, "agent_live");
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

fn test_handle(session_id: &str, alive: bool) -> AgentHandle {
    let (cmd_tx, _cmd_rx) = mpsc::channel(1);
    let alive_flag = Arc::new(AtomicBool::new(alive));
    let startup_gate = StartupGate::opened();
    if !alive {
        alive_flag.store(false, Ordering::Relaxed);
    }
    AgentHandle {
        session_id: SessionId(session_id.to_string()),
        provider: "claude".to_string(),
        label: session_id.to_string(),
        working_dir: "/tmp".to_string(),
        child_pid: 42,
        cmd_tx,
        alive: alive_flag,
        startup_gate,
    }
}
