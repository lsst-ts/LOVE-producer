"""Main executable of the LOVE-producer."""
import asyncio
import json
import os
import time
import threading
import websocket
try:
    import thread
except ImportError:
    import _thread as thread
from lsst.ts import salobj
from telemetries_events.producer import Producer
from scriptqueue.producer import ScriptQueueProducer
from heartbeats.producer import HeartbeatProducer
from command_receiver.receiver import Receiver
from initial_state.producer import InitialStateProducer
from utils import NumpyEncoder
import utils

CONFIG_PATH = 'config/config.json'


def on_ws_message(ws, message, receiver, initialStateProducer, loop):
    async def receive_it():
        jsonmessage = json.loads(message)
        if jsonmessage["category"] == "initial_state":
            answer = await initialStateProducer.process_message(jsonmessage)
            if answer is None:
                return
            dumped_answer = json.dumps(answer, cls=NumpyEncoder)
            ws.send(dumped_answer)
            return

        if jsonmessage["category"] == "cmd":
            answer = await receiver.process_message(message)
            if answer is None:
                return
            dumped_answer = json.dumps(answer, cls=NumpyEncoder)
            ws.send(dumped_answer)
            return
    asyncio.run_coroutine_threadsafe(receive_it(), loop)


def on_ws_error(ws, error):
    print("### error ###")
    print(error)


def on_ws_close(ws):
    print("### closed ###")


def send_message_callback(ws, message):
    """Define a callback that parses a dictionary (message) into a JSON string and sends it through websockets.

    Parameters
    ----------
    ws: `websocket.WebSocket object`
        websocket object that handles the connection
    message : `dict`
        the message to send
    """

    cscs = utils.get_all_csc_names_in_message(message)
    print(cscs)
    
    ws.send(json.dumps(message))


running = False


def on_ws_open(ws, domain, message_getters, loop, csc_list, sq_list):
    """Starts sending messages through a websocket connection every through seconds,
    from a list of messages when the on_open event callback is called.

    Parameters
    ----------
    ws: `websocket.WebSocket object`
        websocket object that handles the connection
    message_getters: `list`
        list of functions such that each one returns a dict with this structure:
        {
            'category': 'event',
            'data' : { .... }
        }
    """
    global running
    print('ws started to open')

    producer_heartbeat = HeartbeatProducer(domain, lambda m: send_message_callback(ws, m), csc_list)
    print('Heartbeat producer created')

    producer_scriptqueues = [
        ScriptQueueProducer(domain, lambda m: send_message_callback(ws, m), sq[1]) for sq in sq_list
    ]
    for producer in producer_scriptqueues:
        loop.create_task(producer.setup())
    print('ScriptQueue producers created')

    # Accept commands
    cmd_subscribe_msg = {
        'option': 'subscribe',
        'category': 'cmd',
        'csc': 'all',
        'salindex': 'all',
        'stream': 'all'
    }
    ws.send(json.dumps(cmd_subscribe_msg))

    # Handle initial-state requests
    initial_state_subscribe_msg = {
        'option': 'subscribe',
        'category': 'initial_state',
        'csc': 'all',
        'salindex': 'all',
        'stream': 'all'
    }
    ws.send(json.dumps(initial_state_subscribe_msg))

    def run(*args):
        asyncio.set_event_loop(args[0])
        producer_heartbeat.start()
        while True:
            for producer_scriptqueue in producer_scriptqueues:

                loop.create_task(producer_scriptqueue.update())
            for get_message in message_getters:
                message = get_message()
                ws.send(json.dumps(message))
            time.sleep(2)
        time.sleep(1)
        ws.close()
        print("thread terminating...")

    if not running:
        thread.start_new_thread(run, (loop,))
        running = True
    print("open")


def run_evt_loop(loop):
    loop.run_forever()


def read_config(path, key=None):
    """ Reads a given config file and returns the lists of CSCs to listen to.
    It can read the full file (by default), or read only a specific key

    Parameters
    ----------
    path: `string`
        The full path of the config file
    key: `string`
        optional key to read

    Returns
    -------
    csc_list: `[()]`
        The list of CSCs to run as a tuple with the CSC name and index
    """
    print('Reading config file: ', path)
    with open(path) as config_file:
        data = json.loads(config_file.read())

    # data = json.load(open(path, 'r'))
    csc_list = []
    if key:
        for csc_instance in data[key]:
            index = None
            if 'index' in csc_instance:
                index = csc_instance['index']
            csc_list.append((key, index))
    else:
        for csc_key, csc_value in data.items():
            for csc_instance in csc_value:
                index = None
                if 'index' in csc_instance:
                    index = csc_instance['index']
                csc_list.append((csc_key, index))
    return csc_list


if __name__ == '__main__':
    """ Runs the Producer """
    print('***** Starting Producer *****')
    path = os.path.join(os.path.dirname(__file__), CONFIG_PATH)
    csc_list = read_config(path)
    sq_list = read_config(path, 'ScriptQueue')
    print('List of CSCs to listen:', csc_list)
    print('List of Script Queues to listen:', sq_list)

    loop = asyncio.get_event_loop()
    t = threading.Thread(target=run_evt_loop, args=(loop,))
    t.start()
    print('Creating domain')
    domain = salobj.Domain()

    WS_HOST = os.environ["WEBSOCKET_HOST"]
    WS_PASS = os.environ["PROCESS_CONNECTION_PASS"]
    url = "ws://{}/?password={}".format(WS_HOST, WS_PASS)
    receiver = Receiver(domain, csc_list)
    initialStateProducer = InitialStateProducer(domain, csc_list)

    ws = websocket.WebSocketApp(
        url,
        on_error=on_ws_error,
        on_close=on_ws_close)

    producer = Producer(loop, domain, csc_list)

    message_getters = [
        producer.get_telemetry_message,
        producer.get_events_message
    ]

    ws.on_open = lambda ws: on_ws_open(
        ws, domain, message_getters, loop, csc_list, sq_list)
    ws.on_message = lambda ws, message: on_ws_message(ws, message, receiver, initialStateProducer, loop)

    # Emitter
    while True:
        # print('loop')
        time.sleep(3)
        ws.run_forever()
