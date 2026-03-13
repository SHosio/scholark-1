"""OpenAlex API client for Scholark-1."""

import os
import httpx
from apis import make_request
from apis.errors import SourceUnavailable, RateLimited

BASE_URL = "https://api.openalex.org/works"

_EMAIL = os.environ.get("OPENALEX_EMAIL", "")


def _reconstruct_abstract(inverted_index: dict | None) -> str:
    """Reconstruct abstract from OpenAlex inverted index format."""
    if not inverted_index:
        return "Not available"
    word_positions = []
    for word, positions in inverted_index.items():
        for pos in positions:
            word_positions.append((pos, word))
    word_positions.sort()
    return " ".join(word for _, word in word_positions)


def format_paper(work: dict) -> str:
    """Format an OpenAlex work into human-readable text with source attribution."""
    title = work.get("title") or "No title"
    authorships = work.get("authorships") or []
    authors = ", ".join(
        a.get("author", {}).get("display_name", "Unknown") for a in authorships
    )
    year = work.get("publication_year") or "Year unknown"
    raw_doi = work.get("doi") or ""
    doi = raw_doi.replace("https://doi.org/", "") if raw_doi else "Not available"
    location = work.get("primary_location") or {}
    source = location.get("source") or {}
    venue = source.get("display_name") or "Not available"
    citations = work.get("cited_by_count", "Unknown")
    oa = work.get("open_access") or {}
    is_open = "Yes" if oa.get("is_oa") else "No"
    abstract = _reconstruct_abstract(work.get("abstract_inverted_index"))

    lines = [
        f"**{title}**",
        f"  Authors: {authors or 'Not available'}",
        f"  Year: {year}",
        f"  DOI: {doi}",
        f"  Venue: {venue}",
        f"  Citations: {citations}",
        f"  Open Access: {is_open}",
        f"  Abstract: {abstract}",
        "  [Source: OpenAlex]",
    ]
    return "\n".join(lines)


async def _call_api(url, params=None):
    """Call make_request, translate HTTP errors to custom exceptions."""
    if _EMAIL:
        if params is None:
            params = {}
        params["mailto"] = _EMAIL
    try:
        return await make_request(url, params=params)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 429:
            raise RateLimited("OpenAlex")
        raise SourceUnavailable("OpenAlex", f"HTTP {e.response.status_code}")


async def search(query: str, limit: int = 10) -> str:
    """Search OpenAlex for papers matching query."""
    if not query.strip():
        raise SourceUnavailable("OpenAlex", "empty query")

    data = await _call_api(
        BASE_URL,
        params={"search": query, "per_page": limit},
    )

    if not data or not data.get("results"):
        raise SourceUnavailable("OpenAlex", "no results")

    results = [format_paper(work) for work in data["results"]]
    return "\n\n".join(results)


async def get_paper_details(doi: str) -> str:
    """Fetch detailed metadata for a paper by DOI from OpenAlex."""
    data = await _call_api(f"{BASE_URL}/doi:{doi}")

    if not data:
        raise SourceUnavailable("OpenAlex", f"no data for DOI '{doi}'")

    return format_paper(data)


async def search_by_topic(
    topic: str,
    year_start: int | None = None,
    year_end: int | None = None,
    limit: int = 10,
) -> str:
    """Search by topic with optional year filtering."""
    if not topic.strip():
        raise SourceUnavailable("OpenAlex", "empty topic")

    params = {"search": topic, "per_page": limit}

    if year_start is not None and year_end is not None:
        params["filter"] = f"publication_year:{year_start}-{year_end}"
    elif year_start is not None:
        params["filter"] = f"publication_year:{year_start}-"
    elif year_end is not None:
        params["filter"] = f"publication_year:-{year_end}"

    data = await _call_api(BASE_URL, params=params)

    if not data or not data.get("results"):
        raise SourceUnavailable("OpenAlex", "no results for this topic")

    results = [format_paper(work) for work in data["results"]]
    return "\n\n".join(results)
