"""Scholark-1 — Your autonomous research intelligence.

An MCP server for deep academic literature work.
Searches Semantic Scholar and Crossref. Returns human-readable results
with source attribution. All results should be manually verified.
"""

import re
from fastmcp import FastMCP
from apis import semantic_scholar, crossref

mcp = FastMCP(
    "scholark-1",
    instructions=(
        "Scholark-1 searches academic databases and returns paper metadata. "
        "IMPORTANT: All results come from external APIs (Semantic Scholar, Crossref) "
        "and should be treated as potentially incomplete. Always tell the user which "
        "source provided each result. If data is missing or a fallback source was used, "
        "say so explicitly. Never present these results as exhaustive — recommend the "
        "user verify important findings manually."
    ),
)


@mcp.tool()
async def search_papers(query: str, limit: int = 10) -> str:
    """Search for academic papers across Semantic Scholar and Crossref.

    Returns results from both sources with clear source attribution.
    Results may be incomplete — always verify important findings manually.

    Args:
        query: Search query (natural language or keywords)
        limit: Max results per source (default 10)
    """
    sections = []

    ss_results = await semantic_scholar.search(query, limit=limit)
    if "no results" not in ss_results.lower() and "unavailable" not in ss_results.lower():
        sections.append(f"=== Semantic Scholar Results ===\n\n{ss_results}")
    else:
        sections.append(f"=== Semantic Scholar ===\n{ss_results}")

    cr_results = await crossref.search(query, limit=limit)
    if "no results" not in cr_results.lower() and "unavailable" not in cr_results.lower():
        sections.append(f"=== Crossref Results ===\n\n{cr_results}")
    else:
        sections.append(f"=== Crossref ===\n{cr_results}")

    sections.append(
        "---\nNote: Results come from Semantic Scholar and Crossref APIs. "
        "These may not be exhaustive. Verify important references manually."
    )

    return "\n\n".join(sections)


@mcp.tool()
async def fetch_paper_details(paper_id: str) -> str:
    """Get detailed metadata for a specific paper.

    Tries Semantic Scholar first, falls back to Crossref if the paper_id is a DOI.
    Results should be verified against the original publication.

    Args:
        paper_id: DOI (e.g. '10.1234/test'), Semantic Scholar ID, or prefixed ID (e.g. 'DOI:10.1234/test')
    """
    ss_result = await semantic_scholar.get_paper_details(paper_id)

    if "could not fetch" not in ss_result.lower():
        return ss_result + (
            "\n\n---\nNote: Data from Semantic Scholar. Verify against the original publication."
        )

    # Fallback to Crossref only if it looks like a DOI
    if not re.match(r"^10\.\d{4,}/", paper_id):
        return (
            f"Could not find paper '{paper_id}' in Semantic Scholar.\n"
            "This doesn't look like a DOI, so Crossref fallback was skipped.\n"
            "Try using a DOI or Semantic Scholar paper ID."
        )

    cr_result = await crossref.get_paper_details(paper_id)
    if "could not fetch" not in cr_result.lower():
        return (
            f"(Semantic Scholar was unavailable for this paper — showing Crossref data)\n\n"
            f"{cr_result}\n\n---\nNote: Data from Crossref fallback. Verify against the original publication."
        )

    return (
        f"Could not find paper '{paper_id}' in either Semantic Scholar or Crossref.\n"
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

    Uses Semantic Scholar with full metadata fields. Falls back to Crossref
    if Semantic Scholar is unavailable. Results should be verified manually.

    Args:
        topic: Research topic or keywords
        year_start: Start year filter (optional)
        year_end: End year filter (optional)
        limit: Max results (default 10)
    """
    ss_result = await semantic_scholar.search_by_topic(
        topic, year_start=year_start, year_end=year_end, limit=limit
    )

    if "no results" not in ss_result.lower():
        return ss_result + (
            "\n\n---\nNote: Results from Semantic Scholar. "
            "May not be exhaustive — verify important references."
        )

    # Fallback to Crossref (no year filtering available via simple search)
    cr_result = await crossref.search(topic, limit=limit)
    fallback_note = "(Semantic Scholar had no results — falling back to Crossref"
    if year_start or year_end:
        fallback_note += ". Note: year filtering is not applied to Crossref fallback results"
    fallback_note += ")"

    return (
        f"{fallback_note}\n\n{cr_result}\n\n---\n"
        "Note: Results from Crossref fallback. Verify important references."
    )


@mcp.tool()
async def doi_to_bibtex(doi: str) -> str:
    """Convert a DOI to a BibTeX entry via content negotiation.

    Accepts DOI in various formats: bare (10.1234/test), URL (https://doi.org/10.1234/test),
    or prefixed (doi:10.1234/test).

    The BibTeX is fetched directly from doi.org — it reflects what the publisher registered.
    Always double-check that the BibTeX fields match your reference manager's expectations.

    Args:
        doi: The DOI to look up
    """
    return await crossref.get_bibtex(doi)


if __name__ == "__main__":
    mcp.run(transport="stdio")
