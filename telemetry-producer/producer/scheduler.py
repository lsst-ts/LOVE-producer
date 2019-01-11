import websocket
import time

try:
    import thread
except ImportError:
    import _thread as thread
import time


import SALPY_scheduler
from lsst.ts import salobj
import time
import json
import os
from utils import NumpyEncoder

def get_remote_values(remote):
    tel_names = remote.salinfo.manager.getTelemetryNames()
    values = {}
    for tel in tel_names:
        tel_remote = getattr(remote, "tel_" + tel)
        data = tel_remote.get()
        if data is None:
            continue
        tel_parameters = [x for x in dir(data) if not x.startswith('__')]
        tel_result = {p:getattr(data, p) for p in tel_parameters}
        values[tel] = tel_result
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
            values = get_remote_values(remote)
            # print(json.dumps(values, cls=NumpyEncoder))
            output = {
                "data": json.dumps(values, cls=NumpyEncoder)
            }
            ws.send(json.dumps(output))
        time.sleep(1)
        ws.close()
        print("thread terminating...")
    thread.start_new_thread(run, ())
    print("open")

def create_remote_and_controller(sallib):
    """
    
    """
    print("\n make remote")
    remote = salobj.Remote(SALPY_scheduler, 0)
    
    print("make controller")
    controller = salobj.Controller(SALPY_scheduler, 0)

    return remote, controller

def launch_emitter_once(controller, test_seed=None):
    """
        Launches an emitter that fills the data to be read
        later in the salobj remote
    """
    import eventlet
    eventlet.monkey_patch()
    from emitter import emit
    freq = 0.5
    eventlet.spawn(emit, controller, test_seed)

def launch_emitter_forever(controller):
    """
        Launches an emitter that fills the data to be read
        later in the salobj remote
    """
    import eventlet
    eventlet.monkey_patch()
    from emitter import emit_forever
    freq = 0.5
    eventlet.spawn(emit_forever, controller, freq)

if __name__ == "__main__":


    remote, controller = create_remote_and_controller(SALPY_scheduler)

    launch_emitter_forever(controller)


    WS_HOST = os.environ["WEBSOCKET_HOST"]
    websocket.enableTrace(True)
    ws = websocket.WebSocketApp("ws://%s/" % WS_HOST,
                              on_message = on_ws_message,
                              on_error = on_ws_error,
                              on_close = on_ws_close)
    ws.on_open = on_ws_open


    #Emitter


    while True:
        time.sleep(3)
        ws.run_forever()
