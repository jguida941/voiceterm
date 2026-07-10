mod commands;
mod refresh_poll;
mod refresh_state;

use std::path::PathBuf;
use std::sync::atomic::{AtomicU64, Ordering};

/// Provision an isolated directory containing a `bridge.md` review artifact
/// and return its path. The repo root no longer carries a bridge.md (the
/// root governance docs were archived to `dev/archive/root-governance-docs/`),
/// so Review-tab tests that need a loadable artifact must provision their own
/// tree and point `state.working_dir` at it instead of depending on repo
/// state.
fn provision_bridge_fixture(prefix: &str, content: &str) -> PathBuf {
    static COUNTER: AtomicU64 = AtomicU64::new(0);
    let now = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .unwrap_or_default()
        .as_nanos();
    let dir = std::env::temp_dir().join(format!(
        "voiceterm-devpanel-bridge-{prefix}-{now}-{}",
        COUNTER.fetch_add(1, Ordering::Relaxed)
    ));
    std::fs::create_dir_all(&dir).expect("create bridge fixture dir");
    std::fs::write(dir.join("bridge.md"), content).expect("write bridge.md fixture");
    dir
}
