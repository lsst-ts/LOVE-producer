import time
import threading
from lsst.ts import salobj
import asyncio
import SALPY_ScriptQueue

from producer_scriptqueue import ScriptQueueProducer
import pprint
import json


import main

from lsst.ts.scriptqueue.base_script import HEARTBEAT_INTERVAL





loop = asyncio.get_event_loop()
t = threading.Thread(
    target = lambda : loop.run_forever())
t.start()

sqp = ScriptQueueProducer(loop, lambda x:x)

import os
import websocket
WS_HOST = os.environ["WEBSOCKET_HOST"]
WS_PASS = os.environ["PROCESS_CONNECTION_PASS"]
# websocket.enableTrace(True)
url = "ws://{}/?password={}".format(WS_HOST, WS_PASS)
ws = websocket.WebSocketApp(url,
                        on_message = main.on_ws_message,
                        on_error = main.on_ws_error,
                        on_close = main.on_ws_close)

ws.on_open = lambda ws:print('asd')


while True:
    time.sleep(2)