"""Repo-portability contracts and policy lookup helpers."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .value_coercion import coerce_mapping, coerce_string, coerce_string_items

REPO_PORTABILITY_CHECK_CONTRACT_ID = "RepoPortabilityCheck"
REPO_PORTABILITY_CHECK_SCHEMA_VERSION = 1
REPO_PORTABILITY_CHECK_STORE_REL = "dev/state/repo_portability_checks.jsonl"


@dataclass(frozen=True, slots=True)
class GuardMandate:
    """Repo-policy sourced enforcement window for one guard."""

    check_id: str
    mandate_packet_id: str = ""
    observed_at_utc: str = ""
    enforced_row_prefixes: tuple[str, ...] = ()
    policy_path: str = ""
    warnings: tuple[str, ...] = ()

    def active(self) -> bool:
        """Return whether this mandate can enforce timestamp/packet windows."""
        return bool(self.mandate_packet_id or self.observed_at_utc)

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class RepoPortabilityCheck:
    """One portability scan result for a substrate path."""

    check_id: str
    target_substrate_path: str
    hardcoded_literal_count: int
    hardcoded_categories: tuple[str, ...]
    proposed_lifts: tuple[str, ...]
    repo_pack_policy_keys_needed: tuple[str, ...]
    schema_version: int = REPO_PORTABILITY_CHECK_SCHEMA_VERSION
    contract_id: str = REPO_PORTABILITY_CHECK_CONTRACT_ID

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def resolve_guard_mandate(
    check_id: str,
    *,
    repo_root: Path,
    policy_path: str | Path | None = None,
) -> GuardMandate:
    """Return the repo-policy mandate window for ``check_id``.

    Missing policy is not replaced by a repository-specific fallback. Guards
    still enforce their structural scopes, but packet/timestamp windows must
    come from repo policy so adopter repos can provide their own packet ids.
    """
    section, warnings, resolved_policy_path = _load_repo_governance_section(
        "guard_mandates",
        repo_root=repo_root,
        policy_path=policy_path,
    )
    raw_mandate = _guard_mandate_payload(section, check_id)
    return GuardMandate(
        check_id=check_id,
        mandate_packet_id=coerce_string(raw_mandate.get("mandate_packet_id")),
        observed_at_utc=coerce_string(raw_mandate.get("observed_at_utc")),
        enforced_row_prefixes=coerce_string_items(
            raw_mandate.get("enforced_row_prefixes")
        ),
        policy_path=_display_path(resolved_policy_path, repo_root=repo_root),
        warnings=warnings,
    )


def load_repo_portability_policy(
    *,
    repo_root: Path,
    policy_path: str | Path | None = None,
) -> tuple[dict[str, Any], tuple[str, ...], Path]:
    """Return the repo-governance portability policy section."""
    section, warnings, resolved_policy_path = _load_repo_governance_section(
        "repo_portability",
        repo_root=repo_root,
        policy_path=policy_path,
    )
    return dict(section), warnings, resolved_policy_path


def portability_target_paths(policy: dict[str, Any]) -> tuple[str, ...]:
    return coerce_string_items(policy.get("target_paths"))


def portability_ignore_paths(policy: dict[str, Any]) -> tuple[str, ...]:
    return coerce_string_items(policy.get("ignore_paths"))


def portability_allowed_literals(policy: dict[str, Any]) -> dict[str, tuple[str, ...]]:
    raw = coerce_mapping(policy.get("allowed_literals"))
    return {
        coerce_string(category): coerce_string_items(values)
        for category, values in raw.items()
        if coerce_string(category)
    }


def portability_project_name_literals(policy: dict[str, Any]) -> tuple[str, ...]:
    return coerce_string_items(policy.get("project_name_literals"))


def portability_operator_identity_literals(policy: dict[str, Any]) -> tuple[str, ...]:
    return coerce_string_items(policy.get("operator_identity_literals"))


def _guard_mandate_payload(
    section: dict[str, Any],
    check_id: str,
) -> dict[str, Any]:
    normalized = check_id.strip()
    candidates = (
        normalized,
        normalized.removeprefix("check_"),
        f"check_{normalized}" if not normalized.startswith("check_") else normalized,
    )
    for candidate in candidates:
        payload = coerce_mapping(section.get(candidate))
        if payload:
            return dict(payload)
    return {}


def _load_repo_governance_section(
    section_name: str,
    *,
    repo_root: Path,
    policy_path: str | Path | None,
) -> tuple[dict[str, Any], tuple[str, ...], Path]:
    try:
        from ..governance.repo_policy import load_repo_governance_section

        section, warnings, resolved_policy_path = load_repo_governance_section(
            section_name,
            repo_root=repo_root,
            policy_path=policy_path,
        )
        return dict(section), tuple(warnings), resolved_policy_path
    except Exception as exc:  # pragma: no cover - policy loader fallback.
        return {}, (f"repo_policy_unavailable:{exc.__class__.__name__}",), (
            repo_root / "dev/config/devctl_repo_policy.json"
        )


def _display_path(path: Path, *, repo_root: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


__all__ = [
    "REPO_PORTABILITY_CHECK_CONTRACT_ID",
    "REPO_PORTABILITY_CHECK_SCHEMA_VERSION",
    "REPO_PORTABILITY_CHECK_STORE_REL",
    "GuardMandate",
    "RepoPortabilityCheck",
    "load_repo_portability_policy",
    "portability_allowed_literals",
    "portability_ignore_paths",
    "portability_operator_identity_literals",
    "portability_project_name_literals",
    "portability_target_paths",
    "resolve_guard_mandate",
]
