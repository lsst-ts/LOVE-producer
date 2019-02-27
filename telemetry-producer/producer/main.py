import time
import websocket
try:
    import thread
except ImportError:
    import _thread as thread
import os

from producer import Producer

def on_ws_open(ws,send_ws_data):
    def run(*args):
        while True:
            time.sleep(2)
            print(200*'\n'+'hola hola')
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