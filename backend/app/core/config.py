from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    # Supabase
    supabase_url: str
    supabase_key: str

    # Slack
    slack_bot_token: str
    slack_signing_secret: str
    slack_user_id_danielle: str = "PLACEHOLDER_DANIELLE"
    slack_user_id_michael: str = "PLACEHOLDER_MICHAEL"
    slack_user_id_david: str = "PLACEHOLDER_DAVID"
    slack_user_id_jeff: str = "PLACEHOLDER_JEFF"

    # Anthropic
    anthropic_api_key: str

    # External data sources
    serper_api_key: str = ""
    news_api_key: str = ""

    # App
    dashboard_url: str = "http://localhost:3000"
    internal_api_key: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache()
def get_settings() -> Settings:
    return Settings()
