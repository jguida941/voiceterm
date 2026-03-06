//! Terminal/theme detection so defaults match the host terminal environment.

use crate::runtime_compat::{detect_terminal_host, TerminalHost};
use std::env;

pub(super) fn is_warp_terminal() -> bool {
    is_warp_terminal_for_host(detect_terminal_host())
}

fn is_warp_terminal_for_host(host: TerminalHost) -> bool {
    if host != TerminalHost::Other {
        return false;
    }

    env::var("TERM_PROGRAM")
        .map(|value| value.to_ascii_lowercase().contains("warp"))
        .unwrap_or(false)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::test_env::{with_env_overrides, TERMINAL_HOST_ENV_KEYS};

    #[test]
    fn warp_detection_matches_term_program_for_other_host() {
        with_env_overrides(
            TERMINAL_HOST_ENV_KEYS,
            &[("TERM_PROGRAM", Some("WarpTerminal"))],
            || {
                assert!(is_warp_terminal());
            },
        );
        with_env_overrides(
            TERMINAL_HOST_ENV_KEYS,
            &[("TERM_PROGRAM", Some("WezTerm"))],
            || {
                assert!(!is_warp_terminal());
            },
        );
    }

    #[test]
    fn warp_detection_respects_canonical_host_precedence() {
        with_env_overrides(
            TERMINAL_HOST_ENV_KEYS,
            &[
                ("TERM_PROGRAM", Some("WarpTerminal")),
                ("IDEA_INITIAL_DIRECTORY", Some("/tmp/project")),
            ],
            || {
                assert!(!is_warp_terminal());
            },
        );
        with_env_overrides(
            TERMINAL_HOST_ENV_KEYS,
            &[
                ("TERM_PROGRAM", Some("WarpTerminal")),
                ("CURSOR_TRACE_ID", Some("trace")),
            ],
            || {
                assert!(!is_warp_terminal());
            },
        );
    }
}
