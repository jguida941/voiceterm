"""Pre-flight validation for review-channel launch terminal mode discipline.

Closes finding F21 (operator-flagged "IS IT HEADLESS CODEX HUGE PROBLEM"):
implementer sessions launching Codex with ``--terminal none`` while the
typed ``interaction_mode`` is ``local_terminal`` (or unresolved) silently
hang on Codex CLI auth/permission prompts. The publisher daemon then keeps
the heartbeat fresh while no actual Codex CLI process is reading the
bridge — the F4 false-positive pattern documented in ``bridge.md`` Root
Cause Diagnosis.

CLAUDE.md Bootstrap explicitly states:

  "In ``local_terminal``, default relaunch/recovery to visible
  ``--terminal terminal-app`` unless the operator explicitly asked for
  headless or the governed session is already intentionally headless. In
  ``remote_control``, keep ``--terminal none``."

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

from dataclasses import dataclass
from typing import Final

# Typed ``interaction_mode`` values that REQUIRE a visible Terminal.app
# launch by default. ``unresolved`` and ``""`` are treated as "unknown,
# fail closed to visible" — the launcher must not silently default to
# headless when the typed authority is missing or empty. The
# ``local_terminal`` value is the canonical local-operator case from
# CLAUDE.md.
_VISIBLE_REQUIRED_INTERACTION_MODES: Final[frozenset[str]] = frozenset(
    {
        "local_terminal",
        "unresolved",
        "",
    }
)

# Typed ``interaction_mode`` value that legitimately permits headless
# launches without an override. The remote operator cannot open a local
# Terminal window, so ``--terminal none`` is the correct default per
# CLAUDE.md ("In remote_control, keep --terminal none").
_HEADLESS_PERMITTED_INTERACTION_MODE: Final[str] = "remote_control"


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
    2. ``terminal_arg == "terminal-app"`` -> ALLOWED. Visible Terminal is
       always safe; the only thing this gate cares about is the headless
       case.
    3. ``terminal_arg == "none"`` AND
       ``interaction_mode == "remote_control"`` -> ALLOWED. Remote
       operator legitimately needs headless because they cannot open a
       local Terminal window.
    4. ``terminal_arg == "none"`` AND
       ``interaction_mode in {"local_terminal", "unresolved", ""}`` AND
       no override -> DENIED with ``headless_launch_in_local_mode``. This is
       the F21 trap.
    5. Anything else hitting ``terminal_arg == "none"`` (unknown
       interaction_mode value not covered above) -> DENIED with
       ``headless_launch_unknown_interaction_mode``. Fail-closed default
       so a future enum value cannot silently bypass the gate.

    The function is pure: no side effects, no I/O, no globals. Tests
    inject all three inputs and assert on the verdict.
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
    if normalized_terminal == "terminal-app":
        return LauncherDisciplineVerdict(allowed=True)
    # From here down: terminal_arg == "none" (headless launch requested).
    normalized_mode = (interaction_mode or "").strip()
    if normalized_mode == _HEADLESS_PERMITTED_INTERACTION_MODE:
        return LauncherDisciplineVerdict(allowed=True)
    if normalized_mode in _VISIBLE_REQUIRED_INTERACTION_MODES:
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


__all__ = [
    "LauncherDisciplineVerdict",
    "validate_visible_launch_in_local_mode",
]
