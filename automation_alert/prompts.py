"""Prompt templates for LLM-based automation exposure scoring.

These prompts instruct the LLM to assess each O*NET item and return
structured JSON that the scoring engine can process.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# System prompt: establishes the LLM's role and the scoring methodology
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """\
You are an expert analyst specializing in AI/automation impact on occupations.
You use the O*NET occupational framework and a rigorous, repeatable scoring
methodology to assess how AI capabilities affect specific work elements.

## Exposure Level Taxonomy (E0–E11)

E0  – No exposure
E1  – Direct LLM exposure (drafting, rewriting, ideation, summarization)
E2  – LLM-powered applications (CRM, ticketing, docs, databases)
E3  – Image capabilities (image generation, recognition, editing)
E4  – Video capabilities (video generation, analysis)
E5  – Audio capabilities (transcription, audio generation, analysis)
E6  – Voice capabilities (conversational voice AI)
E7  – Advanced reasoning (scenario planning, complex synthesis, multi-step logic)
E8  – Persuasion capabilities (tailored messaging, negotiation language)
E9  – Digital world action (AI Agents: tool use across email/calendar/apps)
E10 – Physical world vision (AI vision devices, inspection, monitoring)
E11 – Physical world action (humanoid robots, physical automation)

## Subtask Buckets

Every work element decomposes into these universal subtask buckets:

1. input_gathering – Finding info, collecting docs, asking questions, pulling data
2. transformation_drafting – Writing, summarizing, formatting, creating first drafts
3. analysis_planning – Comparing options, outlining plans, reasoning through scenarios
4. coordination_workflow – Scheduling, reminders, handoffs, status updates, tracking
5. review_qa_compliance – Checking accuracy, policy, legal/brand compliance, approvals
6. human_only_execution – In-person work, hands-on steps, relationship building, physical actions

## Leverage Levels

- high: 50-80% reduction (draft/transform tasks)
- medium: 20-50% reduction (analysis/planning tasks)
- low: 0-20% reduction (relationship/physical tasks)
- workflow_manual: 10-25% (manual copy/paste integration)
- workflow_integrated: 25-50% (integrated LLM-powered apps)
- workflow_agentic: 40-70% (agentic AI with oversight)

## Ceiling Categories

- physical_execution: Hard cap at 25% (physical/in-person tasks)
- high_stakes_compliance: Cap at 50% (must-review, must-approve)
- relationship_persuasion: Cap at 55% (quality and trust dominate)
- pure_drafting: Cap at 85% (pure content creation)

## Instructions

For each work element provided, you MUST return a JSON object with these fields.
Do NOT include any text outside the JSON array.
"""


# ---------------------------------------------------------------------------
# Per-item scoring prompt
# ---------------------------------------------------------------------------

SCORE_ITEMS_PROMPT = """\
Score the following {category_label} items for the occupation "{occupation_title}" \
(SOC: {soc_code}).

For EACH item, return a JSON object with these exact fields:

{{
  "item_name": "<the item text>",
  "exposure_levels": ["E1", "E7"],  // list of applicable E0-E11 codes
  "ceiling_category": "pure_drafting",  // one of: physical_execution, high_stakes_compliance, relationship_persuasion, pure_drafting
  "subtasks": [
    {{
      "bucket": "input_gathering",
      "baseline_share_pct": 0.15,
      "exposure_levels": ["E2"],
      "leverage_level": "medium",
      "efficiency_gain_low": 0.25,
      "efficiency_gain_high": 0.45
    }},
    // ... one entry per relevant subtask bucket (include all 6 buckets)
  ],
  "rationale": "Concise explanation of why this item has this exposure and time-saved potential.",
  "advancement_notes": "How exposure could increase with better tooling (Step I)."
}}

Return a JSON array of objects. All 6 subtask buckets must be present for each item.
The baseline_share_pct values across the 6 buckets must sum to 1.0.

Efficiency gains must fall within the ranges for the assigned leverage_level:
- high: 0.50–0.80
- medium: 0.20–0.50
- low: 0.00–0.20
- workflow_manual: 0.10–0.25
- workflow_integrated: 0.25–0.50
- workflow_agentic: 0.40–0.70

ITEMS TO SCORE:
{items_json}
"""


# ---------------------------------------------------------------------------
# Category-specific context prompts
# ---------------------------------------------------------------------------

CATEGORY_CONTEXT: dict[str, str] = {
    "tasks": (
        "These are specific work tasks performed in this occupation. "
        "Score based on cycle-time reduction at equal-or-better quality. "
        "Consider the full workflow: from gathering inputs to final delivery."
    ),
    "skills": (
        "These are skills required for this occupation. "
        "Score based on how much AI can reduce the time needed to exercise "
        "this skill effectively. A skill with high AI leverage means the "
        "practitioner can achieve the same skill outcome faster with AI."
    ),
    "knowledge": (
        "These are knowledge domains required for this occupation. "
        "Score based on how much AI can reduce the time spent acquiring, "
        "applying, or maintaining this knowledge in work contexts."
    ),
    "abilities": (
        "These are cognitive and physical abilities required for this occupation. "
        "Score based on how much AI can augment or substitute for this ability "
        "in performing work tasks."
    ),
    "work_activities": (
        "These are generalized work activities performed in this occupation. "
        "Score based on cycle-time reduction for the activity as a whole."
    ),
    "detailed_work_activities": (
        "These are detailed/specific work activities. Score each one individually "
        "based on its specific automation exposure."
    ),
    "technology_skills": (
        "These are technology tools and software used in this occupation. "
        "Score based on how much AI integration can reduce the time spent "
        "using these tools or replace them entirely."
    ),
    "work_context": (
        "These are work context/environment factors. Score based on how much "
        "the physical, social, or structural context limits or enables AI automation."
    ),
    "work_styles": (
        "These are work style attributes (e.g., attention to detail, dependability). "
        "Score based on how much AI can support or augment this behavioral attribute "
        "in work performance."
    ),
}


def build_scoring_prompt(
    soc_code: str,
    occupation_title: str,
    category: str,
    items: list[dict],
) -> str:
    """Build the full scoring prompt for a set of items."""
    import json

    category_label = category.replace("_", " ").title()
    items_text = json.dumps(items, indent=2)
    context = CATEGORY_CONTEXT.get(category, "")

    prompt = SCORE_ITEMS_PROMPT.format(
        category_label=category_label,
        occupation_title=occupation_title,
        soc_code=soc_code,
        items_json=items_text,
    )

    if context:
        prompt = f"CATEGORY CONTEXT: {context}\n\n{prompt}"

    return prompt
