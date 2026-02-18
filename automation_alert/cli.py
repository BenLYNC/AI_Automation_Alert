"""CLI entry point for the Automation Alert system.

Usage:
    automation-alert score 41-9022.00 --title "Real Estate Sales Agents"
    automation-alert score 15-1252.00 --title "Software Developers" --format json
    automation-alert score 29-1141.00 --no-agentic --output report.md
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys

from .models import OnetCategory, SCORABLE_CATEGORIES
from .onet_client import OnetClient, OnetApiError
from .renderer import render_json, render_markdown, write_report
from .scorer import Scorer


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="automation-alert",
        description="O*NET Automation Exposure Scoring & Notification System",
    )
    subparsers = parser.add_subparsers(dest="command")

    # -- score command --
    score_parser = subparsers.add_parser(
        "score", help="Score an occupation's automation exposure"
    )
    score_parser.add_argument(
        "soc_code",
        help="O*NET SOC code (e.g., 41-9022.00)",
    )
    score_parser.add_argument(
        "--title",
        help="Occupation title (fetched from O*NET if not provided)",
        default=None,
    )
    score_parser.add_argument(
        "--format",
        choices=["markdown", "json"],
        default="markdown",
        help="Output format (default: markdown)",
    )
    score_parser.add_argument(
        "--output", "-o",
        help="Output file path (default: stdout)",
        default=None,
    )
    score_parser.add_argument(
        "--no-agentic",
        action="store_true",
        help="Skip the agentic impact layer",
    )
    score_parser.add_argument(
        "--model",
        default="claude-sonnet-4-5-20250929",
        help="Anthropic model to use for scoring",
    )
    score_parser.add_argument(
        "--categories",
        nargs="+",
        help="Specific categories to score (default: all scorable)",
        default=None,
    )
    score_parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging",
    )

    # -- list-categories command --
    list_parser = subparsers.add_parser(
        "list-categories", help="List all scorable O*NET categories"
    )

    # -- demo command --
    demo_parser = subparsers.add_parser(
        "demo", help="Run a demo with sample data (no API keys needed)"
    )
    demo_parser.add_argument(
        "--format",
        choices=["markdown", "json"],
        default="markdown",
    )
    demo_parser.add_argument("--output", "-o", default=None)

    args = parser.parse_args(argv)

    if args.command == "list-categories":
        _cmd_list_categories()
    elif args.command == "demo":
        _cmd_demo(args)
    elif args.command == "score":
        _cmd_score(args)
    else:
        parser.print_help()


def _cmd_list_categories() -> None:
    print("Scorable O*NET categories:")
    for cat in SCORABLE_CATEGORIES:
        print(f"  - {cat.value}")


def _cmd_demo(args: argparse.Namespace) -> None:
    """Run a demo using the built-in sample data."""
    from .sample_data import build_sample_alert

    alert = build_sample_alert()
    if args.format == "json":
        output = render_json(alert)
    else:
        output = render_markdown(alert)

    if args.output:
        with open(args.output, "w") as f:
            f.write(output)
        print(f"Report written to {args.output}")
    else:
        print(output)


def _cmd_score(args: argparse.Namespace) -> None:
    """Score an occupation using O*NET data + LLM assessment."""
    if args.verbose:
        logging.basicConfig(level=logging.INFO)

    # Validate API keys
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("Error: ANTHROPIC_API_KEY environment variable not set.", file=sys.stderr)
        sys.exit(1)

    # Initialize clients
    onet = OnetClient()
    scorer = Scorer(model=args.model)

    # Fetch occupation title if not provided
    title = args.title
    if not title:
        try:
            summary = onet.get_category_sync(args.soc_code, OnetCategory.TASKS)
            title = args.soc_code  # Fallback
        except OnetApiError:
            title = args.soc_code

    # Determine which categories to score
    if args.categories:
        categories = [OnetCategory(c) for c in args.categories]
    else:
        categories = SCORABLE_CATEGORIES

    # Fetch O*NET data
    print(f"Fetching O*NET data for {args.soc_code}...", file=sys.stderr)
    onet_data = {}
    for cat in categories:
        try:
            items = onet.get_category_sync(args.soc_code, cat)
            onet_data[cat] = items
            print(f"  {cat.value}: {len(items)} items", file=sys.stderr)
        except OnetApiError as e:
            print(f"  {cat.value}: error ({e})", file=sys.stderr)
            onet_data[cat] = []

    # Run scoring pipeline
    print(f"Running scoring pipeline (agentic={'on' if not args.no_agentic else 'off'})...",
          file=sys.stderr)
    alert, agentic_scores = scorer.score_occupation(
        soc_code=args.soc_code,
        occupation_title=title,
        onet_data=onet_data,
        include_agentic=not args.no_agentic,
    )

    # Output
    if args.format == "json":
        output = render_json(alert, agentic_scores or None)
    else:
        output = render_markdown(alert, agentic_scores or None)

    if args.output:
        with open(args.output, "w") as f:
            f.write(output)
        print(f"Report written to {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
