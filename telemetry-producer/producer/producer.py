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


class Producer:
    """
        Class that creates remote and controller objects using the salobj library
        emitting fake telemetry and event data which is then sent over with websockets
    """
    def __init__(self):

        sal_lib_list = [importlib.import_module(line.rstrip('\n')) for line in open('sallibs.config')]
        self.remote_list = []
        self.controller_list = []
        for i in range(len(sal_lib_list)):
            sal_lib = sal_lib_list[i]
            remote, controller = self.create_remote_and_controller(sal_lib)
            self.remote_list.append(remote)
            self.controller_list.append(controller)

        for i in range(len(self.controller_list)):
            controller = self.controller_list[i]
            self.launch_emitter_forever(controller)

    def getDataType(self, value):
        if isinstance(value, (list, tuple, np.ndarray)):
            return 'Array<%s>' % self.getDataType(value[0])
        if isinstance(value, (int, np.integer)):
            return 'Int'
        if isinstance(value, float):
            return 'Float'
        if isinstance(value, str):
            return 'String'
        return 'None'


    def get_remote_tel_values(self, remote):
        tel_names = remote.salinfo.manager.getTelemetryNames()
        values = {}
        for tel in tel_names:
            tel_remote = getattr(remote, "tel_" + tel)
            data = tel_remote.get()
            if data is None:
                continue
            tel_parameters = [x for x in dir(data) if not x.startswith('__')]
            tel_result = {p:{'value': getattr(data, p), 'dataType': self.getDataType(getattr(data, p))} for p in tel_parameters}
            values[tel] = tel_result
        return values

    def get_remote_event_values(self, remote):
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
                evt_result = {p:{'value': getattr(data, p), 'dataType': self.getDataType(getattr(data, p))} for p in evt_parameters}
                evt_results.append(evt_result)
            if len(evt_results) == 0:
                continue
            values[evt] = evt_results
        return values

    def create_remote_and_controller(self, sallib):
        """
        
        """
        print("\n make remote")
        remote = salobj.Remote(sallib, 0)
        
        print("make controller")
        controller = salobj.Controller(sallib, 0)

        return remote, controller

    def launch_emitter_once(self, controller, test_seed=None):
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

    def launch_emitter_forever(self, controller):
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

    def send_ws_data(self, ws):
        #Send telemetry stream
        output_dict = {}
        for i in range(len(self.remote_list)):
            remote = self.remote_list[i]
            values = self.get_remote_tel_values(remote)
            output = json.dumps(values, cls=NumpyEncoder)

            output_dict[remote.salinfo.name] = output
        ws.send(json.dumps({
            "category": "telemetry",
            "data": output_dict
        }))

        #Send event stream
        output_dict = {}
        for i in range(len(self.remote_list)):
            remote = self.remote_list[i]
            values = self.get_remote_event_values(remote)
            output = json.dumps(values, cls=NumpyEncoder)

            output_dict[remote.salinfo.name] = output
        ws.send(json.dumps({
            "category": "event",
            "data": output_dict
        }))

def on_ws_open(ws,send_ws_data):
    def run(*args):
        while True:
            time.sleep(2)
            send_ws_data(ws)
            
        time.sleep(1)
        ws.close()
        print("thread terminating...")
    thread.start_new_thread(run, ())
    print("open")

def on_ws_message(ws, message):
    print("### message ###")
    print(message)

def on_ws_error(ws, error):
    print("### error ###")
    print(error)

def on_ws_close(ws):
    print("### closed ###")

if __name__=='__main__':

    producer = Producer()

    WS_HOST = os.environ["WEBSOCKET_HOST"]
    websocket.enableTrace(True)
    ws = websocket.WebSocketApp("ws://%s/" % WS_HOST,
                            on_message = on_ws_message,
                            on_error = on_ws_error,
                            on_close = on_ws_close)

    ws.on_open = lambda ws: on_ws_open(ws, producer.send_ws_data)

    #Emitter
    while True:
        time.sleep(3)
        ws.run_forever()    