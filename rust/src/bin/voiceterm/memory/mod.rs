//! Memory Studio runtime: canonical schema, storage, retrieval, governance,
//! and action-center foundation for VoiceTerm's structured memory layer.
//!
//! Module tree:
//!   memory/types.rs         - Canonical event schema and shared types
//!   memory/schema.rs        - Schema validation and SQL DDL
//!   memory/store/jsonl.rs   - Append-only JSONL event writer
//!   memory/store/sqlite.rs  - In-memory query index (SQLite contract)
//!   memory/ingest.rs        - Event ingestion pipeline
//!   memory/retrieval.rs     - Deterministic retrieval APIs
//!   memory/context_pack.rs  - Context pack generation (JSON + MD)
//!   memory/governance.rs    - Retention, redaction, isolation policies
//!   memory/action_audit.rs  - Action Center templates and policy tiers

pub(crate) mod action_audit;
pub(crate) mod context_pack;
pub(crate) mod governance;
pub(crate) mod ingest;
pub(crate) mod retrieval;
pub(crate) mod schema;
pub(crate) mod store;
pub(crate) mod types;

// Re-exports for ergonomic access from event loop and overlays.
pub(crate) use action_audit::ActionCenterState;
pub(crate) use ingest::MemoryIngestor;
pub(crate) use types::{MemoryMode, RetentionPolicy};
