import asyncio
import os
import asynctest
import warnings
from lsst.ts import salobj
from lsst.ts import scriptqueue
from lsst.ts.idl.enums.ScriptQueue import Location, ScriptProcessState
from lsst.ts.idl.enums.Script import ScriptState
from .producer import ScriptQueueProducer
import utils
import yaml

LONG_TIMEOUT = 60
SHORT_TIMEOUT = 1
TIMEOUT = 30

class TestScriptqueueAvailableScripts(asynctest.TestCase):
    async def tearDown(self):
        nkilled = len(self.queue.model.terminate_all())
        if nkilled > 0:
            warnings.warn(f"Killed {nkilled} subprocesses")
        await asyncio.wait_for(self.queue.close(), TIMEOUT)

    async def wait_for_all_config_schema(self):
        while True:
            message = await self.message_queue.get()
            available_scripts = utils.get_parameter_from_last_message(
                message, 'event', 'ScriptQueueState', 1, 'stream', 'available_scripts')
            if all([s["path"] == "unloadable" or len(s["configSchema"]) > 0 for s in available_scripts]):

                return [
                    {
                        'type': s['type'], 'path': s['path'], 'configSchema': yaml.load(s['configSchema'], Loader=yaml.SafeLoader)
                        if s['configSchema'] != '' and s['path'] != 'subdir/subsubdir/script4' else ''
                    }
                    for s in available_scripts]

    async def test_state(self):
        """
            Asserts the produced message contains the right content after moving the queue
            to a certain state (1 running script, 2 waiting, 2 finished)
        """
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
        await asyncio.wait_for(self.queue.start_task, TIMEOUT)

        # Create a remote and send the csc to enabled state
        self.remote = salobj.Remote(domain=self.queue.domain, name="ScriptQueue", index=1)
        # await self.remote.start_task
        await asyncio.wait_for(self.remote.start_task, TIMEOUT)
        await asyncio.wait_for(self.remote.cmd_start.start(timeout=30), TIMEOUT)
        await asyncio.wait_for(self.remote.cmd_enable.start(timeout=30), TIMEOUT)

        # Create the producer
        self.message_queue = asyncio.Queue()

        def callback(msg):
            asyncio.get_event_loop().create_task(self.message_queue.put(msg))

        producer = ScriptQueueProducer(domain=self.queue.domain, send_message_callback=callback, index=1)
        await asyncio.wait_for(producer.setup(), LONG_TIMEOUT)

        # ACT
        await asyncio.wait_for(self.remote.cmd_showAvailableScripts.start(), TIMEOUT)
        availableScripts = await asyncio.wait_for(self.remote.evt_availableScripts.next(flush=True), TIMEOUT)
        received_available = await asyncio.wait_for(self.wait_for_all_config_schema(), LONG_TIMEOUT)

        # Assert
        expected_standard = [
            {
                'type': 'standard',
                'path': path,
                'configSchema': salobj.TestScript.get_schema()
            } if path != 'unloadable' and path != 'subdir/subsubdir/script4' else {
                'type': 'standard',
                'path': path,
                'configSchema': ''
            }
            for path in availableScripts.standard.split(':')
        ]

        expected_external = [
            {
                'type': 'external',
                'path': path,
                'configSchema': salobj.TestScript.get_schema()
            } if path != 'unloadable' and path != 'subdir/subsubdir/script4' else {
                'type': 'external',
                'path': path,
                'configSchema': ''
            } for path in availableScripts.external.split(':')
        ]

        expected_available = expected_standard + expected_external
        self.assertEqual(received_available, expected_available)
