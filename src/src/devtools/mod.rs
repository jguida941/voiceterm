//! Shared Dev Mode building blocks for runtime overlays and offline tooling.

pub mod events;
pub mod state;
pub mod storage;

pub use events::{
    DevCaptureSource, DevEvent, DevEventKind, DEV_EVENT_SCHEMA_VERSION, DEV_EVENT_SOURCE_UNKNOWN,
};
pub use state::{DevModeSnapshot, DevModeStats, DEFAULT_DEV_EVENT_RING_CAPACITY};
pub use storage::{
    default_dev_root_dir, new_session_log_path, DevEventJsonlWriter, DEV_LOG_DIR_NAME,
    DEV_LOG_SESSIONS_DIR_NAME,
};
