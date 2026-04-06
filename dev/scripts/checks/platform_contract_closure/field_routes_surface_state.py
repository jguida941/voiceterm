"""Surface-state field-route closure proofs for platform contract enforcement.

Each check verifies that a key field from a surface-state contract
(ControlPlaneReadModel, AutoModeState, SessionCachePacket) is consumed
in the declared target surface renderer by inspecting the actual
source code for field-access references.

Field-route proof must reflect *executable* consumption: identifier or
attribute access, dotted attribute chains, or string-literal keys used
in code. References that appear only in module, class, or function
docstrings (or in comments) are excluded, because a docstring mention
does not prove that the renderer actually reads the field at runtime.
"""

from __future__ import annotations

import ast
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]


def _source_contains_any(module_path: str, tokens: tuple[str, ...]) -> bool:
    """Return True when non-docstring code at *module_path* references any token.

    Resolves dotted module paths to filesystem paths relative to the
    repo root. Accepts both flat modules (``foo/bar.py``) and packages
    (``foo/bar/__init__.py``); for packages, scans every ``*.py`` file
    in the package root so tokens rendered by submodules still count.
    Executable match is required: a token that appears only in a module,
    class, or function docstring does not satisfy the field-route proof.
    """
    rel_module = module_path.replace(".", "/")
    flat_path = _REPO_ROOT / f"{rel_module}.py"
    if flat_path.is_file():
        return _file_references_any(flat_path, tokens)

    package_dir = _REPO_ROOT / rel_module
    if package_dir.is_dir():
        for py_file in sorted(package_dir.glob("*.py")):
            if _file_references_any(py_file, tokens):
                return True
    return False


def _file_references_any(path: Path, tokens: tuple[str, ...]) -> bool:
    """Return True if *path* has an executable (non-docstring) reference to any token.

    Parses the file as Python AST, strips module/class/function docstrings,
    and walks the remaining tree looking for:

    - ``ast.Name`` nodes whose ``id`` matches a token (bare identifier use),
    - ``ast.Attribute`` nodes whose ``attr`` matches a token (``obj.field``),
    - ``ast.Attribute`` nodes whose reconstructed dotted chain matches a
      dotted token (``auto_state.phase``),
    - ``ast.Constant`` string values equal to a token (``d["field"]`` /
      ``d.get("field", ...)``).

    Returns False if the file cannot be parsed as valid Python. This is a
    fail-closed default: an unparseable consumer cannot prove field-route
    closure, and the caller should treat it as a missing reference rather
    than falling back to raw-text scanning.
    """
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(text)
    except (SyntaxError, ValueError):
        return False

    _strip_docstrings(tree)
    token_set = set(tokens)

    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            if node.id in token_set:
                return True
        elif isinstance(node, ast.Attribute):
            if node.attr in token_set:
                return True
            dotted = _dotted_attribute(node)
            if dotted is not None and dotted in token_set:
                return True
        elif isinstance(node, ast.Constant):
            value = node.value
            if isinstance(value, str) and value in token_set:
                return True
    return False


def _strip_docstrings(tree: ast.AST) -> None:
    """Drop module/class/function docstrings from *tree* in-place.

    A docstring is the first statement of a module, class, or function body
    when that statement is an ``ast.Expr`` wrapping a string ``ast.Constant``.
    Removing it before the reference walk means a field name that appears
    only in documentation does not count as executable consumption.
    """
    for node in ast.walk(tree):
        if isinstance(
            node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
        ):
            body = node.body
            if (
                body
                and isinstance(body[0], ast.Expr)
                and isinstance(body[0].value, ast.Constant)
                and isinstance(body[0].value.value, str)
            ):
                body.pop(0)


def _dotted_attribute(node: ast.Attribute) -> str | None:
    """Reconstruct a dotted attribute chain such as ``a.b.c`` from nested nodes.

    Returns the dotted string when the chain terminates in an ``ast.Name``
    (for example ``auto_state.phase`` for ``Attribute(attr='phase',
    value=Name('auto_state'))``). Returns ``None`` for subscripts, calls, or
    any non-name root so the caller falls back to the shallower ``node.attr``
    match rather than treating arbitrary expressions as dotted paths.
    """
    parts: list[str] = [node.attr]
    current: ast.AST = node.value
    while isinstance(current, ast.Attribute):
        parts.append(current.attr)
        current = current.value
    if isinstance(current, ast.Name):
        parts.append(current.id)
        return ".".join(reversed(parts))
    return None


