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

class MyTestCase(asynctest.TestCase):
    async def setUp(self):
        # Create the CSC and a remote to wait for events
        salobj.set_random_lsst_dds_domain()
        datadir = "/home/saluser/repos/ts_scriptqueue/tests/data"
        standardpath = os.path.join(datadir, "standard")
        externalpath = os.path.join(datadir, "external")
        self.queue = scriptqueue.ScriptQueue(index=1,
                                             standardpath=standardpath,
                                             externalpath=externalpath,
                                             verbose=True)
        await self.queue.start_task

        self.remote = salobj.Remote(domain=self.queue.domain, name="ScriptQueue", index=1)
        await self.remote.start_task
        await self.remote.cmd_start.start(timeout=30)
        await self.remote.cmd_enable.start(timeout=30)

        # Add a script
        ack = await self.remote.cmd_add.set_start(isStandard=True,
                                                  path="script1",
                                                  config="wait_time: 0.1",
                                                  location=Location.LAST,
                                                  locationSalIndex=0,
                                                  descr="test_add", timeout=5)
        self.script_index = int(ack.result)
        self.script_remote = salobj.Remote(domain=self.queue.domain, name='Script', index=self.script_index)
        await self.script_remote.start_task

        # Wait for it to reach the pastQueue
        while True:
            state = await self.remote.evt_queue.next(flush=False)
            print(
                f"\033[92mqueue={state.salIndices[0]}, current={state.currentSalIndex}, past={state.pastSalIndices[0]}\u001b[0m")
            if state.pastSalIndices[0] == int(self.script_index):
                break

        # Pause the queue (just in case), and wait for it to be paused
        await self.remote.cmd_pause.start()
        while True:
            state = await self.remote.evt_queue.next(flush=True)
            print(f'\033[92mrunning?{state.running}\u001b[0m')
            if not state.running:
                break
    
    async def tearDown(self):
        nkilled = len(self.queue.model.terminate_all())
        if nkilled > 0:
            warnings.warn(f"Killed {nkilled} subprocesses")
        await self.queue.close()
    # async def update(self):
    #     # Configure a remote to listen for callbacks of the evt_queue

    #     callback_remote = salobj.Remote(domain=self.queue.domain, name="ScriptQueue", index=1)
    #     await callback_remote.start_task

    #     # the callback should save messages to a queue
    #     message_queue = asyncio.Queue()

    #     def callback(msg):
    #         print('\033[92mwriting with callback\u001b[0m')
    #         asyncio.create_task(message_queue.put(msg))
    #     callback_remote.evt_queue.callback = callback

    #     # with self.assertRaises(asyncio.TimeoutError): 
    #     print(f'\033[92m waiting 10 s \u001b[0m')

        
    #     # m = await message_queue.get()
    #     # import pdb;pdb.set_trace()
    #     with self.assertRaises(asyncio.TimeoutError):
    #         message = await asyncio.wait_for(message_queue.get(), timeout=10)

    async def test_update2(self):
        self.remote.evt_script.flush()
        await self.remote.cmd_showScript.set_start(salIndex=self.script_index)
        evt_script_data = await self.remote.evt_script.next(flush=False)
        metadata = await self.script_remote.evt_metadata.next(flush=False)
        # state = await helper_evt_state(self.script_remote, expected_evt_state) if expected_evt_state is not None else None
        description = await self.script_remote.evt_description.next(flush=False)

        print('\033[92mgot descriptionf\u001b[0m')
        # Configure a callback for the producer
        message_queue = asyncio.Queue()

        def callback(msg):
            print('\033[92mwriting with callback\u001b[0m')
            asyncio.create_task(message_queue.put(msg))

        producer = ScriptQueueProducer(domain=self.queue.domain, send_message_callback=callback, index=1)
        await producer.setup()

        # make sure no more events are triggered
        with self.assertRaises(asyncio.TimeoutError): 
            print('waiting 10s for message')
            message = await asyncio.wait_for(message_queue.get(), timeout=5)


        # update
        print('\n\n will update \n\n\n\n\n\n')
        self.remote.evt_script.flush()
        await producer.update()
        await self.remote.evt_script.next(flush=False)
        # await producer.queue.cmd_showQueue.start(timeout=10)
        print('\033[92m\n\nqsize',message_queue.qsize(),'\u001b[0m')
        while not message_queue.empty():
            message = await message_queue.get()
            print('\n\n',message_queue.qsize())
        print('got message')
        stream = utils.get_stream_from_last_message(message, 'event', 'ScriptQueueState', 1, 'stream')
        
        # Assert: 

        # expected_last_checkpoint = '' if expected_evt_state is None else state.lastCheckpoint
        expected_script = {
            "index": evt_script_data.salIndex,
            "type": "standard" if evt_script_data.isStandard else "external",
            "path": evt_script_data.path,
            "process_state": ScriptProcessState(evt_script_data.processState).name,
            "script_state": ScriptState(evt_script_data.scriptState).name,
            "timestampConfigureEnd": evt_script_data.timestampConfigureEnd,
            "timestampConfigureStart": evt_script_data.timestampConfigureStart,
            "timestampProcessEnd": evt_script_data.timestampProcessEnd,
            "timestampProcessStart": evt_script_data.timestampProcessStart,
            "timestampRunStart": evt_script_data.timestampRunStart,

            "expected_duration": 0, #metadata.duration,
            "last_checkpoint": '', #expected_last_checkpoint,
            # # TODO "pause_checkpoints": checkpoints.pause,
            # # TODO "stop_checkpoints": checkpoints.stop,
            "description": '', # description.description,
            "classname": '', #description.classname,
            "remotes": '', #description.remotes,
        }
        
        produced_script = stream['finished_scripts'][0]
        print('\033[92m\n\n produced_script,', produced_script,'\u001b[0m')

        self.assertEqual(expected_script, produced_script)
        self.assertEqual('None', stream['current'])
        self.assertEqual([], stream['waiting_scripts'])

        print('asdfasdf')