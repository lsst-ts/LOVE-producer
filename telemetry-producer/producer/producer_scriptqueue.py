import asyncio
import time
import threading
from lsst.ts.scriptqueue import ui, ScriptProcessState
from lsst.ts import salobj
import SALPY_Script
import json

class ScriptQueueProducer:
    def __init__(self):
        print('enabling the queue')
        print('queue enabled')
        print('creating request model')
        self.queue = ui.RequestModel(1)
        # self.queue.enable_queue()
        print('request model created')
        queue_state = self.queue.get_queue_state()
        print('got state')
        self.scripts_remotes = {}
        self.scripts_durations = {}

        # run script1 from standard
        #TODO: donde se ven los parametros del config?

    def get_available_scripts(self):
        # get available scripts
        return self.queue.get_scripts()  
    
    def do_run(self):
        script = 'script1'
        is_standard = True
        config = "{wait_time: '10'}"
        self.salindex = self.queue.add(script, is_standard, config)
        print(10*'\n','duration',self.queue.state.scripts[self.salindex]['duration'])

        self.monitor_script(self.salindex)
    
    def monitor_script(self, salindex):
        self.queue.get_script_remote(salindex)

        # print('salindex:', salindex, 'remote:', self.queue.state.scripts[self.salindex]['remote'])

        # t = threading.Thread(target=self.queue.monitor_script(salindex), args=[salindex])
        # t.start()
    
    def update(self):
        self.queue.update_queue_state()
        self.queue.update_scripts_info()

        
    def update_scripts_remotes(self, queue_state):
        """
            Stores the salobj.Remote object of each script
            on the queue
        """
        for queue_name in ['queue_scripts', 'past_scripts']:   
            for salindex in queue_state[queue_name]:
                if salindex not in self.scripts_remotes:
                    self.scripts_remotes[salindex] = salobj.Remote(SALPY_Script, salindex)    
        #TODO: handle current script

    def update_scripts_durations(self):
        """
            Updates the expected duration of each script
            by checking the latest event data.
            This info is available after a script is configured in the
            Script_logevent_metadata.
        """
        for salindex in self.scripts_remotes:
            remote = self.scripts_remotes[salindex]
            if not salindex in self.scripts_durations:
                self.scripts_durations[salindex] = 'UNKNOWN'
            # TODO: if durations exists then continue
            while True:
                info = remote.evt_metadata.get_oldest()
                if info is None:
                    break
                self.scripts_durations[salindex] = info.duration
    def parse_script(self, script):
        new_script = {**script}
        new_script['index'] = int(new_script['index'])
        new_script['script_state'] = new_script['script_state'].name
        new_script['process_state'] = new_script['process_state'].name
        new_script['elapsed_time'] = new_script['duration']; 
        new_script['expected_duration'] = self.scripts_durations[new_script['index']]
        discard = ['duration', 'remote', 'updated']
        for name in discard:
            del new_script[name]
        return new_script

    def parse_queue_state(self):
        """
            Gets the updated state and returns it in a LOVE-friendly format.
        """

        # "get_queue_state" makes the update before parsing the state
        queue_state = self.queue.get_queue_state() 

        # update scripts duration from remote.evt_metadata (this is not in RequestModel)
        self.update_scripts_remotes(queue_state)
        self.update_scripts_durations()

        
        queue_state['finished_scripts'] = list(queue_state['past_scripts'].values())
        queue_state['waiting_scripts'] = list(queue_state['queue_scripts'].values())
        del queue_state['past_scripts']
        del queue_state['queue_scripts']

        for queue_name in ['waiting_scripts', 'finished_scripts']:
            queue = queue_state[queue_name]
            for i, script in enumerate(queue):
                queue[i] = self.parse_script(queue[i])

        if queue_state['current'] == None:
            queue_state['current'] = 'None'
        else:
            queue_state['current'] = self.parse_script(queue_state['current'])

        import pprint
        pprint.pprint(queue_state)
        return queue_state
    
    def get_state_message(self):

        queue_state = self.parse_queue_state()

        message = {
            'category': 'event',
            'data': {
                'scriptQueueState': json.dumps(queue_state)
            }
        }
        
        return message