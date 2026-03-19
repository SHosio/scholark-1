"""Scholark-1 — Your autonomous research intelligence.

An MCP server for deep academic literature work.
Searches Semantic Scholar, OpenAlex, Crossref, and Europe PMC.
Finds open access PDFs via Unpaywall.
Returns human-readable results with source attribution and cross-source deduplication.
All results should be manually verified.
"""

import asyncio
import re
from dotenv import load_dotenv
from fastmcp import FastMCP

load_dotenv()
from apis import semantic_scholar, crossref, openalex, pubmed, unpaywall
from apis.errors import SourceUnavailable
from cache import CacheDB

ALL_SOURCES = "Semantic Scholar, OpenAlex, Crossref, and Europe PMC"

mcp = FastMCP(
    "scholark-1",
    instructions=(
        "Scholark-1 searches academic databases and returns paper metadata. "
        f"IMPORTANT: All results come from external APIs ({ALL_SOURCES}, plus Unpaywall for OA) "
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



def _deduplicate_results(sections: list[str]) -> tuple[list[str], int]:
    """Remove duplicate papers across sections based on DOI.

    Papers are split on double newlines within each section. DOIs are extracted
    via regex. First occurrence wins (source order: SS > OpenAlex > Crossref >
    Europe PMC). Papers without a real DOI are always kept.
    """
    seen_dois: set[str] = set()
    deduped_sections: list[str] = []
    total_removed = 0

    for section in sections:
        # Split section into header + individual paper blocks
        blocks = section.split("\n\n")
        header = blocks[0]
        papers = blocks[1:] if len(blocks) > 1 else []

        # If this is an "unavailable" section (no papers), keep as-is
        if not papers or "unavailable" in header.lower():
            deduped_sections.append(section)
            continue

        kept = []
        for paper in papers:
            doi_match = re.search(r"DOI: (10\.\S+)", paper)
            if doi_match:
                doi = doi_match.group(1).lower().rstrip(".,;")
                if doi in seen_dois:
                    total_removed += 1
                    continue
                seen_dois.add(doi)
            kept.append(paper)

        if kept:
            deduped_sections.append(header + "\n\n" + "\n\n".join(kept))
        else:
            deduped_sections.append(f"{header}\n(all results were duplicates of earlier sources)")

    return deduped_sections, total_removed


async def _try_source(source_fn, name, query, limit):
    """Try a search source, return formatted section string."""
    try:
        return f"=== {name} Results ===\n\n{await source_fn(query, limit)}"
    except SourceUnavailable as e:
        return f"=== {name} ===\n{name} unavailable ({e.reason})."


@mcp.tool()
async def search_papers(query: str, limit: int = 10) -> str:
    """Search for academic papers across multiple databases.

    Searches Semantic Scholar, OpenAlex, Crossref, and Europe PMC in parallel.
    Results are deduplicated by DOI across sources. Returns results with clear
    source attribution. May be incomplete — always verify important findings manually.

    Args:
        query: Search query (natural language or keywords)
        limit: Max results per source (default 10)
    """
    results = await asyncio.gather(
        _try_source(semantic_scholar.search, "Semantic Scholar", query, limit),
        _try_source(openalex.search, "OpenAlex", query, limit),
        _try_source(crossref.search, "Crossref", query, limit),
        _try_source(pubmed.search, "Europe PMC", query, limit),
    )

    sections, dupes_removed = _deduplicate_results(list(results))

    note = (
        f"---\nNote: Results from {ALL_SOURCES}. "
        "These may not be exhaustive. Verify important references manually."
    )
    if dupes_removed:
        note += f"\n({dupes_removed} duplicate paper(s) removed across sources.)"

    sections.append(note)
    return "\n\n".join(sections)


@mcp.tool()
async def fetch_paper_details(paper_id: str) -> str:
    """Get detailed metadata for a specific paper.

    Tries Semantic Scholar first, then falls back through OpenAlex, Crossref,
    and Europe PMC for DOI-shaped identifiers.
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

    # Sequential fallback chain
    fallback_chain = [
        (semantic_scholar.get_paper_details, "Semantic Scholar"),
    ]

    # Only add DOI-capable sources if we have a DOI
    if is_doi:
        fallback_chain.extend([
            (openalex.get_paper_details, "OpenAlex"),
            (crossref.get_paper_details, "Crossref"),
            (pubmed.get_paper_details, "Europe PMC"),
        ])

    for source_fn, name in fallback_chain:
        try:
            query_id = normalized_id if is_doi and name != "Semantic Scholar" else paper_id
            result = await source_fn(query_id)
            if is_doi:
                cache.put(f"paper_details:{normalized_id}", result, name)
            fallback_note = " (fallback)" if name != "Semantic Scholar" else ""
            return result + f"\n\n---\nNote: Data from {name}{fallback_note}. Verify against the original publication."
        except SourceUnavailable:
            continue

    if not is_doi:
        return (
            f"Could not find paper '{paper_id}' in Semantic Scholar.\n"
            "This doesn't look like a DOI, so fallback was skipped.\n"
            "Try using a DOI or Semantic Scholar paper ID."
        )

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

    Sequential fallback: Semantic Scholar, OpenAlex, Europe PMC (all support
    year filtering), then Crossref (no year filtering).

    Args:
        topic: Research topic or keywords
        year_start: Start year filter (optional)
        year_end: End year filter (optional)
        limit: Max results (default 10)
    """
    # Sources that support year filtering
    year_sources = [
        (semantic_scholar.search_by_topic, "Semantic Scholar"),
        (openalex.search_by_topic, "OpenAlex"),
        (pubmed.search_by_topic, "Europe PMC"),
    ]

    for source_fn, name in year_sources:
        try:
            result = await source_fn(
                topic, year_start=year_start, year_end=year_end, limit=limit
            )
            fallback_note = " (fallback)" if name != "Semantic Scholar" else ""
            return result + (
                f"\n\n---\nNote: Results from {name}{fallback_note}. "
                "May not be exhaustive — verify important references."
            )
        except SourceUnavailable:
            continue

    # Crossref last — no year filtering
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
async def get_citation_context(paper_id: str, limit: int = 10) -> str:
    """See how other papers cite a given paper — the actual sentences where they reference it.

    Shows who cited the paper and what they said about it. Useful for understanding
    how a finding was received: supported, criticized, extended, or just mentioned
    in passing. Only available via Semantic Scholar.

    This tool can return a lot of text. Place its output at the end of your response,
    under a "Citation Context" heading.

    Args:
        paper_id: DOI (e.g. '10.1234/test') or Semantic Scholar paper ID
        limit: Max citing papers to return (default 10)
    """
    cache = _get_cache()
    cache_key = f"citation_context:{paper_id}:{limit}"
    cached = cache.get(cache_key)
    if cached:
        return cached + "\n\n(Cached result — citation contexts may have changed.)"

    try:
        result = await semantic_scholar.get_citation_context(paper_id, limit=limit)
        cache.put(cache_key, result, "Semantic Scholar")
        return result
    except SourceUnavailable as e:
        return f"Could not get citation context for '{paper_id}'. {e.reason}"


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


@mcp.tool()
async def find_open_access(doi: str) -> str:
    """Find open access versions of a paper by DOI via Unpaywall.

    Returns OA status, PDF links, host type (repository/publisher), version
    (published/accepted/submitted), and license info. Requires UNPAYWALL_EMAIL
    to be set in .env.

    Args:
        doi: The DOI to look up (e.g. '10.1234/test')
    """
    normalized = crossref.normalize_doi(doi)
    if not normalized:
        return "Please provide a valid DOI."

    cache = _get_cache()
    cached = cache.get(f"unpaywall:{normalized}")
    if cached:
        return cached + "\n\n[Source: Unpaywall (cached)]"

    try:
        result = await unpaywall.find_open_access(normalized)
        cache.put(f"unpaywall:{normalized}", result, "Unpaywall")
        return result
    except SourceUnavailable as e:
        return f"Could not check open access for DOI '{normalized}'. {e.reason}"



if __name__ == "__main__":
    mcp.run(transport="stdio")
