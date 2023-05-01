
import json
import aiohttp as aio
from logging import Logger
from typing import (
    TypeVar,
    AsyncGenerator
)

from message import (
    Message,
    MSG_INFO_LENGHT
)
from common import DISCORD_API_URL
from http_request import Http

class Channel(Http):
    """Represent a Discord channel within a guild."""
    _Self = TypeVar('_Self', bound='Channel')

    def __init__(
            self: _Self,
            client_username: str,
            session: aio.ClientSession,
            header: dict,
            logger: Logger,
            id: str,
            lastMessageId: str,
            type: int,
            name: str,
            position: int,
            flags: int,
            parentId: str,
            topic: str,
        ) -> None:
        super().__init__(session, header)
        self._clientUsername = client_username
        self._logger = logger
        self._id = id
        self._lastMessageId = lastMessageId
        self._type = type
        self._name = name
        self._position = position
        self._flags = flags
        self._parentId = parentId
        self._topic = topic
        self._cachedMessages = []

    @property
    def id(self: _Self) -> str:
        return self._id

    @property
    def name(self: _Self) -> str:
        return self._name

    @property
    def cachedMessages(self: _Self) -> list:
        return self._cachedMessages
    
    def clearCache(self: _Self) -> None:
        self.cachedMessages.clear()

    @staticmethod
    def validate_metadata(metadataStr: str) -> dict:
        valid_keys = ('username', 'display_name', 'global_name', 'timestamp', 'edited_timestamp', 'id')
        metadata = {}
        try:
            res = json.loads(metadataStr)
            if isinstance(res, dict):
                metadata.update(res)
        except Exception:
            pass
        for k1, k2, v in zip(valid_keys, metadata.keys(), metadata.values()):
            if v == 'None':
                v = None
            if k1 != k2:
                metadata.clear()
                break
        return metadata

    async def getMessages(self, *, amount: int = 100, cache: bool = True) -> AsyncGenerator[Message, None]:
        if cache is True:
            self.cachedMessages.clear()
        url: str = DISCORD_API_URL + 'channels/' + self._id + f'/messages?limit={amount}'
        try:
            messages: dict = self.get(url)
            async for msg in messages:
                author = msg['author']
                metadata = self.validate_metadata(str(msg['content']).splitlines()[0])
                if len(metadata) == 0:
                    m = Message(
                        self._clientUsername,
                        self._session,
                        self._header,
                        self._logger,
                        self._id,
                        author['username'],
                        author['display_name'],
                        author['global_name'],
                        msg['timestamp'],
                        msg['edited_timestamp'],
                        msg['id'],
                        msg['tts'],
                        msg['content']
                    )
                    print('1:', m._id)
                else:
                    m = Message(
                        self._clientUsername,
                        self._session,
                        self._header,
                        self._logger,
                        self._id,
                        metadata['username'],
                        metadata['display_name'],
                        metadata['global_name'],
                        metadata['timestamp'],
                        metadata['edited_timestamp'],
                        metadata['id'],
                        msg['tts'],
                        msg['content'],
                        true_id=msg['id'],
                        true_username=author['username'],
                    )
                    print('2:', m._id)
                if cache is True:
                    self.cachedMessages.append(m)
                self._logger.info(
                    "[Channel.getMessages] get message from author: '%s' (id: '%s', channel: '%s')",
                    m._username,
                    m._id,
                    m._channelId
                )
                yield m
        except (
            aio.ClientError,
            aio.http_exceptions.HttpProcessingError
        ) as e:
            self._logger.error(
                "[Channel.getMessages] aiohttp exception for %s [%s]: %s",
                url,
                # Bypass descriptors
                getattr(e, 'status', None),
                getattr(e, 'message', None)
            )

    async def sync(self: _Self, channel: _Self) -> None:
        msgs_other_list: list[Message] = [msg async for msg in channel.getMessages(cache=False)]
        msgs_self: AsyncGenerator[Message, None] = self.getMessages()
        async for msg_self in msgs_self:
            found: bool = False
            for msg_other in msgs_other_list:
                if msg_self == msg_other:
                    found = True
                    break
            # If relayed is message not present in other channel remove it
            metadata = self.validate_metadata(msg_self._content.splitlines()[0])
            if found is False and len(metadata) > 0 and msg_self._trueUsername == self._clientUsername:
                await msg_self.remove()

        # While the async generators are consumed, data is cached
        cache_msgs_self: list[Message] = self._cachedMessages
        # Messages are received from newer to older, we need older to newer
        cache_msgs_self.reverse()
        msgs_other_list.reverse()
        for msg_other in msgs_other_list:
            found: bool = False
            for msg_self in cache_msgs_self:
                if msg_self == msg_other and msg_self._trueUsername == self._clientUsername:
                    # Edit message if content differs
                    content = msg_self._content.splitlines(keepends=True)
                    if len(content) <= MSG_INFO_LENGHT:
                        pass # TODO: must never happen
                    if msg_other._content != ''.join(content[MSG_INFO_LENGHT:]):
                        await msg_self.edit(msg_other._content, msg_other._lastEdit)
                    found = True
                    break
            # Relay message if not present in self channel
            if found is False:
                await msg_other.relay(self._id)
        channel.clearCache()
