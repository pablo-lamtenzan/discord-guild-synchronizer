
import aiohttp as aio
from logging import Logger
from typing import TypeVar
from random import choice
from string import digits

from common import (
    DISCORD_API_URL,
)
from http_request import Http

NONCE_LENGHT: int = 20
MSG_INFO_LENGHT = 2

class Message(Http):
    """Represent a Discord message within a channel (which is within a guild)"""
    _Self = TypeVar('_Self', bound='Message')

    def __init__(
            self: _Self,
            client_username: str,
            session: aio.ClientSession,
            header: dict,
            logger: Logger,
            channelId: str,
            username: str,
            displayName: str,
            globalName: str,
            timestamp: str, # TODO: Chnage
            last_edit: str, # TODO Change
            id: str,
            tts: int,
            content: str,
            *,
            true_id: str = None,
            true_username: str = None,
            # nonce: str = None
        ) -> None:
        super().__init__(session, header)
        self._clientUsername = client_username
        self._logger = logger
        self._channelId = channelId
        self._username = username
        self._displayName = displayName
        self._globalName = globalName
        self._timestamp = timestamp
        self._lastEdit = last_edit
        self._id = id
        self._tts = tts
        self._content = content
        self._trueId = true_id
        self._trueUsername = true_username

    @property
    def username(self: _Self) -> str:
        return self._username

    @property
    def displayName(self: _Self) -> str:
        return self._displayName

    @property
    def globalName(self: _Self) -> str:
        return self._globalName

    @property
    def timestamp(self: _Self) -> str:
        return self._timestamp

    @property
    def lastEdit(self: _Self) -> str:
        return self._lastEdit

    @property
    def id(self: _Self) -> str:
        return self._id

    @property
    def content(self: _Self) -> str:
        return self._content

    @property
    def trueId(self: _Self) -> str:
        return self._trueId

    @property
    def trueUsername(self: _Self) -> str:
        return self._trueUsername

    def build_msg(self) -> str:
        return (
            '{' + f'"username": "{self._username}", "display_name": "{self._displayName}", "global_name": "{self._globalName}", "timestamp": "{self._timestamp}", "edited_timestamp": "{self._lastEdit}", "id": "{self._id}"' + '}'
            + f'\n```[{self._timestamp}] {self._username}:```\n{self._content}'
        )

    async def relay(self, channelId: str) -> None:
        nonce = ''.join(choice(digits) for _ in range(NONCE_LENGHT))
        url: str = DISCORD_API_URL + 'channels/' + channelId + '/messages'
        data: dict = {
            'content': self.build_msg(),
            'flags': 0,
            'nonce': nonce,
            'tts': self._tts
        }
        try:
            response: dict = await self.post(url, data)
            self._logger.info(
                "[Message.relay] relay message from author: '%s' (id: '%s', channel: '%s') to channel '%s' (new id: '%s')",
                self._username,
                self._id,
                self._channelId,
                channelId,
                response['id']
            )
        except (
            aio.ClientError,
            aio.http_exceptions.HttpProcessingError
        ) as e:
            self._logger.error(
                "[Message.relay] aiohttp exception for %s [%s]: %s",
                url,
                # Bypass descriptors
                getattr(e, 'status', None),
                getattr(e, 'message', None)
            )

    async def edit(self, content: str, edited_timestamp: str) -> None:
        id: str = self._trueId if self._trueId is not None else self._id
        url: str = DISCORD_API_URL + 'channels/' + self._channelId + f'/messages/{id}'
        self._content = content
        data: dict = {'content': self.build_msg()}
        try:
            await self.patch(url, data=data)
            self._logger.info(
                "[Message.edit] edit message from author: '%s' (id: '%s', channel: '%s')",
                self._username,
                self._id,
                self._channelId,
            )
            self._lastEdit = edited_timestamp
        except (
            aio.ClientError,
            aio.http_exceptions.HttpProcessingError
        ) as e:
            self._logger.error(
                "[Message.edit] aiohttp exception for %s [%s]: %s",
                url,
                # Bypass descriptors
                getattr(e, 'status', None),
                getattr(e, 'message', None)
            )

    async def remove(self) -> None:
        id: str = self._trueId if self._trueId is not None else self._id
        url: str = DISCORD_API_URL + 'channels/' + self._channelId + f'/messages/{id}'
        try:
            await self.delete(url)
            self._logger.info(
                "[Message.remove] remove message from author: '%s' (id: '%s', channel: '%s')",
                self._username,
                self._id,
                self._channelId,
            )
        except (
            aio.ClientError,
            aio.http_exceptions.HttpProcessingError
        ) as e:
            self._logger.error(
                "[Message.remove] aiohttp exception for %s [%s]: %s",
                url,
                # Bypass descriptors
                getattr(e, 'status', None),
                getattr(e, 'message', None)
            )

    def __eq__(self: _Self, other: _Self) -> bool:
        return (
            self._id == other._id
            and self._username == other._username
            and self._timestamp == other._timestamp
        )
    
    def __ne__(self: _Self, other: _Self) -> bool:
        return not self.__eq__(other)
