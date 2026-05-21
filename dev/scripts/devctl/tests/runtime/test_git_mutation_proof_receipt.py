"""Focused tests for GitMutationProofReceipt code_identity_hash extension."""

from __future__ import annotations

from dev.scripts.devctl.runtime.git_mutation_proof_receipt import (
    GIT_MUTATION_PROOF_RECEIPT_SCHEMA_VERSION,
    GitMutationProofReceipt,
    git_mutation_proof_receipt_from_mapping,
)


def test_git_mutation_proof_receipt_carries_code_identity_hash() -> None:
    receipt = GitMutationProofReceipt(code_identity_hash="sha256:abcd1234")
    payload = receipt.to_dict()
    assert payload["code_identity_hash"] == "sha256:abcd1234"
    assert payload["schema_version"] == GIT_MUTATION_PROOF_RECEIPT_SCHEMA_VERSION


def test_git_mutation_proof_receipt_code_identity_hash_defaults_empty() -> None:
    receipt = GitMutationProofReceipt()
    assert receipt.code_identity_hash == ""
    assert receipt.to_dict()["code_identity_hash"] == ""


def test_git_mutation_proof_receipt_from_mapping_round_trip_code_identity_hash() -> None:
    payload = {
        "contract_id": "GitMutationProofReceipt",
        "schema_version": GIT_MUTATION_PROOF_RECEIPT_SCHEMA_VERSION,
        "receipt_id": "git_mutation_proof:commit:abc",
        "mutation_kind": "commit",
        "code_identity_hash": "sha256:treehash-policyhash-bundlehash",
    }
    restored = git_mutation_proof_receipt_from_mapping(payload)
    assert restored.code_identity_hash == "sha256:treehash-policyhash-bundlehash"
    round_tripped = restored.to_dict()
    assert round_tripped["code_identity_hash"] == "sha256:treehash-policyhash-bundlehash"


def test_git_mutation_proof_receipt_from_mapping_missing_code_identity_hash_is_empty() -> None:
    payload = {
        "contract_id": "GitMutationProofReceipt",
        "schema_version": GIT_MUTATION_PROOF_RECEIPT_SCHEMA_VERSION,
        "receipt_id": "git_mutation_proof:commit:legacy",
    }
    restored = git_mutation_proof_receipt_from_mapping(payload)
    assert restored.code_identity_hash == ""
