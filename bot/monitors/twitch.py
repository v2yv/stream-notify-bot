import asyncio
import logging
from typing import Optional

import aiohttp

from notifier import Notifier

logger = logging.getLogger(__name__)

# Public Client-ID used by the Twitch website itself — no app registration needed
_GQL_CLIENT_ID = "kimne78kx3ncx6brgo4mv6wki5h1ko"
_GQL_URL = "https://gql.twitch.tv/gql"

_QUERY = """
query StreamStatus($login: String!) {
  user(login: $login) {
    stream {
      id
      title
      game {
        name
      }
    }
  }
}
"""


class TwitchMonitor:
    """
    Polls the Twitch GQL API every `interval` seconds.
    No app registration required — uses the same Client-ID as twitch.tv.
    Sends a notification on offline → live transition; resets on stream end.
    """

    def __init__(
        self,
        username: str,
        notifier: Notifier,
        interval: int = 30,
    ) -> None:
        self._username = username
        self._notifier = notifier
        self._interval = interval
        self._is_live: bool = False

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    async def run(self) -> None:
        logger.info("[Twitch] Monitor started for user '%s'", self._username)
        headers = {
            "Client-ID": _GQL_CLIENT_ID,
            "Content-Type": "application/json",
        }
        async with aiohttp.ClientSession(headers=headers) as session:
            self._session = session
            while True:
                try:
                    await self._tick()
                except asyncio.CancelledError:
                    raise
                except Exception as exc:
                    logger.error("[Twitch] Unexpected error: %s", exc, exc_info=True)
                await asyncio.sleep(self._interval)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    async def _tick(self) -> None:
        stream = await self._get_stream()

        if stream is not None:
            if not self._is_live:
                self._is_live = True
                title: str = stream.get("title") or ""
                game: str = (stream.get("game") or {}).get("name", "")
                display = f"{title} — {game}" if game else title
                logger.info(
                    "[Twitch] '%s' went LIVE. %s", self._username, display
                )
                await self._notifier.notify_twitch(
                    username=self._username, stream_title=display
                )
        else:
            if self._is_live:
                logger.info("[Twitch] '%s' stream ended.", self._username)
            self._is_live = False

    async def _get_stream(self) -> Optional[dict]:
        """Returns stream dict if live, None otherwise."""
        payload = {
            "query": _QUERY,
            "variables": {"login": self._username},
        }
        try:
            async with self._session.post(
                _GQL_URL,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status != 200:
                    logger.warning("[Twitch] GQL returned HTTP %s", resp.status)
                    return None

                data = await resp.json()
                errors = data.get("errors")
                if errors:
                    logger.warning("[Twitch] GQL errors: %s", errors)
                    return None

                user = (data.get("data") or {}).get("user")
                if not user:
                    logger.warning(
                        "[Twitch] User '%s' not found.", self._username
                    )
                    return None

                return user.get("stream")  # None if offline

        except asyncio.TimeoutError:
            logger.warning("[Twitch] Request timed out.")
            return None
        except Exception as exc:
            logger.error("[Twitch] Error: %s", exc)
            return None
