import time
import websocket
try:
    import thread
except ImportError:
    import _thread as thread
import os

from producer import Producer
from producer_scriptqueue import ScriptQueueProducer

def on_ws_open(ws,get_message):
    print('ws started to open')
    def run(*args):
        print('start message loop')
        while True:
            print('will send message')
            time.sleep(2)
            print(200*'\n'+'hola hola')
            message_dict = get_message()
            print('message:', message_dict)
            ws.send(json.dumps({
                "category": "event",
                "data": message_dict
            }))
            # send_ws_data(ws)
            
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
    print('--main--')
    # producer = Producer()
    producer_scriptqueue = ScriptQueueProducer()

    WS_HOST = os.environ["WEBSOCKET_HOST"]
    websocket.enableTrace(True)
    ws = websocket.WebSocketApp("ws://%s/" % WS_HOST,
                            on_message = on_ws_message,
                            on_error = on_ws_error,
                            on_close = on_ws_close)

    print('ws will open')

    ws.on_open = lambda ws: on_ws_open(ws, producer_scriptqueue.parse_queue_state)

    #Emitter
    while True:
        time.sleep(3)
        ws.run_forever()