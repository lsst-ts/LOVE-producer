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

        t = threading.Thread(target=self.queue.monitor_script, args=[salindex])
        t.start()
    
    def send_ws_data(self, ws):
        """
            Prepares a message to be sent with websockets (for example),
            based on the updated state of the queue.
        """

        indices = list(self.queue.state.scripts.keys())

        if len(indices) == 0: 
            print('no data')
            return

        self.queue.update_scripts_info()
        self.queue.update_queue_state()

        message = {
          'script_queue_state': {
            'waiting_script_indices': self.queue.state._queue_script_indices,
            'finished_script_indices': self.queue.state._past_script_indices,
            'current_script_index': self.queue.state._current_script_index,
            'state': self.queue.state.state
            'scripts': {},
          }
        }
        
        print('\n\n\n\t current', self.queue.state._current_script_index)
        print('\t waiting:', self.queue.state._queue_script_indices)
        print('\t finished', self.queue.state._past_script_indices)
        import pprint
        
        
        for salindex in indices:
            info = {**self.queue.state.scripts[salindex]}
            info['script_state'] = info['script_state'].name
            info['process_state'] = info['process_state'].name
            info['elapsed_time'] = info['duration']
            del info['duration']
            message['script_queue_state']['scripts'][salindex] = info
        
        return message

        # # print(10*'\n','duration', self.queue.state.scripts[salindex]['duration'])
        # if self.queue.state.scripts[salindex]['process_state'] >= ScriptProcessState.DONE:
        #     print('done')
        #     return
        # remote = self.queue.state.scripts[salindex]['remote']        
        # values = get_remote_event_values(remote)
        # print(5*'\n', self.queue.state.scripts[salindex]['process_state'])
        # print(values)