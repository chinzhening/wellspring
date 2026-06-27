from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    log_level: str = "INFO"
    export_dir: str = "exports"

    database_url: str
    gemini_api_key: str | None = None
    youtube_api_key: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


try:
    settings = Settings()
except Exception as e:
    raise RuntimeError("Missing required environment configuration") from e
