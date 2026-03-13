"""Semantic Scholar API client for Scholark-1."""

from apis import make_request

BASE_URL = "https://api.semanticscholar.org/graph/v1"

SEARCH_FIELDS = (
    "title,authors,year,externalIds,abstract,venue,"
    "isOpenAccess,openAccessPdf,tldr,citationCount"
)


def format_paper(paper: dict) -> str:
    """Format a Semantic Scholar paper into human-readable text with source attribution."""
    title = paper.get("title") or "No title"
    authors = ", ".join(a.get("name", "Unknown") for a in paper.get("authors", []))
    year = paper.get("year") or "Year unknown"
    ext_ids = paper.get("externalIds") or {}
    doi = ext_ids.get("DOI", "Not available")
    venue = paper.get("venue") or "Not available"
    abstract = paper.get("abstract") or "Not available"
    citations = paper.get("citationCount", "Unknown")
    is_open = "Yes" if paper.get("isOpenAccess") else "No"
    pdf_data = paper.get("openAccessPdf") or {}
    pdf_url = pdf_data.get("url", "Not available")
    tldr_data = paper.get("tldr") or {}
    tldr = tldr_data.get("text", "")

    lines = [
        f"**{title}**",
        f"  Authors: {authors or 'Not available'}",
        f"  Year: {year}",
        f"  DOI: {doi}",
        f"  Venue: {venue}",
        f"  Citations: {citations}",
        f"  Open Access: {is_open}",
        f"  PDF: {pdf_url}",
        f"  Abstract: {abstract}",
    ]
    if tldr:
        lines.append(f"  TL;DR: {tldr}")
    lines.append("  [Source: Semantic Scholar]")
    return "\n".join(lines)


async def search(query: str, limit: int = 10) -> str:
    """Search Semantic Scholar for papers matching query."""
    if not query.strip():
        return "Please provide a search query."

    truncated = len(query) > 300
    q = query[:300] if truncated else query

    data = await make_request(
        f"{BASE_URL}/paper/search",
        params={"query": q, "limit": limit, "fields": SEARCH_FIELDS},
    )

    if not data or "data" not in data or not data["data"]:
        return "Semantic Scholar returned no results or was unavailable."

    results = []
    if truncated:
        results.append("Note: Query was truncated to 300 characters.")
    for paper in data["data"]:
        results.append(format_paper(paper))

    return "\n\n".join(results)


async def get_paper_details(paper_id: str) -> str:
    """Fetch detailed metadata for a specific paper."""
    data = await make_request(
        f"{BASE_URL}/paper/{paper_id}",
        params={"fields": SEARCH_FIELDS},
    )

    if not data:
        return f"Could not fetch paper details for '{paper_id}' from Semantic Scholar."

    return format_paper(data)


async def search_by_topic(
    topic: str, year_start: int | None = None, year_end: int | None = None, limit: int = 10
) -> str:
    """Search by topic with optional year filtering."""
    if not topic.strip():
        return "Please provide a topic."

    truncated = len(topic) > 300
    q = topic[:300] if truncated else topic

    params = {"query": q, "limit": limit, "fields": SEARCH_FIELDS}
    if year_start is not None and year_end is not None:
        params["year"] = f"{year_start}-{year_end}"
    elif year_start is not None:
        params["year"] = f"{year_start}-"
    elif year_end is not None:
        params["year"] = f"-{year_end}"

    data = await make_request(f"{BASE_URL}/paper/search", params=params)

    if not data or "data" not in data or not data["data"]:
        return "Semantic Scholar returned no results for this topic."

    results = []
    if truncated:
        results.append("Note: Query was truncated to 300 characters.")
    for paper in data["data"]:
        results.append(format_paper(paper))

    return "\n\n".join(results)
