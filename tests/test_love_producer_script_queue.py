# This file is part of LOVE-producer.
#
# Developed for the Rubin Observatory Telescope and Site System.
# This product includes software developed by Inria Chile and
# the LSST Project (https://www.lsst.org).
#
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

import json
from typing import Dict
import yaml
import pytest
import shutil
import asyncio
import logging
import pathlib
import unittest
import contextlib
import subprocess


from lsst.ts.idl.enums import ScriptQueue
from lsst.ts import utils
from lsst.ts import salobj

from love.producer import LoveProducerScriptQueue
from love.producer.test_utils import cancel_task


@pytest.fixture(scope="class")
def run_script_queue(request):
    salobj.set_random_lsst_dds_partition_prefix()

    index = 1

    datadir = pathlib.Path(__file__).parents[1].joinpath("tests", "data")
    standardpath = datadir / "standard/"
    externalpath = datadir / "external/"

    print(f"standard scripts: {standardpath}")
    print(f"external scripts: {externalpath}")

    process = subprocess.Popen(
        [
            shutil.which("run_script_queue"),
            f"{index}",
            "--standard",
            f"{standardpath}",
            "--external",
            f"{externalpath}",
            "--state",
            "enabled",
        ]
    )

    request.cls.index = index

    with utils.modify_environ(LSST_SITE="test"):
        yield

    process.terminate()
    process.wait()


