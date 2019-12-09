"""Main executable of the LOVE-producer."""
import asyncio
import json
import websockets
from lsst.ts import salobj
from .producer import ScriptQueueProducer
import os
import utils

from base_ws_client import BaseWSClient


class ScriptQueueWSClient(BaseWSClient):
    """Handles the websocket client connection between the ScriptQueue Producer and the LOVE-manager."""

    def __init__(self, salindex):
        super().__init__(name=f'ScriptQueue-{salindex}')
        self.name = f'ScriptQueue-{salindex}'
        self.connection_error = False
        self.salindex = salindex
        self.producer = ScriptQueueProducer(self.domain, self.send_message_callback, self.salindex)

    async def on_start_client(self, websocket):
        """ Initializes the websocket client and producer callbacks """

        self.connection_error = False
        self.websocket = websocket
        await self.producer.setup()
        await self.producer.update()

    def send_message_callback(self, message):
        """Sends messages through websockets. Called after each scriptqueue event """
        asyncio.create_task(self.websocket.send(json.dumps(message)))

    async def on_websocket_receive(self, websocket, message):
        """Handles the reception of messages from the LOVE-manager, and if an initial state is requested it triggers the producer.update() coro"""

        stream_exists = utils.check_stream_from_last_message(
            message, 'initial_state', 'ScriptQueueState', f"{self.salindex}", 'event_name')
        if stream_exists:
            await self.producer.update()

    async def on_websocket_error(self, e):
        self.connection_error = True

async def init_client(salindex):
    sqclient = ScriptQueueWSClient(salindex)
    await sqclient.start_ws_client()


async def main():
    sq_list = BaseWSClient.read_config(BaseWSClient.path, 'ScriptQueue')
    print('List of Script Queues to listen:', sq_list)
    for name, salindex in sq_list:
        asyncio.create_task(init_client(salindex))


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(main())
    loop.run_forever()
