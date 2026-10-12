from pathlib import Path

import pytest

from research_team import Finding, ResearcherAgent, WriterAgent, offline_draft, save_report


class FakeSearch:
    def text(self, keywords, max_results=5):
        assert keywords == "Python AST safety"
        return [
            {"title": "Python AST documentation", "href": "https://docs.python.org/3/library/ast.html", "body": "The ast module helps process Python syntax trees."},
            {"title": "Safe execution guide", "href": "https://example.com/safety", "body": "Generated code should be validated before execution."},
        ][:max_results]


def test_researcher_normalizes_search_results():
    findings = ResearcherAgent(FakeSearch(), max_results=2).research("Python AST safety")
    assert len(findings) == 2
    assert findings[0].url.startswith("https://")
    assert findings[0].source == "DuckDuckGo"


def test_offline_draft_contains_sources_and_references():
    findings = [Finding("Title", "https://example.com", "A useful fact.")]
    report = offline_draft("Demo topic", findings)
    assert "# Demo topic" in report
    assert "https://example.com" in report
    assert "## References" in report


def test_writer_uses_openai_compatible_client():
    class FakeCompletions:
        def create(self, **kwargs):
            assert kwargs["model"] == "test-model"
            return type("Response", (), {"choices": [type("Choice", (), {"message": type("Message", (), {"content": "# Draft report"})()})()]})()

    client = type("Client", (), {"chat": type("Chat", (), {"completions": FakeCompletions()})()})()
    report = WriterAgent(model="test-model", client=client).draft(
        "Demo", [Finding("Title", "https://example.com", "Fact")]
    )
    assert report == "# Draft report"


def test_save_report_writes_markdown_and_json(tmp_path: Path):
    findings = [Finding("Title", "https://example.com", "Fact")]
    report_path, evidence_path = save_report("Demo Topic", findings, "# Report", tmp_path)
    assert report_path.read_text(encoding="utf-8") == "# Report\n"
    assert evidence_path.exists()


def test_writer_requires_hf_token_without_client(monkeypatch):
    monkeypatch.delenv("HF_TOKEN", raising=False)
    with pytest.raises(RuntimeError, match="HF_TOKEN"):
        WriterAgent().draft("Demo", [Finding("Title", "https://example.com", "Fact")])
