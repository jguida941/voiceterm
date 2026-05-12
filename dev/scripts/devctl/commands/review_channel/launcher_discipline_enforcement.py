"""Bypass-aware launcher-discipline enforcement."""

from __future__ import annotations

from pathlib import Path


def enforce_launch_request_discipline(
    *,
    repo_root: Path | None,
    interaction_mode: str,
    terminal_arg: str,
    bypass_reason: str = "",
    bypass_receipt_id: str = "",
) -> dict[str, object] | None:
    """Raise when a launch request violates visible/headless discipline.

    When ``bypass_reason`` is a non-empty string, refused verdicts are
    overridden and a typed ``LauncherDisciplineBypass`` receipt dict is
    returned so the caller can log it to the event store.
    """
    from .launcher_discipline import (
        validate_trusted_visible_launch_root,
        validate_visible_launch_in_local_mode,
    )

    bypass_lifecycle = _active_bypass_lifecycle(
        repo_root=repo_root,
        bypass_receipt_id=bypass_receipt_id,
    )
    effective_bypass_reason = (
        bypass_lifecycle.receipt.reason
        if bypass_lifecycle is not None and bypass_lifecycle.receipt is not None
        else bypass_reason
    )
    bypass_records: list[dict[str, object]] = []
    trusted_root_verdict = validate_trusted_visible_launch_root(
        repo_root=repo_root,
        terminal_arg=terminal_arg,
    )
    if not trusted_root_verdict.allowed:
        if not effective_bypass_reason:
            raise ValueError(
                "Launcher discipline refused this launch: "
                f"reason={trusted_root_verdict.denial_reason}. "
                f"{trusted_root_verdict.operator_message}"
            )
        bypass_records.append(
            _build_bypass_record(
                verdict=trusted_root_verdict,
                bypass_reason=effective_bypass_reason,
                terminal_arg=terminal_arg,
                interaction_mode=interaction_mode,
                bypass_receipt_id=bypass_receipt_id,
                bypass_lifecycle_id=(
                    bypass_lifecycle.lifecycle_id if bypass_lifecycle is not None else ""
                ),
            )
        )

    discipline_verdict = validate_visible_launch_in_local_mode(
        interaction_mode=interaction_mode,
        terminal_arg=terminal_arg,
    )
    if not discipline_verdict.allowed:
        if not effective_bypass_reason:
            raise ValueError(
                "Launcher discipline refused this launch: "
                f"reason={discipline_verdict.denial_reason}. "
                f"{discipline_verdict.operator_message}"
            )
        bypass_records.append(
            _build_bypass_record(
                verdict=discipline_verdict,
                bypass_reason=effective_bypass_reason,
                terminal_arg=terminal_arg,
                interaction_mode=interaction_mode,
                bypass_receipt_id=bypass_receipt_id,
                bypass_lifecycle_id=(
                    bypass_lifecycle.lifecycle_id if bypass_lifecycle is not None else ""
                ),
            )
        )

    if not bypass_records:
        return None
    receipt = dict(
        schema_version=1,
        contract_id="LauncherDisciplineBypass",
        bypass_reason=effective_bypass_reason,
        terminal_arg=terminal_arg,
        interaction_mode=interaction_mode,
        bypassed_verdicts=bypass_records,
    )
    if bypass_receipt_id:
        receipt["bypass_receipt_id"] = bypass_receipt_id
    if bypass_lifecycle is not None:
        receipt["bypass_lifecycle_id"] = bypass_lifecycle.lifecycle_id
    return receipt


def _build_bypass_record(
    *,
    verdict: object,
    bypass_reason: str,
    terminal_arg: str,
    interaction_mode: str,
    bypass_receipt_id: str = "",
    bypass_lifecycle_id: str = "",
) -> dict[str, object]:
    """Typed record for one bypassed launcher-discipline verdict."""
    record = {
        "denial_reason": getattr(verdict, "denial_reason", ""),
        "operator_message": getattr(verdict, "operator_message", ""),
        "bypass_reason": bypass_reason,
        "terminal_arg": terminal_arg,
        "interaction_mode": interaction_mode,
    }
    if bypass_receipt_id:
        record["bypass_receipt_id"] = bypass_receipt_id
    if bypass_lifecycle_id:
        record["bypass_lifecycle_id"] = bypass_lifecycle_id
    return record


def _active_bypass_lifecycle(
    *,
    repo_root: Path | None,
    bypass_receipt_id: str,
):
    if repo_root is None or not bypass_receipt_id:
        return None
    from ...runtime.lifetime_bypass_mode import (
        DEFAULT_BYPASS_LIFECYCLE_STORE_REL,
        BypassAuthorityScope,
        active_bypass_lifecycle_for_receipt_id,
    )

    return active_bypass_lifecycle_for_receipt_id(
        bypass_receipt_id,
        store_path=repo_root / DEFAULT_BYPASS_LIFECYCLE_STORE_REL,
        required_scope=BypassAuthorityScope.EDIT_ONLY,
    )


__all__ = ["enforce_launch_request_discipline"]
