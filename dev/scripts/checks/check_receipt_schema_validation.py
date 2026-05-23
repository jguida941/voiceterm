#!/usr/bin/env python3
"""Backward-compat shim -- use `receipt_schema_validation.command`."""
# shim-owner: tooling/governance
# shim-reason: preserve the stable receipt-schema validation guard entrypoint during package extraction
# shim-expiry: 2026-12-31
# shim-target: dev/scripts/checks/receipt_schema_validation/command.py
if __package__:
    from .receipt_schema_validation.command import main
    from .receipt_schema_validation.evidence import (
        evidence_artifact_resolves as _evidence_artifact_resolves,
        is_concrete_pytest_node_id as _is_concrete_pytest_node_id,
    )
    from .receipt_schema_validation.git_status import (
        git_changed_paths as _git_changed_paths,
        git_commit_exists as _git_commit_exists,
        path_from_git_status_line as _path_from_git_status_line,
    )
    from .receipt_schema_validation.models import (
        COMMAND,
        CONTRACT_ID,
        DEFAULT_FEATURE_PROOF_DIR,
        DISPLAY_TEXT,
        FEATURE_PROOF_REQUIRED_FIELDS,
        REASON_INVALID_JSON,
        REASON_INVALID_SCHEMA,
        REASON_MISSING_FIELD,
        REASON_NO_PYTEST_NODE,
        REASON_NOT_MAPPING,
        REASON_UNRESOLVED_ARTIFACT,
        REASON_UNRESOLVED_COMMIT,
        REASON_WRONG_CONTRACT,
        TYPED_EVIDENCE_PREFIXES,
        ReceiptSchemaViolation,
    )
    from .receipt_schema_validation.paths import (
        changed_feature_proof_paths as _changed_feature_proof_paths,
        feature_proof_paths as _feature_proof_paths,
        feature_proof_paths_for_scope as _feature_proof_paths_for_scope,
        repo_relative as _repo_relative,
    )
    from .receipt_schema_validation.report import build_report, render_markdown
    from .receipt_schema_validation.validation import (
        validate_feature_proof_receipt as _validate_feature_proof_receipt,
    )
else:
    from receipt_schema_validation.command import main
    from receipt_schema_validation.evidence import (
        evidence_artifact_resolves as _evidence_artifact_resolves,
        is_concrete_pytest_node_id as _is_concrete_pytest_node_id,
    )
    from receipt_schema_validation.git_status import (
        git_changed_paths as _git_changed_paths,
        git_commit_exists as _git_commit_exists,
        path_from_git_status_line as _path_from_git_status_line,
    )
    from receipt_schema_validation.models import (
        COMMAND,
        CONTRACT_ID,
        DEFAULT_FEATURE_PROOF_DIR,
        DISPLAY_TEXT,
        FEATURE_PROOF_REQUIRED_FIELDS,
        REASON_INVALID_JSON,
        REASON_INVALID_SCHEMA,
        REASON_MISSING_FIELD,
        REASON_NO_PYTEST_NODE,
        REASON_NOT_MAPPING,
        REASON_UNRESOLVED_ARTIFACT,
        REASON_UNRESOLVED_COMMIT,
        REASON_WRONG_CONTRACT,
        TYPED_EVIDENCE_PREFIXES,
        ReceiptSchemaViolation,
    )
    from receipt_schema_validation.paths import (
        changed_feature_proof_paths as _changed_feature_proof_paths,
        feature_proof_paths as _feature_proof_paths,
        feature_proof_paths_for_scope as _feature_proof_paths_for_scope,
        repo_relative as _repo_relative,
    )
    from receipt_schema_validation.report import build_report, render_markdown
    from receipt_schema_validation.validation import (
        validate_feature_proof_receipt as _validate_feature_proof_receipt,
    )
if __name__ == "__main__":
    raise SystemExit(main())
