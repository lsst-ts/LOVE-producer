import asyncio
import datetime
import json
import logging
from lsst.ts import salobj
from lsst.ts.salobj.base_script import HEARTBEAT_INTERVAL
from lsst.ts.idl.enums.ScriptQueue import ScriptProcessState
from lsst.ts.idl.enums.Script import ScriptState
from utils import NumpyEncoder


class ScriptQueueProducer:
    def __init__(self, domain, send_state, index):
        self.log = logging.getLogger(__name__)
        self.send_state = send_state
        self.domain = domain
        self.scripts_remotes = {}
        self.scripts_durations = {}
        self.max_lost_heartbeats = 5
        self.heartbeat_timeout = 3 * HEARTBEAT_INTERVAL
        self.state = {
            "available_scripts": [],
            "running": False,
            # "waitingIndices": [],
            # "currentIndex": 0,
            # "finishedIndices": [],
            # "enabled": False,
        }
        self.cmd_timeout = 120
        self.scripts = {}
        self.index = index
        self.setup()
        self.update()

    def setup(self):
        # create queue remote
        print('- Setting up ScriptQueue ', self.index)
        domain = self.domain
        self.queue = salobj.Remote(domain=domain, name="ScriptQueue", index=self.index)

        self.set_callback(self.queue.evt_queue, self.queue_callback)
        self.set_callback(self.queue.evt_availableScripts, self.available_scripts_callback)
        self.set_callback(self.queue.evt_script, self.queue_script_callback)
        self.set_callback(self.queue.evt_configSchema, self.config_schema_callback)

    def set_callback(self, evt, callback):
        """
            Adds an event callback to an event using the asyncio event loop
            and appends a send instruction
        """
        def do_callback_and_send(event):
            callback(event)
            self.send_state(self.get_state_message())

        evt.callback = do_callback_and_send

    def update(self):
        """
            Tries to trigger the queue event which will
            update all the info in the queue and its scripts
            if succeeds.
        """
        if self.query_queue_state() < 0:
            self.log.warning('could not get sate of the queue')
            return
        self.query_available_scripts()

    def queue_callback(self, event):
        self.state["running"] = event.running == 1
        self.state["finishedIndices"] = list(
            event.pastSalIndices[:event.pastLength])
        self.state["waitingIndices"] = list(event.salIndices[:event.length])
        self.state["currentIndex"] = event.currentSalIndex
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
                self.query_script_info(salindex)

        # a script in the producer that is not in the queue
        # is a sign of a queue restart
        for salindex in list(self.scripts):
            if salindex not in scripts:
                del self.scripts[salindex]

    def available_scripts_callback(self, event):
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

    def queue_script_callback(self, event):
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

    def config_schema_callback(self, event):
        # print('config_schema_callback\n\n\n\n\n')
        # print(event.configSchema)
        for script in self.state["available_scripts"]:
            if (script['type'] == "standard") == event.isStandard:
                if script['path'] == event.path:
                    script['configSchema'] = event.configSchema
                    break

    def setup_script(self, salindex):
        domain = self.domain
        remote = salobj.Remote(domain=domain, name="Script", index=salindex)

        self.scripts[salindex] = self.new_empty_script()
        self.scripts[salindex]["index"] = salindex
        self.scripts[salindex]["remote"] = remote
        self.scripts[salindex]["setup"] = True

        self.set_callback(
            remote.evt_metadata, lambda ev: self.script_metadata_callback(salindex, ev))
        self.set_callback(remote.evt_state, lambda ev: self.script_state_callback(salindex, ev))
        self.set_callback(remote.evt_checkpoints, lambda ev: self.script_checkpoints_callback(salindex, ev))
        self.set_callback(
            remote.evt_description, lambda ev: self.script_description_callback(salindex, ev))

        if salindex not in self.state["finishedIndices"]:
            self.run(self.monitor_script_heartbeat(salindex))

    def new_empty_script(self):
        default = "UNKNOWN"
        return {
            "remote": None,
            "index": -1,
            "script_state": default,
            "last_checkpoint": "",
            "pause_checkpoints": "",
            "stop_checkpoints": "",
            "process_state": default,
            "elapsed_time": 0,
            "expected_duration": 0,
            "type": default,
            "path": default,
            "lost_heartbeats": 0,
            "setup": False,  # flag to trigger show_script only once,
            "last_heartbeat_timestamp": 0,
            "timestampConfigureEnd": 0,
            "timestampConfigureStart": 0,
            "timestampProcessEnd": 0,
            "timestampProcessStart": 0,
            "timestampRunStart": 0,
            "description": "",
            "classname": "",
            "remotes": ""
        }

    def script_metadata_callback(self, salindex, event):
        """
            Callback for the logevent_metadata. Used to extract
            the expected duration of the script.

            event : SALPY_Script.Script_logevent_metadataC
        """
        self.scripts[salindex]["expected_duration"] = event.duration

    def script_state_callback(self, salindex, event):
        """
            Callback for the Script_logevet_state event. Used to update
            the state of the script.

            event : SALPY_Script.Script_logevent_stateC
        """
        self.scripts[salindex]["script_state"] = ScriptState(event.state).name
        self.scripts[salindex]["last_checkpoint"] = event.lastCheckpoint

    def script_checkpoints_callback(self, salindex, event):
        """
            Callback for the Script_logevet_state event. Used to update
            the state of the script.

            event : SALPY_Script.Script_logevent_stateC
        """
        self.scripts[salindex]["pause_checkpoints"] = event.pause
        self.scripts[salindex]["stop_checkpoints"] = event.stop

    def script_description_callback(self, salindex, event):
        """
            Callback for the logevent_description. Used to extract
            the expected duration of the script.

            event : SALPY_Script.Script_logevent_descriptionC
        """
        self.scripts[salindex]["description"] = event.description
        self.scripts[salindex]["classname"] = event.classname
        self.scripts[salindex]["remotes"] = event.remotes

    def get_parsed_state(self):
        """
            Parses the current state into a LOVE friendly format
        """
        state = {}
        state['max_lost_heartbeats'] = self.max_lost_heartbeats
        state['heartbeat_timeout'] = self.heartbeat_timeout
        state["available_scripts"] = self.state["available_scripts"].copy()
        state["state"] = "Running" if self.state["running"] else "Stopped"
        state["finished_scripts"] = []

        for index in self.state["finishedIndices"]:
            state["finished_scripts"].append({
                key: self.scripts[index][key] for key in self.scripts[index] if key != "remote"
            })

        state["waiting_scripts"] = []

        for index in self.state["waitingIndices"]:
            state["waiting_scripts"].append({
                key: self.scripts[index][key] for key in self.scripts[index] if key != "remote"
            })

        state["current"] = "None"
        if self.state["currentIndex"] > 0:
            state["current"] = {
                key: self.scripts[self.state["currentIndex"]][key]
                for key in self.scripts[self.state["currentIndex"]] if key != "remote"
            }
        return state

    def get_state_message(self):
        queue_state = self.get_parsed_state()
        message = {
            'category': 'event',
            'data': [
                {
                    'csc': 'ScriptQueueState',
                    'salindex': self.index,
                    'data': json.loads(json.dumps({'stream': queue_state}, cls=NumpyEncoder))
                }
            ]
        }
        return message

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
                    'salindex': self.index,
                    'data': json.loads(json.dumps({'stream': heartbeat}, cls=NumpyEncoder))
                }
            ]
        }
        return message

    def run(self, task):
        asyncio.get_event_loop().create_task(task)

    def query_queue_state(self):
        """
            Triggers the queue event by sending a command.
            Returns 0 if everything is fine; -1 otherwise.
        """
        try:
            self.run(self.queue.cmd_showQueue.start(timeout=self.cmd_timeout))

        except Exception as e:
            self.log.error(e, exc_info=True)
            return -1

        return 0

    def query_script_info(self, salindex):
        """
            Send commands to the queue to trigger the script events of each script
        """
        self.queue.cmd_showScript.set(salIndex=salindex)
        try:
            self.run(self.queue.cmd_showScript.start(timeout=self.cmd_timeout))
        except salobj.AckError as ack_err:
            print(f"Could not get info on script {salindex}. "
                  f"Failed with ack.result={ack_err.ack.result}")

    def query_script_config(self, isStandard, script_path):
        """
            Send command to the queue to trigger the script config event
        """
        self.queue.cmd_showSchema.set(isStandard=isStandard, path=script_path)
        try:
            self.run(self.queue.cmd_showSchema.start(timeout=self.cmd_timeout))
        except salobj.AckError as ack_err:
            print(f"Could not get info on script {script_path}. "
                  f"Failed with ack.result={ack_err.ack.result}")

    def query_available_scripts(self):
        """
            Sends commands to the queue to trigger the queue.evt_availableScripts
        """
        self.run(self.queue.cmd_showAvailableScripts.start(
            timeout=self.cmd_timeout))

    async def monitor_script_heartbeat(self, salindex):
        nlost_subsequent = 0
        while True:
            if self.scripts[salindex]['process_state'] in ['DONE', 'STOPPED', 'FAILED']:
                break
            try:
                await self.scripts[salindex]['remote'].evt_heartbeat.next(flush=False, timeout=self.heartbeat_timeout)
                nlost_subsequent = 0
                self.scripts[salindex]["last_heartbeat_timestamp"] = datetime.datetime.now(
                ).timestamp()
            except asyncio.TimeoutError:
                nlost_subsequent += 1
            self.scripts[salindex]["lost_heartbeats"] = nlost_subsequent
            self.send_state(self.get_heartbeat_message(salindex))
