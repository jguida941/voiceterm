"""Evidence artifact resolution helpers."""

from __future__ import annotations

from pathlib import Path

from .models import TYPED_EVIDENCE_PREFIXES


def is_concrete_pytest_node_id(value: str) -> bool:
    text = value.strip()
    return ".py::" in text and "::test" in text


def evidence_artifact_resolves(
    value: str,
    *,
    repo_root: Path,
    feature_proof_dir: Path,
) -> bool:
    text = value.strip()
    if not text:
        return False
    if is_concrete_pytest_node_id(text):
        test_path = text.split("::", 1)[0]
        return (repo_root / test_path).exists()
    prefix, separator, suffix = text.partition(":")
    if separator and prefix in TYPED_EVIDENCE_PREFIXES:
        if prefix == "ancestor_feature_proof_receipt":
            return bool(suffix.strip()) and (feature_proof_dir / f"{suffix.strip()}.json").exists()
        return bool(suffix.strip())
    candidate = repo_root / text
    return candidate.exists()
