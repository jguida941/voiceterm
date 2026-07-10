"""Pytest config policy checks."""

from __future__ import annotations

from pathlib import Path

PYTEST_CONFIG = Path(__file__).resolve().parents[4] / "pytest.ini"


def config_violations() -> list[dict[str, str]]:
    if not PYTEST_CONFIG.exists():
        return [{"kind": "missing_pytest_ini", "path": "pytest.ini"}]
    text = PYTEST_CONFIG.read_text(encoding="utf-8")
    required_terms = ("testpaths", "norecursedirs", "-x")
    missing = [term for term in required_terms if term not in text]
    return [
        {"kind": "pytest_ini_missing_policy", "path": "pytest.ini", "term": term}
        for term in missing
    ]
