"""Compatibility exports for dogfood scenario reducers."""

from __future__ import annotations

from .dogfood_scenario_models import (
    DEFAULT_TESTER_CADENCE_SECONDS,
    DEVELOPMENT_LOOP_SCENARIO_ID,
    DOGFOOD_SCENARIO_REPORT_CONTRACT_ID,
    DOGFOOD_SCENARIO_REPORT_SCHEMA_VERSION,
    PLAN41_TANDEM_SCENARIO_ID,
    VALID_DOGFOOD_FIX_MODES,
    VALID_DOGFOOD_SCENARIOS,
    DogfoodScenarioGate,
    DogfoodScenarioLane,
    DogfoodScenarioReport,
)
from .dogfood_scenario_plan41 import build_plan41_tandem_scenario
from .dogfood_scenario_render import render_dogfood_scenario_markdown

__all__ = [
    "DEFAULT_TESTER_CADENCE_SECONDS",
    "DEVELOPMENT_LOOP_SCENARIO_ID",
    "DOGFOOD_SCENARIO_REPORT_CONTRACT_ID",
    "DOGFOOD_SCENARIO_REPORT_SCHEMA_VERSION",
    "PLAN41_TANDEM_SCENARIO_ID",
    "VALID_DOGFOOD_FIX_MODES",
    "VALID_DOGFOOD_SCENARIOS",
    "DogfoodScenarioGate",
    "DogfoodScenarioLane",
    "DogfoodScenarioReport",
    "build_plan41_tandem_scenario",
    "render_dogfood_scenario_markdown",
]
