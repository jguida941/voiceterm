"""Support helpers for ``check_feature_completion``."""

from __future__ import annotations

import subprocess
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path

try:
    from check_bootstrap import REPO_ROOT
except ModuleNotFoundError:
    from dev.scripts.checks.check_bootstrap import REPO_ROOT


@dataclass(frozen=True, slots=True)
class FeatureCompletionViolation:
    path: str
    reason: str
    detail: str
    remediation: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


class FeatureCompletionSupport:
    """Source, git, and registry helpers for feature-completion checks."""

    @staticmethod
    def check_guard_completion(
        *,
        path: str,
        registered: frozenset[str],
        bundled: frozenset[str],
        quality: frozenset[str],
        router_mapped: frozenset[str],
        existing: frozenset[str],
        source_text: Mapping[str, str],
    ) -> tuple[FeatureCompletionViolation, ...]:
        test_path = FeatureCompletionSupport.focused_test_path(path)
        violations: list[FeatureCompletionViolation] = []
        if path not in registered:
            violations.append(
                FeatureCompletionViolation(
                    path=path,
                    reason="feature_guard_not_cataloged",
                    detail="New guard entrypoint is not registered in script_catalog_registry.",
                    remediation="Register the guard before it can be treated as a feature.",
                )
            )
        if test_path not in existing:
            violations.append(
                FeatureCompletionViolation(
                    path=path,
                    reason="feature_guard_missing_focused_test",
                    detail=f"Focused test file is missing: {test_path}.",
                    remediation="Add the focused pytest file before claiming the guard exists.",
                )
            )
        if path not in router_mapped or test_path not in router_mapped:
            violations.append(
                FeatureCompletionViolation(
                    path=path,
                    reason="feature_guard_missing_router_mapping",
                    detail="Guard and focused test are not both mapped in router_python_tests.",
                    remediation="Map the guard path and focused test path in router_python_tests.py.",
                )
            )
        if path not in quality:
            violations.append(
                FeatureCompletionViolation(
                    path=path,
                    reason="feature_guard_missing_quality_step",
                    detail="Guard has no QualityStepSpec.",
                    remediation="Add a QualityStepSpec in quality_policy/defaults.py.",
                )
            )
        if path not in bundled:
            violations.append(
                FeatureCompletionViolation(
                    path=path,
                    reason="feature_guard_missing_execution_path",
                    detail="Guard is not reachable from a devctl command bundle.",
                    remediation="Add the guard to the appropriate BUNDLE_REGISTRY layer.",
                )
            )
        if not FeatureCompletionSupport.source_has_failure_reason(path, source_text):
            violations.append(
                FeatureCompletionViolation(
                    path=path,
                    reason="feature_guard_missing_failure_reason",
                    detail="Guard source does not expose a machine-readable failure reason.",
                    remediation="Add explicit reason fields or constants to every blocking path.",
                )
            )
        return tuple(violations)

    @staticmethod
    def focused_test_path(path: str) -> str:
        name = Path(path).name
        return f"dev/scripts/devctl/tests/checks/test_{name}"

    @staticmethod
    def source_has_failure_reason(path: str, source_text: Mapping[str, str]) -> bool:
        text = source_text.get(path)
        if text is None:
            try:
                text = (REPO_ROOT / path).read_text(encoding="utf-8")
            except OSError:
                return False
        if FeatureCompletionSupport.text_has_failure_reason(text):
            return True
        shim_target = FeatureCompletionSupport.shim_target(text)
        if not shim_target:
            return False
        target_text = source_text.get(shim_target)
        if target_text is None:
            try:
                target_text = (REPO_ROOT / shim_target).read_text(encoding="utf-8")
            except OSError:
                return False
        return FeatureCompletionSupport.text_has_failure_reason(target_text)

    @staticmethod
    def text_has_failure_reason(text: str) -> bool:
        return "reason=" in text or '"reason"' in text or "'reason'" in text

    @staticmethod
    def shim_target(text: str) -> str:
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("# shim-target:"):
                return stripped.split(":", 1)[1].strip()
        return ""

    @staticmethod
    def registered_check_paths() -> frozenset[str]:
        from dev.scripts.devctl.governance.script_catalog_registry import (
            CHECK_SCRIPT_RELATIVE_PATHS,
        )

        return frozenset(str(path) for path in CHECK_SCRIPT_RELATIVE_PATHS.values())

    @staticmethod
    def bundled_check_paths() -> frozenset[str]:
        from dev.scripts.devctl.bundles.registry import BUNDLE_REGISTRY

        paths: set[str] = set()
        for command in FeatureCompletionSupport.flatten(BUNDLE_REGISTRY.values()):
            for token in command.split():
                if token.startswith("dev/scripts/checks/") and token.endswith(".py"):
                    paths.add(token)
        return frozenset(paths)

    @staticmethod
    def quality_check_paths() -> frozenset[str]:
        from dev.scripts.devctl.governance.script_catalog_registry import (
            CHECK_SCRIPT_RELATIVE_PATHS,
        )
        from dev.scripts.devctl.quality_policy.defaults import AI_GUARD_REGISTRY

        return frozenset(
            CHECK_SCRIPT_RELATIVE_PATHS[script_id]
            for script_id in AI_GUARD_REGISTRY
            if script_id in CHECK_SCRIPT_RELATIVE_PATHS
        )

    @staticmethod
    def router_mapped_paths() -> frozenset[str]:
        from dev.scripts.devctl.commands.check.router_python_tests import (
            _DEVCTL_TEST_TARGETS,
        )

        paths: set[str] = set()
        for source_prefix, test_paths in _DEVCTL_TEST_TARGETS:
            paths.add(source_prefix.rstrip("/"))
            paths.update(test_paths)
        return frozenset(paths)

    @staticmethod
    def flatten(items: object) -> tuple[str, ...]:
        if isinstance(items, str):
            return (items,)
        if isinstance(items, Mapping):
            return FeatureCompletionSupport.flatten(items.values())
        if isinstance(items, Iterable):
            flattened: list[str] = []
            for item in items:
                flattened.extend(FeatureCompletionSupport.flatten(item))
            return tuple(flattened)
        return ()

    @staticmethod
    def existing_paths(paths: Sequence[str]) -> frozenset[str]:
        existing = set(paths)
        for path in paths:
            test_path = FeatureCompletionSupport.focused_test_path(path)
            if (REPO_ROOT / test_path).exists():
                existing.add(test_path)
        return frozenset(existing)

    @staticmethod
    def git_status_output(warnings: list[str]) -> str:
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain", "--untracked-files=all"],
                cwd=REPO_ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
        except OSError as exc:
            warnings.append(f"git status failed: {exc}")
            return ""
        if result.returncode:
            warnings.append(f"git status returned {result.returncode}: {result.stderr.strip()}")
        return result.stdout

    @staticmethod
    def new_or_added_paths(status_output: str) -> tuple[str, ...]:
        paths: list[str] = []
        for line in status_output.splitlines():
            if not line.strip():
                continue
            status = line[:2]
            if status != "??" and "A" not in status:
                continue
            path = line[3:] if len(line) > 3 else line.strip()
            if " -> " in path:
                path = path.split(" -> ", 1)[1]
            path = path.strip()
            if path:
                paths.append(path)
        return tuple(paths)

    @staticmethod
    def is_check_entrypoint(path: str) -> bool:
        name = Path(path).name
        return path.startswith("dev/scripts/checks/") and name.startswith("check_") and name.endswith(".py")
