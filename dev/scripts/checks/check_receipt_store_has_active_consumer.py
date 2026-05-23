#!/usr/bin/env python3
"""Backward-compat shim -- use `receipt_store_consumer.command`."""
# shim-owner: tooling/governance
# shim-reason: preserve the stable receipt-store consumer guard entrypoint during package extraction
# shim-expiry: 2026-12-31
# shim-target: dev/scripts/checks/receipt_store_consumer/command.py
if __package__:
    from .receipt_store_consumer.command import main
    from .receipt_store_consumer.defaults import DEFAULT_CLASSIFICATIONS
    from .receipt_store_consumer.git_status import (
        git_changed_paths as _git_changed_paths,
        path_from_git_status_line as _path_from_git_status_line,
    )
    from .receipt_store_consumer.models import (
        COMMAND,
        CONTRACT_ID,
        DISPLAY_TEXT,
        REASON_MISSING_CLASSIFICATION,
        REASON_NO_READER,
        REASON_NO_WRITER,
        ReceiptStoreClassification,
        ReceiptStoreViolation,
    )
    from .receipt_store_consumer.paths import (
        all_receipt_store_paths as _all_receipt_store_paths,
        changed_receipt_store_paths as _changed_receipt_store_paths,
        repo_path as _repo_path,
        store_paths_for_scope as _store_paths_for_scope,
    )
    from .receipt_store_consumer.report import build_report, render_markdown
else:
    from receipt_store_consumer.command import main
    from receipt_store_consumer.defaults import DEFAULT_CLASSIFICATIONS
    from receipt_store_consumer.git_status import (
        git_changed_paths as _git_changed_paths,
        path_from_git_status_line as _path_from_git_status_line,
    )
    from receipt_store_consumer.models import (
        COMMAND,
        CONTRACT_ID,
        DISPLAY_TEXT,
        REASON_MISSING_CLASSIFICATION,
        REASON_NO_READER,
        REASON_NO_WRITER,
        ReceiptStoreClassification,
        ReceiptStoreViolation,
    )
    from receipt_store_consumer.paths import (
        all_receipt_store_paths as _all_receipt_store_paths,
        changed_receipt_store_paths as _changed_receipt_store_paths,
        repo_path as _repo_path,
        store_paths_for_scope as _store_paths_for_scope,
    )
    from receipt_store_consumer.report import build_report, render_markdown
if __name__ == "__main__":
    raise SystemExit(main())
