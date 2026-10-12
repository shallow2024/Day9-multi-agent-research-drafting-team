# Day 9 — Multi-Agent Research & Drafting Team

A two-agent CLI pipeline for source-backed technical research:

1. The **Researcher Agent** searches DuckDuckGo through the maintained `ddgs` package (the successor to `duckduckgo-search`) and normalizes result titles, URLs, and snippets.
2. The **Writer Agent** sends the evidence to a Hugging Face hosted Qwen model and drafts a cited Markdown report.

The orchestration is intentionally lightweight rather than tied to a large agent framework. This keeps the portfolio project easy to install, test, and understand while still demonstrating agent roles, hand-off, source grounding, and report generation.

> The Writer must use only the supplied snippets. Search snippets can be incomplete, so review the linked sources before relying on a report.

## Architecture

See [docs/architecture.md](docs/architecture.md).

```text
Topic
  ↓
Researcher Agent → DuckDuckGo search → normalized findings + URLs
  ↓ hand-off
Writer Agent → Hugging Face Router / Qwen → cited Markdown report
  ↓
Markdown report + evidence JSON
```

## Requirements

- Python 3.10–3.12 recommended.
- Internet access for DuckDuckGo search.
- `HF_TOKEN` for AI drafting mode.
- No HF token is required for `--offline-demo`.

The default Writer model is:

```text
Qwen/Qwen2.5-Coder-32B-Instruct:featherless-ai
```

You can change it with `--model` if another model/provider route is available to your Hugging Face account.

## Windows PowerShell setup

```powershell
git clone https://github.com/shallow2024/Day9-multi-agent-research-drafting-team.git
cd D:\Day9-multi-agent-research-drafting-team

py -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Test without Hugging Face credits

The offline demo still uses DuckDuckGo research, but skips the Writer LLM and creates a deterministic Markdown report:

```powershell
.\.venv\Scripts\python.exe research_team.py `
  "Python AST code safety" `
  --offline-demo
```

The command creates files under `reports\`:

```text
reports\python-ast-code-safety-report.md
reports\python-ast-code-safety-evidence.json
```

## Run the full two-agent flow

Set your Hugging Face token for the current PowerShell session:

```powershell
$env:HF_TOKEN = "hf_your_token_here"
```

Then run:

```powershell
.\.venv\Scripts\python.exe research_team.py `
  "Python AST code safety"
```

Limit the number of search results:

```powershell
.\.venv\Scripts\python.exe research_team.py `
  "FastAPI error handling" `
  --max-results 3
```

Choose another model route:

```powershell
.\.venv\Scripts\python.exe research_team.py `
  "Python AST code safety" `
  --model "Qwen/Qwen2.5-Coder-32B-Instruct:featherless-ai"
```

The Writer calls:

```text
https://router.huggingface.co/v1/chat/completions
```

## Run tests

The tests do not call DuckDuckGo or Hugging Face. They use fake search and model clients:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

## What each agent does

### Researcher Agent

- Receives a topic.
- Searches DuckDuckGo.
- Extracts title, URL, and snippet.
- Discards incomplete results.
- Hands source-backed `Finding` objects to the Writer.

### Writer Agent

- Receives the topic and findings.
- Sends the evidence to Qwen through Hugging Face.
- Requests Markdown with citations such as `[1]` and `[2]`.
- Rejects an empty response.
- Saves the report and the raw evidence separately.

## Limitations

- DuckDuckGo snippets are discovery material, not a substitute for reading the linked pages.
- The pipeline does not independently fact-check sources.
- Search results can change between runs.
- Hosted inference requires available Hugging Face credits/provider capacity.
- The project uses a framework-light orchestration layer. It demonstrates agent roles and hand-off without hiding the mechanics behind CrewAI abstractions.

## License

MIT. See [LICENSE](LICENSE).
