import asyncio
import unittest
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


class ScriptQueueStateTestCase(unittest.TestCase):
    def setUp(self):
        salobj.set_random_lsst_dds_domain()
        self.datadir = "/home/saluser/repos/ts_scriptqueue/tests/data"
        self.testdata_standardpath = os.path.join(self.datadir, "standard")
        self.testdata_externalpath = os.path.join(self.datadir, "external")
        self.badpath = os.path.join(self.datadir, "not_a_directory")

    def test_available_scripts(self):
        """Test the list of available scripts has the right content with the right format """
        async def doit():
            async with scriptqueue.ScriptQueue(
                    index=1,
                    standardpath=self.testdata_standardpath,
                    externalpath=self.testdata_externalpath) as queue:

                # Arrange

                remote = salobj.Remote(queue.domain, 'ScriptQueue', 1)
                await remote.cmd_start.start(timeout=30)
                await remote.cmd_enable.start(timeout=30)

                callback = MagicMock()
                scriptqueue_producer = ScriptQueueProducer(domain=queue.domain, send_message_callback=callback, index=1)

                # Act
                asyncio.create_task(remote.cmd_showAvailableScripts.start(timeout=STD_TIMEOUT))
                availableScripts = await remote.evt_availableScripts.next(flush=True)

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
                    if len(callback.call_args_list) == 0:
                        await asyncio.sleep(0.5)
                        continue
                    message = callback.call_args_list[-1][0][0]
                    available_scripts = message['data'][0]['data']['stream']['available_scripts']
                    if not available_scripts is None and len(available_scripts) > 0:
                        break
                    await asyncio.sleep(0.5)

                expected_available = expected_standard + expected_external
                received_available = message['data'][0]['data']['stream']['available_scripts']
                self.assertEqual(expected_available, received_available)

                # # Clean up
                await remote.close()
                await scriptqueue_producer.queue.close()
        asyncio.get_event_loop().run_until_complete(doit())

    def test_queue_event_matches(self):
        """Test that the data from the queue event is properly gathered in the message."""

        async def doit():
            async with scriptqueue.ScriptQueue(
                    index=1,
                    standardpath=self.testdata_standardpath,
                    externalpath=self.testdata_externalpath) as queue:
                queue.summaryState = salobj.State.ENABLED
                # Arrange
                remote = salobj.Remote(queue.domain, 'ScriptQueue', 1)
                await asyncio.gather(queue.start_task, remote.start_task)
                await remote.cmd_start.start()
                await remote.cmd_enable.start()
                callback = MagicMock()

                scriptqueue_producer = ScriptQueueProducer(domain=queue.domain, send_message_callback=callback, index=1)

                # Act: add some scripts to the queue
                for i in range(5):
                    if i > 0:
                        await asyncio.sleep(0.5)
                    salindex = await remote.cmd_add.set_start(isStandard=True,
                                                              path="script1",
                                                              config="wait_time: 1",
                                                              location=Location.FIRST,
                                                              locationSalIndex=0,
                                                              descr="test_add", timeout=5)

                    for lap in range(10):
                        # there is no warranty of when the remote will be updated
                        # so better wait for it
                        data = await remote.evt_queue.next(flush=True)
                        if data.currentSalIndex == int(salindex.result):
                            break

                # wait until the current script is the same as in the queue
                for lap in range(10):
                    if lap > 0:
                        await asyncio.sleep(0.5)
                    message = callback.call_args_list[-1][0][0]
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

                # # Clean up
                await remote.close()
                await scriptqueue_producer.queue.close()
        asyncio.get_event_loop().run_until_complete(doit())
