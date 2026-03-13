"""Crossref API client for Scholark-1."""

import re
from apis import make_request, make_request_text

BASE_URL = "https://api.crossref.org/works"


def format_paper(item: dict) -> str:
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
    abstract = item.get("abstract", "Not available")
    if abstract != "Not available":
        abstract = re.sub(r"<[^>]+>", "", abstract).strip()
    citations = item.get("is-referenced-by-count", "Unknown")

    lines = [
        f"**{title}**",
        f"  Authors: {authors or 'Not available'}",
        f"  Year: {year}",
        f"  DOI: {doi}",
        f"  Venue: {venue}",
        f"  Citations: {citations}",
        f"  Abstract: {abstract}",
        "  [Source: Crossref]",
    ]
    return "\n".join(lines)


async def search(query: str, limit: int = 10) -> str:
    """Search Crossref for papers."""
    if not query.strip():
        return "Please provide a search query."

    data = await make_request(
        BASE_URL,
        params={"query": query, "rows": limit},
    )

    if not data or "items" not in data.get("message", {}):
        return "Crossref returned no results or was unavailable."

    items = data["message"]["items"]
    if not items:
        return "Crossref returned no results for this query."

    results = [format_paper(item) for item in items]
    return "\n\n".join(results)


async def get_paper_details(doi: str) -> str:
    """Fetch detailed metadata for a paper by DOI from Crossref."""
    data = await make_request(f"{BASE_URL}/{doi}")

    if not data or "message" not in data:
        return f"Could not fetch details for DOI '{doi}' from Crossref."

    return format_paper(data["message"])


def _normalize_doi(doi_input: str) -> str:
    """Extract bare DOI from various formats: URL, doi: prefix, bare."""
    doi = doi_input.strip()
    doi = re.sub(r"^https?://doi\.org/", "", doi)
    doi = re.sub(r"^doi:\s*", "", doi, flags=re.IGNORECASE)
    return doi


async def get_bibtex(doi_input: str) -> str:
    """Fetch BibTeX for a DOI via content negotiation with doi.org."""
    doi = _normalize_doi(doi_input)
    if not doi:
        return "Please provide a DOI."

    url = f"https://doi.org/{doi}"
    bibtex = await make_request_text(
        url, accept="application/x-bibtex"
    )

    if not bibtex:
        return f"Could not retrieve BibTeX for DOI '{doi}'. The DOI may be invalid or the service may be temporarily unavailable."

    return f"{bibtex.strip()}\n\n[Source: DOI content negotiation via doi.org]"
