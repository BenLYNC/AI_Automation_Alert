"""Tests for the Scorer orchestrator using a fake LLM client."""

from __future__ import annotations

import json

import pytest

from automation_alert.models import OnetCategory
from automation_alert.scorer import Scorer
from tests.conftest import (
    FakeLLMClient,
    _make_agentic_scoring_response,
    _make_base_scoring_response,
)


@pytest.fixture
def scorer(fake_llm):
    return Scorer(llm_client=fake_llm)


# ---------------------------------------------------------------------------
# Base scoring
# ---------------------------------------------------------------------------


class TestScoreCategoryItems:
    def test_returns_scored_items(self, scorer, sample_raw_items):
        items = scorer.score_category_items(
            soc_code="15-1252.00",
            occupation_title="Software Developers",
            category=OnetCategory.TASKS,
            raw_items=sample_raw_items,
        )
        assert len(items) >= 1
        item = items[0]
        assert item.item_name == "Test Task"
        assert item.category == OnetCategory.TASKS
        assert item.time_saved_low_pct >= 0
        assert item.time_saved_high_pct >= item.time_saved_low_pct

    def test_empty_items_returns_empty(self, scorer):
        items = scorer.score_category_items(
            soc_code="15-1252.00",
            occupation_title="Software Developers",
            category=OnetCategory.TASKS,
            raw_items=[],
        )
        assert items == []

    def test_llm_call_is_made(self, fake_llm, sample_raw_items):
        scorer = Scorer(llm_client=fake_llm)
        scorer.score_category_items(
            soc_code="15-1252.00",
            occupation_title="Software Developers",
            category=OnetCategory.TASKS,
            raw_items=sample_raw_items,
        )
        assert len(fake_llm.calls) == 1
        system, user = fake_llm.calls[0]
        assert "15-1252.00" in user or "Software Developers" in user

    def test_handles_malformed_llm_item_gracefully(self, sample_raw_items):
        """If one item in the LLM response is malformed, others still parse."""
        response = json.dumps([
            {"item_name": "Bad Item"},  # missing required fields
            json.loads(_make_base_scoring_response())[0],
        ])
        client = FakeLLMClient(default=response)
        scorer = Scorer(llm_client=client)
        items = scorer.score_category_items(
            soc_code="15-1252.00",
            occupation_title="Software Developers",
            category=OnetCategory.TASKS,
            raw_items=sample_raw_items,
        )
        assert len(items) == 1
        assert items[0].item_name == "Test Task"


# ---------------------------------------------------------------------------
# Agentic scoring
# ---------------------------------------------------------------------------


class TestScoreAgenticImpact:
    def test_returns_agentic_scores(self, sample_raw_items):
        client = FakeLLMClient(default=_make_agentic_scoring_response())
        scorer = Scorer(llm_client=client)
        results = scorer.score_agentic_impact(
            soc_code="15-1252.00",
            occupation_title="Software Developers",
            category=OnetCategory.TASKS,
            raw_items=sample_raw_items,
        )
        assert len(results) >= 1
        ag = results[0]
        assert ag.item_name == "Test Task"
        assert ag.final_time_saved_low_pct >= 0
        assert ag.final_time_saved_high_pct >= ag.final_time_saved_low_pct

    def test_empty_items_returns_empty(self, scorer):
        results = scorer.score_agentic_impact(
            soc_code="15-1252.00",
            occupation_title="Software Developers",
            category=OnetCategory.TASKS,
            raw_items=[],
        )
        assert results == []


# ---------------------------------------------------------------------------
# Full occupation scoring
# ---------------------------------------------------------------------------


class TestScoreOccupation:
    def test_full_pipeline(self, sample_raw_items):
        base_resp = _make_base_scoring_response()
        agentic_resp = _make_agentic_scoring_response()
        client = FakeLLMClient(default=base_resp, responses={"agentic": agentic_resp})
        # The FakeLLMClient matches on substrings — the base prompt system prompt
        # doesn't contain "agentic" so it hits the default (base response).
        # The agentic prompt system prompt contains "agentic" so it matches.
        scorer = Scorer(llm_client=client)

        onet_data = {OnetCategory.TASKS: sample_raw_items}
        alert, agentic_scores = scorer.score_occupation(
            soc_code="41-9022.00",
            occupation_title="Real Estate Sales Agents",
            onet_data=onet_data,
            include_agentic=True,
        )
        assert alert.soc_code == "41-9022.00"
        assert alert.occupation_title == "Real Estate Sales Agents"
        assert len(alert.category_summaries) == 1
        assert alert.overall_time_saved_low_pct >= 0

    def test_no_agentic(self, sample_raw_items):
        client = FakeLLMClient(default=_make_base_scoring_response())
        scorer = Scorer(llm_client=client)

        onet_data = {OnetCategory.TASKS: sample_raw_items}
        alert, agentic_scores = scorer.score_occupation(
            soc_code="41-9022.00",
            occupation_title="Real Estate Sales Agents",
            onet_data=onet_data,
            include_agentic=False,
        )
        assert agentic_scores == {}
        assert len(client.calls) == 1  # only base, no agentic
