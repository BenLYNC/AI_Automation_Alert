"""Shared fixtures for the test suite."""

from __future__ import annotations

import json

import pytest

from automation_alert.llm_client import LLMClient


class FakeLLMClient(LLMClient):
    """Deterministic LLM client for testing.

    Returns canned JSON responses keyed by prompt substring matching.
    """

    def __init__(self, responses: dict[str, str] | None = None, default: str = "[]"):
        self._responses = responses or {}
        self._default = default
        self.calls: list[tuple[str, str]] = []

    def call(self, system: str, user_prompt: str) -> str:
        self.calls.append((system, user_prompt))
        for key, response in self._responses.items():
            if key in user_prompt or key in system:
                return response
        return self._default


def _make_base_scoring_response(item_name: str = "Test Task") -> str:
    """Build a valid base-layer LLM response for a single item."""
    return json.dumps([{
        "item_name": item_name,
        "exposure_levels": ["E1", "E2"],
        "ceiling_category": "pure_drafting",
        "subtasks": [
            {
                "bucket": "input_gathering",
                "baseline_share_pct": 0.3,
                "exposure_levels": ["E2"],
                "leverage_level": "medium",
                "efficiency_gain_low": 0.25,
                "efficiency_gain_high": 0.45,
            },
            {
                "bucket": "transformation_drafting",
                "baseline_share_pct": 0.4,
                "exposure_levels": ["E1"],
                "leverage_level": "high",
                "efficiency_gain_low": 0.55,
                "efficiency_gain_high": 0.75,
            },
            {
                "bucket": "human_only_execution",
                "baseline_share_pct": 0.3,
                "exposure_levels": [],
                "leverage_level": "low",
                "efficiency_gain_low": 0.0,
                "efficiency_gain_high": 0.05,
            },
        ],
        "rationale": "Test rationale for scoring.",
        "advancement_notes": "Could advance with better tooling.",
    }])


def _make_agentic_scoring_response(item_name: str = "Test Task") -> str:
    """Build a valid agentic-layer LLM response for a single item."""
    return json.dumps([{
        "item_name": item_name,
        "recommended_mode": 2,
        "mode_rationale": "Bounded autonomy is appropriate.",
        "workflow_scores": [
            {
                "unit": "intake_triage",
                "time_share_pct": 0.2,
                "agentic_suitability": 2,
                "execution_automation_pct": 0.4,
                "oversight_tax_pct": 0.1,
                "net_gain_pct": 0.3,
                "rationale": "Structured intake.",
            },
            {
                "unit": "tool_actions",
                "time_share_pct": 0.5,
                "agentic_suitability": 3,
                "execution_automation_pct": 0.6,
                "oversight_tax_pct": 0.15,
                "net_gain_pct": 0.45,
                "rationale": "Well-integrated tooling.",
            },
            {
                "unit": "exceptions_human_only",
                "time_share_pct": 0.3,
                "agentic_suitability": 0,
                "execution_automation_pct": 0.0,
                "oversight_tax_pct": 0.0,
                "net_gain_pct": 0.0,
                "rationale": "Requires human judgment.",
            },
        ],
        "exception_rate": 0.15,
        "takeover_cost": 0.5,
        "current_maturity": 2,
        "agentic_ceiling": "standardized_backoffice",
        "knowledge_work_type": "routine_cognitive",
        "stakes_level": "medium",
        "agentic_rationale": "Good candidate for bounded autonomy.",
        "advancement_notes": "Better APIs would help.",
        "near_term_projection": "Expect maturity level 3 within 2 years.",
    }])


@pytest.fixture
def fake_llm():
    """Return a FakeLLMClient with canned base + agentic responses."""
    return FakeLLMClient(
        responses={
            "exposure": _make_base_scoring_response(),
            "agentic": _make_agentic_scoring_response(),
        },
        default=_make_base_scoring_response(),
    )


@pytest.fixture
def sample_raw_items():
    """Return minimal raw O*NET items for testing."""
    return [
        {"name": "Test Task", "score": {"value": 4.2}},
        {"name": "Another Task", "score": {"value": 3.1}},
    ]
