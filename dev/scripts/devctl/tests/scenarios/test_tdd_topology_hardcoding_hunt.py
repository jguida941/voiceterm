"""TDD-discovery hunt for hardcoded provider->role topology.

Per the AntiDumbass amendment in ``delete_after_ingest.md`` (lines 731-870),
``role_id`` is the primary runtime lane field. Provider names are adapter
identities, not role authority. Specifically lines 762-770:

    Role ID is the primary runtime lane field... must never replace or hide
    the primary role ID in active topology, routing, packets, or boot-card
    output... Role ID identifies the lane; it does not grant mutation
    authority by itself. Mutation authority must still resolve from typed
    actor/session/capability grants...

The TDD-discovery role writes RED tests for this invariant first. Each test
below asserts the BEHAVIOR the system SHOULD have. A FAIL is the discovery:
codex is hardwired to reviewer somewhere, or claude is hardwired to
implementer somewhere, or both. Read-only on production code.

Hunt targets surveyed before writing these tests:

  - dev/scripts/devctl/runtime/role_topology.py
  - dev/scripts/devctl/runtime/role_profile.py
  - dev/scripts/devctl/runtime/role_customization.py
  - dev/scripts/devctl/runtime/control_topology.py
  - dev/scripts/devctl/runtime/runtime_count_roles.py
  - dev/scripts/devctl/runtime/conductor_capability.py
  - dev/scripts/devctl/runtime/topology_authority_facts.py
  - dev/scripts/devctl/runtime/agent_loop_decision_builder.py
  - dev/scripts/devctl/runtime/development_collaboration_profiles.py
  - dev/scripts/devctl/runtime/dashboard_codex_sessions.py
  - dev/scripts/devctl/review_channel/collaboration_session.py
  - dev/scripts/devctl/review_channel/bridge_projection.py
  - dev/scripts/devctl/review_channel/launch_script.py
  - dev/scripts/devctl/review_channel/prompt_support.py
  - dev/scripts/devctl/review_channel/recover_support.py
  - dev/scripts/devctl/review_channel/launch_script_watchdog.py
  - dev/scripts/devctl/runtime/control_topology_bridge_counts.py
  - dev/scripts/devctl/commands/review_channel/event_handler.py
  - dev/scripts/devctl/commands/agent_mind/peer_awareness.py
  - dev/scripts/devctl/approval_mode.py
"""

from __future__ import annotations

import ast
import json
import re
from collections.abc import Iterable
from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# Repo path resolution (this file lives 5 dirs deep under repo root)
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parents[5]

# Files under audit. Production source only (no test fixtures, no tests/).
PRODUCTION_PATHS = (
    "dev/scripts/devctl/runtime/role_topology.py",
    "dev/scripts/devctl/runtime/role_profile.py",
    "dev/scripts/devctl/runtime/role_customization.py",
    "dev/scripts/devctl/runtime/control_topology.py",
    "dev/scripts/devctl/runtime/runtime_count_roles.py",
    "dev/scripts/devctl/runtime/conductor_capability.py",
    "dev/scripts/devctl/runtime/topology_authority_facts.py",
    "dev/scripts/devctl/runtime/agent_loop_decision_builder.py",
    "dev/scripts/devctl/runtime/development_collaboration_profiles.py",
    "dev/scripts/devctl/runtime/dashboard_codex_sessions.py",
    "dev/scripts/devctl/review_channel/collaboration_session.py",
    "dev/scripts/devctl/review_channel/bridge_projection.py",
    "dev/scripts/devctl/review_channel/launch_script.py",
    "dev/scripts/devctl/review_channel/prompt_support.py",
    "dev/scripts/devctl/review_channel/recover_support.py",
    "dev/scripts/devctl/review_channel/launch_script_watchdog.py",
    "dev/scripts/devctl/runtime/control_topology_bridge_counts.py",
    "dev/scripts/devctl/commands/review_channel/event_handler.py",
    "dev/scripts/devctl/commands/agent_mind/peer_awareness.py",
    "dev/scripts/devctl/approval_mode.py",
)

