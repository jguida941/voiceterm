"""Smoke coverage for governance guards and probes lacking dedicated suites."""

from __future__ import annotations

import json
import sys
import textwrap
from pathlib import Path
from unittest.mock import patch

from dev.scripts.checks import (
    check_cli_flags_parity,
    check_rustsec_policy,
    check_screenshot_integrity,
    probe_boolean_params,
    probe_defensive_overchecking,
    probe_type_conversions,
    probe_unnecessary_intermediates,
    probe_unwrap_chains,
    probe_vague_errors,
)
from dev.scripts.checks.code_shape_probes import (
    probe_cognitive_complexity as probe_cognitive_complexity_impl,
    probe_match_arm_complexity as probe_match_arm_complexity_impl,
    probe_mutable_parameter_density as probe_mutable_parameter_density_impl,
)


COVERED_GUARD_AND_PROBE_IDS = (
    "cli_flags_parity",
    "rustsec_policy",
    "screenshot_integrity",
    "probe_boolean_params",
    "probe_cognitive_complexity",
    "probe_defensive_overchecking",
    "probe_match_arm_complexity",
    "probe_mutable_parameter_density",
    "probe_type_conversions",
    "probe_unnecessary_intermediates",
    "probe_unwrap_chains",
    "probe_vague_errors",
)


