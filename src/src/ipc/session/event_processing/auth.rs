use std::sync::mpsc::TryRecvError;

use super::super::{send_event, IpcEvent, IpcState, Provider, AUTH_TIMEOUT};

pub(super) fn process_auth_events(state: &mut IpcState) -> bool {
    let job = match state.current_auth_job.as_mut() {
        Some(job) => job,
        None => return false,
    };

    if job.started_at.elapsed() >= AUTH_TIMEOUT {
        let provider = job.provider;
        send_event(&IpcEvent::AuthEnd {
            provider: provider.as_str().to_string(),
            success: false,
            error: Some(format!(
                "Authentication timed out after {}s",
                AUTH_TIMEOUT.as_secs()
            )),
        });
        state.emit_capabilities();
        return true;
    }

    match job.receiver.try_recv() {
        Ok(result) => {
            let provider = job.provider;
            let (success, error) = match result {
                Ok(()) => (true, None),
                Err(err) => (false, Some(err)),
            };

            if success && provider == Provider::Codex {
                state.codex_cli_backend.reset_session();
            }

            send_event(&IpcEvent::AuthEnd {
                provider: provider.as_str().to_string(),
                success,
                error,
            });
            state.emit_capabilities();
            true
        }
        Err(TryRecvError::Empty) => false,
        Err(TryRecvError::Disconnected) => {
            let provider = job.provider;
            send_event(&IpcEvent::AuthEnd {
                provider: provider.as_str().to_string(),
                success: false,
                error: Some("Auth worker disconnected".to_string()),
            });
            state.emit_capabilities();
            true
        }
    }
}
