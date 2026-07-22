//! Memory runtime: canonical schema, storage, retrieval, and privacy controls
//! for VoiceTerm's structured memory layer.
//!
//! Module tree:
//!   memory/types.rs         - Canonical event schema and shared types
//!   memory/schema.rs        - Schema validation and SQL DDL
//!   memory/store/jsonl.rs   - Append-only JSONL event writer
//!   memory/store/sqlite.rs  - In-memory query index (SQLite contract)
//!   memory/ingest.rs        - Event ingestion pipeline
//!   memory/retrieval.rs     - Deterministic retrieval APIs
//!   memory/context_pack.rs  - Context pack generation (JSON + MD)
//!   memory/privacy.rs       - Retention, redaction, isolation policies

#![allow(
    dead_code,
    reason = "Memory Studio APIs are intentionally scaffolded ahead of full UI/runtime wiring (MP-230..MP-255)."
)]
#![allow(
    unused_imports,
    reason = "Module-level re-exports and staged helper surfaces are retained for upcoming Memory Studio integration phases."
)]

pub(crate) mod context_pack;
pub(crate) mod ingest;
pub(crate) mod privacy;
pub(crate) mod retrieval;
pub(crate) mod schema;
pub(crate) mod store;
pub(crate) mod survival_index;
pub(crate) mod types;

// Re-exports for ergonomic access from event loop and overlays.
pub(crate) use ingest::MemoryIngestor;
pub(crate) use types::{MemoryMode, RetentionPolicy};
