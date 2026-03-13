import pytest
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
async def test_search_papers_combines_sources():
    """search_papers should try Semantic Scholar first, then Crossref as fallback."""
    with patch("apis.semantic_scholar.search", new_callable=AsyncMock) as ss_mock, \
         patch("apis.crossref.search", new_callable=AsyncMock) as cr_mock:
        ss_mock.return_value = "**Paper A**\n  [Source: Semantic Scholar]"
        cr_mock.return_value = "**Paper B**\n  [Source: Crossref]"

        from server import search_papers
        result = await search_papers("test query", limit=5)
        assert "Semantic Scholar" in result
        assert "Crossref" in result


@pytest.mark.asyncio
async def test_search_papers_fallback_on_ss_failure():
    """If Semantic Scholar fails, Crossref results still show."""
    with patch("apis.semantic_scholar.search", new_callable=AsyncMock) as ss_mock, \
         patch("apis.crossref.search", new_callable=AsyncMock) as cr_mock:
        ss_mock.return_value = "Semantic Scholar returned no results or was unavailable."
        cr_mock.return_value = "**Paper B**\n  [Source: Crossref]"

        from server import search_papers
        result = await search_papers("test query")
        assert "Crossref" in result


@pytest.mark.asyncio
async def test_doi_to_bibtex():
    with patch("apis.crossref.get_bibtex", new_callable=AsyncMock) as mock:
        mock.return_value = "@article{Test}\n\n[Source: DOI content negotiation via doi.org]"
        from server import doi_to_bibtex
        result = await doi_to_bibtex("10.1234/test")
        assert "@article" in result


@pytest.mark.asyncio
async def test_fetch_paper_details_fallback():
    """If Semantic Scholar fails for a DOI, try Crossref."""
    with patch("apis.semantic_scholar.get_paper_details", new_callable=AsyncMock) as ss_mock, \
         patch("apis.crossref.get_paper_details", new_callable=AsyncMock) as cr_mock:
        ss_mock.return_value = "Could not fetch paper details for '10.1234/test' from Semantic Scholar."
        cr_mock.return_value = "**Test Paper**\n  [Source: Crossref]"

        from server import fetch_paper_details
        result = await fetch_paper_details("10.1234/test")
        assert "Crossref" in result


@pytest.mark.asyncio
async def test_fetch_paper_details_no_crossref_for_non_doi():
    """Non-DOI identifiers should not attempt Crossref fallback."""
    with patch("apis.semantic_scholar.get_paper_details", new_callable=AsyncMock) as ss_mock:
        ss_mock.return_value = "Could not fetch paper details for 'abc123' from Semantic Scholar."

        from server import fetch_paper_details
        result = await fetch_paper_details("abc123")
        assert "doesn't look like a DOI" in result


@pytest.mark.asyncio
async def test_search_by_topic_with_fallback():
    """search_by_topic falls back to Crossref when SS has no results."""
    with patch("apis.semantic_scholar.search_by_topic", new_callable=AsyncMock) as ss_mock, \
         patch("apis.crossref.search", new_callable=AsyncMock) as cr_mock:
        ss_mock.return_value = "Semantic Scholar returned no results for this topic."
        cr_mock.return_value = "**Paper C**\n  [Source: Crossref]"

        from server import search_by_topic
        result = await search_by_topic("HCI design", year_start=2020)
        assert "Crossref" in result
        assert "year filtering is not applied" in result