REVIEW_STATE_PATH = (
    "dev/reports/review_channel/projections/latest/review_state.json"
)
AGENTS_REGISTRY_PATH = (
    "dev/reports/review_channel/projections/latest/registry/agents.json"
)

CANONICAL_ROLE_IDS = frozenset(
    {
        "reviewer",
        "implementer",
        "operator",
        "observer",
        "dashboard",
        "architect",
        "researcher",
        "intake",
        "tester",
        "plan_steward",
        "builder",
        "coder",
        "tdd_discovery",
        "tdd_first_role",
        "operator_inquiry_role",
        "governance_discovery_agent",
        "system_alignment_role",
        # cognitive role family
        "orchestrator",
        "watcher",
        "codex_research",
        "implementation",
        "architecture_review",
        "duplicate_scope_guard",
        "dogfood_test",
        "governance_receipt",
        "architecture_review",
        # operator subagent label observed in projection
        "subagent",
        "unbound",
    }
)
PROVIDER_NAMES = frozenset({"codex", "claude", "cursor", "gemini"})


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _read_text(path: str) -> str:
    return (REPO_ROOT / path).read_text(encoding="utf-8")


def _iter_production_files() -> Iterable[tuple[str, str]]:
    for relative in PRODUCTION_PATHS:
        yield relative, _read_text(relative)


def _find_provider_role_dict_literals(source: str) -> list[tuple[int, str]]:
    """Find dict literals like ``{"codex": "reviewer", "claude": "implementer"}``.

    Returns a list of (line_number, snippet) hits. Walks the AST so it
    ignores docstring prose, regex strings, and similar.
    """
    findings: list[tuple[int, str]] = []
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return findings
    role_keywords = {"reviewer", "implementer", "coder", "reviewer_only"}
    for node in ast.walk(tree):
        if not isinstance(node, ast.Dict):
            continue
        keys = []
        values = []
        for key_node, value_node in zip(node.keys, node.values):
            if isinstance(key_node, ast.Constant) and isinstance(
                key_node.value, str
            ):
                keys.append(key_node.value.lower())
            else:
                keys.append(None)
            if isinstance(value_node, ast.Constant) and isinstance(
                value_node.value, str
            ):
                values.append(value_node.value.lower())
            else:
                values.append(None)
        if None in keys or None in values:
            continue
        has_provider_key = any(k in PROVIDER_NAMES for k in keys)
        has_role_value = any(v in role_keywords for v in values)
        if has_provider_key and has_role_value:
            findings.append(
                (
                    getattr(node, "lineno", 0),
                    f"dict with provider keys {keys!r} -> role values {values!r}",
                )
            )
    return findings


