import asyncio
import time
import threading
async def printstuff(salindex):
    info = await queue.queue.evt_script.next(flush=False)
    queue.state.update_script_info(info)
    if info.salIndex == salindex:
        print('salindex=salindex')
        print(queue.parse_info(queue.state.scripts[salindex]))
    else:
        print('else: log debug')
        queue.log.debug(queue.parse_info(queue.state.scripts[salindex]))

def get_remote_event_values(remote):
    evt_names = remote.salinfo.manager.getEventNames()
    values = {}
    for evt in evt_names:
        evt_remote = getattr(remote, "evt_" + evt)
        evt_results = []
        while True:
            data = evt_remote.get_oldest()
            if data is None:
                break
            evt_parameters = [x for x in dir(data) if not x.startswith('__')]
            evt_result = {p:{'value': getattr(data, p) } for p in evt_parameters}
            evt_results.append(evt_result)
        if len(evt_results) == 0:
            continue
        values[evt] = evt_results
    return values


#--- setup --
from lsst.ts.scriptqueue import ui, ScriptProcessState

class ScriptQueueProducer:
    def __init__(self):
        self.queue = ui.RequestModel(1)
        queue_state = self.queue.get_queue_state()
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
        self.queue.update_scripts_info()
        self.queue.update_queue_state()

    def parse_script(script):
        new_script = {**script}
        new_script['script_state'] = new_script['script_state'].name
        new_script['process_state'] = new_script['process_state'].name
        new_script['elapsed_time'] = new_script['duration']; 
        discard = ['duration', 'remote', 'updated']
        for name in discard:
            del new_script[name]
        return new_script

    def parse_queue_state(self):
        """
            Gets the updated state and returns it in a LOVE-friendly format
        """

        # "get_queue_state" makes the update before parsing the state
        queue_state = self.queue.get_queue_state() 
        queue_state['finished_scripts'] = queue_state['past_scripts']
        queue_state['waiting_scripts'] = queue_state['queue_scripts']
        del queue_state['past_scripts']
        del queue_state['queue_scripts']

        for queue_name in ['waiting_scripts', 'finished_scripts']:
            queue = queue_state[queue_name]
            for script in list(queue.keys()):
                queue[script] = self.parse_script(queue[script])

        if queue_state['current'] == None:
            queue_state['current'] = 'None'
        else:
            queue_state['current'] = self.parse_script(queue_state['current'])
            
        return queue_state
    # def send_ws_data(self, ws):
    #     """
    #         Prepares a message to be sent with websockets (for example),
    #         based on the updated state of the queue.
    #     """

    #     indices = list(self.queue.state.scripts.keys())

    #     if len(indices) == 0: 
    #         print('no data')
    #         return

    #     self.update()


    #     queue_state = self.queue.get_queue_state()
    #     message = {
    #       'script_queue_state': {
    #         'waiting_scripts': queue_state['queue_scripts'],
    #         'finished_scripts': queue_state['past_scripts'],
    #         'current_script_index': queue_state['current'],
    #         'state': queue_state['state'],
    #         'scripts': {},
    #       }
    #     }
        
    #     print('\n\n\n\t current', self.queue.state._current_script_index)
    #     print('\t waiting:', self.queue.state._queue_script_indices)
    #     print('\t finished', self.queue.state._past_script_indices)
    #     import pprint
        


    #     for salindex in indices:
    #         info = {**self.queue.state.scripts[salindex]}
    #         info['script_state'] = info['script_state'].name
    #         info['process_state'] = info['process_state'].name
    #         info['elapsed_time'] = info['duration']; del info['duration']
            
    #         message['script_queue_state']['scripts'][salindex] = info
        
    #         # remote = self.queue.state.scripts[salindex]['remote']        
    #         # print(remote)
    #         # get_remote_event_values(remote)
    #     return message

    #     # # print(10*'\n','duration', self.queue.state.scripts[salindex]['duration'])
    #     # if self.queue.state.scripts[salindex]['process_state'] >= ScriptProcessState.DONE:
    #     #     print('done')
    #     #     return
    #     # values = get_remote_event_values(remote)
    #     # print(5*'\n', self.queue.state.scripts[salindex]['process_state'])
    #     # print(values)