import pytest
from unittest.mock import AsyncMock, patch
from apis.semantic_scholar import get_citation_context
from apis.errors import SourceUnavailable


def _fake_citation_data(with_contexts=True):
    """Fake Semantic Scholar citations response."""
    entry = {
        "citingPaper": {
            "title": "Follow-up Study on Gamification",
            "authors": [{"name": "Alice Zhang"}, {"name": "Bob Lee"}],
            "year": 2023,
            "externalIds": {"DOI": "10.1234/followup"},
            "venue": "CHI 2023",
        },
    }
    if with_contexts:
        entry["contexts"] = [
            "Smith et al. reported a 30% increase in engagement.",
            "However, the effect was not replicated in our longitudinal study.",
        ]
    else:
        entry["contexts"] = []

    return {"data": [entry]}


@pytest.mark.asyncio
async def test_citation_context_returns_formatted():
    with patch("apis.semantic_scholar._call_api", new_callable=AsyncMock) as mock:
        mock.return_value = _fake_citation_data()
        result = await get_citation_context("10.1234/original")
        assert "Follow-up Study on Gamification" in result
        assert "Alice Zhang" in result
        assert "30% increase" in result
        assert "not replicated" in result
        assert "CHI 2023" in result
        assert "[Source: Semantic Scholar citation contexts]" in result


@pytest.mark.asyncio
async def test_citation_context_no_contexts_raises():
    with patch("apis.semantic_scholar._call_api", new_callable=AsyncMock) as mock:
        mock.return_value = _fake_citation_data(with_contexts=False)
        with pytest.raises(SourceUnavailable) as exc_info:
            await get_citation_context("10.1234/original")
        assert "none with context sentences" in exc_info.value.reason


@pytest.mark.asyncio
async def test_citation_context_no_data_raises():
    with patch("apis.semantic_scholar._call_api", new_callable=AsyncMock) as mock:
        mock.return_value = {"data": []}
        with pytest.raises(SourceUnavailable):
            await get_citation_context("10.1234/nothing")


@pytest.mark.asyncio
async def test_citation_context_mixed_with_and_without():
    """Papers with and without contexts — only those with contexts are shown."""
    data = {
        "data": [
            {
                "citingPaper": {
                    "title": "Paper With Context",
                    "authors": [{"name": "A"}],
                    "year": 2023,
                    "externalIds": {},
                    "venue": "",
                },
                "contexts": ["Referenced the original finding."],
            },
            {
                "citingPaper": {
                    "title": "Paper Without Context",
                    "authors": [{"name": "B"}],
                    "year": 2022,
                    "externalIds": {},
                    "venue": "",
                },
                "contexts": [],
            },
        ]
    }
    with patch("apis.semantic_scholar._call_api", new_callable=AsyncMock) as mock:
        mock.return_value = data
        result = await get_citation_context("10.1234/test")
        assert "Paper With Context" in result
        assert "Paper Without Context" not in result
        assert "1 additional citing paper" in result


@pytest.mark.asyncio
async def test_citation_context_server_tool():
    """Test the server-level get_citation_context tool."""
    with patch("apis.semantic_scholar.get_citation_context", new_callable=AsyncMock) as mock, \
         patch("server._get_cache") as cache_mock:
        cache_mock.return_value.get.return_value = None
        mock.return_value = "**Citing Paper**\n  > \"context sentence\"\n[Source: Semantic Scholar citation contexts]"

        from server import get_citation_context
        result = await get_citation_context("10.1234/test")
        assert "context sentence" in result
        cache_mock.return_value.put.assert_called_once()
