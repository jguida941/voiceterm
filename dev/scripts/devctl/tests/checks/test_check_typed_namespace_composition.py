from pathlib import Path

from dev.scripts.checks.check_typed_namespace_composition import (
    NON_COMPOSITION_RATIONALE_MARKER,
    TypedNamespaceRule,
    evaluate_typed_namespace_composition,
)


def test_typed_namespace_importing_canonical_authority_passes(tmp_path: Path) -> None:
    _write(tmp_path, "pkg/runtime/family_canonical.py", "CANONICAL = True\n")
    _write(
        tmp_path,
        "pkg/runtime/family_reader.py",
        "from .family_canonical import CANONICAL\n",
    )

    report = evaluate_typed_namespace_composition(
        repo_root=tmp_path,
        rules=(
            TypedNamespaceRule(
                family_id="family",
                glob_pattern="pkg/runtime/family_*.py",
                canonical_path="pkg/runtime/family_canonical.py",
                canonical_import_module="family_canonical",
            ),
        ),
    )

    assert report.ok is True
    assert report.scanned_file_count == 2
    assert report.canonical_file_count == 1
    assert report.composed_file_count == 1
    assert report.violation_count == 0


def test_typed_namespace_non_composition_rationale_passes(tmp_path: Path) -> None:
    _write(tmp_path, "pkg/runtime/family_canonical.py", "CANONICAL = True\n")
    _write(
        tmp_path,
        "pkg/runtime/family_lower_layer.py",
        f'"""{NON_COMPOSITION_RATIONALE_MARKER} lower layer."""\n',
    )

    report = evaluate_typed_namespace_composition(
        repo_root=tmp_path,
        rules=(
            TypedNamespaceRule(
                family_id="family",
                glob_pattern="pkg/runtime/family_*.py",
                canonical_path="pkg/runtime/family_canonical.py",
                canonical_import_module="family_canonical",
            ),
        ),
    )

    assert report.ok is True
    assert report.rationale_file_count == 1
    assert report.violation_count == 0


def test_typed_namespace_without_import_or_rationale_fails(tmp_path: Path) -> None:
    _write(tmp_path, "pkg/runtime/family_canonical.py", "CANONICAL = True\n")
    _write(tmp_path, "pkg/runtime/family_sidecar.py", "VALUE = 1\n")

    report = evaluate_typed_namespace_composition(
        repo_root=tmp_path,
        rules=(
            TypedNamespaceRule(
                family_id="family",
                glob_pattern="pkg/runtime/family_*.py",
                canonical_path="pkg/runtime/family_canonical.py",
                canonical_import_module="family_canonical",
            ),
        ),
    )

    assert report.ok is False
    assert report.report_only is False
    assert report.would_fail is True
    assert report.violation_count == 1
    assert report.violations[0]["path"] == "pkg/runtime/family_sidecar.py"
    assert report.violations[0]["family_id"] == "family"


def _write(root: Path, relative_path: str, text: str) -> None:
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
