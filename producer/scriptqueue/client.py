"""Main executable of the LOVE-producer."""
import asyncio

from base_ws_client import BaseWSClient
from scriptqueue.producer import ScriptQueueProducer
import producer_utils


class ScriptQueueWSClient(BaseWSClient):
    """Handles the websocket client connection between the ScriptQueue Producer and the LOVE-manager."""

    def __init__(self, salindex, remote=None):
        super().__init__(name=f"ScriptQueue-{salindex}")
        self.name = f"ScriptQueue-{salindex}"
        self.connection_error = False
        self.salindex = salindex
        self.producer = ScriptQueueProducer(
            self.domain, self.send_message_callback, self.salindex, remote
        )

    async def on_start_client(self):
        """Initializes the websocket client and producer callbacks """

        self.connection_error = False
        await self.producer.setup()
        await self.producer.update(showAvailable=True)

    def send_message_callback(self, message):
        """Sends messages through websockets. Called after each scriptqueue event

        Parameters
        ----------
        message: dict
            The message to send
        """
        asyncio.create_task(self.send_message(message))

    async def on_websocket_receive(self, message):
        """Handles the reception of messages from the LOVE-manager,
        and if an initial state is requested it triggers the producer.update() coro

        Parameters
        ----------
        message: dict
            The message
        """

        stream_exists = producer_utils.check_stream_from_last_message(
            message, "initial_state", "ScriptQueueState", self.salindex, "event_name"
        )
        if stream_exists:
            await self.producer.update(showAvailable=False)

    async def on_websocket_error(self, e):
        self.connection_error = True


async def init_client(salindex, remote=None):
    """Initialize the client for a given ScriptQueue SAL index

    Parameters
    ----------
    salindex: int
        The SAL Index of the Script Queue
    """
    sqclient = ScriptQueueWSClient(salindex, remote=remote)
    await sqclient.start_ws_client()


async def main(remote=None):
    """Main function, starts the client."""
    sq_list = BaseWSClient.read_config(BaseWSClient.path, "ScriptQueue")
    print("List of Script Queues to listen:", sq_list)
    for name, salindex in sq_list:
        asyncio.create_task(init_client(salindex, remote=remote))


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(main())
    loop.run_forever()
