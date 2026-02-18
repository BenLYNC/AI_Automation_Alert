"""Core data models for the Automation Alert system.

Encodes the E0–E11 exposure taxonomy, subtask decomposition,
scoring methodology (steps A–I), and all O*NET attribute categories.
"""

from __future__ import annotations

import enum
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# E0–E11 Exposure Level Taxonomy
# ---------------------------------------------------------------------------

class ExposureLevel(str, enum.Enum):
    """AI/automation capability vector that creates exposure for a work element."""

    E0 = "E0"    # No exposure
    E1 = "E1"    # Direct LLM exposure (drafting, rewriting, ideation, summarization)
    E2 = "E2"    # LLM-powered applications (CRM, ticketing, docs, databases)
    E3 = "E3"    # Image capabilities
    E4 = "E4"    # Video capabilities
    E5 = "E5"    # Audio capabilities
    E6 = "E6"    # Voice capabilities
    E7 = "E7"    # Advanced reasoning (scenario planning, complex synthesis)
    E8 = "E8"    # Persuasion capabilities (tailored messaging, negotiation)
    E9 = "E9"    # Digital world action capabilities (AI Agents)
    E10 = "E10"  # Physical world vision capabilities (AI Vision Devices)
    E11 = "E11"  # Physical world action capabilities (Humanoid Robots)


EXPOSURE_LABELS: dict[ExposureLevel, str] = {
    ExposureLevel.E0: "No exposure",
    ExposureLevel.E1: "Direct LLM exposure",
    ExposureLevel.E2: "LLM-powered applications",
    ExposureLevel.E3: "Image capabilities",
    ExposureLevel.E4: "Video capabilities",
    ExposureLevel.E5: "Audio capabilities",
    ExposureLevel.E6: "Voice capabilities",
    ExposureLevel.E7: "Advanced reasoning",
    ExposureLevel.E8: "Persuasion capabilities",
    ExposureLevel.E9: "Digital world action (AI Agents)",
    ExposureLevel.E10: "Physical world vision (AI Vision Devices)",
    ExposureLevel.E11: "Physical world action (Humanoid Robots)",
}


# ---------------------------------------------------------------------------
# O*NET Attribute Categories
# ---------------------------------------------------------------------------

class OnetCategory(str, enum.Enum):
    """Every scorable O*NET attribute category."""

    TASKS = "tasks"
    SKILLS = "skills"
    KNOWLEDGE = "knowledge"
    ABILITIES = "abilities"
    WORK_ACTIVITIES = "work_activities"
    DETAILED_WORK_ACTIVITIES = "detailed_work_activities"
    TECHNOLOGY_SKILLS = "technology_skills"
    WORK_CONTEXT = "work_context"
    WORK_STYLES = "work_styles"
    WORK_VALUES = "work_values"
    INTERESTS = "interests"
    JOB_ZONES = "job_zones"
    EDUCATION = "education"


# Categories that receive full exposure/time-saved scoring.
SCORABLE_CATEGORIES: list[OnetCategory] = [
    OnetCategory.TASKS,
    OnetCategory.SKILLS,
    OnetCategory.KNOWLEDGE,
    OnetCategory.ABILITIES,
    OnetCategory.WORK_ACTIVITIES,
    OnetCategory.DETAILED_WORK_ACTIVITIES,
    OnetCategory.TECHNOLOGY_SKILLS,
    OnetCategory.WORK_CONTEXT,
    OnetCategory.WORK_STYLES,
]


# ---------------------------------------------------------------------------
# Subtask Decomposition  (Step B)
# ---------------------------------------------------------------------------

class SubtaskBucket(str, enum.Enum):
    """Universal subtask decomposition buckets."""

    INPUT_GATHERING = "input_gathering"
    TRANSFORMATION_DRAFTING = "transformation_drafting"
    ANALYSIS_PLANNING = "analysis_planning"
    COORDINATION_WORKFLOW = "coordination_workflow"
    REVIEW_QA_COMPLIANCE = "review_qa_compliance"
    HUMAN_ONLY_EXECUTION = "human_only_execution"


SUBTASK_LABELS: dict[SubtaskBucket, str] = {
    SubtaskBucket.INPUT_GATHERING: "Input gathering (finding info, collecting docs, pulling data)",
    SubtaskBucket.TRANSFORMATION_DRAFTING: "Transformation / drafting (writing, summarizing, formatting)",
    SubtaskBucket.ANALYSIS_PLANNING: "Analysis / planning / decision support",
    SubtaskBucket.COORDINATION_WORKFLOW: "Coordination / workflow (scheduling, reminders, handoffs)",
    SubtaskBucket.REVIEW_QA_COMPLIANCE: "Review / QA / compliance (checking accuracy, approvals)",
    SubtaskBucket.HUMAN_ONLY_EXECUTION: "Human-only / real-world execution (physical, relationship)",
}


