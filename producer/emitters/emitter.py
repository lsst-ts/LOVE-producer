import random
import time
import numpy as np
import asyncio

def randomize_single_value(value):
    if isinstance(value, (int, np.integer)):
        return random.choice([0,1])
    if isinstance(value, float):
        return random.random()
    if isinstance(value, str):
        return random.choice(['a','b','c'])
    return value

def randomize_params(data):

    tel_param_names = [x for x in dir(data) if not x.startswith('__')]
    for param_name in tel_param_names:
        tel_param = getattr(data, param_name)
        if isinstance(tel_param, (list, tuple, np.ndarray)):
            new_array = map(lambda x: randomize_single_value(x), tel_param)
            for i in range(len(tel_param)):
                tel_param[i] = randomize_single_value(tel_param[i])
                # setattr(data, param_name, new_array)
        else:
            setattr(data, param_name, randomize_single_value(tel_param))

def emit(controller, test_seed=None):
    print("putting data")
    if(not test_seed == None): random.seed(test_seed)
    tel_names = controller.salinfo.manager.getTelemetryNames()
    for tel in tel_names:
        tel_controller = getattr(controller, "tel_" + tel)
        data_output = tel_controller.DataType()
        randomize_params(data_output)
        tel_controller.put(data_output)

def emit_forever(controller, frequency, loop):
    asyncio.set_event_loop(loop)
    period = 1/frequency
    while True:
        time.sleep(period)
        emit(controller)