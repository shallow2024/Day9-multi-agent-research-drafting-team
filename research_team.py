"""Day 9: two-agent web research and technical report drafting team."""
from __future__ import annotations

import argparse
import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable, Protocol

DEFAULT_MODEL = "Qwen/Qwen2.5-Coder-32B-Instruct:featherless-ai"


@dataclass(frozen=True)
class Finding:
    title: str
    url: str
    snippet: str
    source: str = "DuckDuckGo"


class SearchClient(Protocol):
    def text(self, keywords: str, max_results: int = 5) -> Iterable[dict[str, Any]]: ...


class ResearcherAgent:
    """Searches the web and normalizes results into source-backed findings."""

    def __init__(self, search_client: SearchClient | None = None, max_results: int = 5):
        self.search_client = search_client
        self.max_results = max_results

    def research(self, topic: str) -> list[Finding]:
        client = self.search_client
        if client is None:
            try:
                from ddgs import DDGS
            except ImportError as exc:
                raise RuntimeError("Install ddgs to use the Researcher agent.") from exc
            client = DDGS()
        raw_results = client.text(topic, max_results=self.max_results)
        findings: list[Finding] = []
        for item in raw_results:
            title = str(item.get("title", "")).strip()
            url = str(item.get("href") or item.get("url") or "").strip()
            snippet = str(item.get("body") or item.get("snippet") or "").strip()
            if title and url and snippet:
                findings.append(Finding(title=title, url=url, snippet=snippet))
        if not findings:
            raise RuntimeError("The Researcher agent found no usable results. Try a broader topic.")
        return findings


class WriterAgent:
    """Turns source-backed findings into a Markdown technical report."""

    def __init__(self, model: str = DEFAULT_MODEL, client: Any | None = None):
        self.model = model
        self.client = client

    def draft(self, topic: str, findings: list[Finding]) -> str:
        if self.client is None:
            token = os.environ.get("HF_TOKEN")
            if not token:
                raise RuntimeError("HF_TOKEN is missing. Use --offline-demo for API-free testing.")
            from openai import OpenAI
            self.client = OpenAI(base_url="https://router.huggingface.co/v1", api_key=token)
        evidence = "\n\n".join(
            f"SOURCE {index}: {finding.title}\nURL: {finding.url}\nSNIPPET: {finding.snippet}"
            for index, finding in enumerate(findings, start=1)
        )
        response = self.client.chat.completions.create(
            model=self.model,
            temperature=0.2,
            max_tokens=1400,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are the Writer agent. Produce a polished technical Markdown report. "
                        "Use only the supplied source snippets. Do not invent facts. Cite claims as [1], [2], etc. "
                        "Include a title, short overview, key findings, practical implications, limitations, and references."
                    ),
                },
                {"role": "user", "content": f"Topic: {topic}\n\nResearcher findings:\n{evidence}"},
            ],
        )
        content = response.choices[0].message.content or ""
        if not content.strip():
            raise RuntimeError("The Writer agent returned an empty report.")
        return content.strip()


def offline_draft(topic: str, findings: list[Finding]) -> str:
    """Create a deterministic report without an LLM for free local testing."""
    lines = [f"# {topic}", "", "## Overview", "", "This offline draft was assembled from the Researcher agent's source snippets.", "", "## Key findings", ""]
    for index, finding in enumerate(findings, start=1):
        lines.extend([f"### {index}. {finding.title}", "", finding.snippet, f"\nSource: [{index}]({finding.url})", ""])
    lines.extend(["## Limitations", "", "This offline mode extracts search snippets and does not perform LLM synthesis.", "", "## References", ""])
    lines.extend(f"[{index}]: {finding.url} \"{finding.title}\"" for index, finding in enumerate(findings, start=1))
    return "\n".join(lines)


def save_report(topic: str, findings: list[Finding], report: str, output_dir: Path) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    slug = "".join(character.lower() if character.isalnum() else "-" for character in topic).strip("-")
    report_path = output_dir / f"{slug or 'research'}-report.md"
    evidence_path = output_dir / f"{slug or 'research'}-evidence.json"
    report_path.write_text(report + "\n", encoding="utf-8")
    evidence_path.write_text(json.dumps([asdict(item) for item in findings], indent=2, ensure_ascii=False), encoding="utf-8")
    return report_path, evidence_path


def run(topic: str, output_dir: Path, max_results: int, model: str, offline_demo: bool) -> tuple[Path, Path]:
    researcher = ResearcherAgent(max_results=max_results)
    findings = researcher.research(topic)
    report = offline_draft(topic, findings) if offline_demo else WriterAgent(model=model).draft(topic, findings)
    report_path, evidence_path = save_report(topic, findings, report, output_dir)
    print(f"Researcher findings: {len(findings)}")
    print(f"Writer mode: {'offline-demo' if offline_demo else 'huggingface'}")
    print(f"Report: {report_path}")
    print(f"Evidence: {evidence_path}")
    return report_path, evidence_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Research a topic with DuckDuckGo, then draft a cited Markdown report.")
    parser.add_argument("topic", help="Research topic, e.g. 'Python AST code safety'")
    parser.add_argument("--max-results", type=int, default=5)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--output-dir", type=Path, default=Path("reports"))
    parser.add_argument("--offline-demo", action="store_true", help="Skip Hugging Face drafting and assemble a deterministic report")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run(args.topic, args.output_dir, args.max_results, args.model, args.offline_demo)
