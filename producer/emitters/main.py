
import numpy as np
from lsst.ts import salobj

import json

import importlib

import threading
import asyncio
import datetime

from emitter import emit_forever
from event_emitter import emit_forever as emit_event_forever

def add_controller_in_thread(sal_lib, loop, index):
    asyncio.set_event_loop(loop)
    controller = create_controller(sal_lib, index)
    launch_emitters_forever(controller)

def create_controller(sallib, index):        
    print("make controller", sallib)
    controller = salobj.Controller(sallib, index)

    return controller

def launch_emitters_forever(controller):
    """
        Launches an emitter that fills the data to be read
        later in the salobj remote
    """
    freq = 0.5
    t1 = threading.Thread(target=emit_forever, args=[controller, freq, loop])
    t1.start()
    t2 = threading.Thread(target=emit_event_forever, args=[controller, freq, loop])
    t2.start()

def run_evt_loop(loop):
    loop.run_forever()

if __name__=='__main__':
    print('--main--')
    loop = asyncio.get_event_loop()
    t = threading.Thread(target=run_evt_loop, args=(loop,))
    t.start()

    sal_lib_param_list = [line.rstrip('\n') for line in open('/usr/src/love/sallibs.config')]
    for i in range(len(sal_lib_param_list)):
        sal_lib_params = sal_lib_param_list[i].split(' ')
        sal_lib_name = sal_lib_params[0]
        index = 0
        print(sal_lib_params)
        if len(sal_lib_params) > 1:
            [sal_lib_name, index] = sal_lib_params
        index = int(index)
        sal_lib = importlib.import_module(sal_lib_name)
        t = threading.Thread(target=add_controller_in_thread, args=[sal_lib, loop, index])
        t.start()