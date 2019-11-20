"""Main executable of the LOVE-producer."""
import asyncio
import json
import websockets
from lsst.ts import salobj
from .receiver import Receiver
import os
import utils

from base_ws_client import BaseWSClient


class CommandWSClient(BaseWSClient):
    """Handles the websocket client connection between the Commands Receiver and the LOVE-manager."""

    def __init__(self):
        super().__init__(name='CommandsReceiver')
        self.receiver = Receiver(self.domain, self.csc_list)
    async def on_start_client(self):
        cmd_subscribe_msg = {
            'option': 'subscribe',
            'category': 'cmd',
            'csc': 'all',
            'salindex': 'all',
            'stream': 'all'
        }
        await self.websocket.send(json.dumps(cmd_subscribe_msg))

    async def process_one_message(self, message):
        """Handles the reception of messages from the LOVE-manager, and if an initial state is requested it triggers the producer.update() coro"""
        answer = await self.receiver.process_message(message)
        if answer is None:
            return
        dumped_answer = json.dumps(answer, cls=utils.NumpyEncoder)
        await self.websocket.send(dumped_answer)


async def main():
    commands_client = CommandWSClient()
    await commands_client.start_ws_client()

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(main())
    loop.run_forever()
