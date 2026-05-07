"""Pre-flight validation for review-channel launch terminal mode discipline.

Closes finding F21 (operator-flagged "IS IT HEADLESS CODEX HUGE PROBLEM"):
implementer sessions launching Codex with ``--terminal none`` while the
typed ``interaction_mode`` is ``local_terminal`` silently hang on Codex CLI
auth/permission prompts. The publisher daemon then keeps
the heartbeat fresh while no actual Codex CLI process is reading the
bridge — the F4 false-positive pattern documented in ``bridge.md`` Root
Cause Diagnosis.

CLAUDE.md Bootstrap explicitly states:

  "In ``local_terminal``, default relaunch/recovery to visible
  ``--terminal terminal-app`` unless the operator explicitly asked for
  headless or the governed session is already intentionally headless. In
  ``remote_control``, keep ``--terminal none``."

The portable operator-mode policy extends that branch table: modes that do
not allow local prompts cannot launch visible Terminal windows, and modes
without remote handoff authority cannot launch headless.

This module turns that documented rule into a deterministic typed gate
that the launch dispatcher can call before spawning conductors. The
function is pure: callers inject the typed ``interaction_mode``, the
caller-provided terminal mode, and an explicit override flag, and the
function returns a verdict + denial reason.

Maps to ``GUARD_AUDIT_FINDINGS.md`` Guard Family #3 (Authority-Source
Integrity Enforcement): "reject compatibility seams acting like hidden
runtime authority". A headless launch in ``local_terminal`` mode is
exactly such a compatibility seam — it looks like a launch but cannot
actually run a CLI conductor that needs an interactive Terminal.

The integration into ``launch_sessions_if_requested`` (in
``bridge_launch_control.py``) is the live dispatch gate. The caller must pass
governance/startup-owned interaction mode, not compatibility bridge prose.
"""

from __future__ import annotations

import tempfile
from dataclasses import dataclass
from pathlib import Path

from ...runtime.operator_context import operator_mode_policy


@dataclass(frozen=True, slots=True)
class LauncherDisciplineVerdict:
    """Typed verdict for one launcher-discipline pre-flight check.

    The verdict is intentionally minimal: ``allowed`` is the boolean
    answer the dispatcher acts on, ``denial_reason`` is a stable code
    for typed surfaces and tests, and ``operator_message`` is the
    human-readable explanation a denied launch should surface to the
    operator (and write into the launcher report payload).
    """

    allowed: bool
    denial_reason: str = ""
    operator_message: str = ""


@dataclass(frozen=True, slots=True)
class LaunchVisibilityDecision:
    """Resolved launch visibility from CLI request plus typed operator facts."""

    terminal: str
    requested_session_visibility: str
    reason: str
    explicit_terminal: bool
    attachment_active: bool
    interaction_mode: str


def resolve_launch_visibility(
    *,
    interaction_mode: str,
    requested_terminal: str | None,
    requested_session_visibility: str | None = None,
    attachment_active: bool = False,
) -> LaunchVisibilityDecision:
    """Resolve launch terminal mode before discipline or session construction.

    The CLI parser leaves ``--terminal`` unset when the operator did not
    explicitly choose a visibility mode. Remote-control attachments and other
    typed remote modes then default to headless; local operator modes default
    to a visible Terminal launch.
    """
    normalized_terminal = str(requested_terminal or "").strip()
    normalized_visibility = str(requested_session_visibility or "").strip()
    normalized_mode = str(interaction_mode or "").strip()
    explicit_terminal = bool(normalized_terminal)
    if normalized_terminal in {"terminal-app", "none"}:
        visibility = normalized_visibility or (
            "headless" if normalized_terminal == "none" else "visible"
        )
        return LaunchVisibilityDecision(
            terminal=normalized_terminal,
            requested_session_visibility=visibility,
            reason="explicit_terminal_request",
            explicit_terminal=True,
            attachment_active=bool(attachment_active),
            interaction_mode=normalized_mode,
        )
    if normalized_terminal:
        return LaunchVisibilityDecision(
            terminal=normalized_terminal,
            requested_session_visibility=normalized_visibility,
            reason="invalid_terminal_request",
            explicit_terminal=True,
            attachment_active=bool(attachment_active),
            interaction_mode=normalized_mode,
        )

    policy = operator_mode_policy(normalized_mode)
    if attachment_active or policy.headless_required or policy.remote_handoff_allowed:
        return LaunchVisibilityDecision(
            terminal="none",
            requested_session_visibility=normalized_visibility or "headless",
            reason=(
                "remote_control_attachment_headless_default"
                if attachment_active
                else "remote_mode_headless_default"
            ),
            explicit_terminal=explicit_terminal,
            attachment_active=bool(attachment_active),
            interaction_mode=normalized_mode,
        )
    return LaunchVisibilityDecision(
        terminal="terminal-app",
        requested_session_visibility=normalized_visibility or "visible",
        reason="local_operator_visible_default",
        explicit_terminal=explicit_terminal,
        attachment_active=bool(attachment_active),
        interaction_mode=normalized_mode,
    )


