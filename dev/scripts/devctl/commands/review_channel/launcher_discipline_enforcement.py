"""Bypass-aware launcher-discipline enforcement."""

from __future__ import annotations

from pathlib import Path


def enforce_launch_request_discipline(
    *,
    repo_root: Path | None,
    interaction_mode: str,
    terminal_arg: str,
    bypass_reason: str = "",
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

    bypass_records: list[dict[str, object]] = []
    trusted_root_verdict = validate_trusted_visible_launch_root(
        repo_root=repo_root,
        terminal_arg=terminal_arg,
    )
    if not trusted_root_verdict.allowed:
        if not bypass_reason:
            raise ValueError(
                "Launcher discipline refused this launch: "
                f"reason={trusted_root_verdict.denial_reason}. "
                f"{trusted_root_verdict.operator_message}"
            )
        bypass_records.append(
            _build_bypass_record(
                verdict=trusted_root_verdict,
                bypass_reason=bypass_reason,
                terminal_arg=terminal_arg,
                interaction_mode=interaction_mode,
            )
        )

    discipline_verdict = validate_visible_launch_in_local_mode(
        interaction_mode=interaction_mode,
        terminal_arg=terminal_arg,
    )
    if not discipline_verdict.allowed:
        if not bypass_reason:
            raise ValueError(
                "Launcher discipline refused this launch: "
                f"reason={discipline_verdict.denial_reason}. "
                f"{discipline_verdict.operator_message}"
            )
        bypass_records.append(
            _build_bypass_record(
                verdict=discipline_verdict,
                bypass_reason=bypass_reason,
                terminal_arg=terminal_arg,
                interaction_mode=interaction_mode,
            )
        )

    if not bypass_records:
        return None
    return dict(
        schema_version=1,
        contract_id="LauncherDisciplineBypass",
        bypass_reason=bypass_reason,
        terminal_arg=terminal_arg,
        interaction_mode=interaction_mode,
        bypassed_verdicts=bypass_records,
    )


def _build_bypass_record(
    *,
    verdict: object,
    bypass_reason: str,
    terminal_arg: str,
    interaction_mode: str,
) -> dict[str, object]:
    """Typed record for one bypassed launcher-discipline verdict."""
    return {
        "denial_reason": getattr(verdict, "denial_reason", ""),
        "operator_message": getattr(verdict, "operator_message", ""),
        "bypass_reason": bypass_reason,
        "terminal_arg": terminal_arg,
        "interaction_mode": interaction_mode,
    }


__all__ = ["enforce_launch_request_discipline"]