def _find_provider_eq_role_branches(source: str, path: str) -> list[tuple[int, str]]:
    """Find ``if provider == "codex": ... return role`` style branches.

    Uses AST + light heuristic: an ``If`` test that compares any name ending
    in ``provider`` against a provider string literal AND a body that either
    returns / assigns a role-string literal or constructs a *RoleBinding(role=...)*.
    """
    findings: list[tuple[int, str]] = []
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return findings
    role_literals = {"reviewer", "implementer", "coder", "review_agent",
                     "coding_agent", "lead_agent", "operator_agent"}

    def name_is_provider_like(target: ast.AST) -> bool:
        if isinstance(target, ast.Name):
            return target.id.lower().endswith("provider") or target.id.lower() == "provider"
        if isinstance(target, ast.Attribute):
            return target.attr.lower().endswith("provider")
        return False

    def is_provider_string(value: ast.AST) -> str | None:
        if isinstance(value, ast.Constant) and isinstance(value.value, str):
            text = value.value.strip().lower()
            if text in PROVIDER_NAMES:
                return text
        return None

    def compare_yields_provider(test: ast.AST) -> str | None:
        # provider == "codex"
        if isinstance(test, ast.Compare) and len(test.ops) == 1 and isinstance(
            test.ops[0], ast.Eq
        ):
            left, right = test.left, test.comparators[0]
            if name_is_provider_like(left):
                provider_str = is_provider_string(right)
                if provider_str:
                    return provider_str
            if name_is_provider_like(right):
                provider_str = is_provider_string(left)
                if provider_str:
                    return provider_str
        return None

    def body_assigns_role(body_nodes: list[ast.stmt]) -> str | None:
        for stmt in body_nodes:
            for sub in ast.walk(stmt):
                if isinstance(sub, ast.Constant) and isinstance(sub.value, str):
                    if sub.value.strip().lower() in role_literals:
                        return sub.value.strip().lower()
                if isinstance(sub, ast.Call):
                    func = sub.func
                    func_name = ""
                    if isinstance(func, ast.Name):
                        func_name = func.id
                    elif isinstance(func, ast.Attribute):
                        func_name = func.attr
                    if "RoleBinding" in func_name or "RoleProfile" in func_name:
                        for kw in sub.keywords:
                            if kw.arg == "role" and isinstance(kw.value, ast.Constant):
                                if isinstance(kw.value.value, str):
                                    val = kw.value.value.strip().lower()
                                    if val in role_literals:
                                        return val
        return None

    for node in ast.walk(tree):
        if isinstance(node, ast.IfExp):
            # ternary: role="reviewer" if provider == "codex" else "implementer"
            provider_str = compare_yields_provider(node.test)
            if provider_str:
                role_then = None
                role_else = None
                if isinstance(node.body, ast.Constant) and isinstance(
                    node.body.value, str
                ):
                    val = node.body.value.strip().lower()
                    if val in role_literals:
                        role_then = val
                if isinstance(node.orelse, ast.Constant) and isinstance(
                    node.orelse.value, str
                ):
                    val = node.orelse.value.strip().lower()
                    if val in role_literals:
                        role_else = val
                if role_then or role_else:
                    findings.append(
                        (
                            getattr(node, "lineno", 0),
                            f"ternary: provider == {provider_str!r} -> "
                            f"role then={role_then!r} else={role_else!r}",
                        )
                    )
            continue
        if not isinstance(node, ast.If):
            continue
        provider_str = compare_yields_provider(node.test)
        if not provider_str:
            continue
        # Note: many `if provider == "codex":` branches are for CLI args, not
        # role assignment. We narrow with body inspection.
        role_assigned = body_assigns_role(node.body)
        if role_assigned:
            findings.append(
                (
                    getattr(node, "lineno", 0),
                    f"if provider == {provider_str!r}: ... role={role_assigned!r}",
                )
            )
    return findings


def _find_role_binding_calls_with_provider_literal(
    source: str,
) -> list[tuple[int, str]]:
    """Find direct ``RoleBinding(role=..., provider=<literal>)`` constructions.

    These are the most damaging: they hardcode a binding directly into the
    runtime topology.
    """
    findings: list[tuple[int, str]] = []
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return findings
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        func_name = ""
        if isinstance(func, ast.Name):
            func_name = func.id
        elif isinstance(func, ast.Attribute):
            func_name = func.attr
        if "RoleBinding" not in func_name and "RoleProfile" not in func_name:
            continue
        role_val: str | None = None
        provider_val: str | None = None
        for kw in node.keywords:
            if kw.arg == "role" and isinstance(kw.value, ast.Constant):
                if isinstance(kw.value.value, str):
                    role_val = kw.value.value.strip().lower()
            if kw.arg == "provider" and isinstance(kw.value, ast.Constant):
                if isinstance(kw.value.value, str):
                    provider_val = kw.value.value.strip().lower()
        if (
            role_val in {"reviewer", "implementer", "coder"}
            and provider_val in PROVIDER_NAMES
        ):
            findings.append(
                (
                    getattr(node, "lineno", 0),
                    f"{func_name}(role={role_val!r}, provider={provider_val!r})",
                )
            )
    return findings


# ---------------------------------------------------------------------------
# 1. No literal {"codex": "reviewer"}-shape dicts in production
# ---------------------------------------------------------------------------

