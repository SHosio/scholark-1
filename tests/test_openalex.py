import pytest
import httpx
from unittest.mock import AsyncMock, patch
from apis.openalex import (
    search, get_paper_details, search_by_topic, format_paper, is_retracted,
)
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


def test_format_paper_flags_preprint():
    work = _fake_openalex_work()
    work["type"] = "preprint"
    result = format_paper(work)
    assert "preprint (not peer reviewed)" in result


def test_format_paper_no_preprint_line_for_articles():
    work = _fake_openalex_work()
    work["type"] = "article"
    result = format_paper(work)
    assert "preprint" not in result.lower()


def test_format_paper_flags_retracted():
    work = _fake_openalex_work()
    work["is_retracted"] = True
    result = format_paper(work)
    assert "RETRACTED" in result


def test_format_paper_no_retraction_line_when_not_retracted():
    work = _fake_openalex_work()
    work["is_retracted"] = False
    result = format_paper(work)
    assert "RETRACTED" not in result


@pytest.mark.asyncio
async def test_is_retracted_true():
    with patch("apis.openalex.make_request", new_callable=AsyncMock) as mock:
        mock.return_value = {"is_retracted": True}
        assert await is_retracted("10.1234/test") is True


@pytest.mark.asyncio
async def test_is_retracted_false():
    with patch("apis.openalex.make_request", new_callable=AsyncMock) as mock:
        mock.return_value = {"is_retracted": False}
        assert await is_retracted("10.1234/test") is False


@pytest.mark.asyncio
async def test_is_retracted_unavailable_returns_none():
    with patch("apis.openalex.make_request", new_callable=AsyncMock) as mock:
        mock.return_value = None
        assert await is_retracted("10.1234/test") is None


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


@pytest.mark.asyncio
async def test_search_sends_mailto_read_at_call_time(monkeypatch):
    monkeypatch.setenv("OPENALEX_EMAIL", "polite@example.com")
    fake_resp = {"results": [_fake_openalex_work()]}
    with patch("apis.openalex.make_request", new_callable=AsyncMock) as mock:
        mock.return_value = fake_resp
        await search("test query")
        params = mock.call_args.kwargs.get("params") or mock.call_args[1].get("params")
        assert params.get("mailto") == "polite@example.com"
