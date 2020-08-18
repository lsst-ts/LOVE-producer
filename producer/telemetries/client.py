"""Main executable of the Events Producer."""
import asyncio
from lsst.ts import salobj
from telemetries.producer import TelemetriesProducer
import os
import utils

from base_ws_client import BaseWSClient


class TelemetriesClient(BaseWSClient):
    """Handles the websocket client connection between the Telemetries&Events Producer and the LOVE-manager."""

    def __init__(self, sleepDuration=2, csc_list=None):
        super().__init__(name="Telemetries")

        if csc_list != None:
            self.csc_list = csc_list
            print("CSCs to listen replaced by", csc_list)

        self.producer = TelemetriesProducer(self.domain, self.csc_list)

        self.sleepDuration = sleepDuration

    async def on_start_client(self):
        """ Initializes the websocket client and producer callbacks """
        for remote in self.producer.remote_list:
            await remote.start_task
        asyncio.create_task(self.send_messages_after_timeout())

    async def send_messages_after_timeout(self):
        """Send the telemetries periodically."""
        while True:
            message = self.producer.get_telemetry_message()
            if len(message["data"]) > 0:
                asyncio.create_task(self.send_message(message))
            await asyncio.sleep(self.sleepDuration)


async def main():
    """The main function, starts the Client."""
    telemetry_client = TelemetriesClient()
    await telemetry_client.start_ws_client()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(main())
    loop.run_forever()