def test_no_provider_to_role_hardcoded_dict() -> None:
    """No production file may contain a dict literal that maps a provider
    name ("codex", "claude", "cursor", "gemini") to a role string literal
    ("reviewer", "implementer", "coder", ...).

    Per AntiDumbass amendment lines 762-766: role assignments must come
    from typed actor/session/capability state, never from a hardcoded
    provider->role table.
    """
    violations: list[str] = []
    for relative, source in _iter_production_files():
        for lineno, snippet in _find_provider_role_dict_literals(source):
            violations.append(f"{relative}:{lineno}: {snippet}")
    assert not violations, (
        "Hardcoded provider->role dict literals found:\n  "
        + "\n  ".join(violations)
    )


# ---------------------------------------------------------------------------
# 2. No `if provider == "codex": ... role = ...` branches
# ---------------------------------------------------------------------------

def test_no_provider_string_in_role_inference() -> None:
    """No production file may infer a role/lane assignment from a provider
    string equality check.

    Patterns covered:
      - ``if provider == "codex": ... role = "reviewer"``
      - ``role = "reviewer" if provider == "codex" else "implementer"``
      - ``RoleBinding(role="reviewer") inside if provider == "codex"``
    """
    violations: list[str] = []
    for relative, source in _iter_production_files():
        for lineno, snippet in _find_provider_eq_role_branches(source, relative):
            violations.append(f"{relative}:{lineno}: {snippet}")
    assert not violations, (
        "provider-string -> role-string inference branches found:\n  "
        + "\n  ".join(violations)
    )


# ---------------------------------------------------------------------------
# 3. role_for_provider must consult typed state, never grant role authority
# ---------------------------------------------------------------------------

def test_role_for_provider_function_does_not_use_hardcoded_default() -> None:
    """``role_for_provider()`` must return ``None`` for every adapter provider
    name without a typed map argument.

    Per role_profile.py: ``DEFAULT_PROVIDER_ROLE_MAP: dict[str, TandemRole] = {}``
    is documented as "Provider names are adapter identities, not role authority.
    Callers that need a provider-to-role mapping must pass a typed map derived
    from session/topology state. An empty default makes provider-only inputs
    fail closed."

    The function must NOT have been re-wired to a non-empty default since.
    """
    import sys
    sys.path.insert(0, str(REPO_ROOT / "dev" / "scripts"))
    from devctl.runtime.role_profile import (
        DEFAULT_PROVIDER_ROLE_MAP,
        default_provider_for_role,
        role_for_provider,
    )

    assert DEFAULT_PROVIDER_ROLE_MAP == {}, (
        f"DEFAULT_PROVIDER_ROLE_MAP must stay empty; got {DEFAULT_PROVIDER_ROLE_MAP!r}"
    )
    for provider in ("codex", "claude", "cursor", "gemini", "future-agent"):
        assert role_for_provider(provider) is None, (
            f"role_for_provider({provider!r}) must return None without typed map; "
            f"got {role_for_provider(provider)!r}"
        )
    for role in ("reviewer", "implementer", "operator"):
        assert default_provider_for_role(role) == "", (
            f"default_provider_for_role({role!r}) must return '' without typed map; "
            f"got {default_provider_for_role(role)!r}"
        )


# ---------------------------------------------------------------------------
# 4. AgentLoopDecision builder must take role from context, not provider
# ---------------------------------------------------------------------------

def test_agent_loop_decision_builder_does_not_default_role_from_provider() -> None:
    """The AgentLoopDecision builder's primary ``decision()`` entrypoint must
    set ``actor_role`` from the typed context's ``role`` field, never from a
    provider-name inference.
    """
    source = _read_text(
        "dev/scripts/devctl/runtime/agent_loop_decision_builder.py"
    )
    tree = ast.parse(source)
    decision_fn = next(
        (
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef) and node.name == "decision"
        ),
        None,
    )
    assert decision_fn is not None, "decision() not found in agent_loop_decision_builder"
    # No provider-string -> role-string branches inside the function body.
    fn_src = ast.get_source_segment(source, decision_fn) or ""
    pattern = re.compile(
        r"""(provider\s*==\s*["'](codex|claude|cursor|gemini)["']"""
        r"""|["'](codex|claude|cursor|gemini)["']\s*==\s*provider)""",
        re.IGNORECASE,
    )
    matches = pattern.findall(fn_src)
    assert not matches, (
        "decision() must not branch on provider-name equality for role inference; "
        f"matches: {matches!r}"
    )
    # actor_role must be sourced from ctx.role (the typed context input).
    assert "actor_role=ctx.role" in fn_src, (
        "decision() must set actor_role from ctx.role (typed session role); "
        "if this assertion fires, role is now sourced from a different field."
    )


