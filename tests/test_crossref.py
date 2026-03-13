import pytest
from unittest.mock import AsyncMock, patch
from apis.crossref import search, get_paper_details, get_bibtex, format_paper, _normalize_doi


def _fake_crossref_item():
    return {
        "DOI": "10.1234/test.2021",
        "title": ["Spaced Repetition and Learning"],
        "author": [
            {"given": "Alice", "family": "Smith"},
            {"given": "Bob", "family": "Jones"},
        ],
        "published-print": {"date-parts": [[2021, 3]]},
        "container-title": ["CHI Conference"],
        "abstract": "We studied spaced repetition...",
        "is-referenced-by-count": 42,
    }


def test_normalize_doi_bare():
    assert _normalize_doi("10.1234/test") == "10.1234/test"


def test_normalize_doi_url():
    assert _normalize_doi("https://doi.org/10.1234/test") == "10.1234/test"


def test_normalize_doi_prefix():
    assert _normalize_doi("doi: 10.1234/test") == "10.1234/test"


def test_normalize_doi_http_url():
    assert _normalize_doi("http://doi.org/10.1234/test") == "10.1234/test"


def test_format_paper_includes_source():
    result = format_paper(_fake_crossref_item())
    assert "[Source: Crossref]" in result


def test_format_paper_includes_fields():
    result = format_paper(_fake_crossref_item())
    assert "Spaced Repetition and Learning" in result
    assert "Alice Smith" in result
    assert "2021" in result
    assert "10.1234/test.2021" in result


def test_format_paper_missing_fields():
    paper = {"DOI": "10.xxx/yyy"}
    result = format_paper(paper)
    assert "10.xxx/yyy" in result
    assert "Not available" in result


@pytest.mark.asyncio
async def test_search_returns_formatted():
    fake_resp = {"message": {"items": [_fake_crossref_item()]}}
    with patch("apis.crossref.make_request", new_callable=AsyncMock) as mock:
        mock.return_value = fake_resp
        result = await search("spaced repetition", limit=5)
        assert "Spaced Repetition" in result
        assert "[Source: Crossref]" in result


@pytest.mark.asyncio
async def test_search_failure():
    with patch("apis.crossref.make_request", new_callable=AsyncMock) as mock:
        mock.return_value = None
        result = await search("test")
        assert "No results" in result or "unavailable" in result.lower()


@pytest.mark.asyncio
async def test_get_bibtex_success():
    fake_bibtex = "@article{Smith2021,\n  title={Test},\n  author={Smith}\n}"
    with patch("apis.crossref.make_request_text", new_callable=AsyncMock) as mock:
        mock.return_value = fake_bibtex
        result = await get_bibtex("10.1234/test.2021")
        assert "@article" in result
        assert "[Source: DOI content negotiation]" in result


@pytest.mark.asyncio
async def test_get_bibtex_failure():
    with patch("apis.crossref.make_request_text", new_callable=AsyncMock) as mock:
        mock.return_value = None
        result = await get_bibtex("10.1234/bad")
        assert "Could not" in result
