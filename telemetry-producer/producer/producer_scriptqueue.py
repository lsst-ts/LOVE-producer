import asyncio
import time
import threading
from lsst.ts.scriptqueue import ui
from lsst.ts import salobj
import SALPY_Script
import json

from lsst.ts import salobj
from lsst.ts.scriptqueue import ScriptProcessState ,ScriptState
import SALPY_ScriptQueue
import SALPY_Script
import asyncio
import pprint
from utils import NumpyEncoder


class ScriptQueueProducer:
    def __init__(self, loop, send_state):
        # self.queue = ui.RequestModel(1)
        self.send_state = send_state
        self.loop = loop
        self.scripts_remotes = {}
        self.scripts_durations = {}
        self.state = {
            "available_scripts": [],
            "running": False,
            "waitingIndices": [],
            "currentIndex": 0,
            "finishedIndices": [],
            "enabled": False
        }

        self.cmd_timeout = 120

        self.scripts = {}

        print('will setup')
        self.setup()

        print('will update')
        self.update()

    def setup(self):
        # create queue remote

        self.queue = salobj.Remote(SALPY_ScriptQueue, 1)        

        self.set_callback(self.queue.evt_queue, self.queue_callback)
        self.set_callback(self.queue.evt_availableScripts, self.available_scripts_callback)
        self.set_callback(self.queue.evt_script, self.queue_script_callback)


        # self.queue.evt_heartbeat.callback = lambda x : print('callback called heartbeat')
        # self.set_callback(self.queue.evt_heartbeat, lambda x: print('callback called heartbeat'))

        # set queue callbacks
        

    def set_callback(self, evt, callback):
        """
            Adds an event callback to an event using the asyncio event loop
            and appends a send instruction
        """
        def do_callback_and_send(event):
            callback(event)
            self.send_state(self.get_state_message())


        def setter():
            evt.callback = do_callback_and_send

        self.loop.call_soon_threadsafe( setter)
    
    def update(self):
        """
            Tries to trigger the queue event which will
            update all the info in the queue and its scripts
            if succeeds.
        """
        print('updating')

        if self.query_queue_state() < 0:
            print('could not get sate of the queue')
            return

        self.query_available_scripts()
        

    def available_scripts_callback(self, event):       
        self.state["available_scripts"] = []

        for script_path in event.standard.split(':'):
            self.state["available_scripts"].append(
                {
                    "type": "standard",
                    "path": script_path
                }
            )
        for script_path in event.external.split(':'):
            self.state["available_scripts"].append(
                {
                    "type": "standard",
                    "path": script_path
                }
            )    
    def queue_script_callback(self, event):
        if(not event.salIndex in self.scripts):
            self.scripts[event.salIndex] = self.new_empty_script()

        self.scripts[event.salIndex]["elapsed_time"] = event.duration
        self.scripts[event.salIndex]["type"] = "standard" if event.isStandard else "external"
        self.scripts[event.salIndex]["path"] = event.path
        self.scripts[event.salIndex]["process_state"] = ScriptProcessState(event.processState).name
        self.scripts[event.salIndex]["script_state"] = ScriptState(event.scriptState).name
    
    def setup_script(self, salindex):
        remote = salobj.Remote(SALPY_Script, salindex)

        self.scripts[salindex] = self.new_empty_script()
        self.scripts[salindex]["index"] = salindex
        self.scripts[salindex]["remote"] = remote

        self.set_callback(remote.evt_metadata, lambda ev: self.script_metadata_callback(salindex, ev))
        self.set_callback(remote.evt_state, lambda ev: self.script_state_callback(salindex, ev))
        self.set_callback(remote.evt_description, lambda ev: self.script_description_callback(salindex, ev))

    def queue_callback(self, event):
        self.state["running"] =  event.running == 1
        self.state["finishedIndices"] =  list(event.pastSalIndices[:event.pastLength])
        self.state["waitingIndices"] =  list(event.salIndices[:event.length])
        self.state["currentIndex"] = event.currentSalIndex
        self.state["enabled"] = event.enabled == 1

        scripts = [
            *self.state["waitingIndices"], 
            *self.state["finishedIndices"]
        ]

        if self.state["currentIndex"] > 0:
            scripts.append(self.state["currentIndex"] )
        
        for salindex in scripts:
            if not salindex in self.scripts: 
                self.setup_script(salindex)

        self.query_scripts_info()        

    def new_empty_script(sef):
        default = "UNKNOWN"
        return {
            "remote": None,
            "index": -1,
            "script_state": default,
            "process_state": default,
            "elapsed_time": 0,
            "expected_duration": 0,
            "type": default,
            "path": default
        }        

    def parse_script(self, script):
        new_script = {**script}
        new_script['index'] = int(new_script['index'])
        for name in discard:
            del new_script[name]
        return new_script


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

    def script_description_callback(self, salindex, event):
        pass

    def get_parsed_state(self):
        """
            Parses the current state into a LOVE friendly format
        """
        state = {}

        state["available_scripts"] = self.state["available_scripts"].copy()

        state["state"] = "Running" if self.state["running"] else "Stopped"


        state["finished_scripts"] = []

        for index in self.state["finishedIndices"]:
            state["finished_scripts"].append({
                key: self.scripts[index][key]  for key in self.scripts[index] if key != "remote"
            })

        state["waiting_scripts"] = []

        for index in self.state["waitingIndices"]:
            state["waiting_scripts"].append({
                key: self.scripts[index][key] for key in self.scripts[index] if key != "remote"
            })

        

        

        state["current"] = "None"
        if self.state["currentIndex"] > 0:
            state["current"] = {
                key: self.scripts[self.state["currentIndex"]][key] for key in self.scripts[self.state["currentIndex"]] if key != "remote"
            }

        return state

    def get_state_message(self):

        queue_state = self.get_parsed_state()

        message = {
            'category': 'event',
            'data': {
                'ScriptQueueState': json.dumps({'stream': queue_state}, cls=NumpyEncoder)
            }
        }
        
        return message

    def run(self, task):
        
        if(asyncio.iscoroutine(task)):
            asyncio.run_coroutine_threadsafe(task, self.loop)
        elif asyncio.isfuture(task):
            asyncio.ensure_future(task, loop=self.loop)
        else:
            print('Unknown task type: ', task)

    def query_queue_state(self):
        """
            Triggers the queue event by sending a command.
            Returns 0 if everything is fine; -1 otherwise.
        """
        try:
            self.run(self.queue.cmd_showQueue.start(timeout=self.cmd_timeout))

        except Exception as e:
            print(e)
            return -1
        
        return 0

    def query_scripts_info(self):
        """
            Send commands to the queue to trigger the script events of each script
        """
        for salindex in self.scripts:
            self.queue.cmd_showScript.set(salIndex=salindex)
            try:
                self.run(self.queue.cmd_showScript.start(timeout=self.cmd_timeout))
            except salobj.AckError as ack_err:
                print(f"Could not get info on script {salindex}. "
                               f"Failed with ack.result={ack_err.ack.result}")

    def query_available_scripts(self):
        """
            Sends commands to the queue to trigger the queue.evt_availableScripts 
        """

        self.run(self.queue.cmd_showAvailableScripts.start(timeout=self.cmd_timeout))
