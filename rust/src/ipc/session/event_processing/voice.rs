use std::sync::mpsc::TryRecvError;

use crate::voice::{VoiceJob, VoiceJobMessage};

use super::super::{log_debug, send_event, IpcEvent};

pub(super) fn process_voice_events(job: &VoiceJob, cancelled: bool) -> bool {
    if cancelled {
        return true;
    }

    match job.receiver.try_recv() {
        Ok(msg) => {
            match msg {
                VoiceJobMessage::Transcript {
                    text,
                    source,
                    metrics,
                } => {
                    let duration_ms = metrics.as_ref().map(|m| m.capture_ms).unwrap_or(0);
                    send_event(&IpcEvent::VoiceEnd { error: None });
                    send_event(&IpcEvent::Transcript { text, duration_ms });
                    log_debug(&format!("Voice transcript via {}", source.label()));
                }
                VoiceJobMessage::Empty { source, metrics: _ } => {
                    send_event(&IpcEvent::VoiceEnd {
                        error: Some("No speech detected".to_string()),
                    });
                    log_debug(&format!("Voice empty via {}", source.label()));
                }
                VoiceJobMessage::Error(message) => {
                    send_event(&IpcEvent::VoiceEnd {
                        error: Some(message.to_string()),
                    });
                }
            }
            true
        }
        Err(TryRecvError::Empty) => false,
        Err(TryRecvError::Disconnected) => {
            send_event(&IpcEvent::VoiceEnd {
                error: Some("Voice worker disconnected".to_string()),
            });
            true
        }
    }
}
