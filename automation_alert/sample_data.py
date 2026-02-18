"""Sample data for demo/testing — Real Estate Sales Agents (41-9022.00).

Based on the user's example output to validate the pipeline end-to-end.
"""

from __future__ import annotations

from .models import (
    CeilingCategory,
    ExposureLevel,
    LeverageLevel,
    OnetCategory,
    SubtaskBucket,
    SubtaskScore,
)
from .scoring_engine import build_automation_alert, score_item, summarize_category


def _sample_tasks() -> list[dict]:
    """Return pre-scored task definitions matching the example output."""
    return [
        {
            "name": "Prospecting & lead list building (sphere, farming, online leads)",
            "exposure": [ExposureLevel.E2],
            "ceiling": CeilingCategory.RELATIONSHIP_PERSUASION,
            "subtasks": [
                (SubtaskBucket.INPUT_GATHERING, 0.25, LeverageLevel.MEDIUM, 0.30, 0.45),
                (SubtaskBucket.TRANSFORMATION_DRAFTING, 0.30, LeverageLevel.HIGH, 0.50, 0.70),
                (SubtaskBucket.ANALYSIS_PLANNING, 0.10, LeverageLevel.MEDIUM, 0.20, 0.35),
                (SubtaskBucket.COORDINATION_WORKFLOW, 0.15, LeverageLevel.WORKFLOW_INTEGRATED, 0.25, 0.40),
                (SubtaskBucket.REVIEW_QA_COMPLIANCE, 0.05, LeverageLevel.LOW, 0.05, 0.15),
                (SubtaskBucket.HUMAN_ONLY_EXECUTION, 0.15, LeverageLevel.LOW, 0.00, 0.10),
            ],
            "rationale": (
                "LLM-powered CRMs can draft outreach sequences, personalize messages "
                "by segment, and suggest follow-up timing; still needs agent judgment "
                "and relationship context."
            ),
            "advancement": "E2 → E9 when agents can autonomously manage drip sequences and respond to lead signals.",
        },
        {
            "name": "Initial client discovery (needs analysis, budget, timeline, motivation)",
            "exposure": [ExposureLevel.E7],
            "ceiling": CeilingCategory.RELATIONSHIP_PERSUASION,
            "subtasks": [
                (SubtaskBucket.INPUT_GATHERING, 0.20, LeverageLevel.MEDIUM, 0.25, 0.40),
                (SubtaskBucket.TRANSFORMATION_DRAFTING, 0.15, LeverageLevel.HIGH, 0.50, 0.65),
                (SubtaskBucket.ANALYSIS_PLANNING, 0.25, LeverageLevel.MEDIUM, 0.20, 0.40),
                (SubtaskBucket.COORDINATION_WORKFLOW, 0.10, LeverageLevel.WORKFLOW_MANUAL, 0.10, 0.20),
                (SubtaskBucket.REVIEW_QA_COMPLIANCE, 0.05, LeverageLevel.LOW, 0.05, 0.10),
                (SubtaskBucket.HUMAN_ONLY_EXECUTION, 0.25, LeverageLevel.LOW, 0.00, 0.05),
            ],
            "rationale": (
                "LLM can generate structured intake questions, summarize notes, and "
                "flag risks/constraints; humans still do rapport-building and sensitive "
                "negotiation cues."
            ),
            "advancement": "E7 → E7/E8 with better persuasion and emotional intelligence capabilities.",
        },
        {
            "name": "Market research & pricing guidance (CMAs, comps, neighborhood insights)",
            "exposure": [ExposureLevel.E2, ExposureLevel.E7],
            "ceiling": CeilingCategory.HIGH_STAKES_COMPLIANCE,
            "subtasks": [
                (SubtaskBucket.INPUT_GATHERING, 0.30, LeverageLevel.MEDIUM, 0.30, 0.50),
                (SubtaskBucket.TRANSFORMATION_DRAFTING, 0.25, LeverageLevel.HIGH, 0.50, 0.75),
                (SubtaskBucket.ANALYSIS_PLANNING, 0.25, LeverageLevel.MEDIUM, 0.25, 0.45),
                (SubtaskBucket.COORDINATION_WORKFLOW, 0.05, LeverageLevel.WORKFLOW_MANUAL, 0.10, 0.20),
                (SubtaskBucket.REVIEW_QA_COMPLIANCE, 0.10, LeverageLevel.LOW, 0.10, 0.20),
                (SubtaskBucket.HUMAN_ONLY_EXECUTION, 0.05, LeverageLevel.LOW, 0.00, 0.05),
            ],
            "rationale": (
                "LLM tools can summarize listing data, draft CMA narratives, and explain "
                "pricing logic; E2 potential rises when MLS/AVM integrations auto-pull "
                "comps and calculate adjustments."
            ),
            "advancement": "E2 → E2/E9 when integrated with MLS APIs for automatic comp pulling and valuation.",
        },
        {
            "name": "Listing description & marketing copy (MLS remarks, brochures, ads)",
            "exposure": [ExposureLevel.E1],
            "ceiling": CeilingCategory.PURE_DRAFTING,
            "subtasks": [
                (SubtaskBucket.INPUT_GATHERING, 0.10, LeverageLevel.MEDIUM, 0.25, 0.40),
                (SubtaskBucket.TRANSFORMATION_DRAFTING, 0.55, LeverageLevel.HIGH, 0.60, 0.80),
                (SubtaskBucket.ANALYSIS_PLANNING, 0.05, LeverageLevel.MEDIUM, 0.20, 0.35),
                (SubtaskBucket.COORDINATION_WORKFLOW, 0.05, LeverageLevel.WORKFLOW_MANUAL, 0.10, 0.20),
                (SubtaskBucket.REVIEW_QA_COMPLIANCE, 0.15, LeverageLevel.LOW, 0.10, 0.20),
                (SubtaskBucket.HUMAN_ONLY_EXECUTION, 0.10, LeverageLevel.LOW, 0.00, 0.05),
            ],
            "rationale": (
                "Drafting and iterating copy, headlines, FAQs, and neighborhood 'value props' "
                "is highly automatable; agent reviews for accuracy and compliance."
            ),
            "advancement": "E1 → E1/E3 with image-aware models that can describe photos and match copy to visuals.",
        },
        {
            "name": "Client communications (status updates, FAQs, objection handling)",
            "exposure": [ExposureLevel.E8],
            "ceiling": CeilingCategory.RELATIONSHIP_PERSUASION,
            "subtasks": [
                (SubtaskBucket.INPUT_GATHERING, 0.10, LeverageLevel.MEDIUM, 0.20, 0.35),
                (SubtaskBucket.TRANSFORMATION_DRAFTING, 0.40, LeverageLevel.HIGH, 0.55, 0.75),
                (SubtaskBucket.ANALYSIS_PLANNING, 0.05, LeverageLevel.MEDIUM, 0.20, 0.30),
                (SubtaskBucket.COORDINATION_WORKFLOW, 0.15, LeverageLevel.WORKFLOW_INTEGRATED, 0.30, 0.50),
                (SubtaskBucket.REVIEW_QA_COMPLIANCE, 0.10, LeverageLevel.LOW, 0.10, 0.20),
                (SubtaskBucket.HUMAN_ONLY_EXECUTION, 0.20, LeverageLevel.LOW, 0.00, 0.10),
            ],
            "rationale": (
                "LLM can draft empathetic updates, handle common objections, and tailor "
                "tone; agent must validate facts, avoid misstatements, and manage emotions."
            ),
            "advancement": "E8 → E8/E9 when agents can send communications autonomously within guardrails.",
        },
        {
            "name": "Transaction coordination (deadlines, inspection/appraisal steps, reminders)",
            "exposure": [ExposureLevel.E2, ExposureLevel.E9],
            "ceiling": CeilingCategory.HIGH_STAKES_COMPLIANCE,
            "subtasks": [
                (SubtaskBucket.INPUT_GATHERING, 0.15, LeverageLevel.MEDIUM, 0.25, 0.45),
                (SubtaskBucket.TRANSFORMATION_DRAFTING, 0.10, LeverageLevel.HIGH, 0.50, 0.65),
                (SubtaskBucket.ANALYSIS_PLANNING, 0.10, LeverageLevel.MEDIUM, 0.20, 0.35),
                (SubtaskBucket.COORDINATION_WORKFLOW, 0.40, LeverageLevel.WORKFLOW_AGENTIC, 0.40, 0.65),
                (SubtaskBucket.REVIEW_QA_COMPLIANCE, 0.15, LeverageLevel.LOW, 0.10, 0.20),
                (SubtaskBucket.HUMAN_ONLY_EXECUTION, 0.10, LeverageLevel.LOW, 0.00, 0.05),
            ],
            "rationale": (
                "Integrated apps can automate reminders and workflow; E9 potential increases "
                "with agentic tools that read email/calendars and trigger tasks—but oversight "
                "is required."
            ),
            "advancement": "E9 already present; advances further as agents gain trusted access to transaction management systems.",
        },
    ]


