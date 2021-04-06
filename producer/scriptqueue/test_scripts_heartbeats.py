import os
import warnings
import datetime

import asyncio
import asynctest
from asynctest.mock import patch
from lsst.ts import salobj
from lsst.ts import scriptqueue
from lsst.ts.idl.enums.ScriptQueue import Location
from lsst.ts.salobj.base_script import HEARTBEAT_INTERVAL

import producer_utils
from scriptqueue.producer import ScriptQueueProducer

LONG_TIMEOUT = 60
SHORT_TIMEOUT = 1
HEARTBEAT_TIMEOUT = 3 * HEARTBEAT_INTERVAL
TIMEOUT = 15


class ScriptHeartbeatTestCase(asynctest.TestCase):
    async def tearDown(self):
        nkilled = len(self.queue.model.terminate_all())
        if nkilled > 0:
            warnings.warn(f"Killed {nkilled} subprocesses")
        await self.queue.close()

    async def wait_until_state_indices_match(
        self, waiting_indices, current_index, finished_indices
    ):
        """Reads/waits for produced messages until the lists of waiting,
        current and finished scripts indices matches the input, returning the
        stream data.
        """
        while True:
            message = await self.message_queue.get()

            # extract stream from message if it exists
            if not producer_utils.check_stream_from_last_message(
                message, "event", "ScriptQueueState", 1, "stream"
            ):
                continue
            stream = producer_utils.get_stream_from_last_message(
                message, "event", "ScriptQueueState", 1, "stream"
            )

            # if any does not match, continue
            if stream["finishedIndices"] != finished_indices:
                continue
            if stream["waitingIndices"] != waiting_indices:
                continue
            if stream["currentIndex"] != current_index:
                continue

            # if everything matches, return
            return stream

    async def wait_for_heartbeat_to_be_received(self, target_stamp):
        """Waits for a heartbeat message to be produced with a specific
        last_heartbeat_timestamp and returns its produced stream"""
        while True:
            message = await self.message_queue.get()
            if producer_utils.check_stream_from_last_message(
                message, "event", "ScriptHeartbeats", 1, "stream"
            ):
                stream = producer_utils.get_stream_from_last_message(
                    message, "event", "ScriptHeartbeats", 1, "stream"
                )
                print(
                    "datetime:", stream["script_heartbeat"]["last_heartbeat_timestamp"]
                )
                if (
                    stream["script_heartbeat"]["last_heartbeat_timestamp"]
                    == target_stamp
                ):
                    return stream

    @patch("scriptqueue.producer.datetime")
    async def test_heartbeats(self, mock_datetime):
        """Tests that a script heartbeat contains the right info
        for a "healthy" current script"""
        mock_datetime.datetime.now.return_value = datetime.datetime(2019, 1, 1)
        # ARRANGE
        # Create the CSC
        salobj.set_random_lsst_dds_partition_prefix()
        datadir = "/home/saluser/repos/ts_scriptqueue/tests/data"
        standardpath = os.path.join(datadir, "standard")
        externalpath = os.path.join(datadir, "external")
        self.queue = scriptqueue.ScriptQueue(
            index=1, standardpath=standardpath, externalpath=externalpath, verbose=True
        )
        await asyncio.wait_for(self.queue.start_task, TIMEOUT)

        # Create a remote and send the csc to enabled state
        self.remote = salobj.Remote(
            domain=self.queue.domain, name="ScriptQueue", index=1
        )
        await self.remote.start_task
        await asyncio.wait_for(self.remote.start_task, TIMEOUT)
        await self.remote.cmd_start.start(timeout=TIMEOUT)
        await self.remote.cmd_enable.start(timeout=TIMEOUT)

        # Create the producer
        self.message_queue = asyncio.Queue()

        def callback(msg):
            asyncio.get_event_loop().create_task(self.message_queue.put(msg))

        producer = ScriptQueueProducer(
            domain=self.queue.domain, send_message_callback=callback, index=1
        )
        await asyncio.wait_for(producer.setup(), TIMEOUT)

        # Add a script
        ack = await self.remote.cmd_add.set_start(
            isStandard=True,
            path="script1",
            config=f"wait_time: 6000000",
            location=Location.LAST,
            locationSalIndex=0,
            descr="test_add",
            timeout=TIMEOUT,
        )
        index = int(ack.result)
        script_remote = salobj.Remote(
            domain=self.queue.domain, name="Script", index=index
        )
        await script_remote.start_task

        # Wait for the script to be the current script
        waiting_indices = []
        current_index = 100000
        finished_indices = []
        await asyncio.wait_for(
            self.wait_until_state_indices_match(
                waiting_indices, current_index, finished_indices
            ),
            timeout=LONG_TIMEOUT,
        )

        # ACT
        # get the next script heartbeat in SAL
        # heartbeat_data = await script_remote.evt_heartbeat.next(
        #     flush=True, timeout=LONG_TIMEOUT
        # )

        # get the produced heartbeat message
        produced_heartbeat_stream = await asyncio.wait_for(
            self.wait_for_heartbeat_to_be_received(
                mock_datetime.datetime.now().timestamp()
            ),
            HEARTBEAT_TIMEOUT,
        )

        # ASSERT
        expected_heartbeat_stream = {
            "script_heartbeat": {
                "salindex": index,
                "lost": 0,
                # https://github.com/lsst-ts/LOVE-producer/issues/53
                # "last_heartbeat_timestamp": heartbeat_data.private_sndStamp
                "last_heartbeat_timestamp": mock_datetime.datetime.now().timestamp(),
            }
        }

        self.assertEqual(produced_heartbeat_stream, expected_heartbeat_stream)
