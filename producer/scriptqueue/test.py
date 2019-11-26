import asyncio
import unittest
import asynctest
import warnings

from lsst.ts import salobj
from lsst.ts import scriptqueue
from lsst.ts.idl.enums.ScriptQueue import ScriptProcessState
from lsst.ts.idl.enums.Script import ScriptState
import os
import yaml
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
    maxDiff = None

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

    async def test_available_scripts_info(self):
        """
        Test the data in the list of available scripts is correct.
        It should get the information from these events:
        - evt_availableScripts
        - evt_configSchema
        """

        # Arrange:
        async def producer_cor(target_salindex):
            while True:
                message = await self.message_queue.get()
                available_scripts = utils.get_parameter_from_last_message(
                    message, 'event', 'ScriptQueueState', 1, 'stream', 'available_scripts')
                if available_scripts is not None and len(available_scripts) > 0:
                    allConfigReady = True
                    for script in available_scripts:
                        if script['configSchema'] == '' and script["path"] != 'unloadable':
                            allConfigReady = False
                            break
                    if allConfigReady:
                        return available_scripts

        producer_task = asyncio.create_task(producer_cor(100002))

        # Act
        helper_task = asyncio.create_task(self.remote.cmd_showAvailableScripts.start(timeout=STD_TIMEOUT))
        availableScripts = await self.remote.evt_availableScripts.next(flush=True)

        received_available = await producer_task
        await helper_task

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
        received_available = [
            {
                'type': script['type'],
                'path': script['path'],
                'configSchema': yaml.safe_load(script['configSchema'])
            } if script['path'] != 'unloadable' and script['path'] != 'subdir/subsubdir/script4' else {
                'type': script['type'],
                'path': script['path'],
                'configSchema': ''
            } for script in received_available
        ]

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
                    message, 'event', 'ScriptQueueState', 1, 'stream', 'currentIndex')
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
        stream = utils.get_stream_from_last_message(message, 'event', 'ScriptQueueState', 1, 'stream')

        # Assert
        self.assertEqual(data.currentSalIndex, stream["currentIndex"])
        self.assertEqual(data.pastSalIndices[:data.pastLength],  stream['finishedIndices'])
        self.assertEqual(data.salIndices[:data.length],  stream['waitingIndices'])
        self.assertEqual(data.running,  stream['running'])
        self.assertEqual(data.enabled,  stream['enabled'])

    async def test_finished_script_state_info(self):

        """
        Test the state of a script is properly obtained once it reaches the DONE state.
        This tests callbacks for the following events:
        - ScriptQueue.evt_script
        - Script.evt_metadata
        - Script.evt_state
        - Script.evt_description
        """
        # Arrange
        async def producer_cor(target_salindex):
            while True:
                message = await self.message_queue.get()
                stream = utils.get_stream_from_last_message(message, 'event', 'ScriptQueueState', 1, 'stream')
                if(len(stream['finished_scripts']) > 0 and stream['finished_scripts'][0]["index"] == int(target_salindex)):
                    return stream

        async def helper_evt_script_cor(target_salindex):
            while True:
                # there is no warranty of when the remote will be updated
                # so better wait for it
                data = await self.remote.evt_script.next(flush=True)
                if ScriptProcessState(data.processState).name == 'DONE' and ScriptState(data.scriptState).name == 'DONE':
                    return data

        async def helper_evt_state(script_remote):
            while True:
                data = await script_remote.evt_state.next(flush=False)
                if(data.lastCheckpoint == "end"):
                    return data

        ack = await self.remote.cmd_add.set_start(isStandard=True,
                                                  path="script1",
                                                  config="wait_time: 0.1",
                                                  location=Location.FIRST,
                                                  locationSalIndex=0,
                                                  descr="test_add", timeout=5)

        script_remote = salobj.Remote(self.queue.domain, 'Script', int(ack.result))

        producer_task = asyncio.create_task(producer_cor(ack.result))
        helper_evt_script_task = asyncio.create_task(helper_evt_script_cor(ack.result))
        state_task = asyncio.create_task(helper_evt_state(script_remote))
        # Act
        [message, data, state] = await asyncio.gather(
            producer_task,
            helper_evt_script_task,
            state_task,
        )
        # TODO
        # checkpoints = await script_remote.evt_checkpoints.next(flush=False)
        metadata = await script_remote.evt_metadata.next(flush=False)
        description = await script_remote.evt_description.next(flush=False)

        # # Assert
        finished_script = message['finished_scripts'][0]
        expected_script = {
            "index": data.salIndex,
            "type": "standard" if data.isStandard else "external",
            "path": data.path,
            "process_state": ScriptProcessState(data.processState).name,
            "script_state": ScriptState(data.scriptState).name,
            "timestampConfigureEnd": data.timestampConfigureEnd,
            "timestampConfigureStart": data.timestampConfigureStart,
            "timestampProcessEnd": data.timestampProcessEnd,
            "timestampProcessStart": data.timestampProcessStart,
            "timestampRunStart": data.timestampRunStart,

            "expected_duration": metadata.duration,
            "last_checkpoint": state.lastCheckpoint,
            # TODO "pause_checkpoints": checkpoints.pause,
            # TODO "stop_checkpoints": checkpoints.stop,
            "description": description.description,
            "classname": description.classname,
            "remotes": description.remotes,
        }

        self.assertEqual(expected_script, finished_script)

    async def test_waiting_and_current_scripts_state_info(self):

        # Arrange

        # - Sends 5 scripts, the third one should be longer
        # - Store  their remotes

        durations = [0.1, 0.1, 100000, 0.1, 0.1]
        remotes = []

        for duration in durations:
            ack = await self.remote.cmd_add.set_start(isStandard=True,
                                                      path="script1",
                                                      config="wait_time: {}".format(duration),
                                                      location=Location.LAST,
                                                      locationSalIndex=0,
                                                      descr="test_add", timeout=5)

            remotes.append(salobj.Remote(self.queue.domain, 'Script', int(ack.result)))

        # - wait for the queue to reach a state where the third script  is the current script and it is running
        async def wait_salindex_tobe_current(target_salindex):
            while True:
                # self.remote.evt_queue.flush()
                # await self.remote.cmd_showQueue.start()
                data = await self.remote.evt_queue.next(flush=False)
                if data.currentSalIndex == target_salindex:
                    return data

        async def wait_for_script_tobe_running(target_index):
            while True:
                self.remote.evt_script.flush()
                await self.remote.cmd_showScript.set_start(salIndex=target_index)
                script_data = await self.remote.evt_script.next(flush=False)

                if ScriptProcessState(script_data.processState).name != 'RUNNING':
                    continue
                if ScriptState(script_data.scriptState).name != 'RUNNING':
                    continue
                return script_data

        # Act
        queue_state = await wait_salindex_tobe_current(remotes[2].salinfo.index)
        script_state = await wait_for_script_tobe_running(remotes[2].salinfo.index)

        # - get the data from the producer
        async def producer_cor(target_salindex):
            while True:
                message = await self.message_queue.get()
                stream = utils.get_stream_from_last_message(message, 'event', 'ScriptQueueState', 1, 'stream')
                if('index' in stream['current'] and stream['current']["index"] == int(target_salindex) and stream['current']['script_state'] == 'RUNNING' and stream['current']['process_state'] == 'RUNNING'):
                    return stream

        stream = await producer_cor(remotes[2].salinfo.index)
        all_scripts = {s["index"]: s for s in [stream['current'], *stream['waiting_scripts']]}

        # Assert

        async def helper_evt_state(script_remote, target_value):
            while True:
                data = await script_remote.evt_state.next(flush=False)
                if(data.lastCheckpoint == target_value):
                    return data
        # - build expected data from evt_script data, evt_metadata, evt_description, evt_state without flushing
        expected_scripts = []
        for [expected_evt_state, remote] in zip(["start", None, None], remotes[2:]):
            # clean and set evt script
            self.remote.evt_script.flush()
            ack = await self.remote.cmd_showScript.set_start(salIndex=remote.salinfo.index)

            # get the data
            data = await self.remote.evt_script.next(flush=False)
            metadata = await remote.evt_metadata.next(flush=False)
            state = await helper_evt_state(remote, expected_evt_state) if expected_evt_state is not None else None
            description = await remote.evt_description.next(flush=False)
            import pdb; pdb.set_trace()

            # build it
            expected_last_checkpoint = '' if expected_evt_state is None else state.lastCheckpoint
            expected_scripts.append({
                "index": data.salIndex,
                "type": "standard" if data.isStandard else "external",
                "path": data.path,
                "process_state": ScriptProcessState(data.processState).name,
                "script_state": ScriptState(data.scriptState).name,
                "timestampConfigureEnd": data.timestampConfigureEnd,
                "timestampConfigureStart": data.timestampConfigureStart,
                "timestampProcessEnd": data.timestampProcessEnd,
                "timestampProcessStart": data.timestampProcessStart,
                "timestampRunStart": data.timestampRunStart,

                "expected_duration": metadata.duration,
                "last_checkpoint": expected_last_checkpoint,
                # TODO "pause_checkpoints": checkpoints.pause,
                # TODO "stop_checkpoints": checkpoints.stop,
                "description": description.description,
                "classname": description.classname,
                "remotes": description.remotes,
            })

        # - assert it
        for expected_script in expected_scripts:
            produced_script = all_scripts[expected_script["index"]]
            self.assertEqual(expected_script, produced_script)

    async def wait_queue_state(self, enabled=True, running=True, currentSalIndex=0, waiting=[], finished=[]):
        """ Waits until the queue evt pops a certain state """
        while True:
            state = await self.remote.evt_queue.next(flush=False)
            if state.running != running:
                print('notrunning ', state.running,  running)
                continue

            if state.enabled != enabled:
                print('notenabled ', state.enabled,  enabled)
                continue

            if state.currentSalIndex != currentSalIndex:
                print('not currentSalIndex', state.currentSalIndex,  currentSalIndex)
                continue

            if state.length != len(waiting):
                print('not length', state.length)
                continue
            if state.salIndices[:state.length] != waiting:
                print('not salIndices', state.salIndices[:state.length],  waiting)
                continue

            if state.pastLength != len(finished):
                print('not pastLength', state.pastLength)
                continue
            if state.pastSalIndices[:state.pastLength] != finished:
                print('not pastSalIndices', state.pastSalIndices[:state.pastLength],  finished)
                continue

            print('all okay', enabled, running, currentSalIndex, waiting, finished)
            return state

    async def wait_for_empty_message_queue(self, message_queue):
        if message_queue == None :
            message_queue = self.message_queue

        messages = []
        while not message_queue.empty():
            messages.append(await message_queue.get())
        return messages

    async def wait_script_state(self):
        pass