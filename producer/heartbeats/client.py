"""The client for the Heartbeats Producer."""
import asyncio
from lsst.ts import salobj
from .producer import HeartbeatProducer
import os
import utils

from base_ws_client import BaseWSClient


class CSCHeartbeatsWSClient(BaseWSClient):
    """Handles the websocket client connection between the Heartbeats Producer and the LOVE-manager."""

    def __init__(self, remote=None):
        """Initializes its producer

        Parameters
        ----------
        remote: salobj.Remote
            Optional Remote object, when the heartbeat of only one Remote is to be monitored
        """
        super().__init__(name="CSCHeartbeats")

        self.connection_error = False
        self.producer = HeartbeatProducer(
            self.domain, self.send_heartbeat, self.csc_list, remote
        )

    async def on_start_client(self):
        """ Initializes producer's callbacks """
        self.connection_error = False
        self.producer.start()

    async def send_heartbeat(self, message):
        """Callback used by self.producer to send messages with the websocket client

        Parameters
        ----------
        message: dictionmary
            Message to send
        """
        asyncio.create_task(self.send_message(message))

    async def on_websocket_error(self, e):
        """Set the internal variable connection_error to True when an error ocurrs

        Parameters
        ----------
        e: object
            The error
        """
        self.connection_error = True


async def main():
    """Main function, starts the client"""
    heartbeats_client = CSCHeartbeatsWSClient()
    await heartbeats_client.start_ws_client()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(main())
    loop.run_forever()
