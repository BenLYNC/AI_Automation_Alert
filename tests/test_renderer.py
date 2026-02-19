"""Tests for the output renderer (markdown + JSON)."""

from __future__ import annotations

import json

from automation_alert.renderer import render_json, render_markdown
from automation_alert.sample_data import build_sample_alert


class TestRenderMarkdown:
    def test_contains_header(self):
        alert = build_sample_alert()
        md = render_markdown(alert)
        assert "# 41-9022.00" in md
        assert "Real Estate Sales Agents" in md

    def test_contains_category_sections(self):
        alert = build_sample_alert()
        md = render_markdown(alert)
        assert "Tasks" in md
        assert "Skills" in md

    def test_contains_exposure_legend(self):
        alert = build_sample_alert()
        md = render_markdown(alert)
        assert "Exposure Level Legend" in md
        assert "E0" in md
        assert "E11" in md


class TestRenderJson:
    def test_valid_json(self):
        alert = build_sample_alert()
        output = render_json(alert)
        data = json.loads(output)
        assert data["soc_code"] == "41-9022.00"

    def test_includes_category_summaries(self):
        alert = build_sample_alert()
        output = render_json(alert)
        data = json.loads(output)
        assert len(data["category_summaries"]) == 2
