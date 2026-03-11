//! Unix domain socket listener for local client connections (PyQt6, CLI tools).

use std::sync::Arc;

use tokio::io::{AsyncBufReadExt, AsyncWriteExt, BufReader};
use tokio::net::UnixListener;
use tokio::sync::mpsc;

use voiceterm::log_debug;

use super::client_codec::{decode_command, encode_event};
use super::event_bus::EventBus;
use super::types::{ClientId, DaemonCommand};

/// Tagged command from a specific client.
pub(super) struct ClientCommand {
    #[allow(
        dead_code,
        reason = "ClientId will be used for targeted per-client responses in follow-up work"
    )]
    pub client_id: ClientId,
    pub command: DaemonCommand,
}

/// Accept loop for the Unix domain socket. Spawns a task per connected client.
pub(super) async fn run_socket_listener(
    listener: UnixListener,
    cmd_tx: mpsc::Sender<ClientCommand>,
    event_bus: Arc<EventBus>,
) {
    log_debug("daemon: Unix socket listener started");
    loop {
        match listener.accept().await {
            Ok((stream, _addr)) => {
                let client_id = ClientId::new("unix");
                let cmd_tx = cmd_tx.clone();
                let event_rx = event_bus.subscribe();
                log_debug(&format!("daemon: client connected: {}", client_id.0));
                tokio::spawn(handle_unix_client(stream, client_id, cmd_tx, event_rx));
            }
            Err(err) => {
                log_debug(&format!("daemon: socket accept error: {err}"));
            }
        }
    }
}

/// Handle a single Unix socket client: read commands, write events.
async fn handle_unix_client(
    stream: tokio::net::UnixStream,
    client_id: ClientId,
    cmd_tx: mpsc::Sender<ClientCommand>,
    mut event_rx: tokio::sync::broadcast::Receiver<super::types::DaemonEvent>,
) {
    let (reader, mut writer) = stream.into_split();
    let mut lines = BufReader::new(reader).lines();
    let cid = client_id.0.clone();

    loop {
        tokio::select! {
            line_result = lines.next_line() => {
                match line_result {
                    Ok(Some(line)) => {
                        match decode_command(&line) {
                            Ok(command) => {
                                let msg = ClientCommand {
                                    client_id: client_id.clone(),
                                    command,
                                };
                                if cmd_tx.send(msg).await.is_err() {
                                    break;
                                }
                            }
                            Err(err) => {
                                let error_json = encode_event(
                                    &super::types::DaemonEvent::Error {
                                        message: err.to_string(),
                                        session_id: None,
                                    },
                                );
                                // best-effort: client may disconnect between read and write
                                let _best_effort = writer.write_all(error_json.as_bytes()).await;
                                let _best_effort = writer.write_all(b"\n").await;
                            }
                        }
                    }
                    Ok(None) => break, // Client disconnected.
                    Err(err) => {
                        log_debug(&format!("daemon: client {cid} read error: {err}"));
                        break;
                    }
                }
            }
            event_result = event_rx.recv() => {
                match event_result {
                    Ok(event) => {
                        let json = encode_event(&event);
                        if writer.write_all(json.as_bytes()).await.is_err() {
                            break;
                        }
                        if writer.write_all(b"\n").await.is_err() {
                            break;
                        }
                    }
                    Err(tokio::sync::broadcast::error::RecvError::Lagged(n)) => {
                        log_debug(&format!("daemon: client {cid} lagged by {n} events"));
                    }
                    Err(tokio::sync::broadcast::error::RecvError::Closed) => break,
                }
            }
        }
    }

    log_debug(&format!("daemon: client disconnected: {cid}"));
}