# ---------------------------------------------------------------------------
# 5. TandemRole is capability metadata, not the primary role_id
# ---------------------------------------------------------------------------

def test_tandem_role_enum_is_capability_metadata_not_primary_role() -> None:
    """``TandemRole`` is documented in role_profile.py as a "capability class"
    used by older tandem-loop guards. Per AntiDumbass amendment lines 762-766,
    primary role_id must remain a typed string, NOT the legacy 3-valued
    capability enum.

    Invariant: ``RoleOccupancy.role_id`` (in role_topology.py) must be typed
    as ``str``, NOT ``TandemRole``. Same for the AgentLoopDecision ``actor_role``
    field.
    """
    role_topology_src = _read_text(
        "dev/scripts/devctl/runtime/role_topology.py"
    )
    tree = ast.parse(role_topology_src)
    occupancy = next(
        (
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.ClassDef) and node.name == "RoleOccupancy"
        ),
        None,
    )
    assert occupancy is not None, "RoleOccupancy class not found"
    role_id_field = next(
        (
            stmt
            for stmt in occupancy.body
            if isinstance(stmt, ast.AnnAssign)
            and isinstance(stmt.target, ast.Name)
            and stmt.target.id == "role_id"
        ),
        None,
    )
    assert role_id_field is not None, "RoleOccupancy.role_id field not found"
    annotation_src = ast.unparse(role_id_field.annotation)
    assert "TandemRole" not in annotation_src, (
        f"RoleOccupancy.role_id must be typed as `str`, not TandemRole; "
        f"actual: {annotation_src!r}. TandemRole is capability metadata only."
    )
    # role_profile.py must document TandemRole as capability metadata.
    role_profile_src = _read_text("dev/scripts/devctl/runtime/role_profile.py")
    tree2 = ast.parse(role_profile_src)
    tandem_cls = next(
        (
            node
            for node in ast.walk(tree2)
            if isinstance(node, ast.ClassDef) and node.name == "TandemRole"
        ),
        None,
    )
    assert tandem_cls is not None, "TandemRole class not found"
    doc = ast.get_docstring(tandem_cls) or ""
    assert "capability" in doc.lower() or "legacy" in doc.lower() or "tandem" in doc.lower(), (
        f"TandemRole docstring should mark it as capability/legacy/tandem "
        f"metadata; got: {doc!r}"
    )


# ---------------------------------------------------------------------------
# 6. Collaboration session role assignment must read typed session input
# ---------------------------------------------------------------------------

def test_collaboration_session_role_assignment_reads_typed_session() -> None:
    """``build_collaboration_session`` and ``_build_role_assignments`` must NOT
    have any provider-name equality branches that set the typed role.

    The typed role must come from ``session_records[*].role`` and the
    typed bridge-liveness role_assignments, not from
    ``if provider == "claude": role = "implementer"``.
    """
    paths = (
        "dev/scripts/devctl/review_channel/collaboration_session.py",
        "dev/scripts/devctl/review_channel/collaboration_session_roster.py",
        "dev/scripts/devctl/review_channel/collaboration_session_presence.py",
        "dev/scripts/devctl/review_channel/collaboration_session_roster_resolution.py",
        "dev/scripts/devctl/review_channel/collaboration_session_roster_lookup.py",
        "dev/scripts/devctl/review_channel/collaboration_session_roster_projection.py",
    )
    violations: list[str] = []
    for relative in paths:
        full = REPO_ROOT / relative
        if not full.exists():
            continue
        source = full.read_text(encoding="utf-8")
        for lineno, snippet in _find_provider_eq_role_branches(source, relative):
            violations.append(f"{relative}:{lineno}: {snippet}")
        for lineno, snippet in _find_role_binding_calls_with_provider_literal(
            source
        ):
            violations.append(
                f"{relative}:{lineno}: hardcoded RoleBinding {snippet}"
            )
    assert not violations, (
        "collaboration session role assignment uses provider-string inference:\n  "
        + "\n  ".join(violations)
    )


