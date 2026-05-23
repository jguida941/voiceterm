from pathlib import Path

from dev.scripts.checks import check_contract_consumer_coverage_sweep as guard


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_contract_with_external_writer_and_reader_passes(tmp_path: Path) -> None:
    contract = tmp_path / "dev/scripts/devctl/runtime/example_contracts.py"
    writer = tmp_path / "dev/scripts/devctl/runtime/example_writer.py"
    reader = tmp_path / "dev/scripts/devctl/runtime/example_reader.py"
    _write(
        contract,
        """
from dataclasses import dataclass

@dataclass(frozen=True)
class ExampleReceipt:
    receipt_id: str
""",
    )
    _write(
        writer,
        """
from dev.scripts.devctl.runtime.example_contracts import ExampleReceipt

def write_receipt() -> ExampleReceipt:
    return ExampleReceipt(receipt_id="r1")
""",
    )
    _write(
        reader,
        """
from dev.scripts.devctl.runtime.example_contracts import ExampleReceipt

def read_receipt(payload: dict[str, object]) -> str:
    return ExampleReceipt.from_mapping(payload).receipt_id
""",
    )

    report = guard.build_report(
        repo_root=tmp_path,
        scope="changed",
        changed_paths=(contract,),
    )

    assert report["ok"] is True
    assert report["contract_count"] == 1


def test_contract_with_canonical_producer_call_passes(tmp_path: Path) -> None:
    contract = tmp_path / "dev/scripts/devctl/runtime/example_contracts.py"
    consumer = tmp_path / "dev/scripts/devctl/runtime/example_consumer.py"
    _write(
        contract,
        """
from dataclasses import dataclass

@dataclass(frozen=True)
class ExampleReceipt:
    receipt_id: str

def compose_receipt() -> ExampleReceipt:
    return ExampleReceipt(receipt_id="r1")
""",
    )
    _write(
        consumer,
        """
from dev.scripts.devctl.runtime.example_contracts import compose_receipt

def consume_receipt() -> str:
    receipt = compose_receipt()
    return receipt.receipt_id
""",
    )

    report = guard.build_report(
        repo_root=tmp_path,
        scope="changed",
        changed_paths=(contract,),
    )

    assert report["ok"] is True
    row = report["contracts"][0]
    assert row["writer_refs"] == [
        (
            "dev/scripts/devctl/runtime/example_consumer.py:"
            "producer:compose_receipt->ExampleReceipt"
        )
    ]
    assert row["reader_refs"] == [
        (
            "dev/scripts/devctl/runtime/example_consumer.py:"
            "producer:compose_receipt->ExampleReceipt"
        )
    ]


def test_contract_with_argument_annotation_reader_passes(tmp_path: Path) -> None:
    contract = tmp_path / "dev/scripts/devctl/runtime/example_contracts.py"
    writer = tmp_path / "dev/scripts/devctl/runtime/example_writer.py"
    reader = tmp_path / "dev/scripts/devctl/runtime/example_reader.py"
    _write(
        contract,
        """
from dataclasses import dataclass

@dataclass(frozen=True)
class ExampleReceipt:
    receipt_id: str
""",
    )
    _write(
        writer,
        """
from dev.scripts.devctl.runtime.example_contracts import ExampleReceipt

def write_receipt():
    return ExampleReceipt(receipt_id="r1")
""",
    )
    _write(
        reader,
        """
from dev.scripts.devctl.runtime.example_contracts import ExampleReceipt

def read_receipt(receipt: ExampleReceipt | None) -> str:
    return receipt.receipt_id if receipt is not None else ""
""",
    )

    report = guard.build_report(
        repo_root=tmp_path,
        scope="changed",
        changed_paths=(contract,),
    )

    assert report["ok"] is True
    row = report["contracts"][0]
    assert row["reader_refs"] == [
        "dev/scripts/devctl/runtime/example_reader.py:argument_annotation:ExampleReceipt"
    ]


def test_contract_without_external_writer_fails(tmp_path: Path) -> None:
    contract = tmp_path / "dev/scripts/devctl/runtime/example_contracts.py"
    reader = tmp_path / "dev/scripts/devctl/runtime/example_reader.py"
    _write(
        contract,
        """
from dataclasses import dataclass

@dataclass
class ExampleReceipt:
    receipt_id: str
""",
    )
    _write(
        reader,
        """
from dev.scripts.devctl.runtime.example_contracts import ExampleReceipt

def read_receipt(payload: dict[str, object]) -> str:
    return ExampleReceipt.from_mapping(payload).receipt_id
""",
    )

    report = guard.build_report(
        repo_root=tmp_path,
        scope="changed",
        changed_paths=(contract,),
    )

    assert report["ok"] is False
    reasons = {violation["reason"] for violation in report["violations"]}
    assert "contract_without_external_writer" in reasons


def test_contract_without_external_reader_fails(tmp_path: Path) -> None:
    contract = tmp_path / "dev/scripts/devctl/runtime/example_contracts.py"
    writer = tmp_path / "dev/scripts/devctl/runtime/example_writer.py"
    _write(
        contract,
        """
from dataclasses import dataclass

@dataclass
class ExampleReceipt:
    receipt_id: str
""",
    )
    _write(
        writer,
        """
from dev.scripts.devctl.runtime.example_contracts import ExampleReceipt

def write_receipt():
    return ExampleReceipt(receipt_id="r1")
""",
    )

    report = guard.build_report(
        repo_root=tmp_path,
        scope="changed",
        changed_paths=(contract,),
    )

    assert report["ok"] is False
    reasons = {violation["reason"] for violation in report["violations"]}
    assert "contract_without_external_reader" in reasons


def test_git_status_parser_preserves_leading_dev_path() -> None:
    assert (
        guard._path_from_git_status_line(
            " M dev/scripts/devctl/runtime/example_contracts.py"
        )
        == "dev/scripts/devctl/runtime/example_contracts.py"
    )
