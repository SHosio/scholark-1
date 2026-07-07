import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from apis.errors import SourceUnavailable, RateLimited


@pytest.mark.asyncio
async def test_search_papers_combines_sources():
    """search_papers shows results from all four sources."""
    with patch("apis.semantic_scholar.search", new_callable=AsyncMock) as ss, \
         patch("apis.openalex.search", new_callable=AsyncMock) as oa, \
         patch("apis.crossref.search", new_callable=AsyncMock) as cr, \
         patch("apis.pubmed.search", new_callable=AsyncMock) as pm:
        ss.return_value = "**Paper A**\n  DOI: 10.1000/ss\n  [Source: Semantic Scholar]"
        oa.return_value = "**Paper B**\n  DOI: 10.1000/oa\n  [Source: OpenAlex]"
        cr.return_value = "**Paper C**\n  DOI: 10.1000/cr\n  [Source: Crossref]"
        pm.return_value = "**Paper D**\n  DOI: 10.1000/pm\n  [Source: Europe PMC]"

        from server import search_papers
        result = await search_papers("test query", limit=5)
        assert "Semantic Scholar" in result
        assert "OpenAlex" in result
        assert "Crossref" in result
        assert "Europe PMC" in result


@pytest.mark.asyncio
async def test_search_papers_handles_source_failure():
    """If one source fails, others still show."""
    with patch("apis.semantic_scholar.search", new_callable=AsyncMock) as ss, \
         patch("apis.openalex.search", new_callable=AsyncMock) as oa, \
         patch("apis.crossref.search", new_callable=AsyncMock) as cr, \
         patch("apis.pubmed.search", new_callable=AsyncMock) as pm:
        ss.side_effect = RateLimited("Semantic Scholar")
        oa.return_value = "**Paper B**\n  DOI: 10.1000/oa\n  [Source: OpenAlex]"
        cr.return_value = "**Paper C**\n  DOI: 10.1000/cr\n  [Source: Crossref]"
        pm.return_value = "**Paper D**\n  DOI: 10.1000/pm\n  [Source: Europe PMC]"

        from server import search_papers
        result = await search_papers("test query")
        assert "rate limit exceeded" in result
        assert "OpenAlex" in result
        assert "Crossref" in result


@pytest.mark.asyncio
async def test_search_papers_deduplicates():
    """Duplicate DOIs across sources are removed."""
    with patch("apis.semantic_scholar.search", new_callable=AsyncMock) as ss, \
         patch("apis.openalex.search", new_callable=AsyncMock) as oa, \
         patch("apis.crossref.search", new_callable=AsyncMock) as cr, \
         patch("apis.pubmed.search", new_callable=AsyncMock) as pm:
        ss.return_value = "**Paper A**\n  DOI: 10.1000/same\n  [Source: Semantic Scholar]"
        oa.return_value = "**Paper A copy**\n  DOI: 10.1000/same\n  [Source: OpenAlex]"
        cr.return_value = "**Paper B**\n  DOI: 10.1000/different\n  [Source: Crossref]"
        pm.side_effect = SourceUnavailable("Europe PMC", "no results")

        from server import search_papers
        result = await search_papers("test query")
        assert "duplicate" in result.lower()
        assert "Paper A copy" not in result


@pytest.mark.asyncio
async def test_fetch_paper_details_fallback_chain():
    """SS fails for a DOI → try OpenAlex → try Crossref."""
    with patch("apis.semantic_scholar.get_paper_details", new_callable=AsyncMock) as ss, \
         patch("apis.openalex.get_paper_details", new_callable=AsyncMock) as oa, \
         patch("apis.crossref.get_paper_details", new_callable=AsyncMock) as cr, \
         patch("apis.openalex.is_retracted", new_callable=AsyncMock) as retr, \
         patch("server._get_cache") as get_cache_mock:
        get_cache_mock.return_value.get.return_value = None
        ss.side_effect = SourceUnavailable("Semantic Scholar", "no data")
        oa.side_effect = SourceUnavailable("OpenAlex", "no data")
        cr.return_value = "**Test Paper**\n  [Source: Crossref]"
        retr.return_value = False

        from server import fetch_paper_details
        result = await fetch_paper_details("10.1234/test")
        assert "Crossref" in result


