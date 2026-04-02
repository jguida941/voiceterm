"""Compatibility wrapper for command-source taint helpers."""

from __future__ import annotations

if __package__:
    from .command_source_validation_taint_classify import (
        bind_assignment_targets,
        classify_expression,
        extract_assigned_names,
        iter_child_expressions,
    )
    from .command_source_validation_taint_imports import (
        SUBPROCESS_METHODS,
        _collect_import_from_bindings,
        collect_import_bindings,
    )
    from .command_source_validation_taint_sources import (
        CLI_CONTAINER_NAMES,
        CONFIG_CONTAINER_NAMES,
        VALIDATOR_TOKENS,
        _is_env_call,
        is_env_source,
        is_environ_attribute,
        is_shlex_split_call,
        is_sys_argv_source,
        is_validator_call,
    )
else:  # pragma: no cover - standalone script fallback
    from command_source_validation_taint_classify import (
        bind_assignment_targets,
        classify_expression,
        extract_assigned_names,
        iter_child_expressions,
    )
    from command_source_validation_taint_imports import (
        SUBPROCESS_METHODS,
        _collect_import_from_bindings,
        collect_import_bindings,
    )
    from command_source_validation_taint_sources import (
        CLI_CONTAINER_NAMES,
        CONFIG_CONTAINER_NAMES,
        VALIDATOR_TOKENS,
        _is_env_call,
        is_env_source,
        is_environ_attribute,
        is_shlex_split_call,
        is_sys_argv_source,
        is_validator_call,
    )
