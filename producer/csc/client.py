"""The client for the CSC Producer."""
import asyncio
from lsst.ts import salobj
from events.client import main as events
from telemetries.client import main as telemetries
from heartbeats.client import main as heartbeats
from scriptqueue.client import main as scriptqueue

import os
import utils

from base_ws_client import BaseWSClient


class CSCWSClient(BaseWSClient):
    """Handles the websocket client connection between the CSC Producer and the LOVE-manager."""

    def __init__(self, csc_list=None):
        """Initializes its producer
        """
        super().__init__(name="CSCProducer")
        self.events_clients = []
        self.telemetries_clients = []
        self.heartbeats_clients = []
        self.scriptqueue_clients = []
        domain = salobj.Domain()
        if csc_list is not None:
            print("CSC list replaced by", csc_list)
            self.csc_list = csc_list

        loop = asyncio.get_event_loop()

        for name, salindex in self.csc_list:
            print("- CSCClient: Listening to events from CSC: ", (name, salindex))
            remote = salobj.Remote(domain=domain, name=name, index=salindex)
            self.events_clients.append(loop.create_task(events(remote=remote)))
            self.telemetries_clients.append(loop.create_task(telemetries(remote=remote)))
            self.heartbeats_clients.append(loop.create_task(heartbeats(remote=remote)))
            if name == "ScriptQueue":
                self.scriptqueue_clients.append(loop.create_task(scriptqueue(remote=remote)))

        self.connection_error = False


    async def on_start_client(self):
        """ Initializes producer's callbacks """
        self.connection_error = False

    async def on_websocket_error(self, e):
        """ Set the internal variable connection_error to True when an error ocurrs

        Parameters
        ----------
        e: object
            The error
        """
        self.connection_error = True

    def close(self):
        """ Cancels running producers tasks """
        for task in self.events_clients:
            task.cancel()
        for task in self.telemetries_clients:
            task.cancel()
        for task in self.heartbeats_clients:
            task.cancel()
        for task in self.scriptqueue_clients:
            task.cancel()

async def main(csc_list=None):
    """Main function, starts the client"""
    CSC_client = CSCWSClient(csc_list=csc_list)
    await CSC_client.start_ws_client()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(main())
    loop.run_forever()
