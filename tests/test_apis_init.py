import pytest
import httpx
from unittest.mock import AsyncMock, patch
from apis import make_request, make_request_text


@pytest.mark.asyncio
async def test_make_request_success():
    """make_request returns parsed JSON on success."""
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = lambda: None
    mock_response.json = lambda: {"data": "test"}

    with patch("apis.httpx.AsyncClient") as mock_client:
        instance = AsyncMock()
        instance.get.return_value = mock_response
        instance.__aenter__ = AsyncMock(return_value=instance)
        instance.__aexit__ = AsyncMock(return_value=False)
        mock_client.return_value = instance

        result = await make_request("https://example.com/api")
        assert result == {"data": "test"}


@pytest.mark.asyncio
async def test_make_request_http_error_raises():
    """make_request raises httpx.HTTPStatusError on HTTP errors."""
    mock_response = AsyncMock()
    mock_response.status_code = 429
    with patch("apis.httpx.AsyncClient") as mock_client:
        instance = AsyncMock()
        instance.get.side_effect = httpx.HTTPStatusError(
            "429", request=AsyncMock(), response=mock_response
        )
        instance.__aenter__ = AsyncMock(return_value=instance)
        instance.__aexit__ = AsyncMock(return_value=False)
        mock_client.return_value = instance

        with pytest.raises(httpx.HTTPStatusError):
            await make_request("https://example.com/api")


@pytest.mark.asyncio
async def test_make_request_connection_error_returns_none():
    """make_request returns None on connection failures."""
    with patch("apis.httpx.AsyncClient") as mock_client:
        instance = AsyncMock()
        instance.get.side_effect = httpx.ConnectError("connection refused")
        instance.__aenter__ = AsyncMock(return_value=instance)
        instance.__aexit__ = AsyncMock(return_value=False)
        mock_client.return_value = instance

        result = await make_request("https://example.com/api")
        assert result is None


@pytest.mark.asyncio
async def test_make_request_text_success():
    """make_request_text returns raw text on success."""
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = lambda: None
    mock_response.text = "@article{Smith2021, title={Test}}"

    with patch("apis.httpx.AsyncClient") as mock_client:
        instance = AsyncMock()
        instance.get.return_value = mock_response
        instance.__aenter__ = AsyncMock(return_value=instance)
        instance.__aexit__ = AsyncMock(return_value=False)
        mock_client.return_value = instance

        result = await make_request_text("https://doi.org/10.1234/test")
        assert "@article" in result


@pytest.mark.asyncio
async def test_make_request_text_failure_returns_none():
    """make_request_text returns None on connection error."""
    with patch("apis.httpx.AsyncClient") as mock_client:
        instance = AsyncMock()
        instance.get.side_effect = httpx.ConnectError("fail")
        instance.__aenter__ = AsyncMock(return_value=instance)
        instance.__aexit__ = AsyncMock(return_value=False)
        mock_client.return_value = instance

        result = await make_request_text("https://doi.org/10.1234/bad")
        assert result is None


@pytest.mark.asyncio
async def test_make_request_text_http_error_raises():
    """make_request_text raises httpx.HTTPStatusError on HTTP errors."""
    mock_response = AsyncMock()
    mock_response.status_code = 429
    with patch("apis.httpx.AsyncClient") as mock_client:
        instance = AsyncMock()
        instance.get.side_effect = httpx.HTTPStatusError(
            "429", request=AsyncMock(), response=mock_response
        )
        instance.__aenter__ = AsyncMock(return_value=instance)
        instance.__aexit__ = AsyncMock(return_value=False)
        mock_client.return_value = instance

        with pytest.raises(httpx.HTTPStatusError):
            await make_request_text("https://doi.org/10.1234/test")


# --- contact_email fallback chain ---

def test_contact_email_specific_var_wins(monkeypatch):
    from apis import contact_email
    monkeypatch.setenv("OPENALEX_EMAIL", "specific@example.com")
    monkeypatch.setenv("SCHOLARK_CONTACT_EMAIL", "shared@example.com")
    assert contact_email("OPENALEX_EMAIL") == "specific@example.com"


def test_contact_email_falls_back_to_shared(monkeypatch):
    from apis import contact_email
    monkeypatch.delenv("OPENALEX_EMAIL", raising=False)
    monkeypatch.setenv("SCHOLARK_CONTACT_EMAIL", "shared@example.com")
    assert contact_email("OPENALEX_EMAIL") == "shared@example.com"


def test_contact_email_empty_when_unset(monkeypatch):
    from apis import contact_email
    monkeypatch.delenv("CROSSREF_MAILTO", raising=False)
    monkeypatch.delenv("SCHOLARK_CONTACT_EMAIL", raising=False)
    assert contact_email("CROSSREF_MAILTO") == ""
