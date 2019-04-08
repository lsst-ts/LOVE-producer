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
class ScriptQueueProducer:
    def __init__(self, loop, send_state):
        print('creating request model')
        # self.queue = ui.RequestModel(1)
        print('request model created')
        self.send_state = send_state
        self.loop = loop
        self.scripts_remotes = {}
        self.scripts_durations = {}
        self.state = {
            "available": {
                "standard": [],
                "external": []
            },
            "running": 0,
            "waitingIndices": [],
            "currentIndex": -1,
            "finishedIndex": [],
            "enabled": False
        }

        self.scripts = {}

        self.setup()

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
            Adds an event callback using the asyncio event loop
        """
        def setter():
            evt.callback = callback
        self.loop.call_soon_threadsafe( setter)
        
    def update(self):
        # get oldest available

        # get oldest queue

        # get oldest per script in the queue
        pass

    def available_scripts_callback(self, event):
        print('\n\n\navailable scripts')
        
        self.state["available"] = {
            "standard": event.standard.split(':'),
            "external": event.external.split(':')
        }
        print('updated available scripts')
        print(self.state["available"])    
    
    def queue_script_callback(self, event):
        print('\n\nqueue script event')
        print(dir(event))
        

        if(not event.salIndex in self.scripts):
            self.scripts[event.salIndex] = self.new_empty_script()

        self.scripts[event.salIndex]["elapsed_time"] = event.duration
        self.scripts[event.salIndex]["type"] = "standard" if event.isStandard else "external"
        self.scripts[event.salIndex]["path"] = event.path
        self.scripts[event.salIndex]["process_state"] = ScriptProcessState(event.processState).name
        self.scripts[event.salIndex]["script_state"] = ScriptState(event.scriptState).name
        pprint.pprint(self.scripts[event.salIndex])
    
    def setup_script(self, salindex):
        remote = salobj.Remote(SALPY_Script, salindex)

        self.scripts[salindex] = self.new_empty_script()
        self.scripts[salindex]["index"] = salindex
        self.scripts[salindex]["remote"] = remote

        self.set_callback(remote.evt_metadata, lambda ev: self.script_metadata_callback(salindex, ev))
        self.set_callback(remote.evt_state, lambda ev: self.script_state_callback(salindex, ev))
        self.set_callback(remote.evt_description, lambda ev: self.script_description_callback(salindex, ev))

    def queue_callback(self, event):
        # import pdb; pdb.set_trace()
        self.state["running"] =  event.running == 1
        self.state["finished"] =  list(event.pastSalIndices[:event.pastLength])
        self.state["waitingIndices"] =  list(event.salIndices[:event.length])
        self.state["currentIndex"] = event.currentSalIndex
        self.state["enabled"] = event.enabled == 1

        scripts = [*self.state["waitingIndices"], self.state["currentIndex"], *self.state["finished"]]
        
        for salindex in scripts:
            if not salindex in self.scripts: 
                self.setup_script(salindex)

        self.send_state(self.state)

    def new_empty_script(sef):
        default = "UNKNOWN"
        return {
            "remote": None,
            "index": default,
            "script_state": default,
            "process_state": default,
            "elapsed_time": default,
            "expected_duration": default,
            "type": default,
            "path": default
        }        

    def script_metadata_callback(self, salindex, event):
        """
            Callback for the logevent_metadata. Used to extract 
            the expected duration of the script.
            
            event : SALPY_Script.Script_logevent_metadataC 
        """

        self.scripts[salindex]["expected_duration"] = event.duration
        print('\n\n\n expected duration updtaed')
        pprint.pprint(self.scripts[salindex])
    
    def script_state_callback(self, salindex, event):
        """
            Callback for the Script_logevet_state event. Used to update 
            the state of the script.
            
            event : SALPY_Script.Script_logevent_stateC
        """

        self.scripts[salindex]["script_state"] = ScriptState(event.state).name
        print('\n\n\nScript state updated ${salindex}')
        pprint.pprint(self.scripts[salindex])

    def script_description_callback(self, salindex, event):
        print('\n\ndescription:', event, '\n ', event.description)

    # def get_available_scripts(self):
    #     # get available scripts
    #     return self.queue.get_scripts()  
    
    #     self.monitor_script(self.salindex)
            
    # def update_scripts_remotes(self, queue_state):
    #     """
    #         Stores the salobj.Remote object of each script
    #         on the queue
    #     """
    #     for queue_name in ['queue_scripts', 'past_scripts']:   
    #         for salindex in queue_state[queue_name]:
    #             if salindex not in self.scripts_remotes:
    #                 self.scripts_remotes[salindex] = salobj.Remote(SALPY_Script, salindex)    
    #     #TODO: handle current script

    # def update_scripts_durations(self):
    #     """
    #         Updates the expected duration of each script
    #         by checking the latest event data.
    #         This info is available after a script is configured in the
    #         Script_logevent_metadata.
    #     """
    #     for salindex in self.scripts_remotes:
    #         remote = self.scripts_remotes[salindex]
    #         if not salindex in self.scripts_durations:
    #             self.scripts_durations[salindex] = 'UNKNOWN'
    #         # TODO: if durations exists then continue
    #         while True:
    #             info = remote.evt_metadata.get_oldest()
    #             if info is None:
    #                 break
    #             self.scripts_durations[salindex] = info.duration
    
    # def parse_script(self, script):
    #     new_script = {**script}
    #     new_script['index'] = int(new_script['index'])
    #     new_script['script_state'] = new_script['script_state'].name
    #     new_script['process_state'] = new_script['process_state'].name
    #     new_script['elapsed_time'] = new_script['duration']; 
    #     new_script['expected_duration'] = 'UNKNOWN'
    #     if(new_script['index'] in self.scripts_durations):
    #         new_script['expected_duration'] = self.scripts_durations[new_script['index']]
    #     discard = ['duration', 'remote', 'updated']
    #     for name in discard:
    #         del new_script[name]
    #     return new_script

    # def parse_available_script(self, script_path, script_type):
    #     return {
    #         'path': script_path,
    #         'type': script_type
    #     }

    # def parse_queue_state(self):
    #     """
    #         Gets the updated state and returns it in a LOVE-friendly format.
    #     """

    #     # "get_queue_state" makes the update before parsing the state
    #     queue_state = self.queue.get_queue_state() 

    #     # update scripts duration from remote.evt_metadata (this is not in RequestModel)
    #     self.update_scripts_remotes(queue_state)
    #     self.update_scripts_durations()

    #     queue_state['available_scripts'] = [] 
    #     if queue_state['state'] == 'Running':
    #         available_scripts = self.queue.get_scripts()

    #         queue_state['available_scripts'] = map(lambda s: self.parse_available_script(s,'external'), available_scripts['external'])
    #         queue_state['available_scripts'] = list(queue_state['available_scripts'])
    #         queue_state['available_scripts'].extend( list(map(lambda s: self.parse_available_script(s,'standard'), available_scripts['standard'])))
    #         queue_state['available_scripts'] = list(queue_state['available_scripts'])

    #     queue_state['finished_scripts'] = list(queue_state['past_scripts'].values())
    #     queue_state['waiting_scripts'] = list(queue_state['queue_scripts'].values())
    #     del queue_state['past_scripts']
    #     del queue_state['queue_scripts']

    #     for queue_name in ['waiting_scripts', 'finished_scripts']:
    #         queue = queue_state[queue_name]
    #         for i, script in enumerate(queue):
    #             queue[i] = self.parse_script(queue[i])

    #     if queue_state['current'] == None:
    #         queue_state['current'] = 'None'
    #     else:
    #         queue_state['current'] = self.parse_script(queue_state['current'])

    #     return queue_state
    
    # def get_state_message(self):

    #     queue_state = self.parse_queue_state()

    #     message = {
    #         'category': 'event',
    #         'data': {
    #             'ScriptQueueState': json.dumps({'stream': queue_state})
    #         }
    #     }
        
    #     return message