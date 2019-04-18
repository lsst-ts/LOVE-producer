import time
import websocket
try:
    import thread
except ImportError:
    import _thread as thread
import os

import threading

from telemetries_events.producer import Producer
from scriptqueue.producer import ScriptQueueProducer
from heartbeats.producer import HeartbeatProducer
import json
import asyncio
import pprint


def on_ws_message(ws, message):
    print("### message ###")
    print(message)

def on_ws_error(ws, error):
    print("### error ###")
    print(error)

def on_ws_close(ws):
    print("### closed ###")

def send_message_callback(ws, message):
    """
        Callback that parses a dictionary (message)
        into a JSON string and sends it through websockets
        
        message : dict
    """
    ws.send(json.dumps(message))


def on_ws_open(ws, message_getters, loop):
    """
        Starts sending messages through a websocket connection
        every through seconds, from a list of messages
        when the on_open event callback is called.

        parameters:
            
        ws: websocket.WebSocket object
        message_getters: list of functions such that each one returns a dict 
        with this structure:
            {
                'category': 'event',
                'data' : { .... }
            }
    """

    producer_scriptqueue = ScriptQueueProducer(loop, lambda m: send_message_callback(ws,m))
    producer_heartbeat = HeartbeatProducer(loop, lambda m: send_message_callback(ws,m))

    print('ws started to open')
    def run(*args):
        asyncio.set_event_loop(args[0])
        producer_heartbeat.start()
        while True:
            producer_scriptqueue.update()
            for get_message in message_getters:
                message = get_message()
                ws.send(json.dumps(message))
            time.sleep(2)            
        time.sleep(1)
        ws.close()
        print("thread terminating...")
    thread.start_new_thread(run, (loop,))
    print("open")
    
def run_evt_loop(loop):
    loop.run_forever()

if __name__=='__main__':
    print('--main--')
    loop = asyncio.get_event_loop()
    t = threading.Thread(target=run_evt_loop, args=(loop,))
    t.start()
    WS_HOST = os.environ["WEBSOCKET_HOST"]
    WS_PASS = os.environ["PROCESS_CONNECTION_PASS"]
    # websocket.enableTrace(True)
    url = "ws://{}/?password={}".format(WS_HOST, WS_PASS)
    ws = websocket.WebSocketApp(url,
                            on_message = on_ws_message,
                            on_error = on_ws_error,
                            on_close = on_ws_close)
    
    producer = Producer(loop)


    message_getters = [
        producer.get_telemetry_message,
        producer.get_events_message
    ]

    ws.on_open = lambda ws: on_ws_open(ws, message_getters, loop)

    #Emitter
    while True:
        # print('loop')
        time.sleep(3)
        ws.run_forever()