import asyncio
from lsst.ts import salobj
from utils import onemsg_generator
from lsst.ts.idl.enums.ScriptQueue import ScriptProcessState
from lsst.ts.idl.enums.Script import ScriptState


class ScriptQueueProducer:
    """
    Listens to several callbacks of the ScriptQueue and Script CSCs
    to build their states and to produce messages for the LOVE-manager
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
        self.scripts = {}
        self.cmd_timeout = 60

        self.queue = salobj.Remote(domain=self.domain, name="ScriptQueue", index=self.salindex)

        self.set_callback(self.queue.evt_availableScripts, self.callback_available_scripts)
        self.set_callback(self.queue.evt_queue, self.callback_queue)
        self.set_callback(self.queue.evt_configSchema, self.callback_config_schema)
        self.set_callback(self.queue.evt_script, self.callback_queue_script)

    def setup_script(self, salindex):
        self.scripts[salindex] = self.new_empty_script()

        remote = salobj.Remote(domain=self.domain, name="Script", index=salindex)
        self.scripts[salindex]["index"] = salindex
        self.scripts[salindex]["remote"] = remote
        self.scripts[salindex]["setup"] = True

        self.set_callback(remote.evt_metadata, lambda ev: self.callback_script_metadata(salindex, ev))
        self.set_callback(remote.evt_state, lambda ev: self.callback_script_state(salindex, ev))
        self.set_callback(remote.evt_description, lambda ev: self.callback_script_description(salindex, ev))

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
            "description": "",
            "classname": "",
            "remotes": ""
        }
    # --- Event callbacks ----

    def set_callback(self, evt, callback):
        """
            Adds a callback to a salobj event using appending a 
            send_message_callback call
        """

        def do_callback_and_send(event):
            callback(event)
            self.send_message_callback(self.get_state_message())

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
                # self.query_script_info(salindex)

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

    def callback_script_metadata(self, salindex, event):
        """
            Callback for the logevent_metadata. Used to extract
            the expected duration of the script.

            event : SALPY_Script.Script_logevent_metadataC
        """
        self.scripts[salindex]["expected_duration"] = event.duration

    def callback_script_state(self, salindex, event):
        """
            Callback for the Script_logevet_state event. Used to update
            the state of the script.

            event : SALPY_Script.Script_logevent_stateC
        """
        self.scripts[salindex]["script_state"] = ScriptState(event.state).name
        self.scripts[salindex]["last_checkpoint"] = event.lastCheckpoint

    def callback_script_description(self, salindex, event):
        """
            Callback for the logevent_description. Used to extract
            the expected duration of the script.

            event : SALPY_Script.Script_logevent_descriptionC
        """
        self.scripts[salindex]["description"] = event.description
        self.scripts[salindex]["classname"] = event.classname
        self.scripts[salindex]["remotes"] = event.remotes

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
            'scripts': [self.parse_script(self.scripts[index]) for index in self.scripts],
            'finished_scripts': [self.parse_script(self.scripts[index]) for index in self.state['finishedIndices']]

        }
        message = onemsg_generator('event', 'ScriptQueue', self.salindex, {'stream': stream})
        return message

    # --------- SAL queries ---------
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
