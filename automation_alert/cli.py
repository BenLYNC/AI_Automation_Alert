"""CLI entry point for the Automation Alert system.

Usage:
    # Free tier (Gemini) — default:
    automation-alert score 41-9022.00 --title "Real Estate Sales Agents"

    # Anthropic (paid):
    automation-alert score 41-9022.00 --provider anthropic --title "Real Estate Sales Agents"

    # Specific model:
    automation-alert score 15-1252.00 --provider gemini --model gemini-1.5-pro --format json

    # Demo (no API keys needed):
    automation-alert demo
"""

from __future__ import annotations

import argparse
import logging
import os
import sys

from .llm_client import AVAILABLE_MODELS, DEFAULT_MODELS
from .models import OnetCategory, SCORABLE_CATEGORIES
from .onet_client import OnetClient, OnetApiError
from .renderer import render_json, render_markdown
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
        "--provider", "-p",
        choices=["gemini", "anthropic"],
        default="gemini",
        help="LLM provider (default: gemini — free tier)",
    )
    score_parser.add_argument(
        "--model", "-m",
        default=None,
        help="Model name (uses provider default if not specified)",
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
    subparsers.add_parser(
        "list-categories", help="List all scorable O*NET categories"
    )

    # -- list-models command --
    subparsers.add_parser(
        "list-models", help="List available LLM providers and models"
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
    elif args.command == "list-models":
        _cmd_list_models()
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


def _cmd_list_models() -> None:
    print("Available LLM providers and models:\n")
    for provider, models in AVAILABLE_MODELS.items():
        default = DEFAULT_MODELS[provider]
        env_var = "GEMINI_API_KEY" if provider == "gemini" else "ANTHROPIC_API_KEY"
        cost = "FREE tier available" if provider == "gemini" else "Paid (starts at $3/M input tokens)"
        print(f"  {provider} ({cost})")
        print(f"    API key env var: {env_var}")
        for m in models:
            marker = " (default)" if m == default else ""
            print(f"    - {m}{marker}")
        print()


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

    # Validate API key for chosen provider
    provider = args.provider
    if provider == "gemini" and not os.environ.get("GEMINI_API_KEY"):
        print(
            "Error: GEMINI_API_KEY not set.\n"
            "Get a free key at: https://aistudio.google.com/apikey\n"
            "Then: export GEMINI_API_KEY=your_key",
            file=sys.stderr,
        )
        sys.exit(1)
    elif provider == "anthropic" and not os.environ.get("ANTHROPIC_API_KEY"):
        print(
            "Error: ANTHROPIC_API_KEY not set.\n"
            "Get a key at: https://console.anthropic.com/\n"
            "Then: export ANTHROPIC_API_KEY=sk-ant-...",
            file=sys.stderr,
        )
        sys.exit(1)

    # Initialize clients
    onet = OnetClient()
    scorer = Scorer(provider=provider, model=args.model)

    model_name = args.model or DEFAULT_MODELS.get(provider, "default")
    print(f"Using {provider}/{model_name}", file=sys.stderr)

    # Fetch occupation title if not provided
    title = args.title
    if not title:
        try:
            onet.get_category_sync(args.soc_code, OnetCategory.TASKS)
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
