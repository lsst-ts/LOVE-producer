import asyncio
import unittest
import asynctest
import warnings

from lsst.ts import salobj
from lsst.ts import scriptqueue
import os
from .producer import ScriptQueueProducer
from unittest.mock import MagicMock
from lsst.ts.idl.enums.ScriptQueue import Location
import utils
STD_TIMEOUT = 10
START_TIMEOUT = 20
END_TIMEOUT = 10


class ScriptQueueStateTestCase(asynctest.TestCase):
    """
        Based on: https://github.com/lsst-ts/ts_scriptqueue/blob/25a3d996c9e71edc30afb61179ec39dcee151dc8/tests/test_script_queue.py#L106
    """
    async def setUp(self):
        salobj.set_random_lsst_dds_domain()
        self.datadir = "/home/saluser/repos/ts_scriptqueue/tests/data"
        standardpath = os.path.join(self.datadir, "standard")
        externalpath = os.path.join(self.datadir, "external")
        self.queue = scriptqueue.ScriptQueue(index=1,
                                             standardpath=standardpath,
                                             externalpath=externalpath,
                                             verbose=True)

        self.callback = MagicMock()
        self.scriptqueue_producer = ScriptQueueProducer(
            domain=self.queue.domain, send_message_callback=self.callback, index=1)
        self.remote = salobj.Remote(domain=self.queue.domain, name="ScriptQueue", index=1)
        await self.remote.cmd_start.start(timeout=30)
        await self.remote.cmd_enable.start(timeout=30)
        await asyncio.gather(self.queue.start_task, self.remote.start_task, self.scriptqueue_producer.queue.start_task)

    async def tearDown(self):
        nkilled = len(self.queue.model.terminate_all())
        if nkilled > 0:
            warnings.warn(f"Killed {nkilled} subprocesses")
        await self.queue.close()

    async def test_evt_availableScripts(self):
        """Test the data from evt_availableScripts is properly obtained """

        # Act
        asyncio.create_task(self.remote.cmd_showAvailableScripts.start(timeout=STD_TIMEOUT))
        availableScripts = await self.remote.evt_availableScripts.next(flush=True)

        # Assert
        expected_standard = [{
            'type': 'standard',
            'path': path,
            'configSchema': ''
        } for path in availableScripts.standard.split(':')]

        expected_external = [{
            'type': 'external',
            'path': path,
            'configSchema': ''
        } for path in availableScripts.external.split(':')]

        max_tries = 5
        for lap in range(max_tries):
            if len(self.callback.call_args_list) == 0:
                await asyncio.sleep(0.5)
                continue
            message = self.callback.call_args_list[-1][0][0]
            available_scripts = message['data'][0]['data']['stream']['available_scripts']
            if not available_scripts is None and len(available_scripts) > 0:
                break
            await asyncio.sleep(0.5)

        expected_available = expected_standard + expected_external
        received_available = message['data'][0]['data']['stream']['available_scripts']
        self.assertEqual(expected_available, received_available)

    async def test_queue_event_matches(self):
        """Test the data from evt_queue is properly obtained after adding some scripts to the queue"""

        # Act: add some scripts to the queue
        nscripts_to_add = 5
        for i in range(nscripts_to_add):
            if i > 0:
                await asyncio.sleep(0.5)
            salindex = await self.remote.cmd_add.set_start(isStandard=True,
                                                        path="script1",
                                                        config="wait_time: 1",
                                                        location=Location.FIRST,
                                                        locationSalIndex=0,
                                                        descr="test_add", timeout=5)

            for lap in range(10):
                # there is no warranty of when the remote will be updated
                # so better wait for it
                data = await self.remote.evt_queue.next(flush=True)
                if data.currentSalIndex == int(salindex.result):
                    break

        # wait until the current script is the same as in the queue
        laps_tolerance = 10
        for lap in range(laps_tolerance ):
            if lap > 0:
                await asyncio.sleep(0.5)
            message = self.callback.call_args_list[-1][0][0]
            currentIndex = utils.get_parameter_from_last_message(
                message, 'event', 'ScriptQueue', 1, 'stream', 'currentIndex')
            if not currentIndex is None and currentIndex > 0 and currentIndex == data.currentSalIndex:
                break

        # Assert
        stream = utils.get_stream_from_last_message(
            message, 'event', 'ScriptQueue', 1, 'stream')
        self.assertEqual(currentIndex, data.currentSalIndex)
        self.assertEqual(data.pastSalIndices[:data.pastLength],  stream['finishedIndices'])
        self.assertEqual(data.salIndices[:data.length],  stream['waitingIndices'])
        self.assertEqual(data.running,  stream['running'])
        self.assertEqual(data.enabled,  stream['enabled'])
