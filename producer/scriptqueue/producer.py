import asyncio
from lsst.ts import salobj
from utils import onemsg_generator


class ScriptQueueProducer:
    """Monitors the state of the ScriptQueue and its Script
    and provides interfaces to produce messages for the LOVE-manager"""

    def __init__(self, domain, send_message_callback, index):
        self.domain = domain
        self.send_message_callback = send_message_callback
        self.salindex = index
        self.state = {
            "available_scripts": [],
            # "running": False,
            "waitingIndices": [],
            # "currentIndex": 0,
            # "finishedIndices": [],
            # "enabled": False
        }
        self.queue = salobj.Remote(domain=self.domain, name="ScriptQueue", index=self.salindex)

        self.set_callback(self.queue.evt_availableScripts, self.callback_available_scripts)
        self.set_callback(self.queue.evt_queue, self.callback_queue)

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
            # self.query_script_config(True, script_path)
        for script_path in event.external.split(':'):
            self.state["available_scripts"].append(
                {
                    "type": "external",
                    "path": script_path,
                    "configSchema": ""
                }
            )
            # self.query_script_config(False, script_path)

    def callback_queue(self, event):
        """
        Saves the queue state using the event data and queries the state of each script that does not exist or has not been set up
        """
        # self.state["running"] = event.running == 1
        self.state["currentIndex"] = event.currentSalIndex
        # self.state["finishedIndices"] = list(
        #     event.pastSalIndices[:event.pastLength])
        # self.state["waitingIndices"] = list(event.salIndices[:event.length])
        # self.state["enabled"] = event.enabled == 1

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

    # ---- Message creation ------

    def get_state_message(self):
        """Parses the current state into a LOVE friendly format"""

        message = onemsg_generator('event','ScriptQueue', self.salindex, {'stream': self.state} )
        return message

