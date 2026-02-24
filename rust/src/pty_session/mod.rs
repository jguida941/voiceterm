//! Minimal PTY wrapper used to host backend CLIs in a real terminal so persistent sessions
//! can keep state (tools, environment) between prompts.

mod counters;
mod io;
mod osc;
mod pty;
mod session_guard;

#[cfg(test)]
mod tests;

pub use pty::{PtyCliSession, PtyOverlaySession};

#[cfg(test)]
pub(crate) use counters::{
    pty_session_read_count, pty_session_send_count, reset_pty_session_counters,
};

#[cfg(test)]
pub(crate) use pty::test_pty_session;
