"""Crossref API client for Scholark-1."""

import re
import httpx
from apis import make_request, make_request_text
from apis.errors import SourceUnavailable, RateLimited

BASE_URL = "https://api.crossref.org/works"


def format_paper(item: dict, compact: bool = False) -> str:
    """Format a Crossref work item into human-readable text."""
    title_list = item.get("title") or ["Not available"]
    title = title_list[0] if title_list else "Not available"
    authors = ", ".join(
        f"{a.get('given', '')} {a.get('family', '')}".strip() or "Unknown"
        for a in item.get("author", [])
    )
    date_parts = item.get("published-print", {}).get("date-parts", [[]])
    if not date_parts or not date_parts[0]:
        date_parts = item.get("published-online", {}).get("date-parts", [[]])
    year = date_parts[0][0] if date_parts and date_parts[0] else "Year unknown"
    doi = item.get("DOI", "Not available")
    venue_list = item.get("container-title") or []
    venue = venue_list[0] if venue_list else "Not available"
    citations = item.get("is-referenced-by-count", "Unknown")

    lines = [
        f"**{title}**",
        f"  Authors: {authors or 'Not available'}",
        f"  Year: {year}",
        f"  DOI: {doi}",
        f"  Venue: {venue}",
        f"  Citations: {citations}",
    ]
    if not compact:
        abstract = item.get("abstract", "Not available")
        if abstract != "Not available":
            abstract = re.sub(r"<[^>]+>", "", abstract).strip()
        lines.append(f"  Abstract: {abstract}")
    lines.append("  [Source: Crossref]")
    return "\n".join(lines)


def normalize_doi(doi_input: str) -> str:
    """Extract bare DOI from various formats: URL, doi: prefix, bare."""
    doi = doi_input.strip()
    doi = re.sub(r"^https?://doi\.org/", "", doi)
    doi = re.sub(r"^doi:\s*", "", doi, flags=re.IGNORECASE)
    return doi


async def _call_api(url, params=None):
    """Call make_request, translate HTTP errors to custom exceptions."""
    try:
        return await make_request(url, params=params)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 429:
            raise RateLimited("Crossref")
        raise SourceUnavailable("Crossref", f"HTTP {e.response.status_code}")


async def search(query: str, limit: int = 10, compact: bool = False) -> str:
    """Search Crossref for papers."""
    if not query.strip():
        raise SourceUnavailable("Crossref", "empty query")

    data = await _call_api(BASE_URL, params={"query": query, "rows": limit})

    if not data or "items" not in data.get("message", {}):
        raise SourceUnavailable("Crossref", "no results or unavailable")

    items = data["message"]["items"]
    if not items:
        raise SourceUnavailable("Crossref", "no results")

    results = [format_paper(item, compact=compact) for item in items]
    return "\n\n".join(results)


async def get_paper_details(doi: str) -> str:
    """Fetch detailed metadata for a paper by DOI from Crossref."""
    data = await _call_api(f"{BASE_URL}/{doi}")

    if not data or "message" not in data:
        raise SourceUnavailable("Crossref", f"no data for DOI '{doi}'")

    return format_paper(data["message"])


async def get_bibtex(doi_input: str) -> str:
    """Fetch BibTeX for a DOI via content negotiation with doi.org."""
    doi = normalize_doi(doi_input)
    if not doi:
        raise SourceUnavailable("Crossref", "empty DOI")

    url = f"https://doi.org/{doi}"
    try:
        bibtex = await make_request_text(url, accept="application/x-bibtex")
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 429:
            raise RateLimited("Crossref")
        raise SourceUnavailable("Crossref", f"HTTP {e.response.status_code}")

    if not bibtex:
        raise SourceUnavailable("Crossref", f"no BibTeX for DOI '{doi}'")

    return f"{bibtex.strip()}\n\n[Source: DOI content negotiation via doi.org]"
