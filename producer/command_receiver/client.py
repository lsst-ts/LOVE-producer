"""Main executable of the LOVE-producer."""
import asyncio
import json
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
        self.should_subscribe = True

    def send_subscription_msg(self):
        cmd_subscribe_msg = {
            'option': 'subscribe',
            'category': 'cmd',
            'csc': 'all',
            'salindex': 'all',
            'stream': 'all'
        }
        asyncio.create_task(self.send_message(json.dumps(cmd_subscribe_msg)))

    async def on_start_client(self):
        self.send_subscription_msg()
        self.should_subscribe = False

    async def on_websocket_receive(self, message):
        if self.should_subscribe:
            self.send_subscription_msg()
            self.should_subscribe = False
        """Handles the reception of messages from the LOVE-manager, and if an initial state is requested it triggers the producer.update() coro"""
        answer = await self.receiver.on_message(message)
        if answer is None:
            return
        dumped_answer = json.dumps(answer, cls=utils.NumpyEncoder)
        asyncio.create_task(self.send_message(dumped_answer))

    async def on_websocket_error(self, e):
        print("CMD CLIENT ERROR", e, flush=True)
        self.should_subscribe = True

async def main():
    commands_client = CommandWSClient()
    await commands_client.start_ws_client()

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(main())
    loop.run_forever()
