# This file is part of ts_salobj.
#
# Developed for Inria Chile and the Rubin Observatory Telescope
# and Site System.
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
import asyncio
import logging
import unittest
import contextlib
import websockets


from love.producer import LoveManagerClient, LoveManagerMessage
from love.producer.test_utils import cancel_task


class TestLoveManagerClient(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        cls.log = logging.getLogger(__name__)
        cls.standard_timeout = 5.0
        cls.pool_timeout = 0.1

    def setUp(self):
        self.love_manager_client = LoveManagerClient(self.log)
        self.love_manager_message = LoveManagerMessage("UnitTest")
        self.received_data = dict()

        self.sample_summary_state = dict(summaryState=4)

    async def asyncTearDown(self):
        await self.love_manager_client.close()

    async def test_url(self):
        async with self.configure_environment_with_websocket_host():
            self.assertIsInstance(self.love_manager_client.url, str)

    def test_url_no_manager_hostname(self):
        back_up_websocket_host = (
            os.environ.pop("WEBSOCKET_HOST") if "WEBSOCKET_HOST" in os.environ else None
        )

        try:
            with self.assertRaises(RuntimeError):
                self.love_manager_client.url
        finally:
            if back_up_websocket_host is not None:
                os.environ["WEBSOCKET_HOST"] = back_up_websocket_host

    async def test_create_producers(self):
        components = self.create_producers()

        self.assertEqual(len(components), len(self.love_manager_client.producers))

        for component, producer in zip(components, self.love_manager_client.producers):
            self.assertEqual(component, producer.component_name)

    async def test_handle_connection_with_manager_no_producers(self):
        """Base connectivity test.

        This test verify that when the manager client connects with server,
        the connected_task result is True and `done_task` is not done, meaning,
        the manager is running.

        Since this is a basic conectivity test, there's no reason to create
        producers.
        """

        async with self.setup_test_environment_to_handle_connection():
            self.assertTrue(self.love_manager_client.connected_task.result())
            self.assertFalse(self.love_manager_client.done_task.done())

    async def test_handle_connection_with_manager_with_producers(self):
        components = self.create_producers()

        async with self.setup_test_environment_to_handle_connection():
            self.assert_initial_state_subscribe_messages_sent(components)

    async def test_send_message(self):
        async with self.setup_test_environment_to_handle_connection():
            data = dict(
                name="test_data",
                test_value_int=10,
                test_value_string="test",
                test_value_float=1.0 / 3.0,
            )
            message = self.love_manager_message.get_message_category_as_json(
                category="telemetry", data=data
            )

            await self.love_manager_client.send_message(message)

            self.log.debug("Waiting for server to process the message.")
            await asyncio.sleep(self.standard_timeout)

            self.log.debug(f"{self.received_data}")

            self.assertEqual(len(self.received_data["telemetry"]), 1)
            self.assertEqual(data, self.received_data["telemetry"][0])

    async def test_handle_message_reception(self):
        components = self.create_producers()

        self.add_summary_state_samples()

        async with self.setup_test_environment_to_handle_connection():
            await asyncio.sleep(1.0)

            self.purge_received_data()

            self.log.debug("Request summary state from samples.")

            await self.websocket.send(
                json.dumps(self.get_sample_message_data_from_manager("UnitTest1", 0))
            )

            await self.websocket.send(
                json.dumps(self.get_sample_message_data_from_manager("UnitTest2", 0))
            )

            await self.wait_for_number_of_samples(len(components))

            self.assertEqual(len(components), len(self.received_data["event"]))

    def test_need_reply_from_producers(self):
        self.assertFalse(self.love_manager_client.need_reply_from_producers(dict()))

        self.assertFalse(
            self.love_manager_client.need_reply_from_producers(dict(category=""))
        )

        self.assertFalse(
            self.love_manager_client.need_reply_from_producers(dict(category="foobar"))
        )

        self.assertTrue(
            self.love_manager_client.need_reply_from_producers(
                dict(category="initial_state")
            )
        )

    def create_producers(self):
        components = ["UnitTest1", "UnitTest2"]

        self.love_manager_client.create_producers(components=components)

        return components

    def get_sample_message_data_from_manager(self, csc, salindex):
        return dict(
            category="initial_state",
            data=[
                {
                    "csc": csc,
                    "salindex": salindex,
                    "stream": {"event_name": "summaryState"},
                }
            ],
        )

    def add_summary_state_samples(self):
        for producer in self.love_manager_client.producers:
            producer.store_samples(summaryState=self.sample_summary_state)

    def assert_initial_state_subscribe_messages_sent(self, components):
        initial_state_messages = self.gather_initial_state_messages()

        for component in components:
            self.assertIn(component, initial_state_messages)

    def gather_initial_state_messages(self):
        return {
            initial_state_message["csc"]
            for initial_state_message in self.received_data.get("initial_state", [])
        }

    def purge_received_data(self):
        self.received_data = dict()

    async def wait_for_number_of_samples(self, number_of_samples, sample_type="event"):
        self.log.debug(
            f"Waiting for {number_of_samples} samples or {self.standard_timeout} seconds, "
            "whatever comes first."
        )

        test_timeout_task = asyncio.create_task(asyncio.sleep(self.standard_timeout))

        while (not test_timeout_task.done()) and (
            len(self.received_data.get(sample_type, [])) < number_of_samples
        ):
            await asyncio.sleep(self.pool_timeout)

        await cancel_task(test_timeout_task)

        self.log.debug(
            f"Done waiting for {number_of_samples} samples. "
            f"Got {len(self.received_data.get(sample_type, []))}."
        )

    @contextlib.asynccontextmanager
    async def setup_test_environment_to_handle_connection(self):
        async with self.configure_environment_with_websocket_host():
            async with self.start_mock_manager() as socket:
                async with self.handle_connection_with_manager():
                    yield socket

    @contextlib.asynccontextmanager
    async def configure_environment_with_websocket_host(self):
        back_up_websocket_host = (
            os.environ.pop("WEBSOCKET_HOST") if "WEBSOCKET_HOST" in os.environ else None
        )

        os.environ["WEBSOCKET_HOST"] = "0.0.0.0:9999"

        try:
            yield
        finally:
            if back_up_websocket_host is not None:
                os.environ["WEBSOCKET_HOST"] = back_up_websocket_host
            else:
                os.environ.pop("WEBSOCKET_HOST")

    @contextlib.asynccontextmanager
    async def start_mock_manager(self):
        self._run_wesocket_server = True

        socket = websockets.serve(
            ws_handler=self.handle_websocket_server_received_message,
            host="0.0.0.0",
            port=9999,
        )

        try:
            await socket
            yield socket
        finally:
            self.log.info("Closing web server")
            self._run_wesocket_server = False
            socket.ws_server.close()

    @contextlib.asynccontextmanager
    async def handle_connection_with_manager(self):
        try:
            start_task = asyncio.create_task(
                self.love_manager_client.handle_connection_with_manager()
            )

            while self.love_manager_client.connected_task is None:
                await asyncio.sleep(self.pool_timeout)

            await asyncio.wait_for(
                self.love_manager_client.connected_task,
                timeout=self.standard_timeout,
            )

            yield

        finally:
            await self.love_manager_client.close()
            await asyncio.wait_for(start_task, timeout=self.standard_timeout)

    async def handle_websocket_server_received_message(
        self, websocket, *args, **kwargs
    ):
        self.websocket = websocket

        try:
            async for message in websocket:
                data_message = json.loads(message)
                data_category = data_message["category"]

                if data_category not in self.received_data:
                    self.log.debug(
                        f"Creating entry for '{data_category}' in received data dictionary."
                    )
                    self.received_data[data_category] = []

                self.log.debug(f"Appending {data_message} to {data_category}")
                self.received_data[data_category].append(
                    data_message["data"][0] if "data" in data_message else data_message
                )
        except websockets.exceptions.ConnectionClosedError:
            self.log.debug("Connection closed.")


if __name__ == "__main__":
    unittest.main()
