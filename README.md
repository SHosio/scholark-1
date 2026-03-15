# Scholark-1

Your autonomous research intelligence. An MCP server for deep academic literature work.

## What it does

Scholark-1 searches **4 academic databases** in parallel, deduplicates results by DOI, and returns human-readable paper metadata with source attribution. It also finds open access PDFs via Unpaywall. Built for use with Claude Code and other MCP-compatible AI assistants.

### Sources

| Source | API Key | What it's good at |
|---|---|---|
| **Semantic Scholar** | Optional (higher rate limits) | CS, biomedical, broad coverage, TL;DRs, citation counts |
| **OpenAlex** | No (email optional) | 250M+ works, open metadata, broad coverage |
| **Crossref** | No | DOI metadata, BibTeX, publisher data |
| **Europe PMC** | No | PubMed + PMC + preprints, biomedical focus, full abstracts |
| **Unpaywall** | Email only | Open access PDF links, OA status, license info |

### Tools

| Tool | Description |
|---|---|
| `search_papers` | Search all sources in parallel, deduplicated by DOI |
| `fetch_paper_details` | Get detailed metadata for a paper (by DOI or Semantic Scholar ID) |
| `search_by_topic` | Topic search with optional year range filtering |
| `doi_to_bibtex` | Convert any DOI to a BibTeX entry |
| `find_open_access` | Find open access PDFs and OA status for a DOI via Unpaywall |
| `get_citation_context` | See how other papers cite a given paper — the actual sentences |

## Setup

```bash
# Install dependencies
uv sync

# Copy and fill in your config
cp .env.example .env
# Edit .env — add your email for Unpaywall (required) and optionally
# your Semantic Scholar API key and OpenAlex email

# Run the server
uv run python server.py
```

### MCP registration (Claude Code)

```json
{
  "mcpServers": {
    "scholark-1": {
      "type": "stdio",
      "command": "uv",
      "args": ["run", "--project", "/path/to/scholark-1", "python", "server.py"]
    }
  }
}
```

## Configuration

All config goes in `.env` (gitignored). Copy `.env.example` and fill in:

```bash
cp .env.example .env
```

| Variable | Required | How to get it |
|---|---|---|
| `SEMANTIC_SCHOLAR_API_KEY` | No (but avoids rate limits) | [semanticscholar.org/product/api](https://www.semanticscholar.org/product/api#api-key) — free, request a key |
| `OPENALEX_EMAIL` | No (gets polite pool) | Just your email address, no signup |
| `UNPAYWALL_EMAIL` | Yes, for `find_open_access` | Just your email address, no signup |

Without `SEMANTIC_SCHOLAR_API_KEY`, Semantic Scholar works but with stricter rate limits (100 req/5min).
Without `OPENALEX_EMAIL`, OpenAlex works but at lower priority in their request queue.
Without `UNPAYWALL_EMAIL`, the `find_open_access` tool will return an error. All other tools work fine.

## Architecture

- **`server.py`** — FastMCP entry point, 6 tools, deduplication layer, fallback chains
- **`apis/`** — One module per source (semantic_scholar, openalex, crossref, pubmed, unpaywall)
- **`apis/__init__.py`** — Shared HTTP helpers (`make_request`, `make_request_text`)
- **`apis/errors.py`** — `SourceUnavailable`, `RateLimited` exceptions
- **`cache.py`** — SQLite cache for DOI lookups (30-day paper details, 90-day BibTeX)

### Design

- **stdio transport** — spawned by Claude Code via `uv run`
- **All tools return human-readable strings** — output is consumed by an LLM
- **Every result states its source** — `[Source: Semantic Scholar]`, etc.
- **Exception-based fallback chain** — API clients raise `SourceUnavailable`, server catches and falls back
- **Cross-source deduplication** — `search_papers` removes duplicate DOIs across all 4 search sources
- **Search is parallel** (`asyncio.gather`), **details/topic are sequential fallback**
- **DOI cache** — paper details and BibTeX cached in SQLite with TTL
- **All APIs are free** for research and non-commercial use

## Development

```bash
# Run tests
uv run pytest

# Run a single test
uv run pytest tests/test_file.py::test_name -v
```
