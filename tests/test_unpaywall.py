import pytest
import httpx
from unittest.mock import AsyncMock, patch
from apis.unpaywall import find_open_access, format_result
from apis.errors import SourceUnavailable


def _fake_unpaywall_response(is_oa=True):
    data = {
        "title": "Deep Learning for Clinical NLP",
        "doi": "10.1234/test.2023",
        "is_oa": is_oa,
        "oa_status": "gold" if is_oa else "closed",
        "journal_name": "Nature Medicine",
        "publisher": "Springer Nature",
        "year": 2023,
    }
    if is_oa:
        data["best_oa_location"] = {
            "url": "https://europepmc.org/article/123",
            "url_for_pdf": "https://europepmc.org/article/123.pdf",
            "host_type": "repository",
            "version": "publishedVersion",
            "license": "cc-by",
        }
        data["oa_locations"] = [data["best_oa_location"]]
    else:
        data["best_oa_location"] = None
        data["oa_locations"] = []
    return data


def test_format_result_oa_paper():
    result = format_result(_fake_unpaywall_response(is_oa=True))
    assert "[Source: Unpaywall]" in result
    assert "Deep Learning for Clinical NLP" in result
    assert "Yes" in result
    assert "gold" in result
    assert "europepmc.org" in result
    assert "cc-by" in result


def test_format_result_closed_paper():
    result = format_result(_fake_unpaywall_response(is_oa=False))
    assert "No" in result
    assert "closed" in result
    assert "No open access version found" in result


def test_format_result_missing_fields():
    data = {"doi": "10.1234/test", "is_oa": False, "oa_status": "closed"}
    result = format_result(data)
    assert "Not available" in result
    assert "[Source: Unpaywall]" in result


@pytest.mark.asyncio
async def test_find_open_access_success():
    with patch("apis.unpaywall.make_request", new_callable=AsyncMock) as mock, \
         patch.dict("os.environ", {"UNPAYWALL_EMAIL": "test@example.com"}):
        mock.return_value = _fake_unpaywall_response()
        result = await find_open_access("10.1234/test.2023")
        assert "Deep Learning" in result
        assert "[Source: Unpaywall]" in result


@pytest.mark.asyncio
async def test_find_open_access_no_email_raises():
    with patch.dict("os.environ", {}, clear=True):
        with pytest.raises(SourceUnavailable) as exc_info:
            await find_open_access("10.1234/test")
        assert "no email" in exc_info.value.reason


@pytest.mark.asyncio
async def test_find_open_access_empty_doi_raises():
    with patch.dict("os.environ", {"UNPAYWALL_EMAIL": "test@example.com"}):
        with pytest.raises(SourceUnavailable):
            await find_open_access("   ")


@pytest.mark.asyncio
async def test_find_open_access_404_raises():
    mock_response = AsyncMock()
    mock_response.status_code = 404
    with patch("apis.unpaywall.make_request", new_callable=AsyncMock) as mock, \
         patch.dict("os.environ", {"UNPAYWALL_EMAIL": "test@example.com"}):
        mock.side_effect = httpx.HTTPStatusError(
            "404", request=AsyncMock(), response=mock_response
        )
        with pytest.raises(SourceUnavailable) as exc_info:
            await find_open_access("10.1234/nonexistent")
        assert "not found" in exc_info.value.reason


@pytest.mark.asyncio
async def test_find_open_access_422_raises():
    mock_response = AsyncMock()
    mock_response.status_code = 422
    with patch("apis.unpaywall.make_request", new_callable=AsyncMock) as mock, \
         patch.dict("os.environ", {"UNPAYWALL_EMAIL": "test@example.com"}):
        mock.side_effect = httpx.HTTPStatusError(
            "422", request=AsyncMock(), response=mock_response
        )
        with pytest.raises(SourceUnavailable) as exc_info:
            await find_open_access("not-a-doi")
        assert "invalid DOI" in exc_info.value.reason