def validate_visible_launch_in_local_mode(
    *,
    interaction_mode: str,
    terminal_arg: str,
) -> LauncherDisciplineVerdict:
    """Return a typed verdict for one launch-time terminal-mode decision.

    Inputs:

    - ``interaction_mode``: the typed operator interaction mode read from
      ``bridge_liveness.interaction_mode`` /
      ``startup_context.interaction_mode``. Pass exactly the string the
      typed surface returned; do not pre-normalize beyond ``.strip()``.
    - ``terminal_arg``: the value of ``--terminal`` on the launch
      invocation. The two valid values today are ``"terminal-app"`` and
      ``"none"``; any other value is rejected as malformed.
    Verdict semantics:

    - ``allowed=True`` with empty ``denial_reason`` -> launch may proceed.
    - ``allowed=False`` with a ``denial_reason`` code -> launch must be
      blocked. The denial reason is a stable token (one of the
      module-level constants defined alongside the verdict tests) so
      typed surfaces and dashboards can branch on it.

Decision rules (in evaluation order):

    1. ``terminal_arg`` is malformed (not ``terminal-app`` or ``none``) ->
       DENIED with ``invalid_terminal_arg``. Fail-closed catch.
    2. ``terminal_arg == "terminal-app"`` AND the operator-mode policy
       disallows local prompts -> DENIED with a visible-launch reason.
    3. ``terminal_arg == "terminal-app"`` -> ALLOWED. Visible Terminal is
       safe for local operator modes.
    4. ``terminal_arg == "none"`` AND the operator-mode policy allows remote
       handoff -> ALLOWED.
    5. ``terminal_arg == "none"`` AND the operator-mode policy requires local
       prompts or the mode is unresolved -> DENIED with
       ``headless_launch_in_local_mode``. This is the F21 trap.
    6. Anything else hitting ``terminal_arg == "none"`` (unknown
       interaction_mode value not covered above) -> DENIED with
       ``headless_launch_unknown_interaction_mode``. Fail-closed default
       so a future enum value cannot silently bypass the gate.

    The function is deterministic and side-effect free: no I/O and no runtime
    state reads beyond the static operator-mode policy table. Tests inject all
    inputs and assert on the verdict.
    """
    normalized_terminal = (terminal_arg or "").strip()
    if normalized_terminal not in {"terminal-app", "none"}:
        return LauncherDisciplineVerdict(
            allowed=False,
            denial_reason="invalid_terminal_arg",
            operator_message=(
                f"Refusing launch: terminal arg `{terminal_arg!r}` is not one"
                " of the two supported values (`terminal-app` or `none`)."
            ),
        )
    normalized_mode = (interaction_mode or "").strip()
    policy = operator_mode_policy(normalized_mode)
    raw_mode_unknown = bool(normalized_mode) and policy.mode != normalized_mode
    if normalized_terminal == "terminal-app":
        if policy.headless_required:
            denial_reason = (
                "visible_launch_in_remote_control"
                if policy.mode == "remote_control"
                else "visible_launch_without_local_operator"
            )
            return LauncherDisciplineVerdict(
                allowed=False,
                denial_reason=denial_reason,
                operator_message=(
                    "Refusing visible Terminal.app launch because typed "
                    f"interaction_mode is `{policy.mode}`. The active operator "
                    "will not see local provider prompts; use `--terminal none` "
                    "only when typed remote handoff authority is present."
                ),
            )
        return LauncherDisciplineVerdict(allowed=True)
    # From here down: terminal_arg == "none" (headless launch requested).
    if policy.remote_handoff_allowed:
        return LauncherDisciplineVerdict(allowed=True)
    if policy.local_prompts_allowed or normalized_mode in {"", "unresolved"}:
        return LauncherDisciplineVerdict(
            allowed=False,
            denial_reason="headless_launch_in_local_mode",
            operator_message=(
                "Refusing headless Codex launch (`--terminal none`) because"
                f" typed interaction_mode is `{normalized_mode or 'unresolved'}`,"
                " not `remote_control`. Headless Codex CLI silently hangs on"
                " auth/permission prompts and the publisher daemon then fakes"
                " aliveness. Use `--terminal terminal-app` (visible local"
                " launch) per CLAUDE.md Bootstrap."
            ),
        )
    if raw_mode_unknown:
        return LauncherDisciplineVerdict(
            allowed=False,
            denial_reason="headless_launch_unknown_interaction_mode",
            operator_message=(
                "Refusing headless Codex launch (`--terminal none`) because typed"
                f" interaction_mode `{normalized_mode!r}` is not in the recognized"
                " set. Update the operator-mode policy before launching headless."
            ),
        )
    # Fail-closed default for any unknown interaction_mode token. A future
    # enum value should not silently bypass the gate; the operator must
    # explicitly override or update the visible-required set.
    return LauncherDisciplineVerdict(
        allowed=False,
        denial_reason="headless_launch_unknown_interaction_mode",
        operator_message=(
            "Refusing headless Codex launch (`--terminal none`) because typed"
            f" interaction_mode `{normalized_mode!r}` is not in the recognized"
            " set. Update the visible-required or headless-permitted set before"
            " launching headless."
        ),
    )


