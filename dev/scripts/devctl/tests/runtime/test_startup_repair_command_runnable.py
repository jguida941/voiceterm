"""Phase 0.6.A v4.43.3 (rev_pkt_4718) — startup repair command runnable tests.

Codex's rev_pkt_4718 finding: ``BlockerSnapshot`` emitted
``python3 dev/scripts/devctl.py check --target import-index-atomicity --format md``
as the repair command for ``import_index_atomicity``, but ``devctl check``
has no ``--target`` flag → argparse error → agent trapped in false repair
loop.

v4.43.3 fixes the directive AND adds tests that every entry in
``_STARTUP_AUTHORITY_REPAIR_DIRECTIVES`` actually parses successfully via
its own argparse layer. The test invokes ``--help`` on the directive's
underlying command (which exercises argparse without doing any work)
and asserts the return code is 0.

This is the "command-contract validation" guard codex requested, scoped
to the startup repair directive table.
"""

from __future__ import annotations

import shlex
import subprocess
import sys

from dev.scripts.devctl.runtime.startup_blocker_decision import (
    _STARTUP_AUTHORITY_REPAIR_DIRECTIVES,
)


def _replace_format_with_help(command: str) -> str:
    """Replace ``--format md`` (or ``--format json``) with ``--help``.

    Invoking with ``--help`` exercises argparse without doing any real
    work: argparse prints the usage and exits 0. If the command's flags
    are invalid (e.g. ``--target import-index-atomicity`` when no
    ``--target`` exists), argparse exits non-zero with an error.

    Some flags only get checked AFTER ``--help``, but argparse normally
    short-circuits on ``--help`` before validating the others. The
    test is: can argparse PARSE the command line and print help?
    """
    tokens = shlex.split(command)
    out: list[str] = []
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        if tok == "--format" and i + 1 < len(tokens):
            i += 2  # skip --format <value>
            continue
        if tok.startswith("--format="):
            i += 1
            continue
        out.append(tok)
        i += 1
    out.append("--help")
    return " ".join(out)


def test_v4_43_3_import_index_atomicity_repair_command_parses() -> None:
    """v4.43.3 (rev_pkt_4718 verbatim regression): the repair command for
    ``import_index_atomicity`` MUST parse argparse successfully.

    Codex's prior reproduction was the broken
    ``devctl.py check --target import-index-atomicity --format md`` —
    argparse exit code 2 ("unrecognized arguments"). The fix is the
    startup-authority-contract entrypoint, which DOES accept its
    arguments."""
    directive = _STARTUP_AUTHORITY_REPAIR_DIRECTIVES["import_index_atomicity"]
    command = directive[3]
    help_form = _replace_format_with_help(command)
    tokens = shlex.split(help_form)
    # First token is "python3"; replace with the running python interpreter
    # so the test works regardless of how the suite was invoked.
    if tokens and tokens[0].startswith("python"):
        tokens[0] = sys.executable
    result = subprocess.run(
        tokens,
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert result.returncode == 0, (
        f"Repair command for import_index_atomicity failed argparse:\n"
        f"  command: {command!r}\n"
        f"  help-form: {help_form!r}\n"
        f"  returncode: {result.returncode}\n"
        f"  stderr: {result.stderr[:500]}\n"
        f"  stdout: {result.stdout[:500]}"
    )
    # The help output should mention --format (the directive's option)
    assert "--format" in result.stdout or "--format" in result.stderr


def test_v4_43_3_all_startup_repair_directives_parse() -> None:
    """v4.43.3: defense-in-depth — EVERY directive in
    ``_STARTUP_AUTHORITY_REPAIR_DIRECTIVES`` must produce a repair
    command that parses argparse. Catches regressions where a new
    directive's command is invalid before it reaches the agent loop."""
    failures: list[tuple[str, str, int, str]] = []
    for blocker_kind, directive in _STARTUP_AUTHORITY_REPAIR_DIRECTIVES.items():
        command = directive[3]
        if not command:
            continue  # Empty repair command — skip
        help_form = _replace_format_with_help(command)
        tokens = shlex.split(help_form)
        if tokens and tokens[0].startswith("python"):
            tokens[0] = sys.executable
        try:
            result = subprocess.run(
                tokens,
                capture_output=True,
                text=True,
                timeout=15,
            )
        except subprocess.TimeoutExpired:
            failures.append((blocker_kind, command, -1, "TIMEOUT"))
            continue
        if result.returncode != 0:
            failures.append(
                (blocker_kind, command, result.returncode, result.stderr[:300])
            )
    assert not failures, (
        "v4.43.3 (rev_pkt_4718): the following startup repair directives "
        "emit commands that DO NOT parse argparse:\n"
        + "\n".join(
            f"  - {kind}: {cmd!r} (returncode={rc}, stderr={err!r})"
            for kind, cmd, rc, err in failures
        )
    )


def test_v4_43_3_directive_command_does_not_use_unknown_target_flag() -> None:
    """v4.43.3 (rev_pkt_4718 regression): explicit check that no directive
    falls back to the old ``--target import-index-atomicity`` shape that
    codex's reproduction caught.

    v4.43.4 (rev_pkt_4720): the canonical valid entrypoint is the stable
    public shim ``dev/scripts/checks/check_startup_authority_contract.py``.
    v4.43.5 (rev_pkt_4721) updates this failure message to name the shim.
    """
    for blocker_kind, directive in _STARTUP_AUTHORITY_REPAIR_DIRECTIVES.items():
        command = directive[3]
        assert "--target import-index-atomicity" not in command, (
            f"v4.43.3: directive {blocker_kind} still uses the broken "
            f"--target import-index-atomicity flag. The valid entrypoint is "
            f"`python3 dev/scripts/checks/check_startup_authority_contract.py`."
        )


def test_v4_43_5_import_index_directive_uses_stable_shim_not_internal_module() -> None:
    """v4.43.5 (rev_pkt_4721): the ``import_index_atomicity`` repair directive
    MUST use the stable public shim path
    ``dev/scripts/checks/check_startup_authority_contract.py`` and MUST NOT
    use the internal ``dev.scripts.checks.startup_authority_contract.command``
    module form. Future fixes cannot pass while leaving stale command
    guidance behind."""
    directive = _STARTUP_AUTHORITY_REPAIR_DIRECTIVES["import_index_atomicity"]
    command = directive[3]
    assert "check_startup_authority_contract.py" in command, (
        f"v4.43.5: import_index_atomicity directive command MUST reference "
        f"the stable shim ``check_startup_authority_contract.py``. "
        f"Current command: {command!r}"
    )
    assert (
        "startup_authority_contract.command" not in command
        and "-m dev.scripts.checks" not in command
    ), (
        f"v4.43.5: import_index_atomicity directive MUST NOT use the "
        f"internal module form ``python3 -m dev.scripts.checks."
        f"startup_authority_contract.command``. The canonical AI-facing "
        f"command shape is the stable shim ``check_startup_authority_contract.py``. "
        f"Current command: {command!r}"
    )
