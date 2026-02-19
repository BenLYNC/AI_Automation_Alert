"""Agentic Impact Layer — dedicated assessment of AI agent capabilities
on cognitive/knowledge work.

Implements the full agentic scoring methodology:
  A) Operating Modes (0–3)
  B) Agent-ready workflow unit decomposition (W1–W7)
  C) Agentic Suitability scoring (AS 0–3)
  D) Execution Automation (EA) vs. Oversight Tax (OT)
  E) Raw agentic time saved (weighted sum + compounding bonus)
  F) Agent-specific reality discounts (exception rate × takeover cost)
  G) Maturity-based range generation (Levels 1–4)
  H) Hard ceilings for agentic automation
  I) Advancement pathway identification

This is layered ON TOP of the base E0-E11 scoring, not a replacement.
"""

from __future__ import annotations

import enum

from pydantic import BaseModel, Field

from .models import ExposureLevel, OnetCategory, ScoredItem


# ---------------------------------------------------------------------------
# Step A: Operating Modes
# ---------------------------------------------------------------------------

class OperatingMode(int, enum.Enum):
    """Agent operating mode — defines autonomy level."""

    COPILOT = 0          # Drafts steps, human executes
    ASSISTED = 1         # Agent executes after explicit approval per step
    BOUNDED_AUTONOMY = 2  # Agent executes within guardrails (policies, limits)
    FULL_AUTONOMY = 3    # Agent executes end-to-end; human audits exceptions


OPERATING_MODE_LABELS: dict[OperatingMode, str] = {
    OperatingMode.COPILOT: "Mode 0 — Copilot (non-agentic): drafts steps, human executes",
    OperatingMode.ASSISTED: "Mode 1 — Assisted execution: agent executes after explicit approval per step",
    OperatingMode.BOUNDED_AUTONOMY: "Mode 2 — Bounded autonomy: agent executes within guardrails",
    OperatingMode.FULL_AUTONOMY: "Mode 3 — Full autonomy: agent executes end-to-end, human audits exceptions",
}


# ---------------------------------------------------------------------------
# Step B: Agent-Ready Workflow Units (W1–W7)
# ---------------------------------------------------------------------------

class WorkflowUnit(str, enum.Enum):
    """Universal agent-ready workflow unit decomposition."""

    W1_INTAKE_TRIAGE = "intake_triage"
    W2_INFO_RETRIEVAL = "info_retrieval"
    W3_PLANNING = "planning"
    W4_TOOL_ACTIONS = "tool_actions"
    W5_VERIFICATION_QA = "verification_qa"
    W6_APPROVALS_COMPLIANCE = "approvals_compliance"
    W7_EXCEPTIONS_HUMAN_ONLY = "exceptions_human_only"


WORKFLOW_UNIT_LABELS: dict[WorkflowUnit, str] = {
    WorkflowUnit.W1_INTAKE_TRIAGE: "W1: Intake & triage (read request, classify, route)",
    WorkflowUnit.W2_INFO_RETRIEVAL: "W2: Info retrieval (search systems, pull data, open docs)",
    WorkflowUnit.W3_PLANNING: "W3: Planning (decide steps, dependencies, schedule)",
    WorkflowUnit.W4_TOOL_ACTIONS: "W4: Tool actions (create/update/send/schedule/upload/submit)",
    WorkflowUnit.W5_VERIFICATION_QA: "W5: Verification & QA (confirm correct, reconcile inconsistencies)",
    WorkflowUnit.W6_APPROVALS_COMPLIANCE: "W6: Approvals & compliance (policy checks, approvals, audit notes)",
    WorkflowUnit.W7_EXCEPTIONS_HUMAN_ONLY: "W7: Exceptions / human-only (judgment calls, relationship, physical)",
}


# ---------------------------------------------------------------------------
# Step C: Agentic Suitability (AS) Rating
# ---------------------------------------------------------------------------

