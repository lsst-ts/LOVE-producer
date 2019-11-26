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
SHORT_TIMEOUT = 1

class TestScriptqueueState(asynctest.TestCase):
    async def tearDown(self):
        nkilled = len(self.queue.model.terminate_all())
        if nkilled > 0:
            warnings.warn(f"Killed {nkilled} subprocesses")
        await self.queue.close()

    async def wait_until_state_indices_match(self, waiting_indices, current_index, finished_indices):
        while True:
            message = await self.message_queue.get()
            stream = utils.get_stream_from_last_message(message, 'event', 'ScriptQueueState', 1, 'stream')
            if stream['finishedIndices'] != finished_indices:
                continue
            if stream['waitingIndices'] != waiting_indices:
                continue
            if stream['currentIndex'] != current_index:
                continue
            break
        return stream

    async def wait_for_script_state_to_match(self, salindex, queue_position, process_state, script_state):
        while True:
            message = await self.message_queue.get()
            stream = utils.get_stream_from_last_message(message, 'event', 'ScriptQueueState', 1, 'stream')
            
            if queue_position == "current":
                script = stream[queue_position]
            else:
                for s in stream[queue_position]:
                    if s["index"] == salindex: 
                        script = s 
                        break

            if script["process_state"] == process_state and script["script_state"] == script_state:
                return stream

    async def get_last_not_none_value_from_event_parameter(self, evt, parameter):
        value = None
        while True:
            last_data = evt.get_oldest()
            if last_data is None:
                return value
            value = getattr(last_data, parameter)
        
        return value

    async def make_expected_script(self, script_remote):
        # get script state data from scriptqueue.evt_script
        self.remote.evt_script.flush()
        await self.remote.cmd_showScript.set_start(salIndex=script_remote.salinfo.index)
        script_data = await self.remote.evt_script.next(flush=False)

        # get metadata, description and state from script remote
        metadata = await script_remote.evt_metadata.next(flush=False)
        description = await script_remote.evt_description.next(flush=False)
        lastCheckpoint = await asyncio.wait_for(self.get_last_not_none_value_from_event_parameter(script_remote.evt_state, 'lastCheckpoint'), SHORT_TIMEOUT)

        return {
            'index': script_data.salIndex,
            'path':  script_data.path,
            'type': "standard" if script_data.isStandard else "external",
            'process_state': ScriptProcessState(script_data.processState).name,
            'script_state':  ScriptState(script_data.scriptState).name,
            "timestampConfigureEnd": script_data.timestampConfigureEnd,
            "timestampConfigureStart": script_data.timestampConfigureStart,
            "timestampProcessEnd": script_data.timestampProcessEnd,
            "timestampProcessStart": script_data.timestampProcessStart,
            "timestampRunStart": script_data.timestampRunStart,

            "expected_duration": metadata.duration,
            "last_checkpoint": lastCheckpoint,
            # TODO "pause_checkpoints": checkpoints.pause,
            # TODO "stop_checkpoints": checkpoints.stop,
            "description": description.description,
            "classname": description.classname,
            "remotes": description.remotes,


        }
    
    async def test_state(self):
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
        self.remote = salobj.Remote(domain=self.queue.domain, name="ScriptQueue", index=1)
        await self.remote.start_task
        await self.remote.cmd_start.start(timeout=30)
        await self.remote.cmd_enable.start(timeout=30)

        # Create the producer
        self.message_queue = asyncio.Queue()

        def callback(msg):
            asyncio.get_event_loop().create_task(self.message_queue.put(msg))

        producer = ScriptQueueProducer(domain=self.queue.domain, send_message_callback=callback, index=1)
        await producer.setup()

        # ACT

        # Add 5 scripts, third one has longer duration
        # the idea is to freeze the queue in the third script
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

        # Wait for the third script to be the current script
        waiting_indices = [100003, 100004]
        current_index = 100002
        finished_indices = [100001, 100000]
        stream = await asyncio.wait_for(self.wait_until_state_indices_match(waiting_indices, current_index, finished_indices), timeout=LONG_TIMEOUT)
        stream = await asyncio.wait_for( self.wait_for_script_state_to_match(index, 'current', 'RUNNING', 'RUNNING'), timeout=LONG_TIMEOUT)

        # ASSERT

        # assert current script
        expected_script = await self.make_expected_script(self.scripts_remotes[current_index])
        self.assertEqual(expected_script, stream['current'])
        
        # assert waiting scripts
        for script_index in waiting_indices:
            expected_script = await self.make_expected_script(self.scripts_remotes[script_index])
            produced_script = next(s for s in stream['waiting_scripts'] if s['index'] == script_index)
            self.assertEqual(expected_script, produced_script)

        # assert finished scripts
        for script_index in finished_indices:
            expected_script = await self.make_expected_script(self.scripts_remotes[script_index])
            produced_script = next(s for s in stream['finished_scripts'] if s['index'] == script_index)
            self.assertEqual(expected_script, produced_script)