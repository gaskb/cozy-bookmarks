from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    env: str = "development"
    log_level: str = "INFO"
    database_url: str = "sqlite:///./data/cozy_bookmarks.db"

    session_cookie_secure: bool = True

    ai_timeout_seconds: float = 30.0

    # "claude" for the native Anthropic adapter; anything else uses the OpenAI-compatible slot below
    ai_provider: str = "openai_compatible"
    ai_openai_compatible_base_url: str = "http://localhost:8000/v1"
    ai_openai_compatible_model: str = "default"
    ai_openai_compatible_api_key: str = ""

    ai_claude_api_key: str = ""
    ai_claude_model: str = "claude-opus-5"

    ai_tagging_enabled: bool = True

    # SMTP / Daily Digest configuration
    smtp_enabled: bool = False
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = "Cozy Bookmarks <noreply@example.com>"
    smtp_tls: bool = True
    smtp_ssl: bool = False
    base_url: str = "http://bookmarks.example.com"


settings = Settings()
