# Scholark-1

**[simohosio.com/scholark-1](https://simohosio.com/scholark-1/)**

Your autonomous research intelligence. Free and open source.

An MCP server that gives your AI agent direct access to real academic papers, real metadata, real BibTeX, and real open access PDFs. No hallucinated references. No copy-pasting from Google Scholar. It just works.

**Zero config to start.** Clone, install, go. All API keys are optional.

## Why Scholark?

Your AI assistant is brilliant at reasoning, but it can't search academic databases. It hallucinates paper titles, invents DOIs, and guesses at citation counts. Scholark fixes that.

- **4 databases searched in parallel** — Semantic Scholar, OpenAlex, Crossref, and Europe PMC
- **Deduplicated by DOI** — the same paper from different sources appears once, not four times
- **Every result cites its source** — you always know where data came from
- **BibTeX on demand** — any DOI to a BibTeX entry, ready for your .tex file
- **Open access PDFs** — finds free, legal versions of papers via Unpaywall
- **Citation context** — see the actual sentences where other papers cite a given work
- **No hallucinations** — every paper, every DOI, every citation count comes from a real API response

## Quick Start

One command, from any project:

```bash
claude mcp add -s project scholark-1 -- uvx --from git+https://github.com/SHosio/scholark-1 scholark-1
```

Or add it manually to your `.mcp.json`:

```json
{
  "mcpServers": {
    "scholark-1": {
      "type": "stdio",
      "command": "uvx",
      "args": ["--from", "git+https://github.com/SHosio/scholark-1", "scholark-1"]
    }
  }
}
```

That's it. Ask your AI assistant to search for papers and it will use Scholark automatically.

## Tools

| Tool | What it does |
|---|---|
| `search_papers` | Search 4 databases in parallel, deduplicated by DOI |
| `fetch_paper_details` | Deep metadata with 4-source fallback chain |
| `search_by_topic` | Topic search with optional year range filtering |
| `doi_to_bibtex` | Any DOI to a BibTeX entry — ready for your .bib file |
| `find_open_access` | Find free, legal PDFs via Unpaywall |
| `get_citation_context` | The actual sentences where other papers cite a work |

## Configuration

All configuration is optional. Without any `.env` file, 5 of 6 tools work immediately.

```bash
cp .env.example .env
```

| Variable | Required? | What it does | How to get it |
|---|---|---|---|
| `SEMANTIC_SCHOLAR_API_KEY` | No | Higher rate limits | [Free key](https://www.semanticscholar.org/product/api#api-key) |
| `OPENALEX_EMAIL` | No | Priority request queue | Just your email |
| `UNPAYWALL_EMAIL` | For `find_open_access` | Enables open access PDF lookup | Just your email |

**Without any keys:** `search_papers`, `fetch_paper_details`, `search_by_topic`, `doi_to_bibtex`, and `get_citation_context` all work. You get results from Semantic Scholar, OpenAlex, Crossref, and Europe PMC.

**Add your email for Unpaywall:** Unlocks `find_open_access` — no signup, no API key, just an email address for contact purposes.

**Add a Semantic Scholar API key:** Free to request, gives you a dedicated rate limit instead of sharing the pool.

## Works With

- **Claude Code** — spawned via MCP stdio transport
- **Claude Desktop** — same MCP registration
- **Cursor, Windsurf** — any MCP-compatible AI editor
- **Any MCP client** — standard protocol, no vendor lock-in

## How It Works

Scholark searches multiple academic databases and combines results intelligently:

- **Search** — queries all 4 sources in parallel via `asyncio.gather`
- **Deduplication** — removes duplicate papers across sources by DOI (first source wins)
- **Fallback** — if one source is down, the others still work. Errors are reported, never hidden.
- **Caching** — paper details and BibTeX entries are cached in SQLite with TTL (30-day details, 90-day BibTeX)
- **Attribution** — every result includes `[Source: ...]` so you know where it came from

## Credits & Data Sources

Scholark queries the following services. All data is retrieved in real-time — Scholark does not redistribute or repackage any data.

- **[Semantic Scholar](https://www.semanticscholar.org/)** by Allen Institute for AI — paper metadata, abstracts, TL;DRs, citation counts, citation contexts. [API License](https://www.semanticscholar.org/product/api/license).
- **[OpenAlex](https://openalex.org/)** — open scholarly metadata. [CC0](https://creativecommons.org/publicdomain/zero/1.0/).
- **[Crossref](https://www.crossref.org/)** — DOI metadata and BibTeX.
- **[Europe PMC](https://europepmc.org/)** — PubMed, PMC, and preprint metadata.
- **[Unpaywall](https://unpaywall.org/)** — open access PDF locations.

## Built By

[Professor Simo Hosio](https://simohosio.com)

Too busy to learn tools like this? You might be doing academia wrong. Check out the [PhD Power Trio Framework](https://edgeacademia.com/powertrio) — a better way to PhD.

## License

MIT

## Development

```bash
uv run pytest              # Run all tests
uv run pytest tests/test_file.py::test_name -v  # Run a single test
```
