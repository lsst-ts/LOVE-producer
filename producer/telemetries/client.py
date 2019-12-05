"""Main executable of the LOVE-producer."""
import asyncio
import json
import websockets
from lsst.ts import salobj
from telemetries import TelemetryProducer
import os
import utils

from base_ws_client import BaseWSClient


class TelemetryEventsWSClient(BaseWSClient):
    """Handles the websocket client connection between the Telemetries&Events Producer and the LOVE-manager."""

    def __init__(self):
        super().__init__(name='Telemetry&Events')

        self.producer = TelemetryProducer(self.domain, self.csc_list, self.send_message_callback)

    async def on_start_client(self):
        """ Initializes the websocket client and producer callbacks """
        asyncio.create_task(self.send_messages_after_timeout())

    async def send_messages_after_timeout(self):
        while True:
            message = self.producer.get_telemetry_message()
            await self.websocket.send(json.dumps(message))
            await asyncio.sleep(2)

    async def process_one_message(self, message):
        if 'data' not in message:
            return
        if len(message['data']) == 0:
            return

        answer = await self.producer.process_message(message)
        if answer is None:
            return
        dumped_answer = json.dumps(answer, cls=utils.NumpyEncoder)
        asyncio.create_task(self.websocket.send(dumped_answer))


async def main():
    telemetry_client = TelemetryEventsWSClient()
    await telemetry_client.start_ws_client()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(main())
    loop.run_forever()
