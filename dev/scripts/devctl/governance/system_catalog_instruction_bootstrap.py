"""Instruction boot-card bootstrap command entries."""

from __future__ import annotations

from .system_catalog_models import CatalogBootstrapCommand, CatalogBootstrapLinks


def _entry(
    command_id: str,
    label: str,
    command: str,
    description: str,
    links: CatalogBootstrapLinks | None = None,
) -> CatalogBootstrapCommand:
    relations = links or CatalogBootstrapLinks()
    return CatalogBootstrapCommand(
        command_id=command_id,
        label=label,
        command=command,
        description=description,
        command_names=relations.command_names,
        guard_ids=relations.guard_ids,
        probe_ids=relations.probe_ids,
        surface_ids=relations.surface_ids,
        contract_ids=relations.contract_ids,
        plan_paths=relations.plan_paths,
    )


def instruction_authority_bootstrap_commands() -> tuple[CatalogBootstrapCommand, ...]:
    """Return boot-card authority reducer entries."""
    return (
        _entry(
            command_id="system_picture",
            label="Current-state reducer",
            command="python3 dev/scripts/devctl.py system-picture --format md",
            description="Composite current-state reducer after startup authority is known.",
            links=CatalogBootstrapLinks(
                command_names=("system-picture",),
                contract_ids=("SystemPictureSnapshot", "SystemCatalog"),
                plan_paths=("dev/active/ai_governance_platform.md",),
            ),
        ),
        _entry(
            command_id="platform_contracts",
            label="Platform contracts",
            command="python3 dev/scripts/devctl.py platform-contracts --format md",
            description="Registered platform contract and runtime-state surface.",
            links=CatalogBootstrapLinks(
                command_names=("platform-contracts",),
                contract_ids=("ContractSpec", "ConnectivityRegistrySnapshot"),
                plan_paths=("dev/active/ai_governance_platform.md",),
            ),
        ),
    )


def instruction_develop_bootstrap_commands() -> tuple[CatalogBootstrapCommand, ...]:
    """Return provider-neutral /develop entries used by boot cards."""
    return (
        _entry(
            command_id="develop_next",
            label="Develop next",
            command="python3 dev/scripts/devctl.py develop next --actor <actor> --format md",
            description="Universal developer-loop router for the next bounded action.",
            links=CatalogBootstrapLinks(
                command_names=("develop",),
                contract_ids=("WorkIntakePacket", "PlanExpectationPacket"),
                plan_paths=("dev/active/ai_governance_platform.md",),
            ),
        ),
        _entry(
            command_id="develop_show",
            label="Develop show",
            command="python3 dev/scripts/devctl.py develop show --slice-id <id> --format md",
            description="Focused /develop read surface for one slice or packet.",
            links=CatalogBootstrapLinks(
                command_names=("develop",),
                contract_ids=("WorkIntakePacket", "PlanExpectationPacket"),
                plan_paths=("dev/active/ai_governance_platform.md",),
            ),
        ),
    )
