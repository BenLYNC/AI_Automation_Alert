"""Tests for the CLI entry point."""

from __future__ import annotations

import pytest

from automation_alert.cli import main


class TestCLI:
    def test_list_categories(self, capsys):
        main(["list-categories"])
        out = capsys.readouterr().out
        assert "tasks" in out
        assert "skills" in out

    def test_list_models(self, capsys):
        main(["list-models"])
        out = capsys.readouterr().out
        assert "gemini" in out
        assert "anthropic" in out
        assert "gemini-2.0-flash" in out

    def test_demo_markdown(self, capsys):
        main(["demo"])
        out = capsys.readouterr().out
        assert "41-9022.00" in out
        assert "Real Estate Sales Agents" in out

    def test_demo_json(self, capsys):
        main(["demo", "--format", "json"])
        out = capsys.readouterr().out
        import json
        data = json.loads(out)
        assert data["soc_code"] == "41-9022.00"

    def test_demo_output_file(self, tmp_path, capsys):
        path = str(tmp_path / "report.md")
        main(["demo", "--output", path])
        with open(path) as f:
            content = f.read()
        assert "Real Estate Sales Agents" in content

    def test_no_command_prints_help(self, capsys):
        main([])
        out = capsys.readouterr().out
        assert "automation-alert" in out or "usage" in out.lower()

    def test_score_missing_gemini_key(self, monkeypatch, capsys):
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        with pytest.raises(SystemExit) as exc_info:
            main(["score", "41-9022.00", "--title", "Test"])
        assert exc_info.value.code == 1
        err = capsys.readouterr().err
        assert "GEMINI_API_KEY" in err

    def test_score_missing_anthropic_key(self, monkeypatch, capsys):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        with pytest.raises(SystemExit) as exc_info:
            main(["score", "41-9022.00", "--provider", "anthropic", "--title", "Test"])
        assert exc_info.value.code == 1
        err = capsys.readouterr().err
        assert "ANTHROPIC_API_KEY" in err
