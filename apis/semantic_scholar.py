"""Semantic Scholar API client for Scholark-1."""

import os
import httpx
from apis import make_request
from apis.errors import SourceUnavailable, RateLimited

BASE_URL = "https://api.semanticscholar.org/graph/v1"

SEARCH_FIELDS = (
    "title,authors,year,externalIds,abstract,venue,"
    "isOpenAccess,openAccessPdf,tldr,citationCount"
)


def format_paper(paper: dict, compact: bool = False) -> str:
    """Format a Semantic Scholar paper into human-readable text with source attribution."""
    title = paper.get("title") or "No title"
    authors = ", ".join(a.get("name", "Unknown") for a in paper.get("authors", []))
    year = paper.get("year") or "Year unknown"
    ext_ids = paper.get("externalIds") or {}
    doi = ext_ids.get("DOI", "Not available")
    venue = paper.get("venue") or "Not available"
    citations = paper.get("citationCount", "Unknown")
    is_open = "Yes" if paper.get("isOpenAccess") else "No"
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
    ]
    if compact:
        if tldr:
            lines.append(f"  TL;DR: {tldr}")
    else:
        pdf_data = paper.get("openAccessPdf") or {}
        pdf_url = pdf_data.get("url", "Not available")
        abstract = paper.get("abstract") or "Not available"
        lines.append(f"  PDF: {pdf_url}")
        lines.append(f"  Abstract: {abstract}")
        if tldr:
            lines.append(f"  TL;DR: {tldr}")
    lines.append("  [Source: Semantic Scholar]")
    return "\n".join(lines)


def _get_headers():
    """Build request headers, including API key if available."""
    api_key = os.environ.get("SEMANTIC_SCHOLAR_API_KEY")
    if api_key:
        return {"x-api-key": api_key}
    return None


async def _call_api(url, params):
    """Call make_request, translate HTTP errors to custom exceptions."""
    try:
        return await make_request(url, params=params, headers=_get_headers())
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 429:
            raise RateLimited("Semantic Scholar")
        raise SourceUnavailable("Semantic Scholar", f"HTTP {e.response.status_code}")


async def search(query: str, limit: int = 10, compact: bool = False) -> str:
    """Search Semantic Scholar for papers matching query."""
    if not query.strip():
        raise SourceUnavailable("Semantic Scholar", "empty query")

    truncated = len(query) > 300
    q = query[:300] if truncated else query

    data = await _call_api(
        f"{BASE_URL}/paper/search",
        params={"query": q, "limit": limit, "fields": SEARCH_FIELDS},
    )

    if not data or "data" not in data or not data["data"]:
        raise SourceUnavailable("Semantic Scholar", "no results")

    results = []
    if truncated:
        results.append("Note: Query was truncated to 300 characters.")
    for paper in data["data"]:
        results.append(format_paper(paper, compact=compact))

    return "\n\n".join(results)


async def get_paper_details(paper_id: str) -> str:
    """Fetch detailed metadata for a specific paper."""
    data = await _call_api(
        f"{BASE_URL}/paper/{paper_id}",
        params={"fields": SEARCH_FIELDS},
    )

    if not data:
        raise SourceUnavailable("Semantic Scholar", f"no data for '{paper_id}'")

    return format_paper(data)


CITATION_FIELDS = "title,authors,year,externalIds,venue,contexts"


async def get_citation_context(paper_id: str, limit: int = 10) -> str:
    """Fetch citing papers and the sentences where they cite this paper."""
    data = await _call_api(
        f"{BASE_URL}/paper/{paper_id}/citations",
        params={"fields": CITATION_FIELDS, "limit": limit},
    )

    if not data or "data" not in data or not data["data"]:
        raise SourceUnavailable("Semantic Scholar", f"no citations for '{paper_id}'")

    citations_with_context = []
    citations_without_context = 0

    for entry in data["data"]:
        citing = entry.get("citingPaper", {})
        contexts = entry.get("contexts") or []

        if not contexts:
            citations_without_context += 1
            continue

        title = citing.get("title") or "No title"
        authors = ", ".join(a.get("name", "Unknown") for a in citing.get("authors", []))
        year = citing.get("year") or "Year unknown"
        ext_ids = citing.get("externalIds") or {}
        doi = ext_ids.get("DOI", "Not available")
        venue = citing.get("venue") or ""

        lines = [f"**{title}**"]
        lines.append(f"  {authors} ({year}){f' — {venue}' if venue else ''}")
        lines.append(f"  DOI: {doi}")
        for ctx in contexts:
            lines.append(f"  > \"{ctx}\"")

        citations_with_context.append("\n".join(lines))

    if not citations_with_context:
        raise SourceUnavailable(
            "Semantic Scholar",
            f"found {citations_without_context} citing paper(s) but none with context sentences"
        )

    result_lines = [f"Found {len(citations_with_context)} citing paper(s) with context sentences."]
    if citations_without_context:
        result_lines.append(
            f"({citations_without_context} additional citing paper(s) without context sentences.)"
        )
    result_lines.append("")
    result_lines.append("\n\n".join(citations_with_context))
    result_lines.append("\n[Source: Semantic Scholar citation contexts]")

    return "\n".join(result_lines)


async def search_by_topic(
    topic: str, year_start: int | None = None, year_end: int | None = None, limit: int = 10, compact: bool = False
) -> str:
    """Search by topic with optional year filtering."""
    if not topic.strip():
        raise SourceUnavailable("Semantic Scholar", "empty topic")

    truncated = len(topic) > 300
    q = topic[:300] if truncated else topic

    params = {"query": q, "limit": limit, "fields": SEARCH_FIELDS}
    if year_start is not None and year_end is not None:
        params["year"] = f"{year_start}-{year_end}"
    elif year_start is not None:
        params["year"] = f"{year_start}-"
    elif year_end is not None:
        params["year"] = f"-{year_end}"

    data = await _call_api(f"{BASE_URL}/paper/search", params=params)

    if not data or "data" not in data or not data["data"]:
        raise SourceUnavailable("Semantic Scholar", "no results for this topic")

    results = []
    if truncated:
        results.append("Note: Query was truncated to 300 characters.")
    for paper in data["data"]:
        results.append(format_paper(paper, compact=compact))

    return "\n\n".join(results)
