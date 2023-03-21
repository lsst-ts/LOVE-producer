# This file is part of ts_salobj.
#
# Developed for the Rubin Observatory Telescope and Site System.
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
import unittest
import logging
import contextlib

from lsst.ts import salobj

from love.producer import LoveProducerCSC
from love.producer.test_utils import cancel_task


class TestLoveProducerCSC(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        cls.log = logging.getLogger(__name__)
        cls.standard_timeout = 5
        cls.time_pooling = 0.1
        cls.csc_construction_timeout = 30.0

    async def asyncSetUp(self):
        salobj.set_random_lsst_dds_partition_prefix()
        os.environ["LSST_SITE"] = "test"

        self.salindex = 1
        self.csc = "Test"

        self.messages_received = {}

        self.domain = salobj.Domain()

        self.producer = LoveProducerCSC(
            csc=self.csc,
            salindex=self.salindex,
            domain=self.domain,
        )

        self.producer.send_message = self.async_send_message

        await self.producer.start_task

    async def asyncTearDown(self):
        await self.producer.close()

    async def test_get_telemetry_attribute_names(self):
        telemetry_attribute_names = [
            name
            for name, _ in self.producer.get_telemetry_attribute_names_and_category()
        ]

        for telemetry_name in self.producer.remote.salinfo.telemetry_names:
            self.assertIn(f"tel_{telemetry_name}", telemetry_attribute_names)

    async def test_get_event_attribute_names_and_category(self):
        event_attribute_names_and_category = (
            self.producer.get_event_attribute_names_and_category()
        )

        event_attribute_names = {name for name, _ in event_attribute_names_and_category}

        for event_name in self.producer.remote.salinfo.event_names:
            self.assertIn(f"evt_{event_name}", event_attribute_names)

    async def test_generate_valid_topic_names_from_good_data(self):
        telemetry_attribute_names = (
            self.producer.get_telemetry_attribute_names_and_category()
        )

        valid_topic_attribute_names = (
            self.producer.generate_valid_topic_attribute_names(
                [name for name, _ in telemetry_attribute_names]
            )
        )

        for topic_attribute_name, _ in valid_topic_attribute_names:
            self.assertTrue(hasattr(self.producer.remote, topic_attribute_name))

    async def test_generate_valid_topic_names_from_bad_data(self):
        attribute_names = self.producer.get_telemetry_attribute_names_and_category()

        attribute_names.append(("tel_unitTestBadName", "telemetry"))
        attribute_names.append(("evt_unitTestBadName", "event"))

        valid_topic_attribute_names = (
            self.producer.generate_valid_topic_attribute_names(
                [name for name, _ in attribute_names]
            )
        )

        for topic_attribute_name, _ in valid_topic_attribute_names:
            self.assertTrue(hasattr(self.producer.remote, topic_attribute_name))

    async def test_get_topic_attribute_name(self):
        rev_code = self.producer.remote.evt_heartbeat.rev_code

        self.assertEqual(
            self.producer.get_topic_attribute_name(rev_code), "evt_heartbeat"
        )

    async def test_summary_state(self):
        async with self.setup_test_csc():
            await self.assert_minimum_samples_of(
                topic_name="summaryState",
                name_index="Test:1",
                category="event",
                minimum_samples=1,
            )

    async def test_heartbeat(self):
        async with self.setup_test_csc():
            heartbeat_minimum_samples = 5
            self.standard_timeout = 20

            await self.assert_minimum_samples_of(
                topic_name="stream",
                name_index="Heartbeat:0",
                category="event",
                minimum_samples=heartbeat_minimum_samples,
            )

    async def test_telemetry(self):
        async with self.setup_test_csc() as remote:
            await salobj.set_summary_state(remote, salobj.State.ENABLED)

            await remote.cmd_setScalars.set_start(
                string0="This is a test.", timeout=self.standard_timeout
            )

            await self.assert_minimum_samples_of(
                topic_name="scalars",
                name_index="Test:1",
                category="telemetry",
                minimum_samples=2,
            )

    async def assert_minimum_samples_of(
        self, topic_name, name_index, category, minimum_samples
    ):
        await self.wait_for_number_of_samples_of_topic(
            number_of_samples=minimum_samples,
            topic_name=topic_name,
            name_index=name_index,
            category=category,
        )

        self.log.debug(
            f"Summary of messages received: {set(self.messages_received[category][name_index].keys())}"
        )

        self.assertGreaterEqual(
            self.get_number_of_samples(
                topic_name=topic_name, name_index=name_index, category=category
            ),
            minimum_samples,
        )

    async def wait_for_number_of_samples_of_topic(
        self, number_of_samples, topic_name, name_index, category
    ):
        self.log.debug(
            f"Waiting for {number_of_samples} samples of {topic_name} or "
            f"{self.standard_timeout} seconds, "
            "whatever comes first."
        )

        test_timeout_task = asyncio.create_task(asyncio.sleep(self.standard_timeout))

        while (not test_timeout_task.done()) and (
            self.get_number_of_samples(
                topic_name=topic_name, name_index=name_index, category=category
            )
            < number_of_samples
        ):
            await asyncio.sleep(self.time_pooling)

        await cancel_task(test_timeout_task)

        number_of_samples_received = self.get_number_of_samples(
            topic_name=topic_name, name_index=name_index, category=category
        )

        self.log.debug(
            f"Done waiting for {number_of_samples} samples. "
            f"Got {number_of_samples_received}."
        )

    def get_number_of_samples(self, topic_name, category, name_index):
        return (
            len(self.messages_received[category][name_index][topic_name])
            if category in self.messages_received
            and name_index in self.messages_received[category]
            and topic_name in self.messages_received[category][name_index]
            else 0
        )

    async def async_send_message(self, message):
        self.log.debug(f"send_message: {message}")
        data_message = json.loads(message)
        data_category = data_message["category"]
        csc = data_message["data"][0]["csc"]
        salindex = data_message["data"][0]["salindex"]
        name_index = f"{csc}:{salindex}"

        if data_category not in self.messages_received:
            self.log.debug(
                f"Creating entry for '{data_category}' in received data dictionary."
            )
            self.messages_received[data_category] = dict()

        if name_index not in self.messages_received[data_category]:
            self.log.debug(f"Adding {name_index} to {data_category}...")
            self.messages_received[data_category][name_index] = dict()

        for topic in data_message["data"][0]["data"]:
            if topic not in self.messages_received[data_category][name_index]:
                self.log.debug(f"Adding topic {topic} to {data_category}::{name_index}")
                self.messages_received[data_category][name_index][topic] = []

            self.messages_received[data_category][name_index][topic].append(
                data_message["data"][0]["data"]
                if "data" in data_message["data"][0]
                else data_message
            )

    @contextlib.asynccontextmanager
    async def setup_test_csc(self):
        try:
            self.log.debug("Starting test csc process...")
            run_test_csc_task = await asyncio.create_subprocess_exec(
                "run_test_csc",
                str(self.salindex),
            )

            self.log.debug("Waiting for CSC to become alive")
            async with salobj.Remote(
                self.domain,
                "Test",
                index=self.salindex,
                include=["heartbeat", "summaryState"],
            ) as r:
                try:
                    await r.evt_heartbeat.next(
                        flush=True, timeout=self.csc_construction_timeout
                    )
                except asyncio.TimeoutError:
                    self.log.error(
                        f"No heartbeat from CSC in the last {self.csc_construction_timeout}. "
                        "Unit tests will probably fail. Continuing."
                    )
                except Exception:
                    self.log.exception(
                        "Error getting heartbeat from CSC. Unit tests will probably fail. Continuing."
                    )
                else:
                    self.log.debug("Received heartbeat from csc.")

                yield r
        finally:
            self.log.debug("Terminating CSC.")
            run_test_csc_task.terminate()
            await run_test_csc_task.wait()


if __name__ == "__main__":
    unittest.main()
