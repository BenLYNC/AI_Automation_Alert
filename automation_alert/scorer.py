"""LLM-powered Scorer — orchestrates the full scoring pipeline.

Takes O*NET data → sends to LLM for assessment → processes through
the scoring engine → produces the AutomationAlert output.

Two-layer scoring:
1. Base layer: E0-E11 exposure taxonomy with subtask decomposition
2. Agentic layer: Operating modes, W1-W7 workflow units, EA/OT, maturity model

Provider-agnostic: works with Anthropic (Claude) or Google (Gemini).
"""

from __future__ import annotations

import logging
from typing import Any

from .agentic_layer import (
    AgenticCeilingCategory,
    AgenticImpactScore,
    AgentMaturityLevel,
    AgenticSuitability,
    KnowledgeWorkType,
    OperatingMode,
    StakesLevel,
    WorkflowUnit,
    WorkflowUnitScore,
    apply_agentic_adjustment,
    score_agentic_item,
)
from .llm_client import LLMClient, create_client
from .models import (
    CeilingCategory,
    ExposureLevel,
    LeverageLevel,
    OnetCategory,
    SCORABLE_CATEGORIES,
    ScoredItem,
    SubtaskBucket,
    SubtaskScore,
)
from .prompts import SYSTEM_PROMPT, build_scoring_prompt
from .prompts_agentic import AGENTIC_SYSTEM_PROMPT, build_agentic_prompt
from .scoring_engine import (
    build_automation_alert,
    score_item,
    summarize_category,
    AutomationAlert,
)

logger = logging.getLogger(__name__)