@pytest.mark.asyncio
async def test_fetch_paper_details_flags_retracted_doi():
    """A retracted DOI gets a prominent retraction alert regardless of source."""
    with patch("apis.semantic_scholar.get_paper_details", new_callable=AsyncMock) as ss, \
         patch("apis.openalex.is_retracted", new_callable=AsyncMock) as retr, \
         patch("server._get_cache") as get_cache_mock:
        get_cache_mock.return_value.get.return_value = None
        ss.return_value = "**Test Paper**\n  [Source: Semantic Scholar]"
        retr.return_value = True

        from server import fetch_paper_details
        result = await fetch_paper_details("10.1234/test")
        assert "RETRACT" in result.upper()


@pytest.mark.asyncio
async def test_fetch_paper_details_reports_clean_retraction_check():
    """A non-retracted DOI notes that the retraction check came back clean."""
    with patch("apis.semantic_scholar.get_paper_details", new_callable=AsyncMock) as ss, \
         patch("apis.openalex.is_retracted", new_callable=AsyncMock) as retr, \
         patch("server._get_cache") as get_cache_mock:
        get_cache_mock.return_value.get.return_value = None
        ss.return_value = "**Test Paper**\n  [Source: Semantic Scholar]"
        retr.return_value = False

        from server import fetch_paper_details
        result = await fetch_paper_details("10.1234/test")
        assert "no retraction record" in result


@pytest.mark.asyncio
async def test_fetch_paper_details_retraction_check_unavailable():
    """If OpenAlex can't be reached, the retraction status is reported as unverified."""
    with patch("apis.semantic_scholar.get_paper_details", new_callable=AsyncMock) as ss, \
         patch("apis.openalex.is_retracted", new_callable=AsyncMock) as retr, \
         patch("server._get_cache") as get_cache_mock:
        get_cache_mock.return_value.get.return_value = None
        ss.return_value = "**Test Paper**\n  [Source: Semantic Scholar]"
        retr.return_value = None

        from server import fetch_paper_details
        result = await fetch_paper_details("10.1234/test")
        assert "could not verify" in result.lower()


@pytest.mark.asyncio
async def test_fetch_paper_details_no_fallback_for_non_doi():
    """Non-DOI identifiers skip OpenAlex/Crossref fallback."""
    with patch("apis.semantic_scholar.get_paper_details", new_callable=AsyncMock) as ss, \
         patch("server._get_cache") as get_cache_mock:
        get_cache_mock.return_value.get.return_value = None
        ss.side_effect = SourceUnavailable("Semantic Scholar", "no data")

        from server import fetch_paper_details
        result = await fetch_paper_details("abc123")
        assert "doesn't look like a DOI" in result


@pytest.mark.asyncio
async def test_fetch_paper_details_cache_hit():
    """Cache hit returns cached metadata but still runs a fresh retraction check."""
    with patch("server._get_cache") as get_cache_mock, \
         patch("apis.openalex.is_retracted", new_callable=AsyncMock) as retr:
        get_cache_mock.return_value.get.return_value = "**Cached Paper**\n  [Source: Semantic Scholar]"
        retr.return_value = True

        from server import fetch_paper_details
        result = await fetch_paper_details("10.1234/test")
        assert "Cached Paper" in result
        assert "RETRACT" in result.upper()


@pytest.mark.asyncio
async def test_doi_to_bibtex_with_cache():
    """doi_to_bibtex checks cache, stores result on miss."""
    with patch("apis.crossref.get_bibtex", new_callable=AsyncMock) as mock, \
         patch("server._get_cache") as get_cache_mock:
        get_cache_mock.return_value.get.return_value = None
        mock.return_value = "@article{Test}\n\n[Source: DOI content negotiation via doi.org]"

        from server import doi_to_bibtex
        result = await doi_to_bibtex("10.1234/test")
        assert "@article" in result
        get_cache_mock.return_value.put.assert_called_once()


