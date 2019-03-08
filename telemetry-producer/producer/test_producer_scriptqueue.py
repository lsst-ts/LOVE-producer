from producer_scriptqueue import ScriptQueueProducer, get_remote_event_values
from lsst.ts import salobj
import SALPY_Script
import pprint
import time
# from importlib import reload
# reload(producer_scriptqueue)

# logfile = open('log.txtadsf','w')

sqp = ScriptQueueProducer()

while True:
    message = sqp.parse_queue_state()
    pprint.pprint(message)
    time.sleep(1)
# while True:
#     try:
#         state = sqp.queue.get_queue_state()
#         # pprint.pprint(state)
#         for queue in ['past_scripts', 'queue_scripts']:
#             if state[queue] is None:
#                 continue
#             script = parseScript(queue[100000])
#             print(queue, script[queue])
#             # for script in state[queue].keys():
#             #     pprint.pprint(queue, script)
#     except:
#         print('error')
#     time.sleep(1)


# sqp.do_run()
# import time
# while True:
#     sqp.send_ws_data(1)
#     # time.sleep(2)
#     break

# script_indices = []
# remotes = {}

# # while True:
# print('-')
# for salindex in list(sqp.queue.state.scripts.keys()):
#     remotes[salindex] = sqp.queue.state.scripts[salindex]['remote']
#     print(salindex, remotes[salindex])

# sqp.queue.update_queue_state



# for salindex in script_indices:
#     values = get_remote_event_values(remotes[salindex])
#     if any(values): 
#         print(values)
#         break
# time.sleep(1)
# i = 0
# while True:
#     i+=1

#     if queue.state.scripts[salindex]['process_state'] >= ScriptProcessState.DONE:
#         print('done')
#         break
#     values = get_remote_event_values(remote)
#     print(5*'\n',i,queue.state.scripts[salindex]['process_state'])
#     print(values)
#     time.sleep(1.0)
    

# get script remote        
# sqp.queue.get_script_remote(salindex)
# remote = queue.state.scripts[salindex]['remote']

# queue.state.scripts[100020]['duration']


# import threading

# t = threading.Thread(target=queue.monitor_script, args=[salindex])
# t.start()
# print('\n\n\nprint print')
# # loop = asyncio.get_event_loop()
# # loop.run_until_complete(printstuff(salindex))

# print(dir(remote))




# salindex = 100005
# self.queue.state.update_script_info(self.queue.queue.evt_script.get())
# info = {**sqp.queue.state.scripts[salindex]}
# info['script_state'] = info['script_state'].name
# info['process_state'] = info['process_state'].name

# from lsst.ts.scriptqueue import ScriptProcessState
# from lsst.ts.scriptqueue.base_script import ScriptState

# statesDict = { getattr(ScriptState, state).name: getattr(ScriptState, state).value for state in dir(ScriptState) if not state.startswith('__')}


# sqp.queue.get_script_remote(salindex)
# remote = queue.state.scripts[salindex]['remote']


# salindex = 100013
# sqp.monitor_script(100015)
# import asyncio

# async def runit():
#     await sqp.queue.evt_loop.run_until_complete(sqp.monitor_script(100018))

# sqp.monitor_script(100019)
# sqp.queue.evt_loop.run_until_complete(runit())
# sqp.queue.state.scripts[salindex]['remote'] = salobj.Remote(SALPY_Script, salindex)
# remote = salobj.Remote(SALPY_Script, salindex)

# >>> remote.evt_metadata.get_oldest() da none por algun motivo