# ---------------------------------------------------------------------------
# 7. default_provider_for_role usage must be advisory-only
# ---------------------------------------------------------------------------

def test_default_provider_for_role_is_advisory_only() -> None:
    """``default_provider_for_role()`` may appear in production code only as
    an inverse advisory hint (e.g. fallback display name, telemetry).

    It must NOT be used as the authority that ASSIGNS a role to a provider.
    Specifically, no production file may pass its return value as the
    ``role=`` argument to a typed authority constructor (RoleBinding,
    RoleProfile, CollaborationRoleBinding, RoleOccupancy).
    """
    # First confirm DEFAULT_PROVIDER_ROLE_MAP is empty (defended by test 3).
    # Then statically scan callers for misuse: ``role=default_provider_for_role(...)``
    # would be the dangerous pattern (it's nonsense semantically, but we
    # check structure not semantics).
    misuse: list[str] = []
    for relative, source in _iter_production_files():
        try:
            tree = ast.parse(source)
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            for kw in node.keywords:
                if kw.arg != "role":
                    continue
                if not isinstance(kw.value, ast.Call):
                    continue
                inner = kw.value.func
                inner_name = ""
                if isinstance(inner, ast.Name):
                    inner_name = inner.id
                elif isinstance(inner, ast.Attribute):
                    inner_name = inner.attr
                if inner_name == "default_provider_for_role":
                    misuse.append(
                        f"{relative}:{getattr(node, 'lineno', 0)}: role=default_provider_for_role(...) misuse"
                    )
    assert not misuse, (
        "default_provider_for_role() used as role-assignment authority:\n  "
        + "\n  ".join(misuse)
    )


# ---------------------------------------------------------------------------
# 8. review_state.json role fields must be typed role_ids, not provider names
# ---------------------------------------------------------------------------

def test_no_provider_name_in_review_state_role_field() -> None:
    """In the latest review-channel projection, every ``role`` / ``role_id`` /
    ``actor_role`` / ``target_role`` / ``role_preset`` field must hold a typed
    role id (e.g. ``reviewer``, ``implementer``, ``architecture_review``,
    ``observer``), never a provider name (``codex``, ``claude``, ``cursor``).

    A provider name leaking into a role field means downstream consumers will
    treat the provider identity as the lane.
    """
    state_path = REPO_ROOT / REVIEW_STATE_PATH
    if not state_path.exists():
        pytest.skip(f"projection missing: {REVIEW_STATE_PATH}")
    data = json.loads(state_path.read_text(encoding="utf-8"))
    leaks: list[str] = []

    def scan(obj, path: str) -> None:
        if isinstance(obj, dict):
            for key, value in obj.items():
                next_path = f"{path}/{key}"
                if key in {"role", "role_id", "actor_role", "target_role",
                          "role_preset", "base_tandem_role"}:
                    if isinstance(value, str):
                        v = value.strip().lower()
                        if v in PROVIDER_NAMES:
                            leaks.append(f"{next_path}={value}")
                scan(value, next_path)
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                scan(item, f"{path}[{i}]")

    scan(data, "")
    assert not leaks, (
        "provider names leaked into role fields of review_state.json:\n  "
        + "\n  ".join(leaks)
    )


# ---------------------------------------------------------------------------
# 9. Agent registry projection must not collapse role to provider name
# ---------------------------------------------------------------------------

