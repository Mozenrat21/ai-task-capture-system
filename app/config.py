from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings.

    Values can be loaded from environment variables or from .env file.
    In Docker, DATABASE_URL is passed through docker-compose.yml.
    """

    app_name: str = "AI Task Capture System"
    app_env: str = "local"

    database_url: str = (
        "postgresql+psycopg://task_user:task_password@localhost:5433/task_capture_db"
    )

    ai_provider: str = "mock"
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini" 
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()