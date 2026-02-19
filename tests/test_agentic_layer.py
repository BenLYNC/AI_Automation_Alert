"""Tests for the agentic impact layer computations."""

from __future__ import annotations

import pytest

from automation_alert.agentic_layer import (
    AGENTIC_CEILING_CAPS,
    AgenticCeilingCategory,
    AgentMaturityLevel,
    AgenticSuitability,
    KnowledgeWorkType,
    OperatingMode,
    StakesLevel,
    WorkflowUnit,
    WorkflowUnitScore,
    apply_agentic_adjustment,
    apply_agentic_ceiling,
    apply_compounding_bonus,
    compute_cognitive_displacement,
    compute_maturity_range,
    compute_raw_agentic_time_saved,
    apply_agentic_discounts,
    score_agentic_item,
)
from automation_alert.models import (
    CeilingCategory,
    ExposureLevel,
    LeverageLevel,
    OnetCategory,
    SubtaskBucket,
    SubtaskScore,
)
from automation_alert.scoring_engine import score_item


def _make_workflow_scores() -> list[WorkflowUnitScore]:
    return [
        WorkflowUnitScore(
            unit=WorkflowUnit.W1_INTAKE_TRIAGE,
            time_share_pct=0.3,
            agentic_suitability=AgenticSuitability.MOSTLY,
            execution_automation_pct=0.4,
            oversight_tax_pct=0.1,
            net_gain_pct=0.3,
            rationale="Structured intake.",
        ),
        WorkflowUnitScore(
            unit=WorkflowUnit.W4_TOOL_ACTIONS,
            time_share_pct=0.4,
            agentic_suitability=AgenticSuitability.HIGHLY,
            execution_automation_pct=0.6,
            oversight_tax_pct=0.15,
            net_gain_pct=0.45,
            rationale="API-driven.",
        ),
        WorkflowUnitScore(
            unit=WorkflowUnit.W7_EXCEPTIONS_HUMAN_ONLY,
            time_share_pct=0.3,
            agentic_suitability=AgenticSuitability.NOT_SUITABLE,
            execution_automation_pct=0.0,
            oversight_tax_pct=0.0,
            net_gain_pct=0.0,
            rationale="Requires human.",
        ),
    ]


class TestRawAgenticTimeSaved:
    def test_weighted_sum(self):
        ws = _make_workflow_scores()
        raw = compute_raw_agentic_time_saved(ws)
        expected = (0.3 * 0.3 + 0.4 * 0.45 + 0.3 * 0.0) * 100
        assert raw == pytest.approx(expected, abs=0.2)

    def test_empty(self):
        assert compute_raw_agentic_time_saved([]) == 0.0


class TestCompoundingBonus:
    def test_bonus_range(self):
        ws = _make_workflow_scores()
        raw = 27.0
        with_bonus, bonus = apply_compounding_bonus(raw, ws)
        assert 3 <= bonus <= 15
        assert with_bonus == pytest.approx(raw + bonus, abs=0.1)

    def test_empty_workflow(self):
        with_bonus, bonus = apply_compounding_bonus(10.0, [])
        assert bonus == 0.0
        assert with_bonus == 10.0


class TestAgenticDiscounts:
    def test_discount_applied(self):
        adjusted = apply_agentic_discounts(40.0, 0.15, 0.5)
        # 40 - (0.15 * 0.5 * 100) = 40 - 7.5 = 32.5
        assert adjusted == pytest.approx(32.5)

    def test_floor_at_zero(self):
        adjusted = apply_agentic_discounts(5.0, 0.5, 0.5)
        # 5 - 25 = -20 -> clamped to 0
        assert adjusted == 0.0


class TestMaturityRange:
    def test_higher_maturity_wider_range(self):
        low1, high1 = compute_maturity_range(30.0, AgentMaturityLevel.LEVEL_1)
        low3, high3 = compute_maturity_range(30.0, AgentMaturityLevel.LEVEL_3)
        assert high3 > high1


class TestAgenticCeiling:
    def test_caps_above_ceiling(self):
        cap = AGENTIC_CEILING_CAPS[AgenticCeilingCategory.PHYSICAL_EXECUTION] * 100
        low, high = apply_agentic_ceiling(20.0, 30.0, AgenticCeilingCategory.PHYSICAL_EXECUTION)
        assert high <= cap

    def test_below_ceiling_unchanged(self):
        low, high = apply_agentic_ceiling(5.0, 10.0, AgenticCeilingCategory.STANDARDIZED_BACKOFFICE)
        assert low == pytest.approx(5.0)
        assert high == pytest.approx(10.0)


class TestCognitiveDisplacement:
    def test_routine_cognitive_high(self):
        disp = compute_cognitive_displacement(
            KnowledgeWorkType.ROUTINE_COGNITIVE,
            OperatingMode.FULL_AUTONOMY,
            60.0,
        )
        assert disp > 0

    def test_physical_manual_low(self):
        disp = compute_cognitive_displacement(
            KnowledgeWorkType.PHYSICAL_MANUAL,
            OperatingMode.COPILOT,
            10.0,
        )
        assert disp < 5.0


class TestScoreAgenticItem:
    def test_full_pipeline(self):
        ws = _make_workflow_scores()
        result = score_agentic_item(
            item_name="Test item",
            category=OnetCategory.TASKS,
            recommended_mode=OperatingMode.BOUNDED_AUTONOMY,
            mode_rationale="Good guardrails.",
            workflow_scores=ws,
            exception_rate=0.10,
            takeover_cost=0.40,
            current_maturity=AgentMaturityLevel.LEVEL_2,
            agentic_ceiling=AgenticCeilingCategory.STANDARDIZED_BACKOFFICE,
            knowledge_work_type=KnowledgeWorkType.ROUTINE_COGNITIVE,
            stakes_level=StakesLevel.MEDIUM,
            agentic_rationale="High suitability.",
        )
        assert result.item_name == "Test item"
        assert result.raw_agentic_time_saved_pct > 0
        assert result.final_time_saved_low_pct <= result.final_time_saved_high_pct
        assert result.cognitive_displacement_pct > 0


class TestApplyAgenticAdjustment:
    def test_uplift_when_agentic_higher(self):
        subtasks = [
            SubtaskScore(
                bucket=SubtaskBucket.TRANSFORMATION_DRAFTING,
                baseline_share_pct=1.0,
                exposure_levels=[ExposureLevel.E9],
                leverage_level=LeverageLevel.MEDIUM,
                efficiency_gain_low=0.15,
                efficiency_gain_high=0.25,
            ),
        ]
        base = score_item(
            item_name="Workflow task",
            category=OnetCategory.TASKS,
            exposure_levels=[ExposureLevel.E9],
            subtask_scores=subtasks,
            ceiling_category=CeilingCategory.PURE_DRAFTING,
            rationale=".",
        )
        ws = _make_workflow_scores()
        agentic = score_agentic_item(
            item_name="Workflow task",
            category=OnetCategory.TASKS,
            recommended_mode=OperatingMode.BOUNDED_AUTONOMY,
            mode_rationale=".",
            workflow_scores=ws,
            exception_rate=0.05,
            takeover_cost=0.3,
            current_maturity=AgentMaturityLevel.LEVEL_3,
            agentic_ceiling=AgenticCeilingCategory.STANDARDIZED_BACKOFFICE,
            knowledge_work_type=KnowledgeWorkType.ROUTINE_COGNITIVE,
            stakes_level=StakesLevel.LOW,
            agentic_rationale=".",
        )
        adjusted = apply_agentic_adjustment(base, agentic)
        assert adjusted.time_saved_high_pct >= base.time_saved_high_pct