# ---------------------------------------------------------------------------
# Efficiency Gain Ranges  (Step D)
# ---------------------------------------------------------------------------

class LeverageLevel(str, enum.Enum):
    """How much leverage the LLM provides for a subtask."""

    HIGH = "high"          # Draft/transform: 50-80% reduction
    MEDIUM = "medium"      # Analysis/planning: 20-50% reduction
    LOW = "low"            # Relationship/physical: 0-20% reduction
    WORKFLOW_MANUAL = "workflow_manual"      # Manual copy/paste: 10-25%
    WORKFLOW_INTEGRATED = "workflow_integrated"  # Integrated E2: 25-50%
    WORKFLOW_AGENTIC = "workflow_agentic"    # Agentic E9: 40-70%


LEVERAGE_GAIN_RANGES: dict[LeverageLevel, tuple[float, float]] = {
    LeverageLevel.HIGH: (0.50, 0.80),
    LeverageLevel.MEDIUM: (0.20, 0.50),
    LeverageLevel.LOW: (0.00, 0.20),
    LeverageLevel.WORKFLOW_MANUAL: (0.10, 0.25),
    LeverageLevel.WORKFLOW_INTEGRATED: (0.25, 0.50),
    LeverageLevel.WORKFLOW_AGENTIC: (0.40, 0.70),
}


# ---------------------------------------------------------------------------
# Automation Ceiling Categories  (Step H)
# ---------------------------------------------------------------------------

class CeilingCategory(str, enum.Enum):
    """Hard ceiling on automation potential based on task nature."""

    PHYSICAL_EXECUTION = "physical_execution"    # Low ceiling
    HIGH_STAKES_COMPLIANCE = "high_stakes_compliance"  # Moderate ceiling
    RELATIONSHIP_PERSUASION = "relationship_persuasion"  # Moderate ceiling
    PURE_DRAFTING = "pure_drafting"  # High ceiling


CEILING_CAPS: dict[CeilingCategory, float] = {
    CeilingCategory.PHYSICAL_EXECUTION: 0.25,
    CeilingCategory.HIGH_STAKES_COMPLIANCE: 0.50,
    CeilingCategory.RELATIONSHIP_PERSUASION: 0.55,
    CeilingCategory.PURE_DRAFTING: 0.85,
}


# ---------------------------------------------------------------------------
# Reality Discount Factors  (Step F)
# ---------------------------------------------------------------------------

class DiscountFactor(BaseModel):
    """A single friction/risk factor that reduces raw time-saved estimates."""

    name: str = Field(description="Name of the discount factor")
    description: str = Field(description="Why this friction exists")
    discount_pct: float = Field(
        ge=0, le=1,
        description="Percentage reduction to apply (0.0–1.0)",
    )


DEFAULT_DISCOUNT_FACTORS: list[DiscountFactor] = [
    DiscountFactor(
        name="Verification tax",
        description="Fact-checking, hallucination risk",
        discount_pct=0.05,
    ),
    DiscountFactor(
        name="Compliance / liability",
        description="Must-read, must-approve steps",
        discount_pct=0.05,
    ),
    DiscountFactor(
        name="Tool friction",
        description="Copy/paste, poor integrations, context switching",
        discount_pct=0.05,
    ),
    DiscountFactor(
        name="Stakeholder delays",
        description="Approvals, external dependencies",
        discount_pct=0.03,
    ),
    DiscountFactor(
        name="Novelty / edge cases",
        description="Rare or complex situations",
        discount_pct=0.02,
    ),
]


# ---------------------------------------------------------------------------
# Scored Item Models  (the output of scoring pipeline)
# ---------------------------------------------------------------------------

class SubtaskScore(BaseModel):
    """Score for a single subtask bucket within an O*NET item."""

    bucket: SubtaskBucket
    baseline_share_pct: float = Field(
        ge=0, le=1,
        description="What % of total time this subtask consumes (shares sum to 1.0)",
    )
    exposure_levels: list[ExposureLevel] = Field(
        description="Which AI capability vectors apply",
    )
    leverage_level: LeverageLevel
    efficiency_gain_low: float = Field(ge=0, le=1)
    efficiency_gain_high: float = Field(ge=0, le=1)


