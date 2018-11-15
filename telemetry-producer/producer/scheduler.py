import websocket
import time

try:
    import thread
except ImportError:
    import _thread as thread
import time


import SALPY_scheduler
import salobj
import time
import json
import os
from utils import NumpyEncoder

def get_remote_values(remote):
    tel_names = remote.salinfo.manager.getTelemetryNames()
    values = []
    for tel in tel_names:
        tel_remote = getattr(remote, "tel_" + tel)
        data = tel_remote.get()
        if data is None:
            continue
        tel_parameters = [x for x in dir(data) if not x.startswith('__')]
        tel_result = {p:getattr(data, p) for p in tel_parameters}
        values.append(tel_result)
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
            ws.send(json.dumps(values, cls=NumpyEncoder))
        time.sleep(1)
        ws.close()
        print("thread terminating...")
    thread.start_new_thread(run, ())
    print("open")


if __name__ == "__main__":
    ### SAL ###
    print("\nmake remote")
    remote = salobj.Remote(SALPY_scheduler, 0)
    print("make controller")
    controller = salobj.Controller(SALPY_scheduler, 0)

    # def callback(data):
    #     ws.send("Hello %d" % i)
    # remote.tel_seeing.callback = callback
    ### SAL ###

    WS_HOST = os.environ["WEBSOCKET_HOST"]
    websocket.enableTrace(True)
    ws = websocket.WebSocketApp("ws://%s/" % WS_HOST,
                              on_message = on_ws_message,
                              on_error = on_ws_error,
                              on_close = on_ws_close)
    ws.on_open = on_ws_open


    #Emitter
    import eventlet
    eventlet.monkey_patch()
    from emitter import run
    freq = 0.5
    eventlet.spawn(run, controller, freq)
    #Emitter


    while True:
        time.sleep(3)
        ws.run_forever()