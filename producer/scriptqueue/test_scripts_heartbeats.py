import asyncio
import os
import asynctest
import warnings
from lsst.ts import salobj
from lsst.ts import scriptqueue
from lsst.ts.idl.enums.ScriptQueue import Location, ScriptProcessState
from lsst.ts.idl.enums.Script import ScriptState
from .producer import ScriptQueueProducer
from lsst.ts.salobj.base_script import HEARTBEAT_INTERVAL

import utils
import yaml

LONG_TIMEOUT = 60
SHORT_TIMEOUT = 1
HEARTBEAT_TIMEOUT = 3 * HEARTBEAT_INTERVAL


class ScriptHeartbeatTestCase(asynctest.TestCase):
    async def tearDown(self):
        nkilled = len(self.queue.model.terminate_all())
        if nkilled > 0:
            warnings.warn(f"Killed {nkilled} subprocesses")
        await self.queue.close()

    async def wait_until_state_indices_match(self, waiting_indices, current_index, finished_indices):
        """Reads/waits for produced messages until the lists of waiting, 
        current and finished scripts indices matches the input, returning the 
        stream data.
        """
        while True:
            message = await self.message_queue.get()

            # extract stream from message if it exists
            if not utils.check_stream_from_last_message(
                    message, 'event', 'ScriptQueueState', 1, 'stream'):
                continue
            stream = utils.get_stream_from_last_message(
                message, 'event', 'ScriptQueueState', 1, 'stream')

            # if any does not match, continue
            if stream['finishedIndices'] != finished_indices:
                continue
            if stream['waitingIndices'] != waiting_indices:
                continue
            if stream['currentIndex'] != current_index:
                continue

            # if everything matches, return
            return stream

    async def wait_for_heartbeat_to_be_received(self, sndStamp):
        """Waits for a heartbeat message to be produced with a specific 
        last_heartbeat_timestamp and returns its produced stream"""
        while True:
            message = await self.message_queue.get()
            if utils.check_stream_from_last_message(
                    message, 'event', 'ScriptHeartbeats', 1, 'stream'):
                stream = utils.get_stream_from_last_message(
                    message, 'event', 'ScriptHeartbeats', 1, 'stream')
                if sndStamp == stream['script_heartbeat']['last_heartbeat_timestamp']:
                    return stream

    async def test_heartbeats(self):
        """Tests that a script heartbeat contains the right info 
        for a "healthy" current script"""
        # ARRANGE
        # Create the CSC
        salobj.set_random_lsst_dds_domain()
        datadir = "/home/saluser/repos/ts_scriptqueue/tests/data"
        standardpath = os.path.join(datadir, "standard")
        externalpath = os.path.join(datadir, "external")
        self.queue = scriptqueue.ScriptQueue(index=1,
                                             standardpath=standardpath,
                                             externalpath=externalpath,
                                             verbose=True)
        await self.queue.start_task

        # Create a remote and send the csc to enabled state
        self.remote = salobj.Remote(
            domain=self.queue.domain, name="ScriptQueue", index=1)
        await self.remote.start_task
        await self.remote.cmd_start.start(timeout=30)
        await self.remote.cmd_enable.start(timeout=30)

        # Create the producer
        self.message_queue = asyncio.Queue()

        def callback(msg):
            asyncio.get_event_loop().create_task(self.message_queue.put(msg))

        producer = ScriptQueueProducer(
            domain=self.queue.domain, send_message_callback=callback, index=1)
        await producer.setup()

        # Add a script
        ack = await self.remote.cmd_add.set_start(isStandard=True,
                                                  path="script1",
                                                  config=f"wait_time: 6000000",
                                                  location=Location.LAST,
                                                  locationSalIndex=0,
                                                  descr="test_add", timeout=5)
        index = int(ack.result)
        script_remote = salobj.Remote(
            domain=self.queue.domain, name='Script', index=index)

        # Wait for the script to be the current script
        waiting_indices = []
        current_index = 100000
        finished_indices = []
        await asyncio.wait_for(
            self.wait_until_state_indices_match(waiting_indices, current_index, finished_indices),
            timeout=LONG_TIMEOUT)

        # ACT
        # get the next script heartbeat in SAL
        heartbeat_data = await script_remote.evt_heartbeat.next(flush=True, timeout=LONG_TIMEOUT)

        # get the produced heartbeat message
        produced_heartbeat_stream = await asyncio.wait_for(
            self.wait_for_heartbeat_to_be_received(heartbeat_data.private_sndStamp), HEARTBEAT_TIMEOUT)

        # ASSERT
        expected_heartbeat_stream = {
            'script_heartbeat': {
                'salindex': index,
                'lost': 0,
                "last_heartbeat_timestamp": heartbeat_data.private_sndStamp
            }
        }

        self.assertEqual(produced_heartbeat_stream, expected_heartbeat_stream)
