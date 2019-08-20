import asyncio
import unittest
from lsst.ts import salobj
from lsst.ts import scriptqueue
import os
from .producer import ScriptQueueProducer


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
        callback_future = asyncio.Future()

        def callback(message):
            callback_future.set_result(message)

        async def doit():
            async with scriptqueue.ScriptQueue(
                    index=1,
                    standardpath=self.testdata_standardpath,
                    externalpath=self.testdata_externalpath) as queue:

                # Arrange

                remote = salobj.Remote(queue.domain, 'ScriptQueue', 1)
                await remote.cmd_start.start(timeout=30)
                await remote.cmd_enable.start(timeout=30)

                scriptqueue_producer = ScriptQueueProducer(domain=queue.domain, send_state=callback, index=1)

                # Act
                asyncio.create_task(remote.cmd_showAvailableScripts.start(timeout=STD_TIMEOUT))
                availableScripts = await remote.evt_availableScripts.next(flush=False)
                message = await callback_future

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
                received_available = message['data'][0]['data']['stream']['available_scripts']

                self.assertEqual(expected_available, received_available)

                # Clean up
                await remote.close()
                await scriptqueue_producer.queue.close()


        asyncio.get_event_loop().run_until_complete(doit())
