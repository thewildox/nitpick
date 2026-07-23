from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str
    redis_url: str
    celery_broker_url: str
    celery_result_backend: str
    github_webhook_secret: str
    github_token: str
    anthropic_api_key: str
    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()