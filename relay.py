#!/usr/bin/python3

import sys
import os
import dotenv
import aiohttp as aio
import asyncio
import yaml
from pathlib import Path
from logging import (
    Logger,
    config,
    getLogger
)

from guild import Guild

LOGGER_NAME: str = 'relay-discord-logger'
LOGGER_CONFIG_FILE: str = 'logger_config.yml'
CURRENT_DIR: Path = Path(__file__).parent

#TODO: Handle time in output
#TODO: Docstrings
#TODO: Threads
#TODO: Reactions

def displayUsage(name):
    print(f'usage: {name} <guild_one_id> <guild_two_id>')

async def main(client_username: str, logger: Logger, header):
    async with aio.ClientSession() as session:
        # Testing
        guildOne = Guild(client_username, session, header, logger, sys.argv[1])
        guildTwo = Guild(client_username, session, header, logger, sys.argv[2])
        ch1 = None
        ch2 = None
        async for chan in guildOne.getChannels():
            if chan._id == '1101868648349577276':
                ch1 = chan
            elif chan._id == '1101871626007621743':
                ch2 = chan
        if ch1 is not None and ch2 is not None:
            await ch1.sync(ch2)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        displayUsage(sys.argv[0])
    else:
        # Set up environment dependencies
        dotenv.load_dotenv()
        auth: str = os.getenv('AUTH_TOKEN')
        if auth is None:
            raise KeyError('Missing .env file or AUTH_TOKEN environment variable from .env file')
        _clientUsername: str = os.getenv('CLIENT_USERNAME')
        if _clientUsername is None:
            raise KeyError('Missing CLIENT_USERNAME environment variable from .env file')
        # Set up logger
        with open(CURRENT_DIR.joinpath(LOGGER_CONFIG_FILE), 'r') as logConf:
            yml = yaml.safe_load(logConf.read())
            config.dictConfig(yml)
        # Set up event loop
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main(_clientUsername, getLogger(LOGGER_NAME), header={'authorization': auth}))
