"""Tests for the sample data module (validates end-to-end pipeline with known data)."""

from __future__ import annotations

from automation_alert.sample_data import build_sample_alert


class TestSampleData:
    def test_builds_successfully(self):
        alert = build_sample_alert()
        assert alert.soc_code == "41-9022.00"
        assert alert.occupation_title == "Real Estate Sales Agents"

    def test_has_category_summaries(self):
        alert = build_sample_alert()
        assert len(alert.category_summaries) == 2  # tasks + skills

    def test_items_have_scores(self):
        alert = build_sample_alert()
        for cs in alert.category_summaries:
            assert cs.item_count > 0
            for item in cs.items:
                assert 0 <= item.time_saved_low_pct <= item.time_saved_high_pct <= 100

    def test_risk_label(self):
        alert = build_sample_alert()
        assert alert.overall_automation_risk_label in {
            "Low", "Moderate", "Significant", "High", "Very High"
        }

    def test_dominant_exposure_vectors(self):
        alert = build_sample_alert()
        assert len(alert.dominant_exposure_vectors) > 0
