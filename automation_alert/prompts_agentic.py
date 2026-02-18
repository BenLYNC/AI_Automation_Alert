"""Prompt templates for the Agentic Impact Layer.

Implements the full agentic scoring methodology:
  A) Operating Modes (0–3)
  B) Agent-ready workflow unit decomposition (W1–W7)
  C) Agentic Suitability scoring (AS 0–3)
  D) Execution Automation (EA) vs. Oversight Tax (OT)

The LLM produces the qualitative assessments; the scoring engine
(agentic_layer.py) then applies steps E–H deterministically.
"""

from __future__ import annotations

AGENTIC_SYSTEM_PROMPT = """\
You are an expert analyst specializing in the impact of agentic AI on
cognitive and knowledge work. Agentic AI goes beyond chat-based LLMs:
agents can plan multi-step workflows, use tools, take actions across
systems, and operate with varying degrees of autonomy.

## Operating Modes (Step A)

- Mode 0 — Copilot: drafts steps, human executes (non-agentic)
- Mode 1 — Assisted execution: agent executes after explicit approval per step
- Mode 2 — Bounded autonomy: agent executes within guardrails (policies, spend limits)
- Mode 3 — Full autonomy: agent executes end-to-end; human audits exceptions

Most real organizations operate in Mode 1–2.

## Agent-Ready Workflow Units (Step B) — W1–W7

Every work element decomposes into these workflow units:

- W1: intake_triage — Read request, classify, route
- W2: info_retrieval — Search systems, pull data, open docs
- W3: planning — Decide steps, dependencies, schedule
- W4: tool_actions — Create/update/send/schedule/upload/submit
- W5: verification_qa — Confirm correct, reconcile inconsistencies
- W6: approvals_compliance — Policy checks, approvals, audit notes
- W7: exceptions_human_only — Judgment calls, relationship, physical work

Time shares across W1–W7 must sum to 1.0.

## Agentic Suitability (Step C) — Rate each unit 0–3

- 0 = Not agent-suitable (high ambiguity, physical, deeply relational)
- 1 = Partially (some actions possible; many checks required)
- 2 = Mostly (clear rules + structured inputs)
- 3 = Highly (repeatable, standardized, machine-checkable)

AS is driven upward by: structured inputs, stable SOPs, accessible APIs, clear success criteria.

## Execution Automation (EA) and Oversight Tax (OT) — Step D

For each workflow unit, estimate:

1. EA (0.0–1.0): How much of that unit's time the agent removes by acting itself
   - Mode 1: EA typically 0.10–0.30
   - Mode 2: EA typically 0.30–0.60
   - Mode 3: EA typically 0.60–0.85

2. OT (0.0–1.0): Extra time added for supervision, review, mistake handling
   - Low stakes: OT 0.05–0.15
   - Medium stakes: OT 0.10–0.25
   - High stakes (money, legal, safety): OT 0.20–0.50

Net gain per unit = EA − OT (can be negative if oversight exceeds automation)

## Knowledge Work Types

- routine_cognitive: Rule-based, repeatable cognitive tasks
- complex_cognitive: Requires judgment, context, expertise
- creative_cognitive: Requires originality, novel approaches
- interpersonal_cognitive: Requires social/emotional intelligence
- physical_manual: Not primarily cognitive

## Stakes Levels

- low: Low consequences of error (5-15% oversight tax)
- medium: Moderate consequences (10-25% oversight tax)
- high: Money, legal, or safety consequences (20-50% oversight tax)

## Agentic Ceiling Categories (Step H)

- regulated_signoffs: ≤50% (hard approvals required)
- high_touch_relationship: ≤30% (relationship quality dominates)
- physical_execution: ≤15% (physical presence required)
- unstructured_bespoke: ≤32% (novel/ambiguous work)
- standardized_backoffice: ≤80% (highly standardized workflows)

## Agent Maturity Levels (Step G)

- 1: Scripted agent (narrow, brittle) — 10–25% savings
- 2: Tool-integrated agent (APIs, reliable actions) — 20–45% savings
- 3: Policy-governed agent (guardrails, audit, rollbacks) — 30–60% savings
- 4: Self-healing agent (detects failures, retries, escalates) — 45–75% savings
"""


