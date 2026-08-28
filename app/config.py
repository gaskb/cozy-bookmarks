from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    env: str = "development"
    log_level: str = "INFO"
    database_url: str = "sqlite:///./data/cozy_bookmarks.db"
    secret_key: str = "dev-secret-change-me"

    ai_timeout_seconds: float = 30.0
    ai_local_base_url: str = "http://localhost:8000/v1"
    ai_local_model: str = "default"
    ai_local_api_key: str = ""


settings = Settings()
