"""Europe PMC API client for Scholark-1.

Uses Europe PMC (europepmc.org) which indexes PubMed, PMC, and preprints.
Returns JSON with full metadata including abstracts. No API key required.
"""

import httpx
from apis import make_request
from apis.errors import SourceUnavailable, RateLimited

BASE_URL = "https://www.ebi.ac.uk/europepmc/webservices/rest"


def format_paper(paper: dict, compact: bool = False) -> str:
    """Format a Europe PMC paper into human-readable text with source attribution."""
    title = paper.get("title") or "No title"
    authors = paper.get("authorString") or "Not available"
    year = paper.get("pubYear") or "Year unknown"
    doi = paper.get("doi") or "Not available"
    pmid = paper.get("pmid") or "Not available"
    pmcid = paper.get("pmcid") or "Not available"
    venue = paper.get("journalTitle") or "Not available"
    citations = paper.get("citedByCount", "Unknown")
    is_open = "Yes" if paper.get("isOpenAccess") == "Y" else "No"

    lines = [
        f"**{title}**",
        f"  Authors: {authors}",
        f"  Year: {year}",
        f"  DOI: {doi}",
        f"  PMID: {pmid}",
        f"  PMCID: {pmcid}",
        f"  Venue: {venue}",
        f"  Citations: {citations}",
        f"  Open Access: {is_open}",
    ]
    if not compact:
        abstract = paper.get("abstractText") or "Not available"
        lines.append(f"  Abstract: {abstract}")
    lines.append("  [Source: Europe PMC]")
    return "\n".join(lines)


async def _call_api(url, params):
    """Call make_request, translate HTTP errors to custom exceptions."""
    try:
        return await make_request(url, params=params)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 429:
            raise RateLimited("Europe PMC")
        raise SourceUnavailable("Europe PMC", f"HTTP {e.response.status_code}")


async def search(query: str, limit: int = 10, compact: bool = False) -> str:
    """Search Europe PMC for papers matching query."""
    if not query.strip():
        raise SourceUnavailable("Europe PMC", "empty query")

    params = {
        "query": query,
        "format": "json",
        "pageSize": min(limit, 25),
        "resultType": "core",
    }
    data = await _call_api(f"{BASE_URL}/search", params)

    if not data or "resultList" not in data:
        raise SourceUnavailable("Europe PMC", "no results")

    results = data["resultList"].get("result", [])
    if not results:
        raise SourceUnavailable("Europe PMC", "no results")

    return "\n\n".join(format_paper(p, compact=compact) for p in results)


async def get_paper_details(paper_id: str) -> str:
    """Fetch paper details by DOI from Europe PMC."""
    params = {
        "query": f'DOI:"{paper_id}"',
        "format": "json",
        "pageSize": 1,
        "resultType": "core",
    }
    data = await _call_api(f"{BASE_URL}/search", params)

    if not data or "resultList" not in data:
        raise SourceUnavailable("Europe PMC", f"no data for '{paper_id}'")

    results = data["resultList"].get("result", [])
    if not results:
        raise SourceUnavailable("Europe PMC", f"no data for '{paper_id}'")

    return format_paper(results[0])


async def search_by_topic(
    topic: str, year_start: int | None = None, year_end: int | None = None, limit: int = 10, compact: bool = False
) -> str:
    """Search by topic with optional year filtering."""
    if not topic.strip():
        raise SourceUnavailable("Europe PMC", "empty topic")

    query = topic
    if year_start or year_end:
        start = year_start or 1900
        end = year_end or 2099
        query = f"({topic}) AND (FIRST_PDATE:[{start}-01-01 TO {end}-12-31])"

    params = {
        "query": query,
        "format": "json",
        "pageSize": min(limit, 25),
        "resultType": "core",
    }
    data = await _call_api(f"{BASE_URL}/search", params)

    if not data or "resultList" not in data:
        raise SourceUnavailable("Europe PMC", "no results for this topic")

    results = data["resultList"].get("result", [])
    if not results:
        raise SourceUnavailable("Europe PMC", "no results for this topic")

    return "\n\n".join(format_paper(p, compact=compact) for p in results)