class AgenticSuitability(int, enum.Enum):
    """How suitable a workflow unit is for agentic execution (0–3)."""

    NOT_SUITABLE = 0     # High ambiguity, physical, deeply relational
    PARTIALLY = 1        # Some actions possible; many checks required
    MOSTLY = 2           # Clear rules + structured inputs
    HIGHLY = 3           # Repeatable, standardized, machine-checkable


AS_DRIVERS: list[str] = [
    "Structured inputs (forms, schemas)",
    "Stable rules (SOPs)",
    "Accessible systems (APIs, permissions)",
    "Clear success criteria (tests, reconciliations)",
]


# ---------------------------------------------------------------------------
# Step D: Execution Automation (EA) and Oversight Tax (OT) Ranges
# ---------------------------------------------------------------------------

# EA ranges by operating mode
EA_RANGES: dict[OperatingMode, tuple[float, float]] = {
    OperatingMode.COPILOT: (0.0, 0.10),       # Non-agentic, just suggesting
    OperatingMode.ASSISTED: (0.10, 0.30),      # Manual approvals, weak integration
    OperatingMode.BOUNDED_AUTONOMY: (0.30, 0.60),  # Good integrations, strong SOPs
    OperatingMode.FULL_AUTONOMY: (0.60, 0.85),     # Highly structured, machine-verifiable
}

# OT ranges by stakes level
class StakesLevel(str, enum.Enum):
    LOW = "low"           # 5-15% oversight tax
    MEDIUM = "medium"     # 10-25% oversight tax
    HIGH = "high"         # 20-50% oversight tax (money, legal, safety)


OT_RANGES: dict[StakesLevel, tuple[float, float]] = {
    StakesLevel.LOW: (0.05, 0.15),
    StakesLevel.MEDIUM: (0.10, 0.25),
    StakesLevel.HIGH: (0.20, 0.50),
}


# ---------------------------------------------------------------------------
# Step G: Agent Maturity Model
# ---------------------------------------------------------------------------

class AgentMaturityLevel(int, enum.Enum):
    """Agent implementation maturity level."""

    LEVEL_1 = 1  # Scripted agent (narrow, brittle)
    LEVEL_2 = 2  # Tool-integrated agent (APIs, reliable actions)
    LEVEL_3 = 3  # Policy-governed agent (guardrails, audit, rollbacks)
    LEVEL_4 = 4  # Self-healing agent (detects failures, retries safely, escalates)


MATURITY_LABELS: dict[AgentMaturityLevel, str] = {
    AgentMaturityLevel.LEVEL_1: "Level 1: Scripted agent (narrow, brittle)",
    AgentMaturityLevel.LEVEL_2: "Level 2: Tool-integrated agent (APIs, reliable actions)",
    AgentMaturityLevel.LEVEL_3: "Level 3: Policy-governed agent (guardrails, audit, rollbacks)",
    AgentMaturityLevel.LEVEL_4: "Level 4: Self-healing agent (detects failures, retries, escalates)",
}

# Net time-saved bands by maturity level (for workflow-heavy tasks)
MATURITY_TIME_SAVED_BANDS: dict[AgentMaturityLevel, tuple[float, float]] = {
    AgentMaturityLevel.LEVEL_1: (0.10, 0.25),
    AgentMaturityLevel.LEVEL_2: (0.20, 0.45),
    AgentMaturityLevel.LEVEL_3: (0.30, 0.60),
    AgentMaturityLevel.LEVEL_4: (0.45, 0.75),
}


# ---------------------------------------------------------------------------
# Step H: Agentic Hard Ceilings
# ---------------------------------------------------------------------------

class AgenticCeilingCategory(str, enum.Enum):
    """Hard ceiling categories specific to agentic automation."""

    REGULATED_SIGNOFFS = "regulated_signoffs"       # ≤50%
    HIGH_TOUCH_RELATIONSHIP = "high_touch_relationship"  # ≤30%
    PHYSICAL_EXECUTION = "physical_execution"       # ≤10-20%
    UNSTRUCTURED_BESPOKE = "unstructured_bespoke"   # ≤25-40%
    STANDARDIZED_BACKOFFICE = "standardized_backoffice"  # ≥60%


