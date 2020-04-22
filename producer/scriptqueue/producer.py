import math
import asyncio
import json
import datetime
from lsst.ts import salobj
from utils import onemsg_generator
from lsst.ts.idl.enums.ScriptQueue import ScriptProcessState
from lsst.ts.idl.enums.Script import ScriptState
from lsst.ts.salobj.base_script import HEARTBEAT_INTERVAL
import utils
HEARTBEAT_TIMEOUT = 3 * HEARTBEAT_INTERVAL


class ScriptQueueProducer:
    """
    Listens to several callbacks of the ScriptQueue and Script CSCs
    to build their states and produce messages for the LOVE-manager
    in the 'event-ScriptQueueState-salindex-stream' group."""

    def __init__(self, domain, send_message_callback, index):
        self.domain = domain
        self.send_message_callback = send_message_callback
        self.salindex = index
        self.state = {
            "available_scripts": [],
            "enabled": False,
            "running": False,
            "waitingIndices": [],
            "currentIndex": 0,
            "finishedIndices": [],
        }

        self.initial_data = {}
        self.scripts = {}
        self.cmd_timeout = 60
        self.queue = salobj.Remote(domain=self.domain, name="ScriptQueue", index=self.salindex)
        self.script_remote = salobj.Remote(domain=self.domain, name="Script", index=0)

    async def setup(self):
        # wait for remotes to be ready
        await self.queue.start_task
        await self.script_remote.start_task

        # Setup Queue events callbacks
        self.set_callback(self.queue.evt_availableScripts, self.callback_available_scripts)
        self.set_callback(self.queue.evt_queue, self.callback_queue)
        self.set_callback(self.queue.evt_configSchema, self.callback_config_schema)
        self.set_callback(self.queue.evt_script, self.callback_queue_script)

        # Setup Script events callbacks
        self.set_callback(self.script_remote.evt_metadata, self.callback_script_metadata)
        self.set_callback(self.script_remote.evt_state, self.callback_script_state)
        self.set_callback(self.script_remote.evt_description, self.callback_script_description)
        self.set_callback(self.script_remote.evt_checkpoints, self.callback_script_checkpoints)
        self.set_callback(self.script_remote.evt_logLevel, self.callback_script_logLevel)
        # --- Event callbacks ----

    def setup_script(self, salindex):
        self.scripts[salindex] = self.new_empty_script()
        self.scripts[salindex]["index"] = salindex
        self.scripts[salindex]["setup"] = True
        asyncio.create_task(self.monitor_scripts_heartbeats())

    def new_empty_script(self):
        default = "UNKNOWN"
        return {
            "remote": None,
            "setup": False,  # flag to trigger show_script only once,
            "index": -1,
            "path": default,
            "type": default,
            "process_state": default,
            "script_state": default,
            "timestampConfigureEnd": 0,
            "timestampConfigureStart": 0,
            "timestampProcessEnd": 0,
            "timestampProcessStart": 0,
            "timestampRunStart": 0,
            "expected_duration": 0,
            "last_checkpoint": "",
            "description": "",
            "classname": "",
            "remotes": "",
            "last_heartbeat_timestamp": 0,
            "lost_heartbeats": 0,
            "pause_checkpoints": "",
            "stop_checkpoints": "",
            "log_level": -1
        }
    # --- Event callbacks ----

    def set_callback(self, evt, callback):
        """
            Adds a callback to a salobj event using appending a
            send_message_callback call
        """

        def do_callback_and_send(event):
            callback(event)
            m = self.get_state_message()
            self.send_message_callback(m)
        evt.callback = do_callback_and_send

    def callback_available_scripts(self, event):
        """ Updates the list of available_scripts in the state according
        to the availableScripts event info"""
        self.state["available_scripts"] = []
        for script_path in event.standard.split(':'):
            self.state["available_scripts"].append(
                {
                    "type": "standard",
                    "path": script_path,
                    "configSchema": ""
                }
            )
            self.query_script_config(True, script_path)
        for script_path in event.external.split(':'):
            self.state["available_scripts"].append(
                {
                    "type": "external",
                    "path": script_path,
                    "configSchema": ""
                }
            )
            self.query_script_config(False, script_path)

    def callback_queue(self, event):
        """
        Saves the queue state using the event data and queries the state of each script that does not exist or has not been set up
        """
        self.state["running"] = event.running == 1
        self.state["currentIndex"] = event.currentSalIndex
        self.state["finishedIndices"] = list(
            event.pastSalIndices[:event.pastLength])
        self.state["waitingIndices"] = list(event.salIndices[:event.length])
        self.state["enabled"] = event.enabled == 1

        scripts = [
            *self.state["waitingIndices"],
            *self.state["finishedIndices"]
        ]

        if self.state["currentIndex"] > 0:
            scripts.append(self.state["currentIndex"])

        for salindex in scripts:
            if salindex not in self.scripts or not self.scripts[salindex]["setup"]:
                self.setup_script(salindex)

    def callback_config_schema(self, event):
        event_script_type = "external"
        if event.isStandard:
            event_script_type = "standard"
        for script in self.state["available_scripts"]:

            if script['path'] == event.path and script['type'] == event_script_type:
                script['configSchema'] = event.configSchema
                break

    def callback_queue_script(self, event):
        """
            Callback for the queue.evt_script event
        """
        if(event.salIndex not in self.scripts):
            self.scripts[event.salIndex] = self.new_empty_script()

        self.scripts[event.salIndex]["type"] = "standard" if event.isStandard else "external"
        self.scripts[event.salIndex]["path"] = event.path
        self.scripts[event.salIndex]["process_state"] = ScriptProcessState(event.processState).name
        self.scripts[event.salIndex]["script_state"] = ScriptState(event.scriptState).name
        self.scripts[event.salIndex]["timestampConfigureEnd"] = event.timestampConfigureEnd
        self.scripts[event.salIndex]["timestampConfigureStart"] = event.timestampConfigureStart
        self.scripts[event.salIndex]["timestampProcessEnd"] = event.timestampProcessEnd
        self.scripts[event.salIndex]["timestampProcessStart"] = event.timestampProcessStart
        self.scripts[event.salIndex]["timestampRunStart"] = event.timestampRunStart

    def callback_script_metadata(self, event):
        """
            Callback for the logevent_metadata. Used to extract
            the expected duration of the script.

            event : SALPY_Script.Script_logevent_metadataC
        """
        salindex = event.ScriptID
        self.scripts[salindex]["expected_duration"] = event.duration

    def callback_script_state(self, event):
        """
            Callback for the Script_logevet_state event. Used to update
            the state of the script.

            event : SALPY_Script.Script_logevent_stateC
        """
        salindex = event.ScriptID
        self.scripts[salindex]["script_state"] = ScriptState(event.state).name
        self.scripts[salindex]["last_checkpoint"] = event.lastCheckpoint

    def callback_script_description(self, event):
        """
            Callback for the logevent_description. Used to extract
            the expected duration of the script.

            event : SALPY_Script.Script_logevent_descriptionC
        """
        salindex = event.ScriptID
        self.scripts[salindex]["description"] = event.description
        self.scripts[salindex]["classname"] = event.classname
        self.scripts[salindex]["remotes"] = event.remotes

    def callback_script_checkpoints(self, event):
        """
            Callback for the logevent_description. Used to extract
            the expected duration of the script.

            event : SALPY_Script.Script_logevent_descriptionC
        """
        salindex = event.ScriptID
        self.scripts[salindex]["pause_checkpoints"] = event.pause
        self.scripts[salindex]["stop_checkpoints"] = event.stop

    def callback_script_logLevel(self, event):
        """ Listens to the logLevel event"""
        salindex = event.ScriptID
        self.scripts[salindex]["log_level"] = event.level
    # ---- Message creation ------

    def parse_script(self, script):
        return {
            "index": script['index'],
            "path": script["path"],
            "type": script["type"],
            "process_state": script["process_state"],
            "script_state": script["script_state"],
            "timestampConfigureEnd": script["timestampConfigureEnd"],
            "timestampConfigureStart": script["timestampConfigureStart"],
            "timestampProcessEnd": script["timestampProcessEnd"],
            "timestampProcessStart": script["timestampProcessStart"],
            "timestampRunStart": script["timestampRunStart"],
            "expected_duration": script["expected_duration"],
            "last_checkpoint": script["last_checkpoint"],
            "description": script["description"],
            "classname": script["classname"],
            "remotes": script["remotes"],
            "pause_checkpoints": script["pause_checkpoints"],
            "stop_checkpoints": script["stop_checkpoints"],
            "log_level": script["log_level"]

        }

    def get_state_message(self):
        """Parses the current state into a LOVE friendly format"""
        stream = {
            'enabled': self.state['enabled'],
            'running': self.state['running'],
            'available_scripts': self.state['available_scripts'],
            'waitingIndices': self.state['waitingIndices'],
            'finishedIndices': self.state['finishedIndices'],
            'currentIndex': self.state['currentIndex'],
            # 'scripts': [self.parse_script(self.scripts[index]) for index in self.scripts],
            'finished_scripts': [self.parse_script(self.scripts[index]) for index in self.state['finishedIndices']],
            'waiting_scripts': [self.parse_script(self.scripts[index]) for index in self.state['waitingIndices']],
            'current': self.parse_script(self.scripts[self.state['currentIndex']]) if self.state['currentIndex'] > 0 else 'None',

        }
        message = onemsg_generator('event', 'ScriptQueueState', self.salindex, {'stream': stream})
        return message

    # --------- SAL queries ---------

    async def query_script_info(self, salindex):
        """
            Send commands to the queue to trigger the script events of each script
        """
        try:
            await self.queue.cmd_showScript.set_start(salIndex=salindex, timeout=self.cmd_timeout)
        except salobj.AckError as ack_err:
            print(f"Could not get info on script {salindex}. "
                  f"Failed with ack.result={ack_err.ack.result}")

    def query_script_config(self, isStandard, script_path):
        """
            Send command to the queue to trigger the script config event
        """
        try:
            asyncio.create_task(self.queue.cmd_showSchema.set_start(
                isStandard=isStandard, path=script_path, timeout=self.cmd_timeout))
        except salobj.AckError as ack_err:
            print(f"Could not get info on script {script_path}. "
                  f"Failed with ack.result={ack_err.ack.result}")

    async def update(self):
        """
            Tries to trigger the queue event which will
            update all the info in the queue and its scripts
            if succeeds.
        """

        try:
            await self.queue.cmd_showQueue.start(timeout=self.cmd_timeout)
            await self.queue.cmd_showAvailableScripts.start(timeout=self.cmd_timeout)
            for script_index in self.scripts:
                await self.queue.cmd_showScript.set_start(salIndex=script_index)

            return True
        except Exception as e:
            print(e)
            return False

    # ----------HEARTBEATS---------

    def get_heartbeat_message(self, salindex):
        heartbeat = {
            'script_heartbeat': {
                'salindex': salindex,
                'lost': self.scripts[salindex]["lost_heartbeats"],
                "last_heartbeat_timestamp": self.scripts[salindex]["last_heartbeat_timestamp"]
            }
        }
        message = {
            'category': 'event',
            'data': [
                {
                    'csc': 'ScriptHeartbeats',
                    'salindex': self.salindex,
                    'data': json.loads(json.dumps({'stream': heartbeat}, cls=utils.NumpyEncoder))
                }
            ]
        }
        return message

    async def monitor_scripts_heartbeats(self):
        while True:
            try:
                script_data = await self.script_remote.evt_heartbeat.next(flush=True, timeout=HEARTBEAT_TIMEOUT)
            except asyncio.TimeoutError:
                for salindex in self.scripts:
                    self.scripts[salindex]["lost_heartbeats"] += 1
                    self.send_message_callback(self.get_heartbeat_message(salindex))
                continue
            
            received_heartbeat_salindex = script_data.ScriptID
            if received_heartbeat_salindex not in self.scripts:
                continue

            # send currently received heartbeat
            current_timestamp = datetime.datetime.now().timestamp()
            self.scripts[received_heartbeat_salindex]["last_heartbeat_timestamp"] = current_timestamp
            self.scripts[received_heartbeat_salindex]["lost_heartbeats"] = 0
            self.send_message_callback(self.get_heartbeat_message(received_heartbeat_salindex))
            # https://github.com/lsst-ts/LOVE-producer/issues/53
            # self.scripts[salindex]["last_heartbeat_timestamp"] = script_data.private_sndStamp

            # check others heartbeats
            for salindex in self.scripts:
                script = self.scripts[salindex]
                if salindex == received_heartbeat_salindex:
                    continue

                # count how many beats were lost since last timestamp
                nlost_heartbeats = (current_timestamp - script["last_heartbeat_timestamp"])/HEARTBEAT_TIMEOUT
                nlost_heartbeats = math.floor(nlost_heartbeats)

                # send it if nlost increased
                if nlost_heartbeats > script["lost_heartbeats"]:
                    self.scripts[salindex]["lost_heartbeats"]=nlost_heartbeats
                    self.send_message_callback(self.get_heartbeat_message(salindex))