def test_cli_flags_parity_extracts_matching_flags(tmp_path: Path) -> None:
    doc_path = tmp_path / "CLI_FLAGS.md"
    doc_path.write_text(
        "\n".join(
            [
                "| Flag | Description |",
                "| --- | --- |",
                "| `--alpha` | first |",
                "| `--beta-value` | second |",
            ]
        ),
        encoding="utf-8",
    )
    schema_path = tmp_path / "cli.rs"
    schema_path.write_text(
        textwrap.dedent(
            """
            struct Args {
                #[arg(long)]
                pub alpha: bool,
                #[arg(long)]
                pub beta_value: String,
            }
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )

    assert check_cli_flags_parity._extract_doc_flags(doc_path) == {"alpha", "beta-value"}
    assert check_cli_flags_parity._extract_schema_flags(schema_path) == {"alpha", "beta-value"}


def test_rustsec_policy_fails_high_severity_vulnerability(tmp_path: Path) -> None:
    payload_path = tmp_path / "audit.json"
    payload_path.write_text(
        json.dumps(
            {
                "vulnerabilities": {
                    "list": [
                        {
                            "advisory": {"id": "RUSTSEC-2026-0001", "cvss": 9.8},
                            "package": {"name": "demo", "version": "1.0.0"},
                        }
                    ]
                },
                "warnings": [],
            }
        ),
        encoding="utf-8",
    )

    with patch.object(
        sys,
        "argv",
        ["check_rustsec_policy.py", "--input", str(payload_path)],
    ):
        assert check_rustsec_policy.main() == 1


def test_screenshot_integrity_collects_local_targets(tmp_path: Path) -> None:
    doc_path = tmp_path / "guide.md"
    doc_path.write_text(
        "\n".join(
            [
                "![Local](images/shot.png)",
                "![Wrapped](<images/wrapped.png>)",
                "![Remote](https://example.com/remote.png)",
            ]
        ),
        encoding="utf-8",
    )

    assert check_screenshot_integrity._collect_image_targets(doc_path) == [
        "images/shot.png",
        "images/wrapped.png",
        "https://example.com/remote.png",
    ]
    assert check_screenshot_integrity._normalize_target("<images/wrapped.png>") == "images/wrapped.png"
    assert check_screenshot_integrity._is_remote_or_ignored("https://example.com/remote.png")


def test_probe_boolean_params_flags_python_function() -> None:
    hints = probe_boolean_params._scan_python_file(
        textwrap.dedent(
            """
            def decide(alpha: bool, beta: bool, gamma: bool) -> bool:
                return alpha and beta and gamma
            """
        ),
        Path("app/demo.py"),
    )

    assert hints
    assert hints[0].symbol == "decide"


def test_probe_cognitive_complexity_flags_nested_python_flow() -> None:
    hints = probe_cognitive_complexity_impl._scan_python_file(
        textwrap.dedent(
            """
            def orchestrate(items):
                for item in items:
                    if item > 0 and item < 5 or item == 99:
                        while item:
                            if item % 2 == 0:
                                if item > 10:
                                    return item
                            else:
                                if item < 0:
                                    return -item
                    else:
                        for other in items:
                            if other:
                                break
                return None
            """
        ),
        Path("dev/scripts/demo.py"),
    )

    assert hints
    assert hints[0].symbol == "orchestrate"


def test_probe_defensive_overchecking_flags_repeated_isinstance() -> None:
    hints = probe_defensive_overchecking._scan_python_file(
        textwrap.dedent(
            """
            def classify(value):
                if isinstance(value, str):
                    return "str"
                elif isinstance(value, int):
                    return "int"
                elif isinstance(value, float):
                    return "float"
                return "other"
            """
        ),
        Path("dev/scripts/demo.py"),
    )

    assert hints
    assert hints[0].symbol == "classify"


def test_probe_match_arm_complexity_flags_large_rust_arm() -> None:
    hints = probe_match_arm_complexity_impl._scan_rust_file(
        textwrap.dedent(
            """
            fn dispatch(code: i32) {
                match code {
                    0 => {
                        let a = 1;
                        let b = 2;
                        let c = 3;
                        let d = 4;
                        let e = 5;
                        println!("{}", a + b + c + d + e);
                    }
                    _ => {}
                }
            }
            """
        ),
        Path("rust/src/demo.rs"),
    )

    assert hints
    assert hints[0].symbol == "dispatch"


def test_probe_mutable_parameter_density_flags_many_mut_refs() -> None:
    hints = probe_mutable_parameter_density_impl._scan_rust_file(
        textwrap.dedent(
            """
            fn update(a: &mut i32, b: &mut i32, c: &mut i32) {
                *a += 1;
                *b += 1;
                *c += 1;
            }
            """
        ),
        Path("rust/src/demo.rs"),
    )

    assert hints
    assert hints[0].symbol == "update"


def test_probe_type_conversions_flags_round_trip_conversions() -> None:
    hints = probe_type_conversions._scan_rust_file(
        textwrap.dedent(
            """
            fn render(name: String) -> String {
                let copy = name.as_str().to_string();
                copy
            }
            """
        ),
        Path("rust/src/demo.rs"),
    )

    assert hints
    assert hints[0].symbol == "render"


def test_probe_unnecessary_intermediates_flags_generic_returns() -> None:
    hints = probe_unnecessary_intermediates._scan_python_file(
        textwrap.dedent(
            """
            def build(flag):
                if flag:
                    result = compute()
                    return result
                output = fallback()
                return output
            """
        ),
        Path("dev/scripts/demo.py"),
    )

    assert hints
    assert hints[0].symbol == "build"


def test_probe_unwrap_chains_flags_multiple_panics() -> None:
    hints = probe_unwrap_chains._scan_rust_file(
        textwrap.dedent(
            """
            fn load_config(values: Vec<String>) -> String {
                let first = values.get(0).unwrap().clone();
                let parsed = first.parse::<u32>().unwrap();
                let label = Some("demo").expect("missing label");
                format!("{}{}", parsed, label)
            }
            """
        ),
        Path("rust/src/demo.rs"),
    )

    assert hints
    assert hints[0].symbol == "load_config"


def test_probe_vague_errors_flags_missing_runtime_context() -> None:
    hints = probe_vague_errors._scan_rust_file(
        textwrap.dedent(
            """
            fn open_config(flag: bool) -> anyhow::Result<()> {
                if flag {
                    anyhow::bail!("failed to open config");
                }
                std::fs::read_to_string("settings.toml").context("unable to load settings")?;
                Ok(())
            }
            """
        ),
        Path("rust/src/demo.rs"),
    )

    assert hints
    assert hints[0].symbol == "open_config"


def test_probe_module_exports_remain_wired() -> None:
    """Keep the probe implementation entrypoints referenced by the smoke suite."""
    assert probe_cognitive_complexity_impl.main is not None
    assert probe_match_arm_complexity_impl.main is not None
    assert probe_mutable_parameter_density_impl.main is not None
    assert COVERED_GUARD_AND_PROBE_IDS
