"""Scholark-1 — Your autonomous research intelligence.

An MCP server for deep academic literature work.
Searches Semantic Scholar, OpenAlex, and Crossref. Returns human-readable results
with source attribution. All results should be manually verified.
"""

import asyncio
import re
from fastmcp import FastMCP
from apis import semantic_scholar, crossref, openalex
from apis.errors import SourceUnavailable
from cache import CacheDB

mcp = FastMCP(
    "scholark-1",
    instructions=(
        "Scholark-1 searches academic databases and returns paper metadata. "
        "IMPORTANT: All results come from external APIs (Semantic Scholar, OpenAlex, Crossref) "
        "and should be treated as potentially incomplete. Always tell the user which "
        "source provided each result. If data is missing or a fallback source was used, "
        "say so explicitly. Never present these results as exhaustive — recommend the "
        "user verify important findings manually."
    ),
)

# Lazy-initialized cache — avoids creating SQLite DB on import (important for tests)
_cache: CacheDB | None = None


def _get_cache() -> CacheDB:
    global _cache
    if _cache is None:
        _cache = CacheDB()
    return _cache


async def _try_source(source_fn, name, query, limit):
    """Try a search source, return formatted section string."""
    try:
        return f"=== {name} Results ===\n\n{await source_fn(query, limit)}"
    except SourceUnavailable as e:
        return f"=== {name} ===\n{name} unavailable ({e.reason})."


@mcp.tool()
async def search_papers(query: str, limit: int = 10) -> str:
    """Search for academic papers across Semantic Scholar, OpenAlex, and Crossref.

    Returns results from all available sources with clear source attribution.
    Results may be incomplete — always verify important findings manually.

    Args:
        query: Search query (natural language or keywords)
        limit: Max results per source (default 10)
    """
    results = await asyncio.gather(
        _try_source(semantic_scholar.search, "Semantic Scholar", query, limit),
        _try_source(openalex.search, "OpenAlex", query, limit),
        _try_source(crossref.search, "Crossref", query, limit),
    )

    sections = list(results)
    sections.append(
        "---\nNote: Results come from Semantic Scholar, OpenAlex, and Crossref APIs. "
        "These may not be exhaustive. Verify important references manually."
    )

    return "\n\n".join(sections)


@mcp.tool()
async def fetch_paper_details(paper_id: str) -> str:
    """Get detailed metadata for a specific paper.

    Tries Semantic Scholar first, falls back to OpenAlex and Crossref for DOIs.
    Results should be verified against the original publication.

    Args:
        paper_id: DOI (e.g. '10.1234/test'), Semantic Scholar ID, or prefixed ID
    """
    # Normalize DOI for cache lookup
    is_doi = bool(re.match(r"^10\.\d{4,}/", paper_id))
    normalized_id = crossref.normalize_doi(paper_id) if is_doi else paper_id
    cache = _get_cache()

    # Check cache for DOI-shaped identifiers
    if is_doi:
        cached = cache.get(f"paper_details:{normalized_id}")
        if cached:
            return cached + "\n\n---\nNote: Cached result. Verify against the original publication."

    # Try Semantic Scholar first
    try:
        result = await semantic_scholar.get_paper_details(paper_id)
        if is_doi:
            cache.put(f"paper_details:{normalized_id}", result, "Semantic Scholar")
        return result + "\n\n---\nNote: Data from Semantic Scholar. Verify against the original publication."
    except SourceUnavailable:
        pass

    # Non-DOI identifiers: no fallback
    if not is_doi:
        return (
            f"Could not find paper '{paper_id}' in Semantic Scholar.\n"
            "This doesn't look like a DOI, so fallback was skipped.\n"
            "Try using a DOI or Semantic Scholar paper ID."
        )

    # DOI fallback: OpenAlex → Crossref
    for source_fn, name in [(openalex.get_paper_details, "OpenAlex"), (crossref.get_paper_details, "Crossref")]:
        try:
            result = await source_fn(normalized_id)
            cache.put(f"paper_details:{normalized_id}", result, name)
            return result + f"\n\n---\nNote: Data from {name} (fallback). Verify against the original publication."
        except SourceUnavailable:
            continue

    return (
        f"Could not find paper '{paper_id}' in any source.\n"
        "Please check the identifier and try again."
    )


@mcp.tool()
async def search_by_topic(
    topic: str,
    year_start: int | None = None,
    year_end: int | None = None,
    limit: int = 10,
) -> str:
    """Search for papers by topic with optional year range filtering.

    Tries Semantic Scholar first (year filtering supported), then OpenAlex
    (year filtering supported), then Crossref (no year filtering).

    Args:
        topic: Research topic or keywords
        year_start: Start year filter (optional)
        year_end: End year filter (optional)
        limit: Max results (default 10)
    """
    # Try Semantic Scholar
    try:
        result = await semantic_scholar.search_by_topic(
            topic, year_start=year_start, year_end=year_end, limit=limit
        )
        return result + (
            "\n\n---\nNote: Results from Semantic Scholar. "
            "May not be exhaustive — verify important references."
        )
    except SourceUnavailable:
        pass

    # Try OpenAlex (supports year filtering)
    try:
        result = await openalex.search_by_topic(
            topic, year_start=year_start, year_end=year_end, limit=limit
        )
        return (
            f"(OpenAlex fallback)\n\n{result}\n\n---\n"
            "Note: Results from OpenAlex fallback. Verify important references."
        )
    except SourceUnavailable:
        pass

    # Try Crossref (no year filtering)
    try:
        result = await crossref.search(topic, limit=limit)
        note = "(Crossref fallback"
        if year_start or year_end:
            note += " — year filtering not applied"
        note += ")"
        return (
            f"{note}\n\n{result}\n\n---\n"
            "Note: Results from Crossref fallback. Verify important references."
        )
    except SourceUnavailable:
        pass

    return "No sources returned results for this topic."


@mcp.tool()
async def doi_to_bibtex(doi: str) -> str:
    """Convert a DOI to a BibTeX entry via content negotiation.

    Accepts DOI in various formats: bare (10.1234/test), URL (https://doi.org/10.1234/test),
    or prefixed (doi:10.1234/test).

    Args:
        doi: The DOI to look up
    """
    normalized = crossref.normalize_doi(doi)
    if not normalized:
        return "Please provide a DOI."

    cache = _get_cache()
    cached = cache.get(f"bibtex:{normalized}")
    if cached:
        return cached

    try:
        result = await crossref.get_bibtex(doi)
        cache.put(f"bibtex:{normalized}", result, "crossref")
        return result
    except SourceUnavailable as e:
        return f"Could not retrieve BibTeX for DOI '{normalized}'. {e.reason}"


if __name__ == "__main__":
    mcp.run(transport="stdio")
