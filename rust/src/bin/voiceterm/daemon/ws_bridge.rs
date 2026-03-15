//! WebSocket bridge so iPhone and remote clients connect to the daemon hub.

use std::sync::Arc;

use futures_util::{SinkExt, StreamExt};
use tokio::net::TcpListener;
use tokio::sync::mpsc;
use tokio_tungstenite::accept_async;
use tungstenite::Message;

use voiceterm::log_debug;

use super::client_codec::{decode_command, encode_event};
use super::event_bus::EventBus;
use super::socket_listener::ClientCommand;
use super::types::{ClientId, DaemonEvent};

/// Accept loop for WebSocket connections on a TCP port.
pub(super) async fn run_ws_bridge(
    listener: TcpListener,
    cmd_tx: mpsc::Sender<ClientCommand>,
    event_bus: Arc<EventBus>,
) {
    log_debug("daemon: WebSocket bridge started");
    loop {
        match listener.accept().await {
            Ok((stream, addr)) => {
                let client_id = ClientId::new("ws");
                let cmd_tx = cmd_tx.clone();
                let event_rx = event_bus.subscribe();
                log_debug(&format!(
                    "daemon: WebSocket client connected: {} from {addr}",
                    client_id.0
                ));
                tokio::spawn(handle_ws_client(stream, client_id, cmd_tx, event_rx));
            }
            Err(err) => {
                log_debug(&format!("daemon: WebSocket accept error: {err}"));
            }
        }
    }
}

/// Handle a single WebSocket client: read command frames, write event frames.
async fn handle_ws_client(
    stream: tokio::net::TcpStream,
    client_id: ClientId,
    cmd_tx: mpsc::Sender<ClientCommand>,
    mut event_rx: tokio::sync::broadcast::Receiver<DaemonEvent>,
) {
    let ws_stream = match accept_async(stream).await {
        Ok(ws) => ws,
        Err(err) => {
            log_debug(&format!(
                "daemon: WebSocket handshake failed for {}: {err}",
                client_id.0
            ));
            return;
        }
    };

    let (mut ws_sink, mut ws_source) = ws_stream.split();
    let cid = client_id.0.clone();

    loop {
        tokio::select! {
            frame = ws_source.next() => {
                let should_break = handle_ws_frame(
                    frame, &client_id, &cmd_tx, &mut ws_sink, &cid,
                ).await;
                if should_break { break; }
            }
            event_result = event_rx.recv() => {
                match event_result {
                    Ok(event) => {
                        let json = encode_event(&event);
                        if ws_sink.send(Message::Text(json)).await.is_err() {
                            break;
                        }
                    }
                    Err(tokio::sync::broadcast::error::RecvError::Lagged(n)) => {
                        log_debug(&format!("daemon: ws client {cid} lagged {n} events"));
                    }
                    Err(tokio::sync::broadcast::error::RecvError::Closed) => break,
                }
            }
        }
    }

    log_debug(&format!("daemon: WebSocket client disconnected: {cid}"));
}

/// Process one WebSocket frame. Returns true when the connection should close.
async fn handle_ws_frame(
    frame: Option<Result<Message, tungstenite::Error>>,
    client_id: &ClientId,
    cmd_tx: &mpsc::Sender<ClientCommand>,
    ws_sink: &mut futures_util::stream::SplitSink<
        tokio_tungstenite::WebSocketStream<tokio::net::TcpStream>,
        Message,
    >,
    cid: &str,
) -> bool {
    match frame {
        Some(Ok(Message::Text(text))) => {
            match decode_command(&text) {
                Ok(command) => {
                    let msg = ClientCommand {
                        client_id: client_id.clone(),
                        command,
                    };
                    if cmd_tx.send(msg).await.is_err() {
                        return true;
                    }
                }
                Err(err) => {
                    let json = encode_event(&DaemonEvent::Error {
                        message: err.to_string(),
                        session_id: None,
                    });
                    // Client may have disconnected between read and write.
                    if ws_sink.send(Message::Text(json)).await.is_err() {
                        return true;
                    }
                }
            }
            false
        }
        Some(Ok(Message::Close(_))) | None => true,
        Some(Ok(_)) => false, // Ignore binary/ping/pong frames.
        Some(Err(err)) => {
            log_debug(&format!("daemon: ws client {cid} error: {err}"));
            true
        }
    }
}
