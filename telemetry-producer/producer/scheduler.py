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


def on_message(ws, message):
    print("### message ###")
    print(message)

def on_error(ws, error):
    print("### error ###")
    print(error)

def on_close(ws):
    print("### closed ###")

def on_open(ws):
    def run(*args):
        while True:
            time.sleep(2)
            data_input = remote.tel_seeing.get()
            if data_input is None:
                print("none received")
                continue
            tel_parameters = [x for x in dir(data_input) if not x.startswith('__')]
            tel_result = {p:getattr(data_input, p) for p in tel_parameters}
            print("latest result:")
            print(data_input.seeing)
            print(json.dumps(tel_result))

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

    websocket.enableTrace(True)
    ws = websocket.WebSocketApp("ws://echo.websocket.org:80/",
                              on_message = on_message,
                              on_error = on_error,
                              on_close = on_close)
    ws.on_open = on_open


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