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
async def test_make_request_failure_returns_none():
    """make_request returns None on HTTP error."""
    with patch("apis.httpx.AsyncClient") as mock_client:
        instance = AsyncMock()
        instance.get.side_effect = httpx.HTTPStatusError(
            "404", request=AsyncMock(), response=AsyncMock()
        )
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
    """make_request_text returns None on HTTP error."""
    with patch("apis.httpx.AsyncClient") as mock_client:
        instance = AsyncMock()
        instance.get.side_effect = httpx.HTTPError("fail")
        instance.__aenter__ = AsyncMock(return_value=instance)
        instance.__aexit__ = AsyncMock(return_value=False)
        mock_client.return_value = instance

        result = await make_request_text("https://doi.org/10.1234/bad")
        assert result is None
