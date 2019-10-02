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
        self.cmd_timeout = 60

        self.queue = salobj.Remote(domain=self.domain, name="ScriptQueue", index=self.salindex)

        self.set_callback(self.queue.evt_availableScripts, self.callback_available_scripts)
        self.set_callback(self.queue.evt_queue, self.callback_queue)
        self.set_callback(self.queue.evt_configSchema, self.callback_config_schema)

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

        # scripts = [
        #     *self.state["waitingIndices"],
        #     *self.state["finishedIndices"]
        # ]

        # if self.state["currentIndex"] > 0:
        #     scripts.append(self.state["currentIndex"])

        # for salindex in scripts:
        #     if salindex not in self.scripts or not self.scripts[salindex]["setup"]:
        #         self.setup_script(salindex)
        #         self.query_script_info(salindex)
    
    def callback_config_schema(self, event):
        event_script_type = "external"
        if event.isStandard: 
            event_script_type = "standard"
        for script in self.state["available_scripts"]:

            if script['path'] == event.path and script['type'] == event_script_type :
                script['configSchema'] = event.configSchema
                break

    # ---- Message creation ------

    def get_state_message(self):
        """Parses the current state into a LOVE friendly format"""

        stream = {
            'enabled': self.state['enabled'],
            'running': self.state['running'],
            'available_scripts': self.state['available_scripts'],
            'waitingIndices': self.state['waitingIndices'],
            'finishedIndices': self.state['finishedIndices'],
            'currentIndex': self.state['currentIndex'],

        }
        message = onemsg_generator('event','ScriptQueue', self.salindex, {'stream': stream} )
        return message

    # --------- SAL queries ---------
    def query_script_config(self, isStandard, script_path):
        """
            Send command to the queue to trigger the script config event
        """
        try:
            asyncio.create_task(self.queue.cmd_showSchema.set_start(isStandard=isStandard, path=script_path, timeout=self.cmd_timeout))
        except salobj.AckError as ack_err:
            print(f"Could not get info on script {script_path}. "
                  f"Failed with ack.result={ack_err.ack.result}")
