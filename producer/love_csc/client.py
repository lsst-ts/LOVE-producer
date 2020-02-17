import asyncio
import json
from lsst.ts import salobj
import os
import utils

from base_ws_client import BaseWSClient
from love_csc.csc import LOVECsc


class LOVEWSClient(BaseWSClient):
    """Handles the websocket client connection between the Telemetries&Events Producer and the LOVE-manager."""

    def __init__(self):
        super().__init__(name='LOVE CSC')
        self.connection_error = False
        self.csc = LOVECsc()

    async def on_start_client(self):
        """ Initializes the websocket client and producer callbacks """
        self.connection_error = False
        await self.csc.start_task

        observingLog_subscribe_msg = {
            'option': 'subscribe',
            'category': 'love_csc',
            'csc': 'love',
            'salindex': '0',
            'stream': 'observingLog'
        }
        await self.send_message(json.dumps(observingLog_subscribe_msg))


    async def on_websocket_receive(self, message):
        if 'category' not in message:
            return
        if message['category'] != 'love_csc':
            return

        if 'data' not in message:
            return
        if len(message['data']) == 0:
            return

        user = utils.get_parameter_from_last_message(message, 'love_csc', 'love', 0, 'observingLog', 'user' )
        log_message = utils.get_parameter_from_last_message(message, 'love_csc', 'love', 0, 'observingLog', 'message' )
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
