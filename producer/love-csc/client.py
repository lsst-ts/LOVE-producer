import asyncio
import json
import websockets
from lsst.ts import salobj
from events.producer import EventsProducer
import os
import utils

from base_ws_client import BaseWSClient
from .csc import LOVECsc


class LOVEWSClient(BaseWSClient):
    """Handles the websocket client connection between the Telemetries&Events Producer and the LOVE-manager."""

    def __init__(self):
        super().__init__(name='Events')
        self.connection_error = False
        self.csc = LOVECsc()

    async def on_start_client(self):
        """ Initializes the websocket client and producer callbacks """
        self.connection_error = False
        await self.csc.start_task

    async def on_websocket_receive(self, message):
        if 'category' not in message:
            return
        if message['category'] != 'love_csc':
            return

        if 'data' not in message:
            return
        if len(message['data']) == 0:
            return

        user = utils.get_parameter_from_last_message(message, 'love_csc', 'love', 0, 'logs', 'user' )
        log_message = utils.get_parameter_from_last_message(message, 'love_csc', 'love', 0, 'logs', 'message' )
        self.csc.add_observing_log(user, log_message)

    async def on_websocket_error(self, e):
        self.connection_error = True

async def main():
    telev_client = LOVEWSClient()
    await telev_client.start_ws_client()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(main())
    loop.run_forever()
