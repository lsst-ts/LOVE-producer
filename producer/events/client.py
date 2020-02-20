"""Main executable of the LOVE-producer."""
import asyncio
import json
from lsst.ts import salobj
from events.producer import EventsProducer
import os
import utils

from base_ws_client import BaseWSClient


class EventsWSClient(BaseWSClient):
    """Handles the websocket client connection between the Telemetries&Events Producer and the LOVE-manager."""

    def __init__(self):
        super().__init__(name='Events')
        self.connection_error = False
        self.producer = EventsProducer(self.domain, self.csc_list, self.send_message_callback)

    async def on_start_client(self):
        """ Initializes the websocket client and producer callbacks """
        self.connection_error = False
        self.producer.setup_callbacks()

    def send_message_callback(self, message):
        asyncio.create_task(self.send_message(json.dumps(message)))

    async def on_websocket_receive(self, message):
        if 'data' not in message:
            return
        if len(message['data']) == 0:
            return
        if 'event_name' not in message['data'][0]: 
            return
        answer = await self.producer.process_message(message)
        if answer is None:
            return
        dumped_answer = json.dumps(answer, cls=utils.NumpyEncoder)
        asyncio.create_task(self.send_message(dumped_answer))

    async def on_websocket_error(self, e):
        self.connection_error = True

async def main():
    telev_client = EventsWSClient()
    await telev_client.start_ws_client()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(main())
    loop.run_forever()
