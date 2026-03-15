import pytest
import httpx
from unittest.mock import AsyncMock, patch
from apis.pubmed import search, get_paper_details, search_by_topic, format_paper
from apis.errors import SourceUnavailable, RateLimited


def _fake_epmc_paper():
    return {
        "title": "Deep Learning for EHR Analysis",
        "authorString": "Alice Smith, Bob Jones",
        "pubYear": "2023",
        "doi": "10.1234/epmc.2023",
        "pmid": "12345678",
        "pmcid": "PMC9999999",
        "journalTitle": "Nature Medicine",
        "abstractText": "We present a deep learning approach for EHR analysis.",
        "citedByCount": 15,
        "isOpenAccess": "Y",
    }


def _fake_epmc_response(papers=None):
    if papers is None:
        papers = [_fake_epmc_paper()]
    return {"resultList": {"result": papers}}


def test_format_paper_includes_source():
    result = format_paper(_fake_epmc_paper())
    assert "[Source: Europe PMC]" in result


def test_format_paper_includes_fields():
    result = format_paper(_fake_epmc_paper())
    assert "Deep Learning for EHR Analysis" in result
    assert "Alice Smith" in result
    assert "2023" in result
    assert "10.1234/epmc.2023" in result
    assert "12345678" in result
    assert "PMC9999999" in result
    assert "Nature Medicine" in result
    assert "15" in result
    assert "Yes" in result


def test_format_paper_missing_fields():
    paper = {"title": "Minimal Paper"}
    result = format_paper(paper)
    assert "Minimal Paper" in result
    assert "Not available" in result


@pytest.mark.asyncio
async def test_search_returns_formatted():
    with patch("apis.pubmed.make_request", new_callable=AsyncMock) as mock:
        mock.return_value = _fake_epmc_response()
        result = await search("deep learning EHR", limit=5)
        assert "Deep Learning" in result
        assert "[Source: Europe PMC]" in result


@pytest.mark.asyncio
async def test_search_empty_query_raises():
    with pytest.raises(SourceUnavailable) as exc_info:
        await search("   ")
    assert exc_info.value.source == "Europe PMC"


@pytest.mark.asyncio
async def test_search_no_results_raises():
    with patch("apis.pubmed.make_request", new_callable=AsyncMock) as mock:
        mock.return_value = {"resultList": {"result": []}}
        with pytest.raises(SourceUnavailable):
            await search("xyznonexistent")


@pytest.mark.asyncio
async def test_search_rate_limit_raises():
    mock_response = AsyncMock()
    mock_response.status_code = 429
    with patch("apis.pubmed.make_request", new_callable=AsyncMock) as mock:
        mock.side_effect = httpx.HTTPStatusError(
            "429", request=AsyncMock(), response=mock_response
        )
        with pytest.raises(RateLimited):
            await search("test")


@pytest.mark.asyncio
async def test_get_paper_details_success():
    with patch("apis.pubmed.make_request", new_callable=AsyncMock) as mock:
        mock.return_value = _fake_epmc_response()
        result = await get_paper_details("10.1234/epmc.2023")
        assert "Deep Learning" in result


@pytest.mark.asyncio
async def test_get_paper_details_no_results_raises():
    with patch("apis.pubmed.make_request", new_callable=AsyncMock) as mock:
        mock.return_value = {"resultList": {"result": []}}
        with pytest.raises(SourceUnavailable):
            await get_paper_details("10.1234/bad")


@pytest.mark.asyncio
async def test_search_by_topic_with_year_filter():
    with patch("apis.pubmed.make_request", new_callable=AsyncMock) as mock:
        mock.return_value = _fake_epmc_response()
        result = await search_by_topic("cancer", year_start=2020, year_end=2024)
        call_kwargs = mock.call_args
        params = call_kwargs.kwargs.get("params") or call_kwargs[1].get("params")
        assert "2020" in str(params)
        assert "2024" in str(params)
        assert "Deep Learning" in result


@pytest.mark.asyncio
async def test_search_by_topic_empty_raises():
    with pytest.raises(SourceUnavailable):
        await search_by_topic("  ")
