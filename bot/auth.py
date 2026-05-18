"""
One-time Telegram login. Creates data/notify_session.session for main.py.

Run from project root:
    python bot/auth.py

Or inside Docker (interactive, needs TTY):
    docker compose run --rm -it bot python bot/auth.py
"""

import asyncio
import logging
import sys

from telethon import TelegramClient

from config import DATA_DIR, SESSION_PATH, settings

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


async def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    client = TelegramClient(
        str(SESSION_PATH),
        settings.TELEGRAM_API_ID,
        settings.TELEGRAM_API_HASH,
    )

    await client.start(phone=settings.TELEGRAM_PHONE)
    me = await client.get_me()
    logger.info(
        "OK — session saved to %s.session\n"
        "Account: %s (id=%s)\n"
        "You can remove TELEGRAM_PHONE from .env and run: python bot/main.py",
        SESSION_PATH.name,
        me.username or me.first_name,
        me.id,
    )
    await client.disconnect()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(130)