def test_agents_registry_lane_title_matches_typed_role() -> None:
    """The agent registry projection writes ``lane_title`` per agent. When a
    ``current_job`` carries a typed role id like ``architecture_review`` or
    ``implementation``, the ``lane_title`` must reflect that role's capability
    class (e.g. ``Reviewer`` / ``Implementer``), not a stale provider-derived
    string.

    More importantly, the registry ``lane`` field must NOT be the only
    visible role evidence; ``current_job`` must surface the typed role.
    """
    registry_path = REPO_ROOT / AGENTS_REGISTRY_PATH
    if not registry_path.exists():
        pytest.skip(f"registry projection missing: {AGENTS_REGISTRY_PATH}")
    data = json.loads(registry_path.read_text(encoding="utf-8"))
    agents = data.get("agents") if isinstance(data, dict) else None
    assert isinstance(agents, list) and agents, "agents.json has no agents"
    # For each non-operator agent, current_job must be a typed role id.
    bad_jobs: list[str] = []
    for entry in agents:
        if not isinstance(entry, dict):
            continue
        provider = str(entry.get("provider") or "").strip().lower()
        if provider == "operator":
            continue
        current_job = str(entry.get("current_job") or "").strip().lower()
        if current_job not in CANONICAL_ROLE_IDS:
            bad_jobs.append(
                f"agent_id={entry.get('agent_id')} provider={provider} "
                f"current_job={current_job!r}"
            )
    assert not bad_jobs, (
        "agents.json carries non-typed current_job (likely provider name leak):\n  "
        + "\n  ".join(bad_jobs)
    )


# ---------------------------------------------------------------------------
# 10. Direct CollaborationRoleBinding literals with provider-pair defaults
# ---------------------------------------------------------------------------

def test_no_collaboration_role_binding_default_provider_pair() -> None:
    """``CollaborationRoleBinding(role="reviewer", provider="codex")`` and
    ``CollaborationRoleBinding(role="implementer", provider="claude")`` are
    explicit hardcoded mappings.

    Per the amendment, the default binding pair must come from typed
    session/topology state, not be wired into a source-file fallback.
    """
    violations: list[str] = []
    for relative, source in _iter_production_files():
        for lineno, snippet in _find_role_binding_calls_with_provider_literal(
            source
        ):
            violations.append(f"{relative}:{lineno}: {snippet}")
    assert not violations, (
        "Hardcoded RoleBinding/RoleProfile(role=..., provider=...) calls found:\n  "
        + "\n  ".join(violations)
    )


# ---------------------------------------------------------------------------
# 11. Cascade lifecycle enforcement must not key on hardcoded provider->role
# ---------------------------------------------------------------------------

def test_cascade_lifecycle_does_not_use_hardcoded_provider_role_map() -> None:
    """``event_handler.py`` enforces "cascade closure" target_role against a
    parent's from_agent (provider). Per AntiDumbass amendment, the expected
    target_role for a parent packet must come from typed session/role state,
    NOT a literal dict ``{"claude": "implementer", "codex": "reviewer"}``.
    """
    source = _read_text(
        "dev/scripts/devctl/commands/review_channel/event_handler.py"
    )
    tree = ast.parse(source)
    # Look for any module-level constant (Assign or AnnAssign) whose value is
    # a dict that maps provider names to role strings.
    violations: list[str] = []
    for node in ast.walk(tree):
        name = ""
        value = None
        if isinstance(node, ast.Assign):
            if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
                name = node.targets[0].id
                value = node.value
        elif isinstance(node, ast.AnnAssign):
            if isinstance(node.target, ast.Name) and node.value is not None:
                name = node.target.id
                value = node.value
        if not name or not isinstance(value, ast.Dict):
            continue
        pairs = []
        for k, v in zip(value.keys, value.values):
            if isinstance(k, ast.Constant) and isinstance(v, ast.Constant):
                pairs.append((k.value, v.value))
        if not pairs:
            continue
        has_provider_key = any(
            isinstance(k, str) and k.strip().lower() in PROVIDER_NAMES
            for k, _ in pairs
        )
        has_role_value = any(
            isinstance(v, str)
            and v.strip().lower() in {"reviewer", "implementer", "coder"}
            for _, v in pairs
        )
        if has_provider_key and has_role_value:
            violations.append(
                f"event_handler.py:{node.lineno}: {name} = {pairs!r}"
            )
    assert not violations, (
        "cascade lifecycle keys target_role on a hardcoded provider->role dict:\n  "
        + "\n  ".join(violations)
    )