class ScoredItem(BaseModel):
    """A single O*NET attribute (task, skill, etc.) with full automation scoring."""

    item_name: str = Field(description="The O*NET element name/description")
    category: OnetCategory
    onet_element_id: Optional[str] = Field(
        default=None,
        description="O*NET element ID if available",
    )
    importance: Optional[float] = Field(
        default=None,
        description="O*NET importance score (1-5) if available",
    )
    level: Optional[float] = Field(
        default=None,
        description="O*NET level score (1-7) if available",
    )

    # Exposure scoring
    exposure_levels: list[ExposureLevel] = Field(
        description="Primary exposure vectors for this item (can be multi-vector)",
    )
    exposure_label: str = Field(
        description="Human-readable exposure label, e.g. 'E2/E7'",
    )

    # Time saved (Step E-G)
    time_saved_low_pct: float = Field(
        ge=0, le=100,
        description="Conservative time-saved estimate (%)",
    )
    time_saved_high_pct: float = Field(
        ge=0, le=100,
        description="Optimistic time-saved estimate (%)",
    )

    # Automation ceiling (Step H)
    ceiling_category: CeilingCategory
    ceiling_cap_pct: float = Field(ge=0, le=100)

    # Methodology detail
    subtask_scores: list[SubtaskScore] = Field(
        default_factory=list,
        description="Subtask-level breakdown (Step B-D)",
    )
    discount_factors: list[DiscountFactor] = Field(
        default_factory=list,
        description="Reality discounts applied (Step F)",
    )
    total_discount_pct: float = Field(
        ge=0, le=1,
        description="Combined discount factor (Step F)",
    )

    # Rationale
    rationale: str = Field(
        description="Human-readable explanation of the scoring (Step A context)",
    )
    advancement_notes: str = Field(
        default="",
        description="How exposure could advance with better tooling (Step I)",
    )


# ---------------------------------------------------------------------------
# Category Summary
# ---------------------------------------------------------------------------

class CategorySummary(BaseModel):
    """Aggregate scores for one O*NET attribute category."""

    category: OnetCategory
    item_count: int
    avg_time_saved_low_pct: float
    avg_time_saved_high_pct: float
    dominant_exposure_vectors: list[ExposureLevel]
    exposure_vector_distribution: dict[str, int] = Field(
        description="Count of items per exposure level",
    )
    items: list[ScoredItem]


# ---------------------------------------------------------------------------
# Delta History  (for tracking changes over time)
# ---------------------------------------------------------------------------

class ScoreDelta(BaseModel):
    """Tracks how an item's score changed between evaluation periods."""

    item_name: str
    category: OnetCategory
    previous_time_saved_low: float
    previous_time_saved_high: float
    current_time_saved_low: float
    current_time_saved_high: float
    delta_low: float
    delta_high: float
    previous_exposure: list[ExposureLevel]
    current_exposure: list[ExposureLevel]
    change_reason: str = Field(description="What capability shift caused the change")
    evaluated_at: datetime


# ---------------------------------------------------------------------------
# Full Occupation Automation Alert  (the top-level output)
# ---------------------------------------------------------------------------

class AutomationAlert(BaseModel):
    """Complete automation exposure profile for a single O*NET occupation."""

    soc_code: str = Field(description="SOC/O*NET code, e.g. '41-9022.00'")
    occupation_title: str
    evaluated_at: datetime = Field(default_factory=datetime.utcnow)

    # Overall composites
    overall_time_saved_low_pct: float = Field(
        ge=0, le=100,
        description="Weighted composite low estimate across all categories",
    )
    overall_time_saved_high_pct: float = Field(
        ge=0, le=100,
        description="Weighted composite high estimate across all categories",
    )
    overall_automation_risk_label: str = Field(
        description="Human-readable risk label: Low / Moderate / Significant / High / Very High",
    )
    dominant_exposure_vectors: list[ExposureLevel] = Field(
        description="Top exposure vectors across all categories",
    )

    # Per-category breakdowns
    category_summaries: list[CategorySummary]

    # Delta history
    deltas: list[ScoreDelta] = Field(
        default_factory=list,
        description="Score changes since last evaluation",
    )

    # Methodology metadata
    methodology_version: str = Field(default="1.0")
    discount_factors_applied: list[DiscountFactor] = Field(
        default_factory=lambda: DEFAULT_DISCOUNT_FACTORS,
    )

    @property
    def overall_midpoint_pct(self) -> float:
        return (self.overall_time_saved_low_pct + self.overall_time_saved_high_pct) / 2

    def risk_label(self) -> str:
        mid = self.overall_midpoint_pct
        if mid < 10:
            return "Low"
        elif mid < 25:
            return "Moderate"
        elif mid < 40:
            return "Significant"
        elif mid < 60:
            return "High"
        else:
            return "Very High"
