from supabase import AsyncClient, AsyncClientOptions, create_async_client

from app.config import settings


def _server_options(*, authorization: str | None = None) -> AsyncClientOptions:
    headers: dict[str, str] = {}
    if authorization is not None:
        headers["Authorization"] = authorization
    return AsyncClientOptions(
        headers=headers,
        auto_refresh_token=False,
        persist_session=False,
    )


async def create_user_client(access_token: str) -> AsyncClient:
    """Supabase client scoped to the authenticated user's JWT (RLS enforced)."""
    if not access_token:
        raise ValueError("access_token is required")

    return await create_async_client(
        settings.supabase_url,
        settings.supabase_anon_key,
        options=_server_options(authorization=f"Bearer {access_token}"),
    )


async def create_service_role_client() -> AsyncClient:
    """Supabase client with service-role privileges (backend only)."""
    return await create_async_client(
        settings.supabase_url,
        settings.supabase_service_role_key,
        options=_server_options(),
    )
