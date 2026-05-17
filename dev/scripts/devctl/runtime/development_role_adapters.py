"""Provider-neutral role adapter commands for ``/develop`` surfaces."""

from __future__ import annotations

from dataclasses import asdict, dataclass

from .development_collaboration_modes import build_default_collaboration_mode_topology

SUPPORTED_DEVELOP_ROLE_ADAPTER_PROVIDERS = ("codex", "claude")

DEFAULT_ROLE_COLLABORATION_MODES = (
    ("dashboard", "dashboard_led"),
    ("implementer", "pair_review"),
    ("reviewer", "pair_review"),
    ("architect", "research_fanout"),
    ("researcher", "research_fanout"),
    ("intake", "intake_fanout"),
    ("tester", "review_fanout"),
    ("watcher", "watcher_fanout"),
    ("operator", "dashboard_led"),
)


@dataclass(frozen=True, slots=True)
class DevelopRoleAdapterSpec:
    """One provider-facing adapter over the shared ``/develop`` request model."""

    provider_id: str
    role_preset: str
    collaboration_mode: str
    adapter_command: str
    authority_source: str = "CollaborationModeTopology"
    backend_surface: str = "devctl develop"

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


def develop_role_adapter_command(
    *,
    provider_id: str,
    role_preset: str,
    collaboration_mode: str = "",
    extra_args: str = "$ARGUMENTS",
) -> str:
    """Return the typed ``devctl develop`` command for one provider role."""
    provider = _safe_token(provider_id, field_name="provider_id")
    role = _known_role(role_preset)
    mode = _known_mode(collaboration_mode or default_mode_for_role(role))
    suffix = str(extra_args or "").strip()
    command = (
        "python3 dev/scripts/devctl.py develop "
        f"--actor {provider} --role-preset {role} --collaboration-mode {mode}"
    )
    if suffix:
        command = f"{command} {suffix}"
    return command


def build_develop_role_adapter_matrix(
    *,
    providers: tuple[str, ...] = SUPPORTED_DEVELOP_ROLE_ADAPTER_PROVIDERS,
    extra_args: str = "$ARGUMENTS",
) -> tuple[DevelopRoleAdapterSpec, ...]:
    """Return role adapter commands for each provider from one shared map."""
    topology = build_default_collaboration_mode_topology()
    rows: list[DevelopRoleAdapterSpec] = []
    for provider_id in providers:
        provider = _safe_token(provider_id, field_name="provider_id")
        for role in topology.role_presets:
            mode = default_mode_for_role(role.preset_id)
            rows.append(
                DevelopRoleAdapterSpec(
                    provider_id=provider,
                    role_preset=role.preset_id,
                    collaboration_mode=mode,
                    adapter_command=develop_role_adapter_command(
                        provider_id=provider,
                        role_preset=role.preset_id,
                        collaboration_mode=mode,
                        extra_args=extra_args,
                    ),
                )
            )
    return tuple(rows)


def render_develop_role_adapter_matrix_markdown(
    *,
    providers: tuple[str, ...] = SUPPORTED_DEVELOP_ROLE_ADAPTER_PROVIDERS,
) -> str:
    """Render a compact provider-neutral slash-adapter catalog."""
    rows = build_develop_role_adapter_matrix(providers=providers)
    by_provider = {provider: [] for provider in providers}
    for row in rows:
        by_provider.setdefault(row.provider_id, []).append(row)

    lines = [
        "Provider-neutral role adapter catalog.",
        "",
        "Canonical source: `CollaborationModeTopology` plus "
        "`development_role_adapters.py`.",
        "Codex and Claude consume the same role-to-mode map; provider slash "
        "files are thin adapters only.",
    ]
    for provider, provider_rows in by_provider.items():
        lines.extend(["", f"## {provider}", ""])
        for row in provider_rows:
            lines.append(
                f"- `{row.role_preset}` -> `{row.adapter_command}`"
            )
    return "\n".join(lines)


def default_mode_for_role(role_preset: str) -> str:
    """Return the default collaboration mode for one role preset."""
    role = _known_role(role_preset)
    for known_role, mode in DEFAULT_ROLE_COLLABORATION_MODES:
        if known_role == role:
            return mode
    raise ValueError(f"role preset `{role}` has no default collaboration mode")


def _known_role(value: str) -> str:
    role = _safe_token(value, field_name="role_preset")
    topology = build_default_collaboration_mode_topology()
    known = {item.preset_id for item in topology.role_presets}
    if role not in known:
        raise ValueError(f"unknown role preset `{role}`")
    return role


def _known_mode(value: str) -> str:
    mode = _safe_token(value, field_name="collaboration_mode")
    topology = build_default_collaboration_mode_topology()
    known = {item.mode_id for item in topology.modes}
    if mode not in known:
        raise ValueError(f"unknown collaboration mode `{mode}`")
    return mode


def _safe_token(value: str, *, field_name: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"{field_name} is required")
    normalized = text.replace("_", "").replace("-", "")
    if not normalized.isalnum():
        raise ValueError(f"{field_name} contains unsupported characters")
    return text
