import asyncio
from unittest.mock import AsyncMock, patch

import pytest
from supabase import AsyncClientOptions

from app.config import settings
from app.database import supabase as supabase_module


def test_create_user_client_uses_anon_key_and_bearer_token():
    with patch.object(
        supabase_module,
        "create_async_client",
        new_callable=AsyncMock,
    ) as mock_create:
        mock_create.return_value = object()

        asyncio.run(supabase_module.create_user_client("user-jwt"))

        mock_create.assert_awaited_once()
        url, key = mock_create.call_args.args
        options = mock_create.call_args.kwargs["options"]
        assert url == settings.supabase_url
        assert key == settings.supabase_anon_key
        assert options.headers["Authorization"] == "Bearer user-jwt"
        assert options.auto_refresh_token is False
        assert options.persist_session is False


def test_create_service_role_client_uses_service_role_key():
    with patch.object(
        supabase_module,
        "create_async_client",
        new_callable=AsyncMock,
    ) as mock_create:
        mock_create.return_value = object()

        asyncio.run(supabase_module.create_service_role_client())

        mock_create.assert_awaited_once()
        url, key = mock_create.call_args.args
        options = mock_create.call_args.kwargs["options"]
        assert url == settings.supabase_url
        assert key == settings.supabase_service_role_key
        assert "Authorization" not in options.headers
        assert options.auto_refresh_token is False
        assert options.persist_session is False


def test_server_options_without_authorization():
    options = supabase_module._server_options()
    assert isinstance(options, AsyncClientOptions)
    assert options.headers == {}
    assert options.auto_refresh_token is False
    assert options.persist_session is False


def test_create_user_client_rejects_empty_token():
    with pytest.raises(ValueError, match="access_token is required"):
        asyncio.run(supabase_module.create_user_client(""))
