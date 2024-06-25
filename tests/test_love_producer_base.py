# This file is part of LOVE-producer.
#
# Developed for the Rubin Observatory Telescope and Site System.
# This product includes software developed by Inria Chile and
# the LSST Project (https://www.lsst.org).
#
# See the COPYRIGHT file at the top-level directory of this distribution
# for details of code ownership and dependencies.
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

import asyncio
import json
import logging
import unittest

import numpy as np
from astropy.time import Time
from love.producer import LoveProducerBase
from love.producer.test_utils import cancel_task


class TestLoveProducerBase(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        cls.log = logging.getLogger(__name__)
        cls.standard_timeout = 5
        cls.time_pooling = 0.1

    async def asyncSetUp(self):
        self.producer = LoveProducerBase()
        self.messages_received = []
        self._run_data_generator_loop = False
        self.data_generator_task = asyncio.Future()
        self.data_generator_task.set_result(True)
        self.generate_async_data_callback = None
        self.sample_message_data_from_manager = dict(
            category="initial_state",
            data=[
                {"csc": "Test", "salindex": 1, "stream": {"event_name": "summaryState"}}
            ],
        )
        self.sample_summary_state = dict(summaryState=4)

    async def asyncTearDown(self):
        self.stop_data_generation_loop()
        try:
            await asyncio.wait_for(
                self.data_generator_task, timeout=self.standard_timeout
            )
        except asyncio.TimeoutError:
            self.log.debug(
                "Timeout waiting for data generator task to complete. Cancelling it."
            )
            await cancel_task(self.data_generator_task)
        except asyncio.CancelledError:
            pass

    def test_get_message_initial_state_as_json_no_component_name(self):
        with self.assertRaises(AssertionError):
            self.producer.get_message_initial_state_as_json()

    def test_get_message_initial_state_as_json(self):
        component_name = "Test"

        self.producer.component_name = component_name

        initial_state_subscribe_msg = json.loads(
            self.producer.get_message_initial_state_as_json()
        )

        for key, value in [
            ("option", "subscribe"),
            ("category", "initial_state"),
            ("csc", component_name),
            ("salindex", "all"),
            ("stream", "all"),
        ]:
            self.assertIn(key, initial_state_subscribe_msg)
            self.assertEqual(initial_state_subscribe_msg[key], value)

    def test_add_metadata(self):
        self.setup_for_data_handling_test(component_index=1)

        message = self.producer.get_message_category_as_json(
            category="telemetry", data_as_dict=dict()
        )

        data_as_dict = json.loads(message)

        self.assertIn("component_index", data_as_dict)
        self.assertEqual(data_as_dict["component_index"], 1)

    async def test_register_monitor_data_periodically_with_function(self):
        self.setup_for_data_handling_test()

        self.producer.register_monitor_data_periodically(
            self.get_random_data, "telemetry"
        )

        await self.assert_monitored_data("get_random_data", 2)

    async def test_register_monitor_data_periodically_fail_component_not_set(self):
        with self.assertRaises(AssertionError):
            self.producer.register_monitor_data_periodically(
                self.async_get_random_data, "telemetry"
            )

    async def test_register_monitor_data_periodically_with_coroutine(self):
        self.setup_for_data_handling_test()

        self.producer.register_monitor_data_periodically(
            self.async_get_random_data, "telemetry"
        )

        await self.assert_monitored_data("async_get_random_data", 2)

    async def test_handle_asynchronous_data_callback(self):
        self.setup_for_data_handling_test()

        self.setup_data_generation_loop()

        self.generate_async_data_callback = (
            self.producer.handle_asynchronous_data_callback
        )

        await self.assert_monitored_data("async_get_random_data_randomly", 3)

    async def test_register_additional_action(self):
        self.setup_for_data_handling_test()

        self.setup_data_generation_loop()

        self.producer.register_additional_action(
            "async_get_random_data_randomly", unittest.mock.AsyncMock()
        )
        self.producer.register_additional_action("none", unittest.mock.AsyncMock())

        self.generate_async_data_callback = (
            self.producer.handle_asynchronous_data_callback
        )

        await self.assert_monitored_data("async_get_random_data_randomly", 3)

        self.producer._additional_data_callbacks[
            "async_get_random_data_randomly"
        ].assert_awaited()
        self.producer._additional_data_callbacks["none"].assert_not_awaited()

    def test_send_message_not_set(self):
        with self.assertRaises(RuntimeError):
            self.producer.send_message("test")

    def test_send_message_set_bad_type_int(self):
        with self.assertRaises(TypeError):
            self.producer.send_message = 1

    def test_send_message_set_bad_type_string(self):
        with self.assertRaises(TypeError):
            self.producer.send_message = "test"

    def test_send_message_set_bad_type_function(self):
        with self.assertRaises(TypeError):
            self.producer.send_message = self.send_message

    async def test_send_message_set_as_coroutine(self):
        self.producer.send_message = self.async_send_message

        await self.producer.send_message("test")

        self.assertIn("test", self.messages_received)

    async def test_should_reply_to_message_data(self):
        self.setup_for_data_handling_test(salindex=1)

        self.producer.store_samples(summaryState=self.sample_summary_state)

        self.assertTrue(
            self.producer.should_reply_to_message_data(
                self.sample_message_data_from_manager
            )
        )

    async def test_should_reply_to_message_data_no_reply_different_csc(self):
        self.setup_for_data_handling_test(salindex=1)

        self.producer.store_samples(summaryState=self.sample_summary_state)

        sample_message_data_from_manager = self.sample_message_data_from_manager.copy()

        sample_message_data_from_manager["data"][0]["csc"] = "NotTest"

        self.assertFalse(
            self.producer.should_reply_to_message_data(sample_message_data_from_manager)
        )

    async def test_should_reply_to_message_data_no_reply_different_salindex(self):
        self.setup_for_data_handling_test(salindex=1)

        self.producer.store_samples(summaryState=self.sample_summary_state)

        sample_message_data_from_manager = self.sample_message_data_from_manager.copy()

        sample_message_data_from_manager["data"][0]["salindex"] = 2

        self.assertFalse(
            self.producer.should_reply_to_message_data(sample_message_data_from_manager)
        )

    async def test_should_reply_to_message_data_no_reply_no_stream(self):
        self.setup_for_data_handling_test(salindex=1)

        self.producer.store_samples(summaryState=self.sample_summary_state)

        sample_message_data_from_manager = self.sample_message_data_from_manager.copy()

        sample_message_data_from_manager["data"][0]["stream"][
            "event_name"
        ] = "notSummaryState"

        self.assertFalse(
            self.producer.should_reply_to_message_data(sample_message_data_from_manager)
        )

    async def test_send_reply_to_message_data(self):
        self.setup_for_data_handling_test(salindex=1)

        self.producer.store_samples(summaryState=self.sample_summary_state)

        await self.producer.send_reply_to_message_data(
            self.sample_message_data_from_manager
        )

        await self.wait_for_number_of_samples(1)

        self.assertEqual(len(self.messages_received), 1)
        self.assertEqual(
            json.loads(self.messages_received[0])["data"][0], self.sample_summary_state
        )

    async def test_reply_to_message_data(self):
        self.setup_for_data_handling_test(salindex=1)

        self.producer.store_samples(summaryState=self.sample_summary_state)

        await self.producer.reply_to_message_data(self.sample_message_data_from_manager)

        await self.wait_for_number_of_samples(number_of_samples=1)

        self.assertGreaterEqual(len(self.messages_received), 1)
        self.assertEqual(
            self.sample_summary_state, json.loads(self.messages_received[0])["data"][0]
        )

    async def test_store_and_retrieve_samples(self):
        self.producer.store_samples(summaryState=self.sample_summary_state)

        sample_summary_state = self.producer.retrieve_samples("summaryState")

        self.assertEqual(sample_summary_state[0], self.sample_summary_state)

    async def assert_monitored_data(self, name, minimum_samples):
        await self.wait_for_number_of_samples(number_of_samples=minimum_samples)

        self.assertGreaterEqual(len(self.messages_received), minimum_samples)

        for message_received in self.messages_received:
            self.log.debug(f"message_received: {message_received}")
            self.assertEqual(json.loads(message_received)["data"][0]["name"], name)

    async def wait_for_number_of_samples(self, number_of_samples):
        timeout = (number_of_samples + 1) * self.producer.period_default_in_seconds

        self.log.debug(
            f"Waiting for {number_of_samples} samples or {timeout} seconds, whatever comes first."
        )

        test_timeout_task = asyncio.create_task(asyncio.sleep(timeout))

        while not test_timeout_task.done():
            if len(self.messages_received) >= number_of_samples:
                await cancel_task(test_timeout_task)
            else:
                await asyncio.sleep(self.time_pooling)

    def setup_for_data_handling_test(self, **kwargs):
        self.producer.send_message = self.async_send_message

        component_name = "Test"

        self.producer.component_name = component_name

        self.producer.add_metadata(**kwargs)

    def setup_data_generation_loop(self):
        self._run_data_generator_loop = True

        self.data_generator_task = asyncio.create_task(self._generate_data_loop())

    def stop_data_generation_loop(self):
        self._run_data_generator_loop = False

    async def _generate_data_loop(self):
        while self._run_data_generator_loop:
            if self.generate_async_data_callback is not None:
                await self.generate_async_data_callback(
                    await self.async_get_random_data_randomly()
                )
            else:
                await asyncio.sleep(self.time_pooling)

    def send_message(self, message):
        pass

    async def async_send_message(self, message):
        await asyncio.sleep(0.0)
        self.messages_received.append(message)

    async def async_get_random_data_randomly(self):
        await asyncio.sleep(np.random.random())
        return self.get_random_data(name="async_get_random_data_randomly")

    async def async_get_random_data(self):
        await asyncio.sleep(0.0)
        return self.get_random_data(name="async_get_random_data")

    def get_random_data(self, name=None):
        return dict(
            name="get_random_data" if name is None else name,
            value=np.random.random(),
            timestamp=Time.now().tai.datetime.timestamp(),
        )


if __name__ == "__main__":
    unittest.main()
