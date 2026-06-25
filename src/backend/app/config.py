from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    SECRET_KEY: str
    ADMIN_PASSWORD: str = "admin123"
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/nodeping.db"
    TELEGRAM_TOKEN: Optional[str] = None
    TELEGRAM_CHAT_ID: Optional[str] = None
    JWT_EXPIRY_HOURS: int = 12
    RATE_LIMIT_WINDOW_MINUTES: int = 15
    RATE_LIMIT_MAX_ATTEMPTS: int = 5


settings = Settings()
