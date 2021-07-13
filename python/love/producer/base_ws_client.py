import os
import json
import aiohttp
import asyncio
import logging
import datetime

from astropy.time import Time
from lsst.ts import salobj

from love.producer.producer_utils import Settings, NumpyEncoder


class BaseWSClient:
    """The base websocket client upon which the clients of all the producers are built."""

    path = os.path.join(os.path.dirname(__file__), Settings.config_path())

    def __init__(self, name):
        self.log = logging.getLogger(__name__)
        self.url = "ws://{}/?password={}".format(Settings.ws_host(), Settings.ws_pass())
        self.domain = salobj.Domain()
        self.name = name
        self.log.info(f"Starting {self.name} Producers @ {self.url}")
        self.csc_list = self.read_config(self.path)
        self.retry = True
        self.websocket = None
        self.heartbeat_task = None
        self.remote_name = None

    async def handle_message_reception(self):
        """Handles the reception of messages from the LOVE-manager,
        and if an initial state is requested it sends the latest seen value in SAL"""
        if self.websocket:
            async for message in self.websocket:
                if message.type == aiohttp.WSMsgType.TEXT:
                    msg = json.loads(message.data)
                    if "category" not in msg:
                        continue
                    await self.on_websocket_receive(msg)

    # DEPRECATED: now heartbeats are handled using SALobj events callbacks
    async def start_heartbeat(self):
        """Sends its heartbeat periodically."""
        while True:
            await self.send_message(
                {
                    "heartbeat": self.name,
                    "timestamp": datetime.datetime.now().timestamp(),
                }
            )
            await asyncio.sleep(3)

    async def start_ws_client(self):
        """Start the websockets client."""
        await self.on_start_client()
        while self.retry:
            try:
                async with aiohttp.ClientSession() as session:
                    self.websocket = await session.ws_connect(self.url)
                    self.log.debug(f"### {self.name} | loaded ws")

                    initial_state_subscribe_msg = {
                        "option": "subscribe",
                        "category": "initial_state",
                        "csc": self.remote_name or "all",
                        "salindex": "all",
                        "stream": "all",
                    }
                    await self.send_message(initial_state_subscribe_msg)
                    self.log.debug(
                        f"### {self.name} | subscribed to initial state of {self.remote_name or 'all'} CSC"
                    )

                    if self.remote_name == "ScriptQueue":
                        initial_state_subscribe_msg = {
                            "option": "subscribe",
                            "category": "initial_state",
                            "csc": "ScriptQueueState",
                            "salindex": "all",
                            "stream": "all",
                        }
                        await self.send_message(initial_state_subscribe_msg)
                        self.log.debug(
                            f"### {self.name} | subscribed to initial state of ScriptQueState CSC"
                        )

                        initial_state_subscribe_msg = {
                            "option": "subscribe",
                            "category": "initial_state",
                            "csc": "Script",
                            "salindex": "all",
                            "stream": "all",
                        }
                        await self.send_message(initial_state_subscribe_msg)
                        self.log.debug(
                            f"### {self.name} | subscribed to initial state of Script CSC"
                        )

                    await self.on_connected()
                    # DEPRECATED: now heartbeats are handled using SALobj events callbacks
                    # self.heartbeat_task = asyncio.create_task(self.start_heartbeat())
                    await self.handle_message_reception()
            except Exception as e:
                self.websocket = None
                self.log.exception(
                    f"[{self.name}]Error attempting to reconnect from start_ws_client."
                )
                if (
                    self.heartbeat_task is not None
                    and not self.heartbeat_task.cancelled()
                ):
                    self.heartbeat_task.cancel()
                    self.heartbeat_task = None
                await self.on_websocket_error(e)
                await asyncio.sleep(3)

    async def send_message(self, message):
        """Send a given message through websockets

        Parameters
        ----------
        message: dict
            The message to send
        """
        if self.websocket:
            if Settings.trace_timestamps():
                snd_time = Time.now().tai.datetime.timestamp()
                message["producer_snd"] = snd_time
            message_str = json.dumps(message, cls=NumpyEncoder)
            try:
                await asyncio.shield(self.websocket.send_str(message_str))
            except Exception:
                self.log.exception("Send Message Exception")
        else:
            self.log.debug(
                f"{self.name} | Unable to send message {message}", flush=True
            )

    async def on_websocket_receive(self, message):
        """ Executed every time a message is received from the LOVE-manager """
        pass

    async def on_start_client(self):
        """ Executed the first time (only) when the client starts, before connecting """
        pass

    async def on_websocket_error(self, e):
        """Handle a websocket error.

        Does nothing for now

        Parameters
        ----------
        e : object
            The error
        """
        pass

    async def on_connected(self):
        """ Executed everytime the connection is made, be it after an error or the first time, etc"""
        pass

    @staticmethod
    def read_config(path, key=None):
        """Reads a given config file and returns the lists of CSCs to listen to.
        It can read the full file (by default), or read only a specific key

        Parameters
        ----------
        path: `string`
            The full path of the config file
        key: `string`
            optional key to read

        Returns
        -------
        csc_list: `[()]`
            The list of CSCs to run as a tuple with the CSC name and index
        """
        with open(path) as config_file:
            data = json.loads(config_file.read())

        csc_list = []
        if key:
            if key not in data:
                return csc_list
            for csc_instance in data[key]:
                index = 0
                if "index" in csc_instance:
                    index = csc_instance["index"]
                csc_list.append((key, index))
        else:
            for csc_key, csc_value in data.items():
                for csc_instance in csc_value:
                    index = 0
                    if "index" in csc_instance:
                        index = csc_instance["index"]
                    csc_list.append((csc_key, index))
        return csc_list
