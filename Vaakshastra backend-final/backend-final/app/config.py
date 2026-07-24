"""
App configuration - loaded from environment variables (or a .env file).

Copy .env.example to .env and fill in your own secrets. Never commit .env.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "VaakShastra"
    debug: bool = True

    # Storage
    storage_backend: str = "local"
    local_upload_dir: str = "./uploads"
    max_file_size_mb: int = 10

    # Database
    database_url: str = "sqlite+aiosqlite:///./vaakshastra.db"

    # Groq LLM - REQUIRED, set in .env
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"

    # JWT - set a strong secret in .env for production
    jwt_secret_key: str = "local-dev-secret-key"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60

    @property
    def max_file_size_bytes(self) -> int:
        return self.max_file_size_mb * 1024 * 1024


settings = Settings()
