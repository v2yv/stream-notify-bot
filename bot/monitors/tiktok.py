import asyncio
import logging

from TikTokLive import TikTokLiveClient
from TikTokLive.client.errors import AlreadyConnectedError, UserOfflineError

from notifier import Notifier

logger = logging.getLogger(__name__)


class TikTokMonitor:
    """Polls TikTok LIVE status via TikTokLive (same approach as test/main.py)."""

    def __init__(
        self,
        username: str,
        notifier: Notifier,
        interval: int = 30,
    ) -> None:
        self._username = username.lstrip("@")
        self._notifier = notifier
        self._interval = interval
        self._is_live: bool = False

    async def run(self) -> None:
        logger.info("[TikTok] Monitor started for @%s", self._username)
        while True:
            try:
                await self._tick()
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                logger.error("[TikTok] Unexpected error: %s", exc, exc_info=True)
            await asyncio.sleep(self._interval)

    async def _tick(self) -> None:
        is_live = await self._check_live()

        if is_live is None:
            return

        if is_live and not self._is_live:
            self._is_live = True
            logger.info("[TikTok] @%s went LIVE.", self._username)
            await self._notifier.notify_tiktok(username=self._username)
        elif not is_live and self._is_live:
            logger.info("[TikTok] @%s LIVE ended.", self._username)
            self._is_live = False

    async def _check_live(self) -> bool | None:
        client = TikTokLiveClient(unique_id=self._username)
        try:
            return await client.is_live()
        except UserOfflineError:
            return False
        except AlreadyConnectedError:
            logger.warning("[TikTok] Client already connected, skip tick.")
            return None
        except Exception as exc:
            err = str(exc).lower()
            if any(k in err for k in ("rate limit", "429", "too many")):
                logger.warning("[TikTok] Rate limit: %s", exc)
            else:
                logger.error("[TikTok] Check failed: %s", exc)
            return None
        finally:
            try:
                await client.disconnect()
            except Exception:
                pass