def validate_trusted_visible_launch_root(
    *,
    repo_root: Path | None,
    terminal_arg: str,
) -> LauncherDisciplineVerdict:
    """Refuse visible local launches from transient temp roots.

    Provider CLIs can prompt for one-time trust/approval when a brand-new
    directory opens in a visible terminal. Local review-channel automation
    should not rely on an operator clicking through those prompts from an
    ephemeral clone under ``/tmp``. The stable fix is to keep normal local
    launches on repo-managed trusted roots and fail closed before any Terminal
    window or daemon starts when the requested visible launch target is a
    transient temp directory.
    """
    normalized_terminal = (terminal_arg or "").strip()
    if normalized_terminal != "terminal-app":
        return LauncherDisciplineVerdict(allowed=True)
    if repo_root is None:
        return LauncherDisciplineVerdict(allowed=True)
    resolved_repo_root = repo_root.expanduser().resolve(strict=False)
    if (
        _looks_like_repo_checkout(resolved_repo_root)
        and any(
            _path_within_root(resolved_repo_root, transient_root)
            for transient_root in _transient_launch_roots()
        )
    ):
        return LauncherDisciplineVerdict(
            allowed=False,
            denial_reason="untrusted_visible_launch_root",
            operator_message=(
                "Refusing visible Terminal.app launch from transient temp clone "
                f"`{resolved_repo_root}` because provider directory-trust prompts "
                "can stall local automation there. Re-run from a stable repo-managed "
                "root or reserve headless launches for governed `remote_control`."
            ),
        )
    return LauncherDisciplineVerdict(allowed=True)


def _transient_launch_roots() -> tuple[Path, ...]:
    temp_root = Path(tempfile.gettempdir()).expanduser().resolve(strict=False)
    candidates = (
        temp_root,
        Path("/tmp").resolve(strict=False),
        Path("/private/tmp").resolve(strict=False),
    )
    ordered_unique: list[Path] = []
    for candidate in candidates:
        if candidate not in ordered_unique:
            ordered_unique.append(candidate)
    return tuple(ordered_unique)


def _path_within_root(path: Path, root: Path) -> bool:
    return path == root or root in path.parents


def _looks_like_repo_checkout(repo_root: Path) -> bool:
    return (repo_root / ".git").exists()


from .launcher_discipline_enforcement import enforce_launch_request_discipline


__all__ = [
    "LauncherDisciplineVerdict",
    "LaunchVisibilityDecision",
    "enforce_launch_request_discipline",
    "resolve_launch_visibility",
    "validate_trusted_visible_launch_root",
    "validate_visible_launch_in_local_mode",
]
