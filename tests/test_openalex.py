import pytest
import httpx
from unittest.mock import AsyncMock, patch
from apis.openalex import search, get_paper_details, search_by_topic, format_paper
from apis.errors import SourceUnavailable, RateLimited


def _fake_openalex_work():
    return {
        "id": "https://openalex.org/W12345",
        "title": "Spaced Repetition and Learning",
        "authorships": [
            {"author": {"display_name": "Alice Smith"}},
            {"author": {"display_name": "Bob Jones"}},
        ],
        "publication_year": 2021,
        "doi": "https://doi.org/10.1234/test.2021",
        "primary_location": {
            "source": {"display_name": "CHI Conference"}
        },
        "cited_by_count": 42,
        "open_access": {"is_oa": True},
        "abstract_inverted_index": {
            "We": [0],
            "studied": [1],
            "spaced": [2],
            "repetition": [3],
        },
    }


def test_format_paper_includes_source():
    result = format_paper(_fake_openalex_work())
    assert "[Source: OpenAlex]" in result


def test_format_paper_includes_fields():
    result = format_paper(_fake_openalex_work())
    assert "Spaced Repetition and Learning" in result
    assert "Alice Smith" in result
    assert "2021" in result
    assert "10.1234/test.2021" in result
    assert "CHI Conference" in result
    assert "42" in result


def test_format_paper_missing_fields():
    paper = {"id": "https://openalex.org/W999", "title": "Minimal"}
    result = format_paper(paper)
    assert "Minimal" in result
    assert "Not available" in result


def test_format_paper_reconstructs_abstract():
    result = format_paper(_fake_openalex_work())
    assert "We studied spaced repetition" in result


@pytest.mark.asyncio
async def test_search_returns_formatted():
    fake_resp = {"results": [_fake_openalex_work()]}
    with patch("apis.openalex.make_request", new_callable=AsyncMock) as mock:
        mock.return_value = fake_resp
        result = await search("spaced repetition", limit=5)
        assert "Spaced Repetition" in result
        assert "[Source: OpenAlex]" in result


@pytest.mark.asyncio
async def test_search_failure_raises():
    with patch("apis.openalex.make_request", new_callable=AsyncMock) as mock:
        mock.return_value = None
        with pytest.raises(SourceUnavailable) as exc_info:
            await search("test")
        assert exc_info.value.source == "OpenAlex"


@pytest.mark.asyncio
async def test_search_rate_limit_raises():
    mock_response = AsyncMock()
    mock_response.status_code = 429
    with patch("apis.openalex.make_request", new_callable=AsyncMock) as mock:
        mock.side_effect = httpx.HTTPStatusError(
            "429", request=AsyncMock(), response=mock_response
        )
        with pytest.raises(RateLimited):
            await search("test")


@pytest.mark.asyncio
async def test_get_paper_details_success():
    with patch("apis.openalex.make_request", new_callable=AsyncMock) as mock:
        mock.return_value = _fake_openalex_work()
        result = await get_paper_details("10.1234/test.2021")
        assert "Spaced Repetition" in result


@pytest.mark.asyncio
async def test_get_paper_details_failure_raises():
    with patch("apis.openalex.make_request", new_callable=AsyncMock) as mock:
        mock.return_value = None
        with pytest.raises(SourceUnavailable):
            await get_paper_details("10.1234/bad")


@pytest.mark.asyncio
async def test_search_by_topic_with_year_filter():
    fake_resp = {"results": [_fake_openalex_work()]}
    with patch("apis.openalex.make_request", new_callable=AsyncMock) as mock:
        mock.return_value = fake_resp
        result = await search_by_topic("HCI", year_start=2020, year_end=2024)
        call_kwargs = mock.call_args
        params = call_kwargs.kwargs.get("params") or call_kwargs[1].get("params")
        assert "publication_year:2020-2024" in str(params)
        assert "Spaced Repetition" in result
