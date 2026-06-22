from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    supabase_url: str
    supabase_anon_key: str
    supabase_service_role_key: str

    database_url: str

    openai_api_key: str
    openai_embedding_model: str = "text-embedding-3-small"
    openai_embedding_dimensions: int = 1536

    allowed_origins: str = "http://localhost:5173"

    @property
    def allowed_origins_list(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",")]


settings = Settings()
