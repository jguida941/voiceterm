#!/usr/bin/env python3
"""Backward-compat shim -- use `receipt_store_coverage_sweep.command`."""
# shim-owner: tooling/governance
# shim-reason: preserve the stable coverage-sweep guard entrypoint during package extraction
# shim-expiry: 2026-12-31
# shim-target: dev/scripts/checks/receipt_store_coverage_sweep/command.py
if __package__:
    from .receipt_store_consumer.git_status import (
        git_changed_paths as _git_changed_paths,
        path_from_git_status_line as _path_from_git_status_line,
    )
    from .receipt_store_coverage_sweep.command import main
    from .receipt_store_coverage_sweep.coverage import (
        schema_guard_ref_is_unresolved as _schema_guard_ref_is_unresolved,
        violations_for_classification as _violations_for_classification,
    )
    from .receipt_store_coverage_sweep.extras import (
        DEFAULT_CLASSIFICATIONS,
        _EXTRA_COVERAGE_BY_STORE,
        _default_classifications,
    )
    from .receipt_store_coverage_sweep.models import (
        COMMAND,
        CONTRACT_ID,
        DISPLAY_TEXT,
        REASON_MISSING_CLASSIFICATION,
        REASON_NO_PROVENANCE,
        REASON_NO_READER,
        REASON_NO_SCHEMA_GUARD,
        REASON_NO_WRITER,
        REASON_UNRESOLVED_SCHEMA_GUARD_REF,
        ReceiptStoreCoverage,
        ReceiptStoreCoverageViolation,
    )
    from .receipt_store_coverage_sweep.report import build_report, render_markdown
    from .receipt_store_coverage_sweep.sweep_paths import (
        all_receipt_store_paths as _all_receipt_store_paths,
        changed_receipt_store_paths as _changed_receipt_store_paths,
        repo_path as _repo_path,
        report_json_store_dirs as _report_json_store_dirs,
        report_store_path_for_json as _report_store_path_for_json,
        store_paths_for_scope as _store_paths_for_scope,
    )
else:
    from receipt_store_consumer.git_status import (
        git_changed_paths as _git_changed_paths,
        path_from_git_status_line as _path_from_git_status_line,
    )
    from receipt_store_coverage_sweep.command import main
    from receipt_store_coverage_sweep.coverage import (
        schema_guard_ref_is_unresolved as _schema_guard_ref_is_unresolved,
        violations_for_classification as _violations_for_classification,
    )
    from receipt_store_coverage_sweep.extras import (
        DEFAULT_CLASSIFICATIONS,
        _EXTRA_COVERAGE_BY_STORE,
        _default_classifications,
    )
    from receipt_store_coverage_sweep.models import (
        COMMAND,
        CONTRACT_ID,
        DISPLAY_TEXT,
        REASON_MISSING_CLASSIFICATION,
        REASON_NO_PROVENANCE,
        REASON_NO_READER,
        REASON_NO_SCHEMA_GUARD,
        REASON_NO_WRITER,
        REASON_UNRESOLVED_SCHEMA_GUARD_REF,
        ReceiptStoreCoverage,
        ReceiptStoreCoverageViolation,
    )
    from receipt_store_coverage_sweep.report import build_report, render_markdown
    from receipt_store_coverage_sweep.sweep_paths import (
        all_receipt_store_paths as _all_receipt_store_paths,
        changed_receipt_store_paths as _changed_receipt_store_paths,
        repo_path as _repo_path,
        report_json_store_dirs as _report_json_store_dirs,
        report_store_path_for_json as _report_store_path_for_json,
        store_paths_for_scope as _store_paths_for_scope,
    )
if __name__ == "__main__":
    raise SystemExit(main())
