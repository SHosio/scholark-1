"""Shared HTTP utilities for Scholark-1 API clients."""

import os

import httpx
from typing import Any

USER_AGENT = "scholark-1/1.0 (academic-research-mcp)"


def contact_email(service_env: str) -> str:
    """Resolve the contact email for a service's polite pool.

    The service-specific variable (e.g. OPENALEX_EMAIL, CROSSREF_MAILTO,
    UNPAYWALL_EMAIL) wins; SCHOLARK_CONTACT_EMAIL is the shared fallback so
    users can set one email once. Read at call time, not import time, so
    .env loading order and tests behave predictably.
    """
    return os.environ.get(service_env) or os.environ.get("SCHOLARK_CONTACT_EMAIL", "")


async def make_request(
    url: str,
    headers: dict | None = None,
    params: dict | None = None,
    accept: str = "application/json",
) -> dict[str, Any] | None:
    """Make an HTTP GET request with error handling.

    Returns parsed JSON on success, None on connection/timeout failures.
    Raises httpx.HTTPStatusError on HTTP error responses (4xx, 5xx)
    so callers can inspect status codes.
    """
    default_headers = {"User-Agent": USER_AGENT, "Accept": accept}
    if headers:
        default_headers.update(headers)

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                url, headers=default_headers, params=params, timeout=30.0
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError:
            raise
        except (httpx.HTTPError, ValueError):
            return None


async def make_request_text(
    url: str,
    headers: dict | None = None,
    params: dict | None = None,
    accept: str = "text/plain",
) -> str | None:
    """Make an HTTP GET request, return raw text. Used for BibTeX content negotiation.

    Raises httpx.HTTPStatusError on HTTP error responses (4xx, 5xx).
    Returns None on connection/timeout failures.
    """
    default_headers = {"User-Agent": USER_AGENT, "Accept": accept}
    if headers:
        default_headers.update(headers)

    async with httpx.AsyncClient(follow_redirects=True) as client:
        try:
            response = await client.get(
                url, headers=default_headers, params=params, timeout=30.0
            )
            response.raise_for_status()
            return response.text
        except httpx.HTTPStatusError:
            raise
        except (httpx.HTTPError, ValueError):
            return None