def _sample_skills() -> list[dict]:
    """Sample skills for Real Estate Sales Agents."""
    return [
        {
            "name": "Active Listening",
            "exposure": [ExposureLevel.E6, ExposureLevel.E7],
            "ceiling": CeilingCategory.RELATIONSHIP_PERSUASION,
            "subtasks": [
                (SubtaskBucket.INPUT_GATHERING, 0.30, LeverageLevel.MEDIUM, 0.20, 0.35),
                (SubtaskBucket.TRANSFORMATION_DRAFTING, 0.10, LeverageLevel.HIGH, 0.50, 0.65),
                (SubtaskBucket.ANALYSIS_PLANNING, 0.15, LeverageLevel.MEDIUM, 0.25, 0.40),
                (SubtaskBucket.COORDINATION_WORKFLOW, 0.05, LeverageLevel.LOW, 0.05, 0.15),
                (SubtaskBucket.REVIEW_QA_COMPLIANCE, 0.05, LeverageLevel.LOW, 0.05, 0.10),
                (SubtaskBucket.HUMAN_ONLY_EXECUTION, 0.35, LeverageLevel.LOW, 0.00, 0.05),
            ],
            "rationale": (
                "Voice AI can transcribe and summarize conversations, flag key points, "
                "and identify client sentiment; the act of listening and responding "
                "empathetically remains human-led."
            ),
            "advancement": "E6/E7 → E6/E7/E8 as voice AI gains real-time coaching ability.",
        },
        {
            "name": "Negotiation",
            "exposure": [ExposureLevel.E7, ExposureLevel.E8],
            "ceiling": CeilingCategory.RELATIONSHIP_PERSUASION,
            "subtasks": [
                (SubtaskBucket.INPUT_GATHERING, 0.15, LeverageLevel.MEDIUM, 0.25, 0.40),
                (SubtaskBucket.TRANSFORMATION_DRAFTING, 0.15, LeverageLevel.HIGH, 0.50, 0.70),
                (SubtaskBucket.ANALYSIS_PLANNING, 0.30, LeverageLevel.MEDIUM, 0.25, 0.45),
                (SubtaskBucket.COORDINATION_WORKFLOW, 0.05, LeverageLevel.LOW, 0.05, 0.15),
                (SubtaskBucket.REVIEW_QA_COMPLIANCE, 0.05, LeverageLevel.LOW, 0.05, 0.10),
                (SubtaskBucket.HUMAN_ONLY_EXECUTION, 0.30, LeverageLevel.LOW, 0.00, 0.10),
            ],
            "rationale": (
                "LLM can model scenarios, draft negotiation language, and anticipate "
                "counteroffers; persuasion is sensitive—agent experience and local norms matter."
            ),
            "advancement": "Advances with better multi-party reasoning and emotional modeling.",
        },
        {
            "name": "Critical Thinking",
            "exposure": [ExposureLevel.E7],
            "ceiling": CeilingCategory.HIGH_STAKES_COMPLIANCE,
            "subtasks": [
                (SubtaskBucket.INPUT_GATHERING, 0.20, LeverageLevel.MEDIUM, 0.25, 0.45),
                (SubtaskBucket.TRANSFORMATION_DRAFTING, 0.10, LeverageLevel.HIGH, 0.50, 0.65),
                (SubtaskBucket.ANALYSIS_PLANNING, 0.40, LeverageLevel.MEDIUM, 0.20, 0.40),
                (SubtaskBucket.COORDINATION_WORKFLOW, 0.05, LeverageLevel.LOW, 0.05, 0.10),
                (SubtaskBucket.REVIEW_QA_COMPLIANCE, 0.10, LeverageLevel.LOW, 0.10, 0.20),
                (SubtaskBucket.HUMAN_ONLY_EXECUTION, 0.15, LeverageLevel.LOW, 0.00, 0.05),
            ],
            "rationale": (
                "Advanced reasoning can surface options, flag inconsistencies, and "
                "structure complex analyses; final judgment on ambiguous situations "
                "remains with the professional."
            ),
            "advancement": "Improves as reasoning models handle more complex multi-step logic.",
        },
    ]


