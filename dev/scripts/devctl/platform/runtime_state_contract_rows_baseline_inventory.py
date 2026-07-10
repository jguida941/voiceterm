"""Baseline-authority inventory runtime-state contract rows."""

from __future__ import annotations

from .contracts import ContractField, ContractSpec

BASELINE_INVENTORY_STATE_CONTRACTS: tuple[ContractSpec, ...] = (
    ContractSpec(
        contract_id="BaselineAuthorityInventoryReceipt",
        owner_layer="governance_runtime",
        purpose=(
            "Typed baseline inventory captured before MP-377 substrate changes so "
            "state stores, writers, readers, projections, duplicate clusters, and "
            "repo proof are auditable from one durable receipt."
        ),
        required_fields=(
            ContractField("inventory_id", "str", "Stable receipt hash for this baseline inventory."),
            ContractField("recorded_at_utc", "str", "UTC timestamp for the baseline capture."),
            ContractField("repo_root", "str", "Resolved repo root used during the scan."),
            ContractField(
                "repo_state_fingerprint",
                "dict[str, object]",
                "Best-effort repo/git fingerprint captured alongside the inventory.",
            ),
            ContractField(
                "search_patterns",
                "tuple[str, ...]",
                "Registry sources and scan patterns used to derive the inventory.",
            ),
            ContractField(
                "file_counts",
                "dict[str, int]",
                "Bounded file and site counts observed during the baseline scan.",
            ),
            ContractField(
                "state_store_entries",
                "tuple[dict[str, object], ...]",
                "Known governed stores with current writer refs and locking posture.",
            ),
            ContractField(
                "state_files",
                "tuple[str, ...]",
                "Repo-relative governed state files discovered during the scan.",
            ),
            ContractField(
                "direct_write_sites",
                "tuple[dict[str, object], ...]",
                "Code sites using raw write APIs such as write_text/open('a')/open('w').",
            ),
            ContractField(
                "direct_read_sites",
                "tuple[dict[str, object], ...]",
                "Code sites using raw read APIs such as read_text().",
            ),
            ContractField(
                "generated_projection_paths",
                "tuple[str, ...]",
                "Known generated projections and review-channel projection artifacts.",
            ),
            ContractField(
                "workflow_surfaces",
                "tuple[str, ...]",
                "GitHub workflow files visible to the current repo snapshot.",
            ),
            ContractField(
                "check_surfaces",
                "tuple[str, ...]",
                "Registered check-script surfaces visible from the catalog registry.",
            ),
            ContractField(
                "bundle_surfaces",
                "tuple[str, ...]",
                "Registered bundle ids visible from the bundle registry.",
            ),
            ContractField(
                "packet_kinds",
                "tuple[str, ...]",
                "Valid packet kinds currently accepted by the review-channel contract.",
            ),
            ContractField(
                "reducer_sites",
                "tuple[dict[str, object], ...]",
                "Reducer functions discovered by the baseline scan.",
            ),
            ContractField(
                "event_producer_sites",
                "tuple[dict[str, object], ...]",
                "Code sites that publish review-channel events.",
            ),
            ContractField(
                "event_subscriber_sites",
                "tuple[dict[str, object], ...]",
                "Code sites that read/reduce event-backed review-channel state.",
            ),
            ContractField(
                "compatibility_shims",
                "tuple[dict[str, object], ...]",
                "Legacy/compatibility/fallback surfaces that may become duplicate authority.",
            ),
            ContractField(
                "duplicate_system_clusters",
                "tuple[dict[str, object], ...]",
                "Known duplicate-system clusters that later MP-377 slices must collapse.",
            ),
            ContractField(
                "system_catalog_counts",
                "dict[str, int]",
                "High-level counts from the generated SystemCatalog.",
            ),
            ContractField(
                "connectivity_registry_counts",
                "dict[str, int]",
                "High-level counts from the connectivity registry snapshot.",
            ),
            ContractField("receipt_path", "str", "Durable JSONL path for this receipt family."),
            ContractField("status", "str", "accepted or preview."),
            ContractField("dry_run", "bool", "Whether the baseline receipt was preview-only."),
        ),
        runtime_model=(
            "dev.scripts.devctl.runtime.baseline_authority_inventory:"
            "BaselineAuthorityInventoryReceipt"
        ),
        startup_surface_tokens=(
            "repo_state_fingerprint",
            "state_store_entries",
            "duplicate_system_clusters",
            "status",
        ),
    ),
)

__all__ = ["BASELINE_INVENTORY_STATE_CONTRACTS"]
