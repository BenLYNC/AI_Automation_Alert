"""Scoring Engine — implements Steps A–I of the estimation methodology.

This module takes the raw LLM-generated per-item assessments and applies
the deterministic scoring pipeline: weighted subtask sums, reality
discounts, ceiling caps, and range generation.

The LLM produces qualitative assessments; this engine quantifies them.
"""

from __future__ import annotations

from collections import Counter
from datetime import datetime

from .models import (
    AutomationAlert,
    CategorySummary,
    CeilingCategory,
    CEILING_CAPS,
    DEFAULT_DISCOUNT_FACTORS,
    DiscountFactor,
    ExposureLevel,
    LEVERAGE_GAIN_RANGES,
    LeverageLevel,
    OnetCategory,
    ScoreDelta,
    ScoredItem,
    SubtaskBucket,
    SubtaskScore,
)


# ---------------------------------------------------------------------------
# Step D: Efficiency gain lookup
# ---------------------------------------------------------------------------

def get_efficiency_gain(leverage: LeverageLevel) -> tuple[float, float]:
    """Return (low, high) efficiency gain for a leverage level."""
    return LEVERAGE_GAIN_RANGES[leverage]


# ---------------------------------------------------------------------------
# Step E: Compute raw time-saved from subtask breakdown
# ---------------------------------------------------------------------------

def compute_raw_time_saved(subtasks: list[SubtaskScore]) -> tuple[float, float]:
    """Weighted sum: Σ(baseline_share × efficiency_gain) for low and high.

    Returns (raw_low, raw_high) as fractions (0.0–1.0).
    """
    raw_low = 0.0
    raw_high = 0.0
    for st in subtasks:
        raw_low += st.baseline_share_pct * st.efficiency_gain_low
        raw_high += st.baseline_share_pct * st.efficiency_gain_high
    return raw_low, raw_high


# ---------------------------------------------------------------------------
# Step F: Apply reality discounts
# ---------------------------------------------------------------------------

def compute_total_discount(factors: list[DiscountFactor] | None = None) -> float:
    """Combine discount factors into a single multiplier.

    Returns the total discount as a fraction (e.g. 0.20 = 20% haircut).
    Discounts are additive (capped at 0.50 to prevent over-penalizing).
    """
    if factors is None:
        factors = DEFAULT_DISCOUNT_FACTORS
    total = sum(f.discount_pct for f in factors)
    return min(total, 0.50)


def apply_discounts(
    raw_low: float,
    raw_high: float,
    total_discount: float,
) -> tuple[float, float]:
    """Adjusted Time Saved = Raw × (1 − Discount Factor).

    Low end gets full discount; high end gets half discount
    (to reflect that optimistic scenarios have less friction).
    """
    adjusted_low = raw_low * (1 - total_discount)
    adjusted_high = raw_high * (1 - total_discount * 0.5)
    return adjusted_low, adjusted_high


# ---------------------------------------------------------------------------
# Step H: Automation ceiling cap
# ---------------------------------------------------------------------------

def apply_ceiling(
    adjusted_low: float,
    adjusted_high: float,
    ceiling_cat: CeilingCategory,
) -> tuple[float, float]:
    """Cap estimates at the automation ceiling for the task's nature."""
    cap = CEILING_CAPS[ceiling_cat]
    return min(adjusted_low, cap), min(adjusted_high, cap)


# ---------------------------------------------------------------------------
# Full item-level scoring pipeline (Steps B–H combined)
# ---------------------------------------------------------------------------

def score_item(
    item_name: str,
    category: OnetCategory,
    exposure_levels: list[ExposureLevel],
    subtask_scores: list[SubtaskScore],
    ceiling_category: CeilingCategory,
    rationale: str,
    advancement_notes: str = "",
    discount_factors: list[DiscountFactor] | None = None,
    onet_element_id: str | None = None,
    importance: float | None = None,
    level: float | None = None,
) -> ScoredItem:
    """Run the full scoring pipeline for a single O*NET item."""

    # Step E: raw weighted sum
    raw_low, raw_high = compute_raw_time_saved(subtask_scores)

    # Step F: reality discounts
    factors = discount_factors or DEFAULT_DISCOUNT_FACTORS
    total_discount = compute_total_discount(factors)
    adj_low, adj_high = apply_discounts(raw_low, raw_high, total_discount)

    # Step H: ceiling cap
    final_low, final_high = apply_ceiling(adj_low, adj_high, ceiling_category)

    # Build exposure label string (e.g. "E2/E7")
    exposure_label = "/".join(e.value for e in exposure_levels)

    return ScoredItem(
        item_name=item_name,
        category=category,
        onet_element_id=onet_element_id,
        importance=importance,
        level=level,
        exposure_levels=exposure_levels,
        exposure_label=exposure_label,
        time_saved_low_pct=round(final_low * 100, 1),
        time_saved_high_pct=round(final_high * 100, 1),
        ceiling_category=ceiling_category,
        ceiling_cap_pct=round(CEILING_CAPS[ceiling_category] * 100, 1),
        subtask_scores=subtask_scores,
        discount_factors=factors,
        total_discount_pct=total_discount,
        rationale=rationale,
        advancement_notes=advancement_notes,
    )


