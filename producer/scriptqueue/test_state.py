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


LONG_TIMEOUT = 60


class TestScriptqueueState(asynctest.TestCase):
    async def tearDown(self):
        nkilled = len(self.queue.model.terminate_all())
        if nkilled > 0:
            warnings.warn(f"Killed {nkilled} subprocesses")
        await self.queue.close()

    async def test_state(self):
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
        print('queue ready')
        # Create a remote and send the csc to enabled state
        self.remote = salobj.Remote(domain=self.queue.domain, name="ScriptQueue", index=1)
        await self.remote.start_task
        await self.remote.cmd_start.start(timeout=30)
        await self.remote.cmd_enable.start(timeout=30)

        print('remote ready')
        # Create the producer
        message_queue = asyncio.Queue()

        def callback(msg):
            print('\033[92mwriting with callback\u001b[0m')

            asyncio.get_event_loop().create_task(message_queue.put(msg))

        producer = ScriptQueueProducer(domain=self.queue.domain, send_message_callback=callback, index=1)
        await producer.setup()

        print('producersetup')

        # Add 5 scripts, third one is longer, the idea is to freeze the queue in the third script
        durations = [0.1, 0.1, 3600, 0.1, 0.1]
        self.scripts_remotes = {}
        for duration in durations:
            ack = await self.remote.cmd_add.set_start(isStandard=True,
                                                      path="script1",
                                                      config=f"wait_time: {duration}",
                                                      location=Location.LAST,
                                                      locationSalIndex=0,
                                                      descr="test_add", timeout=5)
            index = int(ack.result)
            self.scripts_remotes[index] = salobj.Remote(domain=self.queue.domain, name='Script', index=index)

        #
        # # Wait for the third script to be the current script

        print('_---------------------------------------')

        async def wait_until_state_indices_match(waiting_indices, current_index, finished_indices):
            while True:
                message = await message_queue.get()
                stream = utils.get_stream_from_last_message(message, 'event', 'ScriptQueueState', 1, 'stream')
                print('\nfinished', stream['finishedIndices'],
                      stream['finishedIndices'] != finished_indices, finished_indices)
                print('current', stream['currentIndex'], stream['currentIndex'] != current_index, current_index)
                print('waiting', stream['waitingIndices'], stream['waitingIndices'] != waiting_indices, waiting_indices)
                if stream['finishedIndices'] != finished_indices:
                    print('finished noteq')
                    continue
                if stream['waitingIndices'] != waiting_indices:
                    print('waiting noteq')
                    continue
                if stream['currentIndex'] != current_index:
                    print('current noteq')
                    continue
                print('all eq')
                break

        waiting_indices = [100003, 100004]
        current_index = 100002
        finished_indices = [100001, 100000]

        await asyncio.wait_for(wait_until_state_indices_match(waiting_indices, current_index, finished_indices), timeout=LONG_TIMEOUT)

