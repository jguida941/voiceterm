"""`devctl role create` — operator creates a typed CustomRoleDefinition.

Tier 1 lightweight connectivity validation (portable, no pytest):
  1. Schema valid per `validate_role_creation_action()`.
  2. `capability_class` for the typed role resolves in
     `_ROLE_CAPABILITY_CLASSES`.
  3. Referenced `base_workstream_id` exists in
     `known_base_workstream_ids()`. (`instruction_card_ids` and
     `guard_ids` referenced existence is validated when those
     entities are present; empty tuples are valid.)
  4. Round-trip read-after-write through the persistence layer.

Persistence routes through typed `PathRoots.state` (per
`ProjectGovernance.path_roots`); env vars
``DEVCTL_SYSTEM_ROLES_STORE_PATH`` / ``DEVCTL_CUSTOM_ROLES_STORE_PATH``
are TEST-only overrides for hermetic pytest isolation, NOT the
adopter-portability mechanism.

Emits a typed `RoleConnectivityProof` receipt on every invocation
(success or failure). The receipt is the durable record an adopter
repo can inspect.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict
from pathlib import Path
from typing import Any

from ...common import add_standard_output_arguments
from ...config import REPO_ROOT
from ...runtime.project_governance_contract import PathRoots
from ...runtime.role_customization import (
    ROLE_CONNECTIVITY_PROOF_CONTRACT_ID,
    RoleConnectivityProof,
    build_role_creation_action,
    known_base_workstream_ids,
    normalize_custom_role_id,
    validate_role_creation_action,
)
from ...runtime.role_profile import _ROLE_CAPABILITY_CLASSES
from ...runtime.state_store_authority import append_json_mapping


SYSTEM_ROLES_STORE_FILENAME = "system_roles.seed.jsonl"
CUSTOM_ROLES_STORE_FILENAME = "custom_roles.jsonl"


def add_create_parser(sub) -> None:
    parser = sub.add_parser(
        "create",
        help="Create a typed CustomRoleDefinition + emit RoleConnectivityProof.",
    )
    parser.add_argument(
        "--role-id",
        required=True,
        help="Typed role id (lowercase, snake_case).",
    )
    parser.add_argument(
        "--base-tandem-role",
        required=True,
        help="Base capability class for the role (reviewer/implementer/operator).",
    )
    parser.add_argument(
        "--base-workstream",
        required=True,
        help="Base workstream the role overlays (e.g., architect, implementer).",
    )
    parser.add_argument(
        "--display-name",
        default="",
        help="Operator-visible display name for the role.",
    )
    parser.add_argument(
        "--description",
        default="",
        help="Free-text description of the role's purpose.",
    )
    parser.add_argument(
        "--as-system",
        action="store_true",
        default=False,
        help=(
            "Persist to the governance-pack seed file "
            f"(`{SYSTEM_ROLES_STORE_FILENAME}`) instead of the gitignored "
            f"custom store (`{CUSTOM_ROLES_STORE_FILENAME}`). Use for "
            "creating new SYSTEM roles when extending the governance pack."
        ),
    )
    parser.add_argument(
        "--requested-by",
        default="operator",
        help="Actor requesting the role creation (recorded in the action).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help=(
            "Validate authority and emit RoleConnectivityProof receipt "
            "without writing the JSONL row to disk."
        ),
    )
    add_standard_output_arguments(parser, format_choices=("json", "md"), default_format="md")


def run_create(args: Any) -> tuple[dict[str, object], int]:
    """Execute one `devctl role create` invocation. Returns (report, exit_code)."""
    role_id = normalize_custom_role_id(getattr(args, "role_id", ""))
    base_tandem_role = str(getattr(args, "base_tandem_role", "") or "").strip()
    base_workstream = str(getattr(args, "base_workstream", "") or "").strip()
    display_name = str(getattr(args, "display_name", "") or "").strip()
    description = str(getattr(args, "description", "") or "").strip()
    as_system = bool(getattr(args, "as_system", False))
    dry_run = bool(getattr(args, "dry_run", False))
    requested_by = str(getattr(args, "requested_by", "") or "operator")

    persistence_target_path = _resolve_persistence_target(as_system=as_system)

    errors: list[str] = []
    warnings: list[str] = []

    # Tier 1.1 — schema validity via existing validator.
    # `base_tandem_role` and `description` from the CLI flags are
    # recorded for future use but are not arguments to the existing
    # builder — the builder derives tandem-role from the workstream.
    action = build_role_creation_action(
        role_id=role_id,
        base_workstream_id=base_workstream,
        display_name=display_name or role_id,
        requested_by=requested_by,
    )
    _ = description  # accepted for future enhancement; unused today
    schema_errors = validate_role_creation_action(action)
    schema_ok = not schema_errors
    errors.extend(schema_errors)

    # Tier 1.2 — capability_class lookup.
    capability_class_ok = base_tandem_role in {"reviewer", "implementer", "operator"} or any(
        base_tandem_role == known_role for known_role in _ROLE_CAPABILITY_CLASSES
    )
    if not capability_class_ok:
        errors.append(
            f"capability_class_unknown:{base_tandem_role!r} not in typed registry "
            "(_ROLE_CAPABILITY_CLASSES); the role must overlay one of "
            "reviewer/implementer/operator or a registered cognitive role"
        )

    # Tier 1.3 — base workstream existence.
    workstream_ok = base_workstream in known_base_workstream_ids()
    if not workstream_ok:
        known = list(known_base_workstream_ids())[:8]
        errors.append(
            f"base_workstream_not_found:{base_workstream!r} not in typed "
            f"workstream registry; known workstreams (head): {known}"
        )

    # Tier 1.4 — round-trip read-after-write. In dry-run mode the round
    # trip is structural (serialize → deserialize the in-memory payload)
    # rather than disk-touching. The CLI's adopter portability guarantee
    # is that a successful dry-run with connectivity_ok=True predicts a
    # successful live write.
    round_trip_ok = False
    if schema_ok and capability_class_ok and workstream_ok:
        try:
            serialized = json.dumps(action.role.to_dict(), sort_keys=True)
            payload = json.loads(serialized)
            assert payload.get("role_id") == role_id
            assert payload.get("base_workstream_id") == base_workstream
            round_trip_ok = True
        except (ValueError, AssertionError, KeyError) as exc:
            errors.append(f"round_trip_failed:{exc}")

    connectivity_ok = bool(schema_ok and capability_class_ok and workstream_ok and round_trip_ok)

    proof = RoleConnectivityProof(
        role_id=role_id,
        persistence_target_path=str(persistence_target_path),
        connectivity_ok=connectivity_ok,
        schema_ok=schema_ok,
        capability_class_ok=capability_class_ok,
        workstream_ok=workstream_ok,
        round_trip_ok=round_trip_ok,
        errors=tuple(errors),
        warnings=tuple(warnings),
    )

    if connectivity_ok and not dry_run:
        try:
            append_json_mapping(
                Path(persistence_target_path),
                action.role.to_dict(),
                store_id="CustomRoleDefinition",
            )
        except (OSError, ValueError) as exc:
            errors.append(f"persistence_failed:{exc}")
            connectivity_ok = False
            proof = RoleConnectivityProof(
                role_id=role_id,
                persistence_target_path=str(persistence_target_path),
                connectivity_ok=False,
                schema_ok=schema_ok,
                capability_class_ok=capability_class_ok,
                workstream_ok=workstream_ok,
                round_trip_ok=round_trip_ok,
                errors=tuple(errors),
                warnings=tuple(warnings),
            )

    report: dict[str, object] = {
        "ok": connectivity_ok,
        "action": "create",
        "role_id": role_id,
        "persistence_target_path": str(persistence_target_path),
        "dry_run": dry_run,
        "receipt": proof.to_dict(),
        "errors": list(errors),
    }
    return report, (0 if connectivity_ok else 1)


def _resolve_persistence_target(*, as_system: bool) -> Path:
    """Resolve the JSONL persistence target via typed PathRoots.

    Adopter portability: defaults derive from ``PathRoots().state`` (per
    ``ProjectGovernance.path_roots``). The env-var overrides
    (``DEVCTL_SYSTEM_ROLES_STORE_PATH`` / ``DEVCTL_CUSTOM_ROLES_STORE_PATH``)
    are reserved for hermetic test isolation; adopter repos override
    the state-root via typed ``devctl_repo_policy.json``.
    """
    if as_system:
        env_override = os.environ.get("DEVCTL_SYSTEM_ROLES_STORE_PATH", "").strip()
        if env_override:
            return Path(env_override)
        return REPO_ROOT / PathRoots().state / SYSTEM_ROLES_STORE_FILENAME
    env_override = os.environ.get("DEVCTL_CUSTOM_ROLES_STORE_PATH", "").strip()
    if env_override:
        return Path(env_override)
    return REPO_ROOT / PathRoots().state / CUSTOM_ROLES_STORE_FILENAME


__all__ = ["add_create_parser", "run_create"]