def _build_subtask_scores(subtask_tuples: list[tuple]) -> list[SubtaskScore]:
    """Convert shorthand tuples into SubtaskScore objects."""
    return [
        SubtaskScore(
            bucket=bucket,
            baseline_share_pct=share,
            exposure_levels=[],  # Inherited from parent item
            leverage_level=leverage,
            efficiency_gain_low=gain_low,
            efficiency_gain_high=gain_high,
        )
        for bucket, share, leverage, gain_low, gain_high in subtask_tuples
    ]


def build_sample_alert():
    """Build a complete sample AutomationAlert for Real Estate Sales Agents."""
    soc_code = "41-9022.00"
    title = "Real Estate Sales Agents"

    # Score tasks
    task_items = []
    for t in _sample_tasks():
        subtasks = _build_subtask_scores(t["subtasks"])
        item = score_item(
            item_name=t["name"],
            category=OnetCategory.TASKS,
            exposure_levels=t["exposure"],
            subtask_scores=subtasks,
            ceiling_category=t["ceiling"],
            rationale=t["rationale"],
            advancement_notes=t["advancement"],
        )
        task_items.append(item)

    # Score skills
    skill_items = []
    for s in _sample_skills():
        subtasks = _build_subtask_scores(s["subtasks"])
        item = score_item(
            item_name=s["name"],
            category=OnetCategory.SKILLS,
            exposure_levels=s["exposure"],
            subtask_scores=subtasks,
            ceiling_category=s["ceiling"],
            rationale=s["rationale"],
            advancement_notes=s["advancement"],
        )
        skill_items.append(item)

    # Build summaries
    task_summary = summarize_category(OnetCategory.TASKS, task_items)
    skill_summary = summarize_category(OnetCategory.SKILLS, skill_items)

    return build_automation_alert(
        soc_code=soc_code,
        occupation_title=title,
        category_summaries=[task_summary, skill_summary],
    )
