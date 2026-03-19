import pytest
import httpx
from unittest.mock import AsyncMock, MagicMock, patch
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


@pytest.mark.asyncio
async def test_make_request_post_with_json():
    """make_request sends POST when json parameter is provided."""
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.json.return_value = {"result": "ok"}
        mock_response.raise_for_status = MagicMock()
        mock_client.post.return_value = mock_response
        mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_class.return_value.__aexit__ = AsyncMock(return_value=False)

        from apis import make_request
        result = await make_request("http://test", json={"key": "value"})
        mock_client.post.assert_called_once()
        assert result == {"result": "ok"}
