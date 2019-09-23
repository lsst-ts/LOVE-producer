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
            "available_scripts": []
        }
        self.setup()

    def setup(self):
        self.queue = salobj.Remote(domain=self.domain, name="ScriptQueue", index=self.salindex)

        self.set_callback(self.queue.evt_availableScripts, self.callback_available_scripts)

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

    # ---- Message creation ------

    def get_state_message(self):
        """Parses the current state into a LOVE friendly format"""

        message = onemsg_generator('event','ScriptQueue', self.salindex, {'stream': self.state} )
        return message

