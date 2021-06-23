"""Main executable of the LOVE-producer."""
import asyncio

from love.producer.events.producer import EventsProducer
from love.producer.base_ws_client import BaseWSClient


class EventsWSClient(BaseWSClient):
    """Handles the websocket client connection between the Telemetries&Events Producer and the LOVE-manager.
    Parameters
    ----------
    heartbeat_callback: function
        Optional callback to be called when receiving a heartbeat event
    remote: salobj.Remote
        Optional remote to read events from
    """

    def __init__(self, csc_list=None, heartbeat_callback=None, remote=None):
        super().__init__(name="Events")

        if csc_list is not None:
            print("CSC list replaced by", csc_list)
            self.csc_list = csc_list

        self.connection_error = False
        self.remote_name = remote.salinfo.name if remote else None

        self.producer = EventsProducer(
            self.domain,
            self.csc_list,
            self.send_message_callback,
            heartbeat_callback=heartbeat_callback,
            remote=remote,
        )

    async def on_start_client(self):
        """ Initializes the websocket client and producer callbacks """
        self.connection_error = False
        await asyncio.gather(
            *[remote.start_task for remote in self.producer.remote_dict.values()]
        )
        await self.producer.setup_callbacks()

    def send_message_callback(self, message):
        """Create a task to send a given message

        Parameters
        ----------
        message: dictionary
            The object to send
        """
        asyncio.create_task(self.send_message(message))

    async def make_and_send_response(self, message):
        """Make the Producer process a given message and send its response

        Parameters
        ----------
        message: dictionary
            The message to process
        """
        answer = await self.producer.process_message(message)
        if answer is None:
            return
        await self.send_message(answer)

    async def on_websocket_receive(self, message):
        """Handle the reception of a new message and distributes to the corresponding function

        Parameters
        ----------
        message: dictionary
            The message received
        """
        if "data" not in message:
            return
        if message["category"] != "initial_state":
            return

        if len(message["data"]) == 0:
            return

        asyncio.create_task(self.make_and_send_response(message))

    async def on_websocket_error(self, e):
        """Set the internal variable connection_error to True when an error ocurrs

        Parameters
        ----------
        e: object
            The error
        """
        self.connection_error = True

    async def on_connected(self):
        """ Executed everytime the connection is made, be it after an error or the first time, etc"""
        await self.producer.send_initial_state_data()


async def main(heartbeat_callback=None, remote=None):
    """Main function, starts the client"""
    telev_client = EventsWSClient(heartbeat_callback=heartbeat_callback, remote=remote)
    await telev_client.start_ws_client()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(main())
    loop.run_forever()
