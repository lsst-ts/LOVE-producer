# This file is part of LOVE-producer.
#
# Developed for Vera C. Rubin Observatory Telescope and Site Systems.
# This product includes software developed by the LSST Project
# (https://www.lsst.org).
# See the COPYRIGHT file at the top-level directory of this distribution
# for details of code ownership.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import os
import json
import aiohttp
import asyncio
import logging
import textwrap

from typing import Optional

from love.producer import LoveProducerFactory
from .producer_utils import ConnectedTaskDoneError


class LoveManagerClient:
    """Provides connectivity between the LOVE manager and the producer."""

    def __init__(self, log) -> None:

        self.log: logging.Logger = log.getChild(type(self).__name__)

        self.connection_failed_wait_time: float = 3.0

        self.text_width_max = 110

        self.websocket: Optional[aiohttp.ClientWebSocketResponse] = None

        self.connected_task: Optional[asyncio.Future] = None
        self.done_task: Optional[asyncio.Future] = None

        self.producers: list = []

        self._send_message_lock = asyncio.Lock()

    async def handle_connection_with_manager(self) -> None:
        """Keep connection to manager alive and handle incomming requests.
        If connection is closed try to reconnect until process is stopped.
        """

        async for i in self.connect_to_manager():
            self.log.debug(f"Connected after {i} attempts.")
            await self.handle_connected()

    async def connect_to_manager(self) -> None:
        """An async generator that will try to connect to the LOVE manager as
        long as `done_task` is not set.

        Yields
        ------
        connection_attempt: `int`
            How many attempts to connect where mande before succeeding.


        Notes
        -----

        One way to use this async generator is in an `async for` loop.

        See Also
        --------
        handle_connection_with_manager: Connects to manager and handler
            connection.
        """

        self.reset_tasks()

        connection_attempt = 0

        while not self.done_task.done():

            try:
                async with aiohttp.ClientSession() as session:
                    self.websocket = await session.ws_connect(self.url)

                    if self.connected_task.done():
                        raise ConnectedTaskDoneError(
                            "Connected task unexpectedly done."
                        )
                    else:
                        self.connected_task.set_result(True)

                        yield connection_attempt

                        connection_attempt = 0
            except (
                aiohttp.client_exceptions.ClientConnectorError,
                aiohttp.client_exceptions.WSServerHandshakeError,
            ):
                connection_attempt += 1
                self.log.debug(
                    f"Could not connect to manager. Attempt {connection_attempt}. "
                    f"Waiting {self.connection_failed_wait_time} seconds before next attempt."
                )
                await self.handle_wait_retry()
            except ConnectedTaskDoneError:
                connection_attempt = 0
                self.log.debug(
                    "Connection with managed unexpectedly closed. "
                    f"Waiting {self.connection_failed_wait_time} seconds before trying to connect again."
                )
                await self.handle_wait_retry()

    async def handle_wait_retry(self) -> None:
        """Handle retrying to connect to manager."""
        if self.connected_task.done():
            self.connected_task = asyncio.Future()

        await asyncio.sleep(self.connection_failed_wait_time)

    def reset_tasks(self) -> None:
        """Reset both the `connected_task` and `done_task` futures.

        These `asyncio.Future` are used to determine if the client is connected
        to the manager and until when the client should run.

        See Also
        --------
        connect_to_manager: Async generator to connect to manager.
        """
        self.connected_task = asyncio.Future()
        self.done_task = asyncio.Future()

    async def handle_connected(self) -> None:
        """Handle a recently established connection with the LOVE manager."""
        await self._register_producers()
        await self._send_initial_data()
        await self._handle_message_reception()

    async def _register_producers(self) -> None:
        """Register producers with the manager."""

        for producer in self.producers:
            self.log.debug(f"Registering {producer.component_name} producer.")

            async for initial_state_message in producer.get_initial_state_messages_as_json():
                await self.send_message(initial_state_message)

    async def _send_initial_data(self) -> None:
        """Send initial data from producers"""

        for producer in self.producers:
            self.log.debug(
                f"Sending initial data for {producer.component_name} producer."
            )
            await producer.send_initial_data()

    async def _handle_message_reception(self) -> None:
        """Handle message reception from LOVE manager.

        Raises
        ------
        RuntimeError
            If websocket is not initialized with `connect_to_manager`.
        """
        if self.websocket is not None:
            self.log.debug("Start handling message reception...")

            async for message in self.websocket:
                message_data = self.parse_websocket_message(message)
                await self.handle_producers_reply_to_server(message_data)

        else:
            raise RuntimeError(
                "No connection to manager. Run connect_to_manager before running handle_message_reception."
            )

    def parse_websocket_message(self, websocket_message: str) -> dict:
        """Parse input json message string to dictionary if message is of
        type `aiohttp.WSMsgType.TEXT`, if not return empty dictionary.

        Parameters
        ----------
        websocket_message: `str`
            Input json string.

        Returns
        -------
        `dict`
            Resulting dictionary from parsing json string.
        """
        return (
            json.loads(websocket_message.data)
            if websocket_message.type == aiohttp.WSMsgType.TEXT
            else dict()
        )

    async def handle_producers_reply_to_server(self, message_data: dict) -> None:
        """Given the input message data, handle any reply needed from the
        producers to the server.

        Parameters
        ----------
        message_data: `dict`
            Data payload from the message received from the server.
        """

        self.log.debug(f"Received message from server: {message_data}")

        if self.need_reply_from_producers(message_data):
            await asyncio.gather(
                *[
                    producer.reply_to_message_data(message_data)
                    for producer in self.producers
                ]
            )
        else:
            self.log.debug("No reply from producers needed.")

    def need_reply_from_producers(self, message_data: dict) -> bool:
        """Determine if input message_data from the server requires a reply
        from the producers.

        Parameters
        ----------
        message_data: `dict`
            Data from the server to process.

        Returns
        -------
        `bool`
            Does the data need a reply?
        """

        return ("category" in message_data) and (
            message_data["category"] == "initial_state"
        )

    def create_producers(self, components: list, **kwargs) -> None:

        for component in components:
            producer = LoveProducerFactory.get_love_producer_from_name(
                component,
                **kwargs,
            )
            producer.send_message = self.send_message
            self.producers.append(producer)

    async def send_message(self, message: str) -> None:
        """Send a given message through websockets

        Parameters
        ----------
        message: `str`
            JSON string to send to manager.
        """
        if self.websocket:
            try:
                self.log.debug(
                    f"send_message: {textwrap.shorten(message, width=self.text_width_max)}"
                )
                async with self._send_message_lock:
                    await asyncio.shield(self.websocket.send_str(message))
            except Exception:
                self.log.exception("Error sending message to manager.")
        else:
            self.log.warning(
                "No connection to manager. Run connect_to_manager before send_message."
            )

    async def close(self):

        for producer in self.producers:
            await producer.close()

        if self.done_task is not None and not self.done_task.done():
            self.done_task.set_result(True)

        if self.websocket is not None:
            await self.websocket.close()

    @property
    def manager_hostname(self) -> str:
        return os.environ.get("WEBSOCKET_HOST", None)

    @property
    def manager_password(self) -> str:
        return os.environ.get("PROCESS_CONNECTION_PASS", "")

    @property
    def url(self) -> str:
        if self.manager_hostname is None:
            raise RuntimeError("Manager hostname not set.")
        return f"ws://{self.manager_hostname}/?password={self.manager_password}"