# ---------------------------------------------------------------------------
# 12. peer awareness peer_provider fallback must not chain codex<->claude
# ---------------------------------------------------------------------------

def test_peer_awareness_default_peer_is_not_provider_pair_hardcoded() -> None:
    """``commands/agent_mind/peer_awareness.py:_default_peer_provider`` returns
    "claude" when called with "codex" and vice versa, with a hardcoded
    fallback to "codex" when called with any other provider. This collapses
    the multi-agent topology back to a two-provider assumption.

    A typed peer-awareness reducer must read the active topology
    (CollaborationSessionState) to find the peer provider, not assume codex
    and claude are the only two participants.
    """
    source = _read_text(
        "dev/scripts/devctl/commands/agent_mind/peer_awareness.py"
    )
    tree = ast.parse(source)
    target = next(
        (
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.FunctionDef)
            and node.name == "_default_peer_provider"
        ),
        None,
    )
    assert target is not None, "_default_peer_provider not found"
    fn_src = ast.get_source_segment(source, target) or ""
    # The current implementation has a hardcoded chain. We assert it does NOT
    # have one — failure = discovery.
    branch_pattern = re.compile(
        r"""provider\s*==\s*["'](codex|claude)["']""",
        re.IGNORECASE,
    )
    matches = branch_pattern.findall(fn_src)
    assert not matches, (
        f"_default_peer_provider has hardcoded provider-pair fallback; "
        f"branches: {matches!r}. Peer provider must come from typed topology."
    )


# ---------------------------------------------------------------------------
# 13. bridge_role_counts must not key reviewer/implementer totals on provider
# ---------------------------------------------------------------------------

def test_bridge_role_counts_does_not_use_provider_name_literals() -> None:
    """``runtime/control_topology_bridge_counts.py`` must not assign reviewer
    or implementer totals from ``provider == "codex"`` or
    ``provider == "claude"`` literals.

    Earlier hunt tests (#1 and #2) walked AST ``if`` branches and dict
    literals, which missed the generator-expression form
    ``sum(1 for provider in normalized if provider == "codex")`` that lived
    inside ``bridge_role_counts``. That form is the same
    ``provider -> role`` hardcoding pattern the AntiDumbass amendment
    forbids (delete_after_ingest.md:731-870): reviewer/implementer role
    totals must come from typed role evidence (session_liveness_signals
    role field, collaboration role_assignments, role-topology resolution),
    never from a provider-name equality check.

    A future reintroduction of those literals in this file fails this
    test closed.
    """
    source = _read_text(
        "dev/scripts/devctl/runtime/control_topology_bridge_counts.py"
    )
    tree = ast.parse(source)

    def is_provider_string_literal(node: ast.AST) -> str | None:
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            text = node.value.strip().lower()
            if text in PROVIDER_NAMES:
                return text
        return None

    def name_is_provider_like(node: ast.AST) -> bool:
        if isinstance(node, ast.Name):
            return node.id.lower() == "provider" or node.id.lower().endswith(
                "provider"
            )
        if isinstance(node, ast.Attribute):
            return node.attr.lower().endswith("provider")
        return False

    matches: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Compare):
            continue
        if not (len(node.ops) == 1 and isinstance(node.ops[0], ast.Eq)):
            continue
        left, right = node.left, node.comparators[0]
        provider_value: str | None = None
        if name_is_provider_like(left):
            provider_value = is_provider_string_literal(right)
        if provider_value is None and name_is_provider_like(right):
            provider_value = is_provider_string_literal(left)
        if provider_value is None:
            continue
        matches.append(
            (getattr(node, "lineno", 0), f"provider == {provider_value!r}")
        )
    assert not matches, (
        "control_topology_bridge_counts.py contains provider-name equality "
        "checks that gate reviewer/implementer role counts; role totals "
        "must resolve from typed role topology (resolve_role_topology / "
        "live_session_role_counts), not provider-name literals:\n  "
        + "\n  ".join(
            f"line {lineno}: {snippet}" for lineno, snippet in matches
        )
    )
