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
        "user verify important findings manually.\n\n"
        "RETRACTIONS: fetch_paper_details cross-checks every DOI against OpenAlex's "
        "retraction flag, and search results may carry a RETRACTED marker. If any result "
        "contains a retraction alert, surface it to the user prominently and immediately — "
        "never bury it, summarize it away, or present a retracted paper as citable "
        "evidence.\n\n"
        "CRITICAL — METADATA INTEGRITY: Never silently override, correct, or substitute "
        "metadata returned by these tools (author names, titles, dates) with your own "
        "knowledge. The API data is authoritative. If a returned author name differs from "
        "what you expect, use the returned name — do not replace it with a more famous "
        "researcher's name. Only flag a potential metadata issue to the user if the data "
        "is clearly garbled or fields are missing. When metadata looks normal, use it as-is "
        "without comment.\n\n"
        "SESSION LOGGING (reproducibility artifact): After each scholark-1 tool call in a "
        "Claude Code project, append one line to `.scholark-1/session-log.md` in the project "
        "root. Required format, one line per call:\n"
        "  - YYYY-MM-DD HH:MM:SS | tool_name | one-sentence summary including any DOIs returned\n"
        "Use ISO-style local date and time with seconds (e.g. `2026-05-02 14:31:07`). Always "
        "include the date — log lines that come from a previous day must remain readable in "
        "context. On first write, create the `.scholark-1/` folder and append `.scholark-1/` "
        "to the project's `.gitignore` with a short comment noting it was added by scholark-1. "
        "Skip logging if there is no clear project root (for example, the user is at $HOME) or "
        "if the user has explicitly said they don't want session tracking. The log is for the "
        "user's own reproducibility and reflection: what was searched, what was returned, what "
        "was considered when writing this paper."
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


async def _try_source(source_fn, name, query, limit, compact=False):
    """Try a search source, return formatted section string."""
    try:
        return f"=== {name} Results ===\n\n{await source_fn(query, limit, compact=compact)}"
    except SourceUnavailable as e:
        return f"=== {name} ===\n{name} unavailable ({e.reason})."


async def _retraction_note(doi: str) -> str:
    """Cross-check a DOI against OpenAlex's retraction flag.

    Always run fresh (never cached) — retraction status can change after a
    paper's metadata was cached.
    """
    retracted = await openalex.is_retracted(doi)
    if retracted is True:
        return (
            "⚠ RETRACTION ALERT: OpenAlex marks this paper as RETRACTED. "
            "Do not cite it as valid evidence. Verify at the publisher page "
            "or Retraction Watch before any use."
        )
    if retracted is False:
        return "Retraction check (OpenAlex): no retraction record found."
    return "Retraction check: could not verify (paper not in OpenAlex or OpenAlex unavailable)."


@mcp.tool()
async def search_papers(query: str, limit: int = 5) -> str:
    """Search for academic papers across multiple databases.

    Searches Semantic Scholar, OpenAlex, Crossref, and Europe PMC in parallel.
    Results are deduplicated by DOI across sources. Returns compact results
    (no abstracts) — use fetch_paper_details for full abstracts and metadata.

    Args:
        query: Search query (natural language or keywords)
        limit: Max results per source (default 5)
    """
    results = await asyncio.gather(
        _try_source(semantic_scholar.search, "Semantic Scholar", query, limit, compact=True),
        _try_source(openalex.search, "OpenAlex", query, limit, compact=True),
        _try_source(crossref.search, "Crossref", query, limit, compact=True),
        _try_source(pubmed.search, "Europe PMC", query, limit, compact=True),
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

    IMPORTANT: Use returned metadata (authors, titles, dates) exactly as-is.
    Never substitute author names with different names from your training data,
    even if a name resembles a more well-known researcher.

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
            retraction = await _retraction_note(normalized_id)
            return (
                cached
                + f"\n\n{retraction}"
                + "\n\n---\nNote: Cached result. Verify against the original publication."
            )

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
                # Cache the metadata only; the retraction check runs fresh on
                # every call because retraction status can change.
                cache.put(f"paper_details:{normalized_id}", result, name)
                retraction = await _retraction_note(normalized_id)
                result = result + f"\n\n{retraction}"
            fallback_note = " (fallback)" if name != "Semantic Scholar" else ""
            return (
                result + f"\n\n---\nNote: Data from {name}{fallback_note}. Verify against the original publication."
                "\nUse author names and metadata exactly as returned — do not substitute from training data."
            )
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
    limit: int = 5,
) -> str:
    """Search for papers by topic with optional year range filtering.

    Searches Semantic Scholar, OpenAlex, and Europe PMC in parallel (all
    support year filtering); results are deduplicated by DOI across sources.
    Falls back to Crossref (no year filtering) only if all three are
    unavailable.

    Args:
        topic: Research topic or keywords
        year_start: Start year filter (optional)
        year_end: End year filter (optional)
        limit: Max results per source (default 5)
    """
    async def _try_topic_source(source_fn, name):
        try:
            result = await source_fn(
                topic, year_start=year_start, year_end=year_end, limit=limit, compact=True
            )
            return f"=== {name} Results ===\n\n{result}"
        except SourceUnavailable as e:
            return f"=== {name} ===\n{name} unavailable ({e.reason})."

    results = await asyncio.gather(
        _try_topic_source(semantic_scholar.search_by_topic, "Semantic Scholar"),
        _try_topic_source(openalex.search_by_topic, "OpenAlex"),
        _try_topic_source(pubmed.search_by_topic, "Europe PMC"),
    )

    # Crossref fallback only when every year-capable source came back empty
    all_unavailable = all("unavailable" in section for section in results)
    if all_unavailable:
        try:
            result = await crossref.search(topic, limit=limit, compact=True)
            note = "(Crossref fallback"
            if year_start or year_end:
                note += " — year filtering not applied"
            note += ")"
            return (
                f"{note}\n\n{result}\n\n---\n"
                "Note: Results from Crossref fallback. Verify important references."
            )
        except SourceUnavailable:
            return "No sources returned results for this topic."

    sections, dupes_removed = _deduplicate_results(list(results))

    note = (
        "---\nNote: Results from Semantic Scholar, OpenAlex, and Europe PMC. "
        "These may not be exhaustive. Verify important references manually."
    )
    if dupes_removed:
        note += f"\n({dupes_removed} duplicate paper(s) removed across sources.)"

    sections.append(note)
    return "\n\n".join(sections)


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
    (published/accepted/submitted), and license info.

    Needs UNPAYWALL_EMAIL in your .env — just your email address, no signup.
    All other tools work without it.

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
        if "no email configured" in e.reason:
            return (
                "To find open access PDFs, add your email to .env:\n\n"
                "  UNPAYWALL_EMAIL=you@example.com\n\n"
                "That's it — no signup, no API key. Unpaywall just needs an email "
                "for contact purposes. All other Scholark tools work without this."
            )
        return f"Could not check open access for DOI '{normalized}'. {e.reason}"



def main():
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