def _build_coverage(
    contract_id: str,
    field_name: str,
    route_id: str,
    consumer: str,
) -> dict[str, object]:
    return {
        "kind": "field_route",
        "contract_id": contract_id,
        "field_name": field_name,
        "route_id": route_id,
        "consumer": consumer,
        "ok": True,
    }


def _build_violation(
    coverage: dict[str, object],
    detail: str,
) -> dict[str, object]:
    return {
        "kind": "field_route",
        "contract_id": coverage["contract_id"],
        "field_name": coverage["field_name"],
        "route_id": coverage["route_id"],
        "rule": "unconsumed-field-route",
        "detail": detail,
    }


# -- ControlPlaneReadModel.push_eligible routes --

def check_push_eligible_dashboard_route() -> tuple[dict[str, object], dict[str, object] | None]:
    """Verify ControlPlaneReadModel.push_eligible reaches the dashboard.

    ``ControlPlaneReadModel.push_eligible`` is the source-of-truth field,
    but the dashboard builder consumes it through the receipt projection
    ``push_eligible_now``, which carries the same resolved truth under a
    renamed key. Both token forms are accepted here so the field-route
    proof matches either the dataclass field or its receipt projection
    via exact AST reference rather than a raw-text substring coincidence.
    """
    consumer = "dev.scripts.devctl.commands.dashboard_builders"
    coverage = _build_coverage(
        "ControlPlaneReadModel", "push_eligible", "dashboard", consumer,
    )
    if _source_contains_any(consumer, ("push_eligible", "push_eligible_now")):
        coverage["detail"] = (
            "ControlPlaneReadModel.push_eligible is referenced in the "
            "dashboard builder surface through the push_eligible_now "
            "receipt projection."
        )
        return coverage, None
    detail = (
        "ControlPlaneReadModel.push_eligible is not referenced in the "
        "dashboard builder surface."
    )
    coverage["ok"] = False
    coverage["detail"] = detail
    return coverage, _build_violation(coverage, detail)


def check_push_eligible_session_resume_route() -> tuple[dict[str, object], dict[str, object] | None]:
    """Verify ControlPlaneReadModel.push_eligible reaches session-resume."""
    # push_eligible flows into ControlPlaneReadModel.next_command
    # (set to devctl push --execute when push_eligible is True),
    # and session-resume consumes model.next_command.
    consumer = "dev.scripts.devctl.commands.governance.session_resume_support"
    model = "dev.scripts.devctl.runtime.control_plane_read_model"
    coverage = _build_coverage(
        "ControlPlaneReadModel", "push_eligible", "session_resume", consumer,
    )
    if (
        _source_contains_any(model, ("push_eligible",))
        and _source_contains_any(consumer, ("next_command", "next_action"))
    ):
        coverage["detail"] = (
            "ControlPlaneReadModel.push_eligible flows into next_command, "
            "which session-resume consumes from the read model."
        )
        return coverage, None
    detail = (
        "ControlPlaneReadModel.push_eligible does not reach the "
        "session-resume surface through the next_command projection."
    )
    coverage["ok"] = False
    coverage["detail"] = detail
    return coverage, _build_violation(coverage, detail)


# -- ControlPlaneReadModel.top_blocker routes --

def check_top_blocker_dashboard_route() -> tuple[dict[str, object], dict[str, object] | None]:
    """Verify ControlPlaneReadModel.top_blocker reaches the dashboard."""
    consumer = "dev.scripts.devctl.commands.dashboard_render"
    coverage = _build_coverage(
        "ControlPlaneReadModel", "top_blocker", "dashboard", consumer,
    )
    if _source_contains_any(consumer, ("top_blocker",)):
        coverage["detail"] = (
            "ControlPlaneReadModel.top_blocker is referenced in the "
            "dashboard render surface."
        )
        return coverage, None
    detail = (
        "ControlPlaneReadModel.top_blocker is not referenced in the "
        "dashboard render surface."
    )
    coverage["ok"] = False
    coverage["detail"] = detail
    return coverage, _build_violation(coverage, detail)


