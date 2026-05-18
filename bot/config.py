from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
SESSION_PATH = DATA_DIR / "notify_session"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ROOT_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    TELEGRAM_API_ID: int
    TELEGRAM_API_HASH: str
    TELEGRAM_CHANNEL_ID: str  # @mychannel or -1001234567890
    TELEGRAM_PHONE: str | None = None  # +79991234567 — only for first login

    TWITCH_USERNAME: str
    TIKTOK_USERNAME: str
    CHECK_INTERVAL: int = 30


settings = Settings()