AGENTIC_CEILING_CAPS: dict[AgenticCeilingCategory, float] = {
    AgenticCeilingCategory.REGULATED_SIGNOFFS: 0.50,
    AgenticCeilingCategory.HIGH_TOUCH_RELATIONSHIP: 0.30,
    AgenticCeilingCategory.PHYSICAL_EXECUTION: 0.15,
    AgenticCeilingCategory.UNSTRUCTURED_BESPOKE: 0.32,
    AgenticCeilingCategory.STANDARDIZED_BACKOFFICE: 0.80,
}


# ---------------------------------------------------------------------------
# Step I: Advancement Drivers
# ---------------------------------------------------------------------------

ADVANCEMENT_DRIVERS: list[str] = [
    "Standardize inputs: forms, required fields, templates",
    "Define SOPs & policies: 'if X then Y' playbooks",
    "Tool integration: APIs > RPA/UI clicking",
    "Add verification hooks: tests, reconciliations, checklists",
    "Reduce exception rates: better data, clearer rules",
    "Add safe rollback: undo actions, versioning, audit logs",
    "Guardrails: spend limits, approval gates, allowed actions",
]


# ---------------------------------------------------------------------------
# Knowledge Work Impact Classification
# ---------------------------------------------------------------------------

class KnowledgeWorkType(str, enum.Enum):
    """Classification of the cognitive nature of the work element."""

    ROUTINE_COGNITIVE = "routine_cognitive"
    COMPLEX_COGNITIVE = "complex_cognitive"
    CREATIVE_COGNITIVE = "creative_cognitive"
    INTERPERSONAL_COGNITIVE = "interpersonal_cognitive"
    PHYSICAL_MANUAL = "physical_manual"


KNOWLEDGE_WORK_AGENTIC_AFFINITY: dict[KnowledgeWorkType, float] = {
    KnowledgeWorkType.ROUTINE_COGNITIVE: 0.85,
    KnowledgeWorkType.COMPLEX_COGNITIVE: 0.55,
    KnowledgeWorkType.CREATIVE_COGNITIVE: 0.40,
    KnowledgeWorkType.INTERPERSONAL_COGNITIVE: 0.25,
    KnowledgeWorkType.PHYSICAL_MANUAL: 0.05,
}


# ---------------------------------------------------------------------------
# Scored Models (per-item agentic assessment)
# ---------------------------------------------------------------------------

class WorkflowUnitScore(BaseModel):
    """Score for a single workflow unit (W1-W7) within an item."""

    unit: WorkflowUnit
    time_share_pct: float = Field(ge=0, le=1, description="Share of total task time (sums to 1.0)")
    agentic_suitability: AgenticSuitability = Field(description="AS rating 0-3")
    execution_automation_pct: float = Field(ge=0, le=1, description="EA: % of unit time agent removes")
    oversight_tax_pct: float = Field(ge=0, le=1, description="OT: extra time for supervision")
    net_gain_pct: float = Field(description="EA - OT for this unit")
    rationale: str


class AgenticImpactScore(BaseModel):
    """Full agentic impact assessment for a single O*NET item."""

    item_name: str
    category: OnetCategory

    # Step A: Operating mode
    recommended_mode: OperatingMode
    mode_rationale: str

    # Step B-D: Workflow unit breakdown
    workflow_scores: list[WorkflowUnitScore]

    # Step E: Raw agentic time saved
    raw_agentic_time_saved_pct: float = Field(ge=0, le=100)
    workflow_compounding_bonus_pct: float = Field(
        ge=0, le=15,
        description="Bonus for eliminating between-step overhead (+3 to +15 points)",
    )

    # Step F: Reality discounts
    exception_rate_pct: float = Field(
        ge=0, le=100,
        description="% of cases requiring human takeover",
    )
    takeover_cost_pct: float = Field(
        ge=0, le=100,
        description="% of full task time consumed when takeover happens",
    )
    adjusted_agentic_time_saved_pct: float = Field(ge=0, le=100)

    # Step G: Maturity-based range
    current_maturity: AgentMaturityLevel
    time_saved_low_pct: float = Field(ge=0, le=100)
    time_saved_high_pct: float = Field(ge=0, le=100)

    # Step H: Ceiling
    agentic_ceiling: AgenticCeilingCategory
    ceiling_cap_pct: float = Field(ge=0, le=100)
    final_time_saved_low_pct: float = Field(ge=0, le=100)
    final_time_saved_high_pct: float = Field(ge=0, le=100)

    # Knowledge work classification
    knowledge_work_type: KnowledgeWorkType
    cognitive_displacement_pct: float = Field(ge=0, le=100)

    # Stakes assessment
    stakes_level: StakesLevel

    # Rationale and projections
    agentic_rationale: str
    advancement_notes: str = Field(
        default="",
        description="What environmental changes would increase agentic savings (Step I)",
    )
    near_term_projection: str = Field(
        default="",
        description="How agentic capabilities are expected to evolve (1-3 years)",
    )


