import asyncio
import time
import threading
from lsst.ts.scriptqueue import ui
from lsst.ts import salobj
import SALPY_Script
import json

from lsst.ts import salobj
from lsst.ts.scriptqueue import ScriptProcessState ,ScriptState
from lsst.ts.scriptqueue.base_script import HEARTBEAT_INTERVAL
import SALPY_ScriptQueue
import SALPY_Script
import asyncio
import pprint
from utils import NumpyEncoder
import logging
import datetime


class ScriptQueueProducer:
    def __init__(self, loop, send_state):
        # self.queue = ui.RequestModel(1)
        self.log = logging.getLogger(__name__)
        self.send_state = send_state
        self.loop = loop
        self.scripts_remotes = {}
        self.scripts_durations = {}
        self.max_lost_heartbeats = 5
        self.heartbeat_timeout = 3*HEARTBEAT_INTERVAL
        self.state = {
            "available_scripts": [],
            "running": False,
            "waitingIndices": [],
            "currentIndex": 0,
            "finishedIndices": [],
            "enabled": False,
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
            self.log.warning('could not get sate of the queue')
            return

        self.query_available_scripts()
    
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
            if not salindex in self.scripts or not self.scripts[salindex]["setup"]: 
                self.setup_script(salindex)
                self.query_script_info(salindex)        
       
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
                    "type": "external",
                    "path": script_path
                }
            )    
    
    def queue_script_callback(self, event):
        """
            Callback for the queue.evt_script event
        """
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
        self.scripts[salindex]["setup"] = True

        self.set_callback(remote.evt_metadata, lambda ev: self.script_metadata_callback(salindex, ev))
        self.set_callback(remote.evt_state, lambda ev: self.script_state_callback(salindex, ev))
        self.set_callback(remote.evt_description, lambda ev: self.script_description_callback(salindex, ev))

        if not salindex in self.state["finishedIndices"]:
            self.run(self.monitor_script_heartbeat(salindex))


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
            "path": default,
            "lost_heartbeats": 0,
            "setup": False, # flag to trigger show_script only once,
            "last_heartbeat_timestamp": 0
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

        state['max_lost_heartbeats'] = self.max_lost_heartbeats
        state['heartbeat_timeout'] = self.heartbeat_timeout

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
    def get_heartbeat_message(self, salindex):

        heartbeat = {
            'script_heartbeat':{
                'salindex': salindex,
                'lost': self.scripts[salindex]["lost_heartbeats"],
                "last_heartbeat_timestamp": self.scripts[salindex]["last_heartbeat_timestamp"]
            }
        }        

        message = {
            'category': 'event',
            'data': {
                'ScriptQueueState': json.dumps({'stream': heartbeat}, cls=NumpyEncoder)
            }
        }
        return message


    def run(self, task):
        
        if(asyncio.iscoroutine(task)):
            asyncio.run_coroutine_threadsafe(task, self.loop)
        elif asyncio.isfuture(task):
            asyncio.gather(task, loop=self.loop)
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
            self.log.error(e,exc_info=True)
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

    def query_available_scripts(self):
        """
            Sends commands to the queue to trigger the queue.evt_availableScripts 
        """

        self.run(self.queue.cmd_showAvailableScripts.start(timeout=self.cmd_timeout))


    async def monitor_script_heartbeat(self, salindex):
        nlost_subsequent = 0
        while True:
            if self.scripts[salindex]['process_state']  in ['DONE', 'STOPPED', 'FAILED']:
                break
            try:
                await self.scripts[salindex]['remote'].evt_heartbeat.next(flush=False, timeout=self.heartbeat_timeout)
                nlost_subsequent = 0
                self.scripts[salindex]["last_heartbeat_timestamp"] = datetime.datetime.now().timestamp()
            except asyncio.TimeoutError:
                nlost_subsequent += 1
            self.scripts[salindex]["lost_heartbeats"] = nlost_subsequent
            self.send_state(self.get_heartbeat_message(salindex))
            