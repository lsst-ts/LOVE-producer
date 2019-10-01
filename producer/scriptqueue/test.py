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

        self.message_queue = asyncio.Queue()

        def callback(msg):
            asyncio.create_task(self.message_queue.put(msg))
        self.callback = callback
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

    async def test_evt_availableScripts_callback(self):
        """Test the data from evt_availableScripts is properly obtained """

        # Arrange:
        async def producer_cor(target_salindex):
            while True:
                message = await self.message_queue.get()
                available_scripts = utils.get_parameter_from_last_message(message, 'event', 'ScriptQueue', 1, 'stream', 'available_scripts')
                if available_scripts is not None and len(available_scripts) > 0:
                    return available_scripts

        producer_task = asyncio.create_task(producer_cor(100002))

        # Act
        asyncio.create_task(self.remote.cmd_showAvailableScripts.start(timeout=STD_TIMEOUT))
        availableScripts = await self.remote.evt_availableScripts.next(flush=True)

        received_available = await producer_task

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

        expected_available = expected_standard + expected_external
        self.assertEqual(expected_available, received_available)

    async def test_evt_queue_callback(self):
        """Test the data from evt_queue is properly obtained after adding some scripts to the queue"""

        # Arrange:
        async def helper_cor(target_salindex):
            while True:
                # there is no warranty of when the remote will be updated
                # so better wait for it
                data = await self.remote.evt_queue.next(flush=True)
                if data.currentSalIndex == target_salindex:
                    return data

        async def producer_cor(target_salindex):
            while True:
                message = await self.message_queue.get()
                currentIndex = utils.get_parameter_from_last_message(
                    message, 'event', 'ScriptQueue', 1, 'stream', 'currentIndex')
                if currentIndex is not None and currentIndex == target_salindex:
                    return message

        helper_task = asyncio.create_task(helper_cor(100002))
        producer_task = asyncio.create_task(producer_cor(100002))

        # Act: add some scripts to the queue
        nscripts_to_add = 5
        # third_script_duration = 10
        for i in range(nscripts_to_add):
            duration = 0.1
            # if i == 2: duration = third_script_duration
            ack = await self.remote.cmd_add.set_start(isStandard=True,
                                                      path="script1",
                                                      config="wait_time: {}".format(duration),
                                                      location=Location.LAST,
                                                      locationSalIndex=0,
                                                      descr="test_add", timeout=5)

        # wait until the current script is the same as in the queue

        [data, message] = await asyncio.gather(helper_task, producer_task)
        stream = utils.get_stream_from_last_message(message, 'event', 'ScriptQueue', 1, 'stream')

        # Assert
        self.assertEqual(data.currentSalIndex, stream["currentIndex"])
        self.assertEqual(data.pastSalIndices[:data.pastLength],  stream['finishedIndices'])
        self.assertEqual(data.salIndices[:data.length],  stream['waitingIndices'])
        self.assertEqual(data.running,  stream['running'])
        self.assertEqual(data.enabled,  stream['enabled'])

    # async def test_evt_script_data(self):
    #     """
    #     Test the data from evt_queue is properly obtained  by monitoring all of its states changes from
    #     UNKNOWN to DONE
    #     """
    #     # Act:
    #     ack=await self.remote.cmd_add.set_start(isStandard=True,
    #                                               path="script1",
    #                                               config="wait_time: 1",
    #                                               location=Location.FIRST,
    #                                               locationSalIndex=0,
    #                                               descr="test_add", timeout=5)

    #     script_remote=salobj.Remote(domain=self.queue.domain, name="Script", index=int(ack.result))
    #     message=self.callback.call_args_list[-1][0][0]
    #     stream=utils.get_stream_from_last_message(message, 'event', 'ScriptQueue', 1, 'stream')

    #     retrieved_waiting=stream['waitingIndices']
    #     expected_waiting=[int(ack.result)]
    #     self.assertEqual(retrieved_waiting, expected_waiting)
