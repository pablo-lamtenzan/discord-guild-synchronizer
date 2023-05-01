
import aiohttp as aio
import asyncio
from typing import (
    TypeVar,
    AsyncGenerator
    )

class Http:
    """"""
    _Self = TypeVar('_Self', bound='Http')

    def __init__(self: _Self, session: aio.ClientSession, header: dict) -> None:
        self._session = session
        self._header = header

    async def get(self: _Self, url: str) -> AsyncGenerator[dict, None]:
        async with self._session.get(url, headers=self._header) as response:
            response.raise_for_status()
            res = await response.json()
            for elem in res:
                yield elem
                await asyncio.sleep(0) # switch task in event loop

    async def post(self: _Self, url: str, data: dict) -> dict:
        async with self._session.post(url, data=data, headers=self._header) as response:
            response.raise_for_status()
            return await response.json()

    async def patch(self: _Self, url: str, data: dict) -> dict:
        async with self._session.patch(url, data=data, headers=self._header) as response:
            response.raise_for_status()
            return await response.json()

    async def delete(self: _Self, url: str) -> dict:
        async with self._session.delete(url, headers=self._header) as response:
            response.raise_for_status()
