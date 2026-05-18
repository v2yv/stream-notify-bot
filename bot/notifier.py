import logging
from typing import Any

from telethon import TelegramClient

from telegram_channel import resolve_channel

logger = logging.getLogger(__name__)


class Notifier:
    """Posts stream-start notifications to a channel from the user account."""

    def __init__(self, client: TelegramClient, channel_id: str) -> None:
        self._client = client
        self._channel_ref = channel_id
        self._channel: Any = None

    async def connect(self) -> None:
        self._channel = await resolve_channel(self._client, self._channel_ref)

    async def notify_twitch(self, username: str, stream_title: str = "") -> None:
        url = f"https://twitch.tv/{username}"
        title_line = f"\n🎮 <b>{stream_title}</b>" if stream_title else ""
        text = (
            f"❤️ Стримчик уже начался, залетайте ❤️{title_line}\n\n"
            f'🔗 <a href="{url}">{url}</a>'
        )
        await self._send(text)

    async def notify_tiktok(self, username: str) -> None:
        clean = username.lstrip("@")
        url = f"https://www.tiktok.com/@{clean}/live"
        text = (
            f"🔥 Я уже в LIVE, заходите 👀\n\n"
            f'🔗 <a href="{url}">Смотреть трансляцию</a>'
        )
        await self._send(text)

    async def _send(self, text: str) -> None:
        if self._channel is None:
            await self.connect()
        try:
            await self._client.send_message(
                self._channel,
                text,
                parse_mode="html",
                link_preview=True,
            )
            logger.info("Notification sent to %s", self._channel_ref)
        except Exception as exc:
            logger.error("Failed to send notification: %s", exc, exc_info=True)
