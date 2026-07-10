//! JSON-lines codec shared by Unix socket and WebSocket transports.

use super::types::{DaemonCommand, DaemonEvent};

/// Structured decode error instead of bare String.
#[derive(Debug)]
pub(super) enum DecodeError {
    EmptyLine,
    InvalidJson(serde_json::Error),
}

impl std::fmt::Display for DecodeError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::EmptyLine => write!(f, "empty command line"),
            Self::InvalidJson(e) => write!(f, "invalid command JSON: {e}"),
        }
    }
}

/// Decode a single JSON line into a daemon command.
pub(super) fn decode_command(line: &str) -> Result<DaemonCommand, DecodeError> {
    let trimmed = line.trim();
    if trimmed.is_empty() {
        return Err(DecodeError::EmptyLine);
    }
    serde_json::from_str(trimmed).map_err(DecodeError::InvalidJson)
}

/// Encode a daemon event as a single JSON line (no trailing newline).
pub(super) fn encode_event(event: &DaemonEvent) -> String {
    // serde-compat: allow reason=DaemonEvent variants are all non-fallible;
    // the fallback string is a defense-in-depth safeguard only.
    serde_json::to_string(event).unwrap_or_else(|_| {
        r#"{"event":"error","message":"event serialization failed"}"#.to_string()
    })
}

#[cfg(test)]
mod codec_tests {
    use super::*;

    #[test]
    fn decode_valid_command() {
        let cmd = decode_command(r#"{"cmd":"list_agents"}"#).unwrap();
        assert!(matches!(cmd, DaemonCommand::ListAgents));
    }

    #[test]
    fn decode_rejects_empty() {
        assert!(matches!(
            decode_command("").unwrap_err(),
            DecodeError::EmptyLine
        ));
        assert!(matches!(
            decode_command("   ").unwrap_err(),
            DecodeError::EmptyLine
        ));
    }

    #[test]
    fn decode_rejects_invalid_json() {
        assert!(matches!(
            decode_command("{not json}").unwrap_err(),
            DecodeError::InvalidJson(_)
        ));
    }

    #[test]
    fn decode_unknown_command_falls_through() {
        let cmd = decode_command(r#"{"cmd":"future_command_v99"}"#).unwrap();
        assert!(matches!(cmd, DaemonCommand::Unknown));
    }

    #[test]
    fn encode_produces_valid_json() {
        let event = DaemonEvent::DaemonShutdown;
        let json = encode_event(&event);
        assert!(json.contains("daemon_shutdown"));
        let _: serde_json::Value = serde_json::from_str(&json).unwrap();
    }
}
