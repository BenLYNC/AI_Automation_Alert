"""Output Renderer — produces human-readable automation alert reports.

Generates formatted output for the full AutomationAlert, including:
- Overall occupation summary
- Per-category breakdowns with individual item scores
- Agentic impact details (operating modes, W1-W7 workflow, EA/OT, maturity)
- Exposure level legend
- Delta history (when available)

Supports both rich terminal output and plain-text/markdown.
"""

from __future__ import annotations

import json

from .agentic_layer import (
    AgenticImpactScore,
    OPERATING_MODE_LABELS,
    WORKFLOW_UNIT_LABELS,
)
from .models import (
    AutomationAlert,
    CategorySummary,
    EXPOSURE_LABELS,
    ExposureLevel,
)


# ---------------------------------------------------------------------------
# Markdown / Plain-text renderer
# ---------------------------------------------------------------------------

def render_markdown(
    alert: AutomationAlert,
    agentic_scores: dict[str, AgenticImpactScore] | None = None,
) -> str:
    """Render a full AutomationAlert as a markdown report."""
    lines: list[str] = []

    # Header
    lines.append(f"# {alert.soc_code} — {alert.occupation_title}")
    lines.append(f"**Automation Alert Profile** | Evaluated: {alert.evaluated_at:%Y-%m-%d}")
    lines.append("")

    # Overall summary box
    lines.append("## Overall Automation Exposure")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")
    lines.append(
        f"| **Estimated Time Saved** | "
        f"**{alert.overall_time_saved_low_pct:.0f}–{alert.overall_time_saved_high_pct:.0f}%** |"
    )
    lines.append(f"| **Risk Level** | **{alert.overall_automation_risk_label}** |")
    dominant = ", ".join(
        f"{ev.value} ({EXPOSURE_LABELS[ev]})" for ev in alert.dominant_exposure_vectors
    )
    lines.append(f"| **Dominant Exposure Vectors** | {dominant} |")
    lines.append(f"| **Categories Scored** | {len(alert.category_summaries)} |")
    total_items = sum(cs.item_count for cs in alert.category_summaries)
    lines.append(f"| **Total Items Scored** | {total_items} |")
    lines.append("")

    # Category summary table
    lines.append("## Category Summary")
    lines.append("")
    lines.append(
        "| Category | Items | Avg Time Saved (%) | Dominant Vectors |"
    )
    lines.append("|----------|-------|-------------------|-----------------|")
    for cs in alert.category_summaries:
        cat_label = cs.category.value.replace("_", " ").title()
        vectors = ", ".join(ev.value for ev in cs.dominant_exposure_vectors)
        lines.append(
            f"| {cat_label} | {cs.item_count} | "
            f"{cs.avg_time_saved_low_pct:.0f}–{cs.avg_time_saved_high_pct:.0f}% | "
            f"{vectors} |"
        )
    lines.append("")

    # Per-category detail tables
    for cs in alert.category_summaries:
        lines.extend(_render_category_detail(cs, agentic_scores))

    # Agentic impact summary (if available)
    if agentic_scores:
        lines.extend(_render_agentic_summary(agentic_scores))

    # Exposure level legend
    lines.append("## Exposure Level Legend")
    lines.append("")
    lines.append("| Code | Capability |")
    lines.append("|------|-----------|")
    for ev in ExposureLevel:
        lines.append(f"| {ev.value} | {EXPOSURE_LABELS[ev]} |")
    lines.append("")

    # Delta history
    if alert.deltas:
        lines.append("## Score Changes Since Last Evaluation")
        lines.append("")
        lines.append(
            "| Item | Category | Previous | Current | Delta | Reason |"
        )
        lines.append("|------|----------|----------|---------|-------|--------|")
        for d in alert.deltas:
            lines.append(
                f"| {d.item_name} | {d.category.value} | "
                f"{d.previous_time_saved_low:.0f}–{d.previous_time_saved_high:.0f}% | "
                f"{d.current_time_saved_low:.0f}–{d.current_time_saved_high:.0f}% | "
                f"{d.delta_low:+.0f}/{d.delta_high:+.0f}pp | "
                f"{d.change_reason} |"
            )
        lines.append("")

    # Methodology note
    lines.append("---")
    lines.append(f"*Methodology v{alert.methodology_version}*")
    lines.append("")
    lines.append("*Base scoring: Subtask decomposition (6 buckets) → Weighted efficiency gains → "
                 "Reality discounts → Ceiling caps → Range generation*")
    lines.append("")
    lines.append("*Agentic scoring: Operating mode assignment → W1-W7 workflow decomposition → "
                 "Agentic suitability (AS 0-3) → Execution automation vs. oversight tax → "
                 "Compounding bonus → Exception/takeover discounts → Maturity-based range → "
                 "Agentic ceiling cap*")

    return "\n".join(lines)


