"""Tests for the deterministic scoring engine (Steps A-I)."""

from __future__ import annotations

import pytest

from automation_alert.models import (
    CeilingCategory,
    CEILING_CAPS,
    DiscountFactor,
    ExposureLevel,
    LeverageLevel,
    OnetCategory,
    SubtaskBucket,
    SubtaskScore,
)
from automation_alert.scoring_engine import (
    apply_ceiling,
    apply_discounts,
    build_automation_alert,
    compute_delta,
    compute_raw_time_saved,
    compute_total_discount,
    score_item,
    summarize_category,
)


# ---------------------------------------------------------------------------
# Step D/E: Efficiency gains
# ---------------------------------------------------------------------------


class TestComputeRawTimeSaved:
    def test_single_subtask(self):
        subtasks = [
            SubtaskScore(
                bucket=SubtaskBucket.TRANSFORMATION_DRAFTING,
                baseline_share_pct=1.0,
                exposure_levels=[ExposureLevel.E1],
                leverage_level=LeverageLevel.HIGH,
                efficiency_gain_low=0.50,
                efficiency_gain_high=0.80,
            ),
        ]
        low, high = compute_raw_time_saved(subtasks)
        assert low == pytest.approx(0.50)
        assert high == pytest.approx(0.80)

    def test_weighted_sum(self):
        subtasks = [
            SubtaskScore(
                bucket=SubtaskBucket.INPUT_GATHERING,
                baseline_share_pct=0.5,
                exposure_levels=[],
                leverage_level=LeverageLevel.MEDIUM,
                efficiency_gain_low=0.20,
                efficiency_gain_high=0.40,
            ),
            SubtaskScore(
                bucket=SubtaskBucket.HUMAN_ONLY_EXECUTION,
                baseline_share_pct=0.5,
                exposure_levels=[],
                leverage_level=LeverageLevel.LOW,
                efficiency_gain_low=0.0,
                efficiency_gain_high=0.10,
            ),
        ]
        low, high = compute_raw_time_saved(subtasks)
        assert low == pytest.approx(0.10)
        assert high == pytest.approx(0.25)

    def test_empty_returns_zero(self):
        assert compute_raw_time_saved([]) == (0.0, 0.0)


# ---------------------------------------------------------------------------
# Step F: Reality discounts
# ---------------------------------------------------------------------------


class TestDiscounts:
    def test_default_discount(self):
        total = compute_total_discount()
        assert total == pytest.approx(0.20)

    def test_custom_factors(self):
        factors = [
            DiscountFactor(name="Big risk", description="", discount_pct=0.30),
            DiscountFactor(name="Another", description="", discount_pct=0.30),
        ]
        total = compute_total_discount(factors)
        assert total == pytest.approx(0.50)  # Capped at 0.50

    def test_apply_discounts(self):
        adj_low, adj_high = apply_discounts(0.50, 0.80, 0.20)
        assert adj_low == pytest.approx(0.40)
        assert adj_high == pytest.approx(0.72)


# ---------------------------------------------------------------------------
# Step H: Ceiling caps
# ---------------------------------------------------------------------------


class TestCeiling:
    def test_caps_at_ceiling(self):
        cap = CEILING_CAPS[CeilingCategory.PHYSICAL_EXECUTION]  # 0.25
        low, high = apply_ceiling(0.30, 0.50, CeilingCategory.PHYSICAL_EXECUTION)
        assert low == cap
        assert high == cap

    def test_below_ceiling_unchanged(self):
        low, high = apply_ceiling(0.10, 0.20, CeilingCategory.PURE_DRAFTING)
        assert low == pytest.approx(0.10)
        assert high == pytest.approx(0.20)


# ---------------------------------------------------------------------------
# Full item scoring pipeline
# ---------------------------------------------------------------------------


class TestScoreItem:
    def test_produces_valid_scored_item(self):
        subtasks = [
            SubtaskScore(
                bucket=SubtaskBucket.TRANSFORMATION_DRAFTING,
                baseline_share_pct=0.6,
                exposure_levels=[ExposureLevel.E1],
                leverage_level=LeverageLevel.HIGH,
                efficiency_gain_low=0.55,
                efficiency_gain_high=0.75,
            ),
            SubtaskScore(
                bucket=SubtaskBucket.HUMAN_ONLY_EXECUTION,
                baseline_share_pct=0.4,
                exposure_levels=[],
                leverage_level=LeverageLevel.LOW,
                efficiency_gain_low=0.0,
                efficiency_gain_high=0.05,
            ),
        ]
        item = score_item(
            item_name="Draft marketing copy",
            category=OnetCategory.TASKS,
            exposure_levels=[ExposureLevel.E1],
            subtask_scores=subtasks,
            ceiling_category=CeilingCategory.PURE_DRAFTING,
            rationale="Direct LLM exposure for drafting.",
        )
        assert item.item_name == "Draft marketing copy"
        assert item.exposure_label == "E1"
        assert 0 <= item.time_saved_low_pct <= item.time_saved_high_pct <= 100
        assert item.ceiling_cap_pct == pytest.approx(85.0)
        assert item.total_discount_pct > 0

    def test_multi_vector_exposure_label(self):
        subtasks = [
            SubtaskScore(
                bucket=SubtaskBucket.ANALYSIS_PLANNING,
                baseline_share_pct=1.0,
                exposure_levels=[],
                leverage_level=LeverageLevel.MEDIUM,
                efficiency_gain_low=0.20,
                efficiency_gain_high=0.40,
            ),
        ]
        item = score_item(
            item_name="Market analysis",
            category=OnetCategory.TASKS,
            exposure_levels=[ExposureLevel.E2, ExposureLevel.E7],
            subtask_scores=subtasks,
            ceiling_category=CeilingCategory.HIGH_STAKES_COMPLIANCE,
            rationale="Multi-vector.",
        )
        assert item.exposure_label == "E2/E7"


