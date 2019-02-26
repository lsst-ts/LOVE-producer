import websocket
import time
import numpy as np

try:
    import thread
except ImportError:
    import _thread as thread
import time

from lsst.ts import salobj
import time
import json
import os
from utils import NumpyEncoder
import importlib

def getDataType(value):
    if isinstance(value, (list, tuple, np.ndarray)):
        return 'Array<%s>' % getDataType(value[0])
    if isinstance(value, (int, np.integer)):
        return 'Int'
    if isinstance(value, float):
        return 'Float'
    if isinstance(value, str):
        return 'String'
    return 'None'


def get_remote_tel_values(remote):
    tel_names = remote.salinfo.manager.getTelemetryNames()
    values = {}
    for tel in tel_names:
        tel_remote = getattr(remote, "tel_" + tel)
        data = tel_remote.get()
        if data is None:
            continue
        tel_parameters = [x for x in dir(data) if not x.startswith('__')]
        tel_result = {p:{'value': getattr(data, p), 'dataType': getDataType(getattr(data, p))} for p in tel_parameters}
        values[tel] = tel_result
    return values

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
            evt_result = {p:{'value': getattr(data, p), 'dataType': getDataType(getattr(data, p))} for p in evt_parameters}
            evt_results.append(evt_result)
        if len(evt_results) == 0:
            continue
        values[evt] = evt_results
    return values

def on_ws_message(ws, message):
    print("### message ###")
    print(message)

def on_ws_error(ws, error):
    print("### error ###")
    print(error)

def on_ws_close(ws):
    print("### closed ###")

def on_ws_open(ws):
    def run(*args):
        while True:
            time.sleep(2)
            #Send telemetry stream
            output_dict = {}
            for i in range(len(remote_list)):
                remote = remote_list[i]
                values = get_remote_tel_values(remote)
                output = json.dumps(values, cls=NumpyEncoder)

                output_dict[remote.salinfo.name] = output
            ws.send(json.dumps({
                "category": "telemetry",
                "data": output_dict
            }))

            #Send event stream
            output_dict = {}
            for i in range(len(remote_list)):
                remote = remote_list[i]
                values = get_remote_event_values(remote)
                output = json.dumps(values, cls=NumpyEncoder)

                output_dict[remote.salinfo.name] = output
            ws.send(json.dumps({
                "category": "event",
                "data": output_dict
            }))
        time.sleep(1)
        ws.close()
        print("thread terminating...")
    thread.start_new_thread(run, ())
    print("open")

def create_remote_and_controller(sallib):
    """

    """
    print("\n make remote")
    remote = salobj.Remote(sallib, 0)

    print("make controller")
    controller = salobj.Controller(sallib, 0)

    return remote, controller

def launch_emitter_once(controller, test_seed=None):
    """
        Launches an emitter that fills the data to be read
        later in the salobj remote
    """
    import eventlet
    eventlet.monkey_patch()
    from emitter import emit
    from event_emitter import emit as emit_event
    freq = 0.5
    eventlet.spawn(emit, controller, test_seed)
    eventlet.spawn(emit_event, controller, freq)

def launch_emitter_forever(controller):
    """
        Launches an emitter that fills the data to be read
        later in the salobj remote
    """
    import eventlet
    eventlet.monkey_patch()
    from emitter import emit_forever
    from event_emitter import emit_forever as emit_event_forever
    freq = 0.5
    eventlet.spawn(emit_forever, controller, freq)
    eventlet.spawn(emit_event_forever, controller, freq)

if __name__ == "__main__":

    sal_lib_list = [importlib.import_module(line.rstrip('\n')) for line in open('sallibs.config')]
    remote_list = []
    controller_list = []
    for i in range(len(sal_lib_list)):
        sal_lib = sal_lib_list[i]
        remote, controller = create_remote_and_controller(sal_lib)
        remote_list.append(remote)
        controller_list.append(controller)

    for i in range(len(controller_list)):
        controller = controller_list[i]
        launch_emitter_forever(controller)

    WS_HOST = os.environ["WEBSOCKET_HOST"]
    WS_PASS = os.environ["PROCESS_CONNECTION_PASS"]
    websocket.enableTrace(True)
    url = "ws://{}/?password={}".format(WS_HOST, WS_PASS)
    ws = websocket.WebSocketApp(url,
                              on_message = on_ws_message,
                              on_error = on_ws_error,
                              on_close = on_ws_close)
    ws.on_open = on_ws_open


    #Emitter


    while True:
        time.sleep(3)
        ws.run_forever()