# ---------------------------------------------------------------------------
# Computation: Steps E-H
# ---------------------------------------------------------------------------

def compute_raw_agentic_time_saved(
    workflow_scores: list[WorkflowUnitScore],
) -> float:
    """Step E: Weighted sum of net gains across workflow units.

    Raw Agentic Time Saved (%) = Σ [ UnitShare × (EA − OT) ]
    """
    total = sum(ws.time_share_pct * ws.net_gain_pct for ws in workflow_scores)
    return round(max(total * 100, 0.0), 1)


def apply_compounding_bonus(
    raw_pct: float,
    workflow_scores: list[WorkflowUnitScore],
) -> tuple[float, float]:
    """Step E (cont): Add workflow compounding bonus if agent carries state across tools.

    Bonus = +3 to +15 points based on how many workflow units have AS >= 2
    (indicating the agent can carry state across them).
    """
    high_as_count = sum(1 for ws in workflow_scores if ws.agentic_suitability.value >= 2)
    total_units = len(workflow_scores)

    if total_units == 0:
        return raw_pct, 0.0

    ratio = high_as_count / total_units
    bonus = round(3 + (ratio * 12), 1)  # 3-15 range
    return round(raw_pct + bonus, 1), bonus


def apply_agentic_discounts(
    adjusted_pct: float,
    exception_rate: float,
    takeover_cost: float,
) -> float:
    """Step F: Apply agent-specific reality discounts.

    Adjusted Savings = Raw Savings − (ER × TC)
    """
    penalty = exception_rate * takeover_cost * 100
    return round(max(adjusted_pct - penalty, 0.0), 1)


def compute_maturity_range(
    adjusted_pct: float,
    maturity: AgentMaturityLevel,
) -> tuple[float, float]:
    """Step G: Generate low-high range based on agent maturity level."""
    band_low, band_high = MATURITY_TIME_SAVED_BANDS[maturity]

    # Scale the bands by the adjusted estimate
    # The maturity bands act as multipliers on the task-specific estimate
    low = adjusted_pct * (band_low / 0.50)   # Normalize around 50% midpoint
    high = adjusted_pct * (band_high / 0.50)

    return round(max(low, 0.0), 1), round(min(high, 100.0), 1)


def apply_agentic_ceiling(
    low_pct: float,
    high_pct: float,
    ceiling: AgenticCeilingCategory,
) -> tuple[float, float]:
    """Step H: Cap estimates at agentic automation ceiling."""
    cap = AGENTIC_CEILING_CAPS[ceiling] * 100
    return min(low_pct, cap), min(high_pct, cap)


def compute_cognitive_displacement(
    knowledge_work_type: KnowledgeWorkType,
    mode: OperatingMode,
    final_time_saved_high: float,
) -> float:
    """Estimate cognitive effort displacement.

    Combines work type affinity with the operating mode and final savings.
    """
    affinity = KNOWLEDGE_WORK_AGENTIC_AFFINITY[knowledge_work_type]
    mode_factor = 0.5 + (mode.value * 0.15)  # 0.5, 0.65, 0.80, 0.95
    raw = (final_time_saved_high / 100) * affinity * mode_factor * 100
    return round(min(raw, 90.0), 1)