# ---------------------------------------------------------------------------
# Category-level aggregation
# ---------------------------------------------------------------------------

def summarize_category(
    category: OnetCategory,
    items: list[ScoredItem],
) -> CategorySummary:
    """Aggregate item scores into a category summary."""
    if not items:
        return CategorySummary(
            category=category,
            item_count=0,
            avg_time_saved_low_pct=0.0,
            avg_time_saved_high_pct=0.0,
            dominant_exposure_vectors=[],
            exposure_vector_distribution={},
            items=[],
        )

    avg_low = sum(i.time_saved_low_pct for i in items) / len(items)
    avg_high = sum(i.time_saved_high_pct for i in items) / len(items)

    # Count exposure vectors across all items
    counter: Counter[ExposureLevel] = Counter()
    for item in items:
        for ev in item.exposure_levels:
            counter[ev] += 1

    # Top 3 dominant vectors
    dominant = [ev for ev, _ in counter.most_common(3)]

    return CategorySummary(
        category=category,
        item_count=len(items),
        avg_time_saved_low_pct=round(avg_low, 1),
        avg_time_saved_high_pct=round(avg_high, 1),
        dominant_exposure_vectors=dominant,
        exposure_vector_distribution={ev.value: count for ev, count in counter.items()},
        items=items,
    )


# ---------------------------------------------------------------------------
# Occupation-level composite (the full Automation Alert)
# ---------------------------------------------------------------------------

# Weights for each category in the overall composite score.
# Tasks and Work Activities carry the most weight since they represent
# the actual work being done.
CATEGORY_WEIGHTS: dict[OnetCategory, float] = {
    OnetCategory.TASKS: 0.25,
    OnetCategory.WORK_ACTIVITIES: 0.20,
    OnetCategory.SKILLS: 0.15,
    OnetCategory.TECHNOLOGY_SKILLS: 0.12,
    OnetCategory.KNOWLEDGE: 0.08,
    OnetCategory.ABILITIES: 0.07,
    OnetCategory.DETAILED_WORK_ACTIVITIES: 0.05,
    OnetCategory.WORK_CONTEXT: 0.04,
    OnetCategory.WORK_STYLES: 0.04,
}


def build_automation_alert(
    soc_code: str,
    occupation_title: str,
    category_summaries: list[CategorySummary],
    deltas: list[ScoreDelta] | None = None,
) -> AutomationAlert:
    """Build the top-level AutomationAlert from scored category summaries."""

    # Weighted composite
    weighted_low = 0.0
    weighted_high = 0.0
    total_weight = 0.0
    all_exposure_vectors: Counter[ExposureLevel] = Counter()

    for cs in category_summaries:
        w = CATEGORY_WEIGHTS.get(cs.category, 0.05)
        weighted_low += cs.avg_time_saved_low_pct * w
        weighted_high += cs.avg_time_saved_high_pct * w
        total_weight += w
        for ev in cs.dominant_exposure_vectors:
            all_exposure_vectors[ev] += 1

    if total_weight > 0:
        weighted_low /= total_weight
        weighted_high /= total_weight

    dominant = [ev for ev, _ in all_exposure_vectors.most_common(3)]

    alert = AutomationAlert(
        soc_code=soc_code,
        occupation_title=occupation_title,
        overall_time_saved_low_pct=round(weighted_low, 1),
        overall_time_saved_high_pct=round(weighted_high, 1),
        overall_automation_risk_label="",  # filled below
        dominant_exposure_vectors=dominant,
        category_summaries=category_summaries,
        deltas=deltas or [],
    )
    alert.overall_automation_risk_label = alert.risk_label()
    return alert


# ---------------------------------------------------------------------------
# Delta computation
# ---------------------------------------------------------------------------

def compute_delta(
    previous: ScoredItem,
    current: ScoredItem,
    change_reason: str,
) -> ScoreDelta:
    """Compare two evaluations of the same item and produce a delta record."""
    return ScoreDelta(
        item_name=current.item_name,
        category=current.category,
        previous_time_saved_low=previous.time_saved_low_pct,
        previous_time_saved_high=previous.time_saved_high_pct,
        current_time_saved_low=current.time_saved_low_pct,
        current_time_saved_high=current.time_saved_high_pct,
        delta_low=round(current.time_saved_low_pct - previous.time_saved_low_pct, 1),
        delta_high=round(current.time_saved_high_pct - previous.time_saved_high_pct, 1),
        previous_exposure=previous.exposure_levels,
        current_exposure=current.exposure_levels,
        change_reason=change_reason,
        evaluated_at=datetime.utcnow(),
    )
