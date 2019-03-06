import asyncio
import time
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

queue = ui.RequestModel(1)


# get an updated dict with the queue state
queue_state = queue.get_queue_state()


# get available scripts
queue.get_scripts()    

# run script1 from standard
#TODO: donde se ven los parametros del config?
script = 'script1'
is_standard = True
config = "{wait_time: '10'}"
salindex = queue.add(script, is_standard, config)
print(10*'\n','duration',queue.state.scripts[salindex]['duration'])
queue_state = queue.get_queue_state()
#{'state': 'Running', 'queue_scripts': {100000: {'index': 100000, 'type': 'UNKNOWN', 'path': 'UNKNOWN', 'duration': 0.0, 'timestamp': 0.0, 'script_state': <ScriptState.UNKNOWN: 0>, 'process_state': <ScriptProcessState.UNKNOWN: 0>, 'remote': None, 'updated': False}}, 'past_scripts': {}, 'current': None}

#---monitor---

# get script remote        
queue.get_script_remote(salindex)
remote = queue.state.scripts[salindex]['remote']

queue.state.scripts[100020]['duration']


import threading

t = threading.Thread(target=queue.monitor_script, args=[salindex])
t.start()
print('\n\n\nprint print')
# loop = asyncio.get_event_loop()
# loop.run_until_complete(printstuff(salindex))

print(dir(remote))


i = 0
while True:
    i+=1
    print(10*'\n','duration',queue.state.scripts[salindex]['duration'])
    # queue.state.update_script_info(queue.queue.evt_script.get())
    if queue.state.scripts[salindex]['process_state'] >= ScriptProcessState.DONE:
        print('done')
        break
    values = get_remote_event_values(remote)
    print(5*'\n',i,queue.state.scripts[salindex]['process_state'])
    print(values)
    time.sleep(1.0)
    
# [salIndex:100002][Standard][path:script1][duration:0.0][ScriptState.UNCONFIGURED][ScriptProcessState.LOADING]
# [salIndex:100002][Standard][path:script1][duration:0.0][ScriptState.CONFIGURED][ScriptProcessState.LOADING]
# [salIndex:100002][Standard][path:script1][duration:0.0][ScriptState.CONFIGURED][ScriptProcessState.CONFIGURED]
# [salIndex:100002][Standard][path:script1][duration:0.0][ScriptState.RUNNING][ScriptProcessState.RUNNING]
# [salIndex:100002][Standard][path:script1][duration:0.0][ScriptState.ENDING][ScriptProcessState.RUNNING]
# [salIndex:100002][Standard][path:script1][duration:0.0][ScriptState.DONE][ScriptProcessState.RUNNING]
# [salIndex:100002][Standard][path:script1][duration:17.66][ScriptState.DONE][ScriptProcessState.DONE]

script = queue.get_scripts()['external'][0]
# while True:


# {
#   'state': 'Running',
#   'queue_scripts': {
#     100007: {
#       'index': 100007,
#       'type': 'Standard',
#       'path': 'script1',
#       'duration': 0.0,
#       'timestamp': 1551897088.735314,
#       'script_state': < ScriptState.UNCONFIGURED: 1 > ,
#       'process_state': < ScriptProcessState.LOADING: 1 > ,
#       'remote': None,
#       'updated': True
#     }
#   },
#   'past_scripts': {
#     100006: {
#       'index': 100006,
#       'type': 'Standard',
#       'path': 'script1',
#       'duration': 17.649086952209473,
#       'timestamp': 1551896991.462045,
#       'script_state': < ScriptState.DONE: 8 > ,
#       'process_state': < ScriptProcessState.DONE: 4 > ,
#       'remote': None,
#       'updated': True
#     },
#     100005: {
#       'index': 100005,
#       'type': 'Standard',
#       'path': 'script1',
#       'duration': 17.911284923553467,
#       'timestamp': 1551896801.771342,
#       'script_state': < ScriptState.DONE: 8 > ,
#       'process_state': < ScriptProcessState.DONE: 4 > ,
#       'remote': None,
#       'updated': True
#     },
#     100004: {
#       'index': 100004,
#       'type': 'Standard',
#       'path': 'script1',
#       'duration': 17.77105402946472,
#       'timestamp': 1551896758.867856,
#       'script_state': < ScriptState.DONE: 8 > ,
#       'process_state': < ScriptProcessState.DONE: 4 > ,
#       'remote': None,
#       'updated': True
#     },
#     100003: {
#       'index': 100003,
#       'type': 'Standard',
#       'path': 'script1',
#       'duration': 17.786152124404907,
#       'timestamp': 1551896682.48031,
#       'script_state': < ScriptState.DONE: 8 > ,
#       'process_state': < ScriptProcessState.DONE: 4 > ,
#       'remote': None,
#       'updated': True
#     },
#     100002: {
#       'index': 100002,
#       'type': 'Standard',
#       'path': 'script1',
#       'duration': 17.710328102111816,
#       'timestamp': 1551896655.333107,
#       'script_state': < ScriptState.DONE: 8 > ,
#       'process_state': < ScriptProcessState.DONE: 4 > ,
#       'remote': None,
#       'updated': True
#     },
#     100001: {
#       'index': 100001,
#       'type': 'Standard',
#       'path': 'script1',
#       'duration': 18.44283103942871,
#       'timestamp': 1551896636.720454,
#       'script_state': < ScriptState.DONE: 8 > ,
#       'process_state': < ScriptProcessState.DONE: 4 > ,
#       'remote': None,
#       'updated': True
#     },
#     100000: {
#       'index': 100000,
#       'type': 'Standard',
#       'path': 'script1',
#       'duration': 18.38657307624817,
#       'timestamp': 1551896471.427708,
#       'script_state': < ScriptState.DONE: 8 > ,
#       'process_state': < ScriptProcessState.DONE: 4 > ,
#       'remote': None,
#       'updated': True
#     }
#   },
#   'current': None
# }