# ---------------------------------------------------------------------------
# Full agentic scoring pipeline
# ---------------------------------------------------------------------------

def score_agentic_item(
    item_name: str,
    category: OnetCategory,
    recommended_mode: OperatingMode,
    mode_rationale: str,
    workflow_scores: list[WorkflowUnitScore],
    exception_rate: float,
    takeover_cost: float,
    current_maturity: AgentMaturityLevel,
    agentic_ceiling: AgenticCeilingCategory,
    knowledge_work_type: KnowledgeWorkType,
    stakes_level: StakesLevel,
    agentic_rationale: str,
    advancement_notes: str = "",
    near_term_projection: str = "",
) -> AgenticImpactScore:
    """Run the full agentic scoring pipeline for a single item."""

    # Step E: raw time saved
    raw_pct = compute_raw_agentic_time_saved(workflow_scores)
    with_bonus, bonus = apply_compounding_bonus(raw_pct, workflow_scores)

    # Step F: reality discounts
    adjusted_pct = apply_agentic_discounts(with_bonus, exception_rate, takeover_cost)

    # Step G: maturity range
    low_pct, high_pct = compute_maturity_range(adjusted_pct, current_maturity)

    # Step H: ceiling cap
    final_low, final_high = apply_agentic_ceiling(low_pct, high_pct, agentic_ceiling)
    ceiling_cap = AGENTIC_CEILING_CAPS[agentic_ceiling] * 100

    # Cognitive displacement
    cog_disp = compute_cognitive_displacement(knowledge_work_type, recommended_mode, final_high)

    return AgenticImpactScore(
        item_name=item_name,
        category=category,
        recommended_mode=recommended_mode,
        mode_rationale=mode_rationale,
        workflow_scores=workflow_scores,
        raw_agentic_time_saved_pct=raw_pct,
        workflow_compounding_bonus_pct=bonus,
        exception_rate_pct=exception_rate * 100,
        takeover_cost_pct=takeover_cost * 100,
        adjusted_agentic_time_saved_pct=adjusted_pct,
        current_maturity=current_maturity,
        time_saved_low_pct=low_pct,
        time_saved_high_pct=high_pct,
        agentic_ceiling=agentic_ceiling,
        ceiling_cap_pct=ceiling_cap,
        final_time_saved_low_pct=final_low,
        final_time_saved_high_pct=final_high,
        knowledge_work_type=knowledge_work_type,
        cognitive_displacement_pct=cog_disp,
        stakes_level=stakes_level,
        agentic_rationale=agentic_rationale,
        advancement_notes=advancement_notes,
        near_term_projection=near_term_projection,
    )


# ---------------------------------------------------------------------------
# Integration with base scoring
# ---------------------------------------------------------------------------

def apply_agentic_adjustment(
    base_item: ScoredItem,
    agentic_score: AgenticImpactScore,
) -> ScoredItem:
    """Adjust a base ScoredItem's time-saved estimates based on agentic impact.

    The agentic layer can increase time-saved estimates when the item has
    significant agentic potential. The adjustment is the delta between
    base and agentic estimates, applied as an uplift.
    """
    has_agentic = ExposureLevel.E9 in base_item.exposure_levels
    if not has_agentic and agentic_score.final_time_saved_high_pct < 10:
        return base_item

    # Use the higher of base or agentic estimates
    new_low = max(base_item.time_saved_low_pct, agentic_score.final_time_saved_low_pct)
    new_high = max(base_item.time_saved_high_pct, agentic_score.final_time_saved_high_pct)

    # Still respect the base item's automation ceiling
    ceiling_pct = base_item.ceiling_cap_pct
    new_low = min(new_low, ceiling_pct)
    new_high = min(new_high, ceiling_pct)

    return base_item.model_copy(update={
        "time_saved_low_pct": round(new_low, 1),
        "time_saved_high_pct": round(new_high, 1),
    })
