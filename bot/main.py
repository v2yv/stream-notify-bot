import asyncio
import logging
import sys
from pathlib import Path

from telethon import TelegramClient

from config import DATA_DIR, SESSION_PATH, settings
from monitors.tiktok import TikTokMonitor
from monitors.twitch import TwitchMonitor
from notifier import Notifier

LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_DIR / "bot.log", encoding="utf-8"),
    ],
)

logger = logging.getLogger(__name__)


async def main() -> None:
    logger.info("Starting stream notifier (user account)...")

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    client = TelegramClient(
        str(SESSION_PATH),
        settings.TELEGRAM_API_ID,
        settings.TELEGRAM_API_HASH,
    )

    await client.start(phone=settings.TELEGRAM_PHONE)
    me = await client.get_me()
    logger.info(
        "Telegram: logged in as %s (id=%s)",
        me.username or me.first_name,
        me.id,
    )

    notifier = Notifier(client=client, channel_id=settings.TELEGRAM_CHANNEL_ID)
    await notifier.connect()

    twitch_monitor = TwitchMonitor(
        username=settings.TWITCH_USERNAME,
        notifier=notifier,
        interval=settings.CHECK_INTERVAL,
    )
    tiktok_monitor = TikTokMonitor(
        username=settings.TIKTOK_USERNAME,
        notifier=notifier,
        interval=settings.CHECK_INTERVAL,
    )

    try:
        await asyncio.gather(
            twitch_monitor.run(),
            tiktok_monitor.run(),
        )
    except (KeyboardInterrupt, SystemExit):
        logger.info("Stopped by user.")
    finally:
        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
