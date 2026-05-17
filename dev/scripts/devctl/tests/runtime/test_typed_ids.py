"""Strict checks for nominal governance identifier wrappers."""

from __future__ import annotations

import unittest
from typing import assert_type

from dev.scripts.devctl.commands.development.lifecycle_commands import packet_show_command
from dev.scripts.devctl.runtime.typed_ids import (
    PacketId,
    PlanRowId,
    ReceiptId,
    as_packet_id,
    as_plan_row_id,
    as_receipt_id,
    id_text,
    packet_ref,
    plan_row_ref,
    receipt_ref,
)


class TypedIdTests(unittest.TestCase):
    def test_newtype_wrappers_remain_json_safe_strings_at_runtime(self) -> None:
        packet = as_packet_id(" rev_pkt_1 ")
        receipt = as_receipt_id(" receipt_1 ")
        plan_row = as_plan_row_id(" MP377-P0 ")

        assert_type(packet, PacketId)
        assert_type(receipt, ReceiptId)
        assert_type(plan_row, PlanRowId)

        self.assertIsInstance(packet, str)
        self.assertIsInstance(receipt, str)
        self.assertIsInstance(plan_row, str)
        self.assertEqual(id_text(packet), "rev_pkt_1")
        self.assertEqual(id_text(receipt), "receipt_1")
        self.assertEqual(id_text(plan_row), "MP377-P0")

    def test_identifier_refs_are_nominally_typed(self) -> None:
        packet = as_packet_id("rev_pkt_2")
        receipt = as_receipt_id("receipt_2")
        plan_row = as_plan_row_id("MP377-P1")

        self.assertEqual(_packet_anchor(packet), "packet:rev_pkt_2")
        self.assertEqual(_receipt_anchor(receipt), "receipt:receipt_2")
        self.assertEqual(_plan_row_anchor(plan_row), "plan_row:MP377-P1")

    def test_packet_show_command_accepts_normalized_packet_ids(self) -> None:
        command = packet_show_command(as_packet_id("rev_pkt_3"))

        self.assertIn("--packet-id rev_pkt_3", command)
        self.assertEqual(packet_show_command(as_packet_id("")), "")


def _packet_anchor(packet_id: PacketId) -> str:
    return packet_ref(packet_id)


def _receipt_anchor(receipt_id: ReceiptId) -> str:
    return receipt_ref(receipt_id)


def _plan_row_anchor(plan_row_id: PlanRowId) -> str:
    return plan_row_ref(plan_row_id)