AGENTIC_SCORING_PROMPT = """\
Assess the agentic AI impact on these {category_label} items for the
occupation "{occupation_title}" (SOC: {soc_code}).

For EACH item, return a JSON object with this structure:

{{
  "item_name": "<the item text>",
  "recommended_mode": 2,
  "mode_rationale": "Why this operating mode is appropriate.",
  "knowledge_work_type": "routine_cognitive",
  "stakes_level": "medium",
  "agentic_ceiling": "standardized_backoffice",
  "current_maturity": 2,
  "exception_rate": 0.15,
  "takeover_cost": 0.30,
  "workflow_scores": [
    {{
      "unit": "intake_triage",
      "time_share_pct": 0.10,
      "agentic_suitability": 3,
      "execution_automation_pct": 0.55,
      "oversight_tax_pct": 0.10,
      "net_gain_pct": 0.45,
      "rationale": "Structured requests can be auto-classified..."
    }},
    {{
      "unit": "info_retrieval",
      "time_share_pct": 0.20,
      "agentic_suitability": 2,
      "execution_automation_pct": 0.40,
      "oversight_tax_pct": 0.15,
      "net_gain_pct": 0.25,
      "rationale": "Agent can search systems and pull relevant data..."
    }},
    {{
      "unit": "planning",
      "time_share_pct": 0.15,
      "agentic_suitability": 1,
      "execution_automation_pct": 0.20,
      "oversight_tax_pct": 0.15,
      "net_gain_pct": 0.05,
      "rationale": "Planning requires judgment..."
    }},
    {{
      "unit": "tool_actions",
      "time_share_pct": 0.25,
      "agentic_suitability": 3,
      "execution_automation_pct": 0.60,
      "oversight_tax_pct": 0.10,
      "net_gain_pct": 0.50,
      "rationale": "CRUD operations across systems are highly automatable..."
    }},
    {{
      "unit": "verification_qa",
      "time_share_pct": 0.10,
      "agentic_suitability": 2,
      "execution_automation_pct": 0.35,
      "oversight_tax_pct": 0.20,
      "net_gain_pct": 0.15,
      "rationale": "Can auto-check against rules..."
    }},
    {{
      "unit": "approvals_compliance",
      "time_share_pct": 0.10,
      "agentic_suitability": 1,
      "execution_automation_pct": 0.15,
      "oversight_tax_pct": 0.25,
      "net_gain_pct": -0.10,
      "rationale": "Requires human sign-off..."
    }},
    {{
      "unit": "exceptions_human_only",
      "time_share_pct": 0.10,
      "agentic_suitability": 0,
      "execution_automation_pct": 0.0,
      "oversight_tax_pct": 0.0,
      "net_gain_pct": 0.0,
      "rationale": "Edge cases require human judgment..."
    }}
  ],
  "agentic_rationale": "Overall explanation of agentic impact.",
  "advancement_notes": "What environmental changes would increase savings (Step I).",
  "near_term_projection": "How agentic capabilities will evolve 1-3 years."
}}

IMPORTANT:
- All 7 workflow units (W1-W7) must be present for each item
- time_share_pct values must sum to 1.0
- net_gain_pct = execution_automation_pct - oversight_tax_pct
- exception_rate and takeover_cost are fractions (0.0-1.0)
- recommended_mode is an integer (0, 1, 2, or 3)
- current_maturity is an integer (1, 2, 3, or 4)
- agentic_suitability is an integer (0, 1, 2, or 3)

Return a JSON array of objects.

ITEMS TO SCORE:
{items_json}
"""


def build_agentic_prompt(
    soc_code: str,
    occupation_title: str,
    category: str,
    items: list[dict],
) -> str:
    """Build the agentic scoring prompt for a set of items."""
    import json

    category_label = category.replace("_", " ").title()
    items_text = json.dumps(items, indent=2)

    return AGENTIC_SCORING_PROMPT.format(
        category_label=category_label,
        occupation_title=occupation_title,
        soc_code=soc_code,
        items_json=items_text,
    )