def check_top_blocker_session_resume_route() -> tuple[dict[str, object], dict[str, object] | None]:
    """Verify ControlPlaneReadModel.top_blocker reaches session-resume."""
    consumer = "dev.scripts.devctl.commands.governance.session_resume_support"
    coverage = _build_coverage(
        "ControlPlaneReadModel", "top_blocker", "session_resume", consumer,
    )
    if _source_contains_any(consumer, ("top_blocker",)):
        coverage["detail"] = (
            "ControlPlaneReadModel.top_blocker is referenced in the "
            "session-resume support surface."
        )
        return coverage, None
    detail = (
        "ControlPlaneReadModel.top_blocker is not referenced in the "
        "session-resume support surface."
    )
    coverage["ok"] = False
    coverage["detail"] = detail
    return coverage, _build_violation(coverage, detail)


def check_top_blocker_phone_route() -> tuple[dict[str, object], dict[str, object] | None]:
    """Verify ControlPlaneReadModel.top_blocker reaches the phone surface."""
    consumer = "dev.scripts.devctl.commands.phone_status"
    coverage = _build_coverage(
        "ControlPlaneReadModel", "top_blocker", "phone", consumer,
    )
    if _source_contains_any(consumer, ("top_blocker",)):
        coverage["detail"] = (
            "ControlPlaneReadModel.top_blocker is referenced in the "
            "phone status surface."
        )
        return coverage, None
    detail = (
        "ControlPlaneReadModel.top_blocker is not referenced in the "
        "phone status surface."
    )
    coverage["ok"] = False
    coverage["detail"] = detail
    return coverage, _build_violation(coverage, detail)


# -- AutoModeState.phase routes --

def check_auto_mode_phase_session_resume_route() -> tuple[dict[str, object], dict[str, object] | None]:
    """Verify AutoModeState.phase reaches session-resume via resolved_phase.

    AutoModeState.phase flows into ControlPlaneReadModel.resolved_phase
    via ``auto_state.phase`` in the read-model builder.  The closure proof
    requires that ``resolved_phase`` is present as a field in
    SessionCachePacket AND that the session-resume renderer outputs it.
    """
    model = "dev.scripts.devctl.runtime.control_plane_read_model"
    consumer = "dev.scripts.devctl.commands.governance.session_resume_support"
    renderer = "dev.scripts.devctl.commands.governance.session_resume_render"
    coverage = _build_coverage("AutoModeState", "phase", "session_resume", consumer)
    if (
        _source_contains_any(model, ("auto_state.phase", "resolved_phase"))
        and _source_contains_any(consumer, ("resolved_phase",))
        and _source_contains_any(renderer, ("resolved_phase",))
    ):
        coverage["detail"] = (
            "AutoModeState.phase flows through ControlPlaneReadModel.resolved_phase "
            "into SessionCachePacket.resolved_phase and the session-resume renderer."
        )
        return coverage, None
    detail = (
        "AutoModeState.phase does not reach the session-resume surface "
        "through the resolved_phase projection in SessionCachePacket and "
        "the renderer."
    )
    coverage["ok"] = False
    coverage["detail"] = detail
    return coverage, _build_violation(coverage, detail)


# -- SessionCachePacket.last_reviewed_sha routes --

def check_last_reviewed_sha_compact_route() -> tuple[dict[str, object], dict[str, object] | None]:
    """Verify SessionCachePacket.last_reviewed_sha reaches compact projection."""
    consumer = "dev.scripts.devctl.commands.governance.session_resume_support"
    coverage = _build_coverage(
        "SessionCachePacket", "last_reviewed_sha", "compact_projection", consumer,
    )
    if _source_contains_any(consumer, ("last_reviewed_sha",)):
        coverage["detail"] = (
            "SessionCachePacket.last_reviewed_sha is referenced in the "
            "session-resume compact projection surface."
        )
        return coverage, None
    detail = (
        "SessionCachePacket.last_reviewed_sha is not referenced in the "
        "session-resume compact projection surface."
    )
    coverage["ok"] = False
    coverage["detail"] = detail
    return coverage, _build_violation(coverage, detail)