class Scorer:
    """Orchestrates LLM-based scoring for an entire occupation.

    Works with any LLM provider via the LLMClient interface.
    Default provider is Gemini (free tier).
    """

    def __init__(
        self,
        provider: str = "gemini",
        model: str | None = None,
        api_key: str | None = None,
        llm_client: LLMClient | None = None,
    ):
        """Initialize the scorer.

        Args:
            provider: "gemini" or "anthropic" (ignored if llm_client provided)
            model: Model name (uses provider default if not specified)
            api_key: API key (falls back to environment variables)
            llm_client: Pre-built LLM client (overrides provider/model/api_key)
        """
        if llm_client:
            self.llm = llm_client
        else:
            self.llm = create_client(provider=provider, model=model, api_key=api_key)

    # ------------------------------------------------------------------
    # Base E0-E11 Scoring
    # ------------------------------------------------------------------

    def score_category_items(
        self,
        soc_code: str,
        occupation_title: str,
        category: OnetCategory,
        raw_items: list[dict[str, Any]],
    ) -> list[ScoredItem]:
        """Score all items in a single O*NET category."""
        if not raw_items:
            return []

        items_for_prompt = []
        for item in raw_items:
            name = (
                item.get("name")
                or item.get("title")
                or item.get("description")
                or item.get("statement")
                or str(item)
            )
            entry: dict[str, Any] = {"name": name}
            if "score" in item and "value" in item["score"]:
                entry["importance"] = item["score"]["value"]
            items_for_prompt.append(entry)

        prompt = build_scoring_prompt(
            soc_code=soc_code,
            occupation_title=occupation_title,
            category=category.value,
            items=items_for_prompt,
        )

        logger.info(
            "Scoring %d %s items for %s", len(items_for_prompt), category.value, soc_code
        )

        response_text = self.llm.call(SYSTEM_PROMPT, prompt)
        scored_data = self.llm.parse_json_array(response_text)

        scored_items: list[ScoredItem] = []
        for sd in scored_data:
            try:
                scored_items.append(self._build_scored_item(sd, category))
            except Exception as e:
                logger.warning("Failed to process scored item: %s — %s", sd.get("item_name"), e)

        return scored_items

    def _build_scored_item(
        self, data: dict[str, Any], category: OnetCategory
    ) -> ScoredItem:
        """Convert LLM output JSON into a ScoredItem via the scoring engine."""
        exposure_levels = [ExposureLevel(e) for e in data["exposure_levels"]]
        ceiling_cat = CeilingCategory(data["ceiling_category"])

        subtask_scores = []
        for st in data["subtasks"]:
            subtask_scores.append(SubtaskScore(
                bucket=SubtaskBucket(st["bucket"]),
                baseline_share_pct=st["baseline_share_pct"],
                exposure_levels=[ExposureLevel(e) for e in st["exposure_levels"]],
                leverage_level=LeverageLevel(st["leverage_level"]),
                efficiency_gain_low=st["efficiency_gain_low"],
                efficiency_gain_high=st["efficiency_gain_high"],
            ))

        return score_item(
            item_name=data["item_name"],
            category=category,
            exposure_levels=exposure_levels,
            subtask_scores=subtask_scores,
            ceiling_category=ceiling_cat,
            rationale=data["rationale"],
            advancement_notes=data.get("advancement_notes", ""),
        )

    # ------------------------------------------------------------------
    # Agentic Impact Layer (Steps A-I)
    # ------------------------------------------------------------------

    def score_agentic_impact(
        self,
        soc_code: str,
        occupation_title: str,
        category: OnetCategory,
        raw_items: list[dict[str, Any]],
    ) -> list[AgenticImpactScore]:
        """Score agentic AI impact for items in a category.

        Uses the full agentic methodology:
        A) Operating modes → B) W1-W7 decomposition → C) AS scoring →
        D) EA/OT estimation → E-H) computed by scoring engine
        """
        if not raw_items:
            return []

        items_for_prompt = []
        for item in raw_items:
            name = (
                item.get("name")
                or item.get("title")
                or item.get("description")
                or item.get("statement")
                or str(item)
            )
            items_for_prompt.append({"name": name})

        prompt = build_agentic_prompt(
            soc_code=soc_code,
            occupation_title=occupation_title,
            category=category.value,
            items=items_for_prompt,
        )

        logger.info(
            "Scoring agentic impact for %d %s items (%s)",
            len(items_for_prompt), category.value, soc_code,
        )

        response_text = self.llm.call(AGENTIC_SYSTEM_PROMPT, prompt)
        agentic_data = self.llm.parse_json_array(response_text)

        results: list[AgenticImpactScore] = []
        for ad in agentic_data:
            try:
                results.append(self._build_agentic_score(ad, category))
            except Exception as e:
                logger.warning("Failed to process agentic score: %s — %s", ad.get("item_name"), e)

        return results

    def _build_agentic_score(
        self, data: dict[str, Any], category: OnetCategory
    ) -> AgenticImpactScore:
        """Convert LLM agentic output into an AgenticImpactScore.

        The LLM provides qualitative assessments (Steps A-D);
        score_agentic_item() applies the deterministic pipeline (Steps E-H).
        """
        workflow_scores = []
        for ws in data["workflow_scores"]:
            workflow_scores.append(WorkflowUnitScore(
                unit=WorkflowUnit(ws["unit"]),
                time_share_pct=ws["time_share_pct"],
                agentic_suitability=AgenticSuitability(ws["agentic_suitability"]),
                execution_automation_pct=ws["execution_automation_pct"],
                oversight_tax_pct=ws["oversight_tax_pct"],
                net_gain_pct=ws["net_gain_pct"],
                rationale=ws["rationale"],
            ))

        return score_agentic_item(
            item_name=data["item_name"],
            category=category,
            recommended_mode=OperatingMode(data["recommended_mode"]),
            mode_rationale=data["mode_rationale"],
            workflow_scores=workflow_scores,
            exception_rate=data["exception_rate"],
            takeover_cost=data["takeover_cost"],
            current_maturity=AgentMaturityLevel(data["current_maturity"]),
            agentic_ceiling=AgenticCeilingCategory(data["agentic_ceiling"]),
            knowledge_work_type=KnowledgeWorkType(data["knowledge_work_type"]),
            stakes_level=StakesLevel(data["stakes_level"]),
            agentic_rationale=data["agentic_rationale"],
            advancement_notes=data.get("advancement_notes", ""),
            near_term_projection=data.get("near_term_projection", ""),
        )

    # ------------------------------------------------------------------
    # Full Pipeline: Score an entire occupation
    # ------------------------------------------------------------------

    def score_occupation(
        self,
        soc_code: str,
        occupation_title: str,
        onet_data: dict[OnetCategory, list[dict[str, Any]]],
        include_agentic: bool = True,
    ) -> tuple[AutomationAlert, dict[str, AgenticImpactScore]]:
        """Run the full scoring pipeline for an occupation.

        Returns:
            (AutomationAlert, dict of item_name -> AgenticImpactScore)
        """
        category_summaries = []
        all_agentic_scores: dict[str, AgenticImpactScore] = {}

        for category in SCORABLE_CATEGORIES:
            raw_items = onet_data.get(category, [])
            if not raw_items:
                continue

            # Step 1: Base scoring
            scored_items = self.score_category_items(
                soc_code, occupation_title, category, raw_items
            )

            # Step 2: Agentic layer (optional)
            if include_agentic and scored_items:
                agentic_scores = self.score_agentic_impact(
                    soc_code, occupation_title, category, raw_items
                )

                # Store agentic scores for output
                for ag in agentic_scores:
                    all_agentic_scores[ag.item_name] = ag

                # Match agentic scores to base items and apply adjustments
                agentic_by_name = {a.item_name: a for a in agentic_scores}
                adjusted_items = []
                for item in scored_items:
                    agentic = agentic_by_name.get(item.item_name)
                    if agentic:
                        adjusted_items.append(
                            apply_agentic_adjustment(item, agentic)
                        )
                    else:
                        adjusted_items.append(item)
                scored_items = adjusted_items

            # Step 3: Category summary
            summary = summarize_category(category, scored_items)
            category_summaries.append(summary)

        # Step 4: Build the alert
        alert = build_automation_alert(
            soc_code=soc_code,
            occupation_title=occupation_title,
            category_summaries=category_summaries,
        )

        return alert, all_agentic_scores
