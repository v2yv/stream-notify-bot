import logging
import re

from telethon import TelegramClient
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.types import InputPeerChannel, PeerChannel

logger = logging.getLogger(__name__)

_NUMERIC = re.compile(r"^-?\d+$")


def _channel_id_variants(raw: str) -> list:
    """Build candidate refs for get_entity (numeric -100… ids need extra forms)."""
    s = raw.strip()
    out: list = []

    def add(v) -> None:
        if v is not None and v not in out:
            out.append(v)

    add(s)

    if s.startswith("@"):
        add(f"https://t.me/{s[1:]}")
        return out

    if s.startswith("https://t.me/") or s.startswith("t.me/"):
        add(s if s.startswith("https://") else f"https://{s}")
        return out

    if _NUMERIC.match(s):
        n = int(s)
        add(n)
        if str(n).startswith("-100"):
            inner = int(str(n)[4:])
            add(PeerChannel(inner))
            add(InputPeerChannel(inner, 0))
        return out

    add(f"@{s}")
    add(f"https://t.me/{s}")
    return out


async def resolve_channel(client: TelegramClient, channel_ref: str):
    """
    Resolve channel/group for send_message. Joins public channels if needed.
    """
    last_error: Exception | None = None

    for ref in _channel_id_variants(channel_ref):
        try:
            entity = await client.get_entity(ref)
            title = getattr(entity, "title", None) or getattr(entity, "username", ref)
            logger.info("Channel resolved: %s → %s (id=%s)", channel_ref, title, entity.id)
            return entity
        except Exception as exc:
            last_error = exc
            logger.debug("get_entity(%r) failed: %s", ref, exc)

    username = channel_ref.strip().lstrip("@")
    if username and not _NUMERIC.match(channel_ref.strip()):
        try:
            await client(JoinChannelRequest(username))
            entity = await client.get_entity(username)
            logger.info("Joined and resolved channel @%s", username)
            return entity
        except Exception as exc:
            last_error = exc
            logger.debug("JoinChannelRequest(@%s) failed: %s", username, exc)

    raise ValueError(
        f"Cannot resolve channel {channel_ref!r}: {last_error}. "
        "Use @channel_username, open the channel in Telegram as this account, "
        "or check TELEGRAM_CHANNEL_ID in .env."
    ) from last_error
