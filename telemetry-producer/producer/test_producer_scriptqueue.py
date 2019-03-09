from producer_scriptqueue import ScriptQueueProducer, get_remote_event_values
from lsst.ts import salobj
import SALPY_Script
import pprint
import time
import asyncio
sqp = ScriptQueueProducer()

# while True:
#     message = sqp.parse_queue_state()
#     pprint.pprint(message)
#     time.sleep(0.5)


# salindex = 100011
# sqp.queue.state.scripts[salindex]['remote'] = salobj.Remote(SALPY_Script, salindex)
# remote = salobj.Remote(SALPY_Script, salindex)

# salindex = 100005

import numpy as np
import traceback

# def get_scripts_re

# cada dos segundos:
#-----------------------

# ejemplo para actualizar el listado de scripts
# y despues sacarlos reomtes e info de sus valores

# while True:
#     break
#     # obtener los salindex de todos los scripts
#     queue_state = sqp.queue.get_queue_state()
#     indices = list(queue_state['queue_scripts'].keys())
#     # print('\n\n\n scripts indices in the csc: ', sqp.queue.state.scripts.keys())
#     if len(indices) == 0 : 
#         print('empty queue')
#         time.sleep(1)
#         continue

#     salindex = np.max(indices)
#     for salindex in indices:
#         try:
#             if not sqp.queue.state.scripts[salindex]['remote'] == None: continue

#             print('state of the latest script:', salindex,  queue_state['queue_scripts'][salindex]['script_state'])

#             sqp.queue.get_script_remote(salindex)
#             print(sqp.queue.state.scripts[salindex]['remote'] )
#             print('remote update succeeded')
#         except Exception as e:
#             traceback.print_exc()
#             print('err',e)
        
#     for salindex in indices:
#         if sqp.queue.state.scripts[salindex]['remote'] == None: continue
        
#         remote = queue_state['queue_script'][salindex]['remote']

#         import pdb;pdb.set_trace()

        
#     time.sleep(1)
#-----------------------

# catch new indices from events

# then get the remote of that script

# then listen to its events and catch when "duration" is available
# this should be the expected duration
# (tiago said this is after a script is configured)


def get_queue_new_script_indices(values):
    """
        Takes the output of get_remote_event_values
        and returns a list with the indices of the scripts
        that were added to the queue since last event check
    """
    new_indices = []
    for key in values.keys():
        if key == 'queue':
            waiting_length = values['queue'][0]['length']['value']
            waiting_indices = values['queue'][0]['salIndices']['value'][:waiting_length]
            finished_length = values['queue'][0]['pastLength']['value']
            finished_indices = values['queue'][0]['pastSalIndices']['value'][:finished_length]
            current_index = values['queue'][0]['currentSalIndex']['value']

            indices = np.hstack([waiting_indices, finished_indices])
            if current_index > 0 : indices = np.hstack([indices, [current_index]])
            if 0 in indices:
                print('waiting:', waiting_indices)
                print('finished:', finished_indices)
                print('current', current_index)
            new_indices = set(indices).difference(set(sqp.queue.state.scripts.keys()))
    return list(filter(lambda i: i>0, new_indices))

while True: 
    values = get_remote_event_values(sqp.queue.queue)
    new_indices = get_queue_new_script_indices(values)
    print(new_indices)
    time.sleep(1.0)