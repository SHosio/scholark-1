"""Unpaywall API client for Scholark-1.

Uses the Unpaywall API (unpaywall.org) to find open access versions of papers by DOI.
Free to use, requires an email address. No API key needed.
"""

import os
import httpx
from apis import make_request
from apis.errors import SourceUnavailable

BASE_URL = "https://api.unpaywall.org/v2"


def _get_email() -> str:
    """Get email for Unpaywall API. Required for all requests."""
    email = os.environ.get("UNPAYWALL_EMAIL", "")
    if not email:
        raise SourceUnavailable("Unpaywall", "no email configured (set UNPAYWALL_EMAIL)")
    return email


def _format_oa_location(loc: dict) -> str:
    """Format a single OA location."""
    url = loc.get("url") or "Not available"
    pdf_url = loc.get("url_for_pdf") or "Not available"
    host = loc.get("host_type") or "Unknown"
    version = loc.get("version") or "Unknown"
    license_info = loc.get("license") or "Not specified"
    return (
        f"  - Host: {host} | Version: {version} | License: {license_info}\n"
        f"    URL: {url}\n"
        f"    PDF: {pdf_url}"
    )


def format_result(data: dict) -> str:
    """Format Unpaywall response into human-readable text."""
    title = data.get("title") or "No title"
    doi = data.get("doi") or "Not available"
    is_oa = data.get("is_oa", False)
    oa_status = data.get("oa_status") or "unknown"
    journal = data.get("journal_name") or "Not available"
    publisher = data.get("publisher") or "Not available"
    year = data.get("year") or "Year unknown"

    lines = [
        f"**{title}**",
        f"  DOI: {doi}",
        f"  Year: {year}",
        f"  Journal: {journal}",
        f"  Publisher: {publisher}",
        f"  Open Access: {'Yes' if is_oa else 'No'} ({oa_status})",
    ]

    if is_oa:
        best = data.get("best_oa_location")
        if best:
            lines.append(f"  Best OA Location:")
            lines.append(_format_oa_location(best))

        all_locations = data.get("oa_locations") or []
        if len(all_locations) > 1:
            lines.append(f"  All OA Locations ({len(all_locations)}):")
            for loc in all_locations:
                lines.append(_format_oa_location(loc))
    else:
        lines.append("  No open access version found.")

    lines.append("  [Source: Unpaywall]")
    return "\n".join(lines)


async def find_open_access(doi: str) -> str:
    """Look up open access availability for a DOI."""
    if not doi.strip():
        raise SourceUnavailable("Unpaywall", "empty DOI")

    email = _get_email()

    try:
        data = await make_request(
            f"{BASE_URL}/{doi}",
            params={"email": email},
        )
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise SourceUnavailable("Unpaywall", f"DOI '{doi}' not found")
        if e.response.status_code == 422:
            raise SourceUnavailable("Unpaywall", f"invalid DOI format: '{doi}'")
        raise SourceUnavailable("Unpaywall", f"HTTP {e.response.status_code}")

    if not data:
        raise SourceUnavailable("Unpaywall", f"no data for '{doi}'")

    return format_result(data)
