import pytest
import httpx
from unittest.mock import AsyncMock, patch
from apis.semantic_scholar import search, get_paper_details, search_by_topic, format_paper
from apis.errors import SourceUnavailable, RateLimited


def _fake_paper():
    return {
        "paperId": "abc123",
        "title": "Spaced Repetition and Learning",
        "authors": [{"name": "Alice Smith"}, {"name": "Bob Jones"}],
        "year": 2021,
        "externalIds": {"DOI": "10.1234/test.2021"},
        "abstract": "We studied spaced repetition...",
        "venue": "CHI 2021",
        "isOpenAccess": True,
        "openAccessPdf": {"url": "https://example.com/paper.pdf"},
        "tldr": {"text": "Spaced repetition works."},
        "citationCount": 42,
    }


def test_format_paper_includes_source():
    """Formatted output must state the source."""
    result = format_paper(_fake_paper())
    assert "[Source: Semantic Scholar]" in result


def test_format_paper_includes_all_fields():
    paper = _fake_paper()
    result = format_paper(paper)
    assert "Spaced Repetition and Learning" in result
    assert "Alice Smith" in result
    assert "2021" in result
    assert "10.1234/test.2021" in result
    assert "CHI 2021" in result
    assert "We studied spaced repetition" in result


def test_format_paper_missing_fields():
    """Missing fields should show 'Not available', not crash."""
    paper = {"paperId": "abc", "title": "Minimal Paper"}
    result = format_paper(paper)
    assert "Minimal Paper" in result
    assert "Not available" in result


@pytest.mark.asyncio
async def test_search_returns_formatted_results():
    fake_response = {"data": [_fake_paper()]}
    with patch("apis.semantic_scholar.make_request", new_callable=AsyncMock) as mock:
        mock.return_value = fake_response
        result = await search("spaced repetition", limit=5)
        assert "Spaced Repetition and Learning" in result
        assert "[Source: Semantic Scholar]" in result


@pytest.mark.asyncio
async def test_search_api_failure_raises():
    with patch("apis.semantic_scholar.make_request", new_callable=AsyncMock) as mock:
        mock.return_value = None
        with pytest.raises(SourceUnavailable) as exc_info:
            await search("spaced repetition")
        assert exc_info.value.source == "Semantic Scholar"


@pytest.mark.asyncio
async def test_search_rate_limit_raises():
    mock_response = AsyncMock()
    mock_response.status_code = 429
    with patch("apis.semantic_scholar.make_request", new_callable=AsyncMock) as mock:
        mock.side_effect = httpx.HTTPStatusError(
            "429", request=AsyncMock(), response=mock_response
        )
        with pytest.raises(RateLimited) as exc_info:
            await search("spaced repetition")
        assert exc_info.value.source == "Semantic Scholar"


@pytest.mark.asyncio
async def test_search_by_topic_with_year_range():
    fake_response = {"data": [_fake_paper()]}
    with patch("apis.semantic_scholar.make_request", new_callable=AsyncMock) as mock:
        mock.return_value = fake_response
        result = await search_by_topic("HCI", year_start=2020, year_end=2024)
        call_kwargs = mock.call_args
        assert "2020-2024" in str(call_kwargs)