@pytest.mark.asyncio
async def test_search_by_topic_combines_sources():
    """search_by_topic queries all year-capable sources in parallel."""
    with patch("apis.semantic_scholar.search_by_topic", new_callable=AsyncMock) as ss, \
         patch("apis.openalex.search_by_topic", new_callable=AsyncMock) as oa, \
         patch("apis.pubmed.search_by_topic", new_callable=AsyncMock) as pm:
        ss.return_value = "**Paper A**\n  DOI: 10.1000/ss\n  [Source: Semantic Scholar]"
        oa.return_value = "**Paper B**\n  DOI: 10.1000/oa\n  [Source: OpenAlex]"
        pm.return_value = "**Paper C**\n  DOI: 10.1000/pm\n  [Source: Europe PMC]"

        from server import search_by_topic
        result = await search_by_topic("HCI design", year_start=2020)
        assert "Paper A" in result
        assert "Paper B" in result
        assert "Paper C" in result


@pytest.mark.asyncio
async def test_search_by_topic_handles_source_failure():
    """If one topic source fails, the others still show."""
    with patch("apis.semantic_scholar.search_by_topic", new_callable=AsyncMock) as ss, \
         patch("apis.openalex.search_by_topic", new_callable=AsyncMock) as oa, \
         patch("apis.pubmed.search_by_topic", new_callable=AsyncMock) as pm:
        ss.side_effect = RateLimited("Semantic Scholar")
        oa.return_value = "**Paper B**\n  DOI: 10.1000/oa\n  [Source: OpenAlex]"
        pm.return_value = "**Paper C**\n  DOI: 10.1000/pm\n  [Source: Europe PMC]"

        from server import search_by_topic
        result = await search_by_topic("HCI design", year_start=2020)
        assert "OpenAlex" in result
        assert "Europe PMC" in result


@pytest.mark.asyncio
async def test_search_by_topic_deduplicates():
    """Duplicate DOIs across topic sources are removed."""
    with patch("apis.semantic_scholar.search_by_topic", new_callable=AsyncMock) as ss, \
         patch("apis.openalex.search_by_topic", new_callable=AsyncMock) as oa, \
         patch("apis.pubmed.search_by_topic", new_callable=AsyncMock) as pm:
        ss.return_value = "**Paper A**\n  DOI: 10.1000/same\n  [Source: Semantic Scholar]"
        oa.return_value = "**Paper A copy**\n  DOI: 10.1000/same\n  [Source: OpenAlex]"
        pm.side_effect = SourceUnavailable("Europe PMC", "no results")

        from server import search_by_topic
        result = await search_by_topic("HCI design")
        assert "duplicate" in result.lower()
        assert "Paper A copy" not in result


@pytest.mark.asyncio
async def test_search_by_topic_crossref_fallback_notes_year_filter():
    """Crossref fallback in search_by_topic warns about missing year filter."""
    with patch("apis.semantic_scholar.search_by_topic", new_callable=AsyncMock) as ss, \
         patch("apis.openalex.search_by_topic", new_callable=AsyncMock) as oa, \
         patch("apis.pubmed.search_by_topic", new_callable=AsyncMock) as pm, \
         patch("apis.crossref.search", new_callable=AsyncMock) as cr:
        ss.side_effect = SourceUnavailable("SS", "no results")
        oa.side_effect = SourceUnavailable("OpenAlex", "no results")
        pm.side_effect = SourceUnavailable("Europe PMC", "no results")
        cr.return_value = "**Paper C**\n  [Source: Crossref]"

        from server import search_by_topic
        result = await search_by_topic("HCI", year_start=2020)
        assert "year filtering not applied" in result


@pytest.mark.asyncio
async def test_find_open_access():
    """find_open_access returns Unpaywall data."""
    with patch("apis.unpaywall.find_open_access", new_callable=AsyncMock) as mock, \
         patch("server._get_cache") as get_cache_mock:
        get_cache_mock.return_value.get.return_value = None
        mock.return_value = "**Test Paper**\n  Open Access: Yes (gold)\n  [Source: Unpaywall]"

        from server import find_open_access
        result = await find_open_access("10.1234/test")
        assert "Unpaywall" in result
        assert "Open Access" in result


@pytest.mark.asyncio
async def test_find_open_access_cache_hit():
    """find_open_access returns cached result."""
    with patch("server._get_cache") as get_cache_mock:
        get_cache_mock.return_value.get.return_value = "**Cached OA**\n  [Source: Unpaywall]"

        from server import find_open_access
        result = await find_open_access("10.1234/test")
        assert "Cached OA" in result
