"""Main executable of the LOVE-producer."""
import asyncio
import json
import websockets
from lsst.ts import salobj
from telemetries.producer import TelemetriesProducer
import os
import utils

from base_ws_client import BaseWSClient


class TelemetriesClient(BaseWSClient):
    """Handles the websocket client connection between the Telemetries&Events Producer and the LOVE-manager."""

    def __init__(self):
        super().__init__(name='Telemetries')

        self.producer = TelemetriesProducer(self.domain, self.csc_list)

    async def on_start_client(self):
        """ Initializes the websocket client and producer callbacks """
        asyncio.create_task(self.send_messages_after_timeout())

    async def send_messages_after_timeout(self):
        while True:
            message = self.producer.get_telemetry_message()
            await self.websocket.send(json.dumps(message))
            await asyncio.sleep(2)



async def main():
    telemetry_client = TelemetriesClient()
    await telemetry_client.start_ws_client()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(main())
    loop.run_forever()