# ---------------------------------------------------------------------------
# Category summary
# ---------------------------------------------------------------------------


class TestSummarizeCategory:
    def test_empty_category(self):
        summary = summarize_category(OnetCategory.TASKS, [])
        assert summary.item_count == 0
        assert summary.avg_time_saved_low_pct == 0.0

    def test_with_items(self):
        subtasks = [
            SubtaskScore(
                bucket=SubtaskBucket.TRANSFORMATION_DRAFTING,
                baseline_share_pct=1.0,
                exposure_levels=[ExposureLevel.E1],
                leverage_level=LeverageLevel.HIGH,
                efficiency_gain_low=0.50,
                efficiency_gain_high=0.80,
            ),
        ]
        item1 = score_item(
            item_name="A", category=OnetCategory.TASKS,
            exposure_levels=[ExposureLevel.E1],
            subtask_scores=subtasks,
            ceiling_category=CeilingCategory.PURE_DRAFTING,
            rationale=".",
        )
        item2 = score_item(
            item_name="B", category=OnetCategory.TASKS,
            exposure_levels=[ExposureLevel.E2],
            subtask_scores=subtasks,
            ceiling_category=CeilingCategory.PURE_DRAFTING,
            rationale=".",
        )
        summary = summarize_category(OnetCategory.TASKS, [item1, item2])
        assert summary.item_count == 2
        assert summary.avg_time_saved_low_pct > 0
        assert ExposureLevel.E1 in summary.dominant_exposure_vectors


# ---------------------------------------------------------------------------
# Build automation alert
# ---------------------------------------------------------------------------


class TestBuildAutomationAlert:
    def test_alert_risk_label(self):
        subtasks = [
            SubtaskScore(
                bucket=SubtaskBucket.TRANSFORMATION_DRAFTING,
                baseline_share_pct=1.0,
                exposure_levels=[],
                leverage_level=LeverageLevel.HIGH,
                efficiency_gain_low=0.55,
                efficiency_gain_high=0.75,
            ),
        ]
        item = score_item(
            item_name="X", category=OnetCategory.TASKS,
            exposure_levels=[ExposureLevel.E1],
            subtask_scores=subtasks,
            ceiling_category=CeilingCategory.PURE_DRAFTING,
            rationale=".",
        )
        summary = summarize_category(OnetCategory.TASKS, [item])
        alert = build_automation_alert(
            soc_code="99-0000.00",
            occupation_title="Test Occupation",
            category_summaries=[summary],
        )
        assert alert.soc_code == "99-0000.00"
        assert alert.overall_automation_risk_label in {
            "Low", "Moderate", "Significant", "High", "Very High"
        }
        assert alert.overall_midpoint_pct >= 0


# ---------------------------------------------------------------------------
# Delta computation
# ---------------------------------------------------------------------------


class TestComputeDelta:
    def test_delta_values(self):
        subtasks = [
            SubtaskScore(
                bucket=SubtaskBucket.TRANSFORMATION_DRAFTING,
                baseline_share_pct=1.0,
                exposure_levels=[],
                leverage_level=LeverageLevel.MEDIUM,
                efficiency_gain_low=0.20,
                efficiency_gain_high=0.40,
            ),
        ]
        old = score_item(
            item_name="A", category=OnetCategory.TASKS,
            exposure_levels=[ExposureLevel.E1],
            subtask_scores=subtasks,
            ceiling_category=CeilingCategory.HIGH_STAKES_COMPLIANCE,
            rationale=".",
        )
        # Make a "newer" version with higher gains
        subtasks_new = [
            SubtaskScore(
                bucket=SubtaskBucket.TRANSFORMATION_DRAFTING,
                baseline_share_pct=1.0,
                exposure_levels=[],
                leverage_level=LeverageLevel.HIGH,
                efficiency_gain_low=0.50,
                efficiency_gain_high=0.70,
            ),
        ]
        new = score_item(
            item_name="A", category=OnetCategory.TASKS,
            exposure_levels=[ExposureLevel.E1, ExposureLevel.E7],
            subtask_scores=subtasks_new,
            ceiling_category=CeilingCategory.HIGH_STAKES_COMPLIANCE,
            rationale=".",
        )
        delta = compute_delta(old, new, "Better tooling")
        assert delta.delta_low >= 0
        assert delta.delta_high >= 0
        assert delta.change_reason == "Better tooling"
