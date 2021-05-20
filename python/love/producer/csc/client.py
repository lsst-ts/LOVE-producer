"""The client for the CSC Producer."""
import asyncio

from lsst.ts import salobj

from love.producer.events.client import main as events
from love.producer.telemetries.client import main as telemetries
from love.producer.heartbeats.producer import HeartbeatProducer
from love.producer.scriptqueue.client import main as scriptqueue
from love.producer.base_ws_client import BaseWSClient


class CSCWSClient(BaseWSClient):
    """Handles the websocket client connection between the CSC Producer and the LOVE-manager.
    This producer disables the automatic instantiation of new CSCs on the events Producer.

    Parameters
    ----------
    csc_list: List of  (csc, salindex) pairs
    """

    def __init__(self, csc_list=None):
        """Initializes its producer"""
        super().__init__(name="CSCProducer")
        self.events_clients = []
        self.telemetries_clients = []
        self.heartbeats_producers = []
        self.scriptqueue_clients = []

        if csc_list is not None:
            self.log.debug(f"CSC list replaced by {csc_list}.")
            self.csc_list = csc_list

        loop = asyncio.get_event_loop()

        for name, salindex in self.csc_list:
            self.log.debug(
                f"- CSCClient: Listening to events from CSC: {name}, {salindex}"
            )
            remote = salobj.Remote(domain=self.domain, name=name, index=salindex)
            hb_producer = HeartbeatProducer(
                self.domain, self.send_heartbeat, [(name, salindex)], remote=remote
            )
            hb_producer.start()

            def heartbeat_callback(evt):
                hb_producer.set_heartbeat(evt)

            self.events_clients.append(
                loop.create_task(
                    events(heartbeat_callback=heartbeat_callback, remote=remote)
                )
            )
            self.telemetries_clients.append(
                loop.create_task(telemetries(remote=remote))
            )
            self.heartbeats_producers.append(hb_producer)

            if name == "ScriptQueue":
                self.scriptqueue_clients.append(
                    loop.create_task(self.start_scriptqueues())
                )

        self.connection_error = False

    async def start_scriptqueues(self):
        await asyncio.gather(*self.events_clients, scriptqueue())

    async def on_start_client(self):
        """ Initializes producer's callbacks """
        self.connection_error = False

    async def send_heartbeat(self, message):
        """Callback used by the heartbeats producer to send messages with the websocket client

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

    async def close(self):
        """ Cancels running producers tasks """
        for task in self.events_clients:
            task.cancel()
        for task in self.telemetries_clients:
            task.cancel()
        for task in self.scriptqueue_clients:
            task.cancel()
        await self.domain.close()


async def main(csc_list=None):
    """Main function, starts the client"""
    CSC_client = CSCWSClient(csc_list=csc_list)
    await CSC_client.start_ws_client()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(main())
    loop.run_forever()