def _render_category_detail(
    cs: CategorySummary,
    agentic_scores: dict[str, AgenticImpactScore] | None = None,
) -> list[str]:
    """Render the detail table for a single category."""
    lines: list[str] = []
    cat_label = cs.category.value.replace("_", " ").title()

    lines.append(f"### {cat_label}")
    lines.append("")

    has_agentic = agentic_scores and any(
        item.item_name in agentic_scores for item in cs.items
    )

    if has_agentic:
        lines.append(
            "| Item | Exposure | Est. Time Saved | "
            "Agent Mode | Maturity | Cognitive Displ. | Rationale |"
        )
        lines.append("|------|----------|----------------|"
                     "------------|----------|-----------------|-----------|")
    else:
        lines.append("| Item | Exposure Level | Est. Time Saved (%) | Rationale |")
        lines.append("|------|---------------|-------------------|-----------|")

    for item in cs.items:
        time_range = f"{item.time_saved_low_pct:.0f}–{item.time_saved_high_pct:.0f}%"
        rationale_short = item.rationale[:120]
        if len(item.rationale) > 120:
            rationale_short += "..."

        if has_agentic and item.item_name in agentic_scores:
            ag = agentic_scores[item.item_name]
            mode_label = f"Mode {ag.recommended_mode.value}"
            maturity_label = f"L{ag.current_maturity.value}"
            lines.append(
                f"| {item.item_name} | {item.exposure_label} | "
                f"{time_range} | {mode_label} | {maturity_label} | "
                f"{ag.cognitive_displacement_pct:.0f}% | {rationale_short} |"
            )
        else:
            lines.append(
                f"| {item.item_name} | {item.exposure_label} | "
                f"{time_range} | {rationale_short} |"
            )

    lines.append("")
    return lines


def _render_agentic_summary(
    agentic_scores: dict[str, AgenticImpactScore],
) -> list[str]:
    """Render the agentic impact summary section."""
    lines: list[str] = []

    lines.append("## Agentic Impact Analysis")
    lines.append("")

    # Summary table
    lines.append(
        "| Item | Mode | Maturity | Stakes | "
        "Raw Agentic % | Bonus | Exceptions | Final Agentic % | Ceiling |"
    )
    lines.append(
        "|------|------|----------|--------|"
        "--------------|-------|------------|----------------|---------|"
    )

    for name, ag in agentic_scores.items():
        short_name = name[:50] + "..." if len(name) > 50 else name
        lines.append(
            f"| {short_name} | Mode {ag.recommended_mode.value} | "
            f"L{ag.current_maturity.value} | {ag.stakes_level.value} | "
            f"{ag.raw_agentic_time_saved_pct:.0f}% | "
            f"+{ag.workflow_compounding_bonus_pct:.0f}pp | "
            f"{ag.exception_rate_pct:.0f}%/{ag.takeover_cost_pct:.0f}% | "
            f"{ag.final_time_saved_low_pct:.0f}–{ag.final_time_saved_high_pct:.0f}% | "
            f"{ag.ceiling_cap_pct:.0f}% |"
        )

    lines.append("")

    # Workflow unit detail for top items
    sorted_items = sorted(
        agentic_scores.values(),
        key=lambda a: a.final_time_saved_high_pct,
        reverse=True,
    )

    for ag in sorted_items[:5]:  # Top 5 by agentic impact
        lines.append(f"#### {ag.item_name}")
        lines.append(f"**Operating Mode**: {OPERATING_MODE_LABELS[ag.recommended_mode]}")
        lines.append(f"**Knowledge Work Type**: {ag.knowledge_work_type.value}")
        lines.append(f"**Cognitive Displacement**: {ag.cognitive_displacement_pct:.0f}%")
        lines.append("")
        lines.append("| Workflow Unit | Time Share | AS | EA | OT | Net Gain | Rationale |")
        lines.append("|--------------|-----------|----|----|----|---------:|-----------|")

        for ws in ag.workflow_scores:
            label = WORKFLOW_UNIT_LABELS.get(ws.unit, ws.unit.value)
            short_label = label.split("(")[0].strip()
            lines.append(
                f"| {short_label} | {ws.time_share_pct:.0%} | "
                f"{ws.agentic_suitability.value} | {ws.execution_automation_pct:.0%} | "
                f"{ws.oversight_tax_pct:.0%} | {ws.net_gain_pct:+.0%} | "
                f"{ws.rationale[:80]} |"
            )

        lines.append("")
        if ag.advancement_notes:
            lines.append(f"**Advancement path**: {ag.advancement_notes}")
        if ag.near_term_projection:
            lines.append(f"**Near-term projection**: {ag.near_term_projection}")
        lines.append("")

    return lines


# ---------------------------------------------------------------------------
# JSON output
# ---------------------------------------------------------------------------

def render_json(
    alert: AutomationAlert,
    agentic_scores: dict[str, AgenticImpactScore] | None = None,
) -> str:
    """Render the full alert as structured JSON."""
    output = alert.model_dump(mode="json")
    if agentic_scores:
        output["agentic_impact"] = {
            name: score.model_dump(mode="json")
            for name, score in agentic_scores.items()
        }
    return json.dumps(output, indent=2, default=str)


# ---------------------------------------------------------------------------
# File output helper
# ---------------------------------------------------------------------------

def write_report(
    alert: AutomationAlert,
    output_path: str,
    fmt: str = "markdown",
    agentic_scores: dict[str, AgenticImpactScore] | None = None,
) -> None:
    """Write the automation alert report to a file."""
    if fmt == "json":
        content = render_json(alert, agentic_scores)
    else:
        content = render_markdown(alert, agentic_scores)

    with open(output_path, "w") as f:
        f.write(content)
