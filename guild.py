
import aiohttp as aio
from logging import Logger
from typing import (
    TypeVar,
    AsyncGenerator
)

from common import DISCORD_API_URL
from http_request import Http
from channel import Channel

class Guild(Http):
    """Represent a Discord Guild."""
    _Self = TypeVar('_Self', bound='Guild')

    def __init__(
            self: _Self,
            client_username: str,
            session: aio.ClientSession,
            header: dict,
            logger: Logger,
            id: str,
        ) -> None:
        super().__init__(session, header)
        self._clientUsername = client_username
        self._id = id
        self._logger = logger
        self._cachedChannels = []

    @property
    def id(self: _Self) -> str:
        return self._id

    @property
    def cachedChannels(self: _Self) -> list:
        return self._cachedChannels

    async def getChannels(self, *, cache: bool = True) -> AsyncGenerator[Channel, None]:
        if cache is True:
            self._cachedChannels.clear()
        url: str = DISCORD_API_URL + 'guilds/' + self._id + '/channels'
        try:
            channels: dict = self.get(url)

            async for channel in channels:
                chan = Channel(
                    self._clientUsername,
                    self._session,
                    self._header,
                    self._logger,
                    channel['id'],
                    '',#channel['last_message_id'],
                    channel['type'],
                    channel['name'],
                    channel['position'],
                    channel['flags'],
                    channel['parent_id'],
                    '',#channel['topic']
                )
                if cache is True:
                    self._cachedChannels.append(chan)
                self._logger.info(
                    "[Guild.getChannels] get channel: '%s' (id: '%s') from guild '%s'",
                    chan._name,
                    chan._id,
                    self._id
                )
                yield chan
        except (
            aio.ClientError,
            aio.http_exceptions.HttpProcessingError
        ) as e:
            self._logger.error(
                "[Guild.getChannels] aiohttp exception for %s [%s]: %s",
                url,
                # Bypass descriptors
                getattr(e, 'status', None),
                getattr(e, 'message', None)
            )