@pytest.mark.usefixtures("run_script_queue")
class TestLoveProducerScriptQueue(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        cls.log = logging.getLogger(__name__)
        cls.standard_timeout = 5
        cls.time_pooling = 0.1
        cls.csc_construction_timeout = 30.0
        cls.maxDiff = None

    async def asyncSetUp(self):
        self.salindex = 1

        self.messages_received = {}

        self.domain = salobj.Domain()

        self.remote = salobj.Remote(
            self.domain,
            "ScriptQueue",
            index=self.salindex,
            include=["heartbeat", "summaryState", "queue"],
        )

        await self.remote.start_task

        await self.remote.evt_heartbeat.next(
            flush=True, timeout=self.csc_construction_timeout
        )

        self.producer = LoveProducerScriptQueue(
            salindex=self.salindex,
            domain=self.domain,
        )

        self.producer.send_message = self.async_send_message

        await self.producer.start_task

    async def test_heartbeat(self):
        heartbeat_minimum_samples = 3
        self.standard_timeout = 10

        await self.assert_minimum_samples_of(
            topic_name="stream",
            name_index="Heartbeat:0",
            category="event",
            minimum_samples=heartbeat_minimum_samples,
        )

        await self.assert_last_sample(
            topic_name="stream",
            name_index="Heartbeat:0",
            category="event",
            topic_sample=dict(
                csc="ScriptQueue",
                salindex=1,
                lost=0,
                max_lost_heartbeats=5,
            ),
        )

    async def test_initial_subscription_messages(self):
        initial_state_messages_received = []

        async for initial_state_message in self.producer.get_initial_state_messages_as_json():
            initial_state_messages_received.append(json.loads(initial_state_message))

        self.assertEqual(len(initial_state_messages_received), 4)

        initial_state_csc_expected = {
            "all",
            "ScriptQueue",
            "ScriptQueueState",
            "Script",
        }

        for initial_state_message in initial_state_messages_received:
            self.assertIn(initial_state_message["csc"], initial_state_csc_expected)
            initial_state_csc_expected.remove(initial_state_message["csc"])

    async def test_standard_state_transition(self):
        await self.assert_minimum_samples_of(
            topic_name="summaryState",
            name_index="ScriptQueue:1",
            category="event",
            minimum_samples=1,
        )

        await salobj.set_summary_state(self.remote, salobj.State.STANDBY)

        async with self.enable_script_queue():
            expected_events_samples = [
                ("summaryState", 3),
                ("availableScripts", 1),
                ("rootDirectories", 1),
                ("queue", 2),
                ("softwareVersions", 1),
                ("simulationMode", 1),
                ("logLevel", 1),
                ("authList", 1),
            ]

            for event_name, minimum_samples in expected_events_samples:
                await self.assert_minimum_samples_of(
                    topic_name=event_name,
                    name_index="ScriptQueue:1",
                    category="event",
                    minimum_samples=minimum_samples,
                )

    async def test_handle_event_scriptqueue_script(self):
        async with self.enable_script_queue():
            # Pause queue so script won't execute.
            await self.remote.cmd_pause.start()

            await self.remote.cmd_add.set_start(
                isStandard=True,
                path="love_std_script.py",
                location=ScriptQueue.Location.LAST,
                logLevel=logging.DEBUG,
                pauseCheckpoint="pause love",
                stopCheckpoint="stop love",
            )

            await self.assert_minimum_samples_of(
                topic_name="script",
                name_index="ScriptQueue:1",
                category="event",
                minimum_samples=1,
            )

    async def test_reply_initial_state_request(self):
        async with self.enable_script_queue():
            async for initial_state_request_msg in self.get_initial_state_request_msg():
                assert self.producer.should_reply_to_message_data(
                    initial_state_request_msg
                )

                await self.producer.send_reply_to_message_data(
                    initial_state_request_msg
                )

    async def test_script_heartbeat(self):
        heartbeat_minimum_samples = 5
        self.standard_timeout = 20

        async with self.enable_script_queue():
            # Pause queue so script won't execute.
            await self.remote.cmd_pause.start()

            ack = await self.remote.cmd_add.set_start(
                isStandard=True,
                path="love_std_script.py",
                location=ScriptQueue.Location.LAST,
                logLevel=logging.DEBUG,
                pauseCheckpoint="pause love",
                stopCheckpoint="stop love",
            )

            self.log.debug(f"{ack}")

            await self.assert_minimum_samples_of(
                topic_name="stream",
                name_index=f"ScriptHeartbeats:{self.salindex}",
                category="event",
                minimum_samples=heartbeat_minimum_samples,
            )

    async def test_script_log_message(self):
        log_messages_minimum_samples = 4
        self.standard_timeout = 20

        async with self.enable_script_queue():
            ack = await self.remote.cmd_add.set_start(
                isStandard=True,
                path="love_std_script.py",
                location=ScriptQueue.Location.LAST,
                logLevel=logging.DEBUG,
                pauseCheckpoint="pause love",
                stopCheckpoint="stop love",
                timeout=self.standard_timeout,
            )

            self.log.debug(f"{ack}")

            await self.assert_minimum_samples_of(
                topic_name="logMessage",
                name_index=f"Script:{ack.result}",
                category="event",
                minimum_samples=log_messages_minimum_samples,
            )

    async def test_scriptqueue_state_message_data(self):
        state_minimum_samples = 3
        self.standard_timeout = 10

        async with self.enable_script_queue():
            await self.assert_minimum_samples_of(
                topic_name="stream",
                name_index="ScriptQueueState:1",
                category="event",
                minimum_samples=state_minimum_samples,
                additional_samples=5,
            )

            script_queue_state_sample = self.get_script_queue_state_sample()

            await self.assert_last_sample(
                topic_name="stream",
                name_index="ScriptQueueState:1",
                category="event",
                topic_sample=script_queue_state_sample,
            )

            # pause the queue and check new status
            await self.remote.cmd_pause.start(timeout=self.standard_timeout)
            script_queue_state_sample["running"] = False

            await self.assert_last_sample(
                topic_name="stream",
                name_index="ScriptQueueState:1",
                category="event",
                topic_sample=script_queue_state_sample,
            )

    def get_script_queue_state_sample(self) -> Dict:
        return {
            "enabled": True,
            "running": True,
            "available_scripts": [
                {
                    "type": "standard",
                    "path": "love_std_script.py",
                    "configSchema": yaml.safe_dump(
                        yaml.safe_load(
                            """
$schema: http://json-schema.org/draft-07/schema#
$id: https://github.com/lsst-ts/LOVE-producer/blob/develop/tests/data/standard/love_std_script.py
title: LoveStdScript v1
description: Configuration for LoveStdScript.
type: object
properties:
    sleep_time:
        description: How long to sleep for.
        type: number
        default: 0.0
additionalProperties: false
        """
                        )
                    )
                    + "\n",
                },
                {
                    "type": "external",
                    "path": "love_ext_script.py",
                    "configSchema": yaml.safe_dump(
                        yaml.safe_load(
                            """
$schema: http://json-schema.org/draft-07/schema#
$id: https://github.com/lsst-ts/LOVE-producer/blob/develop/tests/data/external/love_ext_script.py
title: LoveExtScript v1
description: Configuration for LoveExtScript.
type: object
properties:
    sleep_time:
        description: How long to sleep for.
        type: number
        default: 0.0
additionalProperties: false
        """
                        )
                    )
                    + "\n",
                },
            ],
            "waitingIndices": [],
            "currentIndex": 0,
            "waiting_scripts": [],
            "current": "None",
        }

    async def asyncTearDown(self):
        await self.remote.close()
        await self.producer.close()
        await self.domain.close()

    async def assert_minimum_samples_of(
        self,
        topic_name,
        name_index,
        category,
        minimum_samples,
        additional_samples=0,
    ):
        await self.wait_for_number_of_samples_of_topic(
            number_of_samples=minimum_samples + additional_samples,
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

    async def assert_last_sample(
        self,
        topic_name,
        name_index,
        category,
        topic_sample,
    ):
        last_sample = self.messages_received[category][name_index][topic_name][-1][
            topic_name
        ]

        self.log.debug(
            f"Last sample of {category}-{name_index}-{topic_name}: {last_sample}"
        )
        self.log.debug(f"Expected last sample: {topic_sample}")
        for key in topic_sample:
            self.assertEqual(
                topic_sample[key],
                last_sample[key],
                f"Mismatched item '{key}' in {topic_name}. "
                f"Expected: {topic_sample[key]}"
                f"Got: {last_sample[key]}",
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

    async def get_initial_state_request_msg(self):
        initial_state_request_msgs = [
            dict(
                category="initial_state",
                data=[
                    dict(
                        csc="Script",
                        salindex=0,
                        data=dict(event_name="logMessage"),
                    )
                ],
                subscription="initial_state-all-all-all",
            ),
            dict(
                category="initial_state",
                data=[
                    dict(
                        csc="ScriptQueueState",
                        salindex=self.salindex,
                        data=dict(event_name="stream"),
                    )
                ],
                subscription="initial_state-all-all-all",
            ),
        ]

        for initial_state_request_msg in initial_state_request_msgs:
            yield initial_state_request_msg

    @contextlib.asynccontextmanager
    async def enable_script_queue(self):
        try:
            self.log.debug("Waiting for CSC to become alive")

            try:
                await self.remote.evt_heartbeat.next(
                    flush=True, timeout=self.csc_construction_timeout
                )
            except asyncio.TimeoutError:
                self.log.error(
                    f"No heartbeat from ScriptQueue in the last {self.csc_construction_timeout}. "
                    "Unit tests will probably fail. Continuing."
                )
            except Exception:
                self.log.exception(
                    "Error getting heartbeat from ScriptQueue. Unit tests will probably fail. "
                    "Continuing."
                )
            else:
                self.log.debug("Received heartbeat from csc.")

            await salobj.set_summary_state(self.remote, salobj.State.ENABLED)

            await self.remote.cmd_resume.start(timeout=self.csc_construction_timeout)

            yield

        finally:
            await self.remote.cmd_pause.start(timeout=self.csc_construction_timeout)

            self.log.debug("Terminate any running script.")

            queue = self.remote.evt_queue.get()

            if queue is not None:
                if queue.length > 0:
                    await self.remote.cmd_stopScripts.set_start(
                        salIndices=queue.salIndices,
                        length=queue.length,
                        terminate=True,
                        timeout=self.csc_construction_timeout,
                    )

                if queue.currentSalIndex > 0:
                    sal_indices = [0 for i in queue.salIndices]
                    sal_indices[0] = queue.currentSalIndex

                    await self.remote.cmd_stopScripts.set_start(
                        salIndices=sal_indices,
                        length=1,
                        terminate=True,
                        timeout=self.csc_construction_timeout,
                    )


if __name__ == "__main__":
    unittest.main()
