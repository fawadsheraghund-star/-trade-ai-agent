from pydantic import BaseSettings


class Settings(BaseSettings):
    APP_ENV: str = "development"
    SECRET_KEY: str = "changeme"

    TELEGRAM_BOT_TOKEN: str
    TELEGRAM_USE_WEBHOOK: bool = False
    TELEGRAM_WEBHOOK_URL: str | None = None

    PORT: int = 8000

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
